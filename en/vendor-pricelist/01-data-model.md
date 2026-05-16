---
title: Vendor Pricelist — Data Model
description: Entities, fields, relationships, and enums for the vendor-pricelist module.
published: true
date: 2026-05-17T11:00:00.000Z
tags: vendor-pricelist, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Data Model

> **At a Glance**
> **Tables:** Tier 1 — `tb_pricelist_template` / `_detail` &nbsp;·&nbsp; Tier 2 — `tb_request_for_pricing` / `_detail` (vendor invitations + URL tokens) &nbsp;·&nbsp; Tier 3 — `tb_pricelist` / `_detail` (vendor submission); plus per-level `_comment` tables
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** request-for-pricing `→ tb_pricelist_template`; invitation `→ tb_vendor` + optional `→ tb_pricelist`; pricelist `→ tb_vendor` / `tb_currency`; pricelist-detail `→ tb_product` / `tb_unit` / `tb_tax_profile`; back-relation from `tb_purchase_request_detail.pricelist_detail_id` (PR price source)
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*`; uniqueness includes `deleted_at`; pricelist-detail unique on `(pricelist_id, product_id, unit_id, moq_qty)` supporting multi-MOQ-tier pricing

> **Source of truth:** Backend Prisma schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
>
> The platform schema contains no vendor-pricelist models; all entities live in the tenant schema. The `generated/client/schema.prisma` files are auto-generated copies and not authoritative.

## 1. Overview

The vendor-pricelist module owns ten tenant-schema entities organised into three tiers. **Tier 1 — Templates** (`tb_pricelist_template`, `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, `tb_pricelist_template_detail_comment`) define what purchasing wants vendors to quote: the product list, default unit-of-measure block, MOQ tier shape, currency, validity window, reminder schedule, and the vendor-facing instructions. **Tier 2 — Request-for-Pricing** (`tb_request_for_pricing`, `tb_request_for_pricing_comment`, `tb_request_for_pricing_detail`, `tb_request_for_pricing_detail_comment`) is the legacy-named "campaign" object — it pins one template to a vendor cohort with start / end dates, a custom message, an email template reference, and per-vendor invitation rows that each carry the cryptographic `pricelist_url_token` and the FK to the vendor's eventual pricelist. **Tier 3 — Pricelist** (`tb_pricelist`, `tb_pricelist_detail`, `tb_pricelist_comment`, `tb_pricelist_detail_comment`) is the vendor's submitted artefact: header with vendor reference, pricelist number, status, validity window, currency, submission method, and url token — plus detail rows that carry product reference, unit, MOQ qty, price-without-tax, tax, and lead time.

