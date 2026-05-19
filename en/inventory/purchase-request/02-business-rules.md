---
title: Purchase Request — Business Rules
description: Validation, calculation, authorization, and posting rules for purchase-request.
published: true
date: 2026-05-19T23:55:00.000Z
tags: purchase-request, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Business Rules

> **At a Glance**
> **Rule families:** `PR_VAL_*` validation &nbsp;·&nbsp; `PR_AUTH_*` permission &nbsp;·&nbsp; `PR_CALC_*` calc &nbsp;·&nbsp; `PR_POST_*` posting
> **Rule count:** approximately 40 rules
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Status lifecycle:** Section 5.1 (where present) carries the Live UI vs BRD discrepancy callouts

## 1. Overview

This page enumerates the rules that govern a Purchase Request (PR) end-to-end: how header and line fields are validated, how monetary totals are calculated from line entries up to the document roll-up, who can move a PR through its workflow chain, what side-effects happen on submit / approve / cancel / convert, and how PR interacts with the budget, vendor-pricelist, inventory, and purchase-order modules. Rules are derived from `purchase-request-ba.md`, `PR-Technical-Specification.md`, and `PR-Module-Structure.md`, and aligned with the canonical Prisma entities documented in [01-data-model](/purchase-request/01-data-model) — specifically `tb_purchase_request`, `tb_purchase_request_detail`, `tb_purchase_request_comment`, `tb_purchase_request_detail_comment`, `tb_purchase_request_template`, and `tb_purchase_request_template_detail`.

The rules cover four governance surfaces. **Validation rules** fire at create / edit / submit time and guard field correctness, referential integrity, and cross-field consistency. **Calculation rules** define deterministic formulas for line and header totals, taxes, discounts, and base-currency conversions, all preserved at five decimals via Prisma `Decimal(15, 5)` / `Decimal(20, 5)`. **Authorization rules** describe who can act on the PR at each workflow stage and which actions (approve, reject, send-back, split-reject) are available. **Posting rules** describe the status transitions on `enum_purchase_request_doc_status` and the downstream effects (budget soft-commit, PO conversion bridge, audit-comment writes). Cross-module rules tie the PR to budget, inventory, vendor-pricelist, and purchase-order. Specific currency amounts in examples use `฿` (Thai Baht).

