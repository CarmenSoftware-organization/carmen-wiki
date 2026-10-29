---
title: Backstage RBAC
description: Permission-based access control for the Backstage SPA — permission catalog, roles, scoped user assignments, and the super-admin bypass.
published: true
date: 2026-10-29T05:00:00.000Z
tags: backstage/rbac, carmen-software
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Backstage RBAC

The **Backstage RBAC** module is the access-control system of the Carmen Blue Backstage admin SPA. It replaces the legacy single-value role enum with a permission-based model: a backend-owned **permission catalog** defines `resource.action` keys, **roles** bundle those keys, **assignments** bind a role to a user at platform-wide or per-cluster scope, and a separate **super-admin flag** bypasses every check. Every route guard, sidebar entry, and in-page action gate in the SPA resolves against this system.

> **Permission key, feature key, superAdminOnly** (`src/components/nav/backstageNav.ts`): the **Backstage Roles** nav row (labelled "Backstage Roles", not "Roles") carries `permission: 'backstage_role.read'`, `feature: 'backstage_roles'`, no `superAdminOnly`. Permission Catalog has **no nav row at all** — see §1.

> **At a Glance**
> **Module purpose:** Permission-based access control — catalog defines `resource.action` keys, roles bundle keys, scoped assignments bind roles to users, super-admin flag bypasses all checks &nbsp;·&nbsp; **Audience:** Developers and QA working on the Backstage SPA and its authorization backend &nbsp;·&nbsp; **Key entities/tables:** `tb_backstage_permission`, `tb_backstage_role`, `tb_backstage_role_tb_permission`, `tb_user_tb_backstage_role` (scope via nullable `cluster_id`), `tb_backstage_super_admin` — all five carry `doc_version` (2026-07-16 platform-wide optimistic-lock rollout) &nbsp;·&nbsp; **Screens documented here:** Roles · Permission Catalog &nbsp;·&nbsp; **Screens summarized here, full module elsewhere:** [Super Admins](/en/backstage/super-admins) · [Backstage Users](/en/backstage/user-backstage) (see scope note below) &nbsp;·&nbsp; **Sub-pages:** 3 &nbsp;·&nbsp; **Permission keys renamed 2026-08-20:** `role.*` → `platform_role.*` (→ `backstage_role.*` on 2026-10-26, `318949a3`) everywhere, the standalone `rbac.read` key some earlier screens used was retired, and Permission Catalog's route moved from `/backstage/permissions` to `/backstage/category-permissions` (`carmen-backstage` commit `8df0b10`) &nbsp;·&nbsp; **Since 2026-09-02:** `RoleManagement`/`RoleEdit` measure a role's permission count against the **catalog size**, not the widest role, and `RoleEdit`'s permission picker became a per-resource-row grid with toggle buttons that also shows withheld actions (`carmen-backstage` PR #252/#253); `SuperAdminManagement` was rewritten a second time, from a `DataTable` into a people-roster list with a self-removal guard (`carmen-backstage` PR #244)

![Backstage RBAC screen](/screenshots/platform/rbac/index.png)

**Scope note (2026-09-05 resync):** this page documents the **Roles** screens and **Permission Catalog** in full. **Backstage Users** and **Super Admins** are covered here at a summary level only — both now have their own standalone Platform modules, [Backstage Users](/en/backstage/user-backstage) and [Super Admins](/en/backstage/super-admins), each with the independent nav row, permission key, and e2e suite noted below and each carrying the full line-by-line verification of its own screen. Facts stated below about them were confirmed against current source, but for the exhaustive treatment — screens, columns, endpoints — see their own module pages, not this one.

## 1. Overview

