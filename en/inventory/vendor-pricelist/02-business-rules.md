---
title: Vendor Pricelist — Business Rules
description: Validation, calculation, authorization, status transitions, and cross-module rules for vendor-pricelist.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Business Rules

> **At a Glance**
> **Rule families:** `VPL_VAL_*` validation &nbsp;·&nbsp; `VPL_CALC_*` calc &nbsp;·&nbsp; `VPL_XMOD_*` cross-module
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Implementation status (verified 2026-07-16):** most rows below are marked either **Confirmed** (real code: a Zod check, a Prisma constraint, or an explicit `if` in a service method) or **Design-target** (present in `../carmen/docs/vendor-pricelist-management/` but with zero matching code anywhere in `carmen-inventory-frontend-react` or `carmen-turborepo-backend-v2`). This module has **no workflow engine**, **no distinct approve/reject/submit endpoints**, **no quality score**, **no validation engine beyond field-level checks**, and **no automatic comment/activity-log writes** — see [01-data-model](/en/inventory/vendor-pricelist/01-data-model) § 5 and [01a-data-model-comments](/en/inventory/vendor-pricelist/01a-data-model-comments) for the underlying evidence.

## 1. Overview

This page captures the operational rules for the module's four real screens — **Vendor**, **Price List** (`tb_pricelist`), **Price List Template** (`tb_pricelist_template`), and **Request for Pricing** (`tb_request_for_pricing`, documented in detail at [request-price-list](/en/inventory/vendor-pricelist/request-price-list)) — plus the external vendor portal. Each of Price List, Price List Template, and Request for Pricing is a plain CRUD resource: create / find / update / soft-delete, with `doc_version` optimistic-concurrency locking on every row. Price List Template additionally has one dedicated endpoint, `PATCH :id/status`, but it performs a bare status write with no validation. There is no separate "submit," "approve," or "reject" action on any of these resources — `status` is just a field the edit form can set, gated only by the same permission that gates the rest of the record.

The previous version of this page synthesised its rules primarily from `../carmen/docs/vendor-pricelist-management/` (`design.md`, `requirements.md`, `price-assignment-workflow-documentation.md`) and treated most of that design document's 6-phase campaign/quality-score/threshold/RBAC machinery as implemented. Re-reading `price-list.service.ts`, `price-list-template.service.ts`, `request-for-pricing.service.ts`, and `check-price-list.service.ts` directly (this pass) shows that machinery does not exist. Rules below are re-anchored to what the code actually does; carmen/docs citations are kept only where they describe something still un-implemented, and are labelled **Design-target** accordingly.

## 2. Validation Rules

