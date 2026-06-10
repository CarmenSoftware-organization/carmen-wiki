---
title: News — UI Screens
description: The NewsManagement list (thumbnail, Target, status filter, CSV export) and the four-card NewsEdit form — MarkdownEditor, ImageUpload, Publishing, and BU Targeting — with validation and keyboard shortcuts.
published: true
date: 2026-06-10T13:00:00.000Z
tags: book/platform, news, ui
editor: markdown
dateCreated: 2026-06-10T13:00:00.000Z
---

# News — UI Screens

> **At a Glance**
> **Screens:** `NewsManagement` (`/news`) · `NewsEdit` (`/news/new`, `/news/:id/edit`) &nbsp;·&nbsp; **Edit layout:** four cards — Content · Publishing · Targeting · Metadata (existing records only) &nbsp;·&nbsp; **Signature UI:** MarkdownEditor Write/Preview tabs · ImageUpload drag-and-drop · BU multi-select behind a "global" checkbox &nbsp;·&nbsp; **Persisted UI state:** 5 `localStorage` keys on the list page &nbsp;·&nbsp; **Shortcuts:** Ctrl/Cmd+S save · Escape cancel · Ctrl/Cmd+K focus search

## 1. Overview

News follows the SPA's standard two-screen Management/Edit pattern with one structural deviation on the edit side: instead of a single details card, `NewsEdit` stacks **four cards** (Content, Publishing, Targeting, Metadata) to separate the article body from its lifecycle and audience. The list page is the standard server-side `DataTable` with module-specific columns: an image **thumbnail**, a **Target** badge (Global vs N BUs), and Published/Updated timestamps.

Both screens ship the dev-only **Debug Sheet** (amber floating button, `import.meta.env.DEV` only) exposing the raw JSON of `GET /api/news` (list) or `GET /api/news/:id` (edit; absent in create mode). Both register the global keyboard shortcuts: on the list, Ctrl/Cmd+K focuses the search input; on the form, Ctrl/Cmd+S submits while editing and Escape cancels edit mode (view/edit route only, not create).

## 2. `NewsManagement` — list (`/news`)

### 2.1 Layout and header actions

Header: title "News Management" / subtitle "Manage announcements and news articles", with two actions — **Export** (client-side CSV of the loaded page: Title, Status, URL, Published; file `news-<YYYY-MM-DD>.csv`; disabled while loading or empty; *not* permission-gated) and **Add News** (navigates to `/news/new`; wrapped in `<Can permission="news.create">`).

### 2.2 Search and filters

A debounced (400 ms) search input over `title`/`contents` (server-side `search` param; yellow highlight while a term is active, inline clear button), plus a **Filters** Sheet with a single **Status** group — three toggle buttons (Draft / Published / Archived; filled when selected, multi-select) that translate to the `advance` query `{ where: { status: { in: [...] } } }`. Active selections render as removable chips under the search row with a "Clear all" link; the Filters button shows a count badge while any status is selected.

### 2.3 Columns

| Column | Rendering |
|---|---|
| (image) | Thumbnail of `image_url` (legacy `image` fallback): `h-10`, max 96 px wide, `object-contain` (aspect ratio preserved), rounded border; hides itself on load error. A muted `ImageIcon` placeholder box when no image |
| Title | Link to `/news/:id/edit`; `(untitled)` when blank |
| Status | Badge — `published` → success (green), `draft` (or missing) → secondary, `archived` → outline; label capitalized |
| Target | `business_unit_ids` non-empty → Building2 icon + "N BU(s)"; empty/absent → outline badge with Globe icon + "Global"; not sortable |
| Published | `published_at` as `YYYY-MM-DD HH:mm:ss` (browser-local), muted small text; `-` when never published |
| Updated | `audit.updated.at` timestamp with the actor name (`audit.updated.name`) on the next line; `-` when absent; not sortable |
| (actions) | `⋯` dropdown — see §2.4 |

Default sort is `published_at:desc` (and the column header is clickable) — but note the **server overrides every sort to `updated_at DESC`**; the sort UI currently has no effect on row order (see [Data Model](./data-model.md) §5). First load renders a 7-column `TableSkeleton`; subsequent loads overlay a "Loading news..." scrim.

The list also silently drops soft-deleted rows client-side (`deleted_at` or `audit.deleted.at`) because the endpoint returns them.

### 2.4 Row actions and delete dialog

The dropdown carries **Edit** (navigate to the edit route) wrapped in `<Can permission="news.update">` and **Delete** (destructive styling) wrapped in `<Can permission="news.delete">`. Delete opens a `ConfirmDialog` ("Delete News — Are you sure you want to delete this news article? This action cannot be undone."); confirming calls `DELETE /api/news/:id` (a soft delete server-side), toasts, and refetches the page. There is no delete affordance anywhere else in the module.

### 2.5 Empty state and persisted UI state

An empty result renders an `EmptyState` card (Newspaper icon, title "No news yet"); the description varies — `No news matching "<term>"` when a search term is active, or "Get started by creating your first news article." with an inline **Add News** CTA when none is. The CTA is **not** `<Can>`-wrapped (see [Permissions](./permissions.md) §2).

| `localStorage` key | Stored type | Persists |
|---|---|---|
| `search_news` | string | Search term |
| `filters_news` | JSON string array | Status filter selections |
| `page_news` | number string | Current page |
| `perpage_news` | number string | Page size |
| `sort_news` | string | Sort (`column:dir`, default `published_at:desc`) |

