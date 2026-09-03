---
title: Purchase Order — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for purchase-order.
published: true
date: 2026-07-15T12:00:00.000Z
tags: purchase-order, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Test Scenarios

> **At a Glance**
> **Module:** [purchase-order](/en/inventory/purchase-order) &nbsp;·&nbsp; **Total scenarios:** ~10 cross-persona + per-persona drill-downs across all personas &nbsp;·&nbsp; **Personas covered:** Purchaser, Procurement Manager, Vendor, Receiver, Finance, Audit / Config
> **Run order:** Audit / Config setup → primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**

## 1. Overview

This page is the **overview entry point** for the test-scenario set of the `purchase-order` module. The PO lifecycle spans six personas — Purchaser, Procurement Manager, Vendor, Receiver, Finance, and Audit / Config — and test coverage is split accordingly: each persona has a dedicated file (linked in Section 3) that enumerates that persona's functional, authorization, validation, edge, and golden-journey scenarios. This overview file gives the global picture: who is in scope, what each persona's tests cover at the headline level, the cross-persona handoff scenarios that stitch the individual journeys into a complete end-to-end flow, and the mapping from each scenario back to the Playwright spec files that exercise it.

Scope of testing on the PO module covers three broad areas: **functional coverage** of every action available on the PO list, detail, create wizards (Blank, From Price List, From PR), edit mode, and post-approval toolbar; **RBAC / authorization** of who can perform each action at each state (Purchaser-only edit on draft, approver-only stage actions on `in_progress`, read-only for Sent/Completed); and **edge cases** around empty data, no-permission users, save-without-items, dynamic skip when seed data is absent. A prior version of this page also listed "three-way match rules at PO ↔ GRN ↔ invoice handoff" as in scope; no invoice/AP-matching feature was found in current source (see [03-user-flow-finance.md](./03-user-flow-finance.md)), so that item is removed here.

## 2. Personas in Scope

- **Purchaser** — Creates POs (blank, from price list, from PR), edits drafts, submits for approval, transmits to vendor, manages amendments and close-out. Owns 24+ scenarios across list, create, detail, edit, post-approval, and golden journey.
- **Procurement Manager** — Acts as the FC approver in seeded data. Owns the My-Approvals dashboard, item-level mark (Approve / Review / Reject), document-level Approve / Send Back / Reject flows, and final-stage transmission to vendor.
- **Vendor** — External party. No system login and no in-system test coverage; documented for cross-persona scenarios (transmission, acknowledgement, fulfilment, decline) and to set expectations for downstream personas.
- **Receiver** — Posts GRN line by line against a Sent PO. Drives the `sent → partial → completed` receipt-state transitions. No dedicated E2E spec yet — partial / final receipt behaviour is exercised through the cross-persona scenarios in Section 4.
- **Finance** — Named in legacy design docs as a three-way-match / AP owner; **unconfirmed** in current source. No invoice-capture screen, AP-posting endpoint, or dedicated spec file exists — see [04-test-scenarios-finance.md](./04-test-scenarios-finance.md) for the correction.
- **Audit / Config** — Auditor (read-only review of activity log) and System Administrator (generic workflow-stage / numbering configuration shared across document types, not PO-specific). No dedicated audit-workspace or PO-specific configuration-workbench route was confirmed — see [04-test-scenarios-audit-config.md](./04-test-scenarios-audit-config.md).

## 3. Persona Test Files

- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Procurement Manager scenarios](./04-test-scenarios-procurement-manager.md)
- [Vendor scenarios](./04-test-scenarios-vendor.md)
- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios

The scenarios below trace the PO across multiple personas. Each row anchors the handoff sequence to the document state at the boundary and the expected end state. They are derived from the handoff table in [03-user-flow.md](./03-user-flow.md) Section 4.

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| X-PO-01 | Full happy path (from PR) | Purchaser → Procurement Manager → Vendor → Receiver | Approved PR exists; vendor reachable | `completed` (every line received) |
| X-PO-02 | Manual PO (no PR linkage) | Purchaser → Procurement Manager → Vendor → Receiver | Vendor in catalogue; pricelist optional; no source PR | `completed` (manual flow; no PR consumed) |
| X-PO-03 | Partial receipt then final balance | Purchaser → Procurement Manager → Vendor → Receiver (partial GRN) → Receiver (second GRN) | PO `sent`; vendor delivers in two shipments | `completed` via `partial` (state crosses `sent → partial → completed`) |
| X-PO-04 | ~~Three-way match quantity discrepancy~~ — removed | — | No invoice/AP-matching feature was found in current source (see [04-test-scenarios-finance.md](./04-test-scenarios-finance.md)) | n/a |
| X-PO-05 | Amendment cycle on Sent PO | Purchaser → Procurement Manager (approve amendment) → Vendor | PO `sent`; vendor accepts amendment | PO `sent` with revision history (`cancelled_qty` / note only, per `PO_VAL_016`) |
| X-PO-06 | Rejection at an approval stage | Purchaser → Procurement Manager (reject) | PO `in_progress`; reason optional | `voided` (direct, terminal; workflow terminated) |
| X-PO-07 | Cancel before any GRN posted | Purchaser (cancel) | PO `draft`, `in_progress`, or `sent`; no GRN against any line | `closed` — corrected from a prior "void mid-flight" framing; there is no separate "void" action distinct from reject, and reject only reaches `voided` from `in_progress` |
| X-PO-08 | Vendor cannot fulfil after transmission | Purchaser → Procurement Manager → Vendor (cannot fulfil) | PO `sent` | `closed` via **Cancel** or **Close** — not `voided` (no path from `sent` to `voided` in current source) |
| X-PO-09 | Close partial PO (vendor cannot supply remainder) | Purchaser → Procurement Manager → Vendor → Receiver (partial GRN) → Inventory Manager (close) | PO `partial`; outstanding balance treated as cancelled | `closed` (remaining qty written as `cancelled_qty`) |
| X-PO-10 | Send-back during approval (item-level Review) | Purchaser → Procurement Manager (Send Back) → Purchaser (revise) → Procurement Manager (approve) | PO `in_progress`; one or more line items marked Review | `sent` (after revise + re-approve); `po_status` stays `in_progress` throughout the send-back itself, corrected from a prior "returns to draft" framing |

