---
title: Purchase Request — Business Rules
description: Validation, calculation, authorization, and posting rules for purchase-request.
published: true
date: '2026-10-27T00:00:00.000Z'
tags: purchase-request, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Business Rules

> **At a Glance**
> **Rule families:** `PR_VAL_*` validation &nbsp;·&nbsp; `PR_AUTH_*` permission &nbsp;·&nbsp; `PR_CALC_*` calc &nbsp;·&nbsp; `PR_POST_*` posting
> **Rule count:** approximately 45 rules &nbsp;·&nbsp; **Re-verified 2026-10-27** (rule set first re-verified 2026-09-22; 2026-10 additions: `PR_VAL_019`, `PR_AUTH_009`–`PR_AUTH_011`) against `apps/micro-business/src/procurement/purchase-request/logic/purchase-request.validate.ts` (submit rules), `logic/verify/*` (pre-flight), `purchase-request.service.ts` (delete / status writes) — rules with no code path are now marked **unconfirmed** instead of being stated as fact
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Status lifecycle:** Section 5.1 (where present) carries the Live UI vs BRD discrepancy callouts

## 1. Overview

This page enumerates the rules that govern a Purchase Request (PR) end-to-end: how header and line fields are validated, how monetary totals are calculated from line entries up to the document roll-up, who can move a PR through its workflow chain, what side-effects happen on submit / approve / reject / delete / convert, and how PR interacts with the vendor-pricelist, inventory, and purchase-order modules. Rules are derived from `purchase-request-ba.md`, `PR-Technical-Specification.md`, and `PR-Module-Structure.md`, and aligned with the canonical Prisma entities documented in [01-data-model](/en/inventory/purchase-request/01-data-model) — specifically `tb_purchase_request`, `tb_purchase_request_detail`, `tb_purchase_request_comment`, `tb_purchase_request_detail_comment`, `tb_purchase_request_template`, and `tb_purchase_request_template_detail`.

The rules cover four governance surfaces. **Validation rules** fire at create / edit / submit time and guard field correctness, referential integrity, and cross-field consistency. **Calculation rules** define deterministic formulas for line and header totals, taxes, discounts, and base-currency conversions, all preserved at five decimals via Prisma `Decimal(15, 5)` / `Decimal(20, 5)`. **Authorization rules** describe who can act on the PR at each workflow stage and which actions (approve, reject, send-back, split-reject) are available. **Posting rules** describe the status transitions on `enum_purchase_request_doc_status` and the downstream effects (PO conversion bridge, audit-comment writes). Cross-module rules tie the PR to inventory, vendor-pricelist, and purchase-order. *(Budget soft-commitments — asserted in earlier revisions — have no code path anywhere in the backend, frontend or Bruno collections; every budget rule below is marked unconfirmed.)* Specific currency amounts in examples use `฿` (Thai Baht).