The SPA still groups four screens under this access-control system in its **Platform** sidebar group. This page documents two of them — **Roles** and **Permission Catalog** — in full, forming one pipeline from key definition to enforced access. **Super Admins** and **Backstage Users** are summarized below and on [UI Screens](/en/backstage/rbac/ui-screens) only: both now have their own standalone Platform modules — [Super Admins](/en/backstage/super-admins) and [Backstage Users](/en/backstage/user-backstage) (see the scope note above) — so their full treatment — screens, columns, endpoints — belongs there, not here.

Documented here in full:

- **Permission Catalog (`/backstage/category-permissions` → `PermissionCatalog`)** — read-only reference of every permission key the backend defines, grouped by resource. **There is no nav row and no SPA route permission gate at all** — `App.tsx` wraps the route in a bare `<PrivateRoute>` with no `requiredPermission`/`feature` prop, so any authenticated platform user who knows or is given the URL can open it. Do not read that as "unprotected data," though: the page's own data fetch (`GET /api-system/backstage/permissions`) is enforced server-side on `backstage_role.read` (`RequireBackstagePermission('backstage_role.read')`, `backstage-permissions.controller.ts`) — a session lacking that key reaches the page shell but the catalog call 403s (the SPA shows a toast and an empty grid, not the permission list). The route moved here from `/backstage/permissions` on 2026-08-20 (`carmen-backstage` commit `8df0b10`); the page is reached from a header button on the Roles list. The SPA cannot create or edit catalog entries.
- **Roles (`/backstage/roles` → `RoleManagement`, `/backstage/roles/new` and `/backstage/roles/:id/edit` → `RoleEdit`)** — standard list + create/view/edit pattern. A role is a named, activatable bundle of permission keys picked from the catalog. The picker used to be an accordion checklist; since 2026-08-20 it is a per-resource-row grid with toggle buttons — see [UI Screens](/en/backstage/rbac/ui-screens).

Summarized here only — see the scope note above for why, and their own module pages for the full treatment:

- **Backstage Users (`/backstage/user-backstage` → `UserBackstageManagement`, `/backstage/user-backstage/:userId` → `UserBackstageEdit`)** — assigns roles to users. Each assignment carries a scope: platform-wide or a specific cluster. The detail page's "Roles & Scope" card is where assignments are added and removed. Redesigned again since the last sync into a "privilege registry" framing (`#250`/`#251`, `carmen-backstage`).
- **Super Admins (`/backstage/super-admins` → `SuperAdminManagement`)** — an add/remove roster of users who bypass every permission check. Membership here is a flag, not a role. Rewritten twice since the module's original 2026-06-10 sync: first into a searchable `DataTable`, then again on 2026-09-02 (`#244`, `carmen-backstage`) into a card-based people roster (avatar, name/status/email/id, a compact "granted … by …" audit line, and a self-removal guard that replaces the Remove button with explanatory text on your own row).

At login the SPA fetches the user's **effective permissions** (`GET /api/user/permission/backstage`) — the flattened result of all their assignments — and every guard in the app evaluates against that snapshot. A second, independent login path also exists for a **cluster-admin-only** session (§2, §5) — see [Permissions](/en/backstage/rbac/permissions) §4 for exactly how it composes with the bootstrap exception.

**Renamed twice.** On 2026-08-20 (`8df0b10`, "เปลี่ยนคีย์เป็น platform_role.*, เลิกใช้ rbac.read, ย้าย route เป็น category-permissions") every Roles permission key changed from `role.*` to `platform_role.*`; on 2026-10-26 the Carmen Blue Backstage rename (`carmen-backstage` `318949a3`, backend `e0eaeff61`) changed them again to `backstage_role.*` (`backstage_role.read`/`.create`/`.update`/`.delete`) — and renamed `user_platform.*` to `user_backstage.*` and `platform_config.*` to `backstage_config.*` the same way. The backend migration `20261026120000_rename_platform_values_to_backstage` rewrote the stored `resource` values in place, an interim `rbac.read` key some earlier builds used was retired, and the Permission Catalog route moved to `/backstage/category-permissions`. **Any page, test, or ticket referencing `role.read`/`role.create`/`role.update`/`role.delete`/`rbac.read`/`platform_role.*`/`/backstage/permissions` describes a state that no longer exists.** The same rename moved the whole console from `/platform/*` to `/backstage/*` (and the segment `user-platform` to `user-backstage`); old bookmarks keep working because `App.tsx:654` mounts `LegacyPlatformRedirect` on `/platform/*`, which rewrites the prefix and preserves query and hash (`App.tsx:677-681`). The seeded role `Platform Admin` is now `Backstage Admin`, and the effective-permissions payload field `platform` is now `backstage` (`GET /api/user/permission/backstage`).

