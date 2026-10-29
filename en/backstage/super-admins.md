---
title: Super Admins
description: The platform's god-mode allowlist — SuperAdminManagement (/backstage/super-admins), gated by superAdminOnly with no RBAC permission key at all, and its three-column tb_backstage_super_admin table.
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, super-admins
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Super Admins

> **At a Glance**
> **Screen:** `SuperAdminManagement` (`/backstage/super-admins`) — a card-based roster (one `<ul>`/`<li>` per person), not a `DataTable` &nbsp;·&nbsp; **The gate:** **no RBAC permission key at all** — the nav entry and the route are both `superAdminOnly: true`, checked against `isSuperAdmin` (derived from `effectivePermissions.is_super_admin`), never against a permission string &nbsp;·&nbsp; **Nav:** `feature: 'super_admins'`, `dividerBefore: true` — the divider marks where the sidebar stops being day-to-day configuration and starts being "who else can reach configuration" &nbsp;·&nbsp; **Backend enforcement:** all three endpoints (`GET`/`POST`/`DELETE /api-system/backstage/super-admins`) sit behind `BackstageSuperAdminGuard`, which re-resolves `is_super_admin` from the database on every single request — no cache anywhere in the chain &nbsp;·&nbsp; **Table:** `tb_backstage_super_admin` — three meaningful columns (`user_id`, `is_active`, `current_business_unit_id`) beyond the audit columns, documented in full below (§5) rather than on a separate `data-model` page &nbsp;·&nbsp; **e2e suite:** `super-admins` (1 spec, HEAD `bb8f671`, 2026-06-11) — predates the 2026-09-02 card-roster rewrite and fails at the shared test fixture itself, not merely in individual assertions (§6)

![Super Admins screen](/screenshots/platform/super-admins/index.png)

## 1. Overview

Super Admins is the one screen in the Backstage product whose entire purpose is to control who can reach every other screen. Its nav entry (`../carmen-backstage/src/components/nav/backstageNav.ts:51`) reads:

```
{ path: '/backstage/super-admins', labelKey: 'nav.superAdmins', icon: ShieldAlert,
  superAdminOnly: true, groupKey: 'navGroup.backstage', feature: 'super_admins', dividerBefore: true }
```

There is no `permission` field on this row at all. Every other row in the sidebar is filtered by `!item.permission || opts.hasPermission(item.permission)` (`backstageNav.ts:118`); this one is filtered by `!item.superAdminOnly || opts.isSuperAdmin` (`backstageNav.ts:119`) instead — a boolean, not a permission-string lookup. The two comment lines immediately above the row (`backstageNav.ts:49-50`, Thai) state the reason for the divider directly: *"the divider separates these two bottom rows from day-to-day configuration work — both of them change what other people can access. Not made a new group, because it's still about Backstage — just a different risk level."* The route (`../carmen-backstage/src/App.tsx:489-496`) is wrapped the same way, in `<PrivateRoute requireSuperAdmin feature="super_admins">`.

The honest way to describe this gate — and the one this page uses throughout — is **"no RBAC permission key — the menu entry and route are `superAdminOnly`,"** not "no permission check at all." The check is real and it runs twice: once in `PrivateRoute` (`../carmen-backstage/src/components/PrivateRoute.tsx:89-91`, `if (requireSuperAdmin && !isSuperAdmin) return <Forbidden />`, evaluated after the platform-authority resolution branch and before the feature-flag check at lines 96-105 — the same permission-before-flag ordering every other gated route in this book follows), and independently again on every backend request. What is genuinely absent is a permission *key*: nothing in `tb_backstage_permission` names this capability, so no role bundle can be granted or denied access to it — the only way in is to already hold the allowlist row this page manages.

