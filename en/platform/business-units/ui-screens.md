---
title: Business Unit — UI Screens
description: BusinessUnitManagement (list) and BusinessUnitEdit (9 collapsible form sections, Users card, 3 dialogs) — layout, filters, actions, persisted state.
published: true
date: '2026-05-19T17:30:00.000Z'
tags: book/platform, business-units, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Business Unit — UI Screens

> **At a Glance**
> **Screens:** `BusinessUnitManagement` (list, `/business-units`) &nbsp;·&nbsp; `BusinessUnitEdit` create (`/business-units/new`) &nbsp;·&nbsp; `BusinessUnitEdit` view/edit (`/business-units/:id/edit`) &nbsp;·&nbsp; **Edit layout:** 9 collapsible `CollapsibleSection` cards in a 2-column grid (Basic Information · Hotel Information · Company Information · Tax Information · Date/Time Formats · Number Formats · Calculation Settings · Configuration · Database Connection) plus a full-width Users card below the form &nbsp;·&nbsp; **Dialogs:** Add User to BU · Edit BU User · Remove BU User confirm · Soft Delete BU confirm &nbsp;·&nbsp; **Access:** all three routes "Authenticated" — no `allowedRoles` prop &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys

## 1. Overview

The business-unit surface follows the Platform SPA's standard two-screen pattern: a server-side `DataTable` list page (`BusinessUnitManagement`) and a shared create/view/edit page (`BusinessUnitEdit`). Unlike the cluster edit page — which uses a 3-column grid with Business Units and Users as sibling cards — the BU edit page stacks all content vertically: a 2-column `grid-cols-1 lg:grid-cols-2` form area containing 9 collapsible section cards, followed by a full-width Users card that only renders in view/edit mode (hidden in create mode).

`BusinessUnitEdit` is the largest edit page in the Platform SPA at 1785 lines. The density comes from the `BusinessUnitFormData` interface covering 33 fields across identity, contact, locale, formatting, costing, connection, and config domains. Every section card uses the shared `CollapsibleSection` component, which has a clickable `CardHeader` that toggles an expand/collapse chevron. All 9 sections are initially rendered with `forceOpen` (they cannot be collapsed), keeping all fields in the DOM and visible on load — the `forceOpen` prop overrides whatever `defaultOpen` value was set. The Users card is outside the `<form>` element and has its own independent mutation lifecycle.

Both screens access all three registered routes without `allowedRoles` — any authenticated platform user can reach the BU list and edit routes. Compare [[clusters]], whose three routes require `platform_admin`, `support_manager`, or `support_staff`.

## 2. `BusinessUnitManagement` — list page (`/business-units`)

### 2.1 Layout

The page renders inside `Layout` with a two-row header: a title/subtitle row ("Business Unit Management" / "Manage business units and departments") and an actions row with **Export** and **Add Business Unit** buttons (the button label shortens to "Add BU" on small screens via responsive visibility classes). Below the header sits a search-and-filters row inside a `Card`. The `DataTable` renders in server-side mode with pagination.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side `Sheet` (slide-over panel). An active-filter count badge appears on the Filters button when any filter is set. Two filter groups are wired:

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). Only one may be active at a time in practice (pressing a button that is already selected deselects it); when one value is selected the query appends an `is_active` equality constraint. When both or neither are selected, no status constraint is applied.
- **Deleted** — a checkbox labelled "Show soft-deleted business units". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface in the table with a red `Deleted` badge in the `name` cell, and a conditional `Deleted By` column is appended to the `DataTable`.

There is no cluster filter group on the list page; filtering by cluster requires the search bar or server-side `advance` parameter. When any filter is active, active filter chips appear in a strip below the search row. Each chip has an inline remove button; a **Clear all** text link clears all filters at once. A **Clear All Filters** button also appears at the bottom of the Sheet when any filter is active. A **Clear** link appears in the Status group header when a status value is selected.

### 2.3 Header actions

Two buttons appear in the header actions row:

- **Export** — client-side CSV export using `generateCSV` / `downloadCSV` utilities (no server call). Exports the currently loaded page of rows with columns: `Code`, `Name`, `Alias Name`, `Cluster`, `Status` (`is_active`), `Max Licensed Users`, `Created` (`created_at`). File name: `business-units-<YYYY-MM-DD>.csv`. The button is disabled while loading or when the table is empty.
- **Add Business Unit** — navigates to `/business-units/new`.

There is no Fetch Keycloak button (that affordance exists only on the Users list) and no Hard Delete action anywhere in business-unit management.

### 2.4 Row actions

