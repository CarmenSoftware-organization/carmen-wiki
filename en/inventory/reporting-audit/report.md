---
title: Report
description: Report pipeline — Backstage report-template catalogue (list reports + print forms with a per-group default), per-document print-viewer endpoints, PDF export for email, and a job/history table that is real but still orphaned.
published: true
date: 2026-10-27T00:00:00.000Z
tags: reporting-audit, report, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Report

> **At a Glance**
> **Owner:** Backstage admin (templates) + BU admin (print-form choice in Default Setting) &nbsp;·&nbsp; **Tables:** `tb_report_template` (Backstage schema — list reports **and** print forms, `template_type` + `is_default`), `tb_report_job` (tenant — real but orphaned) &nbsp;·&nbsp; **Gone:** `tb_print_template_mapping` (dropped 2026-07-23), `tb_report_schedule` (dead) &nbsp;·&nbsp; **Used by:** the report list ("Run"), every "Print" button (11 per-document `print-viewer` endpoints), PO/RFP email-with-PDF, scheduled fires — none write a job row.

![Report screen](/screenshots/reporting-audit/report.png)

## Implementation status (re-verified 2026-10-27)

Changes since 2026-09-22 (micro-report `c9ebf77..origin/main`, FE `0713cbc9..391062b5`, backend `ef4d6f08f..c9d788829`):

1. **Export data (CSV).** A second action next to Run: `POST /api/{bu}/reports/export { template_id, filters }` → micro-report `POST /api/{bu}/report/export` maps the template's dataset through its **Export XML** (`tb_report_template.export_xml`) into a UTF-8-with-BOM CSV (§ 1.4).
2. **Per-template switches and availability.** `allow_run` (default on) and `allow_export` (default off) on the template drive which buttons the report list shows; a template refused for a BU answers **403 `REPORT_TEMPLATE_UNAVAILABLE`** with a `reason` (§ 1.5).
3. **Smarter parameter dialog.** `<Dialog Cols>`, `<Group>`, `Label=` on controls, `<TextBox>`, `<Note>`, paired From-To fields on one row, a 30-minute per-BU/report memory of the last parameters, picker lists re-fetched each time the dialog opens, and server-side picker search (§ 1.6).
4. **New list-report templates** seeded in micro-report: Landed Cost Report (renamed from Extra Cost Report), Monthly Inventory Movement, Slow Moving, Receiving List, Purchase Request List, Purchase Order List, Product List, Vendor List, plus the Vendor Detail and Product Category forms (the last two print from the vendor and category pages). Several existing reports got new layouts (§ 5.3).
5. **Rename.** The "platform" schema is now "Backstage": package `prisma-shared-schema-backstage`, gateway `api-system/backstage/*` routes (the report-template admin API is still `api-system/report-templates`), env `PLATFORM_*` → `BACKSTAGE_*`.

**2026-09-22 verification (kept).**

The 2026-07-22 version of this page still described `tb_print_template_mapping` as the live print mapping. Platform migration `20260723120000_print_form_default` (2026-07-23) **dropped that table**: the default moved onto the template itself (`tb_report_template.is_default`, one per `report_group` among live `template_type = 'form'` rows, enforced by the partial unique index `idx_report_template_default_per_group`), `kind` became `template_type` (`form` | `list`), and the `RFQ` group was renamed `RFP`. The Bruno print-template-mapping requests were archived on 2026-07-29 ("endpoint not found in gateway controllers"). Print no longer goes through a generic resolve + viewer pair either — each document type has its own `GET /api/{bu}/{documents}/{id}/print-viewer` (§1.2).

Unchanged: the on-demand "Run" flow (`report-component.tsx` → `useRunReportMutation` → `POST /api/{bu}/reports/viewer`) and every Print button resolve straight to a viewer URL; neither calls `generate-async`, so neither writes a `tb_report_job` row — a repo-wide frontend search at HEAD still finds zero callers of `generate-async` / `job-status`. See [reporting-audit/history](/en/inventory/reporting-audit/history) and [reporting-audit/schedule](/en/inventory/reporting-audit/schedule).

