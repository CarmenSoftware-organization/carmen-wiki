---
title: Stock Replenishment
description: Auto-generated SR proposal driven by min / max / par / reorder thresholds at each location — the policy-driven counterpart to the manual Store Requisition flow.
published: true
date: 2026-05-17T07:00:16.000Z
tags: store-requisition, replenishment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Stock Replenishment

> **At a Glance**
> **Owner:** Inventory Controller (review / submit) &nbsp;·&nbsp; Cron service account (draft only) &nbsp;·&nbsp; **Table:** none dedicated — output is `tb_store_requisition` draft &nbsp;·&nbsp; **Trigger:** nightly cron (or on-demand) &nbsp;·&nbsp; **Inputs:** `tb_product_location` (min/max/par/reorder) + on-hand + on-order &nbsp;·&nbsp; **1-liner:** cron sweeps deficits and pre-fills SR drafts; humans approve.

![Stock Replenishment screen](/screenshots/store-requisition/stock-replenishment.png)

## 1. What & Who

Stock Replenishment is the **policy-driven variant of [[store-requisition]]**. A scheduled job sweeps every `(product, location)` pair with thresholds configured and proposes an SR draft for every location below par. The Inventory Controller reviews, trims, and submits — from that point it is a regular SR running through the standard approval and fulfillment workflow.

- **Inventory Controller** — reviews the auto-generated draft and submits
- **Cron service account** — inserts drafts only (cannot push past `draft`)
- **No `tb_replenishment` table.** The run is in-memory in the Go cron service; the only durable artifact is the SR draft.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| View today's generated draft | Store Operation → Stock Replenishment inbox | One draft per `(source_location, destination_location)` group |
| Approve a replenishment SR | Open draft → trim lines if needed → **Submit** | Flips `draft → in_progress`, routes via standard SR approval chain |
| Trigger ad-hoc sweep | Inventory Controller → **Run now** | Same idempotency as nightly run; safe to re-trigger |
| Override par / max for a product | [[product]] → location tab → edit `tb_product_location` | Takes effect on next run |
| Configure source location for a destination | Per-BU configuration | Without a source, deficits flag for manual SR instead |
| Investigate a missing replenishment | Check `tb_product_location` exists and `min_qty > 0` | Pairs with no policy or `min_qty = 0` are excluded |
| Check cron run log | `../micro-cronjobs/` service logs | Run state lives in cron service, not the tenant DB |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| Product not appearing in draft | No `tb_product_location` row, or `min_qty = 0` | Add / update the policy row in [[product]] |
| Source location flagged for manual SR | No source configured for the destination | Configure source per BU, or raise SR manually |
| Run skipped today | Period for today is `closed` / `locked` | Re-run after period flips; or use a current-period date |
| Duplicate-looking drafts | None — idempotent per `(from, to, date)` | Re-running updates lines in place, not duplicates |
| Replenishment qty too high | `on_order` not counted into `(on_hand + on_order)` check | Verify open POs / pending SR transfer-in are reflected; flag to dev |
| Service account can't submit | By design — submit requires Inventory Controller / Manager | Human review is the safety gate (`INV_AUTH_004`) |

## 4. Edge Cases

- **No dedicated schema.** No `tb_replenishment` or `tb_replenishment_run` exists in the tenant schema; durable artifact is `tb_store_requisition` only.
- **Idempotency.** Re-running the cron the same day reuses the existing draft per `(from, to)` — never spawns duplicates.
- **`on_order` includes both** open POs heading to the destination AND in-progress SR transfers-in — prevents double-replenishing while a previous SR is in flight.
- **Period gate.** If today's period is `closed` / `locked`, the cron skips emission and writes to its run log.
- **Never auto-submits.** The cron cannot push past `draft`. Human review (`INV_AUTH_004`) is mandatory.
- **Source resolution.** Source location read from per-BU config (typically "main store"); destinations without a source fall back to manual SR.

---

## 5. Process (Dev)

Stock Replenishment is **not a separate Prisma table** — it is a cron-driven process over two upstream tables.

### 5.1 `tb_product_location` (policy)

| Field | Type | Description |
|---|---|---|
| `id` | `String @db.Uuid` | Primary key. |
| `product_id` | `String @db.Uuid` | FK to `tb_product`. |
| `location_id` | `String? @db.Uuid` | FK to `tb_location` (consuming location). |
| `min_qty` | `Decimal(20,5)?` | Trigger: replenish when `on_hand + on_order < min_qty`. |
| `max_qty` | `Decimal(20,5)?` | Target stock level after replenishment. |
| `par_qty` | `Decimal(20,5)?` | Operational par (typically between min and max). |
| `re_order_qty` | `Decimal(20,5)?` | Suggested order qty when trigger fires (often `max - on_hand`). |
| Audit columns | — | Standard. |

**Constraints:** `@@unique([product_id, location_id, deleted_at])`. One policy row per `(product, location)`.

### 5.2 `tb_store_requisition` (output)

Generated SR carries `sr_type` (`issue` or `transfer`), `from_location_id` (source — typically main store), `to_location_id` (consuming outlet), `requestor_id` (service account), `description` (e.g. "Auto-replenishment 2026-05-17"), `doc_status = 'draft'`.

## 6. Algorithm / Lifecycle

```
Nightly (or on-demand) cron run:

1. SELECT every tb_product_location row where min_qty > 0 AND not deleted
2. For each (product, location):
   - on_hand = current InventoryStatus.QuantityOnHand at location
   - on_order = sum of qty on open PO + pending SR transfer-in
   - deficit = max_qty - (on_hand + on_order)     // or re_order_qty if configured
   - if (on_hand + on_order) < min_qty AND deficit > 0:
       emit_line(product, location, deficit)
3. GROUP emitted lines BY (source_location, destination_location)
4. INSERT tb_store_requisition (doc_status = draft, requestor = service account)
   INSERT tb_store_requisition_detail per line
   -> appears in Stock Replenishment inbox
5. Inventory Controller reviews, trims, submits:
   - draft -> in_progress; standard SR approval chain from here
```

If a draft already exists for `(from, to, date)`, the cron updates lines in place (idempotency).

## 7. Cross-References

- [[store-requisition]] — produced document type; downstream lifecycle identical
- [[inventory]] — `on_hand` source for the deficit calculation
- [[product]] — `tb_product_location` policy lives under the product master
- [[master-data/location]] — per-location min / max / par / reorder configuration
- [[purchase-order]] — `on_order` includes open PO qty
- [[inventory/transaction]] — once the SR posts, ledger writes `store_requisition` events

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_product_location` (~4364-4399), `tb_store_requisition` (~2922-2984), `enum_sr_type` (~224-227).
- **Frontend:** `../carmen-inventory-frontend/app/(root)/store-operation/stock-replenishment/`.
- **Cron job:** `../micro-cronjobs/` — Go service hosting the nightly sweep. Run state lives in the cron service (no tenant table).
- **Module landing:** [[store-requisition]] § 3 (movement type, approval workflow).
