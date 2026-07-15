---
title: Purchase Order
description: Formal commitment to a vendor to purchase goods at agreed prices, quantities, and delivery terms.
published: true
date: 2026-07-15T13:30:00.000Z
tags: purchase-order, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Purchase Order

> **At a Glance**
> **Module purpose:** External vendor commitment document (`Draft` → `In Progress` (approval) → `Sent` → `Partial`/`Completed` → `Closed`, with `Voided` reachable only from `In Progress` via reject) that hands off to GRN on receipt &nbsp;·&nbsp; **Audience:** Purchaser, Procurement Manager, Vendor, Receiver, Auditor &nbsp;·&nbsp; **Key entities/tables:** `tb_purchase_order`, `tb_purchase_order_detail`, PR→PO trace fields (`prItemId`, `prNumber`), amendment activity log, [purchase-order/credit-note](/en/inventory/purchase-order/credit-note) &nbsp;·&nbsp; **Sub-pages:** 18

![Purchase Order screen](/screenshots/purchase-order/index.png)

![Purchase Order detail screen](/screenshots/purchase-order/detail.png)

## 1. Overview

A **Purchase Order (PO)** is the formal, externally-binding document a buyer issues to a vendor that commits the organisation to purchase specified goods or services at agreed unit prices, quantities, delivery dates, and payment terms. Each PO has a header — unique reference number, vendor, order date, required delivery date, delivery point, currency and exchange rate, payment and delivery terms, status, created-by, and rolled-up totals — and one or more line items that carry the product or free-text description, ordered quantity, unit of measure, unit price, discount, tax treatment, FOC quantity, and traceability links back to the originating Purchase Request line(s). Header totals (subtotal, total discount, total tax, grand total) are computed from rounded line-level calculations and dual-posted in transaction and base currencies.

The PO lifecycle is status-driven (`enum_purchase_order_doc_status`): `Draft` (editable, no commitment yet) → `In Progress` (submitted into the assigned multi-stage approval workflow — each stage carries a `stage_role` such as `purchase` or `approve` and a set of eligible actors in `user_action.execute[]`) → `Sent` (the final approval stage both approves and transmits to the vendor in the same step — there is no separate manual "Send to Vendor" action) → optionally `Partial` as GRNs are posted against it → `Completed` once every line is matched, or `Closed` when the PO is administratively finalised early with the remainder written to `cancelled_qty`. `Voided` is reachable only from `In Progress`, when any approver at the current stage rejects the PO — this is a direct, terminal transition with no intermediate return to `Draft`. Deletion is only permitted in `Draft`. A separate "send back for revision" action (`review`) does not change `po_status` — it only resets `workflow_current_stage` to an earlier stage (typically back to the creator) while the PO stays `In Progress`. Amendments (price, quantity, delivery date, vendor terms) on an open PO are versioned with an activity-log entry; closing a PO short — accepting a partial receipt as final — is a deliberate action that releases the remaining commitment.

POs originate through three paths: manually (blank PO created from scratch, `po_type = manual`), by converting one or more approved Purchase Requests (`po_type = purchase_request`), or directly from a vendor price list through a 4-step wizard — Order Details → Select Vendors → Select Items → Review & Confirm (`po_type = pricelist`, `routes/procurement/purchase-order/from-price-list/`). When multiple PRs are selected for conversion, a 2-step dialog (select PRs → review grouped PO(s)) groups them server-side by **vendor + delivery date + currency**, producing one PO per unique combination and consolidating the PR lines into it while preserving the PR-to-PO traceability on every line (`POST .../purchase-orders/group-pr` for the preview, `POST .../purchase-orders/confirm-pr` to create). The PO is then the document against which the vendor delivers and the receiver creates a Good Receive Note against it. Note: no vendor-invoice / three-way-match (PO ↔ GRN ↔ invoice) capture feature exists in the current source — searches across the frontend and backend for invoice/AP-matching code turned up nothing; treat any such claim elsewhere in this module's pages as unconfirmed/planned, not live behavior.

## 2. Business Context

The PO is the moment at which an internal request becomes an external commitment. Up to this point the spend exists only as a soft commitment against budget; raising the PO converts that into a hard commitment with a legally enforceable obligation to the vendor on agreed terms. That single transition is what gives finance and procurement control over rogue spending: by routing every external commitment through a documented PO with unique reference number, approved vendor, validated pricelist pricing, and budget check, the organisation prevents off-system orders and ensures every future invoice has a matching authorisation.

