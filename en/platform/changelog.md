---
title: Changelog
description: The platform's versioned changelog — a JSON-sourced, public /changelog page (now searchable) reached via a version badge in the sidebar and on the landing page.
published: true
date: 2026-07-29T00:00:00.000Z
tags: platform, changelog, versioning, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# Changelog

> **At a Glance**
> **Source of truth:** `src/data/changelog.json` &nbsp;·&nbsp; **Public page:** `/changelog` (no auth), now with a search box over versions/categories/entries &nbsp;·&nbsp; **Discovery:** `VersionBadge` in the sidebar footer + landing page &nbsp;·&nbsp; **Generated artifact:** `CHANGELOG.md` (Keep a Changelog format) &nbsp;·&nbsp; **Release:** `bun run build:bump`.

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
| `/changelog` page | Public route; lists the `unreleased` block (if non-empty) then each released version newest-first, filtered by the search box (§4) when a term is active |
| Sidebar footer | `VersionBadge` shows `v{latest}` linking to `/changelog` |
| Landing page | `VersionBadge` next to the build date |

The current version for the badge is derived from `versions[0].version` (fallback `0.0.0`). `/changelog` is registered as a **public path in the auth guard**, so it renders for signed-out visitors.

## 4. Search

A search box (only rendered when the changelog has any entries at all) filters both the `unreleased` block and released versions as the user types — there is no debounce, since everything is client-side over the already-loaded JSON. A term matches a version card if it appears in the **version number** (e.g. `0.1.1`), a **category label** (`Added`, `Fixed`, …), or the text of **any change entry** under that version — a hit on any one of those keeps the whole version card visible, not just the matching line. Two dedicated empty states cover the no-content cases: "No changelog entries yet" (the changelog is genuinely empty — no `unreleased` content and no released versions) versus "No matching entries" (entries exist, but none match the current search term).

## 5. For developers

- **Add a change:** edit `src/data/changelog.json`, adding strings under the appropriate category inside `unreleased`. Do not touch `CHANGELOG.md`.
- **Cut a release:** `bun run build:bump [patch|minor|major]` (default `patch`) increments the semver, promotes the `unreleased` buffer into a new dated `versions[0]` entry, resets `unreleased` to `{}`, syncs `package.json`, regenerates `CHANGELOG.md`, then builds.
- **Public-path note:** if a route-guard refactor changes how public paths are listed, `/changelog` must stay allowlisted or the page will redirect to sign-in.
- **Search is category/entry-text matching only** — it does not match dates, so searching a date string (e.g. `2026-06-01`) will not surface that version.