`isSuperAdmin` itself is `!!effectivePermissions?.is_super_admin` (`../carmen-backstage/src/context/AuthContext.tsx:342`), and `effectivePermissions` is fetched once on page mount and once per sign-in (password login or Google sign-in) (`fetchEffectivePermissions()`, called at `AuthContext.tsx:87`, `:185` and — for Google sign-in — `:289`) — not polled. §5.4 covers what that caching means for a session that is already open when someone's row is removed.

On the backend, `BackstageSuperAdminsController` (`../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage-super-admins/backstage-super-admins.controller.ts:63-65`) applies `@UseGuards(KeycloakGuard, BackstageSuperAdminGuard)` at the controller level, so `list`, `add`, and `remove` are all gated identically. `BackstageSuperAdminGuard.canActivate` (`../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/backstage-super-admin.guard.ts:44-76`) makes a fresh TCP call to `BackstagePermissions.effective` on every invocation and fails closed — a thrown error or a non-OK response denies the request (lines 55-68) — rather than falling back to a cached or default value. This means **the API itself requires an existing super admin to manage the allowlist**, a bootstrapping consequence covered in §5.2.

## 2. Business Context

A row in `tb_backstage_super_admin` is a bypass, not a bundle of grants. Two independent short-circuits key off it:

- **Frontend:** `checkPermission()` (`../carmen-backstage/src/utils/permissions.ts:56`) — `if (eff?.is_super_admin) return true;` — before it ever consults `eff.platform` or `eff.clusters`. Every `hasPermission()`/`<Can>` check in the SPA passes through this function.
- **Backend:** `BackstagePermissionGuard.canActivate` (`../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/backstage-permission.guard.ts:110`) — `if (eff?.is_super_admin === true) return true;` — a strict-equality check the guard's own comment says must match the analytics scope filter exactly, "or a stray value like `\"false\"` or `1` could give the guard and the data filter different answers." This is the guard behind every `@RequireBackstagePermission` decorator in the backend gateway — i.e. behind essentially every RBAC-gated platform route in the product.

This is exactly what the screen's own subtitle says: *"Backstage users who bypass all permission checks"* (`pages.superAdmins.subtitle`, `../carmen-backstage/src/i18n/en.ts:4091`). The screen exists so that a small, auditable allowlist — not a role, not a permission bundle — is the single place that answers "who currently has god mode." Granting it is appropriate for platform engineering/support staff who need unconditional access across every cluster and business unit; it is not a substitute for an RBAC role bundle for anyone whose job is scoped to specific resources.

## 3. Key Concepts

### 3.1 The Roster Screen

`SuperAdminManagement` (`../carmen-backstage/src/pages/SuperAdminManagement.tsx`) fetches `GET /api-system/backstage/super-admins` on mount (`fetchData`, lines 90-105) and renders one `<Card>` containing a `<ul className="divide-y">` of `<li>` rows (lines 284-293) — not a `DataTable`. Each row (`RosterRow`, lines 391-466) shows an avatar with up-to-two-letter initials, the person's resolved name or email (falling back to an em dash, deliberately never to a phrase like "Unknown user" — the component's own comment explains why: a frontend deployed ahead of a backend that hasn't joined these fields yet would otherwise make every row read as though its user had been deleted, lines 28-32), the raw `user_id` UUID, an Active/Inactive badge, and a "Granted `<relative time>`" line.

A search box (`SearchInput`) only appears once the roster exceeds `SEARCH_THRESHOLD = 8` rows (line 57) — the component's own comment states the reasoning: "a roster this short is read, not searched... below that it is a control that never gets used" (lines 54-56). The header subtitle states a consequence rather than a description: while data is loading with nothing on screen yet it shows the generic subtitle, otherwise it states the exact headcount ("One person on this platform bypasses every permission check" / "`{count}` people... bypass every permission check", lines 201-207) — the one fact an operator visits this page to check.

An **Export** button (header, disabled while loading or empty) downloads a CSV of every visible row — user, email, `user_id`, status, and the four audit columns (`created_at`/`created_by`/`updated_at`/`updated_by`) via `auditCsvFields(normalizeAudit(r))` (lines 179-199). A `DevDebugSheet` (line 377) exposes the raw `GET` response for local debugging.

