---
title: Store Requisition — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for store-requisition.
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# Store Requisition — Test Scenarios

> **At a Glance**
> **Module:** [store-requisition](/en/inventory/store-requisition) &nbsp;·&nbsp; **Total scenarios:** cross-persona scenarios (corrected this pass, several removed as unconfirmed) + per-persona drill-downs &nbsp;·&nbsp; **Personas covered:** Requester, Approver, Fulfiller confirmed; "Receiver" and "Audit / Config" unconfirmed (correction stubs)
> **Run order:** primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `store-requisition` module. It groups SR coverage by the personas that interact with the document across its lifecycle, inventories the per-persona test files, captures the cross-persona handoff scenarios that stitch individual paths together, and maps every cross-persona scenario back to the canonical Playwright spec [`701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts). The scope is deliberately wider than a pure functional pass: each persona file includes **functional happy paths**, **RBAC / permission-denial cases** (driven by the `requestor@blueledgers.com` fixture), and **edge cases** (empty / invalid / large input, soft vs hard source-availability mode).

> ⚠️ **Corrected this pass.** Three claim classes that ran through every persona file were checked against `store-requisition.service.ts`, `store-requisition.logic.ts`, and the frontend and found unconfirmed: (1) **segregation of duties** — no `requestor_id` / `approved_by_id` cross-check exists anywhere in the SR service, so "Requester ≠ Approver" and "Approver ≠ Fulfiller" scenarios are not enforced controls; (2) **`cancelled` as a reachable status** — no service method ever assigns it; the only confirmed cancellation path is the whole-document `reject` action, which sets `voided`, available to whoever holds the current workflow stage (not an admin-only "void"); (3) **manual lot selection, multi-tier value-threshold escalation, approval delegation, SLA time-out escalation, a budget-module integration, GL/journal-entry posting, and a closed-period commit block** — none were found in current source (lot assignment is automatic FIFO; the rest returned zero hits for `threshold`, `delegat`, `journal`, `ledger`, `period`, or a budget route). Rows below are corrected in place; see [01-data-model.md](./01-data-model.md) §5 and [02-business-rules.md](./02-business-rules.md) for the full trail.

The cross-persona scenarios in Section 4 are the integration layer above the per-persona suites. They describe end-to-end journeys that cross a handoff boundary recorded in [03-user-flow.md](./03-user-flow.md) Section 4. Section 5 then maps the `701-sr.spec.ts` describe blocks to those journeys so that gaps in automated coverage are visible at a glance; note that `701-sr.spec.ts` is the **only** SR E2E file — there are no per-persona dedicated specs, so the per-persona test files in Section 3 describe scenarios that are partially covered by `701-sr.spec.ts` and partially documented as manual / planned tests.

## 2. Personas in Scope

- **Requester**: Outlet Manager who creates and submits SRs; entry / authoring side of the flow. Owns the `draft`-only soft-delete withdrawal path.
- **Approver**: whoever holds a workflow stage tagged `enum_stage_role.approve` (typically titled Department Head), who reviews, trims, rejects, or sends back lines on submitted SRs via the generic `/approve` and `/review` endpoints.
- **Fulfiller**: whoever holds the workflow stage tagged `enum_stage_role.issue` (typically titled Store Keeper), who records `issued_qty` through the same generic `/approve` endpoint the Approver uses. Lots are FIFO-assigned automatically.
- **"Receiver"** and **"Audit / Config" (Inventory Controller / Finance / Sysadmin / Auditor)**: **unconfirmed as distinct personas** — no matching route, `enum_stage_role` member, or feature (discrepancy flag, admin-void console, GL verification, RBAC/threshold config) was found in current source. Their test-scenario pages are correction stubs — see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) and [04-test-scenarios-audit-config.md](./04-test-scenarios-audit-config.md).

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
| 1 | Full happy path — `sr_type = issue` (kitchen pull) | Requester → Approver → Fulfiller | Source location is `tb_location.location_type = 'inventory'` with on-hand on every line; destination is `direct` (kitchen); workflow has one approve-tagged stage plus one issue-tagged stage. | SR `completed`; source on-hand decremented by `Σ issued_qty`; destination on-hand stays 0 (expensed immediately per `executeTransfer`'s direct-destination branch); lot data auto-assigned (FIFO) on linked `tb_inventory_transaction_detail`. GL/journal-entry posting is unconfirmed — see `SR_POST_007`. |
| 2 | Full happy path — `sr_type = transfer` (warehouse-to-warehouse) | Requester → Approver → Fulfiller | Source and destination are both `inventory` type; recipe-driven or manual creation. | SR `completed`; source on-hand decremented; destination on-hand incremented by the same quantity per line via `executeTransfer`; lot data auto-assigned at both ends. |
| 3 | Approver trim and partial fulfilment | Requester → Approver (trims one line) → Fulfiller | Requested quantity on one line exceeds source on-hand at approval time; approver trims `approved_qty` below `requested_qty` with `approved_message`. | SR `completed`; `requested_qty − issued_qty > 0` on the trimmed line (variance computable from the three stored quantity columns, not a persisted metric); approver's signature captured per line. |
| 4 | Send-back from approver, requester amends and resubmits | Requester → Approver (sends back via `/review`) → Requester (amends) → Approver (approves) → Fulfiller | Approver finds a line missing justification or with an anomalous quantity; sends the whole document back with `review_message` (cannot be mixed with an approve/reject decision on other lines in the same call). | SR walks `draft → in_progress → in_progress (requester stage) → in_progress (approver stage) → completed`; per-line `history` JSON shows the send-back / amend / re-approve sequence. |
| 5 | Whole-document reject — corrected this pass, was "all-lines rejected → automatic cancel" | Requester → Approver (marks every line reject, then invokes the whole-document `/reject`) | Approver decides the entire SR is not justified. | SR `doc_status = voided` (not `cancelled` — `cancelled` is never assigned by any current service method); per-line `reject_message` populated; no inventory impact; requester notified. Rejecting every line does not *automatically* void the document — the whole-document `/reject` is a distinct call the approver must invoke. |
| 6 | At-issue stock-out — fulfiller records partial | Requester → Approver → Fulfiller (short-issues) | Between approval and issue, other consumption reduces source on-hand below `approved_qty`; live `SR_VAL_013` check shows the shortfall. | SR `completed` with `issued_qty < approved_qty` on the affected line; the gap is computable from the stored columns; the specific system-comment wording described in earlier versions of this page was not directly confirmed. |
| 7 | ~~Receiver flags destination discrepancy post-commit~~ — corrected this pass | — | — | **Removed.** No receiver-facing screen, discrepancy comment-type, or escalation route was found in current source; see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md). Any user with read access to a `completed` SR can leave a generic comment — that is the only confirmed post-commit annotation surface. |
| 8 | Lot-controlled item — multi-lot consumption on a single line | Requester → Approver → Fulfiller (final stage advance) | Lot-controlled product; source has multiple active lots. | **Corrected this pass:** lot selection is not a Fulfiller action. `createFifoConsumption()` / `getAvailableFifoLots()` / `consumeFifoLots()` in `inventory-transaction.service.ts` assign lots automatically by FIFO at the final workflow-stage advance; multiple `tb_inventory_transaction_detail` rows may result under one `tb_inventory_transaction`, but no lot-selection UI exists in the SR frontend. |
| 9 | ~~Segregation-of-duties violation at commit~~ — corrected this pass | — | — | **Removed as a testable "reject" scenario.** No `requestor_id` / `approved_by_id` cross-check exists in `store-requisition.service.ts` or `store-requisition.logic.ts` — the same user can request, approve, and issue the same SR without any code-level block. Treat SoD as unenforced until a check is found. |
| 10 | ~~Closed-period commit block~~ — corrected this pass | — | — | **Removed.** A repo-wide search of `store-requisition.service.ts`, `store-requisition.logic.ts`, and the SR DTOs for `period` returned zero hits; there is no confirmed mechanism that blocks a final-stage advance because the accounting period is closed (`SR_VAL_014`). |
| 11 | ~~Administrative void on pre-commit SR~~ — corrected this pass | Whoever holds the current workflow stage | SR at `in_progress` (not restricted to `draft` or "early" `in_progress` — the reject method's only precondition is `doc_status = in_progress`). | SR moves to `voided` via the same whole-document `/reject` call any current-stage actor can invoke (`StoreRequisitionService.reject()`) — there is no separate "admin void" endpoint restricted to Inventory Controller / System Administrator. A `draft` SR cannot be rejected this way; its only pre-submit removal path is the requester's own soft-delete. |
| 12 | Recipe-driven auto-create flows through normal lifecycle | Recipe module (auto-create) → Requester (reviews) → Approver → Fulfiller | `[recipe](/en/inventory/recipe)` computes ingredient demand for a planned banquet event and posts an SR `draft` with `info.recipe_id` back-reference; requester opens, adjusts if needed, and submits. | SR walks the normal `draft → in_progress → completed` lifecycle; `info.recipe_id` preserved end-to-end. The recipe-trigger side of this scenario belongs to the recipe module's own resync pass, not re-verified here. |
| 13 | ~~Period-close reconciliation~~ — corrected this pass | — | — | **Removed.** This scenario depended on the closed-period gate (Scenario 10) and GL/journal-entry posting, neither of which was found in current source. |
| 14 | ~~Workflow / RBAC config change~~ — corrected this pass | — | — | **Narrowed.** `tb_workflow` is a real, tenant-configurable table shared with PR/PO/GRN — changing its stage definitions is a generic workflow-config action, not an SR-specific feature. No SR-specific value-threshold or SoD-relaxation-threshold field was found to configure. |

## 5. E2E Test Mapping

`701-sr.spec.ts` is the **only** Playwright E2E file for the SR module. It is structured as a single file with multiple `describe` blocks per functional area; auth is multi-role through `createAuthTest`, with `purchase@blueledgers.com` for the happy / functional path (Requester / Approver / Fulfiller equivalent in tests) and `requestor@blueledgers.com` for permission-denial cases. There are **no per-persona dedicated specs** — the per-persona test files linked in Section 3 catalogue scenarios; some are covered by `701-sr.spec.ts` describe blocks below, others remain documented / manual.

| `701-sr.spec.ts` describe block (TC group) | Cross-persona scenarios covered (Section 4) |
| ------------------------------------------- | ------------------------------------------- |
| `Store Requisition — Create` (TC-SR-010001–010005) | 1, 2 (entry point for the requester's create flow) |
| `Store Requisition — Create — Permission denial` (TC-SR-010002) | RBAC layer; requester not assigned to department blocked at create |
| `Store Requisition — Add Items` (TC-SR-020001–020003) | 1, 2, 3 (line entry; invalid quantity / insufficient stock soft / hard cases) |
| `Store Requisition — Real-time Inventory` (TC-SR-030001–030004) | 1, 6 (source availability check `SR_VAL_009` at submit + `SR_VAL_013` at the final stage) |
| `Store Requisition — Save & Auto-save` (TC-SR-040001–040005) | 1, 4 (draft persistence; resume after send-back) |
| `Store Requisition — Submit` (TC-SR-050001–050005) | 1, 2 (submit gates) |
| `Store Requisition — Approver list actions` (TC-SR-060001–060005) | 1, 3, 4 (approver queue navigation; bulk action) |
| `Store Requisition — Approve` (TC-SR-070001–070003) | 1 (full approval); test annotations describe a budget-exceeded warning that was not confirmed against current source — see [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) |
| `Store Requisition — Approve Item-level` (TC-SR-080001+) | 3, 4 (per-line approve / trim / reject); permission-denial via `requestor@blueledgers.com` |
| `Store Requisition — Adjust approved quantity` (TC-SR-090001+) | 3 (approver trim down from `requested_qty`) |
| `Store Requisition — Request Review` (TC-SR-100001+) | 4 (send-back for correction with `review_message`) |
| `Store Requisition — Reject` (TC-SR-110001+) | 5 (whole-document reject → `voided`; the test annotations' "Rejected" / "Partially Rejected" status wording is illustrative test-plan copy, not confirmed against the Prisma `enum_doc_status`) |
| `Store Requisition — Issuance` (TC-SR-120001+) | 1, 2, 6, 8 (final-stage advance; partial issuance; multi-lot consumption) |
| (no dedicated block) | Scenario 7 (Receiver) and Scenarios 9, 10, 11, 13, 14 (SoD / closed-period / admin-void / period-close / RBAC-config) were removed or narrowed this pass as unconfirmed against current source — see Section 4. |

Gaps relative to the corrected Section 4: Scenario 12 (recipe-driven auto-create, the recipe-side trigger specifically) is not covered by `701-sr.spec.ts` and remains manual / planned.

## 6. References

- [`../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/701-sr.spec.ts) — canonical Playwright E2E spec (multi-role auth, all TC-SR-0xxxxx groups).
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — cross-persona handoffs that drive the integration scenarios above.
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — posting rules invoked at the final workflow-stage advance and across approval handoffs.
- Per-persona detail: [Requester](./04-test-scenarios-requester.md), [Approver](./04-test-scenarios-approver.md), [Fulfiller](./04-test-scenarios-fulfiller.md), [Receiver](./04-test-scenarios-receiver.md), [Audit / Config](./04-test-scenarios-audit-config.md).
