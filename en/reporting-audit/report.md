---
title: Report
description: Report generation pipeline — tenant-side job and schedule rows backed by platform-side templates and document-type print mappings.
published: true
date: 2026-05-17T07:00:16.000Z
tags: reporting-audit, report, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Report

> **At a Glance**
> **Owner:** Sysadmin (schedules) + Platform Admin (templates, mappings) &nbsp;·&nbsp; **Table:** `tb_report_job` + `tb_report_schedule` (tenant), `tb_report_template` + `tb_print_template_mapping` (platform) &nbsp;·&nbsp; **Used by:** every "Print" button + dashboard / scheduled exports &nbsp;·&nbsp; Full report and print-layout pipeline.

![Report screen](/assets/screenshots/reporting-audit/report.png)

## 1. What & Who

The report entity is the full **report generation pipeline** — ad-hoc on-demand exports + scheduled recurring exports + the print layout behind every "Print" button. Four tables across two schemas:

- `tb_report_template` (platform) — template catalogue (analytical `report` or `print` layout); holds layout (`dialog`, `content`), data binding (`source_type` + `source_name` + `source_params`), orientation, signatures.
- `tb_print_template_mapping` (platform) — maps `document_type` (`PO`, `PR`, `SR`, `GRN`, `CN`, `IA`, …) to one or more templates; exactly one `is_default = true` per type.
- `tb_report_job` (tenant) — execution history (queued / processing / completed / failed / cancelled); filters, format, output metadata.
- `tb_report_schedule` (tenant) — cron-driven recurring runs; enqueues jobs.

Mixed schemas reflect deployment: templates + mappings are curated centrally; jobs + schedules are tenant data.

**Maintained by** Platform Admin (templates, mappings), Sysadmin (schedules). **Read by** the report list, "Print as…" menu, dashboard widgets.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Run a report on demand | Reports menu → pick report → Run | Inserts a `tb_report_job` row |
| Download a finished job | Reports → Jobs → click filename | Resolves `file_url`; respects `expires_at` |
| Schedule a recurring export | Reports → Schedules → New | Cron expression + filters + recipients |
| Add a print layout for a document type | Platform Admin → Print Templates | Toggle `is_default` to switch default |
| BU-scope a template | Edit template `allow_business_unit` / `deny_business_unit` | Null allow-list = all BUs |
| Re-run a failed job | Reports → Jobs → Re-run | Creates new `tb_report_job` |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Job stuck `queued` | Executor not picking up | Check executor health and `idx_report_job_status` |
| Job fails with "view not found" | `source_type` / `source_name` drift | Realign template binding with DB object |
| Multiple defaults per document type | App invariant violated | Repair: keep one `is_default = true`; others false |
| Download 404 | Output reaped per `expires_at` | Re-run the job |
| Template not visible in BU | `allow_business_unit` excludes; or `deny_business_unit` includes | Edit BU scoping |

## 4. Edge Cases

- **Source binding drift** is the single largest cause of failed jobs — keep `source_type` / `source_name` aligned with the actual DB object.
- **Standard vs user-defined templates.** `is_standard = true` UIs typically prevent deletion and warn on edit.
- **Job lifecycle.** `queued → processing → (completed | failed | cancelled)`. Executor sets `started_at` / `completed_at` / `duration_ms`.
- **Output retention.** `expires_at` is the storage reaper contract.

---

## 5. Data Model (Dev)

Source: **mixed** — tenant for jobs/schedules, platform for templates/mappings.

### 5.1 `tb_report_job` (tenant)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `report_type` | `String @db.VarChar(100)` | No | Logical report identifier. |
| `report_category` | `enum_report_category` | No | `inventory`, `procurement`, `recipe`, `vendor`, `financial`, `operational`. |
| `format` | `enum_report_format` | No | `pdf`, `excel`, `csv`, `json`. |
| `status` | `enum_report_job_status` | No | Default `queued`. |
| `filters` / `options` | `Json? @db.JsonB` | Yes | Defaults `{}`. |
| `file_url` / `file_name` / `file_size` / `row_count` | — | Yes | Output metadata. |
| `error_message` | `String?` | Yes | Populated on `failed`. |
| `started_at` / `completed_at` / `expires_at` | `DateTime?` | Yes | Timing. |
| `duration_ms` | `Int?` | Yes | Cached duration. |
| `requested_by_id` | `String @db.Uuid` | No | Requesting user. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Indexes:** `status`, `report_type`, `requested_by_id`, `created_at DESC`.

### 5.2 `tb_report_schedule` (tenant)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` / `name` | `String` | No | Keys. |
| `report_type` / `report_template_id` | `String` | Mixed | Logical id + optional template binding. |
| `format` | `enum_report_format` | No | Output format. |
| `cron_expression` | `String @db.VarChar(100)` | No | Standard cron. |
| `schedule_config` / `filters` / `options` / `recipients` | `Json?` | Yes | Scheduler + run options + email/user IDs. |
| `is_active` | `Boolean` | No | Default `true`. |
| `last_run_at` / `next_run_at` | `DateTime?` | Yes | Scheduler bookkeeping. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 5.3 `tb_report_template` (platform)

Carries `name`, `description`, `report_group`, `kind` (`report` / `print`), `dialog`, `content`, optional `builder_key`, `source_type` (`view` / `function` / `procedure`), `source_name`, `source_params`, `orientation`, `signature_config`, `is_standard`, `allow_business_unit` / `deny_business_unit`, `is_active`. `@@unique([name, deleted_at])`.

### 5.4 `tb_print_template_mapping` (platform)

`document_type` → `report_template_id`; `is_default`, `display_label`, `display_order`, BU allow/deny lists, `is_active`. No DB uniqueness on `(document_type, is_default)` — app enforces single default.

## 6. Business Rules

- **One default print template per document type.** App-enforced; editing flips existing default off in the same transaction.
- **BU scoping.** Effective rule: *allow if in allow-list AND not in deny-list*; empty allow-list = all BUs.
- **Template kind.** `report` for analytical menu; `print` for the print pipeline (hidden from reports menu).
- **Source binding integrity.** `source_type` must match the DB object's nature; positional args declared in `source_params`.
- **Job lifecycle.** `queued → processing → (completed | failed | cancelled)`.
- **Output retention.** `expires_at` governs reaper.
- **Standard templates** UIs typically prevent deletion.

## 7. Cross-References

- All transactional modules — every "Print" button resolves through `tb_print_template_mapping`.
- [[reporting-audit/widget]] — widget tiles can embed reports.
- [[reporting-audit/notification]] — schedule completion may dispatch notifications.
- [[reporting-audit/activity]] — `export` / `print` actions logged.
- [[access-control/user]] — `requested_by_id` + recipients.
- [[master-data/business-unit]] — BU scoping.

## 8. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (lines ~5652-5683), `tb_report_schedule` (lines ~5685-5709).
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_report_template` (lines ~589-656), `tb_print_template_mapping` (lines ~663-688).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/reporting/` (tenant reports/jobs/schedules); template admin in platform app.
- **Microservice:** `../micro-report/` — report execution worker.

