---
title: Inventory — Test Scenarios — Store Keeper
description: Store Keeper's test cases for the read-only Transaction Log — filters, posting verification, and known quirks.
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, test-scenarios, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — Test Scenarios — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **Module:** [inventory](/en/inventory/inventory) &nbsp;·&nbsp; **Surface:** the read-only Transaction Log (`/inventory-management/transaction`)
> **Correction (2026-07-15):** the previous ~29 scenarios (threshold auto-approve, new-lot Controller routing, lot pickers, perishable expiry validation, SoD write-off blocks, negative-balance submit errors on manual documents) described a stock-in/stock-out authoring flow that does not exist in this module — no threshold or lot-entry UI exists anywhere, and lot numbers are system-generated. Manual adjustments belong to [inventory-adjustment](/en/inventory/inventory-adjustment)'s own test pages.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| SK-HP-01 | Verify a GRN posting on the ledger | A GRN was **saved** (`draft → saved`) with received lines; user holds `inventory_management.view` | 1. Open `/inventory-management/transaction`. 2. Search the GRN number. | One row: GRN type badge, `parent_document_no` = the GRN number, product/location names from the detail rows, green Qty In total, item count, total cost. |
| SK-HP-02 | Verify an SR issue | An SR completed its final approval stage | 1. Filter ref-type pill **SR**. 2. Locate the SR number. | Row with SR badge; red Qty Out; transfer rows show the source/destination locations from the detail lines. |
| SK-HP-03 | Verify a direct-location receipt | A GRN line targeted a `location_type = direct` location | 1. Search the GRN number. 2. Open the row's quantities. | Both legs under one transaction: Qty In and Qty Out equal (receipt + automatic `ISS-…` issue); net effect zero. |
| SK-HP-04 | Summary cards reflect the filtered set | Ledger has mixed inbound/outbound rows | 1. Apply a date-range preset (e.g. 7d). 2. Compare cards to the grid. | Four cards — total transactions (+ adjustment count), inbound units + cost, outbound units + cost, signed net change — recompute against the active filter (server-side `summary` in the list response). |
| SK-HP-05 | Filter combination | Rows across several locations/categories | 1. Set Location + Category lookups + direction Inbound. 2. Clear via the active-filter bar. | Grid narrows per filter; active-filter chips render; **Clear all** resets URL-backed state. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour |
| - | -------- | ------------------ |
| SK-PERM-01 | User with `inventory_management.view` opens the ledger | **Allow.** List renders read-only. |
| SK-PERM-02 | Any user attempts to modify a transaction | **Deny by absence.** No create/edit/delete affordance exists in the UI and no update endpoint exists on the API — the ledger is append-only by construction, not by a guard message. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected |
| - | -------- | ------- | -------- |
| SK-VAL-01 | Outbound source document exceeds balance | An SR issue / adjustment-out for more than available | Source module surfaces `` `Insufficient stock. Requested: <X>, Available: <Y>` ``; no ledger rows written. |
| SK-VAL-02 | Backdated source document | Document dated in a closed period | **No error** — the movement posts into the current open period (`resolveCurrentPeriod`); the ledger row's period stamp differs from the document date. |
| SK-VAL-03 | PC ref-type pill | Select the **PC** pill | Returns no rows — `physical_count` is not an `enum_inventory_doc_type` value (frontend/backing-enum mismatch, known quirk); count corrections appear as SI/SO. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| SK-EDGE-01 | Multi-product transaction row | One GRN with several lines | Product and Location cells render de-duplicated comma-joined name lists; the Items column counts detail rows. |
| SK-EDGE-02 | Cross-table sort | Sort by document no / product / location | These are post-resolve sorts: the backend loads all matching rows, resolves names, sorts in JS, then slices the page (`POST_SORT` path in `findAll`) — expect equal results but different latency vs native sorts (date, type). |
| SK-EDGE-03 | Split cost layers | A receipt whose `total_cost / qty` doesn't divide evenly at 2dp | `splitFifoCost` writes multiple `lot_index` rows under one `lot_no` so the layer costs reconcile exactly to the document total. |

## 5. References

- User flow: [03-user-flow-store-keeper](/en/inventory/inventory/03-user-flow-store-keeper).
- Screen reference: [transaction](/en/inventory/inventory/transaction).
- Business rules: [02-business-rules](/en/inventory/inventory/02-business-rules) — `INV_VAL_005`, `INV_VAL_008`, `INV_POST_001`–`INV_POST_003`.
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/transaction/`; backend list/search/sort logic in `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.ts` (`findAll`).
- E2E: no spec exercises this screen directly yet (manual/planned); posting effects assert via `501-grn.spec.ts` / `701-sr.spec.ts` / `601-cn.spec.ts`.
