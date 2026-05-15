---
title: Spot Check — User Flow — Counter
description: Counter path through the spot-check lifecycle.
published: true
date: 2026-05-15T14:30:00.000Z
tags: spot-check, user-flow, counter, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — User Flow — Counter

## 1. Persona

**Counter** — the floor-level worker who performs the physical count of in-scope items or locations on assigned spot checks, records counted quantities on the detail sheet (`tb_spot_check_detail.actual_qty`) accurately and on time, flags items that are damaged, unlabelled, or unfamiliar via line-level comments, and signs off completed sheets back to the Inventory Controller. Authority anchor for `SPC_AUTH_002`.

## 2. Entry Points

- **My spot-check assignments** — list of `tb_spot_check` documents with `pending` or `in_progress` status where the counter has a location-grant.
- **Spot-check sheet view** — drill into one spot check and see the detail lines for the assigned location.
- **Mobile / handheld scanner** — typical floor device for scanning product barcodes and entering `actual_qty` line by line; spot checks tend to be even more mobile-friendly than full physical counts because the scope is small.

## 3. Primary Actions

| Action | State precondition | State effect | Notes |
| ------ | ------------------ | ------------ | ----- |
| Open assigned spot-check sheet | Spot check in `pending` or `in_progress`; counter has location-grant | (read) detail lines visible | Per `SPC_AUTH_004`. |
| Enter first `actual_qty` | Spot check in `pending` | Spot check advances to `in_progress` | First line entry triggers transition. |
| Enter / edit `actual_qty` on a line | Line within assigned location | `actual_qty` saved; `counted_at` / `counted_by_id` stamped | `actual_qty ≥ 0` per `SPC_VAL_005`. |
| Flag damaged / unlabelled / unfamiliar item | Line on assigned spot check | `tb_spot_check_detail_comment` row created with attachment (photo) | Soft-flag; Inventory Controller reviews. |
| Add comment to spot check | Spot check in `in_progress` | `tb_spot_check_comment` row created | Free-text notes (e.g. "shelf restock in progress, recommend recount line 4"). |
| Sign off completed sheet | All assigned lines have non-null `actual_qty` | Notification fires to Inventory Controller | Counter does not submit the document — Inventory Controller does, per `SPC_AUTH_002`. |

## 4. Decision Points

- **Damaged / unfamiliar items.** When a counter finds an item that doesn't match the sheet (unlabelled, damaged, miscategorised), the line is flagged with a comment + photo; the variance handling decision is the Inventory Controller's.
- **Zero-on-shelf vs zero-counted.** If the sheet shows `on_hand_qty > 0` but the counter sees nothing, `actual_qty = 0` is entered explicitly (not left blank). Blank `actual_qty` blocks submit per `SPC_VAL_004`; entered-zero proceeds to variance flag.
- **Recount lines.** When a line is flagged for recount, the recount is ideally performed by a **different counter** to remove individual counting bias — convention rather than hard schema constraint.

> **TODO:** Source the exact mobile / scanner UI screens and any blind-count (book qty hidden) toggle from `../carmen-inventory-frontend/`. Confirm whether the same blind-count tenant policy used in physical-count applies here.

## 5. Exit / Handoff

| Trigger | Handoff to | Artefact |
| ------- | ---------- | -------- |
| Complete all assigned lines | Inventory Controller | Notification + completion tag in comment thread. |
| Flag line for further inspection | Inventory Controller | `tb_spot_check_detail_comment` with damaged / unlabelled tag. |
| (no submit action) | Inventory Controller | Counter cannot submit; only Inventory Controller per `SPC_AUTH_002`. |

## 6. References

- **Primary (TODO):** carmen/docs source — does not exist for this module.
- **Frontend (TODO):** `../carmen-inventory-frontend/` — Counter / mobile UI; check cmobile (`../cmobile/`) for the PWA-side spot-check sheet implementation if applicable.
- **E2E (TODO):** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists.
- Related: [[spot-check/03-user-flow]] (overview), [[spot-check/02-business-rules]] (`SPC_AUTH_002`, `SPC_VAL_004`–`SPC_VAL_005`), [[spot-check/03-user-flow-inventory-controller]] (the handoff partner), [[physical-count/03-user-flow-counter]] (full-count counterpart counter flow).