The pricelist module sits **adjacent to [[purchase-request]], [[purchase-order]], and [[good-receive-note]]** in the procure-to-pay chain. PR detail rows can reference `tb_pricelist_detail.id` directly via `tb_purchase_request_detail.tb_pricelist_detail` (back-relation on the pricelist detail side); PO snapshots its `price` from the active pricelist at PR-to-PO conversion time (a snapshot copy — no live FK), and GRN runs its price-variance check against the same active pricelist. Pricelist rows reference [[product]], `tb_unit`, `tb_tax_profile`, `tb_currency`, and `tb_vendor`; the request-for-pricing detail rows reference `tb_vendor` (the invited vendor) and `tb_pricelist` (the vendor's eventual submitted pricelist, optional until first submission).

The header on each tier carries its own status enum — `enum_pricelist_template_status` for templates (`draft`, `active`, `inactive`), and `enum_pricelist_status` for pricelists (`draft`, `active`, `inactive`, `expired`); request-for-pricing has no dedicated status enum and is treated as active between `start_date` and `end_date`. The pricelist submission method is captured in a separate enum `pricelist_submission_method` (`online`, `email`, `portal`, `manual`). The carmen/docs concept of a "campaign status" (`draft`, `active`, `paused`, `completed`, `cancelled`) and an "invitation submission status" (`pending`, `in-progress`, `submitted`, `approved`, `expired`) are application-layer derivations from `start_date`, `end_date`, `tb_pricelist.status`, and `tb_pricelist.submitted_at` — there are no Prisma columns or enums for them.

The Prisma model is materially leaner than the carmen/docs design document, which describes a full campaign/invitation analytics layer (response rate, average response time, quality score, IP-address tracking, session count, click-through telemetry, encrypted PII at rest) that is **not yet present in Prisma**. Section 5 catalogues the divergences. Where Prisma and carmen/docs disagree, Prisma is canonical for entities and fields; carmen/docs is canonical for workflow semantics and rule descriptions that the application layer enforces on top of the leaner schema.

## 2. Entities

### 2.1 tb_pricelist_template

Reusable definition of "what to ask vendors for". Carries the product list (via `tb_pricelist_template_detail`), the default currency and validity period, vendor-facing instructions, and the reminder / escalation schedule. One template can drive many request-for-pricing rows.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, generated via `gen_random_uuid()`. |
| `name` | `String @db.VarChar` | No | Human-readable template name; unique among non-soft-deleted rows. |
| `status` | `enum_pricelist_template_status` | No | Template status; default `draft`. |
| `description` | `String @db.VarChar` | Yes | Free-text description for purchasing-team reference. |
| `note` | `String @db.VarChar` | Yes | Free-text note attached to the template. |
| `vendor_instructions` | `String @db.Text` | Yes | Vendor-facing instructions rendered on the portal and on the email body. |
| `currency_id` | `String @db.Uuid` | Yes | Default currency for vendor submissions; FK to `tb_currency`. |
| `currency_code` | `String @db.VarChar` | Yes | Snapshot of the currency code at template creation. |
| `validity_period` | `Int` | Yes | Default validity window in days; pricelist `effective_from_date` + `validity_period` ⇒ `effective_to_date`. |
| `send_reminders` | `Boolean` | Yes | Whether automated reminders are enabled; default `true`. |
| `reminder_days` | `Json @db.JsonB` | Yes | Array of days-before-deadline triggers, e.g., `[14, 7, 3, 1]`; default `[]`. |
| `escalation_after_days` | `Int` | Yes | Days after deadline before escalation; default `0`. |
| `info` | `Json @db.JsonB` | Yes | Extension bag for tenant-specific template attributes; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension / classification array; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version counter; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp; defaults to `now()`. |
| `created_by_id` | `String @db.Uuid` | Yes | User id who created the row. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp; defaults to `now()`. |
| `updated_by_id` | `String @db.Uuid` | Yes | User id who last updated the row. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp; non-null means logically deleted. |
| `deleted_by_id` | `String @db.Uuid` | Yes | User id who soft-deleted the row. |

**Constraints:** `@id` on `id`. FK `currency_id → tb_currency.id` (`NoAction`). Back-relations to `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, and `tb_request_for_pricing`.
**Indexes:** `@@unique([name, deleted_at])` as `pricelist_template_name_deletedat_u`; `@@index([name])` as `pricelist_template_name_idx`.

### 2.2 tb_pricelist_template_detail

Per-product row inside a template. Carries the product reference, the inventory unit (the canonical UoM the product converts to), and the JSON `order_unit_obj` that captures the default order unit plus the MOQ tier definitions (qty + unit per tier) the vendor will be asked to quote against.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `pricelist_template_id` | `String @db.Uuid` | No | FK to `tb_pricelist_template.id`. |
| `sequence_no` | `Int` | Yes | Row ordering within the template; default `1`. |
| `comment` | `String @db.VarChar` | Yes | Per-row comment. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`; required. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot of product code. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot of product name. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised product name snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot of SKU. |
| `inventory_unit_id` | `String @db.Uuid` | Yes | Inventory base UoM at template-build time. |
| `inventory_unit_name` | `String @db.VarChar` | Yes | Snapshot of the inventory unit name. |
| `order_unit_obj` | `Json @db.JsonB` | Yes | Default order unit + MOQ tier definitions; structure `{ default_order: { unit_id, unit_name }, moq: [ { unit_id, unit_name, note, qty }, ... ] }`; default `{}`. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Per-row cost dimensions; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FKs: `pricelist_template_id → tb_pricelist_template.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`, required). Back-relation to `tb_pricelist_template_detail_comment`.
**Indexes:** `@@unique([pricelist_template_id, product_id, deleted_at])` as `pricelist_template_detail_pricelist_template_id_product_id_u`; `@@index([pricelist_template_id, product_id])` and `@@index([product_id])`.

