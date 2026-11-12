# ictfromabc.com — Complete Blueprint / Site Map / Folder Structure
Date: 2026-09-11 | Evidence: `D:\Pentesting\ictfromabc\` (endpoints.txt 389 URLs, routes_pages.txt 109, js/ 117 bundles, api_paths_full.txt 106)
Legend: [V] = verified by HTTP/JS evidence · [I] = inferred (SvelteKit convention), do not treat as server paths.

## A. What this site is [V]
- SvelteKit SPA (SSR shell + client-side routing), SMUI + Tailwind, served behind Cloudflare. Every page returns the same HTML shell (~2–6 KB) with different preload bundles; route guards run in browser (localStorage `token` + `role`).
- JSON API at `https://ictfromabc.com/api` (Bearer PAT `id|secret`, Sanctum-consistent format [I-framework, V-format]), FingerprintJS Pro ingress at `https://metrics.ictfromabc.com`.
- No server route manifest is exposed (entry JS has no route table; per-page `node_ids` only in SSR HTML) — the tree below is reconstructed from crawl + bundles, deduped.

## B. Route tree (109 page-routes) [V-existence as SPA routes; auth behavior per §6 of pentest report]
```
/ [V 200]
/public-dashboard [V] /papers/al [V] /papers/ol /papers/ /tutes [V] /ol /about-us /our-team /contact-us /privacy /saga /rusiri /{id}
/auth/login [V] /auth/register [V] /auth/forgot-password [V]  (+ ?phone= carry)
/dashboard/myLessons [V] /all-lessons /ol /tutes /tutes/my-tutes /pastPapers (/pastPapers/al /ol) /model-papers /practical-sessions /reviews /documentation /profile /saga /rusiri
  /pdf/{lessonId} /{lessonId} (dynamic lesson viewer)
/courses/grades /courses/ol-lessons /public/courses/ol-lessons /public/tutes /public-reviews
/purchases/tutes /purchases/bands/free-eligibility /bands/White /tutes/delivery-fee
/lessons/allowed /model-papers/availability /practical-sessions/availability
/email/resend /user/delete
/notifications/* (API-level; frontend bell in dashboard shell)
/blocked [V 200 SPA route, not a WAF page] /contact /contact-us
/admin/* — 57 routes [V as SPA shells]:
  dashboard, courses (+order, /{id} edit), lessons, videos,
  students (+calls, calls/responses, /{id}), users/blocked, users/unverified-nic, users/unverified-email, users/pending-student-calls, pendingNICs, ids/unverified,
  payments (+pending/accepted/requests, /{id}), purchases/accepted, purchases/online, new-year-purchases (+ticket-check),
  tutes (+inventory/packing/transfer/packed/unpacked/csv/pdf/package), tute-packing (+packed),
  past-papers + pastPapers(+/al /ol) [two spellings both exist in bundles], model-papers (+marked/unmarked),
  practical-sessions (+/{id}), tickets (+/{id}, /{id}/status, ticket-categories), reviews (+all, /{id}),
  sms (+send, send-csv, test, sender-options), zoom (+/), tags, ticket-categories,
  allAdmins + all-admins [two spellings] + add-admin + admins/role, profile, user,
  call-responses (+active), student-calls, ticket-categories
/admins/students/ (legacy alias of /admin/students)
/api [V 301→http://…/api/ — downgrade bug]  /storage [V 301→http://…/storage/ — same bug]
/robots.txt [V] /sitemap.xml [V 5 URLs] /_app/version.json [V {"version":"1788800994930"}] /.well-known/http-opportunistic [V]
/forgot-password/request-otp|validate-otp|reset/email — API paths, not pages (in page list only because JS splits base+path).
```

