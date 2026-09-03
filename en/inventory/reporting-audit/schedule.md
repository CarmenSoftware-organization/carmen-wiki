---
title: Report Schedule
description: Recurring report schedule — a create/list/delete-only screen backed by a generic cron-job table in the separate micro-cronjobs service, not by the tenant schema's tb_report_schedule (which has zero code references).
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, schedule, automation, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Report Schedule

> **At a Glance**
> **Route:** `/report/schedules` &nbsp;·&nbsp; **Owner:** Any authenticated user with BU context — no schedule-admin-only gate found &nbsp;·&nbsp; **Real backing:** `"CRONJOBS"."Cronjob"` table in the separate **micro-cronjobs** service, `job_type = "report"` &nbsp;·&nbsp; **Screen:** list + create dialog + delete only — no detail screen, no edit, no pause toggle, no test-run &nbsp;·&nbsp; The tenant schema's `tb_report_schedule` has **zero code references**.

![Report Schedule screen](/screenshots/reporting-audit/schedule.png)

## Implementation status (verified 2026-07-22)

The previous version of this page described `tb_report_schedule` (tenant schema) as the live backing table, plus a detail screen with a cron-expression builder, an Active toggle, a Test Run action, and a typed (`email`/`user`/`sftp`) recipients picker. A repo-wide code search found **zero references to `tb_report_schedule` anywhere in `carmen-turborepo-backend-v2/apps`** outside its own Prisma model declaration — it is a dead table, the same pattern already confirmed for `tb_attachment` and the old `tb_widget_*` family.

The real backing is `reports.service.ts`'s own doc comment: *"micro-report no longer owns schedules; they live in micro-cronjob as rows in the Cronjob table with `job_type="report"` and `source_service="micro-report"`."* `Cronjob` is a **generic** scheduler table (also used for `job_type = "notification"`, `"cleanup"`, `"dashboard_refresh"`) in its own Postgres schema/database, entirely separate from the tenant and platform Prisma schemas. Every UI-level claim below is corrected against `schedule-component.tsx`, `create-schedule-dialog.tsx`, and the `hooks/use-report-schedule.ts` hooks — the frontend has **no detail screen, no edit/update endpoint, no pause toggle, and no test-run** anywhere.

## 1. What & Who

Report Schedule defines **when a report runs and who is notified**. The screen at `/report/schedules` is a flat list (name, report type, format, frequency, active badge, next/last run, delete) plus a single **Create Schedule** dialog. There is no row-click detail view and no update mutation in the frontend — `useReportSchedules` (list), `useCreateReportSchedule` (create), and `useDeleteReportSchedule` (delete) are the only three operations wired up.

Every schedule created through the UI delivers via a **viewer link, not a rendered file**: the create dialog hardcodes `format: "viewer_url"` and `delivery: { type: "viewer_url", viewer_endpoint: ... }` on every submit — there is no format picker. When the schedule fires, `micro-cronjobs`' `ReportExecutor` mints a fresh viewer URL (`POST .../report/viewer`) and pushes it to the selected recipients as an in-app/email notification (`POST .../api/internal/notifications`) — it does **not** render or attach a PDF/Excel/CSV file. A legacy "file" delivery code path exists in the executor (calls micro-report's `generate-async`) but is unreachable from the current UI, since nothing ever sets `delivery.type` to anything but `"viewer_url"`.

**Audience:** any authenticated user with BU context can create and delete their own schedules through this screen — no distinct schedule-admin permission gate was found on the `reports.controller.ts` schedule endpoints (they carry the same `KeycloakGuard` + `X-App-Id` header as every other report endpoint, not a narrower role check).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a schedule | `/report/schedules` → **Create Schedule** | Pick a report template, frequency (daily / weekly / monthly) + time, optional per-template filters, notification channels (web / email checkboxes), and recipients (multi-select of users) |
| Set frequency | Create dialog → **Frequency** select + time picker | Weekly adds a Sun–Sat multi-toggle; monthly adds a 1–31 multi-toggle. There is **no raw cron-expression field** in the UI — the backend derives `cron_expression` from `schedule_config` when one isn't supplied |
| Pick recipients | Create dialog → **Recipients** | A checkbox multi-select over `useAllUsers()` — plain user IDs, not typed `email`/`user`/`sftp` entries |
| See last/next fire | List → **Last Run** / **Next Run** columns | Populated from the `Cronjob` row's `lastRunAt`/`nextRunAt` |
| Delete a schedule | List → row trash icon | Confirmation dialog, then `DELETE .../schedules/:id` |
| **Not available anywhere in the UI** | — | Editing an existing schedule, pausing/reactivating (`is_active` is display-only), a cron-expression builder, and a manual "run now" test |

