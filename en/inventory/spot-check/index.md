---
title: Spot Check
description: Targeted partial count of selected items or locations — a lighter-weight check than a full physical count.
published: true
date: 2026-05-17T07:00:16.000Z
tags: spot-check, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Spot Check

> **At a Glance**
> **Module purpose:** Narrow-scope targeted partial count (random / risk-based / event-driven) with recount and variance-to-adjustment posting &nbsp;·&nbsp; **Audience:** Inventory Controller, Counter, Auditor &nbsp;·&nbsp; **Key entities/tables:** `tb_spot_check`, `tb_spot_check_detail`, two comment tables, `enum_spot_check_status`, `enum_spot_check_method` &nbsp;·&nbsp; **Sub-pages:** 10

![Spot Check screen](/screenshots/spot-check/index.png)

## 1. Overview

A **spot check** is a targeted, partial count of selected inventory items or storage locations performed to verify that on-hand quantities match recorded balances. Unlike a full **physical count**, which counts every item across all locations on a fixed cycle, a spot check focuses on a deliberately narrow scope — a handful of high-value SKUs, a single shelf, one storeroom, or items flagged by an exception report. This makes spot checks fast enough to run during normal operating hours without freezing inventory movement.

Spot checks are typically **triggered** by one of three patterns: *random sampling* (rotating through items to maintain general count discipline), *risk-based selection* (high-value, high-theft, or fast-moving items checked more frequently), and *event-driven* checks (after a suspected discrepancy, a delivery dispute, a system error, or a loss-prevention incident). The typical workflow is short and self-contained: an inventory controller selects the items in scope, a counter performs the physical count, the system compares counted vs. on-hand quantities, variances above a threshold are reviewed and either recounted or accepted, and approved variances are posted as **inventory adjustments** so the perpetual balance reflects reality.

Because spot checks are quick to launch and easy to repeat, they are a core control in any inventory program — catching shrinkage, miscounts, and process errors early, between the longer cycles of the formal physical count.

> **TODO:** Source content from `../carmen-inventory-frontend/` (UI flow) and `../carmen-inventory-frontend-e2e/` (test scenarios). No carmen/docs source folder exists for this module.

## 2. Business Context

In hospitality operations, spot checks provide **daily or weekly verification** of high-risk items — premium spirits, prime cuts, branded amenities, controlled goods — without the operational disruption of a full count. By running short, frequent checks on the items most exposed to loss, operators close the visibility gap between scheduled physical counts (typically monthly or quarterly) and the day-to-day movement of inventory.

The control serves two complementary purposes. First, it is a **loss-prevention** tool: targeted counts on theft-prone or pilferage-prone categories deter shrinkage and surface issues while the trail is still warm enough to investigate. Second, it is a **supplement to the periodic physical-count cycle**: by continuously sampling, finance and operations gain ongoing assurance that perpetual balances are reliable, rather than only learning about discrepancies at month-end. Together, spot checks reduce variance shocks at closing time and keep cost-of-goods reporting trustworthy throughout the period.

## 3. Key Concepts

- **Selection Criteria**: The rule used to choose which items or locations to count. Three common modes are *random* (system picks a sample to rotate coverage), *risk-based* (high-value, high-velocity, or historically variant items selected on a defined frequency), and *triggered* (a specific event — incident report, suspected error, delivery dispute — prompts the check).
- **Count Scope**: The boundary of a single spot check — a list of SKUs, a specific shelf or bin, a sub-location, or a category. Scope is deliberately narrow so the count can finish quickly without freezing other inventory activity.
- **Variance Threshold**: The tolerance (absolute quantity or percentage of on-hand) above which a counted-vs-system difference must be investigated. Variances within threshold may be posted automatically; variances above it require recount and/or approval.
- **Recount**: A second physical count, usually performed by a different counter, used when the first count produces a variance above threshold. The recount result is what gets compared against the system balance for the final variance decision.
- **Posting Workflow**: The sequence by which an approved variance becomes a system entry — variance is reviewed, an adjustment reason is assigned, the entry is approved, and an **inventory adjustment** transaction is posted to update the perpetual balance and corresponding GL accounts.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Inventory Controller | Defines selection criteria, schedules and launches spot checks, reviews variances, approves or rejects recount requests, and approves adjustments for posting. |
| Counter | Performs the physical count of in-scope items or locations and records counted quantities accurately and on time. |
| Auditor | Independently reviews spot-check results, recount evidence, and posted adjustments to confirm controls are operating and shrinkage is investigated. |

## 5. Related Modules

**Cross-module flow:**
- [[inventory]] — spot check verifies a subset of inventory balances
- [[inventory-adjustment]] — variances are posted as adjustments
- [[physical-count]] — full count counterpart

**Master configuration:**
- [[master-data/unit]] — unit of measure for each spot-check line
- [[master-data/location]] — the (sub-)location in scope for the spot check
- [[master-data/adjustment-type]] — reason codes used when posting variance adjustments
- [[system-config/workflow]] — approval workflow for recount and variance posting
- [[access-control/user-location]] — restricts which locations a user can spot-check
- [[reporting-audit/activity]] — spot-check and recount activity log for audit

## 6. Reference Sources

- Concepts: (no source — see TODO in section 1)
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [[spot-check/01-data-model]] — entities, fields, relationships, enums (`tb_spot_check`, `tb_spot_check_detail` plus two comment tables; two enums `enum_spot_check_status` / `enum_spot_check_method`).
- [[spot-check/02-business-rules]] — validation, calculation, authorization, posting, cross-module rules (`SPC_VAL_*` / `SPC_CALC_*` / `SPC_AUTH_*` / `SPC_POST_*` / `SPC_XMOD_*`).
- [[spot-check/03-user-flow]] — document lifecycle overview + persona index.
  - [[spot-check/03-user-flow-inventory-controller]] — Inventory Controller path.
  - [[spot-check/03-user-flow-counter]] — Counter path.
  - [[spot-check/03-user-flow-audit-config]] — Auditor + (implicit) Sysadmin path.
- [[spot-check/04-test-scenarios]] — test scenarios overview + cross-persona handoff scenarios + E2E mapping target.
  - [[spot-check/04-test-scenarios-inventory-controller]] — Inventory Controller scenarios.
  - [[spot-check/04-test-scenarios-counter]] — Counter scenarios.
  - [[spot-check/04-test-scenarios-audit-config]] — Auditor + Sysadmin scenarios.

> **Status:** all sub-pages are skeleton-level (~50-100 lines each). Each carries explicit TODO callouts pointing at the upstream sources to use when filling in (`../carmen-inventory-frontend/` for UI flow; `../carmen-inventory-frontend-e2e/tests/` for E2E specs — no spot-check spec exists yet). Data-model section is grounded in the Prisma schema (`tb_spot_check*` is **its own table set** — four entities, two enums — *not* shared with `tb_physical_count*`; the two modules are conceptual cousins that both roll up to [[inventory-adjustment]], not shared infrastructure); business-rules introduces a proposed `SPC_*` rule-ID catalogue that needs carmen/docs confirmation; user-flow and test-scenarios are structural placeholders.
