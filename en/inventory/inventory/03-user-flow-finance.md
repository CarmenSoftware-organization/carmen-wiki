---
title: Inventory — User Flow — Finance (correction)
description: Correction page — no Finance role, GL reconciliation, or period-lock flow exists in the inventory module; this page documents what replaced the earlier draft.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory, user-flow, finance, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow — Finance (correction)

> **At a Glance**
> **Status:** corrected 2026-07-15 — the Finance persona flow previously documented here (cost-impact approval queue, inventory-to-GL reconciliation dashboard, period-lock progression) **does not exist in the product**.
> **What is real:** the period-end close, executable by any user holding `inventory_management.period_end.execute` — documented in [period-end](/en/inventory/inventory/period-end) and [03-user-flow-inventory-controller](/en/inventory/inventory/03-user-flow-inventory-controller).

## 1. What this page previously claimed, and why it was removed

An earlier draft described a Finance Officer / Finance Manager persona with four flows: a cost-impact approval queue for above-threshold adjustments, a weekly inventory-to-GL reconciliation dashboard, a period-end orchestration flow with a reconciliation journal, and a `closed → locked` period-lock progression. Verification against current source found none of it:

- **No Finance role exists.** `enum_stage_role` (Prisma tenant schema) is `{create, approve, purchase, issue, view_only}` — no `finance` member. The permission catalogue (`carmen-inventory-frontend-react/constant/permissions.ts`) has no finance-scoped key.
- **No inventory-to-GL code exists.** A GL core arrived in 2026-09 (`tb_gl_jv*` tables, `apps/micro-business/src/gl/`, manual journal vouchers under `/api/{bu}/gl-posting`), but a repo-wide search of `carmen-turborepo-backend-v2` for journal/GL posting *from inventory movements* still finds nothing — neither module references the other (see [01-data-model](/en/inventory/inventory/01-data-model) § 1). There is no reconciliation dashboard, tolerance, or compensating-journal mechanism.
- **No threshold-based approval chain exists.** Zero `threshold` hits in the inventory / stock-in / stock-out / period-end services ([02-business-rules](/en/inventory/inventory/02-business-rules) § 4 correction).
- **No lock/reopen flow exists in this module.** `period-end.controller.ts` exposes only `find-all` / `find-current` / `find-review` / `start-counting` / `close`. `enum_period_status.locked` is set by the inventory-period service (`/api/{bu}/inventory-periods`) behind [system-config/period](/en/inventory/system-config/period).

This mirrors the identical Finance-persona findings already confirmed in [purchase-order](/en/inventory/purchase-order/03-user-flow-finance), [good-receive-note](/en/inventory/good-receive-note/03-user-flow-finance), and [store-requisition](/en/inventory/store-requisition).

## 2. Where the real behaviour lives

| Formerly claimed here | Actual mechanism | Page |
|---|---|---|
| Finance triggers the period close | Any user with `inventory_management.period_end.execute` clicks **Close period** on `/inventory-management/period-end/review` | [period-end](/en/inventory/inventory/period-end) |
| Reconciliation gates the close | The real gates are mid-state SR / GRN / CN / SI / SO documents + completed physical counts (PR/PO no longer gate), preceded by a start-counting gate on open stock-moving documents | [02-business-rules](/en/inventory/inventory/02-business-rules) `INV_POST_009` / `INV_POST_009a` |
| Period lock after audit window | `locked` is managed by the system-config period service, not here | [system-config/period](/en/inventory/system-config/period) |
| Cost-impact approval of adjustments | Stock-in/stock-out documents live in the inventory-adjustment module; no Finance tier exists | [inventory-adjustment](/en/inventory/inventory-adjustment) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/period-end/period-end.controller.ts` (the complete endpoint surface), `.../inventory-transaction/inventory-transaction.service.ts` (no GL fan-out).
- Frontend: `../carmen-inventory-frontend-react/constant/permissions.ts` (`inventory_management.period_end.view` / `.execute`).
- Parent overview: [03-user-flow](/en/inventory/inventory/03-user-flow).
