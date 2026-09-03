---
title: Broadcasts
description: Broadcasts module overview — a single push-notification compose screen (with a live preview panel) with three target modes (all users, specific users, one business unit), SYS_/BU_ type presets, and immediate or scheduled delivery, now enforced server-side.
published: true
date: 2026-07-29T00:00:00.000Z
tags: platform/broadcasts, carmen-software
editor: markdown
dateCreated: 2026-06-10T13:15:00.000Z
---

# Broadcasts

The **Broadcasts** module pushes a notification to platform users: all of them, an explicit list, or every member of one business unit — delivered immediately or scheduled for a future time. It is the **push** counterpart to [News](/en/platform/news)'s **pull**: a broadcast lands in each recipient's notification list (and live over WebSocket when they are online), while a news article waits in `tb_news` to be fetched. The SPA side is a **single compose screen** (`/broadcasts/new`) with no list, edit, or cancel routes — once sent, a broadcast is fire-and-forget from this product.

> **At a Glance**
> **Module purpose:** Compose and send push notifications — three target modes (`system_all` / `system_users` / `bu`), type presets resolved to `SYS_*`/`BU_*`, immediate or scheduled (`datetime-local`, must be future) &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA, the backend-gateway notification module, and micro-notification &nbsp;·&nbsp; **Key entities/tables:** `tb_broadcast_notification` + `tb_user_broadcast_action` (lazy read state); targeted sends fan out into `tb_notification` instead &nbsp;·&nbsp; **Endpoints:** `POST /api/notifications/broadcasts/system` and `/bu` — note `/api`, **not** `/api-system` &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

Broadcasts is the only Platform module whose SPA surface is a **single screen**: `/broadcasts/new` → `BroadcastCompose`, a Compose card beside a sticky **Preview** card. There is no `/broadcasts` list route, no edit route, no detail view — a deliberate deviation from the SPA's standard two-screen Management/Edit pattern, because the module's job is a one-shot action, not record management. The page carries the standard furniture anyway: a `PageHeader` (Megaphone icon, no back link — the page is reached only from the sidebar), the `useUnsavedChanges` guard, global keyboard shortcuts (Ctrl/Cmd+S send, Escape reset), toast feedback, and the dev-only Debug Sheet showing the last API response, plus a sticky bottom action bar (Reset/Send) with an "Unsaved changes" indicator.

The Compose card, top to bottom: a **Target** tab strip (All users / Specific users / Business Unit), a conditional recipient picker (`UserMultiSelect`) or BU select, **Title** (≤200 chars, live counter) and **Message** (≤2000 chars, live counter), a **Type** preset select (Info / Warning / Critical / Maintenance / Other…), and a **Send time** tab strip (Send immediately / Schedule for later with a `datetime-local` input). Beside it, a `BroadcastPreview` card renders the notification as recipients will see it (type badge, title, message), a "Reaches" line (audience summary, with a warning tint for the system-wide blast), and a "Delivery" line (immediate vs. the formatted scheduled time) — all recomputed live from the form state. Send always passes through a confirmation dialog whose title and styling vary by target mode. See [UI Screens](/en/platform/broadcasts/ui-screens) for the full walkthrough.

Behind the SPA, the backend-gateway controller (`api/notifications/broadcasts/*`) forwards over TCP (`notifications.create`) to **micro-notification**, which writes the rows and live-pushes over Socket.io to online in-scope users. Storage is a single `tb_broadcast_notification` row per send with lazy per-user read state in `tb_user_broadcast_action` — except the *specific users* mode, which fans out one `tb_notification` row per recipient instead. See [Data Model](/en/platform/broadcasts/data-model).

## 2. Business Context

News and Broadcasts split the announcement problem by urgency. A news article is **pulled** content: it sits behind the public feed until a client renders it, suits policy documents and long-form updates, and can be edited or archived after the fact. A broadcast **interrupts**: it appears in every in-scope user's notification bell (and as a live socket event for online users) the moment it is sent — and it cannot be edited or recalled afterwards. The canonical use cases are operational: scheduled-maintenance warnings (`SYS_MAINTENANCE`), incident notices (`SYS_CRITICAL`), and per-property announcements to one business unit's staff (`BU_INFO`).

Scheduling lets an operator stage the maintenance notice ahead of time: a scheduled broadcast row is created immediately but stays out of recipients' lists until `scheduled_at` passes (read-time filtering — no delivery cron is involved for broadcast rows). Two caveats QA should know up front: the email fan-out side-effect (when SMTP is enabled on micro-notification) fires at **create** time even for scheduled sends, and the *specific users* mode does not honor scheduling at all on the read path — details in [Permissions](/en/platform/broadcasts/permissions) §3–§4.

## 3. Key Concepts

