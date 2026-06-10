---
title: Report Template — Permissions
description: Permission-key route guards, in-page Can gates, sidebar filter, and bootstrap exception for the report-templates surface.
published: true
date: 2026-06-10T14:15:00.000Z
tags: book/platform, report-templates, permissions
editor: markdown
dateCreated: '2026-05-19T18:30:00.000Z'
---

# Report Template — Permissions

> **At a Glance**
> **Gate:** the three report-templates routes carry `requiredPermission="report_template.read"` / `"report_template.create"` / `"report_template.update"` on `PrivateRoute` (`src/App.tsx` lines 156–179) &nbsp;·&nbsp; **In-page gates:** `<Can>` wraps Add Template (`report_template.create`), row Edit (`report_template.update`), row Delete (`report_template.delete`), and the edit-page Edit toggle (`report_template.update`) — none pass a `clusterId` &nbsp;·&nbsp; **`report_template.delete` is in-page only** — no route requires it &nbsp;·&nbsp; **Bootstrap exception:** `hasPermission` returns `true` unconditionally when `userCount !== null && userCount <= 1` &nbsp;·&nbsp; **On failure:** `<AccessDenied>` renders inside `<Layout>` (sidebar stays visible) &nbsp;·&nbsp; **Canonical model doc:** [rbac permissions](/en/platform/rbac/permissions)

## 1. Overview

Report Templates is a Carmen-internal authoring surface for printable and exportable documents that ship as part of the platform's customisation contract. Templates are authored by Carmen support engineers — not customers — using a structured XML/FastReport editor with database-source binding against tenant schemas. Because authoring a template requires platform-level operational knowledge and carries direct implications for what customers can print or export from their business units, access is governed by the platform's permission-based RBAC model ([rbac](/en/platform/rbac)): the backend catalog defines `report_template.read`, `report_template.create`, `report_template.update`, and `report_template.delete` keys; roles bundle those keys; and assignments bind roles to users.

The gating mechanism has three layers, all resolving through the same `AuthContext.hasPermission` → `checkPermission` path (algorithm walkthrough in [rbac permissions](/en/platform/rbac/permissions) §4). At the route level, `PrivateRoute` receives a `requiredPermission` prop and renders `<AccessDenied>` inside the normal `<Layout>` shell when the check fails. At the navigation level, `Layout.tsx` filters the sidebar so users without `report_template.read` never see the Report Templates entry. At the action level, `<Can permission="report_template.*">` wraps the mutating buttons on both report-templates screens. Unlike the cluster gates, **no report-template gate passes a `clusterId`** — report templates are tenant-global, so every check resolves through the broad branch with no per-cluster narrowing.

Until 2026-06 these routes were instead gated by a hardcoded role-enum array (`platform_admin`, `support_manager`, `support_staff`) duplicated across the three route guards; that model has been fully removed from the SPA, the login gate, and the Prisma schema — the migration mapping is documented in [rbac](/en/platform/rbac) §5 and is not repeated here.

## 2. Route guards

| Route | Component rendered | `requiredPermission` | Source |
|---|---|---|---|
| `/report-templates` | `ReportTemplateManagement` | `report_template.read` | `src/App.tsx` (report-templates route block, lines 156–179) |
| `/report-templates/new` | `ReportTemplateEdit` | `report_template.create` | `src/App.tsx` |
| `/report-templates/:id/edit` | `ReportTemplateEdit` | `report_template.update` | `src/App.tsx` |

Each route carries exactly one key. Unlike the legacy duplicated role arrays, the three keys are intentionally different per route, so the list, create, and edit surfaces can be granted independently — a read-only role that bundles only `report_template.read` is now expressible.

Three things to note:

- **Route guards check without a `clusterId`.** `PrivateRoute` calls `hasPermission(requiredPermission)` with no options, taking the broad "any scope grants it" branch. Because the in-page `<Can>` gates on this surface also omit `clusterId` (§7), a role assignment scoped to a single cluster whose role bundles `report_template.*` keys passes everywhere — there is no per-cluster narrowing anywhere on this surface. That is consistent with the data model: report templates are tenant-global and carry no cluster FK ([Data Model](./data-model.md) §3).
- **No route requires `report_template.delete`.** Deletion is reachable only through the list page's row action, gated in-page (§7).
- **No key reuse.** The `report_template.*` keys gate only this module — unlike the Business Units routes, which reuse the `cluster.*` keys (see [Clusters Permissions](../clusters/permissions.md) §2). The sibling [print-template-mapping](/en/platform/print-template-mapping) routes carry their own `print_template_mapping.*` keys; a grant on one module does not open the other.

