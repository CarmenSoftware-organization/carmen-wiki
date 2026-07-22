---
title: Reporting and Audit
description: Activity log, MinIO-backed file attachments, notifications, reporting, dashboard widgets.
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Reporting and Audit

> **At a Glance**
> **Module purpose:** Cross-cutting plumbing for activity audit log, MinIO-backed file attachments, inbox/broadcast notifications, report generation, and dashboard widgets &nbsp;·&nbsp; **Audience:** Auditor (read), Sysadmin (config), Platform Admin (cross-tenant), every module (write) &nbsp;·&nbsp; **Key entities/tables:** `tb_activity`, `tb_file_tag` (separate file-service DB — not `tb_attachment`, which is dead), `tb_notification` + `tb_broadcast_notification`, `tb_report_template` + `tb_report_job`, `tb_dashboard_bu_widget` + `tb_dashboard_personal_widget` &nbsp;·&nbsp; **Sub-pages:** 8

![Reporting and Audit screen](/screenshots/reporting-audit/activity.png)

## 1. Overview

Reporting and Audit is the umbrella for **what happened, what was attached, who got told, what gets exported, and what gets shown on the dashboard**. Six entities cover the surface (the 8 sub-pages add two read-focused views: [reporting-audit/history](/en/inventory/reporting-audit/history) over `report`'s job table, and [reporting-audit/user-activity](/en/inventory/reporting-audit/user-activity) — a filtered view over `activity`, not a separate table). [reporting-audit/activity](/en/inventory/reporting-audit/activity) is the append-only tenant audit log — one row per meaningful state change, with actor, old/new snapshots, IP, and user agent. [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) is the MinIO-backed file registry (`tb_file_tag`, in a separate file-service database) that every transactional module links to for quotations, dockets, photos, and signed paperwork — the tenant schema's `tb_attachment` is a dead table with zero code references. [reporting-audit/notification](/en/inventory/reporting-audit/notification) is the platform-side fan-out for personal inbox messages, system/BU broadcasts, reusable templates, and news posts. [reporting-audit/report](/en/inventory/reporting-audit/report) covers on-demand viewer rendering, the print pipeline, and a job/history table that is real but currently orphaned (see that page's Implementation status callout); recurring **schedules** are not a tenant table at all — see [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) for the real backing (a generic cron-job table in the separate micro-cronjobs service). [reporting-audit/widget](/en/inventory/reporting-audit/widget) is the dashboard tile layer — BU-shared and per-user widgets bound to a code-registered dataset catalog; there is no saved-query/workspace feature anywhere in the system.

Real table locations, corrected: `tb_activity`, `tb_report_job`, `tb_dashboard_bu_widget`, and `tb_dashboard_personal_widget` live in the **tenant schema**. `tb_notification`, `tb_broadcast_notification` + `tb_user_broadcast_action`, `tb_message_format`, `tb_news`, `tb_report_template`, and `tb_print_template_mapping` live in the **platform schema**. The file registry (`tb_file_tag`) lives in a **third, separate file-service database**. Report schedules live in a **fourth, separate database** owned by the micro-cronjobs service — not in either Prisma schema. Several tables previously documented here are confirmed dead (zero non-schema code references): `tb_attachment` (tenant), `tb_report_schedule` (tenant), `tb_user_login_session` (platform), and the entire `tb_widget_dashboard`/`tb_widget_dashboard_item`/`tb_widget_default_layout`/`tb_widget_workspace` family (never existed, or dropped by migration `20260521040013_remove_widget_system`).

The entities that remain are intentionally generic / polymorphic. Activity links to its target row via `(entity_type, entity_id)` rather than typed FKs. File attachments carry no document-type discriminator — the owning row's JSONB array holds the link (`fileToken`). Notification flattens many event types into inbox/broadcast tables. Report templates bind to data through `source_type` + `source_name` rather than typed views. Widget items embed their config as JSON and reference a fixed dataset catalog entry, never a user-authored query. This deliberate genericity is what lets every transactional module plug into the umbrella without growing schema surface here.

## 2. Audience

**Auditor** owns the read path — querying activity history, reviewing notification dispatch logs. **Sysadmin** owns the configuration end — schedules, message formats. Platform Admin operates the cross-tenant surfaces (news posts, the report-template / print-mapping catalogue — outside this repo's own UI, see [reporting-audit/report](/en/inventory/reporting-audit/report)).

## 3. Entity List

| Entity | Purpose | Managed by |
| ------ | ------- | ---------- |
| [activity](/en/inventory/reporting-audit/activity) | Append-only audit log — every state change with actor, snapshots, IP, user agent | Auditor (read) / system (write) |
| [attachment](/en/inventory/reporting-audit/attachment) | MinIO-backed file registry (`tb_file_tag`, separate database) linked to owning documents via JSONB `fileToken` arrays | Owning-module users |
| [notification](/en/inventory/reporting-audit/notification) | Personal inbox + system/BU broadcasts + reusable message templates + platform news bulletins | Sysadmin / Platform Admin |
| [report](/en/inventory/reporting-audit/report) | On-demand viewer rendering + print pipeline; job/history table real but currently orphaned | Platform Admin (templates, mappings) |
| [schedule](/en/inventory/reporting-audit/schedule) | Recurring report fires — backed by a generic cron-job table in the separate micro-cronjobs service, not a tenant table | Any authenticated user (no distinct schedule-admin gate found) |
| [widget](/en/inventory/reporting-audit/widget) | Personal / BU dashboard tiles bound to a code-registered dataset catalog — no default layouts, no saved queries | User / any BU member |

## 4. Cross-Module Dependencies

- **Every transactional module** writes to [reporting-audit/activity](/en/inventory/reporting-audit/activity) through the shared audit service. [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory](/en/inventory/inventory), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [costing](/en/inventory/costing), [vendor-pricelist](/en/inventory/vendor-pricelist), [product](/en/inventory/product), and [recipe](/en/inventory/recipe) are all sources.
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [store-requisition](/en/inventory/store-requisition), [vendor-pricelist](/en/inventory/vendor-pricelist), [recipe](/en/inventory/recipe), and [product](/en/inventory/product) all attach files via [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) (quotations, dockets, photos, count sheets, contracts, yield-test sheets, product images).
- **All approval modules** drive [reporting-audit/notification](/en/inventory/reporting-audit/notification) on every workflow stage transition. The recipient set is resolved by the [system-config/workflow](/en/inventory/system-config/workflow) runtime against [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) memberships and stage role types. [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), and [vendor-pricelist](/en/inventory/vendor-pricelist) are all sources.
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), and [vendor-pricelist](/en/inventory/vendor-pricelist) each have a "Print" path that resolves through [reporting-audit/report](/en/inventory/reporting-audit/report)'s document-type print mapping. [inventory](/en/inventory/inventory), [costing](/en/inventory/costing), [product](/en/inventory/product), and [recipe](/en/inventory/recipe) are common consumers of analytical reports.
- [reporting-audit/widget](/en/inventory/reporting-audit/widget) tiles pull from the [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset) code-registered catalog — not from [reporting-audit/report](/en/inventory/reporting-audit/report) templates, a separate mechanism. Dataset content spans every transactional module above.
- [master-data/business-unit](/en/inventory/master-data/business-unit) scopes [reporting-audit/report](/en/inventory/reporting-audit/report) template / mapping access (allow / deny BU lists) and bounds visibility of BU-scoped widget dashboards (the tenant schema itself is the BU boundary).
- [access-control/user](/en/inventory/access-control/user) resolves `actor_id` / `requested_by_id` / `created_by_id` / `user_id` across every entity here, and decides visibility for personal dashboards and per-user notifications.
- [reporting-audit/schedule](/en/inventory/reporting-audit/schedule) fires dispatch through [reporting-audit/notification](/en/inventory/reporting-audit/notification) (personal, one row per recipient) — not through [reporting-audit/report](/en/inventory/reporting-audit/report)'s job table, which the fire path never writes to.

## 5. References

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity`, `tb_report_job`, `tb_dashboard_bu_widget`, `tb_dashboard_personal_widget`, plus enums `enum_activity_action`, `enum_report_format`, `enum_report_category`, `enum_report_job_status`, `enum_dashboard_widget_type`. (`tb_attachment` and `tb_report_schedule` are also declared here but are confirmed dead — zero non-schema code references.)
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_notification`, `tb_broadcast_notification`, `tb_user_broadcast_action`, `tb_message_format`, `tb_news` (+ `enum_news_status`), `tb_report_template`, `tb_print_template_mapping`. (`tb_user_login_session` is also declared here but is confirmed dead.)
- **Prisma file schema (separate database):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-file/prisma/schema.prisma` — `tb_file_tag`, the real file registry behind [reporting-audit/attachment](/en/inventory/reporting-audit/attachment).
- **micro-cronjobs (separate database, outside either Prisma schema):** `../micro-cronjobs/internal/model/cronjob.go` — the real backing for [reporting-audit/schedule](/en/inventory/reporting-audit/schedule).
- **carmen/docs (if applicable):** `../carmen/docs/workflow-permissions-system.md` — describes the workflow stage transitions that drive most notification fan-out and most audit-log writes.
- **Design spec:** `.specs/2026-05-16-master-config-design.md`.
- **Plan:** `.specs/2026-05-16-master-config-plan.md`.
