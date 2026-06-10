---
title: Platform RBAC — UI Screens
description: RoleManagement/RoleEdit with the PermissionPicker, the read-only Permission Catalog, the Super Admins list, and the User Platform assignment screens.
published: true
date: 2026-06-10T12:00:00.000Z
tags: book/platform, rbac, ui-screens
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Platform RBAC — UI Screens

> **At a Glance**
> **Screens:** `RoleManagement` (`/platform/roles`) · `RoleEdit` (`/platform/roles/new`, `/platform/roles/:id/edit`) · `PermissionCatalog` (`/platform/permissions`) · `SuperAdminManagement` (`/platform/super-admins`) · `UserPlatformManagement` (`/platform/user-platform`) · `UserPlatformEdit` (`/platform/user-platform/:userId`) &nbsp;·&nbsp; **Standard pattern:** Roles and User Platform list use the server-side `DataTable`; Catalog and Super Admins deviate (cards / plain rows) &nbsp;·&nbsp; **Key component:** `PermissionPicker` accordion grouped by resource &nbsp;·&nbsp; **In-page gates:** `<Can permission="user_platform.manage">` on the detail page only

## 1. Overview

Two of the four surfaces follow the Platform SPA's standard Management/Edit pattern: **Roles** (server-side `DataTable` list with debounced search, Sheet filters, CSV export, persisted `localStorage` state, plus a two-card create/view/edit page) and **User Platform** (the same `DataTable` list shape, though without a create route — users are created in the Users module, and the "edit" page manages role assignments rather than entity fields).

The other two deviate deliberately. **Permission Catalog** is a read-only reference: a responsive grid of cards grouped by resource, no table, no mutations, reached only from a header button on the Roles list (it has no sidebar entry). **Super Admins** is a two-card page — an add form and a plain row list — with no `DataTable`, no search, and no pagination; the expected population is a handful of rows.

All six screens ship the SPA's dev-only **Debug Sheet** — the amber floating button (bottom-right) that opens the raw JSON of the screen's API responses (`import.meta.env.DEV` only, never in production builds). On `RoleEdit` it carries two tabs, Role and Catalog, exposing both endpoint payloads — the fastest way for QA to inspect the actual envelope nesting and audit shapes described below.

## 2. Roles

### 2.1 `RoleManagement` — list (`/platform/roles`)

Header row: title "Roles" / subtitle "Manage platform roles and their permissions", and three header actions left to right — **Permission Catalog** (navigates to `/platform/permissions`), **Export** (client-side CSV of the loaded page: Name, Description, Permissions, Active; file `roles-<YYYY-MM-DD>.csv`; disabled while loading or empty), and **Add Role** (navigates to `/platform/roles/new`).

Below sits the standard search-and-filters row: a debounced (400 ms) search input over `name`/`description`, and a **Filters** Sheet with a single Status group (Active / Inactive toggle buttons → `advance` query `{ where: { is_active } }` when exactly one is selected). Active filter chips render below the search row.

`DataTable` columns in order:

| Column | Rendering |
|---|---|
| Name | Clickable — navigates to `/platform/roles/:id/edit` |
| Description | Muted text, `-` when empty |
| Permissions | `permission_count` as a secondary badge (`0` when absent); not sortable |
| Status | Active/Inactive badge from `is_active` |
| Created | `created_at` (`YYYY-MM-DD HH:mm:ss`, browser-local) + `created_by_name` on the next line — flattened from the nested `audit.created` `{ at, name }` shape when the API nests it |
| Updated | Same shape from `audit.updated`; renders `-` when `updated_at === created_at` |
| Actions | `⋯` dropdown: **Edit** (navigate) and **Delete** (opens a destructive `ConfirmDialog`; on confirm calls `DELETE /api-system/platform/roles/:id`) |

When the result set is empty the table is replaced by an `EmptyState` card ("No roles yet", with an inline Add Role CTA when no search term is active, or a `No roles matching "<term>"` message when one is). Default sort is `created_at:desc`. Persisted UI state:

| `localStorage` key | Stored type | Persists |
|---|---|---|
| `search_roles` | string | Search term |
| `filters_roles` | JSON string array | Status filter selections |
| `page_roles` | number string | Current page |
| `perpage_roles` | number string | Page size |
| `sort_roles` | string | Sort (`column:dir`) |

### 2.2 `RoleEdit` — create mode (`/platform/roles/new`)

Title "New Role". A two-card responsive grid (`lg:grid-cols-2`): **Role Details** (left) and **Permissions** (right). The form is immediately editable. Role Details carries `name` (required, validated on blur and pre-submit), `description` (textarea), and an `is_active` checkbox (default checked). The Permissions card hosts the `PermissionPicker` (§2.4); the catalog is fetched on mount and a spinner shows until it arrives.

On submit the SPA calls `POST /api-system/platform/roles` with `permissions: { add: <all selected keys> }`. On success it redirects to `/platform/roles/:id/edit` for the created id (falling back to the list when the response carries no id).

### 2.3 `RoleEdit` — view/edit mode (`/platform/roles/:id/edit`)

Loads via `GET /api-system/platform/roles/:id` and starts **read-only**: Role Details fields render as static text, the Status as a badge, and the Permissions card shows the granted keys grouped by resource prefix as monospace badges (or "No permissions granted."). An **Edit** button in the header switches both cards to editable; Cancel restores the pre-edit snapshot. Unsaved changes trigger the `useUnsavedChanges` navigation guard, and the global shortcuts save (`formRef.requestSubmit`) and cancel.

Saving computes the **permission delta** against the key set captured at fetch time — `add` = selected but not original, `remove` = original but not selected — and sends `PUT /api-system/platform/roles/:id` with `permissions: { add, remove }`. After a successful save the page refetches the role and drops back to view mode.

### 2.4 `PermissionPicker`

Shared component (`src/components/PermissionPicker.tsx`) rendering the catalog as a native `<details>` accordion, one group per `resource` in catalog order. Each group header shows the resource name, an `n/m` selected-count badge (when n > 0), and a **Select all / Clear all** toggle link; groups with any selection start expanded. Inside, checkboxes are laid out 2–3 per row and labelled with the `action` segment only — the full `description` appears as a hover tooltip (`title` attribute).

## 3. Permission Catalog

`PermissionCatalog` (`/platform/permissions`) is a read-only reference of every key in the catalog, loaded once via `GET /api-system/platform/permissions`. Header: a back arrow to `/platform/roles`, title "Permission Catalog", subtitle "Read-only reference of all platform permissions".

Content is a responsive card grid (2 columns at `sm`, 3 at `lg`), one card per resource preserving catalog order. Each card lists its permissions as a monospace outline badge with the full `resource.action` key, with the `description` in muted text beneath when present. There are no buttons, no search, no filters, and no mutation affordances of any kind — the catalog is backend-owned data. An empty catalog renders an `EmptyState` ("No permissions"). The screen has **no sidebar entry**; the only navigation paths in are the Roles header button and the URL itself.

## 4. Super Admins

`SuperAdminManagement` (`/platform/super-admins`) renders two stacked cards — not a `DataTable`:

- **Add Super Admin** — a native `<select>` plus an **Add** button. The dropdown is fed by `userService.getAll({ perpage: 200, sort: 'created_at:desc' })` and **excludes users who are already super admins**. Option labels compose `firstname middlename lastname (email)`, falling back to email/name/id. Add calls `POST /api-system/platform/super-admins` with `{ user_id }`, then refetches.
- **Current Super Admins** — a count badge in the card title and a divided row list. Each row shows the resolved display name (via the same user map), the raw `user_id` in monospace, "Added: `<created_at>`", an Active/Inactive badge (`is_active !== false` renders Active), and a destructive trash icon-button. Removal opens a `ConfirmDialog` warning that the user "will no longer bypass permission checks", then calls `DELETE /api-system/platform/super-admins/:id` with the **flag-row id**, not the user id.

The list response may nest multi-layer `{ data }` envelopes; the page descends them with a local `extractArray` helper until it finds the array. No UI state is persisted to `localStorage`.

## 5. User Platform

