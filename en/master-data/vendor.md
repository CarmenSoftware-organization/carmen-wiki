---
title: Vendor
description: Suppliers and their addresses, contacts, and business-type taxonomy — the counterparty on every procurement document.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, vendor, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Vendor

## 1. Purpose

Vendors are the external counterparties the property buys from. The vendor record is the join point between procurement (PR → PO → GRN), the pricelist workflow (RFQ, vendor pricelist, comparison), and accounting (tax profile, credit terms, payment). Four tables make up the entity: the core `tb_vendor` with identity and tax linkage, multiple addresses per vendor in `tb_vendor_address`, multiple contacts in `tb_vendor_contact`, and a taxonomy of business types in `tb_vendor_business_type`.

The vendor record snapshots tax-profile linkage at the vendor level (`tax_profile_id`, `tax_rate`) so that documents quoting that vendor get sensible defaults that can still be overridden per-line.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_vendor`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Short vendor code. |
| `name` | `String @db.VarChar` | No | Display name. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `business_type` | `Json? @db.JsonB` | Yes | Array of `{id, name}` references to `tb_vendor_business_type` (default `[]`). |
| `tax_profile_id` | `String? @db.Uuid` | Yes | Default tax profile applied to documents quoting this vendor. |
| `tax_profile_name` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `tax_rate` | `Decimal? @db.Decimal(15, 5)` | Yes | Snapshotted rate at link time (default `0`). |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, name, deleted_at])` map `vendor_code_name_u`. Indexes on `code`, `name`, `(code, name)`. FK to `tb_tax_profile` `onDelete: NoAction`.

### 2.2 `tb_vendor_address`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `vendor_id` | `String? @db.Uuid` | Yes | FK to `tb_vendor`. |
| `address_type` | `enum_vendor_address_type?` | Yes | `contact_address`, `mailing_address`, or `register_address`. |
| `address_line1` | `String? @db.VarChar` | Yes | Street / house no / soi. |
| `address_line2` | `String? @db.VarChar` | Yes | Additional (building / floor). |
| `sub_district` | `String? @db.VarChar` | Yes | Tambon / khwaeng. |
| `district` | `String? @db.VarChar` | Yes | Amphoe / khet. |
| `city` | `String? @db.VarChar` | Yes | City (for non-TH addresses). |
| `province` | `String? @db.VarChar` | Yes | Province / state. |
| `postal_code` | `String? @db.VarChar` | Yes | ZIP / postcode. |
| `country` | `String? @db.VarChar` | Yes | Country. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `description`, `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([vendor_id, address_type, deleted_at])` map `vendoraddress_vendor_address_type_deletedat_u` — at most one of each address type per vendor. Indexes on `(vendor_id, address_type)` and `vendor_id`.

`enum_vendor_address_type` values: `contact_address`, `mailing_address`, `register_address`.

### 2.3 `tb_vendor_contact`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `vendor_id` | `String? @db.Uuid` | Yes | FK to `tb_vendor`. |
| `name` | `String @db.VarChar` | No | Contact person name. |
| `email` | `String? @db.VarChar` | Yes | Email address. |
| `phone` | `String? @db.VarChar` | Yes | Phone number. |
| `is_primary` | `Boolean?` | Yes | Primary contact flag (default `false`). |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `description`, `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([vendor_id, name, deleted_at])` map `vendorcontact_vendor_name_deletedat_u`. Indexes on `(vendor_id, name)` and `vendor_id`.

### 2.4 `tb_vendor_business_type`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Business-type label (e.g. `Food`, `Beverage`, `Equipment`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `info`, `dimension`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** unique on `name` among non-deleted rows (application-enforced; see schema for the exact `@@unique` spelling).

## 3. Usage / Cross-References

- [[purchase-request]] — PR detail lines can suggest a preferred vendor.
- [[purchase-order]] — PO header binds a single vendor; FX, tax, and credit terms default from this record.
- [[good-receive-note]] — GRN inherits the PO vendor.
- [[vendor-pricelist]] — pricelists and RFQ rounds are scoped per vendor.
- [[master-data/tax-profile]] — vendor's default tax profile.
- [[master-data/credit-term]] — vendor's default credit term flows to PO header.

## 4. Configuration UI

Managed by **Product Admin** under the Master Data area. The vendor screen is a tabbed master-detail UI: General (code, name, tax profile, business types), Addresses (CRUD against `tb_vendor_address`), Contacts (CRUD against `tb_vendor_contact`), and Activity / Comments. Business-type taxonomy is maintained in a separate list screen.

## 5. Business Rules

- **Uniqueness.** `(code, name)` is unique among non-deleted vendors. At most one of each `address_type` per vendor. Contact `name` is unique within a vendor.
- **Deletion guards.** A vendor referenced by any open document (PR, PO, GRN, pricelist) cannot be hard-deleted. Inactivate instead. Addresses and contacts may be soft-deleted independently, but each vendor should retain at least one active contact.
- **Validation.** `code` and `name` are required. `tax_rate` snapshots the current rate from `tb_tax_profile` at link time; document lines may further override.
- **Lifecycle.** `is_active = false` hides the vendor from new-document pickers; existing documents keep working. A vendor with `is_active = true` but no active address or contact should raise a warning in the UI.
- **Primary contact invariant.** At most one `tb_vendor_contact` per vendor should carry `is_primary = true` (application invariant).
- **Tax-profile change propagation.** Changing the vendor's `tax_profile_id` does not retro-edit existing documents; the snapshot on each document line stays as posted.
- **Business-type referential integrity.** `tb_vendor.business_type` JSON stores an array of `{id, name}` — when a `tb_vendor_business_type` row is renamed, vendors retain the old name until refreshed by a maintenance job.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_vendor` (lines ~3249-3296), `tb_vendor_address` (lines ~3332-3365), `tb_vendor_contact` (lines ~3367-3396), `tb_vendor_business_type` (lines ~4853-…), `enum_vendor_address_type` (lines ~259-263).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/vendor-management/vendor/`.
- **Cross-module:** see Section 3.
