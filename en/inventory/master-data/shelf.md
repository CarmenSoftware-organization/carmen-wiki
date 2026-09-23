---
title: Shelf
description: BU-wide shelf master (walk order for counts) assigned per product-location row — added 2026-08, decoupled from location on 2026-08-20.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: master-data, shelf, location, configuration, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# Shelf

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_location_shelf` &nbsp;·&nbsp; **Used by:** product ↔ location assignment (`tb_product_location.shelf_*`) &nbsp;·&nbsp; **Permission:** `configuration.location_shelf.{view,create,update,delete}` &nbsp;·&nbsp; **Licence key:** `configuration.location_shelf` &nbsp;·&nbsp; A BU-wide list of shelves / racks with a `sequence_no` walk order; **not** scoped to a location despite the table name.

## 1. What & Who

**Shelves** name the physical rack, bin, or bay a product sits on inside a storage location — "Dry Rack A1", "Walk-in door shelf", "Bar back-shelf 3". The master is one flat list per business unit; the *assignment* of a shelf to a product at a location lives on the junction row `tb_product_location` (`shelf_id` + denormalised `shelf_code` / `shelf_name`). `sequence_no` is the order a counter walks the shelves, so a count sheet can follow the real route through the store.

The entity had a short, three-step history that explains its odd name:

| Date | Change | Migration |
| --- | --- | --- |
| 2026-08-14 | Created **location-scoped** as `tb_location_shelf` with `location_id` FK and `(location_id, code)` / `(location_id, name)` uniqueness; `shelf_*` columns added to `tb_product_location` | `20260814150000_add_location_shelf` |
| 2026-08-20 | Backend "แยก shelf เป็น master ของตัวเอง" — `location_id` dropped, uniqueness becomes BU-wide, table renamed `tb_shelf`; frontend removed its location column/picker in the same week (`d447559f`) | `20260820120000_rename_location_shelf_to_shelf` |
| 2026-09-04 | Table renamed **back** to `tb_location_shelf` (index names `location_shelf_*`) with no column change; HTTP path stays `/shelves`, permission/licence keys stay `configuration.location_shelf` | `20260904131500_rename_shelf_and_user_location` |

So today: **one shelf list per BU, reusable at any location.** The frontend's Location Assignment tab still clears the chosen shelf when the location changes (`pd-tab-locations.tsx:197-198`, comment "shelf ผูกกับ location") — that is a UI convenience, not a backend rule. **Maintained by** Product Admin under Configuration → Shelf (`/config/shelf`). **Read by** the product form, the location `products[]` payload, and (by intent, not yet by code) physical count / spot check.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a shelf | Configuration → Shelf → **New** (dialog) | Required: `code`, `name`; optional `description`, `sequence_no` (integer ≥ 1 in the frontend Zod schema; nullable integer on the API), `is_active` (default `true`) |
| Put a product on a shelf | Product → **Location Assignment** tab → **Shelf** column (`LookupShelf`, lists active shelves only) | Sends `locations.add[] / update[].shelf_id`; backend copies `code`/`name` onto the junction row |
| Same, from the location side | API only — `PATCH /locations/:id` `products.add[] / update[].shelf_id` | The location form's product transfer list has no shelf picker |
| Clear a shelf assignment | Send `shelf_id: null` on the product-location row | Omit the field to leave it unchanged |
| See what is on a shelf | `GET /api/config/:bu_code/shelves/:id` | Detail adds `product_count` + `products[]` (`product_code`, `product_name`, `product_local_name`, `product_sku`, `location_code`, `location_name`) sorted by product code (`shelf.helper.ts:16-70`); the list endpoint carries no products |
| Deactivate | Toggle `is_active` | Hidden from the product form's lookup (`lookup-shelf.tsx:41` filters `is_active`); existing assignments keep their snapshot |
| Delete | **Delete** action | **Blocked** while any live `tb_product_location` row references the shelf — one of the few master-data delete guards that actually exists |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `409 SHELF_ALREADY_EXISTS` — "Shelf with this code or name already exists" | Another non-deleted shelf has the same `code` **or** the same `name` (case-insensitive, `shelf.service.ts` `create()` / `update()`) | Pick a different code *and* name |
| `404 SHELF_NOT_FOUND` | Unknown or soft-deleted id on update/delete — or, from the product / location endpoints, a `shelf_id` in `locations[]` / `products[]` that does not resolve (`resolveShelfAssignments`) | Use a live shelf id or `null` |
| `409 SHELF_IN_USE` — "Shelf is still assigned to products and cannot be deleted" | `delete()` counts `tb_product_location` rows with `shelf_id = id AND deleted_at IS NULL` | Move or clear the assignments first |
| `409` on PATCH/PUT with stale `doc_version` | Optimistic lock — `update({ where: { id, doc_version } })` | Reload and resend |
| "Sequence must be at least 1" | Frontend Zod (`shelf-form-schema.ts`) — blank is sent as `undefined`, not `0` | Leave blank to let the backend default (`1`) apply |

## 4. Edge Cases

- **Name uniqueness is as strict as code uniqueness.** Both `location_shelf_code_u` and `location_shelf_name_u` are DB-unique (with `deleted_at`), and the service checks both case-insensitively before insert — two locations cannot each have a shelf called "Top shelf"; name them "KIT Top shelf" / "BAR Top shelf".
- **`sequence_no` is not unique** and defaults to `1`, so a freshly created list has every shelf at position 1; the list sorts `sequence_no:asc, code:asc, id:asc` (`withDefaultSort`), which makes code the effective tiebreaker.
- **Bruno sample body is stale.** `config/location-shelves/POST-create-config-location-shelves.bru` still shows a `location_id` in `body:json` from the 2026-08-14 contract; the request DTO (`common/dto/shelf/shelf.dto.ts`) has no such field and the docs block of the same file correctly says shelves are BU-wide.
- **Count code does not read shelves yet.** A grep of `apps/micro-business/src/inventory/` for `shelf` finds only the stock-card / wastage serializers echoing `shelf_code`; neither physical-count nor spot-check orders lines by `sequence_no`. Treat "count sheets follow walk order" as design intent.
- **Snapshot vs. live name.** `tb_product_location.shelf_name` is copied at assignment time; renaming a shelf does not refresh existing rows (no backfill code found — same pattern as `delivery_point_name` on locations).
- **E2E is mostly deferred.** `tests/083-shelf.spec.ts` runs 2 smoke/error-state cases; the CRUD block (`TC-SHLF-030001…`) is `test.fixme` "deferred until backend endpoint is live" even though the endpoint now exists.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`, line ~1441).

