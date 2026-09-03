---
title: Good Receive Note (GRN)

description: The receiving document that records physical goods received against a purchase order and adds them to inventory.

published: true

date: 2026-07-15T00:00:00.000Z

tags: good-receive-note, inventory, carmen-software

editor: markdown

dateCreated: 2026-05-15T07:48:00.000Z

---

# Good Receive Note (GRN)

> **At a Glance**

> **Module purpose:** Records physical receipt of goods against a PO, posts stock-IN movements, and updates FIFO / average costing (`draft` → `saved` → `committed`, or `voided`)  ·  **Audience:** Store Keeper / Receiver, Inventory Manager, Purchaser  ·  **Key entities/tables:** `tb_good_received_note`, `tb_good_received_note_detail`, `tb_good_received_note_detail_item`, `tb_inventory_transaction`, FIFO / average-cost layers  ·  **Sub-pages:** 13
>
> **Corrected this pass (2026-07-15):** the previous version of this page described a 3-state lifecycle (`Received`/`Draft → Committed → Voided`) with Committing as "the single event that mutates the world" and creating AP/journal entries as part of a PO↔GRN↔invoice **three-way match**. Neither matches current source. The real status enum (`enum_good_received_note_status`) has **four** values — `draft`, `saved`, `committed`, `voided` — and the actual mutating event is the **`draft → saved` transition** (`GoodReceivedNoteLogic.save()` in `good-received-note.logic.ts`): it is `save()`, not `commit()`, that creates the `tb_inventory_transaction` rows, writes the FIFO / average-cost layers, and advances the source PO's `received_qty`. `commit()` (`saved → committed`) only flips `doc_status` and locks the document — no further inventory, PO, or GL side effect was found in the current backend. A repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `journal`, `ledger`, `three-way`, `vendor_invoice`, and `tb_invoice` returned **zero hits** — there is no vendor-invoice capture, AP-journal-posting, or three-way-match feature in current source (mirrors the same finding already confirmed for the `purchase-order` module). Treat any "AP accrual", "GRN Clearing", or "three-way match" claim elsewhere on this page or its sub-pages as unconfirmed / not implemented unless flagged otherwise.

![Good Receive Note (GRN) screen](/screenshots/good-receive-note/index.png)

![Good Receive Note (GRN) detail screen](/screenshots/good-receive-note/detail.png)

## 1. Overview
A **Good Receive Note (GRN)** is the document that formally records the physical receipt of goods from a vendor and writes them into inventory. Each GRN has a header — GRN number, receipt date, vendor, invoice number and date, currency and exchange rate, credit-term snapshot, a `post_type` (`ap` / `consignment` / `cash`), and an extra-cost indicator — and one or more item lines. Each line identifies the product and store location; the actual quantities, prices, and tax live on child receipt-event rows (`tb_good_received_note_detail_item`) so a single line can span multiple receipt events (split deliveries, mixed lots, paid-plus-FOC bundles). Each receipt event carries ordered quantity (when sourced from a PO), received quantity, free-of-charge (FOC) quantity, unit price, discount, tax, and a computed line total; the header rolls these into net, tax, and grand-total figures in both transaction and base currencies. Lot number and expiry date are **not** stored on the GRN line itself — they live on the linked `tb_inventory_transaction_detail` row, reached via the receipt-event's `inventory_transaction_id` (see [01-data-model.md](/en/inventory/good-receive-note/01-data-model) §5).

GRNs follow a four-state lifecycle on `enum_good_received_note_status`: `draft` (editable, no stock or GL impact) → `saved` (line entry complete) → `committed` (locked). `voided` is reachable from either `draft` or `saved` and is administrative — no committed GRN can be voided through the UI (the Void button is only rendered when the GRN is not yet committed). The mutating event is **`draft → saved`**, not `saved → committed`: `GoodReceivedNoteLogic.save()` is what writes the `tb_inventory_transaction` rows, creates the FIFO cost layers or recomputes the weighted average, and advances the source purchase order's `received_qty` (and `po_status`) — all inside one transaction. The subsequent `commit()` call (`saved → committed`) only updates `doc_status` and locks the document against further edits; no additional inventory, PO, or GL side effect was found in the current backend for the commit step itself. Once `committed`, the document is locked — corrections require a compensating adjustment in [inventory-adjustment](/en/inventory/inventory-adjustment) or a `tb_credit_note` against the GRN.

