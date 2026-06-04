---
title: Department User
description: The user↔department membership pivot — declares which users belong to which departments, and marks the Head of Department (HOD) who drives approval routing on PRs and SRs.
published: true
date: 2026-06-04T00:00:00.000Z
tags: access-control, department-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Department User

> **At a Glance**
> **Owner:** Sysadmin / Product Admin &nbsp;·&nbsp; **Table:** `tb_department_user` &nbsp;·&nbsp; **Used by:** PR and SR approval routing, RBAC scope, cost-centre reporting &nbsp;·&nbsp; User↔department membership pivot — `is_hod = true` marks the Head of Department whose approval is required on departmental requisitions.

## 1. What & Who

`department-user` is the **user↔department membership pivot**: it declares that a given [access-control/user](/en/inventory/access-control/user) belongs to a given [master-data/department](/en/inventory/master-data/department). A user may belong to multiple departments; each membership row is independent. The boolean flag `is_hod` marks the Head of Department for that specific assignment — at most one HOD per department is enforced by the application.

The HOD flag drives downstream workflow logic: when a [purchase-request](/en/inventory/purchase-request) or [store-requisition](/en/inventory/store-requisition) is submitted by a user whose requesting department has an HOD, the approval pipeline routes a review step to that HOD. Without a row here a user is invisible to departmental approval routing and cost-centre reports.

**Maintained by** Sysadmin (user-to-department assignments, HOD flag). **Read by** PR/SR approval workflows, RBAC scope resolvers, and reporting.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Assign a user to a department | User-admin screen → Department tab → **Add** | Pick department; `is_hod` defaults `false` |
| Designate as Head of Department | Same screen → toggle `is_hod` | At most one HOD per department (app invariant) |
| Reassign HOD | Toggle off old, toggle on new | Historical approvals keep the original signer |
| Remove user from department | Soft-delete the row | Open PR/SR steps referencing this user are unaffected; future routing will find no HOD |
| List all HODs for a department | Query `tb_department_user WHERE is_hod = true AND deleted_at IS NULL` | Use for audit or workflow-config verification |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Duplicate department assignment" | `(department_id, user_id)` unique constraint on non-deleted row | Remove the existing row first, or soft-delete and re-add |
| Workflow cannot resolve HOD | No `is_hod = true` row for the department | Set one user as HOD in the user-admin Department tab |
| Multiple HOD rows for same department | Application invariant violated | Run a maintenance check; clear extra `is_hod = true` rows |
| Approved step shows removed user | Past approval steps capture the signer at time of action | Expected — HOD change is not retroactive |

## 4. Edge Cases

- **Single-HOD invariant** is app-enforced, not DB-enforced. A user can be HOD of multiple departments simultaneously (one row per department with `is_hod = true`), but each department should have at most one HOD.
- **HOD change** never retro-fits historical approvals — past workflow steps keep the user who signed.
- **Soft-delete preferred** — hard-delete is physically allowed (no transactional FK targets on this row), but soft-delete preserves the audit trail.
- **User without department** — a user with no `tb_department_user` rows can still log in and hold application roles, but PR/SR approval routing will find no HOD resolution path through them.
- **note / info / dimension** metadata fields are available for operational annotations (e.g. effective date comments) but are not used by any system-enforced logic.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 5.1 `tb_department_user`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | FK to platform `tb_user`. |
| `department_id` | `String @db.Uuid` | No | FK to `tb_department`. |
| `is_hod` | `Boolean?` | Yes | Default `false`. `true` = Head of Department for this assignment. |
| `note` | `String? @db.VarChar` | Yes | Free-text annotation. |
| `info` | `Json?` | Yes | Unstructured metadata. |
| `dimension` | `Json?` | Yes | Dimensional metadata. |
| `doc_version` | `Decimal` | No | Default `0`. Optimistic concurrency token. |
| Audit columns | — | Yes | `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id`. |

**Constraints:** `@@unique([department_id, user_id])` map `department_user_u`. FK `tb_department_user.department_id → tb_department.id` `onDelete: NoAction, onUpdate: NoAction`. Indexes on `user_id`, `department_id`, and a partial index on `(department_id, is_hod) WHERE deleted_at IS NULL AND is_hod = true`.

## 6. Business Rules

- **Uniqueness.** At most one active `(department_id, user_id)` row per combination — the unique constraint prevents duplicate assignments.
- **HOD invariant.** At most one `is_hod = true` row per department — application-enforced; toggling a new HOD should clear the previous HOD flag.
- **HOD authority.** `is_hod = true` grants automatic approval authority within that department for PR and SR workflow steps routed to the HOD role type.
- **Multi-department membership.** A user may belong to many departments; each membership is independent and can independently carry `is_hod`.
- **Soft-delete.** Removal is soft (`deleted_at`) to preserve audit. Active membership filter requires `deleted_at IS NULL`.
- **No cascade.** FK `onDelete: NoAction` — deleting a department with active user rows is blocked at the DB level; deactivate or reassign users first.

## 7. Cross-References

- [access-control/user](/en/inventory/access-control/user) — the user side of the membership.
- [master-data/department](/en/inventory/master-data/department) — the department side; also documents `tb_department_user` in its Data Model section.
- [purchase-request](/en/inventory/purchase-request) — PR approval routing resolves the HOD from `tb_department_user` for departmental review steps.
- [store-requisition](/en/inventory/store-requisition) — SR routing similarly consults the HOD flag for inter-department requisitions.
- [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) — parallel BU-level pivot (`tb_user_tb_business_unit`); BU membership gates entry; department membership scopes approval routing inside the BU.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_department_user` (lines ~2345-2366).
- **Docs:** `../carmen/docs/app/system-administration/user-management/DD-user-management.md` — `tb_department_user` entity detail and HOD index definitions.
- **Docs:** `../carmen/docs/app/system-administration/user-management/BR-user-management.md` — BR-002: HOD Designation business rule.
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/department/`.
