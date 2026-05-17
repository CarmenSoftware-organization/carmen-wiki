---
title: Exchange Rate
description: Dated history of currency-to-base-currency conversion rates — every transactional document snapshots the rate effective on its document date.
published: true
date: 2026-05-17T07:28:28.000Z
tags: master-data, exchange-rate, currency, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Exchange Rate

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_exchange_rate` &nbsp;·&nbsp; **Used by:** PR / PO / GRN / pricelist / costing &nbsp;·&nbsp; **Feed:** daily (manual or cron)

![Exchange Rate screen](/assets/screenshots/master-data/exchange-rate.png)

## 1. What & Who

Exchange Rate stores the **dated history** of currency-to-base-currency rates. Every priced document (PR / PO / GRN / pricelist) **snapshots the rate** effective on its date at submit and **freezes it** for the life of the document — re-approval does NOT re-fetch.

**Maintained by** Product Admin (typically each morning). **Read by** the costing engine for FX revaluation on credit notes (`COST_CALC_005`) and period close.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Enter today's rate for all enabled currencies | Configuration → Exchange Rate → **Bulk daily** | Idempotent on `(currency, date)` — safe to re-run |
| Enter one rate (single currency) | Configuration → Exchange Rate → **Manual single-row** | Pick currency, pick date, enter rate |
| Check which rate a document used | Open the PO/GRN, look at the line FX field | Document freezes rate at submit time |
| Refresh FX on a draft PO | PO line → **Refresh FX** action | PR and GRN do NOT have this action |
| Fix a wrong rate on a *posted* document | Cannot edit in-place | Raise a manual journal voucher per finance policy |
| Enable automated daily feed | Configure `micro-cronjobs` FX job | Idempotent — safe to re-run; updates the "current" cache too |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Exchange rate must be > 0" | Rate entered as zero or negative | Re-enter a positive number |
| "Effective date too far in future" | `at_date` > today + 1 day (configurable horizon) | Use today's date for the daily entry |
| "Currency must be active" | `tb_currency.is_active = false` for the chosen code | Activate first under [[master-data/currency]] |
| Duplicate rate for the same date | A row already exists for `(currency, at_date)` | Edit the existing row; do NOT insert a second |
| "Period is closed" | `at_date` falls inside a closed [[system-config/period]] | Cannot back-fill into a closed period; raise a JV |
| Document shows **"rate not in history"** warning | No `tb_exchange_rate` row at or before document date for that currency | Add a backdated rate, then re-open the document so resolution can run |

## 4. Edge Cases

- **Backdated entry is allowed but does NOT retroactively change documents** that already snapshotted a different value. To correct a posted document, use a manual journal voucher.
- **Currency inactivation does NOT delete its rate history** — historical documents continue to render correctly.
- **Precision:** rate stored at `Decimal(15, 5)`; document line totals round to 2 decimals (money) per the rounding convention.
- **"Current" cache vs. history.** `tb_currency.exchange_rate` is a *cache* of the most-recent `tb_exchange_rate` row. New documents resolve via the dated history first; only if no row matches the date does the cache act as fallback (with a warning on the document).

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_exchange_rate`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `at_date` | `DateTime? @db.Timestamptz(6)` | Yes | Effective date (defaults `now()`). Applies *from* this date until superseded. |
| `currency_id` | `String? @db.Uuid` | Yes | FK to `tb_currency`. |
| `currency_code` | `String? @db.VarChar(3)` | Yes | Denormalised display copy (`USD`, `THB`). |
| `currency_name` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `exchange_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Rate against BU default currency (default `1`). |
| `note` | `String? @db.VarChar` | Yes | Free text (e.g. "Daily fix from BoT"). |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([at_date, currency_id, deleted_at])` map `exchangerate_at_date_currency_u` — one rate per `(currency, date)`. Index on `(at_date, currency_id)`. FK on `currency_id` `onDelete: NoAction` so rate history survives a currency soft-delete.

## 6. Business Rules

- **Uniqueness.** One non-deleted row per `(at_date, currency_id)`. Re-entering the same day = update the existing row.
- **Validation.** `exchange_rate > 0`; `at_date <= today + 1 day` (configurable horizon); `currency_id` must reference an active currency.
- **Precision.** Stored at `Decimal(15, 5)`; line totals round to money precision (2 dp) per the rounding convention.
- **Rate resolution.** Engine selects the row with the largest `at_date <= document_date` for the document currency. If no row exists, fall back to `tb_currency.exchange_rate` and flag the document.
- **Snapshot semantics.** Once a document captures a resolved rate, it's frozen. Re-approving / re-routing / re-posting does NOT re-fetch — explicit "Refresh FX" only.
- **Currency inactivation.** Does NOT delete rate history. Soft-deleting a rate row removes it from new resolutions only.
- **Backdated entry.** Allowed; does NOT retroactively update posted documents.
- **Period close.** Closed period rate rows are locked from edit; new inserts with `at_date` inside a closed period are rejected.

## 7. Cross-References

- [[master-data/currency]] — parent. Each rate row scoped to one `tb_currency`.
- [[master-data/business-unit]] — `default_currency_id` is the implicit "to" side of every rate.
- [[purchase-order]], [[good-receive-note]], [[purchase-request]] — documents that snapshot rates.
- [[vendor-pricelist]] — comparison normalised to BU default via the dated rate.
- [[costing]] — `COST_CALC_005` (credit-note FX revaluation) and period close read here.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_exchange_rate` (lines ~744-768).
- **Frontend:** `../carmen-inventory-frontend/app/(root)/config/exchange-rate/`.
- **Cron job:** `../micro-cronjobs/` — daily FX feed.
