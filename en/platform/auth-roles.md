---
title: Authentication & Roles
description: Login flow, session model, role catalog, route guards, and sidebar role-based filtering for the Carmen Platform admin product.
published: true
date: 2026-05-19T12:00:00.000Z
tags: platform/auth-roles, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Authentication & Roles

> **At a Glance**
> **Module purpose:** Login flow, session model, role catalog, and the route + sidebar guards that gate every Platform admin surface &nbsp;·&nbsp; **Audience:** Platform admin developers and QA &nbsp;·&nbsp; **Key entities/tables:** `user`, `platform_role`, `AuthContext` session state, `PrivateRoute` guard, sidebar `NavItem.roles` &nbsp;·&nbsp; **Sub-pages:** 0

## 1. Overview

Authentication & Roles is the cross-cutting access-control documentation for the Carmen Platform admin product. It covers the entire path a signed-in user takes: the `/login` page collects email-or-username and password, the `AuthContext` stores the resulting JWT and the user's `platform_role`, `PrivateRoute` gates every authenticated route, and the sidebar in `Layout` hides nav items the current role cannot reach. No other Platform module owns these pieces — each feature module just consumes them.

The login page itself (`src/pages/Login.tsx`) is a single email-or-username and password form with no SSO, MFA, or password-reset flow. On submit it calls `POST /api/auth/login`, expects an `access_token` and a `platform_role` in the response, and stores both in `localStorage` (`token`, `user`, `loginResponse`). The token is attached as `Authorization: Bearer ...` to every subsequent API call via the shared axios instance. If `platform_role` is not in the allow-list, login is rejected with an "Access Denied" message before the session is created.

After login, `PrivateRoute` wraps every protected route. Without an `allowedRoles` prop it lets any authenticated user through; with one, it checks `hasRole(allowedRoles)` and renders `<AccessDenied>` inside the normal `<Layout>` when the check fails. The same `hasRole()` function drives the sidebar — `Layout` filters its `NavItem[]` against the current role so users only see the entries they can actually reach. There is one bootstrap exception: when `userCount` has resolved to `0` or `1` (first-admin bootstrap state), `hasRole()` returns `true` for any role array so the first administrator can set up the platform. When `userCount` is still `null` (the API call has not yet resolved or failed), the bootstrap exception does NOT fire and normal role checking applies.

## 2. Business Context

Carmen Platform admin is operated by hospitality groups that often run multiple properties under a parent organization, so a single permission level does not fit — cluster-wide operators, per-BU staff, and Carmen-internal support engineers all need different surfaces. The `platform_role` value on each user account encodes which surfaces that user can reach; everything else in this module exists to enforce that binding consistently at login, at the route boundary, and in the sidebar.

## 3. Key Concepts

- **Authentication**: Email-or-username + password sign-in via `POST /api/auth/login`. Returns an `access_token` and a `platform_role`. No SSO, MFA, OAuth, or password-reset flow exists in the Platform admin product today.
- **Session**: The `token`, `user`, and `loginResponse` objects persisted in `localStorage` and mirrored in `AuthContext` React state. The session survives page reloads because `AuthContext` rehydrates from `localStorage` on mount.
- **AuthContext**: The React context (`src/context/AuthContext.tsx`) that exposes `user`, `login`, `logout`, `isAuthenticated`, `platformRole`, `hasRole`, and `userCount` to the rest of the app via the `useAuth()` hook.
- **platform_role**: The single string field on the user that drives every access decision. Stored in `loginResponse.platform_role` and surfaced through `AuthContext.platformRole`.
- **ALLOWED_ROLES**: The hard-coded allow-list inside `AuthContext` that login validates against before creating a session. Currently `platform_admin`, `super_admin`, `support_manager`, `support_staff`, `security_officer`. Any other role value is rejected at login.
- **PrivateRoute**: The route guard component (`src/components/PrivateRoute.tsx`). Redirects unauthenticated users to `/login`. If an `allowedRoles` prop is supplied, runs `hasRole(allowedRoles)` and shows `<AccessDenied>` on failure.
- **allowedRoles**: The optional prop on `PrivateRoute` listing the roles permitted to view a route. Routes without this prop accept any authenticated user; routes with it reject non-matching roles.
- **AccessDenied**: The full-page component rendered inside `<Layout>` when a role check fails on a route. Shows the user's current role and a "Back to Dashboard" button. Defined alongside `PrivateRoute`.
- **hasRole(roles)**: Method on `AuthContext` that returns `true` when the current `platformRole` is in the supplied array. Also returns `true` when `userCount !== null` AND `userCount <= 1` (bootstrap exception for first-admin setup). When `userCount` is `null` (API call not yet resolved or failed), the bootstrap exception does NOT fire — normal role checking applies.
- **Sidebar role filter**: In `Layout.tsx`, the `allNavItems` array carries an optional `roles` field on each entry; `Layout` filters it through `hasRole()` so users never see nav items they cannot open.

## 4. Roles and Personas

The five values in `ALLOWED_ROLES` (`src/context/AuthContext.tsx`) are the only roles that may sign in to the Platform admin product.

| Role | Reaches |
|---|---|
| `platform_admin` | Full platform administrator. Reaches every route, including `Clusters`, `Report Templates`, and `Print Template Mapping`. |
| `super_admin` | Highest-tier administrator. Passes the `ALLOWED_ROLES` gate at login but is not currently listed in any route's `allowedRoles` array — has access to authenticated-only routes but not to cluster/report-template surfaces. |
| `support_manager` | Carmen support manager. Same route access as `platform_admin` — listed in every `allowedRoles` array that gates an admin surface. |
| `support_staff` | Carmen support engineer. Same route access as `support_manager`. |
| `security_officer` | Security/audit role. Passes the `ALLOWED_ROLES` gate at login but is not currently listed in any route's `allowedRoles` array — has access to authenticated-only routes only. |

All five roles can reach `Dashboard`, `Business Units`, `Users`, and `Profile` because those routes use `PrivateRoute` without an `allowedRoles` prop.

## 5. Related Modules

- [[users]] — manages the `platform_role` field this module reads; creating or editing a user is where roles are actually assigned
- [[clusters]] — the highest-impact role-gated surface; its `allowedRoles` array is the canonical example of how features consume `hasRole()`
- [[report-templates]] — second example of a role-gated surface using the same admin-tier role list
- [[profile]] — the only authenticated-only page reachable from the avatar menu rather than the sidebar; depends on this module's session model
- [[business-units]] — reached by every authenticated role; useful counter-example showing what "no `allowedRoles`" looks like in practice

## 6. Reference Sources

- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/Login.tsx`, `../carmen-platform/src/context/AuthContext.tsx`, `../carmen-platform/src/components/PrivateRoute.tsx`, `../carmen-platform/src/components/Layout.tsx`

## 7. Pages in This Module

This module is a single page; see the parent [Platform book index](/en/platform).
