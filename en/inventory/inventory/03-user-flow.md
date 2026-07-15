---
title: Inventory — User Flow
description: Movement lifecycle and persona-specific flow files for inventory.
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow

> **At a Glance**
> **Module:** [inventory](/en/inventory/inventory) &nbsp;·&nbsp; **Personas:** Store Keeper (ledger verification) &nbsp;·&nbsp; Inventory Controller (period-end close) &nbsp;·&nbsp; Finance + Audit / Config (correction pages — no such surfaces exist)
> **Workflow lifecycle:** Movement-driven — each `tb_inventory_transaction` is written already-posted by its source module (no draft → committed on the movement). Per-period lifecycle on `tb_period.status`: `open` → `closed` via the Close action here (`locked` is set elsewhere). Corrections are new transactions via new source documents; rows are never edited.

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `inventory` module. Inventory is unusual relative to its sibling document modules — there is no workflow document on which a draft → saved → committed lifecycle plays out. The module's UI surface is exactly two screens: the read-only **Transaction Log** (`/inventory-management/transaction`) and **Period End** (`/inventory-management/period-end` + `/review`). Every ledger row is written by an upstream source module at its posting event — GRN **save**, SR approve-at-final-stage, inventory-adjustment completion, credit-note completion — and the period close itself writes `close`/`open` rows onto the same ledger.

Section 2 describes the two state machines (movement-level, degenerate; period-level, the substantive one). Section 3 indexes the persona files: two describe real flows over the two screens; two are correction pages for personas whose previously-documented surfaces were confirmed absent from the product.

## 2. Movement and Period Lifecycle

### 2.1 Movement-level transitions

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | post from source document | `posted` | The source module's posting event (GRN save, SR final-stage approve, inventory-adjustment Submit, credit-note completion, period close) | Source document reaches its posting state; outbound consumption passes the balance check (`Insufficient stock…`, except credit-note paths which book `diff_amount`); `at_period`/`period_id` stamped from the **current open period** regardless of document date. |
| `posted` | (no further action) | `posted` | — | Terminal and immutable. No reversal endpoint, no edit endpoint; `deleted_at` is never set by current code. A correction is a **new** transaction posted by a new source document (credit note, stock-in/stock-out). |

### 2.2 Period-level transitions

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | period created | `open` | `ensureNextPeriod` during the previous close, or the period admin screen ([system-config/period](/en/inventory/system-config/period)) | One period per YYMM (`@@unique([fiscal_year, fiscal_month, deleted_at])`). |
| `open` | accept movements | `open` | All transactional roles (via source modules) | Every new movement stamps into this period — including "backdated" ones (re-dated, not rejected). |
| `open` (or `locked`) | **Close period** on `/period-end/review` | `closed` | Any user with `inventory_management.period_end.execute` | All blocking-document gates clear (PR/PO/SR not `in_progress`-mid-workflow; GRN in `{draft, committed, voided}`; CN in `{draft, completed, cancelled, voided}`; all required locations counted). Runs atomically under a `FOR UPDATE` lock with re-validation; writes lot carry-over (`CLOSE-…`/`OPEN-…`) and — average-method tenants only — `tb_period_snapshot` rows; auto-provisions the next `open` period; marks `tb_physical_count_period` rows completed. |
| `closed` | (no transition in this module) | — | — | No reopen endpoint exists here. |
| any | lock / unlock | `locked` / — | The period service behind [system-config/period](/en/inventory/system-config/period) | Out of this module's scope; note `findCurrent` treats `locked` as a current period, so a locked period is displayable and closable here. |

## 3. Persona Index

- [Store Keeper](/en/inventory/inventory/03-user-flow-store-keeper) — verifies postings on the read-only Transaction Log; authors nothing in this module (adjustments live in [inventory-adjustment](/en/inventory/inventory-adjustment), counts in [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check)).
- [Inventory Controller](/en/inventory/inventory/03-user-flow-inventory-controller) — works the period-end review checklist to green and runs the close (`inventory_management.period_end.execute`).
- [Finance](/en/inventory/inventory/03-user-flow-finance) — **correction page**: no Finance role, GL reconciliation, or period-lock flow exists.
- [Audit / Config](/en/inventory/inventory/03-user-flow-audit-config) — **correction page**: no inventory audit workspace or configuration console exists; real configuration lives in master-data / system-config / access-control.

## 4. Cross-Persona Handoffs

| From | Trigger | To | System state at handoff |
| ---- | ------- | -- | ----------------------- |
| Source-module operators (GRN receiver, SR approver, adjuster) | Posting event fires | Store Keeper (verification) | Ledger rows written; `parent_document_no` resolvable on the Transaction Log. |
| Inventory Controller | Blocking-document card incomplete on the review screen | Source-module owners | Documents listed in the per-module dialog; period stays `open` until resolved. |
| Inventory Controller | Physical-count row incomplete | Counters | Deep-link to `/inventory-management/physical-count/{id}/entry`. |
| Inventory Controller | **Close period** succeeds | Everyone | `tb_period.status = closed`; next period `open`; new movements stamp into it automatically. |

## 5. References

- Sibling: [01-data-model](/en/inventory/inventory/01-data-model) — canonical enums and the divergence catalogue (incl. the no-GL and BU-level-costing-method corrections this page relies on).
- Sibling: [02-business-rules](/en/inventory/inventory/02-business-rules) — `INV_VAL_005`/`INV_VAL_008` (balance and period stamping), `INV_POST_009`/`INV_POST_010` (close/open), `INV_AUTH_008` (`period_end.execute`).
- Sibling: [transaction](/en/inventory/inventory/transaction) and [period-end](/en/inventory/inventory/period-end) — the two screens the personas above traverse.
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/` (`transaction/`, `period-end/`); routes registered in `routes/router.tsx`.
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/` (`inventory-transaction/`, `period-end/`).
- carmen/docs: `../carmen/docs/Inventory/inventory-management-prd.md`, `../carmen/docs/inventory-management/period-end-process.md` — concept docs; where they conflict with the implementation described here, the implementation wins.