## 3. Effective access matrix

Read the table as "what a session holding exactly this grant can do on the report-templates surfaces". Grants combine additively; a **super-admin** session (`is_super_admin` flag) bypasses every row and can do everything. SPA gates are advisory — the backend's own permission enforcement is the real security boundary.

| Grant held | `/report-templates` list | Add Template | Row Edit / edit page | Row Delete | Notes |
|---|---|---|---|---|---|
| None of `report_template.*` | `AccessDenied`; sidebar entry hidden | — | — | — | Can still type the URL; route guard catches |
| `report_template.read` | Full list, search, filters, CSV export | Hidden (header); empty-state Add still visible but leads to `AccessDenied` | Row Edit hidden; `/report-templates/:id/edit` route blocked | Hidden | Read-only persona; row-action menu renders empty |
| + `report_template.create` | — | Visible and functional | — | — | Create form is immediately editable once the route guard passes |
| + `report_template.update` | — | — | Row Edit on every row; edit route opens; Edit toggle renders | — | Unlocks the full edit form incl. XML editors, BU scope chips, Browse-in-BU probe |
| + `report_template.delete` | — | — | — | Row Delete renders | In-page only; no route requires this key |

Because no gate on this surface passes a `clusterId`, there is no scoped-grant row in this matrix — a cluster-scoped assignment behaves identically to a platform-scoped one here (§2). The bootstrap exception (§4) can override every column for any session while `userCount <= 1`.

## 4. Bootstrap exception

`hasPermission()` in `AuthContext.tsx` (lines 210–214) carries the first-admin shortcut forward from the legacy model: when `userCount !== null && userCount <= 1`, the function returns `true` unconditionally — every route guard, sidebar filter, and `<Can>` gate passes, including all report-template gates. Full implementation detail — how `userCount` is populated, the login-gate interaction, and the resolution pseudo-code — is in [rbac permissions](/en/platform/rbac/permissions) §4. The same caveats apply to report-templates:

- **During the API loading window** (`userCount === null`): the condition is `false`, so checks run strictly against the permission snapshot — the exception fails closed, not open. A session without `report_template.read` that visits `/report-templates` before the count fetch resolves sees `<AccessDenied>`.
- **Once `userCount > 1`**: the exception is dormant. The count refreshes only on mount and login — deleting users mid-session does not re-arm it until the next refresh.
- **Scope**: under the permission model the bootstrap branch also reaches the login gate — `login()` skips the must-hold-at-least-one-permission requirement when the user count is 0 or 1.

## 5. AccessDenied behaviour

Same as [Clusters Permissions §5](../clusters/permissions.md). `PrivateRoute` (`src/components/PrivateRoute.tsx`) implements two distinct rejection paths:

**Auth-fail (no session):** if `isAuthenticated` is `false`, the component renders `<Navigate to="/login" replace />` — a hard redirect that replaces the current history entry. The user ends up on the login page with no visible error in the current view.

**Permission-fail (authenticated but missing the key):** if `requiredPermission` is set and `hasPermission(requiredPermission)` returns `false`, the component renders `<AccessDenied />` (defined in the same file, lines 9–37), wrapped in `<Layout>` so the full sidebar and header remain visible. Inside the content area, a centred card displays a shield-X icon, the heading "Access Denied" in red, the generic message "You don't have permission to access this page.", and a "Back to Dashboard" button. Unlike the legacy version, the message no longer quotes the failing role — there is no single role value to display under the permission model.

Permission-fail users remain inside the SPA shell, can still use the sidebar to navigate to permitted pages, and are not logged out — their session stays valid.

## 6. Sidebar filter

`Layout.tsx` (line 56) defines the Report Templates nav item in the "Content" group as:

```
{ path: '/report-templates', label: 'Report Templates', icon: FileText, permission: 'report_template.read', group: 'Content' }
```

The full `allNavItems` array is filtered before rendering:

```
const navItems = allNavItems.filter(
  (item) =>
    (!item.permission || hasPermission(item.permission)) &&
    (!item.superAdminOnly || isSuperAdmin),
);
```

