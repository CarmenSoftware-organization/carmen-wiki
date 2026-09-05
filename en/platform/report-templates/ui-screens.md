---
title: Report Template — UI Screens
description: ReportTemplateManagement list (Status + Source Type + Template Type filters, CSV export) and ReportTemplateEdit 2-pane form (left — identity + source + BU scope; right — 3-tab CodeMirror Dialog XML / Content XML / Preview) — layout, filters, Browse-in-BU probe, sticky action bar, not-found gating, doc_version, persisted state.
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, report-templates, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Report Template — UI Screens

> **At a Glance**
> **Screens:** `ReportTemplateManagement` (list, `/report-templates`) &nbsp;·&nbsp; `ReportTemplateEdit` create (`/report-templates/new`) &nbsp;·&nbsp; `ReportTemplateEdit` view/edit (`/report-templates/:id/edit`) &nbsp;·&nbsp; **Edit layout:** 2-pane — left: identity + BU scope + data source cards (sticky); right: 3-tab CodeMirror — Dialog XML · Content XML · Preview &nbsp;·&nbsp; **Dialogs:** Browse in BU probe · Soft Delete confirm &nbsp;·&nbsp; **Access:** routes gated by `report_template.read` / `.create` / `.update`; in-page `<Can>` gates on Add Template, row Edit, row Delete, row/hero View History (`activity_log.read`, new), and the Edit toggle (see [Permissions](/en/platform/report-templates/permissions)) &nbsp;·&nbsp; **Persisted UI state:** 7 `localStorage` keys on the list page + 1 on the edit page &nbsp;·&nbsp; **Since 2026-07-23:** `template_type` (List/Form select, required) drives conditional fields — `is_standard` for list templates, `is_default` + a fixed `report_group` dropdown for form templates; not-found gating and `doc_version` optimistic locking added to the edit page

## 1. Overview

The Platform SPA follows the standard two-screen pattern for report template management: a list page (`ReportTemplateManagement`) with a server-side `DataTable`, a slide-over Filters Sheet, and two header action buttons; and an edit page (`ReportTemplateEdit`) that starts in read-only view mode and transitions to an editable form on demand. Both screens are registered under the `/report-templates` route prefix and are guarded by per-route `requiredPermission` keys — `report_template.read` on the list, `report_template.create` on create, `report_template.update` on edit (see [Permissions §2](/en/platform/report-templates/permissions)).

The edit page uses a 2-pane layout: a left column (fixed width, `minmax(320px, 380px)`, sticky while the right pane scrolls) stacks **three** Cards vertically — **Template Info**, **Business Unit Scope**, and **Data Source**. **Corrected:** a fourth "Metadata" card that used to sit between Business Unit Scope and Data Source no longer exists — commit `682652d` (2026-08-22) removed it in favour of an audit line rendered directly in the page's own `PageHeader` (§4.0). The right column fills the remaining width with a single Card whose header contains the 3-tab selector: **Dialog XML**, **Content XML**, and **Preview**. Each XML tab hosts a `XmlEditor` component wrapping CodeMirror. The Preview tab renders the `dialog` XML as a disabled form using `DialogPreview`. The XML structures accepted by each tab are documented in [XML Spec](/en/platform/report-templates/xml-spec); the `source_params` JSON shape and storage types for `allow_business_unit` / `deny_business_unit` are documented in [Data Model](/en/platform/report-templates/data-model).

## 2. `ReportTemplateManagement` — list page (`/report-templates`)

### 2.1 Layout

