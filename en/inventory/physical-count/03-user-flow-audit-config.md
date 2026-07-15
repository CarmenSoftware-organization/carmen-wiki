---
title: Physical Count — User Flow — Audit & Config (Correction)
description: Correction notice — no Approver/Finance, Auditor, or Sysadmin surface exists for physical count.
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, user-flow, audit, config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — User Flow — Audit & Config (Correction)

> **At a Glance**
> **Status:** confirmed-absent persona group &nbsp;·&nbsp; **Module:** [physical-count](/en/inventory/physical-count) &nbsp;·&nbsp; **What replaces it:** [03-user-flow-count-lead](/en/inventory/physical-count/03-user-flow-count-lead) and [03-user-flow-counter](/en/inventory/physical-count/03-user-flow-counter) document the module's one real, permission-gated role

## 1. What This Page Used to Claim

An earlier draft of this wiki module described a third persona group for physical count — an Approver/Finance Reviewer who reviewed and approved the variance-rollup adjustment, an Auditor who observed counts in progress and inspected the full audit chain, and a Sysadmin who configured tolerance thresholds, the default costing method, and reason-code mappings.

## 2. What the Source Actually Shows

A targeted search of the frontend (`../carmen-inventory-frontend-react/`), backend (`../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count*`), and the Bruno API collection (`../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/physical-count*`) found no matching route, permission key, workflow stage, or configuration screen for any of the three claimed sub-roles.

| Claim | Status | What the source shows |
|---|---|---|
| Approver/Finance Reviewer approves the rollup adjustment | Not found | The rollup `tb_stock_in`/`tb_stock_out` documents are inserted **directly at `doc_status = completed`** by `submit()` — there is no draft or in-progress stage for them to be routed to an approver in the first place (see [02-business-rules.md](/en/inventory/physical-count/02-business-rules) `PHC_POST_001`). |
| Auditor has read-only inspection access to the full chain | Not found | Only one permission key exists for this module, `inventory_management.physical_count` (CRUD) — no read-only variant or distinct auditor role. |
| Sysadmin configures tolerance thresholds | Not found | No tolerance mechanism of any kind exists in the frontend or backend for this module. |
| Sysadmin configures the default costing method | Partially real, but not via any screen | `enum_business_unit_config_key.physical_count_costing_method` is a real tenant-level config key, read once per final Submit (default `last_receiving` if unset/invalid) — but no frontend screen was found anywhere that sets this key. |
| Sysadmin maps `COUNT_OVERAGE`/`COUNT_SHORTAGE` reason codes | Not found | The rollup never sets `adjustment_type_id` on the created `tb_stock_in`/`tb_stock_out` headers — it stays `null`. No reason-code mapping is read or written by this module. |

## 3. What To Read Instead

- [physical-count/03-user-flow-count-lead](/en/inventory/physical-count/03-user-flow-count-lead) — the list screen where a count is started or resumed.
- [physical-count/03-user-flow-counter](/en/inventory/physical-count/03-user-flow-counter) — the entry and review screens where a count is actually performed and submitted.
- [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) § 4 — the module's single real permission rule (`PHC_AUTH_001`–`003`).

## 4. References

- **Frontend:** `../carmen-inventory-frontend-react/constant/permissions.ts`; `routes/inventory-management/physical-count/`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts`.
- **API contracts:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/physical-count*/`.
- Related: [physical-count/03-user-flow](/en/inventory/physical-count/03-user-flow) (overview), [physical-count/04-test-scenarios-audit-config](/en/inventory/physical-count/04-test-scenarios-audit-config) (parallel correction page on the test-scenarios side).
