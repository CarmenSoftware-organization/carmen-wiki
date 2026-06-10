---
title: Platform RBAC — Data Model
description: The five RBAC tables — permission catalog, roles, role-permission join, scoped user assignments, super-admin flag — and divergences from the SPA shapes.
published: true
date: 2026-06-10T12:00:00.000Z
tags: book/platform, rbac, data-model
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Platform RBAC — Data Model

> **At a Glance**
> **Tables:** `tb_platform_permission` &nbsp;·&nbsp; `tb_platform_role` &nbsp;·&nbsp; `tb_platform_role_tb_permission` &nbsp;·&nbsp; `tb_user_tb_platform_role` &nbsp;·&nbsp; `tb_platform_super_admin` &nbsp;·&nbsp; **Enums:** none — `resource`/`action` are free-form VarChar &nbsp;·&nbsp; **Scope:** nullable `cluster_id` on the assignment row (`null` = platform-wide) &nbsp;·&nbsp; **Audit columns:** standard `created_*`/`updated_*`/`deleted_*` trio on every table &nbsp;·&nbsp; **Soft-delete uniques:** every uniqueness constraint includes `deleted_at`, so deleted rows can be re-created

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The RBAC module owns five tables, grouped under the `// Platform RBAC` and `// Platform Super Admin` banners in the Prisma schema (lines 919–1013). `tb_platform_permission` is the catalog: one row per `resource` + `action` pair, written only by the backend (seed/migration) — the SPA reads it but exposes no create/edit surface. `tb_platform_role` holds the named bundles, and `tb_platform_role_tb_permission` is the M:N join that records which catalog rows a role grants.

`tb_user_tb_platform_role` binds a role to a user with a scope: its nullable `cluster_id` column is the entire scope mechanism — `null` means the assignment applies platform-wide, a UUID means it applies inside that cluster only. `tb_platform_super_admin` is deliberately not part of the role graph: it is a flag table (just `user_id` + `is_active` beyond the audit trio) whose rows mark users that bypass every permission check.

All five tables carry the platform-standard audit trio (`created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id`) and use soft-delete-aware unique constraints (`deleted_at` participates in every `@@unique`), so a deleted role name, catalog key, assignment, or super-admin flag can be re-created without a unique-key collision.

## 2. Entities

### 2.1 `tb_platform_permission`

The permission catalog. One row per grantable action; the SPA derives the key string as `resource.action` (e.g. `role.read`). Rows are backend-owned reference data.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `resource` | `String @db.VarChar` | No | Resource segment of the key (e.g. `role`, `cluster`, `user_platform`) |
| `action` | `String @db.VarChar` | No | Action segment of the key (e.g. `read`, `create`, `manage`, `send`) |
| `description` | `String?` | Yes | Human-readable explanation shown in the Permission Catalog screen and PermissionPicker tooltips |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- `@@unique([resource, action, deleted_at])` — map `"platform_permission_resource_action_deleted_at_u"` — one live row per key; a soft-deleted key can be re-introduced

**Indexes:** none beyond the unique map.

### 2.2 `tb_platform_role`

A named, activatable bundle of permissions. The role's key set lives entirely in the join table (§2.3); this row holds only identity and status.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `name` | `String @db.VarChar` | No | Role name; unique among live rows |
| `description` | `String?` | Yes | Optional description shown in the Roles list |
| `is_active` | `Boolean?` | Yes | Default `true`; Active/Inactive badge in the SPA |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- `@@unique([name, deleted_at])` — map `"platform_role_name_deleted_at_u"` — allows name re-use after soft delete

**Indexes:** none beyond the unique map.

### 2.3 `tb_platform_role_tb_permission`

M:N join between roles and catalog rows. Each row grants one permission to one role. The SPA's delta writes (`permissions: { add, remove }`) translate to inserting and soft-deleting rows here.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `platform_role_id` | `String @db.Uuid` | No | FK to `tb_platform_role.id` |
| `platform_permission_id` | `String @db.Uuid` | No | FK to `tb_platform_permission.id` |
| `is_active` | `Boolean?` | Yes | Default `true`; grant active flag |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- FK: `platform_role_id` → `tb_platform_role.id` (`onDelete: NoAction, onUpdate: NoAction`)
- FK: `platform_permission_id` → `tb_platform_permission.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([platform_role_id, platform_permission_id, deleted_at])` — map `"platform_role_permission_deleted_at_u"` — a removed grant can be re-added

