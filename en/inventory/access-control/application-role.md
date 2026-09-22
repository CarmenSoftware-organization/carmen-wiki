---
title: Application Role
description: Per-business-unit role definitions plus the role→permission and user→role join tables — the heart of tenant RBAC. List returns a permission count, detail the full catalog; role print; picker fix for module-level permissions.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: access-control, application-role, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Application Role

> **At a Glance**
> **Owner:** Sysadmin (per BU) &nbsp;·&nbsp; **Table:** `tb_application_role` (+ `tb_application_role_tb_permission`, `tb_user_tb_application_role`) &nbsp;·&nbsp; **Screen:** `/system-admin/role` (+ `/new`, `/:id`) — permission `system_admin.role.view`, licence `system_admin.role` &nbsp;·&nbsp; **Endpoint:** `api/config/:bu_code/application-roles` (`KeycloakGuard` only — **no `AppIdGuard` and no `@Permission` on any of its five routes**, re-verified 2026-09-22) &nbsp;·&nbsp; **Used by:** every transactional module's permission check &nbsp;·&nbsp; Named bundles of permissions assigned to users inside a BU.

## Implementation status (re-verified 2026-09-22)

- **List vs detail payloads split (BE `d911ad988`, 2026-09-07).** `GET …/application-roles` returns `permissions: { count }` per role plus `audit` (`ApplicationRoleResponseDto`, `swagger/response.ts:38-66`); `GET …/application-roles/:id` returns the **whole permission catalog** with the role's grants marked (`ApplicationRoleDetailResponseDto`, `:91-105`). The FE types mirror this (`types/role.ts`: `Role.permissions: { count }`, `RoleDetail.permissions: RolePermission[]`; FE `3d339913`). Since the 2026-09-17 serializer pass the list row carries `business_unit: { id }` instead of a flat `business_unit_id` (BE `5d64f5dfd` — list only; the detail DTO has no such field).
- **Create / update payloads:** `CreateRoleDto { name, description?, permissions: { add: string[] } }`, `UpdateRoleDto { …, doc_version, permissions: { add: string[], remove: string[] } }` (`types/role.ts:35-44`).
- **Role screen rebuilt (FE `aad79674`, 2026-08-20).** `permission-matrix.tsx` was deleted; the form is now `role-form.tsx` + `role-form-hero.tsx` + `permission-picker.tsx` (`permission-catalog.ts` groups the catalog category → resource → action; actions are Toggle pills, `4c28bcf0`). Two picker bugs fixed on 2026-08-31 (`bad71662`): permissions whose `resource` has no dot — the **module-level** grants `procurement`, `configuration`, `inventory_management`, `dashboard`, `report`, `system_admin`, … (11 of them) — were skipped by `if (dot === -1) continue;` and could never be granted from the UI; and soft-deleted permissions returned with `audit.deleted` were still rendered. Module-level rows now appear first in each category as "Module access" (`MODULE_RESOURCE_KEY`).
- **Print (FE `efdc52ba`, 2026-08-20).** `use-role-print.ts` renders a per-module summary of granted permissions (same order and labels as the picker) with BU / printed-by / printed-at header, through a hidden iframe.
- **Delete** is offered in the list row and on the detail hero, both permission-checked (`65751027`).

![Application Role screen](/screenshots/access-control/application-role.png)

![Application Role detail screen](/screenshots/access-control/application-role-detail.png)

## 1. What & Who

Application roles are the **named bundles of [access-control/permission](/en/inventory/access-control/permission)s** assigned to users inside a [master-data/business-unit](/en/inventory/master-data/business-unit). They are the fine-grained, tenant-side authorisation layer that controls *what each user can do in each BU*, distinct from platform-wide roles (`tb_platform_role`, a separate relational, cluster-scoped system owned by Carmen Platform admin — see [access-control/user](/en/inventory/access-control/user) Edge Cases; the older `tb_user.platform_role` enum column it replaced was dropped 2026-06-10). Every transactional UI action — submitting a PR, approving a GRN, posting an adjustment — is gated by checking whether the active user holds an application role that includes the matching permission atom for the active BU.

**Maintained by** Sysadmin (per BU). **Read by** every API endpoint at request time.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a role for a BU | `/system-admin/role/new` → **Name**, Description + permission picker → Save | No BU picker on this form — the role is created inside the caller's active BU context; `POST …/application-roles { name, description, permissions: { add } }` |
| Add permissions to a role | Role edit → permission picker (`permission-picker.tsx`) | One row per resource with a Toggle pill per real action; "Grant all" per category and select-all per row; module-level "Module access" row first in each category |
| Print a role's grants | Role detail → **Print** | `use-role-print.ts` — per-module grant summary, hotel-style document header |
| Assign a user to a role | **Not on the Role screen** — done from `/system-admin/user/:id` → **Edit** → tick roles → Save (`PATCH /api/config/:bu_code/users/:user_id { application_role_id: { add, remove } }`) | The Role edit screen has only Name + Description + Permissions; there is no Users tab (confirmed against `role-form.tsx` and the e2e test-case catalog `1101-role.md`) |
| See who holds which role | `/system-admin/user` → **Print** / **Export** | User × role matrix from `GET /api/config/:bu_code/user-application-roles` |
| Retire a role | Set `is_active = false` | Existing assignments persist; permissions stop granting on next eval |
| Delete a role | Role list row action, or Hero **Delete** button on the detail screen | Blocked if active assignments exist per Validation & Errors below |
| Audit role changes | [reporting-audit/activity](/en/inventory/reporting-audit/activity) log | Filter by `entity_type = application_role` |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Role name already exists in this BU" | Duplicate `(business_unit_id, name)` among non-deleted | Pick a different name or reactivate the existing role |
| "User has no access to this BU" | Missing `tb_user_tb_business_unit` row | Grant BU access first via [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) |
| Cannot delete role | Active assignments exist | Soft-delete or set `is_active = false` instead |
| User still sees old permissions | Cached session | Wait for refresh or force re-login |

