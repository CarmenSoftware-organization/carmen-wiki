---
title: Purchase Order — User Flow — Vendor
description: Vendor's flow within the purchase-order module — external party (no system login); receives PO, acknowledges, fulfils, invoices.
published: true
date: 2026-07-29T04:45:21.000Z
tags: purchase-order, user-flow, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — User Flow — Vendor

> **At a Glance**
> **Persona:** Vendor (external — no Carmen login) &nbsp;·&nbsp; **Module:** [purchase-order](/en/inventory/purchase-order) &nbsp;·&nbsp; **Workflow stages:** sent (touch points) → partial / completed / voided &nbsp;·&nbsp; **Key permissions:** none direct — events recorded by Purchaser / Receiver / Finance / PM on vendor's behalf
> **What this persona does:** Receives the transmitted PO, acknowledges, fulfils delivery, and issues invoice — every system effect captured by an internal persona.

## 1. Role in This Module

The **Vendor** is an **external party with no Carmen system login**. The vendor receives the transmitted PO and fulfils the agreed delivery — the confirmed system-side effect of this is the **Receiver**'s GRN posting, which flips `po_status` to `partial` or `completed` via `PO_POST_006` / `PO_POST_007`. When the PO is transmitted on final approval the system state moves to `sent` (`PO_POST_004`). **Unconfirmed this pass:** whether the vendor's acknowledgement is captured anywhere (comment, portal callback, or otherwise), and whether any vendor-invoice / three-way-match feature exists downstream of receipt — a repo-wide search for `three-way`, `vendor_invoice`, and `tb_invoice` found no matches in either the frontend or backend. Treat the acknowledgement and invoice/AP steps below as documented design intent carried over from `carmen/docs`, not confirmed live behavior; see [03-user-flow-finance.md](./03-user-flow-finance.md) for the fuller correction.

### Workflow position (Vendor touch points highlighted)

```mermaid
graph LR
    sent(("sent")) -->|"PO transmitted<br/>(channel: email / EDI / portal)"| vendor["Vendor receives PO"]:::current
    vendor -.->|"Acknowledges (unconfirmed)"| sent
    vendor -->|"Ships goods"| recv["Physical delivery"]:::current
    recv -->|"Receiver posts GRN"| partial(("partial"))
    recv -->|"Receiver posts GRN"| completed(("completed"))
    vendor -.->|"Issues invoice (unconfirmed feature)"| inv["? no invoice/AP code found"]
    sent -.->|"Cancel (not 'decline→void')"| closed(("closed"))
    classDef current fill:#1a56db,color:#fff,stroke:#1a56db;
```

### Permission Matrix — Vendor Event × System Effect (recorded by internal persona, where confirmed)

The Vendor has **no direct write access** in Carmen. The table below maps each vendor-side event to what actually happens on the PO side, flagging what is confirmed vs. unconfirmed.

| Vendor event | System surface | `po_status` effect |
|---|---|---|
| Acknowledges PO | **Unconfirmed** — no specific comment/portal-callback code was located this pass | Presumed none; `po_status` stays `sent` if it happens at all |
| Ships partial qty | Receiver's GRN posting | `sent → partial` (`PO_POST_006`) |
| Ships full / final balance | Receiver's GRN posting | `sent → completed` or `partial → completed` (`PO_POST_007`) |
| Declines / vendor can no longer fulfil | **Cancel** (`{draft, in_progress, sent} → closed`) or **Close** (`{sent, partial, in_progress} → closed`) | `→ closed`, remainder written to `cancelled_qty` — **not** `voided`; there is no path from `sent` to `voided` in current source |
| Delivers wrong item / over qty | Receiver (refuses at dock) | none — escalates via comment |
| Delivers quality-failed goods | Receiver records a lower `received_qty` than ordered and notes the rejection in a free-text GRN comment — there is no separate acceptance-quantity field anywhere in the GRN or PO schema (confirmed absent repo-wide) | per `PO_POST_006` / `PO_POST_007` |
| Issues invoice | **Not implemented** — no invoice-capture screen or AP-posting code exists in current source | none |

## 2. Entry Point and Primary Flow

**Entry point:** Vendor receives the transmitted PO through the channel configured on the tenant — email PDF, EDI feed, or vendor portal link. The transmission writes `tb_purchase_order.email` and `approval_date`, and the PO is at `po_status = sent`.

**Primary flow (conceptual — confirmed system effects only):**

1. **Acknowledge receipt of the PO** (unconfirmed whether Carmen records this at all).
2. **Prepare and ship the goods against the agreed delivery date.** **System effect:** none — the physical movement is invisible to Carmen until the Receiver opens it at the dock.
3. **Deliver the goods to the receiving location.** **System effect:** none directly — the **Receiver** persona raises the GRN in the downstream [good-receive-note](/en/inventory/good-receive-note) module, which actually flips `po_status` (`sent → partial` or `sent → completed`).
4. **Issue the invoice** — **not implemented** in current source. See [03-user-flow-finance.md](./03-user-flow-finance.md) for the full correction on why no invoice / AP-matching feature was found.

## 3. Decision Branches

- **If the vendor can no longer fulfil the PO after transmission** (price disagreement, stock-out, lead-time impossible): there is no "decline → void" path from `sent` in current source. The PO is ended via **Cancel** or **Close**, both landing on `closed` with the remainder written to `cancelled_qty` — not `voided` (which is only reachable from `in_progress` via reject).
- **If the vendor partial-ships** (only some of the ordered quantity is delivered now, balance to follow): the **Receiver** posts a partial GRN — `received_qty < order_qty − cancelled_qty` on the affected lines — which flips `po_status` to `partial` (`PO_POST_006`). Subsequent shipments are captured by further GRN posts until the balance is cleared (`partial → completed`, `PO_POST_007`) or the remaining balance is written off as `cancelled_qty` via **Close** (`partial → closed`, `PO_POST_011`).
- **If the vendor sends the wrong item, wrong quantity over, or substandard quality**: vendor's discrepancy is detected at the dock. **System effect:** the **Receiver** records the discrepancy on the GRN and the **Purchaser** is notified via comment to initiate a return / replacement with the vendor. The PO does not auto-correct; any agreed write-off goes to `cancelled_qty` on the affected lines.

## 4. Exit Point / Handoffs

The vendor's involvement on a given PO ends at **physical delivery** (confirmed) — invoice issuance is documented design intent, not a confirmed system interaction. From that point the document state on Carmen is one of:

- `sent` — PO transmitted but no GRN posted yet (vendor has not delivered, or delivery is in transit).
- `partial` — Receiver has posted at least one GRN but the PO still has open balance on one or more lines.
- `completed` — Receiver has cleared every line via GRN; the PO has reached the terminal receipt state.
- `closed` — PO was cancelled or closed post-transmission (vendor could not fulfil, or material amendment forced re-issue) — reachable via **Cancel** or **Close**, not `voided`.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — global PO state machine and cross-persona handoff table.
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — internal persona that transmits the PO and runs the amendment loop on vendor's behalf.
- Sibling: [03-user-flow-receiver.md](./03-user-flow-receiver.md) — downstream internal persona that physically accepts the vendor's delivery and posts the GRN that drives `sent → partial → completed`.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — documents why no invoice / three-way-match feature was confirmed in current source.
- Related: [good-receive-note](/en/inventory/good-receive-note) — downstream module that records the vendor's physical delivery and drives the receipt-state transitions on the PO.
- `../carmen/docs/purchase-order-management/purchase-order-module.md` — primary carmen/docs source for the PO module business analysis and transmission flow; treat its three-way-match description as design intent, not verified current behavior.
