---
title: Physical Count — Business Rules
description: Validation, calculation, authorization, posting, and cross-module rules for physical counts.
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# Physical Count — Business Rules

> **At a Glance**
> **Rule families:** `PHC_VAL_*` validation &nbsp;·&nbsp; `PHC_AUTH_*` permission &nbsp;·&nbsp; `PHC_CALC_*` calc &nbsp;·&nbsp; `PHC_POST_*` posting &nbsp;·&nbsp; `PHC_XMOD_*` cross-module
> **Rule count:** 16 rules, re-verified against `physical-count.service.ts` / `physical-count-period.service.ts` / `period-end.validate.ts`
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Status lifecycle:** § 5.1 carries a point-by-point Live Code vs planning-document discrepancy table

## 1. Overview

This page catalogues the operational rules actually enforced by the **physical-count module** — the three-level document tree (`tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`) and the single-screen-family flow (list → entry → review → submit) described in [physical-count/03-user-flow](/en/inventory/physical-count/03-user-flow). Every rule below was checked against `physical-count.service.ts`, `physical-count-period.service.ts`, `period-end.validate.ts`, and the frontend components in `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/`; rules that appeared in earlier drafts of this page with no matching code (recount, tolerance thresholds, location transaction-lock, GL posting, a distinct Approver/Auditor/Sysadmin surface) have been removed rather than kept as unconfirmed scaffolding, since a repo-wide search found zero supporting code for any of them. Rule IDs follow `PHC_VAL_*` (validation), `PHC_CALC_*` (calculation), `PHC_AUTH_*` (authorization), `PHC_POST_*` (posting), `PHC_XMOD_*` (cross-module).

Two structural notes colour every rule below. **First**, the variance rollup at final Submit writes directly into `tb_stock_in`/`tb_stock_out` (the tables [inventory-adjustment](/en/inventory/inventory-adjustment) also uses) but bypasses that module's own service layer entirely — no `tb_inventory_transaction` row, no reason code, and no linkage field are created (see [physical-count/01-data-model](/en/inventory/physical-count/01-data-model) § 1/§ 3). **Second**, there is no `carmen/docs` source for `PHC_*` rules; § 5.1 below instead compares the live code against two aspirational planning documents from the E2E repo that describe a materially different, not-yet-built design.

## 2. Validation Rules

Rule IDs follow `PHC_VAL_NNN`.

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `PHC_VAL_001` | `tb_physical_count_period.status` must already be `counting` for the target period. | Create count document (`POST /physical-counts`) | Reject with `"Physical Count Period is not in counting status"`. No confirmed code path transitions a period from `draft` to `counting` — see [physical-count/01-data-model](/en/inventory/physical-count/01-data-model) § 2. |
| `PHC_VAL_002` | `location_id` must reference an existing, non-deleted `tb_location`. | Create count document | Reject with a location-not-found error. The `create()` method does **not** independently check `location_type` or `is_active`/`physical_count_type` — the list screen only ever offers locations already filtered by `findCurrent()` (`location_type ∈ {inventory, consignment}`, `is_active = true`, and — unless "include not-counted" is checked — `physical_count_type = yes`), so the location-type restriction is enforced by what the UI shows, not by the create endpoint itself. |
| `PHC_VAL_003` | If a `tb_physical_count` already exists for `(period, location)`, `create()` does not create a duplicate — it re-runs the product union and appends any newly-qualifying lines to the existing document, then returns that document's `id`/`doc_version`. | Create count document (idempotent path) | No error; acts as an implicit "resume/refresh" rather than a conflict. |
| `PHC_VAL_004` | Every `tb_physical_count_detail` line must have `counted_at != null` before the document can be submitted. | Submit (`PATCH .../submit`) | Reject with `"<N> products have not been counted yet"`. Only the **Save** call (`PATCH .../save`) stamps `counted_at` — **Submit for Review** (`PATCH .../review`) does not, see [physical-count](/en/inventory/physical-count) § 3. |
| `PHC_VAL_005` | `actual_qty` is parsed client-side with `Math.max(0, Number.parseFloat(raw) || 0)` (`entry-item-row.tsx`) — negative input is clamped to `0` before it ever reaches the API. No matching server-side minimum check was found in `physical-count.service.ts`. | Line entry (client-side only) | Non-numeric or negative input is silently clamped to a valid number in the UI; not confirmed as independently enforced by the backend. |
| `PHC_VAL_006` | `tb_physical_count.status === completed` blocks **Save**, **Submit for Review**, and **Submit** (`"Physical Count is already completed"`) and blocks **Delete** (`"Cannot delete completed Physical Count"`). | Save / Review / Submit / Delete | Reject with the quoted message. There is no equivalent guard on **Update** (`PATCH .../physical-counts/:id`, the legacy `description`-only edit) — it accepts a description change on a `completed` document if called directly, though this route is not reachable from the real navigation flow (see [physical-count](/en/inventory/physical-count) § 1). |
| `PHC_VAL_007` | Every `save`/`update`/`review`/`submit` call must supply the current `doc_version`; a mismatch against the stored value is converted by the shared `@TryCatch` decorator into a `409`-style `ALREADY_EXISTS` result. | Save / Update / Review / Submit | Reject on `doc_version` mismatch; increment on success. See [system-config/doc-version](/en/inventory/system-config/doc-version). |

