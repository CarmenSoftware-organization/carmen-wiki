---
title: Platform RBAC — Permissions
description: Route-guard matrix for the whole SPA, how route/sidebar/in-page gates compose, the permission-resolution algorithm, and edge cases for testers. Updated for the platform_role.* key rename, the category-permissions route move, and the cluster-admin login exception.
published: true
date: 2026-09-06T13:00:00.000Z
tags: book/platform, rbac, permissions
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Platform RBAC — Permissions

> **At a Glance**
> **Gate:** every guarded route carries `requiredPermission="resource.action"` (or `requireSuperAdmin`) plus, since the last sync, an optional `feature="<key>"` prop on `PrivateRoute` &nbsp;·&nbsp; **Resolution order (`hasPermission`, used by every gate):** bootstrap → super-admin → platform keys → cluster keys — unchanged since the last sync &nbsp;·&nbsp; **Bootstrap exception:** total user count 0 or 1 ⇒ login skips the ≥1-permission gate and `hasPermission` returns `true` &nbsp;·&nbsp; **Login also admits a cluster-admin-only session** (no platform permission at all) outside bootstrap — a separate `login()`-time OR-branch, distinct from `hasPermission` (see §4) &nbsp;·&nbsp; **On failure:** the `Forbidden` page (`src/pages/Forbidden.tsx`) renders in place inside `<Layout>` (sidebar stays visible, URL unchanged); a direct `/403` route also renders it &nbsp;·&nbsp; **In-page gates:** `<Can>` wraps Add/Edit/Delete on most management list and edit pages (`.create`/`.update`/`.delete` keys, cluster-scoped for Clusters/Business Units); the Roles list/edit gate Add/Edit/Delete with `platform_role.*` keys (renamed from `role.*` on 2026-08-20), and the User Platform detail page gates on `user_platform.manage` &nbsp;·&nbsp; **Permission Catalog's route carries no key at all** — see §2.1

## 1. Overview

This page is the canonical map of how permission keys gate the Platform SPA. Authorization happens at three layers that share one resolver: the **route guard** (`PrivateRoute`'s `requiredPermission` / `requireSuperAdmin` props, plus an optional `feature` prop checked last — see §3), the **sidebar filter** (`buildPlatformNav()` in `src/components/nav/platformNav.ts` hides nav items whose `permission` the session lacks — `Layout.tsx` itself only calls that function, it no longer defines the nav array), and **in-page gates** (`<Can permission="...">` wrapping individual buttons and forms). All three call `AuthContext.hasPermission`, which delegates to the pure `checkPermission` function over the session's `EffectivePermissions` snapshot.

The same `platformNav.ts` file also derives `NAV_RESOURCE_ORDER` (a list of permission resources in first-appearance menu order) and exports `resourceRank()`, which ranks a resource by its position in that order — a resource with no menu row of its own sorts after every menu-backed resource and keeps catalog order among itself. **`resourceRank()`'s own doc comment gives `rbac` and `license` as its examples of such resources — `rbac` is stale**: that resource was retired along with the `role.*`→`platform_role.*` rename (§1), and `platform_role` now has its own **Platform Roles** menu row, so it is *not* in the unranked tail — it ranks by that row's position (right after Applications). Checking every `permission`/`requiredPermission`/`hasPermission()` call site in the SPA against the nav's own list, the resources genuinely left with no menu row today are **`activity_log`** (the cross-cutting "View History" gate on Clusters/Business Units/Users) and **`license`** (an in-page key inside the Licenses module, distinct from that module's nav-level `subscription.*` keys) — neither is part of this module. `RoleEdit`'s permission grid (§ [UI Screens](/en/platform/rbac/ui-screens)) sorts by this rank, which is why a role's permission list reads top-to-bottom in the same order as the sidebar the reader just came from.

Two routes are authenticated-only with no key requirement: `/dashboard` and `/profile`. Any session that passes login reaches them. Everything else carries a key — and because the login gate itself requires the account to hold at least one permission (or the super-admin flag, or the bootstrap exception), a session cannot be admitted with zero permissions at login time outside bootstrap. The ≥1-permission gate runs only inside `login()`, though: a session whose grants are revoked mid-session stays signed in even after the snapshot refetch — it just fails every subsequent permission check.

## 2. Gate matrix

### 2.1 RBAC module screens

