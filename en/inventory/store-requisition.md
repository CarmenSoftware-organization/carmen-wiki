---
title: Store Requisition
description: Internal request to draw stock from a warehouse or central store to a consuming location (kitchen, bar, outlet).
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Store Requisition

> **At a Glance**
> **Module purpose:** Internal stock movement document — `Issue` (to a direct-cost destination) or `Transfer` (location-to-location) with approval workflow and three-quantity tracking (requested / approved / issued) &nbsp;·&nbsp; **Audience:** Outlet Manager / Requester, Approver, Store Keeper / Fulfiller &nbsp;·&nbsp; **Key entities/tables:** `tb_store_requisition`, `tb_store_requisition_detail`, `tb_inventory_transaction`, `enum_doc_status`, `enum_sr_type` &nbsp;·&nbsp; **Sub-pages:** 16
> ⚠️ **This pass found `StockMovement` and `JournalEntry` were documented as SR-owned tables — neither exists in Prisma; stock movement and journal-entry data live on the shared `tb_inventory_transaction` family (see [01-data-model.md](/en/inventory/store-requisition/01-data-model) §5). It also found the "Receiver" persona, GL/journal-entry posting, segregation-of-duties enforcement, approval delegation/value-thresholds, and store-keeper lot selection have no matching code — see the corrected persona pages and the module progress-log Discrepancy entry.

![Store Requisition screen](/screenshots/store-requisition/index.png)

![Store Requisition detail screen](/screenshots/store-requisition/detail.png)

## 1. Overview

A **Store Requisition (SR)** is an internal document that one location uses to draw stock from another — typically a consuming outlet (kitchen, bar, restaurant, banquet) requesting goods from a central or main store. Each SR carries a header (reference number, date, requesting/source location, destination location, movement type, description, status) and one or more item lines that specify the product, unit of measure, requested quantity, approved quantity, and issued quantity. There are no monetary columns on the SR header or line — unit cost and line total are read from the linked inventory transaction at display time (see [01-data-model.md](/en/inventory/store-requisition/01-data-model) §5). The movement type — `Issue` (consumption to a direct-cost destination) or `Transfer` (location-to-location inventory move) — drives which stock-movement records are written.

SRs progress through a confirmed lifecycle of `draft` → `in_progress` → `completed` (`enum_doc_status`, shared with several other modules). The single approver/issuer-facing action that ends the document early sets `doc_status = voided` directly — there is no separate `cancelled` outcome reachable by any current code path (the enum defines a `cancelled` value, but no SR service method assigns it — see [01-data-model.md](/en/inventory/store-requisition/01-data-model) §5 and [02-business-rules.md](/en/inventory/store-requisition/02-business-rules) §5). The flow supports partial fulfillment at the line level, so a 10-unit request may be issued as 8, and every transition is logged with user, timestamp, and notes for audit.

The SR module is the system of record for internal stock movement between locations. On the final workflow-stage advance (whichever stage that is — the same generic "approve" action is used at every stage, including the stage a store keeper acts at), it validates live availability at the source, records the OUT movement at source and, for `Transfer`, the paired IN movement at destination, through the shared `tb_inventory_transaction` family. No `JournalEntry` or `StockMovement` table exists in this module — see the correction note at the top of this page.

## 2. Business Context

In a hospitality operation, the central store buys and holds inventory in bulk, but the cost of goods actually consumed must land on the outlet that consumed them — the kitchen, the bar, the banquet operation. The Store Requisition is the control that lets the central store release stock to a consuming location while creating the paper trail that attributes the cost to the right cost-centre. Without this control, food cost reporting per outlet is impossible; with it, every issued ingredient is traceable from store shelf to plate.

The approval workflow exists because internal stock is real money. Outlets do not get to pull from the central store at will — requests are reviewed against operational need and current on-hand at the source. Approvers can trim requested quantities before issue, reject lines that are not justified, or return the document with a comment. This design intent is meant to prevent over-issue and to separate the staff requesting the stock from the staff releasing it — but no segregation-of-duties check (requester ≠ approver, approver ≠ issuer) was found anywhere in the current backend or frontend code; treat SoD as a documented intent, not an enforced control, until confirmed otherwise.

