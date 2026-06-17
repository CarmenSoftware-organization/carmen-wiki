---
title: Applications — UI Screens
description: The ApplicationManagement list and the ApplicationEdit form, including the grouped-accordion API Names selector and its ChipInput fallback.
published: true
date: 2026-06-17T08:00:00.000Z
tags: book/platform, applications, ui
editor: markdown
dateCreated: 2026-06-10T12:30:00.000Z
---

# Applications — UI Screens

> **At a Glance**
> **Screens:** `ApplicationManagement` (`/applications`) · `ApplicationEdit` (`/applications/new`, `/applications/:id/edit`) &nbsp;·&nbsp; **Edit layout:** single "Application Details" card with an Edit toggle &nbsp;·&nbsp; **Signature UI:** API Names selector — accordion grouped by module, filter box, per-module All/None, action-only button labels &nbsp;·&nbsp; **Fallback:** `ChipInput` free-text entry when the catalog fetch fails &nbsp;·&nbsp; **Persisted UI state:** 5 `localStorage` keys on the list page

## 1. Overview

Applications follows the SPA's standard two-screen Management/Edit pattern (copied from Clusters): a server-side `DataTable` list with debounced search, Sheet filters, CSV export, and persisted state; plus a single-card create/view/edit form. Two things are module-specific. First, the **App ID** treatment — the record UUID is surfaced read-only in both screens because it is the `x-app-id` credential operators need to copy into client configuration. Second, the **API Names selector** on the edit form, the module's signature component (§3.4): an accordion of catalog keys grouped by module, shown only while "Allow all APIs" is unchecked.

Both screens ship the dev-only **Debug Sheet** (amber floating button, `import.meta.env.DEV` only) exposing the raw JSON of `GET /api-system/applications` (list) or `GET /api-system/applications/:id` (edit) — the quickest way for QA to confirm the actual envelope and audit nesting. Both also register the SPA's global keyboard shortcuts (`useGlobalShortcuts`): on the list the search shortcut focuses the search input; on the edit form the save shortcut submits while editing and the cancel shortcut exits edit mode (view/edit route only, not create).

## 2. `ApplicationManagement` — list (`/applications`)

### 2.1 Layout and header actions

Header: title "Application Management" / subtitle "Manage applications and their API access", with two actions — **Export** (client-side CSV of the loaded page: Name, App ID, Description, Access, Status; file `applications-<YYYY-MM-DD>.csv`; disabled while loading or empty) and **Add Application** (navigates to `/applications/new`; wrapped in `<Can permission="application.create">`).

### 2.2 Search and filters

A debounced (400 ms) search input over `name`/`description` (server-side via the `search` param; the input highlights yellow while a term is active and offers an inline clear button), plus a **Filters** Sheet (description "Filter applications by status and device") with two groups: a **Status** group — Active/Inactive toggle buttons that translate to the `advance` query `{ where: { is_active } }` when exactly one is selected — and a **Device** dropdown whose options are "All devices" (clears the filter) plus `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`); a chosen device adds `{ where: { device } }` to the same `advance` clause. Each active filter (status and device) counts toward the filter badge and renders as a chip under the search row with per-chip remove and a "Clear all" link.

### 2.3 Columns

| Column | Rendering |
|---|---|
| Name | Link to `/applications/:id/edit` |
| App ID | The record UUID in monospace muted text, full value also in the `title` attribute (hover tooltip); not sortable |
| Description | Muted text, `-` when empty; not sortable |
| Access | Right-aligned outline badge: **All APIs** when `allow_all`, else **N APIs** from `api_names.length` (0 when absent); not sortable |
| Status | Active (success) / Inactive (secondary) badge from `is_active` |
| Device | Secondary badge from `device`, falling back to `web` when absent |
| Created | `created_at` (`YYYY-MM-DD HH:mm:ss`, browser-local) with `created_by_name` on the next line — flattened from the nested `audit.created` `{ at, name }` shape when the API nests it |
| Updated | Same shape from `audit.updated`; renders `-` when `updated_at === created_at` |
| Actions | `⋯` dropdown — see §2.4 |

Default sort is `name:asc`. First load renders an 8-column `TableSkeleton`; subsequent loads overlay a "Loading applications..." scrim on the existing table.

### 2.4 Row actions and delete dialog

The actions dropdown carries **Edit** (navigate to the edit route) wrapped in `<Can permission="application.update">` and **Delete** (destructive styling) wrapped in `<Can permission="application.delete">`. Delete opens a `ConfirmDialog` ("Delete Application — Are you sure you want to delete this application? This action cannot be undone."); confirming calls `DELETE /api-system/applications/:id`, toasts, and refetches the page. There is no delete affordance anywhere else in the module.

### 2.5 Empty state and persisted UI state

An empty result renders an `EmptyState` card (AppWindow icon) whose title is always "No applications yet"; only the description beneath it varies — `No applications matching "<term>"` when a search term is active, or "Get started by creating your first application." with an inline **Add Application** CTA when none is (note: this CTA is *not* `<Can>`-wrapped — see [Permissions](./permissions.md)).

