---
title: Activity Events
description: The raw, per-event UI-telemetry explorer at /activity-events — every filter and column, the activity_event.detail permission it shares (but does not duplicate) with Usage Analytics, and why it is not the activity_log "View History" audit trail.
published: true
date: '2026-09-06T02:14:23.000Z'
tags: book/platform, activity-events
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Activity Events

**Activity Events** is one screen, `ActivityEventManagement`, reached at the route **`/activity-events`** — route and module slug match here, unlike its sibling. It is the raw, per-row counterpart to [Usage Analytics](/en/platform/usage-analytics): where that dashboard shows aggregate counts, this screen lists individual UI-telemetry rows (one per click or page view) from the same underlying table, `tb_activity_event`, with filters, sorting, CSV export, and a full-record detail view per row.

**This is not the audit trail.** A screen with a similar name — the "View History" action on Clusters, Business Units, Users, and Report Templates — reads a completely different table (`tb_activity`, resource key `activity_log`) recording who changed which field of a platform *record* and its old/new values. This page has no relationship to that feature; see §2 for the full distinction. (An earlier draft of this page conflated the two — corrected here.)

## 1. Overview

The page (`ActivityEventManagement.tsx`, 434 lines, read in full) renders, top to bottom:

1. A page header with subtitle "Per-event UI telemetry — who clicked what, on which page, and when" (`pages.activityEvents.subtitle`, `src/i18n/en.ts:4143`) and an **Export CSV** button (disabled while loading).
2. A filter bar: a free-text search box (debounced 400ms), a date-range control shared with Usage Analytics (`DateRangeFilter`, default last 7 days via `presetRange(7)`), and a **Filters** button opening a side sheet.
3. The filter sheet: Event type (`click`/`page_view`, dropdown — not free text, to avoid a silent no-match from a typo), Business Unit dropdown, Application dropdown, a free-text User (User ID) field, a free-text Page path field, and a free-text Session ID field.
4. Active-filter chips below the bar, one per non-empty filter, each individually clearable.
5. An error banner, shown only when the fetch itself failed.
6. A data table (columns in §3.2) with server-side pagination and sorting, or a `TableSkeleton`/`EmptyState` in place of it while loading or when zero rows match.
7. In development builds only (`process.env.NODE_ENV === 'development'`), a `DevDebugSheet` showing the raw response of `GET /api-system/platform/analytics/records` (`ActivityEventManagement.tsx:423-428`).

Every row on this page is one `ActivityEvent` (`src/types/index.ts:1367-1386`) — the full field list, what writes each field, and how long rows are kept are documented on the [Data Model](/en/platform/activity-events/data-model) sub-page rather than repeated here.

## 2. Business Context — What This Module Is, and Is Not

This screen exists so an operator holding the narrower of the two analytics permissions can inspect *individual* telemetry rows — which exact session clicked which exact element, on which page, at what timestamp — rather than only the totals `/analytics` shows. It is deliberately gated by a separate, stricter permission key (§4) because a raw row can identify a specific user's specific action, which an aggregate count cannot.

**Two unrelated resources share the word "activity."** Confirmed directly from source, not from a comment alone:

| | `activity_event` (this module) | `activity_log` (View History, elsewhere) |
| --- | --- | --- |
| Table | `tb_activity_event` (`schema.prisma:1489-1509`) | `tb_activity` (`schema.prisma:907-929`) |
| Shape | `session_id`, `event_type` (`click`/`page_view`), `page_path`, `element_id`/`element_text`, `props`, `client_ts`/`server_ts` — UI telemetry | `action`, `entity_type`/`entity_id`, `actor_id`, `old_data`/`new_data` JSON — a change-history record |
| Written by | Frontend telemetry batches, POSTed by the client (§3.4) | A manual audit-logging call site (login/logout, avatar change, and per-module CRUD handlers) |
| Permission keys | `activity_event.read` (aggregate dashboard), `activity_event.detail` (this page) | `activity_log.read` (timeline), `activity_log.detail` (old/new field values) |
| Screens | `/analytics`, `/activity-events` | "View History" on `BusinessUnitManagement`, `ClusterManagement`, `UserManagement`, `ReportTemplateEdit`, and others |

The permission catalog states the split directly, in four adjacent rows (`seed.platform-permission.data.ts:95-100`, `../carmen-turborepo-backend-v2`):

| Resource | Action | Catalog description |
| --- | --- | --- |
| `activity_event` | `read` | "View the Usage Analytics dashboard (aggregate figures only)" |
| `activity_event` | `detail` | "View raw UI telemetry events, including which user clicked what" |
| `activity_log` | `read` | "View the change history timeline of a platform record (who changed it, when)" |
| `activity_log` | `detail` | "View the old and new value of each changed field on a platform record" |