### 5.1 `UserPlatformManagement` — list (`/platform/user-platform`)

Header: title "User Platform" / subtitle "Assign platform roles and scope to users", with a single **Export** action (CSV: Username, Name, Email, Status; file `user-platform-<YYYY-MM-DD>.csv`). There is deliberately **no Add button** — the screen lists existing users (`GET /api-system/user` via `userService.getAll`); user creation belongs to the [users](/en/platform/users) module.

Search (400 ms debounce) and a Status filter Sheet match the Roles list. Columns:

| Column | Rendering |
|---|---|
| Username | Clickable — navigates to `/platform/user-platform/:userId` |
| Name | Composed from `firstname middlename lastname` (filtered, space-joined), falling back to `name`, then `-` |
| Email | Plain text |
| Status | Active/Inactive badge |
| Roles | Assignment count badge, **fetched per row in the background** after the page loads — an N+1 of `userRoleService.list(userId)` calls; a small spinner renders until each count resolves (failures count as `0`); not sortable |
| Created / Updated | Same flattened-audit shape as the Roles list; Updated suppressed when equal to Created |

Persisted UI state: `search_user_platform`, `status_filters_user_platform`, `page_user_platform`, `perpage_user_platform`, `sort_user_platform`.

### 5.2 `UserPlatformEdit` — detail (`/platform/user-platform/:userId`)

Header: back arrow to the list, the user's resolved name (`firstname lastname`, falling back to username/id) and email. The page body is a single **Roles & Scope** card listing the user's assignments (`GET /api-system/platform/users/:userId/roles`, descending nested `{ data }` envelopes). Each assignment row shows the role name (falling back to `role_id`) and a scope badge — the cluster's name (resolved against the cluster list, falling back to the raw `cluster_id`) for cluster-scoped rows, or "Platform" otherwise — plus a remove icon-button.

Mutating affordances are gated by `<Can permission="user_platform.manage">`: the **Add Role** header button, the inline add-role form, and every per-row remove button render only for holders of that key. A viewer with only `user_platform.read` sees the same card fully read-only.

### 5.3 Add-role form and removal

Clicking **Add Role** reveals an inline form (no dialog): a **Role** select fed by `roleService.getAll({ perpage: 200, sort: 'name:asc' })`, a **Scope** select with two options — `Platform` and `Specific cluster` — and, when cluster scope is chosen, a **Cluster** select fed by `clusterService.getAll({ perpage: 200, sort: 'name:asc' })`. Submitting validates that a role (and, for cluster scope, a cluster) is selected, then calls `POST /api-system/platform/users/:userId/roles` with `{ role_id, scope }` where `scope` is the discriminated union (`{ type: 'platform' }` or `{ type: 'cluster', cluster_id }`), and refetches the assignment list.

Removal opens a `ConfirmDialog` naming the role, then calls `DELETE /api-system/platform/users/:userId/roles/:assignmentId` with the assignment-row id. The detail page persists no UI state.

## 6. References

- `../carmen-platform/src/App.tsx` — route registrations for all six screens (lines 236–291).
- `../carmen-platform/src/pages/RoleManagement.tsx` — list columns, audit flattening, CSV export, persisted keys, delete confirm.
- `../carmen-platform/src/pages/RoleEdit.tsx` — two-card layout, view/edit toggle, permission delta computation (lines 174–187).
- `../carmen-platform/src/components/PermissionPicker.tsx` — resource-grouped accordion picker.
- `../carmen-platform/src/pages/PermissionCatalog.tsx` — read-only resource card grid.
- `../carmen-platform/src/pages/SuperAdminManagement.tsx` — add/remove cards, `extractArray` envelope descent, user-option exclusion.
- `../carmen-platform/src/pages/UserPlatformManagement.tsx` — list columns, background per-row roles count (N+1), persisted keys.
- `../carmen-platform/src/pages/UserPlatformEdit.tsx` — Roles & Scope card, `<Can>` gates, add-role form, scope badge resolution.
- `../carmen-platform/src/components/Can.tsx` — the permission-gated render wrapper.

**Cross-links:** [Platform RBAC landing](/en/platform/rbac) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
