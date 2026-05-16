---
title: Permission
description: Atomic resource + action pairs — the building blocks bundled into application roles to authorise every UI and API operation.
published: true
date: 2026-05-16T08:00:00.000Z
tags: access-control, permission, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Permission

## 1. Purpose

A permission is the **smallest unit of authorisation** in the platform: a `(resource, action)` pair such as `(purchase_request, approve)` or `(inventory, view)`. Permissions are catalogued centrally and never assigned directly to a user — they are aggregated into [[access-control/application-role]] rows via `tb_application_role_tb_permission`, and users get permissions transitively by being granted a role. This keeps the authorisation model uniform: the runtime answer to "can user X perform action Y on resource Z in BU B" is a single join across `tb_user_tb_application_role`, `tb_application_role`, and `tb_application_role_tb_permission`.

Because permissions are essentially a closed enumeration, the table is small and rarely changes — new permissions are added when new modules or actions ship, and existing ones are kept for backward compatibility.

## 2. Prisma Model(s)

Source: platform schema.

### 2.1 `tb_permission`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `resource` | `String @db.VarChar` | No | The logical resource (e.g. `purchase_request`, `inventory`, `vendor`). |
| `action` | `String @db.VarChar` | No | The verb (e.g. `view`, `create`, `update`, `delete`, `approve`, `post`). |
| `description` | `String?` | Yes | Human-readable label and rationale. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([resource, action, deleted_at])` map `permission_resource_action_deleted_at_u`. Back-relations to `tb_application_role_tb_permission` and audit FKs to `tb_user` (`onDelete: NoAction`).

## 3. Usage / Cross-References

- **All transactional modules** — every guarded UI action and protected API endpoint is gated by a check against `(resource, action)`. The convention is `<module-slug>.<verb>`.
- [[access-control/application-role]] — the only consumer of `tb_permission` rows (via `tb_application_role_tb_permission`).
- [[access-control/user]] — users hold permissions transitively through roles, not directly.

## 4. Configuration UI

`tb_permission` is **seed-managed**, not user-editable through a normal admin screen. Sysadmin can view the full catalogue (typically under a platform / admin screen) to verify which atoms exist when configuring roles; adding or renaming an atom is a release-time migration. The role-edit screen on [[access-control/application-role]] is where these atoms get bundled into roles in normal operation.

## 5. Business Rules

- **Uniqueness.** `(resource, action)` is unique among non-deleted permissions. The unique constraint includes `deleted_at` so a renamed permission can be soft-deleted and the same `(resource, action)` can be re-created.
- **Closed enumeration.** The set of permissions is closed for any given release — new permissions ship with code that checks them. Deleting a permission used by code at runtime would silently disable that feature for everyone; the deletion guard is *operational* (release process) rather than DB-enforced.
- **No direct user link.** There is no `tb_user_tb_permission` join — all paths go through `tb_application_role`. This is the single source of truth for "what does a permission grant" and keeps audit trails simple.
- **Description discipline.** `description` is intended for the role-edit UI tooltip and must explain *what the permission unlocks*, not just restate the resource and action.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_permission` (lines ~323-341).
- **Frontend route (if known):** Permissions are surfaced inside the role-edit screen at `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/user-role/`; there is no standalone CRUD page.
- **Cross-module:** see Section 3.
