---
title: Notification
description: Notification fan-out after the 2026-08 redesign — personal rows (doc_type + event), system/BU broadcasts with lazy per-user read state, the internal NotifyInput bridge, and BU-scoped platform news with a publish lifecycle.
published: true
date: 2026-09-23T10:06:26.000Z
tags: reporting-audit, notification, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Notification

> **At a Glance**
> **Owner:** Workflow runtime + micro-cronjobs/micro-report (writes) · Platform Admin (broadcasts `broadcast.send`, news) · BU admin (per-BU `tb_notification_template` for email/in-app copy) &nbsp;·&nbsp; **Tables (platform):** `tb_notification` (personal) + `tb_broadcast_notification` / `tb_user_broadcast_action` (broadcast) + `tb_news` &nbsp;·&nbsp; **Gone:** `tb_message_format` (dropped 2026-08-11) &nbsp;·&nbsp; **Used by:** every workflow stage transition, comments, scheduled-report delivery, platform bulletins.

![Notification screen](/screenshots/reporting-audit/notification.png)

## Implementation status (re-verified 2026-09-22)

The notification tables were **redesigned in August 2026** (platform migrations `20260810000000_notification_redesign_additive` and `20260811000000_notification_redesign_drop_legacy`; frontend contract `ac44c550`). Corrections to the 2026-07-22 version of this page:

1. `tb_notification` lost `type`, `category` and `is_sent`; it now carries `doc_type enum_notification_doc_type` (`system`, `business_unit`, `purchase_request`, `store_requisition`, `purchase_order`, `good_received_note`, `credit_note`), `event enum_notification_event` (`info`, `workflow`, `comment`) and `pushed_at`. The `SYS_INFO` / `BU_INFO` / `PR_COMMENT` discriminator strings and the `system` / `user-to-user` category are gone.
2. `tb_broadcast_notification` lost `category` and `type`; it now carries `scope enum_broadcast_scope` (`system` | `business_unit`) + `scope_id`, plus the same `doc_type` / `event` pair. The `'system-to-user'` / `'bu-to-user'` strings on this page were the pre-redesign contract.
3. **`tb_message_format` is gone** (removed by the drop-legacy migration) and with it the `is_email` / `is_sms` / `is_in_app` channel flags. The per-BU **notification templates** screen ([system-config/notification-template](/en/inventory/system-config/notification-template), tenant table `tb_notification_template`: `name`, `type enum_notification_channel`, `subject`, `body`, `description`, `is_active`; gateway `api/config/:bu_code/notification-templates`) is a different, tenant-scoped feature — not a rename of `tb_message_format`. `tb_user.is_online` was removed in the same migration.
4. The write path is now a single validated envelope, **`NotifyInput`** (`packages/notification-contract`), also exposed as the internal HTTP bridge `POST /api/internal/notifications` used by micro-cronjobs and micro-report (§5.6).
5. The unified inbox gained `GET /api/notifications/unread` (paginated) and `GET /api/notifications/recent` (last 30 days); the list response carries `source` (`personal` | `broadcast`) per row and an optional `summary { unread, read }` (its absence means "could not be computed", not zero).

Still true: `tb_news` has real BU scoping and a `draft` / `published` / `archived` lifecycle enforced by `news.service.ts`.

## 1. What & Who

