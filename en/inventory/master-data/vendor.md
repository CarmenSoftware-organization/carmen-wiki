---
title: Vendor
description: Suppliers and their addresses, contacts, and business-type taxonomy — the counterparty on every procurement document.
published: true
date: 2026-05-19T23:55:00.000Z
tags: master-data, vendor, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Vendor

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Tables:** `tb_vendor`, `tb_vendor_address`, `tb_vendor_contact`, `tb_vendor_business_type` &nbsp;·&nbsp; **Used by:** PR, PO, GRN, pricelist, RFQ &nbsp;·&nbsp; The supplier record — defaults tax profile, credit term, and currency onto procurement documents.

![Vendor screen](/screenshots/master-data/vendor.png)

## 1. What & Who

**Vendors** are external counterparties the property buys from. The vendor record is the join point between procurement (PR → PO → GRN), the pricelist workflow (RFQ → pricelist → comparison), and accounting (tax profile, credit terms, payment). Four tables make up the entity: **core** `tb_vendor` (identity + tax linkage), **multiple addresses** in `tb_vendor_address`, **multiple contacts** in `tb_vendor_contact`, and a **taxonomy** of business types in `tb_vendor_business_type`.

The vendor record snapshots the **tax profile** at the vendor level so documents get sensible defaults that lines can still override. **Maintained by** Product Admin; **read by** every procurement and pricelist flow.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a vendor | Master Data → Vendor → **New** | Required: `code`, `name`; pick `tax_profile_id` and business types |
| Add address | Vendor detail → Addresses tab | At most one of each `address_type` per vendor |
| Add contact | Vendor detail → Contacts tab | One contact per vendor may be `is_primary = true` |
| Maintain business types | Master Data → Vendor Business Type | Separate list screen; references stored as JSON `[{id, name}]` on the vendor |
| Deactivate | Toggle `is_active` | Hidden from new pickers; historical docs unchanged |
| Change tax profile | Edit dialog | Snapshots new `tax_rate`; does NOT retro-edit historical documents |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Code/name already in use" | Duplicate `(code, name)` on a non-deleted row | Pick different identifiers |
| "Address type already exists for this vendor" | Second address of same `address_type` attempted | Edit the existing one instead |
| "Cannot delete — referenced by documents" | FK references from PR/PO/GRN/pricelist | Inactivate instead |
| "Vendor has no active contact" warning | All contacts inactive or deleted | Add or reactivate at least one contact |
| "Cannot have two primary contacts" | Two rows with `is_primary = true` | Toggle off the old primary first |

## 4. Edge Cases

- **Tax-profile change** does not retro-edit existing documents; the snapshot on each line stays as posted.
- **Business-type rename** — `tb_vendor.business_type` JSON stores `{id, name}` array; vendors keep the old name until a maintenance job refreshes them.
- **Primary contact invariant** is app-enforced, not DB.
- **Address types** — `contact_address`, `mailing_address`, `register_address`; at most one of each per vendor.
- **Addresses/contacts soft-delete independently** but each vendor should retain at least one active contact.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_vendor`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short vendor code. |
| `name` | `String @db.VarChar` | No | Display name. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `business_type` | `Json? @db.JsonB` | Yes | Array of `{id, name}` refs to `tb_vendor_business_type` (default `[]`). |
| `tax_profile_id` | `String? @db.Uuid` | Yes | Default tax profile for documents. |
| `tax_profile_name` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Snapshotted rate at link time (default `0`). |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, name, deleted_at])` map `vendor_code_name_u`. Indexes on `code`, `name`, `(code, name)`. FK to `tb_tax_profile` `onDelete: NoAction`.

### 5.2 `tb_vendor_address`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `vendor_id` | `String? @db.Uuid` | Yes | FK to `tb_vendor`. |
| `address_type` | `enum_vendor_address_type?` | Yes | `contact_address`, `mailing_address`, or `register_address`. |
| `address_line1` | `String? @db.VarChar` | Yes | Street / house / soi. |
| `address_line2` | `String? @db.VarChar` | Yes | Building / floor. |
| `sub_district` | `String? @db.VarChar` | Yes | Tambon / khwaeng. |
| `district` | `String? @db.VarChar` | Yes | Amphoe / khet. |
| `city` | `String? @db.VarChar` | Yes | For non-TH. |
| `province` | `String? @db.VarChar` | Yes | Province / state. |
| `postal_code` | `String? @db.VarChar` | Yes | ZIP / postcode. |
| `country` | `String? @db.VarChar` | Yes | Country. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `description`, `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([vendor_id, address_type, deleted_at])` — at most one of each address type per vendor. Indexes on `(vendor_id, address_type)` and `vendor_id`.

`enum_vendor_address_type`: `contact_address`, `mailing_address`, `register_address`.

### 5.3 `tb_vendor_contact`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `vendor_id` | `String? @db.Uuid` | Yes | FK to `tb_vendor`. |
| `name` | `String @db.VarChar` | No | Contact person name. |
| `email` | `String? @db.VarChar` | Yes | Email. |
| `phone` | `String? @db.VarChar` | Yes | Phone. |
| `is_primary` | `Boolean?` | Yes | Primary contact (default `false`). |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `description`, `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([vendor_id, name, deleted_at])`. Indexes on `(vendor_id, name)` and `vendor_id`.

### 5.4 `tb_vendor_business_type`

Flat lookup — `id`, `name`, `description`, `note`, `is_active`, standard metadata, audit columns. App-enforced unique `name` among non-deleted rows.

## 6. Business Rules

- **Uniqueness.** `(code, name)` unique among non-deleted vendors. At most one of each `address_type` per vendor. Contact `name` unique within a vendor.
- **Deletion guards.** Open PR/PO/GRN/pricelist references block hard-delete — inactivate.
- **Validation.** `code` and `name` required. `tax_rate` snapshots `tb_tax_profile` at link time.
- **Lifecycle.** `is_active = false` hides from new pickers; existing documents keep working. Active vendor without active contacts should warn in UI.
- **Primary contact invariant.** At most one `is_primary = true` per vendor (app invariant).
- **Tax-profile change propagation.** Does not retro-edit documents; snapshots stay as posted.
- **Business-type rename** requires a maintenance job to refresh JSON snapshots on vendors.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) — PR detail may suggest a preferred vendor.
- [purchase-order](/en/inventory/purchase-order) — PO header binds a single vendor; FX, tax, credit terms default from here.
- [good-receive-note](/en/inventory/good-receive-note) — GRN inherits PO vendor.
- [vendor-pricelist](/en/inventory/vendor-pricelist) — pricelists and RFQ rounds scoped per vendor.
- [master-data/tax-profile](/en/inventory/master-data/tax-profile) — vendor default tax profile.
- [master-data/credit-term](/en/inventory/master-data/credit-term) — vendor default credit term flows to PO header.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_vendor` (lines ~3249-3296), `tb_vendor_address` (lines ~3332-3365), `tb_vendor_contact` (lines ~3367-3396), `tb_vendor_business_type` (lines ~4853-…), `enum_vendor_address_type` (lines ~259-263).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/vendor-management/vendor/`.
