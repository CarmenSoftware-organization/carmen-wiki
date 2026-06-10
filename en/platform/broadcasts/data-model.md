---
title: Broadcasts — Data Model
description: The tb_broadcast_notification and tb_user_broadcast_action field tables, the targeted-send fork into tb_notification, scope_id resolution from bu_code, and divergences against the SPA's write-only payload types.
published: true
date: 2026-06-10T13:15:00.000Z
tags: book/platform, broadcasts, data-model
editor: markdown
dateCreated: 2026-06-10T13:15:00.000Z
---

# Broadcasts — Data Model

> **At a Glance**
> **Tables:** `tb_broadcast_notification` (one row per broadcast) + `tb_user_broadcast_action` (lazy per-user read state, unique per broadcast×user) &nbsp;·&nbsp; **Targeted fork:** `userIds` sends skip both tables and fan out into `tb_notification` (one personal row per recipient) &nbsp;·&nbsp; **Scope:** `scope_id` = `tb_business_unit.id` UUID for `bu-to-user`, null for `system-to-user` — the API accepts the BU **code** and resolves it &nbsp;·&nbsp; **No enums:** `category` and `type` are plain varchar &nbsp;·&nbsp; **Endpoints:** `POST /api/notifications/broadcasts/system` / `/bu` — `/api`, **not** `/api-system`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The module owns two tables. `tb_broadcast_notification` is the schema comment's "single source of truth for a broadcast": one row per message regardless of audience size, with the audience encoded as `category` (`'system-to-user'` or `'bu-to-user'`) plus `scope_id`. `tb_user_broadcast_action` holds per-user state — created **lazily**, only when a user acts (marks read); absence of a row means "not acted on yet", and the unread queries LEFT JOIN to surface broadcasts without a row. The schema comment records that this pair replaced an earlier fan-out-on-write pattern that inserted one `tb_notification` row per recipient.

That legacy pattern is still live on one path: a system send with an explicit `userIds` list bypasses both broadcast tables and fans out into `tb_notification` (§2.3) — micro-notification's code calls this "legacy behavior — small N, fanout is fine".

The persistence path is backend-gateway (`api/notifications/broadcasts/*`, KeycloakGuard) → TCP `notifications.create` → micro-notification, which owns all writes, the `bu_code → scope_id` resolution, the live Socket.io emit for unscheduled sends, and an email fan-out side-effect when SMTP is configured. There are no admin read/update/delete endpoints — the only readers are the recipient-side list/unread/mark-read endpoints documented in §6.

## 2. Entities

### 2.1 `tb_broadcast_notification`

One broadcast message. Schema line 357.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `category` | `String @db.VarChar(50)` | No | `'system-to-user'` (whole platform) or `'bu-to-user'` (one BU) — plain varchar, no enum |
| `scope_id` | `String? @db.Uuid` | Yes | `tb_business_unit.id` when `category = 'bu-to-user'`; `null` for `'system-to-user'`. Resolved server-side from the payload's `bu_code` (live BUs only) — the row stores the stable UUID, not the renameable code |
| `type` | `String @default("SYS_INFO") @db.VarChar(255)` | No | Type label — `SYS_*`/`BU_*` presets or a custom uppercase token (§4) |
| `title` | `String?` | Yes | Notification title (the SPA requires it; the column does not) |
| `message` | `String?` | Yes | Notification body (same — required by the SPA only) |
| `metadata` | `Json? @db.JsonB` | Yes | Free-form. The SPA never sends it; BU sends get `bu_code` merged in server-side |
| `scheduled_at` | `DateTime?` | Yes | Visibility cutoff: list queries hide the row until `scheduled_at <= NOW()`. No timezone annotation (unlike the audit columns) |
| `end_at` | `DateTime?` | Yes | **Declared but dead** — never written or read by any code path as of 2026-06-10 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation, default `now()`; also the list sort key |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit/sender: FK → `tb_user`. Set to the token user for **BU** sends; **left `null` for system sends** (§5) |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: default `now()`; never updated (no update path exists) |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: FK → `tb_user`; never written |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft delete — **respected by every read query but written by no code path**; retraction is a manual DB operation |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: bare UUID; never written |

**Constraints:**
- `@id` on `id`. FK relations: `created_by_id` and `updated_by_id` → `tb_user.id` (`onDelete: NoAction, onUpdate: NoAction`). No unique constraints — nothing stops identical duplicate sends.