**Since 2026-09-02, both Roles screens changed further** (`carmen-backstage` design PRs #252/#253, same day): `RoleManagement`'s list and its new `RolesAccessSummary` strip now measure a role's `permission_count` **against the size of the permission catalog**, not against the widest of the three summarized roles — the summary strip also surfaces a `deleted` (soft-deleted-roles) count that was on the wire but never rendered before, and the list's own Permissions column gained the same catalog-anchored bar. `RoleEdit`'s Settings card (name/description/active toggle) now renders **only while editing** — in view mode, the role's name/description/status and a new audit-actor line moved up into the `RoleIdentityHero`, so there is no longer a separate details card to read (the same "hero absorbs the read-mode card" pattern the `users` module went through). The Permissions card now uses a `PermissionGrid`: every catalog action is shown per resource row, toggle buttons in edit mode, and — new — **withheld (not-granted) actions are shown dimmed rather than omitted**, so a role's shape is visible even where it holds nothing. Full detail on [UI Screens](/en/backstage/rbac/ui-screens).

## 2. Business Context

The legacy model gave each user exactly one role-enum value, and every guard hardcoded which enum values passed (see §5 for the full mapping). That model could not answer the questions the platform actually has:

- **Per-cluster scoping.** Carmen Blue support engineers are often responsible for one customer cluster, not all of them. An assignment row with `scope = { type: 'cluster', cluster_id }` grants a role's keys inside that cluster only — something a global enum value cannot express.
- **Parity with Applications.** The Applications module already grants machine clients fine-grained `api_name` keys (e.g. `cluster.create`). Human access now uses the same `resource.action` key shape, so a developer can reason about one permission vocabulary across both human and machine callers.
- **Composable duties.** "Can manage report templates but only read clusters" required a new enum value per combination before; now it is just a role with the right key set.
- **Bootstrap.** A fresh installation has no catalog-driven roles assigned to anyone. The login gate therefore carries a first-admin escape hatch: when the platform has 0 or 1 users in total, login skips the must-have-at-least-one-permission check so the first administrator can sign in and build roles (see §3). A second, unrelated login exception admits a **cluster-admin-only** session (a user whose only authority is a `tb_cluster_user` admin membership, no platform permission at all) — added after the cluster-admin persona shipped; see [Permissions](/en/backstage/rbac/permissions) §4.
- **Menu-derived ordering.** A role's permission grid and the read-only grant view both list resources in the same order the sidebar itself uses (`NAV_RESOURCE_ORDER`/`resourceRank()` in `backstageNav.ts`, derived from each nav item's `permission` prefix, first appearance wins). **`backstageNav.ts`'s own comment names `rbac` and `license` as the resources with no menu row of their own — that comment is stale.** `platform_role` (this module's own resource, renamed from `role`/`rbac` on 2026-08-20) now has its own **Backstage Roles** nav row, so it ranks normally, not in the unranked tail. Grepping every `permission="resource.action"` / `requiredPermission` / `hasPermission()` call site against the nav's own permission list, the two resources genuinely left with no menu row of their own today are **`activity_log`** (the cross-cutting "View History" gate used on Clusters/Business Units/Users, not this module) and **`license`** (an in-page `license.manage` key inside the Licenses module, distinct from the nav's own `subscription.*` keys) — both sort after every menu-backed resource, in catalog order among themselves. This is why, say, `cluster` permissions always appear before `news` permissions in the picker — it mirrors the sidebar the reader just came from, not an alphabetical or database order.
- **Auditability.** All five RBAC tables carry the platform-standard audit trio and soft-delete-aware unique constraints, so every grant, role change, and assignment is traceable to an actor and reversible without key collisions — the old enum column changed silently in place. One gap: `GET /api-system/backstage/roles/:id` (the role-detail endpoint `RoleEdit` loads from) returns **no audit block at all** — the SPA falls back to the audit fields on that role's row in the *list* endpoint (matched by `id`, best-effort) so the identity hero can still show a "created/updated" line.

