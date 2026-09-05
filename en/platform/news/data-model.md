---
title: News — Data Model
description: The tb_news field table (business_unit_ids, tags, doc_version), enum_news_status, the image_file_token → presigned image_url pipeline, the doc_version optimistic lock, and divergences against the SPA News type.
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, news, data-model
editor: markdown
dateCreated: 2026-06-10T13:00:00.000Z
---

# News — Data Model

> **At a Glance**
> **Tables:** `tb_news` — single table, **no FK relations, no unique constraints beyond the PK** &nbsp;·&nbsp; **Enums:** `enum_news_status` (draft · published · archived) &nbsp;·&nbsp; **Targeting:** `business_unit_ids Json @default("[]")` — a JSONB UUID array, not a join table; `[]` = global &nbsp;·&nbsp; **Tags:** `tags Json @default("[]")` — a JSONB string array, lowercased/deduped/capped server-side &nbsp;·&nbsp; **Concurrency:** `doc_version Int @default(0)` — required on every `PUT`, enforces optimistic locking &nbsp;·&nbsp; **Image:** stored as `image_file_token` (MinIO); API responses replace it with a presigned `image_url` (1-hour expiry) &nbsp;·&nbsp; **Endpoints:** `/api/news` (authenticated CRUD) + `/api/news/tags` + `/api/news/summary` (added 2026-08-24) + `/api/public/news` (anonymous) — `/api`, **not** `/api-system` &nbsp;·&nbsp; **Enforcement:** the three write routes check the caller's own `news.*` permission server-side (`PlatformPermissionGuard`, added 2026-08-20); all four `GET` routes check only `x-app-id` — no user-permission check, by design (§6)

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview

The News module owns exactly one table. `tb_news` holds the article itself (`title`, markdown `contents`, optional source `url`), the image as a MinIO file-token string, freeform `tags`, the publication state (`status`, `published_at`), the targeting list (`business_unit_ids` JSONB), an optimistic-lock counter (`doc_version`), and the platform-standard audit trio. Unusually for the platform schema, the model declares **no `@relation` directives at all**: the audit actor columns are bare UUIDs (contrast `tb_application`, whose actor columns FK to `tb_user`), and the BU targeting is a JSONB array rather than a join table. Referential integrity for targeting is enforced at **write time only**, by the micro-cluster service.

The persistence path is gateway → TCP → micro-cluster (`PRISMA_SYSTEM` client); the gateway layer additionally owns the image side-effects (upload to micro-file, rollback, old-file cleanup) and the response shaping (presigned URL, nested audit enrichment) described in §5.

## 2. Entities

### 2.1 `tb_news`

One announcement/article. Schema line 884.

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `title` | `String @db.VarChar` | No | Article title — the only required content field |
| `contents` | `String? @db.VarChar` | Yes | Markdown body, stored verbatim |
| `url` | `String? @db.VarChar` | Yes | Optional source link (SPA validates http(s) format) |
| `image_file_token` | `String? @db.VarChar` | Yes | MinIO file token from micro-file; **never exposed to API consumers** — resolved to `image_url` (§5) |
| `business_unit_ids` | `Json @default("[]") @db.JsonB` | No | Array of `tb_business_unit.id` UUIDs; `[]` = global (all BUs) |
| `tags` | `Json @default("[]") @db.JsonB` | No | Array of lowercase, de-duplicated tag strings — normalized by micro-cluster on every write (§2.3) |
| `status` | `enum_news_status @default(draft)` | No | `draft` · `published` · `archived` |
| `published_at` | `DateTime? @db.Timestamptz(6)` | Yes | First-publish stamp (server-set, §2.2); also the public feed's visibility cutoff (`<= now()`) |
| `doc_version` | `Int @default(0) @db.Integer` | No | Optimistic-lock counter — every `PUT` must supply the version last read; a mismatch fails the update (§2.4) |
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

### 2.3 Tag normalization (`normalizeTags`)

Owned by micro-cluster, run on every create and on any update that touches `tags`:

