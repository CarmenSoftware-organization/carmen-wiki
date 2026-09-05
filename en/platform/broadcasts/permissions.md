---
title: Broadcasts — Permissions
description: Four broadcast.* keys (read/send/update/delete) gate the module's List/Compose/Edit screens and their matching REST endpoints server-side; content locks once a broadcast has aired, doc_version is a real optimistic lock, and only targeted (system_users) sends stay fire-and-forget.
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, broadcasts, permissions
editor: markdown
dateCreated: 2026-06-10T13:15:00.000Z
---

# Broadcasts — Permissions

> **At a Glance**
> **Four keys, not one:** `broadcast.read` (List + Edit-page view), `broadcast.send` (Compose + Send), `broadcast.update` (Edit action + Expire Now + `PATCH`), `broadcast.delete` (Delete + `DELETE`) &nbsp;·&nbsp; **All four enforced server-side** via `PlatformPermissionGuard`, on every one of the six broadcast routes &nbsp;·&nbsp; **Known coarseness (unchanged since the last sync):** the guard passes on a platform-wide grant **or** a grant in any single cluster — true per-cluster scoping is still explicitly deferred &nbsp;·&nbsp; **Content lock:** title/message/metadata are editable only while a broadcast is still `scheduled`; a 400 `content_locked` otherwise &nbsp;·&nbsp; **`doc_version` is a real optimistic lock**, checked by both `PATCH` and `DELETE` &nbsp;·&nbsp; **Targeted (`system_users`) sends stay fire-and-forget** — invisible to `broadcast.read`/`.update`/`.delete` entirely, since they never touch `tb_broadcast_notification`

## 1. Overview

Broadcasts moved from a single-key gate story to a full four-key one, mirroring its move from a one-shot send screen to a List/Compose/Edit trio. All four keys are registered in the platform permission catalog (`seed.platform-permission.data.ts`) with real descriptions — `broadcast.read` is **no longer an orphan**: it now gates the List route, the nav entry, and the Edit page's view mode, closing the pre-redesign finding that it "gates nothing in the SPA."

