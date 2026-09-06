---
title: Usage Analytics
description: The UI-telemetry dashboard at /analytics (module slug usage-analytics) — every StatCard, the daily chart, and both Top Lists defined against tb_activity_event, plus the activity_event.read/activity_event.detail permission seam that gates its drill-down.
published: true
date: '2026-09-06T01:14:11.000Z'
tags: book/platform, usage-analytics
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Usage Analytics

**Usage Analytics** is one screen, `UsageAnalytics`, reached at the route **`/analytics`** — note that the route and this wiki module's own slug (`usage-analytics`) differ, so a reader searching either term should land here. It is a read-only aggregate dashboard over UI telemetry (page views and clicks the frontend itself logs), built from a single backend call, `GET /api-system/platform/analytics/overview`. It has a narrower sibling, [Activity Events](/en/platform/activity-events) at `/activity-events`, which shows the same telemetry as individual rows rather than aggregates — the two screens are gated by two different permission keys, detailed in §4.

## 1. Overview

The page (`UsageAnalytics.tsx`, 251 lines, read in full) renders, top to bottom:

1. A page header with an **Export CSV** button (disabled while loading).
2. A filter bar: a date-range control (preset 7/30/90 days, or a custom range), a Business Unit dropdown, an Application dropdown, and an Event type dropdown (`click` / `page_view`).
3. An error banner, shown only when the fetch itself failed.
4. Five **StatCards** (`events`, `clicks`, `page_views`, `sessions`, `users`).
5. Below that, one of two mutually exclusive views: an **empty-state card** when the window has zero events, or a **daily area chart** plus two **Top List** cards (Top Pages, Top Elements).

