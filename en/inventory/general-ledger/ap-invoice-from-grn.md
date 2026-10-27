---
title: AP Invoice from GRN
description: The one place a received-goods document reaches the ledger - an AP invoice built from committed GRN lines (grn-candidates, from-grn, matched_qty), the Dr inventory / Dr input VAT / Cr AP voucher it posts on approval, the GRN edit lock it causes, and the separate external export of GRN/CN and SR/SI/SO as Dr/Cr data.
published: true
date: 2026-10-27T00:00:00.000Z
tags: general-ledger, accounts-payable, grn, inventory, carmen-software
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# AP Invoice from GRN

> **At a Glance**
> **Verdict (backend `c9d788829`, 2026-10-27):** a GRN still posts nothing by itself. The ledger is reached **one step later**, by an **AP invoice** (`tb_ap_invoice`, `doc_source = grn`) that pulls committed `post_type = ap` GRN lines and, on final approval, posts one voucher (`source = ap`, `source_ref_type = ap_invoice`) through the subledger facade &nbsp;·&nbsp; **Direction of dependency:** GRN lines are the *source*; the AP invoice records how much of each line it has matched (`tb_ap_invoice_detail_source.matched_qty`) and a GRN that is on a live AP invoice can no longer be edited &nbsp;·&nbsp; **Stock and cost are untouched:** nothing here writes `tb_inventory_transaction*` or a cost layer; the invoice only creates a payable &nbsp;·&nbsp; **UI:** none yet - the React AP screens run on a browser mock (see [General Ledger](/en/inventory/general-ledger) § 4) &nbsp;·&nbsp; **Permission:** `accounting.ap` (licence feature, state `inactive` in the seed); only `void` carries a static `@Permission`

## 1. Scope

This page documents the accounts-payable feature **only where it consumes a GRN** and where the GRN side reacts. AP payment vouchers, withholding tax settlement, AR invoices/receipts, the AP/AR dashboards and the aged-payables views are accounting features with no inventory touch-point; they get a summary row on the [General Ledger](/en/inventory/general-ledger) landing and are otherwise left to the source (`apps/micro-business/src/ap/ap-payment/`, `.../ar/`).

## 2. The inventory-facing flow

```
committed GRN (post_type = ap)  --grn-candidates-->  pick items (same vendor + currency)
        |
        v  POST from-grn { grn_item_ids[], doc_date, vendor_invoice_no, invoice_date, ... }
  draft AP invoice (doc_type = invoice, doc_source = grn)
     one line per GRN item, quantity = received_qty - already matched
     Dr account = inventory account mapping (product, then item group)
     Cr account = vendor.ap_chart_of_accounts_id, else gl_setting.ap_control_account_id
        |
        v  submit
  no AP workflow in the BU  -> posted at once
  AP workflow configured    -> in_review -> (approve ... final approve) -> posted
        |
        v  posted: voucher Dr inventory + Dr input VAT / Cr AP, tax record, GRN lines locked
```

### 2.1 Routes (gateway `api/:bu_code/ap-invoice`, `application/ap-invoice/ap-invoice.controller.ts`)

| Route | Line | What it does |
|---|---|---|
| `GET grn-candidates?vendor_id&currency_id` | `:89` | Items of **committed** GRNs with `post_type = ap` for that vendor and currency whose `received_qty` is not yet fully matched; each row carries `remaining_qty` (`ap-invoice.service.ts` `grnCandidates :333`) |
| `POST from-grn` | `:329` | Builds a **draft** invoice from `grn_item_ids[]` (`createFromGrn :422`) |
| `POST` / `PUT :id` / `DELETE :id` | `:291` / `:370` / `:414` | Manual create (`doc_type` `invoice`, `debit_note`, `credit_note`, `deposit`); update and delete are draft-only |
| `GET`, `GET :id`, `GET :id/reference-candidates` | `:152` / `:197` / `:244` | List, detail, and the CN/DN/deposit documents this invoice may net against |
| `POST :id/submit` / `approve` / `review` / `reject` | `:457` / `:503` / `:549` / `:597` | Workflow actions (`enum_workflow_type.ap_invoice`) |
| `POST :id/void` | `:647` | Void a draft or reverse a posted invoice; static `@Permission({ 'accounting.ap': ['void'] })` |

