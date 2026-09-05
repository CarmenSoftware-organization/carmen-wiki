---
title: Broadcasts
description: Broadcasts module overview — three screens (List, Compose, Edit) covering push notifications with three target modes, a mandatory expiry, and a full sender-side lifecycle (schedule, edit-while-scheduled, expire now, soft-delete) — except targeted sends, which stay fire-and-forget.
published: true
date: 2026-09-05T00:00:00.000Z
tags: platform/broadcasts, carmen-software
editor: markdown
dateCreated: 2026-06-10T13:15:00.000Z
---

# Broadcasts

The **Broadcasts** module pushes a notification to platform users: all of them, an explicit list, or every member of one business unit — delivered immediately or scheduled for a future time, with a **mandatory expiry**. It is the **push** counterpart to [News](/en/platform/news)'s **pull**: a broadcast lands in each recipient's notification list (and live over WebSocket when they are online and the send was unscheduled), while a news article waits in `tb_news` to be fetched.

**This module's shape changed substantially since it was last documented.** What was once a single compose-only screen with no list, edit, or lifecycle now has three distinct screens: a **List** (`/broadcasts` → `BroadcastManagement`) showing every system-wide and business-unit broadcast with search, status/scope filters, a status-summary strip, CSV export, an "Expire Now" shortcut, and soft-delete; a **Compose** (`/broadcasts/new` → `BroadcastCompose`) that sends a new one; and an **Edit** (`/broadcasts/:id/edit` → `BroadcastEdit`) that views one always and edits its schedule/expiry/content while it is still `scheduled`. **Compose and Edit are two different components, not one screen in two modes** — they have separate files, separate routes, and separate permission gates. One target mode is the exception to all of this: sending to **specific users** still fans out into personal `tb_notification` rows and is invisible to both the List and Edit screens — that one mode remains exactly as fire-and-forget as the whole module used to be.

