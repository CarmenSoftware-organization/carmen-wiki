---
title: Good Receive Note (GRN)

description: The receiving document that records physical goods received against a purchase order and adds them to inventory.

published: true

date: 2026-06-09T16:26:48.000Z

tags: good-receive-note, inventory, carmen-software

editor: markdown

dateCreated: 2026-05-15T07:48:00.000Z

---

# Good Receive Note (GRN)

> **At a Glance**

> **Module purpose:** Records physical receipt of goods against a PO, posts stock-IN movements, updates costing, and creates AP entries (`Received` → `Committed` → `Voided`)  ·  **Audience:** Store Keeper / Receiver, Inventory Manager, Purchaser, Finance / AP  ·  **Key entities/tables:** `tb_good_receive_note`, `tb_good_receive_note_detail`, `InventoryStatus`, `JournalEntry`, FIFO lot layers  ·  **Sub-pages:** 12

![Good Receive Note (GRN) screen](/screenshots/good-receive-note/index.png)

![Good Receive Note (GRN) detail screen](/screenshots/good-receive-note/detail.png)

## 1. Overview
A **Good Receive Note (GRN)** is the document that formally records the physical receipt of goods from a vendor and writes them into inventory. Each GRN has a header — reference number, receipt date, vendor, delivery point, invoice number and date, currency and exchange rate, optional consignment/cash flags, and an extra-cost indicator — and one or more item lines. Each line carries the product, store location, ordered quantity (when sourced from a PO), received quantity, free-of-charge (FOC) quantity, unit price, discount, tax, lot information for traceable items, and a computed line total; the header rolls these into subtotal, discount, tax, extra costs, and grand-total figures in both transaction and base currencies.

GRNs follow a tightly bounded lifecycle: `Received` (also called Draft — editable, no stock or GL impact) → `Committed` (immutable, inventory and journal entries posted) → `Voided` (only available from the Received state; reverses the draft). Committing a GRN is the single event that mutates the world: it generates stock-IN movements per line, updates on-hand quantities and last cost on `InventoryStatus`, creates new FIFO cost layers or recomputes the weighted-average per the item's costing method, writes journal entries against accounts payable and inventory, and updates the source purchase order's remaining quantities. Once committed, the document is locked — corrections require a void of the source artefact or a compensating adjustment.

The GRN is the receiving end of the **three-way match** (PO ↔ GRN ↔ vendor invoice). It can be created from one or more open purchase orders (multi-PO consolidation is supported when vendor, currency, and terms agree) or manually for receipts that have no upstream PO. Partial receipts are first-class — the GRN tracks received vs. ordered per line and feeds remaining quantities back to the source PO, which moves to `Partial` until everything is received or cancelled, then to `Closed`. Vendor cancellations are recorded on the GRN, push a cancelled quantity back to the PO, and prevent further receiving once the PO is closed.

## 2. Business Context
The GRN is the control point where physical reality meets the books. Until receiving acknowledges the goods, a PO is only a commitment; once a GRN is committed, stock value is on the balance sheet, an accounts-payable liability is recognised, and the vendor invoice can be matched and paid. Hospitality operations run on tight food-cost margins and rely on this checkpoint to catch under-deliveries, over-deliveries, short-shipped lines, and price variances before they become inventory errors or overpayments. Mandatory invoice number + vendor uniqueness, required cost allocation before commit, role-segregated review, posting-only stock impact, and an immutable post-state exist to make every receipt explainable and to support clean three-way match against the eventual invoice.

The financial side mirrors this. Each committed GRN writes journal entries that debit inventory (or expense, for non-inventory items) for the received value plus any allocated extra costs (freight, duties, handling), credit accounts payable for the vendor obligation, and account for tax separately based on the line's tax-inclusive or tax-exclusive treatment. Multi-currency receipts dual-post in transaction and base currencies using a configurable exchange rate. Consignment receipts are tracked as `Consignment In` movements that don't affect owned-stock value, and non-inventory items skip stock impact entirely while still creating the AP entry.