A source comment sits directly between the two resources' rows: "Record audit trail (`tb_activity`) — a different table from `activity_event` above, which is UI telemetry" (line 97). This is independently confirmed by how the two tables are wired, not merely by the comment: `LogEventsModule`, the generic audit-logging module described in its own comment as being for "manual audit logging (login/logout, avatar, etc.)" writing to `tb_activity`, explicitly **excludes** `tb_activity`, `tb_activity_event`, and `tb_activity_event_daily` from whatever generic model-tracking list it otherwise applies to (`apps/micro-business/src/app.module.ts:211-222`, `excludeModels` array) — the two systems are kept from feeding into each other by name, in code that has nothing to do with either page's permission strings.

No prior conceptual documentation for this module exists in `../carmen/docs` (searched for `activity_event`, `activity event`, `ui telemetry`, `activity-events` — no hits). Everything on this page and its data-model sub-page is sourced from `../carmen-platform`, `../carmen-turborepo-backend-v2`, `../carmen-inventory-frontend-react`, and `../micro-cronjobs` implementation directly.

## 3. The Explorer Screen

### 3.1 Columns and sorting

| Column | Field | Sortable | Notes |
| --- | --- | --- | --- |
| Time | `server_ts` | Yes | Formatted `YYYY-MM-DD HH:MM:SS`, local to the browser |
| User | `user_name` (or first 8 chars of `user_id` if no name resolved), `user_email` below in small text | No | `user_name`/`user_email` are resolved server-side, not stored on the row (§ data model) |
| BU | `bu_code` | No | `-` when absent |
| Type | `event_type` badge | Yes | |
| Page | `page_path`, monospace, truncated with a title tooltip | Yes | |
| Element | `element_id`, monospace, truncated; tooltip shows `element_text` or `element_id` | No | `-` for `page_view` rows, which never carry an element |
| App | `app_name` | No | Hidden on the card/mobile layout (`meta: { card: 'hidden' }`) |
| (actions) | — | No | An eye icon opens the detail sheet for that row |

The four sortable columns match exactly the backend's sort whitelist (`SORTABLE`, `activity-event.service.ts:25-30`, `../carmen-turborepo-backend-v2`): `server_ts`, `client_ts`, `page_path`, `event_type` — except `client_ts` has no table column at all on this screen (it only appears in the detail sheet, §3.3) and so cannot be reached as a sort by any UI control, even though the backend would honor it. An unrecognized or non-whitelisted `sort` value falls back to `server_ts:desc` server-side (`activity-event.service.ts:275-277`); ties always break on `id` in the same direction (`activity-event.service.ts:284`, its own comment: every row inserted in one batch shares the same `server_ts` because Postgres's `now()` default resolves to transaction-start time, so `server_ts` alone cannot guarantee a stable page boundary).

Clicking a column header cycles the table through ascending → descending → unsorted; landing on "unsorted" resets the query to `server_ts:desc` and remounts the table (a `sortResetKey` bump, `ActivityEventManagement.tsx:223-226`) so the header arrow and the actual row order stay in agreement — `DataTable` itself has no controlled way to represent "no sort," so the component is deliberately reset rather than left showing a stale arrow.

### 3.2 Filters, search, and pagination

- **Search** matches `page_path`, `element_id`, or `element_text` via SQL `ILIKE '%term%'` (`buildWhere()`, `activity-event.query.ts:26-31`) — confirmed from the query builder itself, not the endpoint's doc comment alone.
- **Event type**, **Business Unit**, and **Application** are dropdowns (BU/Application options load once, capped at 100 rows each, same `useAnalyticsFilterOptions` hook Usage Analytics uses).
- **User ID**, **Page path**, and **Session ID** are free-text; `page_path` and `session_id` match **exactly** (`page_path = ...`, `session_id = ...`), not by substring — unlike the Search box.
- The four text filters (search, page path, session ID, user ID) each debounce 400ms before triggering a fetch and resetting to page 1 in the same render pass as the debounced value settling, specifically to avoid firing one throwaway fetch with a half-updated filter/page combination (`ActivityEventManagement.tsx:92-103`).
- Page size defaults to 25 and is remembered per browser in `localStorage` (`perpage_activity_events`).
- Every filter here narrows the same server-scoped window that also applies at the backend (§4.3) — a filter can only shrink what a caller already can see, never expand it.

### 3.3 Row detail and CSV export

