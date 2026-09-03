---
title: User — UI Screens
description: UserManagement (list) and UserEdit (BU assignment matrix).
published: true
date: 2026-07-29T07:06:05.000Z
tags: book/platform, users, ui
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — UI Screens

> **At a Glance**
> **Screens:** `UserManagement` (list, `/users`) &nbsp;·&nbsp; `UserEdit` create (`/users/new`) &nbsp;·&nbsp; `UserEdit` view/edit (`/users/:id/edit`) &nbsp;·&nbsp; **New since last sync:** `UserDirectorySummary` strip (list), `UserIdentityHero` + merged `UserAccessTree` card (edit page, replacing the separate Clusters/Business Units cards), a BU-count list column, super-admin bulk soft/hard-delete, `doc_version` optimistic locking, not-found gating &nbsp;·&nbsp; **Dialogs:** Add BU &nbsp;·&nbsp; Change Password &nbsp;·&nbsp; Soft Delete confirm (single + bulk) &nbsp;·&nbsp; Hard Delete typed-confirm (single + bulk random-code) &nbsp;·&nbsp; **Access:** routes guarded `user.read` / `user.create` / `user.update`; in-page `<Can>` gates on Add (`user.create`), Fetch Keycloak (`user.create`, newly gated), Edit (`user.update`), Delete/Hard-Delete (`user.delete`); Add/Remove BU now resolve `cluster.update` per-cluster &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys on the list page

## 1. Overview

The Platform SPA follows a consistent two-screen pattern for every admin entity: a list page (`UserManagement`) with a server-side `DataTable`, filters in a slide-over Sheet, and header action buttons; and an edit page (`UserEdit`) that starts in read-only view mode and transitions to an editable form on demand — this module, unlike [clusters](/en/platform/clusters)/[business-units](/en/platform/business-units), kept the view/edit toggle rather than moving to a one-document always-editable page. The three routes under the `/users` prefix carry `requiredPermission` guards (`user.read` / `user.create` / `user.update`), and individual mutating buttons are wrapped in `<Can>` gates — none of which pass a `clusterId` at the route/row level, unlike the Clusters/Business Units pages (the two BU-assignment actions inside the Access card are the exception — see §4.2). See [Platform RBAC — Permissions](/en/platform/rbac/permissions) for how the gates compose.

