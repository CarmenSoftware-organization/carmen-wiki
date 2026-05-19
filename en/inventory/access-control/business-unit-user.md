---
title: Business Unit User
description: The per-business-unit membership pivot — declares which users may access which BUs, plus the temporary-invitation staging table.
published: true
date: 2026-05-17T11:00:00.000Z
tags: access-control, business-unit-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Business Unit User

> **At a Glance**
> **Owner:** Sysadmin / BU Admin &nbsp;·&nbsp; **Table:** `tb_user_tb_business_unit` (+ `tb_temp_bu_user`) &nbsp;·&nbsp; **Used by:** every authenticated request (BU resolution) &nbsp;·&nbsp; The multi-tenant access pivot — declares which users may operate inside which BUs.

## 1. What & Who

`business-unit-user` is the **multi-tenant access pivot**: it declares that a given [[access-control/user]] is allowed to operate inside a given [[master-data/business-unit]], and assigns a coarse BU-level role (`admin` or `user`). Without an active row here, a user cannot see the BU in their BU selector regardless of which [[access-control/application-role]]s exist for that BU. With a row, the user enters the BU, JWT `x-app-id` resolves, and tenant RBAC kicks in.

The companion `tb_temp_bu_user` stages **email-based invitations** before the recipient signs up: BU id, email, role — consumed when the user accepts and a real `tb_user` exists.

**Maintained by** Sysadmin and BU admins. **Read by** every authenticated request.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Grant a user access to a BU | BU user-management screen → **Add** | Pick user, set role (`user` or `admin`) |
| Invite a non-user by email | BU user-management → **Invite** | Writes `tb_temp_bu_user` + `tb_shot_url` token |
| Change a user's default BU | BU switcher → pick BU → "Make default" | Flips `is_default` on one row, unsets others |
| Suspend access without removing | Toggle `is_active = false` | User loses access on next request; role assignments preserved |
| Revoke access permanently | Soft-delete the row | Membership filter requires `deleted_at IS NULL` |
| Promote to BU admin | Edit row → set `role = admin` | Grants BU-wide admin powers without needing a separate app role |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| BU missing from switcher after grant | Cached session | Refresh / re-login |
| "Email already invited" | Pending `tb_temp_bu_user` row exists | Cancel old invite or wait for acceptance/expiry |
| Multiple `is_default = true` rows | Application invariant violated | Run repair script; should be at most one per user |
| Invitation link 404 | Token expired in `tb_shot_url` | Re-send invitation |

## 4. Edge Cases

- **No uniqueness on `tb_temp_bu_user`** — multiple pending invitations for the same (email, BU) may coexist; app is responsible for dedup.
- **Role = `admin`** grants BU-wide admin (manage roles, invite users) without needing a separate application role.
- **Cross-schema invite.** `tb_temp_bu_user.business_unit_id` is stored as `VarChar(255)` because inviter/invitee tenants may resolve it differently.
- **Hard-delete is allowed** (no transactional FK targets) but soft-delete is preferred to preserve audit.

---

## 5. Data Model (Dev)

Source: platform schema.

### 5.1 `tb_user_tb_business_unit`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String? @db.Uuid` | Yes | FK to `tb_user`. |
| `business_unit_id` | `String? @db.Uuid` | Yes | FK to `tb_business_unit`. |
| `role` | `enum_user_business_unit_role` | No | Default `user`. `admin` or `user`. |
| `is_default` | `Boolean?` | Yes | Default `false`. Marks the BU the user lands in. |
| `is_active` | `Boolean?` | Yes | Default `true`. Disables access without unlinking. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, business_unit_id, deleted_at])`. FKs `onDelete: NoAction`. `enum_user_business_unit_role`: `admin`, `user`.

### 5.2 `tb_temp_bu_user`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `business_unit_id` | `String @db.VarChar(255)` | No | Target BU id (stored as string for cross-tenant resolution). |
| `email` | `String @db.VarChar(255)` | No | Invited email. |
| `role` | `String @db.VarChar(50)` | No | Intended role. |
| `created_at` | `DateTime @db.Timestamptz(6)` | No | Default `now()`. Pairs with TTL for stale-invite expiry. |

**Constraints:** none. Paired with a short-lived `tb_shot_url` invitation token.

## 6. Business Rules

- **Uniqueness.** At most one active `(user_id, business_unit_id)` row per user — re-inviting toggles `is_active`.
- **Default BU invariant.** At most one row per user with `is_default = true` (app-enforced).
- **Role semantics.** `admin` = BU-wide admin capability without separate app role; `user` = default, relies on app-role assignments.
- **Invitation lifecycle.** `tb_temp_bu_user` + `tb_shot_url` = one invitation. Accept upserts membership and removes staging rows.
- **Inactivation.** `is_active = false` revokes access on next request; app-role assignments untouched.

## 7. Cross-References

- [[access-control/user]] — the user side of the membership.
- [[master-data/business-unit]] — the BU side.
- [[access-control/application-role]] — BU-scoped; prerequisite check.
- All transactional modules — every request resolves the active BU through this table.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_tb_business_unit` (lines ~511-532), `tb_temp_bu_user` (lines ~548-554), `enum_user_business_unit_role` (lines ~582-585).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/cluster/`.
