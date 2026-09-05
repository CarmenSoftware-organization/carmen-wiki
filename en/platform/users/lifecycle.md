---
title: User — Lifecycle
description: Create, disable, hard/soft delete, password reset.
published: true
date: 2026-09-05T12:45:00.000Z
tags: book/platform, users, lifecycle
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — Lifecycle

> **At a Glance**
> **Operations covered:** create (now requiring `firstname`/`lastname`, not just `username`/`email`) · edit · activate/deactivate (`is_active`) · soft-delete · hard-delete (single + bulk, super-admin only) · admin password reset · Keycloak sync · the effective-permissions sign-in gate &nbsp;·&nbsp; **Not in this product:** SSO · MFA · OAuth · email-link password reset &nbsp;·&nbsp; **Endpoints:** 9 service methods (8 under `/api-system/user`, incl. the directory-summary endpoint; Keycloak sync at `/api-system/fetch-user`) &nbsp;·&nbsp; **Cross-entity effects:** cluster assignments (read-only here) · BU assignments (mutated here via Add BU dialog, permission-checked per the target cluster) · RBAC role assignments (mutated on `/platform/user-platform`, not here) &nbsp;·&nbsp; **Concurrency:** `doc_version` optimistic lock on save

## 1. Overview

This page covers every mutating operation that an admin performs on a user record through the Platform SPA: creating an account, editing identity fields, toggling the `is_active` flag, soft-deleting and hard-deleting, resetting a password without the user's current credential, and pulling user records from Keycloak into the platform database. The data model that underpins these operations (field definitions, enums, constraints) is on the [Data Model](/en/platform/users/data-model) sibling page.

The product does not implement SSO, MFA, OAuth, or email-link password reset. All credential management is delegated to Keycloak; the SPA performs an admin-override password push via the `reset-password` endpoint and a pull-from-Keycloak sync via the `fetch-user` endpoint — there is no self-service reset link sent to the user's inbox.

Mutation scope is split between three surfaces. This page (user edit screen) owns user identity (`tb_user` + `tb_user_profile` fields) and BU assignment (`tb_user_tb_business_unit`). Cluster assignment (`tb_cluster_user`) is read-only on this screen and is mutated from the cluster edit page; a user must have at least one cluster membership before a BU assignment can be made. Platform-admin access (RBAC role assignments) is mutated on the separate `/platform/user-platform` screen — see [Platform RBAC](/en/platform/rbac); §4 below covers how those assignments gate sign-in.

## 2. Create flow

**Trigger:** The "Add User" button in the `UserManagement` header (`/users`), wrapped in `<Can permission="user.create">`, calls `navigate("/users/new")`, which renders `UserEdit.tsx` with `isNew = true`. The `/users/new` route itself is guarded by `requiredPermission="user.create"`.

**Endpoint:** `POST /api-system/user` via `userService.create(formData)`.

