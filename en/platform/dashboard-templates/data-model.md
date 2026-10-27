---
title: Dashboard Templates — Data Model
description: The backstage tables behind dashboard templates (tb_dashboard_widget_template, tb_dashboard_bu_default_version), the enums they use, and the tenant-side deploy row that records what a business unit received.
published: true
date: 2026-10-27T00:00:00.000Z
tags: book/platform, dashboard-templates, data-model
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Dashboard Templates — Data Model

> **At a Glance**
> **Tables:** 2 owned (backstage DB) + 2 referenced (tenant DB) &nbsp;·&nbsp; **Enums:** `enum_dashboard_widget_type`, `enum_dataset_shape` &nbsp;·&nbsp; **Audit columns:** `doc_version`, `created_*`, `updated_*`, `deleted_*` on the template table &nbsp;·&nbsp; **DB-level rules:** kind and module CHECK constraints, single-row version table &nbsp;·&nbsp; **Divergences vs SPA:** 2 minor

> **Source of truth:** Backend Prisma backstage schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma`
> - `.../prisma/migrations/20261006100000_dashboard_widget_template/migration.sql` (CHECK constraints are only here)
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

Templates live in the **backstage (system) database**. Two tables: the template rows, and a one-row counter that versions the whole BU-default set. When a deploy runs, the data leaves the backstage database: widgets are written into each business unit's own **tenant** database (`tb_dashboard_bu_widget`) and the outcome is recorded in a one-row tenant table (`tb_dashboard_bu_widget_deploy`). The tenant tables are owned by the tenant schema and micro-data and are only summarized here.

## 2. Entities

### 2.1 `tb_dashboard_widget_template`

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| **Identity** | | | |
| `id` | `String @id @db.Uuid` | No | Primary key. |
| `kind` | `String @db.VarChar(20)` | No | `system` or `bu_default` (CHECK). Immutable: not in the update field list. |
| `module` | `String? @db.VarChar(50)` | Yes | Target dashboard module. `NULL` = BU's main `/dashboard`, allowed only for `bu_default` (CHECK). |
| `seed_key` | `String? @db.VarChar(100)` | Yes | Identity of seed-owned rows (`db:seed.dashboard-widget-template`); `NULL` = created through the API. |
| **Widget definition** | | | |
| `dataset_id` | `String @db.VarChar(100)` | No | Dataset id from the micro-data catalog (for example `workflow.pending-approval`). No FK; checked against the catalog on write. |
| `widget_type` | `enum_dashboard_widget_type` | No | Render type. |
| `title` | `String? @db.VarChar(255)` | Yes | Legacy English title (dual-written as `title_i18n.en`). |
| `title_i18n` | `Json? @db.JsonB` | Yes | `{ en, th? }`. Wins over `title`. |
| `order_index` | `Int @default(0)` | No | Position within (kind, module). |
| `params` | `Json? @db.JsonB` | Yes | Dataset parameters, `{ name: string \| number }`. |
| `display` | `Json? @db.JsonB` | Yes | Free-form display options; at most 8 KB serialized (micro-data rejects larger on deploy). The backstage SPA has no editor for it. |
| **Scope (system only)** | | | |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | Array of BU codes; `NULL`/`[]` = no restriction. |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | Array of BU codes; deny beats allow. |
| **Status** | | | |
| `is_active` | `Boolean @default(true)` | No | Inactive rows are neither served (system) nor deployed (bu_default). |
| **Audit** | | | |
| `doc_version` | `Int @default(0)` | No | Optimistic lock. |
| `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` | `Timestamptz(6)?` / `Uuid?` | Yes | Soft delete via `deleted_at`. |

**Constraints:** `ck_dashboard_widget_template_kind` (`kind IN ('system','bu_default')`); `ck_dashboard_widget_template_module` (module NULL only when kind is `bu_default`, otherwise one of the seven module names). Partial unique index `(seed_key) WHERE seed_key IS NOT NULL` (migration `20261006130000_dashboard_widget_template_seed_key`). **Indexes:** `@@index([kind, module, deleted_at])` (`idx_dashboard_widget_template_kind_module`).

The creating migration also inserts the initial system widgets, only when none exist.

### 2.2 `tb_dashboard_bu_default_version`

| Field | Prisma Type | Nullable | Description |
|---|---|---|---|
| `id` | `Int @id @default(1)` | No | Always `1` (CHECK `id = 1`). |
| `version` | `Int @default(0)` | No | Incremented by one on every write to a `bu_default` template: create, update, delete, reorder. Inserted as 0 by the migration; the first bump upserts to 1 if the row is missing. |
| `updated_at`, `updated_by_id` | `Timestamptz(6)?`, `Uuid?` | Yes | Who bumped it last. |

There is exactly one counter for the whole set, not one per module. Editing a single widget makes every BU `outdated`.

### 2.3 Referenced: tenant deploy row

`tb_dashboard_bu_widget_deploy` (tenant schema, `packages/prisma-shared-schema-tenant`): `id Int @id @default(1)`, `deployed_version Int`, `deployed_at`, `deployed_by_id`, `customized_at`, `customized_by_id`. Single row per tenant (CHECK `id = 1`). Maintained by micro-data: a deploy sets `deployed_version`/`deployed_at`/`deployed_by_id` and clears the customized fields; a manual edit of the BU board by a BU admin sets `customized_at` (`DeployMarkCustomized`, `micro-data/db/widget_repo.go:119`). A BU that already had BU widgets before the deploy system existed was backfilled as customized with `deployed_version = 0` (tenant migration 131). The widgets themselves are rows of `tb_dashboard_bu_widget`; see [Reporting Audit: Widget](/en/inventory/reporting-audit/widget).

## 3. Relationships

No foreign keys inside the module. Soft links only: `dataset_id` to micro-data's dataset registry, `allow/deny_business_unit` entries to `tb_business_unit.code`, and `created_by_id`/`updated_by_id` to users. The version counter relates to templates by convention (the service bumps it in the same transaction as the write; no database trigger).

## 4. Enums

| Enum | Values | Notes |
|---|---|---|
| `enum_dashboard_widget_type` | `kpi`, `line`, `area`, `bar`, `pie`, `heatmap`, `gauge`, `table`, `sparkline` | The API validates `widget_type` against this enum (zod) and then against the dataset's `supported_renders`. |
| `enum_dataset_shape` | `scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix` | Drives which renders a dataset supports; used by micro-data, shown in the dataset dropdown as `name · shape`. |

Deploy status (`never`, `customized`, `outdated`, `current`) and deploy mode (`skip_customized`, `overwrite`) are not database enums: status is computed in `deployStatusOf` (`deploy-status-of.ts`), mode is a zod enum on the deploy DTO.

## 5. Divergences from carmen-backstage SPA shape

| Area | Prisma / API | SPA type | Note |
|---|---|---|---|
| `widget_type` | enum of 9 values | `string` (`DashboardTemplate.widget_type`) | Safe: the dialog only offers renders reported by the catalog. Icons exist for the 9 enum values; any other string falls back to a neutral icon (`widgetTypes.ts`). |
| `display`, `seed_key`, `*_by_id` | present on the row | `display` typed, never edited; others absent | `display` round-trips untouched only if the SPA omits it from PATCH; it does (the dialog does not send `display`). |

Otherwise aligned with `DashboardTemplate` (`src/types/index.ts:2010`) as of 2026-10-27.

## 6. References

- Primary: `packages/prisma-shared-schema-backstage/prisma/schema.prisma` (`tb_dashboard_widget_template`, `tb_dashboard_bu_default_version`, enums), migrations `20261006100000_dashboard_widget_template`, `20261006130000_dashboard_widget_template_seed_key`, `20261008100000_dashboard_widget_template_title_i18n`.
- Secondary: `../carmen-backstage/src/types/index.ts` (`DashboardTemplate*`, `DashboardDeploy*`, `DashboardDatasetInfo`).
- Tenant side: `packages/prisma-shared-schema-tenant/prisma/schema.prisma` (`tb_dashboard_bu_widget_deploy`), `micro-data/migrations/tenant/131_dash_bu_widget_module.up.sql`.
- Siblings: [Dashboard Templates](/en/platform/dashboard-templates), [Lifecycle](/en/platform/dashboard-templates/lifecycle).
