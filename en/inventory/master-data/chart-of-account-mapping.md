---
title: Chart of Account Mapping
description: The location x item-group x movement table that decides which GL account and cost center an inventory movement (GRN, credit note, adjustment, store requisition) is exported against - resolution order, override rules, generate, review, and the API.
published: true
date: 2026-10-27T00:00:00.000Z
tags: master-data, account-mapping, chart-of-accounts, general-ledger, configuration, carmen-software
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Chart of Account Mapping

> **At a Glance**
> **Owner:** Sysadmin / Finance &nbsp;·&nbsp; **Table:** `tb_account_mapping` + `enum_account_mapping_{type,movement,origin}` &nbsp;·&nbsp; **Route:** `/config/chart-of-account-mapping` (tabs **AP** / **GL**) &nbsp;·&nbsp; **API:** `api/:bu_code/account-mapping` &nbsp;·&nbsp; **Permission:** `configuration.chart_of_account_mapping.*` &nbsp;·&nbsp; **Licence key:** `configuration.chart_of_account_mapping` &nbsp;·&nbsp; Replaces the earlier read-only mock screen (the "no gateway endpoint" note on the previous version of this module landing page is obsolete).

## 1. What & Who

Inventory documents carry no GL account. The **account mapping** is the lookup that says, for a stock movement at a *location* of a product in an *item group*, which account to debit/credit and which cost center to charge. One row exists per **location x item group x movement** (plus **adjustment type** for adjustments). Rows store only what a user *overrode*; the displayed account and cost center are **resolved** each time from the product classification tree and the location.

| Tab (`mapping_type`) | Movements | What the row decides |
|---|---|---|
| **AP** | `grn`, `cn` | The payable-side account of a goods-receipt / credit-note (the other side of the inventory debit) |
| **GL** | `grn`, `cn`, `sr_in`, `sr_out`, `adjustment` | The inventory/direct-side account of the same movements, the store-requisition in/out legs, and one row per adjustment type for stock-in/out adjustments |

The only live consumer found is the external export API (`GET api/ext/v1/gl-journals` for SR / stock-in / stock-out, `GET api/ext/v1/ap-invoices` for GRN / CN), which calls `AccountMappingService.resolveKeys` through `export-core.service.ts` - **read-only, never creates rows**. `resolveForPosting` (insert missing keys with `origin = auto_posting`, `is_reviewed = false`) exists but its own comment says it has **no caller yet**. In-app inventory posting still writes no ledger entries (see [general-ledger/gl-posting](/en/inventory/general-ledger/gl-posting)).

**Maintained by** Sysadmin / Finance. **Read by** the accounting export; the cost center default comes from [location](/en/inventory/master-data/location) and the account defaults from the [product category tree](/en/inventory/product/category).

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create the rows | **Generate** button (dialog) -> `POST /generate` `{ mode: used \| all, mapping_type? }` | `used` = only (location, item group) pairs that already appear on a product-location, GRN, CN, stock-in/out or SR line; `all` = every active non-consignment location x every active item group. Omitting `mapping_type` generates both tabs. Existing rows are never touched (`ON CONFLICT DO NOTHING`); response `{ created, existing }` per tab. Generated rows start `is_reviewed = true` |
| Find gaps | Status chips: **Incomplete**, **Unreviewed**, **Overridden**, **Default** | Counts cover the whole tab, not the page; the tab badge shows the incomplete count |
| Override one row | Row -> edit sheet -> `PATCH :id` `{ account_code?, cost_center_id?, doc_version }` | `null` = clear the override and fall back to the default; omitted = unchanged. Saving marks the row reviewed |
| Override many rows | Select rows -> **Edit selected** -> `POST /batch-update` | One value applied to up to 100 rows; saves what it can (see § 3) |
| Mark reviewed | Select rows -> **Mark reviewed** -> `POST /review` `{ ids }` (1-100) | Only flips rows that are still unreviewed |
| Dry-run a key | `POST /resolve` `{ lines: [...] }` (1-500 keys) | Read-only; keys with no row are resolved virtually |

