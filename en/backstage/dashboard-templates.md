---
title: Dashboard Templates
description: Platform-managed dashboard widget templates - read-only "system" widgets shown on every BU's module dashboards and a versioned "BU default" set that staff deploy into each business unit's own dashboard.
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, dashboard-templates
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Dashboard Templates

The **Dashboard Templates** module lets platform staff decide which dashboard widgets every business unit sees without anyone configuring them per BU. A template is one widget definition: a **dataset** from the micro-data catalog, a **render type** (KPI, line, bar, ...), a bilingual title, optional dataset parameters, and a position. Templates come in two kinds that behave very differently:

| Kind | Where it shows up | How it reaches a BU |
|---|---|---|
| **System** (`system`) | The per-module dashboard pages (procurement, inventory, product, config, vendor-management, operation-plan, store-operation) of **every** BU, read-only | Read live by the gateway at request time through a 60-second cache; optionally restricted per BU with allow/deny code lists |
| **BU default** (`bu_default`) | The BU's own editable widget board (`tb_dashboard_bu_widget`), including the main `/dashboard` page | **Copied** into the BU's tenant database by an explicit **Deploy** action, tracked against a single global version number |

> **At a Glance**
> **Screen:** `DashboardTemplateManagement` with tabs System / BU default / Deploy &nbsp;·&nbsp; **Route:** `/dashboard-templates` (`?tab=system|bu_default|deploy`) &nbsp;·&nbsp; **Nav:** group `navGroup.content`, `permission: 'dashboard_template.read'`, `feature: 'dashboard_templates'` (`backstageNav.ts:30`) &nbsp;·&nbsp; **Permission keys:** `dashboard_template.read` / `.create` / `.update` / `.delete` / `.deploy` &nbsp;·&nbsp; **API:** `/api-system/dashboard-templates[/...]` &nbsp;·&nbsp; **Tables:** `tb_dashboard_widget_template`, `tb_dashboard_bu_default_version` &nbsp;·&nbsp; **Sub-pages:** 3 &nbsp;·&nbsp; **e2e suite:** none

## 1. Overview

The page is one route with a `TabStrip`. **System** and **BU default** share `TemplateListPanel` (a module picker, a widget table, reorder arrows and an add/edit dialog); **Deploy** is a separate `DeployPanel` that lists every business unit with its deploy status. The Deploy tab is hidden unless the viewer holds `dashboard_template.deploy`; a `?tab=deploy` URL without that permission falls back to System (`DashboardTemplateManagement.tsx`).

The module has no widget *designer*. Everything a template can render comes from the dataset catalog owned by micro-data (`GET /api/dashboard-lab/datasets`, reached through `GET /api-system/dashboard-templates/datasets`): each dataset declares its shape, parameters and the render types it supports, and the dialog only offers valid combinations. This is the same registry the inventory dashboard uses, see §6.

## 2. Business Context

Hotels in a cluster should open Carmen and find a sensible dashboard from day one, and platform staff should be able to roll out a new KPI to every property. Two mechanisms cover the two needs:

- **System widgets** are the "always there" tiles. Because they are read live, changing one (or toggling it inactive) shows up for all BUs with no per-BU action: the gateway drops its cache on every system write, and the cache TTL is 60 seconds (`TTL_MS`, `system-widget-cache.service.ts`). The cache is in-process, so with several gateway instances the other instances catch up only when their own TTL expires.
- **BU default widgets** are a starter board. Once deployed, the BU owns the copy and may edit it. Staff then decide, per BU, whether a later redeploy may overwrite those edits (§4).

## 3. Key Concepts

### 3.1 Modules

`module` is one of `procurement`, `inventory`, `product`, `config`, `vendor-management`, `operation-plan`, `store-operation` (`DASHBOARD_MODULES`, `dashboardTemplates/modules.ts`). For `bu_default` templates the picker adds **Main**, which the wire format sends as `module: null` and means the BU's main `/dashboard` page. Rule enforced by the API and a database CHECK: **`module = null` is allowed only for `bu_default`**; a system template must name a module.

### 3.2 System vs BU default rules

| Rule | Source |
|---|---|
| `allow_business_unit` / `deny_business_unit` apply to `system` only; a `bu_default` write carrying a non-empty list is rejected | create: DTO refine (`dashboard-template.dto`); edit: `validateUpdate`, 422 |
| Visibility of a system widget for BU code `X`: deny list wins; an empty/null allow list means everyone, otherwise `X` must be in it | `visibleToBu` (`dashboard-widgets/visible-to-bu.ts`) |
| `dataset_id` must exist in the micro-data catalog and `widget_type` must be in that dataset's `supported_renders`, else 422 ("Unknown dataset", "cannot render as ...") | `validateAgainstCatalog` |
| `en` title is required whenever a `th` title is given | dialog guard + `normalizeTitleI18n` |
| `display` JSON must serialize to at most 8 KB | create/update zod refine |
| Any create/update/delete/reorder of a `bu_default` row bumps the global BU-default version by 1 | `bumpBuDefaultVersion`, same transaction as the write |
| Writes to `system` rows clear the gateway's system-widget cache immediately | `systemWidgetCache.invalidate()` |