The class carries `KeycloakGuard` + `PermissionGuard`, but the guard returns `true` on any route without its own `@Permission`, so only `void` is permission-gated; everything else is licence + Keycloak (`ap-invoice.controller.ts:40-66`).

### 2.2 Rules enforced when pulling GRN lines

| Rule | Error (`packages/error-catalog`) | Where |
|---|---|---|
| Every requested item exists | `AP_INVOICE_LINE_INVALID` ("one or more GRN items were not found") | `checkGrnItems` (`ap-invoice.service.ts:1357`) |
| GRN is `committed`, not deleted, `post_type = ap` (so `cash` and `consignment` GRNs cannot be invoiced) | `AP_GRN_NOT_COMMITTED` (422) | same |
| All items share one vendor and one currency | `AP_VENDOR_CURRENCY_MISMATCH` (422) | same |
| `remaining = received_qty - Σ matched_qty` of live lines on other non-void documents must be > 0 | `AP_GRN_OVER_MATCHED` (422) | `grnLines :468`; re-checked at submit/post with row locks (`checkGrnSources`, `ap-invoice.posting.ts:169`) |
| Product has an `inventory` account mapping (`tb_product_account_code_mapping`, product first, then item group) | `AP_INVOICE_LINE_INVALID` ("no inventory account mapping for product ...") | `resolveProductAccount` |
| Vendor invoice number unique per vendor among live, non-void documents | `AP_VENDOR_INVOICE_NO_DUPLICATE` (409) | partial index `apinvoice_vendor_invoice_no_u` |
| GL period of `doc_date` is open | `GL_PERIOD_NOT_OPEN` | checked at submit and again inside the post transaction |

Each invoice line stores its sources in `tb_ap_invoice_detail_source` (`good_received_note_id`, `grn_no`, `good_received_note_detail_item_id`, `matched_qty`, `grn_unit_price`, `matched_amount`, `variance_amount`). `variance_amount = line net - round2(matched_qty x grn_unit_price)`, i.e. the invoice-versus-receipt price difference (`ap-invoice.writer.ts:419-466`). The unit price on a from-GRN line starts as the GRN `received_price`, and the VAT profile as the GRN item's `tax_profile_id`.

## 3. The voucher it posts

On the final approval (or on `submit` when the BU has no AP workflow), `ApInvoicePosting.postInTx` (`ap-invoice.posting.ts:278`) builds the lines with `buildInvoiceJvLines` (`ap-invoice.logic.ts:393`) and hands them to `GlSubledgerPostingService.postFromSource` in the **same transaction** as the status change:

| Line | Account | Amount (base currency) |
|---|---|---|
| Dr | line `dr_chart_of_accounts_id` (the inventory account from the mapping) | `base_net_amount` |
| Dr | line `vat_chart_of_accounts_id`, else `gl_setting.input_vat_account_id` | `base_vat_amount` |
| Cr | line `cr_chart_of_accounts_id` (vendor AP account or `ap_control_account_id`) | `base_total_amount` |

A credit note flips every side; a deposit debits `advance_deposit_account_id` instead and carries no VAT. A zero amount line is skipped. The voucher is idempotent per (`source`, `source_ref_type`, `source_ref_id`) - a unique index `gljvheader_source_ref_u` - and its default prefix is `gl_setting.ap_jv_prefix_id`, then `auto_jv_prefix_id`. If the period is closed or a setting key is missing (`GL_SETTING_ACCOUNT_MISSING`), the whole approval rolls back and can be retried.

Side effects at post: a `tb_ap_invoice_tax` record is created (`tax_status = pending`, `expiry_claim_date = invoice_date + 6 months`; a credit note stores negative amounts; no VAT on any line deletes the record), and references (credit note / deposit netting) are applied.

**What it does not do:** it does not post a *Dr inventory / Cr GR-IR* at receiving time, does not compare the invoice price with the cost layer, and does not change `tb_inventory_transaction_cost_layer` - so a price variance (`variance_amount`) never revalues stock. The inventory asset is debited at **invoice** price, not at the GRN cost.

