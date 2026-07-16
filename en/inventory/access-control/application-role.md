---
title: Application Role
description: Per-business-unit role definitions plus the join tables that map roles to permissions and users to roles — the heart of tenant RBAC.
published: true
date: 2026-07-15T23:46:09.000Z
tags: access-control, application-role, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Application Role

> **At a Glance**
> **Owner:** Sysadmin (per BU) &nbsp;·&nbsp; **Table:** `tb_application_role` (+ `tb_application_role_tb_permission`, `tb_user_tb_application_role`) &nbsp;·&nbsp; **Used by:** every transactional module's permission check &nbsp;·&nbsp; Named bundles of permissions assigned to users inside a BU.

![Application Role screen](/screenshots/access-control/application-role.png)

![Application Role detail screen](/screenshots/access-control/application-role-detail.png)

## 1. What & Who

Application roles are the **named bundles of [access-control/permission](/en/inventory/access-control/permission)s** assigned to users inside a [master-data/business-unit](/en/inventory/master-data/business-unit). They are the fine-grained, tenant-side authorisation layer that controls *what each user can do in each BU*, distinct from platform-wide roles (`tb_platform_role`, a separate relational, cluster-scoped system owned by Carmen Platform admin — see [access-control/user](/en/inventory/access-control/user) Edge Cases; the older `tb_user.platform_role` enum column it replaced was dropped 2026-06-10). Every transactional UI action — submitting a PR, approving a GRN, posting an adjustment — is gated by checking whether the active user holds an application role that includes the matching permission atom for the active BU.

**Maintained by** Sysadmin (per BU). **Read by** every API endpoint at request time.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a role for a BU | `/system-admin/role/new` → **Name** + permission matrix → Save | No BU picker on this form — the role is created inside the caller's active BU context |
| Add permissions to a role | Role edit → permission matrix / picker (`permission-matrix.tsx`, `permission-picker.tsx`) | Checkboxes over `tb_permission` grouped by `resource`; column-header click grants/revokes a whole action across all resources, row `Grant All` grants a whole category |
| Assign a user to a role | **Not on the Role screen** — done from `/system-admin/user/:id` → **Assign Roles** section → toggle role cards → Save | The Role edit screen has only Name + Permissions; there is no Users tab (confirmed against `role-form.tsx` and the e2e test-case catalog `1101-role.md`) |
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
- **Managing roles is itself coarsely gated.** The `/system-admin/role` route (and `/system-admin/user`, `/system-admin/user-activity`) is gated by a single coarse frontend permission key, `PERMISSIONS.system_configuration.view` (`constant/module-list.ts`) — there is no granular "who may manage roles" permission distinct from general system-configuration access.

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

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application_role` (line 19), `tb_application_role_tb_permission` (line 44), `tb_user_tb_application_role` (line 606).
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/role/` (`role-form.tsx`, `permission-matrix.tsx`, `permission-picker.tsx`, `role-component.tsx`) for the role screen itself; `../carmen-inventory-frontend-react/routes/system-admin/user/user-assigned-roles.tsx` for user↔role assignment; route guard key in `constant/module-list.ts` / `constant/permissions.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1101-role.md` (documentation-only test-case catalog; no automated Playwright spec yet).
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`.
