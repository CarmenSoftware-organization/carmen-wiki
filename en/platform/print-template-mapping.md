---
title: Print Template Mapping
description: Print Template Mapping module overview — routing document types (PR, PO, GRN, …) to FastReport print templates with a default flag, display ordering, and per-BU allow/deny scoping.
published: true
date: 2026-06-10T12:45:00.000Z
tags: platform/print-template-mapping, carmen-software
editor: markdown
dateCreated: 2026-06-10T12:45:00.000Z
---

# Print Template Mapping

The **Print Template Mapping** module is the routing table between document types and print layouts: each row says "when a document of type X prints, render it with this `tb_report_template`." Where [Report Templates](/en/platform/report-templates) *authors* the FastReport layouts (`kind = "print"` rows), this module decides *which one is used* — per document type, optionally per business unit, with one default per type for the legacy Print button and ordered alternates for the "Print as…" menu. At runtime the print pipeline asks `GET .../resolve?document_type=X&bu_code=Y` and gets back exactly one mapping.

> **At a Glance**
> **Module purpose:** Map document types (PR, PO, GRN, SR, CN, IA, PC, SC, RFQ, INV) to `kind="print"` report templates, with `is_default` for the legacy Print button, `display_label`/`display_order` for the "Print as…" menu, and per-BU allow/deny scoping &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA, the micro-report Go service, and document-print flows in micro-business &nbsp;·&nbsp; **Key entities/tables:** `tb_print_template_mapping` (owned), `tb_report_template` (referenced — see Report Templates) &nbsp;·&nbsp; **Runtime contract:** `GET /api-system/print-template-mappings/resolve` — first active mapping permitting the BU, ordered `is_default DESC, display_order ASC` &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The SPA exposes the module through two screens:

- **`/print-template-mapping` → `PrintTemplateMappingManagement`** — a **deliberate deviation** from the SPA's standard server-side `DataTable` Management pattern: a single card with grouped sub-tables, one group per document type (Badge code + label + "N mapping(s)" count), filtered only by a document-type select and an "Active only" checkbox. No debounced search, no CSV export, no pagination controls, no persisted `localStorage` state — the dataset is small and static enough that the heavyweight furniture would be noise. See [UI Screens](/en/platform/print-template-mapping/ui-screens) §1 for the full rationale.
- **`/print-template-mapping/new` and `/print-template-mapping/:id/edit` → `PrintTemplateMappingEdit`** — the standard single-card form. Create mode is immediately editable; the edit route opens read-only behind an Edit toggle (the same view/edit pattern as Applications). Its signature element is the **Report Template select**, which floats templates matching `kind = "print"` and `report_group = <chosen document type>` to the top with an "N match / M total" count in the placeholder.

Behind the SPA, the backend-gateway controller (`api-system/print-template-mappings`) is a thin authenticated proxy: every call is forwarded over plain HTTP to the **micro-report Go service** (`/api/print-template-mappings/*`), which owns the CRUD, the canonical document-type list, and the `resolve` logic. The mapping rows themselves live in the platform Postgres schema (`tb_print_template_mapping`), read by Go through a LEFT JOIN that denormalizes the template name and group onto each row.

## 2. Business Context

Carmen documents print through FastReport: when a user clicks **Print** on a PO, GRN, or store requisition, the backend builds the document's data payload and needs to know *which template row* renders it. Historically that was a naming convention (`"<Type> Document"`); this module replaces the convention with explicit data:

- The **legacy Print button** prints with the mapping flagged `is_default` for the document type — one click, no menu.
- The **"Print as…" menu** lists every active mapping for the type, sorted by `display_order` and labelled with `display_label` (e.g. "Standard PR (A4 Portrait)") — so a property can offer a portrait original plus a landscape or branded variant.
- **Per-BU allow/deny lists** exist because layouts diverge per property: a hotel group's flagship may demand its own branded GRN slip while sister properties keep the standard one. A blank allow list means "all business units"; the deny list always wins. This is the same scoping convention `tb_report_template` itself carries.

The platform seed (`seed.print-templates.ts`) ships a portrait and a landscape `kind="print"` template per document type and registers the portrait as that type's default mapping (`display_order 0`), so a fresh environment can print every document type out of the box.

## 3. Key Concepts

