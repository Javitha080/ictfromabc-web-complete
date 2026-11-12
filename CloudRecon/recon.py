#!/usr/bin/env python3
"""
CloudRecon - Origin IP Discovery & Recon Tool
By IntSpired | Offensive Cyber & Wireless Security
Replacement for CrimeFlare using free, no-account-required sources

Usage:
  python3 recon.py <domain>                  # full active scan
  python3 recon.py <domain> --passive        # passive/OSINT only
  python3 recon.py <domain> --active         # full active scan (explicit)
  python3 recon.py <domain> --output         # save results to file
  python3 recon.py <domain> --passive --output
"""

import sys
import re
import json
import subprocess
import urllib.request
from datetime import datetime

# ── Colours ────────────────────────────────────────────────────────────────────
R  = "\033[91m"
G  = "\033[92m"
Y  = "\033[93m"
B  = "\033[94m"
C  = "\033[96m"
W  = "\033[97m"
DIM= "\033[2m"
RST= "\033[0m"

OTX_API_KEY = ""

BANNER = f"""
{C}
  ██████╗██╗      ██████╗ ██╗   ██╗██████╗ ██████╗ ███████╗ ██████╗ ██████╗ ███╗   ██╗
 ██╔════╝██║     ██╔═══██╗██║   ██║██╔══██╗██╔══██╗██╔════╝██╔════╝██╔═══██╗████╗  ██║
 ██║     ██║     ██║   ██║██║   ██║██║  ██║██████╔╝█████╗  ██║     ██║   ██║██╔██╗ ██║
 ██║     ██║     ██║   ██║██║   ██║██║  ██║██╔══██╗██╔══╝  ██║     ██║   ██║██║╚██╗██║
 ╚██████╗███████╗╚██████╔╝╚██████╔╝██████╔╝██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║
  ╚═════╝╚══════╝ ╚═════╝  ╚═════╝ ╚═════╝ ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝╚═╝  ╚═══╝
{RST}{DIM}  Origin IP Discovery & Recon Tool — by IntSpired{RST}
  {DIM}Free sources: DNS · ipinfo.io · crt.sh · HackerTarget · Wayback · OTX{RST}
"""

COMMON_SUBS = [
    "mail","ftp","cpanel","webmail","direct","origin","server",
    "admin","dev","test","staging","api","portal","vpn","remote",
    "ns1","ns2","smtp","pop","imap","autodiscover","lyncdiscover",
    "shop","store","blog","old","backup","secure","login","support"
]

_output_lines = []

# ── Helpers ────────────────────────────────────────────────────────────────────

def _print(text=""):
    print(text)
    clean = re.sub(r'\033\[[0-9;]*m', '', text)
    _output_lines.append(clean)

def dig(name, rtype="A"):
    try:
        result = subprocess.run(
            ["dig", "+short", rtype, name],
            capture_output=True, text=True, timeout=10
        )
        return [l.strip() for l in result.stdout.strip().splitlines() if l.strip()]
    except Exception:
        return []

def fetch_json(url, headers=None):
    try:
        req = urllib.request.Request(url, headers=headers or {
            "User-Agent": "CloudRecon/1.0 (+https://intspired.co.uk)"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None

def fetch_text(url):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": "CloudRecon/1.0 (+https://intspired.co.uk)"
        })
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.read().decode(errors="replace")
    except Exception:
        return None

def curl_headers(url):
    try:
        result = subprocess.run(
            ["curl", "-sI", "--max-time", "10", url],
            capture_output=True, text=True, timeout=15
        )
        headers = {}
        for line in result.stdout.splitlines()[1:]:
            if ":" in line:
                k, _, v = line.partition(":")
                headers[k.strip().lower()] = v.strip()
        status = result.stdout.splitlines()[0].strip() if result.stdout else ""
        return status, headers
    except Exception:
        return "", {}

def section(title):
    _print(f"\n{B}{'─'*60}{RST}")
    _print(f"{Y}  {title}{RST}")
    _print(f"{B}{'─'*60}{RST}")

def ok(label, value):   _print(f"  {G}✔{RST}  {W}{label:<26}{RST} {value}")
def warn(label, value): _print(f"  {Y}⚠{RST}  {W}{label:<26}{RST} {Y}{value}{RST}")
def bad(label, value):  _print(f"  {R}✘{RST}  {W}{label:<26}{RST} {R}{value}{RST}")
def info(label, value): _print(f"  {C}·{RST}  {W}{label:<26}{RST} {value}")

# ── Passive modules ─────────────────────────────────────────────────────────────

def otx_recon(domain):
    section("OTX ALIENVAULT (passive DNS / threat intel)")
    headers = {"X-OTX-API-KEY": OTX_API_KEY}
    base    = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}"

    data = fetch_json(f"{base}/passive_dns", headers=headers)
    ips  = []
    if data and data.get("passive_dns"):
        for record in data["passive_dns"][:10]:
            rtype    = record.get("record_type", "?")
            hostname = record.get("hostname", "?")
            address  = record.get("address", "?")
            first    = record.get("first", "?")
            info(rtype, f"{hostname} → {address} ({first})")
            if rtype == "A" and address:
                ips.append(address)
    else:
        info("OTX Passive DNS", "No records found")

    data = fetch_json(f"{base}/general", headers=headers)
    if data:
        info("Pulse count", str(data.get("pulse_info", {}).get("count", 0)))

    return list(set(ips))

