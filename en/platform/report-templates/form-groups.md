---
title: Report Templates — Form Groups
description: The /report-form-groups screen (added 2026-07-24) that replaced print-template-mapping's grouped-card list — one card per fixed report_group code, with a "set as default" action on tb_report_template.is_default.
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, report-templates, form-groups
editor: markdown
dateCreated: 2026-07-29T09:46:00.000Z
---

# Report Templates — Form Groups

> **At a Glance**
> **Screen:** `ReportFormGroupManagement` (`/report-form-groups`, added 2026-07-24) &nbsp;·&nbsp; **Route gate:** `report_template.read` (reused — no new permission keys) **and** `feature="report_form_groups"` — its own feature key, separate from Report Templates' `report_templates` &nbsp;·&nbsp; **Sidebar:** "Form Groups" entry in the Content group (`platformNav.ts`) &nbsp;·&nbsp; **Replaces:** [print-template-mapping](/en/platform/print-template-mapping)'s grouped-card list, removed the same week &nbsp;·&nbsp; **Data:** every `tb_report_template` row where `template_type = "form"`, grouped by `report_group` &nbsp;·&nbsp; **Since 2026-08-22:** each row shows a compact audit line (latest actor, created or updated)

## 1. Overview

Form Groups is the screen where an admin picks, per document type, which single-record **form** template a business unit gets by default when it hasn't chosen one explicitly. It replaced the [print-template-mapping](/en/platform/print-template-mapping) module's own grouped-card list in the same 2026-07-23/24 change that dropped `tb_print_template_mapping` and added `tb_report_template.is_default` — see that page for the full removal timeline and [Report Templates](/en/platform/report-templates) §1/§3 for the `template_type`/`is_default` column pair this screen edits. This page documents the screen itself; it was previously covered only in prose on the parent [Report Templates](/en/platform/report-templates) landing page and the [print-template-mapping](/en/platform/print-template-mapping) historical page.