### 2.3 tb_pricelist_template_comment

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

### 2.4 tb_pricelist_template_detail_comment

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

### 2.5 tb_request_for_pricing

The "campaign" object in carmen/docs language. Pins one template to a vendor cohort with start / end dates, a custom message, and an email-template reference; the per-vendor invitations are written to `tb_request_for_pricing_detail`. Has **no Prisma status column** — the application derives `draft` / `active` / `paused` / `completed` / `cancelled` from `start_date`, `end_date`, and the submitted-pricelist counts on its detail rows.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Campaign name; unique among non-soft-deleted rows. |
| `pricelist_template_id` | `String @db.Uuid` | No | FK to `tb_pricelist_template.id`; the template the campaign issues. |
| `start_date` | `DateTime @db.Timestamptz(6)` | Yes | Vendor portal opens at this date. |
| `end_date` | `DateTime @db.Timestamptz(6)` | Yes | Submission deadline. |
| `custom_message` | `String @db.Text` | Yes | Free-text message rendered in the email body and on the portal. |
| `email_template_id` | `String @db.VarChar` | Yes | Reference to a tenant email-template name or id. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension / classification array; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version; default `0`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | Yes | Creation timestamp. |
| `created_by_id` | `String @db.Uuid` | Yes | Creator id. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | Yes | Last-update timestamp. |
| `updated_by_id` | `String @db.Uuid` | Yes | Updater id. |
| `deleted_at` | `DateTime @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String @db.Uuid` | Yes | Soft-delete actor id. |

**Constraints:** `@id` on `id`. FK `pricelist_template_id → tb_pricelist_template.id` (`NoAction`). Back-relations to `tb_request_for_pricing_detail` and `tb_request_for_pricing_comment`.
**Indexes:** `@@unique([name, deleted_at])` as `request_for_pricing_name_u`; `@@index([pricelist_template_id])`; `@@index([name])`.

### 2.6 tb_request_for_pricing_detail

The per-vendor invitation row. Carries the invited vendor reference, the contact triplet (person / phone / email), the optional pricelist link (populated when the vendor first saves a draft), and — most importantly — the `pricelist_url_token` that grants the vendor portal access. There is no separate "invitation status" column: the application infers `pending` / `in-progress` / `submitted` / `approved` / `expired` from the linked `tb_pricelist.status`, `tb_pricelist.submitted_at`, and the campaign's `end_date`.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `request_for_pricing_id` | `String @db.Uuid` | No | FK to `tb_request_for_pricing.id`. |
| `sequence_no` | `Int` | Yes | Row ordering within the campaign; default `1`. |
| `comment` | `String @db.VarChar` | Yes | Per-row comment (e.g., language preference, escalation note). |
| `vendor_id` | `String @db.Uuid` | No | FK to `tb_vendor.id`; the invited vendor. |
| `vendor_name` | `String @db.VarChar` | Yes | Snapshot of the vendor name. |
| `contact_person` | `String @db.VarChar` | Yes | Vendor-side contact name. |
| `contact_phone` | `String @db.VarChar` | Yes | Vendor-side contact phone. |
| `contact_email` | `String @db.VarChar` | Yes | Vendor-side contact email (used for the invitation email). |
| `pricelist_id` | `String @db.Uuid` | Yes | FK to `tb_pricelist.id`; populated on first save. |
| `pricelist_no` | `String @db.VarChar` | Yes | Snapshot of the pricelist reference number. |
| `pricelist_url_token` | `String @db.VarChar` | Yes | Cryptographic per-invitation token authorising portal entry. |
| `info` | `Json @db.JsonB` | Yes | Extension bag; default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version; default `0`. |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | (standard audit) | Yes | Standard audit columns. |

**Constraints:** `@id` on `id`. FKs: `request_for_pricing_id → tb_request_for_pricing.id` (`NoAction`); `vendor_id → tb_vendor.id` (`NoAction`, required); `pricelist_id → tb_pricelist.id` (`NoAction`, optional). Back-relation to `tb_request_for_pricing_detail_comment`.
**Indexes:** `@@unique([request_for_pricing_id, vendor_id, deleted_at])` as `request_for_pricing_detail_request_for_pricing_id_vendor_id_u`; `@@index([request_for_pricing_id, vendor_id])`.