- **Mapping row** — `(document_type, report_template_id)` plus presentation (`display_label`, `display_order`), the `is_default` flag, BU scoping (`allow_business_unit` / `deny_business_unit`), and `is_active`. Multiple rows may share a document type.
- **Document types** — a **hard-coded list in the micro-report Go service** (`model.SupportedDocumentTypes`): PR, PO, GRN, SR, CN, IA, PC, SC, RFQ, INV. Served by `GET .../document-types` (which populates every dropdown in the SPA) and **validated server-side** — create/update with an unlisted code is rejected with 400. Adding a document type is a Go code change, not a data change.
- **Default flag** — "use this template when the user clicks the legacy Print button." The UI does not stop you from saving two defaults, but the Go service runs a best-effort `EnsureSingleDefault` after every create/update that saves `is_default = true`, demoting any other default for the same document type. Note the column *defaults to true* — schema, Go, and SPA all agree, so an operator must consciously untick it for alternates.
- **Display label and order** — pure presentation for the "Print as…" menu. `display_order` doubles as the resolve tie-breaker among rows with the same `is_default` value.
- **Allow/deny BU lists** — JSONB arrays of BU codes, edited as comma-separated text in the SPA. Blank allow = all BUs; blank deny = none; a code in both lists is denied (deny is checked first). Full precedence rules and pseudo-code are in [Permissions](/en/platform/print-template-mapping/permissions) §3.
- **Relation to Report Templates** — a mapping points at one `tb_report_template` row; the intended pairing is `kind = "print"` with `report_group` equal to the document-type code, which is why the edit form's template select floats those matches to the top. The pairing is a convention, not a constraint: the select still offers every template, and the database enforces no FK (see [Data Model](/en/platform/print-template-mapping/data-model)).
- **Resolution** — `resolve(document_type, bu_code)` filters to active, non-deleted rows for the type, orders by `is_default DESC, display_order ASC`, and returns the **first row whose BU lists permit the `bu_code`** — so a default that denies the BU silently falls through to the next permitted alternate. No match is a 404.

## 4. Roles and Personas

Access is permission-gated through [Platform RBAC](/en/platform/rbac), with route guards and in-page `<Can>` gates:

| Surface | Gate | Key |
|---|---|---|
| `/print-template-mapping` route + "Print Mapping" sidebar entry (Content group, Printer icon) | `PrivateRoute` / sidebar filter | `print_template_mapping.read` |
| `/print-template-mapping/new` route | `PrivateRoute` | `print_template_mapping.create` |
| `/print-template-mapping/:id/edit` route | `PrivateRoute` | `print_template_mapping.update` |
| New Mapping button (list header) | `<Can>` | `print_template_mapping.create` |
| Row Edit (pencil icon button) | `<Can>` | `print_template_mapping.update` |
| Row Delete (trash icon button) | `<Can>` | `print_template_mapping.delete` |
| Edit toggle (edit-page header) | `<Can>` | `print_template_mapping.update` |

As in Applications, `print_template_mapping.delete` exists only as an in-page gate (no route requires it, and the edit page has no delete action), and the edit page's Save button is unwrapped but unreachable without the gated Edit toggle. The full matrix plus the resolve-time BU rules — a second, independent authorization story — is in [Permissions](/en/platform/print-template-mapping/permissions).

## 5. Related Modules

- [Report Templates](/en/platform/report-templates) — the other half of the feature pair: it owns `tb_report_template` (the layouts, their Dialog/Content XML, source binding, and `kind`/`report_group` fields this module selects on). That module's data-model page explicitly scopes `tb_print_template_mapping` out; this module documents it.
- [Business Units](/en/platform/business-units) — the allow/deny lists hold BU *codes* (`tb_business_unit.code`), entered as free text with no validation against the BU registry; a typo simply never matches at resolve time.
- [Platform RBAC](/en/platform/rbac) — defines and resolves the four `print_template_mapping.*` keys (seeded in `seed.platform-permission.ts`).

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — the three `print_template_mapping.*` route guards.
- `../carmen-platform/src/components/Layout.tsx` — "Print Mapping" sidebar entry (Content group, `print_template_mapping.read`).
- `../carmen-platform/src/pages/PrintTemplateMappingManagement.tsx` — grouped-card list, filters, `<Can>` gates, delete dialog.
- `../carmen-platform/src/pages/PrintTemplateMappingEdit.tsx` — create/view/edit form, template-select float logic, CSV BU inputs.
- `../carmen-platform/src/services/printTemplateMappingService.ts` — REST client and the `PrintTemplateMapping` / `DocumentType` types.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_print_template_mapping` (line 776), `tb_report_template` (line 701).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform_print-template-mappings/` — the proxy controller/service.
- `../micro-report/controller/print_template_mapping_controller.go`, `../micro-report/db/print_template_mapping_repo.go`, `../micro-report/model/print_template_mapping.go` — CRUD, `SupportedDocumentTypes`, `Resolve`, `EnsureSingleDefault`.
- `../carmen-turborepo-backend-v2/apps/micro-business/src/common/print-report.helper.ts` — the document-print consumer.

## 7. Pages in This Module

- [Data Model](/en/platform/print-template-mapping/data-model) — the `tb_print_template_mapping` field table (no unique constraints, no DB-level FK), the FK-side view of `tb_report_template`, and the divergences between Prisma, the SPA types, and the Go service.
- [UI Screens](/en/platform/print-template-mapping/ui-screens) — the grouped-card list (and why it deviates from the DataTable pattern) and the view/edit-toggle form with the match-floating template select.
- [Permissions](/en/platform/print-template-mapping/permissions) — the `print_template_mapping.*` gate matrix, the resolve-time allow/deny precedence rules, and the edge-case matrix for testers.
