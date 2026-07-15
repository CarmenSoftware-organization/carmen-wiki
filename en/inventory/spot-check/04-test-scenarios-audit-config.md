---
title: Spot Check — Test Scenarios — Audit & Config (Correction)
description: Correction notice — no Approver/Finance, Auditor, or Sysadmin surface exists for spot check.
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, test-scenarios, audit, config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Test Scenarios — Audit & Config (Correction)

> **At a Glance**
> **Status:** confirmed-absent persona group &nbsp;·&nbsp; **Module:** [spot-check](/en/inventory/spot-check) &nbsp;·&nbsp; **What replaces it:** [04-test-scenarios-inventory-controller](/en/inventory/spot-check/04-test-scenarios-inventory-controller) and [04-test-scenarios-counter](/en/inventory/spot-check/04-test-scenarios-counter)

## 1. What This Page Used to Claim

An earlier draft of this wiki module catalogued roughly twenty-three Auditor and Sysadmin test scenarios for spot check — inspecting a full audit chain from spot-check sheet through a rollup adjustment approval to a journal entry, verifying segregation-of-duties on that approval, and configuring variance-tolerance thresholds, default sampling size/method, and reason-code mappings.

## 2. Why It Was Removed

See [03-user-flow-audit-config.md](/en/inventory/spot-check/03-user-flow-audit-config) for the full source-by-source breakdown. In summary: this module has exactly one permission key (`inventory_management.spot_check`), the final submit produces no rollup document or ledger effect for anyone to approve or trace, no tolerance or recount mechanism exists to configure, and no reason-code mapping is ever read since there is no rollup to attach one to. There is nothing left to write scenarios against for this persona group.

## 3. What To Read Instead

- [spot-check/04-test-scenarios-inventory-controller](/en/inventory/spot-check/04-test-scenarios-inventory-controller) — list/create-screen scenarios.
- [spot-check/04-test-scenarios-counter](/en/inventory/spot-check/04-test-scenarios-counter) — entry/review-screen scenarios, including the module's one real validation and completion rule set.
- [spot-check/04-test-scenarios](/en/inventory/spot-check/04-test-scenarios) § 4 — end-to-end scenarios spanning all four screens.

## 4. References

- **Frontend:** `../carmen-inventory-frontend-react/constant/permissions.ts`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts`.
- Related: [spot-check/03-user-flow-audit-config](/en/inventory/spot-check/03-user-flow-audit-config) (parallel correction page on the user-flow side).