The page renders inside `Layout` with a two-row header: a title row ("Report Templates" / subtitle row) and an actions row containing **Export** and **Add Template** buttons. Below the action row sits a search-and-filters row: a debounced search `Input` on the left with a yellow highlight when a term is active, and a **Filters** Sheet trigger on the right (shows an active-filter count badge when any filter is set). Active filter chips appear as a strip below the search row when any filter is active; each chip has an inline remove button and a **Clear all** text link. The main content area is a `DataTable` in server-side mode with pagination and sort support.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet (`SheetContent side="right"`, `w-full sm:max-w-sm`). Three filter groups are wired (`ReportTemplateManagement.tsx`, the Sheet body):

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). Toggling a button appends or removes the value from `statusFilter`. The SPA serialises the selection as `is_active: boolean` inside the `advance` query object sent to `GET /api-system/report-templates`.
- **Source Type** — three toggle buttons: **view**, **function**, **procedure**. The SPA serialises the selection as `source_type` (a scalar when one value is picked, `{ in: [...] }` when more than one) inside `advance`. Multiple values may be toggled simultaneously.
- **Template Type** — two toggle buttons: **form**, **list** (added 2026-07-23 alongside the `template_type` column rename). Serialises the same way as Source Type (`template_type` scalar or `{ in: [...] }`).

There is no Standard/Custom filter group and no soft-deleted row toggle (unlike clusters). When any filter is active a **Clear All Filters** button appears at the bottom of the Sheet. The active filter count badge (`activeFilterCount`) increments once per filter group that has any active values, not per value — so the maximum shown is `3` (Status + Source Type + Template Type, `ReportTemplateManagement.tsx`).

### 2.3 Header actions

Two buttons appear in the header actions row, left to right:

- **Export** — client-side CSV export using the shared `generateCSV` / `downloadCSV` utilities (`ReportTemplateManagement.tsx`, `handleExport`). Exports the currently loaded page of rows with 9 columns: `Name` (`name`), `Description` (`description`), `Report Group` (`report_group`), `Standard` (`is_standard`), `Status` (`is_active`), `Created` (`created_at`), `Created By` (`created_by`), `Updated` (`updated_at`), `Updated By` (`updated_by`) — **not** `source_type`/`source_name`. The four audit columns are built via `auditCsvFields(normalizeAudit(t))` (§2.5) and always render an **absolute** ISO timestamp, never a relative one, so the exported file stays readable months later. File name: `report-templates-<YYYY-MM-DD>.csv` where the date is the export moment. The button is disabled while loading or when the table is empty. Not permission-gated — any `report_template.read` holder can export.
- **Add Template** — navigates to `/report-templates/new`. Wrapped in `<Can permission="report_template.create">` — hidden without that grant. **The empty-state Add Template button carries the identical gate** (`ReportTemplateManagement.tsx:529-536`, `addAction={<Can permission="report_template.create">...}`) — it is **not** ungated, correcting a pre-existing wiki error; see [Permissions §7](/en/platform/report-templates/permissions).

There is no Hard Delete option in the report-template header. The export is purely client-side — it operates on the in-memory `templates` array, not a separate backend endpoint.

### 2.4 Row actions

Each row has a `DropdownMenu` (⋯ icon button) with **three** items, each wrapped in its own `<Can>` gate (`ReportTemplateManagement.tsx:317-339`):

- **Edit** — navigates to `/report-templates/:id/edit`. Wrapped in `<Can permission="report_template.update">`.
- **View History** (new, cross-cutting Activity Trail feature) — sits between Edit and Delete. Wrapped in `<Can permission="activity_log.read" clusterId={PLATFORM_SCOPED_RECORD}>`; `onSelect` opens the shared `ActivityTrailSheet` for the row via `activityTrail.openFor(row.original.id)`. Recording started 2026-08-31 — a template created earlier shows an empty history. Same feature as [clusters](/en/platform/clusters/ui-screens)/[business-units](/en/platform/business-units/ui-screens)/[users](/en/platform/users/ui-screens)/[applications](/en/platform/applications/ui-screens).
- **Delete** — sets `deleteId` state; opens the Soft Delete confirm `ConfirmDialog` (§5.2). On confirm, calls `DELETE /api-system/report-templates/:id`. The SPA uses `reportTemplateService.delete(id)` with no hard-delete alternative exposed from the management UI. Wrapped in `<Can permission="report_template.delete">`.

