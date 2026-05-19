---
title: Vendor Price List — Data Model — Comment Tables
description: Document-level and line-level comment / attachment tables for the Vendor Price List module across the pricelist-template, request-for-pricing, and pricelist sub-entity families.
published: true
date: 2026-05-20T00:00:00.000Z
tags: vendor-pricelist, data-model, inventory, carmen-software, comments, attachments
editor: markdown
dateCreated: 2026-05-20T00:00:00.000Z
---

# Vendor Price List — Data Model — Comment Tables

## 1. At a Glance

The Vendor Price List module persists user-authored and system-generated notes plus file attachments on dedicated `*_comment` tables across three sub-entity families — pricelist template, request-for-pricing, and pricelist — separate from the lifecycle-bearing header / detail tables documented in [01 — Data Model](/en/inventory/vendor-pricelist/01-data-model). Every comment row carries a free-text `message`, an `attachments` JSON array of S3-token records (`{originalName, fileToken, contentType}`), and a `type` discriminator (`enum_comment_type`) that distinguishes user-authored entries from system-generated transition notes. Each sub-entity family has its own header-level comment table and detail-level (line-level) comment table, supporting per-line clarifications, vendor-quotation evidence attachment, and per-line approval / rejection decisions across the pricelist-request lifecycle.

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

The same shape applies to header-level comments and detail-level comments across all three sub-entity families (pricelist template, request-for-pricing, pricelist); only the parent FK target differs.

## 3. Tables

### 3.1 tb_pricelist_template_comment

Activity-log entries attached to a template header. Holds user comments and `system` events (status transitions, vendor-instruction edits).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `pricelist_template_id` | `String @db.Uuid` | No | FK to `tb_pricelist_template.id`. |
| `type` | `enum_comment_type` | No | `user` or `system`; default `user`. |
| `user_id` | `String @db.Uuid` | Yes | Author user id (null for `system`). |
| `message` | `String` | Yes | Free-text comment body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of `{ originalName, fileToken, contentType }`; default `[]`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `pricelist_template_id → tb_pricelist_template.id` (`NoAction`).
**Indexes:** None declared beyond the primary key.

### 3.2 tb_pricelist_template_detail_comment

Row-level counterpart of `tb_pricelist_template_comment`. Captures comments and system events attached to a single template detail row.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `pricelist_template_detail_id` | `String @db.Uuid` | No | FK to `tb_pricelist_template_detail.id`. |
| `type` | `enum_comment_type` | No | `user` or `system`; default `user`. |
| `user_id` | `String @db.Uuid` | Yes | Author user id (null for `system`). |
| `message` | `String` | Yes | Free-text body. |
| `attachments` | `Json @db.JsonB` | Yes | Array of attachments; default `[]`. |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | (standard audit) | Yes | Standard audit columns. |

**Constraints:** `@id` on `id`. FK `pricelist_template_detail_id → tb_pricelist_template_detail.id` (`NoAction`).

### 3.3 tb_request_for_pricing_comment / tb_request_for_pricing_detail_comment

Activity-log surfaces on the campaign header and per-vendor invitation. Same shape as the template comment tables — `id`, FK to parent, `type` enum (`user` / `system`), `user_id`, `message`, `attachments`, and the standard audit columns.

| Table | Parent FK | Purpose |
| ----- | --------- | ------- |
| `tb_request_for_pricing_comment` | `request_for_pricing_id → tb_request_for_pricing.id` | Campaign-level activity log: campaign created, vendors selected, emails dispatched, reminders fired, campaign closed. |
| `tb_request_for_pricing_detail_comment` | `request_for_pricing_detail_id → tb_request_for_pricing_detail.id` | Per-vendor invitation activity log: email sent / opened / clicked, portal first-access, draft saved, submission completed. The fine-grained email and portal telemetry (delivered, opened, clicked, IP addresses, session count) described in carmen/docs lives in `attachments` / `message` JSON in the application layer; there are no dedicated Prisma columns for it. |

### 3.4 tb_pricelist_comment / tb_pricelist_detail_comment

Activity-log surfaces on the pricelist header and per-row. Same shape as the template comment tables — `id`, FK to parent, `type` enum (`user` / `system`), `user_id`, `message`, `attachments`, and the standard audit columns.

| Table | Parent FK | Purpose |
| ----- | --------- | ------- |
| `tb_pricelist_comment` | `pricelist_id → tb_pricelist.id` | Pricelist-header activity log: created, vendor saved draft, vendor submitted, validation result, purchaser approved / rejected, status transitions. |
| `tb_pricelist_detail_comment` | `pricelist_detail_id → tb_pricelist_detail.id` | Per-row activity log: row edited by purchaser, validation warning attached, preferred-vendor flag toggled, deviation against historical price logged. |

## 4. Cross-References

- Sibling: [01 — Data Model](/en/inventory/vendor-pricelist/01-data-model) — `tb_pricelist_template`, `tb_request_for_pricing`, `tb_pricelist` (header tables) and their `_detail` siblings, enum definitions, the divergence-from-design catalogue.
- Sibling: [02 — Business Rules](/en/inventory/vendor-pricelist/02-business-rules) — validation rules and workflow-stage comment behaviors across the pricelist template, request-for-pricing, and pricelist sub-entity families, all of which persist to their respective `*_comment` / `*_detail_comment` tables.
- Upstream: [Vendor Price List Module Overview](/en/inventory/vendor-pricelist) — module landing page.
