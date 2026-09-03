---
title: Platform RBAC — Permissions
description: Route-guard matrix for the whole SPA, how route/sidebar/in-page gates compose, the permission-resolution algorithm, and edge cases for testers. Updated for the Forbidden rename and Roles-list gating added since 2026-06-10.
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, rbac, permissions
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Platform RBAC — Permissions

> **At a Glance**
> **Gate:** every guarded route carries `requiredPermission="resource.action"` (or `requireSuperAdmin`) on `PrivateRoute` &nbsp;·&nbsp; **Resolution order:** bootstrap → super-admin → platform keys → cluster keys &nbsp;·&nbsp; **Bootstrap exception:** total user count 0 or 1 ⇒ login skips the ≥1-permission gate and `hasPermission` returns `true` &nbsp;·&nbsp; **On failure:** the `Forbidden` page (renamed from an inline `AccessDenied` component; `src/pages/Forbidden.tsx`) renders in place inside `<Layout>` (sidebar stays visible, URL unchanged); a direct `/403` route also renders it &nbsp;·&nbsp; **In-page gates:** `<Can>` wraps Add/Edit/Delete on most management list and edit pages (`.create`/`.update`/`.delete` keys, cluster-scoped for Clusters/Business Units); within the RBAC module's own screens, **Roles list/edit now gate Add/Edit/Delete too** (added since 2026-06-10 — see §2.1), and the User Platform detail page gates on `user_platform.manage`

## 1. Overview