For a `report_template.read`-only session, Edit and Delete are hidden; the dropdown renders only View History if `activity_log.read` is also held, otherwise it renders empty.

There is no Hard Delete row action. Hard deletion is not exposed from the Platform SPA for report templates.

### 2.5 Audit columns

The `DataTable` includes the following columns in order (`ReportTemplateManagement.tsx`, the `columns` array):

| Column header | Accessor / field | Notes |
|---|---|---|
| Name | `name` | Clickable link text (+ description as muted subtext below); navigates to `/report-templates/:id/edit` |
| Template Type | `template_type` | **Added 2026-07-23.** Outline `Badge`, capitalised, defaults to `list` when absent |
| Report Group | `report_group` | Outline `Badge`; when `template_type = 'form'` and `is_default`, a second filled "Default" badge renders alongside it |
| Standard | `is_standard` | `Standard` (default badge) or `Custom` (secondary badge) — shown regardless of `template_type`, though the field is only editable for list templates in the edit form |
| Status | `is_active` | `Active` (success badge) or `Inactive` (secondary badge) |
| Created | via `auditColumns<ReportTemplate>({ t })` | **Corrected — no longer a bespoke fixed-format renderer.** Renders `<AuditMeta variant="cell" actor={normalizeAudit(row).created} />`: relative time (e.g. "5mo ago") on the first line, actor name on the second, full absolute timestamp as a hover `title` tooltip |
| Updated | via `auditColumns<ReportTemplate>({ t })` | Same `AuditMeta variant="cell"` rendering, for `normalizeAudit(row).updated`. **Suppression rule corrected:** the cell is blank when the record has never been edited — decided by `everEdited` (an actor **name** is present, or the timestamp differs from `created` with no name), not by a plain `updated_at === created_at` comparison |
| Actions | — | `DropdownMenu` icon button; see §2.4 |

**Removed 2026-07-23:** the former "Source" column (`source_type` + `source_name` two-line cell) no longer exists in the list — `source_type`/`source_name` are edit-page-only fields now; the Template Type column took its place. There are no `deleted_at` / `deleted_by_name` columns — the list does not support a show-soft-deleted filter (unlike the clusters list). Default sort is `name:asc` (was `created_at:desc` before 2026-07-23 — see §6 for the persisted-key migration this forced).

`normalizeAudit()` (`../carmen-platform/src/utils/audit.ts`) reads the **nested** shape first and falls back to the **flat** shape: `fromNested(nested?.created) ?? fromFlat(record.created_at, record.created_by_name, record.created_by)`, same order for `updated`. This lets the same column definition work whether or not a given backend route has been migrated to the nested `audit.{created,updated}` response shape yet.

## 3. `ReportTemplateEdit` — create mode (`/report-templates/new`)

In create mode (`isNew = true`) the page title is "New Report Template" and the subtitle is "Create a new report template". The form is immediately editable — there is no Edit header button and no view mode. The same 2-pane layout renders as in edit mode, but the **Metadata** card is absent (it is only shown when `!isNew && !loading && (metadata.created_at || metadata.updated_at)` — `ReportTemplateEdit.tsx:743`).

Required fields at submit time (`ReportTemplateEdit.tsx` `handleSubmit`):

| Field | Required | Validation |
|---|---|---|
| `template_type` | Yes | **Added 2026-07-23.** Must be `list` or `form`; inline error if left at the blank placeholder option |
| `name` | Yes | Non-empty; inline error on blur and on submit |
| `report_group` | Yes | Non-empty; inline error on blur and on submit. For `template_type = 'form'` this is a `<select>` constrained to `FORM_REPORT_GROUPS`; for `list` it is a free-text input |
| `source_name` | Conditional | Required when `source_type` is `function` or `procedure`; optional for `view` |

All other fields (`description`, `builder_key`, `is_standard`, `is_default`, `is_active`, `allow_business_unit`, `deny_business_unit`, `dialog`, `content`, `source_params`) are optional at creation time. Default values from `initialFormData`: `template_type = ''` (blank placeholder, unless pre-filled — see below), `is_standard = true`, `is_default = false`, `is_active = true`, `source_type = 'view'`.