## 2. Validation Rules

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `PR_VAL_001` | `tb_purchase_request.pr_no` must be present and unique within the active (`deleted_at IS NULL`) set. Generated server-side in two steps: a **draft** is created with a placeholder `draft-{n}` from a per-BU counter (`nextDraftNo`, config key `pr_running_no`, advisory-locked — it replaced a random `draft-<hex>` in 2026-10), and the **first submit** swaps it for the real number issued by the running-code engine (`reserveDocumentNumbers`, type `PURCHASE-REQUEST`, dated by `pr_date` in the BU calendar; `purchase-request.service.ts:1062`). Duplicating a draft takes a new placeholder, duplicating a non-draft takes a real number (`:1582-1585`); the format is configured in [system-config/running-code](/en/inventory/system-config/running-code). | On create (header insert) | Reject with `"PR reference number is required and must be unique"`. Backed by `PR0_pr_no_u` unique index `(pr_no, deleted_at)`. |
| `PR_VAL_002` | `requestor_id` must reference an active user; `requestor_name` snapshot must be populated alongside it. | On create / on submit | Reject with `"Requestor is required"`. |
| `PR_VAL_003` | `department_id` must be set (`purchase-request.validate.ts:31-38`, `PR_ERROR.DEPARTMENT_REQUIRED`). The frontend also requires it before Save (`pr-form-schema.ts:128`). *Membership check ("requestor must belong to that department") — unconfirmed, no code path; delegation — unconfirmed, see `PR_AUTH_006`.* | On submit (server) / on save (client) | Reject with `"Department is required"`. |
| `PR_VAL_004` | `workflow_id` must be present (`validate.ts:13-20`, `PR_ERROR.WORKFLOW_REQUIRED`); the client only offers workflows the user can create under (`pr-new-content.tsx` / `pr-component.tsx` "noCreatableWorkflow" — the old `pr-form-actions.tsx` was removed in 2026-10, its buttons now live in the `FormToolbar` of `pr-header.tsx`). *A server-side check that the row is active with scope `purchase_request` — unconfirmed.* | On submit | Reject with `"Workflow is required before submitting PR"`. The selected `workflow_name` is snapshotted onto the header. |
| `PR_VAL_005` | `pr_date` must be present (`validate.ts:40-47`, `PR_ERROR.PR_DATE_REQUIRED`; create also throws `'PR date is required'`, `service.ts:940`). *"Not later than today" — unconfirmed, no code path.* | On create / on submit | Reject with `"PR date is required"`. |
| `PR_VAL_006` | At least one non-deleted `tb_purchase_request_detail` row must be attached. | On submit | Reject with `"A PR must contain at least one line item"`. |
| `PR_VAL_007` | Every detail line must reference a non-null `product_id` that resolves to an active row in `tb_product`. Service / free-text lines must still pick a product placeholder. | On line save / on submit | Reject with `"Product is required on every line"`. The DB enforces NOT NULL on `product_id`. |
| `PR_VAL_008` | **Submit-time only (2026-09).** A draft may be saved with `requested_qty = 0` (client schema `pr-form-schema.ts:52-57` is `min(0)`; commit `a848865f` "ปุ่ม Save ของเอกสารร่างไม่บังคับกรอกครบแล้ว"). At submit every line must either buy (`requested_qty > 0`) or receive free goods (`foc_qty > 0`); a line with both at zero fails `PR_ERROR.LINE_ORDERS_NOTHING`, a negative `requested_qty` fails `REQUESTED_QTY_INVALID`, `requested_unit_id` is required when buying and `foc_unit_id` when `foc_qty > 0` (`validate.ts:108-149`). The client pre-checks the same rule (`findRowsMissingQty`, toast "incompleteItems") before opening the submit dialog. `POST …/verify` with `verify_state = submit` additionally checks that each requested unit is an **order unit** of its product (`PR_ERROR` `001013`). | On submit | `"Detail line N: needs a requested_qty or a foc_qty"` / `"requested_qty must be positive"` / `"requested_unit_id is required"`. |
| `PR_VAL_009` | `delivery_date` is **required** on every line by the client schema (`pr-form-schema.ts:82`); lines pre-filled from a template or duplicate default to tomorrow (`freshItem`). *"On or after `pr_date`" — unconfirmed, no code path on either side.* | On save (client) | Client: `"required"` on the delivery-date cell. |
| `PR_VAL_010` | `location_id` on a line must reference an active `tb_location` of a type that can request stock. Per the unique index `PR1_purchase_request_product_location_dimension_u`, the combination `(purchase_request_id, product_id, location_id, dimension)` must be unique within the PR. | On line save | Reject duplicates with `"Same product cannot be requested twice for the same location and dimension"`. |
| `PR_VAL_011` | `currency_id` is required on every line by the client schema (`pr-form-schema.ts:71-74`) and, at the `purchase` stage, by the server-side approve check together with `vendor_id`, `pricelist_price > 0` and `tax_profile_id` (`pr-form-schema.ts` `superRefine`, `verify-approve.ts` purchase-role branch). `exchange_rate` defaults to `1`. *`exchange_rate > 0` and `exchange_rate_date ≤ pr_date` — unconfirmed, no code path.* | On save (client) / on purchase-stage approve | Client: `"required"` on currency; server: verify report lists each missing reference. |
| `PR_VAL_012` | **Line caps (2026-09-17).** A line's `discount_amount` may not exceed its sub-total and its `tax_amount` may not exceed its net amount (`PR_ERROR.DISCOUNT_EXCEEDS_LINE_AMOUNT` / `TAX_EXCEEDS_LINE_AMOUNT`, `common/verify/amount.check.ts`, applied by `findAmountIssues` in the purchase-role verify branch). Manual overrides set `is_tax_adjustment` / `is_discount_adjustment` to `true`. *A `0–100` percent range check — unconfirmed, no code path.* **Enforcement caveat:** the cap is evaluated by `POST …/verify`; the `approve` endpoint itself does not call `findPurchaseRequestApproveIssues` (`purchase-request.logic.ts:492`, inside `verify`, is the only caller), so a client that skips verify can still post an over-cap line. | On `verify` (`verify_state = approve`, `stage_role = purchase`) | Verify report: `error_code` per offending line. |
| `PR_VAL_013` | `approved_qty` may be `0` (the client schema is `min(0)`, `pr-form-schema.ts:68`) but **not negative**, and the approved unit must be an order unit of the product (`verify-approve.ts:173-182`, `PR_APPROVED_UNIT_CHECK`). *"≤ `requested_qty`" — unconfirmed, no code path on either side.* Same enforcement caveat as `PR_VAL_012`: checked by `verify`, not by `approve` itself. | On `verify` (`verify_state = approve`, `stage_role = approve`) | `"Detail line N: approved_qty cannot be negative"`. |
| `PR_VAL_014` | The user submitting the PR must have permission to act on the workflow's first `enum_stage_role = create` stage. | On submit | Reject with `"You are not authorised to submit purchase requests"`. |
| `PR_VAL_015` | **Unconfirmed — no code path.** A budget-availability check at submit was asserted in earlier revisions. `grep -ri budget` over the PR backend module, the gateway controller, the my-pending module and the PR frontend routes finds only an optional `budget_code?: string` on `purchase-request.interface.ts` and the sample reject message `"Budget exceeded for this period"`. | — | — |
| `PR_VAL_016` | Optimistic concurrency: `doc_version` on the row being updated must equal the value the client read. | On any update | Reject with `"Document was modified by another user; reload and retry"` and bump `doc_version` by 1 on successful write. |
| `PR_VAL_017` | **Pre-flight verification (2026-08-19).** `POST /:bu_code/purchase-requests/verify` with `{ verify_state: 'create' \| 'submit' \| 'approve', id?, body? }` evaluates every rule for that action without writing: `create` resolves every id in a create payload; `submit` runs `findPurchaseRequestSubmitIssues` plus the order-unit check on a stored PR; `approve` with `stage_role = purchase` checks references, adjustment flags and recalculates every amount from its inputs, with `stage_role = approve` checks `approved_qty` / approved unit. All issues are returned together (`{ id, verify_state, is_valid, errors: [{ error_code, message, field, detail }] }`); a failing PR still answers **200** with `is_valid: false`, 404 only for an unknown id. Note the live `submit` endpoint stops at the **first** issue (`validateBeforeSubmit`, `purchase-request.logic.ts:1131-1141`). | On demand | `PurchaseRequestVerifySwaggerDto`; Bruno `POST-verify-procurement-purchase-request.bru`. |
| `PR_VAL_018` | **Delete rules (2026-07-29).** Single and batch delete require `pr_status = draft` and document ownership (`created_by_id` or `requestor_id` equals the caller) unless the caller is a Backstage super-admin (`BackstageSuperAdminService`, renamed from the platform one in 2026-10). Batch delete validates every id first and returns `{ deleted[], blocked: [{ id, reason: 'not_found' \| 'not_draft' \| 'not_owner' }] }` (`purchase-request.service.ts:1753-1850`; single delete `:1676-1750`). Delete is a **soft delete** (`deleted_at`), never a status change. | On `DELETE …/:id`, `DELETE …/batch` | `"Only draft purchase requests can be deleted"`, `ERROR_CATALOG.PR_DELETE_FORBIDDEN`; a non-draft single delete answers `ERROR_CATALOG.PR_ONLY_DRAFT_DELETABLE`. |
| `PR_VAL_019` | **Quantity-unit conversion factors (2026-10).** Each of the three quantities on a line — requested, approved, FOC — has its own `*_unit_id` and `*_unit_conversion_factor`. On create / save the server resolves the factor for **all three roles** that carry a quantity (`resolveConversionFactors`, `purchase-request.conversion-factor.ts`; it replaced the FOC-only `resolveFocConversionFactors`): the product's `order_unit` conversion in `tb_unit_conversion` (`to_unit_qty / from_unit_qty`) wins, the product's inventory unit gets `1`, and only otherwise is the factor the client sent kept. A partial update merges the stored unit and quantity first, so editing only a quantity does not lose the factor. | On create / save | Factor and `*_base_qty` rewritten server-side. |

