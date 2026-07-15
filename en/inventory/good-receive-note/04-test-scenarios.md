---
title: Good Receive Note (GRN) — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for good-receive-note.
published: true
date: 2026-07-15T00:00:00.000Z
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — Test Scenarios

> **At a Glance**
> **Module:** [good-receive-note](/en/inventory/good-receive-note) &nbsp;·&nbsp; **Personas covered:** Receiver, Purchaser, Finance (correction page), Audit / Config (correction page)
> **Run order:** primary persona happy paths → cross-persona scenarios
> **Each persona's drill-down is `04-test-scenarios-<role>.md`**
> **Corrected this pass (2026-07-15):** the previous version of this page described commit as the posting event, a three-way-match / AP-posting integration layer, and a batch-commit / scheduled-auto-commit mechanism. None of these match current source — see [02-business-rules.md](./02-business-rules.md) §1 and the corrections inline below.

## 1. Overview

This page is the **overview entry point** for the test-scenarios set of the `good-receive-note` module. It groups GRN coverage by persona (Receiver, Purchaser, Finance, Audit / Config), inventories the per-persona test files, captures the cross-persona handoff scenarios that stitch individual paths together, and maps scenarios back to the canonical Playwright spec [`501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts). **Unconfirmed / removed this pass:** "three-way-match outcomes" and a per-line `accepted_qty` quality-inspection trace were listed as in-scope coverage areas in a prior version of this page — neither feature was found in current source (see [01-data-model.md](./01-data-model.md) and [03-user-flow-finance.md](./03-user-flow-finance.md)).

`501-grn.spec.ts` is the **only** Playwright E2E file for the GRN module; its individual test bodies are mostly best-effort (`.catch(() => {})` on missing UI, few hard assertions), so treat a mapped `TC-GRN-*` id as "a describe block with this name exists", not as proof the described behavior is asserted end-to-end.

## 2. Personas in Scope

- **Receiver**: Receiving / warehouse staff who physically take delivery, raise the GRN in `draft`, and save it for review (`draft → saved`) — the step that posts inventory and advances the PO.
- **Purchaser**: Procurement staff who own the upstream PO and review receiving variance; vendor-side coordination happens off-document.
- **Finance**: **Correction page** — no three-way-match, AP-posting, or Finance-role feature was confirmed for this module.
- **Audit / Config**: **Correction page** — no dedicated GRN configuration console or lot-recall tool was confirmed for this module.

## 3. Persona Test Files

- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Finance scenarios](./04-test-scenarios-finance.md) — correction page.
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md) — correction page.

## 4. Cross-Persona / Handoff Scenarios

The table below spans a handoff recorded in [03-user-flow.md](./03-user-flow.md) Section 4. **Corrected this pass:** rows for "extra-cost allocation review by Finance", "batch commit", "post-commit void with elevated co-auth", and "scheduled auto-commit sweep" are removed — none matched current source (no batch-commit endpoint, no scheduled job, no Finance-role code, and the `/void` endpoint has no `doc_status` precondition beyond "not already voided", so there is no elevated reversal path to test).

| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
| 1 | Full happy path against PO | Receiver → Inventory Manager | Source PO with `po_status ∈ {sent, partial}` and at least one line pending; vendor / currency / exchange rate available; receiver has create-GRN permission. | GRN `saved` (inventory incremented, FIFO / avg-cost layer written, PO line `received_qty` advanced — `po_status` toward `partial` or `completed` — all at save); Inventory Manager subsequently commits (`saved → committed`), which locks the document with no further effect found. |
| 2 | Manual GRN (no PO) | Receiver → Inventory Manager | `doc_type = manual` permitted by tenant config; vendor active; no upstream PO. | GRN `saved` with `doc_type = manual` and no `purchase_order_detail_id` on any line; inventory incremented at save; commit locks the document. |
| 3 | Partial receipt across two GRNs | Receiver → Inventory Manager → Receiver → Inventory Manager | Source PO line has pending qty larger than the first delivery; tenant permits partial receipt. | First GRN `saved` and PO line → `partial` with `received_qty < ordered_qty`; second GRN later `saved` and PO line → `completed`; both GRNs are subsequently committed independently to lock them. |
| 4 | Short receipt flagged for vendor follow-up | Receiver → Purchaser | Delivery contains a short-shipped line; receiver records `received_qty < order_qty` with a variance comment on the line. | GRN `saved` (inventory incremented for the actual `received_qty` only); Purchaser reviews and coordinates vendor follow-up off-document (chase, replacement PO) — no dedicated in-app resolution workflow was found. |
| 5 | Extra-cost entry on the GRN | Receiver | Receiver records freight / duty / clearance against `tb_extra_cost` with a distribution-mode tag (`manual`, `by_value`, or `by_qty`); GRN still `draft`. | Extra-cost row persists with the tag; **unconfirmed** whether it is actually split across lines or fed into the cost-layer calculation at save — see [04-test-scenarios-finance.md](./04-test-scenarios-finance.md). |
| 6 | Multi-PO consolidation into one GRN | Receiver | Same vendor and currency across two open POs (multi-PO wizard rejects a mixed-currency selection). | One GRN with lines spanning both POs; save advances `received_qty` on both POs in one transaction. |

## 5. E2E Test Mapping

`501-grn.spec.ts` is the **only** Playwright E2E file for the GRN module. It is structured as a single file with multiple `describe` blocks per functional area; auth is multi-role through `createAuthTest`, with `purchase@blueledgers.com` for the happy / functional path and `requestor@blueledgers.com` for permission-denial cases.

| `501-grn.spec.ts` describe block (TC group) | Cross-persona scenarios covered (Section 4) |
| ------------------------------------------- | ------------------------------------------- |
| `GRN — List` (TC-GRN-010001–010004) | 1 (entry point for listing GRNs) |
| `GRN — Filter / Search` (TC-GRN-020001–020005) | 1 (vendor / invoice-number search) |
| `GRN — Create from Single PO` (TC-GRN-030001–030005) | 1, 3 (first leg of the happy path and partial receipt) |
| `GRN — Create from Multiple POs` (TC-GRN-040002–040004) | 6 (multi-PO consolidation) |
| `GRN — Manual creation` (TC-GRN-050001–050005) | 2 (manual GRN end-to-end entry point) |
| `GRN — Edit Header` (TC-GRN-060001–060005) | 1, 2 (header edits before save-for-review) |
| `GRN — Add Line Item` (TC-GRN-070001–070004) | 1, 2, 3 (line entry across PO and manual paths) |
| `GRN — Edit Line Item` (TC-GRN-080001–080005) | 4 (editing `received_qty` on a short-shipped line) |
| `GRN — Delete Line Item` (TC-GRN-090001+) | 1, 3 (line cleanup before save) |
| `GRN — Extra Costs` (TC-GRN-100001+) | 5 (extra-cost entry) |
| `GRN — Commit` (TC-GRN-110001+) | 1, 2, 3 (the save-then-commit path — note the describe block's own annotation text calls this "the canonical posting event", which this pass corrects: save is the posting event, commit only locks) |
| `GRN — Void` (TC-GRN-120001–120004) | Void from `draft` / `saved`. **Note:** `TC-GRN-120003`'s annotation describes voiding a `committed` GRN as reverting it to "RECEIVED" with reversed stock movements and a reversed Journal Voucher — this does not match the actual `voidGrnById()` code (which sets `doc_status = voided` with no reversal) and the test body itself asserts nothing; treat the annotation as aspirational, not confirmed behavior. |
| `GRN — Financial Summary` (TC-GRN-130001+) | 5 (read-only totals view; not a three-way-match input) |
| `GRN — Stock Movements` (TC-GRN-140001+) | 1 (inventory transactions written at save) |
| `GRN — Comments` (TC-GRN-150001+) | 4 (variance comments) |
| `GRN — Attachments` (TC-GRN-160001+) | 1 (packing-list evidence) |
| `GRN — Activity Log` (TC-GRN-170001+) | 1 (audit trail across save / commit / void) |
| `GRN — Bulk Approval` (TC-GRN-180001+) | **Unconfirmed** — this describe block's annotations describe a per-line "APPROVED" status that does not exist in the schema (`tb_good_received_note_detail_item` has no status column); the test bodies have no assertions. Not mapped to any scenario above. |
| `GRN — * — Permission denial` (all `requestor@blueledgers.com` blocks) | RBAC layer across every scenario; the two persona files in Section 3 catalogue the persona-specific denial paths. |

## 6. References

- [`../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts) — canonical Playwright E2E spec (multi-role auth, all `TC-GRN-*` groups).
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4 — cross-persona handoffs that drive the integration scenarios above; corrected this pass to remove the batch-commit / auto-commit / post-commit-reversal rows.
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — posting rules; corrected this pass to show save, not commit, as the posting event.
- Per-persona detail: [Receiver](./04-test-scenarios-receiver.md), [Purchaser](./04-test-scenarios-purchaser.md), [Finance](./04-test-scenarios-finance.md), [Audit / Config](./04-test-scenarios-audit-config.md).
