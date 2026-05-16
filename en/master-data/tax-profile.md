---
title: Tax Profile
description: Named tax rate definitions referenced by vendors, products, and every priced document line.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, tax-profile, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Tax Profile

## 1. Purpose

A tax profile is a named definition pairing a label (e.g. `VAT 7%`, `Zero-rated`, `Service Charge`) with a decimal `tax_rate`. Tax profiles are referenced as FK from vendors, product master data, and most priced document lines (PR, PO, GRN, pricelist, credit note). The decoupling matters because tax rates change over time and many properties operate under multiple regimes simultaneously (VAT vs. exempt vs. zero-rated).

Document-line tax computation reads three things: the chosen tax profile, the document's tax mode (`none` / `included` / `add` via `enum_tax_type`), and the line's base amount. The tax profile contributes the *rate*; the tax mode decides how the rate is applied.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_tax_profile`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `VAT 7%`). |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Rate as a decimal (default `0`). `0.07` for 7%. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `taxprofile_name_deletedat_u`. Index on `name`. Wide reverse relations into PR / PO / GRN / pricelist / vendor / product / credit-note / extra-cost-detail.

## 3. Usage / Cross-References

- [[master-data/vendor]] — vendors hold a default tax profile snapshotted at link time.
- [[product]] — product master data references a default tax profile per item.
- [[purchase-request]] — PR detail lines snapshot tax-profile id and rate.
- [[purchase-order]] — PO detail snapshots tax-profile id and rate; default seeded from vendor or product.
- [[good-receive-note]] — GRN detail items snapshot tax-profile id and rate from PO/manual.
- [[vendor-pricelist]] — pricelist details carry tax-profile reference.

## 4. Configuration UI

Managed by **Product Admin** (or **Sysadmin** in some deployments) under the Master Data area. Simple list + edit dialog with name, rate, and active flag.

## 5. Business Rules

- **Uniqueness.** `name` is unique among non-deleted rows (DB-enforced).
- **Deletion guards.** A tax profile referenced by any document or master record cannot be hard-deleted. Inactivate instead so historical lookups continue to resolve the name.
- **Validation.** `tax_rate` must be `>= 0`. Storage uses decimal form — `0.07` for 7%; UI should validate and convert.
- **Lifecycle.** Inactive profiles are hidden from new-document pickers but stay readable on historical documents.
- **Snapshot semantics.** Every document line snapshots the rate at posting time; editing `tax_rate` here does **not** retro-edit existing documents.
- **Rate-change discipline.** When a regulator changes the headline rate, create a new tax profile (e.g. `VAT 9%`) and migrate vendors/products forward — do not edit the old profile's rate.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_tax_profile` (lines ~1395-1429), `enum_tax_type` (lines ~96-100) — note that `enum_tax_type` lives on each document line, not on this entity.
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/tax-profile/`.
- **Cross-module:** see Section 3.
