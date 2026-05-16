---
title: Costing — Data Model
description: Entities, fields, relationships, and enums for the costing module.
published: true
date: 2026-05-17T11:00:00.000Z
tags: costing, data-model, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# Costing — Data Model

> **At a Glance**
> **Tables:** `tb_inventory_transaction_cost_layer` &nbsp;·&nbsp; `tb_inventory_transaction_detail` &nbsp;·&nbsp; `tb_period_snapshot` &nbsp;·&nbsp; `tb_business_unit.calculation_method` &nbsp;·&nbsp; `tb_product.standard_cost`
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** cost-layer `→ tb_inventory_transaction_detail`; cost-layer `→ tb_period`; cross-schema link: tenant cost-layer reads platform `tb_business_unit.calculation_method` via JWT `x-app-id` (no Prisma `@relation`)
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*` on cost-layer and snapshot; **`tb_inventory_transaction_detail` has no soft-delete** — reversal posts a compensating row instead

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview

The Costing module is **not a separate document tree** in the way GRN, PR, or SR are. It is a **read-and-write contract layered over the inventory transaction ledger**: the engine reads `tb_inventory_transaction_detail` and `tb_inventory_transaction_cost_layer` to pick the cost for an outbound movement, writes `cost_per_unit` / `average_cost_per_unit` onto the cost-layer rows at post time, and reads back from the same rows when downstream consumers (recipe costing, financial reporting, valuation) need a unit cost. There is no `tb_costing_*` model in the canonical Prisma schema — costing data lives on the inventory entities (`tb_inventory_transaction_cost_layer` is the canonical cost-flow record, `tb_inventory_transaction_detail.cost_per_unit` is the per-line cost, `tb_period_snapshot.closing_cost_per_unit` is the period-end locked unit cost) and the **costing-method configuration** lives one level up at the **business unit** in the platform schema, not on the product.

The cost-flow assumption — **FIFO** (lots consumed by `lot_seq_no` ascending, each carrying its own `cost_per_unit`) or **Weighted Average** (single moving-average per `(location_id, product_id)` refreshed on every inbound) — is configured on `tb_business_unit.calculation_method` (`enum_calculation_method = average | fifo`, default `average`) at the property level. The tenant schema's `enum_business_unit_config_key` exposes `calculation_method` as a runtime config key, and `enum_physical_count_costing_method` (`standard`, `last`, `average`, `last_receiving`) selects which cost source feeds count-driven variance posts. The product itself (`tb_product`) carries `standard_cost` (the reference cost used by the `standard` count-costing method and by recipe baselining) and `price_deviation_limit` / `qty_deviation_limit` (tolerance bands used by procurement / receiving rules), but it does **not** carry a per-product costing method — that is a deliberate platform-wide simplification documented in Section 5.

The engine runs **per-transaction, not as a periodic batch**. When the inventory module posts an inbound `tb_inventory_transaction_cost_layer` row, the engine writes `cost_per_unit` (the layer cost), recomputes `average_cost_per_unit` for weighted-average, and assigns `lot_seq_no` for FIFO ordering. When an outbound movement posts, the engine reads the configured method, picks the cost (FIFO consumes from `lot_seq_no` ascending; WA reads the most recent `average_cost_per_unit`), and writes the corresponding outbound `out_qty × cost_per_unit` rows. At period close, the engine writes `closing_cost_per_unit` on `tb_period_snapshot` and `transaction_type = close_period` / `open_period` cost-layer rows that anchor the period-boundary unit cost. The sibling [`calculation-methods.md`](./calculation-methods.md) is the deep-dive on the FIFO / WA algorithms and the platform's strategy-pattern design recommendation; this page is the schema-level catalogue.

## 2. Entities

### 2.1 tb_inventory_transaction_cost_layer (canonical cost record)

The **cost-flow ledger row** — the single source of truth for "what did this unit cost?" at every point in time. One row per layer event per movement: inbound rows create a new layer with `in_qty > 0`, `cost_per_unit`, `lot_no`, `lot_index`, `lot_seq_no`; outbound rows consume a layer with `out_qty > 0`, `from_lot_no` resolved by FIFO ordering on `lot_seq_no`, and `cost_per_unit` picked from the consumed layer (FIFO) or from the current moving average (WA). The row also persists `average_cost_per_unit` so weighted-average consumers can read the post-movement moving average without re-aggregating the whole history. `at_period` (`YYMM`) and `period_id` tie the layer to an accounting period so the period-end rollup can sum activity per period.

This entity is owned by the [[inventory]] module — full field catalogue at [[inventory/01-data-model]] § 2.3. The costing module's perspective: this is the table the engine reads at every outbound (to pick `cost_per_unit`) and writes at every inbound (to set `cost_per_unit` and recompute `average_cost_per_unit`).

**Costing-relevant fields:**

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Per-unit cost on this layer event; default `0`. For inbound layers: the GRN / adjustment-in cost. For outbound layers: the cost picked by the costing rule — under FIFO, the consumed layer's cost; under WA, the moving average at post time. The canonical "what did this unit cost" field. |
| `average_cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Post-movement moving-average unit cost at `(location_id, product_id)`; default `0`. Refreshed by every inbound under WA. Outbound movements **do not** change this value (they consume at the prevailing average but don't re-blend). For FIFO-only products this column is informational; for WA, it is the canonical "current average" that the next outbound picks. |
| `lot_seq_no` | `Int` | Yes | FIFO ordering anchor within `(location_id, product_id)`; default `1`. Lower `lot_seq_no` is consumed first under FIFO. Preserved across period boundaries by the `open_period` rollforward so FIFO sequence survives close. Informational for WA-configured products. |
| `diff_amount` | `Decimal @db.Decimal(20, 5)` | Yes | Variance amount used for credit-note-amount adjustments (vendor concedes a price reduction post-receipt — the `cost_per_unit` of the originating lot is recalculated per `INV_CALC_011`) and for end-of-period price revaluation; default `0`. Carries cost-only variance independent of `in_qty` / `out_qty`. |
| `in_qty` / `out_qty` | `Decimal @db.Decimal(20, 5)` | Yes | The quantity side of the layer event; `total_cost = (in_qty or out_qty) × cost_per_unit`. Mutually exclusive on a single row per `INV_VAL_007`. |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `(in_qty − out_qty) × cost_per_unit` (signed); default `0`. The journal-entry amount for the layer event. |
| `transaction_type` | `enum_transaction_type` | Yes | Cost-flow classifier — `good_received_note`, `transfer_in`, `transfer_out`, `issue`, `adjustment_in`, `adjustment_out`, `credit_note_amount`, `credit_note_quantity`, `eop_in`, `eop_out`, `close_period`, `open_period`. Drives which cost-pick rule the engine applies. |
| `at_period` | `String @db.VarChar` | Yes | Period in `YYMM` form (denormalised from `tb_period.period`). Costing aggregations group by this column to produce period-bounded COGS / valuation totals. |
| `period_id` | `String @db.Uuid` | Yes | FK to `tb_period.id` — the accounting period containing this layer event. |

Other fields (`lot_no`, `lot_index`, `parent_lot_no`, `location_id`, `product_id`, audit columns) are listed in full at [[inventory/01-data-model]] § 2.3.

**Costing-relevant constraints:** `@@unique([lot_no, lot_index])` enforces lot identity; the cost-pick algorithm relies on `(location_id, product_id, lot_seq_no)` ordering for FIFO and on the most-recent row at `(location_id, product_id)` for the WA current average. `cost_per_unit` and `average_cost_per_unit` are non-negative per `INV_VAL_007`.

### 2.2 tb_inventory_transaction_detail (per-line cost ledger)

The **per-product / per-lot ledger line** under a movement. Carries `qty`, `cost_per_unit`, `total_cost`, the location, and the lot-trace fields `from_lot_no` / `current_lot_no`. The costing module reads this row to confirm the cost-per-unit posted with a specific source-document line (a GRN line carries `cost_per_unit = vendor unit price after extra-cost allocation`; an SR issue line carries `cost_per_unit = picked cost`); it is the user-facing reflection of the cost-layer's cost.

**Costing-relevant fields:**

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `cost_per_unit` | `Decimal @db.Decimal(20, 5)` | Yes | Unit cost at posting; default `0`. For inbound, the layer cost (drives the cost-layer row's `cost_per_unit`); for outbound, the engine-picked cost. **This is the value visible on the source document's line** (e.g. the GRN detail's unit cost, the SR issue's costed unit). |
| `qty` | `Decimal @db.Decimal(20, 5)` | Yes | Signed quantity in base UoM; positive = inbound, negative = outbound. Multiplied by `cost_per_unit` to produce `total_cost`. |
| `total_cost` | `Decimal @db.Decimal(20, 5)` | Yes | `qty × cost_per_unit` (signed); default `0`. The journal-entry amount on the detail line. |
| `from_lot_no` | `String @db.VarChar` | Yes | Source lot consumed (outbound). Set by the FIFO pick — points to the lot whose `lot_seq_no` was lowest with non-zero remaining balance. |
| `current_lot_no` | `String @db.VarChar` | Yes | Lot newly created or affected (inbound). Carries the new layer's lot identity into the cost-layer row's `lot_no`. |

Other fields and constraints listed in full at [[inventory/01-data-model]] § 2.2.

### 2.3 tb_period_snapshot (period-locked unit cost)

The **locked opening / closing balance row per `(period_id, location_id, product_id, lot_no, lot_index)`**. Written at period close as the audit anchor. From the costing perspective, this row is **the period-end valuation answer** — it carries `closing_qty`, `closing_cost_per_unit`, and `closing_total_cost` that the balance sheet and food-cost reports consume.

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

Other fields listed at [[inventory/01-data-model]] § 2.7.

### 2.4 tb_business_unit.calculation_method (costing-method configuration — platform)

The **costing-method configuration**. Held at the business-unit (property / hotel) level on the **platform schema**, not on the tenant schema and not on the product. Single value applies to every product at that business unit.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `calculation_method` | `enum_calculation_method` | No | Costing method for the business unit. Values: `average` (Weighted Average — default), `fifo` (First-In-First-Out). Read by the inventory cost-layer post engine at every outbound to decide the cost-pick rule. |

`tb_business_unit` is defined in `prisma-shared-schema-platform/prisma/schema.prisma` (not in the tenant schema where `tb_inventory_transaction_cost_layer` lives). The cost-layer post engine reads this value via the tenant-to-platform JWT context (`x-app-id` resolves to the business unit) and applies the picked rule to the cost-layer write. The tenant schema's `enum_business_unit_config_key` enumerates `calculation_method` as a config key — a parallel runtime-config surface (key/value rows) that may shadow or extend the platform default, depending on the tenant's config-loader convention.

### 2.5 tb_product.standard_cost (reference cost on the product)

The **product's reference / standard cost**. Used by the `standard` count-costing method (`enum_physical_count_costing_method = standard` — count variance is valued at the product's `standard_cost` rather than the cost-layer cost) and by recipe baseline costing.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `standard_cost` | `Decimal @db.Decimal(20, 5)` | Yes | Reference / standard cost per unit in base UoM; default `0`. Updated by Finance / cost-controller cadence (typically monthly or quarterly). Not used by the FIFO / WA cost-pick engine — those read the cost-layer's `cost_per_unit` / `average_cost_per_unit`. |
| `price_deviation_limit` | `Decimal @db.Decimal(20, 5)` | Yes | Tolerance band — percentage or absolute — used by procurement / receiving rules to flag a vendor price exceeding the standard cost. Not directly costing-engine consumed; informational for variance reporting. |
| `qty_deviation_limit` | `Decimal @db.Decimal(20, 5)` | Yes | Tolerance band on receiving qty vs ordered. Informational. |

`tb_product` is documented in full under the [[product]] module; this entry covers the costing-relevant subset.

### 2.6 enum_physical_count_costing_method (count-variance valuation source)

A four-value enum that selects **which cost source feeds count-driven variance posts** when a physical-count or spot-check completes with variance. This is a costing-specific concern because count adjustments (`adjustment_in` / `adjustment_out`) need a `cost_per_unit` to compute `total_cost`, and the source of that cost varies by tenant preference.

| Value | Cost source |
| ----- | ----------- |
| `standard` | The product's `tb_product.standard_cost`. Used by tenants who want count variance valued at the reference cost regardless of recent receipt prices. |
| `last` | The most recent cost-layer's `cost_per_unit` at `(location_id, product_id)` regardless of direction. Approximates "current market cost". |
| `average` | The most recent `average_cost_per_unit` at `(location_id, product_id)`. For WA-configured products, equals the current running average; for FIFO, the engine maintains a parallel WA shadow for this purpose. |
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

tb_inventory_transaction
    │ * inventory_transaction_id
    ▼
tb_inventory_transaction_detail
    │  cost_per_unit (user-facing per-line cost)
    │  qty (signed) ── total_cost = qty × cost_per_unit
    │
    │ * inventory_transaction_detail_id
    ▼
tb_inventory_transaction_cost_layer  (canonical cost-flow record)
    │  cost_per_unit            ── layer cost (FIFO: per-lot; WA: per-event)
    │  average_cost_per_unit    ── post-movement moving average (WA path)
    │  lot_seq_no               ── FIFO ordering anchor (consumed lowest-first)
    │  diff_amount              ── credit-note-amount / EOP revaluation variance
    │  in_qty / out_qty         ── direction; mutually exclusive
    │  transaction_type ∈ {good_received_note, transfer_in, transfer_out,
    │                       issue, adjustment_in, adjustment_out,
    │                       credit_note_amount, credit_note_quantity,
    │                       eop_in, eop_out, close_period, open_period}
    │  at_period (YYMM) / period_id ── ties layer to accounting period
    │
    └──► tb_period   (period_id → close_period / open_period rollforward anchor)


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


tb_period ──1──*──► tb_period_snapshot  (locked period × location × product × lot
                                          opening / receipt / issue / adjustment /
                                          closing cost columns — the period-end
                                          valuation anchor)
```

Notes:

- **Configuration cross-schema gap.** The costing-method enum value lives on `tb_business_unit.calculation_method` in the **platform** schema, but the cost-layer rows that consume it live in the **tenant** schema. There is no Prisma `@relation` bridging the two; the relationship is resolved at the application layer via the JWT / `x-app-id` business-unit context that the tenant API call carries. The costing module's read path is therefore: `(tenant: inventory transaction post) → (jwt: x-app-id) → (platform query: tb_business_unit.calculation_method) → apply cost-pick rule`.
- **Per-tenant override via runtime config.** `enum_business_unit_config_key` enumerates `calculation_method` as a valid config key on `tb_business_unit_config_key`. Implementation-wise, this suggests a key/value runtime-config row that can override the platform default per business unit without redeploying — useful for tenants who switch methods at a fiscal-year boundary. The exact precedence (platform column vs key/value row) is an application-layer convention not enforced by the schema.
- **No `tb_costing_*` entity.** The costing module is structurally **a layer of behaviour over inventory entities**, not its own document tree. This is intentional: keeping the cost on the same row as the qty (on `tb_inventory_transaction_cost_layer`) means there can be no drift between the qty ledger and the cost ledger — they are the same ledger.
- **Cost-pick is movement-time, not query-time.** When an outbound posts, the engine resolves the cost at post time and writes it to the cost-layer's `cost_per_unit`. Subsequent reads of the row return that historical cost — even if the configured method changes later, posted rows preserve the cost picked under the method in effect at the time. This is the audit-defence property: every COGS figure traces back to a specific cost-layer row written at a specific moment under a specific method.
- **Period-snapshot is the locked answer.** Once `tb_period_snapshot.closing_cost_per_unit` is written by `INV_POST_009` (period close), the period's valuation is immutable; subsequent corrections to the closed period post as restatements in a later open period, not by editing the snapshot.
- **`standard_cost` is reference-only.** It does **not** drive FIFO or WA cost-pick. It drives the `standard` count-costing method (count variance valued at standard) and recipe baseline costing. Tenants who want count variance valued at the running average configure `physical_count_costing_method = average` instead.

## 4. Enums

- **`enum_calculation_method`** (platform schema, `prisma-shared-schema-platform`): costing-method classifier on `tb_business_unit.calculation_method`. Two values, default `average`:
  - `average` — Weighted Average. Single moving average per `(location_id, product_id)`, refreshed on every inbound per `INV_CALC_007`; outbound consumes at the prevailing average per `INV_CALC_006`.
  - `fifo` — First-In, First-Out. Lots consumed by `lot_seq_no` ascending per `INV_CALC_005`; each consumed lot produces its own outbound cost-layer row at its `cost_per_unit`.
- **`enum_business_unit_config_key`** (tenant schema): enumerates runtime-config keys on `tb_business_unit_config_key` rows. Costing-relevant values:
  - `calculation_method` — runtime override of the platform `tb_business_unit.calculation_method` default; values constrained to the same FIFO / AVG vocabulary.
  - `physical_count_costing_method` — selects the cost source for count-driven variance posts (values per `enum_physical_count_costing_method`).
  - `amount`, `quantity`, `recipe` — formatting / precision config keys (separate concern but configured at the same surface).
- **`enum_physical_count_costing_method`** (tenant schema): count-variance valuation source. Four values, no schema default declared:
  - `standard` — value count variance at `tb_product.standard_cost`.
  - `last` — value at the most recent cost-layer `cost_per_unit` at the `(location, product)` key, regardless of direction.
  - `average` — value at the most recent `average_cost_per_unit` (running WA).
  - `last_receiving` — value at the most recent inbound layer's `cost_per_unit` (filter `transaction_type ∈ {good_received_note, adjustment_in, transfer_in}`).
- **`enum_transaction_type`** (tenant schema): cost-flow effect on `tb_inventory_transaction_cost_layer.transaction_type`. Twelve values listed at [[inventory/01-data-model]] § 4; costing-engine-relevant subset:
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
| 4 | Per-product `costing_method` column on `tb_product` | `inventory/01-data-model.md` § 5 item 4 (the inventory data-model's divergence catalogue) states: "Costing method per product is held on the **product** model (`tb_product`) — not on inventory." | **No `costing_method` column on `tb_product`.** The product model carries `standard_cost`, `price_deviation_limit`, `qty_deviation_limit` but **no** `costing_method` or `valuation_method` enum column. Costing method is on `tb_business_unit.calculation_method` (item 1 above). | Update [[inventory/01-data-model]] § 5 item 4 to correct the claim — costing method is per business unit, not per product. The inventory module's reading of "the product's costing method" is actually reading the business-unit-level setting via the platform JWT context. |
| 5 | Strategy-pattern architecture | `calculation-methods.md` § 6.2 describes an `InventoryCostingStrategy` interface with `FIFOStrategy` and `AverageCostStrategy` implementations, a `CostingService.getStrategy(productId)` lookup that returns the strategy per product. | The architecture matches the strategy pattern, but the **strategy is resolved per business unit, not per product**. The runtime lookup is `getStrategy(businessUnitId)`, not `getStrategy(productId)`. The application service may still expose a per-product API surface for caller convenience but it resolves to the same business-unit-level method internally. | Update `calculation-methods.md` § 6.2 to document the resolution scope (business unit, not product). The interface itself is unchanged; the lookup signature changes. |
| 6 | `physical_count_costing_method` (count-variance source) | Not described in `calculation-methods.md` or `enhanced-costing-engine.md`. | `enum_physical_count_costing_method ∈ {standard, last, average, last_receiving}` is a costing-relevant enum that selects the cost source for count-driven variance posts (Section 2.6 above). | Add a §6.x or §7 to `calculation-methods.md` covering count-variance valuation source. This is a tenant-configurable concern distinct from FIFO / WA cost-pick on regular inbound / outbound. |
| 7 | `diff_amount` (credit-note variance) | Not described in carmen/docs costing reference; mentioned at `inventory/01-data-model.md` § 2.3 (item 12 of inventory divergence catalogue). | `tb_inventory_transaction_cost_layer.diff_amount` carries cost-only variance for credit-note-amount adjustments and end-of-period revaluation; the originating lot's `cost_per_unit` is recalculated per `INV_CALC_011`. | Add to `calculation-methods.md` (and to the carmen/docs costing reference) — the cost-revaluation path is a first-class costing concern (vendor concessions affect ending inventory value and downstream consumption from the same lot). |
| 8 | Enhanced costing engine scope | `../carmen/docs/costing/enhanced-costing-engine.md` describes a **portion-based / recipe-cost / dynamic-pricing** engine: ingredient cost, labor cost, overhead, profitability analysis, BCG matrix, demand elasticity. | The Prisma costing surface covers **inventory valuation only** — FIFO / WA cost-pick on `tb_inventory_transaction_cost_layer`, period-end snapshot on `tb_period_snapshot`. The "enhanced costing engine" described in carmen/docs is an **application-layer service** built **on top of** the inventory valuation surface — it consumes the costed COGS from this module and adds recipe / portion / pricing layers. | Treat the two as separate concerns: this page (and `calculation-methods.md`) documents **inventory cost-flow** (the schema-backed surface); the enhanced costing engine is recipe / pricing layered above. Cross-reference but don't conflate. |
| 9 | "Cost layer" naming vs "lot" naming | `calculation-methods.md` uses "lot" throughout (`lot_id`, "Purchase Lot 1", "lot quantity"). Prisma uses "cost layer" (`tb_inventory_transaction_cost_layer`) — a broader term that includes inbound layer events, outbound consumption events, EOP rollforward, and credit-note-amount variance rows. | A **lot** in carmen/docs ≅ a group of cost-layer rows sharing `(lot_no, lot_index)`. The cost-layer table is broader than just lots — it carries non-lot events (`credit_note_amount`, `close_period`, `open_period`) too. | Keep "lot" as the user-facing term (matches the GRN UI's "Lot" field) but document that internally one lot is a collection of cost-layer rows. Use "cost layer" when discussing the schema row; use "lot" when discussing the business concept. |
| 10 | Rounding and precision | `calculation-methods.md` § 6.4 mentions "Rounding: Round per lot" (FIFO) and "Risk of accumulated errors - use high precision" (WA). | All monetary columns are `Decimal(20, 5)` per `INV_CALC_012` — 5dp storage, half-up rounding to 2dp for display, 3dp for quantities. Aggregates re-read rounded values per step. | No divergence in policy; document the explicit precision (5dp on storage, 2dp on display for currency, 3dp for qty). Add to `calculation-methods.md` § 6.4 or merge into a general "precision" section. |

## 6. References

- **Primary (source of truth):**
  - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — tenant entities (`tb_inventory_transaction_cost_layer`, `tb_inventory_transaction_detail`, `tb_period_snapshot`, `tb_product`), tenant enums (`enum_business_unit_config_key`, `enum_physical_count_costing_method`, `enum_transaction_type`).
  - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — platform entity `tb_business_unit.calculation_method` and platform enum `enum_calculation_method` (the canonical costing-method configuration).
- **Secondary (concept cross-check):**
  - `../carmen/docs/costing/enhanced-costing-engine.md` — recipe / portion / dynamic-pricing layer built on top of inventory cost-flow; divergence in Section 5 item 8.
  - Sibling: [calculation-methods.md](./calculation-methods.md) — FIFO vs WA analysis and algorithms; divergences in Section 5 items 1, 2, 3, 5, 6, 7, 9, 10.
- Related modules: [[inventory]] (the cost-layer ledger lives in the inventory module; this page documents the costing-engine view of the same rows; full inventory schema at [[inventory/01-data-model]]), [[good-receive-note]] (primary inbound source — GRN commit writes the inbound cost-layer with the receipt's unit cost), [[store-requisition]] (primary outbound source — SR issue triggers the cost-pick), [[physical-count]] / [[spot-check]] (count-variance posts use `enum_physical_count_costing_method` to select the variance cost source), [[inventory-adjustment]] (manual `tb_stock_in` / `tb_stock_out` adjustments — `adjustment_type_id` reason code drives the GL routing, costing-engine picks the cost the same way as any other inbound / outbound), [[recipe]] (downstream consumer — recipe costing reads the per-product cost basis the engine maintains), [[product]] (carries `standard_cost` reference cost; **does not** carry costing method per Section 5 item 4).
