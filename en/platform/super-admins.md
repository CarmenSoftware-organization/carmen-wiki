---
title: Super Admins
description: The platform's god-mode allowlist — SuperAdminManagement (/platform/super-admins), gated by superAdminOnly with no RBAC permission key at all, and its two-column tb_platform_super_admin table.
published: true
date: '2026-09-06T22:00:00.000Z'
tags: book/platform, super-admins
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Super Admins

> **At a Glance**
> **Screen:** `SuperAdminManagement` (`/platform/super-admins`) — a card-based roster (one `<ul>`/`<li>` per person), not a `DataTable` &nbsp;·&nbsp; **The gate:** **no RBAC permission key at all** — the nav entry and the route are both `superAdminOnly: true`, checked against `isSuperAdmin` (derived from `effectivePermissions.is_super_admin`), never against a permission string &nbsp;·&nbsp; **Nav:** `feature: 'super_admins'`, `dividerBefore: true` — the divider marks where the sidebar stops being day-to-day configuration and starts being "who else can reach configuration" &nbsp;·&nbsp; **Backend enforcement:** all three endpoints (`GET`/`POST`/`DELETE /api-system/platform/super-admins`) sit behind `PlatformSuperAdminGuard`, which re-resolves `is_super_admin` from the database on every single request — no cache anywhere in the chain &nbsp;·&nbsp; **Table:** `tb_platform_super_admin` — two meaningful columns (`user_id`, `is_active`) beyond the audit columns, documented in full below (§5) rather than on a separate `data-model` page &nbsp;·&nbsp; **e2e suite:** `super-admins` (1 spec, HEAD `bb8f671`, 2026-06-11) — predates the 2026-09-02 card-roster rewrite and fails at the shared test fixture itself, not merely in individual assertions (§6)

## 1. Overview

Super Admins is the one screen in the Platform admin product whose entire purpose is to control who can reach every other screen. Its nav entry (`../carmen-platform/src/components/nav/platformNav.ts:46`) reads:

```
{ path: '/platform/super-admins', labelKey: 'nav.superAdmins', icon: ShieldAlert,
  superAdminOnly: true, groupKey: 'navGroup.platform', feature: 'super_admins', dividerBefore: true }
```

There is no `permission` field on this row at all. Every other row in the sidebar is filtered by `!item.permission || opts.hasPermission(item.permission)` (`platformNav.ts:94`); this one is filtered by `!item.superAdminOnly || opts.isSuperAdmin` (`platformNav.ts:95`) instead — a boolean, not a permission-string lookup. The two comment lines immediately above the row (`platformNav.ts:44-45`, Thai) state the reason for the divider directly: *"the divider separates these two bottom rows from day-to-day configuration work — both of them change what other people can access. Not made a new group, because it's still 'Platform' — just a different risk level."* The route (`../carmen-platform/src/App.tsx:443-448`) is wrapped the same way, in `<PrivateRoute requireSuperAdmin feature="super_admins">`.

The honest way to describe this gate — and the one this page uses throughout — is **"no RBAC permission key — the menu entry and route are `superAdminOnly`,"** not "no permission check at all." The check is real and it runs twice: once in `PrivateRoute` (`../carmen-platform/src/components/PrivateRoute.tsx:87-89`, `if (requireSuperAdmin && !isSuperAdmin) return <Forbidden />`, evaluated after the platform-authority resolution branch and before the feature-flag check at lines 94-103 — the same permission-before-flag ordering every other gated route in this book follows), and independently again on every backend request. What is genuinely absent is a permission *key*: nothing in `tb_platform_permission` names this capability, so no role bundle can be granted or denied access to it — the only way in is to already hold the allowlist row this page manages.

`isSuperAdmin` itself is `!!effectivePermissions?.is_super_admin` (`../carmen-platform/src/context/AuthContext.tsx:256`), and `effectivePermissions` is fetched once at login and once on page mount (`fetchEffectivePermissions()`, called at `AuthContext.tsx:66` and `AuthContext.tsx:164`) — not polled. §5.4 covers what that caching means for a session that is already open when someone's row is removed.