**A real, verified gap in the audit trail:** the per-row "Granted" line (`AuditMeta` with `verbKey="pages.superAdmins.grantedVerb"`, line 451-455) can only ever show a relative timestamp, never a name, and this is not a frontend rendering limit — the name was never captured. `backstage_super_admin.service.ts`'s own `add()` (`../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_super_admin/backstage_super_admin.service.ts:133-138`) and the bootstrap seed script's `create()` call (`packages/prisma-shared-schema-backstage/prisma/seed.backstage-super-admin.ts:29-34`) both write only `{ user_id, is_active: true }` — neither sets `created_by_id`. A repository-wide search for any code that writes to `created_by_id` found none outside this one absent write path; the log-events Prisma middleware (`packages/log-events-library/src/middleware/prisma-audit.middleware.ts`) writes a separate append-only audit-event stream, not this column. The gateway's `@EnrichAuditUsers()` mechanism (`apps/backend-gateway/src/common/enrichment/audit-shape.ts:2,4-7`, `AUDIT_BY_ID_FIELDS = ['created_by_id', ...]`) can only resolve a name from a `created_by_id` it is actually given, so `audit.created` ends up carrying only `.at` — exactly what the frontend's own `SuperAdmin` type comment already anticipates ("gateway's `@EnrichAuditUsers()` nests `created_at` here as `audit.created.at`," `../carmen-backstage/src/types/index.ts:1136`). The same is true in the other direction: `remove()`'s `update()` call (service.ts:163-166) sets only `deleted_at`, never `deleted_by_id` — so the record of *who* deactivated a super admin is not captured either, only *when*.

### 3.2 Adding a Super Admin

The header's **Add Super Admin** button opens a `Dialog` containing a `UserPicker` typeahead (server-side search via `useUserSearch`), not the plain `<select>` an earlier build once used. Users who already hold the privilege are shown disabled in the picker rather than allowed through to a predictable 409 (`superAdminUserIds` memo, `SuperAdminManagement.tsx:113-116`). `handleAdd` (lines 138-164) calls `POST /api-system/backstage/super-admins` with `{ user_id }`; on a `409` specifically it clears the stale selection and refetches, on the reasoning that a 409 here means someone else granted the same user the privilege first, so the list on screen is provably stale (lines 151-160) — any other failure changes nothing server-side and is left alone.

### 3.3 Removing a Super Admin — and Why Self-Removal Is Only a UI Guard

Each row's Remove control opens a `ConfirmDialog` and, on confirm, calls `DELETE /api-system/backstage/super-admins/:id` (`handleConfirmRemove`, lines 166-177). For the row matching the signed-in user's own `user_id`, the Remove button is replaced entirely with static text — *"You cannot revoke your own privileges"* — rather than disabled (`RosterRow`, lines 405-408). The component's own comment explains why removal is hidden, not merely disabled: this page is reachable only by super admins, so the person reading it is often *in* the list, and a live Remove button next to one's own name "is one click away from locking themselves — and possibly everyone — out of this page" (lines 385-389).

**Verified: this guard exists only in the SPA.** `backstage_super_admin.service.ts`'s `remove(id)` (lines 152-169) looks the row up by its own `id` and soft-deletes it; it never compares the row's `user_id` against the caller's own `user_id`, and neither the gateway controller (`backstage-super-admins.controller.ts:148`) nor `BackstageSuperAdminGuard` add such a check. A super admin who calls `DELETE /api-system/backstage/super-admins/:id` directly — with their own entry's `id` — can remove their own row; nothing server-side stops them. The same absence of a lower bound means a sufficiently privileged caller can also remove every remaining row, including the last one: the service performs no "at least one active super admin must remain" check anywhere in `add`, `remove`, or `list`. Both are documented as edge cases in §7, not asserted as theoretical — they follow directly from reading `remove()`'s full body, which contains only an existence check (`findFirst` at lines 155-157) before the `update()`.

