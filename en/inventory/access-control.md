---
title: Access Control
description: Users, roles, permissions, and multi-business-unit access. Re-verified 2026-09-22 — tb_location_user (renamed), tb_user_invitation replaces tb_temp_bu_user, user access edited via PATCH /api/config/:bu_code/users/:user_id.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: access-control, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Access Control

> **At a Glance**
> **Module purpose:** Resolves "may user X perform action Y on resource Z" for every transactional request &nbsp;·&nbsp; **Audience:** Sysadmin, Security Officer, BU Admin &nbsp;·&nbsp; **Key entities/tables:** `tb_user`, `tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_user_invitation` (+ `_business_unit`), `tb_department_user`, `tb_location_user` (renamed from `tb_user_location` on 2026-09-04) &nbsp;·&nbsp; **Sub-pages:** 6 &nbsp;·&nbsp; **Re-verified 2026-09-22.**

## Changes since 2026-07-29 (verified 2026-09-22)

| Change | Date | Source | Wiki page |
|---|---|---|---|
| `tb_user_location` → `tb_location_user` (tenant), together with `tb_shelf` → `tb_location_shelf` | 2026-09-04 | tenant migration `20260904131500_rename_shelf_and_user_location`; BE `d49a81b34` | [user-location](/en/inventory/access-control/user-location) |
| User access edited in one request: `GET` / `PATCH /api/config/:bu_code/users/:user_id` — roles and locations as `{ add[], remove[] }`, department as a single `department_id`; response is one `UserDetail` (`user`, `application_roles[]`, `locations[]`, `department`) | 2026-09-04 / 2026-09-07 | BE `b9eb20818`, `9a91d7f32`, `671288897`; FE `a5038c84`, `39ae1bba`; Bruno `config/users/{GET-get-access,PATCH-patch-access}` | [user](/en/inventory/access-control/user), [user-location](/en/inventory/access-control/user-location), [department-user](/en/inventory/access-control/department-user) |
| User × role matrix `GET /api/config/:bu_code/user-application-roles` (rows `user_id`, `bu_role`, `is_active`, `is_bu_active`, `role_ids[]`; summary `roles[]`) — backs the user list's Print / Export | 2026-08-20 | BE `7a2390f11`; FE `ae37df84` (`use-user-role-report.ts`) | [user](/en/inventory/access-control/user) |
| `GET /api/:bu_code/users` includes each user's `roles[]` | 2026-08-20 | BE `ae8d1cd1e` | [user](/en/inventory/access-control/user) |
| Application-role list returns `permissions: { count }` (+ `audit`); detail returns the full permission catalog with the role's grants marked | 2026-09-07 | BE `d911ad988`, `8162d568c`; FE `3d339913` | [application-role](/en/inventory/access-control/application-role) |
| Role screen: module-level permissions (resource without a dot — 11 of them) were dropped by the picker and soft-deleted permissions were still shown; fixed. Role **Print** produces a per-module grant summary | 2026-08-31 / 2026-08-20 | FE `bad71662`, `efdc52ba` | [application-role](/en/inventory/access-control/application-role), [permission](/en/inventory/access-control/permission) |
| Frontend ghost permission keys (`system_configuration.*`) replaced by the real `tb_permission` resources; `system_admin.query_dataset` removed from the catalog | 2026-09-21 | FE `b9e2de5f`, `91b2b274`, `02bfff7a`; BE `7bebddaa7` | [permission](/en/inventory/access-control/permission) |
| Permission resource `system_admin.period` → `system_admin.inventory_period` | 2026-09-16 | platform migration `20260916140000_rename_period_to_inventory_period` | [permission](/en/inventory/access-control/permission) |
| `tb_temp_bu_user` **dropped**; invitations are now `tb_user_invitation` + `tb_user_invitation_business_unit` (cluster-scoped, email-bound, `pending/accepted/declined/revoked`), created from the Platform (`api-system/clusters/:cluster_id/invitations`) and accepted through `api/invitations/:token/accept` (or `…/accept-with-signup` for an address with no account); `/api/auth/invite-user` removed ("the invite flow that never worked") | 2026-08-05 → 2026-08-08 | platform migrations `20260805000000_user_invitation`, `20260805100000_drop_temp_bu_user`; BE `7f93ce6ad`, `3592a420e`, `2945a4d04` | [business-unit-user](/en/inventory/access-control/business-unit-user) |
| `tb_user` gains `email_verified_at`, `email_verification_token_hash`, `email_verification_expires_at`; live-account uniqueness of `email` / `username` is now two **partial unique indexes** (`lower(email)` / `lower(username)` where `deleted_at IS NULL`) — the Prisma `@@unique([username, deleted_at])` was dropped; auth adds `signup-request`, `signup-token/verify`, `verify-email`, `resend-verification` | 2026-08-04 → 2026-08-08 | platform migrations `20260804000000_user_email_verification`, `20260806000000_user_active_identifier_unique`, `20260808100000_signup_verification` | [user](/en/inventory/access-control/user) |
| Licence block removed from `GET /api/user/profile` → `GET /api/license` | 2026-09-09 | BE `dc5623a05` | [user](/en/inventory/access-control/user) |
| Entity references in config/master responses serialised as nested objects (`business_unit: { id }` on the role list; `department_users[].user: { id }`, `hod_users[].user: { id }` on departments) | 2026-09-17 | BE `5d64f5dfd`; FE `dbb93361`, `b55294b3` | [application-role](/en/inventory/access-control/application-role), [department-user](/en/inventory/access-control/department-user) |

