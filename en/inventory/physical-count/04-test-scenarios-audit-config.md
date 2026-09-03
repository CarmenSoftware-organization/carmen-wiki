---
title: Physical Count — Test Scenarios — Audit & Config (Correction)
description: Correction notice — no Approver/Finance, Auditor, or Sysadmin surface exists for physical count.
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, test-scenarios, audit, config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Test Scenarios — Audit & Config (Correction)

> **At a Glance**
> **Status:** confirmed-absent persona group &nbsp;·&nbsp; **Module:** [physical-count](/en/inventory/physical-count) &nbsp;·&nbsp; **What replaces it:** [04-test-scenarios-count-lead](/en/inventory/physical-count/04-test-scenarios-count-lead) and [04-test-scenarios-counter](/en/inventory/physical-count/04-test-scenarios-counter)

## 1. What This Page Used to Claim

An earlier draft of this wiki module catalogued roughly thirty Approver/Finance, Auditor, and Sysadmin test scenarios for physical count — reviewing and approving the variance-rollup adjustment, observing counts in progress, inspecting the full audit chain, and configuring tolerance thresholds, the default costing method, and reason-code mappings.

## 2. Why It Was Removed

See [03-user-flow-audit-config.md](/en/inventory/physical-count/03-user-flow-audit-config) for the full source-by-source breakdown. In summary: this module has exactly one permission key (`inventory_management.physical_count`), the rollup documents are inserted directly at `doc_status = completed` with no approval stage to route them through, no tolerance or recount mechanism exists to configure, and no reason-code mapping is ever read by the rollup (`adjustment_type_id` stays `null`). There is nothing left to write scenarios against for this persona group.

## 3. What To Read Instead

- [physical-count/04-test-scenarios-count-lead](/en/inventory/physical-count/04-test-scenarios-count-lead) — list-screen scenarios.
- [physical-count/04-test-scenarios-counter](/en/inventory/physical-count/04-test-scenarios-counter) — entry/review-screen scenarios, including the module's one real validation and posting rule set.
- [physical-count/04-test-scenarios](/en/inventory/physical-count/04-test-scenarios) § 4 — end-to-end scenarios spanning both screens.

## 4. References

- **Frontend:** `../carmen-inventory-frontend-react/constant/permissions.ts`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts`.
- Related: [physical-count/03-user-flow-audit-config](/en/inventory/physical-count/03-user-flow-audit-config) (parallel correction page on the user-flow side).
