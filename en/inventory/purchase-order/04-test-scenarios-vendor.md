---
title: Purchase Order — Test Scenarios — Vendor
description: Vendor's test cases (happy path, edge cases) for purchase-order. External party — no in-system permission scenarios; no confirmed invoice/AP-matching feature.
published: true
date: 2026-07-15T12:00:00.000Z
tags: purchase-order, test-scenarios, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Test Scenarios — Vendor

> **At a Glance**
> **Persona:** Vendor (external party — no Carmen login) &nbsp;·&nbsp; **Module:** [purchase-order](/en/inventory/purchase-order) &nbsp;·&nbsp; **Scenarios:** ~8
> **Categories:** Happy Path &nbsp;·&nbsp; Permission (N/A) &nbsp;·&nbsp; Edge Case
> **E2E coverage:** no dedicated vendor spec (no Carmen login); vendor-driven events exercised indirectly via `tests/401-po.spec.ts` (TC-PO-030001..030004 send-to-vendor, TC-PO-340001..340003 GRN-sync) in `../carmen-inventory-frontend-e2e/`

> ⚠️ **Corrected this pass.** The previous version of this page included an invoice-issuance happy path (VND-HP-05) and a full Validation section (VND-VAL-01 through VND-VAL-05) built entirely around a three-way-match / AP-invoice feature. No invoice-capture screen, AP-posting endpoint, or match algorithm was found anywhere in current source (see [03-user-flow-finance.md](./03-user-flow-finance.md) for the searches run) — those scenarios are removed. The "vendor declines / voids" edge cases are also corrected: there is no path from `sent` to `voided` in current source; ending a `sent` PO uses **Cancel** or **Close**, both landing on `closed`.

This page captures the test scenarios that exercise the **Vendor** persona's interaction with the `purchase-order` module. The Vendor is an **external party with no Carmen system login** ([03-user-flow-vendor.md](./03-user-flow-vendor.md) Section 1) — the confirmed system-side effect of a vendor action is the **Receiver**'s GRN posting, which drives `PO_POST_006` / `PO_POST_007`. Whether vendor acknowledgement is captured anywhere in current source was not confirmed. Because the vendor has no in-system role, this file has no meaningful Permission / Authorization section and is shorter than the other persona scenario files.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| VND-HP-01 | Receive a transmitted PO (email PDF or vendor-portal callback) | PO at `po_status = sent` after the final-stage approve call; `tb_purchase_order.email` set and `approval_date = now()` | 1. Carmen transmits the PO via the configured channel (email PDF, EDI feed, or vendor-portal link) as part of the same final-stage approve call — there is no separate manual "Send to Vendor" step. 2. Vendor's mailbox / portal receives the document referencing `po_no`, lines, qty, price, delivery date, and payment terms. | The PO is delivered to the vendor; `po_status` remains `sent`. **Unconfirmed:** whether Carmen records any acknowledgement of receipt. |
| VND-HP-02 | Full shipment on the agreed delivery date (Receiver records matching GRN) | PO at `po_status = sent` with line `L1 : order_qty = 10`, `received_qty = 0`, `cancelled_qty = 0`; vendor dispatches 10 units against the agreed `delivery_date` | 1. Vendor's logistics partner delivers the full 10 units to the receiving location with a delivery note referencing `po_no`. 2. Receiver opens the PO in [good-receive-note](/en/inventory/good-receive-note) and posts a GRN of qty 10 against `L1`. | GRN posting flips `po_status` from `sent → completed` via `PO_POST_007` because `received_qty + cancelled_qty = order_qty` on every line (`L1`: `10 + 0 = 10`); `tb_purchase_order_detail.received_qty = 10` on `L1`; inventory on-hand is incremented in the [inventory](/en/inventory/inventory) module per `PO_XMOD_008`. |
| VND-HP-03 | Partial shipment then second delivery (Receiver records partial then full) | PO at `po_status = sent` with `L1 : order_qty = 10`; vendor can supply 6 today and 4 next week | 1. Vendor ships 6 units with the delivery note marked partial. 2. Receiver posts GRN #1 of qty 6 against `L1`. 3. Vendor ships the remaining 4 units a week later. 4. Receiver posts GRN #2 of qty 4 against `L1`. | After GRN #1: `received_qty = 6`, `po_status` flips `sent → partial` per `PO_POST_006` because `received_qty < order_qty − cancelled_qty` on `L1`; after GRN #2: `received_qty = 10`, `po_status` flips `partial → completed` per `PO_POST_007` because every line satisfies `received_qty + cancelled_qty = order_qty`. |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour |
| - | -------- | ------------------ |
| VND-PERM-01 | Vendor is an external party with no system login; in-system permissions are N/A. | N/A — there is no Carmen login for the vendor and no UI surface to test. Every effect of a vendor action that reaches the system does so through the Receiver's GRN posting (`PO_POST_006` / `PO_POST_007`). Where a vendor portal is configured, it is a separate concern from the PO module's RBAC matrix (`PO_AUTH_001`–`PO_AUTH_011`). |

