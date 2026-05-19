---
title: Vendor Pricelist — User Flow — Finance
description: Finance's flow within the vendor-pricelist module — variance audit against posted GRN/invoice, currency/FX validation, multi-currency sign-off.
published: true
date: 2026-05-19T23:55:00.000Z
tags: vendor-pricelist, user-flow, finance, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow — Finance

> **At a Glance**
> **Persona:** Finance Officer / AP + Finance Manager &nbsp;·&nbsp; **Module:** [vendor-pricelist](/en/inventory/vendor-pricelist) &nbsp;·&nbsp; **Workflow stages:** off-path — multi-currency / high-value pre-activation co-approve + post-receipt variance audit &nbsp;·&nbsp; **Key permissions:** read across pricelists, co-approve multi-currency / high-value, audit GRN / invoice variance, no direct status write
> **What this persona does:** Audits price variance against posted GRN / invoice, validates currency / FX, and co-signs multi-currency or high-value activations.

## 1. Role in This Module

The **Finance** persona covers the **Finance Officer / Accounts Payable** clerk who audits price variance between active pricelists and posted GRN / invoice lines, validates currency and exchange-rate handling, and reconciles negotiated vs realised pricing, plus the **Finance Manager** who reviews variance reports and vendor performance, validates the financial impact of multi-currency pricelists, and exercises co-approval authority on multi-currency or high-value pricelists alongside the Purchasing Manager. Finance has **no write surface on the pricelist itself** — `VPL_AUTH_009` is read-only across pricelists, campaigns, and invitations; Finance cannot edit, approve, or change pricelist status alone. The Finance Manager's **co-approval right** on multi-currency pricelists (`VPL_AUTH_010`) is exercised through a Finance-stage signoff in the approval workflow, but the actual `VPL_POST_017` status flip is recorded against the Purchaser / Purchasing Manager; Finance Manager's signoff is captured as a `system` comment in `tb_pricelist_comment`. Finance's primary touch point is **post-receipt variance audit** — when GRN / invoice posting in the downstream procure-to-pay chain surfaces a price gap against the active pricelist (per [purchase-order/02-business-rules](/en/inventory/purchase-order/02-business-rules) § `PO_POST_009` three-way-match failure, or [vendor-pricelist/02-business-rules](/en/inventory/vendor-pricelist/02-business-rules) § `VPL_XMOD_005`), Finance investigates whether the gap is (a) within tenant tolerance — proceed to post AP at the invoiced price with a purchase-price-variance (PPV) entry, (b) outside tolerance — route the discrepancy back to the Purchaser for resolution (credit note, amendment, or pricelist re-collection), or (c) caused by an FX move on the cross-currency posting — recorded as a realised FX gain / loss. The PO module documents the operational mechanics of the three-way match; this page covers the **vendor-pricelist-side** of the same flow: how Finance reads the active pricelist to anchor the audit, what feedback Finance writes back to the pricelist module (variance entries, deviation analytics), and how Finance signs off on multi-currency pricelist activation.

## 2. Entry Point and Primary Flow

Finance has two flows in this module, addressed separately below.

### 2.1. Multi-currency / high-value pre-activation sign-off (Finance Manager)

**Entry point:** Finance Manager is added as a co-approver on the approval workflow stage for any submitted pricelist whose currency differs from the tenant base currency and whose projected aggregate value crosses the cross-border-FX threshold, OR whose aggregate value crosses the high-value approval threshold regardless of currency. Entry is via the **Finance review queue** notification when the pricelist enters this stage.

**Primary flow (4 steps):**