List filters: location (multi), location type (`inventory` / `direct`), category, sub-category, item group, movement, adjustment type (multi), status, free-text search over the resolved account code, location code/name and item-group code/name. Sortable columns: `location`, `location_type`, `category`, `sub_category`, `item_group`, `movement`, `adjustment_type`, `cost_center`, `account` (any other `sort` value is a 400). `perpage` is clamped to 1-100. The filter bar does not hide inactive locations / categories (a row may point at something since disabled).

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `422 ACCOUNT_MAPPING_ACCOUNT_INVALID` | `account_code` is not an active [chart-of-accounts](/en/inventory/master-data/chart-of-accounts) code (`is_active` true or null) | Pick a live account |
| `422 ACCOUNT_MAPPING_COST_CENTER_INVALID` | `cost_center_id` unknown or inactive | Pick a live [cost center](/en/inventory/master-data/cost-center) |
| `404 ACCOUNT_MAPPING_NOT_FOUND` | Unknown row id on `PATCH` | Reload the list |
| `COMMON_DOC_VERSION_REQUIRED` / `409` | `PATCH` without a numeric `doc_version`, or a stale one (optimistic lock) | Reload and retry |
| Batch result `{ updated, conflicts, not_found }` | Per-row `doc_version` mismatch -> `conflicts`; deleted -> `not_found`. An invalid target value fails the **whole** batch with 422 before any row is written | The UI keeps the failed rows selected and reports a partial result |
| Row shows an **issue** badge | `missing_inventory_account`, `missing_direct_account` (no account at item group, sub-category or category for that location type), `missing_ap_account`, `missing_adjustment_account` (AP and adjustment rows have *no* default), `account_not_in_coa` (resolved code does not exist in the COA), `missing_cost_center` (no override and the location has none) | Set the account on the category tree, the cost center on the location, or override the row |

## 4. Edge Cases

- **Resolution order (account).** GL rows for `grn` / `cn` / `sr_in` / `sr_out`: row override -> item group -> sub-category -> category, reading the **Inventory** account for an `inventory` location and the **Direct** account for a `direct` location (`tb_product_account_code_mapping`, `account_type` `inventory` / `direct`). **AP rows and GL `adjustment` rows take the override only** - there is no fallback to the vendor, the BU default, the adjustment type, or the product account (commit `db3544c76` removed those fallbacks). `tb_adjustment_type.chart_of_accounts_id` and `tb_vendor.ap_chart_of_accounts_id` therefore do not feed this table.
- **Resolution order (cost center).** Row override -> the location's `cost_center_id`. No further fallback.
- **Consignment locations are skipped** by the resolver (`skip = true`) and are never generated.
- **Defaults are live, overrides are sticky.** Changing a category's account changes every non-overridden row at once; overridden rows keep their value. Use **Overridden** to find the exceptions.
- **Cascade from the category tree.** Saving an account on a category / sub-category / item group can overwrite the same account type on every descendant (and product) when the user confirms the cascade dialog - see [product/category](/en/inventory/product/category) § 2. That changes what these rows resolve to.
- **Generate `used` is a snapshot.** A new location x item group pair that first appears later has no row until **Generate** is run again (or, once wired, until posting auto-creates it).
- **`origin`** records how a row was born: `generated_all`, `generated_used`, `auto_posting`.
- **No inventory costing impact.** Cost layers, valuation and the stock ledger never read this table.

---

## 5. Data Model (Dev)

Source: tenant schema, migrations `20261014100100_account_mapping` and `20261016140000_account_mapping_contra_defaults`.

### 5.1 `tb_account_mapping`

