---
title: Cluster Admin
description: The cluster-administration console — a second navigation and persona scoped to one cluster, gated by cluster membership rather than any RBAC permission key.
published: true
date: '2026-09-06T23:45:00.000Z'
tags: book/platform, cluster-admin
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Cluster Admin

> **At a Glance**
> **What this is:** A **second console**, not another screen of the platform admin product — its own navigation, its own layout chrome, and its own persona, mounted entirely under `/cluster-admin/:clusterId/*` &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA's customer-facing "cluster administrator" surface — a role a customer's own staff can hold without any platform RBAC grant &nbsp;·&nbsp; **Entry route:** `/cluster-admin` → `ClusterAdminEntry`, guarded by the authentication-only `AuthedRoute` &nbsp;·&nbsp; **Per-cluster routes:** `/cluster-admin/:clusterId/{cluster,business-units,business-units/:buId/edit,users,licenses,profile}`, all guarded by `ClusterAdminRoute` &nbsp;·&nbsp; **The gate:** **no RBAC permission key — gated instead by cluster membership via `isClusterAdminOf`**, checked before the feature flag, on every one of the five per-cluster routes &nbsp;·&nbsp; **Nav:** `clusterAdminNav.ts` applies **no permission filtering at all** — clearing the route guard is the whole check — and its four feature keys (`cluster_admin_cluster`, `cluster_admin_business_units`, `cluster_admin_licenses`, `cluster_admin_users`) are a **separate namespace** from the platform nav's keys, despite sharing menu labels &nbsp;·&nbsp; **Key entities/tables:** reads `tb_cluster`, `tb_business_unit`, `tb_cluster_user`, `tb_cluster_license`, `tb_business_unit_license` — the same tables the platform-side [Clusters](/en/platform/clusters), [Business Units](/en/platform/business-units), [Users](/en/platform/users) and [Licenses](/en/platform/licenses) modules own; this module owns no schema of its own &nbsp;·&nbsp; **e2e suite:** **None** — `../carmen-platform-e2e/tests/` has no `cluster-admin` directory; every claim on these pages is sourced from `../carmen-platform` (and, for the backend mirror of the gate, `../carmen-turborepo-backend-v2`) implementation directly &nbsp;·&nbsp; **Sub-pages:** 2

## 1. Overview

Cluster Admin is the Carmen Platform's second front door. Every other module in this book — Clusters, Business Units, Users, Licenses, RBAC — is reached through the platform admin's own sidebar and gated by an RBAC permission key from `tb_user_tb_platform_role`. This module is reached through an entirely different sidebar, built by a different function (`buildClusterAdminNav()`, `../carmen-platform/src/components/nav/clusterAdminNav.ts`), and gated by a different axis altogether: **cluster membership** — a row in `tb_cluster_user` with `role: 'admin'`, not a permission grant.

The landing point is `/cluster-admin`, wired to `ClusterAdminEntry` inside `AuthedRoute` (`../carmen-platform/src/App.tsx:578-581`). `AuthedRoute` checks only that the caller is authenticated — no permission, no membership check yet (`../carmen-platform/src/components/AuthedRoute.tsx:6-27`). Its own doc-comment explains why it has to be this thin: the platform's `PrivateRoute` redirects a membership-only cluster admin *to* `/cluster-admin` whenever it decides they have no platform authority (`../carmen-platform/src/components/PrivateRoute.tsx:60-81`), so wrapping `/cluster-admin` itself in `PrivateRoute` would redirect the route to itself forever. `ClusterAdminEntry` (`../carmen-platform/src/pages/clusterAdmin/ClusterAdminEntry.tsx`) resolves the rest itself from `adminScope`: exactly one administered cluster (and not a super admin) auto-redirects straight into it; anything else — zero clusters, several clusters, or a super admin who administers everything — renders a picker grid or, for zero clusters, an `EmptyState` the component's own comment describes as "not a 403 in substance… the user is authenticated and simply administers nothing" (lines 10-13).

