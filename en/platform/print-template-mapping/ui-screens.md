---
title: Print Template Mapping — UI Screens
description: The grouped-card PrintTemplateMappingManagement list (a deliberate deviation from the DataTable pattern) and the PrintTemplateMappingEdit view/edit form with the match-floating template select.
published: true
date: 2026-06-10T12:45:00.000Z
tags: book/platform, print-template-mapping, ui
editor: markdown
dateCreated: 2026-06-10T12:45:00.000Z
---

# Print Template Mapping — UI Screens

> **At a Glance**
> **Screens:** `PrintTemplateMappingManagement` (`/print-template-mapping`) · `PrintTemplateMappingEdit` (`/print-template-mapping/new`, `/print-template-mapping/:id/edit`) &nbsp;·&nbsp; **List layout:** grouped card sub-tables per document type — **not** the standard `DataTable`; no search, no CSV, no pagination controls &nbsp;·&nbsp; **Edit layout:** single "Mapping" card with a view/edit toggle &nbsp;·&nbsp; **Signature UI:** Report Template select floating `kind="print"` + `report_group` matches with an "N match / M total" count &nbsp;·&nbsp; **Persisted UI state:** none

## 1. Overview

The list page is a **deliberate deviation** from the SPA's standard Management pattern (Clusters, Applications, Report Templates): instead of a server-side `DataTable` with debounced search, Sheet filters, CSV export, and `localStorage`-persisted state, it renders one card containing a bordered sub-table **per document type**. The dataset justifies it — at most a handful of mappings per each of ten document types, written rarely — and the grouping *is* the information: "what prints for a GRN" is the question operators ask, and a flat sortable table would bury it. The trade-offs of skipping the standard furniture (notably the hidden server-side pagination) are called out in §2.5.

The edit page is conventional: a single "Mapping" card following the same view/edit-toggle pattern as Applications — create mode immediately editable, the edit route opening read-only behind a `<Can>`-gated Edit button. Its one signature element is the Report Template select (§3.3), which floats templates matching the chosen document type to the top rather than hiding the rest.

Both pages use toast feedback on mutations; the edit page additionally registers the global keyboard shortcuts (save submits while editing, cancel exits edit mode), arms the `useUnsavedChanges` navigation guard on any diff while editing, and ships the dev-only Debug Sheet (§3.4). The list page has no Debug Sheet.

## 2. `PrintTemplateMappingManagement` — list (`/print-template-mapping`)

### 2.1 Layout and header

A single Card. The header carries a Printer icon + title "Print Template Mapping", the subtitle "Map document types (PR/PO/SR/GRN/...) to the FastReport templates used for printing.", and one action: **New Mapping** (navigates to `/print-template-mapping/new`; wrapped in `<Can permission="print_template_mapping.create">`).

### 2.2 Filters

Inline controls on a bordered row — no Sheet panel:

- **Document Type** — a native select fed by `GET .../document-types`, options rendered as `CODE — Label`, with an "All" default. Selecting refetches the list with `?document_type=`.
- **Active only** — a checkbox that refetches with `?active_only=true`.

Both are server-side filters (every change refetches); there is no free-text search.

### 2.3 Grouped tables

Rows are grouped client-side by `document_type`; groups sort by code (`localeCompare`). Each group renders a bordered block with a muted header — a filled Badge with the type code, the type's label resolved from the document-types lookup, and a "(N mapping(s))" count — followed by a plain table:

| Column | Rendering |
|---|---|
| Template | `template_name` (bold; `-` when the joined template is missing) with `template_group` as muted subtext beneath |
| Display Label | Muted text, `-` when empty |
| Default | Filled "Default" badge when `is_default`, else `-` |
| Order | `display_order` in monospace |
| Active | Active (success) / Inactive (secondary) badge |
| (actions) | Right-aligned inline icon buttons — see §2.4 |

Within a group, rows keep the server's order: `display_order` ascending, `is_default DESC` as tie-break (applied by the Go list query when no sort is requested) — i.e. the same order the "Print as…" menu would show.

### 2.4 Row actions and delete dialog

Unlike the standard pattern's `⋯` dropdown, actions are two **inline ghost icon buttons**: a pencil (navigate to the edit route) wrapped in `<Can permission="print_template_mapping.update">` and a destructive trash wrapped in `<Can permission="print_template_mapping.delete">`. Delete opens a `ConfirmDialog` — title "Delete Print Template Mapping", description `Delete mapping "<DOC> → <template name>"? This cannot be undone (soft delete).` — and on confirm calls `DELETE .../print-template-mappings/:id`, toasts, and refetches. There is no delete affordance on the edit page.

### 2.5 States, and what the missing furniture costs

