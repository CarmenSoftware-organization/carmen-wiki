---
title: Print Template Mapping — Data Model
description: The tb_print_template_mapping table (no unique constraints, no DB-level FK), the referenced tb_report_template, the denormalized Go read shape, and the update-merge JSONB quirks.
published: true
date: 2026-06-10T12:45:00.000Z
tags: book/platform, print-template-mapping, data-model
editor: markdown
dateCreated: 2026-06-10T12:45:00.000Z
---

# Print Template Mapping — Data Model

> **At a Glance**
> **Tables:** `tb_print_template_mapping` (owned) &nbsp;·&nbsp; `tb_report_template` (referenced — full doc in Report Templates) &nbsp;·&nbsp; **Enums:** none — `document_type` is VarChar validated against a hard-coded Go list of 10 codes &nbsp;·&nbsp; **Constraints:** `@id` only — **no `@@unique`, no Prisma `@relation`/DB FK**; the template link and single-default rule are application-layer &nbsp;·&nbsp; **Read shape:** Go LEFT JOIN denormalizes `template_name` / `template_group` / audit names onto each row &nbsp;·&nbsp; **Write quirk:** `PUT` is a partial merge and JSON `null` means "leave unchanged" — the SPA cannot clear a BU list

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The module owns a single table. `tb_print_template_mapping` is a routing row: a `document_type` code, a pointer to the `tb_report_template` that renders it, presentation fields for the print menus (`is_default`, `display_label`, `display_order`), the BU allow/deny pair, `is_active`, and the platform-standard audit trio. The schema comment states the contract: multiple rows may share a `document_type`; exactly one *should* be flagged `is_default` for the legacy Print button, the rest surface in the "Print as…" menu.

Unusually for the platform schema, the table carries **no unique constraints and no Prisma relations at all** — the database happily stores duplicate `(document_type, report_template_id)` pairs, dangling `report_template_id` values, and multiple defaults. Every integrity rule lives in the application layer: the micro-report Go service validates `document_type` against its hard-coded list, demotes competing defaults best-effort after each save, and joins the template by id at read time. Testers should treat the DB as permissive and probe the service-layer rules instead.

Although the table lives in the platform Prisma schema, the **CRUD owner is the micro-report Go service** (GORM, `db/print_template_mapping_repo.go`); the backend-gateway controller is a pass-through proxy, and Prisma touches the table only in the seed and in micro-business's inline print-path query (§5).

## 2. Entities

### 2.1 `tb_print_template_mapping`

One document-type → template routing row. Schema line 776.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `document_type` | `String @db.VarChar(50)` | No | Document-type code (`PR`, `PO`, `GRN`, …); free-form in the schema, validated by the Go service against `SupportedDocumentTypes` (§4) |
| `report_template_id` | `String @db.Uuid` | No | Id of the rendering `tb_report_template` row — **no `@relation`, no DB FK**; resolved by LEFT JOIN at read time |
| `is_default` | `Boolean @default(true)` | No | Template for the legacy Print button. **Defaults to `true`** — every new row claims default unless explicitly unticked |
| `display_label` | `String? @db.VarChar(255)` | Yes | Label shown in the "Print as…" menu (e.g. "Standard PR (A4 Portrait)") |
| `display_order` | `Int @default(0)` | No | Sort position in the "Print as…" menu; resolve tie-breaker (§5 row 7) |
| `allow_business_unit` | `Json? @db.JsonB` | Yes | Array of BU codes allowed to use this mapping; `NULL`/empty = all BUs (same convention as `tb_report_template`) |
| `deny_business_unit` | `Json? @db.JsonB` | Yes | Array of BU codes denied; `NULL`/empty = none; deny wins over allow |
| `is_active` | `Boolean @default(true)` | No | Inactive rows are skipped by `resolve` and hidden behind the list's "Active only" filter |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id — bare UUID, no FK |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id — bare UUID, no FK |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id — bare UUID, no FK |

