---
title: User — UI Screens
description: UserManagement (list) and UserEdit (BU assignment matrix).
published: true
date: '2026-05-19T15:00:00.000Z'
tags: book/platform, users, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — UI Screens

> **At a Glance**
> **Screens:** `UserManagement` (list, `/users`) &nbsp;·&nbsp; `UserEdit` create (`/users/new`) &nbsp;·&nbsp; `UserEdit` view/edit (`/users/:id/edit`) &nbsp;·&nbsp; **Dialogs:** Add BU &nbsp;·&nbsp; Change Password &nbsp;·&nbsp; Soft Delete confirm &nbsp;·&nbsp; Hard Delete typed-confirm &nbsp;·&nbsp; **Access:** all three routes "Authenticated" — no `allowedRoles` prop &nbsp;·&nbsp; **Persisted UI state:** 7 `localStorage` keys on the list page

## 1. Overview

The Platform SPA follows a consistent two-screen pattern for every admin entity: a list page (`UserManagement`) with a server-side `DataTable`, filters in a slide-over Sheet, and header action buttons; and an edit page (`UserEdit`) that starts in read-only view mode and transitions to an editable form on demand. Both screens are registered under the `/users` route prefix and require only the generic "Authenticated" guard — no role restriction is applied at the router level.

Users carry two additions not found on simpler entities. First, the list page exposes a **Fetch Keycloak** button that pulls user records from the Keycloak identity provider into the platform database — a sync operation specific to this module. Second, the view/edit page exposes a **Change Password** button (view mode header only) and, within the Business Units card, an **Add BU** button (visible only when the user already belongs to at least one cluster), allowing an admin to assign additional BU memberships without navigating away.

## 2. `UserManagement` — list page (`/users`)

### 2.1 Layout

The page renders inside `Layout`, under a two-row header: a title/subtitle row and an actions row. Below the header, active filter badges are shown as a chip strip when any filter is set. The main content area is a `DataTable` component operating in server-side mode, with built-in pagination controls.

Columns in order: `username` (clickable — navigates to edit), `name` (computed from `firstname + middlename + lastname`, falls back to `name`), `email`, `platform_role` (badge), `BU` (active/total count), `is_active` (Active/Inactive badge), `created_at` + `created_by_name`, `updated_at` + `updated_by_name`, and conditionally `deleted_at` + `deleted_by_name` (see §2.5). The final column is an icon-button row action menu.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet. Three filter groups are available:

- **Role** — toggle buttons for each of the seven `PLATFORM_ROLES` values (`super_admin`, `platform_admin`, `support_manager`, `support_staff`, `security_officer`, `integration_developer`, `user`). Multiple values can be active simultaneously; the query uses an `{ in: [...] }` operator. A **Clear** link appears when any role is selected.
- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). No tri-state "all" option; clearing both buttons removes the filter entirely.
- **Deleted** — a checkbox labelled "Show soft-deleted users". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface in the table with a red `Deleted` badge beside the user's name.

When any filter is active, a **Clear All Filters** button appears at the bottom of the Sheet, and active filter chips appear in the strip below the header.

### 2.3 Header actions

Three buttons appear in the header actions row, left to right:

- **Fetch Keycloak** — calls `userService.fetchKeycloakUsers()` → `POST /api-system/fetch-user`. A spinner replaces the icon while the request is in flight; on success a toast confirms the sync and the table reloads via a paginate-state bump.
- **Export** — client-side CSV export (uses `generateCSV` / `downloadCSV` utilities). Exports the currently loaded page of rows with columns: `username`, `email`, `platform_role`, `is_active`, `created_at`. The button is disabled while loading or when the table is empty. File name: `users-<YYYY-MM-DD>.csv`.
- **Add User** — navigates to `/users/new`.

The search input (debounced via `setTimeout` at ~300 ms) and the **Filters** Sheet trigger are in a second row below the header buttons. Active filter chip badges with per-chip remove buttons appear below that row when any filter is set.

### 2.4 Row actions

Each row has a `DropdownMenu` (⋯ icon button) with three items:

- **Edit** — navigates to `/users/:id/edit`.
- **Delete** — sets `deleteId` state; triggers the `ConfirmDialog` (§5.3). Submit calls `DELETE /api-system/user/:id`.
- **Hard Delete** (separated by a `DropdownMenuSeparator`) — sets `hardDeleteUser` state; opens the typed-confirmation Dialog (§5.4).

### 2.5 Audit columns

Two audit columns are always shown:

| Column header | Fields rendered |
|---|---|
| Created | `created_at` (formatted `YYYY-MM-DD HH:mm:ss`, local time) + `created_by_name` on the next line |
| Updated | `updated_at` + `updated_by_name` — suppressed (returns `null`) when `updated_at === created_at` |

When the "Show soft-deleted users" filter toggle is on, a third audit column is appended:

| Column header | Fields rendered |
|---|---|
| Deleted By | `deleted_at` + `deleted_by_name` (text in destructive red); shows `-` for non-deleted rows |

All timestamps are formatted in the browser's local timezone using JS `Date` — no UTC offset indicator is displayed.

## 3. `UserEdit` — create mode (`/users/new`)

The create mode renders a single **User Details** card. The page title is "Add User" and the subtitle is "Create a new user". There is no Clusters card, no Business Units card, and no Change Password or Edit buttons in the header — these only appear after the record is saved.

The editable form contains the eight fields from `UserFormData`:

| Field | Input type | Notes |
|---|---|---|
| `username` | text | Required; `disabled={!isNew}` — editable here, disabled on edit |
| `email` | email | Required |
| `platform_role` | select | Dropdown over the seven `PLATFORM_ROLES` values |
| `alias_name` | text | Optional |
| `firstname` | text | Optional |
| `middlename` | text | Optional |
| `lastname` | text | Optional |
| `is_active` | checkbox | Defaults to `true` |

There is no `password` field on the create form. Credentials are set later via the Change Password admin-reset dialog or via Keycloak.

Submit calls `POST /api-system/user`. On success, if the response includes an `id`, the page redirects to `/users/:id/edit` with `{ replace: true }` (so Back goes to the list, not the create form). If no `id` is returned, it redirects to `/users`.

## 4. `UserEdit` — view/edit mode (`/users/:id/edit`)

The page starts in **view mode** (`editing = false`). The title is "User Details"; the header shows two buttons: **Change Password** and **Edit**. Clicking **Edit** sets `editing = true`, saves the current form state to `savedFormData`, changes the title to "Edit User", and hides the Change Password and Edit buttons (Save and Cancel buttons appear inside the form instead).

Three cards are stacked vertically (Clusters and Business Units cards are hidden in create mode).

### 4.1 User Details card

- **View mode**: all eight fields rendered as read-only styled `div` containers.
- **Edit mode**: inputs become editable. The `username` field is **disabled** (`disabled={!isNew}`, which is `false` for edit mode), so `username` cannot be changed after creation.
- **Save Changes** → `PUT /api-system/user/:id`; on success, `fetchUser()` re-fetches and `setEditing(false)` returns to view mode.
- **Cancel** → restores `formData` from `savedFormData`, calls `setEditing(false)`. No API call.

### 4.2 Clusters card (read-only)

Displays each `tb_cluster_user` row as a small card in a responsive grid (1 / 2 / 3 columns). Each card shows: cluster name (linked to `/clusters/:id`), cluster code, active/inactive badge, and the per-cluster role badge (`admin` or `user`). The card header shows a count of active vs. total clusters.

There is no Add/Remove control for clusters on this page. Cluster membership is managed on the cluster edit page.

### 4.3 Business Units card

Displays each `tb_user_tb_business_unit` row as a small card in a responsive grid. Each card shows: BU name (linked to `/business-units/:id/edit`), BU code, active/inactive badge, per-BU role badge, a `Default` badge (blue outline) if `is_default` is set, and a Trash icon button to remove the assignment. Below the BU name, the parent cluster name is shown (looked up from `userClusters`).

The card header shows a count of active vs. total BU assignments. The **Add BU** button appears in the card header only when `userClusters.length > 0` — a user with no cluster membership cannot be assigned a BU.

## 5. Dialogs

### 5.1 Add BU dialog

Triggered by the **Add BU** button in the Business Units card header on `/users/:id/edit`.