Users carry several additions not found on simpler entities. The list page exposes a **Fetch Keycloak** button that pulls user records from the Keycloak identity provider into the platform database (now gated `<Can permission="user.create">`, corrected since the last sync) and a **Directory** summary strip (`UserDirectorySummary`, §2.1a). The view/edit page exposes a **Change Password** button (now living in the `UserIdentityHero`'s actions slot, view mode only) and, within the merged Access card, an **Add BU** button gated by a real per-cluster permission check (`canAddBU`, §4.2) rather than merely "the user belongs to at least one cluster." For super-admin sessions, the list page also offers bulk soft/hard delete (§2.4a).

## 2. `UserManagement` — list page (`/users`)

### 2.1 Layout

The page renders inside `Layout`, under a two-row header: a title/subtitle row and an actions row. Below the header sits the **Directory** summary card (§2.1a), then a search-and-filters row: debounced search input on the left, Filters button (opens a Sheet) on the right. Active filter badges are shown as a chip strip when any filter is set. The main content area is a `DataTable` component operating in server-side mode, with built-in pagination controls; for super-admin sessions it additionally renders selection checkboxes (§2.4a).

Columns in order: avatar (see below), `username` (clickable — navigates to edit), `name` (composed by the `getNameDisplay` helper: the non-empty parts of `firstname`/`middlename`/`lastname` joined with spaces, falling back to the flat `name` field, then `-`), `email`, `BU` (a `Building2`-icon active/total count of the user's business-unit assignments), `is_active` (Active/Inactive badge), `created_at` + `created_by_name`, `updated_at` + `updated_by_name`, and conditionally `deleted_at` + `deleted_by_name` (see §2.5). The final column is an icon-button row action menu. The legacy `platform_role` badge column is gone with the role enum.

### 2.1a Directory strip

A `UserDirectorySummary` card sits between the header and the search row, summarising **every non-deleted user** (a separate unpaginated `perpage: -1` fetch, plus a lightweight count-only fetch for soft-deleted rows) — not just the current page:

- A large total count.
- A stacked Active/Inactive proportion bar with a legend (Active, Inactive, and — only when non-zero — Archived, i.e. soft-deleted).
- A **"Recently added"** overlapping-avatar stack (`FACE_LIMIT = 6`) showing the newest users by `created_at`, each with the same initials-fallback/presigned-image pattern as the list's avatar column, collapsing any remainder into a `+N` badge.

The internal `summarizeUsers()` helper also computes a distinct-BU-count across the population (not currently surfaced in the card UI). The strip shows a skeleton while loading and an inline error/retry state on fetch failure — the main table is unaffected either way.

The **avatar column** renders a small circular `Avatar` (`h-8 w-8`): an `AvatarFallback` shows initials (first letters of `firstname` + `lastname`; if both are empty, the first two characters of `name`/`username`/`email`; else `?`), and when the record carries a presigned `avatar_url` an `AvatarImage` is layered on top, hiding itself again on load error so the initials show through.

When a row is soft-deleted (visible only with the "Show soft-deleted users" filter on), the Name cell additionally renders a red "Deleted" badge whose `title` tooltip reads "Deleted by &lt;deleted_by_name&gt;" when that name is present.

### 2.2 Filters (Sheet panel)

Clicking **Filters** opens a right-side Sheet. Two filter groups are available (the legacy Role filter was removed along with the role enum — status is now the only field filter):

- **Status** — two toggle buttons: **Active** (`is_active = true`) and **Inactive** (`is_active = false`). No tri-state "all" option; clearing both buttons removes the filter entirely — both off is equivalent to no status constraint (all rows shown). A **Clear** link appears when any status is selected.
- **Deleted** — a checkbox labelled "Show soft-deleted users". When off (default), the query appends `deleted_at: null`; when on, soft-deleted rows surface in the table with a red `Deleted` badge beside the user's name.

When any filter is active, a **Clear All Filters** button appears at the bottom of the Sheet, and active filter chips appear in the strip below the header.

### 2.3 Header actions

Three buttons appear in the header actions row, left to right:

- **Fetch Keycloak** — calls `userService.fetchKeycloakUsers()` → `POST /api-system/fetch-user`. A spinner replaces the icon while the request is in flight; on success a toast confirms the sync and both the table and the Directory strip reload. **Now wrapped in `<Can permission="user.create">`** — corrected since the last sync, when it carried no gate at all.
- **Export** — client-side CSV export (uses `generateCSV` / `downloadCSV` utilities). Exports the currently loaded page of rows with columns: `username`, `email`, `is_active`, `created_at`. The button is disabled while loading or when the table is empty. File name: `users-<YYYY-MM-DD>.csv`. Not `<Can>`-gated.
- **Add User** — navigates to `/users/new`. Wrapped in `<Can permission="user.create">`. Note: the empty-state's "Add User" shortcut (shown when the table has no rows and no search term) is **not** wrapped in `<Can>` — it renders for any `user.read` session, though the `/users/new` route guard still blocks navigation without `user.create`.

### 2.4 Row actions

Each row has a `DropdownMenu` (⋯ icon button) with three items, each wrapped in a `<Can>` gate (no `clusterId` is passed):

- **Edit** (`<Can permission="user.update">`) — navigates to `/users/:id/edit`.
- **Delete** (`<Can permission="user.delete">`) — sets `deleteId` state; triggers the `ConfirmDialog` (§5.3). Submit calls `DELETE /api-system/user/:id`.
- **Hard Delete** (also `<Can permission="user.delete">`, separated by a `DropdownMenuSeparator` inside the same gate) — sets `hardDeleteUser` state; opens the typed-confirmation Dialog (§5.4), which now also shows a super-admin-only "copy username" clipboard button.

A session holding only `user.read` sees an empty dropdown — the gates remove the items entirely rather than disabling them.

### 2.4a Bulk actions (super-admin only, new since the last sync)

`enableRowSelection={isSuperAdmin}` — row checkboxes render only for super-admin sessions (a super-admin flag check, not a `user.*` permission key). Selecting one or more rows reveals a toolbar above the table: **Delete** (opens a plain `ConfirmDialog`, "Delete `<n>` user(s)... They can be restored later.") and **Hard Delete** (opens a random-6-character-code confirmation dialog, §5.5) and **Clear**. Each bulk action fires one request per selected row (`Promise.allSettled`, continuing past individual failures) then shows an aggregate toast. Selection is scoped to the current page/filter state and clears automatically whenever page, page size, search, sort, or filters change.

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

The create mode renders a single card titled **"Account details"** (not "User Details" — corrected since the last sync; the title is computed as `isNew ? "Account details" : "Edit account"`) with description "Fill in the details for the new user". The page's `PageHeader` title is "Add User", subtitle "Create a new user". There is no hero card, no Access card, and no Change Password button — these only appear after the record is saved (`!isNew`).

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

The page starts in **view mode** (`editing = false`). A back-to-Users link sits above a **`UserIdentityHero`** card (new since the last sync, replacing the previous plain header + separate avatar): a `size-14` avatar (initials fallback from `firstname`/`lastname`, else the first two characters of username/email, with the presigned `avatar_url` image layered on top when present — loaded as `user.avatar_url || profile.avatar_url`, hidden again on load error), the user's full name as the page's only `<h1>`, username/email/alias chips, an Active/Inactive badge, and a summary line — "Access to `<n>` business unit(s) across `<m>` cluster(s)" or "No access assigned yet." In view mode only, the hero's actions slot shows two buttons: **Change Password** (not `<Can>`-gated) and **Edit** (wrapped in `<Can permission="user.update">` — redundant in practice with the route's own `user.update` guard, but consistent with the other modules' edit pages). Clicking **Edit** sets `editing = true`, saves the current form state to `savedFormData`, hides the hero's action buttons (Save and Cancel appear inside the form card instead), and swaps the form card's title to "Edit account".

Two cards are stacked vertically below the hero: the **User Details** card, and — for an existing user only — a single merged **Access** card (`UserAccessTree`) that replaced the two separate Clusters and Business Units cards from the prior sync.

### 4.1 User Details card

- **View mode**: all seven fields rendered as read-only styled `div` containers.
- **Edit mode**: inputs become editable. `username` is always `disabled={!isNew}` and cannot be changed after creation.
- **Save Changes** → `PUT /api-system/user/:id`, now with the loaded `doc_version` attached; on success, `fetchUser()` re-fetches (refreshing `doc_version` too) and `setEditing(false)` returns to view mode. A stale `409` shows a conflict toast and reloads the record instead.
- **Cancel** → restores `formData` from `savedFormData`, calls `setEditing(false)`. No API call.

### 4.2 Access card (`UserAccessTree`) — merged Clusters + Business Units, new since the last sync

Replaces the prior sync's two separate cards with one hierarchy: `groupAccessByCluster()` folds the user's `tb_cluster_user` memberships and `tb_user_tb_business_unit` assignments into a list of **cluster groups**, each showing the cluster name (linked to `/clusters/:clusterId` — **note: this is not a registered route**; `App.tsx` only registers `/clusters`, `/clusters/new`, and `/clusters/:id/edit` — clicking a cluster name in this card hits the SPA's `*` catch-all `NotFound` page, not the cluster's edit screen), code, the user's per-cluster role badge, and an Active/Inactive badge, followed by the business units assigned within that cluster. Any BU assignment whose own cluster isn't among the user's memberships collects into a trailing **"Other business units"** group so nothing is silently dropped. Each BU row shows its name (linked to `/business-units/:id/edit` — a real registered route), code, per-BU role badge, a `Default` badge (blue outline, `is_default`), an Active/Inactive badge, and a Remove (Trash) icon.

The card header shows "`<n>` business unit(s) across `<m>` cluster(s)" and an **Add BU** button. Two gating corrections since the last sync:

- **Add BU button** — visible only when `canAddBU` is true: `hasPermission('cluster.update', { clusterId })` evaluated across the user's own cluster memberships, **not** simply "the user belongs to at least one cluster" (the prior version's check). Previously undocumented as gated at all.
- **Remove (Trash) button per BU row** — now wrapped in `<Can permission="cluster.update" clusterId={bu's own cluster_id}>`, scoped to that specific BU's cluster (not the viewer's broader memberships), falling back to a sentinel that can never match a real cluster when the BU's own cluster is unresolved (the "Other business units" group). Previously undocumented as gated at all.

