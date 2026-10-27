---
title: Good Receive Note (GRN) — Test Scenarios — Finance
description: Why no Finance test scenarios live in the GRN module, what the backend AP Invoice module now covers, and where to test the GRN side of the link.
published: true
date: '2026-10-27T00:00:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, finance, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — Test Scenarios — Finance

> **At a Glance**
> **Status:** Status page — the GRN module has no dedicated Finance persona or screen. Since 2026-10 the backend AP Invoice module matches committed GRN lines and posts to the GL ([AP Invoice from GRN](/en/inventory/general-ledger/ap-invoice-from-grn)); its tests belong with that module. The GRN-side effects to test are listed below.

> ⚠️ **Major correction this pass (2026-07-15).** The previous version of this page listed roughly 30 scenarios (FIN-HP-01 through FIN-EDGE-06) covering pre-AP extra-cost-allocation adjustment, a three-way match against a vendor invoice, AP-journal posting (`Dr GRN Clearing / Cr AP-Trade`), FX-adjustment postings, and period-close reconciliation. None of this maps to current source:

- **Re-checked 2026-10-27:** an AP Invoice module now exists in the backend (`apps/micro-business/src/ap/ap-invoice`, `ap-payment`); AP posting writes GL journals with `source = ap` (`ap-invoice.posting.ts:291`). No GRN, inventory-transaction, or period-end code calls the GL module, and `enum_gl_jv_source.inventory` has no writer. The frontend `routes/accounting` screens (AP invoice / payment, AR, JV) run on a browser mock (`ap-mock-repository.ts`, `documentsFor()`) and call no API, so there is no UI path to test.
- The good-received-note backend module has five lifecycle operations (`save`, `commit`, `approve`, `reject`, `voidGrnById`) — none touch a journal, ledger, or AP entity.
- `enum_stage_role` has no `finance` member.
- The `501-grn.spec.ts` E2E spec has no describe block for invoice matching, AP posting, or period close (and no AP spec exists in `../carmen-frontend-e2e/tests`); its "Financial Summary" group (`TC-GRN-1300xx`) only exercises a read-only totals tab on the GRN detail page, with no assertions tying it to a three-way match or a journal entry.

> **Executable coverage:** `../carmen-frontend-e2e/tests/501-grn.spec.ts` groups `GRN — Extra Costs` (`TC-GRN-1000xx`) and `GRN — Financial Summary` (`TC-GRN-1300xx`); gap report `docs/test-cases/gaps/501-grn-core-gap.md` (tax / discount section). No AP or GL spec exists; the new opt-in `502-grn-doc-flow.spec.ts` covers only manual-GRN draft/edit/delete/saved-on-AVG.

| Previously-claimed scenario group | Finding |
| --- | --- |
| FIN-HP-01..03 (pre-AP extra-cost allocation switch, `manual` / `by_value` / `by_qty` recompute with GL delta posting) | Extra-cost **allocation is now real** (2026-09-10): `allocateExtraCost()` splits the total at posting — `by_qty` equal shares, `by_value` weighted by stock quantity, `manual` nothing — into landed cost and `tb_inventory_transaction_cost_layer.extra_cost_amount`. There is still no GL delta, no re-allocation after posting (a committed GRN is never re-posted), and no per-line manual entry. Test it from the Receiver side: [04-test-scenarios](./04-test-scenarios.md) Scenario 5, [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) RCV-EDGE-02. |
| FIN-HP-04..06 (clean match, partial match, price-within-tolerance auto-pass) | **Backend only, AP-module scope.** Quantity matching exists (`matched_qty` ≤ `received_qty`, `AP_GRN_OVER_MATCHED`; `variance_amount` stored per source) but there is no price-tolerance auto-pass. API-test from the AP side; the GRN-side checks are in the table below. |
| FIN-HP-07 (FX adjustment on rate movement between GRN snapshot and AP posting date) | AP invoices carry their own `exchange_rate` and realized-FX columns (`tb_ap_invoice_reference.realized_fx_amount`); AP-module scope, not a GRN scenario. |
| FIN-HP-08 (period-close reconciliation and sign-off) | No period-close feature specific to this module was found. |
| FIN-PERM-01..07, FIN-VAL-01..09, FIN-EDGE-01..06 | Built on the old three-way-match design; not reconstructed. New GRN-side scenarios are listed below. |

## What to test instead

Extra-cost storage (`tb_extra_cost` / `tb_extra_cost_detail`, the three-mode `allocate_extra_cost_type` tag, the frontend's flat-amount-per-type entry UI offering `by_qty` / `by_value`) **and its allocation into landed cost at posting** are real and testable — see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) and [04-test-scenarios](./04-test-scenarios.md) Scenario 5 for the scenarios that exercise it as part of the Receiver's commit flow (observable on the Stock Movement tab and in `tb_inventory_transaction_cost_layer.extra_cost_amount`), and `501-grn.spec.ts`'s `GRN — Extra Costs` describe block (`TC-GRN-1000xx`) for the canonical E2E coverage. Note the mode semantics are the reverse of their names (`by_value` weights by quantity; `by_qty` splits evenly) — [02-business-rules.md](./02-business-rules.md) `GRN_CALC_010` / `GRN_CALC_011`.

### GRN-side scenarios of the AP link (added 2026-10-27)

API-level only — no UI creates AP invoices yet. None is covered by the E2E repo.

| ID | Scenario | Expected |
| --- | --- | --- |
| FIN-AP-01 | `PATCH …/good-received-notes/:id` on a `committed` GRN with no AP invoice, changing `invoice_no` | Accepted; the change is stored and `doc_version` increments. |
| FIN-AP-02 | Same `PATCH` changing a line or `grn_date` | `GRN_COMMITTED_HEADER_ONLY` (400) naming the rejected fields. |
| FIN-AP-03 | Create an AP invoice line sourced from that GRN's detail item, then repeat FIN-AP-01 | `GRN_AP_LINKED_NOT_EDITABLE` (400) with the AP document number; `GET …/good-received-notes/:id` lists it in `ap_invoices`; voiding the AP invoice (`void`) releases the lock. |
| FIN-AP-04 | AP line sourced from a `saved` GRN, or from a `committed` GRN with `post_type = cash` / `consignment` | `AP_GRN_NOT_COMMITTED` at submit/post. |
| FIN-AP-05 | Two AP documents each matching 60% of one GRN item's `received_qty` | The second is refused with `AP_GRN_OVER_MATCHED`. |
| FIN-AP-06 | `GET /api/ext/v1/ap-invoices` for the BU | Lists the committed GRN (not drafts/saved); a `post_type = consignment` GRN is absent. |

## References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — corrected cross-persona scenario table.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — the fuller correction and the searches run.
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — extra-cost entry as part of the Receiver's save flow.
- E2E spec: `../carmen-frontend-e2e/tests/501-grn.spec.ts` — `GRN — Extra Costs` (`TC-GRN-1000xx`) and `GRN — Financial Summary` (`TC-GRN-1300xx`) describe blocks are the closest real coverage; neither exercises invoice matching or AP posting.