On the backend, `PlatformSuperAdminController` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-super-admins/platform-super-admins.controller.ts:54-58`) applies `@UseGuards(KeycloakGuard, PlatformSuperAdminGuard)` at the controller level, so `list`, `add`, and `remove` are all gated identically. `PlatformSuperAdminGuard.canActivate` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-super-admin.guard.ts:40-70`) makes a fresh TCP call to `PlatformPermissions.effective` on every invocation and fails closed — a thrown error or a non-OK response denies the request (lines 51-62) — rather than falling back to a cached or default value. This means **the API itself requires an existing super admin to manage the allowlist**, a bootstrapping consequence covered in §5.2.

## 2. Business Context

A row in `tb_platform_super_admin` is a bypass, not a bundle of grants. Two independent short-circuits key off it:

- **Frontend:** `checkPermission()` (`../carmen-platform/src/utils/permissions.ts:56`) — `if (eff?.is_super_admin) return true;` — before it ever consults `eff.platform` or `eff.clusters`. Every `hasPermission()`/`<Can>` check in the SPA passes through this function.
- **Backend:** `PlatformPermissionGuard.canActivate` (`../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-permission.guard.ts:104`) — `if (eff?.is_super_admin === true) return true;` — a strict-equality check the guard's own comment says must match the analytics scope filter exactly, "or a stray value like `\"false\"` or `1` could give the guard and the data filter different answers." This is the guard behind every `@RequirePlatformPermission` decorator in the backend gateway — i.e. behind essentially every RBAC-gated platform route in the product.

This is exactly what the screen's own subtitle says: *"Platform users who bypass all permission checks"* (`pages.superAdmins.subtitle`, `../carmen-platform/src/i18n/en.ts:3612`). The screen exists so that a small, auditable allowlist — not a role, not a permission bundle — is the single place that answers "who currently has god mode." Granting it is appropriate for platform engineering/support staff who need unconditional access across every cluster and business unit; it is not a substitute for an RBAC role bundle for anyone whose job is scoped to specific resources.

## 3. Key Concepts

### 3.1 The Roster Screen

`SuperAdminManagement` (`../carmen-platform/src/pages/SuperAdminManagement.tsx`) fetches `GET /api-system/platform/super-admins` on mount (`fetchData`, lines 90-105) and renders one `<Card>` containing a `<ul className="divide-y">` of `<li>` rows (lines 284-293) — not a `DataTable`. Each row (`RosterRow`, lines 391-466) shows an avatar with up-to-two-letter initials, the person's resolved name or email (falling back to an em dash, deliberately never to a phrase like "Unknown user" — the component's own comment explains why: a frontend deployed ahead of a backend that hasn't joined these fields yet would otherwise make every row read as though its user had been deleted, lines 28-32), the raw `user_id` UUID, an Active/Inactive badge, and a "Granted `<relative time>`" line.

A search box (`SearchInput`) only appears once the roster exceeds `SEARCH_THRESHOLD = 8` rows (line 57) — the component's own comment states the reasoning: "a roster this short is read, not searched... below that it is a control that never gets used" (lines 54-56). The header subtitle states a consequence rather than a description: while data is loading with nothing on screen yet it shows the generic subtitle, otherwise it states the exact headcount ("One person on this platform bypasses every permission check" / "`{count}` people... bypass every permission check", lines 201-207) — the one fact an operator visits this page to check.

An **Export** button (header, disabled while loading or empty) downloads a CSV of every visible row — user, email, `user_id`, status, and the four audit columns (`created_at`/`created_by`/`updated_at`/`updated_by`) via `auditCsvFields(normalizeAudit(r))` (lines 179-199). A `DevDebugSheet` (line 377) exposes the raw `GET` response for local debugging.

**A real, verified gap in the audit trail:** the per-row "Granted" line (`AuditMeta` with `verbKey="pages.superAdmins.grantedVerb"`, line 451-455) can only ever show a relative timestamp, never a name, and this is not a frontend rendering limit — the name was never captured. `platform_super_admin.service.ts`'s own `add()` (`../carmen-turborepo-backend-v2/apps/micro-business/src/authen/platform_super_admin/platform_super_admin.service.ts:143-148`) and the bootstrap seed script's `create()` call (`packages/prisma-shared-schema-platform/prisma/seed.platform-super-admin.ts:29-34`) both write only `{ user_id, is_active: true }` — neither sets `created_by_id`. A repository-wide search for any code that writes to `created_by_id` found none outside this one absent write path; the log-events Prisma middleware (`packages/log-events-library/src/middleware/prisma-audit.middleware.ts`) writes a separate append-only audit-event stream, not this column. The gateway's `@EnrichAuditUsers()` mechanism (`apps/backend-gateway/src/common/enrichment/audit-shape.ts:2,4-7`, `AUDIT_BY_ID_FIELDS = ['created_by_id', ...]`) can only resolve a name from a `created_by_id` it is actually given, so `audit.created` ends up carrying only `.at` — exactly what the frontend's own `SuperAdmin` type comment already anticipates ("gateway's `@EnrichAuditUsers()` nests `created_at` here as `audit.created.at`," `../carmen-platform/src/types/index.ts:985`). The same is true in the other direction: `remove()`'s `update()` call (service.ts:176-179) sets only `deleted_at`, never `deleted_by_id` — so the record of *who* deactivated a super admin is not captured either, only *when*.