```
normalizeTags(input):
    if input is null/undefined: return []
    if input is not an array: error "tags must be an array"
    pieces = input.flatMap(el -> String(el).split(','))   -- defends against a stored
                                                            -- tag containing the chip
                                                            -- input's own delimiter
    for each piece:
        tag = piece.trim().toLowerCase()
        skip if empty or already seen (de-dupe)
        error if tag.length > 40                            -- MAX_TAG_LENGTH
        append to cleaned
    error if cleaned.length > 20                             -- MAX_TAGS
    return cleaned
```

The SPA's `ChipInput`/`NewsEdit` apply the same lowercase-trim-dedupe rule client-side before the request is even sent; the backend re-applies it as defense in depth (and is the only enforcement point for the 20-tag / 40-character caps).

### 2.4 Optimistic locking (`doc_version`)

`update()` rejects a request with no `doc_version` (`ErrorCode` `COMMON_DOC_VERSION_REQUIRED`) and otherwise issues:

```sql
UPDATE tb_news SET ... WHERE id = :id AND doc_version = :doc_version
```

via Prisma's `update({ where: { id, doc_version } })`. If another write changed the row since the client's last read, this matches zero rows; a shared Prisma hook raises `OptimisticLockError` (`code = 'DOC_VERSION_CONFLICT'`), which the service's `@TryCatch` decorator maps to `ErrorCode.ALREADY_EXISTS` — surfaced as **HTTP 409** with that message text. The SPA's `isVersionConflict` helper checks for the 409 status **and** either the `DOC_VERSION_CONFLICT` code or the "modified by another request" message text (the code can arrive as `ALREADY_EXISTS` instead, so the message match is load-bearing), then shows "This record was changed by someone else" and refetches. This is the same mechanism used across the Platform book's other `doc_version`-guarded modules (clusters, business units, users, applications, RBAC).

## 3. Relationships

`tb_news` participates in **zero Prisma relations**. The two logical references are convention-only:

- **`business_unit_ids` → `tb_business_unit.id` (logical M:N, stored as JSONB).** Micro-cluster validates on create and on any update that touches the field: the value must be an array of strings, and every unique id must match a **live** (`deleted_at: null`) `tb_business_unit` row — otherwise 400 `One or more business_unit_ids do not exist`. Because nothing enforces it afterwards, a BU soft-deleted later leaves a **stale id** in the array; the public-feed `array_contains` match would still serve that BU's id if a caller presented it.
- **Audit actor columns → `tb_user.id` (logical, no FK).** Resolved to display names at read time by the gateway's audit enrichment (§5), not by a join.

## 4. Enums

### `enum_news_status` (schema line 798)

| Value | Meaning |
|---|---|
| `draft` | Default. Work in progress — invisible to the public feed |
| `published` | Live — served by `/api/public/news` once `published_at <= now()` |
| `archived` | Retired from the public feed but kept visible in the admin list; distinct from soft delete (§5, edge cases in [Permissions](/en/platform/news/permissions) §4) |

Transitions are unrestricted in both the SPA (plain select) and the backend (no transition guard) — any status can move to any other.

## 5. Divergences from carmen-platform SPA shape

The SPA type is `News` in `../carmen-platform/src/types/index.ts`; the translation layer is `src/services/newsService.ts` plus two gateway-side response shapers (`news-image.helper.ts`, the `EnrichAuditUsers` interceptor).

