---
title: Purchase Order — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for purchase-order.
published: true
date: '2026-09-22T18:00:00.000Z'
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

> **Executable coverage (e2e, `../carmen-inventory-frontend-e2e/` @ 809d8e3, 2026-09-20):** the Playwright suite is the executable spec — this page does not mirror it. Catalogs: `docs/user-stories/401-po.md` (60 cases — spec `tests/401-po.spec.ts`), `docs/user-stories/402-po-purchaser-journey.md` (32 cases — `tests/402-po-purchaser-journey.spec.ts`), `docs/user-stories/403-po-approver-journey.md` (19 cases — `tests/403-po-approver-journey.spec.ts`), `docs/user-stories/201-my-approvals.md` (20 cases — `tests/201-my-approvals.spec.ts`). Gap reports (cases the specs do **not** cover): `docs/test-cases/gaps/401-po-create-flows-gap.md` (29), `gaps/402-po-purchaser-journey-gap.md` (39), `gaps/403-po-approver-journey-gap.md` (49), `gaps/201-my-approvals-gap.md` (34). Credit-note: `docs/user-stories/601-cn.md` (124 cases, `tests/601-cn.spec.ts` — 82 skipped, ~6 real oracles per `gaps/601-cn-gap.md`, 65 gap cases) and `602-cn-reason` (18 / 27). **Known spec lag vs source HEAD:** the 402/403 specs still look for a **Send to Vendor** button and a `SENT` status; at HEAD the button is **Send Email** and the statuses are `approved` → `sent_or_print` (2026-09-14). The FE approve-dialog copy still reads "Once approved, the PO will be sent to the vendor" (`messages/en.json` L3899) although approval no longer transmits.

This page is the **overview entry point** for the test-scenario set of the `purchase-order` module. The PO lifecycle spans six personas — Purchaser, Procurement Manager, Vendor, Receiver, Finance, and Audit / Config — and test coverage is split accordingly: each persona has a dedicated file (linked in Section 3) that enumerates that persona's functional, authorization, validation, edge, and golden-journey scenarios. This overview file gives the global picture: who is in scope, what each persona's tests cover at the headline level, the cross-persona handoff scenarios that stitch the individual journeys into a complete end-to-end flow, and the mapping from each scenario back to the Playwright spec files that exercise it.

Scope of testing on the PO module covers three broad areas: **functional coverage** of every action available on the PO list, detail, create paths (Blank, From Price List, From PR page), edit mode, the `POST /verify` dry-run, and the post-approval toolbar (Send Email → `sent_or_print`, Close, Cancel); **RBAC / authorization** of who can perform each action at each state (creator edit on draft, approver-only stage actions on `in_progress`, owner-only removal of drafts, read-only from `approved` onward); and **edge cases** around empty data, no-permission users, save-without-items, one-location-per-line payloads, FOC ordered vs received, and dynamic skip when seed data is absent. A prior version of this page also listed "three-way match rules at PO ↔ GRN ↔ invoice handoff" as in scope; no invoice/AP-matching feature was found in current source (see [03-user-flow-finance.md](./03-user-flow-finance.md)), so that item is removed here.

## 2. Personas in Scope

