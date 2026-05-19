---
title: Inventory Adjustment — Data Model: Comment Tables
description: Document-level and line-level comment / attachment tables for the Inventory Adjustment module — message text, attachments JSON, and the user/system comment-type enum.
published: true
date: 2026-05-20T00:00:00.000Z
tags: inventory-adjustment, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# Inventory Adjustment — Data Model: Comment Tables

## 1. At a Glance

The Inventory Adjustment module persists user-authored and system-generated notes plus file attachments on dedicated `*_comment` tables, separate from the lifecycle-bearing header / detail tables documented in [01 — Data Model](/en/inventory/inventory-adjustment/01-data-model). Every comment row carries a free-text `message`, an `attachments` JSON array of S3-token records (`{originalName, fileToken, contentType}`), and a `type` discriminator (`enum_comment_type`) that distinguishes user-authored entries from system-generated transition notes. Document-level comment tables anchor to the document header (`tb_stock_in_comment`, `tb_stock_out_comment`); detail-level comment tables anchor to a specific line (`tb_stock_in_detail_comment`, `tb_stock_out_detail_comment`), enabling per-line evidence such as photos of the specific item's damage or vendor-RMA references.

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

The same shape applies to header-level comments and detail-level comments; only the parent FK differs. The stock-in tables (`tb_stock_in_comment`, `tb_stock_in_detail_comment`) mirror the stock-out tables (`tb_stock_out_comment`, `tb_stock_out_detail_comment`) byte-for-byte in column layout; only the parent FK target differs.

## 3. Tables

### 3.1 tb_stock_in_comment

The **document-level comment / attachment** on a stock-in. Carries free-text `message` and an `attachments` JSON array of S3-token records (photo of damage, vendor RMA, count sheet scan). User-vs-system tagging via `enum_comment_type`.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `stock_in_id` | `String @db.Uuid` | No | FK to `tb_stock_in.id`. |
| `type` | `enum_comment_type` | No | `user` (default) or `system`. |
| `user_id` | `String @db.Uuid` | Yes | User who left the comment. |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of `{originalName, fileToken, contentType}`; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `stock_in_id → tb_stock_in.id` (`NoAction`).

### 3.2 tb_stock_in_detail_comment

The **line-level comment / attachment** on a stock-in detail row. Same shape as `tb_stock_in_comment` but anchored to a specific line — used for "photo of this specific item's damage" or "vendor RMA for this product".

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `stock_in_detail_id` | `String @db.Uuid` | No | FK to `tb_stock_in_detail.id`. |
| `type` | `enum_comment_type` | No | `user` (default) or `system`. |
| `user_id` | `String @db.Uuid` | Yes | User. |
| `message` | `String` | Yes | Free-text. |
| `attachments` | `Json @db.JsonB` | Yes | Array of attachment records; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `stock_in_detail_id → tb_stock_in_detail.id` (`NoAction`).

### 3.3 tb_stock_out_comment, tb_stock_out_detail_comment

Mirror of `tb_stock_in_comment` / `tb_stock_in_detail_comment` for the outbound document. Same column shape; FKs to `tb_stock_out.id` / `tb_stock_out_detail.id` respectively. Used for damage-photo attachment on write-off lines, recall-RMA references, count-shortage sign-off notes.

## 4. Cross-References

- Sibling: [01 — Data Model](/en/inventory/inventory-adjustment/01-data-model) — header and detail tables, the `tb_adjustment_type` reason classifier, enum definitions (`enum_adjustment_type`, `enum_doc_status`, `enum_last_action`, `enum_comment_type`), ERD, and the divergence-from-design catalogue.
- Sibling: [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules) — `ADJ_VAL_010` consumes `tb_stock_in_comment.attachments` / `tb_stock_out_comment.attachments` to enforce the supporting-document requirement when an adjustment type's `info.requiresDocument = true`.
- Upstream: [03 — User Flow: Store Keeper](/en/inventory/inventory-adjustment/03-user-flow-store-keeper) — documents drag-and-drop attachment of evidence onto comment rows during adjustment creation.
- Upstream: [04 — Test Scenarios: Inventory Controller](/en/inventory/inventory-adjustment/04-test-scenarios-inventory-controller) — IC-EDGE-08 covers comment-based escalation flagging by Department Manager.
- Upstream: [Inventory Adjustment Module Overview](/en/inventory/inventory-adjustment) — module landing page.
