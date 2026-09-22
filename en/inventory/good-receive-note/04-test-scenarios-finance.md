---
title: Good Receive Note (GRN) — Test Scenarios — Finance
description: Why no three-way-match / AP-posting test scenarios exist for good-receive-note in current source, and what is confirmed instead.
published: true
date: '2026-09-22T18:00:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, finance, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — Test Scenarios — Finance

> **At a Glance**
> **Status:** Correction page — no dedicated Finance persona, three-way match, or AP-posting feature was confirmed for good-receive-note in current source.

> ⚠️ **Major correction this pass (2026-07-15).** The previous version of this page listed roughly 30 scenarios (FIN-HP-01 through FIN-EDGE-06) covering pre-AP extra-cost-allocation adjustment, a three-way match against a vendor invoice, AP-journal posting (`Dr GRN Clearing / Cr AP-Trade`), FX-adjustment postings, and period-close reconciliation. None of this maps to current source:

- **Re-checked 2026-09-22:** still no vendor-invoice entity, AP-posting endpoint, or three-way match. A GL module now exists (`apps/micro-business/src/gl/`), but no GRN, inventory-transaction, or period-end code calls it — `GlPostingService.post()` (`gl-posting.service.ts:293`) posts only journal vouchers created manually, from templates, or by its own reversal / closing paths; `enum_gl_jv_source.ap` / `.inventory` have no writer. The frontend `routes/accounting` (AP invoice / payment, AR, JV) shows fabricated rows from `routes/accounting/accounting-documents.ts`.
- The good-received-note backend module has five lifecycle operations (`save`, `commit`, `approve`, `reject`, `voidGrnById`) — none touch a journal, ledger, or AP entity.
- `enum_stage_role` has no `finance` member.
- The `501-grn.spec.ts` E2E spec (76 cases) has no describe block for invoice matching, AP posting, or period close; its "Financial Summary" group (`TC-GRN-1300xx`) only exercises a read-only totals tab on the GRN detail page, with no assertions tying it to a three-way match or a journal entry.

> **Executable coverage:** `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` groups `GRN — Extra Costs` (`TC-GRN-1000xx`) and `GRN — Financial Summary` (`TC-GRN-1300xx`); gap report `docs/test-cases/gaps/501-grn-core-gap.md` (tax / discount section). No AP or GL spec exists.

| Previously-claimed scenario group | Finding |
| --- | --- |
| FIN-HP-01..03 (pre-AP extra-cost allocation switch, `manual` / `by_value` / `by_qty` recompute with GL delta posting) | Extra-cost **allocation is now real** (2026-09-10): `allocateExtraCost()` splits the total at posting — `by_qty` equal shares, `by_value` weighted by stock quantity, `manual` nothing — into landed cost and `tb_inventory_transaction_cost_layer.extra_cost_amount`. There is still no GL delta, no re-allocation after posting (a committed GRN is never re-posted), and no per-line manual entry. Test it from the Receiver side: [04-test-scenarios](./04-test-scenarios.md) Scenario 5, [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) RCV-EDGE-02. |
| FIN-HP-04..06 (clean match, partial match, price-within-tolerance auto-pass) | No invoice-capture, AP-posting, or match-algorithm code found anywhere in current source. |
| FIN-HP-07 (FX adjustment on rate movement between GRN snapshot and AP posting date) | No AP-posting-date concept exists — there is no AP posting step at all. |
| FIN-HP-08 (period-close reconciliation and sign-off) | No period-close feature specific to this module was found. |
| FIN-PERM-01..07, FIN-VAL-01..09, FIN-EDGE-01..06 | All built on the same unconfirmed three-way-match / AP-posting foundation; not reconstructed. |

## What to test instead

Extra-cost storage (`tb_extra_cost` / `tb_extra_cost_detail`, the three-mode `allocate_extra_cost_type` tag, the frontend's flat-amount-per-type entry UI offering `by_qty` / `by_value`) **and its allocation into landed cost at posting** are real and testable — see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) and [04-test-scenarios](./04-test-scenarios.md) Scenario 5 for the scenarios that exercise it as part of the Receiver's commit flow (observable on the Stock Movement tab and in `tb_inventory_transaction_cost_layer.extra_cost_amount`), and `501-grn.spec.ts`'s `GRN — Extra Costs` describe block (`TC-GRN-1000xx`) for the canonical E2E coverage. Note the mode semantics are the reverse of their names (`by_value` weights by quantity; `by_qty` splits evenly) — [02-business-rules.md](./02-business-rules.md) `GRN_CALC_010` / `GRN_CALC_011`.

## References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — corrected cross-persona scenario table.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — the fuller correction and the searches run.
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — extra-cost entry as part of the Receiver's save flow.
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — `GRN — Extra Costs` (`TC-GRN-1000xx`) and `GRN — Financial Summary` (`TC-GRN-1300xx`) describe blocks are the closest real coverage; neither exercises invoice matching or AP posting.