The GRN can be created from one or more open purchase orders — multi-PO consolidation is supported when the selected POs share the same **vendor and currency** (the create wizard rejects a mixed-currency selection; no additional check on credit terms was found) — or manually for receipts that have no upstream PO (`doc_type = manual`). Partial receipts are first-class — the GRN tracks received vs. ordered per line and feeds `received_qty` back to the source PO, which moves toward `partial` or `completed` depending on whether every line is fully received. **Unconfirmed:** no vendor-invoice capture, AP-journal-posting, or three-way-match (PO ↔ GRN ↔ invoice) feature was found anywhere in the current frontend or backend — treat any such claim elsewhere in this module as design intent, not implemented behavior.

## 2. Business Context
The GRN is the control point where physical reality meets the books: until the `draft → saved` transition fires, a PO is only a commitment; once saved, stock on-hand and the cost layer are updated and the source PO's `received_qty` advances. Hospitality operations run on tight food-cost margins and rely on this checkpoint to catch under-deliveries, over-deliveries, and price variances before they become inventory errors. Mandatory invoice number + vendor uniqueness (`(invoice_no, vendor_id)` unique per non-voided GRN), a PO/manual `doc_type` split, and a locked post-commit state exist to make every receipt explainable.

**Unconfirmed / not found in current source:** no journal-entry, ledger, or GL-posting code exists anywhere in the good-received-note backend module (`good-received-note.service.ts`, `good-received-note.logic.ts`) — a repo-wide search for `journal`, `ledger`, `accounts_payable`, `vendor_invoice`, and `tb_invoice` returned zero hits. Treat "debit inventory / credit accounts payable", "AP entry", and similar bookkeeping claims as design intent from `carmen/docs`, not confirmed live behavior. The Prisma schema's `is_consignment` and `is_cash` boolean fields described in an earlier version of this page **no longer exist** — the current header carries a single `post_type` enum (`ap` | `consignment` | `cash`, default `ap`) instead, and no branching logic on that field was found in the backend either (see [01-data-model.md](/en/inventory/good-receive-note/01-data-model) §4–§5). `enum_transaction_type` (the enum that labels inventory-ledger rows) has no "Stock In", "Consignment In", or "Non-Inventory" member — a GRN receipt always resolves to the single value `good_received_note`; movement-type differentiation by `post_type` is not implemented.

Food-safety and quality control: perishable goods carry lot numbers (system-generated in the fixed format `RC{YY}{MM}{4-digit sequence}`, or overridden manually) and expiry dates that travel with the linked inventory transaction, so subsequent FIFO consumption and recall traces are traceable back to the originating GRN. **Unconfirmed:** no per-line "quality hold" gate, `accepted_qty` field, or accept/reject/partially-accept mechanism was found anywhere in the schema or application code — a receiving discrepancy is handled simply by entering less than the ordered quantity as `received_qty`, not by a separate acceptance step. Price variance against the vendor pricelist at GRN entry is described in `carmen/docs` design material but no matching code was found within the GRN module itself during this pass.

## 3. Key Concepts
- **Receiving Lot**: A lot number assigned at receipt on the linked inventory transaction (not on the GRN line itself), in the system-generated fixed format `RC{YY}{MM}{4-digit sequence}` (`inventory-transaction.service.ts`), with optional manual override and expiry date. Lot history is preserved end-to-end so FIFO consumption and recall events trace back to the originating GRN. **Corrected this pass:** no evidence of a *configurable* lot-number format (date components, item identifiers, tenant-defined tokens) was found — the current generator uses one fixed pattern.
- **Partial Receipt**: A GRN that fulfils only part of an outstanding PO. Received quantities can be less than ordered, and the source PO moves toward `partial` status with the remaining open quantity available for future GRNs. Multiple GRNs can be raised against the same PO until every line is fully received (`po_status = completed`).
- **Over/Under Receipt**: Quantity variance between PO and GRN. Under-receipt (received less than ordered) leaves the PO `partial`; over-receipt is constrained by validation against `order_qty − received_qty − cancelled_qty` on the PO line, subject to a tenant over-receipt tolerance.
- **Save (the mutating event)**: The `draft → saved` transition — not commit — is the single event that updates stock. On save, the system: (1) writes a `tb_inventory_transaction` row per receipt event, (2) creates new FIFO cost layers or recomputes the weighted average per the item's costing method, and (3) advances the source PO line's `received_qty` (and `po_status`). **Commit** (`saved → committed`) then only flips `doc_status` and locks the document — no further inventory or PO-side effect was found in current source. **Unconfirmed:** no journal-entry / GL-posting code was found anywhere in the module; batch commit and end-of-period auto-commit were also not found in current source (no batch endpoint, no scheduled job) — treat both as design intent, not implemented behavior.
- **Extra Cost Allocation**: Landed-cost components (freight, handling, duties) are recorded against the GRN with a distribution-mode tag (`manual`, `by_value`, or `by_qty` — `enum_allocate_extra_cost_type`; no `by_weight` / `by_volume` mode exists). **Unconfirmed:** no server-side code was found that actually splits an extra-cost amount across GRN lines or feeds it into the FIFO / average cost-layer calculation — the current frontend captures a single flat amount per extra-cost type with no per-line breakdown, and `createInventoryTransactions`/cost-layer creation in the backend reads only the line's own net amount. Treat "Last Cost = (Net Amount + Extra Costs) / (Received Qty + FOC Qty)" as design intent, not confirmed live behavior.
- **FOC (Free of Charge)**: A receipt event where vendor-supplied items arrive at zero price (samples, promotional bonus, replacement for damaged stock), recorded as a parallel `tb_good_received_note_detail_item` row with `foc_qty` on the same line. FOC quantities are excluded from the line subtotal but included in on-hand and lot quantities.
- **`post_type` (ap / consignment / cash)**: A header-level enum (`enum_good_received_note_post_type`, default `ap`) that replaced an earlier `is_consignment` / `is_cash` boolean pair — those two boolean fields no longer exist in the schema. **Unconfirmed:** no branching logic on `post_type` was found in the backend (no differentiated GL treatment, no distinct inventory-transaction type); the field is currently stored and exposed through the API but does not appear to change system behavior. `enum_transaction_type` (the inventory-ledger type enum) has no "Stock In" / "Consignment In" / "Non-Inventory" members — a GRN receipt always posts as the single value `good_received_note`.

