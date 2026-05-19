---
title: Store Requisition — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for store-requisition.
published: true
date: 2026-05-19T23:55:00.000Z
tags: store-requisition, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# Store Requisition — Test Scenarios

> **At a Glance**
> **Module:** [store-requisition](/en/inventory/store-requisition) &nbsp;·&nbsp; **Total scenarios:** ~14 cross-persona + per-persona drill-downs across all personas &nbsp;·&nbsp; **Personas covered:** Requester, Approver, Fulfiller, Receiver, Audit / Config
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `store-requisition` module. It groups SR coverage by the five personas that interact with the document across its lifecycle (Requester, Approver, Fulfiller, Receiver, Audit / Config), inventories the per-persona test files, captures the cross-persona handoff scenarios that stitch individual paths together, and maps every cross-persona scenario back to the canonical Playwright spec [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts). The scope is deliberately wider than a pure functional pass: each persona file includes **functional happy paths**, **RBAC / permission-denial cases** (driven by the `requestor@blueledgers.com` fixture), **edge cases** (empty / invalid / large input, soft vs hard source-availability mode), **segregation-of-duties tests** (Requester ≠ Approver per `SR_AUTH_011`, Approver ≠ Fulfiller per `SR_AUTH_012`), and **lot-tracking traces** (lot data persists on the linked `tb_inventory_transaction_detail`, not on the SR line).

The cross-persona scenarios in Section 4 are the integration layer above the per-persona suites. They describe end-to-end journeys that cross a handoff boundary recorded in [03-user-flow.md](./03-user-flow.md) Section 4 — for example, *Requester submits → Approver trims → Fulfiller commits partial → Receiver flags*. Section 5 then maps the `701-sr.spec.ts` describe blocks to those journeys so that gaps in automated coverage are visible at a glance; note that `701-sr.spec.ts` is the **only** SR E2E file — there are no per-persona dedicated specs, so the per-persona test files in Section 3 describe scenarios that are partially covered by `701-sr.spec.ts` and partially documented as manual / planned tests.

## 2. Personas in Scope

- **Requester**: Outlet Manager who creates and submits SRs; entry / authoring side of the flow.
- **Approver**: Department Head (and any higher-tier approver) who reviews, trims, rejects, or sends back lines on submitted SRs.
- **Fulfiller**: Store Keeper at the source location who picks goods, records `issued_qty`, selects lots, and commits the SR.
- **Receiver**: Destination outlet representative who acknowledges physical receipt and flags discrepancies; does NOT change `doc_status`.
- **Audit / Config**: Inventory Controller (variance, admin void), Finance (closed-period block, journal-entry verification, period close), Sysadmin (workflow / RBAC config), Auditor (read-only trace).

## 3. Persona Test Files

- [Requester scenarios](./04-test-scenarios-requester.md)
- [Approver scenarios](./04-test-scenarios-approver.md)
- [Fulfiller scenarios](./04-test-scenarios-fulfiller.md)
- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

