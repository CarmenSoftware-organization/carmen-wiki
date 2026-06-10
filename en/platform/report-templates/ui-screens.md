---
title: Report Template — UI Screens
description: ReportTemplateManagement list (Status + Source Type filters, CSV export) and ReportTemplateEdit 2-pane form (left — identity + source + BU scope; right — 3-tab CodeMirror Dialog XML / Content XML / Preview) — layout, filters, Browse-in-BU probe, sticky action bar, persisted state.
published: true
date: 2026-06-10T14:15:00.000Z
tags: book/platform, report-templates, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Report Template — UI Screens

> **At a Glance**
> **Screens:** `ReportTemplateManagement` (list, `/report-templates`) &nbsp;·&nbsp; `ReportTemplateEdit` create (`/report-templates/new`) &nbsp;·&nbsp; `ReportTemplateEdit` view/edit (`/report-templates/:id/edit`) &nbsp;·&nbsp; **Edit layout:** 2-pane — left: identity + BU scope + data source cards (sticky); right: 3-tab CodeMirror — Dialog XML · Content XML · Preview &nbsp;·&nbsp; **Dialogs:** Browse in BU probe · Soft Delete confirm &nbsp;·&nbsp; **Access:** routes gated by `report_template.read` / `.create` / `.update`; in-page `<Can>` gates on Add Template, row Edit, row Delete, and the Edit toggle (see [Permissions](./permissions.md)) &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys on the list page + 1 on the edit page

## 1. Overview

The Platform SPA follows the standard two-screen pattern for report template management: a list page (`ReportTemplateManagement`) with a server-side `DataTable`, a slide-over Filters Sheet, and two header action buttons; and an edit page (`ReportTemplateEdit`) that starts in read-only view mode and transitions to an editable form on demand. Both screens are registered under the `/report-templates` route prefix and are guarded by per-route `requiredPermission` keys — `report_template.read` on the list, `report_template.create` on create, `report_template.update` on edit (see [Permissions §2](./permissions.md)).

The edit page uses a 2-pane layout: a left column (fixed width, `minmax(320px, 380px)`, sticky while the right pane scrolls) stacks four Cards vertically — **Template Info**, **Business Unit Scope**, **Metadata** (view-mode only), and **Data Source**. The right column fills the remaining width with a single Card whose header contains the 3-tab selector: **Dialog XML**, **Content XML**, and **Preview**. Each XML tab hosts a `XmlEditor` component wrapping CodeMirror. The Preview tab renders the `dialog` XML as a disabled form using `DialogPreview`. The XML structures accepted by each tab are documented in [XML Spec](./xml-spec.md); the `source_params` JSON shape and storage types for `allow_business_unit` / `deny_business_unit` are documented in [Data Model](./data-model.md).

## 2. `ReportTemplateManagement` — list page (`/report-templates`)

### 2.1 Layout

The page renders inside `Layout` with a two-row header: a title row ("Report Templates" / subtitle row) and an actions row containing **Export** and **Add Template** buttons. Below the action row sits a search-and-filters row: a debounced search `Input` on the left with a yellow highlight when a term is active, and a **Filters** Sheet trigger on the right (shows an active-filter count badge when any filter is set). Active filter chips appear as a strip below the search row when any filter is active; each chip has an inline remove button and a **Clear all** text link. The main content area is a `DataTable` in server-side mode with pagination and sort support.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet (`SheetContent side="right"`, `w-full sm:max-w-sm`). Two filter groups are wired (`ReportTemplateManagement.tsx:373-428`):

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). Toggling a button appends or removes the value from `statusFilter`. The SPA serialises the selection as `is_active: boolean` inside the `advance` query object sent to `GET /api-system/report-templates`.
- **Source Type** — three toggle buttons: **View**, **Function**, **Procedure** (values: `view`, `function`, `procedure`). The SPA serialises the selection as `source_type: { in: [...] }` inside `advance` when any value is selected. Multiple values may be toggled simultaneously.

