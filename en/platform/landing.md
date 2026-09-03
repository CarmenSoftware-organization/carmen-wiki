---
title: Landing
description: The public marketing page at / — redirects an already-authenticated session straight to Dashboard, and shows a hardcoded "Inside the console" module index that has drifted from the real sidebar (still lists the removed Print Mapping module; missing Form Groups, User Platform, and SQL Workbench).
published: true
date: 2026-07-29T09:46:00.000Z
tags: platform/landing, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Landing

> **At a Glance**
> **Screen:** `Landing` (`/`) &nbsp;·&nbsp; **Access:** fully public — the route carries no `<PrivateRoute>` wrapper at all, not even the bare authenticated-only kind [Dashboard](/en/platform/dashboard) and [Profile](/en/platform/profile) use &nbsp;·&nbsp; **Behaviour:** redirects an already-authenticated session straight to `/dashboard` &nbsp;·&nbsp; **Content:** hero + sign-in CTA + a hardcoded three-group "Inside the console" module index + version footer &nbsp;·&nbsp; **Confirmed drift:** the module index still names the removed Print Mapping module and omits three real screens (§4)

## 1. Overview

Landing is the signed-out entry point at `/` — a single static marketing page with no data fetching of its own. `<Route path="/" element={<Landing />} />` in `App.tsx` has no `<PrivateRoute>` wrapper whatsoever, unlike every other route in this book; the only routes as unguarded as this one are `/login` and `/changelog`. An already-authenticated visitor never actually sees the marketing content: a `useEffect` checks `isAuthenticated` and immediately `navigate('/dashboard', { replace: true })`s away — the same pattern `Login.tsx` uses for the same reason. While `AuthContext` is still resolving (`loading === true`), the page instead shows a centered "C" mark, a spinner, and "Loading…" — so a returning signed-in visitor typically sees a brief loading flash, then Dashboard, never the hero below.

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

Direct comparison of `Landing.tsx`'s `groups` array against `Layout.tsx`'s live `allNavItems` list (the same source [Business Units](/en/platform/business-units), [Report Templates](/en/platform/report-templates), and every other module page in this book cites for its own sidebar entry) shows the marketing index has not been kept in sync with the last two rounds of sidebar changes:

- **Print Mapping is still listed under Content**, even though the [print-template-mapping](/en/platform/print-template-mapping) module — sidebar entry included — was deleted from carmen-platform on 2026-07-24. The Landing page's own copy was not touched by that removal commit.
- **Form Groups is missing from Content.** [Report Templates — Form Groups](/en/platform/report-templates/form-groups) (`/report-form-groups`) shipped the same week as the Print Mapping removal (2026-07-24) and sits in the sidebar's Content group today; Landing's Content list still shows only 3 of the group's real 4 items.
- **User Platform and SQL Workbench are both missing from Platform.** The sidebar's Platform group has 5 items (Applications, Roles, Super Admins, User Platform, SQL Workbench); Landing's Platform list shows only 3, omitting the `UserPlatformManagement` screen (part of [Platform RBAC](/en/platform/rbac)) entirely and predating [SQL Workbench](/en/platform/sql-workbench) (added 2026-07-09) by longer still.

None of this affects behaviour — the index is inert text with no links, read only by a signed-out visitor deciding whether to sign in — but a reader using this page as a feature list would come away with an inaccurate picture of what the console currently does. This is a documentation-style drift in the product's own marketing copy, not a wiki error; flagged here rather than silently corrected, since fixing `Landing.tsx` itself is outside this wiki's scope.

## 5. Roles and Personas

No authentication and no permission grant of any kind is required to view this page — it is the one screen in the product reachable by an anonymous browser. The only interactive elements are the two navigation links (Sign in → `/login`, See what's new → `/changelog`), neither of which is gated.

## 6. Related Modules

- [Dashboard](/en/platform/dashboard) — where an authenticated session is redirected to, both from this page and from Login; the real, permission-filtered module surface (via the sidebar `Layout.tsx` renders once signed in) that this page's static index is meant to preview.
- [Changelog](/en/platform/changelog) — the other fully public route, linked from the hero's "See what's new" and sharing the `VersionBadge` component with this page's footer.
- [print-template-mapping](/en/platform/print-template-mapping) — the removed module this page's own index has not yet stopped listing (§4).
- [Report Templates — Form Groups](/en/platform/report-templates/form-groups), [Platform RBAC](/en/platform/rbac), [SQL Workbench](/en/platform/sql-workbench) — the three real screens missing from this page's index (§4).

## 7. Reference Sources

- `../carmen-platform/src/pages/Landing.tsx` — the page: auth-redirect effect, loading state, hero, the hardcoded `groups` array, footer.
- `../carmen-platform/src/pages/Login.tsx` — the sibling public route with the identical already-authenticated redirect pattern.
- `../carmen-platform/src/components/Layout.tsx:50-68` — the live `allNavItems` sidebar list this page's index was compared against.
- `../carmen-platform/src/App.tsx:61` — the unwrapped `<Route path="/" element={<Landing />} />` (no `<PrivateRoute>`).
- `../carmen-platform/src/components/VersionBadge.tsx` — the shared version-badge component, documented in full in [Changelog](/en/platform/changelog) §3.

## 8. Pages in This Module

This module is a single page; see the parent [Platform book index](/en/platform).
