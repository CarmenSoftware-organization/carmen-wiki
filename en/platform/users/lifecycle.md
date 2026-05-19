---
title: User — Lifecycle
description: Create, disable, hard/soft delete, password reset.
published: true
date: '2026-05-19T15:00:00.000Z'
tags: book/platform, users, lifecycle
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — Lifecycle

> **At a Glance**
> **Operations covered:** create &nbsp;·&nbsp; edit &nbsp;·&nbsp; activate/deactivate (`is_active`) &nbsp;·&nbsp; soft-delete &nbsp;·&nbsp; hard-delete &nbsp;·&nbsp; admin password reset &nbsp;·&nbsp; Keycloak sync &nbsp;·&nbsp; **Not in this product:** SSO, MFA, OAuth, email-link password reset &nbsp;·&nbsp; **Endpoints:** 8 methods under `/api-system/user` &nbsp;·&nbsp; **Cross-entity effects:** cluster assignments (read-only here), BU assignments (mutated here via Add BU dialog)

## 1. Overview

This page covers every mutating operation that an admin performs on a user record through the Platform SPA: creating an account, editing identity fields, toggling the `is_active` flag, soft-deleting and hard-deleting, resetting a password without the user's current credential, and pulling user records from Keycloak into the platform database. The data model that underpins these operations (field definitions, enums, constraints) is on the [[data-model]] sibling page.

The product does not implement SSO, MFA, OAuth, or email-link password reset. All credential management is delegated to Keycloak; the SPA performs an admin-override password push via the `reset-password` endpoint and a pull-from-Keycloak sync via the `fetch-user` endpoint — there is no self-service reset link sent to the user's inbox.

Mutation scope is split between two surfaces. This page (user edit screen) owns user identity (`tb_user` + `tb_user_profile` fields) and BU assignment (`tb_user_tb_business_unit`). Cluster assignment (`tb_cluster_user`) is read-only on this screen and is mutated from the cluster edit page; a user must have at least one cluster membership before a BU assignment can be made.

## 2. Create flow

**Trigger:** The "Add User" button in the `UserManagement` header (`/users`) calls `navigate("/users/new")`, which renders `UserEdit.tsx` with `isNew = true`.

**Endpoint:** `POST /api-system/user` via `userService.create(formData)`.

**Request body:** The full `UserFormData` object is posted as-is. Its 8 fields are:

| Field | Type | Notes |
| ----- | ---- | ----- |
| `username` | string | Required; set once; the input is enabled only on create — it is `disabled={!isNew}` in the form |
| `email` | string (email) | Required |
| `platform_role` | `enum_platform_role` | Default `"user"` |
| `alias_name` | string | Optional |
| `firstname` | string | Stored in `tb_user_profile` |
| `middlename` | string | Stored in `tb_user_profile` |
| `lastname` | string | Stored in `tb_user_profile` |
| `is_active` | boolean | Default `true` at create |

There is no separate password field in `UserFormData`. The account is created without a credential in the SPA payload; the admin must use the "Change Password" button (§6) after creation, or the user's credential is managed entirely by Keycloak.

**Success:** On a successful `POST`, the SPA calls `navigate('/users/${created.id}/edit', { replace: true })`, switching the page into edit mode for the new record. A `toast.success('User created successfully')` appears.

**Failure:** Any `4xx`/`5xx` response is caught and surfaced as `setError("Failed to save user: " + detail)`, shown in a red alert band at the top of the form.

## 3. Edit flow

**Trigger:** The "Edit" button in the row action menu (`/users` table) or the "Edit" button in the header of `/users/:id/edit` when the page is in view mode. Both call `handleEditToggle()`, which saves the current `formData` into `savedFormData` and sets `editing = true`.

**Endpoint:** `PUT /api-system/user/:id` via `userService.update(id, formData)`.

**Username lock:** The `username` input carries `disabled={!isNew}`, so it is always disabled in edit mode. The field is included in `formData` but the backend receives it — whether the backend ignores it on `PUT` is not enforced by the SPA; the SPA always sends the full object.

**Mode toggle:** Clicking "Edit" reveals "Save" and "Cancel" buttons. "Cancel" calls `handleCancelEdit()`, which restores `formData` to the snapshot taken at `handleEditToggle()` time — no API call is made. Unsaved changes are tracked by comparing `formData` to `savedFormData` using `JSON.stringify`; the `useUnsavedChanges` hook will prompt the user before navigation if there are pending changes.