def ip_enrichment(ips):
    section("IP ENRICHMENT (ipinfo.io)")
    enriched = []
    for ip in ips:
        data = fetch_json(f"https://ipinfo.io/{ip}/json")
        if data:
            ok("IP",             data.get("ip", ip))
            info("Hostname",     data.get("hostname", "n/a"))
            info("Organisation", data.get("org", "n/a"))
            info("Location",     f"{data.get('city','')}, {data.get('region','')}, {data.get('country','')}")
            info("Postal",       data.get("postal", "n/a"))
            info("Timezone",     data.get("timezone", "n/a"))
            enriched.append(data)
        else:
            warn("IP", f"{ip} — enrichment failed")
    return enriched

def hackertarget(domain):
    section("HACKERTARGET SUBDOMAIN SEARCH")
    text  = fetch_text(f"https://api.hackertarget.com/hostsearch/?q={domain}")
    found = []
    if text and "error" not in text.lower():
        for line in text.strip().splitlines():
            parts = line.split(",")
            if len(parts) == 2:
                ok(parts[0], parts[1])
                found.append((parts[0], parts[1]))
    else:
        info("HackerTarget", "No results or rate limited")
    return found

def crtsh(domain):
    section("CERTIFICATE TRANSPARENCY (crt.sh)")
    data  = fetch_json(f"https://crt.sh/?q={domain}&output=json")
    names = set()
    if data:
        for entry in data:
            for name in entry.get("name_value", "").splitlines():
                name = name.strip().lstrip("*.")
                if domain in name:
                    names.add(name)
        for n in sorted(names):
            info("CT Entry", n)
        if not names:
            info("crt.sh", "No subdomains found in certificate logs")
    else:
        info("crt.sh", "No certificate records found")
    return list(names)

def wayback(domain):
    section("WAYBACK MACHINE (historical snapshots)")
    url  = f"http://web.archive.org/cdx/search/cdx?url={domain}&output=json&limit=5&fl=timestamp,original&filter=statuscode:200"
    data = fetch_json(url)
    if data and len(data) > 1:
        for row in data[1:6]:
            info(row[0], row[1][:80])
    else:
        info("Wayback", "No snapshots found")

# ── Active modules ──────────────────────────────────────────────────────────────

def dns_recon(domain):
    section("DNS RECORDS  [ACTIVE]")
    results = {}
    a = dig(domain, "A")
    results["a"] = a
    for ip in a:
        ok("A Record", ip)
    if not a:
        bad("A Record", "none found")
    for r in dig(domain, "NS"):
        info("NS", r)
    for r in dig(domain, "MX"):
        info("MX", r)
    for r in dig(domain, "TXT"):
        info("TXT", r[:80] + ("…" if len(r) > 80 else ""))
    return results

def waf_check(domain, ips):
    section("WAF / CDN DETECTION  [ACTIVE]")
    ns    = dig(domain, "NS")
    cf_ns = any("cloudflare" in n.lower() for n in ns)
    if cf_ns:
        warn("Cloudflare NS", "Cloudflare nameservers detected")
    else:
        ok("Cloudflare NS", "Not using Cloudflare NS")

    for ip in ips:
        data = fetch_json(f"https://ipinfo.io/{ip}/json")
        if data:
            org = data.get("org", "")
            if "13335" in org or "cloudflare" in org.lower():
                warn("IP ASN", f"{ip} → {org} (Cloudflare)")
            elif "amazon" in org.lower() or "aws" in org.lower():
                info("IP ASN", f"{ip} → {org} (AWS/Amazon)")
            elif "akamai" in org.lower():
                warn("IP ASN", f"{ip} → {org} (Akamai)")
            elif "fastly" in org.lower():
                warn("IP ASN", f"{ip} → {org} (Fastly)")
            else:
                ok("IP ASN", f"{ip} → {org}")

def subdomain_check(domain):
    section("SUBDOMAIN ENUMERATION  [ACTIVE]")
    found = []
    for sub in COMMON_SUBS:
        fqdn = f"{sub}.{domain}"
        ips  = dig(fqdn, "A")
        if ips:
            ok(fqdn, ", ".join(ips))
            found.append((fqdn, ips))
        else:
            _print(f"  {DIM}  {fqdn:<42} no record{RST}")
    return found