Every value on the page comes from one response shape, `AnalyticsOverview` (`src/types/index.ts:1360-1365`, under the file's own `// ==================== Usage Analytics (tb_activity_event) ====================` section header) — `summary`, `daily[]`, `top_pages[]`, `top_elements[]`. All four are computed by one backend call in one round trip; there is no per-widget endpoint.

## 2. Business Context

This dashboard exists so an operator can see how the Platform admin console (and, via the shared `app_id`/telemetry table, other applications logging through the same pipe) is actually being used — which pages get opened, which buttons get clicked, by how many distinct sessions and users — without granting access to the raw, per-individual rows behind those numbers. That distinction is deliberate and enforced by two separate permission keys (§4), not by two views of the same permission.

No prior conceptual documentation exists for this module. A search of `../carmen/docs` for `usage analytics` / `activity_event` returns only an unrelated bullet ("Permission usage analytics") in `workflow-permissions-system.md` that is not about this screen. Everything on this page is sourced from `../carmen-platform` and `../carmen-turborepo-backend-v2` implementation directly.

## 3. Metrics — What Each Number Counts, Its Source, and Its Window

### 3.1 The time window and filters

- The backend requires `from`/`to` as ISO 8601 UTC and treats the window as **half-open**: `server_ts >= from AND server_ts < to` (`activity-event.query.ts`'s `buildWhere()`). The cutoff column is `server_ts` — the timestamp the platform database recorded on write — not `client_ts`, the timestamp the browser reported for when the event actually happened.
- The window is capped at **90 days** (`MAX_RANGE_DAYS`, `analytics-range.ts`), enforced by `parseRange()` with a `400 Bad Request` past that span (`analytics-range.ts:16-32`). The frontend mirrors the same constant (`utils/analyticsRange.ts:14`, comment: "ต้องตรงกับ MAX_RANGE_DAYS ฝั่ง backend" / "must match the backend's MAX_RANGE_DAYS") purely to reject an over-wide custom range client-side before firing a request the server would 400 anyway.
- The default on load is the **last 7 days**, computed by `presetRange(7)` (`UsageAnalytics.tsx:30`). Preset boundaries are cut at **Thailand midnight**, not UTC midnight (`presetRange()`/`tzMidnightToUtc()`, `analyticsRange.ts:72-93`) — the file's own header comment states why (`analyticsRange.ts:1-7`): cutting at UTC midnight would show the first and last day in the chart as partial days, because daily bucketing on the backend also groups by Thailand date (§3.3).
- Three further filters narrow — never widen — the same window: **Business Unit**, **Application**, and **Event type** (`click`/`page_view`). The BU and Application dropdowns load once on mount from `businessUnitService`/`applicationService`, each capped at `perpage: 100` (`useAnalyticsFilterOptions.ts:32-33`) — a fleet with more than 100 business units or 100 applications will not show every option in these two dropdowns; this is a structural cap in the hook, not a runtime failure, and was not checked against any live deployment's actual counts.
- On the wire, the BU filter is sent as `filter_bu_code`, not `bu_code` — deliberately. `analyticsService.ts`'s own comment explains: `KeycloakGuard` (which wraps the whole controller) branches on the mere *presence* of a query parameter literally named `bu_code` and then requires the caller to be a member of that BU or a super-admin, throwing `401` otherwise — which would 401 every `support_manager` call that filters by BU, and 401 everyone (even a super-admin) whose typed code doesn't match a real BU. The backend controller repeats the same warning verbatim above its own parameter (`platform-analytics.controller.ts`, comment above `filter_bu_code` on both routes): "อย่า 'จัดระเบียบ' กลับ" — "do not 'tidy this up' back to `bu_code`."

### 3.2 The five StatCards (`summary`)

All five are one Postgres row from one query, computed over the exact window and filters above (`activity-event.service.ts`'s `getOverview()`, the `summaryRows` query):

| Card | What it counts | SQL |
| --- | --- | --- |
| Events | Every matching row, both event types | `COUNT(*)` |
| Clicks | Matching rows where `event_type = 'click'` | `COUNT(*) FILTER (WHERE event_type = 'click')` |
| Page views | Matching rows where `event_type = 'page_view'` | `COUNT(*) FILTER (WHERE event_type = 'page_view')` |
| Sessions | Distinct `session_id` values among matching rows | `COUNT(DISTINCT session_id)` |
| Active users | Distinct `user_id` values among matching rows | `COUNT(DISTINCT user_id)` |

"Active" in "Active users" means only "logged at least one click or page view in this window" — there is no separate session-duration or idle-timeout definition behind it.

When the fetch itself fails, `StatCards` renders an em dash (`—`) for every card instead of `0` (`StatCards.tsx`, its own comment: "ไม่มี `summary` (โหลดไม่สำเร็จ) ≠ ค่าเป็นศูนย์" — "no `summary` [i.e., the fetch failed] is not the same as a value of zero"). This is a deliberate design choice to keep a failed measurement from looking like a real reading of zero.

### 3.3 The daily series — what's charted vs. what's only exported

The same `WHERE` also drives a `GROUP BY` query bucketed by day (`activity-event.service.ts`, the `daily` query): `clicks`, `page_views`, `sessions`, `users` per day, using

```
to_char((server_ts AT TIME ZONE 'Asia/Bangkok')::date, 'YYYY-MM-DD') AS day
```

`'Asia/Bangkok'` is `ANALYTICS_TZ`, a single named constant on the backend (`activity-event.types.ts:1-2`, comment: "จุดเดียวในระบบ อย่า hardcode ซ้ำที่อื่น" — "the one place in the system; do not hardcode this elsewhere") — and, separately, a hardcoded literal offset (`TZ_OFFSET_MS = 7 * 60 * 60 * 1000`) on the frontend that the file's own comment states must be changed in lockstep with the backend constant if it ever changes, since nothing derives one from the other (`analyticsRange.ts:17-30`). The comment also states why a fixed offset is used rather than resolving the timezone via `Intl`: Bangkok has carried UTC+7 with no DST since 1920.

**Only `sessions` and `users` are drawn on the chart.** `UsageChart.tsx` renders exactly two `Area` series, `sessions` and `users` — `clicks` and `page_views` are computed per day and returned in the same response, but never plotted; they are reachable only through the CSV export below.

Because `sessions` and `users` in the daily rows are each `COUNT(DISTINCT ...)` **within that single day**, they do not sum to the `summary` card's totals when a session or a user is active on more than one day inside the window — the two figures are not designed to reconcile, and a difference between "sum of the daily column" and "the summary card" is not a bug.

**CSV export** ("Export CSV" in the page header) writes `day, clicks, page_views, sessions, users` straight from the already-fetched `overview.daily` array — there is no separate export endpoint (`UsageAnalytics.tsx:101-118`, `generateCSV`/`downloadCSV` in `utils/csvExport.ts`). `generateCSV` neutralizes CSV-formula-injection (a leading `=`, `+`, `@`, tab, or CR is prefixed with a quote) before the blob is built client-side. The filename's date range is computed through the same Thailand-timezone conversion the UI displays (`ymdInTz()`), not a raw UTC slice of the ISO string — the code comment gives the concrete case this avoids: a "Aug 1–7 Thailand time" window whose `from` is `2026-07-31T17:00Z` would otherwise print a filename starting on July 31.

### 3.4 Top Pages (`top_pages`)

One more query, same `WHERE`, grouped by `page_path`, ordered by event count descending, `LIMIT 10` (`activity-event.service.ts`, the `topPages` query): `events` (`COUNT(*)`), `sessions` and `users` (both `COUNT(DISTINCT ...)`, scoped to that one `page_path`'s own rows — not the window-wide sessions/users figure). The sub-label under each row ("`{sessions} sessions · {users} users`", `pages.usageAnalytics.topPageSub`) reports these per-page distinct counts, not a share of the summary total.

`page_path` is the raw pathname as logged by the frontend — the query comment on the backend controller states this can include a record id for a detail route, which is exactly why this list (unlike Top Elements) is scoped by cluster at all (§4.2).

### 3.5 Top Elements (`top_elements`)

Grouped by `element_id`, restricted to `event_type = 'click' AND element_id IS NOT NULL AND element_id <> ''`, ordered by click count descending, `LIMIT 10` (`activity-event.service.ts`, the `topElements` query): `clicks` (`COUNT(*)`). `element_text` and `page_path` are each picked with Postgres `mode() WITHIN GROUP (...)` — the single most frequently logged value for that `element_id` within the window, not necessarily the element's current text or page. If the same `element_id` was rendered under two different page paths or with two different labels during the window, the row shows whichever occurred more often, which need not be the one most recently true.

Top Elements is never clickable, for anyone: `TopList.tsx` only makes a row a `<button>` when an `onSelect` prop is passed, and `UsageAnalytics.tsx` never passes one when rendering the Top Elements list (contrast Top Pages, §4.1).

### 3.6 Consistency across the four figures — not a shared snapshot

`summary`, `daily`, `top_pages`, and `top_elements` are four independent SQL statements sent together with `Promise.all` purely to reduce latency, not inside one transaction (`activity-event.service.ts`'s own comment on `getOverview()`: "ไม่ใช่เพื่อความสอดคล้องของข้อมูล... ไม่มี transaction ร่วมกัน" — "not for data consistency... there is no shared transaction"). A write landing between the four queries can leave the figures slightly out of step with each other; the same comment states this is accepted for a dashboard of this kind ("เป็นตัวเลขเชิงภาพรวม ไม่ใช่ยอดที่ต้องกระทบยอด" — "an overview figure, not a total that must reconcile"), not something this page's numbers are expected to guarantee against.

### 3.7 Empty state vs. error state — two different reasons to show no chart

`UsageAnalytics.tsx` distinguishes two states that could otherwise look identical:

- **Fetch failed** (`error` is set): the error banner renders; `overview` is reset to `null`; the chart/Top List area is not rendered at all — not even the empty-state card. A source comment states the reasoning directly: rendering an empty chart alongside a "no data" Top List would "read like a genuine reading of zero, when the true state is that the value is simply unknown" (`UsageAnalytics.tsx:184-188`).
- **Fetch succeeded, zero events** (`isEmpty`, i.e. `overview.summary.events === 0`): the chart/Top Lists are replaced by an `EmptyState` card reading "No events in the selected range," with the suggestion to widen the date range or clear the BU/Application filters (`pages.usageAnalytics.emptyTitle`/`emptyDescription`). The StatCards still show real zeros in this case, since `overview` itself is non-null.

## 4. Roles and Permissions

### 4.1 The two keys — what each grants, and which screen each opens

The permission catalog states the distinction between the two `activity_event` actions directly (`seed.platform-permission.data.ts:95-96`, `../carmen-turborepo-backend-v2`):

| Key | Catalog description | Opens |
| --- | --- | --- |
| `activity_event.read` | "View the Usage Analytics dashboard (aggregate figures only)" | This page, `/analytics` |
| `activity_event.detail` | "View raw UI telemetry events, including which user clicked what" | [Activity Events](/en/platform/activity-events), `/activity-events` |

A caller can hold either key without the other — they are independent grants, not tiers of one permission. Both gate three layers identically in shape but differently in key:

| Layer | `/analytics` (this page) | `/activity-events` |
| --- | --- | --- |
| Sidebar nav row | `permission: 'activity_event.read'`, `feature: 'usage_analytics'`, `groupKey: 'navGroup.analytics'` | `permission: 'activity_event.detail'`, `feature: 'activity_events'`, same group | 
| Route (`PrivateRoute`) | `requiredPermission="activity_event.read"` `feature="usage_analytics"` | `requiredPermission="activity_event.detail"` `feature="activity_events"` |
| Backend endpoint | `GET .../analytics/overview` — `@RequirePlatformPermission('activity_event.read')` | `GET .../analytics/records` — `@RequirePlatformPermission('activity_event.detail')` |

Sources: `platformNav.ts:30-33` (rows at 32-33, kept deliberately contiguous per the comment at 30-31: splitting them would render two separate "Analytics" sidebar headings); `App.tsx:475-489`; `platform-analytics.controller.ts` (`@RequirePlatformPermission` on `overview()` and `events()`). Neither row carries `superAdminOnly`.

`PrivateRoute.tsx` (read in full) checks permission **before** the feature flag: a session without the required key sees `<Forbidden />` regardless of the flag; only a session that already passed the permission check can then hit `hide` (→ `<NotFound />`) or `inactive` (→ `<ComingSoon />`) on the `usage_analytics` feature key (`src/constants/featureFlags.ts:64`, `groupKey: 'navGroup.analytics'`, `defaultState: 'active'`).

### 4.2 `activity_event.detail` also gates drill-down, inside this page

Clicking a row in the **Top Pages** list normally navigates to `/activity-events` with the current filters carried over as query parameters (`goToEvents()`, `UsageAnalytics.tsx:93-99`) — its own comment explains why every active filter (not just page path and date) must be forwarded: a user filtered to one BU who lands on an unfiltered explorer would see a row count that doesn't match what they just clicked, with nothing on screen explaining why.

This drill-down is itself wrapped in `<Can permission="activity_event.detail">` (`UsageAnalytics.tsx:207-223`): a caller who holds it sees the **same** Top Pages list rendered with `onSelect={goToEvents}` (clickable rows); a caller who does not sees the **identical** list — same rows, same numbers, same sub-labels — via `<Can>`'s `fallback`, just without the `onSelect` prop, so the rows render as plain (non-clickable) text (`Can.tsx`, `TopList.tsx`). Nothing is hidden or blanked; only the navigation affordance is withheld. Top Elements never receives `onSelect` either way (§3.5) — the drill-down exists only for Top Pages.

`Can`'s check (`hasAuth` via `AuthContext.hasPermission`, called here with no `clusterId`) resolves to `checkPermission(eff, 'activity_event.detail')` with no cluster scoping argument, which is defined as true "if `activity_event.detail` exists in the platform-wide scope **OR any cluster scope at all**" (`utils/permissions.ts:43-61`, its own doc comment). This is a coarse, "can this person see the affordance" check — it does not mean the destination screen will show unrestricted data; the backend narrows what `/activity-events` actually returns per request (§4.3), independent of what made the button clickable on this page.

### 4.3 Backend enforcement and cluster scoping

`platform-analytics.controller.ts` (`../carmen-turborepo-backend-v2`) stacks three guards on each route:

| Route | Guards | Permission required |
| --- | --- | --- |
| `GET /api-system/platform/analytics/overview` | `KeycloakGuard` (class-level) + `AppIdGuard('analytics.overview')` + `PlatformPermissionGuard` | `activity_event.read` |
| `GET /api-system/platform/analytics/records` | `KeycloakGuard` (class-level) + `AppIdGuard('analytics.events')` + `PlatformPermissionGuard` | `activity_event.detail` |

`AppIdGuard` (`apps/backend-gateway/src/common/guard/app-id.guard.ts`, read in full) checks only that the `x-app-id` request header is a UUID present in an in-memory allowlist for the given `api_name` (`appAllowlistStore.isAllowed(appId, this.api_name)`) — it never reads `request.user` or any permission; it answers "is this application build allowed to call this API," not "is this user allowed." The frontend's shared `api.ts` client (read directly, lines 1-23) attaches `x-app-id` from a build-time env var to every request (line 8) and a `Bearer` token from `localStorage` on top of it via a request interceptor (line 23) — this is a genuine per-user session call layered under an app-identity check, not a service-to-service call `AppIdGuard` alone would be gating.

`PlatformPermissionGuard.canActivate()` (`auth/guards/platform-permission.guard.ts`, read in full) is documented in its own header comment as a **"coarse-grained platform RBAC gate"**: it passes if the required key exists in the caller's platform-wide scope **or in any cluster scope at all** (line 13), attaches the resolved `EffectivePlatformPermissions` object onto the request either way, and short-circuits to `true` for `is_super_admin === true` before checking the key. Both analytics routes are correctly decorated with `@RequirePlatformPermission`, so the guard's fail-open branch for an *undecorated* route (which would otherwise log a warning and pass every caller by default, per the same file) is not in play here.

The controller narrows further, per request, using `resolveAllowedClusterIds()` (`analytics-scope.ts`, read in full) — and, critically, using **whichever key actually gates that endpoint**, not a shared default: `overview()` resolves scope against `ACTIVITY_EVENT_READ`; `events()` resolves it against `ACTIVITY_EVENT_DETAIL` (the function's `required` parameter has no default value, by its own comment, specifically so a future endpoint cannot silently inherit the wrong key). The result is one of three shapes, fed into every one of the four `getOverview()` queries identically (`activity-event.query.ts`'s `buildScopedWhere()`):

- `null` — unrestricted (super-admin, or the required key held platform-wide).
- `[]` — restricted to nothing (fail-closed): the caller holds the key in no cluster at all, or the permissions object itself was missing/malformed.
- `[...clusterIds]` — restricted to business units belonging to exactly those clusters, via `bu_code IN (...)`, computed by looking up `tb_business_unit` rows with `deleted_at: null` for those cluster ids (`resolveBuScope()`, `activity-event.service.ts`). A `bu_code IN (...)` predicate excludes rows with a `NULL` bu_code under SQL's three-valued logic — platform-level events (logged before any BU was selected) are invisible to a cluster-scoped caller by construction, not by an extra check.

The service's own comment on `getOverview()` states this scoping applies to **all four** query shapes, not just the raw-row list — because `top_pages.page_path` can carry a record id, and `summary.users` alone can reveal a single-user case, both of which would otherwise leak identity across tenants to a caller who should only see their own clusters' data (`activity-event.service.ts`, the comment block above `getOverview()`).

### 4.4 Role-bundle assignment

The permission catalog seeds exactly two actions on the `activity_event` resource — `read` and `detail` (`seed.platform-permission.data.ts:95-96`) — and its own comment distinguishes the resource from `activity_log` (`tb_activity`, the separate change-history/"View History" audit trail used elsewhere in the product): "คนละตารางกับ activity_event ข้างบนซึ่งเป็น UI telemetry" — "a different table from `activity_event` above, which is UI telemetry" (line 97). The two are unrelated mechanisms that happen to share the word "activity"; a reader should not assume the audit-trail permission (`activity_log.read`) has any bearing on this page.

Of the four seeded platform role bundles (`seed.platform-role-permission.data.ts:11-52`, read in full):

| Role | `activity_event.read` (this page) | `activity_event.detail` (drill-down / `/activity-events`) |
| --- | --- | --- |
| Platform Admin | Yes — via `activity_event.*` (line 14) | Yes — via `activity_event.*` |
| Support Manager | Yes — explicit `activity_event.read` (line 40) | **No** |
| Support Staff | No | No |
| Security Officer | No | No |

A source comment above Platform Admin's grant states the reasoning for Support Manager's narrower grant directly, in the context of the sibling `activity_log.*` resource but describing the same read/detail split pattern: giving only `.read` is "พอสำหรับตอบลูกค้า" — "enough to answer a customer" — without exposing the underlying raw, per-individual rows. Concretely: a Support Manager can open this dashboard and see every aggregate figure on it, but cannot open `/activity-events` and cannot click through from Top Pages, because they hold `.read` and not `.detail`. Support Staff and Security Officer hold neither key and cannot reach either screen at all.

### 4.5 e2e coverage: none

`../carmen-platform-e2e/tests/` (HEAD `a8e3b31`, 2026-08-25) has no `usage-analytics`, `analytics`, or `activity-events` directory — confirmed by listing the repository directly. The only trace of this screen in that repository is a single screenshot artifact from a manual run, `runs/screens/2026-08-25_10-37-26/images/analytics.png`, which is not a test. Every behavioral claim on this page is sourced from reading `../carmen-platform` and `../carmen-turborepo-backend-v2` implementation, not from an executable spec.

## 5. Related Modules

- [Activity Events](/en/platform/activity-events) — the raw per-event explorer this page's Top Pages drill-down opens, gated by `activity_event.detail` (§4.1–§4.2). It shares this page's `analyticsService.ts` and reads from the same `tb_activity_event` table.
- [Feature Flags](/en/platform/feature-flags) — owns the `usage_analytics` feature key that gates this page after the permission check (§4.1).
- [Platform RBAC](/en/platform/rbac) — the permission catalog and role-bundle definitions referenced in §4.
- [Business Units](/en/platform/business-units) and [Applications](/en/platform/applications) — supply the two filter dropdowns (§3.1); this page does not own either list.

## 6. Reference Sources

All paths below are `../carmen-platform` (the Platform admin SPA, HEAD `157a65e`, 2026-09-04) unless prefixed `../carmen-turborepo-backend-v2` (the backend monorepo, HEAD `937cf5ac4`, 2026-09-06) or `../carmen-platform-e2e` (HEAD `a8e3b31`, 2026-08-25).

- `../carmen-platform/src/pages/UsageAnalytics.tsx` (full, 251 lines) — the screen, `fetchOverview`, `goToEvents` (93-99), `handleExport` (101-118), `isEmpty` (120), the `<Can>`-wrapped Top Pages drill-down (184-236).
- `../carmen-platform/src/pages/usageAnalytics/StatCards.tsx`, `TopList.tsx`, `UsageChart.tsx` — the five KPI cards and their em-dash-on-failure rule; the clickable/non-clickable row rendering; the two-series (sessions/users) area chart.
- `../carmen-platform/src/services/analyticsService.ts` — `getOverview`/`getEvents`, the `filter_bu_code` rename comment (§3.1), the `analytics/records` vs. `analytics/event*` ad-blocker naming comment.
- `../carmen-platform/src/types/index.ts:1327-1365` — `AnalyticsSummary`, `AnalyticsDaily`, `AnalyticsTopPage`, `AnalyticsTopElement`, `AnalyticsOverview`, under the file's own `tb_activity_event` section header.
- `../carmen-platform/src/utils/analyticsRange.ts` (full) — `ANALYTICS_TZ`, `MAX_RANGE_DAYS`, `TZ_OFFSET_MS` and its lockstep-with-backend comment, `presetRange`/`customRange`/`rangeSpanDays`.
- `../carmen-platform/src/components/analytics/DateRangeFilter.tsx` — preset/custom UI, client-side range-cap validation.
- `../carmen-platform/src/hooks/useAnalyticsFilterOptions.ts` — BU/Application dropdown load, the 100-row cap, `Promise.allSettled` reasoning.
- `../carmen-platform/src/utils/csvExport.ts` — `generateCSV` (CSV-injection neutralization), `downloadCSV`.
- `../carmen-platform/src/components/Can.tsx`, `src/components/PrivateRoute.tsx` (both full) — permission-then-feature-flag gate order; `Forbidden`/`ComingSoon`/`NotFound` outcomes.
- `../carmen-platform/src/context/AuthContext.tsx:268-272`, `src/utils/permissions.ts` (full) — `hasPermission`'s bootstrap escape hatch and `checkPermission`'s with/without-`clusterId` semantics (§4.2).
- `../carmen-platform/src/App.tsx:475-489` — the `/analytics` and `/activity-events` route registrations.
- `../carmen-platform/src/components/nav/platformNav.ts:30-33` — the two nav rows (32-33) and the contiguity comment above them (30-31).
- `../carmen-platform/src/constants/featureFlags.ts:64` — the `usage_analytics` feature-catalog entry.
- `../carmen-platform/src/i18n/en.ts` (lines 99-102, 4089-4116) and `src/i18n/th.ts` (lines 3112-3129) — page copy quoted in §3.2/§3.3/§3.7.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/platform-analytics.controller.ts` (full) — both routes, their guards, and every naming-trap comment cited in §3.1/§4.3.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/platform-analytics.service.ts` — the gateway-to-microservice proxy and `IAnalyticsQuery` shape.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/analytics-range.ts` (full) — `parseRange`, `MAX_RANGE_DAYS`.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/analytics-scope.ts` (full) — `ACTIVITY_EVENT_READ`/`ACTIVITY_EVENT_DETAIL`, `resolveAllowedClusterIds()`'s decision table.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-permission.guard.ts` (full) — the coarse-gate mechanism, super-admin short-circuit, undecorated-route fail-open branch.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/guard/app-id.guard.ts` (full) — the `x-app-id`/allowlist mechanism (§4.3).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.service.ts` (full, 348 lines) — `getOverview()`'s four raw-SQL queries, `resolveBuScope()`, `findEvents()`.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.types.ts` (full) — `ANALYTICS_TZ`, row shapes, the `allowed_cluster_ids` null/`[]`/`undefined` semantics comment.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.query.ts` (full) — `buildWhere()` (the `server_ts` window), `NEVER_MATCH`, `buildBuCodeScope()` (the deleted-BU/NULL-bu_code exclusion), `buildScopedWhere()`.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts:93-99` — the `activity_event.read`/`.detail` catalog descriptions and the `activity_log` distinction comment.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-role-permission.data.ts:11-52` (full) — the four role bundles' exact permission arrays.
- `../carmen-platform-e2e/tests/` — listed directly to confirm no `usage-analytics`/`analytics`/`activity-events` suite exists (§4.5).

## 7. Pages in This Module

This module is a single page; see the parent [Platform book index](/en/platform).