- **Purchaser** — Creates POs (blank, from price list, from PR), edits drafts, submits for approval, transmits to vendor, manages amendments and close-out. Owns 24+ scenarios across list, create, detail, edit, post-approval, and golden journey.
- **Procurement Manager** — Acts as the FC approver in seeded data. Owns the My-Approvals dashboard, item-level mark (Approve / Review / Reject), document-level Approve / Send Back / Reject flows, and final-stage transmission to vendor.
- **Vendor** — External party. No system login and no in-system test coverage; documented for cross-persona scenarios (transmission, acknowledgement, fulfilment, decline) and to set expectations for downstream personas.
- **Receiver** — Posts GRN line by line against an `approved` / `sent_or_print` PO. Drives the `→ partial → completed` receipt-state transitions. No dedicated E2E spec yet — partial / final receipt behaviour is exercised through the cross-persona scenarios in Section 4 and the GRN suite (`tests/501-*`).
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
| X-PO-01 | Full happy path (from PR) | Purchaser → Procurement Manager (→ `approved`) → Purchaser (Send Email → `sent_or_print`) → Vendor → Receiver | Approved PR exists; BU email profile configured | `completed` (every line received; `tb_activity` has one `email_sent`) |
| X-PO-02 | Manual PO (no PR linkage) | Purchaser → Procurement Manager → Purchaser (Send Email) → Vendor → Receiver | Vendor in catalogue; pricelist optional; no source PR | `completed` (manual flow; no PR consumed; no GRN label on the PO lines because `pr_details = []`) |
| X-PO-03 | Partial receipt then final balance | Purchaser → Procurement Manager → Purchaser (Send Email) → Vendor → Receiver (partial GRN) → Receiver (second GRN) | PO `sent_or_print`; vendor delivers in two shipments | `completed` via `partial` (state crosses `sent_or_print → partial → completed`) |
| X-PO-03b | Goods arrive before the email | Purchaser → Procurement Manager (→ `approved`) → Receiver (GRN) → Purchaser (Send Email afterwards) | PO `approved`, never emailed | `partial` / `completed` straight from `approved` (`findOnePoForGrn` accepts `approved`); the later Send Email only logs — `markPoAsSent` matches `approved` only, so the status stays as the GRN left it |
| X-PO-04 | ~~Three-way match quantity discrepancy~~ — removed | — | No invoice/AP-matching feature was found in current source (see [04-test-scenarios-finance.md](./04-test-scenarios-finance.md)) | n/a |
| X-PO-05 | Change after approval | Purchaser (Cancel + new PO, or Close after receipt) | PO `approved` / `sent_or_print`; vendor agrees a change | No in-place amendment exists (`PO_VAL_016`): `closed` + fresh PO for material changes; `closed` with remainder in `cancelled_qty` for short supply |
| X-PO-06 | Rejection at an approval stage | Purchaser → Procurement Manager (reject) | PO `in_progress`; reason optional | `voided` (direct, terminal; workflow terminated) |
| X-PO-07 | Cancel before any GRN posted | Purchaser (cancel) | PO `draft`, `in_progress`, `approved`, or `sent_or_print`; no GRN against any line | `closed` — every line `cancelled_qty = order_qty − 0`; there is no separate "void" action distinct from reject, and reject only reaches `voided` from `in_progress` |
| X-PO-08 | Vendor cannot fulfil after transmission | Purchaser → Procurement Manager → Purchaser (Send Email) → Vendor (cannot fulfil) | PO `sent_or_print` | `closed` via **Cancel** or **Close** — not `voided` (no path from `sent_or_print` to `voided` in current source) |
| X-PO-08b | Email bounces | Purchaser (Send Email) | PO `approved`; vendor address invalid | `{ sent: false, rejected[] }` with HTTP 200; PO stays `approved`; `tb_activity` `email_sent` still written; re-send after fixing the address moves it to `sent_or_print` |
| X-PO-09 | Close partial PO (vendor cannot supply remainder) | Purchaser → Procurement Manager → Vendor → Receiver (partial GRN) → Inventory Manager (close) | PO `partial`; outstanding balance treated as cancelled | `closed` (remaining qty written as `cancelled_qty`) |
| X-PO-10 | Send-back during approval (item-level Review) | Purchaser → Procurement Manager (Send Back) → Purchaser (revise + re-submit) → Procurement Manager (approve) | PO `in_progress`; one or more line items marked Review | `approved` (after revise + re-approve); `po_status` stays `in_progress` throughout the send-back itself; re-submit is accepted because `last_action = reviewed`; `po_no` unchanged |
| X-PO-11 | Swipe-approve a batch (mobile) | Procurement Manager (`POST /swipe-approve`) | Several `in_progress` POs at the Manager's stage | Per-PO `success` / `message`; final-stage POs land on `approved`; a `purchase`-stage PO in the batch is refused without failing the others |

## 5. E2E Test Mapping

Three Playwright specs exist for the PO module under `../carmen-inventory-frontend-e2e/tests/` (plus `201-my-approvals.spec.ts` for the shared approval queue and `601-cn` / `602-cn-reason` for Credit Note). Only the Purchaser and Procurement Manager (FC Approver) personas have dedicated specs today. Vendor, Receiver, Finance, and Audit / Config persona files note "no dedicated E2E spec yet — see shared `401-po.spec.ts` for general PO list coverage" and rely on the cross-persona scenarios in Section 4 to anchor expected behaviour for downstream automation. Case counts below are from `docs/user-stories/*.md`; the `gaps/` twins list what is still uncovered.