> **At a Glance**
> **Module purpose:** List, compose, schedule, edit (while scheduled), expire, and soft-delete push notifications — three target modes (`system_all` / `system_users` / `bu`), a sender-only severity label, and a mandatory expiry (`end_at`) &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA, the backend-gateway notification module, and micro-notification &nbsp;·&nbsp; **Key entities/tables:** `tb_broadcast_notification` (scope/doc_type/event enums, `doc_version` now a real optimistic lock) + `tb_user_broadcast_action` (lazy read state); **targeted (`system_users`) sends fork into `tb_notification` instead and never appear on the List or Edit screens** &nbsp;·&nbsp; **Endpoints:** `POST /api/notifications/broadcasts/system` and `/bu` (send), `GET .../broadcasts` (admin list), `GET/PATCH/DELETE .../broadcasts/:id` — all under `/api`, **not** `/api-system` &nbsp;·&nbsp; **Permission keys:** `broadcast.read` (nav, list, Edit-page view) · `broadcast.send` (Compose route + Send) · `broadcast.update` (Edit action + PATCH) · `broadcast.delete` (Delete action + DELETE) — nav `feature: 'broadcasts'`, no `superAdminOnly` &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The sidebar entry ("Broadcasts", Megaphone icon, Content group) is defined in `platformNav.ts` with `permission: 'broadcast.read'` and `feature: 'broadcasts'` — no `superAdminOnly`. It opens the **List** screen, `BroadcastManagement`: a `PageHeader` (subtitle plus an explicit note that targeted sends don't appear here), a clickable status-summary strip (All / Active / Scheduled / Expired / Deleted counts, each toggling the matching filter), a search box, a Filters sheet (status, scope, "show deleted"), a server-side `DataTable` (Title+message, Scope, Severity, Status, Scheduled Date, Expires, Created), a CSV Export button, and a "New Broadcast" button gated on `broadcast.send`. Each row's action menu offers Edit (`broadcast.update`, hidden once deleted), Expire Now (`broadcast.update`, active rows only), and Delete (`broadcast.delete`, hidden once deleted).

**Compose** (`/broadcasts/new` → `BroadcastCompose`) is the send screen: a Target tab strip (All users / Specific users / Business Unit), a conditional recipient picker (`UserMultiSelect`) or BU select, an optional "Related Business Unit" metadata tag (independent of the actual audience), Title/Message with live counters, a Type preset (Info / Warning / Critical / Maintenance / Other…) that is **purely a sender-side label** — it is never shown to recipients — a Send-time tab strip (immediate or scheduled), and a required Expiry (7/30/90 days or a custom date). A shared `BroadcastPreview` card renders the notification, its reach, and its delivery/expiry timing live from the form state. Send always confirms first, with red styling reserved for the system-wide blast.

**Edit** (`/broadcasts/:id/edit` → `BroadcastEdit`) is a separate component reached from the List's title link or its row menu. The route itself only requires `broadcast.read` — any reader can open it in view mode; the Edit button (and everything it unlocks) requires `broadcast.update`. Scope/audience are fixed at send time and never editable here. Schedule and expiry are always editable; **title, message, and severity are editable only while the broadcast's current status is still `scheduled`** — once it has aired, the backend 400s any attempt to touch that content (`content_locked`), because recipients may already have read it. The same `BroadcastPreview` card reused from Compose shows the edit live.

Behind the SPA, the backend-gateway controller (`api/notifications/broadcasts/*`) forwards over RPC to **micro-notification**'s `BroadcastService` (create) and `BroadcastAdminService` (list/get/update/delete), which write `tb_broadcast_notification` and lazily populate `tb_user_broadcast_action` on read. See [Data Model](/en/platform/broadcasts/data-model).

## 2. Business Context

News and Broadcasts still split the announcement problem by urgency. A news article is **pulled** content: it sits behind the public feed until a client renders it. A broadcast **interrupts**: it can appear in every in-scope user's notification bell — and live over WebSocket for an online user — the moment it is sent. What is no longer true is that a broadcast "cannot be edited or recalled": a sender can now edit a still-`scheduled` broadcast's content, retime its schedule or expiry at any point, expire an active one immediately from the list, or soft-delete it outright. Only the *content* is locked once it has aired — the audience and the fact that it aired cannot be undone. The canonical use cases are unchanged: scheduled-maintenance warnings, incident notices, and per-property announcements to one business unit.

Scheduling still lets an operator stage a notice ahead of time: a scheduled broadcast row is created immediately but stays out of recipients' lists until `scheduled_at` passes (read-time filtering, same as before). One thing has changed for the better on the **targeted** path only: a scheduled send to specific users used to sit undelivered forever with no live push; a new 30-second background worker now claims due, unpushed personal notifications and pushes them live once their time arrives. **System-wide and business-unit broadcasts get no equivalent** — once scheduled, they only ever surface passively, on the recipient's next fetch. Details in [Permissions](/en/platform/broadcasts/permissions) §3–§4.

## 3. Key Concepts

- **Target modes** — unchanged: `BroadcastTargetMode = 'system_all' | 'system_users' | 'bu'`. The first two share `POST .../broadcasts/system` (an explicit `userIds` array turns "everyone" into "these users"); `bu` posts to `.../broadcasts/bu` with a `bu_code`, resolved server-side to `tb_business_unit.id`.
- **Severity is a sender-only label, not a recipient-facing type.** The old `SYS_*`/`BU_*` prefixed `type` column is **gone** — `tb_broadcast_notification` has no `type` or `category` column at all anymore. What the sender picks (Info/Warning/Critical/Maintenance/Other…) is stored as a plain string in `metadata.severity` for the admin UI's own badges; every broadcast's real `event` column is hardcoded to `info` and `doc_type` mirrors its scope (`system` or `business_unit`). The compose UI says so directly: "Colour and label are an internal categorisation — recipients see a standard notification."
- **Expiry (`end_at`) is now mandatory**, not a dead column. The Compose screen defaults to a 30-day preset (7/30/90 days, or a custom date), based on the *scheduled* send time when scheduling, otherwise now. `end_at` is what the backend uses to derive a broadcast's `status`.
- **`status` is computed, never stored.** `active` / `scheduled` / `expired` / `deleted` are derived server-side from `deleted_at`, `scheduled_at`, and `end_at` on every read — there is no status column.
- **`doc_version` is a real optimistic lock now**, not schema-only decoration. Both the update and delete admin endpoints require it and reject a stale value with 409.
- **Content lock** — title, message, and metadata are editable only while the row's current status is `scheduled`. Rescheduling an already-aired broadcast back into the future re-opens content editing (an intentional two-step "withdraw", not a loophole).
- **One row, lazy read state** — a `system_all` or `bu` broadcast is still a single `tb_broadcast_notification` row; who has read it lives in `tb_user_broadcast_action`, created lazily on first action.
- **Targeted sends still fork away entirely.** A `system_users` send with `userIds` never touches `tb_broadcast_notification` — it fans out into one `tb_notification` row per existing recipient id, exactly like before. This is also the one target mode the List/Edit screens cannot see, manage, or soft-delete after the fact.
- **Delete now works.** `DELETE /api/notifications/broadcasts/:id` soft-deletes a `system_all`/`bu` broadcast (`deleted_at`/`deleted_by_id`), superseding the prior "no code path ever writes `deleted_at`" finding.

## 4. Roles and Personas

Four permission keys now gate the module, through [Platform RBAC](/en/platform/rbac), seeded per role in `seed.platform-role-permission.data.ts`:

| Surface | Gate | Key |
|---|---|---|
| `/broadcasts` route + nav entry | `PrivateRoute` / nav filter | `broadcast.read` |
| `/broadcasts/:id/edit` route (view mode) | `PrivateRoute` | `broadcast.read` |
| `/broadcasts/new` route | `PrivateRoute` | `broadcast.send` |
| Send button (Compose) | `<Can>` | `broadcast.send` |
| Edit button (List row + Edit page) | `<Can>` | `broadcast.update` |
| Expire Now (List row) | `<Can>` | `broadcast.update` |
| Delete (List row) | `<Can>` | `broadcast.delete` |
| `GET/PATCH/DELETE .../broadcasts*` | `KeycloakGuard` + `PlatformPermissionGuard` | matching key, server-side |

| Role | Keys granted |
|---|---|
| Platform Admin | `broadcast.*` (all four) |
| Support Manager | `read`, `send`, `update` — **not** `delete` |
| Support Staff | `read` only |
| Security Officer | none |

`broadcast.read` is **no longer an orphan key** — it now gates the List route, the nav entry, and the Edit page's view mode. Every server-side route enforces the matching key via `PlatformPermissionGuard`, coarsely: a platform-wide grant **or** a grant in any single cluster passes, matching the SPA's own unscoped checks; true per-cluster scoping remains an explicitly deferred gap. The full matrix, the content-lock rule, and the per-mode delivery/scheduling semantics are in [Permissions](/en/platform/broadcasts/permissions).

## 5. Related Modules

- [News](/en/platform/news) — the pull-side sibling: authored content with a lifecycle and a public feed, versus Broadcasts' push.
- [Business Units](/en/platform/business-units) — BU mode targets one unit by `code`; the Compose screen loads its select options from that module's API (active BUs only, capped at 100).
- [Users](/en/platform/users) — *specific users* mode searches the user registry through `UserMultiSelect`; recipients are sent as `tb_user.id` UUIDs.
- [Platform RBAC](/en/platform/rbac) — defines and resolves the four `broadcast.*` keys gating the SPA and API surfaces.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — the three route guards (`broadcast.read`, `broadcast.send`, `broadcast.read`) and `feature="broadcasts"`.
- `../carmen-platform/src/components/nav/platformNav.ts` — the "Broadcasts" nav entry (`permission: 'broadcast.read'`, `feature: 'broadcasts'`, no `superAdminOnly`).
- `../carmen-platform/src/pages/BroadcastManagement.tsx`, `src/pages/broadcastManagement/{BroadcastSummary,BroadcastFilters,broadcastColumns}.tsx` — the List screen.
- `../carmen-platform/src/pages/BroadcastCompose.tsx` — the Compose screen: tabs, validation, payload builders, expiry presets, confirm dialog, shortcuts.
- `../carmen-platform/src/pages/BroadcastEdit.tsx` — the Edit screen: content lock, schedule/expiry editing, past/reschedule confirmations.
- `../carmen-platform/src/components/BroadcastPreview.tsx` — the live preview shared by Compose and Edit (`severityStyle`, `reachSummary`).
- `../carmen-platform/src/utils/broadcastExpiry.ts` — `resolveExpiryIso()`, the 7/30/90-day presets.
- `../carmen-platform/src/services/broadcastService.ts` — `sendSystem`/`sendBu`/`getAll`/`getById`/`update`/`remove`; `src/types/index.ts` — `BroadcastTargetMode`, `BroadcastTypePreset`, `BroadcastListItem`, `BroadcastStatus`, `BroadcastUpdatePayload`, `BroadcastSummary`.
- `../carmen-platform/src/utils/permissions.ts` — the `PERMISSIONS.BROADCAST.SEND` constant.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification` (line 332), `tb_broadcast_notification` (line 369), `tb_user_broadcast_action` (line 403); enums `enum_broadcast_scope`, `enum_notification_doc_type`, `enum_notification_event` (lines 112–131).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260810000000_notification_redesign_additive/`, `20260811000000_notification_redesign_drop_legacy/` — the redesign that dropped `type`/`category`/`is_sent` and added `scope`/`doc_type`/`event`/`pushed_at`.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` — all six broadcast routes and their guards.
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/broadcast.service.ts` (create path), `broadcast-admin.service.ts` (list/get/update/delete, status derivation), `schedule.worker.ts` (the 30-second due-notification push worker, `tb_notification` only).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.platform-permission.data.ts`, `seed.platform-role-permission.data.ts` — the four `broadcast.*` keys and their per-role assignment.

## 7. Pages in This Module

- [Data Model](/en/platform/broadcasts/data-model) — the `tb_broadcast_notification` and `tb_user_broadcast_action` field tables, the enum rework, the targeted-send fork into `tb_notification`, and divergences against the SPA's types.
- [UI Screens](/en/platform/broadcasts/ui-screens) — all three screens: the List (columns, filters, summary, CSV export), Compose (target tabs, expiry presets, live preview), and Edit (content lock, schedule/expiry editing).
- [Permissions](/en/platform/broadcasts/permissions) — the four-key gate matrix, per-mode delivery/scheduling semantics, the content-lock and optimistic-lock rules, and the edge-case matrix for testers.
