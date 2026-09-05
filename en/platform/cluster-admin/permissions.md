---
title: Cluster Admin — Permissions
description: No RBAC permission key anywhere in this module — gated instead by cluster membership via isClusterAdminOf, checked before the feature flag on every route, and re-enforced independently by the backend on every write.
published: true
date: '2026-09-06T11:00:00.000Z'
tags: book/platform, cluster-admin, permissions
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Cluster Admin — Permissions

> **At a Glance**
> **No RBAC permission key anywhere in this module.** Every per-cluster route is gated instead by cluster membership via `isClusterAdminOf`, checked before the feature flag &nbsp;·&nbsp; **`/cluster-admin` itself** carries only an authentication check (`AuthedRoute`) — membership is resolved afterward, inside `ClusterAdminEntry` &nbsp;·&nbsp; **The nav applies no permission filtering at all** — `clusterAdminNav.ts` filters by feature flag only; reaching the nav already required clearing the route guard &nbsp;·&nbsp; **In-page writes are gated the same way** — `ClusterProfile`'s edit toggle and `BusinessUnitForm`'s `canEdit` are both computed from route reachability alone, with no permission or role check inside the component &nbsp;·&nbsp; **The backend independently re-checks membership on every write** — `ClusterAdminAuthzService.isClusterAdmin` mirrors the frontend check and is called before every mutation this module's screens make &nbsp;·&nbsp; **Not an absence of a check** — membership is a real, enforced gate; do not describe this module as "unguarded" or "no permission check at all" &nbsp;·&nbsp; **No e2e suite** — every claim below is sourced from `../carmen-platform` and, for the backend mirror, `../carmen-turborepo-backend-v2` implementation directly

## 1. Overview

This module sits entirely outside the RBAC permission model [RBAC](/en/platform/rbac) documents for the rest of the Platform admin product. There is no `cluster_admin.*` (or any other) permission key checked anywhere in `src/pages/clusterAdmin/` or on any of its six routes — confirmed by a repo-wide grep of the directory for `hasPermission`/`requiredPermission`/`<Can permission=`, which returns nothing. The axis this module checks instead is **cluster membership**: an active, non-deleted `tb_cluster_user` row with `role: 'admin'` for the specific cluster named in the URL.

The correct, precise description — used consistently across every page in this module, per this plan's own ruling — is: **no RBAC permission key — gated instead by cluster membership via `isClusterAdminOf`.** This is deliberately not the same statement as "no permission check at all," "unguarded," or "gated only by the feature flag." Those three phrasings have each already appeared, incorrectly, on a different module's page in this plan (most recently [Licenses](/en/platform/licenses/permissions), corrected in a fix round) — each reads as though any authenticated user could open any cluster's screens once the flag is on, which is false. Membership is the load-bearing gate, checked before the feature flag is even consulted (§2).

The one route that is a genuine exception to "membership-gated" is the entry point itself: `/cluster-admin` is wrapped in `AuthedRoute`, which checks authentication only (§2). Membership is not yet in scope there — `ClusterAdminEntry` reads the caller's own `adminScope` and shows a picker, an auto-redirect, or an empty state accordingly, none of which is a boundary decision the same way `ClusterAdminRoute`'s `<Forbidden />` is.

## 2. Gate matrix

All five per-cluster routes resolve through `ClusterAdminRoute`, which checks membership first (failure → `<Forbidden>`, in place, URL unchanged) and the `feature` flag strictly afterward (failure → `NotFound` on `hide`, `ComingSoon` on `inactive`) — the identical resolution order [RBAC — Permissions](/en/platform/rbac/permissions) documents for the platform-side `PrivateRoute`, restated for this module's own guard.

