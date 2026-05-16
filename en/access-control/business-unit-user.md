---
title: Business Unit User
description: The per-business-unit membership pivot — declares which users may access which BUs, plus the temporary-invitation staging table.
published: true
date: 2026-05-16T08:00:00.000Z
tags: access-control, business-unit-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Business Unit User

## 1. Purpose

`business-unit-user` is the **multi-tenant access pivot**: it declares that a given [[access-control/user]] is allowed to operate inside a given [[master-data/business-unit]], and gives them a coarse BU-level role (`admin` or `user`). Without an active row here, a user cannot see the BU in their business-unit selector, regardless of which [[access-control/application-role]]s exist for that BU. With a row here, the user enters the BU, the JWT `x-app-id` resolves, and tenant-side RBAC kicks in.

A companion table `tb_temp_bu_user` stages **email-based invitations** before the recipient has signed up: it stores BU id, email, and role and is consumed when the user accepts the invitation and a real `tb_user` exists to bind to. The two tables together implement the "invite → accept → grant access" flow.

## 2. Prisma Model(s)

Source: platform schema.

### 2.1 `tb_user_tb_business_unit`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String? @db.Uuid` | Yes | FK to `tb_user`. |
| `business_unit_id` | `String? @db.Uuid` | Yes | FK to `tb_business_unit`. |
| `role` | `enum_user_business_unit_role` | No | Default `user`. Coarse per-BU role (`admin` or `user`). |
| `is_default` | `Boolean?` | Yes | Default `false`. Marks the BU the user lands in after login. |
| `is_active` | `Boolean?` | Yes | Default `true`. Disables access without unlinking. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, business_unit_id, deleted_at])` map `user_businessunit_user_business_unit_deleted_at_u` — a user has at most one active membership per BU. FKs to `tb_user` and `tb_business_unit` both `onDelete: NoAction`. `enum_user_business_unit_role` values: `admin`, `user`.

### 2.2 `tb_temp_bu_user`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `business_unit_id` | `String @db.VarChar(255)` | No | Target BU id (stored as string because the inviter and invitee tenants may resolve it differently). |
| `email` | `String @db.VarChar(255)` | No | Invited email. |
| `role` | `String @db.VarChar(50)` | No | Intended role (stringified `enum_user_business_unit_role`). |
| `created_at` | `DateTime @db.Timestamptz(6)` | No | Default `now()`. Used together with TTL to expire stale invites. |

**Constraints:** no unique constraints — multiple pending invitations for the same email + BU may coexist while the first is in flight; the application is responsible for dedup before insertion. There is no FK to `tb_user` because the invitee may not yet exist; the row is paired with a short-lived invitation token (see `tb_shot_url`).

## 3. Usage / Cross-References

- **All transactional modules** — every authenticated request resolves the active BU through this table; without an active row the BU is invisible.
- [[access-control/user]] — the user side of the membership.
- [[master-data/business-unit]] — the BU side of the membership.
- [[access-control/application-role]] — application roles are BU-scoped, so this table is the prerequisite for any role assignment within a BU.

## 4. Configuration UI

Managed by **Sysadmin** at the BU level (the BU-admin screen lists users with their per-BU role and default flag) and by users themselves through the BU switcher (which writes `is_default` when they pick a new home BU). Invitations are sent from the BU user-management screen and write into `tb_temp_bu_user` plus an entry in `tb_shot_url` for the email link. Security Officer audits membership changes.

## 5. Business Rules

- **Uniqueness.** At most one active `(user_id, business_unit_id)` row per user — re-inviting an existing member toggles `is_active` rather than inserting a duplicate.
- **Default BU invariant.** At most one row per user should carry `is_default = true`. Application-enforced; changing the default BU updates one row to `true` and any previously-default row to `false`.
- **Role semantics.** `role = admin` grants BU-wide administrative capabilities (manage roles, invite users, view audit) without needing a separate [[access-control/application-role]]. `role = user` is the default and relies on application-role assignments for capabilities.
- **Invitation lifecycle.** A `tb_temp_bu_user` row plus a `tb_shot_url` row is the unit of an invitation. Accepting the invitation upserts a `tb_user_tb_business_unit` row for the resolved user and removes both staging rows; expiry deletes them.
- **Deletion guards.** Hard-delete is allowed because there is no transactional FK targeting this table. Soft-delete (`deleted_at`) preserves audit history; the user loses access on next request because the membership filter requires `deleted_at IS NULL` and `is_active = true`.
- **Inactivation behaviour.** Setting `is_active = false` revokes the user's access to the BU at the next request without touching their application-role assignments — useful for temporary suspension.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_tb_business_unit` (lines ~511-532), `tb_temp_bu_user` (lines ~548-554), `enum_user_business_unit_role` (lines ~582-585).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/cluster/` (cluster + BU admin) and the BU user-management screen.
- **Cross-module:** see Section 3.
