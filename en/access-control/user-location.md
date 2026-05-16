---
title: User Location
description: Per-user location scoping inside a tenant — restricts a user to a subset of inventory locations for issue, count, and adjustment operations.
published: true
date: 2026-05-17T11:00:00.000Z
tags: access-control, user-location, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# User Location

> **At a Glance**
> **Owner:** Sysadmin / BU Admin &nbsp;·&nbsp; **Table:** `tb_user_location` &nbsp;·&nbsp; **Used by:** [[inventory]], [[store-requisition]], [[physical-count]], [[spot-check]] &nbsp;·&nbsp; Row-level location filter — restricts inventory rows visible to the user.

## 1. What & Who

`user-location` narrows a user's effective scope from "all locations" to "this subset". A storekeeper assigned to two storerooms should only see those two in their location pickers, count documents, and adjustment screens. The table is a simple many-to-many between [[access-control/user]] and [[master-data/location]] with an active-only soft-delete pattern.

Unlike [[access-control/application-role]] (which gates **actions**) and [[access-control/business-unit-user]] (which gates **BU entry**), `user-location` is a **row-level data filter** — it restricts visible rows without changing roles or permissions. An empty set is conventionally interpreted as "no restriction".

**Maintained by** Sysadmin and BU admins. **Read by** every list/picker in inventory-bearing modules.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Assign user to location | User-edit → **Locations** tab → Add | Pick location from BU catalogue |
| Reassign storekeeper | Soft-delete old row + insert new | Open documents continue to work (FKs target `tb_location`) |
| View user's effective scope | User-edit → **Locations** tab | Shows current active assignments |
| Remove all scope (full access) | Soft-delete all rows | Empty set = "no restriction" by convention |
| Audit scope changes | [[reporting-audit/activity]] log | Filter by `entity_type = user_location` |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| User cannot see expected location | Missing `tb_user_location` row OR empty-set convention not applied | Add row or confirm service code behaviour |
| Duplicate assignment error | `(user_id, location_id)` exists | Reactivate the existing row instead |
| "Location not in this BU" | Location belongs to a different BU | Pick a location from the user's active BU |
| Orphan `user_id` after platform-user deletion | Cross-schema, no FK enforcement | Run maintenance job to clean stale rows |

## 4. Edge Cases

- **Empty-set semantics.** Conventionally "no row-level restriction" — confirm with service code if relying on this default for a sensitive path.
- **Cross-schema integrity.** `user_id` references platform `tb_user.id` but is **not** a Prisma FK — application validates on insert.
- **Per-document overrides.** This table is the **default scope** for pickers; specific workflows may broaden (e.g. an approver in [[store-requisition]] needs both source and destination).
- **Reassignment is two ops.** Soft-delete A row, insert B row — open documents keep working.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_user_location`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | References platform `tb_user.id`; not a Prisma FK (cross-schema). |
| `location_id` | `String @db.Uuid` | No | FK to tenant `tb_location`. |
| `note` | `String? @db.VarChar` | Yes | Assignment context. |
| `info` | `Json? @db.JsonB` | Yes | Default `{}`. Reserved metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, location_id, deleted_at])`. Index on `(user_id, location_id)`. FK to `tb_location` `onDelete: NoAction`. `user_id` enforced application-side.

## 6. Business Rules

- **Uniqueness.** A user has at most one active assignment per location.
- **Empty-set semantics.** Conventionally "no row-level restriction" — code paths needing explicit assignment must check `count > 0`.
- **Cross-schema integrity.** Application validates `user_id` on insert; maintenance job cleans up after user deletion.
- **Deletion guards.** Hard-delete allowed (no transactional FK targets); soft-delete preserves audit.
- **Lifecycle.** Reassignment is two operations (soft-delete + insert); document-level FKs target `tb_location`, so open work is preserved.
- **Per-document overrides.** Default scope only — specific workflows may broaden or narrow.

## 7. Cross-References

- [[inventory]] — list and movement screens filter by user's set.
- [[store-requisition]] — issue/requesting locations validated against scope.
- [[physical-count]], [[spot-check]] — count documents restricted to user's locations.
- [[master-data/location]] — the location side.
- [[access-control/user]] — the user side.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_user_location` (lines ~4451-4470).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/user-role/` — Locations tab.
