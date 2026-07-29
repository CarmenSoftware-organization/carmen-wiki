---
title: Platform RBAC
description: Permission-based access control for the Platform admin SPA — permission catalog, roles, scoped user assignments, the super-admin bypass, and the 2026-07 RoleEdit/SuperAdminManagement/UserPlatformManagement redesign.
published: true
date: 2026-07-29T00:00:00.000Z
tags: platform/rbac, carmen-software
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Platform RBAC

The **Platform RBAC** module is the access-control system of the Carmen Platform admin SPA. It replaces the legacy single-value role enum with a permission-based model: a backend-owned **permission catalog** defines `resource.action` keys, **roles** bundle those keys, **assignments** bind a role to a user at platform-wide or per-cluster scope, and a separate **super-admin flag** bypasses every check. Every route guard, sidebar entry, and in-page action gate in the SPA resolves against this system.

> **At a Glance**
> **Module purpose:** Permission-based access control — catalog defines `resource.action` keys, roles bundle keys, scoped assignments bind roles to users, super-admin flag bypasses all checks &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA and its authorization backend &nbsp;·&nbsp; **Key entities/tables:** `tb_platform_permission`, `tb_platform_role`, `tb_platform_role_tb_permission`, `tb_user_tb_platform_role` (scope via nullable `cluster_id`), `tb_platform_super_admin` — all five carry `doc_version` (2026-07-16 platform-wide optimistic-lock rollout) &nbsp;·&nbsp; **Screens:** Roles · Permission Catalog · Super Admins · User Platform &nbsp;·&nbsp; **Sub-pages:** 3 &nbsp;·&nbsp; **Since 2026-07:** `RoleEdit` gained an identity hero + not-found gating + `doc_version` conflict handling; `RoleManagement` gained a Roles Access Summary strip and now gates row Edit/Delete with `<Can>`; `SuperAdminManagement` was rewritten from a two-card layout to a searchable `DataTable` + Add dialog; `UserPlatformManagement` gained a Platform Access Summary strip and an Actions column

## 1. Overview

The module surfaces as four screens in the SPA's **Platform** sidebar group, forming one pipeline from key definition to enforced access:

- **Permission Catalog (`/platform/permissions` → `PermissionCatalog`)** — read-only reference of every permission key the backend defines, grouped by resource. There is no sidebar entry; it is reached from a header button on the Roles list. The SPA cannot create or edit catalog entries.
- **Roles (`/platform/roles` → `RoleManagement`, `/platform/roles/new` and `/platform/roles/:id/edit` → `RoleEdit`)** — standard list + create/view/edit pattern. A role is a named, activatable bundle of permission keys picked from the catalog via an accordion `PermissionPicker`.
- **User Platform (`/platform/user-platform` → `UserPlatformManagement`, `/platform/user-platform/:userId` → `UserPlatformEdit`)** — assigns roles to users. Each assignment carries a scope: platform-wide or a specific cluster. The detail page's "Roles & Scope" card is where assignments are added and removed.
- **Super Admins (`/platform/super-admins` → `SuperAdminManagement`)** — an add/remove list of users who bypass every permission check. Membership here is a flag, not a role. **Rewritten since 2026-06-10:** the former two-card layout (inline native `<select>` + plain divided row list) is now a searchable `DataTable` (User / Status / Added / Actions columns) with a header CSV Export button and a modal Add-Super-Admin dialog (shadcn `Select`, not an inline native one).

At login the SPA fetches the user's **effective permissions** (`GET /api/user/permission/platform`) — the flattened result of all their assignments — and every guard in the app evaluates against that snapshot.

**Since 2026-07, all four screens gained further changes not present in the last sync:** `RoleEdit` now opens with a `RoleIdentityHero` card (name, Active/Inactive badge, a permission-reach summary that flags "Full access to every permission" in amber) above a Permissions-card-left / Settings-card-right form, adds not-found gating for a bad/deleted `id`, and sends `doc_version` on every save with the shared version-conflict toast; `RoleManagement`'s list gained a **Roles Access Summary** strip (total/active/inactive counts plus the three broadest roles by permission count, as horizontal bars) and now gates row **Edit** (`role.update`) and **Delete** (`role.delete`) with `<Can>` — previously both were visible to any `role.read` holder; `UserPlatformManagement` gained a **Platform Access Summary** strip and a row Actions dropdown ("Manage roles"), and its background per-row role-count fetch now distinguishes a failed count (amber warning icon) from a genuine zero rather than collapsing both to `0`. All five RBAC tables (`tb_platform_permission`, `tb_platform_role`, `tb_platform_role_tb_permission`, `tb_user_tb_platform_role`, `tb_platform_super_admin`) picked up `doc_version` in the 2026-07-16 platform-wide rollout. Full detail on [UI Screens](/en/platform/rbac/ui-screens).

