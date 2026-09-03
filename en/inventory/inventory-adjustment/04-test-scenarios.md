---
title: Inventory Adjustment — Test Scenarios
description: Test cases for the actual (always-completed) inventory-adjustment lifecycle, plus E2E coverage gaps.
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Test Scenarios

> **At a Glance**
> **Module:** [inventory-adjustment](/en/inventory/inventory-adjustment) &nbsp;·&nbsp; **Personas covered:** Store Keeper, Inventory Controller (same undifferentiated screen); Finance and Audit/Config have no matching surface — see their pages
> **Headline fact that shapes every scenario below:** creation always posts immediately — there is no pending/approval state to test, and Edit/Void are unreachable through the UI for any persisted document
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

An earlier version of this page organized ~150 scenarios around a threshold-gated, multi-role approval chain that does not exist in the current implementation (see [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules) § 1 and § 4). This rewrite keeps the same shape — happy path, permission, validation, edge case — but scopes every scenario to what `create()`, `update()`, `delete()`, `voidStockIn()`/`voidStockOut()`, and the Zod schema actually do. There is no dedicated `inventory-adjustment.spec.ts` E2E file; the only spec touching this module's own surface is `031-adjustment-type.spec.ts`, which covers the reason-code master, not the Stock-In/Stock-Out screens themselves.

## 2. Personas in Scope

- **Store Keeper**: enters Stock-In/Stock-Out documents; every document they create posts immediately regardless of which button they click.
- **Inventory Controller**: uses the identical create screen; otherwise reads the list/detail/print output, since nothing is left pending for them to approve.
- **Finance**: no matching surface — see [04 — Test Scenarios — Finance](./04-test-scenarios-finance.md) correction notice.
- **Audit / Config**: no matching surface beyond the generic reason-code master — see [04 — Test Scenarios — Audit / Config](./04-test-scenarios-audit-config.md) correction notice.

## 3. Persona Test Files

- [Store Keeper scenarios](./04-test-scenarios-store-keeper.md)
- [Inventory Controller scenarios](./04-test-scenarios-inventory-controller.md)
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Cutting Scenarios

| # | Scenario | Pre-condition | Expected end state |
| - | -------- | ------------- | ------------------- |
| 1 | Save and Submit produce the identical result | Any valid Stock-In/Stock-Out form. | Both buttons call `create()`; the backend writes `doc_status = completed` and posts the ledger either way — no observable difference between the two paths. |
| 2 | Edit is unreachable on a real document | Any `completed` document, opened in view mode. | `isReadOnly = true` (since `doc_status === 'completed'`); the Edit button (`isView && !isReadOnly`) does not render. |
| 3 | Void is unreachable through the UI | Any `completed` document. | The Void button requires `isEdit`, which is only reachable via the (unreached) Edit button — Void never renders. A direct `PATCH` with `doc_status: "voided"` does work server-side (see `04-test-scenarios-inventory-controller.md` IC-HP-02). |
| 4 | List-view Delete always fails | Any `completed` document, from the list's row-menu. | Clicking Delete → Confirm calls the delete mutation, which returns `"Cannot delete a completed Stock In — inventory has already been adjusted"` (or the Stock-Out equivalent) — a 400, surfaced as an error toast. |
| 5 | Voiding a document removes it from the list | A document voided via direct API call. | `voidStockIn`/`voidStockOut` set `deleted_at` alongside `doc_status = voided`; the list and detail endpoints both filter `deleted_at: null`, so the document disappears from both rather than showing a "Voided" badge. |

## 5. E2E Test Mapping

| Spec | Coverage |
| ---- | -------- |
| [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) | Reason-code (`tb_adjustment_type`) master-data CRUD — code uniqueness, active/inactive toggle, list/search. Does not exercise the Stock-In/Stock-Out screens themselves. |

No spec was found exercising Stock-In/Stock-Out creation, the cost-suggestion probes, the insufficient-stock rejection, or the void endpoint. These are gaps, not "manual/planned" coverage claimed by a prior version of this page — no test-plan annotation referencing them was found either.

## 6. References

- Sibling: [03-user-flow.md](./03-user-flow.md) — the always-completed lifecycle every scenario above is scoped to.
- Sibling: [02-business-rules.md](./02-business-rules.md) — the rule IDs referenced above.
- Per-persona detail: [Store Keeper](./04-test-scenarios-store-keeper.md), [Inventory Controller](./04-test-scenarios-inventory-controller.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md).
