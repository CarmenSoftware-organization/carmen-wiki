---
title: Credit Note
description: Vendor credit against a prior GRN — quantity_return deducts stock, amount_discount revalues cost; one product per GRN once, date must fall in the current period, return must be covered by stock on that date; only drafts are editable; submit goes draft → completed. No AP/GL posting.
published: true
date: '2026-10-27T00:00:00.000Z'
tags: purchase-order, credit-note, accounting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Credit Note

> **At a Glance**
> **Owner:** Procurement &nbsp;·&nbsp; **Table:** `tb_credit_note` (+ detail, comments) &nbsp;·&nbsp; **Lifecycle:** `draft` → `completed` on **Submit** (single transaction with the stock ledger); `in_progress` / `cancelled` / `voided` exist in the enum but nothing writes them &nbsp;·&nbsp; **Upstream:** [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; Post-receipt offset against a prior GRN — reverses the inventory cost layer (returns goods or revalues cost); no AP/GL posting exists.
> **Re-synced 2026-10-27** against `credit-note.{service,logic,validate,base-amounts}.ts` + `credit-note-return-stock.helper.ts` @ c9d788829, `routes/procurement/credit-note/` @ 391062b5, e2e `601-cn` / `602-cn-reason` / new `603-cn-doc-flow`. **New since 2026-09-22:** (1) `cn_date` must lie in the **current inventory period** on create and again on submit (`CREDIT_NOTE_DATE_NOT_CURRENT_PERIOD` / `CREDIT_NOTE_NO_OPEN_PERIOD`) — this corrects the earlier "no period gate"; (2) a `quantity_return` must be **covered by stock on the note's date** (`CREDIT_NOTE_INSUFFICIENT_STOCK`) on create, update and submit, so the old "deduct what is there, book the rest as variance" path now applies only to direct-type locations; (3) **only a `draft` can be edited** (`CREDIT_NOTE_ONLY_DRAFT_EDITABLE`; `doc_status` is no longer accepted by `PATCH`); (4) the server now derives every `base_*` amount on the lines from the note's `exchange_rate` and posts the ledger in base currency; (5) line-rule failures come back as catalog codes carrying a `failures[]` list; (6) the Select-from-GRN dialog locks products another CN already credited; (7) CN numbers are reserved through the shared running-code engine. An **AP module** also exists now, but its `credit_note` document type is separate from this table (§ 4).

> **Re-synced 2026-09-22** against `credit-note.{service,logic,validate}.ts` @ ef4d6f08f, `routes/procurement/credit-note/` @ 0713cbc9, Bruno `procurement/credit-note/` (7 files), e2e `601-cn` / `602-cn-reason`. Rules added 2026-09-17/21: each product on a GRN can be credited once; per-line discount / tax may not exceed the line value nor the GRN's proportional share; the server recomputes `return_base_qty`; the Stock Movement tab is a real API. **Corrected:** no approval workflow, no Void action, no period-close gate.

![Credit Note screen](/screenshots/purchase-order/credit-note.png)

![Credit Note detail screen](/screenshots/purchase-order/credit-note-detail.png)

## 1. What & Who

A **Credit Note (CRN)** is the post-receipt correction instrument in procure-to-pay. When a vendor over-bills, ships defective or short goods, or grants a retrospective rebate, the CRN documents the offset against the originating GRN and reverses the inventory cost layer. No AP-liability-posting code exists anywhere in the credit-note backend (see § 4). Two variants: **`quantity_return`** physically returns goods (decrements stock against the GRN's lots, reverses the cost layer) and **`amount_discount`** is a pure price correction (no inventory movement, revalues lot cost).

**Created by** Procurement when the vendor issues a credit invoice (`procurement.credit_note` is a CRUD permission resource in the SPA, `constant/permissions.ts`; the gateway declares no `@Permission` on the CN routes) &nbsp;·&nbsp; **Completed by** the same user pressing **Submit** — there is **no approval stage**: `submit()` moves `draft → completed` directly and posts the ledger in the same transaction (`credit-note.logic.ts` `submit` L730-890). `tb_credit_note` carries `workflow_*` / `user_action` columns, but no code in `credit-note.service.ts` / `credit-note.logic.ts` reads or writes a workflow (the only `workflow` hit is a notification event name). **Corrected 2026-09-22** — a prior version said "approved by workflow approvers (PO-style routing)". &nbsp;·&nbsp; **Read by** the costing engine and the period-end close (`period-end.validate.ts` `CN_COMPLETE = {completed, cancelled, voided}`; a `draft` CN counts as an open document that blocks closing the period).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Raise a CN against a GRN | Procurement → Credit Note → **New** (`/procurement/credit-note/new`) | Pick the vendor and GRN (`grn_id`); lines are added only through **Select from GRN** (`cn-add-item-dialog.tsx` — one row per received `product × location` on that GRN, carrying the GRN's qty, price, discount, tax and net); no blank rows. The vendor / GRN pickers search on demand (`c2ce1271`); the GRN picker only lists GRNs that can still be credited, so a saved note passes its own GRN as `savedGrn` to label the field. The Currency field is locked to the GRN's currency, read from either the nested `currency.id` or the flat `currency_id` (`cn-grn-currency.ts`, `grnCurrencyId`). `cn_date` must fall in the current inventory period (see § 3). |
| Pick `quantity_return` vs `amount_discount` | Header `credit_note_type` | Return moves stock; discount only revalues cost. Per line the form caps `return_qty ≤ GRN received qty` and, for `amount_discount`, `net_amount ≤ GRN net amount` (`cn-form-schema.ts` `maxReturnQty` / `maxCnAmount`, `039e3523`) |
| Credit the same product twice | — | **Blocked.** Each product on a GRN can be credited once across all non-cancelled, non-voided CNs (`findAlreadyCreditedIssues`, `credit-note.validate.ts` L133; keyed on product, not product × location, so the same goods cannot be credited once per location). The dialog now enforces it up front: `useGrnCreditedProducts` calls `GET good-received-notes/:id/ref` (staleTime 0) and disables, with "Credited on <cn_no>", every product another CN holds; the note being edited does not lock its own products (`currentCnNo`) — `cn-add-item-dialog.tsx`, `use-grn-credited-products.ts` |
| Check the ledger effect before / after submit | Detail → **Stock Movement** tab | Real API since 2026-09-21: `GET .../credit-notes/:id/stock-movements` — before submit a preview built from the lines (lot `-`), after submit the actual movements (lot, in/out qty, cost); `quantity_return` rows read as issues, `amount_discount` rows carry cost only (`cn-stock-table.tsx`, `use-credit-note.ts`; gateway `credit-notes.controller.ts` L142 — not yet in the Bruno collection) |
| Set return-to-stock vs write-off | (Automatic) | Engine consumes the GRN's own FIFO lots first, then falls back to other available lots for the same product+location, only after the stock-on-date check below has passed (direct-type locations are exempt from that check); any variance between the CN's cost and the consumed lot's cost is recorded as `diff_amount` on the cost-layer row — **not** posted to any GL/write-off account (no such posting code exists) — see [costing](/en/inventory/costing) `COST_XMOD_006` |
| Submit | Detail → summary bar **Submit** (`cn-footer-action.tsx`, claims the form's primary-button slot) | `PATCH .../credit-notes/:id/submit` `{ doc_version }` — re-checks the period (`checkDateInActivePeriod`, L763) and stock cover (`checkReturnCovered`, L769), then `draft → completed` and the inventory posting happen in **one** transaction (`55bfc6b5b`): base amounts are re-derived onto the lines, the movement is posted `as_of` the note's `cn_date`, and the lines' price is converted to base currency (`calcBase(price, exchange_rate)`) before it is compared with lot cost. A `quantity_return` line at a **direct** location that credits more than it holds is still deducted down to zero with the rest booked as a cost variance, reported as `shortfalls[]` in the submit response. The UI locks the document (`isLocked`) once `completed` |
| Apply CN to AP | — | **Not implemented** — no AP debit-memo or AP-posting code exists anywhere in the credit-note backend; `completed` only triggers the inventory posting described in § 6 |
| Cite vendor's credit-invoice ref | Header `invoice_no` / `tax_invoice_no` | Vendor-side reference fields only; no downstream match feature exists (see [03-user-flow-finance.md](/en/inventory/purchase-order/03-user-flow-finance)). The list endpoint does not return them (`types/credit-note.ts`). |
| Void / cancel a posted CN | — | **Not implemented.** The gateway exposes only `GET`, `GET :id`, `GET :id/stock-movements`, `POST`, `PATCH :id`, `DELETE :id`, `PATCH :id/submit`, `GET :id/print-viewer` (`credit-notes.controller.ts`); no endpoint writes `cancelled` or `voided` (repo-wide the two values appear only in `notIn` filters and period-end sets). **Corrected 2026-09-22** — a prior version listed a Detail → **Void** action; the e2e gap report (`601-cn-gap.md`) independently confirms "no Commit and no Void button anywhere in this module" |
| Edit a saved note | Detail → Edit → Save (`PATCH .../credit-notes/:id`) | Allowed only while `doc_status = draft`: `checkEditable` returns `CREDIT_NOTE_ONLY_DRAFT_EDITABLE` otherwise (`credit-note.logic.ts` L232, called from `update` L612-615). The gateway update schema omits `doc_status` (`CreditNoteSchema.omit({ doc_status: true })`) — before `c447fa30f` a `PATCH` could pull a `completed` note back to `draft` and a second Submit moved the stock again |
| Remove a draft | Detail → delete (`cn-header.tsx`, shown while `!isLocked`) | `DELETE .../credit-notes/:id` — `CREDIT_NOTE_ONLY_DRAFT_DELETABLE` "Only draft credit notes can be deleted" (`credit-note.service.ts` L534; was a bare `VALIDATION_FAILURE` string before 2026-10) |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `CREDIT_NOTE_LINE_ALREADY_CREDITED` (3050005) "Line {line} ({product}) returns a product already credited on this receipt — each product on a goods receipt can be credited once" (`CN_ERROR.GRN_LINE_ALREADY_CREDITED`, field `product_id`) | Another CN (not `cancelled` / `voided`) already credited this product on the same `grn_id` (`findAlreadyCreditedIssues`; `b6772667f`, 2026-09-21) | Remove the line; adjust the earlier CN instead |
| `CREDIT_NOTE_DISCOUNT_EXCEEDS_LINE` (3050006) / `CREDIT_NOTE_TAX_EXCEEDS_LINE` (3050007) | `discount_amount` or `tax_amount` on a line exceeds `return_qty × price` — a discount larger than the line would push `net_amount` negative (`findCreditNoteAmountIssues`, `credit-note.validate.ts` L76; the shared `findAmountCapIssues` rule also applied to PR / PO / GRN, `0293a6fa4`) | Correct the amount |
| "Discount on <line> is X, but the receipt only discounted Y …" / tax equivalent (fields `discount_amount` / `tax_amount`) | Line discount / tax exceeds the GRN line's discount / tax **pro-rated by the fraction being returned** (`findCreditNoteGrnAmountIssues`, L224; `1c6dcc262`; catalog `CREDIT_NOTE_DISCOUNT_EXCEEDS_GRN` / `CREDIT_NOTE_TAX_EXCEEDS_GRN`) — returning a tenth of a delivery can credit back a tenth of its discount. Lines the GRN never received, or GRN lines with zero qty, are left alone | Reduce the amount to the GRN share |
| `CREDIT_NOTE_DATE_NOT_CURRENT_PERIOD` (3050003) "A credit note can only be dated inside the current period ({period}: {start} to {end})" / `CREDIT_NOTE_NO_OPEN_PERIOD` (3050004) | `cn_date` is outside the **current** inventory period — the oldest period still open or locked, which can drift behind the calendar — or no period is open at all (`assertDateInCurrentPeriod`, `inventory-period.helper.ts` L307). Checked on create (`credit-note.logic.ts` L110) and again on submit (L763) because the period can close while the note sits in draft | Change `cn_date` into the named period, or ask finance to open a period |
| `CREDIT_NOTE_INSUFFICIENT_STOCK` (3050011) "Not enough {product} at {location} to return on {date}: {on_hand} available, returning {requested} (lowest balance from {date} on falls on {short_on})" | `quantity_return` takes more of a product than the location held on `cn_date`, summed per product over the lines the note will hold after the edit; the same stock-out rule as other outbound documents (period brought-forward + movements up to the date, without leaving a later day short). Runs on create, update and submit (`checkReturnCovered` L437 → `findReturnShortage`, `credit-note-return-stock.helper.ts`). Direct-type locations are skipped (receipts there are expensed on arrival and hold nothing) | Lower the return qty or move the date |
| `CREDIT_NOTE_ONLY_DRAFT_EDITABLE` (3050010) | `PATCH` on a note that is not `draft` | — |
| Form: `maxReturnQty` / `maxCnAmount` / "positive" `net_amount` | Client-side caps in `cn-form-schema.ts`: `return_qty ≤ _grn_received_qty`; for `amount_discount`, `net_amount ≤ _grn_net_amount` and `> 0` (`039e3523`) | Fix before Save; the server re-validates on submit |
| "Cannot submit credit note with status '<status>'. Only draft can be submitted." | Submit on a non-draft CN (`credit-note.logic.ts` L754) | — |
| "Only draft credit notes can be deleted" | `DELETE` on a completed CN | — |
| `409 Conflict` | `doc_version` in the `PATCH` / `submit` body is stale (`OptimisticLockError`, `credit-note.service.ts` L424) | Reload and re-apply |
| Submit response `shortfalls[]` ("N line(s) exceeded the stock on hand and were booked as a cost variance, not deducted.") | `quantity_return` lines credited more than a **direct-type** location held (other locations are stopped earlier by `CREDIT_NOTE_INSUFFICIENT_STOCK`); the CN is still `completed` | Investigate stock; the difference is `diff_amount` on the cost layer, not a GL entry |
| "GRN required for quantity_return" | **Unconfirmed — not found as a literal.** `submit()` tolerates a missing `grn_id`: it marks the CN `completed` with the message "Credit note submitted (no inventory impact — missing GRN or details)" (`submit`, L790-800). The form requires a GRN in practice because lines can only be added from one | — |
| "Period is closed — cannot void", "Rate not in history", "Tax rate must match GRN snapshot", "User not authorised at this stage" | **Still absent (the "period gate" part changed 2026-10-27):** these exact messages do not exist. There is no void action, no dynamic FX lookup, no stage authorisation (no workflow). A period gate **does** now exist on create and submit, but as `CREDIT_NOTE_DATE_NOT_CURRENT_PERIOD`, not a void-time message | — |

## 4. Edge Cases

- **Money rounding.** Line money fields stored at `Decimal(20,5)`; computed totals round half-up to **2 decimals** at line level, then sum into header (matches PO/GRN rounding).
- **FX rate handling.** `exchange_rate` is a plain snapshot field, auto-populated once — from the selected GRN's rate or the currency master's rate (`cn-general-fields.tsx`) — and then editable. No dynamic re-resolution keyed on `cn_date` and no FX gain/loss computation exists. **New 2026-10:** the server derives every `base_*` field on each line from the document-currency amounts and the note's rate (`calcCreditNoteBaseAmounts`, `credit-note.base-amounts.ts`: price, sub-total, discount, net, tax, total, extra cost), on create, on update (lines not touched are re-based when the header rate changes, `credit-note.service.ts` L465-501) and again on submit (`credit-note.logic.ts` L816). Before, `base_*` stayed at 0 unless the client sent it. Mirrors the shared pattern in [master-data/exchange-rate](/en/inventory/master-data/exchange-rate).
- **Return-to-stock vs write-off.** `quantity_return` first has to pass the stock-on-date check (`CREDIT_NOTE_INSUFFICIENT_STOCK`, § 3), except at direct-type locations. The posting then consumes the GRN's own FIFO lots first and falls back to other available lots for the same product+location, `as_of` the note's date. At a direct location with no stock, `out_qty = 0` and the cost is booked entirely as `diff_amount` on the cost-layer row. **No GL/write-off-account posting exists** — `diff_amount` is a plain column on `tb_inventory_transaction_cost_layer` (see [inventory/02-business-rules](/en/inventory/inventory/02-business-rules)).
- **Snapshot semantics.** Vendor name, product, currency, FX rate, tax rate, and pricelist refs are snapshotted at draft. Master-record edits do NOT retroactively change the CRN.
- **No voiding.** No endpoint or button voids or cancels a CN (`cancelled` / `voided` have no writer). Period-end counts `draft` CNs as open documents (`CN_COMPLETE` excludes `draft`). The only period rule is the create/submit date gate (§ 3).
- **One product, one credit.** The once-per-GRN rule is keyed on `product_id` alone (`creditNoteGrnProductKey`), so goods stored in two locations cannot be credited twice; it ignores `cancelled` / `voided` CNs (`loadCreditedGrnLineKeys`, `credit-note.logic.ts` L386-405) — which today ignores nothing, since neither status is written. The note being edited is excluded from its own check.
- **Server-computed base quantity.** `return_base_qty = return_qty × return_conversion_factor` is derived on the server from the product's unit factor (`credit-note.logic.ts` L324-369; `55bfc6b5b`) — a client-sent value is ignored, and a unit the product cannot be returned in leaves the stored factor untouched; the ledger moves `return_base_qty`.
- **Shortfall handling.** Only at direct-type locations can a `quantity_return` exceed what the location holds (other locations are refused earlier): the deduction stops at what is there, the remainder is booked as a cost variance, the submit still succeeds and returns `shortfalls[]`.
- **No AP posting from this table.** Neither type creates a debit memo or AP row on `completed`; nothing in `credit-note.*` calls AP or GL. The new AP module (`apps/micro-business/src/ap/`) has its own `credit_note` document type (running code `AP-CN`) that never reads `tb_credit_note`; AP invoices are built from GRN items, so a procurement CN does not reduce an AP invoice automatically. See [general-ledger](/en/inventory/general-ledger).

---

## 5. Data Model (Dev)

Source: tenant schema (`tb_credit_note`, `tb_credit_note_detail`, `tb_credit_note_comment`, `tb_credit_note_detail_comment`).

### 5.1 `tb_credit_note`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `cn_no` | `String? @db.VarChar` | Yes | CRN reference number; unique among non-deleted rows. |
| `cn_date` | `DateTime? @db.Timestamptz(6)` | Yes | Document date — generates `cn_no` (`generateCnNo` → `reserveDocumentNumbers`, `credit-note.service.ts` L561), must lie in the current inventory period (create + submit), and since 2026-10 is passed as `as_of` to `executeCreditNoteQty` (return only what existed that day, at that day's cost) and used by the stock-cover check. It does not drive FX rate resolution. |
| `doc_status` | `enum_credit_note_doc_status` | No | `draft` → `completed` (the only transition any code performs — `submit()`; `PATCH` no longer accepts `doc_status`). `in_progress`, `cancelled`, `voided` are declared (schema.prisma L211-217) and rendered by `CN_STATUS_CONFIG`, but no service writes them; the SPA's `CN_STATUS` enum omits `in_progress` altogether (`types/credit-note.ts`). |
| `credit_note_type` | `enum_credit_note_type` | No | `quantity_return` or `amount_discount`. |
| `vendor_id`, `vendor_name` | `String? @db.Uuid` / `VarChar` | Yes | Snapshot from `tb_vendor` at draft. |
| `grn_id`, `grn_no`, `grn_date` | mixed | Yes | Anchor GRN — required for `quantity_return`, optional for `amount_discount`. |
| `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price` | mixed | Yes | Optional pricelist reference. |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | Currency + rate snapshot, auto-populated once from the selected GRN's or currency master's rate at edit time and freely editable thereafter. **Corrected:** not dynamically resolved against `cn_date` — no such code exists. |
| `cn_reason_id`, `cn_reason_name`, `cn_reason_description` | mixed | Yes | FK + snapshot to `tb_credit_note_reason` (config screen `/config/credit-note-reason`, e2e `602-cn-reason`). |
| `invoice_no`, `invoice_date`, `tax_invoice_no`, `tax_invoice_date` | mixed | Yes | Vendor's credit-invoice reference. Optional in the payload (`invoice_date` must be omitted, not `""`, when empty — ISO-8601 datetime); not returned by the list endpoint. |
| `workflow_id`, `workflow_*`, `user_action` | mixed | Yes | Declared (same shape as PO; `workflow_history` default `{}`) but **unused** — no CN code path reads or writes them. |
| `last_action`, `last_action_*` | mixed | Yes | Most recent transition. |
| `note`, `description`, `info`, `dimension`, `doc_version` | mixed | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([cn_no, deleted_at])` map `creditnote_cn_no_u`; `@@index([cn_no])`. FKs to `tb_vendor`, `tb_currency`, `tb_good_received_note`, `tb_credit_note_reason` — all `onDelete: NoAction`.

### 5.2 `tb_credit_note_detail`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id`, `credit_note_id`, `sequence_no` | mixed | No / No / Yes | PK, parent FK, ordinal. |
| `inventory_transaction_id` | `String? @db.Uuid` | Yes | FK to originating `tb_inventory_transaction` for `quantity_return`. Null for `amount_discount`. |
| `location_id`, `location_*`, `delivery_point_*` | mixed | Yes | Original receipt location; return sources from same. |
| `product_id`, `product_*` | mixed | No / Yes | Product snapshot. |
| `return_qty`, `return_unit_*`, `return_conversion_factor`, `return_base_qty` | `Decimal(20,5)` / mixed | Yes | Return qty in user unit + base. `0` for `amount_discount`. |
| `price` | `Decimal(20,5)` | Yes | Unit price — typically the GRN line price. |
| `tax_*`, `is_tax_adjustment` | mixed | Yes | Tax snapshot + base conversion. |
| `discount_*`, `is_discount_adjustment` | mixed | Yes | Discount snapshot + base. |
| `extra_cost_amount`, `base_extra_cost_amount` | `Decimal(20,5)` | Yes | Allocated extra-cost credit (e.g. freight). |
| `cn_amount` | `Decimal(20,5)` | Yes | Credit amount column added by `20260710000000_add_cn_amount_credit_note_detail`; present in the schema (L611) but not referenced by `credit-note.logic.ts` / `credit-note.service.ts` at HEAD — treat as reserved. |
| `sub_total_price`, `net_amount`, `total_price` | `Decimal(20,5)` | Yes | Line totals in transaction currency; `net_amount` is what the form caps against the GRN net for `amount_discount`. |
| `base_*` | `Decimal(20,5)` | Yes | Same in BU base currency; derived on the server from the note's `exchange_rate` (`calcCreditNoteBaseAmounts`) — client values are replaced. |
| `info`, `dimension`, `doc_version`, audit | — | Yes | Standard metadata. |

**Constraints:** `@@unique([credit_note_id, sequence_no, deleted_at])`; `@@index([credit_note_id, sequence_no])`. FKs `onDelete: NoAction`.

### 5.3 Comment tables

`tb_credit_note_comment` and `tb_credit_note_detail_comment` follow the canonical comment shape — see [purchase-request/01-data-model](/en/inventory/purchase-request/01-data-model).

## 6. Workflow / Business Rules

`doc_status`: `draft` → `completed` (terminal) on **Submit**. That is the whole live machine.

```
[*] → draft ──(PATCH :id/submit, one transaction: status + ledger)──► completed
        │
        └──(DELETE :id, draft only)──► removed (soft delete)

  in_progress / cancelled / voided : declared in enum_credit_note_doc_status,
                                     rendered by CN_STATUS_CONFIG, never written
```

- **`draft`** — the only editable state; no AP or inventory effect. Save = `PATCH .../credit-notes/:id` with `doc_version` and `credit_note_detail.{add,update,delete}`; a stale `doc_version` returns `409`.
- **`completed`** — set by `submit()` together with the inventory posting (`quantity_return`: `executeCreditNoteQty` deducts `return_base_qty` from the GRN's lots, FIFO or average per the BU's costing method; `amount_discount`: cost revaluation / `diff_amount` variance) and the `inventory_transaction_id` back-link written onto every line. No AP debit memo or GL entry is created for either type.
- **`in_progress`**, **`cancelled`**, **`voided`** — **no writer exists.** A prior version of this section described an approval stage reusing the PO workflow, a cancel path, and a period-bounded void that "reverses every posting"; none of that is in the code (`credit-note.logic.ts`, `credit-note.service.ts`, gateway `credit-notes.controller.ts`). Correcting a `completed` CN today means a compensating document, not a reversal.

**GRN anchor:** lines come only from the anchor GRN's received `product × location` rows, `return_qty` is capped at the GRN received qty, discount / tax at the line value and at the GRN's pro-rated share, and each product on that GRN can be credited by one CN only. **Authorisation:** the SPA gates the routes on `procurement.credit_note` (CRUD); the backend applies tenant scoping only — no stage or role check.

## 7. Cross-References

- [purchase-order](/en/inventory/purchase-order) — the PO behind the original GRN. **Unconfirmed:** whether CRN totals feed any PO open / received figure — `received_qty` on `tb_purchase_order_detail` is incremented by GRN posting only and no CN code touches PO rows.
- [good-receive-note](/en/inventory/good-receive-note) — anchor for every `quantity_return` line.
- [costing](/en/inventory/costing) — `COST_POST_003` (amount revaluation), `COST_XMOD_006` (lot cost reversal), `COST_CALC_005` (credit-note-amount lot revaluation — corrected; not FX, as previously miscited here).
- [master-data/credit-note-reason](/en/inventory/master-data/credit-note-reason) — reason taxonomy.
- [master-data/exchange-rate](/en/inventory/master-data/exchange-rate) — rate snapshot pattern shared with PO/PR/GRN (auto-populate once, freely editable; no dynamic re-resolution).
- [master-data/vendor](/en/inventory/master-data/vendor) — vendor snapshot. AP debit-memo routing is unconfirmed (no such code exists).

## 8. References

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note` (L451-526), `tb_credit_note_detail` (L564-639), `tb_credit_note_comment` (L528), `tb_credit_note_detail_comment` (L641), `tb_credit_note_reason` (L428), enums `enum_credit_note_type` (L201) and `enum_credit_note_doc_status` (L206-212).
- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/procurement/credit-note/` — `credit-note.validate.ts` (once-per-GRN L133, line amount cap L76, GRN share L224), `credit-note.logic.ts` (`create` L105, `checkEditable` L232, `checkDateInActivePeriod` L258, base-qty derivation L324-369, credited-key lookup L386, `checkReturnCovered` L437, `update` L612, `submit` L730), `credit-note-return-stock.helper.ts` (`findReturnShortage`), `credit-note.base-amounts.ts`, `credit-note.service.ts` (`update` L409, optimistic lock L424, delete guard L534, `generateCnNo` L561); gateway `apps/backend-gateway/src/application/credit-notes/credit-notes.controller.ts` (8 routes incl. `GET :id/stock-movements` L142).
- **API contracts:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/procurement/credit-note/` — 7 files (`GET-list`, `GET-by-id`, `POST-create`, `PATCH-update`, `PATCH-submit`, `DELETE-remove`, `GET-print-to-report`); `stock-movements` is not yet in the collection.
- **Frontend route:** `../carmen-frontend/routes/procurement/credit-note/` — `cn-form-schema.ts` (caps), `cn-add-item-dialog.tsx` (Select from GRN), `cn-stock-table.tsx` (Stock Movement tab), `cn-header.tsx` / `cn-footer-action.tsx` (Edit / delete / Submit only), `use-grn-credited-products.ts`, `cn-grn-currency.ts`; `types/credit-note.ts`; `constant/credit-note.ts`.
- **E2E:** `../carmen-frontend-e2e/docs/user-stories/601-cn.md` (124 cases, `tests/601-cn.spec.ts` — 82 skipped, ~6 real oracles) and `docs/test-cases/gaps/601-cn-gap.md` (65 uncovered cases; its reviewer note is the best short description of the real UI: no Commit / Void buttons, statuses `draft · in_progress · completed · cancelled · voided`, no lot concept, no header amount field); `docs/user-stories/602-cn-reason.md` (18) / `gaps/602-cn-reason-gap.md` (27); new 2026-10 `docs/user-stories/603-cn-doc-flow.md` (7 cases, `tests/603-cn-doc-flow.spec.ts` — create from a committed GRN, reopen, already-credited product locked, edit, delete draft, Submit → `completed` with stock returned; none covers the new period / stock-cover errors).
- **Carmen docs:** `../carmen/docs/cn/` — CN-PRD, CN-Business-Requirements, CN-API-Specification, CN-Page-Flow, CN-User-Flow-Diagram.
