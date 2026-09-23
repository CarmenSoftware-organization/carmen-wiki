---
title: Good Receive Note (GRN) — User Flow — Audit & Config
description: Why no dedicated GRN configuration console or lot-recall tool was confirmed for good-receive-note in current source, and what is actually confirmed.
published: true
date: '2026-09-22T18:00:00.000Z'
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, audit-config, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — User Flow — Audit & Config

> **At a Glance**
> **What this page documents:** why the previously-described "Audit / Config" flow (a GRN-specific configuration console with lot-number-format, RBAC, tax/currency/reason-code, and integration panels, plus a dedicated Auditor lot-recall tool with sensitive-field export approval) does not match current source, and what is actually confirmed.

> ⚠️ **Major correction this pass (2026-07-15).** The previous version of this page described a "GRN configuration console" (Sysadmin panels for lot-number format, RBAC roles and approval thresholds, tax / currency / reason codes, and PO / Inventory / Finance / Vendor integration endpoints) and an Auditor lot-recall trace tool with a Controller/DPO sensitive-field-export approval workflow. No matching route, frontend component, or backend endpoint was found in `carmen-inventory-frontend-react` or `carmen-turborepo-backend-v2`, and no such route appears in `.specs/resync-2026-07-15-routes-inventory.txt`.

## What is and is not confirmed

| Claim | Status |
| --- | --- |
| Lot-number generation | **Confirmed, but not configurable.** **Corrected 2026-09-22:** the format is `<location_code><YYMM><4-digit run>` (e.g. `MK-0126070246`), built by `buildLotNo()` in `apps/micro-business/src/common/helpers/lot-number.helper.ts:27-35`; the run number is the cost layer's `lot_seq_no`, which restarts at 1 every inventory period. The earlier `RC{YY}{MM}{seq}` pattern no longer exists. No lot-number-format editor exists in the frontend and there is no manual override on the GRN. |
| RBAC roles and approval thresholds specific to GRN | **Not implemented as a dedicated GRN panel.** Authorization is generic RBAC shared across modules (see [access-control](/en/inventory/access-control)); no "approval threshold" concept exists anywhere in the backend for this module (mirrors the same finding already confirmed for the `purchase-order` module's `PO_AUTH_004`). |
| Tax codes, currency rates, cancellation/rejection reason codes | **Real, but generic — not GRN-owned.** Tax profiles, currencies, and running-code sequencing are configured through the cross-module [system-config](/en/inventory/system-config) and [master-data](/en/inventory/master-data) screens, not a GRN-specific console. |
| Integration endpoints to PO / Inventory / Finance / Vendor (with a dual-write cutover workflow) | **Not implemented.** No integration-endpoint configuration UI or dual-write mechanism was found for this module. |
| Auditor read-only activity-log review | **Plausible but unconfirmed as a dedicated screen.** `tb_good_received_note.workflow_history` (JSON) is a real, populated field that a generic activity-log / reporting screen could read; no GRN-specific "audit module" route was found — see [reporting-audit](/en/inventory/reporting-audit) for the generic equivalent. |
| Lot-recall trace tool (forward/backward trace via `lot_no`) | **Not implemented as a dedicated tool.** The underlying linkage is real and, since 2026-08-10, direct: `tb_inventory_transaction_detail.good_received_note_detail_item_id → tb_good_received_note_detail_item` (real `@relation`), plus `GET …/good-received-notes/:id/stock-movements` which returns the lots per GRN line. No purpose-built recall-trace screen or export workflow exists. |
| Sensitive-field export requiring Controller/DPO secondary approval | **Not implemented.** No approval-workflow code for exports was found anywhere in the module. |
| Post-commit void requiring Inventory Manager + Finance co-authorisation | **Not implemented — and post-commit void is now refused outright.** `voidGrnById()` (`good-received-note.service.ts:2244-2256`) returns `GRN_COMMITTED_NOT_VOIDABLE` for a `committed` GRN; the only correction path is a credit note or inventory adjustment — see [02-business-rules.md](./02-business-rules.md) `GRN_POST_010`. |

This heavily overlaps the **system-config** and **access-control** modules' scope — recurring, cross-module screens (workflow-stage config, running-code / GRN-number sequencing, tax-profile, currency) genuinely exist elsewhere in the product, just not under a GRN-specific "configuration console" name. Recommend consulting those modules' own pages for what is actually configurable.

## References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the corrected four-state lifecycle.
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — the persona whose save / commit transitions write the activity entries a generic activity-log screen would read.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — correction page for the parallel three-way-match / AP fabrication.
- Sibling: [02-business-rules.md](./02-business-rules.md) §4 / §6 — authorization and cross-module rules, several marked unconfirmed or not implemented this pass.
- Related, real generic modules: [system-config](/en/inventory/system-config), [master-data](/en/inventory/master-data), [access-control](/en/inventory/access-control), [reporting-audit](/en/inventory/reporting-audit).
- `../carmen/docs/good-recive-note-managment/GRN-Overview.md` — carmen/docs module overview: System Administrator role description; treat as design intent, not verified current behavior, for anything beyond the generic cross-module screens above.