## 3. Calculation Rules

All monetary values are stored as `Decimal(20, 5)` on line columns and `Decimal(15, 5)` on header roll-ups and rates. Intermediate values are rounded to five decimal places before being used in subsequent steps (half-up rounding). Display layers may further truncate to two decimals per `PR_UI` rules but the persisted value retains five decimals.

### `PR_CALC_001` — Line subtotal (transaction currency)

```
sub_total_price = pricelist_price × approved_qty
```

If `approved_qty` is null prior to approval, the requestor's `requested_qty` is used in the live preview; persisted lines after approval use `approved_qty`.

### `PR_CALC_002` — Line discount amount

```
discount_amount =
  is_discount_adjustment ? <user override>
                         : round(sub_total_price × (discount_rate / 100), 5)
```

### `PR_CALC_003` — Line net amount

```
net_amount = sub_total_price − discount_amount
```

### `PR_CALC_004` — Line tax amount

```
tax_amount =
  is_tax_adjustment ? <user override>
                    : round(net_amount × (tax_rate / 100), 5)
```

### `PR_CALC_005` — Line total

```
total_price = net_amount + tax_amount
```

### `PR_CALC_006` — Base-currency conversion

```
base_price             = round(pricelist_price       × exchange_rate, 5)
base_sub_total_price   = round(base_price            × approved_qty, 5)
base_discount_amount   = round(discount_amount       × exchange_rate, 5)
base_net_amount        = base_sub_total_price − base_discount_amount
base_tax_amount        = round(tax_amount            × exchange_rate, 5)
base_total_price       = base_net_amount + base_tax_amount
```

