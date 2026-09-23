---
title: Good Receive Note (GRN) — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for good-receive-note.
published: true
date: '2026-09-22T18:00:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — Test Scenarios

> **At a Glance**
> **Module:** [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; **Personas covered:** Receiver, Purchaser, Finance (correction page), Audit / Config (correction page)
> **Run order:** primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**
> **Re-verified 2026-09-22:** expected behaviours below now follow the current posting model — **commit** posts stock and advances the PO; **average-costed business units** post stock already at save; void/reject unwind that early movement; extra cost and FOC are part of landed cost. See [02-business-rules.md](./02-business-rules.md) §1 and §5.

> **Executable coverage (E2E repo `../carmen-inventory-frontend-e2e/`):** spec `tests/501-grn.spec.ts` — **76 cases** (44 High / 24 Medium / 8 Low per `docs/user-stories/501-grn.md`), but `docs/test-cases/SPEC-HEALTH.md` records that **57 of the 76 have no `expect()` at all**. There is no `docs/test-cases/501-grn-core.md` catalog page; the two **gap reports** are the authoritative list of behaviours still lacking a failing oracle: `docs/test-cases/gaps/501-grn-core-gap.md` (**62 cases**, list · detail · edit · receive · tax/discount · status · permissions) and `docs/test-cases/gaps/501-grn-from-po-gap.md` (**24 cases**, `TC-GRN-040005`–`040028`, the `/from-po` wizard — which the spec never opens). `docs/test-cases/COVERAGE.md` maps route `/procurement/goods-receive-note` to `002-spa-smoke.spec.ts`, `501-grn.spec.ts`, `710-wastage-reporting.spec.ts`. This page does not mirror those cases.

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `good-receive-note` module. It groups GRN coverage by persona (Receiver, Purchaser, Finance, Audit / Config), inventories the per-persona test files, captures the cross-persona handoff scenarios that stitch individual paths together, and maps scenarios back to the canonical Playwright spec [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts). "Three-way-match outcomes" and a per-line `accepted_qty` quality-inspection trace remain out of scope — neither feature exists (re-checked 2026-09-22; see [01-data-model.md](./01-data-model.md) and [03-user-flow-finance.md](./03-user-flow-finance.md)).

`501-grn.spec.ts` is the **only** Playwright E2E file for the GRN module; three quarters of its cases walk the UI without asserting anything (see the coverage note above), so treat a mapped `TC-GRN-*` id as "a describe block with this name exists", not as proof the described behavior is asserted end-to-end. The E2E fixtures now log in as `…@carmensoftware.dev` users against BU `GR2VYNKQ` (`d2b35a1`), not `@blueledgers.com`.

## 2. Personas in Scope

- **Receiver**: Receiving / warehouse staff who physically take delivery, raise the GRN in `draft`, save it (`draft → saved` — validate, number, and on average-costed units post stock), and commit it (`saved → committed` — post stock if not yet, advance the PO).
- **Purchaser**: Procurement staff who own the upstream PO and review receiving variance; vendor-side coordination happens off-document.
- **Finance**: **Correction page** — no three-way-match, AP-posting, or Finance-role feature was confirmed for this module.
- **Audit / Config**: **Correction page** — no dedicated GRN configuration console or lot-recall tool was confirmed for this module.

## 3. Persona Test Files

- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Finance scenarios](./04-test-scenarios-finance.md) — correction page.
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md) — correction page.

## 4. Cross-Persona / Handoff Scenarios

