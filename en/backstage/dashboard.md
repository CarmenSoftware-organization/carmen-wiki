---
title: Dashboard
description: The signed-in home hub (/dashboard) — a unified recent-activity stream across six domains plus a sticky per-domain active/total counts rail. No requiredPermission of its own; every domain silently drops out of both if the session can't read it.
published: true
date: 2026-10-29T05:30:00.000Z
tags: backstage/dashboard, carmen-software
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Dashboard

> **At a Glance**
> **Screen:** `Dashboard` (`/dashboard`) &nbsp;·&nbsp; **Access:** authenticated-only — the route carries no `requiredPermission` **and no `feature` key** (`backstageNav.ts`'s only nav row with neither), same as [Profile](/en/backstage/profile), so it is always visible/reachable regardless of grants or feature-flag state &nbsp;·&nbsp; **Sidebar:** top nav item, ungated, above every `groupKey` group (Organization, License Management, Content, Analytics, Scheduling, Backstage, AI, Database — see §4) &nbsp;·&nbsp; **Content:** a merged recent-activity stream over 6 domains + a sticky active/total counts rail &nbsp;·&nbsp; **Reached from:** post-login redirect (from [Landing](/en/backstage/landing) or Login), the sidebar brand mark, or the "Dashboard" nav item itself — though a membership-only cluster admin who lands here is immediately bounced onward to `/cluster-admin` (§5)

![Dashboard screen](/screenshots/platform/dashboard/index.png)

## 1. Overview

Dashboard is the first screen a signed-in session with platform authority lands on: both [Landing](/en/backstage/landing) and the Login page redirect an already-authenticated session straight to `/dashboard` unconditionally, and — for a session with platform authority — the sidebar's brand mark (logo + "Carmen Blue Backstage" wordmark) links back here from anywhere in the app. A membership-only cluster admin's brand mark instead points at their own cluster's page (`/cluster-admin/:clusterId/cluster`), and `PrivateRoute` bounces that same session straight to `/cluster-admin` if it ever lands on `/dashboard` regardless of how it got there (§5) — the redirect from Landing/Login is unconditional, but arriving here is not the end of the story for every session. Unlike every module screen documented elsewhere in this book, Dashboard reads **across** modules rather than owning one — its whole job is to answer "what changed, and how big is my estate" without navigating anywhere.

The page has two independent panels: a left **Activity Stream** (a merged, filterable, day-grouped timeline of the most recent create/update/publish events across six domains) and a right **Counts Rail** (a sticky summary card showing an "Estate" total plus each domain's active/total counts, each row linking straight to that domain's list page). Both panels load independently and fail independently — a slow or erroring domain does not block the other panel or the other domains within its own panel.

## 2. Activity Stream

Six domains feed the stream, in this fixed order: **Clusters, Business Units, Users, Applications, News, Report Templates**. For each, the page fetches its 8 most-recently-updated non-deleted records (`sort: 'updated_at:desc'`, `perpage: 8`) via that domain's own `getAll` service call — the same call each domain's own list page makes, not a dedicated activity endpoint. The six requests run concurrently via `Promise.allSettled`; **a domain whose fetch fails is silently dropped from the stream** rather than surfacing an error for that one domain (see §4 for what this means for low-privilege sessions). Every returned record is normalized (tolerating both flat `updated_at`/`updated_by_name` and nested `audit.updated.{at,name}` API shapes), classified as **created** (its `created_at` and effective "at" timestamp are equal), **updated** (they differ), or **published** (News domain only, when `status === 'published'`, overriding the created/updated inference) — then every domain's items are merged, sorted newest-first, and capped at 15 total.

The rendered timeline groups items by day (sticky day-header rows), and each row shows a coloured dot keyed to its verb (green = created, blue = updated, amber = published), a relative/clock timestamp, the record's name (plus its code, if the domain has one), the domain label, and — when known — who made the change; the whole row links to that record's edit page. A row of filter chips ("All" plus one per domain, each showing that domain's count within the current 15-item window) lets the viewer narrow the timeline to a single domain client-side. Three states besides the populated timeline: a 5-row skeleton while loading, an empty-state message ("Nothing changed here yet…") when the merge is empty, and a `FetchErrorState` with a Retry button — but that error state is not reachable through a per-domain failure. `fetchActivity()` fetches all six domains through `Promise.allSettled`, which never rejects; a domain whose request fails is simply excluded from the merge (per the paragraph above), so **even a total failure across all six domains still resolves successfully with an empty array** and renders the same "Nothing changed here yet…" empty state as six domains that are all genuinely quiet — the two cases are visually indistinguishable. The dedicated `FetchErrorState`/Retry path exists for a failure in `fetchActivity()` itself (something that throws outside the per-domain `Promise.allSettled` calls), not for the domains it fetches.

## 3. Counts Rail

The same six domains (in the same order) each contribute an **active** count and a **total** count, computed as two separate `getAll` calls per domain (`perpage: 1) with an `advance` filter — one unfiltered-but-not-deleted, one additionally filtered by that domain's own "active" predicate: `is_active: true` for Clusters/Business Units/Users/Applications/Report Templates, `status: 'published'` for News. The rail's header shows a single "Estate" figure — the sum of all six domains' **total** counts (only counting domains that resolved) — labelled "records governed." Below it, one row per domain shows `active / total` in monospace, each row a link to that domain's list page. If *any* single domain's pair of count calls fails, the whole rail (not just that row) switches to a `FetchErrorState` with a Retry button — a stricter failure mode than the Activity Stream, which drops only the failing domain.

## 4. What's Not on the Dashboard

`ACTIVITY_SOURCES` (the six domains listed in §2) has not grown since the module was last built — every other row in the sidebar's live navigation list, `ALL_BACKSTAGE_NAV_ITEMS` in `backstageNav.ts`, is absent from both panels. That list has grown substantially since this page's own last sync (many of the rows below are modules added after 2026-07-29), so the gap is wider than a first read of the page suggests:

| `groupKey` | Sidebar items not on the Dashboard |
|---|---|
| `navGroup.organization` | Tenant Migrations, Tenant Seed Data, Data Import (the three other rows in this group — Clusters, Business Units, Users — *are* covered) |
| `navGroup.licenseManagement` | Licenses, License Feature Groups, License Features — the whole group |
| `navGroup.content` | Form Groups, Dashboard Templates, Broadcasts (Report Templates and News, the group's other two rows, *are* covered) |
| `navGroup.analytics` | Usage Analytics, Activity Events — the whole group |
| `navGroup.scheduling` | Scheduled Jobs — the whole group |
| `navGroup.backstage` | Backstage Config, Email Settings, Backstage Roles, Backstage Users, Super Admins, Feature Flags (Applications, the group's other row, *is* covered) |
| `navGroup.ai` | Purchase Request AI Providers — the whole group |
| `navGroup.database` | Backstage Migrations, SQL Workbench, Database Pools — the whole group |

Also outside the Dashboard's reach entirely: the **cluster-admin** persona (`/cluster-admin/...`), which is not part of `ALL_BACKSTAGE_NAV_ITEMS` at all and has no dashboard-equivalent landing page of its own.

Broadcasts is worth a specific correction: this page previously said it "has no list endpoint at all," which was true when Broadcasts was a fire-and-forget compose-only screen, but is no longer true — `broadcastService.getAll()` (`GET /api/notifications/broadcasts`) has existed since the 2026-08-10/11 notification redesign that gave Broadcasts its own admin list/edit surface (see [Broadcasts](/en/backstage/broadcasts)). Dashboard's `ACTIVITY_SOURCES` simply has not been updated to add it as a seventh domain — a real gap now, not an architectural impossibility. Form Groups was always a view over the Report Templates resource, not a domain of its own, so its absence is by design rather than a gap. None of these rows' activity or counts appear anywhere on this page — a change to a role, a super-admin grant, a tenant migration, a cronjob, or a form-group default will not surface in the Activity Stream or the Counts Rail no matter how recent.

## 5. Roles and Personas

The `/dashboard` route is wrapped in a plain `<PrivateRoute>` with no `requiredPermission` and no `feature` prop — the same bare wrapping [Profile](/en/backstage/profile)'s platform-side `/profile` route gets. "Authentication is the only gate" is not the whole story, though: `PrivateRoute` (`src/components/PrivateRoute.tsx`) carries a Backstage-authority/cluster-admin resolution branch that runs for every route it guards, gated or not. Once `effectivePermissions` has resolved, a session that lacks Backstage authority is not rendered here at all — if it holds cluster-admin scope for at least one cluster (`hasClusterAdminScope`) it is redirected to `/cluster-admin` instead (`PrivateRoute.tsx:74-75`); a session with neither platform authority nor cluster-admin scope falls through and still renders the page, a deliberate exception so a fresh install's first (bootstrap) administrator is not locked out of `/dashboard` while their own super-admin-count check is still in flight. In other words: reaching `/dashboard` at all already implies platform authority (or that narrow bootstrap window) — a membership-only cluster admin never sees this page, redirected away by the guard itself rather than by anything the Dashboard component checks. There is no `<Can>` gate anywhere inside the page. Beyond that guard, access to each panel's content is indirect: each of the six underlying `getAll` calls still passes through that domain's own backend permission check, so a session lacking (for example) `report_template.read` will have its Report Templates fetch fail at the API and that domain will simply be missing from both panels (§2/§3) — the Dashboard does not itself check `hasPermission` for any domain, it inherits whatever the domain's own list endpoint enforces, one failed request at a time.

**Return-to-page after sign-in (since 2026-10-26, `254a5121`).** A signed-out visit to a guarded route no longer just lands on `/login`: `PrivateRoute` sends the browser to `/login?next=<path+query+hash>` (`loginPathFor()` in `src/utils/resolveNextPath.ts`, `PrivateRoute.tsx:59`), and Login sends the user back there after sign-in instead of always to `/dashboard`. `/dashboard` is only the fallback when `next` is absent or fails the open-redirect guard (`resolveNextPath` accepts only a same-origin relative path). The public pages (`/`, `/login`, `/login/callback`, `/changelog`) never get a `next`. A missing permission still renders `<Forbidden />` in place, and a session without Backstage authority still goes to `/cluster-admin`.

## 6. Related Modules

- [Landing](/en/backstage/landing) — the public page that redirects an already-authenticated session straight here; also the page whose own hardcoded "Inside the console" index should list the same modules the sidebar does (see that page's Overview for a confirmed drift between the two).
- [Profile](/en/backstage/profile) — the other route gated by a bare `<PrivateRoute>` with no permission requirement, and the one shared component reachable from both the platform view and the separate cluster-admin persona described below.
- [Clusters](/en/backstage/clusters), [Business Units](/en/backstage/business-units), [Users](/en/backstage/users), [Applications](/en/backstage/applications), [News](/en/backstage/news), [Report Templates](/en/backstage/report-templates) — the six domains the Activity Stream and Counts Rail read from.
- [Cluster Admin](/en/backstage/cluster-admin) — the separate, dashboard-less persona a membership-only cluster admin is redirected into instead of this page (§5); that module's own [Permissions](/en/backstage/cluster-admin/permissions) §4, edge case 9, documents the identical `PrivateRoute` redirect from the other side.

## 7. Reference Sources

- `../carmen-backstage/src/pages/Dashboard.tsx` — the page: parallel count-loading, activity-loading, layout.
- `../carmen-backstage/src/pages/dashboard/activity.ts` — `ACTIVITY_SOURCES` (the six domains, in display order), `fetchActivity`, `toActivityItem`, `deriveVerb`, `mergeAndSort`.
- `../carmen-backstage/src/pages/dashboard/ActivityStream.tsx` — filter chips, day grouping, timeline rendering, loading/error/empty states.
- `../carmen-backstage/src/pages/dashboard/CountsRail.tsx` — the Estate total and per-domain active/total rows.
- `../carmen-backstage/src/App.tsx:107-114` — the bare `<PrivateRoute>` (no `requiredPermission`, no `feature`) on `/dashboard`.
- `../carmen-backstage/src/components/PrivateRoute.tsx:62-83` — the Backstage-authority/cluster-admin resolution branch described in §5 (`effectivePermissions`, `hasClusterAdminScope`, the redirect to `/cluster-admin`, and the bootstrap-admin fall-through).
- `../carmen-backstage/src/components/nav/backstageNav.ts` — `ALL_BACKSTAGE_NAV_ITEMS`, the live sidebar list §4 is compared against; the ungated, feature-less `/dashboard` row sits outside every `groupKey` group. `Layout.tsx` itself no longer defines nav rows — it only calls `buildBackstageNav()` (`Layout.tsx:105`) and computes the brand-mark's destination (`Layout.tsx:109`, `hasBackstageAuthority ? '/dashboard' : '/cluster-admin'` — so the brand mark's "reached from anywhere" framing in §1 holds only for a session with platform authority).

## 8. Pages in This Module

This module is a single page; see the parent [Backstage book index](/en/backstage).
