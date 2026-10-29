---
title: Backstage book renamed from platform/ but screenshot asset URLs keep /screenshots/platform/
author: Thammanoon
date: 2026-10-29
branch: docs/rename-platform-to-backstage
cost: { minutes: 2, tokens: 43646 }
id: l-d87698ab
scope: repo
status: active
src: agent
touches:
  - CLAUDE.md
  - README.md
  - assets/screenshots/backstage/.gitkeep
  - assets/screenshots/backstage/activity-events/index.png
  - assets/screenshots/backstage/applications/index.png
  - assets/screenshots/backstage/applications/ui-screens-form.png
  - assets/screenshots/backstage/applications/ui-screens.png
  - assets/screenshots/backstage/broadcasts/index.png
  - assets/screenshots/backstage/broadcasts/ui-screens-form.png
  - assets/screenshots/backstage/broadcasts/ui-screens.png
---

## Decided
- 2026-10-29: book folder en|th/platform/ -> en|th/backstage/ (URL /en/backstage), per user; old /platform pages on dev Wiki.js deleted, no redirect stubs (Wiki.js has no native redirects).
- On-disk screenshots moved to assets/screenshots/backstage/, but the Wiki.js Asset Manager folder stays `screenshots/platform/` so ~already-embedded `/screenshots/platform/...` image URLs keep working. scripts/upload_assets.py ASSET_FOLDER and scripts/embed_screenshots.py URL_PREFIX map backstage -> platform.

## Watch out
- Do not blanket-replace the word "platform": module slugs (platform-config, user-platform, platform-migrations), the "## 7. Platform" nav group, "platform-wide", and carmen-frontend's app title "Carmen Blue Platform" are legit. Only book paths, `book/platform` tags, "Platform book", and "Platform admin" (product sense) were renamed. The seeded role name "Platform Admin" (capital A) is historical and was left.
- zsh does not word-split $FILES; pipe file lists to push_pages.py via xargs.
