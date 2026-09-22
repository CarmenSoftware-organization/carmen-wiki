---
title: Inventory — User Flow — Store Keeper
description: Store Keeper's flow within the inventory module — reading the transaction ledger to verify that source-document postings landed correctly.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory, user-flow, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **Module:** [inventory](/en/inventory/inventory) &nbsp;·&nbsp; **Surface in this module:** the **read-only** Transaction Log (`/inventory-management/transaction`, `inventory_management.view`) — verifying that GRN / SR / adjustment postings landed &nbsp;·&nbsp; **Not in this module:** authoring adjustments (lives in [inventory-adjustment](/en/inventory/inventory-adjustment)) and counting (lives in [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check))
> **Correction (2026-07-15):** the stock-in/stock-out authoring flow with threshold-based auto-approve and Controller routing previously documented here was **not backed by source** — no threshold exists anywhere in the backend, and the adjustment screens are the inventory-adjustment module's, not this one's.

## 1. Role in This Module

The **Store Keeper** persona is the operator at the floor / location level. Inside the *inventory* wiki module (transaction ledger + period-end), their surface is **read-only**: after a GRN save, an SR issue, or an inventory-adjustment completion, the Store Keeper opens the Transaction Log to confirm the movement landed — correct product, location, quantity direction, and cost. Everything they *author* lives in sibling modules:

- Manual stock-in / stock-out documents → [inventory-adjustment](/en/inventory/inventory-adjustment) (`/inventory-management/inventory-adjustment`, nav permission `inventory_management.view`). The document flow there is **Save = draft, Commit = posted** (`PATCH …/commit`, since 2026-07-30) — commit posts the inventory transaction atomically; edits are only possible at `draft`; **Void** reverses a posted document.
- Physical counts and spot checks → [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check).
- Receiving at the dock → [good-receive-note](/en/inventory/good-receive-note) (note: on an average-method business unit the ledger rows appear on GRN **save**; on a FIFO business unit they appear on **commit** — `postsInventoryAtSave`).

There is no per-location posting scope, threshold, or approval routing in this module's code; access to the ledger is gated by the single `inventory_management.view` permission.

## 2. Entry Point and Primary Flow

**Entry point:** Inventory Management → Transaction (`/inventory-management/transaction`).

**Primary flow (verify a posting, 5 steps):**

1. **Open the Transaction Log.** The list renders one row per transaction with: date, type badge (GRN / SR / SI / SO / CN), `parent_document_no`, product name(s), location(s), Qty In, Qty Out, item count, and total cost. Four summary cards sit above the grid: total transactions (with adjustment count), total inbound (units + cost), total outbound, and signed net change.
2. **Filter to the expected movement.** Search by document number / product / location name, or use the filters: date-range presets (Today / 7d / 30d / This month / custom picker), Inbound–Outbound direction, Location lookup, Category lookup, and ref-type pills (GRN / SR / SI / SO / PC).
3. **Locate the row** whose `parent_document_no` matches the source document just posted.
4. **Check direction and quantities.** Qty In is green, Qty Out red; a direct-location GRN receipt shows both legs (the receipt and the automatic offsetting issue) under the same transaction.
5. **Escalate a mismatch via a source document.** The ledger has no edit affordance — a wrong posting is corrected by a credit note (GRN-sourced) or a stock-in / stock-out in [inventory-adjustment](/en/inventory/inventory-adjustment), never by editing the row.

## 3. Decision Branches

- **Row missing after a GRN action** — check the BU costing method and which action ran: average-method BUs post on **save** (`draft → saved`) and re-post on quantity edits; FIFO BUs post only on **commit**. A GRN still at `draft` has no ledger presence either way.
- **Movement appears in "the wrong month"** — since 2026-08-31 the period stamp follows the document date (`findOpenPeriodForDate`); a stock-in dated in a closed period is rejected (`The stock-in date does not fall inside any open period`, 422) and a stock-out must be dated in the current period (`Stock-outs can only be dated inside the current period (…)`, 422). Only movements with no document date (void reversals, credit notes) fall back to the current open period.
- **PC pill returns nothing** — the `physical_count` ref-type value has no matching `enum_inventory_doc_type` member; count corrections arrive as SI / SO documents.
- **Insufficient-stock error on an outbound document** — a stock-out **Commit** pre-checks every line and returns `Insufficient stock for {product} at {location}: on hand {x}, requested {y}` (`STOCK_OUT_INSUFFICIENT_STOCK`, 400); an SR issue that gets past its own checks surfaces the ledger's `Insufficient stock. Requested: <X>, Available: <Y>`; the Store Keeper reduces the quantity or investigates the balance in the ledger (or the product's stock panel dialog on the document line).

## 4. Exit Point / Handoffs

- **Verification clean** — no further action; the ledger row is immutable and permanent.
- **Mismatch found** — handoff to the owning source module (GRN credit note, inventory-adjustment correction); the correction posts its own new transaction, and the pair of rows is the audit trail.

## 5. References

- Parent overview: [03-user-flow](/en/inventory/inventory/03-user-flow).
- Sibling: [transaction](/en/inventory/inventory/transaction) — full data-model and event matrix for the screen this flow uses.
- Sibling: [02-business-rules](/en/inventory/inventory/02-business-rules) — `INV_VAL_005` (insufficient stock), `INV_VAL_008` (period stamping), `INV_POST_001`–`INV_POST_003` (what each posting writes).
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/transaction/` (`transaction-component.tsx`, `use-transaction-table.tsx`, `transaction-summary.tsx`).
- Related: [inventory-adjustment](/en/inventory/inventory-adjustment), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check).