**Indexes:**
- `@@index([category, scope_id, created_at(sort: Desc)])` — drives the scoped list queries (system rows for everyone, BU rows matched against the user's BU memberships, newest first).
- `@@index([deleted_at])`.

### 2.2 `tb_user_broadcast_action`

Lazy per-user state for one broadcast. Schema line 388.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `broadcast_id` | `String @db.Uuid` | No | FK → `tb_broadcast_notification.id`, **`onDelete: Cascade`** |
| `user_id` | `String @db.Uuid` | No | FK → `tb_user.id`, **`onDelete: Cascade`** |
| `is_read` | `Boolean? @default(false)` | Yes | Read flag; the unread queries treat a missing row and `is_read = false` identically (`COALESCE(a.is_read, false)`) |
| `read_at` | `DateTime?` | Yes | Stamped by the mark-as-read upsert |
| `dismissed_at` | `DateTime?` | Yes | **Declared but dead** — the schema comment anticipates a dismiss action, but no code writes it as of 2026-06-10 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Default `now()` |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Default `now()`; touched by the mark-read upsert |

**Constraints:**
- `@id` on `id`; `@@unique([broadcast_id, user_id])` (map `user_broadcast_action_broadcast_user_u`) — one state row per user per broadcast; the mark-read path upserts against this key. No audit actor or soft-delete columns.

**Indexes:**
- `@@index([user_id, is_read])` — the unread lookup.

Rows are written by exactly two paths in micro-notification: single mark-as-read (Prisma upsert) and mark-all-as-read (one raw SQL `INSERT … ON CONFLICT … DO UPDATE` covering every in-scope unread broadcast).

### 2.3 `tb_notification` (referenced)

The personal-notification table (schema line 316; `to_user_id`/`from_user_id` FKs, `type` default `SYS_INFO`, `category` default `'system'`, `is_read`/`is_sent` flags, own `scheduled_at`, full audit columns). Broadcasts touches it on one path only: a system send carrying `userIds` creates one row **per existing recipient id** (`category = 'system'`, `from_user_id = null`), then live-emits and stamps `is_sent = true` when unscheduled. Ids that match no `tb_user` row are silently dropped — no error, no partial-failure report. The table's broader lifecycle (user-to-user messages, workflow notifications) belongs to the notification feature generally, not to this module.

## 3. Relationships

- `tb_broadcast_notification` 1:M `tb_user_broadcast_action` — `broadcast_id`, `onDelete: Cascade` (deleting a broadcast hard-deletes its read-state rows).
- `tb_user` 1:M `tb_user_broadcast_action` — `user_id`, `onDelete: Cascade` (deleting a user removes their read state).
- `tb_user` 1:M `tb_broadcast_notification` via `created_by_id` / `updated_by_id` (`NoAction` — audit references).
- **`scope_id` → `tb_business_unit.id` is convention, not a Prisma relation.** Validated only at send time (the `bu_code` must match a live BU or the send fails); a BU deleted later leaves the broadcast row pointing at a dead scope — its members simply stop matching the scope query.

## 4. Enums

None — `category` and `type` are plain varchar. The conventional `type` vocabulary, assembled client-side by the SPA (see [UI Screens](./ui-screens.md) §2.5):

| Preset | System modes send | BU mode sends |
|---|---|---|
| Info | `SYS_INFO` | `BU_INFO` |
| Warning | `SYS_WARNING` | `BU_WARNING` |
| Critical | `SYS_CRITICAL` | `BU_CRITICAL` |
| Maintenance | `SYS_MAINTENANCE` | `BU_MAINTENANCE` |
| Other… | custom token, verbatim — **no prefix** | custom token, verbatim — **no prefix** |

Custom tokens are `[A-Z0-9_]+`, ≤50 chars (SPA validation; the column accepts any varchar(255)). API callers omitting `type` get the gateway defaults `SYS_INFO` / `BU_INFO`. `tb_notification`'s doc comment lists the wider vocabulary in use elsewhere (`PR`, `PR_COMMENT`, `SR`, `SR_COMMENT`).

## 5. Divergences from carmen-platform SPA shape

The SPA types (`src/types/index.ts`) are **write-only DTOs** — `BroadcastSystemPayload` and `BroadcastBuPayload` describe requests; there is no SPA read type because the SPA never reads broadcasts back.

| SPA shape | SPA source | Prisma storage | Notes |
| --------- | ---------- | -------------- | ----- |
| `bu_code: string` | `BroadcastBuPayload` | `scope_id String? @db.Uuid` | The API takes the mutable BU **code**; micro-notification resolves it against live `tb_business_unit` rows and stores the UUID. Unknown/deleted code → the create fails (500 envelope, `Business unit not found: <code>`). The original code is preserved in `metadata.bu_code` |
| `userIds?: string[]` | `BroadcastSystemPayload` | — (switches table) | Present → one `tb_notification` row per **existing** id (unknown ids silently dropped); absent → one `tb_broadcast_notification` row. The same endpoint writes to two different tables depending on this field |
| `type?: string` (optional) | both payloads | `@default("SYS_INFO")` | Type resolution (`SYS_`/`BU_` prefixing) happens **client-side** in `BroadcastCompose.resolveType`; the SPA always sends a resolved value. The server defaults only protect non-SPA callers |
| `metadata?: Record<string, unknown>` | both payloads | `Json? @db.JsonB` | The SPA never sets it. BU sends arrive with `bu_code` merged in server-side, so a stored BU row's metadata is never null-equivalent to what the caller sent |
| `scheduled_at?: string` (ISO) | both payloads | `DateTime?` | The SPA converts its `datetime-local` input via `new Date(v).toISOString()` — browser-local time, shipped as UTC |
| — | — | `created_by_id` | The gateway forwards the token user as `from_user_id` and its Swagger doc claims "the token user becomes `from_user_id`" — but micro-notification's **system** path drops it (`CreateSystemNotificationData` has no such field): system broadcast rows store `created_by_id = null`. Only **BU** rows record the sender. Targeted fan-out rows also store `from_user_id = null` |
| — | — | `end_at`, `dismissed_at` | Schema-only fields with no reader or writer anywhere (§2.1, §2.2) |

## 6. References

REST surface (backend-gateway). **Note the prefix: `/api/notifications/...`, not `/api-system/...`** — the SPA originally called `/api-system` and was fixed in carmen-platform commit `579b3f7`. Both routes carry `KeycloakGuard` (bearer auth) only; no RBAC or app-id guard — see [Permissions](./permissions.md) §2.

| Method + Path | Auth | Purpose | Notes |
|---|---|---|---|
| `POST /api/notifications/broadcasts/system` | Bearer | System-wide or targeted send | Body `{ title, message, type?, metadata?, scheduled_at?, userIds? }`. Without `userIds`: one broadcast row (`system-to-user`), live emit to all active users when unscheduled. With `userIds`: per-user `tb_notification` fan-out. 201 `{ notifications, count }` |
| `POST /api/notifications/broadcasts/bu` | Bearer | BU-scoped send | Body `{ bu_code, title, message, type?, metadata?, scheduled_at? }`. One broadcast row (`bu-to-user`, `scope_id` = resolved BU id), live emit to BU members when unscheduled. 201 adds `bu_code` to the response |
| `GET /api/notifications` / `/recent` / `/unread` | Bearer | Recipient-side lists | Merge personal + in-scope broadcast rows; broadcasts filtered by `deleted_at IS NULL` and `scheduled_at IS NULL OR <= NOW()` |
| `PUT /api/notifications/:id/read` | Bearer | Mark read | FE passes the row's `category`; `system-to-user`/`bu-to-user` route to a `tb_user_broadcast_action` upsert, anything else to `tb_notification` |

No Bruno collection exists for the broadcast endpoints as of 2026-06-10; the Swagger annotations on the gateway controller are the closest contract document.

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_broadcast_notification` (line 357), `tb_user_broadcast_action` (line 388), `tb_notification` (line 316).
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.service.ts` — `createSystemNotification` (fan-out fork), `createBusinessUnitNotification` (`bu_code` resolution), `createBroadcastNotification`, `markBroadcastAsRead`/`markAllBroadcastsAsRead`, the scoped list queries.

**Secondary (gateway + consumer shape):**
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` — the two POST routes, payload interfaces, TCP forwarding, type defaults.
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.controller.ts` — create dispatch, broadcast-vs-fanout discriminator, live emit + `is_sent` stamping.
- `../carmen-platform/src/types/index.ts` — `BroadcastTargetMode`, `BroadcastTypePreset`, `BroadcastSystemPayload`, `BroadcastBuPayload`; `src/services/broadcastService.ts` — the two calls.

**Cross-links:** [Broadcasts landing](/en/platform/broadcasts) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Business Units data-model](../business-units/data-model.md) (the `scope_id` target) &nbsp;·&nbsp; [Users data-model](../users/data-model.md) (recipients and read-state rows)
