---
title: Report Schedule
description: Cron-driven schedule for recurring report generation — fires runs on a cadence and delivers the output to configured recipients without manual invocation.
published: true
date: 2026-05-16T17:00:00.000Z
tags: reporting-audit, schedule, automation, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Report Schedule

## 1. Purpose

Report Schedule defines **when each report runs on a cadence and where the output goes**. Every row pairs a report template with a cron expression, a frozen filter set, a delivery list, and an active flag. The cron service (`micro-cronjobs`) polls active schedules, computes the next fire time per row, and at fire enqueues a [[reporting-audit/history]] job that the reports executor (`micro-report`) picks up. The history row is the artefact of record; the schedule row is the definition.

Schedules answer two operational questions: *"is the daily inventory valuation export still going to Finance every morning at 06:00?"* and *"when did we last send the monthly vendor-spend report, and when is the next one due?"*. The `last_run_at` and `next_run_at` columns are the operator's at-a-glance health check.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_report_schedule`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar(255)` | No | Display name. |
| `report_type` | `String @db.VarChar(100)` | No | Logical report identifier (resolves a `tb_report_template` row). |
| `report_template_id` | `String? @db.Uuid` | Yes | Optional explicit template binding; otherwise resolved by `report_type`. |
| `format` | `enum_report_format` | No | Output format: `pdf`, `excel`, `csv`, `json`. |
| `cron_expression` | `String @db.VarChar(100)` | No | Standard 5- or 6-field cron expression. |
| `schedule_config` | `Json? @db.JsonB` | Yes | Scheduler options — typically `{ "timezone": "Asia/Bangkok", "jitter_seconds": 0, "misfire_policy": "fire_once" }`. |
| `filters` | `Json? @db.JsonB` | Yes | Default `{}`. Filter set applied on every run. |
| `options` | `Json? @db.JsonB` | Yes | Default `{}`. Render options. |
| `recipients` | `Json? @db.JsonB` | Yes | Default `[]`. Array of delivery targets — emails, user IDs, sFTP destinations. |
| `is_active` | `Boolean` | No | Default `true`. Disable without deleting. |
| `last_run_at` | `DateTime? @db.Timestamptz(6)` | Yes | Most recent successful fire timestamp. |
| `next_run_at` | `DateTime? @db.Timestamptz(6)` | Yes | Next planned fire timestamp. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** index on `is_active` (`idx_report_schedule_active`) — the scheduler poll filters `is_active = true AND deleted_at IS NULL AND next_run_at <= now()`. No uniqueness on `(report_type, cron_expression)`; multiple schedules per template are intentional (e.g. a daily snapshot to Finance and a weekly digest to Operations both backed by the same template).

## 3. Usage / Cross-References

- [[reporting-audit/report]] — the parent module. `report_type` and `report_template_id` resolve into `tb_report_template`; the schedule has no meaning without the template.
- [[reporting-audit/history]] — every fire writes one `tb_report_job` row. The schedule's `last_run_at` mirrors the most recent completed job for diagnostics, with the source-of-truth artefact living in history.
- [[reporting-audit/notification]] — recipients that are user IDs receive an in-app notification on completion; email recipients receive the rendered artefact as an attachment via the platform mailer.
- [[reporting-audit/activity]] — schedule create / update / delete / enable / disable are logged with `entity_type = 'report_schedule'`.
- [[access-control/user]] — `created_by_id` identifies the schedule owner; the scheduler runs as a service principal but the audit chain attributes the schedule's effect to its creator.

## 4. Configuration UI

- **Reports → Schedules** (`/report/schedules`): managed by **Sysadmin** and trusted operations users. The list shows name, report type, cron expression, next-run countdown, last status, and the active toggle. The detail screen exposes the cron builder, recipients picker, filter form rendered from the template's `dialog` definition, and a Test Run button that enqueues a one-off job with the same parameters.
- **Document detail → Print Schedule** (where applicable): some printable reports allow recurring delivery (e.g. weekly PO digest). The detail screen surfaces a thin schedule editor that writes here with `report_type` and a fixed `kind = report` template.
- **Read access** to schedules requires the corresponding report category read permission. Edit and toggle-active require the schedule-admin permission, typically held by Sysadmin only.

## 5. Business Rules

- **Cron expression format.** Standard `minute hour day-of-month month day-of-week` syntax. Examples: `0 6 * * *` (daily 06:00), `0 7 * * 1` (Monday 07:00), `0 0 1 * *` (1st of month). Timezone defaults to the tenant timezone declared in `schedule_config.timezone`; if absent, falls back to UTC.
- **Idempotency.** The scheduler uses a Redis lock keyed by `(schedule_id, fire_timestamp)` to guarantee exactly-one enqueue across replicas. A second scheduler instance racing the same fire becomes a no-op. The enqueued `tb_report_job` carries `options.schedule_id` and `options.scheduled_fire_at` for traceability.
- **Missed-fire policy.** `schedule_config.misfire_policy` is one of `fire_once` (default — fire on next poll if missed), `skip` (drop the missed slot, advance to the next), or `fire_all` (catch up by firing every missed slot). Long-stopped tenants should configure `skip` to avoid a thundering herd on resume.
- **Active flag.** Toggling `is_active = false` keeps the row but suspends polling. Reactivating recomputes `next_run_at` from the cron expression against the current time. Deletion is soft via `deleted_at`; the scheduler ignores soft-deleted rows.
- **Recipient resolution.** Each entry in `recipients` is a typed object — `{"type":"email","value":"..."}` for SMTP, `{"type":"user","value":"<uuid>"}` for in-app, `{"type":"sftp","value":"<config_id>"}` for sFTP. Unknown types are skipped with a warning on the job row's `error_message`.
- **RBAC on creation.** Only users with schedule-admin can create or edit schedules. Sysadmin holds this implicitly; per-category schedule-admin grants are managed under [[access-control/permission]].
- **Retention of schedule history.** The schedule row itself is retained indefinitely (subject to soft-delete). Its artefacts (the [[reporting-audit/history]] rows it produced) age out per the history retention policy.

## 6. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_schedule` (lines 5685-5709), `enum_report_format` (lines ~5628-5633).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/report/schedules/` — list and detail screens, with `_components/` for the cron builder and recipients picker.
- **Cron microservice:** `../micro-cronjobs/internal/scheduler/scheduler.go` (poll loop and dispatch), `../micro-cronjobs/internal/scheduler/redis_locker.go` (idempotency lock), `../micro-cronjobs/internal/repository/cronjob_repo.go` (schedule reads).
- **Reports microservice:** `../micro-report/` — consumes the enqueued job and produces the artefact recorded in [[reporting-audit/history]].
- **Cross-module:** see Section 3.
