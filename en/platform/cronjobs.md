---
title: Cronjobs
description: The platform's scheduling console over the shared "CRONJOBS"."Cronjob" table — six job types, who runs them (../micro-cronjobs), and exactly where a failed run becomes visible.
published: true
date: '2026-09-06T23:10:00.000Z'
tags: book/platform, cronjobs
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Cronjobs

> **At a Glance**
> **Module purpose:** Platform-wide admin console over one shared table, `"CRONJOBS"."Cronjob"`, that this module and other backend services both write scheduled jobs into &nbsp;·&nbsp; **Screens:** `CronJobManagement` (list, `/cronjobs`) and `CronJobEdit`, used for both create (`/cronjobs/new`) and edit (`/cronjobs/:id/edit`) &nbsp;·&nbsp; **Backing service:** [`../micro-cronjobs`](#6-reference-sources) (Go) — a standalone scheduler/worker process with **no authentication of its own** &nbsp;·&nbsp; **Nav entry:** `permission: 'cronjob.read'`, its own nav group `navGroup.scheduling` — not folded into `navGroup.platform` &nbsp;·&nbsp; **Feature flag:** `cronjobs` &nbsp;·&nbsp; **Two-permission model:** `cronjob.read` (the **only** permission the frontend route guard checks on all three routes, including `/new` and `/:id/edit`) and `cronjob.manage` (every mutating action — start/stop/run-now/edit/delete/create — gated by `<Can>` **and** re-checked in the submit handler) &nbsp;·&nbsp; **Role assignment:** only the **Platform Admin** role holds any `cronjob.*` permission &nbsp;·&nbsp; **Job types:** 6 — `report`, `notification`, `cleanup`, `dashboard_refresh`, `activity_rollup`, `activity_retention` &nbsp;·&nbsp; **e2e suite:** **none** — `../carmen-platform-e2e/tests/` has no `cronjobs` directory &nbsp;·&nbsp; **Sub-pages:** 2

## 1. Overview

**Cronjobs** is the platform's window onto every scheduled background job in Carmen — one list (`CronJobManagement.tsx`, read in full) and one create/edit form (`CronJobEdit.tsx`, read in full), both reached under `/cronjobs`. The screen itself does nothing but read and write rows; the work each row describes — sending a report, refreshing a dashboard, deleting old telemetry — is carried out entirely by a separate Go service, **`../micro-cronjobs`**, polling the same database table this console edits. Understanding this module means understanding both halves: what the console lets an operator configure, and what the worker actually does with that configuration once saved — including, critically, where a run that failed becomes visible to someone testing it.

The console proxies through `backend-gateway`'s `PlatformCronjobsController` / `PlatformCronjobsService` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/`), which in turn calls `micro-cronjobs`'s own REST API (`CRONJOB_SERVICE_URL`) over plain HTTP. `micro-cronjobs` has no login, no session, no API key of its own — the gateway controller's own doc comment states this outright: it "is the only thing standing between a browser and a service that will delete any job for anyone," and `CRONJOB_SERVICE_URL` must never be exposed to the frontend. Every permission check a tester can observe from the browser happens at the gateway, not in the worker.

## 2. Business Context

`"CRONJOBS"."Cronjob"` is not owned exclusively by this module — it is a **shared table**. Some rows are created here, by an operator, through this console (`source_service` is empty, shown as "Platform" in the Owner column). Other rows are created by a different service on a business unit's behalf — most notably `reports.service.ts` in `backend-gateway` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/reports/reports.service.ts`), which calls `micro-cronjobs`'s `by-source` endpoints directly (its own `cronjobHttp` client against `CRONJOB_SERVICE_URL`, bypassing this module's gateway controller entirely) whenever a business unit sets up a recurring report schedule elsewhere in the product. Those "foreign-owned" rows are still fully visible, editable, and deletable from this console — see §3 for exactly what that means and does not mean.

This is also why the module sits in its **own** nav group rather than inside `navGroup.platform`. The comment above the nav entry (`platformNav.ts:34-35`) reads: "Scheduling — งานตามเวลา ไม่ใช่การตั้งค่าระบบ จึงเป็นกลุ่มของตัวเอง" ("Scheduling — scheduled work, not system configuration, so it gets its own group"). Verified structurally rather than taken on the comment's word: `navGroup.scheduling` contains exactly one row (`/cronjobs`, grepped across the whole nav file), sitting between the Analytics group (Usage Analytics, Activity Events) and the Platform group (Platform Config, Email Settings, Applications, Roles, User Platform, Super Admins, Feature Flags) — genuinely isolated on both sides, not merged with either neighbor. The reasoning holds: everything else in `navGroup.platform` decides *who can do what* or *how the platform is configured*; Cronjobs decides *when background work runs*, which is a materially different kind of setting.

## 3. Key Concepts

- **One row, one scheduled job.** Every row is a `job_type` (one of six — §3.1), a 5-field cron expression, a type-specific `job_config` JSON blob, an active/inactive flag, and the outcome of its own most recent run (`last_run_at`, `next_run_at`, `last_error`, `run_count`). Full field table: [Data Model](/en/platform/cronjobs/data-model) §2.
- **The scheduler, not the console, decides when a job fires.** `micro-cronjobs` polls the database once a minute, holds every active job in an in-memory `go-cron` scheduler, and fires it at the moment its cron expression is next due — in the process's resolved timezone (normally `Asia/Bangkok`; see [Data Model](/en/platform/cronjobs/data-model) §4). Saving an edit here does not run the job; it changes what the next scheduled (or manually triggered) run will do.
- **"Run Now" dispatches; it does not confirm.** The execute button (`POST /:id/execute`) hands the job to a background goroutine and returns immediately — the console's own toast says "dispatched" (`toast.info`), deliberately not "succeeded," because the outcome is not yet known when the HTTP response comes back. See §3.5 and [Data Model](/en/platform/cronjobs/data-model) §5 for where that outcome eventually surfaces.
- **Ownership is visible but not a lock.** A job another service created (`source_service` set) can be started, stopped, run now, edited, or deleted from this console exactly like a platform-created one — the gateway's `update()`/`remove()`/`control()` methods run no ownership check at all (confirmed by reading `platform_cronjobs.service.ts` — each says so in its own comment). The console's only concession to ownership is informational: an Owner column/badge on the list, a warning banner on the edit page, and a different confirmation message before deleting ("this removes that business unit's report schedule for good," not a generic "delete this job?").
- **`cronjob.manage` gates every mutation; `cronjob.read` gates the page itself — including the create/edit routes.** `App.tsx:531-551` puts `requiredPermission="cronjob.read"` on **all three** routes (`/cronjobs`, `/cronjobs/new`, `/cronjobs/:id/edit`); `cronjob.manage` is checked only inside the page, via `<Can>` around every button that writes and again inside `handleSave()`. A read-only session can open the create form and fill it in, but the Save button is not rendered and the submit handler returns before calling the API. Full gate table: §4.
- **Only Platform Admin can reach this module at all.** `seed.platform-role-permission.data.ts:15` grants `cronjob.*` to Platform Admin alone; Support Manager, Support Staff, and Security Officer hold neither key, so the nav item, the route guard, and the backend all agree: nobody else sees Cronjobs.

### 3.1 Job types

| `job_type` | What it does | Config highlights | Executor (`../micro-cronjobs`) |
|---|---|---|---|
| `report` | Delivers a scheduled report — mints a shareable viewer URL or queues the legacy file-render flow, then notifies recipients | `template_id`, `bu_codes` (**required** — the executor errors without it), `format`, `filters`, `recipients` (user IDs, not free-text emails), `delivery.type` (`file` / `viewer_url`), `notifications.{web,email,mail_source}`; the only type that reads the row-level `notify_at`/`notify_day_offset` fields | `ReportExecutor` (`report.go`) |
| `notification` | Sends an ad hoc system notification to a fixed set of users | `title`, `message`, `type`, `category` (default `system`), `user_ids` (**required**) | `NotificationExecutor` (`notification.go`) |
| `cleanup` | Declared, schedulable, and logged — **but not implemented**: the executor logs its config and returns success without doing any deletion | `action`, `type`, `older_than` (free text, not validated) | `CleanupExecutor` (`cleanup.go`) — body is a `// TODO: implement cleanup logic per type` |
| `dashboard_refresh` | Rebuilds materialized views in `micro-data` | `bu_codes` (optional — empty means every active business unit), `tier` (optional — `operational` / `breakdown` / `matrix`, empty means all tiers) | `DashboardRefreshExecutor` (`dashboard.go`) |
| `activity_rollup` | Recomputes `tb_activity_event_daily` from the last N days of raw UI telemetry | `days_back` (default 2 — self-heals late-arriving events) | `ActivityRollupExecutor` (`activity_rollup.go`) — see [Activity Events — Data Model](/en/platform/activity-events/data-model) §4.2 |
| `activity_retention` | Batch-deletes raw `tb_activity_event` rows past a retention window | `retention_days` (default 365), `batch_size` (default 10000) | `ActivityRetentionExecutor` (`activity_retention.go`) — see [Activity Events — Data Model](/en/platform/activity-events/data-model) §4.1 |

`job_type` is **locked after creation** — the Select is disabled on the edit form, and the update DTO on the backend does not even accept the field, because `job_config` is a union of six structurally unrelated shapes and there is no migration path from one to another.

### 3.2 Seeded jobs already running

Three job types ship with active rows seeded by migration, not created through this console — an operator opening `/cronjobs` on a fresh environment already sees these:

| Name | `job_type` | Schedule | Config | Migration |
|---|---|---|---|---|
| Dashboard MV refresh - operational | `dashboard_refresh` | `*/5 * * * *` (every 5 min) | `{"tier":"operational"}` | `20260610120000_seed_dashboard_refresh_jobs.up.sql` |
| Dashboard MV refresh - breakdown | `dashboard_refresh` | `*/30 * * * *` (every 30 min) | `{"tier":"breakdown"}` | same |
| Dashboard MV refresh - matrix | `dashboard_refresh` | `0 */6 * * *` (every 6 hours) | `{"tier":"matrix"}` | same |
| Activity events daily rollup | `activity_rollup` | `30 3 * * *` (03:30) | `{"days_back":2}` | `20260730092930_seed_activity_rollup_job.up.sql` |
| Activity events retention (365d) | `activity_retention` | `0 4 * * *` (04:00) | `{"retention_days":365,"batch_size":10000}` | `20260730093731_seed_activity_retention_job.up.sql` |

**Agreement with [Activity Events — Data Model](/en/platform/activity-events/data-model) §4:** that page states the rollup runs at 03:30 and retention at 04:00, both against `"CRONJOBS"."Cronjob"`, both `is_active: true`. This page independently re-read both seed migrations and the executor dispatch table and reaches the identical conclusion — no discrepancy. The one thing added here that the Activity Events page had no reason to cover: these two jobs are administrable from **this** console like any other row (an operator with `cronjob.manage` could reschedule, disable, or delete either one), which is a structural fact about where they live, not a claim about whether anyone has actually done so in a live deployment.

### 3.3 Schedule format

Every `cron_expression` is a standard 5-field cron string (`minute hour day-of-month month day-of-week`) — no seconds field. The Go scheduler parses it for its own "next run" calculation with `robfig/cron`'s `cron.ParseStandard` (`scheduler.go`); the console's schedule builder (`CronScheduleField`, see [UI Screens](/en/platform/cronjobs/ui-screens) §4) offers six guided modes — every N minutes, hourly, daily, weekly, monthly, and a raw 5-field custom mode — built and parsed against the same expression string, so typing directly into the expression field and using the builder controls stay in sync with each other; there is no separate "mode" state stored anywhere.

### 3.4 Retries, timeouts, and concurrency

- **Timeout** (`timeout_seconds`, default 300): wraps the whole run in a context deadline, for both a scheduled fire and a manually triggered one.
- **Retry** (`max_retries`, default 0): on failure, the scheduler retries synchronously up to that many times with exponential backoff — 10s, 40s, 90s, and so on (`attempt² × 10s`) — updating the row's `last_run_at`/`last_error`/`retry_count` after every attempt.
- **Concurrency cap:** at most 5 jobs run at the same instant across the whole `micro-cronjobs` process (`gocron.WithLimitConcurrentJobs(5, gocron.LimitModeWait)`); a sixth due job waits its turn rather than running in parallel.
- **Poll cycle:** the scheduler reloads active jobs from the database once a minute and rebuilds (removes and re-adds) any job whose cron expression, config, or notify settings changed since the last poll — gocron has no in-place "update schedule" API. Every create/update/delete/start/stop call from the gateway also fires an immediate, asynchronous re-sync (`ForceSync()`), so in practice a saved edit is usually picked up well before the next scheduled poll — but that re-sync is fire-and-forget, so the HTTP response an operator gets back after Save carries no guarantee the scheduler has already applied it.

### 3.5 Where a failed run becomes visible

This is the question a list of job names cannot answer on its own — see [Data Model](/en/platform/cronjobs/data-model) §5 for the full account (the DB column that carries it, exactly what the list page shows and where it falls short, why the edit page shows none of it, and the OpenTelemetry trace that is the only place a full error/timing trace exists). In short: **the list page's Last Run column**, via a warning icon whose tooltip holds the raw error string, is the only place in this console a human reads what went wrong.

## 4. Roles and Permissions

| Surface | Gate | Key |
|---|---|---|
| `/cronjobs`, `/cronjobs/new`, `/cronjobs/:id/edit` routes | `PrivateRoute requiredPermission` + `feature` | `cronjob.read` + `cronjobs` (`App.tsx:531-551` — **the same single permission on all three routes**, `.manage` is never checked at the route level) |
| Sidebar "Cronjobs" entry | `permission` + `feature` filter | `cronjob.read` / `cronjobs` (`platformNav.ts:36`, its own `navGroup.scheduling`) |
| List: Add Job button (header and empty state) | `<Can>` | `cronjob.manage` |
| List: Start/Stop, Run Now, Edit, Delete icons per row | entire actions cell returns `null` unless `canManage` | `cronjob.manage` |
| Edit page: Save button in the unsaved-changes bar | `<Can>` | `cronjob.manage` |
| Edit page: `handleSave`'s own permission check, independent of the Save button | `hasPermission('cronjob.manage')`, returns early if false | `cronjob.manage` |
| Backend gateway: `GET` (list / status / one) | `AppIdGuard('cronjob.findAll'\|'.status'\|'.findOne')` + `PlatformPermissionGuard` | `cronjob.read` |
| Backend gateway: `POST`/`PATCH`/`DELETE`/start/stop/execute | `AppIdGuard('cronjob.create'\|'.update'\|'.delete'\|'.start'\|'.stop'\|'.execute')` + `PlatformPermissionGuard` | `cronjob.manage` |
| `micro-cronjobs` itself | **none** — no authentication of any kind | n/a |

Two things worth calling out precisely, both confirmed by reading the code rather than inferred from the permission names:

1. **A `cronjob.read`-only session can open the create form and every field of the edit form**, for the same reason documented for [Database Pools](/en/platform/database-pools) §4: the route guard checks only the read permission on all three routes, and `CronJobEdit.tsx` renders unconditionally regardless of `cronjob.manage`. It cannot submit through any path — the Save button lives inside `<Can permission="cronjob.manage">`, and `handleSave()` independently calls `hasPermission('cronjob.manage')` and returns before validating or calling the API, guarding against `Ctrl/Cmd+S` and the native form submit bypassing a hidden button.
2. **Ownership does not gate anything.** A `cronjob.manage` session can start, stop, run, edit, or delete a job another service created (`source_service` set) exactly as freely as a platform-created one — see §3. The frontend still defends against a `FOREIGN_OWNED_JOB` 409 error code in its error-handling branch, with a comment explaining the current gateway no longer returns it (the `assertPlatformOwned` check was removed from `update`/`delete`) but that the branch is kept in case an older gateway build is still deployed somewhere. Confirmed against `platform_cronjobs.service.ts`: `update()`, `remove()`, and `control()` each carry an explicit "No ownership check" comment.

## 5. Related Modules

- [Activity Events](/en/platform/activity-events) and its [Data Model](/en/platform/activity-events/data-model) §4 — the `activity_rollup` and `activity_retention` jobs' schedules and enforcement points are documented there in depth; this page agrees with that account (§3.2) and adds only that both rows are administrable from this console.
- [Usage Analytics](/en/platform/usage-analytics) — the dashboard that reads the table `activity_rollup` maintains; unrelated to this module's own screens.
- [Report Templates](/en/platform/report-templates) — the module a business unit's recurring report schedule is set up from; those schedules land in the same `"CRONJOBS"."Cronjob"` table this console administers, created through `backend-gateway`'s `reports.service.ts`, not through this module's own create form.
- [Database Pools](/en/platform/database-pools) §4 — the sibling module this page's read/manage permission split and "read-only session can open but not save the form" behavior directly mirrors.
- [Platform RBAC](/en/platform/rbac) — the permission catalog behind `cronjob.read`/`cronjob.manage`, and why only Platform Admin holds either key.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx:531-551` — the three routes, all three gated on `cronjob.read` only.
- `../carmen-platform/src/components/nav/platformNav.ts:34-36` — sidebar entry and the `navGroup.scheduling` comment, verified structurally against the full nav array.
- `../carmen-platform/src/constants/featureFlags.ts:67` — the `cronjobs` feature-flag entry, same `navGroup.scheduling`.
- `../carmen-platform/src/pages/cronjobs/CronJobManagement.tsx` — list page, read in full.
- `../carmen-platform/src/pages/cronjobs/CronJobEdit.tsx` — create/edit page, read in full.
- `../carmen-platform/src/pages/cronjobs/CronJobFilterSheet.tsx`, `CronScheduleField.tsx` — read in full.
- `../carmen-platform/src/pages/cronjobs/jobConfig/*.tsx` (all six type-specific config components) — read in full.
- `../carmen-platform/src/services/cronjobService.ts` — REST client and the gateway filter-encoding quirk it works around.
- `../carmen-platform/src/types/index.ts:1660-1746` — `CronJob`, `CronJobWriteInput`, `CronJobConfig` and its six member types.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_cronjobs/{platform_cronjobs.controller.ts,platform_cronjobs.service.ts,swagger/request.ts}` — gateway REST surface and HTTP proxy, read in full.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/reports/reports.service.ts` — the `by-source` job-creation path used by report schedules (`cronjobHttp`, `CRONJOB_SERVICE_URL`).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts:91-92` — `cronjob.read`/`cronjob.manage` catalog descriptions.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-role-permission.data.ts:11-15` — only Platform Admin holds `cronjob.*`.
- `../micro-cronjobs/internal/model/cronjob.go`, `internal/executor/*.go`, `internal/scheduler/scheduler.go`, `internal/handler/cronjob_handler.go`, `internal/repository/cronjob_repo.go`, `cmd/server/main.go` — all read in full; see [Data Model](/en/platform/cronjobs/data-model) §8 for the complete list with line counts.
- `../micro-cronjobs/migrations/20260610120000_seed_dashboard_refresh_jobs.up.sql`, `20260730092930_seed_activity_rollup_job.up.sql`, `20260730093731_seed_activity_retention_job.up.sql` — the seeded jobs in §3.2.
- Verified against `carmen-platform` HEAD `157a65e` (2026-09-04), `carmen-turborepo-backend-v2` HEAD `937cf5ac4` (2026-09-06), and `micro-cronjobs` HEAD `d17d8eb9bc3` (2026-09-04).
- `../carmen-platform-e2e/tests/` — listed directly (`applications`, `auth`, `broadcast`, `business-units`, `changelog`, `clusters`, `dashboard`, `journeys`, `landing`, `news`, `permission-catalog`, `print-template-mapping`, `profile`, `report-templates`, `roles`, `super-admins`, `user-platform`, `users`); no `cronjobs` directory, HEAD `a8e3b31`.

## 7. Pages in This Module

- [Data Model](/en/platform/cronjobs/data-model) — the full `"CRONJOBS"."Cronjob"` field table (owned entirely by `micro-cronjobs`'s own SQL migrations, not by the platform's Prisma schema), every job type's config shape, the scheduler's polling/retry/timezone mechanics, and the complete answer to "where does a failed run become visible."
- [UI Screens](/en/platform/cronjobs/ui-screens) — a tour of `CronJobManagement` (list, filters, summary stats, CSV export) and `CronJobEdit` (basics/schedule/execution/type-config cards, the schedule builder, version-conflict handling), including the read-permission/create-form interaction documented in §4 above.
