---
title: User
description: Core user account with profile, password, and login-session tables — the identity behind every audit column in the system.
published: true
date: 2026-05-17T07:28:28.000Z
tags: access-control, user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# User

> **At a Glance**
> **Owner:** Sysadmin (+ Security Officer for credentials) &nbsp;·&nbsp; **Table:** `tb_user` (+ `tb_user_profile`, `tb_password`, `tb_user_login_session`) &nbsp;·&nbsp; **Used by:** every `*_by_id` audit column in the system &nbsp;·&nbsp; Identity layer — the most-FK'd entity in the platform.

![User screen](/assets/screenshots/access-control/user.png)

## 1. What & Who

The user entity is the **identity layer** for the entire platform. Every transactional row in every tenant carries `created_by_id` / `updated_by_id` / `deleted_by_id` referencing a row here, so this is the most-foreign-keyed entity in the system. It also feeds RBAC ([[access-control/application-role]]), per-BU access ([[access-control/business-unit-user]]), and per-location scoping ([[access-control/user-location]]).

The entity is split across four tables: `tb_user` (account), `tb_user_profile` (name/phone/bio), `tb_password` (bcrypt + expiry), `tb_user_login_session` (tokens). Splitting keeps the hot path narrow.

**Maintained by** Sysadmin (accounts) and Security Officer (credentials/sessions). **Read by** every API request (audit + auth).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a user account | Platform admin → User Management → **New** | Sets `tb_user` + initial `tb_password` |
| Edit profile (firstname, phone) | Account → Profile screen | User can self-edit |
| Reset password | Security Officer → User → **Reset** | Inserts new `tb_password`, inactivates old |
| Deactivate account | Set `is_active = false` | Login blocked; FKs preserved |
| Force logout | Delete `tb_user_login_session` rows | Or wait for `expired_on` to lapse |
| Soft-delete user | Set `deleted_at` | FK targets remain valid for historical audit |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Username already exists" | App-level uniqueness on non-deleted users | Pick a different username |
| Login rejected after reset | Multiple active `tb_password` rows | Only one should be `is_active = true` — clean up |
| "Must accept T&Cs" | `is_consent = false` | User must accept to unlock transactional UI |
| Cannot hard-delete user | Audit FKs reference the row | Inactivate or soft-delete instead |
| Forced password change | `expired_on` past | User sets new password (rotates `tb_password`) |

## 4. Edge Cases

- **Platform role bypass.** `super_admin` / `platform_admin` bypass tenant RBAC; `security_officer` manages credentials; `integration_developer` exists for service accounts.
- **Online presence is best-effort.** `is_online` / `socket_id` are caches written by the realtime channel — **not** authoritative for security.
- **Password history.** Many `tb_password` rows per user — only one `is_active = true`; rotated hashes stay for replay detection.
- **Session uniqueness.** `token` is globally unique so token reuse is detectable.

---

## 5. Data Model (Dev)

Source: platform schema.

### 5.1 `tb_user`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. Target of every `*_by_id` FK. |
| `username` | `String @db.VarChar` | No | Login username. |
| `email` | `String @db.VarChar` | No | Login / contact email. |
| `alias_name` | `String? @db.VarChar` | Yes | Optional display alias. |
| `platform_role` | `enum_platform_role` | No | Default `user`. Coarse platform-wide role. |
| `is_active` | `Boolean?` | Yes | Default `false`. Account-enabled. |
| `is_consent` | `Boolean?` | Yes | Default `false`. T&C acceptance. |
| `socket_id` | `String?` | Yes | Live socket id (presence). |
| `is_online` | `Boolean` | No | Default `false`. Cached presence. |
| `consent_at` | `DateTime? @db.Timestamptz(6)` | Yes | When user accepted T&C. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**`enum_platform_role`:** `super_admin`, `platform_admin`, `support_manager`, `support_staff`, `security_officer`, `integration_developer`, `user`.

### 5.2 `tb_user_profile`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String? @db.Uuid` | Yes | FK to `tb_user`. |
| `firstname` / `middlename` / `lastname` | `String @db.VarChar(100)` | Mixed | Default `""`. |
| `telephone` | `String? @db.VarChar(20)` | Yes | Phone. |
| `bio` | `Json? @db.Json` | Yes | Default `{}`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 5.3 `tb_password`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` / `user_id` | `String @db.Uuid` | No | Keys. |
| `hash` | `String` | No | Bcrypt hash. |
| `is_active` | `Boolean?` | Yes | Default `false`. |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + '90 days'`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 5.4 `tb_user_login_session`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` / `user_id` | `String @db.Uuid` | No | Keys. |
| `token` | `String @db.VarChar` | No | Token string. |
| `token_type` | `enum_token_type` | No | Default `access_token`. |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + '1 day'`. |

**Constraints:** `@@unique([token])`. `enum_token_type`: `access_token`, `refresh_token`.

## 6. Business Rules

- **Uniqueness.** App-level: `username` and `email` globally unique among non-deleted users.
- **Deletion guards.** Users referenced by audit FKs cannot be hard-deleted — inactivate instead.
- **Consent.** `is_consent = true` required before transactional UI is unlocked.
- **Password rotation.** Many `tb_password` rows, one `is_active = true`. Past `expired_on` forces rotation.
- **Session lifecycle.** Short-lived; refresh deleted on logout; reuse detectable via unique `token`.
- **Online presence.** Caches only; not authoritative for security decisions.

## 7. Cross-References

- [[access-control/application-role]] — RBAC join.
- [[access-control/business-unit-user]] — per-BU access.
- [[access-control/user-location]] — tenant-side per-location scope.
- [[access-control/permission]] — granted transitively via roles.
- [[master-data/business-unit]] — every BU is audited by `tb_user`.
- All transactional modules — every `*_by_id` audit column.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user` (lines ~388-454), `tb_user_profile` (lines ~467-489), `tb_password` (lines ~303-321), `tb_user_login_session` (lines ~456-465), enums (lines ~561-580).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/account/` + platform admin user-management.
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`.
