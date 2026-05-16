---
title: Purchase Order
description: Formal commitment to a vendor to purchase goods at agreed prices, quantities, and delivery terms.
published: true
date: 2026-05-16T09:00:00.000Z
tags: purchase-order, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Purchase Order

## 1. Overview

A **Purchase Order (PO)** is the formal, externally-binding document a buyer issues to a vendor that commits the organisation to purchase specified goods or services at agreed unit prices, quantities, delivery dates, and payment terms. Each PO has a header — unique reference number, vendor, order date, required delivery date, delivery point, currency and exchange rate, payment and delivery terms, status, created-by, and rolled-up totals — and one or more line items that carry the product or free-text description, ordered quantity, unit of measure, unit price, discount, tax treatment, FOC quantity, and traceability links back to the originating Purchase Request line(s). Header totals (subtotal, total discount, total tax, grand total) are computed from rounded line-level calculations and dual-posted in transaction and base currencies.

The PO lifecycle is status-driven: `Draft` (editable, no commitment yet) → `Sent` (transmitted to the vendor and a firm budget commitment is established) → optionally `Partially Received` as GRNs are posted against it → `Fully Received` once every line is matched → `Closed` when the PO is administratively finalised (or `Voided` if cancelled before receipt). Deletion is only permitted in `Draft`; active POs can only be voided or closed so the audit trail is preserved. Amendments (price, quantity, delivery date, vendor terms) on an open PO are versioned with an activity-log entry; closing a PO short — accepting a partial receipt as final — is a deliberate action that releases the remaining commitment.

POs originate either manually (blank PO created from scratch) or by converting one or more approved Purchase Requests. When multiple PRs are selected for conversion the system groups them automatically by **vendor + currency**, producing one PO per unique combination and consolidating the PR lines into it while preserving the PR-to-PO traceability on every line. The PO is then the document against which the vendor delivers, the receiver creates a Good Receive Note, and the three-way match (PO ↔ GRN ↔ vendor invoice) clears the goods for accounts-payable posting.

## 2. Business Context

The PO is the moment at which an internal request becomes an external commitment. Up to this point the spend exists only as a soft commitment against budget; raising the PO converts that into a hard commitment with a legally enforceable obligation to the vendor on agreed terms. That single transition is what gives finance and procurement control over rogue spending: by routing every external commitment through a documented PO with unique reference number, approved vendor, validated pricelist pricing, and budget check, the organisation prevents off-system orders and ensures every future invoice has a matching authorisation.

The module is the integration spine for the procure-to-pay chain. PRs feed in on the upstream side with vendor allocation and approved quantities; the PO commits those quantities and prices to the vendor; the GRN module receives against the PO and validates ordered vs received vs accepted quantities; the inventory module increments on-order at PO send and on-hand at GRN post; the vendor-pricelist module supplies and validates unit prices; and finance picks up the firm commitment and, on invoice receipt, runs the three-way match before posting to accounts payable. Document management (attachments, comments, activity log) gives every PO a complete audit trail — who created it, what was amended, when it was sent, who received against it, when it was closed.

