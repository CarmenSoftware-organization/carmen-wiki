---
title: Permission
description: Atomic resource + action pairs bundled into application roles for RBAC; a separate App ID client-allowlist mechanism gates comment and approval-workflow routes.
published: true
date: 2026-07-15T23:46:09.000Z
tags: access-control, permission, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Permission

> **At a Glance**
> **Owner:** Seed-managed (release-time) &nbsp;·&nbsp; **Table:** `tb_permission` &nbsp;·&nbsp; **Used by:** [access-control/application-role](/en/inventory/access-control/application-role) (only consumer) &nbsp;·&nbsp; Atomic `(resource, action)` pairs — the smallest unit of authorisation.

## 1. What & Who

A permission is the **smallest unit of authorisation**: a `(resource, action)` pair, e.g. `resource = "procurement.purchase_request"`, `action = "view"` (the `resource` column is itself a dot-namespaced string such as `procurement.purchase_request` or `inventory_management.stock_in` — not a bare noun). Permissions are catalogued centrally (seed script `packages/prisma-shared-schema-platform/prisma/seed.permission.data.ts`) and **never assigned directly** to users — they are aggregated into [access-control/application-role](/en/inventory/access-control/application-role) rows via `tb_application_role_tb_permission`, and users get them transitively by being granted a role.

The runtime check is enforced by a concrete backend guard, not just an abstract join: a route declares `@Permission({ 'procurement.purchase_request': ['view'] })` (`apps/backend-gateway/src/auth/decorators/permission.decorator.ts`), and `PermissionGuard` (`apps/backend-gateway/src/auth/guards/permission.guard.ts`) reads the caller's resolved grants from the `x-bu-datas` header (computed at login/BU-switch from the `tb_user_tb_application_role` → `tb_application_role` → `tb_application_role_tb_permission` join) and checks `hasAllPermissions`. A user whose `tb_user_tb_business_unit.role = admin` for that BU bypasses the check entirely ("god-mode" — matches the BU-admin bypass documented on [access-control/business-unit-user](/en/inventory/access-control/business-unit-user)). Not every route carries a `@Permission` decorator — if absent, `PermissionGuard` allows the request through unconditionally, so some endpoints have no RBAC check at all (confirmed against several Bruno collection entries documented as "Permissions: None").

The frontend mirrors this catalogue as a typed, dot-notation object in `constant/permissions.ts` (`PERMISSIONS.procurement.purchase_request.view`, etc.) rather than raw strings, purely so components can gate menu items and routes without literal-string typos; the object's own leading comment states it "mirrors the BE `/permissions` endpoint."

**Maintained by** release migrations (seed). **Read by** the role-edit UI for bundling and by `PermissionGuard` for every guarded API request.

### 1.1 The App ID client-application allowlist — a separate mechanism

Comment threads on documents, most approval-workflow actions (`approve`/`reject`/`review`/`submit`), and the cross-module "my approvals" inbox are **not** gated by `tb_permission` / `@Permission` at all. They carry `@UseGuards(new AppIdGuard('<api name>'))` instead, which checks the `x-app-id` request header against an in-memory allowlist snapshot (`apps/backend-gateway/src/common/guard/app-allowlist.store.ts`) sourced from the platform-schema `tb_application` + `tb_application_api` tables. `x-app-id` identifies which **registered client application** (e.g. the web SPA, a mobile client, an integration) is calling — each `tb_application` row has `allow_all` (wildcard) or an explicit list of allowed API names — and is unrelated to which permissions the calling **user**'s role grants. A request can pass `AppIdGuard` with a fully-permissioned user yet be blocked if the calling client isn't allowlisted for that API name, and vice versa; the two guards are independent and a given route may carry either, both, or neither.

Comment API names follow a uniform verb set per document type:

| Document type | Comment API-name prefix | Actions |
|---|---|---|
| Purchase Request | `purchaseRequestComment` | `findAll`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |
| Purchase Order | `purchaseOrderComment` | `findAll`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |
| Store Requisition | `storeRequisitionComment` | `findAll`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |

There is no separate plain `create` — `createWithFiles` is the sole create action (single multipart request that posts the comment and any attachments together; confirmed no comment controller exposes an additional bare `create` endpoint).

Other App IDs seen on approval/workflow routes:

| API name | Purpose |
|---|---|
| `storeRequisition.approve` | Approve a store-requisition at an approval step |
| `storeRequisition.reject` | Reject a store-requisition at an approval step |
| `storeRequisition.review` | Mark a store-requisition reviewed (intermediate workflow action) |
| `storeRequisition.submit` | Submit a store-requisition into its approval workflow |
| `my-approve.findAll` | List every document awaiting **the current user's** approval, across document types — backs the cross-module approval inbox ([dashboard/my-approval](/en/inventory/dashboard/my-approval)) |

These API names are registered per client application via `tb_application_api`, not bundled into `tb_application_role` — see [access-control/application-role](/en/inventory/access-control/application-role) for the actual per-user RBAC bundle.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| View the permission catalogue | Only inside the Role edit screen's permission matrix (`routes/system-admin/role/permission-matrix.tsx` + `permission-picker.tsx`) | No standalone permission-list screen exists in the inventory frontend |
| Bundle permissions into a role | [access-control/application-role](/en/inventory/access-control/application-role) edit screen | Checkbox grid; this is the normal path |
| Add a new permission atom | Release migration / seed | `tb_permission` is seed-managed, not UI-editable |
| Rename / retire a permission | Soft-delete + re-create | Constraint includes `deleted_at` so `(resource, action)` can be re-used |
| Find which roles include a permission | Query `tb_application_role_tb_permission` by `permission_id` | Useful before retirement |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Permission not found" at runtime | Code references a permission that was deleted or never seeded | Re-seed or restore via migration |
| Duplicate `(resource, action)` insert | Existing non-deleted row | Use the existing row instead |
| Feature silently disabled for everyone | Permission deleted while code still references it | Operational guard — restore via migration |
| Confusing tooltip in role editor | Missing or terse `description` | Update seed; descriptions should explain *what the permission unlocks* |

## 4. Edge Cases

- **Closed enumeration.** The set of permissions is closed per release — new permissions ship with code that checks them.
- **No direct user link.** There is no `tb_user_tb_permission` join — all paths go through application roles.
- **Soft-delete + rename.** Constraint includes `deleted_at` so a renamed permission can be soft-deleted and `(resource, action)` re-created.
- **Description discipline.** `description` is for the role-edit tooltip — must explain *what the permission unlocks*, not just restate the pair.

---

## 5. Data Model (Dev)

Source: platform schema.

### 5.1 `tb_permission`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `resource` | `String @db.VarChar` | No | Dot-namespaced resource string, e.g. `procurement.purchase_request`, `inventory_management.stock_in`, `configuration.department` — not a bare noun. |
| `action` | `String @db.VarChar` | No | Verb (e.g. `view`, `view_department`, `view_all`, `create`, `update`, `delete`, `commit`). |
| `description` | `String?` | Yes | Human-readable label and rationale. |
| `show_in_mobile` | `Boolean` | No | Default `false`. Whether the permission is exposed to the mobile app's permission surface. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([resource, action, deleted_at])`. Back-relation to `tb_application_role_tb_permission`. Audit FKs `onDelete: NoAction`.

## 6. Business Rules

- **Uniqueness.** `(resource, action)` is unique among non-deleted permissions; constraint includes `deleted_at` to allow rename via soft-delete + re-create.
- **Closed enumeration.** New permissions ship with code that checks them; deletion is an *operational* guard (release process), not DB-enforced.
- **No direct user link.** Every authorisation path goes through `tb_application_role`. Single source of truth keeps audit trails simple.
- **Description discipline.** Required for the role-edit UI tooltip — must explain consequences, not just restate the pair.

## 7. Cross-References

- [access-control/application-role](/en/inventory/access-control/application-role) — sole consumer.
- [access-control/user](/en/inventory/access-control/user) — holds permissions transitively through roles.
- All transactional modules — every route carrying a `@Permission` decorator resolves against a `(resource, action)` via `PermissionGuard`; routes without the decorator have no RBAC check, and comment/approval-workflow routes are gated separately by `AppIdGuard` (§1.1).

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_permission` (`model tb_permission`, line 425).
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.permission.data.ts`, `seed.permission.ts`.
- **Backend guard:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/decorators/permission.decorator.ts`, `.../auth/guards/permission.guard.ts` (RBAC); `.../common/guard/app-id.guard.ts`, `.../common/guard/app-allowlist.store.ts` (App ID client allowlist, §1.1).
- **Frontend:** Surfaced inside role-edit at `../carmen-inventory-frontend-react/routes/system-admin/role/permission-matrix.tsx` + `permission-picker.tsx`. No standalone CRUD. Typed key catalogue mirrored in `../carmen-inventory-frontend-react/constant/permissions.ts`.
