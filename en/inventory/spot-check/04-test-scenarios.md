---
title: Spot Check — Test Scenarios
description: Test cases by screen, end-to-end scenarios, and the manual test-case catalog mapping for spot checks.
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Test Scenarios

> **At a Glance**
> **Module:** [spot-check](/en/inventory/spot-check) &nbsp;·&nbsp; **Scope:** one real permission-gated role split across two screen files (list/create; entry/review), plus a confirmed-absent third group
> **Run order:** list/create-screen scenarios → entry/review-screen scenarios → end-to-end scenarios below
> **E2E coverage:** no `spot-check` Playwright spec exists at `../carmen-inventory-frontend-e2e/tests/`; a manual test-case catalog exists at `docs/test-cases/760-spot-check.md` (32 cases, authored from the live component) — see § 5 for how it maps to, and diverges from, the real routing

## 1. Overview

This page is the overview entry point for the test-scenarios set of the `spot-check` module. Coverage is organised around the module's one real permission-gated role, viewed from its two screen pairs — the location list and create form (`04-test-scenarios-inventory-controller.md`) and the entry/review flow (`04-test-scenarios-counter.md`) — plus a correction page (`04-test-scenarios-audit-config.md`) documenting a confirmed-absent third persona group. Section 4 below covers end-to-end scenarios crossing all four screens in one document's lifecycle.

## 2. Scope

- **List / Create screens** — starting a spot check for a location, choosing a sampling method and scope; per [spot-check/03-user-flow-inventory-controller](/en/inventory/spot-check/03-user-flow-inventory-controller).
- **Entry / Review screens** — line entry, notes, import/export, Submit for Review, and the final Submit; per [spot-check/03-user-flow-counter](/en/inventory/spot-check/03-user-flow-counter).
- **Confirmed-absent** — an Approver/Finance, Auditor, or Sysadmin surface; per [spot-check/03-user-flow-audit-config](/en/inventory/spot-check/03-user-flow-audit-config).

## 3. Persona Test Files

- [List/Create-screen scenarios](./04-test-scenarios-inventory-controller.md)
- [Entry/Review-screen scenarios](./04-test-scenarios-counter.md)
- [Confirmed-absent group (correction page)](./04-test-scenarios-audit-config.md)

## 4. End-to-End Scenarios

Each row below is a full document lifecycle, anchored to the real state machine in [03-user-flow.md](./03-user-flow.md) § 2.

