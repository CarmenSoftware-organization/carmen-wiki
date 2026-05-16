---
title: Notification
description: Cross-tenant notification fan-out — notification rows, reusable message templates, and platform-wide news posts.
published: true
date: 2026-05-16T08:00:00.000Z
tags: reporting-audit, notification, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Notification

## 1. Purpose

The notification entity is the **inbound message pipe** for users — every workflow stage transition, comment mention, system bulletin, and platform announcement is materialised here so the app shell can render a notification badge, an inbox drawer, and (optionally) dispatch the same message through email, SMS, or push.

Three platform-schema tables collaborate:

- `tb_notification` is the row-per-message inbox table. Each row pairs a `from_user_id` with a `to_user_id`, carries a `type` discriminator (`SYS_INFO`, `BU_INFO`, `PR`, `PR_COMMENT`, `SR`, `SR_COMMENT`, …), a `category` (`system` or `user-to-user`), a `title` / `message` body, and `is_read` / `is_sent` flags. It is the per-user inbox surface and the audit trail of what was delivered.
- `tb_message_format` is the **reusable template** catalogue. Each row names a format, holds the template body, and flags which channels it ships through (`is_email`, `is_sms`, `is_in_app`). Workflow stage transitions and other system events pick a format by name and render concrete `tb_notification` rows from it.
- `tb_news` is the platform-wide bulletin table — broadcast announcements (release notes, planned maintenance) with a title, body, optional URL, and image. Renders in a dashboard widget separately from the per-user inbox.

All three live in the **platform schema** because notifications cross BU boundaries and platform-admin broadcasts must reach every tenant.

## 2. Prisma Model(s)

Source: platform schema (`packages/prisma-shared-schema-platform/prisma/schema.prisma`).

### 2.1 `tb_notification`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `from_user_id` | `String? @db.Uuid` | Yes | FK to `tb_user`. `NULL` for system-originated messages. |
| `to_user_id` | `String? @db.Uuid` | Yes | FK to `tb_user`. The recipient. |
| `type` | `String @db.VarChar(255)` | No | Default `SYS_INFO`. Discriminator: `SYS_INFO`, `BU_INFO`, `PR`, `PR_COMMENT`, `SR`, `SR_COMMENT`, plus module-specific values. |
| `category` | `String @db.VarChar(255)` | No | Default `system`. Either `system` or `user-to-user`. |
| `title` | `String?` | Yes | Display title. |
| `message` | `String?` | Yes | Display body. |
| `metadata` | `Json? @db.JsonB` | Yes | Source context (entity_id, route, original event id). |
| `is_read` | `Boolean?` | Yes | Default `false`. Recipient has opened the message. |
| `is_sent` | `Boolean?` | Yes | Default `false`. Outbound channel (email / SMS / push) confirmed delivery. |
| `scheduled_at` | `DateTime?` | Yes | Defer-until timestamp for scheduled notifications. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** FKs to `tb_user` for `from_user_id`, `to_user_id`, `created_by_id`, `updated_by_id` all `onDelete: NoAction`. No application uniqueness constraint — the same logical event may produce one row per recipient.

### 2.2 `tb_message_format`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Format name (e.g. `pr_stage_advanced`). |
| `message` | `String?` | Yes | Template body — may include interpolation tokens. |
| `is_email` | `Boolean` | No | Default `false`. Ship via email. |
| `is_sms` | `Boolean?` | Yes | Default `false`. Ship via SMS. |
| `is_in_app` | `Boolean?` | Yes | Default `true`. Materialise a `tb_notification` row. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `messageformat_name_deleted_at_u` — names unique among non-deleted rows. FK to `tb_user` for audit columns `onDelete: NoAction`.

### 2.3 `tb_news`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `title` | `String @db.VarChar` | No | Bulletin title. |
| `contents` | `String? @db.VarChar` | Yes | Bulletin body (may include short HTML / markdown depending on renderer). |
| `url` | `String? @db.VarChar` | Yes | Optional read-more URL. |
| `image` | `String? @db.VarChar` | Yes | Optional banner image URL. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** primary key only. No FKs; this is a broadcast surface read by everyone.

## 3. Usage / Cross-References

- **Workflow stage transitions across all approval modules** — every advance / approve / reject / cancel on [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], and [[vendor-pricelist]] picks a `tb_message_format` row by name, renders the per-stakeholder messages, and writes one `tb_notification` row per recipient. Recipient resolution is performed by the workflow runtime against [[system-config/workflow]] role types and [[access-control/business-unit-user]] memberships.
- [[access-control/user]] — `from_user_id` / `to_user_id` resolve through this entity. System messages have `from_user_id IS NULL`.
- [[reporting-audit/activity]] — workflow events typically write *both* an activity row and one or more notification rows.
- App shell / dashboard — the in-app inbox component polls `tb_notification` filtered by `to_user_id = me AND is_read = false`. The dashboard renders `tb_news` as a separate bulletin widget.

## 4. Configuration UI

- **Notifications inbox** — every authenticated user sees their own inbox in the app shell. Marking-as-read updates `is_read`. No CRUD beyond that for end users.
- **Message format catalogue** — managed by **Sysadmin** (or Notification Admin) under Platform Configuration → Message Formats. Editing here changes the rendered output of *every* event that picks that format; preview / sample-render is recommended before save.
- **News bulletins** — managed by **Platform Admin** (super_admin / platform_admin from `enum_platform_role` on [[access-control/user]]). Posting a row makes the bulletin visible to every tenant immediately.

## 5. Business Rules

- **Recipient fan-out.** A single business event may produce many `tb_notification` rows (one per recipient). The application is responsible for de-duplication if a recipient appears more than once in the resolved set.
- **Channel dispatch.** `tb_message_format` channel flags decide *whether* email / SMS / in-app delivery is attempted. Each successful outbound (or skipped) sets `is_sent = true` on the in-app row when the in-app channel is configured.
- **Read state.** `is_read` is owned by the recipient; the writer never updates it.
- **Cross-schema linkage.** `metadata` may carry tenant-side identifiers (e.g. PR id). The platform schema does not enforce FKs into tenant tables; the inbox UI calls back into the appropriate tenant API when the user clicks through.
- **Format uniqueness.** `tb_message_format.name` is unique among non-deleted rows; recover a deleted format by reactivating or by inserting a new row with a different name.
- **News broadcast scope.** `tb_news` has no BU scoping — every authenticated user across every tenant sees the rows. Use targeted in-app notifications for tenant-specific announcements.
- **Scheduling.** `scheduled_at` lets a notification be queued for future delivery; the dispatcher only flips `is_sent` once the schedule fires.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification` (lines ~267-301), `tb_message_format` (lines ~226-245), `tb_news` (lines ~690-703).
- **Frontend route (if known):** Inbox drawer is part of the app shell; news widget on the dashboard. Message-format admin under Platform Configuration; news posting in the platform-admin app.
- **carmen/docs (if applicable):** `../carmen/docs/workflow-permissions-system.md` describes the role types whose workflow stage events drive most of the notifications written here.
- **Cross-module:** see Section 3.
