---
title: Department
description: Organisational departments and their user assignments — used as cost-centre and approval scope on requisition and PR documents.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, department, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Department

## 1. Purpose

Departments model the cost-centre / requesting-unit dimension of the property — Kitchen, F&B, Engineering, Housekeeping, Front Office, etc. Every internal request for goods (purchase request, store requisition) carries a department FK, and approval workflows often route by department. Department is also the join axis between users and the part of the business they belong to via `tb_department_user`.

`tb_department_user` links each user to one or more departments and marks one of them as Head of Department (`is_hod`). Workflow steps that need a "department head" reviewer resolve via this table.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_department`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short department code (e.g. `KIT`, `FB`). |
| `name` | `String @db.VarChar` | No | Department name. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:**

- `@@unique([name, deleted_at])` map `department_name_u`.
- `@@unique([code, deleted_at])` map `department_code_u`.
- `@@unique([code, name, deleted_at])` map `department_code_name_u`.
- Indexes on `name` and `code`.

### 2.2 `tb_department_user`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | FK to platform `tb_user`. |
| `department_id` | `String @db.Uuid` | No | FK to `tb_department`. |
| `is_hod` | `Boolean?` | Yes | True when this user is the department head, defaults `false`. |
| `note`, `info`, `dimension`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([department_id, user_id, deleted_at])` map `department_user_u`. Indexes on `(department_id, user_id)`, `user_id`, and `department_id`. FK to `tb_department` with `onDelete: NoAction`.

## 3. Usage / Cross-References

- [[purchase-request]] — PR header references requesting department; routing uses department head from `tb_department_user`.
- [[store-requisition]] — `from`/`to` location is paired with department on every requisition.
- [[access-control]] — department membership influences default RBAC scope.
- [[reporting-audit]] — many reports group by department.

## 4. Configuration UI

Managed by **Product Admin** (department list + active flag) and **Sysadmin** (user-to-department assignment, HOD flag). Department list lives in the Master Data area; user assignments live in the user-admin screen.

## 5. Business Rules

- **Uniqueness.** `code` is unique among non-deleted rows; the combined `(code, name)` index also guards against typo duplicates.
- **Deletion guards.** A department referenced by any open PR or SR cannot be hard-deleted; soft-delete only after all open documents are closed and no active user mappings remain.
- **Validation.** `code` and `name` are required. Only one `is_hod = true` per department at a time (application invariant; not enforced by the DB).
- **Lifecycle.** `is_active = false` removes the department from new-document pickers but preserves historical references.
- **HOD changes.** Changing the HOD does not retro-fit historical approvals — past steps keep the user who actually signed.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_department` (lines ~682-708), `tb_department_user` (lines ~4401-4425).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/department/`.
- **Cross-module:** see Section 3.
