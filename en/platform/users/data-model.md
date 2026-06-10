---
title: User — Data Model
description: User entity, profile extension, status, per-cluster BU assignments.
published: true
date: 2026-06-10T14:00:00.000Z
tags: book/platform, users, data-model
editor: markdown
dateCreated: '2026-05-19T00:00:00.000Z'
---

# User — Data Model

> **At a Glance**
> **Tables:** `tb_user` &nbsp;·&nbsp; `tb_cluster_user` &nbsp;·&nbsp; `tb_user_tb_business_unit` &nbsp;·&nbsp; `tb_user_profile` (profile extension, incl. `avatar_file_token`) &nbsp;·&nbsp; **Enums:** `enum_cluster_user_role` (admin/user) &nbsp;·&nbsp; `enum_user_business_unit_role` (admin/user) &nbsp;·&nbsp; **Audit columns:** standard `created_*`/`updated_*`/`deleted_*` trio on every table, surfaced as a nested `audit` object by the API &nbsp;·&nbsp; **Platform access:** not stored on these tables — RBAC role assignments own it (see [Platform RBAC](/en/platform/rbac))

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The Users module is backed by four tables. `tb_user` is the identity anchor: one row per person, holding the fields required for sign-in (`username`, `email`) and the `is_active` / `is_consent` flags that gate access. What the account may do in the Platform admin SPA is **not** stored here — the legacy `platform_role` column was removed along with `enum_platform_role` (see §4 historical note); platform access now lives in the RBAC assignment tables (`tb_user_tb_platform_role` and friends), documented in the [Platform RBAC data model](/en/platform/rbac/data-model). Name parts (`firstname`, `middlename`, `lastname`), the avatar (`avatar_file_token`), and supplementary contact fields live in the companion table `tb_user_profile`, which has a 1:M relation to `tb_user` via `user_id` — the Prisma relation is 1:M at the schema level, but the application treats it as a 1:1 extension of `tb_user` — see §2.4 for the constraint detail.

The two many-to-many join tables extend the user into organisational scope. `tb_cluster_user` records which clusters a user belongs to and at what per-cluster role (`admin` or `user`); this table is authoritatively mutated from the cluster edit page, not from the Users module. `tb_user_tb_business_unit` records which business units a user is assigned to within those clusters, carrying its own per-BU role and an `is_default` flag that marks the BU the inventory application should land on at login; this table is mutated from the Add BU dialog on the user edit screen.

All four tables carry the full audit trio — `created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id` — enabling soft-delete and full audit trails. The `deleted_at`-based unique constraints on all join tables mean a user-cluster or user-BU relationship can be logically deleted and then re-created without a unique-key collision.

## 2. Entities

### 2.1 `tb_user`

