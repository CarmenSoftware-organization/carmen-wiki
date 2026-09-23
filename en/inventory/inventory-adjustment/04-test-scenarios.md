---
title: Inventory Adjustment — Test Scenarios
description: Test cases for the draft → commit → void inventory-adjustment lifecycle, plus E2E coverage pointers.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory-adjustment, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Test Scenarios

> **At a Glance**
> **Module:** [inventory-adjustment](/en/inventory/inventory-adjustment) &nbsp;·&nbsp; **Personas covered:** Store Keeper, Inventory Controller (same undifferentiated screen); Finance and Audit/Config have no matching surface — see their pages
> **Headline fact that shapes every scenario below:** creation writes a `draft`; **Commit** posts; **Void** reverses (UI: drafts only; posted documents via API)
> **Executable coverage (2026-09-22):** no Playwright spec exercises this screen. Manual catalog `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (60 cases, re-verified against the redesigned form 2026-09-20 — covers Commit, Void-requires-Edit, Delete-in-view, status filter) and generated stories `docs/user-stories/730-inventory-adjustment.md` (32). `tests/031-adjustment-type.spec.ts` covers the reason-code master only.

## 1. Overview

The 2026-07-15 revision of this page was scoped to an always-completed document with dead Edit/Void buttons. Since the backend split create/commit on 2026-07-30 and the form redesign of the same day, the module has a real three-state lifecycle, so the scenarios below are re-based on `create()` (draft), `update()` (save), `commit()`, `delete()`, `voidStockIn()`/`voidStockOut()`, the period-date guards and the stock-out on-hand pre-check. Rule IDs refer to [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules).

## 2. Personas in Scope

- **Store Keeper**: enters Stock-In/Stock-Out documents, saves drafts, commits.
- **Inventory Controller**: reviews drafts, commits, deletes/voids, reads completed documents and their stock movements; voids posted documents through the API.
- **Finance**: no matching surface — see [04 — Test Scenarios — Finance](/en/inventory/inventory-adjustment/04-test-scenarios-finance).
- **Audit / Config**: no matching surface beyond the reason-code master — see [04 — Test Scenarios — Audit / Config](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config).

## 3. Persona Test Files

- [Store Keeper scenarios](/en/inventory/inventory-adjustment/04-test-scenarios-store-keeper)
- [Inventory Controller scenarios](/en/inventory/inventory-adjustment/04-test-scenarios-inventory-controller)
- [Finance scenarios](/en/inventory/inventory-adjustment/04-test-scenarios-finance)
- [Audit / Config scenarios](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config)

## 4. Cross-Cutting Scenarios

| # | Scenario | Pre-condition | Expected end state |
| - | -------- | ------------- | ------------------- |
| 1 | Save creates a draft, not a posting | Any valid Stock-In/Stock-Out form; click **Save** | `POST` returns `doc_status = draft`; no `tb_inventory_transaction`; on-hand unchanged; screen stays on `/{id}?type=…` in view mode with **Edit** and **Delete** visible. |
| 2 | Commit posts and locks | A draft; click **Commit** → confirm | `PATCH /{id}/commit` → `completed`; one ledger transaction per line with `inventory_transaction_id` stamped; on-hand moves; Edit / Delete / Void no longer render (`isReadOnly`), **Print** and **Stock movements** do (`TC-IADJ-060002`, `TC-IADJ-020005`). |
| 3 | Commit from a new form | Unsaved form; click **Commit** | Frontend first `POST`s the draft, then `PATCH /{id}/commit` with the returned `doc_version` — one completed document, no orphan draft. |
| 4 | Commit validation gate | Invalid form (missing location / reason / lines); click **Commit** | Zod errors shown; the confirm dialog never opens; no request sent (`TC-IADJ-060003`). |
| 5 | Void on a draft (UI) | Draft opened → **Edit** → **Void** with reason | `DELETE /{id}/void` → `voided` + `deleted_at`; nothing to reverse; document disappears from the list (`TC-IADJ-060001`). |
| 6 | Void on a posted document (API) | Completed stock-in; sufficient on-hand | `DELETE /{id}/void` → reversal `adjustment_out` per line; `voided` + soft-deleted; list no longer shows it. No UI path exists for this case. |
| 7 | Removal rules | Draft: the view-mode remove action → gone. Completed: the same call (API only) → 400 `Cannot delete a completed Stock In — inventory has already been adjusted`. |
| 8 | Period-end interaction | A draft stock-in dated in the current period | **Start Period Close** is blocked with the draft listed in "Finish these documents first"; committing or removing it unblocks. |

## 5. E2E Test Mapping

| Spec / catalog | Coverage |
| ---- | -------- |
| `../carmen-inventory-frontend-e2e/docs/test-cases/730-inventory-adjustment.md` (catalog, 60) | List (columns, `Type` badge, status filter incl. the never-matching `In Progress`), new/edit form, Commit / Void / Delete gating, read-only completed documents. Not automated. |
| `../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts` | Reason-code (`tb_adjustment_type`) master-data CRUD only. |
| `../carmen-inventory-frontend-e2e/tests/900-period-end.spec.ts` + `docs/test-cases/gaps/900-period-end-gap.md` | SI/SO cards and links on the period-end review (`TC-PE-320102`), draft SI/SO as start-counting blockers. |

Gaps: no automated test for Save/Commit/Void, the date guards, the on-hand pre-check, or the stock-movements panel.

## 6. References

- Sibling: [03-user-flow](/en/inventory/inventory-adjustment/03-user-flow) — the lifecycle every scenario above is scoped to.
- Sibling: [02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) — the rule IDs referenced.
- Per-persona detail: [Store Keeper](/en/inventory/inventory-adjustment/04-test-scenarios-store-keeper), [Inventory Controller](/en/inventory/inventory-adjustment/04-test-scenarios-inventory-controller), [Finance](/en/inventory/inventory-adjustment/04-test-scenarios-finance), [Audit / Config](/en/inventory/inventory-adjustment/04-test-scenarios-audit-config).
