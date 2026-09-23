---
title: Business Unit User
description: The per-BU membership pivot (tb_user_tb_business_unit) plus the cluster-scoped invitation flow (tb_user_invitation + _business_unit) that replaced the dropped tb_temp_bu_user on 2026-08-05; /api/auth/invite-user is gone.
published: true
date: 2026-09-23T10:06:26.000Z
tags: access-control, business-unit-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Business Unit User

> **At a Glance**
> **Owner:** Platform / cluster admin (invite), user (accept), Sysadmin (membership rows) &nbsp;·&nbsp; **Tables:** `tb_user_tb_business_unit` (membership) + `tb_user_invitation` / `tb_user_invitation_business_unit` (invitations — **replaced `tb_temp_bu_user`, dropped 2026-08-05**) &nbsp;·&nbsp; **Endpoints:** `POST /api/business-units/default` (switch), `GET /api/business-units` (current), `api/invitations/{mine,:token,:token/accept,:token/accept-with-signup,:token/decline}`, Platform `api-system/clusters/:cluster_id/invitations` (create / list / revoke / resend) &nbsp;·&nbsp; **Used by:** every authenticated request (BU resolution) &nbsp;·&nbsp; The multi-tenant access pivot — declares which users may operate inside which BUs.

![Business Unit User screen](/screenshots/access-control/business-unit-user.png)

## Implementation status (re-verified 2026-09-22)

The 2026-07-15 finding ("`tb_temp_bu_user` is schema-only; `/api/auth/invite-user` issues a bare registration token") is obsolete on both counts:

- **`tb_temp_bu_user` was dropped** (platform migration `20260805100000_drop_temp_bu_user`) and **`/api/auth/invite-user` was removed** (BE `7f93ce6ad`, 2026-08-05, "remove the invite flow that never worked").
- **A real invitation flow replaced them** (migration `20260805000000_user_invitation`; BE `3592a420e` 2026-08-05, `2945a4d04` 2026-08-08): `tb_user_invitation` is a cluster-scoped, **email-bound** offer (`cluster_id`, `email`, `token_hash`, `cluster_role`, `status` `pending|accepted|declined|revoked`, `invited_by_id`, `expires_at`, `accepted_at`/`accepted_user_id`, `declined_*`, `revoked_*`), with one `tb_user_invitation_business_unit` row per BU the invitation grants (`business_unit_id`, `role` = `enum_user_business_unit_role`, `is_default`). A partial unique index enforces one *pending* invitation per `(cluster, email)` — SQL only, Prisma cannot express it. `expired` is deliberately not a stored status; it is derived from `expires_at`.
- **Who does what:** a cluster admin creates / lists / revokes / resends from the Platform (`api-system/clusters/:cluster_id/invitations`, `platform_cluster-invitations.controller.ts:74-266`, platform permissions); the recipient reads `GET api/invitations/:token` and `GET api/invitations/mine` and answers with `POST …/accept`, `POST …/accept-with-signup` (public — `@IgnoreGuards(KeycloakGuard)`, `invitations.controller.ts:107,206` — for an address with no account yet) or `POST …/decline`. On accept, `user-invitation.service.ts` (micro-cluster) creates the cluster membership and one `tb_user_tb_business_unit` row per invited BU with the invited `role` and `is_default` (`:480-500`, `:577-578`). Seats are counted against the **cluster** pool (`v_business_unit_seat`, `SEAT_LIMIT_EXCEEDED`; pending invitations are reported alongside `used`/`cap` in `GET /api/license` `seat.pending_invites`).
- The membership table itself is unchanged; the `admin` RBAC bypass in `PermissionGuard` still holds. There is still **no BU-membership admin CRUD screen in `carmen-inventory-frontend-react`** — grant/revoke and the invitation UI live in the Platform SPA (see the Platform book).

## 1. What & Who

