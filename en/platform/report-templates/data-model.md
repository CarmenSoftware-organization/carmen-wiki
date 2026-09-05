---
title: Report Template — Data Model
description: tb_report_template entity, dialog/content XML payloads, source binding, BU scope, and the 2026-07-23 kind→template_type rename plus is_default/doc_version columns.
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, report-templates, data-model
editor: markdown
dateCreated: 2026-05-19T18:30:00.000Z
---

# Report Template — Data Model

> **At a Glance**
> **Tables:** `tb_report_template` (primary) &nbsp;·&nbsp; **Former sibling table:** `tb_print_template_mapping` — **dropped 2026-07-23**, its `is_default` role absorbed onto this table; see [Print Template Mapping](/en/platform/print-template-mapping) (historical) &nbsp;·&nbsp; **JSON payloads:** `dialog` (XML, non-nullable), `content` (XML, non-nullable), `source_params` (`{ params: [...] }`), `signature_config` (`{ blocks: [...] }`) &nbsp;·&nbsp; **Source binding:** `source_type` (plain String: `view` / `function` / `procedure`) + `source_name` + `source_params` &nbsp;·&nbsp; **BU scope:** `allow_business_unit` / `deny_business_unit` stored as `Json?`; serialised to CSV strings in the SPA form &nbsp;·&nbsp; **Lifecycle flags:** `is_standard`, `is_default` (form templates only, new 2026-07-23), `is_active`, `doc_version`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

`tb_report_template` is the catalogue entry for one printable or exportable document in the Carmen Platform. Each row encodes the complete definition of a report: its identity (`name`, `report_group`, `template_type`), two XML payload columns (`dialog` and `content`) consumed by the report runtime, the runtime source binding (`source_type`, `source_name`, `source_params`), print-layout fields (`orientation`, `signature_config`), a BU-scope allow/deny pair, and the standard lifecycle flags and audit trio (including `doc_version`, the platform-wide optimistic-lock column added 2026-06-12 — **corrected**, an earlier sync misdated this 2026-07-16).

Report templates are tenant-global — they are not cluster-scoped and carry no FK to `tb_cluster`. The BU-scope columns (`allow_business_unit`, `deny_business_unit`) are opt-in filtering lists that restrict which business units a template is visible to; they do not bind the row to any particular cluster. This distinguishes the report-templates surface from the [clusters](/en/platform/clusters) and [business-units](/en/platform/business-units) pages, which document the cluster/BU hierarchy. BU codes referenced in the chip lists correspond to `tb_business_unit.code` values, but there is no FK constraint — the reference is an application-layer convention.

The `template_type` column (renamed from `kind` by migration `20260723120000_print_form_default`, 2026-07-23) distinguishes the two uses of this table: `"list"` rows (was `"report"`) are user-facing tabular analytical reports; `"form"` rows (was `"print"`) are single-record document layouts. Until 2026-07-23, a separate `tb_print_template_mapping` table mapped document types (PO, GRN, SR, …) to a `kind="print"` row here; that table has been **dropped**. Its job — picking the one default template a business unit gets for a given group — is now done by this table's own `is_default` column, scoped to `report_group` and enforced by a partial unique index (§2.1). See [Print Template Mapping](/en/platform/print-template-mapping) for the removal timeline; this page covers `tb_report_template` only.

## 2. Entities

### 2.1 `tb_report_template`