Columns in order: `code` (clickable link — navigates to `/business-units/:id/edit`), `name` (clickable link — also navigates to edit; a red `Deleted` badge is appended when `deleted_at` is non-null), `alias_name` (muted text), `cluster_name`, `is_active` (Active/Inactive badge), `created_at` + `created_by_name`, `updated_at` + `updated_by_name` (suppressed when equal to `created_at`), and conditionally `deleted_at` + `deleted_by_name` in destructive red (only when "Show soft-deleted" filter is on). The final column is a `DropdownMenu` icon button (⋯) with two items:

- **Edit** — navigates to `/business-units/:id/edit`.
- **Delete** — sets `deleteId` state; opens the Soft Delete BU `ConfirmDialog` (§5.4).

There is no Hard Delete option in the row action menu. The `BusinessUnitManagement` page calls only `DELETE /api-system/business-unit/:id` (soft delete — sets `deleted_at`).

### 2.5 Audit columns

| Column header | Fields rendered |
|---|---|
| Created | `created_at` (formatted `YYYY-MM-DD HH:mm:ss`, browser local time) + `created_by_name` on the next line |
| Updated | `updated_at` + `updated_by_name` — suppressed (renders `null`) when `updated_at === created_at` |

When "Show soft-deleted" is on, a third audit column is appended:

| Column header | Fields rendered |
|---|---|
| Deleted By | `deleted_at` + `deleted_by_name` (text in destructive red); shows `-` for non-deleted rows |

## 3. `BusinessUnitEdit` — create mode (`/business-units/new`)

In create mode (`isNew = true`) the page title is "Add Business Unit" and the subtitle is "Create a new business unit". The form is immediately editable — no Edit header button appears. The Users card is hidden (rendered only when `!isNew`).

The form renders all 9 `CollapsibleSection` cards in the 2-column grid. All fields are editable. Required fields are marked with `*` in the label when `editing` is true.

**`?cluster_id=<id>` query parameter:** the `initialFormData` reads `searchParams.get('cluster_id') || ''` and sets it as the initial value of `cluster_id` in `formData` (line 186). When `BusinessUnitEdit` is reached by clicking **Add** in the Cluster Details card of [[clusters]] (`/business-units/new?cluster_id=<id>`), the Cluster select in the Basic Information section is pre-selected to that cluster. The user can change it before saving.

**License limit check on submit:** before calling `POST /api-system/business-unit`, the form fetches the selected cluster via `GET /api-system/cluster/:id` and counts existing BUs in that cluster. If `currentCount >= cluster.max_license_bu`, it blocks the submit with an inline error and does not call the create endpoint.

**Post-create navigation:** on success, if the response includes an `id`, navigates to `/business-units/:id` with `{ replace: true }` — the create form is replaced in browser history so Back goes to the list. If no `id` is returned, navigates to `/business-units`. **Cancel** navigates to `/business-units` without an API call.

## 4. `BusinessUnitEdit` — view/edit mode (`/business-units/:id/edit`)

The page starts in **view mode** (`editing = false`, `isNew = false`). Title: "Business Unit Details". A single **Edit** button appears in the header. Clicking **Edit** saves `formData` to `savedFormData` and sets `editing = true`. In edit mode the title changes to "Edit Business Unit" / "Update business unit information"; Save Changes and Cancel buttons appear in a full-width row spanning both grid columns (`lg:col-span-2`). **Cancel** restores `formData` from `savedFormData` without an API call. **Save Changes** → `PUT /api-system/business-unit/:id`; on success, `fetchBusinessUnit()` re-fetches and `setEditing(false)` returns to view mode. The `useUnsavedChanges` hook fires if the user attempts to navigate away while `editing = true` and `formData !== savedFormData`.

All 9 section cards are rendered identically in view and edit mode. In view mode the `CollapsibleSection` renders fields using `ReadOnlyText` (styled `div` with `bg-muted/50`) or `ReadOnlyTextarea` for multi-line fields. In edit mode the same positions render `Input`, `textarea`, or `select` elements.

### 4.1 Basic Information

Fields: **Cluster** (required, `select` from all clusters via `GET /api-system/cluster?perpage=-1`), **Code** (required, text, inline validation on blur), **Name** (required, text), **Alias Name** (optional text), **Description** (optional, 3-row `textarea`), **Max Licensed Users** (optional number input — displays "Unlimited" in read-only mode when blank), **Headquarters (HQ)** checkbox, **Active** checkbox.

Both checkboxes are editable in both create and edit mode. There is no `disabled` guard on any field — `code`, `cluster_id`, `is_hq`, and `is_active` are all editable after creation. Note: `is_hq` uniqueness is enforced at the application layer only (no DB constraint); the UI allows setting multiple BUs as HQ without a warning. See [Data Model](./data-model.md) for schema details.

In view mode, `is_hq` and `is_active` are shown as success/secondary badges rather than checkboxes.

