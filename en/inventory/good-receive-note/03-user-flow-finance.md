---
title: Good Receive Note (GRN) — User Flow — Finance
description: What the GRN module does and does not do for Finance — the AP Invoice module now matches committed GRNs, but the GRN itself has no Finance screen, role, or journal.
published: true
date: '2026-10-27T00:00:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, finance, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — User Flow — Finance

> **At a Glance**
> **What this page documents:** where a Finance / AP user touches a GRN as of 2026-10-27. The GRN module itself still has no Finance persona, role, or journal; what changed is that a separate **Accounts Payable** module can now pull `committed` GRN lines into an AP invoice and post it to the general ledger.

> ⚠️ **Status changed this pass (2026-10-27).** Earlier versions of this page (2026-07-15, re-checked 2026-09-22) said there was no vendor-invoice entity, no AP posting, and no match algorithm, and that the frontend `routes/accounting` area rendered only fabricated rows. Re-checked against `carmen-turborepo-backend` `c9d788829` and `carmen-frontend` `391062b5`:
>
> - **AP Invoice now exists.** Backend `apps/micro-business/src/ap/ap-invoice` (and `ap-payment`), gateway `application/ap-invoice`, tables `tb_ap_invoice`, `tb_ap_invoice_detail`, `tb_ap_invoice_detail_source`, status `enum_ap_invoice_status = draft | in_review | posted | void`, source `enum_ap_invoice_source = manual | grn | copy | excel | ai | interface`. **Frontend: none yet** — `routes/accounting/accounts-payable` builds its hooks on `createApMockRepository` (`shared/use-accounts-payable.ts`, `ap-mock-repository.ts`) and calls no API, and `routes/accounting/documents` is mock rows (`documentsFor()`). A fuller write-up of the backend flow is on [AP Invoice from GRN](/en/inventory/general-ledger/ap-invoice-from-grn).
> - **GRN → AP link.** `GET` of GRN candidates (`grnCandidates`, `ap-invoice.service.ts`) returns the items of **`committed` GRNs with `post_type = ap`** for one vendor and currency that still have `remaining_qty > 0`. Each AP line stores `tb_ap_invoice_detail_source` rows with `good_received_note_id`, `good_received_note_detail_item_id`, `matched_qty`, `grn_unit_price`, `matched_amount`, and `variance_amount`. On submit/post the check requires the GRN to be live, `committed`, and `post_type = ap` (`AP_GRN_NOT_COMMITTED`), all lines to share one vendor and currency (`AP_VENDOR_CURRENCY_MISMATCH`), and `Σ matched_qty` over all non-void AP documents to stay ≤ the item's `received_qty` (`AP_GRN_OVER_MATCHED`) — `ap-invoice.posting.ts:152-230,1100-1130`. That is a GRN ↔ invoice quantity match; a PO-level three-way match is not a separate feature.
> - **AP posting writes GL journals** with `source = ap` (`ap-invoice.posting.ts:291`). The GRN, `inventory-transaction.service.ts`, and `period-end.*` still import nothing from the GL module, and `enum_gl_jv_source.inventory` has no writer.
> - **The GRN side of the link.** The GRN detail response carries `ap_invoices` (active, non-void AP documents that took any of its lines, `findActiveApInvoicesForGrn`, `good-received-note.ap-link.ts:87`); while that list is non-empty a committed GRN cannot be edited at all (`GRN_AP_LINKED_NOT_EDITABLE`), and the frontend shows *Edit* disabled with the AP document numbers (`grn-header.tsx:60-65,167-175`) — the lock is therefore reachable today only through the gateway API. Without AP, a committed GRN still accepts invoice-header edits (`invoice_no`, `invoice_date`, `invoice_f`, `payment_due_date`, credit-term fields, `post_type`, `description`, `note`).
> - **Void path.** There is no AP guard on `voidGrnById` / `reject`, and none is needed: AP only sources `committed` GRNs, which void and reject already refuse (`GRN_COMMITTED_NOT_VOIDABLE`; reject accepts `draft`/`saved` only). A committed GRN can never be voided, with or without AP.
> - **External export.** `GET /api/ext/v1/ap-invoices` (BU API key, read-only, `inventory/accounting-export`) publishes `committed` GRNs and credit notes as vendor-invoice documents for an outside accounting system and skips `post_type = consignment` GRNs (`export-core.service.ts:194-228`).
> - `enum_stage_role` (the workflow-stage-role enum shared with PR / PO / GRN) still has no `finance` member, and the GRN module has no Finance screen, approval stage, or journal action. Its lifecycle operations (`save`, `commit`, `approve`, `reject` in `good-received-note.logic.ts`, `voidGrnById` in `good-received-note.service.ts`) touch no journal or AP entity.
> - **Credit Note** (`tb_credit_note`, FK back to `tb_good_received_note`, one credit per product per GRN since 2026-09-21) remains a separate document documented under [purchase-order/credit-note](/en/inventory/purchase-order/credit-note); a live credit note locks the referenced GRN lines against edit and void (`GRN_LINE_STOCK_LOCKED`).

