---
title: User
description: Core user account with profile, password, and login-session tables — the identity behind every audit column in the system.
published: true
date: 2026-05-16T08:00:00.000Z
tags: access-control, user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# User

## 1. Purpose

The user entity is the identity layer for the entire platform. Every transactional row in every tenant carries a `created_by_id` / `updated_by_id` / `deleted_by_id` referencing a row here, so the user record is the most-foreign-keyed entity in the system. It also feeds RBAC (via [[access-control/application-role]] join tables), per-business-unit access (via [[access-control/business-unit-user]]), and per-location scoping in the tenant schema (via [[access-control/user-location]]).

The entity is split across four platform-schema tables: `tb_user` holds the account itself (username, email, platform role, active / online / consent flags); `tb_user_profile` holds the human-readable name, telephone, and free-form bio; `tb_password` holds the bcrypt hash plus expiry; and `tb_user_login_session` holds short-lived access / refresh tokens. Splitting these keeps the hot path (`tb_user`) narrow and lets password rotation and session revocation operate on focused tables.

## 2. Prisma Model(s)

Source: platform schema.

### 2.1 `tb_user`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. Foreign-key target for every `*_by_id` column in tenant and platform. |
| `username` | `String @db.VarChar` | No | Login username. |
| `email` | `String @db.VarChar` | No | Login / contact email. |
| `alias_name` | `String? @db.VarChar` | Yes | Optional display alias. |
| `platform_role` | `enum_platform_role` | No | Default `user`. Coarse platform-wide role (see enum below). |
| `is_active` | `Boolean?` | Yes | Default `false`. Account-enabled flag. |
| `is_consent` | `Boolean?` | Yes | Default `false`. T&C acceptance flag. |
| `socket_id` | `String?` | Yes | Live socket id (presence). |
| `is_online` | `Boolean` | No | Default `false`. Cached online flag. |
| `consent_at` | `DateTime? @db.Timestamptz(6)` | Yes | When the user accepted T&C. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `id` is the primary key. The `tb_user` model declares numerous back-relations (`tb_application_role`, `tb_business_unit`, `tb_cluster`, etc.) used by the rest of platform — every `*_by_id` FK from any other model targets `tb_user.id` with `onDelete: NoAction`. `enum_platform_role` values: `super_admin`, `platform_admin`, `support_manager`, `support_staff`, `security_officer`, `integration_developer`, `user`.

### 2.2 `tb_user_profile`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String? @db.Uuid` | Yes | FK to `tb_user`. |
| `firstname` | `String @db.VarChar(100)` | No | Default `""`. |
| `middlename` | `String? @db.VarChar(100)` | Yes | Default `""`. |
| `lastname` | `String? @db.VarChar(100)` | Yes | Default `""`. |
| `telephone` | `String? @db.VarChar(20)` | Yes | Phone number. |
| `bio` | `Json? @db.Json` | Yes | Default `{}`. Free-form profile data. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** indexes on `(firstname, lastname)` map `userprofile_firstname_lastname_idx` and on `user_id` map `userprofile_user_idx`. FK to `tb_user` `onDelete: NoAction`.

### 2.3 `tb_password`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | FK to `tb_user`. |
| `hash` | `String` | No | Bcrypt-style password hash. |
| `is_active` | `Boolean?` | Yes | Default `false`. Active-credential flag. |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + '90 days'`. Forced-rotation deadline. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** index on `user_id` map `password_user_idx`. FK to `tb_user` `onDelete: NoAction`. Multiple rows per user is allowed — the application picks the most recent `is_active = true` row when authenticating; rotated hashes stay in the table for replay-detection.

### 2.4 `tb_user_login_session`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `token` | `String @db.VarChar` | No | The token string (access or refresh). |
| `token_type` | `enum_token_type` | No | Default `access_token`. `access_token` or `refresh_token`. |
| `user_id` | `String @db.Uuid` | No | FK to `tb_user`. |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + '1 day'`. Token expiry. |

**Constraints:** `@@unique([token])` map `user_login_session_token_u`. FK to `tb_user` `onDelete: NoAction`. `enum_token_type` values: `access_token`, `refresh_token`.

## 3. Usage / Cross-References

- **All transactional modules** — every `*_by_id` audit column references `tb_user`. This is the most-referenced platform entity.
- [[access-control/application-role]] — `tb_user_tb_application_role` joins users to roles.
- [[access-control/business-unit-user]] — `tb_user_tb_business_unit` grants per-BU access.
- [[access-control/user-location]] — tenant-side per-location scope.
- [[master-data/business-unit]] — every BU is created and updated by a `tb_user`.
- [[access-control/permission]] — granted indirectly through `tb_application_role_tb_permission`.

## 4. Configuration UI

Managed by **Sysadmin** and (for password resets / lockouts) by **Security Officer**. The user-management screen lists users with filters by platform role and active flag, opens to a tabbed edit (General, Profile, Roles, Business Units, Sessions). Profile edits are permitted by the user themselves through the account / profile screen. Password reset is a separate action that writes a new `tb_password` row and inactivates earlier ones for the same user.

## 5. Business Rules

- **Uniqueness.** Application-level: `username` and `email` are expected to be globally unique among non-deleted users (enforced by service code; check schema for any DB-level constraint).
- **Deletion guards.** A user referenced by audit columns on any document cannot be hard-deleted. Inactivate (`is_active = false`) instead. Soft-delete (`deleted_at`) is acceptable but the FK targets remain valid.
- **Platform role.** `platform_role` is a coarse switch — `super_admin` / `platform_admin` bypass tenant RBAC; `support_*` roles see read-only access for diagnostics; `security_officer` manages credentials; `integration_developer` exists for service accounts; `user` is the default for everyone else and is governed by per-BU roles and application-role assignments.
- **Consent.** `is_consent = true` is required before transactional UI is unlocked. `consent_at` records when consent was given.
- **Password rotation.** A user may have many `tb_password` rows; only one should be `is_active = true` at a time. When `expired_on` passes, the user is forced to set a new password.
- **Session lifecycle.** Sessions are short-lived (1 day for `access_token`); refresh tokens are deleted on logout. `token` is globally unique so token reuse is detectable.
- **Online presence.** `is_online` / `socket_id` are best-effort caches written by the realtime channel; they are not authoritative for security decisions.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user` (lines ~388-454), `tb_user_profile` (lines ~467-489), `tb_password` (lines ~303-321), `tb_user_login_session` (lines ~456-465), `enum_platform_role` (lines ~561-569), `enum_token_type` (lines ~577-580).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/account/` and the platform admin user-management screen under the platform / admin app.
- **carmen/docs (if applicable):** `../carmen/docs/workflow-permissions-system.md` describes the workflow-stage role types that complement the platform `enum_platform_role`.
- **Cross-module:** see Section 3.
