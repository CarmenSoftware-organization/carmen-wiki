---
title: User — UI Screens
description: UserManagement (list) and UserEdit (BU assignment matrix).
published: true
date: 2026-06-10T14:00:00.000Z
tags: book/platform, users, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — UI Screens

> **At a Glance**
> **Screens:** `UserManagement` (list, `/users`) &nbsp;·&nbsp; `UserEdit` create (`/users/new`) &nbsp;·&nbsp; `UserEdit` view/edit (`/users/:id/edit`) &nbsp;·&nbsp; **Dialogs:** Add BU &nbsp;·&nbsp; Change Password &nbsp;·&nbsp; Soft Delete confirm &nbsp;·&nbsp; Hard Delete typed-confirm &nbsp;·&nbsp; **Access:** routes guarded `user.read` / `user.create` / `user.update`; in-page `<Can>` gates on Add (`user.create`), Edit (`user.update`), Delete/Hard-Delete (`user.delete`) &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys on the list page

## 1. Overview

The Platform SPA follows a consistent two-screen pattern for every admin entity: a list page (`UserManagement`) with a server-side `DataTable`, filters in a slide-over Sheet, and header action buttons; and an edit page (`UserEdit`) that starts in read-only view mode and transitions to an editable form on demand. The three routes under the `/users` prefix carry `requiredPermission` guards (`user.read` / `user.create` / `user.update`), and individual mutating buttons are wrapped in `<Can>` gates — none of which pass a `clusterId`, unlike the Clusters/Business Units pages. See [Platform RBAC — Permissions](/en/platform/rbac/permissions) for how the gates compose.

Users carry two additions not found on simpler entities. First, the list page exposes a **Fetch Keycloak** button that pulls user records from the Keycloak identity provider into the platform database — a sync operation specific to this module. Second, the view/edit page exposes a **Change Password** button (view mode header only) and, within the Business Units card, an **Add BU** button (visible only when the user already belongs to at least one cluster), allowing an admin to assign additional BU memberships without navigating away.

## 2. `UserManagement` — list page (`/users`)

### 2.1 Layout

The page renders inside `Layout`, under a two-row header: a title/subtitle row and an actions row. Below the action buttons sits a search-and-filters row: debounced search input on the left, Filters button (opens a Sheet) on the right. Active filter badges are shown as a chip strip when any filter is set. The main content area is a `DataTable` component operating in server-side mode, with built-in pagination controls.

Columns in order: avatar (see below), `username` (clickable — navigates to edit), `name` (composed by the `getNameDisplay` helper: the non-empty parts of `firstname`/`middlename`/`lastname` joined with spaces, falling back to the flat `name` field, then `-`), `email`, `BU` (active/total count), `is_active` (Active/Inactive badge), `created_at` + `created_by_name`, `updated_at` + `updated_by_name`, and conditionally `deleted_at` + `deleted_by_name` (see §2.5). The final column is an icon-button row action menu. The legacy `platform_role` badge column is gone with the role enum.

The **avatar column** renders a small circular `Avatar` (`h-8 w-8`): an `AvatarFallback` shows initials (first letters of `firstname` + `lastname`; if both are empty, the first two characters of `name`/`username`/`email`; else `?`), and when the record carries a presigned `avatar_url` an `AvatarImage` is layered on top, hiding itself again on load error so the initials show through.

When a row is soft-deleted (visible only with the "Show soft-deleted users" filter on), the Name cell additionally renders a red "Deleted" badge whose `title` tooltip reads "Deleted by &lt;deleted_by_name&gt;" when that name is present.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet. Two filter groups are available (the legacy Role filter was removed along with the role enum — status is now the only field filter):

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). No tri-state "all" option; clearing both buttons removes the filter entirely — both off is equivalent to no status constraint (all rows shown). A **Clear** link appears when any status is selected.
- **Deleted** — a checkbox labelled "Show soft-deleted users". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface in the table with a red `Deleted` badge beside the user's name.

When any filter is active, a **Clear All Filters** button appears at the bottom of the Sheet, and active filter chips appear in the strip below the header.

### 2.3 Header actions

Three buttons appear in the header actions row, left to right:

- **Fetch Keycloak** — calls `userService.fetchKeycloakUsers()` → `POST /api-system/fetch-user`. A spinner replaces the icon while the request is in flight; on success a toast confirms the sync and the table reloads via a paginate-state bump. Not `<Can>`-gated.
- **Export** — client-side CSV export (uses `generateCSV` / `downloadCSV` utilities). Exports the currently loaded page of rows with columns: `username`, `email`, `is_active`, `created_at`. The button is disabled while loading or when the table is empty. File name: `users-<YYYY-MM-DD>.csv`. Not `<Can>`-gated.
- **Add User** — navigates to `/users/new`. Wrapped in `<Can permission="user.create">`. Note: the empty-state's "Add User" shortcut (shown when the table has no rows and no search term) is **not** wrapped in `<Can>` — it renders for any `user.read` session, though the `/users/new` route guard still blocks navigation without `user.create`.

