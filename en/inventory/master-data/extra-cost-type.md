---
title: Extra Cost Type
description: Catalogue of GRN landed-cost categories (freight, duty, handling) with per-instance allocation modes — since 2026-09-10 the GRN ledger really spreads the total into cost-layer extra_cost_amount.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: master-data, extra-cost-type, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Extra Cost Type

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Tables:** `tb_extra_cost_type` (catalogue) + `tb_extra_cost` (per-GRN instance) &nbsp;·&nbsp; **Used by:** GRN landed-cost allocation &nbsp;·&nbsp; Categories like Freight / Duty / Handling with `by_value` / `by_qty` / `manual` allocation modes.

![Extra Cost Type screen](/screenshots/master-data/extra-cost-type.png)

## 1. What & Who

**Extra costs** are the freight, duty, handling, and other **landed-cost** components allocated onto received goods so the **unit cost in inventory** reflects the *delivered* cost, not just the invoice line. `tb_extra_cost_type` holds the named categories (`Freight`, `Customs Duty`, `Brokerage`); `tb_extra_cost` is a per-GRN instance with a chosen **allocation mode** (`by_value`, `by_qty`, or `manual`).

`by_value` and `by_qty` are the two allocation-mode labels a user can pick in the current GRN form; `manual` is a third value the enum and schema permit but the picker never offers. **Maintained by** Product Admin (catalogue) and GRN users (instances). **Read by** the GRN ledger builder at commit time.

**Allocation is live since 2026-09-10 (corrected this pass).** The 2026-07 version of this page reported — correctly at the time — that `allocate_extra_cost_type` was a tag with no computational effect. Backend commit "GRN FOC to stock + extra cost into landed cost" (2026-09-10) changed that: `apps/micro-business/src/inventory/good-received-note/good-received-note.extra-cost.ts` (`allocateExtraCost`) now spreads the **sum of every `tb_extra_cost_detail.amount` on the GRN** across the receipt lines that actually put stock on hand, and `good-received-note.ledger.ts:105-133` writes each line's share (converted to base currency with the GRN's `exchange_rate`) into `base_extra_cost_amount`, which lands in the new cost-layer column `tb_inventory_transaction_cost_layer.extra_cost_amount` (`20260910130000_add_cost_layer_extra_cost`). The landed unit cost the costing engine averages is `base_net_amount + base_extra_cost_amount` (`inventory-transaction.service.ts:91`). What each cost line's typed `amount` means is therefore "this much of the total", and what the header mode means is "how the total is split across product lines":

| `allocate_extra_cost_type` | What the code does (`allocateExtraCost`) |
| --- | --- |
| `by_qty` | **Equal share per receiving line** — every line with `stock_qty > 0` gets `total / n`, regardless of how much it received. (The name suggests proportional-to-quantity; the code is an even split — weights are `1` per line.) |
| `by_value` | **Weighted by units received** — weights are each line's `stock_qty`. (The name suggests proportional-to-value; the code weights by quantity, not by amount.) |
| `manual` / `null` | Nothing is allocated; `extra_cost_amount` stays `0`. The code comment says a per-line manual-share input "does not exist yet". |

Lines that receive nothing (`stock_qty = 0`) never take a share, so an all-FOC or zero-qty line cannot strand money or divide by zero. When historical data has more than one `tb_extra_cost` header on a GRN, all their detail amounts are summed and spread under the **oldest** header's mode (the one `findOne` shows).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a cost type | Configuration → Master Data → Extra Cost Type → **New** | Required: `name` |
| Deactivate a type | Toggle `is_active` | Hidden from new GRNs; historical GRNs unaffected |
| Attach to GRN | GRN edit screen → **Extra Costs** section | Creates a `tb_extra_cost` header (one per GRN) plus one `tb_extra_cost_detail` row per added cost line |
| Pick an allocation-mode label | Same screen → mode dropdown | Only `by_qty` / `by_value` are offered (`by_qty` is the form default); `manual` exists in the schema but is not a picker option |
| Enter a cost-line amount | Same screen → **Add Cost** → `amount` field per row | A plain manually-typed number per cost line (freight ฿1,200, duty ฿300, …). The *sum* of these lines is what the header mode spreads across product lines when the ledger is built — the split itself is never shown or edited on the form |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already in use" | Duplicate `name` on a non-deleted row | Pick a different name |
| **Unconfirmed** — no delete guard found | `extra_cost_type.service.ts`'s `delete()` is an unconditional soft-delete with no check for existing `tb_extra_cost_detail` references | A prior version of this page asserted "cannot delete — referenced by GRN extra-cost detail" as an enforced error; treat it as **not enforced** until re-verified |
| **Unconfirmed** — no reconciliation or posted-GRN lock found | A prior version of this page asserted "missing allocation amount," "allocated sum doesn't equal parent," and "cannot change allocation on a posted GRN" as enforced errors. No sum-reconciliation check exists because there is nothing to reconcile — the split is computed, not entered (`splitByWeight` distributes rounding so the shares always add up to the total). Any edit restriction comes from the parent GRN's own `doc_status` gate (saved / committed — see [good-receive-note](/en/inventory/good-receive-note)), not from anything specific to extra costs | Treat these three messages as not applicable / not enforced |