**Indexes:**
- `@@index([platform_permission_id, deleted_at])` — map `"platform_role_permission_permission_deleted_at_idx"` — supports "which roles grant key X" lookups

### 2.4 `tb_user_tb_platform_role`

The assignment table: binds a user to a role at a scope. This is the row the User Platform detail screen creates and deletes, and the input to the effective-permissions flattening.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()`; the `assignmentId` used by the delete endpoint |
| `user_id` | `String @db.Uuid` | No | Target user id — plain column, **no Prisma `@relation` to `tb_user`** |
| `platform_role_id` | `String @db.Uuid` | No | FK to `tb_platform_role.id` |
| `cluster_id` | `String? @db.Uuid` | Yes | Scope: `null` = platform-wide; set = scoped to this cluster (schema comment verbatim). Plain column, no `@relation` to `tb_cluster` |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- FK: `platform_role_id` → `tb_platform_role.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([user_id, platform_role_id, cluster_id, deleted_at])` — map `"user_platform_role_deleted_at_u"` — the same role may be assigned to the same user once per distinct scope

**Indexes:**
- `@@index([user_id, deleted_at])` — map `"user_platform_role_user_deleted_at_idx"` — drives "roles of user X" (the list endpoint and effective-permissions flattening)
- `@@index([cluster_id, deleted_at])` — map `"user_platform_role_cluster_deleted_at_idx"` — drives "assignments scoped to cluster Y"

### 2.5 `tb_platform_super_admin`

The bypass flag. A live row here makes `is_super_admin: true` appear in the user's effective-permissions payload, short-circuiting every check. It carries no role or permission references — membership is the entire semantic.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()`; the id used by the remove endpoint |
| `user_id` | `String @db.Uuid` | No | Flagged user id — plain column, no `@relation` to `tb_user` |
| `is_active` | `Boolean?` | Yes | Default `true`; the SPA renders Inactive rows but they exist in data |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` — shown as "Added" in the SPA |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- `@@unique([user_id, deleted_at])` — map `"platform_super_admin_user_deleted_at_u"` — one live flag per user; removable and re-grantable

**Indexes:** none beyond the unique map.

## 3. Relationships

```
tb_platform_role  1 ─── M  tb_platform_role_tb_permission  M ─── 1  tb_platform_permission
tb_platform_role  1 ─── M  tb_user_tb_platform_role
tb_user_tb_platform_role.user_id     ──>  tb_user.id     (application-level, no Prisma FK)
tb_user_tb_platform_role.cluster_id  ──>  tb_cluster.id  (application-level, no Prisma FK; null = platform scope)
tb_platform_super_admin.user_id      ──>  tb_user.id     (application-level, no Prisma FK)
```

Declared FK relations (both `onDelete: NoAction, onUpdate: NoAction`):

- `tb_platform_role_tb_permission.platform_role_id` → `tb_platform_role.id`
- `tb_platform_role_tb_permission.platform_permission_id` → `tb_platform_permission.id`
- `tb_user_tb_platform_role.platform_role_id` → `tb_platform_role.id`

Note the asymmetry: only the role-side links are real Prisma relations. `user_id` (on both the assignment and super-admin tables) and `cluster_id` (on the assignment table) are plain UUID columns with **no `@relation` directive and no database FK** — referential integrity to `tb_user` and `tb_cluster` is enforced at the application layer. Deleting a user or cluster does not cascade into these tables; orphaned assignment rows are possible at the schema level and testers should not assume the database prevents them.

## 4. Enums

This module defines **no enums**. The two places where an enum might be expected are deliberately not enums:

- **Permission keys** — `resource` and `action` are free-form `VarChar` columns. The key vocabulary is open-ended data, extended by backend seeds/migrations without a schema change.
- **Scope** — modelled as the nullable `cluster_id` column on `tb_user_tb_platform_role`, not a scope-type enum. The SPA's `Scope` union type (§5) is a client-side construction over that column.

The legacy 7-value role enum that previously lived on the user row has been removed from the schema entirely — see the migration section of the [module landing](/en/platform/rbac).

## 5. Divergences from carmen-platform SPA shape

The SPA types live in `../carmen-platform/src/types/index.ts` (`Role`, `PermissionCatalogItem`, `UserRoleAssignment`, `Scope`, `EffectivePermissions`). The API flattens the Prisma graph considerably:

| SPA shape | SPA source | Prisma storage | Notes |
| --------- | ---------- | -------------- | ----- |
| `Role.permissions: string[]` (key strings) | `Role` | `tb_platform_role_tb_permission` join rows | The API flattens join rows into derived `resource.action` strings; the SPA never sees join-row ids. Writes go back as deltas `{ add, remove }` (`roleService.RoleWriteData`), not as the full set |
| `permission_count` on list rows | `RoleRow` in `RoleManagement.tsx` | not a column | Server-side aggregate over live join rows; exists only in the list response |
| `PermissionCatalogItem.key` | `permissionService.getCatalog` | not a column | Derived; the service synthesizes `` `${resource}.${action}` `` when the response lacks `key` |
| `Scope` union `{ type: 'platform' } \| { type: 'cluster', cluster_id }` | `Scope` | single nullable `cluster_id` column | The discriminated union is an API/client construction; `type: 'platform'` ⇔ `cluster_id IS NULL` |
| `UserRoleAssignment.role_name` | `UserRoleAssignment` | not a column | Joined in from `tb_platform_role.name` by the API for display |
| `EffectivePermissions` `{ platform, clusters, is_super_admin }` | `EffectivePermissions` | no table | Computed flattening of all live assignments + the super-admin flag; served by `GET /api/user/permission/platform` |
| Flat `created_at`/`created_by_name` on role list rows | `RoleManagement.tsx` | audit id columns | The list response may nest audit data as `audit.created/updated` `{ at, name }`; the SPA flattens and tolerates both shapes |
| Multi-layer `{ data }` envelopes | `userRoleService.list`, `SuperAdminManagement.extractArray` | n/a | The user-roles and super-admins endpoints may nest `{ data: { data: [...] } }` deeper than the usual one level; both consumers descend until they hit an array |

### 5.1 Endpoints

REST surface consumed by the SPA services (`roleService.ts`, `permissionService.ts`, `superAdminService.ts`, `userRoleService.ts`):

| Method + Path | Purpose | Notes |
|---|---|---|
| `GET /api-system/platform/roles` | Roles list | Paginated; rows carry `permission_count` and possibly nested `audit` |
| `POST /api-system/platform/roles` | Create role | Body includes `permissions: { add: string[] }` |
| `GET /api-system/platform/roles/:id` | Role detail | Returns flattened `permissions: string[]` |
| `PUT /api-system/platform/roles/:id` | Update role | Body includes `permissions: { add: string[], remove: string[] }` (delta) |
| `DELETE /api-system/platform/roles/:id` | Delete role | |
| `GET /api-system/platform/permissions` | Permission catalog | Read-only; no write endpoints exist in the SPA |
| `GET /api-system/platform/super-admins` | Super-admin list | Response may nest multi-layer `{ data }` envelopes |
| `POST /api-system/platform/super-admins` | Grant flag | Body `{ user_id }` |
| `DELETE /api-system/platform/super-admins/:id` | Revoke flag | `:id` is the flag-row id, not the user id |
| `GET /api-system/platform/users/:userId/roles` | List assignments | Response may nest multi-layer `{ data }` envelopes |
| `POST /api-system/platform/users/:userId/roles` | Add assignment | Body `{ role_id, scope }` with the `Scope` union shape |
| `DELETE /api-system/platform/users/:userId/roles/:assignmentId` | Remove assignment | `:assignmentId` is the `tb_user_tb_platform_role.id` |
| `GET /api/user/permission/platform` | Effective permissions of the current session | Called post-login and on every `AuthProvider` mount |

## 6. References

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — models `tb_platform_permission` (line 921), `tb_platform_role` (line 939), `tb_platform_role_tb_permission` (line 958), `tb_user_tb_platform_role` (line 978), `tb_platform_super_admin` (line 1000).

**Secondary (consumer shape):**
- `../carmen-platform/src/types/index.ts` — `Role`, `PermissionCatalogItem`, `UserRoleAssignment`, `Scope`, `EffectivePermissions`.
- `../carmen-platform/src/services/roleService.ts` — `RoleWriteData` delta shape, roles endpoints.
- `../carmen-platform/src/services/permissionService.ts` — catalog mapping (key derivation), effective-permissions fetch.
- `../carmen-platform/src/services/superAdminService.ts` and `src/pages/SuperAdminManagement.tsx` — super-admin endpoints and the envelope-descending `extractArray`.
- `../carmen-platform/src/services/userRoleService.ts` — assignment endpoints and envelope descent.

**Cross-links:** [Platform RBAC landing](/en/platform/rbac) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [users data-model](../users/data-model.md) (the `tb_user` rows assignments point at)
