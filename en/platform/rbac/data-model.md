---
title: Platform RBAC — Data Model
description: The five RBAC tables — permission catalog, roles, role-permission join, scoped user assignments, super-admin flag — their 2026-07-16 doc_version rollout, and divergences from the SPA shapes.
published: true
date: 2026-10-27T00:00:00.000Z
tags: book/platform, rbac, data-model
editor: markdown
dateCreated: 2026-06-10T12:00:00.000Z
---

# Platform RBAC — Data Model

> **At a Glance**
> **Tables:** `tb_backstage_permission` &nbsp;·&nbsp; `tb_backstage_role` &nbsp;·&nbsp; `tb_backstage_role_tb_permission` &nbsp;·&nbsp; `tb_user_tb_backstage_role` &nbsp;·&nbsp; `tb_backstage_super_admin` &nbsp;·&nbsp; **Enums:** none — `resource`/`action` are free-form VarChar &nbsp;·&nbsp; **Scope:** nullable `cluster_id` on the assignment row (`null` = platform-wide) &nbsp;·&nbsp; **Audit columns:** standard `created_*`/`updated_*`/`deleted_*` trio on every table, plus `doc_version Int @default(0)` on all five (added 2026-07-16, platform-wide optimistic-lock rollout) &nbsp;·&nbsp; **Soft-delete uniques:** every uniqueness constraint includes `deleted_at`, so deleted rows can be re-created

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The RBAC module owns five tables, grouped under the `// Platform RBAC` and `// Platform Super Admin` banners in the Prisma schema (lines 933–1032). `tb_backstage_permission` is the catalog: one row per `resource` + `action` pair, written only by the backend (seed/migration) — the SPA reads it but exposes no create/edit surface. `tb_backstage_role` holds the named bundles, and `tb_backstage_role_tb_permission` is the M:N join that records which catalog rows a role grants.

`tb_user_tb_backstage_role` binds a role to a user with a scope: its nullable `cluster_id` column is the entire scope mechanism — `null` means the assignment applies platform-wide, a UUID means it applies inside that cluster only. `tb_backstage_super_admin` is deliberately not part of the role graph: it is a flag table (just `user_id` + `is_active` beyond the audit trio) whose rows mark users that bypass every permission check.

All five tables carry the platform-standard audit trio (`created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id`) and use soft-delete-aware unique constraints (`deleted_at` participates in every `@@unique`), so a deleted role name, catalog key, assignment, or super-admin flag can be re-created without a unique-key collision.

## 2. Entities

### 2.1 `tb_backstage_permission`

The permission catalog. One row per grantable action; the SPA derives the key string as `resource.action` (e.g. `backstage_role.read`). Rows are backend-owned reference data.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `resource` | `String @db.VarChar` | No | Resource segment of the key (e.g. `role`, `cluster`, `user_backstage`) |
| `action` | `String @db.VarChar` | No | Action segment of the key (e.g. `read`, `create`, `manage`, `send`) |
| `description` | `String?` | Yes | Human-readable explanation shown in the Permission Catalog screen and PermissionPicker tooltips |
| `doc_version` | `Int @default(0) @db.Integer` | No | Optimistic-lock token, added 2026-07-16 (platform-wide rollout, all 35 tables) |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- `@@unique([resource, action, deleted_at])` — map `"backstage_permission_resource_action_deleted_at_u"` — one live row per key; a soft-deleted key can be re-introduced

**Indexes:** none beyond the unique map.

### 2.2 `tb_backstage_role`

A named, activatable bundle of permissions. The role's key set lives entirely in the join table (§2.3); this row holds only identity and status.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `name` | `String @db.VarChar` | No | Role name; unique among live rows |
| `description` | `String?` | Yes | Optional description shown in the Roles list |
| `is_active` | `Boolean?` | Yes | Default `true`; Active/Inactive badge in the SPA |
| `doc_version` | `Int @default(0) @db.Integer` | No | Optimistic-lock token, added 2026-07-16; `RoleEdit.tsx` sends it on every `PUT` and shows a conflict toast + reload on mismatch |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- `@@unique([name, deleted_at])` — map `"backstage_role_name_deleted_at_u"` — allows name re-use after soft delete

**Indexes:** none beyond the unique map.

### 2.3 `tb_backstage_role_tb_permission`

