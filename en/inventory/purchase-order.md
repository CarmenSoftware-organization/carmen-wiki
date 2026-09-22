---
title: Purchase Order
description: Formal commitment to a vendor to purchase goods at agreed prices, quantities, and delivery terms.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: purchase-order, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Purchase Order

> **At a Glance**
> **Module purpose:** External vendor commitment document (`draft` → `in_progress` (approval) → `approved` → `sent_or_print` (emailed or marked sent) → `partial`/`completed` → `closed`, with `voided` reachable only from `in_progress` via reject) that hands off to GRN on receipt &nbsp;·&nbsp; **Audience:** Purchaser, Procurement Manager, Vendor, Receiver, Auditor &nbsp;·&nbsp; **Key entities/tables:** `tb_purchase_order` (now with header `delivery_point_id`), `tb_purchase_order_detail` (one row = one location), PR↔PO bridge `tb_purchase_order_detail_tb_purchase_request_detail` (ordered vs received FOC), `tb_activity` email/mark-sent entries, [purchase-order/credit-note](/en/inventory/purchase-order/credit-note) &nbsp;·&nbsp; **Sub-pages:** 18

> ⚠️ **Re-synced 2026-09-22 against source HEAD.** Three breaking changes since the 2026-07-29 baseline run through every sub-page: (1) `enum_purchase_order_doc_status` gained `approved` and renamed `sent` → `sent_or_print` (migrations `20260914080000_po_status_add_approved`, `20260914080100_po_status_backfill_and_rename_sent`) — final approval now lands on `approved`, and `sent_or_print` is reached only by `POST .../purchase-orders/:id/send-email` succeeding or `POST .../purchase-orders/:id/mark-sent`; (2) a PO line is one delivery location (`feat(po)!: location ย้ายมาแบนบน detail`, 2026-09-09) — the nested `locations[]` breakdown is gone from create payloads and detail responses; (3) `tb_purchase_order.delivery_point_id/name` on the header (`20260915120000_po_header_delivery_point`) and `pr_detail_foc_qty` / `foc_received_qty` on the PR↔PO bridge (`20260916030000_po_junction_foc_ordered_vs_received`).

![Purchase Order screen](/screenshots/purchase-order/index.png)

![Purchase Order detail screen](/screenshots/purchase-order/detail.png)

## 1. Overview

A **Purchase Order (PO)** is the formal, externally-binding document a buyer issues to a vendor that commits the organisation to purchase specified goods or services at agreed unit prices, quantities, delivery dates, and payment terms. Each PO has a header — unique reference number, vendor, order date, required delivery date, delivery point, currency and exchange rate, payment and delivery terms, status, created-by, and rolled-up totals — and one or more line items that carry the product or free-text description, ordered quantity, unit of measure, unit price, discount, tax treatment, FOC quantity, and traceability links back to the originating Purchase Request line(s). Header totals (subtotal, total discount, total tax, grand total) are computed from rounded line-level calculations and dual-posted in transaction and base currencies.

The PO lifecycle is status-driven (`enum_purchase_order_doc_status`): `draft` (editable, no commitment yet) → `in_progress` (submitted into the assigned multi-stage approval workflow — each stage carries a `stage_role` such as `purchase` or `approve` and a set of eligible actors in `user_action.execute[]`) → `approved` (the final approval stage; `purchase-order.logic.ts` `performApprove`: `po_status: isFinalApproval ? approved : in_progress`, `approval_date` set — **nothing is transmitted yet**) → `sent_or_print` (reached only when the PO actually reaches the vendor: `POST .../purchase-orders/:id/send-email` succeeds, or the user records an out-of-band delivery with `POST .../purchase-orders/:id/mark-sent`; both are `updateMany where po_status = approved` in `purchase-order.service.ts` `markPoAsSent`) → optionally `partial` as GRNs are posted against it → `completed` once every line is matched, or `closed` when the PO is administratively finalised early with the remainder written to `cancelled_qty`. A GRN may be raised against an `approved`, `sent_or_print`, or `partial` PO — receipt is unlocked at approval, not at send (`findOnePoForGrn`, `receivableStatuses`). `voided` is reachable only from `in_progress`, when any approver at the current stage rejects the PO — this is a direct, terminal transition with no intermediate return to `draft`. Deletion is only permitted in `draft`, and only by the document owner or a platform super-admin (`remove()`, `isDocumentOwner`). A separate "send back for revision" action (`review`) does not change `po_status` — it only resets `workflow_current_stage` to an earlier stage (typically back to the creator) while the PO stays `in_progress`; re-submitting after a send-back is accepted because `submit()` matches `draft` **or** `in_progress + last_action = reviewed`. The PO number is assigned once at creation and is **no longer regenerated on submit** (`fix(po): PO เลิกออกเลขใหม่ตอน submit`, 2026-09-14). Closing a PO short — accepting a partial receipt as final — is a deliberate action that releases the remaining commitment.