### 2.4 Row actions

Each row has a `DropdownMenu` (⋯ icon button) with three items, each wrapped in a `<Can>` gate (no `clusterId` is passed):

- **Edit** (`<Can permission="user.update">`) — navigates to `/users/:id/edit`.
- **Delete** (`<Can permission="user.delete">`) — sets `deleteId` state; triggers the `ConfirmDialog` (§5.3). Submit calls `DELETE /api-system/user/:id`.
- **Hard Delete** (also `<Can permission="user.delete">`, separated by a `DropdownMenuSeparator` inside the same gate) — sets `hardDeleteUser` state; opens the typed-confirmation Dialog (§5.4).

A session holding only `user.read` sees an empty dropdown — the gates remove the items entirely rather than disabling them.

### 2.5 Audit columns

Two audit columns are always shown:

| Column header | Fields rendered |
|---|---|
| Created | `created_at` (formatted `YYYY-MM-DD HH:mm:ss`, local time) + `created_by_name` on the next line |
| Updated | `updated_at` + `updated_by_name` — suppressed (returns `null`) when `updated_at === created_at` |

The fields feeding these columns are flattened in `fetchUsers`: the API now groups audit data under a nested `audit` object, and the mapping tolerates both shapes with the flat fields winning when present (`item.created_at ?? item.audit?.created?.at`, and likewise for `updated`/`deleted` and the `_by_name` actor fields — commits `f9b61cb`, `30b5bd6`).

When the "Show soft-deleted users" filter toggle is on, a third audit column is appended:

| Column header | Fields rendered |
|---|---|
| Deleted By | `deleted_at` + `deleted_by_name` (text in destructive red); shows `-` for non-deleted rows |

All timestamps are formatted in the browser's local timezone using JS `Date` — no UTC offset indicator is displayed.

## 3. `UserEdit` — create mode (`/users/new`)

The create mode renders a single **User Details** card. The page title is "Add User" and the subtitle is "Create a new user". There is no Clusters card, no Business Units card, and no Change Password or Edit buttons in the header — these only appear after the record is saved.

The editable form contains the seven fields from `UserFormData`, laid out in a two-column grid in this order:

| Field | Input type | Notes |
|---|---|---|
| `username` | text | Required; `disabled={!isNew}` — editable here, disabled on edit |
| `email` | email | Required |
| `alias_name` | text | Optional |
| `firstname` | text | Optional |
| `lastname` | text | Optional — note the form places Last Name before Middle Name |
| `middlename` | text | Optional |
| `is_active` | checkbox | Defaults to `true` |

There is no `password` field on the create form — credentials are set later via the Change Password admin-reset dialog or via Keycloak — and no access/role field: the legacy `platform_role` select was removed with the RBAC migration. Granting Platform admin access is a separate step on `/platform/user-platform` (see [Platform RBAC](/en/platform/rbac)).

Submit calls `POST /api-system/user`. On success, if the response includes an `id`, the page redirects to `/users/:id/edit` with `{ replace: true }` (so Back goes to the list, not the create form). If no `id` is returned, it redirects to `/users`.

## 4. `UserEdit` — view/edit mode (`/users/:id/edit`)

The page starts in **view mode** (`editing = false`). Between the back button and the title sits the user's **avatar** (`h-12 w-12` — larger than the list's `h-8 w-8`): initials fallback from `firstname`/`lastname` (else the first two characters of username/email), with the presigned `avatar_url` image layered on top when present (loaded as `user.avatar_url || profile.avatar_url`, hidden again on load error). The title is "User Details"; the header shows two buttons: **Change Password** (not `<Can>`-gated) and **Edit** (wrapped in `<Can permission="user.update">` — redundant in practice with the route's own `user.update` guard, but consistent with the other modules' edit pages). Clicking **Edit** sets `editing = true`, saves the current form state to `savedFormData`, changes the title to "Edit User", and hides the Change Password and Edit buttons (Save and Cancel buttons appear inside the form instead).

Three cards are stacked vertically (Clusters and Business Units cards are hidden in create mode).

### 4.1 User Details card

