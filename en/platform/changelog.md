---
title: Changelog
description: The platform's versioned changelog — a JSON-sourced, public /changelog page reached via a version badge in the sidebar and on the landing page.
published: true
date: 2026-06-09T00:00:00.000Z
tags: platform, changelog, versioning, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# Changelog

> **At a Glance**
> **Source of truth:** `src/data/changelog.json` &nbsp;·&nbsp; **Public page:** `/changelog` (no auth) &nbsp;·&nbsp; **Discovery:** `VersionBadge` in the sidebar footer + landing page &nbsp;·&nbsp; **Generated artifact:** `CHANGELOG.md` (Keep a Changelog format) &nbsp;·&nbsp; **Release:** `bun run build:bump`.

## 1. What & Who

The Changelog is a versioned, **public** record of what shipped in the Carmen Platform admin product. A single JSON file (`src/data/changelog.json`) is the source of truth; the React app imports it statically (no runtime fetch) to render the `/changelog` page, and a Node script regenerates a human-readable `CHANGELOG.md` (Keep a Changelog format) at the repo root. `CHANGELOG.md` is **never hand-edited** — edit the JSON.

**Authored by** developers (under the `unreleased` buffer as they work). **Read by** anyone — the page is public.

## 2. How it's sourced

The JSON holds an `unreleased` buffer plus released `versions` (latest first). Empty categories are omitted for easy authoring:

```
{
  "unreleased": { "Added": ["A feature not yet released"] },
  "versions": [
    {
      "version": "0.1.0",
      "date": "2026-06-01",
      "changes": {
        "Added": ["Public changelog page with version badge"],
        "Fixed": ["Audit dates read from the nested audit object in lists"]
      }
    }
  ]
}
```

Categories use the full Keep a Changelog set, rendered in this order: **Added, Changed, Deprecated, Removed, Fixed, Security**. Change entries are plain strings (no per-entry metadata). Dates are authored as `YYYY-MM-DD` and rendered **verbatim** — the page deliberately avoids `new Date(value)` because parsing a date-only string as UTC midnight shifts it a day earlier for users west of UTC.

## 3. Where it appears

| Surface | Behaviour |
|---|---|
| `/changelog` page | Public route; lists the `unreleased` block (if non-empty) then each released version newest-first |
| Sidebar footer | `VersionBadge` shows `v{latest}` linking to `/changelog` |
| Landing page | `VersionBadge` next to the build date |

The current version for the badge is derived from `versions[0].version` (fallback `0.0.0`). `/changelog` is registered as a **public path in the auth guard**, so it renders for signed-out visitors.

## 4. For developers

- **Add a change:** edit `src/data/changelog.json`, adding strings under the appropriate category inside `unreleased`. Do not touch `CHANGELOG.md`.
- **Cut a release:** `bun run build:bump [patch|minor|major]` (default `patch`) increments the semver, promotes the `unreleased` buffer into a new dated `versions[0]` entry, resets `unreleased` to `{}`, syncs `package.json`, regenerates `CHANGELOG.md`, then builds.
- **Public-path note:** if a route-guard refactor changes how public paths are listed, `/changelog` must stay allowlisted or the page will redirect to sign-in.
