---
title: Vendor Pricelist — Test Scenarios — Finance (Correction)
description: Correction page — Finance is not a distinct persona in the vendor-pricelist module; no test scenarios apply.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, test-scenarios, finance, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — Test Scenarios — Finance (Correction)

> This page previously catalogued scenarios for a Finance Officer / Finance Manager persona: multi-currency co-signoff gates, a variance-audit dashboard, and FX-policy enforcement. See [03-user-flow-finance.md](./03-user-flow-finance.md) for the full correction — none of this has matching code in `price-list.service.ts`, `price-list-template.service.ts`, or `request-for-pricing.service.ts`.

No Finance-specific test scenarios apply to this module. If GRN-side price variance is being tested, see the [good-receive-note](/en/inventory/good-receive-note) module's own test-scenario pages instead.

## References

- [03-user-flow-finance.md](./03-user-flow-finance.md) — full correction detail.
- [02-business-rules.md](./02-business-rules.md) § 4.
- [04-test-scenarios.md](./04-test-scenarios.md) — persona index (Finance removed).
