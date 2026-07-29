---
title: Print Template Mapping
description: Removed module — document-type-to-print-template routing was deleted from carmen-platform on 2026-07-23/24 and merged into Report Templates' Form Groups (report_group + is_default).
published: true
date: 2026-07-29T00:00:00.000Z
tags: platform/print-template-mapping, carmen-software
editor: markdown
dateCreated: 2026-06-10T12:45:00.000Z
---

# Print Template Mapping

> **Implementation status (verified 2026-07-29): this module has been removed.** Every screen, route, backend proxy, and database table described below was deleted between 2026-07-23 and 2026-07-24. The document-type → template selection problem this module solved still exists, but it is now solved **inside** [Report Templates](/en/platform/report-templates) via a `report_group` + `is_default` column pair and a new **Form Groups** screen (`/report-form-groups`, not yet documented as its own wiki unit — see the parent Task 5 backlog). This page is kept as a historical record so old cross-links and search hits resolve to an explanation rather than a 404; do not use it as a guide to current behaviour.

Historically, the **Print Template Mapping** module was the routing table between document types and print layouts: each row said "when a document of type X prints, render it with this `tb_report_template`." Where [Report Templates](/en/platform/report-templates) *authored* the FastReport layouts, this module decided *which one was used* — per document type, optionally per business unit, with one default per type for the legacy Print button and ordered alternates for a "Print as…" menu.

> **At a Glance**
> **Status:** REMOVED (confirmed 2026-07-23/24) &nbsp;·&nbsp; **Removed by:** carmen-platform commit `de11377` (SPA pages, routes, sidebar entry, permission keys), carmen-turborepo-backend-v2 commit `c135bb21e` (backend-gateway proxy controller/service + permission-seed rows), migration `20260723120000_print_form_default` (`DROP TABLE tb_print_template_mapping`) &nbsp;·&nbsp; **Replaced by:** `tb_report_template.report_group` (fixed 12-code list, `FORM_REPORT_GROUPS`) + new `tb_report_template.is_default` column, edited from the Report Templates module's new **Form Groups** screen &nbsp;·&nbsp; **Sub-pages:** 3 (kept for historical reference)

## 1. What existed, and when it stopped

The module surfaced as two screens: `/print-template-mapping` (a grouped-card list, one bordered sub-table per document type) and `/print-template-mapping/new` + `/print-template-mapping/:id/edit` (a single-card create/view/edit form whose signature element was a Report Template select that floated `kind="print"` + matching `report_group` templates to the top). Behind the SPA, a backend-gateway controller (`api-system/print-template-mappings`) proxied every call to the micro-report Go service, which owned the CRUD, the canonical ten-code document-type list (`PR, PO, GRN, SR, CN, IA, PC, SC, RFQ, INV`), and the `resolve(document_type, bu_code)` logic. The routing rows lived in the platform Postgres schema as `tb_print_template_mapping`.

That entire stack was deleted in a same-week pair of commits:

- **carmen-platform, commit `de11377`** ("remove the print template mapping pages", 2026-07-24): deleted `PrintTemplateMappingManagement.tsx`, `PrintTemplateMappingEdit.tsx`, `printTemplateMappingService.ts`, their tests, the three `/print-template-mapping*` routes and `requiredPermission` guards in `App.tsx`, the sidebar "Print Mapping" entry in `Layout.tsx`, and the breadcrumb entry — 1,476 deletions, 1 insertion, across 10 files.
- **carmen-turborepo-backend-v2, commit `c135bb21e`** ("delete the print-template-mapping module and its reports proxy", 2026-07-23): deleted the backend-gateway `platform_print-template-mappings` controller/service/module (and their specs) and the `reports.controller.ts`/`reports.service.ts` pair that exposed the resolve proxy; removed the four `print_template_mapping.*` rows from `seed.platform-permission.data.ts` and every reference to them from `seed.platform-role-permission.data.ts`'s role bundles (`platform_admin`, `support_manager`, `support_staff`) — the permission catalog itself no longer defines these keys.
- **Migration `20260723120000_print_form_default`** (same backend repo): added `tb_report_template.is_default BOOLEAN NOT NULL DEFAULT false`; backfilled it from every active `tb_print_template_mapping` row; created a partial unique index `idx_report_template_default_per_group` on `tb_report_template(report_group)` (`WHERE is_default AND template_type = 'form' AND deleted_at IS NULL`) to enforce "one default form template per group"; renamed the `RFQ` report group to `RFP` for form-type templates; and finished with `DROP TABLE "tb_print_template_mapping"`. The table is gone at the schema level, not just unused.

