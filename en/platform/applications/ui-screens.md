---
title: Applications — UI Screens
description: The ApplicationManagement list and the ApplicationEdit form, including the grouped-accordion API Names selector and its ChipInput fallback.
published: true
date: 2026-07-29T07:21:27.000Z
tags: book/platform, applications, ui
editor: markdown
dateCreated: 2026-06-10T12:30:00.000Z
---

# Applications — UI Screens

> **At a Glance**
> **Screens:** `ApplicationManagement` (`/applications`) · `ApplicationEdit` (`/applications/new`, `/applications/:id/edit`) &nbsp;·&nbsp; **New since last sync:** `ApplicationRegistrySummary` strip (list), `ApplicationIdentityHero` (edit page), App ID + Description folded under the Name column (no longer separate columns), edit layout rewritten from one card into hero + API-access/Settings two-column, sticky bottom Save bar, not-found gating, `doc_version` optimistic locking &nbsp;·&nbsp; **Edit layout:** still a view/edit toggle (unlike clusters/business-units' one-document rewrite) &nbsp;·&nbsp; **Signature UI:** API Names selector — accordion grouped by module, filter box, per-module All/None, action-only button labels &nbsp;·&nbsp; **Fallback:** `ChipInput` free-text entry when the catalog fetch fails &nbsp;·&nbsp; **Persisted UI state:** 5 `localStorage` keys on the list page

## 1. Overview

Applications follows the SPA's standard two-screen Management/Edit pattern: a server-side `DataTable` list with debounced search, Sheet filters, CSV export, a **Registry** summary strip, and persisted state; plus a create/view/edit page that, since the last sync, was rewritten from a single "Application Details" card into an `ApplicationIdentityHero` above a two-column **API access** / **Settings** layout. Two things remain module-specific. First, the **App ID** treatment — the record UUID is surfaced read-only, now via a copyable chip in the hero (and, on the list, inline under the application's name) because it is the `x-app-id` credential operators need to copy into client configuration. Second, the **API Names selector**, the module's signature component (§3.4): an accordion of catalog keys grouped by module, shown only while "Allow all APIs" is unchecked (with a warning banner in its place when `allow_all` is on).

Both screens ship the dev-only **Debug Sheet** (amber floating button, `import.meta.env.DEV` only) exposing the raw JSON of `GET /api-system/applications` (list) or `GET /api-system/applications/:id` (edit) — the quickest way for QA to confirm the actual envelope and audit nesting. Both also register the SPA's global keyboard shortcuts (`useGlobalShortcuts`): on the list the search shortcut focuses the search input; on the edit form the save shortcut submits while editing and the cancel shortcut exits edit mode (view/edit route only, not create).

## 2. `ApplicationManagement` — list (`/applications`)

### 2.1 Layout and header actions

Header (`PageHeader`): title "Application Management" / subtitle "Manage applications and their API access", with two actions — **Export** (client-side CSV of the loaded page: Name, App ID, Description, Access, Status; file `applications-<YYYY-MM-DD>.csv`; disabled while loading or empty) and **Add Application** (navigates to `/applications/new`; wrapped in `<Can permission="application.create">`). Below the header sits the **Registry** summary strip (§2.1a), then the search/filter row.

### 2.1a Registry strip

An `ApplicationRegistrySummary` card summarises **every application** (a separate unpaginated `perpage: -1` fetch, not just the current page):

- A large total count with "`<n>` active" / "`<n>` active · `<n>` inactive" underneath.
- An **"API access scope"** proportion bar — full-access (`allow_all`, styled in the warning colour, since an unrestricted app is audit-worthy) vs. scoped (explicit list), with a legend; the "Full access" legend entry itself switches to a warning triangle icon when the count is non-zero.
- A **"Devices"** breakdown — one chip per device value in use, ordered `web`/`mobile`/`desktop`/`pos` then alphabetically, each showing its count.

Shows a skeleton while loading and an inline error/retry state on fetch failure — the main table is unaffected either way.

### 2.2 Search and filters

A debounced (400 ms) search input over `name`/`description` (server-side via the `search` param), plus a **Filters** Sheet (description "Filter applications by status and device") with two groups: a **Status** group — Active/Inactive toggle buttons that translate to the `advance` query `{ where: { is_active } }` when exactly one is selected — and a **Device** dropdown whose options are "All devices" (clears the filter) plus `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`); a chosen device adds `{ where: { device } }` to the same `advance` clause. Each active filter (status and device) counts toward the filter badge and renders as a chip under the search row with per-chip remove and a "Clear all" link.

### 2.3 Columns

**The App ID and Description columns no longer exist as separate columns** — both were folded under Name, a layout change since the last sync (mirrors the equivalent "report-templates-style" table adopted across the SPA):