def http_headers(domain):
    section("HTTP HEADERS & SECURITY POSTURE  [ACTIVE]")
    status, headers = curl_headers(f"https://{domain}")
    if status:
        info("Status", status)

    checks = {
        "server":                   ("Platform",               "info"),
        "strict-transport-security":("HSTS",                   "ok"),
        "content-security-policy":  ("CSP",                    "ok"),
        "x-content-type-options":   ("X-Content-Type-Options", "ok"),
        "referrer-policy":          ("Referrer-Policy",        "ok"),
        "permissions-policy":       ("Permissions-Policy",     "ok"),
        "x-frame-options":          ("X-Frame-Options",        "ok"),
    }

    missing = []
    for key, (label, _) in checks.items():
        val = headers.get(key)
        if val:
            if key == "server":
                info(label, val)
            else:
                ok(label, val[:80])
        else:
            if key != "server":
                missing.append(label)
                bad(label, "MISSING")

    cookie = headers.get("set-cookie", "")
    if cookie:
        flags = []
        if "httponly" not in cookie.lower(): flags.append("missing HttpOnly")
        if "samesite" not in cookie.lower(): flags.append("missing SameSite")
        if "secure"   not in cookie.lower(): flags.append("missing Secure")
        if flags:
            warn("Cookie flags", ", ".join(flags))
        else:
            ok("Cookie flags", "HttpOnly + SameSite + Secure present")

    return missing

def direct_ip_test(domain, ips):
    section("DIRECT IP ACCESS TEST  [ACTIVE]")
    for ip in ips:
        status, _ = curl_headers(f"http://{ip}")
        if status:
            if "400" in status or "403" in status:
                ok(ip, f"{status} — hostname-dependent (good)")
            elif "200" in status:
                warn(ip, f"{status} — responds without Host header!")
            else:
                info(ip, status)
        try:
            result = subprocess.run(
                ["curl", "-sI", "--max-time", "10", f"http://{ip}", "-H", f"Host: {domain}"],
                capture_output=True, text=True, timeout=15
            )
            first = result.stdout.splitlines()[0].strip() if result.stdout else "no response"
            info(f"{ip} (Host: {domain})", first)
        except Exception:
            pass

# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        print(BANNER)
        print(f"  {Y}Usage:{RST}")
        print(f"    python3 recon.py <domain>                  full active scan (default)")
        print(f"    python3 recon.py <domain> --passive        passive/OSINT only")
        print(f"    python3 recon.py <domain> --active         explicit full active scan")
        print(f"    python3 recon.py <domain> --output         save results to file")
        print(f"    python3 recon.py <domain> --passive --output\n")
        sys.exit(0)

    domain  = args[0].lower().strip()
    if domain.startswith("http"):
        domain = domain.split("//")[-1].split("/")[0]

    passive = "--passive" in args
    save    = "--output"  in args

    print(BANNER)
    _print(f"\n  {W}Target:{RST}  {C}{domain}{RST}")
    _print(f"  {W}Time:{RST}    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    _print(f"  {Y}Mode:{RST}    {'PASSIVE — no direct contact with target' if passive else 'ACTIVE — full scan including direct target contact'}")

    # ── Passive sources (always run) ───────────────────────────────────────────
    _print(f"\n{G}  [ PASSIVE / OSINT SOURCES ]{RST}")

    otx_ips = otx_recon(domain)
    hackertarget(domain)
    crtsh(domain)
    wayback(domain)

    if otx_ips:
        ip_enrichment(otx_ips)

    # ── Active sources ─────────────────────────────────────────────────────────
    ips     = otx_ips
    missing = []

    if not passive:
        _print(f"\n{R}  [ ACTIVE SOURCES — DIRECT TARGET CONTACT ]{RST}")
        dns  = dns_recon(domain)
        ips  = dns.get("a", [])

        if ips:
            ip_enrichment(ips)
            waf_check(domain, ips)
            direct_ip_test(domain, ips)
        else:
            warn("Note", "No A records found — skipping IP checks")

        subdomain_check(domain)
        missing = http_headers(domain)

    # ── Summary ────────────────────────────────────────────────────────────────
    section("SUMMARY")
    ok("Target",   domain)
    ok("Mode",     "Passive only" if passive else "Full active")
    ok("IPs found", ", ".join(ips) if ips else "none found")
    if missing:
        warn("Missing headers", ", ".join(missing))
    elif not passive:
        ok("Security headers", "All key headers present")

    _print(f"\n  {DIM}CloudRecon by IntSpired — intspired.co.uk{RST}\n")

    # ── Save to file ───────────────────────────────────────────────────────────
    if save:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"cloudrecon_{domain}_{timestamp}.txt"
        with open(filename, "w") as f:
            f.write("\n".join(_output_lines))
        print(f"\n  {G}✔{RST}  Results saved to {W}{filename}{RST}\n")

if __name__ == "__main__":
    main()
