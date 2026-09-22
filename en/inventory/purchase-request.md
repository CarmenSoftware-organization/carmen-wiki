---
title: Purchase Request
description: Internal request to procure goods — the upstream demand signal that becomes a purchase order after approval.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: purchase-request, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Purchase Request

> **At a Glance**
> **Module purpose:** Multi-stage internal demand workflow (`Draft` → `In Progress` (multi-stage approval; Send-Back keeps `In Progress`) → `Approved` → `Completed`, or `Voided` via an approver Reject; drafts are soft-deleted) that hands a vendor-allocated requirement to procurement &nbsp;·&nbsp; **Audience:** Requestor, stage approvers (HOD / FC / GM — whatever the workflow defines), Purchaser, Procurement Manager, Auditor &nbsp;·&nbsp; **Key entities/tables:** `tb_purchase_request`, `tb_purchase_request_detail`, approval history, pricelist allocation, [purchase-request/my-approval](/en/inventory/purchase-request/my-approval) &nbsp;·&nbsp; **Sub-pages:** 15

![Purchase Request module screen](/screenshots/purchase-request/index.png)

![Purchase Request module detail screen](/screenshots/purchase-request/detail.png)

## 1. Overview

A **Purchase Request (PR)** is the internal demand document raised by an operating department to authorise the procurement of goods or services before any external commitment is made to a vendor. Each PR has a header — server-generated `pr_no`, `pr_date`, the `workflow_id` it will route through, requestor and department (snapshotted as `*_name`), description and note — and one or more item lines that carry the product, store location, delivery point and delivery date, requested / approved / FOC quantity triples each with their own unit, vendor and pricelist snapshot, unit price, discount, tax profile, and computed line totals in both transaction and base currency. The header rolls the lines into `base_net_amount` / `base_total_amount` (`tb_purchase_request`, Prisma schema `tb_purchase_request` model). There is **no PR-type, job/cost-code or header delivery-date column** — those appeared in the concept docs only; see [01-data-model](/en/inventory/purchase-request/01-data-model) §5.

The PR document status (`tb_purchase_request.pr_status`, `enum_purchase_request_doc_status`) is workflow-driven: `draft` (editable by the requestor) → `in_progress` on submit (the PR stays `in_progress` while it is routed through every stage of the chain, **including after a Send-Back** — a review moves `workflow_current_stage` backwards but never rewrites `pr_status`, `purchase-request.service.ts:2052`) → `approved` once the final stage clears → `completed` once every line has been converted to a purchase order. A header-level **Reject** from any approver moves the PR to `voided` — the only code path that writes that value (`purchase-request.service.ts:2201`); there is **no separate administrative "void" endpoint** in `purchase-requests.controller.ts` (asserted in earlier revisions — unconfirmed). A `draft` is not voided but **soft-deleted** (`DELETE /:bu_code/purchase-requests/:id`, draft-only, owner or platform super-admin — `purchase-request.service.ts:1648-1720`). Stages are whatever the assigned workflow defines (`enum_stage_role = create | approve | purchase | issue | view_only`); labels such as "Department Head", "Budget Controller" or "Finance" in this module's pages are illustrative stage names, not roles the code knows about. Amount-threshold routing between stages is real (`tb_workflow.data.routing_rules`, see `PR_AUTH_005`); a delegation-of-authority mechanism is not (`PR_AUTH_006`, unconfirmed).

The PR is the upstream demand signal in the procure-to-pay chain. It captures *what* is needed, *for whom*, *by when*, and *roughly how much*, then hands an approved, costed, vendor-allocated requirement to procurement. **Auto Allocate** (`pr-auto-allocate.ts`) calls the pricelist price-compare endpoint per line; the backend returns every active pricelist row for the product / unit / currency / date with `price > 0`, ordered **preferred vendor first, then lowest price** (`price-list.service.ts:715` `orderBy: [{ is_preferred: 'desc' }, { price: 'asc' }]`), keeps the best MOQ tier the requested `qty` reaches, and hands back the winner as `selected` together with the product's **last purchase price** (`last_price`, 2026-09-17). "Last-receiving history" as a ranking criterion — asserted in earlier revisions — has no code path. The approved PR is then converted into a purchase order to commit externally. **Budget checks and soft commitments** — asserted throughout earlier revisions of this module — have **no code path**: a grep for `budget` / `soft_commit` across `apps/micro-business/src/procurement/purchase-request`, `apps/backend-gateway/src/application/purchase-requests`, `apps/backend-gateway/src/application/my-pending` and `routes/procurement/purchase-request` finds only an optional `budget_code?: string` interface field and the example reject message "Budget exceeded for this period". Treat every budget sentence in this module as unconfirmed design intent.

