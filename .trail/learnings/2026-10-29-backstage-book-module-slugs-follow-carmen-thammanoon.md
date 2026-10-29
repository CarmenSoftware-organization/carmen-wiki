---
title: "Backstage book: module slugs follow carmen-backstage, but screenshot asset URLs keep /screenshots/platform/"
author: Thammanoon
date: 2026-10-29
branch: docs/rename-backstage-modules-2026-10-29
cost: { minutes: 1, tokens: 4666 }
id: l-2d4f3360
scope: repo
status: active
replaces: l-d87698ab
src: agent
touches:
  - scripts/upload_assets.py
  - scripts/embed_screenshots.py
  - scripts/nav-overrides.yaml
---

## Decided
- 2026-10-29: book folder en|th/platform/ -> en|th/backstage/ (URL /en/backstage); old /platform pages deleted on dev Wiki.js, no redirect stubs (Wiki.js has no native redirects).
- Same day, module slugs renamed to match carmen-backstage routes/i18n: platform-config -> backstage-config ("Backstage Config"), user-platform -> user-backstage ("Backstage Users", nav.userBackstage), platform-migrations -> backstage-migrations ("Backstage Migrations"); index group "7. Platform" -> "7. Backstage". Names come from carmen-backstage src/components/nav/backstageNav.ts + src/i18n/en.ts.
- Wiki.js asset folder stays `screenshots/platform/<module>/` (on disk: assets/screenshots/backstage/<module>/). scripts/upload_assets.py ASSET_FOLDER and scripts/embed_screenshots.py URL_PREFIX map backstage -> platform. Module subfolders DO follow the new slugs (re-uploaded 4 PNGs).

## Watch out
- Lowercase "platform" stays where it means the shared platform DB/schema ("platform migrations `2026...`", "platform-wide", "platform config" as a generic noun), in repo code paths (carmen-backstage-e2e tests/user-platform/...), and in rbac.md's history of the role rename "Platform Admin" -> "Backstage Admin".
- Don't `git stash` / `stash pop` with staged renames to compare dry-runs: pop drops the index, and the next commit silently holds only the new files. Re-`git add -A` before committing.
- zsh does not word-split $FILES; pipe file lists to push_pages.py via xargs.
