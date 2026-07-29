---
title: Platform RBAC — UI Screens
description: RoleManagement/RoleEdit with the PermissionPicker and RolesAccessSummary, the read-only Permission Catalog, the redesigned DataTable-based Super Admins screen, and the User Platform assignment screens.
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, rbac, ui
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Platform RBAC — UI Screens

> **At a Glance**
> **Screens:** `RoleManagement` (`/platform/roles`) · `RoleEdit` (`/platform/roles/new`, `/platform/roles/:id/edit`) · `PermissionCatalog` (`/platform/permissions`) · `SuperAdminManagement` (`/platform/super-admins`) · `UserPlatformManagement` (`/platform/user-platform`) · `UserPlatformEdit` (`/platform/user-platform/:userId`) &nbsp;·&nbsp; **Standard pattern:** Roles, Super Admins (since 2026-07), and User Platform list all use the server-side `DataTable`; only Permission Catalog deviates (a read-only card grid) &nbsp;·&nbsp; **Key component:** `PermissionPicker` accordion grouped by resource &nbsp;·&nbsp; **In-page gates:** Roles list/edit gate Add/Edit/Delete and the Edit toggle (added since 2026-06-10); `<Can permission="user_platform.manage">` on the User Platform detail page &nbsp;·&nbsp; **Summary strips (new since 2026-07):** `RolesAccessSummary` on the Roles list, `PlatformAccessSummary` on the User Platform list

## 1. Overview

Three of the four surfaces follow the Platform SPA's standard Management/Edit pattern: **Roles** (server-side `DataTable` list with debounced search, Sheet filters, CSV export, a `RolesAccessSummary` strip, plus a create/view/edit page led by a `RoleIdentityHero` card), **User Platform** (the same `DataTable` list shape plus a `PlatformAccessSummary` strip, though without a create route — users are created in the Users module, and the "edit" page manages role assignments rather than entity fields), and, **since a 2026-07 rewrite**, **Super Admins** — no longer the two-card layout described in earlier syncs, it is now a server-rendered-style `DataTable` (search, no filters) with the Add action moved into the header as a modal dialog.

Only **Permission Catalog** still deviates: a read-only reference, a responsive grid of cards grouped by resource, no table, no mutations, reached only from a header button on the Roles list (it has no sidebar entry).

All six screens ship the SPA's dev-only **Debug Sheet** — the amber floating button (bottom-right) that opens the raw JSON of the screen's API responses (`import.meta.env.DEV` only, never in production builds). On `RoleEdit` it carries two tabs, Role and Catalog, exposing both endpoint payloads — the fastest way for QA to inspect the actual envelope nesting and audit shapes described below.

## 2. Roles

### 2.1 `RoleManagement` — list (`/platform/roles`)

Header row: title "Roles" / subtitle "Manage platform roles and their permissions", and three header actions left to right — **Permission Catalog** (navigates to `/platform/permissions`), **Export** (client-side CSV of the loaded page: Name, Description, Permissions, Active; file `roles-<YYYY-MM-DD>.csv`; disabled while loading or empty), and **Add Role** (navigates to `/platform/roles/new`, wrapped in `<Can permission="role.create">` — **added since 2026-06-10**, previously ungated).

**Added since 2026-06-10:** below the header sits a **`RolesAccessSummary`** strip (`roleManagement/RolesAccessSummary.tsx`) — a card showing the total role count (active/inactive breakdown) plus the three roles with the broadest permission grant, each as a name + horizontal bar (scaled to the widest role's `permission_count`) + count. It loads independently of the table (`perpage: -1`, ignoring the table's filters) and shows its own skeleton/error/retry state.

Below that sits the standard search-and-filters row: a debounced (400 ms) search input over `name`/`description`, and a **Filters** Sheet with a single Status group (Active / Inactive toggle buttons → `advance` query `{ where: { is_active } }` when exactly one is selected). Active filter chips render below the search row.

`DataTable` columns in order:

| Column | Rendering |
|---|---|
| Name | Clickable link — navigates to `/platform/roles/:id/edit` — with the role's `description` as muted subtext beneath it (**merged into this column; there is no separate Description column**) |
| Permissions | `permission_count` as a secondary badge (`0` when absent); not sortable |
| Status | Active/Inactive badge from `is_active` |
| Created | `created_at` (`YYYY-MM-DD HH:mm:ss`, browser-local) + `created_by_name` on the next line — flattened from the nested `audit.created` `{ at, name }` shape when the API nests it |
| Updated | Same shape from `audit.updated`; renders `-` when `updated_at === created_at` |
| Actions | `⋯` dropdown: **Edit** (navigate; `<Can permission="role.update">` — **added since 2026-06-10**) and **Delete** (opens a destructive `ConfirmDialog`; on confirm calls `DELETE /api-system/platform/roles/:id`; `<Can permission="role.delete">` — **added since 2026-06-10**). A `role.read`-only session now sees an empty dropdown, matching every other management list in the SPA |

