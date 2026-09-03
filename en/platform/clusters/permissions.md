---
title: Cluster — Permissions
description: Permission-key route guards, in-page Can gates, bootstrap exception, and sidebar filter for all cluster operations.
published: true
date: 2026-07-29T06:35:38.000Z
tags: book/platform, clusters, permissions
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Permissions

> **At a Glance**
> **Gate:** the three cluster routes carry `requiredPermission="cluster.read"` / `"cluster.create"` / `"cluster.update"` on `PrivateRoute` &nbsp;·&nbsp; **In-page gates:** `<Can>`/`canEdit` wraps Add Cluster (`cluster.create`), row Edit (`cluster.update`), row Delete (`cluster.delete`), and every Details/Branding/Users field or action on the edit page (`cluster.update`, computed once as `canEdit`, no page-level Edit toggle) — the row and edit-page gates are **cluster-scoped** via `clusterId` &nbsp;·&nbsp; **`cluster.delete` is in-page only** — no route requires it &nbsp;·&nbsp; **Bootstrap exception:** `hasPermission` returns `true` unconditionally when `userCount !== null && userCount <= 1` (first-admin setup) &nbsp;·&nbsp; **On failure:** `<Forbidden>` (403 page) renders inside `<Layout>` (sidebar stays visible) &nbsp;·&nbsp; **Canonical model doc:** [rbac permissions](/en/platform/rbac/permissions)

## 1. Overview

Cluster management carries admin-tier responsibility: creating or editing a cluster affects license capacity (`max_license_bu`), defines the top-level tenant container that all business units and users belong to, and can have cross-tenant data implications if the wrong sessions are permitted. Access is governed by the platform's permission-based RBAC model ([rbac](/en/platform/rbac)): the backend catalog defines `cluster.read`, `cluster.create`, `cluster.update`, and `cluster.delete` keys; roles bundle those keys; and assignments bind roles to users either platform-wide or scoped to a single cluster.

The gating mechanism has three layers, all resolving through the same `AuthContext.hasPermission` → `checkPermission` path (algorithm walkthrough in [rbac permissions](/en/platform/rbac/permissions) §4). At the route level, `PrivateRoute` receives a `requiredPermission` prop and renders `<Forbidden>` inside the normal `<Layout>` shell when the check fails. At the navigation level, `Layout.tsx` filters the sidebar so users without `cluster.read` never see the Clusters entry. At the action level, `<Can permission="..." clusterId?>` wraps the mutating buttons on both cluster screens — and the cluster gates are the SPA's only `<Can>` call sites (alongside Business Units) that pass a `clusterId`, activating the cluster-scoped resolution branch.

Until 2026-06 these routes were instead gated by hardcoded role-enum arrays on each route; that model has been fully removed from the SPA, the login gate, and the Prisma schema — the migration mapping is documented in [rbac](/en/platform/rbac) §5 and is not repeated here.

## 2. Route guards

| Route | Component rendered | `requiredPermission` | Source |
|---|---|---|---|
| `/clusters` | `ClusterManagement` | `cluster.read` | `src/App.tsx` (cluster route block, lines 72–93) |
| `/clusters/new` | `ClusterEdit` | `cluster.create` | `src/App.tsx` |
| `/clusters/:id/edit` | `ClusterEdit` | `cluster.update` | `src/App.tsx` |

Each route carries exactly one key — there is no shared constant, but unlike the legacy duplicated role arrays, the three keys are intentionally different per route, so the list/create/edit surfaces can be granted independently.

Three things to note:

- **Route guards check without a `clusterId`.** `PrivateRoute` calls `hasPermission(requiredPermission)` with no options, taking the broad "any cluster grants it" branch — a role assignment scoped to a single cluster still opens `/clusters` and `/clusters/:id/edit` for *every* cluster. The scoped narrowing happens at the in-page `<Can clusterId>` gates (§3) and in backend enforcement.
- **No route requires `cluster.delete`.** Deletion is reachable only through the list page's row action, gated in-page (§7).
- **Key-reuse gotcha:** the `/business-units`, `/business-units/new`, and `/business-units/:id/edit` routes reuse the same `cluster.read` / `cluster.create` / `cluster.update` keys — there are no `business_unit.*` keys, so any grant that opens cluster routes also opens the Business Units module, and the two cannot be separated. The reuse extends beyond the three route keys to the in-page `cluster.delete` gate: the Business Units list wraps its row Delete in `<Can permission="cluster.delete" clusterId={row.original.cluster_id}>`.

## 3. Effective access matrix

Read the table as "what a session holding exactly this grant can do on the cluster surfaces". Grants combine additively; a **super-admin** session (`is_super_admin` flag) bypasses every row and can do everything. Remember that SPA gates are advisory — the backend's own permission enforcement is the real security boundary.

| Grant held | `/clusters` list | Add Cluster | Row Edit / edit page | Row Delete | Notes |
|---|---|---|---|---|---|
| None of `cluster.*` | `Forbidden` (403); sidebar entry hidden | — | — | — | Can still type the URL; route guard catches |
| `cluster.read` (platform scope) | Full list, search, filters, CSV export | Hidden (header); empty-state Add still visible but leads to `Forbidden` | Row Edit hidden; `/clusters/:id/edit` route blocked | Hidden | Read-only persona; row-action menu renders empty |
| + `cluster.create` (platform scope) | — | Visible and functional | — | — | Create form only; post-create navigation quirk in [UI Screens](./ui-screens.md) §3 |
| + `cluster.update` (platform scope) | — | — | Row Edit on every row; edit route opens; edit page's `canEdit` resolves `true` (fields/uploads/actions become editable) | — | Unlocks the full edit page incl. Branding uploads and cluster-user management (§7) |
| + `cluster.update` scoped to cluster A | — | — | Edit route opens for *any* cluster (broad route check), but row Edit renders and `canEdit` resolves `true` only for cluster A | — | The scoped-vs-broad asymmetry testers should target |
| + `cluster.delete` (platform or scoped) | — | — | — | Row Delete renders (per matching cluster when scoped) | Consumed by the cluster row Delete and — via the key-reuse gotcha (§2) — the Business Units row Delete; no other surface |

## 4. Bootstrap exception

`hasPermission()` in `AuthContext.tsx` (line 220) carries the first-admin shortcut forward from the legacy model:

```
const hasPermission = (key: string, opts?: { clusterId?: string }): boolean => {
  // Bootstrap escape hatch: 0–1 users => allow everything.
  if (userCount !== null && userCount <= 1) return true;
  return checkPermission(effectivePermissions, key, opts);
};
```

When `userCount !== null && userCount <= 1`, the function returns `true` unconditionally — every route guard, sidebar filter, and `<Can>` gate passes, including all cluster gates. This allows the first administrator of a fresh installation to reach `/clusters` (and everything else) before any catalog roles have been assigned.

**How `userCount` is populated.** On `AuthProvider` mount and on every successful login, `fetchUserCount()` (line 105) calls `userService.getAll({ page: 1, perpage: 1 })` and reads the total via the fallback chain `response.paginate?.total ?? response.total ?? response.data?.length ?? 0`. The value lives in React state (line 21), initialised to `null`.

**The `userCount === null` case.** While the count fetch is pending (or if it failed), the condition is `false` and checks run strictly against the permission snapshot — the exception fails closed, not open.

**The `userCount > 1` case.** Once a second user exists the exception is dormant. The count refreshes only on mount and login, so deleting users mid-session does not re-arm it until the next refresh.

**Scope of the exception.** Unlike the legacy model, the bootstrap branch also reaches the **login gate**: `login()` requires the account to hold at least one permission (or the super-admin flag) before admitting a session, and skips that requirement when the user count is 0 or 1. Full login pseudo-code in [rbac permissions](/en/platform/rbac/permissions) §4.

## 5. Forbidden (403) behaviour

`PrivateRoute` (`src/components/PrivateRoute.tsx`) implements two distinct rejection paths:

