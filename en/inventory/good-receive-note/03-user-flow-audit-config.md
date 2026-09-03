---
title: Good Receive Note (GRN) — User Flow — Audit & Config
description: Why no dedicated GRN configuration console or lot-recall tool was confirmed for good-receive-note in current source, and what is actually confirmed.
published: true
date: 2026-07-15T00:00:00.000Z
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
| Lot-number generation | **Confirmed, but not configurable.** `inventory-transaction.service.ts` generates lot numbers in one fixed format — `RC{YY}{MM}{4-digit sequence}` — computed in code. No lot-number-format editor / token-grammar panel was found anywhere in the frontend. |
| RBAC roles and approval thresholds specific to GRN | **Not implemented as a dedicated GRN panel.** Authorization is generic RBAC shared across modules (see [access-control](/en/inventory/access-control)); no "approval threshold" concept exists anywhere in the backend for this module (mirrors the same finding already confirmed for the `purchase-order` module's `PO_AUTH_004`). |
| Tax codes, currency rates, cancellation/rejection reason codes | **Real, but generic — not GRN-owned.** Tax profiles, currencies, and running-code sequencing are configured through the cross-module [system-config](/en/inventory/system-config) and [master-data](/en/inventory/master-data) screens, not a GRN-specific console. |
| Integration endpoints to PO / Inventory / Finance / Vendor (with a dual-write cutover workflow) | **Not implemented.** No integration-endpoint configuration UI or dual-write mechanism was found for this module. |
| Auditor read-only activity-log review | **Plausible but unconfirmed as a dedicated screen.** `tb_good_received_note.workflow_history` (JSON) is a real, populated field that a generic activity-log / reporting screen could read; no GRN-specific "audit module" route was found — see [reporting-audit](/en/inventory/reporting-audit) for the generic equivalent. |
| Lot-recall trace tool (forward/backward trace via `lot_no`) | **Not implemented as a dedicated tool.** The underlying data linkage is real (`tb_good_received_note_detail_item.inventory_transaction_id` → `tb_inventory_transaction_detail.lot_no`), so a trace is *possible* by joining tables, but no purpose-built recall-trace screen or export workflow was found in current source. |
| Sensitive-field export requiring Controller/DPO secondary approval | **Not implemented.** No approval-workflow code for exports was found anywhere in the module. |
| Post-commit void requiring Inventory Manager + Finance co-authorisation | **Not implemented.** The `/void` endpoint (`GoodReceivedNoteService.voidGrnById`) has no `doc_status` precondition beyond "not already voided" and no co-authorisation gate of any kind — see [02-business-rules.md](./02-business-rules.md) `GRN_POST_010`. |

This heavily overlaps the **system-config** and **access-control** modules' scope — recurring, cross-module screens (workflow-stage config, running-code / GRN-number sequencing, tax-profile, currency) genuinely exist elsewhere in the product, just not under a GRN-specific "configuration console" name. Recommend consulting those modules' own pages for what is actually configurable.

## References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — the corrected four-state lifecycle.
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — the persona whose `draft → saved` transition writes the `workflow_history` entries a generic activity-log screen would read.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — correction page for the parallel three-way-match / AP fabrication.
- Sibling: [02-business-rules.md](./02-business-rules.md) §4 / §6 — authorization and cross-module rules, several marked unconfirmed or not implemented this pass.
- Related, real generic modules: [system-config](/en/inventory/system-config), [master-data](/en/inventory/master-data), [access-control](/en/inventory/access-control), [reporting-audit](/en/inventory/reporting-audit).
- `../carmen/docs/good-recive-note-managment/GRN-Overview.md` — carmen/docs module overview: System Administrator role description; treat as design intent, not verified current behavior, for anything beyond the generic cross-module screens above.