## 4. Edge Cases

- **The form still shows no allocation.** The mode `Select` and the per-row `amount` `Input` in `grn-extra-cost-fields.tsx` remain independent fields; the per-product split is computed only when the GRN ledger is built (see [good-receive-note](/en/inventory/good-receive-note) for the save / commit timing), so a tester cannot see the share on the GRN screen — inspect `tb_inventory_transaction_cost_layer.extra_cost_amount` (or the stock card's unit cost) instead.
- **Mode names are misleading.** `by_qty` is an even split per line and `by_value` weights by `stock_qty` — neither uses line value. Test expectations must follow the code, not the label.
- **`manual` is schema-only.** The Prisma enum and DTOs accept `manual` as a third `allocate_extra_cost_type` value, but the GRN form's dropdown hard-codes only `by_qty` and `by_value` as options — `manual` is unreachable through the UI.
- **Inactive types** stay readable on historical GRNs.
- **Costing impact — confirmed.** `extra_cost_amount` on the inbound cost layer is included in the layer's cost (`base_net_amount + base_extra_cost_amount`), so AVG and FIFO unit costs both carry landed cost from the moment the GRN ledger rows are written (save / commit timing per the GRN module). A GRN posted before 2026-09-10 has `extra_cost_amount = 0` on its layers (column default) and is **not** back-filled.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_extra_cost_type`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String? @db.VarChar` | Yes | Display name (e.g. `Freight`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `info`, `dimension`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `extra_cost_type_name_u`. Index on `name`. Reverse relation to `tb_extra_cost_detail`.

### 5.2 `tb_extra_cost`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String? @db.VarChar` | Yes | Free-text label. |
| `good_received_note_id` | `String? @db.Uuid` | Yes | FK to `tb_good_received_note`. |
| `allocate_extra_cost_type` | `enum_allocate_extra_cost_type?` | Yes | `manual`, `by_value`, or `by_qty`. |
| `description`, `note` | `String?` | Yes | Free text. |
| `info`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** index on `name` (`extra_cost_name_idx`). FK to `tb_good_received_note` `onDelete: NoAction`. Reverse relations to `tb_extra_cost_detail` and `tb_extra_cost_comment`. (`tb_extra_cost_detail` carries the per-line breakdown including the FK to `tb_extra_cost_type`.)

`enum_allocate_extra_cost_type` values: `manual`, `by_value`, `by_qty`.

## 6. Business Rules

- **Uniqueness.** `tb_extra_cost_type.name` unique among non-deleted rows.
- **Deletion guards — unconfirmed.** No reference check was found in `delete()`; soft-delete succeeds unconditionally even with existing `tb_extra_cost_detail` references.
- **Validation.** No code requires every cost line to carry an amount; a zero-amount line simply contributes nothing to the total. `allocateExtraCost` skips totals within `AMOUNT_EPSILON` of zero.
- **Allocation invariants — confirmed.** Shares are produced by `splitByWeight(total, weights)` over the receiving lines only; the shares sum to the total by construction. Mode semantics: `by_qty` → equal weights, `by_value` → `stock_qty` weights, `manual` → no allocation (`good-received-note.extra-cost.ts:41-60`).
- **Default sort.** `GET /extra-cost-types` with no `?sort=` returns `name:asc, id:asc` (`extra_cost_type.service.ts`, `withDefaultSort`, 2026-09-13).
- **Lifecycle.** Inactive types readable on historical GRNs; hidden from new GRN pickers.
- **Re-allocation — unconfirmed.** No mode-specific edit lock was found; any restriction on editing extra costs after posting comes from the GRN's own general `doc_status` gate, not from this entity.

## 7. Cross-References

- [good-receive-note](/en/inventory/good-receive-note) — sole consumer. Each GRN has one `tb_extra_cost` header holding multiple `tb_extra_cost_detail` lines, each tagged with an extra-cost type and a manually-entered amount.
- [costing](/en/inventory/costing) — landed unit cost includes each layer's `extra_cost_amount` (`inventory-transaction.service.ts:91`); see [inventory/01-data-model](/en/inventory/inventory/01-data-model) for the cost-layer columns.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_extra_cost_type` (line ~5811), `tb_extra_cost` (~5675), `enum_allocate_extra_cost_type` (~109).
- **Migration:** `20260910130000_add_cost_layer_extra_cost` (`tb_inventory_transaction_cost_layer.extra_cost_amount DECIMAL(20,5) DEFAULT 0`).
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/good-received-note/good-received-note.extra-cost.ts` (`allocateExtraCost`), `good-received-note.ledger.ts` (`base_extra_cost_amount`), `apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.ts:91`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/030-extra-cost.spec.ts` + `docs/test-cases/gaps/030-extra-cost-gap.md`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/extra-cost-type/` (catalogue); `../carmen-inventory-frontend-react/routes/procurement/goods-receive-note/grn-extra-cost-fields.tsx` (GRN instance form).