> **Not found in code (removed from this catalogue):** a tolerance-threshold percentage or absolute-quantity check driving a "flag for recount" state; a distinct recount action performed by "a different counter"; a location-level transaction lock blocking GRN/SR/other postings while a count is `in_progress`; a "blind count" toggle hiding book quantity from the counter (the entry screen simply never renders `on_hand_qty` to the counter at all, by page design, not a configurable toggle).

## 3. Calculation Rules

Rule IDs follow `PHC_CALC_NNN`. Quantity fields are `Decimal(20, 5)` on `tb_physical_count_detail.on_hand_qty` / `actual_qty` / `diff_qty`.

| Rule ID | Formula |
| ------- | ------- |
| `PHC_CALC_001` (variance qty) | `diff_qty = actual_qty − on_hand_qty` per line, computed server-side both by `save()` (against whatever `on_hand_qty` is currently stored) and by `reviewItems()` (against a freshly-recomputed live `on_hand_qty`). |
| `PHC_CALC_002` (on-hand recomputation) | `reviewItems()` computes `on_hand_qty` for **every** line as `Σ tb_inventory_transaction_detail.qty` at the count's `location_id`, grouped by `product_id`, with **no date cut-off** — it is the current ledger balance at the moment "Submit for Review" is clicked, not a value frozen when the sheet was created. |
| `PHC_CALC_003` (progress) | `product_counted` is recomputed on every `save()`/`reviewItems()` call as the count of lines with a non-null/non-zero effective `actual_qty`; `product_total` is the count of lines on the sheet (set at create/refresh time). The entry screen's percent-complete figure is `Math.round(counted / total × 100)`, computed client-side from the same numbers. |
| `PHC_CALC_004` (rollup cost) | At final `submit()`, each variance line's `cost_per_unit` is looked up once per submit via `CostingService.getCostsPerUnit()`, using the single business-unit-wide method resolved from `enum_business_unit_config_key.physical_count_costing_method` (default `last_receiving` if unset/invalid); `total_cost = cost_per_unit × |diff_qty|`. All lines in the same submit share the same method — there is no per-line or per-count override. |

## 4. Authorization Rules

Rule IDs follow `PHC_AUTH_NNN`.

