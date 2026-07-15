---
title: Purchase Request — Test Scenarios — Purchaser
description: Purchaser's test cases (happy path, permission, validation, edge cases) for purchase-request.
published: true
date: 2026-07-15T10:20:00.000Z
tags: purchase-request, test-scenarios, purchaser, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Test Scenarios — Purchaser

> **At a Glance**
> **Persona:** Purchaser (Purchasing Staff — `enum_stage_role = purchase` stage in the PR's own chain, plus operator of the separate Convert-to-PO dialog) &nbsp;·&nbsp; **Module:** [purchase-request](/en/inventory/purchase-request) &nbsp;·&nbsp; **Scenarios:** ~18
> **Categories:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** `tests/304-pr-purchaser-journey.spec.ts` (`TC-PR-0701xx`–`TC-PR-0709xx`, primary source), plus purchase-role blocks in `tests/301-pr.spec.ts` (`TC-PR-470xxx` edit pricing, `TC-PR-490xxx` submit after allocation, `TC-PR-600xxx` reject, `TC-PR-410xxx` convert to PO) in `../carmen-inventory-frontend-e2e/`

This page captures the test scenarios the Purchaser persona directly drives in the `purchase-request` module, split across the two things they actually do in the current build: (1) act at the `purchase`-role stage inside the PR's own approval chain — edit vendor / unit price / discount / tax profile, run **Auto Allocate**, then bulk Approve / Reject / Send for Review / Split, exactly like any other stage — and (2) separately, once a PR is `approved`, run the **Convert to PO** dialog from the Purchase Order module. See [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) for the full walkthrough of both.

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | Expected |
| - | -------- | ------------- | ----- | -------- |
| PUR-HP-01 | List loads, My Pending default; PR at Purchase stage visible | Purchaser logged in; a PR was submitted and HOD-approved so it now sits at a stage assigned to the Purchaser | Sidebar → Purchase Request. Confirm URL and My Pending tab (`TC-PR-070101`). | List loads at `/procurement/purchase-request`; My Pending tab selected when present. |
| PUR-HP-02 | Detail loads with Items tab default; no standalone Approve/Reject buttons | PR seeded at the Purchase stage (`submitPRAsRequestor` + `approveAsHOD`) | Open the PR detail page (`TC-PR-070201`, `TC-PR-070203`). | Detail URL loads; Items tab selected when present; no standalone header-level Approve / Reject / Send-back buttons are visible (BRD discrepancy — bulk toolbar only). |
| PUR-HP-03 | Enter Edit Mode → vendor / price / discount / tax become editable | Same PR, Edit button visible | Click **Edit**; check Vendor, Unit Price, Discount, Tax Profile inputs on the first line (`TC-PR-070301`–`TC-PR-070305`). | Vendor, Unit Price, Discount, Tax Profile inputs are editable; `Approved Qty` stays disabled/read-only (`TC-PR-070306`) because the HOD stage already set it. |
| PUR-HP-04 | Auto Allocate fills vendor + price via scoring lookup | Edit Mode active, at least one line with product / unit / currency set | Click **Auto Allocate** (`TC-PR-070307`). | Request completes and the page stays on the PR detail URL; vendor, price, pricelist reference, and tax populate from the price-compare lookup for lines that resolved a match. |
| PUR-HP-05 | Save edits persists vendor/price changes | Edit Mode with a changed Unit Price | Fill Unit Price, click **Save Draft** (`TC-PR-070309`). | Form returns to view mode; Edit button visible again; the new price is retained. |
| PUR-HP-06 | Bulk Approve advances the PR | Edit Mode, all rows selected | Select all, click bulk **Approve**, confirm (`TC-PR-070401`, golden flow `TC-PR-070901`). | PR stays on its detail URL; stage advances (or `pr_status` flips `in_progress → approved` per `PR_POST_005` if this was the final stage). |
| PUR-HP-07 | Bulk Reject with reason | Edit Mode, all rows selected | Select all, click bulk **Reject**, enter a reason, confirm (`TC-PR-070402`; also `TC-PR-600001` via the single-PR Reject button). | `pr_status` flips to `voided` (terminal); reason and rejecting user recorded on the audit trail. |
| PUR-HP-08 | Bulk Send for Review returns to a prior stage | Edit Mode, all rows selected | Select all, click bulk **Send for Review**, enter a reason and target stage, confirm (`TC-PR-070403`). | `workflow_current_stage` moves back one step; if the target is the create stage, `pr_status` returns to `draft`. |
| PUR-HP-09 | Bulk Split — accept some lines, reject others | Edit Mode, PR with 2+ lines | Select all, click bulk **Split** (`TC-PR-070404`). | Split UI opens; rejected lines are flagged `current_stage_status = rejected` and excluded from further processing, accepted lines continue. |
| PUR-HP-10 | Convert an approved PR to a PO | One or more PRs at `pr_status = approved` | From the Purchase Order module, open **Convert to PO**; pick a workflow; tick the approved PR(s); review the auto-grouped draft PO(s); confirm (`TC-PR-410001`, and the `group-pr` / `confirm-pr` endpoints). | One `tb_purchase_order` is created per `(vendor, delivery_date, currency)` group; source PR(s) whose lines are now all bridged flip from `approved` to `completed` (`PR_POST_007`). |

## 2. Permission / Authorization

| # | Scenario | Expected behaviour (allow/deny + reason) |
| - | -------- | --------------------------------------- |
| PUR-PERM-01 | Purchaser opens a PR currently at a stage assigned to them | **Allow** view + Edit Mode + bulk toolbar actions. `PR_AUTH_002` is satisfied because the signed-in user is in `user_action.execute[]` for the current stage. |
| PUR-PERM-02 | Purchaser opens a PR at a non-Purchase stage (e.g. still at HOD) | **Deny edit.** No Edit button is shown, or Edit Mode's vendor field stays disabled (`TC-PR-070405`) — the Purchaser is not the current stage's assigned user. |
| PUR-PERM-03 | Purchaser attempts to edit `approved_qty` | **Deny.** The field is read-only for the `purchase`-role stage; it was set by the Approver chain per `PR_VAL_013`. |
| PUR-PERM-04 | Non-purchase user (Requestor / HOD) attempts the Convert-to-PO dialog | **Deny.** The dialog is scoped to purchase-order create permissions; a Requestor cannot open it (see the parallel "Convert to PO — Permission denial" block in `301-pr.spec.ts`). |
| PUR-PERM-05 | Purchaser attempts to convert a PR still `in_progress` | **Deny — wrong status.** The PR-for-PO list only returns PRs at `pr_status = approved`; an in-progress PR does not appear as a selectable candidate. |

## 3. Validation / Error

| # | Scenario | Trigger | Expected error |
| - | -------- | ------- | -------------- |
| PUR-VAL-01 | Submit-equivalent bulk action with a missing unit price | Bulk Approve attempted while a line has no `unit_price` / `pricelist_price` set (`TC-PR-490002`) | Reject — inline validation error surfaces; the Purchaser fills the price and retries. |
| PUR-VAL-02 | Bulk action with an incomplete vendor selection | Bulk Approve attempted while a line has `vendor_id IS NULL` (`TC-PR-490003`) | Reject — inline validation error; the Purchaser runs Auto Allocate or picks a vendor manually and retries. |
| PUR-VAL-03 | Reject with too-short a reason | Bulk/Reject reason shorter than the minimum length (`TC-PR-600002`) | Reject — error message that the reason is too short; Confirm stays blocked until corrected. |
| PUR-VAL-04 | Convert to PO with an invalid vendor on a group | Convert-to-PO attempted where a selected PR's line resolves to an invalid/unmatched vendor (`TC-PR-410002`) | Reject — error surfaces in the dialog; no PO is created; source PR `pr_status` unchanged. |

## 4. Edge Cases

| # | Scenario | Condition | Expected |
| - | -------- | --------- | -------- |
| PUR-EDGE-01 | Multiple line items — pricing edits are independent per row | PR seeded with 2 lines | Setting Unit Price on row 0 does not affect row 1's value (`TC-PR-070308`). |
| PUR-EDGE-02 | Cancel edits discards changes | Edit Mode with an unsaved price change | Click **Cancel** — form returns to view mode; the change is not persisted (`TC-PR-070310`). |
| PUR-EDGE-03 | Convert to PO when the PR has no delivery date | PR approved with a line missing `delivery_date` (`TC-PR-410003`) | PO is created using a default delivery date rather than blocking the conversion. |
| PUR-EDGE-04 | PR already fully converted does not reappear in the PR-for-PO list | Source PR previously flipped to `completed` via `PR_POST_007` | The PR is absent from the Convert-to-PO Step 1 list; it cannot be selected again. |

## 5. References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — happy-path source for Section 1 above; describes the `purchase`-stage edit + bulk-decide flow and the separate Convert-to-PO dialog
- Business rules: [02-business-rules.md](./02-business-rules.md) Section 5 (`PR_POST_005` final approve → `approved`, `PR_POST_007` convert to PO → `completed`)
- Data model: [01-data-model.md](./01-data-model.md) Section 2 — bridge table `tb_purchase_order_detail_tb_purchase_request_detail`
- E2E: `../carmen-inventory-frontend-e2e/tests/304-pr-purchaser-journey.spec.ts` (primary, persona-journey — `purchaseTest` fixture) and `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` (purchase-role blocks: "PR — Edit pricing", "PR — Submit after vendor allocation", "PR — Reject by Purchase Staff", "PR — Convert to PO — Purchase Staff"). PR Template coverage adjacent to Purchaser scope is in `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts`.
- Cross-link: [purchase-order](/en/inventory/purchase-order) — downstream module that receives the converted POs
- Cross-link: [vendor-pricelist](/en/inventory/vendor-pricelist) — pricelist source for Auto Allocate
