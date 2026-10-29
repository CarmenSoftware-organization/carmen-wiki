---
title: AI Providers — UI Screens
description: Walkthrough of the AI Providers list and its create/edit dialog - columns, responsive behaviour, the form sections, validation hints, delete confirmation and what is not persisted.
published: true
date: 2026-10-29T03:30:00.000Z
tags: book/backstage, ai-providers, ui-screens
editor: markdown
dateCreated: 2026-10-27T00:00:00.000Z
---

# AI Providers — UI Screens

> **At a Glance**
> **Screens:** 1 list page + 1 dialog (create and edit share it) + 1 delete confirm &nbsp;·&nbsp; **Edit layout:** single scrolling dialog, four sections &nbsp;·&nbsp; **Dialogs:** `AiProviderEditDialog`, `ConfirmDialog` &nbsp;·&nbsp; **Access:** `ai_provider.read` to see; create/update/delete per button &nbsp;·&nbsp; **Persisted UI state:** none

## 1. Overview

The module is one page, `AiProviderManagement` at `/purchase-request-ai-providers`, wrapped in the usual `Layout` + `PageHeader`. There is **no search box, no filter panel, no pagination and no sort control**: the catalog is small, always loaded in full and ordered by `sort_order`. Creating and editing happen in `AiProviderEditDialog`; there are no `/new` or `/:id/edit` routes. Page title is `nav.aiProviders` ("Purchase Request AI Providers"), subtitle "Changes apply to every business unit."

## 2. `AiProviderManagement` (`/purchase-request-ai-providers`)

### 2.1 Layout

A single `Card` with a table (`TableSkeleton` while the first load runs; `ListEmptyState` "No AI providers yet" when empty). Columns, with the breakpoint at which each appears:

| Column | Shown | Content |
|---|---|---|
| Provider | always | 36px icon tile (`icon_url` image, else built-in `ProviderIconMark` by `icon_key`), `label`, and the `code` in monospace (below `md`, the link's hostname is shown instead). Inactive rows render at 50% opacity. |
| Opens | `md`+ | Hostname of `url_template` (the `{query}` token is swapped for `q` to parse it) and a hint: "Prompt pre-filled" (template contains `{query}`) or "Prompt copied to paste". |
| Default prompt | `lg`+ | Character count; second line says "Shared with N more" when other providers have an identical prompt, else "Unique to this provider". Hover shows the full prompt as a tooltip. |
| Status | always | `Active` / `Inactive` badge; below `md` it also shows the BU default as a second line. |
| Business units | `md`+ | Badge "On by default" or "Opt-in" (from `default_enabled_for_bu`). |
| Order | `md`+ | `sort_order`, right-aligned. |
| (actions) | always | Edit and Delete icon buttons. |

### 2.2 Header actions

"Add provider" opens the dialog in create mode. Rendered only for `ai_provider.create`.

### 2.3 Row actions

Edit (pencil) opens the dialog with the row; Delete (trash) opens the confirm dialog. Gated by `ai_provider.update` and `ai_provider.delete` respectively. Both are disabled while a reload is running.

### 2.4 Delete confirmation

`ConfirmDialog` "Delete this AI provider?" with text "The provider disappears from every business unit. Per-BU settings are kept but ignored." On confirm: `DELETE /api-system/ai-providers/:id`, success toast, list reloads. A failure shows an error toast with the server detail.

## 3. `AiProviderEditDialog`: create mode

Opened by "Add provider". `code` is editable here and only here. Initial values: empty text fields, no built-in icon, `is_active` ON, `default_enabled_for_bu` OFF, `sort_order` = current maximum + 10 (so a new provider lands last). `POST /api-system/ai-providers` with the fields plus `code`; success toast "created", dialog closes, list reloads.

## 4. `AiProviderEditDialog`: edit mode

Same dialog with the row loaded. `code` is disabled. `PATCH /api-system/ai-providers/:id` sends the editable fields plus the row's `doc_version`; on a version conflict the dialog shows the shared conflict toast, closes and reloads. Any other failure appears as an inline red alert at the top of the dialog ("Could not save: ...").

The dialog header shows a live icon preview (the `icon_url` if it starts with `https://`, otherwise the built-in mark). Sections:

### 4.1 Provider (identity)

| Field | Control | Notes |
|---|---|---|
| Name (`label`) | text, max 100 | required |
| Code | text, max 50, monospace | create only; red border + message when it does not match `^[a-z0-9][a-z0-9_-]{1,49}$`; hint "a-z, 0-9, _ or -, 2 to 50 characters. Cannot be changed after creation." |
| Built-in icon | select: None + `claude`, `chatgpt`, `gemini`, `deepseek`, `grok`, `google` (each with its mark) | |
| Icon URL | text, placeholder `https://` | hint "https only. When set, it is shown instead of the built-in icon." Not validated client-side beyond the header preview. |

### 4.2 Where it opens (link)

`url_template`, monospace, placeholder `https://example.com/search?q={query}`. Below it a **Preview** line shows the template with `{query}` replaced by the URL-encoded text `sample prompt`.

### 4.3 Default prompt

Monospace textarea (8 rows) with a live `length/4000` counter that turns red over the limit. Hint explains the `{items}` token.

### 4.4 Availability

Two ON/OFF toggle buttons (rendered as badges with `role="switch"`, because the repo has no switch component): **Active** (hint "Inactive providers are hidden in every business unit.") and **On by default for business units** (hint "Applies to business units that have not chosen for themselves."), then a numeric **Sort order** input.

**Save is enabled only when:** not already saving, `code` valid (always true in edit), `label`, `url_template` and `prompt` non-blank, prompt length at most 4000, and `sort_order` is a non-negative integer.

## 5. Persisted UI state

None. The page writes no `localStorage` keys, and the dialog resets every field each time it opens.

## 6. Screenshots

> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 7. References

- `../carmen-backstage/src/pages/AiProviderManagement.tsx` (list), `src/pages/aiProviders/AiProviderEditDialog.tsx` (dialog; `CODE_RE`, `ICON_KEYS`, `PROMPT_MAX` at the top), `src/services/aiProviderService.ts`.
- i18n keys: `pages.aiProviders.*` in `src/i18n/en.ts`.
- Siblings: [AI Providers](/en/backstage/ai-providers), [Data Model](/en/backstage/ai-providers/data-model).
