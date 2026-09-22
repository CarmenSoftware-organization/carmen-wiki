---
title: Wastage Reporting
description: Near-expiry lot list and write-off API under Store Operations — real backend since 2026-08-10; the write-off creates a completed Stock Out per location and posts it to the ledger.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory-adjustment, wastage, loss, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Wastage Reporting

> **At a Glance**
> **Location:** Store Operations → Wastage Reporting (`/store-operation/wastage-reporting`, nav permission `inventory_management.stock_out.view`) — cross-referenced from Inventory Adjustment because its write-off *is* a `tb_stock_out` &nbsp;·&nbsp; **Status:** **real API since 2026-08-10** (`c9348f667`; frontend switched off the mock on 2026-08-20 `061a0f3f`) &nbsp;·&nbsp; **Endpoints:** `GET /api/{bu}/wastage-reporting` (near-expiry lots) and `POST /api/{bu}/wastage-reporting` (write-off) &nbsp;·&nbsp; **Backend:** `apps/micro-business/src/inventory/wastage-reporting/` — no table of its own; it reads GRN lots and writes `tb_stock_out` &nbsp;·&nbsp; **UI today:** list only — the write-off endpoint has no button in the shipped frontend

![Wastage Reporting screen](/screenshots/inventory-adjustment/wastage-reporting.png)

## 1. What & Who

The 2026-07-15 revision of this page described a **mock-data-only** screen (`wr-mock-data.ts`, a `WastageReport` type with `pending/approved/rejected` statuses, fake CRUD). That is no longer true — and the real feature is a different shape from the mock. Wastage Reporting is now a **near-expiry lot report over committed GRN receipts** plus a **write-off endpoint** that turns selected lots into a completed, ledger-posted Stock Out. There is still no `tb_wastage_report` table and no approval workflow.

- **Store / kitchen staff** (any user with `inventory_management.stock_out.view`) — read the list: which lots expire within *n* days, how many units remain, what they are worth
- **Whoever calls `POST /wastage-reporting`** — currently only reachable via API (Bruno `_uncategorized/wastage-reporting/POST-write-off-wastage-reporting.bru`); the shipped list screen has no write-off action
- **Inventory** — receives one `adjustment_out` transaction per written-off line

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| See lots expiring soon | Store Operation → Wastage Reporting | `GET /wastage-reporting?days=30` (default window `DEFAULT_EXPIRY_WINDOW_DAYS = 30`); optional `include_expired`, `status=expiring|expired`, `location_id`, `product_id`, search + pagination. Summary bar: items, expired count, expiring count, qty at risk, value at risk |
| Jump to the receipt | Click the GRN number | Opens `/procurement/goods-receive-note/{grn_id}` |
| Write off a lot (API) | `POST /wastage-reporting` with `{ so_date?, adjustment_type_id, description?, note?, items: [{ grn_detail_item_id, qty, note? }] }` | Lines are grouped by location; for each location one `tb_stock_out` is created at `draft`, every line posted through `executeAdjustmentOut`, then the header is set to `completed` — all in one transaction (`wastage-reporting.logic.ts`). `so_date` defaults to today and must satisfy the stock-out period rule |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| Empty list | No committed GRN line has `expired_at` inside the window (`tb_good_received_note_detail_item.expired_at`, migration `20260731120000_add_inflow_price_expiry`), or every candidate lot's remaining qty ≤ 0 | Widen `days`, or check that receipts carry an expiry date |
| `WASTAGE_ITEMS_REQUIRED` | `items` empty | Send at least one line |
| Write-off rejected for quantity | `qty` exceeds the lot's remaining balance (`remaining_qty` = layer `in_qty` − consumption via `parent_lot_no`) or the location's on-hand | Reduce `qty` |
| `STOCK_OUT_DATE_NOT_CURRENT_PERIOD` (422) | `so_date` outside the current inventory period — the write-off inherits the stock-out date guard | Re-date |

## 4. Edge Cases