**Auth-fail (no session):** if `isAuthenticated` is `false`, the component renders `<Navigate to="/login" replace />` — a hard redirect that replaces the current history entry. The user ends up on the login page with no visible error in the current view.

**Permission-fail (authenticated but missing the key):** if `requiredPermission` is set and `hasPermission(requiredPermission)` returns `false`, the component renders `<Forbidden />` **in place** — a dedicated page component (`src/pages/Forbidden.tsx`, not defined inline in `PrivateRoute` any more), still wrapped in `<Layout>` so the full sidebar and header remain visible. Rendering in place (rather than redirecting to a `/403` route) deliberately keeps the URL on the blocked route, so a "Go Back" click returns to a page the user could actually reach instead of bouncing forward again. Inside the content area, a `StatusPage` displays a shield-X icon, code "403", the heading "Access Denied" in red, the generic message "You don't have permission to access this page.", and two actions: **Go Back** (via `useBackOrFallback`, falling back to `/dashboard` if there is no in-app history to return to) and **Go to Dashboard**. Unlike the legacy version, the message no longer quotes the failing role — there is no single role value to display under the permission model. (`PrivateRoute` also supports a `requireSuperAdmin` prop with the same `<Forbidden />` rendering, but no cluster route uses it.)

The consequence for permission-fail users is that they remain inside the SPA shell, can still use the sidebar to navigate to permitted pages, and are not logged out — their session stays valid. A separate `NotFound.tsx` (404) page now serves the SPA's catch-all route (`path="*"`) — unmatched URLs like the pre-fix `/clusters/:id` create-navigation target (see [UI Screens](./ui-screens.md) §3) get a dedicated "Page Not Found" page instead of a silent redirect to Landing/Dashboard.

## 6. Sidebar filter

`Layout.tsx` (line 53) defines the Clusters nav item in the "Organization" group as:

```
{ path: '/clusters', label: 'Clusters', icon: Network, permission: 'cluster.read', group: 'Organization' }
```

The full `allNavItems` array is filtered before rendering:

```
const navItems = allNavItems.filter(
  (item) =>
    (!item.permission || hasPermission(item.permission)) &&
    (!item.superAdminOnly || isSuperAdmin),
);
```

The sidebar `permission` value (`cluster.read`) matches the `/clusters` route guard exactly, so there is no divergence where a visible entry leads to `Forbidden`. The neighbouring **Business Units** entry (line 54) also filters on `cluster.read` — the sidebar half of the key-reuse gotcha from §2, which also extends to the in-page `cluster.delete` gate on the BU row Delete, not just the three route keys. A third Organization-group entry, **Tenant Migrations** (`/tenant-migrations`, line 55), reuses the same `cluster.read` key too, though that screen is outside this module's own pages (see [business-units](/en/platform/business-units) for any cross-reference). Any future change to which key gates Clusters must be applied in BOTH `src/App.tsx` (the route guard) AND `src/components/Layout.tsx` (the sidebar `permission` field); pulling one and not the other would expose the entry while blocking the route, or vice versa.

A user without `cluster.read` simply does not see the Clusters entry. They can still reach `/clusters` by typing the URL directly, but the route guard renders `<Forbidden>` before any cluster data is loaded.

## 7. Within the cluster surface

Unlike the legacy model, passing the route guard no longer unlocks every button — the mutating actions carry their own `<Can>` gates, and the cluster gates pass a `clusterId`, so they resolve against that specific cluster's grants (a platform-scoped grant passes everywhere; a cluster-scoped grant passes only on its own cluster):

