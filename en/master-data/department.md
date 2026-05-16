---
title: Department
description: Organisational departments and their user assignments — used as cost-centre and approval scope on requisition and PR documents.
published: true
date: 2026-05-17T11:00:00.000Z
tags: master-data, department, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Department

> **At a Glance**
> **Owner:** Product Admin (list) / Sysadmin (user mapping) &nbsp;·&nbsp; **Tables:** `tb_department`, `tb_department_user` &nbsp;·&nbsp; **Used by:** PR, SR, approval workflows, RBAC, reports &nbsp;·&nbsp; Cost-centre + requesting-unit dimension; resolves Head-of-Department reviewer.

## 1. What & Who

Departments model the **cost-centre / requesting-unit** dimension of the property — Kitchen, F&B, Engineering, Housekeeping, Front Office, etc. Every internal request for goods (PR, SR) carries a department FK, and approval workflows often route by department. Department is also the join axis between users and the part of the business they belong to via `tb_department_user`, which marks one user as **Head of Department** (`is_hod`).

**Maintained by** Product Admin (department list, active flag) and Sysadmin (user-to-department assignment, HOD flag). **Read by** developers on PR/SR routing, RBAC, and reports.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a department | Configuration → Master Data → Department → **New** | Required: `code`, `name` |
| Deactivate | Toggle `is_active` | Hidden from PR/SR pickers; historical references preserved |
| Assign user to department | User-admin screen → Department tab | Writes to `tb_department_user` |
| Set HOD | Same screen → toggle `is_hod` | At most one HOD per department (app invariant) |
| Reassign HOD | Toggle off old, on new | Past approvals retain the original signer |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code already in use" | Duplicate `code` on a non-deleted row | Pick a different code |
| "Department-name typo conflict" | `(code, name)` collides with an existing row | Resolve naming or reactivate the existing row |
| "Code / name required" | Form submitted blank | Add both |
| "Cannot delete — referenced by open PR/SR" | FK references exist | Soft-delete only after closing open docs and clearing user mappings |
| Workflow can't resolve HOD | No `is_hod = true` in the department | Set one user as HOD |

## 4. Edge Cases

- **Single-HOD invariant** is app-enforced, not DB. A maintenance check should fail loudly if multiple `is_hod = true` rows appear.
- **HOD change** doesn't retro-fit historical approvals — past steps keep the user who actually signed.
- **Soft-delete** requires no active user mappings; otherwise HOD resolution breaks for those users.
- **Triple unique** — `code`, `name`, and `(code, name)` all have uniqueness guards to prevent typo duplicates.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 5.1 `tb_department`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short department code (e.g. `KIT`, `FB`). |
| `name` | `String @db.VarChar` | No | Department name. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `is_active` | `Boolean?` | Yes | Active flag, defaults `true`. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `department_name_u`; `@@unique([code, deleted_at])` map `department_code_u`; `@@unique([code, name, deleted_at])` map `department_code_name_u`. Indexes on `name` and `code`.

### 5.2 `tb_department_user`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | FK to platform `tb_user`. |
| `department_id` | `String @db.Uuid` | No | FK to `tb_department`. |
| `is_hod` | `Boolean?` | Yes | True for Head of Department (default `false`). |
| `note`, `info`, `dimension`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([department_id, user_id, deleted_at])` map `department_user_u`. Indexes on `(department_id, user_id)`, `user_id`, `department_id`. FK to `tb_department` `onDelete: NoAction`.

## 6. Business Rules

- **Uniqueness.** `code` unique among non-deleted rows; `(code, name)` index guards typo duplicates.
- **Deletion guards.** Open PR/SR references block hard-delete; soft-delete only after closure and clearing user mappings.
- **Validation.** `code` and `name` required. At most one `is_hod = true` per department (app invariant).
- **Lifecycle.** `is_active = false` hides from new pickers; preserves historical references.
- **HOD changes** never retro-fit historical approvals.

## 7. Cross-References

- [[purchase-request]] — PR header references requesting department; routing uses HOD from `tb_department_user`.
- [[store-requisition]] — `from`/`to` location paired with department on every requisition.
- [[access-control]] — department membership drives default RBAC scope.
- [[reporting-audit]] — many reports group by department.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_department` (lines ~682-708), `tb_department_user` (lines ~4401-4425).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/department/`.