`exchange_rate` is snapshotted on the line at submit (column `exchange_rate`, `Decimal(15, 5)`, default `1`); the rate is fixed for the life of the document — re-approving does **not** re-fetch the rate.

### `PR_CALC_007` — Header roll-up

```
tb_purchase_request.base_net_amount   = Σ tb_purchase_request_detail.base_net_amount
tb_purchase_request.base_total_amount = Σ tb_purchase_request_detail.base_total_price
```

Header subtotal / tax columns are not separately persisted in Prisma — they are derived in the API response from the line roll-ups when needed.

### `PR_CALC_008` — UoM conversion (qty triples)

```
requested_base_qty = round(requested_qty × requested_unit_conversion_factor, 5)
approved_base_qty  = round(approved_qty  × approved_unit_conversion_factor, 5)
foc_base_qty       = round(foc_qty       × foc_unit_conversion_factor, 5)
```

Where `*_unit_conversion_factor` is the multiplier from the line's UoM to the product's inventory base UoM (`inventory_unit_id`).

### Worked example (`฿`, base = THB)

PR line: 12 × bottle of cooking oil at pricelist `฿185.00000`/bottle. Discount `5%`. Tax `7%`. Transaction currency THB, `exchange_rate = 1.00000`.

```
sub_total_price       = 185.00000 × 12         = 2,220.00000
discount_amount       = 2,220.00000 × 0.05     =   111.00000
net_amount            = 2,220.00000 − 111.00000 = 2,109.00000
tax_amount            = 2,109.00000 × 0.07     =   147.63000
total_price           = 2,109.00000 + 147.63000 = 2,256.63000
base_total_price      = 2,256.63000 × 1.00000  = 2,256.63000  ฿
```

Cross-currency example: same line but priced in USD with `exchange_rate = 35.50000` (THB per USD), pricelist `$5.20000`/bottle:

```
sub_total_price       = 5.20000 × 12           =     62.40000  USD
total_price (USD)     = 62.40000 × 0.95 × 1.07 =     63.42960  USD
base_price            = 5.20000 × 35.50000     =    184.60000  ฿
base_sub_total_price  = 184.60000 × 12         =  2,215.20000  ฿
base_total_price (THB) ≈ 2,251.74180                          ฿
```

## 4. Authorization Rules

Stage role labels come from `enum_stage_role = { create, approve, purchase, issue, view_only }`. The four-stage default approval chain captured in `purchase-request-ba.md` is:

| Stage | Default role | Typical `enum_stage_role` | What this stage can do |
|-------|--------------|---------------------------|------------------------|
| 1 | Requestor / Department Head | `create` / `approve` | Submit / re-submit; approve at department level; reject; send back to drafter |
| 2 | Budget Controller | `approve` | Confirm budget; reject with reason; send back to Stage 1 |
| 3 | Finance | `approve` | Confirm financial impact; reject; send back to Stage 1 or Stage 2 |
| 4 | Procurement Manager | `purchase` | Final approval; allocate vendor; convert to PO; reject; send back |

Actual stages are configurable per organisation in `tb_workflow`; the chain a given PR follows is determined by the row referenced by `tb_purchase_request.workflow_id`. The four rows above are the concept-doc default, **not** roles the code knows: the only stage vocabulary is `enum_stage_role`, and no stage carries budget- or finance-specific logic (see `PR_VAL_015`).