| Rule ID | Rule |
| ------- | ---- |
| `PHC_AUTH_001` | Every list, create, save, review, submit, refresh, delete, and comment action in this module is gated by one CRUD permission key: `inventory_management.physical_count` (`constant/permissions.ts`). No distinct create-only, approve-only, or read-only permission variant was found for this module. |
| `PHC_AUTH_002` | No zone-based, location-scoped-to-user, or "assigned counter" restriction was found in `physical-count.service.ts` — any user holding the module permission can open, enter, and submit any count document. A generic `tb_user_location` table exists in the schema for location-level access grants elsewhere in the product, but no reference to it was found anywhere in this module's own service code; treat a "counter is scoped to their assigned location" claim as unconfirmed for this module specifically. |
| `PHC_AUTH_003` | No Approver/Finance Reviewer, Auditor, or Sysadmin permission, route, or workflow stage exists for this module — the "review" and final "submit" steps are both performed by the same permission-gated user who did the counting, in the same session. |

## 5. Posting Rules

Rule IDs follow `PHC_POST_NNN`. "Posting" in this module means the variance-rollup transaction that fires inside `submit()`.

| Rule ID | Rule |
| ------- | ---- |
| `PHC_POST_001` | On `submit()`, the service partitions the detail rows with `diff_qty ≠ 0` by sign: all positive-variance lines go into **one** new `tb_stock_in`; all negative-variance lines go into **one** new `tb_stock_out`. Lines with `diff_qty = 0` produce no rollup row. Both created headers are inserted with `doc_status: enum_doc_status.completed` directly — there is no draft or approval stage, matching the same "create() posts completed unconditionally" pattern already confirmed for the inventory-adjustment module's own Stock In/Out screens. |
| `PHC_POST_002` | Neither the created header's nor any detail row's `info` JSON field is populated — there is **no** structured linkage (no `info.countId`, no reason code on `adjustment_type_id`, which is left `null`) back to the source `tb_physical_count`. The only connective tissue is a shared, human-readable `description`/`note` string containing the period's date range. |
| `PHC_POST_003` | `submit()` does **not** call `InventoryTransactionService.executeAdjustmentIn`/`executeAdjustmentOut` — no `tb_inventory_transaction` row is written by this action. The rollup's `tb_stock_in`/`tb_stock_out` documents exist purely as records; they do not themselves move the on-hand balance the way a normal Stock In/Out create (in [inventory-adjustment](/en/inventory/inventory-adjustment)) does. |
| `PHC_POST_004` | Once `submit()` succeeds, `tb_physical_count.status` becomes `completed` and `completed_at`/`completed_by_id` are stamped; the document is then rejected by `save()`/`reviewItems()`/`submit()`'s own completed-guard (`PHC_VAL_006`) — any further correction requires raising a fresh, independent adjustment through [inventory-adjustment](/en/inventory/inventory-adjustment), not a re-open of the count. |

## 5.1 Live Code vs Planning-Document Discrepancies

No `carmen/docs` catalogue of `PHC-*` rules exists for this module. The closest available reference is a planning-stage document in the E2E repo, `docs/persona-doc/System Process/tx-08-physical-stocktake.md` (version 1.1.1, 2026-04-27) — a BRD-style design note, **not** an automated test or confirmed-shipped behaviour. Direct reading of the current implementation shows it diverges from that document on nearly every substantive point:

> Diff legend: 🔵 planning-document only (no matching code) · 🔴 live code differs from the planning document's description

