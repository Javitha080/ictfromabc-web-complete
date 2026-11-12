# DEEP DIVE — small security functions, all-round check (ictfromabc.com)
Date: 2026-09-11 | Evidence: `D:\Pentesting\ictfromabc\deepdive_smallfuncs*.txt`, `dns_txt.txt`, `dns_mxns.txt`, `nmap_ssl.txt`, `ffuf*.json`, `route_probe.txt`
Rule: only what was measured. Anything else is marked NOT-TESTED.

## 1. Session handling [V]
- Stateless Bearer PAT (`id|secret`, Sanctum-consistent) in localStorage; NO `Set-Cookie` on `/` or `/api/*` (verified headers). Consequence: no cookie-flag issues possible, but any XSS = full token theft (raises priority of CSP/SRI fixes in main report).
- 401 before method logic (`PUT /api/user` anon → 401, not 405) = auth-first ordering correct.
- Wrong method `GET /api/login` → 405 `Allow: POST` + Laravel message "The GET method is not supported for route api/login…" — confirms Laravel backend [V] and correct method enforcement.
- TRACE → 405 via Cloudflare. OPTIONS preflight on `/api/login` with legit origin echoes `Access-Control-Allow-Origin: https://www.ictfromabc.com`, `Allow-Methods: POST`, `Max-Age: 0`; with `Origin: https://evil.example` NO ACAO returned [V] — whitelist works, no CORS misconfig. Main page sends no ACAO at all + `Vary: Accept-Encoding` only.

## 2. Input validation bits [V]
- Login phone: client regex `/^07\d+$/` len 10; server 422 envelope `{message, errors{field:[…]}}` observed. Reflected `?phone=<script>` is NOT in static HTML (server shell static; JS sets input value via binding — no innerHTML sink in login node). DOM-XSS via phone param: not observed; would need browser-DOM test (NOT-TESTED).
- Unknown SPA path → proper HTTP 404 size 3058 (SvelteKit), so ffuf 200s are real routes, not fallback. Backup-file sweep (Common-DB-Backups.txt, 336 reqs) = no backup/zip/sql/env/git artifacts found (one junk hit was a `#`-fragment wordlist line resolving to `/`).

## 3. Redirects [V, FINDING]
- `/api` → `Location: http://www.ictfromabc.com/api/` and `/storage` → `http://…/storage/` (both 301, nginx body). https→http downgrade leaks tokens/cookies on hostile networks. Fix: `APP_URL=https`, `TRUSTED_PROXIES`, CF Always-Use-HTTPS + HSTS.

## 4. TLS [V, FINDING]
- nmap ssl-enum-ciphers: TLS 1.0 + 1.1 offered (`ECDHE_ECDSA_WITH_AES_128/256_CBC_SHA`), TLS 1.2 offers CBC alongside GCM/ChaCha, TLS 1.3 clean. Matches nuclei `weak-cipher-suites` + `deprecated-tls`. Action: min TLS 1.2, drop CBC-SHA suites.

## 5. Mail auth [V, WEAK]
- TXT: SPF `v=spf1 include:_spf.smtp.mailtrap.live ~all` (Mailtrap = testing mailer in prod SPF), google-site-verification, Apple `ca3-*` token. DMARC `_dmarc`: `p=none; rua/ruf=…mailtrap.live` (monitoring only, reports to dev mailbox). No MX at apex in this query. Verdict: spoofing/phishing posture weak — move to `p=quarantine→reject`, `-all`, production ESP + aligned DKIM. Mail-plane hosts (cpanel/webmail/mail) exist as names only; logins NOT attempted.

## 6. Origin server [V-info]
- Error-page body on `/api` redirect says `nginx` (no version) — origin stack nginx behind Cloudflare; version not disclosed. No origin IP found (see main report §4).

## 7. Small hardening hygiene [V]
- `security.txt` absent (SvelteKit 404). `version.json` build id exposed (low). `http-opportunistic` advertises `http://` URL (align with https fix). No `X-Powered-By` leak in sampled headers. `Cache-Control: no-cache, private` on API (good). `cf-cache-status: DYNAMIC` on HTML (good — no authed page cached).

## 8. NOT-TESTED (explicitly out of this pass)
OTP send/validate/rate-limit, registration duplicate/phone-enumeration timing, password-update + logout with live token (would mutate session), upload/slip MIME/malware, IDOR beyond own id, stored/reflected XSS payload firing, SQLi, Zoom/SMS endpoints, cPanel logins, Burp active scan, full nuclei http/cves/dast.