### 3.2 Adding a Super Admin

The header's **Add Super Admin** button opens a `Dialog` containing a `UserPicker` typeahead (server-side search via `useUserSearch`), not the plain `<select>` an earlier build once used (see §6). Users who already hold the privilege are shown disabled in the picker rather than allowed through to a predictable 409 (`superAdminUserIds` memo, `SuperAdminManagement.tsx:113-116`). `handleAdd` (lines 138-164) calls `POST /api-system/platform/super-admins` with `{ user_id }`; on a `409` specifically it clears the stale selection and refetches, on the reasoning that a 409 here means someone else granted the same user the privilege first, so the list on screen is provably stale (lines 151-160) — any other failure changes nothing server-side and is left alone.

### 3.3 Removing a Super Admin — and Why Self-Removal Is Only a UI Guard

Each row's Remove control opens a `ConfirmDialog` and, on confirm, calls `DELETE /api-system/platform/super-admins/:id` (`handleConfirmRemove`, lines 166-177). For the row matching the signed-in user's own `user_id`, the Remove button is replaced entirely with static text — *"You cannot revoke your own privileges"* — rather than disabled (`RosterRow`, lines 405-408). The component's own comment explains why removal is hidden, not merely disabled: this page is reachable only by super admins, so the person reading it is often *in* the list, and a live Remove button next to one's own name "is one click away from locking themselves — and possibly everyone — out of this page" (lines 385-389).

**Verified: this guard exists only in the SPA.** `platform_super_admin.service.ts`'s `remove(id)` (lines 161-182) looks the row up by its own `id` and soft-deletes it; it never compares the row's `user_id` against the caller's own `user_id`, and neither the gateway controller (`platform-super-admins.controller.ts:149-178`) nor `PlatformSuperAdminGuard` add such a check. A super admin who calls `DELETE /api-system/platform/super-admins/:id` directly — with their own entry's `id` — can remove their own row; nothing server-side stops them. The same absence of a lower bound means a sufficiently privileged caller can also remove every remaining row, including the last one: the service performs no "at least one active super admin must remain" check anywhere in `add`, `remove`, or `list`. Both are documented as edge cases in §7, not asserted as theoretical — they follow directly from reading `remove()`'s full body, which contains only an existence check (`findFirst` at lines 168-171) before the `update()`.

## 4. Roles and Personas

| Surface | Guard | Check | Notes |
|---|---|---|---|
| `/platform/super-admins` route | `PrivateRoute` | `requireSuperAdmin` → `isSuperAdmin` | `../carmen-platform/src/App.tsx:443-448`; `PrivateRoute.tsx:87-89` |
| Sidebar "Super Admins" entry | `buildPlatformNav` | `superAdminOnly: true` → `opts.isSuperAdmin` | `platformNav.ts:46,95`; no `permission` field exists on this row |
| `GET /api-system/platform/super-admins` | `PlatformSuperAdminGuard` | live `is_super_admin` re-check | `platform-super-admins.controller.ts:76-96` |
| `POST /api-system/platform/super-admins` | `PlatformSuperAdminGuard` | live `is_super_admin` re-check | `platform-super-admins.controller.ts:105-140`; 409 if already active |
| `DELETE /api-system/platform/super-admins/:id` | `PlatformSuperAdminGuard` | live `is_super_admin` re-check | `platform-super-admins.controller.ts:149-178`; no self-check, no last-admin check (§3.3) |

Every row in this table is the same fact stated once: **no RBAC permission key anywhere in this module — every gate is `isSuperAdmin`, resolved fresh from `tb_platform_super_admin` on the backend and cached only in the SPA's own session state on the frontend (§5.4).**