| Action | In-page gate | Cluster-scoped? |
|---|---|---|
| View list (pagination, search, filters) | None — route key (`cluster.read`) suffices | — |
| Export cluster list as CSV | None — any `cluster.read` holder can export | — |
| Add Cluster (header button) | `<Can permission="cluster.create">` | No |
| Add Cluster (empty-state button) | **Ungated** — renders for any `cluster.read` holder; the `cluster.create` route guard on `/clusters/new` catches | No |
| Row Edit (list dropdown) | `<Can permission="cluster.update" clusterId={row.original.id}>` | Yes |
| Row Delete (list dropdown) | `<Can permission="cluster.delete" clusterId={row.original.id}>` — plus a client-side "has business units" guard that blocks the confirm dialog regardless of permission | Yes |
| Details/Branding fields (edit-in-place) | `disabled={!canEdit}`, `canEdit = hasPermission('cluster.update', { clusterId: id })` computed once per page — no separate Edit toggle any more | Yes |
| Save Changes / Cancel (sticky bar) | None of their own — the bar only appears when Details fields differ, and those fields are already `canEdit`-gated | Indirectly |
| Add User button, bulk Remove / Move-to-BU actions (Users section) | `canEdit` (same boolean as Details/Branding) | Yes |
| Add BU (navigate-to-new) | `<Can permission="cluster.create">` (unscoped — no `clusterId` passed by `BusinessUnitsSection`) | No |
| BU row Edit (Pencil, navigate-to-edit) | None in-page — the target `/business-units/:id/edit` route itself reuses `cluster.update` | — |
| Per-row Parent-BU / Role inline edit, per-row Remove (Users section) | `canEdit` (same boolean) | Yes |

Two tester-relevant consequences. First, the cluster-user management actions (Add User, inline Role/Parent-BU edit, Remove, bulk actions) all share the single page-level `canEdit` boolean rather than each carrying its own `<Can>` call — reaching the edit route (broad `cluster.update` check) plus holding a scoped `cluster.update` grant for this specific cluster is what unlocks all of them together; backend enforcement remains the real boundary on the mutations themselves. Second, the `max_license_bu` / `max_license_users` caps that disable the Add BU button and BU options are business-rule constraints, not permission gates — all permitted sessions see the same enabled/disabled state. Test plans should cover the scoped gates (§3, scoped-grant row) per cluster, not per persona.

## 8. References

**Primary sources (read these before updating this page):**
- `../carmen-platform/src/App.tsx` — the three cluster routes with `requiredPermission` props (route block lines 72–93).
- `../carmen-platform/src/context/AuthContext.tsx` — `hasPermission` (line 220), `userCount` state (line 21), `fetchUserCount` (line 105), login permission gate (`login`, line 117).
- `../carmen-platform/src/utils/permissions.ts` — pure `checkPermission` resolution (super-admin → platform keys → cluster keys), `DEV_MOCK_EFFECTIVE_PERMISSIONS`.
- `../carmen-platform/src/components/PrivateRoute.tsx` — auth-fail redirect, permission-fail `<Forbidden />` render (18 lines total; renders the page component, no longer defines it inline).
- `../carmen-platform/src/pages/Forbidden.tsx` — the 403 page component itself (`StatusPage`, Go Back / Go to Dashboard actions).
- `../carmen-platform/src/pages/NotFound.tsx` — the 404 catch-all page (`path="*"` in `App.tsx`).
- `../carmen-platform/src/components/Can.tsx` — the in-page gate component (`permission`, optional `clusterId`, optional `fallback`).
- `../carmen-platform/src/components/Layout.tsx` — sidebar `NavItem[]` with `permission` fields (Clusters line 53, Business Units line 54, Tenant Migrations line 55) and the filter expression (from line 70).
- `../carmen-platform/src/pages/ClusterManagement.tsx` / `ClusterEdit.tsx` and `clusterEdit/sections/*.tsx` — the `<Can>`/`canEdit` call sites listed in §7.

**Cross-links:**
- [rbac](/en/platform/rbac) — the permission model: catalog, roles, scoped assignments, super-admin flag, and the legacy-model migration table (§5)
- [rbac permissions](/en/platform/rbac/permissions) — SPA-wide gate matrix and the full permission-resolution algorithm
- [users](/en/platform/users) — user identity rows that role assignments point at
- [clusters](/en/platform/clusters) — Clusters module landing
- [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) — sibling sub-pages
