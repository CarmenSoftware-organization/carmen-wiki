---
title: Report Templates — Form Groups
description: The /report-form-groups screen now has its own top-level module — this page covers only what remains specific to Report Templates, the shared tb_report_template columns and the Add/Edit hand-off between the two screens.
published: true
date: 2026-09-06T21:00:00.000Z
tags: book/platform, report-templates, form-groups
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Report Templates — Form Groups

> **Moved:** the `/report-form-groups` screen (`ReportFormGroupManagement`, its own route, sidebar entry, and `report_form_groups` feature key) is documented in full at **[Report Form Groups](/en/platform/report-form-groups)** — layout, the group-default flow, fixed vs. legacy groups, roles, and edge cases. This page now covers only the one relationship that is genuinely Report-Templates-specific: the shared `tb_report_template` columns and the Add/Edit hand-off between the two screens.

## 1. What Report Form Groups Edits on This Module's Table

Report Form Groups edits exactly three columns this module owns on `tb_report_template`: `template_type` (constrained to `"form"` for anything shown there), `report_group` (constrained by the SPA to the fixed 12-code list documented at [Report Form Groups](/en/platform/report-form-groups) §3.4), and `is_default` (the group-default flag, set through that screen's own two-step, non-transactional `PUT` pair — its §3.3). Every other field on the row — the XML payloads, data-source binding, BU scope, `is_standard`/`is_active` — is edited only here, on this module's own Edit page; Report Form Groups has no edit surface of its own.

Both screens' Add/Edit actions land in the same place. Report Form Groups' **New Form Template** header button and each card's **Add** button navigate to `/report-templates/new` — this module's own create route — pre-filled with `template_type: 'form'` (a card's **Add** additionally pre-fills that card's `report_group`). Every row's **Edit** link on that screen opens `/report-templates/:id/edit`, this module's own edit page. Report Form Groups is a curated, grouped view over rows this module's Edit page fully owns, not a parallel authoring surface.

The two screens also share a permission key worth restating from this side: `/report-templates` and `/report-form-groups` both gate on `report_template.read` (see [Permissions](/en/platform/report-templates/permissions) §7) — a grant here is a grant there too. What separates them independently is the **feature** key: `report_templates` for this module, `report_form_groups` for the other.

## 2. References

- [Report Form Groups](/en/platform/report-form-groups) — the full screen documentation.
- [Report Templates](/en/platform/report-templates) §3 — this module's own `template_type`/`report_group`/`is_default` field definitions.
- [Permissions](/en/platform/report-templates/permissions) — the full `report_template.*` gate matrix both screens share.
- `../carmen-platform/src/pages/ReportTemplateEdit.tsx` — the shared Edit page both screens' Add/Edit actions open.