1. **Open the pricelist from the review queue.** The screen shows the **Header** (vendor, currency, validity dates, submission method), the **Detail Rows** (product, unit, MOQ, price-without-tax, tax, lead-time), the **Validation Panel** (engine output written to `tb_pricelist.info.validation_results` + `quality_score` per `VPL_CALC_006`), and the **Activity Log**.
2. **Verify financial integrity.** Confirm `currency_id` matches the vendor's contracted currency (or a tenant-approved alternative for dual-currency vendors); verify the tenant FX rate source can quote `currency_id ↔ tenant_base_currency` for the validity window of the pricelist; check that the tax rates on detail rows reconcile with the vendor's tax registration and product tax profiles per `VPL_CALC_001`–`VPL_CALC_002`.
3. **Spot-check the aggregate financial impact.** Compute projected spend = `Σ (effective_unit_price_per_base_uom × historical_demand_by_product)` over the validity window; verify the projection is consistent with the Purchasing Manager's high-value threshold rationale; ensure no single line carries an order-of-magnitude outlier that the validator did not catch.
4. **Sign off or send-back.**
   - **Sign off:** post a Finance signoff `system` comment on `tb_pricelist_comment`. The workflow advances; if the Purchaser / Purchasing Manager has already signed off, `VPL_POST_017` fires and the pricelist activates. Otherwise the workflow continues to wait on the Purchaser side.
   - **Send-back:** post a Finance objection with reason text. Pricelist returns to `draft + submitted_at = NULL` per `VPL_POST_018`; vendor is notified for resubmission with the Finance-side rationale visible to the Purchaser. The send-back is a hard veto on multi-currency activation; the Purchaser cannot override Finance on this gate.

### 2.2. Post-receipt variance audit (Finance Officer / AP)

**Entry point:** GRN posting or three-way-match in the downstream PO / AP chain flags a price variance against the active pricelist. The variance event surfaces in the **Pricelist Variance** dashboard (a Finance-side report joining `tb_pricelist_detail` to posted `tb_good_received_note_detail` and AP invoice records). Each row shows the vendor, product, pricelist price, GRN / invoice price, magnitude (absolute and percentage), and the linked PO / GRN / invoice ids.

**Primary flow (6 steps):**

1. **Open the variance dashboard.** Filter by vendor, product, period, magnitude, or PO / GRN reference. Each row drills into the underlying transaction chain.
2. **Drill into one variance.** Open a variance row; the detail view shows the **active pricelist row** (`tb_pricelist_detail` with price, MOQ, unit, validity), the **GRN line** (received qty, GRN unit price, GRN-posting actor and timestamp), and the **invoice line** (vendor invoice number, invoice qty, invoice unit price, three-way-match outcome).
3. **Categorise the variance.** Three categories:
   - **Within tolerance (auto-pass on the PO three-way-match side):** the variance fell inside the tenant price tolerance band, the PO match passed (per [purchase-order/02-business-rules](/en/inventory/purchase-order/02-business-rules) § `PO_POST_008`), and AP was posted at the invoiced price with a PPV entry. Finance Officer's role here is reconciliation review only; no action on the pricelist.
   - **Outside tolerance, vendor over-billed:** PO match failed (per `PO_POST_009`); invoice held in dispute; Finance Officer pursues a credit note from the vendor through the Purchaser. No action on the pricelist itself unless the over-billing reveals a systematic pattern (multiple vendors / products), in which case Finance escalates to the Purchasing Manager for pricelist re-collection.
   - **Outside tolerance, pricelist out-of-date:** the pricelist price no longer reflects market reality (e.g., commodity spike), and the vendor is invoicing at the new market rate. Finance Officer files a variance memo, routes to the Purchaser, and recommends pricelist inactivation + re-collection. Finance does not directly inactivate (no write right per `VPL_AUTH_009`); the Purchaser executes `VPL_POST_019` after review.
4. **Verify currency / FX handling.** For cross-currency invoices, confirm the FX rate used at posting matches the tenant FX policy at the invoice date; confirm the FX gain / loss entry on AP is correctly classified. Pricelist values stored in vendor currency per `VPL_CALC_005` are never mutated for FX — the FX impact lives on the AP-posting side.
5. **Write back to the pricelist.** When the variance categorisation is complete, Finance writes a `system` comment on `tb_pricelist_comment` (and on the affected `tb_pricelist_detail_comment`) referencing the GRN / invoice ids, the variance magnitude, and the categorisation. This feeds the pricelist-deviation analytics rollup that downstream PR-line preferred-vendor logic ([vendor-pricelist/02-business-rules](/en/inventory/vendor-pricelist/02-business-rules) § `VPL_XMOD_001`) and Purchasing Manager's vendor-performance scoring read.
6. **Close the variance case.** When the categorisation is recorded and any required action (credit note pursuit, pricelist re-collection request) is handed off, the variance row drops from Finance's open dashboard. The audit log retains the case file for the Auditor's chain audit.

