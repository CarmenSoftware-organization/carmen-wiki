---
title: Activity Events — Data Model
description: Every field of the tb_activity_event record — what writes it, what's optional, the enriched fields added only at read time — plus the 365-day retention job and daily rollup that govern how long rows live.
published: true
date: '2026-09-06T01:55:00.000Z'
tags: book/platform, activity-events, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Activity Events — Data Model

This page documents `tb_activity_event`, the append-only UI-telemetry table behind [Activity Events](/en/platform/activity-events) and its aggregate sibling [Usage Analytics](/en/platform/usage-analytics). It is **not** `tb_activity`, the change-history/audit table behind the "View History" action elsewhere in the product — see the parent page's §2 for that distinction; nothing on this page describes `tb_activity`.

The model is defined in `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1489-1509` (HEAD `937cf5ac4`, 2026-09-06). Its own header comment states the design intent directly, and the write/retention paths below confirm it rather than merely repeat it: "Raw UI telemetry (append-only) — no soft-delete/audit columns by design: high volume, rows are never edited, only a retention job deletes them in bulk (micro-cronjobs)" (`schema.prisma:1487-1488`).

## 1. The Record

| Field | Type | Required? | Set by | Notes |
| --- | --- | --- | --- | --- |
| `id` | uuid | Always | Database (`gen_random_uuid()` default) | Row's own primary key; not shown as a labelled value anywhere in the UI, but used as the sort tiebreaker (§3) |
| `event_id` | uuid | Always | Client, per event | The dedupe key — `@unique`; a retried batch cannot create a duplicate row (§2) |
| `session_id` | string | Always | Client, per browser tab | `crypto.randomUUID()`, cached in `sessionStorage`; lives for the tab's lifetime, not the user's |
| `user_id` | uuid | Always | **Server**, from the caller's auth token | Never present in the client's payload at all — see §2 |
| `bu_code` | string, max 64 | Optional | Client, per event | Whichever BU the user had selected at that moment; absent if the profile/BU hadn't loaded yet. This is also the field cluster-scoping filters on (see Usage Analytics §4.3) — a row with no `bu_code` is invisible to any caller scoped to specific clusters |
| `app_id` | uuid | Optional | **Server**, from the `x-app-id` request header | Same value for every row in one batch (one HTTP request = one header); `null` if the header is missing or not a UUID |
| `domain` | string, max 253 | Optional | **Server**, from the `Origin` request header | Hostname only (scheme/port/path stripped, lowercased); `null` if `Origin` is missing or unparseable |
| `user_agent` | string, max 512 | Optional | **Server**, from the `User-Agent` request header | Truncated to 512 characters before storage |
| `event_type` | enum: `click` \| `page_view` | Always | Client, per event | `enum_activity_event_type` (`schema.prisma:1482-1485`) |
| `page_path` | string, max 512 | Always | Client, per event | `window.location.pathname` at the moment of the event |
| `element_id` | string, max 100 | Optional | Client, `click` events only | Derived, first match wins: `data-track` attribute → element `id` → `aria-label` → trimmed text content. Never set for `page_view` |
| `element_text` | string, max 200 | Optional | Client, `click` events only | Trimmed `textContent` of the clicked element. Never set for `page_view` |
| `props` | JSON object, default `{}` | Optional | Client, per event | For `page_view`: always `{ route_pattern }` (the path with dynamic segments normalized, e.g. `/procurement/purchase-request/:id`). For `click`: only `data-track-*` extra attributes, if any are present |
| `client_ts` | timestamptz | Always | Client, per event | `new Date().toISOString()` at the moment the event is *queued* — not necessarily when the batch is sent (queueing/retry can delay the actual request) |
| `server_ts` | timestamptz | Always | **Database**, `@default(now())` | Not settable by client or application code — nothing in `createBatch()`'s insert payload sets it. All rows in one `createMany()` batch share the same value, because Postgres's `now()` default resolves to transaction-start time, not per-row wall-clock time (§3) |

No column is ever updated after insert, and there is no soft-delete column (`deleted_at`) — a row exists exactly as written until the retention job physically deletes it (§4).

## 2. Fields the client never sends

Two boundaries are easy to misread from the frontend `AnalyticsEvent`/`ActivityEvent` type shapes alone, so they are stated explicitly here, each confirmed by reading the field's actual source rather than assuming from the type definition:

- **`user_id` is never part of the client's payload.** The frontend's own `AnalyticsEvent` interface (`../carmen-inventory-frontend-react/lib/analytics.ts:32-42`) has no `user_id` field, and the backend's per-event Zod schema (`ActivityEventSchema`, `activity-event.dto.ts:9-46`) has no `user_id` field either. It is read from the authenticated request (`ExtractRequestHeader(req)` in `analytics-events.controller.ts:87`) and passed down as a separate `user_id` parameter, stamped identically onto every event in the batch by `createBatch()` (`activity-event.service.ts:92-96`). A client cannot claim to be a different user than its own Bearer token.
- **`app_id`, `domain`, and `user_agent` are never part of the per-event payload either** — they are one shared "client context" per HTTP request, extracted from headers by `ExtractClientContext()` (`extract_client_context.ts`, full, 62 lines) and stamped onto every event in that batch identically (`activity-event.service.ts:98-101`, its own comment: "client context is the same for every row — one batch comes from one request"). `ExtractClientContext()` never throws on a malformed header (its own doc comment: "a malformed header must not fail a request that already passed the guards") — it degrades to `null` for that field instead.

## 3. Fields added only when the row is read (not stored)

`findEvents()` (`activity-event.service.ts:246-347`, the raw-explorer query) enriches each returned row with three fields that **do not exist on `tb_activity_event` at all**:

| Field | Source | Fallback |
| --- | --- | --- |
| `user_name` | Looked up from `tb_user`/`tb_user_profile` by `user_id`, after the page's rows are fetched (one lookup query for the whole page, not per row) — first + last name, else `username`, else `email` | `null` if the user record can't be resolved |
| `user_email` | Same lookup, `tb_user.email` | `null` |
| `app_name` | Looked up from `tb_application` by `app_id`, same one-query-per-page pattern | `null` if `app_id` itself is absent |

Because these three are computed at read time, they can go stale relative to the row's original actor/application (e.g. a user later renamed) — the raw `user_id`/`app_id` on the stored row do not change, only what the join resolves them to on a later read.

## 4. Retention and Rollup