| Route | Component | Guard | In-page gates |
|---|---|---|---|
| `/platform/roles` | `RoleManagement` | `platform_role.read` (`feature="platform_roles"`) | row **Edit** gated `<Can permission="platform_role.update">`, row **Delete** gated `<Can permission="platform_role.delete">`. **Add Role** (header button and the empty-state CTA) gated `<Can permission="platform_role.create">`. Export remains ungated |
| `/platform/roles/new` | `RoleEdit` | `platform_role.create` (`feature="platform_roles"`) | None |
| `/platform/roles/:id/edit` | `RoleEdit` | `platform_role.update` (`feature="platform_roles"`) | The header **Edit** button is `<Can permission="platform_role.update">` |
| `/platform/category-permissions` | `PermissionCatalog` | **None** — a bare `<PrivateRoute>` with no `requiredPermission`/`feature`; any authenticated platform user can open the route. The page's `GET /api-system/platform/permissions` call is itself enforced server-side on `platform_role.read` (`RequirePlatformPermission`), so a session lacking that key reaches the page but the catalog fetch 403s | None (read-only screen) |
| `/platform/super-admins` | `SuperAdminManagement` | `requireSuperAdmin` (`feature="super_admins"`) | None — only super admins ever reach the page |
| `/platform/user-platform` | `UserPlatformManagement` | `user_platform.read` (`feature="user_platform"`) | None |
| `/platform/user-platform/:userId` | `UserPlatformEdit` | `user_platform.read` | `<Can permission="user_platform.manage">` on Add Role, the add-role form, and per-row Remove |

**Renamed 2026-08-20** (`carmen-platform` commit `8df0b10`): every Roles key changed from `role.*` to `platform_role.*`, and the Permission Catalog's route moved from `/platform/permissions` (which no longer exists) to `/platform/category-permissions`. The Roles list's row Edit/Delete and Add Role have carried `<Can>` gates since 2026-06-10 (`role.*` originally, `platform_role.*` now) — the gating *pattern* is unchanged, only the key strings are. Whether a role delete actually succeeds is still up to the backend's own enforcement of `platform_role.delete` (see §5) — the in-page gate is advisory, as everywhere else.

### 2.2 Rest of the SPA

| Route prefix | Guard (list / new / edit) | Gotcha |
|---|---|---|
| `/dashboard`, `/profile` | authenticated only — no key | |
| `/clusters` | `cluster.read` / `cluster.create` / `cluster.update` | |
| `/business-units` | `cluster.read` / `cluster.create` / `cluster.update` | **Reuses `cluster.*` keys** — there are no `business_unit.*` keys; granting cluster access also grants Business Units, and the two cannot be separated |
| `/tenant-migrations` | `cluster.read` | Standalone fleet-wide migration overview; also reuses `cluster.*` — documented as [Business Units — Tenant Migrations](/en/platform/business-units/tenant-migrations), a sub-page of Business Units rather than a top-level module of its own |
| `/users` | `user.read` / `user.create` / `user.update` | Distinct from `user_platform.*`, which gates role assignment, not user CRUD |
| `/applications` | `application.read` / `application.create` / `application.update` | |
| `/report-templates` | `report_template.read` / `report_template.create` / `report_template.update` | |
| `/report-form-groups` | `report_template.read` (mutations via `report_template.update`/`.create`) | New 2026-07-23; reuses Report Templates' keys, no new ones |
| `/news` | `news.read` / `news.create` / `news.update` | |
| `/broadcasts/new` | `broadcast.send` | Single route; no list page |
| `/sql-workbench` | `sql_workbench.read` | Documented as [SQL Workbench](/en/platform/sql-workbench), one of the book's standalone pages (not a sub-page of another module) |

**Removed 2026-07-23/24:** `/print-template-mapping*` and its `print_template_mapping.*` keys no longer exist — the module was deleted from carmen-platform on 2026-07-24 (commit `de11377`) and the permission-catalog rows it used were dropped the day before from carmen-turborepo-backend-v2's seed (commit `c135bb21e`, 2026-07-23); `template_type` plus the [Report Templates — Form Groups](/en/platform/report-templates/form-groups) screen now serve the same need.

Three routes are fully public (no `PrivateRoute` at all): `/` (landing), `/login`, and `/changelog`. Source: `../carmen-platform/src/App.tsx` (the full `<Routes>` block). No route anywhere in the SPA passes a `.delete` key as `requiredPermission` — delete actions live inside list pages, where every management list gates them in-page with `<Can permission="*.delete">` (§3), **now including Roles** (§2.1) — the previous sync's "only the Roles list still exposes Delete to anyone holding its `.read` guard" is stale.

