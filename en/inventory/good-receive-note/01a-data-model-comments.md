---
title: Goods Receive Note — Data Model — Comment Tables
description: Document-level and line-level comment / attachment tables for the Goods Receive Note module — message text, attachments JSON, and the user/system comment-type enum.
published: true
date: 2026-05-20T00:00:00.000Z
tags: good-receive-note, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# Goods Receive Note — Data Model — Comment Tables

## 1. At a Glance

The Goods Receive Note module persists user-authored and system-generated notes plus file attachments on dedicated `*_comment` tables, separate from the lifecycle-bearing header / detail tables documented in [01 — Data Model](/en/inventory/good-receive-note/01-data-model). Every comment row carries a free-text `message`, an `attachments` JSON array of S3-token records (`{originalName, fileToken, contentType}`), and a `type` discriminator (`enum_comment_type`) that distinguishes user-authored entries from system-generated transition notes. Document-level comment tables anchor to the document header; detail-level comment tables anchor to a specific line, enabling per-line evidence (e.g. "photo of damage on this specific item").

## 2. Shared Shape

Every `*_comment` row in this module follows the same column layout:

```
id                  uuid / PK
<parent>_id         uuid / FK to header or detail row
message             text (free-form, nullable)
attachments         json — array of `{originalName, fileToken, contentType}` (nullable)
type                enum_comment_type — `user` (default) | `system`
created_at          timestamp
created_by_id       uuid / FK to tb_user
updated_at          timestamp
updated_by_id       uuid / FK to tb_user
```

The same shape applies to header-level comments and detail-level comments; only the parent FK differs.

## 3. Tables

### 3.1 tb_good_received_note_comment

Workflow / activity-log entries attached to a GRN header. There is no dedicated `tb_good_received_note_workflow` table — this comment table, combined with the JSON workflow columns on the header, is the persistent record of the workflow timeline. Each row is either a user comment (`type = user`) or a system event (`type = system`) such as a stage transition.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `good_received_note_id` | `String @db.Uuid` | No | FK to `tb_good_received_note.id`. |
| `type` | `enum_comment_type` | No | `user` or `system`; default `user`. |
| `user_id` | `String @db.Uuid` | Yes | Author user id (null for `system` entries). |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of `{ originalName, fileToken, contentType }`; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `good_received_note_id → tb_good_received_note.id` (`NoAction` on delete/update).
**Indexes:** None declared beyond the primary key.

### 3.2 tb_good_received_note_detail_comment

Line-level counterpart of `tb_good_received_note_comment`. Captures comments and system events attached to a single GRN line — typically used during inspection to record acceptance / rejection notes and during commit to log per-line posting decisions.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `good_received_note_detail_id` | `String @db.Uuid` | No | FK to `tb_good_received_note_detail.id`. |
| `type` | `enum_comment_type` | No | `user` or `system`; default `user`. |
| `user_id` | `String @db.Uuid` | Yes | Author user id (null for `system` entries). |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of attachments; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `good_received_note_detail_id → tb_good_received_note_detail.id` (`NoAction` on delete/update).
**Indexes:** None declared beyond the primary key.

## 4. Cross-References

- Sibling: [01 — Data Model](/en/inventory/good-receive-note/01-data-model) — header and detail tables, enum definitions, ERD, the divergence-from-design table.
- Sibling: [02 — Business Rules](/en/inventory/good-receive-note/02-business-rules) — validation rules for the GRN lifecycle.
- Upstream: [Goods Receive Note Module Overview](/en/inventory/good-receive-note) — module landing page.
