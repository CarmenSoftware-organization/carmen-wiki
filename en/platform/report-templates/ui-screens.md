---
title: Report Template — UI Screens
description: The report templates list (status/source/template-type/calculation-method filters, CSV export, JSON backup and import) and the two-pane edit form — EN/TH identity, source, BU and costing scope, a four-tab XML editor with a drag-and-drop Dialog layout editor, and a version-history sheet.
published: true
date: 2026-10-27T00:00:00.000Z
tags: book/platform, report-templates, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Report Template — UI Screens

> **At a Glance**
> **Screens:** `ReportTemplateManagement` (list, `/report-templates`) &nbsp;·&nbsp; `ReportTemplateEdit` create (`/report-templates/new`) &nbsp;·&nbsp; `ReportTemplateEdit` view/edit (`/report-templates/:id/edit`) &nbsp;·&nbsp; **Edit layout:** 2-pane — left: one card with Template Info · Business Unit Scope · Data Source sections; right (sticky below the top bar): 4-tab pane — Dialog XML · Content XML · Export XML · Preview (a drag-and-drop layout editor while editing) &nbsp;·&nbsp; **Dialogs and sheets:** Browse in BU probe · Soft Delete confirm · XML versions sheet (+ restore confirm) · Import dialog &nbsp;·&nbsp; **Access:** routes gated by `report_template.read` / `.create` / `.update`; in-page `<Can>` gates on Add Template, Import, Download backup, row Edit, row Delete, row/hero View History (`activity_log.read`), the Edit toggle and Restore (see [Permissions](/en/platform/report-templates/permissions)) &nbsp;·&nbsp; **Persisted UI state:** 8 `localStorage` keys on the list page + 1 on the edit page &nbsp;·&nbsp; **Since 2026-07-23:** `template_type` (List/Form select, required) drives conditional fields; not-found gating and `doc_version` optimistic locking on the edit page

![Report Template — UI Screens screen](/screenshots/platform/report-templates/ui-screens.png)

![Report Template — UI Screens form screen](/screenshots/platform/report-templates/ui-screens-form.png)

## 1. Overview

The Backstage SPA follows the standard two-screen pattern for report template management: a list page (`ReportTemplateManagement`) with a server-side `DataTable` (row selection on), a slide-over Filters Sheet, and four header action buttons; and an edit page (`ReportTemplateEdit`) that starts in read-only view mode and transitions to an editable form on demand. Both screens are registered under the `/report-templates` route prefix and are guarded by per-route `requiredPermission` keys — `report_template.read` on the list, `report_template.create` on create, `report_template.update` on edit (see [Permissions §2](/en/platform/report-templates/permissions)).

The edit page uses a 2-pane layout (`grid-cols-1 lg:grid-cols-[minmax(320px,380px)_1fr]`). The left column is **one Card with three sections** separated by rules — **Template Info**, **Business Unit Scope** (which also holds the costing-method checkboxes for list templates), and **Data Source**. It scrolls with the page: an earlier build pinned this column, but it was taller than the screen and never actually stuck, so the pin moved to the other side. The right column (`lg:sticky lg:top-20`) holds a single Card whose header is a `TabStrip` with four tabs — **Dialog XML**, **Content XML**, **Export XML** and **Preview** — and the XML editors are sized to fit the viewport (`calc(100vh - 21rem)` max height) so the code stays in view while the left form scrolls. Directly under the page title a **lineage strip** (`SourceLineage`) summarises how the report is assembled: `Dialog · N fields → View|Function|Procedure <source_name> → <builder_key>` (the last hop only when a builder key is set; field count is the number of non-`<Label>` children of `<Dialog>`, or just "Dialog" when the XML does not parse). The XML structures accepted by each tab are documented in [XML Spec](/en/platform/report-templates/xml-spec); the `source_params` JSON shape and storage types for `allow_business_unit` / `deny_business_unit` are documented in [Data Model](/en/platform/report-templates/data-model).

## 2. `ReportTemplateManagement` — list page (`/report-templates`)

### 2.1 Layout

The page renders inside `Layout` with a two-row header: a title row ("Report Templates" / subtitle row) and an actions row containing the **Import**, **Backup all**, **Export** and **Add Template** buttons (§2.3). Below the action row sits a search-and-filters row: a debounced search `Input` on the left with a yellow highlight when a term is active, and a **Filters** Sheet trigger on the right (shows an active-filter count badge when any filter is set). Active filter chips appear as a strip below the search row when any filter is active; each chip has an inline remove button and a **Clear all** text link. The main content area is a `DataTable` in server-side mode with pagination and sort support.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet (`SheetContent side="right"`, `w-full sm:max-w-sm`). Four filter groups are wired (`ReportTemplateManagement.tsx`, the Sheet body):

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). Toggling a button appends or removes the value from `statusFilter`. The SPA serialises the selection as `is_active: boolean` inside the `advance` query object sent to `GET /api-system/report-templates`.
- **Source Type** — three toggle buttons: **view**, **function**, **procedure**. The SPA serialises the selection as `source_type` (a scalar when one value is picked, `{ in: [...] }` when more than one) inside `advance`. Multiple values may be toggled simultaneously.
- **Template Type** — two toggle buttons: **form**, **list** (added 2026-07-23 alongside the `template_type` column rename). Serialises the same way as Source Type (`template_type` scalar or `{ in: [...] }`).
- **Calculation Method** — four toggle buttons: **FIFO**, **Average**, **Average per location**, **Restricted only**. Picking methods matches a template that is tagged with any picked method **or** is untagged (an untagged template supports every method); **Restricted only** matches templates that carry at least one tag; both together mean "tagged and carrying a picked method" (`buildCalculationMethodWhere`, `pages/reportTemplates/calculationMethods.tsx`). The stored value is validated against the known method names on read, because one bad enum value makes Prisma answer 500 for the whole list.

