---
title: Dashboard
description: The signed-in home hub (/dashboard) — a unified recent-activity stream across six domains plus a sticky per-domain active/total counts rail. No requiredPermission of its own; every domain silently drops out of both if the session can't read it.
published: true
date: 2026-07-29T09:46:00.000Z
tags: platform/dashboard, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Dashboard

> **At a Glance**
> **Screen:** `Dashboard` (`/dashboard`) &nbsp;·&nbsp; **Access:** authenticated-only — the route carries no `requiredPermission`, same as [Profile](/en/platform/profile) &nbsp;·&nbsp; **Sidebar:** top nav item (ungated, above the Organization/Content/Platform groups) &nbsp;·&nbsp; **Content:** a merged recent-activity stream over 6 domains + a sticky active/total counts rail &nbsp;·&nbsp; **Reached from:** post-login redirect (from [Landing](/en/platform/landing) or Login), the sidebar brand mark, or the "Dashboard" nav item itself

## 1. Overview

Dashboard is the first screen a signed-in session lands on: both [Landing](/en/platform/landing) and the Login page redirect an already-authenticated session straight to `/dashboard`, and the sidebar's brand mark (logo + "Carmen Platform" wordmark) links here from anywhere in the app. Unlike every module screen documented elsewhere in this book, Dashboard reads **across** modules rather than owning one — its whole job is to answer "what changed, and how big is my estate" without navigating anywhere.

The page has two independent panels: a left **Activity Stream** (a merged, filterable, day-grouped timeline of the most recent create/update/publish events across six domains) and a right **Counts Rail** (a sticky summary card showing an "Estate" total plus each domain's active/total counts, each row linking straight to that domain's list page). Both panels load independently and fail independently — a slow or erroring domain does not block the other panel or the other domains within its own panel.

## 2. Activity Stream

Six domains feed the stream, in this fixed order: **Clusters, Business Units, Users, Applications, News, Report Templates**. For each, the page fetches its 8 most-recently-updated non-deleted records (`sort: 'updated_at:desc'`, `perpage: 8`) via that domain's own `getAll` service call — the same call each domain's own list page makes, not a dedicated activity endpoint. The six requests run concurrently via `Promise.allSettled`; **a domain whose fetch fails is silently dropped from the stream** rather than surfacing an error for that one domain (see §4 for what this means for low-privilege sessions). Every returned record is normalized (tolerating both flat `updated_at`/`updated_by_name` and nested `audit.updated.{at,name}` API shapes), classified as **created** (its `created_at` and effective "at" timestamp are equal), **updated** (they differ), or **published** (News domain only, when `status === 'published'`, overriding the created/updated inference) — then every domain's items are merged, sorted newest-first, and capped at 15 total.

The rendered timeline groups items by day (sticky day-header rows), and each row shows a coloured dot keyed to its verb (green = created, blue = updated, amber = published), a relative/clock timestamp, the record's name (plus its code, if the domain has one), the domain label, and — when known — who made the change; the whole row links to that record's edit page. A row of filter chips ("All" plus one per domain, each showing that domain's count within the current 15-item window) lets the viewer narrow the timeline to a single domain client-side. Three states besides the populated timeline: a 5-row skeleton while loading, a `FetchErrorState` with a Retry button if literally every domain's fetch failed (rather than an empty merge), and an empty-state message ("Nothing changed here yet…") when the merge is empty but no errors occurred.

## 3. Counts Rail

The same six domains (in the same order) each contribute an **active** count and a **total** count, computed as two separate `getAll` calls per domain (`perpage: 1) with an `advance` filter — one unfiltered-but-not-deleted, one additionally filtered by that domain's own "active" predicate: `is_active: true` for Clusters/Business Units/Users/Applications/Report Templates, `status: 'published'` for News. The rail's header shows a single "Estate" figure — the sum of all six domains' **total** counts (only counting domains that resolved) — labelled "records governed." Below it, one row per domain shows `active / total` in monospace, each row a link to that domain's list page. If *any* single domain's pair of count calls fails, the whole rail (not just that row) switches to a `FetchErrorState` with a Retry button — a stricter failure mode than the Activity Stream, which drops only the failing domain.

## 4. What's Not on the Dashboard

Notably absent from both panels, by direct comparison against the sidebar's own module list (`Layout.tsx`): **Broadcasts** (no list endpoint — it is a fire-and-forget compose screen, nothing to count or show as "recent"), **Platform RBAC / Roles / Super Admins / User Platform**, **Tenant Migrations**, **SQL Workbench**, and **Report Form Groups** (a view over Report Templates, not a domain of its own). None of these six domains' activity or counts appear anywhere on this page — a change to a role, a super-admin grant, a tenant migration, or a form-group default will not surface in the Activity Stream or the Counts Rail no matter how recent.

## 5. Roles and Personas

The `/dashboard` route is wrapped in a plain `<PrivateRoute>` with no `requiredPermission` prop — authentication is the only gate, identical to [Profile](/en/platform/profile). There is no `<Can>` gate anywhere inside the page itself. The practical access control is indirect: each of the six underlying `getAll` calls still passes through that domain's own backend permission check, so a session lacking (for example) `report_template.read` will have its Report Templates fetch fail at the API and that domain will simply be missing from both panels (§2/§3) — the Dashboard does not itself check `hasPermission` for any domain, it inherits whatever the domain's own list endpoint enforces, one failed request at a time.

## 6. Related Modules

- [Landing](/en/platform/landing) — the public page that redirects an already-authenticated session straight here; also the page whose own hardcoded "Inside the console" index should list the same modules the sidebar does (see that page's Overview for a confirmed drift between the two).
- [Profile](/en/platform/profile) — the other route gated by a bare `<PrivateRoute>` with no permission requirement.
- [Clusters](/en/platform/clusters), [Business Units](/en/platform/business-units), [Users](/en/platform/users), [Applications](/en/platform/applications), [News](/en/platform/news), [Report Templates](/en/platform/report-templates) — the six domains the Activity Stream and Counts Rail read from.

## 7. Reference Sources

- `../carmen-platform/src/pages/Dashboard.tsx` — the page: parallel count-loading, activity-loading, layout.
- `../carmen-platform/src/pages/dashboard/activity.ts` — `ACTIVITY_SOURCES` (the six domains, in display order), `fetchActivity`, `toActivityItem`, `deriveVerb`, `mergeAndSort`.
- `../carmen-platform/src/pages/dashboard/ActivityStream.tsx` — filter chips, day grouping, timeline rendering, loading/error/empty states.
- `../carmen-platform/src/pages/dashboard/CountsRail.tsx` — the Estate total and per-domain active/total rows.
- `../carmen-platform/src/App.tsx:64` (bare `<PrivateRoute>` on `/dashboard`); `src/components/Layout.tsx:51` — the ungated top-level "Dashboard" nav item, and the brand-mark link at `Layout.tsx:149`.

## 8. Pages in This Module

This module is a single page; see the parent [Platform book index](/en/platform).