There is still no Add/Remove control for cluster *membership itself* on this page — only BU assignment is mutated here; cluster membership is managed on the cluster edit page.

## 5. Dialogs

### 5.1 Add BU dialog

Triggered by the **Add BU** button in the Access card header on `/users/:id/edit` (§4.2) — rendered only when `canAddBU` is true.

Fields in the dialog:

1. **Cluster** — select populated from `userClusters` (the user's existing cluster memberships). Choosing a cluster triggers an API call (`GET /api-system/business-units?...&advance={"where":{"cluster_id":"..."}}` — the BU endpoint is plural) to load the BUs for that cluster.
2. **Business Unit** — select populated from the cluster's BUs, filtered to exclude BUs the user is already assigned to (`availableBUs`). Shown only after a cluster is selected.
3. **BU Role** — select with values `Admin` and `User`.

There is no `is_default` checkbox in this dialog. The `is_default` field is shown on existing BU assignment rows but is not set during the Add BU flow. No Platform admin SPA surface currently sets `is_default`; the flag is writable only at the backend API or DB level.

Submit: re-checks `hasPermission('cluster.update', { clusterId: selectedClusterId })` against the specific cluster chosen (not just the broader `canAddBU`) before calling `businessUnitService.createUserBusinessUnit({ user_id, business_unit_id, role })` → `POST /api-system/user/business-units`. On success, dialog closes, a toast confirms, and `fetchUser()` re-fetches. The **Add** button is disabled while the request is in flight or if no BU has been selected. (Removal via the trash icon — gated `<Can permission="cluster.update" clusterId={bu's own cluster_id}>`, §4.2 — calls `deleteUserBusinessUnit(id)` → `DELETE /api-system/user/business-units/:id`, also re-checked against the BU's own cluster before firing.)

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

Submit: `DELETE /api-system/user/:id/hard`. The dialog cannot be closed while the delete request is in flight (`hardDeleting = true`). **New since the last sync:** for super-admin sessions, a small clipboard icon button beside the displayed username/email copies it (`navigator.clipboard.writeText`, `Check` icon confirms for 2 seconds) — a convenience, not a security control.

### 5.5 Bulk Soft Delete and Bulk Hard Delete confirm (super-admin only, new since the last sync)

Triggered by **Delete**/**Hard Delete** in the selection toolbar (§2.4a), visible only when `isSuperAdmin` and at least one row is selected.

**Bulk Soft Delete** uses the shared `ConfirmDialog`. Title: `Delete <n> user(s)`. Description: "Soft-delete the selected user(s)? They can be restored later." Confirm label: "Delete." On confirm, fans out one `DELETE /api-system/user/:id` per selected row (continuing past individual failures) and shows an aggregate result toast.

**Bulk Hard Delete** is a custom `Dialog` (not `ConfirmDialog`). Title: `Permanently Delete <n> User(s)` with a destructive alert icon. Lists every selected user by username/email/id in a scrollable box, then prompts the operator to type a **random 6-character alphanumeric code** generated fresh each time the dialog opens (input auto-uppercases as typed) — a materially different confirmation mechanism from the single-row flow's "type the exact username," since there is no single shared identifier across multiple rows. The **Permanently Delete** button stays disabled until the typed value matches the generated code exactly. On confirm, fans out one `DELETE /api-system/user/:id/hard` per selected row and shows the same aggregate-result toast pattern.

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

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan. **Note (2026-07-29):** the edit page gained a hero card and merged Access tree, and the list page gained a Directory strip and bulk-action toolbar, since this page was last captured-for — any future capture should target the current layout described in §2/§4.

## 8. References

- `../carmen-platform/src/App.tsx` — `requiredPermission` guards on the three user routes (route block, lines 152–174). (`SITEMAP.md` still shows the pre-RBAC "Authenticated" rows and lags the code.)
- `../carmen-platform/src/pages/UserManagement.tsx` and `userManagement/UserDirectorySummary.tsx` — list page: Directory summary strip, avatar column (`getInitials`), `getNameDisplay`, BU-count column, filters, header actions (`<Can>`-gated Fetch Keycloak/Add User, ungated Export), `<Can>`-gated row action menu (Edit / Delete / Hard Delete), super-admin bulk soft/hard-delete with row selection, nested-`audit` flattening, audit columns, `localStorage` keys.
- `../carmen-platform/src/pages/UserEdit.tsx` and `userEdit/{UserIdentityHero,UserAccessTree}.tsx` — create/view/edit page: hero card, User Details + merged Access card layout, `<Can>`-gated Edit toggle, `canAddBU`/scoped-Remove permission checks, Add BU dialog, Change Password dialog, `doc_version` wiring, `username` disabled-in-edit behaviour.
- `../carmen-platform/src/utils/docVersion.ts` — optimistic-lock helpers.
- `../carmen-platform/src/services/userService.ts` — API surface: all endpoints referenced in this page.
- Cross-links: [users](/en/platform/users) (landing), [Data Model](./data-model.md) (schema view), [Lifecycle](./lifecycle.md) (operations view), [rbac permissions](/en/platform/rbac/permissions) (gate composition), [clusters](/en/platform/clusters) (mutates `tb_cluster_user`), [business-units](/en/platform/business-units) (the other surface mutating `tb_user_tb_business_unit`).
