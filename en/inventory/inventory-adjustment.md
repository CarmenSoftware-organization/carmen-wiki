---
title: Inventory Adjustment
description: Manual stock-in / stock-out corrections outside procurement and consumption — write-offs, write-ons, and count-variance rollups.
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Inventory Adjustment

> **At a Glance**
> **Module purpose:** Manual stock corrections outside procurement (GRN) and consumption (Store Requisition) — two independent document trees, Stock-In (`tb_stock_in`) and Stock-Out (`tb_stock_out`), classified by a shared reason-code master (`tb_adjustment_type`) &nbsp;·&nbsp; **Audience:** any user with the `inventory_management.view` permission (no distinct approval role exists in code) &nbsp;·&nbsp; **Key entities/tables:** `tb_stock_in`, `tb_stock_in_detail`, `tb_stock_out`, `tb_stock_out_detail`, `tb_adjustment_type` &nbsp;·&nbsp; **Sub-pages:** 14

![Inventory Adjustment screen](/screenshots/inventory-adjustment/index.png)

## 1. Overview

**Inventory Adjustment** covers two screens under `/inventory-management/inventory-adjustment`: **Stock-In** (positive correction — found stock, count overage) and **Stock-Out** (negative correction — breakage, expiry, count shortage). They are two independent documents, `tb_stock_in` and `tb_stock_out`, not variants of one shared `tb_inventory_adjustment` entity. Both share the same header shape — document number (`si_no` / `so_no`), date, a reason (`adjustment_type_id`, displayed to the user as **Reason**), location, description, and one or more product lines with `qty`, `cost_per_unit`, and `total_cost` — and both link to the [inventory](/en/inventory/inventory) ledger via a nullable `inventory_transaction_id` stamped onto each detail line at creation.

**The document *is* the posting event.** Unlike GRN or Store Requisition, there is no separate submit-then-approve stage: `StockInService.create()` / `StockOutService.create()` write the header at `doc_status = completed` and call the [inventory](/en/inventory/inventory) ledger's `executeAdjustmentIn` / `executeAdjustmentOut` in the same database transaction, unconditionally — this happens regardless of which button the user clicks. The form's **Save** button sets `doc_status: "draft"` and **Submit** sets `doc_status: "completed"` before calling the identical create mutation, but the backend ignores the client-sent value and always writes `completed`. In practice there is no reachable draft state for a newly created adjustment — every stock-in/stock-out that exists in the system posted to the ledger at the instant it was created.

One consequence carries through the whole UI: `isReadOnly` on the detail screen is `doc_status === 'voided' || doc_status === 'completed'`, and since every persisted document is `completed`, `isReadOnly` is always true. The **Edit** button (`isView && !isReadOnly`) therefore never renders for a real document, so the form's edit mode is never entered — and the **Void** button, which requires `isEdit` to be true, is consequently never reachable either, even though the backend implements a real void endpoint (see [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules) § 5). The list view's row-menu **Delete** action does render unconditionally, but the backend rejects it with `"Cannot delete a completed Stock In — inventory has already been adjusted"` for every existing row, since `delete()` only succeeds when `doc_status = draft`. Once created, a Stock-In or Stock-Out document is functionally **read-only** through the current UI (view + print only).

## 2. Business Context

Hospitality operations need a channel to correct stock that changes outside a purchase or a requisition: damage discovered in storage, expired product written off, found stock recovered during a shelf check, or the overage/shortage lines that a completed [physical-count](/en/inventory/physical-count) leaves behind. `PhysicalCountService.submit()` creates `tb_stock_in` (overage) / `tb_stock_out` (shortage) rows directly — at `doc_status = completed`, with no `adjustment_type_id` set at all (count-driven rows carry no reason code) — as the audit record of the count's variance; whether that write also drives the ledger's cost layers the same way a manual Stock-In/Stock-Out does was not confirmed in this pass and should be re-checked against `physical-count`'s own resync pass.

Because the reason-code master (`tb_adjustment_type`) only carries `code`, `name`, `type` (direction), `description`, and `is_active` — no GL-account field, no document-required flag, no quality-check flag — there is no accounting integration built into this module: a repo-wide search of both the frontend and the `carmen-turborepo-backend-v2` backend found zero references to `journal`, `ledger`, or a GL-posting engine anywhere in the stock-in/stock-out code path. Every adjustment is a pure inventory-quantity/value movement; it does not produce a journal entry.

## 3. Key Concepts