There is no Standard/Custom filter group and no soft-deleted row toggle (unlike clusters). When any filter is active a **Clear All Filters** button appears at the bottom of the Sheet. The active filter count badge (`activeFilterCount`) increments once per filter group that has any active values, not per value — so the maximum shown is `2` (`ReportTemplateManagement.tsx:157`).

### 2.3 Header actions

Two buttons appear in the header actions row, left to right:

- **Export** — client-side CSV export using the shared `generateCSV` / `downloadCSV` utilities (`ReportTemplateManagement.tsx:181-191`). Exports the currently loaded page of rows with columns: `name`, `description`, `report_group`, `source_type`, `source_name`, `Standard` (`is_standard`), `Status` (`is_active`). File name: `report-templates-<YYYY-MM-DD>.csv` where the date is the export moment. The button is disabled while loading or when the table is empty. Not permission-gated — any `report_template.read` holder can export.
- **Add Template** — navigates to `/report-templates/new`. Wrapped in `<Can permission="report_template.create">` — hidden without that grant. (The empty-state Add Template button is ungated; the route guard on `/report-templates/new` catches — see [Permissions §7](./permissions.md).)

There is no Hard Delete option in the report-template header. The export is purely client-side — it operates on the in-memory `templates` array, not a separate backend endpoint.

### 2.4 Row actions

Each row has a `DropdownMenu` (⋯ icon button) with two items, each wrapped in its own `<Can>` gate (`ReportTemplateManagement.tsx:304-315`):

- **Edit** — navigates to `/report-templates/:id/edit`. Wrapped in `<Can permission="report_template.update">`.
- **Delete** — sets `deleteId` state; opens the Soft Delete confirm `ConfirmDialog` (§5.2). On confirm, calls `DELETE /api-system/report-templates/:id`. The SPA uses `reportTemplateService.delete(id)` with no hard-delete alternative exposed from the management UI. Wrapped in `<Can permission="report_template.delete">`.

For a `report_template.read`-only session both items are hidden and the dropdown renders empty.

There is no Hard Delete row action. Hard deletion is not exposed from the Platform SPA for report templates.

### 2.5 Audit columns

The `DataTable` includes the following columns in order (`ReportTemplateManagement.tsx:194-315`):

| Column header | Accessor / field | Notes |
|---|---|---|
| Name | `name` | Clickable link text; navigates to `/report-templates/:id/edit` |
| Description | `description` | Truncated at `max-w-[200px]`; muted foreground text |
| Report Group | `report_group` | Rendered as an outline `Badge` |
| Source | `source_type` + `source_name` | Two-line cell: type badge (variant `default` = function, `secondary` = procedure, `outline` = view) + monospace `source_name` below |
| Standard | `is_standard` | `Standard` (default badge) or `Custom` (secondary badge) |
| Status | `is_active` | `Active` (success badge) or `Inactive` (secondary badge) |
| Created | `created_at` | Formatted `YYYY-MM-DD HH:mm:ss` in browser local time |
| Updated | `updated_at` | Same format; suppressed (renders `null`) when `updated_at === created_at` |
| Actions | — | `DropdownMenu` icon button; see §2.4 |

There are no `deleted_at` / `deleted_by_name` columns — the list does not support a show-soft-deleted filter (unlike the clusters list).

## 3. `ReportTemplateEdit` — create mode (`/report-templates/new`)

In create mode (`isNew = true`) the page title is "New Report Template" and the subtitle is "Create a new report template". The form is immediately editable — there is no Edit header button and no view mode. The same 2-pane layout renders as in edit mode, but the **Metadata** card is absent (it is only shown when `!isNew && !loading && (metadata.created_at || metadata.updated_at)` — `ReportTemplateEdit.tsx:536`).

Required fields at submit time (`ReportTemplateEdit.tsx:259-268`):