![Access Control screen](/screenshots/access-control/application-role.png)

![Access Control detail screen](/screenshots/access-control/application-role-detail.png)

## 1. Overview

Access Control is the umbrella for **who can do what, where**. It binds five entities into a single authorisation pipeline. [access-control/user](/en/inventory/access-control/user) is the identity (account, profile, sessions — passwords are externalized). [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) declares which business units a user may enter at all. [access-control/application-role](/en/inventory/access-control/application-role) is the named bundle of [access-control/permission](/en/inventory/access-control/permission) atoms assigned to a user within a BU. [access-control/user-location](/en/inventory/access-control/user-location) then narrows the user's row-level scope inside the tenant to specific [master-data/location](/en/inventory/master-data/location)s.

Every transactional action in the system — submitting a PR, approving a GRN, posting an inventory adjustment, running a count — resolves through this pipeline. The runtime question "may user X perform action Y on resource Z" decomposes to: does X have an active `tb_user_tb_business_unit` row for the active BU; does the BU's licence include the feature the route maps to (`LicenseInterceptor`, since 2026-08); does X hold an `tb_application_role` in that BU whose `tb_application_role_tb_permission` set includes `(Z, Y)` — checked only on routes that declare `@Permission`, see [access-control/permission](/en/inventory/access-control/permission); and (for location-scoped resources) is the target row inside X's `tb_location_user` set.

Four of the five entity groups live in the **platform schema** (shared across tenants — `tb_user`, `tb_user_profile`, `tb_user_login_session`, `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_user_invitation`, `tb_user_invitation_business_unit`, `enum_user_business_unit_role`, `enum_user_invitation_status`). The fifth — `tb_location_user` (renamed from `tb_user_location` on 2026-09-04) — lives in the **tenant schema** because it joins users to tenant-side locations; `tb_department_user` is tenant-side for the same reason.

## 2. Audience

Sysadmin owns the configuration end-to-end. Security Officer audits credentials, sessions, and role assignments. BU-level user invitation may be delegated to a BU admin (a user whose `tb_user_tb_business_unit.role = admin`).

## 3. Entity List

