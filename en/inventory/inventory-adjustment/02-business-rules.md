---
title: Inventory Adjustment — Business Rules
description: Validation, calculation, authorization and posting rules for manual stock-in / stock-out — draft on create, ledger write on commit, reversal on void.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory-adjustment, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Business Rules

> **At a Glance**
> **Rule families:** `ADJ_VAL_*` validation &nbsp;·&nbsp; `ADJ_CALC_*` calculation &nbsp;·&nbsp; `ADJ_POST_*` posting
> **Rule count:** 27 rules, traced to `ia-form-schema.ts`, `stock-in.service.ts` / `stock-out.service.ts`, `inventory-period.helper.ts`, `inventory-transaction.service.ts` and `packages/error-catalog/src/catalog.ts`
> **Audience:** Test author + developer
> **Headline (re-verified 2026-09-22):** `create()` writes `doc_status = draft` and nothing else; `commit()` is the posting event; there is still no approval stage, threshold or GL entry

## 1. Overview

This page catalogues the rules actually enforced by the **inventory-adjustment module** — the two-table document layer (`tb_stock_in` / `tb_stock_out`) for manual stock corrections. The 2026-07-15 revision was written against code where creation *was* posting; the backend commit `281a16399` (2026-07-30) split that into **create → draft** and **commit → post**, and a series of 2026-08 changes added the server-side period-date guards (`4898ec8d3`, `3ff5e05dc`, `6ca3266e1`), stock-out numbering by document date (`5d878a6c8`), and the stock-out on-hand pre-check. Every rule below was re-read from HEAD. What has **not** changed: no threshold-gated approval chain, no GL/journal posting, no lot-entry UI, no segregation-of-duties check.

## 2. Validation Rules

Rule IDs follow `ADJ_VAL_NNN`. "Client" = Zod in `ia-form-schema.ts` (runs on Save and before the Commit confirm dialog); "Server" = `StockInService` / `StockOutService` and the error catalog.

