---
title: Physical Count — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and E2E mapping for physical counts.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: physical-count, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Test Scenarios

> **At a Glance**
> **Module:** [physical-count](/en/inventory/physical-count) &nbsp;·&nbsp; **Scope:** one real permission-gated role split across two screen files (list; entry/review), plus a confirmed-absent third group
> **Run order:** period/period-provisioning checks → list-screen scenarios → entry/review-screen scenarios → end-to-end scenarios below
> **Executable coverage (2026-09-22):** no `physical-count` Playwright spec exists at `../carmen-inventory-frontend-e2e/tests/`. Manual catalog `docs/test-cases/750-physical-count.md` (41 cases, re-verified against the live component 2026-09-20 — it now documents the real mechanics, incl. the Start Period Close prerequisite and the "Counting has not started" dialog) and generated stories `docs/user-stories/750-physical-count.md` (33). `docs/persona-doc/System Process/tx-08-physical-stocktake.md` remains a planning-stage design that the implementation does not match — see [02-business-rules.md](/en/inventory/physical-count/02-business-rules) § 5.1. The period-end gap catalog `docs/test-cases/gaps/900-period-end-gap.md` (TC-PE-31xxxx) covers the Start-button unlock.

## 1. Overview

This page is the overview entry point for the test-scenarios set of the `physical-count` module. Coverage is organised around the module's one real permission-gated role, viewed from its two screens — the location list (`04-test-scenarios-count-lead.md`) and the entry/review flow (`04-test-scenarios-counter.md`) — plus a correction page (`04-test-scenarios-audit-config.md`) documenting a confirmed-absent third persona group. Section 4 below covers end-to-end scenarios that cross both screens in one document's lifecycle.

## 2. Scope

- **List screen** — starting or resuming a count for a location; per [physical-count/03-user-flow-count-lead](/en/inventory/physical-count/03-user-flow-count-lead).
- **Entry / Review screens** — line entry, notes, import/export, Submit for Review, and the final Submit; per [physical-count/03-user-flow-counter](/en/inventory/physical-count/03-user-flow-counter).
- **Confirmed-absent** — an Approver/Finance, Auditor, or Sysadmin surface; per [physical-count/03-user-flow-audit-config](/en/inventory/physical-count/03-user-flow-audit-config).

## 3. Persona Test Files

- [List-screen scenarios](./04-test-scenarios-count-lead.md)
- [Entry/Review-screen scenarios](./04-test-scenarios-counter.md)
- [Confirmed-absent group (correction page)](./04-test-scenarios-audit-config.md)

## 4. End-to-End Scenarios

Each row below is a full document lifecycle, anchored to the real state machine in [03-user-flow.md](./03-user-flow.md) § 2.

| # | Scenario | Steps | Expected end state |
| - | -------- | ----- | ------------------- |
| 1 | Full count, no variance | Start count for a location → enter `actual_qty` equal to whatever the review step computes for every line → Save → Submit for Review → Submit. | `tb_physical_count.status = completed`; no `tb_stock_in`/`tb_stock_out` created (every `diff_qty = 0`). |
| 2 | Full count, mixed overage and shortage | Start count → enter quantities producing both positive and negative variance lines → Save each line → Submit for Review → Submit. | Both a `tb_stock_in` (overage lines) and a `tb_stock_out` (shortage lines) are created, both already `doc_status = completed`; no `tb_inventory_transaction` row is written by this action (`PHC_POST_003`). |
| 3 | Resume an in-progress count | Save a partial set of lines → navigate away → return to the list screen → click Resume on the same location. | Navigates back to `/:id/entry` with the previously-saved lines still populated; no new document created. |
| 4 | Refresh mid-count picks up a newly-stocked product | A product receives its first stock movement at the location after the count sheet was created → click Refresh on the entry screen. | The new product line is appended to the sheet (`product_total` increases); previously-entered lines are unaffected. |
| 5 | `doc_version` conflict | Two browser tabs open the same count; Tab A saves; Tab B then saves using its now-stale `doc_version`. | Tab B's save is rejected with a `409`-style conflict (`PHC_VAL_007`); Tab B must reload and retry. |
| 6 | Submit blocked by an uncounted line | Every line shows a value on the entry screen from typing, but at least one of those values was entered and immediately submitted for review without an intervening Save. | Final Submit is rejected with `"<N> products have not been counted yet"`, since that line's `counted_at` was never stamped (`PHC_VAL_004`) — see the caveat in [02-business-rules.md](./02-business-rules.md). |
| 7 | Period-end close blocked by an incomplete required location | A required location (`physical_count_type = yes`) has no `completed` count under the closing period. | Period-end close is blocked by `period-end.validate.ts`'s `validatePhysicalCount` until that location's count reaches `completed`. |
| 8 | Not-required location counted anyway | A location flagged `physical_count_type = no` is counted and submitted to `completed` via the "include not-counted" toggle on the list screen. | Count completes normally; it has no effect on the period-end close gate, since only `physical_count_type = yes` locations are checked. |

## 5. E2E Spec Map

No `physical-count` Playwright spec exists at `../carmen-inventory-frontend-e2e/tests/` (verified by `ls tests/ | grep -i 'physical\|count'`). The manual catalog `docs/test-cases/750-physical-count.md` (41 cases) was rewritten against the live component on 2026-09-20 and is the closest thing to an executable spec — its case 24 note and `TC-PC-900002`–`900004` cover the Start Period Close prerequisite; `docs/user-stories/750-physical-count.md` (33) is generated from it. `docs/persona-doc/System Process/tx-08-physical-stocktake.md` still describes a design (own transaction type, `FINALIZED`/GL-posted status, location transaction lock, tolerance/recount) that the current implementation does not match; see [02-business-rules.md](/en/inventory/physical-count/02-business-rules) § 5.1. Treat every scenario in this module as manual until an automated spec is added, and write new automated coverage against the real mechanics documented here.

## 6. References

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts`, `.../physical-count-period/physical-count-period.service.ts`, `.../period-end/period-end.validate.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists; manual catalog `docs/test-cases/750-physical-count.md` (41), stories `docs/user-stories/750-physical-count.md` (33), planning doc `docs/persona-doc/System Process/tx-08-physical-stocktake.md`, period-end unlock in `docs/test-cases/gaps/900-period-end-gap.md`.
- Related: [physical-count/03-user-flow](/en/inventory/physical-count/03-user-flow) (the state machine this page exercises), [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) (`PHC_VAL_*` / `PHC_AUTH_*` / `PHC_POST_*`), [inventory-adjustment/04-test-scenarios](/en/inventory/inventory-adjustment/04-test-scenarios) (the tables the rollup writes into).
