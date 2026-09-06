---
title: Cronjobs — Data Model
description: The full "CRONJOBS"."Cronjob" field table (owned by micro-cronjobs' own SQL migrations, not Prisma), every job type's config shape, scheduler mechanics, and exactly where a failed run becomes visible.
published: true
date: '2026-09-06T22:00:00.000Z'
tags: book/platform, cronjobs, data-model
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Cronjobs — Data Model

> **Source of truth:** read these before updating this page.
> - `../micro-cronjobs/internal/model/cronjob.go` — the Go struct and its GORM column mapping (read in full)
> - `../micro-cronjobs/migrations/*.up.sql` — every DDL change to `"CRONJOBS"."Cronjob"`, in order (all ten files read)
> - `../micro-cronjobs/internal/executor/{executor.go,report.go,notification.go,cleanup.go,dashboard.go,activity_rollup.go,activity_retention.go}` — the six dispatch targets (read in full)
> - `../micro-cronjobs/internal/scheduler/scheduler.go`, `cmd/server/main.go` — polling, retry, timezone (read in full)
> - `../micro-cronjobs/internal/handler/cronjob_handler.go`, `internal/repository/cronjob_repo.go` — the REST surface and the row-level write path (read in full)
> - `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/{platform_cronjobs.controller.ts,platform_cronjobs.service.ts}` — the only permission gate in front of the above (read in full)
>
> Verified against `carmen-platform` HEAD `157a65e` (2026-09-04), `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06), and `micro-cronjobs` HEAD `d17d8eb9bc3` (2026-09-04). Each hash confirmed with `git -C <repo> cat-file -e <hash>`.

## 1. Overview

The seeded skeleton for this page pointed at `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` as the source for this table. **That is wrong, and worth stating plainly rather than quietly fixing:** grepping the platform's Prisma schema for `Cronjob`/`CRONJOBS` returns nothing. The table is not a Prisma model at all — it is owned entirely by `../micro-cronjobs`'s own hand-written SQL migrations, in its own Postgres schema (`"CRONJOBS"`), read and written through `gorm`, not Prisma. Every claim on this page traces back to that repository's migrations and Go source, not to the platform's shared schema.

`"CRONJOBS"."Cronjob"` is also a **shared** table in a second sense: rows are written both by this module's own create/edit form and by other backend services acting on a business unit's behalf (most notably recurring report schedules — see the landing page §2). One row, one job; nothing here associates a job with the business unit it might logically belong to except whatever `bu_codes` happen to sit inside that row's own `job_config`.

## 2. Entity: `"CRONJOBS"."Cronjob"`

| Column (Postgres) | Go field | Type | Written by |
| --- | --- | --- | --- |
| `id` | `ID` | `UUID`, `default gen_random_uuid()` | DB, on insert |
| `name` | `Name` | `VARCHAR(255) NOT NULL` | Operator (create/edit form) or the creating service |
| `description` | `Description` | `TEXT`, nullable | Operator or creating service |
| `"jobType"` | `JobType` | `VARCHAR(50) NOT NULL` | Set once at creation; the update DTO does not accept it |
| `"cronExpression"` | `CronExpression` | `VARCHAR(100) NOT NULL` | Operator, via the schedule builder or raw expression field |
| `"jobData"` | `JobConfig` | `JSONB`, serialized as `any` | Operator, via the per-type config fields (§3) |
| `"sourceService"` / `"sourceID"` | `SourceService` / `SourceID` | `VARCHAR(100)` / `VARCHAR(255)`, nullable | The creating service only — stripped from every payload this console's own create/update calls send, so an edit through this console can never set or clear them |
| `"isActive"` | `IsActive` | `BOOLEAN DEFAULT true` | Operator (Start/Stop actions, or the Active checkbox on the form) |
| `"lastRunAt"` / `"nextRunAt"` | `LastRunAt` / `NextRunAt` | `TIMESTAMPTZ`, nullable | **The scheduler only**, after every scheduled or manually triggered run |
| `"lastError"` | `LastError` | `TEXT`, nullable | The scheduler only — the failing run's `err.Error()` string, or `NULL` cleared on the next successful run |
| `"runCount"` | `RunCount` | `INTEGER DEFAULT 0` | The scheduler only, incremented on every run attempt (success or failure) |
| `"notifyAt"` | `NotifyAt` | `VARCHAR(5)`, nullable, `CHECK` constrains it to `HH:mm` | Operator — **`report` job type only**; no other executor reads it |
| `"notifyDayOffset"` | `NotifyDayOffset` | `SMALLINT DEFAULT 0`, `CHECK` between 0 and 7 | **Not settable from this console's UI at all** — see §4.4 |
| `"maxRetries"` | `MaxRetries` | `INTEGER DEFAULT 0` | Operator (Execution card) |
| `"retryCount"` | `RetryCount` | `INTEGER DEFAULT 0` | The scheduler only — incremented per failed retry attempt, reset to 0 on the next success |
| `"timeoutSeconds"` | `TimeoutSeconds` | `INTEGER DEFAULT 300` | Operator (Execution card) |
| `"docVersion"` | `DocVersion` | `INT NOT NULL DEFAULT 1` | Bumped by every human edit through the update path; **deliberately not bumped** by the scheduler's own `UpdateLastRun` write |
| `"createdAt"` / `"createdByID"` / `"updatedAt"` / `"updatedByID"` | — | `TIMESTAMPTZ` / `UUID` | Standard audit columns |
| `"deletedAt"` | — | `TIMESTAMPTZ`, nullable | Soft delete — every read path filters `"deletedAt" IS NULL` |

**No unique constraint on `name`.** Two active jobs can share a name; nothing in the schema or the service layer prevents it (unlike, for example, [Database Pools](/en/platform/database-pools/data-model) §2, which does enforce name uniqueness at the application layer).

### 2.1 Schema history

The table has been renamed and restructured twice since its first migration, entirely within `micro-cronjobs`'s own migration chain:

1. `20260405120000_create_cronjob.up.sql` — first shape, `snake_case` columns, in whichever schema `search_path` pointed at.
2. `20260406010000_move_to_cronjobs_schema.up.sql` — dropped that table and an earlier Prisma-generated one, recreated it explicitly in `"CRONJOBS"`, and added `source_service`/`source_id` for multi-service ownership.
3. `20260406135707_update_field.up.sql` — renamed the table `tb_cronjob` → `"Cronjob"` and every column from `snake_case` to `camelCase` (the shape in the table above).
4. `20260610120000_seed_dashboard_refresh_jobs.up.sql` — seeded the three `dashboard_refresh` rows (landing page §3.2); no schema change.
5. `20260730092930_seed_activity_rollup_job.up.sql` / `20260730093731_seed_activity_retention_job.up.sql` — seeded the two Activity Events jobs; no schema change.
6. `20260824100000_add_notify_at_column.up.sql` — added `"notifyAt"`, migrated any pre-existing value out of `jobData->schedule_config->notify_time` (backfilled only if it already matched `HH:mm`), then deleted that key from `jobData`.
7. `20260902104533_add_doc_version.up.sql` — added `"docVersion"` (default 1) for optimistic locking on human edits.
8. `20260903100000_add_notify_day_offset.up.sql` — added `"notifyDayOffset"` (default 0, `CHECK 0..7`), explicitly framed by its own comment as a fact about the schedule, not a value inferred at run time — see §4.4.

## 3. Job Types and Their Configs

`job_config` is a discriminated-by-`job_type` JSON blob with no shared shape across the six types (the frontend's own `CronJobConfig` union has almost no overlapping property names — `../carmen-platform/src/types/index.ts:1691-1697`). Every field below is optional at the Go struct level; the executor is what actually enforces which ones are required at run time.

### 3.1 `report`

| Field | Required at run time? | Notes |
|---|---|---|
| `template_id` | No | Report template to render |
| `bu_codes` | **Yes** — `ReportExecutor.Execute()` returns `"report job config missing bu_codes"` if empty | The console's own hint text used to say "leave empty for all business units," copied from the `dashboard_refresh` fields — corrected in the current UI to say it is required |
| `format` | No | `pdf` / `excel` / `csv` / `json`; also picks the legacy delivery path when `delivery.type` is unset |
| `filters` | No | Free-form key/value pairs, editable as rows in the form |
| `recipients` | No (but empty means nobody is notified) | **User IDs, not email addresses** — passed straight through as `audience.user_ids` to the notification envelope; an earlier version of this field took free-text email strings, which never resolved to anyone |
| `delivery.type` | No | `file` (legacy — micro-report renders and notifies itself) or `viewer_url` (mints a shareable link, this executor notifies) |
| `delivery.viewer_endpoint` | No, and **deliberately not editable from the form** | The Go executor ignores a relative URL (what the SPA would otherwise store, a Next.js proxy path unreachable from this backend) and composes its own from `REPORT_SERVICE_URL` + the first `bu_code`; the form has no input for this field at all specifically because a browser-writable value controlling a server-side POST would be an authenticated SSRF primitive gated only on `cronjob.manage` |
| `notifications.{web,email,mail_source}` | No | `mail_source: "external"` switches delivery to the business unit's own `report_email` SMTP config in `tb_application_config`; default is `"internal"` (the notification service's own SMTP env) |

This is the **only** job type that reads the row-level `notify_at`/`notify_day_offset` columns — no other executor even looks at them. `notify_at` (`HH:mm`) plus `notify_day_offset` (days to add first) together resolve to the instant recipients are told the report is ready; if that computed instant has already passed by the time the run finishes, the notification goes out immediately instead of waiting a full day (`scheduledNotifyAt()`, `report.go`).

### 3.2 `notification`

| Field | Required at run time? | Notes |
|---|---|---|
| `title` / `message` | No, but an empty title/message still sends | Sent verbatim; title truncated to 255 runes |
| `type` / `category` | No | `category` defaults to `system` if unset |
| `user_ids` | **Yes** — `NotificationExecutor.Execute()` returns `"notification job config missing user_ids"` if empty | Same required-not-optional correction as `report.bu_codes` (§3.1) applies to this field's form hint |

### 3.3 `cleanup`

| Field | Required at run time? | Notes |
|---|---|---|
| `action` / `type` / `older_than` | No — nothing is validated | The executor logs these three values and returns `nil` unconditionally |

**This job type does nothing.** `CleanupExecutor.Execute()` (`cleanup.go`, read in full) is a nine-line function whose entire body is a structured log line followed by `// TODO: implement cleanup logic per type` and `return nil`. A `cleanup` job scheduled through this console will run on schedule, log its own config, report success (`last_error` stays `NULL`, `run_count` increments), and delete nothing. This is stated as a fact read directly from the executor's source, not inferred from the absence of a deletion call elsewhere — the function is short enough to read in full and confirm.

### 3.4 `dashboard_refresh`

| Field | Required at run time? | Notes |
|---|---|---|
| `bu_codes` | No — empty means every active business unit | The one job type where the console's "leave empty for all" hint is accurate |
| `tier` | No — empty means every tier | `operational` / `breakdown` / `matrix`, mirroring `micro-data`'s materialized-view groupings |

The executor's HTTP client has its own 5-minute timeout (independent of the job row's own `timeout_seconds`), described in its own comment as needed because "a full sweep across every tenant's materialized views can take a while." Per-materialized-view errors returned inside the `micro-data` response body are logged as a warning but **do not** fail the job or set `last_error` — see §5.4.