| SPA shape | SPA source | Prisma storage | Notes |
| --------- | ---------- | -------------- | ----- |
| `image_url?: string` (presigned) + `image?: string` (legacy fallback) | `News`; list/edit read `image_url \|\| image` | `image_file_token String?` | The gateway resolves the token via micro-file (`files.presigned-url`, 3600 s expiry), sets `image_url`, and **deletes `image_file_token` from the payload**. URLs expire — never persist or cache them. `image` is an older payload field kept only as a read fallback |
| `audit?: Audit` — nested `{ created, updated, deleted }`, each `{ at, id, name, avatar }` | `News`, `Audit`, `AuditEntry` | six flat audit columns | `@EnrichAuditUsers()` on the GET/POST/PUT routes collapses the flat columns into the nested object (resolving actor names) and removes the flat fields. On enrichment failure the original flat payload passes through — hence the next row |
| Soft-delete dual detection: `!n.deleted_at && !n.audit?.deleted?.at` | `newsService.getAll` | `deleted_at` | **Confirmed fixed since the last sync.** Micro-cluster's `findAll` now merges `deleted_at: null` into its `where` clause (the same fix applied to Applications and Business Units) — the admin list endpoint no longer returns soft-deleted rows at all. The SPA's client-side dual check is now a defensive no-op, not the only filter. `getById`/update/delete continue to enforce `deleted_at: null` server-side (404) |
| `business_unit_ids?: string[]` | `News` | `Json @default("[]")` | Same values; under **multipart** writes the SPA JSON-encodes the array into a string field, which `news-body.parser.ts` parses back. Absent/`[]` both mean global |
| `tags?: string[]` | `News` | `Json @default("[]")` | Same lowercase/deduped values on both sides; under multipart the SPA JSON-encodes the array the same way as `business_unit_ids` |
| List sort `published_at:desc` (default; column sorts clickable) | `NewsManagement` `DataTable` | n/a | **The server ignores the sort parameter**: micro-cluster's list spreads the query args and then overrides with `orderBy: { updated_at: 'desc' }`. The list is always most-recently-updated first regardless of the SPA's sort UI |
| Update response | `newsService.update` → `fetchNews()` re-fetch | n/a | `PUT` returns only `{ id, doc_version }` (list/detail responses carry the full row); the SPA re-fetches the record after a save either way |
| `published_at?: string` (read-only in the SPA) | `NewsEdit` | `DateTime?` | The API accepts explicit `published_at` on create/update (set or `null`-clear); the SPA never sends it and relies on the server stamp (§2.2) |
| `doc_version?: number` | `NewsEdit`, `NewsManagement` (bulk actions) | `Int @default(0)` | Required on every `PUT`; the SPA threads it through from whatever it last fetched (single edit) or from each selected row (bulk publish/archive) |

## 6. References

REST surface (backend-gateway). **Note the prefix: `/api/news`, not `/api-system/...`** — News lives in the gateway's `application/` module group, unlike the platform-admin modules this book otherwise documents.

| Method + Path | Auth | Purpose | Notes |
|---|---|---|---|
| `GET /api/news` | Bearer + `x-app-id` (`news.findAll`) — **no platform-permission check** | Admin list | Paginated; SPA searches `title`,`contents`; status/tag filters via `advance` `{ where: { status: { in }, OR: [{ tags: { array_contains } }, ...] } }`; **excludes soft-deleted rows** (`where.deleted_at = null`, confirmed fixed); audit nested; server-side sort fixed to `updated_at DESC` |
| `GET /api/news/tags` | Bearer + `x-app-id` (`news.findAll`) — **no platform-permission check** | Distinct tags | `SELECT DISTINCT jsonb_array_elements_text(tags) ... WHERE deleted_at IS NULL`, alphabetical — feeds the list's Tags filter and the edit page's autocomplete |
| `GET /api/news/summary` | Bearer + `x-app-id` (`news.findAll`, reused — see §6 notes) — **no platform-permission check** | Newsroom aggregate | Added 2026-08-24 alongside the same fix on Applications; unfiltered (`where: {}`) — status-pipeline counts (draft/published/archived), a fleet-wide `deleted` count, and the lead (most recently published) story; feeds `NewsroomSummary` |
| `GET /api/news/:news_id` | Bearer + `x-app-id` (`news.findOne`) — **no platform-permission check** | Detail | UUID v4 param; 404 when soft-deleted; audit nested; `image_url` presigned |
| `POST /api/news` | Bearer + `x-app-id` (`news.create`) **+ platform permission `news.create`** (`PlatformPermissionGuard`, added 2026-08-20 — see §6 notes) | Create | `multipart/form-data` (binary `image` field; `business_unit_ids`/`tags` as JSON-encoded strings) **or** plain JSON without an image. Returns 201 `{ id, doc_version }`. Failed create rolls the uploaded file back |
| `PUT /api/news/:news_id` | Bearer + `x-app-id` (`news.update`) **+ platform permission `news.update`** (`PlatformPermissionGuard`, added 2026-08-20) | Update | Same multipart/JSON fork; **requires `doc_version`** (400 if missing, 409 on a stale value); a new image replaces and deletes the old file; JSON-only updates leave the image unchanged. Returns `{ id, doc_version }` only |
| `DELETE /api/news/:news_id` | Bearer + `x-app-id` (`news.delete`) **+ platform permission `news.delete`** (`PlatformPermissionGuard`, added 2026-08-20) | Soft delete | Sets `deleted_at`/`deleted_by_id`; best-effort deletes the MinIO file |
| `GET /api/public/news` | **None (anonymous)** | Public feed | `bu_id`/`page`/`perpage` query; published + `published_at <= now()` + not deleted; no `bu_id` → global only; with `bu_id` → global + targeted; lean projection (`id`,`title`,`contents`,`url`,`image_url`,`tags`,`published_at`), `published_at DESC` |
| `GET /api/public/news/:news_id` | **None (anonymous)** | Public detail | 404 for draft/archived/deleted/future-dated/unknown alike |

