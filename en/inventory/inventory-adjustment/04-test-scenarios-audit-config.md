---
title: Inventory Adjustment — Test Scenarios — Audit & Config
description: Correction notice — no dedicated Auditor or config-threshold surface exists for this module; see the real reason-code master's own E2E spec instead.
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, test-scenarios, audit, sysadmin, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — Test Scenarios — Audit & Config

> **Correction notice.** This page previously catalogued ~38 test scenarios for a System Administrator threshold/GL/RBAC console and an Auditor SoD/lot-recall/void-chain workspace specific to this module. Neither exists — see [03 — User Flow — Audit / Config](./03-user-flow-audit-config.md) for the full correction notice and what was checked.

The only real, testable configuration surface for this module is the reason-code master (`tb_adjustment_type`), already exercised by [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) — ordinary CRUD, code uniqueness, and active/inactive toggling. There is no threshold, GL-mapping, or document-required configuration to test, and no dedicated Auditor screen for this module.

## References

- [03 — User Flow — Audit / Config](./03-user-flow-audit-config.md) — correction notice and what was checked.
- [04 — Test Scenarios](./04-test-scenarios.md) — the module's real test scenarios.
- [`031-adjustment-type.spec.ts`](../../../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts) — the real reason-code CRUD spec.
