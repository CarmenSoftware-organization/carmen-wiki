---
title: Exchange Rate
description: Dated history of currency-to-base-currency conversion rates — every transactional document snapshots the rate effective on its document date.
published: true
date: 2026-07-15T21:47:09.000Z
tags: master-data, exchange-rate, currency, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Exchange Rate

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_exchange_rate` &nbsp;·&nbsp; **Used by:** PR / PO / GRN / pricelist / costing &nbsp;·&nbsp; **Feed:** manual entry, or bulk sync from an external FX API (currently broken — see Edge Cases). No cron job exists.

![Exchange Rate screen](/screenshots/master-data/exchange-rate.png)

## 1. What & Who

Exchange Rate stores the **dated history** of currency-to-base-currency rates. Every priced document (PR / PO / GRN / pricelist) **snapshots the rate** effective on its date at submit and **freezes it** for the life of the document — re-approval does NOT re-fetch.

**Maintained by** Product Admin (typically each morning, via manual entry — the bulk external-sync button is confirmed broken in the current build, see Edge Cases). **Read by** the costing engine for FX revaluation on credit notes (`COST_CALC_005`) and period close.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Enter one rate (single currency) | Configuration → Exchange Rate → **Add Manual** | Pick currency, pick date, enter rate; backend rejects only an exact duplicate `(currency, at_date)` row |
| Sync all enabled currencies from an external rate feed | Configuration → Exchange Rate → **Update** | Fetches live rates from an external FX API (`/api/exchange-rate?base=<code>`), diffs them against each currency's cached rate, and bulk-submits the changed ones dated today via a real `createBulk` endpoint — **but see Edge Cases: this fetch is confirmed broken in the current build** |
| Check which rate a document used | Open the PR/PO/GRN, look at the line FX field | Document freezes rate at submit time |
| Change the rate on a draft PR/PO/GRN | Document header → currency picker | Re-selecting the currency re-populates the field from `tb_currency.exchange_rate`; the field is also directly editable. There is no distinct "Refresh FX" action anywhere in the codebase — PR, PO, and GRN all behave identically here |
| Fix a wrong rate on a *posted* document | Cannot edit in-place | Raise a manual journal voucher per finance policy |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Must be at least 0" | Rate entered as negative in the Add Manual / Edit dialog (client-side Zod `min(0)`) | Re-enter zero or a positive number |
| Duplicate rate for the same date | A row already exists for `(currency, at_date)` — `create()` rejects with "Exchange rate already exists"; `createBulk()` silently skips it instead | Edit the existing row; do NOT insert a second |
| Document shows **"rate not in history"** warning | No `tb_exchange_rate` row at or before document date for that currency | Add a backdated rate, then re-open the document so resolution can run |
| **Unconfirmed** — the backend has no validation beyond "currency exists" | `ExchangeRateCreateSchema`/`ExchangeRateUpdateSchema` (`exchange-rate.dto.ts`) only check `currency_id` resolves to a row — no positive-rate check, no future-date horizon, no active-currency check, and no period-closed check were found anywhere in `exchange-rate.service.ts` | A prior version of this page asserted "rate must be > 0", "date too far in future", "currency must be active", and "period is closed" as server-enforced errors — none were found in the backend read this pass; treat all four as **frontend-only or absent**, not server guarantees, until re-confirmed |

## 4. Edge Cases

- **Backdated entry is allowed but does NOT retroactively change documents** that already snapshotted a different value. To correct a posted document, use a manual journal voucher.
- **Currency inactivation does NOT delete its rate history** — historical documents continue to render correctly.
- **Precision:** rate stored at `Decimal(15, 5)`; document line totals round to 2 decimals (money) per the rounding convention.
- **"Current" cache vs. history.** `tb_currency.exchange_rate` is a *cache* of the most-recent `tb_exchange_rate` row. New documents resolve via the dated history first; only if no row matches the date does the cache act as fallback (with a warning on the document).
- **Confirmed half-built feature — the "Update" bulk-sync button.** `ExchangeRateComponent`'s `useExternalExchangeRates` hook fetches `GET /api/exchange-rate?base=<currency-code>`, a route that was a Next.js API endpoint in a previous stack. A repo-wide search of the current NestJS gateway (`carmen-turborepo-backend-v2/apps/backend-gateway`) finds no matching route — only the CRUD `api/config/:bu_code/exchange-rates` controller exists. The hook's own code comments confirm this directly: `// TODO(phase-config): /api/exchange-rate was a Next route — move to backend or client-side fetch when the config module migrates`, and a second comment notes that on static hosting the SPA fallback returns `index.html` with a `200` status, so the endpoint degrades to an "Exchange rate endpoint is not available" error rather than crashing. The **Add Manual** single-row path is unaffected — it posts straight to the real `POST /exchange-rates` endpoint.
- **No cron-driven feed exists.** A repo-wide search of `../micro-cronjobs` for `exchange`/`fx`/`currency` returned zero hits. There is no scheduled job that refreshes rates; the only two ways a rate row is created are the (currently broken) external-sync button and the manual single-row dialog.

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
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`); the update DTO requires it and rejects a mismatch. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([at_date, currency_id, deleted_at])` map `exchangerate_at_date_currency_u` — one rate per `(currency, date)`. Index on `(at_date, currency_id)`. FK on `currency_id` `onDelete: NoAction` so rate history survives a currency soft-delete.