## 4. What the GRN side does in response

| Behaviour | Source |
|---|---|
| `GET good-received-note/:id` returns `ap_invoices: [{ id, doc_no, doc_status }]` - live (not void, not deleted) AP invoices that matched any line of the GRN | `good-received-note.service.ts:351,357`; `good-received-note.ap-link.ts:87` |
| Updating a **committed** GRN that is on a live AP invoice is refused with `GRN_AP_LINKED_NOT_EDITABLE` (400, "... already on AP invoice {doc_nos} ...") **before** the header-only rule runs | `good-received-note.ap-link.ts:122-153`; called from `update` (`good-received-note.service.ts:1499`) |
| A committed GRN with no AP invoice can still change only vendor-invoice facts (`invoice_no`, `invoice_date`, `invoice_f`, `payment_due_date`, credit-term fields, `description`, `note`, `post_type`); anything else is `GRN_COMMITTED_HEADER_ONLY` | `HEADER_EDITABLE_KEYS` (`good-received-note.ap-link.ts:19`) |
| The GRN screen disables editing when `ap_invoices` is non-empty and the GRN is committed | `carmen-frontend/routes/procurement/goods-receive-note/grn-header.tsx:61-65` |
| Voiding the AP invoice (draft: deleted/void directly; posted: reversal voucher) frees the matched quantity again - `checkGrnSources` and the lock query ignore `void` documents | `ap-invoice.posting.ts:169`, `voidPostedInTx :339` |

See [good-receive-note](/en/inventory/good-receive-note) for the GRN states and `post_type`.

## 5. Voiding

A draft is voided in place (tax record voided). A **posted** invoice is voided by a reversal voucher through the facade (`reverseBySource`), subject to, in order: no live payment voucher (`AP_INVOICE_HAS_PAYMENT`, 409), nothing applied against it by another document (`AP_INVOICE_IS_REFERENCED`, 409), and an open GL period for the void date (`GL_PERIOD_NOT_OPEN`). The GL screen's own void/reverse refuses the same voucher (`isSubledgerVoucher`, `gl-posting.service.ts:77`): void the **AP invoice**, not the journal voucher.

## 6. External export of the same data (read-only, pull)

Separately from posting, micro-business builds Dr/Cr data **on demand** from inventory documents for an external accounting system. Nothing is written to `tb_gl_jv_*`.

| Endpoint (`apps/backend-gateway/src/external-api/`) | Documents | Shape |
|---|---|---|
| `GET api/ext/v1/ap-invoices` | `GRN`, `CN` (final and voided) | vendor-invoice records, one line per received/returned item, accounts named by role (`debit_*` inventory, `ap_*` payable) plus tax amounts; CN amounts positive (reverse by `doc_type`); input-VAT account is the external system's job |
| `GET api/ext/v1/gl-journals` | `SR`, `SI`, `SO` (final and stock-moving voided) | one balanced Dr/Cr journal per document; documents that move no stock are excluded |

Query: `date_from`, `date_to` (inclusive, at most 366 days), optional `doc_types`, `date_field` (`document` default, or `updated` for incremental sync), `page`, `perpage` (1-200, default 50). Auth is a per-BU API key (`x-client-id` / `x-client-secret`, `BuApiKeyGuard`), not Keycloak; the BU comes from the key. Accounts come from `tb_account_mapping` only (migration `20261014100100_account_mapping`: `mapping_type` `AP` for `grn`/`cn`, `GL` for `adjustment`/`sr_in`/`sr_out`, keyed by location x product item group; see [chart-of-account-mapping](/en/inventory/master-data/chart-of-account-mapping)) - note this is a different table from the `tb_product_account_code_mapping` that the AP-invoice-from-GRN route in § 2 uses; a line whose account cannot be resolved is returned with `unmapped: true` and an `issues` entry rather than failing. Builders: `micro-business/src/inventory/accounting-export/builders/{grn.ap-builder,cn.ap-builder,sr.builder,stock-adjustment.builder}.ts`. A document appears in exactly one of the two endpoints. The GRN builder drops items at a consignment location, treats `cash` as AP, and excludes `consignment` GRNs entirely.

