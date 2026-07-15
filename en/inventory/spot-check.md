---
title: Spot Check
description: Ad-hoc partial count of a sampled set of products at one location — no automatic posting anywhere.
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Spot Check

> **At a Glance**
> **Module purpose:** ad-hoc, narrow-scope count of a random / high-value / manually-picked sample of products at one location, entered and reviewed by a single generic role &nbsp;·&nbsp; **Audience:** any user holding the `inventory_management.spot_check` permission — no distinct persona split was found in code &nbsp;·&nbsp; **Key entities/tables:** `tb_spot_check`, `tb_spot_check_detail`, two comment tables (`tb_spot_check_comment` is schema-only — no frontend hook reads or writes it; `tb_spot_check_detail_comment` is the one actually used, for per-line notes/photos), `enum_spot_check_status` (4 values), `enum_spot_check_method` (3 values) &nbsp;·&nbsp; **Sub-pages:** 10

![Spot Check screen](/screenshots/spot-check/index.png)

![Spot Check review screen](/screenshots/spot-check/review.png)

## 1. Overview

A **spot check** is an ad-hoc, narrow-scope count of a sampled set of products at one location — the lighter-weight cousin of [physical-count](/en/inventory/physical-count), which counts every item at a location under a fiscal period. The real implementation (`../carmen-inventory-frontend-react/routes/inventory-management/spot-check/`) is a single continuous flow with no persona hand-off: a user opens the location list (`spot-check`), starts a new check for a not-yet-checked location (`spot-check/location/:location_id`) by picking a location-locked location, a sampling `method` (random / high-value / manual), and a sample size, enters `actual_qty` per sampled product on the entry screen (`spot-check/:id`), reviews the computed variance (`spot-check/:id/review`), and confirms the final submit. Every action is gated by one CRUD permission key, `inventory_management.spot_check` (`constant/permissions.ts`); no separate approver, auditor, or configuration role, route, or permission was found anywhere in the frontend, backend, or Bruno collection for this module.

**The headline finding for this module: nothing about a spot check ever posts anywhere.** The final submit (`spot-check.service.ts` `submit()`) does exactly two things — sets `doc_status = completed` and stamps `end_date` — and its own doc-comment says so explicitly: *"Does not create stock-in/stock-out — any follow-up adjustments are user-driven."* A repo-wide search of the spot-check frontend and backend for `stock_in`, `stock_out`, `executeAdjustment`, `journal`, `ledger`, `threshold`, `tolerance`, and `recount` returned zero hits. This is a materially different — and simpler — mechanism than [physical-count](/en/inventory/physical-count)'s own rollup (which at least creates raw, unposted `tb_stock_in`/`tb_stock_out` rows): a spot check records a variance and stops there. If a variance needs correcting in the ledger, a user must separately go create an ordinary [inventory-adjustment](/en/inventory/inventory-adjustment) Stock In/Out document — there is no automatic link, reason code, or even a shared description string connecting the two.

**A second, previously-undocumented finding: the module's own create/edit form (`sc-form.tsx`) has dead view/edit/delete code paths.** `ScForm` is rendered from exactly one place in the app, `spot-check-by-location-content.tsx`, and always without a `spotCheck` entity — so it is always in "add" mode. The component's `isView`/`isEdit` branches, its Edit/Delete buttons, and the `useUpdateSpotCheck`/`useDeleteSpotCheck` hooks they call are therefore unreachable through any real navigation path; `spot-check/:id` (the only other route that could plausibly open an existing document) always renders the entry/counting screen (`ScEntryComponent`), never `ScForm`. A backend `update()`/`delete()` pair exists and would work if called directly (e.g. from Bruno), but no button in the shipped UI reaches them.

## 2. Business Context

In hospitality operations, spot checks provide **quick, low-friction verification** of high-risk items — premium spirits, prime cuts, branded amenities, controlled goods — without the operational overhead of a full physical count. Because a spot check samples a handful of products at one location rather than every product everywhere, it can be launched and finished inside a single shift.

The real value of the feature, as implemented, is narrower than a "loss-prevention program" framing would suggest: it is a **counting and variance-recording tool**, not a posting or approval workflow. A user samples products, counts them, and sees a matches/variances/overages/shortages summary. Whatever happens next — investigating a shortage, raising a formal inventory adjustment, escalating a suspected theft — is a manual, out-of-band process this module does not orchestrate or track.