- **Loading** — a plain "Loading…" line (no `TableSkeleton`).
- **Error** — an inline destructive banner ("Failed to load print mappings: …"); the document-types lookup failing separately raises a toast.
- **Empty** — plain centered text: "No mappings yet. Click **New Mapping** to create one." (text only — not a button, so there is no ungated-CTA leak here, though the sentence references a button a `.create`-less session cannot see).
- **No persisted UI state** — neither filter survives a reload; nothing is written to `localStorage`.
- **Hidden pagination** — the SPA sends no `page`/`perpage`, the Go endpoint defaults to `perpage = 10`, and the page renders only what arrives with no pager or count. With more than 10 live mappings the list **silently truncates**. The response envelope may also nest (`data`, `data.data`, …) — the page unwraps up to five `.data` levels until it finds an array.

## 3. `PrintTemplateMappingEdit` (`/print-template-mapping/new`, `/print-template-mapping/:id/edit`)

### 3.1 Create mode (`/print-template-mapping/new`)

Title "New Print Template Mapping"; the card is immediately editable with defaults `is_default = true`, `display_order = 0`, `is_active = true`, everything else blank. Submit validates Document Type and Report Template (toast per missing field), calls `POST`, toasts "Mapping created", and redirects to the new row's edit route (`replace: true`), falling back to the list when the response carries no id. Cancel navigates back to the list.

### 3.2 View mode (`/print-template-mapping/:id/edit`, default)

Loads via `GET .../:id` and renders every field read-only: muted static boxes for the text fields (Document Type shown as `CODE — Label`, Report Template as `name [report_group]` resolved from the loaded template list, falling back to the raw id), the allow/deny lists as **secondary badge chips** (one per code; `-` when empty), and Default/Active as badges. The header carries a Back button and an **Edit** button wrapped in `<Can permission="print_template_mapping.update">` — without that key the page is permanently read-only, since the Save/Cancel row only renders in edit mode.

### 3.3 Edit mode — fields

The Edit toggle snapshots the form, then switches the card to editable. Fields (two-column grid):

| Field | Control | Notes |
|---|---|---|
| Document Type * | Native select of `CODE — Label` options from the document-types endpoint | Required (pre-submit toast) |
| Report Template * | Native select — see below | Required (pre-submit toast) |
| Display Label | Text input, placeholder "e.g. Standard PR (A4 Portrait)" | Helper text: shown in the "Print as…" menu when multiple templates exist for the same document type |
| Display Order | Number input | Non-numeric input coerces to 0 |
| Allow Business Units | Text input, placeholder "e.g. T01,T03 (comma-separated, blank = all)" | CSV of BU codes; parsed/trimmed on save; blank sends `null` — which does **not** clear a stored list (see [Data Model](./data-model.md) §5) |
| Deny Business Units | Text input, placeholder "e.g. T02 (comma-separated, blank = none)" | Same CSV handling |
| Default for this Document Type | Checkbox | Label: "Use this template when the user clicks the legacy "Print" button" |
| Active | Checkbox | |

**The Report Template select** loads up to 500 templates once on mount (`reportTemplateService.getAll({ perpage: 500 })`). With a document type chosen, templates matching `kind === 'print' && report_group === document_type` **float to the top — the rest remain selectable below** (a soft sort, not a hard filter, despite the helper text saying "Filtered by report_group matching the document type"). The placeholder reads `Select template (N match / M total)…` (or `(M total)` with no type chosen, or `— no templates available —`), and options render as `name [report_group]`. Picking a non-matching template is therefore possible by design — useful for cross-group reuse, easy to do by accident.

On save in edit mode the page `PUT`s the full form payload, toasts "Changes saved", re-fetches, and drops back to view mode. Cancel restores the pre-edit snapshot and exits edit mode without a server call.

### 3.4 Debug Sheet (dev only)

On the edit route (never create, never the list), `import.meta.env.DEV` builds render an amber floating button opening a Sheet with the raw JSON of the last `GET .../:id` response plus a Copy JSON button — the quickest way for QA to inspect the denormalized join fields and the actual JSONB shape of the BU lists.

## 4. References

- `../carmen-platform/src/pages/PrintTemplateMappingManagement.tsx` — grouped list, filters, `<Can>` gates, delete dialog, envelope unwrapping.
- `../carmen-platform/src/pages/PrintTemplateMappingEdit.tsx` — form state, `rowToForm`/`parseList`, the template float logic (`matches`, `filteredTemplates`, `matchedCount`), Debug Sheet.
- `../carmen-platform/src/services/printTemplateMappingService.ts` — the endpoints behind every action.
- `../carmen-platform/src/services/reportTemplateService.ts` — `ReportTemplate` (`kind`, `report_group`) consumed by the template select.
- `../micro-report/db/print_template_mapping_repo.go` — the server-side default row ordering and `perpage` behaviour surfaced in §2.3/§2.5.

**Cross-links:** [Print Template Mapping landing](/en/platform/print-template-mapping) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Report Templates — UI Screens](../report-templates/ui-screens.md)
