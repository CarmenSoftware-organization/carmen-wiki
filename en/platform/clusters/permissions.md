---
title: Cluster — Permissions
description: Permission-key route guards, in-page Can gates, bootstrap exception, and sidebar filter for all cluster operations.
published: true
date: 2026-06-10T13:30:00.000Z
tags: book/platform, clusters, permissions
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Permissions

> **At a Glance**
> **Gate:** the three cluster routes carry `requiredPermission="cluster.read"` / `"cluster.create"` / `"cluster.update"` on `PrivateRoute` &nbsp;·&nbsp; **In-page gates:** `<Can>` wraps Add Cluster (`cluster.create`), row Edit (`cluster.update`), row Delete (`cluster.delete`), and the edit-page Edit toggle (`cluster.update`) — the row and edit-page gates are **cluster-scoped** via `clusterId` &nbsp;·&nbsp; **`cluster.delete` is in-page only** — no route requires it &nbsp;·&nbsp; **Bootstrap exception:** `hasPermission` returns `true` unconditionally when `userCount !== null && userCount <= 1` (first-admin setup) &nbsp;·&nbsp; **On failure:** `<AccessDenied>` renders inside `<Layout>` (sidebar stays visible) &nbsp;·&nbsp; **Canonical model doc:** [rbac permissions](/en/platform/rbac/permissions)

## 1. Overview

Cluster management carries admin-tier responsibility: creating or editing a cluster affects license capacity (`max_license_bu`), defines the top-level tenant container that all business units and users belong to, and can have cross-tenant data implications if the wrong sessions are permitted. Access is governed by the platform's permission-based RBAC model ([rbac](/en/platform/rbac)): the backend catalog defines `cluster.read`, `cluster.create`, `cluster.update`, and `cluster.delete` keys; roles bundle those keys; and assignments bind roles to users either platform-wide or scoped to a single cluster.

The gating mechanism has three layers, all resolving through the same `AuthContext.hasPermission` → `checkPermission` path (algorithm walkthrough in [rbac permissions](/en/platform/rbac/permissions) §4). At the route level, `PrivateRoute` receives a `requiredPermission` prop and renders `<AccessDenied>` inside the normal `<Layout>` shell when the check fails. At the navigation level, `Layout.tsx` filters the sidebar so users without `cluster.read` never see the Clusters entry. At the action level, `<Can permission="..." clusterId?>` wraps the mutating buttons on both cluster screens — and the cluster gates are the SPA's only `<Can>` call sites (alongside Business Units) that pass a `clusterId`, activating the cluster-scoped resolution branch.

Until 2026-06 these routes were instead gated by hardcoded role-enum arrays on each route; that model has been fully removed from the SPA, the login gate, and the Prisma schema — the migration mapping is documented in [rbac](/en/platform/rbac) §5 and is not repeated here.

## 2. Route guards

| Route | Component rendered | `requiredPermission` | Source |
|---|---|---|---|
| `/clusters` | `ClusterManagement` | `cluster.read` | `src/App.tsx` (cluster route block, lines 60–83) |
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
| None of `cluster.*` | `AccessDenied`; sidebar entry hidden | — | — | — | Can still type the URL; route guard catches |
| `cluster.read` (platform scope) | Full list, search, filters, CSV export | Hidden (header); empty-state Add still visible but leads to `AccessDenied` | Row Edit hidden; `/clusters/:id/edit` route blocked | Hidden | Read-only persona; row-action menu renders empty |
| + `cluster.create` (platform scope) | — | Visible and functional | — | — | Create form only; post-create navigation quirk in [UI Screens](./ui-screens.md) §3 |
| + `cluster.update` (platform scope) | — | — | Row Edit on every row; edit route opens; Edit toggle renders | — | Unlocks the full edit page incl. Branding uploads and cluster-user management (§7) |
| + `cluster.update` scoped to cluster A | — | — | Edit route opens for *any* cluster (broad route check), but row Edit and the Edit toggle render only for cluster A | — | The scoped-vs-broad asymmetry testers should target |
| + `cluster.delete` (platform or scoped) | — | — | — | Row Delete renders (per matching cluster when scoped) | Consumed by the cluster row Delete and — via the key-reuse gotcha (§2) — the Business Units row Delete; no other surface |

