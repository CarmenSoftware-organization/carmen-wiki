---
title: Currency
description: Per-tenant currency catalogue, ISO reference list, and dated exchange-rate history — drives all FX conversion on POs, GRNs, pricelists, and costing.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, currency, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Currency

## 1. Purpose

Currency master data covers three tables across two schemas: a platform-level ISO reference (`tb_currency_iso`), a tenant-level enabled-currencies catalogue (`tb_currency`) with its current exchange rate, and a tenant-level dated history (`tb_exchange_rate`) capturing the rate per currency per date. Together they let any priced document be expressed in any currency the tenant has enabled, and let the costing engine pick the right rate for the document's date.

Each tenant chooses a subset of ISO currencies to enable. The BU's `default_currency_id` (see [[master-data/business-unit]]) points to one of these enabled rows.

## 2. Prisma Model(s)

Mixed source: tenant + platform.

### 2.1 `tb_currency_iso` (platform)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `iso_code` | `String @db.VarChar` | No | ISO 4217 code (`USD`, `THB`, `EUR`). |
| `name` | `String @db.VarChar(255)` | No | Long name (default `Unknown`). |
| `symbol` | `String @db.VarChar(10)` | No | Currency symbol (default `Unknown`). |

**Constraints:** `@@unique([iso_code])` map `currency_iso_iso_code_u`. Reference-only — no audit columns; tenants do not write here.

### 2.2 `tb_currency` (tenant)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar(3)` | No | ISO code mirrored from `tb_currency_iso`. |
| `name` | `String @db.VarChar(100)` | No | Tenant-overridable display name. |
| `symbol` | `String? @db.VarChar(5)` | Yes | Override symbol. |
| `description` | `String?` | Yes | Free text (default `""`). |
| `decimal_places` | `Int?` | Yes | Default `2`. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `exchange_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Current rate against BU default currency (default `1`). |
| `exchange_rate_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp the current rate was set. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** primary key on `id`; uniqueness on `code` enforced at application layer. Reverse relations to GRN, JV, PO, PR, pricelist, credit note, and exchange-rate history.

### 2.3 `tb_exchange_rate` (tenant)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `at_date` | `DateTime? @db.Timestamptz(6)` | Yes | Effective date (defaults `now()`). |
| `currency_id` | `String? @db.Uuid` | Yes | FK to `tb_currency`. |
| `currency_code` / `currency_name` | `String? @db.VarChar` | Yes | Denormalised display copies. |
| `exchange_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Rate vs. BU default (default `1`). |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([at_date, currency_id, deleted_at])` map `exchangerate_at_date_currency_u`. Index on `(at_date, currency_id)`. FK to `tb_currency` `onDelete: NoAction`.

## 3. Usage / Cross-References

- [[purchase-order]] — PO header carries currency; PO line uses dated rate from `tb_exchange_rate` for FX conversion.
- [[good-receive-note]] — GRN copies the PO currency and snapshots the rate at GRN date for landed-cost calculation.
- [[vendor-pricelist]] — pricelists are quoted in a specific currency; comparison logic normalises to BU default via `tb_exchange_rate`.
- [[costing]] — costing engine resolves the receipt-date rate to value cost in BU currency.
- [[master-data/business-unit]] — `default_currency_id` points here.

## 4. Configuration UI

**Sysadmin** seeds `tb_currency_iso` at the platform level. **Product Admin** activates currencies for the tenant and maintains the dated exchange-rate history under the Master Data area.

## 5. Business Rules

- **Uniqueness.** `tb_currency.code` is unique among active rows; `tb_currency_iso.iso_code` is DB-unique. One `tb_exchange_rate` row per `(at_date, currency_id)`.
- **Deletion guards.** A currency referenced by any document or pricelist cannot be hard-deleted. Inactivate instead.
- **Validation.** `exchange_rate` must be `> 0`. ISO code must match a row in `tb_currency_iso`.
- **Lifecycle.** Inactive currencies are hidden from new-document pickers; historical documents continue to render against their snapshotted rate.
- **Rate resolution.** For any priced document, the engine selects the largest `at_date <= document_date` for `currency_id`. If none exists, it falls back to `tb_currency.exchange_rate` (the "current" rate) and flags the document.
- **BU default invariant.** A currency that is the BU `default_currency_id` cannot be inactivated.

## 6. References

- **Prisma:**
  - Tenant: `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_currency` (lines ~545-621), `tb_exchange_rate` (lines ~744-768).
  - Platform: `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_currency_iso` (lines ~217-224).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/currency/`.
- **Cross-module:** see Section 3.
