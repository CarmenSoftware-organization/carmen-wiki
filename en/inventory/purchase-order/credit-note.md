---
title: Credit Note
description: Vendor credit against a prior GRN — quantity_return deducts stock, amount_discount revalues cost; one product per GRN once, discount/tax capped by line and GRN share; submit goes draft → completed. No AP/GL posting.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: purchase-order, credit-note, accounting, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Credit Note

> **At a Glance**
> **Owner:** Procurement &nbsp;·&nbsp; **Table:** `tb_credit_note` (+ detail, comments) &nbsp;·&nbsp; **Lifecycle:** `draft` → `completed` on **Submit** (single transaction with the stock ledger); `in_progress` / `cancelled` / `voided` exist in the enum but nothing writes them &nbsp;·&nbsp; **Upstream:** [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; Post-receipt offset against a prior GRN — reverses the inventory cost layer (returns goods or revalues cost); no AP/GL posting exists.
> **Re-synced 2026-09-22** against `credit-note.{service,logic,validate}.ts` @ ef4d6f08f, `routes/procurement/credit-note/` @ 0713cbc9, Bruno `procurement/credit-note/` (7 files), e2e `601-cn` / `602-cn-reason`. Rules added 2026-09-17/21: each product on a GRN can be credited once; per-line discount / tax may not exceed the line value nor the GRN's proportional share; the server recomputes `return_base_qty`; the Stock Movement tab is a real API. **Corrected:** no approval workflow, no Void action, no period-close gate.

![Credit Note screen](/screenshots/purchase-order/credit-note.png)

![Credit Note detail screen](/screenshots/purchase-order/credit-note-detail.png)

## 1. What & Who

A **Credit Note (CRN)** is the post-receipt correction instrument in procure-to-pay. When a vendor over-bills, ships defective or short goods, or grants a retrospective rebate, the CRN documents the offset against the originating GRN and reverses the inventory cost layer. No AP-liability-posting code exists anywhere in the credit-note backend (see § 4). Two variants: **`quantity_return`** physically returns goods (decrements stock against the GRN's lots, reverses the cost layer) and **`amount_discount`** is a pure price correction (no inventory movement, revalues lot cost).

**Created by** Procurement when the vendor issues a credit invoice (`procurement.credit_note` is a CRUD permission resource in the SPA, `constant/permissions.ts`; the gateway declares no `@Permission` on the CN routes) &nbsp;·&nbsp; **Completed by** the same user pressing **Submit** — there is **no approval stage**: `submit()` moves `draft → completed` directly and posts the ledger in the same transaction (`credit-note.logic.ts` L513-640). `tb_credit_note` carries `workflow_*` / `user_action` columns, but no code in `credit-note.service.ts` / `credit-note.logic.ts` reads or writes a workflow (the only `workflow` hit is a notification event name). **Corrected 2026-09-22** — a prior version said "approved by workflow approvers (PO-style routing)". &nbsp;·&nbsp; **Read by** the costing engine and the period-end close (`period-end.validate.ts` `CN_COMPLETE = {completed, cancelled, voided}`; a `draft` CN counts as an open document that blocks closing the period).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Raise a CN against a GRN | Procurement → Credit Note → **New** (`/procurement/credit-note/new`) | Pick the vendor and GRN (`grn_id`); lines are added only through **Select from GRN** (`cn-add-item-dialog.tsx` — one row per received `product × location` on that GRN, carrying the GRN's qty, price, discount, tax and net); no blank rows. The vendor / GRN pickers search on demand (`c2ce1271`). |
| Pick `quantity_return` vs `amount_discount` | Header `credit_note_type` | Return moves stock; discount only revalues cost. Per line the form caps `return_qty ≤ GRN received qty` and, for `amount_discount`, `net_amount ≤ GRN net amount` (`cn-form-schema.ts` `maxReturnQty` / `maxCnAmount`, `039e3523`) |
| Credit the same product twice | — | **Blocked.** Each product on a GRN can be credited once across all non-cancelled, non-voided CNs (`findAlreadyCreditedIssues`, `credit-note.validate.ts` L105-138; keyed on product, not product × location, so the same goods cannot be credited once per location) |
| Check the ledger effect before / after submit | Detail → **Stock Movement** tab | Real API since 2026-09-21: `GET .../credit-notes/:id/stock-movements` — before submit a preview built from the lines (lot `-`), after submit the actual movements (lot, in/out qty, cost); `quantity_return` rows read as issues, `amount_discount` rows carry cost only (`cn-stock-table.tsx`, `use-credit-note.ts` L191; gateway `credit-notes.controller.ts` L142 — not yet in the Bruno collection) |
| Set return-to-stock vs write-off | (Automatic) | Engine consumes the GRN's own FIFO lots first, then falls back to other available lots for the same product+location; any variance between the CN's cost and the consumed lot's cost is recorded as `diff_amount` on the cost-layer row — **not** posted to any GL/write-off account (no such posting code exists) — see [costing](/en/inventory/costing) `COST_XMOD_006` |
| Submit | Detail → summary bar **Submit** (`cn-footer-action.tsx`) | `PATCH .../credit-notes/:id/submit` `{ doc_version }` — `draft → completed` and the inventory posting happen in **one** transaction (`55bfc6b5b`); lines that credit more than the location holds are deducted down to zero and the rest booked as a cost variance, reported back as `shortfalls[]` in the submit response. The UI locks the document (`isLocked`) once `completed` |
| Apply CN to AP | — | **Not implemented** — no AP debit-memo or AP-posting code exists anywhere in the credit-note backend; `completed` only triggers the inventory posting described in § 6 |
| Cite vendor's credit-invoice ref | Header `invoice_no` / `tax_invoice_no` | Vendor-side reference fields only; no downstream match feature exists (see [03-user-flow-finance.md](/en/inventory/purchase-order/03-user-flow-finance)). The list endpoint does not return them (`types/credit-note.ts`). |
| Void / cancel a posted CN | — | **Not implemented.** The gateway exposes only `GET`, `GET :id`, `GET :id/stock-movements`, `POST`, `PATCH :id`, `DELETE :id`, `PATCH :id/submit`, `GET :id/print-viewer` (`credit-notes.controller.ts`); no endpoint writes `cancelled` or `voided` (repo-wide the two values appear only in `notIn` filters and period-end sets). **Corrected 2026-09-22** — a prior version listed a Detail → **Void** action; the e2e gap report (`601-cn-gap.md`) independently confirms "no Commit and no Void button anywhere in this module" |
| Remove a draft | Detail → delete (`cn-header.tsx`, shown while `!isLocked`) | `DELETE .../credit-notes/:id` — "Only draft credit notes can be deleted" (`credit-note.service.ts` L507) |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "… returns a product that has already been credited on this receipt. Each product on a goods receipt can be credited once." (`CN_ERROR.GRN_LINE_ALREADY_CREDITED`, field `product_id`) | Another CN (not `cancelled` / `voided`) already credited this product on the same `grn_id` (`findAlreadyCreditedIssues`; `b6772667f`, 2026-09-21) | Remove the line; adjust the earlier CN instead |
| `DISCOUNT_EXCEEDS_LINE_AMOUNT` / `TAX_EXCEEDS_LINE_AMOUNT` | `discount_amount` or `tax_amount` on a line exceeds `return_qty × price` — a discount larger than the line would push `net_amount` negative (`findCreditNoteAmountIssues`, `credit-note.validate.ts` L40-80; the shared `findAmountCapIssues` rule also applied to PR / PO / GRN, `0293a6fa4`) | Correct the amount |
| "Discount on <line> is X, but the receipt only discounted Y …" / tax equivalent (fields `discount_amount` / `tax_amount`) | Line discount / tax exceeds the GRN line's discount / tax **pro-rated by the fraction being returned** (`findCreditNoteGrnAmountIssues`, L180-250; `1c6dcc262`) — returning a tenth of a delivery can credit back a tenth of its discount. Lines the GRN never received, or GRN lines with zero qty, are left alone | Reduce the amount to the GRN share |
| Form: `maxReturnQty` / `maxCnAmount` / "positive" `net_amount` | Client-side caps in `cn-form-schema.ts`: `return_qty ≤ _grn_received_qty`; for `amount_discount`, `net_amount ≤ _grn_net_amount` and `> 0` (`039e3523`) | Fix before Save; the server re-validates on submit |
| "Cannot submit credit note with status '<status>'. Only draft can be submitted." | Submit on a non-draft CN (`credit-note.logic.ts` L543) | — |
| "Only draft credit notes can be deleted" | `DELETE` on a completed CN | — |
| `409 Conflict` | `doc_version` in the `PATCH` / `submit` body is stale (`OptimisticLockError`, `credit-note.service.ts` L418) | Reload and re-apply |
| Submit response `shortfalls[]` ("N line(s) exceeded the stock on hand and were booked as a cost variance, not deducted.") | `quantity_return` lines credited more than the location held; the CN is still `completed` | Investigate stock; the difference is `diff_amount` on the cost layer, not a GL entry |
| "GRN required for quantity_return" | **Unconfirmed — not found as a literal.** `submit()` tolerates a missing `grn_id`: it marks the CN `completed` with the message "Credit note submitted (no inventory impact — missing GRN or details)" (L570-576). The form requires a GRN in practice because lines can only be added from one | — |
| "Period is closed — cannot void", "Rate not in history", "Tax rate must match GRN snapshot", "User not authorised at this stage" | **Removed 2026-09-22 — none of these messages exist.** No void action, no period gate on CN submit, no dynamic FX lookup, no stage authorisation (no workflow) in the credit-note backend | — |

## 4. Edge Cases

- **Money rounding.** Line money fields stored at `Decimal(20,5)`; computed totals round half-up to **2 decimals** at line level, then sum into header (matches PO/GRN rounding).
- **FX rate handling.** `exchange_rate` is a plain snapshot field, auto-populated once — either from the selected GRN's rate or from the currency master's current rate (`cn-general-fields.tsx`) — and then freely editable. **Unconfirmed/corrected:** no dynamic rate re-resolution keyed on `cn_date` and no FX gain/loss computation exists anywhere in the credit-note backend; this mirrors the same finding already established for PO/PR/GRN in [master-data/exchange-rate](/en/inventory/master-data/exchange-rate).
- **Return-to-stock vs write-off.** `quantity_return` consumes the GRN's own FIFO lots first, then falls back to other available lots for the same product+location (still FIFO order); no negative-inventory guard blocks this path — if no stock is available anywhere, `out_qty = 0` and the CN's cost is recorded entirely as `diff_amount` on the cost-layer row. **No GL/write-off-account posting exists anywhere in the backend** — `diff_amount` is a plain column on `tb_inventory_transaction_cost_layer`, not a general-ledger entry (confirmed absent module-wide; see [inventory/02-business-rules](/en/inventory/inventory/02-business-rules)).
- **Snapshot semantics.** Vendor name, product, currency, FX rate, tax rate, and pricelist refs are snapshotted at draft. Master-record edits do NOT retroactively change the CRN.
- **No voiding.** No endpoint or button voids or cancels a CN (`cancelled` / `voided` are enum members with no writer). **Corrected 2026-09-22** from "may only be voided while its period is open" — there is no void and no period gate; the period tables were also renamed `tb_period*` → `tb_inventory_period*` (2026-09-16). Period-end merely counts `draft` CNs as open documents (`CN_COMPLETE` excludes `draft`).
- **One product, one credit.** The once-per-GRN rule is keyed on `product_id` alone (`creditNoteGrnProductKey`), deliberately not on product × location, so goods stored in two locations cannot be credited twice; the check ignores CNs that are `cancelled` / `voided` (`credit-note.logic.ts` L265-290) — which today means it ignores nothing, since neither status is ever written.
- **Server-computed base quantity.** `return_base_qty = return_qty × return_conversion_factor` is derived on the server (`credit-note.logic.ts` L211-220; `55bfc6b5b`) — a client-sent value is ignored; the ledger moves `return_base_qty`.
- **Shortfall handling.** When a `quantity_return` line exceeds what the location holds, the deduction stops at what is there and the remainder is booked as a cost variance; the submit still succeeds (`completed`) and returns `shortfalls[]` so the operator knows the deduction was not clean.
- **No AP posting exists.** Neither `quantity_return` nor `amount_discount` creates a debit memo or any AP-side record on `completed`; no AP-posting code exists anywhere in the credit-note backend (`credit-note.logic.ts`, `credit-note.service.ts`, `inventory-transaction.service.ts`).

---

## 5. Data Model (Dev)

Source: tenant schema (`tb_credit_note`, `tb_credit_note_detail`, `tb_credit_note_comment`, `tb_credit_note_detail_comment`).

### 5.1 `tb_credit_note`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `cn_no` | `String? @db.VarChar` | Yes | CRN reference number; unique among non-deleted rows. |
| `cn_date` | `DateTime? @db.Timestamptz(6)` | Yes | Document date — used to generate `cn_no` (`generateCnNo`, `credit-note.service.ts` L560). Does not drive FX rate resolution (no such code exists) and is not passed to the inventory posting on submit (`executeCreditNoteQty` / `executeCreditNoteAmount` receive `grn_id`, `credit_note_id`, `detail_items`, `user_id` only); how the resulting movement is assigned to a `tb_inventory_period` is the inventory-transaction service's concern — see [inventory/transaction](/en/inventory/inventory/transaction). |
| `doc_status` | `enum_credit_note_doc_status` | No | `draft` → `completed` (the only transition any code performs — `submit()`). `in_progress`, `cancelled`, `voided` are declared (schema.prisma L211-217) and rendered by `CN_STATUS_CONFIG`, but no service writes them; the SPA's `CN_STATUS` enum omits `in_progress` altogether (`types/credit-note.ts`). |
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
| `cn_amount` | `Decimal(20,5)` | Yes | Credit amount column added by `20260710000000_add_cn_amount_credit_note_detail`; present in the schema (L448-523) but not referenced by `credit-note.logic.ts` / `credit-note.service.ts` at HEAD — treat as reserved. |
| `sub_total_price`, `net_amount`, `total_price` | `Decimal(20,5)` | Yes | Line totals in transaction currency; `net_amount` is what the form caps against the GRN net for `amount_discount`. |
| `base_*` | `Decimal(20,5)` | Yes | Same in BU base currency. |
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

- **`draft`** — editable; no AP or inventory effect. Save = `PATCH .../credit-notes/:id` with `doc_version` and `credit_note_detail.{add,update,delete}`; a stale `doc_version` returns `409`.
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

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note` (L335-410), `tb_credit_note_detail` (L448-523), `tb_credit_note_comment` (L412), `tb_credit_note_detail_comment` (L525), `tb_credit_note_reason` (L312), enums `enum_credit_note_type` (L206) and `enum_credit_note_doc_status` (L211-217).
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/credit-note/` — `credit-note.validate.ts` (once-per-GRN L105-138, line amount cap L40-80, GRN share L180-250), `credit-note.logic.ts` (`submit` L513-640, base-qty derivation L211, credited-key lookup L265-290), `credit-note.service.ts` (`generateCnNo` L560, delete guard L507, optimistic lock L418); gateway `apps/backend-gateway/src/application/credit-notes/credit-notes.controller.ts` (8 routes incl. `GET :id/stock-movements` L142).
- **API contracts:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/procurement/credit-note/` — 7 files (`GET-list`, `GET-by-id`, `POST-create`, `PATCH-update`, `PATCH-submit`, `DELETE-remove`, `GET-print-to-report`); `stock-movements` is not yet in the collection.
- **Frontend route:** `../carmen-inventory-frontend-react/routes/procurement/credit-note/` — `cn-form-schema.ts` (caps), `cn-add-item-dialog.tsx` (Select from GRN), `cn-stock-table.tsx` (Stock Movement tab), `cn-header.tsx` / `cn-footer-action.tsx` (Edit / delete / Submit only); `types/credit-note.ts`; `constant/credit-note.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/docs/user-stories/601-cn.md` (124 cases, `tests/601-cn.spec.ts` — 82 skipped, ~6 real oracles) and `docs/test-cases/gaps/601-cn-gap.md` (65 uncovered cases; its reviewer note is the best short description of the real UI: no Commit / Void buttons, statuses `draft · in_progress · completed · cancelled · voided`, no lot concept, no header amount field); `docs/user-stories/602-cn-reason.md` (18) / `gaps/602-cn-reason-gap.md` (27).
- **Carmen docs:** `../carmen/docs/cn/` — CN-PRD, CN-Business-Requirements, CN-API-Specification, CN-Page-Flow, CN-User-Flow-Diagram.
