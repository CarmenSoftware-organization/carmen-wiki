---
title: Physical Count — Data Model
description: Entities, fields, relationships, and enums for the physical-count module.
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Data Model

> **At a Glance**
> **Tables:** `tb_physical_count_period` &nbsp;·&nbsp; `tb_physical_count` &nbsp;·&nbsp; `tb_physical_count_detail` &nbsp;·&nbsp; per-level `_comment` tables (three)
> **Audience:** Developer / Auditor (dev reference)
> **Key FKs:** period `→ tb_period`; count `→ tb_location` and `→ tb_physical_count_period`; detail `→ tb_product` and `→ tb_unit` (`inventory_unit_id`). The variance rollup into [inventory-adjustment](/en/inventory/inventory-adjustment) has **no FK and no JSON linkage field at all** — the created `tb_stock_in`/`tb_stock_out` rows carry only a shared, human-readable description string
> **Audit pattern:** standard `created_*` / `updated_*` / `deleted_*`; three-level hierarchy (period → document → detail) — count itself does **not** write to the inventory ledger; the rollup at final submit creates already-`completed` stock-in/out documents that also do not write to the ledger (see § 3)

> **Source of truth:** Backend Prisma schema plus the service methods that read/write it. Always read both first when updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count-period/physical-count-period.service.ts`
>
> The `generated/client/schema.prisma` file under the Prisma package is an auto-generated copy and not authoritative.

## 1. Overview

The Physical Count module persists a three-level document tree under **`tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`**: a period header groups every count document opened against the same fiscal period (`tb_period`), each count document represents one `(period, location)` pairing, and each detail row is one product line on that count with `on_hand_qty` (book), `actual_qty` (counted), and `diff_qty` (variance). Comments and attachments hang off all three levels (`tb_physical_count_period_comment`, `tb_physical_count_comment`, `tb_physical_count_detail_comment`); the detail-level comment table is the one actually exercised by the live UI, via the entry screen's per-line "Add Notes" dialog (photo + free text).

The module sits **upstream of [inventory-adjustment](/en/inventory/inventory-adjustment)** in name only: when a count document's final **Submit** fires (`physical-count.service.ts` `submit()`), the service inserts variance lines directly into new `tb_stock_in` (overage) and/or `tb_stock_out` (shortage) rows — but it does so with a raw Prisma transaction that never imports or calls `InventoryTransactionService`, `executeAdjustmentIn`, or `executeAdjustmentOut`, the helpers `stock-in.service.ts`/`stock-out.service.ts` call for every one of their own detail lines. As a direct consequence: no `tb_inventory_transaction` row is created by this rollup, `adjustment_type_id` is left `null` on both created headers (no reason code), and neither header nor any detail row's `info` JSON field is populated with a back-reference to the source `tb_physical_count.id` — the only trace connecting the two documents is a shared, human-readable description string (`"Physical Count Adjustment - Period: <start> to <end>"`) and a per-line `note` string. Lot data on the count detail is sparse — `tb_physical_count_detail` carries only `on_hand_qty` / `actual_qty` per product at a location (no `lot_no` column) — and since the rollup never reaches the inventory-transaction/cost-layer code path, no lot is created or consumed by a physical count at all in the current implementation.

## 2. Entities

The canonical Prisma schema defines six tables (verified against `prisma-shared-schema-tenant/prisma/schema.prisma` lines 5370-5537):

- **`tb_physical_count_period`** — the period-level header grouping all count documents for one fiscal period (`period_id → tb_period`). Carries `status` on `enum_physical_count_period_status` (`draft`, `counting`, `completed`), defaulting to `draft`. **Confirmed gap:** no code path anywhere in the frontend or backend was found that ever sets this field to `counting` — `physical-count-period.service.ts`'s `findCurrent()` (used by the list screen) auto-creates a missing period at `status: draft`, and `physical-count.service.ts`'s `create()` unconditionally rejects with `"Physical Count Period is not in counting status"` unless the period is already `counting`. The only way a period reaches `counting` appears to be an explicit `POST /physical-count-periods` call with `status` set directly in the request body — the Bruno sample body for that endpoint itself sends `"status": null` (which falls back to `draft`), and no frontend screen calls the create/update hooks for this endpoint at all (`useCreatePhysicalCountPeriod`/`useUpdatePhysicalCountPeriod` are exported but unused by any route). Flagged in the progress log as an unconfirmed likely gap rather than asserted as a guaranteed defect, since a pre-seeded tenant could hold periods already at `counting`.
- **`tb_physical_count_period_comment`** — period-level comments / attachments. Carries `message`, `attachments` JSON array, and `enum_comment_type` (`user` / `system`). No UI in the current frontend surfaces period-level comments.
- **`tb_physical_count`** — the count document for one `(period, location)` pair. Carries `location_id → tb_location`, snapshot `location_code` / `location_name`, `physical_count_type` (`enum_physical_count_type`, schema default `yes`, but never explicitly set by `create()` — every document created through the real flow simply keeps this default; there is no frozen-vs-live behavioural branch anywhere in the code, see [physical-count](/en/inventory/physical-count) § 3), `description`, `status` on `enum_physical_count_status` (`pending`, `in_progress`, `completed` — `create()` sets new documents straight to `in_progress`, so `pending` is not reachable through the confirmed create path; it is referenced only as part of a combined `{pending, in_progress}` filter in the cross-BU "pending count" dashboard widget query), `start_counting_at` / `start_counting_by_id` (stamped immediately at creation, not on the counter's first line entry), `completed_at` / `completed_by_id`, progress counters `product_counted` / `product_total`, and `doc_version` (`Int @db.Integer`, default `0`) — optimistic-concurrency version counter required on every `save`/`update`/`review`/`submit` call; a mismatch is converted to a `409`-style `ALREADY_EXISTS` result by the shared `@TryCatch` decorator (see [system-config/doc-version](/en/inventory/system-config/doc-version)). Unique within `(physical_count_period_id, location_id, deleted_at)`.
- **`tb_physical_count_comment`** — document-level comments / attachments on a count. No UI in the current frontend surfaces document-level comments (only detail-level, see below).
- **`tb_physical_count_detail`** — the per-product count line. Carries `product_id`, snapshot `product_code` / `product_name` / `product_local_name` / `product_sku`, `inventory_unit_id` (FK to `tb_unit`), `on_hand_qty` (seeded `0` at creation; only recomputed to a live figure by the **Submit for Review** step, `reviewItems()` — see [physical-count](/en/inventory/physical-count) § 3), `actual_qty` (seeded `null`; set by **Save**, or overwritten by **Submit for Review**), `diff_qty` (`actual_qty − on_hand_qty`), `counted_at` / `counted_by_id` (stamped **only** by the **Save** call, not by Submit for Review — see the discrepancy note on [physical-count](/en/inventory/physical-count) § 3), and `sequence_no` for sheet ordering.
- **`tb_physical_count_detail_comment`** — line-level comments / attachments on a count detail row. This is the one comment table the live UI actually uses: the entry screen's per-line "Add Notes" dialog (`pc-entry-notes-dialog.tsx`) reads/writes it via `GET`/`POST /physical-count-detail-comments/:detailId`, storing free text plus photo attachments.

## 3. Relationships

```
tb_period
    │
    └─1──*──► tb_physical_count_period  (status: draft → counting → completed;
                │                          no confirmed code path sets counting — see § 2)
                │
                ├─1──*──► tb_physical_count_period_comment
                │
                └─1──*──► tb_physical_count  (one row per (period, location);
                            │                  status: pending → in_progress → completed;
                            │                  created already in_progress, not pending;
                            │                  physical_count_type stays at its schema
                            │                  default — no frozen/live branch exists)
                            │
                            ├─1──*──► tb_physical_count_comment  (unused by current UI)
                            │
                            └─1──*──► tb_physical_count_detail
                                        │   (on_hand_qty stays 0 until Submit for Review;
                                        │    actual_qty / diff_qty; counted_at / counted_by_id
                                        │    stamped only by Save; no lot_no column)
                                        │
                                        └─1──*──► tb_physical_count_detail_comment  (real: photo/notes)

