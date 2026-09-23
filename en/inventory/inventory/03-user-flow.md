---
title: Inventory — User Flow
description: Movement lifecycle and persona-specific flow files for inventory.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: inventory, user-flow, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# Inventory — User Flow

> **At a Glance**
> **Module:** [inventory](/en/inventory/inventory) &nbsp;·&nbsp; **Personas:** Store Keeper (ledger verification) &nbsp;·&nbsp; Inventory Controller (period-end close) &nbsp;·&nbsp; Finance + Audit / Config (correction pages — no such surfaces exist)
> **Workflow lifecycle:** Movement-driven — each `tb_inventory_transaction` is written already-posted by its source module (no draft → committed on the movement). Per-period lifecycle on `tb_inventory_period.status`: `open` → (**Start Period Close** opens the counting round on `tb_physical_count_period`) → `closed` via **Close Period** here (`locked` is set elsewhere). Corrections are new transactions via new source documents; rows are never edited.

## 1. Overview

This page is the **overview entry point** for the user-flow set of the `inventory` module. Inventory is unusual relative to its sibling document modules — there is no workflow document on which a draft → saved → committed lifecycle plays out. The module's UI surface is exactly two screens: the read-only **Transaction Log** (`/inventory-management/transaction`) and **Period End** (`/inventory-management/period-end` + `/review`). Every ledger row is written by an upstream source module at its posting event — GRN **save** (average-method BU) or **commit** (FIFO BU), SR approve-at-final-stage, stock-in / stock-out **commit**, credit-note completion — and the period close itself writes `close`/`open` rows onto the same ledger.

Section 2 describes the two state machines (movement-level, degenerate; period-level, the substantive one). Section 3 indexes the persona files: two describe real flows over the two screens; two are correction pages for personas whose previously-documented surfaces were confirmed absent from the product.

## 2. Movement and Period Lifecycle

### 2.1 Movement-level transitions

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | post from source document | `posted` | The source module's posting event (GRN save on average BUs / commit on FIFO BUs, SR final-stage approve, stock-in / stock-out **Commit**, credit-note completion, period close) | Source document reaches its posting state; its document date falls inside an open period (SI: any open/locked period; SO: the current period; GRN: any open period — otherwise the create/commit is rejected, see `INV_VAL_008`); outbound consumption passes the balance check (`Insufficient stock…`, except credit-note paths which book `diff_amount`); `at_period`/`period_id` stamped from the **document date's** period. |
| `posted` | (no further action) | `posted` | — | Terminal and immutable. No reversal endpoint, no edit endpoint; `deleted_at` is never set by current code. A correction is a **new** transaction posted by a new source document (credit note, stock-in/stock-out). |

### 2.2 Period-level transitions

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | period created | `open` | `ensureNextPeriod` during the previous close, or the period admin screen ([system-config/period](/en/inventory/system-config/period)) | One period per YYMM (`@@unique([fiscal_year, fiscal_month, deleted_at])`). |
| `open` | accept movements | `open` | All transactional roles (via source modules) | Movements whose document date falls inside this period post into it; a document dated inside a `closed` period is rejected at create/commit (SI/SO/GRN date guards). |
| `open` | **Start Period Close** on `/period-end` | `open` (period) + `counting` (its `tb_physical_count_period`) | Any user with `inventory_management.period_end.execute` | No GRN dated in the period outside `{committed, voided}`, no SI/SO outside `{completed, cancelled, voided}`, no numbered SR at `draft`/`in_progress` (`listStartCountingBlockers`); PR/PO never block. Idempotent while the round is `counting`; 409 once it is `completed`. This is the only path that lets a physical count be opened. |
| `open` (or `locked`) | **Close Period** on `/period-end/review` | `closed` | Any user with `inventory_management.period_end.execute` | All close gates clear (numbered SR not `in_progress`-mid-workflow; GRN in `{draft, committed, voided}`; CN in `{draft, completed, cancelled, voided}`; SI/SO not `in_progress`; all required locations counted — PR/PO no longer gate). Runs atomically under a `FOR UPDATE` lock with re-validation; sweeps only lots whose period `end_at ≤` this period's; writes lot carry-over (new `{location_code}{YYMM}{seq4}` lots) and — average-method tenants only — `tb_inventory_period_snapshot` rows; auto-provisions the next `open` period; marks `tb_physical_count_period` rows completed. |
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
| Inventory Controller | **Start Period Close** blocked ("Finish these documents first" dialog) | GRN / SI / SO / SR owners | The 422 payload lists every blocking document with a link; the counting round stays `draft`. |
| Inventory Controller | Physical-count location card not completed | Counters | Clicking the card opens the location's count (creating it if none exists, `openPhysicalCount`); cards are disabled until the round is `counting`. |
| Inventory Controller | **Close Period** succeeds | Everyone | `tb_inventory_period.status = closed`; next period `open`; documents dated in the new period post into it, documents still dated in the closed one are rejected. |

## 5. References

- Sibling: [01-data-model](/en/inventory/inventory/01-data-model) — canonical enums and the divergence catalogue (incl. the no-GL and BU-level-costing-method corrections this page relies on).
- Sibling: [02-business-rules](/en/inventory/inventory/02-business-rules) — `INV_VAL_005`/`INV_VAL_008` (balance and period stamping), `INV_POST_009`/`INV_POST_010` (close/open), `INV_AUTH_008` (`period_end.execute`).
- Sibling: [transaction](/en/inventory/inventory/transaction) and [period-end](/en/inventory/inventory/period-end) — the two screens the personas above traverse.
- Frontend: `../carmen-inventory-frontend-react/routes/inventory-management/` (`transaction/`, `period-end/`); routes registered in `routes/router.tsx`.
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/` (`inventory-transaction/`, `period-end/`).
- carmen/docs: `../carmen/docs/Inventory/inventory-management-prd.md`, `../carmen/docs/inventory-management/period-end-process.md` — concept docs; where they conflict with the implementation described here, the implementation wins.