There is no Standard/Custom filter group and no soft-deleted row toggle (unlike clusters). When any filter is active a **Clear All Filters** button appears at the bottom of the Sheet. The active filter count badge (`activeFilterCount`) increments once per filter group that has any active values, not per value — so the maximum shown is `4` (Status + Source Type + Template Type + Calculation Method).

### 2.3 Header actions

Four buttons appear in the header actions row, left to right:

- **Import** (`Upload` icon) — opens the Import dialog (§5.4). Wrapped in `<Can permission="report_template.create">`.
- **Backup all** — downloads every template matching the current search/filters as one JSON file (§5.5): it pages the list in batches of 100 to collect ids, then fetches each template in full (4 requests in flight) because the list endpoint does not return the XML. Shows `Listing templates…` and then `Backing up done/total`. Wrapped in `<Can permission="report_template.read">`; disabled while loading, while a backup is running, or when the table is empty.
- **Export** — client-side CSV export using the shared `generateCSV` / `downloadCSV` utilities (`handleExport`). Exports the currently loaded page of rows with 12 columns: `Name` (`name`), `Description`, `Name (TH)`, `Description (TH)`, `Report Group`, `Calculation Method` (labels joined with ", ", or "All methods" when untagged), `Standard`, `Status`, then the four audit columns built via `auditCsvFields(normalizeAudit(t))` (§2.5) — always an **absolute** ISO timestamp — **not** `source_type`/`source_name`. File name: `report-templates-<YYYY-MM-DD>.csv`. Disabled while loading or when the table is empty. Not permission-gated — any `report_template.read` holder can export.
- **Add Template** — navigates to `/report-templates/new`. Wrapped in `<Can permission="report_template.create">` — hidden without that grant. **The empty-state Add Template button carries the identical gate** (`addAction={<Can permission="report_template.create">...}`) — it is **not** ungated, correcting a pre-existing wiki error; see [Permissions §7](/en/platform/report-templates/permissions).

There is no Hard Delete option in the report-template header. The CSV export is purely client-side — it operates on the in-memory `templates` array, not a separate backend endpoint.

### 2.4 Row actions and selection

The first column is a selection checkbox (`enableRowSelection`, ids are template ids). Selecting rows shows a bar above the table — `N selected`, **Download backup (N)** and **Clear**. The selection is current-page only: it is discarded whenever the page, page size, search, sort or filters change.

Each row has a `DropdownMenu` (⋯ icon button) with **four** items, each wrapped in its own `<Can>` gate:

- **Edit** — navigates to `/report-templates/:id/edit`. Wrapped in `<Can permission="report_template.update">`.
- **View History** (cross-cutting Activity Trail feature) — wrapped in `<Can permission="activity_log.read" clusterId={BACKSTAGE_SCOPED_RECORD}>`; `onSelect` opens the shared `ActivityTrailSheet` for the row via `activityTrail.openFor(row.original.id)`. Recording started 2026-08-31 — a template created earlier shows an empty history. Same feature as [clusters](/en/platform/clusters/ui-screens)/[business-units](/en/platform/business-units/ui-screens)/[users](/en/platform/users/ui-screens)/[applications](/en/platform/applications/ui-screens). Not to be confused with the XML versions sheet (§5.3), which records content snapshots rather than audit events.
- **Download backup** — `<Can permission="report_template.read">`; fetches that one template in full and downloads it as a JSON backup (§5.5).
- **Delete** — sets `deleteId` state; opens the Soft Delete confirm `ConfirmDialog` (§5.2). On confirm, calls `DELETE /api-system/report-templates/:id`. Wrapped in `<Can permission="report_template.delete">`.

For a `report_template.read`-only session, Edit and Delete are hidden; the menu still offers **Download backup** (and View History if `activity_log.read` is also held).

There is no Hard Delete row action. Hard deletion is not exposed from the Backstage SPA for report templates.

### 2.5 Audit columns

The `DataTable` includes a leading selection-checkbox column and then the following columns in order (`ReportTemplateManagement.tsx`, the `columns` array):

| Column header | Accessor / field | Notes |
|---|---|---|
| Name | `name` | Clickable link text in the UI language (`pickLocalized` over `name_i18n`, falling back to `name`), with the other language as muted subtext and the description below; navigates to `/report-templates/:id/edit` |
| Template Type | `template_type` | **Added 2026-07-23.** Outline `Badge`, capitalised, defaults to `list` when absent |
| Report Group | `report_group` | Outline `Badge`; when `template_type = 'form'` and `is_default`, a second filled "Default" badge renders alongside it |
| Calculation Method | `calculation_methods` | **Added 2026-10.** Outline badges for the tagged methods, or a muted "All methods" when untagged; not sortable |
| Standard | `is_standard` | `Standard` (default badge) or `Custom` (secondary badge) — shown regardless of `template_type`, though the field is only editable for list templates in the edit form |
| Status | `is_active` | `Active` (success badge) or `Inactive` (secondary badge) |
| Created | via `auditColumns<ReportTemplate>({ t })` | **Corrected — no longer a bespoke fixed-format renderer.** Renders `<AuditMeta variant="cell" actor={normalizeAudit(row).created} />`: relative time (e.g. "5mo ago") on the first line, actor name on the second, full absolute timestamp as a hover `title` tooltip |
| Updated | via `auditColumns<ReportTemplate>({ t })` | Same `AuditMeta variant="cell"` rendering, for `normalizeAudit(row).updated`. **Suppression rule corrected:** the cell is blank when the record has never been edited — decided by `everEdited` (an actor **name** is present, or the timestamp differs from `created` with no name), not by a plain `updated_at === created_at` comparison |
| Actions | — | `DropdownMenu` icon button; see §2.4 |