## 3. Common Questions

| Symptom / Question | Cause / Answer | Action |
|---|---|---|
| Why can't I edit a schedule? | No update endpoint is exposed by `reports.controller.ts` — only create, list, and delete | Delete and recreate |
| Why can't I pause a schedule? | No toggle mutation anywhere in the frontend; the Active badge is read-only | Delete it if it should stop firing |
| Why does the fired report always arrive as a link, not a file? | The create dialog always sends `format: "viewer_url"` — the "file" (PDF/Excel/CSV render) delivery path exists in the executor but nothing in the UI ever selects it | Open the viewer link; download from there if the viewer supports it |
| What happens if two scheduler instances are running? | `micro-cronjobs`' scheduler uses a Redis `SET NX` lock (key `cronjob:lock:<job-id>`, 5-minute TTL) per job execution via `go-cron`'s distributed locker — exactly-once execution across replicas | — |
| Which timezone does the schedule run in? | The scheduler process's own `time.Location` (defaults to `time.Local` if unset) — there is **no per-schedule timezone field** on the `Cronjob` model | Confirm the scheduler process's configured timezone with Ops rather than assuming per-schedule control |
| Are missed fires (downtime) caught up? | No misfire-policy field exists on the `Cronjob` model — `go-cron` simply resumes polling on restart; no catch-up/skip configuration was found | — |
| Who can create schedules? | Any authenticated user in BU context — no distinct schedule-admin gate was found | — |

## 4. Edge Cases

