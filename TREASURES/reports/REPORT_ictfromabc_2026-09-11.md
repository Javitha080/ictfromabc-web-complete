# ictfromabc.com — Active Penetration Test + Vulnerability Scan + Security Architecture Report
Date (UTC): 2026-09-11 | Target: https://ictfromabc.com/ (tested via www.ictfromabc.com)
Method: authorized testing with provided STUDENT account. Only verified outputs below. Inferences are labeled.
Evidence dir: `D:\Pentesting\ictfromabc\`

## 1. Executive summary
- SvelteKit SPA behind Cloudflare. API at `https://ictfromabc.com/api` (Bearer token auth).
- Login with provided creds SUCCEEDED (HTTP 200, role STUDENT). Auth endpoints enforce auth correctly: anon `/api/user` and `/api/notifications` = 401; STUDENT on `/api/admin/courses` = 403 (proper RBAC split).
- No critical/high vulns found in the scans actually run (nuclei exposures+misconfig 1561 templates = 13 info-only; SSL = 2 low + 1 info; ffuf common.txt = 7 paths, no exposed admin/storage listing).
- Real hardening gaps, all verified: missing security headers (12x info), TLS 1.0/1.1 + weak CBC cipher (low), missing SRI on 4 CDN scripts (info), `/api` and `/storage` 301 redirect downgrades https→http, client-side-only admin route shell (200 unauthenticated SPA shell), public Telegram invite links + course/institute catalog, FingerprintJS Pro API key + metrics endpoint enumerable from public JS.
- Cloudflare origin NOT exposed by any method tried (CloudRecon passive+active, crt.sh, HackerTarget, DNS brute-force of 30 origin-ish names). Origin cert is Let's Encrypt (vs Google Trust on edge) but no direct origin IP found.
- Honesty note: OTP brute-force, SQLi/XSS payload firing, and origin direct-hit were deliberately NOT executed. Anything not in evidence files was not tested.

## 2. Toolbox + version audit (your D:\Pentesting)
| Tool | Installed | Latest seen 2026-09 | Status |
|---|---|---|---|
| nmap | 7.98 | 7.991 (2026-08-06) | outdated, minor |
| nuclei engine | v3.7.1 | v3.11.x (Jul 2026) | outdated |
| nuclei-templates (live `~\nuclei-templates`) | v10.4.0 | v10.4.8 | outdated, 94 templates behind per engine banner |
| nuclei-templates-10.3.9.zip (your copy) | 2026-02-16, has only cloud/code/dast/dns/file — NO http/ | — | DO NOT USE for web scans (this is why old `nuclei_*.txt` runs were 0 bytes) |
| subfinder | v2.12.0 | v2.16.0 (2026-08-22) | outdated |
| httpx | v1.8.1 | (update check says outdated) | outdated |
| naabu | v2.4.0 | (update check says outdated) | outdated |
| katana | v1.4.0 | (update check says outdated) | outdated |
| dnsx | v1.2.3 | (update check says outdated) | outdated |
| interactsh-server | v1.2.4 | — | ok for now |
| ffuf | 2.1.0 | 2.2.x (Jul 2026) | outdated |
| gobuster | 3.8.2 (2025-09-04) | — | check `gobuster -v` |
| sqlmap | 1.10.2.17#dev (self-warns outdated) | git HEAD | run `git pull` in `D:\Pentesting\sqlmap` |
| tor | 0.4.9.5 | — | ok |
| DIE | 3.10 portable | — | ok |
| CloudRecon (cloned today to `ictfromabc\CloudRecon`, intspired/CloudRecon) | current HEAD | — | CrimeFlare/CloudPeler are DEAD (backend api dead, domain expired); CloudRecon is the maintained free replacement — used |
Recommendation: update nuclei (`nuclei -update`), templates (`nuclei -ut`), and `*-update` flags for pd tools before retest; `git pull` sqlmap + SecLists.

## 3. Surface map (verified)
- Subdomains (subfinder, 12): mail, webdisk, webmail, metrics, mt-link, www.zoom, zoom, cpanel, cpcontacts, www, autodiscover, cpcalendars (`ictfromabc\subdomains.txt`). cpanel-family = cPanel mail hosting footprint (inference).
- HTTP-live (httpx, 3): `www` 200 (app), `metrics` 200 empty (Fingerprint ingress), `mt-link` 404 Google Cloud (`ictfromabc\active_hosts.txt`).
- DNS (dnsx): www → 172.67.194.222 + 104.21.20.239 (Cloudflare); metrics → 76.223.2.56 + 52.223.59.86 (AWS); mt-link → 34.96.69.148 (GCP) (`ictfromabc\dns.txt`).
- Ports (naabu+nmap): 80/443/8080/8443 only, all "Cloudflare http proxy"; origin hidden (`ictfromabc\naabu_ports.txt`, `nmap.txt`).
- Certs: edge Google Trust WE1 (`*.ictfromabc.com`, valid 2026-07-18→10-16); mt-link Google WR3; metrics Amazon RSA 2048 M04; origin Let's Encrypt YE2 for bare domain (crt.sh) — edge/origin cert split, no key leak.
- crt.sh names: 13 entries incl. zoom/www.zoom (no дополнительных unknown hosts beyond subfinder set).
- robots.txt: `Allow: /public-dashboard/`, sitemap = 5 public URLs. `/_app/version.json` = `{"version":"1788800994930"}` (build id). `/.well-known/security.txt` = SvelteKit 404 (not implemented).

