---
title: Report
description: Report generation pipeline — tenant-side job and schedule rows backed by platform-side templates and document-type print mappings.
published: true
date: 2026-05-16T08:00:00.000Z
tags: reporting-audit, report, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Report

## 1. Purpose

The report entity is the full **report generation pipeline** — both ad-hoc on-demand exports and scheduled recurring exports, plus the print-layout machinery that backs every "Print" button across the application. Four tables collaborate across both schemas:

- `tb_report_template` (platform) is the **template catalogue** — one row per defined report or print layout. It carries the layout definition (`dialog`, `content`), the data binding (`source_type` + `source_name` + `source_params`), an optional `builder_key` for Go-side registered definitions, page orientation, and signature block configuration. The `kind` column (`report` or `print`) splits user-facing analytical reports from printable document layouts.
- `tb_print_template_mapping` (platform) maps a **document type** (`PO`, `PR`, `SR`, `GRN`, `CN`, `IA`, …) to one or more `tb_report_template` rows. Exactly one mapping per document type should have `is_default = true` for the default "Print" button; others appear under "Print as…".
- `tb_report_job` (tenant) records every **execution** — queued / processing / completed / failed / cancelled — with filters, requested format, output file metadata, timing, and the requesting user. This is the audit + download surface.
- `tb_report_schedule` (tenant) defines **cron-driven recurring runs** — name, template, format, cron expression, filters, recipients, last/next-run timestamps. The scheduler enqueues `tb_report_job` rows from active schedules.

Mixing schemas reflects the actual deployment topology: templates and the document-type mapping are platform assets (curated centrally), while jobs and schedules are tenant data (each tenant owns its own execution history and schedule).

## 2. Prisma Model(s)

Source: **mixed** — `tb_report_job` and `tb_report_schedule` live in the tenant schema; `tb_report_template` and `tb_print_template_mapping` live in the platform schema.

### 2.1 `tb_report_job` (tenant)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `report_type` | `String @db.VarChar(100)` | No | Logical report identifier (matches a template). |
| `report_category` | `enum_report_category` | No | One of `inventory`, `procurement`, `recipe`, `vendor`, `financial`, `operational`. |
| `format` | `enum_report_format` | No | Output format: `pdf`, `excel`, `csv`, `json`. |
| `status` | `enum_report_job_status` | No | Default `queued`. One of `queued`, `processing`, `completed`, `failed`, `cancelled`. |
| `filters` | `Json? @db.JsonB` | Yes | Default `{}`. Concrete filter values for this run. |
| `options` | `Json? @db.JsonB` | Yes | Default `{}`. Render options. |
| `file_url` | `String?` | Yes | Resolved URL to the produced artefact. |
| `file_name` | `String? @db.VarChar(255)` | Yes | Output filename. |
| `file_size` | `BigInt?` | Yes | Size in bytes. |
| `row_count` | `Int?` | Yes | Rows in the result set. |
| `error_message` | `String?` | Yes | Populated when `status = failed`. |
| `started_at` | `DateTime? @db.Timestamptz(6)` | Yes | Execution start timestamp. |
| `completed_at` | `DateTime? @db.Timestamptz(6)` | Yes | Execution end timestamp. |
| `expires_at` | `DateTime? @db.Timestamptz(6)` | Yes | When the output is reaped. |
| `duration_ms` | `Int?` | Yes | Cached execution duration. |
| `requested_by_id` | `String @db.Uuid` | No | Requesting user. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** indexes on `status` (`idx_report_job_status`), `report_type` (`idx_report_job_type`), `requested_by_id` (`idx_report_job_requested`), and `created_at DESC` (`idx_report_job_created`) for "my recent jobs" queries.

### 2.2 `tb_report_schedule` (tenant)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar(255)` | No | Display name for the schedule. |
| `report_type` | `String @db.VarChar(100)` | No | Logical report identifier. |
| `report_template_id` | `String? @db.Uuid` | Yes | Optional explicit template binding (otherwise resolved by `report_type`). |
| `format` | `enum_report_format` | No | Output format. |
| `cron_expression` | `String @db.VarChar(100)` | No | Standard cron expression. |
| `schedule_config` | `Json? @db.JsonB` | Yes | Additional scheduler options (timezone, jitter). |
| `filters` | `Json? @db.JsonB` | Yes | Default `{}`. Filters applied on every run. |
| `options` | `Json? @db.JsonB` | Yes | Default `{}`. Render options. |
| `recipients` | `Json? @db.JsonB` | Yes | Default `[]`. Email / user IDs to notify on completion. |
| `is_active` | `Boolean` | No | Default `true`. Disable a schedule without deleting it. |
| `last_run_at` | `DateTime? @db.Timestamptz(6)` | Yes | Most recent execution timestamp. |
| `next_run_at` | `DateTime? @db.Timestamptz(6)` | Yes | Next planned execution timestamp. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** index on `is_active` (`idx_report_schedule_active`) for the scheduler poll.

