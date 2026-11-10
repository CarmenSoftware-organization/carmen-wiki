---
title: 2026-09-23 screenshot sync for both books
author: Thammanoon
date: 2026-11-09
id: l-636eaa1c
scope: repo
status: active
touches:
  - scripts/embed_screenshots.py
  - scripts/upload_assets.py
---

## Decided
Screenshots now cover every screen page: Inventory 83/92, Platform 45/49 (EN+TH), merged 2026-09-23 (carmen-wiki 823b6f6).

- Inventory capture: `ShotSpec.wikiTarget` writes straight to curated wiki files — the "two organizations" remap in screenshot_two_organizations is obsolete for mapped shots. Run with `WIKI_CAPTURE_WIKI_ONLY=1`.
- Platform capture: `carmen-platform-e2e` `bun run wiki:capture` → `assets/screenshots/platform/<module>/`, URL `/screenshots/platform/<module>/<file>` (namespaced; inventory URLs unchanged).
- Wiki side: `scripts/embed_screenshots.py` (convention embed, idempotent, `--dry-run`) and `scripts/upload_assets.py` (creates Asset Manager folders via GraphQL; `.sh` is a wrapper).
- Capture target used: `E2E_BASE_URL=https://carmen-inventory.vercel.app` / `https://carmen-inventory-platform.vercel.app`, `E2E_NO_WEBSERVER=1` — local :4000 backend was down; Vercel inventory points at dev :4001.

**Why:** the default capture user `[email]` is in TEST BU, which is unlicensed on dev — every module renders "Permission Denied — not included in your organization's subscription". Use `WIKI_CAPTURE_EMAIL=[email]` (BU ZB01, licensed, data-rich).

## Watch out
always review captured PNGs on contact sheets before embedding (PIL montage in /tmp); capture now throws on login/denied/unlicensed pages. Known gaps: application-config (/system-admin/interface errors on dev), platform landing (auth redirects), dialog-based create forms. Follow-up PRs (wiki #16, inv-e2e #64, plat-e2e #7, opened 2026-09-23) fixed the catalog collision, cluster-admin card grid (`rowSelector`), variant allow-list {detail, form}, and hash-verified uploads. inventory/system-config/query-dataset must never get a screenshot (SQL Workbench moved to Platform 2026-07-09). See screensho
…

_From Claude Code's memory of this repo, last updated Sep 23._
