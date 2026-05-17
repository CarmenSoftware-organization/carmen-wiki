---
title: Adjustment Type
description: Coded reasons for stock-in / stock-out adjustments — used by inventory adjustments, physical count, and spot check to explain variance.
published: true
date: 2026-05-17T07:28:28.000Z
tags: master-data, adjustment-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Adjustment Type

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_adjustment_type` &nbsp;·&nbsp; **Used by:** inventory adjustment / physical count / spot check &nbsp;·&nbsp; Coded reason for every stock-in / stock-out movement.

![Adjustment Type screen](/assets/screenshots/master-data/adjustment-type.png)

## 1. What & Who

Adjustment types classify *why* a stock balance moves up or down — write-off, write-on, spoilage, theft, count variance, transfer error, etc. Every `tb_stock_in` and `tb_stock_out` record carries one, and downstream variance reports group by reason so the controller can spot patterns. The `type` discriminator (`STOCK_IN` / `STOCK_OUT`) lets the catalogue be filtered by direction.

**Maintained by** Product Admin. **Read by** any developer or tester working on adjustments, physical count, or spot check posting paths.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a new reason | Configuration → Master Data → Adjustment Type → **New** | Set `code`, `name`, and `type` (`STOCK_IN` or `STOCK_OUT`) |
| Deactivate a reason | Same screen → toggle `is_active` | Historical rows still resolve the name; hidden from new pickers |
| Edit description | Edit dialog | `code`, `name`, `type` should not change after first use |
| Check which reason a posting used | Open the stock-in/out record, look at the reason field | Snapshot via FK |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code already in use" | Duplicate `code` on a non-deleted row | Pick a different code or reactivate the existing row |
| "Type required" | Form submitted without `STOCK_IN` / `STOCK_OUT` | Pick the direction — the UI filters by it |
| "Cannot delete — referenced by postings" | At least one stock-in/out record points to this reason | Inactivate instead |
| "Type cannot be changed" | Attempt to flip `STOCK_IN` ↔ `STOCK_OUT` after use | Create a new reason in the correct direction |

## 4. Edge Cases

- **Direction flip after use** corrupts historical reporting — the system rejects it.
- **Deletion of a referenced reason** is blocked; soft-delete also leaves historical rows resolvable.
- **Direction filtering** is at the picker — stock-in screens never see `STOCK_OUT` rows and vice versa.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_adjustment_type`

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

## 6. Business Rules

- **Uniqueness.** `code` is unique among non-deleted rows (DB-enforced).
- **Deletion guards.** A reason referenced by any posted stock-in/out cannot be hard-deleted — inactivate.
- **Validation.** `code`, `name`, and `type` are required. `type` cannot be flipped after first use.
- **Lifecycle.** Inactive reasons stay readable on historical adjustments; hidden from new-adjustment pickers.
- **Direction filtering.** UI pickers filter by `type` — the discriminator never needs re-filtering downstream.

## 7. Cross-References

- [[inventory-adjustment]] — every adjustment line carries an adjustment-type FK.
- [[physical-count]] — variance write-on / write-off posts against an adjustment type.
- [[spot-check]] — spot-check variances follow the same posting path.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_adjustment_type` (lines ~2569-2594), `enum_adjustment_type` (lines ~2564-2567).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/adjustment-type/`.