Once inside a specific cluster, all five remaining routes carry `:clusterId` in the path and sit behind `ClusterAdminRoute` (`../carmen-platform/src/components/ClusterAdminRoute.tsx`), which resolves the membership question once per cluster and lets every page beneath it inherit the answer — see §3.2 and [Permissions](/en/platform/cluster-admin/permissions) for the exact check and its order. Because the cluster id lives in the URL rather than in any client-side selection state, the sidebar built from it (`buildClusterAdminNav`) literally cannot construct a link that leaves the cluster the URL names — every nav item is `${base}/...` where `base = /cluster-admin/${clusterId}` (`clusterAdminNav.ts:15`). Switching clusters is a `ClusterSwitcher` dialog in the header that navigates to a different URL, not a state change (`../carmen-platform/src/components/ClusterSwitcher.tsx:20-22`).

The chrome itself is `ClusterAdminLayout` (`../carmen-platform/src/components/ClusterAdminLayout.tsx`) — it reuses the platform's shared `Layout` component wholesale and supplies only three things: the nav items from `buildClusterAdminNav`, a `ClusterSwitcher` in the header slot, and the brand identity, which becomes the administered cluster's own name/code/avatar (falling back to the product brand only when the cluster isn't in the caller's own cached `adminScope.clusters` page — the super-admin case, where looking it up would cost a request just for a label). The brand link goes to `/cluster-admin/:clusterId/cluster`, not `/dashboard`.

## 2. Business Context

Carmen sells a cluster of business units to a hospitality customer, and that customer typically has someone on staff — an IT lead, a regional ops manager — who needs to see and lightly manage their own cluster without becoming a Carmen platform operator. Handing that person an RBAC role (`tb_user_tb_platform_role`) would be the wrong shape twice over: it would require Carmen support to provision and audit a platform-side grant for every customer admin, and — because platform roles are not inherently cluster-scoped in the way this relationship needs — it would risk that admin reaching clusters that are not theirs.

The product's answer is a membership row instead: `tb_cluster_user.role = 'admin'` marks someone as an administrator of one specific cluster, independent of any RBAC grant. That single row is what both `isClusterAdminOf` (frontend, `AuthContext.tsx`) and `ClusterAdminAuthzService.isClusterAdmin` (backend, §3.2) key off. A person can hold this standing on zero, one, or several clusters, can hold RBAC platform authority at the same time or not at all, and the two systems never consult each other.

What the customer admin gets to do inside their cluster mirrors this module's five screens: review the cluster's own identity and branding (§3.3), see and lightly maintain its business units and their staff, invite and manage the cluster's users, and check — read-only — how much of what was purchased is left. It is a licence-position and light-roster console, not a purchasing or platform-configuration surface: nothing in this module can create a business unit, edit a licence, or touch anything outside the one cluster in the URL.

## 3. Key Concepts

### 3.1 `adminScope` and `isClusterAdminOf` — resolved once, cached client-side

`AuthContext` fetches `GET /api-system/me/admin-clusters` once per session (`fetchAdminScope`, `AuthContext.tsx:98-107`) into `adminScope: { all: boolean; clusters: AdminCluster[] }`, cached in `localStorage` under `adminScope`. `all` short-circuits every subsequent check — it is set only for a platform super admin, per `clusterAdminService.getMyAdminClusters`'s own comment: "a super admin administers everything, so `clusters` is only a searchable page" (`../carmen-platform/src/services/clusterAdminService.ts:14-17`). `isClusterAdminOf(clusterId)` (`AuthContext.tsx:274-275`) is simply `adminScope.all || adminScope.clusters.some(c => c.id === clusterId)` — a synchronous, cached read, not a fresh request per navigation.

### 3.2 `ClusterAdminRoute` — the gate, in the order it actually runs

`ClusterAdminRoute` (`../carmen-platform/src/components/ClusterAdminRoute.tsx:20-59`) checks, in this exact order:

1. **Authenticated** — unauthenticated callers redirect to `/login`.
2. **`adminScope` loaded** — a `null` scope (not yet fetched) shows a loading state rather than deciding early.
3. **`!clusterId || !isClusterAdminOf(clusterId)` → renders `<Forbidden />`, in place.** This is the load-bearing check, and it is a membership test, not a permission string.
4. **Only then, the feature flag**, when one is passed. The component's own comment states the ordering is deliberate and names the reason: "the feature gate comes last, same reasoning as `PrivateRoute`: scope answers before the flag" (lines 42-43) — the identical ordering rule [RBAC — Permissions](/en/platform/rbac/permissions) documents for the platform-side guard.

The honest description of step 3, used consistently across every page in this module: **no RBAC permission key — gated instead by cluster membership via `isClusterAdminOf`.** This is not an absence of a check. A non-member is stopped cold, before the feature flag is even consulted — see [Permissions](/en/platform/cluster-admin/permissions) for the full gate matrix and why this matters for testing.

`ClusterAdminRoute`'s own comment is explicit that this is "navigation, not security": the real enforcement is server-side, and it happens independently, on every request, not once at route-entry. `../carmen-turborepo-backend-v2`'s `ClusterAdminAuthzService.isClusterAdmin(userId, clusterId)` (`apps/micro-cluster/src/common/cluster-admin-authz.service.ts:46-63`) mirrors the frontend check field-for-field — an active, non-deleted `tb_cluster_user` row with `role: 'admin'` for that cluster, or platform super-admin status — and every mutating call this module's screens make (cluster updates, business-unit updates, invitation create/resend/revoke) calls it independently before writing. A cached, stale `adminScope` on the client (say, from a membership revoked mid-session) cannot itself force a write through; the backend re-checks every time. The same "self-scope, no permission decorator" design extends to the read side too: the backend's own permission-coverage exception list documents `GET api-system/me/admin-clusters` as deliberately ungated because "the service filters by the caller's own `user_id`, returning only the clusters they themselves administer" (`packages/prisma-shared-schema-platform/prisma/check.api-system-permission-coverage.ts`, the `admin-clusters` entry) — the same self-scoping reasoning as the frontend gate, applied on the one backend endpoint this module's entry screen depends on.

Wrapping this in one Fragment also fixes a React Router quirk worth knowing for testing: `ClusterAdminRoute` wraps its children in `<React.Fragment key={clusterId}>` (line 58) specifically to force a full remount when `clusterId` changes — without it, a browser's long-press Back/Forward history jump straight from one administered cluster's page to another's could leave state captured from the previous cluster on screen, since React Router reuses a component instance when only a route param differs.

### 3.3 The nav has no permission filtering — reachability is the whole check

`buildClusterAdminNav(clusterId, flagOf)` (`clusterAdminNav.ts:10-27`) filters its four items by feature-flag state only (`hide` removes the row, `inactive` marks it `comingSoon`) — there is no `permission` field on any `NavItem` it returns, and its own comment states the reason plainly: "No permission filtering: reaching this navigation already required clearing `ClusterAdminRoute`" (lines 7-8). The four feature keys — `cluster_admin_cluster`, `cluster_admin_business_units`, `cluster_admin_licenses`, `cluster_admin_users` — share menu labels with platform-side rows (Cluster, Business Units, Licenses, Users) but are a **separate namespace**; flipping a platform feature flag has no effect here, and vice versa. A reader who assumes the platform-side keys (`clusters`, `business_units`, `licenses`, `users`) apply to this console will be testing the wrong flag.

### 3.4 Two finite pools, read-only everywhere in this console

Every screen that shows capacity — `ClusterProfile`, `ClusterAdminLicenses`, and the `BuPropertyPlate` hero on `BusinessUnitForm` — draws the same two numbers: the cluster's **BU quota** (how many business units it may create, from `bu_cap`/`bu_used` on the cluster record, ultimately `v_cluster_bu_cap`) and its **seat pool** (`total_max_license_users`/`users_count`, cluster-wide, not per-BU). Both reuse the platform's own capacity math and colour scale (`utils/capacity`), so a "warn" or "over" level means the same thing here as on the platform-side gauges documented in [Licenses — Data Model](/en/platform/licenses/data-model) §3. Nothing in this console can purchase, edit, or cancel either pool — see §4 and [UI Screens](/en/platform/cluster-admin/ui-screens) §7 for the read-only `ClusterAdminLicenses` screen, and [Licenses](/en/platform/licenses) §4 for where those numbers actually get written.