## 2. Validation Rules

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `PR_VAL_001` | `tb_purchase_request.pr_no` must be present and unique within the active (`deleted_at IS NULL`) set. Generated server-side; format is application-policy (e.g. `PR-YYYYMM-NNNN`). | On create (header insert) | Reject with `"PR reference number is required and must be unique"`. Backed by `PR0_pr_no_u` unique index `(pr_no, deleted_at)`. |
| `PR_VAL_002` | `requestor_id` must reference an active user; `requestor_name` snapshot must be populated alongside it. | On create / on submit | Reject with `"Requestor is required"`. |
| `PR_VAL_003` | `department_id` must be set and the requestor must belong to that department (or be delegated authority for it). | On create / on submit | Reject with `"Department is required and must match requestor membership"`. |
| `PR_VAL_004` | `workflow_id` must reference an active row in `tb_workflow` whose document scope is `purchase-request`. | On submit | Reject with `"A valid PR workflow must be selected"`. The selected `workflow_name` is snapshotted onto the header. |
| `PR_VAL_005` | `pr_date` must be present, in valid ISO-8601 form, and not later than today (no future-dated documents). | On submit | Reject with `"PR date cannot be in the future"`. |
| `PR_VAL_006` | At least one non-deleted `tb_purchase_request_detail` row must be attached. | On submit | Reject with `"A PR must contain at least one line item"`. |
| `PR_VAL_007` | Every detail line must reference a non-null `product_id` that resolves to an active row in `tb_product`. Service / free-text lines must still pick a product placeholder. | On line save / on submit | Reject with `"Product is required on every line"`. The DB enforces NOT NULL on `product_id`. |
| `PR_VAL_008` | Every detail line must carry `requested_qty > 0` together with `requested_unit_id` and a non-null `requested_unit_conversion_factor`. | On line save / on submit | Reject with `"Requested quantity must be greater than zero and have a unit"`. |
| `PR_VAL_009` | `delivery_date` on a line, when supplied, must be on or after `pr_date`. | On line save / on submit | Reject with `"Delivery date cannot be earlier than the PR date"`. |
| `PR_VAL_010` | `location_id` on a line must reference an active `tb_location` of a type that can request stock. Per the unique index `PR1_purchase_request_product_location_dimension_u`, the combination `(purchase_request_id, product_id, location_id, dimension)` must be unique within the PR. | On line save | Reject duplicates with `"Same product cannot be requested twice for the same location and dimension"`. |
| `PR_VAL_011` | `currency_id` on the line must reference an active `tb_currency`; `exchange_rate` must be > 0 (default `1`); `exchange_rate_date` must be on or before `pr_date`. | On line save / on submit | Reject with `"Currency and exchange rate are required and must be effective on or before the PR date"`. |
| `PR_VAL_012` | `tax_rate` and `discount_rate` must each be between `0` and `100` (percent). `tax_amount` / `discount_amount` must be ≥ `0`. Manual overrides set `is_tax_adjustment` / `is_discount_adjustment` to `true`. | On line save | Reject with `"Tax and discount rates must be between 0 and 100"`. |
| `PR_VAL_013` | When `approved_qty` is provided it must be > 0 and ≤ `requested_qty` (after conversion to a common base UoM). `approved_unit_id` and `approved_unit_conversion_factor` must be supplied with it. | On approval action | Reject with `"Approved quantity must be positive and may not exceed requested quantity"`. |
| `PR_VAL_014` | The user submitting the PR must have permission to act on the workflow's first `enum_stage_role = create` stage. | On submit | Reject with `"You are not authorised to submit purchase requests"`. |
| `PR_VAL_015` | Budget availability must be checked at submit. The sum of `base_total_amount` plus existing soft-commitments for the `(department, budget_category, period)` triple must not exceed the period's available budget. | On submit | Reject with `"Budget unavailable for this department / category"`. Override requires a budget-controller flag (see `PR_AUTH_005`). |
| `PR_VAL_016` | Optimistic concurrency: `doc_version` on the row being updated must equal the value the client read. | On any update | Reject with `"Document was modified by another user; reload and retry"` and bump `doc_version` by 1 on successful write. |

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

Actual stages are configurable per organisation in `tb_workflow`; the chain a given PR follows is determined by the row referenced by `tb_purchase_request.workflow_id`.

- **`PR_AUTH_001`** — Only the requestor (`requestor_id == auth.user.id`) or a user delegated by the requestor may edit a PR while `pr_status = draft`. Other users have read-only access.
- **`PR_AUTH_002`** — At each stage, only the users named in `tb_purchase_request.user_action.execute[]` may take an action. The list is recomputed on every stage transition from the stage's role / department / amount-threshold rules.
- **`PR_AUTH_003`** — Every approver has three line-level actions: **approve**, **reject**, and **send-back**. `send-back` returns the PR to the prior stage with `last_action = reviewed`; **split-reject** lets the approver reject specific lines while letting the rest of the PR proceed (rejected lines remain on the document with `current_stage_status = rejected`).
- **`PR_AUTH_004`** — Header-level **reject** terminates the chain immediately and moves `pr_status` to `cancelled`; the soft-commitment to budget is released (see `PR_POST_006`).
- **`PR_AUTH_005`** — Amount thresholds drive which stages fire (e.g. `Stage 4` may be skipped below a configurable threshold). Specific amount thresholds are configurable per organisation; see workflow configuration in `tb_workflow`. The source documentation does not fix specific numbers.
- **`PR_AUTH_006`** — Delegation: an approver may temporarily delegate their stage to another user via the workflow engine. The delegated user inherits the same approve / reject / send-back rights for the delegation window only; the original `last_action_by_id` reflects the delegate, while audit comments capture the delegation source.
- **`PR_AUTH_007`** — **Void** rights belong to a Finance or system-admin role and are available at any stage after submit. Void sets `pr_status = voided`, freezes the document for further action, and releases any open soft-commitments.
- **`PR_AUTH_008`** — Conversion to PO is restricted to roles with `enum_stage_role = purchase`. Approved PRs may sit in the `approved` status until a procurement user creates the PO via the bridge `tb_purchase_order_detail_tb_purchase_request_detail`.