## 3. Decision Branches

- **Co-approval split between Finance Manager and Purchasing Manager.** On a multi-currency pricelist that is also high-value, both Finance Manager (`VPL_AUTH_010`) and Purchasing Manager (`VPL_AUTH_005`) must sign off. The order is not strict — either can go first — but `VPL_POST_017` fires only when both signoff `system` comments are present. If Finance Manager signs off but Purchasing Manager rejects, the rejection wins and the pricelist returns to `draft + submitted_at = NULL`. The reverse scenario is symmetrical.
- **Finance Manager sends back on FX policy violation.** When Finance Manager review finds that the pricelist `currency_id` is not in the tenant's permitted-currency list, or that the FX rate source cannot quote the currency pair for the validity window (e.g., a thinly-traded currency without a real-time rate source), Finance vetoes activation via `VPL_POST_018`. The vendor is notified to resubmit in an approved currency. This is a hard veto — the Purchaser cannot work around it.
- **Variance reveals systematic vendor over-billing.** When the Finance Officer's variance audit shows the same vendor over-billing repeatedly across multiple PO / GRN / invoice triplets, the pattern is escalated to the Purchasing Manager. The Manager decides whether to (a) inactivate the active pricelist and re-collect, (b) trigger a contractual review with the vendor (out-of-band), or (c) revoke the vendor's preferred-vendor status by toggling all `is_preferred` flags off on the vendor's active pricelist rows. The decision is recorded on the vendor's performance profile and feeds the business-rules engine.
- **Variance reveals pricelist out-of-date due to market move.** Finance Officer routes the case to the Purchaser with a recommendation to inactivate the pricelist and launch a fresh campaign. The Purchaser executes `VPL_POST_019` and follows up with a new campaign per the Purchaser's flow Step 4. The downstream PR / PO cohort referencing the old pricelist remains under snapshot semantics; new PRs default from whichever pricelist is active at PR-creation time (could be a fallback pricelist from another vendor, or `pricelist_type = manual_input` per `VPL_XMOD_002` if coverage is now missing).
- **Variance attributed to FX move on a cross-currency posting.** When the variance is entirely accounted for by the difference between the PO snapshot FX rate and the invoice-date FX rate, the pricelist itself is not at fault — the realised FX gain / loss is posted on AP and the pricelist remains active. Finance Officer records the FX-only categorisation in the variance case file; no handoff to Purchaser is needed unless cumulative FX exposure crosses a tenant threshold (in which case the Finance Manager reviews currency-hedging policy out-of-band).
- **No active pricelist at the time of GRN / invoice posting.** When the three-way-match fails because the originating PR was created with `pricelist_type = manual_input` (`VPL_XMOD_002`) and there is no pricelist anchor for the variance check, Finance Officer routes the case directly to the Purchasing Manager to (a) launch a campaign to fill the coverage gap, and (b) decide whether the absence of pricelist anchor warrants a non-policy AP posting requiring Manager override on the AP side. The pricelist module records the coverage gap as a `system` comment on the affected vendor's pricelist registry.

## 4. Exit Point / Handoffs

Finance's involvement on a given pricelist or variance case ends at one of several documented points; the document state at each handoff is anchored to the lifecycles in [03-user-flow.md](./03-user-flow.md) § 2.

