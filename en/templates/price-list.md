---
title: Price List Template
description: Reusable RFQ / pricelist template defining currency, validity, reminders, and escalation — the parent of vendor pricelists.
published: true
date: 2026-05-17T11:00:00.000Z
tags: templates, price-list, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Price List Template

> **At a Glance**
> **Owner:** Product Admin / Procurement Lead &nbsp;·&nbsp; **Table:** `tb_pricelist_template` &nbsp;·&nbsp; **Used by:** [[vendor-pricelist]] (RFQ rounds spawn from a template) &nbsp;·&nbsp; The shape of a pricelist round — currency, validity, reminders, escalation.

## 1. What & Who

A pricelist template is the **shape of a pricelist round**: which currency the quote is in, how many days the resulting pricelist stays valid, what reminder schedule chases vendors before the deadline, and after how many days an unfilled response escalates. The buyer picks the template when starting a new RFQ round; actual vendor responses live on the `tb_pricelist` child table.

Templates speed up recurring procurement cycles — instead of re-configuring every RFQ, the buyer reuses (for example) the "Quarterly Beverage RFQ" template with all its notification settings already in place.

**Maintained by** Product Admin or the procurement lead. **Read by** the RFQ creation flow and the reminder background job.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Create a template | Master Data → Pricelist Templates → New | Pick currency, validity, reminders |
| Activate for new rounds | Set `status = active` | Selectable in the new-RFQ picker |
| Edit reminder schedule | Template edit → reminder days | Array of days-before-deadline (e.g. `[14,7,3,1]`) |
| Retire a template | Set `status = inactive` | Removed from pickers; historical RFQs still readable |
| Clone for a variant | Use UI clone action | Avoids re-entering currency/validity/reminders |
| Change vendor instructions | Template edit → vendor instructions text | Renders to vendor when RFQ is sent |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Name already exists" | Duplicate among non-deleted templates | Pick different name (app-enforced) |
| Cannot delete | Template has issued RFQ rounds | Flip `status = inactive` instead |
| Reminder days rejected | Not sorted descending or contains non-positive integers | Fix the array (e.g. `[14,7,3,1]`) |
| "Currency not active" | `tb_currency.is_active = false` | Activate currency under [[master-data/currency]] |
| Validity negative | `validity_period < 0` | Use a non-negative integer |

## 4. Edge Cases

- **Currency change on an active template** affects only new RFQ rounds; existing pricelists retain their original currency.
- **Reminder execution** lives in a background job; the template captures the *schedule*, not the job state.
- **Lifecycle.** `draft` → `active` → `inactive`. `draft` is editable; `active` is selectable; `inactive` removes from pickers but stays readable on history.
- **Hard-delete blocked** once a template has been issued; soft-delete only.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_pricelist_template`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Template name. |
| `status` | `enum_pricelist_template_status` | No | `draft` (default), `active`, `inactive`. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `vendor_instructions` | `String? @db.Text` | Yes | Rendered to vendor on RFQ send. |
| `currency_id` | `String? @db.Uuid` | Yes | FK to `tb_currency`. |
| `currency_code` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `validity_period` | `Int?` | Yes | Days the resulting pricelist stays valid after issuance. |
| `send_reminders` | `Boolean?` | Yes | Master switch (default `true`). |
| `reminder_days` | `Json? @db.JsonB` | Yes | Array of days-before-deadline (e.g. `[14, 7, 3, 1]`). |
| `escalation_after_days` | `Int? @db.Integer` | Yes | Days after deadline to escalate (default `0`). |
| `info`, `dimension`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** Primary key on `id`. FK on `currency_id` `onDelete: NoAction`. Reverse relations to `tb_pricelist_template_detail` and `tb_request_for_pricing`.

**`enum_pricelist_template_status`:** `draft`, `active`, `inactive`.

## 6. Business Rules

- **Uniqueness.** `name` unique among non-deleted (application-enforced; no explicit `@@unique`).
- **Deletion guards.** Template issued as a real RFQ cannot be hard-deleted; flip `inactive` instead.
- **Validation.** `validity_period >= 0`; `escalation_after_days >= 0`; `reminder_days` sorted descending with positive integers; `currency_id` must reference an active currency.
- **Lifecycle.** `draft` editable; `active` selectable for new RFQs; `inactive` removes from pickers, keeps readable.
- **Reminder execution.** Background job inspects flags + RFQ deadline; template captures schedule only.
- **Currency change.** New rounds only — historical pricelists unchanged.

## 7. Cross-References

- [[vendor-pricelist]] — sole consumer. RFQ rounds spawn from a template.
- [[master-data/currency]] — `currency_id` resolution.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_pricelist_template` (lines ~3869-3911), `enum_pricelist_template_status` (lines ~3863-3867).
- **Frontend:** `../carmen-inventory-frontend/app/(root)/(protected)/vendor-management/price-list-template/`.