Holding this row also silently satisfies unrelated authorization branches elsewhere in the platform, independent of this screen: `resolveProfileMemberships` in the auth service surfaces every active business unit as an admin membership for a super admin's own profile (`../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts:2371-2385`); `TenantService.isSuperAdmin` grants a fail-closed database-connection bypass (`apps/micro-business/src/tenant/tenant.service.ts:374-386`); the gateway's own `PermissionService.isSuperAdmin` (`apps/backend-gateway/src/auth/services/permission.service.ts:372-382`) and `micro-cluster`'s `ClusterAdminAuthzService.isPlatformSuperAdmin` (`apps/micro-cluster/src/common/cluster-admin-authz.service.ts:30-36`, consulted at five separate gate points in that same file) each independently re-run the identical `{ user_id, is_active: true, deleted_at: null }` query rather than sharing one service — because each is a separate deployable with its own Prisma client, not because the check differs.

## 5. Entity: `tb_platform_super_admin`

`tb_platform_super_admin` is defined at `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1090`, created by migration `20260610073505_add_god_mode` and extended by `20260612000000_add_doc_version`. Beyond the standard audit columns, it holds exactly two meaningful fields — small enough that, per this plan's depth rule, it is documented here rather than on a dedicated `data-model` page.

### 5.1 Columns

