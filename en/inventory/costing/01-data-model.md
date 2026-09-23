---
title: Costing — Data Model
description: Entities, fields, relationships, and enums for the costing module.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: costing, data-model, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — Data Model

> **At a Glance**
> **Tables:** `tb_inventory_transaction_cost_layer` &nbsp;·&nbsp; `tb_inventory_transaction_detail` &nbsp;·&nbsp; `tb_inventory_period_snapshot` (renamed from `tb_period_snapshot`, `20260916141000_rename_tb_period_to_tb_inventory_period`) &nbsp;·&nbsp; `tb_business_unit.calculation_method` &nbsp;·&nbsp; `tb_product.standard_cost`
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** cost-layer `→ tb_inventory_transaction_detail`; cost-layer `→ tb_inventory_period` (`period_id`, `schema.prisma:1217`); detail `→ tb_good_received_note_detail_item` (`good_received_note_detail_item_id`, since 2026-08-10); cross-schema link: tenant cost-layer reads platform `tb_business_unit.calculation_method` via the `bu_code` of the request (no Prisma `@relation`)
> **Re-verified 2026-09-22:** new column `tb_inventory_transaction_cost_layer.extra_cost_amount` (`20260910130000_add_cost_layer_extra_cost`); `tb_period*` → `tb_inventory_period*`; average is per **product**, not per `(location, product)`; ledger `cost_per_unit` is rounded to **2 dp**; lot numbers are `<location_code><YYMM><run>`.
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*` on cost-layer and snapshot; **`tb_inventory_transaction_detail` has no soft-delete** — reversal posts a compensating row instead

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The Costing module is **not a separate document tree** in the way GRN, PR, or SR are. It is a **read-and-write contract layered over the inventory transaction ledger**: the engine reads `tb_inventory_transaction_detail` and `tb_inventory_transaction_cost_layer` to pick the cost for an outbound movement, writes `cost_per_unit` / `average_cost_per_unit` / `extra_cost_amount` onto the cost-layer rows at post time, and reads back from the same rows when downstream consumers (recipe costing, financial reporting, valuation, the `GET …/cost/products/:id/*` endpoints) need a unit cost. There is no `tb_costing_*` model in the canonical Prisma schema — costing data lives on the inventory entities (`tb_inventory_transaction_cost_layer` is the canonical cost-flow record, `tb_inventory_transaction_detail.cost_per_unit` is the per-line cost, `tb_inventory_period_snapshot.closing_cost_per_unit` is the period-end locked unit cost) and the **costing-method configuration** lives one level up at the **business unit** in the platform schema, not on the product.

The cost-flow assumption — **FIFO** (lots consumed by `lot_seq_no` ascending, each carrying its own `cost_per_unit`) or **Weighted Average** (single moving average **per product**, refreshed on every inbound and re-stamped on every live layer of that product — **corrected 2026-09-22**, the average is not per `(location_id, product_id)`: `getNetTotals(tx, productId)` in `inventory-transaction.service.ts:1487-1509` ignores location) — is configured on `tb_business_unit.calculation_method` (platform `enum_calculation_method = average | fifo`, default `average`) at the property level. Note the **tenant** schema also declares an `enum_calculation_method { FIFO, AVG }` (`schema.prisma:39-42`) that the engine does not use — the code imports the platform enum (`inventory-transaction.service.ts:2`). The tenant schema's `enum_business_unit_config_key` exposes `calculation_method` as a runtime config key, and `enum_physical_count_costing_method` (`standard`, `last`, `average`, `last_receiving`) selects which cost source feeds count-driven variance posts. The product itself (`tb_product`) carries `standard_cost` (the reference cost used by the `standard` count-costing method and by recipe baselining) and `price_deviation_limit` / `qty_deviation_limit` (percent ceilings that the GRN **save** checklist enforces against the PO line — [good-receive-note/02-business-rules](/en/inventory/good-receive-note/02-business-rules) `GRN_VAL_006`/`007`), but it does **not** carry a per-product costing method — that is a deliberate platform-wide simplification documented in Section 5.

The engine runs **per-transaction, not as a periodic batch**. When a GRN posts (commit on FIFO units, save on average units), the engine receives one item per receipt event with `received_base_qty`, `foc_base_qty`, `base_net_amount`, and `base_extra_cost_amount` (`ICreateFromGrnDetailItem`, `inventory-transaction.service.ts:44-56`), writes one `tb_inventory_transaction_detail` (`qty = received + FOC`, `cost_per_unit = Round2(total / qty)`, `current_lot_no = <location_code><YYMM><run>`, `good_received_note_detail_item_id`) and one or more cost layers (`splitFifoCost(qty, totalCost, 2)` reconciles the exact decimal total across `lot_index` rows; the extra-cost share is split across the same rows into `extra_cost_amount`), assigns the period-scoped `lot_seq_no`, and — average units only — recomputes and re-stamps `average_cost_per_unit`. When an outbound movement posts, the engine reads the configured method, picks the cost (FIFO consumes from `lot_seq_no` ascending; WA reads the product's current average), and writes the corresponding outbound `out_qty × cost_per_unit` rows. At period close, the engine writes `closing_cost_per_unit` on `tb_inventory_period_snapshot` (average units) and `transaction_type = close_period` / `open_period` cost-layer rows that anchor the period-boundary unit cost. The sibling [`calculation-methods.md`](./calculation-methods.md) is the deep-dive on the FIFO / WA algorithms and the platform's strategy-pattern design recommendation; this page is the schema-level catalogue.

## 2. Entities

### 2.1 tb_inventory_transaction_cost_layer (canonical cost record)

The **cost-flow ledger row** — the single source of truth for "what did this unit cost?" at every point in time. One row per layer event per movement: inbound rows create a new layer with `in_qty > 0`, `cost_per_unit`, `lot_no`, `lot_index`, `lot_seq_no`; outbound rows consume a layer with `out_qty > 0`, `from_lot_no` resolved by FIFO ordering on `lot_seq_no`, and `cost_per_unit` picked from the consumed layer (FIFO) or from the current moving average (WA). The row also persists `average_cost_per_unit` so weighted-average consumers can read the post-movement moving average without re-aggregating the whole history. `at_period` (`YYMM`) and `period_id` tie the layer to an accounting period so the period-end rollup can sum activity per period.

This entity is owned by the [inventory](/en/inventory/inventory) module — full field catalogue at [inventory/01-data-model](/en/inventory/inventory/01-data-model) § 2.3. The costing module's perspective: this is the table the engine reads at every outbound (to pick `cost_per_unit`) and writes at every inbound (to set `cost_per_unit` and recompute `average_cost_per_unit`).

**Costing-relevant fields:**

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Per-unit cost on this layer event; default `0`. For GRN inbound layers: the **landed** cost `Round2((base_net_amount + base_extra_cost_amount) / (received_base_qty + foc_base_qty))` — stored at 5 dp but computed to **2 dp** (`inventory-transaction.service.ts:941,1134`); adjustment-in: the document's cost. For outbound layers: the cost picked by the costing rule — under FIFO, the consumed layer's cost; under WA, the product average at post time. The canonical "what did this unit cost" field. |
| `extra_cost_amount` | `Decimal @db.Decimal(20, 5)` | Yes | **New 2026-09-10** (`20260910130000_add_cost_layer_extra_cost`). The part of this layer's `total_cost` that came from the receipt's extra cost (freight, handling, duty) rather than the goods themselves, in base currency; default `0`. Written once when the receipt posts (`splitByWeight(base_extra_cost_amount, layer quantities)`, `:971-974,996`) and never edited — the schema comment calls it "a record of a decision already made". `total_cost − extra_cost_amount` is the goods-only value. |
| `average_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Post-movement moving-average unit cost **of the product across all locations** (corrected 2026-09-22); default `0`. Refreshed by every inbound under WA and **re-stamped on every live, non-direct layer of the product** (`:1236-1247`, `restampAverageCostForProducts` `:1521-1543`) so reports read it without recomputing. Outbound movements **do not** change it. **Under FIFO a GRN receipt writes `0` here** (`:998`) — there is no shadow average on FIFO units. Direct-location layers always carry `0`. |
| `lot_seq_no` | `Int` | Yes | Run number **within the inventory period** (`getNextLotSeqNo(tx, atPeriod)` takes `max(lot_seq_no) + 1` over `at_period`, `:1399-1406`), not within `(location, product)`; default `1`. It is also the last four digits of `lot_no`. Lower `lot_seq_no` is consumed first under FIFO. Preserved across period boundaries by the `open_period` rollforward so FIFO sequence survives close. |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Variance amount used for credit-note-amount adjustments (vendor concedes a price reduction post-receipt — the `cost_per_unit` of the originating lot is recalculated per `INV_CALC_011`) and for end-of-period price revaluation; default `0`. Carries cost-only variance independent of `in_qty` / `out_qty`. |
| `in_qty` / `out_qty` | `Decimal @db.Decimal(20, 5)` | Yes | The quantity side of the layer event; `total_cost = (in_qty or out_qty) × cost_per_unit`. Mutually exclusive on a single row per `INV_VAL_007`. |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `(in_qty − out_qty) × cost_per_unit` (signed); default `0`. The journal-entry amount for the layer event. |
| `transaction_type` | `enum_transaction_type` | Yes | Cost-flow classifier — `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period`. Drives which cost-pick rule the engine applies. |
| `at_period` | `String @db.VarChar` | Yes | Period in `YYMM` form (denormalised from `tb_inventory_period.period`). Costing aggregations group by this column to produce period-bounded COGS / valuation totals. |
| `period_id` | `String @db.Uuid` | Yes | FK to `tb_inventory_period.id` (`@relation`, `schema.prisma:1217`) — the inventory period containing this layer event. **Corrected 2026-09-22:** for a GRN the period is resolved from `grn_date` **by date range** (`resolvePeriodForDate` → `findOpenPeriodForDate`, `inventory-period.helper.ts`), never by deriving a name from the date, and the write **throws** when no `open`/`locked` period covers the date; issues / adjustments still use the current open period (`resolveCurrentPeriod`). |
| `lot_no` | `String @db.VarChar` | Yes | `<location_code><YYMM><4-digit run>` — e.g. `MK-0126070246` — from `buildLotNo()` (`common/helpers/lot-number.helper.ts:27-35`). **Corrected 2026-09-22:** not `RC{YY}{MM}{seq}`; no document-type prefix; identical across every movement type. |

Other fields (`lot_index`, `parent_lot_no`, `location_id`, `product_id`, audit columns) are listed in full at [inventory/01-data-model](/en/inventory/inventory/01-data-model) § 2.3.

**Costing-relevant constraints:** `@@unique([lot_no, lot_index])` enforces lot identity; the cost-pick algorithm relies on `lot_seq_no` ordering within the location's lots for FIFO and on the product-wide `average_cost_per_unit` for WA. `cost_per_unit` and `average_cost_per_unit` are non-negative per `INV_VAL_007`.

### 2.2 tb_inventory_transaction_detail (per-line cost ledger)

The **per-product / per-lot ledger line** under a movement. Carries `qty`, `cost_per_unit`, `total_cost`, the location, the lot-trace fields `from_lot_no` / `current_lot_no`, and — since `20260810180000_move_grn_lot_link_to_ledger` — `good_received_note_detail_item_id`, the receipt event this inbound row came from (`NULL` for adjustments / transfers / legacy rows). The costing module reads this row to confirm the cost-per-unit posted with a specific source-document line (a GRN row carries `cost_per_unit` = **landed cost after extra-cost allocation, over received + FOC quantity** — confirmed live 2026-09-22; an SR issue line carries `cost_per_unit = picked cost`); it is the user-facing reflection of the cost-layer's cost and what `GET …/good-received-notes/:id/stock-movements` returns.

**Costing-relevant fields:**

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Unit cost at posting; default `0`. For inbound, the layer cost (drives the cost-layer row's `cost_per_unit`; GRN: `Round2((base_net_amount + extra-cost share) / (received_base_qty + foc_base_qty))`); for outbound, the engine-picked cost. **This is the value visible on the GRN's Stock Movement tab.** |
| `good_received_note_detail_item_id` | `String @db.Uuid` | Yes | FK to `tb_good_received_note_detail_item.id` (`@relation`, `schema.prisma:1135,1150`; index `inventorytransactiondetail_grndetailitemid_idx`). The receipt event that produced this row; the same id may appear on several rows if one event ever splits into several lots. `NULL` = not from a GRN. |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | Signed quantity in base UoM; positive = inbound (for GRN: `received_base_qty + foc_base_qty` — FOC units are on hand at the diluted cost), negative = outbound. Multiplied by `cost_per_unit` to produce `total_cost`. |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit` (signed); default `0`. The journal-entry amount on the detail line. |
| `from_lot_no` | `String @db.VarChar` | Yes | Source lot consumed (outbound). Set by the FIFO pick — points to the lot whose `lot_seq_no` was lowest with non-zero remaining balance. |
| `current_lot_no` | `String @db.VarChar` | Yes | Lot newly created or affected (inbound). Carries the new layer's lot identity into the cost-layer row's `lot_no`. |

Other fields and constraints listed in full at [inventory/01-data-model](/en/inventory/inventory/01-data-model) § 2.2.

### 2.3 tb_inventory_period_snapshot (period-locked unit cost)

**Renamed** from `tb_period_snapshot` by `20260916141000_rename_tb_period_to_tb_inventory_period` (together with `tb_period → tb_inventory_period`, `tb_period_comment → tb_inventory_period_comment`; HTTP path `/inventory-periods`, permission / licence key `system_admin.inventory_period`). The **locked opening / closing balance row per `(period_id, location_id, product_id, lot_no, lot_index)`**. Written at period close as the audit anchor — **average-method business units only** (`period-end.close-average.helper.ts:480`). From the costing perspective, this row is **the period-end valuation answer** — it carries `closing_qty`, `closing_cost_per_unit`, and `closing_total_cost` that the balance sheet and food-cost reports consume.

**Costing-relevant fields:**

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `opening_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Opening unit cost for the period — typically the prior period's `closing_cost_per_unit`. |
| `opening_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `opening_qty × opening_cost_per_unit`. The balance-sheet opening valuation. |
| `receipt_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Sum of inbound `in_qty × cost_per_unit` during the period; default `0`. |
| `issue_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Sum of outbound `out_qty × cost_per_unit` during the period — the **COGS bucket** at the period × location × product × lot grain. |
| `adjustment_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Net adjustment cost (sum of `adjustment_in / adjustment_out / credit_note_*` layers including `diff_amount`). |
| `closing_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Closing unit cost — for WA, the period-end weighted average; for FIFO, the residual lot's `cost_per_unit` (per `INV_CALC_010`). |
| `closing_total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `closing_qty × closing_cost_per_unit`. The locked balance-sheet valuation; written once and never edited. |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Variance bucket (typically from physical-count adjustments captured in the period); summed into `adjustment_total_cost`. |

Other fields listed at [inventory/01-data-model](/en/inventory/inventory/01-data-model) § 2.7.

### 2.4 tb_business_unit.calculation_method (costing-method configuration — platform)

The **costing-method configuration**. Held at the business-unit (property / hotel) level on the **platform schema**, not on the tenant schema and not on the product. Single value applies to every product at that business unit.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `calculation_method` | `enum_calculation_method` | No | Costing method for the business unit. Values: `average` (Weighted Average — default), `fifo` (First-In-First-Out). Read by the inventory cost-layer post engine at every outbound to decide the cost-pick rule. |

`tb_business_unit` is defined in `prisma-shared-schema-platform/prisma/schema.prisma:191` (not in the tenant schema where `tb_inventory_transaction_cost_layer` lives). The cost-layer post engine reads this value by the request's `bu_code` (`getCalculationMethod(bu_code)`, `inventory-transaction.service.ts:402-408`, falling back to `fifo` when the row has no value) and applies the picked rule to the cost-layer write. The tenant schema's `enum_business_unit_config_key` enumerates `calculation_method` as a config key — a parallel runtime-config surface (key/value rows) that the engine does **not** read. The GRN module also reads the method (`postsInventoryAtSave()`) to decide whether a receipt posts at save (average) or commit (FIFO).

### 2.5 tb_product.standard_cost (reference cost on the product)

The **product's reference / standard cost**. Used by the `standard` count-costing method (`enum_physical_count_costing_method = standard` — count variance is valued at the product's `standard_cost` rather than the cost-layer cost) and by recipe baseline costing.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `standard_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Reference / standard cost per unit in base UoM; default `0`. Updated by Finance / cost-controller cadence (typically monthly or quarterly). Not used by the FIFO / WA cost-pick engine — those read the cost-layer's `cost_per_unit` / `average_cost_per_unit`. |
| `price_deviation_limit` | `Decimal @db.Decimal(20, 5)` | Yes | **Percent** ceiling, enforced (since 2026-08) by the GRN save checklist: received price per base unit may exceed the PO's `order_price` per base unit by at most this percent (`good-received-note.deviation.ts:98-116`); `0` / `NULL` = no ceiling. Not consumed by the cost-pick engine itself. |
| `qty_deviation_limit` | `Decimal @db.Decimal(20, 5)` | Yes | **Percent** ceiling on `received_base_qty` over `order_base_qty`, enforced at GRN save (`deviation.ts:125-134`); shortfalls never breach it. |

`tb_product` is documented in full under the [product](/en/inventory/product) module; this entry covers the costing-relevant subset.

### 2.7 Cost read endpoints (gateway `application/cost`)

Not a table, but the only costing-specific API surface (`apps/backend-gateway/src/application/cost/cost.controller.ts`, micro-business `src/inventory/costing/`; Bruno `_uncategorized/cost/`). All read-only, `KeycloakGuard` + `AppIdGuard`:

| Endpoint | Guard key | Returns |
| -------- | --------- | ------- |
| `GET /api/:bu_code/cost/products/:product_id/location/:location_id/qty/:qty` | `product.cost-estimate` | Cost estimate for issuing `qty` from that location under the BU's method |
| `GET /api/:bu_code/cost/products/:product_id/last-receiving` | `product.last-receiving` | Most recent GRN receipt of the product |
| `GET /api/:bu_code/cost/products/:product_id/last-cost` | `product.last-cost` | Most recent inbound (`good_received_note` **or** `stock_in`) — "last cost regardless of receiving source" |
| `GET /api/:bu_code/cost/products/:product_id/last-receiving/unit/:unit_id` | `product.last-receiving-by-unit` | Most recent GRN received in that unit, `cost_per_unit = net_amount / received_qty` (per received unit, **before** extra cost); `{}` if never received in that unit |

**Cost centres (`tb_cost_center`, `tb_cost_center_group`, `tb_cost_center_account`, `20260904103000_add_cost_center`)** are **not** linked to costing: no inventory or costing table carries `cost_center_id` — the only FK is `tb_gl_jv_detail.cost_center_id` (`schema.prisma:4505`); inventory rows carry only the free-form `dimension` JSON array.

### 2.6 enum_physical_count_costing_method (count-variance valuation source)

A four-value enum that selects **which cost source feeds count-driven variance posts** when a physical-count or spot-check completes with variance. This is a costing-specific concern because count adjustments (`adjustment_in` / `adjustment_out`) need a `cost_per_unit` to compute `total_cost`, and the source of that cost varies by tenant preference.

| Value | Cost source |
| ----- | ----------- |
| `standard` | The product's `tb_product.standard_cost`. Used by tenants who want count variance valued at the reference cost regardless of recent receipt prices. |
| `last` | The most recent cost-layer's `cost_per_unit` at `(location_id, product_id)` regardless of direction. Approximates "current market cost". |
| `average` | The product's current `average_cost_per_unit`. For WA-configured business units, equals the running average; on FIFO units GRN receipts write `0` into that column (no shadow average is maintained — corrected 2026-09-22), so this option is only meaningful on average units. |
| `last_receiving` | The most recent **inbound** layer's `cost_per_unit` (filtered to `transaction_type ∈ {good_received_note, adjustment_in, transfer_in}`). Approximates "the last price we paid". |

Configured per business unit (typically via `tb_business_unit_config_key = physical_count_costing_method`), read by the count-variance posting code at the moment of writing the `tb_stock_in` / `tb_stock_out` document derived from a completed count.

## 3. Relationships

```
tb_business_unit (platform schema)
    │  calculation_method ∈ {average, fifo}  ── single costing method per business unit
    │
    │  Read by the cost-layer post engine via the x-app-id / JWT business-unit context.
    │  No Prisma @relation to tenant entities — cross-schema reference.
    ▼

tb_inventory_transaction  (info JSON on GRN headers: { posted_at_save, po_receiving_applied })
    │ * inventory_transaction_id
    ▼
tb_inventory_transaction_detail
    │  cost_per_unit (landed cost, 2 dp)
    │  qty (signed) ── total_cost = qty × cost_per_unit  (GRN: qty = received + FOC)
    │  good_received_note_detail_item_id ──► tb_good_received_note_detail_item (receipt event)
    │
    │ * inventory_transaction_detail_id
    ▼
tb_inventory_transaction_cost_layer  (canonical cost-flow record)
    │  cost_per_unit            ── layer cost (FIFO: per-lot; WA: per-event)
    │  extra_cost_amount        ── share of total_cost that is freight/duty (GRN only, 2026-09-10)
    │  average_cost_per_unit    ── product-wide moving average (WA units; 0 on FIFO receipts)
    │  lot_no = <location_code><YYMM><lot_seq_no>
    │  lot_seq_no               ── period-scoped run number; FIFO consumes lowest-first
    │  diff_amount              ── credit-note-amount / EOP revaluation variance
    │  in_qty / out_qty         ── direction; mutually exclusive
    │  transaction_type ∈ {good_received_note, transfer_in, transfer_out,
    │                       issue, adjustment_in, adjustment_out,
    │                       credit_note_amount, credit_note_quantity,
    │                       eop_in, eop_out, close_period, open_period}
    │  at_period (YYMM) / period_id ── ties layer to the inventory period
    │
    └──► tb_inventory_period   (period_id → close_period / open_period rollforward anchor)


tb_product
    │  standard_cost           ── reference cost (used by count-costing-method = standard)
    │  price_deviation_limit   ── tolerance band (informational)
    │  qty_deviation_limit     ── tolerance band (informational)
    │
    │  No per-product costing_method field — single method per business unit.
    │
    │ * product_id (no @relation declared on cost-layer / detail)
    ▼
tb_inventory_transaction_cost_layer / tb_inventory_transaction_detail
    (cost-layer rows reference product_id but no Prisma @relation)


tb_inventory_period ──1──*──► tb_inventory_period_snapshot
                                         (locked period × location × product × lot
                                          opening / receipt / issue / adjustment /
                                          closing cost columns — the period-end
                                          valuation anchor; average units only)
```

Notes:

- **Configuration cross-schema gap.** The costing-method enum value lives on `tb_business_unit.calculation_method` in the **platform** schema, but the cost-layer rows that consume it live in the **tenant** schema. There is no Prisma `@relation` bridging the two; the engine resolves it by the request's `bu_code` (`getCalculationMethod(bu_code)`). The costing module's read path is therefore: `(tenant: inventory transaction post) → (bu_code) → (platform query: tb_business_unit.calculation_method) → apply cost-pick rule`.
- **Runtime-config key is not read by the engine.** `enum_business_unit_config_key.calculation_method` exists, but `getCalculationMethod` reads only the platform column (`inventory-transaction.service.ts:402-408`). Treat the config key as unused for costing until a reader appears.
- **Average is product-wide.** `getNetTotals` / `restampAverageCostForProducts` filter by `product_id` only; a receipt at one location changes the average used for issues at every location of the business unit.
- **No `tb_costing_*` entity.** The costing module is structurally **a layer of behaviour over inventory entities**, not its own document tree. This is intentional: keeping the cost on the same row as the qty (on `tb_inventory_transaction_cost_layer`) means there can be no drift between the qty ledger and the cost ledger — they are the same ledger.
- **Cost-pick is movement-time, not query-time.** When an outbound posts, the engine resolves the cost at post time and writes it to the cost-layer's `cost_per_unit`. Subsequent reads of the row return that historical cost — even if the configured method changes later, posted rows preserve the cost picked under the method in effect at the time. This is the audit-defence property: every COGS figure traces back to a specific cost-layer row written at a specific moment under a specific method.
- **Period-snapshot is the locked answer.** Once `tb_inventory_period_snapshot.closing_cost_per_unit` is written by `INV_POST_009` (period close, average units), the period's valuation is immutable; subsequent corrections to the closed period post as restatements in a later open period, not by editing the snapshot.
- **`standard_cost` is reference-only.** It does **not** drive FIFO or WA cost-pick. It drives the `standard` count-costing method (count variance valued at standard) and recipe baseline costing. Tenants who want count variance valued at the running average configure `physical_count_costing_method = average` instead.

## 4. Enums

- **`enum_calculation_method`** (platform schema, `prisma-shared-schema-platform/prisma/schema.prisma:133-136`): costing-method classifier on `tb_business_unit.calculation_method`. Two values, default `average`:
  - `average` — Weighted Average. Single moving average **per product** (all locations), refreshed on every inbound per `INV_CALC_007`; outbound consumes at the prevailing average per `INV_CALC_006`. Also makes GRNs post their stock movement at **save**.
  - `fifo` — First-In, First-Out. Lots consumed by `lot_seq_no` ascending per `INV_CALC_005`; each consumed lot produces its own outbound cost-layer row at its `cost_per_unit`. GRNs post at **commit**.
  - Note: the **tenant** schema separately declares `enum_calculation_method { FIFO, AVG }` (`prisma-shared-schema-tenant/prisma/schema.prisma:39-42`); the engine imports the platform enum and never reads the tenant one.
- **`enum_business_unit_config_key`** (tenant schema): enumerates runtime-config keys on `tb_business_unit_config_key` rows. Costing-relevant values:
  - `calculation_method` — declared, but **not read by the costing engine** (see § 3 notes).
  - `physical_count_costing_method` — selects the cost source for count-driven variance posts (values per `enum_physical_count_costing_method`).
  - `amount`, `quantity`, `recipe` — formatting / precision config keys (separate concern but configured at the same surface).
- **`enum_physical_count_costing_method`** (tenant schema): count-variance valuation source. Four values, no schema default declared:
  - `standard` — value count variance at `tb_product.standard_cost`.
  - `last` — value at the most recent cost-layer `cost_per_unit` at the `(location, product)` key, regardless of direction.
  - `average` — value at the most recent `average_cost_per_unit` (running WA).
  - `last_receiving` — value at the most recent inbound layer's `cost_per_unit` (filter `transaction_type ∈ {good_received_note, adjustment_in, transfer_in}`).
- **`enum_transaction_type`** (tenant schema): cost-flow effect on `tb_inventory_transaction_cost_layer.transaction_type`. Twelve values listed at [inventory/01-data-model](/en/inventory/inventory/01-data-model) § 4; costing-engine-relevant subset:
  - `good_received_note` / `transfer_in` / `adjustment_in` — inbound layer events the engine writes a fresh `cost_per_unit` to (and recomputes `average_cost_per_unit` for WA).
  - `issue` / `transfer_out` / `adjustment_out` — outbound events the engine picks a cost for (FIFO or WA).
  - `credit_note_amount` — vendor concession adjusting `cost_per_unit` on an existing lot via `diff_amount` (per `INV_CALC_011`).
  - `credit_note_quantity` — outbound consuming from the originating receipt's lot at the lot's `cost_per_unit`.
  - `eop_in` / `eop_out` — end-of-period rollforward (the engine writes `closing_cost_per_unit` / `opening_cost_per_unit` for the period anchor).
  - `close_period` / `open_period` — period-anchor rows; cost preserved across the boundary so FIFO sequence and WA running-average survive close.

## 5. Divergences from carmen/docs

The carmen/docs costing reference (`../carmen/docs/costing/enhanced-costing-engine.md`) and the sibling [`calculation-methods.md`](./calculation-methods.md) describe a richer model than the Prisma reality — in particular, a per-product costing-method configuration and a separate `inventory_lot` / `inventory_balance` schema that the platform does not have. Cross-checking against the canonical Prisma schemas yields the following divergences:

| # | Item | carmen/docs (or sibling calculation-methods.md) says | Prisma has | Action |
|---|------|------------------------------------------------------|------------|--------|
| 1 | Costing-method configuration scope | `calculation-methods.md` § 6.1 describes configuration "at the **organization or product category** level" — implying per-product or per-category costing method, with `product_category.costing_method` and `organization_settings.costing_method` columns. | **Per business unit only.** `tb_business_unit.calculation_method ∈ {average, fifo}` (platform schema, default `average`) — single value applies to every product at that business unit. **No per-product or per-category column exists** on `tb_product`, `tb_product_category`, `tb_product_sub_category`, or `tb_product_item_group`. The tenant `enum_business_unit_config_key = calculation_method` is a runtime-config override at the same business-unit grain, not a finer-scope option. | Treat Prisma as canonical: the platform supports **one costing method per business unit (property / hotel)**, not per product or category. Update `calculation-methods.md` § 6.1 and any per-product framing to note that mixed methods across products at the same business unit are **not supported** by the schema. Tenants that need mixed methods either (a) split into separate business units, or (b) defer to an application-layer extension; neither is a current schema feature. |
| 2 | Separate `inventory_lot` schema | `calculation-methods.md` § 2.3 describes an `inventory_lot` table with `lot_id`, `product_id`, `warehouse_id`, `purchase_date`, `quantity`, `unit_cost` as a dedicated lot-tracking entity. | **No `tb_inventory_lot` model exists.** Lot identity lives on `tb_inventory_transaction_cost_layer.(lot_no, lot_index)` (with `@@unique([lot_no, lot_index])`), and lot quantity is derived as `Σ (in_qty − out_qty)` for the lot since the most recent period snapshot. There is no row that represents a lot independently of its cost-layer events. | Update `calculation-methods.md` § 2.3 to reflect that lots are represented as a logical grouping of cost-layer rows by `(lot_no, lot_index)`, not a separate entity. The "current lot balance" is a derived query, not a persisted column — same derivation pattern as on-hand. |
| 3 | Separate `inventory_balance` schema (WA path) | `calculation-methods.md` § 3.3 describes an `inventory_balance` table with `product_id`, `warehouse_id`, `quantity`, `average_cost`, `total_value` as a per-product / per-location running balance for WA. | **No `tb_inventory_balance` model exists.** The running average is held on `tb_inventory_transaction_cost_layer.average_cost_per_unit` on the **most recent layer event** at the `(location_id, product_id)` key. On-hand is derived (same pattern as FIFO). Total value is derived as `on_hand × average_cost_per_unit`. | Update `calculation-methods.md` § 3.3 to document that WA running state lives on the cost-layer ledger (not on a dedicated balance row). The advantage cited there ("Lower storage requirements: single record per product-warehouse pair") does not apply — the platform writes one cost-layer row per movement under both methods; the difference is the cost-pick algorithm, not the storage footprint. |
| 4 | Per-product `costing_method` column on `tb_product` | *(Resolved 2026-07-22 — historical entry, kept for the audit trail.)* An earlier draft of `inventory/01-data-model.md` § 5 item 4 stated: "Costing method per product is held on the **product** model (`tb_product`) — not on inventory." | **No `costing_method` column on `tb_product`.** The product model carries `standard_cost`, `price_deviation_limit`, `qty_deviation_limit` but **no** `costing_method` or `valuation_method` enum column. Costing method is on `tb_business_unit.calculation_method` (item 1 above). | Already corrected — [inventory/01-data-model](/en/inventory/inventory/01-data-model) § 5 item 4 was rewritten in the 2026-07-15 inventory-module resync pass and now states the method is BU-wide with no per-product override, matching this page. No further action. |
| 5 | Strategy-pattern architecture | `calculation-methods.md` § 6.2 describes an `InventoryCostingStrategy` interface with `FIFOStrategy` and `AverageCostStrategy` implementations, a `CostingService.getStrategy(productId)` lookup that returns the strategy per product. | The architecture matches the strategy pattern, but the **strategy is resolved per business unit, not per product**. The runtime lookup is `getStrategy(businessUnitId)`, not `getStrategy(productId)`. The application service may still expose a per-product API surface for caller convenience but it resolves to the same business-unit-level method internally. | Update `calculation-methods.md` § 6.2 to document the resolution scope (business unit, not product). The interface itself is unchanged; the lookup signature changes. |
| 6 | `physical_count_costing_method` (count-variance source) | Not described in `calculation-methods.md` or `enhanced-costing-engine.md`. | `enum_physical_count_costing_method ∈ {standard, last, average, last_receiving}` is a costing-relevant enum that selects the cost source for count-driven variance posts (Section 2.6 above). | Add a §6.x or §7 to `calculation-methods.md` covering count-variance valuation source. This is a tenant-configurable concern distinct from FIFO / WA cost-pick on regular inbound / outbound. |
| 7 | `diff_amount` (credit-note variance) | Not described in carmen/docs costing reference; mentioned at `inventory/01-data-model.md` § 2.3 (item 12 of inventory divergence catalogue). | `tb_inventory_transaction_cost_layer.diff_amount` carries cost-only variance for credit-note-amount adjustments and end-of-period revaluation; the originating lot's `cost_per_unit` is recalculated per `INV_CALC_011`. | Add to `calculation-methods.md` (and to the carmen/docs costing reference) — the cost-revaluation path is a first-class costing concern (vendor concessions affect ending inventory value and downstream consumption from the same lot). |
| 8 | Enhanced costing engine scope | `../carmen/docs/costing/enhanced-costing-engine.md` describes a **portion-based / recipe-cost / dynamic-pricing** engine: ingredient cost, labor cost, overhead, profitability analysis, BCG matrix, demand elasticity. | The Prisma costing surface covers **inventory valuation only** — FIFO / WA cost-pick on `tb_inventory_transaction_cost_layer`, period-end snapshot on `tb_inventory_period_snapshot`. The "enhanced costing engine" described in carmen/docs is an **application-layer service** built **on top of** the inventory valuation surface — it consumes the costed COGS from this module and adds recipe / portion / pricing layers. | Treat the two as separate concerns: this page (and `calculation-methods.md`) documents **inventory cost-flow** (the schema-backed surface); the enhanced costing engine is recipe / pricing layered above. Cross-reference but don't conflate. |
| 9 | "Cost layer" naming vs "lot" naming | `calculation-methods.md` uses "lot" throughout (`lot_id`, "Purchase Lot 1", "lot quantity"). Prisma uses "cost layer" (`tb_inventory_transaction_cost_layer`) — a broader term that includes inbound layer events, outbound consumption events, EOP rollforward, and credit-note-amount variance rows. | A **lot** in carmen/docs ≅ a group of cost-layer rows sharing `(lot_no, lot_index)`. The cost-layer table is broader than just lots — it carries non-lot events (`credit_note_amount`, `close_period`, `open_period`) too. | Keep "lot" as the user-facing term (matches the GRN UI's "Lot" field) but document that internally one lot is a collection of cost-layer rows. Use "cost layer" when discussing the schema row; use "lot" when discussing the business concept. |
| 10 | Rounding and precision | `calculation-methods.md` § 6.4 mentions "Rounding: Round per lot" (FIFO) and "Risk of accumulated errors - use high precision" (WA). | Columns are `Decimal(20, 5)`, but **the engine rounds unit costs to 2 dp** — `cost_per_unit = Math.round(x × 100) / 100` (`inventory-transaction.service.ts:941,1134`), `calculateNewAverageCost` returns 2 dp (`inventory-cost.formula.ts:100`), `splitFifoCost(qty, totalCost, 2)` reconciles layers to the exact 2-dp total. The GRN money chain upstream is 5 dp. | Document the real precision: 5 dp on the document, 2 dp on the ledger unit cost. `calculation-methods.md`'s "use high precision" advice is not what the code does. |
| 11 | Extra-cost allocation | `calculation-methods.md` / carmen/docs treat landed cost as out of scope; the 2026-07-15 GRN pages marked allocation "unconfirmed". | **Live since 2026-09-10:** `allocateExtraCost()` splits the receipt's extra cost across lines (`by_qty` equal, `by_value` by stock qty, `manual` none) and each cost layer stores its `extra_cost_amount`. | Add landed cost to the algorithm description; note the mode names are inverted relative to their behaviour. |
| 12 | Average scope | `calculation-methods.md` § 3 and earlier versions of this page: average per `(warehouse / location, product)`. | **Per product across all locations** (`getNetTotals(tx, productId)`); location is only used for the on-hand check. | Correct the scope everywhere it is stated. |
| 13 | Period tables | `tb_period`, `tb_period_snapshot`. | Renamed `tb_inventory_period`, `tb_inventory_period_snapshot`, `tb_inventory_period_comment` (`20260916141000`); HTTP `/inventory-periods`; permission `system_admin.inventory_period`. | Rename in every page that cites the old names. |

## 6. References

- **Primary (source of truth):**
  - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — tenant entities (`tb_inventory_transaction_cost_layer` `:1177-1221`, `tb_inventory_transaction_detail` `:1122-1155`, `tb_inventory_period_snapshot` `:1298`, `tb_product`), tenant enums (`enum_business_unit_config_key`, `enum_physical_count_costing_method`, `enum_transaction_type`); migrations `20260910130000_add_cost_layer_extra_cost`, `20260810180000_move_grn_lot_link_to_ledger`, `20260916141000_rename_tb_period_to_tb_inventory_period`.
  - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.ts` (`createFromGoodReceivedNote` `:841`, `createFifoTransaction` `:893`, `createAverageTransaction` `:1051`, `getNetTotals` `:1487`, `restampAverageCostForProducts` `:1521`), `apps/micro-business/src/common/helpers/inventory-cost.formula.ts`, `lot-number.helper.ts`, `fifo-cost-split.helper.ts`.
  - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — platform entity `tb_business_unit.calculation_method` and platform enum `enum_calculation_method` (the canonical costing-method configuration).
- **Secondary (concept cross-check):**
  - `../carmen/docs/costing/enhanced-costing-engine.md` — recipe / portion / dynamic-pricing layer built on top of inventory cost-flow; divergence in Section 5 item 8.
  - Sibling: [calculation-methods.md](./calculation-methods.md) — FIFO vs WA analysis and algorithms; divergences in Section 5 items 1, 2, 3, 5, 6, 7, 9, 10.
- Related modules: [inventory](/en/inventory/inventory) (the cost-layer ledger lives in the inventory module; this page documents the costing-engine view of the same rows; full inventory schema at [inventory/01-data-model](/en/inventory/inventory/01-data-model)), [good-receive-note](/en/inventory/good-receive-note) (primary inbound source — GRN commit, or save on average units, writes the inbound cost layers with the receipt's landed cost), [store-requisition](/en/inventory/store-requisition) (primary outbound source — SR issue triggers the cost-pick), [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check) (count-variance posts use `enum_physical_count_costing_method` to select the variance cost source), [inventory-adjustment](/en/inventory/inventory-adjustment) (manual `tb_stock_in` / `tb_stock_out` adjustments — created as `draft`, posted by `PATCH …/commit`; `adjustment_type_id` is a reason code only and drives no GL routing — the GL module is not called from inventory code), [recipe](/en/inventory/recipe) (downstream consumer — recipe costing reads the per-product cost basis the engine maintains), [product](/en/inventory/product) (carries `standard_cost` reference cost and the deviation ceilings; **does not** carry costing method per Section 5 item 4).