## 4. Bootstrap exception

`hasPermission()` in `AuthContext.tsx` (lines 210–214) carries the first-admin shortcut forward from the legacy model:

```
const hasPermission = (key: string, opts?: { clusterId?: string }): boolean => {
  // Bootstrap escape hatch: 0–1 users => allow everything.
  if (userCount !== null && userCount <= 1) return true;
  return checkPermission(effectivePermissions, key, opts);
};
```

When `userCount !== null && userCount <= 1`, the function returns `true` unconditionally — every route guard, sidebar filter, and `<Can>` gate passes, including all cluster gates. This allows the first administrator of a fresh installation to reach `/clusters` (and everything else) before any catalog roles have been assigned.

**How `userCount` is populated.** On `AuthProvider` mount and on every successful login, `fetchUserCount()` (line 103) calls `userService.getAll({ page: 1, perpage: 1 })` and reads the total via the fallback chain `response.paginate?.total ?? response.total ?? response.data?.length ?? 0`. The value lives in React state (line 20), initialised to `null`.

**The `userCount === null` case.** While the count fetch is pending (or if it failed), the condition is `false` and checks run strictly against the permission snapshot — the exception fails closed, not open.

**The `userCount > 1` case.** Once a second user exists the exception is dormant. The count refreshes only on mount and login, so deleting users mid-session does not re-arm it until the next refresh.

**Scope of the exception.** Unlike the legacy model, the bootstrap branch also reaches the **login gate**: `login()` requires the account to hold at least one permission (or the super-admin flag) before admitting a session, and skips that requirement when the user count is 0 or 1. Full login pseudo-code in [rbac permissions](/en/platform/rbac/permissions) §4.

## 5. AccessDenied behaviour

`PrivateRoute` (`src/components/PrivateRoute.tsx`) implements two distinct rejection paths:

**Auth-fail (no session):** if `isAuthenticated` is `false`, the component renders `<Navigate to="/login" replace />` — a hard redirect that replaces the current history entry. The user ends up on the login page with no visible error in the current view.

**Permission-fail (authenticated but missing the key):** if `requiredPermission` is set and `hasPermission(requiredPermission)` returns `false`, the component renders `<AccessDenied />` (defined in the same file, lines 9–37), which is wrapped in `<Layout>` so the full sidebar and header remain visible. Inside the content area, a centred card displays a shield-X icon, the heading "Access Denied" in red, the generic message "You don't have permission to access this page.", and a "Back to Dashboard" button. Unlike the legacy version, the message no longer quotes the failing role — there is no single role value to display under the permission model. (`PrivateRoute` also supports a `requireSuperAdmin` prop with the same failure rendering, but no cluster route uses it.)

The consequence for permission-fail users is that they remain inside the SPA shell, can still use the sidebar to navigate to permitted pages, and are not logged out — their session stays valid.

## 6. Sidebar filter

`Layout.tsx` (line 52) defines the Clusters nav item in the "Organization" group as:

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

The sidebar `permission` value (`cluster.read`) matches the `/clusters` route guard exactly, so there is no divergence where a visible entry leads to `AccessDenied`. The neighbouring **Business Units** entry (line 53) also filters on `cluster.read` — the sidebar half of the key-reuse gotcha from §2, which also extends to the in-page `cluster.delete` gate on the BU row Delete, not just the three route keys. Any future change to which key gates Clusters must be applied in BOTH `src/App.tsx` (the route guard) AND `src/components/Layout.tsx` (the sidebar `permission` field); pulling one and not the other would expose the entry while blocking the route, or vice versa.

