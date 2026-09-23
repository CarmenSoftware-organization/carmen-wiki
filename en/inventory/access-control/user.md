---
title: User
description: Core user account with profile and login-session tables — the identity behind every audit column. Passwords in Keycloak; email verification + partial unique indexes since 2026-08; access edited via PATCH /api/config/:bu_code/users/:id.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: access-control, user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# User

> **At a Glance**
> **Owner:** Sysadmin (+ Security Officer for sessions) &nbsp;·&nbsp; **Table:** `tb_user` (+ `tb_user_profile`, `tb_user_login_session`) &nbsp;·&nbsp; **Admin screen:** `/system-admin/user` (list, Print / Export user × role report) and `/system-admin/user/:id` (assign roles, locations, department) — permission `system_admin.user.view`, licence `system_admin.user` &nbsp;·&nbsp; **Endpoints:** `GET api/:bu_code/users` (with `roles[]`), `GET`/`PATCH api/config/:bu_code/users/:user_id` (single-response access record), `GET api/config/:bu_code/user-application-roles` (matrix), `GET`/`PATCH /api/user/profile`, `GET /api/user/permission` &nbsp;·&nbsp; **Used by:** every `*_by_id` audit column in the system &nbsp;·&nbsp; **Passwords are externalized** (the `tb_password` table was dropped 2026-05-17); email verification lives on `tb_user` since 2026-08-04.

## Implementation status (re-verified 2026-09-22)

- **Admin user screen is one request now.** `GET /api/config/:bu_code/users/:user_id` (`configUser.getAccess`, `config_users.controller.ts:149`) returns `UserDetail` — `user{ username, email, alias_name, is_active, firstname, middlename, lastname, telephone, avatar_url }`, `application_roles[{ id, application_role_id, application_role_name, application_role_description, assigned_at }]`, `locations[]`, `department{ id, name } | null` (BE `671288897`; FE `types/user.ts`). `PATCH` on the same URL (`configUser.patchAccess`, `:64`) takes `{ application_role_id?: { add, remove }, location_id?: { add, remove }, department_id?: string }` and applies roles (platform) + locations (tenant) + department in one transaction (BE `b9eb20818`, `9a91d7f32`; FE `a5038c84`, `39ae1bba`). Errors: `USER_ACCESS_NO_CHANGES`, `USER_ACCESS_ROLE_ADD_REMOVE_CONFLICT`, `USER_ACCESS_LOCATION_ADD_REMOVE_CONFLICT`, `USER_ACCESS_LOCATIONS_TO_ADD_NOT_FOUND`, `…_TO_REMOVE_NOT_FOUND`, `USER_ACCESS_LOCATION_WRITE_FAILED`, `USER_ACCESS_DEPARTMENT_NOT_FOUND`, `USER_ACCESS_DEPARTMENT_ALREADY_HOD` (`packages/error-catalog/src/catalog.ts:306-358`). Bruno: `config/users/{GET-get-access,PATCH-patch-access}-config-users.bru`.
- **Print / Export on the user list are real** (FE `ae37df84`, 2026-08-20): `use-user-role-report.ts` reads `GET /api/config/:bu_code/user-application-roles` twice (first for `paginate.total`, then `perpage=total`) and renders a user × role matrix — A4-landscape print via a hidden iframe, or CSV with a UTF-8 BOM. The matrix endpoint (BE `7a2390f11`) returns rows `{ user_id, username, email, firstname, middlename, lastname, bu_role, is_active, is_bu_active, role_ids[] }` with `summary.roles[]` as the column set (`config_user-application-roles/swagger/response.ts:77-152`; Bruno `config/user-application-roles/GET-find-matrix`). A prior FE build showed a "Coming soon" toast (`8c16c424`); superseded the same day.
- **`GET /api/user/profile` no longer carries `business_unit[i].license`** (BE `dc5623a05`, 2026-09-09, breaking) — licence data moved to `GET /api/license`. The profile still carries each BU's `config` JSON and the current inventory period the footer status bar reads.
- **`tb_user` columns and uniqueness changed** (platform migrations `20260804000000_user_email_verification`, `20260806000000_user_active_identifier_unique`): `email_verified_at`, `email_verification_token_hash`, `email_verification_expires_at` added; `@@unique([username, deleted_at])` dropped in favour of two **partial** unique indexes `user_email_active_u` on `lower(email)` and `user_username_active_u` on `lower(username)` where `deleted_at IS NULL` — Prisma cannot express partial indexes, so the schema shows only plain `@@index`es and the comment warns not to read that as "no uniqueness". Uniqueness is now case-insensitive.
- **Auth surface** (`apps/backend-gateway/src/auth/auth.controller.ts`): `login`, `logout`, `register`, `signup-request` (`AppIdGuard('auth.signup-request')`, sends a sign-up link), `signup-token/verify`, `verify-email`, `resend-verification`, `refresh-token`, `forgot-password`, `reset-password-with-token`. **`invite-user` was removed** on 2026-08-05 (`7f93ce6ad`, "remove the invite flow that never worked") — invitations are the cluster-scoped `tb_user_invitation` flow documented at [access-control/business-unit-user](/en/inventory/access-control/business-unit-user).
- `GET /api/user/:user_id/signature` (`user.getSignatureByUserId`, `user.controller.ts:602`) exposes another user's signature image for printed documents (Bruno `user-management/user/GET-get-signature-by-user-id`); the print layer's signature block (`99c5708d3`) reads it.
- The HOD block was removed from the user screen (`5684f93e`, 2026-09-04); department membership is shown/edited as a single `LookupDepartment` (`user-assigned-departments.tsx`).

