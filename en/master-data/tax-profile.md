---
title: Tax Profile
description: Named tax rate definitions referenced by vendors, products, and every priced document line.
published: true
date: 2026-05-17T07:28:28.000Z
tags: master-data, tax-profile, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Tax Profile

> **At a Glance**
> **Owner:** Product Admin (or Sysadmin) &nbsp;·&nbsp; **Table:** `tb_tax_profile` &nbsp;·&nbsp; **Used by:** vendor, product, PR / PO / GRN / pricelist / credit note &nbsp;·&nbsp; Named rate (`VAT 7%`, `Zero-rated`) — line tax mode decides how it's applied.

![Tax Profile screen](/assets/screenshots/master-data/tax-profile.png)

## 1. What & Who

A **tax profile** is a named definition pairing a label (e.g. `VAT 7%`, `Zero-rated`, `Service Charge`) with a decimal `tax_rate`. Tax profiles are referenced from **vendors, product master data, and most priced document lines** (PR, PO, GRN, pricelist, credit note). The decoupling matters: rates change over time and many properties operate under multiple regimes simultaneously.

Document-line tax computation reads three things: the **chosen tax profile**, the document's **tax mode** (`none` / `included` / `add` via `enum_tax_type`), and the **line's base amount**. The tax profile contributes the *rate*; the mode decides how it's applied. **Maintained by** Product Admin; **read by** every priced-document flow.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a profile | Configuration → Master Data → Tax Profile → **New** | Required: `name`, `tax_rate` (decimal — `0.07` = 7%) |
| Deactivate | Toggle `is_active` | Hidden from new-document pickers; historical lines unchanged |
| New regulator rate | **Create a new profile** | E.g. `VAT 9%` — do NOT edit the old profile's rate |
| Migrate vendors/products | Bulk update reference fields | After creating the new profile, migrate references forward |
| Check rate used on a line | Open the document line | Rate is snapshotted, not resolved from this table |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already in use" | Duplicate `name` on a non-deleted row | Pick a different name or reactivate the existing row |
| "Rate must be >= 0" | Negative `tax_rate` | Enter zero or positive decimal |
| "Cannot delete — referenced by documents/vendors/products" | FK references exist | Inactivate instead |
| Line shows old rate after profile edit | Line snapshotted the original rate | Expected — snapshot is the contract |

## 4. Edge Cases

- **Snapshot semantics.** Every document line snapshots the rate at posting time; editing `tax_rate` here does NOT retro-edit posted lines.
- **Rate-change discipline.** When the regulator changes the headline rate, **create a new profile** (e.g. `VAT 9%`) and migrate vendors/products forward — do not edit the old profile.
- **Decimal form** — `0.07` represents 7%; UI must validate and convert.
- **Inactivation** keeps historical lookups resolvable.
- **`enum_tax_type`** lives on each document line, not on the profile — see schema note in References.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_tax_profile`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `VAT 7%`). |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Rate as decimal (default `0`). `0.07` for 7%. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `taxprofile_name_deletedat_u`. Index on `name`. Wide reverse relations into PR / PO / GRN / pricelist / vendor / product / credit-note / extra-cost-detail.

## 6. Business Rules

- **Uniqueness.** `name` unique among non-deleted rows (DB-enforced).
- **Deletion guards.** Any document/master reference blocks hard-delete — inactivate.
- **Validation.** `tax_rate >= 0`; storage is decimal form (`0.07` = 7%).
- **Lifecycle.** Inactive profiles hidden from new pickers; readable on historical lines.
- **Snapshot semantics.** Document lines snapshot the rate; editing here does not retro-edit historical documents.
- **Rate-change discipline.** Always create a new profile when the headline rate changes.

## 7. Cross-References

- [[master-data/vendor]] — vendors hold a default tax profile snapshotted at link time.
- [[product]] — product master references a default tax profile per item.
- [[purchase-request]] — PR detail lines snapshot profile id + rate.
- [[purchase-order]] — PO detail snapshots; default from vendor/product.
- [[good-receive-note]] — GRN detail snapshots from PO/manual.
- [[vendor-pricelist]] — pricelist details carry tax-profile reference.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_tax_profile` (lines ~1395-1429), `enum_tax_type` (lines ~96-100) — note that `enum_tax_type` lives on each document line, not on this entity.
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/tax-profile/`.
