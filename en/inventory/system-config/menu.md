---
title: Menu
description: A tb_menu table exists in the tenant schema with zero non-schema code references anywhere in the backend or frontend — the app shell's real sidebar is a static, code-defined navigation tree, not data-driven from this table.
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, menu, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Menu

> **At a Glance**
> **Owner:** Nobody — **the table is never read or written by any code found** &nbsp;·&nbsp; **Table:** `tb_menu` (schema-only) &nbsp;·&nbsp; **Real navigation:** a static, code-defined tree (e.g. `landing-types.ts`'s `CHAPTERS` for the System Admin hub, and an equivalent structure for the main app sidebar) &nbsp;·&nbsp; Dead table — kept in the schema, not wired to anything.

## Implementation status (verified 2026-07-16)

A repo-wide search for `tb_menu` across `carmen-turborepo-backend-v2/apps` and `carmen-turborepo-backend-v2/packages` returns **only the Prisma schema declaration and its migration SQL** — zero hits in any `.service.ts`, `.controller.ts`, or DTO file. There is no `menu.service.ts`, no `menu.controller.ts`, no Bruno `config/menu/*` folder, and no `menu` route anywhere under `../carmen-inventory-frontend-react/routes/`.

The app shell's actual navigation is **hard-coded in the frontend**, not data-driven: the System Admin landing page renders from a compile-time `CHAPTERS` array (`routes/system-admin/landing-types.ts`) mapping module keys straight to `href` strings (e.g. `{ key: "period", href: "/system-admin/period" }`); the main app sidebar follows the same static-config pattern. Disabling a module for one property, or changing navigation visibility, requires a **frontend code change and redeploy** — there is no admin screen, and no runtime row, that controls it today.

Everything below this line describes the **design intent** implied by the schema's field shape (`is_visible` / `is_active` / `is_lock` / `module_id`), preserved because the table may be built out later — not verified, shipped behavior.

## 1. What & Who

`tb_menu` was evidently designed as a **navigation registry** — one row per addressable screen grouped by `module_id`, with a target `url`, display `name`, and three boolean controls (`is_visible`, `is_active`, `is_lock`). No code was found that reads this table at boot, at login, or anywhere else — the app shell does not consult it.

**Maintained by** nobody — no admin surface exists. **Read by** nothing found.

## 2. Common Tasks

No task below is possible today — kept as design intent only.

| Task (design intent, unbuilt) | Where (does not exist) | Notes |
|---|---|---|
| Hide a module's entry | ~~Set `is_visible = false`~~ | No screen writes this table; navigation is a frontend code constant |
| Disable a route | ~~Set `is_active = false`~~ | Not implemented |
| Add a custom menu entry | ~~System Config → Menu → New~~ | No such screen exists |
| Lock a built-in entry | ~~`is_lock = true`~~ | Not implemented |
| Reorder entries | ~~Drag within `module_id` group~~ | Not implemented — order is fixed in the frontend `CHAPTERS`/sidebar array |

## 3. Validation & Errors

Unconfirmed — no service layer exists to enforce any of these.

| Symptom (hypothetical) | Cause | Action |
|---|---|---|
| "Duplicate name in module" | `(module_id, name)` exists among non-deleted | Not implemented — no create endpoint |
| Click → 404 | `url` points at non-existent route | Not applicable — navigation is a static, tested code constant, not user-editable data |
| Locked entry edit blocked | `is_lock = true` | Not implemented |
| Entry visible but click does nothing | `is_active = false` | Not implemented |

## 4. Edge Cases

- **No effective-visibility formula exists in code.** The `is_active && is_visible && deleted_at IS NULL` combination described here is inferred from column names, not from any observed guard.
- **No FK from `module_id`** to a `tb_module` table in the schema — consistent with a design that was never finished, not evidence either way about implementation.
- **To actually hide a module today**, a Sysadmin has no lever at all — the change has to go through the frontend codebase (e.g. editing `landing-types.ts`'s `CHAPTERS` or the main sidebar config) and a deploy.

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

None of the following is enforced by any code found — the unique index is the only thing the database actually enforces; everything else is inferred from column names.

- **Uniqueness (schema-level only).** `(module_id, name)` unique among non-deleted — a DB constraint, not backed by any service.
- **Lock semantics, visibility cascade, URL hygiene, module grouping, audit-on-edit** — all design intent; **no code implements any of them.**

## 7. Cross-References

No module was found to read `tb_menu`. Cross-links removed — there is nothing to cross-reference until the table is wired to something. See [system-config/application-config](/en/inventory/system-config/application-config) for the (also largely unimplemented) feature-flag concept.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_menu` (lines ~1412-1430).
- **Frontend (the real, static navigation, for comparison):** `../carmen-inventory-frontend-react/routes/system-admin/landing-types.ts` (`CHAPTERS` — the System Admin hub's module list) and `../carmen-inventory-frontend-react/routes/router.tsx` (the full static route tree). Neither reads `tb_menu`.
