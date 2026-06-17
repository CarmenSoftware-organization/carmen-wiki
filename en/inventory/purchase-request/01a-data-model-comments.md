---
title: Purchase Request — Data Model — Comment Tables
description: Document-level and line-level comment / attachment tables for the Purchase Request module — message text, attachments JSON, and the user/system comment-type enum.
published: true
date: 2026-06-17T08:00:00.000Z
tags: purchase-request, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# Purchase Request — Data Model — Comment Tables

## 1. At a Glance

The Purchase Request module persists user-authored and system-generated notes plus file attachments on dedicated `*_comment` tables, separate from the lifecycle-bearing header / detail tables documented in [01 — Data Model](/en/inventory/purchase-request/01-data-model). Every comment row carries a free-text `message`, an `attachments` JSON array of S3-token records (`{originalName, fileToken, contentType}`), and a `type` discriminator (`enum_comment_type`) that distinguishes user-authored entries from system-generated transition notes such as approval decisions, return-to-requester reasons, and workflow-stage notes. Document-level comments anchor to the PR header (`tb_purchase_request_comment`); detail-level comments anchor to a specific PR line (`tb_purchase_request_detail_comment`), supporting per-line clarifications and per-line approval decisions.

## 2. Shared Shape

Every `*_comment` row in this module follows the same column layout:

```
id                  uuid / PK
<parent>_id         uuid / FK to header or detail row
message             text (free-form, nullable)
attachments         json — array of `{originalName, fileToken, contentType}` (nullable)
type                enum_comment_type — `user` (default) | `system`
doc_version         Int — optimistic-concurrency version counter (default 0)
created_at          timestamp
created_by_id       uuid / FK to tb_user
updated_at          timestamp
updated_by_id       uuid / FK to tb_user
```

The same shape applies to header-level comments and detail-level comments; only the parent FK differs.

## 3. Tables

### 3.1 tb_purchase_request_comment

Workflow / activity-log entries attached to a PR header. The Prisma schema has no dedicated `tb_purchase_request_workflow` table — this comment table, combined with the JSON workflow columns on the header, is the persistent record of the workflow timeline. Each row is either a user comment (`type = user`) or a system event (`type = system`) such as a stage transition.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `purchase_request_id` | `String @db.Uuid` | No | FK to `tb_purchase_request.id`. |
| `type` | `enum_comment_type` | No | `user` or `system`; default `user`. |
| `user_id` | `String @db.Uuid` | Yes | Author user id (null for `system` entries). |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of `{ originalName, fileToken, contentType }`; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version counter; default 0. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `purchase_request_id → tb_purchase_request.id` (`NoAction` on delete/update).
**Indexes:** None declared beyond the primary key.

### 3.2 tb_purchase_request_detail_comment

Line-level counterpart of `tb_purchase_request_comment`. Captures comments and system events attached to a single PR line — typically used during approval to record stage-level decisions and rejection reasons per line.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `purchase_request_detail_id` | `String @db.Uuid` | No | FK to `tb_purchase_request_detail.id`. |
| `type` | `enum_comment_type` | No | `user` or `system`; default `user`. |
| `user_id` | `String @db.Uuid` | Yes | Author user id. |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of attachments; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version counter; default 0. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `purchase_request_detail_id → tb_purchase_request_detail.id`.
**Indexes:** None declared beyond the primary key.

## 4. Cross-References

- Sibling: [01 — Data Model](/en/inventory/purchase-request/01-data-model) — `tb_purchase_request` and `tb_purchase_request_detail` (header / line tables), enum definitions, and the workflow / history JSON columns.
- Sibling: [02 — Business Rules](/en/inventory/purchase-request/02-business-rules) — validation rules and workflow-stage comment behaviors that persist to `tb_purchase_request_comment` / `tb_purchase_request_detail_comment`.
- Upstream: [Purchase Request Module Overview](/en/inventory/purchase-request) — module landing page.