## 4. Edge Cases

- **Permission checks are live, not snapshot.** Unlike master data, role changes take effect on next permission re-evaluation — historical documents are not retro-permissioned.
- **BU scoping is application-enforced.** No DB constraint blocks assigning a role to a user without BU access — the service layer must validate.
- **Soft-deleted roles** stop granting permissions (joins filter `deleted_at IS NULL`) but assignment rows persist for audit.
- **Inactive permission link** (`tb_application_role_tb_permission.is_active = false`) removes the permission without deleting the link — useful for staged rollouts.
- **Managing roles is gated in the frontend only.** The `/system-admin/role` nav entry gates on `PERMISSIONS.system_admin.role.view` (`constant/module-list.ts:691-695`; the `system_configuration.view` key a prior version cited was a ghost, replaced 2026-09-21) and `tb_permission` carries `system_admin.role.{view,create,update,delete}` — but `config_application-roles.controller.ts` checks none of them: its five routes sit behind the class-level `KeycloakGuard` (`:59`) with no `AppIdGuard` and no `@Permission` decorator (`grep -c` = 0 at HEAD). The same is true of `config_user-application-roles` and `config_permissions`. Any authenticated member of the BU whose licence includes `system_admin.role` can create, edit or delete roles via the API. **Unconfirmed whether this is intended** — flagged, not fixed.

---

## 5. Data Model (Dev)

Source: platform schema.

### 5.1 `tb_application_role`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `business_unit_id` | `String @db.Uuid` | No | FK to `tb_business_unit` — roles are BU-scoped. |
| `name` | `String @db.VarChar` | No | Role name (e.g. `Procurement Manager`, `Storekeeper`). |
| `description` | `String?` | Yes | Free text. |
| `is_active` | `Boolean? @db.Boolean` | Yes | Default `true`. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-lock version — the update DTO echoes the loaded record's version (`role.doc_version` in `role-form.tsx`); the backend rejects a stale value. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([business_unit_id, name, deleted_at])`. Index on `(business_unit_id, name, deleted_at)`. FK to `tb_business_unit` `onDelete: NoAction`.

### 5.2 `tb_application_role_tb_permission`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `application_role_id` | `String @db.Uuid` | No | FK to `tb_application_role`. |
| `permission_id` | `String @db.Uuid` | No | FK to `tb_permission`. |
| `is_active` | `Boolean? @db.Boolean` | Yes | Default `true`. Schema supports disabling a permission link without unlinking; no UI surfaces this toggle today — the role-edit screen only adds/removes links. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([application_role_id, permission_id, deleted_at])`. FKs `onDelete: NoAction`.

### 5.3 `tb_user_tb_application_role`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | FK to `tb_user`. |
| `application_role_id` | `String @db.Uuid` | No | FK to `tb_application_role`. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, application_role_id, deleted_at])`. The (user, BU) → role[] traversal joins through `tb_application_role` because `business_unit_id` lives there.

## 6. Business Rules

- **Uniqueness.** `(business_unit_id, name)` is unique among non-deleted roles. A user holds each role at most once per BU.
- **BU scoping.** A role can only be assigned to a user with an active `tb_user_tb_business_unit` row for the same BU (application-enforced).
- **Deletion guards.** Hard-delete blocked if any active assignment exists. Soft-delete allowed; assignments persist but no permissions granted.
- **Inactivation cascade.** `is_active = false` revokes permissions on next re-evaluation; cached sessions may continue until refresh.
- **Live, not snapshot.** Permission checks evaluate the current join state — no document-side snapshot.

## 7. Cross-References

- [access-control/permission](/en/inventory/access-control/permission) — atoms that roles aggregate.
- [access-control/user](/en/inventory/access-control/user) — accounts roles are assigned to.
- [master-data/business-unit](/en/inventory/master-data/business-unit) — every role is BU-owned.
- [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) — prerequisite for any role assignment.
- All transactional modules — every auth check joins through these tables.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`.
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_application-roles/config_application-roles.controller.ts` (`GET` `:76`, `GET :id` `:140`, `POST` `:190`, `PUT :id` `:253`, `DELETE :id` `:320`; swagger `response.ts`), `config/config_user-application-roles/` (matrix `GET` `:80`, per-user `GET :user_id`, `POST`, `PATCH`, `DELETE`); service `apps/micro-business/src/authen/role_permission/role_permission.service.ts`; serializer `apps/backend-gateway/src/common/dto/application-role/application-role.serializer.ts`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/application-roles/`, `config/user-application-roles/`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/role/` (`role.route.tsx`, `role-new.route.tsx`, `role-edit.route.tsx`, `role-component.tsx`, `role-form.tsx`, `role-form-hero.tsx`, `role-form-schema.ts`, `permission-picker.tsx`, `permission-catalog.ts`, `use-permission.ts`, `use-role-print.ts`, `use-role-table.tsx`) for the role screen itself; `../carmen-inventory-frontend-react/routes/system-admin/user/user-assigned-roles.tsx` for user↔role assignment; `types/role.ts`; nav key in `constant/module-list.ts:691-695` / `constant/permissions.ts` (`system_admin.role`).
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1101-role.md` (44 cases, documentation-only; no automated Playwright spec yet).
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`.
