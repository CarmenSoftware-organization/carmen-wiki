---
title: Department User
description: The user↔department membership pivot — declares which users belong to which departments, and marks the Head of Department (HOD) who drives approval routing on PRs and SRs.
published: true
date: 2026-07-16T01:26:05.000Z
tags: access-control, department-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Department User

> **At a Glance**
> **Owner:** Sysadmin / Product Admin &nbsp;·&nbsp; **Table:** `tb_department_user` &nbsp;·&nbsp; **Used by:** PR and SR approval routing, RBAC scope, cost-centre reporting &nbsp;·&nbsp; User↔department membership pivot — `is_hod = true` marks the Head of Department whose approval is required on departmental requisitions.

## 1. What & Who

`department-user` is the **user↔department membership pivot**: it declares that a given [access-control/user](/en/inventory/access-control/user) belongs to a given [master-data/department](/en/inventory/master-data/department). Ordinary membership (`is_hod = false`) is effectively **single-department per user** in practice: the lookup endpoint (`findByUserId` in `department-user.service.ts`) uses `findFirst` to return one "member" department (nullable), and the Department edit screen's Members picker filters out any user who already has a `department` elsewhere. The `is_hod` boolean is separate and **can span multiple departments** — a user may be Head of Department for several departments simultaneously; there is no code enforcing at most one HOD per department (see Edge Cases).

The HOD flag drives downstream workflow logic: when a [purchase-request](/en/inventory/purchase-request) or [store-requisition](/en/inventory/store-requisition) is submitted by a user whose requesting department has an HOD, the approval pipeline routes a review step to that HOD. Without a row here a user is invisible to departmental approval routing and cost-centre reports.

**Maintained by** Sysadmin (user-to-department assignments, HOD flag). **Read by** PR/SR approval workflows, RBAC scope resolvers, and reporting.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Assign a user to a department | **Department** edit screen (`/config/department/:id`) → **Members** panel → Transfer control (`department-form.tsx`) | Not on the user side — the User Assign screen's Departments section is read-only (see [access-control/user](/en/inventory/access-control/user)) |
| Designate as Head of Department | Same Department edit screen → **HOD** panel → Transfer control | Independent Transfer widget from Members; add/remove is not blocked by any existing-HOD check |
| Reassign HOD | HOD panel → move the old HOD back to Available, move the new one to Assigned → Save | Historical approvals keep the original signer; nothing clears a previous HOD automatically (see Edge Cases) |
| Remove user from department | Members panel → move user back to Available → Save | Open PR/SR steps referencing this user are unaffected; future routing will find no HOD if this was the last one |
| List all HODs for a department | Query `tb_department_user WHERE department_id = ? AND is_hod = true AND deleted_at IS NULL` (`getHodInDepartment` in `department-user.service.ts`) | Use for audit or workflow-config verification |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Duplicate department assignment" | `(department_id, user_id)` unique constraint on non-deleted row | Remove the existing row first, or soft-delete and re-add |
| Workflow cannot resolve HOD | No `is_hod = true` row for the department | Add a user to the department's HOD panel |
| Approved step shows removed user | Past approval steps capture the signer at time of action | Expected — HOD change is not retroactive |

## 4. Edge Cases

- **Single-HOD-per-department is *not* enforced anywhere.** `departments.service.ts`'s HOD-add path (`data.hod_users.add`) only checks whether the acting user already has an `is_hod = true` row for *that same department* (to avoid a duplicate row) — it does not check or clear any *other* user's existing HOD row first. Nothing in the backend or frontend stops two or more users from being marked HOD for the same department simultaneously. Treat "one HOD per department" as a data-entry convention, not a guarantee.
- **Ordinary membership is effectively single-department**, driven by query shape (`findFirst`) and a frontend picker filter — not a DB constraint. The unique constraint is `(department_id, user_id, deleted_at)`, which technically permits the same user in two departments' Members lists if inserted directly; the UI and the `findByUserId` lookup just don't support or surface that state.
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
| `user_id` | `String @db.Uuid` | No | References platform `tb_user.id`; **not** a Prisma FK on this model (cross-schema, same pattern as [access-control/user-location](/en/inventory/access-control/user-location)) — only `department_id` has a declared `@relation`. |
| `department_id` | `String @db.Uuid` | No | FK to `tb_department`. |
| `is_hod` | `Boolean?` | Yes | Default `false`. `true` = Head of Department for this assignment. |
| `note` | `String? @db.VarChar` | Yes | Free-text annotation. |
| `info` | `Json?` | Yes | Unstructured metadata. |
| `dimension` | `Json?` | Yes | Dimensional metadata. |
| `doc_version` | `Int` | No | Default `0`. Optimistic concurrency token. |
| Audit columns | — | Yes | `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id`. |

**Constraints:** `@@unique([department_id, user_id, deleted_at])` map `department_user_u`. FK `tb_department_user.department_id → tb_department.id` `onDelete: NoAction, onUpdate: NoAction`. Three plain indexes: `(department_id, user_id)`, `(user_id)`, `(department_id)` — **no** `is_hod`-related index of any kind, partial or otherwise, which is consistent with the Edge Cases finding above that nothing in the schema enforces at most one HOD per department.

## 6. Business Rules

- **Uniqueness.** At most one active `(department_id, user_id)` row per combination — the unique constraint prevents duplicate assignments.
- **HOD is not invariant-enforced.** Nothing in `departments.service.ts` or elsewhere clears a department's existing HOD before adding a new one — see Edge Cases. Treat "one HOD per department" as a UI/process convention, not a guarantee.
- **HOD authority.** `is_hod = true` grants automatic approval authority within that department for PR and SR workflow steps routed to the HOD role type.
- **Membership is effectively single-department; HOD is independently multi-department.** The `findByUserId` lookup and the Department edit screen's Members picker both treat non-HOD membership as one department per user; the HOD flag is a separate axis and a user can be HOD of several departments at once.
- **Soft-delete.** Removal is soft (`deleted_at`) to preserve audit. Active membership filter requires `deleted_at IS NULL`.
- **No cascade.** FK `onDelete: NoAction` — deleting a department with active user rows is blocked at the DB level; deactivate or reassign users first.

## 7. Cross-References

- [access-control/user](/en/inventory/access-control/user) — the user side of the membership.
- [master-data/department](/en/inventory/master-data/department) — the department side; also documents `tb_department_user` in its Data Model section.
- [purchase-request](/en/inventory/purchase-request) — PR approval routing resolves the HOD from `tb_department_user` for departmental review steps.
- [store-requisition](/en/inventory/store-requisition) — SR routing similarly consults the HOD flag for inter-department requisitions.
- [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) — parallel BU-level pivot (`tb_user_tb_business_unit`); BU membership gates entry; department membership scopes approval routing inside the BU.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_department_user` (line 4771).
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/department-user/department-user.service.ts` (`findByUserId`, `hasHodInDepartment`, `getHodInDepartment`); `.../apps/micro-business/src/master/departments/departments.service.ts` (Members/HOD add-remove on department update); `.../apps/backend-gateway/src/config/config_department-users/` (gateway proxy).
- **Docs:** `../carmen/docs/app/system-administration/user-management/DD-user-management.md` — `tb_department_user` entity detail and HOD index definitions.
- **Docs:** `../carmen/docs/app/system-administration/user-management/BR-user-management.md` — BR-002: HOD Designation business rule (design intent; not enforced in current code — see Edge Cases).
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/department/department-form.tsx` (Members + HOD Transfer widgets on the Department edit screen). The User Assign screen (`routes/system-admin/user/user-assigned-departments.tsx`) only *displays* membership read-only.