### 2.7 tb_request_for_pricing_comment / tb_request_for_pricing_detail_comment

Activity-log surfaces on the campaign header and per-vendor invitation. Same shape as the template comment tables — `id`, FK to parent, `type` enum (`user` / `system`), `user_id`, `message`, `attachments`, and the standard audit columns.

| Table | Parent FK | Purpose |
| ----- | --------- | ------- |
| `tb_request_for_pricing_comment` | `request_for_pricing_id → tb_request_for_pricing.id` | Campaign-level activity log: campaign created, vendors selected, emails dispatched, reminders fired, campaign closed. |
| `tb_request_for_pricing_detail_comment` | `request_for_pricing_detail_id → tb_request_for_pricing_detail.id` | Per-vendor invitation activity log: email sent / opened / clicked, portal first-access, draft saved, submission completed. The fine-grained email and portal telemetry (delivered, opened, clicked, IP addresses, session count) described in carmen/docs lives in `attachments` / `message` JSON in the application layer; there are no dedicated Prisma columns for it. |

### 2.8 tb_pricelist

The vendor's submitted pricelist header. Carries the pricelist reference number, status, vendor reference, validity window, currency, submission method, and the portal `url_token` (a denormalised snapshot of the invitation token for direct portal navigation after token rotation). One header has many `tb_pricelist_detail` rows; the pricelist may be linked back to the originating `tb_request_for_pricing_detail` row, but the FK lives on the invitation side (`tb_request_for_pricing_detail.pricelist_id`).

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `pricelist_no` | `String @db.VarChar` | No | Pricelist reference number; unique among non-soft-deleted rows. |
| `name` | `String @db.VarChar` | Yes | Pricelist name (e.g., "Q2 2026 — Vendor A — Beverages"). |
| `status` | `enum_pricelist_status` | No | Document status; default `draft`. |
| `url_token` | `String @db.VarChar` | Yes | Portal access token for direct navigation; denormalised copy of the invitation token. |
| `vendor_id` | `String @db.Uuid` | Yes | FK to `tb_vendor.id`. |
| `vendor_name` | `String @db.VarChar` | Yes | Snapshot of the vendor name. |
| `effective_from_date` | `DateTime @db.Timestamptz(6)` | Yes | Validity window start. |
| `effective_to_date` | `DateTime @db.Timestamptz(6)` | Yes | Validity window end. |
| `currency_id` | `String @db.Uuid` | Yes | FK to `tb_currency.id`; the vendor-chosen submission currency. |
| `currency_code` | `String @db.VarChar` | Yes | Snapshot of the currency code. |
| `submission_method` | `pricelist_submission_method` | Yes | How the pricelist was returned; default `online`. |
| `submitted_at` | `DateTime @db.Timestamptz(6)` | Yes | Timestamp the vendor clicked Submit. |
| `description` | `String @db.VarChar` | Yes | Free-text description. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `info` | `Json @db.JsonB` | Yes | Extension bag for tenant-specific header attributes (quality score, validation results, telemetry); default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Cost-dimension array; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version; default `0`. |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | (standard audit) | Yes | Standard audit columns. |

**Constraints:** `@id` on `id`. FKs: `vendor_id → tb_vendor.id` (`NoAction`); `currency_id → tb_currency.id` (`NoAction`). Back-relations to `tb_pricelist_detail`, `tb_pricelist_comment`, and `tb_request_for_pricing_detail`.
**Indexes:** `@@unique([pricelist_no, deleted_at])` as `pricelist_pricelist_no_u`; `@@index([name])`; `@@index([pricelist_no])`.

### 2.9 tb_pricelist_detail

