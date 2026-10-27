---
title: User Location (tb_location_user)
description: Per-user location scoping inside a tenant — restricts a user to a subset of inventory locations. Table renamed tb_user_location → tb_location_user on 2026-09-04; edited via PATCH /api/config/:bu_code/users/:user_id.
published: true
date: 2026-10-27T00:00:00.000Z
tags: access-control, user-location, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# User Location (`tb_location_user`)

> **At a Glance**
> **Owner:** Sysadmin / BU Admin &nbsp;·&nbsp; **Table:** `tb_location_user` (tenant; **renamed from `tb_user_location` on 2026-09-04**) &nbsp;·&nbsp; **Edited via:** `PATCH /api/config/:bu_code/users/:user_id { location_id: { add[], remove[] } }` (2026-09-04) or `PUT /api/config/:bu_code/locations-users/:userId` (replace list) &nbsp;·&nbsp; **Read by:** [inventory](/en/inventory/inventory), [store-requisition](/en/inventory/store-requisition), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check), and the workflow product-location picker &nbsp;·&nbsp; Row-level location filter — restricts inventory rows visible to the user.

![User Location (tb_location_user) screen](/screenshots/access-control/user-location.png)

## Rename notice (2026-09-04)

Tenant migration `20260904131500_rename_shelf_and_user_location` (BE `d49a81b34`) renamed `tb_user_location` → `tb_location_user` (and `tb_shelf` → `tb_location_shelf`) so the table name reads "location's users" like its sibling `tb_location_shelf`, `tb_location_product`. The migration is metadata-only (`ALTER TABLE … RENAME`, constraint `tb_user_location_pkey` → `tb_location_user_pkey`, FK `…_location_id_fkey` renamed, indexes `user_location_*` → `location_user_*`). The Prisma model is `tb_location_user` (`schema.prisma`, `@@unique([user_id, location_id, deleted_at]) map "location_user_user_id_location_id_u"`). Gateway paths did **not** change: `api/config/:bu_code/locations-users` (`locationUser.*` api names) still exists. **Correction 2026-10-27:** the sibling `api/config/:bu_code/user-locations` (`userLocation.getUsersByLocationId` / `managerUserLocation`) that this page listed as "still existing" was a gateway module that was **never registered** in the app and has been deleted as dead code (BE `d5829efd3`, 2026-10-05; Bruno `config/user-location/` archived under `_archived/2026-10-07`) — those two calls never reached a handler. The caller's own scope is `GET api/:bu_code/user-locations` (`application/user-locations/`), which is unaffected. This wiki slug (`user-location`) is kept.

## Implementation status (re-verified 2026-10-27)

- **No behaviour change** in the table, endpoints or error codes since 2026-09-22. `tb_location_user` is unchanged in `schema.prisma` (`:5594`); `config_users.controller.ts`, the location-user service and the `USER_ACCESS_LOCATION_*` catalog entries differ from the last pass only by the project-wide `platform` → `backstage` rename (BE `cb78788a6`, `c820b5064`).
- **Edit-mode registry is loaded through `useLocationAll`** (FE `0bac08d4`): the Locations section still fetches the BU's whole location register only when **Edit** is pressed (`enabled: !isDisabled`), now via the shared "list all" helper instead of `perpage=-1`. View mode shows the locations that arrive with the user (`GET …/users/:user_id`). The location-type filter, checkbox grid and diff-only `PATCH` are unchanged.
- **Layout:** the user form now sits in `FormPageShell` + `FormToolbar` (FE `7c9bc0ae`); the Save button is outside the `<form>` and references it by `form="user-assigned-form"`. No change to what is saved.

## 1. What & Who

`user-location` narrows a user's effective scope from "all locations" to "this subset". A storekeeper assigned to two storerooms should only see those two in their location pickers, count documents, and adjustment screens. The table is a simple many-to-many between [access-control/user](/en/inventory/access-control/user) and [master-data/location](/en/inventory/master-data/location) with an active-only soft-delete pattern.

Unlike [access-control/application-role](/en/inventory/access-control/application-role) (which gates **actions**) and [access-control/business-unit-user](/en/inventory/access-control/business-unit-user) (which gates **BU entry**), `user-location` is a **row-level data filter** — it restricts visible rows without changing roles or permissions. An empty set is conventionally interpreted as "no restriction".

