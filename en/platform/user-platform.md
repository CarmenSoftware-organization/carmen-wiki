---
title: User Platform
description: Assigns RBAC platform roles — platform-wide or per-cluster — to existing tb_user accounts, the privilege-registry screen split out of RBAC and Users. The detail route is /platform/user-platform/:userId, with no /edit suffix; most real workflows on it also need user.read from the Users module, a dependency this module's own nav gate does not cover.
published: true
date: '2026-09-06T21:00:00.000Z'
tags: book/platform, user-platform
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# User Platform

> **At a Glance**
> **Components:** `UserPlatformManagement` (list) &nbsp;·&nbsp; `UserPlatformEdit` (per-user detail) &nbsp;·&nbsp; **Routes:** `/platform/user-platform` &nbsp;·&nbsp; `/platform/user-platform/:userId` — **note the param is `:userId`, and there is no `/edit` suffix**, unlike almost every other edit route in this book &nbsp;·&nbsp; **Nav:** `permission: 'user_platform.read'`, `feature: 'user_platform'`, `groupKey: 'navGroup.platform'` (`platformNav.ts:43`) — **not** `superAdminOnly` &nbsp;·&nbsp; **Permission keys:** `user_platform.read` (both routes) + `user_platform.manage` (every mutating affordance on both screens) &nbsp;·&nbsp; **A second, undeclared dependency:** most of what the detail screen shows also requires `user.read`, a [Users](/en/platform/users) module key this module's own route guard never checks — see §4 and [Permissions](/en/platform/user-platform/permissions) §3 for the exact trace &nbsp;·&nbsp; **e2e suite:** `user-platform` (2 specs) — has coverage, unlike most modules in this batch, but both specs target UI this screen no longer has; see [UI Screens](/en/platform/user-platform/ui-screens) §4 &nbsp;·&nbsp; **Sub-pages:** 2

## 1. Overview

User Platform is where a [RBAC](/en/platform/rbac) platform role — platform-wide, or scoped to one cluster — gets attached to an existing user account. It was split out of the RBAC module's own screens into its own nav row and its own pair of components, and both were rewritten the same day, 2026-09-02, into what their own commit messages call a "privilege registry" rather than a generic CRUD table: `UserPlatformManagement` (`../carmen-platform` commit `fc690cb`, PR #250) and `UserPlatformEdit` (`f6e91c9`, PR #251).

`/platform/user-platform` lists every user who holds at least one platform-role assignment — someone with none is excluded server-side and never appears here. Clicking a row's name (an `<a>` via react-router's `Link`, not a button) or its "Manage roles" action navigates to `/platform/user-platform/:userId` — **the id is a plain path segment, with no `/edit` suffix.** A reader who pattern-matches from `/users/:id/edit`, `/clusters/:id/edit`, `/applications/:id/edit`, and nearly every other detail route in this book will construct `/platform/user-platform/:userId/edit` and get a 404 — that route does not exist (`../carmen-platform/src/App.tsx:458-465`). The detail screen itself has no read/edit-mode toggle either: it is one page that assigns and removes role grants directly, not a form with a Save button.

Both routes are gated identically at the route level — `requiredPermission="user_platform.read"`, `feature="user_platform"` (`App.tsx:453,461`) — so holding the read key alone is enough to *navigate* to any user's detail page. Whether that page shows anything useful once you're there is a separate question, answered in §4.

## 2. Business Context

**A platform user is not a kind of account — it is a `tb_user` row that happens to hold at least one row in `tb_user_tb_platform_role`.** Nothing on this screen creates that underlying account. A person becomes eligible to appear here the same way anyone becomes a `tb_user` row at all — created directly on [Users](/en/platform/users) (`/users/new`), through a cluster/BU invitation, or through self-service sign-up — and only starts *appearing* on this registry the moment someone with `user_platform.manage` grants them a first role, either through **Grant Access** on the list screen (any user, searched by name) or **Add Role** on an existing holder's own detail page.