| # | Scenario | Steps | Expected end state |
| - | -------- | ----- | ------------------- |
| 1 | Random sample, no variance | Start (Random, `items = 10`) → count every line to match whatever `reviewItems()` computes → Save For Resume → Submit For Review → Submit Spot Check. | `tb_spot_check.doc_status = completed`; no other document created; every `diff_qty = 0`. |
| 2 | High-value sample, mixed overage and shortage | Start (High Value, `items = 10`, no `minimum_cost`) with an open/locked fiscal period → count producing both positive and negative variance → Submit For Review → Submit. | `doc_status = completed`; review screen showed both overage and shortage tiles; no rollup document exists anywhere for either. |
| 3 | Manual sample, triggered by a suspected discrepancy | Start (Manual) → pick 3 specific products via the transfer picker → count → Submit For Review → Submit. | Exactly 3 detail rows created and counted; `doc_status = completed`. |
| 4 | High-value sample with no open fiscal period | Attempt Start (High Value) when no `tb_period` has `status ∈ {open, locked}`. | `POST /spot-checks` rejected with `SPOT_CHECK_NO_ACTIVE_PERIOD` (`SPC_VAL_004`); document not created. |
| 5 | Skip Save, go straight to Submit for Review | Start → count every line without ever clicking Save For Resume → Submit For Review (button available since `uncountedCount === 0`) → Submit. | `doc_status` never passes through `in_progress` — it goes `pending → completed` directly, since only Save performs that transition; the document still completes normally. |
| 6 | Submit with uncounted lines | Start → leave several lines at their seeded `actual_qty = 0` → Submit For Review → Submit. | Both calls succeed — there is no server-side completeness check (`SPC_VAL_008`); the uncounted lines simply show `diff_qty = -on_hand_qty` (a full shortage) on the review screen. |
| 7 | Reset an in-progress spot check | Start → Save a partial count → return to the list screen → click Reset → confirm. | `doc_status = void`; `tb_spot_check_detail` rows are **not** cleared (they still hold whatever was typed); the location falls back to the Not Started bucket. |
| 8 | Reopen a completed spot check from History | Complete a spot check → open it again from the History tab → click through to Submit For Review a second time. | `reviewItems()` succeeds (no status guard) and overwrites `on_hand_qty`/`actual_qty`/`diff_qty`/`counted_at` on every detail row; a subsequent attempt at the terminal Submit is rejected with `"Spot check is already completed"` (`SPC_VAL_008`). |
| 9 | `doc_version` conflict | Two browser tabs open the same spot check; Tab A saves; Tab B then saves using its now-stale `doc_version`. | Tab B's save fails to match the `where` clause and is rejected; client must reload and retry. |
| 10 | No products at the location | Start a spot check for a location with an empty eligible product pool (no `tb_product_location` assignment and no non-zero stock). | `POST /spot-checks` rejected with `"No products found at this location"` (`SPC_VAL_002`); document not created. |
| 11 | Manual sample with a product outside the location's pool | Start (Manual) → select a product that has never been assigned to or stocked at this location. | If it is the only product selected, creation is rejected with `"None of the selected products were found at this location"` (`SPC_VAL_003`); if selected alongside valid products, it is silently dropped and the rest proceed. |
| 12 | Variance never reaches the ledger | Complete a spot check with several confirmed shortages. | `tb_spot_check.doc_status = completed`; no `tb_stock_in`/`tb_stock_out`, no `tb_inventory_transaction` row, and no field anywhere referencing this spot check exists outside its own tables — a user must separately create an [inventory-adjustment](/en/inventory/inventory-adjustment) document to correct the ledger, with no system-provided link back to this spot check. |

## 5. Manual Test-Case Catalog Mapping

No `spot-check` Playwright spec exists at `../carmen-inventory-frontend-e2e/tests/` (verified by `ls tests/ | grep -i 'spot\|check'`). A manual, documentation-only test-case catalog exists instead at `docs/test-cases/760-spot-check.md` — 32 cases (`TC-SPC-*`), explicitly authored by reading the live component, the closest thing to an executable spec this module has. Most of its scenarios match the routing and mechanics confirmed in this pass (locations/history toggle, KPI tiles, the three creation methods, entry-screen filters/notes/calculator, Submit For Review, the review screen's stat tiles, and the final Submit renaming `doc_status` to `completed`).

**Two scenarios in that catalog describe a screen this app's routing does not actually reach.** `TC-SPC-040001` ("edit a saved spot check: open detail in view mode, click Edit, edit description, Save") and `TC-SPC-050001` ("delete a saved spot check: open detail, click Edit, click Delete") both presuppose a view/edit detail screen distinct from the counting screen. Direct reading of `router.tsx` shows `spot-check/:id` always renders `sc-entry-component.tsx` (the counting UI) — never `sc-form.tsx` in view or edit mode. `ScForm`'s `isView`/`isEdit` branches, and the `useUpdateSpotCheck`/`useDeleteSpotCheck` hooks its Save/Delete buttons call, are only ever instantiated from the create screen (`spot-check-by-location-content.tsx`), always without an entity — so those branches are unreachable dead code from any real navigation path. Treat `TC-SPC-040001`/`TC-SPC-050001` as describing intended-but-unwired functionality rather than a confirmed, testable flow; the underlying `update()`/`delete()` backend endpoints are real and would work if exercised directly (e.g. via Bruno), just not from any button in the shipped UI.

## 6. References

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts`, `spot-check.logic.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists; manual test-case catalog at `docs/test-cases/760-spot-check.md` (32 cases; two — `TC-SPC-040001`, `TC-SPC-050001` — describe an unreachable view/edit screen, see § 5).
- Related: [spot-check/03-user-flow](/en/inventory/spot-check/03-user-flow) (the state machine this page exercises), [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) (`SPC_VAL_*` / `SPC_AUTH_*` / `SPC_POST_*`), [inventory-adjustment/04-test-scenarios](/en/inventory/inventory-adjustment/04-test-scenarios) (where a confirmed variance must be manually corrected).
