---
title: News — UI Screens
description: The NewsroomSummary masthead + NewsManagement list (thumbnail, Target, Tags, status/tag filters, CSV export, bulk publish/archive/delete) and the masthead-based NewsEdit form — MarkdownEditor, ImageUpload, Tags, Publish rail — with validation and keyboard shortcuts.
published: true
date: 2026-07-29T03:00:00.000Z
tags: book/platform, news, ui
editor: markdown
dateCreated: 2026-06-10T13:00:00.000Z
---

# News — UI Screens

> **At a Glance**
> **Screens:** `NewsManagement` (`/news`) · `NewsEdit` (`/news/new`, `/news/:id/edit`) &nbsp;·&nbsp; **List extras:** `NewsroomSummary` pipeline + lead-story card, checkbox row selection, bulk Publish/Archive/Delete &nbsp;·&nbsp; **Edit layout:** `NewsMasthead` (cover/status/reach/title) + Article card (body, URL, tags) + sticky Publish rail + History card &nbsp;·&nbsp; **Signature UI:** MarkdownEditor Write/Preview tabs · ImageUpload drag-and-drop (now inside the masthead) · ChipInput tags with autocomplete · BU multi-select behind a "global" checkbox &nbsp;·&nbsp; **Persisted UI state:** 6 `localStorage` keys on the list page &nbsp;·&nbsp; **Shortcuts:** Ctrl/Cmd+S save · Escape cancel · Ctrl/Cmd+K focus search

## 1. Overview

News follows the SPA's standard two-screen Management/Edit pattern with structural deviations on both sides. The list page adds a `NewsroomSummary` masthead above the table — a Draft → Published → Archived pipeline strip plus a "Latest" tile for the most recently published article — and supports checkbox row selection for bulk Publish/Archive/Delete. The edit side replaces the earlier four-card stack with a `NewsMasthead` (cover, status/reach/state badges, the headline) over an **Article** card and a sticky **Publish** rail, to separate the article body from its lifecycle and audience.

Both screens ship the dev-only **Debug Sheet** (amber floating button, `import.meta.env.DEV` only) exposing the raw JSON of `GET /api/news` (list) or `GET /api/news/:id` (edit; absent in create mode). Both register the global keyboard shortcuts: on the list, Ctrl/Cmd+K focuses the search input; on the form, Ctrl/Cmd+S submits while editing and Escape cancels edit mode (view/edit route only, not create).

## 2. `NewsManagement` — list (`/news`)

### 2.1 Layout and header actions

Header (`PageHeader`): title "News Management" / subtitle "Manage announcements and news articles", with two actions — **Export** (client-side CSV of the loaded page: Title, Status, URL, Published; file `news-<YYYY-MM-DD>.csv`; disabled while loading or empty; *not* permission-gated) and **Add News** (navigates to `/news/new`; wrapped in `<Can permission="news.create">`).

### 2.2 `NewsroomSummary`

A card rendered between the header and the table, built from a *separate* unfiltered fetch (`perpage: -1`, ignoring the active search/status/tag filters — the masthead always reflects the whole desk) via `summarizeNews`:

- **Latest** — the most recently *published* article (by `published_at`): its cover thumbnail (or a placeholder), title (linking to its edit page), a relative "Published `<time ago>`" label (`timeAgo`: "just now" / "N min/hour(s) ago" / "yesterday" / "N days/weeks ago" / an absolute date beyond 5 weeks), and its reach (Global or "N BUs"). When nothing is published yet, a "Nothing published yet" placeholder shows instead.
- **Pipeline** — three stage counters (Draft / Published / Archived, chevron-separated) plus a "N articles total" caption. Counts exclude soft-deleted rows.
- Loading renders skeleton placeholders; a fetch failure swaps the whole card for an inline error with a **Retry** button (`FetchErrorState`) — the table below still works independently.

### 2.3 Search and filters

A debounced (400 ms) search input over `title`/`contents` (server-side `search` param; yellow highlight while a term is active, inline clear button), plus a **Filters** Sheet with two groups:

- **Status** — three toggle buttons (Draft / Published / Archived; filled when selected, multi-select).
- **Tags** — one toggle button per distinct tag in use (fetched once via `GET /api/news/tags`); the group only renders once at least one tag exists anywhere.

