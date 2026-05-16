---
title: Vendor Pricelist — Business Rules
description: Validation, calculation, authorization, status transitions, and cross-module rules for vendor-pricelist.
published: true
date: 2026-05-17T11:00:00.000Z
tags: vendor-pricelist, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Business Rules

> **At a Glance**
> **Rule families:** `VPL_VAL_*` validation &nbsp;·&nbsp; `VPL_AUTH_*` permission &nbsp;·&nbsp; `VPL_CALC_*` calc &nbsp;·&nbsp; `VPL_POST_*` posting &nbsp;·&nbsp; `VPL_XMOD_*` cross-module
> **Rule count:** approximately 81 rules
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Status lifecycle:** Section 5.1 (where present) carries the Live UI vs BRD discrepancy callouts

## 1. Overview

This page captures the operational business rules that govern the three tiers of the vendor-pricelist module — **templates** (`tb_pricelist_template`), **request-for-pricing campaigns** (`tb_request_for_pricing`), and **vendor pricelists** (`tb_pricelist`) — through their respective lifecycles. The rule families are: input validation at create / edit / submit time, MOQ-tier validation across multiple rows per product, monetary calculation (line-level price decomposition; effective unit price per base UoM; multi-currency display), authorization gates by role (Purchaser / Manager / Vendor / Finance / Sysadmin / Auditor), status transitions on `enum_pricelist_template_status` and `enum_pricelist_status`, portal-token policy (expiration, IP, sessions), validation-engine semantics (format, completeness, business rules, quality score), and cross-module rules with [[purchase-request]] (price defaulting from preferred vendor pricelist), [[purchase-order]] (price snapshot + deviation tracking), [[good-receive-note]] (price-variance check), and [[product]] (referenced from every detail row).

Rules below are synthesised from the carmen/docs vendor-pricelist documents (`design.md`, `requirements.md`, `price-assignment-workflow-documentation.md`, `VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md`, `VENDOR_MANAGEMENT_TECHNICAL_SPECIFICATION.md`) and the canonical Prisma data model in [[vendor-pricelist/01-data-model]]. Where carmen/docs and Prisma disagree, **Prisma is canonical for entities, fields, and enum values**; carmen/docs is canonical for workflow semantics, rule descriptions, and policy that the application layer enforces on top of the leaner Prisma schema — in particular the campaign status (`draft` / `active` / `paused` / `completed` / `cancelled`) and invitation submission status (`pending` / `in-progress` / `submitted` / `approved` / `expired`) are application-layer derivations because Prisma has no dedicated columns for them ([[vendor-pricelist/01-data-model]] § 5 catalogues the 12 material divergences).

## 2. Validation Rules

Rule IDs follow `VPL_VAL_NNN`. Template rules (001–007) run on the template create / edit / activate path; campaign rules (008–013) on the request-for-pricing create / send-invitation path; pricelist rules (014–025) on the vendor submission / purchaser approval path. Where a Prisma `@@unique` index is the final guard, the validation message is delivered at the application layer with the DB index as the fallback.

