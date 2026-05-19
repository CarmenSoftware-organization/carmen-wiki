---
title: Cluster — UI Screens
description: ClusterManagement (list) and ClusterEdit (create/view/edit) screens — layout, filters, dialogs, persisted state.
published: true
date: '2026-05-19T18:00:00.000Z'
tags: book/platform, clusters, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — UI Screens

> **At a Glance**
> **Screens:** `ClusterManagement` (list, `/clusters`) &nbsp;·&nbsp; `ClusterEdit` create (`/clusters/new`) &nbsp;·&nbsp; `ClusterEdit` view/edit (`/clusters/:id/edit`) &nbsp;·&nbsp; **Edit layout:** 3-column grid — Cluster Details (left, 1 col) + Business Units + Users (right, 2 cols) &nbsp;·&nbsp; **Dialogs:** Add User to Cluster · Edit Cluster User · Remove Cluster User confirm · Soft Delete Cluster confirm &nbsp;·&nbsp; **Access:** all three routes gated to `platform_admin`, `support_manager`, `support_staff` (see [Permissions](./permissions.md)) &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys on the list page

## 1. Overview

The Platform SPA follows a consistent two-screen pattern for cluster management: a list page (`ClusterManagement`) with a server-side `DataTable`, a slide-over filters Sheet, and two header action buttons; and an edit page (`ClusterEdit`) that starts in read-only view mode and transitions to an editable form on demand. Both screens are registered under the `/clusters` route prefix and are guarded by `allowedRoles: ['platform_admin', 'support_manager', 'support_staff']` — tighter than the user-management routes which allow any authenticated user.

The cluster edit page is the main structural difference from the analogous user edit page. Rather than a vertically stacked single-column layout, `ClusterEdit` renders a `grid-cols-1 lg:grid-cols-3` responsive grid once the cluster exists: the **Cluster Details** card occupies the left column (1 fractional unit); the **Business Units** card and **Users** card share the right column (2 fractional units, stacked vertically). In create mode (`isNew = true`) the grid collapses to a single Cluster Details card only — the BU and Users cards are hidden until the record is saved and the SPA navigates to `/clusters/:id/edit`. The Business Units card uses a navigate-to-create flow (`/business-units/new?cluster_id=<id>`) to pre-link a new BU to this cluster; the Users card has its own in-page **Add User to Cluster** dialog that searches the global user pool. Neither card on this page matches the pattern seen in `UserEdit` where BUs are added via an in-page dialog scoped to the user's existing cluster memberships.

## 2. `ClusterManagement` — list page (`/clusters`)

### 2.1 Layout

The page renders inside `Layout` with a two-row header: a title/subtitle row ("Cluster Management" / "Manage and configure clusters") and an actions row containing **Export** and **Add Cluster** buttons. Below the action row sits a search-and-filters row: a debounced (400 ms) search `Input` on the left, and a **Filters** Sheet trigger on the right (shows an active-filter count badge when any filter is set). Active filter chips appear as a strip below the search row when any filter is active. The main content area is a `DataTable` in server-side mode with pagination.

Columns in order: `code` (clickable link — navigates to `/clusters/:id/edit`), `name` (clickable link — also navigates to edit, with a red `Deleted` badge appended when `deleted_at` is non-null), `is_active` (Active/Inactive badge), `bu_count` (BU count, shown as `count / max` when `max_license_bu` is set, `-` when both are zero/null), `users_count` (user count, shown red when count ≥ `total_max_license_users`), `created_at` + `created_by_name`, `updated_at` + `updated_by_name` (suppressed when equal to `created_at`), and conditionally `deleted_at` + `deleted_by_name` in destructive red (appended only when the "Show soft-deleted" filter is active). The final column is an icon-button `DropdownMenu` for row actions.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet. Two filter groups are wired:

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). The two buttons may be toggled independently; when both are active or both are off, no `is_active` constraint is applied (the filter is elided from the query). A **Clear** link appears in the group header when any status value is selected.
- **Deleted** — a checkbox labelled "Show soft-deleted clusters". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface in the table with a red `Deleted` badge in the `name` cell, and the conditional `Deleted By` audit column is appended to the `DataTable`.

There is no Role filter group (unlike user management). When any filter is active a **Clear All Filters** button appears at the bottom of the Sheet, and active filter chips appear in the strip below the search row. Each chip has an inline remove button; a **Clear all** text link also clears all filters at once.

### 2.3 Header actions

Two buttons appear in the header actions row, left to right:

