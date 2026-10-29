---
title: Report Template — Data Model
description: tb_report_template and tb_report_template_version: dialog/content/export XML, EN/TH names, source binding, BU and costing-method scope, run/export switches, template_type, is_default and doc_version.
published: true
date: 2026-10-29T05:30:00.000Z
tags: book/backstage, report-templates, data-model
editor: markdown
dateCreated: 2026-05-19T18:30:00.000Z
---

# Report Template — Data Model

> **At a Glance**
> **Tables:** `tb_report_template` (primary) and `tb_report_template_version` (snapshot per write, §2.2) &nbsp;·&nbsp; **Former sibling table:** `tb_print_template_mapping` — **dropped 2026-07-23** (migration `20260723120000_print_form_default`), its `is_default` role absorbed onto this table; the print-template-mapping module that owned it was removed from the product 2026-07-24 (carmen-backstage commit `de11377`; see §7 Cross-links) &nbsp;·&nbsp; **JSON/XML payloads:** `dialog` (XML, non-nullable), `content` (XML, non-nullable), `export_xml` (XML, nullable), `name_i18n` / `description_i18n` (`{en?, th?}`), `source_params` (`{ params: [...] }`), `signature_config` (`{ blocks: [...] }`) &nbsp;·&nbsp; **Source binding:** `source_type` (plain String: `view` / `function` / `procedure`) + `source_name` + `source_params` &nbsp;·&nbsp; **BU scope:** `allow_business_unit` / `deny_business_unit` stored as `Json?`; serialised to CSV strings in the SPA form &nbsp;·&nbsp; **Costing scope:** `calculation_methods` (`enum_calculation_method[]`, empty = all) &nbsp;·&nbsp; **Lifecycle flags:** `is_standard`, `is_default` (form templates only, new 2026-07-23), `is_active`, `allow_run`, `allow_export`, `doc_version`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

`tb_report_template` is the catalogue entry for one printable or exportable document in Carmen Blue. Each row encodes the complete definition of a report: its identity (`name`, `report_group`, `template_type`), two XML payload columns (`dialog` and `content`) consumed by the report runtime, the runtime source binding (`source_type`, `source_name`, `source_params`), print-layout fields (`orientation`, `signature_config`), a BU-scope allow/deny pair, and the standard lifecycle flags and audit trio (including `doc_version`, the platform-wide optimistic-lock column added 2026-06-12 — **corrected**, an earlier sync misdated this 2026-07-16).

Report templates are tenant-global — they are not cluster-scoped and carry no FK to `tb_cluster`. The BU-scope columns (`allow_business_unit`, `deny_business_unit`) are opt-in filtering lists that restrict which business units a template is visible to; they do not bind the row to any particular cluster. This distinguishes the report-templates surface from the [clusters](/en/backstage/clusters) and [business-units](/en/backstage/business-units) pages, which document the cluster/BU hierarchy. BU codes referenced in the chip lists correspond to `tb_business_unit.code` values, but there is no FK constraint — the reference is an application-layer convention.

The table also grew in the 2026-08 to 2026-10 rounds: EN/TH names (`name_i18n`, `description_i18n`), an Export XML column, run/export switches, a costing-method scope, and a sibling `tb_report_template_version` table that records every write (§2.2). The `template_type` column (renamed from `kind` by migration `20260723120000_print_form_default`, 2026-07-23) distinguishes the two uses of this table: `"list"` rows (was `"report"`) are user-facing tabular analytical reports; `"form"` rows (was `"print"`) are single-record document layouts. Until 2026-07-23, a separate `tb_print_template_mapping` table mapped document types (PO, GRN, SR, …) to a `kind="print"` row here; that table has been **dropped**. Its job — picking the one default template a business unit gets for a given group — is now done by this table's own `is_default` column, scoped to `report_group` and enforced by a partial unique index (§2.1). The print-template-mapping module that owned this table was itself removed from the product 2026-07-24 (carmen-backstage commit `de11377`) — see §7 Cross-links for the full removal timeline; this page covers `tb_report_template` only.

## 2. Entities

### 2.1 `tb_report_template`