## 2. Business Context

Hospitality procurement runs on tight margins and high-volume, low-value purchases across many cost centres, so the PR is the control point that prevents uncontrolled spend before any external commitment is made. By forcing every purchase intent through a documented, multi-approver workflow — with mandatory requestor, department, workflow, PR date, at least one line that either buys (`requested_qty > 0`) or receives free goods (`foc_qty > 0`), and a unique reference number (`purchase-request.validate.ts`) — the PR enforces spending policy upstream of the vendor. *(A forward-looking budget view driven by soft commitments was asserted in earlier revisions — unconfirmed, no code path; see §1.)*

The module is also the integration spine for everything downstream. PR data flows into the inventory module (on-hand, on-order and last purchase price visible to the requestor per line — `pr-inventory-row.tsx`, `pr-last-receiving-info.tsx`), the vendor-pricelist module (price comparison, Auto Allocate, MOQ tiers), the workflow engine (configurable approval routing, `user_action.execute[]`, notifications), and the purchase order module (PR-to-PO conversion with full traceability through `tb_purchase_order_detail_tb_purchase_request_detail`). Document management (comments, attachments, activity log) gives every PR a complete audit trail — who created it, who changed it, who approved or rejected it and when.

Financial accuracy is enforced at the calculation layer: line and header amounts are persisted at five decimals (`Decimal(20, 5)` / `Decimal(15, 5)`), the server recomputes every amount from its own inputs at the `purchase` stage (`POST …/verify` with `stage_role = purchase`), and a per-line discount or tax that exceeds the line value is rejected (`PR_ERROR.DISCOUNT_EXCEEDS_LINE_AMOUNT` / `TAX_EXCEEDS_LINE_AMOUNT`, `common/verify/amount.check.ts`, 2026-09-17). See [02-business-rules](/en/inventory/purchase-request/02-business-rules) §3 for the formulas.

## 3. Key Concepts

