---
title: Inventory Adjustment
description: Manual stock-in / stock-out corrections outside procurement and consumption — draft, commit to post, void to reverse; plus the near-expiry wastage write-off.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory-adjustment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Inventory Adjustment

> **At a Glance**
> **Module purpose:** Manual stock corrections outside procurement (GRN) and consumption (Store Requisition) — two independent document trees, Stock-In (`tb_stock_in`) and Stock-Out (`tb_stock_out`), classified by a shared reason-code master (`tb_adjustment_type`) &nbsp;·&nbsp; **Audience:** any user with the `inventory_management.view` permission (no distinct approval role exists in code) &nbsp;·&nbsp; **Lifecycle:** `draft` → **Commit** → `completed` (posted) → **Void** → `voided` &nbsp;·&nbsp; **Key entities/tables:** `tb_stock_in`, `tb_stock_in_detail` (with `expired_at`), `tb_stock_out`, `tb_stock_out_detail`, `tb_adjustment_type` &nbsp;·&nbsp; **Sub-pages:** 14

![Inventory Adjustment screen](/screenshots/inventory-adjustment/index.png)

## 1. Overview

**Inventory Adjustment** covers two document types under one screen, `/inventory-management/inventory-adjustment` (`?type=stock-in` / `?type=stock-out`, list filter `adj_type`): **Stock-In** (positive correction — found stock, count overage) and **Stock-Out** (negative correction — breakage, expiry, count shortage). They are two independent documents, `tb_stock_in` and `tb_stock_out`, not variants of one shared `tb_inventory_adjustment` entity. Both share the same header shape — document number (`si_no` / `so_no`), date, a reason (`adjustment_type_id`, displayed as **Reason**), location, description, and one or more product lines with `qty`, `cost_per_unit`, and `total_cost` — and both link to the [inventory](/en/inventory/inventory) ledger via a nullable `inventory_transaction_id` stamped onto each detail line **at commit**.

**Creation is no longer posting.** The 2026-07-15 revision of this module documented that `create()` wrote `doc_status = completed` and posted the ledger immediately, leaving Edit / Void unreachable. On 2026-07-30 the backend (`281a16399`, "si and so endpoint create are no longer mean complete must call /commit") changed that: `POST /stock-ins` / `POST /stock-outs` now create a **`draft`**, `PATCH /{id}/save` edits it, and **`PATCH /{id}/commit`** is the single posting event — it re-validates the document date against the inventory period, pre-checks stock-out lines against on-hand, calls `executeAdjustmentIn` / `executeAdjustmentOut` per line in one transaction, and flips the header to `completed`. The frontend form was redesigned the same day (`198d83c1`) and now has **Save**, **Commit** (with confirm dialog), **Void**, **Delete** and **Print**; Save keeps you on the document, Commit returns to the list (`128380f9`).

Read-only rules follow the status: `isReadOnly = doc_status ∈ {completed, voided}`. A `draft` shows **Edit** (`isView && !isReadOnly`) and **Delete**; in Edit mode it also shows **Void** (`canVoid = isEdit && !isReadOnly`). A `completed` document is view + print + stock-movements only in the UI — the real reversal endpoint, `DELETE /{id}/void`, works on a posted document but the shipped screen never offers the button for one (it only offers Void on drafts, where it behaves like a delete-with-reason). Deleting a completed document answers `Cannot delete a completed Stock In — inventory has already been adjusted` (400).

## 2. Business Context

Hospitality operations need a channel to correct stock that changes outside a purchase or a requisition: damage discovered in storage, expired product written off, found stock recovered during a shelf check, or the overage/shortage lines that a completed [physical-count](/en/inventory/physical-count) leaves behind. Two other producers write into the same tables:

- `PhysicalCountService.submit()` creates `tb_stock_in` (overage) / `tb_stock_out` (shortage) rows directly at `doc_status = completed`, with no `adjustment_type_id` — **and does not post them to the ledger** (confirmed 2026-09-22: no `inventoryTransactionService` reference anywhere in `physical-count/*.ts`). They are audit records of the variance, not stock movements.
- `POST /wastage-reporting` ([wastage-reporting](/en/inventory/inventory-adjustment/wastage-reporting)) creates one `tb_stock_out` per location for the selected near-expiry lots and commits it in the same call — these **are** posted (`executeAdjustmentOut` with `target_lot_nos`).

