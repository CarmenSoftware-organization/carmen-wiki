---
title: Widget
description: Dashboard composition entity — per-user / per-BU dashboards, default layouts, and personal saved workspace queries.
published: true
date: 2026-05-16T08:00:00.000Z
tags: reporting-audit, widget, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Widget

## 1. Purpose

The widget entity powers the **dashboards layer** of the application. It is multi-table by design because dashboards solve three related-but-distinct problems: composing a personal-or-BU-scoped dashboard out of widget tiles (`tb_widget_dashboard` + items), seeding new users with sensible defaults (`tb_widget_default_layout`), and letting users save reusable ad-hoc data queries that surface across the app (`tb_widget_workspace`).

`tb_widget_dashboard` is the dashboard header — a `scope` enum (`personal` or `bu`) decides whether the dashboard is visible only to its creator or to everyone in the active business unit. Items (in a sibling `tb_widget_dashboard_item` table referenced via Prisma relation) describe each tile's type, dimensions (`w`, `h`), order, and free-form `config` JSON.

`tb_widget_default_layout` holds one row per `scope` — the JSON `items` payload describes the seed layout for users who do not yet have a personal dashboard, and for BUs that do not yet have a BU dashboard. Editing the row immediately changes the layout new users / BUs are seeded with.

`tb_widget_workspace` is the **saved-query** surface — a name + raw query string per user. Workspace rows appear in the data-explorer panel and may be referenced from dashboard tiles via their `config` JSON. The query language is application-defined (typically a structured filter spec, not raw SQL).

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_widget_dashboard`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `label` | `String @db.VarChar(48)` | No | Dashboard display name. |
| `scope` | `enum_widget_dashboard_scope` | No | Either `personal` or `bu`. |
| `accent` | `enum_widget_accent?` | Yes | Optional accent colour: `muted`, `primary`, `success`, `warning`, `destructive`, `info`. |
| `created_at` | `DateTime @db.Timestamptz(6)` | No | Default `now()`. |
| `created_by_id` | `String @db.Uuid` | No | Owner — used for visibility on `scope = personal`. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | No | `@updatedAt`. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last editor. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor. |

**Relations:** `items` — has-many to `tb_widget_dashboard_item` (sibling table; documented under the relation here for context but out of scope of the 3-table umbrella inventory).

**Constraints:** `@@index([scope, deleted_at])` for the "all live dashboards by scope" list. `@@index([created_by_id, scope])` for "my personal dashboards" lookup.

### 2.2 `tb_widget_default_layout`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `scope` | `enum_widget_dashboard_scope` | No | Primary key — exactly one row per scope (`personal`, `bu`). |
| `items` | `Json @db.JsonB` | No | The seed layout payload — an array of item descriptors (type, position, size, config). |
| `created_at` | `DateTime @db.Timestamptz(6)` | No | Default `now()`. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | No | `@updatedAt`. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last editor. |

**Constraints:** `scope` is the primary key — exactly two possible rows. No audit columns beyond `updated_*` (the row never has a meaningful "creator" — it is part of the tenant bootstrap).

### 2.3 `tb_widget_workspace`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar(48)` | No | Display name for the saved workspace. |
| `query` | `String @db.Text` | No | Stored query body. Format is application-defined (typically a structured filter document). |
| `created_at` | `DateTime @db.Timestamptz(6)` | No | Default `now()`. |
| `created_by_id` | `String @db.Uuid` | No | Owner. |
| `updated_at` | `DateTime @db.Timestamptz(6)` | No | `@updatedAt`. |
| `updated_by_id` | `String? @db.Uuid` | Yes | Last editor. |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp. |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Soft-delete actor. |

**Constraints:** `@@index([created_by_id, created_at])` and `@@index([created_by_id, deleted_at])` for "my workspaces" lookups.

**`enum_widget_dashboard_scope` values:** `personal`, `bu`.
**`enum_widget_accent` values:** `muted`, `primary`, `success`, `warning`, `destructive`, `info`.

## 3. Usage / Cross-References

- **Dashboards** — the app shell renders the dashboard layer from `tb_widget_dashboard` plus its items, scoped by the active BU and the current user.
- [[access-control/user]] — `created_by_id` on a `personal` dashboard and on every workspace decides visibility.
- [[master-data/business-unit]] — the active BU bounds which `bu`-scope dashboards are listed.
- [[reporting-audit/report]] — widget tile `config` may embed a `report_template_id`; the widget executes the template through the same pipeline as on-demand reports and renders the result inline.
- [[inventory]], [[costing]], [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]], [[product]], [[recipe]] — common data sources for widget tiles (KPI cards, charts, recent-activity feeds).
- [[reporting-audit/activity]] — dashboard create / edit actions are logged.

## 4. Configuration UI

- **Personal dashboards** — every user manages their own through the Dashboard screen (add tile, drag-to-reorder, resize, edit config). The row's `created_by_id = active user` and `scope = personal`.
- **BU dashboards** — managed by a BU admin (a user whose [[access-control/business-unit-user]] role grants dashboard-edit). The row's `scope = bu` and visibility extends to every member of the BU.
- **Default layouts** — managed by **Sysadmin** under System Configuration → Dashboard Defaults. There are exactly two rows (one per `scope`); editing the JSON payload immediately changes the seed layout for new users / new BU dashboards.
- **Workspaces** — managed by each user from the data-explorer panel ("Save as workspace"). Workspaces are per-user; no sharing surface is exposed in the current schema.

## 5. Business Rules

- **Scope visibility.** `scope = personal` dashboards are visible only when `created_by_id = active user`. `scope = bu` dashboards are visible to every member of the BU bound to the current session. Application code enforces both checks before listing.
- **Default seeding.** A new user without a personal dashboard sees the `tb_widget_default_layout` row for `personal`; the layout is materialised into a real `tb_widget_dashboard` + items the first time the user edits any tile. The same applies to a new BU and the `bu` default.
- **Soft-delete on dashboards and workspaces.** `deleted_at` hides the row; items remain in the sibling table referenced by the deleted dashboard. A garbage-collection job reaps items belonging to dashboards soft-deleted for longer than the retention window.
- **No soft-delete on default layout.** `tb_widget_default_layout` is overwritten in place — it has only `updated_*` audit fields, not `deleted_*`. There are exactly two rows; editing them is non-destructive.
- **Item ordering and sizing.** Items are stored in the sibling `tb_widget_dashboard_item` table; ordering is driven by `sort_order`. The widget renderer treats `w` and `h` as grid units (typically a 12-column grid).
- **Workspace query format.** `query` is opaque to the schema. The application contract is a structured filter document; raw SQL is not accepted. Mis-shaped queries are rejected at the API layer, not at the database.
- **Accent semantics.** `accent` is purely cosmetic; it tints the dashboard header strip and has no behavioural effect.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_widget_dashboard` (lines ~5727-5744), `tb_widget_workspace` (lines ~5787-5801), `tb_widget_default_layout` (lines ~5803-5809), `enum_widget_dashboard_scope` (lines ~5713-5716), `enum_widget_accent` (lines ~5718-5725).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/dashboard/` for the dashboard renderer; data-explorer panel hosts the workspace save / load UI. Sysadmin defaults under System Configuration.
- **Cross-module:** see Section 3.