Both groups translate into the `advance` query as `{ where: { status: { in: [...] }, OR: [{ tags: { array_contains: [tag] } }, ...] } }`. Active selections render as removable chips under the search row with a "Clear all" link; the Filters button shows a count badge (0, 1, or 2 — one per group with an active selection, not per chip).

### 2.4 Columns

| Column | Rendering |
|---|---|
| (selection) | Checkbox, shown only when the session holds `news.update` or `news.delete`; `getRowSelectionLabel` announces "Select `<title>`" |
| (image) | Thumbnail of `image_url` (legacy `image` fallback): `h-10`, max 96 px wide, `object-contain` (aspect ratio preserved), rounded border; hides itself on load error. A muted `ImageIcon` placeholder box when no image |
| Title | Link to `/news/:id/edit`; `(untitled)` when blank |
| Status | Badge — `published` → success (green), `draft` (or missing) → secondary, `archived` → outline; label capitalized |
| Target | `business_unit_ids` non-empty → Building2 icon + "N BU(s)"; empty/absent → outline badge with Globe icon + "Global"; not sortable |
| Tags | Up to 3 `Badge` chips plus a "+N" overflow count; `-` when empty; not sortable |
| Published | `published_at` as `YYYY-MM-DD HH:mm:ss` (browser-local), muted small text; `-` when never published |
| Updated | `audit.updated.at` timestamp with the actor name (`audit.updated.name`) on the next line; `-` when absent; not sortable |
| (actions) | `⋯` dropdown — see §2.6 |

Default sort is `published_at:desc` (and the column header is clickable) — but note the **server overrides every sort to `updated_at DESC`**; the sort UI currently has no effect on row order (see [Data Model](./data-model.md) §5). The leftmost 2–3 columns (selection + image, plus Title when selection is enabled) stay sticky while scrolling horizontally. First load renders a `TableSkeleton` sized to the current column count; subsequent loads overlay a "Loading news..." scrim.

Because the admin list query now filters `deleted_at: null` server-side (§ [Data Model](./data-model.md) §5), the list no longer needs to hide soft-deleted rows — the SPA's client-side `deleted_at`/`audit.deleted.at` filter in `newsService.getAll` is now a defensive no-op.

### 2.5 Bulk selection toolbar

Selecting one or more rows reveals a toolbar above the table: "N selected", **Publish Selected** and **Archive Selected** (both gated on `news.update`), **Delete Selected** (gated on `news.delete`, destructive styling), and a **Clear** link. Selection is scoped to the current page and is cleared automatically whenever the result set changes (page, page size, search, sort, or filters), so it can never hold rows that scroll out of view.

Each action opens a shared bulk dialog (title/description/icon vary by action — Send/Archive/Trash2) listing the selected titles and requiring the user to type a random 6-character confirmation code (regenerated per open) before the button enables. Confirming fires one request **per selected row** via `Promise.allSettled` — `PUT` with `{ status: 'published' | 'archived', doc_version }` for Publish/Archive, `DELETE` for Delete — and reports a combined toast: full success ("`<Verb>` N news article(s)"), full failure, or a "N succeeded, M failed" warning. There is no dedicated bulk API endpoint.

### 2.6 Row actions and delete dialog

The dropdown carries **Edit** (navigate to the edit route) wrapped in `<Can permission="news.update">` and **Delete** (destructive styling) wrapped in `<Can permission="news.delete">`. Delete opens a `ConfirmDialog` ("Delete News — Are you sure you want to delete this news article? This action cannot be undone."); confirming calls `DELETE /api/news/:id` (a soft delete server-side), toasts, and refetches the page (and reloads the `NewsroomSummary`). There is no other single-row delete affordance.

### 2.7 Empty state and persisted UI state

An empty result renders a filter-aware `ListEmptyState` (`Newspaper` icon): when neither a search term nor any filter is active it shows "No news yet" / "Get started by creating your first news article." with an inline **Add News** CTA (not `<Can>`-wrapped — see [Permissions](./permissions.md) §2); otherwise it shows the shared "No matches found" copy regardless of which filter is responsible.

