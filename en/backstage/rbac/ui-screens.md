---
title: Backstage Roles — UI Screens
description: RoleManagement/RoleEdit with the catalog-anchored RolesAccessSummary and the resource-row PermissionGrid, the read-only Permission Catalog, and (summary-level) the redesigned Super Admins roster and Backstage Users assignment screens.
published: true
date: 2026-10-29T05:30:00.000Z
tags: book/backstage, rbac, ui
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Backstage Roles — UI Screens

> **At a Glance**
> **Screens:** `RoleManagement` (`/backstage/roles`) · `RoleEdit` (`/backstage/roles/new`, `/backstage/roles/:id/edit`) · `PermissionCatalog` (`/backstage/category-permissions`) · `SuperAdminManagement` (`/backstage/super-admins`) · `UserBackstageManagement` (`/backstage/user-backstage`) · `UserBackstageEdit` (`/backstage/user-backstage/:userId`) &nbsp;·&nbsp; **Standard pattern:** Roles and Backstage Users list use the server-side `DataTable`; Super Admins (rewritten again 2026-09-02) is a card-based roster, not a table; Permission Catalog is a read-only card grid &nbsp;·&nbsp; **Key component:** `PermissionGrid` — every catalog action shown as a per-resource row, toggle buttons in edit mode, withheld actions dimmed rather than hidden (replaced the accordion `PermissionPicker` on 2026-08-20) &nbsp;·&nbsp; **In-page gates:** Roles list/edit gate Add/Edit/Delete and the Edit toggle with `backstage_role.*` keys; `<Can permission="user_backstage.manage">` on the Backstage Users detail page &nbsp;·&nbsp; **Summary strips:** `RolesAccessSummary` on the Roles list (now catalog-anchored, since 2026-09-02), `BackstageAccessSummary` on the Backstage Users list

![Backstage Roles — UI Screens screen](/screenshots/platform/rbac/ui-screens.png)

![Backstage Roles — UI Screens form screen](/screenshots/platform/rbac/ui-screens-form.png)

**Scope note:** this page verifies §2 (Roles) and §3 (Permission Catalog) against current source in full. §4 (Super Admins) and §5 (Backstage Users) are updated at a summary level only — see the scope note on the [module landing page](/en/backstage/rbac).

## 1. Overview

**Roles** follows the Platform SPA's standard Management/Edit pattern: a server-side `DataTable` list with debounced search, Sheet filters, CSV export, a `RolesAccessSummary` strip, plus a create/view/edit page led by a `RoleIdentityHero` card. **Permission keys renamed from `role.*` to `platform_role.*` (now `backstage_role.*`, `318949a3`) and the Permission Catalog route moved to `/backstage/category-permissions` on 2026-08-20** (`carmen-backstage` commit `8df0b10`) — see the [module landing](/en/backstage/rbac) and [Permissions](/en/backstage/rbac/permissions) for the full rename.

**Permission Catalog** is a read-only reference: a responsive grid of cards grouped by resource, no table, no mutations, reached only from a header button on the Roles list. It has no sidebar entry and, unlike every other screen in this module, **no permission gate at the SPA route level at all** — any authenticated platform user can navigate to it directly. Its data fetch is still backend-enforced on `backstage_role.read` (§3).

**Backstage Users** and **Super Admins** are summarized in §4/§5 per the scope note above; both went through further redesigns since the module's last full sync (`carmen-backstage` PRs #244/#250/#251, all 2026-09-02) that are not verified line-by-line here.

All six screens ship the SPA's dev-only **Debug Sheet** — the amber floating button (bottom-right) that opens the raw JSON of the screen's API responses (`import.meta.env.DEV` only, never in production builds). On `RoleEdit` it carries two tabs, Role and Catalog, exposing both endpoint payloads — the fastest way for QA to inspect the actual envelope nesting and audit shapes described below.

## 2. Roles

### 2.1 `RoleManagement` — list (`/backstage/roles`)

