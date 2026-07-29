---
title: Broadcasts — Permissions
description: The single broadcast.send gate across route, sidebar, and Send button — now confirmed enforced server-side too (backend PR #239), with a documented coarse-grant caveat — per-target-mode delivery semantics, and the edge-case matrix for testers.
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, broadcasts, permissions
editor: markdown
dateCreated: 2026-06-10T13:15:00.000Z
---

# Broadcasts — Permissions

> **At a Glance**
> **Gate:** one key — `broadcast.send` — on the route, the sidebar entry, and the Send button &nbsp;·&nbsp; **Server side (confirmed fixed since the last sync):** both endpoints now enforce `broadcast.send` via `PlatformPermissionGuard` (backend PR #239) — no longer client-side only &nbsp;·&nbsp; **Known coarseness:** the guard passes on a platform-wide grant **or** a grant in any single cluster, so a cluster-scoped grantee still reaches the system-wide send modes server-side — true per-cluster scoping is explicitly deferred, not a bug &nbsp;·&nbsp; **Orphan key:** `broadcast.read` is seeded but gates nothing in the SPA &nbsp;·&nbsp; **Delivery:** audience resolved from the row (`category` + `scope_id`) at read time; live socket push only for unscheduled sends

## 1. Overview

Broadcasts has the simplest gate story in the Platform book: a single [Platform RBAC](/en/platform/rbac) key, `broadcast.send`, guards every SPA surface — there is no read/create/update/delete split because sending is the only operation. The seed (`seed.platform-permission.ts`) registers two keys, `broadcast.read` and `broadcast.send`, but `broadcast.read` is an **orphan**: no route, sidebar entry, or `<Can>` references it anywhere (its only SPA occurrence is the dev-only mock permission list in `src/utils/permissions.ts`). Presumably reserved for a future broadcast-history surface.

**Confirmed fixed since the last sync:** the previously-documented server-side gap — the two gateway endpoints checking bearer authentication only, with `broadcast.send` enforced client-side alone — is closed. Backend commit `1fa15ec02` ("Server-side authz enforcement: guard broadcast sends + close DB-password leak (#239)") added `PlatformPermissionGuard` + `@RequirePlatformPermission('broadcast.send')` to both `POST /api/notifications/broadcasts/system` and `/bu`. A companion frontend commit (`9911b8f`) updated the code's own comments to record the fix and repaired a `parseApiError` bug that had silently swallowed nested `{ error: { message } }` API error bodies — so a 403 from the newly-enforced guard now surfaces its real message ("Missing platform permission: broadcast.send") instead of a generic one.

The enforcement is deliberately **coarse**, by design, not by oversight: `PlatformPermissionGuard` resolves the caller's effective permissions and calls `PlatformPermissionService.has()`, which returns true if the required key is present in the **platform-wide** scope **or** in **any single cluster's** scope (verified by direct read of `platform-permission.service.ts`). A user granted `broadcast.send` on exactly one cluster therefore still passes the guard for a `system_all` send that reaches every user platform-wide — the guard does not (yet) check "is this specific action platform-scoped or does it belong to the caller's own cluster." The code's own comments describe **true** per-cluster scoping (system-wide requiring a platform-only grant; BU mode scoped to the target BU's own cluster) as explicitly deferred, pending backend infrastructure to resolve `bu_code → cluster_id` and check that specific bucket — infrastructure that does not exist yet in this repo. The SPA's own `canSendSystem`/`canSend` checks are equally unscoped, so client and server now **agree** on the same (coarse) boundary — this is a narrower, still-real caveat, not the "no server check at all" finding from the last sync.

## 2. Gate matrix

| Surface | Mechanism | Key | Source |
|---|---|---|---|
| `/broadcasts/new` | `PrivateRoute requiredPermission` | `broadcast.send` | `src/App.tsx` |
| Sidebar "Send Broadcast" (Content group, Megaphone icon) | `Layout.tsx` nav filter | `broadcast.send` | `src/components/Layout.tsx` |
| Send button (sticky bottom action bar) | `<Can>` | `broadcast.send` | `BroadcastCompose.tsx` (added in carmen-platform commit `f3f77cf`) |
| "All users" + "Specific users" tabs | in-component `hasPermission('broadcast.send')` (`canSendSystem`) | `broadcast.send` | `BroadcastCompose.tsx` |
| `POST /api/notifications/broadcasts/system` / `/bu` | `KeycloakGuard` + `PlatformPermissionGuard` | `broadcast.send` (coarse: platform-wide or any cluster) | gateway `notification.controller.ts`, `platform-permission.guard.ts` |

Tester-relevant readings:

- **Every SPA gate is the same key**, so the in-component layers are redundant today: a session without `broadcast.send` never gets past the route guard (`Forbidden` inside the Layout shell — renamed from the earlier inline `AccessDenied`), so the tab-hiding and the `<Can>` around Send are unreachable defensive code. They only become observable if the route guard's key ever diverges from the component's.
- **The real enforcement boundary is now authorization, matching authentication** — both the SPA and the API require `broadcast.send`, and a `.send`-less session's direct POST now fails with a 403 (not a silent success). This reverses the last sync's finding.
- **The remaining gap is scope granularity, not presence of a check.** A user with `broadcast.send` scoped to a single cluster can still send a system-wide (`system_all`) broadcast through the API (and through the SPA, since `canSendSystem` doesn't scope either) — server and client are consistent with each other, but neither restricts a cluster-scoped grant to that cluster's own audience. Treat this as a known, deferred limitation when writing test cases, not a defect to file fresh.
- Reset, the target tabs, and all form fields are ungated — only Send is wrapped.
- Super-admin and bootstrap sessions pass every gate; never QA this matrix from one.

## 3. Target-mode delivery semantics

Who actually receives a broadcast is decided by micro-notification, per mode:

| Mode | Storage | Audience (read path) | Live push (unscheduled only) | Email side-effect |
|---|---|---|---|---|
| `system_all` | one `tb_broadcast_notification` row, `category = 'system-to-user'`, `scope_id = null` | **every user** — the scoped list queries match `system-to-user` rows unconditionally | socket emit to every active, non-deleted user id | all active users' emails |
| `system_users` | one `tb_notification` row **per existing recipient id** (unknown ids silently dropped) | exactly those users — personal rows, `to_user_id` match | socket emit per row, then `is_sent = true` | the picked users' emails |
| `bu` | one `tb_broadcast_notification` row, `category = 'bu-to-user'`, `scope_id` = resolved BU id | users whose `tb_user_tb_business_unit` membership (live rows) contains the scope BU | socket emit to current BU member ids | BU members' emails |

Three behaviors that follow from "audience resolved at read time" (broadcast rows only):

1. **Membership is evaluated per query, not per send.** A user added to the BU *after* a BU broadcast was sent still sees it — in the unread list indefinitely (no time window) and in the recent list for 30 days; a user removed stops seeing it. There is no recipient snapshot.
2. **Scheduled rows deliver passively.** The list queries hide rows until `scheduled_at <= NOW()`; once due, the broadcast appears on the next fetch. **No socket push ever fires for a scheduled broadcast** — the create-time emit is skipped and nothing replays it later.
3. **Read state is lazy and per-user** (`tb_user_broadcast_action`, unique per broadcast×user): no rows are written at send time, so "sent" can never be confirmed from the database beyond the broadcast row's existence.

The email fan-out (only when SMTP is configured on micro-notification; suppressible per-send via `metadata.notify_email = false`, which the SPA never sends) fires **at create time even for scheduled sends** — the schedule defers in-app visibility, not email.

## 4. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | Stale recipients leak into "All users" | Picking recipients under *Specific users* and then switching to *All users* does **not** clear them; `buildSystemPayload` includes `userIds` whenever recipients exist, so the send silently becomes targeted — while the confirm dialog claims "Send to ALL users?" | Verified in `BroadcastCompose.tsx` as of 2026-06-10: tab switches preserve form state and `system_all` validation ignores recipients. Reset (or removing the badges) clears them. Worth a bug report against the SPA |
| 2 | Scheduled *Specific users* send is visible immediately | The personal-row list queries do **not** filter `scheduled_at` (only broadcast-row queries do), so targeted scheduled notifications appear in recipients' lists at once; the deferred live emit never happens — `getScheduledNotifications()` (due + unsent) has **no caller** anywhere, and micro-cronjobs' NotificationExecutor only posts recurring configured jobs | The gateway DTO comment promises "the live emit is deferred to the scheduled worker", but no such worker exists. Scheduling is only honored for `system_all`/`bu` sends |
| 3 | No way to see or cancel a sent/scheduled broadcast | The SPA has no list route, and no gateway or micro-notification endpoint lists, updates, or deletes broadcasts. Read queries respect `deleted_at`, but nothing writes it | Retracting a mis-send is a manual DB soft-delete (`UPDATE tb_broadcast_notification SET deleted_at = NOW() …`). For mis-scheduled broadcasts this is the only abort path |
| 4 | Scheduled time in the past | Client validation rejects (`Scheduled time must be in the future`, against `Date.now()` at validation time); the backend does not validate — an API caller sending a past `scheduled_at` creates a row that is immediately visible (it passes the `<= NOW()` filter) but never live-pushed | The SPA *can* slip a past time through: validation runs when Send is clicked, but confirming does **not** re-validate — a confirm dialog left open past the scheduled instant submits a now-past `scheduled_at` |
| 5 | Custom type rejected | Other… requires `[A-Z0-9_]+`, ≤50 chars; input auto-uppercases typed and pasted text alike, so lowercase can never reach validation — the regex error is reachable only with disallowed characters such as spaces or hyphens | Server accepts any varchar(255) — the regex is SPA-only. API callers can store arbitrary `type` strings |
| 6 | BU list fails to load / has >100 BUs | Load failure shows the parsed error with an inline Retry; the fetch caps at `perpage: 100`, so BUs beyond the first 100 are unselectable | The cap is invisible in the UI — on large clusters verify the target BU appears before filing "missing BU" defects |
| 7 | BU code unknown or BU soft-deleted at send time | micro-notification resolves `bu_code` against live BUs; failure surfaces as a 500-enveloped "Failed to create notification" with details `Business unit not found: <code>` | Reachable from the SPA only in a race (BU deleted between option load and send) — the select offers live BUs |
| 8 | `system_all` destructive confirmation | The only mode with a red confirm button and the "This broadcast will reach every user in the system." warning | UX-only friction — the endpoint behind it is identical |
| 9 | Duplicate sends | No unique constraint, no idempotency key — double-confirming two composes creates two rows, each delivered | The Send button disables while in flight, so a single click cannot double-post |
| 10 | `.send`-less session posts directly | **Confirmed fixed since the last sync.** `PlatformPermissionGuard` now rejects with 403 (`Missing platform permission: broadcast.send`) before the request reaches micro-notification; the fixed `parseApiError` surfaces that exact message in the SPA rather than a swallowed/garbled one | Previously this succeeded (client-side-only enforcement); don't re-file the old finding — verify the 403 and correct message instead |
| 11 | Cluster-scoped grant sends a `system_all` broadcast | `PlatformPermissionGuard`/`PlatformPermissionService.has()` passes on **any** cluster grant, not just a platform-wide one — a user granted `broadcast.send` on a single cluster can still reach every user platform-wide via `system_all` or `system_users`, server-side | Deliberate, documented coarseness (per the code's own comments), not a bug to file — true per-cluster scoping needs `bu_code → cluster_id` resolution infra that doesn't exist yet |

## 5. Recommendations

- **QA the target × timing matrix end to end** — six cells (`system_all`/`system_users`/`bu` × immediate/scheduled). For each: confirm-dialog wording, the 201 response shape in the Debug Sheet, recipient visibility in the notification list, and live-socket arrival for an online recipient. Expect the two scheduled-broadcast cells to deliver passively (no socket) and the scheduled-targeted cell to misbehave per edge case 2.
- **Re-verify the security boundary, not the old finding.** Send the POST with a valid bearer from a session lacking `broadcast.send` and confirm it now fails with 403 and a correct error message (edge case 10) — the prior "it succeeds" finding is stale. Separately, confirm a cluster-scoped `broadcast.send` grant still reaches `system_all` server-side (edge case 11) — expected, not a defect.
- **Test edge case 1 explicitly** (recipients → switch to All users → confirm dialog vs actual payload); the Debug Sheet shows the response, and the request payload is visible in the network tab.
- **Read-state QA needs two users:** send a broadcast, confirm both see it unread (no `tb_user_broadcast_action` rows yet), have one mark it read, and confirm the other's unread state is untouched.
- **Treat `broadcast.read`, `end_at`, `dismissed_at`, and the schema-only `doc_version` columns as dormant** — seeded/declared but unused; don't file their absence from the UI as defects.

**References:** `../carmen-platform/src/App.tsx` (route guard) · `src/components/Layout.tsx` (sidebar) · `src/pages/BroadcastCompose.tsx` (`canSendSystem`/`canSend`, `<Can>`, payload builders, the in-code comments recording backend PR #239) · `src/utils/errorParser.ts` (the fixed nested-error-message parsing) · `src/utils/permissions.ts` (dev mock list — `broadcast.read`'s only SPA occurrence) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` (`KeycloakGuard` + `PlatformPermissionGuard`; still Swagger-only `x-app-id`) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-permission.guard.ts`, `src/auth/services/platform-permission.service.ts` (the coarse platform-or-any-cluster check) · `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.controller.ts` / `notification.service.ts` (delivery, scope queries, the uncalled `getScheduledNotifications`) · `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.ts` (the two keys).
**Cross-links:** [Broadcasts landing](/en/platform/broadcasts) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Platform RBAC — Permissions](../rbac/permissions.md) &nbsp;·&nbsp; [Business Units](/en/platform/business-units)
