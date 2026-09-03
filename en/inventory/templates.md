---
title: Templates
description: Reusable scaffold definitions consumed by PR and Vendor Pricelist — two structurally different implementations, not one shared mechanic, despite both prefilling a new record on instantiation.
published: true
date: 2026-07-29T04:21:35.000Z
tags: templates, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T16:00:00.000Z
---

# Templates

> **At a Glance**
> **Module purpose:** Reusable scaffolds (PR line-bundle, RFQ pricelist round) that prefill a new record's fields on selection &nbsp;·&nbsp; **Audience:** Requestor (PR), Product Admin / Procurement Lead (pricelist), Product Admin (PR template maintenance) &nbsp;·&nbsp; **Key entities/tables:** `tb_purchase_request_template` (+ detail, comment), `tb_pricelist_template` (+ detail, comment) &nbsp;·&nbsp; **Sub-pages:** 2

![Templates screen](/screenshots/templates/purchase-request.png)

![Templates detail screen](/screenshots/templates/purchase-request-detail.png)

> **Implementation status (verified 2026-07-29):** the two templates in this module are **not** built the same way, despite the surface-level similarity of "pick a template, get a prefilled record." PR templates deep-clone nothing — selecting one just pre-fills the new-PR form client-side, and the resulting PR keeps no link back to the template. Pricelist templates keep a live, persisted FK (`tb_request_for_pricing.pricelist_template_id`) from every RFQ round issued against them. Delete semantics also diverge: PR template delete is an unconditional hard delete; pricelist template delete is an unconditional soft delete. See each sub-page's own implementation-status callout for the full detail — this page no longer asserts one uniform mechanic for both.

## 1. Overview

Templates in Carmen are configuration, not transactional documents — neither variant enters a workflow or posts to a ledger itself. Their purpose is to prefill a new transactional record (a PR draft, an RFQ pricelist round) with values the operator would otherwise re-enter every time. Beyond that shared purpose, the two implementations differ in ways the rest of this page documents rather than glosses over: whether the new record retains any link to the template, whether deletion is hard or soft, and whether "lifecycle" is a single boolean or a real status enum.

## 2. Shared Mechanics

What genuinely holds across both variants:

- **Neither posts anywhere.** No GL, AP, or inventory effect from creating, editing, or deleting a template of either kind.
- **Neither participates in a workflow.** No `doc_status`, no `workflow_current_stage`, no approval chain on the template row itself.
- **Both carry standard audit columns** (`created_*`, `updated_*`, `deleted_*`) and a `doc_version` optimistic-lock counter on the header.
- **Both expose Name-uniqueness and CRUD via a dedicated route** (`/procurement/purchase-request-template`, `/vendor-management/price-list-template`) with list/detail/new screens.

What does **not** hold across both — see the two sub-pages for specifics:

| | PR Template | Price List Template |
|---|---|---|
| Instantiation mechanism | Client-side form pre-fill only (no backend clone endpoint) | N/A — the template isn't "instantiated"; RFQ rounds reference it by FK |
| Link from the new/derived record back to the template | None — no `created_from_template_id` or equivalent column anywhere | Live — `tb_request_for_pricing.pricelist_template_id` persists |
| Lifecycle field | Single boolean `is_active`, no "draft" state | Real 3-value enum `status` (`draft`/`active`/`inactive`) |
| Delete semantics | Unconditional **hard delete**, no usage guard | Unconditional **soft delete** (`status = inactive` + `deleted_at`), no usage guard |
| Line/detail content | Location, product, unit, qty, currency only — tax/discount/FOC/dimension are schema-only | Per-product MOQ tiers (`order_unit_obj` JSON array) — this module's actual payload |

## 3. Pages in This Module

- [templates/purchase-request](/en/inventory/templates/purchase-request) — PR line-bundle scaffold, pre-filled into a new PR via "Create PR from Template" in the procurement UI.
- [templates/price-list](/en/inventory/templates/price-list) — RFQ / pricelist scaffold defining currency, validity, vendor instructions, and a product/MOQ list; `reminder_days`/`escalation_after_days` exist on the table but are inert (no UI, no job reads them).

## 4. Related Modules

- [purchase-request](/en/inventory/purchase-request) — consumer of PR templates (Requestor persona, REQ-HP-06 scenario).
- [vendor-pricelist](/en/inventory/vendor-pricelist) — consumer of pricelist templates; RFQ (Request for Pricing) rounds carry the persisted `pricelist_template_id` FK.
- [system-config/workflow](/en/inventory/system-config/workflow) — workflow assignment carried on PR templates (`workflow_id`).
- [master-data/currency](/en/inventory/master-data/currency) — currency existence-checked (not `is_active`-checked) on pricelist templates.

## 5. Reference Sources

- `../carmen-inventory-frontend-react/routes/procurement/purchase-request-template/` — PR template frontend (`prt-form.tsx`, `prt-form-schema.ts`, `prt-item-table.tsx`).
- `../carmen-inventory-frontend-react/routes/vendor-management/price-list-template/` — Pricelist template frontend (`plt-form.tsx`, `plt-form-schema.ts`, `plt-form-products-section.tsx`).
- `../carmen-inventory-frontend-react/routes/procurement/purchase-request/new-purchase-request-content.tsx` + `pr-form-schema.ts` — where a PR template's fields actually get merged into a new PR.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-request-template/purchase-request-template.service.ts` — real PR-template data layer (direct Prisma).
- `../carmen-turborepo-backend-v2/apps/micro-business/src/master/price-list-template/price-list-template.service.ts` — real pricelist-template data layer (direct Prisma); `apps/backend-gateway/src/application/pricelist-templates/` is a thin TCP proxy in front of it.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_purchase_request_template` (+detail/comment, lines 2635-2797), `tb_pricelist_template` (+detail/comment, lines 4222-4360), `tb_request_for_pricing` (lines 4400-4429).
- `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts`, `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` — E2E specs; both contain `describe` blocks for features not present in current code (PR template "Clone"/"Set as Default"; pricelist template's removed Clone, confirmed via its own dedicated "(removed)" suite).