The product row on a submitted pricelist. Carries product reference, unit, MOQ qty, price-without-tax / tax / price, lead time, the `is_preferred` flag (the per-row preferred-vendor designation), and the rating field. The MOQ structure is **one row per MOQ tier** — the unique key `(pricelist_id, product_id, unit_id, moq_qty)` allows multiple rows per product so a vendor can quote different prices at MOQ 1 / 50 / 100.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `pricelist_id` | `String @db.Uuid` | No | FK to `tb_pricelist.id`. |
| `sequence_no` | `Int` | Yes | Row ordering within the pricelist; default `1`. |
| `product_id` | `String @db.Uuid` | No | FK to `tb_product.id`; required. |
| `product_code` | `String @db.VarChar` | Yes | Snapshot of product code. |
| `product_name` | `String @db.VarChar` | Yes | Snapshot of product name. |
| `product_local_name` | `String @db.VarChar` | Yes | Localised product name snapshot. |
| `product_sku` | `String @db.VarChar` | Yes | Snapshot of SKU. |
| `unit_id` | `String @db.Uuid` | Yes | FK to `tb_unit.id`; the unit the vendor quotes in. |
| `unit_name` | `String @db.VarChar` | Yes | Snapshot of the unit name. |
| `is_preferred` | `Boolean` | Yes | `true` when this row is the preferred-vendor pick for the product; default `false`. |
| `rating` | `Int` | Yes | Per-row rating used by the price-assignment engine; default `0`. |
| `tax_profile_id` | `String @db.Uuid` | Yes | FK to `tb_tax_profile.id`. |
| `tax_profile_name` | `String @db.VarChar` | Yes | Snapshot of the tax profile name. |
| `tax_rate` | `Decimal @db.Decimal(15, 5)` | Yes | Effective tax rate; default `0`. |
| `moq_qty` | `Decimal @db.Decimal(20, 5)` | Yes | Minimum order quantity for this row's price; default `0`. Multiple rows per `(pricelist, product, unit)` are permitted at different MOQs. |
| `price_without_tax` | `Decimal @db.Decimal(20, 5)` | Yes | Unit price net of tax; default `0`. |
| `tax_amt` | `Decimal @db.Decimal(20, 5)` | Yes | Tax amount per unit at this price; default `0`. |
| `price` | `Decimal @db.Decimal(20, 5)` | Yes | Unit price gross of tax (`price_without_tax + tax_amt`); default `0`. |
| `lead_time_days` | `Int @db.Integer` | Yes | Vendor-quoted lead time in days; default `0`. |
| `is_active` | `Boolean` | Yes | Whether the row is active; default `true`. |
| `description` | `String @db.VarChar` | Yes | Free-text description. |
| `note` | `String @db.VarChar` | Yes | Free-text note. |
| `comment` | `String @db.VarChar` | Yes | Per-row comment. |
| `info` | `Json @db.JsonB` | Yes | Extension bag (per-row validation result, quality flag); default `{}`. |
| `dimension` | `Json @db.JsonB` | Yes | Per-row cost dimensions; default `[]`. |
| `doc_version` | `Int @db.Integer` | No | Optimistic-concurrency version; default `0`. |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | (standard audit) | Yes | Standard audit columns. |

**Constraints:** `@id` on `id`. FKs: `pricelist_id → tb_pricelist.id` (`NoAction`); `product_id → tb_product.id` (`NoAction`, required); `unit_id → tb_unit.id` (`NoAction`); `tax_profile_id → tb_tax_profile.id` (`NoAction`). Back-relations to `tb_purchase_request_detail` (PR detail can reference a specific pricelist row as the price source) and `tb_pricelist_detail_comment`.
**Indexes:** `@@unique([pricelist_id, product_id, unit_id, moq_qty, deleted_at])` as `pricelist_detail_pricelist_id_product_id_unit_id_moqqty_u` — note `moq_qty` is part of the uniqueness, supporting the multi-MOQ-tier-per-product pattern; `@@index([pricelist_id, product_id])`.

### 2.10 tb_pricelist_comment / tb_pricelist_detail_comment

Activity-log surfaces on the pricelist header and per-row. Same shape as the template comment tables — `id`, FK to parent, `type` enum (`user` / `system`), `user_id`, `message`, `attachments`, and the standard audit columns.

| Table | Parent FK | Purpose |
| ----- | --------- | ------- |
| `tb_pricelist_comment` | `pricelist_id → tb_pricelist.id` | Pricelist-header activity log: created, vendor saved draft, vendor submitted, validation result, purchaser approved / rejected, status transitions. |
| `tb_pricelist_detail_comment` | `pricelist_detail_id → tb_pricelist_detail.id` | Per-row activity log: row edited by purchaser, validation warning attached, preferred-vendor flag toggled, deviation against historical price logged. |