## 3. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| VND-EDGE-01 | Vendor can no longer fulfil the PO after transmission | PO at `po_status = sent`; a stock-out / price-disagreement means the vendor cannot deliver | The PO is ended via **Cancel** (`{draft, in_progress, sent} → closed`) or **Close** (`{sent, partial, in_progress} → closed`) — both write the remainder to `cancelled_qty`. **Corrected this pass:** a prior version of this scenario described escalation to a Manager-only "void" reaching `sent → voided`; no such transition exists in current source. |
| VND-EDGE-02 | Vendor partial-ships wrong items (Receiver records discrepancy) | PO line `L1 : order_qty = 10` (product `P1`); vendor delivers 8 units of `P1` and 2 units of an unrelated product `P_wrong` (substitution / packing error) | Receiver opens the GRN against `L1` and records 8 received against `L1` (flipping `po_status → partial` per `PO_POST_006`) plus a variance comment in `tb_purchase_order_comment` referencing `P_wrong`. The wrong-item delivery does **not** post to inventory under `L1`; any agreed write-off of the remaining 2 units of `P1` is written to `cancelled_qty` on `L1` via **Close**. |
| VND-EDGE-03 | Vendor goes out of business mid-PO | PO at `po_status = partial` with `received_qty = 6` on `L1 : order_qty = 10`; vendor ceases trading before delivering the balance of 4 units | **Close** (`partial → closed`, `PO_AUTH_008`, `PO_POST_011`) writes the remaining 4 units to `cancelled_qty`; the 6 units already received remain on `tb_purchase_order_detail.received_qty`. **Corrected this pass:** a prior version of this scenario used a Procurement-Manager-only "Void" (`partial → voided`); no code path reaches `voided` from `partial` — only Close (→ `closed`) is available from this status. |

## 4. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — cross-persona handoffs that involve the vendor's actions but are driven by internal personas: `X-PO-01` (full happy path from PR through transmission to receipt), `X-PO-05` (amendment cycle on Sent PO).
- User flow: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — source for Section 1 above; documents what is confirmed vs. unconfirmed about vendor-side events.
- Sibling: [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md) — internal persona that transmits the PO and runs the amendment loop on the vendor's behalf.
- Sibling: [04-test-scenarios-procurement-manager.md](./04-test-scenarios-procurement-manager.md) — internal persona with Close authority used in VND-EDGE-01 and VND-EDGE-03.
- Sibling (downstream): the **Receiver** persona's test scenarios cover the GRN postings that flip `po_status` per `PO_POST_006` / `PO_POST_007` in response to vendor deliveries.
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) / [04-test-scenarios-finance.md](./04-test-scenarios-finance.md) — the correction explaining why no invoice / three-way-match scenarios appear on this page.
- Business rules being verified: [02-business-rules.md](./02-business-rules.md) Section 6 — `PO_XMOD_003` (GRN may only be created against `po_status ∈ {sent, partial}`), `PO_XMOD_004` (over-receipt tolerance referenced in VND-EDGE-02); Section 5 — `PO_POST_004` (transmit on final approval), `PO_POST_006` / `PO_POST_007` (GRN-driven receipt transitions), `PO_POST_010`/`PO_POST_010b` / `PO_POST_011` (cancel / reject / close, corrected).
- E2E: `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts` — shared / mixed-persona spec; there is **no dedicated vendor E2E** because the vendor has no Carmen login.
- Cross-link: [good-receive-note](/en/inventory/good-receive-note) — downstream module that records the vendor's physical delivery and drives the receipt-state transitions on the PO; primary surface for VND-HP-02, VND-HP-03, and the wrong-item discrepancy in VND-EDGE-02.