POs originate through three paths, chosen from the **Create Purchase Order** dialog (`po-create-dialog.tsx`): manually (blank PO created from scratch at `/procurement/purchase-order/new`, `po_type = manual`), by converting one or more approved Purchase Requests (`po_type = purchase_request`, the 3-step page `/procurement/purchase-order/from-pr` — Select PRs → Review Groups → Result, `routes/procurement/purchase-order/from-pr/`), or directly from a vendor price list through a 4-step wizard — Order Details → Select Vendors → Select Items → Review & Confirm (`po_type = pricelist`, `routes/procurement/purchase-order/from-price-list/`). When multiple PRs are selected for conversion the server groups their lines by **vendor + delivery date + currency** (`buildPoGroupKey` → `${vendor_id}|${yyyy-MM-dd}|${currency_id}`), producing one PO per unique combination and consolidating the PR lines into it while preserving the PR-to-PO traceability on every line (`POST .../purchase-orders/group-pr` for the preview, `POST .../purchase-orders/confirm-pr` to create). Since 2026-09-15 both endpoints also accept optional header overrides `delivery_date`, `delivery_point_id`, and `note` (`IPurchaseOrderFromPrOverrides`); a supplied `delivery_date` replaces every line's requested date, collapsing the date dimension of the grouping key so lines that would have split by date merge into one PO. The React page does not yet send these overrides — it posts only `pr_ids`, `workflow_id`, `buyer_id`, `buyer_name` (`from-pr-content.tsx` `handleConfirm`). The PO is then the document against which the vendor delivers and the receiver creates a Good Receive Note against it. Note: no vendor-invoice / three-way-match (PO ↔ GRN ↔ invoice) capture feature exists in the current source — searches across the frontend and backend for invoice/AP-matching code turned up nothing; treat any such claim elsewhere in this module's pages as unconfirmed/planned, not live behavior.

### 1.1 Endpoint surface (gateway `apps/backend-gateway/src/application/purchase-orders/purchase-orders.controller.ts`, Bruno `procurement/purchase-order/`)

