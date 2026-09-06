---
title: Broadcasts — Data Model
description: The tb_broadcast_notification and tb_user_broadcast_action field tables after the notification redesign — new enums and a real optimistic-lock doc_version.
published: true
date: 2026-09-06T23:45:00.000Z
tags: book/platform, broadcasts, data-model
editor: markdown
dateCreated: 2026-06-10T13:15:00.000Z
---

# Broadcasts — Data Model

> **At a Glance**
> **Tables:** `tb_broadcast_notification` (one row per `system_all`/`bu` broadcast) + `tb_user_broadcast_action` (lazy per-user read state, unique per broadcast×user) &nbsp;·&nbsp; **Targeted fork:** `system_users` sends (`userIds`) skip both tables and fan out into `tb_notification` (one personal row per recipient) — invisible to the admin List/Edit screens &nbsp;·&nbsp; **Enums, not varchar:** `scope` (`enum_broadcast_scope`), `doc_type`/`event` (`enum_notification_doc_type`/`enum_notification_event`, shared with `tb_notification`) replaced the old `category`/`type` varchar columns &nbsp;·&nbsp; **No severity column:** the sender's Info/Warning/Critical/Maintenance/Other… label lives only in `metadata.severity`; `event` is hardcoded `info` on every broadcast &nbsp;·&nbsp; **`end_at` is mandatory** and drives the derived `status` (never a stored column) &nbsp;·&nbsp; **`doc_version` is a real optimistic lock** now, checked by both `PATCH` and `DELETE` &nbsp;·&nbsp; **Endpoints:** `POST /api/notifications/broadcasts/system` / `/bu` (send) plus `GET`/`GET :id`/`PATCH :id`/`DELETE :id` — `/api`, **not** `/api-system`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The module owns two tables, plus a fork into a third. `tb_broadcast_notification` is one row per `system_all`/`bu` message regardless of audience size, with the audience encoded as `scope` (`system` or `business_unit`) plus `scope_id`. `tb_user_broadcast_action` holds per-user state — created **lazily**, only when a user acts (marks read); absence of a row means "not acted on yet", and the unread queries LEFT JOIN to surface broadcasts without a row.

A **`system_users`** send (an explicit `userIds` list) bypasses both broadcast tables entirely and fans out into `tb_notification` — one row **per existing recipient id** (unknown ids silently dropped). This is not a legacy leftover being phased out: it is the module's only supported way to notify a hand-picked list of people, and it is also the one target mode the sender-side admin **List** and **Edit** screens cannot see, search, edit, or soft-delete afterward — `GET .../broadcasts` (§6) queries `tb_broadcast_notification` exclusively. The Compose screen's own subtitle says so: *"Broadcasts sent to specific users don't appear here — they're recorded as individual notifications."*

The persistence path is backend-gateway (`api/notifications/broadcasts/*`, `KeycloakGuard` + `PlatformPermissionGuard`) → RPC → micro-notification. Two services split the work on the notification side: **`BroadcastService`** owns the create path (resolving `bu_code`, writing the row, the read-state upserts, and the recipient-resolution helpers the live push uses) and **`BroadcastAdminService`** owns the sender-side list/get/update/delete surface, including status derivation. **`NotificationWriteService`** is the single write entry point for `notifications.create`: it delegates to `BroadcastService` for any non-`users` audience and writes `tb_notification` rows directly, in one transaction, for a `users` audience.

## 2. Entities

### 2.1 `tb_broadcast_notification`