The module is the integration spine for the procure-to-pay chain. PRs feed in on the upstream side with vendor allocation and approved quantities; the PO commits those quantities and prices to the vendor; the GRN module receives against the PO and validates ordered vs received quantities; the inventory module increments on-order at PO send and on-hand at GRN post; the vendor-pricelist module supplies unit prices. Document management (attachments, comments, activity log) gives every PO a complete audit trail — who created it, what was amended, when it was sent, who received against it, when it was closed. **Unverified:** no vendor-invoice capture or three-way-match (PO ↔ GRN ↔ invoice) feature was found in the current frontend or backend source — treat any AP/invoice-matching claim elsewhere as design intent, not implemented behavior.

Financial accuracy is enforced at the calculation layer. Item subtotal, discount, net amount, tax, and total are each rounded at the line level using half-up (banker's) rounding with 3 decimals for quantity, 2 decimals for money, and 5 decimals for exchange rates; PO header totals roll up from rounded line values; cross-currency POs dual-post with explicit exchange-rate handling. The PO must reconcile cleanly against the originating PR and the eventual GRN and invoice, so the same rounding discipline runs end-to-end through the procure-to-pay calculations.

## 3. Key Concepts

- **PO Header**: The transaction-level record carrying vendor, reference number, order and required delivery dates, currency and exchange rate, delivery point, payment and delivery terms, status, totals, and audit fields. The header binds all line items into a single commitment to one vendor in one currency.
- **PO Line / PO Item**: A line on the PO representing a single product or free-text item with ordered quantity, unit of measure, unit price, discount, tax rate, FOC quantity, computed line totals, and traceability fields (`prItemId`, `prNumber`) when sourced from a Purchase Request. Lines are the unit of receipt against the GRN.
- **Delivery Terms**: The Incoterm or equivalent clause that defines where title passes, who pays freight and insurance, and where the vendor's delivery obligation ends (e.g., delivery point, on-premise unloading). Carried on the header and used by receiving and finance.
- **Payment Terms**: The credit terms agreed with the vendor (e.g., net 30, 2/10 net 30, COD). Sourced from the vendor master, copied onto the PO header at creation, and used by AP to compute due dates and discount windows on the eventual invoice.
- **Amendment**: A controlled change to an active PO — price, quantity, delivery date, terms, or line addition/removal — recorded as a versioned event in the activity log. Amendments adjust the open commitment and propagate to budget and inventory on-order; vendor re-acknowledgement is typically required for material changes.
- **Open vs Closed PO**: An **open** PO has remaining quantity to receive or has not yet been administratively closed. A **closed** PO is finalised — either fully received and closed, or short-closed with the remaining commitment released. Closed POs cannot accept further GRNs and become read-only except for reporting and audit.
- **Voided PO**: The terminal outcome when an approver rejects a PO while it is `in_progress` (via the `/reject` endpoint) — the transition is direct (`in_progress → voided`), with no intermediate return to `draft`. There is no separate manual "void" action reachable from `draft`, `sent`, or `partial`: ending a PO from those statuses goes through **Cancel** or **Close** instead, both of which land on `closed` (with the outstanding balance written to `cancelled_qty`), not `voided`.
- **Vendor + Delivery Date + Currency Grouping**: The rule that splits a set of selected PRs into one PO per unique `(vendor, delivery_date, currency)` combination during PR-to-PO conversion. Ensures each PO is single-vendor and single-currency, consolidates eligible PR lines sharing the same delivery date into one PO, and keeps procurement practice clean.
- **PR-to-PO Traceability**: The persistent link from each PO line back to the originating PR line (`prItemId`, `prNumber`). Preserved through amendments and partial receipts so auditors and operators can trace any received item back to the demand that requested it.
- **FOC (Free of Charge)**: A line-level field for vendor-supplied items at zero price (samples, promotional bonuses). FOC quantities are excluded from the PO subtotal but flow through to the GRN so the receiving side records them in inventory.
- **Exchange Rate**: The conversion rate captured on the PO header at creation, used to dual-post the PO totals in base currency. Locked on the PO so the commitment and the eventual receipt and invoice reconcile against a stable basis.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Procurement Officer / Purchaser | Creates POs manually, by converting approved PRs, or from a vendor price list; validates vendor allocation and pricelist pricing; sets delivery and payment terms; submits into the approval workflow; manages amendments and follow-up once `sent`. |
| Procurement Manager | Acts as an approver on a configured workflow stage (same generic stage-based approve / send-back / reject mechanism as any other approver — no amount-threshold or deviation-percentage auto-routing was found in current source). Holds delete-in-draft authority. |
| Vendor | External party that receives the PO and fulfils delivery against the agreed terms. No confirmed in-system acknowledgement or invoice-matching feature exists today. |
| Receiver / Store Keeper | Downstream role that physically accepts the goods and raises the GRN against the PO line by line. The GRN posting increments `received_qty` on the PO line and drives the `sent → partial → completed` transition; inventory on-hand is incremented by the GRN / inventory module, not by the PO. |
| Inventory Manager | Manages goods receipt for the location, supervises GRN creation, and closes POs once receipt is complete or accepted as final. |
| Finance | Named in legacy design docs as a pre-transmission approver and post-receipt three-way-match / AP-posting owner. **Unconfirmed:** no distinct "finance" `stage_role`, invoice-capture screen, or AP-matching code was found; the only approver evidence in current e2e fixtures (`fc@blueledgers.com`) is documented elsewhere as the same generic approve-stage actor as the Procurement Manager. |
| System Administrator | Configures PO numbering (via the generic running-code screen), workflow stage definitions, and RBAC. A dedicated PO-specific configuration workbench (vendor ranking, conversion-grouping rule editor, pricelist-tolerance band, approval-amount threshold) was not found in current source — treat it as unconfirmed. |
| Auditor | Read-only access to POs, amendments, and the activity log to verify policy compliance, segregation of duties, and traceability from PR through PO and GRN. |

## 5. Related Modules

**Cross-module flow:**
- [purchase-request](/en/inventory/purchase-request) — POs are generated from approved PRs
- [good-receive-note](/en/inventory/good-receive-note) — GRN is created against a PO on receipt
- [vendor-pricelist](/en/inventory/vendor-pricelist) — PO prices are validated against vendor pricelists
- [product](/en/inventory/product) — PO lines reference products from the catalog

**Master configuration:**
- [master-data/vendor](/en/inventory/master-data/vendor) — vendor master (header + addresses + contacts) referenced by PO header
- [master-data/currency](/en/inventory/master-data/currency) — currency and exchange rate for multi-currency POs
- [master-data/tax-profile](/en/inventory/master-data/tax-profile) — tax codes applied to PO lines
- [master-data/credit-term](/en/inventory/master-data/credit-term) — payment terms copied from vendor master onto the PO header
- [master-data/delivery-point](/en/inventory/master-data/delivery-point) — agreed delivery point for the commitment
- [master-data/unit](/en/inventory/master-data/unit) — unit of measure for PO line quantities
- [system-config/workflow](/en/inventory/system-config/workflow) — approval workflow definitions for PO authorization and amendments
- [system-config/running-code](/en/inventory/system-config/running-code) — PO document number sequencing
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — PO status-transition and amendment log for audit
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — vendor acknowledgements and contract documents attached to the PO

## 6. Reference Sources

- Concepts: `../carmen/docs/purchase-order-management/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](/en/inventory/purchase-order/01-data-model) — Entities, fields, relationships, and enums (Prisma-derived).
- [01a — Data Model — Comment Tables](/en/inventory/purchase-order/01a-data-model-comments) — Document-level and line-level comment / attachment tables and the `enum_comment_type` user/system tagging.
- [02 — Business Rules](/en/inventory/purchase-order/02-business-rules) — Validation, calculation, authorization, posting, and cross-module rules.
- [03 — User Flow](/en/inventory/purchase-order/03-user-flow) — Document lifecycle and persona index.
  - [Purchaser](/en/inventory/purchase-order/03-user-flow-purchaser)
  - [Procurement Manager](/en/inventory/purchase-order/03-user-flow-procurement-manager)
  - [Vendor](/en/inventory/purchase-order/03-user-flow-vendor)
  - [Receiver](/en/inventory/purchase-order/03-user-flow-receiver)
  - [Finance](/en/inventory/purchase-order/03-user-flow-finance)
  - [Audit / Config](/en/inventory/purchase-order/03-user-flow-audit-config)
- [04 — Test Scenarios](/en/inventory/purchase-order/04-test-scenarios) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Purchaser](/en/inventory/purchase-order/04-test-scenarios-purchaser)
  - [Procurement Manager](/en/inventory/purchase-order/04-test-scenarios-procurement-manager)
  - [Vendor](/en/inventory/purchase-order/04-test-scenarios-vendor)
  - [Receiver](/en/inventory/purchase-order/04-test-scenarios-receiver)
  - [Finance](/en/inventory/purchase-order/04-test-scenarios-finance)
  - [Audit / Config](/en/inventory/purchase-order/04-test-scenarios-audit-config)
- [Credit Note](/en/inventory/purchase-order/credit-note) — Vendor-issued credit document reversing all or part of a prior PO / GRN.