## 2. Business Context

The legacy model gave each user exactly one role-enum value, and every guard hardcoded which enum values passed (see §5 for the full mapping). That model could not answer the questions the platform actually has:

- **Per-cluster scoping.** Carmen support engineers are often responsible for one customer cluster, not all of them. An assignment row with `scope = { type: 'cluster', cluster_id }` grants a role's keys inside that cluster only — something a global enum value cannot express.
- **Parity with Applications.** The Applications module already grants machine clients fine-grained `api_name` keys (e.g. `cluster.create`). Human access now uses the same `resource.action` key shape, so a developer can reason about one permission vocabulary across both human and machine callers.
- **Composable duties.** "Can manage report templates but only read clusters" required a new enum value per combination before; now it is just a role with the right key set.
- **Bootstrap.** A fresh installation has no catalog-driven roles assigned to anyone. The login gate therefore carries a first-admin escape hatch: when the platform has 0 or 1 users in total, login skips the must-have-at-least-one-permission check so the first administrator can sign in and build roles (see §3).
- **Auditability.** All five RBAC tables carry the platform-standard audit trio and soft-delete-aware unique constraints, so every grant, role change, and assignment is traceable to an actor and reversible without key collisions — the old enum column changed silently in place.

## 3. Key Concepts

- **Permission key** — the string `resource.action`. The catalog stores `resource` and `action` as separate columns; the key is derived. Keys are defined by the backend — the SPA only reads them. Representative keys:

| Example key | What it opens |
|---|---|
| `role.read` | Roles list, role detail view, and the Permission Catalog |
| `role.create` / `role.update` | Role create / edit routes |
| `user_platform.read` | User Platform list and detail (read-only) |
| `user_platform.manage` | Add/remove role assignments on the detail page (in-page `<Can>` gate) |
| `cluster.read` | Clusters list — and the Business Units list, via key reuse (see §6) |
| `broadcast.send` | The single Send Broadcast route — an example of a non-CRUD action segment |

- **Role** — a named bundle of permission keys with `is_active` and a description. Role writes are **deltas**: the SPA sends `permissions: { add: string[], remove?: string[] }`, computed against the key set loaded at fetch time, never the full desired set.
- **Assignment and Scope** — a `tb_user_tb_platform_role` row binding user + role + scope. In the SPA, `Scope` is the union `{ type: 'platform' } | { type: 'cluster', cluster_id }`; in Prisma it is a single nullable `cluster_id` column (`null` = platform-wide).
- **EffectivePermissions** — `{ platform: string[], clusters: Record<clusterId, string[]>, is_super_admin?: boolean }`, fetched after login and on every `AuthProvider` mount via `GET /api/user/permission/platform`, cached in `localStorage` under `effectivePermissions`.
- **`checkPermission` order** (`src/utils/permissions.ts`) — super-admin bypass first; then the `platform` array (a platform-scoped grant applies everywhere); then, with a `clusterId`, only that cluster's array; without one, any cluster's array (the broad "show this nav/page" check).
- **Bootstrap exception** — when the total user count is 0 or 1, `login()` skips the must-have-≥1-permission gate and `hasPermission()` returns `true` unconditionally. Dormant once a second user exists.
- **Super-admin flag ≠ role** — `tb_platform_super_admin` is a per-user flag table, not a role in `tb_platform_role`. It surfaces as `is_super_admin` in the effective-permissions payload and short-circuits every check before any key is consulted.

## 4. Roles and Personas

Access to the four RBAC screens is itself permission-gated. Route guards use `requiredPermission` (or `requireSuperAdmin`) on `PrivateRoute`; one screen additionally gates in-page actions with `<Can>`:

| Screen | Route(s) | Route guard | In-page gates |
|---|---|---|---|
| Roles list | `/platform/roles` | `role.read` | **Corrected — no longer "None":** Add is `<Can permission="role.create">`; row Edit is `<Can permission="role.update">`; row Delete is `<Can permission="role.delete">` (all three added since the last sync). Export remains ungated |
| Role create | `/platform/roles/new` | `role.create` | None |
| Role edit | `/platform/roles/:id/edit` | `role.update` | The header **Edit** button is `<Can permission="role.update">` |
| Permission Catalog | `/platform/permissions` | `role.read` | None (read-only screen) |
| Super Admins | `/platform/super-admins` | `requireSuperAdmin` | None — only super admins ever reach the page |
| User Platform list | `/platform/user-platform` | `user_platform.read` | None |
| User Platform detail | `/platform/user-platform/:userId` | `user_platform.read` | `<Can permission="user_platform.manage">` wraps the Add Role button, the add-role form, and each per-row Remove button |