Every key is enforced **both** client-side (`<Can>`, `PrivateRoute`) and server-side (`KeycloakGuard` + `PlatformPermissionGuard` + `@RequirePlatformPermission(...)`) on all six gateway routes: the two send endpoints (unchanged coarse enforcement since backend PR #239) plus the four admin endpoints (list/get/update/delete) added in the same redesign that built the List/Edit screens. The enforcement is deliberately **coarse** everywhere, not just on send: `PlatformPermissionService.has()` returns true if the required key is present in the caller's **platform-wide** scope **or** in **any single cluster's** scope — a user granted, say, `broadcast.delete` on exactly one cluster can delete *any* broadcast row through this API, system-wide or BU-scoped, because there is no code path anywhere in this module that resolves "which cluster does this specific broadcast belong to" and checks the grant against it. This is the same limitation the pre-redesign wiki documented for `broadcast.send` alone; it now applies identically to all four keys.

## 2. Gate matrix

| Surface | Mechanism | Key | Source |
|---|---|---|---|
| `/broadcasts` route + nav entry | `PrivateRoute` / nav filter | `broadcast.read` | `src/App.tsx`, `src/components/nav/platformNav.ts` |
| `/broadcasts/:id/edit` route (opens in view mode) | `PrivateRoute` | `broadcast.read` | `src/App.tsx` |
| `/broadcasts/new` route | `PrivateRoute requiredPermission` | `broadcast.send` | `src/App.tsx` |
| "New Broadcast" (List header + empty state) | `<Can>` | `broadcast.send` | `BroadcastManagement.tsx` |
| Send button (Compose) | `<Can>` | `broadcast.send` | `BroadcastCompose.tsx` |
| "All users" + "Specific users" audience tabs | in-component `hasPermission('broadcast.send')` | `broadcast.send` | `BroadcastCompose.tsx` — unreachable defensive code, since reaching the page at all already requires the same key |
| Edit button (List row + Edit page) | `<Can>` | `broadcast.update` | `broadcastColumns.tsx`, `BroadcastEdit.tsx` |
| Expire Now (List row) | `<Can>` | `broadcast.update` | `broadcastColumns.tsx` |
| Delete (List row) | `<Can>` | `broadcast.delete` | `broadcastColumns.tsx` |
| `POST /api/notifications/broadcasts/system` / `/bu` | `KeycloakGuard` + `PlatformPermissionGuard` | `broadcast.send` (coarse) | `notification.controller.ts` |
| `GET /api/notifications/broadcasts` (list) | same guards | `broadcast.read` (coarse) | `notification.controller.ts` |
| `GET /api/notifications/broadcasts/:id` | same guards | `broadcast.read` (coarse) | `notification.controller.ts` |
| `PATCH /api/notifications/broadcasts/:id` | same guards | `broadcast.update` (coarse) | `notification.controller.ts` |
| `DELETE /api/notifications/broadcasts/:id` | same guards | `broadcast.delete` (coarse) | `notification.controller.ts` |

### Role assignment (from `seed.platform-role-permission.data.ts`)

| Role | Keys |
|---|---|
| Platform Admin | `broadcast.*` — all four |
| Support Manager | `read`, `send`, `update` — **not** `delete` |
| Support Staff | `read` only |
| Security Officer | none |

Tester-relevant readings:

- **The in-component audience-tab gate on Compose is redundant, not decorative-only-in-theory** — a session without `broadcast.send` never reaches `/broadcasts/new` at all (the route guard blocks it first), so the tab-hiding logic inside `BroadcastCompose` is unreachable in practice. It only matters if the route guard's key ever diverges from the component's own check.
- **`broadcast.read` alone is enough to browse and open every `system_all`/`bu` broadcast, including its content, in view mode** — it is not a "can see the list exists" key, it is "can see everything the list and Edit screen show." Only mutating actions require the other three keys.
- **Support Manager can edit and expire broadcasts but never delete one** — a real, intentional asymmetry worth testing explicitly (Edit/Expire Now visible, Delete absent, from that role).

## 3. Per-mode delivery, scheduling, and push semantics

Delivery/visibility is unchanged in its read-time-filtering shape, but **live-push behaviour now diverges by target mode** in a way it did not before:

| Mode | Storage | Audience (read path) | Live push when unscheduled | Live push once a schedule becomes due |
|---|---|---|---|---|
| `system_all` | `tb_broadcast_notification`, `scope = 'system'` | every user | socket emit to every active, non-deleted user id | **never** — no worker watches this table |
| `system_users` | `tb_notification`, one row **per existing recipient id** | exactly those users | socket emit per row | **now delivered** — a 30-second `ScheduleWorker` cron claims due, unpushed `tb_notification` rows and pushes them live, stamping `pushed_at` |
| `bu` | `tb_broadcast_notification`, `scope = 'business_unit'` | users whose live `tb_user_tb_business_unit` membership matches the scope BU | socket emit to current BU member ids | **never** — same as `system_all` |

This is a genuine, mode-specific fix and a mode-specific gap, both worth calling out explicitly to testers:

1. **Targeted scheduling now works as a tester would expect.** The pre-redesign wiki documented `getScheduledNotifications()` as dead code with no caller — that function and the gap it represented no longer exist. `ScheduleWorker.releaseDueNotifications()` replaces it: every 30 seconds it claims rows where `scheduled_at <= NOW()`, `pushed_at IS NULL`, and `scheduled_at` is no more than 7 days old (a cold-start guard), under `FOR UPDATE SKIP LOCKED`, emits each live, then stamps `pushed_at`.
2. **`system_all`/`bu` broadcasts still get no equivalent.** The worker's query only ever touches `tb_notification` — a scheduled system-wide or BU broadcast still only becomes visible passively, on the recipient's next REST fetch, exactly as before the redesign (just for a narrower reason now: not "no worker exists" but "the worker that exists doesn't look at this table").
3. **Membership is still evaluated per query, not per send** for `system_all`/`bu` — a user added to a BU after a broadcast was sent still sees it; one removed stops seeing it. There is no recipient snapshot.
4. **Read state is still lazy and per-user** (`tb_user_broadcast_action`).

The pre-redesign wiki's "email fan-out side-effect (when SMTP is enabled)" claim **no longer applies — this behaviour has been removed.** `NotificationWriteService.notify()`, `BroadcastService.create()`, and `NotificationGateway` were all read in full for this task; none of them call `EmailService`/`PlatformEmailService`. Those email services still exist in micro-notification, but strictly for the unrelated platform-email and app-config test-send features — nothing in the broadcast/notification create path invokes them anymore.

## 4. Content lock and optimistic locking

- **Content lock**: `title`/`message`/`metadata` on a `PATCH` are accepted only while the target row's *current* derived status is `scheduled`. Touching any of them once a broadcast has aired returns **400 `content_locked`** — recipients may already have read it. Rescheduling it back into the future first (a "withdraw") legitimately re-opens content editing; that is an intended two-step, not a bypass.
- **`doc_version` is a real optimistic lock**, not schema-only decoration: both `PATCH` and `DELETE` require it and compare it against the stored row before writing (`updateMany` with `doc_version` in the `where` clause, so two concurrent requests holding the same version can never both "win" — the second gets 409, not a silent double-increment). This corrects the pre-redesign finding that `doc_version` on this table was schema-only with "no update endpoint... to lock in the first place."
- Setting `end_at` to the past is a legitimate way to expire a live broadcast immediately (that is exactly what the List screen's "Expire Now" action does under the hood) — the backend allows it explicitly, unlike a would-be future-only expiry check.

## 5. Edge Cases

| # | Scenario | Behaviour | Tester notes |
|---|---|---|---|
| 1 | Stale recipients leak into "All users" | Picking recipients under *Specific users* and then switching to *All users* does **not** clear them; `buildSystemPayload` includes `userIds` whenever recipients exist, so the send silently becomes targeted — while the confirm dialog claims "Send to ALL users?" | Re-verified against current `BroadcastCompose.tsx` — unchanged from the pre-redesign behaviour. Reset (or removing the badges) clears them |
| 2 | Scheduled *Specific users* send | **Now delivers a live push once due.** `ScheduleWorker` claims the row from `tb_notification` and emits it, then stamps `pushed_at` | This reverses the pre-redesign finding ("the deferred live emit never happens — no such worker exists"). Verify the push arrives within ~30 seconds of the scheduled time for an online recipient |
| 3 | Scheduled `system_all`/`bu` send | Still no live push ever, even once due — only read-time visibility on the recipient's next fetch | Unlike edge case 2, this one is **unchanged** — confirm testers don't conflate the two target-mode families |
| 4 | Viewing, editing, or deleting a `system_all`/`bu` broadcast after it was sent | **Now fully possible** — the List and Edit screens exist precisely for this. Edit while `scheduled`; Expire Now while `active`; Delete (soft) at any status except already-deleted | Supersedes the pre-redesign "no way to see or cancel a sent/scheduled broadcast" finding entirely — do not re-file that as a gap |
| 5 | Viewing or managing a *specific-users* send after it was sent | **Still impossible** — it lives in `tb_notification`, which neither the List nor the Edit screen ever queries | The one mode where the old "fire-and-forget, no code path" story still applies in full |
| 6 | Editing content after a broadcast has aired | 400 `content_locked` server-side; the Edit screen's Content card renders read-only (with an explicit warning) whenever status isn't `scheduled`, so the UI cannot normally trigger this | Reachable only via a direct API call, or a race where the broadcast airs between page load and Save |
| 7 | Concurrent edits to the same broadcast | Second `PATCH`/`DELETE` with a stale `doc_version` gets 409; the SPA shows the shared version-conflict toast and silently refetches | Confirm the refetched row reflects the winner's changes, not the loser's |
| 8 | Custom severity rejected | Other… requires `[A-Z0-9_]+`, ≤50 chars, auto-uppercased as typed — client-side validation only, since severity is never a recipient-facing field | Server accepts any string inside `metadata`; the regex is SPA-only decoration on a field that is itself decoration |
| 9 | BU list fails to load / has >100 BUs | Load failure shows the parsed error with inline Retry; the fetch caps at `perpage: 100` — affects both the audience BU select and the "Related Business Unit" metadata select on Compose | The cap is invisible in the UI — on large clusters verify the target BU appears before filing "missing BU" defects |
| 10 | BU code unknown or soft-deleted at send time | Resolves against live BUs; failure now surfaces as a **404** (`COMMON_BUSINESS_UNIT_NOT_FOUND`) | Corrects the pre-redesign "500-enveloped" description — re-verify the status code, not just the message, if writing a regression test |
| 11 | `system_all` destructive confirmation | The only mode with a red confirm button and a "reach every user" warning | Unchanged |
| 12 | Duplicate sends | No unique constraint, no idempotency key — double-confirming two composes creates two rows. The Send button still disables while a request is in flight, so a single click cannot double-post | Unchanged from before, but a duplicate can now be cleaned up afterward via Delete on the List screen, which was not possible pre-redesign |
| 13 | `.send`/`.read`/`.update`/`.delete`-less session calls the matching endpoint directly | `PlatformPermissionGuard` rejects with 403 before the request reaches micro-notification, for **all six** routes now, not just the two send endpoints | Verify each of the four keys independently — this task extended coverage well beyond the send-only enforcement the last sync verified |
| 14 | Cluster-scoped grant reaches every cluster's broadcasts | Any single-cluster grant of a `broadcast.*` key passes the guard for **every** row, system-wide or any other BU's — not just that grantee's own cluster | Deliberate, documented coarseness (§1), not a bug to file — applies identically to read/send/update/delete now |
| 15 | Deleted broadcast reopened from the list | `GET .../broadcasts/:id` still returns it (`status: "deleted"`), so it stays viewable read-only; Edit button is hidden, content is naturally locked | Confirm a deleted row cannot be un-deleted from the UI — there is no restore action anywhere in this module |

## 6. Recommendations

- **QA all four keys independently**, not just `broadcast.send` as before — a session with only `read` should see everything but be unable to act; a `read`+`update` session (no `send`, no `delete`) should be able to edit/expire but never send or delete; confirm the matrix in §2 holds for each combination.
- **Re-verify the target-mode push split (edge cases 2–3) explicitly** — it is easy to conflate "scheduling now works" with "scheduling now works for every mode." It does not: only targeted (`system_users`) sends get the new worker-driven push.
- **Test the content-lock boundary directly**: edit a `scheduled` broadcast's title (should succeed), let it age into `active` (or send one immediately), then attempt the same edit (should 400 `content_locked` server-side and render read-only client-side).
- **Test the optimistic lock**: open the same broadcast in two sessions, save from one, then attempt to save from the other — expect 409 and a version-conflict toast, not a silent overwrite.
- **Test edge case 1 explicitly** (recipients → switch to All users → confirm dialog vs. actual payload) — unchanged from the pre-redesign finding and still worth a bug report against the SPA if it has not already been filed.
- **Confirm `system_users` sends genuinely never appear** on the List or Edit screens after sending, even for a Platform Admin — this is intentional, not a filter to work around.

**References:** `../carmen-platform/src/App.tsx` (route guards) · `src/components/nav/platformNav.ts` (nav entry) · `src/pages/BroadcastManagement.tsx`, `src/pages/broadcastManagement/broadcastColumns.tsx` (row-action gates) · `src/pages/BroadcastCompose.tsx` (`canSendSystem`/`canSend`, `<Can>`) · `src/pages/BroadcastEdit.tsx` (`contentEditable`, `<Can permission="broadcast.update">`) · `src/utils/permissions.ts` (`PERMISSIONS.BROADCAST.SEND`) · `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` (all six guarded routes) · `apps/backend-gateway/src/auth/guards/platform-permission.guard.ts`, `src/auth/services/platform-permission.service.ts` (the coarse platform-or-any-cluster check, unchanged since PR from 2026-06-10) · `apps/micro-notification/src/notification/broadcast-admin.service.ts` (`content_locked`/`conflict` rules) · `apps/micro-notification/src/notification/schedule.worker.ts` (the targeted-only push worker) · `packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts`, `seed.platform-role-permission.data.ts` (the four keys and their role assignment) · `packages/error-catalog/src/catalog.ts` (`COMMON_BUSINESS_UNIT_NOT_FOUND`, 404).

**Cross-links:** [Broadcasts landing](/en/platform/broadcasts) &nbsp;·&nbsp; [Data Model](/en/platform/broadcasts/data-model) &nbsp;·&nbsp; [UI Screens](/en/platform/broadcasts/ui-screens) &nbsp;·&nbsp; [Platform RBAC — Permissions](/en/platform/rbac/permissions) &nbsp;·&nbsp; [Business Units](/en/platform/business-units)
