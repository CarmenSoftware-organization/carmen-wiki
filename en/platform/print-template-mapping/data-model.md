---
title: Print Template Mapping — Data Model
description: Historical record — tb_print_template_mapping was dropped by migration 20260723120000_print_form_default; is_default now lives on tb_report_template instead.
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, print-template-mapping, data-model
editor: markdown
dateCreated: 2026-06-10T12:45:00.000Z
---

# Print Template Mapping — Data Model

> **Implementation status (verified 2026-07-29): `tb_print_template_mapping` no longer exists.** Migration `20260723120000_print_form_default` (carmen-turborepo-backend-v2) ran `DROP TABLE "tb_print_template_mapping"` after backfilling its `is_default` semantics onto a new `tb_report_template.is_default` column. This page documents the table as it existed through the last verified sync (2026-06-10) for historical reference only — do not use it as a current schema reference. See [Report Templates — Data Model](/en/platform/report-templates/data-model) for the live `is_default` / `report_group` mechanism.

> **At a Glance (historical)**
> **Table:** `tb_print_template_mapping` — **dropped 2026-07-23** &nbsp;·&nbsp; **Referenced:** `tb_report_template` (still live — see [Report Templates](/en/platform/report-templates/data-model)) &nbsp;·&nbsp; **Enums:** none — `document_type` was VarChar validated against a hard-coded Go list of 10 codes &nbsp;·&nbsp; **Constraints:** `@id` only — no `@@unique`, no Prisma `@relation`/DB FK

## 1. Overview (as it existed through 2026-06-10)

The module owned a single table. `tb_print_template_mapping` was a routing row: a `document_type` code, a pointer to the `tb_report_template` that rendered it, presentation fields for the print menus (`is_default`, `display_label`, `display_order`), a BU allow/deny pair, `is_active`, and the platform-standard audit trio. Unusually for the platform schema, the table carried no unique constraints and no Prisma relations at all — every integrity rule (document-type validation, single-default demotion) lived in the micro-report Go service, not the database.

Although the table lived in the platform Prisma schema, its CRUD owner was the micro-report Go service (GORM); the backend-gateway controller was a pass-through proxy. Both the Go model/repo/controller and the gateway proxy were deleted alongside the table (carmen-turborepo-backend-v2 commit `c135bb21e`).

## 2. Former schema

### 2.1 `tb_print_template_mapping` (dropped)

| Field | Prisma Type | Description |
| ----- | ----------- | ----------- |
| `id` | `String @db.Uuid` | Primary key |
| `document_type` | `String @db.VarChar(50)` | Document-type code (`PR`, `PO`, `GRN`, …); validated by the Go service against `SupportedDocumentTypes` |
| `report_template_id` | `String @db.Uuid` | Id of the rendering `tb_report_template` row — no `@relation`, no DB FK |
| `is_default` | `Boolean @default(true)` | Template for the legacy Print button |
| `display_label` | `String? @db.VarChar(255)` | Label shown in the "Print as…" menu |
| `display_order` | `Int @default(0)` | Sort position; resolve tie-breaker |
| `allow_business_unit` / `deny_business_unit` | `Json? @db.JsonB` | BU-code arrays scoping the mapping |
| `is_active` | `Boolean @default(true)` | Inactive rows skipped by `resolve` |
| audit trio | — | `created_at/by_id`, `updated_at/by_id`, `deleted_at/by_id` — bare UUIDs, no FK |

**What replaced each field:** `is_default` → `tb_report_template.is_default` (now DB-enforced via a partial unique index instead of Go-side best-effort demotion). `document_type` → `tb_report_template.report_group` (still a plain String, now driven by the SPA-side `FORM_REPORT_GROUPS` constant rather than a Go-side hard-coded list). `display_label` / `display_order` — no replacement found; the new Form Groups screen sorts by `is_default` then name, with no per-row label or manual ordering. `allow_business_unit` / `deny_business_unit` on the *mapping* — no replacement; `tb_report_template` carries its own allow/deny pair scoping the template row itself, but there is no longer a way to scope "which template is the default" differently per business unit the way the mapping row could.

## 3. Former relationships

```
tb_report_template  1 ─── M  tb_print_template_mapping   (dropped 2026-07-23)
```

## 4. Former enums

`document_type` was validated against `model.SupportedDocumentTypes` (a hard-coded Go slice, also served by `GET .../document-types`): `PR, PO, GRN, SR, CN, IA, PC, SC, RFQ, INV`. Compare the *current* `FORM_REPORT_GROUPS` list on `tb_report_template.report_group`: `PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP` — gained `SI`, `SO`, `EOP`; lost `INV`; `RFQ` renamed `RFP`. The two lists are not the same vocabulary even though they solve the same problem.

## 5. References

- carmen-turborepo-backend-v2 migration `packages/prisma-shared-schema-platform/prisma/migrations/20260723120000_print_form_default/migration.sql` — the drop, the backfill, and the new unique index.
- carmen-turborepo-backend-v2 commit `c135bb21e` — removal of the Go-side model/repo/controller and the gateway proxy.
- `../carmen-platform/src/constants/reportGroups.ts` — the current `FORM_REPORT_GROUPS` list.

**Cross-links:** [Print Template Mapping landing](/en/platform/print-template-mapping) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Report Templates — Data Model](../report-templates/data-model.md)