> ⚠️ **Discrepancy — bulk-toolbar vs row-level actions (BRD FR-PR-005A):** The BRD specifies per-row standalone **Approve / Reject / Send for Review** buttons in the PR list / detail header. The current live UI exposes these actions only as **bulk toolbar actions** inside Edit Mode (via the Select All dropdown → bulk action toolbar). Confirmed bulk actions: Approve, Reject, Send for Review (BRD "Return Selected"), Split. Standalone row-level buttons remain absent. Source: `Test_case/Purchase_Request/Approver/INDEX.md` (capture date 2026-04-19). Verification status: confirmed for HOD; assumed for FC / GM / Owner.

> ⚠️ **Discrepancy — Send-back disabled-button tooltip:** The Submit / Send-back buttons are disabled when pre-conditions are not met (`PR_VAL_004`–`PR_VAL_006`) but the live UI shows no tooltip explaining the disabled reason. Known usability gap captured in `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § 6.4.

## 5. Posting Rules

Status transitions are recorded on `tb_purchase_request.pr_status` (`enum_purchase_request_doc_status = { draft, in_progress, voided, approved, completed, cancelled }`). Every transition writes both a header row in `workflow_history` (JSON timeline) and a `tb_purchase_request_comment` row with `type = system` for the audit trail.

- **`PR_POST_001` — Create.** New PR is inserted with `pr_status = draft`, `last_action = submitted` is **not** yet set, `workflow_current_stage` is the workflow's entry stage, and `base_*_amount` totals are zero until lines are added.
- **`PR_POST_002` — Submit.** Transition `draft → in_progress`. The system: (a) sets `last_action = submitted`, `last_action_at_date = now()`, `last_action_by_*` to the requestor; (b) snapshots `workflow_name` from the chosen `tb_workflow`; (c) initialises `stages_status` per stage; (d) computes the budget soft-commitment (see Section 6) and inserts the period reservation; (e) inserts a `tb_purchase_request_comment` with `type = system` and the submit message; (f) notifies the users in `user_action.execute[]` of the first approval stage. BRD `FR-PR-005` sets the first-approver notification SLA at **5 minutes** from submit; the SLA is not yet verified against the live notification service.

> ⚠️ **Discrepancy — notification SLA unverified:** BRD `FR-PR-005` specifies a 5-minute email notification SLA for the first approver on submit. Not yet verified in the test environment because dispatch depends on the notification service availability. Source: `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § BR-06.

> ⚠️ **Discrepancy — budget check `warn` vs `block`:** BRD `FR-PR-004` makes the budget check configurable per organisation policy — either *warn* (allow submit with warning) or *block* (prevent submit when over budget). The current test account has zero unit prices on items (commitment = `฿0.00`) so the live behaviour for an over-budget submit is not observable. Source: `Test_case/Purchase_Request/Creator/step-06-submit-confirmation.md` § BR-09.
- **`PR_POST_003` — Send-back.** Transition `in_progress → in_progress` with `workflow_current_stage` moved one step back and `last_action = reviewed`. Notification is sent to the user at the new (previous) stage. The soft-commitment remains in place.
- **`PR_POST_004` — Approve (intermediate stage).** Updates `workflow_previous_stage`, `workflow_current_stage`, `workflow_next_stage`, `last_action = approved`, `stages_status` for the just-completed stage; appends `workflow_history`; recomputes `user_action.execute[]` for the next stage. `pr_status` stays `in_progress`.
- **`PR_POST_005` — Final approve.** When the last `approve` stage clears, `pr_status` flips from `in_progress` to `approved`. The PR is now eligible for PO conversion; the soft-commitment remains in place (it is converted to a hard commitment when the PO is created — see [purchase-order](/en/inventory/purchase-order)).
- **`PR_POST_006` — Reject / Void / Cancel.** A header-level `reject` from any approver moves `pr_status` to `cancelled`. A Finance / admin `void` moves `pr_status` to `voided`. Both transitions release the budget soft-commitment, append `workflow_history`, and insert a `type = system` comment with the reason. Line-level `reject` (split-reject) sets per-line `current_stage_status = rejected` but does not change `pr_status`.
- **`PR_POST_007` — Convert to PO.** When a procurement user creates a PO from one or more approved PRs, each affected `tb_purchase_request_detail` row gains a row in the bridge `tb_purchase_order_detail_tb_purchase_request_detail` linking it to the new PO line. Once **all** lines of the PR are either fully converted (sum of bridge-linked PO quantities equals `approved_base_qty`) or explicitly cancelled, the system flips `pr_status` from `approved` to `completed`. Partial conversion leaves the PR in `approved` with remaining open quantity until a subsequent PO consumes it.
- **`PR_POST_008` — Audit comments are immutable.** `tb_purchase_request_comment` rows with `type = system` cannot be edited after insert. User comments (`type = user`) may be soft-deleted (`deleted_at`) by their author but never hard-deleted; the soft-delete itself is captured by audit.

