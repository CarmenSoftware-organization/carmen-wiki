---
title: Widget
description: Dashboard composition entity — per-user / per-BU dashboards, default layouts, and personal saved workspace queries.
published: true
date: 2026-05-17T11:00:00.000Z
tags: reporting-audit, widget, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Widget

> **At a Glance**
> **Owner:** End users (personal) + BU admins (BU) + Sysadmin (defaults) &nbsp;·&nbsp; **Table:** `tb_widget_dashboard` (+ `tb_widget_default_layout`, `tb_widget_workspace`) &nbsp;·&nbsp; **Used by:** dashboard renderer + data-explorer panel &nbsp;·&nbsp; Dashboards, seed layouts, saved queries.

## 1. What & Who

The widget entity powers the **dashboards layer** — multi-table because dashboards solve three related problems: composing a personal-or-BU-scoped dashboard out of tiles, seeding new users with sensible defaults, and letting users save reusable data queries.

- `tb_widget_dashboard` — dashboard header; `scope` (`personal` or `bu`) decides visibility; items live in a sibling `tb_widget_dashboard_item` table.
- `tb_widget_default_layout` — exactly one row per scope; JSON `items` describes the seed layout for new users / new BU dashboards.
- `tb_widget_workspace` — per-user saved queries; surfaces in the data-explorer panel and may be referenced from dashboard tiles.

**Maintained by** end users (their personal dashboards + workspaces), BU admins (BU dashboards), Sysadmin (defaults). **Read by** the dashboard layer and data-explorer.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a tile to dashboard | Dashboard → Edit → Add tile | Writes a sibling `tb_widget_dashboard_item` row |
| Resize / reorder tiles | Drag handles in edit mode | `w`, `h` (grid units) + `sort_order` |
| Save a data-explorer query | Data explorer → Save as workspace | Per-user `tb_widget_workspace` row |
| Set default layout for new users | Sysadmin → Dashboard Defaults → `personal` | Edits the JSON payload |
| Create a BU dashboard | Dashboard → New, scope = `bu` | Visible to every BU member |
| Soft-delete a dashboard | Dashboard menu → Delete | Items remain; reaped by GC after retention |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| User does not see their personal dashboard | Wrong `created_by_id` | Personal dashboards filter by current user |
| BU dashboard invisible to a user | User not a member of the BU | Grant via [[access-control/business-unit-user]] |
| Workspace query rejected | Mis-shaped (not a structured filter doc) | Use the structured filter language; raw SQL not accepted |
| New user sees old defaults | Default layout was edited post-seed | New users get current defaults; existing materialised dashboards untouched |

## 4. Edge Cases

- **Default seeding** materialises into a real `tb_widget_dashboard` the first time the user edits any tile.
- **No soft-delete on default layout** — `tb_widget_default_layout` is overwritten in place; only `updated_*` audit fields.
- **No workspace sharing surface** in the current schema — workspaces are strictly per-user.
- **Accent semantics** purely cosmetic.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_widget_dashboard`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `label` | `String @db.VarChar(48)` | No | Display name. |
| `scope` | `enum_widget_dashboard_scope` | No | `personal` or `bu`. |
| `accent` | `enum_widget_accent?` | Yes | `muted`, `primary`, `success`, `warning`, `destructive`, `info`. |
| `created_*` / `updated_*` / `deleted_*` | — | Mixed | Standard audit. |

**Relations:** has-many `tb_widget_dashboard_item` (sibling). **Indexes:** `(scope, deleted_at)`, `(created_by_id, scope)`.

### 5.2 `tb_widget_default_layout`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `scope` | `enum_widget_dashboard_scope` | No | Primary key — exactly one row per scope. |
| `items` | `Json @db.JsonB` | No | Seed layout (array of item descriptors). |
| `created_at` / `updated_at` / `updated_by_id` | — | Mixed | Limited audit (no creator / no soft-delete). |

### 5.3 `tb_widget_workspace`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar(48)` | No | Display name. |
| `query` | `String @db.Text` | No | Stored query body (structured filter doc). |
| Audit columns | — | Mixed | Standard. |

**Indexes:** `(created_by_id, created_at)`, `(created_by_id, deleted_at)`.

**Enums:** `enum_widget_dashboard_scope`: `personal`, `bu`. `enum_widget_accent`: `muted`, `primary`, `success`, `warning`, `destructive`, `info`.

## 6. Business Rules

- **Scope visibility.** `personal` visible only to creator; `bu` visible to every BU member. App enforces both checks before listing.
- **Default seeding.** New user without a personal dashboard sees `tb_widget_default_layout[personal]`; materialised on first edit.
- **Soft-delete on dashboards/workspaces.** Items remain in sibling table; reaped by GC after retention.
- **No soft-delete on default layout.** Overwritten in place; exactly two rows.
- **Item ordering.** Sibling table; `sort_order` + 12-column grid.
- **Workspace query format.** Structured filter doc only; raw SQL rejected at API layer.
- **Accent is cosmetic.**

## 7. Cross-References

- [[access-control/user]] — owner of personal dashboards and workspaces.
- [[master-data/business-unit]] — bounds `bu`-scope visibility.
- [[reporting-audit/report]] — tile `config` may embed `report_template_id`.
- [[reporting-audit/activity]] — dashboard edits logged.
- All transactional modules — common data sources for tiles.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_widget_dashboard` (lines ~5727-5744), `tb_widget_workspace` (lines ~5787-5801), `tb_widget_default_layout` (lines ~5803-5809), enums (lines ~5713-5725).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/dashboard/`; data-explorer panel for workspaces.
