---
title: Adjustment Type
description: Coded reasons for stock-in / stock-out adjustments — used by the inventory-adjustment module's manual postings; physical count and spot check do not set it.
published: true
date: 2026-07-15T21:47:09.000Z
tags: master-data, adjustment-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Adjustment Type

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_adjustment_type` &nbsp;·&nbsp; **Used by:** inventory-adjustment's manual Stock-In / Stock-Out forms only — nullable FK, left `null` by physical count and never touched by spot check &nbsp;·&nbsp; Coded reason for a manually-entered stock-in / stock-out movement.

![Adjustment Type screen](/screenshots/master-data/adjustment-type.png)

## 1. What & Who

Adjustment types classify *why* a stock balance moves up or down — write-off, write-on, spoilage, theft, transfer error, etc. `adjustment_type_id` on `tb_stock_in` / `tb_stock_out` is **nullable**, and in practice it is only ever populated by the [inventory-adjustment](/en/inventory/inventory-adjustment) module's own manual Stock-In / Stock-Out forms, where picking a reason is required. The `type` discriminator (`stock_in` / `stock_out`) lets the catalogue be filtered by direction there.

**Not a universal posting reason (confirmed this pass).** [physical-count](/en/inventory/physical-count)'s variance rollup creates `tb_stock_in`/`tb_stock_out` rows directly at submit time but never sets `adjustment_type_id` — it stays `null` on every row that module creates. [spot-check](/en/inventory/spot-check) is simpler still: its `submit()` does not create any `tb_stock_in`/`tb_stock_out` row at all, so it never touches this table in any way. Only inventory-adjustment's own postings carry a real reason code.

**Maintained by** Product Admin. **Read by** any developer or tester working on adjustments, physical count, or spot check posting paths.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a new reason | Configuration → Master Data → Adjustment Type → **New** | Set `code`, `name`, and `type` (`stock_in` or `stock_out`) |
| Deactivate a reason | Same screen → toggle `is_active` | Historical rows still resolve the name; hidden from new pickers |
| Edit description | Edit dialog | `code`, `name`, `type` should not change after first use |
| Check which reason a posting used | Open the stock-in/out record, look at the reason field | Snapshot via FK |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code already in use" | Duplicate `code` on a non-deleted row | Pick a different code or reactivate the existing row |
| "Type required" | Form submitted without `stock_in` / `stock_out` | Pick the direction — the UI filters by it |
| **Unconfirmed** — no delete guard or type-lock found | A direct read of `adjustment-type.service.ts`'s `delete()` and `update()` this pass found **no** check for existing stock-in/out references before soft-delete, and **no** check preventing `type` from being changed on `update()` — `...data` is spread straight into the Prisma update with only a code-uniqueness check. A prior version of this page asserted both as enforced server errors | Treat "cannot delete — referenced by postings" and "type cannot be changed" as **not enforced** until re-verified; inactivating or retyping a reason already in use will currently succeed |

## 4. Edge Cases

- **Direction flip after use is possible today.** No code blocks it — `update()` accepts a new `type` on an already-referenced row. This would corrupt direction-based reporting for existing postings; treat the prior "the system rejects it" claim as unconfirmed.
- **Deletion of a referenced reason currently succeeds.** `delete()` is an unconditional soft-delete (`is_active: false` + `deleted_at`) with no FK-reference check — historical rows still resolve the name via the (soft-deleted) FK either way.
- **Direction filtering** is at the picker — stock-in screens never see `stock_out` rows and vice versa.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_adjustment_type`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short code (e.g. `SPOIL`, `THEFT`, `WO`). |
| `name` | `String @db.VarChar` | No | Display name. |
| `type` | `enum_adjustment_type` | No | `stock_in` or `stock_out`. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, deleted_at])` map `AT1_code_u`. Index on `code`. Reverse relations to `tb_stock_in` and `tb_stock_out`.

`enum_adjustment_type` values: `stock_in`, `stock_out` (user-facing — appear in this picker), plus `eop_in`, `eop_out` (system-reserved for the period-end rollforward engine — not surfaced here). See [inventory-adjustment/01-data-model](/en/inventory/inventory-adjustment/01-data-model) § 4 for the full enum.

## 6. Business Rules

- **Uniqueness.** `code` is unique among non-deleted rows (DB-enforced).
- **Deletion guards — unconfirmed.** No reference check was found in `delete()`; soft-delete succeeds unconditionally even when stock-in/out rows point to the reason.
- **Validation.** `code`, `name`, and `type` are required on create. `update()` does not block changing `type` after first use — confirmed absent, not just unconfirmed.
- **Lifecycle.** Inactive reasons stay readable on historical adjustments; hidden from new-adjustment pickers.
- **Direction filtering.** UI pickers filter by `type` — the discriminator never needs re-filtering downstream.

## 7. Cross-References

- [inventory-adjustment](/en/inventory/inventory-adjustment) — every manual Stock-In / Stock-Out line carries an adjustment-type FK; the only module that actually sets it.
- [physical-count](/en/inventory/physical-count) — its variance rollup creates `tb_stock_in`/`tb_stock_out` rows directly but does **not** set `adjustment_type_id` (confirmed `null` on every row it creates) — no reason code, no link back to this table.
- [spot-check](/en/inventory/spot-check) — its `submit()` does not create `tb_stock_in`/`tb_stock_out` rows at all, so it never references this table.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_adjustment_type` (lines ~2807-2833), `enum_adjustment_type` (lines ~2800-2805).
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/adjustment-type/`.