The screen fetches **every** template with `template_type = "form"` (paging through in batches of 500 until the server's reported total is reached, so the grouping never silently operates on a partial fetch) and buckets them by `report_group`. It reuses `report_template.*` permissions end-to-end — there are no `report_form_group.*` or similar keys anywhere in the permission catalog.

## 2. Screen Layout

- **Header** — `PageHeader` titled "Form Groups", subtitle "Manage the default form template for each report group"; a **New Form Template** button (gated `report_template.create`) that navigates to `/report-templates/new` pre-filled with `template_type: "form"`.
- **Filter bar** — a search box (matches group code or template name) and an "Active only" checkbox that filters rows within each group card (never hides an otherwise-matching card entirely).
- **Group cards grid** (2-column on large screens) — one `GroupCard` per report group. Each card shows:
  - the group code as a monospace outline badge, plus a template count ("N templates");
  - an **Add** button (gated `report_template.create`) that pre-fills `report_group` alongside `template_type: "form"` when navigating to create;
  - a warning banner ("No default set — pick one.") when the group has at least one template but none marked default;
  - one row per template: a radio button (checked = current default), the template name with a compact audit line underneath (**added 2026-08-22**, commit `f62a90ec54b72cde4fcbc9b77a17650b0e3c389b`) — `latestActor(t)` picks whichever of created/updated is most recent and `<AuditMeta variant="compact">` renders it as "Created `<relative>` · `<name>`" or "Updated `<relative>` · `<name>`" — an **Active/Inactive** badge, a **Standard/Custom** badge, an **Edit** link to `/report-templates/:id/edit`, and — gated `report_template.update` — a kebab menu with a single **Activate**/**Deactivate** action;
  - an empty state ("No form templates" / "No form templates in {code} yet.") when the group (after filtering) has no rows.
- Rows within a card are sorted default-first, then by name; the default's radio and the "Default" framing are purely presentational — there is no separate "Default" column badge on this screen (that badge lives on the Report Templates list page instead, per [Report Templates](/en/platform/report-templates) §1).
- A dev-only `DevDebugSheet` shows the raw first-page API response.

## 3. Setting a Group Default

Clicking an un-checked radio opens a confirm dialog ("Set '{name}' as the default for {code}? Replaces '{old name}'." when a prior default exists). Confirming calls `reportTemplateService.setGroupDefault({ current, target })`, which is **two sequential, non-transactional `PUT /api-system/report-templates/:id` calls** — first `{ is_default: false }` on the current default (skipped entirely if there was none), then `{ is_default: true }` on the target — each carrying its own `doc_version` for the optimistic-lock check. A `409` version conflict on either call triggers the shared `notifyVersionConflict()` toast and a re-fetch of the whole group list; any other failure shows a generic "Failed to set default" toast, also followed by a re-fetch so the UI reflects whatever state actually landed.

The database enforces the invariant this two-step flow is trying to maintain: `idx_report_template_default_per_group` is a partial unique index on `tb_report_template(report_group)` `WHERE is_default AND template_type = 'form' AND deleted_at IS NULL` (added by the same `20260723120000_print_form_default` migration that dropped `tb_print_template_mapping` — see [print-template-mapping](/en/platform/print-template-mapping) §1). Because the two `PUT`s are not wrapped in one transaction, a narrow window exists between them where the group has **zero** defaults rather than exactly one; whether a concurrent second admin's own default-set request in that same window fails cleanly (unique-violation) or races unpredictably was not independently tested this pass — flagged as an edge case, not confirmed either way.

The **Activate/Deactivate** kebab action is a separate, single `PUT` (`{ is_active: !t.is_active }` plus `doc_version`) and carries its own client-side lock: deactivating the group's current default while it is still active is disabled in the menu item (`lockDeactivate = t.is_default && t.is_active`) — an admin must reassign the default elsewhere in the group before they can deactivate the template that currently holds it. Setting an **inactive** template as the new default via its radio is separately disabled (`disableRadio = !canWrite || !t.is_active || busy`), with a tooltip ("Activate the template to make it the default") on the radio's label — an admin must activate a template before it can become the group's default.

## 4. Fixed vs. Legacy Groups

The card grid always renders the 12 codes in `FORM_REPORT_GROUPS` (`carmen-platform/src/constants/reportGroups.ts`: `PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP`) in that fixed order, even when a code currently has zero form templates — so an admin always sees the complete, canonical list of document types needing a default, not just the ones already populated. Any `report_group` value present in the data but **not** in that fixed list (a "legacy" code) still gets its own card, sorted alphabetically and appended after the 12 fixed ones, but only when it has at least one visible row — legacy codes with nothing to show are not rendered as empty cards the way fixed codes are. Under an active search term, a fixed-code card is kept only if the code itself matches the query or it still has matching rows; this is the one case where a fixed group can disappear from view.

## 5. Roles and Personas

| Surface | Gate | Key |
|---|---|---|
| `/report-form-groups` route | `requiredPermission` + `feature` | `report_template.read` + `report_form_groups` |
| Sidebar "Form Groups" entry | `permission` + `feature` filter (`platformNav.ts`) | `report_template.read` + `report_form_groups` |
| **New Form Template** button | `hasPermission` | `report_template.create` |
| Per-card **Add** button | `canCreate` prop (same check) | `report_template.create` |
| Set-as-default radio, kebab menu | `canWrite` prop | `report_template.update` |

No new **permission** keys were introduced for this screen — it is gated entirely by the same `report_template.*` catalog documented in full (route matrix, bootstrap exception, effective-access table) on [Report Templates — Permissions](/en/platform/report-templates/permissions). It does carry its own **feature** key, though (`report_form_groups`, distinct from Report Templates' `report_templates`) — a feature-flag change to one module does not affect the other. A session with only `report_template.read` can view every group and every template's current default, but sees no Add button, no kebab menu, and cannot select a different default radio (rendered disabled rather than hidden).

## 6. Related Modules

- [Report Templates](/en/platform/report-templates) — owns `tb_report_template`, the `template_type`/`is_default`/`report_group` columns this screen edits, and the Edit page every row's **Edit** link opens.
- [Report Templates — Permissions](/en/platform/report-templates/permissions) — the full `report_template.*` gate matrix this screen reuses without modification.
- [print-template-mapping](/en/platform/print-template-mapping) — the removed module this screen's job replaced; its landing page documents the full 2026-07-23/24 removal timeline and the one capability (per-BU default scoping) that did not carry over.

## 7. Reference Sources

- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx` — the page: paged fetch, grouping, search/active filter, default-set and activate-toggle handlers.
- `../carmen-platform/src/pages/reportFormGroups/GroupCard.tsx` — per-group card: radio, compact audit line (`latestActor()` + `AuditMeta variant="compact"`, added 2026-08-22), badges, Edit link, kebab menu, empty state, no-default warning.
- `../carmen-platform/src/constants/reportGroups.ts` — `FORM_REPORT_GROUPS`, the fixed 12-code canonical order.
- `../carmen-platform/src/services/reportTemplateService.ts` — `setGroupDefault` (the two sequential `PUT`s), `getAll`, `update`.
- `../carmen-platform/src/utils/docVersion.ts` — `getDocVersion`, `isVersionConflict`, `notifyVersionConflict`.
- `../carmen-platform/src/utils/audit.ts` — `latestActor()`.
- **Stale citation fixed:** `../carmen-platform/src/App.tsx:323-329` — the `/report-form-groups` route (`requiredPermission="report_template.read"`, `feature="report_form_groups"`); `../carmen-platform/src/components/nav/platformNav.ts:25` — the sidebar entry (not `Layout.tsx`, which defines no nav rows today).
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260723120000_print_form_default/migration.sql` — `is_default` column, `idx_report_template_default_per_group` partial unique index.

## 8. Pages in This Module

This is a sub-page of [Report Templates](/en/platform/report-templates) — see that landing page's §7 for the complete sub-page list.