### 3.5 `activity_rollup`

| Field | Required at run time? | Notes |
|---|---|---|
| `days_back` | No — default 2 | How many trailing UTC days to recompute; 2 rather than 1 so a late-arriving event from yesterday still gets folded into its correct daily bucket |

Full write path and enforcement point documented in [Activity Events — Data Model](/en/platform/activity-events/data-model) §4.2; this page agrees with that account (landing page §3.2).

### 3.6 `activity_retention`

| Field | Required at run time? | Notes |
|---|---|---|
| `retention_days` | No — default 365 | Rows older than this, by `server_ts`, are eligible for deletion |
| `batch_size` | No — default 10000 | Rows deleted per `DELETE ... LIMIT` iteration, looping until a pass deletes zero |

Full write path and enforcement point documented in [Activity Events — Data Model](/en/platform/activity-events/data-model) §4.1; this page agrees with that account (landing page §3.2).

## 4. Scheduler Behavior

### 4.1 Polling and reconciliation

`micro-cronjobs` holds every active job (`isActive = true AND "deletedAt" IS NULL`) in an in-memory `go-cron` scheduler (`gocron/v2`). A background loop reloads that set from the database once a minute (`pollInterval = 1 * time.Minute`, `scheduler.go`) and reconciles three ways:

- A job no longer in the active set is removed from the in-memory scheduler.
- A job present but not yet scheduled is added.
- A job whose **cron expression, `job_config`, `notify_at`, or `notify_day_offset`** changed since the last poll is removed and re-added with the new values — `gocron` has no in-place "update a running job's schedule" API, so this is the only way an edit takes effect. The comparison is a fingerprint (`revisionOf()`) built from the cron string plus a SHA-256 hash of the JSON-encoded `job_config` — `encoding/json` sorts map keys, so the hash is stable across polls regardless of key order.

