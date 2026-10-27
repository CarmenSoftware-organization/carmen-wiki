---
title: Cost Center
description: Cost-center groups, cost centers, and the per-center chart-of-accounts allow-list (tb_cost_center_group / tb_cost_center / tb_cost_center_account) — now with list screens, an optional group, a Carmen GL department import, and an in-use delete guard.
published: true
date: 2026-10-27T00:00:00.000Z
tags: master-data, cost-center, general-ledger, configuration, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# Cost Center

> **At a Glance**
> **Owner:** Sysadmin / Finance &nbsp;·&nbsp; **Tables:** `tb_cost_center_group` → `tb_cost_center` → `tb_cost_center_account` &nbsp;·&nbsp; **Used by:** [general-ledger](/en/inventory/general-ledger) JV lines on accounts flagged `is_require_cost_center` &nbsp;·&nbsp; **Permissions:** `configuration.cost_center_group.*`, `configuration.cost_center.*` &nbsp;·&nbsp; **Licence keys:** `configuration.cost_center_group`, `configuration.cost_center` &nbsp;·&nbsp; **UI:** `/config/cost-center` and `/config/cost-center-group` (list + dialog; no allow-list editor).

## 1. What & Who

A **cost center** is the accounting dimension a GL journal line is charged to — an outlet, a kitchen, a revenue centre. It is deliberately **not** the same thing as a [department](/en/inventory/master-data/department): `tb_department` is the organisational unit users belong to and PR/SR documents are raised from; `tb_cost_center` is the GL dimension (schema comment: "ศูนย์ต้นทุน/ศูนย์รายได้ทางบัญชี — คนละความหมายกับ tb_department"). Cost centers are grouped in `tb_cost_center_group` (with a display `color_tag`), and each cost center may carry an **account allow-list** — the subset of the [chart of accounts](/en/inventory/master-data/chart-of-accounts) it is allowed to post to. An empty allow-list means every account is allowed.

Added 2026-09-04 (`20260904103000_add_cost_center`, backend design spec `docs/superpowers/specs/2026-09-04-cost-center-schema-design.md` in the backend repo) as part of the GL-core build-out. **Frontend screens now exist** (corrects the 2026-09-22 "no frontend route" statement): Configuration → **Cost Center** (`/config/cost-center`, licence `configuration.cost_center`) and **Cost Center Group** (`/config/cost-center-group`, licence `configuration.cost_center_group`), each a list with a create/edit dialog (`routes/config/cost-center/`, `routes/config/cost-center-group/`). The cost-center dialog edits `code`, `name`, `cost_center_group_id`, `description`, `note`, `is_active`; the group dialog edits `code`, `name`, `description`, `note`, `is_active` (no `color_tag`). **Neither screen can edit the account allow-list** — `PUT …/accounts` is still API-only.

Two more things changed in the 2026-10 window: a cost center **no longer needs a group** (migration `20261016120000_cost_center_group_optional` drops `NOT NULL`; the dialog sends `null` for "no group"), and a [location](/en/inventory/master-data/location) can now point at a cost center (`tb_location.cost_center_id`), which becomes the default cost center in [chart-of-account-mapping](/en/inventory/master-data/chart-of-account-mapping). **Maintained by** Sysadmin / Finance. **Read by** the GL JV posting validation, account mapping and the accounting export.

## 2. Common Tasks

