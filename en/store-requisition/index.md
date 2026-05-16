---
title: Store Requisition
description: Internal request to draw stock from a warehouse or central store to a consuming location (kitchen, bar, outlet).
published: true
date: 2026-05-16T09:00:00.000Z
tags: store-requisition, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Store Requisition

## 1. Overview

A **Store Requisition (SR)** is an internal document that one location uses to draw stock from another — typically a consuming outlet (kitchen, bar, restaurant, banquet) requesting goods from a central or main store. Each SR carries a header (reference number, date, requesting/source location, destination location, movement type, description, status, totals) and one or more item lines that specify the product, unit of measure, requested quantity, approved quantity, issued quantity, unit cost, and line total. The movement type — `Issue` (consumption to a direct-cost destination) or `Transfer` (location-to-location inventory move) — drives both the stock-movement records and the journal entries that posting generates.

SRs progress through a controlled lifecycle: `Draft` (editable, no impact) → `In Process` (submitted for approval) → `Approved` (approver may reduce requested quantities or reject lines) → `Issued` (source location commits stock OUT and the system writes the stock-movement record) → `Received` / `Complete` at the destination, or `Reject` / `Void` for terminal cancellations. The flow supports partial fulfillment at the line level, so a 10-unit request may be issued as 8 with the remainder rejected or back-ordered, and every transition is logged with user, timestamp, and notes for audit.

The SR module is the system of record for internal stock movement between locations. It enforces approval routing, reserves inventory once approved, validates availability at the source before issue, records the OUT movement at source and the IN movement at destination on transfer, and generates the cost-allocation journal entries that move expense from the central store's inventory account to the consuming outlet's cost centre.

## 2. Business Context

In a hospitality operation, the central store buys and holds inventory in bulk, but the cost of goods actually consumed must land on the outlet that consumed them — the kitchen, the bar, the banquet operation. The Store Requisition is the control that lets the central store release stock to a consuming location while creating the paper trail that attributes the cost to the right cost-centre. Without this control, food cost reporting per outlet is impossible; with it, every issued ingredient is traceable from store shelf to plate, and every outlet manager can be held accountable for the cost they draw against budget.

The approval workflow exists because internal stock is real money. Outlets do not get to pull from the central store at will — requests are reviewed against operational need, par levels, current on-hand at the source, and budget. Approvers can trim requested quantities before issue, reject lines that are not justified, or return the document with a comment. This both prevents over-issue (which inflates outlet cost or leaves the store short for other outlets) and creates segregation of duties between the staff requesting the stock and the staff releasing it.

Financially, every posted issuance generates journal entries that credit the source location's inventory account and either debit the destination's inventory account (for a `Transfer`) or debit the destination's consumption expense account on its cost-centre (for an `Issue`). Costing uses the source location's current method — weighted-average or FIFO — so the value moved is consistent with how the source values its remaining stock, and food-cost reporting per outlet rolls up cleanly from the SR-driven journal entries.

## 3. Key Concepts

