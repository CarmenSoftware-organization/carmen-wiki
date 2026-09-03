---
title: Report Template — Permissions
description: Permission-key route guards, in-page Can gates, sidebar filter, and bootstrap exception for the report-templates surface. Updated for the Forbidden rename and the removal of the neighbouring print-template-mapping module.
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, report-templates, permissions
editor: markdown
dateCreated: '2026-05-19T18:30:00.000Z'
---

# Report Template — Permissions

> **At a Glance**
> **Gate:** the three report-templates routes carry `requiredPermission="report_template.read"` / `"report_template.create"` / `"report_template.update"` on `PrivateRoute` (`src/App.tsx`, report-templates route block) &nbsp;·&nbsp; **In-page gates:** `<Can>` wraps Add Template (`report_template.create`), row Edit (`report_template.update`), row Delete (`report_template.delete`), and the edit-page Edit toggle (`report_template.update`) — none pass a `clusterId` &nbsp;·&nbsp; **`report_template.delete` is in-page only** — no route requires it &nbsp;·&nbsp; **Bootstrap exception:** `hasPermission` returns `true` unconditionally when `userCount !== null && userCount <= 1` &nbsp;·&nbsp; **On failure:** the `Forbidden` page (`src/pages/Forbidden.tsx`, renamed from an inline `AccessDenied`) renders in place inside `<Layout>` (sidebar stays visible) &nbsp;·&nbsp; **Since 2026-07-23:** the same `report_template.*` keys also gate the new Form Groups screen (`/report-form-groups`); the sibling `print_template_mapping.*` keys this page used to reference no longer exist (module removed) &nbsp;·&nbsp; **Canonical model doc:** [rbac permissions](/en/platform/rbac/permissions)

## 1. Overview

Report Templates is a Carmen-internal authoring surface for printable and exportable documents that ship as part of the platform's customisation contract. Templates are authored by Carmen support engineers — not customers — using a structured XML/FastReport editor with database-source binding against tenant schemas. Because authoring a template requires platform-level operational knowledge and carries direct implications for what customers can print or export from their business units, access is governed by the platform's permission-based RBAC model ([rbac](/en/platform/rbac)): the backend catalog defines `report_template.read`, `report_template.create`, `report_template.update`, and `report_template.delete` keys; roles bundle those keys; and assignments bind roles to users.

The gating mechanism has three layers, all resolving through the same `AuthContext.hasPermission` → `checkPermission` path (algorithm walkthrough in [rbac permissions](/en/platform/rbac/permissions) §4). At the route level, `PrivateRoute` receives a `requiredPermission` prop and renders the `Forbidden` page in place inside the normal `<Layout>` shell when the check fails (renamed from an inline `AccessDenied` component — see §5). At the navigation level, `Layout.tsx` filters the sidebar so users without `report_template.read` never see the Report Templates entry. At the action level, `<Can permission="report_template.*">` wraps the mutating buttons on the report-templates screens (and, since 2026-07-23, the new Form Groups screen — §7). Unlike the cluster gates, **no report-template gate passes a `clusterId`** — report templates are tenant-global, so every check resolves through the broad branch with no per-cluster narrowing.

Until 2026-06 these routes were instead gated by a hardcoded role-enum array (`platform_admin`, `support_manager`, `support_staff`) duplicated across the three route guards; that model has been fully removed from the SPA, the login gate, and the Prisma schema — the migration mapping is documented in [rbac](/en/platform/rbac) §5 and is not repeated here.

## 2. Route guards

| Route | Component rendered | `requiredPermission` | Source |
|---|---|---|---|
| `/report-templates` | `ReportTemplateManagement` | `report_template.read` | `src/App.tsx` (report-templates route block) |
| `/report-templates/new` | `ReportTemplateEdit` | `report_template.create` | `src/App.tsx` |
| `/report-templates/:id/edit` | `ReportTemplateEdit` | `report_template.update` | `src/App.tsx` |
| `/report-form-groups` | `ReportFormGroupManagement` | `report_template.read` | **Added 2026-07-23.** `src/App.tsx`; not one of the three routes this page originally documented, but gated by the same key family — see §7 |

Each route carries exactly one key. Unlike the legacy duplicated role arrays, the three original keys are intentionally different per route, so the list, create, and edit surfaces can be granted independently — a read-only role that bundles only `report_template.read` is now expressible.

Four things to note:

- **Route guards check without a `clusterId`.** `PrivateRoute` calls `hasPermission(requiredPermission)` with no options, taking the broad "any scope grants it" branch. Because the in-page `<Can>` gates on this surface also omit `clusterId` (§7), a role assignment scoped to a single cluster whose role bundles `report_template.*` keys passes everywhere — there is no per-cluster narrowing anywhere on this surface. That is consistent with the data model: report templates are tenant-global and carry no cluster FK ([Data Model](./data-model.md) §3).
- **No route requires `report_template.delete`.** Deletion is reachable only through the list page's row action, gated in-page (§7).
- **No key reuse.** The `report_template.*` keys gate only this module (now including Form Groups) — unlike the Business Units routes, which reuse the `cluster.*` keys (see [Clusters Permissions](../clusters/permissions.md) §2).
- **Removed 2026-07-23/24:** the sibling `print-template-mapping` module and its `print_template_mapping.*` keys no longer exist — that module has been deleted outright (see [print-template-mapping](/en/platform/print-template-mapping), historical page), not merely disconnected from this one.

## 3. Effective access matrix

Read the table as "what a session holding exactly this grant can do on the report-templates surfaces". Grants combine additively; a **super-admin** session (`is_super_admin` flag) bypasses every row and can do everything. SPA gates are advisory — the backend's own permission enforcement is the real security boundary.

| Grant held | `/report-templates` list | Add Template | Row Edit / edit page | Row Delete | Notes |
|---|---|---|---|---|---|
| None of `report_template.*` | `Forbidden`; sidebar entry hidden | — | — | — | Can still type the URL; route guard catches |
| `report_template.read` | Full list, search, filters, CSV export | Hidden (header); empty-state Add still visible but leads to `Forbidden` | Row Edit hidden; `/report-templates/:id/edit` route blocked | Hidden | Read-only persona; row-action menu renders empty |
| + `report_template.create` | — | Visible and functional | — | — | Create form is immediately editable once the route guard passes |
| + `report_template.update` | — | — | Row Edit on every row; edit route opens; Edit toggle renders | — | Unlocks the full edit form incl. XML editors, BU scope chips, Browse-in-BU probe |
| + `report_template.delete` | — | — | — | Row Delete renders | In-page only; no route requires this key |

Because no gate on this surface passes a `clusterId`, there is no scoped-grant row in this matrix — a cluster-scoped assignment behaves identically to a platform-scoped one here (§2). The bootstrap exception (§4) can override every column for any session while `userCount <= 1`.

## 4. Bootstrap exception

`hasPermission()` in `AuthContext.tsx` (lines 210–214) carries the first-admin shortcut forward from the legacy model: when `userCount !== null && userCount <= 1`, the function returns `true` unconditionally — every route guard, sidebar filter, and `<Can>` gate passes, including all report-template gates. Full implementation detail — how `userCount` is populated, the login-gate interaction, and the resolution pseudo-code — is in [rbac permissions](/en/platform/rbac/permissions) §4. The same caveats apply to report-templates:

- **During the API loading window** (`userCount === null`): the condition is `false`, so checks run strictly against the permission snapshot — the exception fails closed, not open. A session without `report_template.read` that visits `/report-templates` before the count fetch resolves sees `Forbidden`.
- **Once `userCount > 1`**: the exception is dormant. The count refreshes only on mount and login — deleting users mid-session does not re-arm it until the next refresh.
- **Scope**: under the permission model the bootstrap branch also reaches the login gate — `login()` skips the must-hold-at-least-one-permission requirement when the user count is 0 or 1.

## 5. Forbidden (renamed from AccessDenied)

Same mechanism as [Clusters Permissions §5](../clusters/permissions.md). `PrivateRoute` (`src/components/PrivateRoute.tsx`, 40 lines) implements two distinct rejection paths:

**Auth-fail (no session):** if `isAuthenticated` is `false`, the component renders `<Navigate to="/login" replace />` — a hard redirect that replaces the current history entry. The user ends up on the login page with no visible error in the current view.

**Permission-fail (authenticated but missing the key):** if `requiredPermission` is set and `hasPermission(requiredPermission)` returns `false`, the component renders `<Forbidden />` **in place** — a dedicated page component (`src/pages/Forbidden.tsx`), no longer an `AccessDenied` component defined inline inside `PrivateRoute.tsx` as the last sync described. Rendering in place (rather than redirecting to `/403`) keeps the blocked URL in the address bar, so the page's own "Go Back" action doesn't bounce off the guard. Wrapped in `<Layout>` so the full sidebar and header remain visible, it shows a `ShieldX` icon, "403", the heading "Access Denied", the generic message "You don't have permission to access this page.", and now **two** actions — "Go Back" (context-aware, falls back to `/dashboard`) and "Go to Dashboard" — where the previous sync described only a single Back-to-Dashboard button. A direct `/403` route renders the same page. The message still does not quote the failing role — there is no single role value to display under the permission model.

Permission-fail users remain inside the SPA shell, can still use the sidebar to navigate to permitted pages, and are not logged out — their session stays valid.

