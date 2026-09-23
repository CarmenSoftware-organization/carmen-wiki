---
title: Inventory Adjustment — Test Scenarios — Store Keeper
description: Test cases for entering a Stock-In / Stock-Out adjustment — save a draft, commit to post, with the period-date and on-hand guards.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory-adjustment, test-scenarios, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Test Scenarios — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **Module:** [inventory-adjustment](/en/inventory/inventory-adjustment)
> **Categories:** Happy Path &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **Executable coverage:** none automated — manual catalog `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (60 cases; TC-IADJ-03xxxx new form, TC-IADJ-05xxxx items, TC-IADJ-06xxxx commit/void); see [04-test-scenarios](/en/inventory/inventory-adjustment/04-test-scenarios) § 5

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| SK-HP-01 | Stock-In draft, then commit (Average BU) | Product `P-1` at `LOC-A`, current cost `฿10.00`; `si_date` inside the current period | 1. Add Stock-In. 2. Reason (`stock_in`), location `LOC-A`. 3. Add line `P-1`, `qty = 10`; `cost_per_unit` pre-fills `฿10.00`, change to `฿12.00`. 4. **Save**. 5. **Commit** → confirm. | Step 4: `POST /stock-ins` → `draft`, `si_no` numbered from `si_date`, no ledger rows. Step 5: `PATCH /stock-ins/{id}/commit` → `completed`; one `tb_inventory_transaction` (`stock_in`), inbound layer `in_qty 10 @ ฿12.00`, lot `{LOC-A code}{YYMM}{seq4}`, `average_cost_per_unit` restamped; on-hand +10. |
| SK-HP-02 | Commit straight from a new form | Same as SK-HP-01 but click **Commit** without saving | Frontend `POST`s the draft, then commits it with the returned `doc_version`; end state identical to SK-HP-01. |
| SK-HP-03 | Stock-Out for breakage, FIFO product | FIFO BU; `P-2` at `LOC-A`: 5 @ `฿10.00` (`lot_seq_no 1`), 3 @ `฿12.00` (`lot_seq_no 2`); `so_date` inside the current period | 1. Add Stock-Out, reason (`stock_out`), `LOC-A`. 2. Line `P-2`, `qty = 6` (no cost column). 3. Save. 4. Commit. | `createFifoConsumption` consumes 5 from lot 1 and 1 from lot 2 — two outbound layers at their lot costs; `tb_stock_out_detail.cost_per_unit`/`total_cost` stay `0`; on-hand 8 → 2. |
| SK-HP-04 | Multi-line document | Two products at the same location | Add both lines, Save, Commit | One header, two detail rows, one `tb_inventory_transaction` per line at commit. |
| SK-HP-05 | Fractional quantity | Product with fractional UoM (kg) | Line `qty = 1.5` | Accepted (`qty ≥ 0`, `Decimal(20,5)`). |
| SK-HP-06 | Edit a draft | Draft from SK-HP-01 before step 5 | Open → **Edit** → change qty → **Save** | `PATCH /stock-ins/{id}/save`; `doc_version` increments; still `draft`; no ledger rows. |

## 2. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| SK-VAL-01 | Missing location | Save with `location_id` empty | Client Zod blocks; direct API → 400 `Location is required for stock in` / `…stock out`. |
| SK-VAL-02 | Negative quantity | Line `qty = -1` | Client rejects (`min 0`). |
| SK-VAL-03 | No line items | Save with zero lines | Client (`atLeastOneItem`); direct API → 400 `Stock in detail items are required`. |
| SK-VAL-04 | Unknown product id | Direct API with an unknown `product_id` | Enrichment rejects the line / `PRODUCT_NOT_FOUND` on the detail endpoints. |
| SK-VAL-05 | Negative cost on Stock-In | `cost_per_unit = -1` | Client rejects (`minZero`). |
| SK-VAL-06 | Insufficient stock on Stock-Out | Requested qty > on-hand at the location (either costing method) | **Commit** → 400 `Insufficient stock for {product} at {location}: on hand {x}, requested {y}` (`STOCK_OUT_INSUFFICIENT_STOCK`); draft survives, nothing posted. |
| SK-VAL-07 | Stock-in dated in a closed period | `si_date` before the earliest open period | Client `dateOutsidePeriod`; direct API → 422 `The stock-in date does not fall inside any open period` at create **and** at commit. |
| SK-VAL-08 | Stock-out dated outside the current period | `so_date` in a previous (even still-open) period | 422 `Stock-outs can only be dated inside the current period ({period}: {start} to {end})` at create and commit; 422 `No inventory period is open…` when nothing is open. |
| SK-VAL-09 | Blank description | Save with empty `description` | Accepted — optional. |
| SK-VAL-10 | Commit twice | Commit an already-completed document (API) | 400 `Only a draft Stock In can be committed`. |
| SK-VAL-11 | Change status through save | `PATCH /save` with `doc_status: "completed"` | 400 `doc_status cannot be changed on save — use the commit or void endpoint`. |

## 3. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| SK-EDGE-01 | Reason/direction mismatch via API | Stock-in create referencing a `stock_out`-typed reason | Not rejected server-side (enrichment only checks the row exists). |
| SK-EDGE-02 | Direct-cost location via API | `location_type = direct` | Not rejected server-side; only the picker filters. |
| SK-EDGE-03 | Cost suggestion for a new product/location pair | No prior cost data | `useProductCostByLocationQty` returns no cost; field stays empty/0 and is editable. |
| SK-EDGE-04 | `expired_at` on a stock-in line | Sent via API only | Persisted on `tb_stock_in_detail.expired_at` and returned by `GET /details`; the form has no input for it. |
| SK-EDGE-05 | Draft left over at period end | Draft dated in the period | Blocks **Start Period Close** until committed or removed. |
| SK-EDGE-06 | Stock movements after commit | Completed document | `GET /stock-ins/{id}/stock-movements` lists each posted line with lot, qty, cost and `transaction_type`. |

## 4. References

- Parent overview: [04-test-scenarios](/en/inventory/inventory-adjustment/04-test-scenarios).
- User flow: [03-user-flow-store-keeper](/en/inventory/inventory-adjustment/03-user-flow-store-keeper).
- Business rules: [02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) — `ADJ_VAL_001`–`ADJ_VAL_015`, `ADJ_CALC_001`–`ADJ_CALC_009`, `ADJ_POST_001`–`ADJ_POST_003`.
- Cross-link: [inventory](/en/inventory/inventory) — ledger-side effects of every commit; [costing](/en/inventory/costing) — FIFO/Average cost resolution.
