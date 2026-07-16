---
title: User
description: Core user account with profile and login-session tables — the identity behind every audit column in the system. Passwords are externalized (no tb_password table).
published: true
date: 2026-07-15T23:46:09.000Z
tags: access-control, user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# User

> **At a Glance**
> **Owner:** Sysadmin (+ Security Officer for sessions) &nbsp;·&nbsp; **Table:** `tb_user` (+ `tb_user_profile`, `tb_user_login_session`) &nbsp;·&nbsp; **Used by:** every `*_by_id` audit column in the system &nbsp;·&nbsp; Identity layer — the most-FK'd entity in the platform. **Passwords are externalized** (the `tb_password` table was dropped 2026-05-17).

![User screen](/screenshots/access-control/user.png)

![User detail screen](/screenshots/access-control/user-detail.png)

## 1. What & Who

The user entity is the **identity layer** for the entire platform. Every transactional row in every tenant carries `created_by_id` / `updated_by_id` / `deleted_by_id` referencing a row here, so this is the most-foreign-keyed entity in the system. It also feeds RBAC ([access-control/application-role](/en/inventory/access-control/application-role)), per-BU access ([access-control/business-unit-user](/en/inventory/access-control/business-unit-user)), and per-location scoping ([access-control/user-location](/en/inventory/access-control/user-location)).

The entity is split across three platform tables: `tb_user` (account), `tb_user_profile` (name/phone/bio/avatar), `tb_user_login_session` (tokens). Splitting keeps the hot path narrow. The `tb_password` table was removed on 2026-05-17 — password storage and verification now live in Keycloak (`auth.service.ts`'s `changePassword` proxies to the Keycloak Account API), which issues the tokens recorded in `tb_user_login_session`. The platform schema is therefore credential-free.

**Maintained by** Sysadmin (accounts) and Security Officer (sessions). **Read by** every API request (audit + token validation). Password reset / rotation is handled by the external identity provider.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a user account | **No create/invite screen in `carmen-inventory-frontend-react`** — confirmed by that repo's own e2e test-case doc (`1102-user.md`: "โมดูลนี้ไม่มีหน้า create/invite ผู้ใช้ใหม่"); `/system-admin/user/:id` only assigns roles/departments/locations to an *existing* account | Account creation happens via `/api/auth/invite-user` (email-only registration invite) or platform admin, outside this screen |
| Edit profile (firstname, phone, avatar) | `/profile/setting` (`routes/profile/user-profile-setting.tsx`) | User self-edit; avatar upload, signature upload also live here |
| Change password | `/profile/setting` → Change Password dialog (`change-password-dialog.tsx`) | Proxies to **Keycloak**'s Account API (`keycloak-auth.change-password`), which validates the current password; carmen platform schema never sees it. Auto-logs-out on success. |
| Deactivate account | Set `is_active = false` | Login blocked here even if Keycloak still issues tokens (server validates `is_active`) |
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

- **`platform_role` (the enum column) no longer exists.** It was dropped 2026-06-10 (`06d8a921` "remove legacy platform_role column and API surface") along with the login response field (`433b5e77`). Platform-wide roles are now a fully relational, cluster-scoped RBAC system — `tb_platform_role` (named roles) + `tb_platform_role_tb_permission` (bundle) + `tb_user_tb_platform_role` (assignment; `cluster_id = null` means platform-wide, a set value scopes the grant to one cluster) — with its own `tb_platform_permission` catalogue, distinct from the tenant-side `tb_permission` this page documents. Managing platform roles/clusters is Carmen Platform admin territory (see the Platform book), not this inventory-frontend `tb_user` record.
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
| `is_active` | `Boolean?` | Yes | Default `false`. Account-enabled. |
| `is_consent` | `Boolean?` | Yes | Default `false`. T&C acceptance. |
| `socket_id` | `String?` | Yes | Live socket id (presence). |
| `is_online` | `Boolean` | No | Default `false`. Cached presence. |
| `consent_at` | `DateTime? @db.Timestamptz(6)` | Yes | When user accepted T&C. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

There is no `platform_role` column — see Edge Cases for the relational system that replaced it.

### 5.2 `tb_user_profile`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String? @db.Uuid` | Yes | FK to `tb_user`. |
| `firstname` / `middlename` / `lastname` | `String @db.VarChar(100)` | Mixed | Default `""`. |
| `telephone` | `String? @db.VarChar(20)` | Yes | Phone. |
| `bio` | `Json? @db.Json` | Yes | Default `{}`. |
| `avatar_file_token` | `String? @db.VarChar` | Yes | Reference to the user's avatar image in the platform file service (added 2026-05-20). Same `file_token` pattern as `tb_business_unit.logo_file_token` and `tb_product_image.file_token`. |
| `signature_file_token` | `String? @db.VarChar` | Yes | Reference to the user's uploaded signature image; surfaced by `/profile/setting`'s Signature dialog and shown read-only on `/profile`. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

### 5.3 `tb_user_login_session`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` / `user_id` | `String @db.Uuid` | No | Keys. |
| `token` | `String @db.VarChar` | No | Token string. |
| `token_type` | `enum_token_type` | No | Default `access_token`. |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + '1 day'`. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-lock version. |

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

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user` (line 494), `tb_user_profile` (line 579), `tb_user_login_session` (line 567). `tb_password` was removed in commit `b2829da2` (2026-05-17); the `platform_role` enum column was removed in commit `06d8a921` (2026-06-10) — see Edge Cases. Credential storage and verification now live in Keycloak.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (`changePassword` — Keycloak Account API).
- **Frontend:** `../carmen-inventory-frontend-react/routes/profile/` (self-service profile, avatar, signature, change-password, BU list); `../carmen-inventory-frontend-react/routes/system-admin/user/` (admin: assign roles/departments/locations to existing users — no create/invite screen).
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1102-user.md` (documentation-only test-case catalog; explicitly notes there is no create/invite page).
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`.