| Route | Guard | Membership check | Feature key | Source |
|---|---|---|---|---|
| `/cluster-admin` | `AuthedRoute` | None — resolved inside `ClusterAdminEntry` from `adminScope` | — | `../carmen-platform/src/App.tsx:578-581` |
| `/cluster-admin/:clusterId/cluster` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_cluster` | `App.tsx:582-585` |
| `/cluster-admin/:clusterId/business-units` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_business_units` | `App.tsx:586-589` |
| `/cluster-admin/:clusterId/business-units/:buId/edit` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_business_units` | `App.tsx:590-593` |
| `/cluster-admin/:clusterId/users` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_users` | `App.tsx:594-597` |
| `/cluster-admin/:clusterId/licenses` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | `cluster_admin_licenses` | `App.tsx:598-601` |
| `/cluster-admin/:clusterId/profile` | `ClusterAdminRoute` | `isClusterAdminOf(clusterId)` | **None passed at all** | `App.tsx:602-605` |

Sidebar nav (`buildClusterAdminNav`, `../carmen-platform/src/components/nav/clusterAdminNav.ts:10-27`): filters its four rows by feature-flag state only (`hide` removes the row entirely; `inactive` marks it `comingSoon`, still rendered). There is **no `permission` field on any `NavItem`** it returns — the function's own comment states the reason directly: "reaching this navigation already required clearing `ClusterAdminRoute`." A row disappearing from this sidebar therefore always means the feature flag is `hide`, never a missing permission grant.

In-page write actions, all gated by route reachability alone — no permission or role string checked inside any of these components:

| Surface | Write | Gate |
|---|---|---|
| `ClusterProfile` edit toggle (Pencil → Save/Cancel) | Update cluster identity/branding | `!accessLost` (i.e., the route already let the caller in) |
| `BusinessUnitForm` (whole document) | Update business unit fields | `canEdit = !accessLost`, `BusinessUnitForm.tsx` — the component's own comment states this is "identical permission scope: whoever can reach the route can edit," with any narrower scope explicitly deferred to a future spec |
| `BusinessUnitForm`'s People tab, `BusinessUnitUsersCard` | Add/edit/remove BU membership | Same `canEdit` as above — no `subscription.*`/`user.*`/`cluster.*` key involved, unlike the platform `BusinessUnitEdit`'s own Users tab, which ties the same shared component's `canEdit` to `cluster.update` |
| `ClusterUsers` — Members tab | Change cluster role, remove member | No permission string; `clusterService.updateClusterUser`/`deleteClusterUser` |
| `ClusterUsers` — Invitations tab | Create/resend/revoke invitation | No permission string; `clusterAdminService.createInvitation`/`resendInvitation`/`revokeInvitation` |
| `ClusterAdminLicenses` | — | **No write UI exists on this screen at all** — see [UI Screens](/en/platform/cluster-admin/ui-screens) §7 |
| `Profile` (`/cluster-admin/:clusterId/profile`) | Edit own identity, change own password | Same as the platform mounting — authentication plus cluster membership of the URL's cluster; no RBAC key (see [Profile](/en/platform/profile) §4) |

Backend enforcement, proven directly against source (`../carmen-turborepo-backend-v2`, HEAD `937cf5ac4`): `ClusterAdminAuthzService.isClusterAdmin(userId, clusterId)` (`apps/micro-cluster/src/common/cluster-admin-authz.service.ts:46-63`) — an active, non-deleted `tb_cluster_user` row with `role: enum_cluster_user_role.admin` for that cluster, or platform super-admin status — is called independently before every write this module's screens make: `apps/micro-cluster/src/cluster/cluster/cluster.service.ts` (cluster update, business-unit update paths, lines 1211/1275/1399/1404/1466) and `apps/micro-cluster/src/cluster/user-invitation/user-invitation.service.ts` (invitation create/resend/revoke, lines 390/563/636/699). None of these call sites checks any `tb_user_tb_platform_role` grant at all as an alternative path for a membership admin — membership is the entire backend authorization for this module's writes, matching the frontend's own gate exactly.

## 3. Why there is no permission key here — the design reasoning

`ClusterAdminRoute`'s own comment states this outright: the frontend check is "navigation, not security" — each request underneath still meets `isClusterAdmin` on the server independently, which is what makes deciding from the client's cached `adminScope` acceptable at the route layer. Two supporting facts, both verified against source rather than taken on the comment's word alone:

1. **The backend re-validates on every write, not once at login.** `ClusterAdminAuthzService.isClusterAdmin` is called fresh, per request, at every cluster/business-unit/invitation mutation site listed in §2 — a stale cached `adminScope` on the client (say, from a membership revoked after the page loaded) cannot itself push a write through; the server's own membership check would reject it independently.
2. **The one read this module's entry screen depends on is deliberately self-scoped, not permission-gated, on the backend side too.** `GET /api-system/me/admin-clusters` carries no `@RequirePlatformPermission` decorator; its own doc-comment states why — "the answer is derived from the caller's own memberships… which is fail-closed and returns an empty list — never another user's clusters — for an unprivileged caller" (`platform_me-admin-clusters.controller.ts`). The backend's own permission-coverage exception list records the identical reasoning for this specific route: "self-scope: the service filters by the caller's own `user_id`, returning only the clusters they themselves administer" (`packages/prisma-shared-schema-platform/prisma/check.api-system-permission-coverage.ts`, the `admin-clusters` entry).

This is the same "backend enforces independently of the frontend's key" shape [Licenses — Permissions](/en/platform/licenses/permissions) §3 documents for its own module's read/manage split — the difference here is that this module's UI never even attempts a gated write path in the first place (§2's `ClusterAdminLicenses` row): every licence mutation endpoint requires `subscription.manage`, a key membership alone can never grant, so the frontend simply never renders a control that would 403.

## 4. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | Authenticated caller with zero cluster-admin memberships deep-links to `/cluster-admin/<any-clusterId>/cluster` | `<Forbidden />` renders in place, before the `cluster_admin_cluster` feature flag is even consulted | Reproduce by typing the URL directly — the address bar keeps the blocked path, matching `PrivateRoute`'s own "Back must not trap the user" convention |
| 2 | Cluster admin of cluster A deep-links to cluster B's URL | Same as edge case 1 — `isClusterAdminOf` is per-cluster, not "administers something" | Confirms membership is checked against the specific `:clusterId` in the URL, not merely a boolean "is any kind of cluster admin" |
| 3 | Authenticated caller with zero administered clusters visits `/cluster-admin` itself | Not a 403 — `ClusterAdminEntry` renders its own `EmptyState` ("No clusters to administer"), since `AuthedRoute` only checks authentication | The distinction matters for testers: the entry route and the five per-cluster routes fail differently for the same underlying "administers nothing" condition |
| 4 | Membership revoked while a `ClusterProfile`/`BusinessUnitList`/`BusinessUnitForm`/`ClusterUsers` page is already open | The route guard already passed at mount and does not re-run; the page's next API call 403s and the page renders `ClusterAccessLost` in place of its body | Reproduce by revoking the membership row in another session/tab, then triggering a refetch (e.g. Save, or a background poll) on the already-open page |
| 5 | Same as edge case 4, but on `ClusterAdminLicenses` | **No `ClusterAccessLost` handling exists on this screen** — a grep of `ClusterAdminLicenses.tsx` finds only an `isNotFoundError` branch for a missing/deleted cluster, no 403-specific catch | A genuine gap relative to its four sibling screens, not a deliberate design choice stated anywhere in source — flag if reproduced, since the resulting on-screen state (a raw failed-fetch presentation rather than the shared "access lost, back to my clusters" empty state) has not been independently characterised here |
| 6 | Super admin (`adminScope.all = true`) visits any `/cluster-admin/:clusterId/*` route | `isClusterAdminOf` returns `true` unconditionally for every cluster id — every gate in this table passes | Never QA this module's membership gate from a super-admin session; it cannot reveal a missing `tb_cluster_user` row the way a genuine membership-only session can |
| 7 | A `cluster_admin_*` feature flag is set to `hide` for one of the five per-cluster routes, for a session that otherwise passes the membership check | The route renders `NotFound`, and the nav's own row disappears from the sidebar entirely (§2) | Membership always resolves first — a `NotFound` here still means "you're a member but this feature is off," not "you're not a member"; do not conflate the two when triaging a bug report |
| 8 | Same as edge case 7, but the flag is `inactive` rather than `hide` | The route renders `ComingSoon`; the nav row still renders, marked `comingSoon` | The nav and the route agree here — unlike `hide`, an `inactive` feature stays visible as a promise, not silently removed |
| 9 | A platform-authority session with `hasClusterAdminScope` true but unresolved platform permissions visits `/dashboard` or `/profile` directly | `PrivateRoute`'s own redirect branch (not this module's own guard) sends them to `/cluster-admin` before any permission check runs | Documented on [Dashboard](/en/platform/dashboard) §5 and [Profile](/en/platform/profile) §4; restated here because it is the one way a session can land in this module without navigating to `/cluster-admin` at all |
| 10 | A cluster admin adds/edits/removes a BU member on `BusinessUnitForm`'s People tab | Succeeds with no permission check beyond having reached the route — contrast directly with the platform `BusinessUnitEdit`'s own Users tab, where the identical `BusinessUnitUsersCard` component's `canEdit` is tied to `cluster.update` | The same component, two different gating rules depending on which shell renders it — do not assume a permission-based test written against the platform screen also validates this one |

