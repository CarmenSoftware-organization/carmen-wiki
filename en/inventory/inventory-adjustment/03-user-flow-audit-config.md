---
title: Inventory Adjustment — User Flow — Audit & Config
description: Correction notice — no dedicated Auditor or System Administrator surface exists for this module beyond the generic reason-code master.
published: true
date: 2026-07-15T17:02:22.000Z
tags: inventory-adjustment, user-flow, audit, sysadmin, carmen-software
editor: markdown
dateCreated: 2026-05-15T13:00:00.000Z
---

# Inventory Adjustment — User Flow — Audit & Config

> **Correction notice.** This page previously described a System Administrator configuring reason-code GL mappings, tenant thresholds, and RBAC, plus an Auditor running SoD-compliance checks, lot-recall traces, and void-chain verification specific to this module. None of it exists in the current source, beyond the real (and much smaller) reason-code master-data screen.

## What was checked

- The only real configuration surface for this module is the reason-code master (`/config/adjustment-type`, [master-data/adjustment-type](/en/inventory/master-data/adjustment-type)), which is a plain CRUD screen for `code`, `name`, `type` (`stock_in`/`stock_out`), `description`, `note`, `is_active` — no GL-account field, no document-required flag, no quality-check flag, no threshold configuration of any kind.
- A repo-wide search for `threshold` scoped to this module and its shared services found zero hits.
- A repo-wide search for a segregation-of-duties cross-check (e.g. a `buyer_id`/`created_by_id` comparison between a receipt and a write-off) found no matching code in `stock-in.service.ts` / `stock-out.service.ts`.
- No lot-recall trace screen, void-chain verification screen, or audit-trail workspace specific to this module was found in the frontend routes.
- The only E2E spec touching this module's config surface is `031-adjustment-type.spec.ts`, which covers ordinary reason-code CRUD (code uniqueness, active/inactive toggle) — nothing threshold- or GL-related.

## Claim status

| Previously claimed | Status | What the source actually shows |
| ------------------- | ------ | -------------------------------- |
| System Administrator sets `info.glAccount`, `requiresDocument`, `requiresQualityCheck`, thresholds | **Fabricated** | `tb_adjustment_type` has no such fields; the real reason-code screen only edits `code`/`name`/`type`/`description`/`note`/`is_active`. |
| Auditor runs SoD-compliance checks, lot-recall traces, void-chain verification for this module | **Fabricated** | No matching route, component, or backend query was found. |
| Configuration changes apply "prospectively" to a threshold ladder | **Fabricated** | There is no threshold ladder to apply changes to. |

## Where to look instead

- [master-data/adjustment-type](/en/inventory/master-data/adjustment-type) — the real reason-code CRUD screen.
- [03 — User Flow](/en/inventory/inventory-adjustment/03-user-flow) — the actual document lifecycle for this module.
- [02 — Business Rules](/en/inventory/inventory-adjustment/02-business-rules) — the module's real rules, with no authorization ladder.
- E2E: `../carmen-inventory-frontend-e2e/tests/031-adjustment-type.spec.ts` — the real reason-code CRUD spec.