| Rule ID | Tier | Condition | Status | Evidence |
| ------- | ---- | --------- | ------ | -------- |
| `VPL_VAL_001` | Template | `tb_pricelist_template.name` non-empty and unique among non-soft-deleted rows. | **Confirmed** (DB) | `@@unique([name, deleted_at])` (`pricelist_template_name_deletedat_u`); no separate app-level pre-check found, so the first signal a caller sees on a duplicate name is the DB constraint violation. |
| `VPL_VAL_002` | Template | Activate (`draft → active`) requires ≥1 `tb_pricelist_template_detail` row; re-activate requires all referenced products still active. | **Design-target** | `pricelist-templates.service.ts`'s `updateStatus()` sets `status` directly with no row-count or product-validity check of any kind. |
| `VPL_VAL_003` | Template | `currency_id` references a non-soft-deleted `tb_currency` row when set. | **Confirmed** (DB FK) | `currency_id → tb_currency.id`; no explicit application-layer message beyond the FK failure. |
| `VPL_VAL_004` | Template | `validity_period > 0`; `reminder_days` strictly decreasing. | **Design-target** | No such check in `price-list-template.service.ts`'s create/update path; `reminder_days` is stored as opaque `Json`. |
| `VPL_VAL_005` | Template | `tb_pricelist_template_detail.product_id` references an active product; unique per `(template, product)`. | **Confirmed (uniqueness only)** | `@@unique([pricelist_template_id, product_id, deleted_at])` is real; "product must be active" is not separately checked. |
| `VPL_VAL_006` | Template | `order_unit_obj` carries a `default_order` + ≥1 MOQ tier with `qty > 0`, strictly increasing across tiers. | **Design-target** | `order_unit_obj` is persisted as an opaque JSON blob (`Json? @default("{}")`); no service or frontend schema validates its internal shape. |
| `VPL_VAL_007` | Template | `escalation_after_days >= 0`. | **Design-target** | No such check found. |
| `VPL_VAL_008` | RFQ | `tb_request_for_pricing.name` non-empty and unique among non-soft-deleted rows. | **Confirmed** (DB) | `@@unique([name, deleted_at])` (`request_for_pricing_name_u`). |
| `VPL_VAL_009` | RFQ | `pricelist_template_id` references a template whose `status = active`. | **Design-target (partial)** | `request-for-pricing.service.ts create()` checks the template **exists**, not that its `status` is `active`. |
| `VPL_VAL_010` | RFQ | `start_date < end_date`; both windows valid; minimum tenant response window (design: 3 days). | **Confirmed (partial)** | `create()` explicitly rejects `startDate > endDate` (`RFP_INVALID_DATE_RANGE`); no separate "minimum window" check exists. |
| `VPL_VAL_011` | RFQ | ≥1 invited vendor with a valid contact email required before "launch." | **Design-target** | There is no separate launch step — `create()` accepts a `vendors.add` array of any length, including zero, in the same call that creates the RFQ header; nothing blocks a zero-vendor RFQ. |
| `VPL_VAL_012` | RFQ | Same vendor cannot be invited twice. | **Confirmed** (DB) | `@@unique([request_for_pricing_id, vendor_id, deleted_at])`. |
| `VPL_VAL_013` | RFQ | `email_template_id` must reference a valid, non-archived tenant email template. | **Design-target** | `email_template_id` is stored as a free `String?`; no lookup or validation against an email-template registry was found. |
| `VPL_VAL_014` | Pricelist | `pricelist_no` non-empty and unique among non-soft-deleted rows. | **Confirmed** (DB + app) | `@@unique([pricelist_no, deleted_at])`; `generatePLNo()` derives the next running number from the tenant's running-code pattern. |
| `VPL_VAL_015` | Pricelist | `vendor_id` / `currency_id` required and reference active master-data rows. | **Confirmed (existence only)** | `create()` looks up vendor/currency by id to snapshot the name/code; there is no explicit "must be active" gate found. |
| `VPL_VAL_016` | Pricelist | `effective_from_date < effective_to_date`; neither date in the past at create. | **Confirmed** | `create()` explicitly checks `effective_from_date < now()`, `effective_to_date < now()`, and `effective_from_date > effective_to_date`, each with its own `ERROR_CATALOG` entry. |
| `VPL_VAL_017` | Pricelist | `submission_method ∈ {online, email, portal, manual}`. | **Confirmed** (Prisma enum) | `pricelist_submission_method`. |
| `VPL_VAL_018` | Pricelist | Each detail row's `product_id` references an active product that also appears on the issuing template. | **Design-target** | `create()`/`update()` only look up the product to snapshot its name/code/SKU; no check that it belongs to any template. |
| `VPL_VAL_019` | Pricelist | `moq_qty >= 0`; no duplicate `(product, unit, moq_qty)` per pricelist. | **Confirmed (uniqueness only)** | `@@unique([pricelist_id, product_id, unit_id, moq_qty, deleted_at])`; the `>= 0` bound is enforced client-side (Zod `min(0)` in `pl-form-schema.ts`) but not re-checked server-side. |
| `VPL_VAL_020` | Pricelist | Multiple MOQ-tier rows for the same product must be non-increasing in price as `moq_qty` increases. | **Design-target** | No sort-and-compare check exists anywhere — neither in `price-list.service.ts` nor in the frontend form. A vendor or purchaser can save ascending MOQ pricing without any warning or rejection. |
| `VPL_VAL_021` | Pricelist | `tax_amt = Round(price_without_tax × tax_rate, 5)`; `price = Round(price_without_tax + tax_amt, 5)`. | **Confirmed (client-side only)** | `pl-form-schema.ts` derives `tax_amt`/`price` from `price_without_tax` and `tax_rate` before submit; the backend persists whatever values it receives with no server-side recomputation or reconciliation check. |
| `VPL_VAL_022` | Pricelist | `lead_time_days >= 0`; `rating` within a configurable 0–5 band. | **Confirmed (client-side only)** | Enforced by the frontend Zod schema; not re-checked server-side. |
| `VPL_VAL_023` | Pricelist | Submit requires ≥1 valid detail row. | **N/A** | There is no distinct "submit" action on the internal Price List screen; `status` is just set to whatever value the edit form sends. (The external vendor-portal `submit` call exists in the frontend but targets a backend route that does not exist — see [03-user-flow-vendor](/en/inventory/vendor-pricelist/03-user-flow-vendor).) |
| `VPL_VAL_024` | Pricelist | Status transitions follow a fixed state machine; out-of-order transitions blocked. | **Design-target** | No transition guard exists — `update()` writes whatever `status` value the caller sends, in any direction. |
| `VPL_VAL_025` | Pricelist | An `active` pricelist is immutable except for `status`. | **Design-target** | `update()` has no status-based branch — detail rows can be added/edited/removed on an `active` pricelist exactly as on a `draft` one. |