**Pre-filled create (added 2026-07-23):** navigating from the Form Groups screen's "+ Add" action passes `{ template_type: 'form', report_group: <group code> }` via router state, seeding the create form (`seedInitialFormData`) so the author doesn't have to re-pick the type/group. Direct visits to `/report-templates/new` (no state) get the plain blank defaults above.

The sticky action bar (§4.8) shows the **Create Template** label. On submit, calls `POST /api-system/report-templates`. On success, if the response carries an `id`, navigates to `/report-templates/:id/edit` with `{ replace: true }` so Back returns to the list rather than the create form. If no `id` is returned, navigates to `/report-templates`.

## 4. `ReportTemplateEdit` — view/edit mode (`/report-templates/:id/edit`)

The page starts in **view mode** (`editing = false`). The `PageHeader`'s `actions` row (rendered whenever `!isNew && !loading`, independent of `editing`) carries, left to right: a **View History** button gated on `<Can permission="activity_log.read" clusterId={PLATFORM_SCOPED_RECORD}>` (new, cross-cutting Activity Trail feature — see [Permissions §7](/en/platform/report-templates/permissions)), then either **Cancel** (while editing) or **Edit** (`<Pencil>` icon, wrapped in `<Can permission="report_template.update">` — a session without that grant sees a permanently read-only page; in practice the edit route's own `report_template.update` guard already blocks such sessions, so the in-page gate re-checks the same key). Clicking **Edit** saves the current `formData` to `savedFormData` and sets `editing = true`.

**Audit line (new, replaces the removed Metadata card — see §4.3):** the same `PageHeader` also takes an `audit={normalizeAudit(templateRecord)}` prop (only when `!isNew && !loading`), which renders one line under the subtitle: "Created `<relative>` by `<name>` · Updated `<relative>` by `<name>`" via the shared `AuditMeta variant="header"` component, each half omitted if inapplicable, full absolute timestamp as a hover tooltip.

The 2-pane grid uses `grid-cols-1 lg:grid-cols-[minmax(320px,380px)_1fr]` — the left column is fixed-width and `lg:sticky lg:top-4 lg:self-start` so it stays visible while the right pane scrolls.

### 4.0 Not-found gating and doc_version (both added 2026-07-23)

A bad or deleted `id` renders a dedicated not-found shell instead of the edit form: `PageHeader` with just a back link, a `SearchX`-icon `EmptyState` titled "Report template not found", and a "Back to report templates" button — mirrors the same pattern added to clusters/business-units/users/applications. `docVersion` is captured from the loaded record (`getDocVersion`) and sent back on every `PUT`; a version conflict shows the shared `notifyVersionConflict()` toast and re-fetches rather than silently overwriting.

Below the header (view mode only), a badge row shows: Active/Inactive, then either a Standard/Custom badge (list templates) or a Default/— badge (form templates, shown only when `is_default`), then the `report_group` value as an outline badge.

### 4.1 Left pane — Template Info card

Card title: "Template Info".

| Field | Input type | Required | Edit-mode notes |
|---|---|---|---|
| `template_type` | `<select>` (List / Form) | Yes | **Added 2026-07-23.** In view mode shown as an outline `Badge`. Changes which of `is_standard`/`is_default` and which `report_group` control (select vs. free text) render below |
| `name` | text `Input` | Yes | `required`, inline destructive error on blur and submit |
| `description` | `<textarea>` | No | 3 rows; auto-resize not used |
| `report_group` | `<select>` (form templates) or text `Input` (list templates) | Yes | For `template_type = 'form'`: a `<select>` constrained to `FORM_REPORT_GROUPS`, with the current value kept as an extra option if it's a legacy code outside that list. For `list`: a free-text input, unconstrained. In view mode both render as an outline `Badge` |
| `is_standard` | checkbox | — | Visible in edit mode only, and **only when `template_type ≠ 'form'`**. Defaults `true`. **Also forced `true` on submit, not just hidden:** `handleSubmit` sends `is_standard: isForm ? true : formData.is_standard` — even an existing form template loaded with `is_standard = false` is coerced to `true` the next time it is saved |
| `is_default` | checkbox ("Default for this report group") | — | **Added 2026-07-23.** Visible in edit mode only, and **only when `template_type = 'form'`**. A helper note below warns that saving a second default in the same group will fail server-side (the partial unique index) — unset the other one first |
| `is_active` | checkbox | — | Visible in edit mode only. Defaults `true` |

