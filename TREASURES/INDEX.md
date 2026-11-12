# TREASURES — all findings, organized (2026-09-11)
Target: ictfromabc.com | Source dir: `D:\Pentesting\ictfromabc\`

## reports/ (read these first)
1. REPORT — pentest + vuln scan + architecture
2. BLUEPRINT — full route/API/folder map
3. DEEPDIVE — small security functions
4. DEVICELOCK — device-pause mechanism + admin visibility
5. PUZZLES — LinkFinder/SecretFinder + wayback intel

## recon/ — subdomains, hosts, DNS, ports, crawl, Cloudflare-bypass, wayback
subdomains, active_hosts, dns(+txt/mxns), naabu_ports, nmap(+ssl), endpoints(389), routes_pages(109), route_probe, crt.json, cloudrecon passive+active, wayback_urls + wayback_api

## api/ — endpoints + live auth evidence
api_paths_full(106) + variants, auth_endpoints, access_control matrix, login_test (first 200 + token — ROTATE), login_bad + login_retest (422s), revalidate (401), wayback_telegram + wayback_admindash snapshots

## scans/ — nuclei, ffuf, small-function probes
nuclei_quick (13 info), nuclei_tech_ssl, ffuf.json (7) + ffuf_backup, deepdive_smallfuncs(1+2)

## NOT copied (stay in parent dir)
- me.json (your personal profile PII) — kept out on purpose
- js/, js_todl, login.html, admin/blocked HTML, CloudRecon/, tools/, tools_out/ — raw workdirs, see parent
