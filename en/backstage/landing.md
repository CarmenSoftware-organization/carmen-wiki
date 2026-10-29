---
title: Landing
description: The public marketing page at / — redirects an authenticated session straight to Dashboard, and shows a hardcoded module index that has drifted from the real sidebar.
published: true
date: 2026-10-29T05:30:00.000Z
tags: backstage/landing, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Landing

> **At a Glance**
> **Screen:** `Landing` (`/`) &nbsp;·&nbsp; **Access:** fully public — the route carries no `<PrivateRoute>` wrapper at all, not even the bare authenticated-only kind [Dashboard](/en/backstage/dashboard) and [Profile](/en/backstage/profile) use &nbsp;·&nbsp; **Behaviour:** redirects an already-authenticated session straight to `/dashboard` unconditionally — [Dashboard](/en/backstage/dashboard)'s own route guard then decides whether that session actually belongs there (§4) &nbsp;·&nbsp; **Content:** hero + sign-in CTA + a hardcoded three-group "Inside the console" module index + version-stamp footer &nbsp;·&nbsp; **Confirmed drift:** the dead Print Mapping row was finally removed on 2026-09-07, but the module index is still missing the majority of the sidebar's real rows (§4)

## 1. Overview

Landing is the signed-out entry point at `/` — a single static marketing page with no data fetching of its own. `<Route path="/" element={<Landing />} />` in `App.tsx` has no `<PrivateRoute>` wrapper whatsoever, unlike every other route in this book; the only routes as unguarded as this one are `/login` and `/changelog`. An already-authenticated visitor never actually sees the marketing content: a `useEffect` checks `isAuthenticated` and immediately `navigate('/dashboard', { replace: true })`s away — the same pattern `Login.tsx` uses for the same reason. While `AuthContext` is still resolving (`loading === true`), the page instead shows a centered "C" mark, a spinner, and "Loading…" — so a returning signed-in visitor typically sees a brief loading flash, then Dashboard, never the hero below. This redirect is deliberately unconditional and does not itself distinguish a Backstage-authority session from a membership-only cluster admin: per `PrivateRoute`'s own doc comment, "entry points like Login and Landing…read a pre-login snapshot of the context…so they keep sending everyone to `/dashboard` and let this guard route the ones who do not belong there" — a cluster-admin-only visitor is bounced onward from `/dashboard` to `/cluster-admin` by [Dashboard](/en/backstage/dashboard)'s own route guard a moment later, not by anything Landing decides.

## 2. Page Content

For a genuinely signed-out visitor, the page renders:

- **Header** — a "C" mark + "Carmen Blue Backstage / Operations console" wordmark, and a **Sign in** button linking to `/login`.
- **Hero** — a left-aligned headline ("Run the whole operation from one console."), one sentence of positioning copy, a **Sign in** call-to-action button, and a **"See what's new"** text link to `/changelog` (the one other fully public route, documented on its own page — [Changelog](/en/backstage/changelog)).
- **"Inside the console" module index** — three groups of named items rendered as a plain three-column list (no links — each item is inert text, not a navigable tile). See §3 for the exact contents and §4 for how they compare to the real sidebar.
- **Footer** — the shared `VersionStamp` (the same component the sidebar footer and the Login page use; since `918a3b8a`, 2026-10-07): the app version `v<CURRENT_VERSION>` linking to `/changelog`, the build commit SHA when `REACT_APP_BUILD_SHA` is set, and the API version (`API v<version>`) fetched from the backend's public `GET /version` with a plain `fetch` (no session needed, so it works on this signed-out page) and silently omitted when the call fails; then an optional environment label (`REACT_APP_ENV`), a copyright line, and an optional build-date stamp (`REACT_APP_BUILD_DATE`). It no longer uses `VersionBadge` as a component — `VersionBadge.tsx` now only exports the `CURRENT_VERSION` and `BUILD_SHA` constants that `VersionStamp` reads.

## 3. The "Inside the Console" Index

The index is a hardcoded array in `Landing.tsx` (`groups`), not derived from the sidebar's own `NavItem[]` list or from any permission check — it renders identically for every visitor regardless of what they'll actually see once signed in. As authored, it lists:

| Group | Items (as shown on Landing) |
|---|---|
| Organization | Clusters, Business Units, Users, Tenant Migrations |
| Content | Report Templates, News, Broadcasts |
| Backstage | Applications, Roles & Access, Super Admins |

## 4. Confirmed Drift: Index vs. Real Sidebar

Direct comparison of `Landing.tsx`'s `groups` array against `ALL_BACKSTAGE_NAV_ITEMS` — the live sidebar list in `src/components/nav/backstageNav.ts` (the same source [Business Units](/en/backstage/business-units), [Report Templates](/en/backstage/report-templates), and every other module page in this book cites for its own sidebar entry; `Layout.tsx` itself no longer defines nav rows, it only calls `buildBackstageNav()`) — shows the marketing index has drifted much further out of sync than it had at this page's own last review. The real sidebar today has **eight** `groupKey` groups (Organization, License Management, Content, Analytics, Scheduling, Backstage, AI, Database, in that order) plus the ungated Dashboard row; Landing's hardcoded index still only knows about three of them (its third group is now labelled "Backstage", via `navGroup.backstage`):