- **Export** — client-side CSV export using `generateCSV` / `downloadCSV` utilities. Exports the currently loaded page of rows with columns: `Code`, `Name`, `Alias`, `Status` (`is_active`), `Max Licensed BUs` (`max_license_bu`), `Users` (`users_count`), `Max Licensed Users` (`total_max_license_users`), `Created` (`created_at`). File name: `clusters-<YYYY-MM-DD>.csv`. The button is disabled while loading or when the table is empty.
- **Add Cluster** — navigates to `/clusters/new`.

There is no Fetch Keycloak button (that affordance exists only on the Users list). There is no Hard Delete action anywhere in cluster management — the `ClusterManagement.tsx` row action menu contains only **Edit** and **Delete** (soft). No hard-delete endpoint is called from the clusters UI.

### 2.4 Row actions

Each row has a `DropdownMenu` (⋯ icon button) with two items:

- **Edit** — navigates to `/clusters/:id/edit`.
- **Delete** — sets `deleteId` state; opens the Soft Delete Cluster `ConfirmDialog` (§5.4). On confirm, calls `DELETE /api-system/cluster/:id` (soft delete — sets `deleted_at`).

There is no **Hard Delete** option in the cluster row action menu. Hard deletion of cluster records is not exposed through the Platform SPA.

### 2.5 Audit columns

Two audit columns are always shown:

| Column header | Fields rendered |
|---|---|
| Created | `created_at` (formatted `YYYY-MM-DD HH:mm:ss`, browser local time) + `created_by_name` on the next line |
| Updated | `updated_at` + `updated_by_name` — suppressed (renders `null`) when `updated_at === created_at` |

When the "Show soft-deleted clusters" filter toggle is on, a third audit column is conditionally appended:

| Column header | Fields rendered |
|---|---|
| Deleted By | `deleted_at` + `deleted_by_name` (text in destructive red); shows `-` for non-deleted rows |

All timestamps are formatted in the browser's local timezone using JS `Date` — no UTC offset indicator is displayed. This matches the audit-column format used across all Platform SPA list pages.

## 3. `ClusterEdit` — create mode (`/clusters/new`)

In create mode (`isNew = true`) the page title is "Add Cluster" and the subtitle is "Create a new cluster". The page renders a single **Cluster Details** card (no grid, no BU card, no Users card). There is no Edit button in the header — the form is immediately editable.

The form contains six fields from `ClusterFormData`:

| Field | Input type | Required | Notes |
|---|---|---|---|
| `code` | text | Yes | Cluster short identifier. **Editable in create mode** — see §4.1 for edit-mode behaviour |
| `alias_name` | text | No | Max 3 characters (`maxLength={3}`). Used in compact UI surfaces |
| `name` | text | Yes | Full display name |
| `max_license_bu` | number | No | Leave blank for unlimited; placeholder text "Unlimited" |
| `logo_url` | url | No | When a valid URL is entered, a 40×40 px logo preview is shown below the input |
| `is_active` | checkbox | — | Defaults to `true` |

Submit button label: **Create Cluster**. On submit, calls `POST /api-system/cluster`. On success, if the response includes an `id`, navigates to `/clusters/:id` with `{ replace: true }` (so Back goes to the list, not the create form) — note the absence of the `/edit` suffix; this is a source divergence vs. the user create flow, which navigates to `/users/:id/edit` (the view/edit route `/clusters/:id/edit` is reached separately, see §4). If no `id` is returned, navigates to `/clusters`. **Cancel** navigates to `/clusters` without an API call.

## 4. `ClusterEdit` — view/edit mode (`/clusters/:id/edit`)

The page starts in **view mode** (`editing = false`). The title is "Cluster Details" and the subtitle is "View cluster information". A single **Edit** button appears in the header. Clicking **Edit** saves the current form state to `savedFormData`, sets `editing = true`, changes the title to "Edit Cluster" / "Update cluster information", and hides the Edit header button (Save Changes and Cancel buttons appear inside the Cluster Details form instead).

The layout is a 1:2 responsive grid (`grid-cols-1 lg:grid-cols-3` with the right column set to `lg:col-span-2`) — the Cluster Details card spans 1 column on the left, and the Business Units + Users cards stack vertically in the 2-column-wide right region. On smaller screens all three cards stack into a single column.

### 4.1 Cluster Details card (left column)