One `system_all`/`bu` broadcast message. Schema line 369.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `scope_id` | `String? @db.Uuid` | Yes | `tb_business_unit.id` when `scope = 'business_unit'`; `null` for `'system'`. Resolved server-side from the payload's `bu_code` (live BUs only) — the row stores the stable UUID, not the renameable code |
| `title` | `String?` | Yes | Notification title (the SPA requires it; the column does not) |
| `message` | `String?` | Yes | Notification body (same — required by the SPA only) |
| `metadata` | `Json? @db.JsonB` | Yes | Free-form. Carries the sender's cosmetic `severity` label plus server-merged `bu_code`/`id` — see §5 |
| `scheduled_at` | `DateTime? @db.Timestamptz(6)` | Yes | Visibility cutoff: list queries hide the row until `scheduled_at <= NOW()` |
| `end_at` | `DateTime? @db.Timestamptz(6)` | Yes | **Mandatory at send time** (the SPA and the Zod request schema both require it) — the primary input to `deriveStatus()`: past `end_at` means `expired` |
| `doc_type` | `enum_notification_doc_type` | No | `system` for `system_all`/`system_users`, `business_unit` for `bu` — set at create time from the request path, not user input |
| `event` | `enum_notification_event` | No | **Hardcoded `info`** on every broadcast created through this module's two send endpoints — there is no way for a sender to make a broadcast carry any other event value |
| `scope` | `enum_broadcast_scope` | No | `system` or `business_unit` — replaces the pre-redesign `category` varchar (`'system-to-user'`/`'bu-to-user'`) |
| `doc_version` | `Int @default(0) @db.Integer` | No | **Now a real optimistic lock.** `BroadcastAdminService.update()`/`.remove()` both read it, compare it against the caller's value (409 on mismatch), and write it conditionally (`updateMany` with `doc_version` in the `where`, `{ increment: 1 }` in the `data`) so two concurrent PATCHes can never both "win" |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Audit: row creation; also the default list sort key |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit/sender: FK → `tb_user`. Populated with the token user on every send in this redesign (both system and BU paths) |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | **Written on every successful `PATCH`/`DELETE`** now — but never returned by the API (see §5) |
| `updated_by_id` | `String? @db.Uuid` | Yes | **Written on every successful `PATCH`/`DELETE`** — same invisibility caveat |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft delete. **`DELETE /api/notifications/broadcasts/:id` now writes this** — a real code path exists, superseding the "no code path ever writes it" finding from the pre-redesign wiki |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: FK → `tb_user`, written by the same delete path |

**Constraints:** `@id` on `id`. FK relations: `created_by_id`/`updated_by_id` → `tb_user.id` (`onDelete: NoAction`). No unique constraints — nothing stops identical duplicate sends.

**Indexes:** `@@index([scope, scope_id, created_at(sort: Desc)])` (replaced the pre-redesign `[category, scope_id, created_at]` index — created *before* the column drop so there is never a window without one) · `@@index([deleted_at])`.

**Status is computed, not stored.** `BroadcastAdminService.deriveStatus()` reads `deleted_at`/`scheduled_at`/`end_at` against a single reference `now`: `deleted_at` set → `deleted` (wins over everything); else `scheduled_at` still future → `scheduled`; else `end_at` already past → `expired`; else `active`.

### 2.2 `tb_user_broadcast_action`