**Server-side permission enforcement is asymmetric, and deliberately so.** Before 2026-08-20, `news.controller.ts` carried zero `@RequirePlatformPermission` decorators at all — only `KeycloakGuard` (must be logged in) and `AppIdGuard` (the calling application must hold the key in its allowlist). A fix that same day added `PlatformPermissionGuard` + `@RequirePlatformPermission` to the three write routes only. The four `GET` routes were left as-is on purpose: the DEV database shows the `mobile-app` application (`allow_all: false`) holds `news.findAll`/`news.findOne` in its allowlist and serves tenant-level users who hold no platform role whatsoever — requiring `news.read` there would lock every mobile user out of news. Reading `/api/news` therefore stays authenticated-but-unauthorized-by-role; `news.read` remains purely a client-side "show the admin menu item" key. Unauthenticated public reads have their own separate, unguarded controller (`PublicNewsController` at `/api/public/news`).

Multipart format details (create/update): field `image` carries the binary; the gateway's `validateImageUpload` enforces MIME `image/jpeg`/`png`/`webp`, ≤5 MB, and ≤2048×2048 px (parse failure → 400 `BAD_DIMENSIONS`). Text fields arrive as strings; `business_unit_ids` and `tags` are JSON-decoded.

**Primary (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_news` (line 884), `enum_news_status` (line 798).
- `../carmen-turborepo-backend-v2/apps/micro-cluster/src/cluster/news/news.service.ts` — BU validation, tag normalization, `published_at` stamping, the `doc_version` optimistic lock, soft-delete filtering, public filters, the `updated_at` sort override.

**Secondary (gateway + consumer shape):**
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/news/` — `news.controller.ts` (`PlatformPermissionGuard` on the three write routes only — see §6 above), `news.service.ts` (upload/rollback/cleanup; RPC proxy to `micro-cluster`, not direct Prisma access), `news-image.helper.ts`, `news-body.parser.ts`, `public-news.controller.ts`.
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/helpers/image-upload.validator.ts` — server-side image limits.
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/src/index.ts` — `OptimisticLockError` (`DOC_VERSION_CONFLICT`).
- `../carmen-platform/src/types/index.ts` — `News`, `NewsStatus`, `Audit`, `AuditEntry`; `src/services/newsService.ts` — multipart builder, `getTags`, envelope walking; `src/utils/docVersion.ts` — conflict helpers.
- `../carmen-turborepo-backend-bruno/collections/carmen-inventory/master-data/news/` — executable contracts including the `public/` pair and `GET-find-tags-master-data-news.bru`.

**Cross-links:** [News landing](/en/platform/news) &nbsp;·&nbsp; [UI Screens](/en/platform/news/ui-screens) &nbsp;·&nbsp; [Permissions](/en/platform/news/permissions) &nbsp;·&nbsp; [Business Units data-model](/en/platform/business-units/data-model) (the targeted ids)