- **`is_active` is always `true` on create and never toggled.** `reports.service.ts`'s `createSchedule()` hardcodes `is_active: true` on every payload sent to `micro-cronjobs`; nothing in the reachable UI ever flips it.
- **Recipients are plain user IDs.** The `recipients` array holds user UUIDs selected from the standard user picker — no `email`/`sftp` recipient type exists in the current schema or UI, despite the type definitions in `types/report-schedule.ts` allowing other `ReportFormat` string values that are never actually set by the create flow.
- **The Redis lock is per job-execution, not per `(schedule_id, fire_timestamp)`.** `RedisLocker.Lock()` takes a single `key` argument (the job's gocron identity) and locks it with a 5-minute TTL via `SET NX` — there is no fire-timestamp component in the lock key.
- **Cron expression is derived, not authored.** When the frontend omits `cron_expression`, the gateway's `cronFromConfig()` derives one from `schedule_config.frequency`/`time`/`days_of_week`/`days_of_month` — e.g. `daily` → `mm hh * * *`.
- **Recurring schedules never write to `tb_report_job`.** Because every schedule delivers via `viewer_url` (see §1), the fire path never creates a report-job row — see [reporting-audit/history](/en/inventory/reporting-audit/history) for the resulting gap in the history log.

---

## 5. Data Model (Dev)

Source: **`micro-cronjobs` service's own Postgres schema** (`"CRONJOBS"."Cronjob"`) — not the tenant Prisma schema. `tb_report_schedule` (tenant schema) is listed for contrast only; it is dead.

### 5.1 `Cronjob` (real backing table, `job_type = "report"` rows)

| Field (Go struct / DB column) | Type | Description |
| --- | --- | --- |
| `ID` / `id` | `uuid` | Primary key. |
| `Name` / `name` | `string` | Display name — the schedule's `name`. |
| `Description` / `description` | `string?` | Auto-set to `"Scheduled report: <report_type>"`. |
| `JobType` / `jobType` | `string` | `"report"` for schedules created from this screen; `"notification"` / `"cleanup"` / `"dashboard_refresh"` for other cron consumers. |
| `CronExpression` / `cronExpression` | `string` | Standard cron, supplied directly or derived from `schedule_config`. |
| `JobConfig` / `jobData` | `jsonb` | `ReportJobConfig`: `template_id`, `bu_codes`, `format`, `filters`, `recipients`, `user_id`, `options`, `delivery`, `notifications`. |
| `SourceService` / `sourceService` | `string?` | `"micro-report"` for report schedules. |
| `SourceID` / `sourceID` | `string?` | The report template id (or `report_type` fallback). |
| `IsActive` / `isActive` | `bool` | Default `true`. Always `true` on create; no UI path flips it. |
| `LastRunAt` / `lastRunAt`, `NextRunAt` / `nextRunAt` | `timestamp?` | Scheduler bookkeeping. |
| `LastError` / `lastError` | `string?` | Populated on execution failure. |
| `RunCount` / `runCount` | `int` | Default `0`. |
| `MaxRetries` / `maxRetries`, `RetryCount` / `retryCount` | `int` | Default `0`. Exponential-backoff retry (`10s, 40s, 90s, …`) when `MaxRetries > 0`. |
| `TimeoutSeconds` / `timeoutSeconds` | `int` | Default `300`. |
| Audit columns | mixed | `createdAt`/`createdByID`, `updatedAt`/`updatedByID`, `deletedAt` (soft delete). |

**Table:** `"CRONJOBS"."Cronjob"` (schema-qualified, double-quoted to preserve case — this is a distinct Postgres schema, not the tenant or platform database).

### 5.2 `ReportJobConfig` (the `jobData`/`JobConfig` JSONB shape for `job_type = "report"`)

`template_id`, `bu_codes: string[]`, `format`, `filters: map[string]string`, `recipients: string[]`, `user_id`, `options: map[string]any`, `delivery: { type, viewer_endpoint }`, `notifications: { web, email, mail_source }`.

### 5.3 `tb_report_schedule` (tenant schema — dead table, kept for contrast)

`id` / `name` / `report_type` / `report_template_id` / `format` / `cron_expression` / `schedule_config` / `filters` / `options` / `recipients` / `is_active` / `last_run_at` / `next_run_at` / audit columns. Shaped almost identically to the real `Cronjob` + `ReportJobConfig` pair above but **zero non-schema code references were found anywhere** in `carmen-turborepo-backend-v2/apps` or `micro-report`/`micro-cronjobs`.

## 6. Business Rules

- **`Cronjob` (micro-cronjobs) is the real schedule store; `tb_report_schedule` is dead.** Confirmed by a repo-wide search across TypeScript and Go source.
- **Create-only lifecycle from the UI.** No update endpoint is exposed anywhere in `reports.controller.ts`'s schedule routes — only `POST /schedules` (create), `GET /schedules` (list), `DELETE /schedules/:id` (delete).
- **Delivery is always `viewer_url` from this screen.** The legacy file-render delivery path exists in the executor but is unreachable from the current create dialog.
- **Redis-locked, exactly-once execution.** `go-cron`'s distributed locker + a Redis `SET NX` key (`cronjob:lock:<job-id>`, 5-minute TTL) prevents double-fire across scheduler replicas.
- **Poll-based, not event-driven.** The scheduler polls `Cronjob` rows on a 1-minute interval and reconciles in-memory `go-cron` jobs against the DB — editing `cron_expression` directly in the DB (no UI path does this) takes effect on the next poll.
- **No misfire policy, no per-schedule timezone.** Neither field exists on the `Cronjob` model — both were previously documented as configurable and are corrected here as absent.

## 7. Cross-References

- [reporting-audit/report](/en/inventory/reporting-audit/report) — parent module; `report_template_id` resolves a `tb_report_template` row (platform schema, still real).
- [reporting-audit/history](/en/inventory/reporting-audit/history) — because every schedule created through this screen delivers via `viewer_url`, fired schedules do **not** write a `tb_report_job` row — see that page's Implementation status callout for the resulting gap.
- [reporting-audit/notification](/en/inventory/reporting-audit/notification) — the actual delivery mechanism: a `POST /api/internal/notifications` call per recipient when a schedule fires.
- [access-control/user](/en/inventory/access-control/user) — recipients are plain user IDs.

## 8. References

- **Real backing (Go, `micro-cronjobs`):** `../micro-cronjobs/internal/model/cronjob.go` (`CronJob`, `ReportJobConfig`, `ReportDelivery`, `ReportNotifications`), `../micro-cronjobs/internal/repository/cronjob_repo.go`, `../micro-cronjobs/internal/scheduler/scheduler.go` (poll loop, retry), `../micro-cronjobs/internal/scheduler/redis_locker.go` (distributed lock), `../micro-cronjobs/internal/executor/report.go` (`viewer_url` vs `file` delivery dispatch).
- **Gateway (schedule CRUD proxy → micro-cronjobs):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/reports/reports.controller.ts` (`@Post('schedules')`, `@Get('schedules')`, `@Delete('schedules/:schedule_id')`), `reports.service.ts` (`createSchedule`/`listSchedules`/`deleteSchedule`, `cronFromConfig()`).
- **Prisma tenant (dead table, for contrast):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_schedule` (line ~6128).
- **Frontend route:** `../carmen-inventory-frontend-react/routes/report/schedules/report-schedules.route.tsx`, `schedule-component.tsx`, `create-schedule-dialog.tsx`, `schedule-frequency-field.tsx`, `schedule-recipients-field.tsx`, `schedule-notifications-field.tsx`.
- **Frontend hooks/types:** `../carmen-inventory-frontend-react/hooks/use-report-schedule.ts` (`useReportSchedules`, `useCreateReportSchedule`, `useDeleteReportSchedule` — no update hook exists), `types/report-schedule.ts`.