- **Finance Manager pre-activation sign-off** — Finance Manager signs off on the multi-currency / high-value pricelist; handoff is to the **Purchaser / Purchasing Manager** for the final activation click (or, if they have already signed off, `VPL_POST_017` fires immediately and the pricelist activates). Document state at handoff: pricelist `draft + submitted_at IS NOT NULL`; a Finance signoff `system` comment is on the pricelist's activity log.
- **Finance Manager pre-activation send-back** — Finance Manager vetoes activation; handoff is to the **Vendor** (via rejection email under the original token, exactly as `VPL_POST_018` for any rejection) and the **Purchaser** (notification). Document state at handoff: pricelist `draft + submitted_at = NULL`; Finance objection `system` comment captures the FX / multi-currency policy rationale.
- **Variance categorised within-tolerance** — no action on the pricelist; the variance row drops from the open dashboard; document state on the pricelist unchanged (`active`); the case file is retained for the Auditor.
- **Variance categorised vendor over-billed** — Finance Officer hands off to the **Purchaser** to pursue a credit note with the vendor; document state on the pricelist unchanged (`active`); variance `system` comment written for pricelist-deviation analytics.
- **Variance categorised pricelist out-of-date** — Finance Officer hands off to the **Purchasing Manager** with a recommendation to inactivate; Manager executes `VPL_POST_019` (or delegates to the Purchaser for follow-up). Document state at handoff: pricelist `active`; the Manager's decision drives the next state.
- **Variance categorised FX-only** — no action on the pricelist; AP-posting side carries the realised FX gain / loss; document state on the pricelist unchanged (`active`); FX `system` comment written.
- **No pricelist coverage** — Finance Officer hands off to the **Purchasing Manager** for a new campaign launch; document state on the pricelist module: a coverage gap is recorded against the vendor / product registry; pricelist `(none)` for the affected product until the new campaign completes.

In every case, the pricelist `status` is changed (if at all) only by the Purchaser / Purchasing Manager — Finance's role is to anchor the audit, post the AP-side entries, and recommend the pricelist-side action.

## 5. References

- Parent overview: [03-user-flow.md](./03-user-flow.md) — global lifecycle and cross-persona handoff table; the Finance row sits at the multi-currency co-approval gate and at every post-GRN variance investigation.
- Authorization: [02-business-rules.md](./02-business-rules.md) § 4 — `VPL_AUTH_009` (Finance Officer read-only), `VPL_AUTH_010` (Finance Manager co-approval), `VPL_AUTH_014` (segregation of duties).
- Posting rules: [02-business-rules.md](./02-business-rules.md) § 5 — `VPL_POST_017` (activation by Purchaser, conditional on Finance Manager signoff for multi-currency), `VPL_POST_018` (rejection, including Finance veto), `VPL_POST_019` (inactivation, executed by Purchaser on Finance recommendation).
- Calculation rules: [02-business-rules.md](./02-business-rules.md) § 3 — `VPL_CALC_001`–`VPL_CALC_002` (tax decomposition Finance verifies), `VPL_CALC_005` (multi-currency display — pricelist never FX-mutated), `VPL_CALC_006` (quality score Finance reviews).
- Cross-module rules: [02-business-rules.md](./02-business-rules.md) § 6 — `VPL_XMOD_005` (GRN price-variance check against active pricelist — Finance's primary post-receipt entry point), `VPL_XMOD_002` (missing pricelist coverage on PR-line manual input — Finance's coverage-gap referral), `VPL_XMOD_008` (currency master integrity verified at Finance pre-activation sign-off).
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — internal persona that activates / inactivates the pricelist on Finance's recommendation; pursues credit notes on Finance's request.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Auditor consumes Finance's variance case files in the chain audit; Sysadmin configures the FX rate source and tax-profile master data Finance verifies.
- Sibling: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — external counterparty whose rejection-resubmission loop closes back through the same Finance review on the next pass for multi-currency cases.
- Cross-link: [purchase-order](/en/inventory/purchase-order) — primary downstream consumer where Finance runs the three-way match that drives variance investigation back into this module. `PO_POST_008` / `PO_POST_009` are the operational counterparts to `VPL_XMOD_005`.
- Cross-link: [good-receive-note](/en/inventory/good-receive-note) — upstream variance source where GRN posting first compares against the active pricelist.
- Cross-link: [purchase-request](/en/inventory/purchase-request) — `VPL_XMOD_002` missing-pricelist coverage gap referrals originate at PR-line creation.
- `../carmen/docs/vendor-pricelist-management/design.md` — Phase 6 (Data Validation & Quality Control) and the analytics / reporting layer Finance reads.
- `../carmen/docs/vendor-pricelist-management/price-assignment-workflow-documentation.md` — variance categorisation and PPV linkage at the AP-posting side.