Because the reason-code master (`tb_adjustment_type`) only carries `code`, `name`, `type` (direction), `description`, and `is_active` — no GL-account field, no document-required flag, no quality-check flag — there is no accounting integration in this module: the 2026-09 GL core (`tb_gl_jv*`, manual journal vouchers) has no hook from stock-in / stock-out code. Every adjustment is a pure inventory-quantity/value movement.

## 3. Key Concepts

- **Two parallel document trees, one classifier.** `tb_stock_in` (inbound) and `tb_stock_out` (outbound) are independent Prisma models with an identical header/detail shape. `tb_adjustment_type.type` (`enum_adjustment_type`: `stock_in` | `stock_out` | `eop_in` | `eop_out`) gates which tree a reason is meant for — `eop_in`/`eop_out` are reserved for the period-end engine and are not offered in the reason picker. The picker filters by direction client-side only; the backend enriches the header from the referenced `tb_adjustment_type` row but does not re-check that its `type` matches the document's direction.
- **Reason ("Adjustment Type").** The UI's **Reason** field is the `adjustment_type_id` foreign key documented on [01 — Data Model](/en/inventory/inventory-adjustment/01-data-model). Reason rows are maintained on `/config/adjustment-type`, out of this module's scope.
- **Cost entry differs by direction.** For **Stock-In**, `cost_per_unit` is a user-editable field on each line (pre-filled from `useProductCostByLocationQty` as a suggestion); the value the user commits becomes the new cost layer's cost. For **Stock-Out**, the backend never writes `cost_per_unit`/`total_cost` onto `tb_stock_out_detail` (both stay `0`); the actual cost is picked at commit by the ledger (FIFO: oldest layers first; Average: current BU average).
- **Expiry on stock-in lines (API only).** `tb_stock_in_detail.expired_at` (migration `20260731120000_add_inflow_price_expiry`) is accepted and persisted by `POST /stock-ins`, `PATCH /save` and the detail endpoints (stock-in DTO + swagger since 2026-08-03), but the shipped form has **no expiry input** (`grep expired routes/inventory-management/inventory-adjustment/` → nothing) and nothing in this module reads it; the GRN line's `expired_at` is what feeds [wastage-reporting](/en/inventory/inventory-adjustment/wastage-reporting).
- **No lot-picking UI.** Neither screen exposes a lot number or lot-selection control. Lot identity is generated by the ledger (`buildLotNo` → `{location_code}{YYMM}{seq4}`), the same format used by every other inventory-transaction-writing module.
- **Location scope.** The location picker (`LookupUserLocation`) is filtered client-side to Inventory / Consignment location types; the backend only requires `location_id` (`STOCK_IN_LOCATION_REQUIRED`) and does not re-check the type.
- **Date-within-period — now enforced server-side.** The form validates the date against the current period window (Zod, `ia-form-schema.ts`), and since 2026-08-31 the backend re-checks at create **and** commit: stock-in `si_date` must fall inside an open/locked period (`STOCK_IN_DATE_OUTSIDE_OPEN_PERIOD`, 422), stock-out `so_date` must fall inside the **current** period (`STOCK_OUT_DATE_NOT_CURRENT_PERIOD`, 422; `STOCK_OUT_NO_OPEN_PERIOD` if none). `si_no` / `so_no` are numbered from the document date, not the click date (`5d878a6c8`).
- **Insufficient stock is checked before posting.** `StockOutService.commit` sums requested qty per product and compares with `getOnHandQty`; a shortfall returns `Insufficient stock for {product} at {location}: on hand {x}, requested {y}` (`STOCK_OUT_INSUFFICIENT_STOCK`, 400) and nothing is written.
- **Optimistic concurrency.** `doc_version` is required on save and commit (`COMMON_DOC_VERSION_REQUIRED` family); the frontend re-reads the incremented value after save so a following commit does not race.

## 4. Roles and Personas

