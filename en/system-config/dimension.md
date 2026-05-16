---
title: Dimension
description: User-defined custom fields (cost centre, project code, etc.) that can be attached to any document or master record, with per-entity display rules.
published: true
date: 2026-05-16T08:00:00.000Z
tags: system-config, dimension, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Dimension

## 1. Purpose

Dimensions are the **user-extensible custom-field system** in Carmen. A dimension defines a named tag (`cost_centre`, `project_code`, `gl_account_override`, `event_name`, etc.) with a typed value space, a default value, and a list of *places it should appear* — header of PR, detail of GRN, the vendor master, an inventory location, and so on. The end-user value is then stored in the `dimension` JSONB column that every transactional table and most master records carry.

The two-table split keeps the catalogue clean. `tb_dimension` is the *definition* — key, type, default, validation metadata. `tb_dimension_display_in` is the *display matrix* — one row per place the dimension should be rendered (and per-place override defaults). This is how Carmen supports cost-centre tagging on PR headers and inventory-adjustment detail lines while not polluting either schema with hardcoded columns.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_dimension`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `key` | `String @db.VarChar` | No | Programmatic key (e.g. `cost_centre`). Stored verbatim in document `dimension` arrays. |
| `type` | `enum_dimension_type` | No | Value type: `string`, `number`, `boolean`, `date`, `datetime`, `json`, `dataset`, `lookup`, `lookup_dataset`. |
| `value` | `Json? @db.JsonB` | Yes | Catalogue / allowed-values list. Shape depends on `type`. |
| `description` | `String? @db.VarChar` | Yes | Human description. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `default_value` | `Json? @db.JsonB` | Yes | Default value applied if no per-place default exists. |
| `is_active` | `Boolean?` | Yes | Active flag (default `true`). |
| `info` | `Json? @db.JsonB` | Yes | Free-form metadata. |
| `doc_version` | `Int` | No | Optimistic-concurrency token (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([key, deleted_at])` map `dimension_key_u`. Index on `[key]`. Reverse relations to `tb_dimension_display_in` and `tb_dimension_comment`.

### 2.2 `tb_dimension_display_in`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `dimension_id` | `String @db.Uuid` | No | FK to `tb_dimension.id`. |
| `display_in` | `enum_dimension_display_in` | No | Where this dimension shows up. See enum below. |
| `default_value` | `Json? @db.JsonB` | Yes | Per-place default override. |
| `note` / `info` | — | Mixed | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-concurrency token. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([dimension_id, display_in, deleted_at])` map `dimension_display_in_u`. Index on `[dimension_id, display_in]`. FK to `tb_dimension` with `onDelete: NoAction`.

**`enum_dimension_display_in`:** `currency`, `exchange_rate`, `delivery_point`, `department`, `product_category`, `product_sub_category`, `product_item_group`, `product`, `location`, `vendor`, `pricelist`, `unit`, `purchase_request_header`, `purchase_request_detail`, `purchase_order_header`, `purchase_order_detail`, `goods_received_note_header`, `goods_received_note_detail`, `transfer_header`, `transfer_detail`, `stock_in_header`, `stock_in_detail`, `stock_out_header`, `stock_out_detail`.

**`enum_dimension_type`:** `string`, `number`, `boolean`, `date`, `datetime`, `json`, `dataset`, `lookup`, `lookup_dataset`.

## 3. Usage / Cross-References

- [[purchase-request]] — `purchase_request_header` and `purchase_request_detail` are the most common dimension targets (cost centre, project code, event).
- [[purchase-order]] — `purchase_order_header` / `purchase_order_detail` mirror PR for procurement reporting.
- [[good-receive-note]] — `goods_received_note_header` / `goods_received_note_detail` carry the cost-centre allocation forward through receipt.
- [[store-requisition]] — issue dimensions (e.g. `event_name`, `project_code`) drive cost allocation on consumption.
- [[inventory-adjustment]] — `stock_in_header` / `stock_in_detail` / `stock_out_header` / `stock_out_detail` carry adjustment-time tagging (department, GL override).
- [[inventory]] — cost-centre allocation at issue/transfer time uses dimensions; `transfer_header` / `transfer_detail` enums are reserved for inter-location movement.
- [[master-data/vendor]], [[master-data/location]], [[master-data/currency]], [[product]] — master records can be tagged so transactional documents inherit dimension defaults.

## 4. Configuration UI

Managed by **Sysadmin** under System Configuration → Dimensions. The screen has two panes: a list of dimension definitions (CRUD on `tb_dimension`) and a *display-in matrix* (checkbox grid against the 24 enum values, editing `tb_dimension_display_in` rows). For `lookup` and `lookup_dataset` types the admin curates the allowed-value list in the dimension's `value` JSON. Per-place default overrides are edited inline.

## 5. Business Rules

- **Uniqueness.** `key` is unique among non-deleted rows. Each `(dimension_id, display_in)` row is unique — a dimension can only be enabled once per place.
- **Type validation.** When a document persists a dimension value, the application validates it against the dimension's `type`. `lookup` and `lookup_dataset` values must be a member of the catalogue in `value`.
- **Default cascade.** Resolution order at form-render time: per-place `default_value` from `tb_dimension_display_in` → top-level `default_value` from `tb_dimension` → empty.
- **Deletion guards.** A dimension with any `display_in` row enabled and at least one document containing a non-empty value for that key cannot be hard-deleted. Inactivate via `is_active = false` to hide it from new forms; existing document values remain.
- **Place removal.** Removing a `display_in` row hides the field from new documents at that place but does not strip persisted values from existing documents.
- **Snapshot semantics.** Document `dimension` JSON arrays store the value at write-time; later edits to the dimension catalogue do not retro-edit historical documents.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_dimension` (lines ~4608-4635), `tb_dimension_display_in` (lines ~4671-4692), `enum_dimension_type` (lines ~115-125), `enum_dimension_display_in` (lines ~160-185).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/dimension/`.
- **Cross-module:** see Section 3.