One row per report or print template. The field table below follows the Prisma declaration order, grouped by purpose. The table has more than 15 fields, so bold separator rows are used to cluster related columns.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| **— Identity —** | | | | |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `name` | `String @db.VarChar(255)` | No | — | Human-readable template name; unique among live rows (with `deleted_at`) |
| `description` | `String?` | Yes | — | Optional free-text description of the template's purpose |
| `report_group` | `String @db.VarChar(100)` | No | — | Grouping key used to organise templates in the management list (e.g. `"Receiving"`, `"Inventory"`) |
| `template_type` | `String @default("list") @db.Text` | No | `"list"` | Template category: `"list"` (tabular analytical report, was `"report"`) or `"form"` (single-record document layout, was `"print"`). Renamed from `kind` by migration `20260723120000_print_form_default` (2026-07-23); values changed at the same time |
| **— XML Payloads —** | | | | |
| `dialog` | `String @db.Text` | No | — | XML string defining the parameter form rendered by the report runtime. Not nullable — an empty string `""` is the valid "no dialog" value. Detailed XML structure documented in [XML Spec §2](/en/platform/report-templates/xml-spec) |
| `content` | `String @db.Text` | No | — | XML string defining the report output layout rendered by the report runtime. Not nullable — `""` is valid for a new template. The Content tab in the editor also accepts `.frx` / `.xml` / `.txt` file uploads (legacy FastReport migration). Detailed structure in [XML Spec §3](/en/platform/report-templates/xml-spec) |
| **— Go Builder —** | | | | |
| `builder_key` | `String? @db.VarChar` | Yes | — | Links a template row to a Go report.Definition registry key. When set, the Go runtime uses this key to resolve the report definition rather than executing `source_type`/`source_name` directly |
| **— Source Binding (legacy) —** | | | | |
| `view_name` | `String? @db.VarChar` | Yes | — | Legacy column retained for backward compatibility. Prefer `source_type` + `source_name`. The Go registry falls back to `view_name` when `source_name` is empty. The SPA loads `source_name` as `template.source_name \|\| template.view_name` |
| **— Source Binding —** | | | | |
| `source_type` | `String @db.VarChar(20)` | No | `"view"` | Tells the report executor how to read the data. Plain String — not a Prisma enum; the SPA validates the values client-side. Valid values: `"view"`, `"function"`, `"procedure"` (see §4) |
| `source_name` | `String? @db.VarChar` | Yes | — | Bare identifier of the view, function, or procedure (no schema prefix; resolved against the tenant's `current_schema()`). Required when `source_type` is `"function"` or `"procedure"` — the SPA enforces this with a field-level validation error |
| `source_params` | `Json @db.JsonB` | No | `{"params":[]}` | Positional argument mapping for function/procedure invocations. Shape: `{ "params": [{ "filter": "DateFrom", "type": "date", "nullable": false }, ...] }`. Default is an empty params array; see §5.3 |
| **— Print Layout —** | | | | |
| `orientation` | `String @db.VarChar(20)` | No | `"portrait"` | Page orientation for print-style templates: `"portrait"` or `"landscape"`. Replaces the legacy `"Document Landscape"` name suffix convention |
| `signature_config` | `Json @db.JsonB` | No | `{"blocks":[]}` | Signature block definitions rendered on the print layout. Shape: `{ "blocks": [{ "key": "Sig1Name", "label": "Requestor", "required": true }, ...] }`. Replaces the previous behaviour of pulling `Sig1Name`…`Sig5Name` from active workflow stages |
| **— Lifecycle —** | | | | |
| `is_standard` | `Boolean` | No | `true` | Marks the template as a standard (system-provided) template. Standard templates are typically read-only for end operators |
| `is_default` | `Boolean` | No | `false` | **New 2026-07-23.** Meaningful only for `template_type = "form"`: the one live template per `report_group` used when a business unit hasn't chosen one. Enforced by the partial unique index below, not just application logic — this is the column that absorbed `tb_print_template_mapping.is_default` when that table was dropped |
| **— BU Scope —** | | | | |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | — | Optional list of BU codes that may see this template. `NULL` = visible to all BUs. The SPA reads this as an array (or scalar) and normalises it to a comma-separated string for the chip-input field via `toCsv()` |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | — | Optional list of BU codes explicitly excluded from seeing this template. `NULL` = no denials. Same `toCsv()` normalisation as `allow_business_unit` |
| `is_active` | `Boolean` | No | `true` | When `false`, the template is inactive and hidden from selection lists |
| **— Audit —** | | | | |
| `doc_version` | `Int @default(0) @db.Integer` | No | `0` | Optimistic-lock token, part of the platform-wide `doc_version` rollout (**2026-06-12**, migration `20260612000000_add_doc_version`, all 35 platform tables — corrects an earlier sync's "2026-07-16"). The SPA sends it on every `PUT` and shows a conflict toast + reload on a version mismatch |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: row creation time |
| `created_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the creator (application-layer convention; no Prisma `@relation` declared) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: last update time |
| `updated_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the last updater (application-layer convention; no Prisma `@relation` declared) |
| **— Soft-delete —** | | | | |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Soft-delete timestamp; `NULL` = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the deleter (application-layer convention; no Prisma `@relation` declared) |

**Constraints:**
- `@id` on `id`
- `@@unique([name, deleted_at])` — map `"report_template_name_deleted_at_u"` — template names are unique among live rows; allows name reuse after soft delete
- **New 2026-07-23:** a partial unique index `idx_report_template_default_per_group` on `(report_group)` `WHERE is_default AND template_type = 'form' AND deleted_at IS NULL` — enforces "at most one live default form template per group" at the database level. This index is SQL-only (added directly in the migration, not expressible in the Prisma schema DSL) — `prisma migrate diff` will not see it, so it must not be dropped by a future auto-generated migration

**Indexes:**
- `@@index([report_group])` — map `"idx_report_template_report_group"` — supports listing templates filtered or sorted by group

## 3. Relationships

```
tb_report_template  self-FK  created_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  updated_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  deleted_by_id  → tb_user.id  (audit; no Prisma @relation)
```

**Removed 2026-07-23:** `tb_report_template 1 ─── M tb_print_template_mapping` no longer exists — the mapping table was dropped outright, not merely disconnected. See [Print Template Mapping](/en/platform/print-template-mapping) for the removal.

Notable absences:

- **No FK to `tb_cluster`** — report templates are tenant-global, not cluster-scoped. There is no cluster column on `tb_report_template`.
- **No FK to `tb_business_unit`** — the `allow_business_unit` and `deny_business_unit` columns reference BU codes by value (application-layer convention), not by a declared FK constraint. The database does not enforce referential integrity between these JSON columns and `tb_business_unit.code`.
- **Audit FKs are application-layer only** — `created_by_id`, `updated_by_id`, and `deleted_by_id` are typed as `String? @db.Uuid` in Prisma but carry no `@relation` directive. The schema does not declare FK constraints for these fields, consistent with the pattern used across the platform schema for the delete path.

## 4. Enums

`source_type` is declared as `String @db.VarChar(20)` in Prisma — it is **not** a Prisma named enum. The database does not enforce the set of allowed values. The SPA (`ReportTemplateEdit.tsx`) enforces the valid set at the client layer via a typed union: `"view" | "function" | "procedure"`. The `reportTemplateService.ts` re-exports this union as `ReportSourceType`.

| Value | Meaning |
| ----- | ------- |
| `"view"` | The executor runs `SELECT * FROM <source_name>` (default). `source_params` is not used; filters are applied via a runtime WHERE clause |
| `"function"` | The executor runs `SELECT * FROM <source_name>($1, $2, …)` where the function returns a TABLE or SETOF. Arguments are positional, mapped by `source_params.params` in declaration order |
| `"procedure"` | The executor runs `CALL <source_name>($1, …, 'rs'::refcursor)` and fetches from the cursor named `rs`. Arguments are positional from `source_params.params`; the trailing refcursor is a runtime convention not represented in `source_params` |

Similarly, `template_type` and `orientation` are plain String columns. Their valid values are enforced only at the application layer:

- `template_type`: `"list"` (default) or `"form"` — renamed from `kind` (`"report"`/`"print"`) by migration `20260723120000_print_form_default`
- `orientation`: `"portrait"` (default) or `"landscape"`

## 5. The JSON columns

Four columns on `tb_report_template` carry structured payloads that the database cannot validate internally — the application layer owns those contracts. Two of them (`source_params`, `signature_config`) are `Json @db.JsonB` columns; the other two (`dialog`, `content`) are `String @db.Text` columns that hold XML strings. The per-subsection detail below covers each column's shape.

### 5.1 `dialog` (XML payload)

A non-nullable `String @db.Text` column (not `Json`) containing the XML that the report runtime renders as the parameter input form shown to users before running the report. An empty string `""` is the valid "no parameters" state for templates that take no user input.

The Dialog tab in the SPA editor accepts free-form XML entry or file upload. Detailed XML element and attribute reference is in [XML Spec §2](/en/platform/report-templates/xml-spec).

### 5.2 `content` (XML payload)

A non-nullable `String @db.Text` column containing the XML that defines the report output layout — columns, groupings, totals, formatting, etc. An empty string is valid for a newly created template before content is added.

The Content tab in the editor accepts direct XML entry and also allows uploading `.frx`, `.xml`, or `.txt` files, which supports migrating legacy FastReport template files. Detailed XML structure is in [XML Spec §3](/en/platform/report-templates/xml-spec).

### 5.3 `source_params` (object)

A non-nullable `Json @db.JsonB` column with default `{"params":[]}`.

Shape:

```
{
  "params": [
    { "filter": "DateFrom",  "type": "date",  "nullable": false },
    { "filter": "DateTo",    "type": "date",  "nullable": false },
    { "filter": "BuCode",    "type": "text",  "nullable": true  }
  ]
}
```

Each element in `params` maps one Dialog filter field name (the `filter` key, e.g. `"DateFrom"`) to a PostgreSQL parameter type (the `type` key, e.g. `"date"`, `"uuid"`, `"text"`) plus a `nullable` boolean flag.

Behaviour by `source_type`:

- **`"view"`** — `source_params` is ignored at runtime. The executor applies filter values via a WHERE clause rather than positional arguments. An empty `{ "params": [] }` (the default) is the correct value.
- **`"function"`** — the `params` array is positional. Arguments are passed to the function in the order they appear in the array, matching the function's declared parameter list.
- **`"procedure"`** — same positional binding as `"function"`. The procedure is additionally called with a trailing `INOUT refcursor` named `rs` (the executor fetches `FETCH ALL FROM "rs"` after the call). This trailing cursor is a runtime convention and is **not** represented in `source_params`.

The SPA's `SourceParamRow` interface (`ReportTemplateEdit.tsx`, line 30) mirrors the per-element shape:

```
interface SourceParamRow {
  filter:   string
  type:     string
  nullable: boolean
}
```

On save, the SPA constructs `{ params: cleanParams }` where `cleanParams` is the array with blank rows filtered out.

### 5.4 `signature_config` (object)

A non-nullable `Json @db.JsonB` column with default `{"blocks":[]}`.

Shape:

```
{
  "blocks": [
    { "key": "Sig1Name", "label": "Requestor",   "required": true  },
    { "key": "Sig2Name", "label": "Department",  "required": true  },
    { "key": "Sig3Name", "label": "Approver",    "required": false }
  ]
}
```

Each block defines one signature line on the printed document. The `key` field corresponds to the legacy `Sig1Name`…`Sig5Name` naming convention used in earlier workflow-stage-based signature lookup; the `label` is the human-readable role name printed above the signature line. This replaces the previous behaviour where signature names were pulled from active workflow stage definitions at print time.

`signature_config` is not surfaced in the current `ReportTemplateFormData` interface in the SPA — it is managed separately from the main edit form.

## 6. Divergences from carmen-platform SPA shape

The `ReportTemplate` interface in `../carmen-platform/src/services/reportTemplateService.ts` (lines 19–44) and the `ReportTemplateFormData` interface in `../carmen-platform/src/pages/ReportTemplateEdit.tsx` (lines 44–60) were compared against the Prisma `tb_report_template` model. Notably, the `ReportTemplate` TS interface lives in `src/services/reportTemplateService.ts`, not `src/types/index.ts` where the other Platform-module interfaces (`Cluster`, `BusinessUnit`, `User`) reside — developers searching for the canonical TS shape should look in the service file.

**Resolved 2026-07-23 (no longer a divergence):** `kind`/`template_type` and `is_default` now match on both sides. `ReportTemplateFormData` carries `template_type: '' | 'form' | 'list'` (required, exposed as a select) and `is_default: boolean` — the previous sync's item 1 ("`kind` absent from the form") is stale; the field is not only present but required at submit.

| # | Item | Prisma has | SPA expects | Notes |
| - | ---- | ---------- | ----------- | ----- |
| 1 | `orientation` | `String @db.VarChar(20)` | Not present in `ReportTemplate` or `ReportTemplateFormData` | Still not surfaced in the SPA as of 2026-07-29. Defaults to `"portrait"` at the database level |
| 2 | `signature_config` | `Json @db.JsonB` | Not present in `ReportTemplate` or `ReportTemplateFormData` | Still not surfaced in the SPA edit form |
| 3 | `view_name` | `String? @db.VarChar` | Not in `ReportTemplate` service interface | Legacy column; accessed only implicitly in the Edit form load path (`template.source_name \|\| template.view_name`) as a fallback |
| 4 | `allow_business_unit` / `deny_business_unit` | `Json? @db.JsonB` | `unknown` on `ReportTemplate` service interface; `string` in `ReportTemplateFormData` | The Edit form normalises the JSON value (array or scalar) to a comma-separated string via `toCsv()` for the chip-input field. Disabled and cleared client-side when `template_type = 'form'` — form templates are not BU-scoped this way |
| 5 | `created_by_id` / `updated_by_id` | `String? @db.Uuid` (raw IDs) | `created_by_id?: string` / `updated_by_id?: string` on `ReportTemplate` | Raw IDs are present in the service interface. The SPA also reads `created_by_name` / `updated_by_name` from the API response (resolved by the backend), but these are held in a separate `MetadataFields` state variable, not in the `ReportTemplate` type |
| 6 | `source_params` | `Json @db.JsonB` (non-nullable) | `source_params?: ReportSourceParams` (optional) on service interface | The service interface marks it optional to handle partial API responses; the Prisma default ensures the DB column always has a value |

All core identity fields (`id`, `name`, `description`, `report_group`, `template_type`), XML payload fields (`dialog`, `content`), source binding fields (`source_type`, `source_name`), lifecycle flags (`is_standard`, `is_default`, `is_active`), `doc_version`, and audit timestamps (`created_at`, `updated_at`) align between Prisma and the SPA shape. Remaining divergences are new Prisma columns not yet surfaced in the edit form (items 1–3) or form-layer type coercions for JSON columns (items 4, 6).

## 7. References

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `model tb_report_template` (line 806 — corrects an earlier sync's "line 734"; the file grew above this model since the last sync).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260723120000_print_form_default/migration.sql` — the `kind`→`template_type` rename's accompanying data migration, `is_default` addition, unique index, and `tb_print_template_mapping` drop.

**Secondary (consumer shape):**
- `../carmen-platform/src/pages/ReportTemplateEdit.tsx` — `ReportTemplateFormData` interface (lines 44–60); `SourceParamRow` interface (lines 38–42); load path incl. `toCsv` (lines 196–262); save path incl. `source_params`/`template_type` payload construction (lines 302–368).
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` — report template list view.
- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx` — the Form Groups screen that edits `is_default` per `report_group`.
- `../carmen-platform/src/constants/reportGroups.ts` — `FORM_REPORT_GROUPS`, the fixed 12-code list the SPA constrains `report_group` to for form templates.
- `../carmen-platform/src/services/reportTemplateService.ts` — `ReportTemplate` interface (lines 19–44); `ReportSourceType`, `ReportSourceParam`, `ReportSourceParams` types (lines 5–17); `setGroupDefault` (lines 89–107).
- `../carmen-platform/src/types/index.ts` — no `ReportTemplate` type defined here; the type lives in the service file.

**Cross-links:**
- [report-templates](/en/platform/report-templates) — module landing page
- [print-template-mapping](/en/platform/print-template-mapping) — **removed 2026-07-23/24** (historical page); used to own `tb_print_template_mapping`, dropped by the same migration that added `is_default` here
- [business-units](/en/platform/business-units) — BU codes referenced in the allow/deny chip lists correspond to `tb_business_unit.code`
- [clusters](/en/platform/clusters) — sibling Platform surface; report templates are tenant-global and not cluster-scoped
- [Permissions](/en/platform/report-templates/permissions) — access control for the report-templates admin surface
- [UI Screens](/en/platform/report-templates/ui-screens) — SPA screens for report template management and editing
- [XML Spec](/en/platform/report-templates/xml-spec) — detailed structure of the `dialog` and `content` XML payloads
