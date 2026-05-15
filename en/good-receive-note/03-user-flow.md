---
title: Good Receive Note (GRN) — User Flow
description: Document lifecycle and persona-specific flow files for good-receive-note.
published: true
date: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# Good Receive Note (GRN) — User Flow

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `good-receive-note` module. A Good Receive Note (GRN) is the document that records the **physical receipt of goods** from a vendor — a header row in `tb_good_received_note` together with one or more `tb_good_received_note_detail` lines and their child `tb_good_received_note_detail_item` receipt-event rows. A GRN may be raised against an upstream Purchase Order (`doc_type = purchase_order`, the standard path) or as a manual receipt with no PO (`doc_type = manual`, e.g. ad-hoc / emergency purchases). The GRN is the **central anchor of the three-way match** in procure-to-pay: until a GRN commits, no inventory is incremented and no AP liability is raised; once committed, the source PO line's `received_qty` advances, the FIFO / average-cost layer is written, and the GRN becomes the evidence document that the vendor invoice is matched against.

Section 2 below is the **global state machine** — the canonical list of legal transitions across the four values of `enum_good_received_note_status` (`draft`, `saved`, `committed`, `voided`), independent of who acts. Each per-persona file (linked from Section 3) describes that persona's *path through* the state machine — their entry point, the actions available to them, the decision branches they face, and the handoff that ends their involvement. Section 4 then summarises the cross-persona handoffs that stitch the individual paths together. Read this overview first to anchor the lifecycle, then drill into the persona file that matches your role.

## 2. Document Lifecycle

The GRN document status is stored on `tb_good_received_note.doc_status` and constrained to the four values declared in `enum_good_received_note_status`: `draft` (initial editable state, no stock or GL impact), `saved` (line entry complete and saved for review, still editable, still no stock or GL impact), `committed` (single posting event has fired — inventory incremented, cost layers written, PO line advanced, document locked), and `voided` (administratively cancelled with no inventory or GL impact, or post-commit reversed via the elevated path). The transitions below cover the legal moves between them; everything else is rejected by the workflow engine. Receipt-driven downstream effects (`sent → partial → completed` on the source PO, FIFO / average-cost layer creation in [[costing]]) fire on the `saved → committed` transition only — see [02-business-rules.md](./02-business-rules.md) Section 5 for posting rules.

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create (against PO) | `draft` | Receiver | `doc_type = purchase_order`; source PO has `po_status ∈ {sent, partial}` and at least one line with pending qty; header fields populated from the PO snapshot (`vendor_id`, `currency_id`, `exchange_rate`). |
| `(none)` | create (manual) | `draft` | Receiver | `doc_type = manual`; vendor / currency / receipt date entered directly; no `purchase_order_detail_id` written on any line. |
| `draft` | save (edit) | `draft` | Receiver (owner) | Header and line validation rules in [02-business-rules.md](./02-business-rules.md) Section 2 pass at save time (header rules) or warn-only (line rules); document remains editable. |
| `draft` | save for review | `saved` | Receiver (owner) | All line-level rules `GRN_VAL_006`–`GRN_VAL_010` pass; receipt events recorded on every line; document is now visible to Inventory Manager and Finance for review. |
| `saved` | resume edit | `saved` | Receiver (owner) | Document still uncommitted; edits are written in-place; remains in `saved`. |
| `saved` | commit | `committed` | Inventory Manager (and Receiver subset where RBAC permits) | All commit-time rules pass (`GRN_VAL_011`–`GRN_VAL_014`): at least one detail_item, lot data present on inventory transactions for inventory items, PO status valid, extra costs allocated. **Triggers inventory increment, cost-layer write, PO line `received_qty` advance, AP accrual.** |
| `saved` | batch commit | `committed` | Inventory Manager | End-of-shift commit of multiple `saved` GRNs in one transaction; each GRN evaluated against the same commit-time rule set; partial-batch failure rolls back only the failing GRN. |
| `draft` | cancel (void pre-commit) | `voided` | Receiver (own draft), Inventory Manager | Reason text required; no inventory or GL impact; document terminates. |
| `saved` | cancel (void pre-commit) | `voided` | Receiver (own document), Inventory Manager | Reason text required; no inventory or GL impact; document terminates. |
| `committed` | void (post-commit reversal) | `voided` | Inventory Manager + Finance (elevated co-authorisation), System Administrator | Reason text required; **must trigger compensating reversal of inventory transaction, cost-layer reversal, PO line `received_qty` decrement, and reversing AP entry**. Typically handled via a credit-note workflow against the GRN. |
| `saved` | auto-commit (scheduled) | `committed` | System Administrator (scheduled job) | End-of-period sweep covers stale `saved` GRNs older than the tenant grace window; same commit-time rule set applies; failures are logged and routed to Inventory Manager for manual resolution. |
| `voided` | (no further action) | `voided` | — | Terminal state. The voided document is retained for audit; any subsequent receipt must be raised as a new GRN. |
| `committed` | (no further action) | `committed` | — | Terminal state for the receipt path. Corrections require a `tb_credit_note` against this GRN or a compensating adjustment in [[inventory-adjustment]]; the GRN itself remains locked. |