| Field | Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `UUID` | No | Primary key. |
| `mapping_type` | `enum_account_mapping_type` | No | `AP` \| `GL`. |
| `location_id` | `UUID` FK -> `tb_location` | No | |
| `product_item_group_id` | `UUID` FK -> `tb_product_item_group` | No | |
| `movement` | `enum_account_mapping_movement` | No | `grn` \| `cn` \| `adjustment` \| `sr_in` \| `sr_out`. |
| `adjustment_type_id` | `UUID` FK -> `tb_adjustment_type` | Yes | Required exactly when `movement = adjustment` (`accountmapping_adjustment_type_ck`). |
| `account_code` | `VARCHAR` | Yes | The **override**; plain code string, no FK to `tb_chart_of_accounts` (validated on write only). |
| `cost_center_id` | `UUID` FK -> `tb_cost_center` | Yes | The cost-center override. |
| `origin` | `enum_account_mapping_origin` | No | `generated_all` \| `generated_used` \| `auto_posting`. |
| `is_reviewed` | `Boolean` | No | Default `false`. |
| `doc_version` | `Int` | No | Optimistic lock, default `0`. |
| Audit columns | - | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `accountmapping_type_movement_ck` - AP pairs with `grn` / `cn` only; GL pairs with any of the five movements (relaxed by `…_contra_defaults`; the original migration allowed GL only `adjustment`, `sr_in`, `sr_out`). Partial unique index `accountmapping_key_live_u` on `(mapping_type, location_id, product_item_group_id, movement, COALESCE(adjustment_type_id, nil-uuid)) WHERE deleted_at IS NULL`. Indexes on `(mapping_type, location_id)` and `product_item_group_id`.

Related columns added in the same migrations: `tb_location.cost_center_id` (FK -> `tb_cost_center`, index `location_cost_center_id_idx`), `enum_account_type` value `direct`, `tb_adjustment_type.chart_of_accounts_id` (no FK).

## 6. Business Rules

- **Overrides are validated at write time only** (active COA code / active cost center). A later-deactivated account stays on the row; `account_not_in_coa` is raised when the resolved code has no row in `tb_chart_of_accounts` at all.
- **Optimistic locking** on `PATCH` and per item on batch update; `review` and `generate` are not versioned.
- **Access.** Gateway `@Controller('api/:bu_code/account-mapping')` with `KeycloakGuard` + `PermissionGuard` on resource `configuration.chart_of_account_mapping` (`view` for list/resolve, `update` for patch/review/batch-update, `create` for generate) and `AppIdGuard('account-mapping.*')`; route-map entry `app:account-mapping`; the menu entry is licence-gated.
- **Status definitions.** *Incomplete* = resolved account or cost center is null; *Overridden* = a non-empty `account_code` or a `cost_center_id` on the row; *Default* = neither; *Unreviewed* = `is_reviewed = false`. Counts ignore the status filter but honour all other filters.

## 7. Cross-References

- [chart-of-accounts](/en/inventory/master-data/chart-of-accounts) - the codes an override must exist in.
- [cost-center](/en/inventory/master-data/cost-center) and [location](/en/inventory/master-data/location) - the default cost center lives on the location.
- [product/category](/en/inventory/product/category) - where the Inventory / Direct account defaults are set and cascaded.
- [adjustment-type](/en/inventory/master-data/adjustment-type) - one GL row per adjustment type.
- [general-ledger/gl-posting](/en/inventory/general-ledger/gl-posting) - the JV posting engine that inventory does not call yet.

## 8. References

- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/master/account-mapping/` (`account-mapping.resolver.ts` - resolution rules and status flags; `account-mapping.service.ts` - `findAll` `:211`, `update` `:500`, `review` `:535`, `batchUpdate` `:554`, `generate` `:615`, `resolve` `:706`, `resolveForPosting` `:720`; `dto/account-mapping.dto.ts`); gateway `apps/backend-gateway/src/application/account-mapping/account-mapping.controller.ts`; consumer `apps/micro-business/src/inventory/accounting-export/export-core.service.ts`; error catalog `ACCOUNT_MAPPING_*`.
- **Migrations:** `20261014100100_account_mapping`, `20261014100000_account_type_direct`, `20261016140000_account_mapping_contra_defaults`.
- **Frontend:** `../carmen-frontend/routes/config/chart-of-account-mapping/` (`coam-component.tsx`, `use-account-mapping.ts`, `coam-generate-dialog.tsx`, `coam-edit-sheet.tsx`, `coam-batch-edit-sheet.tsx`, `coam-filter-fields.ts`), `types/chart-of-account-mapping.ts`.
- **E2E:** `../carmen-frontend-e2e/tests/081-chart-of-account-mapping.spec.ts` (not reviewed this pass). **Bruno:** no `account-mapping` request found.
