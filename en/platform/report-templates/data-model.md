---
title: Report Template — Data Model
description: tb_report_template entity, dialog/content XML payloads, source binding, BU scope.
published: true
date: 2026-05-19T23:55:00.000Z
tags: book/platform, report-templates, data-model
editor: markdown
dateCreated: 2026-05-19T18:30:00.000Z
---

# Report Template — Data Model

> **At a Glance**
> **Tables:** `tb_report_template` (primary) &nbsp;·&nbsp; **Out of scope:** `tb_print_template_mapping` (sibling feature pair, separate documentation) &nbsp;·&nbsp; **JSON payloads:** `dialog` (XML, non-nullable), `content` (XML, non-nullable), `source_params` (`{ params: [...] }`), `signature_config` (`{ blocks: [...] }`) &nbsp;·&nbsp; **Source binding:** `source_type` (plain String: `view` / `function` / `procedure`) + `source_name` + `source_params` &nbsp;·&nbsp; **BU scope:** `allow_business_unit` / `deny_business_unit` stored as `Json?`; serialised to CSV strings in the SPA form &nbsp;·&nbsp; **Lifecycle flags:** `is_standard`, `is_active`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

`tb_report_template` is the catalogue entry for one printable or exportable document in the Carmen Platform. Each row encodes the complete definition of a report: its identity (`name`, `report_group`, `kind`), two XML payload columns (`dialog` and `content`) consumed by the report runtime, the runtime source binding (`source_type`, `source_name`, `source_params`), a BU-scope allow/deny pair, and the standard lifecycle flags and audit trio.

Report templates are tenant-global — they are not cluster-scoped and carry no FK to `tb_cluster`. The BU-scope columns (`allow_business_unit`, `deny_business_unit`) are opt-in filtering lists that restrict which business units a template is visible to; they do not bind the row to any particular cluster. This distinguishes the report-templates surface from the [clusters](/en/platform/clusters) and [business-units](/en/platform/business-units) pages, which document the cluster/BU hierarchy. BU codes referenced in the chip lists correspond to `tb_business_unit.code` values, but there is no FK constraint — the reference is an application-layer convention.

The `kind` column distinguishes the two uses of this table: `"report"` rows are user-facing analytical reports; `"print"` rows are printable document layouts consumed by `tb_print_template_mapping`. That sibling join table (Prisma model `tb_print_template_mapping`) maps document types (PO, GRN, SR, …) to a `tb_report_template` row. It is not documented here — this page covers `tb_report_template` only.

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
| `kind` | `String @db.VarChar(20)` | No | `"report"` | Template category: `"report"` (analytical report visible to users) or `"print"` (document layout consumed by `tb_print_template_mapping`) |
| **— XML Payloads —** | | | | |
| `dialog` | `String @db.Text` | No | — | XML string defining the parameter form rendered by the report runtime. Not nullable — an empty string `""` is the valid "no dialog" value. Detailed XML structure documented in [XML Spec §2](./xml-spec.md) |
| `content` | `String @db.Text` | No | — | XML string defining the report output layout rendered by the report runtime. Not nullable — `""` is valid for a new template. The Content tab in the editor also accepts `.frx` / `.xml` / `.txt` file uploads (legacy FastReport migration). Detailed structure in [XML Spec §3](./xml-spec.md) |
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
| **— BU Scope —** | | | | |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | — | Optional list of BU codes that may see this template. `NULL` = visible to all BUs. The SPA reads this as an array (or scalar) and normalises it to a comma-separated string for the chip-input field via `toCsv()` |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | — | Optional list of BU codes explicitly excluded from seeing this template. `NULL` = no denials. Same `toCsv()` normalisation as `allow_business_unit` |
| `is_active` | `Boolean` | No | `true` | When `false`, the template is inactive and hidden from selection lists |
| **— Audit —** | | | | |
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

**Indexes:**
- `@@index([report_group])` — map `"idx_report_template_report_group"` — supports listing templates filtered or sorted by group

## 3. Relationships

```
tb_report_template  self-FK  created_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  updated_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  deleted_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  1 ─── M  tb_print_template_mapping      (via tb_print_template_mapping.report_template_id; out of scope for this page)
```

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

Similarly, `kind` and `orientation` are plain String columns. Their valid values are enforced only at the application layer:

- `kind`: `"report"` (default) or `"print"`
- `orientation`: `"portrait"` (default) or `"landscape"`

## 5. The JSON columns

Four columns on `tb_report_template` carry structured payloads that the database cannot validate internally — the application layer owns those contracts. Two of them (`source_params`, `signature_config`) are `Json @db.JsonB` columns; the other two (`dialog`, `content`) are `String @db.Text` columns that hold XML strings. The per-subsection detail below covers each column's shape.

### 5.1 `dialog` (XML payload)

A non-nullable `String @db.Text` column (not `Json`) containing the XML that the report runtime renders as the parameter input form shown to users before running the report. An empty string `""` is the valid "no parameters" state for templates that take no user input.