**Request body:** The full `UserFormData` object is posted as-is. Its 7 fields, now grouped on the form into three labelled sections — Sign-in details / Display name / Status (design pass commit `d21c57c`, #220) — are:

| Field | Type | Notes |
| ----- | ---- | ----- |
| `username` | string | Required; set once; the input is enabled only on create — it is `disabled={!isNew}` in the form |
| `email` | string (email) | Required |
| `firstname` | string | **Required (new since the last sync)** — carries the HTML `required` attribute and is checked by a client-side preflight before submit; stored in `tb_user_profile` |
| `middlename` | string | Optional; stored in `tb_user_profile` |
| `lastname` | string | **Required (new since the last sync)** — same validation as `firstname`; stored in `tb_user_profile` |
| `alias_name` | string | Optional |
| `is_active` | boolean | Default `true` at create |

Previously only `username` and `email` were required; `firstname`/`lastname` are now required too, so the "minimum required fields" case is four fields, not two.

There is no separate password field in `UserFormData`. The account is created without a credential in the SPA payload; the admin must use the "Change Password" button (§6) after creation, or the user's credential is managed entirely by Keycloak.

There is also no access field: creating an account grants **no** Platform admin access by itself. The new user holds zero RBAC role assignments, so the sign-in gate (§4) rejects them until an operator assigns a role on `/platform/user-platform`. (Historical: until 2026-06-10 the form carried a `platform_role` field whose value decided access — removed with the RBAC migration; see [Platform RBAC](/en/platform/rbac).)

**Success:** On a successful `POST`, the SPA calls `navigate('/users/:id/edit', { replace: true })` (where `:id` is the newly created user's UUID), switching to the edit route for the new record. Because both routes render the same `UserEdit` component, React preserves its state across the navigation — `editing` was initialised to `true` on `/users/new` and nothing resets it — so the page stays in edit mode after create; only a fresh visit to `/users/:id/edit` (e.g. from the list) opens in view mode. A `toast.success('User created successfully')` appears.

**Failure:** Any `4xx`/`5xx` response is caught and surfaced as `setError("Failed to save user: " + detail)`, shown in a red alert band at the top of the form.

## 3. Edit flow

**Trigger:** The "Edit" item in the row action menu (`/users` table, wrapped in `<Can permission="user.update">`) navigates to `/users/:id/edit`, which opens in view mode. The "Edit" button — now part of the `UserIdentityHero` card's action slot (view mode only), not a bare header button — (also wrapped in `<Can permission="user.update">`) calls `handleEditToggle()`, which saves the current `formData` into `savedFormData` and sets `editing = true`.

**Endpoint:** `PUT /api-system/user/:id` via `userService.update(id, formData)`, with the loaded `doc_version` appended to the payload when present (optimistic lock — see [Data Model](/en/platform/users/data-model) §2.1). A stale save (`409`) shows a "changed by someone else" toast and reloads the record via `fetchUser()` instead of overwriting.

**Username lock:** The `username` input carries `disabled={!isNew}`, so it is always disabled in edit mode. The SPA always sends the full `formData` object including `username`; backend handling of this field on `PUT` is not reflected in the SPA source.

**Mode toggle:** Clicking "Edit" reveals "Save" and "Cancel" buttons. "Cancel" calls `handleCancelEdit()`, which restores `formData` to the snapshot taken at `handleEditToggle()` time — no API call is made. Unsaved changes are tracked by comparing `formData` to `savedFormData` using `JSON.stringify`; the `useUnsavedChanges` hook will prompt the user before navigation if there are pending changes. Save and Cancel are also bound as keyboard shortcuts via `useGlobalShortcuts`: `Ctrl`/`⌘`+`S` submits the form while `editing && !saving`; `Escape` calls `handleCancelEdit()` only while `editing && !isNew` (a no-op in create mode).

**Success:** A `toast.success('Changes saved successfully')` appears; the page re-fetches the user from the server via `fetchUser()` and exits edit mode.

**Failure:** `setError("Failed to save user: " + detail)` shows the error in the alert band.

## 4. Activate / Deactivate

**Field:** `is_active` boolean on `tb_user` (nullable, default `false` at the DB level; the SPA initialises it to `true` for new records and reads `user.is_active ?? true` when loading existing ones).

**UI:** A checkbox labelled "Active" in the account-details card (see [UI Screens](/en/platform/users/ui-screens) §4.1) — that whole card, checkbox included, renders only while `editing`, so its own `Badge`-based view-mode branch is unreachable; the Active/Inactive status a viewer actually sees in view mode comes from the `UserIdentityHero` badge instead. The checkbox is editable only when the form is in edit mode; toggling it updates `formData.is_active`. The change is persisted on the next "Save" via the normal `PUT /api-system/user/:id` request — there is no dedicated toggle endpoint.

**Effect on sign-in:** When `is_active` is `false` the user's row is present in the database but the downstream inventory application treats the account as blocked. The Platform SPA's `AuthContext` does not check `is_active` at login itself — the gate is enforced by the consuming applications.

**Platform SPA sign-in gate (separate from `is_active`):** whether an account can sign in to the Platform admin SPA is decided at login by its **effective permissions**, not by any field on the user row. `login()` fetches `GET /api/user/permission/platform` and admits the session only if it holds at least one permission (platform- or cluster-scoped), carries the super-admin flag, or the bootstrap exception applies (total user count 0–1, the first-admin escape hatch); otherwise the partial session is torn down and the form shows "Access Denied. You are not authorized to access this platform." (Historical: until 2026-06-10 this gate was a `platform_role` allow-list — `ALLOWED_ROLES` — removed in `carmen-platform` commit `5f629f2`.) The full walkthrough, including the `hasPermission` resolution order and tester edge cases, lives in [Platform RBAC](/en/platform/rbac) §3 and [RBAC Permissions](/en/platform/rbac/permissions) §4–§5 — this page does not duplicate it.

**Independence from soft-delete:** `is_active = false` is a reversible flag; soft-delete stamps `deleted_at` and hides the row from the default list view. The two states are independent — a record can be inactive without being soft-deleted, or soft-deleted while still carrying `is_active = true`.

## 5. Soft delete vs. Hard delete

### 5.1 Soft delete

**Trigger:** "Delete" item in the row action dropdown (`DropdownMenuItem`, wrapped in `<Can permission="user.delete">`) in `UserManagement`. Calls `handleDelete(row.original.id)`, which sets `deleteId` state.

**Confirm dialog:** A `ConfirmDialog` component opens with the title "Delete User" and the message "Are you sure you want to delete this user? This action cannot be undone." It requires a single button click ("Delete") — no typed confirmation.

**Endpoint:** `DELETE /api-system/user/:id` via `userService.delete(id)`.

**Server-side effect:** The backend stamps `deleted_at` (and `deleted_by_id` / `deleted_by_name`) on the `tb_user` row; the row is not physically removed.

**List view behaviour:** By default the list query adds `where.deleted_at = null` (via `buildAdvance()`), so soft-deleted rows are hidden. Toggling "Show soft-deleted users" (`showDeleted` state, checkbox in the filter panel) removes that constraint. When `showDeleted` is enabled and a row has a non-null `deleted_at`, the Name column renders a red "Deleted" badge (its `title` tooltip reads "Deleted by &lt;deleted_by_name&gt;" when the name is present), and a "Deleted By" column showing `deleted_at` + `deleted_by_name` appears in the table.

**Success/failure:** `toast.success('User deleted successfully')` or `toast.error('Failed to delete user', ...)`.

### 5.2 Hard delete

**Trigger:** "Hard Delete" item (with `AlertTriangle` icon) in the row action dropdown, wrapped in `<Can permission="user.delete">` like the soft delete. Calls `handleHardDelete(row.original)`, which sets `hardDeleteUser` state and opens a custom dialog.

**Typed-confirmation dialog:** The dialog title is "Permanently Delete User". It displays the user's `username` (falling back to `email`) and full name. The operator must type the exact value of `hardDeleteUser?.username || hardDeleteUser?.email` into a text input; the "Permanently Delete" button is `disabled` until `hardDeleteConfirm === (hardDeleteUser?.username || hardDeleteUser?.email)`. This means: if `username` is set, the operator types the username; if `username` is absent (e.g. a Keycloak-synced record with only an email), the operator types the email.

**Endpoint:** `DELETE /api-system/user/:id/hard` via `userService.hardDelete(id)`.

**Effect on join rows:** Both `tb_cluster_user.user_id → tb_user.id` and `tb_user_tb_business_unit.user_id → tb_user.id` are declared `onDelete: NoAction` in the Prisma platform schema. Hard-deleting a `tb_user` row will therefore fail at the database level if any `tb_cluster_user` or `tb_user_tb_business_unit` rows reference the user — the database engine will raise a foreign-key violation rather than cascade. The SPA shows this as `toast.error('Failed to permanently delete user', ...)`. Operators must remove or soft-delete the user's cluster and BU memberships before a hard delete can succeed.

**Success:** `toast.success('User permanently deleted')`; the table and the Directory summary strip both reload.

**Super-admin copy-username shortcut (new since the last sync):** when `isSuperAdmin` is true, the confirmation dialog shows a small clipboard button beside the displayed username/email that copies it to the clipboard (`navigator.clipboard.writeText`, a `Check` icon confirms for 2 seconds) — a convenience for pasting the exact confirmation string, not a security control.

### 5.3 Bulk soft delete and bulk hard delete (super-admin only, new since the last sync)

**Trigger:** Row checkboxes on `UserManagement` are rendered only when `isSuperAdmin` is true (`enableRowSelection={isSuperAdmin}` on the `DataTable`) — this is a super-admin capability check, not a `user.*` permission key. Selecting one or more rows reveals a selection toolbar with **Delete** and **Hard Delete** buttons; the selection resets whenever the page, page size, search, sort, or filters change so an off-screen row can never stay silently selected.

**Bulk soft delete:** Delete opens a plain `ConfirmDialog` ("Delete `<n>` user(s)... They can be restored later."); on confirm, one `DELETE /api-system/user/:id` per selected user fires via `Promise.allSettled`, followed by an aggregate toast (`Deleted N user(s)`, or a partial-failure warning naming both counts).

**Bulk hard delete:** Hard Delete opens a dialog listing every selected user by username/email, and generates a random 6-character alphanumeric code the operator must retype exactly (uppercased as typed) — a materially different confirmation mechanism from the single-row flow's "type the exact username" requirement, chosen because there is no single shared identifier across multiple rows. On confirm, one `DELETE /api-system/user/:id/hard` per selected user fires via `Promise.allSettled`, with the same aggregate-result toast pattern. The same FK-cascade caveat as §5.2 applies per-row — a user with live cluster/BU memberships fails silently into the "failed" count of the aggregate toast, it does not block the rest of the batch.

## 6. Admin-initiated password reset

**Trigger:** The "Change Password" button (with `KeyRound` icon), part of the `UserIdentityHero` card's actions slot on `/users/:id/edit` (visible only when `!isNew && !editing`). **Like the neighbouring Edit button, it is now wrapped in `<Can permission="user.update">`** — previously it carried no in-page gate at all and rendered for any session that passed the route's `user.update` guard; this page's own gate is functionally redundant with that route guard, but it is present in current source. Calls `handleOpenPasswordDialog()`, which resets the dialog fields and sets `showPasswordDialog = true`.

**Dialog fields:**

| Field | Validation |
| ----- | ---------- |
| New Password | Required; minimum 6 characters (`newPassword.length < 6` rejects client-side) |
| Confirm Password | Required; must equal New Password |

The user's current password is **not** required — this is an admin override. If validation fails, an inline `passwordError` message appears inside the dialog.

**Endpoint:** `PUT /api-system/user/:id/reset-password` via `userService.resetPassword(id, newPassword)` with body `{ newPassword }`.

**Post-call behaviour:** On success, the dialog closes and `toast.success('Password changed successfully')` appears. The SPA does not re-fetch the user record, does not refresh `AuthContext`, and does not send any email notification to the user. On failure, `passwordError` is set to `'Failed to change password: ' + detail` and shown inside the dialog.

For self-service password change by the user themselves, see [profile](/en/platform/profile).

## 7. Keycloak sync

**Trigger:** The "Fetch Keycloak" button (`RefreshCw` icon) in the `UserManagement` header. Calls `handleFetchKeycloak()`, which sets `syncing = true` and calls `userService.fetchKeycloakUsers()`.

**Endpoint:** `POST /api-system/fetch-user` (no request body from the SPA).

**Effect:** The backend pulls the current Keycloak user roster and upserts matching records into `tb_user`. After the call, the SPA triggers a table reload by calling `setPaginate(prev => ({ ...prev }))` and refreshes the Directory summary strip. The button shows a spinning `Loader2` icon and the label "Fetching..." while `syncing` is true.

**Access control — corrected since the last sync:** the button is now wrapped in `<Can permission="user.create">` — it previously carried no in-page gate at all (any `user.read` session could see and click it). It is visible only to sessions holding `user.create`; backend enforcement remains the actual security boundary regardless.

## 8. Cross-entity side effects

**Cluster assignments (`tb_cluster_user`):** The user edit screen (`UserEdit.tsx`) displays the user's cluster memberships read-only, nested inside the `UserAccessTree` card (which replaced the former separate Clusters card). The Add BU dialog queries business units filtered by `cluster_id` from the user's existing `tb_cluster_user` rows — cluster membership must exist before a BU can be assigned. Cluster membership itself is created and deleted from the cluster edit page, not here.

**BU assignments (`tb_user_tb_business_unit`):** The `UserAccessTree` card on the user edit screen provides an "Add BU" button that opens a two-step dialog: select a cluster (from the user's existing memberships), then select a BU from that cluster. **Permission check, corrected since the last sync:** the Add BU button itself only renders when `canAddBU` is true — computed as `hasPermission('cluster.update', { clusterId })` across the user's own cluster memberships, not merely "the user belongs to at least one cluster" (a prior version conflated a data precondition with a permission check; `handleAddBU` also re-verifies against the specific cluster selected in the dialog before submitting, since an admin might hold `cluster.update` on one of the user's clusters but not the one actually chosen). The resulting `businessUnitService.createUserBusinessUnit()` call (`POST /api-system/user/business-units`) writes a new row to `tb_user_tb_business_unit` with the chosen `user_id`, `business_unit_id`, and `role`. Existing BU rows can be removed via the trash-icon button beside each entry — now wrapped in `<Can permission="cluster.update" clusterId={bu's own cluster_id}>` (scoped to the BU's own cluster, not the viewer's broader memberships, and falling back to a sentinel that can never match a real cluster when the BU's cluster is unresolved, so an orphaned "Other business units" row fails closed) — which calls `businessUnitService.deleteUserBusinessUnit(id)` (`DELETE /api-system/user/business-units/:id`) after a `ConfirmDialog`.

For FK cascade behaviour affecting these joins on hard delete, see §5.2 (and its bulk counterpart, §5.3).

## 9. References

**SPA sources (primary):**
- `../carmen-platform/src/services/userService.ts` — all 9 API methods: `getAll`, `getById`, `getDirectorySummary`, `create`, `update`, `delete`, `hardDelete`, `resetPassword`, `fetchKeycloakUsers`.
- `../carmen-platform/src/pages/UserManagement.tsx` — soft-delete `ConfirmDialog`, hard-delete typed-confirmation dialog (+ super-admin copy-username button), bulk soft/hard-delete dialogs (super-admin only, random-code confirmation), `<Can permission="user.create">`-gated "Fetch Keycloak" handler, "Show soft-deleted users" toggle, `buildAdvance()` filter logic, `<Can>` gates on the row actions.
- `../carmen-platform/src/pages/UserEdit.tsx` and `userEdit/{UserIdentityHero,UserAccessTree}.tsx` — "Change Password" dialog (`handleResetPassword`, now `<Can permission="user.update">`-gated), `handleSubmit` (create/update, `doc_version`-aware, required-field preflight), `handleCancelEdit` (mode toggle), `handleAddBU` / `handleDeleteBU` (BU assignment, `canAddBU` / scoped `<Can>` permission checks), `<Can permission="user.update">` on the Edit toggle.
- `../carmen-platform/src/utils/docVersion.ts` — optimistic-lock helpers used by `handleSubmit`.
- `../carmen-platform/src/context/AuthContext.tsx` — `login()` effective-permissions gate and bootstrap exception (§4).

**Schema source:**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (backend HEAD `3bae0679d`) — FK `onDelete: NoAction` on `tb_cluster_user.user_id` and `tb_user_tb_business_unit.user_id`; `tb_user` model (line 476); `doc_version` added to `tb_user`/`tb_user_profile` on 2026-07-16.

**Cross-links:**
- [users](/en/platform/users) — module landing: overview, key concepts, navigation map.
- [Data Model](/en/platform/users/data-model) — schema reference: field definitions, enums, constraints, SPA divergences.
- [rbac](/en/platform/rbac) — the effective-permissions login gate, role assignments (`/platform/user-platform`), and the bootstrap exception referenced in §4.
- [profile](/en/platform/profile) — self-service password change by the signed-in user.
