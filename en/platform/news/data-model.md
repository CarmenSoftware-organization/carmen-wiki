---
title: News — Data Model
description: The tb_news field table, the JSONB business_unit_ids targeting column, enum_news_status, the image_file_token → presigned image_url pipeline, and divergences against the SPA News type.
published: true
date: 2026-06-10T13:00:00.000Z
tags: book/platform, news, data-model
editor: markdown
dateCreated: 2026-06-10T13:00:00.000Z
---

# News — Data Model

> **At a Glance**
> **Tables:** `tb_news` — single table, **no FK relations, no unique constraints beyond the PK** &nbsp;·&nbsp; **Enums:** `enum_news_status` (draft · published · archived) &nbsp;·&nbsp; **Targeting:** `business_unit_ids Json @default("[]")` — a JSONB UUID array, not a join table; `[]` = global &nbsp;·&nbsp; **Image:** stored as `image_file_token` (MinIO); API responses replace it with a presigned `image_url` (1-hour expiry) &nbsp;·&nbsp; **Endpoints:** `/api/news` (authenticated CRUD) + `/api/public/news` (anonymous) — `/api`, **not** `/api-system`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The News module owns exactly one table. `tb_news` holds the article itself (`title`, markdown `contents`, optional source `url`), the image as a MinIO file-token string, the publication state (`status`, `published_at`), the targeting list (`business_unit_ids` JSONB), and the platform-standard audit trio. Unusually for the platform schema, the model declares **no `@relation` directives at all**: the audit actor columns are bare UUIDs (contrast `tb_application`, whose actor columns FK to `tb_user`), and the BU targeting is a JSONB array rather than a join table. Referential integrity for targeting is enforced at **write time only**, by the micro-cluster service.

The persistence path is gateway → TCP → micro-cluster (`PRISMA_SYSTEM` client); the gateway layer additionally owns the image side-effects (upload to micro-file, rollback, old-file cleanup) and the response shaping (presigned URL, nested audit enrichment) described in §5.

## 2. Entities

### 2.1 `tb_news`

One announcement/article. Schema line 803.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `title` | `String @db.VarChar` | No | Article title — the only required content field |
| `contents` | `String? @db.VarChar` | Yes | Markdown body, stored verbatim |
| `url` | `String? @db.VarChar` | Yes | Optional source link (SPA validates http(s) format) |
| `image_file_token` | `String? @db.VarChar` | Yes | MinIO file token from micro-file; **never exposed to API consumers** — resolved to `image_url` (§5) |
| `business_unit_ids` | `Json @default("[]") @db.JsonB` | No | Array of `tb_business_unit.id` UUIDs; `[]` = global (all BUs) |
| `status` | `enum_news_status @default(draft)` | No | `draft` · `published` · `archived` |
| `published_at` | `DateTime? @db.Timestamptz(6)` | Yes | First-publish stamp (server-set, §2.2); also the public feed's visibility cutoff (`<= now()`) |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: row creation time, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: creator user id — **bare UUID, no FK** |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: last update time, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: last updater user id — bare UUID, no FK |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Soft-delete timestamp; NULL = live row |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: deleter user id — bare UUID, no FK |

**Constraints:**
- `@id` on `id` — the only constraint. No `@@unique` (duplicate titles are allowed), no FK to any table.

**Indexes:**
- `@@index([status, published_at])` — map `"tb_news_status_published_at_idx"` — drives the public feed query (`status = published AND published_at <= now()` ordered by `published_at DESC`).

### 2.2 `published_at` write semantics

Owned by micro-cluster (`news.service.ts`), not the database:

```
create(data):
    status = data.status ?? draft
    published_at = data.published_at ?? null
    if status == published and published_at is null:
        published_at = now()                      -- first-publish stamp

update(id, data):
    if data.published_at provided:                -- explicit set or clear wins
        published_at = data.published_at (null clears)
    else if data.status == published
         and existing.status != published
         and existing.published_at is null:       -- never-published rows only
        published_at = now()
    else:
        published_at unchanged
```

Consequences: the stamp is set **once** — demoting to `draft`/`archived` keeps it, and re-publishing later keeps the *original* time. A future-dated `published_at` (settable via API only; the SPA never sends the field) keeps the row out of the public feed until that time — de-facto scheduled publishing.

## 3. Relationships

`tb_news` participates in **zero Prisma relations**. The two logical references are convention-only:

- **`business_unit_ids` → `tb_business_unit.id` (logical M:N, stored as JSONB).** Micro-cluster validates on create and on any update that touches the field: the value must be an array of strings, and every unique id must match a **live** (`deleted_at: null`) `tb_business_unit` row — otherwise 400 `One or more business_unit_ids do not exist`. Because nothing enforces it afterwards, a BU soft-deleted later leaves a **stale id** in the array; the public-feed `array_contains` match would still serve that BU's id if a caller presented it.
- **Audit actor columns → `tb_user.id` (logical, no FK).** Resolved to display names at read time by the gateway's audit enrichment (§5), not by a join.

## 4. Enums

### `enum_news_status` (schema line 693)

| Value | Meaning |
|---|---|
| `draft` | Default. Work in progress — invisible to the public feed |
| `published` | Live — served by `/api/public/news` once `published_at <= now()` |
| `archived` | Retired from the public feed but kept visible in the admin list; distinct from soft delete (§5, edge cases in [Permissions](./permissions.md) §4) |

Transitions are unrestricted in both the SPA (plain select) and the backend (no transition guard) — any status can move to any other.

## 5. Divergences from carmen-platform SPA shape