## 3. Key Concepts

- **Permission key** — the string `resource.action`. The catalog stores `resource` and `action` as separate columns; the key is derived. Keys are defined by the backend — the SPA only reads them. Representative keys:

| Example key | What it opens |
|---|---|
| `backstage_role.read` | Roles list and role detail view. **Not** the Permission Catalog — that route carries no permission key at all (see §1), though the catalog *data fetch* itself is backend-enforced on this same key |
| `backstage_role.create` / `backstage_role.update` / `backstage_role.delete` | Role create / edit / delete actions (renamed from `role.*` on 2026-08-20, `8df0b10`) |
| `user_backstage.read` | Backstage Users list and detail (read-only) |
| `user_backstage.manage` | Add/remove role assignments on the detail page (in-page `<Can>` gate) |
| `cluster.read` | Clusters list — and the Business Units list, via key reuse (see §6) |
| `broadcast.send` | The single Send Broadcast route — an example of a non-CRUD action segment |

- **Role** — a named bundle of permission keys with `is_active` and a description. Role writes are **deltas**: the SPA sends `permissions: { add: string[], remove?: string[] }`, computed against the key set loaded at fetch time, never the full desired set.
- **Assignment and Scope** — a `tb_user_tb_backstage_role` row binding user + role + scope. In the SPA, `Scope` is the union `{ type: 'backstage' } | { type: 'cluster', cluster_id }`; in Prisma it is a single nullable `cluster_id` column (`null` = platform-wide).
- **EffectivePermissions** — `{ platform: string[], clusters: Record<clusterId, string[]>, is_super_admin?: boolean }`, fetched after login and on every `AuthProvider` mount via `GET /api/user/permission/backstage`, cached in `localStorage` under `effectivePermissions`.
- **`checkPermission` order** (`src/utils/permissions.ts`) — super-admin bypass first; then the `platform` array (a platform-scoped grant applies everywhere); then, with a `clusterId`, only that cluster's array; without one, any cluster's array (the broad "show this nav/page" check). Unchanged since the last sync — verified against current source line-for-line.
- **Bootstrap exception** — when the total user count is 0 or 1, `login()` skips the must-have-≥1-permission gate and `hasPermission()` returns `true` unconditionally. Dormant once a second user exists.
- **Super-admin flag ≠ role** — `tb_backstage_super_admin` is a per-user flag table, not a role in `tb_backstage_role`. It surfaces as `is_super_admin` in the effective-permissions payload and short-circuits every check before any key is consulted.

## 4. Roles and Personas

Access to the four RBAC screens is itself permission-gated. Route guards use `requiredPermission` (or `requireSuperAdmin`) on `PrivateRoute`; the Roles screens and the Backstage Users detail page additionally gate in-page actions with `<Can>` (Permission Catalog, Super Admins, and the Backstage Users list have no in-page gate — their route guard is the only barrier):

