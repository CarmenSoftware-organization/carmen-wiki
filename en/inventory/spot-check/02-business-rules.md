---
title: Spot Check — Business Rules
description: Validation, calculation, authorization, posting, and cross-module rules for spot checks.
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# Spot Check — Business Rules

> **At a Glance**
> **Rule families:** `SPC_VAL_*` validation &nbsp;·&nbsp; `SPC_AUTH_*` permission &nbsp;·&nbsp; `SPC_CALC_*` calc &nbsp;·&nbsp; `SPC_POST_*` posting &nbsp;·&nbsp; `SPC_XMOD_*` cross-module
> **Rule count:** 14 rules, re-verified against `spot-check.service.ts` / `spot-check.logic.ts`
> **Audience:** Test author + developer — every rule ID is anchored from `04-test-scenarios*` pages
> **Status lifecycle:** § 5.1 carries a point-by-point Live Code vs planning-document comparison

## 1. Overview

This page catalogues the operational rules actually enforced by the **spot-check module** — the flat two-level document tree (`tb_spot_check` → `tb_spot_check_detail`) and the single-screen-family flow (list → create → entry → review → submit) described in [spot-check/03-user-flow](/en/inventory/spot-check/03-user-flow). Every rule below was checked against `spot-check.service.ts`, `spot-check.logic.ts`, and the frontend components in `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/`; rules that appeared in earlier drafts of this page with no matching code (recount, variance-tolerance thresholds, a rollup into `tb_stock_in`/`tb_stock_out`, GL posting, a distinct Approver/Auditor/Sysadmin surface) have been removed rather than kept as unconfirmed scaffolding, since a repo-wide search found zero supporting code for any of them. Rule IDs follow `SPC_VAL_*` (validation), `SPC_CALC_*` (calculation), `SPC_AUTH_*` (authorization), `SPC_POST_*` (posting), `SPC_XMOD_*` (cross-module).

Two structural notes colour every rule below. **First**, unlike [physical-count](/en/inventory/physical-count) — whose own rollup at least creates raw, unposted `tb_stock_in`/`tb_stock_out` rows — a spot check's final submit writes nothing anywhere except its own `doc_status`/`end_date`. **Second**, there is no `carmen/docs` source for `SPC_*` rules; § 5.1 below instead compares the live code against one planning-stage document from the E2E repo whose core "posting is pending" claim the live code actually matches, but whose status-lifecycle detail does not.

## 2. Validation Rules

Rule IDs follow `SPC_VAL_NNN`.

| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |
| `SPC_VAL_001` | `location_id` must reference an existing, non-deleted `tb_location`. | Create (`POST /spot-checks`) | Reject with `COMMON_LOCATION_NOT_FOUND`. No independent check on `location_type` or `is_active` inside `create()` itself — the list screen only ever offers locations already filtered by `findCurrentByLocation()` (`location_type ∈ {inventory, consignment}`, `is_active = true`, and — unless "Include Not Count" is checked — `physical_count_type = yes`). |
| `SPC_VAL_002` | The eligible product pool (union of `tb_product_location` assignments and any product with non-zero net stock at the location) must be non-empty. | Create | Reject with `"No products found at this location"`. |
| `SPC_VAL_003` | `method = manual` requires a non-empty `product_id[]` array; after filtering to products actually in the eligible pool, at least one must remain. | Create | Reject with `"product_id is required for manual selection"` (empty/missing array) or `"None of the selected products were found at this location"` (all filtered out). |
| `SPC_VAL_004` | `method = high_value` requires at least one `tb_period` row with `status ∈ {open, locked}` to exist. | Create | Reject with `SPOT_CHECK_NO_ACTIVE_PERIOD` ("No active period found") if none does. |
| `SPC_VAL_005` | Only `doc_status = pending` documents can be updated (`description`/`note` only — no other field is editable via `update()`). | Update | Reject with `"Only pending spot checks can be updated"`. **Not reachable through any shipped screen** — see [spot-check](/en/inventory/spot-check) § 1; only Bruno/direct-API calls exercise this path. |
| `SPC_VAL_006` | `doc_status = void` or `= completed` blocks Reset (`"Spot check is already void"` / `"Completed spot check cannot be reset"`). `pending`/`in_progress` are the only resettable states. | Reset | Reject with the quoted message on `void`/`completed`; allow otherwise. |
| `SPC_VAL_007` | Save (`saveItems()`) requires a non-empty `items[]` array, and the document must be `pending` or `in_progress`. | Save | Reject with `SPOT_CHECK_NO_ITEMS` ("No items to save") on an empty array, or `"Cannot save items when spot check is <status>"` outside `{pending, in_progress}`. |
| `SPC_VAL_008` | `submit()` (final) rejects only on `doc_status = completed` or `= void`. **There is no completeness check** — a document with lines still at their seeded `actual_qty = 0` can be submitted to `completed` without error. | Submit | Reject with `"Spot check is already completed"` / `"Void spot check cannot be submitted"`; otherwise always succeeds. |

