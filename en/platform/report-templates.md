---
title: Report Templates
description: XML-based report template catalogue with tabbed Dialog/Content/Preview editor, database source binding, and business-unit allow/deny scoping.
published: true
date: 2026-06-10T14:15:00.000Z
tags: platform/report-templates, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# Report Templates

> **At a Glance**
> **Module purpose:** Authoring surface where Carmen-internal admins create and maintain the XML-based report templates that drive every printable document in the platform &nbsp;·&nbsp; **Audience:** Carmen-internal admins and support engineers holding `report_template.*` permission grants (see [Permissions](/en/platform/report-templates/permissions)) &nbsp;·&nbsp; **Key entities/tables:** `tb_report_template` (fields: `name`, `description`, `report_group`, `kind`, `dialog`, `content`, `source_type`, `source_name`, `source_params`, `allow_business_unit`, `deny_business_unit`, `is_standard`, `is_active`, `builder_key`) &nbsp;·&nbsp; **Sub-pages:** 4

## 1. Overview

The Report Templates module is the authoring surface for the platform's report definitions. Each row in `tb_report_template` describes one printable/exportable document: a human-readable name, a `report_group` tag for grouping in the runtime picker, two XML payloads (a **Dialog XML** that defines the filter form shown to the end user, and a **Content XML** that defines the rendered output), a data-source binding (`source_type` + `source_name` + `source_params`), and access-control fields that constrain which business units may run it. The list view at `/report-templates` (`ReportTemplateManagement.tsx`) is a server-paginated, searchable, filterable catalogue with status/source-type facets and CSV export. The edit page at `/report-templates/:id/edit` and `/report-templates/new` (`ReportTemplateEdit.tsx`) is a two-column layout: a left rail of template info, BU scope, metadata, and data-source binding, and a right pane with the tabbed XML editors and the live Dialog preview.

The data-source binding is the runtime contract. A template either reads from a database **view** (no parameters; filters apply via the runtime WHERE clause), a **function** (positional arguments derived from `source_params`), or a **procedure** (same positional arguments plus a trailing INOUT refcursor named `rs`; the procedure is responsible for applying its own filters). Each `source_params` row maps one filter field from the Dialog XML (e.g. `DateFrom`) to a PostgreSQL type and a `nullable` flag. The `source_name` is a plain identifier without schema prefix or quotes — it is resolved against each tenant's schema at runtime. A "Browse in BU" probe lets an admin pick a target business unit, fetch the list of views/functions/procedures that actually exist in that tenant's schema, and select one rather than typing the identifier from memory.