## 5. Recommendations

- **Never test this module's access control by checking RBAC permission grants.** A real test session needs a `tb_cluster_user` row with `role: 'admin'` for the target cluster, not a `platform_role` assignment — the two axes are independent (see [Landing](/en/platform/cluster-admin) §3.5).
- **Test membership-loss mid-session on all five per-cluster screens**, and specifically confirm `ClusterAdminLicenses`'s gap (edge case 5) before assuming it behaves like its four siblings.
- **Do not describe this module's gate as an absence anywhere** — "no RBAC permission key — gated instead by cluster membership via `isClusterAdminOf`" is the one phrasing to use, in an At-a-Glance line, an edge-case table, or prose; three other modules in this plan have already gotten this wrong once each.
- **When this module eventually gets an e2e suite**, the membership-before-flag ordering (§2, edge cases 1/2/7) is the single highest-value case to encode first, since it is the one thing a reader cannot infer just from the nav's own feature-flag filtering.
- **Route reachability is not itself a permission model** — `ClusterProfile`/`BusinessUnitForm`'s `canEdit = !accessLost` (§2) means every cluster admin of a given cluster can write everything this module's screens expose for it; do not test for a finer-grained write permission that does not exist in source today.

**References:** all paths `../carmen-platform` (HEAD `157a65e`) unless noted. `src/App.tsx:578-605` (routes) · `src/components/{AuthedRoute,ClusterAdminRoute}.tsx` (guards) · `src/components/nav/clusterAdminNav.ts` (nav) · `src/context/AuthContext.tsx` (`isClusterAdminOf`, `adminScope`, `hasClusterAdminScope`) · `src/pages/clusterAdmin/{ClusterProfile,BusinessUnitForm,ClusterUsers,ClusterAdminLicenses}.tsx` (in-page gates) · `../carmen-turborepo-backend-v2/apps/micro-cluster/src/common/cluster-admin-authz.service.ts` (backend mirror, HEAD `937cf5ac4`) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_me-admin-clusters/platform_me-admin-clusters.controller.ts` and `packages/prisma-shared-schema-platform/prisma/check.api-system-permission-coverage.ts` (the deliberately ungated self-scope read).
**Cross-links:** [Cluster Admin landing](/en/platform/cluster-admin) &nbsp;·&nbsp; [UI Screens](/en/platform/cluster-admin/ui-screens) &nbsp;·&nbsp; [Platform RBAC — Permissions](/en/platform/rbac/permissions) &nbsp;·&nbsp; [Licenses — Permissions](/en/platform/licenses/permissions) &nbsp;·&nbsp; [Dashboard](/en/platform/dashboard) &nbsp;·&nbsp; [Profile](/en/platform/profile)