**Removed 2026-07-23:** the former "Source" column (`source_type` + `source_name` two-line cell) no longer exists in the list — `source_type`/`source_name` are edit-page-only fields now; the Template Type column took its place. There are no `deleted_at` / `deleted_by_name` columns — the list does not support a show-soft-deleted filter (unlike the clusters list). Default sort is `name:asc` (was `created_at:desc` before 2026-07-23 — see §6 for the persisted-key migration this forced). The stored per-page size is read through `readStoredPerpage('perpage_report_templates', 10)` — integers 1 to 100 only, because the gateway answers `400 INVALID_PERPAGE` for anything else.

`normalizeAudit()` (`../carmen-backstage/src/utils/audit.ts`) reads the **nested** shape first and falls back to the **flat** shape: `fromNested(nested?.created) ?? fromFlat(record.created_at, record.created_by_name, record.created_by)`, same order for `updated`. This lets the same column definition work whether or not a given backend route has been migrated to the nested `audit.{created,updated}` response shape yet.

## 3. `ReportTemplateEdit` — create mode (`/report-templates/new`)

In create mode (`isNew = true`) the page title is "New Report Template" and the subtitle is "Create a new report template". The form is immediately editable — there is no Edit header button, no lineage strip, no audit line and no header actions (Versions, backup and View History all need a saved record). The same 2-pane layout renders as in edit mode.

Required fields at submit time (`handleSubmit`):

| Field | Required | Validation |
|---|---|---|
| `template_type` | Yes | **Added 2026-07-23.** Must be `list` or `form`; inline error if left at the blank placeholder option |
| `name` (EN) | Yes | Non-empty after trim; inline error on blur and on submit |
| `report_group` | Yes | Non-empty; inline error on blur and on submit. For `template_type = 'form'` this is a `<select>` constrained to `FORM_REPORT_GROUPS`; for `list` it is a free-text input |
| `source_name` | Conditional | Required when `source_type` is `function` or `procedure`; optional for `view`. The backend additionally rejects (`COMMON_VALIDATION_FAILED`) anything that is not a bare identifier (`^[A-Za-z_][A-Za-z0-9_]*$`, at most 63 characters) |

All other fields (`name` TH, `description` EN/TH, `builder_key`, `is_standard`, `is_default`, `is_active`, `allow_run`, `allow_export`, `allow_business_unit`, `deny_business_unit`, `calculation_methods`, `dialog`, `content`, `export_xml`, `source_params`) are optional at creation time. Default values from `initialFormData`: `template_type = ''` (blank placeholder, unless pre-filled — see below), `is_standard = true`, `is_default = false`, `is_active = true`, `allow_run = true`, `allow_export = false`, `source_type = 'view'`.

**Pre-filled create (added 2026-07-23):** navigating from the Form Groups screen's "+ Add" action passes `{ template_type: 'form', report_group: <group code> }` via router state, seeding the create form (`seedInitialFormData`) so the author doesn't have to re-pick the type/group. Direct visits to `/report-templates/new` (no state) get the plain blank defaults above.

The sticky action bar (§4.9) shows the **Create Template** label. On submit, calls `POST /api-system/report-templates`. On success, if the response carries an `id`, navigates to `/report-templates/:id/edit` with `{ replace: true }` so Back returns to the list rather than the create form. If no `id` is returned, navigates to `/report-templates`. The backend answers `REPORT_TEMPLATE_NAME_ALREADY_EXISTS` for a name (EN) already used by a live template.

## 4. `ReportTemplateEdit` — view/edit mode (`/report-templates/:id/edit`)

The page starts in **view mode** (`editing = false`). The `PageHeader`'s `actions` row (rendered once the record has loaded, independent of `editing`) carries, left to right: a **View History** button gated on `<Can permission="activity_log.read" clusterId={BACKSTAGE_SCOPED_RECORD}>` (Activity Trail, see [Permissions §7](/en/platform/report-templates/permissions)); the **XML versions** button (§5.3, `<Can permission="report_template.read">`, hidden altogether when the versions endpoint answers 404); **Download backup** (§5.5, `<Can permission="report_template.read">`); then either **Cancel** (while editing) or **Edit** (`<Pencil>` icon, wrapped in `<Can permission="report_template.update">` — a session without that grant sees a permanently read-only page; in practice the edit route's own `report_template.update` guard already blocks such sessions, so the in-page gate re-checks the same key). Clicking **Edit** saves the current `formData` to `savedFormData` and sets `editing = true`. Next to the title a `v<doc_version>` badge shows the optimistic-lock version, which is also the version number of the latest row in the versions sheet.