At final Submit, the backend groups non-zero-diff_qty lines by sign and inserts,
in one transaction, orphan documents with NO linking field back to the count:
    ▼
tb_stock_in  (doc_status = completed directly; adjustment_type_id = null)   for diff_qty > 0 lines
tb_stock_out (doc_status = completed directly; adjustment_type_id = null)   for diff_qty < 0 lines
    │
    └── description / detail.note = free-text "Physical Count Adjustment - Period: …" string only
    │
    └── NO tb_inventory_transaction row is created by this action (no executeAdjustmentIn/Out call)
```

Notes:

- **Three-level hierarchy, but the bottom two levels are the only ones with a live UI.** The period header exists to group locations under one fiscal period; the frontend's list screen (`physical-count`) reads it via `GET /physical-count-periods/current`, auto-provisioning a `draft` period the first time it is requested for a newly-opened fiscal period.
- **No FK and no structured JSON linkage for the variance rollup.** Earlier drafts of this page described an `info.countId` / `info.countPeriodId` convention on the created `tb_stock_in`/`tb_stock_out` rows. Direct reading of `physical-count.service.ts`'s `submit()` method (lines ~934-1036) shows neither the header's nor any detail row's `info` field is ever written — the rollup's only trace back to its source count is a shared, unstructured description string. Reconstructing "which count produced this stock-in/out" from the ledger side is therefore not possible via any indexed field.
- **All explicit `@relation` FK declarations use `onDelete: NoAction` or `onDelete: Cascade`** — preserving soft-delete (`deleted_at`) semantics.

## 4. Enums

- **`enum_physical_count_period_status`** — period-level lifecycle. Three values: `draft`, `counting`, `completed`. See the confirmed gap noted in § 2 — no code path was found that transitions a period from `draft` to `counting`.
- **`enum_physical_count_status`** — document-level lifecycle. Three values: `pending`, `in_progress`, `completed`. `pending` is defined on the enum but is not reachable through the confirmed `create()` path (every document is created directly at `in_progress`).
- **`enum_physical_count_type`** — two values, `yes` / `no`. Declared on **both** `tb_location` (default `no`; the per-location "is this location required for physical count" admin flag, edited on the location's own config form) and `tb_physical_count` (default `yes`; never explicitly set by `create()`, so it stays at its default on every real document). There is no frozen-vs-live behavioural branch anywhere in the codebase associated with this enum — see [physical-count](/en/inventory/physical-count) § 3.
- **`enum_physical_count_costing_method`** — a separate top-level enum (`standard`, `last`, `average`, `last_receiving`) that does **not** appear as a field on any physical-count table. It is read once per final `submit()` as a **business-unit-wide tenant config value** (`enum_business_unit_config_key.physical_count_costing_method`, default fallback `last_receiving` if unset or invalid), via `TenantService.getBuConfig()`, and applied uniformly to every variance line's `cost_per_unit` for that submit. No frontend screen was found that lets a user set this config key.
- **`enum_transaction_type`** — at the inventory ledger level. `physical-count` is not a value on this enum, and — per § 1/§ 3 above — the values `adjustment_in`/`adjustment_out` that a normal inventory-adjustment posting would produce are never written by this module's own rollup at all, since no `tb_inventory_transaction` row is created.

## 5. Divergences from carmen/docs

No `carmen/docs` source folder exists for this module. Two aspirational planning documents in the E2E repo (`docs/persona-doc/System Process/tx-08-physical-stocktake.md` and `docs/test-cases/750-physical-count.md`, `docs/user-stories/750-physical-count.md`) describe a design that diverges sharply from the current implementation — see [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) § 5.1 for the point-by-point comparison (own transaction type vs. actual Stock In/Out reuse; a `FINALIZED`/GL-posted status that does not exist; a transaction lock during counting that has no matching code; tolerance and recount mechanics that have no matching code).

## 6. References

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — six entities (`tb_physical_count_period`, `tb_physical_count_period_comment`, `tb_physical_count`, `tb_physical_count_comment`, `tb_physical_count_detail`, `tb_physical_count_detail_comment`); four enums (`enum_physical_count_period_status`, `enum_physical_count_status`, `enum_physical_count_type`, `enum_physical_count_costing_method`).
- **Service layer:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts` (create/refresh/save/reviewItems/submit/delete/update); `.../physical-count-period/physical-count-period.service.ts` (findCurrent/create/update); `.../period-end/period-end.validate.ts` (`validatePhysicalCount`, the period-close gate).
- **Secondary (aspirational, not implemented):** `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-08-physical-stocktake.md`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/` (`pc-component.tsx`, `pc-entry-component.tsx`, `pc-review-component.tsx`); `types/physical-count.ts`; `hooks/use-physical-count.ts`, `hooks/use-physical-count-period.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists.
- Related modules: [inventory](/en/inventory/inventory) (ledger that a *normal* inventory-adjustment posting writes to — not reached by this module's own rollup), [inventory-adjustment](/en/inventory/inventory-adjustment) (the tables the rollup writes into, bypassing that module's service layer), [spot-check](/en/inventory/spot-check) (partial-count cousin using a separate document tree).
