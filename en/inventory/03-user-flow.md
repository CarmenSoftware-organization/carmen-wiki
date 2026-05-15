---
title: Inventory — User Flow
description: Movement lifecycle and persona-specific flow files for inventory.
published: true
date: 2026-05-15T12:00:00.000Z
tags: inventory, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `inventory` module. Inventory is unusual relative to its sibling document modules — there is no single workflow document on which a draft → saved → committed lifecycle plays out. Instead, the module is **movement-driven**: each `tb_inventory_transaction` row is **itself the posting event**, written by an upstream source module (GRN commit, SR approve, count complete, credit-note approve, manual stock-in / stock-out approve). The "lifecycle" the personas walk is therefore the **lifecycle of a stock balance at `(location_id, product_id, lot_no)`**: it opens with a period-open rollforward (or the first inbound when the location is new), accumulates inbound / outbound movements through the period, is reconciled against a physical or spot count, gets adjusted for variance, and is closed into a `tb_period_snapshot` row at period end. Each persona owns a different slice of that lifecycle.

Section 2 below describes the **movement-and-period-state machine** — the canonical set of legal transitions on the movement and period levels, independent of who acts. Each per-persona file (linked from Section 3) describes that persona's *path through* this state space — their entry point, the actions available to them, the decision branches they face, and the handoff that ends their involvement. Section 4 then summarises the cross-persona handoffs that stitch the individual paths together (Store Keeper → Inventory Controller for variance review, Inventory Controller → Finance for valuation sign-off, Finance Manager → Audit at period lock). Read this overview first to anchor the lifecycle, then drill into the persona file that matches your role.

## 2. Movement and Period Lifecycle

Two distinct state machines coexist in this module: the **per-movement** lifecycle (degenerate — each transaction is written posted, optionally compensated, optionally hidden via `deleted_at`) and the **per-period** lifecycle on `tb_period.status` (the substantive lifecycle: `open` → `closed` → `locked`). The transitions below cover both.

### 2.1 Movement-level transitions

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | post from source document | `posted` | Source-document role (GRN-Inventory-Manager-on-commit, SR-Approver-on-issue, Counter-on-count-complete, Finance-on-credit-note-approve, Store-Keeper-or-Controller-on-stock-in/out-approve) | Source document is in its terminal posting state; `INV_VAL_001`–`INV_VAL_013` all pass; period containing the transaction date is `open` per `INV_VAL_008`. Writes `tb_inventory_transaction` header + `tb_inventory_transaction_detail` + (for inventory-type / consignment locations) `tb_inventory_transaction_cost_layer`. |
| `posted` | compensating reversal | `posted` (new row) | Store Keeper, Inventory Controller, Finance | Tenant policy permits reversal at the user's role / threshold. A **new** `tb_inventory_transaction` is written with negated `qty`; the original row is **not** edited (the inventory transaction is immutable on write per `INV_POST_012`). |
| `posted` | soft-delete original (after compensating reversal) | `posted` with `deleted_at` set | Store Keeper, Inventory Controller, Finance | Compensating transaction must have been written first per `INV_VAL_013`; tenant policy is "hide reversed transactions". The original row's `deleted_at` is set; the row remains in the database for audit but is filtered out of normal views. |
| `posted` | (no further direct action) | `posted` | — | Terminal state. Audit can read; reporting can read; period close will sweep into `tb_period_snapshot`. |

### 2.2 Period-level transitions

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create period (system / scheduled) | `open` | System Administrator | Period definition (`YYMM`, `fiscal_year`, `fiscal_month`, `start_at`, `end_at`) populated; no overlap with existing period rows. |
| `open` | accept movements | `open` | All transactional roles (via source modules) | The period accepts any inbound / outbound movement whose transaction date falls within `[start_at, end_at]`. Backdated postings before the period's `start_at` route to the prior period (rejected if that period is `closed` / `locked` per `INV_VAL_008`). |
| `open` | period close (run period-end job) | `closed` | Finance, with Inventory Controller's variance-review sign-off as a pre-condition | Pre-period-end checklist complete: all `draft` / `saved` source documents either committed or voided; spot checks complete; full physical count if scheduled (`tb_location.physical_count_type = yes`); all count-variance adjustments approved per `INV_AUTH_003`; cost reconciliation reviewed per `INV_AUTH_005`. The job (`INV_POST_009`) writes `tb_period_snapshot` rows and `close_period` cost-layer rows. |
| `closed` | period open (rollforward — chained with close) | `open` (on next period) | System Administrator (scheduled job) | Chained with the close; writes the next period's opening cost-layer rows (`open_period`) and the next period's snapshot opening fields per `INV_CALC_008`. |
| `closed` | re-open period (exceptional) | `open` | Finance Manager (elevated; audit-logged per `INV_AUTH_006`) | Audit-grade justification required ("exceptional adjustment necessary in the closed period"). Re-opens the period for back-posting; subsequent re-close must be performed before the next regular period close. |
| `closed` | lock period | `locked` | Finance Manager | The reconciliation report passes (no variance between inventory sub-ledger and GL); aging report reviewed; Finance Manager signs off per `INV_POST_011`. After lock, no role can re-open or post. |
| `locked` | (no further transitions) | `locked` | — | Terminal. The locked period is immutable; corrections post into the current open period as restatement. |

## 3. Persona Index

Each persona below has a dedicated drill-down file describing their entry point, primary flow, decision branches, and exit point. Slugs match the persona role; clicking the link opens the per-persona view.