One consumer is now explicit in code: `GET api/config/:bu_code/workflows/:workflow_id/products/:product_id/locations` (2026-09-03) returns the locations where a product may be used under a workflow *for the calling user* — the intersection of `tb_workflow.data.products`, `tb_product_location`, and the caller's `tb_location_user` rows; "the caller holds none of its locations" is an empty array, not an error (Bruno `GET-find-product-locations-config-workflows.bru`). See [system-config/workflow](/en/inventory/system-config/workflow).

**Maintained by** Sysadmin and BU admins. **Read by** every list/picker in inventory-bearing modules.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Assign user to locations | User Assign screen (`/system-admin/user/:id`) → **Edit** → **Locations** section (`user-assigned-locations.tsx`) → tick locations → Save | Since 2026-08-27 (`96e569ad`) the section is a `DataGrid` with a checkbox per row, search, sort and a type filter (Inventory / Direct / Consignment), not the two-panel Transfer control this page used to describe; the form diffs the ticked set and sends only `{ location_id: { add, remove } }` (`buildUserPatch`, `user-assigned-form-schema.ts:63-77`) |
| Reassign storekeeper | Untick A, tick B → Save | One `PATCH`; open documents continue to work (FKs target `tb_location`) |
| View user's effective scope | Same screen, view mode | `GET /api/config/:bu_code/users/:user_id` → `locations[{ id, location_id, location_code, location_name, location_type, is_active }]` |
| Replace one user's whole location list | `PUT /api/config/:bu_code/locations-users/:userId` (`locationUser.managerLocationUser`) | Bruno `config/locations-user/`; no dedicated screen. There is **no** location-keyed variant (the `…/user-locations/:locationId` route listed here before was never registered and is deleted) |
| Remove all scope (full access) | Untick every location, Save | Empty set = "no restriction" by convention (confirm with the consuming service before relying on this for a sensitive path) |
| Audit scope changes | [reporting-audit/activity](/en/inventory/reporting-audit/activity) log | Filter by entity type |

**History:** between 2026-09-03 (`2ee5b2c1`, locations made view-only on the user screen) and 2026-09-07 (`39ae1bba`, editing re-enabled through the new single-request user endpoint) the user screen could not change locations; the `locations-users` PUT was the only path.

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| User cannot see expected location | Missing `tb_location_user` row OR empty-set convention not applied | Add row or confirm service code behaviour |
| `USER_ACCESS_LOCATION_ADD_REMOVE_CONFLICT` | The same location id in both `add` and `remove` | Fix the payload |
| `USER_ACCESS_LOCATIONS_TO_ADD_NOT_FOUND` / `…_TO_REMOVE_NOT_FOUND` | Unknown location id, or removing an assignment that does not exist | Reload and retry (`packages/error-catalog/src/catalog.ts:366-386`; `…_ADD_REMOVE_CONFLICT` is HTTP 400) |
| `USER_ACCESS_LOCATION_WRITE_FAILED` | Tenant write failed after the backstage side succeeded | Retry; report if persistent |
| `USER_ACCESS_NO_CHANGES` | `PATCH` body contained no effective change | Nothing to do |
| Orphan `user_id` after backstage-user deletion | Cross-schema, no FK enforcement | Run maintenance job to clean stale rows |

## 4. Edge Cases

