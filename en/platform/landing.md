---
title: Landing
description: The public marketing page at / — redirects an authenticated session straight to Dashboard, and shows a hardcoded module index that has drifted from the real sidebar.
published: true
date: 2026-09-06T23:45:00.000Z
tags: platform/landing, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Landing

> **At a Glance**
> **Screen:** `Landing` (`/`) &nbsp;·&nbsp; **Access:** fully public — the route carries no `<PrivateRoute>` wrapper at all, not even the bare authenticated-only kind [Dashboard](/en/platform/dashboard) and [Profile](/en/platform/profile) use &nbsp;·&nbsp; **Behaviour:** redirects an already-authenticated session straight to `/dashboard` unconditionally — [Dashboard](/en/platform/dashboard)'s own route guard then decides whether that session actually belongs there (§4) &nbsp;·&nbsp; **Content:** hero + sign-in CTA + a hardcoded three-group "Inside the console" module index + version footer &nbsp;·&nbsp; **Confirmed drift:** the module index still names the removed Print Mapping module and is now missing the majority of the sidebar's real rows (§4)

## 1. Overview

Landing is the signed-out entry point at `/` — a single static marketing page with no data fetching of its own. `<Route path="/" element={<Landing />} />` in `App.tsx` has no `<PrivateRoute>` wrapper whatsoever, unlike every other route in this book; the only routes as unguarded as this one are `/login` and `/changelog`. An already-authenticated visitor never actually sees the marketing content: a `useEffect` checks `isAuthenticated` and immediately `navigate('/dashboard', { replace: true })`s away — the same pattern `Login.tsx` uses for the same reason. While `AuthContext` is still resolving (`loading === true`), the page instead shows a centered "C" mark, a spinner, and "Loading…" — so a returning signed-in visitor typically sees a brief loading flash, then Dashboard, never the hero below. This redirect is deliberately unconditional and does not itself distinguish a platform-authority session from a membership-only cluster admin: per `PrivateRoute`'s own doc comment, "entry points like Login and Landing…read a pre-login snapshot of the context…so they keep sending everyone to `/dashboard` and let this guard route the ones who do not belong there" — a cluster-admin-only visitor is bounced onward from `/dashboard` to `/cluster-admin` by [Dashboard](/en/platform/dashboard)'s own route guard a moment later, not by anything Landing decides.

## 2. Page Content

For a genuinely signed-out visitor, the page renders:

- **Header** — a "C" mark + "Carmen Platform / Operations console" wordmark, and a **Sign in** button linking to `/login`.
- **Hero** — a left-aligned headline ("Run the whole operation from one console."), one sentence of positioning copy, a **Sign in** call-to-action button, and a **"See what's new"** text link to `/changelog` (the one other fully public route, documented on its own page — [Changelog](/en/platform/changelog)).
- **"Inside the console" module index** — three groups of named items rendered as a plain three-column list (no links — each item is inert text, not a navigable tile). See §3 for the exact contents and §4 for how they compare to the real sidebar.
- **Footer** — the shared `VersionBadge` (the same component the sidebar footer uses, documented in [Changelog](/en/platform/changelog) §3), an optional environment label (`REACT_APP_ENV`), a copyright line, and an optional build-date stamp (`REACT_APP_BUILD_DATE`).

## 3. The "Inside the Console" Index

The index is a hardcoded array in `Landing.tsx` (`groups`), not derived from the sidebar's own `NavItem[]` list or from any permission check — it renders identically for every visitor regardless of what they'll actually see once signed in. As authored, it lists:

| Group | Items (as shown on Landing) |
|---|---|
| Organization | Clusters, Business Units, Users, Tenant Migrations |
| Content | Report Templates, **Print Mapping**, News, Broadcasts |
| Platform | Applications, Roles & Access, Super Admins |

## 4. Confirmed Drift: Index vs. Real Sidebar

Direct comparison of `Landing.tsx`'s `groups` array against `ALL_PLATFORM_NAV_ITEMS` — the live sidebar list in `src/components/nav/platformNav.ts` (the same source [Business Units](/en/platform/business-units), [Report Templates](/en/platform/report-templates), and every other module page in this book cites for its own sidebar entry; `Layout.tsx` itself no longer defines nav rows, it only calls `buildPlatformNav()`) — shows the marketing index has drifted much further out of sync than it had at this page's own last review. The real sidebar today has **seven** `groupKey` groups (Organization, License Management, Content, Analytics, Scheduling, Platform, Database, in that order) plus the ungated Dashboard row; Landing's hardcoded index still only knows about three of them:

| Group | Landing's index (as shown) | Sidebar today (`platformNav.ts`) | Gap |
|---|---|---|---|
| Organization | Clusters, Business Units, Users, Tenant Migrations | + Tenant Imports | missing 1 of 5 |
| License Management | *(group does not exist on Landing)* | Licenses, License Feature Groups, License Features | missing 3 of 3 — whole group absent |
| Content | Report Templates, **Print Mapping**, News, Broadcasts | Report Templates, Report Form Groups, News, Broadcasts | lists a dead item; missing Form Groups |
| Analytics | *(group does not exist on Landing)* | Usage Analytics, Activity Events | missing 2 of 2 — whole group absent |
| Scheduling | *(group does not exist on Landing)* | Cronjobs | missing 1 of 1 — whole group absent |
| Platform | Applications, Roles & Access, Super Admins | + Platform Config, Email Settings, User Platform, Feature Flags | missing 4 of 7 |
| Database | *(group does not exist on Landing)* | Platform Migrations, SQL Workbench, Database Pools | missing 3 of 3 — whole group absent |

In prose:

- **Print Mapping is still listed under Content**, even though the print-template-mapping module — sidebar entry included — was deleted from carmen-platform on 2026-07-24 (commit `de11377`). The Landing page's own copy was not touched by that removal commit; confirmed still current — `pages.landing.itemPrintMapping` remains in `Landing.tsx`'s hardcoded Content group as of this task.
- **Report Form Groups is missing from Content** — it shipped the same week as the Print Mapping removal (2026-07-24) and sits in the sidebar's Content group today, but Landing's Content list still only shows the pre-2026-07-24 four items (one of which is the now-dead Print Mapping row).
- **The Platform group is missing four of its current seven rows**: User Platform (part of [Platform RBAC](/en/platform/rbac)), SQL Workbench, and two rows added since this page's own last review — Platform Config and Email Settings (both `navGroup.platform`) — plus Feature Flags, whose own nav entry carries a permission (`feature_flag.manage`) but deliberately no `feature` key of its own, per `platformNav.ts`'s comment: "a switch that could hide itself could never be restored from the UI." Feature Flags now has its own wiki module — [Feature Flags](/en/platform/feature-flags).
- **Three entire groups the current sidebar organizes work into — License Management, Analytics, and Scheduling — have no representation on Landing at all.** These are all modules added after this page's last review: Licenses, License Feature Groups, and License Features (License Management); Usage Analytics and Activity Events (Analytics); Cronjobs (Scheduling).
- **The Database group is also entirely absent**, including SQL Workbench (already flagged above), plus Platform Migrations and Database Pools, both added after this page's last review.

None of this affects behaviour — the index is inert text with no links, read only by a signed-out visitor deciding whether to sign in — but a reader using this page as a feature list would come away with a picture of the console that is missing roughly half of its current administrative surface. This is a documentation-style drift in the product's own marketing copy, not a wiki error; flagged here rather than silently corrected, since fixing `Landing.tsx` itself is outside this wiki's scope.

## 5. Roles and Personas

No authentication and no permission grant of any kind is required to view this page — it is the one screen in the product reachable by an anonymous browser. The only interactive elements are the two navigation links (Sign in → `/login`, See what's new → `/changelog`), neither of which is gated.

## 6. Related Modules

- [Dashboard](/en/platform/dashboard) — where an authenticated session is redirected to, both from this page and from Login, and whose own route guard (not Landing) is what actually separates a platform-authority session from a membership-only cluster admin (§1); the real, permission-filtered module surface that this page's static index is meant to preview.
- [Changelog](/en/platform/changelog) — the other fully public route, linked from the hero's "See what's new" and sharing the `VersionBadge` component with this page's footer.
- [Report Form Groups](/en/platform/report-form-groups), [Platform RBAC](/en/platform/rbac), [SQL Workbench](/en/platform/sql-workbench) — three of the many real screens missing from this page's index (§4); see §4's table for the full accounting, including the three groups (License Management, Analytics, Scheduling) that have no representation on Landing at all.

## 7. Reference Sources

- `../carmen-platform/src/pages/Landing.tsx` — the page: auth-redirect effect, loading state, hero, the hardcoded `groups` array, footer.
- `../carmen-platform/src/pages/Login.tsx` — the sibling public route with the identical already-authenticated redirect pattern.
- `../carmen-platform/src/components/nav/platformNav.ts` — `ALL_PLATFORM_NAV_ITEMS`, the live sidebar list this page's index was compared against in §4. `Layout.tsx` no longer defines nav rows itself — it only calls `buildPlatformNav()`.
- `../carmen-platform/src/components/PrivateRoute.tsx` — the platform-authority/cluster-admin resolution branch quoted in §1, documented in full on [Dashboard](/en/platform/dashboard) §5.
- `../carmen-platform/src/App.tsx:99` — the unwrapped `<Route path="/" element={<Landing />} />` (no `<PrivateRoute>`).
- `../carmen-platform/src/components/VersionBadge.tsx` — the shared version-badge component, documented in full in [Changelog](/en/platform/changelog) §3.

## 8. Pages in This Module

This module is a single page; see the parent [Platform book index](/en/platform).
