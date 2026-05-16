---
title: Period End
description: End-of-period close orchestrator — gates costing snapshot, GL handoff, and backdating lock once Physical Count and Spot Check requirements are met.
published: true
date: 2026-05-16T15:00:00.000Z
tags: inventory, period-end, costing, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Period End

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/inventory-management/period-end`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Period End is the run-the-close button. Per `Test_case/System_Process/tx-09-end-period-close.md` and the Process Execution Swim Lane, the close is gated by three prerequisites: every transactional document (GRN / SR / adjustments / wastage) posted, every Spot Check completed, and every Physical Count finalized. On success the costing engine writes a `tb_period_snapshot` row per `(location, product, lot)`, [[system-config/period]] flips to `closed` / `locked`, and any further backdated post is rejected. Finance owns the trigger; the Inventory Manager monitors the prerequisite checklist.

## 2. Related Modules

- [[system-config/period]] — the period rows this process closes
- [[costing]] — snapshot generation
- [[physical-count]], [[spot-check]] — gating prerequisites
- [[reporting-audit]] — close-out reports

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/inventory-management/period-end/` — frontend page
- `Test_case/System_Process/tx-09-end-period-close.md` — close procedure
- `Test_case/System_Process/INDEX.md` § Process Execution Swim Lane — prerequisite chain