New since 2026-07-29 (all in `micro-report` unless noted): PDF export for email attachments (§1.3, 2026-09-08), signature images baked into form templates (2026-08-05), Stock In / Stock Out form templates (`145630b`), tenant DB resolution through `tb_database_pool` (2026-08-18), `tb_inventory_period` raw SQL for period lookups (2026-09-16), and the shared internal RPC token — micro-report guards every route except `/health`, `/`, `/swagger` with `GinInternalAuth` (`ffb1abf`, 2026-09-14) and the gateway/micro-business must send `x-internal-token` (`bb7ea9e61`, "ไม่งั้นพิมพ์เอกสารไม่ได้").

## 1. What & Who

The report entity is the **report generation pipeline** — ad-hoc on-demand rendering, the print layout behind every "Print" button, PDF export for outbound email, and (structurally, though not currently populated) scheduled recurring exports. Two tables are relevant, plus the external scheduler database:

- `tb_report_template` (Backstage schema) — one catalogue for both **list reports** (`template_type = 'list'`, analytical, shown on `/report`) and **print forms** (`template_type = 'form'`, one document layout per `report_group` such as `PR`, `PO`, `GRN`, `SR`, `CN`, `SI`, `SO`, `IA`, `PC`, `SC`, `RFP`). Holds layout (`dialog`, `content`), data binding (`source_type` + `source_name` + `source_params`, `builder_key`), `orientation`, `signature_config`, `is_default`, `export_xml`, `allow_run`, `allow_export`, supported `calculation_methods`, BU allow/deny lists, and (2026-10-08) multilingual `name`/`description` and a version history table `tb_report_template_version`. Authored on the Backstage admin (`api-system/report-templates`, Backstage permission `report_template.*`); the inventory app only reads it.
- `tb_report_job` (tenant) — job/history table. Real and correctly wired to `/report/history`, but confirmed to receive zero writes from any currently-reachable UI path.

Report **schedules** live in the separate micro-cronjobs service — see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule).

**Maintained by** the Backstage admin (templates). A BU admin chooses which form prints each document type on the **Default Setting** screen (`/system-admin/default-setting`, "Print form" section, fed by `GET /api-system/report-templates/forms?perpage=-1` — opened to BU users on `685da259b`; only `AppIdGuard('report-template.findAll')` remains on that route). **Read by** the report list, every Print button, PO/RFP email send.

### 1.1 Dataset vs render — the micro-data split

Report generation is split across two Go services, with the **`Dataset`** object (columns + rows + totals + summary) as the boundary contract:

| Concern | Columns on `tb_report_template` | Owner | Does |
|---|---|---|---|
| **Dataset** | `source_type`, `source_name`, `source_params`, `dialog`, `view_name`, `builder_key` | **micro-data** | Resolves the view / function / procedure, composes the WHERE clause from filters, fans out across tenant BUs, returns `Dataset`. Renders nothing. |
| **Report** | `content`, `template_type`, `report_group`, `orientation`, `signature_config`, `is_default` | **micro-report** | Owns output format (viewer URL / PDF), template layout, form defaults, and job tracking. |

micro-report calls micro-data's `POST /api/datasets/execute` (`micro-report/service/dataset/client.go`) and renders the returned `Dataset`; the `tb_report_template` row still physically holds both column sets.

### 1.2 Print path (per document type)

`lib/print-document.ts` `printDocument()` maps each `PrintDocumentType` to a dedicated gateway endpoint, e.g. `GET /api/{bu}/purchase-orders/{id}/print-viewer?template_id=` — the same shape exists for PR, GRN, SR, CN, SI (`stock-ins`), SO (`stock-outs`), IA, PC (`physical-counts`), SC (`spot-checks`) and RFP (`request-for-pricings`); 11 gateway controllers carry a `print-viewer` route (Bruno `*/GET-print-to-report-*.bru`). **EOP** has no form template and no endpoint — configurable, not printable.