## 4. Roles and Personas

| Surface | Guard | Check | Notes |
|---|---|---|---|
| `/backstage/super-admins` route | `PrivateRoute` | `requireSuperAdmin` → `isSuperAdmin` | `../carmen-backstage/src/App.tsx:489-496`; `PrivateRoute.tsx:89-91` |
| Sidebar "Super Admins" entry | `buildBackstageNav` | `superAdminOnly: true` → `opts.isSuperAdmin` | `backstageNav.ts:51,119`; no `permission` field exists on this row |
| `GET /api-system/backstage/super-admins` | `BackstageSuperAdminGuard` | live `is_super_admin` re-check | `backstage-super-admins.controller.ts:78-98` |
| `POST /api-system/backstage/super-admins` | `BackstageSuperAdminGuard` | live `is_super_admin` re-check | `backstage-super-admins.controller.ts:107-139`; 409 if already active |
| `DELETE /api-system/backstage/super-admins/:id` | `BackstageSuperAdminGuard` | live `is_super_admin` re-check | `backstage-super-admins.controller.ts:148`; no self-check, no last-admin check (§3.3) |

Every row in this table is the same fact stated once: **no RBAC permission key anywhere in this module — every gate is `isSuperAdmin`, resolved fresh from `tb_backstage_super_admin` on the backend and cached only in the SPA's own session state on the frontend (§5.4).**

Holding this row also silently satisfies unrelated authorization branches elsewhere in the platform, independent of this screen: `resolveProfileMemberships` in the auth service surfaces every active business unit as an admin membership for a super admin's own profile (`../carmen-turborepo-backend/apps/micro-business/src/authen/auth/auth.service.ts:2796-2824`); `TenantService.isSuperAdmin` grants a fail-closed database-connection bypass (`apps/micro-business/src/tenant/tenant.service.ts:348-358,394-400`); the gateway's own `PermissionService.isSuperAdmin` (`apps/backend-gateway/src/auth/services/permission.service.ts:373-384`) and `micro-cluster`'s `ClusterAdminAuthzService.isBackstageSuperAdmin` (`apps/micro-cluster/src/common/cluster-admin-authz.service.ts:27-34`, consulted at five separate gate points in that same file) each independently re-run the identical `{ user_id, is_active: true, deleted_at: null }` query rather than sharing one service — because each is a separate deployable with its own Prisma client, not because the check differs.

## 5. Entity: `tb_backstage_super_admin`

`tb_backstage_super_admin` is defined at `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma:1371`, created by migration `20260610073505_add_god_mode` and extended by `20260612000000_add_doc_version`. Beyond the standard audit columns, it holds exactly three meaningful fields — small enough that, per this plan's depth rule, it is documented here rather than on a dedicated `data-model` page.

### 5.1 Columns