Every create, update, delete, start, or stop call from the gateway also triggers `ForceSync()` — an immediate, asynchronous re-run of the same reconciliation, so a saved change is usually applied well before the next scheduled poll in practice. It is fire-and-forget (`go s.syncJobs()`), so the HTTP response the console receives carries no confirmation that the in-memory scheduler has already picked up the change.

### 4.2 Timezone

Resolved **once**, at process startup (`cmd/server/main.go:142-166`): the primary business unit's configured IANA timezone (`BusinessUnitRepo.PrimaryTimezone()`), falling back to `DEFAULT_TIMEZONE` (env, default `Asia/Bangkok`) if that lookup errors or returns empty, and falling back to UTC if the resolved name fails to load. The chosen location becomes both `time.Local` for the whole process and the location every cron expression is interpreted in — including the seeded jobs in the landing page §3.2, whose "03:30"/"04:00" times are in this zone, normally Asia/Bangkok. This matches and independently confirms the account in [Activity Events — Data Model](/en/platform/activity-events/data-model) §4.1's "HQ BU timezone" framing.

### 4.3 Retries, timeouts, concurrency

- **Timeout:** `timeout_seconds` (row field, default 300s) wraps the run in a `context.WithTimeout`, for both a scheduled fire (`addJob`'s task closure) and a manual "Run Now" (the handler's own detached goroutine uses the identical value).
- **Retry:** on failure, `retryJob()` retries synchronously — blocking the same goroutine, not queuing a new scheduled fire — up to `max_retries` times, waiting `attempt² × 10s` between attempts (10s, 40s, 90s, 160s, ...). Every attempt, success or failure, writes `last_run_at`/`last_error`/`retry_count` to the row as it happens, so a job's `retry_count` reflects the number of retry attempts made on its most recent run, reset to 0 the moment any attempt (initial or retry) succeeds.
- **Concurrency:** `gocron.WithLimitConcurrentJobs(5, gocron.LimitModeWait)` caps the whole process at 5 simultaneously-running jobs; a sixth due job waits rather than running alongside the others.
- **Manual execution** (`POST /:id/execute`): detaches from the inbound HTTP request's context specifically so that closing the browser tab or the request timing out does not cancel an in-flight report render or notification dispatch, then runs in a background goroutine and returns `{"message": "execution triggered"}` before the outcome is known.