Clicking a row's eye icon opens `EventDetailSheet` (`src/pages/activityEvents/EventDetailSheet.tsx`, full, 78 lines), which shows every field the raw explorer's API response carries for that row: server time, client time, type, user (name/id), email, BU, application, domain, page path, element id, element text, session id, event id, the raw `props` object (via a `JsonViewer`), and the raw `user_agent` string — plus a **"View this entire session"** button that reopens the table filtered to that `session_id` alone (clearing the page-path filter first, since a session view that stayed page-scoped would silently hide most of the session).

**CSV export** (`handleExport`, `ActivityEventManagement.tsx:228-241`) writes only the columns visible in the table plus the user's email — `server_ts` (labelled "Server time"), `user_name`, `user_email`, `bu_code`, `event_type`, `page_path`, `element_id`, `app_name` — **not** `session_id`, `event_id`, `client_ts`, `domain`, `user_agent`, or `props`; those six fields are visible only in the detail sheet, never in the export. It reuses the same `generateCSV`/`downloadCSV` helpers as Usage Analytics, including the same formula-injection neutralization on every cell (see that page's §3.3 for the exact regex and its hyphen-handling case, which applies identically here).

### 3.4 Who writes these rows

Neither this screen nor `carmen-platform` writes any `tb_activity_event` rows — confirmed by grepping `../carmen-platform/src` for any call to the ingestion endpoint or a tracking client; there is none. The rows this page reads are written by a *different* application: `../carmen-inventory-frontend-react`'s `lib/analytics.ts` (full), a click/page-view telemetry batcher that runs only inside that app's authenticated shell (`components/analytics-bridge.tsx`, mounted in `RootLayout`/`ProtectedShell`, so nothing is queued before login). It captures every click on `[data-track], button, a, [role="button"]` and every route change, batches up to 50 events per request (queue-capped at 500, flushed every 10s, on reaching 20 queued events, or immediately with `keepalive` on tab hide), and POSTs to `/api/analytics-events` — proxied through the gateway's `POST api/analytics-events` (`analytics-events.controller.ts`, `../carmen-turborepo-backend-v2`), guarded by `KeycloakGuard` and `AppIdGuard('analyticsEvent.create')`, into `ActivityEventService.createBatch()` (`../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.service.ts:82-112`), which inserts via `createMany({ skipDuplicates: true })` keyed on the client-generated `event_id` for retry-safe idempotency. Full field-by-field detail — including which of these fields the client can set and which are stamped server-side — is on the [Data Model](/en/platform/activity-events/data-model) page.

## 4. Roles and Permissions

### 4.1 The gating key, and how it differs from the dashboard's

| Layer | This page (`/activity-events`) |
| --- | --- |
| Sidebar nav row | `permission: 'activity_event.detail'`, `feature: 'activity_events'`, `groupKey: 'navGroup.analytics'` — not `superAdminOnly` (`platformNav.ts:33`) |
| Route (`PrivateRoute`) | `requiredPermission="activity_event.detail"` `feature="activity_events"` (`App.tsx:483-489`) |
| Backend endpoint | `GET /api-system/platform/analytics/records` — `@RequirePlatformPermission('activity_event.detail')` (`platform-analytics.controller.ts:180-182`) |

`activity_event.detail` is a **different key** from `activity_event.read`, which gates only the aggregate `/analytics` dashboard — a caller can hold either without the other. The full two-key comparison (what each grants, the three-layer gate table, `<Can>`-wrapped drill-down from Top Pages, backend cluster-scoping mechanics, and role-bundle assignment) is documented in depth on [Usage Analytics §4](/en/platform/usage-analytics) rather than duplicated here, since both screens share the identical guard stack and the identical `resolveAllowedClusterIds()` scoping function — only the key passed to it differs (`ACTIVITY_EVENT_DETAIL` here vs. `ACTIVITY_EVENT_READ` there, `analytics-scope.ts:7-13`).

### 4.2 What `activity_event.detail` alone means for this page

Holding `activity_event.detail` opens this screen outright — a caller does not need `activity_event.read` as well. Per the role-bundle seed (`seed.platform-role-permission.data.ts:11-52`, `../carmen-turborepo-backend-v2`, independently re-read for this page — see §6): **Platform Admin** holds both keys via `activity_event.*` (line 14); **Support Manager** holds `activity_event.read` only (line 40) and therefore cannot open this page at all (sees `<Forbidden />` at the route, and no nav row); **Support Staff** and **Security Officer** hold neither key. This matches, and does not differ from, what [Usage Analytics §4.4](/en/platform/usage-analytics) documents for the same two keys.

### 4.3 e2e coverage: none