Costing uses the source location's current method — weighted-average or FIFO — so the value moved is consistent with how the source values its remaining stock. GL/journal-entry posting from SR issuance is not confirmed: a repo-wide search for `journal`, `ledger`, and related terms in the SR module and its inventory-transaction dependency returned no hits.

## 3. Key Concepts

- **Source Location (Requested From)**: The location that holds the stock being drawn — typically the main store or a central warehouse. Stored on the header as `from_location_id` / `from_location_name`. The source's costing method (weighted-average or FIFO) determines the unit cost applied to each issued line, and availability at the source is validated at submit and again at the moment of the final workflow-stage advance to prevent negative stock.
- **Destination Location (Request To)**: The consuming or receiving location — kitchen, bar, outlet, or another inventory store. Stored as `to_location_id` / `to_location_name`. The destination's `location_type` (`direct` for cost-centre consumption, `inventory` for an onward inventory holding) is what gates the allowed movement type: `Issue` requires a direct-cost destination, `Transfer` requires an inventory destination.
- **Movement Type (Issue vs Transfer)**: `Issue` posts a single stock OUT at source — used when stock leaves inventory and is immediately consumed (kitchen pull, bar pull). `Transfer` posts a stock OUT at source and a paired stock IN at destination — used when stock physically moves between two inventory-holding locations without yet being consumed.
- **Approval Workflow**: SRs are routed through one or more stages defined by the tenant's `tb_workflow` configuration (the same generic workflow engine PR/PO/GRN use). Approvers can approve a line in full, trim it, reject it (bundled into the same approve call as other approved lines), or send the whole document back for correction. A separate whole-document reject action is also available, gated only by "every line is marked reject" in the current form — it sets `doc_status = voided` directly, not a distinct `cancelled` state. No value-threshold-based routing, delegation, or SLA-timeout escalation was found in current source — treat any claim of these as unconfirmed.
- **Requested vs Approved vs Issued Quantity**: Three quantities per line tell the whole story. `requested_qty` is what the outlet asked for; `approved_qty` is what the approver authorised (≤ `requested_qty`); `issued_qty` is what was actually released at the final stage (≤ `approved_qty`). These three numbers, taken across many SRs, drive variance analysis.
- **Variance (Requested − Issued)**: The gap between what was requested and what was actually issued, captured per line. Variance arises from approver trim-down or partial fulfillment. Tracking variance over time can reveal chronic over-requesting or supply shortfalls, though no dedicated variance-dashboard screen was found in this pass.
- **Lot Tracking**: For lot-controlled items, lot selection at consumption is computed automatically by FIFO (`getAvailableFifoLots` / `consumeFifoLots` in the inventory-transaction service) — no lot-selection UI was found in the SR frontend, so this is not a manual store-keeper action.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Outlet Manager / Requester | Identifies stock needs at the consuming location, creates the SR, adds items with requested quantities and required dates, attaches supporting notes, and submits the document for approval. Tracks status until fulfilment. |
| Approver / Department Head | Reviews submitted requisitions against operational need and source availability; approves, trims `approved_qty` down from `requested_qty`, rejects lines, or sends it back for correction. Per-line signature is persisted for audit. |
| Store Keeper / Fulfiller | Acts at whichever workflow stage is tagged for issuance — the same generic approve action the Approver uses — and records `issued_qty` per line (which may be less than `approved_qty` if stock is short). There is no dedicated "commit" endpoint distinct from approve, and no lot-selection UI (lots are picked automatically by FIFO). |

No dedicated "Receiver", "Inventory Controller", or "Finance" backend role or workflow stage was found for this module — see [03-user-flow-receiver.md](/en/inventory/store-requisition/03-user-flow-receiver) and [03-user-flow-audit-config.md](/en/inventory/store-requisition/03-user-flow-audit-config) for the full correction.

## 5. Related Modules