| Rule ID | Condition | Enforced by | Behaviour |
| ------- | --------- | ----------- | --------- |
| `ADJ_VAL_001` | `location_id` is required. | Client (Zod `.min(1)`) and server on create **and** commit (`STOCK_IN_LOCATION_REQUIRED` / `STOCK_OUT_LOCATION_REQUIRED`). | 400 `Location is required for stock in` / `…stock out`. |
| `ADJ_VAL_002` | `adjustment_type_id` is required and should match the document's direction. | Client only (Zod `.refine`; the picker filters `tb_adjustment_type` by `type`). The server enriches the header from the referenced row (`enrichment.enrich('tb_stock_in', …)`) and does not re-check `type`. | A direct API call with a mismatched-direction reason is not rejected server-side. |
| `ADJ_VAL_003` | Document date must fall inside a period. | Client (Zod `.refine` against the current period window) **and server** — stock-in: `assertDateInOpenPeriod(si_date)` on create and commit; stock-out: `assertDateInCurrentPeriod(so_date)` on create and commit (`inventory-period.helper.ts`). | 422 `STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD` ("The stock-in date does not fall inside any open period"); 422 `STOCK_OUT_DATE_NOT_CURRENT_PERIOD` ("Stock-outs can only be dated inside the current period ({period}: {start} to {end})"); 422 `STOCK_OUT_NO_OPEN_PERIOD` when no period is open. Note the asymmetry: a stock-in may be dated in any `open`/`locked` period, a stock-out only in the current (earliest open) one. |
| `ADJ_VAL_004` | At least one line item. | Client (Zod `items.min(1)`) and server on create (`stock_in_detail.add` non-empty) and commit (`STOCK_IN_DETAIL_ITEMS_REQUIRED` / `STOCK_OUT_DETAIL_ITEMS_REQUIRED`). | 400 `Stock in detail items are required` / `…out…`. |
| `ADJ_VAL_005` | Each line's `product_id` resolves to an existing `tb_product`. | Client (`.min(1)`) and server enrichment (`enrich('tb_stock_in_detail', …)`; detail endpoints return `PRODUCT_NOT_FOUND`). | Rejected per document / per line. |
| `ADJ_VAL_006` | Each line's `qty ≥ 0`. | Client only (Zod `.min(0)` — relaxed from the earlier `≥ 1`; `e9d7fd35c` "xxx_qty can accept float"). | Fractional quantities are accepted; a zero line passes validation but posts nothing useful. |
| `ADJ_VAL_007` | Each line's `cost_per_unit ≥ 0`. | Client only (Zod `.min(0)`). Meaningful for Stock-In only — the Stock-Out grid hides the column and the server never persists it for stock-out lines. | Reject with a non-negative-cost message on Stock-In. |
| `ADJ_VAL_008` | `description` (header and line) ≤ 256 characters; not required. | Client only. | Blank description saves and commits. |
| `ADJ_VAL_009` | Location type restricted to Inventory / Consignment. | Client only (`LookupUserLocation` `locationTypes`). Server only requires the id. | A direct API call with a `direct` location is not rejected. |
| `ADJ_VAL_010` | Stock-Out on-hand pre-check at commit: Σ requested per product ≤ `getOnHandQty(product, location)`. | Server (`StockOutService.commit` → `findStockShortage`, before the transaction opens). | 400 `STOCK_OUT_INSUFFICIENT_STOCK`: `Insufficient stock for {product} at {location}: on hand {x}, requested {y}`; nothing written, draft survives. The ledger's own `Insufficient stock. Requested: …, Available: …` (Error → 500) remains as a second guard inside `createAverageConsumption` / `createFifoConsumption`. |
| `ADJ_VAL_011` | Optimistic concurrency: `doc_version` must be sent on save and commit and match the stored value. | Server (`COMMON_DOC_VERSION_REQUIRED`; Prisma `where: { id, doc_version }`). | Stale version matches zero rows → update/commit fails; the frontend re-reads the incremented `doc_version` after every save (`useUpdateInventoryAdjustment`). |
| `ADJ_VAL_012` | Void preconditions: not already `voided`; for a posted stock-in, on-hand at the location must cover the reversal of every posted line. | Server (`STOCK_IN_ALREADY_VOIDED` / `STOCK_OUT_ALREADY_VOIDED`; `voidStockIn` on-hand loop). | 400 `Stock in is already voided`; `Cannot void: product <code> has insufficient on-hand qty (<X>) at this location to reverse <Y>` (INVALID_ARGUMENT). `voidStockOut` reverses with `executeAdjustmentIn` and has no on-hand precondition. |
| `ADJ_VAL_013` | Reason-direction match (`tb_adjustment_type.type` vs document tree). | Client only. | Not enforceable outside the picker UI. |
| `ADJ_VAL_014` | Only a `draft` can be committed, saved, or have lines added/updated/removed; only a `draft` can be deleted. | Server (`STOCK_IN_ONLY_DRAFT_COMMITTABLE`, `STOCK_IN_COMPLETED_NO_UPDATE`, `STOCK_IN_NON_DRAFT_NO_ADD/UPDATE/DELETE_DETAIL`, `STOCK_IN_COMPLETED_NO_DELETE`, and the `STOCK_OUT_*` twins). | 400 `Only a draft Stock In can be committed`; `Cannot update a completed Stock In — inventory has already been adjusted`; `Cannot delete a completed Stock In — …`. |
| `ADJ_VAL_015` | `doc_status` cannot be changed through save. | Server (`STOCK_IN_STATUS_CHANGE_NOT_ALLOWED` / `STOCK_OUT_STATUS_CHANGE_NOT_ALLOWED` when the payload's `doc_status ≠ draft`). | 400 `doc_status cannot be changed on save — use the commit or void endpoint`. |

## 3. Calculation Rules

| Rule ID | Formula |
| ------- | ------- |
| `ADJ_CALC_001` (line total) | `total_cost = qty × cost_per_unit`, computed client-side (`use-ia-item-table.tsx`) and persisted on `tb_stock_in_detail`; on Stock-Out the value is display-only and never persisted. |
| `ADJ_CALC_002` (Stock-In cost suggestion) | `cost_per_unit` is pre-filled via `useProductCostByLocationQty(buCode, productId, locationId, qty)` — the product's current cost at that location — as soon as the product is picked (`e246abaa`); editable, and the committed value is what the ledger uses. |
| `ADJ_CALC_003` (Stock-Out cost preview) | Display-only preview from the product cost hooks; plays no role in the posted cost. |
| `ADJ_CALC_004` (new average cost, Average BU) | On Stock-In commit `executeAdjustmentIn` writes the new inbound layer and restamps `average_cost_per_unit` for the product (`restampAverageCostForProducts`) — generic ledger logic shared with GRN. |
| `ADJ_CALC_005` (FIFO consumption, Stock-Out) | `createFifoConsumption` consumes from `getAvailableFifoLots` in `lot_seq_no` order until the requested qty is satisfied, one outbound layer per consumed lot; wastage write-offs pass `target_lot_nos` to consume a named lot. |
| `ADJ_CALC_006` (Average consumption, Stock-Out) | `createAverageConsumption` charges the entire outbound qty at the current BU-wide average. |
| `ADJ_CALC_007` (rounding) | Monetary values round to 2 dp at each cost-layer write; quantity columns store 5 dp. |
| `ADJ_CALC_008` (period stamp) | Stock-in layers: `resolvePeriodForDate(si_date)` (throws `No open period covers …` if none — unreachable in practice because `ADJ_VAL_003` runs first). Stock-out consumption and both void reversals: `resolveCurrentPeriod` (earliest `open`/`locked` period). |
| `ADJ_CALC_009` (document number) | `si_no` / `so_no` are generated by the running-code service from the **document date** (`generateSINo(si_date)` / `generateSONo(so_date)`, `5d878a6c8`), not the creation date. |

## 4. Authorization

No role- or threshold-based authorization exists in this module. The nav entry, the list and the create/edit screen gate on the single generic permission `inventory_management.view` (`constant/module-list.ts`). The frontend catalog also defines `inventory_management.stock_in.*` / `inventory_management.stock_out.*` CRUD keys (`constant/permissions.ts`), but they gate two **other** Store Operations nav entries — Stock Replenishment (`.stock_in.view`) and Wastage Reporting (`.stock_out.view`) — not this module's screens. The gateway is finer-grained: `stock-ins.controller.ts` guards `stockIn.findAll / findOne / create / update / commit / delete / print / getStockMovements` (and the `stockOut.*` twins) via `AppIdGuard`; `inventory-adjustments.controller.ts` guards `inventoryAdjustment.findAll / findOne / print`.

## 5. Posting Rules

Rule IDs follow `ADJ_POST_NNN`.

| Rule ID | Event | Effects |
| ------- | ----- | ------- |
| `ADJ_POST_001` | `create()` — `POST /stock-ins` \| `/stock-outs` (**Save**, or the first half of **Commit** on a new form) | Single transaction: header at `doc_status = draft`, `doc_version = 0`, `si_no`/`so_no` from the document date, enriched location / reason snapshots; each detail line created (stock-in lines with `cost_per_unit`, `total_cost`, optional `expired_at`; stock-out lines without cost). **No ledger write.** |
| `ADJ_POST_002` | `update()` — `PATCH /{id}/save` | Draft only (`ADJ_VAL_014`). Header fields and `stock_in_detail.{add, update, remove}` applied; `doc_version` checked and incremented; `doc_status` in the payload must be `draft` (`ADJ_VAL_015`). Detail endpoints `POST/PUT/DELETE /{id}/details[/:detail_id]` follow the same draft-only rule. |
| `ADJ_POST_003` | `commit()` — `PATCH /{id}/commit` `{ doc_version }` | Draft only. Re-checks location, lines, date (`ADJ_VAL_003`), and for stock-out on-hand (`ADJ_VAL_010`); resolves the BU `calculation_method`; then in one transaction, per line: `executeAdjustmentIn` (stock-in: new inbound layer at the entered cost, lot `{location_code}{YYMM}{seq4}`, `at_period` from `si_date`) or `executeAdjustmentOut` (stock-out: FIFO / average consumption), `inventory_transaction_id` stamped on the line; header → `completed`, `doc_version + 1`. |
| `ADJ_POST_004` | `delete()` — `DELETE /{id}` | Draft only; soft-delete of header and lines. Completed → `STOCK_IN_COMPLETED_NO_DELETE`. |
| `ADJ_POST_005` | `voidStockIn()` / `voidStockOut()` — `DELETE /{id}/void` `{ void_reason }` | Not-already-voided check; stock-in additionally checks on-hand can absorb each posted line's reversal. Then in one transaction: for every line with an `inventory_transaction_id`, the opposite leg (`executeAdjustmentOut` for a stock-in, `executeAdjustmentIn` for a stock-out) at the cost the ledger resolves at void time, `at_period` = current period; header `doc_status = voided`, `deleted_at` / `deleted_by_id` set, `info.void_reason` stored. A `draft` (no posted lines) is simply marked voided and soft-deleted. Because the row is soft-deleted, it disappears from list and detail queries. UI reachability: **Void** renders only in Edit mode on a draft; voiding a posted document is API-only. |
| `ADJ_POST_006` | Other producers of `tb_stock_in` / `tb_stock_out` rows | [physical-count](/en/inventory/physical-count) `submit()` writes overage/shortage rows directly at `completed` with no reason code and **no ledger call** (confirmed: no `inventoryTransactionService` reference in `physical-count/*.ts`). [wastage-reporting](/en/inventory/inventory-adjustment/wastage-reporting) `writeOff()` creates one stock-out per location at `draft`, posts each line with `executeAdjustmentOut(target_lot_nos)`, and sets `completed` — all in one call. |

## 6. References

- Sibling: [01 — Data Model](/en/inventory/inventory-adjustment/01-data-model) — canonical `tb_stock_in` / `tb_stock_out` / `tb_adjustment_type` shape.
- Sibling: [03 — User Flow](/en/inventory/inventory-adjustment/03-user-flow) — how these rules play out across the persona pages.
- Frontend: `ia-form-schema.ts` (Zod rules), `use-ia-item-table.tsx` (`recalcTotal`, cost prefill), `ia-form.tsx` (`confirmCommit`, `isReadOnly`), `ia-form-hero.tsx` (button gating), `use-inventory-adjustment.ts` (endpoints).
- Backend: `apps/micro-business/src/inventory/stock-in/stock-in.service.ts`, `.../stock-out/stock-out.service.ts`, `.../inventory-period.helper.ts` (`assertDateInOpenPeriod`, `assertDateInCurrentPeriod`), `.../inventory-transaction/inventory-transaction.service.ts` (`executeAdjustmentIn` / `executeAdjustmentOut`), `packages/error-catalog/src/catalog.ts` (`STOCK_IN_*` / `STOCK_OUT_*`, incl. `STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD`, `STOCK_OUT_DATE_NOT_CURRENT_PERIOD`, `STOCK_OUT_NO_OPEN_PERIOD`, `STOCK_OUT_INSUFFICIENT_STOCK`, `*_ONLY_DRAFT_COMMITTABLE`, `*_STATUS_CHANGE_NOT_ALLOWED`).
- Bruno: `collections/carmen-inventory/inventory/stock-in/`, `inventory/stock-out/` (`POST-create`, `PATCH-update`, `PATCH-commit`, `DELETE-void-*`, `DELETE-remove`, `GET-print-to-report`, `details/`).
- Related: [inventory](/en/inventory/inventory) — the shared ledger and costing-method rules this module's postings feed into; [inventory/period-end](/en/inventory/inventory/period-end) — drafts block Start Period Close.