| Column | Type | Meaning |
|---|---|---|
| `id` | `uuid`, PK, `gen_random_uuid()` | The allowlist entry's own id — this, not `user_id`, is what `DELETE .../:id` takes. |
| `user_id` | `uuid`, required | The platform user this entry names. Not a foreign key by this schema's own convention (no relation is declared) — `list()` joins it to `tb_user`/`tb_user_profile` in application code (§3.1) rather than at the database level. |
| `is_active` | `boolean?`, default `true` | Written `true` at row creation and never written `false` by any code path found in this repository (verified in §5.3) — every read that matters filters `is_active: true, deleted_at: null` together, so in practice the column is a constant once a row exists. |
| `doc_version`, `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | standard audit columns | `created_by_id`/`deleted_by_id` are present in the schema but never populated for this table specifically — see §3.1's audit-trail finding. |

A unique index, `platform_super_admin_user_deleted_at_u` on `(user_id, deleted_at)` (`schema.prisma:1103`, created by the same migration), is what makes `add()`'s duplicate check meaningful at the database level, not only in application code: a second **active** row for the same `user_id` (`deleted_at IS NULL` in both) would collide on this index, though `add()`'s own `findFirst` check (§5.2) is what actually produces the user-facing 409 before that would ever happen.

### 5.2 How a Row Comes to Exist

There are exactly two paths, and they are asymmetric on purpose:

1. **Bootstrap, direct database write.** `packages/prisma-shared-schema-platform/prisma/seed.platform-super-admin.ts` reads a `SUPER_ADMIN_USER_ID` environment variable, checks for an existing non-deleted row, and if none exists calls `tb_platform_super_admin.create({ data: { user_id, is_active: true } })` directly against the database — bypassing `PlatformSuperAdminGuard`, the gateway, and every RPC hop entirely. This path exists *because it has to*: `PlatformSuperAdminGuard` gates `POST /api-system/platform/super-admins` on the caller already being an active super admin (§1), so before any row exists, no session can call the API to create the first one. The seed script is the only way out of that circularity.
2. **In-app, by an existing super admin.** `POST /api-system/platform/super-admins` → `PlatformSuperAdminService.add(userId)` (`../carmen-turborepo-backend-v2/apps/micro-business/src/authen/platform_super_admin/platform_super_admin.service.ts:125-151`) — checks for an existing active, non-deleted row for that `user_id` (lines 132-134), returns `ALREADY_EXISTS` (HTTP 409, `packages/error-catalog/src/catalog.ts` → `std-response.ts:144`) if one is found, otherwise creates a new row with `is_active: true`.

### 5.3 How a Row Is Deactivated

**It is a soft delete, not an `is_active` flip, and this is a fact about the whole codebase, not a design choice stated anywhere in a comment — it follows from there being exactly one `.update()` call against this table in the entire backend.** `PlatformSuperAdminService.remove(id)` (service.ts:161-182) looks the row up by `id`, and if found calls:

```
await this.prismaSystem.tb_platform_super_admin.update({
  where: { id },
  data: { deleted_at: new Date().toISOString() },
});
```

— only `deleted_at`. A repository-wide search for every write to `tb_platform_super_admin` found this to be the only `.update()` call against the model anywhere in `../carmen-turborepo-backend-v2`; `is_active` is written exactly twice in the whole backend, both times as the literal `true`, both at creation (§5.2's two paths). No code path ever sets `is_active: false`. Concretely: **removing a super admin through this screen (or the API directly) is a soft delete keyed on `deleted_at`, and the `is_active` column — despite being filtered on in every read — never actually changes value for the lifetime of a row.** A row that shows `Active` on screen and one that has been "removed" differ only in whether `deleted_at` is null; `is_active` reads `true` in both. `list()`'s own comment (service.ts:74-78) states that deleted/deactivated *users* are deliberately not filtered out of the roster — a super-admin row for a soft-deleted `tb_user` still has god-mode and must stay visible so an operator can revoke it — but that is a statement about the joined `tb_user` row, not about this table's own `is_active` column, which this page's research found to be effectively write-once.

### 5.4 Effect on a Session Already Open

Removal takes effect on the very next backend request, for every consumer of the flag, because none of them cache it: `PlatformSuperAdminGuard` (§1) and `EffectivePermissionsService.resolve()` (`../carmen-turborepo-backend-v2/apps/micro-business/src/authen/platform_permission/effective_permissions.service.ts:31-32`, `is_super_admin: isSuperAdmin` computed by calling `this.superAdmin.isSuperAdmin(userId)` fresh every call) both query the database live, as do the four independent re-implementations of the same check listed in §4. There is no Redis or in-process cache anywhere in this call chain (checked directly — no cache/Redis reference exists in `apps/micro-business/src/authen/platform_permission` or the guard itself).

The frontend is a different story, and this is the part worth testing deliberately: `AuthContext` fetches `effectivePermissions` exactly twice per session — once on initial mount from a token already in `localStorage` (`AuthContext.tsx:66`) and once at `login()` (`AuthContext.tsx:164`) — and otherwise never refetches or polls it. So a browser tab that was already open and authenticated as a now-removed super admin keeps rendering the "Super Admins" nav entry and every other `isSuperAdmin`-gated UI element until that tab reloads or the user logs in again; `isSuperAdmin` in that stale tab's React state stays `true`. What that stale tab **cannot** do is actually complete a privileged action: the next request it sends to any `PlatformSuperAdminGuard`- or `PlatformPermissionGuard`-protected endpoint (including this module's own `GET`/`POST`/`DELETE`) is checked live against the database and gets a fresh, correct 403. The window this creates is purely cosmetic (stale nav visibility, stale-looking UI affordances) rather than a live authorization gap — inferred from reading both the frontend fetch sites and the backend guards directly, not observed at runtime.

## 6. e2e Coverage

`../carmen-platform-e2e/tests/super-admins/super-admin-manage.spec.ts` (1 spec file, 2 tests) was last touched at commit `bb8f671` (2026-06-11, the suite's original import from `carmen-platform`) and has not been updated since. `SuperAdminManagement.tsx` was rewritten from a `DataTable` into the current card-based roster at commit `28f92eb` (2026-09-02, `#244`, "ทำให้หน้านี้เป็นทะเบียนคน ไม่ใช่ตารางข้อมูล" — "make this page a registry of people, not a data table"). The suite predates that rewrite by nearly three months and, on reading its page object against current source, **fails at the shared test fixture itself — before either test's own body runs — not merely in individual assertions**:

- `SuperAdminManagementPage.goto()` (`../carmen-platform-e2e/pages/SuperAdminManagementPage.ts:47-53`) awaits `expect(this.userSelect).toBeEnabled(...)`, where `userSelect` is `page.locator('select[aria-label="Select user to add as super admin"]')` — a native `<select>` present on the page by default. Current source has no such element in the initial DOM at all: the picker is a `UserPicker` typeahead rendered as an `<input>` (`UserPicker.tsx:158`, `aria-label={ariaLabel}`, confirmed as an `<input>` not a `<select>`), and it exists only inside the `Dialog` opened by clicking "Add Super Admin" (`SuperAdminManagement.tsx:301-338`) — closed by default (`showAddDialog` starts `false`, line 70). Both tests' `beforeEach` calls `goto()`, so both tests fail here, before checking anything test-specific.
- `adminRows` (`div.divide-y > div`) and `removeButtons` (`button[aria-label^="Remove "][aria-label$=" as super admin"]`) assume `<div>` rows and an aria-label of the shape "Remove `<name>` as super admin." Current markup is `<ul className="divide-y">`/`<li>` (`SuperAdminManagement.tsx:284,422`), and the current i18n key is `removeAria: 'Remove super admin {{name}}'` (`../carmen-platform/src/i18n/en.ts:3638`) — a different word order that the page object's suffix-anchored selector (`$=" as super admin"`) would never match even if the tag name were fixed.
- `addButton` is `getByRole('button', { name: 'Add', exact: true })`. Current source has no button whose accessible name is exactly "Add": the header action reads "Add Super Admin" at the default (desktop) viewport (`sm:inline` span, `SuperAdminManagement.tsx:228`) and the dialog's submit button also reads "Add Super Admin" (or "Adding..." mid-request) (line 359) — never the bare word "Add."

What the suite got right and would still hold if the fixture were fixed: the toast copy. `addSuccess`/`removeSuccess` in current i18n (`en.ts:3616,3618`: "Super admin added successfully" / "Super admin removed successfully") match the strings the spec waits for verbatim (`super-admin-manage.spec.ts:53,56`) — a coincidence worth noting rather than evidence the rest of the suite is close to working. **Net assessment: this suite is not usable as current evidence for any behavior on this page** — it cannot even reach a loaded state under current source — and every claim on this page traces to `../carmen-platform`/`../carmen-turborepo-backend-v2` source directly, never to this suite. Fixing the suite (new locators for the `UserPicker` dialog, the `<ul>/<li>` roster, and the current aria-label/button-text strings) is out of scope for this documentation task, per this plan's standing rule that e2e maintenance is separate work.

## 7. Edge Cases

| Scenario | Behavior | Source |
|---|---|---|
| Self-removal via the UI | Remove control is replaced with static text; no request is ever sent | `SuperAdminManagement.tsx:405-408` |
| Self-removal via a direct API call | **Not prevented.** `remove(id)` has no check comparing the row's `user_id` to the caller's own | `platform_super_admin.service.ts:161-182` (verified: only an existence check, no ownership check) |
| Removing the last remaining active super admin | **Not prevented anywhere** — `add`, `remove`, and `list` contain no "at least one must remain" check | Full read of `platform_super_admin.service.ts` |
| Adding a `user_id` that already has an active row | `409 ALREADY_EXISTS`; frontend clears the stale selection and refetches on exactly this status code | `platform_super_admin.service.ts:132-141`; `SuperAdminManagement.tsx:151-160` |
| A listed super admin's underlying `tb_user` row is soft-deleted or deactivated | Row is **deliberately kept visible** (not filtered) so the privilege can still be revoked; row renders with an em dash where the name/email would be if both are empty | `platform_super_admin.service.ts:74-78`; `SuperAdminManagement.tsx:28-33,433-435` |
| Who granted a privilege, after the fact | **Not recorded.** `created_by_id`/`deleted_by_id` are never written for this table; the roster can only ever show *when*, never *who* did the granting/revoking | §3.1, §5.1, §5.3 |
| A super admin's session is already open in a browser tab when their row is removed | Backend calls from that tab are checked live and correctly denied on the next request; the tab's own cached `effectivePermissions` (fetched only at login/mount) keeps showing super-admin UI until reload or re-login | §5.4 |
| The very first super admin, on a brand-new deployment | Cannot be created through the UI or API — every endpoint requires an existing active super admin. Must be created by the `SUPER_ADMIN_USER_ID` seed script writing directly to the database | §5.2 |

## 8. Recommendations

Treat this page as a break-glass control, not a routine admin screen: every grant here is a full RBAC bypass, both frontend and backend, confirmed at the exact short-circuit lines cited in §2. Because removal is a soft delete with no server-side self-check and no minimum-headcount guard (§3.3, §7), a second pair of eyes before removing a row — especially one's own, or the last remaining row — is a process control this screen does not enforce for you. Anyone testing this module with a reduced-permission session should note there is no reduced-permission session to test with respect to *this* module specifically — the only two states are "super admin" and "not," and the existing e2e suite (§6) currently cannot exercise either state against the current UI. A rewritten suite should assert the `UserPicker` dialog flow, the `<ul>/<li>` roster shape, and the current toast/aria-label strings directly from source rather than reusing any locator from the pre-2026-09-02 suite.

