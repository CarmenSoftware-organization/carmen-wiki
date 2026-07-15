---
title: Good Receive Note (GRN) — Test Scenarios — Purchaser
description: Purchaser's test cases (happy path, permission, validation, edge cases) for good-receive-note.
published: true
date: 2026-07-15T00:00:00.000Z
dateCreated: 2026-05-19T23:55:00.000Z
tags: good-receive-note, test-scenarios, purchaser, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — Test Scenarios — Purchaser

> **At a Glance**
> **Persona:** Purchaser (Procurement Officer + Department Manager) &nbsp;·&nbsp; **Module:** [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; **Scenarios:** ~12
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** maps to `501-grn.spec.ts` in `../carmen-inventory-frontend-e2e/`
> **Corrected this pass (2026-07-15):** removed `accepted_qty` references (no such field exists), the pricelist-deviation-check scenarios (no matching code found in the GRN module), the Finance/credit-note handoff scenarios (no three-way-match feature confirmed — see [04-test-scenarios-finance.md](./04-test-scenarios-finance.md)), and re-labelled segregation-of-duties as unconfirmed rather than enforced.

This page captures the test scenarios that the Purchaser persona (the **Purchaser / Procurement Officer** who raised the upstream PO, plus the **Department Manager** subset) directly drives in the `good-receive-note` module. The Purchaser is a **review-only** participant on the GRN — they do **not** create the GRN at the dock, do **not** save line entries (the save is what posts inventory and advances the PO — see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)), and do **not** commit or edit the GRN document at any state.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| PUR-HP-01 | Open a `saved` / `committed` GRN against an own PO in read mode | Purchaser `purchase@blueledgers.com` is the `buyer_id` of PO `PO-X` at `po_status ∈ {sent, partial}`; Receiver has driven a GRN against `PO-X` to `saved` (which already posted inventory and advanced the PO). | 1. Open the PO module's Receiving History tab for `PO-X`. 2. Click into the GRN row. | The GRN read view opens; header shows `doc_status`, `vendor_id`, `receipt_date`, currency; lines show `order_qty`, `received_qty`, and the pending balance on the source PO; no edit, save, commit, or void affordance is rendered. Maps to TC-GRN-010001. |
| PUR-HP-02 | Review a clean receipt — no vendor contact needed | A GRN against own PO `PO-X` where every line satisfies `received_qty = pending_qty`. | 1. Open the GRN from the Receiving History tab. 2. Compare the line-level `received_qty` / `pending_qty` columns. | No vendor-side action is fired; no PO amendment raised; the GRN document itself is **not** edited; the PO line transitions naturally at the Receiver's save (`sent → partial → completed`). |
| PUR-HP-03 | Review a short receipt and chase the vendor | GRN against own PO `PO-Y` (`order_qty = 10`) with `received_qty = 6` on the line; Receiver wrote a variance comment; `po_status = sent → partial`. | 1. Open the GRN. 2. Confirm `received_qty (6) < pending_qty (10)`. 3. Read the Receiver's comment. 4. Contact the vendor outside the GRN document (email / vendor portal). 5. Write a comment recording the vendor's response. | Vendor chase fires off-document; the GRN itself is unchanged — no header / line mutation by the Purchaser; source PO stays at `po_status = partial` with pending = 4; when the follow-up shipment arrives, the Receiver creates a second GRN which advances `received_qty` to 10 and flips `po_status → completed`. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| PUR-PERM-01 | Purchaser opens a GRN in read mode where they own the source PO | **Allow.** The GRN read endpoint is open to the user identified by `tb_purchase_order.buyer_id` for every line on the GRN that carries a `purchase_order_detail_id` pointing to a PO they own. Header, line, lot, attachment, and activity log are all visible; **no** edit, save, commit, or void affordance is rendered. Maps to TC-GRN-010001. |
| PUR-PERM-02 | Purchaser attempts to open a GRN whose source PO they do **not** own | **Deny — scope.** A direct deep-link to the GRN detail returns `403` / redirects to the GRN list with the row filtered out. Maps to TC-GRN-010003. |
| PUR-PERM-03 | Purchaser attempts to modify a GRN header / line | **Deny — Receiver only.** The header edit and line add / edit / delete endpoints return `"This action requires the Receiver / Store Keeper role."` The UI hides every edit affordance for the Purchaser role. **Unconfirmed** whether this is enforced by a segregation-of-duties rule specifically, or simply by the Purchaser role never holding an edit permission for this module — no `buyer_id` cross-check was found in `good-received-note.service.ts` during this pass. Maps to TC-GRN-080005. |
| PUR-PERM-04 | Purchaser attempts to create a GRN (New GRN button) | **Deny — Receiver / Inventory Manager only.** The **New GRN** button is hidden / disabled for the Purchaser role; a direct API call returns `"GRN creation requires the Receiver (Store Keeper) or Inventory Manager role."` |
| PUR-PERM-05 | Purchaser attempts to commit a `saved` GRN | **Deny — Inventory Manager only.** The **Commit** button is hidden / disabled for the Purchaser role; a direct API call returns `"Commit from status saved requires the Inventory Manager role."` Maps to TC-GRN-110002. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| PUR-VAL-01 | Purchaser cannot trigger commit on a `saved` GRN they own the source PO for | A `saved` GRN sits against own PO `PO-X`; Purchaser tries to call the commit endpoint directly. | **Reject** — role check. Server returns `"Commit from status saved requires the Inventory Manager role."` `doc_status` stays `saved`. Maps to TC-GRN-110002. |
| PUR-VAL-02 | Purchaser attempts to edit a line's `received_qty` on a GRN they own the source PO for | `saved` GRN against own PO with `received_qty = 10`; Purchaser tries to PATCH the line. | **Reject** — role check. Server returns `"Line quantities are editable only by the Receiver / Store Keeper role."` The line stays unchanged; the Purchaser's correct path is to comment on the GRN and ask the Receiver to re-evaluate while the GRN is still `saved`. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| PUR-EDGE-01 | Multi-PO consolidation review — single GRN spanning two of the Purchaser's POs | Same vendor delivers in one truck covering `PO-A` (one line, pending 4) and `PO-B` (two lines, pending 6 each); Receiver consolidates into one GRN with three lines per RCV-EDGE-04 (see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md)); both POs are owned by the same Purchaser. | Opening the GRN renders all three lines (cross-PO ownership scope is unified for the read view since the Purchaser owns both POs); a short line's variance is scoped to the PO it sits against (`PO-A` line `L1`, or `PO-B` line `L1` / `L2`). Maps to TC-GRN-040002, TC-GRN-040004. |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — cross-persona handoffs that pivot off the Purchaser.
- User flow: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — happy-path source for Section 1 above.
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — upstream test set that creates and saves (posts) the GRN.
- Sibling: [04-test-scenarios-finance.md](./04-test-scenarios-finance.md) — correction page: why no credit-note / three-way-match handoff test scenarios exist.
- Business rules being verified: [02-business-rules.md](./02-business-rules.md) — segregation-of-duties (`GRN_AUTH_010`, marked unconfirmed this pass) referenced in PUR-PERM-03, PUR-VAL-01, PUR-VAL-02.
- Cross-link: [purchase-order](/en/inventory/purchase-order) — upstream module owned by this persona; the source of `pending_qty`, `po_status`, and the activity log.
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — canonical Playwright spec for the GRN module. Purchaser-relevant test groups: **TC-GRN-010001** (View GRN List), **TC-GRN-010003** (View GRN List with Insufficient Permissions), **TC-GRN-080005** (Edit Line Item in RECEIVED status — role denial), **TC-GRN-110002** (No Permission to Commit), **TC-GRN-040002 / 040004** (Create from Multiple POs — multi-PO consolidation review).
