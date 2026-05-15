---
title: Spot Check — User Flow — Inventory Controller
description: Inventory Controller path through the spot-check lifecycle.
published: true
date: 2026-05-15T14:30:00.000Z
tags: spot-check, user-flow, inventory-controller, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — User Flow — Inventory Controller

## 1. Persona

**Inventory Controller** — the single owner of the spot-check exercise: defines selection criteria (`method` = random / high_value / manual, `size` of the sample), schedules and launches the spot check, assigns the Counter, monitors progress, reviews variances, approves or rejects recount requests, and triggers the variance rollup to [[inventory-adjustment]]. Authority anchor for `SPC_AUTH_001`.

## 2. Entry Points

- **Spot-check scheduler / launcher** — open a new `tb_spot_check` for an inventory or consignment location.
- **My spot checks** — list of in-flight `tb_spot_check` documents owned by the controller (`pending` / `in_progress`).
- **My queue** — recount-flagged lines and pending submissions awaiting controller action.
- **Notifications** — counter completion alerts, variance-breach alerts.

## 3. Primary Actions

| Action | State precondition | State effect | Notes |
| ------ | ------------------ | ------------ | ----- |
| Open spot check (random sampling) | Location is inventory- or consignment-type per `SPC_VAL_001` | New `tb_spot_check` in `pending`; `method = random`; system samples `size` distinct products | Per `SPC_VAL_002`–`SPC_VAL_003`. |
| Open spot check (high-value sampling) | Same | New `tb_spot_check` in `pending`; `method = high_value`; top-`size` products by value / velocity sampled | Per `SPC_VAL_003`. |
| Open spot check (manual selection) | Same | New `tb_spot_check` in `pending`; `method = manual`; controller adds `tb_spot_check_detail` rows explicitly | Manual is the event-driven path (suspected discrepancy, incident). |
| Assign counter | Spot check in `pending` | Counter location-grant recorded | Per `SPC_AUTH_004`. |
| Monitor progress | Spot check in `in_progress` | (read) lines with `actual_qty` populated vs total | No persisted progress counters on `tb_spot_check` — derived per `SPC_CALC_004`. |
| Flag line for recount | Variance breaches tolerance per `SPC_VAL_006` | Detail-comment with recount tag | Recount ideally by a different counter to remove bias. |
| Override / accept variance | `SPC_VAL_006` flag exists | Flag cleared; line eligible for rollup | Controller countersignature recorded in detail-comment thread. |
| Submit spot check | All detail lines have `actual_qty`; no open recount flags | `doc_status = completed`; rollup adjustment created | Per `SPC_POST_001`–`SPC_POST_002`. |
| Void spot check | Status is `pending` or `in_progress` | `doc_status = void`; no rollup | Per `SPC_VAL_008`; partial entries preserved. |

## 4. Decision Points

- **Method choice.** *Random* maintains rotating coverage of inventory. *High_value* concentrates effort on theft-prone or pilferage-prone categories. *Manual* responds to a specific trigger (discrepancy, incident, dispute). Drive by risk profile and operational signal.
- **Tolerance breach response.** When `|diff_qty| / on_hand_qty` exceeds threshold, the controller can (a) trigger recount (different counter), (b) override / accept the variance with countersignature, (c) hold the line pending investigation.
- **Submit vs hold vs void.** Once all lines counted, controller chooses to submit (firing the rollup), hold pending operational reconciliation (e.g. expected receipts not yet posted), or void if the spot check itself was mis-scoped.

> **TODO:** Source the exact UI for sampling method selection, recount flagging, override countersignature, and rollup-trigger button from `../carmen-inventory-frontend/`.

## 5. Exit / Handoff

| Trigger | Handoff to | Artefact |
| ------- | ---------- | -------- |
| Submit spot check | System → [[inventory-adjustment]] rollup | `tb_spot_check.doc_status = completed`; `tb_stock_in` / `tb_stock_out` created with `info.spotCheckId`. |
| Route rollup adjustment for approval | Audit / Config (Approver / Finance) per `ADJ_AUTH_*` | Rollup `tb_stock_in` / `tb_stock_out` in `in_progress`. |
| Void | (terminal) | `tb_spot_check.doc_status = void`. |

## 6. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — Inventory Controller UI screens.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists.
- Related: [[spot-check/03-user-flow]] (overview), [[spot-check/02-business-rules]] (`SPC_AUTH_001`, `SPC_VAL_*`, `SPC_POST_*`), [[physical-count/03-user-flow-count-lead]] (full-count counterpart owner path — same persona acting with a wider scope), [[inventory-adjustment/03-user-flow-inventory-controller]] (rollup-side flow, same persona acting as adjustment owner).