**Audit line:** the `PageHeader` also takes an `audit={normalizeAudit(templateRecord)}` prop (only when `!isNew && !loading`), which renders one line under the subtitle ("Created `<relative>` by `<name>` · Updated `<relative>` by `<name>`") via the shared `AuditMeta variant="header"` component, each half omitted if inapplicable, full absolute timestamp as a hover tooltip. In edit mode the subtitle slot holds the lineage strip (§1) rather than plain text.

### 4.0 Not-found gating and doc_version (both added 2026-07-23)

A bad or deleted `id` renders a dedicated not-found shell instead of the edit form: `PageHeader` with just a back link, a `SearchX`-icon `EmptyState` titled "Report template not found", and a "Back to report templates" button — mirrors the same pattern added to clusters/business-units/users/applications. `docVersion` is captured from the loaded record (`getDocVersion`) and sent back on every `PUT`; a version conflict shows the shared `notifyVersionConflict()` toast and re-fetches rather than silently overwriting.

Below the header, a badge row shows: Active/Inactive, then either a Standard/Custom badge (list templates) or a Default badge (form templates, shown only when `is_default`), then the `report_group` value as an outline badge. On first load only, if the Dialog XML is blank but the Content XML is not (typical for Form templates) the page opens on the Content tab instead of an empty Dialog editor; later reloads (after save or restore) never move the active tab.

### 4.1 Left card — Template Info section

Section title: "Template Info".

| Field | Input type | Required | Edit-mode notes |
|---|---|---|---|
| `template_type` | `<select>` (List / Form) | Yes | In view mode shown as an outline `Badge`. Changes which of `is_standard`/`is_default`/run-export switches and which `report_group` control (select vs. free text) render below |
| `name` (EN) | text `Input` | Yes | Label "Name (EN)"; `required`, inline destructive error on blur and submit. Loaded from the plain `name` column first (outside writers update `name`/`description` only), falling back to `name_i18n.en` |
| `name_th` | text `Input`, max 255 | No | **Added 2026-10.** Stored as `name_i18n.th` |
| `description` (EN) | `<textarea>` | No | 3 rows |
| `description_th` | `<textarea>` | No | **Added 2026-10.** Stored as `description_i18n.th` |
| `report_group` | `<select>` (form templates) or text `Input` (list templates) | Yes | Edit mode only (view mode shows it as a badge under the header). For `template_type = 'form'`: constrained to `FORM_REPORT_GROUPS`, with the current value kept as an extra option if it is a legacy code outside that list. For `list`: free text |
| `is_standard` | checkbox | — | Edit mode only, **only when `template_type ≠ 'form'`**. Defaults `true`. **Also forced `true` on submit for form templates, not just hidden:** `is_standard: isForm ? true : formData.is_standard` |
| `is_default` | checkbox ("Default for this report group") | — | Edit mode only, **only when `template_type = 'form'`**. A note warns that saving a second default in the same group fails server-side (the partial unique index) — unset the other one first. Sent only for form templates (omitted for list so the stored value is preserved) |
| `is_active` | checkbox | — | Edit mode only. Defaults `true` |
| `allow_run` | checkbox ("Run report") | — | **Added 2026-10.** Edit mode, **list templates only**. Hint: "Show the Run Report button in Report List." |
| `allow_export` | checkbox ("Export data") | — | **Added 2026-10.** Edit mode, **list templates only**. Hint: "Show the Export data button. Needs an Export XML." Shows a warning when on with an empty Export XML ("the button stays hidden"); with both switches off a note says the template is hidden from Report List |

For form templates `allow_run`/`allow_export` are not sent at all; the list-type switches are enforced by micro-report, see [Report Templates](/en/platform/report-templates) §3. In view mode the lifecycle flags are not form fields — they are the badges in the header row.

### 4.2 Left card — Business Unit Scope section

Section title: "Business Unit Scope".

Two `ChipInput` fields:

| Field | Label | Placeholder |
|---|---|---|
| `allow_business_unit` | Allow | "Type BU code + Enter (blank = all)" |
| `deny_business_unit` | Deny | "Type BU code + Enter (blank = none)" |

Both inputs are disabled when `editing = false`. Both are also force-disabled with empty values whenever `template_type = 'form'` (placeholders read "All business units (form template)" / "—") — form templates are not BU-scoped this way, and `handleSubmit` sends `''` for both. In **view mode** the pair collapses into one read-only line, "All business units", when neither list has entries (or the form-template placeholder for forms). Each chip represents one BU code; pressing Enter after typing a code adds it; clicking the chip's remove button deletes it.

**Calculation method** (new, **list templates only**): below the chips, a row of three checkboxes — FIFO, Average, Average per location — with the hint "Leave all unchecked if the report works with every costing method. Business units using an unchecked method will not see or run it." View mode shows the tagged methods as badges or \"All methods\". The array is always kept in canonical order (`fifo`, `average`, `average_per_location`) so ticking a box off and on again does not count as a change. For form templates the field is hidden and `calculation_methods: []` is sent.

**Storage note:** the underlying Prisma columns `allow_business_unit` and `deny_business_unit` are `Json @db.JsonB` (see [Data Model §2.1](/en/platform/report-templates/data-model)). The SPA normalises the API response to a CSV string via a local `toCsv()` helper (inside `fetchTemplate`) for `ChipInput` display. On save, the form sends the CSV string directly in the payload and the service stores it as received, so rows saved from this page hold a JSON string while seeded rows may hold an array; micro-report parses both. Testers verifying API round-trips should read the data-model page for the exact stored representation.

