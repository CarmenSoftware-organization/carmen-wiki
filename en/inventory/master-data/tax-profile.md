---
title: Tax Profile
description: Named tax rate definitions referenced by vendors, products, and every priced document line; now also classified VAT or withholding tax (WHT) with an optional GL account and PND form.
published: true
date: 2026-10-27T00:00:00.000Z
tags: master-data, tax-profile, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Tax Profile

> **At a Glance**
> **Owner:** Product Admin (or Sysadmin) &nbsp;·&nbsp; **Table:** `tb_tax_profile` &nbsp;·&nbsp; **Used by:** vendor, product, PR / PO / GRN / pricelist / credit note &nbsp;·&nbsp; Named rate (`VAT 7%`, `Zero-rated`) — line tax mode decides how it's applied.

![Tax Profile screen](/screenshots/master-data/tax-profile.png)

## 1. What & Who

A **tax profile** is a named definition pairing a label (e.g. `VAT 7%`, `Zero-rated`, `Service Charge`) with a decimal `tax_rate`. Tax profiles are referenced from **vendors, product master data, and most priced document lines** (PR, PO, GRN, pricelist, credit note). The decoupling matters: rates change over time and many properties operate under multiple regimes simultaneously.

Since 2026-09-23 a profile also carries an **AP tax classification** (`tax_type` = `vat` \| `wht`, optional `chart_of_accounts_id`, and for WHT a `wht_pnd_form` and `wht_income_type`) used by the AP-invoice work. This is **API-only for now**: the Tax Profile dialog sends none of the four fields, so profiles created through the UI are `vat` with no account.

Document-line tax computation reads three things: the **chosen tax profile**, the document's **tax mode** (`none` / `included` / `add` via `enum_tax_type`), and the **line's base amount**. The tax profile contributes the *rate*; the mode decides how it's applied. **Maintained by** Product Admin; **read by** every priced-document flow.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a profile | Configuration → Master Data → Tax Profile → **New** | Required: `name`, `tax_rate` (decimal — `0.07` = 7%) |
| Classify as VAT / WHT, link a GL account (API) | `tax_type`, `chart_of_accounts_id`, `wht_pnd_form`, `wht_income_type` on `POST/PUT` tax-profiles | `chart_of_accounts_id` must be an active, **postable** [chart-of-accounts](/en/inventory/master-data/chart-of-accounts) row (type not `header` / `summary`). Sending `tax_type = vat` nulls `wht_pnd_form` and `wht_income_type` (`normalizeWhtFields`) |
| Deactivate | Toggle `is_active` | Hidden from new-document pickers; historical lines unchanged |
| New regulator rate | **Create a new profile** | E.g. `VAT 9%` — do NOT edit the old profile's rate |
| Migrate vendors/products | Bulk update reference fields | After creating the new profile, migrate references forward |
| Check rate used on a line | Open the document line | Rate is snapshotted, not resolved from this table |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `409 TAX_PROFILE_NAME_ALREADY_EXISTS` — "Tax profile name already exists" | Duplicate `name` on a non-deleted row (dialog shows it under **Name**) | Pick a different name or reactivate the existing row |
| `422 GL_ACCOUNT_NOT_POSTABLE` — "Account is inactive or is a header/summary account that cannot be posted to" | `chart_of_accounts_id` unknown, deleted, inactive, or of type `header` / `summary` (create and update) | Pick a postable account |
| **Unconfirmed** — no rate or delete guard found | `TaxProfileCreateSchema`/`TaxProfileUpdateSchema` (`tax-profile.dto.ts`) declare `tax_rate` as a plain optional `z.number()` with no minimum, and `tax_profile.service.ts`'s `delete()` is an unconditional soft-delete with no reference check | A prior version of this page asserted "rate must be >= 0" and "cannot delete — referenced by documents/vendors/products" as enforced errors; treat both as **not enforced** until re-verified |
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
| `tax_type` | `enum_tax_profile_tax_type` | No | `vat` (default) \| `wht`. |
| `chart_of_accounts_id` | `String? @db.Uuid` | Yes | FK → `tb_chart_of_accounts` (`onDelete: NoAction`). |
| `wht_pnd_form` | `enum_tax_profile_wht_pnd_form?` | Yes | `pnd_1`, `pnd_2`, `pnd_3`, `pnd_53`, `pnd_54`; meaningful for WHT only. |
| `wht_income_type` | `String? @db.VarChar` | Yes | Free text; WHT only. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `taxprofile_name_deletedat_u`. Index on `name`. Wide reverse relations into PR / PO / GRN / pricelist / vendor / product / credit-note / extra-cost-detail.

## 6. Business Rules

- **Uniqueness.** `name` unique among non-deleted rows (DB-enforced).
- **Deletion guards — unconfirmed.** No reference check was found in `delete()`; soft-delete succeeds unconditionally even with document/vendor/product references.
- **Validation — unconfirmed.** No positive-value check on `tax_rate` was found server-side; storage is decimal form (`0.07` = 7%).
- **Lifecycle.** Inactive profiles hidden from new pickers; readable on historical lines.
- **Snapshot semantics.** Document lines snapshot the rate; editing here does not retro-edit historical documents.
- **Rate-change discipline.** Always create a new profile when the headline rate changes.
- **Classification.** `tax_type`, `chart_of_accounts_id` and the WHT fields are read by the AP-invoice code, not by PR / PO / GRN line tax computation; `tax_type` defaults to `vat`.
- **Default sort.** `GET /tax-profiles` with no `?sort=` returns `name:asc, tax_rate:asc, id:asc` (`tax_profile.service.ts`, `withDefaultSort`, 2026-09-13).

## 7. Cross-References

- [master-data/vendor](/en/inventory/master-data/vendor) — vendors hold a default tax profile snapshotted at link time.
- [product](/en/inventory/product) — product master references a default tax profile per item.
- [purchase-request](/en/inventory/purchase-request) — PR detail lines snapshot profile id + rate.
- [purchase-order](/en/inventory/purchase-order) — PO detail snapshots; default from vendor/product.
- [good-receive-note](/en/inventory/good-receive-note) — GRN detail snapshots from PO/manual.
- [vendor-pricelist](/en/inventory/vendor-pricelist) — pricelist details carry tax-profile reference.

## 8. References

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_tax_profile` (line ~1491), `enum_tax_type` (~96) — note that `enum_tax_type` lives on each document line, not on this entity.
- **Migration / backend (classification):** `20260923060040_accounting_foundation_ap`; `apps/micro-business/src/master/tax_profile/tax_profile.service.ts` (`validateChartOfAccounts`, `normalizeWhtFields`).
- **E2E:** `../carmen-frontend-e2e/tests/042-tax-profile.spec.ts` + `docs/test-cases/gaps/042-tax-profile-gap.md`.
- **Frontend:** `../carmen-frontend/routes/config/tax-profile/`.
