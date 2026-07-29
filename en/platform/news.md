---
title: News
description: News module overview — markdown announcements with optional image, tags, a draft → published → archived lifecycle, global or per-BU targeting, and bulk publish/archive/delete — authored in the admin SPA and delivered through anonymous public endpoints.
published: true
date: 2026-07-29T00:00:00.000Z
tags: platform/news, carmen-software
editor: markdown
dateCreated: 2026-06-10T13:00:00.000Z
---

# News

The **News** module manages announcements and articles for platform users: a markdown body, an optional image, a source URL, freeform tags, and a `draft → published → archived` status lifecycle, targeted either globally or at an explicit list of business units. The Platform admin SPA is the **authoring side**; delivery to end users happens through a separate pair of **anonymous public endpoints** (`/api/public/news`) that expose only published, non-deleted articles whose publish time has arrived (no in-repo client consumes them yet — see §2).

> **At a Glance**
> **Module purpose:** Author and manage announcements — markdown `contents`, optional image (multipart upload → MinIO file token → presigned `image_url`), freeform tags, status lifecycle with server-stamped `published_at`, global vs per-BU targeting, bulk publish/archive/delete &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA, the backend-gateway news module, and the micro-cluster news service &nbsp;·&nbsp; **Key entities/tables:** `tb_news` (single table, JSONB `business_unit_ids` and `tags`, `doc_version` optimistic lock, no FK relations) &nbsp;·&nbsp; **Endpoints:** `/api/news` (authenticated CRUD — note `/api`, **not** `/api-system`), `/api/news/tags` (distinct tag list), and `/api/public/news` (anonymous read) &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The module follows the SPA's standard two-screen pattern:

- **`/news` → `NewsManagement`** — server-side `DataTable` with debounced search (title/contents), a Sheet-based Status + Tags filter, CSV export, checkbox row selection with bulk Publish/Archive/Delete, and persisted UI state in `localStorage`. Above the table sits a **`NewsroomSummary`** card: a Draft → Published → Archived pipeline strip plus a "Latest" lead-story tile (most recently published article, its cover thumbnail, and a relative "time ago"). Module-specific columns: an **image thumbnail**, a **Target** column (Global vs "N BUs"), a **Tags** column, and **Published**/**Updated** timestamp columns.
- **`/news/new` and `/news/:id/edit` → `NewsEdit`** — a masthead-and-two-column layout rather than the old four-card stack: a `NewsMasthead` card (cover image, status/reach/state badges, the headline itself) sits above an **Article** card (body markdown, source URL, tags) and a sticky **Publish** rail (status, BU targeting, published-at) plus a **History** card for existing records. A sticky bottom action bar carries Cancel/Save. Create mode is immediately editable; the edit route opens read-only behind an Edit toggle. Its signature elements are the **MarkdownEditor** (Write/Preview tabs), the **ImageUpload** drag-and-drop zone (now embedded in the masthead), and a **ChipInput** for tags with autocomplete.

A news record is one row in `tb_news`: `title` (required), `contents` (markdown), `url` (optional source link), an image stored as a MinIO **file token** (`image_file_token` — the API resolves it to a presigned `image_url` and never exposes the token), `tags` (a JSONB string array), `status`, `published_at`, `business_unit_ids` (a JSONB array; empty = visible to all business units), and `doc_version` (optimistic-lock counter). See [Data Model](/en/platform/news/data-model) for the full field table and [UI Screens](/en/platform/news/ui-screens) for the screen walkthrough.

Everything else is standard Management-page furniture: `TableSkeleton`, a filter-aware `ListEmptyState`, toast feedback, the `useUnsavedChanges` guard, global keyboard shortcuts (Ctrl/Cmd+S save, Escape cancel, Ctrl/Cmd+K search focus), and the dev-only Debug Sheet.

## 2. Business Context

News exists to communicate operational updates — policy changes, maintenance notices, hotel-group announcements — to the staff of one, several, or all business units. The module splits cleanly into two halves with different security models:

- **Authoring** (this SPA + `/api/news`): full CRUD, gated by RBAC `news.*` keys for the human and `AppIdGuard` grants for the calling application. Authors see every record regardless of status, including drafts and archived rows.
- **Delivery** (`/api/public/news` + `/api/public/news/:id`): **anonymous** — the controller carries no authentication guard at all. It serves only rows that are `status = published`, not soft-deleted, **and** `published_at <= now()`. With no `bu_id` query parameter only global news returns; with a `bu_id`, global news plus news targeting that BU. A draft, archived, deleted, or future-dated article answers 404 — the same response as an unknown id, so record existence never leaks.

The `published_at <= now()` filter means an author can **schedule** an article by publishing it with a future timestamp via the API (the SPA itself never sends `published_at` — see §3). No in-repo client renders the public feed yet: the Carmen Inventory web frontend has no news surface. Treat the public endpoints as the module's delivery contract.

## 3. Key Concepts

- **Status lifecycle** — `enum_news_status`: `draft` (default) → `published` → `archived`. The status select is free-form: any value can move to any other; nothing in the SPA or backend forbids un-publishing back to draft or resurrecting an archived row.
- **`published_at` is server-stamped, once.** On create with `status = published` and on the first transition into `published`, micro-cluster stamps `published_at = now()` — but only when the record has never carried a publish time. Moving back to draft or archived does **not** clear it, and re-publishing later keeps the *original* stamp. API callers may set or clear `published_at` explicitly; the SPA never sends the field and renders it read-only (helper text: Set automatically when status becomes "Published".).
- **Global vs BU targeting** — `business_unit_ids` is a JSONB array of BU UUIDs on the row itself, not a join table. Empty array (the column default) = global. The SPA models this as a "Visible to all business units" checkbox that, when unchecked, requires at least one BU in a multi-select. The backend validates every id against live `tb_business_unit` rows at write time, but stores them FK-free — see [Data Model](/en/platform/news/data-model) §3.
- **Tags** — `tags` is a JSONB string array, edited through a `ChipInput` (Enter/comma/Tab commits a chip; Backspace on an empty draft removes the last one) with autocomplete suggestions from `GET /api/news/tags` (distinct tags across all non-deleted news). Both the SPA and micro-cluster lowercase, trim, and de-duplicate entries; the backend additionally caps tags at 20 per article and 40 characters each, and splits any comma-containing element (defense against a stored tag corrupting the chip input's own comma delimiter). The list page's Tags column shows up to 3 badges plus a "+N" overflow, and the Filters Sheet grows a Tags group once any tag exists.
- **Optimistic locking (`doc_version`)** — every `PUT /api/news/:id` must include the `doc_version` the client last read; the backend rejects a missing version (`COMMON_DOC_VERSION_REQUIRED`) and rejects a stale one with a 409 conflict. The SPA's `getDocVersion`/`isVersionConflict` helpers surface this as "This record was changed by someone else", discard any pending image selection, and refetch the record — the same pattern used elsewhere in the Platform book (clusters, business units, users, applications, RBAC).
- **Markdown contents** — `contents` is a markdown string edited in Write/Preview tabs (`react-markdown` + `remark-gfm` for the preview). The backend stores it verbatim; rendering rules are each consumer's concern.
- **Image upload via multipart** — create/update accept `multipart/form-data` with the binary in an `image` field (under multipart, `business_unit_ids` and `tags` travel as JSON-encoded string fields). The gateway uploads the file to micro-file (MinIO), stores the returned token in `image_file_token`, and on every read swaps the token for a **presigned URL (1-hour expiry)** exposed as `image_url`. Replacing an image deletes the old file; deleting the news best-effort deletes its file. JSON (non-multipart) writes leave the image untouched — which also means the SPA offers **no way to remove an image without replacing it**.
- **Soft delete, and the admin list now filters it (confirmed fixed).** `DELETE /api/news/:id` sets `deleted_at`/`deleted_by_id`. The gateway's `EnrichAuditUsers` interceptor collapses the six flat audit columns into a nested `audit: { created, updated, deleted }` object. Unlike the state documented at the last sync, **the admin list query now merges `deleted_at: null` into its `where` clause** (micro-cluster's `findAll`, alongside the same fix on Applications and Business Units) — soft-deleted news no longer appears in `GET /api/news` at all. The SPA's client-side dual `deleted_at`/`audit.deleted.at` filter is now a defensive no-op rather than the only line of defense.
- **Bulk actions** — selecting one or more rows (checkbox column, shown to any session holding `news.update` or `news.delete`) reveals a **Publish Selected** / **Archive Selected** / **Delete Selected** toolbar. Each opens a confirm dialog that requires typing a random 6-character code before the action runs. There is no real bulk API: the SPA fires one `PUT` (publish/archive, carrying `doc_version`) or `DELETE` per selected row via `Promise.allSettled` and reports a combined success/partial-failure/failure toast.

## 4. Roles and Personas

Access is permission-gated through [Platform RBAC](/en/platform/rbac) (the four `news.*` keys are seeded in `seed.platform-permission.ts`), with route guards and in-page `<Can>` gates:

| Surface | Gate | Key |
|---|---|---|
| `/news` route + "News" sidebar entry (Content group, Newspaper icon) | `PrivateRoute` / sidebar filter | `news.read` |
| `/news/new` route | `PrivateRoute` | `news.create` |
| `/news/:id/edit` route | `PrivateRoute` | `news.update` |
| Add News button (list header) | `<Can>` | `news.create` |
| Row Edit (list actions dropdown) | `<Can>` | `news.update` |
| Row Delete (list actions dropdown) | `<Can>` | `news.delete` |
| Bulk Publish / Archive Selected | in-component (`canUpdate`) | `news.update` |
| Bulk Delete Selected | in-component (`canDelete`) | `news.delete` |
| Edit toggle (edit-page header) | `<Can>` | `news.update` |

As in Applications and Print Template Mapping, `news.delete` exists **only as an in-page gate** — no route requires it. A failed route guard now renders the dedicated `Forbidden` page (renamed from the old inline `AccessDenied`, still a 403 "Access Denied" heading, now with Go Back / Go to Dashboard actions) inside the normal `Layout` shell. Machine callers are gated separately by `AppIdGuard` keys (`news.findAll`, `news.findOne`, `news.create`, `news.update`, `news.delete` — the same key also guards `GET /api/news/tags`) — a different vocabulary from the RBAC keys. The full matrix, including an ungated empty-state CTA, is in [Permissions](/en/platform/news/permissions).

## 5. Related Modules

- [Business Units](/en/platform/business-units) — targeting references `tb_business_unit.id` values: validated as live BUs at write time, stored FK-free in JSONB. The targeting multi-select loads the full BU list from that module's API.
- [Broadcasts](/en/platform/broadcasts) — the **push** counterpart to News's **pull**: a broadcast pushes a notification to all users, chosen users, or one business unit (immediately or scheduled), while a news article sits in `tb_news` waiting to be fetched from the public feed. Use Broadcasts to interrupt, News to inform.
- [Platform RBAC](/en/platform/rbac) — defines and resolves the four `news.*` permission keys gating the SPA surfaces.
- [Applications](/en/platform/applications) — the `x-app-id` axis: every `/api/news` call must come from an application granted the corresponding `news.*` `api_name` (or `allow_all`). The anonymous `/api/public/news` controller checks neither tokens nor app ids.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — the three `news.*` route guards.
- `../carmen-platform/src/components/Layout.tsx` — "News" sidebar entry (Content group, `news.read`).
- `../carmen-platform/src/pages/NewsManagement.tsx`, `src/pages/newsManagement/NewsroomSummary.tsx` — list page: thumbnail/Target/Tags columns, status/tag filters, CSV export, bulk toolbar, `<Can>` gates.
- `../carmen-platform/src/pages/NewsEdit.tsx`, `src/pages/newsEdit/NewsMasthead.tsx` — masthead + two-column create/view/edit layout and validation.
- `../carmen-platform/src/services/newsService.ts` — REST client, multipart builder, `getTags`.
- `../carmen-platform/src/components/MarkdownEditor.tsx`, `ImageUpload.tsx`, `BusinessUnitMultiSelect.tsx`, `ui/chip-input.tsx`, `ReadOnlyField.tsx` — the module's form components.
- `../carmen-platform/src/utils/docVersion.ts` — `getDocVersion`/`isVersionConflict`/`notifyVersionConflict` optimistic-lock helpers.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_news` (line 812), `enum_news_status` (line 726).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/` — `news.controller.ts` (guards, multipart, `GET tags`), `news.service.ts` (file upload/rollback/cleanup), `news-image.helper.ts` (presigned `image_url`), `news-body.parser.ts`, `public-news.controller.ts` / `public-news.service.ts` (anonymous delivery).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` — persistence: BU validation, tag normalization, `published_at` stamping, the `doc_version` optimistic lock, soft-delete filtering, public visibility filters.
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/news/` — request/response contracts, including the `public/` pair and `GET-find-tags-master-data-news.bru`.

## 7. Pages in This Module

- [Data Model](/en/platform/news/data-model) — the `tb_news` field table (including `tags` and `doc_version`), the JSONB targeting column, `enum_news_status`, divergences against the SPA `News` type, and the endpoint table.
- [UI Screens](/en/platform/news/ui-screens) — the `NewsManagement` list (thumbnail, Target, Tags, `NewsroomSummary`, bulk toolbar) and the masthead-based `NewsEdit` form with markdown editor, image upload, tags, and BU targeting.
- [Permissions](/en/platform/news/permissions) — the `news.*` gate matrix, reader-side visibility rules on the public endpoints, and the edge-case matrix for testers.