### 4.3 Metadata card — removed 2026-08-22

**Corrected:** there is no separate "Metadata" card on this page. Commit `682652d94c3ee5e243f22459d13ee410bb92f804` (2026-08-22, `refactor(audit): หน้า Edit และ Hero ที่คู่กันใช้ AuditMeta`) deleted the bespoke card — its four read-only fields and the presence check that gated it are both gone. The equivalent information now renders as the single audit line inside the page's own `PageHeader`, documented in §4 above — same underlying data (`normalizeAudit(templateRecord)`), same "hidden in create mode" behaviour, but relative-time formatting instead of an absolute one. This is the same "hero absorbs the read-mode metadata" pattern documented on [users](/en/platform/users/ui-screens), [rbac](/en/platform/rbac/ui-screens), and [news](/en/platform/news/ui-screens).

### 4.4 Left card — Data Source section

Section title: "Data Source".

**Source Type** (`source_type`): a `<select>` with three options in edit mode: `View`, `Function`, `Procedure` (values: `view`, `function`, `procedure`). In view mode renders as an outline `Badge`. Changing `source_type` updates the Source Name placeholder and determines whether `source_name` becomes required.

**Source Name** (`source_name`): text `Input` in edit mode. Required when `source_type` is `function` or `procedure`; optional for `view`. Placeholder text changes per type: `e.g. v_pr_summary` (view), `e.g. fn_pr_report` (function), `e.g. sp_pr_report` (procedure). Help text below: "Plain identifier only — no schema prefix, no quotes. Resolved against each tenant's schema at runtime." In view mode renders as `ReadOnlyField`. On save a blank value is sent as `null` (so an existing `source_name` can be cleared; `undefined` would leave it untouched).

**Browse in BU** (inline probe panel, edit mode only): a dashed-border panel below the Source Name input. The author enters a BU code into a compact text input (`probe_bu`), clicks **Load**, and the SPA calls `reportTemplateService.listDbObjects(buCode)` → `GET /api-system/report-templates/db-objects?bu_code=<buCode>`, which the gateway guards with `sql_workbench.read` (§5.1). The response (`{ views, functions, procedures }` each as `Array<{ name, kind }>`) is stored in `dbObjects` state. A `<select>` dropdown appears listing all objects matching the current `source_type`; selecting one populates `source_name`. The last-used BU code is persisted to `localStorage` key `report_template_probe_bu` so it survives page reloads. If the chosen `source_type` has no objects in that BU, an italic message "No `<type>`s found in `<BU>`" is shown instead of the select. A failed load shows a `FetchErrorState` with a Retry button.

**Source Parameters** (`source_params`): an editable table of `SourceParamRow` items. Columns: `Filter Field (ReportFilters)`, `PG Type` (PostgreSQL type string, e.g. `date`, `uuid`, `text`), `Nullable` (checkbox). An **+ Add Param** button appends a blank row (hidden for views); each row has a `×` remove button. In view mode the table renders read-only with monospace text, and the whole section is hidden for `view` sources (views take no parameters — filters apply via WHERE clause). For `source_type = 'procedure'`, an italic note explains: "Procedure must accept these positional args plus an INOUT refcursor at the end (default name `rs`). Filters are applied inside the procedure — executor will not add a WHERE clause."

**Builder Key** (`builder_key`): optional text `Input`; placeholder `e.g. pr-summary`. In view mode renders as `ReadOnlyField`.

### 4.5 Right pane — Dialog XML tab

Tab label "Dialog XML" with a line-count badge and a red dot (`aria-label="Has errors"`) when the XML does not parse. The tab strip is the shared `TabStrip` component (`count`/`hasError` props). Hosts an `XmlEditor` (CodeMirror) with `uploadAccept=".xml,.txt"`, `readOnly={!editing}`, `minHeight={360}`, `maxHeight="calc(100vh - 21rem)"` (the editor scrolls inside that box on both axes — long lines no longer wrap since 2026-10, so the XML shows exactly as it is stored), `onParseChange={setDialogValidation}`. An empty editor shows a neutral "empty XML" status instead of the green "Valid XML" check. The Dialog XML defines the filter dialog shown to end users at report-run time; see [XML Spec §2](/en/platform/report-templates/xml-spec).

### 4.6 Right pane — Content XML tab

Tab label "Content XML" with a line-count badge and a red dot when invalid. Same `XmlEditor` configuration except `uploadAccept=".frx,.xml,.txt"` (the `.frx` extension supports migration of existing FastReport templates) and `onParseChange={setContentValidation}`. See [XML Spec §3](/en/platform/report-templates/xml-spec).

### 4.7 Right pane — Export XML tab

**Added 2026-10.** Tab label "Export XML" with line count and error dot. An `XmlEditor` bound to `export_xml` (`uploadAccept=".xml,.txt"`, download name `export.xml`). Below the editor, non-blocking warnings from `lintExportXml(export_xml, content)` appear in an amber list: root element must be `<Export>`, at least one `<Column>`, each column needs a `Header` and exactly one of `Field`/`Value`/`Expression`, `Sort` needs a `Field` and a `Desc` of `true`/`false`, and any `Field`, `Sort Field` or `[bracketed]` expression reference that is not a column declared in the Content XML's `<TableDataSource>` (computed fields `GroupBy`, `BuName`, `CalculationMethod` are exempt) produces "… is not a column in Content XML — the cell will be empty". Saving is never blocked by these warnings. A blank editor is saved as `null`. See [XML Spec §4](/en/platform/report-templates/xml-spec).