## 3. Calculation Rules

All monetary values are stored as `Decimal(20, 5)` at the row level; tax rates use `Decimal(15, 5)`.

| Rule ID | Formula | Status |
| ------- | ------- | ------ |
| `VPL_CALC_001` (line tax amount) | `tax_amt = Round(price_without_tax × tax_rate, 5)`. | **Confirmed (client-side)** — computed in `pl-form-schema.ts` before submit; the backend does not recompute it. |
| `VPL_CALC_002` (line gross price) | `price = Round(price_without_tax + tax_amt, 5)`. | **Confirmed (client-side)** — same caveat. |
| `VPL_CALC_003` (effective unit price per base UoM) | `effective_unit_price = price ÷ unit.conversion_factor_to_base`. | **Design-target** — no code anywhere computes or displays this; `tb_pricelist_detail` has no conversion-factor column and the frontend never resolves one. |
| `VPL_CALC_004` (preferred-row selection) | For a `(product_id, currency_id, due_date)` tuple, `GET .../pricelists/price-compare` returns matching `tb_pricelist_detail` rows across all vendors sorted `is_preferred desc, price asc`; the first row is `selected`, the rest are `lists`. | **Confirmed** — real endpoint (`PriceListService.priceCompare`), used by downstream pricing/comparison dialogs. |
| `VPL_CALC_005` (multi-currency display) | Pricelist values are stored in `tb_pricelist.currency_id`; no FX conversion is applied or stored anywhere in this module. | **Confirmed (by absence)** — no FX-rate lookup exists in `price-list.service.ts`; any cross-currency conversion is a downstream-module concern, not something this module performs. |
| `VPL_CALC_006` (quality score) | *(previously documented formula)* | **Removed — no code.** A repo-wide search for `quality_score`/`qualityScore` returns zero hits in this module. |

### 3.1 Worked example — multi-MOQ pricing on one product

Vendor `V1` submits a pricelist for product `P1` (`unit = Each`) at three MOQ tiers in `currency_id = THB`, `tax_rate = 0.07000`:

- Tier 1: `moq_qty = 1`, `price_without_tax = ฿12.50` → `tax_amt = ฿0.87500` → `price = ฿13.37500` (computed client-side per `VPL_CALC_001`/`VPL_CALC_002`).
- Tier 2: `moq_qty = 50`, `price_without_tax = ฿10.50` → `tax_amt = ฿0.73500` → `price = ฿11.23500`.
- Tier 3: `moq_qty = 100`, `price_without_tax = ฿9.75` → `tax_amt = ฿0.68250` → `price = ฿10.43250`.

These three prices happen to be non-increasing as `moq_qty` rises, which matches the intent behind `VPL_VAL_020` — but nothing in the current code checks or enforces that ordering. A vendor (or a purchaser typing directly into the Price List form) could save Tier 3 at `฿15.00` and the record would save without warning.

## 4. Authorization

Authorization in this module is coarse: **Vendor** (the CRUD screen, distinct from the external portal Vendor persona), **Price List**, **Price List Template**, and **Request for Pricing** each gate on their own module-level permission — there is no separate create-vs-edit-vs-approve split, no Manager-only high-value threshold, and no segregation-of-duties check anywhere in the code.