**Constraints:**
- `@id` on `id` — and nothing else. No `@@unique` (contrast `tb_application`'s soft-delete-aware name uniqueness): duplicate `(document_type, report_template_id)` rows and multiple `is_default = true` rows per type are representable at the DB level.
- No FK constraints of any kind — `report_template_id` and the audit ids are bare UUIDs.

**Indexes:**
- `@@index([document_type])` — map `"idx_print_template_mapping_document_type"` — drives both the list filter and `resolve`.
- `@@index([report_template_id])` — map `"idx_print_template_mapping_template_id"` — drives "where is this template used" lookups.

### 2.2 `tb_report_template` (referenced)

The mapping's target. Full documentation lives in [Report Templates — Data Model](/en/platform/report-templates/data-model); only the FK-side perspective matters here. A mapping is intended to point at a row with `kind = "print"` (a printable document layout, as opposed to `kind = "report"` analytical reports) whose `report_group` equals the mapping's `document_type` — the SPA's template select floats exactly those matches. The Go read path LEFT JOINs the template to denormalize `name` (as `template_name`) and `report_group` (as `template_group`) onto every mapping row, so the admin UI never makes a second round-trip. Because the join is a LEFT JOIN with no FK behind it, a mapping whose template was deleted still loads — with `template_name` null — rather than failing.

## 3. Relationships

```
tb_report_template  1 ─── M  tb_print_template_mapping
    (logical only — no Prisma @relation, no DB FK;
     joined via report_template_id in micro-report's read SQL)

tb_print_template_mapping.created_by_id / updated_by_id / deleted_by_id
    ──> tb_user.id  (audit actors by convention — bare UUIDs, no FK;
         micro-report joins tb_user_profile on created_by_id and
         updated_by_id only — deleted_by_id gets no display-name join)
```

There is no relation to clusters or business units: BU scoping is carried as JSONB code arrays, not join rows, so nothing in the schema prevents a list from naming a BU code that does not exist.

## 4. Enums

No Prisma enums. Two columns carry constrained vocabularies enforced outside the schema:

- **`document_type`** — validated on create/update by the micro-report Go service against `model.SupportedDocumentTypes` (a hard-coded Go slice, also served by `GET .../document-types`): `PR` Purchase Request · `PO` Purchase Order · `GRN` Good Received Note · `SR` Store Requisition · `CN` Credit Note · `IA` Inventory Adjustment · `PC` Physical Count · `SC` Spot Check · `RFQ` Request For Quotation · `INV` Invoice. An unlisted code is a 400 ("unsupported document_type — see GET /document-types"; the update path omits the "— see GET /document-types" suffix). Extending the list is a Go code change and redeploy.
- **`allow_business_unit` / `deny_business_unit`** — by convention JSON arrays of BU code strings; the Go reader tolerates `[]string` or `[]any`-of-strings and silently drops non-string elements.

## 5. Divergences from carmen-platform SPA shape

The SPA type is `PrintTemplateMapping` in `src/services/printTemplateMappingService.ts` (not `src/types/index.ts`); the form mapping lives in `PrintTemplateMappingEdit.tsx`. Divergences against Prisma and the Go service as of 2026-06-10:

| # | Aspect | SPA shape | Storage / service reality | Notes |
|---|--------|-----------|---------------------------|-------|
| 1 | BU list typing | `allow_business_unit?: unknown` / `deny_business_unit?: unknown` | `Json?` JSONB array | Deliberately untyped: `rowToForm` tolerates a `string[]` **or** a CSV string on read; on write `parseList` always sends `string[]` (or `null` when blank) |
| 2 | Clearing a BU list | Blank input → payload field `null` | Go treats JSON `null` as *not provided* (nil-interface check) and keeps the stored list; the repo additionally skips nil JSONB columns in its `Updates` map | **Blanking an allow/deny list in the SPA edit form does not clear it server-side.** The only way to clear is a direct `PUT` with an explicit empty array `[]` |
| 3 | `template_name` / `template_group` / `created_by_name` / `updated_by_name` | Optional read fields | **Not columns** — denormalized by micro-report's LEFT JOIN onto `tb_report_template` and `tb_user_profile` | Read-only; never echo them back in writes. `template_name` is null when the joined template is soft-deleted |
| 4 | `PUT` semantics | Sends the full form | **Partial merge**, not replace: Go copies only provided fields onto the loaded row; blank-string `document_type`/`report_template_id` are ignored | Opposite of the Applications module's full-set replace — do not port either convention to the other |
| 5 | Single default | UI does not enforce; checkbox freely tickable on any row | Go runs `EnsureSingleDefault` after create/update when `is_default = true`, demoting other defaults for the document type — **best-effort** (failure only logs a warning) | Duplicate defaults remain representable (direct DB writes, demotion failure); `resolve` tolerates them via the `display_order` tie-break |
| 6 | List pagination | SPA sends only `document_type`/`active_only` and renders everything it gets — no pagination UI | The Go list endpoint applies monorepo-standard pagination with **default `perpage = 10`** | With more than 10 live mappings the SPA list silently shows only the first page — see [UI Screens](./ui-screens.md) §2.5 |
| 7 | Runtime resolution | `printTemplateMappingService.resolve()` exists but no SPA screen calls it | Go `Resolve` honours active flags, BU lists, and `is_default DESC, display_order ASC` ordering | The intended runtime contract. **However**, micro-business's actual print path (`print-report.helper.ts`) queries Prisma directly with the same ordering and **does not apply the BU lists at all** — see [Permissions](./permissions.md) §3 |

## 6. References

REST surface (backend-gateway `api-system/print-template-mappings`, proxied 1:1 to micro-report `/api/print-template-mappings`):

| Method + Path | Purpose | Notes |
|---|---|---|
| `GET /api-system/print-template-mappings` | List | Filters `document_type`, `active_only`; monorepo pagination (`page`/`perpage`/`search`/`sort`/`filter`) forwarded, default `perpage` 10; rows carry the denormalized join fields |
| `GET /api-system/print-template-mappings/document-types` | Canonical document-type list | `{ document_types: [{ code, label }] }` from the hard-coded Go slice |
| `GET /api-system/print-template-mappings/resolve?document_type=X&bu_code=Y` | Runtime resolution | `document_type` required (400 if blank); 404 when no active mapping permits the BU |
| `GET /api-system/print-template-mappings/:id` | Detail | Gateway validates the id as UUID v4 |
| `POST /api-system/print-template-mappings` | Create | `document_type` + `report_template_id` required; `document_type` validated; `EnsureSingleDefault` runs after save when the saved row has `is_default = true` |
| `PUT /api-system/print-template-mappings/:id` | Update | **Partial merge**; JSON `null` = leave unchanged (§5 rows 2, 4); `EnsureSingleDefault` runs after save when the saved row has `is_default = true` |
| `DELETE /api-system/print-template-mappings/:id` | Soft delete | Sets `deleted_at` / `deleted_by_id` |

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_print_template_mapping` (line 776), `tb_report_template` (line 701).
- `../micro-report/model/print_template_mapping.go` — GORM model, `SupportedDocumentTypes`, joined read fields.
- `../micro-report/db/print_template_mapping_repo.go` — read joins, `Resolve`, `EnsureSingleDefault`, the JSONB nil-skip update path.
- `../micro-report/controller/print_template_mapping_controller.go` — input validation and the partial-merge update.

**Secondary (consumer shape):**
- `../carmen-platform/src/services/printTemplateMappingService.ts` — `PrintTemplateMapping`, `DocumentType`, create/update inputs.
- `../carmen-platform/src/pages/PrintTemplateMappingEdit.tsx` — `rowToForm` (CSV-or-array tolerance), `parseList` (write shape).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_print-template-mappings/platform_print-template-mappings.service.ts` — the proxy DTOs.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/seed.print-templates.ts` — the seeded per-type default mappings.

**Cross-links:** [Print Template Mapping landing](/en/platform/print-template-mapping) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Report Templates — Data Model](../report-templates/data-model.md)