## 3. Relationships

```
tb_pricelist_template ──1──*──► tb_pricelist_template_detail ──1──*──► tb_pricelist_template_detail_comment
        │  1                       │
        │  *  (back-relation)      │
        │                          └──► tb_product            (required, product_id)
        ▼
tb_pricelist_template_comment

tb_pricelist_template ──1──*──► tb_request_for_pricing ──1──*──► tb_request_for_pricing_detail
                                       │  1                            │  *
                                       ▼  *                             ├──► tb_vendor              (required, vendor_id)
                                tb_request_for_pricing_comment          ├──► tb_pricelist           (optional, pricelist_id — populated on first save)
                                                                        └──► tb_request_for_pricing_detail_comment

tb_pricelist ──1──*──► tb_pricelist_detail ──1──*──► tb_pricelist_detail_comment
    │  1                  │
    ▼  *                  ├──► tb_product             (required, product_id)
tb_pricelist_comment      ├──► tb_unit                (unit_id)
                          ├──► tb_tax_profile         (tax_profile_id)
                          └──► tb_purchase_request_detail   (back-relation — PR detail references pricelist row as price source)

tb_pricelist  (header-level FKs)
    ├──► tb_vendor              (vendor_id)
    └──► tb_currency            (currency_id)

tb_pricelist_template (header-level FKs)
    └──► tb_currency            (currency_id)
```

Notes:

- **Template → request-for-pricing** is 1-to-many. A single template can drive many campaigns over time (quarterly cycles, ad-hoc surveys, event-based collections). The campaign carries the cohort, schedule, and email-template; the template carries the product list and unit/MOQ shape.
- **Request-for-pricing → detail** is 1-to-many. Each detail row is one vendor's invitation — unique by `(request_for_pricing_id, vendor_id, deleted_at)`. The detail row carries the cryptographic `pricelist_url_token` and the FK to `tb_pricelist` (nullable until the vendor first saves).
- **Request-for-pricing-detail → pricelist** is 1-to-1 in practice: each invitation produces at most one vendor pricelist; the FK lives on the invitation side and is populated by the application on first save.
- **Pricelist → detail** is 1-to-many. The detail row supports multiple MOQ tiers per `(pricelist, product, unit)` because `moq_qty` is part of the uniqueness key — this is the schema mechanism for the "MOQ 1 / 50 / 100" pricing pattern.
- **Pricelist-detail → PR detail** is 1-to-many (back-relation): a single pricelist row can be the price source for many PR detail rows. The PR side carries the FK `tb_purchase_request_detail.pricelist_detail_id`; the snapshot of the price at PR creation lives on the PR row.
- **Header → comment** and **detail → comment** are both 1-to-many on every tier. Comment tables are the persistent record of activity; carmen/docs's "campaign analytics" / "invitation tracking" structures (response rate, open rate, IP audit) are application-layer rollups of these comments plus `info` JSON.
- **No campaign-status table.** Carmen/docs's `CollectionCampaign.status` enum (`draft`, `active`, `paused`, `completed`, `cancelled`) is **not** a Prisma column on `tb_request_for_pricing`; the application derives it from `start_date`, `end_date`, and the detail-side `pricelist.status` counts. Section 5 catalogues this divergence.
- All `@relation` FK declarations use `onDelete: NoAction, onUpdate: NoAction`, so referential integrity is preserved by application-level soft-delete (`deleted_at`) rather than cascade.

## 4. Enums

