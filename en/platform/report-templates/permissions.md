---
title: Report Template — Permissions
description: Three admin-tier-gated routes (same gate as clusters); access matrix; AccessDenied behaviour; sidebar filter.
published: true
date: 2026-05-19T23:55:00.000Z'
tags: book/platform, report-templates, permissions
editor: markdown
dateCreated: '2026-05-19T18:30:00.000Z'
---

# Report Template — Permissions

> **At a Glance**
> **Gate:** all three report-templates routes carry `allowedRoles={["platform_admin", "support_manager", "support_staff"]}` (`src/App.tsx` lines 114, 122, 130) &nbsp;·&nbsp; **Bootstrap exception:** same `userCount <= 1` mechanic as [Clusters Permissions §4](../clusters/permissions.md) &nbsp;·&nbsp; **On role failure:** `<AccessDenied>` renders inside `<Layout>` (sidebar stays visible) &nbsp;·&nbsp; **Sidebar filter:** Report Templates entry hidden from users who fail `hasRole()` &nbsp;·&nbsp; **No per-button role gates** within the report-templates surface

## 1. Overview

Report Templates is a Carmen-internal authoring surface for printable and exportable documents that ship as part of the platform's customisation contract. Templates are authored by Carmen support engineers — not customers — using a structured XML/FastReport editor with database-source binding against tenant schemas. Because authoring a template requires platform-level operational knowledge and carries direct implications for what customers can print or export from their business units, every report-templates route is gated to the same three admin-tier roles as Clusters: `platform_admin`, `support_manager`, and `support_staff`.

Report Templates shares the **same role gate** as [clusters](/en/platform/clusters). The detailed access mechanics — bootstrap exception, `<AccessDenied>` render path, and sidebar filter — work identically across the two modules. This page cross-links to [Clusters Permissions](../clusters/permissions.md) for the canonical implementation detail and documents only what is specific to the report-templates surface. By contrast, modules such as Business Units, Users, and Dashboard have no route-level `allowedRoles` restriction and are visible to any authenticated user in `ALLOWED_ROLES`.

## 2. Route guards

| Route | Component rendered | `allowedRoles` | Source |
|---|---|---|---|
| `/report-templates` | `ReportTemplateManagement` | `platform_admin`, `support_manager`, `support_staff` | `src/App.tsx` line 114 |
| `/report-templates/new` | `ReportTemplateEdit` | (same) | `src/App.tsx` line 122 |
| `/report-templates/:id/edit` | `ReportTemplateEdit` | (same) | `src/App.tsx` line 130 |

The `allowedRoles` array is hardcoded inline at each of the three `<PrivateRoute>` call sites — there is no shared constant. The identical array is duplicated three times, identical to the pattern in the cluster routes. Any change to which roles may access report-templates routes must be applied at all three call sites; forgetting one will create an inconsistent state where a role can reach the list page but not the edit page (or vice versa). The sidebar `roles` field in `Layout.tsx` (see §6) must also be updated in the same change.

## 3. Effective access matrix

Read the table left-to-right: sign-in eligibility (`AuthContext.ALLOWED_ROLES`, see [auth-roles](/en/platform/auth-roles)) is checked first at login; report-templates route eligibility (the `allowedRoles` array on each `PrivateRoute`) is checked only for roles that can sign in. The "Effective access" column states the combined outcome.

`enum_platform_role` (Prisma `schema.prisma` line 539) defines seven values. `AuthContext.ALLOWED_ROLES` (line 10) lists five values permitted to sign in to the SPA. Of those five, three are permitted to reach report-templates routes.

| `platform_role` | Can sign in to SPA? | In report-templates `allowedRoles`? | Effective access |
|---|---|---|---|
| `super_admin` | Yes (in `ALLOWED_ROLES`) | No | Blocked — sees `<AccessDenied>` inside `<Layout>` |
| `platform_admin` | Yes | Yes | Full access to list, create, and edit |
| `support_manager` | Yes | Yes | Full access to list, create, and edit |
| `support_staff` | Yes | Yes | Full access to list, create, and edit |
| `security_officer` | Yes (in `ALLOWED_ROLES`) | No | Blocked — sees `<AccessDenied>` inside `<Layout>` |
| `integration_developer` | No (not in `ALLOWED_ROLES`) | n/a | Cannot sign in to the SPA at all |
| `user` | No (not in `ALLOWED_ROLES`) | n/a | Cannot sign in to the SPA at all |

The matrix is identical to the clusters matrix ([Clusters Permissions §3](../clusters/permissions.md)). `integration_developer` and `user` are rejected at login time before the route guard is ever reached. The bootstrap exception (§4) can override the "Effective access" column for any session while `userCount <= 1`, but does not override the "Can sign in?" column.

## 4. Bootstrap exception

The `userCount <= 1` shortcut in `AuthContext.hasRole()` (lines 180–185) works identically for every role-gated module. Full implementation detail — the `null` vs `<= 1` vs `> 1` cases, the non-reactive refetch behaviour, and the scope of the exception — is documented in [Clusters Permissions §4](../clusters/permissions.md). The same caveats apply to report-templates:

- **During the API loading window** (`userCount === null`): the condition `userCount !== null && userCount <= 1` is `false`, so normal role checking applies. An authenticated user with a non-allowed role who visits `/report-templates` before `fetchUserCount()` resolves will see `<AccessDenied>`.
- **Once `userCount > 1`**: the exception is dormant. `fetchUserCount()` is called only on mount and on login — it does not subscribe to real-time changes, so the exception will not re-fire mid-session if user count drops during an active session.
- **Scope**: the bootstrap exception applies only to `hasRole()` route-time checks inside `PrivateRoute`. The login-time `ALLOWED_ROLES` check is a separate code path and is not affected.

## 5. AccessDenied behaviour

Same as [Clusters Permissions §5](../clusters/permissions.md). `PrivateRoute` (`src/components/PrivateRoute.tsx`) implements two distinct rejection paths:

**Auth-fail (no session, lines 52–53):** if `isAuthenticated` is `false`, the component renders `<Navigate to="/login" replace />` — a hard redirect that replaces the current history entry. The user ends up on the login page with no visible error in the current view.

**Role-fail (authenticated but wrong role, lines 56–57):** if `allowedRoles` is provided and `hasRole(allowedRoles)` returns `false`, the component renders `<AccessDenied />`. `AccessDenied` is defined in the same file (lines 9–38) and is wrapped in `<Layout>`, so the full sidebar and header remain visible. Inside the content area, a card displays a shield-X icon, the heading "Access Denied" in red, the message `Your role "<platformRole>" does not have permission to access this page.`, and a "Back to Dashboard" button (`onClick={() => navigate('/dashboard')}`).

Role-fail users remain inside the SPA shell, can still use the sidebar to navigate to permitted pages, and receive a clear statement of their current role. They are not logged out and their session is not invalidated.

## 6. Sidebar filter

`Layout.tsx` (line 54) defines the Report Templates nav item as:

```
{ path: '/report-templates', label: 'Report Templates', icon: FileText, roles: ['platform_admin', 'support_manager', 'support_staff'] }
```

Line 58 filters the full `allNavItems` array before rendering:

```
const navItems = allNavItems.filter(item => !item.roles || hasRole(item.roles));
```

Items with no `roles` field (Dashboard, Business Units, Users) pass the filter for all authenticated users. Items with a `roles` field (Clusters, Report Templates, Print Template Mapping) are kept only when `hasRole(item.roles)` returns `true`. The Report Templates `roles` field — `['platform_admin', 'support_manager', 'support_staff']` — is identical to the `allowedRoles` arrays in `App.tsx` route guards. Route guard and sidebar filter are consistent; there is no divergence that would expose the sidebar entry while blocking the route (or vice versa).

Any future change to which roles may access Report Templates must be applied in BOTH:
- `src/App.tsx` — the three route guards at lines 114, 122, 130 (see §2)
- `src/components/Layout.tsx` — the sidebar `NavItem` `roles` field at line 54

The duplication is intentional and load-bearing — same pattern as documented in [Clusters Permissions §6](../clusters/permissions.md).

## 7. Within the report-templates surface

Once a user passes the route guard, the SPA does NOT additionally gate individual buttons or fields by `platform_role`. Every action on the report-templates list and edit screens is visible to all three permitted roles equally:

| Action | Visible to all three permitted roles? |
|---|---|
| View template list (pagination, search) | Yes |
| Create new template (navigate to `/report-templates/new`) | Yes |
| Edit an existing template (`/report-templates/:id/edit`) | Yes |
| Save / Cancel on edit form | Yes |
| Soft-delete a template | Yes |
| File upload (Content tab — `.frx`, `.xml`, `.txt`) | Yes |
| Browse tenant-schema BU probe (views/functions/procedures dialog) | Yes |
| Standard / Custom toggle | Yes |
| Active / Inactive toggle | Yes |

There is no "viewer" sub-role within the report-templates surface. Testers planning role-based test scenarios should focus on testing the route gate (§2) and the bootstrap exception (§4), not per-button differentiation within the surface.

## 8. References

**Primary sources (read these before updating this page):**
- `../carmen-platform/src/App.tsx` — route wiring with `allowedRoles` (lines 114, 122, 130).
- `../carmen-platform/src/context/AuthContext.tsx` — `ALLOWED_ROLES` (line 10), `hasRole` (line 180), `userCount` state (line 26), bootstrap exception condition (line 182).
- `../carmen-platform/src/components/PrivateRoute.tsx` — gate logic: auth-fail redirect (lines 52–53), role-fail `<AccessDenied>` render (lines 56–57), `AccessDenied` component definition (lines 9–38).
- `../carmen-platform/src/components/Layout.tsx` — sidebar `NavItem` `roles` field (line 54), filter via `hasRole()` (line 58).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `enum_platform_role` (line 539) for the 7-value source list.

**Cross-links:**
- [auth-roles](/en/platform/auth-roles) — full role definitions and cross-SPA route map
- [users](/en/platform/users) — where `platform_role` is assigned to a platform user
- [Clusters Permissions](../clusters/permissions.md) — canonical permissions.md shape; same role gate; bootstrap exception detail (§4); AccessDenied detail (§5)
- [clusters](/en/platform/clusters) — Clusters module landing
- [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [XML Spec](./xml-spec.md) — sibling sub-pages