The notification entity is the **inbound message pipe** — every workflow stage transition, comment, scheduled-report delivery, system bulletin and platform announcement is materialised so the app shell can render a badge + inbox drawer (and optionally send email through the BU's email profile).

Four platform-schema tables collaborate:

- `tb_notification` — row-per-recipient personal inbox (workflow events, comments, report-ready notices).
- `tb_broadcast_notification` + `tb_user_broadcast_action` — the broadcast mechanism: one row per broadcast message regardless of audience size, with per-user read state created lazily on first action (open/dismiss) rather than fanned out on write.
- `tb_news` — platform-wide or BU-scoped bulletins with a `draft` / `published` / `archived` lifecycle.

All live in the **platform schema** because notifications cross BU boundaries and broadcasts must reach every tenant.

**Maintained by** the workflow runtime and other services through `NotifyInput` (personal + broadcast rows per event), Platform Admin (broadcasts, news), BU admin (`tb_notification_template` copy). **Read by** the app shell inbox (`notification.controller.ts` unified list merging both sources).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| View inbox | App shell → notification bell | `GET /api/notifications` (all, paginated) / `recent` (30 days) / `unread`; rows carry `source`, `doc_type`, `event`, `metadata.id` (document id) |
| Mark a personal notification as read | Click message | `PUT /api/notifications/{id}/read` with `{ source: "personal" }` (or omitted) → `tb_notification.is_read = true` |
| Mark a broadcast as read | Click message | Same endpoint with `{ source: "broadcast" }` → upserts a `tb_user_broadcast_action` row (lazily created on first action) |
| Mark everything read | Inbox → mark all | `PUT /api/notifications/mark-all-read` |
| Push a system-wide or BU broadcast | Platform admin | `POST /api/notifications/broadcasts/system` / `broadcasts/bu` — platform permission `broadcast.send`; sender-side list/edit/delete at `GET/PATCH/DELETE /api/notifications/broadcasts[/:id]` |
| Edit the copy of workflow / report emails for this BU | `/system-admin/notification-template` | Tenant `tb_notification_template` rows per channel (`enum_notification_channel`) — see [system-config/notification-template](/en/inventory/system-config/notification-template) |
| Post a platform bulletin | Platform Admin → News | Defaults to `status = draft` — **not** visible publicly until explicitly set to `published`; can be scoped to specific BUs via `business_unit_ids` |
| Schedule a notification | Set `scheduled_at` in `NotifyInput` | Dispatcher fires when the schedule passes; `pushed_at` records delivery |
| Notify from another service | `POST /api/internal/notifications` | `NotifyInput` envelope (§5.6); used by micro-cronjobs report fires and micro-report |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| User did not receive expected notification | Recipient resolution missed (`audience.kind = users` with the wrong ids), or the BU email profile is not configured for email delivery | Check the workflow recipient map and the BU email profile |
| `400` from `/api/internal/notifications` | Payload fails `NotifyInputSchema` (unknown `doc_type`/`event`, or a key from the wrong `audience` branch — e.g. `user_ids` with `kind: business_unit`) | Fix the envelope |
| `404` from `/api/internal/notifications` | `audience.kind = business_unit` names an unknown `bu_code` | Fix the code |
| Read state not sticking on a broadcast | Client sent `source: personal` (or none) for a broadcast row | Echo back the `source` received from the list endpoint |
| Duplicate inbox rows for one event | Recipient set contained duplicates | App must dedup before insert |
| Click-through 404 | `metadata.id` references a deleted tenant entity | No FK enforcement; UI must handle gracefully |

## 4. Edge Cases

- **Cross-schema linkage.** `metadata` may carry tenant identifiers (the new write path always puts the document id in `metadata.id`; older rows may still carry `pr_id` / `po_id` / `sr_id` / `grn_id` / `cn_id` — no new rows are produced with those keys). Platform schema enforces no FKs into tenant tables.
- **News scope is real, not global-only.** `business_unit_ids` (JSONB array) — an empty array means globally visible; a non-empty array scopes the post to only those business units. `findPublicAll()` applies `OR: [{business_unit_ids: {equals: []}}, {business_unit_ids: {array_contains: [bu_id]}}]` when a `bu_id` is supplied.
- **News has a draft/published/archived lifecycle.** `status` defaults to `draft` on create; `create()`/`update()` auto-stamp `published_at = now()` the first time `status` transitions to `published` (unless an explicit `published_at` was supplied). Public queries hard-filter `status: published AND published_at <= now()`.
- **Broadcast read state is lazy, not fanned out.** `tb_user_broadcast_action` rows are created on first read/dismiss action per user — the explicit design reason `tb_broadcast_notification` replaced the older per-recipient `tb_notification` fan-out for broadcasts.
- **System messages.** `from_user_id IS NULL` (personal); broadcasts have no `from_user_id` at all.
- **Read ownership.** `is_read` (personal) / `tb_user_broadcast_action.is_read` (broadcast) both owned by the recipient — writer never updates them.
- **`summary` is optional.** The list endpoint computes `{ unread, read }` in a try/catch; a missing summary means the count could not be produced, not that it is zero (`types/notification.ts`).

---

## 5. Data Model (Dev)

Source: platform schema (`packages/prisma-shared-schema-platform/prisma/schema.prisma`).

### 5.1 `tb_notification`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `from_user_id` / `to_user_id` | `String? @db.Uuid` | Yes | FKs to `tb_user`. `from = NULL` = system. |
| `doc_type` | `enum_notification_doc_type` | No | `system`, `business_unit`, `purchase_request`, `store_requisition`, `purchase_order`, `good_received_note`, `credit_note`. |
| `event` | `enum_notification_event` | No | `info`, `workflow`, `comment`. |
| `title` / `message` | `String?` | Yes | Display text. |
| `metadata` | `Json? @db.JsonB` | Yes | Source context — `id` (document id), `action`, `current_stage`, `is_fully_approved`, … |
| `is_read` | `Boolean?` | Yes | Default `false`. |
| `scheduled_at` / `pushed_at` | `DateTime?` | Yes | Defer-until / delivered-at. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Indexes:** `[to_user_id, is_read, created_at DESC]`, `[deleted_at]`. Removed 2026-08-11: `type`, `category`, `is_sent`.

### 5.2 `tb_broadcast_notification`

One row per broadcast message regardless of audience size.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `scope` | `enum_broadcast_scope` | No | `system` (whole platform) or `business_unit`. |
| `scope_id` | `String? @db.Uuid` | Yes | `business_unit.id` when `scope = business_unit`; `null` for `system`. |
| `doc_type` / `event` | enums as above | No | Same discriminators as `tb_notification`. |
| `title` / `message` | `String?` | Yes | Display text. |
| `metadata` | `Json? @db.JsonB` | Yes | Source context. |
| `scheduled_at` / `end_at` | `DateTime?` | Yes | Defer-until / expiry. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

Removed 2026-08-11: `category`, `type`.

### 5.3 `tb_user_broadcast_action`

Per-user read/dismiss state for a broadcast — created lazily on first action.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `broadcast_id` | `String @db.Uuid` | No | FK to `tb_broadcast_notification`, `onDelete: Cascade`. |
| `user_id` | `String @db.Uuid` | No | FK to `tb_user`. |
| `is_read` | `Boolean?` | Yes | Default `false`. |
| `read_at` / `dismissed_at` | `DateTime?` | Yes | Timestamps. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| Audit columns | — | Yes | `created_at`, `updated_at` only (no soft delete). |

**Constraints:** `@@unique([broadcast_id, user_id])`; `@@index([user_id, is_read])`.

### 5.4 `tb_message_format` — removed

Removed by `20260811000000_notification_redesign_drop_legacy`. Nothing replaces its platform-wide channel flags; per-BU message copy lives in the tenant `tb_notification_template` ([system-config/notification-template](/en/inventory/system-config/notification-template)), and channel delivery (web / email) is decided per call by the writer (e.g. a report schedule's `notifications { web, email }`).

### 5.5 `tb_news`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `title` | `String @db.VarChar` | No | Bulletin title. |
| `contents` | `String? @db.VarChar` | Yes | Body. |
| `url` | `String? @db.VarChar` | Yes | Optional read-more URL. |
| `image_file_token` | `String? @db.VarChar` | Yes | Banner image — a `tb_file_tag` token (see [reporting-audit/attachment](/en/inventory/reporting-audit/attachment)). |
| `business_unit_ids` | `Json @db.JsonB` | No | Default `[]`. Empty = every BU (global); non-empty = scoped to those BU ids. |
| `tags` | `Json @db.JsonB` | No | Default `[]`. Normalized lowercase, deduplicated, max 20 tags of ≤40 chars each. |
| `status` | `enum_news_status` | No | Default `draft`. `draft` / `published` / `archived`. |
| `published_at` | `DateTime? @db.Timestamptz(6)` | Yes | Auto-stamped on first transition to `published` unless explicitly supplied. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Required on every update (`COMMON_DOC_VERSION_REQUIRED` otherwise). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Indexes:** `[status, published_at]` (`tb_news_status_published_at_idx`).

### 5.6 `NotifyInput` envelope (`packages/notification-contract`)

```
NotifyInput {
  doc_type:  enum_notification_doc_type
  event:     enum_notification_event
  title, message: string
  audience:  { kind: "users", user_ids: uuid[] }
           | { kind: "business_unit", bu_code: string }
           | { kind: "all_users" }
  from_user_id?, doc_id?, bu_code?, scheduled_at?, metadata?
}
```

`kind = users` writes one `tb_notification` per id; `business_unit` / `all_users` write one `tb_broadcast_notification` with `scope = business_unit` / `system`. Keys from the wrong branch are rejected. Exposed to non-NestJS callers as `POST /api/internal/notifications` (`internal-notification.controller.ts`, 201 on success) — used by micro-cronjobs for report-ready notices and by micro-report (`pkg/notify/client.go`, HTTP RPC `POST /rpc` `{ pattern, data }` with `x-internal-token`).

## 6. Business Rules

- **Two delivery mechanisms, one envelope.** Personal, per-recipient events use `tb_notification`; system/BU broadcasts use `tb_broadcast_notification` + lazily-created `tb_user_broadcast_action` rows. Both are produced from `NotifyInput.audience.kind`.
- **Read state.** Owned by the recipient in both mechanisms; the client must echo the row's `source` when marking read.
- **Broadcast sending is a platform permission** (`broadcast.send`), not a tenant permission.
- **News is BU-scopeable and gated by publish status.** `business_unit_ids` (empty = global) and `status` (`draft` default; only `published` + `published_at <= now()` rows are publicly visible) both enforced server-side in `news.service.ts`.
- **Scheduling.** `scheduled_at` defers; `pushed_at` records delivery (personal). `tb_broadcast_notification` carries `scheduled_at` / `end_at`; the broadcast dispatch-timing mechanism was not independently traced in this pass.

## 7. Cross-References

- All workflow modules — [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [vendor-pricelist](/en/inventory/vendor-pricelist) — `event = workflow` / `comment` rows via `NotifyInput`.
- [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) — a fired report schedule sends one `POST /api/internal/notifications` per recipient at `notify_at`, not a broadcast.
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — `tb_news.image_file_token` references the same `tb_file_tag` registry.
- [access-control/user](/en/inventory/access-control/user) — `from_user_id` / `to_user_id` / `user_id` resolution.
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — workflow events typically write both an activity row and a notification.
- [system-config/workflow](/en/inventory/system-config/workflow) — recipient resolution against stage role types.
- [system-config/notification-template](/en/inventory/system-config/notification-template) — per-BU message copy.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification`, `tb_broadcast_notification`, `tb_user_broadcast_action`, `tb_news`, `enum_notification_doc_type`, `enum_notification_event`, `enum_broadcast_scope`, `enum_news_status`; migrations `20260810000000_notification_redesign_additive`, `20260811000000_notification_redesign_drop_legacy`.
- **Contract:** `../carmen-turborepo-backend-v2/packages/notification-contract/src/notify-input.schema.ts`.
- **Backend (unified read/write):** `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.service.ts`, `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts` (`GET /`, `recent`, `unread`, `broadcasts*`, `:id`, `PUT :id/read`, `PUT mark-all-read`, `POST broadcasts/system|bu`), `internal-notification.controller.ts` (`POST /api/internal/notifications`).
- **Backend (news):** `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` (admin CRUD), `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/public-news.service.ts` (public read).
- **Backend (per-BU templates):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_notification-templates/config_notification-templates.controller.ts`; tenant `tb_notification_template` (migration `20260525041511_add_notification_template`).
- **Frontend:** `../carmen-inventory-frontend-react/types/notification.ts` (`Notification`, `NotificationSource`, `NotificationDocType`, `NotificationListResponse.summary`), `constant/api-endpoints.ts` (`NOTIFICATIONS`, `NOTIFICATIONS_UNREAD`, `NOTIFICATIONS_MARK_ALL_READ`, `NOTIFICATION_MARK_READ`, `NOTIFICATION_TEMPLATES`).
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — role types driving notifications (frozen 2026-04-27; predates the redesign).