### 4.2 Hotel Information

Fields: **Hotel Name** (text), **Telephone** (text, validated on blur), **Email** (text, validated on blur), **Address** (3-row `textarea`), **Zip Code** (text). All optional. No required markers.

Telephone and email fields use `onBlur` / `onFocus` handlers for inline validation error display via `fieldErrors` state (same `validateField` utility used in the cluster and user forms).

### 4.3 Company Information

Fields: **Company Name** (text), **Telephone** (text, validated on blur), **Email** (text, validated on blur), **Address** (3-row `textarea`), **Zip Code** (text). All optional. Structure mirrors Hotel Information.

### 4.4 Tax Information

Fields (2-column grid): **Tax No.** (text), **Branch No.** (text). Both optional.

### 4.5 Date/Time Formats

Fields (2-column grid, 3 rows): **Date Format** (e.g. `YYYY-MM-DD`), **Date/Time Format** (e.g. `YYYY-MM-DD HH:mm:ss`), **Time Format** (e.g. `HH:mm:ss`), **Long Time Format** (e.g. `HH:mm:ss.SSS`), **Short Time Format** (e.g. `HH:mm`), **Timezone** (e.g. `Asia/Bangkok`). All are free-text inputs with placeholder hints. No dropdown or IANA picker.

### 4.6 Number Formats

Fields (2-column grid): **Per Page Format**, **Amount Format**, **Quantity Format**, **Recipe Format**. All stored as JSON strings in `formData` (typed `string` in `BusinessUnitFormData`) and edited as plain text inputs. Default values are the JSON object `{"locales":"th-TH","minimumIntegerDigits":2}` for amount/quantity/recipe, and `{"default":10}` for perpage. On save, `buildPayload` parses these strings back to objects before sending — a parse failure passes the raw string to the API. See [Data Model](./data-model.md) for the column types.

In view (read-only) mode these fields display via `ReadOnlyText` — the raw JSON string as stored, with no pretty-printing.

### 4.7 Calculation Settings

Fields (2-column grid): **Calculation Method** (`select` with options `average` / `fifo`, matching the `enum_calculation_method` values documented in [Data Model](./data-model.md)), **Default Currency ID** (free-text input accepting a UUID).

In view mode, when `defaultCurrency` data is present (fetched inline with the BU record), a read-only currency detail panel is shown below the two fields with sub-fields: Code, Name, Symbol, Decimal Places, Description, and an Active/Inactive badge. This panel is hidden in edit mode (the currency ID input is shown instead).

### 4.8 Configuration

The `config` column stores an array of `BusinessUnitConfig` entries (`{ key: string; label: string; datatype: string; value: unknown }`). This section renders the array differently depending on mode:

- **Edit mode** — each existing row is shown as an inline 5-column row (Key\*, Label\*, Data Type select, Value, Delete button). Supported Data Type options: `string`, `number`, `boolean`, `date`, `json`. An **Add Config Entry** button appends a blank row. The Delete button (Trash icon, destructive colour) removes the row from `formData.config` immediately with no confirmation. On save, `buildPayload` filters out rows where both `key` and `label` are empty before sending.
- **View mode** — rows are shown in a read-only `<table>` with columns Key, Label, Type, Value. If `config` is empty, a "No configuration entries." message is shown.

There is no separate dialog for adding/editing config rows — all editing is in-place within the section.

### 4.9 Database Connection

Field: **Connection Config** — a single `<pre>` element that shows the `db_connection` JSON string, pretty-printed (`JSON.stringify(JSON.parse(...), null, 2)`) when the string is valid JSON, or raw if not. Maximum height is 240 px with overflow scroll.

In view mode the background is `bg-muted/50`; in edit mode the background is `bg-transparent`. The field is rendered as a `<pre>` in both modes — there is no `<textarea>` or `Input` for `db_connection` in the current source. The value is editable only indirectly: `db_connection` is included in `formData` and in `buildPayload`, but the current UI does not render an editable input for it. The field can be populated from the initial `fetchBusinessUnit()` response and is submitted back as-is. Developers intending to update `db_connection` must currently use the API directly or a `textarea` field may need to be added.

## 5. Dialogs

### 5.1 Add User to BU dialog

**Trigger:** the **Add User** button (`UserPlus` icon) in the Users card header. Only available in view/edit mode (`!isNew`).

The dialog (`sm:max-w-lg`) loads the cluster's user list when `formData.cluster_id` is set and the response is not yet cached (`GET /api-system/user/cluster/:clusterId` via `clusterService.getClusterUsers`). It shows a scrollable list of cluster users not already in this BU (`availableClusterUsers` filter). A debounced inline search input filters the list client-side by `username`, `email`, and full name (first/middle/last from `userInfo`).

