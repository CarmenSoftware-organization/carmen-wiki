---
title: Inventory Adjustment — User Flow — Finance
description: Correction notice — no Finance persona, GL posting, or threshold-based approval exists for this module.
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, user-flow, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — User Flow — Finance

> **Correction notice.** This page previously described a Finance persona approving above-threshold adjustments, verifying GL-account mappings, and signing off on period-end reconciliation. None of this exists in the current source.

## What was checked

- A repo-wide search of `carmen-turborepo-backend-v2` and `carmen-inventory-frontend-react` for `journal`, `ledger`, and GL-posting code in the stock-in/stock-out module found no hits.
- `tb_adjustment_type` has no GL-account field, no document-required flag, no quality-check flag — only `code`, `name`, `type`, `description`, `is_active`, `note`.
- `enum_stage_role` (the platform's workflow-role enum) is `{create, approve, purchase, issue, view_only}` — it has no `finance` member, and this module's `create()`/`update()`/`void*()` methods never call a workflow orchestrator at all.
- A repo-wide search for `threshold` scoped to the inventory/stock-in/stock-out modules found zero relevant hits.
- The nav entry and every route under `/inventory-management/inventory-adjustment` gate on the single generic `inventory_management.view` permission — there is no distinct Finance-scoped permission or route guard.

## Claim status

| Previously claimed | Status | What the source actually shows |
| ------------------- | ------ | -------------------------------- |
| Finance approves above-Controller-threshold adjustments | **Fabricated** | No approval stage exists at all — `create()` always writes `doc_status = completed` directly (see [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules) § 1). |
| GL-account mapping per reason code (`info.glAccount`) | **Fabricated** | No such field exists on `tb_adjustment_type`; no journal/ledger code anywhere in this module. |
| Period-end sign-off / inventory-to-GL reconciliation | **Fabricated** | No matching route or backend method found for this module. Period close itself is a real feature of the separate [inventory](/en/inventory/inventory) module, unrelated to a Finance-specific sign-off here. |
| Compensating-reversal (void) authority | **Real endpoint, wrong owner** | `voidStockIn`/`voidStockOut` are real backend methods, but they aren't gated to any role — and the UI button that would call them never renders for any persisted document (see [03 — User Flow](/en/inventory/inventory-adjustment/03-user-flow) § 1). |

## Where to look instead

- [03 — User Flow](/en/inventory/inventory-adjustment/03-user-flow) — the actual (always-completed) document lifecycle.
- [03 — User Flow — Store Keeper](/en/inventory/inventory-adjustment/03-user-flow-store-keeper) / [Inventory Controller](/en/inventory/inventory-adjustment/03-user-flow-inventory-controller) — the two real, undifferentiated personas.
- [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules) — the module's real validation, calculation, and posting rules.
