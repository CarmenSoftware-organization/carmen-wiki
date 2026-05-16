---
title: Report History
description: Archive of every executed report run — date, parameters, status, link to the generated file or rendered output.
published: true
date: 2026-05-16T17:00:00.000Z
tags: reporting-audit, history, archive, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Report History

## 1. Purpose

Report History is the **append-only execution log** for every report run on the tenant — manual ad-hoc exports kicked off from the Reports menu, "Print" invocations resolved from a print-template mapping, and scheduled runs enqueued by [[reporting-audit/schedule]]. Each row records the report identifier, the concrete filter set used, the format requested, the executing user (or schedule), the lifecycle state, and a pointer to the produced artefact in blob storage. It answers the audit questions *"which numbers were exported on which date, by whom, against which filter set, and is the output file still retrievable?"* and *"why did this scheduled run fail?"*.

It is also the source of the **download surface** on the Reports → History screen: the row carries `file_url`, `file_name`, `file_size`, and `expires_at`, so the frontend renders a working download link until the storage reaper enforces retention.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_report_job`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `report_type` | `String @db.VarChar(100)` | No | Logical identifier matching the template. |
| `report_category` | `enum_report_category` | No | One of `inventory`, `procurement`, `recipe`, `vendor`, `financial`, `operational`. |
| `format` | `enum_report_format` | No | Output format: `pdf`, `excel`, `csv`, `json`. |
| `status` | `enum_report_job_status` | No | Default `queued`. One of `queued`, `processing`, `completed`, `failed`, `cancelled`. |
| `filters` | `Json? @db.JsonB` | Yes | Default `{}`. Concrete filter values for this run. |
| `options` | `Json? @db.JsonB` | Yes | Default `{}`. Render options (page size, locale, signature toggle). |
| `file_url` | `String?` | Yes | Resolved URL to the produced artefact. |
| `file_name` | `String? @db.VarChar(255)` | Yes | Output filename. |
| `file_size` | `BigInt?` | Yes | Size in bytes. |
| `row_count` | `Int?` | Yes | Rows in the result set. |
| `error_message` | `String?` | Yes | Populated when `status = failed`. |
| `started_at` | `DateTime? @db.Timestamptz(6)` | Yes | Execution start. |
| `completed_at` | `DateTime? @db.Timestamptz(6)` | Yes | Execution end. |
| `expires_at` | `DateTime? @db.Timestamptz(6)` | Yes | When the storage reaper removes the artefact. |
| `duration_ms` | `Int?` | Yes | Cached execution duration. |
| `requested_by_id` | `String @db.Uuid` | No | Requesting user (or the schedule's `created_by_id` for scheduled runs). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** indexes on `status` (`idx_report_job_status`), `report_type` (`idx_report_job_type`), `requested_by_id` (`idx_report_job_requested`), and `created_at DESC` (`idx_report_job_created`) — the last is the dominant access pattern for "my recent jobs" and the global history list. No FK to `tb_report_schedule`; the link is logical, established via matching `report_type` + correlation id stuffed into `options`.

## 3. Usage / Cross-References

- [[reporting-audit/report]] — parent module that defines templates and the job lifecycle. Every `kind = report` template that fires produces a row here.
- [[reporting-audit/schedule]] — recurring runs enqueue jobs here; the schedule's `last_run_at` is computed from the most recent completed job for that schedule.
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]] — each "Print" click resolves a `kind = print` template and writes a job row here, so the print path is auditable too.
- [[reporting-audit/activity]] — `export` and `print` actions are also logged in `tb_activity` with `entity_type = 'report_job'` and `entity_id = tb_report_job.id`. Activity stays as the user-action trail; history stays as the artefact catalogue.
- [[access-control/user]] — `requested_by_id` resolves through platform `tb_user`.

## 4. Configuration UI

History is **read-only**. There is no create / edit screen — rows are written by the report executor service (`micro-report`) and amended only by the same service to mark terminal states.

- **Reports → History** (`/report/history`): Auditor, Finance, and any user with the corresponding report read permission see their own rows; Sysadmin sees all rows across the tenant. Filters: status, report type, date range, requester. Each row exposes Download (if `file_url` resolvable), Re-run (re-enqueue with the same filters), and View Details (full filter / options JSON, error message).
- **Document detail → Print History** drawer: where a print job was launched from a transactional document, the detail screen shows the recent jobs against that document so testers can confirm the right template fired.

## 5. Business Rules

- **Append-only.** The executor writes a row on enqueue and updates only `status`, `started_at`, `completed_at`, `duration_ms`, `row_count`, `error_message`, `file_*`, and the standard `updated_*` columns. No other application path mutates this table.
- **Lifecycle.** `queued → processing → (completed | failed | cancelled)`. `started_at` is set on entering `processing`; `completed_at` and `duration_ms` are set on every terminal state. `cancelled` is reachable from `queued` or `processing` via the cancel endpoint.
- **Output retention.** `expires_at` is the contract for the storage reaper. After the timestamp passes, the artefact behind `file_url` is deleted from blob storage; the row remains so the audit trail (who ran, what filters, what row count) survives the artefact. Default retention is tenant-policy driven; failed and cancelled jobs may use a shorter horizon since they have no artefact.
- **RBAC on reading.** A user can read a job row only if (a) they are the requester, (b) they hold the read permission for the corresponding report category, or (c) they hold Sysadmin / Auditor on the tenant. The frontend list query filters on these conditions; never trust the client.
- **Time-zone of timestamps.** All timestamp columns are `Timestamptz(6)` and stored in UTC; the frontend renders against the user's profile timezone. Schedule-driven jobs encode the schedule's intended fire time in `options.scheduled_fire_at` so timezone-of-record is unambiguous on review.
- **No PII leakage in error messages.** The executor scrubs error messages of credentials, tokens, and raw SQL values before persisting; only the bound parameter names survive.

## 6. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (lines 5652-5683), `enum_report_job_status` (lines 5644-5650), `enum_report_format` (lines ~5628-5633), `enum_report_category` (lines ~5635-5642).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/report/history/` — the History screen, with `_components/` for the table, filter bar, and download cell.
- **Reports microservice:** `../micro-report/controller/report_controller.go` and `../micro-report/db/report_job_repo.go` — the executor that owns writes to this table.
- **Cross-module:** see Section 3.