- **Target modes** — `BroadcastTargetMode = 'system_all' | 'system_users' | 'bu'`. The first two share `POST .../broadcasts/system` (an explicit `userIds` array turns "everyone" into "these users"); `bu` posts to `.../broadcasts/bu` with a `bu_code` — the human-readable BU **code**, not the UUID; micro-notification resolves it to `tb_business_unit.id` and stores that as `scope_id`.
- **Type resolution** — the SPA resolves the preset client-side: `SYS_<PRESET>` for the two system modes, `BU_<PRESET>` for BU mode (e.g. Maintenance → `SYS_MAINTENANCE` or `BU_MAINTENANCE`). Choosing **Other…** reveals a custom-type input (`[A-Z0-9_]+`, ≤50 chars, auto-uppercased) sent verbatim with **no prefix**. If `type` is omitted entirely (API callers only — the SPA always sends it), the gateway defaults to `SYS_INFO`/`BU_INFO`.
- **One row, lazy read state** — a system-wide or BU broadcast is a single `tb_broadcast_notification` row; who has read it lives in `tb_user_broadcast_action`, created lazily on first action. This replaced an earlier fan-out-on-write design (the schema comment documents the migration). The *specific users* path still uses the legacy fan-out: one `tb_notification` row per recipient.
- **Scheduling = read-time visibility** — a broadcast with `scheduled_at` in the future exists immediately but is filtered out of every list query (`scheduled_at IS NULL OR scheduled_at <= NOW()`) until the time passes; the live socket push is skipped for scheduled sends and never happens later (recipients see it on their next list fetch).
- **Fire-and-forget** — no API anywhere (gateway or micro-notification) lists, updates, cancels, or deletes a broadcast. The read queries respect `deleted_at`, but no code path ever writes it — retracting a mis-sent or mis-scheduled broadcast is a manual database operation today.

## 4. Roles and Personas

One permission key gates every surface, through [Platform RBAC](/en/platform/rbac) (`broadcast.send`, seeded in `seed.platform-permission.ts` alongside an SPA-unused `broadcast.read`):

| Surface | Gate | Key |
|---|---|---|
| `/broadcasts/new` route | `PrivateRoute` | `broadcast.send` |
| Sidebar "Send Broadcast" (Content group, Megaphone icon) | `Layout.tsx` nav filter | `broadcast.send` |
| Send button (form footer) | `<Can>` | `broadcast.send` |
| `POST /api/notifications/broadcasts/system` / `/bu` | `KeycloakGuard` + `PlatformPermissionGuard` | `broadcast.send` |

Unlike the CRUD modules there is no read/create/update/delete split — sending is the module's only operation. **Confirmed fixed since the last sync:** the two gateway endpoints now enforce `broadcast.send` server-side too (backend PR #239, `PlatformPermissionGuard` + `@RequirePlatformPermission('broadcast.send')`) — previously the SPA's own gate was the only boundary. The enforcement is deliberately **coarse**: it passes on a platform-wide grant **or** a grant in any single cluster, matching (not exceeding) the SPA's own unscoped checks; true per-cluster scoping is a known, explicitly-deferred gap. The full matrix, the in-component tab gating quirk, and the target-mode delivery semantics are in [Permissions](/en/platform/broadcasts/permissions).

## 5. Related Modules

- [News](/en/platform/news) — the pull-side sibling: authored content with a lifecycle and a public feed, versus Broadcasts' immediate one-shot push. Use Broadcasts to interrupt, News to inform.
- [Business Units](/en/platform/business-units) — BU mode targets one unit by `code`; the compose screen loads its select options from that module's API (active BUs only), and micro-notification resolves the code against live `tb_business_unit` rows at send time.
- [Users](/en/platform/users) — *specific users* mode searches the user registry through `UserMultiSelect`; recipients are sent as `tb_user.id` UUIDs.
- [Platform RBAC](/en/platform/rbac) — defines and resolves the `broadcast.send` key gating the SPA surfaces.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — the `/broadcasts/new` route guard (`broadcast.send`).
- `../carmen-platform/src/components/Layout.tsx` — "Send Broadcast" sidebar entry (Content group).
- `../carmen-platform/src/pages/BroadcastCompose.tsx`, `src/pages/broadcastCompose/BroadcastPreview.tsx` — the compose screen: tabs, validation, payload builders, live preview, confirm dialog, shortcuts.
- `../carmen-platform/src/components/UserMultiSelect.tsx` — debounced user search with badge selection.
- `../carmen-platform/src/services/broadcastService.ts` — the two POST calls; `src/types/index.ts` — `BroadcastTargetMode`, `BroadcastTypePreset`, the two payload types, `UserOption`.
- `../carmen-platform/src/utils/permissions.ts` — the `PERMISSIONS.BROADCAST.SEND` constant.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification` (line 332), `tb_broadcast_notification` (line 374), `tb_user_broadcast_action` (line 406).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` — `pushSystemBroadcast` / `pushBuBroadcast` (`KeycloakGuard` + `PlatformPermissionGuard`, TCP forward).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/guards/platform-permission.guard.ts`, `src/auth/services/platform-permission.service.ts` — the coarse platform-wide-or-any-cluster server-side check (backend PR #239, commit `1fa15ec02`).
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/` — `notification.controller.ts` (create dispatch, live emit), `notification.service.ts` (row writes, scope resolution, read-time filters, email fan-out).

## 7. Pages in This Module

- [Data Model](/en/platform/broadcasts/data-model) — the `tb_broadcast_notification` and `tb_user_broadcast_action` field tables, the targeted-send fork into `tb_notification`, the type vocabulary, and divergences against the SPA payload types.
- [UI Screens](/en/platform/broadcasts/ui-screens) — the compose screen and its live preview panel: target tabs, recipient pickers, counters, send/schedule flow, confirmation dialog, and shortcuts.
- [Permissions](/en/platform/broadcasts/permissions) — the one-key gate matrix, the confirmed-fixed server-side enforcement (and its known coarseness), per-mode delivery semantics, and the edge-case matrix for testers.
