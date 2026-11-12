# VULNERABILITIES — verified holes, bugs, exploits (ictfromabc.com)
Date: 2026-09-11 | Evidence: `vuln_probes1/2.txt`, `nuclei_medcrit.txt`, plus prior report files
Scope: safe non-destructive probes only. No OTP sent, no payloads stored, no other users touched.

## V1. Phone-number enumeration oracle [LOW] — CONFIRMED
`GET /api/validate-phone-number/{n}` anon returns `{"exists":true}` for your number, `{"exists":false}` for 0710000000, `400 {"msg":"Invalid Phone Number"}` for garbage. Throttle exists (Limit 20, Remaining 18) but a targeted oracle remains — feeds credential-stuffing lists + tells attackers which numbers receive OTPs.
Fix: require a CAPTCHA/Fingerprint-valid session before answering, or always return 200 with ambiguous body and do the exists-check server-side at OTP-send time.

## V2. https→http redirect downgrade on /api + /storage [MEDIUM] — CONFIRMED
Both 301 to `http://…`. Bearer tokens following the redirect leak off-network. Fix per main report.

## V3. Missing security headers (12) + legacy TLS + no SRI [LOW/INFO] — CONFIRMED
Nuclei 13 info + nmap full cipher table. Raises cost of any future XSS/clickjacking. Fix list in main report.

## V4. Mail posture: SPF softfail via Mailtrap, DMARC p=none to dev mailbox [LOW] — CONFIRMED
`v=spf1 include:_spf.smtp.mailtrap.live ~all`, `p=none; rua/ruf=…mailtrap.live`, no apex MX in query. Phishing-from-your-domain is easy. Fix: production ESP, `-all`, `p=quarantine→reject`.

## V5. Public Telegram invites + course catalog + named reviews [INFO]
By-design but confirm intent: invite hashes, 7 institutes, 52 KB tute catalog, reviews with student full names are world-readable.

## NEGATIVES (tested, held — equally important)
- N1. Nuclei `http/` medium+high+critical, 5802 templates: **0 matches** (engine v3.7.1/templates v10.4.0 outdated — re-run after `-update`).
- N2. RBAC: anon admin APIs 401, STUDENT on admin 403, method tampering (`GET /login`, `POST /courses`) correct 405s with Allow lists.
- N3. CORS: evil origin gets no ACAO on pages or API preflight. TRACE 405.
- N4. Injection: oneligature SQLi probe (`' OR '1'='1`) → clean 422 "Phone number is invalid", no SQL error text. Single probe only — NOT a clean bill, just no low-hanging signal.
- N5. Secrets: no keys/tokens in 117 bundles. Old `/assets/fonts/*` stack gone (404s).
- N6. Login throttle live: `X-RateLimit: 30` on `/api/login` (Remaining 24), `20` on enum endpoint. Brute force slowed, not replaced by lockout evidence (lockout NOT tested to avoid account damage).
- N7. Origin: still hidden after full bypass battery.

## BLOCKED (needs your live session — token dead since first login series)
Authenticated IDOR (`tickets?student=`, purchase/slip objects, notifications of other ids), upload MIME/malware checks, OTP rate-limit/error behavior, logout/password-change flows. Hand me a fresh token captured from YOUR browser devtools (or a test account) and I'll run the authed tier without touching your main device binding — one session, minutes apart, same network.
