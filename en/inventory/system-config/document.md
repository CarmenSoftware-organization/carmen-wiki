---
title: Document Management
description: Tenant-scoped file storage registry backed by MinIO and a tb_file_tag metadata table in a separate file-service database — NOT the tenant schema's tb_attachment, which is a dead, unreferenced table. Upload has no server-side size or MIME validation.
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, document, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Document Management

> **At a Glance**
> **Owner:** Sysadmin (delete); list / download via App ID grants &nbsp;·&nbsp; **Storage:** `micro-file` microservice over MinIO + `tb_file_tag` metadata table in a **separate `prisma-shared-schema-file` database** — **not** the tenant schema's `tb_attachment`, which has zero code references &nbsp;·&nbsp; **Used by:** PR / PO / GRN / SR / IA / count / pricelist / vendor / product attachments &nbsp;·&nbsp; **10 MB cap and MIME allow-list are frontend-only — not re-validated server-side.**

![Document Management screen](/screenshots/system-config/document.png)

## Implementation status (verified 2026-07-16)

Two corrections to the previous version of this page:

1. **The metadata table is `tb_file_tag`, not `tb_attachment`.** A repo-wide search found **zero references to `tb_attachment`** anywhere in `carmen-turborepo-backend-v2/apps` outside its own Prisma model declaration — no service, controller, or DTO reads or writes it. The actual file-upload path (`micro-file/src/files/files.service.ts`) uses `PrismaClient_FILE` from a wholly separate `@repo/prisma-shared-schema-file` database (the `CARMEN_FILE` schema) and writes one row per upload to **`tb_file_tag`** (`bu_code`, `file_token`, `object_name`, `original_name`, `content_type`, `size`, `reference_type`/`reference_id`/`reference_no`, free-form `tags` JSONB) — storage itself is **MinIO**, addressed via `minioClient.putObject`/`getObject`/`removeObject`/`presignedGetObject`, not a generic "S3-compatible" claim tied to `tb_attachment`. §5 below is corrected to describe `tb_file_tag`.
2. **No server-side size or MIME validation.** `files.service.ts`'s `uploadFile()` calls `minioClient.putObject` with the client-supplied `mimetype` and buffer directly — there is no file-size check and no MIME/extension allow-list anywhere in that method. The 10 MB cap (`MAX_FILE_SIZE = 10 * 1024 * 1024` in `document-component.tsx`) and the picker's `accept` attribute are **frontend-only**; a caller that bypasses the browser (direct API call) can upload a larger file of any type. The claimed "defence-in-depth MIME sniffing server-side" was not found in code.

## 1. What & Who

Document Management is the **file-storage registry surface** at `/system-admin/document` — the BU-scoped index of every file uploaded into Carmen. Each row is one object in MinIO storage plus its display metadata in `tb_file_tag`. The same files surface elsewhere as attachments on PR / PO / GRN / SR / IA / pricelist / count documents, where each transactional table carries an `attachments` JSONB referencing **file tokens** from this registry.

**Audience:** Sysadmin manages uploads / deletes here; non-admin roles typically have list / get / download but not delete. The file microservice (`micro-file`, commands `files.upload` / `files.get` / `files.info` / `files.find-all` (list) / `files.delete` / `files.presigned-url` / `files.update-tags`) owns storage and the metadata registry; the gateway's `document-management` module proxies the REST surface to it over TCP.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Upload a new file | System Admin → Document → **Upload** | Single-file picker; picker suggests `.pdf, .docx, .xls/.xlsx, .csv, .txt`; frontend rejects over 10 MB — **neither check is enforced server-side** |
| Filter by file type | Type multi-select (PDF, Excel/CSV, Word, Image, Text, Archive, Code) | URL-synced; active-filter badge bar appears |
| Download a file | Per-row download action | Presigned URL via `GET /api/:bu_code/documents/:filetoken/download` |
| Share a time-limited link | `GET /api/:bu_code/documents/:filetoken/presigned-url?expirySeconds=N` | Never embed permanent storage creds in the browser |
| Delete a stale file | Per-row delete (Sysadmin only) | Confirmation dialog; removes the MinIO object **and** soft-deletes (`deleted_at`) the `tb_file_tag` row; dangling `fileToken`s render as "missing" on bound documents |
| Attach a file to a PR / PO / GRN | **NOT here** — use the transactional screen | This page is the registry, not per-document attachment management |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `fileSizeLimit` toast on upload | File > 10 MB — **frontend check only** | Compress / split before upload; be aware a direct API call bypasses this entirely |
| File rejected by picker | MIME not in the picker's suggested list — **frontend hint only, not enforced server-side** | Convert to an accepted format, or note that the server will in fact accept it via direct API |
| "Missing" attachment on a PR/PO/GRN | File was deleted from this registry while still referenced | Re-upload and re-attach; clean up dangling `fileToken`s manually |
| 403 on delete | User lacks `documents.delete` App ID | Grant via [access-control/application-role](/en/inventory/access-control/application-role) — confirmed real: `AppIdGuard('documents.delete')` on the gateway controller |
| File from BU `T01` invisible in BU `T02` | Expected — BU-scoped storage prefix | Each BU has its own partition; cross-BU access impossible |
| Presigned URL expired | `expirySeconds` elapsed | Request a new one |