| `localStorage` key | Stored type | Persists |
|---|---|---|
| `search_applications` | string | Search term |
| `filters_applications` | JSON string array | Status filter selections |
| `devicefilter_applications` | string | Device filter selection (empty = all devices) |
| `page_applications` | number string | Current page |
| `perpage_applications` | number string | Page size |
| `sort_applications` | string | Sort (`column:dir`, default `name:asc`) |

The edit page persists no UI state.

## 3. `ApplicationEdit` (`/applications/new`, `/applications/:id/edit`)

### 3.1 Create mode (`/applications/new`)

Title "Add Application"; the single "Application Details" card is immediately editable. The App ID row is absent — the UUID exists only after the server creates the row. On submit the SPA validates `name` (required; also validated on blur, with the error cleared on focus), calls `POST /api-system/applications`, toasts, and redirects to `/applications/:id/edit` for the created id (`replace: true`), falling back to the list when the response carries no id.

### 3.2 View mode (`/applications/:id/edit`, default)

Loads via `GET /api-system/applications/:id` (skeleton placeholders while in flight) and renders read-only: title "Application Details", every field as a static muted box, **Status** and **API Access** as badges (API Access reads "All APIs" or "N selected"). The header carries a back arrow to `/applications` and an **Edit** button wrapped in `<Can permission="application.update">` — without that key the page is permanently read-only, since Save is unreachable outside edit mode.

When `allow_all` is off and names are granted, the **API Names** block shows the selection as read-only grouped badges: one sub-list per module (`groupApiNames` over the loaded `api_names`), each badge labelled with the action segment only (`actionOf`) and carrying the full key in its `title` attribute. With no names granted it shows `-`.

### 3.3 Edit mode — fields

The Edit toggle snapshots the current form, then switches the card to editable:

| Field | Edit-mode control | Notes |
|---|---|---|
| Name * | Text input | Required; blur + pre-submit validation |
| App ID | — | Always a read-only monospace box showing the record UUID (truncated when narrow); server-generated, never editable |
| Description | Text input | Optional |
| Device | `<select>` of `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`) | Defaults to `web` (also the fallback when a loaded value is outside the option set); renders as a secondary Badge in view mode |
| Active | Checkbox | Renders as the Status badge in view mode |
| Allow all APIs | Checkbox | Renders as the API Access badge in view mode; checking it hides the API Names block entirely |
| API Names | Grouped accordion selector (§3.4) | Only when "Allow all APIs" is unchecked |

**Save** (`Save Changes` / `Create Application`, with a spinner while saving) submits the form; **Cancel** restores the pre-edit snapshot and exits edit mode (in create mode it navigates back to the list). Unsaved changes (any diff against the snapshot while editing) arm the `useUnsavedChanges` navigation guard, and the global keyboard shortcuts trigger save and cancel. On a successful update the page **re-fetches the application and drops back to view mode**.

### 3.4 The API Names selector

The module's signature component, rendered inline in the form (no separate component file). Options come from `GET /api-system/applications/api-catalog`, fetched once on mount; until groups arrive the box shows "Loading catalog…".

- **Accordion grouped by module** — one collapsible row per `ApiCatalogGroup`, in a bordered scroll container (`max-h-80`, ~320 px). Each module header packs: a chevron (expand/collapse), the module name, a `selected/total` count badge (filled variant once anything is selected), and an **All/None** button that selects or clears the whole module in one click.
- **Filter input** — matches against the module name *or* any `api_name` (case-insensitive). A module-name match shows the entire group; otherwise the group narrows to matching names. Matching groups **auto-expand** while a filter is active (manual chevron toggling is suspended); a non-matching filter shows `No API names matching "<term>"`.
- **Expand all / Collapse all** — a single toggle scoped to the currently *visible* groups, so it composes with the filter.
- **Per-key toggle buttons** — inside an expanded group, each `api_name` is a small button labelled with the **action segment only** (`actionOf(api)`), with the full key in the `title` attribute; selected keys render filled with an `X` glyph. A running "N selected" count sits under the box.
- **`ChipInput` fallback** — if the catalog fetch fails (`catalogFailed`), the selector degrades to a free-text chip input ("Type an api_name and press Enter"), so grants remain editable without the catalog; entries are comma-joined into the same `api_names` array.

Selections live in flat form state (`api_names: string[]`); on save the service converts them to the write payload's `details.add[]` (replace semantics — see [Data Model](./data-model.md) §5).

## 4. References

- `../carmen-platform/src/pages/ApplicationManagement.tsx` — list page: columns, filter Sheet, CSV export, `<Can>` gates, audit flattening, persisted keys.
- `../carmen-platform/src/pages/ApplicationEdit.tsx` — form, App ID display, `allow_all` fork, the inline accordion selector (≈ lines 380–550), ChipInput fallback, save flow.
- `../carmen-platform/src/services/applicationService.ts` — endpoints, `toWritePayload`, `getApiCatalog` with grouping fallback.
- `../carmen-platform/src/utils/apiCatalog.ts` — `moduleOf` / `actionOf` / `groupApiNames` (shared by the selector and the read-only badge view).
- `../carmen-platform/CLAUDE.md` — "Application Management Specifics" section (read/write asymmetry, grouped catalog pattern).

**Cross-links:** [Applications landing](/en/platform/applications) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