- **View mode**: all six fields rendered as read-only styled `div` containers. `max_license_bu` shows "Unlimited" when the field is empty. `is_active` shows an Active/Inactive badge.
- **Edit mode**: inputs become editable. **`code` is editable in edit mode** — the form does not disable the `code` field after creation (no `disabled={!isNew}` guard on the `code` input, unlike `username` on the user form). Developers should be aware that changing a cluster's code after creation is permitted by the UI despite the `@@unique([code, name, deleted_at])` constraint on the backend; a code change that conflicts with a live cluster will be rejected with an API error.
- **Save Changes** → `PUT /api-system/cluster/:id`; on success, `fetchCluster()` re-fetches the record and `setEditing(false)` returns to view mode.
- **Cancel** → restores `formData` from `savedFormData`, calls `setEditing(false)`. No API call.
- **Unsaved changes guard**: the `useUnsavedChanges` hook fires if the user attempts to navigate away while `editing = true` and `formData !== savedFormData`.

### 4.2 Business Units card (right column, top)

The Business Units card lists every `tb_business_unit` row whose `cluster_id` matches the current cluster, fetched from `GET /api-system/business-unit?perpage=-1` and filtered client-side on `bu.cluster_id === id`. Rows are sorted alphabetically by `name`. The card header shows an Active count badge and a total count; if `max_license_bu` is set, it also shows a "N of M licensed" indicator.

The card renders a plain `<table>` (not `DataTable`) with columns: **Code** (outline badge), **Name**, **Users** (count of `clusterUsers` where `parent_bu_id === bu.id`, shown as `count/max` when `bu.max_license_users` is set, red when at limit), **Status** (Active/Inactive badge), and a right-aligned **Edit** icon button.

Card header controls:
- **Refresh** (icon button) — re-calls `fetchBusinessUnits()`.
- **Add** button — navigates to `/business-units/new?cluster_id=<id>` ([[business-units]]). The `cluster_id` query parameter wires the new BU create form so it lands pre-linked to this cluster. The button is disabled and shows a "License limit reached" tooltip when `businessUnits.length >= max_license_bu`.

Row controls: the **Edit** icon button (Pencil) navigates to `/business-units/:buId/edit`. There is no Remove/Unlink button on BU rows — BU cluster membership is managed on the BU edit page. There is no in-place BU create dialog; the SPA always navigates away to the BU create route.

### 4.3 Users card (right column, bottom)

The Users card lists `tb_cluster_user` rows for this cluster, fetched from `GET /api-system/user/cluster/:id`. Rows are sorted by display name (first/middle/last name from `userInfo`, falling back to `email`), then by email. The card header shows an Active count badge and a total count; if any BU in the cluster has `max_license_users` set, it also shows a "N/M licensed" indicator in red when the count equals or exceeds the sum of BU license caps.

The card renders a `<table>` with columns: **Name** (clickable link — opens the Edit Cluster User dialog, §5.2), **Email**, **Parent Business Unit** (outline badge showing `code - name` from the matched BU, or `-`), **Platform Role** (outline badge showing `platform_role` or, if absent, the cluster `role` — the `platform_role` shown here is the joined user's `tb_user.platform_role` denormalized into the API response; it does not live on the `tb_cluster_user` join row, which stores only `role`; it is distinct from the sign-in `platform_role` on the `tb_user` record documented in [[users]]; the fallback to `role` handles API responses where the user's platform role is not yet populated), **Status** (Active/Inactive badge), and a right-aligned **Remove** icon button (Trash, destructive colour).

Card header controls:
- **Refresh** (icon button) — re-calls `fetchClusterUsers()`.
- **Add User** button — opens the Add User to Cluster dialog (§5.1).

## 5. Dialogs

### 5.1 Add User to Cluster dialog

Triggered by the **Add User** button in the Users card header on `/clusters/:id/edit`.

The dialog searches the global user pool ([[users]], `GET /api-system/user` via `userService.getAll`) with a 400 ms debounced search input. Search fields: `username`, `email`, `firstname`, `lastname`. Results are paginated at 10 per page with infinite-scroll load-more (triggered by scrolling to within 40 px of the bottom of the results list). Users already in this cluster are excluded from the results (`availableUsers` filter). Selecting a user shows a confirmation card with `username`, `email`, and full name; clicking the X on that card deselects and returns to the search list.

Fields after a user is selected:
- **Cluster Role** — select populated from `CLUSTER_ROLES = ['admin', 'user']`. Default: `user`.
- **Business Unit** — select populated from the cluster's current BUs (all BUs, not filtered by active status). Shows `code - name (count/max users)` per option; options are disabled when their BU is at `max_license_users` limit. Empty default: "Select business unit" (the BU assignment is optional).

The **Add User** button is disabled when: no user is selected, the request is in flight (`addingUser`), or the selected BU is at its user license limit. On submit, calls `POST /api-system/user/cluster` with body `{ user_id, cluster_id, role, is_active: true }` (plus `parent_bu_id` if a BU was selected). On success, dialog closes, a toast confirms, and `fetchClusterUsers()` re-fetches.