### 3.5 Membership vs. RBAC — two axes that never intersect

A user account can independently be: a platform admin with RBAC grants (reaches the platform sidebar, subject to [RBAC](/en/platform/rbac)'s permission keys), a cluster admin via `tb_cluster_user` membership (reaches this console for whichever clusters they administer), both at once, or neither. Nothing in either system checks the other. The most common real-world case for this console is the second one alone — a customer's own staff member with no Carmen platform role at all.

### 3.6 `ClusterAccessLost` — membership revoked mid-session

`ClusterAdminRoute` decides once, at mount. If a cluster admin's membership is revoked while a page under `/cluster-admin/:clusterId/*` is already open, the route guard cannot catch it — the next API call the open page makes simply 403s. `ClusterProfile`, `BusinessUnitList`, `BusinessUnitForm`, and `ClusterUsers` each catch that 403 individually and render `ClusterAccessLost` (`../carmen-platform/src/pages/clusterAdmin/ClusterAccessLost.tsx`) — an `EmptyState` with a "Back to my clusters" button — in place of the page body, rather than crashing or showing a raw error. `ClusterAdminLicenses` does **not** implement this same catch (see [UI Screens](/en/platform/cluster-admin/ui-screens) §7 and [Permissions](/en/platform/cluster-admin/permissions) §4, edge case 9).

## 4. Roles and Personas

| Route | Guard | Membership check | Feature key | Notes |
|---|---|---|---|---|
| `/cluster-admin` | `AuthedRoute` | None yet — resolved inside `ClusterAdminEntry` from `adminScope` | — | Authentication only; see §1 |
| `/cluster-admin/:clusterId/cluster` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_cluster` | [UI Screens](/en/platform/cluster-admin/ui-screens) §3 |
| `/cluster-admin/:clusterId/business-units` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_business_units` | [UI Screens](/en/platform/cluster-admin/ui-screens) §4 |
| `/cluster-admin/:clusterId/business-units/:buId/edit` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_business_units` | [UI Screens](/en/platform/cluster-admin/ui-screens) §5 |
| `/cluster-admin/:clusterId/users` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_users` | [UI Screens](/en/platform/cluster-admin/ui-screens) §6 |
| `/cluster-admin/:clusterId/licenses` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_licenses` | [UI Screens](/en/platform/cluster-admin/ui-screens) §7 |
| `/cluster-admin/:clusterId/profile` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | **None passed** — no feature gate on this one route | Shared component; see §4.1 |

Every membership-gated row in this table is the same fact stated once: **no RBAC permission key — gated instead by cluster membership via `isClusterAdminOf`.**

### 4.1 `/cluster-admin/:clusterId/profile` is the platform `/profile` page, in this shell

`Profile.tsx` is one component mounted at two routes; the [Profile](/en/platform/profile) page documents both mountings in full (§1.1's chrome-comparison table) and this page agrees with that account rather than restating it: same data, same fields, same validation, same `PATCH /api/user/profile` — only the `Shell` (`Layout` vs. `ClusterAdminLayout`), the brand identity, and the header's `ClusterSwitcher` differ. The one route-guard nuance worth restating here: this is the single per-cluster route that passes `ClusterAdminRoute` no `feature` prop at all (`App.tsx:603-604`), so it has no feature-flag gate whatsoever — membership is the entire check.

### 4.2 A session can be redirected here from the platform shell entirely

[Dashboard](/en/platform/dashboard) §5 and [Profile](/en/platform/profile) §4 both document a `PrivateRoute` branch that activates before any permission check: a session with `hasClusterAdminScope` (administers at least one cluster) but no resolved platform authority is redirected to `/cluster-admin` rather than shown a 403 (`PrivateRoute.tsx:60-81`). This is the same reasoning `AuthedRoute`'s own comment gives for why `/cluster-admin` itself cannot use `PrivateRoute` (§1) — the redirect would otherwise loop. In practice this means a membership-only cluster admin who types `/dashboard` or `/profile` directly lands here instead, without ever seeing a Forbidden page.

## 5. Related Modules

- [Clusters](/en/platform/clusters) — `ClusterProfile` is a narrower, read-scoped mirror of `ClusterEdit`; see [UI Screens](/en/platform/cluster-admin/ui-screens) §3 for the contrast.
- [Business Units](/en/platform/business-units) — `BusinessUnitList`/`BusinessUnitForm` are cluster-scoped, edit-only mirrors of `BusinessUnitManagement`/`BusinessUnitEdit`; see [UI Screens](/en/platform/cluster-admin/ui-screens) §4–5.
- [Users](/en/platform/users) — an entirely different data model: this module's Users screen manages `tb_cluster_user` membership and cluster invitations, not the `tb_user` platform account records the Users module owns; see [UI Screens](/en/platform/cluster-admin/ui-screens) §6.
- [Licenses](/en/platform/licenses) — already documents this module's read-only licence screen from its own side (§4, §5) and states the identical gate description used here; `ClusterAdminLicenses` reuses that module's own hooks (`useLicenseLedger`, `useClusterSeatLicenses`) and services.
- [RBAC](/en/platform/rbac) — owns the permission axis this entire module deliberately sits outside of (§3.5).
- [Profile](/en/platform/profile) — owns the full account of the shared `Profile` component this module mounts a second time (§4.1).
- [Dashboard](/en/platform/dashboard) — documents the `PrivateRoute` redirect mechanism that can land a session here without it ever requesting `/cluster-admin` directly (§4.2).

## 6. Reference Sources

All paths `../carmen-platform` (HEAD `157a65e`, 2026-09-04) unless prefixed `../carmen-turborepo-backend-v2` (HEAD `937cf5ac4`, 2026-09-06).

- `src/App.tsx:578-605` — the six `/cluster-admin*` routes and their guards/feature props.
- `src/components/AuthedRoute.tsx` — the authentication-only entry guard and why it exists.
- `src/components/ClusterAdminRoute.tsx` — the per-cluster gate (§3.2).
- `src/components/ClusterAdminLayout.tsx`, `src/components/ClusterSwitcher.tsx` — the shell chrome.
- `src/components/nav/clusterAdminNav.ts` — the four-item, permission-free nav (§3.3).
- `src/components/PrivateRoute.tsx:38-104` — the platform-side guard, including the redirect branch described in §4.2.
- `src/context/AuthContext.tsx` — `adminScope`, `fetchAdminScope`, `isClusterAdminOf`, `hasClusterAdminScope`.
- `src/services/clusterAdminService.ts` — `getMyAdminClusters`, invitation CRUD.
- `src/pages/clusterAdmin/ClusterAdminEntry.tsx` — the `/cluster-admin` landing screen.
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/common/cluster-admin-authz.service.ts:46-63` — `ClusterAdminAuthzService.isClusterAdmin`, the backend mirror of `isClusterAdminOf`.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_me-admin-clusters/platform_me-admin-clusters.controller.ts` and `packages/prisma-shared-schema-platform/prisma/check.api-system-permission-coverage.ts` — the deliberately ungated `GET api-system/me/admin-clusters` endpoint and its documented exception.

## 7. Pages in This Module

- [UI Screens](/en/platform/cluster-admin/ui-screens) — all six screens (`ClusterAdminEntry`, `ClusterProfile`, `BusinessUnitList`, `BusinessUnitForm`, `ClusterUsers`, `ClusterAdminLicenses`) plus the shared `Profile` mounting, each contrasted with its platform-side twin.
- [Permissions](/en/platform/cluster-admin/permissions) — the full gate matrix, the design reasoning for having no RBAC key, and edge cases for testers.