| Task | Where (API) | Notes |
|---|---|---|
| Create a group | `POST /api/config/:bu_code/cost-center-groups` | `code`, `name` required; `description`, `color_tag` (free text, e.g. `#FF8800`), `is_active` optional |
| Create a cost center | **New** (dialog) / `POST /api/config/:bu_code/cost-centers` | `code`, `name` required; `cost_center_group_id` **optional** (null = ungrouped); optional `description`, `is_active`, `chart_of_accounts_ids[]` (initial allow-list, created in the same transaction — API only) |
| Pull from Carmen GL | **Import from Carmen GL** button on the list (`cost-center-import-carmen-gl-button.tsx`) → `POST …/cost-centers/import-from-interface/carmen-gl` | Reads Carmen 4 **departments** (`DeptCode`, `Description`) and reconciles them into cost centers in one transaction. Button renders only when the BU's `accounting.carmen_gl` interface entitlement is `entitled` and the user can write. Policy (`on_duplicate` skip / upsert / error, `on_local_only` keep / delete) comes from the app-config `interface_accounting_carmen_gl.sync_policy`, never from the request. Upsert touches only `name` / `is_active`, never group, description or allow-list. Result `{ total_rows, created, updated, skipped, deleted, in_use, errors }` plus `deleted_codes`, `in_use_codes` |
| Replace the allow-list | `PUT /api/config/:bu_code/cost-centers/:id/accounts` `{ chart_of_accounts_ids: [] }` | Whole-set replace: ids no longer wanted are soft-deleted, new ids inserted, duplicates in the request collapsed. Empty list = allow all accounts |
| Move a cost center to another group (or remove it from one) | `PATCH …/cost-centers/:id` with `cost_center_group_id` | Group must exist and be live; `null` removes the group |
| List | `GET …/cost-centers`, `GET …/cost-center-groups` | Rows carry the group **flat** as `cost_center_group_code` / `cost_center_group_name` (`cost-center.service.ts:31-33`) — this pair was written before the 2026-09-17 nested-object convention and has not been converted |
| Deactivate | `is_active = false` on either level | — |
| Delete a group | `DELETE …/cost-center-groups/:id` | **Blocked** while any live cost center references it |
| Delete a cost center | `DELETE …/cost-centers/:id` | **Guarded since 2026-10:** refused with `409 COST_CENTER_IN_USE` (payload `{ locations, account_mappings, accounting_records }`) while any live location, account-mapping row, JV detail / JV-template detail / budget detail, GL balance, AP-payment expense or AP/AR invoice-detail line references it. Otherwise soft-deletes the center **and** its `tb_cost_center_account` rows in one transaction |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `409 COST_CENTER_GROUP_DUPLICATE_CODE` / `409 COST_CENTER_DUPLICATE_CODE` | Another non-deleted row has the same `code` (service pre-check + partial unique indexes `costcentergroup_code_live_u` / `costcenter_code_live_u`) | Pick a different code |
| `404 COST_CENTER_GROUP_NOT_FOUND` | Unknown group id on group read/update/delete, **or** an unknown / deleted `cost_center_group_id` on cost-center create/update (`assertGroupExists`) | Use a live group |
| `404 COST_CENTER_NOT_FOUND` | Unknown cost-center id | — |
| `404 COST_CENTER_ACCOUNT_NOT_FOUND` — "One or more chart of accounts entries in the mapping do not exist" | Any id in `chart_of_accounts_ids` is not a live `tb_chart_of_accounts` row (`assertAccountsExist`) | Remove the bad id |
| `409 COST_CENTER_GROUP_IN_USE` — "Cost center group is still referenced by cost centers" | `delete()` on a group counts live `tb_cost_center` rows (`{ cost_centers: n }` in the error payload) | Move or delete the cost centers first |
| `409 COST_CENTER_IN_USE` — "Cost center is still used by locations, account mappings or accounting records" | `delete()` counts references (`countReferences`); the GL/AP/AR tables reference cost centers without an FK, which is why the check is in code | Remove the references (or deactivate instead) |
| `400 COST_CENTER_IMPORT_REJECTED` / `COST_CENTER_IMPORT_EMPTY` / `…_TOO_MANY_ROWS` / `…_INTERFACE_NOT_CONFIGURED` / `…_DISABLED` / `…_MULTI_PAGE` / `…_TOKEN_UNREADABLE`, `502 COST_CENTER_INTERFACE_REQUEST_FAILED` | Carmen GL import: empty `DeptCode` / `Description`, code > 50 chars, duplicate code within the response, or (policy `error`) a code that already exists → whole import rejected, failing rows in `data.errors` (cap 100); interface not configured / disabled / paged / token unreadable; upstream non-2xx | Fix the source data or interface config; nothing is written on rejection |
| `409` on PATCH/PUT with stale `doc_version` | Optimistic lock | Reload |

## 4. Edge Cases

- **Allow-list semantics are "replace", not "add".** `setAccounts` diffs the current live rows against the requested set; sending `[]` clears the list (which *widens* what the center may post to — every account becomes allowed). Test both directions.
- **Cost-center delete is now guarded** (corrects "not enforced" from 2026-09-22): `COST_CENTER_IN_USE` covers locations, account-mapping rows and seven GL/AP/AR reference tables. `tb_gl_balance` and `tb_ap_payment_expense` have no `deleted_at`, so *every* row counts. Import with `on_local_only = delete` skips in-use centers and reports them in `in_use_codes` instead of failing.
- **Import never sets a group.** Imported cost centers are created ungrouped (`cost_center_group_id` null) — which is only legal since the group became optional.
- **Location default.** A location with no `cost_center_id` shows a warning-coloured "Not assigned" label in the location list; account-mapping rows for it report `missing_cost_center` until an override or a location cost center exists.
- **Partial unique indexes live only in SQL.** The three `*_live_u` indexes (`WHERE deleted_at IS NULL`) are not in the Prisma model; the model shows the looser `(code, deleted_at)` / `(cost_center_id, chart_of_accounts_id, deleted_at)` uniques. A table rename needs a hand-written `ALTER INDEX … RENAME` (schema comment).
- **`color_tag` is unvalidated text.** Any string is stored; the `#RRGGBB` form in the Bruno sample is a convention.
- **Where the allow-list bites.** The rule "JV line on an `is_require_cost_center` account must carry a cost center that is in the account's allow-list" is documented on `tb_chart_of_accounts.is_require_cost_center` and enforced by the GL JV service — see [general-ledger](/en/inventory/general-ledger); nothing in this module's services validates JV lines.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`, lines ~2976-3063).