## 3. Key Concepts

- **Sampling `method`**: how the in-scope product list is chosen at creation. Three values on `enum_spot_check_method`: `random` (Fisher-Yates shuffle over every product assigned to or stocked at the location, first `size` items kept), `high_value` (ranks the same pool by the highest `cost_per_unit` seen in a cost-layer receipt during the tenant's currently open-or-locked fiscal period, optionally excluding anything under a `minimum_cost` floor), and `manual` (the user picks specific products directly via a two-column transfer picker). `high_value` requires at least one `tb_period` with `status ∈ {open, locked}` to exist — if none does, creation fails with `SPOT_CHECK_NO_ACTIVE_PERIOD` ("No active period found").
- **Eligible product pool**: the same union logic [physical-count](/en/inventory/physical-count) uses — every product formally assigned to the location via `tb_product_location`, plus any product with a non-zero net quantity in `tb_inventory_transaction_detail` at that location, so "phantom stock" items are always sample-eligible even if not formally assigned.
- **`on_hand_qty` is snapshotted at creation** (unlike physical-count, where it starts at `0`): `create()` seeds each detail row's `on_hand_qty` from the pool's live stock figure at the moment the sample is generated. It is then **overwritten with a fresh live figure** the moment the user clicks **Submit for Review** (`reviewItems()` recomputes `on_hand_qty` for every line from the current ledger balance, with no date cut-off) — so the number actually compared against on the review screen is the balance at review time, not at creation time, if any other movement happened at that location in between.
- **No completeness check on the server.** The entry screen's footer only shows **Submit for Review** once every line has a locally-entered value (`uncountedCount === 0`) — but this is a client-side UI gate only. Neither `reviewItems()` nor the final `submit()` rejects an incomplete document; a spot check with several lines still at their seeded `actual_qty = 0` can be reviewed and submitted to `completed` without any block. There is also no tolerance percentage, absolute-quantity threshold, or recount mechanism anywhere in the frontend or backend for this module.
- **Reset = void, not restart.** The **Reset** button, shown only on the location list's "Resume" section for a location with a `pending`/`in_progress` spot check, calls `POST /spot-checks/:id/reset`, which sets `doc_status = void` unconditionally (rejecting only if already `void` or `completed`) and does **not** touch any `tb_spot_check_detail` row — despite the Bruno collection's doc comment describing it as "clears all recorded actual quantities and resets... to draft state." Once voided, the location drops back into the "Not Started" bucket (`GET /spot-check/current` only returns `pending`/`in_progress` documents as a location's `latest_spot_check`), so "starting over" after a Reset means creating a brand-new spot check, not resuming the voided one.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Spot-check operator (any user holding `inventory_management.spot_check`) | The single, undifferentiated role for this module: starts a check from the location list, picks a sampling method and scope, counts the sampled products, submits for review, and confirms the final submit. |

No distinct Inventory Controller, Counter, Approver/Finance, Auditor, or Sysadmin permission key, route, or workflow stage was found for this module — the persona split documented in earlier drafts of this wiki module does not exist in the current implementation. The frontend's own manual test-case catalog (`../carmen-inventory-frontend-e2e/docs/test-cases/760-spot-check.md`) defaults every scenario to a single generic "Store Manager" precondition, consistent with this. The sub-pages in § 7 below retain an Inventory Controller / Counter / Audit-Config split as a page-organisation device only (the same real screen's actions viewed from two angles); `03-user-flow-audit-config.md` and `04-test-scenarios-audit-config.md` are correction pages for the confirmed-absent third group.

## 5. Related Modules

**Cross-module flow:**
- [inventory](/en/inventory/inventory) — a spot check compares its sample against this ledger's balance, but never writes to it directly
- [inventory-adjustment](/en/inventory/inventory-adjustment) — the intended (but not automated) destination for correcting a confirmed variance; no linkage of any kind exists between the two modules' documents
- [physical-count](/en/inventory/physical-count) — the full-count counterpart; a separate document tree, not a parent or child of it

**Master configuration:**
- [master-data/unit](/en/inventory/master-data/unit) — unit of measure for each spot-check line (`inventory_unit_id`)
- [master-data/location](/en/inventory/master-data/location) — the location being sampled, and the source of the `physical_count_type` flag that (by default) filters which locations appear on the spot-check list screen

## 6. Reference Sources

- Concepts: no `carmen/docs` source folder exists for this module; a planning-stage document exists in the E2E repo (`docs/persona-doc/System Process/tx-10-spot-check.md`) whose core "variance posting is pending, not yet implemented" claim matches the live code, but whose status-lifecycle detail (`draft`/`on-hold`/`cancelled`) does not — see [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) § 5.1
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/` (`sc-component.tsx`, `sc-form.tsx`, `sc-entry-component.tsx`, `sc-review-component.tsx`)
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/` (`spot-check.service.ts`, `spot-check.logic.ts`)
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/spot-check/`
- E2E tests: `../carmen-inventory-frontend-e2e/` — no Playwright spec exists for this module (`ls tests/ | grep -i 'spot\|check'`); a manual test-case catalog exists at `docs/test-cases/760-spot-check.md` (32 cases, authored from the live component — the closest thing to an executable spec this module has, though two of its scenarios describe a view/edit/delete screen this app's routing does not actually reach, see [spot-check/04-test-scenarios](/en/inventory/spot-check/04-test-scenarios) § 5)

## 7. Pages in This Module

- [spot-check/01-data-model](/en/inventory/spot-check/01-data-model) — entities, fields, relationships, enums (`tb_spot_check`, `tb_spot_check_detail` plus two comment tables; two enums `enum_spot_check_status` / `enum_spot_check_method`).
- [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) — validation, calculation, authorization, posting, cross-module rules (`SPC_VAL_*` / `SPC_CALC_*` / `SPC_AUTH_*` / `SPC_POST_*` / `SPC_XMOD_*`).
- [spot-check/03-user-flow](/en/inventory/spot-check/03-user-flow) — document lifecycle overview + persona index.
  - [spot-check/03-user-flow-inventory-controller](/en/inventory/spot-check/03-user-flow-inventory-controller) — the list + create screens.
  - [spot-check/03-user-flow-counter](/en/inventory/spot-check/03-user-flow-counter) — the entry + review screens.
  - [spot-check/03-user-flow-audit-config](/en/inventory/spot-check/03-user-flow-audit-config) — correction page: no Approver/Auditor/Sysadmin surface exists.
- [spot-check/04-test-scenarios](/en/inventory/spot-check/04-test-scenarios) — test scenarios overview + end-to-end scenarios + the manual test-case catalog mapping.
  - [spot-check/04-test-scenarios-inventory-controller](/en/inventory/spot-check/04-test-scenarios-inventory-controller) — list/create-screen scenarios.
  - [spot-check/04-test-scenarios-counter](/en/inventory/spot-check/04-test-scenarios-counter) — entry/review-screen scenarios.
  - [spot-check/04-test-scenarios-audit-config](/en/inventory/spot-check/04-test-scenarios-audit-config) — correction page (mirrors the user-flow correction page).

> **Status:** re-synced against the live frontend (`sc-component.tsx`, `sc-form.tsx`, `sc-entry-component.tsx`, `sc-review-component.tsx`), backend (`spot-check.service.ts`, `spot-check.logic.ts`), Prisma schema, and Bruno collection. The previous draft of this module described an entirely fabricated three-persona workflow (Inventory Controller / Counter / Auditor+Sysadmin) with recount escalation, variance-tolerance thresholds, and an automatic rollup into `tb_stock_in`/`tb_stock_out` with GL posting — none of it exists in code; every persona, rule, and mermaid diagram across all 10 sub-pages has been rewritten against the real single-flow, single-permission implementation. No E2E Playwright spec exists yet for this module; a manual test-case catalog (`docs/test-cases/760-spot-check.md`) is the closest available executable-style reference, and a planning-stage document (`docs/persona-doc/System Process/tx-10-spot-check.md`) correctly anticipated the "no variance posting" finding but not the exact status lifecycle — see [spot-check/02-business-rules](/en/inventory/spot-check/02-business-rules) § 5.1 for the point-by-point comparison.