| Column | Type | Meaning |
|---|---|---|
| `id` | `uuid`, PK, `gen_random_uuid()` | The allowlist entry's own id — this, not `user_id`, is what `DELETE .../:id` takes. |
| `user_id` | `uuid`, required | The platform user this entry names. Not a foreign key by this schema's own convention (no relation is declared) — `list()` joins it to `tb_user`/`tb_user_profile` in application code (§3.1) rather than at the database level. |
| `is_active` | `boolean?`, default `true` | Written `true` at row creation and never written `false` by any code path found in this repository (verified in §5.3) — every read that matters filters `is_active: true, deleted_at: null` together, so in practice the column is a constant once a row exists. |
| `current_business_unit_id` | `uuid?` | The business unit this super admin last switched to (added 2026-10-26, `5d7bab295`). A super admin's profile lists every active BU without membership links (an active link would consume a customer seat), so `setDefaultTenant` in micro-cluster stores the choice here (`business-unit.service.ts:1355-1366`, also writing `updated_by_id`/`updated_at`) and `resolveProfileMemberships` reads it to mark `is_default` (`auth.service.ts:2796-2824`); the list is ordered by BU name. |
| `doc_version`, `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | standard audit columns | `created_by_id`/`deleted_by_id` are present in the schema but never populated for this table specifically — see §3.1's audit-trail finding. |

A unique index, `backstage_super_admin_user_deleted_at_u` on `(user_id, deleted_at)` (`schema.prisma:1389`, created by the same migration), is what makes `add()`'s duplicate check meaningful at the database level, not only in application code: a second **active** row for the same `user_id` (`deleted_at IS NULL` in both) would collide on this index, though `add()`'s own `findFirst` check (§5.2) is what actually produces the user-facing 409 before that would ever happen.

### 5.2 How a Row Comes to Exist

There are exactly two paths, and they are asymmetric on purpose:

1. **Bootstrap, direct database write.** `packages/prisma-shared-schema-backstage/prisma/seed.backstage-super-admin.ts` reads a `SUPER_ADMIN_USER_ID` environment variable, checks for an existing non-deleted row, and if none exists calls `tb_backstage_super_admin.create({ data: { user_id, is_active: true } })` directly against the database — bypassing `BackstageSuperAdminGuard`, the gateway, and every RPC hop entirely. This path exists *because it has to*: `BackstageSuperAdminGuard` gates `POST /api-system/backstage/super-admins` on the caller already being an active super admin (§1), so before any row exists, no session can call the API to create the first one. The seed script is the only way out of that circularity.
2. **In-app, by an existing super admin.** `POST /api-system/backstage/super-admins` → `BackstageSuperAdminService.add(userId)` (`../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_super_admin/backstage_super_admin.service.ts:119-141`) — checks for an existing active, non-deleted row for that `user_id` (lines 122-124), returns `ALREADY_EXISTS` (HTTP 409, `packages/error-catalog/src/catalog.ts` → `std-response.ts:143`) if one is found, otherwise creates a new row with `is_active: true`.

### 5.3 How a Row Is Deactivated

**It is a soft delete, not an `is_active` flip, and this is a fact about the whole codebase, not a design choice stated anywhere in a comment — it follows from there being exactly one `.update()` call in the entire backend that changes the *lifecycle* of a row (a second `.update()`, in micro-cluster's `setDefaultTenant`, writes only `current_business_unit_id` plus the audit pair).** `BackstageSuperAdminService.remove(id)` (service.ts:152-169) looks the row up by `id`, and if found calls:

```
await this.prismaSystem.tb_backstage_super_admin.update({
  where: { id },
  data: { deleted_at: new Date().toISOString() },
});
```

— only `deleted_at`. A repository-wide search for every write to `tb_backstage_super_admin` found this to be the only `.update()` that touches `deleted_at` or `is_active` anywhere in `../carmen-turborepo-backend` (the other update, `setDefaultTenant`, sets `current_business_unit_id`, `updated_by_id`, `updated_at`); `is_active` is written exactly twice in the whole backend, both times as the literal `true`, both at creation (§5.2's two paths). No code path ever sets `is_active: false`. Concretely: **removing a super admin through this screen (or the API directly) is a soft delete keyed on `deleted_at`, and the `is_active` column — despite being filtered on in every read — never actually changes value for the lifetime of a row.** A row that shows `Active` on screen and one that has been "removed" differ only in whether `deleted_at` is null; `is_active` reads `true` in both. `list()`'s own comment (service.ts:69-73) states that deleted/deactivated *users* are deliberately not filtered out of the roster — a super-admin row for a soft-deleted `tb_user` still has god-mode and must stay visible so an operator can revoke it — but that is a statement about the joined `tb_user` row, not about this table's own `is_active` column, which this page's research found to be effectively write-once.

### 5.4 Effect on a Session Already Open

Removal takes effect on the very next backend request, for every consumer of the flag, because none of them cache it: `BackstageSuperAdminGuard` (§1) and `EffectivePermissionsService.resolve()` (`../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_permission/effective_permissions.service.ts:31-32`, `is_super_admin: isSuperAdmin` computed by calling `this.superAdmin.isSuperAdmin(userId)` fresh every call) both query the database live, as do the four independent re-implementations of the same check listed in §4. There is no Redis or in-process cache anywhere in this call chain (checked directly — no cache/Redis reference exists in `apps/micro-business/src/authen/backstage_permission` or the guard itself).

The frontend is a different story, and this is the part worth testing deliberately: `AuthContext` fetches `effectivePermissions` at only three call sites — once on initial mount from a token already in `localStorage` (`AuthContext.tsx:87`), once at `login()` (`AuthContext.tsx:185`), and once at `loginWithTokens()` (the Google sign-in path, `AuthContext.tsx:289`) — and otherwise never refetches or polls it. So a browser tab that was already open and authenticated as a now-removed super admin keeps rendering the "Super Admins" nav entry and every other `isSuperAdmin`-gated UI element until that tab reloads or the user logs in again; `isSuperAdmin` in that stale tab's React state stays `true`. What that stale tab **cannot** do is actually complete a privileged action: the next request it sends to any `BackstageSuperAdminGuard`- or `BackstagePermissionGuard`-protected endpoint (including this module's own `GET`/`POST`/`DELETE`) is checked live against the database and gets a fresh, correct 403. The window this creates is purely cosmetic (stale nav visibility, stale-looking UI affordances) rather than a live authorization gap — inferred from reading both the frontend fetch sites and the backend guards directly, not observed at runtime.

## 6. e2e Coverage

`../carmen-backstage-e2e/tests/super-admins/super-admin-manage.spec.ts` (1 spec file, 2 tests: a smoke test that the title, the "Add Super Admin" trigger and at least one Remove button render, and a self-cleaning add-then-remove round trip) was last touched at commit `538632d` (2026-09-18, "follow login and the super-admin picker to their current shapes"); its page object `../carmen-backstage-e2e/pages/SuperAdminManagementPage.ts` was last touched at `7bc9dc9` (2026-10-26, the `api-system/backstage` path rename).

An earlier revision of this page recorded that the suite predated the card-based roster rewrite (`28f92eb`, 2026-09-02, `#244`) and failed at its fixture. **That is no longer true**: the page object now matches the current screen.

