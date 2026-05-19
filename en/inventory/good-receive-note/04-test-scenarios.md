---
title: Good Receive Note (GRN) — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for good-receive-note.
published: true
date: 2026-05-17T11:00:00.000Z
tags: good-receive-note, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# Good Receive Note (GRN) — Test Scenarios

> **At a Glance**
> **Module:** [[good-receive-note]] &nbsp;·&nbsp; **Total scenarios:** ~10 cross-persona + ~110 per-persona &nbsp;·&nbsp; **Personas covered:** Receiver, Purchaser, Finance, Audit / Config
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `good-receive-note` module. It groups GRN coverage by the four personas that interact with the document across its lifecycle (Receiver, Purchaser, Finance, Audit / Config), inventories the per-persona test files, captures the cross-persona handoff scenarios that stitch individual paths together, and maps every cross-persona scenario back to the canonical Playwright spec [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts). The scope is deliberately wider than a pure functional pass: each persona file includes **functional happy paths**, **RBAC / permission-denial cases** (driven by the `requestor@blueledgers.com` fixture), **edge cases** (empty / invalid / large input), **three-way-match outcomes** (PO ↔ GRN ↔ invoice alignment, partial receipt, price / qty discrepancy), and **lot-tracking traces** (commit-time lot data presence and post-commit recall queries via `tb_inventory_transaction_detail`).

The cross-persona scenarios in Section 4 are the integration layer above the per-persona suites. They describe end-to-end journeys that cross a handoff boundary recorded in [03-user-flow.md](./03-user-flow.md) Section 4 — for example, *Receiver saves → Inventory Manager commits → Finance matches invoice*. Section 5 then maps the `501-grn.spec.ts` describe blocks to those journeys so that gaps in automated coverage are visible at a glance; note that `501-grn.spec.ts` is the **only** GRN E2E file — there are no per-persona dedicated specs, so the per-persona test files in Section 3 describe scenarios that are partially covered by `501-grn.spec.ts` and partially documented as manual / planned tests.

## 2. Personas in Scope

- **Receiver**: Receiving / warehouse staff who physically take delivery, raise the GRN in `draft`, populate header and lines (against PO or manual), and save for review.
- **Purchaser**: Procurement staff who own the upstream PO and absorb variance / quality / three-way-mismatch handoffs back from Receiver and Finance.
- **Finance**: AP staff who consume `committed` GRNs, run the three-way match against the vendor invoice, and co-authorise post-commit reversals.
- **Audit / Config**: System Administrator and auditors who own RBAC, lot-format / posting / extra-cost config, scheduled sweeps, and read-only audit traces across inventory transactions.

## 3. Persona Test Files

- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

The table below is the integration layer. Each row spans at least one handoff from [03-user-flow.md](./03-user-flow.md) Section 4 and ends with the document in a terminal or steady state. "Personas in order" lists the actors in execution sequence; "Pre-condition" captures the system state required to begin; "Expected end state" anchors the GRN `doc_status` and downstream effects (inventory, PO, AP).

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Full happy path against PO | Receiver → Inventory Manager → Finance | Source PO with `po_status ∈ {sent, partial}` and at least one line pending; vendor / currency / exchange rate available; receiver has create-GRN permission. | GRN `committed`; inventory incremented; FIFO / avg-cost layer written; PO line `received_qty` advanced (PO → `partial` or `completed`); AP accrual raised; vendor invoice three-way matched and posted by Finance. |
| 2 | Manual GRN (no PO) | Receiver → Inventory Manager → Finance | `doc_type = manual` permitted by tenant config; vendor active; no upstream PO. | GRN `committed` with `doc_type = manual` and no `purchase_order_detail_id` on any line; inventory incremented; AP accrual raised; Finance matches against vendor invoice without PO leg. |
| 3 | Partial receipt across two GRNs | Receiver → Inventory Manager → Receiver → Inventory Manager → Finance | Source PO line has pending qty larger than the first delivery; tenant permits partial receipt. | First GRN `committed` and PO line → `partial` with `received_qty` < `ordered_qty`; second GRN later `committed` and PO line → `completed`; Finance matches one or both invoices depending on vendor billing. |
| 4 | Quality issue at receiving | Receiver → Inventory Manager → Purchaser | Delivery contains damaged / short-qty goods; receiver records `accepted_qty < received_qty` with variance comment on the line. | GRN `committed` with quality flag on affected lines; Purchaser receives variance handoff for vendor coordination (credit note or replacement PO); inventory reflects accepted qty only. |
| 5 | Three-way mismatch on invoice | Receiver → Inventory Manager → Finance → Purchaser | GRN `committed` cleanly; vendor invoice arrives with price or qty deviating beyond tolerance from the PO / GRN. | GRN remains `committed` unchanged; Finance flags invoice discrepancy and bounces back to Purchaser; resolution path is credit note against GRN or post-commit reversal (Scenario 9). |
| 6 | Extra-cost allocation review | Receiver → Finance → Inventory Manager | Receiver records freight / duty / clearance in `tb_good_received_note_extra_cost` with allocation mode `manual`, `by_value`, or `by_qty`; GRN still in `saved`. | Finance reviews / adjusts allocation pre-AP; Inventory Manager commits with reconciled extra-cost lines; AP accrual raised includes extra-cost portion; cost layers carry landed cost. |
| 7 | Batch commit at end of shift | Receiver (×N) → Inventory Manager | N GRNs sit in `saved` from the shift; each independently passes line-level rules. | Inventory Manager fires batch commit; each GRN evaluated against commit-time rules; partial-batch failure rolls back only the failing GRN(s); successful GRNs → `committed` in one transaction window. |
| 8 | Lot recall trace | System Administrator → Auditor | At least one `committed` GRN has lot data written on `tb_inventory_transaction_detail` via `tb_good_received_note_detail_item.inventory_transaction_id`. | Sysadmin queries by lot number; Auditor traces from inventory transactions back to the GRN detail_item and forward to downstream issues / stock counts; no document state change. |
| 9 | Post-commit void (elevated co-auth) | Inventory Manager + Finance → Receiver | GRN `committed`; reversal request raised with reason text; elevated co-authorisation available. | GRN → `voided` with compensating reversal of inventory transaction, cost-layer reversal, PO line `received_qty` decrement, and reversing AP entry; Receiver may raise a replacement GRN if the physical receipt is re-recorded. |
| 10 | Scheduled auto-commit sweep | System Administrator → Finance, Inventory Manager | Stale `saved` GRNs older than the tenant grace window exist; sweep job scheduled. | Eligible GRNs → `committed` by the sweep using the same commit-time rule set; failed GRNs logged and routed to Inventory Manager for manual resolution; Finance picks up newly committed GRNs for matching. |

