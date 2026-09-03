---
title: Currency
description: Per-tenant currency catalogue, ISO reference list, and dated exchange-rate history — drives all FX conversion on POs, GRNs, pricelists, and costing.
published: true
date: 2026-07-15T21:47:09.000Z
tags: master-data, currency, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Currency

> **At a Glance**
> **Owner:** Sysadmin (ISO seed) / Product Admin (tenant catalogue) &nbsp;·&nbsp; **Tables:** `tb_currency_iso`, `tb_currency`, `tb_exchange_rate` &nbsp;·&nbsp; **Used by:** every priced document + costing engine &nbsp;·&nbsp; Tenant-enabled currencies + their "current" rate cache.

![Currency screen](/screenshots/master-data/currency.png)

## 1. What & Who

Currency master data spans **three tables across two schemas**: a **platform ISO reference** (`tb_currency_iso`), a **tenant enabled-currencies catalogue** (`tb_currency`) with a "current" rate cache, and the **tenant dated rate history** (`tb_exchange_rate`). Together they let any priced document be expressed in any currency the tenant has enabled and let the costing engine pick the right rate for the document's date.

Each tenant chooses a subset of ISO currencies to enable. The BU's `default_currency_id` (see [master-data/business-unit](/en/inventory/master-data/business-unit)) points to one of these enabled rows. **Maintained by** Sysadmin (ISO seed) and Product Admin (tenant catalogue); **read by** developers on the FX / costing paths and testers on document FX flows.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Enable a currency for the tenant | Configuration → Master Data → Currency → **New** | Pick `iso_code` from `tb_currency_iso`; sets `is_active = true` |
| Override symbol or name | Edit dialog | Tenant copies in `tb_currency.symbol` / `name` override the ISO row |
| Set BU default currency | [master-data/business-unit](/en/inventory/master-data/business-unit) detail | Must reference an active `tb_currency` row |
| Maintain rates | See [master-data/exchange-rate](/en/inventory/master-data/exchange-rate) | Dated history lives there, not on this entity |
| Deactivate a currency | Toggle `is_active` | Blocked if it is any BU's `default_currency_id` |
| Seed a new ISO code | Platform DB migration | Tenants cannot write `tb_currency_iso` |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Currency already exists" | Duplicate `code` (case-insensitive) among non-deleted rows | Pick a different code or reactivate the existing row |
| Document shows "rate not in history" warning | No `tb_exchange_rate` row at/before document date | Add a backdated rate in [master-data/exchange-rate](/en/inventory/master-data/exchange-rate) |
| **Unconfirmed** — no cross-schema, value, or BU-default guard found | `CurrencyCreateSchema`/`CurrencyUpdateSchema` (`currency.dto.ts`) only type-check `code`/`exchange_rate`; `currency.service.ts`'s `create()`/`update()`/`delete()` do not check `tb_currency_iso` for a matching ISO code, do not require `exchange_rate > 0`, do not check whether the currency is any BU's `default_currency_id` before inactivating, and do not check for document/pricelist references before soft-deleting | A prior version of this page asserted "ISO code not found", "exchange rate must be > 0", "cannot inactivate — set as BU default", and "cannot delete — referenced by documents/pricelists" as enforced server errors — none were found this pass; treat all four as **not enforced** until re-verified |

## 4. Edge Cases

- **"Current" cache vs. history.** `tb_currency.exchange_rate` is a *cache* of the most-recent `tb_exchange_rate`. New documents resolve via dated history first; cache is fallback (with a warning).
- **Inactivation does not delete history** — historical documents continue to render against their snapshotted rate.
- **BU default invariant — unconfirmed.** No code was found that blocks inactivating a currency that is a BU's `default_currency_id`; treat this as a design intent, not a live guard.
- **Per-tenant override** — `tb_currency.name` / `symbol` override the ISO copies for display.
- **No ISO cross-check.** `tb_currency.code` is a free-typed string on create — nothing requires it to match a `tb_currency_iso.iso_code` row.
- **Decimal places.** `tb_currency.decimal_places` controls rendering only — storage is `Decimal(15, 5)` for rates, money rounds to 2 dp.

---

## 5. Data Model (Dev)

Mixed source: tenant + platform.

### 5.1 `tb_currency_iso` (platform)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `iso_code` | `String @db.VarChar` | No | ISO 4217 code (`USD`, `THB`, `EUR`). |
| `name` | `String @db.VarChar(255)` | No | Long name (default `Unknown`). |
| `symbol` | `String @db.VarChar(10)` | No | Symbol (default `Unknown`). |

**Constraints:** `@@unique([iso_code])` map `currency_iso_iso_code_u`. Reference-only — no audit columns.

### 5.2 `tb_currency` (tenant)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar(3)` | No | ISO code mirrored from `tb_currency_iso`. |
| `name` | `String @db.VarChar(100)` | No | Tenant-overridable display name. |
| `symbol` | `String? @db.VarChar(5)` | Yes | Override symbol. |
| `description` | `String?` | Yes | Free text (default `""`). |
| `decimal_places` | `Int?` | Yes | Default `2`. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `exchange_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Current rate cache vs. BU default (default `1`). |
| `exchange_rate_at` | `DateTime? @db.Timestamptz(6)` | Yes | Cache timestamp. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** primary key on `id`; uniqueness on `code` enforced at application layer. Reverse relations to GRN, JV, PO, PR, pricelist, credit note, and exchange-rate history.

### 5.3 `tb_exchange_rate` (tenant)

See [master-data/exchange-rate](/en/inventory/master-data/exchange-rate) for the full schema and resolution rules. `@@unique([at_date, currency_id, deleted_at])`; FK to `tb_currency` `onDelete: NoAction`.

## 6. Business Rules

- **Uniqueness.** `tb_currency.code` unique (case-insensitive) among non-deleted rows, app-checked in `create()`/`update()`; `tb_currency_iso.iso_code` DB-unique. One `tb_exchange_rate` per `(at_date, currency_id)`.
- **Deletion guards — unconfirmed.** No reference check was found in `delete()`; soft-delete succeeds unconditionally even with document/pricelist references.
- **Validation — unconfirmed.** No positive-value check on `exchange_rate` and no cross-check against `tb_currency_iso` were found in `currency.service.ts` or its Zod DTOs.
- **Lifecycle.** Inactive currencies hidden from new-document pickers; historical documents render off the snapshot.
- **Rate resolution.** Engine selects largest `at_date <= document_date` for `currency_id`; falls back to `tb_currency.exchange_rate` cache and flags the document.
- **BU default invariant — unconfirmed.** No code was found that blocks inactivating a currency that is any BU's `default_currency_id`.

## 7. Cross-References

- [master-data/exchange-rate](/en/inventory/master-data/exchange-rate) — dated rate history; resolution rules.
- [master-data/business-unit](/en/inventory/master-data/business-unit) — `default_currency_id` points here.
- [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note), [purchase-request](/en/inventory/purchase-request) — documents carry currency + snapshot rate.
- [vendor-pricelist](/en/inventory/vendor-pricelist) — comparison normalises to BU default via the dated rate.
- [costing](/en/inventory/costing) — costing resolves receipt-date rate to BU currency.

## 8. References

- **Prisma (tenant):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_currency` (lines ~553-596), `tb_exchange_rate` (lines ~760-785).
- **Prisma (platform):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_currency_iso` (lines ~279-287).
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/currency/`.