The edit page persists no UI state.

## 3. `NewsEdit` (`/news/new`, `/news/:id/edit`)

### 3.1 Modes

- **Create** (`/news/new`): title "Add News", all four cards immediately editable (Metadata absent — no audit yet). On submit: `POST /api/news`, toast, then redirect to `/news/:id/edit` for the created id (`replace: true`), falling back to the list when the response carries no id.
- **View** (`/news/:id/edit`, default): title "News Details", loaded via `GET /api/news/:id` (skeleton while in flight); every field read-only — markdown rendered, status as a badge, saved image as a small preview. The header carries a back arrow to `/news` and an **Edit** button wrapped in `<Can permission="news.update">`.
- **Edit** (after the toggle): title "Edit News". The toggle snapshots the form; **Cancel** restores the snapshot (also discarding any pending image selection) and exits edit mode. Unsaved changes — any form diff **or** a pending image file — arm the `useUnsavedChanges` navigation guard. On a successful update the page re-fetches and drops back to view mode.

### 3.2 Content card

| Field | Edit-mode control | Validation |
|---|---|---|
| Title * | Text input | Required — checked on blur and pre-submit ("Title is required") |
| Content (Markdown) | `MarkdownEditor` — **Write** tab (monospace textarea, ≥200 px, placeholder "Write your news content in Markdown...") and **Preview** tab (`react-markdown` + `remark-gfm`: GFM tables, lists, code, blockquotes) | None — optional |
| Source URL | URL input | When non-empty: "Must be a valid http(s) URL" (blur + pre-submit) |
| Image | `ImageUpload` (§3.3) | Client-side type/size checks |

In view mode the markdown renders read-only in a muted box (`-` when empty).

### 3.3 The ImageUpload component

A dashed drop zone ("Drag & drop an image here, or *browse*") doubling as a click/keyboard-activated file picker. Client-side validation toasts on rejection: accepted types JPEG/PNG/WebP/GIF, ≤5 MB. A selected file shows a local object-URL preview (64 px tall, aspect preserved) with a **Remove** button that clears only the *pending selection* — the saved image cannot be removed, only replaced (see [Permissions](./permissions.md) §4). In view mode the component renders just the saved presigned-URL preview, or nothing.

Two server-side caveats QA should know: the backend additionally rejects **GIF** (`image/gif` passes the picker but returns 400 `BAD_FILE_TYPE`) and images over **2048×2048 px** (400 `BAD_DIMENSIONS`) — both surface as a "Failed to save news" form error, not as an upload-time toast.

### 3.4 Publishing card

- **Status** — native select with Draft / Published / Archived (free transition in any direction); renders as the colored badge in view mode.
- **Published At** — always read-only, with helper text "Set automatically by the server when status becomes 'Published'." The SPA never sends the field; the server stamps it on first publish and keeps it thereafter ([Data Model](./data-model.md) §2.2).

### 3.5 Targeting card

- **"Visible to all business units (global)"** checkbox — checked by default on create. While checked, no BU control renders and the save payload sends `business_unit_ids: []`.
- Unchecked reveals **Business Units**: a `BusinessUnitMultiSelect` that loads the full BU list once (`perpage: -1`, sorted by name), offers a name/code search box over a checkbox list, and renders selections as removable badges above it.
- Pre-submit validation: not global + zero BUs → "Select at least one business unit, or enable \"Visible to all business units\"." Re-checking the global box clears the error.

### 3.6 Metadata card (existing records only)

Rendered when the loaded record carries an `audit` object: **Created** and **Last Updated**, each `YYYY-MM-DD HH:mm:ss` plus `by <name>` when the enriched audit includes the actor.

### 3.7 Save flow

Save (`Create News` / `Save Changes`, spinner while saving) submits `{ title, contents?, url?, status, business_unit_ids }`. With a pending image file the service switches to `multipart/form-data` — binary `image` field, `business_unit_ids` JSON-encoded as a string, and an explicit multipart `Content-Type` (required: the axios instance defaults to JSON, which would serialize the `FormData` away). Without a file it sends plain JSON, leaving any saved image untouched. API field errors from `parseApiError` map back onto the form fields; after a successful update the SPA re-fetches the record (the `PUT` response carries only `{ id, image_url }`).

## 4. References

- `../carmen-platform/src/pages/NewsManagement.tsx` — columns, status-filter Sheet, CSV export, `<Can>` gates, client-side soft-delete filter, persisted keys.
- `../carmen-platform/src/pages/NewsEdit.tsx` — four-card form, mode toggle, validation, save payload, shortcuts.
- `../carmen-platform/src/components/MarkdownEditor.tsx` — Write/Preview tabs, GFM preview, read-only rendering.
- `../carmen-platform/src/components/ImageUpload.tsx` — drop zone, accept list, 5 MB cap, local preview/remove semantics.
- `../carmen-platform/src/components/BusinessUnitMultiSelect.tsx` — BU loading, search, badge selection.
- `../carmen-platform/src/services/newsService.ts` — `buildNewsFormData`, the multipart `Content-Type` note, envelope walking.
- `../carmen-platform/src/components/KeyboardShortcuts.tsx` — Ctrl/Cmd+S, Ctrl/Cmd+K, Escape bindings.

**Cross-links:** [News landing](/en/platform/news) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