![User screen](/screenshots/access-control/user.png)

![User detail screen](/screenshots/access-control/user-detail.png)

## 1. What & Who

The user entity is the **identity layer** for the entire platform. Every transactional row in every tenant carries `created_by_id` / `updated_by_id` / `deleted_by_id` referencing a row here, so this is the most-foreign-keyed entity in the system. It also feeds RBAC ([access-control/application-role](/en/inventory/access-control/application-role)), per-BU access ([access-control/business-unit-user](/en/inventory/access-control/business-unit-user)), and per-location scoping ([access-control/user-location](/en/inventory/access-control/user-location)).

The entity is split across three platform tables: `tb_user` (account), `tb_user_profile` (name/phone/bio/avatar), `tb_user_login_session` (tokens). Splitting keeps the hot path narrow. The `tb_password` table was removed on 2026-05-17 — password storage and verification now live in Keycloak (`auth.service.ts`'s `changePassword` proxies to the Keycloak Account API), which issues the tokens recorded in `tb_user_login_session`. The platform schema is therefore credential-free.

**Maintained by** Sysadmin (accounts) and Security Officer (sessions). **Read by** every API request (audit + token validation). Password reset / rotation is handled by the external identity provider.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a user account | **No create/invite screen in `carmen-inventory-frontend-react`** — confirmed by that repo's own e2e test-case doc (`1102-user.md`: "โมดูลนี้ไม่มีหน้า create/invite ผู้ใช้ใหม่"); `/system-admin/user/:id` only assigns roles/department/locations to an *existing* account | Accounts arrive via a cluster invitation (`POST api-system/clusters/:cluster_id/invitations` from the Platform, accepted at `POST api/invitations/:token/accept` or `…/accept-with-signup`) or self sign-up (`POST /api/auth/signup-request` → `signup-token/verify` → `register`); `/api/auth/invite-user` no longer exists |
| Assign roles / locations / department to a user | `/system-admin/user/:id` → **Edit** → tick roles (`user-assigned-roles.tsx`), tick locations (`user-assigned-locations.tsx` DataGrid), pick a department (`user-assigned-departments.tsx`) → Save | One `PATCH /api/config/:bu_code/users/:user_id` with only the diff (`buildUserPatch`) |
| Print / export the user × role matrix | `/system-admin/user` → **Print** / **Export** | `GET /api/config/:bu_code/user-application-roles`; print = A4 landscape with ✓ per role, export = CSV (Y / blank) |
| Edit profile (firstname, phone, avatar) | `/profile/setting` (`routes/profile/user-profile-setting.tsx`) | User self-edit; avatar upload, signature upload also live here |
| Change password | `/profile/setting` → Change Password dialog (`change-password-dialog.tsx`) | Proxies to **Keycloak**'s Account API (`keycloak-auth.change-password`), which validates the current password; carmen platform schema never sees it. Auto-logs-out on success. |
| Deactivate account | Set `is_active = false` | Login blocked here even if Keycloak still issues tokens (server validates `is_active`) |
| Force logout | Delete `tb_user_login_session` rows | Or wait for `expired_on` to lapse |
| Soft-delete user | Set `deleted_at` | FK targets remain valid for historical audit |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Username already exists" / "Email already exists" | Partial unique index on `lower(username)` / `lower(email)` among non-deleted users (DB-enforced since 2026-08-06, case-insensitive) | Pick a different value; soft-deleted accounts do not block reuse |
| `USER_ACCESS_*` errors on the assign screen | See Implementation status — conflicting add/remove, unknown location, department already has an HOD, etc. | Reload and resubmit |
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
| `socket_id` | `String?` | Yes | Live socket id (presence). (`is_online`, listed by a prior version of this page, is not on the model at HEAD.) |
| `consent_at` | `DateTime? @db.Timestamptz(6)` | Yes | When user accepted T&C. |
| `email_verified_at` | `DateTime? @db.Timestamptz(6)` | Yes | Set by `POST /api/auth/verify-email` (added 2026-08-04). |
| `email_verification_token_hash` / `email_verification_expires_at` | `String? @db.VarChar` / `DateTime?` | Yes | Hashed one-time token + expiry for the verification / sign-up link; indexed (`user_email_verification_token_hash_idx`). |
| `doc_version` | `Int` | No | Default `0`. Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** plain indexes on `email` and `username`; uniqueness is enforced by two partial unique indexes that exist **only in SQL** (`user_email_active_u`, `user_username_active_u` — `lower(col) WHERE deleted_at IS NULL`, migration `20260806000000_user_active_identifier_unique`). `is_online` was not present at HEAD (`schema.prisma` `model tb_user`) — the Edge-Case note below about presence caching refers to `socket_id` only. There is no `platform_role` column — see Edge Cases for the relational system that replaced it.

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

- **Uniqueness.** DB-level since 2026-08-06: `lower(username)` and `lower(email)` unique among non-deleted users (partial indexes, not visible in Prisma).
- **Access edits are atomic per user.** Roles, locations and department change in one `PATCH`; a location write failure after the role write is surfaced as `USER_ACCESS_LOCATION_WRITE_FAILED`.
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

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user`, `tb_user_profile`, `tb_user_login_session`; migrations `20260804000000_user_email_verification`, `20260806000000_user_active_identifier_unique`, `20260808100000_signup_verification`. `tb_password` was removed in commit `b2829da2` (2026-05-17); the `platform_role` enum column was removed in commit `06d8a921` (2026-06-10) — see Edge Cases. Credential storage and verification now live in Keycloak.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (`changePassword` — Keycloak Account API); gateway `apps/backend-gateway/src/auth/auth.controller.ts`, `apps/backend-gateway/src/application/user/user.controller.ts` (profile, permission, `api/:bu_code/users`, signature), `apps/backend-gateway/src/config/config_users/` (single-response access record + `PATCH`), `apps/backend-gateway/src/config/config_user-application-roles/` (matrix + per-user role CRUD).
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/users/`, `config/user-application-roles/GET-find-matrix-…`, `user-management/user/GET-get-signature-by-user-id-…`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/profile/` (self-service profile, avatar, signature, change-password, BU list); `../carmen-inventory-frontend-react/routes/system-admin/user/` (`user-component.tsx` list + Print/Export, `user-edit.route.tsx` + `user-edit-content.tsx`, `user-assigned-form.tsx`, `user-assigned-roles.tsx`, `user-assigned-locations.tsx`, `user-assigned-departments.tsx`, `user-assigned-form-schema.ts`, `use-user-role-report.ts`); `types/user.ts` (`UserDetail`, `UpdateUserPayload`, `UserApplicationRole`); `hooks/use-license.ts` + `types/license.ts` for the licence block that left the profile.
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1102-user.md` (39 cases, documentation-only; explicitly notes there is no create/invite page).
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`.