| Entity | Purpose | Managed by |
| ------ | ------- | ---------- |
| [user](/en/inventory/access-control/user) | Account, profile, and login session — the identity layer (passwords externalized) | Sysadmin / Security Officer |
| [application-role](/en/inventory/access-control/application-role) | BU-scoped named role + role-permission and user-role joins | Sysadmin |
| [permission](/en/inventory/access-control/permission) | Atomic `(resource, action)` permission catalogue | Sysadmin (seed-managed) |
| [business-unit-user](/en/inventory/access-control/business-unit-user) | Per-BU access membership + cluster-scoped email invitations (`tb_user_invitation*`, replacing the dropped `tb_temp_bu_user`) | Platform / cluster admin (invite), user (accept) |
| [department-user](/en/inventory/access-control/department-user) | User↔department membership + Head of Department (HOD) designation for approval routing; now also editable from the user side via `PATCH …/users/:user_id { department_id }` | Sysadmin / Product Admin |
| [user-location](/en/inventory/access-control/user-location) | Tenant-side per-user location scope (`tb_location_user`) | Sysadmin / BU Admin |

## 4. Cross-Module Dependencies

- **All transactional modules** depend on [access-control/user](/en/inventory/access-control/user), [access-control/application-role](/en/inventory/access-control/application-role), [access-control/permission](/en/inventory/access-control/permission), and [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) — every authenticated request resolves through this chain before any module-specific logic runs. Listing each module here would just repeat the same four entities, so the rule is: every action in [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [store-requisition](/en/inventory/store-requisition), [inventory](/en/inventory/inventory), [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), [costing](/en/inventory/costing), [vendor-pricelist](/en/inventory/vendor-pricelist), [product](/en/inventory/product), and [recipe](/en/inventory/recipe) is RBAC-gated.
- [inventory](/en/inventory/inventory) additionally consults [access-control/user-location](/en/inventory/access-control/user-location) for row-level filtering of inventory listings and movement screens.
- [store-requisition](/en/inventory/store-requisition) additionally consults [access-control/user-location](/en/inventory/access-control/user-location) for location-bound issuing.
- [physical-count](/en/inventory/physical-count) additionally consults [access-control/user-location](/en/inventory/access-control/user-location) so storekeepers only see and count their own areas.
- [spot-check](/en/inventory/spot-check) additionally consults [access-control/user-location](/en/inventory/access-control/user-location) for the same scoping reason as physical-count.
- [master-data/business-unit](/en/inventory/master-data/business-unit) is the scope-anchor for [access-control/application-role](/en/inventory/access-control/application-role) (every role is owned by a BU) and for [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) (every membership references a BU).
- [master-data/location](/en/inventory/master-data/location) is the scope target for [access-control/user-location](/en/inventory/access-control/user-location).
- [reporting-audit](/en/inventory/reporting-audit) consumes the audit columns and role / membership change events surfaced by every entity in this umbrella.

## 5. References

- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user`, `tb_user_profile`, `tb_user_login_session`, `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_user_invitation`, `tb_user_invitation_business_unit`, and the supporting `enum_token_type`, `enum_user_business_unit_role`, `enum_user_invitation_status`. `tb_temp_bu_user` was dropped on 2026-08-05 (`20260805100000_drop_temp_bu_user`). There is no `enum_platform_role` — it was dropped 2026-06-10 in favor of the relational `tb_platform_role` system (Carmen Platform admin scope; see [access-control/user](/en/inventory/access-control/user) Edge Cases).
- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location_user`, `tb_department_user`.
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/{config_users,config_user-application-roles,config_application-roles,config_permissions,config_department-users,config_locations-users,config_user-locations}/`, `apps/backend-gateway/src/application/{user,user-business-units,user-locations,invitations}/`, `apps/backend-gateway/src/platform/platform_cluster-invitations/`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/{users,user-application-roles,application-roles,permissions,department-user,locations-user,user-location}/`, `user-management/user/`.
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — describes how workflow-stage role types (requester / purchaser / approver / reviewer) layer on top of the application-role permission grants documented here. Frozen 2026-04-27; the actual `enum_stage_role` is `create / approve / purchase / issue / view_only` (see [system-config/workflow](/en/inventory/system-config/workflow)).
- **Design spec:** `.specs/2026-05-16-master-config-design.md`.
- **Plan:** `.specs/2026-05-16-master-config-plan.md`.
