---
title: Stock Replenishment
description: Below-par list driven by par / max thresholds on tb_product_location, with wizards that raise PR or SR drafts — real API since 2026-08; no scheduled sweep.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: store-requisition, replenishment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Stock Replenishment

> **At a Glance**
> **Owner:** Purchaser / Requester (reviews the below-par list, raises PR or SR drafts) &nbsp;·&nbsp; **Table:** none dedicated — reads `tb_product_location` + on-hand, writes ordinary `tb_purchase_request` / `tb_store_requisition` drafts &nbsp;·&nbsp; **Trigger:** on demand (screen load) — **no cron** &nbsp;·&nbsp; **Endpoints:** `GET /api/{bu}/stock-replenishment`, `GET …/location-products/:location_id/:product_id/pending-documents`, `POST …/stock-replenishment/pr`, `POST …/stock-replenishment/sr` &nbsp;·&nbsp; **1-liner:** the screen lists every `(location, product)` below par; humans pick rows and raise the documents.

> ✅ **Implementation status (re-verified 2026-09-22):** the 2026-07-15 note that this screen was mock-data-driven is obsolete. `feat: add stock replenishment and wastage reporting api` (`c9348f667`, 2026-08) added the backend (`apps/micro-business/src/inventory/stock-replenishment/`, gateway `apps/backend-gateway/src/application/stock-replenishment/`), `57d5715a0` (2026-08-26) added the PR/SR creation endpoints, and the frontend hook `routes/store-operation/stock-replenishment/use-stock-replenishment.ts` now calls the real API. What is **still** not implemented: any scheduled sweep (no `replenish` / `par_qty` hit in `../micro-cronjobs/`), idempotent "one draft per day", an `on_order` term, a source-location configuration, and a period gate — Sections 2–6 below describe the code as it is.

![Stock Replenishment screen](/screenshots/store-requisition/stock-replenishment.png)

## 1. What & Who

Stock Replenishment is the **policy-driven front door to [store-requisition](/en/inventory/store-requisition) and [purchase-request](/en/inventory/purchase-request)**. `GET /api/{bu}/stock-replenishment` scans every `tb_product_location` row with `par_qty > 0` whose location is active and not `direct`, sums on-hand per `(location, product)`, and returns the rows whose on-hand is below par, grouped by location and ranked by reorder quantity. From the screen (`/store-operation/stock-replenishment`) the user ticks rows and opens one of two wizards: **Create PR** (`POST …/pr`, buys the shortfall in) or **Create SR** (`POST …/sr`, pulls it from another location). The created documents are ordinary drafts that then run the normal PR / SR workflows.

- **Purchaser / Requester** — reviews the list, chooses PR vs SR, picks the workflow (and, for SR, the source location), edits quantities in the wizard, and submits the resulting draft from its own module.
- **No service account, no cron** — nothing runs unattended.
- **No `tb_replenishment` table** — the only durable artefacts are the PR / SR drafts.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| See what is below par | Store Operation → Stock Replenishment | Summary bar: locations / items / critical / warning / low / total reorder qty; one collapsible group per location; each row shows on-hand, min, max, par, reorder qty and a status badge |
| Raise a PR for the shortfall | Select rows → **Create PR** wizard → pick workflow, adjust `request_qty` / order unit → confirm | `POST …/stock-replenishment/pr` — one PR draft per call; the location rides on each line |
| Raise an SR for the shortfall | Select rows → **Create SR** wizard → pick source location + SR workflow → confirm | `POST …/stock-replenishment/sr` — lines sharing a `(from_location, location_id)` pair become one SR draft; the response is the array of created ids |
| See what is already on the way for a row | Row → pending documents | `GET …/location-products/:location_id/:product_id/pending-documents` (`stock-replenishment.pending.ts`) lists PRs in `draft` / `in_progress` / `approved` (approved counts as pending on purpose — cleared the workflow, goods not yet received), SRs in `draft` / `in_progress`, and the PO lines linked to those PR lines, for that pair. Informational — the list does **not** subtract them from the shortfall |
| Change the thresholds | [product](/en/inventory/product) → location tab → edit `tb_product_location.par_qty` / `max_qty` / `min_qty` | Takes effect on the next screen load |
| Investigate a missing row | Check `tb_product_location` exists, `is_active`, and `par_qty > 0` | Pairs with no policy or `par_qty = 0` are excluded; `min_qty` plays no part in selection |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| Product not in the list | No `tb_product_location` row, `par_qty = 0`, on-hand ≥ par, or the location is `direct` / inactive | Add / raise the policy row; note `min_qty` is *not* the trigger and `direct` locations are never listed |
| `STOCK_REPLENISHMENT_WORKFLOW_NOT_FOUND` / `…_WORKFLOW_PERMISSION_DENIED` (400, "Insufficient user permission to create sr/pr") | The chosen `workflow_id` does not exist, or its first stage does not let the caller create | Pick a workflow of the right type (`purchase_request` for PR, `store_requisition` for SR) whose create stage includes the user (`stock-replenishment.verify.ts`) |
| `STOCK_REPLENISHMENT_LOCATION_PERMISSION_DENIED` (400) | The caller is not assigned to a line's location (`tb_location_user`) | Assign the location to the user or drop the row |
| `STOCK_REPLENISHMENT_PRODUCTS_NOT_APPLICABLE` (400, "…cannot apply with workflow: {workflow_name}") | The workflow's `data.products` list is non-empty and excludes a selected product | Choose a workflow that covers the product |
| PR wizard rejects the order unit | `request_unit_id` is not one of the product's order units (`loadProductOrderUnits`) | Pick a listed unit; the conversion factor is resolved server-side |
| SR draft fails downstream | The SR create rules apply unchanged — e.g. a `direct` source location is rejected by `deriveSrType()` | Pick an `inventory` / `consignment` source |
| Same shortfall raised twice | No idempotency — each wizard run creates new drafts | Check the pending-documents list first |

