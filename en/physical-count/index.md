---
title: Physical Count
description: Periodic count of every item at a location to reconcile system balances against reality.
published: true
date: 2026-05-17T07:00:16.000Z
tags: physical-count, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Physical Count

> **At a Glance**
> **Module purpose:** Scheduled full count of every item at a location, with recount workflow and variance posting via inventory adjustments &nbsp;·&nbsp; **Audience:** Inventory Controller (count lead), Counter / Store Keeper, Finance Reviewer, Auditor &nbsp;·&nbsp; **Key entities/tables:** `tb_physical_count_period`, `tb_physical_count`, `tb_physical_count_detail`, three comment tables, four `enum_physical_count_*` enums &nbsp;·&nbsp; **Sub-pages:** 10

![Physical Count screen](/assets/screenshots/physical-count/index.png)

## 1. Overview

A **Physical Count** is a scheduled, end-to-end count of every item held at a location, performed to reconcile the system's book balance against what is actually on the shelf. The process is document-driven: a count sheet (or count list) is generated from the current on-hand snapshot for the target location, counters walk the floor and record physical quantities line by line, and the system computes a per-line variance — physical minus book. Discrepant lines are flagged for a recount before any variance is accepted as final.

Physical counts are typically run in one of two operating modes. A **frozen-stock** count locks all inbound and outbound movements at the count location for the duration of the exercise, so the book balance does not drift while counters are working; this gives the cleanest variance but requires downtime. A **live-count** mode permits operations to continue, with the system snapshotting the book quantity at count time and reconciling subsequent movements against that snapshot — faster for the business but harder to audit. The choice is driven by the value of the location, audit policy, and how long the count is expected to take.

Cadence varies by operation and risk profile. High-value or high-velocity stock (spirits, premium proteins, controlled drugs) is often counted monthly; bulk dry goods quarterly; full-house wall-to-wall counts typically run at fiscal period-end (annual or semi-annual) for audit sign-off. Once recounts are complete and variances are accepted, the physical count posts: book balances are reset to the counted quantities and the variance lines are written out as inventory adjustments through the normal posting workflow, so every count correction lands in the same audit trail as any other stock movement.

> **TODO:** Source content from `../carmen-inventory-frontend/` (UI flow) and `../carmen-inventory-frontend-e2e/` (test scenarios). No carmen/docs source folder exists for this module.

## 2. Business Context

Physical count is a regulatory and audit baseline, not a discretionary task. External auditors require a documented count at period-end to certify the inventory line on the balance sheet, and most hospitality groups have internal policy mandating cycle counts on high-risk categories at higher frequency. A complete, signed-off count is the evidence that the inventory value carried on the books is real — without it, the closing valuation is unsupported and the audit opinion is at risk.

The financial accuracy stakes are immediate. Hospitality operations run on thin food and beverage margins, and uncounted shrinkage compounds quickly: theft, spoilage, miss-pours, transfer errors, and miscategorised consumption all erode book accuracy between counts. Period-end physical count is where that drift is detected, quantified, and posted as cost-of-goods variance — making the count the single largest correcting entry against COGS in many operations. A late or incomplete count means a misstated COGS, a misstated gross margin, and downstream errors in menu engineering and procurement forecasting.

## 3. Key Concepts

