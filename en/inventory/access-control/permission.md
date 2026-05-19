---
title: Permission
description: Atomic resource + action pairs — the building blocks bundled into application roles to authorise every UI and API operation.
published: true
date: 2026-05-19T23:55:00.000Z
tags: access-control, permission, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Permission

> **At a Glance**
> **Owner:** Seed-managed (release-time) &nbsp;·&nbsp; **Table:** `tb_permission` &nbsp;·&nbsp; **Used by:** [access-control/application-role](/en/inventory/access-control/application-role) (only consumer) &nbsp;·&nbsp; Atomic `(resource, action)` pairs — the smallest unit of authorisation.

## 1. What & Who

A permission is the **smallest unit of authorisation**: a `(resource, action)` pair such as `(purchase_request, approve)` or `(inventory, view)`. Permissions are catalogued centrally and **never assigned directly** to users — they are aggregated into [access-control/application-role](/en/inventory/access-control/application-role) rows via `tb_application_role_tb_permission`, and users get them transitively by being granted a role.

The runtime check "can user X perform action Y on resource Z in BU B" is a single join across `tb_user_tb_application_role`, `tb_application_role`, and `tb_application_role_tb_permission`.

**Maintained by** release migrations (seed). **Read by** the role-edit UI for bundling and by every API request for permission checks.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| View the permission catalogue | Sysadmin → Platform → Permissions (read-only) | List grouped by `resource` |
| Bundle permissions into a role | [access-control/application-role](/en/inventory/access-control/application-role) edit screen | Checkbox grid; this is the normal path |
| Add a new permission atom | Release migration / seed | `tb_permission` is seed-managed, not UI-editable |
| Rename / retire a permission | Soft-delete + re-create | Constraint includes `deleted_at` so `(resource, action)` can be re-used |
| Find which roles include a permission | Query `tb_application_role_tb_permission` by `permission_id` | Useful before retirement |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Permission not found" at runtime | Code references a permission that was deleted or never seeded | Re-seed or restore via migration |
| Duplicate `(resource, action)` insert | Existing non-deleted row | Use the existing row instead |
| Feature silently disabled for everyone | Permission deleted while code still references it | Operational guard — restore via migration |
| Confusing tooltip in role editor | Missing or terse `description` | Update seed; descriptions should explain *what the permission unlocks* |

## 4. Edge Cases

- **Closed enumeration.** The set of permissions is closed per release — new permissions ship with code that checks them.
- **No direct user link.** There is no `tb_user_tb_permission` join — all paths go through application roles.
- **Soft-delete + rename.** Constraint includes `deleted_at` so a renamed permission can be soft-deleted and `(resource, action)` re-created.
- **Description discipline.** `description` is for the role-edit tooltip — must explain *what the permission unlocks*, not just restate the pair.

---

## 5. Data Model (Dev)

Source: platform schema.

### 5.1 `tb_permission`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `resource` | `String @db.VarChar` | No | Logical resource (e.g. `purchase_request`, `inventory`, `vendor`). |
| `action` | `String @db.VarChar` | No | Verb (e.g. `view`, `create`, `update`, `delete`, `approve`, `post`). |
| `description` | `String?` | Yes | Human-readable label and rationale. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([resource, action, deleted_at])`. Back-relation to `tb_application_role_tb_permission`. Audit FKs `onDelete: NoAction`.

## 6. Business Rules

- **Uniqueness.** `(resource, action)` is unique among non-deleted permissions; constraint includes `deleted_at` to allow rename via soft-delete + re-create.
- **Closed enumeration.** New permissions ship with code that checks them; deletion is an *operational* guard (release process), not DB-enforced.
- **No direct user link.** Every authorisation path goes through `tb_application_role`. Single source of truth keeps audit trails simple.
- **Description discipline.** Required for the role-edit UI tooltip — must explain consequences, not just restate the pair.

## 7. Cross-References

- [access-control/application-role](/en/inventory/access-control/application-role) — sole consumer.
- [access-control/user](/en/inventory/access-control/user) — holds permissions transitively through roles.
- All transactional modules — every guarded UI action / protected API endpoint resolves against a `(resource, action)`.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_permission` (lines ~323-341).
- **Frontend:** Surfaced inside role-edit at `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/user-role/`. No standalone CRUD.