## 5. E2E Test Mapping

Three Playwright specs exist for the PO module under `../carmen-inventory-frontend-e2e/tests/`. Only the Purchaser and Procurement Manager (FC Approver) personas have dedicated specs today. Vendor, Receiver, Finance, and Audit / Config persona files note "no dedicated E2E spec yet — see shared `401-po.spec.ts` for general PO list coverage" and rely on the cross-persona scenarios in Section 4 to anchor expected behaviour for downstream automation.

### 5.1 `401-po.spec.ts` — General / shared coverage

Mixed-persona spec running both `purchase@blueledgers.com` (Purchaser) and `requestor@blueledgers.com` (no-PO-permission negative cases). Covers:

- TC-PO-010001 — Create PO from approved PR (happy path)
- TC-PO-010003 — Edge case when no approved PRs exist
- TC-PO-010004 — Negative: invalid vendor assignment
- List-view fixtures, search, filter, sort scenarios used by all personas
- Backend / time-based scenarios marked `SKIP_NOTE_BACKEND` / `SKIP_NOTE_TIME` (documented but not executable through the UI)

Cross-persona coverage: X-PO-02 (manual PO entry point), X-PO-01 (PR-sourced PO entry point), general list/search/filter scenarios used by every downstream persona.

### 5.2 `402-po-purchaser-journey.spec.ts` — Purchaser persona

Runs as `purchase@blueledgers.com`. Sourced from `docs/persona-doc/Purchase Order/Purchaser/INDEX.md`. Covers Steps 1–5 plus a Golden Journey (TC-PO-060101 through TC-PO-060901):

- Step 1 — PO list (load, tab switch, filter, search, sort)
- Step 2 — Create PO via Blank / From Price List / From PR wizards
- Step 3 — PO detail loads (Draft) with header + items + Item Details panel
- Step 4 — Edit mode (modify qty, add line, cancel edit, submit Draft, delete in-progress)
- Step 5 — Post-approval (Send to Vendor, Close with received items, Close without received items)
- Golden Journey TC-PO-060901 — full create → submit → FC approve (cross-context) → Send to Vendor

Cross-persona coverage: X-PO-01 (happy path PR-sourced), X-PO-02 (manual flow), X-PO-05 (amendment via edit mode), X-PO-07 (Close-without-received-items path, landing on `closed`), X-PO-09 (close partial).

### 5.3 `403-po-approver-journey.spec.ts` — Procurement Manager (FC Approver) persona

Runs as `fc@blueledgers.com`. Sourced from `docs/persona-doc/Purchase Order/Approver/INDEX.md`. Covers Steps 1–3 plus a Golden Journey (TC-PO-070101 through TC-PO-070901):

- Step 1 — My Approval dashboard (load, PO filter tab, row click to detail)
- Step 2 — PO detail (FC view) — header read-only, Edit + Comment visible, status badge `IN PROGRESS`
- Step 3 — Approval actions: item-level mark (Approve / Review / Reject) + document-level Approve / Send Back / Reject + edit-mode cancel
- Golden Journey TC-PO-070901 — full open → edit → mark all approved → document approve → hard assertion is a badge matching `/approved|sent/i` (the real persisted status is `sent`; no distinct `approved` status exists in `enum_purchase_order_doc_status` — the test's regex is simply tolerant of either word)

Cross-persona coverage: X-PO-01 / X-PO-02 (approval leg), X-PO-06 (rejection), X-PO-10 (Send-Back during approval).

## 6. References

- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/403-po-approver-journey.spec.ts`
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 (handoff source)
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 (posting rules — the three-way-match rules there are marked not implemented)
