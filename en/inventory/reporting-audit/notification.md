---
title: Notification
description: Cross-tenant notification fan-out — notification rows, reusable message templates, and platform-wide news posts.
published: true
date: 2026-05-17T11:00:00.000Z
tags: reporting-audit, notification, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Notification

> **At a Glance**
> **Owner:** Workflow runtime (writes) + Sysadmin / Platform Admin (templates & news) &nbsp;·&nbsp; **Table:** `tb_notification` (+ `tb_message_format`, `tb_news`) &nbsp;·&nbsp; **Used by:** every workflow stage transition &nbsp;·&nbsp; The inbound message pipe — inbox, templates, platform bulletins.

## 1. What & Who

The notification entity is the **inbound message pipe** — every workflow stage transition, comment mention, system bulletin, and platform announcement is materialised so the app shell can render a badge + inbox drawer, and optionally dispatch via email, SMS, or push.

Three platform-schema tables collaborate: `tb_notification` (row-per-message inbox), `tb_message_format` (reusable templates with channel flags `is_email` / `is_sms` / `is_in_app`), and `tb_news` (platform-wide bulletins). All live in **platform schema** because notifications cross BU boundaries and broadcasts must reach every tenant.

**Maintained by** workflow runtime (writes per-event), Sysadmin (templates), Platform Admin (news). **Read by** the app shell inbox and dashboard widget.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| View inbox | App shell → notification bell | Filtered to `to_user_id = me` |
| Mark as read | Click message | Updates `is_read = true` |
| Edit a message template | Sysadmin → Platform Config → Message Formats | Affects every event using that format |
| Post a platform bulletin | Platform Admin → News | Visible to every tenant immediately |
| Schedule a notification | Set `scheduled_at` | Dispatcher fires when schedule passes |
| Resend dispatch | Re-process via outbound channel | `is_sent` tracks per-channel delivery |

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
- **News broadcast scope.** `tb_news` has no BU scoping — every authenticated user across every tenant sees rows. Use targeted in-app for tenant-specific.
- **System messages.** `from_user_id IS NULL`.
- **Read ownership.** `is_read` owned by recipient — writer never updates it.

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
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 5.2 `tb_message_format`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Format name (e.g. `pr_stage_advanced`). |
| `message` | `String?` | Yes | Template body with interpolation tokens. |
| `is_email` | `Boolean` | No | Default `false`. |
| `is_sms` | `Boolean?` | Yes | Default `false`. |
| `is_in_app` | `Boolean?` | Yes | Default `true`. Materialise inbox row. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])`.

### 5.3 `tb_news`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `title` | `String @db.VarChar` | No | Bulletin title. |
| `contents` | `String? @db.VarChar` | Yes | Body. |
| `url` / `image` | `String? @db.VarChar` | Yes | Optional read-more URL / banner. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

## 6. Business Rules

- **Recipient fan-out.** One event may produce many `tb_notification` rows. App responsible for dedup.
- **Channel dispatch.** `tb_message_format` flags decide which channels attempt delivery; `is_sent` records outcome.
- **Read state.** Owned by recipient.
- **Format uniqueness.** `name` unique among non-deleted; recover via reactivate or insert under new name.
- **News scope.** Global — every authenticated user across every tenant.
- **Scheduling.** Dispatcher flips `is_sent` only when `scheduled_at` fires.

## 7. Cross-References

- All workflow modules — [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]].
- [[access-control/user]] — `from_user_id` / `to_user_id` resolution.
- [[reporting-audit/activity]] — workflow events typically write both rows.
- [[system-config/workflow]] — recipient resolution against stage role types.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification` (lines ~267-301), `tb_message_format` (lines ~226-245), `tb_news` (lines ~690-703).
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — role types driving notifications.
