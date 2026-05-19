---
title: Users
description: Platform-level user accounts — identity, the `platform_role` field that drives every role gate elsewhere, and the cluster/BU assignments that scope what the user can reach in the inventory app.
published: true
date: 2026-05-19T22:00:00.000Z
tags: platform/users, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Users

> **At a Glance**
> **Module purpose:** Authoring surface for the platform-level user account — one row per person who can sign in, holding the identity fields (`username`, `email`, name parts, `alias_name`), the single `platform_role` value that every other module's `allowedRoles` array checks, the `is_active` flag, and the read-only views of which clusters and BUs the user is assigned to (assignments themselves are mutated from the cluster side or, for BUs, from the Add-BU dialog inside this page) &nbsp;·&nbsp; **Audience:** Any authenticated platform user — same open-access shape as Business Units; Carmen support engineers and customer-side admins both use it &nbsp;·&nbsp; **Key entities/tables:** `user` (8 form fields: `username`, `email`, `platform_role`, `alias_name`, `firstname`, `middlename`, `lastname`, `is_active`; plus soft-delete trio `deleted_at`/`deleted_by_name`/timestamps), `tb_cluster_user` (M:N cluster join — read-only here), BU-user join (M:N BU assignment with per-BU `role` of `admin`/`user` and an `is_default` flag) &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The Users module exposes the platform-level user aggregate through the
same two-screen pattern used everywhere else in the Platform SPA:

- **`/users` → `UserManagement`** — server-side `DataTable` with
  debounced search, a Sheet-based filters panel (Role multi-select over
  the seven `PLATFORM_ROLES` values, Active/Inactive status,
  "show soft-deleted"), CSV export, persisted UI state in `localStorage`
  (search, page, perpage, sort, role/status filters, show-deleted
  toggle), plus two header actions unique to this module: **Fetch
  Keycloak** (calls `userService.fetchKeycloakUsers()` to pull the
  current Keycloak user list into the platform DB) and the standard
  **Add User**.
- **`/users/new` → `UserEdit` (create mode)** — single "User Details"
  card with the eight form fields; on successful create the page
  `navigate(..., { replace: true })`s to the edit route for the new id.
- **`/users/:id/edit` → `UserEdit` (view/edit mode)** — three stacked
  cards. The **User Details** card is view-only by default and switched
  to editable via the Edit button (in edit mode, `username` is disabled
  — it is set once at create). The **Clusters** card is read-only and
  lists the `tb_cluster_user` join rows: each card shows the cluster
  name/code, an active/inactive badge, and the per-cluster role
  (`admin` or `user`). The **Business Units** card lists the BU-user
  join rows with per-BU role, `is_default` badge, and a Trash icon to
  remove; it has its own **Add BU** dialog whose available BUs are
  scoped to clusters the user is already a member of.

The header on the edit screen also exposes a **Change Password** action
(admin-initiated password reset via `userService.resetPassword`, with
a confirm-twice dialog) and the list page exposes a hard-delete dialog
that requires the operator to type the username/email to confirm.

## 2. Business Context

A user record is the platform's source of truth for "this person can
sign in." The `platform_role` field is the single value that every
`allowedRoles` array elsewhere in the SPA checks — clusters and report
templates restrict to `platform_admin`/`support_manager`/`support_staff`,
business units and users themselves are open to any authenticated role,
and the inventory app reads the same value to decide whether someone is
a Carmen-internal operator or a customer-side user. Because that
single field drives so many downstream gates, getting it right at
user-create time is the most consequential decision on this page.

Beyond the platform role, the user record also captures **where** the
user can operate. Cluster membership lives in `tb_cluster_user` and is
mutated from the cluster edit page (Section 5 cross-link); the Users
module shows the resulting set read-only as the Clusters card on the
edit screen. BU membership is per-cluster — the **Add BU** dialog on
this page only lists BUs whose `cluster_id` matches one of the user's
current cluster memberships, which keeps the tenant boundary clean: a
user cannot be assigned to a BU outside the clusters they already
belong to. The BU-user join carries its own `role` (`admin` or `user`,
orthogonal to `platform_role`) and an `is_default` flag that marks the
BU the inventory app should land on at login.

Two additional flows are admin-only by convention even though the
routes are open to all authenticated users: the **Fetch Keycloak** sync
button (only meaningful for operators with backend admin access to
Keycloak) and the **Hard Delete** action (typed-username confirmation
on the list page, vs. the standard soft-delete from the row's action
menu).

## 3. Key Concepts

- **User** — one row in `user` representing one identity that can sign
  in. Eight editable fields: `username` (set once at create, then
  disabled), `email`, `platform_role`, `alias_name`, `firstname`,
  `middlename`, `lastname`, and `is_active`. The list response also
  surfaces `created_at`/`created_by_name` and `updated_at`/
  `updated_by_name` for the audit columns and `deleted_at`/
  `deleted_by_name` for the soft-delete badge.
- **Platform role** — a single value picked from the seven-element
  `PLATFORM_ROLES` constant: `super_admin`, `platform_admin`,
  `support_manager`, `support_staff`, `security_officer`,
  `integration_developer`, `user`. This is the field that every other
  module's `allowedRoles` array tests against; changing it changes what
  modules the user can reach next time they sign in. Note: only 5 of
  these 7 values (`platform_admin`, `super_admin`, `support_manager`,
  `support_staff`, `security_officer`) appear in `AuthContext.ALLOWED_ROLES`
  and can authenticate against the Platform admin SPA — `integration_developer`
  and `user` are valid data values but their holders cannot sign in. See
  [[auth-roles]] for the login flow.