Lazy per-user state for one `system_all`/`bu` broadcast. Schema line 403. **Unchanged** from the pre-redesign shape.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `broadcast_id` | `String @db.Uuid` | No | FK → `tb_broadcast_notification.id`, `onDelete: Cascade` |
| `user_id` | `String @db.Uuid` | No | FK → `tb_user.id`, `onDelete: Cascade` |
| `is_read` | `Boolean? @default(false)` | Yes | Read flag; unread queries treat a missing row and `is_read = false` identically |
| `read_at` | `DateTime?` | Yes | Stamped by the mark-as-read upsert |
| `dismissed_at` | `DateTime?` | Yes | **Declared but dead** — no code writes it |
| `doc_version` | `Int @default(0) @db.Integer` | No | **Still schema-only here** — the mark-read upserts (`markBroadcastAsRead`/`markAllBroadcastsAsRead`) never read or increment it |
| `created_at` / `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Default `now()`; `updated_at` touched by the mark-read upsert |

**Constraints:** `@@unique([broadcast_id, user_id])` (`user_broadcast_action_broadcast_user_u`) — the mark-read path upserts against this key. **Indexes:** `@@index([user_id, is_read])`.

Rows are written by exactly two paths in micro-notification: single mark-as-read (`BroadcastService.markBroadcastAsRead`, a Prisma upsert) and mark-all-as-read (`markAllBroadcastsAsRead`, one raw SQL `INSERT … ON CONFLICT … DO UPDATE` covering every in-scope unread broadcast in a single round trip) — both unchanged by the redesign.

### 2.3 `tb_notification` (referenced — the targeted-send fork)

The personal-notification table (schema line 332). **Reshaped by the same redesign**: `type` (varchar), `category` (varchar), and `is_sent` (boolean) were all **dropped**; `doc_type`/`event` (the same two enums broadcasts use) and a new `pushed_at` timestamp were added.

| Field | Type | Notes |
|---|---|---|
| `to_user_id` / `from_user_id` | `String? @db.Uuid` | FKs to `tb_user`; a targeted broadcast's rows carry the sender as `from_user_id` |
| `doc_type` | `enum_notification_doc_type` | Forwarded from the envelope — `system` for a targeted system send |
| `event` | `enum_notification_event` | Forwarded from the envelope — `info` for a targeted broadcast |
| `pushed_at` | `DateTime? @db.Timestamptz(6)` | **New.** Set once the row has been emitted on the WebSocket bus — replaces the removed `is_sent` boolean, which was "set to true at INSERT time without waiting for delivery" and therefore never carried real information |
| `scheduled_at` | `DateTime? @db.Timestamptz(6)` | Same visibility-cutoff semantics as the broadcast table |
| `is_read` | `Boolean? @default(false)` | Unchanged |

`NotificationWriteService.notify()` writes one row per id in `userIds` inside a single transaction (all-or-nothing — a mid-batch failure used to leave later recipients silently unwritten under the old per-recipient loop). **A new 30-second `ScheduleWorker` cron now claims due, unpushed `tb_notification` rows** (`scheduled_at <= NOW()`, `pushed_at IS NULL`, capped to a 7-day-old window, `FOR UPDATE SKIP LOCKED`) and pushes each live via the same `emitNotification()` helper `emitCreated()` uses, then stamps `pushed_at`. **This worker only ever queries `tb_notification`** — a scheduled `system_all`/`bu` broadcast gets no equivalent; see [Permissions](/en/platform/broadcasts/permissions) §3.

## 3. Relationships

- `tb_broadcast_notification` 1:M `tb_user_broadcast_action` — `broadcast_id`, `onDelete: Cascade`.
- `tb_user` 1:M `tb_user_broadcast_action` — `user_id`, `onDelete: Cascade`.
- `tb_user` 1:M `tb_broadcast_notification` via `created_by_id` / `updated_by_id` (`NoAction` — audit references).
- **`scope_id` → `tb_business_unit.id` is convention, not a Prisma relation.** Validated only at send time; a BU deleted later leaves the broadcast row pointing at a dead scope.

## 4. Enums

**This is a real enum-backed schema now — not plain varchar.** The pre-redesign `category`/`type` varchar columns have been fully replaced:

| Enum | Values | Used by |
|---|---|---|
| `enum_broadcast_scope` | `system`, `business_unit` | `tb_broadcast_notification.scope` |
| `enum_notification_doc_type` | `system`, `business_unit`, `purchase_request`, `store_requisition`, `purchase_order`, `good_received_note`, `credit_note` | `tb_broadcast_notification.doc_type`, `tb_notification.doc_type` (broadcasts only ever use the first two) |
| `enum_notification_event` | `info`, `workflow`, `comment` | `tb_broadcast_notification.event` (hardcoded `info`), `tb_notification.event` |

There is **no `severity` column anywhere** in either table. The sender's Info/Warning/Critical/Maintenance/Other… choice is a client-side-only convenience, persisted purely as a string inside `metadata.severity` and echoed back by `BroadcastAdminService.toRow()` as the wire-level `severity` field so the admin list/edit UI can render its own badges. It has no effect on what a recipient sees: every broadcast's `event` is `info`, and the client's own preview panel says so directly ("Colour and label are an internal categorisation — recipients see a standard notification"). Custom Other… tokens are validated client-side only (`[A-Z0-9_]+`, ≤50 chars, auto-uppercased); the server accepts any string in `metadata`.

## 5. Divergences from carmen-platform SPA shape

| SPA shape | SPA source | Prisma storage | Notes |
| --------- | ---------- | -------------- | ----- |
| `bu_code: string` | `BroadcastBuPayload` | `scope_id String? @db.Uuid` | The API takes the mutable BU **code**; resolved against live `tb_business_unit` rows and stored as the UUID. Unknown/soft-deleted code → the create fails with a **404** (`COMMON_BUSINESS_UNIT_NOT_FOUND`, `http_status: 404` in the shared error catalog) — corrects the pre-redesign wiki's "500-enveloped" description |
| `userIds?: string[]` | `BroadcastSystemPayload` | — (switches to `tb_notification`) | Present → one row per **existing** id (unknown ids dropped); absent → one `tb_broadcast_notification` row |
| `end_at: string` (**required**) | both payloads | `DateTime?` (nullable column, non-null in practice) | The column stays nullable in Prisma, but both the SPA and the Zod request schema (`SystemBroadcastCreateSchema`/`BuBroadcastCreateSchema`) require it unconditionally — even on the `userIds` fan-out branch, where `NotifyInput`'s `audience: { kind: 'users' }` has no `end_at` field of its own to carry it into |
| `metadata.severity?: string` | both payloads (via `resolveSeverity()`) | `Json? @db.JsonB` | Client-only categorisation — see §4. There is **no** server-side `type` field to resolve to anymore; the pre-redesign `SYS_*`/`BU_*` prefixing scheme no longer exists |
| `metadata.bu_code`, `metadata.id` | server-merged | `Json? @db.JsonB` | `NotificationWriteService`'s `buildMetadata()` always folds `bu_code`/`doc_id` into the stored `metadata`, merged (not replaced) on update — a client PATCH cannot overwrite these two keys even by sending them explicitly (`BroadcastAdminService.update()` strips `bu_code`/`id` from the caller's `metadata` before merging) |
| `scheduled_at?: string` (ISO) | both payloads | `DateTime?` | Unchanged: the SPA converts its `datetime-local` input via `new Date(v).toISOString()` |
| — | — | `severity` (wire field, no DB column) | `BroadcastAdminRow.severity` is synthesized per-row from `metadata.severity`, not read from a schema field — there isn't one |
| — | — | `updated_at`, `updated_by_id` | **Written by every `PATCH`/`DELETE` but never returned** by `GET`/`GET :id`/`PATCH`/`DELETE` (`BroadcastAdminRow`/`BroadcastListItem` carry no `updated_at`/`updated_by` field at all) — the List screen's CSV export still requests these two columns and they render permanently blank (see [UI Screens](/en/platform/broadcasts/ui-screens) §2.1). The `PageHeader`'s audit line on the Edit screen therefore only ever shows "Created", never "Updated", even for a broadcast that has in fact been edited |
| — | — | `end_at`, `dismissed_at` (on `tb_user_broadcast_action`) | `dismissed_at` remains schema-only (§2.2); the broadcast table's own `end_at` is the opposite case — no longer dead, see above |
| `created_by_id` (**resolved divergence**) | — | `created_by_id` | The pre-redesign wiki documented a live inconsistency: the gateway's Swagger doc claimed "the token user becomes `from_user_id`", but the system-send code path silently dropped it, leaving `created_by_id = null` on every `system_all` row (only BU rows recorded a sender). `BroadcastService.create()` now sets `created_by_id: input.from_user_id ?? null` for **every** non-`users` audience — `system_all` and `bu` sends both record the sender consistently. This divergence is fixed, not merely re-described |

## 6. References

REST surface (backend-gateway), all under `/api/notifications/...` — **not** `/api-system/...`. **Still no `AppIdGuard` on any of the six broadcast routes** (unlike News's authenticated CRUD) — re-verified against the current controller: the class carries `@ApiHeaderRequiredXAppId()`, which only documents the header for Swagger, and none of the six route decorators add an `AppIdGuard` to their `@UseGuards(...)` list.

| Method + Path | Auth | Purpose | Notes |
|---|---|---|---|
| `POST /api/notifications/broadcasts/system` | Bearer + `broadcast.send` (coarse: platform-wide or any cluster) | System-wide or targeted send | Body `{ title, message, end_at, metadata?, scheduled_at?, userIds? }`. Without `userIds`: one broadcast row (`scope: system`). With `userIds`: per-user `tb_notification` fan-out. 201 |
| `POST /api/notifications/broadcasts/bu` | Bearer + `broadcast.send` (same coarse check) | BU-scoped send | Body `{ bu_code, title, message, end_at, metadata?, scheduled_at? }`. One broadcast row (`scope: business_unit`, `scope_id` = resolved BU id). 201 |
| `GET /api/notifications/broadcasts` | Bearer + `broadcast.read` | Sender-side admin list | Every row regardless of schedule/expiry (unlike the recipient endpoints below); `page`/`perpage`/`search`/`sort`/`status`/`scope`/`include_deleted`; returns `{ data, paginate, summary }` where `summary` deliberately ignores the `status` filter |
| `GET /api/notifications/broadcasts/:id` | Bearer + `broadcast.read` | Sender-side single fetch | Returns soft-deleted rows too (`status: "deleted"`), so a deleted list entry stays openable |
| `PATCH /api/notifications/broadcasts/:id` | Bearer + `broadcast.update` | Update schedule/expiry/content | Requires `doc_version` (409 on mismatch); `title`/`message`/`metadata` only while `status === 'scheduled'` (400 `content_locked` otherwise); a past `end_at` is how "Expire Now" works |
| `DELETE /api/notifications/broadcasts/:id` | Bearer + `broadcast.delete` | Soft-delete | Requires `doc_version` as a query param (409 on mismatch) |
| `GET /api/notifications` / `/recent` / `/unread` | Bearer | Recipient-side lists | Merge personal + in-scope broadcast rows; broadcasts filtered by `deleted_at IS NULL` and `scheduled_at IS NULL OR <= NOW()` |
| `GET /api/notifications/:notification_id` | Bearer | Single recipient-side fetch | Returns the `tb_notification` row if the caller is the recipient, or the `tb_broadcast_notification` row if the caller is in scope; 404 otherwise — same scope/`scheduled_at` filters as the list endpoints above |
| `PUT /api/notifications/:id/read` | Bearer | Mark read | Client passes the row's `source` (`'broadcast'` or `'personal'`, **not** the retired `category`) to route to the right table |
| `PUT /api/notifications/mark-all-read` | Bearer | Mark every unread notification read, personal **and** broadcast | Marks both in one call: `tb_notification.updateMany({ to_user_id, is_read: false })` **and** `BroadcastService.markAllBroadcastsAsRead()` (§2.2's raw-SQL upsert) run together via `Promise.all`. **The gateway's own Swagger description undersells this** — it says only "every unread `tb_notification` row" — but the RPC handler's own doc comment and its actual implementation (`notification.service.ts`'s `markAllNotificationsAsRead()`) cover both tables and return `{ count, personal_count, broadcast_count }` |

No Bruno collection exists for the broadcast endpoints (verified still absent) — the Swagger annotations on the gateway controller are the closest contract document.

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification` (line 332), `tb_broadcast_notification` (line 369), `tb_user_broadcast_action` (line 403), enums (lines 112–131).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260810000000_notification_redesign_additive/`, `20260811000000_notification_redesign_drop_legacy/migration.sql` — the enum introduction, backfill, and column drops.
- `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/broadcast.service.ts` (create, recipient resolution), `broadcast-admin.service.ts` (list/get/update/delete, `deriveStatus`), `notification-write.service.ts` (single write entry point), `schedule.worker.ts` (due-notification push, `tb_notification` only).

**Secondary (gateway + consumer shape):**
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` — all six broadcast routes, payload builders, TCP forwarding.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/dto/notification/notification.dto.ts` — `SystemBroadcastCreateSchema`/`BuBroadcastCreateSchema` (`end_at` required), `BroadcastListQuerySchema`.
- `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts` — `COMMON_BUSINESS_UNIT_NOT_FOUND` (`http_status: 404`).
- `../carmen-platform/src/types/index.ts` — `BroadcastTargetMode`, `BroadcastTypePreset`, `BroadcastListItem`, `BroadcastStatus`, `BroadcastUpdatePayload`, `BroadcastSummary`; `src/services/broadcastService.ts` — the six calls.

**Cross-links:** [Broadcasts landing](/en/platform/broadcasts) &nbsp;·&nbsp; [UI Screens](/en/platform/broadcasts/ui-screens) &nbsp;·&nbsp; [Permissions](/en/platform/broadcasts/permissions) &nbsp;·&nbsp; [Business Units — Data Model](/en/platform/business-units/data-model) (the `scope_id` target) &nbsp;·&nbsp; [Users — Data Model](/en/platform/users/data-model) (recipients and read-state rows)