| Screen | Route(s) | Route guard | In-page gates |
|---|---|---|---|
| Roles list | `/backstage/roles` | `backstage_role.read` (`feature="backstage_roles"`) | Add is `<Can permission="backstage_role.create">`; row Edit is `<Can permission="backstage_role.update">`; row Delete is `<Can permission="backstage_role.delete">`. Export remains ungated |
| Role create | `/backstage/roles/new` | `backstage_role.create` (`feature="backstage_roles"`) | None |
| Role edit | `/backstage/roles/:id/edit` | `backstage_role.update` (`feature="backstage_roles"`) | The header **Edit** button is `<Can permission="backstage_role.update">` |
| Permission Catalog | `/backstage/category-permissions` | **None at the route** — `<PrivateRoute>` with no `requiredPermission`/`feature`; any authenticated platform user can open it. The page's own `GET .../permissions` call is enforced server-side on `backstage_role.read` (a session lacking it gets a 403 toast and an empty grid) | None (read-only screen) |
| Super Admins | `/backstage/super-admins` | `requireSuperAdmin` (`feature="super_admins"`) | None — only super admins ever reach the page |
| Backstage Users list | `/backstage/user-backstage` | `user_backstage.read` (`feature="user_backstage"`) | None |
| Backstage Users detail | `/backstage/user-backstage/:userId` | `user_backstage.read` | `<Can permission="user_backstage.manage">` wraps the Add Role button, the add-role form, and each per-row Remove button |

The sidebar array lives in `src/components/nav/backstageNav.ts` (`ALL_BACKSTAGE_NAV_ITEMS`, filtered by `buildBackstageNav()`) — `Layout.tsx` only calls that function, it no longer defines the nav items itself:

| Sidebar entry | Filter condition |
|---|---|
| Backstage Roles (labelled "Backstage Roles", not "Roles") | `permission: 'backstage_role.read'`, `feature: 'backstage_roles'` |
| Super Admins | `superAdminOnly: true`, `feature: 'super_admins'` |
| Backstage Users | `permission: 'user_backstage.read'`, `feature: 'user_backstage'` |
| Permission Catalog | — no sidebar entry; reached from the Roles header button |