**Success:** A `toast.success('Changes saved successfully')` appears; the page re-fetches the user from the server via `fetchUser()` and exits edit mode.

**Failure:** `setError("Failed to save user: " + detail)` shows the error in the alert band.

## 4. Activate / Deactivate

**Field:** `is_active` boolean on `tb_user` (nullable, default `false` at the DB level; the SPA initialises it to `true` for new records and reads `user.is_active ?? true` when loading existing ones).

**UI:** A checkbox labelled "Active" in the User Details card, with a `Badge` showing "Active" (green) or "Inactive" (grey). The checkbox is editable only when the form is in edit mode; toggling it updates `formData.is_active`. The change is persisted on the next "Save" via the normal `PUT /api-system/user/:id` request — there is no dedicated toggle endpoint.

**Effect on sign-in:** When `is_active` is `false` the user's row is present in the database but the downstream inventory application treats the account as blocked. The Platform SPA's `AuthContext` does not check `is_active` at login itself — the gate is enforced by the consuming applications.

**Independence from soft-delete:** `is_active = false` is a reversible flag; soft-delete stamps `deleted_at` and hides the row from the default list view. The two states are independent — a record can be inactive without being soft-deleted, or soft-deleted while still carrying `is_active = true`.

## 5. Soft delete vs. Hard delete

### 5.1 Soft delete

**Trigger:** "Delete" item in the row action dropdown (`DropdownMenuItem`) in `UserManagement`. Calls `handleDelete(row.original.id)`, which sets `deleteId` state.

**Confirm dialog:** A `ConfirmDialog` component opens with the title "Delete User" and the message "Are you sure you want to delete this user? This action cannot be undone." It requires a single button click ("Delete") — no typed confirmation.

**Endpoint:** `DELETE /api-system/user/:id` via `userService.delete(id)`.

**Server-side effect:** The backend stamps `deleted_at` (and `deleted_by_id` / `deleted_by_name`) on the `tb_user` row; the row is not physically removed.

**List view behaviour:** By default the list query adds `where.deleted_at = null` (via `buildAdvance()`), so soft-deleted rows are hidden. Toggling "Show soft-deleted users" (`showDeleted` state, checkbox in the filter panel) removes that constraint. When `showDeleted` is enabled and a row has a non-null `deleted_at`, the Name column renders a red "Deleted" badge, and the `deleted_at` / `deleted_by_name` columns appear in the table.

**Success/failure:** `toast.success('User deleted successfully')` or `toast.error('Failed to delete user', ...)`.

### 5.2 Hard delete

**Trigger:** "Hard Delete" item (with `AlertTriangle` icon) in the row action dropdown. Calls `handleHardDelete(row.original)`, which sets `hardDeleteUser` state and opens a custom dialog.

**Typed-confirmation dialog:** The dialog title is "Permanently Delete User". It displays the user's `username` (falling back to `email`) and full name. The operator must type the exact value of `hardDeleteUser?.username || hardDeleteUser?.email` into a text input; the "Permanently Delete" button is `disabled` until `hardDeleteConfirm === (hardDeleteUser?.username || hardDeleteUser?.email)`. This means: if `username` is set, the operator types the username; if `username` is absent (e.g. a Keycloak-synced record with only an email), the operator types the email.

**Endpoint:** `DELETE /api-system/user/:id/hard` via `userService.hardDelete(id)`.

**Effect on join rows:** Both `tb_cluster_user.user_id → tb_user.id` and `tb_user_tb_business_unit.user_id → tb_user.id` are declared `onDelete: NoAction` in the Prisma platform schema. Hard-deleting a `tb_user` row will therefore fail at the database level if any `tb_cluster_user` or `tb_user_tb_business_unit` rows reference the user — the database engine will raise a foreign-key violation rather than cascade. The SPA shows this as `toast.error('Failed to permanently delete user', ...)`. Operators must remove or soft-delete the user's cluster and BU memberships before a hard delete can succeed.

**Success:** `toast.success('User permanently deleted')`; the table reloads.

## 6. Admin-initiated password reset

**Trigger:** The "Change Password" button (with `KeyRound` icon) in the header of `/users/:id/edit`, visible only when `!isNew && !editing`. Calls `handleOpenPasswordDialog()`, which resets the dialog fields and sets `showPasswordDialog = true`.