## 9. Related Modules

- [RBAC](/en/platform/rbac) — owns the permission-key/role-bundle axis this module deliberately sits outside of; §2 above shows exactly where `is_super_admin` short-circuits that system on both sides.
- [User Platform](/en/platform/user-platform) — the ordinary, RBAC-scoped way to grant platform privileges; contrast with this module's unconditional bypass.
- [Cluster Admin](/en/platform/cluster-admin) — a second axis this same flag also short-circuits: `ClusterAdminAuthzService.isPlatformSuperAdmin` treats every super admin as an administrator of every cluster (§4 above).
- [Users](/en/platform/users) — owns the `tb_user`/`tb_user_profile` records this module's roster joins against for display only (§3.1).

## 10. Reference Sources

All `../carmen-platform` paths are HEAD `157a65e` (2026-09-04); all `../carmen-turborepo-backend-v2` paths are HEAD `937cf5ac4` (2026-09-06); `../carmen-platform-e2e` is HEAD `a8e3b31` (2026-08-25), with the `super-admins` spec itself last touched at `bb8f671` (2026-06-11).

- `src/pages/SuperAdminManagement.tsx` — the whole screen (read in full, 484 lines).
- `src/services/superAdminService.ts` — `list`/`add`/`remove`.
- `src/types/index.ts:968-986` — the `SuperAdmin` interface and its audit-shape comment.
- `src/components/nav/platformNav.ts:44-46,94-104` — the nav row, its Thai divider comment, and `buildPlatformNav`'s filter.
- `src/App.tsx:443-448` — the route.
- `src/components/PrivateRoute.tsx:38-106` — the frontend guard, including ordering relative to the feature-flag check.
- `src/context/AuthContext.tsx:66,82-89,164,256` — `isSuperAdmin`, `fetchEffectivePermissions`, and when each is called.
- `src/utils/permissions.ts:50-78` — `checkPermission`'s and `checkPlatformAuthority`'s super-admin short-circuits.
- `src/components/UserPicker.tsx` — the typeahead used by the Add dialog.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-super-admins/{platform-super-admins.controller.ts,platform-super-admins.service.ts}` — the HTTP surface and its RPC proxy.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-super-admin.guard.ts` — the live, uncached `is_super_admin` re-check.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-permission.guard.ts:100-104` — the super-admin bypass shared by every RBAC-gated backend route.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/platform_super_admin/{platform_super_admin.service.ts,platform_super_admin.controller.ts,platform_super_admin.service.spec.ts}` — the table's only reader/writer, and its own test suite confirming the soft-delete/no-self-check/no-last-admin-check behavior described in §3.3, §5.3, §7.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/platform_permission/effective_permissions.service.ts:31-32,90` — where `is_super_admin` enters the effective-permissions payload.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:1090-1104` — the `tb_platform_super_admin` model.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/{20260610073505_add_god_mode,20260612000000_add_doc_version}/migration.sql` — table creation and the later `doc_version` column.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-super-admin.ts` — the bootstrap path (§5.2).
- `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts` (`SUPER_ADMIN_NOT_FOUND`, 404) and `../carmen-turborepo-backend-v2/packages/nest-result/src/std-response.ts:144` (`ALREADY_EXISTS` → 409).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/enrichment/audit-shape.ts:1-7` and `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/enrichment/enrichment.service.ts` — the `@EnrichAuditUsers()` mechanism cited in §3.1's audit-trail finding.
- Cross-module `is_super_admin` consumers cited in §4: `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts:2371-2385`, `../carmen-turborepo-backend-v2/apps/micro-business/src/tenant/tenant.service.ts:374-386`, `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/services/permission.service.ts:372-382`, `../carmen-turborepo-backend-v2/apps/micro-cluster/src/common/cluster-admin-authz.service.ts:30-36`.
- `../carmen-platform-e2e/tests/super-admins/super-admin-manage.spec.ts` and `../carmen-platform-e2e/pages/SuperAdminManagementPage.ts` — read in full for §6.

## 11. Pages in This Module

This module is a single page. `tb_platform_super_admin` is documented in §5 above rather than on a separate `data-model` page, and there is no `permissions` page — §4's five-row gate matrix is the entire permission surface, and every one of its five rows resolves to the same `isSuperAdmin` check. See the parent [Platform book index](/en/platform).