In view mode, `is_standard`/`is_default` and `is_active` are not rendered as form fields — they appear in the badge row above the form (§4.0) and as small labelled badges inside the Template Info card ("Kind"/"Group Default" + "Status"). In edit mode the lifecycle checkboxes render side-by-side in a `grid-cols-2` row inside the Template Info card.

**Renamed 2026-07-23:** the field previously called `kind` (`'report' | 'print'`, undocumented in the SPA form) is now `template_type` (`'list' | 'form'`) and **is** exposed as the first field in this card, required at submit — the earlier sync's claim that it was absent from the form is stale.

### 4.2 Left pane — Business Unit Scope card

Card title: "Business Unit Scope" (`ReportTemplateEdit.tsx:706`).

Two `ChipInput` fields:

| Field | Label | Placeholder |
|---|---|---|
| `allow_business_unit` | Allow | "Type BU code + Enter (blank = all)" |
| `deny_business_unit` | Deny | "Type BU code + Enter (blank = none)" |

Both inputs are disabled when `editing = false`. **Added 2026-07-23:** both are also force-disabled and show empty/placeholder values whenever `template_type = 'form'` (placeholders read "All business units (form template)" / "—") — form templates are not BU-scoped this way; the fields only do anything for `template_type = 'list'`. Each chip represents one BU code; pressing Enter after typing a code adds it; clicking the chip's remove button deletes it.

**Storage note:** the underlying Prisma columns `allow_business_unit` and `deny_business_unit` are `Json @db.JsonB` (see [Data Model §2.1](/en/platform/report-templates/data-model)). The SPA normalises the API response to a CSV string via a local `toCsv()` helper (`ReportTemplateEdit.tsx:213-217`) for `ChipInput` display. On save, the form sends the CSV string directly in the payload — the backend is responsible for parsing it back to the stored JSON shape. Testers verifying API round-trips should read the data-model page for the exact stored representation.

### 4.3 Metadata card — removed 2026-08-22

**Corrected:** there is no longer a separate "Metadata" card on this page. Commit `682652d` (2026-08-22, `refactor(audit): หน้า Edit และ Hero ที่คู่กันใช้ AuditMeta`) deleted the bespoke card — its four read-only fields (Created date/time, Created by, Updated date/time, Updated by, each hand-formatted `YYYY-MM-DD HH:mm`) and the `metadata.created_at || metadata.updated_at` presence check that gated it are both gone. The equivalent information now renders as a single audit line inside the page's own `PageHeader`, documented in §4.0 above — same underlying data (`normalizeAudit(templateRecord)`), same "hidden in create mode" behaviour (the `audit` prop is only passed when `!isNew`), but relative-time formatting instead of an absolute one, and positioned in the header rather than as a left-pane card between Business Unit Scope and Data Source. This is the same "hero absorbs the read-mode metadata" pattern documented on [users](/en/platform/users/ui-screens), [rbac](/en/platform/rbac/ui-screens), and [news](/en/platform/news/ui-screens).

### 4.4 Left pane — Data Source card

Card title: "Data Source" (`ReportTemplateEdit.tsx:764`).

**Source Type** (`source_type`): a `<select>` with three options in edit mode: `View`, `Function`, `Procedure` (values: `view`, `function`, `procedure`). In view mode renders as an outline `Badge`. Changing `source_type` updates the Source Name placeholder and determines whether `source_name` becomes required.

