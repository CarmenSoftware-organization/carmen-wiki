---
title: Adjustment Type
description: Coded reasons for stock-in / stock-out adjustments — used by inventory adjustments, physical count, and spot check to explain variance.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, adjustment-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Adjustment Type

## 1. Purpose

Adjustment types classify *why* a stock balance is being adjusted up or down: write-off, write-on, spoilage, theft, transfer-in error, count variance, etc. Every stock-in (`tb_stock_in`) and stock-out (`tb_stock_out`) record must carry an adjustment type, and downstream variance reports group by it so the controller can spot patterns (e.g. recurring spoilage in a specific location).

The `type` discriminator (`STOCK_IN` / `STOCK_OUT`) lets the same catalogue be filtered by direction in the UI — a stock-out screen does not need to offer write-on reasons.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_adjustment_type`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code (e.g. `SPOIL`, `THEFT`, `WO`). |
| `name` | `String @db.VarChar` | No | Display name. |
| `type` | `enum_adjustment_type` | No | `STOCK_IN` or `STOCK_OUT`. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, deleted_at])` map `AT1_code_u`. Index on `code`. Reverse relations to `tb_stock_in` and `tb_stock_out`.

`enum_adjustment_type` values: `STOCK_IN`, `STOCK_OUT`.

## 3. Usage / Cross-References

- [[inventory-adjustment]] — every adjustment line carries an adjustment-type FK explaining the reason.
- [[physical-count]] — variance lines that resolve to write-on / write-off post against an adjustment type.
- [[spot-check]] — spot-check variances follow the same posting path.

## 4. Configuration UI

Managed by **Product Admin** under the Master Data area. List screen plus an edit dialog (code, name, type, active).

## 5. Business Rules

- **Uniqueness.** `code` is unique among non-deleted rows (DB-enforced).
- **Deletion guards.** An adjustment type referenced by any posted stock-in/out cannot be hard-deleted. Inactivate instead.
- **Validation.** `code`, `name`, and `type` are required. `type` cannot be flipped after the row has been used (would corrupt historical reporting).
- **Lifecycle.** Inactive types stay readable on historical adjustments but are hidden from new-adjustment pickers.
- **Direction filtering.** UI for stock-in posting only shows `type = STOCK_IN` rows; stock-out only shows `STOCK_OUT`. The discriminator should never need to be re-filtered downstream.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_adjustment_type` (lines ~2569-2594), `enum_adjustment_type` (lines ~2564-2567).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/adjustment-type/`.
- **Cross-module:** see Section 3.