## C. Backend API map (base `https://ictfromabc.com/api`) [V]
Auth (open): `POST /login`, `POST /register (FormData)`, `GET /validate-phone-number/{phone}`, `POST /request-otp-v2/{phone}`, `POST /validate-otp-v2/{phone}`, forgot-password × {phone,email} × {request-otp,validate-otp,reset}, `POST /logout` (auth), `PATCH-via-POST /user` (password change).
Self (Bearer): `GET /user` [V 200], `GET /notifications` [V 200].
Public (Bearer optional): `GET /courses`, `/institutes`, `/public/tutes`, `/telegram` [all V 200 both].
Admin (Bearer ADMIN+; STUDENT→403 [V], anon→401 [V]): `GET /api/admin/courses` (+ full CRUD behind /admin/* UI).
Frontend-only (404 on /api): `/dashboard/myLessons` etc. are SPA routes, not API [V 404].
Error envelope: `{message|msg|errors{field:[…]}}`; 302→`redirect_url`; 401/403→wipe token, bounce `/auth/login` [V from wrapper].

## D. Deployed folder structure (what you can actually download) [V]
```
/
/favicon.jpg  /smui.css
/_app/version.json
/_app/immutable/
  entry/start.B9OgZMnK.js  entry/app.K_xawjjT.js
  chunks/*.js  (~150+: BitTBVkN runtime, Bc7KUd1A UI kit, BJCETRoq, IW6k_RM6 router,
    L4WPQHn8 api-wrapper, B7ab6jJc auth-api, Boci2IdA fingerprint, Bl8ODbBR flags,
    CimyUyqm footer/social, CsaFGerN, CpwLOqZt, MAw91ZOv …)
  nodes/*.js   (~83: 0 layout, 6 login, 51 login-form, + per-route nodes)
  assets/*.css|*.png|*.jpeg (Alert, tailwind, Breadcrumb, password, helpInfo, logos…)
```
Hashes rotate per build (old Wayback hashes ≠ current) — always re-crawl `_app` after a deploy.

## E. Source-tree reconstruction [I — SvelteKit convention, for orientation only]
```
src/routes/
  +layout.svelte  +page.svelte (/)
  public-dashboard/+page …/papers/[level] …/tutes …/saga …/rusiri …/about-us …/our-team …/contact-us …/privacy
  auth/login|register|forgot-password/+page
  dashboard/myLessons|all-lessons|ol|tutes|my-tutes|pastPapers|model-papers|practical-sessions|reviews|documentation|profile|saga|rusiri (+ [id] viewers)
  admin/courses|lessons|videos|students|users|payments|purchases|tutes|past-papers|model-papers|practical-sessions|tickets|reviews|sms|zoom|tags|allAdmins|profile …
src/lib/ apiClient (L4WPQHn8) · authApi (B7ab6jJc) · fingerprint (Boci2IdA) · flags (Bl8ODbBR) · stores (token, role)
```

## F. Data model (from live responses) [V-shape, single-account sample]
- User: whatsapp_number, telegram_number, birthday, course_id (2027-al), medium (S), school, institute_id (2→Sakya Nugegoda), address, nearest_city, district, id_number, first/last name, email, phone_number, last_active_at, verified_id/email.
- Courses: {id (2027-al|2026-al|al-2028…), title, type al, updated_at, telegram_link}.
- Institutes (7): Nanik Gampaha, Sakya Nugegoda, Sipwin Kurunegala, IMS Kandy, Yahansa Kiribathgoda, Online Only, +1.
- Tutes catalog: {id, title, description (EN+SI), …} 52 KB public.
- Notifications: {id UUID, data{msg,link}, read_at, created_at}.
- Login: {msg, token `id|secret`, role STUDENT|ADMIN|SUPER_ADMIN, skippable 0|1, course_id}.

## G. Infra [V]
- www/apex: Cloudflare (172.67.194.222, 104.21.20.239 + IPv6), ports 80/443/8080/8443 CF-proxy, edge cert Google WE1, origin cert Let's Encrypt YE2 (origin hidden — no IP found via CloudRecon/crt.sh/HackerTarget/brute-force).
- metrics.ictfromabc.com: AWS (76.223.2.56, 52.223.59.86), FP-Pro ingress, bare GET 200 empty.
- mt-link.ictfromabc.com: GCP (34.96.69.148), bare GET 404 (standalone service).
- mail plane: cpanel/webmail/cpcontacts/cpcalendars/autodiscover/mail/webdisk (cPanel footprint [I-purpose, V-names]).
- Third parties: Google Fonts (3 families), cdnjs FA 5.15.4, Cloudflare Insights beacon, Fingerprint CDN (fpnpmcdn.net loader ref), YouTube/Facebook/Telegram links.

## H. Key flows [V-logic from JS + 3 live logins]
Login: phone(07…,10d)+password → FP visitorId/score → POST /api/login → store token/role → STUDENT→/dashboard/myLessons (VIDEO_GATE exception path exists but flag off) / ADMIN→/admin/courses; fail→generic message; 401/403 anywhere→wipe+bounce. Register: FormData POST /register. Forgot: request→validate→reset (phone + email variants, OTPv2 variant). Flags: all 9 ENABLE_* currently false → SAGA/RUSIRI/band/countdown/video-gate/popup dormant.

## I. Honesty ledger
Verified: §§A–D,F–G items marked [V] + `route_probe.txt`, `access_control.txt`, `login_test.json`, `me.json`, `nuclei_*`, `ffuf.json`, `cloudrecon_*`. Inferred: framework family (Sanctum-style, not header-confirmed), mail-plane purpose, §E tree, any route's server-side data (all shells are static — real data comes from API). Not mapped: authenticated dashboard/admin SSR data (needs browser session crawl), upload/storage ACLs, OTP rate limits, Zoom/SMS backends.
Next to complete it: authenticated Playwright crawl (captures XHR → full private API list) + `nuclei http/cves` + SPF/DKIM/DMARC. Say the word and I'll run it.