**Source Name** (`source_name`): text `Input` in edit mode. Required when `source_type` is `function` or `procedure`; optional for `view`. Placeholder text changes per type: `e.g. v_pr_summary` (view), `e.g. fn_pr_report` (function), `e.g. sp_pr_report` (procedure). Help text below: "Plain identifier only — no schema prefix, no quotes. Resolved against each tenant's schema at runtime." In view mode renders as `ReadOnlyText`.

**Browse in BU** (inline probe panel, edit mode only — `ReportTemplateEdit.tsx:818-897`): a dashed-border panel below the Source Name input. The author enters a BU code into a compact text input (`probe_bu`), clicks **Load**, and the SPA calls `reportTemplateService.listDbObjects(buCode)` → `GET /api-system/report-templates/db-objects?bu_code=<buCode>`. The response (`{ views, functions, procedures }` each as `Array<{ name, kind }>`) is stored in `dbObjects` state. A `<select>` dropdown appears listing all objects matching the current `source_type`; selecting one populates `source_name`. The last-used BU code is persisted to `localStorage` key `report_template_probe_bu` so it survives page reloads. If the chosen `source_type` has no objects in that BU, an italic message "No `<type>`s found in `<BU>`" is shown instead of the select.

**Source Parameters** (`source_params`): an editable table of `SourceParamRow` items. Columns: `Filter Field (ReportFilters)` (maps a named filter from the Dialog XML to a procedure/function argument), `PG Type` (PostgreSQL type string, e.g. `date`, `uuid`, `text`), `Nullable` (checkbox). An **+ Add Param** button appends a blank row; each row has a `×` remove button. In view mode the table renders read-only with monospace text. For `source_type = 'view'`, a hint reads "Views do not take parameters — filters apply via WHERE clause" and the Add Param button is hidden. For `source_type = 'procedure'`, an italic note explains: "Procedure must accept these positional args plus an INOUT refcursor at the end (default name `rs`). Filters are applied inside the procedure — executor will not add a WHERE clause."

**Builder Key** (`builder_key`): optional text `Input`; placeholder `e.g. pr-summary`. Intended for future report-builder integrations. In view mode renders as `ReadOnlyText`.

### 4.5 Right pane — Dialog XML tab

Tab trigger label: "Dialog XML" with a line-count badge (count of newlines in `formData.dialog`) and a red dot (`aria-label="Has errors"`) when `dialogValidation.valid = false`. **Corrected 2026-09-02 (`3b7cba0`):** the tab strip is now the shared `TabStrip` component (`count`/`hasError` props), not bespoke `Tabs`/`TabsTrigger` markup — same visual badge and dot, but the screen-reader label changed from "Invalid" to "Has errors" to match every other tab strip in the app.

Hosts a `XmlEditor` component with:
- `uploadAccept=".xml,.txt"` — file upload button in the editor toolbar accepts `.xml` and `.txt`
- `readOnly={!editing}` — editor is non-interactive in view mode
- `minHeight={360}`, `maxHeight={560}` — CodeMirror viewport constraints
- `onParseChange={setDialogValidation}` — live XML parse callback; invalid XML sets the red dot on the tab trigger

The Dialog XML structure defines the filter dialog shown to end users at report-run time. See [XML Spec §2](/en/platform/report-templates/xml-spec) for the schema.

### 4.6 Right pane — Content XML tab

Tab trigger label: "Content XML" with a line-count badge and a red dot when `contentValidation.valid = false`.

Hosts a `XmlEditor` component with:
- `uploadAccept=".frx,.xml,.txt"` — accepts `.frx` (legacy FastReport binary-less XML), `.xml`, and `.txt`. The `.frx` extension distinguishes this tab from the Dialog XML tab (which accepts only `.xml,.txt`). This supports migration of existing FastReport templates.
- `readOnly={!editing}`
- `minHeight={360}`, `maxHeight={560}`
- `onParseChange={setContentValidation}`