Templates are split into **standard** (shipped/curated) and **custom** (per-customer) via `is_standard`, and into **active**/**inactive** via `is_active`; both are toggleable per row from the Edit page and used as list-view facets. The `allow_business_unit` and `deny_business_unit` chip-input lists scope a template to specific BUs (blank `allow` = all; `deny` overrides). Editing a template surfaces XML validation inline (line count, parse error dot per tab) and warns about unsaved changes via the sticky bottom action bar and the `useUnsavedChanges` hook. Detailed UI behaviour and the XML schema itself live on the sub-pages — this landing page only orients.

## 2. Business Context

Hospitality platforms print and email a long tail of operational documents — purchase orders, GRN slips, store-requisition pick lists, valuation reports, food-cost summaries — and the layout of each is rarely uniform across customers. Brand groups want their logo and address block; finance teams want the exchange rate stamped at the top; some properties need a Thai-language variant alongside the English original. Hard-coding every variation into application code is untenable, so the platform externalises the report definition into XML rows that Carmen support engineers (not customers) can edit through this admin surface.

The `tb_report_template` row therefore plays two roles. Operationally, it is the source the report runtime executes when a user clicks "print" or opens a report — the Dialog XML renders the parameter form, the Content XML renders the output, and `source_name`/`source_params` decide which database object to call. Commercially, it is the unit of customisation: shipping a new printable for a customer means adding (or cloning) a row here, not redeploying the application. Keeping authoring inside the platform admin product — gated behind the `report_template.*` permission keys ([rbac](/en/platform/rbac)) — preserves that customisation contract without exposing customers to the underlying XML. Which `kind="print"` template actually renders a given document type at print time is decided by the sibling [print-template-mapping](/en/platform/print-template-mapping) module, not here.

## 3. Key Concepts

- **Report template**: A single row in `tb_report_template` that fully describes one printable/exportable document: identification fields (`name`, `description`, `report_group`, `kind`), the two XML payloads (`dialog`, `content`), the data-source binding (`source_type`, `source_name`, `source_params`), the BU scope (`allow_business_unit`, `deny_business_unit`), and the lifecycle flags (`is_standard`, `is_active`, `builder_key`).
- **Dialog XML**: The XML payload stored in the `dialog` field that the report runtime uses to render the filter/parameter form shown to the end user before the report runs. Edited in the **Dialog XML** tab of the right pane with line count and inline validation.
- **Content XML**: The XML payload stored in the `content` field that defines how the report output is rendered. Edited in the **Content XML** tab; the editor accepts `.frx`, `.xml`, or `.txt` uploads, reflecting that legacy reports were authored in FastReport `.frx` and migrated into XML here.
- **Preview**: The third tab of the right pane that renders the Dialog XML as a disabled form so the author can see exactly what the end user will see without running the report.
- **Source type**: One of `view`, `function`, or `procedure`. Views take no parameters (the runtime applies filters via a WHERE clause); functions and procedures must declare positional parameters via `source_params`. Procedures must additionally accept a trailing INOUT refcursor (default name `rs`) and are responsible for applying filters internally.
- **Source name**: A plain SQL identifier (no schema prefix, no quotes) that names the view/function/procedure in each tenant's schema. Resolved at runtime against the calling business unit's schema. Required when `source_type` is `function` or `procedure`.
- **Source params**: An ordered list mapping a Dialog filter field (`filter`, e.g. `DateFrom`) to a PostgreSQL `type` (e.g. `date`, `uuid`, `text`) with a `nullable` flag. Persisted as `{ params: [...] }`. Empty for `view` sources.
- **Allow / Deny business unit**: Two comma-separated BU-code lists captured via chip inputs. A blank `allow` list means "all business units may run this template"; the `deny` list overrides `allow`.
- **Kind (`report` vs. `print`)**: The `kind` column splits the catalogue into user-facing analytical reports (`"report"`) and printable document layouts (`"print"`). The `"print"` rows are the ones [print-template-mapping](/en/platform/print-template-mapping) rows point at, selected per document type via `report_group` matching. `kind` exists on the API type but is **not exposed** in the SPA edit form.
- **Standard vs. Custom**: The `is_standard` flag distinguishes templates shipped/curated by Carmen (`Standard`) from per-customer additions (`Custom`). Surfaced as a column badge in the list view.
- **Active / Inactive status**: The `is_active` flag controls whether the template appears in runtime pickers. Inactive templates remain editable here but are hidden from end users.
- **Builder key**: Optional short identifier (e.g. `pr-summary`) that links a template to a builder/registration in application code. Free-text and not currently validated by the admin product.
- **Probe BU picker**: A development-affordance inside the Source section of the Edit page that loads the actual list of views/functions/procedures from a chosen tenant schema (`reportTemplateService.listDbObjects`) so the admin can pick `source_name` from a dropdown rather than typing.

## 4. Roles and Personas

Access is governed by the platform's permission-based RBAC model ([rbac](/en/platform/rbac)): each route carries its own `requiredPermission` key on `PrivateRoute`, and a session needs the matching `report_template.*` grant (or the super-admin flag) to pass. A session missing the key sees `<AccessDenied>` inside the normal `<Layout>` shell.

| Route | `requiredPermission` |
|---|---|
| `/report-templates` | `report_template.read` |
| `/report-templates/new` | `report_template.create` |
| `/report-templates/:id/edit` | `report_template.update` |

Within the surface, the mutating actions carry their own `<Can>` gates: **Add Template** is wrapped in `report_template.create`, row **Edit** in `report_template.update`, row **Delete** in `report_template.delete` (in-page only — no route requires the delete key), and the edit page's **Edit** toggle in `report_template.update`. None of these gates pass a `clusterId` — report templates are tenant-global, so checks resolve without per-cluster narrowing. The sidebar entry is filtered on `report_template.read`. Full matrix, bootstrap exception, and gate mechanics on [Permissions](/en/platform/report-templates/permissions).

End customers never reach this module — they consume report output through the runtime picker, not the template catalogue. Authoring remains a Carmen-internal task: granting someone access means assigning them a catalog role that bundles the `report_template.*` keys (until 2026-06 this surface was instead hardcoded to the legacy `platform_admin` / `support_manager` / `support_staff` role enum, since removed — migration mapping in [rbac](/en/platform/rbac) §5).

## 5. Related Modules

- [rbac](/en/platform/rbac) — the permission model behind the `report_template.*` keys: catalog, roles, scoped assignments, super-admin bypass; gate mechanics in [rbac permissions](/en/platform/rbac/permissions)
- [print-template-mapping](/en/platform/print-template-mapping) — the routing table that decides which `kind="print"` template renders each document type at print time: mappings select print-kind rows per document type (the edit form floats templates matching `kind = "print"` and `report_group = <document type>` to the top), with one `is_default` per type and per-BU allow/deny scoping. Report Templates *authors* the layouts; Print Template Mapping decides *which one is used*
- [business-units](/en/platform/business-units) — supplies the BU codes used in the `allow_business_unit` / `deny_business_unit` chip inputs and the "Probe BU" picker's tenant-schema lookups
- [clusters](/en/platform/clusters) — documents the cluster/BU hierarchy above the BU level; report templates are tenant-global and carry no cluster FK
- [users](/en/platform/users) — the user identity rows that RBAC role assignments point at; granting report-template access means assigning a role bundling the `report_template.*` keys

## 6. Reference Sources

- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/ReportTemplateManagement.tsx`, `../carmen-platform/src/pages/ReportTemplateEdit.tsx`, `../carmen-platform/src/services/reportTemplateService.ts`, `../carmen-platform/src/App.tsx`

## 7. Pages in This Module

- [Data Model](/en/platform/report-templates/data-model) — `tb_report_template` entity, JSON payloads (Dialog/Content XML are `String @db.Text`; `source_params`, `signature_config`, BU scope are JsonB), divergence check against SPA `ReportTemplate` type.
- [Permissions](/en/platform/report-templates/permissions) — per-route `requiredPermission` keys (`report_template.read` / `.create` / `.update`), in-page `<Can>` gates (incl. the route-less `report_template.delete`), sidebar filter, bootstrap exception, effective access matrix by grant.
- [UI Screens](/en/platform/report-templates/ui-screens) — `ReportTemplateManagement` list with Status + Source Type filters, 2-pane `ReportTemplateEdit` (left: Template Info + Business Unit Scope + Metadata + Data Source cards; right: 3-tab CodeMirror — Dialog XML / Content XML / Preview), inline Browse-in-BU panel, sticky action bar.
- [XML Spec](/en/platform/report-templates/xml-spec) — Dialog XML element catalogue (`<Dialog>`/`<Label>`/`<Date>`/`<Lookup>`), positional Label/control pairing, opaque Content XML, source_params binding, validation scope (well-formedness only), worked example.