| Topic | Planning document (`tx-08-physical-stocktake.md`) | Live code | Diff |
|---|---|---|---|
| Transaction type | "Posted as its own **Physical Stocktake transaction type** — **not** a Stock In/Out adjustment." | `submit()` creates literal `tb_stock_in`/`tb_stock_out` rows — the exact mechanism the planning document says it is not. No distinct physical-count transaction type exists on `enum_transaction_type`. | 🔴 |
| Ledger effect | Variance "changes QOH", "adjusts lots", triggers "Cost Calculation" (AVCO re-average / FIFO layer add). | None of this happens: `submit()` never calls the inventory-transaction/cost-layer services, so no `tb_inventory_transaction`, lot, or cost-layer effect is produced by this action at all (§ `PHC_POST_003`). | 🔴 |
| Status lifecycle | Three states: `IN PROGRESS → COMPLETED → FINALIZED`, where `FINALIZED` means "variance adjustments posted to GL" and is required for End Period Close Stage 3. | `enum_physical_count_status` has three values (`pending`, `in_progress`, `completed`) but no `finalized` value and no GL-posting step anywhere in the codebase; `completed` is the terminal state. The real period-end gate (`period-end.validate.ts`'s `validatePhysicalCount`) only checks for `status = completed` at each required location — there is no separate GL-posted milestone to satisfy. | 🔴 |
| Transaction lock | "Transactions at a location are locked while the Physical Count is IN PROGRESS" — GRN, CRN, SR, Issues, Sales, Stock In/Out adj all blocked. | No matching guard was found anywhere in the GRN, SR, or stock-in/out services — a repeat, targeted search for a physical-count check in those modules returned zero hits. | 🔵 |
| Tolerance / recount | Implied by an earlier draft of this wiki page, not actually present in `tx-08`. | No tolerance percentage, absolute-quantity threshold, or recount flow exists in either the frontend or backend for this module. | 🔵 |
| Positive-variance lot handling | "New lot created (or existing lot adjusted up — TBC)." | Moot — no lot is created or adjusted by this module's rollup, since the inventory-transaction/lot code path is never reached. | 🔴 |

**Recommendation for testers:** treat `tx-08-physical-stocktake.md` as a design aspiration, not a spec of current behaviour. Assertions in test scenarios should be written against the live `enum_physical_count_status` values and the confirmed rollup mechanics above, not against `FINALIZED`/GL posting/location-lock language.

## 6. Cross-Module Rules

Rule IDs follow `PHC_XMOD_NNN`.

| Rule ID | Rule |
| ------- | ---- |
| `PHC_XMOD_001` | **→ [inventory-adjustment](/en/inventory/inventory-adjustment)**: the rollup at Submit writes directly into that module's `tb_stock_in`/`tb_stock_out` tables, but bypasses its service layer — see § 5 above. |
| `PHC_XMOD_002` | **→ [inventory](/en/inventory/inventory)**: no ledger effect is produced by this module's own rollup (`PHC_POST_003`); any ledger effect from the resulting stock-in/out rows would require a separate process this repo does not contain. |
| `PHC_XMOD_003` | **→ [system-config/period](/en/inventory/system-config/period)**: `period-end.validate.ts`'s `validatePhysicalCount` blocks period close until every required location (`location_type ∈ {inventory, consignment}`, `physical_count_type = yes`, `is_active = true`) has a `completed` `tb_physical_count` under the closing period. This is the one confirmed, real cross-module gate this module participates in. |
| `PHC_XMOD_004` | **→ [spot-check](/en/inventory/spot-check)**: a separate module and document tree for narrower, partial counts; not a child of `tb_physical_count_period` and not otherwise linked in the schema. |

## 7. References

- **Primary:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts` (create/refresh/save/reviewItems/submit/delete/update), `.../physical-count-period/physical-count-period.service.ts` (findCurrent/create/update), `.../period-end/period-end.validate.ts` (`validatePhysicalCount`).
- **Secondary (aspirational, not implemented):** `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-08-physical-stocktake.md`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/` (`pc-component.tsx`, `pc-entry-component.tsx`, `pc-review-component.tsx`, `entry-item-row.tsx`); `constant/permissions.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no physical-count spec currently exists.
- Related rule sets: [inventory-adjustment/02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) (the tables the rollup writes into), [inventory/02-business-rules](/en/inventory/inventory/02-business-rules) (ledger semantics — not reached by this module's rollup), [system-config/period](/en/inventory/system-config/period) (the real cross-module gate, `PHC_XMOD_003`).
