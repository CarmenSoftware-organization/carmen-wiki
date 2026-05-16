---
title: Templates
description: Reusable scaffold definitions consumed by PR and Vendor Pricelist — shared mechanics for seed-only documents that prefill a new transactional record on instantiation.
published: true
date: 2026-05-17T11:00:00.000Z
tags: templates, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T16:00:00.000Z
---

# Templates

> **At a Glance**
> **Module purpose:** Seed-only scaffolds (PR draft, RFQ / pricelist round) that deep-copy header and detail rows into a new transactional record on instantiation &nbsp;·&nbsp; **Audience:** Requestor (PR), Purchaser (pricelist), Sysadmin &nbsp;·&nbsp; **Key entities/tables:** `tb_purchase_request_template`, `tb_pricelist_template` &nbsp;·&nbsp; **Sub-pages:** 2

## 1. Overview

Templates in Carmen are *seed-only* documents — they themselves never enter a workflow or post to any ledger. Their purpose is to prefill a new transactional record (a PR draft, an RFQ pricelist round) with header values and detail rows that the operator would otherwise re-enter every time. When a user picks **Create from Template**, the relevant fields are cloned into a brand-new draft record; from that point on the new record is independent and the template is unchanged.

## 2. Shared Mechanics

The behaviours below apply to every template variant in the system:

- **Seed-only persistence.** Template tables (`tb_purchase_request_template`, `tb_pricelist_template`) carry their own primary key and audit columns, but are never referenced as parents by transactional records.
- **Clone semantics.** Instantiation deep-copies the header and detail rows into the new transactional record. Subsequent template edits do **not** propagate to records already created from it.
- **Lifecycle.** `draft` (editable, not yet selectable in pickers) → `active` (selectable when creating new records) → `inactive` (retired from new pickers, still readable on historical records).
- **Soft-delete + audit columns.** Same convention as every other configuration table — `created_*`, `updated_*`, `deleted_*` are present, and hard-delete is blocked once the template has been used at least once.
- **Currency / workflow snapshot.** Where the template carries currency, workflow, or tax-profile references, those resolve to the *current* configuration at clone time. Changing them on the template later affects only future clones.

## 3. Pages in This Module

- [[templates/purchase-request]] — PR scaffold cloned via "Create PR from Template" in the procurement UI.
- [[templates/price-list]] — RFQ / pricelist scaffold defining currency, validity, reminder schedule, and escalation rules.

## 4. Related Modules

- [[purchase-request]] — primary consumer of PR templates (Requestor persona, REQ-HP-06 scenario).
- [[vendor-pricelist]] — primary consumer of pricelist templates (Purchaser starting an RFQ round).
- [[system-config/workflow]] — workflow assignment carried on PR templates.
- [[master-data/currency]] — currency resolved on pricelist templates.

## 5. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/procurement/purchase-request-template/` — PR template frontend page.
- `../carmen-inventory-frontend/app/(root)/(protected)/vendor-management/price-list-template/` — Pricelist template frontend page.
- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — template-based PR creation flow.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_purchase_request_template`, `tb_pricelist_template`.
