# CloudRecon

**Origin IP Discovery & Recon Tool — by [IntSpired](https://intspired.co.uk)**

> A modern, actively maintained replacement for CrimeFlare / CloudPeler — both of which are now dead. CloudRecon uncovers the real IP behind WAFs and CDNs (Cloudflare, Akamai, Fastly, AWS) using entirely free sources, with no proprietary database required.

---

## What It Does

CloudRecon performs passive and active reconnaissance against a target domain, combining multiple free intelligence sources to build a complete picture of the infrastructure:

- **Origin IP discovery** — find the real IP behind Cloudflare and other WAFs
- **Historical DNS** — identify IPs the domain pointed to before WAF migration
- **Subdomain enumeration** — discover forgotten or exposed subdomains
- **Platform fingerprinting** — identify hosting provider, CDN, email platform
- **Security header audit** — flag missing or misconfigured HTTP security headers
- **Threat intelligence** — check domain reputation and passive DNS via OTX AlienVault
- **Certificate transparency** — surface subdomains from historical TLS certificates

---

## Why Not CrimeFlare?

CrimeFlare's backend API (`crimeflare.zidansec.com`) is dead. The domain `crimeflare.com` has expired. The CloudPeler repo was archived in December 2024. **The tool returns nothing.**

CloudRecon replaces it using free, actively maintained sources — and goes further with security header analysis, cookie flag checks, and WAF/CDN detection that CrimeFlare never had.

---

## Sources Used

| Source | Type | Requires Account |
|---|---|---|
| OTX AlienVault | Passive DNS / threat intel | Free account |
| HackerTarget | Subdomain discovery | No |
| crt.sh | Certificate transparency | No |
| Wayback Machine | Historical snapshots | No |
| ipinfo.io | IP enrichment / ASN | No |
| DNS (dig) | Live DNS records | No (local) |
| HTTP headers (curl) | Security posture | No (local) |

---

## Installation

```bash
git clone https://github.com/intspired/CloudRecon.git
cd CloudRecon
```

**Requirements:** Python 3, `dig`, `curl` — all present by default on Kali Linux.

**OTX API key (free):** Register at [otx.alienvault.com](https://otx.alienvault.com), then inject your key:

```bash
sed -i 's/OTX_API_KEY = ""/OTX_API_KEY = "YOUR_KEY_HERE"/' recon.py
```

---

## Usage

```bash
# Full active scan (default)
python3 recon.py target.com

# Passive / OSINT only — zero direct contact with target
python3 recon.py target.com --passive

# Full active scan (explicit)
python3 recon.py target.com --active

# Save results to timestamped file
python3 recon.py target.com --output

# Passive + save
python3 recon.py target.com --passive --output
```

---

## Passive vs Active

| Check | Passive | Active |
|---|---|---|
| OTX historical DNS | ✅ | ✅ |
| HackerTarget subdomains | ✅ | ✅ |
| crt.sh certificate history | ✅ | ✅ |
| Wayback Machine snapshots | ✅ | ✅ |
| IP enrichment (ipinfo.io) | ✅ | ✅ |
| Live DNS records | ❌ | ✅ |
| WAF / CDN detection | ❌ | ✅ |
| Direct IP access test | ❌ | ✅ |
| Subdomain brute force | ❌ | ✅ |
| HTTP security headers | ❌ | ✅ |

**Always run passive first.** Active mode sends real requests to the target and may trigger WAF/IDS alerts.

---

## Output Example

```
  Target:  target.com
  Mode:    ACTIVE — full scan including direct target contact

  [ PASSIVE / OSINT SOURCES ]

  OTX ALIENVAULT (passive DNS / threat intel)
  ·  A    target.com → 104.20.68.142 (2023-04-12T10:22:01)
  ·  A    target.com → 200.100.11.119 (2021-08-03T14:11:45)

  [ ACTIVE SOURCES ]

  WAF / CDN DETECTION
  ⚠  Cloudflare NS    Cloudflare nameservers detected
  ⚠  IP ASN           104.20.68.142 → AS13335 Cloudflare (Cloudflare)

  DIRECT IP ACCESS TEST
  ✔  200.100.11.119   HTTP/1.1 200 OK — responds without Host header!

  HTTP HEADERS & SECURITY POSTURE
  ✘  X-Content-Type-Options   MISSING
  ✘  Referrer-Policy          MISSING
  ⚠  Cookie flags             missing HttpOnly, missing SameSite

  SUMMARY
  ✔  Target      target.com
  ✔  Mode        Full active
  ✔  IPs found   104.20.68.142, 200.100.11.119
  ⚠  Missing headers   X-Content-Type-Options, Referrer-Policy
```

---

## Legal

This tool is intended for **authorised penetration testing and security research only**. Always obtain written permission before scanning any target you do not own.

---

## Author

**IntSpired** | Offensive Cyber & Wireless Security  
[intspired.co.uk](https://intspired.co.uk)

---

## License

MIT
