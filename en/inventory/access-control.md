---
title: Access Control
description: Users, roles, permissions, and multi-business-unit access.
published: true
date: 2026-06-09T16:28:56.000Z
tags: access-control, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Access Control

> **At a Glance**
> **Module purpose:** Resolves "may user X perform action Y on resource Z" for every transactional request &nbsp;·&nbsp; **Audience:** Sysadmin, Security Officer, BU Admin &nbsp;·&nbsp; **Key entities/tables:** `tb_user`, `tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_department_user`, `tb_user_location` &nbsp;·&nbsp; **Sub-pages:** 6

![Access Control screen](/screenshots/access-control/application-role.png)

![Access Control detail screen](/screenshots/access-control/application-role-detail.png)

## 1. Overview

Access Control is the umbrella for **who can do what, where**. It binds five entities into a single authorisation pipeline. [access-control/user](/en/inventory/access-control/user) is the identity (account, profile, sessions — passwords are externalized). [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) declares which business units a user may enter at all. [access-control/application-role](/en/inventory/access-control/application-role) is the named bundle of [access-control/permission](/en/inventory/access-control/permission) atoms assigned to a user within a BU. [access-control/user-location](/en/inventory/access-control/user-location) then narrows the user's row-level scope inside the tenant to specific [master-data/location](/en/inventory/master-data/location)s.

Every transactional action in the system — submitting a PR, approving a GRN, posting an inventory adjustment, running a count — resolves through this pipeline. The runtime question "may user X perform action Y on resource Z" decomposes to: does X have an active `tb_user_tb_business_unit` row for the active BU; does X hold an `tb_application_role` in that BU whose `tb_application_role_tb_permission` set includes `(Z, Y)`; and (for location-scoped resources) is the target row inside X's `tb_user_location` set.

Four of the five entity groups live in the **platform schema** (shared across tenants — `tb_user`, `tb_user_profile`, `tb_user_login_session`, `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_temp_bu_user`, `enum_user_business_unit_role`). The fifth — `tb_user_location` — lives in the **tenant schema** because it joins users to tenant-side locations.

## 2. Audience

Sysadmin owns the configuration end-to-end. Security Officer audits credentials, sessions, and role assignments. BU-level user invitation may be delegated to a BU admin (a user whose `tb_user_tb_business_unit.role = admin`).

## 3. Entity List

| Entity | Purpose | Managed by |
| ------ | ------- | ---------- |
| [user](/en/inventory/access-control/user) | Account, profile, and login session — the identity layer (passwords externalized) | Sysadmin / Security Officer |
| [application-role](/en/inventory/access-control/application-role) | BU-scoped named role + role-permission and user-role joins | Sysadmin |
| [permission](/en/inventory/access-control/permission) | Atomic `(resource, action)` permission catalogue | Sysadmin (seed-managed) |
| [business-unit-user](/en/inventory/access-control/business-unit-user) | Per-BU access membership + email-invitation staging | Sysadmin / BU Admin |
| [department-user](/en/inventory/access-control/department-user) | User↔department membership + Head of Department (HOD) designation for approval routing | Sysadmin / Product Admin |
| [user-location](/en/inventory/access-control/user-location) | Tenant-side per-user location scope | Sysadmin / BU Admin |

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

- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user`, `tb_user_profile`, `tb_user_login_session`, `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_temp_bu_user`, and the supporting `enum_platform_role`, `enum_token_type`, `enum_user_business_unit_role`.
- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_user_location`.
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — describes how workflow-stage role types (requester / purchaser / approver / reviewer) layer on top of the application-role permission grants documented here.
- **Design spec:** `.specs/2026-05-16-master-config-design.md`.
- **Plan:** `.specs/2026-05-16-master-config-plan.md`.
