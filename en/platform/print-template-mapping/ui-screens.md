---
title: Print Template Mapping — UI Screens
description: Historical record — PrintTemplateMappingManagement and PrintTemplateMappingEdit were deleted from carmen-platform on 2026-07-24 (commit de11377); use Report Templates' Form Groups screen instead.
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, print-template-mapping, ui
editor: markdown
dateCreated: 2026-06-10T12:45:00.000Z
---

# Print Template Mapping — UI Screens

> **Implementation status (verified 2026-07-29): both screens described below have been deleted.** `PrintTemplateMappingManagement.tsx`, `PrintTemplateMappingEdit.tsx`, and `printTemplateMappingService.ts` were removed from carmen-platform in commit `de11377` ("remove the print template mapping pages", 2026-07-24), along with the three routes, the sidebar entry, and the breadcrumb entry. Nothing at `/print-template-mapping*` renders in the current SPA — the path hits the `*` catch-all `NotFound` page. This page documents the screens as they existed through 2026-06-10, for historical reference. The current equivalent is the **Form Groups** screen (`/report-form-groups`, `ReportFormGroupManagement.tsx`) inside the Report Templates module — see [Report Templates — UI Screens](/en/platform/report-templates/ui-screens).

## 1. Overview (historical)

The list page (`/print-template-mapping`) was a deliberate deviation from the SPA's standard Management pattern: one card containing a bordered sub-table per document type, rather than a server-side `DataTable`. The edit page (`/print-template-mapping/new`, `/print-template-mapping/:id/edit`) was a conventional single-card view/edit-toggle form whose signature element was a Report Template select that floated `kind="print"` + matching `report_group` templates to the top.

## 2. `PrintTemplateMappingManagement` — list (former)

A single Card: Printer icon, title "Print Template Mapping", one action ("New Mapping", gated `print_template_mapping.create`). Filters were inline (Document Type select + "Active only" checkbox, no Sheet panel, no free-text search). Rows were grouped client-side by `document_type`, each group a bordered block (Template / Display Label / Default / Order / Active / row actions). Row actions were two inline ghost icon buttons (Edit, Delete) rather than the standard `⋯` dropdown. The list had no `localStorage`-persisted state and no client-side pagination — the Go endpoint defaulted to `perpage = 10` and the page rendered only what arrived, silently truncating beyond 10 live mappings.

## 3. `PrintTemplateMappingEdit` — create/view/edit (former)

Create mode defaulted to `is_default = true`, `display_order = 0`, `is_active = true`. View mode rendered every field read-only with a `<Can permission="print_template_mapping.update">`-gated Edit button. Edit mode exposed Document Type, Report Template, Display Label, Display Order, Allow/Deny Business Units (CSV text inputs), a Default checkbox, and an Active checkbox. The Report Template select loaded up to 500 templates and floated `kind === 'print' && report_group === document_type` matches to the top as a soft sort, not a hard filter.

## 4. What replaced these screens

The **Form Groups** screen (`/report-form-groups`) now covers the "pick the default template per document type" job: one card per `report_group` (from the fixed `FORM_REPORT_GROUPS` list), listing every `template_type = 'form'` template in that group with a "Set as default" action (`reportTemplateService.setGroupDefault`) instead of an `is_default` checkbox on a separate mapping-row form. There is no grouped multi-document-type overview screen, no Display Label / Display Order fields, and no per-mapping BU allow/deny scoping in the replacement — see [Report Templates — UI Screens](/en/platform/report-templates/ui-screens) for what the new screen actually does.

## 5. References

- carmen-platform commit `de11377` — the deletion.
- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx` — the current replacement screen.

**Cross-links:** [Print Template Mapping landing](/en/platform/print-template-mapping) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Report Templates — UI Screens](../report-templates/ui-screens.md)