## 5. E2E Test Mapping

`501-grn.spec.ts` is the **only** Playwright E2E file for the GRN module. It is structured as a single file with multiple `describe` blocks per functional area; auth is multi-role through `createAuthTest`, with `purchase@blueledgers.com` for the happy / functional path (Receiver + Purchaser equivalent) and `requestor@blueledgers.com` for permission-denial cases. There are **no per-persona dedicated specs** — the per-persona test files linked in Section 3 catalogue scenarios; some are covered by `501-grn.spec.ts` describe blocks below, others remain documented / manual.

| `501-grn.spec.ts` describe block (TC group) | Cross-persona scenarios covered (Section 4) |
| ------------------------------------------- | ------------------------------------------- |
| `GRN — List` (TC-GRN-900001 / 010001–010004) | 1, 8 (entry point for listing committed GRNs by lot / status) |
| `GRN — Filter / Search` (TC-GRN-900002 / 020001–020005) | 8 (lot / vendor / invoice number recall queries) |
| `GRN — Create from Single PO` (TC-GRN-900003 / 030001–030005) | 1, 3 (first leg of the happy path and partial receipt) |
| `GRN — Create from Multiple POs` (TC-GRN-900004 / 040002–040004) | 1, 3 (multi-PO consolidation into one GRN) |
| `GRN — Manual creation` (TC-GRN-900005 / 050001–050005) | 2 (manual GRN end-to-end entry point) |
| `GRN — Edit Header` (TC-GRN-900006 / 060001–060005) | 1, 2 (header edits before save-for-review) |
| `GRN — Add Line Item` (TC-GRN-900007 / 070001–070004) | 1, 2, 3 (line entry across PO and manual paths) |
| `GRN — Edit Line Item` (TC-GRN-900008 / 080001–080005) | 4 (quality issue: editing `accepted_qty` < `received_qty`) |
| `GRN — Delete Line Item` (TC-GRN-900009 / 090001+) | 1, 3 (line cleanup before commit) |
| `GRN — Extra Costs` (TC-GRN-900010 / 1059+) | 6 (extra-cost allocation review) |
| `GRN — Commit` (TC-GRN-900011 / 1150+) | 1, 2, 3, 4, 6, 7 (the canonical posting event) |
| `GRN — Void` (TC-GRN-900012 / 1263+) | 9 (pre-commit void; post-commit reversal partially covered) |
| `GRN — Financial Summary` (TC-GRN-900013 / 1372+) | 5, 6 (three-way-match inputs and landed cost) |
| `GRN — Stock Movements` (TC-GRN-900014 / 1476+) | 1, 8 (inventory transactions written at commit; lot trace) |
| `GRN — Comments` (TC-GRN-900015 / 1554+) | 4, 5 (variance comments at handoff to Purchaser) |
| `GRN — Attachments` (TC-GRN-900016 / 1692+) | 5 (invoice / packing-list evidence for three-way match) |
| `GRN — Activity Log` (TC-GRN-900017 / 1821+) | 8, 9 (audit trail across commit / void / reversal) |
| `GRN — Bulk Approval` (TC-GRN-900018 / 1925+) | 7 (batch commit at end of shift) |
| `GRN — * — Permission denial` (all `requestor@blueledgers.com` blocks) | RBAC layer across every scenario; the four persona files in Section 3 catalogue the persona-specific denial paths. |

Gaps relative to Section 4: Scenario 5 (three-way mismatch end-to-end) and Scenario 10 (scheduled auto-commit sweep) are not yet covered by `501-grn.spec.ts` and live as manual / planned cases in the persona files.

## 6. References

- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — canonical Playwright E2E spec (multi-role auth, all TC-GRN-9xxxxx groups).
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — cross-persona handoffs that drive the integration scenarios above.
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — posting rules and three-way-match rules invoked at the `saved → committed` transition.
- Per-persona detail: [Receiver](./04-test-scenarios-receiver.md), [Purchaser](./04-test-scenarios-purchaser.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md).