- **Remaining quantity is computed from the ledger, per lot.** `resolveLotsByDetailItemIds` walks `tb_inventory_transaction_detail.good_received_note_detail_item_id` (added 2026-08-10) from the GRN line to its `current_lot_no`, then sums `in_qty` and `out_qty` on `tb_inventory_transaction_cost_layer` (`parent_lot_no` for consumption). Lots with `remaining_qty ≤ QTY_EPSILON` are dropped from the list.
- **Only committed receipts count** (`doc_status = committed` on both the GRN and its detail path); a draft or voided GRN never appears.
- **`days_to_expiry` is a signed integer** — negative for already-expired lots (`status = expired`); the list is sorted by `expired_at` ascending.
- **One Stock Out per location, not per call.** A write-off spanning three locations creates three `tb_stock_out` documents, each with its own `so_no`, all tagged with the caller's `adjustment_type_id` and `description`.
- **No UI for the write-off.** `routes/store-operation/wastage-reporting/` contains only `use-wastage-report.ts` (GET), `use-wr-table.tsx` and `wr-component.tsx`; the form / mock files were deleted on 2026-08-20. Voiding a wastage Stock Out is done from the Inventory Adjustment screen like any other stock-out.
- **Permission is real but coarse.** The nav entry is gated by `inventory_management.stock_out.view` (`constant/module-list.ts`); the gateway guards are `wastageReporting.findAll` / `wastageReporting.writeOff`.

## 5. Data Shape (API response)

Source: `apps/backend-gateway/src/application/wastage-reporting/swagger` and `apps/micro-business/src/inventory/wastage-reporting/dto/wastage-reporting.serializer.ts`.

| Field | Notes |
|---|---|
| `grn_detail_item_id`, `grn_detail_id`, `grn_id`, `grn_no`, `grn_date` | The receipt line the lot came from — `grn_detail_item_id` is the key the write-off takes back |
| `product_id`, `product_code`, `product_name`, `product_local_name`, `product_sku` | Product snapshot |
| `location_id`, `location_code`, `location_name` | Receiving location — the write-off's Stock Out is created here |
| `lot_no` | Ledger lot (`{location_code}{YYMM}{seq4}`), from the linked `tb_inventory_transaction_detail.current_lot_no` |
| `expired_at`, `days_to_expiry`, `status` (`expiring` / `expired`) | Expiry data from the GRN line |
| `remaining_qty`, `cost_per_unit`, `remaining_value`, inventory unit | Ledger-derived balance and value at risk |

Write-off response: the created `tb_stock_out` header(s) — `{ id, so_no, doc_status: completed, location_id, location_code, location_name }` per location.

## 6. Cross-References

- [inventory-adjustment](/en/inventory/inventory-adjustment) — the write-off is an ordinary `tb_stock_out` (`adjustment_type_id` required) and shows up in the Stock Out list, where it can be voided.
- [inventory/transaction](/en/inventory/inventory/transaction) — each written-off line is an `adjustment_out` cost-layer consumption from the named lot.
- [good-receive-note](/en/inventory/good-receive-note) — `expired_at` is captured on the GRN line; the near-expiry list is a view over those lines.
- [master-data/adjustment-type](/en/inventory/master-data/adjustment-type) — the reason master the write-off references.

## 7. References

- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/wastage-reporting/` (`wastage-reporting.service.ts` — `findNearExpiry`, `resolveLotsByDetailItemIds`; `wastage-reporting.logic.ts` — `WastageReportingLogic.writeOff`, `groupWriteOffByLocation`; `dto/wastage-reporting.dto.ts`, `dto/wastage-reporting.serializer.ts`); gateway `apps/backend-gateway/src/application/wastage-reporting/wastage-reporting.controller.ts` (`@Controller('api/:bu_code/wastage-reporting')`).
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/wastage-reporting/` (`GET-find-near-expiry-wastage-reporting.bru`, `POST-write-off-wastage-reporting.bru`).
- **Frontend:** `../carmen-inventory-frontend-react/routes/store-operation/wastage-reporting/` (`wr-component.tsx`, `use-wr-table.tsx`, `use-wastage-report.ts`); nav gate in `constant/module-list.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/710-wastage-reporting.spec.ts` (20 tests, generated stories `docs/user-stories/710-wastage-reporting.md`) — list, summary and GRN-link behaviour; no write-off coverage because the UI has none.
