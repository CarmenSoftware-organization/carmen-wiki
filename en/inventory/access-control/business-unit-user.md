---
title: Business Unit User
description: The per-business-unit membership pivot — declares which users may access which BUs, plus a designed-but-unimplemented invitation staging table.
published: true
date: 2026-07-15T23:46:09.000Z
tags: access-control, business-unit-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Business Unit User

> **At a Glance**
> **Owner:** Sysadmin / BU Admin &nbsp;·&nbsp; **Table:** `tb_user_tb_business_unit` (+ `tb_temp_bu_user`) &nbsp;·&nbsp; **Used by:** every authenticated request (BU resolution) &nbsp;·&nbsp; The multi-tenant access pivot — declares which users may operate inside which BUs.

## 1. What & Who

`business-unit-user` is the **multi-tenant access pivot**: it declares that a given [access-control/user](/en/inventory/access-control/user) is allowed to operate inside a given [master-data/business-unit](/en/inventory/master-data/business-unit), and assigns a coarse BU-level role (`admin` or `user`). Without an active row here, a user cannot see the BU in their BU selector regardless of which [access-control/application-role](/en/inventory/access-control/application-role)s exist for that BU. With a row, the user can switch into the BU (`POST /api/business-units/default`); the backend then resolves that user's per-BU grants into the `x-bu-datas` header that [access-control/permission](/en/inventory/access-control/permission)'s `PermissionGuard` reads on subsequent requests. (`x-app-id` is an unrelated header — it identifies the calling *client application* against a separate allowlist, not the active BU or user; see [access-control/permission](/en/inventory/access-control/permission) §1.1.)

A companion table, `tb_temp_bu_user`, was designed to stage **email-based invitations** before the recipient signs up (BU id, email, role), but no backend code creates, reads, or consumes it today — see Edge Cases. The invite flow that actually exists (`/api/auth/invite-user`) only issues a generic platform-registration token with no BU or role attached.

**Maintained by** Sysadmin and BU admins. **Read by** every authenticated request.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Grant a user access to a BU | No screen in `carmen-inventory-frontend-react` exposes this | BU-membership admin CRUD (grant/revoke, set per-BU `role`) is not implemented in this frontend; the inventory app only offers self-service views (below) |
| Invite a new person by email | `POST /api/auth/invite-user` (`{ "email": ... }`) — generic platform sign-up, not surfaced as a UI screen in this frontend | Creates a `tb_shot_url` registration token only; does **not** write `tb_temp_bu_user` or attach a target BU/role at invite time |
| Switch active BU / set default | Navbar BU switcher (`components/navbar/bu-switcher.tsx`) → click a BU | One action, not two steps — clicking immediately calls `POST /api/business-units/default` and flips `is_default` on the selected row (optimistic UI update in `hooks/use-switch-bu.ts`); there's no separate "Make default" control |
| View own BU memberships | `/profile` → Business Units section (`routes/profile/bu-section.tsx`) | Read view + BU logo/avatar upload for BUs the user administers; not a membership-grant screen |
| Suspend access without removing | Toggle `is_active = false` (schema-level; no admin UI in this frontend) | User loses access on next request; role assignments preserved |
| Revoke access permanently | Soft-delete the row (schema-level; no admin UI in this frontend) | Membership filter requires `deleted_at IS NULL` |
| Promote to BU admin | Set `role = admin` (schema-level; no admin UI in this frontend) | Confirmed functionally significant: `PermissionGuard` treats `tb_user_tb_business_unit.role = admin` as a full RBAC bypass ("god-mode") for that BU — see [access-control/permission](/en/inventory/access-control/permission) |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| BU missing from switcher after grant | Cached session | Refresh / re-login |
| "User already exists" (409) on invite | `/api/auth/invite-user` found an existing `tb_user` with that email (`auth.service.ts` `inviteUser`) | Grant BU access to the existing user instead of re-inviting |
| Multiple `is_default = true` rows | Application invariant violated | Run repair script; should be at most one per user |
| Invitation link 404 | `tb_shot_url` token expired (`INVITATION_LIMIT_HOURS`, default 1 hour) | Re-send via `/api/auth/invite-user` |

## 4. Edge Cases

- **`tb_temp_bu_user` is schema-only — no code path writes or reads it.** A repo-wide search of `carmen-turborepo-backend-v2` found zero references to `tb_temp_bu_user` outside the Prisma schema itself. The table models a BU-scoped invitation stage (business_unit_id + email + role) that was designed but never implemented; the real invite endpoint (`/api/auth/invite-user`) only creates a generic `tb_shot_url` registration token with no BU or role attached. Treat the fields below as a schema reference, not a live flow.
- **Role = `admin`** grants BU-wide RBAC bypass (verified via `PermissionGuard`'s admin check) without needing a separate application role.
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

### 5.2 `tb_temp_bu_user` (schema-only — no code references it; see Edge Cases)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `business_unit_id` | `String @db.VarChar(255)` | No | Target BU id (stored as string for cross-tenant resolution). |
| `email` | `String @db.VarChar(255)` | No | Invited email. |
| `role` | `String @db.VarChar(50)` | No | Intended role. |
| `created_at` | `DateTime @db.Timestamptz(6)` | No | Default `now()`. Pairs with TTL for stale-invite expiry. |

**Constraints:** none. Designed to pair with a short-lived `tb_shot_url` invitation token, but no service currently creates, reads, or consumes a row here.

## 6. Business Rules

- **Uniqueness.** At most one active `(user_id, business_unit_id)` row per user — re-inviting toggles `is_active`.
- **Default BU invariant.** At most one row per user with `is_default = true` (app-enforced — verified in `hooks/use-switch-bu.ts`, which flips `is_default` on the target and implicitly clears it elsewhere on refetch).
- **Role semantics.** `admin` = BU-wide RBAC bypass without a separate app role (verified in `PermissionGuard`); `user` = default, relies on app-role assignments.
- **The real invite flow bypasses `tb_temp_bu_user` entirely.** `/api/auth/invite-user` takes only an email, checks it isn't already a `tb_user`, and issues a `tb_shot_url` registration token — no `business_unit_id` or `role` is captured at invite time.
- **Inactivation.** `is_active = false` revokes access on next request; app-role assignments untouched.

## 7. Cross-References

- [access-control/user](/en/inventory/access-control/user) — the user side of the membership.
- [master-data/business-unit](/en/inventory/master-data/business-unit) — the BU side.
- [access-control/application-role](/en/inventory/access-control/application-role) — BU-scoped; prerequisite check.
- [access-control/permission](/en/inventory/access-control/permission) — `PermissionGuard`'s admin-role bypass.
- All transactional modules — every request resolves the active BU through this table.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_tb_business_unit` (line 627), `tb_temp_bu_user` (line 666), `enum_user_business_unit_role` (line 691).
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (`inviteUser`, `changePassword`); `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/auth.controller.ts` (`POST /api/auth/invite-user`).
- **Frontend:** `../carmen-inventory-frontend-react/components/navbar/bu-switcher.tsx` + `hooks/use-switch-bu.ts` (switch/default); `../carmen-inventory-frontend-react/routes/profile/bu-section.tsx` (self-view). No BU-membership admin CRUD screen exists in this frontend.