| `localStorage` key | Stored type | Persists |
|---|---|---|
| `search_news` | string | Search term |
| `filters_news` | JSON string array | Status filter selections |
| `tagfilters_news` | JSON string array | Tag filter selections |
| `page_news` | number string | Current page |
| `perpage_news` | number string | Page size |
| `sort_news` | string | Sort (`column:dir`, default `published_at:desc`) |

The edit page persists no UI state.

## 3. `NewsEdit` (`/news/new`, `/news/:id/edit`)

### 3.1 Modes

A back link ("← News", to `/news`) sits above the form in every mode. The form itself is `NewsMasthead` (§3.2) followed by a two-column grid: an **Article** card on the left, a sticky **Publish** rail (plus a **History** card) on the right.

- **Create** (`/news/new`): title "Add News" via the masthead's title editor; both cards immediately editable (no History card — no audit yet). On submit: `POST /api/news`, toast, then redirect to `/news/:id/edit` for the created id (`replace: true`), falling back to the list when the response carries no id.
- **View** (`/news/:id/edit`, default): loaded via `GET /api/news/:id` (skeleton while in flight); every field read-only — markdown rendered, status as a masthead badge, saved image as the masthead's banner. The masthead's `actions` slot carries an **Edit** button wrapped in `<Can permission="news.update">`.
- **Edit** (after the toggle): the toggle snapshots the form; **Cancel** restores the snapshot (also discarding any pending image selection) and exits edit mode. Unsaved changes — any form diff **or** a pending image file — arm the `useUnsavedChanges` navigation guard and show an "Unsaved changes" indicator in the sticky action bar (§3.7). On a successful update the page re-fetches and drops back to view mode.

### 3.2 `NewsMasthead`

A card combining what used to be scattered across separate cards:

- **Cover** — in edit mode, the `ImageUpload` control (see §3.4) rendered inline; in view mode, the saved image as a `h-40`–`h-48` banner (hides itself on load error), or a muted placeholder box (`Newspaper` icon) when there is none.
- **Eyebrow row** — a status `Badge` (success/secondary/outline per §3.5), a reach indicator (Globe "Global" or Building2 "N business unit(s)"), and a trailing state note: the formatted `published_at` once published, "Hidden from readers" when archived, or "Not visible to readers" while draft.
- **Title** — the headline itself: an `<h1>` in view mode, or the title `<input>` (required, inline validation) in edit mode.
- **Actions** — the Edit button (view mode, existing records only).

### 3.3 Article card

| Field | Edit-mode control | Validation |
|---|---|---|
| Body (Markdown) | `MarkdownEditor` — **Write** tab (monospace textarea, ≥200 px, placeholder "Write your news content in Markdown...") and **Preview** tab (`react-markdown` + `remark-gfm`: GFM tables, lists, code, blockquotes) | None — optional |
| Source URL | URL input; `ReadOnlyField` in view mode | When non-empty: "Must be a valid http(s) URL" (blur + pre-submit) |
| Tags | `ChipInput` (§3.4a), disabled outside edit mode | None client-side beyond the chip commit rules; server enforces ≤20 tags, ≤40 chars each |

In view mode the markdown renders read-only in a muted box.

### 3.4 The `ImageUpload` component

A dashed drop zone ("Drag & drop an image here, or *browse*") doubling as a click/keyboard-activated file picker, now rendered inside the masthead's cover slot rather than its own card. Client-side validation toasts on rejection: accepted types JPEG/PNG/WebP/GIF, ≤5 MB. A selected file shows a local object-URL preview with a **Remove** button that clears only the *pending selection* — the saved image cannot be removed, only replaced (see [Permissions](./permissions.md) §4).

Two server-side caveats QA should know: the backend additionally rejects **GIF** (`image/gif` passes the picker but returns 400 `BAD_FILE_TYPE`) and images over **2048×2048 px** (400 `BAD_DIMENSIONS`) — both surface as a "Failed to save news" form error, not as an upload-time toast. A discarded pending image (Cancel, a successful save, or a `doc_version` conflict) bumps an `imageResetSignal` so the control's internal preview can never go stale.

### 3.4a The `ChipInput` component (tags)

