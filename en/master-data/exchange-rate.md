---
title: Exchange Rate
description: Dated history of currency-to-base-currency conversion rates — every transactional document snapshots the rate effective on its document date.
published: true
date: 2026-05-16T16:30:00.000Z
tags: master-data, exchange-rate, currency, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Exchange Rate

## 1. Purpose

The exchange-rate table is the dated companion to [[master-data/currency]]. Where `tb_currency` carries one *current* rate per enabled currency, `tb_exchange_rate` carries the full history — one row per `(currency, effective date)` — so that historical priced documents can resolve to the rate that applied on their document date, not whatever the current rate happens to be.

Two consumers read this table:

1. **Document snapshot at submit/post time.** PR / PO / GRN / pricelist freeze the resolved rate onto the document at submission and never re-fetch. Re-approving a document does not re-read here.
2. **Costing engine for FX revaluation.** On credit-note posting (`COST_CALC_005`) and period-end close, the cost engine looks up the rate effective on the document date to value movements in the BU's base currency.

The table is typically populated daily — either via a scheduled job from an external FX provider, or by Product Admin entering rates manually in the morning.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_exchange_rate`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `at_date` | `DateTime? @db.Timestamptz(6)` | Yes | Effective date (defaults `now()`). The date this rate applies *from* until the next row supersedes it. |
| `currency_id` | `String? @db.Uuid` | Yes | FK to `tb_currency`. |
| `currency_code` | `String? @db.VarChar(3)` | Yes | Denormalised display copy (`USD`, `THB`). |
| `currency_name` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `exchange_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Rate against BU default currency (default `1`). Five-decimal precision per CLAUDE.md rounding convention. |
| `note` | `String? @db.VarChar` | Yes | Free text (e.g. "Daily fix from BoT"). |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([at_date, currency_id, deleted_at])` map `exchangerate_at_date_currency_u` — one rate per currency per effective date. Index on `(at_date, currency_id)`. FK on `currency_id` `onDelete: NoAction` so historical rate rows survive a currency soft-delete.

## 3. Usage / Cross-References

- [[master-data/currency]] — parent. Each rate row is scoped to a single `tb_currency`.
- [[master-data/business-unit]] — `default_currency_id` is the implicit "to" side of every rate (rates are quoted *against* BU default).
- [[purchase-order]] — PO line snapshots the rate effective on PO date for FX-converted totals.
- [[good-receive-note]] — GRN copies the PO currency and snapshots the rate at *GRN date* for landed-cost calculation. The PO and GRN may carry different rates if days have elapsed.
- [[purchase-request]] — PR carries an estimated rate; the binding rate is resolved later on PO.
- [[vendor-pricelist]] — pricelist quotes are stored in the vendor's currency; comparison and ranking normalise to BU default via the dated rate.
- [[costing]] — `COST_CALC_005` (credit-note FX revaluation) and period close both read here.

## 4. Configuration UI

Managed by **Product Admin** under Configuration → Exchange Rate (or via the dated history dialog from the Currency screen). Three entry modes:

- **Manual single-row** — pick currency + date, enter rate.
- **Bulk daily** — enter today's rate for every enabled currency in one dialog (typical morning workflow).
- **Automated feed** — `micro-cronjobs` can be configured to pull from an external FX provider and `INSERT` a row per enabled currency each morning. The job is idempotent on `(at_date, currency_id)`.

The "current" rate on `tb_currency.exchange_rate` is a *cache* of the most-recent `tb_exchange_rate` row; it is updated by the same insert.

## 5. Business Rules

- **Uniqueness.** One non-deleted row per `(at_date, currency_id)`. Re-entering a rate for the same day requires updating the existing row, not inserting a new one.
- **Validation.** `exchange_rate > 0`. `at_date` must not be in the future beyond a configurable horizon (default: today + 1 day). `currency_id` must reference an active currency.
- **Precision.** Stored at `Decimal(15, 5)`. Document-side calculations use this precision then round line totals to money precision per CLAUDE.md rounding convention.
- **Rate resolution.** For any priced document with `document_date = D` and `currency_id = C`, the engine selects the row with the largest `at_date <= D` for currency `C`. If no row exists, it falls back to `tb_currency.exchange_rate` (the "current" cache) and flags the document with a "rate not in history" warning so finance can review.
- **Snapshot semantics.** Once a document captures a resolved rate, that rate is frozen on the document row. Re-approving, re-routing, or re-posting does NOT re-fetch — the only path to refresh a rate is an explicit user action (e.g. "Refresh FX" on the PO line, where supported).
- **Currency inactivation.** Inactivating a currency does NOT delete its rate history; rates remain readable so historical documents continue to render. Soft-deleting a rate row removes it from new resolutions only.
- **Backdated entry.** Inserting a rate for `at_date` in the past is allowed but does NOT retroactively update documents that already snapshotted a different value. Use a manual journal voucher if a correction is needed on a posted document.
- **Period close.** A closed period's rate rows are locked from edit (system-enforced via `tb_period.status = closed`). Inserting a new row with `at_date` inside a closed period is rejected.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_exchange_rate` (lines ~744-768).
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/(protected)/config/exchange-rate/`.
- **Cron job:** `../micro-cronjobs/` — daily FX feed if enabled.
- **Cross-module:** see Section 3.