## 4. Edge Cases

- **10 MB cap and MIME allow-list are frontend-only.** Confirmed no server-side enforcement in `files.service.ts`'s `uploadFile()`. Larger or unlisted-type files are only blocked if the request goes through the picker's own client-side check.
- **Delete is a soft-delete on the registry row, hard on storage.** `deleteFile()` removes the MinIO object (unrecoverable) and sets `tb_file_tag.deleted_at` (best-effort — logged as a warning, not fatal, if the DB update fails after the object is already gone). Per-document `attachments` JSONB arrays are *not* cleaned up — dangling tokens render as "missing". Do not delete files still attached to in-flight documents.
- **`tb_attachment` (tenant schema) is a dead table.** It has an identically-shaped `doc_version Int @default(0)` column to the one described in [system-config/doc-version](/en/inventory/system-config/doc-version), but zero code anywhere reads or writes it, and it is not the same table as the real registry (`tb_file_tag`, in the separate file-service database). See [system-config/doc-version](/en/inventory/system-config/doc-version) §5 for the corrected framing of this field.
- **Presigned URLs preferred over direct streaming** for browser sharing — never embed permanent storage credentials in the page.

---

## 5. Data Model (Dev)

The tenant schema's `tb_attachment` table is **not** the real registry — confirmed zero code references anywhere outside its own Prisma declaration. Files are actually tracked in a separate file-service database plus per-document JSONB arrays.

