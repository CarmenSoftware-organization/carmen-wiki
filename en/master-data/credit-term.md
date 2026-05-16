---
title: Credit Term
description: Vendor payment terms (NET 30, COD, etc.) selected on purchase orders to drive due-date and accounts-payable schedules.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, credit-term, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Credit Term

## 1. Purpose

Credit terms encode the supplier-payment agreement as a named record with a day count. `NET 30` means payment is due 30 days after invoice date; `COD` (`value = 0`) means payment due on delivery. POs reference a credit term so the downstream accounts-payable schedule has a concrete due-date target.

The entity is intentionally minimal — just name, day-count value, and an active flag. Anything more sophisticated (early-payment discounts, multi-tier schedules) is layered on top in application logic or a future companion table.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_credit_term`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `NET 30`, `COD`). |
| `value` | `Int? @db.Integer` | Yes | Days after invoice date until due (default `0`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `is_active` | `Boolean?` | Yes | Active flag. |
| `info`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `credit_term_name_u`. Index on `name`. Reverse relation to `tb_purchase_order`.

## 3. Usage / Cross-References

- [[purchase-order]] — PO header carries `credit_term_id`; the due date is `po_date + value` days.
- [[master-data/vendor]] — many properties pre-assign a default credit term per vendor in application logic; the value is then defaulted onto new POs for that vendor.

## 4. Configuration UI

Managed by **Product Admin** under the Master Data area. Simple list + edit dialog (name, value, active).

## 5. Business Rules

- **Uniqueness.** `name` is unique among non-deleted rows (DB-enforced).
- **Deletion guards.** A credit term referenced by open POs cannot be deleted; inactivate instead.
- **Validation.** `value` must be `>= 0`. `name` is required.
- **Lifecycle.** Inactive credit terms are hidden from new-PO pickers; historical POs continue to render their assigned term.
- **Snapshot semantics.** PO stores the term id; the day-count is read at lookup time. Renaming a term or changing the `value` changes how *new* POs default but does not retro-edit the saved due date on historical POs (the due date is computed and stored on the PO).

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_term` (lines ~4548-4572).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/credit-term/`.
- **Cross-module:** see Section 3.