## 4. Cloudflare bypass (GitHub tooling, as requested)
- Cloned `intspired/CloudRecon` (CloudFlair needs paid Censys keys; CrimeFlare/CloudPeler backend is dead — verified via project README).
- Passive: OTX 0 pulses / no passive DNS; HackerTarget confirms CF/AWS/GCP split; CT lists known names only; Wayback snapshots 2021 + 2024-06/08 (`cloudrecon_passive.txt`).
- Active: DNS brute-force (mail/ftp/cpanel/direct/origin/server/admin/dev/test/staging/api/vpn/…) = no record; headers confirm Cloudflare platform; missing-headers list matches nuclei; direct-IP test = none found (`cloudrecon_active.txt`).
- Verdict: NO origin IP disclosed. Do not hammer Cloudflare IP ranges; next step would be authorized origin-log review, not more bypass brute force.

## 5. Crawl + JS/API discovery (the "hidden things")
- katana: 389 URLs (`endpoints.txt`). SPA routes found: `/auth/login?phone=`, `/auth/register`, `/auth/forgot-password`, `/dashboard/*` (myLessons, all-lessons, tutes/my-tutes, pastPapers, model-papers, practical-sessions, reviews, documentation, profile, saga, rusiri, ol), `/admin/*` (courses, lessons, students, calls, pendingNICs, payments pending/accepted/requests, purchases, tutes + inventory/packing/transfer, past-papers/papers, model-papers marked/unmarked, practical-sessions, tickets + categories, reviews, sms, zoom, tags, users blocked/unverified-nic/unverified-email, allAdmins/add-admin, dashboard), `/public-dashboard/*`, `/purchases/*`, `/bands/White`, `/tutes/delivery-fee`, `/api`, `/user/delete`, `/email/resend`, `/lessons/allowed`, `/notifications/*`, forgot-password OTP email endpoints.
- Downloaded 34 `js/all` + 83 `js/nodes` bundles. API wrapper (`chunks/L4WPQHn8.js`) VERIFIED: base `https://ictfromabc.com/api`, Bearer from localStorage, JSON, 302→redirect_url, 401/403→wipe token + `/auth/login`, error unpack `message|msg|errors[0]`.
- Auth API (`chunks/B7ab6jJc.js`) VERIFIED: `POST /login {phoneNumber,password,visitorId,confidenceScore}`, `POST /register (FormData)`, `POST /logout`, `PATCH-via-POST /user {_method:PATCH,…}`, forgot-password phone+email request/validate/reset, OTPv2 request/validate, `GET /validate-phone-number/{phone}`.
- Fingerprint (`chunks/Boci2IdA.js` = FingerprintJS Pro v3.12.15) VERIFIED: `apiKey rDaS5GdGD0S43aJ8ry6f`, endpoint `https://metrics.ictfromabc.com`, loader `metrics…/web/v<version>/<apiKey>/loader_v<loaderVersion>.js`; login sends visitorId+confidenceScore.
- Flags (`chunks/Bl8ODbBR.js`): ALL false (`!1`): BAND_PURCHASE, AL_COUNTDOWN, VIDEO_GATE, SAGA(+ADMIN, +QR_SEND), RUSIRI, CHRISTMAS_TREE, POPUP_MESSAGE.
- Login node: phone regex `/^07\d+$/` len 10; role routing STUDENT→`/dashboard/myLessons` (VIDEO_GATE exception for 2027-al? current build flag off), ADMIN/SUPER_ADMIN→`/admin/courses`; `?phone=` carried to register/forgot; "Token Error" catch.
- Full path list: `api_paths_full.txt` (106 literals, 103 interesting). Socials: youtube.com/c/RavinduBandaranayake, facebook.com/ictfromabc. Telegram links served by API (see §7).

