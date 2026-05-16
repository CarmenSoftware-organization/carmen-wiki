---
title: Application Role
description: Per-business-unit role definitions plus the join tables that map roles to permissions and users to roles — the heart of tenant RBAC.
published: true
date: 2026-05-16T08:00:00.000Z
tags: access-control, application-role, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Application Role

## 1. Purpose

Application roles are the **named bundles of [[access-control/permission]]s** that get assigned to users inside a [[master-data/business-unit]]. Where `platform_role` on `tb_user` is a coarse global switch, application roles are the fine-grained, tenant-side authorisation layer that controls *what each user can do in each BU*. Every transactional UI action — submitting a PR, approving a GRN, posting an inventory adjustment — is gated by checking whether the active user holds an application role that includes the matching permission atom for the active BU.

The entity is implemented as three platform tables: `tb_application_role` is the named role (one row per (BU, role-name) pair); `tb_application_role_tb_permission` is the role-to-permission fan-out; and `tb_user_tb_application_role` is the user-to-role fan-out. The two join tables let the same user hold multiple roles, the same role include many permissions, and the same permission appear in many roles. Soft-delete on all three preserves history.

## 2. Prisma Model(s)

Source: platform schema.

### 2.1 `tb_application_role`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `business_unit_id` | `String @db.Uuid` | No | FK to `tb_business_unit` — roles are BU-scoped. |
| `name` | `String @db.VarChar` | No | Role name (e.g. `Procurement Manager`, `Storekeeper`). |
| `description` | `String?` | Yes | Free text. |
| `is_active` | `Boolean? @db.Boolean` | Yes | Default `true`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([business_unit_id, name, deleted_at])` map `applicationrole_business_unit_name_deleted_at_u`. Index on `(business_unit_id, name, deleted_at)` map `applicationrole_business_unit_name_deleted_at_idx`. FK to `tb_business_unit` `onDelete: NoAction`, audit FKs to `tb_user` `onDelete: NoAction`.

### 2.2 `tb_application_role_tb_permission`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `application_role_id` | `String @db.Uuid` | No | FK to `tb_application_role`. |
| `permission_id` | `String @db.Uuid` | No | FK to `tb_permission`. |
| `is_active` | `Boolean? @db.Boolean` | Yes | Default `true`. Lets a permission be temporarily disabled without unlinking. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([application_role_id, permission_id, deleted_at])` map `applicationrole_permission_role_permission_deleted_at_u`. FKs to `tb_application_role` and `tb_permission` `onDelete: NoAction`.

### 2.3 `tb_user_tb_application_role`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | FK to `tb_user`. |
| `application_role_id` | `String @db.Uuid` | No | FK to `tb_application_role`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, application_role_id, deleted_at])` map `user_applicationrole_user_application_role_deleted_at_u`. FKs to `tb_user` and `tb_application_role` `onDelete: NoAction`. Because `business_unit_id` lives on `tb_application_role`, the (user, BU) → role[] traversal is `tb_user_tb_application_role` ⨝ `tb_application_role`.

## 3. Usage / Cross-References

- **All transactional modules** — every authorisation check resolves to `(user, BU, permission)`, which is satisfied by `tb_user_tb_application_role` ⨝ `tb_application_role` ⨝ `tb_application_role_tb_permission`.
- [[access-control/permission]] — atoms that roles aggregate.
- [[access-control/user]] — accounts that roles get assigned to.
- [[master-data/business-unit]] — every role is owned by a BU; copying / templating roles across BUs is an explicit admin action.
- [[access-control/business-unit-user]] — granting a user BU access (`tb_user_tb_business_unit`) is a prerequisite for assigning them any role in that BU.

## 4. Configuration UI

Managed by **Sysadmin** within each business unit. The role-management screen lists roles for the active BU, opens to a two-pane edit: the left pane is role metadata (name, description, active flag); the right pane is the permission grid (checkboxes over `tb_permission` grouped by `resource`). A separate users tab on each role lists assigned users with the option to add / remove. Security Officer audits role changes through the activity log.

## 5. Business Rules

- **Uniqueness.** `(business_unit_id, name)` is unique among non-deleted roles. A user holds each role at most once per BU.
- **BU scoping.** A role can only be assigned to a user who already has access to the role's BU (i.e. an active `tb_user_tb_business_unit` row for the same BU exists). The application enforces this — there is no DB-level cross-table constraint.
- **Deletion guards.** Hard-delete is blocked if any active assignment exists. Soft-delete is allowed; assignments persist but the role no longer grants permissions because the join query filters by `deleted_at IS NULL`.
- **Inactivation cascade.** Setting `tb_application_role.is_active = false` immediately revokes all permissions granted through it on next permission re-evaluation. Existing sessions may continue using cached permissions until refresh.
- **Permission link toggling.** `tb_application_role_tb_permission.is_active = false` removes that permission from the role without deleting the link — useful for staged rollouts.
- **Role assignment lifecycle.** Removing a user from a role does not retro-edit historical documents the user authored; audit columns continue to reference the user record.
- **Snapshot vs live.** Permission checks are evaluated *live* against the current join state — there is no snapshot semantics here; this is fundamentally different from master data.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application_role` (lines ~30-52), `tb_application_role_tb_permission` (lines ~54-72), `tb_user_tb_application_role` (lines ~491-509).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/user-role/` and platform admin role-template screens.
- **carmen/docs (if applicable):** `../carmen/docs/workflow-permissions-system.md` — describes how *workflow* stage roles complement application roles for document-flow gating.
- **Cross-module:** see Section 3.