| Verb + path (`/api/{bu_code}/purchase-orders…`) | Purpose | Status guard (backend) |
|---|---|---|
| `GET /`, `GET /:id`, `GET /:id/details`, `GET /:id/details/:detail_id` | List / detail / lines. Detail response carries nested `vendor`, `currency`, `buyer`, `workflow`, `credit_term` objects (`@ExpandRefs`, 2026-09-17) and per-line `location`, `delivery_point`, `pr_details[] { pr_detail, pr_id, pr_no, grn[] { grn_id, grn_no }, order_qty, received_qty, foc_qty, foc_received_qty }`. | — |
| `GET /detail/:detail_id/history` | Per-line change history (every save and stage action). **New since baseline.** | — |
| `POST /`, `PUT /:id`, `PATCH /:id/save`, `DELETE /:id`, `DELETE /batch`, `DELETE /:id/details/:detail_id` | Create / update / save (role-aware: only the creator's save carries prices) / delete. | delete: `draft` + owner or super-admin |
| `POST /verify` | Dry-run of `create` / `save` / `submit` — evaluates every rule, returns `200` with `is_valid: false` and the full issue list. **New since baseline** (`e3a6f0efb`, 2026-08-19). | — |
| `PATCH /:id/submit` | `draft → in_progress` (also accepted from `in_progress + last_action = reviewed`). | see left |
| `PATCH /:id/approve`, `/reject`, `/review` | Stage actions; final approve → `approved`; reject → `voided`; review keeps `in_progress`. | `in_progress` |
| `POST /swipe-approve` | Batch-approve `{ po_ids[] }` — every line of each PO at its current stage; per-PO success/failure; refused for `stage_role = purchase` or non-action users. **New since baseline** (`8e1319614`, 2026-08-13; mobile). | `in_progress` |
| `POST /:id/send-email` | Email the PO to the vendor through a BU email profile (`profile_id`, `to[]`, `cc[]`, `subject`, `body`, `attach_pdf`); PDF rendered server-side by micro-report (`exportPdfViaMicroReport` → FastReport `POST /api/Report/Export/Pdf`, `micro-report/service/render/viewer_client.go:133`); every attempt logged to `tb_activity` (`email_sent`); success moves `approved → sent_or_print`. **New since baseline** (`1897b4fc1`, 2026-09-08). | `approved`, `sent_or_print`, `partial`, `closed`, `completed` (`EMAILABLE_PO_STATUSES`) |
| `POST /:id/mark-sent` | Record an out-of-band delivery (printed, faxed, phoned); `tb_activity` "Marked as sent to vendor". **New since baseline** (`3969b8cf6`, 2026-09-14). No React button exists yet — Bruno/API only. | `approved` only |
| `POST /:id/cancel` | `→ closed`, every line `cancelled_qty = order_qty − received_qty`. | `draft`, `in_progress`, `approved`, `sent_or_print` |
| `POST /:id/close` | `→ closed`, remainder written to `cancelled_qty` where `> 0`; notifies buyer. | `in_progress`, `approved`, `sent_or_print`, `partial` |
| `POST /group-pr`, `POST /confirm-pr` | PR→PO preview / create with optional `delivery_date`, `delivery_point_id`, `note` overrides. | source PRs `approved` |
| `GET /grn/vendor`, `GET /grn/vendor/:vendor_id`, `GET /grn`, `GET /grn/:id` | PO pickers for GRN creation with per-location `can_use` (from `tb_location_user`, `c0b6d549f`). `GET /grn/:id` is the **only** PO route with a gateway `@Permission` (`procurement.purchase_order: ['create']`). | `approved`, `sent_or_print`, `partial` |
| `GET /:id/print`, `GET /:id/print-viewer`, `GET /:id/export` | PDF, FastReport viewer URL, Excel. | — |
| `GET /workflow-stages`, `GET /:po_id/previous-stages` | Workflow stage lookups for the send-back dialog. | — |

Every other PO route lists `Permissions: None` in Bruno; the React app declares `procurement.purchase_order` as a view-only resource and `procurement.credit_note` as CRUD in `constant/permissions.ts`.

## 2. Business Context

The PO is the moment at which an internal request becomes an external commitment. Up to this point the spend exists only as a soft commitment against budget; raising the PO converts that into a hard commitment with a legally enforceable obligation to the vendor on agreed terms. That single transition is what gives finance and procurement control over rogue spending: by routing every external commitment through a documented PO with unique reference number, approved vendor, validated pricelist pricing, and budget check, the organisation prevents off-system orders and ensures every future invoice has a matching authorisation.

The module is the integration spine for the procure-to-pay chain. PRs feed in on the upstream side with vendor allocation and approved quantities; the PO commits those quantities and prices to the vendor; the GRN module receives against the PO and validates ordered vs received quantities; the inventory module increments on-order at PO send and on-hand at GRN post; the vendor-pricelist module supplies unit prices. Document management (attachments, comments, activity log) gives every PO a complete audit trail — who created it, what was amended, when it was sent, who received against it, when it was closed. **Unverified:** no vendor-invoice capture or three-way-match (PO ↔ GRN ↔ invoice) feature was found in the current frontend or backend source — treat any AP/invoice-matching claim elsewhere as design intent, not implemented behavior.

Financial accuracy is enforced at the calculation layer. Item subtotal, discount, net amount, tax, and total are each rounded at the line level using half-up (banker's) rounding with 3 decimals for quantity, 2 decimals for money, and 5 decimals for exchange rates; PO header totals roll up from rounded line values; cross-currency POs dual-post with explicit exchange-rate handling. The PO must reconcile cleanly against the originating PR and the eventual GRN and invoice, so the same rounding discipline runs end-to-end through the procure-to-pay calculations.

## 3. Key Concepts

- **PO Header**: The transaction-level record carrying vendor, reference number, order and required delivery dates, currency and exchange rate, delivery point (`delivery_point_id/name` on `tb_purchase_order` since 2026-09-15 — previously the only delivery point in the PO tree sat on the PR↔PO bridge), payment and delivery terms, status, totals, and audit fields. The header binds all line items into a single commitment to one vendor in one currency.
- **PO Line / PO Item**: A line on the PO representing a single product **for a single delivery location** — a product going to two stores is two lines (`create-purchase-order.dto.ts`: `location_id` required per line; detail response `location` / `delivery_point` objects on the row). It carries ordered quantity, unit of measure, unit price, discount, tax rate, FOC quantity (`foc_qty`) and FOC already received (`foc_received_qty`), computed line totals, and traceability via `pr_details[]` (each entry names the source PR `pr_id`/`pr_no`, the PR line, and the GRN(s) that received against it). Lines are the unit of receipt against the GRN. The detail screen shows a GRN label per line, a "view source PR" button per line, and FOC received under the FOC / GRN column (`po-item-cells/pr-source-button.tsx`, `qty-cell.tsx`, 2026-09-21/22).
- **Approved vs Sent-or-Print**: `approved` means the workflow is finished; `sent_or_print` means the vendor has the document. The split exists because goods can arrive before anyone emails or prints the order, so receiving is unlocked at `approved` while the send status stays honest about what the vendor has seen.
- **Delivery Terms**: The Incoterm or equivalent clause that defines where title passes, who pays freight and insurance, and where the vendor's delivery obligation ends (e.g., delivery point, on-premise unloading). Carried on the header and used by receiving and finance.
- **Payment Terms**: The credit terms agreed with the vendor (e.g., net 30, 2/10 net 30, COD). Sourced from the vendor master, copied onto the PO header at creation, and used by AP to compute due dates and discount windows on the eventual invoice.
- **Amendment**: A controlled change to an active PO — price, quantity, delivery date, terms, or line addition/removal — recorded as a versioned event in the activity log. Amendments adjust the open commitment and propagate to budget and inventory on-order; vendor re-acknowledgement is typically required for material changes.
- **Open vs Closed PO**: An **open** PO has remaining quantity to receive or has not yet been administratively closed. A **closed** PO is finalised — either fully received and closed, or short-closed with the remaining commitment released. Closed POs cannot accept further GRNs and become read-only except for reporting and audit.
- **Voided PO**: The terminal outcome when an approver rejects a PO while it is `in_progress` (via the `/reject` endpoint) — the transition is direct (`in_progress → voided`), with no intermediate return to `draft`. There is no separate manual "void" action reachable from `draft`, `approved`, `sent_or_print`, or `partial`: ending a PO from those statuses goes through **Cancel** (`draft`/`in_progress`/`approved`/`sent_or_print`) or **Close** (`in_progress`/`approved`/`sent_or_print`/`partial`) instead, both of which land on `closed` (with the outstanding balance written to `cancelled_qty`), not `voided`.
- **Vendor + Delivery Date + Currency Grouping**: The rule that splits a set of selected PRs into one PO per unique `(vendor, delivery_date, currency)` combination during PR-to-PO conversion. Ensures each PO is single-vendor and single-currency, consolidates eligible PR lines sharing the same delivery date into one PO, and keeps procurement practice clean.
- **PR-to-PO Traceability**: The persistent link from each PO line back to the originating PR line (`prItemId`, `prNumber`). Preserved through amendments and partial receipts so auditors and operators can trace any received item back to the demand that requested it.
- **FOC (Free of Charge)**: A line-level field for vendor-supplied items at zero price (samples, promotional bonuses). FOC quantities are excluded from the PO subtotal but flow through to the GRN so the receiving side records them in inventory.
- **Exchange Rate**: The conversion rate captured on the PO header at creation, used to dual-post the PO totals in base currency. Locked on the PO so the commitment and the eventual receipt and invoice reconcile against a stable basis.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Procurement Officer / Purchaser | Creates POs manually, by converting approved PRs, or from a vendor price list; validates vendor allocation and pricelist pricing; sets delivery and payment terms; submits into the approval workflow; once the PO is `approved`, sends it to the vendor by email (**Send Email** button, `po-send-email-dialog.tsx`) — which is what moves it to `sent_or_print` — and manages follow-up. |
| Procurement Manager | Acts as an approver on a configured workflow stage (same generic stage-based approve / send-back / reject mechanism as any other approver). **Confirmed this pass:** the assigned workflow's `routing_rules` (configured from the generic **Routing** tab of `/system-admin/workflow`) can amount-route which stage comes next via `total_amount` — a per-workflow configuration choice, not a Procurement-Manager-specific mechanism; no pricelist-deviation-percentage routing field exists (see `02-business-rules.md` `PO_AUTH_004`). Delete-in-draft is **not** a Manager right — `remove()` allows the document owner or a platform super-admin only. |
| Vendor | External party that receives the PO (email with optional PDF, or an out-of-band print/fax recorded via `mark-sent`) and fulfils delivery against the agreed terms. No confirmed in-system acknowledgement or invoice-matching feature exists today. |
| Receiver / Store Keeper | Downstream role that physically accepts the goods and raises the GRN against the PO line by line. GRN creation is allowed from `approved`, `sent_or_print`, or `partial`; the GRN posting increments `received_qty` on the PO line (and `foc_received_qty` on the bridge row) and drives the `→ partial → completed` transition; inventory on-hand is incremented by the GRN / inventory module, not by the PO. |
| Inventory Manager | Manages goods receipt for the location, supervises GRN creation, and closes POs once receipt is complete or accepted as final. |
| Finance | Named in legacy design docs as a pre-transmission approver and post-receipt three-way-match / AP-posting owner. **Unconfirmed:** no distinct "finance" `stage_role`, invoice-capture screen, or AP-matching code was found; the only approver evidence in current e2e fixtures (`fc@blueledgers.com`) is documented elsewhere as the same generic approve-stage actor as the Procurement Manager. |
| System Administrator | Configures PO numbering (via the generic running-code screen), workflow stage definitions and amount/department/category routing rules (via the generic **Routing** tab of `/system-admin/workflow`, shared across PR/PO/SR — not a PO-specific screen), and RBAC. A dedicated PO-specific configuration workbench (vendor ranking, conversion-grouping rule editor, pricelist-tolerance band) was not found in current source — treat it as unconfirmed. |
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
- [master-data/delivery-point](/en/inventory/master-data/delivery-point) — agreed delivery point for the commitment (`tb_purchase_order.delivery_point_id` on the header since 2026-09-15; per-line `delivery_point_id` on the PR↔PO bridge)
- [master-data/location](/en/inventory/master-data/location) — one PO line is one delivery location; `can_use` on the GRN pickers comes from `tb_location_user`
- [system-config/config-email](/en/inventory/system-config/config-email) — BU email profile used by `POST .../purchase-orders/:id/send-email`; PO/RFP email templates seeded per BU (`ccc72e78b`, 2026-09-16)
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