- `userSelect` is `input[aria-label="Select user to add as super admin"]` (`SuperAdminManagementPage.ts:45`), matching the `UserPicker` typeahead `<input>` (`UserPicker.tsx:158`); it is only reachable after `openAddDialog()` clicks the page's "Add Super Admin" trigger (`:49`, `:61-64`), because the picker lives inside the `Dialog` (`SuperAdminManagement.tsx:301-363`).
- `addButton` is scoped to the dialog and matches `/Add Super Admin|Adding/` (`:48`), consistent with the dialog submit label (`SuperAdminManagement.tsx:359`).
- `goto()` waits for the "Super Admins" `h1` and network quiet instead of the old `<select>` (`:52-58`).
- `adminRows` is `ul.divide-y > li` (`:67-69`) and `removeButtons` is `button[aria-label^="Remove super admin "]` (`:72-74`), matching the `<ul>`/`<li>` roster (`SuperAdminManagement.tsx:284,422`) and `removeAria: 'Remove super admin {{name}}'` (`../carmen-backstage/src/i18n/en.ts:4117`).
- The success-toast strings the page object waits for (`SuperAdminManagementPage.ts:146,169`) match `addSuccess`/`removeSuccess` in current i18n (`en.ts:4095,4097`).

**Caveats.** The suite was read against current source, not executed for this page; whether it passes at runtime was not verified. The spec's `annotation` step text still says "select" in places (for example "Assert the 'Select user to add as super admin' select is visible"), but the test bodies use the dialog/picker flow. Coverage is narrow: nothing tests the self-removal guard, the 409 duplicate path, or the stale-tab behavior in §5.4, and the suite deliberately never touches the login user. Every claim on this page still traces to `../carmen-backstage`/`../carmen-turborepo-backend` source directly, not to this suite.