Fields in the dialog:

1. **Cluster** — select populated from `userClusters` (the user's existing cluster memberships). Choosing a cluster triggers an API call (`GET /api-system/business-unit?...&advance={"where":{"cluster_id":"..."}}`) to load the BUs for that cluster.
2. **Business Unit** — select populated from the cluster's BUs, filtered to exclude BUs the user is already assigned to (`availableBUs`). Shown only after a cluster is selected.
3. **BU Role** — select with values `Admin` and `User`.

There is no `is_default` checkbox in this dialog. The `is_default` field is shown on existing BU assignment cards but is not set during the Add BU flow.

Submit: `businessUnitService.createUserBusinessUnit({ user_id, business_unit_id, role })`. On success, dialog closes, a toast confirms, and `fetchUser()` re-fetches. The **Add** button is disabled while the request is in flight or if no BU has been selected.

### 5.2 Change Password dialog

Triggered by the **Change Password** button visible in the `/users/:id/edit` header when in view mode.

Fields:

- **New Password** (password input) — required; validated: min 6 characters.
- **Confirm Password** (password input) — required; must match New Password.

Validation is performed client-side on submit (not on blur). Error messages are shown inline above the form.

Submit: `PUT /api-system/user/:id/reset-password` with body `{ newPassword }`. On success, dialog closes and a toast confirms — there is no profile re-fetch and no `AuthContext` refresh. The **Update Password** button shows a spinner while the request is in flight.

### 5.3 Soft Delete confirm

Triggered by **Delete** in the row action menu on `UserManagement`.

Uses the shared `ConfirmDialog` component — a simple Yes/No dialog. Title: "Delete User". Description: "Are you sure you want to delete this user? This action cannot be undone." Confirm button label: "Delete" (destructive variant). No typed confirmation required.

Submit: `DELETE /api-system/user/:id` (soft delete — sets `deleted_at`).

### 5.4 Hard Delete confirm

Triggered by **Hard Delete** in the row action menu on `UserManagement`.

A custom `Dialog` (not the shared `ConfirmDialog`). Title: "Permanently Delete User" with a destructive alert icon. The dialog displays the target user's `username || email` (with full name below) in a highlighted info box, then prompts the operator to type that value into an input field.

The **Permanently Delete** button stays disabled until `hardDeleteConfirm === (hardDeleteUser?.username || hardDeleteUser?.email || '')`. The fallback to `email` applies when `username` is absent or empty.

Submit: `DELETE /api-system/user/:id/hard`. The dialog cannot be closed while the delete request is in flight (`hardDeleting = true`).

## 6. Persisted UI state

The list page writes 7 keys to `localStorage` so the filter and pagination state survives page reloads. The edit page writes no `localStorage` keys.

| Key | Type | Persists |
|---|---|---|
| `search_users` | string | Current search term |
| `page_users` | number (string) | Current page number (reset to `1` on filter changes) |
| `perpage_users` | number (string) | Rows per page |
| `sort_users` | string | Current sort column/direction |
| `role_filters_users` | JSON array | Active role filter values |
| `status_filters_users` | JSON array | Active status filter values (`["true"]` / `["false"]` / `[]`) |
| `filter_users_deleted` | JSON boolean | Show soft-deleted toggle state |

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References

- `../carmen-platform/SITEMAP.md` — route table confirming three user routes, all "Authenticated".
- `../carmen-platform/src/pages/UserManagement.tsx` — list page: filters, header actions (Fetch Keycloak, Export, Add User), row action menu (Edit / Delete / Hard Delete), audit columns, `localStorage` keys.
- `../carmen-platform/src/pages/UserEdit.tsx` — create/view/edit page: three-card layout, Add BU dialog, Change Password dialog, `username` disabled-in-edit behaviour.
- `../carmen-platform/src/services/userService.ts` — API surface: all endpoints referenced in this page.
- Cross-links: [[users]] (landing), [Data Model](./data-model.md) (schema view), [Lifecycle](./lifecycle.md) (operations view), [[clusters]] (mutates `tb_cluster_user`), [[business-units]] (the other surface mutating `tb_user_tb_business_unit`).
