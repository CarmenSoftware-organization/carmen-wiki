---
title: System Configuration
description: Document-flow and accounting-period system configuration — workflow, period, running codes are real, working screens; dimension, menu, application-config, and query-dataset are schema/backend features with no working Sysadmin UI.
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# System Configuration

> **At a Glance**
> **Module purpose:** Document-flow and accounting-period machinery — approval workflows, accounting periods, document numbering, plus several schema-provisioned-but-unimplemented concepts (dimensions, generic app config, menu registry) &nbsp;·&nbsp; **Audience:** Sysadmin, Workflow Administrator, Finance (period close) &nbsp;·&nbsp; **Key entities/tables:** `tb_workflow`, `tb_period`, `tb_dimension`, `tb_config_running_code`, `tb_application_config`, `tb_menu` &nbsp;·&nbsp; **Sub-pages:** 11 &nbsp;·&nbsp; **Verified 2026-07-16: 6 of 11 sub-pages describe a real, reachable Sysadmin screen (workflow, period, running-code, config-email, document, dashboard-dataset); dimension and menu have no code path at all beyond a dead schema table; application-config and query-dataset are real backend capabilities with no general admin screen.**

![System Configuration screen](/screenshots/system-config/index.png)

## 1. Overview

System Configuration is the umbrella for the **document-flow and accounting-period machinery** that every transactional module depends on. Workflows define multi-stage approval routing with per-stage actions, recipients, and field visibility. Periods define the accounting calendar and gate which dated postings are allowed (via a plain CRUD screen — see [system-config/period](/en/inventory/system-config/period)). Running codes drive document numbering (via a raw-JSON edit dialog — see [system-config/running-code](/en/inventory/system-config/running-code)). Application config is a real, actively-used key-value table, but consumed key-by-key by specific features (SMTP settings, signature candidates) rather than through a general editor. Dimensions and the menu registry are **schema-provisioned but unimplemented** — no CRUD service or frontend route was found for either, in a repo-wide search of `carmen-inventory-frontend-react` and `carmen-turborepo-backend-v2`.

The six entities here sit between [master-data](/en/inventory/master-data) (the static catalogues — units, vendors, currencies) and the runtime [access-control](/en/inventory/access-control) layer (users, roles, permissions). Where master data answers *what* a transaction is referencing, system configuration answers *how* it should flow, *when* it should post, and *what extra dimensions* it should carry — the last of these ("extra dimensions") remains design intent only today. Most rows are owned and edited by Sysadmin; a few — workflow stages in particular — see day-to-day adjustment from a designated Workflow Administrator.

All six entities live in the **tenant** schema. None of them have a platform counterpart — they describe per-property document flow, so each tenant gets its own copy.

## 2. Audience

Sysadmin. Workflow definition may be delegated to a Workflow Administrator persona (typically the Finance Manager or Procurement Manager) for day-to-day stage / approver maintenance. Finance owns period close.

## 3. Entity List

| Entity | Purpose | Managed by | Implementation |
| ------ | ------- | ---------- | --------------- |
| [workflow](/en/inventory/system-config/workflow) | Multi-stage approval workflows with per-stage actions, recipients, field visibility | Sysadmin / Workflow Admin | Real screen |
| [period](/en/inventory/system-config/period) | Accounting periods (open/closed/locked) and per-period inventory snapshots | Sysadmin / Finance | Real screen — plain CRUD, no dedicated Close/Lock/Reopen actions |
| [running-code](/en/inventory/system-config/running-code) | Document-number patterns per document type | Sysadmin | Real screen — raw JSON edit, no segment builder |
| [config-email](/en/inventory/system-config/config-email) | Per-BU SMTP profile for outbound system email — workflow notifications, scheduled reports, password reset | Sysadmin by convention | Real screen; **backend has no permission guard** |
| [document](/en/inventory/system-config/document) | Tenant-scoped file-storage registry — upload, list, download, and delete for documents attached to transactional records | Sysadmin | Real screen; backed by `tb_file_tag` + MinIO (not `tb_attachment`) |
| [dashboard-dataset](/en/inventory/system-config/dashboard-dataset) | Read-only catalog of code-registered data feeds available to dashboard widgets | Sysadmin | Real screen |
| [application-config](/en/inventory/system-config/application-config) | Tenant-wide key-value settings + per-user preference overrides | No general admin screen | Real table, consumed key-by-key by config-email/signature features only |
| [query-dataset](/en/inventory/system-config/query-dataset) | SQL Workbench — author tenant views, stored procedures, and functions as reusable data sources | No admin screen found | Real backend service; **no frontend route exists** |
| [dimension](/en/inventory/system-config/dimension) | User-defined custom fields with per-place display matrix | Nobody — no CRUD path | Schema only; no service, controller, or route found |
| [menu](/en/inventory/system-config/menu) | Navigation registry rendered by the app shell | Nobody — table unused | Schema only; zero non-schema code references; nav is a static frontend constant |
| [doc-version](/en/inventory/system-config/doc-version) | Optimistic-concurrency `doc_version` guard — clients echo the version on save or get a 409 | Engineering | Cross-cutting mechanism, not a screen |

