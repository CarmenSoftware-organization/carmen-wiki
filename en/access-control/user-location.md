---
title: User Location
description: Per-user location scoping inside a tenant — restricts a user to a subset of inventory locations for issue, count, and adjustment operations.
published: true
date: 2026-05-16T08:00:00.000Z
tags: access-control, user-location, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# User Location

## 1. Purpose

`user-location` narrows a user's effective scope inside a tenant from "all locations" to "this subset". A storekeeper assigned to two storerooms should only see those two in their location pickers, count documents, and adjustment screens; the front-office cashier should not see the central kitchen at all. The table is a simple many-to-many between [[access-control/user]] (via `user_id`) and [[master-data/location]] (via `location_id`), with an active-only soft-delete pattern.

Unlike [[access-control/application-role]] (which gates **what actions** a user can perform) and [[access-control/business-unit-user]] (which gates **which BU** they can enter), `user-location` is purely a **row-level data filter**: it restricts which inventory rows are visible without changing the user's role or permissions. An empty set is conventionally interpreted as "no restriction" (i.e. the user sees all locations the BU exposes) — confirm with service code before relying on this default.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_user_location`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | The user being scoped. References platform `tb_user.id`; not a Prisma-declared FK (cross-schema). |
| `location_id` | `String @db.Uuid` | No | FK to tenant `tb_location`. |
| `note` | `String? @db.VarChar` | Yes | Free-text reason / assignment context. |
| `info` | `Json? @db.JsonB` | Yes | Default `{}`. Reserved metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, location_id, deleted_at])` map `user_location_user_id_location_id_u`. Index on `(user_id, location_id)` map `user_location_user_id_location_id_idx`. FK to `tb_location` `onDelete: NoAction`. `user_id` is a logical reference to platform `tb_user` and is enforced application-side, not by the database (cross-schema).

## 3. Usage / Cross-References

- [[inventory]] — inventory listings and movement screens filter `tb_inventory_*` rows by `location_id IN (user's set)`.
- [[store-requisition]] — issue and requesting locations on SR documents are validated against the user's set when policy demands location-bound issuing.
- [[physical-count]] — count documents are restricted to the user's locations, so storekeepers only see and count their own areas.
- [[spot-check]] — same as physical-count for ad-hoc spot checks.
- [[master-data/location]] — the location side of the relationship.
- [[access-control/user]] — the user side of the relationship.

## 4. Configuration UI

Managed by **Sysadmin** (and optionally by a BU admin holding `tb_user_tb_business_unit.role = admin`). The user-edit screen has a Locations tab that lists current scope and provides add / remove against the BU's `tb_location` catalogue. Audit of scope changes is captured through the standard `created_*` / `updated_*` columns and surfaced in the [[reporting-audit]] activity log.

## 5. Business Rules

- **Uniqueness.** A user has at most one active assignment per location (`(user_id, location_id)` is unique among non-deleted rows).
- **Empty-set semantics.** Conventionally interpreted as "no row-level restriction" — the user sees all locations the BU exposes through normal RBAC. Code paths that require an explicit assignment (rare) must check `count > 0` before resolving scope.
- **Deletion guards.** Hard-delete is permitted because no transactional row references this table directly. Soft-delete (`deleted_at`) preserves audit history.
- **Cross-schema integrity.** The `user_id` column references platform `tb_user.id` but is **not** a Prisma FK because the two models live in different schemas. The application must validate the user id when inserting and must clean up on user-deletion through a maintenance job.
- **Lifecycle.** Reassigning a storekeeper from Storeroom A to Storeroom B is two operations: soft-delete the A row, insert a B row. The user's open documents that reference A keep working because document-level FKs target `tb_location`, not `tb_user_location`.
- **Per-document overrides.** This table is the **default scope** for pickers; specific document workflows may broaden or narrow it (e.g. an approver in [[store-requisition]] needs to see both source and destination locations regardless of their own assignment).

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_user_location` (lines ~4451-4470).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/user-role/` — Locations tab on the user-edit screen.
- **Cross-module:** see Section 3.