Each endpoint runs micro-business's `print-report.helper.ts`: pick the template — the caller's `template_id` (the BU's print-form choice) when supplied and valid for the group, else the `is_default` form whose `report_group` equals the document type (error when none) — build the header/detail payload, attach signature captions and images resolved from the workflow stages (`loadSignatureBlock()`, up to 5 signers), and `POST http://micro-report/api/{bu}/report/viewer-with-data` with `x-internal-token`. micro-report lifts each `Sig<N>Image` out of the payload and **bakes it into the template's `PictureObject`** before calling the FastReport viewer (`9a8e48a`, 2026-08-05 — the viewer never hydrates a `System.Byte[]` column from JSON, so binding silently rendered nothing). The viewer URL is opened through `safeNavigationHref` (rejects `javascript:`/`data:`).

### 1.3 PDF export for email

`POST /api/{bu}/report/export-pdf-with-data` (`904a1c6`, 2026-09-08) renders the same document a print would, but returns PDF bytes via the viewer's `/api/Report/Export/Pdf` (`service/render/viewer_client.go` `ExportPDF()`, `ExportReportWithExternalData()`). micro-business uses it to attach the PDF when sending a PO to the vendor by email (`1897b4fc1`) and when sending an RFP (`2b750267e`); both write an `email_sent` row to `tb_activity`, success or failure — see [reporting-audit/activity](/en/inventory/reporting-audit/activity).

### 1.4 Export data (CSV via Export XML)

| Aspect | Behaviour |
|---|---|
| Button | "Export data" in the report-parameter dialog, shown only when the template `has_export` (= `allow_export` and a non-blank `export_xml`); double-click guarded by a ref (`d71ef5f0`). The same hook (`hooks/use-export-report.ts`) powers the Print/Export button on the product-category page (`82e9c12d`, Product Category Report form) |
| Request | `POST /api/{bu}/reports/export` (gateway `reports.controller.ts:398`) with `{ template_id, filters }`; same filters as Run |
| Response | `200 text/csv; charset=utf-8` (BOM), `Content-Disposition: attachment; filename="<slug>_<yyyyMMdd_HHmmss>.csv"` (Asia/Bangkok clock), `X-Row-Count`; the gateway adds `Access-Control-Expose-Headers: Content-Disposition, X-Row-Count` so the SPA can read them. Zero rows → the FE shows an info toast instead of downloading |
| Errors | `400 export_not_configured` (no/blank Export XML) or invalid XML; `403 REPORT_TEMPLATE_UNAVAILABLE` (`export_disabled`, or BU/costing-method refusal) |
| Mapping | `<Export FileName GroupBy?>` with ordered `<Sort Field Desc?>` keys and `<Column Header Field|Value|Expression Format?>`; column order = CSV order. `GroupBy` pins the grouping so an export is one row per document regardless of the on-screen Group By; numeric strings (including `NUMERIC` returned as text) sort and print as numbers; `inf`/`NaN` strings with a numeric format are not numbers; cells starting with a formula character are neutralised (CSV formula-injection guard, `6cbd433`). Parser: `micro-report/service/export_xml.go` |
| Data | Same row builder as the viewer (`buildRowsForTemplate`) with the computed columns injected, dates left raw so `Format` can parse them; `GroupBy`, `BuName` and (when the template declares it) `CalculationMethod` are added per row |

Templates seeded with an Export XML at HEAD: Product List, Product Category, Credit Note Detail, Purchase Order List (the `db/seed/report-templates/*.export.xml` files); others can be configured in Backstage.

### 1.5 Availability, `allow_run` and `allow_export`

`EnsureAvailable` runs before every view/export. A template is refused for a BU with `403 { code: "REPORT_TEMPLATE_UNAVAILABLE", reason }`:

| `reason` | Cause |
|---|---|
| `bu_denied` | BU is in `deny_business_unit` |
| `bu_not_allowed` | `allow_business_unit` is non-empty and does not list the BU |
| `calculation_method_unsupported` | `calculation_methods` is non-empty and does not include the BU's costing method (`fifo`, `average`, `average_per_location`) |
| `run_disabled` | `allow_run = false` on a `list` template, for the interactive **Run** only (`ViewReportForUser`); forms and schedule runs ignore it |
| `export_disabled` | `allow_export = false` |

`GET /api/{bu}/reports/templates?actionable=true` (used only by `/report`) hides templates that have neither Run nor Export; the schedule form's report picker calls it without `actionable` so it sees everything. `GET /api/{bu}/reports/templates/:template_id` returns 200 or the same 403 (404 when missing/inactive). The FE maps `run_disabled` / `export_disabled` to the "action disabled" toast and every other reason to "unavailable for this business unit". A null `allow_run` (column not migrated) counts as on. See [schedule](/en/inventory/reporting-audit/schedule) § 1.2 for how scheduled runs treat a refused template.

### 1.6 The parameter dialog (template `dialog` XML)

Parsed in the browser (`routes/report/list/parse-report-dialog.ts`; the schedule form has its own parser, `routes/report/schedules/parse-schedule-dialog.ts`, which flattens `<Group>` and honours `Label=` but ignores layout).

| Element / attribute | Effect |
|---|---|
| `<Dialog Cols="n">` | Lays controls out in `n` columns (max 4, `MAX_COLS`); modal widens (`sm:max-w-3xl` / `sm:max-w-5xl`). `ColSpan` on a control spans columns |
| `<Group Label?>` | Author-defined box with optional heading; nested groups allowed; no automatic From/To pairing inside |
| `Label="…"` on a control | Wins over a preceding `<Label>`; empty value shows the control `Name` |
| `<Lookup Name DataSource|Items+Values Multi?>` | Picker; `Multi="true"` renders a checkbox group and submits comma-joined values. Option lists come from `GET /api/{bu}/reports/lookups?types=` and are re-fetched every time the dialog opens (`staleTime 0`) |
| `<Date Name Value>` | Date field |
| `<TextBox Name Value Type="Number" Min>` | Free text; `Type="Number"` accepts integers ≥ `Min` (default 1) and is required (Slow Moving: `Day`) |
| `<Note Text>` | Non-filter text under the fields; `@today` is replaced by today's date `dd/MM/yyyy` |
| `…From` / `…To` pairs | Rendered on one row and pre-filled so the range is never empty (`6e1ee12a`) |

Picker search: typing sends `GET …/reports/lookups?types=<source>&search=<text>&limit=50` (debounced 150 ms) so rows beyond the first 500 by code are reachable; the micro-report lookup default and maximum is **500 rows per type**, `limit` accepted 1-500, `search` is a case-insensitive match on code or name (not applied to `period`). Parameter memory: the values and picker labels of the last **Run** are kept in `localStorage` per BU + report for **30 minutes** (`carmen.report-params:<bu>:<report>`, `report-param-memory.ts`); expired or unreadable storage silently falls back to defaults. The report list header shows the template description under the name in list mode (`bbdfa238`) and clears the page number when searching from page 2+ (`e76637ce`).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Run a report on demand | `/report` → pick report → Run | `POST /api/{bu}/reports/viewer` — renders a viewer URL directly; **no `tb_report_job` row written**. Parameters come from the template `dialog` (§ 1.6, `report-param-dialog.tsx`); lookups from `GET .../reports/lookups`. Run is hidden when the template has `allow_run = false` |
| Download a report's data as CSV | `/report` → pick report → Export data | § 1.4; only for templates with an Export XML and `allow_export` |
| Print a document | Any document's Print action | `GET /api/{bu}/{documents}/{id}/print-viewer?template_id=` → viewer URL — same "no job row" behaviour |
| Email a PO / RFP with the PDF attached | PO / RFP detail → Send email | micro-business → `export-pdf-with-data` → attachment; activity `email_sent` |
| Choose which form prints each document type in this BU | `/system-admin/default-setting` → Print form | One dropdown per `report_group`; empty = the group's `is_default` form |
| Filter the report list | Search box + report-group filter, saved views | Server-side search; group filter over the current page |
| Add or change a print layout | Backstage admin (outside the inventory UI) | `POST/PUT api-system/report-templates` (`report_template.create/update`); exactly one `is_default` form per group |
| BU-scope a template | Edit template `allow_business_unit` / `deny_business_unit` | Null allow-list = all BUs |
| Schedule a recurring export | See [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) | Separate scheduler service |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| History screen shows nothing for a run I just did | Expected — no reachable path writes `tb_report_job` | Not a bug in the read path |
| Print returns "no default template for this document type" | No live `template_type = 'form'` row with `is_default = true` for that `report_group`, and the BU has not chosen one | Backstage admin sets a default; or pick a form in Default Setting |
| Print returns "template is not a valid form for this type" | `template_id` supplied points at a template of another `report_group` or a `list` template | Fix the BU print-form choice |
| Every print fails with 401 from micro-report | Missing/mismatched `x-internal-token` (`INTERNAL_RPC_SECRET`) between micro-business/gateway and micro-report | Ops: align the secret (`bb7ea9e61`) |
| Signature block empty on the printout | Template has no `signature_config` block for that slot, or the workflow stage resolved no signer | Check `signature_config.blocks` on the template and the document's workflow stages |
| Report data fails with "view not found" | `source_type` / `source_name` drift | Realign template binding with the DB object |
| Period picker empty in a report dialog | Lookup reads `tb_inventory_period` (renamed from `tb_period`, `cf4ea57`) — an old micro-report build still queries `tb_period` | Deploy micro-report ≥ 2026-09-16 |
| Template not visible in BU | `allow_business_unit` excludes; `deny_business_unit` includes; costing method not in `calculation_methods`; or both `allow_run` and `export` are off (`actionable=true` hides it) | Edit BU scoping / switches in Backstage |
| Toast "action disabled" / "unavailable for this business unit" | 403 `REPORT_TEMPLATE_UNAVAILABLE` with `reason` (§ 1.5) | Check the template's switches, BU lists and costing methods |
| Export returns 400 `export_not_configured` | Template has `allow_export` but no `export_xml`, or the XML does not parse | Add/fix Export XML in Backstage |

## 4. Edge Cases

- **On-demand runs and Print are synchronous viewer renders, not queued jobs.** No `tb_report_job` row, no history entry, no `expires_at` retention applies to them.
- **One default per group is a DB invariant now** (partial unique index), not an application check — the 2026-07-23 migration fails loudly if two active mappings existed for one document type.
- **Tenant connection is assembled from two Backstage tables.** micro-report resolves `tb_business_unit.db_schema` + `tb_database_pool` (`host`, `port`, `database`, `username`, `password` as `enc:v1` ciphertext) via a LEFT JOIN (`micro-report/db/db.go` `resolveTenantDBURL`, platform migration `20260813010000_database_pool_drop_db_connection`); a BU without a pool or schema is `ErrTenantNotProvisioned` (skippable), and a plaintext pool password is a hard error.
- **Signature images do not travel as data.** They are embedded into the template XML per render; captions are ordinary string columns.
- **Async job lifecycle exists but is unreached.** `queued → processing → (completed | failed | cancelled)` remains the model's contract; only `generate-async` advances it and nothing in the frontend calls it.

---

## 5. Data Model (Dev)

Source: **mixed** — tenant for the job/history table, Backstage schema for templates. Schedules are **not** a tenant table — see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) §5.

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