## 7. Edge Cases

| Scenario | Behavior | Source |
|---|---|---|
| Self-removal via the UI | Remove control is replaced with static text; no request is ever sent | `SuperAdminManagement.tsx:405-408` |
| Self-removal via a direct API call | **Not prevented.** `remove(id)` has no check comparing the row's `user_id` to the caller's own | `backstage_super_admin.service.ts:152-169` (verified: only an existence check, no ownership check) |
| Removing the last remaining active super admin | **Not prevented anywhere** — `add`, `remove`, and `list` contain no "at least one must remain" check | Full read of `backstage_super_admin.service.ts` |
| Adding a `user_id` that already has an active row | `409 ALREADY_EXISTS`; frontend clears the stale selection and refetches on exactly this status code | `backstage_super_admin.service.ts:122-131`; `SuperAdminManagement.tsx:151-160` |
| A listed super admin's underlying `tb_user` row is soft-deleted or deactivated | Row is **deliberately kept visible** (not filtered) so the privilege can still be revoked; row renders with an em dash where the name/email would be if both are empty | `backstage_super_admin.service.ts:69-72,98-103`; `SuperAdminManagement.tsx:28-33,433-435` |
| Who granted a privilege, after the fact | **Not recorded.** `created_by_id`/`deleted_by_id` are never written for this table; the roster can only ever show *when*, never *who* did the granting/revoking | §3.1, §5.1, §5.3 |
| A super admin's session is already open in a browser tab when their row is removed | Backend calls from that tab are checked live and correctly denied on the next request; the tab's own cached `effectivePermissions` (fetched only at login/mount) keeps showing super-admin UI until reload or re-login | §5.4 |
| The very first super admin, on a brand-new deployment | Cannot be created through the UI or API — every endpoint requires an existing active super admin. Must be created by the `SUPER_ADMIN_USER_ID` seed script writing directly to the database | §5.2 |

## 8. Recommendations

Treat this page as a break-glass control, not a routine admin screen: every grant here is a full RBAC bypass, both frontend and backend, confirmed at the exact short-circuit lines cited in §2. Because removal is a soft delete with no server-side self-check and no minimum-headcount guard (§3.3, §7), a second pair of eyes before removing a row — especially one's own, or the last remaining row — is a process control this screen does not enforce for you. Anyone testing this module with a reduced-permission session should note there is no reduced-permission session to test with respect to *this* module specifically — the only two states are "super admin" and "not," and the existing e2e suite (§6) exercises only the super-admin state (its login user) and the add/remove round trip. A reduced-permission session is the one thing it cannot cover; extending it should assert the self-removal guard and the 409 path (§6 caveats) against current source.

## 9. Related Modules

- [RBAC](/en/backstage/rbac) — owns the permission-key/role-bundle axis this module deliberately sits outside of; §2 above shows exactly where `is_super_admin` short-circuits that system on both sides.
- [User Platform](/en/backstage/user-platform) — the ordinary, RBAC-scoped way to grant platform privileges; contrast with this module's unconditional bypass.
- [Cluster Admin](/en/backstage/cluster-admin) — a second axis this same flag also short-circuits: `ClusterAdminAuthzService.isBackstageSuperAdmin` treats every super admin as an administrator of every cluster (§4 above).
- [Users](/en/backstage/users) — owns the `tb_user`/`tb_user_profile` records this module's roster joins against for display only (§3.1).

## 10. Reference Sources

All `../carmen-backstage` paths are HEAD `8405788f` (2026-10-27); all `../carmen-turborepo-backend` paths are HEAD `c9d788829` (2026-10-27); `../carmen-backstage-e2e` is HEAD `9584887` (2026-10-27), with the `super-admins` spec itself last touched at `538632d` (2026-09-18).

