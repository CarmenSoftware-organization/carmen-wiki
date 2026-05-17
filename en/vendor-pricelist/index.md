---
title: Vendor Pricelist
description: Vendor catalogs of products with agreed prices, units, and validity periods — the reference for PR/PO pricing.
published: true
date: 2026-05-17T07:00:16.000Z
tags: vendor-pricelist, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Vendor Pricelist

> **At a Glance**
> **Module purpose:** Vendor-specific, time-bound MOQ-tiered price catalogue collected via a 6-phase campaign / portal workflow — the reference for PR / PO / GRN pricing and variance &nbsp;·&nbsp; **Audience:** Purchaser, Purchasing Manager, Vendor (external portal), Finance, Auditor &nbsp;·&nbsp; **Key entities/tables:** `tb_pricelist`, `tb_pricelist_detail`, `tb_request_for_pricing`, `tb_pricelist_template`, [[vendor-pricelist/request-price-list]] &nbsp;·&nbsp; **Sub-pages:** 13

![Vendor Pricelist screen](/assets/screenshots/vendor-pricelist/index.png)

## 1. Overview

A **Vendor Pricelist** is the authoritative record of the prices a specific vendor has quoted for a specific set of products, expressed in the vendor's currency, scoped to a defined validity period, and structured around the unit and minimum-order-quantity (MOQ) tiers the vendor will honour. Each pricelist has a header — vendor, pricelist number, currency, validity-from and validity-to dates, originating campaign or template, submission method, status, quality score, and audit fields — and one or more line items that carry the product reference, the MOQ-tiered pricing rows (unit, unit price, conversion factor, effective unit price, lead time), validation status, and notes. The same product on the same vendor's pricelist can carry multiple MOQ rows (e.g., MOQ 1 at €12.50/Each, MOQ 50 at €10.50/Each, MOQ 100 at €9.75/Each), and the system auto-sorts and validates them so higher quantities consistently carry lower or equal unit prices.

Pricelists are vendor-specific and time-bound. Several vendors can carry the same product, each on their own pricelist at their own price and currency, and the procurement function decides — per product, per category, or via business rules — which vendor's pricelist is the **preferred** source for that product at any given moment. Multi-currency is first-class: the vendor selects the currency at submission and the system carries it through display, comparison, and reporting, with conversion handled at the point of use (PR pricing, PO commitment, GRN variance) rather than mutating the stored vendor price. Pricelists are collected through a 6-phase workflow — vendor setup, template creation, campaign planning, invitation, secure-portal submission, validation — so the pricing the rest of the system relies on has a clear provenance and a defensible audit trail back to the vendor that quoted it.

Once active, a pricelist becomes the reference dataset for every downstream procurement decision. PR pricing defaults from the preferred vendor's active pricelist; PO unit prices are validated against it before the commitment is sent; GRN posting calculates price variance between received-and-invoiced and the active pricelist value; and finance reporting groups spend by vendor and pricelist for negotiation leverage. Expired or superseded pricelists remain queryable for historical analysis and price-trend detection, while only one pricelist per vendor-product-validity window is treated as active for live transactions.

## 2. Business Context

The vendor pricelist is the mechanism by which the organisation enforces negotiated rates. Procurement spends real effort negotiating prices, units, MOQ tiers, and validity windows with each vendor; without a live, system-of-record pricelist tied to those agreements, the negotiated rate exists only on paper and buyers default to whatever price a vendor quotes on the day. Routing every PR and PO through the active pricelist closes that gap: PR pricing defaults from the pricelist, PO prices are validated against it, and GRN price variance is calculated against it. A line that diverges from the pricelist is flagged immediately for purchaser review rather than being discovered weeks later at invoice match.

The module is also the basis for variance reporting and procurement performance. Because every transaction is anchored to a known vendor price at a known point in time, finance can quantify the gap between negotiated and realised pricing — by product, vendor, period, or buyer — and feed that back into the next negotiation cycle. Quality scoring at the submission level (data completeness, business-rule compliance, vendor reliability) flows through to vendor performance metrics and influences which vendor is chosen for the next PR. The audit trail — campaign, invitation token, submission method, validation results, approvals — gives auditors a clean chain of custody from the vendor's quote to the line price on a posted invoice.

Operationally, the module compresses a process that is otherwise email-and-spreadsheet heavy. Templates standardise what is asked of vendors; campaigns orchestrate when and from whom prices are collected; the secure vendor portal lets the vendor enter prices directly, upload an Excel template, or email it to purchasing — with the same validation engine running across all three channels. Auto-save, draft mode, and progress tracking let vendors complete pricing over multiple sessions without losing work, which materially improves response rates and the quality of the pricing data that downstream modules consume.

## 3. Key Concepts

