---
title: Vendor Pricelist — User Flow — Audit & Config (Correction)
description: Correction page — no dedicated Audit workspace or Configuration console exists in the vendor-pricelist module.
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, audit-config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# Vendor Pricelist — User Flow — Audit & Config (Correction)

> **This page previously described an Auditor persona** (a query-builder workspace over templates/campaigns/invitations/pricelists, with segregation-of-duties and quality-score checks) **and a System Administrator persona** (numbering, RBAC, portal-token policy, email integration, validation-rule registry, FX-source configuration, and per-invitation token revocation, each its own configuration page). Re-reading the module's four services directly (2026-07-16) found no matching code for any of it — mirroring the established, confirmed-absent pattern already documented for the equivalent "Audit / Config" pages in the `purchase-order`, `good-receive-note`, `store-requisition`, `inventory`, `inventory-adjustment`, `physical-count`, and `spot-check` modules.

## What was claimed vs. what exists

| Claim | Status |
| ----- | ------ |
| A dedicated "Pricelist Activity Queries" audit workspace with saved query templates. | **Not implemented.** No such route or component exists. |
| Segregation-of-duties verification (vendor-token holder ≠ approver; high-value editor ≠ approver). | **Not implemented.** No such cross-check exists in any service in this module. |
| Portal-token policy configuration (expiration, IP allowlist, concurrent-session limit, suspicious-activity detection). | **Not implemented.** `check-price-list.service.ts`'s `checkPricelist()` never checks an expiry date, an IP address, or a session count. |
| Per-invitation "Revoke Token" action. | **Not implemented.** No endpoint sets `pricelist_url_token` back to `NULL` anywhere in the backend; the token is written once at RFQ-create time. |
| A dedicated pricelist-numbering / RBAC / email-integration / validation-rule-registry / FX-source configuration console. | **Not implemented as VPL-specific screens.** Generic numbering (`tb_config_running_code`, used by `generatePLNo()`), RBAC, and currency master data exist elsewhere in the product (see `system-config` and `master-data` books/modules), but there are no pricelist-specific configuration pages layered on top of them. |
| Configuration changes snapshot cleanly for in-flight documents, with a rollback-capable configuration audit log. | **Not implemented.** There is no configuration-versioning mechanism in this module to snapshot or roll back in the first place. |

## What is real

- The generic running-code pattern (`tb_config_running_code`, type `PRICE-LIST`) drives `pricelist_no` generation — this is the same generic numbering mechanism used across the product, not a pricelist-specific numbering console.
- Comment tables exist and have their own manual CRUD endpoints per entity family, usable by any authorized user for free-text notes — but writing one is always a manual action, never an automatic audit-trail entry (see [01a-data-model-comments](/en/inventory/vendor-pricelist/01a-data-model-comments)).
- If a dedicated audit query surface or a token-revocation action is wanted, it does not exist today and would be new-feature work, not a documentation gap.

## References

- [vendor-pricelist](/en/inventory/vendor-pricelist) — module landing, corrected roles table.
- [02-business-rules.md](./02-business-rules.md) § 4, § 5.4 — confirmed-vs-design-target authorization and status claims, including the portal-token gap.
- [03-user-flow.md](./03-user-flow.md) — persona index (Audit/Config removed).
- [system-config](/en/inventory/system-config), [master-data](/en/inventory/master-data), [access-control](/en/inventory/access-control) — where the real, generic numbering / currency / RBAC configuration screens live.
