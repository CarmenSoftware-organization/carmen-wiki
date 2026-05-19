---
title: User
description: Core user account with profile and login-session tables — the identity behind every audit column in the system. Passwords are externalized (no tb_password table).
published: true
date: 2026-05-20T01:00:00.000Z
tags: access-control, user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# User

> **At a Glance**
> **Owner:** Sysadmin (+ Security Officer for sessions) &nbsp;·&nbsp; **Table:** `tb_user` (+ `tb_user_profile`, `tb_user_login_session`) &nbsp;·&nbsp; **Used by:** every `*_by_id` audit column in the system &nbsp;·&nbsp; Identity layer — the most-FK'd entity in the platform. **Passwords are externalized** (the `tb_password` table was dropped 2026-05-17).

![User screen](/screenshots/access-control/user.png)

## 1. What & Who

The user entity is the **identity layer** for the entire platform. Every transactional row in every tenant carries `created_by_id` / `updated_by_id` / `deleted_by_id` referencing a row here, so this is the most-foreign-keyed entity in the system. It also feeds RBAC ([access-control/application-role](/en/inventory/access-control/application-role)), per-BU access ([access-control/business-unit-user](/en/inventory/access-control/business-unit-user)), and per-location scoping ([access-control/user-location](/en/inventory/access-control/user-location)).

The entity is split across three platform tables: `tb_user` (account), `tb_user_profile` (name/phone/bio/avatar), `tb_user_login_session` (tokens). Splitting keeps the hot path narrow. The `tb_password` table was removed on 2026-05-17 — password storage and verification now live in an external identity provider that issues the tokens recorded in `tb_user_login_session`. The platform schema is therefore credential-free.

**Maintained by** Sysadmin (accounts) and Security Officer (sessions). **Read by** every API request (audit + token validation). Password reset / rotation is handled by the external identity provider.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a user account | Platform admin → User Management → **New** | Sets `tb_user` row; initial credential provisioning happens in the external identity provider |
| Edit profile (firstname, phone, avatar) | Account → Profile screen | User can self-edit |
| Reset password | External identity provider's flow (e.g. reset email link) | No schema effect on the carmen platform side; subsequent logins simply present a fresh `access_token` |
| Deactivate account | Set `is_active = false` | Login blocked here even if external IdP still issues tokens (server validates `is_active`) |
| Force logout | Delete `tb_user_login_session` rows | Or wait for `expired_on` to lapse |
| Soft-delete user | Set `deleted_at` | FK targets remain valid for historical audit |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Username already exists" | App-level uniqueness on non-deleted users | Pick a different username |
| Login rejected unexpectedly | External identity provider rejected the credential or returned an unmapped subject | Investigate at the IdP; the platform schema no longer stores password state |
| "Must accept T&Cs" | `is_consent = false` | User must accept to unlock transactional UI |
| Cannot hard-delete user | Audit FKs reference the row | Inactivate or soft-delete instead |
| Forced password change | Driven by the external IdP's rotation policy | Handled outside this schema |

## 4. Edge Cases

- **Platform role bypass.** `super_admin` / `platform_admin` bypass tenant RBAC; `security_officer` manages credentials; `integration_developer` exists for service accounts.
- **Online presence is best-effort.** `is_online` / `socket_id` are caches written by the realtime channel — **not** authoritative for security.
- **No password history on this side.** Past hashes / rotation policy live in the external identity provider. The carmen platform schema only sees the issued token in `tb_user_login_session`.
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
| `avatar_file_token` | `String? @db.VarChar` | Yes | Reference to the user's avatar image in the platform file service (added 2026-05-20). Same `file_token` pattern as `tb_business_unit.logo_file_token` and `tb_product_image.file_token`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 5.3 `tb_user_login_session`

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
- **Password rotation.** Owned by the external identity provider — no rows on the carmen platform side.
- **Session lifecycle.** Short-lived; refresh deleted on logout; reuse detectable via unique `token`.
- **Online presence.** Caches only; not authoritative for security decisions.

## 7. Cross-References

- [access-control/application-role](/en/inventory/access-control/application-role) — RBAC join.
- [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) — per-BU access.
- [access-control/user-location](/en/inventory/access-control/user-location) — tenant-side per-location scope.
- [access-control/permission](/en/inventory/access-control/permission) — granted transitively via roles.
- [master-data/business-unit](/en/inventory/master-data/business-unit) — every BU is audited by `tb_user`.
- All transactional modules — every `*_by_id` audit column.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user`, `tb_user_profile`, `tb_user_login_session`, enums. `tb_password` was removed in commit `b2829da2` (2026-05-17); credential storage and verification now live in the external identity provider.
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/account/` + platform admin user-management.
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`.