- **Approval Stage**: A configurable stage in the PR workflow (`tb_workflow`) with a `stage_role`, assigned users and optional routing rules. The workflow's routing rules can skip or jump to a stage once the header total (or department) crosses a configured value (`PR_AUTH_005`). The entire path is recorded in `workflow_history` and the activity log. *(Deputy-delegation of approvals — unconfirmed, no such mechanism found; see `PR_AUTH_006`.)*
- **Budget Check / Soft Commitment**: **Unconfirmed — no code path.** Earlier revisions described an availability check at submit and a reversible soft commitment released on reject. Nothing in the backend, frontend or Bruno collections implements either (see §1 for the grep); the only budget-related artefacts are an optional `budget_code` string on the interface and a sample reject message.
- **Preferred Vendor / Auto Allocate**: The price-compare lookup selects, per line, the pricelist row that is preferred first and cheapest second, at the MOQ tier the requested quantity qualifies for, and populates vendor, `pricelist_detail_id`, `pricelist_no`, unit price, tax profile and exchange rate. The Purchaser can override it from the **Price Comparison** dialog; if the line's Adjust checkbox is set, prices are no longer auto-updated by re-allocation.
- **PR Type**: **Not a field.** `tb_purchase_request` has no `pr_type` column and no enum; the "General Purchase / Market List / Asset" classification exists only in `../carmen/docs/`. Routing differences come from choosing a different `workflow_id`.
- **Approved Quantity vs. Requested Quantity**: Each line carries both. The requestor enters `requested_qty`; approvers at an `approve`-role stage edit `approved_qty`. The server only rejects a **negative** `approved_qty` and an approved unit that is not an order unit of the product (`logic/verify/purchase-request.verify-approve.ts:172-181`); an upper bound of `requested_qty` — asserted in earlier revisions — has no code path. The approved quantity is what flows into the purchase order on conversion.
- **FOC (Free of Charge)**: A line-level quantity triple (`foc_qty`, `foc_unit_id`, factor) for vendor-supplied items that arrive at zero price. Since 2026-09 a line may be **FOC-only**: `requested_qty = 0` with `foc_qty > 0` is submittable, while a line with both at zero is rejected ("needs a requested_qty or a foc_qty", `purchase-request.validate.ts:105-131`; FE gate `findRowsMissingQty` in `pr-form-schema.ts`). FOC quantities are excluded from the PR subtotal but appear on the resulting PO and GRN.
- **Conversion to PO**: The procurement step where one or more `approved` PRs are turned into purchase orders — whole PRs are selected, lines are grouped by `(vendor, delivery_date, currency)`, and the PR flips to `completed` once every line is bridged (`PR_POST_007`; see [purchase-order](/en/inventory/purchase-order)).
- **Delete vs. Reject**: A `draft` PR is **deleted** (soft delete, owner or super-admin, single or batch — `DELETE /:bu_code/purchase-requests/batch` reports `not_found` / `not_draft` / `not_owner` per id). Once submitted, termination only happens through the workflow: an approver chooses **Reject** (→ `voided`, reason required) or **Send Back** (stage cursor moves back, PR stays `in_progress`). **Split** lets an approver reject specific lines while approving the rest (`POST …/:id/split`).
- **Price Comparison**: A line-level dialog (`pr-pricelist-dialog.tsx`) that lists every active pricelist row for the product — vendor, pricelist no., unit, price (with a "best" marker), effective range — plus an **Assign** button per row. Its header shows the requested and approved quantity and, since 2026-09-22, the product's **last purchase price** (`last_price.cost_per_unit`). The request sends `qty`, so each vendor is shown at the MOQ tier that quantity reaches (2026-09-16).
- **Pre-flight verification**: `POST /:bu_code/purchase-requests/verify` (2026-08-19) runs the full rule set for `verify_state = create | submit | approve` without writing anything and returns every problem at once (`is_valid`, `errors[]` with `error_code` / `field`); a failing PR still answers 200. See `PR_VAL_017`.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Requestor | Hotel or department staff member who initiates the PR. Creates the request, adds items with quantity, unit, location, delivery point and date, attaches supporting documents, and submits for approval. Tracks status and responds to send-backs. Owns (and may delete) their own drafts. |
| Department Head / stage approver (`approve` role) | Reviews PRs at the stage assigned to them, adjusts `approved_qty` if required, and approves, rejects, sends back, or splits individual lines. "Budget Controller" and "Finance" in this module's pages are further `approve`-role stages a workflow *may* define — the code has no budget check and no finance-specific behaviour. |
| Purchaser (`purchase` role) | At the `purchase` stage sets or validates vendor, unit price, discount and tax profile per line (Auto Allocate / Price Comparison), then bulk-decides like any other stage. Separately converts approved PRs to POs from the Purchase Order module. |
| Procurement Manager | An escalated `approve`-role stage reached by threshold routing or direct workflow configuration — identical UI and rights to any other approver. No vendor-ranking or allocation-rule configuration screen exists. |
| System Administrator | Configures workflow stages and routing thresholds (generic `/system-admin/workflow`), tax profiles, currency rates, users and roles. *(An administrative "void" action and delegation rules were asserted in earlier revisions — unconfirmed; no void endpoint exists and no delegation mechanism was found.)* |
| Auditor | Read-only access to PRs, comments and the generic `/system-admin/activity-log`. No dedicated audit workspace exists. |

## 5. Related Modules

**Cross-module flow:**
- [purchase-order](/en/inventory/purchase-order) — approved PRs become POs
- [product](/en/inventory/product) — PR lines reference products from the catalog
- [vendor-pricelist](/en/inventory/vendor-pricelist) — preferred vendors and reference prices come from the pricelist
- [inventory](/en/inventory/inventory) — current stock levels often justify a PR
- [templates/purchase-request](/en/inventory/templates/purchase-request) — reusable PR scaffold cloned via "Create from Template"

**Master configuration:**
- [master-data/vendor](/en/inventory/master-data/vendor) — allocated vendor per line resolved from the pricelist
- [master-data/currency](/en/inventory/master-data/currency) — transaction currency and exchange rate for multi-currency PRs
- [master-data/tax-profile](/en/inventory/master-data/tax-profile) — tax codes derived for PR lines
- [master-data/unit](/en/inventory/master-data/unit) — unit of measure on each PR line
- [master-data/department](/en/inventory/master-data/department) — requesting department / cost-centre on the PR header
- [system-config/workflow](/en/inventory/system-config/workflow) — multi-level approval workflow definitions for PR authorization
- [system-config/running-code](/en/inventory/system-config/running-code) — PR document number sequencing
- [system-config/dimension](/en/inventory/system-config/dimension) — analytical dimensions (job/cost code, project) carried on the PR
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — PR status-transition and approval-history log for audit
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — supporting documents (quotes, specifications) attached to the PR
- [reporting-audit/notification](/en/inventory/reporting-audit/notification) — approval / send-back / reject notifications routed through the workflow