Two scheduled jobs govern this table's lifecycle, both defined in `../micro-cronjobs` (HEAD `d17d8eb9bc3`, 2026-09-04) and both seeded as **active** cron entries in the same `"CRONJOBS"."Cronjob"` table the platform's own [Cronjobs](/en/platform/cronjobs) module administers (confirmed by that module's own backend proxy, `platform_cronjobs.service.ts:7-30`, which documents `CronJobRow` as "one row of `\"CRONJOBS\".\"Cronjob\"` as micro-cronjob serialises it" — the same table name the seed migrations below insert into).

### 4.1 Retention — the answer, and its enforcement point

**Raw rows are kept for 365 days, then physically deleted.** The enforcement point is `ActivityRetentionExecutor.Execute()` (`../micro-cronjobs/internal/executor/activity_retention.go`, full, 65 lines), dispatched when a cron job's `job_type` is `"activity_retention"` (`executor.go:80-81`). It runs as a batched delete loop, not one statement:

```
DELETE FROM tb_activity_event
WHERE id IN (
    SELECT id FROM tb_activity_event
    WHERE server_ts < NOW() - make_interval(days => retention_days)
    LIMIT batch_size
)
```

— repeated until a pass deletes zero rows, checking the job's context deadline (`ctx.Err()`) between batches so a long-running purge can be cut off cleanly by the scheduler's own timeout rather than left half-finished with no record of how far it got.

The job is not hypothetical: a seed migration inserts it as an **active**, scheduled cron entry — `../micro-cronjobs/migrations/20260730093731_seed_activity_retention_job.up.sql` — named "Activity events retention (365d)", `job_type = 'activity_retention'`, `cron_expression = '0 4 * * *'` (04:00 daily), `job_data = {"retention_days":365,"batch_size":10000}`, `is_active = true`. (The executor's own Go struct defaults to the same numbers — `RetentionDays: 365, BatchSize: 10000` — if a job's config is ever missing them, but the seeded row supplies them explicitly.)

Because this row lives in the same table the platform's Cronjobs screen manages, an operator holding `cronjob.manage` could in principle disable or reconfigure this retention window from that screen — this was confirmed structurally (same table, same row shape) but not tested against a live deployment, and is out of scope for this page beyond noting the connection.

### 4.2 Rollup — what feeds `tb_activity_event_daily`, and who reads it

Before retention runs each day, a second job aggregates recent raw rows into `tb_activity_event_daily` (`schema.prisma:1511-1529`) — a `(day, bu_code, domain, app_id, event_type, page_path, element_id)`-keyed summary of `clicks`/`sessions`/`users`. Enforcement point: `ActivityRollupExecutor.Execute()` (`../micro-cronjobs/internal/executor/activity_rollup.go`, full, 80 lines), dispatched on `job_type = "activity_rollup"` (`executor.go:78-79`), seeded active at `cron_expression = '30 3 * * *'` (03:30 daily, ahead of the 04:00 retention run), `job_data = {"days_back":2}` (`migrations/20260730092930_seed_activity_rollup_job.up.sql`). It re-aggregates one full **UTC** calendar day at a time, going back `days_back` days, and always skips the current (still in-progress) day; the upsert uses `ON CONFLICT ... DO UPDATE`, so re-running it for a day already rolled up is safe and idempotent — a design the file's own comment confirms is deliberate ("Idempotent — upserts via `ON CONFLICT` so re-running the same day is safe").

`tb_activity_event_daily` is **never deleted** by either job, or by anything else found: a grep of the entire migration/model history for `tb_activity_event_daily` outside its own creation and the rollup's insert turns up exactly one `DELETE`, and it is not a retention mechanism — a one-time, guarded statement in a schema migration (`20260731000000_activity_event_client_context/migration.sql`) that clears the table *only if* its unique index still lacks the `domain`/`app_id` columns being added in that same migration, to prevent the next rollup from double-counting under the old key shape. It runs at most once, is a no-op on any database where it has already applied, and is unrelated to the ongoing 365-day raw-row retention.

**No reader of `tb_activity_event_daily` was found.** A search of every repository consulted for this book — `../carmen-turborepo-backend-v2`, `../micro-cronjobs`, `../micro-report`, `../micro-data` — for any `SELECT`/query against this table, outside the rollup job's own `INSERT ... ON CONFLICT`, returns nothing. [Usage Analytics](/en/platform/usage-analytics) computes its own daily bucketing live from raw `tb_activity_event` rows within its (capped 90-day) query window rather than reading this table. This is stated as a finding from the repositories available, not as proof no consumer exists anywhere — a reader could exist in a repository outside this book's reference set.

## 5. Related Modules

- [Activity Events](/en/platform/activity-events) — the screen this record backs; filters, columns, and the write path in outline (§3.4 there).
- [Usage Analytics](/en/platform/usage-analytics) — the aggregate dashboard computed from the same raw table.
- [Cronjobs](/en/platform/cronjobs) — the platform's own admin screen over the same `"CRONJOBS"."Cronjob"` table that schedules retention and rollup (§4).
- [Applications](/en/platform/applications) — owner of the `tb_application` rows joined into `app_name` at read time (§3).

## 6. Reference Sources

- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1479-1529` (HEAD `937cf5ac4`, 2026-09-06) — `enum_activity_event_type`, `tb_activity_event`, `tb_activity_event_daily`, and their header comments.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/dto/activity-event/activity-event.dto.ts` (full) — `ActivityEventSchema`/`ActivityEventBatchSchema`, every per-field length cap and the 1–100 event batch cap.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/helpers/extract_client_context.ts` (full, 62 lines) — `ExtractClientContext()`, the `app_id`/`domain`/`user_agent` stamping and their caps/fallbacks.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/analytics-events/analytics-events.controller.ts` (full) — `POST api/analytics-events`, `ExtractRequestHeader` for `user_id`, guards.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/analytics-events/analytics-events.service.ts` (full) — the gateway-to-microservice proxy.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/log/activity-event/activity-event.service.ts:82-112,246-347` — `createBatch()` (the insert) and `findEvents()` (the read-time user/app-name enrichment).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/platform_cronjobs.service.ts:7-30` — `CronJobRow`, confirming the platform's Cronjobs module and the seeded retention/rollup jobs share one table.
- `../carmen-inventory-frontend-react/lib/analytics.ts:30-42` (HEAD `72d6cd340`, 2026-09-04) — the `AnalyticsEvent` client-side shape (confirms `user_id` is absent from it).
- `../micro-cronjobs/internal/executor/activity_retention.go` (full, 65 lines, HEAD `d17d8eb9bc3`, 2026-09-04) — the batched-delete retention executor.
- `../micro-cronjobs/internal/executor/activity_rollup.go` (full, 80 lines) — the daily upsert rollup executor.
- `../micro-cronjobs/internal/executor/executor.go:68-84` — the `job.JobType` dispatch switch, confirming both job types are wired to their executors.
- `../micro-cronjobs/migrations/20260730093731_seed_activity_retention_job.up.sql` — the seeded, active retention cron entry (365 days, 04:00 daily).
- `../micro-cronjobs/migrations/20260730092930_seed_activity_rollup_job.up.sql` — the seeded, active rollup cron entry (03:30 daily, 2 days back).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260731000000_activity_event_client_context/migration.sql` — the one-time, guarded `tb_activity_event_daily` clear tied to the `domain`/`app_id` dimension-key change, not a retention mechanism.