Financial accuracy is enforced at the calculation layer. Item subtotal, discount, net amount, tax, and total are each rounded at the line level using half-up (banker's) rounding with 3 decimals for quantity, 2 decimals for money, and 5 decimals for exchange rates; PO header totals roll up from rounded line values; cross-currency POs dual-post with explicit exchange-rate handling. The PO must reconcile cleanly against the originating PR and the eventual GRN and invoice, so the same rounding discipline runs end-to-end through the procure-to-pay calculations.

## 3. Key Concepts

- **PO Header**: The transaction-level record carrying vendor, reference number, order and required delivery dates, currency and exchange rate, delivery point, payment and delivery terms, status, totals, and audit fields. The header binds all line items into a single commitment to one vendor in one currency.
- **PO Line / PO Item**: A line on the PO representing a single product or free-text item with ordered quantity, unit of measure, unit price, discount, tax rate, FOC quantity, computed line totals, and traceability fields (`prItemId`, `prNumber`) when sourced from a Purchase Request. Lines are the unit of receipt, three-way match, and AP posting.
- **Delivery Terms**: The Incoterm or equivalent clause that defines where title passes, who pays freight and insurance, and where the vendor's delivery obligation ends (e.g., delivery point, on-premise unloading). Carried on the header and used by receiving and finance.
- **Payment Terms**: The credit terms agreed with the vendor (e.g., net 30, 2/10 net 30, COD). Sourced from the vendor master, copied onto the PO header at creation, and used by AP to compute due dates and discount windows on the eventual invoice.
- **Amendment**: A controlled change to an active PO — price, quantity, delivery date, terms, or line addition/removal — recorded as a versioned event in the activity log. Amendments adjust the open commitment and propagate to budget and inventory on-order; vendor re-acknowledgement is typically required for material changes.
- **Open vs Closed PO**: An **open** PO has remaining quantity to receive or has not yet been administratively closed. A **closed** PO is finalised — either fully received and closed, or short-closed with the remaining commitment released. Closed POs cannot accept further GRNs and become read-only except for reporting and audit.
- **Three-Way Match**: The AP control that compares PO line (what was ordered), GRN line (what was received and accepted), and vendor invoice line (what is being billed) on quantity and price before approving the invoice for payment. Discrepancies route to procurement or finance for resolution.
- **Voided PO**: An active PO cancelled before any receipt has been posted. Voiding releases the budget commitment, marks the PO uneditable, and preserves the record for audit. POs with at least one GRN cannot be voided — they must be closed instead.
- **Vendor + Currency Grouping**: The conversion rule that splits a set of selected PRs into one PO per unique vendor-and-currency combination. Ensures each PO is single-vendor and single-currency, consolidates eligible PR lines into one PO, and keeps procurement practice clean.
- **PR-to-PO Traceability**: The persistent link from each PO line back to the originating PR line (`prItemId`, `prNumber`). Preserved through amendments and partial receipts so auditors and operators can trace any received item back to the demand that requested it.
- **FOC (Free of Charge)**: A line-level field for vendor-supplied items at zero price (samples, promotional bonuses). FOC quantities are excluded from the PO subtotal but flow through to the GRN so the receiving side records them in inventory.
- **Exchange Rate**: The conversion rate captured on the PO header at creation, used to dual-post the PO totals in base currency. Locked on the PO so the commitment and the eventual receipt and invoice reconcile against a stable basis.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Procurement Officer / Purchaser | Creates POs manually or by converting approved PRs, validates vendor allocation and pricelist pricing, sets delivery and payment terms, transmits the PO to the vendor, manages amendments and follow-up, and voids or closes POs as the lifecycle requires. |
| Procurement Manager | Oversees the procurement function, approves high-value or strategically sensitive POs and amendments, manages vendor relationships and ranking, and tunes the conversion and grouping rules. Holds delete-in-draft and override authority. |
| Vendor | External party that receives the PO, confirms acceptance, fulfils delivery against the agreed terms, and issues the invoice that is matched against the PO and GRN before payment. |
| Receiver / Store Keeper | Downstream role that physically accepts the goods, raises the GRN against the PO, and validates received and accepted quantities line by line. Triggers the inventory on-hand increment and the partial-/fully-received status transition on the PO. |
| Inventory Manager | Manages goods receipt for the location, supervises GRN creation, and closes POs once receipt is complete or accepted as final. |
| Finance Officer / Accounts Payable | Reviews PO terms and financial accuracy, runs the three-way match on the vendor invoice against the PO and GRN, posts the AP liability on invoice match, and flags discrepancies back to procurement. |
| Finance Manager | Reviews high-value POs and amendments before transmission, validates currency and exchange-rate handling, and oversees the AP-side controls and reporting. |
| System Administrator | Configures PO numbering, status transitions, RBAC, vendor and pricelist integration, budget and inventory integration, document templates, and conversion/grouping rules. |
| Auditor | Read-only access to POs, amendments, and the activity log to verify policy compliance, segregation of duties, three-way-match integrity, and end-to-end traceability from PR through PO and GRN to invoice. |

## 5. Related Modules

**Cross-module flow:**
- [[purchase-request]] — POs are generated from approved PRs
- [[good-receive-note]] — GRN is created against a PO on receipt
- [[vendor-pricelist]] — PO prices are validated against vendor pricelists
- [[product]] — PO lines reference products from the catalog

**Master configuration:**
- [[master-data/vendor]] — vendor master (header + addresses + contacts) referenced by PO header
- [[master-data/currency]] — currency and exchange rate for multi-currency POs
- [[master-data/tax-profile]] — tax codes applied to PO lines
- [[master-data/credit-term]] — payment terms copied from vendor master onto the PO header
- [[master-data/delivery-point]] — agreed delivery point for the commitment
- [[master-data/unit]] — unit of measure for PO line quantities
- [[system-config/workflow]] — approval workflow definitions for PO authorization and amendments
- [[system-config/running-code]] — PO document number sequencing
- [[reporting-audit/activity]] — PO status-transition, amendment, and three-way-match log for audit
- [[reporting-audit/attachment]] — vendor acknowledgements and contract documents attached to the PO

## 6. Reference Sources

- Concepts: `../carmen/docs/purchase-order-management/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](./02-business-rules.md) — Validation, calculation, authorization, posting, and three-way-match rules.
- [03 — User Flow](./03-user-flow.md) — Document lifecycle and persona index.
  - [Purchaser](./03-user-flow-purchaser.md)
  - [Procurement Manager](./03-user-flow-procurement-manager.md)
  - [Vendor](./03-user-flow-vendor.md)
  - [Receiver](./03-user-flow-receiver.md)
  - [Finance](./03-user-flow-finance.md)
  - [Audit / Config](./03-user-flow-audit-config.md)
- [04 — Test Scenarios](./04-test-scenarios.md) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Purchaser](./04-test-scenarios-purchaser.md)
  - [Procurement Manager](./04-test-scenarios-procurement-manager.md)
  - [Vendor](./04-test-scenarios-vendor.md)
  - [Receiver](./04-test-scenarios-receiver.md)
  - [Finance](./04-test-scenarios-finance.md)
  - [Audit / Config](./04-test-scenarios-audit-config.md)