Food-safety and quality control sit on top of all this. Perishable goods carry lot numbers (auto-generated or manually overridden) and expiry dates that travel with the stock layer, so subsequent FIFO consumption, expiry-driven write-offs, and recall events are all traceable to the original GRN. The receiving workflow can flag a delivery for quality inspection — accept, reject, or partially accept — with the reject quantities feeding back to vendor performance metrics. Variance on price between the PO and the receipt is surfaced for review against the vendor pricelist before commit.

## 3. Key Concepts
- **Receiving Lot**: A lot number assigned to each line of a lot-tracked item at receipt, linking the received stock to a specific batch with optional expiry date and FOC flag. The system auto-generates lot numbers in a configurable format (date components, item identifiers, sequential suffix) and allows manual override. Lot history is preserved end-to-end so FIFO consumption, expiry write-offs, and recall events trace back to the originating GRN.
- **Three-Way Match**: The reconciliation of three documents — the purchase order (what was ordered), the GRN (what was received), and the vendor invoice (what was billed) — to authorise vendor payment. The GRN is the receiving leg; matched quantities and prices unlock invoice approval, while variances (short shipment, over-billing, price mismatch) flag the invoice for AP review.
- **Partial Receipt**: A GRN that fulfils only part of an outstanding PO. Received quantities can be less than ordered, and the source PO is moved to `Partial` status with the remaining open quantity available for future GRNs. Multiple GRNs can be raised against the same PO until the PO is fully received or `Closed`.
- **Over/Under Receipt**: Quantity variance between PO and GRN. Under-receipt (received less than ordered) leaves the PO `Partial`; over-receipt (received more than ordered) is constrained by validation (`Received quantity cannot exceed ordered minus already-received minus cancelled`) and requires either a PO amendment upstream or rejection of the excess. Vendor cancellations are recorded as cancelled quantities that close out the remaining open balance.
- **Receipt Posting (Commit)**: The single event that updates stock and the GL. On commit, the system: (1) writes a stock-IN movement per line, (2) updates `InventoryStatus.QuantityOnHand`, `LastUnitCost`, and `TotalCost`, (3) creates new FIFO cost layers or recomputes `AverageCostTracking` per the item's costing method, (4) generates journal entries (debit inventory, credit AP, with separate tax and extra-cost treatment), (5) updates the source PO's remaining quantities, and (6) locks the GRN against further edits. Individual, batch, and end-of-period auto-commit modes are supported.
- **Quality Hold / Inspection**: An optional gate before commit where received items are inspected and may be accepted, rejected, or partially accepted. Rejected quantities are excluded from the stock IN and feed vendor-performance metrics; conditional acceptance is recorded with notes on the line. This is what keeps food-safety failures (broken seal, wrong temperature, damaged carton) out of inventory.
- **Extra Cost Allocation**: Landed-cost components (freight, handling, duties, third-party services) added to the GRN and allocated across line items by quantity or by amount. Allocated extras flow into the item's last-cost calculation — `Last Cost = (Net Amount + Extra Costs) / (Received Quantity + FOC Quantity)` — so inventory valuation reflects the true delivered cost rather than just the unit price.
- **FOC (Free of Charge)**: A receipt mode where vendor-supplied items arrive at zero price (samples, promotional bonus, replacement for damaged stock). FOC quantities are excluded from `Subtotal` and `Last Price` but included in `Last Cost` denominator and in lot quantities, so the average unit cost dilutes correctly without overstating receipt value.
- **Transaction Types**: Each GRN line resolves to one of three movement types on commit — `Stock In` (regular owned inventory, full impact on on-hand and valuation), `Consignment In` (vendor-owned stock held at the location, tracked separately, no owned-inventory or AP impact until consumed), or `Non-Inventory` (immediately expensed, no stock impact but full AP and tax treatment).