- **`PR_AUTH_001`** — Only the requestor (`requestor_id == auth.user.id`) may edit a PR while `pr_status = draft`; other users have read-only access. *(An earlier revision of this rule also granted edit rights to "a user delegated by the requestor" — unconfirmed, see `PR_AUTH_006`.)*
- **`PR_AUTH_002`** — At each stage, only the users named in `tb_purchase_request.user_action.execute[]` may take an action. The list is recomputed on every stage transition from the stage's role / department / amount-threshold rules.
- **`PR_AUTH_003`** — Every approver has the bulk actions **Approve**, **Reject**, **Send for Review** (send-back, `last_action = reviewed`, target stage chosen from `GET …/:pr_id/previous-stages`) and **Split** (`POST …/:id/split` moves the selected lines into a new PR); individual lines can also be rejected so they remain on the document with `current_stage_status = rejected` and never reach PO conversion.
- **`PR_AUTH_004`** — Header-level **reject** terminates the chain immediately and moves `pr_status` to `voided` (`purchase-request.service.ts:2201` — the only write of that value). *(Budget soft-commitment release — unconfirmed, see `PR_VAL_015`.)*
- **`PR_AUTH_005`** — **Confirmed.** Amount thresholds drive which stages fire. The workflow assigned to the PR (`tb_workflow.data.routing_rules`) can carry per-stage routing rules that compare a condition field (`total_amount` — the sum of the PR's line `total_price`; also `department` or `category`) against a configured value using an operator (`eq`, `not_eq`, `gt`, `lt`, `gte`, `lte`, `in`, `between`) and, on match, either skip to a named target stage or jump to it — evaluated by the workflow engine on both submit and every approve action, so a threshold crossed by a mid-review `approved_qty` edit changes the *next* stage's routing before that stage is reached. Configured from the workflow's **Routing** panel in `/system-admin/workflow` (generic — shared by PR, PO, and SR workflows, not a PR-specific screen). Specific thresholds and target stages are configured per organisation/workflow; the source documentation does not fix specific numbers. **Nuance confirmed this pass:** a `category`-based routing rule would silently never match — none of the PR/PO/SR workflow mappers emit a document-level `category` field into `navigation_request_data`, and `evaluateCondition` in `workflows.navagation.service.ts` returns `false` (not an error) for a missing field. The engine also supports `in`/`not_eq` operators beyond the `wf-routing-constants.ts` UI's `eq`/`gt`/`lt`/`gte`/`lte`/`between` set, so a rule built via a direct API call (not the Routing panel) could use them even though the UI cannot configure them. Source: `workflows.navagation.service.ts` ~L455-456 (missing-field comment) and ~L498-500 (`in`/`not_eq` cases).
- **`PR_AUTH_006`** — **(Unconfirmed — no delegation code found.)** This rule previously asserted that an approver may temporarily delegate their stage to another user via the workflow engine, with the delegate inheriting approve / reject / send-back rights for a delegation window, `last_action_by_id` reflecting the delegate, and audit comments capturing the delegation source. A repo-wide search of the frontend (including the same workflow **Routing** panel that confirmed `PR_AUTH_005`) and the backend workflow orchestrator found no delegation, reassignment, proxy, or substitute-approver mechanism anywhere, generic or PR-specific — `routing_rules` only route the *document* between stages by amount/department/category, they do not hand off a stage to a different *user*. Treat delegation as unconfirmed design intent, not verified live behavior.
- **`PR_AUTH_007`** — **(Unconfirmed — no void endpoint.)** Earlier revisions asserted a Finance / system-admin **Void** available at any stage after submit. `purchase-requests.controller.ts` exposes no void route, `enum_purchase_request_doc_status.voided` is written only by `reject`, and the frontend PR form offers Edit / Save / Delete / Submit / Approve / Reject / Send Back only (`pr-header.tsx` `FormToolbar`, `workflow/pr-footer-action.tsx`). A `draft` is removed by **Delete** (soft delete, owner or super-admin — `PR_VAL_018`); a submitted PR can only be terminated by an approver's Reject.
- **`PR_AUTH_008`** — Conversion to PO is *intended* for the `purchase` role, but no permission is enforced on `group-pr` / `confirm-pr` or the Convert-to-PO dialog (see [03-user-flow-purchaser](./03-user-flow-purchaser.md)). Approved PRs sit in `approved` until a user creates the PO via the bridge `tb_purchase_order_detail_tb_purchase_request_detail`. **List visibility** is what the permission catalogue actually gates: `procurement.purchase_request.view` / `view_department` / `view_all` (`constant/permissions.ts`; backend `@Permission({ 'procurement.purchase_request': ['view'] })` on the list endpoints).
- **`PR_AUTH_009` — Row visibility (2026-10).** `procurement.purchase_request` `view_all` sees every PR; `view_department` sees the caller's department (a caller with no department row falls back to own PRs, never the whole BU — #811); `view` sees own PRs (`requestor_id`); a caller with none of the three gets an empty list; a BU `admin` role is unrestricted (`buildPurchaseRequestRowFilter`, `logic/purchase-request.row-filter.ts`). The **detail** read adds a participant clause — requestor, current-stage `user_action.execute`, or anyone in `workflow_history` — so approvers can open what they approve without a view action (`buildPurchaseRequestDetailFilter`, #812). A PR the caller may not see answers as not found.
- **`PR_AUTH_010` — Stage actions can be switched off (2026-10).** A stage with `stage_role` `approve`, `purchase` or `issue` may disable **approve**, **reject** or **send back** (`available_actions.<action>.is_active = false`). `approve`, `reject`, `review` and each id in `swipe-approve` / `swipe-reject` check it first (`checkStageActionAllowed`) and fail with `WORKFLOW_STAGE_ACTION_DISABLED`; stages with another role are never blocked. The detail exposes `stage_actions` so the UI hides the buttons; the UI is a convenience, the backend check is the rule.
- **`PR_AUTH_011` — Hidden prices (2026-10).** A stage may hide `price_per_unit` and/or `total_price` from its actors. For a non-draft PR and a caller listed in the current stage's `user_action.execute`, the response masks the matching keys to `null` (`hidden_fields` names the groups) and the write path (save, approve) drops every price / price-source key the caller sends, refuses new lines and header totals, and recomputes the line money from the stored row (`pr-price-mask.ts`, `pr-hidden-price-guard.ts`). The same mask applies to list rows, My Approval rows and the print / report payload (`starPrReportDetail`).

> ⚠️ **Discrepancy — bulk-toolbar vs row-level actions (BRD FR-PR-005A):** The BRD specifies per-row standalone **Approve / Reject / Send for Review** buttons in the PR list / detail header. The current live UI exposes these actions only as **bulk toolbar actions** inside Edit Mode (via the Select All dropdown → bulk action toolbar). Confirmed bulk actions: Approve, Reject, Send for Review (BRD "Return Selected"), Split. Standalone row-level buttons remain absent. Source: `Test_case/Purchase_Request/Approver/INDEX.md` (capture date 2026-04-19). Verification status: confirmed for HOD; assumed for FC / GM / Owner.

> ⚠️ **Discrepancy — Send-back disabled-button tooltip:** The Submit / Send-back buttons are disabled when pre-conditions are not met (`PR_VAL_004`–`PR_VAL_006`) but the live UI shows no tooltip explaining the disabled reason. Known usability gap captured in `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § 6.4.

## 5. Posting Rules

Status transitions are recorded on `tb_purchase_request.pr_status` (`enum_purchase_request_doc_status = { draft, in_progress, voided, approved, completed }`). Every transition writes both a header row in `workflow_history` (JSON timeline) and a `tb_purchase_request_comment` row with `type = system` for the audit trail.

- **`PR_POST_001` — Create.** New PR is inserted with `pr_status = draft`, `last_action = submitted` is **not** yet set, `workflow_current_stage` is the workflow's entry stage, and `base_*_amount` totals are zero until lines are added.
- **`PR_POST_002` — Submit.** Transition `draft → in_progress`. The system: (a) sets `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_*` to the requestor; (b) snapshots `workflow_name` from the chosen `tb_workflow`; (c) initialises `stages_status` per stage; (d) *budget soft-commitment — unconfirmed, no code path (`PR_VAL_015`)*; (e) inserts a `tb_purchase_request_comment` with `type = system` and the submit message; (f) notifies the users in `user_action.execute[]` of the first approval stage. BRD `FR-PR-005` sets the first-approver notification SLA at **5 minutes** from submit; the SLA is not yet verified against the live notification service.

> ⚠️ **Discrepancy — notification SLA unverified:** BRD `FR-PR-005` specifies a 5-minute email notification SLA for the first approver on submit. Not yet verified in the test environment because dispatch depends on the notification service availability. Source: `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § BR-06.

> ⚠️ **Discrepancy — budget check `warn` vs `block`:** BRD `FR-PR-004` makes the budget check configurable per organisation policy — either *warn* (allow submit with warning) or *block* (prevent submit when over budget). The current test account has zero unit prices on items (commitment = `฿0.00`) so the live behaviour for an over-budget submit is not observable. Source: `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § BR-09.
- **`PR_POST_003` — Send-back.** Transition `in_progress → in_progress` with `workflow_current_stage` moved back to the chosen target stage and `last_action = reviewed` (`review`, `purchase-request.service.ts:2053-2157`, only matches a PR that is already `in_progress` (`:2073`) and **never writes `pr_status`** — even when the target is the requestor's `create` stage the PR does **not** return to `draft`; the requestor edits it as an `in_progress` document at that stage). The send-back option can be switched off per stage (`PR_AUTH_010`). Notification is sent to the user at the new stage.
- **`PR_POST_004` — Approve (intermediate stage).** Updates `workflow_previous_stage`, `workflow_current_stage`, `workflow_next_stage`, `last_action = approved`, `stages_status` for the just-completed stage; appends `workflow_history`; recomputes `user_action.execute[]` for the next stage. `pr_status` stays `in_progress`.
- **`PR_POST_005` — Final approve.** When the last stage clears, `pr_status` flips from `in_progress` to `approved` (`purchase-request.service.ts:1932-1936`: `workflow_next_stage === '-'` gives `approved`, otherwise `in_progress`). The PR is now eligible for PO conversion (see [purchase-order](/en/inventory/purchase-order)). *(Soft-to-hard budget commitment — unconfirmed, `PR_VAL_015`.)*
- **`PR_POST_006` — Reject.** A header-level `reject` from any approver moves `pr_status` to `voided`, appends `workflow_history`, updates each line's `stages_status` / `history` / `current_stage_status`, and inserts a `type = system` comment with the reason (`purchase-request.service.ts:2159-2231`; the `voided` write is at `:2222`). Line-level reject (split) sets per-line `current_stage_status = rejected` but does not change `pr_status`. *An administrative void and a requestor "cancel to `voided`" — unconfirmed; drafts are soft-deleted (`PR_POST_009`), and `voided` has no other writer.*
- **`PR_POST_007` — Convert to PO.** When a procurement user creates a PO from one or more approved PRs, each affected `tb_purchase_request_detail` row gains a row in the bridge `tb_purchase_order_detail_tb_purchase_request_detail` linking it to the new PO line. Once **all** lines of the PR are either fully converted (sum of bridge-linked PO quantities equals `approved_base_qty`) or explicitly cancelled, the system flips `pr_status` from `approved` to `completed`. Partial conversion leaves the PR in `approved` with remaining open quantity until a subsequent PO consumes it.
- **`PR_POST_009` — Delete (draft only).** `DELETE …/:id` and `DELETE …/batch` stamp `deleted_at` on the header and every detail row and zero the header totals on batch delete (`purchase-request.service.ts:1812`); `pr_status` is untouched and the row disappears from every list and from `sys_v_my_pending`. See `PR_VAL_018` for who may delete.
- **`PR_POST_008` — Audit comments are immutable.** `tb_purchase_request_comment` rows with `type = system` cannot be edited after insert. User comments (`type = user`) may be soft-deleted (`deleted_at`) by their author but never hard-deleted; the soft-delete itself is captured by audit.

There are no stock-level postings from PR: the PR module is a procurement intent document and does not touch inventory balances. Stock movements occur downstream in [purchase-order](/en/inventory/purchase-order) and Good Receive Note ([good-receive-note](/en/inventory/good-receive-note)).

## 6. Cross-Module Rules

- **Budget** — **Unconfirmed — no code path.** `BudgetData.softCommitmentPR`, `availableBudget` and every other budget symbol asserted in earlier revisions come from `../carmen/docs/` only; nothing in `carmen-turborepo-backend`, `carmen-frontend` or the Bruno collections implements a budget module (`PR_VAL_015`).
- **Inventory** — The line capture UI reads from [inventory](/en/inventory/inventory) to display on-hand and on-order quantity (`pr-inventory-row.tsx`, fetched live, not cached — commit `4077b4ea`; shows **current** stock — an on-hand-at-document-date variant (`90018c6d`) was reverted for PR/PO in `8b6d7675`) and the last receiving info (`pr-last-receiving-info.tsx`); since 2026-09-17 the PR detail response itself carries `last_price` per line (`purchase-request.serializer.ts:106`) and the price-compare response carries `last_price` for the product. None of these values are persisted on `tb_purchase_request_detail`. The PR does **not** reserve or move inventory. *(Reorder level / average monthly usage in the PR grid — unconfirmed.)*
- **Vendor & vendor-pricelist** — Each detail line resolves an optional preferred vendor via the price-compare endpoint ([vendor-pricelist](/en/inventory/vendor-pricelist)) against product, requested unit, currency, date and `qty`, so the MOQ tier the quantity reaches is the one offered. The qty differs by caller: the client (Auto Allocate and the Price Comparison dialog) sends the **approved** quantity when set and the requested one otherwise (`resolveApprovedQty`, 2026-10), while the server-side auto price compare at submit sends `requested_qty ?? approved_qty` (`lookupPricelistForDetails`, `purchase-request.logic.ts:1183`). When price-compare returns no `selected` row, the server falls back to the product's latest real receipt — a GRN line in status `saved` or `committed` with `received_base_qty > 0` — priced as `base_sub_total_price ÷ received_base_qty × requested-unit factor ÷ line exchange rate` (`lookupLatestGrnPrice`, `:1250`; fixed 2026-10 so the price is in the line's own unit and currency); that fallback carries the GRN's vendor but no `pricelist_detail_id` / `pricelist_no`. Rows are ordered preferred-first, then cheapest (`price-list.service.ts:715`); rows priced `0` are excluded. The chosen `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price`, and `pricelist_type` (`enum_pricelist_compare_type`) are snapshotted onto the line so historical PR data is stable even when pricelists change. If the requestor manually selects a vendor outside the pricelist, `pricelist_type` is set accordingly and `is_discount_adjustment` / `is_tax_adjustment` may be flagged.
- **Product** — `product_id` is a required FK to [product](/en/inventory/product); product master data (code, name, local name, SKU, inventory base UoM) is snapshotted onto the line at write time. Inactive products cannot be added (`PR_VAL_007`). Service-line behaviour is achieved by selecting a "service" placeholder product.
- **Purchase-order** — PR is the upstream document for [purchase-order](/en/inventory/purchase-order). The link is the bridge table `tb_purchase_order_detail_tb_purchase_request_detail` (many-to-many), supporting both **consolidation** (multiple PR lines feed one PO line — typically grouped by vendor and currency) and **partial conversion** (one PR line spawns multiple PO lines across delivery dates or vendors). The PR `pr_status` does not flip to `completed` until every line is fully bridged or cancelled (`PR_POST_007`).
- **Templates** — `tb_purchase_request_template` / `tb_purchase_request_template_detail` are seed-only. They do not enter a workflow themselves; **Create from Template** is a client-side pre-fill (`/procurement/purchase-request/from-template` → quantity step → the normal new-PR form with the template passed as router state) — nothing is written until the user saves, and the resulting PR keeps no link to the template. The template's `workflow_id` is copied as the new PR's workflow; see [templates/purchase-request](/en/inventory/templates/purchase-request).

## 7. References

- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — primary business-analysis source; rule IDs `PR_CRT_*`, `PR_BDG_*`, `PR_WFL_*`, `PR_ITM_*`, plus the calculation block `PR_036`–`PR_055`.
- `../carmen/docs/purchase-request-management/PR-Technical-Specification.md` — technical rules, Zod validation schemas (`PurchaseRequestSchema`, `PurchaseRequestItemSchema`), approval-flow sequence diagrams, and threshold-based workflow routing.
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — cross-module integration (budget, inventory, workflow, notification), role-based permissions, and state shape.
- Sibling page: [01-data-model](/en/inventory/purchase-request/01-data-model) — canonical Prisma entities, enums, and rounding precision (`Decimal(15, 5)` / `Decimal(20, 5)`).
- Backend rule implementation: `../carmen-turborepo-backend/apps/micro-business/src/procurement/purchase-request/` — `logic/purchase-request.validate.ts` (submit rules), `logic/verify/purchase-request.verify-create.ts` / `verify-approve.ts` (pre-flight), `logic/purchase-request.logic.ts` (`verify`, `submit`, `approve`, `reject`, `review`), `purchase-request.service.ts` (`delete`, `deleteBatch`, status writes), `logic/purchase-request.row-filter.ts` (visibility), `pr-price-mask.ts` / `pr-hidden-price-guard.ts` (hidden prices), `purchase-request.conversion-factor.ts` (unit factors) — plus `purchase-request-comment/`, `purchase-request-template/`, and the API edge in `apps/backend-gateway/src/application/purchase-requests/` (`purchase-requests.controller.ts`, `swagger/request.ts` `PurchaseRequestVerifySwaggerDto`).
- Frontend rule implementation: `../carmen-frontend/routes/procurement/purchase-request/pr-form-schema.ts` (Zod schema, `findRowsMissingQty`), `use-pr-form-actions.ts` (`handleSubmitPr`), `workflow/pr-footer-action.tsx`, `pr-hidden-fields.ts`, `swipe-results.ts`.