`../carmen-platform-e2e/tests/` (HEAD `a8e3b31`, 2026-08-25) has no `activity-events` directory, confirmed by listing the repository directly — matching the Task 1 source map's no-e2e list for this module. Every behavioral claim on this page and its data-model sub-page is sourced from reading `../carmen-platform`, `../carmen-turborepo-backend-v2`, `../carmen-inventory-frontend-react`, and `../micro-cronjobs` implementation, not from an executable spec.

## 5. Related Modules

- [Usage Analytics](/en/platform/usage-analytics) — the aggregate dashboard sibling at `/analytics`, gated by `activity_event.read`; owns the full permission/guard/cluster-scoping writeup this page's §4 defers to.
- [Platform RBAC](/en/platform/rbac) — the permission catalog and role-bundle definitions referenced in §2 and §4.
- [Business Units](/en/platform/business-units) and [Applications](/en/platform/applications) — supply the BU and Application filter dropdowns (§3.2); this page does not own either list.
- [Cronjobs](/en/platform/cronjobs) — the platform's own scheduled-job admin screen, which (per the same `"CRONJOBS"."Cronjob"` table `../carmen-turborepo-backend-v2`'s `platform_cronjobs.service.ts` reads and writes) is the same store that holds the retention and rollup job definitions documented on the [Data Model](/en/platform/activity-events/data-model) page.

## 6. Reference Sources

All paths below are `../carmen-platform` (the Platform admin SPA, HEAD `157a65e`, 2026-09-04) unless prefixed otherwise.

- `../carmen-platform/src/pages/ActivityEventManagement.tsx` (full, 434 lines) — the screen: filters (`fetchEvents`), columns, sorting/pagination handlers, CSV export, dev debug panel.
- `../carmen-platform/src/pages/activityEvents/EventDetailSheet.tsx` (full, 78 lines) — the per-row detail sheet and "View this entire session" handoff.
- `../carmen-platform/src/services/analyticsService.ts` — `getEvents()`, shared with Usage Analytics.
- `../carmen-platform/src/types/index.ts:1367-1386` — the `ActivityEvent` frontend type.
- `../carmen-platform/src/App.tsx:483-489` — the `/activity-events` route registration.
- `../carmen-platform/src/components/nav/platformNav.ts:32-33` — the two contiguous Analytics nav rows.
- `../carmen-platform/src/i18n/en.ts:4142-4191` and `src/i18n/th.ts:3151` onward — page copy quoted in §1/§3.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/platform-analytics.controller.ts:147-259` (HEAD `937cf5ac4`, 2026-09-06) — the `GET /records` route, its guards, and the ad-blocker naming-trap comment governing the URL (`analytics/records`, never `analytics/event*`).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-analytics/analytics-scope.ts` (full) — `ACTIVITY_EVENT_DETAIL`, `resolveAllowedClusterIds()`.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.service.ts:82-112,246-347` — `createBatch()` (the insert path, §3.4) and `findEvents()` (the sort-tiebreak comment, user/application name resolution).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.query.ts` (full) — `buildWhere()`'s `ILIKE` search clause.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/analytics-events/analytics-events.controller.ts` (full) — `POST api/analytics-events`, its guards (`KeycloakGuard`, `AppIdGuard('analyticsEvent.create')`), and its 100-event cap.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/analytics-events/analytics-events.service.ts` (full) — the gateway-to-microservice proxy calling `ActivityEvents.createBatch`.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/dto/activity-event/activity-event.dto.ts` (full) — the Zod validation schema (per-field length caps, the 1–100 event batch cap) documented on the data-model page.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/helpers/extract_client_context.ts` (full) — how `app_id`/`domain`/`user_agent` are stamped server-side from headers, documented on the data-model page.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:907-929,1479-1529` — `tb_activity` and `tb_activity_event`/`tb_activity_event_daily`, read side by side for §2's table.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts:93-101` — the four permission-catalog rows quoted in §2.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-role-permission.data.ts:11-52` (full) — role-bundle assignment, re-verified independently for §4.2.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/app.module.ts:211-222` — `LogEventsModule`'s `excludeModels`, the independent confirmation cited in §2.
- `../carmen-inventory-frontend-react/lib/analytics.ts` (full, HEAD `72d6cd340`, 2026-09-04) — the telemetry batcher: `enqueue`, `deriveElementId`, `collectTrackProps`, `flush`, batching/retry/disable rules.
- `../carmen-inventory-frontend-react/components/analytics-bridge.tsx` (full) — where and when tracking starts.
- `../carmen-platform-e2e/tests/` (HEAD `a8e3b31`, 2026-08-25) — listed directly to confirm no `activity-events` suite exists (§4.3).

## 7. Pages in This Module

- [Data Model](/en/platform/activity-events/data-model) — every field of the `tb_activity_event` record, what writes it, and the retention/rollup mechanism that governs how long rows are kept.
