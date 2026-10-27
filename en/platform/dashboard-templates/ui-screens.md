---
title: Dashboard Templates — UI Screens
description: The Dashboard Templates page tab by tab - System and BU default widget lists, the add/edit widget dialog, reorder arrows, and the Deploy tab with its overwrite confirmation.
published: true
date: 2026-10-27T00:00:00.000Z
tags: book/platform, dashboard-templates, ui-screens
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# Dashboard Templates — UI Screens

> **At a Glance**
> **Screens:** 1 page, 3 tabs (System, BU default, Deploy) &nbsp;·&nbsp; **Edit layout:** modal dialog, no edit route &nbsp;·&nbsp; **Dialogs:** `TemplateEditDialog`, delete `ConfirmDialog`, `OverwriteConfirmDialog` &nbsp;·&nbsp; **Access:** `dashboard_template.read`; Deploy tab needs `.deploy` &nbsp;·&nbsp; **Persisted UI state:** active tab in the URL only

## 1. Overview

`DashboardTemplateManagement` at `/dashboard-templates` renders a `PageHeader` and a `TabStrip`. The selected tab is kept in the query string (`?tab=`), written with `replace` so switching tabs does not add history entries. System and BU default render the same component with a `kind` prop; `key={tab}` remounts it on switch, so module selection resets. There is no search, pagination or sort control: a module has a handful of widgets and ordering is the feature.

## 2. `TemplateListPanel` (System and BU default tabs)

### 2.1 Layout

A card with a toolbar and a table. Toolbar, left to right: **Module** select (System: the seven modules, default Procurement; BU default: **Main** plus the seven, default Main), a **version badge** (BU default tab only, "Version N", read from `GET /bu-default/version` after every load), and the **Thai coverage** badge ("Thai titles done/total", counting titled rows that also have a Thai title; amber until all do). **Add widget** sits on the right.

The table:

| Column | Notes |
|---|---|
| Title | Title in the UI language (falls back to the other language, then to the dataset name labelled "(Dataset name)"). Second line shows the other language with an `en`/`th` tag, or the italic "No Thai title" hint. |
| Dataset | Dataset name (from the catalog) over the `dataset_id` in monospace; red "Dataset no longer exists" badge when the catalog loaded and does not contain it. |
| Type | Icon plus `widget_type`. |
| Scope | **System tab only.** "All business units", or "Only N business unit(s)" / "Hidden from N" with the BU codes in a tooltip. |
| Status | Active / Inactive badge; inactive rows are greyed. |
| (actions) | Move up, move down, edit, delete. |

Loading uses `TableSkeleton`; empty uses `ListEmptyState`. Only the latest request writes state, so quick module switches never show a stale answer.

### 2.2 Row actions

| Action | Permission | Behaviour |
|---|---|---|
| Move up / down | `dashboard_template.update` | `PATCH /reorder` with the whole module renumbered 10, 20, 30...; disabled at the first/last row and while busy |
| Edit | `dashboard_template.update` | Opens `TemplateEditDialog` |
| Delete | `dashboard_template.delete` | Confirm dialog, then `DELETE /:id` |

The delete confirm is titled "Delete widget" and says business units that already received the template keep their copy until the next deploy.

## 3. `TemplateEditDialog`: create mode

Opened by Add widget. Context (kind, module) comes from the panel, so it is not editable here. New widgets get `order_index` = current max + 10. Fields:

| Field | Control | Notes |
|---|---|---|
| Dataset | select, sorted by category then name, labelled `name · shape` | required; changing it resets widget type and params |
| Widget type | select of the dataset's `supported_renders` | disabled until a dataset is chosen; required |
| Title (EN) / Title (TH) | text, max 255 | TH without EN is blocked client-side |
| Dataset parameters | `DatasetParamFields`: select when the param has `options`, number input when `type = number`, otherwise text; required marked with `*` | blank values are dropped instead of sent as `''` |
| Allow BUs / Deny BUs | `BusinessUnitMultiSelect` keyed by BU **code** | System kind only |
| Active | checkbox | default on |

Save needs a dataset and a widget type. `POST /api-system/dashboard-templates` with `kind`, wire `module` (`main` becomes `null`) and `order_index`.

## 4. `TemplateEditDialog`: edit mode

Same dialog preloaded from the row. `kind` and `module` are not editable (the dialog sends neither). `PATCH /:id` carries `doc_version` when the row has one; version conflicts show the shared toast, close and reload. Other errors render inline ("Could not save: ...") including the backend's 422 messages for an unknown dataset or an incompatible widget type. Title is sent as both `title` and `title_i18n`. `display` is never sent.

## 5. `DeployPanel` (Deploy tab)

Hidden and non-renderable without `dashboard_template.deploy` (the component returns `null` if the check fails).

### 5.1 Layout

Hint text with the current version, an alert when the active BU-default set is empty, then a toolbar: **Refresh status**, **Select outdated** (selects BUs whose status is `outdated` or `never`), a **mode** radio pair (Skip customized / Overwrite), and **Deploy (N)** which becomes a red **Stop** while running. Below, a table of every business unit sorted by code.

| Column | Content |
|---|---|
| (checkbox) | per-row and select-all |
| Business unit | `code - name` |
| Deploy status | Badge: `current` (green), `outdated` (amber), `customized` (grey), `never` (outline), `unknown` before the first check (outline), `error` (red); spinner while checking/deploying; per-row result line ("Deployed N widget(s)", a skipped note, or the error) |
| Deployed version | `deployed_version` or a dash |
| Deployed at / Customized at | locale-formatted date-time, dash when null |

On mount the panel loads all BUs (`fetchAllBusinessUnits`), then the version and the active-widget count, then checks every BU's status with concurrency 4.

### 5.2 Overwrite confirmation

Choosing Overwrite and pressing Deploy opens `OverwriteConfirmDialog`: red title, a line saying how many selected BUs changed their dashboard by hand (their changes will be replaced), and an input that must read `OVERWRITE` (typing is upper-cased). The confirm button repeats "Deploy (N)". Skip customized mode deploys without a confirmation.

## 6. Persisted UI state

| Where | What | Persists |
|---|---|---|
| URL query | `tab` (`system`, `bu_default`, `deploy`) | Until navigation |
| `localStorage` | nothing written by this page | n/a |

Module selection, selection checkboxes and deploy mode reset on tab switch or reload.

## 7. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References

- `../carmen-backstage/src/pages/DashboardTemplateManagement.tsx`, `src/pages/dashboardTemplates/{TemplateListPanel,TemplateEditDialog,DeployPanel,OverwriteConfirmDialog,DatasetParamFields}.tsx`, `modules.ts`, `reorderItems.ts`, `deployRowState.ts`.
- i18n: `pages.dashboardTemplates.*`.
- Siblings: [Dashboard Templates](/en/platform/dashboard-templates), [Lifecycle](/en/platform/dashboard-templates/lifecycle).
