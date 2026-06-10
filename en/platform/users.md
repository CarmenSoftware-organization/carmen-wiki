---
title: Users
description: Platform-level user accounts — identity, avatars, and the cluster/BU assignments that scope what the user can reach in the inventory app. Platform-admin access itself is granted via RBAC role assignments.
published: true
date: 2026-06-10T14:00:00.000Z
tags: platform/users, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Users

> **At a Glance**
> **Module purpose:** Authoring surface for the platform-level user account — one row per person who can sign in, holding the identity fields (`username`, `email`, name parts, `alias_name`), the avatar, the `is_active` flag, and the read-only views of which clusters and BUs the user is assigned to (assignments themselves are mutated from the cluster side or, for BUs, from the Add-BU dialog inside this page). What the account can *do* in the Platform admin SPA is not stored here — that is the [RBAC](/en/platform/rbac) module's role assignments &nbsp;·&nbsp; **Audience:** Holders of the `user.read`/`user.create`/`user.update`/`user.delete` permission keys — typically Carmen support engineers and customer-side admins &nbsp;·&nbsp; **Key entities/tables:** `tb_user` + `tb_user_profile` (7 form fields: `username`, `email`, `alias_name`, `firstname`, `middlename`, `lastname`, `is_active`; plus soft-delete trio `deleted_at`/`deleted_by_name`/timestamps and a presigned `avatar_url` on read), `tb_cluster_user` (M:N cluster join — read-only here), BU-user join (M:N BU assignment with per-BU `role` of `admin`/`user` and an `is_default` flag) &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The Users module exposes the platform-level user aggregate through the same two-screen pattern used everywhere else in the Platform SPA:

- **`/users` → `UserManagement`** — server-side `DataTable` with a leading avatar column (initials fallback in a circular badge, real presigned `avatar_url` layered on top when present), debounced search, a Sheet-based filters panel (Active/Inactive status and "show soft-deleted" — the legacy role filter left with the role enum), CSV export, persisted UI state in `localStorage` (search, page, perpage, sort, status filters, show-deleted toggle), Created/Updated audit columns, plus two header actions unique to this module: **Fetch Keycloak** (calls `userService.fetchKeycloakUsers()` to pull the current Keycloak user list into the platform DB) and **Add User** (wrapped in `<Can permission="user.create">`). Row Edit and Delete/Hard-Delete actions are gated in-page by `user.update` and `user.delete`.
- **`/users/new` → `UserEdit` (create mode)** — single "User Details" card with the seven form fields; on successful create the page `navigate(..., { replace: true })`s to the edit route for the new id.
- **`/users/:id/edit` → `UserEdit` (view/edit mode)** — header shows the user's avatar (same initials-fallback pattern as the list) beside the title, then three stacked cards. The **User Details** card is view-only by default and switched to editable via the Edit button, which is wrapped in `<Can permission="user.update">` (in edit mode, `username` is disabled — it is set once at create). The **Clusters** card is read-only and lists the `tb_cluster_user` join rows: each card shows the cluster name/code, an active/inactive badge, and the per-cluster role (`admin` or `user`). The **Business Units** card lists the BU-user join rows with per-BU role, `is_default` badge, and a Trash icon to remove; it has its own **Add BU** dialog whose available BUs are scoped to clusters the user is already a member of.

The header on the edit screen also exposes a **Change Password** action (admin-initiated password reset via `userService.resetPassword`, with a confirm-twice dialog) and the list page exposes a hard-delete dialog that requires the operator to type the username/email to confirm.

## 2. Business Context

A user record is the platform's source of truth for "this person can sign in." What the account can *do* in the Platform admin SPA is no longer stored on the user row: the legacy single-value `platform_role` enum was removed (frontend commit `6091ffc`; the column and `enum_platform_role` are gone from the Prisma platform schema). Platform-level access is now granted through RBAC role assignments managed on the separate **User Platform** screen (`/platform/user-platform`) — the Users module manages the *account*; role and scope assignment lives in the [RBAC](/en/platform/rbac) module. At login the SPA validates the account's effective permissions (`GET /api/user/permission/platform`) and rejects sessions that hold none, with a bootstrap exception while the platform has 0–1 users — so a freshly created account cannot reach the Platform admin SPA until someone assigns it a role.