The table below spans a handoff recorded in [03-user-flow.md](./03-user-flow.md) Section 4. Rows for "extra-cost allocation review by Finance", "batch commit", "post-commit void with elevated co-auth", and "scheduled auto-commit sweep" stay removed — none exist (re-checked 2026-09-22; post-commit void is now refused by the server outright).

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Full happy path against PO (FIFO business unit) | Receiver → Inventory Manager | Source PO at `po_status ∈ {approved, sent_or_print, partial}` with at least one line pending; BU `calculation_method = fifo`; receiver holds `procurement.goods_received_note.create` + `.commit`. | After **save**: `doc_status = saved`, real `grn_no` issued, **no** ledger row, PO untouched. After **commit**: one `tb_inventory_transaction` (`inventory_doc_type = good_received_note`) with one detail + cost layer per line (`lot_no = <location_code><YYMM><run>`, `cost_per_unit` = landed cost 2 dp, `extra_cost_amount`), `detail_item.inventory_transaction_id` set, PO junction + `tb_purchase_order_detail.received_qty` advanced, `po_status → partial` or `completed`; document locked; Stock Movement tab visible. |
| 1b | Same, on an **average** business unit | Receiver → Inventory Manager | As 1 but `calculation_method = average`; `grn_date` inside an open period. | After **save**: ledger already written (`tb_inventory_transaction.info.posted_at_save = true`), product `average_cost_per_unit` re-stamped on all its layers, PO **untouched**. After **commit**: no second ledger write; PO advanced; `info.po_receiving_applied = true`. |
| 2 | Manual GRN (no PO) | Receiver → Inventory Manager | `doc_type = manual`; vendor active; no upstream PO. | `saved` with no `purchase_order_detail_id` and `order_price = NULL` on every event (so no price-deviation check); commit posts stock; no PO to advance. |
| 3 | Partial receipt across two GRNs | Receiver → Inventory Manager → Receiver → Inventory Manager | Source PO line has pending qty larger than the first delivery. | First GRN committed → PO line `received_qty < order_qty − cancelled_qty`, `po_status = partial`; second GRN committed → `po_status = completed`. Nothing on the PO changes at either save. |
| 4 | Short receipt flagged for vendor follow-up | Receiver → Purchaser | Delivery contains a short-shipped line; receiver records `received_qty < order_qty` with a variance comment on the line. | Save passes (shortfall never breaches the deviation ceiling); commit posts the actual `received_qty` only; Purchaser reviews and coordinates vendor follow-up off-document — no in-app resolution workflow. |
| 5 | Extra cost and FOC in landed cost | Receiver → Inventory Manager | Extra-cost header with `allocate_extra_cost_type = by_value` and details summing to ฿200; two lines with stock quantities 10 and 4 (one line also `foc_qty = 1`). | At posting: shares `฿200 × 11/15` and `฿200 × 4/15` (`by_value` weights by `received_base + foc_base`); each line's cost layer `total_cost = base_net_amount + share`, `extra_cost_amount = share`, `in_qty` includes the FOC unit; `cost_per_unit` rounded 2 dp. With `by_qty` each line gets ฿100; with `manual` nothing is allocated. PO junction FOC-received counter advanced by 1. |
| 6 | Multi-PO consolidation into one GRN | Receiver | Same vendor and currency across two receivable POs; wizard step 2 multi-select; a mixed-currency selection is refused with the `mixedCurrencyError` toast (`from-po-content.tsx:93-95`). | One GRN with lines spanning both POs; commit advances `received_qty` on both POs in one transaction. |
| 7 | Void a saved GRN on an average unit after stock was issued | Receiver → Store Keeper (SR issue) → Receiver | Average unit; GRN `saved` (stock posted); an SR / stock-out has consumed part of the received lot. | `DELETE …/void` and `POST …/reject` both return **409 `GRN_RECEIPT_ALREADY_CONSUMED`**; document stays `saved`. Without the consumption, void succeeds, the movement is soft-deleted, `inventory_transaction_id` cleared, and the product average re-stamped. |
| 8 | Receipt date outside the open period | Receiver | Draft with `grn_date` in a `closed` period (or no period). | `POST …/verify` (`verify_state = create`) and commit / approve (and save on average units) return **422 `GRN_DATE_OUTSIDE_OPEN_PERIOD`**; the UI commit dialog offers "move to open period" which rewrites `grn_date` to the period's `start_at` before the `PATCH → /save → /commit` chain. |

## 5. E2E Test Mapping