- [Store Keeper](./03-user-flow-store-keeper.md) — records day-to-day stock movements at the location level. Issues stock-in / stock-out documents for routine adjustments (found-stock, breakage), runs physical counts on their locations, captures count-variance lines that route upward for approval, and operates the receiving dock for GRN-driven inbound (covered in detail in [[good-receive-note]]'s Receiver flow). Their inventory-module ownership starts when a movement needs to be initiated at the floor level and ends when the document carrying the movement is handed off to the Inventory Controller for above-threshold approval.
- [Inventory Controller](./03-user-flow-inventory-controller.md) — owns **balance accuracy**. Reviews variance from physical / spot counts, approves stock-in / stock-out documents above the Store Keeper threshold, coordinates the count cadence and the spot-check programme, maintains per-product / per-location stock policy (par / min / max / reorder) on `tb_product_location`, and is the second signature on the period-end pre-flight (variance approved before Finance runs the close).
- [Finance](./03-user-flow-finance.md) — owns **valuation and the GL reconciliation**. Reviews the costing feed (FIFO layer integrity, weighted-average drift), reconciles the inventory sub-ledger against the GL Inventory control account, approves cost-impact adjustments above the Inventory Controller threshold, posts the period-end inventory-to-GL reconciliation entry, and (as Finance Manager) runs the period-close → period-lock progression on `tb_period.status`.
- [Audit / Config](./03-user-flow-audit-config.md) — System Administrator (configures `tb_location` including `location_type` and `physical_count_type`, `tb_adjustment_type` reason codes, costing method per product, period definitions, integration endpoints with the source modules, RBAC) and Auditor (read-only review of all inventory transactions, cost-layer ledger, period snapshots, configuration history; runs lot-trace and reconciliation queries during audit and recall workstreams).

## 4. Cross-Persona Handoffs

The table below captures the moments where inventory work moves from one persona's responsibility to another's. Each handoff is anchored to the system state at the point of transfer.

| From persona | Trigger | To persona | System state at handoff |
| ------------ | ------- | ---------- | ----------------------- |
| Store Keeper | Stock-in / stock-out document raised above threshold | Inventory Controller | Source document at `tb_stock_in.doc_status = in_progress` / `tb_stock_out.doc_status = in_progress`; no inventory transaction written yet. |
| Store Keeper | Physical / spot count complete with variance lines | Inventory Controller | Count document at `tb_count_stock.status = completed`; variance lines staged but not yet posted as `tb_stock_in` / `tb_stock_out`. |
| Inventory Controller | Stock-in / stock-out approved (above Controller threshold) | Finance | Source document remains `in_progress`; awaiting Finance approval (typically large-value write-offs, recall write-offs, audit-flagged adjustments). |
| Inventory Controller | Variance-review sign-off for the period | Finance | All count-variance posts complete; period is still `open`; pre-period-end checklist clear. |
| Finance | Inventory sub-ledger reconciled to GL; period-end run | Finance Manager | Period in `open` state, ready to close. Reconciliation report passes (variance ≤ tolerance). |
| Finance Manager | Period close run | Finance, Inventory Controller, Store Keeper | Period at `tb_period.status = closed`; `tb_period_snapshot` rows written; backdated postings rejected per `INV_VAL_008`. Personas re-engage at the new (open) period. |
| Finance Manager | Period lock run | Auditor | Period at `tb_period.status = locked`; immutable; ready for external audit. |
| System Administrator | Configuration change applied (location type, costing method, adjustment-type list, RBAC, integration endpoint) | All personas | No transaction state change; new rules apply prospectively to new movements; in-flight source documents may need re-evaluation per the snapshot rule in `[03-user-flow-audit-config.md](./03-user-flow-audit-config.md)`. |
| Auditor | Lot-recall trace complete | Inventory Controller (write-off coordination) + Finance (financial provisioning) | No transaction state change; recall execution lives on `[[inventory-adjustment]]` and `[[good-receive-note]]` credit-note paths. |

## 5. References

- `../carmen/docs/Inventory/inventory-management-prd.md` — carmen/docs PRD describing inventory-module personas and goals (note: the PRD's `StockMovement` workflow status is **not** canonical — Prisma has no `doc_status` on `tb_inventory_transaction`; this page follows the movement-driven model documented in [[inventory/01-data-model]]).
- `../carmen/docs/Inventory/location-type-and-financial-treatment.md` — carmen/docs reference for the `location_type` posting variants that change the persona flow for direct-cost and consignment locations.
- `../carmen/docs/inventory-management/period-end-process.md` — carmen/docs period-end checklist, the procedural backdrop to Section 2.2 (period-level state machine) and the cross-persona handoffs at period close / lock.
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_inventory_doc_type`, `enum_transaction_type`, `enum_period_status`, `enum_location_type`, `enum_physical_count_type` (the enums used in Section 2's transitions), and the divergences against carmen/docs that shape the no-`doc_status` framing.
- Sibling: [02-business-rules.md](./02-business-rules.md) — posting and authorization rules referenced by each transition row in Section 2 (notably `INV_POST_001`–`INV_POST_012` for the fan-out effects, `INV_AUTH_001`–`INV_AUTH_010` for the role gates, `INV_VAL_008` for the period-lock guard).
- Related modules: [[good-receive-note]] (primary upstream source of inbound; receipts post via `enum_inventory_doc_type = good_received_note`), [[store-requisition]] (primary upstream source of outbound; issues / transfers), [[physical-count]] (variance source for period-end), [[spot-check]] (mid-period variance source), [[inventory-adjustment]] (manual stock-in / stock-out), [[costing]] (downstream consumer of cost-layer data), [[product]] (carries the costing-method configuration).