**Cross-module flow:**
- [inventory](/en/inventory/inventory) — issuing a requisition posts a stock OUT movement at source and a stock IN movement at destination (or a single OUT for consumption)
- [costing](/en/inventory/costing) — issued quantities are costed at the source location's current cost
- [recipe](/en/inventory/recipe) — recipes may auto-generate requisitions for ingredients needed
- [good-receive-note](/en/inventory/good-receive-note) — inter-location transfers may use a paired SR + GRN

**Master configuration:**
- [master-data/unit](/en/inventory/master-data/unit) — unit of measure for each requisition line
- [master-data/location](/en/inventory/master-data/location) — source (issuing) and destination (receiving) locations on the requisition header
- [master-data/department](/en/inventory/master-data/department) — requesting department / cost-centre the issued cost lands on
- [system-config/workflow](/en/inventory/system-config/workflow) — approval workflow definitions for requisition authorization
- [system-config/dimension](/en/inventory/system-config/dimension) — analytical dimensions stamped on the requisition line
- [system-config/running-code](/en/inventory/system-config/running-code) — SR document number sequencing
- [access-control/user-location](/en/inventory/access-control/user-location) — restricts source and destination locations a user can transact between
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — requisition status-transition and approval-history log for audit

## 6. Reference Sources

- Concepts: `../carmen/docs/store-requisitions/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](/en/inventory/store-requisition/01-data-model) — Prisma entities (`tb_store_requisition`, `tb_store_requisition_detail`, comment tables), enums (`enum_doc_status`, `enum_sr_type`), relationships, and divergences from carmen/docs.
- [01a — Data Model — Comment Tables](/en/inventory/store-requisition/01a-data-model-comments) — Document-level and line-level comment / attachment tables and the `enum_comment_type` user/system tagging.
- [02 — Business Rules](/en/inventory/store-requisition/02-business-rules) — Validation (`SR_VAL_*`), calculation (`SR_CALC_*`, quantity invariant), authorization (`SR_AUTH_*`), posting (`SR_POST_*`, single posting event at the final workflow-stage advance), and cross-module rules (`SR_XMOD_*`).
- [03 — User Flow](/en/inventory/store-requisition/03-user-flow) — Document lifecycle overview and persona-specific flow files:
  - [Requester](/en/inventory/store-requisition/03-user-flow-requester) — Outlet Manager: identifies needs, creates SR, submits.
  - [Approver](/en/inventory/store-requisition/03-user-flow-approver) — Department Head: reviews, trims, rejects, sends back.
  - [Fulfiller](/en/inventory/store-requisition/03-user-flow-fulfiller) — Store Keeper: records `issued_qty` at the issuance stage (same generic approve action; lots are auto-selected, not chosen manually).
  - [Receiver](/en/inventory/store-requisition/03-user-flow-receiver) — **Corrected this pass:** no matching backend role or discrepancy-flag mechanism was found; see the page for what is and isn't confirmed.
  - [Audit / Config](/en/inventory/store-requisition/03-user-flow-audit-config) — **Corrected this pass:** no matching RBAC console, GL-verification, or SoD-relaxation config was found; see the page for what is and isn't confirmed.
- [04 — Test Scenarios](/en/inventory/store-requisition/04-test-scenarios) — Cross-persona scenarios + Playwright mapping, with per-persona drill-downs:
  - [Requester scenarios](/en/inventory/store-requisition/04-test-scenarios-requester)
  - [Approver scenarios](/en/inventory/store-requisition/04-test-scenarios-approver)
  - [Fulfiller scenarios](/en/inventory/store-requisition/04-test-scenarios-fulfiller)
  - [Receiver scenarios](/en/inventory/store-requisition/04-test-scenarios-receiver) — corrected this pass.
  - [Audit / Config scenarios](/en/inventory/store-requisition/04-test-scenarios-audit-config) — corrected this pass.
- [Stock Replenishment](/en/inventory/store-requisition/stock-replenishment) — the designed policy-driven counterpart to the manual SR flow (min/max/par thresholds on `tb_product_location` producing `tb_store_requisition` drafts); **the frontend screen is currently mock-data-driven and no backend/cron implementation was found** — see the page's implementation-status warning.
