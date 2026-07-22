---
title: Attachment
description: File-metadata registry used by every module with file uploads — MinIO-backed tb_file_tag in a separate file-service database, served by the micro-file microservice. The tenant schema's tb_attachment table has zero code references and is dead.
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Attachment

> **At a Glance**
> **Owner:** Owning module's upload flow &nbsp;·&nbsp; **Table:** `tb_file_tag` — in a **separate `prisma-shared-schema-file` (`CARMEN_FILE`) database**, not the tenant schema &nbsp;·&nbsp; **Storage:** MinIO &nbsp;·&nbsp; **Used by:** every module with file uploads &nbsp;·&nbsp; The tenant schema's `tb_attachment` table is dead — zero non-schema code references.

## Implementation status (verified 2026-07-22)

The previous version of this page described `tb_attachment` (tenant schema) as the live, shared file-metadata catalogue, with an S3-backed `s3_token`/`s3_folder` shape and a `doc_version` "re-render counter... incremented on re-render; older versions retained for audit." A repo-wide search of `carmen-turborepo-backend-v2/apps` found **zero references to `tb_attachment` outside its own Prisma model declaration** — no service, controller, repository, or DTO reads or writes it anywhere. `tb_attachment.doc_version` is likewise never incremented or read by any code path; it is inert schema, not a working re-render counter. This mirrors the already-confirmed [system-config/document](/en/inventory/system-config/document) finding for the same table.

The real file-storage path is the **`micro-file`** microservice (`micro-file/src/files/files.service.ts`), which writes to **MinIO** object storage and to **`tb_file_tag`** — a table in a wholly separate `@repo/prisma-shared-schema-file` database (the `CARMEN_FILE` schema), not the tenant or platform schema. This page is corrected to describe that mechanism. See [system-config/document](/en/inventory/system-config/document) for the full admin-screen walkthrough (`/system-admin/document`) — this page focuses on the entity as consumed by other modules.

## 1. What & Who

The real file registry is `tb_file_tag`, one row per uploaded MinIO object, linked back to its owning document through **per-document JSONB arrays** rather than an in-schema FK. Quotations on a PR, vendor confirmations on a PO, signed delivery dockets on a GRN, count sheets on a physical count, photos on a spot check — every transactional table that supports attachments (`tb_purchase_request`, `tb_purchase_order`, `tb_goods_received_note`, `tb_store_requisition`, `tb_inventory_adjustment`, `tb_physical_count`, `tb_spot_check`, `tb_credit_note`, `tb_recipe`, `tb_product`, `tb_vendor`, `tb_tax_profile`, …) carries an `attachments` JSONB column whose entries reference a `fileToken` — not `tb_attachment.s3_token`.

Each `tb_file_tag` row carries the MinIO object key (`object_name`), original file metadata (`original_name`, `content_type`, `size`), and structured/free-form tags (`reference_type`/`reference_id`/`reference_no`, `tags` JSONB) for lookups. There is **no `doc_version`/re-render-versioning column on `tb_file_tag`** — re-uploading a document's PDF is a plain new upload, not a versioned revision of an existing row.

**Maintained by** the owning module's upload flow, via `micro-file`'s commands (`files.upload` / `files.get` / `files.info` / `files.find-all` / `files.delete` / `files.presigned-url` / `files.update-tags`). **Read by** the owning module's detail screens, which resolve each `fileToken` back to a fresh, time-limited MinIO URL.

### 1.1 File retrieval — the stored URL is never trusted

**On read, the URL is re-resolved, not replayed from storage.** For every attachment, the gateway resolves a fresh **presigned MinIO URL** (1-hour TTL) from the internal `fileToken`; if resolution fails it falls back to a relative gateway route `/api/{bu_code}/documents/{fileToken}/download`. The internal `fileToken` is then **stripped** from the response in some projections (e.g. comment attachments) — callers only ever see the resolved `fileUrl`.

The attachment shape exposed in comment responses (a real, narrower response DTO — distinct from the full `DocumentFile` projection on [system-config/document](/en/inventory/system-config/document) §5.4):

| Field | Type | Notes |
|---|---|---|
| `fileName` | string | Original file name |
| `fileUrl` | string (optional) | Presigned URL, or relative fallback route; refilled per request |
| `contentType` | string | MIME type (`image/jpeg`, `image/png`, `image/webp`, `image/gif`, `application/pdf`) |
| `size` | number (optional) | Bytes |

Comment responses additionally **strip internal author fields** (`user_id`, `username`, `firstname`, `middlename`, `lastname`) — the resolved author is exposed via the enriched `audit` object instead.

> **Note — the confirmed-dead `doc_version` column.** `tb_attachment.doc_version` in the tenant schema is a legacy, never-referenced field — not a re-render counter and not the same concept as the optimistic-concurrency `doc_version` carried by transactional documents. See [system-config/doc-version](/en/inventory/system-config/doc-version) for the corrected framing of that field.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Attach a file to a document | Document detail → **Attachments** tab → Upload | Writes a `tb_file_tag` row + appends to the owning table's `attachments` JSONB |
| Download attachment | Click filename | Presigned MinIO URL, re-resolved fresh each request (1-hour TTL) |
| Remove an attachment | Attachments tab → Delete | Removes the MinIO object (unrecoverable) and soft-deletes the `tb_file_tag` row; the owning document's `attachments` array entry is **not** cleaned up — see Edge Cases |
| Confirmed no server-side size/MIME check | `files.service.ts`'s `uploadFile()` | See [system-config/document](/en/inventory/system-config/document) §Implementation status — any client-declared size/MIME limit is frontend-only |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| Broken/expired file link | Presigned URL TTL passed | Re-open the document — the URL is re-resolved on every fetch, never cached server-side |
| "Missing" attachment on a document | The `tb_file_tag` row was deleted from the registry while a `fileToken` still referenced it | Dangling tokens are not cleaned up automatically; re-upload and re-attach |
| MIME mismatch | `content_type` taken verbatim from the upload request, not re-verified server-side | Do NOT rely on `content_type` for security decisions |