A user without `cluster.read` simply does not see the Clusters entry. They can still reach `/clusters` by typing the URL directly, but the route guard renders `<AccessDenied>` before any cluster data is loaded.

## 7. Within the cluster surface

Unlike the legacy model, passing the route guard no longer unlocks every button — the mutating actions carry their own `<Can>` gates, and the cluster gates pass a `clusterId`, so they resolve against that specific cluster's grants (a platform-scoped grant passes everywhere; a cluster-scoped grant passes only on its own cluster):

| Action | In-page gate | Cluster-scoped? |
|---|---|---|
| View list (pagination, search, filters) | None — route key (`cluster.read`) suffices | — |
| Export cluster list as CSV | None — any `cluster.read` holder can export | — |
| Add Cluster (header button) | `<Can permission="cluster.create">` | No |
| Add Cluster (empty-state button) | **Ungated** — renders for any `cluster.read` holder; the `cluster.create` route guard on `/clusters/new` catches | No |
| Row Edit (list dropdown) | `<Can permission="cluster.update" clusterId={row.original.id}>` | Yes |
| Row Delete (list dropdown) | `<Can permission="cluster.delete" clusterId={row.original.id}>` | Yes |
| Edit toggle (edit page header) | `<Can permission="cluster.update" clusterId={id}>` | Yes |
| Save / Cancel on edit form | None — unreachable without the gated Edit toggle | — |
| Branding logo/avatar upload | None — but `disabled={!editing}`, so effectively behind the Edit toggle's `cluster.update` gate | Indirectly |
| Add BU (navigate-to-new) / BU row Edit | None in-page — the target `/business-units*` routes reuse `cluster.create` / `cluster.update` | No |
| Add / Edit / Remove cluster user | **None** — visible and clickable for anyone who reaches the edit page | — |

Two tester-relevant consequences. First, the cluster-user management actions (Add User, Edit Cluster User, Remove) carry no key gate of their own — reaching the edit route (broad `cluster.update` check) is enough to see them, so backend enforcement is the only boundary on those mutations. Second, the `max_license_bu` / `max_license_users` caps that disable the Add BU button and BU options are business-rule constraints, not permission gates — all permitted sessions see the same enabled/disabled state. Test plans should cover the scoped gates (§3, scoped-grant row) per cluster, not per persona.

## 8. References

**Primary sources (read these before updating this page):**
- `../carmen-platform/src/App.tsx` — the three cluster routes with `requiredPermission` props (route block lines 60–83).
- `../carmen-platform/src/context/AuthContext.tsx` — `hasPermission` (lines 210–214), `userCount` state (line 20), `fetchUserCount` (line 103), login permission gate (`login`, line 115).
- `../carmen-platform/src/utils/permissions.ts` — pure `checkPermission` resolution (super-admin → platform keys → cluster keys), `DEV_MOCK_EFFECTIVE_PERMISSIONS`.
- `../carmen-platform/src/components/PrivateRoute.tsx` — auth-fail redirect, permission-fail `<AccessDenied>` render (component at lines 9–37).
- `../carmen-platform/src/components/Can.tsx` — the in-page gate component (`permission`, optional `clusterId`, optional `fallback`).
- `../carmen-platform/src/components/Layout.tsx` — sidebar `NavItem[]` with `permission` fields and the filter expression (lines 49–71).
- `../carmen-platform/src/pages/ClusterManagement.tsx` / `ClusterEdit.tsx` — the `<Can>` call sites listed in §7.

**Cross-links:**
- [rbac](/en/platform/rbac) — the permission model: catalog, roles, scoped assignments, super-admin flag, and the legacy-model migration table (§5)
- [rbac permissions](/en/platform/rbac/permissions) — SPA-wide gate matrix and the full permission-resolution algorithm
- [users](/en/platform/users) — user identity rows that role assignments point at
- [clusters](/en/platform/clusters) — Clusters module landing
- [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) — sibling sub-pages