- **Pricelist Header**: The vendor-level record carrying vendor reference, pricelist number, originating campaign and template, currency, validity-from and validity-to dates, submission method (online, upload, email), status (`draft`, `submitted`, `under-review`, `approved`, `rejected`), quality score, validation results, and audit fields. The header binds all the line items to one vendor in one currency for one validity window.
- **Pricelist Line / Pricelist Item**: A row representing a single product on the pricelist, carrying product reference (code, name, category), one or more MOQ-tiered pricing rows, optional lead time and notes, and a validation status (`valid`, `warning`, `error`). The line is the unit of pricing lookup for PR, PO, and GRN.
- **MOQ Tier**: A pricing row inside a pricelist line that specifies a minimum order quantity, unit of measure, conversion factor (e.g., 1 Box = 50 Each), unit price, effective unit price per base unit, and optional lead time. Each product can carry multiple tiers and they are auto-sorted by MOQ; the system validates that higher quantities have lower or equal unit prices.
- **Validity Period**: The from-and-to date window during which the pricelist is treated as the current reference for downstream pricing. Outside the window the pricelist is historical-only — queryable for reporting, not used for new PR/PO defaulting or GRN variance.
- **Preferred Vendor**: The vendor whose active pricelist is treated as the default source of price and supply for a given product. Set per product (or per category) and resolved at PR-item creation; downstream modules pull pricing from this vendor's pricelist unless a rule, override, or fallback chooses differently.
- **Price Variance**: The delta between a transacted price (PO line, GRN line, vendor invoice line) and the unit price on the active pricelist for the same vendor-product-unit-quantity combination at that point in time. Calculated at GRN posting and three-way match; values exceeding the configured threshold are flagged for review.
- **Unit Conversion**: The factor that maps a vendor's pricing unit (Box, Carton, Pack) to the inventory base unit (Each). Captured per MOQ tier so the effective unit price per base unit is computed and comparable across vendors and units.
- **Price Collection Template**: A reusable definition of what to ask vendors for — products (selected by category, subcategory, item group, or specific item), supported currencies, required fields, MOQ tier limit, validity period, and validation rules. Used to generate vendor-specific Excel templates and portal interfaces.
- **Price Collection Campaign**: A scheduled, vendor-targeted instance of a template — campaign name, selected vendors, start and end dates, reminder schedule, status (`draft`, `active`, `paused`, `completed`, `cancelled`), and aggregated analytics on response and completion. One-time, recurring, or event-based.
- **Vendor Invitation**: The per-vendor record of a campaign — vendor reference, unique cryptographic token, pricelist identifier, email-delivery telemetry (sent, delivered, opened, clicked), portal-access telemetry (first/last access, session count, IP addresses), and submission status (`pending`, `in-progress`, `submitted`, `approved`, `expired`). Each invitation generates one vendor-specific pricelist.
- **Submission Method**: How the vendor returned the pricing — `online` (direct portal entry with inline MOQ expansion and auto-save), `upload` (Excel template uploaded to the portal), or `email` (Excel emailed to purchasing for staff to process). The same validation engine runs across all three.
- **Validation Engine**: The rule set that runs against every submission — format (price, currency, units), completeness (required fields, missing data), and business rules (no duplicate MOQs, higher quantity ≤ unit price, price reasonableness vs historical and market data). Produces validation results, a quality score, and inline correction guidance.
- **Quality Score**: An automated rating of a submitted pricelist, combining data completeness, format correctness, business-rule pass rate, and consistency. Feeds into approval routing and into the vendor's performance profile for future vendor selection.
- **Portal Token**: The cryptographically secure, time-limited, per-vendor access token embedded in the invitation email. Authorises portal entry, enforces session limits and IP tracking, and can be revoked immediately by purchasing or admins.
- **Auto-Save / Draft Mode**: The vendor-portal mechanism that saves entered pricing every ~30 seconds, preserves state across sessions, and supports partial submission. Vendors can leave and return without losing work; staff can see draft age and progress.
- **Active Pricelist**: For any vendor-product-unit-validity combination, the single pricelist row that is approved, in-window, and treated as the live reference for downstream pricing and variance calculation.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Purchaser / Purchasing Staff | Negotiates rates with vendors, builds price-collection templates and campaigns, sends invitations, reviews and approves submitted pricelists, manages individual price-item edits and status, assigns preferred vendor per product, and uploads emailed vendor submissions. Owns the operational pricelist lifecycle end-to-end. |
| Purchasing Manager | Owns the negotiation strategy and the vendor mix, approves high-value or strategically sensitive pricelists, configures business rules for preferred-vendor and price-assignment logic, and signs off on multi-currency and cross-border pricing. |
| Vendor | External party that receives the invitation, accesses the secure portal via token, provides pricing through online entry, Excel upload, or email submission, selects the currency, supplies MOQ tiers with units and conversion factors, and can save drafts and resubmit. The provider of the pricing data. |
| Finance Officer / Accounts Payable | Audits price variance between active pricelists and posted GRN/invoice lines, validates currency and exchange-rate handling, reconciles negotiated vs realised pricing, and feeds variance findings back to procurement. |
| Finance Manager | Reviews variance reports and vendor performance, validates the financial impact of multi-currency pricelists, and ensures the audit trail supports compliance and reporting needs. |
| Receiver / Store Keeper | Indirect consumer — GRN posting uses the active pricelist for variance calculation; significant divergences from the pricelist are surfaced for review at the point of receipt. |
| System Administrator | Configures pricelist numbering, status transitions, RBAC, template and campaign settings, portal token policy (expiration, IP restrictions, session limits), email-delivery integration, and validation rules. Manages token revocation and audit log retention. |
| Auditor | Read-only access to pricelists, campaigns, invitations, submission history, validation results, and the activity log — used to verify pricing provenance, segregation of duties, and end-to-end traceability from vendor quote to posted invoice. |