`501-grn.spec.ts` is the **only** Playwright E2E file for the GRN module. It is structured as a single file with multiple `describe` blocks per functional area; auth is multi-role through `createAuthTest`, with the Purchase-role user for the happy / functional path and the Requestor-role user for permission-denial cases (users migrated to the `carmensoftware.dev` domain, BU `GR2VYNKQ`). The wizard route `/from-po` is **not** visited by any case — see `gaps/501-grn-from-po-gap.md`.

| `501-grn.spec.ts` describe block (TC group) | Cross-persona scenarios covered (Section 4) |
| ------------------------------------------- | ------------------------------------------- |
| `GRN — List` (TC-GRN-010001–010004) | 1 (entry point for listing GRNs) |
| `GRN — Filter / Search` (TC-GRN-020001–020005) | 1 (vendor / invoice-number search) |
| `GRN — Create from Single PO` (TC-GRN-030001–030005) | 1, 3 (first leg of the happy path and partial receipt) |
| `GRN — Create from Multiple POs` (TC-GRN-040002–040004) | 6 (multi-PO consolidation) |
| `GRN — Manual creation` (TC-GRN-050001–050005) | 2 (manual GRN end-to-end entry point) |
| `GRN — Edit Header` (TC-GRN-060001–060005) | 1, 2 (header edits before save-for-review) |
| `GRN — Add Line Item` (TC-GRN-070001–070004) | 1, 2, 3 (line entry across PO and manual paths) |
| `GRN — Edit Line Item` (TC-GRN-080001–080005) | 4 (editing `received_qty` on a short-shipped line) |
| `GRN — Delete Line Item` (TC-GRN-090001+) | 1, 3 (line cleanup before save) |
| `GRN — Extra Costs` (TC-GRN-100001+) | 5 (extra-cost entry; the allocation into landed cost is only observable on the Stock Movement tab after commit) |
| `GRN — Commit` (TC-GRN-110001+) | 1, 1b, 2, 3 (the describe block's annotation calling commit "the canonical posting event" is **correct again** as of `c815d67ce`; on average units stock is already posted at save) |
| `GRN — Void` (TC-GRN-120001–120004) | 7 — void from `draft` / `saved`. **Note:** `TC-GRN-120003`'s annotation describes voiding a `committed` GRN as reverting it to "RECEIVED" with reversed stock movements and a reversed Journal Voucher — the server now returns `GRN_COMMITTED_NOT_VOIDABLE` for a committed GRN and no JV exists; the test body asserts nothing. |
| `GRN — Financial Summary` (TC-GRN-130001+) | 5 (read-only totals view; header totals exclude extra cost) |
| `GRN — Stock Movements` (TC-GRN-140001+) | 1, 1b, 5 (`GET …/stock-movements` is a real API since 2026-08; the tab renders only for `committed` GRNs — `grnStockVisible()`) |
| `GRN — Comments` (TC-GRN-150001+) | 4 (variance comments) |
| `GRN — Attachments` (TC-GRN-160001+) | 1 (packing-list evidence) |
| `GRN — Activity Log` (TC-GRN-170001+) | 1 (audit trail across save / commit / void) |
| `GRN — Bulk Approval` (TC-GRN-180001+) | **Unconfirmed** — this describe block's annotations describe a per-line "APPROVED" status that does not exist in the schema (`tb_good_received_note_detail_item` has no status column); the test bodies have no assertions. Not mapped to any scenario above. |
| `GRN — * — Permission denial` (all `requestor@blueledgers.com` blocks) | RBAC layer across every scenario; the two persona files in Section 3 catalogue the persona-specific denial paths. |

## 6. References

- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — canonical Playwright E2E spec (76 cases, multi-role auth, all `TC-GRN-*` groups); generated catalogue `docs/user-stories/501-grn.md`; gap reports `docs/test-cases/gaps/501-grn-core-gap.md` (62) and `docs/test-cases/gaps/501-grn-from-po-gap.md` (24); health `docs/test-cases/SPEC-HEALTH.md`.
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — cross-persona handoffs that drive the integration scenarios above.
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — posting rules (re-verified 2026-09-22: commit posts; average units post stock at save).
- Per-persona detail: [Receiver](./04-test-scenarios-receiver.md), [Purchaser](./04-test-scenarios-purchaser.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md).
