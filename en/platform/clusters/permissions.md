---
title: Cluster — Permissions
description: Route guards, access matrix, bootstrap exception, and sidebar filter for all cluster operations.
published: true
date: 2026-05-19T23:55:00.000Z'
tags: book/platform, clusters, permissions
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# Cluster — Permissions

> **At a Glance**
> **Gate:** all three cluster routes carry `allowedRoles={["platform_admin", "support_manager", "support_staff"]}` &nbsp;·&nbsp; **Bootstrap exception:** `hasRole` returns `true` unconditionally when `userCount !== null && userCount <= 1` (first-admin setup) &nbsp;·&nbsp; **On role failure:** `<AccessDenied>` renders inside `<Layout>` (sidebar stays visible) &nbsp;·&nbsp; **Sidebar filter:** Clusters entry hidden from users who fail `hasRole()` &nbsp;·&nbsp; **No per-button role gates** within the cluster surface — pass the route guard and you see every action

## 1. Overview

Cluster management carries admin-tier responsibility: creating or editing a cluster affects license capacity (`max_license_bu`), defines the top-level tenant container that all business units and users belong to, and can have cross-tenant data implications if the wrong roles are permitted. Because of this, every cluster route is gated to the three highest operational roles in the platform — `platform_admin`, `support_manager`, and `support_staff` — while modules such as Business Units, Users, and Dashboard have no route-level `allowedRoles` restriction.

The gating mechanism is implemented in two layers. At the route level, `PrivateRoute` (in `src/components/PrivateRoute.tsx`) receives an `allowedRoles` prop and calls `hasRole()` from `AuthContext`; if the check fails, it renders `<AccessDenied>` inside the normal `<Layout>` shell instead of the requested component. At the navigation level, `Layout.tsx` filters the sidebar `NavItem[]` array through `hasRole()` before rendering, so users without the required role never see the Clusters entry in the sidebar at all — though they can still type the URL directly, where the route guard catches them.

By contrast, `/business-units`, `/users`, and `/dashboard` are wrapped with `<PrivateRoute>` but without an `allowedRoles` prop; those routes are visible to any authenticated user whose `platform_role` is in the `ALLOWED_ROLES` (see [auth-roles](/en/platform/auth-roles)) allow-list, regardless of which specific role they hold. Clusters is one of only three navigation destinations (along with Report Templates and Print Template Mapping) that carry the additional route-level role restriction.

## 2. Route guards

| Route | Component rendered | `allowedRoles` | Source |
|---|---|---|---|
| `/clusters` | `ClusterManagement` | `platform_admin`, `support_manager`, `support_staff` | `src/App.tsx` line 42 |
| `/clusters/new` | `ClusterEdit` | `platform_admin`, `support_manager`, `support_staff` | `src/App.tsx` line 50 |
| `/clusters/:id/edit` | `ClusterEdit` | `platform_admin`, `support_manager`, `support_staff` | `src/App.tsx` line 58 |

The `allowedRoles` array is hardcoded inline at each of the three `<PrivateRoute>` call sites (`App.tsx` lines 42, 50, 58). There is no shared constant — the identical array is duplicated three times. Any change to which roles may access cluster routes must therefore be applied at all three call sites; forgetting one will create an inconsistent state where a role can reach the list page but not the edit page (or vice versa).

## 3. Effective access matrix

Read the table left-to-right: sign-in eligibility (`AuthContext.ALLOWED_ROLES`) is checked first at login; cluster-route eligibility (the `allowedRoles` array on each `PrivateRoute`) is checked only for roles that can sign in. The "Effective cluster access" column states the combined outcome.

`enum_platform_role` (Prisma `schema.prisma` line 539) defines seven values. `AuthContext.ALLOWED_ROLES` (see [auth-roles](/en/platform/auth-roles), line 10) lists five values that are permitted to sign in to the SPA at all. Of those five, three are permitted to reach cluster routes.