> **Not found in code (removed from this catalogue):** a tolerance-threshold percentage or absolute-quantity check driving a "flag for recount" state; a distinct recount action performed by a different counter; a location-level transaction lock blocking GRN/SR/other postings while a spot check is open; a "blind count" toggle (the entry screen simply never renders `on_hand_qty` to the counter at all, by page design, not a configurable toggle); a completeness gate at the API layer (only the client-side button visibility enforces "all lines counted").

## 3. Calculation Rules

Rule IDs follow `SPC_CALC_NNN`. Quantity fields are `Decimal(20, 5)` on `tb_spot_check_detail.on_hand_qty` / `actual_qty` / `diff_qty`.

| Rule ID | Formula |
| ------- | ------- |
| `SPC_CALC_001` (variance qty) | `diff_qty = actual_qty − on_hand_qty` per line, computed server-side by both `saveItems()` (against whichever `on_hand_qty` is currently stored) and `reviewItems()` (against a freshly-recomputed live `on_hand_qty`). |
| `SPC_CALC_002` (on-hand recomputation at review) | `reviewItems()` computes `on_hand_qty` for every line as `Σ tb_inventory_transaction_detail.qty` at the spot check's `location_id`, grouped by `product_id`, with no date cut-off — the live ledger balance at the moment "Submit for Review" is clicked, which can differ from the figure captured at creation. |
| `SPC_CALC_003` (review summary) | `getReview()`/the review payload compute `matched = count(diff_qty === 0)`, `variant = total − matched`; the review screen additionally derives `overages = count(diff_qty > 0)` and `shortages = count(diff_qty < 0)` client-side from the same `diff_qty` values. **No monetary variance value is calculated anywhere** — `diff_qty × cost_per_unit` does not exist in this module; cost only appears as a *selection-ranking* input for the `high_value` sampling method (§ 4 below), never as a valuation of the counted variance. |
| `SPC_CALC_004` (high-value ranking) | For `method = high_value`: rank each pool product by `on_hand_qty × max(cost_per_unit)`, where the max cost is read from `tb_inventory_transaction_cost_layer` rows at that location with `in_qty > 0` and a `lot_at_date` inside the active period's `[start_at, end_at]` window; products under an optional `minimum_cost` floor are excluded; products with no discoverable cost are appended after the costed group (only when no `minimum_cost` is set), ordered by most-recently-assigned-to-location first; the first `size` (or fewer, if the pool is smaller) are kept. |

## 4. Authorization Rules

Rule IDs follow `SPC_AUTH_NNN`.