### 5.1 `tb_cost_center_group`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | e.g. `FB`. |
| `name` | `String @db.VarChar` | No | e.g. `Food & Beverage`. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `color_tag` | `String? @db.VarChar` | Yes | Display colour hint. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `note`, `info` | — | Yes | Standard metadata (no `dimension` on this table). |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, deleted_at])` map `costcentergroup_code_u`; partial unique `costcentergroup_code_live_u`; indexes on `code`, `name`. Reverse relation `tb_cost_center[]`.

### 5.2 `tb_cost_center`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | e.g. `FB-01`. |
| `name` | `String @db.VarChar` | No | e.g. `Main Restaurant`. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `cost_center_group_id` | `String? @db.Uuid` | Yes | FK → `tb_cost_center_group` (`onDelete: NoAction`); nullable since `20261016120000_cost_center_group_optional`. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, deleted_at])` map `costcenter_code_u`; partial unique `costcenter_code_live_u`; indexes `costcenter_code_idx`, `costcenter_name_idx`, `costcenter_group_id_idx`. Reverse relation `tb_cost_center_account[]`.

### 5.3 `tb_cost_center_account`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `cost_center_id` | `String @db.Uuid` | No | FK → `tb_cost_center` (`onDelete: NoAction`). |
| `chart_of_accounts_id` | `String @db.Uuid` | No | FK → `tb_chart_of_accounts` (`onDelete: NoAction`). |
| `doc_version` | `Int` | No | Optimistic-lock version. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. No `note` / `info` / `is_active`. |

**Constraints:** `@@unique([cost_center_id, chart_of_accounts_id, deleted_at])` map `costcenteraccount_u`; partial unique `costcenteraccount_live_u`; indexes on each FK.

## 6. Business Rules

- **Uniqueness.** `code` unique among non-deleted rows at both levels (service pre-check + partial unique index). One allow-list row per `(cost_center, account)`.
- **Referential checks on write.** When a group is given it must exist (`assertGroupExists`); every allow-list account must exist (`assertAccountsExist`).
- **Deletion guards.** Group: blocked while live cost centers reference it. Cost center: blocked while referenced (`COST_CENTER_IN_USE`); otherwise cascades its own allow-list rows. Allow-list rows: replaced wholesale by `PUT :id/accounts`.
- **Allow-list meaning.** Empty = all accounts allowed; non-empty = only listed accounts, and only when the account itself is flagged `is_require_cost_center`.
- **Lifecycle.** `is_active = false` at either level; soft-delete sets `deleted_at` (+ `is_active: false`).
- **Default sort.** `code:asc, id:asc` on both list endpoints (`withDefaultSort`, 2026-09-13).
- **Optimistic lock.** Update / patch require `doc_version`.
- **Access.** Route map `config:cost-center-groups → configuration.cost_center_group`, `config:cost-centers → configuration.cost_center`; permission rows seeded (`seed.permission.data.ts:983-1015`); licence features `configuration.cost_center`, `configuration.cost_center_group` (`seed.license-feature.data.ts:164-172`). Handlers use `AppIdGuard('cost-centers.*')` incl. `cost-centers.setAccounts`.

## 7. Cross-References

- [chart-of-accounts](/en/inventory/master-data/chart-of-accounts) — allow-list target; `is_require_cost_center` is the flag that makes a cost center mandatory.
- [general-ledger](/en/inventory/general-ledger) — JV line validation and posting.
- [chart-of-account-mapping](/en/inventory/master-data/chart-of-account-mapping) — cost-center overrides per mapping row; location default.
- [master-data/location](/en/inventory/master-data/location) — `cost_center_id` default.
- [master-data/department](/en/inventory/master-data/department) — the *organisational* unit; not interchangeable with a cost center.

## 8. References

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_cost_center_group` (line ~2976), `tb_cost_center` (~3005), `tb_cost_center_account` (~3037).
- **Migrations:** `20260904103000_add_cost_center`, `20261014100100_account_mapping` (adds `tb_location.cost_center_id`), `20261016120000_cost_center_group_optional`.
- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/master/cost-center/cost-center.service.ts` (`setAccounts`, `countReferences` / `countReferencesMany`, `delete`, `importFromInterfaceCarmenGl`; import row mapping in `cost-center.import.ts`; shared Carmen fetch in `master/carmen-gl-interface/carmen-gl-interface.ts`), `master/cost-center-group/cost-center-group.service.ts`; gateway `apps/backend-gateway/src/config/config_cost-centers/` (`@Controller('api/config/:bu_code/cost-centers')`, `PUT :cost_center_id/accounts` `:396`), `config_cost-center-groups/`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/cost-centers/*.bru` (7 incl. `PUT-set-accounts-*`), `config/cost-center-groups/*.bru` (6).
- **Frontend:** `../carmen-frontend/routes/config/cost-center/` (`cost-center-dialog.tsx`, `cost-center-import-carmen-gl-button.tsx`, `use-cost-center-table.tsx`), `routes/config/cost-center-group/`, `constant/api-endpoints.ts:170-180`.
- **E2E:** none found.