| Group | Landing's index (as shown) | Sidebar today (`backstageNav.ts`) | Gap |
|---|---|---|---|
| Organization | Clusters, Business Units, Users, Tenant Migrations | + Tenant Seed Data, Data Import (the Tenant Migrations, Tenant Seed Data and Data Import rows are drawn as sub-rows under Business Units) | missing 2 of 6 |
| License Management | *(group does not exist on Landing)* | Licenses, License Feature Groups, License Features | missing 3 of 3 — whole group absent |
| Content | Report Templates, News, Broadcasts | Report Templates, Form Groups, Dashboard Templates, News, Broadcasts | missing 2 of 5 (Form Groups, Dashboard Templates) — the dead Print Mapping row was finally removed on 2026-09-07 |
| Analytics | *(group does not exist on Landing)* | Usage Analytics, Activity Events | missing 2 of 2 — whole group absent |
| Scheduling | *(group does not exist on Landing)* | Scheduled Jobs | missing 1 of 1 — whole group absent |
| Backstage | Applications, Roles & Access, Super Admins | + Backstage Config, Email Settings, Backstage Users (+ Backstage Roles inside "Roles & Access"), Feature Flags | missing 4 of 7 |
| AI | *(group does not exist on Landing)* | Purchase Request AI Providers | missing 1 of 1 — whole group absent |
| Database | *(group does not exist on Landing)* | Backstage Migrations, SQL Workbench, Database Pools | missing 3 of 3 — whole group absent |

In prose:

- **Print Mapping is no longer listed** — the dead row this page flagged in its 2026-09-06 revision (the print-template-mapping module was deleted on 2026-07-24, commit `de11377`, but Landing's hardcoded copy kept the item) was removed from `Landing.tsx`'s Content group on 2026-09-07 (commit `344be13`, PR #283, which also dropped the `pages.landing.itemPrintMapping`/`descPrintMapping` i18n keys). Content now lists three items, all of which exist.
- **Form Groups and Dashboard Templates are missing from Content** — Form Groups shipped the same week as the Print Mapping removal (2026-07-24), but PR #283 only deleted the dead row; it did not add the missing one. Dashboard Templates arrived later and is also absent.
- **The Backstage group is missing four of its current seven rows**: Backstage Users (part of [Backstage Roles](/en/backstage/rbac)), and two rows added since this page's own last review — Backstage Config and Email Settings (both `navGroup.backstage`) — plus Feature Flags, whose own nav entry carries a permission (`feature_flag.manage`) but deliberately no `feature` key of its own, per `backstageNav.ts`'s comment: "a switch that could hide itself could never be restored from the UI." Feature Flags now has its own wiki module — [Feature Flags](/en/backstage/feature-flags).
- **Four entire groups the current sidebar organizes work into — License Management, Analytics, Scheduling and AI — have no representation on Landing at all.** These are all modules added after this page's last review: Licenses, License Feature Groups, and License Features (License Management); Usage Analytics and Activity Events (Analytics); Scheduled Jobs (Scheduling); Purchase Request AI Providers (AI).
- **The Database group is also entirely absent**: SQL Workbench, Backstage Migrations and Database Pools.

None of this affects behaviour — the index is inert text with no links, read only by a signed-out visitor deciding whether to sign in — but a reader using this page as a feature list would come away with a picture of the console that is missing roughly half of its current administrative surface. This is a documentation-style drift in the product's own marketing copy, not a wiki error; flagged here rather than silently corrected, since fixing `Landing.tsx` itself is outside this wiki's scope.

## 5. Roles and Personas

No authentication and no permission grant of any kind is required to view this page — it is the one screen in the product reachable by an anonymous browser. The only interactive elements are the two navigation links (Sign in → `/login`, See what's new → `/changelog`), neither of which is gated.

## 6. Related Modules

- [Dashboard](/en/backstage/dashboard) — where an authenticated session is redirected to, both from this page and from Login, and whose own route guard (not Landing) is what actually separates a platform-authority session from a membership-only cluster admin (§1); the real, permission-filtered module surface that this page's static index is meant to preview.
- [Changelog](/en/backstage/changelog) — the other fully public route, linked from the hero's "See what's new" and sharing the `VersionStamp` component with this page's footer.
- [Form Groups](/en/backstage/report-form-groups), [Backstage Roles](/en/backstage/rbac), [SQL Workbench](/en/backstage/sql-workbench) — three of the many real screens missing from this page's index (§4); see §4's table for the full accounting, including the four groups (License Management, Analytics, Scheduling, AI) that have no representation on Landing at all.

## 7. Reference Sources

- `../carmen-backstage/src/pages/Landing.tsx` — the page: auth-redirect effect, loading state, hero, the hardcoded `groups` array, footer.
- `../carmen-backstage/src/pages/Login.tsx` — the sibling public route with the identical already-authenticated redirect pattern.
- `../carmen-backstage/src/components/nav/backstageNav.ts` — `ALL_BACKSTAGE_NAV_ITEMS`, the live sidebar list this page's index was compared against in §4. `Layout.tsx` no longer defines nav rows itself — it only calls `buildBackstageNav()`.
- `../carmen-backstage/src/components/PrivateRoute.tsx` — the Backstage-authority/cluster-admin resolution branch quoted in §1, documented in full on [Dashboard](/en/backstage/dashboard) §5.
- `../carmen-backstage/src/App.tsx:103` — the unwrapped `<Route path="/" element={<Landing />} />` (no `<PrivateRoute>`).
- `../carmen-backstage/src/components/VersionStamp.tsx` (with `src/hooks/useBackendVersion.ts` and `src/services/versionService.ts`) — the footer's version stamp; `src/components/VersionBadge.tsx` now only supplies the `CURRENT_VERSION` / `BUILD_SHA` constants. The version-badge history is in [Changelog](/en/backstage/changelog) §3.

## 8. Pages in This Module

This module is a single page; see the parent [Backstage book index](/en/backstage).