## 5. Where a Failed Run Becomes Visible

This is the answer the landing page defers to this section (§3.5 there). Read top to bottom, this is everywhere a failed run's evidence exists, and what each place does and does not show.

### 5.1 The database row (`last_error`, `retry_count`, `run_count`)

`CronJobRepo.UpdateLastRun()` is called after **every** run — scheduled, retried, or manually triggered — and sets `last_run_at`, `next_run_at`, increments `run_count`, and sets `last_error` to either the failing error's message or `NULL` on success (resetting `retry_count` to 0 in the success case, incrementing it in the failure case). This call deliberately never touches `doc_version`, so a job's edit form is never rejected as "modified by someone else" purely because the scheduler ran it in the background — that concurrency-control detail is called out explicitly in the repository's own comment.

### 5.2 The list page (`CronJobManagement`, `/cronjobs`)

- **Last Run column:** relative time (e.g. "2 hours ago", tooltip shows the absolute timestamp) plus a small warning-triangle icon, rendered **only when `last_error` is non-empty**, whose own tooltip holds the raw error string verbatim. This is the only place in the console a human reads the actual failure text.
- **"With Errors" summary stat:** a dedicated count in the stat band above the table (`items.filter(j => !!j.last_error).length`). It counts only the rows currently loaded on the page — the band's own caption says so — not every failing job across the whole table; there is no server-side "has error" filter to see every failure at once (§6).
- **No run history.** A row holds only its single most recent run's outcome. A job that failed twice, then succeeded on a third attempt, shows a clean `last_error` (`NULL`) and a `retry_count` of 0 the moment that final attempt lands — the two earlier failures leave no visible trace on this screen once the run as a whole succeeds.