## 3. Persona Index

Each persona below has a dedicated drill-down file describing their entry point, primary flow, decision branches, and exit point. Slugs match the persona role; clicking the link opens the per-persona view.

- [Receiver](./03-user-flow-receiver.md) — Receiver / Store Keeper (and the Inventory Manager subset that performs commit). Creates the GRN at the dock against a PO or manually, counts and inspects the goods, records lot / expiry data (via the linked inventory transaction, not directly on the GRN line), saves for review, and — when authorised — commits the document to post inventory and raise AP.
- [Purchaser](./03-user-flow-purchaser.md) — Owner of the upstream PO. Reviews receiving information once a GRN is `saved` or `committed`, investigates qty / price / quality variance flagged by the Receiver, coordinates resolution with the vendor (short-ship, substitution, return). The Department Manager reviews cost-centre variance on the same flagged GRNs.
- [Finance](./03-user-flow-finance.md) — Finance Officer / AP + Finance Manager. Runs the three-way match (PO ↔ GRN ↔ invoice) on `committed` GRNs, allocates extra costs (freight, duty, landed-cost components), posts the AP liability, manages FX revaluation, and handles period close.
- [Audit / Config](./03-user-flow-audit-config.md) — System Administrator (lot-number format configuration, RBAC for commit / void authority, integration to ERP / GL) and Auditor (read-only review of GRN history, commit events, and post-commit reversals).

## 4. Cross-Persona Handoffs

The table below captures the moments where the GRN moves from one persona's responsibility to another's. Each handoff is anchored to the document state at the point of transfer.

| From persona | Trigger | To persona | Document state at handoff |
| ------------ | ------- | ---------- | ------------------------- |
| Receiver | Save for review (commit-ready) | Inventory Manager | `saved` (line data complete; awaiting commit) |
| Receiver / Inventory Manager | Commit posted | Finance | `committed` (inventory incremented, AP accrual raised, ready for three-way match) |
| Receiver | Save with variance flagged on line | Purchaser, Inventory Manager | `saved` (variance comment written; awaiting vendor coordination) |
| Inventory Manager | Commit with variance flagged on line | Purchaser | `committed` (variance recorded; vendor follow-up needed but inventory already posted) |
| Finance | Three-way match discrepancy (price / qty mismatch with invoice) | Purchaser | `committed` (GRN unchanged; resolution may require credit note or post-commit reversal) |
| Inventory Manager + Finance | Post-commit reversal authorised | Receiver (to raise replacement GRN if needed) | `voided` (with reversing inventory transaction and AP entry recorded) |
| System Administrator | Scheduled auto-commit sweep runs | Finance, Inventory Manager | `committed` (stale `saved` GRNs swept; exceptions routed back to Inventory Manager) |
| System Administrator | Lot-format / RBAC / integration change applied | All personas | (no document state change; new rules apply prospectively to subsequent GRNs) |

## 5. References

- `../carmen/docs/good-recive-note-managment/GRN-User-Experience.md` — carmen/docs user-experience source: persona descriptions and main user flow (note: legacy 5-state model `DRAFT / PENDING_APPROVAL / APPROVED / REJECTED / CANCELLED` is **not** canonical here; this page follows the Prisma 4-state enum).
- `../carmen/docs/good-recive-note-managment/GRN-User-Flow-Diagram.md` — carmen/docs flow diagrams (lifecycle, integration, mobile); referenced for shape only, status values realigned to the Prisma enum.
- `../carmen/docs/good-recive-note-managment/GRN-Overview.md` — carmen/docs module overview: purpose, scope, audience, integration points.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_good_received_note_status` (the four-state enum used in Section 2) and the carmen/docs divergences (Section 5 of the data model).
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — posting effects and authorization gates referenced by each row of Section 2.
- Related modules: [[purchase-order]] (upstream source; commit advances PO `received_qty` and may flip PO status `sent → partial → completed`), [[inventory]] (downstream — inventory transactions are where lot, expiry, and cost-layer data live), [[costing]] (FIFO / average-cost layer creation on commit), [[inventory-adjustment]] (post-commit corrections), [[vendor-pricelist]] (price-variance check against GRN unit price).
