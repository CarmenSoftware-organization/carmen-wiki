---
title: Purchase Order — User Flow — Receiver
description: Receiver's flow within the purchase-order module — physically accepts goods, raises GRN against PO, triggers receipt state transition.
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, user-flow, receiver, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — User Flow — Receiver

## 1. Role in This Module

The **Receiver** persona covers the **Receiver / Store Keeper** at the dock and the **Inventory Manager** who oversees receipt closure for the location. Together they own the physical-acceptance leg of the procure-to-pay chain: the Store Keeper inspects the vendor's delivery against the PO, raises the **Good Receive Note** (GRN) line by line, and records `received_qty` and `accepted_qty` on each PO line; the Inventory Manager supervises that posting and closes POs once receipt is complete or accepted as final. The PO status on entry to this flow is `sent` (or `partial` for follow-on deliveries). The GRN posting itself is performed in the downstream `[[good-receive-note]]` module — this page describes the **PO-side effects only**: how the Receiver's GRN flips `tb_purchase_order.po_status` from `sent → partial` (`PO_POST_006`) or `sent → completed` / `partial → completed` (`PO_POST_007`), how the Inventory Manager closes a `partial` PO with the remainder written to `cancelled_qty` (`PO_POST_011`), and how the PO line counters (`received_qty`, `cancelled_qty`) advance against `order_qty`. Inventory on-hand is incremented by the GRN module, not by the PO. Segregation of duties is enforced by `PO_AUTH_010` — the user who created or transmitted the PO MUST NOT be the same user who posts the GRN against it.

## 2. Entry Point and Primary Flow

**Entry point:** Two equivalent paths into the GRN posting:

- **From the PO module** — open a PO at `po_status ∈ {sent, partial}` and click **Receive** on the PO header, which deep-links into the GRN module with the PO pre-selected.
- **From the GRN module directly** — start a new GRN, pick the vendor, then select the PO from the list of open POs against that vendor / delivery location.

Either entry routes into the same posting screen; the PO-side effects below are identical.

**Primary flow (8 steps):**

1. **Open the PO** at the dock against the physical delivery. The screen shows each line's `order_qty`, the running `received_qty`, `cancelled_qty`, and the pending balance (`order_qty − received_qty − cancelled_qty`). Authorization is checked under `PO_AUTH_008` (Inventory Manager / Receiver may act when `po_status ∈ {sent, partial}`) and `PO_AUTH_010` (the GRN poster must not be the PO buyer / transmitter).
2. **Verify the physical delivery against the PO** — match the delivery note / packing list to the PO lines, count cartons, and identify any short delivery, over delivery, wrong item, or quality issue before opening the GRN.
3. **Start a new GRN** referencing the PO. The GRN header inherits `vendor_id`, `currency_id`, and delivery location from the PO; the GRN detail rows are pre-populated from `tb_purchase_order_detail` with `pending_qty` as the default editable quantity.
4. **Enter `received_qty` per line** — what physically arrived in the order UoM. May equal, be less than, or (subject to over-delivery policy) exceed the pending balance.
5. **Enter `accepted_qty` per line** — what passes quality / specification inspection and is accepted into inventory. `accepted_qty ≤ received_qty`; the gap (`received_qty − accepted_qty`) is the quality-rejection variance that stays with the vendor for return / credit note.
6. **Review totals and discrepancies** — the GRN screen displays variance summary (short, over, quality-reject) and the resulting PO line state preview (will this line close, or stay open?).
7. **Post the GRN.** On post, the GRN module commits the transaction: it writes the GRN detail rows, increments `tb_purchase_order_detail.received_qty` by the GRN line quantity, updates the PR-side bridge `tb_purchase_order_detail_tb_purchase_request_detail.received_qty` proportionally, and increments inventory on-hand by `accepted_qty` (handled inside the GRN / inventory module, not by the PO).
8. **PO state updates** are computed line-wise and applied to the header:
   - If at least one PO line still has `received_qty < order_qty − cancelled_qty`, `po_status` is set to `partial` (`PO_POST_006`). The PO remains open for further GRN posts.
   - If **every** active PO line satisfies `received_qty + cancelled_qty ≥ order_qty`, `po_status` is set to `completed` (`PO_POST_007`). The PO is closed normally; no further GRNs are accepted.

## 3. Decision Branches