### 4.8 Right pane — Preview tab and the Dialog layout editor

Tab label "Preview" (no badge, no dot). The tab body is capped to the viewport height and scrolls on its own.

- **View mode** (or a viewport narrower than 768px): `<DialogPreview xml={formData.dialog} />` renders the Dialog XML as a disabled form on a `Cols`-wide grid (1 to 4 columns, with a badge showing the effective count), with a header showing the field count, per-tag counts and a warning count. Parser warnings (invalid or clamped `Cols`/`ColSpan`, nested groups flattened, empty groups, `ColSpan` on a `<Label>`, unknown elements, a label with no control or a control with no label) are listed above the grid. An empty Dialog shows an empty state, not an error; a missing `<Dialog>` root or unparseable XML shows a red "Preview unavailable" box. Two extra notices appear when the XML uses `<Group>` or a `Label=` attribute on a control, reminding the author that the inventory build must already support them (see [XML Spec](/en/platform/report-templates/xml-spec) §2). On a narrow screen in edit mode a line says to open the tab on a wider screen to arrange the layout.
- **Edit mode on a wide screen:** the same tab is the **Dialog layout editor** (`DialogLayoutEditor`, `@dnd-kit`). The author can: pick **Columns** 1 to 4; widen/narrow a cell with the ColSpan stepper; drag a cell by its handle to reorder it or to move it into or out of a `<Group>` (pointer-first drop targets, an \"end of dialog\" drop zone, keyboard dragging with Space/Enter and arrow keys, localized screen-reader announcements; a rejected drop shows a toast, e.g. a group cannot go inside another group, and a range that uses a hidden \"to\" label cannot go into a group); tick cells and **Group N cells** / **Ungroup**; **Add field** with Date, Lookup, Date range (From / To) or Lookup range (From / To) — inserted after the focused cell or inside the focused group, with the smallest `Name` number that keeps every name unique; and delete a cell or group with an **Undo** toast (the undo refuses with \"the dialog changed since\" if the XML moved on). Clicking a cell focuses it and opens the **property panel** beside the canvas (or below it on narrower editors): Label, Name (letters, digits and `_`, not starting with a digit, unique), default value (Date accepts `@today`), data source (with a known-sources suggestion list) or a **Fixed list** of shown-text/value rows (a `~` in a value is rejected because it is the list separator), Multi-select, ColSpan, range From/To labels, and a group's Heading. Invalid panel input blocks moving to another cell until it is fixed or Esc restores the previous value. Every change is written straight into `formData.dialog`, so it flows through the normal unsaved-changes and save path; the Dialog XML tab shows the resulting XML. While a drag is in progress, Esc cancels the drag and does not trigger the page's Cancel shortcut.

### 4.9 Sticky action bar

Rendered when `editing = true` as a `fixed bottom-0 ... z-40` bar with a translucent backdrop, inset to the sidebar width (`md:left-16 lg:left-60`).

Left side: unsaved-changes indicator. When `hasChanges = true` (i.e. `editing` is true and current `formData !== savedFormData`), shows a pulsing amber dot + "Unsaved changes" text. When no changes have been made yet, shows "No changes" in muted foreground.

Right side, left to right:
- **Cancel** (outline button, shown only when `!isNew`) — calls `handleCancelEdit()`: restores `formData` from `savedFormData`, sets `editing = false`, clears `fieldErrors` and `error`. No API call.
- **Create Template** / **Save Changes** (primary button) — calls `formRef.current?.requestSubmit()`. Label is "Create Template" in create mode, "Save Changes" in edit mode. Disabled when saving or (in edit mode) when `!hasChanges`. Shows a `Loader2` spinner while `saving = true`.

**Keyboard shortcuts**: the `useGlobalShortcuts` hook wires Ctrl/Cmd+S to `formRef.current?.requestSubmit()` and plain Escape (no modifier) to `handleCancelEdit()` (ignored while a layout-editor drag is active).

**Unsaved-changes guard**: `useUnsavedChanges(hasChanges)` fires a browser `beforeunload` warning when the user attempts to navigate away or close the tab while `hasChanges = true`.

## 5. Dialogs and sheets

### 5.1 Browse in BU probe

This is not a modal dialog — it is an **inline panel** inside the Data Source section's Source Name block, visible only in edit mode (§4.4). The panel uses a dashed border to distinguish it from the main form area.

Workflow:
1. Author types a BU code into the compact `probe_bu` input. The code is persisted immediately to `localStorage.setItem('report_template_probe_bu', value)`.
2. Author clicks **Load**. The button shows "Loading…" while `loadingDbObjects = true`.
3. SPA calls `reportTemplateService.listDbObjects(buCode)` → `GET /api-system/report-templates/db-objects?bu_code=<buCode>`. **Server-side this route is guarded by `sql_workbench.read`** (`@RequireBackstagePermission('sql_workbench.read')`, `backstage_report-templates.controller.ts:130`), not by a `report_template.*` key: an author with `report_template.update` but no SQL Workbench grant gets the error toast and the retry state, and has to type `source_name` by hand.
4. On success, a `<select>` renders the objects of the matching type (`views` / `functions` / `procedures` based on current `source_type`). The placeholder option shows the count: "— pick from N `<type>`s in `<BU>` —".
5. Selecting an object sets `formData.source_name` to that object's `name` value.
6. On error, a `toast.error` is shown, `dbObjects` is reset to `null`, and a `FetchErrorState` with a retry button appears in the panel.

If a probe BU code was restored from `localStorage` on mount, `loadDbObjects` is called automatically.

### 5.2 Soft Delete confirm

Triggered by the **Delete** row action in `ReportTemplateManagement`. Uses the shared `ConfirmDialog` component — a simple Yes/No confirm, no typed confirmation required. Properties:
- **Title:** "Delete Report Template"
- **Description:** "Are you sure you want to delete this report template? This action cannot be undone."
- **Confirm button label:** "Delete" (destructive variant)

On confirm, calls `reportTemplateService.delete(id)` → `DELETE /api-system/report-templates/:id`. On success, `fetchTemplates()` re-fetches the list. The delete is a soft delete and does not write a version row; there is no hard-delete dialog.

### 5.3 XML versions sheet

**Added 2026-10** (backend commits `0aba9ec75`, `3468a5bc7`; SPA `ReportTemplateVersionsSheet`). The **XML versions** button on the edit-page header (`<Can permission="report_template.read">`) opens a right-hand sheet titled "Version history" ("Every save creates a version. Expand one to compare it with the current template."). The hook probes `GET /api-system/report-templates/:id/versions` once on mount and hides the button entirely if the backend answers 404; it reloads the list each time the sheet opens.

- **List:** one row per version, newest first: `v<n>`, a change badge (Created / Updated / Imported / `Restored from v<m>`), a `Current` badge on the row equal to the page's `doc_version`, and a compact actor line (relative time · name). Empty state: "No versions yet — versions are recorded from the next save."
- **Expanded row** (loads `GET .../versions/:version_no` on first expand, cached per version): a **Changed fields** list of `field: old → new` for the scalar fields that differ from the *current saved* record (name, name.th, description, description.th, report_group, template_type, is_active, is_standard, builder_key, source_type, source_name, source_params, orientation, allow/deny BU, and — only when the old snapshot has them — calculation_methods, allow_run, allow_export), or "Same metadata as current"; then a `TabStrip` for Dialog / Content / Export XML (a count shows the line-count difference when that XML changed) over an XML diff view of the version against the current record.
- **Download this version** — saves that snapshot as a one-template JSON backup (§5.5). **Restore this version** — `<Can permission="report_template.update">`, hidden on the current version and when the page has no `doc_version`; disabled with the tooltip "Save or cancel your edits first" while the page is in edit mode. It opens a confirm ("This creates v`<next>` from the content of v`<n>`. The default-form flag is not changed.") and calls `POST .../versions/:version_no/restore` with `{ doc_version }`. A stale `doc_version` surfaces the shared version-conflict toast and reloads; success toasts "Restored v`<n>`", re-fetches the template and reloads the list.

Each save from the form, every restore and every import adds a version, and so does each partial `PUT` from the Form Groups "set default" flow.

### 5.4 Import dialog

**Added 2026-10** (`ReportTemplateImportDialog`). Opened from the list header **Import** button (`report_template.create`). Choose a `.json` backup (limit 10 MB). The file is parsed locally (`parseBackup`): it must have `format = "carmen.report-template-backup"`, a `format_version` not newer than 1, and at least one template; otherwise a toast names the problem (not valid JSON / not a backup file / from a newer version / empty). The dialog then loads all existing template names (pages of 100) and shows a preview table — Name (EN, with TH beneath), Group, Type, Status, Action:

- **New** (name not found) — action Create.
- **Name exists** (a live template has the same EN name) — action Skip by default; with `report_template.update` the author can switch the row to Overwrite, or press **Overwrite all**. Without `.update` the row stays Skip.
- **Invalid** — red problem lines: missing name, missing report group, missing dialog/content XML, dialog or content XML not well-formed, unknown template type, name repeated in the same file. Invalid rows are skipped.

**Import N** runs the rows one at a time (so version numbers read in order and the default-form unique index is never hit), showing `Importing done/total`. Create sends `POST` with `is_default: false` (an imported form never takes over a group's default); Overwrite re-reads the current row and sends `PUT` carrying the row's current `is_default` and `doc_version`. The payload is built from the known backup fields only — `id`, `version`, `doc_version`, audit and delete fields in the file are ignored — `view_name` is dropped, `change_type: "import"` is added (so the new version row is labelled Imported), `name_i18n.en` is forced equal to `name`, and `source_params` / `signature_config` stored as `{}` by the micro-report seeder are normalised to `{ params: [] }` / `{ blocks: [] }`. The dialog cannot be closed while a check or import is running; the final toast reads "Created … · overwritten … · skipped … · failed …", and the list refreshes if anything succeeded.

### 5.5 JSON backup files

Backups are written by `buildBackup` (`utils/reportTemplateBackup.ts`): `{ format: "carmen.report-template-backup", format_version: 1, exported_at, source: { api_base_url, app_version }, templates: [...] }`. Each template carries `id`, `version` (its `doc_version`) and these fields: `name`, `name_i18n`, `description`, `description_i18n`, `report_group`, `template_type`, `dialog`, `content`, `export_xml`, `builder_key`, `view_name`, `source_type`, `source_name`, `source_params`, `orientation`, `signature_config`, `is_standard`, `is_default`, `allow_run`, `allow_export`, `is_active`, `allow_business_unit`, `deny_business_unit`, `calculation_methods` (the same list as the backend's version snapshot). File names: `report-template_<slug>_v<version>_<date>.json` for one template, `report-templates_<count>_<date>.json` for several. The edit-page button exports the **saved** record, not unsaved form edits.

## 6. Persisted UI state

The list page writes 8 keys to `localStorage`. The edit page writes 1 key (the Browse-in-BU probe BU code).

| Key | Stored type | Persists |
|---|---|---|
| `search_report_templates` | string | Current debounced search term |
| `page_report_templates` | number (string) | Current page number; reset to `1` on search or filter change |
| `perpage_report_templates` | number (string) | Rows per page; read back through `readStoredPerpage` (integers 1 to 100, else 10) |
| `sort_report_templates_v2` | string | Current sort column/direction (default `name:asc`). **Renamed from `sort_report_templates` on 2026-07-23** — the code comment explains this deliberately force-resets any user who had the old `created_at:desc` default persisted, since the new default is `name:asc` |
| `filters_report_templates` | JSON array | Active Status filter values (e.g. `["true"]`, `["false"]`, `[]`) |
| `filters_report_templates_source_type` | JSON array | Active Source Type filter values (e.g. `["view","function"]`, `[]`) |
| `filters_report_templates_template_type` | JSON array | Active Template Type filter values (e.g. `["form"]`, `["form","list"]`, `[]`) |
| `filters_report_templates_calculation_method` | JSON array | **Added 2026-10.** Active Calculation Method filter values (`fifo`, `average`, `average_per_location`, `restricted`); unknown values are dropped on read |
| `report_template_probe_bu` | string | Last-used BU code for the Browse-in-BU probe in the edit page |

Note: `filters_report_templates` stores `is_active` booleans as **string values** `"true"` / `"false"` (not native JSON booleans) because they originate from button click values. Readers querying this key directly should parse strings, not booleans.

There is no Standard/Custom filter and therefore no `filters_report_templates_standard` key. The `ReportTemplateEdit` page does not persist any state beyond `report_template_probe_bu`.

## 7. Screenshots

Captured under `assets/screenshots/platform/report-templates/` (`ui-screens.png` for the list, `ui-screens-form.png` for the edit form, embedded at the top of this page); not recaptured in the 2026-10-27 re-sync, so they predate the layout described in §4.

## 8. References

- `../carmen-backstage/SITEMAP.md` — route table for the three report-template routes; note it still shows the legacy `allowedRoles` lists — `src/App.tsx` is authoritative for the `requiredPermission` keys.
- `../carmen-backstage/src/pages/ReportTemplateManagement.tsx` — list page: filters (Status + Source Type + Template Type + Calculation Method), header actions (Import, Backup all, Export, Add Template), row selection and actions (Edit / View History / Download backup / Delete, behind `<Can>` gates), `auditColumns()`-based DataTable columns, 8 `localStorage` keys.
- `../carmen-backstage/src/pages/ReportTemplateEdit.tsx` — create/view/edit page: 2-pane layout (one left Card with Template Info / Business Unit Scope / Data Source sections), lineage strip, header actions (View History, XML versions, Download backup, Edit), not-found gating, `doc_version`, 4-tab `TabStrip` right pane, sticky action bar, `useUnsavedChanges`.
- `../carmen-backstage/src/pages/reportTemplates/{ReportTemplateVersionsSheet,ReportTemplateImportDialog,SourceLineage,calculationMethods,useReportTemplateVersions}.ts(x)`; `../carmen-backstage/src/utils/{reportTemplateBackup,exportXml,dialogXml}.ts`; `../carmen-backstage/src/components/DialogPreview.tsx` and `src/components/dialogPreview/{DialogLayoutEditor,PropertyPanel,SortableCell,CellView,CellToolbar,panelInputs,warningText}.ts(x)`.
- `../carmen-backstage/src/pages/ReportFormGroupManagement.tsx` / `../carmen-backstage/src/constants/reportGroups.ts` — the Form Groups screen and its fixed `report_group` list (see [report-templates landing](/en/platform/report-templates) §1).
- `../carmen-backstage/src/services/reportTemplateService.ts` — API surface: `GET /api-system/report-templates`, `GET .../:id`, `POST`, `PUT .../:id`, `DELETE .../:id`, `GET .../db-objects?bu_code=<buCode>` (`listDbObjects`), `GET .../:id/versions`, `GET .../:id/versions/:version_no`, `POST .../:id/versions/:version_no/restore`.
- Cross-links: [report-templates](/en/platform/report-templates) (module landing), [business-units](/en/platform/business-units) (BU chip context), [Data Model](/en/platform/report-templates/data-model) (storage types for `allow_business_unit`, `deny_business_unit`, `source_params`; `template_type`/`is_default` fields; version table), [Permissions](/en/platform/report-templates/permissions), [XML Spec](/en/platform/report-templates/xml-spec) (Dialog XML §2, Content XML §3, Export XML §4), print-template-mapping — removed from the product 2026-07-24 (carmen-backstage commit `de11377`), the module whose grouped-card list the Form Groups screen replaced.