- **Two parallel document trees, one classifier.** `tb_stock_in` (inbound) and `tb_stock_out` (outbound) are independent Prisma models with an identical header/detail shape. `tb_adjustment_type.type` (`enum_adjustment_type`: `stock_in` | `stock_out` | `eop_in` | `eop_out`) gates which tree a reason is meant for — `eop_in`/`eop_out` are reserved for the period-end engine and are not offered in the Stock-In/Stock-Out reason picker. The picker filters by direction client-side only; the backend's header validation confirms the referenced `tb_adjustment_type` row exists, but does **not** re-check that its `type` matches the document's direction — a direct API call could attach a `stock_out`-typed reason to a `tb_stock_in` document.
- **Reason ("Adjustment Type").** The UI's **Reason** field is the same `adjustment_type_id` foreign key documented on [01 — Data Model](/en/inventory/inventory-adjustment/01-data-model) — there is no separate "reason code" concept layered on top of it. Reason rows are maintained on a distinct master-data screen (`/config/adjustment-type`), out of this module's scope.
- **Cost entry differs by direction.** For **Stock-In**, `cost_per_unit` is a user-editable field on each line (pre-filled from `useProductCostByLocationQty`'s current location average as a starting suggestion); the value the user submits is what gets persisted on `tb_stock_in_detail` and passed straight through to the ledger's `executeAdjustmentIn`, which uses it to build the new FIFO layer or recompute the BU-wide weighted average. For **Stock-Out**, the `cost_per_unit` column is hidden from the line-item grid entirely — the backend's `create()` never writes `cost_per_unit`/`total_cost` onto `tb_stock_out_detail` (both stay at their schema default of `0`); the actual cost is picked automatically at write time by the ledger (FIFO: oldest layers first; Average: current BU average), independent of anything the client sent.
- **No lot-picking UI.** Neither the Stock-In nor Stock-Out screen exposes a lot number, expiry date, or lot-selection control anywhere in the form. Lot identity is generated mechanically by the ledger — inbound lots as `ADI-YYYY-MM-NNNN`, outbound consumption lots as `ADO-YYYY-MM-NNNN` — the same system-generated pattern used by every other inventory-transaction-writing module.
- **Location scope.** The location picker (`LookupUserLocation`) is filtered client-side to `INVENTORY_TYPE.INVENTORY` and `INVENTORY_TYPE.CONSIGNMENT` location types. The backend's header validation (`StockInLogic.validateAndEnrichHeader` / `StockOutLogic.validateAndEnrichHeader`) only confirms the `location_id` exists — it does not re-check the location's type — so this restriction is enforced by the UI, not the server.
- **Date-within-period.** The date field is validated client-side (Zod) against the current period's `start_at`/`end_at` window from `useProfile()`. No equivalent period check exists in `StockInService.create()` / `StockOutService.update()` on the backend for this pass's read of the source.
- **Optimistic concurrency.** Both `doc_version` (header) and each line's own `doc_version` are checked on update — the Prisma `where` clause on the update call includes `doc_version`, so a stale write fails rather than silently overwriting a concurrent edit.

## 4. Roles and Personas

The code does not distinguish a Store Keeper from an Inventory Controller for this module: the nav entry, the create/edit screens, and the list all gate on the single generic `inventory_management.view` permission, and there is no workflow stage, approval queue, or `enum_stage_role` assignment anywhere in `stock-in.service.ts` / `stock-out.service.ts`. The wiki keeps two persona pages for readability, but both describe the same undifferentiated screen:

| Role | Realistic scope |
|------|----------------|
| Store Keeper / whoever enters the document | Opens **Add Stock-In** / **Add Stock-Out**, picks reason + location, enters lines, clicks Save or Submit — either button posts to the ledger immediately. |
| Inventory Controller | Same create screen, plus the read-only historical view (list, detail, print) — since Edit/Void are unreachable in the UI for any persisted document (§ 1), day-to-day "review" here means reading the list/print output, not approving anything in-app. |

A dedicated Finance persona, a System Administrator config workbench, and an Auditor read-scope were previously documented for this module; no matching route, component, permission key, or backend endpoint was found for any of them (`enum_stage_role` = `{create, approve, purchase, issue, view_only}` has no `finance` member, and there is no workflow orchestrator call anywhere in this module's service code). See [03 — User Flow — Finance](/en/inventory/inventory-adjustment/03-user-flow-finance) and [03 — User Flow — Audit / Config](/en/inventory/inventory-adjustment/03-user-flow-audit-config) for the correction notice.

## 5. Related Modules

**Cross-module flow:**
- [inventory](/en/inventory/inventory) — every stock-in/stock-out write calls the shared `InventoryTransactionService` (`executeAdjustmentIn` / `executeAdjustmentOut`) that also backs GRN, SR, and period-end
- [physical-count](/en/inventory/physical-count) — count completion creates `tb_stock_in` (overage) / `tb_stock_out` (shortage) rows directly at `completed`, with no reason code; verify this module's own ledger-linkage claim during that module's pass
- [costing](/en/inventory/costing) — FIFO layer creation on Stock-In, FIFO consumption / weighted-average recompute on Stock-Out

**Master configuration:**
- [master-data/adjustment-type](/en/inventory/master-data/adjustment-type) — reason-code master (`code`, `name`, direction, `is_active`) referenced by `adjustment_type_id`
- [master-data/location](/en/inventory/master-data/location) — the location whose balance the adjustment moves

## 6. Reference Sources

- Concepts: `../carmen/docs/inventory-adjustment/`
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/inventory-adjustment/`
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/stock-in/`, `.../stock-out/`, `.../inventory-transaction/`
- API contracts: no `../carmen-turborepo-backend-bruno/` collection exists for `stock-in`/`stock-out`/`inventory-adjustment` — verified directly against the backend controllers instead
- E2E tests: no dedicated inventory-adjustment spec exists in `../carmen-inventory-frontend-e2e/`; `031-adjustment-type.spec.ts` covers only the reason-code master-data screen

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
- [Wastage Reporting](/en/inventory/inventory-adjustment/wastage-reporting) — a separate, mock-data-only screen under Store Operations; cross-referenced here, not a variant of Stock-Out.