## 6. Reference Sources

- Concepts: `../carmen/docs/purchase-request-management/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](/en/inventory/purchase-request/01-data-model) — Entities, fields, relationships, and enums (Prisma-derived).
- [01a — Data Model — Comment Tables](/en/inventory/purchase-request/01a-data-model-comments) — Document-level and line-level comment / attachment tables and the `enum_comment_type` user/system tagging.
- [02 — Business Rules](/en/inventory/purchase-request/02-business-rules) — Validation, calculation, authorization, and posting rules.
- [03 — User Flow](/en/inventory/purchase-request/03-user-flow) — Document lifecycle and persona index.
  - [Requestor](/en/inventory/purchase-request/03-user-flow-requestor)
  - [Approver](/en/inventory/purchase-request/03-user-flow-approver)
  - [Purchaser](/en/inventory/purchase-request/03-user-flow-purchaser)
  - [Procurement Manager](/en/inventory/purchase-request/03-user-flow-procurement-manager)
  - [Audit / Config](/en/inventory/purchase-request/03-user-flow-audit-config)
- [04 — Test Scenarios](/en/inventory/purchase-request/04-test-scenarios) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Requestor](/en/inventory/purchase-request/04-test-scenarios-requestor)
  - [Approver](/en/inventory/purchase-request/04-test-scenarios-approver)
  - [Purchaser](/en/inventory/purchase-request/04-test-scenarios-purchaser)
  - [Procurement Manager](/en/inventory/purchase-request/04-test-scenarios-procurement-manager)
  - [Audit / Config](/en/inventory/purchase-request/04-test-scenarios-audit-config)

## 8. API Surface (verified 2026-09-22)

All routes live in `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/purchase-requests/purchase-requests.controller.ts` (`@Controller('api')`); guards are `AppIdGuard('purchaseRequest.<verb>')` plus `@Permission({ 'procurement.purchase_request': ['view'] })` on the list endpoints. Bruno: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/procurement/purchase-request/`.

| Verb + path | Purpose | Notes |
|---|---|---|
| `GET /purchase-requests` | Cross-unit list (no `bu_code` in the path) | `@Serialize(PurchaseRequestListItemResponseSchema)` |
| `GET /:bu_code/purchase-requests/for-po` | Approved PRs selectable for PO conversion | |
| `GET /:bu_code/purchase-requests/workflow-stages` · `/:pr_id/previous-stages` | Stage lists for filters / send-back targets | |
| `GET /:bu_code/purchase-requests/:id` | Detail; entity references as objects, `last_price` per line | serializer `common/dto/purchase-request/purchase-request.serializer.ts` |
| `GET /:bu_code/purchase-requests/:id/status/:status` | Detail filtered by line stage status | `AppIdGuard('purchaseRequest.approval')` |
| `POST /:bu_code/purchase-requests` · `PATCH …/:id/save` | Create / save draft (`stage_role` in body; `@ExpandRefs`) | qty `0` allowed on save |
| `POST /:bu_code/purchase-requests/verify` | Pre-flight rule check, `verify_state = create \| submit \| approve` | 200 with `is_valid: false` on failure |
| `PATCH …/:id/submit` · `/approve` · `/reject` · `/review` | Workflow verbs (`doc_version` echoed) | `review` = send back |
| `POST …/duplicate-pr` · `POST …/:id/split` | Copy a PR; split selected lines into a new PR | |
| `POST …/swipe-approve` · `/swipe-reject` | Mobile bulk approve / reject | |
| `DELETE /:bu_code/purchase-requests/:id` · `DELETE …/batch` | Soft-delete drafts (owner or super-admin) | batch returns per-id `not_found` / `not_draft` / `not_owner` |
| `GET …/:id/export` · `/print` · `/print-viewer` | Excel export, PDF print | |
| `GET …/detail/:detail_id/dimension` · `/history` · `/calculate` | Line dimensions, per-line stage history, price calculation | |
| `POST …/regenerate-totals` · `POST …/:id/regenerate-totals` | Recompute header roll-ups | |
| `GET /api/my-pending/purchase-requests…` | Per-user pending PRs (My Pending tab) | see [my-approval](/en/inventory/purchase-request/my-approval) |

