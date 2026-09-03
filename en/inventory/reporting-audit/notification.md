---
title: Notification
description: Cross-tenant notification fan-out — personal notification rows plus a newer, separate broadcast mechanism (tb_broadcast_notification + tb_user_broadcast_action), reusable message templates, and platform-wide news posts with real BU scoping and a draft/published/archived lifecycle.
published: true
date: 2026-07-22T03:05:28.000Z
tags: reporting-audit, notification, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Notification

> **At a Glance**
> **Owner:** Workflow runtime (writes) + Sysadmin / Platform Admin (templates & news) &nbsp;·&nbsp; **Tables:** `tb_notification` (personal) + `tb_broadcast_notification` / `tb_user_broadcast_action` (broadcast — not previously documented) + `tb_message_format` + `tb_news` &nbsp;·&nbsp; **Used by:** every workflow stage transition + scheduled report delivery &nbsp;·&nbsp; The inbound message pipe — personal inbox, BU/system broadcasts, templates, platform bulletins.

## Implementation status (verified 2026-07-22)

Two corrections to the previous version of this page:

1. **A separate broadcast mechanism exists and was undocumented.** `tb_broadcast_notification` (one row per broadcast, `category` = `'system-to-user'` or `'bu-to-user'`, `scope_id` = the `business_unit.id` for BU-scoped broadcasts) + `tb_user_broadcast_action` (per-user read/dismiss state, created lazily on first action) is confirmed **live** — actively read/written in `micro-notification/src/notification/notification.service.ts` and exposed through `backend-gateway/src/notification/notification.controller.ts`. Its own Prisma doc-comment (on `model tb_broadcast_notification`, `prisma-shared-schema-platform/schema.prisma` line ~372) states it explicitly: *"This replaces the previous fan-out-on-write pattern that inserted one `tb_notification` row per recipient for the same broadcast message."* `tb_notification` remains real and live for **personal**, per-recipient notifications (workflow events, scheduled-report delivery — see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule)); the unified inbox list merges both sources (`source: 'personal' | 'broadcast'`) into one response shape for the frontend.
2. **`tb_news` has real BU scoping and a draft/published/archived lifecycle** — the opposite of what this page previously claimed. `business_unit_ids` (JSONB array; empty = global, non-empty = scoped to those BUs) and `status enum_news_status` (`draft` default, `published`, `archived`) both exist and are enforced by `news.service.ts`: a freshly-created post defaults to `draft` and is invisible to `findPublicAll()`/`findPublicOne()` (which both hard-filter `status: published`) until explicitly published.

## 1. What & Who

The notification entity is the **inbound message pipe** — every workflow stage transition, comment mention, system bulletin, and platform announcement is materialised so the app shell can render a badge + inbox drawer, and optionally dispatch via email, SMS, or push.

Five platform-schema tables collaborate:

- `tb_notification` — row-per-recipient personal inbox (workflow events, scheduled-report delivery).
- `tb_broadcast_notification` + `tb_user_broadcast_action` — the real, current broadcast mechanism: one row per broadcast message regardless of audience size, with per-user read state created lazily on first action (open/dismiss) rather than fanned out on write.
- `tb_message_format` — reusable templates with channel flags `is_email` / `is_sms` / `is_in_app`.
- `tb_news` — platform-wide or BU-scoped bulletins with a `draft`/`published`/`archived` lifecycle.

All live in **platform schema** because notifications cross BU boundaries and broadcasts must reach every tenant.