- **Source Location (Requested From)**: The location that holds the stock being drawn — typically the main store or a central warehouse. Stored on the header as `movement.source` / `movement.sourceName`. The source's costing method (weighted-average or FIFO) determines the unit cost applied to each issued line, and availability at the source is validated both at creation (`SR_CRT_006`) and again at the moment of issue to prevent negative stock.
- **Destination Location (Request To)**: The consuming or receiving location — kitchen, bar, outlet, or another inventory store. Stored as `movement.destination` / `movement.destinationName`. The destination's `locationType` (`direct` for cost-centre consumption, `inventory` for an onward inventory holding) is what gates the allowed movement type: `Issue` requires a direct-cost destination, `Transfer` requires an inventory destination.
- **Movement Type (Issue vs Transfer)**: `Issue` posts a single stock OUT at source and routes the value to the destination's consumption expense account — used when stock leaves inventory and is immediately consumed (kitchen pull, bar pull). `Transfer` posts a stock OUT at source and a paired stock IN at destination — used when stock physically moves between two inventory-holding locations without yet being consumed. The choice determines which journal entries are written and which downstream documents (e.g. a paired GRN) may be involved.
- **Approval Workflow**: SRs are routed for approval based on configurable rules (role, value threshold, location). Approvers can `Approve`, `Reject` (with mandatory reason), `Split & Reject` (partially approve), or `Send Back` for correction. Approvers may modify `qtyApproved` downward from `qtyRequired` but never above it. Approval history — actor, action, timestamp, comment — is persisted for audit, and approval can be delegated.
- **Requested vs Approved vs Issued Quantity**: Three quantities per line tell the whole story. `qtyRequired` is what the outlet asked for; `qtyApproved` is what the approver authorised (≤ `qtyRequired`); `qtyIssued` is what the store keeper actually released at fulfillment (≤ `qtyApproved`). These three numbers, taken across many SRs, drive variance analysis and supply-planning decisions.
- **Variance (Requested − Issued)**: The gap between what was requested and what was actually issued, captured per line. Variance arises from approver trim-down, source stock-out at issue time, or partial fulfillment. Tracking variance over time reveals chronic over-requesting, supply shortfalls, and outlets whose requisition discipline needs review.
- **Cost Center**: The accounting bucket that the issued cost lands on at the destination — typically tied to the destination outlet (Kitchen, Banquet, Bar XYZ). The cost-centre is stamped on each journal entry line so monthly food-cost reports per outlet roll up from SR postings without manual allocation.
- **Stock Movement Record**: Every issued line writes a `StockMovement` row capturing `commitDate`, `postingDate`, source and destination location, movement type, `inQty` / `outQty`, `unitCost`, `totalCost`, lot detail (for lot-tracked items), and a reference back to the originating SR. This is the immutable record the inventory sub-ledger reconciles against.
- **Journal Entry / Cost Allocation**: Posting an SR generates `JournalEntry` rows that credit the source's inventory GL account and debit either the destination's inventory account (Transfer) or the destination's consumption expense account on its cost-centre (Issue). Entries must balance (debits = credits) and are blocked if the posting date falls in a closed period.
- **Lot Tracking**: For lot-controlled items, the SR records which lot(s) were issued so expiry, recall, and lot-cost traceability are preserved end-to-end from receipt through consumption.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Outlet Manager / Requester | Identifies stock needs at the consuming location, creates the SR, adds items with requested quantities and required dates, attaches supporting notes, and submits the document for approval. Tracks status until receipt at the outlet. |
| Approver / Department Head | Reviews submitted requisitions against operational need, par levels, and source availability; approves, trims `qtyApproved` down from `qtyRequired`, rejects lines with a reason, splits a request, or sends it back for correction. Approval signature is persisted for audit. |
| Store Keeper / Fulfiller | Receives approved requisitions at the source location, picks the items, records `qtyIssued` per line (which may be less than `qtyApproved` if stock is short), commits the stock-movement, and releases the goods. May select specific lots for lot-controlled items. |
| Receiver | Confirms physical receipt of the issued goods at the destination, flags discrepancies between issued and received quantities, and closes out the requisition. |
| Inventory Controller / Manager | Oversees the entire SR flow, monitors variance and partial-fulfillment patterns, reconciles inventory sub-ledger against GL postings, manages approval thresholds, and signs off on period-end activity. |
| Finance Team | Verifies cost-centre mapping and journal entries, reconciles outlet food-cost reports against SR postings, and ensures cost allocation between departments is accurate at period close. |

## 5. Related Modules

**Cross-module flow:**
- [[inventory]] — issuing a requisition posts a stock OUT movement at source and a stock IN movement at destination (or a single OUT for consumption)
- [[costing]] — issued quantities are costed at the source location's current cost
- [[recipe]] — recipes may auto-generate requisitions for ingredients needed
- [[good-receive-note]] — inter-location transfers may use a paired SR + GRN

**Master configuration:**
- [[master-data/unit]] — unit of measure for each requisition line
- [[master-data/location]] — source (issuing) and destination (receiving) locations on the requisition header
- [[master-data/department]] — requesting department / cost-centre the issued cost lands on
- [[system-config/workflow]] — approval workflow definitions for requisition authorization
- [[system-config/dimension]] — analytical dimensions stamped on the issuance journal entries
- [[system-config/running-code]] — SR document number sequencing
- [[access-control/user-location]] — restricts source and destination locations a user can transact between
- [[reporting-audit/activity]] — requisition status-transition and approval-history log for audit

## 6. Reference Sources

- Concepts: `../carmen/docs/store-requisitions/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) — Prisma entities (`tb_store_requisition`, `tb_store_requisition_detail`, comment tables), enums (`enum_doc_status`, `enum_sr_type`), relationships, and divergences from carmen/docs.
- [02 — Business Rules](./02-business-rules.md) — Validation (`SR_VAL_*`), calculation (`SR_CALC_*`, quantity invariant), authorization (`SR_AUTH_*`, SoD), posting (`SR_POST_*`, single posting event at `in_progress → completed`), and cross-module rules (`SR_XMOD_*`).
- [03 — User Flow](./03-user-flow.md) — Document lifecycle overview and persona-specific flow files:
  - [Requester](./03-user-flow-requester.md) — Outlet Manager: identifies needs, creates SR, submits.
  - [Approver](./03-user-flow-approver.md) — Department Head: reviews, trims, rejects, sends back.
  - [Fulfiller](./03-user-flow-fulfiller.md) — Store Keeper: picks, records `issued_qty`, selects lots, commits.
  - [Receiver](./03-user-flow-receiver.md) — Destination representative: acknowledges receipt, flags discrepancies.
  - [Audit / Config](./03-user-flow-audit-config.md) — Inventory Controller, Finance, Sysadmin, Auditor oversight.
- [04 — Test Scenarios](./04-test-scenarios.md) — Cross-persona scenarios + Playwright mapping, with per-persona drill-downs:
  - [Requester scenarios](./04-test-scenarios-requester.md)
  - [Approver scenarios](./04-test-scenarios-approver.md)
  - [Fulfiller scenarios](./04-test-scenarios-fulfiller.md)
  - [Receiver scenarios](./04-test-scenarios-receiver.md)
  - [Audit / Config scenarios](./04-test-scenarios-audit-config.md)