### 5.2 Schedules — not a tenant table

The tenant schema still declares `tb_report_schedule`, but no code references it. The real schedule store is the `Cronjob` table (`job_type = "report"`) in micro-cronjobs — [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) §5.

### 5.3 `tb_report_template` (Backstage)

| Field | Type | Description |
| --- | --- | --- |
| `name`, `description` | text | `@@unique([name, deleted_at])`. |
| `report_group` | `VarChar(100)` | Analytical group for lists; **the document type** for forms (`PR`, `PO`, `GRN`, `SR`, `CN`, `SI`, `SO`, `IA`, `PC`, `SC`, `RFP`, …). |
| `template_type` | text, default `list` | `form` (single-record document layout) or `list` (tabular report). Replaced `kind`. |
| `dialog`, `content` | text | FastReport dialog + layout XML. |
| `builder_key` | `VarChar(100)`, default `''` | Links to a Go `report.Definition` (e.g. `po-document`, `cn-document-landscape`). |
| `view_name` | text? | Legacy; prefer `source_type` + `source_name`. |
| `source_type` / `source_name` / `source_params` | `view`/`function`/`procedure`, name, `{ "params": [...] }` | Read by micro-data. |
| `orientation` | `portrait` / `landscape` | Replaces the old "Document Landscape" name suffix. |
| `signature_config` | JSONB `{ "blocks": [{ "key": "Sig1Name", "label": "Requestor", "required": true }, …] }` | Labelled signature slots on the print layout. |
| `is_standard` | bool, default `true` | Seeded template (`db/seed/report-templates/*.xml` + `_metadata.json`). |
| `is_default` | bool, default `false` | The form used when a BU has not chosen one for this group. Partial unique index `idx_report_template_default_per_group` on `(report_group) WHERE is_default AND template_type = 'form' AND deleted_at IS NULL` — exists only in migration SQL, inexpressible in Prisma. |
| `export_xml` | text? | Export XML mapping for CSV export (§ 1.4); `NULL` = no export. Migration `20261019120000_report_template_export_xml` |
| `allow_run`, `allow_export` | bool (defaults `true` / `false`) | Switch the Run and Export data buttons. Migration `20261019180000_report_template_allow_run_export` |
| `calculation_methods` | enum array | Costing methods the template supports; empty = all. Migration `20261008130000_report_template_calculation_methods` |
| `allow_business_unit` / `deny_business_unit` | JSONB? | BU scoping; null allow = all. |
| `is_active`, `doc_version`, audit columns | — | Standard. |

