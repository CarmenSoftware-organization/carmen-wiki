---
title: System Configuration
description: Document-flow and accounting-period system configuration — workflow, period, dimensions, numbering.
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# System Configuration

> **At a Glance**
> **Module purpose:** Document-flow and accounting-period machinery — approval workflows, accounting periods, dimensions, document numbering, app config, menu &nbsp;·&nbsp; **Audience:** Sysadmin, Workflow Administrator, Finance (period close) &nbsp;·&nbsp; **Key entities/tables:** `tb_workflow`, `tb_period`, `tb_dimension`, `tb_config_running_code`, `tb_application_config`, `tb_menu` &nbsp;·&nbsp; **Sub-pages:** 9

![System Configuration screen](/screenshots/system-config/index.png)

## 1. Overview

System Configuration is the umbrella for the **document-flow and accounting-period machinery** that every transactional module depends on. Workflows define multi-stage approval routing with per-stage actions, recipients, and field visibility. Periods define the accounting calendar and gate which dated postings are allowed. Dimensions are the user-extensible custom-field system threaded through every transactional table. Running codes drive document numbering. Application config is the generic key-value escape hatch. The menu registry feeds the app shell.

The six entities here sit between [master-data](/en/inventory/master-data) (the static catalogues — units, vendors, currencies) and the runtime [access-control](/en/inventory/access-control) layer (users, roles, permissions). Where master data answers *what* a transaction is referencing, system configuration answers *how* it should flow, *when* it should post, and *what extra dimensions* it should carry. Most rows are owned and edited by Sysadmin; a few — workflow stages and dimension catalogues in particular — see day-to-day adjustment from a designated Workflow Administrator.

All six entities live in the **tenant** schema. None of them have a platform counterpart — they describe per-property document flow, so each tenant gets its own copy.

## 2. Audience

Sysadmin. Workflow definition may be delegated to a Workflow Administrator persona (typically the Finance Manager or Procurement Manager) for day-to-day stage / approver maintenance. Finance owns period close.

## 3. Entity List

| Entity | Purpose | Managed by |
| ------ | ------- | ---------- |
| [workflow](/en/inventory/system-config/workflow) | Multi-stage approval workflows with per-stage actions, recipients, field visibility | Sysadmin / Workflow Admin |
| [period](/en/inventory/system-config/period) | Accounting periods (open/closed/locked) and per-period inventory snapshots | Sysadmin / Finance |
| [dimension](/en/inventory/system-config/dimension) | User-defined custom fields with per-place display matrix | Sysadmin |
| [running-code](/en/inventory/system-config/running-code) | Document-number patterns per document type | Sysadmin |
| [application-config](/en/inventory/system-config/application-config) | Tenant-wide key-value settings + per-user preference overrides | Sysadmin |
| [menu](/en/inventory/system-config/menu) | Navigation registry rendered by the app shell | Sysadmin |

## 4. Cross-Module Dependencies

- [purchase-request](/en/inventory/purchase-request) requires [system-config/workflow](/en/inventory/system-config/workflow) (PR approval routing), [system-config/running-code](/en/inventory/system-config/running-code) (PR number), [system-config/dimension](/en/inventory/system-config/dimension) (PR header/detail tagging).
- [purchase-order](/en/inventory/purchase-order) requires [system-config/workflow](/en/inventory/system-config/workflow) (PO approval routing where policy demands it), [system-config/running-code](/en/inventory/system-config/running-code) (PO number), [system-config/dimension](/en/inventory/system-config/dimension) (PO header/detail tagging).
- [good-receive-note](/en/inventory/good-receive-note) requires [system-config/period](/en/inventory/system-config/period) (posting-date guard), [system-config/running-code](/en/inventory/system-config/running-code) (GRN number), [system-config/dimension](/en/inventory/system-config/dimension) (GRN header/detail tagging), [system-config/workflow](/en/inventory/system-config/workflow) (optional approval).
- [store-requisition](/en/inventory/store-requisition) requires [system-config/workflow](/en/inventory/system-config/workflow) (SR approval routing — canonical multi-stage workflow), [system-config/running-code](/en/inventory/system-config/running-code) (SR number), [system-config/dimension](/en/inventory/system-config/dimension) (issue tagging — project / event).
- [inventory-adjustment](/en/inventory/inventory-adjustment) requires [system-config/period](/en/inventory/system-config/period) (posting-date guard), [system-config/running-code](/en/inventory/system-config/running-code) (IA / SI / SO numbers), [system-config/dimension](/en/inventory/system-config/dimension) (stock-in / stock-out tagging), [system-config/workflow](/en/inventory/system-config/workflow) (optional approval).
- [inventory](/en/inventory/inventory) requires [system-config/period](/en/inventory/system-config/period) (period boundaries on every movement) and [system-config/dimension](/en/inventory/system-config/dimension) (cost-centre allocation on transfer).
- [costing](/en/inventory/costing) requires [system-config/period](/en/inventory/system-config/period) (the cost-close engine writes `tb_period_snapshot`).
- [physical-count](/en/inventory/physical-count) requires [system-config/period](/en/inventory/system-config/period) (count documents are frozen against a period), [system-config/running-code](/en/inventory/system-config/running-code) (count document number), [system-config/workflow](/en/inventory/system-config/workflow) (variance approval).
- [spot-check](/en/inventory/spot-check) requires [system-config/running-code](/en/inventory/system-config/running-code) (document number), [system-config/workflow](/en/inventory/system-config/workflow) (variance approval).
- [vendor-pricelist](/en/inventory/vendor-pricelist) requires [system-config/running-code](/en/inventory/system-config/running-code) (pricelist reference), [system-config/workflow](/en/inventory/system-config/workflow) (optional publish-approval), [system-config/dimension](/en/inventory/system-config/dimension) (pricelist tagging).
- [system-config/application-config](/en/inventory/system-config/application-config) and [system-config/menu](/en/inventory/system-config/menu) are referenced by every module — application-config tunes feature toggles and defaults, menu controls navigation visibility.

## 5. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`.
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` (workflow role types and the permission matrix consumed by [system-config/workflow](/en/inventory/system-config/workflow)).
- **Seed data:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/` — `tb_workflow.json`, `tb_config_running_code.json`, `tb_application_config.json`.
- **Design spec:** `.specs/2026-05-16-master-config-design.md`.
- **Plan:** `.specs/2026-05-16-master-config-plan.md`.