- **Count Sheet**: The working document for a physical count at a specific location. Generated from the system's on-hand snapshot at count time, the sheet lists every product expected at the location with its book quantity (typically hidden from the counter to avoid bias), unit of measure, and a blank field for the physical count. Lines are grouped by storage area or zone so counters can walk the location systematically. The sheet is the unit of assignment, sign-off, and audit retention.
- **Frozen vs Live Count**: The two operating modes for the count window. A **frozen** count blocks all stock movements (receipts, issues, transfers) at the location while counting is in progress, so the book balance is static and variances are unambiguous; the trade-off is operational downtime. A **live** count allows business to continue and reconciles by snapshotting the book quantity at the moment each line is counted, with subsequent movements applied to the post-count balance. Frozen counts are standard for period-end and high-value categories; live counts are common for routine cycle counting.
- **Variance**: The difference between counted physical quantity and book on-hand quantity for a line, calculated as `Variance = Physical Count − Book Quantity`. Positive variance is found stock (write-on); negative is shortage (write-off). Variance is also expressed in value terms using the item's current unit cost, and as a percentage of book quantity to flag outliers. Tolerance thresholds (absolute and percentage) drive which lines trigger recount and which can auto-accept.
- **Recount**: A mandatory second physical count for any line whose first-count variance exceeds the tolerance threshold. Performed by a different counter (or an inventory controller) to remove individual counting error, the recount either confirms the variance — escalating it for posting — or reconciles it to within tolerance. Recount results are tracked alongside the original count on the sheet so audit can see the full chain.
- **Posting Workflow**: The terminal step that turns accepted count results into stock and GL impact. On post, the system: (1) updates each item's on-hand balance to the counted quantity at the count location, (2) generates an inventory adjustment document for the variance lines, routed through the same approval and posting flow as an ad-hoc adjustment, (3) writes stock-movement records and journal entries against the variance reason code's GL account, and (4) closes the count sheet as immutable. Once posted, a count cannot be edited — corrections require a new adjustment.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Inventory Controller / Inventory Manager | Leads the count: schedules the exercise, configures scope (location, categories, mode), assigns counters and zones, generates and distributes count sheets, monitors progress, resolves discrepancies, approves recounts, and triggers posting. |
| Counter / Store Keeper | Performs the physical count on assigned zones, records quantities on the count sheet, flags items that are damaged, unlabelled, or unfamiliar, and signs off completed sheets. |
| Approver / Finance Reviewer | Reviews completed counts and recount results, validates variance reasonableness against historical patterns, approves the variance adjustment document, and signs off on the financial impact at period close. |
| Auditor | Observes a sample of the count in progress, inspects the full chain — count sheets, recount records, approvals, posted adjustments, journal entries — for compliance, segregation-of-duties, and policy adherence. |

## 5. Related Modules

**Cross-module flow:**
- [[inventory]] — physical count resets balances to counted quantities
- [[inventory-adjustment]] — variances between count and book are posted as adjustments
- [[spot-check]] — narrower partial count uses the same concept

**Master configuration:**
- [[master-data/unit]] — unit of measure for each count line
- [[master-data/location]] — the location whose balances are being counted
- [[master-data/adjustment-type]] — reason codes used when posting variance adjustments
- [[system-config/workflow]] — approval workflow for count sign-off and variance posting
- [[system-config/period]] — accounting period gate for count posting
- [[access-control/user-location]] — restricts which locations a user can count
- [[reporting-audit/activity]] — count and recount activity log for audit

## 6. Reference Sources

- Concepts: (no source — see TODO in section 1)
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [[physical-count/01-data-model]] — entities, fields, relationships, enums (`tb_physical_count_period`, `tb_physical_count`, `tb_physical_count_detail` plus three comment tables; four enums).
- [[physical-count/02-business-rules]] — validation, calculation, authorization, posting, cross-module rules (`PHC_VAL_*` / `PHC_CALC_*` / `PHC_AUTH_*` / `PHC_POST_*` / `PHC_XMOD_*`).
- [[physical-count/03-user-flow]] — document lifecycle overview + persona index.
  - [[physical-count/03-user-flow-count-lead]] — Inventory Controller / Inventory Manager path.
  - [[physical-count/03-user-flow-counter]] — Counter / Store Keeper path.
  - [[physical-count/03-user-flow-audit-config]] — Approver / Finance + Auditor + Sysadmin path.
- [[physical-count/04-test-scenarios]] — test scenarios overview + cross-persona handoff scenarios + E2E mapping target.
  - [[physical-count/04-test-scenarios-count-lead]] — Count Lead scenarios.
  - [[physical-count/04-test-scenarios-counter]] — Counter scenarios.
  - [[physical-count/04-test-scenarios-audit-config]] — Approver / Finance + Auditor + Sysadmin scenarios.

> **Status:** all sub-pages are skeleton-level (~50-100 lines each). Each carries explicit TODO callouts pointing at the upstream sources to use when filling in (`../carmen-inventory-frontend/` for UI flow; `../carmen-inventory-frontend-e2e/tests/` for E2E specs — no physical-count spec exists yet). Data-model section is grounded in the Prisma schema and is the most-developed page; business-rules introduces a proposed `PHC_*` rule-ID catalogue that needs carmen/docs confirmation; user-flow and test-scenarios are structural placeholders.
