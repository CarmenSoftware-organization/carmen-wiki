---
title: Inventory Adjustment — Test Scenarios — Inventory Controller
description: Test cases for reviewing drafts, committing, removing/voiding, and reading completed documents — no approval queue exists.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory-adjustment, test-scenarios, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Test Scenarios — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller (same permission/screen as Store Keeper) &nbsp;·&nbsp; **Module:** [inventory-adjustment](/en/inventory/inventory-adjustment)
> **Categories:** Happy Path (review, commit, void) &nbsp;·&nbsp; Edge Case
> **Executable coverage:** none automated — manual catalog `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (TC-IADJ-01xxxx list, TC-IADJ-02xxxx detail/read-only, TC-IADJ-06xxxx void/commit)

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| IC-HP-01 | Read the merged list | Drafts and completed Stock-Ins and Stock-Outs exist | 1. Open the list. 2. Filter `adj_type` / status / date / search. | Both types merged by the gateway's `inventory-adjustments` service (fetch-all from both upstreams, sort, paginate in memory); status shown as icon + label (`draft` / `completed`; `voided` rows are soft-deleted and absent). |
| IC-HP-02 | Commit a Store Keeper's draft | A draft Stock-Out; on-hand sufficient | 1. Open the draft. 2. **Commit** → confirm. | `PATCH /stock-outs/{id}/commit` → `completed`; ledger rows written; returns to the list. |
| IC-HP-03 | Void a posted document via API | Completed Stock-In `P-1 qty 10` at `LOC-A`; on-hand ≥ 10 | `DELETE /{bu}/stock-ins/{id}/void` `{ void_reason }` with a valid token | `voidStockIn`: already-voided check, on-hand check, reversing `executeAdjustmentOut` per posted line, `doc_status = voided`, `deleted_at` set, `info.void_reason` stored; the document leaves list/detail. |
| IC-HP-04 | Print a posted document | Any `completed` document | Detail → **Print** | `GET /stock-ins/{id}/print-viewer` (FastReport); the button renders in view mode (`canPrint = isView && !!id`). |
| IC-HP-05 | Read stock movements | Any `completed` document | Detail → stock-movements panel | `GET /{id}/stock-movements` returns one line per posted detail with lot, qty, cost and `transaction_type` (`adjustment_in` / `adjustment_out`). |
| IC-HP-06 | Void with insufficient on-hand | Completed Stock-In `qty 10`; on-hand since dropped to 4 | Direct void call | Rejected: `Cannot void: product P-1 has insufficient on-hand qty (4) at this location to reverse 10`. |
| IC-HP-07 | Void an already-voided document | `doc_status = voided` | Direct void call | 400 `Stock in is already voided` / `Stock out is already voided`. |

## 2. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| IC-EDGE-01 | Void button on a completed document | Open a completed document | No **Edit** (`isView && !isReadOnly` false) and therefore no **Void** (`canVoid = isEdit && …`); reversal is API-only. |
| IC-EDGE-02 | Remove a completed document | Removal call via API (the detail view hides the button once `isReadOnly`) | 400 `Cannot delete a completed Stock In — inventory has already been adjusted`. |
| IC-EDGE-03 | `In Progress` status filter | Select `In Progress` in the list filter | Returns nothing — no code path ever sets `in_progress` on `tb_stock_in`/`tb_stock_out`. |
| IC-EDGE-04 | Physical-count rows in the list | A physical count was submitted with variances | Its `tb_stock_in`/`tb_stock_out` rows appear as `completed` with no reason and **no stock movements** (never posted). |
| IC-EDGE-05 | Wastage write-off rows in the list | `POST /wastage-reporting` was called | One `completed` Stock-Out per location with the caller's reason; stock movements show `adjustment_out` from the named lots. |
| IC-EDGE-06 | Stale `doc_version` | Two sessions edit the same draft | Second save/commit fails on the `doc_version` mismatch; reload and retry. |

## 3. References

- Parent overview: [04-test-scenarios](/en/inventory/inventory-adjustment/04-test-scenarios).
- User flow: [03-user-flow-inventory-controller](/en/inventory/inventory-adjustment/03-user-flow-inventory-controller).
- Business rules: [02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) `ADJ_POST_002`–`ADJ_POST_006`, `ADJ_VAL_010`–`ADJ_VAL_015`.
- Cross-link: [inventory](/en/inventory/inventory) — the ledger effect of both commit and void; [inventory/period-end](/en/inventory/inventory/period-end) — drafts block Start Period Close.