### 3.3 Titles

A title is stored twice: legacy `title` (= English) and `title_i18n` (`{ en, th? }`). The SPA writes both. On the list a row with no title falls back to the dataset's name, labelled "(Dataset name)". A header badge shows Thai coverage ("Thai titles n/m") and turns amber when any titled row lacks Thai.

## 4. Deploying BU defaults (summary)

Deploy pushes the **active** BU-default set to selected business units. Each BU has a status derived from its tenant deploy row and the current version:

| Status | Meaning |
|---|---|
| `never` | BU has no deploy row; nothing was ever deployed |
| `customized` | BU admin edited the board after the last deploy (`customized_at` set) |
| `outdated` | Deployed earlier, deployed version is lower than the current version, not customized |
| `current` | Deployed at the current version |

Two modes: **skip_customized** (default; BUs flagged customized are skipped) and **overwrite** (replaces the BU's widgets; the dialog forces typing `OVERWRITE`). Full flow, concurrency, and failure modes are in [Lifecycle](/en/backstage/dashboard-templates/lifecycle).

## 5. Permissions

| Action | Required key | Notes |
|---|---|---|
| Open page, list templates, list datasets, read version | `dashboard_template.read` | |
| Add widget | `dashboard_template.create` | API also requires a backstage-wide grant |
| Edit, **reorder** | `dashboard_template.update` | Reorder arrows live inside the same `<Can>` as Edit |
| Delete | `dashboard_template.delete` | |
| Deploy tab, deploy status, deploy | `dashboard_template.deploy` | Status endpoint is gated by `deploy`, not `read` |

Write and deploy endpoints combine `BackstagePermissionGuard` with `BackstageWidePermissionGuard`, so cluster-scoped grants do not count (super-admin or backstage-wide grant only). SPA checks pass `BACKSTAGE_SCOPED_RECORD`.

**Default roles** (`seed.backstage-role-permission.data.ts`): Backstage Admin holds `dashboard_template.*` (so includes `deploy`); Support Manager and Support Staff hold `dashboard_template.read` only: they see the System and BU default tabs without buttons and never see the Deploy tab; Security Officer holds none.

## 6. Relationship to the Inventory dashboard

Verified in source, not inferred:

- The dataset catalog the template dialog offers is the one micro-data serves at `/api/dashboard-lab/datasets`, the same registry documented in [Dashboard Dataset](/en/inventory/system-config/dashboard-dataset) and consumed by the inventory [Dashboard](/en/inventory/dashboard) widget picker ([Widget Workspace](/en/inventory/dashboard/widget-workspace)).
- System templates are served to tenants by `GET /api/:bu_code/dashboard-widgets/<module>` (for example `/inventory`), each item bundled with live dataset values (`system-widgets.controller.ts`, `SystemWidgetCache.forBu`).
- Deployed BU defaults land in the tenant table `tb_dashboard_bu_widget`, documented from the tenant side in [Reporting Audit: Widget](/en/inventory/reporting-audit/widget). That page notes no inventory screen reads BU widgets today; the deploy pipeline here still writes them.

## 7. Edge Cases

| Case | Behaviour |
|---|---|
| Dataset removed from the catalog | Row stays; list shows a red "Dataset no longer exists" badge once the catalog loaded successfully (`datasetMissing`). A migration named `20261006120000_dashboard_template_dead_dataset_ids` exists for ids that stopped existing in the catalog. |
| Change dataset in the dialog | Widget type resets to the first render the new dataset supports; params reset to the dataset defaults. |
| Reorder | Swaps with the neighbour and renumbers the whole module as 10, 20, 30...; arrows disabled at the ends. |
| Deploy while the set is empty | Deploy tab shows a red alert and disables the buttons; API answers 422. |
| Someone edits BU defaults mid-deploy | Version no longer matches `expected_version`: 409, whole run stops (see Lifecycle). |
| Delete a template | Soft delete; BU-default deletes also bump the version, so every deployed BU becomes `outdated`. |

## 8. Sub-pages

- [Data Model](/en/backstage/dashboard-templates/data-model) - template table, version table, the tenant deploy row.
- [UI Screens](/en/backstage/dashboard-templates/ui-screens) - the three tabs, dialogs, columns.
- [Lifecycle](/en/backstage/dashboard-templates/lifecycle) - CRUD side effects, version bumping, status and deploy flow.

## 9. References

- SPA: `../carmen-backstage/src/pages/DashboardTemplateManagement.tsx`, `src/pages/dashboardTemplates/*`, `src/services/dashboardTemplateService.ts`, `src/types/index.ts` (`DashboardTemplate`, line 2010).
- Gateway: `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage_dashboard-templates/` (`api-system/dashboard-templates`, deploy under `api-system/dashboard-templates/deploy`).
- Micro-cluster: `apps/micro-cluster/src/cluster/dashboard-template/`. Micro-data: `micro-data/service/bu_widget_deploy.go`.
- Related: [Report Templates](/en/backstage/report-templates) (the other "Content" group module), [Feature Flags](/en/backstage/feature-flags).
