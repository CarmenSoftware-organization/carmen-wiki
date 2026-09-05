---
title: Cluster — Permissions
description: Permission-key route guards, the feature-flag layer, in-page Can gates, the platform-authority/cluster-admin redirect, and what each cluster.* key opens.
published: true
date: 2026-09-05T14:00:00.000Z
tags: book/platform, clusters, permissions
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Permissions

> **At a Glance**
> **Gate:** the three cluster routes carry `requiredPermission="cluster.read"` / `"cluster.create"` / `"cluster.update"` **and** `feature="clusters"` on `PrivateRoute` &nbsp;·&nbsp; **In-page gates:** `<Can>`/`canEdit` wraps Add Cluster (`cluster.create`), row Edit (`cluster.update`), row/header **View History** (`activity_log.read` — new), row Delete (`cluster.delete`), and every plate/tab field or action on the edit page (`cluster.update`, computed once as `canEdit`) — the row and edit-page gates are **cluster-scoped** via `clusterId` &nbsp;·&nbsp; **`cluster.delete` is in-page only** — no route requires it &nbsp;·&nbsp; **Bootstrap exception:** `hasPermission` returns `true` unconditionally when `userCount !== null && userCount <= 1` (first-admin setup) &nbsp;·&nbsp; **Platform-authority check runs before the permission check** — a session with no platform-wide or cluster-scoped grant at all is redirected to `/cluster-admin` (if it holds that scope) rather than shown a 403 &nbsp;·&nbsp; **On permission failure:** `<Forbidden>` (403 page) renders inside `<Layout>` (sidebar stays visible) &nbsp;·&nbsp; **Canonical model doc:** [rbac permissions](/en/platform/rbac/permissions)

## 1. Overview

Cluster management carries admin-tier responsibility: creating or editing a cluster affects licence capacity, defines the top-level tenant container that all business units and users belong to, and can have cross-tenant data implications if the wrong sessions are permitted. Access is governed by the platform's permission-based RBAC model ([rbac](/en/platform/rbac)): the backend catalog defines `cluster.read`, `cluster.create`, `cluster.update`, `cluster.delete`, and (cross-cutting, new since the last sync) `activity_log.read`; roles bundle those keys; and assignments bind roles to users either platform-wide or scoped to a single cluster.

The gating mechanism has four layers now (one more than the prior sync), all still resolving permission strings through the same `AuthContext.hasPermission` → `checkPermission` path (algorithm walkthrough in [rbac permissions](/en/platform/rbac/permissions) §4):