## 4. Edge Cases

- **Delete is hard on storage, soft on the registry row, and never cascades.** `deleteFile()` removes the MinIO object immediately (unrecoverable) and sets `tb_file_tag.deleted_at` on a best-effort basis. The owning document's `attachments` JSONB array is **not** updated — a deleted file's token renders as "missing" on any document still referencing it.
- **No polymorphic FK — by design.** Linkage is one-directional: the owning table's `attachments` JSONB holds `fileToken`s pointing at `tb_file_tag`; there is no reverse index on `tb_file_tag` back to every owning row.
- **MIME / size trust.** Both come from the upload request and are not re-verified server-side — do not rely on them for security.
- **Separate database.** `tb_file_tag` lives in a distinct Postgres database/schema (`CARMEN_FILE`) from both the tenant and platform schemas — cross-schema joins are not possible at the SQL level; resolution is always via the `micro-file` service API.

---

## 5. Data Model (Dev)

Source: **separate `prisma-shared-schema-file` database** — not the tenant schema.

### 5.1 `tb_file_tag` (real metadata registry)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `bu_code` | `String @db.VarChar` | No | Owning business unit. |
| `file_token` | `String @db.VarChar` (unique) | No | Canonical handle, format `<bu_code>/<uuid>` — matches per-document `attachments[].fileToken`. |
| `object_name` | `String @db.VarChar` | No | MinIO object key. |
| `original_name` | `String @db.VarChar` | No | Display file name. |
| `content_type` | `String @db.VarChar` | No | MIME type, verbatim from the upload request. |
| `size` | `Int` | No | Bytes. |
| `reference_type` / `reference_id` / `reference_no` | `String? @db.VarChar` | Yes | Structured, indexed tag fields — which document the file belongs to. |
| `description` | `String?` | Yes | Free text. |
| `tags` | `Json? @db.JsonB` | Yes | Default `{}`; free-form, GIN-indexed. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` (no `doc_version` on this model). |

**Constraints:** unique on `file_token`; indexes on `[bu_code, deleted_at]`, `[bu_code, reference_type, reference_id]`, `[bu_code, reference_no]`, and a GIN index on `tags`.

### 5.2 `tb_attachment` (tenant schema — dead table, kept for contrast)

`id` / `s3_token` / `s3_folder` / `file_name` / `file_ext` / `file_type` / `file_size` / `file_url` / `info` / `doc_version Int @default(0)` / audit columns. Shaped like a file registry but **zero non-schema code references were found anywhere in the backend**. Do not treat this as the backing table for any module's attachments.

### 5.3 Per-document `attachments` JSONB

```jsonc
"attachments": [
  { "fileToken": "T01/019638a6-...", "fileName": "vendor-invoice.pdf",
    "fileSize": 102400, "contentType": "application/pdf",
    "uploadedAt": "2026-05-15T08:00:00.000Z" }
]
```

`fileToken` matches `tb_file_tag.file_token`, never `tb_attachment.s3_token`.

## 6. Business Rules

- **`tb_file_tag` is the real registry; `tb_attachment` is dead.** Confirmed by a repo-wide code search — no service anywhere reads or writes `tb_attachment`.
- **No server-side size or MIME validation** on the underlying upload path (`files.service.ts`'s `uploadFile()`).
- **Delete is immediate and unrecoverable on MinIO**, best-effort soft-delete on `tb_file_tag`, and never cascades to owning-document `attachments` arrays.
- **URL lifecycle.** Always re-resolve via the file service — never cache a `fileUrl` across sessions; the presigned URL expires after 1 hour.
- **Cross-database linkage.** `tb_file_tag` cannot be joined at the SQL level with tenant or platform tables — resolution is always through the `micro-file` service API.

## 7. Cross-References

- [system-config/document](/en/inventory/system-config/document) — the canonical page for this mechanism: the `/system-admin/document` registry screen, full `DocumentFile` API projection, and AppId guards.
- [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), [good-receive-note](/en/inventory/good-receive-note) — quotations, confirmations, dockets.
- [inventory-adjustment](/en/inventory/inventory-adjustment), [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check) — supporting paperwork and evidence.
- [store-requisition](/en/inventory/store-requisition), [vendor-pricelist](/en/inventory/vendor-pricelist), [recipe](/en/inventory/recipe), [product](/en/inventory/product) — module-specific attachments.
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — upload/download actions logged with `entity_type = 'attachment'` (unconfirmed against `tb_file_tag` specifically — the activity write path was not traced against the file service in this pass).

## 8. References

- **Prisma (file schema — the real registry):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-file/prisma/schema.prisma` — `tb_file_tag` (lines ~19-49).
- **Prisma (tenant schema — dead table, for contrast):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (line ~4790).
- **Backend gateway (proxy layer):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.controller.ts` + `.service.ts` — forwards to the `FILE_SERVICE` microservice over `files.*` TCP commands.
- **Backend file microservice (actual storage + registry):** `../carmen-turborepo-backend-v2/apps/micro-file/src/files/files.controller.ts` + `files.service.ts` — MinIO client, `tb_file_tag` CRUD.
