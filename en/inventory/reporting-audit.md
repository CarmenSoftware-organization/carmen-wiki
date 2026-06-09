---
title: Reporting and Audit
description: Activity log, attachments, notifications, reporting, dashboards.
published: true
date: 2026-06-09T16:26:48.000Z
tags: reporting-audit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Reporting and Audit

> **At a Glance**
> **Module purpose:** Cross-cutting plumbing for activity audit log, polymorphic attachments, inbox notifications, report job/template pipeline, and dashboard widgets &nbsp;·&nbsp; **Audience:** Auditor (read), Sysadmin (config), Platform Admin (cross-tenant), every module (write) &nbsp;·&nbsp; **Key entities/tables:** `tb_activity`, `tb_attachment`, `tb_notification`, `tb_report_template` + `tb_report_job`, `tb_widget_dashboard` &nbsp;·&nbsp; **Sub-pages:** 8

![Reporting and Audit screen](/screenshots/reporting-audit/activity.png)

## 1. Overview

Reporting and Audit is the umbrella for **what happened, what was attached, who got told, what gets exported, and what gets shown on the dashboard**. Five entities cover the surface. [reporting-audit/activity](/en/inventory/reporting-audit/activity) is the append-only tenant audit log — one row per meaningful state change, with actor, old/new snapshots, IP, and user agent. [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) is the generic file-storage entity that every transactional module links to for quotations, dockets, photos, and signed paperwork. [reporting-audit/notification](/en/inventory/reporting-audit/notification) is the platform-side fan-out for inbox messages, reusable templates, and broadcast news. [reporting-audit/report](/en/inventory/reporting-audit/report) is the four-table pipeline (tenant jobs + schedules, platform templates + print mappings) that produces every analytical export and every "Print" output. [reporting-audit/widget](/en/inventory/reporting-audit/widget) is the dashboard composition layer — per-scope dashboards, default layouts, and saved workspaces.

The umbrella spans both schemas. `tb_activity`, `tb_attachment`, `tb_report_job`, `tb_report_schedule`, `tb_widget_dashboard`, `tb_widget_default_layout`, and `tb_widget_workspace` live in the **tenant schema** because each tenant owns its own audit history, files, executions, schedules, and dashboards. `tb_notification`, `tb_message_format`, `tb_news`, `tb_report_template`, and `tb_print_template_mapping` live in the **platform schema** because notifications cross BU and tenant boundaries and report templates / print mappings are curated centrally as platform assets.

The five entities are intentionally generic / polymorphic. Activity links to its target row via `(entity_type, entity_id)` rather than typed FKs. Attachment carries no document-type discriminator — the owning row holds the link. Notification flattens many event types into a single inbox table. Report templates bind to data through `source_type` + `source_name` rather than typed views. Widget items embed their config as JSON. This deliberate genericity is what lets every transactional module plug into the umbrella without growing schema surface here.

## 2. Audience

**Auditor** owns the read path — querying activity history, reviewing notification dispatch logs, downloading scheduled compliance reports. **Sysadmin** owns the configuration end — templates, print mappings, schedules, message formats, default dashboard layouts. Platform Admin operates the cross-tenant surfaces (news posts, the standard report-template catalogue).

## 3. Entity List

| Entity | Purpose | Managed by |
| ------ | ------- | ---------- |
| [activity](/en/inventory/reporting-audit/activity) | Append-only audit log — every state change with actor, snapshots, IP, user agent | Auditor (read) / system (write) |
| [attachment](/en/inventory/reporting-audit/attachment) | Generic file storage linked to owning documents through polymorphic application FKs | Owning-module users |
| [notification](/en/inventory/reporting-audit/notification) | Per-user inbox + reusable message templates + platform news bulletins | Sysadmin / Platform Admin |
| [report](/en/inventory/reporting-audit/report) | Tenant jobs and schedules backed by platform templates and document-type print mappings | Sysadmin / Platform Admin |
| [widget](/en/inventory/reporting-audit/widget) | Personal / BU dashboards, default seed layouts, saved data-explorer workspaces | User / BU Admin / Sysadmin |

## 4. Cross-Module Dependencies

- **Every transactional module** writes to [reporting-audit/activity](/en/inventory/reporting-audit/activity) through the shared audit service. [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory](/en/inventory/inventory), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [costing](/en/inventory/costing), [vendor-pricelist](/en/inventory/vendor-pricelist), [product](/en/inventory/product), and [recipe](/en/inventory/recipe) are all sources.
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [store-requisition](/en/inventory/store-requisition), [vendor-pricelist](/en/inventory/vendor-pricelist), [recipe](/en/inventory/recipe), and [product](/en/inventory/product) all attach files via [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) (quotations, dockets, photos, count sheets, contracts, yield-test sheets, product images).
- **All approval modules** drive [reporting-audit/notification](/en/inventory/reporting-audit/notification) on every workflow stage transition. The recipient set is resolved by the [system-config/workflow](/en/inventory/system-config/workflow) runtime against [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) memberships and stage role types. [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), and [vendor-pricelist](/en/inventory/vendor-pricelist) are all sources.
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), and [vendor-pricelist](/en/inventory/vendor-pricelist) each have a "Print" path that resolves a [reporting-audit/report](/en/inventory/reporting-audit/report) template via the document-type print mapping. [inventory](/en/inventory/inventory), [costing](/en/inventory/costing), [product](/en/inventory/product), and [recipe](/en/inventory/recipe) are common consumers of analytical reports.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) tiles can embed [reporting-audit/report](/en/inventory/reporting-audit/report) templates; tile data sources span every transactional module above.
- [master-data/business-unit](/en/inventory/master-data/business-unit) scopes [reporting-audit/report](/en/inventory/reporting-audit/report) template / mapping access (allow / deny BU lists) and bounds visibility of `scope = bu` widget dashboards.
- [access-control/user](/en/inventory/access-control/user) resolves `actor_id` / `requested_by_id` / `created_by_id` across every entity here, and decides visibility for personal dashboards and per-user notifications.
- [reporting-audit/notification](/en/inventory/reporting-audit/notification) additionally consumes events written by [reporting-audit/activity](/en/inventory/reporting-audit/activity) for some workflow-driven message formats.

## 5. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity`, `tb_attachment`, `tb_report_job`, `tb_report_schedule`, `tb_widget_dashboard`, `tb_widget_default_layout`, `tb_widget_workspace`, plus enums `enum_activity_action`, `enum_report_format`, `enum_report_category`, `enum_report_job_status`, `enum_widget_dashboard_scope`, `enum_widget_accent`.
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification`, `tb_message_format`, `tb_news`, `tb_report_template`, `tb_print_template_mapping`.
- **carmen/docs (if applicable):** `../carmen/docs/workflow-permissions-system.md` — describes the workflow stage transitions that drive most notification fan-out and most audit-log writes.
- **Design spec:** `.specs/2026-05-16-master-config-design.md`.
- **Plan:** `.specs/2026-05-16-master-config-plan.md`.