## 5. Related Modules

**Cross-module flow:**
- [[product]] — pricelist entries reference products
- [[purchase-request]] — PRs default to preferred vendor pricelists
- [[purchase-order]] — POs validate prices against the active pricelist
- [[good-receive-note]] — GRN price variance is calculated against pricelist

**Master configuration:**
- [[master-data/vendor]] — vendor master each pricelist is scoped to
- [[master-data/currency]] — currency the vendor selects at submission
- [[master-data/tax-profile]] — tax codes on each pricelist line
- [[templates/price-list]] — reusable template defining what to ask vendors for in a campaign
- [[master-data/unit]] — pricing unit (Box / Carton / Pack) plus conversion to base inventory unit
- [[system-config/workflow]] — pricelist submission and approval workflow
- [[reporting-audit/activity]] — pricelist submission, validation, and approval activity log for audit

## 6. Reference Sources

- Concepts: `../carmen/docs/vendor-pricelist-management/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [[vendor-pricelist/01-data-model]] — entities, fields, relationships, enums for the ten tenant-schema models (`tb_pricelist_template`, `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, `tb_pricelist_template_detail_comment`, `tb_request_for_pricing`, `tb_request_for_pricing_comment`, `tb_request_for_pricing_detail`, `tb_request_for_pricing_detail_comment`, `tb_pricelist`, `tb_pricelist_detail`, `tb_pricelist_comment`, `tb_pricelist_detail_comment`) and the three module-local enums (`enum_pricelist_template_status`, `enum_pricelist_status`, `pricelist_submission_method`) plus the divergence table for the 12 material differences between carmen/docs `design.md` and Prisma.
- [[vendor-pricelist/02-business-rules]] — validation (`VPL_VAL_001`–`VPL_VAL_025`), calculation (`VPL_CALC_001`–`VPL_CALC_008`), authorization (`VPL_AUTH_001`–`VPL_AUTH_015`), status / posting (`VPL_POST_001`–`VPL_POST_022` across all three lifecycles + application-derived campaign / invitation statuses), and cross-module rules (`VPL_XMOD_001`–`VPL_XMOD_009` to PR / PO / GRN / product / vendor / currency / validation engine).
- [[vendor-pricelist/03-user-flow]] — document-lifecycle overview + persona index.
  - [[vendor-pricelist/03-user-flow-purchaser]] — Purchaser + Purchasing Manager (collapsed) path: template builder, campaign launcher, submission reviewer, preferred-vendor curator.
  - [[vendor-pricelist/03-user-flow-vendor]] — Vendor (external, token-authenticated portal session) path. Shorter file — the only external persona in the Carmen suite with persistent in-system effect via the portal.
  - [[vendor-pricelist/03-user-flow-finance]] — Finance Officer + Finance Manager (variance audit against GRN / invoice; multi-currency co-signoff for activation).
  - [[vendor-pricelist/03-user-flow-audit-config]] — Auditor + System Administrator (read-only chain audit; numbering, RBAC, portal-token policy, email integration, validation rules, currency / FX sources, audit retention; per-invitation token revocation).
- [[vendor-pricelist/04-test-scenarios]] — test-scenarios overview + 12 cross-persona handoff scenarios + E2E mapping target (roadmap item — no dedicated spec today).
  - [[vendor-pricelist/04-test-scenarios-purchaser]] — Purchaser + Manager scenarios.
  - [[vendor-pricelist/04-test-scenarios-vendor]] — Vendor scenarios; Permission section is N/A (single row) because the vendor has no Carmen RBAC matrix.
  - [[vendor-pricelist/04-test-scenarios-finance]] — Finance Officer + Manager scenarios.
  - [[vendor-pricelist/04-test-scenarios-audit-config]] — Auditor + Sysadmin scenarios.

> **Status:** all sub-pages are full-detail and self-contained. Data-model section is grounded in the canonical Prisma schema (`tb_pricelist*` + `tb_request_for_pricing*` + `tb_pricelist_template*` — ten entities, three module-local enums); business-rules introduces the `VPL_*` rule-ID catalogue grounded in carmen/docs (`design.md`, `requirements.md`, `price-assignment-workflow-documentation.md`); user-flow and test-scenarios cover all four persona groups consolidated from the 8 personas in Section 4. The Receiver / Store Keeper from Section 4 is documented as an indirect consumer in cross-persona scenarios (no dedicated persona file). No E2E spec exists today — coverage runs at the API / integration level and through downstream-module E2E specs (`401-po.spec.ts`, `402-po-purchaser-journey.spec.ts`); a dedicated vendor-pricelist E2E spec is a roadmap item per `../carmen/docs/vendor-pricelist-management/tasks.md`.