A failed route guard renders the `Forbidden` page (`src/pages/Forbidden.tsx` — renamed from an inline `AccessDenied` component previously defined inside `PrivateRoute.tsx`) **in place**, leaving the URL untouched, inside the normal `<Layout>` shell — the sidebar stays visible, the session stays valid, and two actions are offered: "Go Back" (context-aware, falls back to `/dashboard` if there's no sensible back target) and "Go to Dashboard". A direct `/403` route renders the same page. `/dashboard` and `/profile` remain authenticated-only — any signed-in user reaches them regardless of permissions. The full per-route key map for the rest of the SPA lives in [Permissions](/en/backstage/rbac/permissions).

## 5. Migration from the legacy role model

Until 2026-06-10 the SPA gated access by a single `platform_role` enum on the user row (`platform_admin`, `support_manager`, `support_staff`, etc.) and `allowedRoles` arrays on each route. That model is fully removed — from the frontend in commit `6091ffc` ("remove legacy platform_role from frontend") and from the login gate in commit `5f629f2` ("permission-based login gate — drop platform_role/ALLOWED_ROLES from login"), both in the `carmen-backstage` repo. The `enum_platform_role` enum and the `tb_user.platform_role` column are likewise gone from the backend Prisma platform schema.

| Legacy (removed) | Replacement | Notes |
|---|---|---|
| `tb_user.platform_role` enum (one value per user) | Catalog + roles + scoped assignments (`tb_backstage_permission` / `tb_backstage_role` / `tb_user_tb_backstage_role`) | A user can now hold many roles, each platform-wide or per-cluster |
| `allowedRoles={[...]}` prop on `PrivateRoute` | `requiredPermission="resource.action"` (or `requireSuperAdmin`) | One key per route instead of a duplicated role array |
| `AuthContext.hasRole(roles[])` | `AuthContext.hasPermission(key, { clusterId? })` → `checkPermission` | Same bootstrap escape hatch carried over |
| Login-time `ALLOWED_ROLES` role-name allow-list | Must-hold-≥1-permission gate (super-admin, any platform key, or any cluster key) | Commit `5f629f2`; bootstrap exception applies to this gate too |
| Sidebar `roles: [...]` filter in `Layout.tsx` | Sidebar `permission:` / `superAdminOnly:` filter | Same hide-don't-disable behaviour |
| `super_admin` enum value | `tb_backstage_super_admin` flag table → `is_super_admin` bypass | A flag with real bypass semantics, unlike the old enum value which carried no extra routes |
| AccessDenied message quoting the failing role name | Generic "You don't have permission to access this page." | The SPA no longer has a single role value to display |

This module supersedes the legacy Authentication & Roles page (removed from this wiki); anything written against the old model (role names such as `support_manager`/`support_staff`, `allowedRoles` tables) describes behaviour that no longer exists in the SPA.

## 6. Related Modules

- [users](/en/backstage/users) — owns the `tb_user` identity rows that assignments and the super-admin flag point at. User creation/lifecycle stays in the Users module; the Backstage Users screen only manages role assignments. **Cross-module note:** `tb_user` picked up three email-verification columns (`email_verified_at` and two siblings, migration `20260804000000_user_email_verification`) that no page in this module's own screens reads — the only SPA surface is an "Email Unverified" badge on `UserBackstageEdit.tsx` (`!!userRecord?.email_verified_at`, line 198). Documented on [users/data-model](/en/backstage/users/data-model) since the column lives on `tb_user`; noted here because the only UI consumer is a screen this module currently documents.
- [applications](/en/backstage/applications) — the machine-client counterpart: grants `api_name` keys (same `resource.action` shape) to API clients. Useful contrast when reasoning about whether a caller is gated by RBAC (human session) or application grants (machine token).
- [clusters](/en/backstage/clusters) — cluster-scoped assignments reference `tb_cluster` ids; the add-role form's cluster dropdown is fed by the cluster list. Cluster screens are guarded by `cluster.read/create/update`.
- [business-units](/en/backstage/business-units) — **gotcha:** the `/business-units`, `/business-units/new`, and `/business-units/:id/edit` routes reuse the `cluster.read` / `cluster.create` / `cluster.update` keys. There are no `business_unit.*` keys — granting cluster access also grants Business Units, and you cannot grant one without the other.
- **Backstage Migrations' "Role permissions" seed op is a different system — do not confuse it with this module.** The seed console at `/backstage/migrations` lists a `seed-role-permission` operation ("Role permissions: Bindings between app roles and permissions") that **`carmen-backstage` PR #281** (2026-09-04, commit `157a65e` in the `carmen-backstage` repo — a *different* PR #281 exists in `carmen-turborepo-backend`; do not confuse the two) extended to accept **several Business Units at once** (`BuSwitcher`'s new `multiple` mode) instead of one BU per run. That operation seeds the **tenant-level app-role catalog** used inside Carmen Blue itself (`Requestor`/`Approver`-style roles, scoped per Business Unit — `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/seed.role-permission.ts`), which is unrelated to this module's `tb_backstage_role`/`tb_backstage_permission` tables. The seed op that actually populates *this* module's data is the separate, platform-wide `seed-backstage-role-permission` op, which has no BU parameter and was not touched by that PR.

## 7. Pages in This Module

- [Data Model](/en/backstage/rbac/data-model) — the five Prisma tables, soft-delete unique constraints, scope column, and divergences from the SPA TypeScript shapes.
- [UI Screens](/en/backstage/rbac/ui-screens) — Roles list/edit with the resource-row `PermissionGrid`, the read-only Permission Catalog, and (summary-level) the Super Admins roster and the Backstage Users assignment screens.
- [Permissions](/en/backstage/rbac/permissions) — the full route-guard matrix, how route/sidebar/in-page gates compose, the permission-resolution algorithm, and edge cases for testers.
