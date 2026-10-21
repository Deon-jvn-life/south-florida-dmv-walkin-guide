# South Florida DMV Walk-in Guide (static site)

Unofficial, independent guide to walk-in vs appointment rules at driver license and ID offices in Broward, Miami-Dade and Palm Beach.

- `tools/flhsmv_raw.json`: office rows parsed from the FLHSMV county location pages (driver license and dual service centres used; motor vehicle only rows ignored).
- `tools/build.py`: generator, writes `site/` and `tools/offices_parsed.json`. Walk-in policies come from each county tax collector site.
- BASE: https://south-florida-dmv-walkin-guide.vercel.app

Last checked: 21 Oct 2026.