The Content XML carries the FastReport-compatible layout definition. See [XML Spec §3](/en/platform/report-templates/xml-spec) for the schema.

### 4.7 Right pane — Preview tab

Tab trigger label: "Preview" (no badge, no validation dot).

Renders `<DialogPreview xml={formData.dialog} />` — a disabled-form rendering of the Dialog XML. This lets the template author verify what filter controls end users will see when they run the report, without leaving the edit page. The preview reflects the current in-memory `formData.dialog` value, including unsaved edits.

### 4.8 Sticky action bar

Rendered when `editing = true` as a `fixed bottom-0 ... z-40` bar with a translucent backdrop (`bg-background/85 backdrop-blur-xl`), inset to the sidebar width (`md:left-16 lg:left-60`) (`ReportTemplateEdit.tsx:1122-1164`).

Left side: unsaved-changes indicator. When `hasChanges = true` (i.e. `editing` is true and current `formData !== savedFormData`), shows a pulsing amber dot + "Unsaved changes" text. When no changes have been made yet, shows "No changes" in muted foreground.

Right side, left to right:
- **Cancel** (outline button, shown only when `!isNew`) — calls `handleCancelEdit()`: restores `formData` from `savedFormData`, sets `editing = false`, clears `fieldErrors` and `error`. No API call.
- **Create Template** / **Save Changes** (primary button) — calls `formRef.current?.requestSubmit()`. Label is "Create Template" in create mode, "Save Changes" in edit mode. Disabled when saving or (in edit mode) when `!hasChanges`. Shows a `Loader2` spinner while `saving = true`.

**Keyboard shortcuts**: the `useGlobalShortcuts` hook wires Ctrl/Cmd+S to `formRef.current?.requestSubmit()` and plain Escape (no modifier) to `handleCancelEdit()` (`ReportTemplateEdit.tsx:181-188`).

**Unsaved-changes guard**: `useUnsavedChanges(hasChanges)` fires a browser `beforeunload` warning when the user attempts to navigate away or close the tab while `hasChanges = true` (`ReportTemplateEdit.tsx:172`).

## 5. Dialogs

### 5.1 Browse in BU probe

This is not a modal dialog — it is an **inline panel** inside the Data Source card's Source Name section, visible only in edit mode (§4.4). The panel uses a dashed border to distinguish it from the main form area.

Workflow:
1. Author types a BU code into the compact `probe_bu` input. The code is persisted immediately to `localStorage.setItem('report_template_probe_bu', value)` (`ReportTemplateEdit.tsx:829`).
2. Author clicks **Load**. The button shows "Loading…" while `loadingDbObjects = true`.
3. SPA calls `reportTemplateService.listDbObjects(buCode)` → `GET /api-system/report-templates/db-objects?bu_code=<buCode>`.
4. On success, a `<select>` renders the objects of the matching type (`views` / `functions` / `procedures` based on current `source_type`). The placeholder option shows the count: "— pick from N `<type>`s in `<BU>` —".
5. Selecting an object sets `formData.source_name` to that object's `name` value.
6. On error, a `toast.error` is shown and `dbObjects` is reset to `null`.

If `probeBuCode` is present on mount (restored from `localStorage`), `loadDbObjects` is called automatically during `useEffect` (`ReportTemplateEdit.tsx:166-169`).

### 5.2 Soft Delete confirm

Triggered by the **Delete** row action in `ReportTemplateManagement` (`ReportTemplateManagement.tsx:315-326`).

Uses the shared `ConfirmDialog` component — a simple Yes/No confirm, no typed confirmation required (`ReportTemplateManagement.tsx:552-560`). Properties:
- **Title:** "Delete Report Template"
- **Description:** "Are you sure you want to delete this report template? This action cannot be undone."
- **Confirm button label:** "Delete" (destructive variant)

On confirm, calls `reportTemplateService.delete(id)` → `DELETE /api-system/report-templates/:id`. On success, `fetchTemplates()` re-fetches the list. There is no hard-delete dialog; hard deletion is not exposed from the management UI.