| Rule ID | Tier | Condition | When enforced | Error / behaviour |
| ------- | ---- | --------- | ------------- | ----------------- |
| `VPL_VAL_001` | Template | `tb_pricelist_template.name` is non-empty and unique among non-soft-deleted rows (`@@unique([name, deleted_at])`). | Create, edit, activate | Reject with "Template name is required and must be unique." DB-level fallback via the unique index `pricelist_template_name_deletedat_u`. |
| `VPL_VAL_002` | Template | `tb_pricelist_template.status ∈ enum_pricelist_template_status (draft, active, inactive)`. Activate transition (`draft → active`) requires at least one `tb_pricelist_template_detail` row. | Activate | Reject with "Template must contain at least one product before it can be activated." |
| `VPL_VAL_003` | Template | `tb_pricelist_template.currency_id` references a non-soft-deleted `tb_currency` row when set. | Save | Reject with "Default currency must be a valid, active currency." Currency on the template is a default — the vendor may select a different submission currency on the pricelist itself. |
| `VPL_VAL_004` | Template | `tb_pricelist_template.validity_period > 0` when set; days-to-deadline values in `reminder_days` are positive and strictly decreasing (e.g., `[14, 7, 3, 1]`). | Save | Reject with "Validity period must be positive and reminder schedule must be strictly decreasing." |
| `VPL_VAL_005` | Template | Each `tb_pricelist_template_detail.product_id` references an active, non-soft-deleted `tb_product`; `@@unique([pricelist_template_id, product_id, deleted_at])` prevents duplicate products on the same template. | Save line | Reject with "Product is required and may only appear once per template." DB fallback via unique index. |
| `VPL_VAL_006` | Template | `tb_pricelist_template_detail.order_unit_obj` carries a `default_order` object and at least one MOQ tier; each MOQ tier has `unit_id`, `unit_name`, and `qty > 0`; MOQ `qty` values are strictly increasing across tiers (sorted at save). | Save line | Reject with "Order unit and at least one MOQ tier with positive quantity are required; MOQ quantities must be strictly increasing." |
| `VPL_VAL_007` | Template | `tb_pricelist_template.escalation_after_days >= 0`. Cannot escalate before deadline. | Save | Reject with "Escalation days must be non-negative." |
| `VPL_VAL_008` | Campaign | `tb_request_for_pricing.name` is non-empty and unique among non-soft-deleted rows (`@@unique([name, deleted_at])`). | Create, edit | Reject with "Campaign name is required and must be unique." |
| `VPL_VAL_009` | Campaign | `tb_request_for_pricing.pricelist_template_id` references a `tb_pricelist_template` whose `status = active`. | Create | Reject with "Campaign must reference an active template — draft or inactive templates cannot drive campaigns." |
| `VPL_VAL_010` | Campaign | `tb_request_for_pricing.start_date < end_date`; `end_date > now()` at campaign launch; `start_date` and `end_date` together cover at least one tenant-minimum response window (default 3 days, configurable). | Create, launch | Reject with "Campaign window must run for at least the tenant minimum (default 3 days) and end strictly after start; end_date must be in the future at launch." |
| `VPL_VAL_011` | Campaign | At least one `tb_request_for_pricing_detail` row exists before campaign launch; each detail row has a non-null `vendor_id` and a `contact_email` (snapshot-or-master) that is a syntactically valid email. | Launch | Reject with "Campaign must invite at least one vendor and every invited vendor must have a contact email." |
| `VPL_VAL_012` | Campaign | `tb_request_for_pricing_detail.@@unique([request_for_pricing_id, vendor_id, deleted_at])` prevents inviting the same vendor twice. | Add vendor | Reject with "Vendor has already been invited to this campaign." DB-level fallback. |
| `VPL_VAL_013` | Campaign | Email-template referenced by `email_template_id` exists in the tenant email-template registry and is not archived. | Launch | Reject with "Email template not found or archived — pick a valid template before launch." |
| `VPL_VAL_014` | Pricelist | `tb_pricelist.pricelist_no` is non-empty and unique among non-soft-deleted rows (`@@unique([pricelist_no, deleted_at])`). | Create | Reject with "Pricelist reference number is required and must be unique." DB fallback via index `pricelist_pricelist_no_u`. |
| `VPL_VAL_015` | Pricelist | `tb_pricelist.vendor_id` references an active, non-soft-deleted `tb_vendor`; `tb_pricelist.currency_id` references a non-soft-deleted `tb_currency`. | Save | Reject with "Vendor and currency are required and must reference active master-data records." |
| `VPL_VAL_016` | Pricelist | `tb_pricelist.effective_from_date < effective_to_date`; `effective_from_date >= submitted_at` (effective date cannot be in the past relative to submission, unless the template explicitly permits back-dating). | Save, submit | Reject with "Effective-from date must precede effective-to date; effective-from cannot precede submission." |
| `VPL_VAL_017` | Pricelist | `tb_pricelist.submission_method ∈ pricelist_submission_method (online, email, portal, manual)`. | Save | Reject with "Submission method must be one of online, email, portal, or manual." |
| `VPL_VAL_018` | Pricelist | Each `tb_pricelist_detail.product_id` references an active, non-soft-deleted `tb_product`; the product must also be present on the template referenced by the campaign that issued the invitation (vendor cannot quote a product not asked for). | Save line | Reject with "Product is required and must appear on the issuing template." |
| `VPL_VAL_019` | Pricelist | `tb_pricelist_detail.@@unique([pricelist_id, product_id, unit_id, moq_qty, deleted_at])` permits multiple rows per `(pricelist, product, unit)` distinguished by `moq_qty`. Each row's `moq_qty >= 0`. | Save line | Reject with "MOQ quantity is required and must be non-negative; duplicate (product, unit, MOQ) rows are not permitted." |
| `VPL_VAL_020` | Pricelist | When a product has multiple MOQ-tier rows on the same pricelist (same `product_id` + `unit_id`), the rows are auto-sorted by `moq_qty` ascending, and **higher quantities must carry equal-or-lower unit price** (`price` non-increasing as `moq_qty` increases). | Save, submit | Warn at save with "Tier MOQ 50 (฿10.50) is cheaper than MOQ 100 (฿11.00) — please review."; reject at submit with "MOQ-tier pricing must be non-increasing as MOQ quantity increases." |
| `VPL_VAL_021` | Pricelist | `tb_pricelist_detail.price_without_tax >= 0` (zero permitted but flagged for review); `tax_rate >= 0`; `tax_amt = Round(price_without_tax × tax_rate, 5)`; `price = Round(price_without_tax + tax_amt, 5)`. | Save line | Reject with "Price-without-tax must be non-negative; tax_amt and price must reconcile to the configured rounding rule (5 dp internal, 2 dp display)." |
| `VPL_VAL_022` | Pricelist | `tb_pricelist_detail.lead_time_days >= 0`; `tb_pricelist_detail.rating ∈ [0, 5]` (tenant-configurable upper bound). | Save line | Reject with "Lead time must be non-negative; rating must be within 0–5." |
| `VPL_VAL_023` | Pricelist | On submit (vendor clicks Submit), pricelist has at least one non-soft-deleted detail row; every detail row passes `VPL_VAL_018`–`VPL_VAL_022`. | Submit | Reject with "Pricelist must contain at least one valid line item to submit." |
| `VPL_VAL_024` | Pricelist | Status transitions follow the state machine in § 5; out-of-order transitions are blocked. | On status change | Reject with "Invalid status transition from `<from>` to `<to>`." |
| `VPL_VAL_025` | Pricelist | After `tb_pricelist.status = active`, the pricelist header is immutable except for `status` (admin can move to `inactive`) and the comment / activity-log surfaces; detail-row edits require either an administrative override or a new pricelist (issued under a fresh campaign). | Edit on active | Reject with "Active pricelist is immutable — open a new pricelist via a fresh campaign, or move this pricelist to inactive first." |

