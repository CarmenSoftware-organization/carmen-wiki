---
title: Platform RBAC — Permissions
description: Route-guard matrix for the whole SPA, how route/sidebar/in-page gates compose, the permission-resolution algorithm, and edge cases for testers.
published: true
date: 2026-06-10T12:00:00.000Z
tags: book/platform, rbac, permissions
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Platform RBAC — Permissions

> **At a Glance**
> **Gate:** every guarded route carries `requiredPermission="resource.action"` (or `requireSuperAdmin`) on `PrivateRoute` &nbsp;·&nbsp; **Resolution order:** bootstrap → super-admin → platform keys → cluster keys &nbsp;·&nbsp; **Bootstrap exception:** total user count 0 or 1 ⇒ login skips the ≥1-permission gate and `hasPermission` returns `true` &nbsp;·&nbsp; **On failure:** `<AccessDenied>` inside `<Layout>` (sidebar stays visible) &nbsp;·&nbsp; **In-page gates:** `<Can>` — currently only `user_platform.manage` on the User Platform detail page

## 1. Overview

This page is the canonical map of how permission keys gate the Platform SPA. Authorization happens at three layers that share one resolver: the **route guard** (`PrivateRoute`'s `requiredPermission` / `requireSuperAdmin` props), the **sidebar filter** (`Layout.tsx` hides nav items whose `permission` the session lacks), and **in-page gates** (`<Can permission="...">` wrapping individual buttons and forms). All three call `AuthContext.hasPermission`, which delegates to the pure `checkPermission` function over the session's `EffectivePermissions` snapshot.

Two routes are authenticated-only with no key requirement: `/dashboard` and `/profile`. Any session that passes login reaches them. Everything else carries a key — and because the login gate itself requires the account to hold at least one permission (or the super-admin flag, or the bootstrap exception), there is no such thing as a signed-in session with zero permissions outside bootstrap.

## 2. Gate matrix

### 2.1 RBAC module screens

| Route | Component | Guard | In-page gates |
|---|---|---|---|
| `/platform/roles` | `RoleManagement` | `role.read` | None — Add/Edit/Delete/Export visible to every holder of `role.read` |
| `/platform/roles/new` | `RoleEdit` | `role.create` | None |
| `/platform/roles/:id/edit` | `RoleEdit` | `role.update` | None |
| `/platform/permissions` | `PermissionCatalog` | `role.read` | None (read-only screen) |
| `/platform/super-admins` | `SuperAdminManagement` | `requireSuperAdmin` | None |
| `/platform/user-platform` | `UserPlatformManagement` | `user_platform.read` | None |
| `/platform/user-platform/:userId` | `UserPlatformEdit` | `user_platform.read` | `<Can permission="user_platform.manage">` on Add Role, the add-role form, and per-row Remove |

Note that the Roles list's **Delete** action is not separately gated — `role.read` suffices to see and click it. Whether the delete succeeds is up to the backend's enforcement of `role.delete` (see §5).

### 2.2 Rest of the SPA

| Route prefix | Guard (list / new / edit) | Gotcha |
|---|---|---|
| `/dashboard`, `/profile` | authenticated only — no key | |
| `/clusters` | `cluster.read` / `cluster.create` / `cluster.update` | |
| `/business-units` | `cluster.read` / `cluster.create` / `cluster.update` | **Reuses `cluster.*` keys** — there are no `business_unit.*` keys; granting cluster access also grants Business Units, and the two cannot be separated |
| `/users` | `user.read` / `user.create` / `user.update` | Distinct from `user_platform.*`, which gates role assignment, not user CRUD |
| `/applications` | `application.read` / `application.create` / `application.update` | |
| `/report-templates` | `report_template.read` / `report_template.create` / `report_template.update` | |
| `/print-template-mapping` | `print_template_mapping.read` / `print_template_mapping.create` / `print_template_mapping.update` | |
| `/news` | `news.read` / `news.create` / `news.update` | |
| `/broadcasts/new` | `broadcast.send` | Single route; no list page |

Three routes are fully public (no `PrivateRoute` at all): `/` (landing), `/login`, and `/changelog`. Source: `../carmen-platform/src/App.tsx` (the full `<Routes>` block, lines 48–301). No route anywhere in the SPA passes a `.delete` key as `requiredPermission` — delete actions live inside list pages whose guard is the `.read` key.

## 3. How guards compose

A user's path to any action passes up to three gates, outermost first:

1. **Route guard** — `PrivateRoute` (`src/components/PrivateRoute.tsx`). If the session is unauthenticated it renders `<Navigate to="/login" replace />`. If `requiredPermission` is set and `hasPermission(requiredPermission)` is false — or `requireSuperAdmin` is set and `isSuperAdmin` is false — it renders `<AccessDenied />`, a card inside the normal `<Layout>` shell (shield icon, "Access Denied", "You don't have permission to access this page.", a Back-to-Dashboard button). The sidebar stays visible and the session stays valid.
2. **Sidebar filter** — `Layout.tsx` declares `allNavItems` where each entry may carry `permission: '<key>'` or `superAdminOnly: true`, then filters: an item survives only when `(!item.permission || hasPermission(item.permission)) && (!item.superAdminOnly || isSuperAdmin)`. Hidden items are still directly addressable by URL — the route guard is the real barrier; the sidebar is UX. The sidebar keys match the route keys one-for-one for the list routes (`role.read`, `user_platform.read`, `cluster.read`, etc.), so there is no divergence where a visible entry leads to `AccessDenied`. The Permission Catalog has no sidebar entry at all.
3. **In-page gate** — `<Can permission="..." clusterId?>` (`src/components/Can.tsx`) renders its children only when `hasPermission` passes, with an optional `fallback` (default: nothing). Currently the only production use is `user_platform.manage` on the User Platform detail page; every other screen exposes all of its actions to anyone who passes the route guard.

All three layers call the same `hasPermission(key, opts?)` from `AuthContext` — there is exactly one resolution algorithm (§4), so route, sidebar, and in-page outcomes can never disagree for the same key. Note that route guards never pass a `clusterId`, so they take the broad "any cluster grants it" branch: a role scoped to a single cluster still opens the corresponding screens platform-wide in the current SPA, and the cluster-scoped narrowing matters for `<Can clusterId>` call sites and backend enforcement.

## 4. Permission resolution walkthrough

The full resolution path, from login to a single check (sources: `AuthContext.tsx` `login`/`hasPermission`, `utils/permissions.ts` `checkPermission`):

```
on login(credentials):
    token = POST /api/auth/login                       # unwrap { data: { access_token } }
    store token; set Authorization header

    eff   = GET /api/user/permission/platform          # EffectivePermissions
    count = GET /api-system/user?page=1&perpage=1      # read paginate.total

    hasAnyPermission = eff exists and (
        eff.is_super_admin
        or eff.platform is non-empty
        or eff.clusters has any key
    )
    isBootstrap = count is not null and count <= 1     # first-admin escape hatch

    if not hasAnyPermission and not isBootstrap:
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

## 5. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | Bootstrap login — platform has 0 or 1 total users | `login()` admits a session with zero permissions; every `hasPermission` returns `true`, so all routes, sidebar entries, and `<Can>` blocks open | The intended first-admin path: sign in, create roles, assign them. Dormant as soon as a second user row exists; an in-flight session does not re-check the count until refresh/login |
| 2 | `userCount` still `null` (count fetch pending or failed) | Bootstrap branch does not fire; checks run strictly against the permission snapshot | A failed count fetch fails closed, not open |
| 3 | Super admin session | `is_super_admin` short-circuits before any key list — even with empty `platform`/`clusters` everything passes | Never QA key coverage from a super-admin session; it cannot reveal missing grants. Test with a role-built session instead |
| 4 | `user_platform.read` without `user_platform.manage` | List and detail pages load; the Roles & Scope card is read-only — Add Role, the add-role form, and Remove buttons do not render | The canonical `<Can>` test case; verify the buttons are absent, not merely disabled |
| 5 | `role.read` without `role.delete` | The Delete item in the Roles list dropdown is still visible and clickable — no client-side `.delete` gate exists | Expect the backend to reject and the SPA to surface an error toast; if the delete succeeds, that is a backend authorization gap, not intended behaviour |
| 6 | Permission revoked mid-session | The cached `effectivePermissions` snapshot keeps granting until the next login or `AuthProvider` mount refetches | Backend enforcement is the real boundary; the SPA snapshot is advisory between refreshes |
| 7 | New permission key needed | The catalog is read-only in the SPA — new `resource.action` rows arrive only via backend seed/migration and redeploy | A feature branch adding a guarded route must coordinate a backend catalog change; the key will not exist until then |
| 8 | Cluster-scoped role and platform-wide routes | Route guards check without `clusterId`, so any single cluster grant opens the corresponding screens globally | Scoping narrows `<Can clusterId>` call sites and backend data filtering, not SPA route access |
| 9 | Dev builds with an empty permission response | `DEV_MOCK_EFFECTIVE_PERMISSIONS` (all platform-management keys, `is_super_admin: false`) is substituted in `import.meta.env.DEV` only | Never active in production builds; do not interpret dev-mode access as a grant |
| 10 | Granting cluster access | `cluster.*` keys also open `/business-units*` — there are no separate `business_unit.*` keys | Include Business Units screens in any cluster-permission test plan |

## 6. Recommendations

- **Test per key, not per persona.** Build one QA role per permission key (or small key set) and verify the route, sidebar entry, and in-page affordances toggle together — they share one resolver, so a divergence indicates a hardcoded gate.
- **Keep a non-super-admin QA account.** Edge case 3 makes super-admin sessions useless for verifying grants; reserve the flag for testing the bypass itself and the `/platform/super-admins` screen.
- **Treat SPA gates as advisory.** Every mutation the SPA hides behind a key (`user_platform.manage`, the ungated role Delete) must be re-verified against the backend with a token lacking that key — client-side gating alone is not a security boundary.
- **When adding a guarded feature**, register all three layers together: the catalog row (backend), the `requiredPermission` on the route, and the sidebar `permission` field — plus `<Can>` for any action narrower than the route's key. Follow the `resource.action` naming of the existing catalog.
- **Decide deliberately about `business_unit.*`.** If Business Units ever needs independent gating, new keys plus route/sidebar updates are required; until then, document the `cluster.*` reuse in test plans rather than treating it as a bug.

**References:** `../carmen-platform/src/App.tsx` (route guards) · `src/components/PrivateRoute.tsx` (guard + AccessDenied) · `src/components/Layout.tsx` (sidebar filter, lines 49–71) · `src/components/Can.tsx` · `src/context/AuthContext.tsx` (`login` lines 115–188, `hasPermission` lines 210–214) · `src/utils/permissions.ts` (`checkPermission`, dev mock).
**Cross-links:** [Platform RBAC landing](/en/platform/rbac) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md)
