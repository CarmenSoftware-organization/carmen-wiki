---
title: Menu
description: Application navigation entries — per-module menu items rendered in the app shell, with visibility, active, and lock flags.
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, menu, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Menu

> **At a Glance**
> **Owner:** Sysadmin &nbsp;·&nbsp; **Table:** `tb_menu` &nbsp;·&nbsp; **Used by:** app shell navigation &nbsp;·&nbsp; One row per addressable screen — data-driven sidebar / top-nav.

## 1. What & Who

The menu table is the **navigation registry** — one row per addressable screen grouped by `module_id`. The app shell reads this table at boot (or login) and renders the sidebar / top-nav as a tree. Each row has a target `url`, display `name`, and three boolean controls: `is_visible` (render), `is_active` (selectable), `is_lock` (system-protected, only Sysadmin can edit).

Keeping navigation data-driven lets a property disable an unused module ("hide Recipe entirely") or pin a custom landing URL without a code deploy. The row declares the entry point only — the platform's RBAC and feature-flag layer decide who actually sees it.

**Maintained by** Sysadmin. **Read by** the app shell at boot.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Hide a module's entry | Set `is_visible = false` | Removed from sidebar; route still reachable by URL |
| Disable a route | Set `is_active = false` | Renders but not clickable |
| Add a custom menu entry | System Config → Menu → New | Pick `module_id`, name, url |
| Lock a built-in entry | `is_lock = true` (system-set) | Non-Sysadmin cannot edit/delete |
| Reorder entries | Drag within `module_id` group | Currently app-side via additional metadata |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Duplicate name in module" | `(module_id, name)` exists among non-deleted | Pick different name |
| Click → 404 | `url` points at non-existent route | Update `url` to valid route |
| Locked entry edit blocked | `is_lock = true` and user lacks `menu.manage_locked` | Grant permission or unlock from Sysadmin |
| Entry visible but click does nothing | `is_active = false` | Toggle on or remove the entry |

## 4. Edge Cases

- **Effective visibility** = `is_active && is_visible && deleted_at IS NULL && user has permission for URL`. Any false hides the entry.
- **No FK from `module_id`** to a `tb_module` table — module catalogue is resolved by the application layer.
- **Lock semantics.** Soft-deleting a locked entry effectively hides the built-in route.
- **URL hygiene.** Stored verbatim; no validation — invalid URLs 404 at click.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_menu`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `module_id` | `String @db.Uuid` | No | Logical module grouping (app-side catalogue). |
| `name` | `String @db.VarChar` | No | Display label. |
| `url` | `String @db.VarChar` | No | Target route. |
| `description` | `String?` | Yes | Tooltip / description. |
| `is_visible` | `Boolean?` | Yes | Default `true`. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `is_lock` | `Boolean?` | Yes | Default `true`. System-protected. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([module_id, name, deleted_at])`. Index on `[name]`. No FK from `module_id` (resolved app-side).

## 6. Business Rules

- **Uniqueness.** `(module_id, name)` unique among non-deleted.
- **Lock semantics.** `is_lock = true` blocks hard-delete and `url` change for non-Sysadmin.
- **Visibility cascade.** All conditions must pass (active + visible + not deleted + RBAC).
- **URL hygiene.** Stored verbatim; no validation.
- **Module grouping.** `module_id` opaque to schema; ordering / icons in app metadata.
- **Audit.** Edits to locked entries should write [reporting-audit/activity](/en/inventory/reporting-audit/activity) rows.

## 7. Cross-References

- All transactional modules — each typically has one or more menu entries.
- [access-control/permission](/en/inventory/access-control/permission) — visibility intersected with per-user permissions.
- [system-config/application-config](/en/inventory/system-config/application-config) — feature flags can further hide entries.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_menu` (lines ~1375-1393).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/menu/`.