## 4. Roles and Personas
| Role | Responsibility |
| --- | --- |
| Store Keeper / Receiving Clerk | Receives the physical delivery at the dock, counts and inspects goods against the PO and the vendor delivery note, creates the GRN in Received (Draft) status, attaches packing slips and quality evidence, records lot numbers and expiry dates, and documents any discrepancies, short shipments, or rejected lines. |
| Store Manager / Inventory Manager | Reconciles the GRN against the actual stock received, oversees lot/batch tracking and storage-location assignment, monitors receipt patterns and variances, and commits individual GRNs or processes batch commits at end of shift or end of period. |
| Purchaser / Procurement Officer | Owns the upstream PO that the GRN is matched against, reviews receiving information for the POs they raised, investigates vendor performance issues (late, short, damaged, wrong item), and coordinates resolution with the vendor for variances. |
| Finance Team / AP Clerk | Verifies the GRN against the vendor invoice (three-way match), validates extra-cost allocation and tax treatment, adjusts and finalises GRN entries before AP posting, reconciles the inventory sub-ledger against the GL, and signs off on receipt activity at period close. |
| Department Manager | Reviews GRNs hitting the department's cost-centre, validates that received goods match what was ordered for the department, and monitors price variance against the vendor pricelist. |
| System Administrator | Maintains the lot-number generation format, configures user permissions and approval thresholds, manages tax codes, currency rates, and reason codes for cancellations and rejections, and oversees integration with PO, Inventory, Finance, and Vendor modules. |

## 5. Related Modules
**Cross-module flow:**

- [purchase-order](/en/inventory/purchase-order) — GRN is created against a PO; matched on receipt
- [inventory](/en/inventory/inventory) — receiving a GRN posts a stock IN movement
- [costing](/en/inventory/costing) — GRN unit costs feed FIFO lot records or update Weighted Average
- [vendor-pricelist](/en/inventory/vendor-pricelist) — GRN price variance is checked against the vendor pricelist
**Master configuration:**

- [master-data/vendor](/en/inventory/master-data/vendor) — vendor master referenced by GRN header
- [master-data/currency](/en/inventory/master-data/currency) — transaction currency and exchange rate for dual-posted receipts
- [master-data/tax-profile](/en/inventory/master-data/tax-profile) — tax codes applied to GRN lines
- [master-data/credit-term](/en/inventory/master-data/credit-term) — payment terms copied from vendor master onto the GRN
- [master-data/extra-cost-type](/en/inventory/master-data/extra-cost-type) — landed-cost components (freight, duties, handling) allocated across lines
- [master-data/delivery-point](/en/inventory/master-data/delivery-point) — receiving location where goods are physically accepted
- [master-data/unit](/en/inventory/master-data/unit) — unit of measure for received quantities
- [master-data/location](/en/inventory/master-data/location) — store location each line writes its stock-IN movement against
- [system-config/workflow](/en/inventory/system-config/workflow) — approval / commit workflow for GRN authorization
- [system-config/period](/en/inventory/system-config/period) — accounting period gate for GRN posting
- [system-config/running-code](/en/inventory/system-config/running-code) — GRN document number sequencing
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — GRN status-transition and amendment log for audit
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — packing slips, delivery notes, and quality evidence attached to each GRN

## 6. Reference Sources
- Concepts: `../carmen/docs/good-recive-note-managment/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module
- [01 — Data Model](/en/inventory/good-receive-note/01-data-model) — Entities, fields, relationships, and enums (Prisma-derived).
- [01a — Data Model — Comment Tables](/en/inventory/good-receive-note/01a-data-model-comments) — Document-level and line-level comment / attachment tables and the `enum_comment_type` user/system tagging.
- [02 — Business Rules](/en/inventory/good-receive-note/02-business-rules) — Validation, calculation, authorization, posting, and three-way-match rules.
- [03 — User Flow](/en/inventory/good-receive-note/03-user-flow) — Document lifecycle and persona index.
  - [Receiver](/en/inventory/good-receive-note/03-user-flow-receiver)
  - [Purchaser](/en/inventory/good-receive-note/03-user-flow-purchaser)
  - [Finance](/en/inventory/good-receive-note/03-user-flow-finance)
  - [Audit / Config](/en/inventory/good-receive-note/03-user-flow-audit-config)
- [04 — Test Scenarios](/en/inventory/good-receive-note/04-test-scenarios) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Receiver](/en/inventory/good-receive-note/04-test-scenarios-receiver)
  - [Purchaser](/en/inventory/good-receive-note/04-test-scenarios-purchaser)
  - [Finance](/en/inventory/good-receive-note/04-test-scenarios-finance)
  - [Audit / Config](/en/inventory/good-receive-note/04-test-scenarios-audit-config)