There are no stock-level postings from PR: the PR module is a procurement intent document and does not touch inventory balances. Stock movements occur downstream in [purchase-order](/en/inventory/purchase-order) and Good Receive Note ([good-receive-note](/en/inventory/good-receive-note)).

## 6. Cross-Module Rules

- **Budget** — On submit, the PR's `base_total_amount` plus any per-line allocation against a budget category creates a **soft commitment** in the budget module (`BudgetData.softCommitmentPR`). The commitment decrements `availableBudget` for the relevant period. Soft commitments are released on `cancelled` / `voided`, and are converted to a hard commitment on `tb_purchase_order` creation (see `PR_POST_007` and [purchase-order](/en/inventory/purchase-order)).
- **Inventory** — The line capture UI reads from [inventory](/en/inventory/inventory) to display on-hand qty, on-order qty, reorder level, average monthly usage, and last purchase price for context only — none of these values are persisted on the PR detail. The PR does **not** reserve or move inventory.
- **Vendor & vendor-pricelist** — Each detail line resolves an optional preferred vendor via [vendor-pricelist](/en/inventory/vendor-pricelist) lookups against the requested product, location, and effective date. The chosen `pricelist_detail_id`, `pricelist_no`, `pricelist_unit`, `pricelist_price`, and `pricelist_type` (`enum_pricelist_compare_type`) are snapshotted onto the line so historical PR data is stable even when pricelists change. If the requestor manually selects a vendor outside the pricelist, `pricelist_type` is set accordingly and `is_discount_adjustment` / `is_tax_adjustment` may be flagged.
- **Product** — `product_id` is a required FK to [product](/en/inventory/product); product master data (code, name, local name, SKU, inventory base UoM) is snapshotted onto the line at write time. Inactive products cannot be added (`PR_VAL_007`). Service-line behaviour is achieved by selecting a "service" placeholder product.
- **Purchase-order** — PR is the upstream document for [purchase-order](/en/inventory/purchase-order). The link is the bridge table `tb_purchase_order_detail_tb_purchase_request_detail` (many-to-many), supporting both **consolidation** (multiple PR lines feed one PO line — typically grouped by vendor and currency) and **partial conversion** (one PR line spawns multiple PO lines across delivery dates or vendors). The PR `pr_status` does not flip to `completed` until every line is fully bridged or cancelled (`PR_POST_007`).
- **Templates** — `tb_purchase_request_template` / `tb_purchase_request_template_detail` are seed-only. They do not enter a workflow themselves; creating a PR from a template clones the template's lines into a new `tb_purchase_request` with status `draft`. The template's `workflow_id` is copied as the new PR's default workflow.

## 7. References

- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — primary business-analysis source; rule IDs `PR_CRT_*`, `PR_BDG_*`, `PR_WFL_*`, `PR_ITM_*`, plus the calculation block `PR_036`–`PR_055`.
- `../carmen/docs/purchase-request-management/PR-Technical-Specification.md` — technical rules, Zod validation schemas (`PurchaseRequestSchema`, `PurchaseRequestItemSchema`), approval-flow sequence diagrams, and threshold-based workflow routing.
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — cross-module integration (budget, inventory, workflow, notification), role-based permissions, and state shape.
- Sibling page: [01-data-model](/purchase-request/01-data-model) — canonical Prisma entities, enums, and rounding precision (`Decimal(15, 5)` / `Decimal(20, 5)`).
- Backend rule implementation: `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-request/` (header service), `purchase-request-comment/`, and `purchase-request-template/` plus the API edge in `apps/backend-gateway/src/application/purchase-requests/`.