The identity row. One row per platform user, driving sign-in. This table does not store a password hash directly — credential management is delegated to Keycloak; the `fetchKeycloakUsers` API call synchronises user records from Keycloak into this table. Online-presence fields (`socket_id`, `is_online`) track real-time WebSocket state. **Historical note:** until 2026-06-10 this table carried a `platform_role` enum column (`enum_platform_role`, 7 values) that drove every access gate in the SPA; both the column and the enum are gone from the schema, replaced by RBAC role assignments — see [Platform RBAC §5](/en/platform/rbac) for the legacy→replacement mapping.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key, UUID v4 |
| `username` | `String @db.VarChar` | No | — | Sign-in handle; unique (with `deleted_at`); set once at create and disabled in the edit form |
| `email` | `String @db.VarChar` | No | — | Email address; indexed |
| `alias_name` | `String? @db.VarChar` | Yes | — | Display alias, shown in place of full name when set |
| `is_active` | `Boolean?` | Yes | `false` | When `false`, sign-in is blocked regardless of Keycloak state |
| `is_consent` | `Boolean?` | Yes | `false` | Tracks whether the user has accepted the terms/consent flow |
| `consent_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Timestamp of consent acceptance |
| `socket_id` | `String?` | Yes | — | WebSocket socket identifier for the current session, if any |
| `is_online` | `Boolean` | No | `false` | Real-time presence flag updated by the WebSocket layer |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: row creation time |
| `created_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the creator |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: last update time |
| `updated_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the last updater |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the deleter |

**Constraints:**
- `@id` on `id`
- `@@unique([username, deleted_at])` — map `"user_username_deleted_at_u"` — allows username re-use after soft delete
- FK: `created_by_id` → `tb_user.id` (NoAction / NoAction)
- FK: `updated_by_id` → `tb_user.id` (NoAction / NoAction)

**Indexes:**
- `@@index([email])` — map `"user_email_idx"`
- `@@index([username])` — map `"user_username_idx"`

### 2.2 `tb_cluster_user`

Many-to-many join between `tb_user` and `tb_cluster`. Each row records that a specific user belongs to a specific cluster, at what role, and whether that membership is currently active. This table is the authoritative source for cluster membership; the Users module shows these rows read-only in the Clusters card. The `parent_bu_id` field (nullable) identifies the billing-owner BU for the user within that cluster.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key |
| `user_id` | `String? @db.Uuid` | Yes | — | FK to `tb_user.id` |
| `cluster_id` | `String @db.Uuid` | No | — | FK to `tb_cluster.id` |
| `is_active` | `Boolean?` | Yes | `true` | Membership active flag |
| `parent_bu_id` | `String? @db.Uuid` | Yes | — | Billing-owner BU for this user-cluster relationship |
| `role` | `enum_cluster_user_role` | No | `user` | Per-cluster role: `admin` or `user` |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: row creation time |
| `created_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the creator |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: last update time |
| `updated_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the last updater |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the deleter |

**Constraints:**
- `@id` on `id`
- FK: `cluster_id` → `tb_cluster.id` (NoAction / NoAction)
- FK: `user_id` → `tb_user.id` (NoAction / NoAction)

**Indexes:**
- `@@unique([user_id, cluster_id, deleted_at])` — map `"user_cluster_deleted_at_u"` — allows re-assignment after soft delete

### 2.3 `tb_user_tb_business_unit`

Many-to-many join between `tb_user` and `tb_business_unit`. Each row records that a specific user is assigned to a specific business unit, at what role, whether that assignment is active, and whether it is the user's default BU (the one the inventory application lands on at login). This table is mutated from the Add BU dialog on the user edit screen; the `business_unit` module's Users card reads the same rows.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key |
| `user_id` | `String? @db.Uuid` | Yes | — | FK to `tb_user.id` |
| `business_unit_id` | `String? @db.Uuid` | Yes | — | FK to `tb_business_unit.id` |
| `role` | `enum_user_business_unit_role` | No | `user` | Per-BU role: `admin` or `user`; orthogonal to the platform RBAC assignments |
| `is_default` | `Boolean?` | Yes | `false` | Marks the BU the inventory app lands on at login |
| `is_active` | `Boolean?` | Yes | `true` | Assignment active flag |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: row creation time |
| `created_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the creator |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: last update time |
| `updated_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the last updater |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the deleter |

**Constraints:**
- `@id` on `id`
- FK: `business_unit_id` → `tb_business_unit.id` (NoAction / NoAction)
- FK: `user_id` → `tb_user.id` (NoAction / NoAction)

**Indexes:**
- `@@unique([user_id, business_unit_id, deleted_at])` — map `"user_businessunit_user_business_unit_deleted_at_u"` — allows re-assignment after soft delete

### 2.4 `tb_user_profile`

Profile extension for `tb_user`. Holds the name parts and supplementary contact fields that the SPA surfaces in the User Details form as editable fields. The Prisma relation is 1:M (`user_id` is nullable with no UNIQUE constraint at the Prisma level), but the application treats it as a 1:1 extension, creating or updating exactly one profile row per user.

| Field | Prisma Type | Nullable | Default | Description |
| ----- | ----------- | -------- | ------- | ----------- |
| `id` | `String @db.Uuid` | No | `gen_random_uuid()` | Primary key |
| `user_id` | `String? @db.Uuid` | Yes | — | FK to `tb_user.id` |
| `firstname` | `String @db.VarChar(100)` | No | `""` | Given name |
| `middlename` | `String? @db.VarChar(100)` | Yes | `""` | Middle name |
| `lastname` | `String? @db.VarChar(100)` | Yes | `""` | Family name |
| `telephone` | `String? @db.VarChar(20)` | Yes | — | Contact telephone number |
| `bio` | `Json? @db.Json` | Yes | `{}` | Free-form biography/notes as JSON |
| `avatar_file_token` | `String? @db.VarChar` | Yes | — | Reference to the user's avatar image in the platform file service. The API resolves it to a presigned `avatar_url` string on user list and detail responses — the raw token is not exposed to the SPA (same `file_token` storage pattern as `tb_cluster.avatar_file_token` and `tb_business_unit.logo_file_token`; see §5). Added 2026-05-20. |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: row creation time |
| `created_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the creator |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | `now()` | Audit: last update time |
| `updated_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the last updater |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | — | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | — | Audit: FK to `tb_user.id` of the deleter |

**Constraints:**
- `@id` on `id`
- FK: `user_id` → `tb_user.id` (NoAction / NoAction)

**Indexes:**
- `@@index([firstname, lastname])` — map `"userprofile_firstname_lastname_idx"`
- `@@index([user_id])` — map `"userprofile_user_idx"`

## 3. Relationships

```
tb_user  1 ─── M  tb_cluster_user  M ─── 1  tb_cluster
tb_user  1 ─── M  tb_user_tb_business_unit  M ─── 1  tb_business_unit
tb_user  1 ─── M  tb_user_profile
tb_user  self-FK  created_by_id, updated_by_id  (audit relations)
```

Key FK directions (all `onDelete: NoAction, onUpdate: NoAction`):

- `tb_cluster_user.user_id` → `tb_user.id`
- `tb_cluster_user.cluster_id` → `tb_cluster.id`
- `tb_user_tb_business_unit.user_id` → `tb_user.id`
- `tb_user_tb_business_unit.business_unit_id` → `tb_business_unit.id`
- `tb_user_profile.user_id` → `tb_user.id`

Note: `tb_user_tb_business_unit` does **not** carry a `cluster_id` column in the Prisma schema. The scoping of available BUs to the user's existing clusters is enforced at the application layer (the Add BU dialog queries BUs filtered by the user's current cluster memberships), not as a FK constraint at the database level.

## 4. Enums

### `enum_platform_role` — removed (historical)

Until 2026-06-10 the schema defined a 7-value `enum_platform_role` (`super_admin`, `platform_admin`, `support_manager`, `support_staff`, `security_officer`, `integration_developer`, `user`) carried on `tb_user.platform_role`, and the SPA's login gate checked the value against an `ALLOWED_ROLES` allow-list. Both the enum and the column are gone from the Prisma platform schema, and the frontend dropped every reference (commits `6091ffc`, `5f629f2` in `carmen-platform`). Platform access is now expressed as permission-key role assignments in `tb_platform_role` / `tb_user_tb_platform_role` (with a separate `tb_platform_super_admin` flag table) — see the [Platform RBAC data model](/en/platform/rbac/data-model) for those tables and [Platform RBAC §5](/en/platform/rbac) for the full legacy→replacement mapping.

### `enum_cluster_user_role` — 2 values

Carried on `tb_cluster_user.role`. Controls what the user can do within a specific cluster. Independent from the platform-level RBAC assignments — a Carmen support engineer could have cluster `admin` rights on one cluster and cluster `user` rights on another.

| Value | Meaning |
| ----- | ------- |
| `admin` | Cluster-level administrator; can manage the cluster's BUs and user roster |
| `user` | Standard cluster member; read and operational access within the cluster |

### `enum_user_business_unit_role` — 2 values

Carried on `tb_user_tb_business_unit.role`. Controls what the user can do within a specific business unit. Independent from both the platform-level RBAC assignments and `enum_cluster_user_role`.

| Value | Meaning |
| ----- | ------- |
| `admin` | BU-level administrator; can manage the BU's settings and inventory operations |
| `user` | Standard BU member; operational access to the BU's inventory workflows |

## 5. Divergences from carmen-platform SPA shape

The `UserFormData` interface in `UserEdit.tsx` (lines 59–67) declares 7 editable fields: `username`, `email`, `alias_name`, `firstname`, `middlename`, `lastname`, `is_active`. (Historical: `platform_role` was the 8th field until the RBAC migration removed it from the form and the schema — commit `6091ffc`.)

The Prisma-level divergence is that `firstname`, `middlename`, and `lastname` do **not** live in `tb_user`. They live in `tb_user_profile`. The SPA flattens both tables into a single `UserFormData` object and splits writes between `tb_user` (core fields) and `tb_user_profile` (name fields) transparently. The `UserEdit.tsx` load function confirms this: it merges `profile.firstname || user.firstname` when populating the form, reflecting that some older records may have had name fields on the user row before the profile extension table was introduced.

The `User` interface in `src/types/index.ts` also carries `firstname`, `middlename`, `lastname` directly (not nested under a `user_profile` key), which is the flattened API response shape rather than the Prisma storage shape.

The load function additionally reads `profile.alias_name || user.alias_name`; since `alias_name` has never lived on `tb_user_profile`, the profile leg always resolves to undefined and `user.alias_name` is the effective value — a defensive fallback the SPA carries but does not depend on.

Three further read-shape divergences:

- **Audit columns** — Prisma stores the flat trio (`created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id`, raw IDs); the API resolves the `_id` FKs to actor names and groups everything under a nested `audit` object (`audit.created/updated/deleted`, each `{ at, id, name, avatar }`). The SPA list page flattens this back into `created_at`/`created_by_name` etc. for its date columns, tolerating the older flat shape, which wins when present (`item.created_at ?? item.audit?.created?.at` — commits `f9b61cb`, `30b5bd6` in `carmen-platform`).
- **Avatar** — Prisma stores `avatar_file_token` on `tb_user_profile`; the API returns a presigned **`avatar_url` string** on list and detail responses, and the SPA reads `user.avatar_url || profile.avatar_url`. Note the contrast with clusters/business units, where the same token pattern resolves to an embedded `PresignedImage` *object* (`{ url, expires_at }`) on a `logo`/`avatar` key — users get a plain string.
- **Nested assignment arrays** — the detail response (`GET /api-system/user/:id`) embeds the user's `clusters` (the `tb_cluster_user` rows with a nested `cluster` object) and `business_units` (the `tb_user_tb_business_unit` rows with a nested `business_unit` object); the list response embeds a `business_unit` array used for the BU active/total count column.

No other divergences detected as of 2026-06-10.

| SPA field | SPA source | Prisma table | Notes |
| --------- | ---------- | ------------ | ----- |
| `username` | `UserFormData` | `tb_user.username` | Aligned |
| `email` | `UserFormData` | `tb_user.email` | Aligned |
| `alias_name` | `UserFormData` | `tb_user.alias_name` | Loaded via `profile.alias_name \|\| user.alias_name`; profile leg is always undefined — effectively aligned. |
| `is_active` | `UserFormData` | `tb_user.is_active` | Aligned |
| `firstname` | `UserFormData` | `tb_user_profile.firstname` | SPA flattens profile into user form |
| `middlename` | `UserFormData` | `tb_user_profile.middlename` | SPA flattens profile into user form |
| `lastname` | `UserFormData` | `tb_user_profile.lastname` | SPA flattens profile into user form |
| `avatar_url` | `UserRecord` / detail read shape (read-only) | `tb_user_profile.avatar_file_token` | Presigned-URL resolution server-side; not part of the form |

## 6. References

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — models `tb_user` (line 472), `tb_cluster_user` (line 243), `tb_user_tb_business_unit` (line 600), `tb_user_profile` (line 555); enums `enum_cluster_user_role` (line 645), `enum_user_business_unit_role` (line 661). Line numbers as of 2026-06-10. (`enum_platform_role` and `tb_user.platform_role` no longer exist — see §4.)

**Secondary (consumer shape):**
- `../carmen-platform/src/pages/UserEdit.tsx` — `UserFormData` interface (lines 59–67); `BU_ROLES` constant; load logic merging `tb_user` + `tb_user_profile` fields and resolving `avatar_url`.
- `../carmen-platform/src/pages/UserManagement.tsx` — `UserRecord` list shape (incl. `avatar_url` and the nested-`audit` flattening).
- `../carmen-platform/src/types/index.ts` — `User` interface (flattened API response shape), `UserInfo` interface, `Audit`/`AuditEntry`.
- `../carmen-platform/src/services/userService.ts` — REST client at `/api-system/user`.
- `../carmen-platform/src/context/AuthContext.tsx` — permission-based login gate (effective permissions, not a role allow-list); see [Platform RBAC](/en/platform/rbac).

**Landing cross-link:** [users](/en/platform/users)