- **Short delivery** (`received_qty < pending_balance`): post the GRN with what physically arrived. The PO transitions to `partial` (or stays at `partial`) under `PO_POST_006`; the unfulfilled balance remains as the pending quantity on the affected lines, available for a subsequent GRN. Notify the Purchaser via the standard activity log so the vendor can be chased for the remainder.
- **Over delivery** (`received_qty > pending_balance`): the GRN module gates this against the tenant over-delivery tolerance. If accepted (within tolerance or with explicit override), the GRN posts the over-shipped quantity, `tb_purchase_order_detail.received_qty` rises above `order_qty − cancelled_qty`, and the PO transitions to `completed` (`PO_POST_007`). If rejected (out of tolerance), the Receiver caps `received_qty` at the pending balance and refuses the excess at the dock — no system record for the rejected excess; the Purchaser logs the vendor-side dispute on the PO.
- **Quality issue** (`accepted_qty < received_qty`): post the GRN with both values. The line's pending balance is reduced by `received_qty`, but inventory on-hand only rises by `accepted_qty`; the variance (`received_qty − accepted_qty`) is the return / credit-note quantity tracked on the GRN. The PO does not auto-correct — the resolution path is amendment, return, or credit note initiated by the Purchaser.
- **Wrong item** (delivery does not match the PO product): **do not post a GRN.** Refuse the delivery at the dock and escalate to the Purchaser, who logs the vendor-side error in `tb_purchase_order_comment`. The PO remains at `sent` (or its prior state) with no quantity change.
- **Partial GRN now, remainder later**: post the GRN for what arrived today; `po_status` becomes `partial` (`PO_POST_006`) and the open balance is carried forward. When the next shipment arrives, repeat steps 1–7 above; the PO either stays `partial` or progresses to `completed` when the final balance clears (`PO_POST_007`).
- **Close PO with remainder cancelled** (Inventory Manager only): when the vendor cannot supply the outstanding quantity, the Inventory Manager closes the PO under `PO_AUTH_008` / `PO_POST_011`. For each line still pending, the application writes the remainder to `cancelled_qty` so that `received_qty + cancelled_qty = order_qty`; `po_status` becomes `closed` (terminal). Reason text is required and recorded in `tb_purchase_order_comment`.

## 4. Exit Point / Handoffs

The Receiver's involvement on a given PO ends on **GRN post**. From that point the document state on Carmen is one of:

- `partial` — at least one PO line still has open balance; the Receiver may re-enter the flow when the next shipment arrives.
- `completed` — every line is fully received; the PO is at its terminal receipt state and is read-only for inventory purposes. The matched-but-unbilled position is handed off to **Finance** for three-way match (PO ↔ GRN ↔ invoice) once the vendor's invoice arrives; the AP liability is then posted under `PO_POST_008`.
- `closed` — the **Inventory Manager** closed a `partial` PO with the remainder written to `cancelled_qty` under `PO_POST_011`; the close-out is reviewed by Finance for any already-posted GRNs against the closed lines.

In all three cases the next persona is **Finance** for invoice match (and for closed POs, close-out reconciliation). The PO itself is not status-changed by the three-way match — the match outcome lives on the linked invoice record and the AP posting; the PO retains whichever fulfilment status it reached (`partial`, `completed`, or `closed`). See the Finance persona file for the receiving side of the invoice handoff.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — global PO state machine and cross-persona handoff table; the `sent → partial → completed` row and the `partial → closed` row are this persona's territory.
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — upstream internal persona that transmits the PO and is notified of discrepancies at the dock for amendment / return / credit-note follow-up.
- Sibling: [03-user-flow-procurement-manager.md](./03-user-flow-procurement-manager.md) — holds the close / void override authority and reviews `partial → closed` decisions alongside the Inventory Manager.
- Sibling: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — external party whose physical delivery this persona accepts at the dock.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — downstream persona that picks up the matched-but-unbilled position for three-way match after GRN post.
- Related: [[good-receive-note]] — downstream module where the GRN is actually raised and posted; this page describes the PO-side effects only.
- Related: [[inventory]] — on-hand increment from `accepted_qty` is owned by the inventory module on GRN post; the PO contributes only the on-order pipeline quantity (`order_qty − received_qty − cancelled_qty`) per `PO_XMOD_008`.
- Sibling: [02-business-rules.md](./02-business-rules.md) — `PO_POST_006`, `PO_POST_007`, `PO_POST_011`, `PO_AUTH_008`, and `PO_AUTH_010` for the receipt-side transitions and authorization referenced above.
- `../carmen/docs/purchase-order-management/purchase-order-module.md` — primary carmen/docs source for the PO module business analysis, GRN integration, and the receipt-state transitions.