### 5.2 Edit Cluster User dialog

Triggered by clicking the user's **Name** (link text) in the Users card table row.

The dialog title is "Edit Cluster User". The description shows the user's display name (first/middle/last from `userInfo`, falling back to `email`).

Editable fields:
- **Cluster Role** — select from `CLUSTER_ROLES` (`admin` / `user`). Pre-populated from the existing `role`.
- **Parent Business Unit** — select populated from the cluster's BUs. Pre-populated from the existing `parent_bu_id`. Options are disabled when at `max_license_users` limit, with an exception: the user's **current** BU is never disabled (the `isCurrentBu` guard prevents the current assignment from being blocked by its own occupancy).

On submit, calls `PUT /api-system/user/cluster/:clusterUserId` with body `{ role, parent_bu_id }`. On success, toast confirms and `fetchClusterUsers()` re-fetches. The **Save** button shows a spinner while `savingClusterUser` is true.

### 5.3 Remove Cluster User confirm

Triggered by the **Trash** icon button on a Users card row.

Uses the shared `ConfirmDialog` component — a simple Yes/No confirm (no typed confirmation required). Title: "Remove User from Cluster". Description: `Are you sure you want to remove "<display name>" from this cluster?` where the display name is resolved from `userInfo` first/middle/last, falling back to `username` then `email`. Note: the Remove confirm uses `username` as an intermediate fallback before `email`; this differs from the Edit Cluster User dialog (§5.2), which goes directly from `userInfo` to `email` with no `username` step.

On confirm, calls `DELETE /api-system/user/cluster/:clusterUserId` using the `tb_cluster_user.id` field returned by the cluster users endpoint. On success, toast confirms and `fetchClusterUsers()` re-fetches.

### 5.4 Soft Delete Cluster confirm

Triggered by the **Delete** row action in `ClusterManagement`.

Uses the shared `ConfirmDialog` — a simple Yes/No confirm (no typed confirmation required). Title: "Delete Cluster". Description: "Are you sure you want to delete this cluster? This action cannot be undone." Confirm button label: "Delete" (destructive variant).

On confirm, calls `DELETE /api-system/cluster/:id` (soft delete — sets `deleted_at`). No hard-delete dialog exists for clusters in the Platform SPA.

## 6. Persisted UI state

The list page writes 6 keys to `localStorage` so that filter and pagination state survives page reloads. The `ClusterEdit` page writes no `localStorage` keys.

| Key | Stored type | Persists |
|---|---|---|
| `search_clusters` | string | Current search term |
| `page_clusters` | number (string) | Current page number (reset to `1` on filter or search changes) |
| `perpage_clusters` | number (string) | Rows per page |
| `sort_clusters` | string | Current sort column/direction (default `created_at:desc`) |
| `filters_clusters` | JSON array | Active status filter values (e.g. `["true"]`, `["false"]`, `[]`) |
| `filter_clusters_deleted` | JSON boolean | "Show soft-deleted clusters" toggle state (default `false`) |

Note: the clusters list does **not** persist a `role_filters_clusters` key because there is no role filter group on this page (clusters carry no `platform_role` equivalent). This is a meaningful absence vs. the 7-key users list which persists `role_filters_users`.

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References

- `../carmen-platform/SITEMAP.md` — route table confirming three cluster routes, all restricted to `platform_admin`, `support_manager`, `support_staff`.
- `../carmen-platform/src/pages/ClusterManagement.tsx` — list page: filters (Status + Deleted), header actions (Export, Add Cluster), row action menu (Edit / Delete soft), audit columns, 6 `localStorage` keys.
- `../carmen-platform/src/pages/ClusterEdit.tsx` — create/view/edit page: 3-column grid layout, Cluster Details form (6 fields, `code` editable in edit mode), Business Units table (navigate-to-new flow), Users table (Add/Edit/Remove user dialogs), `CLUSTER_ROLES` constant.
- `../carmen-platform/src/services/clusterService.ts` — API surface: `GET /api-system/cluster`, `POST /api-system/cluster`, `PUT /api-system/cluster/:id`, `DELETE /api-system/cluster/:id`, `GET /api-system/user/cluster/:clusterId`.
- Cross-links: [[clusters]] (module landing), [[users]] (global user pool searched by Add User dialog; `tb_cluster_user` doc), [[business-units]] (Add BU navigate-to-new flow; `cluster_id` FK), [Data Model](./data-model.md), [Permissions](./permissions.md).