When the result set is empty the table is replaced by an `EmptyState` card ("No roles yet", with an inline Add Role CTA — itself `<Can permission="role.create">`-gated — when no search term is active, or a `No roles matching "<term>"` message when one is). Default sort is `created_at:desc`. Persisted UI state:

| `localStorage` key | Stored type | Persists |
|---|---|---|
| `search_roles` | string | Search term |
| `filters_roles` | JSON string array | Status filter selections |
| `page_roles` | number string | Current page |
| `perpage_roles` | number string | Page size |
| `sort_roles` | string | Sort (`column:dir`) |

### 2.2 `RoleEdit` — layout (both modes, rewritten since 2026-06-10)

**The whole page layout changed.** The previous two-card `lg:grid-cols-2` grid (Role Details left, Permissions right) is gone. The page now opens with a **`RoleIdentityHero`** card (`roleEdit/RoleIdentityHero.tsx`) — a shield icon, the role name (or "(unnamed role)"), an Active/Inactive badge, and a one-line **permission-reach summary**: "Full access to every permission" (in amber, with a warning triangle, when the role's granted-key count reaches the catalog size), "No permissions granted yet", or "`N` permissions across `M` resources". The (existing, in view mode only) **Edit** button renders inside the hero's action slot, gated `<Can permission="role.update">`.

Below the hero, the form is a two-column grid (`lg:grid-cols-[1fr_minmax(300px,340px)]`) with the columns **swapped from the old layout**: **Permissions** is now the left/wide column (hosting the `PermissionPicker`, §2.4, when editing, or read-only resource-grouped badges otherwise) and **Settings** — renamed from "Role Details" — is the right/narrow sticky rail, carrying `name` (required), `description` (textarea), and an `is_active` checkbox/badge.

### 2.3 `RoleEdit` — create mode (`/platform/roles/new`)

Title comes from the hero (empty name shows "(unnamed role)"); the form is immediately editable (`editing = true` from mount) — there is no Edit button in create mode. On submit the SPA calls `POST /api-system/platform/roles` with `permissions: { add: <all selected keys> }`. On success it redirects to `/platform/roles/:id/edit` for the created id (falling back to the list when the response carries no id).

### 2.4 `RoleEdit` — view/edit mode (`/platform/roles/:id/edit`)

**Not-found gating (added since 2026-06-10):** a bad or deleted `id` renders a dedicated shell instead of the form — just the back link and a `SearchX`-icon `EmptyState` ("Role not found", "This role doesn't exist, or it may have been deleted…", a "Back to roles" button) — mirrors the same pattern added to clusters/business-units/users/applications/report-templates.

Loads via `GET /api-system/platform/roles/:id` and starts **read-only**: the Settings fields render as static text/badges, and the Permissions card shows the granted keys grouped by resource prefix as monospace badges (or "No permissions granted."). Clicking **Edit** (in the hero) switches to editable; **Cancel** (in the sticky bottom bar, §2.5) restores the pre-edit snapshot. Unsaved changes trigger the `useUnsavedChanges` navigation guard, and the global shortcuts save (`formRef.requestSubmit`) and cancel (only when `!isNew`).

Saving computes the **permission delta** against the key set captured at fetch time — `add` = selected but not original, `remove` = original but not selected — and sends `PUT /api-system/platform/roles/:id` with `permissions: { add, remove }` plus **`doc_version` when known (added since 2026-06-10)**. A version mismatch triggers the shared `notifyVersionConflict()` toast and re-fetches rather than silently overwriting. After a successful save the page refetches the role and drops back to view mode.

### 2.5 Sticky action bar (added since 2026-06-10)

Rendered only while `editing = true`, mirroring the pattern used across clusters/business-units/users/applications/report-templates: a `fixed bottom-0` bar with an unsaved-changes indicator (pulsing amber dot + "Unsaved changes", or "No changes" in muted text) on the left, and **Cancel** (hidden in create mode; disabled while saving) + **Create Role**/**Save Changes** (disabled while saving, or in edit mode when there are no changes) on the right.

### 2.6 `PermissionPicker`

Shared component (`src/components/PermissionPicker.tsx`) rendering the catalog as a native `<details>` accordion, one group per `resource` in catalog order. Each group header shows the resource name, an `n/m` selected-count badge (when n > 0), and a **Select all / Clear all** toggle link; groups with any selection start expanded. Inside, checkboxes are laid out 2–3 per row and labelled with the `action` segment only — the full `description` appears as a hover tooltip (`title` attribute).

## 3. Permission Catalog

`PermissionCatalog` (`/platform/permissions`) is a read-only reference of every key in the catalog, loaded once via `GET /api-system/platform/permissions`. Header: a back arrow to `/platform/roles`, title "Permission Catalog", subtitle "Read-only reference of all platform permissions".

Content is a responsive card grid (2 columns at `sm`, 3 at `lg`), one card per resource preserving catalog order. Each card lists its permissions as a monospace outline badge with the full `resource.action` key, with the `description` in muted text beneath when present. There are no buttons, no search, no filters, and no mutation affordances of any kind — the catalog is backend-owned data. An empty catalog renders an `EmptyState` ("No permissions"). The screen has **no sidebar entry**; the only navigation paths in are the Roles header button and the URL itself.

## 4. Super Admins

**Rewritten since 2026-06-10 — no longer the "two stacked cards, not a `DataTable`" screen described in the earlier sync.** `SuperAdminManagement` (`/platform/super-admins`) is now a standard-shaped management screen:

- **Header:** title "Super Admins" / subtitle "Platform users who bypass all permission checks", with two actions — **Export** (client-side CSV: User, User ID, Status, Added; file `super-admins-<YYYY-MM-DD>.csv`; disabled while loading or empty) and **Add Super Admin**, which now opens a **modal `Dialog`** rather than an inline card form.
- **Add Super Admin dialog:** a shadcn `Select` (searchable-style dropdown, not a native `<select>`) fed by `userService.getAll({ perpage: 200, sort: 'created_at:desc' })` and **excluding users who are already super admins**. Option labels compose `firstname middlename lastname (email)`, falling back to email/name/id. Confirming calls `POST /api-system/platform/super-admins` with `{ user_id }`, then refetches and closes the dialog.
- **List:** a single Card containing a debounced search input (client-side filter over the resolved display name and raw `user_id` — **added since 2026-06-10**, the previous version had no search) and a `DataTable` with columns **User** (resolved display name + raw `user_id` in monospace beneath), **Status** (Active/Inactive badge, `is_active !== false` renders Active), **Added** (`created_at`), and **Actions** (`⋯` dropdown with a destructive **Remove** item — replacing the previous version's inline trash icon-button). Removal opens a `ConfirmDialog` warning that the user "will no longer bypass permission checks", then calls `DELETE /api-system/platform/super-admins/:id` with the **flag-row id**, not the user id.

The list response may nest multi-layer `{ data }` envelopes; the page still descends them with a local `extractArray` helper until it finds the array — that part of the previous sync's finding is unchanged. No pagination controls (client-side search over a fully-loaded list, no server paging) and no other UI state is persisted to `localStorage` beyond the search term (`search_super_admins`, added since 2026-06-10).

## 5. User Platform

### 5.1 `UserPlatformManagement` — list (`/platform/user-platform`)

Header: title "User Platform" / subtitle "Assign platform roles and scope to users", with a single **Export** action (CSV: Username, Name, Email, Status; file `user-platform-<YYYY-MM-DD>.csv`). There is deliberately **no Add button** — the screen lists existing users (`GET /api-system/user` via `userService.getAll`); user creation belongs to the [users](/en/platform/users) module.

**Added since 2026-06-10:** below the header sits a **`PlatformAccessSummary`** strip (`userPlatformManagement/PlatformAccessSummary.tsx`) — a governance-band card summarising the whole user set (not just the current page/filter) by platform-role-assignment count, loaded via the same per-user `userRoleService.list()` N+1 pattern the table itself uses, extended to every user.

Search (400 ms debounce) and a Status filter Sheet match the Roles list. Columns:

| Column | Rendering |
|---|---|
| Username | Clickable — navigates to `/platform/user-platform/:userId` |
| Name | Composed from `firstname middlename lastname` (filtered, space-joined), falling back to `name`, then `-` |
| Email | Plain text |
| Status | Active/Inactive badge |
| Roles | Assignment count badge, **fetched per row in the background** after the page loads — an N+1 of `userRoleService.list(userId)` calls; a small spinner renders until each count resolves. **Corrected:** a failed per-row fetch does **not** silently count as `0` — it renders a distinct amber warning-triangle + "-" (aria-labelled "Couldn't load roles"), and a toast reports how many rows failed; not sortable |
| Created / Updated | Same flattened-audit shape as the Roles list; Updated suppressed when equal to Created |
| Actions | **Added since 2026-06-10.** `⋯` dropdown with a single ungated "Manage roles" item, navigating to the detail page — same destination as clicking the Username link |

Persisted UI state: `search_user_platform`, `status_filters_user_platform`, `page_user_platform`, `perpage_user_platform`, `sort_user_platform`.

### 5.2 `UserPlatformEdit` — detail (`/platform/user-platform/:userId`)

Header: back arrow to the list, the user's resolved name (`firstname lastname`, falling back to username/id) and email. The page body is a single **Roles & Scope** card listing the user's assignments (`GET /api-system/platform/users/:userId/roles`, descending nested `{ data }` envelopes). Each assignment row shows the role name (falling back to `role_id`) and a scope badge — the cluster's name (resolved against the cluster list, falling back to the raw `cluster_id`) for cluster-scoped rows, or "Platform" otherwise — plus a remove icon-button.

Mutating affordances are gated by `<Can permission="user_platform.manage">`: the **Add Role** header button, the inline add-role form, and every per-row remove button render only for holders of that key. A viewer with only `user_platform.read` sees the same card fully read-only.

### 5.3 Add-role form and removal

Clicking **Add Role** reveals an inline form (no dialog): a **Role** select fed by `roleService.getAll({ perpage: 200, sort: 'name:asc' })`, a **Scope** select with two options — `Platform` and `Specific cluster` — and, when cluster scope is chosen, a **Cluster** select fed by `clusterService.getAll({ perpage: 200, sort: 'name:asc' })`. Submitting validates that a role (and, for cluster scope, a cluster) is selected, then calls `POST /api-system/platform/users/:userId/roles` with `{ role_id, scope }` where `scope` is the discriminated union (`{ type: 'platform' }` or `{ type: 'cluster', cluster_id }`), and refetches the assignment list. The open add-role form is covered by `useUnsavedChanges` while any of its fields have been touched (a browser `beforeunload` warning, not a save prompt — the form has no saved baseline to restore).

Removal opens a `ConfirmDialog` naming the role, then calls `DELETE /api-system/platform/users/:userId/roles/:assignmentId` with the assignment-row id. The detail page persists no UI state.

## 6. References

- `../carmen-platform/src/App.tsx` — route registrations for all six screens (lines 241–296).
- `../carmen-platform/src/pages/RoleManagement.tsx` — list columns (name+description merged, `RolesAccessSummary`), audit flattening, CSV export, persisted keys, `<Can>`-gated Edit/Delete/Add.
- `../carmen-platform/src/pages/roleManagement/RolesAccessSummary.tsx` — the roles-count/breadth summary strip.
- `../carmen-platform/src/pages/RoleEdit.tsx` — hero + Permissions-left/Settings-right layout, not-found gating, `doc_version`, permission delta computation (`handleSubmit`, lines 176–230; delta at 202–205).
- `../carmen-platform/src/pages/roleEdit/RoleIdentityHero.tsx` — the hero card and `permissionSummary()` reach text.
- `../carmen-platform/src/components/PermissionPicker.tsx` — resource-grouped accordion picker.
- `../carmen-platform/src/pages/PermissionCatalog.tsx` — read-only resource card grid.
- `../carmen-platform/src/pages/SuperAdminManagement.tsx` — the rewritten `DataTable` + Add-dialog screen, `extractArray` envelope descent, user-option exclusion.
- `../carmen-platform/src/pages/UserPlatformManagement.tsx` — list columns incl. the new Actions column, `PlatformAccessSummary`, background per-row roles count (N+1) with distinct error state, persisted keys.
- `../carmen-platform/src/pages/userPlatformManagement/PlatformAccessSummary.tsx` — the governance-band summary strip.
- `../carmen-platform/src/pages/UserPlatformEdit.tsx` — Roles & Scope card, `<Can>` gates, add-role form, scope badge resolution.
- `../carmen-platform/src/components/Can.tsx` — the permission-gated render wrapper.
- `../carmen-platform/src/pages/Forbidden.tsx` — the renamed 403 page rendered on a failed route guard (see [Permissions](./permissions.md)).

**Cross-links:** [Platform RBAC landing](/en/platform/rbac) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
