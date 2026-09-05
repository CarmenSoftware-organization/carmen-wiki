---
title: User Platform — UI Screens
description: UserPlatformManagement's filter-consistent registry (PlatformAccessSummary, RoleChips, Grant Access) and UserPlatformEdit's per-holder dossier (AccessReachBand, RoleGrantList, MembershipCard) — plus the two ways the user-platform e2e suite no longer matches this UI.
published: true
date: '2026-09-06T19:00:00.000Z'
tags: book/platform, user-platform, ui
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# User Platform — UI Screens

> **At a Glance**
> **Screens:** `UserPlatformManagement` (`/platform/user-platform`) &nbsp;·&nbsp; `UserPlatformEdit` (`/platform/user-platform/:userId`, no `/edit` suffix — see [Landing](/en/platform/user-platform) §1) &nbsp;·&nbsp; **Shared shell:** `Layout`, `PageHeader`, a dev-only `DevDebugSheet` on both screens, `useGlobalShortcuts` &nbsp;·&nbsp; **e2e suite:** `user-platform` (2 specs, `../carmen-platform-e2e`, HEAD `a8e3b31`, 2026-08-25) — **both specs predate the 2026-09-02 rewrite and no longer match current markup**; see §4

## 1. Overview

Both screens follow this book's usual Management/Edit shape but neither is a form: `UserPlatformManagement` is a registry list with no create-a-record action (Grant Access assigns roles to an existing user; it does not create one), and `UserPlatformEdit` has no edit-mode toggle — every action on it (add a role, remove a role) writes immediately, there is nothing to "Save." Both share a `TableSkeleton`/`Skeleton` loading treatment rather than a spinner, a dev-only `DevDebugSheet` exposing the raw API response, and `useGlobalShortcuts` for search-focus (list) or save/cancel (the Add Role sheet).

Both screens reuse the same small vocabulary for "how far does this privilege reach": `ScopeRail` (a thin coloured bar, filled for platform-wide, outlined for cluster-scoped) and the "Platform-wide"/cluster-name label pairing, defined once in `userPlatformManagement/roleChips.tsx` and imported by both `userPlatformEdit/AccessReachBand.tsx` and `userPlatformEdit/RoleGrantList.tsx`. A reviewer moving from the list to one holder's page reads the same visual language on both, not two independently designed ones.

## 2. `UserPlatformManagement` — registry (`/platform/user-platform`)