| Claim in the previous draft | Status | Evidence |
| --- | --- | --- |
| Purchasing Manager approves pricelists above a tenant "high-value threshold"; Purchaser is capped below it. | **Design-target — removed.** | A repo-wide search for `threshold` in this module returns zero relevant hits (mirrors the identical, already-confirmed finding in the `purchase-order` module). There is no distinct approve endpoint to gate in the first place — `status` is set via the ordinary `PATCH`. |
| Finance Manager co-signoff required to activate a multi-currency pricelist. | **Design-target — removed.** | No Finance persona or co-signoff mechanism exists — see [03-user-flow-finance](/en/inventory/vendor-pricelist/03-user-flow-finance). |
| Vendor portal session gated by token expiration, IP allowlist, and a concurrent-session limit (default 5). | **Design-target — removed.** | `check-price-list.service.ts`'s `checkPriceList()` looks the invitation row up by id and returns/creates a pricelist; it never checks `end_date`, an IP address, or a session count. |
| Segregation of duties: vendor-token holder ≠ approving user; high-value editor ≠ approver. | **Design-target — removed.** | No such cross-check exists in any service in this module. |
| System Administrator can revoke a vendor's portal token. | **Design-target — removed.** | No endpoint sets `pricelist_url_token` back to `NULL` anywhere in the backend; the token is written once, at RFQ-create time, and never touched again by any found code path. |
| Purchaser manually uploads an emailed pricelist on a vendor's behalf. | **Confirmed (mechanism), unconfirmed (label)** | `submission_method = email` is a real, settable field on `tb_pricelist`; a Purchaser can create/edit a pricelist with that value directly. There is no dedicated "upload on vendor's behalf" screen distinct from the ordinary Price List create/edit form. |
| Auditor has read-only access to pricelists/campaigns/invitations/validation results/activity log. | **Partially true, overstated** | Any user with view access can read the four list/detail screens; there is no dedicated Auditor role, query-builder workspace, or "validation results" surface (there are no validation results to show). See [03-user-flow-audit-config](/en/inventory/vendor-pricelist/03-user-flow-audit-config). |

## 5. Status Rules

### 5.1 Price List Template (`enum_pricelist_template_status`: `draft`, `active`, `inactive`)

`updateStatus()` is a real, dedicated endpoint (`PATCH :id/status`) but performs **no validation** — any authenticated caller with the endpoint's permission can move the status in either direction, at any time, regardless of whether the template has any product rows. There is no cron, no re-activation gate, and no comment written on the transition.

### 5.2 Request for Pricing (no status column)

`tb_request_for_pricing` has no status field, and no application code derives one. The only per-vendor signal the UI reads is `has_submitted: !!pricelist_id` on each invitation row (`request-for-pricings.service.ts findAll()`). There is no `draft`/`active`/`paused`/`completed`/`cancelled` derivation anywhere — the previous draft's entire "campaign lifecycle" section described a state machine with zero backing code and has been removed. A "cancelled" RFQ is simply a soft-deleted row (`remove()`).

### 5.3 Price List (`enum_pricelist_status`: `draft`, `active`, `inactive`, `expired`)

`create()`/`update()` set `status` to whatever value the caller sends; there is no distinct approve/reject/submit/activate action, no transition guard, and no auto-expire cron found in this repo (`micro-cronjobs` has no matching job). `remove()` (soft-delete) additionally forces `status = inactive`. Detail rows can be added, edited, or removed regardless of the header's current `status`, including `active`.

### 5.4 External vendor portal (confirmed gap)

`POST /api/check-pricelist/:url_token` (the only real backend endpoint for the portal) auto-creates a zero-priced draft pricelist from the invitation's template on first visit, or returns the existing one. The frontend also wires up `PATCH /api/pricelist-external/:token` (save) and `POST /api/pricelist-external/:token/submit` (submit) via `hooks/use-price-list-external.ts`, but **no backend route matching `pricelist-external` exists anywhere in `carmen-turborepo-backend-v2`** — confirmed by a repo-wide search returning zero hits outside the frontend's own endpoint-constant file. In the current codebase, the vendor portal can only be viewed; edits and submission do not persist through it. See [03-user-flow-vendor](/en/inventory/vendor-pricelist/03-user-flow-vendor) for the full detail.

