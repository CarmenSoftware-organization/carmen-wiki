---
title: Users
description: Platform-level user accounts — identity, avatars, and the cluster/BU assignments that scope what the user can reach in the inventory app. Platform-admin access itself is granted via RBAC role assignments.
published: true
date: 2026-07-29T07:06:05.000Z
tags: platform/users, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Users

> **At a Glance**
> **Module purpose:** Authoring surface for the platform-level user account — one row per person who can sign in, holding the identity fields (`username`, `email`, name parts, `alias_name`), the avatar, the `is_active` flag, and the read-only views of which clusters and BUs the user is assigned to (assignments themselves are mutated from the cluster side or, for BUs, from the Add-BU dialog inside this page). What the account can *do* in the Platform admin SPA is not stored here — that is the [RBAC](/en/platform/rbac) module's role assignments &nbsp;·&nbsp; **Audience:** Holders of the `user.read`/`user.create`/`user.update`/`user.delete` permission keys — typically Carmen support engineers and customer-side admins &nbsp;·&nbsp; **Key entities/tables:** `tb_user` + `tb_user_profile` (7 form fields: `username`, `email`, `alias_name`, `firstname`, `middlename`, `lastname`, `is_active`; plus soft-delete trio `deleted_at`/`deleted_by_name`/timestamps and a presigned `avatar_url` on read), `tb_cluster_user` (M:N cluster join — read-only here), BU-user join (M:N BU assignment with per-BU `role` of `admin`/`user` and an `is_default` flag) &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The Users module exposes the platform-level user aggregate through the same two-screen pattern used everywhere else in the Platform SPA:

- **`/users` → `UserManagement`** — server-side `DataTable` with a leading avatar column (initials fallback in a circular badge, real presigned `avatar_url` layered on top when present), a **Directory** summary strip (`UserDirectorySummary` — total/active/inactive/archived counts plus a "Recently added" overlapping-avatar stack of the newest users), debounced search, a Sheet-based filters panel (Active/Inactive status and "show soft-deleted"), CSV export, persisted UI state in `localStorage` (search, page, perpage, sort, status filters, show-deleted toggle), a **BU** column (active/total business-unit-assignment count per user, new since the last sync), Created/Updated audit columns, plus two header actions unique to this module: **Fetch Keycloak** (calls `userService.fetchKeycloakUsers()` to pull the current Keycloak user list into the platform DB — now gated `<Can permission="user.create">`) and **Add User** (also `user.create`). For super-admin sessions only, row checkboxes enable **bulk soft-delete** and **bulk hard-delete** (the latter behind a random 6-character confirmation code). Row Edit and Delete/Hard-Delete actions are gated in-page by `user.update` and `user.delete`; the single-row hard-delete dialog also gained a super-admin-only "Copy username" clipboard button.
- **`/users/new` → `UserEdit` (create mode)** — single "Account details" card with the seven form fields; on successful create the page `navigate(..., { replace: true })`s to the edit route for the new id.
- **`/users/:id/edit` → `UserEdit` (view/edit mode)** — a **`UserIdentityHero`** card (avatar, name as the page's only `<h1>`, username/email/alias chips, Active/Inactive badge, an "Access to N business units across M clusters" summary line, and — in view mode only — Change Password + Edit action buttons) replaces the previous plain header. The **User Details** card underneath is still view-only by default and switched to editable via the same Edit button (wrapped in `<Can permission="user.update">`; in edit mode, `username` is disabled — it is set once at create). Below it, the former separate Clusters card and Business Units card have been **merged into one `UserAccessTree` card** — a single hierarchy of the user's clusters, each expandable to the business units assigned within it (with an "Other business units" catch-all group for any BU assignment whose cluster isn't among the user's own memberships); its own **Add BU** dialog is scoped to clusters the user already belongs to, same as before. A not-found empty state now gates the whole page shell when the id doesn't resolve, and saves are guarded by a `doc_version` optimistic-lock token — all three patterns shared with [clusters](/en/platform/clusters)/[business-units](/en/platform/business-units).

The header on the edit screen also exposes a **Change Password** action (admin-initiated password reset via `userService.resetPassword`, with a confirm-twice dialog) and the list page exposes a hard-delete dialog that requires the operator to type the username/email to confirm.

## 2. Business Context

A user record is the platform's source of truth for "this person can sign in." What the account can *do* in the Platform admin SPA is no longer stored on the user row: the legacy single-value `platform_role` enum was removed (frontend commit `6091ffc`; the column and `enum_platform_role` are gone from the Prisma platform schema). Platform-level access is now granted through RBAC role assignments managed on the separate **User Platform** screen (`/platform/user-platform`) — the Users module manages the *account*; role and scope assignment lives in the [RBAC](/en/platform/rbac) module. At login the SPA validates the account's effective permissions (`GET /api/user/permission/platform`) and rejects sessions that hold none, with a bootstrap exception while the platform has 0–1 users — so a freshly created account cannot reach the Platform admin SPA until someone assigns it a role.

Beyond identity, the user record also captures **where** the user can operate. Cluster membership lives in `tb_cluster_user` and is mutated from the cluster edit page (Section 5 cross-link); the Users module shows the resulting set read-only, nested inside the `UserAccessTree` card on the edit screen. BU membership is per-cluster — the **Add BU** dialog on this page only lists BUs whose `cluster_id` matches one of the user's current cluster memberships, which keeps the tenant boundary clean: a user cannot be assigned to a BU outside the clusters they already belong to. The BU-user join carries its own `role` (`admin` or `user`, orthogonal to the platform RBAC assignments) and an `is_default` flag that marks the BU the inventory app should land on at login.

Two additional flows deserve care beyond their UI gates: the **Fetch Keycloak** sync button (now behind `<Can permission="user.create">` — corrected since the last sync, when it carried no in-page gate — and only meaningful for operators with backend admin access to Keycloak) and the **Hard Delete** action (gated `user.delete`, plus a typed-username confirmation on the list page, vs. the standard soft-delete from the row's action menu — with a bulk equivalent for super-admins, §3).

## 3. Key Concepts

- **User** — one row in `tb_user` representing one identity that can sign in. Seven editable fields: `username` (set once at create, then disabled), `email`, `alias_name`, `firstname`, `middlename`, `lastname`, and `is_active`. The list response also surfaces `created_at`/`created_by_name` and `updated_at`/ `updated_by_name` for the audit columns (flat fields win; nested `audit` object is the fallback) and `deleted_at`/ `deleted_by_name` for the soft-delete badge.
- **Platform access via RBAC assignments** — what the account can reach in the Platform admin SPA is decided by role assignments (platform-wide or per-cluster scope), managed on the `/platform/user-platform` screen — *not* on the user edit page. The login gate admits a session only when it holds at least one effective permission, carries the super-admin flag, or the bootstrap exception (total user count 0–1) applies. See [Platform RBAC](/en/platform/rbac) for the catalog/roles/assignments model and the login walkthrough; until 2026-06-10 this was a single `platform_role` enum on the user row, now removed.
- **Avatar** — stored as `avatar_file_token` on `tb_user_profile`; the API resolves it to a presigned `avatar_url` string on list and detail responses. The list's leading column, the Directory strip's "Recently added" faces, and the edit-page's `UserIdentityHero` all render a circular avatar with an initials fallback (first letters of `firstname`+`lastname`) and layer the real image on top when `avatar_url` is present, hiding it again on load error. `tb_user_profile` also gained a `signature_file_token` column (see [Data Model](/en/platform/users/data-model) §2.4) with no SPA surface yet.
- **Display name** — the list's Name column is composed by the `getNameDisplay` helper: when any of `firstname`/`middlename`/`lastname` is set, the non-empty parts are joined with spaces; otherwise the flat `name` field is shown, falling back to `-`.
- **BU count column** — the list now shows an active/total business-unit-assignment count per user (`Building2` icon, green active count over grey total), sourced from the same `business_unit` array the Directory strip uses to count distinct BUs spanned by the whole population.
- **Cluster assignments (`tb_cluster_user`)** — M:N join between user and cluster, carrying a per-cluster `role` of `admin` or `user`. The Users edit page shows this read-only, grouped inside the `UserAccessTree` card; mutation happens from the cluster edit page's Users section. A user must be a cluster member before they can be added to one of that cluster's BUs.
- **BU assignments** — M:N join between user and business unit, with its own per-BU `role` (`admin` or `user`, from the `BU_ROLES` constant), `is_active` flag, and `is_default` flag. The Users edit page is the canonical place to add and remove these rows; the **Add BU** dialog filters available BUs to those belonging to clusters the user is already in.
- **Active flag (`is_active`)** — toggles whether the user can sign in. Independent from soft-delete; an active user can still be on the way out, or an inactive user can be retained for audit before deletion.
- **Soft delete vs. hard delete** — the row-level action menu offers both, each wrapped in `<Can permission="user.delete">`. Soft delete sets `deleted_at`/`deleted_by_name`; the list view hides those rows unless the "Show soft-deleted users" filter is on, and surfaces a red "Deleted" badge (whose tooltip names the deleter via `deleted_by_name`) plus a "Deleted By" column. Hard delete is permanent and additionally gated by a dialog requiring the operator to type the exact username/email. **New: bulk versions of both, super-admin only** (`isSuperAdmin`, not a `user.*` permission key) — row checkboxes appear only for super-admin sessions, a selected-rows toolbar offers bulk Delete (a plain confirm) and bulk Hard Delete (behind a random 6-character code the operator must retype, distinct from the single-row flow's exact-username requirement), and each fires one request per selected user (`Promise.allSettled`) with an aggregate success/failure toast.
- **Keycloak sync** — `userService.fetchKeycloakUsers()` is exposed as a header button on the list page, now gated `user.create`. It refreshes the platform's user list from Keycloak; the page reloads the table and the Directory summary after success.
- **Admin password reset** — the edit screen's header has a **Change Password** action that opens a dialog with new + confirm fields (minimum 6 chars, must match). Submits to `userService.resetPassword(id, newPassword)`. There is no email-link flow in this surface — the reset is admin-initiated and immediate.
- **Optimistic concurrency (`doc_version`)** — `tb_user` and `tb_user_profile` both carry a `doc_version` counter (added 2026-07-16, all 35 platform tables). `UserEdit` resends it on every `PUT`; a stale write is rejected with `409` and shows a conflict toast + reload instead of overwriting silently.

## 4. Roles and Personas

All three user routes are wrapped in `PrivateRoute` with a `requiredPermission` prop — confirmed by reading `../carmen-platform/src/App.tsx` (route block, lines 152–174) — and the sidebar's "Users" entry (Organization group, `Layout.tsx` line 56) is filtered by the same `user.read` key. In-page mutations are additionally wrapped in `<Can>` gates or, for the two access-tree BU actions, a permission-derived boolean computed in `UserEdit.tsx` (`canAddBU`) or a direct `<Can>` on the row (`UserAccessTree.tsx`). Unlike the Clusters and Business Units pages, the route-level and header/row gates pass no `clusterId` — but the two BU-assignment actions inside `UserAccessTree` now DO resolve against `cluster.update` scoped per-cluster (see below), a correction from the prior sync.

| Surface | Gate |
|---|---|
| `/users` (list) | route guard `user.read` |
| `/users/new` (create) | route guard `user.create` |
| `/users/:id/edit` (view/edit) | route guard `user.update` |
| Add User (list header + empty state) | `<Can permission="user.create">` |
| Fetch Keycloak (list header) | `<Can permission="user.create">` — **corrected since the last sync**, previously undocumented as gated |
| Row action: Edit | `<Can permission="user.update">` |
| Row actions: Delete + Hard Delete | `<Can permission="user.delete">` |
| Bulk Delete / Bulk Hard Delete (list, row checkboxes) | `isSuperAdmin` only — not a `user.*` permission key |
| Edit toggle (edit-page hero) | `<Can permission="user.update">` |
| Add BU button (Access card) | `canAddBU` — `hasPermission('cluster.update', { clusterId })` across the user's own cluster memberships, **not** merely "has any cluster" (a prior data-condition-as-permission bug, since fixed) |
| Remove BU (Trash icon, Access card) | `<Can permission="cluster.update" clusterId={bu's own cluster_id}>` — scoped to the BU's cluster, not the viewer's |

Not gated in-page (visible to anyone who passes the route guard): **Export** and **Change Password**. For these, backend enforcement is the real boundary. Note that the `user.*` keys gate account CRUD only; role/scope assignment is gated by the separate `user_platform.*` keys on the [RBAC](/en/platform/rbac) screens.

| Persona | Typical keys | What they typically do here |
|---|---|---|
| Carmen support engineer / customer-side admin | `user.read` + `user.create`/`user.update`/`user.delete` | Onboard new customer users, reset passwords, update staff contact info, manage the BU roster |
| Read-only auditor | `user.read` only | Browse the list only — the username link targets `/users/:id/edit`, which the `user.update` route guard blocks with `Forbidden` (no read-only detail route exists); Add User, row Edit/Delete, and the Edit toggle do not render |

## 5. Related Modules

- [business-units](/en/platform/business-units) — supplies the BUs that show up in the user's Access card; assignments created here appear on the BU's own Users card. Both pages mutate the same BU-user join with the same `BU_ROLES` (`admin`/`user`) and `is_default` flag.
- [clusters](/en/platform/clusters) — supplies the clusters that show up in the user's Access card (read-only here); the cluster edit page is the canonical place to add/remove `tb_cluster_user` rows. The Users module gates BU-assignment dropdowns by current cluster membership, so cluster membership must be granted from the cluster side first.
- [rbac](/en/platform/rbac) — owns the access side of the user: the permission catalog, roles, scoped assignments (`/platform/user-platform`), the super-admin flag, and the effective-permissions login gate. The Users module creates the account; RBAC decides what it can do.
- [profile](/en/platform/profile) — the user's own first-person view of the same user record; the avatar menu's "Profile" link lands there. The Users module is the third-person admin view, the Profile module is the same row viewed by its owner.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — `PrivateRoute` wiring (route block, lines 152–174); `requiredPermission` keys `user.read`/`user.create`/`user.update` on the three user routes. (`SITEMAP.md` in the same repo still shows the pre-RBAC "Authenticated" rows and lags the code.)
- `../carmen-platform/src/pages/UserManagement.tsx` and `userManagement/UserDirectorySummary.tsx` — list page: Directory summary strip, avatar column with initials fallback, `getNameDisplay`, BU-count column, status/show-deleted filters, CSV export, `<Can>`-gated Fetch Keycloak/Add/Edit/Delete, single and bulk (super-admin) soft/hard-delete dialogs, the nested-`audit` flattening.
- `../carmen-platform/src/pages/UserEdit.tsx` and `userEdit/{UserIdentityHero,UserAccessTree}.tsx` — create/view/edit page: hero card, User Details card, `<Can permission="user.update">` on the Edit toggle, the merged cluster+BU `UserAccessTree` card with `canAddBU`/scoped-Remove permission checks, Add BU dialog, Change Password dialog, `doc_version` wiring, the `BU_ROLES` constant, the `UserFormData` interface (7 fields).
- `../carmen-platform/src/services/userService.ts` — REST client (`/api-system/user`), `fetchKeycloakUsers`, `resetPassword`, `delete`, `hardDelete`.
- `../carmen-platform/src/utils/docVersion.ts` — `getDocVersion`/`isVersionConflict`/`notifyVersionConflict` optimistic-lock helpers used by `UserEdit.tsx`.
- `../carmen-platform/src/components/Can.tsx` and `src/context/AuthContext.tsx` — the in-page gate component and the `hasPermission` resolver behind every gate above.

## 7. Pages in This Module

- [Data Model](/en/platform/users/data-model) — user entity fields (incl. `doc_version`), the profile extension (name parts, `avatar_file_token`, `signature_file_token`), the `tb_cluster_user` join, the BU-user join with its per-BU role and `is_default` flag.
- [Lifecycle](/en/platform/users/lifecycle) — create flow, the effective-permissions sign-in gate, activate/deactivate via `is_active`, soft vs. hard delete (incl. bulk, super-admin-only), admin-initiated password reset, Keycloak sync.
- [UI Screens](/en/platform/users/ui-screens) — `UserManagement` list screen with its Directory strip, avatar column, BU-count column, filters, bulk actions, and Keycloak sync button, and the `UserEdit` hero + Access-tree layout including the Add BU dialog and Change Password dialog.