Seeded forms at HEAD include portrait + landscape documents for CN, GRN, IA, Invoice, PC, PO, PR, RFQ/RFP, SC, SI, SO, SR, and the Vendor Detail and Product Category forms. Seeded list reports (`db/seed/report-templates/*.content.xml`): Inventory Balance, Stock Card Detailed, Monthly Inventory Movement, Slow Moving, Receiving Detail, Receiving Detail Summary by Product, Receiving List, Purchase Analysis by Item, Purchase Request Detail / List, Purchase Order Detail / List, Credit Note Detail, Stock In / Stock Out Detail, Store Requisition Detail, Deviation by Item, Material Consumption, Menu Engineering, Recipe Card, EOP Checklist / Adjustment, Landed Cost (was Extra Cost Report, `8196f53`), Product List, Vendor List. Notable behaviour changes: Stock Card on `average` BUs shows `-` for Lot# and marks Avg Cost with `*` until the period is closed, and its AVG Grand Total is the sum of the group Total Amounts (`54d7e6c`, `f2c3db1`); the Stock Card seed passes the BU's `@calculation_method` into the function (`bffff67`); Monthly Inventory Movement shows Lot# on FIFO BUs and a Diff Amount column; Store Requisition Detail has a Movement Type (Issue/Transfer) parameter; report date ranges compare whole calendar days in Asia/Bangkok (`75b5fcd`); the `ReportFilters` struct gained `OrderBy`/`Sort`, `MovementType`, `DeliveryDateFrom/To`.