| Rule ID | Rule |
| ------- | ---- |
| `SPC_AUTH_001` | Every list, create, save, review, submit, reset, delete, and comment action in this module is gated by one CRUD permission key: `inventory_management.spot_check` (`constant/permissions.ts`). No distinct create-only, approve-only, or read-only permission variant was found. |
| `SPC_AUTH_002` | No zone-based, location-scoped-to-user, or "assigned counter" restriction was found in `spot-check.service.ts` — any user holding the module permission can open, count, and submit any spot check at any location. A generic `tb_user_location` table exists elsewhere in the schema for location-level access grants, but no reference to it was found in this module's own service code. |
| `SPC_AUTH_003` | No Approver/Finance Reviewer, Auditor, or Sysadmin permission, route, or workflow stage exists for this module — there is nothing to review or approve, since the final submit has no downstream document or ledger effect to gate. |

## 5. Posting Rules

Rule IDs follow `SPC_POST_NNN`. "Posting," for this module, means only the state change performed by `submit()` — there is no rollup, no adjustment document, no ledger write.

| Rule ID | Rule |
| ------- | ---- |
| `SPC_POST_001` | `submit()` sets `doc_status = completed` and stamps `end_date = now()`. That is the entire effect of the final submit. |
| `SPC_POST_002` | No `tb_stock_in`/`tb_stock_out` document is created, and no `tb_inventory_transaction` row is written, by `submit()` — confirmed by both the absence of any matching import/call in `spot-check.service.ts` and the method's own doc-comment: *"Does not create stock-in/stock-out — any follow-up adjustments are user-driven."* This is a materially simpler (and less automated) mechanism than [physical-count](/en/inventory/physical-count)'s own final submit, which at least creates raw stock-in/out rows without posting them to the ledger. |
| `SPC_POST_003` | Correcting a confirmed variance therefore requires a user to separately create an ordinary [inventory-adjustment](/en/inventory/inventory-adjustment) Stock In/Out document. No field, JSON convention, or description string links that document back to the spot check that surfaced the variance — the audit trail, if any is needed, must be reconstructed manually (e.g. by matching location and date). |
| `SPC_POST_004` | Once `submit()` succeeds, further Save/Submit-for-Review calls against the same document are rejected by `SPC_VAL_007` (`saveItems()`'s own status guard). **`reviewItems()` has no equivalent guard** — it will recompute and overwrite `on_hand_qty`/`actual_qty`/`diff_qty`/`counted_at` on every detail row of an already-`completed` (or `void`) document if that endpoint is called again, e.g. by reopening a completed spot check from the list's History tab (whose click handler routes to the same entry screen regardless of status) and clicking through to "Submit for Review" a second time. Only the terminal `submit()` call itself is guarded (`SPC_VAL_008`). This is a confirmed gap in the code, not independently exercised by any automated test. |

## 5.1 Live Code vs Planning-Document Comparison

No `carmen/docs` catalogue of `SPC-*` rules exists for this module. The closest available reference is a planning-stage document in the E2E repo, `docs/persona-doc/System Process/tx-10-spot-check.md` (v1.0.0, 2026-04-27) — a BRD-style design note, not an automated test or confirmed-shipped behaviour.

> Diff legend: ✅ matches live code · 🟡 renamed/collapsed in live schema · 🔴 planning-document only (no matching code)

| Topic | Planning document (`tx-10-spot-check.md`) | Live code | Diff |
|---|---|---|---|
| Variance posting to inventory | "Real-time variance posting to inventory is listed as **Pending** — not yet implemented... does not post variance adjustments to inventory, lots, or cost." | Confirmed exactly: `submit()` has no posting effect of any kind, and its own doc-comment states this directly. | ✅ |
| Status set | Six values: `draft`, `pending`, `in-progress`, `on-hold`, `completed`, `cancelled`. | `enum_spot_check_status` has four: `pending`, `in_progress`, `void`, `completed`. The document's `draft`/`pending` pre-count distinction and the `on-hold` pause state have no schema equivalent; `cancelled` maps to the live `void`. | 🟡 |
| Check types | Five: `random`, `targeted`, `high-value`, `variance-based`, `cycle-count`. | `enum_spot_check_method` has three: `random`, `high_value`, `manual`. `targeted`/`variance-based`/`cycle-count` have no schema equivalent; the closest live analogue to "targeted" is `manual` (explicit product picking). | 🟡 |
| Reference format | `SC-YYMMDD-XXXX`. | The running-code service generates `spot_check_no` from a configurable date + sequence pattern of type `SPOT-CHECK` — the exact format is tenant-configured via the shared running-code screens, not hardcoded to `SC-YYMMDD-XXXX`. | 🟡 |
| Period-end gate | "All Spot Checks must be `completed` before End Period Close Stage 2." | A repo-wide search of `period-end.validate.ts` for any `spot` reference returned zero hits — spot check is **not** a period-end gate of any kind, consistent with the same finding already confirmed for the [inventory](/en/inventory/inventory) module's own period-end pass. | 🔴 |
| Pause/resume | `in-progress → on-hold → in-progress`, for "staff/items unavailable." | No `on_hold`/pause state exists; a user can simply leave the entry screen and return later (the document stays `in_progress` or `pending` with whatever was locally unsaved, lost — only a Save call persists progress). | 🔴 |

**Recommendation for testers:** treat `tx-10-spot-check.md`'s "posting is pending" framing as confirmed and durable — there is no evidence a posting feature is imminent — but write status-lifecycle assertions against the real four-value `enum_spot_check_status`, not the six-value planning description.

## 6. Cross-Module Rules

Rule IDs follow `SPC_XMOD_NNN`.

| Rule ID | Rule |
| ------- | ---- |
| `SPC_XMOD_001` | **→ [inventory-adjustment](/en/inventory/inventory-adjustment)**: no automated link exists. A confirmed variance is corrected only by a user manually creating a separate Stock In/Out document there — nothing about the spot check itself references, triggers, or pre-fills that action. |
| `SPC_XMOD_002` | **→ [inventory](/en/inventory/inventory)**: a spot check reads the ledger (`tb_inventory_transaction_detail`) twice — once to build the eligible product pool and seed `on_hand_qty` at creation, again at Submit-for-Review to refresh `on_hand_qty` — but never writes to it. |
| `SPC_XMOD_003` | **→ [master-data/location](/en/inventory/master-data/location)**: the list screen's default filter (hide locations flagged `physical_count_type = no`, unless "Include Not Count" is checked) reuses the same per-location admin flag [physical-count](/en/inventory/physical-count) uses for its own period-end gate — but spot check itself is not a period-end gate (see § 5.1). |
| `SPC_XMOD_004` | **→ [physical-count](/en/inventory/physical-count)**: spot check is the narrower, ad-hoc partial-count cousin — a completely separate document tree (no shared tables, no shared enums) that happens to reuse the same product-pool union logic and the same generic notes-dialog UI component. |

## 7. References

- **Primary:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts` (create/update/delete/reset/saveItems/reviewItems/getReview/submit), `spot-check.logic.ts` (sampling strategies).
- **Secondary (planning-stage, partially confirmed):** `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-10-spot-check.md`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/` (`sc-component.tsx`, `sc-form.tsx`, `sc-entry-component.tsx`, `sc-review-component.tsx`); `constant/permissions.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — no spot-check spec currently exists; manual test-case catalog at `docs/test-cases/760-spot-check.md`.
- Related rule sets: [physical-count/02-business-rules](/en/inventory/physical-count/02-business-rules) (`PHC_*` — the full-count counterpart, which at least creates unposted stock-in/out rows at submit), [inventory-adjustment/02-business-rules](/en/inventory/inventory-adjustment/02-business-rules) (`ADJ_*` — where a confirmed variance must be manually corrected), [inventory/02-business-rules](/en/inventory/inventory/02-business-rules) (ledger semantics — not reached by this module at all).
