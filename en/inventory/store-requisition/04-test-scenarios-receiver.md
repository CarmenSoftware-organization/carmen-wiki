---
title: Store Requisition — Test Scenarios — Receiver
description: Receiver's test cases — unconfirmed persona; documents why the prior scenario set does not match current source.
published: true
date: 2026-07-15T12:00:00.000Z
tags: store-requisition, test-scenarios, receiver, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:30:00.000Z
---

# Store Requisition — Test Scenarios — Receiver

> **At a Glance**
> **Persona:** Receiver — **unconfirmed as a distinct persona in current source** &nbsp;·&nbsp; **Module:** [store-requisition](/en/inventory/store-requisition)
> ⚠️ **Major correction this pass.** This page previously listed ~20 test scenarios (happy path, permission, validation, edge case) for a destination-outlet "Receiver" who acknowledges physical receipt, flags discrepancies, and escalates to an Inventory Controller. [03-user-flow-receiver.md](./03-user-flow-receiver.md) documents the full source-check trail: a repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `receiver` / `discrepancy` returned zero hits inside the `store-requisition` module, `enum_stage_role` has no `receiver` member, and there is no receiver-facing route or component. There is therefore nothing to write test scenarios against.

## 1. What Replaces These Scenarios

The only confirmed post-commit interaction available today is: any user with read access to a `completed` SR can append a generic `user`-type comment via `tb_store_requisition_comment` / `tb_store_requisition_detail_comment` (the same comment endpoints every persona uses — not receiver-exclusive, no `discrepancy` sub-type). A minimal, honest test scenario against *that* real surface would be:

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| RCV-HP-01 | Any user appends a free-text comment on a `completed` SR | SR is `doc_status = completed`; user has read access. | 1. Open the SR. 2. Add a comment via the comment panel. 3. Save. | Comment persists via the generic comment endpoint; `doc_status` is unaffected; no discrepancy-specific field, escalation, or notification exists to assert against. |

If a formal receipt-acknowledgement or discrepancy-flagging feature becomes a real product requirement, the scenarios previously on this page (short receipt, over receipt, wrong lot, damaged goods, late arrival, missing-on-arrival) are a reasonable starting *design* for that future feature's test plan — but they must not be represented as tests of current behavior.

## 2. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — Scenario 7 in the cross-persona table was removed this pass for the same reason.
- User flow: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — the full "what is and isn't confirmed" trail this page summarizes.
- Sibling: [04-test-scenarios-fulfiller.md](./04-test-scenarios-fulfiller.md) — the final workflow-stage advance is the last confirmed action on the document; nothing downstream of it was found in code.
- Business rules: [02-business-rules.md](./02-business-rules.md) § 4 (`SR_AUTH_008`, marked unconfirmed), § 5 (`SR_POST_013`, marked unconfirmed).