**Dialog fields:**

| Field | Validation |
| ----- | ---------- |
| New Password | Required; minimum 6 characters (`newPassword.length < 6` rejects client-side) |
| Confirm Password | Required; must equal New Password |

The user's current password is **not** required — this is an admin override. If validation fails, an inline `passwordError` message appears inside the dialog.

**Endpoint:** `PUT /api-system/user/:id/reset-password` via `userService.resetPassword(id, newPassword)` with body `{ newPassword }`.

**Post-call behaviour:** On success, the dialog closes and `toast.success('Password changed successfully')` appears. The SPA does not re-fetch the user record, does not refresh `AuthContext`, and does not send any email notification to the user. On failure, `passwordError` is set to `'Failed to change password: ' + detail` and shown inside the dialog.

For self-service password change by the user themselves, see [[profile]].

## 7. Keycloak sync

**Trigger:** The "Fetch Keycloak" button (`RefreshCw` icon) in the `UserManagement` header. Calls `handleFetchKeycloak()`, which sets `syncing = true` and calls `userService.fetchKeycloakUsers()`.

**Endpoint:** `POST /api-system/fetch-user` (no request body from the SPA).

**Effect:** The backend pulls the current Keycloak user roster and upserts matching records into `tb_user`. After the call, the SPA triggers a table reload by calling `setPaginate(prev => ({ ...prev }))`. The button shows a spinning `Loader2` icon and the label "Fetching..." while `syncing` is true.

**Access control:** The SPA attaches no `allowedRoles` gate to this button — it is visible to any authenticated user who can reach the `UserManagement` page. Operationally the action is meaningful only when the backend service account has admin access to Keycloak; without it, the backend call will fail and the SPA shows `toast.error('Failed to fetch users from Keycloak', ...)`.

## 8. Cross-entity side effects

**Cluster assignments (`tb_cluster_user`):** The user edit screen (`UserEdit.tsx`) displays the user's cluster memberships in a read-only Clusters card. The Add BU dialog queries business units filtered by `cluster_id` from the user's existing `tb_cluster_user` rows — cluster membership must exist before a BU can be assigned. Cluster membership itself is created and deleted from the cluster edit page, not here.

**BU assignments (`tb_user_tb_business_unit`):** The Business Units card on the user edit screen provides an "Add BU" button that opens a two-step dialog: select a cluster (from the user's existing memberships), then select a BU from that cluster. The resulting `POST` to `businessUnitService.createUserBusinessUnit()` writes a new row to `tb_user_tb_business_unit` with the chosen `user_id`, `business_unit_id`, and `role`. Existing BU rows can be removed via the trash-icon button beside each entry, which calls `businessUnitService.deleteUserBusinessUnit(id)` after a `ConfirmDialog`.

**Cascade behaviour on hard delete:** As established in §5.2, both `tb_cluster_user.user_id` and `tb_user_tb_business_unit.user_id` FK constraints declare `onDelete: NoAction, onUpdate: NoAction` (Prisma platform schema, lines 212 and ~490 respectively). No rows in either join table are automatically removed when a `tb_user` row is hard-deleted. The hard delete will fail with a FK violation unless the operator manually removes all cluster and BU memberships for the user first.

## 9. References

**SPA sources (primary):**
- `../carmen-platform/src/services/userService.ts` — all 8 API methods: `getAll`, `getById`, `create`, `update`, `delete`, `hardDelete`, `resetPassword`, `fetchKeycloakUsers`.
- `../carmen-platform/src/pages/UserManagement.tsx` — soft-delete `ConfirmDialog`, hard-delete typed-confirmation dialog, "Fetch Keycloak" handler, "Show soft-deleted users" toggle, `buildAdvance()` filter logic.
- `../carmen-platform/src/pages/UserEdit.tsx` — "Change Password" dialog (`handleResetPassword`), `handleSubmit` (create/update), `handleCancelEdit` (mode toggle), `handleAddBU` / `handleDeleteBU` (BU assignment).

**Schema source:**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — FK `onDelete: NoAction` on `tb_cluster_user.user_id` (line 212) and `tb_user_tb_business_unit.user_id`; `tb_user` model (line 368).

**Cross-links:**
- [[users]] — module landing: overview, key concepts, navigation map.
- [[data-model]] — schema reference: field definitions, enums, constraints, SPA divergences.
- [[profile]] — self-service password change by the signed-in user.