### 5.1 `tb_location_shelf`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`). |
| `code` | `String @db.VarChar` | No | Short code, e.g. `A-01`. |
| `name` | `String @db.VarChar` | No | Display name, e.g. `Dry Rack A1`. |
| `description` | `String?` | Yes | Free text. |
| `sequence_no` | `Int?` | Yes | Walk order for counts; default `1`. |
| `is_active` | `Boolean?` | Yes | Active flag, default `true`. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata (`{}` / `[]` defaults). |
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, deleted_at])` map `location_shelf_code_u`; `@@unique([name, deleted_at])` map `location_shelf_name_u`. Indexes `location_shelf_code_idx`, `location_shelf_name_idx`. Reverse relation `tb_product_location[]` (FK `tb_product_location.shelf_id`, `onDelete: NoAction`, index `product_location_shelf_id_idx`). No `location_id` column.

### 5.2 Assignment columns on `tb_product_location`

| Field | Prisma Type | Description |
| --- | --- | --- |
| `shelf_id` | `String? @db.Uuid` | FK → `tb_location_shelf.id`; nullable because not every location is shelved. |
| `shelf_code` / `shelf_name` | `String? @db.VarChar` | Denormalised copies written by `shelfColumns()` (`master/shelf/shelf.helper.ts:149`) whenever `shelf_id` is set. |

## 6. Business Rules

- **Uniqueness.** `code` and `name` each unique among non-deleted rows, DB-enforced and pre-checked case-insensitively in the service.
- **Deletion guard — confirmed.** `delete()` returns `SHELF_IN_USE` while any live product-location row references the shelf; otherwise soft-deletes (`is_active: false`, `deleted_at`).
- **Referential check on assignment.** Product create/update (`products.service.ts:2035`, `:2244`) and location update (`locations.service.ts:~1290`) resolve every supplied `shelf_id` against live shelves first and fail the whole request with `SHELF_NOT_FOUND` if any is unknown.
- **Lifecycle.** `is_active = false` hides the shelf from the product form lookup; historical assignments keep `shelf_code` / `shelf_name`.
- **Default sort.** `sequence_no:asc, code:asc, id:asc` when no `?sort=` is sent.
- **Optimistic lock.** PATCH/PUT require the current `doc_version`.
- **Access.** Gateway guards: `KeycloakGuard` + `PermissionGuard` on the controller, `AppIdGuard('shelf.*')` per handler; permission rows `configuration.location_shelf:{view,create,update,delete}` are seeded (`seed.permission.data.ts:895-910`), licence feature `configuration.location_shelf` (`seed.license-feature.data.ts:268`), route map `config:shelves → configuration.location_shelf`. The frontend menu entry requires `.view`.

## 7. Cross-References

- [master-data/location](/en/inventory/master-data/location) — the junction row a shelf is assigned on; § 5.3 there.
- [product](/en/inventory/product) — the **Location Assignment** tab is the only UI that sets a shelf ([product/03-user-flow-product-admin](/en/inventory/product/03-user-flow-product-admin) step 9).
- [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check) — intended consumers of `sequence_no`; no code path yet.
- [inventory](/en/inventory/inventory) — stock card rows echo `shelf_code` where the junction row has one.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location_shelf` (line ~1441), `tb_product_location` (~5334).
- **Migrations:** `20260814150000_add_location_shelf`, `20260820120000_rename_location_shelf_to_shelf`, `20260904131500_rename_shelf_and_user_location`.
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/shelf/shelf.service.ts`, `shelf.helper.ts`; gateway `apps/backend-gateway/src/config/config_shelves/` (`@Controller('api/config/:bu_code/shelves')`), DTO `common/dto/shelf/`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/location-shelves/*.bru` (6 requests, URL `/api/config/{{bu_code}}/shelves`).
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/shelf/`, `components/lookup/lookup-shelf.tsx`, `types/shelf.ts`; menu `constant/module-list.ts` (`/config/shelf`).
- **E2E:** `../carmen-inventory-frontend-e2e/tests/083-shelf.spec.ts` (2 executable + deferred CRUD), `docs/user-stories/083-shelf.md` (8 cases).