## 6. Sidebar filter

`Layout.tsx` defines the Report Templates nav item in the "Content" group as:

```
{ path: '/report-templates', label: 'Report Templates', icon: FileText, permission: 'report_template.read', group: 'Content' }
```

**Added 2026-07-23**, immediately below it: `{ path: '/report-form-groups', label: 'Form Groups', icon: LayoutGrid, permission: 'report_template.read', group: 'Content' }` — the Form Groups screen reuses the same sidebar-filter key.

The full `allNavItems` array is filtered before rendering:

```
const navItems = allNavItems.filter(
  (item) =>
    (!item.permission || hasPermission(item.permission)) &&
    (!item.superAdminOnly || isSuperAdmin),
);
```

The sidebar `permission` value (`report_template.read`) matches the `/report-templates` route guard exactly, so there is no divergence where a visible entry leads to `Forbidden`. **Removed 2026-07-24:** the previously-neighbouring **Print Mapping** entry (which filtered on its own `print_template_mapping.read` key) no longer exists — the module was deleted, not merely regrouped. Any future change to which key gates Report Templates must be applied in BOTH `src/App.tsx` (the route guard) AND `src/components/Layout.tsx` (the sidebar `permission` field); pulling one and not the other would expose the entry while blocking the route, or vice versa.

A user without `report_template.read` simply does not see the Report Templates or Form Groups entries. They can still reach `/report-templates` by typing the URL directly, but the route guard renders `Forbidden` before any template data is loaded.

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
| **Form Groups screen** (`/report-form-groups`) — set group default | `<Can>` not used here; the "Set default" action is available to any `report_template.update` holder (button visibility on the screen is driven by `hasPermission`, not a `<Can>` wrapper) — **added 2026-07-23**, gated by the same key family as the rest of this module |
| **Form Groups screen** — "New Form Template" button | Visible only when `report_template.create` is held |

Call sites: list-page gates in `ReportTemplateManagement.tsx` (row Edit/Delete `<Can>` wraps in the `actions` column definition, Add Template in the `PageHeader` actions); edit-page Edit toggle in `ReportTemplateEdit.tsx` (header `actions`, gated when `!editing`).

Tester-relevant consequences. First, a `report_template.read`-only session sees a fully read-only catalogue: the row-action dropdown renders but is empty, and the only escape hatch is the ungated empty-state Add button, which dead-ends at the route guard. Second, the `/report-templates/:id/edit` route opens for any `report_template.update` holder, but the page still starts in view mode — the in-page Edit toggle re-checks the same key, so route and toggle cannot disagree. Test plans should cover the per-key gates (§3) and the bootstrap exception (§4), not per-role differentiation — there are no role-enum personas anymore. **Removed 2026-07-23/24:** any test plan referencing `print_template_mapping.*` keys is testing a module that no longer exists.

## 8. References

**Primary sources (read these before updating this page):**
- `../carmen-platform/src/App.tsx` — the report-templates + Form Groups routes with `requiredPermission` props.
- `../carmen-platform/src/context/AuthContext.tsx` — `hasPermission`, `userCount` state, login permission gate.
- `../carmen-platform/src/utils/permissions.ts` — pure `checkPermission` resolution (super-admin → platform keys → cluster keys).
- `../carmen-platform/src/components/PrivateRoute.tsx` — auth-fail redirect, permission-fail render (40 lines total).
- `../carmen-platform/src/pages/Forbidden.tsx` — the renamed 403 page.
- `../carmen-platform/src/components/Can.tsx` — the in-page gate component (`permission`, optional `clusterId`, optional `fallback`).
- `../carmen-platform/src/components/Layout.tsx` — sidebar `NavItem[]` with `permission` fields (Report Templates + Form Groups, both `report_template.read`) and the filter expression.
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` / `ReportTemplateEdit.tsx` / `ReportFormGroupManagement.tsx` — the `<Can>` / `hasPermission` call sites listed in §7.

**Cross-links:**
- [rbac](/en/platform/rbac) — the permission model: catalog, roles, scoped assignments, super-admin flag, and the legacy-model migration table (§5)
- [rbac permissions](/en/platform/rbac/permissions) — SPA-wide gate matrix and the full permission-resolution algorithm
- [users](/en/platform/users) — user identity rows that role assignments point at
- [Clusters Permissions](../clusters/permissions.md) — sibling permissions page; documents the cluster-scoped `<Can clusterId>` variant this surface does *not* use
- [print-template-mapping](/en/platform/print-template-mapping) — **removed 2026-07-23/24** (historical page); used to be a sibling Content-group module with its own `print_template_mapping.*` keys, now gone
- [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [XML Spec](./xml-spec.md) — sibling sub-pages