### 2.3 `tb_report_template` (platform)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar(255)` | No | Display name. |
| `description` | `String?` | Yes | Free text. |
| `report_group` | `String @db.VarChar(100)` | No | Logical grouping (used for menu + filtering). |
| `kind` | `String @db.VarChar(20)` | No | Default `report`. Either `report` (user-facing analytical) or `print` (document layout). |
| `dialog` | `String @db.Text` | No | Filter-dialog definition. |
| `content` | `String @db.Text` | No | Layout body. |
| `builder_key` | `String? @db.VarChar` | Yes | Links to a Go-side `report.Definition` registry key when set. |
| `view_name` | `String? @db.VarChar` | Yes | Legacy. Prefer `source_type` + `source_name`. |
| `source_type` | `String @db.VarChar(20)` | No | Default `view`. One of `view`, `function`, `procedure`. |
| `source_name` | `String? @db.VarChar` | Yes | Bare identifier (no schema prefix). |
| `source_params` | `Json @db.JsonB` | No | Default `{"params":[]}`. Positional argument mapping. |
| `orientation` | `String @db.VarChar(20)` | No | Default `portrait`. Either `portrait` or `landscape`. |
| `signature_config` | `Json @db.JsonB` | No | Default `{"blocks":[]}`. Labelled signature blocks for print layouts. |
| `is_standard` | `Boolean` | No | Default `true`. `true` for system-managed templates. |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | BU allow-list (NULL = all BUs). |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | BU deny-list. |
| `is_active` | `Boolean` | No | Default `true`. Soft-disable without deleting. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `report_template_name_deleted_at_u`. Index on `report_group` (`idx_report_template_report_group`).

### 2.4 `tb_print_template_mapping` (platform)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `document_type` | `String @db.VarChar(50)` | No | Module document code (`PO`, `PR`, `SR`, `GRN`, `CN`, `IA`, …). |
| `report_template_id` | `String @db.Uuid` | No | FK to `tb_report_template.id`. |
| `is_default` | `Boolean` | No | Default `true`. The default-print template for this document type. |
| `display_label` | `String? @db.VarChar(255)` | Yes | Label shown in "Print as…" menu. |
| `display_order` | `Int` | No | Default `0`. Order in the "Print as…" menu. |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | BU allow-list. |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | BU deny-list. |
| `is_active` | `Boolean` | No | Default `true`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** indexes on `document_type` (`idx_print_template_mapping_document_type`) and `report_template_id` (`idx_print_template_mapping_template_id`). No uniqueness on `(document_type, is_default)` — application enforces "exactly one default per document type".

## 3. Usage / Cross-References

- **Dashboards and exports** — every report on a dashboard widget or run from the report list fans out as a `tb_report_job` row. Outputs are downloaded by the requesting user and (optionally) emailed to `recipients`.
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]] — each module's "Print" button resolves a `tb_print_template_mapping` row by `document_type`, picks the active `tb_report_template`, runs it with the document id as a filter, and produces a PDF.
- [[inventory]], [[costing]], [[product]], [[recipe]] — common consumers of analytical (`kind = report`) templates grouped by `report_group`.
- [[access-control/user]] — `requested_by_id` and recipients resolve through this entity.
- [[master-data/business-unit]] — `allow_business_unit` / `deny_business_unit` on both templates and mappings scope which BUs see / use the template.
- [[reporting-audit/widget]] — dashboard widgets can be wired to run a report and embed its result.
- [[reporting-audit/notification]] — schedule completion may dispatch a notification to recipients.
- [[reporting-audit/activity]] — `export` / `print` actions are logged.

## 4. Configuration UI

- **Templates** (`tb_report_template`) are managed by **Sysadmin** or Platform Admin under Platform Configuration → Report Templates. The screen exposes the SQL source binding (`source_type` + `source_name`), the layout (`dialog`, `content`), orientation, signature blocks, BU scoping, and the active / standard flags.
- **Print mappings** (`tb_print_template_mapping`) are managed alongside templates — typically Platform Admin only. Toggle `is_default` to switch the document-type default; add additional mappings to populate the "Print as…" menu.
- **Schedules** (`tb_report_schedule`) are managed by **Sysadmin** or operations users under tenant-side Reports → Schedules. Adding a schedule writes the cron, recipients, and filters.
- **Jobs** (`tb_report_job`) are surfaced as a read-only history under Reports → Jobs, with download links and re-run buttons.

## 5. Business Rules

- **One default print template per document type.** Application code enforces that exactly one `tb_print_template_mapping` row per `document_type` has `is_default = true`. Editing flips the existing default off in the same transaction.
- **BU scoping.** `allow_business_unit` and `deny_business_unit` apply on both templates and mappings. The effective rule is *allow if BU in allow-list AND BU not in deny-list*; an empty allow-list means "allow all BUs".
- **Template kind.** `kind = report` powers the analytical reports listed in the Reports menu. `kind = print` is reserved for the print pipeline and is hidden from the reports menu.
- **Source binding integrity.** `source_type` must match the database object's nature — a `view` source must be a SQL view in the tenant schema; `function` and `procedure` sources must accept the positional arguments declared in `source_params`. Drift here is the single largest source of failed jobs.
- **Job lifecycle.** `status` transitions are `queued → processing → (completed | failed | cancelled)`. The executor sets `started_at` on entering `processing` and `completed_at` plus `duration_ms` on terminal states.
- **Output retention.** `expires_at` is the contract for the storage reaper; outputs whose row has passed `expires_at` are removed from blob storage and `file_url` becomes invalid.
- **Schedule activation.** `is_active = false` keeps the row but stops the scheduler from enqueueing jobs. Reactivating recomputes `next_run_at` based on the cron expression and current time.
- **Standard vs user-defined templates.** `is_standard = true` marks system templates; UIs typically prevent deletion and warn before edit. User-defined (`is_standard = false`) templates may be deleted freely.

## 6. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (lines ~5652-5683), `tb_report_schedule` (lines ~5685-5709), `enum_report_format` (lines ~5628-5633), `enum_report_category` (lines ~5635-5642), `enum_report_job_status` (lines ~5644-5650).
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_report_template` (lines ~589-656), `tb_print_template_mapping` (lines ~663-688).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/reporting/` for the tenant-side reports + jobs + schedules screens; template + print-mapping admin under the platform / admin app.
- **Cross-module:** see Section 3.
