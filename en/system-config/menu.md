---
title: Menu
description: Application navigation entries — per-module menu items rendered in the app shell, with visibility, active, and lock flags.
published: true
date: 2026-05-16T08:00:00.000Z
tags: system-config, menu, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Menu

## 1. Purpose

The menu table is the **navigation registry** — one row per addressable screen, grouped by `module_id`. The application shell reads this table at boot (or login) and renders the sidebar / top-nav as a tree. Each row has a target `url`, a display `name`, and three boolean controls: `is_visible` (show in the rendered menu), `is_active` (selectable / clickable), and `is_lock` (system-protected — only Sysadmin can edit or remove).

Keeping navigation data-driven means a property can disable an unused module ("hide Recipe entirely") or pin a custom landing URL without a code deploy. The table is structurally simple — it does not define the page itself; it just declares the entry point and lets the platform's RBAC and feature-flag layer decide who actually sees it.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_menu`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `module_id` | `String @db.Uuid` | No | Logical module grouping (e.g. one ID for `procurement`, one for `inventory`). Resolved via application catalogue. |
| `name` | `String @db.VarChar` | No | Display label for the menu entry. |
| `url` | `String @db.VarChar` | No | Target route (typically a frontend path, e.g. `/procurement/purchase-request`). |
| `description` | `String?` | Yes | Free-text description / tooltip. |
| `is_visible` | `Boolean?` | Yes | Whether to render in the menu (default `true`). |
| `is_active` | `Boolean?` | Yes | Whether the entry is selectable (default `true`). |
| `is_lock` | `Boolean?` | Yes | System-protected entry — locked entries cannot be edited or deleted by non-Sysadmin (default `true`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([module_id, name, deleted_at])` map `menu_module_id_name_u`. Index on `[name]`.

Note: there is no in-schema FK from `module_id` to a `tb_module` table — the module catalogue is resolved by the application layer.

## 3. Usage / Cross-References

- App shell — the navigation component reads the menu at boot, intersects with the user's RBAC permissions ([[access-control/permission]]) and feature flags ([[system-config/application-config]]), and renders the resulting tree.
- All transactional modules — every module ([[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[vendor-pricelist]], [[product]], [[recipe]], [[costing]]) typically has one or more menu entries pointing at its list / detail routes.
- [[access-control/permission]] — menu visibility is intersected with the per-user permission set; an entry with no matching permission is hidden regardless of `is_visible`.

## 4. Configuration UI

Managed by **Sysadmin** under System Configuration → Menu. The screen shows the menu tree grouped by `module_id` with inline toggles for `is_visible` and `is_active`. Adding a new entry requires picking a `module_id` and entering name + url; `is_lock` is set by the system when a menu entry maps to a built-in route. Editing a locked entry is gated behind a confirmation dialog.

## 5. Business Rules

- **Uniqueness.** `(module_id, name)` is unique among non-deleted rows.
- **Lock semantics.** `is_lock = true` entries cannot be hard-deleted or have their `url` changed except by a Sysadmin with the `menu.manage_locked` permission. Soft-deleting a locked entry effectively hides the built-in route.
- **Visibility cascade.** Effective visibility at render time = `is_active && is_visible && deleted_at IS NULL && user has permission for the URL`. Failing any condition hides the entry.
- **URL hygiene.** `url` should be a relative frontend path. The application performs no validation on the URL beyond storing it verbatim; pointing at a non-existent route produces a 404 at click time.
- **Module grouping.** `module_id` is opaque to the schema. Reordering within a group, custom icons, and grouping labels are application-side concerns (typically driven by additional columns in `info` on a future migration, or a sibling catalogue table).
- **Audit.** Edits to locked entries should be logged via [[reporting-audit/activity]] for compliance.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_menu` (lines ~1375-1393).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/menu/`.
- **Cross-module:** see Section 3.