- **Cluster assignments (`tb_cluster_user`)** — M:N join between user
  and cluster, carrying a per-cluster `role` of `admin` or `user`. The
  Users edit page shows this read-only as the Clusters card; mutation
  happens from the cluster edit page's Users card. A user must be a
  cluster member before they can be added to one of that cluster's BUs.
- **BU assignments** — M:N join between user and business unit, with
  its own per-BU `role` (`admin` or `user`, from the `BU_ROLES`
  constant), `is_active` flag, and `is_default` flag. The Users edit
  page is the canonical place to add and remove these rows; the **Add
  BU** dialog filters available BUs to those belonging to clusters the
  user is already in.
- **Active flag (`is_active`)** — toggles whether the user can sign in.
  Independent from soft-delete; an active user can still be on the way
  out, or an inactive user can be retained for audit before deletion.
- **Soft delete vs. hard delete** — the row-level action menu offers
  both. Soft delete sets `deleted_at`/`deleted_by_name`; the list view
  hides those rows unless the "Show soft-deleted users" filter is on,
  and surfaces a red "Deleted" badge plus a "Deleted By" column. Hard
  delete is permanent and gated by a dialog requiring the operator to
  type the exact username/email.
- **Keycloak sync** — `userService.fetchKeycloakUsers()` is exposed as
  a header button on the list page. It refreshes the platform's user
  list from Keycloak; the page reloads the table after success.
- **Admin password reset** — the edit screen's header has a **Change
  Password** action that opens a dialog with new + confirm fields
  (minimum 6 chars, must match). Submits to
  `userService.resetPassword(id, newPassword)`. There is no email-link
  flow in this surface — the reset is admin-initiated and immediate.

## 4. Roles and Personas

All three user routes are wrapped in `PrivateRoute` **without an
`allowedRoles` prop** — confirmed by reading
`../carmen-platform/src/App.tsx` (lines 87–109) and
`../carmen-platform/SITEMAP.md` (rows for `/users`, `/users/new`,
`/users/:id/edit` all list "Authenticated"). Any user with a valid
session reaches these routes. `UserEdit.tsx` does not gate individual
buttons (Edit, Save, Change Password, Add BU, Trash on BU rows) by
platform role either; `UserManagement.tsx` does not gate Fetch
Keycloak, Export, Add User, Delete, or Hard Delete by platform role.
The only role concepts the page handles are **data** it edits — the
user's own `platform_role` field and the per-BU `role` on assignment
rows — not gates on it.

| Persona | Route access | What they typically do here |
|---|---|---|
| All authenticated platform users | Full access to list, create, edit, soft-delete, hard-delete users, fetch from Keycloak, change passwords, and assign/unassign BUs | Whatever the operational context calls for — Carmen support engineers onboard new customer users and reset passwords; customer-side admins update their own staff's contact info and BU roster |

Because there is no `allowedRoles` array, who can mutate user state at
the API level is the responsibility of the backend and provisioning
process, not this admin surface. The Section 5 cross-links cover how
the platform's more strictly gated admin surfaces (clusters, report
templates) read the `platform_role` value written here.

## 5. Related Modules

- [[business-units]] — supplies the BUs that show up in the user's
  Business Units card; assignments created here appear on the BU's own
  Users card. Both pages mutate the same BU-user join with the same
  `BU_ROLES` (`admin`/`user`) and `is_default` flag.
- [[clusters]] — supplies the clusters that show up in the user's
  Clusters card (read-only here); the cluster edit page is the
  canonical place to add/remove `tb_cluster_user` rows. The Users
  module gates BU-assignment dropdowns by current cluster membership,
  so cluster membership must be granted from the cluster side first.
- [[auth-roles]] — defines what each of the seven `platform_role`
  values means and which `allowedRoles` arrays they appear in across
  the SPA. Changing `platform_role` here changes what modules the user
  reaches next sign-in.
- [[profile]] — the user's own first-person view of the same user
  record; the avatar menu's "Profile" link lands there. The Users
  module is the third-person admin view, the Profile module is the
  same row viewed by its owner.

## 6. Reference Sources

- `../carmen-platform/SITEMAP.md` — the route table is the source of
  truth for the three user routes (all "Authenticated").
- `../carmen-platform/src/App.tsx` — `PrivateRoute` wiring at lines
  87–109; confirms no `allowedRoles` prop on any user route.
- `../carmen-platform/src/pages/UserManagement.tsx` — list page,
  role/status/show-deleted filters, CSV export, Fetch Keycloak action,
  delete and hard-delete dialogs, the `PLATFORM_ROLES` constant.
- `../carmen-platform/src/pages/UserEdit.tsx` — create/view/edit page,
  User Details card, Clusters card (read-only), Business Units card
  with Add BU dialog, Change Password dialog, the `BU_ROLES` and
  `PLATFORM_ROLES` constants, the `UserFormData` interface.
- `../carmen-platform/src/services/userService.ts` — REST client
  (`/api-system/user`), `fetchKeycloakUsers`, `resetPassword`,
  `delete`, `hardDelete`.

## 7. Pages in This Module

- [[users/data-model|Data Model]] — user entity fields, the
  `platform_role` enum, the `tb_cluster_user` join, the BU-user join
  with its per-BU role and `is_default` flag.
- [[users/lifecycle|Lifecycle]] — create flow, activate/deactivate via
  `is_active`, soft vs. hard delete, admin-initiated password reset,
  Keycloak sync.
- [[users/ui-screens|UI Screens]] — `UserManagement` list screen with
  its filters and Keycloak sync button, and the three-card `UserEdit`
  layout including the Add BU dialog and Change Password dialog.
