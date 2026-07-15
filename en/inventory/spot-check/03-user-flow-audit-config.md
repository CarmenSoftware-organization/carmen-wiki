---
title: Spot Check — User Flow — Audit & Config (Correction)
description: Correction notice — no Approver/Finance, Auditor, or Sysadmin surface exists for spot check.
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, user-flow, audit, config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — User Flow — Audit & Config (Correction)

> **At a Glance**
> **Status:** confirmed-absent persona group &nbsp;·&nbsp; **Module:** [spot-check](/en/inventory/spot-check) &nbsp;·&nbsp; **What replaces it:** [03-user-flow-inventory-controller](/en/inventory/spot-check/03-user-flow-inventory-controller) and [03-user-flow-counter](/en/inventory/spot-check/03-user-flow-counter) document the module's one real, permission-gated role

## 1. What This Page Used to Claim

An earlier draft of this wiki module described a third persona group for spot check — an Auditor who observed checks in progress and inspected a full audit chain (spot-check sheet → recount → rollup adjustment approval → journal entry), and an implicit Sysadmin who configured variance-tolerance thresholds, default sampling size/method, and reason-code mappings for a `SPOT_CHECK_OVERAGE`/`SPOT_CHECK_SHORTAGE` rollup.

## 2. What the Source Actually Shows

A targeted search of the frontend (`../carmen-inventory-frontend-react/routes/inventory-management/spot-check/`), backend (`../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check*`), and the Bruno API collection (`../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/spot-check*`) found no matching route, permission key, workflow stage, or configuration screen for any of the claimed sub-roles.

| Claim | Status | What the source shows |
|---|---|---|
| A rollup adjustment exists for an Approver/Finance persona to approve | Not found | `submit()` has no downstream document to approve at all — its only effect is `doc_status = completed` and an `end_date` stamp (see [02-business-rules.md](/en/inventory/spot-check/02-business-rules) `SPC_POST_001`–`002`). There is nothing to route for approval. |
| Auditor has read-only inspection access to a full audit chain | Not found | Only one permission key exists for this module, `inventory_management.spot_check` (CRUD) — no read-only variant or distinct auditor role. There is also no chain to inspect: no rollup document, no journal entry, no linkage field connects a spot check to anything else. |
| Sysadmin configures variance-tolerance thresholds | Not found | No tolerance mechanism of any kind — percentage, absolute-quantity, or otherwise — exists in the frontend or backend for this module. |
| Sysadmin configures default sampling `size`/`method` | Not found | No configuration screen sets a tenant-wide default for either field; every spot check's `method`/`size` (or `product_id[]`, for manual) is chosen fresh on the create screen each time. |
| Sysadmin maps `SPOT_CHECK_OVERAGE`/`SPOT_CHECK_SHORTAGE` reason codes | Not found | Neither reason code exists anywhere in the schema or code — there is no rollup for a reason code to be attached to in the first place. |

## 3. What To Read Instead

- [spot-check/03-user-flow-inventory-controller](/en/inventory/spot-check/03-user-flow-inventory-controller) — the list and create screens.
- [spot-check/03-user-flow-counter](/en/inventory/spot-check/03-user-flow-counter) — the entry and review screens where a spot check is actually performed and submitted.
- [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) § 4 — the module's single real permission rule (`SPC_AUTH_001`–`003`).

## 4. References

- **Frontend:** `../carmen-inventory-frontend-react/constant/permissions.ts`; `routes/inventory-management/spot-check/`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts`.
- **API contracts:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/spot-check/`.
- Related: [spot-check/03-user-flow](/en/inventory/spot-check/03-user-flow) (overview), [spot-check/04-test-scenarios-audit-config](/en/inventory/spot-check/04-test-scenarios-audit-config) (parallel correction page on the test-scenarios side).