This page is the canonical map of how permission keys gate the Platform SPA. Authorization happens at three layers that share one resolver: the **route guard** (`PrivateRoute`'s `requiredPermission` / `requireSuperAdmin` props), the **sidebar filter** (`Layout.tsx` hides nav items whose `permission` the session lacks), and **in-page gates** (`<Can permission="...">` wrapping individual buttons and forms). All three call `AuthContext.hasPermission`, which delegates to the pure `checkPermission` function over the session's `EffectivePermissions` snapshot.

Two routes are authenticated-only with no key requirement: `/dashboard` and `/profile`. Any session that passes login reaches them. Everything else carries a key — and because the login gate itself requires the account to hold at least one permission (or the super-admin flag, or the bootstrap exception), a session cannot be admitted with zero permissions at login time outside bootstrap. The ≥1-permission gate runs only inside `login()`, though: a session whose grants are revoked mid-session stays signed in even after the snapshot refetch — it just fails every subsequent permission check.

## 2. Gate matrix

### 2.1 RBAC module screens

| Route | Component | Guard | In-page gates |
|---|---|---|---|
| `/platform/roles` | `RoleManagement` | `role.read` | **Corrected — no longer "None":** row **Edit** gated `<Can permission="role.update">`, row **Delete** gated `<Can permission="role.delete">` (both added since 2026-06-10). **Add Role** (header button) gated `<Can permission="role.create">`. Export remains ungated |
| `/platform/roles/new` | `RoleEdit` | `role.create` | None |
| `/platform/roles/:id/edit` | `RoleEdit` | `role.update` | The header **Edit** button is `<Can permission="role.update">` (added since 2026-06-10, matching the pattern already used elsewhere in the SPA) |
| `/platform/permissions` | `PermissionCatalog` | `role.read` | None (read-only screen) |
| `/platform/super-admins` | `SuperAdminManagement` | `requireSuperAdmin` | None — only super admins ever reach the page |
| `/platform/user-platform` | `UserPlatformManagement` | `user_platform.read` | None |
| `/platform/user-platform/:userId` | `UserPlatformEdit` | `user_platform.read` | `<Can permission="user_platform.manage">` on Add Role, the add-role form, and per-row Remove |

**Corrected (stale as of the last sync):** the Roles list's **Delete** action used to be ungated — `role.read` alone was enough to see and click it. That is no longer true: row Edit and row Delete now carry the same `<Can>` gates as every other management list (§3), and the Roles list is no longer the one exception. Whether the role delete succeeds is still up to the backend's own enforcement of `role.delete` (see §5) — the in-page gate is advisory, as everywhere else.

### 2.2 Rest of the SPA

| Route prefix | Guard (list / new / edit) | Gotcha |
|---|---|---|
| `/dashboard`, `/profile` | authenticated only — no key | |
| `/clusters` | `cluster.read` / `cluster.create` / `cluster.update` | |
| `/business-units` | `cluster.read` / `cluster.create` / `cluster.update` | **Reuses `cluster.*` keys** — there are no `business_unit.*` keys; granting cluster access also grants Business Units, and the two cannot be separated |
| `/tenant-migrations` | `cluster.read` | Standalone fleet-wide migration overview; also reuses `cluster.*` (not a named unit of this book) |
| `/users` | `user.read` / `user.create` / `user.update` | Distinct from `user_platform.*`, which gates role assignment, not user CRUD |
| `/applications` | `application.read` / `application.create` / `application.update` | |
| `/report-templates` | `report_template.read` / `report_template.create` / `report_template.update` | |
| `/report-form-groups` | `report_template.read` (mutations via `report_template.update`/`.create`) | New 2026-07-23; reuses Report Templates' keys, no new ones |
| `/news` | `news.read` / `news.create` / `news.update` | |
| `/broadcasts/new` | `broadcast.send` | Single route; no list page |
| `/sql-workbench` | `sql_workbench.read` | Not a named unit of this book; no wiki page yet |

**Removed 2026-07-23/24:** `/print-template-mapping*` and its `print_template_mapping.*` keys no longer exist — the module and the permission catalog rows it used were both deleted (see [print-template-mapping](/en/platform/print-template-mapping), historical page).

Three routes are fully public (no `PrivateRoute` at all): `/` (landing), `/login`, and `/changelog`. Source: `../carmen-platform/src/App.tsx` (the full `<Routes>` block). No route anywhere in the SPA passes a `.delete` key as `requiredPermission` — delete actions live inside list pages, where every management list gates them in-page with `<Can permission="*.delete">` (§3), **now including Roles** (§2.1) — the previous sync's "only the Roles list still exposes Delete to anyone holding its `.read` guard" is stale.

## 3. How guards compose

A user's path to any action passes up to three gates, outermost first:

1. **Route guard** — `PrivateRoute` (`src/components/PrivateRoute.tsx`, 40 lines). If the session is unauthenticated it renders `<Navigate to="/login" replace />`. If `requiredPermission` is set and `hasPermission(requiredPermission)` is false — or `requireSuperAdmin` is set and `isSuperAdmin` is false — it renders `<Forbidden />` **in place** (a dedicated page, `src/pages/Forbidden.tsx` — renamed from an inline `AccessDenied` component that used to live inside this same file), preserving the URL so its "Go Back" action can't bounce off the guard. `Forbidden` renders inside the normal `<Layout>` shell: a `ShieldX` icon, "403" code, "Access Denied" heading, "You don't have permission to access this page.", and two actions — "Go Back" (falls back to `/dashboard` when there's no sensible back target) and "Go to Dashboard". The sidebar stays visible and the session stays valid. A direct `/403` route renders the same `Forbidden` page.
2. **Sidebar filter** — `Layout.tsx` declares `allNavItems` where each entry may carry `permission: '<key>'` or `superAdminOnly: true`, then filters: an item survives only when `(!item.permission || hasPermission(item.permission)) && (!item.superAdminOnly || isSuperAdmin)`. Hidden items are still directly addressable by URL — the route guard is the real barrier; the sidebar is UX. The sidebar keys match the route keys one-for-one for the list routes (`role.read`, `user_platform.read`, `cluster.read`, etc.), so there is no divergence where a visible entry leads to `Forbidden`. The Permission Catalog has no sidebar entry at all.
3. **In-page gate** — `<Can permission="..." clusterId?>` (`src/components/Can.tsx`) renders its children only when `hasPermission` passes, with an optional `fallback` (default: nothing). `<Can>` gates Add/Edit/Delete across most of the SPA's management pages: the list pages (Clusters, Business Units, Users, Applications, Report Templates, News) wrap their Add button in the `.create` key, row Edit in `.update`, and row Delete in `.delete`; the corresponding edit pages wrap their Edit toggle in `.update` (without it the detail view stays read-only, so Save is unreachable — Save itself is not wrapped, and edit pages have no `<Can>`-gated delete); and BroadcastCompose wraps Send in `broadcast.send`. The Clusters and Business Units gates pass a `clusterId` (e.g. `<Can permission="cluster.update" clusterId={row.original.id}>`), taking the cluster-specific resolution branch (§4) — the only call sites that do. **The removed Print Template Mapping module used to appear in this list too — it no longer exists (see [print-template-mapping](/en/platform/print-template-mapping)).** Within the RBAC module's own screens, the Roles list and Role editor **now follow the same pattern as the rest of the SPA** (row Edit/Delete and the Edit toggle gated — corrected from the last sync's "expose all actions to anyone who passes the route guard"); the User Platform detail page uses `<Can>` for `user_platform.manage` (Add Role, the add-role form, per-row Remove); Permission Catalog, Super Admins, and User Platform list remain fully ungated in-page (their route guards are the only barrier).

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
| 5 | `role.read` without `role.delete` | **Corrected — no longer reproducible as previously described.** The Delete item in the Roles list dropdown is now `<Can permission="role.delete">`-gated like every other management list and does not render for a session lacking the key | Verify the Delete item is absent, not merely disabled — mirrors edge case 4's `<Can>` test pattern. Backend enforcement of `role.delete` remains the real boundary regardless |
| 6 | Permission revoked mid-session | The cached `effectivePermissions` snapshot keeps granting until the next login or `AuthProvider` mount refetches | Backend enforcement is the real boundary; the SPA snapshot is advisory between refreshes |
| 7 | New permission key needed | The catalog is read-only in the SPA — new `resource.action` rows arrive only via backend seed/migration and redeploy | A feature branch adding a guarded route must coordinate a backend catalog change; the key will not exist until then |
| 8 | Cluster-scoped role and platform-wide routes | Route guards check without `clusterId`, so any single cluster grant opens the corresponding screens globally | Scoping narrows `<Can clusterId>` call sites and backend data filtering, not SPA route access |
| 9 | Dev builds with an empty permission response | `DEV_MOCK_EFFECTIVE_PERMISSIONS` (all platform-management keys, `is_super_admin: false`) is substituted in `import.meta.env.DEV` only | Never active in production builds; do not interpret dev-mode access as a grant |
| 10 | Granting cluster access | `cluster.*` keys also open `/business-units*` — there are no separate `business_unit.*` keys | Include Business Units screens in any cluster-permission test plan |

## 6. Recommendations

- **Test per key, not per persona.** Build one QA role per permission key (or small key set) and verify the route, sidebar entry, and in-page affordances toggle together — they share one resolver, so a divergence indicates a hardcoded gate.
- **Keep a non-super-admin QA account.** Edge case 3 makes super-admin sessions useless for verifying grants; reserve the flag for testing the bypass itself and the `/platform/super-admins` screen.
- **Treat SPA gates as advisory.** Every mutation the SPA hides behind a key (`user_platform.manage`, `role.update`/`.delete`, and the rest) must be re-verified against the backend with a token lacking that key — client-side gating alone is not a security boundary.
- **When adding a guarded feature**, register all three layers together: the catalog row (backend), the `requiredPermission` on the route, and the sidebar `permission` field — plus `<Can>` for any action narrower than the route's key. Follow the `resource.action` naming of the existing catalog.
- **Decide deliberately about `business_unit.*`.** If Business Units ever needs independent gating, new keys plus route/sidebar updates are required; until then, document the `cluster.*` reuse in test plans rather than treating it as a bug.

**References:** `../carmen-platform/src/App.tsx` (route guards) · `src/components/PrivateRoute.tsx` (guard, 40 lines total) · `src/pages/Forbidden.tsx` (the renamed 403 page) · `src/components/Layout.tsx` (sidebar filter, lines 50–73) · `src/components/Can.tsx` · `src/context/AuthContext.tsx` (`login` lines 117–190, `hasPermission` lines 220–223) · `src/utils/permissions.ts` (`checkPermission`, dev mock).
**Cross-links:** [Platform RBAC landing](/en/platform/rbac) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md)