## 3. How guards compose

A user's path to any action passes up to three gates, outermost first:

1. **Route guard** — `PrivateRoute` (`src/components/PrivateRoute.tsx`, 40 lines). If the session is unauthenticated it renders `<Navigate to="/login" replace />`. If `requiredPermission` is set and `hasPermission(requiredPermission)` is false — or `requireSuperAdmin` is set and `isSuperAdmin` is false — it renders `<Forbidden />` **in place** (a dedicated page, `src/pages/Forbidden.tsx` — renamed from an inline `AccessDenied` component that used to live inside this same file), preserving the URL so its "Go Back" action can't bounce off the guard. `Forbidden` renders inside the normal `<Layout>` shell: a `ShieldX` icon, "403" code, "Access Denied" heading, "You don't have permission to access this page.", and two actions — "Go Back" (falls back to `/dashboard` when there's no sensible back target) and "Go to Dashboard". The sidebar stays visible and the session stays valid. A direct `/403` route renders the same `Forbidden` page.
2. **Sidebar filter** — `ALL_PLATFORM_NAV_ITEMS` in `src/components/nav/platformNav.ts` (`Layout.tsx` only calls `buildPlatformNav()`, it no longer declares the array itself) lists each entry's `permission: '<key>'` or `superAdminOnly: true`, then `buildPlatformNav()` filters: an item survives only when `(!item.permission || hasPermission(item.permission)) && (!item.superAdminOnly || isSuperAdmin)` and its `feature` flag is not `hide`. Hidden items are still directly addressable by URL — the route guard is the real barrier; the sidebar is UX. The sidebar keys match the route keys one-for-one for the list routes (`platform_role.read`, `user_platform.read`, `cluster.read`, etc.), so there is no divergence where a visible entry leads to `Forbidden`. The Permission Catalog has no sidebar entry at all.
3. **In-page gate** — `<Can permission="..." clusterId?>` (`src/components/Can.tsx`) renders its children only when `hasPermission` passes, with an optional `fallback` (default: nothing). `<Can>` gates Add/Edit/Delete across most of the SPA's management pages: the list pages (Clusters, Business Units, Users, Applications, Report Templates, News) wrap their Add button in the `.create` key, row Edit in `.update`, and row Delete in `.delete`; the corresponding edit pages wrap their Edit toggle in `.update` (without it the detail view stays read-only, so Save is unreachable — Save itself is not wrapped, and edit pages have no `<Can>`-gated delete); and BroadcastCompose wraps Send in `broadcast.send`. The Clusters and Business Units gates pass a `clusterId` (e.g. `<Can permission="cluster.update" clusterId={row.original.id}>`), taking the cluster-specific resolution branch (§4) — the only call sites that do. Within the RBAC module's own screens, the Roles list and Role editor gate Add/Edit/Delete and the Edit toggle with `platform_role.*` keys (renamed from `role.*` on 2026-08-20 — the gating pattern itself is unchanged); the User Platform detail page uses `<Can>` for `user_platform.manage` (Add Role, the add-role form, per-row Remove); Permission Catalog, Super Admins, and User Platform list remain fully ungated in-page (their route guards are the only barrier — and Permission Catalog's route guard is itself absent, see §2.1).

All three layers call the same `hasPermission(key, opts?)` from `AuthContext` — there is exactly one resolution algorithm (§4), so route, sidebar, and in-page outcomes can never disagree for the same key. Note that route guards never pass a `clusterId`, so they take the broad "any cluster grants it" branch: a role scoped to a single cluster still opens the corresponding screens platform-wide in the current SPA, and the cluster-scoped narrowing matters for `<Can clusterId>` call sites and backend enforcement.

## 4. Permission resolution walkthrough

The full resolution path, from login to a single check (sources: `AuthContext.tsx` `login`/`hasPermission`, `utils/permissions.ts` `checkPermission`):

```
on login(credentials):
    token = POST /api/auth/login                       # unwrap { data: { access_token } }
    store token; set Authorization header

    # Fetched in parallel (Promise.all)
    eff   = GET /api/user/permission/platform          # EffectivePermissions
    count = GET /api-system/user?page=1&perpage=1      # read paginate.total
    scope = fetchAdminScope()                          # cluster-admin membership, if any

    hasAnyPermission = eff exists and (
        eff.is_super_admin
        or eff.platform is non-empty
        or eff.clusters has any key
    )
    # A cluster-admin membership is authority in its own right, independent of every
    # platform permission check above — added after the cluster-admin persona shipped.
    # Without it, a user whose only authority is that membership cannot log in at all.
    hasClusterAdmin = scope exists and (scope.all or scope.clusters is non-empty)
    isBootstrap = count is not null and count <= 1     # first-admin escape hatch

    if not hasAnyPermission and not hasClusterAdmin and not isBootstrap:
        tear down the partial session (drop token, permissions, header)
        return "Access Denied. You are not authorized to access this platform."

    persist session; cache eff in localStorage["effectivePermissions"]


function hasPermission(key, opts?):                    # AuthContext — used by ALL gates
    # 1. Bootstrap escape hatch: 0-1 users => allow everything
    if userCount is not null and userCount <= 1:
        return true
    return checkPermission(effectivePermissions, key, opts)


function checkPermission(eff, key, opts?):             # pure function, utils/permissions.ts
    if eff is null:
        return false
    # 2. Super-admin bypass — checked before any key list
    if eff.is_super_admin:
        return true
    # 3. Platform-scoped grant applies everywhere
    if key in eff.platform:
        return true
    # 4a. Cluster-specific check: only that cluster's grants count
    if opts.clusterId is set:
        return key in eff.clusters[opts.clusterId]
    # 4b. Broad check (no clusterId): any cluster granting the key passes
    return any cluster_keys in eff.clusters where key in cluster_keys
```

The `EffectivePermissions` snapshot is fetched at login and again on every `AuthProvider` mount (page refresh), with the `localStorage` copy used as the initial value while the refetch is in flight. `userCount` is `null` until its fetch resolves; the bootstrap branch requires a non-null count, so during the loading window checks are enforced strictly.

**The `hasClusterAdmin` branch only decides whether `login()` admits the session — it changes nothing about `hasPermission`/`checkPermission` above**, which is what every route/sidebar/`<Can>` gate actually calls. A cluster-admin-only session that logs in this way holds zero platform permissions, so every `hasPermission(key)` call still returns `false` for it (outside bootstrap); `PrivateRoute` separately resolves this case *before* its own permission check and redirects such a session to `/cluster-admin` rather than rendering `Forbidden` on every platform route (`src/components/PrivateRoute.tsx`: if `hasPlatformAuthority` is false and `hasClusterAdminScope` is true, `<Navigate to="/cluster-admin" replace />`). This module's own screens are unaffected in practice — none of them are reachable via cluster-scoped admin authority, only via a `platform_role.*`/`user_platform.*`/super-admin grant.

## 5. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | Bootstrap login — platform has 0 or 1 total users | `login()` admits a session with zero permissions; every `hasPermission` returns `true`, so all routes, sidebar entries, and `<Can>` blocks open | The intended first-admin path: sign in, create roles, assign them. Dormant as soon as a second user row exists; an in-flight session does not re-check the count until refresh/login |
| 2 | `userCount` still `null` (count fetch pending or failed) | Bootstrap branch does not fire; checks run strictly against the permission snapshot | A failed count fetch fails closed, not open |
| 3 | Super admin session | `is_super_admin` short-circuits before any key list — even with empty `platform`/`clusters` everything passes | Never QA key coverage from a super-admin session; it cannot reveal missing grants. Test with a role-built session instead |
| 4 | `user_platform.read` without `user_platform.manage` | List and detail pages load; the Roles & Scope card is read-only — Add Role, the add-role form, and Remove buttons do not render | The canonical `<Can>` test case; verify the buttons are absent, not merely disabled |
| 5 | `platform_role.read` without `platform_role.delete` | The Delete item in the Roles list dropdown is `<Can permission="platform_role.delete">`-gated (key renamed from `role.delete` on 2026-08-20) and does not render for a session lacking it | Verify the Delete item is absent, not merely disabled — mirrors edge case 4's `<Can>` test pattern. Backend enforcement of `platform_role.delete` remains the real boundary regardless |
| 6 | Permission revoked mid-session | The cached `effectivePermissions` snapshot keeps granting until the next login or `AuthProvider` mount refetches | Backend enforcement is the real boundary; the SPA snapshot is advisory between refreshes |
| 7 | New permission key needed | The catalog is read-only in the SPA — new `resource.action` rows arrive only via backend seed/migration and redeploy | A feature branch adding a guarded route must coordinate a backend catalog change; the key will not exist until then |
| 8 | Cluster-scoped role and platform-wide routes | Route guards check without `clusterId`, so any single cluster grant opens the corresponding screens globally | Scoping narrows `<Can clusterId>` call sites and backend data filtering, not SPA route access |
| 9 | **Removed 2026-08-06** (`carmen-platform` commit `19d90c4`) — dev builds no longer get a mock permission set | `DEV_MOCK_EFFECTIVE_PERMISSIONS` (all 31 platform keys, substituted whenever the backend returned none in `import.meta.env.DEV`) was deleted outright — it happened to match a membership-only cluster admin's permission shape exactly, so that boundary was invisible in local development and could not be verified in a browser. A dev instance pointed at an unseeded backend can no longer sign in at all; DEV has shipped 31 seeded permissions and 5 seeded roles for some time | Do not write test plans or setup docs referencing a dev-mode permission mock — none exists. The bootstrap hatch (`userCount <= 1`) is the only escape valve for a genuinely fresh install |
| 10 | Granting cluster access | `cluster.*` keys also open `/business-units*` — there are no separate `business_unit.*` keys | Include Business Units screens in any cluster-permission test plan |

## 6. Recommendations

- **Test per key, not per persona.** Build one QA role per permission key (or small key set) and verify the route, sidebar entry, and in-page affordances toggle together — they share one resolver, so a divergence indicates a hardcoded gate.
- **Keep a non-super-admin QA account.** Edge case 3 makes super-admin sessions useless for verifying grants; reserve the flag for testing the bypass itself and the `/platform/super-admins` screen.
- **Treat SPA gates as advisory.** Every mutation the SPA hides behind a key (`user_platform.manage`, `platform_role.update`/`.delete`, and the rest) must be re-verified against the backend with a token lacking that key — client-side gating alone is not a security boundary.
- **When adding a guarded feature**, register all three layers together: the catalog row (backend), the `requiredPermission` on the route, and the sidebar `permission` field — plus `<Can>` for any action narrower than the route's key. Follow the `resource.action` naming of the existing catalog.
- **Decide deliberately about `business_unit.*`.** If Business Units ever needs independent gating, new keys plus route/sidebar updates are required; until then, document the `cluster.*` reuse in test plans rather than treating it as a bug.

**Stale e2e, not evidence:** `../carmen-platform-e2e/tests/permission-catalog/permission-catalog.spec.ts` navigates to `/platform/permissions`, a route that no longer exists (moved to `/platform/category-permissions` on 2026-08-20) — every test in that spec is broken against current source. `../carmen-platform-e2e/tests/roles/role-crud.spec.ts` (and its `pages/RoleEditPage.ts` page object) drives the permission picker as a **checkbox** ("toggle the `cluster.read` permission checkbox", "confirm the checkbox is checked") — the current `PermissionGrid` (2026-08-20, `carmen-platform` commit `42eeafe`) uses `aria-pressed` toggle `<button>`s, not checkbox inputs, so those selectors no longer match. `pages/RoleManagementPage.ts`'s own doc comment ("The Name cell is a `<button>`... not a link") also contradicts current source, where the Name cell renders as a `<Link>`. All three e2e files are dated `bb8f671` (2026-06-11), predating every change on this page. Per the resync ruling, the implementation wins; these suites need maintenance out of scope for this sync.

**References:** `../carmen-platform/src/App.tsx` (route guards) · `src/components/PrivateRoute.tsx` (guard) · `src/pages/Forbidden.tsx` (the 403 page) · `src/components/nav/platformNav.ts` (sidebar array, `buildPlatformNav()`, `NAV_RESOURCE_ORDER`/`resourceRank()`) · `src/components/Can.tsx` · `src/context/AuthContext.tsx` (`login`, `hasPermission`, `hasPlatformAuthority`, `hasClusterAdminScope`) · `src/utils/permissions.ts` (`checkPermission`, `checkPlatformAuthority`) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-permissions/platform-permissions.controller.ts` (`platform_role.read` enforcement on the catalog endpoint).
**Cross-links:** [Platform RBAC landing](/en/platform/rbac) &nbsp;·&nbsp; [Data Model](/en/platform/rbac/data-model) &nbsp;·&nbsp; [UI Screens](/en/platform/rbac/ui-screens)