## 6. Persisted UI state

The list page writes 7 keys to `localStorage`. The edit page writes 1 key (the Browse-in-BU probe BU code).

| Key | Stored type | Persists |
|---|---|---|
| `search_report_templates` | string | Current debounced search term |
| `page_report_templates` | number (string) | Current page number; reset to `1` on search or filter change |
| `perpage_report_templates` | number (string) | Rows per page |
| `sort_report_templates_v2` | string | Current sort column/direction (default `name:asc`). **Renamed from `sort_report_templates` on 2026-07-23** — the code comment explains this deliberately force-resets any user who had the old `created_at:desc` default persisted, since the new default is `name:asc` |
| `filters_report_templates` | JSON array | Active Status filter values (e.g. `["true"]`, `["false"]`, `[]`) |
| `filters_report_templates_source_type` | JSON array | Active Source Type filter values (e.g. `["view","function"]`, `[]`) |
| `filters_report_templates_template_type` | JSON array | **Added 2026-07-23.** Active Template Type filter values (e.g. `["form"]`, `["form","list"]`, `[]`) |
| `report_template_probe_bu` | string | Last-used BU code for the Browse-in-BU probe in the edit page |

Note: `filters_report_templates` stores `is_active` booleans as **string values** `"true"` / `"false"` (not native JSON booleans) because they originate from button click values. Readers querying this key directly should parse strings, not booleans.

There is no Standard/Custom filter and therefore no `filters_report_templates_standard` key. The `ReportTemplateEdit` page does not persist any state beyond `report_template_probe_bu`.

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References

- `../carmen-platform/SITEMAP.md` — route table for the three report-template routes; note it still shows the legacy `allowedRoles` lists — `src/App.tsx` is authoritative for the `requiredPermission` keys.
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` — list page: filters (Status + Source Type + Template Type), header actions (Export, Add Template behind `<Can permission="report_template.create">` on both the header and empty-state buttons), row actions (Edit / View History / Delete soft, behind `<Can>` gates), `auditColumns()`-based DataTable columns, 7 `localStorage` keys (**corrected** — an earlier sync undercounted this at 6).
- `../carmen-platform/src/pages/ReportTemplateEdit.tsx` — create/view/edit page: 2-pane layout (Template Info card — `template_type`/`is_standard`/`is_default` conditional on type — and Business Unit Scope card, ChipInput, `toCsv()` normalisation, disabled for form templates, plus Data Source card: source binding, Browse-in-BU probe, source params table, builder key; **no Metadata card since 2026-08-22**, replaced by a `PageHeader`-level audit line and View History button), not-found gating, `doc_version`, 3-tab `TabStrip` CodeMirror right pane, sticky action bar, `useUnsavedChanges` hook.
- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx` / `../carmen-platform/src/constants/reportGroups.ts` — the Form Groups screen and its fixed `report_group` list (see [report-templates landing](/en/platform/report-templates) §1).
- `../carmen-platform/src/services/reportTemplateService.ts` — API surface (paths pluralised 2026-06): `GET /api-system/report-templates`, `GET /api-system/report-templates/:id`, `POST /api-system/report-templates`, `PUT /api-system/report-templates/:id`, `DELETE /api-system/report-templates/:id`, `GET /api-system/report-templates/db-objects?bu_code=<buCode>` (`listDbObjects`).
- Cross-links: [report-templates](/en/platform/report-templates) (module landing), [business-units](/en/platform/business-units) (BU chip context and `cluster_id` FK), [Data Model](/en/platform/report-templates/data-model) (storage types for `allow_business_unit`, `deny_business_unit`, `source_params`; `template_type`/`is_default` fields), [Permissions](/en/platform/report-templates/permissions), [XML Spec](/en/platform/report-templates/xml-spec) (Dialog XML schema §2, Content XML schema §3), [print-template-mapping](/en/platform/print-template-mapping) (removed 2026-07-23/24 — historical page for what the Form Groups screen replaced).