## 6. Auth + access control (with your STUDENT creds; 3 login POSTs total, no brute force)
- Valid login `POST /api/login` → 200 `{"msg":"Login Successful","token":"1023295|…","role":"STUDENT","skippable":1,"course_id":"2027-al"}` (`login_test.json`; full token kept in that file — ROTATE it after testing). Format `id|secret` is consistent with Laravel Sanctum PAT (inference, header does not confirm framework).
- `GET /api/user` with token → 200 own profile (PII redacted here; raw in `me.json`); anon → 401 `Unauthenticated.` CORRECT.
- `GET /api/notifications` auth → 200 (items with UUIDs, e.g. model-paper notice 2026-08); anon → 401. CORRECT.
- `GET /api/admin/courses` STUDENT → 403 `Unauthorized`; anon → 401. CORRECT RBAC (403≠401 split is proper).
- `GET /api/dashboard/myLessons` → 404 both (frontend route, not API — confirms SPA/API split, not a vuln).
- Wrong-password login → 422 `Phone number is required (and 3 more errors)` flagging all four fields despite being sent (`login_bad.json`). ANOMALY (not a confirmed vuln): valid creds + dummy fingerprint got 200, wrong password + same dummy fingerprint got 422. Likely fingerprint/validation-branch behavior; retest from a real browser session before judging. No account lockout message observed on ONE bad attempt (lockout policy NOT tested — would need rate testing you did not authorize to hammer).
- OTP endpoints enumerated, NOT exercised (no OTP sent/brute-forced).

## 7. More verified API behavior (safe GETs, auth vs anon)
| Endpoint | auth | anon | Note |
|---|---|---|---|
| /api/courses | 200 catalog (A/L 2028/2027/2026…) | 200 same | public by design |
| /api/institutes | 200 (7 institutes) | 200 | public by design |
| /api/public/tutes | 200, 52 KB | 200 | public by design |
| /api/telegram | 200 invite links (t.me/ictfromabc28, +invite hashes) | 200 | PUBLIC — consider gating to enrolled students |
| full matrix | — | — | `access_control.txt` |

## 8. Vulnerability scans (what actually ran)
- nuclei exposures+misconfig (1561 templates, live store): 13 matches, ALL info — 12× missing/weak security headers + missing-SRI on 4 CDN URLs (font-awesome 5.15.4, 3× Google Fonts) (`nuclei_quick.txt`).
- nuclei ssl/tech (partial, run timed out at 5 min on ssl set): captured `weak-cipher-suites tls-1.0 + tls-1.1 (ECDHE_ECDSA_WITH_AES_128_CBC_SHA)` [low] ×2, `deprecated-tls tls_1.0` [info] (`nuclei_tech_ssl.txt`). Cloudflare edge still negotiates legacy TLS — lower to TLS 1.2+ minimum.
- ffuf common.txt (4751 reqs): 7 hits — `/admin` 200 SPA shell (client-side guard only; admin JS publicly fetchable), `/api` 301→`http://…/api/` (!), `/storage` 301→`http://…/storage/` (!), `/blocked` 200 SPA shell, `/robots.txt`, `/sitemap.xml`, `/.well-known/http-opportunistic` 200 `["http://www.ictfromabc.com"]` (`ffuf.json`).
- Downgrade finding is REAL (both Location headers say `http://`): fix server-side `APP_URL`/proxy (`X-Forwarded-Proto`) handling so https stays https.
- nikto/Burp intrusive scan, sqlmap, XSS/SQLi payloads: NOT RUN (would need explicit destructive-testing approval + staging target).

## 9. UI/UX review (observed, no fakes)
- SvelteKit + SMUI + Tailwind; Roboto/Fredoka; FontAwesome 5.15.4 (2019-era, SRI missing); Cloudflare Insights beacon.
- Public funnel: landing → public-dashboard (papers al/ol, tutes, about/our-team, contact, privacy) → auth. Login UX: phone-first (10-digit 07…), password step, forgot-password + create-account preserve phone, generic "Login failed" (good), per-field phone validation (good).
- Student shell: myLessons/all-lessons, tutes, past/model papers, practical sessions, saga/rusiri (currently flag-gated off), reviews, documentation, profile, notifications (read-all/delete-all), payment slip upload + status/audit modals, file viewer, ticket system.
- Admin shell (JS-visible): student lifecycle (calls/responses, NIC/email verification, blocked), course/lesson ordering, tute inventory/packing/transfer/csv/pdf, payments review (pending/accepted/requests, online), purchases incl. new-year ticket-check, past/model paper marking, practical sessions, Zoom mgmt, SMS (send/csv/test/sender-options), tickets, reviews, call-responses, pendingNICs, role admin (allAdmins/add-admin/role).
- A11y/robustness nits (info): missing CSP/X-Frame/SRI weakens tab-nabbing/clickjacking posture for an education checkout flow; toast stacks ×7 containers fine.

