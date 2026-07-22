---
title: Costing — Test Scenarios — Inventory Controller (correction)
description: Correction page — the Inventory Controller test suite previously documented here targeted a cost-pick-preview adjustment-approval queue that does not exist.
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — Test Scenarios — Inventory Controller (correction)

> **At a Glance**
> **Status:** corrected 2026-07-22 — the scenarios previously on this page (cost-pick-preview review on adjustment approval, new-lot cost-basis vs vendor-pricelist tolerance check, Finance-escalated variance investigation, cost-anomaly dashboard triage) targeted surfaces with **no source backing** and were removed rather than re-fabricated.

## 1. Why these scenarios were removed

- **No approval queue exists for `tb_stock_in` / `tb_stock_out` at all.** [inventory-adjustment](/en/inventory/inventory-adjustment) § 1 (already verified) found that `StockInService.create()` / `StockOutService.create()` post unconditionally — `doc_status = completed` is written in the same call that creates the document, regardless of which button the client sends. There is no draft state left for any approver to review.
- **No "cost-pick preview" screen exists** in the stock-in/stock-out forms.
- **No Inventory-Controller-vs-Store-Keeper distinction exists in this module** — both gate on the single generic `inventory_management.view` permission.
- **No Finance persona exists to escalate a variance to** — see [03-user-flow-finance](./03-user-flow-finance.md) (correction).

This mirrors the confirmed-fabricated approval-queue findings on [inventory-adjustment](/en/inventory/inventory-adjustment)'s own resync pass and the identical correction pattern applied where a module claimed a review step that turned out to be a creation-is-posting flow.

## 2. Where the testable behaviour lives now

| Formerly tested here | Real test location |
|---|---|
| Cost-pick preview / adjustment approval | No approval step exists — see [inventory-adjustment](/en/inventory/inventory-adjustment) § 1 |
| FIFO / Average cost-pick arithmetic | [04-test-scenarios](./04-test-scenarios.md) Scenarios 1, 2, 9, 10, 11 |
| Period-end review checklist + close | [inventory/04-test-scenarios-inventory-controller](/en/inventory/inventory/04-test-scenarios-inventory-controller) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-adjustment/` (`stock-in.service.ts`, `stock-out.service.ts`).
- Parent overview: [04-test-scenarios](./04-test-scenarios.md); user-flow counterpart: [03-user-flow-inventory-controller](./03-user-flow-inventory-controller.md).