1. **Authentication + platform-authority resolution** (`PrivateRoute`, new logic — §5) — decides whether this session belongs in the platform-admin view at all, before any permission string is even consulted.
2. **Route-level `requiredPermission`** — `<Forbidden>` in place on failure.
3. **Route-level `feature`** — a feature-flag check, evaluated *after* the permission check (§2), so a session without access still sees 403 rather than a flag-driven 404.
4. **In-page `<Can permission="..." clusterId?>`** — wraps individual mutating buttons; cluster-scoped call sites (Clusters and Business Units are the SPA's only ones) resolve against a specific cluster's grants.

Until 2026-06 these routes were instead gated by hardcoded role-enum arrays; that model has been fully removed from the SPA, the login gate, and the Prisma schema — the migration mapping is documented in [rbac](/en/platform/rbac) §5 and is not repeated here.

## 2. Route guards

| Route | Component rendered | `requiredPermission` | `feature` | Source |
|---|---|---|---|---|
| `/clusters` | `ClusterManagement` | `cluster.read` | `clusters` | `src/App.tsx` (cluster route block) |
| `/clusters/new` | `ClusterEdit` | `cluster.create` | `clusters` | `src/App.tsx` |
| `/clusters/:id/edit` | `ClusterEdit` | `cluster.update` | `clusters` | `src/App.tsx` |

Each route carries one permission key plus the same feature-flag key. **New since the last sync:** `PrivateRoute` now accepts an optional `feature` prop (a key in the feature-flag catalog, `src/constants/featureFlags.ts`), checked *last*, after both the permission check and the `requireSuperAdmin` check:

```
if (requiredPermission && !hasPermission(requiredPermission)) return <Forbidden />;
if (requireSuperAdmin && !isSuperAdmin) return <Forbidden />;
if (feature) {
  if (!flagsReady) return <div className="loading">…</div>;
  const state = flagOf(feature);
  if (state === 'hide') return <NotFound />;
  if (state === 'inactive') return <ComingSoon />;
}
return <>{children}</>;
```

The ordering is deliberate (source comment, `src/components/PrivateRoute.tsx`): "permission answers *can you access this*, the flag answers *is this ready yet*" — someone without `cluster.*` access must still see 403, not a 404 that hides whether the route exists. A session that **does** hold the required permission but whose `clusters` feature flag is set to `hide` gets a 404 instead of the cluster screen; `inactive` gets a "Coming Soon" placeholder instead. This is a cross-cutting mechanism (documented in full under the **feature-flags** module — forward link, not yet written as of this sync) rather than anything specific to clusters, but it now sits on every cluster route and is a real state QA can put the app into.

Three things to note, unchanged from the prior sync:

- **Route guards check without a `clusterId`.** `PrivateRoute` calls `hasPermission(requiredPermission)` with no options, taking the broad "any cluster grants it" branch — a role assignment scoped to a single cluster still opens `/clusters` and `/clusters/:id/edit` for *every* cluster. The scoped narrowing happens at the in-page `<Can clusterId>` gates (§3) and in backend enforcement.
- **No route requires `cluster.delete`.** Deletion is reachable only through the list page's row action, gated in-page (§7).
- **Key-reuse gotcha:** `/business-units*` routes reuse the same `cluster.read`/`cluster.create`/`cluster.update` keys — there are no `business_unit.*` keys. The reuse extends to the in-page `cluster.delete` gate: the Business Units list wraps its row Delete in `<Can permission="cluster.delete" clusterId={row.original.cluster_id}>`.

## 3. Effective access matrix

Read the table as "what a session holding exactly this grant can do on the cluster surfaces," **assuming the `clusters` feature flag is not `hide`/`inactive`** (§2). Grants combine additively; a **super-admin** session bypasses every row.

| Grant held | `/clusters` list | Add Cluster | Row Edit / edit page | Row Delete | View History | Notes |
|---|---|---|---|---|---|---|
| None of `cluster.*` | `Forbidden` (403); sidebar entry hidden | — | — | — | — | Can still type the URL; route guard catches |
| `cluster.read` (platform scope) | Full list, search, filters, CSV export | Hidden — both the header button and the empty-state button are `<Can permission="cluster.create">`-gated, so neither renders | Row Edit hidden; edit route blocked | Hidden | Hidden | Read-only persona; row-action menu renders empty or near-empty |
| + `cluster.create` (platform scope) | — | Visible and functional | — | — | — | Create form only |
| + `cluster.update` (platform scope) | — | — | Row Edit on every row; edit page's `canEdit` resolves `true` | — | — | Unlocks the full plate + all three tabs, incl. Branding uploads and Users tab management |
| + `cluster.update` scoped to cluster A | — | — | Edit route opens for *any* cluster (broad route check), but row Edit renders and `canEdit` resolves `true` only for cluster A | — | — | The scoped-vs-broad asymmetry testers should target |
| + `cluster.delete` (platform or scoped) | — | — | — | Row Delete renders (per matching cluster when scoped) | — | Also gates the Business Units row Delete via the key-reuse gotcha (§2) |
| + `activity_log.read` (platform or scoped) | — | — | — | — | View History renders (list row + edit-page header, per matching cluster when scoped) | Independent of every other cluster key — a session can hold this without holding any `cluster.*` grant at all, though without `cluster.read` it would never reach a cluster row to click it from |

## 4. Bootstrap exception

Unchanged from the prior sync. `hasPermission()` in `AuthContext.tsx` still carries the first-admin shortcut forward:

```
const hasPermission = (key: string, opts?: { clusterId?: string }): boolean => {
  if (userCount !== null && userCount <= 1) return true;
  return checkPermission(effectivePermissions, key, opts);
};
```

When `userCount !== null && userCount <= 1`, every route guard, sidebar filter, and `<Can>` gate passes, including all cluster gates and `activity_log.read`. `userCount` is refreshed on `AuthProvider` mount and on every successful login (`fetchUserCount()`), and stays `null` (checks run strictly) while that fetch is pending or has failed. Full walkthrough in [rbac permissions](/en/platform/rbac/permissions) §4.

## 5. Platform-authority resolution (new layer, ahead of the permission check)

`PrivateRoute` now resolves **who this session is** before it ever looks at `requiredPermission`. This did not exist at the prior sync and changes what a permission-less session actually experiences on `/clusters*`:

```
if (effectivePermissions !== null && !hasPlatformAuthority) {
  if (adminScope === null) return <div className="loading">…</div>;
  if (hasClusterAdminScope) return <Navigate to="/cluster-admin" replace />;
  // else: falls through to the requiredPermission check below
}
```

`hasPlatformAuthority` (`../carmen-platform/src/utils/permissions.ts`, `checkPlatformAuthority`) is `true` for a super-admin, for any platform-wide permission grant, or for **any** cluster-scoped grant — deliberately **not** true for a user whose only standing is a `tb_cluster_user.role = 'admin'` membership (that role, §4 of [Data Model](/en/platform/clusters/data-model), is a tenant-membership attribute, not platform authority). A session with a resolved permission payload and no platform authority at all is redirected to `/cluster-admin` if it has that scope (a distinct persona and route tree — see [business-units](/en/platform/business-units) and the source map's `cluster-admin` row); if it has neither authority, the check falls through to the ordinary `requiredPermission` gate below it, which will then 403 it exactly as before. This branch exists so a pure cluster-admin member is routed to the surface built for them instead of hitting a confusing 403 on the platform-admin list, and so it does not change the *outcome* for a genuinely permission-less session — only for one with legitimate cluster-admin-only standing.

## 6. Forbidden (403) behaviour

`PrivateRoute` still implements two distinct rejection paths, unchanged from the prior sync:

**Auth-fail (no session):** renders `<Navigate to="/login" replace />`.

**Permission-fail (authenticated, resolved as platform-side, but missing the key):** renders `<Forbidden />` **in place** — `src/pages/Forbidden.tsx`, wrapped in `<Layout>` so the sidebar and header remain visible. A `StatusPage` shows a shield-X icon, "403", "Access Denied", and two actions: **Go Back** (`useBackOrFallback`, falling back to `/dashboard`) and **Go to Dashboard**. A separate `NotFound.tsx` (404) serves the catch-all route and, since §2, also serves any route whose `feature` flag resolves to `hide` — including `/clusters*` if that flag were ever set that way.

## 7. Sidebar filter

`platformNav.ts` defines the Clusters entry (in the group `navGroup.organization`) as:

```
{ path: '/clusters', labelKey: 'nav.clusters', icon: Network, permission: 'cluster.read', groupKey: 'navGroup.organization', feature: 'clusters' }
```

**Nav item definitions moved from `src/components/Layout.tsx` to a dedicated `src/components/nav/platformNav.ts` since the prior sync** (part of the i18n rework — labels are now translation keys, not literal English strings), and the entry now also carries the `feature` key so the sidebar can hide/grey the item consistently with the route guard. The array is still filtered before rendering (`(!item.permission || hasPermission(item.permission)) && (!item.superAdminOnly || isSuperAdmin)`, plus a feature-flag pass), so there is no divergence where a visible entry leads to `Forbidden`.

Two neighbouring entries in the same nav group reuse `cluster.read`: **Business Units** (`feature: 'business_units'`) and **Tenant Migrations** (`feature: 'tenant_migrations'`, a module outside this page's scope — see the source map). Any future change to which key gates Clusters must be applied in `src/App.tsx` (route) AND `src/components/nav/platformNav.ts` (sidebar) together.

A user without `cluster.read` does not see the Clusters entry, and (per §5) a user with no platform authority at all is redirected away from the platform shell before the sidebar even renders it.

## 8. Within the cluster surface

Passing the route guard does not unlock every button — the mutating actions carry their own `<Can>` gates, cluster-scoped where noted (a platform-scoped grant passes everywhere; a cluster-scoped grant passes only on its own cluster):

| Action | In-page gate | Cluster-scoped? |
|---|---|---|
| View list (pagination, search, filters) | None — route key (`cluster.read`) suffices | — |
| Export cluster list as CSV | None — any `cluster.read` holder can export | — |
| Add Cluster (header button) | `<Can permission="cluster.create">` | No |
| Add Cluster (empty-state button) | `<Can permission="cluster.create">` (`ClusterManagement.tsx` lines 670–671) — an earlier version of this page called this button ungated; it is not. The `cluster.create` route guard on `/clusters/new` is still a live second layer if the button were ever reached without the permission | No |
| Row Edit (list dropdown) | `<Can permission="cluster.update" clusterId={row.original.id}>` | Yes |
| Row/header **View History** | `<Can permission="activity_log.read" clusterId={...}>` — **new** | Yes |
| Row Delete (list dropdown) | `<Can permission="cluster.delete" clusterId={row.original.id}>` — plus a client-side "has business units" guard regardless of permission | Yes |
| Plate identity fields (name/status/code/alias), Branding uploads | `disabled={!canEdit}`, `canEdit = hasPermission('cluster.update', { clusterId: id })` computed once per page | Yes |
| Save Changes / Cancel (sticky bar) | None of their own — the bar only appears when the plate's identity fields differ, and those fields are already `canEdit`-gated | Indirectly |
| Licensing tab: subscription content | `subscription.read` internally (inside `SubscriptionCard`, out of this module's scope) — renders nothing without it | Yes, per the cluster |
| Add User button, bulk Remove action, per-row Role edit, per-row Remove (Users tab) | `canEdit` (same boolean as the plate) | Yes |
| Add BU (navigate-to-new, Business Units tab) | `<Can permission="cluster.create">` (unscoped) | No |
| BU row Edit (Pencil, navigate-to-edit) | None in-page — the target `/business-units/:id/edit` route reuses `cluster.update` | — |

Two tester-relevant consequences, both carried forward unchanged: the cluster-user management actions all still share the single page-level `canEdit` boolean rather than each carrying its own `<Can>` call; and the BU-quota cap that disables the Add BU button is now a licence-ledger fact (`bu_cap`, see [Data Model](/en/platform/clusters/data-model) §2.4) rather than a permission gate — all permitted sessions see the same enabled/disabled state. **The bulk "Move to BU" action documented in the prior sync no longer exists** — it depended on `parent_bu_id`, which has been removed (§ Data Model §2.2). Test plans should cover the scoped gates (§3) per cluster, not per persona, and should now also exercise the `clusters` feature flag's `hide`/`inactive` states (§2) alongside the permission matrix.

## 9. References

**Primary sources (read these before updating this page):**
- `../carmen-platform/src/App.tsx` — the three cluster routes with `requiredPermission` + `feature` props.
- `../carmen-platform/src/components/PrivateRoute.tsx` — auth-fail redirect, platform-authority/cluster-admin resolution (§5, new), permission-fail `<Forbidden />`, `requireSuperAdmin`, and the feature-flag check (§2), in that order.
- `../carmen-platform/src/context/AuthContext.tsx` — `hasPermission`, `hasPlatformAuthority`, `userCount` state, `fetchUserCount`, login permission gate.
- `../carmen-platform/src/utils/permissions.ts` — pure `checkPermission` resolution, `checkPlatformAuthority`, and the `UNRESOLVED_CLUSTER_ID`/`PLATFORM_SCOPED_RECORD` sentinels used by other modules' `activity_log.read` call sites (not needed for clusters itself, since a cluster row always has a resolvable id).
- `../carmen-platform/src/context/FeatureFlagContext.tsx` — `flagOf`/`isReady`, consumed by `PrivateRoute`'s `feature` check.
- `../carmen-platform/src/components/PrivateRoute.tsx`, `src/pages/Forbidden.tsx`, `src/pages/NotFound.tsx`, `src/pages/ComingSoon.tsx` — the three possible route-guard outcomes.
- `../carmen-platform/src/components/Can.tsx` — the in-page gate component (`permission`, optional `clusterId`, optional `fallback`) — unchanged.
- `../carmen-platform/src/components/nav/platformNav.ts` — nav item definitions (Clusters, Business Units, Tenant Migrations), including `permission`/`feature`/`groupKey`/`superAdminOnly`.
- `../carmen-platform/src/pages/ClusterManagement.tsx` / `ClusterEdit.tsx` and `clusterEdit/sections/*.tsx` — the `<Can>`/`canEdit` call sites listed in §8, including the new `activity_log.read` sites.

**Cross-links:**
- [rbac](/en/platform/rbac) — the permission model: catalog, roles, scoped assignments, super-admin flag, and the legacy-model migration table (§5)
- [rbac permissions](/en/platform/rbac/permissions) — SPA-wide gate matrix and the full permission-resolution algorithm
- [users](/en/platform/users) — user identity rows that role assignments point at
- [clusters](/en/platform/clusters) — Clusters module landing
- [Data Model](/en/platform/clusters/data-model) &nbsp;·&nbsp; [UI Screens](/en/platform/clusters/ui-screens) — sibling sub-pages