## 4. Cross-Module Dependencies

**Workflow attachment is narrower than a prior version of this list claimed.** `enum_workflow_type` has exactly three values — `purchase_request`, `store_requisition`, `purchase_order` — confirmed against the Prisma schema. GRN, inventory-adjustment, physical-count, spot-check, and vendor-pricelist have **no `workflow_type` enum member** and cannot attach a `tb_workflow` row; any "optional approval" language for those modules below has been corrected. Likewise, [system-config/dimension](/en/inventory/system-config/dimension)'s tagging claims have been corrected module-wide — the `dimension` JSONB column exists on these tables but no code was found that reads or writes it anywhere (see that page's Implementation status).

- [purchase-request](/en/inventory/purchase-request) requires [system-config/workflow](/en/inventory/system-config/workflow) (PR approval routing — real, `workflow_type = purchase_request`), [system-config/running-code](/en/inventory/system-config/running-code) (PR number). `dimension` column present, unused.
- [purchase-order](/en/inventory/purchase-order) requires [system-config/workflow](/en/inventory/system-config/workflow) (PO approval routing — real, `workflow_type = purchase_order`, though `tb_purchase_order.workflow_id` is a loose UUID field, not a declared Prisma relation), [system-config/running-code](/en/inventory/system-config/running-code) (PO number). `dimension` column present, unused.
- [good-receive-note](/en/inventory/good-receive-note) requires [system-config/period](/en/inventory/system-config/period) (posting-date guard), [system-config/running-code](/en/inventory/system-config/running-code) (GRN number). **No workflow attachment** — `goods_received_note` is not a member of `enum_workflow_type`.
- [store-requisition](/en/inventory/store-requisition) requires [system-config/workflow](/en/inventory/system-config/workflow) (SR approval routing — real, `workflow_type = store_requisition`), [system-config/running-code](/en/inventory/system-config/running-code) (SR number).
- [inventory-adjustment](/en/inventory/inventory-adjustment) requires [system-config/period](/en/inventory/system-config/period) (posting-date guard), [system-config/running-code](/en/inventory/system-config/running-code) (IA / SI / SO numbers). **No workflow attachment.**
- [inventory](/en/inventory/inventory) requires [system-config/period](/en/inventory/system-config/period) (period boundaries on every movement). `dimension` column present, unused.
- [costing](/en/inventory/costing) requires [system-config/period](/en/inventory/system-config/period) (the cost-close engine writes `tb_period_snapshot`).
- [physical-count](/en/inventory/physical-count) requires [system-config/period](/en/inventory/system-config/period) (count documents are frozen against a period), [system-config/running-code](/en/inventory/system-config/running-code) (count document number). **No workflow attachment.**
- [spot-check](/en/inventory/spot-check) requires [system-config/running-code](/en/inventory/system-config/running-code) (document number). **No workflow attachment.**
- [vendor-pricelist](/en/inventory/vendor-pricelist) requires [system-config/running-code](/en/inventory/system-config/running-code) (pricelist reference). **No workflow attachment.**
- [system-config/application-config](/en/inventory/system-config/application-config) is a real table, but consumed key-by-key by specific features (SMTP config, signature settings) — not a general feature-flag layer read by every module. [system-config/menu](/en/inventory/system-config/menu) has no confirmed consumer anywhere; navigation is a static frontend constant instead.

## 5. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`.
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` (workflow role types and the permission matrix consumed by [system-config/workflow](/en/inventory/system-config/workflow)).
- **Seed data:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/` — `tb_workflow.json`, `tb_config_running_code.json`, `tb_application_config.json`.
- **Design spec:** `.specs/2026-05-16-master-config-design.md`.
- **Plan:** `.specs/2026-05-16-master-config-plan.md`.