### 5.4 Print-form default resolution (replaces `tb_print_template_mapping`)

```
resolvePrintTemplate(documentType, templateId?):
  if templateId:
    row = tb_report_template where id = templateId and template_type = 'form'
          and report_group = documentType and deleted_at is null
    if none -> error "not a valid form for this type"
  else:
    row = tb_report_template where report_group = documentType
          and template_type = 'form' and is_default and deleted_at is null
    if none -> error "no default form for this type"
  return row
```

`templateId` is the BU's choice from the Default Setting screen (passed as `?template_id=` by `printDocument()`); the group's `is_default` form is the fallback.

## 6. Business Rules

- **One default print form per document type** — DB-enforced partial unique index on `tb_report_template` (2026-07-23); the BU choice never changes `is_default`, it only overrides at print time.
- **BU scoping.** Effective rule: *allow if in allow-list AND not in deny-list*; empty allow-list = all BUs.
- **Template type.** `list` for the analytical report list; `form` for the print pipeline. `GET /api/{bu}/reports/templates` returns only `template_type = 'list'` (`template_controller.go` `listFlat`); `GET /api-system/report-templates/forms` returns forms.
- **Source binding integrity.** `source_type` must match the DB object's nature; positional args declared in `source_params`.
- **On-demand runs and Print never queue a job.** Both call synchronous viewer endpoints — `tb_report_job`'s lifecycle is real but unreached by any frontend code path.
- **Internal calls carry `x-internal-token`.** micro-business → micro-report (print, PDF), gateway → micro-report (reports, templates), micro-report → micro-notification (`pkg/notify/client.go`, HTTP RPC `POST /rpc` with a `{pattern, data}` body; plural pattern fix `0b364cd`).