`business-unit-user` is the **multi-tenant access pivot**: it declares that a given [access-control/user](/en/inventory/access-control/user) is allowed to operate inside a given [master-data/business-unit](/en/inventory/master-data/business-unit), and assigns a coarse BU-level role (`admin` or `user`). Without an active row here, a user cannot see the BU in their BU selector regardless of which [access-control/application-role](/en/inventory/access-control/application-role)s exist for that BU. With a row, the user can switch into the BU (`POST /api/business-units/default`); the backend then resolves that user's per-BU grants into the `x-bu-datas` header that [access-control/permission](/en/inventory/access-control/permission)'s `PermissionGuard` reads on subsequent requests. (`x-app-id` is an unrelated header — it identifies the calling *client application* against a separate allowlist, not the active BU or user; see [access-control/permission](/en/inventory/access-control/permission) §1.1.) Since 2026-08 a third check runs per request: the BU's **licence** must include the route's feature (`LicenseInterceptor`), read by the client from `GET /api/license` rather than the profile.

Rows are created in three ways: by accepting a cluster invitation (the normal path, above), by the Platform's BU/user management, or by seed. **Maintained by** cluster admins (Platform) and Sysadmin. **Read by** every authenticated request.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Grant a user access to a BU | No screen in `carmen-inventory-frontend-react` exposes this | Invite them (below) or use the Platform SPA's BU / user management; the inventory app only offers self-service views |
| Invite a new person by email | Platform SPA → cluster → Invitations (`POST api-system/clusters/:cluster_id/invitations` with `email`, `cluster_role`, `business_units[{ business_unit_id, role, is_default }]`) | Writes `tb_user_invitation` + `_business_unit`; the recipient gets a tokenised link; `resend` and `DELETE` (revoke) exist |
| Accept an invitation | Link → `GET api/invitations/:token` → `POST …/accept` (signed in) or `…/accept-with-signup` (no account yet — creates the account and accepts in one step) | Creates the cluster membership and the `tb_user_tb_business_unit` rows with the invited `role` / `is_default`; `INVITATION_ADDRESS_CONFLICT` if signed in as a different address |
| See my pending invitations | `GET api/invitations/mine` | Bound to the caller's email |
| Switch active BU / set default | Navbar BU switcher (`components/navbar/bu-switcher.tsx`) → click a BU | One action, not two steps — clicking immediately calls `POST /api/business-units/default` and flips `is_default` on the selected row (optimistic UI update in `hooks/use-switch-bu.ts`); there's no separate "Make default" control |
| View own BU memberships | `/profile` → Business Units section (`routes/profile/bu-section.tsx`) | Read view + BU logo/avatar upload for BUs the user administers; not a membership-grant screen |
| Suspend access without removing | Toggle `is_active = false` (schema-level; no admin UI in this frontend) | User loses access on next request; role assignments preserved |
| Revoke access permanently | Soft-delete the row (schema-level; no admin UI in this frontend) | Membership filter requires `deleted_at IS NULL` |
| Promote to BU admin | Set `role = admin` (schema-level; no admin UI in this frontend) | Confirmed functionally significant: `PermissionGuard` treats `tb_user_tb_business_unit.role = admin` as a full RBAC bypass ("god-mode") for that BU — see [access-control/permission](/en/inventory/access-control/permission) |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| BU missing from switcher after grant | Cached session | Refresh / re-login |
| Duplicate pending invitation for the same `(cluster, email)` | Partial unique index (SQL only) | Revoke or resend the existing one instead |
| `INVITATION_ADDRESS_CONFLICT` | Accepting while signed in as an account whose email differs from the invited address | Sign in with the invited address, or use `accept-with-signup` |
| Invitation shows as expired | `expires_at` passed (derived, not stored) | Cluster admin → **Resend** |
| `SEAT_LIMIT_EXCEEDED` on accept | Cluster seat pool (`cap`) already used, counting pending invitations | Buy seats or revoke unused invitations |
| Multiple `is_default = true` rows | Application invariant violated | Run repair script; should be at most one per user |

## 4. Edge Cases

- **`tb_temp_bu_user` no longer exists** (dropped 2026-08-05). The invitation stage it was designed for is now `tb_user_invitation` + `tb_user_invitation_business_unit` — cluster-scoped rather than BU-scoped, so one invitation can grant several BUs at once and carries a `cluster_role` too.
- **Invitations are email-bound, not user-bound**, so an address without an account can be invited; `accept-with-signup` creates the account. The `x-app-id` allowlist still applies to the public accept routes.
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