The table below is the integration layer. Each row spans at least one handoff from [03-user-flow.md](./03-user-flow.md) Section 4 and ends with the document in a terminal or steady state. "Personas in order" lists the actors in execution sequence; "Pre-condition" captures the system state required to begin; "Expected end state" anchors the SR `doc_status` and downstream effects (inventory, GL).

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Full happy path — `sr_type = issue` (kitchen pull) | Requester → Approver → Fulfiller → Receiver | Source location is `tb_location.location_type = 'inventory'` with on-hand on every line; destination is `direct` (kitchen); requester / approver / fulfiller are distinct users (SoD satisfied); workflow has one approval stage; tenant in hard or soft `SR_VAL_009` mode. | SR `completed`; source on-hand decremented by `Σ issued_qty`; destination cost-centre debited via the journal entry per `SR_POST_007`; lot data persisted on linked `tb_inventory_transaction_detail`; Receiver acknowledged full receipt. |
| 2 | Full happy path — `sr_type = transfer` (warehouse-to-warehouse) | Requester → Approver → Fulfiller → Receiver | Source and destination are both `inventory` type; recipe-driven or manual creation; tenant config supports `transfer` without paired GRN. | SR `completed`; source on-hand decremented; destination on-hand incremented by the same quantity per line; paired stock-OUT / stock-IN rows on `tb_inventory_transaction`; lot data preserved at both ends; Receiver acknowledged. |
| 3 | Approver trim and partial fulfilment | Requester → Approver (trims one line) → Fulfiller (commits) → Receiver | Requested quantity on one line exceeds source on-hand at approval time; approver trims `approved_qty` below `requested_qty` with `approved_message`. | SR `completed`; `requested_qty − issued_qty > 0` on the trimmed line (variance recorded); approver's signature captured per line; Receiver acknowledges the trimmed quantity as full receipt of what was actually approved. |
| 4 | Send-back from approver, requester amends and resubmits | Requester → Approver (sends back) → Requester (amends) → Approver (approves) → Fulfiller → Receiver | Approver finds a line missing justification or with an anomalous quantity; sends back with `review_message`. | SR walks `draft → in_progress → in_progress (requester stage) → in_progress (approver stage) → completed`; per-line `history` JSON shows the send-back / amend / re-approve sequence; the requester ultimately commits a corrected SR through to receipt. |
| 5 | All-lines rejected at approval — automatic cancel | Requester → Approver (rejects every line) | Approver decides the entire SR is not justified (e.g. duplicate of an active SR, budget overrun, vendor-side cancellation). | SR `cancelled` automatically via `SR_POST_004` tail → `SR_POST_009`; per-line `reject_message` populated; no inventory or GL impact; requester is notified per line; may raise a revised SR. |
| 6 | At-issue stock-out — fulfiller commits partial | Requester → Approver → Fulfiller (short-fulfils) → Receiver + Inventory Controller | Between approval and issue, another SR (or other consumption) reduces source on-hand below `approved_qty`; live `SR_VAL_013` check shows the shortfall. | SR `completed` with `issued_qty < approved_qty` on the affected line; `fulfilment_gap` recorded; per-line system comment "issued X of Y; Z short due to concurrent consumption"; variance event raised; Inventory Controller alerted in parallel. |
| 7 | Receiver flags destination discrepancy post-commit | Requester → Approver → Fulfiller → Receiver (flags) → Inventory Controller (resolves via adjustment) | SR `completed`; goods arrive at destination short of `issued_qty` or with wrong lot; Receiver writes discrepancy comment with evidence. | SR remains `completed` (no state change per `SR_POST_013`); Inventory Controller posts an `[inventory-adjustment](/en/inventory/inventory-adjustment)` carrying back-reference `sr_id`; destination on-hand reconciles to physical; SR comment thread shows the discrepancy resolution. |
| 8 | Lot-controlled item — multi-lot pick on a single line | Requester → Approver → Fulfiller (selects lots) → Receiver | Lot-controlled product; source has multiple active lots; rotation policy is FIFO by expiry. | Fulfiller selects lots summing to `issued_qty`; lot selection writes multiple `tb_inventory_transaction_detail` rows under one `tb_inventory_transaction` for the line; cost-layer consumption picks each lot's `cost_per_unit`; Receiver verifies lot labels on physical goods match the linked transaction. |
| 9 | Segregation-of-duties violation at commit | Requester → Approver (= Fulfiller, single user) → commit attempt | SoD relaxation NOT enabled; tenant requires `Approver ≠ Fulfiller`; same user holds both rights and attempts to commit a self-approved SR. | Commit rejected per `SR_AUTH_012` with error message; SR remains `in_progress`; a different fulfiller (deputy or escalation) must take over to complete the flow. |
| 10 | Closed-period commit block | Requester → Approver → Fulfiller (commit attempt) → Finance (period reopen or reject) | Fulfiller tries to commit with `last_action_at_date` mapping to a closed accounting period; `SR_VAL_014` blocks. | Commit rejected; SR remains `in_progress`; Finance either reopens the period (rare; CFO sign-off) or asks the Fulfiller to advance the posting date to a current period; if not reconcilable, Inventory Controller administratively voids and a fresh SR is raised. |
| 11 | Administrative void on pre-commit SR | Requester → Inventory Controller (admin voids) | Audit hold raised on the requester, duplicate SR detected, or supplier-side cancellation invalidates the request; SR is at `draft` or early `in_progress`. | SR moves to `voided` per `SR_POST_010`; reason text recorded; no inventory or GL impact; requester notified; document terminates. |
| 12 | Recipe-driven auto-create flows through normal lifecycle | Recipe module (auto-create) → Requester (reviews) → Approver → Fulfiller → Receiver | `[recipe](/en/inventory/recipe)` computes ingredient demand for a planned banquet event and posts an SR `draft` with `info.recipe_id` back-reference; requester opens, adjusts if needed, and submits. | SR walks the normal `draft → in_progress → completed` lifecycle; `info.recipe_id` preserved end-to-end; variance vs the recipe's computed demand surfaces in the variance dashboard at period close. |
| 13 | Period-close reconciliation | Finance | All `completed` SRs in the period; outlet food-cost reports computed. | Finance reconciles outlet food-cost against `Σ (issued_qty × cost_per_unit)` per outlet from the SR-driven inventory transactions; gaps investigated; period locked. SR module sees no state change; subsequent SRs with posting dates in the closed period are blocked by `SR_VAL_014`. |
| 14 | Workflow / RBAC config change | Sysadmin → all personas | Tenant decides to add a second approval tier above ฿10,000 or to relax the SoD threshold for low-value SRs. | Sysadmin commits the `tb_workflow` change; new rules apply prospectively to subsequent SRs; existing in-flight SRs are re-routed per the Sysadmin / Inventory Controller coordination; no SR state changes from the config itself. |

