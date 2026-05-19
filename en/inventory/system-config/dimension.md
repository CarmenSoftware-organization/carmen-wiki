---
title: Dimension
description: User-defined custom fields (cost centre, project code, etc.) that can be attached to any document or master record, with per-entity display rules.
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, dimension, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Dimension

> **At a Glance**
> **Owner:** Sysadmin &nbsp;·&nbsp; **Table:** `tb_dimension` (+ `tb_dimension_display_in`) &nbsp;·&nbsp; **Used by:** PR / PO / GRN / SR / IA / inventory / master records &nbsp;·&nbsp; User-extensible custom-field system — cost-centre, project code, GL override.

## 1. What & Who

Dimensions are the **user-extensible custom-field system**. A dimension defines a named tag (`cost_centre`, `project_code`, `gl_account_override`, `event_name`, …) with a typed value space, default value, and a list of *places it should appear* — header of PR, detail of GRN, the vendor master, etc. End-user values are stored in the `dimension` JSONB column that every transactional table and most master records carry.

The two-table split keeps the catalogue clean. `tb_dimension` is the *definition*. `tb_dimension_display_in` is the *display matrix* — one row per place the dimension should appear (with per-place override defaults). This is how Carmen supports cost-centre tagging on PR headers and IA detail lines without hardcoded columns.

**Maintained by** Sysadmin. **Read by** every form that renders dimension fields, every cost-allocation report.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Define a dimension | System Config → Dimensions → New | Set key, type, optional default value |
| Enable a dimension on a place | Dimension edit → display-in matrix | Checkbox grid against 24 enum values |
| Curate `lookup` allowed values | Dimension edit → `value` editor | Required for `lookup` / `lookup_dataset` |
| Override default per place | Display-in row → `default_value` | Wins over top-level dimension default |
| Retire a dimension | Set `is_active = false` | Hides from new forms; existing values remain |
| Audit dimension changes | [reporting-audit/activity](/en/inventory/reporting-audit/activity) log | `entity_type = dimension` |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Key already exists" | Duplicate among non-deleted | Pick different key or reactivate existing |
| "Value not in catalogue" | `lookup` value not in `value` JSON | Add to catalogue or pick existing |
| Cannot hard-delete dimension | Documents have non-empty values for the key | Set `is_active = false` instead |
| Field missing from new form | `display_in` row missing or removed | Add row in display-in matrix |
| Type mismatch on save | Document value violates `type` | Form-side validation should reject earlier |

## 4. Edge Cases

- **Snapshot semantics.** Document `dimension` JSON arrays store values at write-time; later catalogue edits do not retro-edit historical documents.
- **Place removal** hides the field from new documents but does not strip persisted values.
- **Default cascade.** Resolution at form-render: per-place `default_value` → top-level `default_value` → empty.
- **Master-record tagging.** Tagging vendor / location / currency lets transactional docs inherit dimension defaults.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_dimension`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `key` | `String @db.VarChar` | No | Programmatic key (e.g. `cost_centre`). Stored verbatim in document `dimension` arrays. |
| `type` | `enum_dimension_type` | No | `string`, `number`, `boolean`, `date`, `datetime`, `json`, `dataset`, `lookup`, `lookup_dataset`. |
| `value` | `Json? @db.JsonB` | Yes | Catalogue / allowed-values list. |
| `description` / `note` | `String?` | Yes | Free text. |
| `default_value` | `Json? @db.JsonB` | Yes | Top-level default. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `info` | `Json? @db.JsonB` | Yes | Free-form metadata. |
| `doc_version` | `Int` | No | Optimistic-concurrency token. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([key, deleted_at])`. Index on `[key]`.

### 5.2 `tb_dimension_display_in`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `dimension_id` | `String @db.Uuid` | No | FK to `tb_dimension.id`. |
| `display_in` | `enum_dimension_display_in` | No | Where the dimension shows up. |
| `default_value` | `Json? @db.JsonB` | Yes | Per-place override. |
| `note` / `info` / `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([dimension_id, display_in, deleted_at])`. Index on `[dimension_id, display_in]`. FK `onDelete: NoAction`.

**`enum_dimension_display_in`:** `currency`, `exchange_rate`, `delivery_point`, `department`, `product_category`, `product_sub_category`, `product_item_group`, `product`, `location`, `vendor`, `pricelist`, `unit`, `purchase_request_header`, `purchase_request_detail`, `purchase_order_header`, `purchase_order_detail`, `goods_received_note_header`, `goods_received_note_detail`, `transfer_header`, `transfer_detail`, `stock_in_header`, `stock_in_detail`, `stock_out_header`, `stock_out_detail`.

## 6. Business Rules

- **Uniqueness.** `key` unique among non-deleted; each `(dimension_id, display_in)` unique.
- **Type validation.** Document write validates against dimension's `type`; `lookup` / `lookup_dataset` checked against `value` catalogue.
- **Default cascade.** Per-place → top-level → empty.
- **Deletion guards.** Hard-delete blocked if any document holds a non-empty value for the key; inactivate instead.
- **Place removal** hides from new forms; persisted values remain.
- **Snapshot semantics.** Document values are write-time snapshots — no retro-edit.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order) — header + detail tagging.
- [good-receive-note](/en/inventory/good-receive-note) — carries cost-centre allocation forward.
- [store-requisition](/en/inventory/store-requisition) — issue dimensions drive cost allocation.
- [inventory-adjustment](/en/inventory/inventory-adjustment) — stock-in / stock-out tagging.
- [inventory](/en/inventory/inventory) — transfer tagging.
- [master-data/vendor](/en/inventory/master-data/vendor), [master-data/location](/en/inventory/master-data/location), [master-data/currency](/en/inventory/master-data/currency), [product](/en/inventory/product) — master-record tagging cascades defaults to transactional docs.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_dimension` (lines ~4608-4635), `tb_dimension_display_in` (lines ~4671-4692), enums (lines ~115-185).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/dimension/`.