### 5.1 `401-po.spec.ts` — General / shared coverage (60 cases; gap report `gaps/401-po-create-flows-gap.md`, 29)

Mixed-persona spec running both `purchase@blueledgers.com` (Purchaser) and `requestor@blueledgers.com` (no-PO-permission negative cases). Covers:

- TC-PO-010001 — Create PO from approved PR (happy path)
- TC-PO-010003 — Edge case when no approved PRs exist
- TC-PO-010004 — Negative: invalid vendor assignment
- List-view fixtures, search, filter, sort scenarios used by all personas
- Backend / time-based scenarios marked `SKIP_NOTE_BACKEND` / `SKIP_NOTE_TIME` (documented but not executable through the UI)

Cross-persona coverage: X-PO-02 (manual PO entry point), X-PO-01 (PR-sourced PO entry point), general list/search/filter scenarios used by every downstream persona.

### 5.2 `402-po-purchaser-journey.spec.ts` — Purchaser persona (32 cases; gap report `gaps/402-po-purchaser-journey-gap.md`, 39)

Runs as `purchase@blueledgers.com`. Sourced from `docs/persona-doc/Purchase Order/Purchaser/INDEX.md`. Covers Steps 1–5 plus a Golden Journey (TC-PO-060101 through TC-PO-060901):

- Step 1 — PO list (load, tab switch, filter, search, sort)
- Step 2 — Create PO via Blank / From Price List / From PR wizards
- Step 3 — PO detail loads (Draft) with header + items + Item Details panel
- Step 4 — Edit mode (modify qty, add line, cancel edit, submit Draft, delete in-progress)
- Step 5 — Post-approval ("Send to Vendor" — at HEAD the button is **Send Email** and success means `approved → sent_or_print`; Close with received items; Close without received items). TC-PO-060501/060502 self-skip when the button label is not found, so they currently report skipped rather than failed against HEAD.
- Golden Journey TC-PO-060901 — full create → submit → FC approve (cross-context, lands on `approved`) → Send to Vendor (Send Email)

Cross-persona coverage: X-PO-01 (happy path PR-sourced), X-PO-02 (manual flow), X-PO-05 (amendment via edit mode), X-PO-07 (Close-without-received-items path, landing on `closed`), X-PO-09 (close partial).

### 5.3 `403-po-approver-journey.spec.ts` — Procurement Manager (FC Approver) persona (19 cases; gap report `gaps/403-po-approver-journey-gap.md`, 49)

Runs as `fc@blueledgers.com`; opens `/procurement/my-approvals` (falls back to the PR route), which at HEAD is the unified `GET /api/my-pending` queue. Sourced from `docs/persona-doc/Purchase Order/Approver/INDEX.md`. Covers Steps 1–3 plus a Golden Journey (TC-PO-070101 through TC-PO-070901):

- Step 1 — My Approval dashboard (load, PO filter tab, row click to detail)
- Step 2 — PO detail (FC view) — header read-only, Edit + Comment visible, status badge `IN PROGRESS`
- Step 3 — Approval actions: item-level mark (Approve / Review / Reject) + document-level Approve / Send Back / Reject + edit-mode cancel
- Golden Journey TC-PO-070901 — full open → edit → mark all approved → document approve → hard assertion is a badge matching `/approved|sent/i`. **Re-read 2026-09-22:** the persisted status after final approval is now `approved` (a real enum member since 2026-09-14), so the regex matches the `APPROVED` badge; it would also match `SENT OR PRINT` once the Purchaser emails the PO.

Cross-persona coverage: X-PO-01 / X-PO-02 (approval leg), X-PO-06 (rejection), X-PO-10 (Send-Back during approval).

## 6. References

- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/403-po-approver-journey.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/201-my-approvals.spec.ts`, `tests/601-cn.spec.ts`, `tests/602-cn-reason.spec.ts`
- `../carmen-inventory-frontend-e2e/docs/user-stories/{401-po,402-po-purchaser-journey,403-po-approver-journey,201-my-approvals,601-cn,602-cn-reason}.md` and `docs/test-cases/gaps/{401-po-create-flows,402-po-purchaser-journey,403-po-approver-journey,201-my-approvals,601-cn,602-cn-reason}-gap.md`; `docs/test-cases/COVERAGE.md` rows `/procurement/purchase-order`, `/procurement/approval`, `/procurement/credit-note`
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 (handoff source)
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 (posting rules — the three-way-match rules there are marked not implemented)
