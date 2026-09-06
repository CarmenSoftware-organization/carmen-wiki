---
title: Report Form Groups
description: One card per fixed report_group code, each listing its form templates with a set-as-default action — the surface that replaced print-template-mapping.
published: true
date: '2026-09-06T23:45:00.000Z'
tags: book/platform, report-form-groups
editor: markdown
dateCreated: '2026-09-05T18:14:07.000Z'
---

# Report Form Groups

**Report Form Groups** is the screen where a Carmen-internal admin picks, per document type, which single-record **form** template a business unit gets by default when it hasn't chosen one explicitly. It shares its data and most of its permission model with [Report Templates](/en/platform/report-templates) — both surfaces edit the same `tb_report_template` rows — but it is its own top-level Platform module with its own route, its own sidebar entry, and its own feature-flag key.

> **At a Glance**
> **Component:** `ReportFormGroupManagement` &nbsp;·&nbsp; **Route:** `/report-form-groups`, gated by `<PrivateRoute requiredPermission="report_template.read" feature="report_form_groups">` (`../carmen-platform/src/App.tsx:322-329`) &nbsp;·&nbsp; **Nav:** "Form Groups" entry in the Content sidebar group — **same `report_template.read` permission as Report Templates**, a **different** `report_form_groups` feature key (`../carmen-platform/src/components/nav/platformNav.ts:25`) &nbsp;·&nbsp; **Added:** 2026-07-24 (`bf7a28a`), the same week `print-template-mapping` was removed from the product &nbsp;·&nbsp; **Data:** every `tb_report_template` row where `template_type = "form"`, grouped by `report_group` &nbsp;·&nbsp; **Since 2026-08-22:** each row shows a compact audit line (latest actor, created or updated) &nbsp;·&nbsp; **e2e suite:** **None** — confirmed no `report-form-groups` (or similarly named) directory in `../carmen-platform-e2e/tests/` (HEAD `a8e3b31`, 2026-08-25) &nbsp;·&nbsp; **Sub-pages:** 0

## 1. Overview

The permission-key sharing is worth naming plainly, because it is exactly the kind of thing a reader misreads: the `/report-form-groups` route and its sidebar row both carry `permission: 'report_template.read'` — the same key that gates [Report Templates](/en/platform/report-templates) itself — so anyone who can see one module can see the other, and a `report_template.*` grant is not scoped to "just the templates list" the way its name might suggest. What *does* separate the two modules independently is the **feature** key: `report_templates` gates Report Templates' three routes, while `report_form_groups` gates this module's route and nav row on its own — a feature-flag change to one has no effect on the other (§4).

The screen fetches every template with `template_type = "form"` and buckets them by `report_group`. It reuses `report_template.*` permissions end-to-end — there are no `report_form_group.*` or similar keys anywhere in the permission catalog.

## 2. Business Context

Until 2026-07-23, deciding which template rendered a given document type was the job of a separate module, `print-template-mapping`, with its own table (`tb_print_template_mapping`) and its own permission keys. That module was removed from the product across two days: the backend-gateway proxy and the `print_template_mapping.*` permission-catalog rows were dropped first, on 2026-07-23 (carmen-turborepo-backend-v2 commit `c135bb21e`), and the frontend pages followed the next day, 2026-07-24 (carmen-platform commit `de11377`). This module and [Report Templates](/en/platform/report-templates)' own `template_type` field are what replaced it — a documentation succession, not a product merge, and the two module pages should (and do, as of this migration) tell the same story.

The replacement was built in a short, traceable sequence, all in `../carmen-platform`:

- **2026-07-23** — schema migration `20260723120000_print_form_default` (full path in [Reference Sources](#7-reference-sources)) added `tb_report_template.is_default`, backfilled it from every `tb_print_template_mapping` row that was still active and not soft-deleted, created the partial unique index that enforces "at most one default per group" (§3.3), and dropped `tb_print_template_mapping`. The same migration renamed a `report_group` value from `RFQ` to `RFP`, as a no-op if an admin had already renamed it through the UI. The frontend side landed the same day: `cd4fc5d` ("add IA to form groups, expose the group default") added `IA` to the form-groups code list and surfaced `is_default` in `ReportTemplateEdit.tsx`.
- **2026-07-24** — `bf7a28a` added the `ReportFormGroupManagement` page itself; `ea699bc` added the `GroupCard` component (§3.2); `aa454d3` extracted the fixed code list out of `ReportTemplateEdit.tsx` into the shared `src/constants/reportGroups.ts` (§3.4); `2a73a4d` wired the per-card **Add** action to pre-fill a new template (§3.2). `b707b0a`, the same day, replaced an earlier `perpage: -1` "fetch everything" call with the paginated fetch described in §3.1 — the module's very first version already needed the fix.
- **2026-08-22** — `f62a90ec` added the compact per-row audit line (§3.2).

One capability did not carry over: **per-business-unit default scoping**. The removed module could route a different default template to different business units for the same document type; nothing in this screen's `is_default` mechanism replaces that — a group has exactly one default, platform-wide, or none.

## 3. Key Concepts

### 3.1 Fetching and Grouping

`fetchAll()` pages through `reportTemplateService.getAll()` in batches of 500 (`PAGE_SIZE`), sorted `name:asc`, filtered server-side to `template_type: 'form', deleted_at: null`. It keeps requesting subsequent pages until an empty page comes back, until the accumulated count reaches the server-reported `paginate.total`, or — only when no total is reported at all — until a page comes back shorter than 500. A `MAX_PAGES` constant (50) is a runaway guard, not a design limit reachable in normal use (50 × 500 = 25,000 form templates). This means the grouping below never silently operates on a partial fetch, at the cost of one full page always being requested even for a handful of templates. Search focus has its own shortcut: `useGlobalShortcuts({ onSearch: ... })` focuses the search box from the keyboard, the same convention other list pages in the SPA use.

Rows are bucketed by `t.report_group`, falling back to a literal `(none)` sentinel key for rows with no `report_group` set at all. Within a group, rows are sorted default-first, then by name (`sortRows`).

### 3.2 The Group Card

The header (`PageHeader`, title bound to the `nav.formGroups` i18n key, "Form Groups"; subtitle reading exactly `Manage the default form template for each report group`) carries a **New Form Template** button, gated `report_template.create`, that navigates to `/report-templates/new` with router state `{ template_type: 'form' }`. Below it, a filter bar holds a search box (matches group code or template name, case-insensitive) and an "Active only" checkbox that filters rows *within* each card — it never hides an otherwise-matching card outright.

The card grid (`GroupCard`, `../carmen-platform/src/pages/reportFormGroups/GroupCard.tsx`, two columns on large screens via `lg:grid-cols-2`) renders one card per group:

- the group code as a monospace outline badge, plus a template count — `"{n} template"` for exactly one, `"{n} templates"` otherwise (the catalog carries both forms; Thai uses one string for both, since Thai does not inflect for number);
- a per-card **Add** button, gated `report_template.create`, that navigates to create with state `{ template_type: 'form', report_group: <code> }` (omitted when the card is the `(none)` bucket);
- a warning banner reading exactly `No default set — pick one.` when the group has at least one template but none marked default;
- one row per template: a radio button (checked when `is_default`), the template name with a compact audit line underneath, an **Active/Inactive** status badge, a **Standard**/`Custom` type badge, an **Edit** link to `/report-templates/:id/edit`, and — gated `report_template.update` — a kebab menu with a single toggle action;
- an empty state, `No form templates` / `No form templates in {code} yet.`, when the card's row list (**after** the search/active-only filter is applied — see [Edge Cases](#5-edge-cases)) is empty.

Rows within a card are sorted default-first, then by name (§3.1); the default's radio and the surrounding "Default" framing are purely presentational — there is no separate "Default" column badge on this screen. That badge lives on the Report Templates list page instead, per [Report Templates](/en/platform/report-templates) §1. A dev-only `DevDebugSheet` (`title="Form Groups — raw"`) shows the raw **first-page-only** API response — the same `firstResponse` captured once in §3.1's paging loop, not the full aggregated list.

The audit line (added 2026-08-22, commit `f62a90ec54b72cde4fcbc9b77a17650b0e3c389b`) is rendered by `<AuditMeta variant="compact" verbKey={...} actor={...}>`, where `latestActor()` (`../carmen-platform/src/utils/audit.ts:101-108`) picks whichever of created/updated is more recent and returns an i18n **key** — `common.audit.created` ("Created") or `common.audit.updatedDate` ("Updated") — not a hardcoded string; the component composes it with the actor's relative time and name as `<verb> <relative> · <name>` (`AuditMeta.tsx:62-70`). This is a deliberate fix for a bug the source comments describe on `latestActor()` itself: an earlier version returned the literal English words, which produced mixed-language lines like "Updated 23 วันที่แล้ว" in the Thai UI once the relative-time part was translated but the verb was not.

The radio is disabled when `!canWrite || !t.is_active || busy` (`disableRadio`); its label carries a `title` tooltip whose text — read verbatim from the i18n catalog, `pages.reportFormGroups.activateFirstTitle` — is `Activate the template to make it the default`, shown only when the template is inactive. Clicking an un-checked, enabled radio calls `onRequestDefault`, opening the confirm dialog in §3.3.

The kebab menu's single item toggles Activate/Deactivate (gated `report_template.update`) and is disabled (`lockDeactivate = t.is_default && t.is_active`) whenever deactivating it would leave the group's current default inactive — the menu label then also gets a literal `" (default)"` suffix appended (`pages.reportFormGroups.defaultSuffix`), so a disabled "Deactivate (default)" item is visible, not hidden. An admin must reassign the group's default elsewhere before they can deactivate the template currently holding it.

### 3.3 Setting a Group Default

Clicking an un-checked, enabled radio opens a confirm dialog. Its text is built from two i18n templates and is quoted here exactly as they read in `../carmen-platform/src/i18n/en.ts` (`pages.reportFormGroups.setDefaultConfirm` / `.setDefaultReplaces`) — double quotes, not single:

> `Set "{name}" as the default for {code}?` — always shown — followed by `Replaces "{name}".` when a prior default exists.

The second `{name}` is the **current** default's name, not the target's; the two lines are two separate i18n strings concatenated in the component, not one template with two distinct placeholders.

Confirming calls `reportTemplateService.setGroupDefault({ current, target })` (`../carmen-platform/src/services/reportTemplateService.ts:81-99`), which is **two sequential, non-transactional** `PUT /api-system/report-templates/:id` calls: first `{ is_default: false }` on the current default (skipped entirely when there was none), then `{ is_default: true }` on the target — each carrying its own `doc_version` for the optimistic-lock check, and each a partial update (only the two fields sent are changed; the backend preserves everything else). The function also short-circuits (`if (current && current.id === target.id) return;`) if asked to replace a default with itself — in practice unreachable from this screen's own UI, since the caller (`requestDefault`) already excludes the target's own id when it looks up `current`; the guard is defensive, not load-bearing, for this call site. A `409` version conflict on either `PUT` triggers the shared `notifyVersionConflict()` toast and a re-fetch of the whole group list; any other failure shows a generic "Failed to set default" toast, also followed by a re-fetch so the UI reflects whatever state actually landed.

The database enforces the invariant this two-step flow is trying to maintain: `idx_report_template_default_per_group` is a partial unique index on `tb_report_template(report_group)` `WHERE is_default AND template_type = 'form' AND deleted_at IS NULL`, added by the same `20260723120000_print_form_default` migration described in §2. Because the two `PUT`s are not wrapped in one transaction, a narrow window exists between them where the group has **zero** defaults rather than exactly one. Whether a concurrent second admin's own default-set request in that same window fails cleanly (unique-violation surfaced as an error) or races unpredictably was not independently tested this pass — flagged as an edge case, not confirmed either way (§5).

Setting an **inactive** template as the new default via its radio is separately prevented, since `disableRadio` already covers `!t.is_active` (§3.2) — an admin must activate a template before it can become its group's default.

### 3.4 Fixed vs. Legacy Groups

The grid always renders the 12 codes in `FORM_REPORT_GROUPS` (`../carmen-platform/src/constants/reportGroups.ts:6-8`): `PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP`, in that fixed order, even when a code currently has zero form templates — so an admin always sees the complete, canonical list of document types needing a default, not just the ones already populated. Any `report_group` value present in the data but **not** in that fixed list (a "legacy" code, including the literal `(none)` bucket for rows with no group at all) still gets its own card, sorted alphabetically and appended after the 12 fixed ones — but only when it has at least one row left after the search/active-only filter; legacy codes with nothing left to show are not rendered as empty cards the way fixed codes are (§5).

## 4. Roles and Permissions

| Surface | Gate | Key(s) |
|---|---|---|
| `/report-form-groups` route | `requiredPermission` + `feature` | `report_template.read` + `report_form_groups` |
| Sidebar "Form Groups" entry | `permission` + `feature` filter (`platformNav.ts`) | `report_template.read` + `report_form_groups` |
| **New Form Template** header button | `hasPermission` (via `<Can>`) | `report_template.create` |
| Per-card **Add** button | `canCreate` prop, same check | `report_template.create` |
| Set-as-default radio, kebab menu | `canWrite` prop | `report_template.update` |

No new **permission** keys were introduced for this module — it is gated entirely by the same `report_template.*` catalog documented in full (route matrix, bootstrap exception, effective-access table) on [Report Templates — Permissions](/en/platform/report-templates/permissions). It carries its own **feature** key, though (`report_form_groups`, distinct from Report Templates' `report_templates`): a feature-flag change to one module does not affect the other. A session with only `report_template.read` can view every group and every template's current default, but sees no **New Form Template**/**Add** button, no kebab menu, and cannot select a different default radio — that radio renders disabled, not hidden.

## 5. Edge Cases

| Scenario | Behavior |
|---|---|
| A fixed group's remaining rows are all filtered out by "Active only" | The card still renders (fixed codes always render without a search query — §3.4), but shows the same `No form templates in {code} yet.` empty state as a group with genuinely zero templates. There is no distinct message for "everything here is just hidden by the filter." |
| A legacy group's remaining rows are all filtered out by "Active only" | The card **disappears entirely** — the legacy branch only renders a code when it has at least one row surviving the filter, with no separate all-filtered state. This is the one asymmetry between fixed and legacy codes beyond the ordering rule in §3.4. |
| A search term matches neither a fixed code nor any of its rows | That fixed card is the one case where a fixed group can vanish from view — every other fixed card stays visible regardless of the query. |
| Two admins race to set a default for the same group | The DB's partial unique index guarantees at most one default lands, but the two-step, non-transactional `PUT` pair (§3.3) means there is a real window with zero defaults; the exact failure shape for the losing request was not independently tested. |
| Setting a default on an inactive template | Prevented client-side: the radio is disabled while `!t.is_active`, with an explicit tooltip telling the admin to activate the template first. |
| Deactivating the group's current, active default | Prevented client-side: the kebab's Deactivate item is disabled (`lockDeactivate`) and visibly suffixed `(default)` until the admin reassigns the default elsewhere in the group. |

## 6. Related Modules

- [Report Templates](/en/platform/report-templates) — owns `tb_report_template`, the `template_type`/`is_default`/`report_group` columns this screen edits, and the Edit page every row's **Edit** link opens; also carries the full succession narrative from the module side.
- [Report Templates — Permissions](/en/platform/report-templates/permissions) — the full `report_template.*` gate matrix this screen reuses without modification.
- **Print Template Mapping** — the module this screen's job replaced, removed from the product across 2026-07-23/24 (§2). Its wiki page was deleted; the succession is now recorded on this page, on [Report Templates](/en/platform/report-templates), and on [Changelog](/en/platform/changelog) §6.

## 7. Reference Sources

- `../carmen-platform/src/pages/ReportFormGroupManagement.tsx` — the page: paged fetch, grouping, search/active filter, default-set and activate-toggle handlers.
- `../carmen-platform/src/pages/reportFormGroups/GroupCard.tsx` — per-group card: radio, compact audit line (`latestActor()` + `AuditMeta variant="compact"`), badges, Edit link, kebab menu, empty state, no-default warning.
- `../carmen-platform/src/constants/reportGroups.ts` — `FORM_REPORT_GROUPS`, the fixed 12-code canonical order.
- `../carmen-platform/src/services/reportTemplateService.ts:81-99` — `setGroupDefault` (the two sequential `PUT`s); `:66-69` `update`; `:49-54` `getAll`.
- `../carmen-platform/src/utils/docVersion.ts` — `getDocVersion`, `isVersionConflict`, `notifyVersionConflict`.
- `../carmen-platform/src/utils/audit.ts:101-108` — `latestActor()`; `../carmen-platform/src/components/AuditMeta.tsx:62-70` — the compact-variant render.
- `../carmen-platform/src/i18n/en.ts` (`reportFormGroups` block, "slice 6: Report Templates") — every UI string quoted on this page, read verbatim rather than paraphrased.
- `../carmen-platform/src/App.tsx:322-329` — the `/report-form-groups` route (`requiredPermission="report_template.read"`, `feature="report_form_groups"`); `../carmen-platform/src/components/nav/platformNav.ts:25` — the sidebar entry.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/migrations/20260723120000_print_form_default/migration.sql` — `is_default` column, backfill from `tb_print_template_mapping`, `idx_report_template_default_per_group` partial unique index, the `RFQ`→`RFP` rename, and the `DROP TABLE tb_print_template_mapping`.
- `../carmen-platform-e2e/tests/` — listed directly (HEAD `a8e3b31`, 2026-08-25) to confirm no `report-form-groups`/`form-groups` directory exists, and that `tests/report-templates/` (`report-template-crud.spec.ts`, `report-template-list.spec.ts`) does not cover this screen either.
- Commits: `de11377` (frontend removal, 2026-07-24), `c135bb21e` (backend removal, 2026-07-23, `../carmen-turborepo-backend-v2`), `cd4fc5d` (group default exposed + IA added, 2026-07-23), `bf7a28a` (page added, 2026-07-24), `ea699bc` (`GroupCard` added, 2026-07-24), `aa454d3` (`FORM_REPORT_GROUPS` extracted, 2026-07-24), `2a73a4d` (Add pre-fill, 2026-07-24), `b707b0a` (pagination fix, 2026-07-24), `f62a90ec54b72cde4fcbc9b77a17650b0e3c389b` (audit line, 2026-08-22) — all in `../carmen-platform` unless noted.

## 8. Pages in This Module

This module is a single page; see the parent [Platform book index](/en/platform).