The code does not distinguish a Store Keeper from an Inventory Controller for this module: the nav entry, the create/edit screen, and the list all gate on the single generic `inventory_management.view` permission (`constant/module-list.ts`), and there is no workflow stage, approval queue, or `enum_stage_role` assignment in `stock-in.service.ts` / `stock-out.service.ts`. (The gateway does carry finer guard keys — `stockIn.create / update / commit / delete / print / getStockMovements` — but the frontend catalog's `inventory_management.stock_in.*` / `.stock_out.*` keys gate the two Store Operations nav entries, not this screen.) The wiki keeps two persona pages for readability:

| Role | Realistic scope |
|------|----------------|
| Store Keeper / whoever enters the document | Opens **Add Stock-In** / **Add Stock-Out**, picks reason + location, enters lines, **Save**s a draft, **Commit**s when ready. |
| Inventory Controller | Same screen: reviews drafts (Edit / Delete / Void), commits them, reads completed documents, their **stock movements** and print output; voids a posted document via the API if a reversal is needed. |

A dedicated Finance persona, a System Administrator config workbench, and an Auditor read-scope were previously documented for this module; no matching route, component, permission key, or backend endpoint was found for any of them. See [03 — User Flow — Finance](/en/inventory/inventory-adjustment/03-user-flow-finance) and [03 — User Flow — Audit / Config](/en/inventory/inventory-adjustment/03-user-flow-audit-config).

## 5. Related Modules

**Cross-module flow:**
- [inventory](/en/inventory/inventory) — every commit calls the shared `InventoryTransactionService` (`executeAdjustmentIn` / `executeAdjustmentOut`) that also backs GRN, SR, wastage write-off and period-end
- [inventory/period-end](/en/inventory/inventory/period-end) — a `draft` stock-in / stock-out dated in the period blocks **Start Period Close**; the SI/SO review cards on `/period-end/review` link back here
- [physical-count](/en/inventory/physical-count) — count completion creates `tb_stock_in` / `tb_stock_out` rows directly at `completed`, with no reason code and **no ledger posting**
- [inventory-adjustment/wastage-reporting](/en/inventory/inventory-adjustment/wastage-reporting) — near-expiry lots; the write-off endpoint creates and commits a Stock Out per location
- [costing](/en/inventory/costing) — FIFO layer creation on Stock-In, FIFO consumption / weighted-average recompute on Stock-Out

**Master configuration:**
- [master-data/adjustment-type](/en/inventory/master-data/adjustment-type) — reason-code master (`code`, `name`, direction, `is_active`) referenced by `adjustment_type_id`
- [master-data/location](/en/inventory/master-data/location) — the location whose balance the adjustment moves

## 6. Reference Sources

- Concepts: `../carmen/docs/inventory-adjustment/` (frozen 2026-04-27; single-entity, GL-posting, threshold-approval design — superseded by the code)
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/inventory-adjustment/`
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/stock-in/`, `.../stock-out/`, `.../inventory-transaction/`; gateway `apps/backend-gateway/src/application/stock-ins/`, `stock-outs/`, `inventory-adjustments/`
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/stock-in/`, `inventory/stock-out/` (create, update, **commit**, void, remove, by-id, list, print-viewer, `details/`), `inventory/inventory-adjustment/` (merged list, by-id, print)
- E2E tests: no Playwright spec; manual catalog `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (60 cases, re-verified against the 2026-09 form — Commit, Void-needs-Edit, Delete-in-view), generated stories `docs/user-stories/730-inventory-adjustment.md` (32); `tests/031-adjustment-type.spec.ts` covers the reason-code master only

## 7. Pages in This Module

- [01 — Data Model](/en/inventory/inventory-adjustment/01-data-model) — Entities, fields, relationships, and enums (Prisma-derived).
- [01a — Data Model — Comment Tables](/en/inventory/inventory-adjustment/01a-data-model-comments) — Document-level and line-level comment / attachment tables and the `enum_comment_type` user/system tagging.
- [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules) — Validation, calculation, and posting rules.
- [03 — User Flow](/en/inventory/inventory-adjustment/03-user-flow) — Document lifecycle, plus persona index.
  - [Store Keeper](/en/inventory/inventory-adjustment/03-user-flow-store-keeper)
  - [Inventory Controller](/en/inventory/inventory-adjustment/03-user-flow-inventory-controller)
  - [Finance](/en/inventory/inventory-adjustment/03-user-flow-finance)
  - [Audit / Config](/en/inventory/inventory-adjustment/03-user-flow-audit-config)
- [04 — Test Scenarios](/en/inventory/inventory-adjustment/04-test-scenarios) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Store Keeper](/en/inventory/inventory-adjustment/04-test-scenarios-store-keeper)
  - [Inventory Controller](/en/inventory/inventory-adjustment/04-test-scenarios-inventory-controller)
  - [Finance](/en/inventory/inventory-adjustment/04-test-scenarios-finance)
  - [Audit / Config](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config)
- [Wastage Reporting](/en/inventory/inventory-adjustment/wastage-reporting) — near-expiry lot list under Store Operations and the write-off API that creates a committed Stock Out per location.