A server-side `DataTable` (`serverSide`, `tableLayout="auto"`) whose four columns are, in order: **User** (avatar-free — a name/username line plus a de-duplicated email line, an `Inactive` badge when applicable), **Roles & scope** (`RoleChips` — assignments grouped by scope, platform-wide group first, each group's scope name written once beside its role badges, not repeated per badge), **Granted** (relative time + absolute-timestamp tooltip for the *most recently created* assignment, plus that grant's issuer — per-assignment attribution lives only on the detail page), and a row-actions column (kebab menu: **Manage roles** — no RBAC permission key on the menu item itself, gated instead by the detail route's own `user_platform.read` guard, which every viewer of this list already holds; **Revoke all access**, gated `<Can permission="user_platform.manage">`, only for holders with roles to revoke).

Above the table, **`PlatformAccessSummary`** renders the registry-wide aggregate ([Landing](/en/platform/user-platform) §3.1): a large holder count, a proportional platform-wide/cluster-scoped bar (decorative — every number it encodes is also written in the legend beneath it), and a clickable inactive-holder warning that applies the inactive filter. The platform-wide legend entry is also clickable (toggles the `cluster_id: null` filter); the cluster-scoped entry is a plain stat, deliberately not a control — the component's own comment explains why: an "any cluster" filter would need a `{ not: null }` query the backend has never been sent, so a control that might silently filter nothing was rejected in favor of one that plainly reads as a stat.

Standard chrome below that: debounced search (username/email), a Filters sheet (status, role — multi-select buttons sourced from `roleService.getAll()`, best-effort, falls back to raw role ids if that fetch fails — and scope, a `<select>` of "Any scope" / "Platform-wide" / one option per cluster from `clusterService.getAll()`), active-filter chips with individual and clear-all removal, and CSV export. Export is **per-assignment, not per-holder** — a user with three roles produces three CSV rows, one per role/scope pair, because "a spreadsheet cell can't filter on several roles at once" (the code's own comment); columns are username, email, status, role, scope, granted-at, granted-by.

**Grant Access** (header button and the empty-state's call-to-action, both `<Can permission="user_platform.manage">`) opens `GrantAccessDialog`: a `UserPicker` typeahead (searches `GET /api-system/user`, gated `user.read` on the backend — see [Permissions](/en/platform/user-platform/permissions) §3), a checkbox list of platform roles, and one shared scope (Platform-wide or a specific cluster) applied to every checked role at once via `POST .../roles/bulk`. A 409 from an already-granted role is matched back to its checkbox by a simple substring test against the error message (`roleOptions.filter(r => message.includes(r.name))`) and marked in red — a display nicety, not a validation the backend itself performs role-by-role.

**Revoke all access** has no dedicated bulk-revoke endpoint on the backend: it is a sequential client-side loop over `DELETE .../roles/:assignmentId`, one call per assignment, that reports honestly which ones failed rather than claiming a blanket success (`handleRevokeAll`, `UserPlatformManagement.tsx:248-262`). A partial failure leaves the holder with whatever roles did not fail to remove — the page simply refetches and shows the result, rather than retrying or rolling back the ones that succeeded.

## 3. `UserPlatformEdit` — per-holder dossier (`/platform/user-platform/:userId`)

Reached with `backTo="/platform/user-platform"` in the header. The page header itself carries the account's own audit line (`normalizeAudit(userRecord)` — created/updated on the `tb_user` row) plus, in its actions slot, an `Inactive` badge when the account is deactivated and an "Email not verified" badge when `email_verified_at` is falsy ([Landing](/en/platform/user-platform) §3.3) — both purely informational, neither is a control.

Below the header, in order:

1. **A mid-session error banner**, shown whenever the account/role fetch fails — see [Permissions](/en/platform/user-platform/permissions) §3 for exactly when and why, and what the rest of the page looks like when it does.
2. **An inactive-holder warning** (`!isActive && roleAssignments.length > 0`) — the per-holder counterpart to the registry's inactive count, present specifically so a reviewer who opened one person's page directly (not via the registry's warning link) still cannot miss it.
3. **`AccessReachBand`** — the page's headline: "Reaches the entire platform" / "Reaches N cluster(s), listed by name" / "No platform privilege," plus a total assignment count, in the same `ScopeRail` vocabulary as the list.
4. **The "Roles & Scope" card** — `RoleGrantList`, assignments grouped by scope (platform-wide first; a lone platform-wide group's heading is suppressed since the reach band already said it), each row showing the role name, who granted it and when where that is known, a "Self-granted" warning badge when the grantor is the holder themselves, and a per-row **Remove** button (`<Can permission="user_platform.manage">`). The card header's **Add Role** control (`AddRoleSheet`, same permission) is a side sheet, not an inline panel — a Role `<select>`, a Scope `<select>` (Platform-wide / Specific cluster, the latter revealing a Cluster `<select>`), and Add/Cancel buttons, with `Ctrl/⌘+S`/`Escape` wired through `useGlobalShortcuts` and an unsaved-changes guard keyed on "has any field been touched" (no saved baseline to diff against, since nothing is being edited — it's a one-shot create form).
5. **`MembershipCard`** — where the holder sits in the tenant tree (clusters and business units, each with an active/inactive badge), captioned explicitly as "not platform privilege": it exists so a reviewer can sanity-check whether a cluster-scoped grant lines up with where the person actually works, not to duplicate the reach band.

**Grant provenance is best-effort and explicitly labelled when it is missing.** The per-user roles endpoint (`GET .../roles`) returns no actor/timestamp for each assignment; that only comes from the registry list endpoint's audit enrichment. `UserPlatformEdit` re-queries the registry by the holder's own email/username (`loadProvenance`, matched on `user_id`, never on search-result position) purely to backfill this — a failure there is non-fatal and every row falls back to an explicit "Grant history unavailable" line rather than a blank, so an unenriched grant is never visually confused with an attributed one showing nobody.

## 4. The e2e suite predates this UI — two concrete mismatches, not a general caution

`../carmen-platform-e2e/tests/user-platform/` has two specs, last touched `a8e3b31` (2026-08-25) — eight days before the 2026-09-02 rewrite (`fc690cb`/`f6e91c9`) this page documents. Per this plan's standing rule, an e2e suite is not automatically evidence; reading the page objects against current source confirms two specific ways this one is stale, not just a generic "might have drifted":

- **`user-platform-list.spec.ts`'s own annotation states "no Add button by design"**, and its page object (`pages/UserPlatformManagementPage.ts`) carries a doc-comment: "NO Add button (users are created on /users; this page only assigns roles). The inherited `addButton`/`clickAdd` must never be used." Current source has a **Grant Access** button (`<Plus>` icon, header and empty state, §2 above), gated `<Can permission="user_platform.manage">`. The suite authenticates as a super admin (its own precondition), and `hasPermission()` (`AuthContext.tsx:268-272`) delegates to `checkPermission()`, whose first check is `if (eff?.is_super_admin) return true` (`utils/permissions.ts:56`) — so that session sees the button rendered. The test does not assert its *absence*, so it would not fail outright on this point alone — but the documented expectation is false against current source.
- **The same page object's `openUser`/`openFirstNonLoginUser` click `row.locator('button').first()`, on the stated assumption that the username cell is "a BUTTON... not an `<a>`."** Current source renders the username as a react-router `<Link>` (an `<a>` tag, `UserPlatformManagement.tsx:316-321`); the only actual `<button>` element inside a data row is the row-actions kebab menu trigger (confirmed by reading `data-table.tsx`: the row-index cell is plain text, no selection checkbox is enabled on this table, and the sort-toggle buttons live in `<thead>`, outside a row's scope). Clicking `row.locator('button').first()` today opens that dropdown menu, not the detail page — both specs that depend on this helper (`user-platform-list.spec.ts`'s navigation test and the whole of `user-platform-config.spec.ts`, which reaches the detail page exclusively through it) would fail at this step, not later.
- **`user-platform-config.spec.ts`'s page object (`pages/UserPlatformEditPage.ts`) expects "Add Role" to reveal an inline panel**, `div.rounded-md.border.p-3.space-y-3`, containing the Role/Scope `<select>` elements directly. Current source's `AddRoleSheet` is a `Sheet` (`side="right"`, `className="w-full p-4 sm:max-w-sm sm:p-6"`) whose inner content div is `mt-6 space-y-4 px-1` — no matching `rounded-md border p-3 space-y-3` element exists anywhere in it. The page object's `addPanel` locator resolves to nothing against current markup, so `roleSelect`/`scopeSelect` (both scoped under `addPanel`) would find nothing and `assignFirstAvailableRole()` would time out, not merely render differently.

Net effect: the "renders title and a non-empty user table" smoke test in `user-platform-list.spec.ts` likely still passes (heading, row count, search/filter/export chrome are unchanged), but every other test in both files depends on one of the two broken helpers above. Treat this suite as **not usable as current evidence** for either screen's interactive behavior; every claim on this page and [Permissions](/en/platform/user-platform/permissions) is sourced from `../carmen-platform`/`../carmen-turborepo-backend-v2` implementation directly, not from this suite.

## 5. Reference Sources

All paths `../carmen-platform` (HEAD `157a65e`) unless prefixed `../carmen-turborepo-backend-v2` (HEAD `937cf5ac4`) or `../carmen-platform-e2e` (HEAD `a8e3b31`).

- `src/pages/UserPlatformManagement.tsx` (commit `fc690cb`) — list screen, columns, filters, export, revoke-all loop (lines 248-262).
- `src/pages/userPlatformManagement/{PlatformAccessSummary,roleChips,GrantAccessDialog}.tsx` — summary band, `ScopeRail`/`RoleChips`, grant dialog.
- `src/pages/UserPlatformEdit.tsx` (commit `f6e91c9`) — detail screen, header badges, error/warning banners.
- `src/pages/userPlatformEdit/{AccessReachBand,RoleGrantList,MembershipCard,AddRoleSheet}.tsx` — reach band, grant list with provenance, membership card, add-role sheet.
- `src/components/ui/data-table.tsx:181-230,325-395` — row/column structure cited in §4 to establish which elements are actually `<button>`s.
- `src/components/Can.tsx`, `src/context/AuthContext.tsx:268-272`, `src/utils/permissions.ts:56` — `<Can>`'s render-nothing-on-false behavior and the super-admin short-circuit cited in §4.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/user_platform_role/user_platform_role.service.ts` — `assign`/`assignBulk`/`remove` backing every write on both screens.
- `../carmen-platform-e2e/tests/user-platform/{user-platform-list,user-platform-config}.spec.ts`, `pages/UserPlatform{ManagementPage,EditPage}.ts` — the stale suite discussed in §4.

**Cross-links:** [User Platform landing](/en/platform/user-platform) &nbsp;·&nbsp; [Permissions](/en/platform/user-platform/permissions) &nbsp;·&nbsp; [Users](/en/platform/users) &nbsp;·&nbsp; [Platform RBAC](/en/platform/rbac)