### 5.3 The edit page (`CronJobEdit`, `/cronjobs/:id/edit`)

**Shows none of it.** The page's own "History" card renders only `created_at`/`created_by_id`/`updated_at`/`updated_by_id` via `AuditMeta` — who last edited the row's *configuration*, not anything about its *execution*. `last_run_at`, `next_run_at`, `last_error`, and `run_count` are all present on the loaded record (`jobRecord`, visible in the dev-only debug panel) but are not rendered anywhere on this page. A tester who opens Edit expecting to find out why a job failed will not find it there.

### 5.4 What does not surface as `last_error` at all

`dashboard_refresh`'s executor treats a successful HTTP call to `micro-data` as job success even when that response body's own `errors` array is non-empty — per-materialized-view failures are logged as a warning (`DashboardRefreshExecutor.Execute()`, own comment: "the endpoint itself succeeded and the next scheduled run retries naturally") but never reach `last_error`. A partial refresh failure is therefore invisible anywhere in this console — not the Last Run icon, not the "With Errors" stat — and is only discoverable in the Go service's own logs or an OpenTelemetry trace (§5.5).

### 5.5 Observability (SigNoz via OpenTelemetry)

`executor.go`'s `Execute()` opens one root span per run (`cronjob <job_type>`) and calls `span.RecordError(err)` plus `span.SetStatus(codes.Error, ...)` on failure. This is the only place a full timing/stack trace of a specific failed run exists, and it requires access to the configured SigNoz instance — out of reach for a tester using only the platform console.

### 5.6 A second, independent failure signal: the scheduler status mismatch

The list page's summary band shows **"Active in Scheduler"** from `GET /api/cronjobs/status` → `scheduler.ActiveJobCount()` — a live, in-memory count, deliberately computed independently of the DB-derived "Running"/"Stopped" figures on the same band. The component's own comment states the reason: a disagreement between the two (for example, "Running: 12" from the database against "Active in Scheduler: 9") is itself evidence the scheduler process is stuck or behind on its poll cycle, not a display bug to be reconciled away.

## 6. Edge Cases