The sidebar mirrors the route guards (`src/components/Layout.tsx`, "Platform" group):

| Sidebar entry | Filter condition |
|---|---|
| Roles | `permission: 'role.read'` |
| Super Admins | `superAdminOnly: true` |
| User Platform | `permission: 'user_platform.read'` |
| Permission Catalog | — no sidebar entry; reached from the Roles header button |

A failed route guard renders the `Forbidden` page (`src/pages/Forbidden.tsx` — renamed from an inline `AccessDenied` component previously defined inside `PrivateRoute.tsx`) **in place**, leaving the URL untouched, inside the normal `<Layout>` shell — the sidebar stays visible, the session stays valid, and two actions are offered: "Go Back" (context-aware, falls back to `/dashboard` if there's no sensible back target) and "Go to Dashboard". A direct `/403` route renders the same page. `/dashboard` and `/profile` remain authenticated-only — any signed-in user reaches them regardless of permissions. The full per-route key map for the rest of the SPA lives in [Permissions](/en/platform/rbac/permissions).

## 5. Migration from the legacy role model

Until 2026-06-10 the SPA gated access by a single `platform_role` enum on the user row (`platform_admin`, `support_manager`, `support_staff`, etc.) and `allowedRoles` arrays on each route. That model is fully removed — from the frontend in commit `6091ffc` ("remove legacy platform_role from frontend") and from the login gate in commit `5f629f2` ("permission-based login gate — drop platform_role/ALLOWED_ROLES from login"), both in the `carmen-platform` repo. The `enum_platform_role` enum and the `tb_user.platform_role` column are likewise gone from the backend Prisma platform schema.

| Legacy (removed) | Replacement | Notes |
|---|---|---|
| `tb_user.platform_role` enum (one value per user) | Catalog + roles + scoped assignments (`tb_platform_permission` / `tb_platform_role` / `tb_user_tb_platform_role`) | A user can now hold many roles, each platform-wide or per-cluster |
| `allowedRoles={[...]}` prop on `PrivateRoute` | `requiredPermission="resource.action"` (or `requireSuperAdmin`) | One key per route instead of a duplicated role array |
| `AuthContext.hasRole(roles[])` | `AuthContext.hasPermission(key, { clusterId? })` → `checkPermission` | Same bootstrap escape hatch carried over |
| Login-time `ALLOWED_ROLES` role-name allow-list | Must-hold-≥1-permission gate (super-admin, any platform key, or any cluster key) | Commit `5f629f2`; bootstrap exception applies to this gate too |
| Sidebar `roles: [...]` filter in `Layout.tsx` | Sidebar `permission:` / `superAdminOnly:` filter | Same hide-don't-disable behaviour |
| `super_admin` enum value | `tb_platform_super_admin` flag table → `is_super_admin` bypass | A flag with real bypass semantics, unlike the old enum value which carried no extra routes |
| AccessDenied message quoting the failing role name | Generic "You don't have permission to access this page." | The SPA no longer has a single role value to display |

This module supersedes the legacy Authentication & Roles page (removed from this wiki); anything written against the old model (role names such as `support_manager`/`support_staff`, `allowedRoles` tables) describes behaviour that no longer exists in the SPA.

## 6. Related Modules

- [users](/en/platform/users) — owns the `tb_user` identity rows that assignments and the super-admin flag point at. User creation/lifecycle stays in the Users module; the User Platform screen only manages role assignments.
- [applications](/en/platform/applications) — the machine-client counterpart: grants `api_name` keys (same `resource.action` shape) to API clients. Useful contrast when reasoning about whether a caller is gated by RBAC (human session) or application grants (machine token).
- [clusters](/en/platform/clusters) — cluster-scoped assignments reference `tb_cluster` ids; the add-role form's cluster dropdown is fed by the cluster list. Cluster screens are guarded by `cluster.read/create/update`.
- [business-units](/en/platform/business-units) — **gotcha:** the `/business-units`, `/business-units/new`, and `/business-units/:id/edit` routes reuse the `cluster.read` / `cluster.create` / `cluster.update` keys. There are no `business_unit.*` keys — granting cluster access also grants Business Units, and you cannot grant one without the other.

## 7. Pages in This Module

- [Data Model](/en/platform/rbac/data-model) — the five Prisma tables, soft-delete unique constraints, scope column, and divergences from the SPA TypeScript shapes.
- [UI Screens](/en/platform/rbac/ui-screens) — Roles list/edit with the PermissionPicker, the read-only Permission Catalog, the Super Admins list, and the User Platform assignment screens.
- [Permissions](/en/platform/rbac/permissions) — the full route-guard matrix, how route/sidebar/in-page gates compose, the permission-resolution algorithm, and edge cases for testers.