- **`enum_pricelist_template_status`** (`tb_pricelist_template.status`): `draft`, `active`, `inactive`. `draft` is the editable working state; `active` is the operational state where the template can drive new request-for-pricing campaigns; `inactive` is the archived state (template still queryable, but not selectable for new campaigns).
- **`enum_pricelist_status`** (`tb_pricelist.status`): `draft`, `active`, `inactive`, `expired`. `draft` covers the vendor-edit window (auto-save) before the vendor clicks Submit; `active` is the post-approval state where the pricelist is the reference for PR / PO / GRN; `inactive` is the post-approval suspended state (admin can re-activate); `expired` is the auto-transition once `effective_to_date` is in the past. The carmen/docs additional states `submitted` / `under-review` / `approved` / `rejected` are **not** Prisma enum values — the application infers them from `status`, `submitted_at`, and comment-table audit entries.
- **`pricelist_submission_method`** (`tb_pricelist.submission_method`): `online`, `email`, `portal`, `manual`. `online` is direct portal entry; `email` covers Excel-template emailed to purchasing and uploaded by staff; `portal` covers Excel-template drag-and-dropped on the portal; `manual` covers direct purchaser-side data entry without any vendor portal round-trip (e.g., for a vendor that refuses to use the portal).
- **`enum_pricelist_compare_type`** (declared in the schema and referenced elsewhere — for example PR line `pricelist_type`): `automatic`, `manual_select`, `manual_input`. Distinguishes how a PR line acquires its pricelist reference — auto-resolution from the preferred-vendor rule, manual selection from a candidate list, or free-form manual input.
- **`enum_comment_type`** (shared module-wide): `user` (human-authored comment), `system` (auto-generated activity-log entry written by the workflow / portal layer). Used by every comment table in this module.

## 5. Divergences from carmen/docs