## 4. Edge Cases

- **Status bands are ratios of on-hand to par** (`stock-replenishment.helper.ts`): `on_hand / par_qty ≤ 0.25` → `critical`; `≤ 0.5` → `warning`; otherwise `low`. A negative ledger balance is clamped to zero for the ratio and the reorder formula, while `on_hand_qty` in the response still shows the raw (possibly negative) figure.
- **Reorder level prefers `max_qty`.** `reorder_level = max_qty > 0 ? max_qty : par_qty`; `reorder_qty = max(reorder_level − on_hand, 0)`. `min_qty` is returned for display only.
- **No `on_order` term.** Open POs and in-flight SR transfers do not reduce the shortfall; the pending-documents endpoint is the manual substitute.
- **No cron, no idempotency, no period gate.** Every wizard run creates fresh drafts; nothing checks the inventory period here (the SR's own submit/issue date rules apply later — see [store-requisition/02-business-rules](/en/inventory/store-requisition/02-business-rules) `SR_VAL_014`).
- **Source location is chosen per wizard run**, not configured per BU; the SR wizard excludes the destination from the source picker.
- **The draft header comes from the caller**: `buildDraftHeader()` takes the caller's first `tb_department_user` membership as the department and the chosen workflow; `requestor_id` is the caller.
- **Pagination is by location group** (`perpage < 0` returns all); rows inside a group are sorted `reorder_qty desc, name asc`.

---

## 5. Process (Dev)

Stock Replenishment is **not a separate Prisma table** — it is a read model over `tb_product_location` plus the on-hand balance, and two thin creators that delegate to the PR / SR modules.

### 5.1 `tb_product_location` (policy)

| Field | Type | Description |
|---|---|---|
| `id` | `String @db.Uuid` | Primary key. |
| `product_id` | `String @db.Uuid` | FK to `tb_product`. |
| `location_id` | `String? @db.Uuid` | FK to `tb_location` (consuming location). |
| `min_qty` | `Decimal(20,5)?` | Returned for display; **not** used in the selection or the reorder formula. |
| `max_qty` | `Decimal(20,5)?` | Target level: when `> 0` it is the `reorder_level`. |
| `par_qty` | `Decimal(20,5)?` | Trigger: a row is listed when `par_qty > 0` and `on_hand < par_qty`; fallback `reorder_level` when `max_qty = 0`. |
| `re_order_qty` | `Decimal(20,5)?` | Present in the schema; **not read** by the replenishment service. |
| Audit columns | — | Standard. |

**Constraints:** `@@unique([product_id, location_id, deleted_at])`. One policy row per `(product, location)`.

### 5.2 Response shape (`StockReplenishmentLocationResponseSchema`)

```
[
  { location_id, location_code, location_name,
    products_location: [
      { id, code, name, local_name, category{id,name}, sub_category{id,name}, item_group{id,name},
        on_hand_qty, min_qty, max_qty, par_qty, reorder_qty,
        status: low | warning | critical,
        product_location_id, inventory_unit_id, inventory_unit_name }
    ] }
]
summary: { total_locations, total_items, critical_count, warning_count, low_count, total_reorder_qty }
```

### 5.3 Create payloads

```
POST /api/{bu}/stock-replenishment/pr
{ workflow_id, products: [ { id, request_unit_id, request_qty, location_id } ] }

POST /api/{bu}/stock-replenishment/sr
{ workflow_id, products: [ { id, request_qty, location_id, from_location } ] }
→ data: [ <sr id>, … ]   (one per distinct (from_location, location_id) pair)
```

The frontend wizards (`stock-repl-pr-wizard.tsx`, `stock-repl-sr-wizard.tsx`) send the location(s) once at the top level; the gateway DTO expects them per line (`StockReplenishmentCreatePrSchema` / `…SrSchema`) — the wizard fans the chosen location out to every line before posting.

## 6. Algorithm / Lifecycle

```
GET (on screen load, optional ?location_id=, ?search=):
1. candidates = tb_product_location WHERE deleted_at IS NULL AND par_qty > 0
                AND location IS active AND location_type <> direct
                (optionally filtered by ?location_id= / product search)
2. on_hand[(location, product)] = Σ balance from the inventory ledger for the pair
3. for each candidate:
     par = par_qty; on_hand = max(raw_balance, 0); if on_hand >= par: skip
     reorder_level = max_qty > 0 ? max_qty : par
     reorder_qty   = max(reorder_level - on_hand, 0)
     status        = ratio(on_hand / par) <= 0.25 ? critical : <= 0.5 ? warning : low
4. group by location, sort rows by reorder_qty desc then name, page by location group

POST …/sr (user action):
1. verify(): workflow exists and is store_requisition type; caller is in its create stage;
             caller is assigned to every location_id (tb_location_user);
             every product is allowed by workflow.data.products (when that list is non-empty)
2. header = { requestor = caller, department = caller's first tb_department_user, workflow }
3. group lines by (from_location, location_id) → one StoreRequisitionLogic.create() per group
   (sr_type derived from the two locations; sr_no = draft-<hex>)
4. return the created ids → the SRs continue as ordinary drafts
```

`POST …/pr` is the same shape with one PR draft per call and per-line `request_unit_id` converted through the product's order units.

## 7. Cross-References

- [store-requisition](/en/inventory/store-requisition) — produced document type; downstream lifecycle identical (`SR_XMOD_011`)
- [purchase-request](/en/inventory/purchase-request) — the other produced document type
- [inventory](/en/inventory/inventory) — `on_hand` source for the shortfall calculation
- [product](/en/inventory/product) — `tb_product_location` policy lives under the product master
- [master-data/location](/en/inventory/master-data/location) — per-location par / max configuration
- [inventory/transaction](/en/inventory/inventory/transaction) — once the SR posts, the inventory transaction log (`tb_inventory_transaction`, `inventory_doc_type = store_requisition`) records the movement

## 8. References

- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/stock-replenishment/` — `stock-replenishment.service.ts` (`findAll`, `selectBelowPar`, `createPrByReplenishmentProduct`, `createSrByReplenishmentProduct`, `findPendingDocuments`, `buildDraftHeader`), `stock-replenishment.helper.ts` (`toReplenishmentStatus`, `toReorderQty`, `RATIO_CRITICAL = 0.25`, `RATIO_WARNING = 0.5`), `stock-replenishment.verify.ts`, `stock-replenishment.draft.ts`, `dto/stock-replenishment.dto.ts`, `dto/stock-replenishment.serializer.ts`; gateway `apps/backend-gateway/src/application/stock-replenishment/stock-replenishment.controller.ts` (app-ids `stockReplenishment.findAll` / `findPendingDocuments` / `createPr` / `createSr`).
- **Error catalogue:** `STOCK_REPLENISHMENT_WORKFLOW_NOT_FOUND`, `STOCK_REPLENISHMENT_WORKFLOW_PERMISSION_DENIED`, `STOCK_REPLENISHMENT_LOCATION_PERMISSION_DENIED`, `STOCK_REPLENISHMENT_PRODUCTS_NOT_APPLICABLE` in `packages/error-catalog/src/catalog.ts`.
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_product_location`, `tb_store_requisition`, `enum_sr_type`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/store-operation/stock-replenishment/` — `use-stock-replenishment.ts` (`useStockReplenishment`, `useCreateStockReplPr`, `useCreateStockReplSr`), `stock-repl-component.tsx`, `stock-repl-location.tsx`, `stock-repl-pr-wizard.tsx`, `stock-repl-sr-wizard.tsx`; `types/stock-replenishment.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/711-stock-replenishment.spec.ts` (33 cases, `TC-SRPL-*`: page load, summary bar, location groups, expand/collapse, selection, wizards); narrative in `docs/user-stories/711-stock-replenishment.md`.
- **Cron job:** none — `../micro-cronjobs/` has no replenishment code as of this pass.
- **Module landing:** [store-requisition](/en/inventory/store-requisition) § 7.
