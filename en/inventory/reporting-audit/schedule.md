---
title: Report Schedule
description: Cron-driven schedule for recurring report generation — fires runs on a cadence and delivers output to configured recipients.
published: true
date: 2026-05-19T23:55:00.000Z
tags: reporting-audit, schedule, automation, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Report Schedule

> **At a Glance**
> **Owner:** Sysadmin / schedule-admin &nbsp;·&nbsp; **Table:** `tb_report_schedule` &nbsp;·&nbsp; **Retention:** indefinite (soft-delete only); artefacts age out via [reporting-audit/history](/en/inventory/reporting-audit/history) &nbsp;·&nbsp; **Used by:** `micro-cronjobs` poller &nbsp;·&nbsp; **Pairs a report template with a cron expression, frozen filters, and a delivery list.**

![Report Schedule screen](/screenshots/reporting-audit/schedule.png)

## 1. What & Who

Report Schedule defines **when a report runs and where the output goes**. Each row binds a report template to a cron expression, a frozen filter set, and a recipient list. The cron service polls active schedules, locks the fire slot in Redis, and enqueues a [reporting-audit/history](/en/inventory/reporting-audit/history) job that `micro-report` executes. The history row is the artefact of record; the schedule row is the definition.

**Audience:** **Sysadmin** (create / edit / disable), **Operations** (recipient changes, cron tuning), **Auditor** (verify daily exports still fire).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Pause a schedule | Reports → Schedules → row → **Active toggle off** | Sets `is_active = false`; row preserved, polling suspended |
| Change cron expression | Detail screen → **Cron builder** | Recomputes `next_run_at` from now |
| Update recipients | Detail screen → **Recipients picker** | Typed entries: `email` / `user` / `sftp` |
| Test a schedule without waiting | Detail screen → **Test Run** | Enqueues a one-off job with same parameters |
| See last fire result | List → **Last status** column | Mirrors latest [reporting-audit/history](/en/inventory/reporting-audit/history) row |
| See next fire time | List → **Next-run countdown** | Live from `next_run_at` |
| Delete a schedule | Detail screen → **Delete** | Soft-delete via `deleted_at`; scheduler ignores |
| Have two cadences off one template | Create a second schedule with same `report_type` | No uniqueness on `(report_type, cron_expression)` — intentional |

## 3. Common Questions

| Symptom / Question | Cause / Answer | Action |
|---|---|---|
| Schedule isn't firing | `is_active = false`, `deleted_at` set, or cron expression wrong | Toggle active + verify cron in the builder |
| Two scheduler replicas — will it fire twice? | No — Redis lock on `(schedule_id, fire_timestamp)` guarantees exactly-one enqueue | — |
| What happens if we were down for a missed slot? | `schedule_config.misfire_policy`: `fire_once` (default), `skip`, or `fire_all` | Long-stopped tenants should use `skip` |
| Which timezone does cron run in? | `schedule_config.timezone` (typically `Asia/Bangkok`); falls back to UTC if absent | Set on creation |
| Where does the output land? | History row's `file_url` + delivered to each entry in `recipients` | See [reporting-audit/history](/en/inventory/reporting-audit/history) |
| Why was a recipient skipped? | Unknown `type` in the recipient object | Warning written to job row's `error_message` |
| Who can create schedules? | Schedule-admin permission (Sysadmin holds implicitly) | Grant via [access-control/permission](/en/inventory/access-control/permission) |

## 4. Edge Cases

- **Idempotency.** Redis lock per `(schedule_id, fire_timestamp)`; second racing scheduler is a no-op. Enqueued job carries `options.schedule_id` and `options.scheduled_fire_at` for traceability.
- **Soft-delete semantics.** Scheduler poll filters `is_active = true AND deleted_at IS NULL AND next_run_at <= now()`. Soft-deleted rows ignored forever.
- **Reactivation** recomputes `next_run_at` from cron against the current time — does **not** back-fill missed slots.
- **Time-zone.** Cron evaluated against `schedule_config.timezone`. `last_run_at` / `next_run_at` stored UTC.
- **RBAC on reading.** Read access requires the report category's read permission; edit / toggle requires schedule-admin.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 5.1 `tb_report_schedule`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar(255)` | No | Display name. |
| `report_type` | `String @db.VarChar(100)` | No | Logical report identifier (resolves a `tb_report_template`). |
| `report_template_id` | `String? @db.Uuid` | Yes | Optional explicit binding; otherwise resolved by `report_type`. |
| `format` | `enum_report_format` | No | `pdf` / `excel` / `csv` / `json`. |
| `cron_expression` | `String @db.VarChar(100)` | No | Standard 5- or 6-field cron. |
| `schedule_config` | `Json? @db.JsonB` | Yes | `{ timezone, jitter_seconds, misfire_policy }`. |
| `filters` | `Json? @db.JsonB` | Yes | Default `{}`. Filter set applied each run. |
| `options` | `Json? @db.JsonB` | Yes | Default `{}`. Render options. |
| `recipients` | `Json? @db.JsonB` | Yes | Default `[]`. Typed delivery targets. |
| `is_active` | `Boolean` | No | Default `true`. Disable without deleting. |
| `last_run_at`, `next_run_at` | `DateTime? @db.Timestamptz(6)` | Yes | Health-check columns. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** index on `is_active` (`idx_report_schedule_active`). No uniqueness on `(report_type, cron_expression)` — multiple schedules per template are intentional.

## 6. Business Rules

- **Cron format.** Standard `minute hour day-of-month month day-of-week`. Examples: `0 6 * * *` (daily 06:00), `0 7 * * 1` (Mon 07:00), `0 0 1 * *` (1st of month).
- **Idempotency.** Redis lock on `(schedule_id, fire_timestamp)` guarantees exactly-one enqueue across replicas.
- **Missed-fire policy.** `fire_once` (default — fire on next poll), `skip` (drop and advance), or `fire_all` (catch up every missed slot).
- **Active flag.** `is_active = false` suspends polling without deletion; toggling on recomputes `next_run_at` from now.
- **Recipient resolution.** Typed objects — `{type:"email",value:...}`, `{type:"user",value:<uuid>}`, `{type:"sftp",value:<config_id>}`. Unknown types skipped with warning.
- **RBAC on creation.** Only schedule-admin grant (Sysadmin implicit) can create / edit.
- **Retention.** Schedule rows retained indefinitely (soft-delete only); artefacts age out per [reporting-audit/history](/en/inventory/reporting-audit/history) retention.

## 7. Cross-References

- [reporting-audit/report](/en/inventory/reporting-audit/report) — parent module. `report_type` / `report_template_id` resolve `tb_report_template`.
- [reporting-audit/history](/en/inventory/reporting-audit/history) — every fire writes one `tb_report_job` row; `last_run_at` mirrors it.
- [reporting-audit/notification](/en/inventory/reporting-audit/notification) — `user`-type recipients receive in-app notification; `email` receives the artefact via platform mailer.
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — create / update / delete / enable / disable logged with `entity_type = 'report_schedule'`.
- [access-control/user](/en/inventory/access-control/user), [access-control/permission](/en/inventory/access-control/permission) — owner + schedule-admin grants.

## 8. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_schedule` (lines 5685-5709), `enum_report_format` (~5628-5633).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/report/schedules/`.
- **Cron microservice:** `../micro-cronjobs/internal/scheduler/scheduler.go` (poll + dispatch), `../micro-cronjobs/internal/scheduler/redis_locker.go` (idempotency), `../micro-cronjobs/internal/repository/cronjob_repo.go` (reads).
- **Reports microservice:** `../micro-report/` — consumes the enqueued job.