## 7. Edge Cases

| # | Scenario | Expected | Source |
|---|---|---|---|
| 1 | A second AP invoice pulls a GRN item a first (even draft) invoice already matched | `matchedQtyByItem` counts every non-void, non-deleted document, so `from-grn` gets only the remaining quantity, or `AP_GRN_OVER_MATCHED` when none is left; submit/post re-checks under row locks (`FOR NO KEY UPDATE`, ordered by id) so concurrent submits serialise | `grnLines`, `checkGrnSources` |
| 2 | GRN item has no inventory account mapping | `from-grn` refuses the whole request; create the invoice manually with an explicit `dr_chart_of_accounts_id` | `grnLines` |
| 3 | GRN is `cash` or `consignment` | Not in `grn-candidates`; `from-grn` returns `AP_GRN_NOT_COMMITTED` | `checkGrnItems` |
| 4 | Edit a committed GRN's line after an AP invoice (even a draft) pulled it | `GRN_AP_LINKED_NOT_EDITABLE`; void/delete the invoice first | `findActiveApInvoicesForGrn` counts any non-void, non-deleted invoice |
| 5 | Approve while the GL period is closed | `GL_PERIOD_NOT_OPEN`; approval rolls back, invoice stays `in_review` | `approve` doc comment |
| 6 | Void the GL voucher of an AP invoice from the journal screen | `GL_JV_IMMUTABLE`; void the invoice instead | `isSubledgerVoucher` |
| 7 | Void a posted invoice that has a payment | `AP_INVOICE_HAS_PAYMENT` | `voidPostedInTx` |
| 8 | Invoice price differs from GRN price | Stored as `variance_amount`; stock value unchanged, ledger carries the invoice price | `ap-invoice.writer.ts:466` |

## 8. Code findings (not fixed)

- **No AP-link guard on GRN void.** `findActiveApInvoicesForGrn` is called only from the GRN detail read and `update` (`good-received-note.service.ts:351,1499`); a grep of the GRN void path finds no use. Whether a committed GRN that sits on a *posted* AP invoice can be voided (leaving a payable against reversed stock) should be confirmed with a test.
- **`enum_gl_jv_source.inventory` is still never written** - the receiving side of the ledger exists only through this AP route and the export in § 6.
- **Frontend does not call these routes.** `routes/accounting/accounts-payable/shared/use-accounts-payable.ts` always builds `createApMockRepository`; no `fetch` of `ap-invoice` exists. Backend-only testing via Bruno / Swagger.

## 9. References

- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/ap/ap-invoice/` (`ap-invoice.service.ts`, `ap-invoice.posting.ts`, `ap-invoice.logic.ts`, `ap-invoice.writer.ts`, `ap-invoice.validation.ts`); `.../gl/gl-subledger-posting/gl-subledger-posting.service.ts`; `.../inventory/good-received-note/good-received-note.ap-link.ts`; `.../inventory/accounting-export/`.
- **Gateway:** `apps/backend-gateway/src/application/ap-invoice/ap-invoice.controller.ts`; `apps/backend-gateway/src/external-api/{ap-invoice,gl-journal}/`; query schemas `packages/rpc-contract/src/schemas/accounting-export-query.ts`.
- **Prisma:** `packages/prisma-shared-schema-tenant/prisma/schema.prisma` - `tb_ap_invoice :7182`, `tb_ap_invoice_detail :7267`, `tb_ap_invoice_detail_source :7350`, `tb_ap_invoice_reference :7370`, `tb_ap_invoice_tax :7390`, `enum_ap_invoice_doc_type :300`, `enum_ap_invoice_status :307`, `enum_ap_invoice_source :314`; migration `20260923060040_accounting_foundation_ap`.
- **Related:** [GL Posting and the Inventory Seam](/en/inventory/general-ledger/gl-posting), [good-receive-note](/en/inventory/good-receive-note), [credit-note](/en/inventory/purchase-order/credit-note).