## 7. Cross-References

- All transactional modules — every "Print" button calls its own `print-viewer` endpoint; the form comes from the BU's Default Setting choice or the group default.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) — dashboard tiles pull from the [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) catalog, a separate mechanism from this template catalogue.
- [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) — recurring fires; not backed by a tenant table.
- [reporting-audit/history](/en/inventory/reporting-audit/history) — the `tb_report_job` read screen; confirmed structurally orphaned.
- [reporting-audit/notification](/en/inventory/reporting-audit/notification) — schedule fires dispatch a viewer-link notification per recipient.
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — `email_sent` on PO/RFP email; `print` / `export` not confirmed against the viewer path.
- [system-config/inventory-period](/en/inventory/system-config/period) — period lookups read `tb_inventory_period`.
- [master-data/business-unit](/en/inventory/master-data/business-unit) — BU scoping; tenant DB via `tb_database_pool`.

## 8. References

- **Prisma tenant:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_report_job`, `enum_report_job_status`, `enum_report_format`, `enum_report_category`; `tb_report_schedule` (dead).
- **Prisma Backstage:** `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` — `tb_report_template`; migrations `20260429110000_add_print_template_mapping` (created the mapping table), `20260723120000_print_form_default` (moved the default onto the template and dropped it), `20260813010000_database_pool_drop_db_connection`.
- **Gateway:** `../carmen-turborepo-backend/apps/backend-gateway/src/application/reports/reports.controller.ts` (`POST generate`, `GET types`, `GET templates`, `GET templates/:id`, `POST viewer`, `POST data`, `GET lookups`, `POST generate-async`, `GET jobs/:job_id`, `GET history`, schedules), `src/backstage/backstage_report-templates/backstage_report-templates.controller.ts` (`GET forms`, CRUD, `GET db-objects`), per-document controllers' `print-viewer` routes.
- **micro-business:** `../carmen-turborepo-backend/apps/micro-business/src/common/print-report.helper.ts` (template resolution, payload, signatures, viewer + PDF calls), `procurement/purchase-order/purchase-order.service.ts` (`printToReport`, email + `email_sent`).
- **micro-report:** `../micro-report/controller/report_controller.go` (`viewReport`, `viewReportWithData`, `exportPdfWithData`, `reportData`, `lookups`, `dbObjects`, `dialogParams`, `generateAsync`, `jobStatus`, `history`; `tb_inventory_period` SQL), `controller/template_controller.go` (`listFlat`), `service/render/viewer_client.go` (`View`, `ExportPDF`), `service/report_service.go` (`ExportReportWithExternalData`), `service/dataset/client.go` (`/api/datasets/execute`), `db/db.go` (`resolveTenantDBURL`), `middleware/internal_auth.go`, `pkg/notify/client.go`, `db/seed/report-templates/` (+ `_metadata.json`).
- **Frontend:** `../carmen-frontend/routes/report/` (`list/`, `schedules/`, `history/`, `shared/use-report.ts`), `lib/print-document.ts` (`DEDICATED_PRINT_ENDPOINTS`), `routes/system-admin/default-setting/use-report-form-templates.ts`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/documents-and-reports/report/*`, `platform/report-templates/GET-find-forms-…bru`, `platform/report-template/*`, `*/GET-print-to-report-*.bru`; archived `_archived/2026-07-29/platform/print-template-mapping/*` and `_archived/2026-07-29/documents-and-reports/report/GET-resolve-print-template-…bru`.