| `platform_role` value | Can sign in to SPA? | In cluster `allowedRoles`? | Effective cluster access |
|---|---|---|---|
| `super_admin` | Yes (in `ALLOWED_ROLES`) | No | Blocked — sees `<AccessDenied>` inside `<Layout>` |
| `platform_admin` | Yes | Yes | Full access to list, create, and edit |
| `support_manager` | Yes | Yes | Full access to list, create, and edit |
| `support_staff` | Yes | Yes | Full access to list, create, and edit |
| `security_officer` | Yes (in `ALLOWED_ROLES`) | No | Blocked — sees `<AccessDenied>` inside `<Layout>` |
| `integration_developer` | No (not in `ALLOWED_ROLES`) | n/a | Cannot sign in to the SPA at all |
| `user` | No (not in `ALLOWED_ROLES`) | n/a | Cannot sign in to the SPA at all |

`integration_developer` and `user` are rejected at login time: `AuthContext.login()` (lines 104–112) checks `ALLOWED_ROLES` before storing a token and returns an "Access Denied" result immediately. They never obtain a session and so the route guard is never reached for them.

`super_admin` and `security_officer` can sign in and hold a valid session, but when they navigate to `/clusters`, `/clusters/new`, or `/clusters/:id/edit`, `PrivateRoute` calls `hasRole(["platform_admin", "support_manager", "support_staff"])`, which returns `false`, and renders `<AccessDenied>` instead of the cluster component.

The bootstrap exception (see §4) can override the "Effective cluster access" column above for any session while `userCount <= 1` (i.e. during initial platform setup) — but it does NOT override the "Can sign in to SPA?" column; login-time `ALLOWED_ROLES` checking is not bypassed by the bootstrap exception.

## 4. Bootstrap exception

`hasRole()` in `AuthContext.tsx` (lines 180–185) implements a first-admin shortcut:

```
const hasRole = (roles: string[]): boolean => {
  // Allow all access when there are 0 or 1 users (initial setup)
  if (userCount !== null && userCount <= 1) return true;
  if (!platformRole) return false;
  return roles.includes(platformRole);
};
```

When `userCount !== null && userCount <= 1`, the function returns `true` unconditionally, bypassing the `roles.includes(platformRole)` check. This allows the first administrator who sets up the platform to reach `/clusters` — and all other role-gated routes — without necessarily holding one of the three permitted roles.

**How `userCount` is populated.** On every mount of `AuthProvider` (and on every successful login), `fetchUserCount()` (lines 81–89) calls `userService.getAll({ page: 1, perpage: 1 })`, which hits `GET /api-system/user?page=1&perpage=1`. The total count is read from `response.paginate?.total ?? response.total ?? response.data?.length ?? 0` and stored in the `userCount` state variable.

**The `userCount === null` case.** `userCount` is initialised to `null` (line 26) and stays `null` until `fetchUserCount()` resolves. The condition `userCount !== null && userCount <= 1` is `false` when `userCount` is `null`, so the bootstrap exception does NOT fire during the loading window. A user with a non-cluster-permitted role who visits `/clusters` before `fetchUserCount()` completes will see `<AccessDenied>` — they may see the cluster content only once the count resolves to `<= 1` and `PrivateRoute` re-renders.

**The `userCount > 1` case.** Once the platform has two or more users, `userCount > 1` and the exception is dormant. `fetchUserCount()` is called only on mount and on login — it does not subscribe to real-time changes. If a platform operator deletes all but one user while an existing session is active, the in-memory `userCount` will not update until the next page refresh or login, so the exception will not automatically re-fire mid-session. A fresh session after the count drops to `<= 1` will pick up the new count and the exception will fire again.

**Scope of the exception.** The bootstrap exception applies only to `hasRole()` route-time checks inside `PrivateRoute`. The login-time `ALLOWED_ROLES` check in `login()` (line 105) is a separate code path and is not affected — a user with `platform_role = integration_developer` cannot sign in regardless of `userCount`.

## 5. AccessDenied behaviour

`PrivateRoute` (`src/components/PrivateRoute.tsx`) implements two distinct rejection paths:

**Auth-fail (no session, lines 52–54):** if `isAuthenticated` is `false`, the component renders `<Navigate to="/login" replace />` — a hard redirect that replaces the current history entry. The user ends up on the login page with no visible error in the current view.

**Role-fail (authenticated but wrong role, lines 56–58):** if `allowedRoles` is provided and `hasRole(allowedRoles)` returns `false`, the component renders `<AccessDenied />`. `AccessDenied` is defined in the same file (lines 9–38) and is wrapped in `<Layout>`, so the full sidebar and header remain visible. Inside the content area, a card displays a shield-X icon, the heading "Access Denied" in red, the message `Your role "<platformRole>" does not have permission to access this page.`, and a "Back to Dashboard" button (`onClick={() => navigate('/dashboard')}`).