| Scenario | What actually happens | Source |
|---|---|---|
| A `cleanup` job is scheduled and runs | Logs its config, reports success, deletes nothing — the executor has no implementation | `cleanup.go` (full, `// TODO`) |
| `dashboard_refresh` partially fails (some materialized views error) | Job still reports success; `last_error` stays `NULL`; per-MV errors are logged only, not surfaced in the console | `dashboard.go` (§5.4) |
| An operator wants to change when a `report` job's recipients are notified relative to the run, on a day other than the run day | Cannot — the create/edit form has no field for `notify_day_offset`; every job authored through this console keeps the column's default (0, same-day) even though the backend and executor fully support 0–7 | `types/index.ts:1735-1746` (no field in `CronJobWriteInput`), `CronJobEdit.tsx` (no input rendered) |
| A `cronjob.read`-only session opens `/cronjobs/new` | Sees and can fill every field of the create form; cannot submit — Save is not rendered, and `handleSave()` returns before calling the API | `CronJobEdit.tsx:171`, `App.tsx:531-551` |
| The gateway responds `409 FOREIGN_OWNED_JOB` | Frontend still has a branch for this code, but the current gateway's `update()`/`delete()` run no ownership check and cannot produce it — dead code kept for backward compatibility with an older gateway build | `CronJobEdit.tsx` (comment), `platform_cronjobs.service.ts` ("No ownership check") |
| An operator wants to see every currently-failing job across the whole table, not just the loaded page | No server-side filter exists for "has `last_error`"; the "With Errors" stat and the sortable columns do not include one | `CronJobManagement.tsx` (§5.2), `platform_cronjobs.service.ts` (`SORTABLE` set has no error column) |
| A schedule is edited and saved | Applied to the in-memory scheduler on the next `ForceSync()` (typically near-immediate) or, failing that, the next poll (up to ~1 minute later) — no confirmation of either is returned to the browser | `scheduler.go` (`ForceSync`, `syncJobs`) |
| A caller reaches `micro-cronjobs` directly, bypassing the gateway | Every operation succeeds — the service has no authentication of its own | `platform_cronjobs.controller.ts` (doc comment), `platform_cronjobs.service.ts` (doc comment) |

## 7. Recommendations

- **Implement `CleanupExecutor`, or remove `cleanup` from the create-form's job-type list** until it does something — as it stands, an operator can schedule a job that always silently reports success while deleting nothing.
- **Surface `dashboard_refresh`'s per-MV error array in the console**, or at minimum set `last_error` when that array is non-empty, so a partial materialized-view refresh failure is visible without a log or trace lookup.
- **Add a `notify_day_offset` control to the report job's schedule section**, alongside the existing `notify_at` time input — the backend and executor already fully support the full 0–7 range; only the console cannot set it.
- **Add a server-side "has error" filter** (or a sort on `last_error IS NOT NULL`) so an operator can find every currently-failing job across the whole table, not only the page currently loaded.
- **Consider a run-history table**, even a short rolling window, since the current schema keeps only the single most recent run's outcome per job — a job whose failures precede its most recent success currently looks indistinguishable from one that has never failed.

## 8. References

- `../micro-cronjobs/internal/model/cronjob.go` (139 lines) — the Go struct, table name, and every job-type config struct.
- `../micro-cronjobs/internal/executor/executor.go` (85 lines), `report.go` (422 lines), `notification.go` (102 lines), `cleanup.go` (40 lines), `dashboard.go` (98 lines), `activity_rollup.go` (80 lines), `activity_retention.go` (64 lines) — all read in full.
- `../micro-cronjobs/internal/scheduler/scheduler.go` (345 lines) — polling, reconciliation, retry, `ForceSync`, `ExecuteNow`.
- `../micro-cronjobs/internal/handler/cronjob_handler.go` (451 lines) — the REST surface (`list`, `status`, `getByID`, `create`, `update`, `delete`, `start`, `stop`, `execute`, `getBySource`, `updateBySource`, `deleteBySource`).
- `../micro-cronjobs/internal/repository/cronjob_repo.go` (207 lines) — `UpdateLastRun`, optimistic-lock `Update`, `FindActive`/`FindBySource`.
- `../micro-cronjobs/cmd/server/main.go` (166 lines) — wiring, timezone resolution.
- `../micro-cronjobs/migrations/{20260405120000,20260406010000,20260406135707,20260610120000,20260730092930,20260730093731,20260824100000,20260902104533,20260903100000}_*.up.sql` — all ten migration files, read in full.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/platform_cronjobs.service.ts` — the ownership-check removal comments (§5, edge cases).
- `../carmen-platform/src/types/index.ts:1660-1746` — frontend type shapes, cross-checked against the Go struct field-for-field.
- [Activity Events — Data Model](/en/platform/activity-events/data-model) §4 — the `activity_rollup`/`activity_retention` account this page agrees with.
- [Database Pools — Data Model](/en/platform/database-pools/data-model) §2 — the sibling module's name-uniqueness enforcement, contrasted in §2 above.