M:N join between roles and catalog rows. Each row grants one permission to one role. The SPA's delta writes (`permissions: { add, remove }`) translate to inserting and soft-deleting rows here.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `backstage_role_id` | `String @db.Uuid` | No | FK to `tb_backstage_role.id` |
| `backstage_permission_id` | `String @db.Uuid` | No | FK to `tb_backstage_permission.id` |
| `is_active` | `Boolean?` | Yes | Default `true`; grant active flag |
| `doc_version` | `Int @default(0) @db.Integer` | No | Optimistic-lock token, added 2026-07-16 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- FK: `backstage_role_id` → `tb_backstage_role.id` (`onDelete: NoAction, onUpdate: NoAction`)
- FK: `backstage_permission_id` → `tb_backstage_permission.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([backstage_role_id, backstage_permission_id, deleted_at])` — map `"backstage_role_permission_deleted_at_u"` — a removed grant can be re-added

**Indexes:**
- `@@index([backstage_permission_id, deleted_at])` — map `"backstage_role_permission_permission_deleted_at_idx"` — supports "which roles grant key X" lookups

### 2.4 `tb_user_tb_backstage_role`

The assignment table: binds a user to a role at a scope. This is the row the User Platform detail screen creates and deletes, and the input to the effective-permissions flattening.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()`; the `assignmentId` used by the delete endpoint |
| `user_id` | `String @db.Uuid` | No | Target user id — plain column, **no Prisma `@relation` to `tb_user`** |
| `backstage_role_id` | `String @db.Uuid` | No | FK to `tb_backstage_role.id` |
| `cluster_id` | `String? @db.Uuid` | Yes | Scope: `null` = platform-wide scope; set = scoped to this cluster (schema comment verbatim). Plain column, no `@relation` to `tb_cluster` |
| `doc_version` | `Int @default(0) @db.Integer` | No | Optimistic-lock token, added 2026-07-16 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- FK: `backstage_role_id` → `tb_backstage_role.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([user_id, backstage_role_id, cluster_id, deleted_at])` — map `"user_backstage_role_deleted_at_u"` — the same role may be assigned to the same user once per distinct scope

**Indexes:**
- `@@index([user_id, deleted_at])` — map `"user_backstage_role_user_deleted_at_idx"` — drives "roles of user X" (the list endpoint and effective-permissions flattening)
- `@@index([cluster_id, deleted_at])` — map `"user_backstage_role_cluster_deleted_at_idx"` — drives "assignments scoped to cluster Y"

### 2.5 `tb_backstage_super_admin`

The bypass flag. A live row here makes `is_super_admin: true` appear in the user's effective-permissions payload, short-circuiting every check. It carries no role or permission references — membership is the entire semantic.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()`; the id used by the remove endpoint |
| `user_id` | `String @db.Uuid` | No | Flagged user id — plain column, no `@relation` to `tb_user` |
| `is_active` | `Boolean?` | Yes | Default `true`; the SPA renders Inactive rows but they exist in data |
| `current_business_unit_id` | `String? @db.Uuid` | Yes | The BU this super admin last switched to (added 2026-10-26); lets the profile mark a current BU without creating seat-consuming membership links |
| `doc_version` | `Int @default(0) @db.Integer` | No | Optimistic-lock token, added 2026-07-16 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` — shown as "Added" in the SPA |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id |

**Constraints:**
- `@id` on `id`
- `@@unique([user_id, deleted_at])` — map `"backstage_super_admin_user_deleted_at_u"` — one live flag per user; removable and re-grantable

**Indexes:** none beyond the unique map.

## 3. Relationships

```
tb_backstage_role  1 ─── M  tb_backstage_role_tb_permission  M ─── 1  tb_backstage_permission
tb_backstage_role  1 ─── M  tb_user_tb_backstage_role
tb_user_tb_backstage_role.user_id     ──>  tb_user.id     (application-level, no Prisma FK)
tb_user_tb_backstage_role.cluster_id  ──>  tb_cluster.id  (application-level, no Prisma FK; null = platform scope)
tb_backstage_super_admin.user_id      ──>  tb_user.id     (application-level, no Prisma FK)
```

Declared FK relations (both `onDelete: NoAction, onUpdate: NoAction`):

- `tb_backstage_role_tb_permission.backstage_role_id` → `tb_backstage_role.id`
- `tb_backstage_role_tb_permission.backstage_permission_id` → `tb_backstage_permission.id`
- `tb_user_tb_backstage_role.backstage_role_id` → `tb_backstage_role.id`

Note the asymmetry: only the role-side links are real Prisma relations. `user_id` (on both the assignment and super-admin tables) and `cluster_id` (on the assignment table) are plain UUID columns with **no `@relation` directive and no database FK** — referential integrity to `tb_user` and `tb_cluster` is enforced at the application layer. Deleting a user or cluster does not cascade into these tables; orphaned assignment rows are possible at the schema level and testers should not assume the database prevents them.

## 4. Enums

This module defines **no enums**. The two places where an enum might be expected are deliberately not enums:

- **Permission keys** — `resource` and `action` are free-form `VarChar` columns. The key vocabulary is open-ended data, extended by backend seeds/migrations without a schema change.
- **Scope** — modelled as the nullable `cluster_id` column on `tb_user_tb_backstage_role`, not a scope-type enum. The SPA's `Scope` union type (§5) is a client-side construction over that column.

The legacy 7-value role enum that previously lived on the user row has been removed from the schema entirely — see the migration section of the [module landing](/en/platform/rbac).

## 5. Divergences from carmen-backstage SPA shape

The SPA types live in `../carmen-backstage/src/types/index.ts` (`Role`, `PermissionCatalogItem`, `UserRoleAssignment`, `Scope`, `EffectivePermissions`). The API flattens the Prisma graph considerably:

| SPA shape | SPA source | Prisma storage | Notes |
| --------- | ---------- | -------------- | ----- |
| `Role.permissions: string[]` (key strings) | `Role` | `tb_backstage_role_tb_permission` join rows | The API flattens join rows into derived `resource.action` strings; the SPA never sees join-row ids. Writes go back as deltas `{ add, remove }` (`roleService.RoleWriteData`), not as the full set |
| `permission_count` on list rows | `RoleRow` in `RoleManagement.tsx` | not a column | Server-side aggregate over live join rows; **absent on the single-role detail read** (`Role.permission_count?` is documented in `types/index.ts` as "list read model only") — the reach shown in `RoleIdentityHero` is instead computed client-side from `formData.permissions.length` |
| `PermissionCatalogItem.key` | `permissionService.getCatalog` | not a column | Derived; the service synthesizes `` `${resource}.${action}` `` when the response lacks `key` |
| `PermissionCatalogItem.created_at`/`created_by_name`/`audit` | `permissionService.getCatalog` mapper | audit trio on `tb_backstage_permission` | Optional and, in practice, always absent: `tb_backstage_permission` is seed data with `created_by_id` null throughout, so `PermissionCatalog.tsx`'s per-row `latestActor()`/`AuditMeta` line renders nothing today. The fields are kept in the type/mapper so the UI does not need a change if the backend ever attributes catalog edits to an actor |
| `Scope` union `{ type: 'backstage' } \| { type: 'cluster', cluster_id }` | `Scope` | single nullable `cluster_id` column | The discriminated union is an API/client construction; `type: 'platform'` ⇔ `cluster_id IS NULL` |
| `UserRoleAssignment.role_name` | `UserRoleAssignment` | not a column | Joined in from `tb_backstage_role.name` by the API for display |
| `EffectivePermissions` `{ platform, clusters, is_super_admin }` | `EffectivePermissions` | no table | Computed flattening of all live assignments + the super-admin flag; served by `GET /api/user/permission/backstage` |
| Flat `created_at`/`created_by_name` (or `created_by: {id,name}`) on role list rows | `RoleManagement.tsx` (via the shared `auditColumns()`/`normalizeAudit()`) | audit id columns | The list response may nest audit data as `audit.created/updated` `{ at, name }`; `normalizeAudit()` tries the **nested shape first** and falls back to the flat columns only when the nested entry is absent — not the reverse. List cells render this as relative time (`AuditMeta`, e.g. "5mo ago") with the absolute timestamp as a `title` tooltip, not a fixed string; the Updated cell is omitted only when the record has never really been edited (`everEdited`: an updated actor name is present, or its `at` differs from `created.at`) — not by a plain `updated_at === created_at` check |
| **`GET /api-system/backstage/roles/:id` carries no audit block at all** | `RoleEdit.fetchRole()` | n/a | The single-role detail payload is `{ id, doc_version, name, description, is_active, permissions }` only. `RoleEdit.tsx` compensates with a second, best-effort request — it re-queries the *list* endpoint filtered to that one `id` (`advance: { where: { id } }`) and lifts that row's audit fields for the `RoleIdentityHero` audit line. A role absent from that follow-up query (e.g. transient failure) simply shows no audit line rather than a wrong one |
| Multi-layer `{ data }` envelopes | `userRoleService.list`, `SuperAdminManagement.extractArray` | n/a | The user-roles and super-admins endpoints may nest `{ data: { data: [...] } }` deeper than the usual one level; both consumers descend until they hit an array |
| `RolesSummaryData` `{ total, active, inactive, deleted, top_roles }` | `RolesResponse.summary` (`roleService.getAccessSummary()`) | aggregate over `tb_backstage_role` | Unfiltered (no `search`/`advance`), fetched from a **dedicated summary endpoint** rather than a `perpage: -1` sweep of the list. `deleted` (soft-deleted role count) is carried on the wire but, before the 2026-09-02 `RolesAccessSummary` rewrite, was never rendered |
| `Role.doc_version?: number` | `Role` (`src/types/index.ts`) | `doc_version Int @default(0)` | **Aligned, not a divergence** — added to both sides in the 2026-07-16 rollout. `RoleEdit.tsx` reads it via `getDocVersion()` and sends it back on `PUT`, alongside the `permissions` delta |

### 5.1 Endpoints

REST surface consumed by the SPA services (`roleService.ts`, `permissionService.ts`, `superAdminService.ts`, `userRoleService.ts`):

| Method + Path | Purpose | Notes |
|---|---|---|
| `GET /api-system/backstage/roles` | Roles list | Paginated; rows carry `permission_count` and possibly nested `audit`; response may carry a `summary` block (`RolesSummaryData`) |
| `GET /api-system/backstage/roles/summary` | Roles access summary (added since the last sync) | `roleService.getAccessSummary()` — unfiltered fleet-wide aggregate, not scoped to the table's current search/filter |
| `POST /api-system/backstage/roles` | Create role | Body includes `permissions: { add: string[] }` |
| `GET /api-system/backstage/roles/:id` | Role detail | Returns flattened `permissions: string[]`; **no audit block** (see §5 above) |
| `PUT /api-system/backstage/roles/:id` | Update role | Body includes `permissions: { add: string[], remove: string[] }` (delta) plus `doc_version` when known — a mismatch is surfaced as a version-conflict toast and the page re-fetches |
| `DELETE /api-system/backstage/roles/:id` | Delete role | |
| `GET /api-system/backstage/permissions` | Permission catalog | Read-only; no write endpoints exist in the SPA. **Enforced server-side on `backstage_role.read`** (`RequireBackstagePermission`, `backstage-permissions.controller.ts`) even though the SPA route that calls it (`/backstage/category-permissions`) carries no frontend permission gate |
| `GET /api-system/backstage/super-admins` | Super-admin list | Response may nest multi-layer `{ data }` envelopes |
| `POST /api-system/backstage/super-admins` | Grant flag | Body `{ user_id }` |
| `DELETE /api-system/backstage/super-admins/:id` | Revoke flag | `:id` is the flag-row id, not the user id |
| `GET /api-system/backstage/users/:userId/roles` | List assignments | Response may nest multi-layer `{ data }` envelopes |
| `POST /api-system/backstage/users/:userId/roles` | Add assignment | Body `{ role_id, scope }` with the `Scope` union shape |
| `DELETE /api-system/backstage/users/:userId/roles/:assignmentId` | Remove assignment | `:assignmentId` is the `tb_user_tb_backstage_role.id` |
| `GET /api/user/permission/backstage` | Effective permissions of the current session | Called post-login and on every `AuthProvider` mount |

## 6. References

**Primary (source of truth):**
- `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/schema.prisma` (backend HEAD `2378c3b`, 2026-09-05) — models `tb_backstage_permission` (line 1007), `tb_backstage_role` (line 1026), `tb_backstage_role_tb_permission` (line 1046), `tb_user_tb_backstage_role` (line 1067), `tb_backstage_super_admin` (line 1090). Field lists are unchanged since the last sync — only line numbers shifted, from tables other modules added earlier in the file.

**Secondary (consumer shape):**
- `../carmen-backstage/src/types/index.ts` — `Role`, `PermissionCatalogItem`, `UserRoleAssignment`, `Scope`, `EffectivePermissions`, `RolesSummaryData`.
- `../carmen-backstage/src/services/roleService.ts` — `RoleWriteData` delta shape, roles endpoints, `getAccessSummary()`.
- `../carmen-backstage/src/services/permissionService.ts` — catalog mapping (key derivation), effective-permissions fetch.
- `../carmen-backstage/src/pages/RoleEdit.tsx` — `fetchAudit()`, the list-endpoint audit fallback for the detail page.
- `../carmen-turborepo-backend/apps/backend-gateway/src/backstage/backstage-permissions/backstage-permissions.controller.ts` — `RequireBackstagePermission('backstage_role.read')` on the catalog endpoint.
- `../carmen-backstage/src/services/superAdminService.ts` and `src/pages/SuperAdminManagement.tsx` — super-admin endpoints and the envelope-descending `extractArray`.
- `../carmen-backstage/src/services/userRoleService.ts` — assignment endpoints and envelope descent.

**Cross-links:** [Platform RBAC landing](/en/platform/rbac) &nbsp;·&nbsp; [UI Screens](/en/platform/rbac/ui-screens) &nbsp;·&nbsp; [Permissions](/en/platform/rbac/permissions) &nbsp;·&nbsp; [users data-model](/en/platform/users/data-model) (the `tb_user` rows assignments point at)