A generic chip/tag input (`components/ui/chip-input.tsx`) reused for News tags: typed text commits to a chip on Enter, comma, or Tab; Backspace on an empty draft removes the last chip; an optional `suggestions` list (here, `GET /api/news/tags`, filtered to exclude already-picked tags) renders as a datalist. Values round-trip as a single comma-joined string internally; `NewsEdit` lowercases, trims, and de-duplicates on every change before storing the array. Tag suggestions are fetched only in create mode or while editing an existing record.

### 3.5 Publish rail

- **Status** — native select with Draft / Published / Archived (free transition in any direction); renders as the masthead's colored badge in view mode.
- **Targeting** — the **"Visible to all business units"** checkbox (checked by default on create); unchecked reveals a `BusinessUnitMultiSelect` (loads the full BU list once, `perpage: -1`, sorted by name, with a name/code search box and removable badge selections). Pre-submit validation: not global + zero BUs → "Select at least one business unit, or enable \"Visible to all business units\"."; re-checking the global box clears the error.
- **Published At** — always a `ReadOnlyField`, with helper text: Set automatically when status becomes "Published". The SPA never sends the field; the server stamps it on first publish and keeps it thereafter ([Data Model](./data-model.md) §2.2).

### 3.6 History card (existing records only)

Rendered when the loaded record carries an `audit` object: **Created** and **Last updated**, each `YYYY-MM-DD HH:mm:ss` plus `by <name>` when the enriched audit includes the actor. Sits below the Publish rail, sticky alongside it on desktop.

### 3.7 Save flow

A sticky bottom bar (visible only while editing) shows an "Unsaved changes" dot indicator (or "No changes") plus **Cancel** and **Save** (`Create News` / `Save Changes`, spinner while saving, disabled when nothing changed on an existing record). Save submits `{ title, contents?, url?, status, business_unit_ids, tags, doc_version? }`. With a pending image file the service switches to `multipart/form-data` — binary `image` field, `business_unit_ids` and `tags` JSON-encoded as string fields, and an explicit multipart `Content-Type` (required: the axios instance defaults to JSON, which would serialize the `FormData` away). Without a file it sends plain JSON, leaving any saved image untouched.

A stale `doc_version` on update returns a 409; the SPA shows "This record was changed by someone else", discards any pending image selection, and refetches the record instead of surfacing a generic save error. Other API field errors from `parseApiError` map back onto the form fields; after a successful update the SPA re-fetches the record (the `PUT` response carries only `{ id, doc_version }` — see [Data Model](./data-model.md) §6). The Debug Sheet's floating button shifts up (`bottom-20`) while editing so it doesn't collide with the sticky action bar.

## 4. References

- `../carmen-platform/src/pages/NewsManagement.tsx`, `src/pages/newsManagement/NewsroomSummary.tsx` — columns, status/tag filter Sheet, CSV export, bulk toolbar + dialog, `<Can>` gates, persisted keys.
- `../carmen-platform/src/pages/NewsEdit.tsx`, `src/pages/newsEdit/NewsMasthead.tsx` — masthead + two-column form, mode toggle, validation, save payload, shortcuts.
- `../carmen-platform/src/components/MarkdownEditor.tsx` — Write/Preview tabs, GFM preview, read-only rendering.
- `../carmen-platform/src/components/ImageUpload.tsx` — drop zone, accept list, 5 MB cap, local preview/remove semantics.
- `../carmen-platform/src/components/ui/chip-input.tsx` — tag chip parsing/joining, suggestion filtering, keyboard commit rules.
- `../carmen-platform/src/components/BusinessUnitMultiSelect.tsx` — BU loading, search, badge selection.
- `../carmen-platform/src/components/ReadOnlyField.tsx` — the shared read-only field renderer used across the redesigned edit pages.
- `../carmen-platform/src/services/newsService.ts` — `buildNewsFormData`, `getTags`, the multipart `Content-Type` note, envelope walking.
- `../carmen-platform/src/utils/docVersion.ts` — optimistic-lock helpers.
- `../carmen-platform/src/components/KeyboardShortcuts.tsx` — Ctrl/Cmd+S, Ctrl/Cmd+K, Escape bindings.

**Cross-links:** [News landing](/en/platform/news) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
