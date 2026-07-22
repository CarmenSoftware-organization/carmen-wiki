---
title: Costing — User Flow — Inventory Controller (correction)
description: Correction page — no cost-pick-preview adjustment-approval queue exists in the costing module; stock-in/stock-out post unconditionally on creation.
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, user-flow, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — User Flow — Inventory Controller (correction)

> **At a Glance**
> **Status:** corrected 2026-07-22 — the "adjustment approval queue with cost-pick preview" previously documented here (Store Keeper-initiated, Controller reviews FIFO/Average cost preview, approves or rejects) **does not exist in the product**.
> **What is real:** the only concrete Inventory-Controller-facing surface this engine plugs into is the period-end review/close, documented on [inventory/period-end](/en/inventory/inventory/period-end) and [inventory/03-user-flow-inventory-controller](/en/inventory/inventory/03-user-flow-inventory-controller).

## 1. What this page previously claimed, and why it was removed

An earlier draft described an Inventory Controller persona reviewing a "cost-pick preview" (the FIFO lot walk or the Average running cost) on every `tb_stock_in` / `tb_stock_out` document before approving it, cross-referencing new-lot costs against a vendor pricelist deviation tolerance, and running a proactive "cost-anomaly dashboard." Verification against current source found none of it:

- **No approval queue exists for stock-in / stock-out at all.** [inventory-adjustment](/en/inventory/inventory-adjustment) § 1 (already verified) found that **creation is posting**: `StockInService.create()` / `StockOutService.create()` write `doc_status = completed` unconditionally, in the same call that posts to the ledger — regardless of which button (Save vs Submit) the client sends. There is no reachable draft state, so there is nothing left in a reviewable pending state for any approver to act on.
- **No distinction between Store Keeper and Inventory Controller in this module.** The nav entry, the create/edit screens, and the list all gate on the single generic `inventory_management.view` permission; there is no workflow stage, approval queue, or `enum_stage_role` assignment anywhere in `stock-in.service.ts` / `stock-out.service.ts`.
- **No "cost-pick preview" screen exists.** The stock-in/stock-out forms show the fields the user enters (cost is user-editable on stock-in, hidden entirely on stock-out — the ledger picks it automatically at write time); there is no separate preview step showing which FIFO lots would be consumed before the document posts.
- **No adjustment-cost-basis-vs-vendor-pricelist tolerance check found in this module's code**, despite `tb_product.price_deviation_limit` being a real field (it is read elsewhere — see [product](/en/inventory/product)).

This mirrors the identical finding already confirmed in [inventory-adjustment/03-user-flow](/en/inventory/inventory-adjustment/03-user-flow) ("two undifferentiated screens... there is no approval action for this persona to perform, since nothing is ever left in a reviewable pending state").

## 2. Where the real behaviour lives

| Formerly claimed here | Actual mechanism | Page |
|---|---|---|
| Controller reviews cost-pick preview before approving an adjustment | Stock-in/stock-out post unconditionally on creation; there is nothing to approve | [inventory-adjustment](/en/inventory/inventory-adjustment) § 1 |
| Controller verifies new-lot cost against vendor pricelist tolerance | No such check found in this module's code | [inventory-adjustment/02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) |
| Controller investigates Finance-escalated valuation variance | No Finance persona exists to escalate from — see [03-user-flow-finance](./03-user-flow-finance.md) | — |
| Controller signs off pre-period-end variance review, then runs the close | Real: any user holding `inventory_management.period_end.execute` works the review checklist and clicks **Close period** | [inventory/03-user-flow-inventory-controller](/en/inventory/inventory/03-user-flow-inventory-controller) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-adjustment/` (`stock-in.service.ts`, `stock-out.service.ts` — `create()` posts unconditionally), `.../period-end/`.
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/inventory-adjustment/`, `.../period-end/`.
- Parent overview: [03-user-flow](./03-user-flow.md).
- Cross-link: [inventory-adjustment](/en/inventory/inventory-adjustment) — the module that actually owns the `tb_stock_in`/`tb_stock_out` documents this page's earlier draft mis-described.
- Cross-link: [inventory/03-user-flow-inventory-controller](/en/inventory/inventory/03-user-flow-inventory-controller) — the real period-end close flow.