## 10. Security architecture deep dive
- Edge: Cloudflare (proxy, H3, NEL, DYNAMIC cache for HTML, Google Trust edge cert). Origin hidden; Let's Encrypt cert on bare domain suggests origin terminates TLS itself behind CF (normal).
- App: SvelteKit frontend (SSR shell + CSR routes) + JSON API (`/api`) with Sanctum-style Bearer PATs in localStorage; 401/403 handling + login bounce is coherent.
- Bot/fraud: FingerprintJS Pro (metrics.ictfromabc.com ingress, AWS) + visitorId/confidenceScore on login. Key is public by design (client key) but restrict its allowed origins in the Fingerprint dashboard.
- Data: roles STUDENT/ADMIN/SUPER_ADMIN; student PII via `/api/user`; payments slips + NIC/email verification flows = sensitive-doc handling — ensure storage is private (the `/storage` 301 is just a redirect, not a listing, but verify no public disk symlink).
- Infra split: app on Cloudflare-fronted host; mt-link on GCP (404 standalone); metrics on AWS (FP ingress); mail/cPanel footprint (cpanel/webmail/autodiscover) = separate mail plane — verify SPF/DKIM/DMARC for ictfromabc.com (not checked — add).
- Missing: security.txt, CSP/HSTS/X-Frame/Permissions-Policy/Referrer-Policy/X-Content-Type-Options, SRI, TLS min-version, https-preserving redirects, OTP rate-limit evidence.

## 11. Hidden/noteworthy (all verified)
- build id `1788800994930`; `/blocked` SPA route (not a WAF page); http-opportunistic advertises plain-http origin URL; Wayback `.well-known/ai-plugin.json, assetlinks.json, gpc.json, trust.txt…` (historical interest, not fetched for vulns); admin bundle URLs public without auth (expected for SPA, but don't embed secrets — none found in the 117 files grepped); public Telegram invite hashes; course ids `2027-al`, `al-2028`; login `?phone=` reflected into form (benign, encoded).

## 12. What was NOT done (so you know what's still open)
OTP send/validate/brute-force, registration abuse, SQLi/XSS/SSTI payloads, IDOR beyond own account, payment-slip upload malware/mime tests, Zoom/SMS abuse, origin direct-IP hit, mail-record (SPF/DKIM/DMARC) check, Burp full crawl, nuclei full `http/` + `cves/` + `dast` sets, gobuster/feroxbuster large lists, sqlmap. Say the word with a staging scope and I'll run the next tier.

## 13. Fixes, priority order
1. Force https redirects (`/api`, `/storage` → https Location) + enable HSTS (preload only after https is clean).
2. Add CSP (start report-only; allow self, fonts.googleapis/gstatic, cdnjs with hashes), X-Frame-Options SAMEORIGIN (or frame-ancestors), X-Content-Type-Options nosniff, Referrer-Policy strict-origin-when-cross-origin, Permissions-Policy (camera/mic/geolocation=()), remove `X-Powered-By`-style leaks if any.
3. Cloudflare SSL → TLS 1.2 minimum; drop TLS 1.0/1.1 + CBC suites.
4. Add SRI (or self-host) for font-awesome/Google Fonts; consider upgrading FA 5.15.4.
5. Gate `/api/telegram` + course Telegram links to enrolled/authenticated students if exclusivity matters.
6. Fingerprint dashboard: lock `rDaS5…` key to `ictfromabc.com` origins; monitor confidence< threshold logins.
7. Add `/.well-known/security.txt` with contact + expiry; keep robots minimal (fine as-is).
8. Rotate the test token (`1023295|…` in `login_test.json`) + confirm only ONE active session per device if policy requires.
9. Re-run: `nuclei -ut`, full `http/`+`ssl`+`misconfig` + authenticated crawl with(Build:
 `nuclei -u https://www.ictfromabc.com -t ~\nuclei-templates\http\ -severity medium,high,critical`), plus SPF/DKIM/DMARC + backup/zip/old-file checks.
10. Update the toolbox (§2) before the next round.

## 14. Appendix — evidence files
`subdomains.txt, active_hosts.txt, dns.txt, naabu_ports.txt, nmap.txt, endpoints.txt (389), crt.json, wayback_urls.txt, login.html, js/ + js/all + js/nodes (117), api_paths*.txt, api_paths_full.txt (106), access_control.txt, login_test.json, login_bad.json, me.json (PII — handle carefully), notifications (in access_control), nuclei_quick.txt (13), nuclei_tech_ssl.txt (3), ffuf.json (7), blocked.html, admin.html, cloudrecon_passive/active.txt, CloudRecon/ (tool), version/robots/sitemap notes in §3.`
Raw PII/token files stay local; report text above is redacted on purpose.