Bruno's `platform/print-template-mapping/` collection folder is likewise empty on the current branch — every request file was moved to `_archived/2026-07-29/platform/print-template-mapping/` by the API-contract maintainers the same week this wiki pass ran.

## 2. What replaced it

The same document-type-to-template decision is now made on `tb_report_template` itself:

- `report_group` is a fixed code from `FORM_REPORT_GROUPS` (`carmen-platform/src/constants/reportGroups.ts`): `PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP` — 12 codes, not the old module's 10 (gained `SI`, `SO`, `EOP`; lost `INV`; `RFQ` renamed `RFP`).
- `template_type = 'form'` marks a template as a single-record document layout (the old `kind = 'print'`); `template_type = 'list'` is the old `kind = 'report'` (tabular analytical reports). `kind` itself no longer exists as a column name — see [Report Templates — Data Model](/en/platform/report-templates/data-model) for the rename.
- `is_default` (new boolean column, described above) marks the one form template a business unit gets for a `report_group` when it has not chosen one — the exact role `tb_print_template_mapping.is_default` used to play, just moved one table over and with the plurality enforced by a real unique index instead of a Go best-effort demotion.
- The new **Form Groups** screen (`/report-form-groups`, `ReportFormGroupManagement.tsx`, sidebar entry in the "Content" group) replaces `PrintTemplateMappingManagement`'s grouped-card list: one card per `report_group`, listing every `template_type = 'form'` template in it, with a "Set as default" action per row (`reportTemplateService.setGroupDefault`) instead of a `is_default` checkbox on a separate mapping row.
- There is no BU-scoped equivalent of the old `allow_business_unit` / `deny_business_unit` mapping-row lists or the `resolve(document_type, bu_code)` endpoint. `tb_report_template` still carries its own `allow_business_unit` / `deny_business_unit` columns (BU visibility of the template row itself), but nothing in the new mechanism replicates the old per-BU "different default template per business unit" routing — this is a real capability gap versus the removed module, not something this pass can resolve; noted for Task 5.

`/report-form-groups` is not one of this book's 11 named Platform units and is not yet a wiki page of its own — see the Route gaps entry in the resync progress log.

## 3. Where the old content still applies

Nothing in this module's former business rules, permission keys, or schema is live. Do not cite `print_template_mapping.*` permission keys, the `/print-template-mapping*` routes, or `tb_print_template_mapping` in new pages — all three are gone. The sub-pages below are kept only as an archive of what the removed screens did, for anyone trying to understand a stale reference elsewhere in the codebase or docs.

## 4. Related Modules

- [Report Templates](/en/platform/report-templates) — owns the replacement mechanism (`report_group`, `is_default`, the Form Groups screen) and the `tb_report_template` table this module used to point at.
- [Platform RBAC](/en/platform/rbac) — the `print_template_mapping.*` keys this module used are no longer in the permission catalog at all (removed from the seed, not merely unassigned).
- [Business Units](/en/platform/business-units) — the removed module's allow/deny lists held BU codes; that per-mapping BU scoping has no replacement (see §2).

## 5. Reference Sources

- carmen-platform commit `de11377` — deletion of the SPA pages, routes, sidebar entry, and permission references.
- carmen-turborepo-backend-v2 commit `c135bb21e` — deletion of the backend-gateway proxy and permission-seed rows.
- carmen-turborepo-backend-v2 migration `packages/prisma-shared-schema-platform/prisma/migrations/20260723120000_print_form_default/migration.sql` — `is_default` added to `tb_report_template`, unique index, `DROP TABLE tb_print_template_mapping`.
- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx`, `../carmen-platform/src/constants/reportGroups.ts` — the replacement screen and the current `FORM_REPORT_GROUPS` list.
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_archived/2026-07-29/platform/print-template-mapping/` — the archived Bruno requests for the removed endpoints.

## 6. Pages in This Module

These sub-pages describe the removed screens as they existed through 2026-06-10 (last verified sync before removal). Each carries the same removal notice.

- [Data Model](/en/platform/print-template-mapping/data-model) — the former `tb_print_template_mapping` field table (now dropped).
- [UI Screens](/en/platform/print-template-mapping/ui-screens) — the former grouped-card list and view/edit-toggle form (now deleted).
- [Permissions](/en/platform/print-template-mapping/permissions) — the former `print_template_mapping.*` gate matrix and resolve-time BU rules (keys now removed from the catalog).