- **View mode**: all seven fields rendered as read-only styled `div` containers.
- **Edit mode**: inputs become editable. `username` is always `disabled={!isNew}` and cannot be changed after creation.
- **Save Changes** → `PUT /api-system/user/:id`; on success, `fetchUser()` re-fetches and `setEditing(false)` returns to view mode.
- **Cancel** → restores `formData` from `savedFormData`, calls `setEditing(false)`. No API call.

### 4.2 Clusters card (read-only)

Displays each `tb_cluster_user` row as a small card in a responsive grid (1 / 2 / 3 columns). Each card shows: cluster name (linked to `/clusters/:id`), cluster code, active/inactive badge, and the per-cluster role badge (`admin` or `user`). The card header shows a count of active vs. total clusters.

There is no Add/Remove control for clusters on this page. Cluster membership is managed on the cluster edit page.

### 4.3 Business Units card

Displays each `tb_user_tb_business_unit` row as a small card in a responsive grid. Each card shows: BU name (linked to `/business-units/:id/edit`), BU code, active/inactive badge, per-BU role badge, a `Default` badge (blue outline) if `is_default` is set, and a Trash icon button to remove the assignment. Below the BU name, the parent cluster name is shown (looked up from `userClusters`).

The card header shows a count of active vs. total BU assignments. The **Add BU** button appears in the card header only when `userClusters.length > 0` — a user with no cluster membership cannot be assigned a BU. Neither Add BU nor the per-row Trash button carries a `<Can>` gate; they render for anyone who passes the route's `user.update` guard.

## 5. Dialogs

### 5.1 Add BU dialog

Triggered by the **Add BU** button in the Business Units card header on `/users/:id/edit`.

Fields in the dialog:

1. **Cluster** — select populated from `userClusters` (the user's existing cluster memberships). Choosing a cluster triggers an API call (`GET /api-system/business-units?...&advance={"where":{"cluster_id":"..."}}` — the BU endpoint is plural) to load the BUs for that cluster.
2. **Business Unit** — select populated from the cluster's BUs, filtered to exclude BUs the user is already assigned to (`availableBUs`). Shown only after a cluster is selected.
3. **BU Role** — select with values `Admin` and `User`.

There is no `is_default` checkbox in this dialog. The `is_default` field is shown on existing BU assignment cards but is not set during the Add BU flow. No Platform admin SPA surface currently sets `is_default`; the flag is writable only at the backend API or DB level.

Submit: `businessUnitService.createUserBusinessUnit({ user_id, business_unit_id, role })` → `POST /api-system/user/business-units`. On success, dialog closes, a toast confirms, and `fetchUser()` re-fetches. The **Add** button is disabled while the request is in flight or if no BU has been selected. (Removal via the trash icon calls `deleteUserBusinessUnit(id)` → `DELETE /api-system/user/business-units/:id`.)

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

The list page writes 6 keys to `localStorage` so the filter and pagination state survives page reloads (the legacy `role_filters_users` key went away with the role filter). The edit page writes no `localStorage` keys.

| Key | Stored type | Persists |
|---|---|---|
| `search_users` | string | Current search term |
| `page_users` | number (string) | Current page number (reset to `1` on filter changes) |
| `perpage_users` | number (string) | Rows per page |
| `sort_users` | string | Current sort column/direction |
| `status_filters_users` | JSON array | Active status filter values (`["true"]` / `["false"]` / `[]`) |
| `filter_users_deleted` | JSON boolean | Show soft-deleted toggle state |

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References

- `../carmen-platform/src/App.tsx` — `requiredPermission` guards on the three user routes (lines 132–155). (`SITEMAP.md` still shows the pre-RBAC "Authenticated" rows and lags the code.)
- `../carmen-platform/src/pages/UserManagement.tsx` — list page: avatar column (`getInitials`), `getNameDisplay`, filters, header actions (Fetch Keycloak, Export, `<Can>`-gated Add User), `<Can>`-gated row action menu (Edit / Delete / Hard Delete), nested-`audit` flattening, audit columns, `localStorage` keys.
- `../carmen-platform/src/pages/UserEdit.tsx` — create/view/edit page: header avatar, three-card layout, `<Can>`-gated Edit toggle, Add BU dialog, Change Password dialog, `username` disabled-in-edit behaviour.
- `../carmen-platform/src/services/userService.ts` — API surface: all endpoints referenced in this page.
- Cross-links: [users](/en/platform/users) (landing), [Data Model](./data-model.md) (schema view), [Lifecycle](./lifecycle.md) (operations view), [rbac permissions](/en/platform/rbac/permissions) (gate composition), [clusters](/en/platform/clusters) (mutates `tb_cluster_user`), [business-units](/en/platform/business-units) (the other surface mutating `tb_user_tb_business_unit`).