The sidebar `permission` value (`report_template.read`) matches the `/report-templates` route guard exactly, so there is no divergence where a visible entry leads to `AccessDenied`. The neighbouring **Print Mapping** entry (line 57) filters on its own `print_template_mapping.read` key — the two Content-group modules are independently grantable. Any future change to which key gates Report Templates must be applied in BOTH `src/App.tsx` (the route guard) AND `src/components/Layout.tsx` (the sidebar `permission` field); pulling one and not the other would expose the entry while blocking the route, or vice versa.

A user without `report_template.read` simply does not see the Report Templates entry. They can still reach `/report-templates` by typing the URL directly, but the route guard renders `<AccessDenied>` before any template data is loaded.

## 7. Within the report-templates surface

Unlike the legacy model, passing the route guard no longer unlocks every button — the mutating actions carry their own `<Can>` gates (added alongside the RBAC migration). None of them pass a `clusterId`:

| Action | In-page gate |
|---|---|
| View template list (pagination, search, filters) | None — route key (`report_template.read`) suffices |
| Export list as CSV | None — any `report_template.read` holder; disabled only while loading or empty |
| Add Template (header button) | `<Can permission="report_template.create">` |
| Add Template (empty-state button) | **Ungated** — renders for any `report_template.read` holder when the list is empty; the `report_template.create` route guard on `/report-templates/new` catches |
| Row Edit (list dropdown) | `<Can permission="report_template.update">` |
| Row Delete (list dropdown) | `<Can permission="report_template.delete">` |
| Edit toggle (edit page header) | `<Can permission="report_template.update">` |
| Save / Cancel on edit form | None — unreachable without the gated Edit toggle |
| XML editing + file upload (Dialog/Content tabs) | None — but `readOnly={!editing}`, so effectively behind the Edit toggle's `report_template.update` gate |
| Browse-in-BU probe (views/functions/procedures lookup) | None — rendered in edit mode only, so behind the Edit toggle |
| Standard / Custom and Active / Inactive checkboxes | None — rendered in edit mode only, so behind the Edit toggle |

Call sites: list-page gates in `ReportTemplateManagement.tsx` (row Edit lines 304–309, row Delete lines 310–315, Add Template lines 335–340); edit-page Edit toggle in `ReportTemplateEdit.tsx` (lines 360–365).

Tester-relevant consequences. First, a `report_template.read`-only session sees a fully read-only catalogue: the row-action dropdown renders but is empty, and the only escape hatch is the ungated empty-state Add button, which dead-ends at the route guard. Second, the `/report-templates/:id/edit` route opens for any `report_template.update` holder, but the page still starts in view mode — the in-page Edit toggle re-checks the same key, so route and toggle cannot disagree. Test plans should cover the per-key gates (§3) and the bootstrap exception (§4), not per-role differentiation — there are no role-enum personas anymore.

## 8. References

**Primary sources (read these before updating this page):**
- `../carmen-platform/src/App.tsx` — the three report-templates routes with `requiredPermission` props (route block lines 156–179).
- `../carmen-platform/src/context/AuthContext.tsx` — `hasPermission` (lines 210–214), `userCount` state, login permission gate.
- `../carmen-platform/src/utils/permissions.ts` — pure `checkPermission` resolution (super-admin → platform keys → cluster keys).
- `../carmen-platform/src/components/PrivateRoute.tsx` — auth-fail redirect, permission-fail `<AccessDenied>` render (component at lines 9–37).
- `../carmen-platform/src/components/Can.tsx` — the in-page gate component (`permission`, optional `clusterId`, optional `fallback`).
- `../carmen-platform/src/components/Layout.tsx` — sidebar `NavItem[]` with `permission` fields (Report Templates at line 56) and the filter expression.
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` / `ReportTemplateEdit.tsx` — the `<Can>` call sites listed in §7.

**Cross-links:**
- [rbac](/en/platform/rbac) — the permission model: catalog, roles, scoped assignments, super-admin flag, and the legacy-model migration table (§5)
- [rbac permissions](/en/platform/rbac/permissions) — SPA-wide gate matrix and the full permission-resolution algorithm
- [users](/en/platform/users) — user identity rows that role assignments point at
- [Clusters Permissions](../clusters/permissions.md) — sibling permissions page; documents the cluster-scoped `<Can clusterId>` variant this surface does *not* use
- [print-template-mapping](/en/platform/print-template-mapping) — sibling Content-group module with its own `print_template_mapping.*` keys
- [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [XML Spec](./xml-spec.md) — sibling sub-pages