Header row: title "Roles" / subtitle "Manage platform roles and their permissions", and three header actions left to right — **Permission Catalog** (navigates to `/backstage/category-permissions`), **Export** (client-side CSV of the loaded page: Name, Description, Permissions, Active, Created At/By, Updated At/By — via `auditCsvFields(normalizeAudit(r))`; file `roles-<YYYY-MM-DD>.csv`; disabled while loading or empty), and **Add Role** (navigates to `/backstage/roles/new`, wrapped in `<Can permission="backstage_role.create">`).

Below the header sits a **`RolesAccessSummary`** strip (`roleManagement/RolesAccessSummary.tsx`), fetched from a dedicated `GET /api-system/backstage/roles/summary` endpoint (`roleService.getAccessSummary()` — fleet-wide, ignores the table's search/filters, keeps its last-known numbers and dims itself on a failed refresh rather than blanking). It shows the total role count with active/inactive/**deleted** breakdown (the soft-deleted count is new on the wire since the last sync and was not rendered before) plus up to three roles with the broadest permission grant. **Since 2026-09-02 (`carmen-backstage` PR #252), the "broadest roles" bars are scaled against the permission catalog's size, not the widest of the three roles shown** — a role that holds every catalog permission gets a warning-coloured bar and an alert icon (matching the `RoleIdentityHero`'s own "Full access" wording), and the section header states "of `N`" once the catalog size is known; without it (catalog still loading/failed) the bars are dropped entirely rather than drawn against a meaningless denominator.

Below that sits the standard search-and-filters row: a debounced (400 ms) search input over `name`/`description`, and a **Filters** Sheet with a single Status group (Active / Inactive toggle buttons → `advance` query `{ where: { is_active } }` when exactly one is selected). Active filter chips render below the search row.

`DataTable` columns in order:

| Column | Rendering |
|---|---|
| Name | Clickable link — navigates to `/backstage/roles/:id/edit` — with the role's `description` as muted subtext beneath it (merged into this column; there is no separate Description column) |
| Permissions | **`RoleReachCell`** (`roleManagement/RoleReachCell.tsx`, since 2026-09-02) — `permission_count`/`catalogSize` as a fraction with a proportional bar (bar hidden below `lg` to avoid a near-invisible sliver), a warning icon + amber styling when the role holds the whole catalog, and an optional `resource_count` line beneath ("N resources") when the backend sends it; **sortable since 2026-09-09** (PR #293) by `permission_count`, which `micro-business`'s `backstage_role.service.ts` (`DERIVED_SORT_KEYS = ['permission_count', 'resource_count']`, line 46) orders in memory rather than via a Prisma relation `_count` |
| Status | Active/Inactive badge from `is_active` |
| Created | `AuditMeta` (`variant="cell"`) via the shared `auditColumns()` — relative time (e.g. "5mo ago") on one line, actor name on the next, full timestamp as a hover `title`. Reads `normalizeAudit(row)`, which tries the nested `audit.created` `{ at, name }` shape first and falls back to flat `created_at`/`created_by_name` only when nested is absent |
| Updated | Same `AuditMeta` rendering from `normalizeAudit(row).updated` — **omitted (renders `-`) only when the record has never really been edited** (`everEdited`: an updated actor name is present, or its timestamp differs from `created`'s), not by a plain `updated_at === created_at` comparison |
| Actions | `⋯` dropdown: **Edit** (navigate; `<Can permission="backstage_role.update">`) and **Delete** (opens a destructive `ConfirmDialog`; on confirm calls `DELETE /api-system/backstage/roles/:id`; `<Can permission="backstage_role.delete">`). A `backstage_role.read`-only session sees an empty dropdown, matching every other management list in the SPA |

When the result set is empty the table is replaced by an `EmptyState` card ("No roles yet", with an inline Add Role CTA — itself `<Can permission="backstage_role.create">`-gated — when no search term is active, or a `No roles matching "<term>"` message when one is). Default sort is `created_at:desc`. Persisted UI state:

| `localStorage` key | Stored type | Persists |
|---|---|---|
| `search_roles` | string | Search term |
| `filters_roles` | JSON string array | Status filter selections |
| `page_roles` | number string | Current page |
| `perpage_roles` | number string | Page size |
| `sort_roles` | string | Sort (`column:dir`) |

### 2.2 `RoleEdit` — layout

The page opens with a **`RoleIdentityHero`** card (`roleEdit/RoleIdentityHero.tsx`) — a shield icon, the role name (or "(unnamed role)"), an inline `description` line **shown only in view mode** (moved up from the Settings card, see below), an Active/Inactive badge, a one-line **permission-reach summary**, and — new since the last sync — an **audit-actor line** (`<AuditMeta variant="header">`, "Created … · Updated … by …"). The (view-mode-only) **Edit** button renders inside the hero's action slot, gated `<Can permission="backstage_role.update">`.

The reach summary has two distinct forms depending on mode:
- **View mode (existing role, not editing):** shows the richer text `RoleEdit.tsx` itself computes (`grantSummary`) — "`N` permission(s) · `X` of `Y` resources" plus, when every granted action is `read`, " · read only", or up to three distinct verbs joined by " · " otherwise.
- **Create mode, or while editing:** the hero falls back to its own simpler `permissionSummary()` — "No permissions granted yet", or "`N` permission(s) across `M` resource(s)" — recomputed live as toggles change.
- **Either mode, whenever the role's granted-key count reaches the catalog size:** both forms are overridden by "Full access to every permission" in amber with a warning triangle — the single most audit-worthy state, so it always wins.

Below the hero, the form is a two-column grid **only while editing** (`lg:grid-cols-[1fr_minmax(300px,340px)]`); in view mode it collapses to one column. **Permissions** is the left/wide card in both modes, hosting the `PermissionGrid` (§2.6). **Settings** — `name` (required), `description` (textarea), and an `is_active` checkbox/badge — is the right/narrow sticky rail, but **since 2026-09-02 (`carmen-backstage` PR #253) it renders only while editing**: in view mode there is no separate "Settings" or "Role Details" card at all, because the two facts it used to duplicate (name as an `<h1>`, status as a badge) already sit in the hero, and the one fact it carried alone (description) moved into the hero too. This mirrors the pattern the `users` module went through — a read-mode details card absorbed into the identity hero.

### 2.3 `RoleEdit` — create mode (`/backstage/roles/new`)

Title comes from the hero (empty name shows "(unnamed role)"); the form is immediately editable (`editing = true` from mount) — there is no Edit button in create mode. On submit the SPA calls `POST /api-system/backstage/roles` with `permissions: { add: <all selected keys> }`. On success it redirects to `/backstage/roles/:id/edit` for the created id (falling back to the list when the response carries no id).

### 2.4 `RoleEdit` — view/edit mode (`/backstage/roles/:id/edit`)

**Not-found gating:** a bad or deleted `id` renders a dedicated shell instead of the form — just the back link and a `SearchX`-icon `EmptyState` ("Role not found", "This role doesn't exist, or it may have been deleted…", a "Back to roles" button).

Loads via `GET /api-system/backstage/roles/:id`, which returns `{ id, doc_version, name, description, is_active, permissions }` and **no audit block at all**. `RoleEdit.tsx` compensates with a second, best-effort call to the *list* endpoint filtered to that one `id` (`roleService.getAll({ advance: { where: { id } } })`) and lifts that row's audit fields for the hero's `AuditMeta` line; the role's own record wins if it ever grows an audit block, the list-row fallback is used otherwise, and a failed fallback simply shows no audit line. The page starts **read-only**: the Permissions card shows every catalog action grouped by resource, granted ones highlighted and **withheld ones dimmed rather than omitted** (§2.6) — or, if the catalog itself failed to load, just the role's own granted keys with nothing greyed (the page cannot tell "withheld" from "never learned about" without the catalog); a role with zero granted keys and no catalog to fall back on shows "No permissions granted." instead of an empty card. Clicking **Edit** (in the hero) switches to editable; **Cancel** (in the sticky bottom bar, §2.5) restores the pre-edit snapshot. Unsaved changes trigger the `useUnsavedChanges` navigation guard, and the global shortcuts save (`formRef.requestSubmit`) and cancel (only when `!isNew`).

Saving computes the **permission delta** against the key set captured at fetch time — `add` = selected but not original, `remove` = original but not selected — and sends `PUT /api-system/backstage/roles/:id` with `permissions: { add, remove }` plus `doc_version` when known. A version mismatch triggers the shared `notifyVersionConflict()` toast and re-fetches rather than silently overwriting. After a successful save the page refetches the role and drops back to view mode.

### 2.5 Sticky action bar

Rendered only while `editing = true`, mirroring the pattern used across clusters/business-units/users/applications/report-templates: a `fixed bottom-0` bar with an unsaved-changes indicator (pulsing amber dot + "Unsaved changes", or "No changes" in muted text) on the left, and **Cancel** (hidden in create mode; disabled while saving) + **Create Role**/**Save Changes** (disabled while saving, or in edit mode when there are no changes) on the right.

### 2.6 `PermissionGrid` (replaced the accordion `PermissionPicker` on 2026-08-20, `carmen-backstage` commit `42eeafe`)

`roleEdit/PermissionGrid.tsx` is the one component both modes share — read and edit render identically except for the affordance, so pressing Edit cannot move anything on screen. Rows are one per `resource`, ordered by `resourceRank()` (`backstageNav.ts`'s nav-derived order — see [Permissions](/en/backstage/rbac/permissions)); within a row, actions are ordered by `actionRank()` (`utils/permissionOrder.ts`: `['read', 'create', 'update', 'delete', 'manage']`, unlisted verbs sort last in catalog order) rather than the catalog's own alphabetical order, which would otherwise put `create`/`delete` ahead of `read`.

**Every catalog action is shown, granted or not** — the accordion this replaced only rendered granted keys, so a role's withheld access was invisible. In **edit mode**, each action is a toggle `<button aria-pressed>` (not a checkbox): filled/tinted when granted, dashed-outline and muted when withheld, with the action's `description` as a hover tooltip; a small text link at the end of each resource's row reads **"All"** (grant every remaining action in that resource) or **"None"** (clear every granted action in that resource), toggling with the row's own current state. In **read mode**, the same actions render as `Badge`s — solid for granted, dashed-outline for withheld — and a resource with zero grants recedes further with a muted resource-name label. A short legend line ("Dashed actions are in the catalog but not granted to this role.") appears under the grid, but only in read mode with the full catalog loaded, and only when at least one resource has fewer granted actions than its total (including a resource with none granted at all) — it never appears while editing (a dashed action is a button you can press, which explains itself).

**Reworked 2026-09-29 as an "access review" (`carmen-backstage` `463d3cc6` … `2369e4b0`).** The grid is now carved into the sidebar's own sections (`groupGrantRows()` in `roleEdit/grantGroups.ts`): each section heading shows `held/total` resources (hidden when the grid was rebuilt from the role's own keys because the catalog request failed — `complete={false}`, because a section that only knows the resources the role holds would always read as full, for example `4/4`; `PermissionGrid.tsx:39-46`), and in edit mode each section also gets its own grant-all/none button next to the per-resource one. Each resource row shows the menu's icon and name above the exact `resource` key, followed by a short description taken from the catalog payload (`resource_description` / `resource_description_th` on `GET /api-system/backstage/permissions`, Thai falling back to English; the backend builds these from the in-code `BACKSTAGE_PERMISSION_RESOURCE_SEED` constant, not from a database column — `backstage_permission.service.ts:46-57`). A resource with no menu entry gets a name from `UNMENUED_RESOURCE_META` instead of a bare key: `activity_log` is "Record History" and `license` is "License Enforcement" (`grantGroups.ts`). In edit mode a chip whose state differs from the saved grant carries a small dot (green = added, red = removed).

**Escalation marking.** Granted chips for `backstage_role.create`, `backstage_role.update` and `user_backstage.manage` render amber instead of the normal tint (`ESCALATION_KEYS`, `src/utils/permissionRisk.ts`) because each lets its holder raise their own access; the role hero adds a "Can grant itself more access:" warning listing them unless the role is full-access. The list is the frontend's own reading of the catalog — the backend does not report it — so a future key with the same power has to be added there by hand.

**Access-shape strip.** `RoleIdentityHero` draws the role's reach as `AccessShapeStrip` (`roleEdit/AccessShapeStrip.tsx`): one tick per catalog resource in menu order, grouped by section — muted when nothing is held, half-tint when partial, solid when every action is held, amber when an escalation key is held. It is rendered only from a complete catalog (`RoleEdit.tsx:495-497`), since otherwise an empty tick could not distinguish "not held" from "never learned about".

## 3. Permission Catalog

`PermissionCatalog` (`/backstage/category-permissions` — moved from `/backstage/permissions` on 2026-08-20) is a read-only reference of every key in the catalog, loaded once via `GET /api-system/backstage/permissions`. Header: a back link to `/backstage/roles`, title "Permission Catalog", subtitle "Read-only reference of all platform permissions". **The route itself carries no permission requirement** — `App.tsx` wraps it in a bare `<PrivateRoute>` — but the data fetch it makes is enforced server-side on `backstage_role.read`; a session lacking that key sees the page shell, an error toast, and an empty grid, not a client-side "access denied."

Content is a responsive card grid (2 columns at `sm`, 3 at `lg`), one card per resource preserving catalog order. Each card lists its permissions as a monospace outline badge with the full `resource.action` key, the `description` in muted text beneath when present, and — new since the last sync — a compact audit line (`AuditMeta variant="compact"`, via `latestActor()`) showing who last touched that catalog row. In practice this line renders nothing for almost every key: `tb_backstage_permission` is backend seed data with `created_by_id` null throughout, so `PermissionCatalogItem`'s audit fields are populated only if the backend ever starts attributing catalog edits to an actor. There are no buttons, no search, no filters, and no mutation affordances of any kind — the catalog is backend-owned data. An empty catalog renders an `EmptyState` ("No permissions"). The screen has **no sidebar entry**; the only navigation paths in are the Roles header button and the URL itself.

## 4. Super Admins (summary-level — see the scope note in §1)

`SuperAdminManagement` (`/backstage/super-admins`) was rewritten a **second time** since this module's last full sync, on 2026-09-02 (`#244`, "make this page a people registry, not a data table"). It is no longer the `DataTable`-based screen the last sync described: it is now a card-based **roster** —

- **Header:** title "Super Admins", a dynamic subtitle stating the standing headcount ("N super admins") rather than a fixed description, and two actions — **Export** (client-side CSV, now including audit columns: User, Email, User ID, Status, Created At/By, Updated At/By) and **Add Super Admin**, opening a modal `Dialog`.
- **Add Super Admin dialog:** a server-side typeahead **`UserPicker`** component (not a preloaded `Select` of 200 users) searching every user by name/email as you type, excluding users who already hold the flag. Confirming calls `POST /api-system/backstage/super-admins` with `{ user_id }`.
- **Roster:** a plain `<ul>` of rows (avatar-initials, name, Active/Inactive badge, email, `user_id`, and a compact "granted … by …" audit line per row) — not a `DataTable`. A search box appears only once the roster exceeds 8 rows. Each row's Remove button is a plain destructive `<Button>` (not a dropdown item); **on your own row it is replaced entirely by explanatory text** ("cannot remove yourself") rather than a disabled control, since this screen is reachable only by super admins and a live self-Remove button next to your own name risks locking yourself (and possibly everyone) out.

The list response still nests multi-layer `{ data }` envelopes descended by a local `extractArray` helper. Persisted UI state is just the search term (`search_super_admins`).

## 5. Backstage Users (summary-level — see the scope note in §1)

Both screens were substantially redesigned since the last full sync (`#250`/`#251`, 2026-09-02, "make this a privilege registry, not a role-edit form").

**`UserBackstageManagement`** (`/backstage/user-backstage`) list: still no Add button (users are created in the [users](/en/backstage/users) module). Its summary strip (`BackstageAccessSummary`) is now sourced from a **filter-consistent `summary` block on the list response itself** rather than an N+1 per-row `userRoleService.list()` sweep of every user — the list's own **Roles** column composes each row's assignments inline (`RoleChips`) instead of a bare count badge, and a **Granted** column shows the most recent grant's relative age with its actor. Filters expanded beyond Status to include Role and Scope (Platform-wide / specific cluster). Export is now per-**assignment**, not per-user (one CSV row per role grant, so a user with three roles produces three rows), and rows carry a "Revoke all access" destructive action (`<Can permission="user_backstage.manage">`) beside "Manage roles" in the row menu.

**`UserBackstageEdit`** (`/backstage/user-backstage/:userId`) detail: gained an **Access Reach Band** (platform-wide vs. per-cluster reach summary), an inactive-account warning banner when a deactivated user still holds role assignments, an "Email Unverified" badge (`!!userRecord?.email_verified_at` — the `tb_user` email-verification column noted on the [module landing](/en/backstage/rbac)), and a **Membership Card** listing the user's cluster/BU memberships for context. Per-assignment "granted by" attribution is still a workaround: the per-user roles endpoint returns no actor, so the page separately queries the registry list endpoint by search term and matches rows back by `user_id`, falling back to an explicit "provenance unavailable" state on failure rather than guessing. The Roles & Scope card, its `<Can permission="user_backstage.manage">` gate, and the add-role/remove flow are structurally the same as before, though the add-role UI moved from an inline form to a Sheet (`AddRoleSheet`).

Given the depth of this redesign, a full section-by-section rewrite of §4/§5 (columns, exact copy, persisted `localStorage` keys, every component) is left to the standalone [Backstage Users](/en/backstage/user-backstage) and [Super Admins](/en/backstage/super-admins) modules, which now document each screen at that depth.

## 6. References

- `../carmen-backstage/src/App.tsx` — route registrations for the four Roles/Permission-Catalog routes (lines 450–480, incl. `/backstage/category-permissions`'s bare `<PrivateRoute>`); Backstage Users and Super Admins routes are elsewhere in the same file.
- `../carmen-backstage/src/pages/RoleManagement.tsx` — list columns (name+description merged, `RoleReachCell`), `backstage_role.*` gates, CSV export incl. audit columns, persisted keys.
- `../carmen-backstage/src/pages/roleManagement/RolesAccessSummary.tsx`, `.../RoleReachCell.tsx` — the catalog-anchored reach summary strip and list-cell bar (2026-09-02).
- `../carmen-backstage/src/pages/RoleEdit.tsx` — hero + `PermissionGrid` layout (Settings rail edit-mode-only), not-found gating, `doc_version`, the list-endpoint audit fallback (`fetchAudit`), permission delta computation (`handleSubmit`).
- `../carmen-backstage/src/pages/roleEdit/RoleIdentityHero.tsx` — the hero card, `permissionSummary()` reach text, and the audit-actor line.
- `../carmen-backstage/src/pages/roleEdit/PermissionGrid.tsx` — the resource-row grant grid (replaced `PermissionPicker` on 2026-08-20, `42eeafe`; the old accordion component no longer exists).
- `../carmen-backstage/src/utils/permissionOrder.ts` — `ACTION_ORDER`/`actionRank()`.
- `../carmen-backstage/src/components/nav/backstageNav.ts` — `resourceRank()`/`NAV_RESOURCE_ORDER`, consumed by `RoleEdit.tsx`.
- `../carmen-backstage/src/pages/PermissionCatalog.tsx` — read-only resource card grid, per-item audit line.
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage-permissions/backstage-permissions.controller.ts` — `backstage_role.read` enforcement on the catalog endpoint.
- `../carmen-backstage/src/pages/SuperAdminManagement.tsx` — the roster-list rewrite (2026-09-02, `#244`), `extractArray` envelope descent, self-removal guard, `UserPicker` typeahead.
- `../carmen-backstage/src/components/UserPicker.tsx` — server-side user typeahead used by Super Admins' Add dialog.
- `../carmen-backstage/src/pages/UserBackstageManagement.tsx`, `.../UserBackstageEdit.tsx` — the privilege-registry redesign (2026-09-02, `#250`/`#251`); not verified line-by-line here (see §1 scope note).
- `../carmen-backstage/src/components/Can.tsx` — the permission-gated render wrapper.
- `../carmen-backstage/src/pages/Forbidden.tsx` — the 403 page rendered on a failed route guard (see [Permissions](/en/backstage/rbac/permissions)).

**Cross-links:** [Backstage Roles landing](/en/backstage/rbac) &nbsp;·&nbsp; [Data Model](/en/backstage/rbac/data-model) &nbsp;·&nbsp; [Permissions](/en/backstage/rbac/permissions)