The SPA type is `News` in `../carmen-platform/src/types/index.ts`; the translation layer is `src/services/newsService.ts` plus two gateway-side response shapers (`news-image.helper.ts`, the `EnrichAuditUsers` interceptor).

| SPA shape | SPA source | Prisma storage | Notes |
| --------- | ---------- | -------------- | ----- |
| `image_url?: string` (presigned) + `image?: string` (legacy fallback) | `News`; list/edit read `image_url \|\| image` | `image_file_token String?` | The gateway resolves the token via micro-file (`files.presigned-url`, 3600 s expiry), sets `image_url`, and **deletes `image_file_token` from the payload**. URLs expire — never persist or cache them. `image` is an older payload field kept only as a read fallback |
| `audit?: Audit` — nested `{ created, updated, deleted }`, each `{ at, id, name, avatar }` | `News`, `Audit`, `AuditEntry` | six flat audit columns | `@EnrichAuditUsers()` on the GET/POST/PUT routes collapses the flat columns into the nested object (resolving actor names) and removes the flat fields. On enrichment failure the original flat payload passes through — hence the next row |
| Soft-delete dual detection: `!n.deleted_at && !n.audit?.deleted?.at` | `newsService.getAll` | `deleted_at` | The **admin list endpoint returns soft-deleted rows** (micro-cluster's list query applies no `deleted_at` filter); the SPA hides them client-side, checking both the enriched and the flat location. `getById`/update/delete do enforce `deleted_at: null` server-side (404) |
| `business_unit_ids?: string[]` | `News` | `Json @default("[]")` | Same values; under **multipart** writes the SPA JSON-encodes the array into a string field, which `news-body.parser.ts` parses back. Absent/`[]` both mean global |
| List sort `published_at:desc` (default; column sorts clickable) | `NewsManagement` `DataTable` | n/a | **The server ignores the sort parameter**: micro-cluster's list spreads the query args and then overrides with `orderBy: { updated_at: 'desc' }`. The list is always most-recently-updated first regardless of the SPA's sort UI |
| Update response | `newsService.update` → `fetchNews()` re-fetch | n/a | `PUT` returns only `{ id, image_url }`, not the full record — the SPA re-fetches after every save; API consumers must `GET :id` for the updated row |
| `published_at?: string` (read-only in the SPA) | `NewsEdit` | `DateTime?` | The API accepts explicit `published_at` on create/update (set or `null`-clear); the SPA never sends it and relies on the server stamp (§2.2) |

## 6. References

REST surface (backend-gateway). **Note the prefix: `/api/news`, not `/api-system/...`** — News lives in the gateway's `application/` module group, unlike the platform-admin modules this book otherwise documents.

| Method + Path | Auth | Purpose | Notes |
|---|---|---|---|
| `GET /api/news` | Bearer + `x-app-id` (`news.findAll`) | Admin list | Paginated; SPA searches `title`,`contents`; status filter via `advance` `{ where: { status: { in } } }`; **includes soft-deleted rows**; audit nested; server-side sort fixed to `updated_at DESC` |
| `GET /api/news/:news_id` | Bearer + `x-app-id` (`news.findOne`) | Detail | UUID v4 param; 404 when soft-deleted; audit nested; `image_url` presigned |
| `POST /api/news` | Bearer + `x-app-id` (`news.create`) | Create | `multipart/form-data` (binary `image` field; `business_unit_ids` as JSON-encoded string) **or** plain JSON without an image. Returns 201 `{ id }` (+ `image_url` when uploaded). Failed create rolls the uploaded file back |
| `PUT /api/news/:news_id` | Bearer + `x-app-id` (`news.update`) | Update | Same multipart/JSON fork; a new image replaces and deletes the old file; JSON-only updates leave the image unchanged. Returns `{ id, image_url }` only |
| `DELETE /api/news/:news_id` | Bearer + `x-app-id` (`news.delete`) | Soft delete | Sets `deleted_at`/`deleted_by_id`; best-effort deletes the MinIO file |
| `GET /api/public/news` | **None (anonymous)** | Public feed | `bu_id`/`page`/`perpage` query; published + `published_at <= now()` + not deleted; no `bu_id` → global only; with `bu_id` → global + targeted; lean projection (`id`,`title`,`contents`,`url`,`image_url`,`published_at`), `published_at DESC` |
| `GET /api/public/news/:news_id` | **None (anonymous)** | Public detail | 404 for draft/archived/deleted/future-dated/unknown alike |

Multipart format details (create/update): field `image` carries the binary; the gateway's `validateImageUpload` enforces MIME `image/jpeg`/`png`/`webp`, ≤5 MB, and ≤2048×2048 px (parse failure → 400 `BAD_DIMENSIONS`). Text fields arrive as strings; only `business_unit_ids` is JSON-decoded.

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_news` (line 803), `enum_news_status` (line 693).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` — BU validation, `published_at` stamping, soft delete, public filters, the `updated_at` sort override.

**Secondary (gateway + consumer shape):**
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/` — `news.controller.ts`, `news.service.ts` (upload/rollback/cleanup), `news-image.helper.ts`, `news-body.parser.ts`, `public-news.controller.ts`.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/helpers/image-upload.validator.ts` — server-side image limits.
- `../carmen-platform/src/types/index.ts` — `News`, `NewsStatus`, `Audit`, `AuditEntry`; `src/services/newsService.ts` — multipart builder, envelope walking, soft-delete filter.
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/news/` — executable contracts including the `public/` pair.

**Cross-links:** [News landing](/en/platform/news) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Business Units data-model](../business-units/data-model.md) (the targeted ids)