This is the same distinction [Users](/en/platform/users) §2 already states from its own side: "what the account can *do* in the Platform admin SPA is not stored [on the user row] — that is the RBAC module's role assignments." User Platform is where those assignments are actually authored. Concretely, what you can change here and cannot change on `/users/:id/edit` is exactly one thing — which platform roles a user holds, and at what scope — and what you can change on `/users/:id/edit` and cannot change here is everything about the account itself: `username`, `email`, name fields, `is_active`, password, cluster/BU membership. Deactivating or deleting the account is a Users-module action; it does not touch this registry directly, though an account that goes inactive still keeps its role rows and is flagged for it here (§3.4, [UI Screens](/en/platform/user-platform/ui-screens) §3).

The registry framing itself is deliberate, not cosmetic: this screen exists so an access reviewer can ask "who can do what to the whole platform, and how did they get it" without cross-referencing the Users directory and the Roles catalog by hand. Every row states scope, every grant states who issued it and when (where that provenance is obtainable — §3.2), and an inactive holder who still carries privilege is called out rather than left to blend into an otherwise-normal-looking list.

## 3. Key Concepts

### 3.1 The registry-wide summary aggregate

`GET /api-system/platform/users` (`userPlatformService.getAll()`, backed by `UserPlatformRolesController.listUsers`, `RequirePlatformPermission('user_platform.read')`) returns not just the current page of holders but a `summary` block — `holders`, `platform_wide`, `cluster_only`, `assignments`, `inactive` — describing **every** holder matching the active filter/search, not just the loaded page (`user_platform_role.service.ts:541-572`, `buildRegistrySummary`). This is what lets `PlatformAccessSummary` (the band above the table) show an accurate inactive-holder count and platform-wide/cluster-scoped split even when the one inactive holder is sorted onto page 3.

The frontend type for this field is optional and its own comment frames it as something that "ships in a later backend deploy" (`types/index.ts:587-590`), and `PlatformAccessSummary.tsx` correctly renders an explicit "summary isn't available yet" fallback for that case. **At this plan's pinned source HEAD, that transition has already completed on the backend — every response carries a `summary` object, though not through one unconditional call.** `listPlatformUsers()` branches on whether any live assignment matches the filter at all: when none does (`grouped.length === 0`), it returns a zeroed `summary` literal directly, without ever calling `buildRegistrySummary()` (`user_platform_role.service.ts:350-356`). Otherwise, `buildRegistrySummary(matched)` is called exactly once, against the full filtered user set (line 411), and that single result is threaded through every remaining return path rather than recomputed — the page-out-of-range branch (`pageIds.length === 0`, lines 432-438) and the final response (lines 517-521) both reuse the same `summary` variable. So the two branches differ in *how* they produce a summary — one is a hardcoded zero-value literal, the other actually calls the aggregate function — but both always produce one. The gateway proxy then forwards whatever it receives (`user-platform-roles.service.ts:140-148`), which per the above is always a `summary`-bearing response. The frontend's fallback branch remains correct defensive code; it is simply unreachable against the backend this plan documents. Do not read its continued presence in source as evidence the aggregate is still rolling out.

One computation detail worth stating precisely, because it is easy to get backwards: `holders` and `inactive` are counted over the **filtered** set (respecting an active role/cluster/status filter), but `platform_wide`/`cluster_only` are computed from each matched holder's **full** set of live assignments, deliberately not narrowed by an active role/cluster filter — so a holder filtered in by one role still counts toward the platform-wide/cluster-scoped split based on everything they hold, not just the role that matched the filter (`user_platform_role.service.ts:534-538`, the method's own doc-comment). The reasoning stated there is the same one [UI Screens](/en/platform/user-platform/ui-screens) §2 gives for the per-row assignment list: understating a holder's actual reach on an access-review screen is the wrong failure mode.

### 3.2 Two entry points, one pair of write endpoints — and a documented race

Granting a role happens from either screen: **Grant Access** on the list (`GrantAccessDialog`, any user picked via a search typeahead, one or more roles at one shared scope, `POST .../roles/bulk`) or **Add Role** on an existing holder's detail page (`AddRoleSheet`, one role at a time, `POST .../roles`). Both ultimately write the same table, `tb_user_tb_platform_role`, and both reject an exact duplicate (same user + role + scope, live) with a 409 before writing anything — `assign()`/`assignBulk()` in `user_platform_role.service.ts:103-141,175-218`.