## 3. Calculation Rules

All monetary values are stored as `Decimal(20, 5)` at the row level; tax rates use `Decimal(15, 5)`. Display rounding is half-up (banker's rounding for ties on .5) to 2 decimals for currency, 3 decimals for quantities, and 5 decimals for rates. Intermediate computations always re-read the rounded value of the prior step.

Rule IDs follow `VPL_CALC_NNN`.

| Rule ID | Formula |
| ------- | ------- |
| `VPL_CALC_001` (line tax amount) | `tax_amt = Round(price_without_tax × tax_rate, 5)` per `tb_pricelist_detail`. |
| `VPL_CALC_002` (line gross price) | `price = Round(price_without_tax + tax_amt, 5)`. |
| `VPL_CALC_003` (effective unit price per base UoM) | For an MOQ-tier row at `(unit_id, moq_qty, price)`: `effective_unit_price = Round(price ÷ unit.conversion_factor_to_base, 5)`. The `conversion_factor_to_base` is resolved at lookup time from `tb_unit`, not stored on the pricelist row. Display rounding to 2 dp on render. |
| `VPL_CALC_004` (tier comparison) | When a product carries multiple MOQ-tier rows on the same pricelist, the rows are sorted by `moq_qty` ascending at save; the application asserts `price[i+1] <= price[i]` for adjacent rows after sort (`VPL_VAL_020`). For comparison reports across vendors, the effective unit price per base UoM (`VPL_CALC_003`) is the comparable value. |
| `VPL_CALC_005` (multi-currency display) | Pricelist values are stored in `tb_pricelist.currency_id` (the vendor's chosen submission currency); no FX conversion is stored on the row. Comparison and reporting convert to a target currency at display time using the tenant FX rate at the report's as-of date — the stored pricelist price is never mutated for FX. |
| `VPL_CALC_006` (quality score — application layer, stored in `info`) | `quality_score ∈ [0, 100] = w1 × completeness_pct + w2 × business_rule_pass_pct + w3 × format_correctness_pct + w4 × vendor_reliability_score`, with tenant-configurable weights (defaults `0.30 / 0.40 / 0.15 / 0.15`). Stored as `info.quality_score` on `tb_pricelist`. |
| `VPL_CALC_007` (validity countdown for portal display) | `days_remaining = floor((effective_to_date − now()) ÷ 1 day)` rendered on the vendor portal and on the purchaser's open-pricelists dashboard. |
| `VPL_CALC_008` (rounding mode) | Half-up (banker's) mode for all monetary and rate rounding; regional number formatting is applied at presentation only, not at storage. |

### 3.1 Worked example — multi-MOQ pricing on one product

Vendor `V1` submits a pricelist for product `P1` (`unit = Each`, conversion to base `Each = 1`) at three MOQ tiers in `currency_id = THB`, `tax_rate = 0.07000`:

- Tier 1: `moq_qty = 1`, `unit_id = Each`, `price_without_tax = ฿12.50`.
  - `tax_amt = Round(12.50 × 0.07, 5) = ฿0.87500`
  - `price = Round(12.50 + 0.87500, 5) = ฿13.37500`
  - `effective_unit_price_per_base = Round(13.37500 ÷ 1, 5) = ฿13.37500`
- Tier 2: `moq_qty = 50`, `unit_id = Each`, `price_without_tax = ฿10.50`.
  - `tax_amt = ฿0.73500`; `price = ฿11.23500`; `effective_unit_price_per_base = ฿11.23500`
- Tier 3: `moq_qty = 100`, `unit_id = Each`, `price_without_tax = ฿9.75`.
  - `tax_amt = ฿0.68250`; `price = ฿10.43250`; `effective_unit_price_per_base = ฿10.43250`

Validation `VPL_VAL_020` passes — `price` is strictly decreasing across the three tiers (`13.375 > 11.235 > 10.4325`). If Tier 3 were quoted at `฿11.00` (above Tier 2), the save warns and submit rejects.

If `V1` also offers the same product at `unit = Box of 12` (`tb_unit.conversion_factor_to_base = 12`) at `moq_qty = 1`, `price_without_tax = ฿138.00`, then `effective_unit_price_per_base = Round(138.00 ÷ 12, 5) = ฿11.50000` — **comparable** to the `Each` MOQ-tier prices above. The schema stores the row in the vendor's quoting unit (`Box`); comparison happens via `VPL_CALC_003`.

## 4. Authorization Rules

Rule IDs follow `VPL_AUTH_NNN`. Authorization is enforced by RBAC at the API layer; the rules below identify the policy, not the implementation. Role names mirror the carmen/docs RBAC table. "High-value" or "multi-currency" thresholds for Manager-only approval are tenant-configurable.

| Rule ID | Subject | Right | Constraint |
| ------- | ------- | ----- | ---------- |
| `VPL_AUTH_001` | Purchaser / Purchasing Staff | Create / edit / activate / inactivate `tb_pricelist_template` | Both `status = draft` and `status = active` may be edited; activate requires `VPL_VAL_002`. |
| `VPL_AUTH_002` | Purchaser | Create / edit / launch `tb_request_for_pricing` (campaign) | Launch requires `VPL_VAL_009`–`VPL_VAL_013`; only the campaign creator or a member of the procurement-team role may edit a campaign mid-flight. |
| `VPL_AUTH_003` | Purchaser | Manually upload an emailed pricelist (`tb_pricelist.submission_method = email`) on the vendor's behalf | Permitted; the upload writes a `system` comment on the pricelist recording the email source, the staff member who uploaded, and the original email reference. |
| `VPL_AUTH_004` | Purchaser | Review and approve submitted pricelist (`draft → active`) | Below the tenant high-value threshold; high-value pricelists route to the Purchasing Manager per `VPL_AUTH_005`. |
| `VPL_AUTH_005` | Purchasing Manager | Approve high-value or multi-currency pricelist; configure business rules for preferred-vendor and price-assignment logic | Required for pricelists exceeding the tenant high-value threshold or covering multi-currency cross-border deals. Also holds sign-off on the preferred-vendor flag toggle (`tb_pricelist_detail.is_preferred`). |
| `VPL_AUTH_006` | Purchasing Manager | Reject submitted pricelist with reason | Returns the pricelist to vendor (status remains `draft` with a `system` rejection comment in `tb_pricelist_comment`); vendor receives an email with the rejection reason and may resubmit through the same portal token (if not expired). |
| `VPL_AUTH_007` | Vendor (external) | Access portal via `pricelist_url_token`; draft, save, resubmit pricelist | Token must be unexpired (not past `tb_request_for_pricing.end_date` and not revoked); IP must match the configured allowlist if one is set; session limit enforced (default 5 concurrent sessions per token). |
| `VPL_AUTH_008` | Vendor | Choose submission currency; supply MOQ tiers with units and conversion factors | Currency must be in the tenant's permitted-currency list; conversion factor is read from `tb_unit` master data, not vendor-supplied as a free-form value. |
| `VPL_AUTH_009` | Finance Officer / Accounts Payable | Read pricelist for variance audit | Read-only across all pricelists, campaigns, and invitations; cannot edit or change status. |
| `VPL_AUTH_010` | Finance Manager | Sign off on multi-currency or high-value pricelist | Co-approval right alongside the Purchasing Manager when configured; gates the `draft → active` transition for the multi-currency case. |
| `VPL_AUTH_011` | Receiver / Store Keeper | Indirect consumer — no module write right | Read access via [[good-receive-note]] variance check; cannot edit pricelists. |
| `VPL_AUTH_012` | System Administrator | Configure pricelist numbering scheme, RBAC, template / campaign settings, portal token policy (expiration, IP restrictions, session limits), email integration, validation rules | Cannot create or approve pricelists; cannot transact in the module. Can revoke portal tokens by setting `tb_request_for_pricing_detail.pricelist_url_token = NULL` and writing a `system` comment, which immediately invalidates the vendor's portal access. |
| `VPL_AUTH_013` | Auditor | Read-only across pricelists, campaigns, invitations, submission history, validation results, and activity log | No write surface; cannot approve, reject, void, or amend. Exports of sensitive fields (full vendor identities, pricing snapshots, portal-token telemetry) require secondary export approval per tenant data-export policy. |
| `VPL_AUTH_014` | Segregation of duties | Vendor ≠ Purchaser; Purchaser ≠ Approver (for high-value) | A user holding the vendor portal token cannot also approve the pricelist; the user who created or substantially edited a high-value pricelist's detail rows must not be the same user who approves it. Enforced at status transition. |
| `VPL_AUTH_015` | Token revocation | System Administrator OR Purchasing Manager may revoke a `pricelist_url_token` | Revocation is immediate; subsequent portal access with the revoked token returns `401 — token revoked`. Re-issue requires sending a new invitation with a fresh token; the original invitation row remains for audit. |

## 5. Status / Posting Rules

The module has three status enums with distinct lifecycles, plus the application-derived campaign and invitation statuses.

### 5.1 Template lifecycle (`enum_pricelist_template_status`)

States: `draft`, `active`, `inactive`. Rule IDs `VPL_POST_001`–`VPL_POST_004`.

| Rule ID | Transition | Effects |
| ------- | ---------- | ------- |
| `VPL_POST_001` | Create (→ `draft`) | Insert `tb_pricelist_template` with `status = draft`, `doc_version = 0`. Detail rows can be added / edited freely. Cannot drive a campaign while `draft`. |
| `VPL_POST_002` | Activate (`draft → active`) | Requires `VPL_VAL_002`–`VPL_VAL_007`. Sets `status = active`; the template is now selectable as the source for new `tb_request_for_pricing` rows. A `system` comment is appended in `tb_pricelist_template_comment` recording the activation. |
| `VPL_POST_003` | Inactivate (`active → inactive`) | Sets `status = inactive`. The template can no longer drive new campaigns; existing campaigns continue under their snapshotted reference. |
| `VPL_POST_004` | Re-activate (`inactive → active`) | Allowed when the template's referenced products and currency are still valid; if any product is now soft-deleted, the activate is rejected with a list of affected products. |

### 5.2 Campaign lifecycle (application-derived from `start_date`, `end_date`, and detail-side pricelist counts)

Per [[vendor-pricelist/01-data-model]] § 5 item 2, there is **no Prisma column for campaign status**. The application derives the status as follows. Rule IDs `VPL_POST_005`–`VPL_POST_009`.

| Rule ID | Derived state | Condition | Effects |
| ------- | ------------- | --------- | ------- |
| `VPL_POST_005` | `draft` | `tb_request_for_pricing` exists with `start_date IS NULL` OR `start_date > now()` and no detail row has dispatched an invitation email. | Campaign is being prepared; vendors not yet contacted; can edit freely. |
| `VPL_POST_006` | `active` | `start_date <= now() < end_date` AND at least one detail row has dispatched an invitation. | Campaign is live; vendors can access portal via token; reminders fire per template schedule. |
| `VPL_POST_007` | `paused` | Application-set flag (in `info` JSON on `tb_request_for_pricing`) suppresses reminders and locks new invitations; existing portal tokens remain valid. | Used when purchasing temporarily halts a campaign (e.g., template error discovered). Detail rows retain their `pricelist_url_token`; vendors can still submit if they wish. |
| `VPL_POST_008` | `completed` | `now() >= end_date` OR every detail row has its linked `tb_pricelist.status = active`. | Campaign window closed; reminders suppressed; portal tokens may be revoked by `VPL_AUTH_015`. |
| `VPL_POST_009` | `cancelled` | Application-set flag (in `info` JSON) records cancellation with a `system` comment in `tb_request_for_pricing_comment`. | Used when a campaign is abandoned before completion. All portal tokens revoked; vendors notified by email. |

### 5.3 Invitation lifecycle (application-derived from `tb_pricelist.status` and `submitted_at`)

Per [[vendor-pricelist/01-data-model]] § 5 item 4. Rule IDs `VPL_POST_010`–`VPL_POST_014`.

| Rule ID | Derived state | Condition |
| ------- | ------------- | --------- |
| `VPL_POST_010` | `pending` | `tb_request_for_pricing_detail.pricelist_id IS NULL` AND no portal access recorded. |
| `VPL_POST_011` | `in-progress` | Portal access recorded (first-access `system` comment present) OR linked `tb_pricelist` exists with `status = draft` and `submitted_at IS NULL`. |
| `VPL_POST_012` | `submitted` | Linked `tb_pricelist.submitted_at IS NOT NULL` AND `tb_pricelist.status = draft` (awaiting purchaser approval). |
| `VPL_POST_013` | `approved` | Linked `tb_pricelist.status = active`. |
| `VPL_POST_014` | `expired` | Campaign `end_date < now()` AND linked `tb_pricelist.submitted_at IS NULL`. Portal token is revoked automatically by the cron job. |

### 5.4 Pricelist lifecycle (`enum_pricelist_status`)

States: `draft`, `active`, `inactive`, `expired`. Rule IDs `VPL_POST_015`–`VPL_POST_022`.

| Rule ID | Transition / Event | Effects |
| ------- | ------------------ | ------- |
| `VPL_POST_015` | Create (→ `draft`) | Vendor first saves at the portal: insert `tb_pricelist` with `status = draft`, `doc_version = 0`, snapshot `vendor_id` / `currency_id` from invitation; FK `tb_request_for_pricing_detail.pricelist_id` is populated. Auto-save fires every 30 s thereafter. |
| `VPL_POST_016` | Submit (`draft → draft` with `submitted_at` written) | Vendor clicks Submit at portal: validator runs (`VPL_VAL_018`–`VPL_VAL_023`); on pass, `submitted_at = now()`, a `system` comment is appended on `tb_pricelist_comment` recording submission, the quality score is computed (`VPL_CALC_006`) and written to `info`, and the purchaser is notified for review. Status remains `draft` until purchaser approval — the carmen/docs `submitted` / `under-review` states are this `draft + submitted_at IS NOT NULL` window. |
| `VPL_POST_017` | Approve (`draft → active`) | Purchaser approves: requires `VPL_AUTH_004` (or `VPL_AUTH_005` for high-value, plus `VPL_AUTH_010` for multi-currency). Sets `status = active`; the pricelist is now the live reference for downstream PR / PO / GRN within its validity window. Approval `system` comment appended. |
| `VPL_POST_018` | Reject (`draft → draft` with `system` rejection comment) | Purchaser rejects via `VPL_AUTH_006` with reason: pricelist stays at `draft`, `submitted_at` is reset to `NULL`, a `system` comment captures the reason, and the vendor is emailed for resubmission. Vendor can resubmit through the same portal token until expiry. |
| `VPL_POST_019` | Inactivate (`active → inactive`) | Purchaser or Sysadmin moves an active pricelist to `inactive` (e.g., vendor flagged for compliance review). Downstream PR / PO / GRN treat the pricelist as historical-only from this point. Inactivation `system` comment appended. |
| `VPL_POST_020` | Re-activate (`inactive → active`) | Allowed within the validity window only. Outside the window, the system rejects the re-activation and requires a new pricelist (via a fresh campaign). |
| `VPL_POST_021` | Auto-expire (`active → expired`) | Background cron: when `now() > effective_to_date` AND `status = active`, set `status = expired`. Auto-expiry `system` comment is appended. The pricelist remains queryable for historical reporting; PR / PO / GRN downstream no longer treat it as live. |
| `VPL_POST_022` | Soft delete | `deleted_at = now()`, `deleted_by_id = user`. Permitted only at `draft` (before approval); active pricelists cannot be soft-deleted because PR / PO / GRN downstream may reference them. All unique indexes include `deleted_at` so a new pricelist can reuse the same `pricelist_no`. |

State diagram (Prisma-canonical):

```
[*] → draft → (submitted_at written) → draft → active → inactive → active (within window)
                                          ↓        ↓
                                       (reject)  expired (auto, when now > effective_to_date)
                                          ↓
                                        draft
```

`expired` and `inactive` are recoverable to `active` (`expired` requires fresh validity dates via a new pricelist; `inactive` re-activates within window). `draft` accepts soft-delete; `active` / `inactive` / `expired` retain audit history.

## 6. Cross-Module Rules

Rule IDs follow `VPL_XMOD_NNN`.

| Rule ID | Related module | Rule |
| ------- | -------------- | ---- |
| `VPL_XMOD_001` | [[purchase-request]] | PR line creation defaults the unit price from the **preferred vendor's active pricelist** for the `(product_id, currency_id)` tuple, sized to the PR-line MOQ via `VPL_CALC_004`. Preferred vendor is resolved per `is_preferred = true` on `tb_pricelist_detail` (or via the business-rules engine documented in carmen/docs `price-assignment-workflow-documentation.md`). The PR line stores `pricelist_detail_id` as a back-reference and `pricelist_type ∈ enum_pricelist_compare_type (automatic, manual_select, manual_input)` to record how the price was acquired. |
| `VPL_XMOD_002` | [[purchase-request]] | When no active pricelist exists for the product, the PR line is created with `pricelist_type = manual_input`, the price is captured free-form, and a `system` comment is appended on the PR flagging missing pricelist coverage. The Purchaser is expected to either raise a campaign to collect coverage or override the manual price during approval. |
| `VPL_XMOD_003` | [[purchase-order]] | At PR-to-PO conversion, the PO line snapshots `price` from the PR line's `pricelist_detail_id` (the price in force at PR creation). If the active pricelist has changed between PR creation and PO conversion, the system surfaces the deviation against the **current** pricelist price for the Purchaser's review. The PO line stores the snapshotted price, not a live FK — the pricelist may change without affecting the PO. Reference: `PO_XMOD_005` in [[purchase-order/02-business-rules]] § 6. |
| `VPL_XMOD_004` | [[purchase-order]] | When the PO line price diverges from the active pricelist beyond the tenant tolerance (default ±5%), the PO is routed to a high-value approval stage even if `total_amount` is below the threshold. The deviation is logged in `tb_purchase_order_detail_comment` and surfaces as a vendor-pricelist deviation entry. Reference: `PO_XMOD_006`. |
| `VPL_XMOD_005` | [[good-receive-note]] | At GRN posting, the unit price on the GRN line is compared against the active pricelist price for the `(vendor_id, product_id, unit_id, qty bracket)` tuple. Variance beyond the tenant tolerance is flagged as a variance comment on the GRN and creates a deviation entry on the vendor / vendor-pricelist side, feeding pricelist-deviation analytics. |
| `VPL_XMOD_006` | [[product]] | Every `tb_pricelist_detail.product_id` references `tb_product`. If a product is soft-deleted while it has active pricelist rows, the rows remain queryable but the product picker filters the product out for new pricelists. The application surfaces orphaned pricelist rows in the data-hygiene report for Purchasing review. |
| `VPL_XMOD_007` | Vendor master (`tb_vendor`) | A vendor flagged as inactive (`tb_vendor.is_active = false`) or soft-deleted cannot be invited to new campaigns and cannot have new pricelists created. Existing active pricelists remain queryable but are surfaced for review; the application may auto-inactivate (`VPL_POST_019`) on vendor inactivation per tenant policy. |
| `VPL_XMOD_008` | Currency master (`tb_currency`) | Pricelist values are stored in the vendor-chosen `currency_id` and are **not** mutated by FX moves. Cross-vendor and cross-currency comparison applies the tenant FX rate at the report's as-of date (`VPL_CALC_005`). FX rate sourcing is the System Administrator's configuration concern. |
| `VPL_XMOD_009` | Validation engine (application layer) | Every submitted pricelist is validated by the validation engine running format checks (price formats, currency consistency), business-rule checks (MOQ-tier non-increasing, lead-time bounds, deduplicate product+unit+MOQ), completeness checks (required fields populated, all template products covered), and quality scoring (`VPL_CALC_006`). The output is written to `tb_pricelist.info` as `validation_results` (structured object) and `quality_score` (numeric). Quality score below the tenant threshold (default 70) routes the pricelist to Purchasing Manager review rather than auto-approve. |

## 7. References

- `../carmen/docs/vendor-pricelist-management/design.md` — 6-phase architecture, component breakdown, and TypeScript interfaces used as the carmen/docs basis for cross-checking each rule family above.
- `../carmen/docs/vendor-pricelist-management/requirements.md` — 30+ functional requirements; mapped to validation rules in Section 2, authorization rules in Section 4, and cross-module rules in Section 6.
- `../carmen/docs/vendor-pricelist-management/price-assignment-workflow-documentation.md` — business-rules-engine specification: rule categories, conditions, actions, and the real-time assignment logic that drives `VPL_XMOD_001`–`VPL_XMOD_004` on the consuming-module side.
- `../carmen/docs/vendor-pricelist-management/VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md` — vendor portal features used in `VPL_AUTH_007`–`VPL_AUTH_008` and `VPL_POST_015`–`VPL_POST_016`.
- `../carmen/docs/vendor-pricelist-management/VENDOR_MANAGEMENT_TECHNICAL_SPECIFICATION.md` — RBAC matrix used in Section 4.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical Prisma model, enum values, the multi-MOQ-per-product unique key on `tb_pricelist_detail`, and the divergence table that Section 5 derivations rely on.
- Backend rule implementation (when added): `../carmen-turborepo-backend-v2/apps/` — the vendor-pricelist service module is the implementation hook for these rules (validation engine, quality scorer, campaign-status derivation, token middleware, cron jobs for auto-expire).
- Related modules: [[purchase-request]] (`VPL_XMOD_001`–`VPL_XMOD_002`), [[purchase-order]] (`VPL_XMOD_003`–`VPL_XMOD_004`), [[good-receive-note]] (`VPL_XMOD_005`), [[product]] (`VPL_XMOD_006`).