| Column | Rendering |
|---|---|
| Name | A small stack: the name (link to `/applications/:id/edit`), the record UUID underneath in monospace muted text with an inline copy-to-clipboard icon button (`Copy`/`Check` toggle, 2 s confirm, toast on copy), and the description (if any) below that in smaller muted text |
| Access | Right-aligned outline badge: **All APIs** when `allow_all`, else **N APIs** from `api_names.length` (0 when absent); not sortable |
| Device | Secondary badge from `device`, falling back to `web` when absent |
| Status | Active (success) / Inactive (secondary) badge from `is_active` |
| Created | `created_at` (`YYYY-MM-DD HH:mm:ss`, browser-local) with `created_by_name` on the next line — flattened from the nested `audit.created` `{ at, name }` shape when the API nests it |
| Updated | Same shape from `audit.updated`; renders `-` when `updated_at === created_at` |
| Actions | `⋯` dropdown — see §2.4 |

Default sort is `name:asc`. First load renders a `TableSkeleton` sized to the current column count; subsequent loads overlay a "Loading applications..." scrim on the existing table.

### 2.4 Row actions and delete dialog

The actions dropdown carries **Edit** (navigate to the edit route) wrapped in `<Can permission="application.update">` and **Delete** (destructive styling) wrapped in `<Can permission="application.delete">`. Delete opens a `ConfirmDialog` ("Delete Application — Are you sure you want to delete this application? This action cannot be undone."); confirming calls `DELETE /api-system/applications/:id`, toasts, and refetches the page (and reloads the Registry strip). There is no delete affordance anywhere else in the module.

### 2.5 Empty state and persisted UI state

An empty result renders an `EmptyState` card (AppWindow icon) whose title is always "No applications yet"; only the description beneath it varies — `No applications matching "<term>"` when a search term is active, or "Get started by creating your first application." with an inline **Add Application** CTA when none is. **Corrected since the last sync: this CTA is now `<Can permission="application.create">`-wrapped**, same as the header button — the gap previously flagged in [Permissions](./permissions.md) is closed.

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

Title "Add Application" (`PageHeader`, no hero — the hero needs an existing `id` for its App ID chip and audit lines). Both cards (API access, Settings) render immediately editable in the two-column layout described in §3.3. On submit the SPA validates `name` (required; also validated on blur, with the error cleared on focus), calls `POST /api-system/applications` (payload includes `doc_version: undefined`, which the client drops), toasts, and redirects to `/applications/:id/edit` for the created id (`replace: true`), falling back to the list when the response carries no id.

### 3.2 View mode (`/applications/:id/edit`, default)

Loads via `GET /api-system/applications/:id` (a hero + two-card skeleton while in flight, matching the loaded layout exactly). A dedicated **not-found** state (new since the last sync) replaces the whole shell with an `EmptyState` ("Application not found... Back to applications") when the id doesn't resolve to a live record, rather than rendering the edit page over blank data.

Above the form sits the **`ApplicationIdentityHero`**: an `AppWindow`-icon avatar tile, the name as the page's `<h1>`, Device and Active/Inactive badges, an App ID chip (monospace, with its own copy button) shown once the record exists, an access-reach summary line ("Full access to every endpoint" in the warning colour with an alert-triangle icon, or "`<n>` endpoint(s) across `<m>` module(s)" / "No endpoints granted yet" in muted text), and Created/Updated audit lines. In view mode, the hero's actions slot shows a single **Edit** button wrapped in `<Can permission="application.update">` — without that key the page is permanently read-only, since Save is unreachable outside edit mode.

The two-column body renders read-only in view mode: the **API access** card shows either the warning banner (`allow_all`) or, when names are granted, read-only grouped badges — one sub-list per module (`groupApiNames` over the loaded `api_names`), each badge labelled with the action segment only (`actionOf`) and carrying the full key in its `title` attribute (or "No endpoints granted." when empty) — and the **Settings** card shows Name/Description/Device/Status as static fields/badges.

### 3.3 Edit mode — two-column layout

The Edit toggle (hero action button) snapshots the current form, then switches both cards to editable. **The single "Application Details" card from the prior sync no longer exists** — the form is now `grid-cols-1 lg:grid-cols-[1fr_minmax(300px,340px)]`: a wide left column holds the **"API access"** card (title + "Which endpoints this app may call." description) with the `allow_all` checkbox and the selector; a narrower right column holds a **sticky** ("Settings") card with the remaining fields:

| Field | Edit-mode control | Notes |
|---|---|---|
| Full access to every API (`allow_all`) | Checkbox, in the API access card | Labelled "Full access to every API" with a description line; checking it replaces the selector with a warning banner (also shown in view mode) |
| API Names | Grouped accordion selector (§3.4), in the API access card | Only when `allow_all` is unchecked |
| Name * | Text input, in the Settings card | Required; blur + pre-submit validation |
| Description | Text input, in the Settings card | Optional |
| Device | `<select>` of `mobile` / `web` / `desktop` / `pos` (`DEVICE_OPTIONS`), in the Settings card | Defaults to `web` (also the fallback when a loaded value is outside the option set); renders as a capitalised secondary Badge in view mode |
| Active (`is_active`) | Checkbox, in the Settings card | Renders as the Status badge in view mode |

**App ID is no longer a Settings-card field row** — it now lives only in the hero chip (§3.2), not repeated in the form.

A **sticky bottom bar** (new since the last sync, replacing the previous in-card Save/Cancel row) shows **Save Changes** / **Create Application** (with a spinner while saving) and **Cancel**, plus an "Unsaved changes" / "No changes" indicator, fixed to the viewport bottom while `editing` is true. Cancel restores the pre-edit snapshot and exits edit mode (in create mode it navigates back to the list). Unsaved changes (any diff against the snapshot while editing) arm the `useUnsavedChanges` navigation guard, and the global keyboard shortcuts trigger save and cancel. On a successful update the page **re-fetches the application (refreshing `doc_version`) and drops back to view mode**; a stale save (`409`) shows a conflict toast and reloads instead of overwriting.

### 3.4 The API Names selector

The module's signature component, rendered inline in the API access card (no separate component file). Options come from `GET /api-system/applications/api-catalog`, fetched once on mount; until groups arrive the box shows "Loading catalog…", and a genuinely empty catalog ("No API endpoints are defined in the catalog yet.") is now distinguished from the loading state (a fix since the last sync).

- **Accordion grouped by module** — one row per `ApiCatalogGroup`, in a bordered scroll container (`max-h-80`, ~320 px). Each module row is a real ≥44px tap target (`min-h-11` on the toggle, not an overlay); it packs a chevron (expand/collapse), the module name, a `selected/total` count badge (filled variant once anything is selected), and an **All/None** button (a `HIT_SLOP_44` overlay on this compact button, since only one per module row is needed) that selects or clears the whole module in one click.
- **Filter input** — matches against the module name *or* any `api_name` (case-insensitive). A module-name match shows the entire group; otherwise the group narrows to matching names. Matching groups **auto-expand** while a filter is active (manual chevron toggling is suspended); a non-matching filter shows `No API names matching "<term>"`.
- **Expand all / Collapse all** — a single toggle scoped to the currently *visible* groups, so it composes with the filter.
- **Per-key toggle buttons** — inside an expanded group, each `api_name` is a small button labelled with the **action segment only** (`actionOf(api)`), with the full key in the `title` attribute; selected keys render filled with an `X` glyph. **These chips deliberately do NOT get a 44px hit-slop overlay** — at their compact size (`h-7`) with only a 6px row gap, a centred 44px overlay would bleed past each edge further than the gap and let vertically-adjacent rows' tap zones overlap; on this permission-granting surface an overlapping tap could grant the wrong API, so the chips were kept at their smaller, non-overlapping size instead (a documented, deliberate accessibility trade-off, not an oversight). A running "N selected" count sits under the box.
- **`ChipInput` fallback** — if the catalog fetch fails (`catalogFailed`), the selector degrades to a free-text chip input ("Type an api_name and press Enter") behind a `FetchErrorState` retry banner, so grants remain editable without the catalog; entries are comma-joined into the same `api_names` array.

Selections live in flat form state (`api_names: string[]`); on save the service converts them to the write payload's `details.add[]` (replace semantics — see [Data Model](./data-model.md) §5).

## 4. References

- `../carmen-platform/src/pages/ApplicationManagement.tsx` and `applicationManagement/ApplicationRegistrySummary.tsx` — list page: Registry summary strip, Name-column App-ID/description fold-in, filter Sheet, CSV export, `<Can>` gates (incl. the fixed empty-state CTA), audit flattening, persisted keys.
- `../carmen-platform/src/pages/ApplicationEdit.tsx` and `applicationEdit/ApplicationIdentityHero.tsx` — hero card, two-column API-access/Settings form, `allow_all` fork, the inline accordion selector, ChipInput fallback, `doc_version`-aware save flow, not-found gating.
- `../carmen-platform/src/utils/docVersion.ts` — optimistic-lock helpers.
- `../carmen-platform/src/services/applicationService.ts` — endpoints, `toWritePayload` (incl. `doc_version`), `getApiCatalog` with grouping fallback.
- `../carmen-platform/src/utils/apiCatalog.ts` — `moduleOf` / `actionOf` / `groupApiNames` (shared by the selector and the read-only badge view).
- `../carmen-platform/CLAUDE.md` — "Application Management Specifics" section (read/write asymmetry, grouped catalog pattern).

**Cross-links:** [Applications landing](/en/platform/applications) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