## 5. E2E Test Mapping

`701-sr.spec.ts` is the **only** Playwright E2E file for the SR module. It is structured as a single file with multiple `describe` blocks per functional area; auth is multi-role through `createAuthTest`, with `purchase@blueledgers.com` for the happy / functional path (Requester / Approver / Fulfiller equivalent in tests) and `requestor@blueledgers.com` for permission-denial cases. There are **no per-persona dedicated specs** — the per-persona test files linked in Section 3 catalogue scenarios; some are covered by `701-sr.spec.ts` describe blocks below, others remain documented / manual.

| `701-sr.spec.ts` describe block (TC group) | Cross-persona scenarios covered (Section 4) |
| ------------------------------------------- | ------------------------------------------- |
| `Store Requisition — Create` (TC-SR-900001 / 010001–010005) | 1, 2, 11 (entry point for the requester's create flow; permission-denial case `requestor@blueledgers.com`) |
| `Store Requisition — Create — Permission denial` (TC-SR-010002) | RBAC layer; requester not assigned to department blocked at create |
| `Store Requisition — Add Items` (TC-SR-900002 / 020001–020003) | 1, 2, 3 (line entry; invalid quantity / insufficient stock soft / hard cases) |
| `Store Requisition — Real-time Inventory` (TC-SR-900003 / 030001–030004) | 1, 6 (source availability check `SR_VAL_009` at submit + `SR_VAL_013` at commit) |
| `Store Requisition — Save & Auto-save` (TC-SR-900004 / 040001–040005) | 1, 4 (draft persistence; resume after send-back) |
| `Store Requisition — Submit` (TC-SR-900005 / 050001–050005) | 1, 2, 11 (submit gates; permission-denial; emergency flag) |
| `Store Requisition — Approver list actions` (TC-SR-900006 / 060001–060005) | 1, 3, 4, 5 (approver queue navigation; bulk action; delegation) |
| `Store Requisition — Approve` (TC-SR-900007 / 070001–070003) | 1 (full approval); 9 (unauthorized approver — SoD-adjacent); budget-exceeded warning |
| `Store Requisition — Approve Item-level` (TC-SR-900008 / 080001+) | 3, 5 (per-line approve / trim / reject); permission-denial via `requestor@blueledgers.com` |
| `Store Requisition — Adjust approved quantity` (TC-SR-900009 / 090001+) | 3 (approver trim down from `requested_qty`) |
| `Store Requisition — Request Review` (TC-SR-900010 / 100001+) | 4 (send-back for correction with `review_message`) |
| `Store Requisition — Reject` (TC-SR-900011 / 110001+) | 5 (all-lines-rejected → cancelled) |
| `Store Requisition — Issuance` (TC-SR-900012 / 120001+) | 1, 2, 6, 8 (fulfiller commit; partial fulfilment; multi-lot pick) |
| (no dedicated block for Receiver acknowledgement) | Scenario 7 (Receiver discrepancy) is currently documented as manual / planned |
| (no dedicated block for period close or admin void) | Scenarios 10, 11, 13, 14 (Audit / Config flows) are documented as manual / planned |

Gaps relative to Section 4: Scenarios 7 (Receiver discrepancy end-to-end), 10 (closed-period commit block resolution), 11 (administrative void with the full event chain), 12 (recipe-driven auto-create), 13 (period-close reconciliation), and 14 (workflow / RBAC config change) are not yet covered by `701-sr.spec.ts` and live as manual / planned cases in the persona files (primarily under [04-test-scenarios-audit-config.md](./04-test-scenarios-audit-config.md) and [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)).

## 6. References

- [`../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — canonical Playwright E2E spec (multi-role auth, all TC-SR-9xxxxx groups).
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — cross-persona handoffs that drive the integration scenarios above.
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — posting rules and SoD rules invoked at the `in_progress → completed` transition and across approval handoffs.
- Per-persona detail: [Requester](./04-test-scenarios-requester.md), [Approver](./04-test-scenarios-approver.md), [Fulfiller](./04-test-scenarios-fulfiller.md), [Receiver](./04-test-scenarios-receiver.md), [Audit / Config](./04-test-scenarios-audit-config.md).