Beyond identity, the user record also captures **where** the user can operate. Cluster membership lives in `tb_cluster_user` and is mutated from the cluster edit page (Section 5 cross-link); the Users module shows the resulting set read-only as the Clusters card on the edit screen. BU membership is per-cluster — the **Add BU** dialog on this page only lists BUs whose `cluster_id` matches one of the user's current cluster memberships, which keeps the tenant boundary clean: a user cannot be assigned to a BU outside the clusters they already belong to. The BU-user join carries its own `role` (`admin` or `user`, orthogonal to the platform RBAC assignments) and an `is_default` flag that marks the BU the inventory app should land on at login.

Two additional flows deserve care beyond their UI gates: the **Fetch Keycloak** sync button (carries no in-page `<Can>` gate — any `user.read` session sees it — and is only meaningful for operators with backend admin access to Keycloak) and the **Hard Delete** action (gated `user.delete`, plus a typed-username confirmation on the list page, vs. the standard soft-delete from the row's action menu).

## 3. Key Concepts

- **User** — one row in `tb_user` representing one identity that can sign in. Seven editable fields: `username` (set once at create, then disabled), `email`, `alias_name`, `firstname`, `middlename`, `lastname`, and `is_active`. The list response also surfaces `created_at`/`created_by_name` and `updated_at`/ `updated_by_name` for the audit columns (flat fields win; nested `audit` object is the fallback) and `deleted_at`/ `deleted_by_name` for the soft-delete badge.
- **Platform access via RBAC assignments** — what the account can reach in the Platform admin SPA is decided by role assignments (platform-wide or per-cluster scope), managed on the `/platform/user-platform` screen — *not* on the user edit page. The login gate admits a session only when it holds at least one effective permission, carries the super-admin flag, or the bootstrap exception (total user count 0–1) applies. See [Platform RBAC](/en/platform/rbac) for the catalog/roles/assignments model and the login walkthrough; until 2026-06-10 this was a single `platform_role` enum on the user row, now removed.
- **Avatar** — stored as `avatar_file_token` on `tb_user_profile`; the API resolves it to a presigned `avatar_url` string on list and detail responses. The list's leading column and the edit-page header render a circular avatar with an initials fallback (first letters of `firstname`+`lastname`) and layer the real image on top when `avatar_url` is present, hiding it again on load error. The secondary fallback differs per surface: the list falls back to the first two characters of `name`/`username`/`email`, while the edit header consults only `username`/`email` (the form data carries no flat `name` field).
- **Display name** — the list's Name column is composed by the `getNameDisplay` helper: when any of `firstname`/`middlename`/`lastname` is set, the non-empty parts are joined with spaces; otherwise the flat `name` field is shown, falling back to `-`.
- **Cluster assignments (`tb_cluster_user`)** — M:N join between user and cluster, carrying a per-cluster `role` of `admin` or `user`. The Users edit page shows this read-only as the Clusters card; mutation happens from the cluster edit page's Users card. A user must be a cluster member before they can be added to one of that cluster's BUs.
- **BU assignments** — M:N join between user and business unit, with its own per-BU `role` (`admin` or `user`, from the `BU_ROLES` constant), `is_active` flag, and `is_default` flag. The Users edit page is the canonical place to add and remove these rows; the **Add BU** dialog filters available BUs to those belonging to clusters the user is already in.
- **Active flag (`is_active`)** — toggles whether the user can sign in. Independent from soft-delete; an active user can still be on the way out, or an inactive user can be retained for audit before deletion.
- **Soft delete vs. hard delete** — the row-level action menu offers both, each wrapped in `<Can permission="user.delete">`. Soft delete sets `deleted_at`/`deleted_by_name`; the list view hides those rows unless the "Show soft-deleted users" filter is on, and surfaces a red "Deleted" badge (whose tooltip names the deleter via `deleted_by_name`) plus a "Deleted By" column. Hard delete is permanent and additionally gated by a dialog requiring the operator to type the exact username/email.
- **Keycloak sync** — `userService.fetchKeycloakUsers()` is exposed as a header button on the list page. It refreshes the platform's user list from Keycloak; the page reloads the table after success.
- **Admin password reset** — the edit screen's header has a **Change Password** action that opens a dialog with new + confirm fields (minimum 6 chars, must match). Submits to `userService.resetPassword(id, newPassword)`. There is no email-link flow in this surface — the reset is admin-initiated and immediate.

## 4. Roles and Personas

All three user routes are wrapped in `PrivateRoute` with a `requiredPermission` prop — confirmed by reading `../carmen-platform/src/App.tsx` (lines 132–155) — and the sidebar's "Users" entry (Organization group) is filtered by the same `user.read` key in `Layout.tsx`. In-page mutations are additionally wrapped in `<Can>` gates (commits `239b4a9`, `f3f77cf`). Unlike the Clusters and Business Units pages, none of the user gates pass a `clusterId` — user permission checks always run at the broad scope, so a cluster-scoped grant of a `user.*` key behaves the same as a platform-scoped one in this module's UI.

| Surface | Gate |
|---|---|
| `/users` (list) | route guard `user.read` |
| `/users/new` (create) | route guard `user.create` |
| `/users/:id/edit` (view/edit) | route guard `user.update` |
| Add User (list header) | `<Can permission="user.create">` |
| Row action: Edit | `<Can permission="user.update">` |
| Row actions: Delete + Hard Delete | `<Can permission="user.delete">` |
| Edit toggle (edit-page header) | `<Can permission="user.update">` |

Not gated in-page (visible to anyone who passes the route guard): **Fetch Keycloak**, **Export**, **Change Password**, **Add BU**, and the BU-removal trash icon — plus the empty-state's "Add User" shortcut, which (unlike the header button) is not wrapped in `<Can>`. For these, backend enforcement is the real boundary. Note that the `user.*` keys gate account CRUD only; role/scope assignment is gated by the separate `user_platform.*` keys on the [RBAC](/en/platform/rbac) screens.

| Persona | Typical keys | What they typically do here |
|---|---|---|
| Carmen support engineer / customer-side admin | `user.read` + `user.create`/`user.update`/`user.delete` | Onboard new customer users, reset passwords, update staff contact info, manage the BU roster |
| Read-only auditor | `user.read` only | Browse the list only — the username link targets `/users/:id/edit`, which the `user.update` route guard blocks with Access Denied (no read-only detail route exists); Add User, row Edit/Delete, and the Edit toggle do not render |

## 5. Related Modules

- [business-units](/en/platform/business-units) — supplies the BUs that show up in the user's Business Units card; assignments created here appear on the BU's own Users card. Both pages mutate the same BU-user join with the same `BU_ROLES` (`admin`/`user`) and `is_default` flag.
- [clusters](/en/platform/clusters) — supplies the clusters that show up in the user's Clusters card (read-only here); the cluster edit page is the canonical place to add/remove `tb_cluster_user` rows. The Users module gates BU-assignment dropdowns by current cluster membership, so cluster membership must be granted from the cluster side first.
- [rbac](/en/platform/rbac) — owns the access side of the user: the permission catalog, roles, scoped assignments (`/platform/user-platform`), the super-admin flag, and the effective-permissions login gate. The Users module creates the account; RBAC decides what it can do.
- [profile](/en/platform/profile) — the user's own first-person view of the same user record; the avatar menu's "Profile" link lands there. The Users module is the third-person admin view, the Profile module is the same row viewed by its owner.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — `PrivateRoute` wiring at lines 132–155; `requiredPermission` keys `user.read`/`user.create`/`user.update` on the three user routes. (`SITEMAP.md` in the same repo still shows the pre-RBAC "Authenticated" rows and lags the code.)
- `../carmen-platform/src/pages/UserManagement.tsx` — list page, avatar column with initials fallback, `getNameDisplay`, status/show-deleted filters, CSV export, Fetch Keycloak action, `<Can>`-gated Add/Edit/Delete, delete and hard-delete dialogs, the nested-`audit` flattening.
- `../carmen-platform/src/pages/UserEdit.tsx` — create/view/edit page, header avatar, User Details card, `<Can permission="user.update">` on the Edit toggle, Clusters card (read-only), Business Units card with Add BU dialog, Change Password dialog, the `BU_ROLES` constant, the `UserFormData` interface (7 fields).
- `../carmen-platform/src/services/userService.ts` — REST client (`/api-system/user`), `fetchKeycloakUsers`, `resetPassword`, `delete`, `hardDelete`.
- `../carmen-platform/src/components/Can.tsx` and `src/context/AuthContext.tsx` — the in-page gate component and the `hasPermission` resolver behind every gate above.

## 7. Pages in This Module

- [Data Model](/en/platform/users/data-model) — user entity fields, the profile extension (name parts, `avatar_file_token`), the `tb_cluster_user` join, the BU-user join with its per-BU role and `is_default` flag.
- [Lifecycle](/en/platform/users/lifecycle) — create flow, the effective-permissions sign-in gate, activate/deactivate via `is_active`, soft vs. hard delete, admin-initiated password reset, Keycloak sync.
- [UI Screens](/en/platform/users/ui-screens) — `UserManagement` list screen with its avatar column, filters, and Keycloak sync button, and the three-card `UserEdit` layout including the Add BU dialog and Change Password dialog.
