---
title: Vendor Pricelist — Test Scenarios — Audit & Config (Correction)
description: Correction page — no dedicated Audit workspace or Configuration console exists in the vendor-pricelist module; no test scenarios apply.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: vendor-pricelist, test-scenarios, audit-config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Test Scenarios — Audit & Config (Correction)

> **Executable coverage (2026-09-22):** none targets this persona — see [04-test-scenarios](/en/inventory/vendor-pricelist/04-test-scenarios) for the module's specs and gap reports.

> This page previously catalogued scenarios for an Auditor query-builder workspace and a System Administrator configuration console (numbering, RBAC, portal-token policy, email integration, validation-rule registry, FX-source configuration, token revocation). See [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) for the full correction — none of this has matching code.

No Audit/Config-specific test scenarios apply to this module. The one policy item that became real since (portal-link expiry at the RFQ `end_date`) is exercised from the Vendor page (`VPL-VND-EDGE-01`), and portal / email actions are visible in the shared Activity log (`tb_activity`), which is generic, not a module console. Generic numbering, RBAC, and currency-master screens are tested under [system-config](/en/inventory/system-config), [access-control](/en/inventory/access-control), and [master-data](/en/inventory/master-data) instead.

## References

- [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — full correction detail.
- [02-business-rules.md](./02-business-rules.md) § 4, § 5.4.
- [04-test-scenarios.md](./04-test-scenarios.md) — persona index (Audit/Config removed).
