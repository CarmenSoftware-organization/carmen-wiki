---
title: Credit Term
description: Vendor payment terms (NET 30, COD, etc.) selected on purchase orders to drive due-date and accounts-payable schedules.
published: true
date: 2026-05-19T23:55:00.000Z
tags: master-data, credit-term, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Credit Term

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_credit_term` &nbsp;·&nbsp; **Used by:** purchase orders (default per vendor) &nbsp;·&nbsp; Named payment terms — `name` + day-count `value`.

![Credit Term screen](/screenshots/master-data/credit-term.png)

## 1. What & Who

Credit terms encode the supplier-payment agreement as a named record with a day count: `NET 30` means payment due 30 days after invoice date; `COD` (`value = 0`) means payment on delivery. POs reference a credit term so the **accounts-payable schedule** has a concrete due-date target.

The entity is intentionally minimal — `name`, `value` (days), and an `is_active` flag. Anything richer (early-payment discounts, tiered schedules) lives in application logic, not on this record. **Maintained by** Product Admin; **read by** developers and testers on the PO and AP paths.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a new term | Configuration → Master Data → Credit Term → **New** | Required: `name`; `value` defaults `0` (COD) |
| Deactivate a term | Toggle `is_active` | Hidden from new-PO pickers; historical POs keep their term |
| Change day-count | Edit `value` | New POs default to new value; historical POs already have the due date stored |
| Set default per vendor | [master-data/vendor](/en/inventory/master-data/vendor) detail | App-layer; not on this record |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already in use" | Duplicate `name` on a non-deleted row | Pick a different name |
| "Value must be >= 0" | Negative day-count entered | Use `0` for COD or a positive integer |
| "Name required" | Empty `name` | Add a display name (e.g. `NET 30`) |
| "Cannot delete — referenced by open POs" | At least one open PO uses this term | Inactivate instead |

## 4. Edge Cases

- **Renaming or value-changes** affect only **new** POs; the due date is **computed and stored** on the PO at creation.
- **Soft-deleted terms** stay resolvable on historical POs.
- **COD = `value = 0`** is the standard convention; same-day due.
- **Vendor default** is app-layer — Carmen seeds the term onto the PO at vendor selection, but the user can still override.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_credit_term`

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

## 6. Business Rules

- **Uniqueness.** `name` unique among non-deleted rows (DB-enforced).
- **Deletion guards.** Open POs block hard-delete — inactivate instead.
- **Validation.** `value >= 0`; `name` required.
- **Lifecycle.** Inactive terms hidden from new-PO pickers; historical POs keep their assigned term.
- **Snapshot semantics.** PO stores the term id; the due date is computed at PO creation and stored. Rate/value changes here do not retro-edit historical POs.

## 7. Cross-References

- [purchase-order](/en/inventory/purchase-order) — PO header carries `credit_term_id`; due date = `po_date + value` days.
- [master-data/vendor](/en/inventory/master-data/vendor) — vendors pre-assign a default credit term in app logic; defaulted onto new POs.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_term` (lines ~4548-4572).
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/credit-term/`.
