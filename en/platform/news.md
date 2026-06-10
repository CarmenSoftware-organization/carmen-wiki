---
title: News
description: News module overview — markdown announcements with optional image, a draft → published → archived lifecycle, and global or per-BU targeting, authored in the admin SPA and delivered through anonymous public endpoints.
published: true
date: 2026-06-10T13:00:00.000Z
tags: platform/news, carmen-software
editor: markdown
dateCreated: 2026-06-10T13:00:00.000Z
---

# News

The **News** module manages announcements and articles for platform users: a markdown body, an optional image, a source URL, and a `draft → published → archived` status lifecycle, targeted either globally or at an explicit list of business units. The Platform admin SPA is the **authoring side**; delivery to end users happens through a separate pair of **anonymous public endpoints** (`/api/public/news`) that expose only published, non-deleted articles whose publish time has arrived (no in-repo client consumes them yet — see §2).

> **At a Glance**
> **Module purpose:** Author and manage announcements — markdown `contents`, optional image (multipart upload → MinIO file token → presigned `image_url`), status lifecycle with server-stamped `published_at`, global vs per-BU targeting &nbsp;·&nbsp; **Audience:** Developers and QA working on the Platform admin SPA, the backend-gateway news module, and the micro-cluster news service &nbsp;·&nbsp; **Key entities/tables:** `tb_news` (single table, JSONB `business_unit_ids`, no FK relations) &nbsp;·&nbsp; **Endpoints:** `/api/news` (authenticated CRUD — note `/api`, **not** `/api-system`) and `/api/public/news` (anonymous read) &nbsp;·&nbsp; **Sub-pages:** 3

## 1. Overview

The module follows the SPA's standard two-screen pattern:

- **`/news` → `NewsManagement`** — server-side `DataTable` with debounced search (title/contents), a Sheet-based status filter (Draft/Published/Archived), CSV export, and persisted UI state in `localStorage`. Module-specific columns: an **image thumbnail** (aspect-ratio-preserving, ≤96 px wide, placeholder icon when absent), a **Target** column rendering a "Global" badge or an "N BUs" count, and **Published**/**Updated** timestamp columns.
- **`/news/new` and `/news/:id/edit` → `NewsEdit`** — a four-card form (Content, Publishing, Targeting, Metadata) rather than the usual single card. Create mode is immediately editable; the edit route opens read-only behind an Edit toggle. Its signature elements are the **MarkdownEditor** (Write/Preview tabs) and the **ImageUpload** drag-and-drop zone.

A news record is one row in `tb_news`: `title` (required), `contents` (markdown), `url` (optional source link), an image stored as a MinIO **file token** (`image_file_token` — the API resolves it to a presigned `image_url` and never exposes the token), `status`, `published_at`, and `business_unit_ids` (a JSONB array; empty = visible to all business units). See [Data Model](/en/platform/news/data-model) for the full field table and [UI Screens](/en/platform/news/ui-screens) for the screen walkthrough.

Everything else is standard Management-page furniture: `TableSkeleton`, `EmptyState`, toast feedback, the `useUnsavedChanges` guard, global keyboard shortcuts (Ctrl/Cmd+S save, Escape cancel, Ctrl/Cmd+K search focus), and the dev-only Debug Sheet.

## 2. Business Context

News exists to communicate operational updates — policy changes, maintenance notices, hotel-group announcements — to the staff of one, several, or all business units. The module splits cleanly into two halves with different security models:

- **Authoring** (this SPA + `/api/news`): full CRUD, gated by RBAC `news.*` keys for the human and `AppIdGuard` grants for the calling application. Authors see every record regardless of status, including drafts and archived rows.
- **Delivery** (`/api/public/news` + `/api/public/news/:id`): **anonymous** — the controller carries no authentication guard at all. It serves only rows that are `status = published`, not soft-deleted, **and** `published_at <= now()`. With no `bu_id` query parameter only global news returns; with a `bu_id`, global news plus news targeting that BU. A draft, archived, deleted, or future-dated article answers 404 — the same response as an unknown id, so record existence never leaks.

The `published_at <= now()` filter means an author can **schedule** an article by publishing it with a future timestamp via the API (the SPA itself never sends `published_at` — see §3). As of 2026-06-10 **no in-repo client renders the public feed yet**: the Carmen Inventory web frontend has no news surface, and the mobile app's home-screen `NewsCarousel` (`carmen-inventory-mobile/src/components/ui/news-carousel.tsx`) is the obvious future consumer but currently renders hard-coded translation strings, not the API. Treat the public endpoints as the module's delivery contract.

## 3. Key Concepts

- **Status lifecycle** — `enum_news_status`: `draft` (default) → `published` → `archived`. The status select is free-form: any value can move to any other; nothing in the SPA or backend forbids un-publishing back to draft or resurrecting an archived row.
- **`published_at` is server-stamped, once.** On create with `status = published` and on the first transition into `published`, micro-cluster stamps `published_at = now()` — but only when the record has never carried a publish time. Moving back to draft or archived does **not** clear it, and re-publishing later keeps the *original* stamp. API callers may set or clear `published_at` explicitly; the SPA never sends the field and renders it read-only ("Set automatically by the server when status becomes 'Published'.").
- **Global vs BU targeting** — `business_unit_ids` is a JSONB array of BU UUIDs on the row itself, not a join table. Empty array (the column default) = global. The SPA models this as a "Visible to all business units (global)" checkbox that, when unchecked, requires at least one BU in a multi-select. The backend validates every id against live `tb_business_unit` rows at write time, but stores them FK-free — see [Data Model](/en/platform/news/data-model) §3.
- **Markdown contents** — `contents` is a markdown string edited in Write/Preview tabs (`react-markdown` + `remark-gfm` for the preview). The backend stores it verbatim; rendering rules are each consumer's concern.
- **Image upload via multipart** — create/update accept `multipart/form-data` with the binary in an `image` field (under multipart, `business_unit_ids` travels as a JSON-encoded string field). The gateway uploads the file to micro-file (MinIO), stores the returned token in `image_file_token`, and on every read swaps the token for a **presigned URL (1-hour expiry)** exposed as `image_url`. Replacing an image deletes the old file; deleting the news best-effort deletes its file. JSON (non-multipart) writes leave the image untouched — which also means the SPA offers **no way to remove an image without replacing it**.
- **Soft delete via nested audit** — `DELETE /api/news/:id` sets `deleted_at`/`deleted_by_id`. The gateway's `EnrichAuditUsers` interceptor collapses the six flat audit columns into a nested `audit: { created, updated, deleted }` object (each `{ at, id, name, avatar }`) and removes the flat fields. The admin **list endpoint does not filter soft-deleted rows** — the SPA hides them client-side by checking both `deleted_at` and `audit.deleted.at` (the dual check covers enrichment-failure fallbacks and older payloads).

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
| Edit toggle (edit-page header) | `<Can>` | `news.update` |

As in Applications and Print Template Mapping, `news.delete` exists **only as an in-page gate** — no route requires it and the edit page has no delete action; deletion happens exclusively from the list row dropdown. The edit page's Save button is unwrapped but unreachable without the gated Edit toggle. Machine callers are gated separately by `AppIdGuard` keys (`news.findAll`, `news.findOne`, `news.create`, `news.update`, `news.delete`) — a different vocabulary from the RBAC keys. The full matrix, including an ungated empty-state CTA, is in [Permissions](/en/platform/news/permissions).

## 5. Related Modules

- [Business Units](/en/platform/business-units) — targeting references `tb_business_unit.id` values: validated as live BUs at write time, stored FK-free in JSONB. The targeting multi-select loads the full BU list from that module's API.
- **Broadcasts** (SPA route `/broadcasts/new`, sidebar "Send Broadcast", `broadcast.send`; not yet a page in this book) — the **push** counterpart to News's **pull**: a broadcast fans out notification rows to users (optionally scheduled), while a news article sits in `tb_news` waiting to be fetched from the public feed. Use Broadcasts to interrupt, News to inform.
- [Platform RBAC](/en/platform/rbac) — defines and resolves the four `news.*` permission keys gating the SPA surfaces.
- [Applications](/en/platform/applications) — the `x-app-id` axis: every `/api/news` call must come from an application granted the corresponding `news.*` `api_name` (or `allow_all`). The anonymous `/api/public/news` controller checks neither tokens nor app ids.

## 6. Reference Sources

- `../carmen-platform/src/App.tsx` — the three `news.*` route guards.
- `../carmen-platform/src/components/Layout.tsx` — "News" sidebar entry (Content group, `news.read`).
- `../carmen-platform/src/pages/NewsManagement.tsx` — list page: thumbnail/Target columns, status filter, CSV export, `<Can>` gates.
- `../carmen-platform/src/pages/NewsEdit.tsx` — four-card create/view/edit form and validation.
- `../carmen-platform/src/services/newsService.ts` — REST client, multipart builder, client-side soft-delete filtering.
- `../carmen-platform/src/components/MarkdownEditor.tsx`, `ImageUpload.tsx`, `BusinessUnitMultiSelect.tsx` — the module's three form components.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_news` (line 803), `enum_news_status` (line 693).
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/` — `news.controller.ts` (guards, multipart), `news.service.ts` (file upload/rollback/cleanup), `news-image.helper.ts` (presigned `image_url`), `news-body.parser.ts`, `public-news.controller.ts` / `public-news.service.ts` (anonymous delivery).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` — persistence: BU validation, `published_at` stamping, soft delete, public visibility filters.
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/news/` — request/response contracts, including the `public/` pair.

## 7. Pages in This Module

- [Data Model](/en/platform/news/data-model) — the `tb_news` field table, the JSONB targeting column, `enum_news_status`, divergences against the SPA `News` type (token vs presigned URL, nested audit, soft-delete dual detection), and the endpoint table.
- [UI Screens](/en/platform/news/ui-screens) — the `NewsManagement` list (thumbnail, Target, status filter) and the four-card `NewsEdit` form with markdown editor, image upload, and BU targeting.
- [Permissions](/en/platform/news/permissions) — the `news.*` gate matrix, reader-side visibility rules on the public endpoints, and the edge-case matrix for testers.