After selecting a user (click on a row), the selected-user display replaces the search list; an X button on the display card deselects and returns to the list.

Fields:
- **BU Role** — select from `BU_ROLES = ['admin', 'user']`. Default: `user`.

Note: there is no `is_default` checkbox in the Add User dialog. The `is_default` field on the `tb_user_tb_business_unit` join exists in the schema but is not exposed in the current UI.

On submit (clicking **Add User**, disabled until a user is selected and the request is not in flight), calls `POST /api-system/user/business-unit` with body `{ user_id, business_unit_id, role }`. On success, the dialog closes, a toast confirms, and `fetchBuUsers()` re-fetches the BU record to refresh the Users table.

### 5.2 Edit BU User dialog

**Trigger:** the **Edit** (Pencil) icon button on a user row in the Users table.

The dialog (`sm:max-w-md`) title is "Edit User in Business Unit". The description shows the user's `username` and display name (first/middle/last joined, falling back to `email`).

Editable fields:
- **BU Role** — select from `BU_ROLES` (`admin` / `user`). Pre-populated from `user.role`.
- **BU Status** — select `Active` / `Inactive`. Pre-populated from `user.is_active` (the `is_active` field on the BU-user join row, not the global user account status).

On submit, calls `PATCH /api-system/user/business-unit/:id` with body `{ role, is_active }`. On success, the local `buUsers` state is updated optimistically without a full re-fetch; a toast confirms.

### 5.3 Remove BU User confirm

**Trigger:** the **Delete** (Trash, destructive colour) icon button on a user row in the Users table.

Uses the shared `ConfirmDialog`. Title: "Remove User". Description: `Are you sure you want to remove "<display name>" from this business unit?` where display name resolves first/middle/last, then `username`, then `email`. Confirm button label: "Remove" (destructive variant). No typed confirmation required.

On confirm, calls `DELETE /api-system/user/business-unit/:id` (the `tb_user_tb_business_unit.id`, not the `user_id`). On success, the matching entry is removed from local `buUsers` state; a toast confirms.

### 5.4 Soft Delete BU confirm

**Trigger:** the **Delete** row action in `BusinessUnitManagement`.

Uses the shared `ConfirmDialog`. Title: "Delete Business Unit". Description: "Are you sure you want to delete this business unit? This action cannot be undone." Confirm button label: "Delete" (destructive variant). No hard-delete option exists anywhere in the BU management UI.

On confirm, calls `DELETE /api-system/business-unit/:id` (soft delete — sets `deleted_at`). On success, a toast confirms and the list re-fetches.

## 6. Persisted UI state

The list page writes 6 keys to `localStorage`. `BusinessUnitEdit` writes no `localStorage` keys.

| Key | Stored type | Persists |
|---|---|---|
| `search_business_units` | string | Current search term |
| `page_business_units` | number (string) | Current page number (reset to `1` on filter or search changes) |
| `perpage_business_units` | number (string) | Rows per page |
| `sort_business_units` | string | Current sort column/direction (default `created_at:desc`) |
| `filters_business_units` | JSON array | Active status filter values (e.g. `["true"]`, `["false"]`, `[]`) |
| `filter_business_units_deleted` | JSON boolean | "Show soft-deleted business units" toggle state (default `false`) |

Note: there is no `role_filters_business_units` key because business units do not carry a `platform_role` equivalent on the join row. The Users list has a 7th key (`role_filters_users`) for this purpose.

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References

- `../carmen-platform/SITEMAP.md` — three BU routes, all "Authenticated" (no `allowedRoles`), with note on `?cluster_id` query-param flow from cluster edit.
- `../carmen-platform/src/pages/BusinessUnitManagement.tsx` — list page: filters (Status + Deleted), header actions (Export, Add Business Unit), row actions (Edit / Delete soft), audit columns, 6 `localStorage` keys.
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx` — create/view/edit page: 9 `CollapsibleSection` form cards in a 2-column grid, Users card with Add/Edit/Remove user dialogs, `BU_ROLES` constant, `?cluster_id` query-param pre-select, license-limit pre-flight check on create.
- `../carmen-platform/src/services/businessUnitService.ts` — API surface: `GET /api-system/business-unit`, `POST /api-system/business-unit`, `PUT /api-system/business-unit/:id`, `DELETE /api-system/business-unit/:id`, `PATCH /api-system/user/business-unit/:id`, `POST /api-system/user/business-unit`, `DELETE /api-system/user/business-unit/:id`.
- Cross-links: [[business-units]] (module landing), [[clusters]] (parent cluster; source of `?cluster_id` navigate-to-new), [[users]] (other surface mutating `tb_user_tb_business_unit`), [Data Model](./data-model.md).
