---
title: Report
description: Report generation pipeline — a report-template catalogue and print-type mapping (platform), on-demand viewer rendering, and a job/history table that is real but currently orphaned (nothing writes to it through any reachable UI path).
published: true
date: 2026-07-22T03:05:28.000Z
tags: reporting-audit, report, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Report

> **At a Glance**
> **Owner:** Platform Admin (templates, mappings) &nbsp;·&nbsp; **Table:** `tb_report_job` (tenant — real but currently orphaned) — schedules are **not** in `tb_report_schedule` (dead, see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule)), `tb_report_template` + `tb_print_template_mapping` (platform, real) &nbsp;·&nbsp; **Used by:** the report list ("Run"), every "Print" button, and scheduled fires — all three render via a viewer-URL endpoint, none of the three write a job row.

## Implementation status (verified 2026-07-22)

The on-demand "Run" flow on the report list (`report-component.tsx` → `useRunReportMutation` → `POST .../reports/viewer`) and every module's "Print" button (`lib/print-document.ts`) both resolve straight to a rendered viewer URL — neither calls the async job endpoint (`generate-async`), so neither writes a `tb_report_job` row. A repo-wide frontend search found zero callers of `generate-async`/`job-status` anywhere. See [reporting-audit/history](/en/inventory/reporting-audit/history) for the full finding and its consequences for the history screen, and [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) for the confirmed-dead `tb_report_schedule` table (the real schedule store is a generic `Cronjob` table in the separate micro-cronjobs service).

## 1. What & Who

The report entity is the **report generation pipeline** — ad-hoc on-demand rendering, the print layout behind every "Print" button, and (structurally, though not currently populated) scheduled recurring exports. Three tables are relevant, spanning two schemas plus a third external scheduler database:

- `tb_report_template` (platform) — template catalogue (analytical `report` or `print` layout); holds layout (`dialog`, `content`), data binding (`source_type` + `source_name` + `source_params`), orientation, signatures. Read-only from `carmen-inventory-frontend-react`'s report list — no template-authoring UI was found in this repo (template `POST`/`PUT`/`DELETE` exist on the backend but are exposed under a `platform/` gateway module, outside this repo's scope).
- `tb_print_template_mapping` (platform) — maps `document_type` (`PO`, `PR`, `SR`, `GRN`, `CN`, `IA`, …) to one or more templates; exactly one `is_default = true` per type. Real and actively resolved by every "Print" button via `GET .../report/print-template?document_type=`.
- `tb_report_job` (tenant) — job/history table. Real and correctly wired to `/report/history`, but confirmed to receive zero writes from any currently-reachable UI path — see Implementation status above.

Report **schedules** are not a fourth tenant table here — see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) for the corrected model (a generic `Cronjob` row in the separate micro-cronjobs service).

**Maintained by** Platform Admin (templates, mappings) — schedules are not a Sysadmin-gated concern here; see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) (any authenticated user with BU context, no schedule-admin gate found). **Read by** the report list, "Print as…" menu, dashboard widgets.

### 1.1 Dataset vs render — the micro-data split

Report generation is split across two Go services, with the **`Dataset`** object (columns + rows + totals + summary) as the boundary contract:

| Concern | Columns on `tb_report_template` | Owner | Does |
|---|---|---|---|
| **Dataset** | `source_type`, `source_name`, `source_params`, `dialog`, `view_name`, `builder_key` | **micro-data** | Resolves the view / function / procedure, composes the WHERE clause from filters, fans out across tenant BUs, returns `Dataset`. Renders nothing. |
| **Report** | `content`, `kind`, `report_group`, format / orientation / signatures | **micro-report** | Owns output format (PDF / Excel / CSV / JSON), template layout, `kind`, print mappings, and job tracking. |

micro-report no longer runs the query in-process — it calls micro-data's `POST /api/datasets/execute` (passing the source's `builder_key` or `name`, `bu_codes`, and `filters`) and renders the returned `Dataset`. The `tb_report_template` row still physically holds both column sets; micro-data reads only the dataset columns (mapped onto `model.DatasetSource`). Extracting them into a `tb_dataset_source` table is a noted future migration, not yet in effect.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Run a report on demand | Report list → pick report → Run | `POST .../reports/viewer` — renders a viewer URL directly; **no `tb_report_job` row written** |
| Print a document | Any document's Print action | Resolves `tb_print_template_mapping`, then the same viewer endpoint — same "no job row" behavior |
| Filter the report list | Search box + report-group filter | Server-side search; group filter is client-side over the current page |
| Add a print layout for a document type | Platform Admin (outside this repo's UI — see below) | Toggle `is_default` to switch default; real backend endpoint, no editing screen found in `carmen-inventory-frontend-react` |
| BU-scope a template | Edit template `allow_business_unit` / `deny_business_unit` | Null allow-list = all BUs |
| Schedule a recurring export | See [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) | Not stored in this module's tenant tables — real backing is a separate scheduler service |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| History screen shows nothing for a run I just did | Expected — see Implementation status above; no reachable path writes `tb_report_job` | Not a bug in the read path |
| Job fails with "view not found" (when the async path *is* exercised) | `source_type` / `source_name` drift | Realign template binding with DB object |
| Multiple defaults per document type | App invariant violated | Repair: keep one `is_default = true`; others false |
| Template not visible in BU | `allow_business_unit` excludes; or `deny_business_unit` includes | Edit BU scoping |

## 4. Edge Cases

- **On-demand runs and Print are synchronous viewer renders, not queued jobs.** No `tb_report_job` row, no history entry, no `expires_at` retention applies to them.
- **Source binding drift** is the largest plausible cause of failure on the viewer path (a `source_type`/`source_name` mismatch) — keep template binding aligned with the actual DB object.
- **Standard vs user-defined templates.** `is_standard = true` templates are handled specially by the backend `delete`/`update` handlers (unconfirmed exact UI behavior in this pass — no template-editing screen exists in `carmen-inventory-frontend-react`).
- **Async job lifecycle exists but is unreached.** `queued → processing → (completed | failed | cancelled)` remains the model's contract; the executor only advances it via `generate-async`, which nothing in the current frontend calls.

---

## 5. Data Model (Dev)

Source: **mixed** — tenant for the job/history table, platform for templates/mappings. Schedules are **not** a tenant table here — see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) §5 for the real `Cronjob` model in the separate micro-cronjobs service.