- **Empty-set semantics.** Conventionally "no row-level restriction" — confirm with service code if relying on this default for a sensitive path.
- **Cross-schema integrity.** `user_id` references backstage `tb_user.id` (`prisma-shared-schema-backstage`, renamed from the platform schema in BE `c820b5064`) but is **not** a Prisma FK — application validates on insert.
- **Two write paths, one table.** The user-side `PATCH` (add/remove diff) and the `locations-users/:userId` `PUT` (replace list) both write `tb_location_user`; the `PATCH` is transactional across backstage (roles) and tenant (locations) writes and reports the tenant failure as `USER_ACCESS_LOCATION_WRITE_FAILED`.
- **Per-document overrides.** This table is the **default scope** for pickers; specific workflows may broaden (e.g. an approver in [store-requisition](/en/inventory/store-requisition) needs both source and destination).
- **Reassignment is two ops.** Soft-delete A row, insert B row — open documents keep working.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_location_user`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `user_id` | `String @db.Uuid` | No | References backstage `tb_user.id`; not a Prisma FK (cross-schema). |
| `location_id` | `String @db.Uuid` | No | FK to tenant `tb_location`. |
| `note` | `String? @db.VarChar` | Yes | Assignment context. |
| `info` | `Json? @db.JsonB` | Yes | Default `{}`. Reserved metadata. |
| `doc_version` | `Int` | No | Default `0`. Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([user_id, location_id, deleted_at])` (`location_user_user_id_location_id_u`). Index `location_user_user_id_location_id_idx`. FK to `tb_location` `onDelete: NoAction`. `user_id` enforced application-side.

### 5.2 API surface

```
GET   /api/config/:bu_code/users/:user_id                  configUser.getAccess   → locations[] (+ roles, department)
PATCH /api/config/:bu_code/users/:user_id                  configUser.patchAccess { location_id: { add[], remove[] } }
GET   /api/config/:bu_code/locations-users/:userId         locationUser.getLocationByUserId
PUT   /api/config/:bu_code/locations-users/:userId         locationUser.managerLocationUser
GET   /api/:bu_code/user-locations                         userLocation.findAll (caller's own scope)
GET   /api/:bu_code/user-locations/product/:product_id     locations.findAllByProductId
GET   /api/:bu_code/user-locations/:user_location_id       (application/user-locations, `:206`)
```

Licence route keys `config:locations-users`, `config:user-locations` (now orphaned — its controller is gone), `app:user-locations` all map to `configuration.location` (`packages/prisma-shared-schema-backstage/prisma/permission.route-map.ts:180,190,203` — the file moved with the platform → backstage package rename).

## 6. Business Rules

- **Uniqueness.** A user has at most one active assignment per location.
- **Empty-set semantics.** Conventionally "no row-level restriction" — code paths needing explicit assignment must check `count > 0`.
- **Cross-schema integrity.** Application validates `user_id` on insert; maintenance job cleans up after user deletion.
- **Deletion guards.** Hard-delete allowed (no transactional FK targets); soft-delete preserves audit.
- **Lifecycle.** Reassignment is two operations (soft-delete + insert); document-level FKs target `tb_location`, so open work is preserved.
- **Per-document overrides.** Default scope only — specific workflows may broaden or narrow.

## 7. Cross-References

- [inventory](/en/inventory/inventory) — list and movement screens filter by user's set.
- [store-requisition](/en/inventory/store-requisition) — issue/requesting locations validated against scope.
- [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check) — count documents restricted to user's locations.
- [system-config/workflow](/en/inventory/system-config/workflow) — `…/products/:product_id/locations` picker.
- [master-data/location](/en/inventory/master-data/location) — the location side; shelves are `tb_location_shelf` after the same migration.
- [access-control/user](/en/inventory/access-control/user) — the user side and the single-request access endpoint.

## 8. References

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location_user`; migration `20260904131500_rename_shelf_and_user_location`.
- **Gateway:** `../carmen-turborepo-backend/apps/backend-gateway/src/config/config_users/config_users.controller.ts` (`PATCH :user_id` `:64`, `GET :user_id` `:149`; swagger `request.ts` `ConfigUserAccessPatchRequest`, `response.ts` `ConfigUserAccessLocationDto`); `config/config_locations-users/` (`GET`/`PUT :userId` `:60`/`:119`); `application/user-locations/` (`GET` `:69`, `GET product/:product_id` `:130`). `config/config_user-locations/` no longer exists.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/users/{GET-get-access,PATCH-patch-access}-config-users.bru`, `config/locations-user/` (the `config/user-location/` folder is archived).
- **Frontend:** `../carmen-frontend/routes/system-admin/user/user-assigned-locations.tsx` (DataGrid + checkbox), `user-assigned-form.tsx`, `user-assigned-form-schema.ts` (`buildUserPatch`), `types/user.ts` (`UserLocation`, `UpdateUserPayload`).