**Maintained by** workflow runtime (writes personal + broadcast rows per-event), Sysadmin (templates), Platform Admin (news). **Read by** the app shell inbox (`notification.controller.ts`'s unified list, merging `tb_notification` + `tb_broadcast_notification`) and dashboard widget.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| View inbox | App shell → notification bell | Unified list merging `tb_notification` (`source: 'personal'`) and `tb_broadcast_notification` (`source: 'broadcast'`) |
| Mark a personal notification as read | Click message | Updates `tb_notification.is_read = true` |
| Mark a broadcast as read | Click message | Client sends the `category` it received (`system-to-user`/`bu-to-user`); backend upserts a `tb_user_broadcast_action` row (lazily created on first action, not pre-materialised per recipient) |
| Edit a message template | Sysadmin → Platform Config → Message Formats | Affects every event using that format |
| Post a platform bulletin | Platform Admin → News | Defaults to `status = draft` — **not** visible publicly until explicitly set to `published`; can be scoped to specific BUs via `business_unit_ids` |
| Schedule a notification | Set `scheduled_at` | Dispatcher fires when schedule passes |
| Resend dispatch | Re-process via outbound channel | `is_sent` tracks per-channel delivery (personal `tb_notification` only) |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| User did not receive expected notification | Recipient resolution missed; or `is_in_app = false` on the format | Check `tb_message_format` channel flags + workflow recipient map |
| Duplicate inbox rows for one event | Recipient set contained duplicates | App must dedup before insert |
| Template name conflict | `tb_message_format.name` exists among non-deleted | Reactivate or pick different name |
| Email dispatched but in-app missing | `is_in_app = false` on format | Toggle on if both channels needed |
| Click-through 404 | `metadata` references a deleted tenant entity | No FK enforcement; UI must handle gracefully |

## 4. Edge Cases

- **Cross-schema linkage.** `metadata` may carry tenant identifiers (e.g. PR id). Platform schema enforces no FKs into tenant tables.
- **News scope is real, not global-only.** `business_unit_ids` (JSONB array) — an empty array means globally visible; a non-empty array scopes the post to only those business units. `findPublicAll()` applies `OR: [{business_unit_ids: {equals: []}}, {business_unit_ids: {array_contains: [bu_id]}}]` when a `bu_id` is supplied.
- **News has a draft/published/archived lifecycle.** `status` defaults to `draft` on create; `create()`/`update()` auto-stamp `published_at = now()` the first time `status` transitions to `published` (unless an explicit `published_at` was supplied). Public queries hard-filter `status: published AND published_at <= now()` — a draft post is invisible outside the admin screen.
- **Broadcast read state is lazy, not fanned out.** `tb_user_broadcast_action` rows are created on first read/dismiss action per user, not pre-inserted for every eligible recipient when the broadcast is created — this is the explicit design reason `tb_broadcast_notification` replaced the older per-recipient `tb_notification` fan-out for broadcasts.
- **System messages.** `from_user_id IS NULL` (personal) / broadcasts have no `from_user_id` requirement at all.
- **Read ownership.** `is_read` (personal) / `tb_user_broadcast_action.is_read` (broadcast) both owned by the recipient — writer never updates them.

---

## 5. Data Model (Dev)

Source: platform schema.

### 5.1 `tb_notification`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `from_user_id` / `to_user_id` | `String? @db.Uuid` | Yes | FKs to `tb_user`. `from = NULL` = system. |
| `type` | `String @db.VarChar(255)` | No | Default `SYS_INFO`. Discriminator (`SYS_INFO`, `BU_INFO`, `PR`, `PR_COMMENT`, `SR`, `SR_COMMENT`, …). |
| `category` | `String @db.VarChar(255)` | No | Default `system`. `system` or `user-to-user`. |
| `title` / `message` | `String?` | Yes | Display text. |
| `metadata` | `Json? @db.JsonB` | Yes | Source context (entity_id, route, event id). |
| `is_read` / `is_sent` | `Boolean?` | Yes | Default `false`. |
| `scheduled_at` | `DateTime?` | Yes | Defer-until timestamp. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Added 2026-06-12 across 103 platform/tenant tables. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 5.2 `tb_broadcast_notification` (real, not previously documented)

One row per broadcast message regardless of audience size — replaces the older per-recipient `tb_notification` fan-out for system-wide and BU-wide messages.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `category` | `String @db.VarChar(50)` | No | `'system-to-user'` (whole platform) or `'bu-to-user'` (single BU). |
| `scope_id` | `String? @db.Uuid` | Yes | `business_unit.id` when `category = 'bu-to-user'`; `null` for `'system-to-user'`. |
| `type` | `String @db.VarChar(255)` | No | Default `SYS_INFO`. Same discriminator space as `tb_notification.type`. |
| `title` / `message` | `String?` | Yes | Display text. |
| `metadata` | `Json? @db.JsonB` | Yes | Source context. |
| `scheduled_at` / `end_at` | `DateTime?` | Yes | Defer-until / expiry. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Indexes:** `[category, scope_id, created_at DESC]`, `[deleted_at]`.

### 5.3 `tb_user_broadcast_action` (real, not previously documented)

Per-user read/dismiss state for a broadcast — created lazily on first action, not pre-inserted per eligible recipient.

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `broadcast_id` | `String @db.Uuid` | No | FK to `tb_broadcast_notification`, `onDelete: Cascade`. |
| `user_id` | `String @db.Uuid` | No | FK to `tb_user`, `onDelete: Cascade`. |
| `is_read` | `Boolean?` | Yes | Default `false`. |
| `read_at` / `dismissed_at` | `DateTime?` | Yes | Timestamps. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| Audit columns | — | Yes | `created_at`, `updated_at` only (no soft delete). |

**Constraints:** `@@unique([broadcast_id, user_id])`; `@@index([user_id, is_read])`.

### 5.4 `tb_message_format`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Format name (e.g. `pr_stage_advanced`). |
| `message` | `String?` | Yes | Template body with interpolation tokens. |
| `is_email` | `Boolean` | No | Default `false`. |
| `is_sms` | `Boolean?` | Yes | Default `false`. |
| `is_in_app` | `Boolean?` | Yes | Default `true`. Materialise inbox row. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])`.

### 5.5 `tb_news` (corrected — real BU scoping and publish lifecycle)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `title` | `String @db.VarChar` | No | Bulletin title. |
| `contents` | `String? @db.VarChar` | Yes | Body. |
| `url` | `String? @db.VarChar` | Yes | Optional read-more URL. |
| `image_file_token` | `String? @db.VarChar` | Yes | Banner image — a `tb_file_tag` token (see [reporting-audit/attachment](/en/inventory/reporting-audit/attachment)), **not** a raw `image` URL as previously documented. |
| `business_unit_ids` | `Json @db.JsonB` | No | Default `[]`. Empty = every BU (global); non-empty = scoped to those BU ids. |
| `tags` | `Json @db.JsonB` | No | Default `[]`. Normalized lowercase, deduplicated, max 20 tags of ≤40 chars each. |
| `status` | `enum_news_status` | No | Default `draft`. `draft` / `published` / `archived`. |
| `published_at` | `DateTime? @db.Timestamptz(6)` | Yes | Auto-stamped on first transition to `published` unless explicitly supplied. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Required on every update (`COMMON_DOC_VERSION_REQUIRED` error otherwise). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Indexes:** `[status, published_at]` (`tb_news_status_published_at_idx`).

## 6. Business Rules

- **Two independent delivery mechanisms.** Personal, per-recipient events use `tb_notification` (one row per recipient, app responsible for dedup). System/BU broadcasts use `tb_broadcast_notification` (one row regardless of audience size) + lazily-created `tb_user_broadcast_action` rows.
- **Channel dispatch.** `tb_message_format` flags decide which channels attempt delivery; `is_sent` records outcome — applies to `tb_notification` only (no per-channel dispatch flag was found on the broadcast tables).
- **Read state.** Owned by recipient in both mechanisms — `tb_notification.is_read` vs. `tb_user_broadcast_action.is_read`/`read_at`/`dismissed_at`.
- **Format uniqueness.** `tb_message_format.name` unique among non-deleted; recover via reactivate or insert under new name.
- **News is BU-scopeable and gated by publish status.** `business_unit_ids` (empty = global) and `status` (`draft` default; only `published` + `published_at <= now()` rows are publicly visible) both enforced server-side in `news.service.ts`.
- **Scheduling.** Dispatcher flips `is_sent` only when `scheduled_at` fires (personal `tb_notification`); `tb_broadcast_notification` also carries `scheduled_at`/`end_at` but the dispatch-timing mechanism for broadcasts was not independently traced in this pass.

## 7. Cross-References

- All workflow modules — [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [vendor-pricelist](/en/inventory/vendor-pricelist).
- [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) — a fired report schedule dispatches one `POST /api/internal/notifications` call per recipient (personal, `type: REPORT_READY`), not a broadcast.
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — `tb_news.image_file_token` references the same `tb_file_tag` registry.
- [access-control/user](/en/inventory/access-control/user) — `from_user_id` / `to_user_id` / `user_id` resolution.
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — workflow events typically write both an activity row and a notification.
- [system-config/workflow](/en/inventory/system-config/workflow) — recipient resolution against stage role types.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_message_format` (line ~289), `tb_notification` (line ~332), `tb_broadcast_notification` (near `tb_news`), `tb_user_broadcast_action` (line ~406), `tb_news` (line ~834), `enum_news_status` (line ~723).
- **Backend (personal + broadcast unified read/write):** `../carmen-turborepo-backend-v2/apps/micro-notification/src/notification/notification.service.ts`, `../carmen-turborepo-backend-v2/apps/backend-gateway/src/notification/notification.controller.ts`.
- **Backend (news):** `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` (admin CRUD), `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/public-news.service.ts` (public read).
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — role types driving notifications.