`assignBulk()`'s own comment states a caveat that also applies to the single-role path even though only this comment spells it out: the duplicate check is read-then-write, and the unique index behind it includes `deleted_at`, which Postgres treats as distinct-per-NULL in a unique index by default — so it does **not** block two concurrent identical grants from both landing as separate live rows (`user_platform_role.service.ts:220-228`). Removing one afterward still works normally; the registry would just show the same role/scope pair twice in the interim. Worth knowing before treating a duplicate row as a UI bug rather than the documented race it is.

### 3.3 `tb_user`'s three email-verification columns — the only screen that shows them

Three columns exist on `tb_user` that no page in the Users module reads at all: `email_verified_at`, `email_verification_token_hash`, `email_verification_expires_at` (added by migration `20260804000000_user_email_verification`, `schema.prisma:485-487`). `UserPlatformEdit.tsx` is the **only** SPA surface for any of them, and even there only the first: `email_verified_at?: string | null` (line 43) feeds a single derived boolean, `emailVerified = !!userRecord?.email_verified_at` (line 195), rendered as an outline "Email not verified" badge beside the page header when false. The token/expiry pair is never sent to the frontend or displayed anywhere.

What sets them, none of it on this screen: `email_verified_at` is written to `new Date().toISOString()` either at account-creation time — for an invitation-based account, whose email was already proven before the account exists (`AuthService`'s `createVerifiedUser`, `auth.service.ts:927-931`) — or later, when `verifyEmail(token)` consumes a still-valid `email_verification_token_hash`/`email_verification_expires_at` pair (`auth.service.ts:1244-1302`). `resendVerificationEmail()` is what (re)issues that token pair for an account whose email is not yet verified (`auth.service.ts:1329-1375`). A `null` `email_verified_at` also blocks login outright, independent of anything on this screen (`auth.service.ts:498`) — every account that existed before the migration was backfilled to "verified" at deploy time specifically so this new gate would not lock out the platform's entire existing user base (`20260804000000_user_email_verification/migration.sql`).

The practical implication for this module: an "Email not verified" badge on a role holder is not a cosmetic detail — it describes an account that may not even be able to log in and use the role being reviewed. This screen surfaces that fact; changing it requires the account owner to complete verification (or an operator to intervene through the auth flows above), not anything on `/platform/user-platform`.

### 3.4 Inactive holders, and what "reach" means on the detail page

Both screens treat "holds privilege while deactivated" as a finding, not a routine state: the list's summary band surfaces an inactive-holder count as a clickable warning, and the detail page repeats the same warning per-holder (`!isActive && roleAssignments.length > 0`, `UserPlatformEdit.tsx:277-285`) — because a reviewer opening one person's page should not have to remember a count they saw on a different screen. The detail page's own "reach" headline (`AccessReachBand`) is derived entirely from `roleAssignments`, which is a *separate* fetch from the account record itself (§4) — see [Permissions](/en/platform/user-platform/permissions) §3 for what happens to that headline when the fetch that populates it fails.

## 4. Roles and Permissions

| Surface | Permission | Notes |
| --- | --- | --- |
| Sidebar entry, both routes | `user_platform.read` | `platformNav.ts:43`; `App.tsx:453,461` |
| Grant Access (list header + empty state), Revoke all access (list row menu), Add Role (detail), Remove role (detail row) | `user_platform.manage` | The **only** other key this module uses anywhere — a repo-wide grep of `user_platform\.` finds no third literal. Every write endpoint's backend decorator agrees exactly: `POST .../roles`, `POST .../roles/bulk`, `DELETE .../roles/:id` are all `RequirePlatformPermission('user_platform.manage')` |
| Loading the detail page's account identity and role list | **`user.read`** — not `user_platform.read` | The detail route's own guard never checks this. See [Permissions](/en/platform/user-platform/permissions) §3 for the full trace of what a session missing it actually sees |

This module's own write-side gating is unusually clean compared to two other modules already documented in this plan ([Platform Config](/en/platform/platform-config) §4.3, [Email Settings](/en/platform/email-settings) §4.2): the frontend `<Can>` gate and the backend `@RequirePlatformPermission` decorator check the **identical** resource and action, `user_platform.manage`, on all four mutating affordances across both screens. The complication here is not a frontend/backend mismatch — it is that reaching this module at all (`user_platform.read`) is not the same as being able to *see* anything once you reach the detail page. Full gate matrix, backend guard table, and the exact key combination that reproduces the gap: [Permissions](/en/platform/user-platform/permissions).

## 5. Related Modules

- [Users](/en/platform/users) — owns the `tb_user` account this module attaches roles to: identity, activation, and cluster/BU membership are all edited there, never here. See §2 for the exact division and §3.3 for the email-verification columns this module surfaces on the Users module's own behalf.
- [Platform RBAC](/en/platform/rbac) — owns the catalog and the roles themselves (`tb_platform_role`, `tb_platform_permission`), the `Scope` union this module's `PlatformUserScope`/`Scope` types mirror, and documented this module at a summary level before this page existed; this page is now the fuller treatment.
- [Super Admins](/en/platform/super-admins) — a separate, `superAdminOnly`-gated bypass flag (`tb_platform_super_admin`), not a role in `tb_platform_role` and not something this screen shows or grants.
- Clusters — the `cluster_id` a scoped assignment resolves against; both Grant Access and Add Role read the cluster list purely to populate a scope picker (`cluster.read`, best-effort — a failed fetch degrades the picker to raw ids rather than blocking the grant).

## 6. Reference Sources

All paths `../carmen-platform` (HEAD `157a65e`, 2026-09-04) unless prefixed `../carmen-turborepo-backend-v2` (HEAD `937cf5ac4`, 2026-09-06) or `../carmen-platform-e2e` (HEAD `a8e3b31`, 2026-08-25).

- `src/pages/UserPlatformManagement.tsx` — the list/registry screen (commit `fc690cb`, PR #250, 2026-09-02).
- `src/pages/UserPlatformEdit.tsx` — the per-user detail screen (commit `f6e91c9`, PR #251, 2026-09-02), including the `UserDetailRecord.email_verified_at` field (line 43) and its derived badge (line 195).
- `src/pages/userPlatformManagement/{PlatformAccessSummary,roleChips,GrantAccessDialog}.tsx`, `src/pages/userPlatformEdit/{AccessReachBand,MembershipCard,RoleGrantList,AddRoleSheet}.tsx` — the supporting components documented in full on [UI Screens](/en/platform/user-platform/ui-screens).
- `src/services/userPlatformService.ts`, `src/services/userRoleService.ts` — the two REST clients this module calls directly.
- `src/components/nav/platformNav.ts:43`, `src/App.tsx:451-465` — nav entry and route registration.
- `src/types/index.ts:544-603` — `Scope`, `PlatformUserScope`, `PlatformUserRoleAssignment`, `PlatformUserRow`, `PlatformUserRegistrySummary`, `PlatformUsersResponse`.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/user-platform-roles/user-platform-roles.controller.ts` — the REST surface and every route's permission decorator (§4).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/user-platform-roles/user-platform-roles.service.ts:140-148` — the `summary` forwarding logic (§3.1).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/user_platform_role/user_platform_role.service.ts` — `assign`/`assignBulk`/`remove`/`listPlatformUsers`/`buildRegistrySummary` (§3.1, §3.2).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` — `createVerifiedUser` (lines 919-933), `verifyEmail` (1244-1302), `resendVerificationEmail` (1329-1375), the login gate (line 498) (§3.3).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma:485-487` — the three `tb_user` email-verification columns; migration `20260804000000_user_email_verification`.
- `../carmen-platform-e2e/tests/user-platform/{user-platform-list,user-platform-config}.spec.ts` and `pages/UserPlatform{ManagementPage,EditPage}.ts` — see [UI Screens](/en/platform/user-platform/ui-screens) §4 for the specific ways this suite no longer matches current source.

## 7. Pages in This Module

- [UI Screens](/en/platform/user-platform/ui-screens) — both screens' full layout and behavior, and the e2e suite's staleness findings.
- [Permissions](/en/platform/user-platform/permissions) — the full gate matrix and the `user.read` gap traced end to end.