## 6. Cross-Module Rules

| Rule ID | Related module | Rule | Status |
| ------- | -------------- | ---- | ------ |
| `VPL_XMOD_001` | [purchase-request](/en/inventory/purchase-request) | PR-line pricing can source from `price-compare`'s `selected` row for the line's product/currency/date. | **Confirmed (mechanism)** — via the real `price-compare` endpoint; whether the PR module's own UI actually calls it for every line is documented in the `purchase-request` module's own pass, not verified again here. |
| `VPL_XMOD_002` | [purchase-request](/en/inventory/purchase-request) | When no active pricelist covers a product, the PR line is captured with `pricelist_type = manual_input` (`enum_pricelist_compare_type`). | **Confirmed (schema)** — the enum and the PR-line field are real; documented in the `purchase-request` module. |
| `VPL_XMOD_003` | [purchase-order](/en/inventory/purchase-order) | PO conversion snapshots the price at the point of PR-to-PO conversion rather than holding a live FK. | **Confirmed** — matches the already-documented PO-module finding; no live re-read of the pricelist happens after conversion. |
| `VPL_XMOD_004` | [purchase-order](/en/inventory/purchase-order) | A PO line diverging from the active pricelist beyond a tenant tolerance routes to a "high-value" approval stage. | **Design-target — removed.** The PO module's own resync pass already confirmed zero `threshold` hits for this mechanism (`PO_AUTH_004`/`PO_XMOD_006`). |
| `VPL_XMOD_005` | [good-receive-note](/en/inventory/good-receive-note) | GRN posting can compare its unit price against the active pricelist and flag variance. | **Unconfirmed here** — read this module's own claim with the GRN module's own resync findings; this pass did not re-verify GRN-side code. |
| `VPL_XMOD_006` | [product](/en/inventory/product) | Every `tb_pricelist_detail.product_id` references `tb_product`; a soft-deleted product's existing pricelist rows remain queryable. | **Confirmed (schema)** — `onDelete: NoAction`, soft-delete pattern consistent with the rest of the schema. |
| `VPL_XMOD_007` | Vendor | An inactive vendor should not be invitable to new RFQs or have new pricelists created. | **Design-target** — no `is_active` check on vendor was found in `request-for-pricing.service.ts create()` or `price-list.service.ts create()`. |
| `VPL_XMOD_008` | Currency master | Pricelist values are stored in whatever currency was picked; cross-currency comparison, if needed, is a downstream concern. | **Confirmed (by absence)** — see `VPL_CALC_005`. |
| `VPL_XMOD_009` | Validation engine | A format/completeness/business-rule/quality-scoring engine validates every submission. | **Removed — no code.** See § 2 and § 3 above; the closest real analogue is ordinary Zod field validation on the frontend form. |

## 7. References

- Frontend: `../carmen-inventory-frontend-react/routes/vendor-management/` (vendor, price-list, price-list-template, request-price-list) and `routes/external/pl/` (vendor portal).
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/master/price-list/price-list.service.ts`, `.../price-list-template/price-list-template.service.ts`, `.../request-for-pricing/request-for-pricing.service.ts`, `.../check-price-list/check-price-list.service.ts`; gateway controllers under `apps/backend-gateway/src/application/pricelists/`, `pricelist-templates/`, `request-for-pricings/`.
- Prisma: `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (`tb_pricelist*`, `tb_pricelist_template*`, `tb_request_for_pricing*`).
- `../carmen/docs/vendor-pricelist-management/` — retained as the source for every rule labelled **Design-target**; treat it as an aspirational spec, not a description of current behaviour.
- E2E: `../carmen-inventory-frontend-e2e/tests/150-vendor.spec.ts`, `159-pl.spec.ts`, `160-pl-template.spec.ts`.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical Prisma model and the § 5 divergence table this page's status labels are drawn from.
- Related modules: [purchase-request](/en/inventory/purchase-request) (`VPL_XMOD_001`–`VPL_XMOD_002`), [purchase-order](/en/inventory/purchase-order) (`VPL_XMOD_003`–`VPL_XMOD_004`), [good-receive-note](/en/inventory/good-receive-note) (`VPL_XMOD_005`), [product](/en/inventory/product) (`VPL_XMOD_006`).