| Field | Required | Validation |
|---|---|---|
| `name` | Yes | Non-empty; inline error on blur and on submit |
| `report_group` | Yes | Non-empty; inline error on blur and on submit |
| `source_name` | Conditional | Required when `source_type` is `function` or `procedure`; optional for `view` |

All other fields (`description`, `builder_key`, `is_standard`, `is_active`, `allow_business_unit`, `deny_business_unit`, `dialog`, `content`, `source_params`) are optional at creation time. Default values from `initialFormData`: `is_standard = true`, `is_active = true`, `source_type = 'view'`.

The sticky action bar (§4.8) shows the **Create Template** label. On submit, calls `POST /api-system/report-templates`. On success, if the response carries an `id`, navigates to `/report-templates/:id/edit` with `{ replace: true }` so Back returns to the list rather than the create form. If no `id` is returned, navigates to `/report-templates`.

## 4. `ReportTemplateEdit` — view/edit mode (`/report-templates/:id/edit`)

The page starts in **view mode** (`editing = false`). An **Edit** button appears at the top right of the header (`<Pencil>` icon), wrapped in `<Can permission="report_template.update">` — a session without that grant sees a permanently read-only page (in practice the edit route's own `report_template.update` guard already blocks such sessions; the in-page gate re-checks the same key). Clicking **Edit** saves the current `formData` to `savedFormData` and sets `editing = true`. The Edit button is replaced by a **Cancel** button in the header while editing is active.

The 2-pane grid uses `grid-cols-1 lg:grid-cols-[minmax(320px,380px)_1fr]` — the left column is fixed-width and `lg:sticky lg:top-4 lg:self-start` so it stays visible while the right pane scrolls.

### 4.1 Left pane — Template Info card

Card title: "Template Info" (`ReportTemplateEdit.tsx:381`).

| Field | Input type | Required | Edit-mode notes |
|---|---|---|---|
| `name` | text `Input` | Yes | `required`, inline destructive error on blur and submit |
| `description` | `<textarea>` | No | 3 rows; auto-resize not used |
| `report_group` | text `Input` | Yes | Inline error; in view mode shown as an outline `Badge` |
| `is_standard` | checkbox | — | Visible in edit mode only (`ReportTemplateEdit.tsx:468-480`). Defaults `true`. |
| `is_active` | checkbox | — | Visible in edit mode only (`ReportTemplateEdit.tsx:480-490`). Defaults `true`. |

In view mode, `is_standard` and `is_active` are not rendered as fields — they appear as header badges only (`ReportTemplateEdit.tsx:337-343`). In edit mode they render as side-by-side checkboxes in a `grid-cols-2` row inside the Template Info card.

The `kind` field (`'report' | 'print'` in `ReportTemplate` service type — `reportTemplateService.ts:22`) is **not exposed** in the edit form. It exists on the API type but the SPA form does not display or mutate it.

### 4.2 Left pane — Business Unit Scope card

Card title: "Business Unit Scope" (`ReportTemplateEdit.tsx:498`).

Two `ChipInput` fields:

| Field | Label | Placeholder |
|---|---|---|
| `allow_business_unit` | Allow | "Type BU code + Enter (blank = all)" |
| `deny_business_unit` | Deny | "Type BU code + Enter (blank = none)" |

Both inputs are disabled when `editing = false`. Each chip represents one BU code; pressing Enter after typing a code adds it; clicking the chip's remove button deletes it.

**Storage note:** the underlying Prisma columns `allow_business_unit` and `deny_business_unit` are `Json @db.JsonB` (see [Data Model §2.1](./data-model.md)). The SPA normalises the API response to a CSV string via a local `toCsv()` helper (`ReportTemplateEdit.tsx:183-186`) for `ChipInput` display. On save, the form sends the CSV string directly in the payload — the backend is responsible for parsing it back to the stored JSON shape. Testers verifying API round-trips should read the data-model page for the exact stored representation.

### 4.3 Left pane — Metadata card

Shown only in view/edit mode, only when at least one of `created_at` or `updated_at` is non-null (`ReportTemplateEdit.tsx:536`). Card title: "Metadata".

Displays four read-only fields: Created date/time (`fmtDateTime`), Created by (`created_by_name`), Updated date/time, Updated by (`updated_by_name`). All timestamps are formatted `YYYY-MM-DD HH:mm` in browser local time.

The Metadata card is absent in create mode and absent while loading. It appears between the Business Unit Scope card and the Data Source card when conditions are met.

### 4.4 Left pane — Data Source card

Card title: "Data Source" (`ReportTemplateEdit.tsx:560`).

**Source Type** (`source_type`): a `<select>` with three options in edit mode: `View`, `Function`, `Procedure` (values: `view`, `function`, `procedure`). In view mode renders as an outline `Badge`. Changing `source_type` updates the Source Name placeholder and determines whether `source_name` becomes required.

**Source Name** (`source_name`): text `Input` in edit mode. Required when `source_type` is `function` or `procedure`; optional for `view`. Placeholder text changes per type: `e.g. v_pr_summary` (view), `e.g. fn_pr_report` (function), `e.g. sp_pr_report` (procedure). Help text below: "Plain identifier only — no schema prefix, no quotes. Resolved against each tenant's schema at runtime." In view mode renders as `ReadOnlyText`.

**Browse in BU** (inline probe panel, edit mode only — `ReportTemplateEdit.tsx:610-676`): a dashed-border panel below the Source Name input. The author enters a BU code into a compact text input (`probe_bu`), clicks **Load**, and the SPA calls `reportTemplateService.listDbObjects(buCode)` → `GET /api-system/report-templates/db-objects?bu_code=<buCode>`. The response (`{ views, functions, procedures }` each as `Array<{ name, kind }>`) is stored in `dbObjects` state. A `<select>` dropdown appears listing all objects matching the current `source_type`; selecting one populates `source_name`. The last-used BU code is persisted to `localStorage` key `report_template_probe_bu` so it survives page reloads. If the chosen `source_type` has no objects in that BU, an italic message "No `<type>`s found in `<BU>`" is shown instead of the select.

**Source Parameters** (`source_params`): an editable table of `SourceParamRow` items. Columns: `Filter Field (ReportFilters)` (maps a named filter from the Dialog XML to a procedure/function argument), `PG Type` (PostgreSQL type string, e.g. `date`, `uuid`, `text`), `Nullable` (checkbox). An **+ Add Param** button appends a blank row; each row has a `×` remove button. In view mode the table renders read-only with monospace text. For `source_type = 'view'`, a hint reads "Views do not take parameters — filters apply via WHERE clause" and the Add Param button is hidden. For `source_type = 'procedure'`, an italic note explains: "Procedure must accept these positional args plus an INOUT refcursor at the end (default name `rs`). Filters are applied inside the procedure — executor will not add a WHERE clause."

**Builder Key** (`builder_key`): optional text `Input`; placeholder `e.g. pr-summary`. Intended for future report-builder integrations. In view mode renders as `ReadOnlyText`.

### 4.5 Right pane — Dialog XML tab

Tab trigger label: "Dialog XML" with a line-count badge (count of newlines in `formData.dialog`) and a red dot (`aria-label="Invalid"`) when `dialogValidation.valid = false` (`ReportTemplateEdit.tsx:832-845`).

Hosts a `XmlEditor` component with:
- `uploadAccept=".xml,.txt"` — file upload button in the editor toolbar accepts `.xml` and `.txt`
- `readOnly={!editing}` — editor is non-interactive in view mode
- `minHeight={360}`, `maxHeight={560}` — CodeMirror viewport constraints
- `onParseChange={setDialogValidation}` — live XML parse callback; invalid XML sets the red dot on the tab trigger

The Dialog XML structure defines the filter dialog shown to end users at report-run time. See [XML Spec §2](./xml-spec.md) for the schema.

### 4.6 Right pane — Content XML tab

Tab trigger label: "Content XML" with a line-count badge and a red dot when `contentValidation.valid = false`.

Hosts a `XmlEditor` component with:
- `uploadAccept=".frx,.xml,.txt"` — accepts `.frx` (legacy FastReport binary-less XML), `.xml`, and `.txt`. The `.frx` extension distinguishes this tab from the Dialog XML tab (which accepts only `.xml,.txt`). This supports migration of existing FastReport templates.
- `readOnly={!editing}`
- `minHeight={360}`, `maxHeight={560}`
- `onParseChange={setContentValidation}`

The Content XML carries the FastReport-compatible layout definition. See [XML Spec §3](./xml-spec.md) for the schema.

### 4.7 Right pane — Preview tab

Tab trigger label: "Preview" (no badge, no validation dot).

Renders `<DialogPreview xml={formData.dialog} />` — a disabled-form rendering of the Dialog XML. This lets the template author verify what filter controls end users will see when they run the report, without leaving the edit page. The preview reflects the current in-memory `formData.dialog` value, including unsaved edits.

### 4.8 Sticky action bar

Rendered when `editing = true` as a `fixed bottom-0 ... z-40` bar with a translucent backdrop (`bg-background/85 backdrop-blur-xl`), inset to the sidebar width (`md:left-16 lg:left-60`) (`ReportTemplateEdit.tsx:912-948`).

Left side: unsaved-changes indicator. When `hasChanges = true` (i.e. `editing` is true and current `formData !== savedFormData`), shows a pulsing amber dot + "Unsaved changes" text. When no changes have been made yet, shows "No changes" in muted foreground.

Right side, left to right:
- **Cancel** (outline button, shown only when `!isNew`) — calls `handleCancelEdit()`: restores `formData` from `savedFormData`, sets `editing = false`, clears `fieldErrors` and `error`. No API call.
- **Create Template** / **Save Changes** (primary button) — calls `formRef.current?.requestSubmit()`. Label is "Create Template" in create mode, "Save Changes" in edit mode. Disabled when saving or (in edit mode) when `!hasChanges`. Shows a `Loader2` spinner while `saving = true`.

**Keyboard shortcuts**: the `useGlobalShortcuts` hook wires Ctrl/Cmd+S to `formRef.current?.requestSubmit()` and plain Escape (no modifier) to `handleCancelEdit()` (`ReportTemplateEdit.tsx:153-163`).

**Unsaved-changes guard**: `useUnsavedChanges(hasChanges)` fires a browser `beforeunload` warning when the user attempts to navigate away or close the tab while `hasChanges = true` (`ReportTemplateEdit.tsx:144`).

## 5. Dialogs

### 5.1 Browse in BU probe

This is not a modal dialog — it is an **inline panel** inside the Data Source card's Source Name section, visible only in edit mode (§4.4). The panel uses a dashed border to distinguish it from the main form area.

Workflow:
1. Author types a BU code into the compact `probe_bu` input. The code is persisted immediately to `localStorage.setItem('report_template_probe_bu', value)` (`ReportTemplateEdit.tsx:621`).
2. Author clicks **Load**. The button shows "Loading…" while `loadingDbObjects = true`.
3. SPA calls `reportTemplateService.listDbObjects(buCode)` → `GET /api-system/report-templates/db-objects?bu_code=<buCode>`.
4. On success, a `<select>` renders the objects of the matching type (`views` / `functions` / `procedures` based on current `source_type`). The placeholder option shows the count: "— pick from N `<type>`s in `<BU>` —".
5. Selecting an object sets `formData.source_name` to that object's `name` value.
6. On error, a `toast.error` is shown and `dbObjects` is reset to `null`.

If `probeBuCode` is present on mount (restored from `localStorage`), `loadDbObjects` is called automatically during `useEffect` (`ReportTemplateEdit.tsx:136-140`).

### 5.2 Soft Delete confirm

Triggered by the **Delete** row action in `ReportTemplateManagement` (`ReportTemplateManagement.tsx:310-315`).

Uses the shared `ConfirmDialog` component — a simple Yes/No confirm, no typed confirmation required (`ReportTemplateManagement.tsx:508-516`). Properties:
- **Title:** "Delete Report Template"
- **Description:** "Are you sure you want to delete this report template? This action cannot be undone."
- **Confirm button label:** "Delete" (destructive variant)

On confirm, calls `reportTemplateService.delete(id)` → `DELETE /api-system/report-templates/:id`. On success, `fetchTemplates()` re-fetches the list. There is no hard-delete dialog; hard deletion is not exposed from the management UI.

## 6. Persisted UI state

The list page writes 6 keys to `localStorage`. The edit page writes 1 key (the Browse-in-BU probe BU code).

| Key | Stored type | Persists |
|---|---|---|
| `search_report_templates` | string | Current debounced search term |
| `page_report_templates` | number (string) | Current page number; reset to `1` on search or filter change |
| `perpage_report_templates` | number (string) | Rows per page |
| `sort_report_templates` | string | Current sort column/direction (default `created_at:desc`) |
| `filters_report_templates` | JSON array | Active Status filter values (e.g. `["true"]`, `["false"]`, `[]`) |
| `filters_report_templates_source_type` | JSON array | Active Source Type filter values (e.g. `["view","function"]`, `[]`) |
| `report_template_probe_bu` | string | Last-used BU code for the Browse-in-BU probe in the edit page |

Note: `filters_report_templates` stores `is_active` booleans as **string values** `"true"` / `"false"` (not native JSON booleans) because they originate from button click values (`ReportTemplateManagement.tsx:392-406`). Readers querying this key directly should parse strings, not booleans.

There is no Standard/Custom filter and therefore no `filters_report_templates_standard` key. The `ReportTemplateEdit` page does not persist any state beyond `report_template_probe_bu`.

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References

- `../carmen-platform/SITEMAP.md` — route table for the three report-template routes; note it still shows the legacy `allowedRoles` lists — `src/App.tsx` is authoritative for the `requiredPermission` keys.
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` — list page: filters (Status + Source Type), header actions (Export, Add Template behind `<Can permission="report_template.create">`), row actions (Edit / Delete soft, behind `<Can>` gates), DataTable columns, 6 `localStorage` keys.
- `../carmen-platform/src/pages/ReportTemplateEdit.tsx` — create/view/edit page: 2-pane layout, Template Info card (5 visible fields + `kind` absent), Business Unit Scope card (ChipInput, `toCsv()` normalisation), Metadata card, Data Source card (source binding, Browse-in-BU probe, source params table, builder key), 3-tab CodeMirror right pane, sticky action bar, `useUnsavedChanges` hook.
- `../carmen-platform/src/services/reportTemplateService.ts` — API surface (paths pluralised 2026-06): `GET /api-system/report-templates`, `GET /api-system/report-templates/:id`, `POST /api-system/report-templates`, `PUT /api-system/report-templates/:id`, `DELETE /api-system/report-templates/:id`, `GET /api-system/report-templates/db-objects?bu_code=<buCode>` (`listDbObjects`).
- Cross-links: [report-templates](/en/platform/report-templates) (module landing), [business-units](/en/platform/business-units) (BU chip context and `cluster_id` FK), [Data Model](./data-model.md) (storage types for `allow_business_unit`, `deny_business_unit`, `source_params`; `kind` field), [Permissions](./permissions.md), [XML Spec](./xml-spec.md) (Dialog XML schema §2, Content XML schema §3).