The consequence for role-fail users is that they remain inside the SPA shell, can still use the sidebar to navigate to permitted pages, and receive a clear statement of their current role. They are not logged out and their session is not invalidated.

## 6. Sidebar filter

`Layout.tsx` (line 51) defines the Clusters nav item as:

```
{ path: '/clusters', label: 'Clusters', icon: Network, roles: ['platform_admin', 'support_manager', 'support_staff'] }
```

Line 58 filters the full `allNavItems` array before rendering:

```
const navItems = allNavItems.filter(item => !item.roles || hasRole(item.roles));
```

Items with no `roles` field (Dashboard, Business Units, Users) pass the filter for all authenticated users. Items with a `roles` field (Clusters, Report Templates, Print Template Mapping) are kept only when `hasRole(item.roles)` returns `true`. The Clusters `roles` field is `['platform_admin', 'support_manager', 'support_staff']` — the identical set used in `App.tsx` route guards. Route guard and sidebar filter are consistent; there is no divergence that would expose the Clusters entry in the sidebar while blocking the route (or vice versa). Any future change to which roles may access Clusters must therefore be applied in BOTH `src/App.tsx` (the three route guards at lines 42, 50, 58 — see §2) AND `src/components/Layout.tsx` (the sidebar `NavItem` `roles` field at line 51). The duplication is intentional and load-bearing — pulling one and not the other would expose the Clusters entry in the sidebar while blocking the route (or vice versa).

A user without the required role simply does not see the Clusters entry in the sidebar. They can still reach `/clusters` by typing the URL directly, but the route guard renders `<AccessDenied>` before any cluster data is loaded.

## 7. Within the cluster surface

Once a user passes the route guard, the SPA does NOT additionally gate individual UI elements by `platform_role`. Every button and action on the cluster list and edit screens is visible and functional to all three permitted roles equally:

| Action | Visible to all three permitted roles? |
|---|---|
| View cluster list (pagination, search, CSV export) | Yes |
| Export cluster list as CSV | Yes |
| Create new cluster (navigate to `/clusters/new`) | Yes |
| Edit an existing cluster (`/clusters/:id/edit`) | Yes |
| Save / Cancel on edit form | Yes |
| Soft-delete a cluster | Yes |
| Add a user to the cluster | Yes |
| Edit a cluster user's role (`admin` / `user`) | Yes |
| Remove a user from the cluster | Yes |
| Add Business Unit link (navigate-to-new) | Yes — subject only to `max_license_bu` cap check, not role |

There is no "viewer" sub-role within the cluster surface. The `max_license_bu` cap on the Add Business Unit action is a business-rule constraint, not a role gate — all three permitted roles see the same enabled/disabled state of that control depending on the current BU count. Testers planning role-based test scenarios should focus on testing the route guard (§2) and the bootstrap exception (§4), not per-button differentiation within the cluster surface.

## 8. References

**Primary sources (read these before updating this page):**
- `../carmen-platform/src/App.tsx` — route wiring with `allowedRoles` props (lines 42, 50, 58).
- `../carmen-platform/src/context/AuthContext.tsx` — `ALLOWED_ROLES` (line 10), `hasRole` (line 180), `userCount` state (line 26), `fetchUserCount` (line 81), bootstrap exception condition (line 182).
- `../carmen-platform/src/components/PrivateRoute.tsx` — gate logic: auth-fail redirect (lines 52–54), role-fail `<AccessDenied>` render (lines 56–58), `AccessDenied` component definition (lines 9–38).
- `../carmen-platform/src/components/Layout.tsx` — sidebar `NavItem[]` filter via `hasRole()` (lines 51, 58).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `enum_platform_role` (line 539) for the 7-value source list.

**Cross-links:**
- [auth-roles](/en/platform/auth-roles) — full role definitions and cross-SPA route map
- [users](/en/platform/users) — where `platform_role` is assigned to a platform user
- [clusters](/en/platform/clusters) — Clusters module landing
- [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) — sibling sub-pages