### 5.2 `tb_user_invitation` (platform; replaces the dropped `tb_temp_bu_user`)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `cluster_id` | `String @db.Uuid` | No | Cluster the invitation belongs to. |
| `email` | `String @db.VarChar(255)` | No | Invited address (the invitation is bound to it, not to a user id). |
| `token_hash` | `String @db.VarChar` | No | Hash of the link token. |
| `cluster_role` | `enum_cluster_user_role` | No | Default `user`. Cluster-level role granted on accept. |
| `status` | `enum_user_invitation_status` | No | `pending` (default), `accepted`, `declined`, `revoked`. `expired` is derived from `expires_at`. |
| `invited_by_id` | `String @db.Uuid` | No | Inviting admin. |
| `expires_at` | `DateTime @db.Timestamptz(6)` | No | Link expiry. |
| `accepted_at` / `accepted_user_id`, `declined_at` / `declined_user_id`, `revoked_at` / `revoked_by_id` | — | Yes | Outcome stamps. |
| `doc_version` | `Int` | No | Default `0`. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** partial unique index "one pending invitation per `(cluster_id, email)`" in migration SQL only (`20260805000000_user_invitation`).

### 5.3 `tb_user_invitation_business_unit`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_invitation_id` | `String @db.Uuid` | No | Parent invitation. |
| `business_unit_id` | `String @db.Uuid` | No | BU to grant on accept. |
| `role` | `enum_user_business_unit_role` | No | Default `user`. Becomes `tb_user_tb_business_unit.role`. |
| `is_default` | `Boolean` | No | Default `false`. Becomes `tb_user_tb_business_unit.is_default`. |
| `doc_version` + audit columns | — | Mixed | Standard. |

## 6. Business Rules

- **Uniqueness.** At most one active `(user_id, business_unit_id)` row per user — re-inviting toggles `is_active`.
- **Default BU invariant.** At most one row per user with `is_default = true` (app-enforced — verified in `hooks/use-switch-bu.ts`, which flips `is_default` on the target and implicitly clears it elsewhere on refetch).
- **Role semantics.** `admin` = BU-wide RBAC bypass without a separate app role (verified in `PermissionGuard`); `user` = default, relies on app-role assignments.
- **Invitations carry the BU grants.** `role` and `is_default` per BU are captured at invite time (`tb_user_invitation_business_unit`) and materialised into `tb_user_tb_business_unit` on accept; one pending invitation per `(cluster, email)`.
- **Seats are a cluster pool.** Accepting is refused with `SEAT_LIMIT_EXCEEDED` when the cluster's `cap` is reached; pending invitations count towards it.
- **Inactivation.** `is_active = false` revokes access on next request; app-role assignments untouched.

## 7. Cross-References

- [access-control/user](/en/inventory/access-control/user) — the user side of the membership.
- [master-data/business-unit](/en/inventory/master-data/business-unit) — the BU side.
- [access-control/application-role](/en/inventory/access-control/application-role) — BU-scoped; prerequisite check.
- [access-control/permission](/en/inventory/access-control/permission) — `PermissionGuard`'s admin-role bypass.
- All transactional modules — every request resolves the active BU through this table.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_tb_business_unit`, `tb_user_invitation`, `tb_user_invitation_business_unit`, `enum_user_business_unit_role`, `enum_user_invitation_status`; migrations `20260805000000_user_invitation`, `20260805100000_drop_temp_bu_user`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/invitations/invitations.controller.ts` (`mine` `:70`, `:token` `:106`, `accept` `:148`, `accept-with-signup` `:201`, `decline` `:257`); `apps/backend-gateway/src/platform/platform_cluster-invitations/` (`POST` `:74`, `GET` `:147`, `DELETE :id` `:202`, `POST :id/resend` `:266`); `apps/micro-cluster/src/cluster/user-invitation/user-invitation.service.ts`; `apps/backend-gateway/src/application/user-business-units/user-business-units.controller.ts` (`POST default`, `GET`, `PUT`, `PATCH`).
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/platform/cluster-invitations/`, `user-management/`.
- **Frontend:** `../carmen-inventory-frontend-react/components/navbar/bu-switcher.tsx` + `hooks/use-switch-bu.ts` (switch/default); `../carmen-inventory-frontend-react/routes/profile/bu-section.tsx` (self-view). No BU-membership admin CRUD or invitation screen exists in this frontend — see the Platform book.