## 6. Business Rules

- **Uniqueness.** One non-deleted row per `(at_date, currency_id)`, DB-enforced. `create()` rejects an exact duplicate with "Exchange rate already exists" rather than updating it; `createBulk()` silently skips duplicates instead of erroring. Editing an existing row requires opening it explicitly (a separate `update()` call carrying its `doc_version`).
- **Validation (confirmed).** `ExchangeRateCreateSchema`/`ExchangeRateUpdateSchema` (`exchange-rate.dto.ts`) only require `currency_id` to resolve to an existing `tb_currency` row (`validateCurrencyIdExists` — no `is_active` filter, so even an inactive or soft-deleted currency passes). There is no server-side check that `exchange_rate` is positive, no future-date horizon, and no period-closed check anywhere in `exchange-rate.service.ts`. The frontend's Add Manual / Edit dialogs independently enforce `exchange_rate >= 0` (Zod `min(0)`, so `0` itself is accepted) and non-empty `currency_id`/`at_date` on the manual form — client-side only.
- **Optimistic lock.** Update carries a required `doc_version`; a stale value is rejected. Create does not need one.
- **Precision.** Stored at `Decimal(15, 5)`; line totals round to money precision (2 dp) per the rounding convention.
- **Rate resolution.** Engine selects the row with the largest `at_date <= document_date` for the document currency. If no row exists, fall back to `tb_currency.exchange_rate` and flag the document.
- **Snapshot semantics.** Once a document captures a resolved rate, it's frozen. Re-approving / re-routing / re-posting does NOT re-fetch automatically; the field stays user-editable, and re-selecting the currency on the document header re-populates it from the current `tb_currency.exchange_rate` cache — there is no dedicated "Refresh FX" action anywhere in the codebase.
- **Currency inactivation.** Does NOT delete rate history. Soft-deleting a rate row removes it from new resolutions only.
- **Backdated entry.** Allowed; does NOT retroactively update posted documents.

## 7. Cross-References

- [master-data/currency](/en/inventory/master-data/currency) — parent. Each rate row scoped to one `tb_currency`.
- [master-data/business-unit](/en/inventory/master-data/business-unit) — `default_currency_id` is the implicit "to" side of every rate.
- [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [purchase-request](/en/inventory/purchase-request) — documents that snapshot rates.
- [vendor-pricelist](/en/inventory/vendor-pricelist) — comparison normalised to BU default via the dated rate.
- [costing](/en/inventory/costing) — `COST_CALC_005` (credit-note FX revaluation) and period close read here.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_exchange_rate` (lines ~760-785).
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/exchange-rate/` — `use-exchange-rate.ts`'s `useExternalExchangeRates` hook is the confirmed-broken external-sync call.
- **Backend:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_exchange-rates/` (CRUD, incl. `createBulk`) and `apps/micro-business/src/master/exchange-rate/exchange-rate.service.ts`.
- **Cron job:** none found. `../micro-cronjobs/` has zero hits for `exchange`/`fx`/`currency`; there is no scheduled FX feed.