The Dialog tab in the SPA editor accepts free-form XML entry or file upload. Detailed XML element and attribute reference is in [XML Spec §2](./xml-spec.md).

### 5.2 `content` (XML payload)

A non-nullable `String @db.Text` column containing the XML that defines the report output layout — columns, groupings, totals, formatting, etc. An empty string is valid for a newly created template before content is added.

The Content tab in the editor accepts direct XML entry and also allows uploading `.frx`, `.xml`, or `.txt` files, which supports migrating legacy FastReport template files. Detailed XML structure is in [XML Spec §3](./xml-spec.md).

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

The `ReportTemplate` interface in `../carmen-platform/src/services/reportTemplateService.ts` (lines 17–37) and the `ReportTemplateFormData` interface in `../carmen-platform/src/pages/ReportTemplateEdit.tsx` (lines 36–50) were compared against the Prisma `tb_report_template` model. Notably, the `ReportTemplate` TS interface lives in `src/services/reportTemplateService.ts` (line 17), not `src/types/index.ts` where the other Platform-module interfaces (`Cluster`, `BusinessUnit`, `User`) reside — developers searching for the canonical TS shape should look in the service file.

| # | Item | Prisma has | SPA expects | Notes |
| - | ---- | ---------- | ----------- | ----- |
| 1 | `kind` | `String @db.VarChar(20)` | `kind: 'report' \| 'print'` on `ReportTemplate` service interface | Present in the service type but absent from `ReportTemplateFormData` — the SPA edit form does not expose a `kind` field. Templates are presumably assigned `kind` server-side or on creation |
| 2 | `orientation` | `String @db.VarChar(20)` | Not present in `ReportTemplate` or `ReportTemplateFormData` | New Prisma column not yet surfaced in the SPA. Defaults to `"portrait"` at the database level |
| 3 | `signature_config` | `Json @db.JsonB` | Not present in `ReportTemplate` or `ReportTemplateFormData` | Not yet surfaced in the SPA edit form |
| 4 | `view_name` | `String? @db.VarChar` | Not in `ReportTemplate` service interface | Legacy column; accessed only implicitly in the Edit form load path (`template.source_name \|\| template.view_name`) as a fallback |
| 5 | `allow_business_unit` / `deny_business_unit` | `Json? @db.JsonB` | `unknown` on `ReportTemplate` service interface; `string` in `ReportTemplateFormData` | The Edit form normalises the JSON value (array or scalar) to a comma-separated string via `toCsv()` for the chip-input field. The service interface types these as `unknown` to accommodate both the raw JSON from the API and the serialised form value |
| 6 | `created_by_id` / `updated_by_id` | `String? @db.Uuid` (raw IDs) | `created_by_id?: string` / `updated_by_id?: string` on `ReportTemplate` | Raw IDs are present in the service interface. The SPA also reads `created_by_name` / `updated_by_name` from the API response (resolved by the backend), but these are held in a separate `MetadataFields` state variable, not in the `ReportTemplate` type |
| 7 | `source_params` | `Json @db.JsonB` (non-nullable) | `source_params?: ReportSourceParams` (optional) on service interface | The service interface marks it optional to handle partial API responses; the Prisma default ensures the DB column always has a value |

All core identity fields (`id`, `name`, `description`, `report_group`), XML payload fields (`dialog`, `content`), source binding fields (`source_type`, `source_name`), lifecycle flags (`is_standard`, `is_active`), and audit timestamps (`created_at`, `updated_at`) align between Prisma and the SPA shape. Divergences are primarily new Prisma columns not yet surfaced in the edit form (items 2–4) or form-layer type coercions for JSON columns (items 5, 7).

## 7. References

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `model tb_report_template` (line 567).

**Secondary (consumer shape):**
- `../carmen-platform/src/pages/ReportTemplateEdit.tsx` — `ReportTemplateFormData` interface (lines 36–50); `SourceParamRow` interface (lines 30–34); `toCsv` helper and load path (lines 180–204); save path `source_params` construction (lines 278–285).
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` — report template list view.
- `../carmen-platform/src/services/reportTemplateService.ts` — `ReportTemplate` interface (lines 17–37); `ReportSourceType`, `ReportSourceParam`, `ReportSourceParams` types (lines 5–15).
- `../carmen-platform/src/types/index.ts` — no `ReportTemplate` type defined here; the type lives in the service file.

**Cross-links:**
- [report-templates](/en/platform/report-templates) — module landing page
- [business-units](/en/platform/business-units) — BU codes referenced in the allow/deny chip lists correspond to `tb_business_unit.code`
- [clusters](/en/platform/clusters) — sibling admin-tier-gated surface; report templates are tenant-global and not cluster-scoped
- [Permissions](./permissions.md) — access control for the report-templates admin surface
- [UI Screens](./ui-screens.md) — SPA screens for report template management and editing
- [XML Spec](./xml-spec.md) — detailed structure of the `dialog` and `content` XML payloads
