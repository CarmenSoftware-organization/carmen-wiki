---
title: User Platform — Permissions
description: user_backstage.read gates both routes; user_backstage.manage gates every mutating action — but most of the detail screen also needs the Users module's user.read.
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, user-platform, permissions
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# User Platform — Permissions

> **At a Glance**
> **Two keys total:** `user_backstage.read` (both routes' nav/route gate) and `user_backstage.manage` (every mutating affordance on both screens) — a repo-wide grep of `user_backstage\.` finds no third literal &nbsp;·&nbsp; **Frontend and backend agree exactly** on all four write actions — same resource, same action, no cross-key mismatch of the kind found in [Platform Config](/en/backstage/platform-config) §4.3 or [Email Settings](/en/backstage/email-settings) §4.2 &nbsp;·&nbsp; **The real gap is a read, not a write:** the detail page's account identity and role list both require `user.read` — a [Users](/en/backstage/users) module key — which `user_backstage.read` alone does not grant, and the route guard never checks &nbsp;·&nbsp; **Not silent** — the failure surfaces as an explicit error banner, but the page beneath it still reads as "this holder has no roles," which is not always true &nbsp;·&nbsp; **No e2e coverage of this trace** — the `user-platform` suite's two specs do not exercise a reduced-permission session at all (see [UI Screens](/en/backstage/user-platform/ui-screens) §4)

## 1. Overview

This module's own permission surface is small and, on the write side, clean: two keys, checked identically on the frontend and the backend, with no key renamed or retired since it was split out of RBAC. The interesting behavior is not a mismatch inside this module — it is a dependency this module's screens have on a key that belongs to a different module entirely, one the route guard was never written to require.

## 2. Gate matrix

| Surface | Guard | Key | Source |
| --- | --- | --- | --- |
| `/backstage/user-backstage` route | `PrivateRoute` | `user_backstage.read`, `feature: 'user_backstage'` | `App.tsx:497-504` |
| `/backstage/user-backstage/:userId` route | `PrivateRoute` | `user_backstage.read`, `feature: 'user_backstage'` | `App.tsx:505-512` |
| Sidebar entry | nav filter | `permission: 'user_backstage.read'`, `feature: 'user_backstage'`, `groupKey: 'navGroup.backstage'` — not `superAdminOnly` | `backstageNav.ts:48` |
| Grant Access button (list header, empty state) | `<Can>` | `user_backstage.manage` | `UserBackstageManagement.tsx:417,586` |
| Revoke all access (list row menu) | `<Can>` | `user_backstage.manage` | `UserBackstageManagement.tsx:390` |
| Add Role sheet (detail page) | `<Can>` | `user_backstage.manage` | `UserBackstageEdit.tsx:302` |
| Remove role (detail page, per row) | `<Can>` | `user_backstage.manage` | `RoleGrantList.tsx:126` |
| Manage roles (list row menu → navigate to detail) | no RBAC permission key on the menu item — gated instead by the detail route's own `user_backstage.read` guard | — | `UserBackstageManagement.tsx:383-389` |

Backend, all in `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/user-backstage-roles/user-backstage-roles.controller.ts`, HEAD `937cf5ac4`:

| Route | Guard | Source |
| --- | --- | --- |
| `GET /api-system/backstage/users` | `AppIdGuard` + `BackstagePermissionGuard`, `user_backstage.read` | lines 88-90 |
| `GET /api-system/backstage/users/:user_id/roles` | same, **`user.read`** | lines 135-137 |
| `POST /api-system/backstage/users/:user_id/roles` | same, `user_backstage.manage` | lines 180-182 |
| `POST /api-system/backstage/users/:user_id/roles/bulk` | same, `user_backstage.manage` | lines 233-235 |
| `DELETE /api-system/backstage/users/:user_id/roles/:assignment_id` | same, `user_backstage.manage` | lines 280-282 |

Two calls the detail page makes are **not** in the table above because they hit a different controller entirely: `GET /api-system/user/:user_id` (the account record itself, `userService.getById`) is gated `user.read` on `backstage-user.controller.ts:264-266`, and `GET /api-system/user?...` (the search behind `GrantAccessDialog`'s `UserPicker`, on the list screen) is gated `user.read` on the same controller, lines 128-130. Both are [Users](/en/backstage/users) module endpoints — this module reuses them rather than duplicating a second way to look someone up.

## 3. The `user.read` gap, traced end to end

**The claim, precisely stated:** a session holding `user_backstage.read` and `user_backstage.manage`, but not `user.read`, can reach both screens and can technically trigger every write action this module exposes — but cannot see whether a given holder already has the role they are about to grant, on either screen, and on the detail page specifically sees a broken-looking page while doing it. This is a real, reproducible gap, not a hypothetical: `user_backstage.read` and `user.read` are two different resources, checked by two different controllers, and nothing anywhere ties them together.

**On the list screen**, this session sees the registry table load and filter normally — `GET /api-system/backstage/users` only needs `user_backstage.read`, which it has. Revoking an existing holder's access works fully; nothing in that path touches `user.read`. Granting access to someone new is where it breaks: `GrantAccessDialog`'s `UserPicker` searches via `GET /api-system/user`, which 403s. Per the component's own design (`useUserSearch.ts`, `UserPicker.tsx`), that failure surfaces **inline, inside the dropdown**, never as a toast — so the dialog does not crash, but no user can ever be selected, and `handleSubmit` refuses to submit without one (`if (!user) { toast.error(...); return; }`). Grant Access is reachable and clickable; it cannot be completed.

**On the detail page**, the sequence in `UserBackstageEdit.tsx`'s `load()` (lines 134-160) is: `userService.getById(userId)` first, then — only if that succeeds — `loadAssignments()` (which calls `GET .../roles`, also `user.read`) and `loadProvenance()` (which calls the registry endpoint, `user_backstage.read` — this one succeeds). Because `userService.getById` is awaited first and both calls it gates share the *same* permission, this session's `load()` throws on the very first line and never reaches the others — there is no split-brain state where the account loads but roles don't, or vice versa; they fail together, deterministically, every time. The catch block sets a visible error banner (`t('pages.userBackstage.loadUserFailed', { detail: ... })`, set at `UserBackstageEdit.tsx:159` and rendered in the `role="alert"` banner at `UserBackstageEdit.tsx:265-271`) rather than crashing or hanging.

**What the rest of the page shows anyway, because nothing below that catch block is gated on the fetch having succeeded:** `roleAssignments` stays at its initial empty array, so `AccessReachBand` reads "No platform privilege," the "Roles & Scope" card reads "No roles assigned," and `MembershipCard` reads "Not a member of any cluster or business unit" — three confident-sounding empty states sitting directly beneath an error banner that explains why none of them can be trusted. **And the Add Role sheet still renders**, because it is gated purely on `user_backstage.manage` (`UserBackstageEdit.tsx:302`), which this session holds, with no dependency on whether the surrounding page actually loaded. A manager in this exact position — `user_backstage.manage` without `user.read` — can click Add Role and grant a platform-wide or cluster-scoped role to a holder whose *existing* roles they were never shown, risking a redundant grant at a different scope that the backend's own duplicate check (§3.2 of the [landing page](/en/backstage/user-platform)) would not catch, because it only rejects an *exact* role+scope repeat.

**Why this is not the same mistake a previous module's page made.** A different module in this plan asserted a write-side trap for a session that turned out to be structurally unable to reach the button at all, because a failing read gate blanked the control before the write gate could ever matter. That failure mode does **not** apply here: `AddRoleSheet`'s render condition is `<Can permission="user_backstage.manage">` alone (`UserBackstageEdit.tsx:302`) — it has no second condition tied to whether `userRecord`, `roleAssignments`, or `error` resolved successfully. The button is genuinely, unconditionally clickable in this state; this was verified by reading the JSX directly, not assumed from the permission name.

**The reverse combination is not a gap.** A session holding `user.read` but not `user_backstage.read` cannot reach either route at all (`App.tsx:497-512`) — there is nothing to check on the detail page's own dependency in that direction, since the route guard itself is the binding constraint.

## 4. Edge Cases

| # | Scenario | Behaviour | Tester notes |
| --- | --- | --- | --- |
| 1 | Session has `user_backstage.read` + `.manage`, lacks `user.read`; opens an existing holder's detail page | Error banner ("Failed to load user: …"); Access Reach Band reads "No platform privilege"; Roles & Scope reads "No roles assigned"; Add Role sheet still renders and can complete a write | The one combination worth deliberately testing — see §3. Reproduce with a role granted only `user_backstage.*` |
| 2 | Same session, on the list screen, uses Grant Access | `UserPicker` dropdown shows an inline search error for any query; no user can be selected; Submit is blocked client-side (`if (!user) return`) | The dialog never reaches the backend at all in this state — nothing is written, nothing 403s, it simply cannot be completed |
| 3 | Same session, on the list screen, uses Revoke all access on an existing row | Succeeds fully — this action never depends on `user.read` | Confirms the gap is specific to *discovering* a user or a holder's existing roles, not to the write endpoints themselves |
| 4 | Session has `user_backstage.read` only (no `.manage`, no `user.read`) | List loads read-only; detail page shows the same error banner and empty states as edge case 1, with no Add Role/Remove/Revoke controls anywhere | The `.manage`-shaped risk in edge case 1 does not apply here — nothing on the page can be written |
| 5 | Two admins submit an identical Grant Access request (same user, role, and scope) within the same instant | Both can succeed, creating two live duplicate assignment rows | Documented, not hypothetical: the unique index behind the duplicate check is NULL-distinct on `deleted_at` in Postgres, so two concurrent live inserts are not blocked by it (`user_backstage_role.service.ts:198-216`, [Landing](/en/backstage/user-platform) §3.2). Removing one afterward works normally |
| 6 | A holder's account is deactivated while they still hold platform roles | Surfaced twice: an inactive-holder count in the list's summary band (clickable, applies the inactive filter) and a repeated per-holder warning on their own detail page | Deactivating the account happens on [Users](/en/backstage/users), not here — this module only displays the resulting state |
| 7 | Super-admin session exercises any gate on this page | Every `<Can>` check passes unconditionally (`checkPermission()`'s `is_super_admin` short-circuit, [UI Screens](/en/backstage/user-platform/ui-screens) §4) | Never QA this module's permission boundaries from a super-admin session — it cannot reveal the `user.read` gap in §3, which requires a session with `user_backstage.*` specifically withheld from `user.*` |

## 5. Recommendations

- **Test §3's exact combination deliberately** — a role granting `user_backstage.read`/`.manage` without `user.read` — since it is the one scenario in this module that produces a misleading rather than merely restrictive result: empty-looking states that are actually "couldn't check," sitting beside a fully functional write control.
- **Do not test this module's write gating for a frontend/backend mismatch** the way [Platform Config](/en/backstage/platform-config) §4.3 or [Email Settings](/en/backstage/email-settings) §4.2 require — there isn't one here; all four `<Can>` gates and all three write-endpoint decorators check the identical `user_backstage.manage` key.
- **Do not rely on the `user-platform` e2e suite for any permission-boundary test** — both specs run as a super admin and neither exercises a reduced-permission session; see [UI Screens](/en/backstage/user-platform/ui-screens) §4 for the two ways the suite is also stale on plain, non-permission grounds.
- **When verifying an inactive-holder warning or an "Email not verified" badge, confirm you are looking at real state, not the failure mode in edge case 1** — both are legitimate, sourced facts about the account (§3.4/§3.3 of the [landing page](/en/backstage/user-platform)) only when the account fetch actually succeeded.

**References:** all paths `../carmen-backstage` (HEAD `157a65e`) unless prefixed `../carmen-turborepo-backend` (HEAD `937cf5ac4`). `src/App.tsx:497-512` (routes) · `src/components/nav/backstageNav.ts:48` (nav) · `src/pages/UserBackstageManagement.tsx` (list gates, lines 390,417,586) · `src/pages/UserBackstageEdit.tsx` (detail gates and load sequence, lines 134-160,265-271,302) · `src/pages/userBackstageEdit/RoleGrantList.tsx:126` · `src/components/UserPicker.tsx`, `src/hooks/useUserSearch.ts` (inline search-failure behavior) · `src/context/AuthContext.tsx:354-358`, `src/utils/permissions.ts:56` (super-admin short-circuit) · `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/user-backstage-roles/user-backstage-roles.controller.ts` (lines 88-90,135-137,180-182,233-235,280-282) · `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage-user/backstage-user.controller.ts:128-130,264-266` (`user.read` on the Users-module endpoints this module depends on) · `../carmen-turborepo-backend/apps/micro-business/src/authen/user_backstage_role/user_backstage_role.service.ts:198-216` (the duplicate-grant race, edge case 5).
**Cross-links:** [User Platform landing](/en/backstage/user-platform) &nbsp;·&nbsp; [UI Screens](/en/backstage/user-platform/ui-screens) &nbsp;·&nbsp; [Users](/en/backstage/users) &nbsp;·&nbsp; [Backstage RBAC — Permissions](/en/backstage/rbac/permissions) &nbsp;·&nbsp; [Platform Config](/en/backstage/platform-config) &nbsp;·&nbsp; [Email Settings](/en/backstage/email-settings)
