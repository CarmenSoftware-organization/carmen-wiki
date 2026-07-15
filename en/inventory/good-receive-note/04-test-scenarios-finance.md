---
title: Good Receive Note (GRN) — Test Scenarios — Finance
description: Why no three-way-match / AP-posting test scenarios exist for good-receive-note in current source, and what is confirmed instead.
published: true
date: 2026-07-15T00:00:00.000Z
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, finance, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — Test Scenarios — Finance

> **At a Glance**
> **Status:** Correction page — no dedicated Finance persona, three-way match, or AP-posting feature was confirmed for good-receive-note in current source.

> ⚠️ **Major correction this pass (2026-07-15).** The previous version of this page listed roughly 30 scenarios (FIN-HP-01 through FIN-EDGE-06) covering pre-AP extra-cost-allocation adjustment, a three-way match against a vendor invoice, AP-journal posting (`Dr GRN Clearing / Cr AP-Trade`), FX-adjustment postings, and period-close reconciliation. None of this maps to current source:

- A repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `journal`, `ledger`, `three-way`, `vendor_invoice`, `VendorInvoice`, and `tb_invoice` returned zero hits.
- The good-received-note backend module has exactly four lifecycle operations (`save`, `commit`, `reject`, `voidGrnById`) — none touch a journal, ledger, or AP entity.
- `enum_stage_role` has no `finance` member.
- The `501-grn.spec.ts` E2E spec has no describe block for invoice matching, AP posting, or period close; its "Financial Summary" group (`TC-GRN-1300xx`) only exercises a read-only totals tab on the GRN detail page, with no assertions tying it to a three-way match or a journal entry.

| Previously-claimed scenario group | Finding |
| --- | --- |
| FIN-HP-01..03 (pre-AP extra-cost allocation switch, `manual` / `by_value` / `by_qty` recompute with GL delta posting) | Extra-cost storage is real (`tb_extra_cost`, three-mode enum) but no allocation-splitting or GL-delta code was found — see [03-user-flow-finance.md](./03-user-flow-finance.md). |
| FIN-HP-04..06 (clean match, partial match, price-within-tolerance auto-pass) | No invoice-capture, AP-posting, or match-algorithm code found anywhere in current source. |
| FIN-HP-07 (FX adjustment on rate movement between GRN snapshot and AP posting date) | No AP-posting-date concept exists — there is no AP posting step at all. |
| FIN-HP-08 (period-close reconciliation and sign-off) | No period-close feature specific to this module was found. |
| FIN-PERM-01..07, FIN-VAL-01..09, FIN-EDGE-01..06 | All built on the same unconfirmed three-way-match / AP-posting foundation; not reconstructed. |

## What to test instead

Extra-cost storage (`tb_extra_cost` / `tb_extra_cost_detail`, the three-mode `allocate_extra_cost_type` tag, and the frontend's flat-amount-per-type entry UI) is real and testable — see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) for the scenarios that exercise it as part of the Receiver's save flow, and `501-grn.spec.ts`'s `GRN — Extra Costs` describe block (`TC-GRN-1000xx`) for the canonical E2E coverage.

## References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — corrected cross-persona scenario table.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — the fuller correction and the searches run.
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — extra-cost entry as part of the Receiver's save flow.
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — `GRN — Extra Costs` (`TC-GRN-1000xx`) and `GRN — Financial Summary` (`TC-GRN-1300xx`) describe blocks are the closest real coverage; neither exercises invoice matching or AP posting.
