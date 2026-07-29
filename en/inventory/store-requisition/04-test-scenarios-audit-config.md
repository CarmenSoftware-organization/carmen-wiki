---
title: Store Requisition — Test Scenarios — Audit & Config
description: Inventory Controller, Finance, Sysadmin, and Auditor test cases — largely unconfirmed persona; documents why the prior scenario set does not match current source.
published: true
date: 2026-07-29T05:45:00.000Z
tags: store-requisition, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# Store Requisition — Test Scenarios — Audit & Config

> **At a Glance**
> **Persona:** Inventory Controller + Finance + Sysadmin + Auditor — **largely unconfirmed as distinct SR-module personas in current source** &nbsp;·&nbsp; **Module:** [store-requisition](/en/inventory/store-requisition)
> ⚠️ **Major correction this pass.** This page previously listed ~27 test scenarios for an admin-void console, a Finance closed-period gate with journal-entry verification, a Sysadmin RBAC/workflow/SoD-threshold configuration console, and an Auditor signature-trace tool. [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) documents the full source-check trail: no admin-void method exists separate from the ordinary whole-document `reject` (which any current-stage actor can invoke); no `journal`/`ledger` code exists anywhere in this module; no `period` check exists in `store-requisition.service.ts` or `store-requisition.logic.ts`; and no `delegat` hits exist anywhere in this module or the workflow orchestrator. There is therefore nothing distinct to write test scenarios against for these four sub-roles. **One exception, corrected this pass:** the generic amount-based workflow `routing_rules` (which an earlier version of this correction wrongly folded into the "zero hits" finding — that search covered only the literal word `threshold`) is real and does affect SR stage routing (`SR_XMOD_008`), but it is system-config functionality shared with PR/PO, not a dedicated Sysadmin console for SR specifically — so it still doesn't give this module's Audit/Config persona anything distinct to test.

## 1. What Replaces These Scenarios

The closest existing analogues to what this page previously tested:

| Prior scenario class | What is actually confirmed |
|---|---|
| Admin void on pre-commit SR | The ordinary whole-document `reject` action (`StoreRequisitionService.reject()`), available to whoever holds the current workflow stage — see [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) APR-EDGE-02 and [04-test-scenarios-fulfiller.md](./04-test-scenarios-fulfiller.md). Not a separate "admin" path. |
| Finance closed-period block, journal-entry verification, period close | **Not implemented.** No test scenario can be written against a feature with zero code hits. |
| Sysadmin RBAC / workflow / SoD-relaxation-threshold console | `tb_workflow` is a real, tenant-configurable table shared with PR/PO/GRN — testing a stage-count, stage-role, or amount/department/category routing-rule change there is a generic workflow-config test (the routing-rule part is confirmed real, `SR_XMOD_008`), not SR-specific. No SoD-relaxation field exists to test. |
| Auditor read-only signature trace | `workflow_history` and per-line `history` JSON are readable by anyone with SR read access — there is no Auditor-exclusive route to test. |

A minimal, honest test scenario against the real surface:

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| AC-HP-01 | Whoever holds the current workflow stage rejects the whole document | SR at `doc_status = in_progress`. | 1. Open the SR. 2. Invoke the whole-document reject. 3. Confirm. | `doc_status = voided` (not `cancelled`); available to any user in `user_action.execute` for the current stage, not restricted to an "Inventory Controller" or "Sysadmin" role. See `04-test-scenarios-approver.md` APR-EDGE-02. |

## 2. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — Scenarios 9, 10, 11, 13, 14 were removed or narrowed this pass for the same reasons.
- User flow: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — the full "what is and isn't confirmed" trail this page summarizes.
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — the discrepancy-escalation target this page's prior version described; itself unconfirmed.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 2 (`SR_VAL_014`, unconfirmed), § 4 (`SR_AUTH_009`–`SR_AUTH_013`, corrected), § 5 (`SR_POST_007`, `SR_POST_009`, `SR_POST_010`, `SR_POST_013`, corrected).
