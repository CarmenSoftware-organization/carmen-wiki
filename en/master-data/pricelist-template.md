---
title: Pricelist Template
description: Reusable RFQ / pricelist template defining currency, validity, reminders, and escalation — the parent of vendor pricelists.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, pricelist-template, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Pricelist Template

## 1. Purpose

A pricelist template is the *shape* of a pricelist round: which currency the quote is in, how many days the resulting pricelist stays valid, what reminder schedule chases the vendor before the deadline, and after how many days an unfilled response escalates to a human. The template is what the buyer picks when starting a new Request-for-Pricing round; the actual vendor responses live on the `tb_pricelist` child table.

Templates speed up recurring procurement cycles — instead of re-configuring every RFQ, the buyer reuses (for example) the "Quarterly Beverage RFQ" template with all its notification settings already in place.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_pricelist_template`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Template name. |
| `status` | `enum_pricelist_template_status` | No | `draft` (default), `active`, or `inactive`. |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `vendor_instructions` | `String? @db.Text` | Yes | Instructions rendered to vendor when the RFQ is sent. |
| `currency_id` | `String? @db.Uuid` | Yes | FK to `tb_currency`. |
| `currency_code` | `String? @db.VarChar` | Yes | Denormalised display copy. |
| `validity_period` | `Int?` | Yes | Days the resulting pricelist remains valid after issuance. |
| `send_reminders` | `Boolean?` | Yes | Master switch for reminder emails (default `true`). |
| `reminder_days` | `Json? @db.JsonB` | Yes | Array of days-before-deadline to send reminders, e.g. `[14, 7, 3, 1]`. |
| `escalation_after_days` | `Int? @db.Integer` | Yes | Days after deadline to escalate (default `0`). |
| `info`, `dimension`, `doc_version` | — | Mixed | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** primary key on `id`. FK on `currency_id` `onDelete: NoAction`. Reverse relations to `tb_pricelist_template_detail` and `tb_request_for_pricing`.

`enum_pricelist_template_status` values: `draft`, `active`, `inactive`.

## 3. Usage / Cross-References

- [[vendor-pricelist]] — sole consumer. RFQ rounds and resulting pricelists are spawned from a template; the template's currency, validity, and reminder schedule cascade to each invitation.
- [[master-data/currency]] — `currency_id` resolves here.

## 4. Configuration UI

Managed by **Product Admin** (or the procurement lead) under the Master Data area or inside the Vendor Pricelist module. The detail screen surfaces the template's line items (`tb_pricelist_template_detail`, not in this entity's scope) and the notification schedule.

## 5. Business Rules

- **Uniqueness.** `name` should be unique among non-deleted rows (application-enforced — no explicit `@@unique`).
- **Deletion guards.** A template that has been issued as a real RFQ cannot be hard-deleted; status flip to `inactive` retires it from new-round pickers.
- **Validation.** `validity_period >= 0`, `escalation_after_days >= 0`. `reminder_days` array must be sorted descending and contain only positive integers. `currency_id` must reference an active currency.
- **Lifecycle.** `status = draft` is editable; flipping to `active` makes it selectable for new RFQs. `inactive` removes it from pickers but keeps it readable on historical RFQs.
- **Reminder execution.** A background job inspects `send_reminders`, `reminder_days`, and the RFQ deadline to send chasers; the template captures the schedule but does not own its execution.
- **Currency change.** Changing `currency_id` on an `active` template affects only new RFQ rounds; existing pricelists retain their original currency.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_pricelist_template` (lines ~3869-3911), `enum_pricelist_template_status` (lines ~3863-3867).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/vendor-management/pricelist-template/`.
- **Cross-module:** see Section 3.