## What is and is not confirmed

| Claim | Status |
| --- | --- |
| Extra-cost allocation mode tag (`manual` / `by_value` / `by_qty`) stored on `tb_extra_cost` | **Confirmed** — real Prisma enum `enum_allocate_extra_cost_type` (three values only; no `by_weight` / `by_volume`). The frontend offers `by_qty` and `by_value` (`grn-extra-cost-fields.tsx:201-202`). |
| Extra-cost amount split across GRN lines and fed into the FIFO / average cost-layer calculation | **Confirmed live since 2026-09-10** (`f8cd9f0d9`). `allocateExtraCost()` (`good-received-note.extra-cost.ts:40-61`) splits `Σ tb_extra_cost_detail.amount` across the lines that put stock on hand — `by_qty` = equal shares, `by_value` = weighted by `received_base_qty + foc_base_qty`, `manual` = nothing — at posting time; the share is added to the line's landed cost and stored per cost layer as `extra_cost_amount`. Since 2026-10-24 the extra cost of a `saved` GRN can still be changed until a line is stock-locked (`GRN_COST_STOCK_LOCKED`), and an average-unit edit re-posts the affected lines. |
| Match of GRN lines to a vendor invoice (quantity-level) | **Implemented in the AP Invoice module** (see the banner); not a GRN screen. |
| AP-journal posting | **Implemented in the AP module** (`source = ap`), not by the GRN. Exact account mapping (`Dr` / `Cr`) is AP/GL configuration and is not documented here. |
| GRN-originated journal (accrual `Dr Inventory / Cr GRN Clearing`) | **Not implemented.** No GRN, inventory-transaction, or period-end code calls the GL module. |
| `post_type` field distinguishing `ap` / `consignment` / `cash` | **Confirmed with two consumers outside the GRN**: AP invoicing accepts only `ap`; the external export skips `consignment`. It changes nothing inside the GRN module. It stays editable after commit until an AP invoice takes the GRN. |
| Finance Manager period-close sign-off, GRN-Clearing aging report | **Not implemented.** No period-close feature specific to this module was found. |
| Finance Officer as a distinct workflow-stage role | **Not implemented.** `enum_stage_role` has no `finance` value; AP screens are gated by their own permission keys. |

For the AP and GL modules themselves, see [AP Invoice from GRN](/en/inventory/general-ledger/ap-invoice-from-grn) and the [general-ledger](/en/inventory/general-ledger) pages. Rules `GRN_POST_006`–`GRN_POST_009` and `GRN_XMOD_007` in [02-business-rules.md](./02-business-rules.md) are rewritten to point at the AP module.

## References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the four-state lifecycle; the posting event is `saved → committed` (average units post stock at save).
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — the persona whose commit posts inventory and advances the PO.
- GL module (documented on its own wiki page, not here): `../carmen-turborepo-backend/apps/micro-business/src/gl/`, gateway `apps/backend-gateway/src/application/{gl-jv,gl-posting,gl-reports}/`.
- AP module source: `../carmen-turborepo-backend/apps/micro-business/src/ap/`; frontend mock `../carmen-frontend/routes/accounting/accounts-payable/` (no API calls).
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — owns vendor-side resolution for receiving variance.
- Sibling: [02-business-rules.md](./02-business-rules.md) §5 / §6 — posting-rule table and cross-module rules.
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — legacy design source for the three-way-match / AP concept; design intent, not verified behavior.
- Related document: [purchase-order/credit-note](/en/inventory/purchase-order/credit-note).