One row per report or print template. The field table below follows the Prisma declaration order, grouped by purpose. The table has more than 15 fields, so bold separator rows are used to cluster related columns.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| **— Identity —** | | | | |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `name` | `String @db.VarChar(255)` | No | — | Human-readable template name; unique among live rows (with `deleted_at`) |
| `description` | `String?` | Yes | — | Optional free-text description of the template's purpose |
| `name_i18n` | `Json? @db.JsonB` | Yes | — | Localized names `{ en?, th? }`. `name` stays the unique key and is dual-written equal to `name_i18n.en`; the service rejects an empty name on create and update, and the SPA sends both on every save |
| `description_i18n` | `Json? @db.JsonB` | Yes | — | Localized descriptions `{ en?, th? }`; `description` remains the EN value of record |
| `report_group` | `String @db.VarChar(100)` | No | — | Grouping key used to organise templates in the management list (e.g. `"Receiving"`, `"Inventory"`) |
| `template_type` | `String @default("list") @db.Text` | No | `"list"` | Template category: `"list"` (tabular analytical report, was `"report"`) or `"form"` (single-record document layout, was `"print"`). Renamed from `kind` by migration `20260723120000_print_form_default` (2026-07-23); values changed at the same time |
| **— XML Payloads —** | | | | |
| `dialog` | `String @db.Text` | No | — | XML string defining the parameter form rendered by the report runtime. Not nullable — an empty string `""` is the valid "no dialog" value. Detailed XML structure documented in [XML Spec §2](/en/backstage/report-templates/xml-spec) |
| `content` | `String @db.Text` | No | — | XML string defining the report output layout rendered by the report runtime. Not nullable — `""` is valid for a new template. The Content tab in the editor also accepts `.frx` / `.xml` / `.txt` file uploads (legacy FastReport migration). Detailed structure in [XML Spec §3](/en/backstage/report-templates/xml-spec) |
| `export_xml` | `String? @db.Text` | Yes | — | `<Export>` document mapping the report dataset to CSV columns for the "Export data" action. `NULL` = no export mapping; the service stores a blank/whitespace string as `NULL`. Format: [XML Spec §4](/en/backstage/report-templates/xml-spec) |
| **— Go Builder —** | | | | |
| `builder_key` | `String @db.VarChar(100)` | No | `""` | **Corrected 2026-10-27 — no longer nullable** (empty string = not linked). Links a template row to a Go report.Definition registry key. When set, the Go runtime uses this key to resolve the report definition rather than executing `source_type`/`source_name` directly |
| **— Source Binding (legacy) —** | | | | |
| `view_name` | `String? @db.VarChar` | Yes | — | Legacy column retained for backward compatibility. Prefer `source_type` + `source_name`. The Go registry falls back to `view_name` when `source_name` is empty. The SPA loads `source_name` as `template.source_name \|\| template.view_name` |
| **— Source Binding —** | | | | |
| `source_type` | `String @db.VarChar(20)` | No | `"view"` | Tells the report executor how to read the data. Plain String — not a Prisma enum; the SPA validates the values client-side. Valid values: `"view"`, `"function"`, `"procedure"` (see §4) |
| `source_name` | `String? @db.VarChar` | Yes | — | Bare identifier of the view, function, or procedure (no schema prefix; resolved against the tenant's `current_schema()`). Required when `source_type` is `"function"` or `"procedure"` — the SPA enforces this with a field-level validation error |
| `source_params` | `Json @db.JsonB` | No | `{"params":[]}` | Positional argument mapping for function/procedure invocations. Shape: `{ "params": [{ "filter": "DateFrom", "type": "date", "nullable": false }, ...] }`. Default is an empty params array; see §5.3 |
| **— Print Layout —** | | | | |
| `orientation` | `String @db.VarChar(20)` | No | `"portrait"` | Page orientation for print-style templates: `"portrait"` or `"landscape"`. Replaces the legacy `"Document Landscape"` name suffix convention |
| `signature_config` | `Json @db.JsonB` | No | `{"blocks":[]}` | Signature block definitions rendered on the print layout. Shape: `{ "blocks": [{ "key": "Sig1Name", "label": "Requestor", "required": true }, ...] }`. Replaces the previous behaviour of pulling `Sig1Name`…`Sig5Name` from active workflow stages |
| **— Costing scope —** | | | | |
| `calculation_methods` | `enum_calculation_method[]` | No | `[]` | Costing methods the template supports: `average`, `fifo`, `average_per_location`. Empty = supports every method. micro-report refuses a run for a business unit whose method is not listed (`calculation_method_unsupported`); form templates are exempt. The SPA clears it for `template_type = "form"` |
| **— Run / export switches —** | | | | |
| `allow_run` | `Boolean` | No | `true` | Shows the Run Report button. The interactive run of a `list` template is refused when `false` (micro-report `run_disabled`); schedules are not affected (only the web caller is checked). Not sent for form templates |
| `allow_export` | `Boolean` | No | `false` | Shows the Export data button; micro-report refuses the export endpoint when `false` (`export_disabled`). `has_export` in the BU template list is true only when `allow_export` is on **and** `export_xml` is non-blank |
| **— Lifecycle —** | | | | |
| `is_standard` | `Boolean` | No | `true` | Marks the template as a standard (system-provided) template. Standard templates are typically read-only for end operators |
| `is_default` | `Boolean` | No | `false` | **New 2026-07-23.** Meaningful only for `template_type = "form"`: the one live template per `report_group` used when a business unit hasn't chosen one. Enforced by the partial unique index below, not just application logic — this is the column that absorbed `tb_print_template_mapping.is_default` when that table was dropped |
| **— BU Scope —** | | | | |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | — | Optional list of BU codes that may see this template. `NULL` or empty = visible to all BUs. **Stored as received:** the SPA sends a comma-separated string (so rows saved from the Edit page hold a JSON string), while seeds and API writers may store an array; the SPA reads either (array or scalar) and normalises to a CSV string via `toCsv()`, and micro-report's `ParseBuList` accepts both shapes (comparison is case-insensitive). Ignored for `form` templates |
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

### 2.2 `tb_report_template_version`

One immutable snapshot row per write to a template. Added in the 2026-10 rounds (carmen-turborepo-backend commits `0aba9ec75` table + create/update snapshots, `3468a5bc7` list/get/restore endpoints). Written inside the same transaction as the write (`writeVersion`, `report-template-version.ts`); delete does **not** write a version.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`) |
| `report_template_id` | `String @db.Uuid` | No | FK to `tb_report_template.id` |
| `version` | `Int` | No | The template's `doc_version` **after** the write; unique per template (`report_template_version_template_version_u`) |
| `snapshot` | `Json @db.JsonB` | No | The editable fields (`SNAPSHOT_FIELDS`): `name`, `name_i18n`, `description`, `description_i18n`, `report_group`, `template_type`, `dialog`, `content`, `export_xml`, `allow_run`, `allow_export`, `builder_key`, `view_name`, `source_type`, `source_name`, `source_params`, `orientation`, `signature_config`, `is_standard`, `is_default`, `is_active`, `allow_business_unit`, `deny_business_unit`, `calculation_methods` |
| `change_type` | `String @db.VarChar(20)` | No | `create` \| `update` \| `restore` \| `import` (`import` is set when the payload carries `change_type: "import"`, which the SPA's Import dialog does) |
| `restored_from_version` | `Int?` | Yes | Source version when `change_type = "restore"` |
| `note` | `String?` | Yes | Free text; not written by any current code path |
| `created_at` / `created_by_id` | `DateTime` / `String? @db.Uuid` | No / Yes | When and by whom |

Index: `(report_template_id, created_at DESC)` (`idx_report_template_version_template_created`). **Restore** (`POST .../versions/:version_no/restore`, body `{ doc_version }`) copies the snapshot back onto the live row under the usual optimistic lock and writes a new `restore` version; it deliberately leaves `is_default` untouched (the partial unique index allows one default per group), re-validates `source_name` against the identifier pattern, and keeps the current `calculation_methods` when the snapshot predates that field. A missing version answers `REPORT_TEMPLATE_VERSION_NOT_FOUND` (`report-template.service.ts` `restoreVersion`).

Because the set-default flow on [Form Groups](/en/backstage/report-form-groups) is two partial `PUT`s, each default switch writes **two** `update` versions (one per affected template).

`source_name` validation (new): the service rejects, with `COMMON_VALIDATION_FAILED`, any `source_name` that is not a bare identifier (`^[A-Za-z_][A-Za-z0-9_]*$`, at most 63 characters) on create, update and restore, because micro-report interpolates it unquoted into SQL (`report-template-source-name.ts`, commit `bb2530c12`).

## 3. Relationships

```
tb_report_template  1 ─── M  tb_report_template_version  (report_template_id; Prisma @relation)
tb_report_template  self-FK  created_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  updated_by_id  → tb_user.id  (audit; no Prisma @relation)
tb_report_template  self-FK  deleted_by_id  → tb_user.id  (audit; no Prisma @relation)
```

**Removed 2026-07-23:** `tb_report_template 1 ─── M tb_print_template_mapping` no longer exists — the mapping table was dropped outright, not merely disconnected (migration `20260723120000_print_form_default`); the print-template-mapping module itself was removed from the product the next day, 2026-07-24 (carmen-backstage commit `de11377`) — see §7 Cross-links.

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

Five columns on `tb_report_template` carry structured payloads that the database cannot validate internally — the application layer owns those contracts. Two of them (`source_params`, `signature_config`) are `Json @db.JsonB` columns; the other three (`dialog`, `content`, and the optional `export_xml`) are `String @db.Text` columns that hold XML strings (`export_xml` is documented in [XML Spec §4](/en/backstage/report-templates/xml-spec); the localized `name_i18n` / `description_i18n` and the BU lists are JsonB too but are simple enough to be covered in §2.1). The per-subsection detail below covers each column's shape.

### 5.1 `dialog` (XML payload)

A non-nullable `String @db.Text` column (not `Json`) containing the XML that the report runtime renders as the parameter input form shown to users before running the report. An empty string `""` is the valid "no parameters" state for templates that take no user input.

The Dialog tab in the SPA editor accepts free-form XML entry or file upload. Detailed XML element and attribute reference is in [XML Spec §2](/en/backstage/report-templates/xml-spec).

### 5.2 `content` (XML payload)

A non-nullable `String @db.Text` column containing the XML that defines the report output layout — columns, groupings, totals, formatting, etc. An empty string is valid for a newly created template before content is added.

The Content tab in the editor accepts direct XML entry and also allows uploading `.frx`, `.xml`, or `.txt` files, which supports migrating legacy FastReport template files. Detailed XML structure is in [XML Spec §3](/en/backstage/report-templates/xml-spec).

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

`signature_config` is not part of the SPA's `ReportTemplateFormData` interface — the edit form has no control for it, so a normal edit-page save does not send it (the backend's update leaves an omitted `signature_config` unchanged). It only travels through JSON backup/import and version snapshots.

## 6. Divergences from carmen-backstage SPA shape

The `ReportTemplate` interface in `../carmen-backstage/src/services/reportTemplateService.ts` (lines 21–59) and the `ReportTemplateFormData` interface in `../carmen-backstage/src/pages/ReportTemplateEdit.tsx` (lines 84–106) were compared against the Prisma `tb_report_template` model. Notably, the `ReportTemplate` TS interface lives in `src/services/reportTemplateService.ts`, not `src/types/index.ts` where the other Platform-module interfaces (`Cluster`, `BusinessUnit`, `User`) reside — developers searching for the canonical TS shape should look in the service file.

**Resolved 2026-07-23 (no longer a divergence):** `kind`/`template_type` and `is_default` now match on both sides. `ReportTemplateFormData` carries `template_type: '' | 'form' | 'list'` (required, exposed as a select) and `is_default: boolean` — the previous sync's item 1 ("`kind` absent from the form") is stale; the field is not only present but required at submit.

| # | Item | Prisma has | SPA expects | Notes |
| - | ---- | ---------- | ----------- | ----- |
| 1 | `orientation` | `String @db.VarChar(20)` | Optional on the `ReportTemplate` service type; not in `ReportTemplateFormData` | Still no form control as of 2026-10-27. Defaults to `"portrait"` at the database level; carried through backups, imports and version snapshots |
| 2 | `signature_config` | `Json @db.JsonB` | Optional on the `ReportTemplate` service type; not in `ReportTemplateFormData` | Still no form control. Carried through backups and imports (Import fills `{ blocks: [] }` when the file holds `{}`, as micro-report's seeder writes) |
| 3 | `view_name` | `String? @db.VarChar` | Optional on the `ReportTemplate` service type | Legacy column; the Edit form load path falls back to it (`template.source_name \|\| template.view_name`). The Import dialog strips it from payloads (the DTO does not accept it) but backups and version snapshots still carry it |
| 4 | `allow_business_unit` / `deny_business_unit` | `Json? @db.JsonB` | `unknown` on `ReportTemplate` service interface; `string` in `ReportTemplateFormData` | The Edit form normalises the JSON value (array or scalar) to a comma-separated string via `toCsv()` for the chip-input field. Disabled and cleared client-side when `template_type = 'form'` — form templates are not BU-scoped this way |
| 5 | `created_by_id` / `updated_by_id` | `String? @db.Uuid` (raw IDs) | `created_by_id?: string` / `updated_by_id?: string` on `ReportTemplate` | Raw IDs are present in the service interface. The SPA also reads `created_by_name` / `updated_by_name` from the API response (resolved by the backend), but these are held in a separate `MetadataFields` state variable, not in the `ReportTemplate` type |
| 6 | `source_params` | `Json @db.JsonB` (non-nullable) | `source_params?: ReportSourceParams` (optional) on service interface | The service interface marks it optional to handle partial API responses; the Prisma default ensures the DB column always has a value |

All core identity fields (`id`, `name`, `description`, `report_group`, `template_type`), XML payload fields (`dialog`, `content`), source binding fields (`source_type`, `source_name`), lifecycle flags (`is_standard`, `is_default`, `is_active`), `doc_version`, and audit timestamps (`created_at`, `updated_at`) align between Prisma and the SPA shape. Remaining divergences are new Prisma columns not yet surfaced in the edit form (items 1–3) or form-layer type coercions for JSON columns (items 4, 6).

## 7. References

**Primary (source of truth):**
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` — `model tb_report_template` (line 1027) and `model tb_report_template_version` (line 1124).
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/migrations/20260723120000_print_form_default/migration.sql` — the `kind`→`template_type` rename's accompanying data migration, `is_default` addition, unique index, and `tb_print_template_mapping` drop.

**Secondary (consumer shape):**
- `../carmen-backstage/src/pages/ReportTemplateEdit.tsx` — `ReportTemplateFormData` interface (lines 84–106); `SourceParamRow` interface (lines 78–82); load path incl. `toCsv` (`fetchTemplate`, lines 255–330); save path incl. `source_params`/`template_type`/i18n payload construction (`handleSubmit`, lines 384–485).
- `../carmen-backstage/src/pages/ReportTemplateManagement.tsx` — report template list view.
- `../carmen-backstage/src/pages/ReportFormGroupManagement.tsx` — the Form Groups screen that edits `is_default` per `report_group`.
- `../carmen-backstage/src/constants/reportGroups.ts` — `FORM_REPORT_GROUPS`, the fixed 12-code list the SPA constrains `report_group` to for form templates.
- `../carmen-backstage/src/services/reportTemplateService.ts` — `ReportTemplate` interface (lines 21–59); `ReportSourceType`, `CalculationMethod`, `ReportSourceParam`, `ReportSourceParams` types (lines 5–19); `setGroupDefault` (lines 118–137); `listVersions` / `getVersion` / `restoreVersion` (lines 139–158).
- `../carmen-backstage/src/types/index.ts` — no `ReportTemplate` type defined here; the type lives in the service file.

**Cross-links:**
- [report-templates](/en/backstage/report-templates) — module landing page
- **Print Template Mapping** — removed from the product 2026-07-24 (carmen-backstage commit `de11377`); used to own `tb_print_template_mapping`, dropped by the same `20260723120000_print_form_default` migration that added `is_default` here. Its job is now served by `template_type = "form"` + `report_group` + `is_default` on this table, surfaced by the standalone [Form Groups](/en/backstage/report-form-groups) module
- [business-units](/en/backstage/business-units) — BU codes referenced in the allow/deny chip lists correspond to `tb_business_unit.code`
- [clusters](/en/backstage/clusters) — sibling Platform surface; report templates are tenant-global and not cluster-scoped
- [Permissions](/en/backstage/report-templates/permissions) — access control for the report-templates admin surface
- [UI Screens](/en/backstage/report-templates/ui-screens) — SPA screens for report template management and editing
- [XML Spec](/en/backstage/report-templates/xml-spec) — detailed structure of the `dialog` and `content` XML payloads