### 5.1 `tb_report_job` (tenant — real, currently orphaned; see [reporting-audit/history](/en/inventory/reporting-audit/history))

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

### 5.2 Schedules — not a tenant table (corrected)

The tenant schema does declare a `tb_report_schedule` model, but a repo-wide code search found **zero references to it anywhere** outside its own Prisma declaration — it is dead, the same pattern confirmed for `tb_attachment` and the old `tb_widget_*` family. The real schedule store is a generic `Cronjob` table (`job_type = "report"` rows) in the separate micro-cronjobs service's own Postgres schema. See [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) §5 for the full corrected model.

### 5.3 `tb_report_template` (platform)

Carries `name`, `description`, `report_group`, `kind` (`report` / `print`), `dialog`, `content`, optional `builder_key`, `source_type` (`view` / `function` / `procedure`), `source_name`, `source_params`, `orientation`, `signature_config`, `is_standard`, `allow_business_unit` / `deny_business_unit`, `is_active`. `@@unique([name, deleted_at])`.

> **Service ownership note:** the dataset columns (`source_type`, `source_name`, `source_params`, `dialog`, `view_name`, `builder_key`) are read by **micro-data** (mapped onto `model.DatasetSource`); the remaining columns are read by **micro-report**. See [§1.1](#) for the split rationale.

### 5.4 `tb_print_template_mapping` (platform)

`document_type` → `report_template_id`; `is_default`, `display_label`, `display_order`, BU allow/deny lists, `is_active`. No DB uniqueness on `(document_type, is_default)` — app enforces single default.

## 6. Business Rules

- **One default print template per document type.** App-enforced; editing flips existing default off in the same transaction.
- **BU scoping.** Effective rule: *allow if in allow-list AND not in deny-list*; empty allow-list = all BUs.
- **Template kind.** `report` for the analytical report list; `print` for the print pipeline.
- **Source binding integrity.** `source_type` must match the DB object's nature; positional args declared in `source_params`.
- **On-demand runs and Print never queue a job.** Both call the synchronous viewer endpoint — `tb_report_job`'s `queued → processing → (completed | failed | cancelled)` lifecycle is real but currently unreached by any frontend code path.
- **Standard templates** — backend has distinct handling for `is_standard = true` (per the Go handler code); no editing UI to observe the resulting behavior in this repo.

## 7. Cross-References

- All transactional modules — every "Print" button resolves through `tb_print_template_mapping`, then renders via the viewer endpoint (no job row).
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — dashboard widget tiles pull from the [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) catalog, a separate mechanism from this report-template catalogue.
- [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) — recurring fires; not backed by a tenant table in this module.
- [reporting-audit/history](/en/inventory/reporting-audit/history) — the `tb_report_job` read screen; confirmed structurally orphaned.
- [reporting-audit/notification](/en/inventory/reporting-audit/notification) — schedule fires dispatch a viewer-link notification per recipient.
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — `export` / `print` actions logged (unconfirmed against the viewer path specifically in this pass).
- [access-control/user](/en/inventory/access-control/user) — `requested_by_id` + recipients.
- [master-data/business-unit](/en/inventory/master-data/business-unit) — BU scoping.

## 8. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job` (line ~6094), `enum_report_job_status` (line ~6086), `enum_report_format` (line ~6070), `enum_report_category` (line ~6077).
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_report_template` (line ~731), `tb_print_template_mapping` (line ~806).
- **Frontend:** `../carmen-inventory-frontend-react/routes/report/` (`list/`, `schedules/`, `history/`); `lib/print-document.ts` (Print integration used by every transactional module).
- **Microservice:** `../micro-report/` — `controller/report_controller.go` (`viewReport`, `generateAsync`, `history`), `controller/template_controller.go`, `controller/print_template_mapping_controller.go`.

