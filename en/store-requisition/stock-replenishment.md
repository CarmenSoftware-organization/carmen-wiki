---
title: Stock Replenishment
description: Auto-generated SR proposal driven by min / max / par / reorder thresholds at each location — the policy-driven counterpart to the manual Store Requisition flow.
published: true
date: 2026-05-16T17:00:00.000Z
tags: store-requisition, replenishment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Stock Replenishment

## 1. Purpose

Stock Replenishment is the **policy-driven variant of [[store-requisition]]**. Instead of an outlet manager hand-typing what they need, a scheduled job sweeps every `(product, location)` pair with replenishment thresholds configured and proposes an SR draft for every location below par. The Inventory Controller reviews the proposal, trims or accepts lines, and submits it; from that point it is a regular SR running through the standard approval and fulfillment workflow.

The variant exists because routine outlet topping-up is repetitive, error-prone, and easy to forget. Hospitality outlets need their daily par of dry goods, beverages, and supplies maintained against an agreed min/max envelope; a nightly cron computing deficits and pre-filling a draft removes the manual step while preserving the approval safety net.

## 2. Process Model

Stock Replenishment is **not a separate Prisma table**. The output is a regular `tb_store_requisition` row (with `sr_type = 'transfer'` or `'issue'` per destination type) that the Inventory Controller authored implicitly via the cron job. Two upstream tables drive the algorithm:

### 2.1 `tb_product_location` (replenishment policy)

| Field | Prisma Type | Description |
| --- | --- | --- |
| `id` | `String @db.Uuid` | Primary key. |
| `product_id` | `String @db.Uuid` | FK to `tb_product`. |
| `location_id` | `String? @db.Uuid` | FK to `tb_location` (the consuming location). |
| `min_qty` | `Decimal(20,5)?` | Trigger threshold — replenish when `on_hand + on_order < min_qty`. |
| `max_qty` | `Decimal(20,5)?` | Upper cap — target stock level after replenishment. |
| `par_qty` | `Decimal(20,5)?` | Operational par level (typically between `min` and `max`). |
| `re_order_qty` | `Decimal(20,5)?` | Suggested order quantity when the trigger fires (often `max - on_hand`). |
| Audit columns | — | Standard `created_*` / `updated_*` / `deleted_*`. |

**Constraints:** `@@unique([product_id, location_id, deleted_at])`. One policy row per `(product, location)`.

### 2.2 `tb_store_requisition` (output)

The generated SR carries `sr_type` (`issue` or `transfer`), `from_location_id` (the source — typically the main store), `to_location_id` (the consuming outlet), `requestor_id` (set to a system / service account), `description` (e.g. "Auto-replenishment 2026-05-16"), and `doc_status = 'draft'` awaiting Inventory Controller review.

Inferred — there is no dedicated `tb_replenishment` or `tb_replenishment_run` table in the tenant schema; the run is in-memory in the cron job and its only durable artifact is the SR draft it produces.

## 3. Algorithm

```
Nightly (or on-demand) cron run:

1. SELECT every tb_product_location row where min_qty > 0 AND is not deleted
2. For each (product, location):
   - on_hand = current InventoryStatus.QuantityOnHand at location
   - on_order = sum of qty on open PO / pending SR transfer-in to location
   - deficit = max_qty - (on_hand + on_order)     // or re_order_qty when configured
   - if (on_hand + on_order) < min_qty AND deficit > 0:
       emit_line(product, location, deficit)

3. GROUP emitted lines BY (source_location, destination_location):
   - source_location resolves from product policy (main store for the BU) or location config
   - one SR draft per (source, destination) group with all deficit lines

4. INSERT tb_store_requisition (sr_type, from/to_location, requestor = service account,
                                doc_status = draft, description = 'Auto-replenishment YYYY-MM-DD')
   INSERT tb_store_requisition_detail per line
   The draft now appears in the Stock Replenishment inbox for review

5. Inventory Controller reviews, may trim qty or remove lines, then submits:
   - doc_status flips draft -> in_progress, follows standard SR approval chain
   - From here it is indistinguishable from a manually-authored SR
```

If a SR already exists in `draft` for the same `(from, to, date)` pair, the cron updates lines in place (idempotency) rather than spawning a duplicate.

## 4. Usage / Cross-References

- [[store-requisition]] — the document type produced; downstream lifecycle is identical
- [[inventory]] — `on_hand` source for the deficit calculation
- [[product]] — `tb_product_location` policy lives under the product master
- [[master-data/location]] — per-location min/max/par/reorder configuration
- [[purchase-order]] — `on_order` includes open PO qty heading to the location (transfer-in chain)
- [[inventory/transaction]] — once the generated SR is issued, ledger rows post as normal `store_requisition` events

## 5. Business Rules

- **Authority.** Only Inventory Controller / Inventory Manager can submit a replenishment draft to in_progress. The cron's service account is allowed to insert drafts only.
- **Policy required.** A `(product, location)` pair with no `tb_product_location` row, or with `min_qty = 0`, is excluded from the sweep.
- **Source resolution.** The source location for the generated SR is read from a per-BU configuration (typically "main store"); if no source is configured for a destination, the deficit is flagged for manual SR instead of auto-generated.
- **On-order accounting.** `on_order` includes open POs and in-progress SR transfers-in; this prevents double-replenishing while a previous SR is still in flight.
- **Idempotency.** Re-running the cron on the same day reuses the same draft SR per `(from, to)` rather than creating duplicates.
- **Period gate.** The generated SR carries today's date; if the period for today is `closed` / `locked`, the cron skips emission and logs to its run log.
- **Authorization reference.** `INV_AUTH_004` governs who may approve replenishment SRs (same authority as manual SRs).
- **No auto-submit.** The cron never submits past `draft`. Human review is the safety gate.
- **Schedule.** Default nightly run; can be triggered ad-hoc from the Frontend (Inventory Controller).

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_product_location` (lines ~4364-4399), `tb_store_requisition` (lines ~2922-2984), `enum_sr_type` (lines ~224-227).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/store-operation/stock-replenishment/`.
- **Cron job:** `../micro-cronjobs/` — Go service that hosts the nightly sweep (replenishment job module — table name `tb_replenishment_run` not present in tenant schema; run state lives in the cron service).
- **Module landing:** [[store-requisition]] § 3 (movement type, approval workflow).
- **Cross-module:** see Section 4.