The carmen/docs design under `vendor-pricelist-management/` (`design.md`, `requirements.md`, `VENDOR_MANAGEMENT_TECHNICAL_SPECIFICATION.md`, `price-assignment-workflow-documentation.md`) describes a much richer entity set than Prisma actually carries today. The table below captures material differences that downstream documentation must reconcile; treat Prisma as canonical for entities and fields, and carmen/docs as canonical for workflow / rule semantics that the application layer enforces on top of the leaner schema.

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|
| 1 | "Campaign" object name | `CollectionCampaign` (TypeScript interface in design.md § Data Models) | `tb_request_for_pricing` (no "campaign" anywhere in the schema). | Document both names. Carmen-wiki uses "Request-for-Pricing" for the entity name and "Campaign" only as a synonym in narrative prose. |
| 2 | Campaign status enum | `'draft' \| 'active' \| 'paused' \| 'completed' \| 'cancelled'` | No Prisma column or enum for campaign status on `tb_request_for_pricing`. | The application derives status from `start_date`, `end_date`, and the count / status of submitted pricelists on its detail rows. Document the derivation rule in `02-business-rules.md`. |
| 3 | Invitation object name | `VendorInvitation` (design.md § Data Models) | `tb_request_for_pricing_detail`. | Same as item 1 — use the Prisma name in entity references, "invitation" in narrative. |
| 4 | Invitation submission status | `'pending' \| 'in-progress' \| 'submitted' \| 'approved' \| 'expired'` | No Prisma column. Derived from `tb_pricelist.status`, `tb_pricelist.submitted_at`, and the campaign's `end_date`. | Document the derivation rule. The transition `pending → in-progress` fires when the vendor first opens the portal (recorded as a `system` comment); `in-progress → submitted` when `tb_pricelist.submitted_at` is written; `submitted → approved` when `tb_pricelist.status` becomes `active`; `* → expired` when `end_date` passes with no submission. |
| 5 | Pricelist status enum | `'draft' \| 'submitted' \| 'under-review' \| 'approved' \| 'rejected'` (design.md) | `enum_pricelist_status = { draft, active, inactive, expired }`. | Two-enum mapping: carmen/docs `submitted` and `under-review` are both Prisma `draft` (with `submitted_at IS NOT NULL` distinguishing "submitted but unapproved"); carmen/docs `approved` is Prisma `active`; carmen/docs `rejected` is Prisma `draft` + a `system` rejection comment in `tb_pricelist_comment`. Document the mapping in `02-business-rules.md`. |
| 6 | Portal access telemetry | Per-invitation `portalAccess { firstAccessAt, lastAccessAt, sessionCount, ipAddresses[] }`; per-invitation `emailDetails { sentAt, deliveredAt, openedAt, clickedAt }` (design.md). | No dedicated columns. The data is written to `tb_request_for_pricing_detail_comment` as `system` entries with attachments / message JSON, and surfaced via `info` JSON on the parent row. | Document the telemetry-via-comments pattern in `02-business-rules.md`. Where stronger guarantees are needed (e.g., analytics queries), a dedicated table is on the roadmap. |
| 7 | Quality score / validation results | Per-pricelist `qualityScore` numeric, `validationResults` structured object (design.md § Data Models). | No dedicated columns on `tb_pricelist`; the values live in `info` JSON. | Document the JSON shape and the validator's contract for writing into `info` in `02-business-rules.md`. The Prisma model is intentionally schemaless on this axis to allow the validator to evolve. |
| 8 | MOQ-tier conversion factor | "Conversion factor (e.g., 1 Box = 50 Each)" per MOQ tier (design.md). | `tb_pricelist_detail` has `unit_id` and `moq_qty` but no separate `conversion_factor` column. | The conversion factor is resolved at lookup time from `tb_unit` (the unit's `conversion_factor` to base UoM), not stored on the pricelist row. The carmen/docs claim of a per-row conversion factor is application-layer rendering, not a schema column. |
| 9 | Effective unit price per base unit | "Effective unit price per base unit" displayed on every MOQ tier (design.md). | Not a stored column. Computed on the fly as `price ÷ unit.conversion_factor`. | Document the formula in `02-business-rules.md` § Calculation Rules. |
| 10 | "Preferred vendor" linkage | Set "per product (or per category)" with a dedicated preferred-vendor table (design.md § Pre-Assignment Setup). | One `is_preferred` boolean on `tb_pricelist_detail` per row; no separate preferred-vendor table. | Document the per-row pattern. The carmen/docs cross-category and rule-based mechanisms are application-layer derivations from `is_preferred` + the `tb_business_rules` registry; no schema-level "preferred-vendor-per-product" table exists yet. |
| 11 | Email / portal token security policy | "Cryptographically secure tokens with configurable expiration times and access restrictions"; "IP address tracking"; "session timeout controls, concurrent session limits, suspicious activity detection" (requirements.md § Requirement 28). | `tb_request_for_pricing_detail.pricelist_url_token` (one column); `tb_pricelist.url_token` (denormalised copy). | The richer token-policy surface (expiration, IP restrictions, concurrent sessions) is enforced by the application's portal middleware, not by the schema. Document in `02-business-rules.md` § Authorization Rules. |
| 12 | Audit history table | "Complete audit trail with user attribution and timestamps" implied to be a dedicated table (requirements.md § Requirement 19). | No dedicated audit-trail table for this module beyond the comment tables and the shared `tb_activity` cross-module audit table. | Same pattern as other modules: comment tables + `tb_activity` are the persistence; carmen/docs's prose description aligns with this once `tb_activity` is documented. |

## 6. References

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — all ten vendor-pricelist models and the three module-local enums (`enum_pricelist_template_status`, `enum_pricelist_status`, `pricelist_submission_method`), plus the shared `enum_pricelist_compare_type` and `enum_comment_type`.
- **Secondary (concept cross-check):** `../carmen/docs/vendor-pricelist-management/` — eight design / requirements documents:
  - `design.md` — 6-phase architecture, component breakdown, TypeScript data-model interfaces (used as the carmen/docs basis for the divergence table in Section 5).
  - `requirements.md` — 30+ functional requirements covering vendor CRUD, template setup, campaign management, portal UX, multi-currency, validation, audit.
  - `price-assignment-workflow-documentation.md` — business rules engine, rule categories, vendor eligibility, real-time assignment logic (foundational for `02-business-rules.md` § Cross-Module Rules).
  - `VENDOR_MANAGEMENT_TECHNICAL_SPECIFICATION.md` — technical spec covering vendor CRUD, RBAC, integration architecture.
  - `VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md` — vendor portal features and security posture.
  - `pricelist-management-navigation-summary.md` — UI navigation tree for the module.
  - `vendor-product-assignments-summary.md` — vendor↔product assignment patterns underpinning the preferred-vendor flag on `tb_pricelist_detail`.
  - `tasks.md` — implementation task list.
- **Sibling reference:** `en/purchase-request/01-data-model.md` — `tb_purchase_request_detail` carries the back-reference `pricelist_detail_id` into this module; documented there, not duplicated here.
- Related modules: [[product]] (every pricelist detail row references a product), [[purchase-request]] (PR line defaults price from the active pricelist), [[purchase-order]] (PO snapshots pricelist price at PR-to-PO conversion), [[good-receive-note]] (GRN price-variance check runs against the active pricelist).