- `src/pages/SuperAdminManagement.tsx` — the whole screen (read in full, 484 lines).
- `src/services/superAdminService.ts` — `list`/`add`/`remove`.
- `src/types/index.ts:1129-1137` — the `SuperAdmin` interface and its audit-shape comment.
- `src/components/nav/backstageNav.ts:49-51,116-128` — the nav row, its Thai divider comment, and `buildBackstageNav`'s filter.
- `src/App.tsx:489-496` — the route.
- `src/components/PrivateRoute.tsx:39-108` — the frontend guard, including ordering relative to the feature-flag check.
- `src/context/AuthContext.tsx:87,185,289,342` — `isSuperAdmin`, `fetchEffectivePermissions`, and when each is called.
- `src/utils/permissions.ts:50-78` — `checkPermission`'s and `checkBackstageAuthority`'s super-admin short-circuits.
- `src/components/UserPicker.tsx` — the typeahead used by the Add dialog.
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage-super-admins/{backstage-super-admins.controller.ts,backstage-super-admins.service.ts}` — the HTTP surface and its RPC proxy.
- `../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/backstage-super-admin.guard.ts` — the live, uncached `is_super_admin` re-check.
- `../carmen-turborepo-backend/apps/backend-gateway/src/auth/guards/backstage-permission.guard.ts:108-110` — the super-admin bypass shared by every RBAC-gated backend route.
- `../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_super_admin/{backstage_super_admin.service.ts,backstage_super_admin.controller.ts,backstage_super_admin.service.spec.ts}` — the table's only reader/writer, and its own test suite confirming the soft-delete/no-self-check/no-last-admin-check behavior described in §3.3, §5.3, §7.
- `../carmen-turborepo-backend/apps/micro-business/src/authen/backstage_permission/effective_permissions.service.ts:31-32,77` — where `is_super_admin` enters the effective-permissions payload.
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma:1371-1390` — the `tb_backstage_super_admin` model.
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/migrations/{20260610073505_add_god_mode,20260612000000_add_doc_version}/migration.sql` — table creation and the later `doc_version` column.
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/seed.backstage-super-admin.ts` — the bootstrap path (§5.2).
- `../carmen-turborepo-backend/packages/error-catalog/src/catalog.ts` (`SUPER_ADMIN_NOT_FOUND`, 404) and `../carmen-turborepo-backend/packages/nest-result/src/std-response.ts:143` (`ALREADY_EXISTS` → 409).
- `../carmen-turborepo-backend/apps/backend-gateway/src/common/enrichment/audit-shape.ts:1-7` and `../carmen-turborepo-backend/apps/backend-gateway/src/common/enrichment/enrichment.service.ts` — the `@EnrichAuditUsers()` mechanism cited in §3.1's audit-trail finding.
- Cross-module `is_super_admin` consumers cited in §4: `../carmen-turborepo-backend/apps/micro-business/src/authen/auth/auth.service.ts:2796-2824`, `../carmen-turborepo-backend/apps/micro-business/src/tenant/tenant.service.ts:348-358,394-400`, `../carmen-turborepo-backend/apps/backend-gateway/src/auth/services/permission.service.ts:373-384`, `../carmen-turborepo-backend/apps/micro-cluster/src/common/cluster-admin-authz.service.ts:27-34`.
- `../carmen-backstage-e2e/tests/super-admins/super-admin-manage.spec.ts` and `../carmen-backstage-e2e/pages/SuperAdminManagementPage.ts` — read in full for §6.

## 11. Pages in This Module

This module is a single page. `tb_backstage_super_admin` is documented in §5 above rather than on a separate `data-model` page, and there is no `permissions` page — §4's five-row gate matrix is the entire permission surface, and every one of its five rows resolves to the same `isSuperAdmin` check. See the parent [Backstage book index](/en/backstage).