### 5.1 `tb_file_tag` (real metadata registry — separate `prisma-shared-schema-file` database)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `bu_code` | `String @db.VarChar` | No | Owning business unit. |
| `file_token` | `String @db.VarChar` (unique) | No | Canonical handle, format `<bu_code>/<uuid>` — matches per-document `attachments[].fileToken`. |
| `object_name` | `String @db.VarChar` | No | MinIO object key (`<file_token>.<ext>`). |
| `original_name` | `String @db.VarChar` | No | Display file name. |
| `content_type` | `String @db.VarChar` | No | MIME type, taken verbatim from the upload request. |
| `size` | `Int` | No | Bytes. |
| `reference_type` / `reference_id` / `reference_no` | `String? @db.VarChar` | Yes | Structured tag fields (indexed) — which document the file belongs to. |
| `description` | `String?` | Yes | Free text. |
| `tags` | `Json? @db.JsonB` | Yes | Free-form tag bag, default `{}`; GIN-indexed. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` (no `doc_version` on this model). |

**Constraints:** unique on `file_token`; indexes on `[bu_code, deleted_at]`, `[bu_code, reference_type, reference_id]`, `[bu_code, reference_no]`, and a GIN index on `tags`. Storage itself is a **MinIO** bucket (`envConfig.MINIO_BUCKET_NAME`), addressed by `object_name` — not a generic third-party S3 account.

### 5.2 `tb_attachment` (tenant schema — dead table, kept for contrast)

`id` / `s3_token` / `s3_folder` / `file_name` / `file_ext` / `file_type` / `file_size` / `file_url` / `doc_version Int @default(0)` / audit columns — shaped like a file registry, but **zero non-schema code references were found**. Do not treat this as the backing table for Document Management.

### 5.3 Per-document `attachments` JSONB

Every transactional table that supports attachments (`tb_purchase_request`, `tb_purchase_order`, `tb_goods_received_note`, `tb_store_requisition`, `tb_inventory_adjustment`, `tb_physical_count`, `tb_spot_check`, `tb_credit_note`, `tb_recipe`, `tb_product`, `tb_vendor`, `tb_tax_profile`, …) carries:

```jsonc
"attachments": [
  { "fileToken": "T01/019638a6-...", "fileName": "vendor-invoice.pdf",
    "fileSize": 102400, "contentType": "application/pdf",
    "uploadedAt": "2026-05-15T08:00:00.000Z" }
]
```

`fileToken` matches `tb_file_tag.file_token` (**not** `tb_attachment.s3_token`). The list endpoint queries `micro-file`/`tb_file_tag` (source of truth), not the tenant schema.

### 5.4 `DocumentFile` API projection

`fileToken` (may carry `<buCode>/` prefix — stripped before delete) &nbsp;·&nbsp; `objectName` &nbsp;·&nbsp; `originalName` &nbsp;·&nbsp; `size` &nbsp;·&nbsp; `contentType` (drives type filter) &nbsp;·&nbsp; `lastModified`.

## 6. Business Rules

- **10 MB upload cap and MIME allow-list are frontend-only.** Confirmed no server-side check in `files.service.ts`'s `uploadFile()`.
- **BU-scoped.** All endpoints under `/api/:bu_code/documents/*`; MinIO objects and `tb_file_tag` rows both partitioned by `bu_code`.
- **Presigned URLs** for download / sharing — never embed permanent credentials.
- **AppId guards (confirmed real).** `documents.upload`, `documents.list`, `documents.get`, `documents.download`, `documents.info`, `documents.presignedUrl`, `documents.delete` — each is a distinct `AppIdGuard(...)` decorator on `document-management.controller.ts`. Non-admin = list / get / download only.
- **Delete.** MinIO object removal is immediate and unrecoverable; the `tb_file_tag` row is soft-deleted (`deleted_at`) on a best-effort basis (a DB failure here is logged, not raised). Per-document `attachments` arrays are *not* cascaded.
- **Audit logging** via `runWithAuditContext`/`AuditContext` in `micro-file`'s controller (uploads, deletes, presigned-URL, tag updates).
- **No in-place versioning** — overwrite via delete + re-upload.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) / [purchase-order](/en/inventory/purchase-order) / [good-receive-note](/en/inventory/good-receive-note) / [store-requisition](/en/inventory/store-requisition) / [inventory-adjustment](/en/inventory/inventory-adjustment) / [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check) — carry `attachments` JSONB.
- [master-data/vendor](/en/inventory/master-data/vendor) / [product](/en/inventory/product) — vendor and product master records carry their own `attachments` arrays.
- [system-config/doc-version](/en/inventory/system-config/doc-version) — `tb_attachment.doc_version` is an inert column on this dead table, not an active concurrency guard or re-render counter.
- [reporting-audit/report](/en/inventory/reporting-audit/report) — generated report artefacts are intended to land here via the same `fileToken` mechanism (unconfirmed this pass).
- [system-config/workflow](/en/inventory/system-config/workflow) — workflow comments embed `attachments` arrays for evidence files.

## 8. References

- **Prisma (file schema — the real registry):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-file/prisma/schema.prisma` — `tb_file_tag` (lines ~19-49).
- **Prisma (tenant schema — dead table, for contrast):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (lines ~4797-4819); per-document `attachments` JSONB columns throughout.
- **Backend gateway (proxy layer):** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.controller.ts` + `document-management.service.ts` — forwards to the `FILE_SERVICE` microservice over `files.*` TCP commands.
- **Backend file microservice (actual storage + registry):** `../carmen-turborepo-backend-v2/apps/micro-file/src/files/files.controller.ts` + `files.service.ts` — MinIO client, `tb_file_tag` CRUD.
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/document/document.route.tsx` + `document-component.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend-react/hooks/use-document.ts` — `useDocument`, `useUploadDocument`, `useDeleteDocument`.
- **Frontend type:** `../carmen-inventory-frontend-react/types/document.ts` — `DocumentFile`.