## 4. Roles and Personas
| Role | Responsibility |
| --- | --- |
| Store Keeper / Receiving Clerk | Receives the physical delivery at the dock, counts goods against the PO and the vendor delivery note, creates the GRN in `draft` status, attaches packing slips, records the receipt quantity per line, and saves for review (`draft → saved`, which posts stock). |
| Store Manager / Inventory Manager | Reconciles the GRN against the actual stock received, oversees lot/batch tracking and storage-location assignment, and commits (`saved → committed`) to lock the document. |
| Purchaser / Procurement Officer | Owns the upstream PO the GRN is created against, reviews receiving information for the POs they raised, and coordinates with the vendor on variances (short-ship, wrong item). |
| Department Manager | Reviews GRNs hitting the department's cost-centre and validates that received goods match what was ordered for the department. |
| System Administrator | Maintains RBAC and running-code (GRN-number) sequencing, tax codes, and currency rates; oversees the integration wiring with PO and Inventory. **Unconfirmed:** no dedicated "GRN configuration console" (lot-number-format editor, integration-endpoint panel) was found in current source — configuration surfaces for tax, currency, and running-code are generic, cross-module screens documented under [system-config](/en/inventory/system-config) and [master-data](/en/inventory/master-data), not a GRN-specific workspace. |

**Removed this pass (no matching route, component, or endpoint found):** a "Finance Team / AP Clerk" role described as running a three-way match, validating extra-cost allocation pre-AP-posting, and signing off on receipt activity at period close. A repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `three-way`, `vendor_invoice`, `VendorInvoice`, and `tb_invoice` returned zero hits, and `enum_stage_role` (the workflow-stage-role enum shared with PR/PO) has no `finance` member — mirrors the same finding already confirmed for the `purchase-order` module.

## 5. Related Modules
**Cross-module flow:**

- [purchase-order](/en/inventory/purchase-order) — GRN is created against a PO; receipt advances the PO's `received_qty` and `po_status`
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
- [02 — Business Rules](/en/inventory/good-receive-note/02-business-rules) — Validation, calculation, authorization, and posting rules (§6 corrects a prior three-way-match / AP-journal narrative not found in current source).
- [03 — User Flow](/en/inventory/good-receive-note/03-user-flow) — Document lifecycle and persona index.
  - [Receiver](/en/inventory/good-receive-note/03-user-flow-receiver)
  - [Purchaser](/en/inventory/good-receive-note/03-user-flow-purchaser)
  - [Finance](/en/inventory/good-receive-note/03-user-flow-finance) — correction page: why no Finance / three-way-match persona was confirmed.
  - [Audit / Config](/en/inventory/good-receive-note/03-user-flow-audit-config) — correction page: why no dedicated GRN configuration console was confirmed.
- [04 — Test Scenarios](/en/inventory/good-receive-note/04-test-scenarios) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Receiver](/en/inventory/good-receive-note/04-test-scenarios-receiver)
  - [Purchaser](/en/inventory/good-receive-note/04-test-scenarios-purchaser)
  - [Finance](/en/inventory/good-receive-note/04-test-scenarios-finance) — correction page.
  - [Audit / Config](/en/inventory/good-receive-note/04-test-scenarios-audit-config) — correction page.