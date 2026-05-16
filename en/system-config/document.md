---
title: Document Management
description: Tenant-scoped file storage registry — upload, list, download, presigned URLs, and delete for documents attached to transactional records.
published: true
date: 2026-05-16T17:00:00.000Z
tags: system-config, document, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Document Management

## 1. Purpose

Document Management is the **file-storage registry surface** under System Admin — not a per-document-type policy table, but the BU-scoped index of every file that has been uploaded into Carmen. Each row represents one binary blob held in object storage (S3-compatible) plus its display metadata. The screen at `/system-admin/document` lets Sysadmin browse, filter by MIME type, upload new files, and delete stale ones; the same files surface elsewhere as attachments on PR / PO / GRN / SR / IA / pricelist / count documents, where each transactional table carries its own `attachments` JSONB column referencing file tokens from this registry.

The page also serves as the upload entry-point for documents that aren't (yet) attached to a transaction — for example, vendor master documents, signed contracts, scanned invoices waiting to be linked to a GRN, or supporting evidence for an audit. The file microservice (`FILE_SERVICE`, command `files.upload` / `files.get` / `files.list` / `files.delete`) owns the storage; the gateway exposes the REST surface.

## 2. Prisma Model(s) OR Data Model

The tenant schema does not have a `tb_document` table. Files are tracked in two places:

### 2.1 `tb_attachment` (file metadata mirror)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `s3_token` | `String? @db.VarChar(255)` | Yes | Storage token returned by `FILE_SERVICE` — the canonical handle used everywhere downstream. |
| `s3_folder` | `String? @db.VarChar(255)` | Yes | Storage folder / prefix (typically `<bu_code>/<yyyy-mm>/`). |
| `file_name` | `String? @db.VarChar(255)` | Yes | Display name. |
| `file_ext` | `String? @db.VarChar(255)` | Yes | Extension (`pdf`, `xlsx`, `png`, …). |
| `file_type` | `String? @db.VarChar(255)` | Yes | MIME type. |
| `file_size` | `BigInt? @db.BigInt` | Yes | Bytes. |
| `file_url` | `String? @db.VarChar(255)` | Yes | Persistent URL (presigned URLs are issued on demand and not stored here). |
| `info` | `Json? @db.Json` | Yes | Free-form metadata. |
| `doc_version` | `Int` | No | Default `0`; reserved for future versioning. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([s3_token, deleted_at], map: "attachment_s3_token_u")` and index on `[s3_token]`. There are no foreign keys *out* of this table — referential integrity to transactional documents lives in the per-document `attachments` JSONB.

### 2.2 Per-document `attachments` JSONB

Every transactional table that supports attachments (`tb_purchase_request`, `tb_purchase_order`, `tb_goods_received_note`, `tb_store_requisition`, `tb_inventory_adjustment`, `tb_physical_count`, `tb_spot_check`, `tb_credit_note`, `tb_recipe`, `tb_product`, `tb_vendor`, `tb_tax_profile`, …) carries a column:

```jsonc
"attachments": [
  {
    "fileToken": "S3_UUID",
    "fileName":  "vendor-invoice.pdf",
    "fileSize":  102400,
    "contentType": "application/pdf",
    "uploadedAt": "2026-05-15T08:00:00.000Z"
  }
]
```

The `fileToken` matches `tb_attachment.s3_token` and is the link between the registry and the using document. The list endpoint surfaced by `/system-admin/document` does not query `tb_attachment` directly — it queries the file microservice, which is the source of truth.

### 2.3 Document-management API shape (`DocumentFile`)

The list endpoint returns the following projection per file (see `types/document.ts`):

| Field | Type | Description |
| --- | --- | --- |
| `fileToken` | `string` | Stable handle. May carry a `<buCode>/` prefix in the response — frontend strips before issuing delete. |
| `objectName` | `string` | Storage key. |
| `originalName` | `string` | User-supplied file name at upload. |
| `size` | `number` | Bytes. |
| `contentType` | `string` | MIME type. Drives the grid type filter (PDF / Excel / Word / Image / Text / Archive / Code). |
| `lastModified` | `string` | ISO 8601. |

## 3. Usage / Cross-References

- [[purchase-request]] / [[purchase-order]] / [[good-receive-note]] / [[store-requisition]] / [[inventory-adjustment]] / [[physical-count]] / [[spot-check]] — every transactional document carries an `attachments` JSONB referencing `fileToken`s from this registry.
- [[vendor]] / [[product-management]] — vendor and product master records carry their own `attachments` arrays for contracts, certificates, spec sheets.
- [[reporting-audit/attachment]] — cross-module attachment policy and visibility rules.
- [[reporting-audit/report]] — generated report artefacts (PDF / Excel) land back here via the same `fileToken` mechanism; `tb_report_job.file_url` references storage in the same bucket.
- [[system-config/workflow]] — workflow comments (`tb_workflow_comment`, `tb_period_comment`, etc.) embed `attachments` arrays for evidence files.

## 4. Configuration UI

Managed by **Sysadmin** under System Admin → Document (`/system-admin/document`). The page is a paginated DataGrid with:

- **Header:** module-accent dot, title, total-record count badge, and an **Upload** button (single-file picker, accepts `.pdf, .docx, .xls/.xlsx, .csv, .txt`).
- **Filter bar:** free-text search plus a multi-select **Type** filter with seven categories (PDF, Excel/CSV, Word, Image, Text, Archive, Code). Filters are URL-synced; an active-filter badge bar appears under the search.
- **List:** desktop renders the DataGrid (sortable columns, sticky header, pagination); mobile renders a card grid with infinite scroll.
- **Per-row actions:** download (via presigned URL) and delete (with confirmation dialog).

The screen is **read-mostly** for non-admin users; only Sysadmin can delete. Per-document attachment management (adding a file to a PR / PO / GRN) happens inside the relevant transactional screen, not here.

## 5. Business Rules

- **10 MB upload cap.** The frontend enforces `MAX_FILE_SIZE = 10 * 1024 * 1024` bytes before issuing the multipart `POST`. The backend re-validates server-side. Larger files are rejected with the localised `fileSizeLimit` toast.
- **MIME allow-list.** The file picker accepts `.pdf, .docx, .xls, .xlsx, .csv, .txt`. The frontend filter recognises additional categories (image, archive, code) so legacy uploads remain discoverable — but new uploads should land in the picker's allow-list. The `FILE_SERVICE` performs its own server-side MIME sniffing as a defence-in-depth check.
- **BU-scoped.** Every endpoint is mounted under `/api/:bu_code/documents/*`. A file uploaded in BU `T01` is invisible to BU `T02`; the file microservice partitions the storage prefix by `bu_code`.
- **Presigned URLs for download.** Direct download is via `GET /api/:bu_code/documents/:filetoken/download` (binary stream) or `GET /api/:bu_code/documents/:filetoken/presigned-url?expirySeconds=N` for a time-limited link suitable for sharing — never embed permanent storage credentials in the browser.
- **Permissions via AppId guards.** Each endpoint is gated by `documents.upload`, `documents.list`, `documents.get`, `documents.download`, `documents.info`, `documents.presignedUrl`, `documents.delete`. Non-admin roles typically have list / get / download but not delete.
- **Deletion is hard.** `DELETE /api/:bu_code/documents/:filetoken` removes the file from storage; `tb_attachment.deleted_at` is set; per-document `attachments` arrays are *not* cleaned up — a dangling `fileToken` on a PR/PO/GRN renders as "missing" in the attachment list. Cleaning dangling references is a future enhancement; for now, do not delete files still attached to in-flight documents.
- **Audit logging.** All endpoints carry `EnrichAuditUsers`; uploads, deletes, and presigned-URL generations land in [[reporting-audit/activity]] with `user_id`, `bu_code`, `fileToken`. (*Inferred — to be verified for the presigned-URL action specifically.*)
- **Versioning.** `tb_attachment.doc_version` defaults to `0` and is reserved; the current pipeline overwrites by deleting and re-uploading rather than versioning in place.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (lines ~4427-4449); per-document `attachments` JSONB columns throughout.
- **Backend controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.controller.ts`.
- **Backend service:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.service.ts` — forwards to `FILE_SERVICE` over the `files.*` microservice commands.
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/document/page.tsx` and `_components/document-component.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend/hooks/use-document.ts` — `useDocument`, `useUploadDocument`, `useDeleteDocument`.
- **Frontend type:** `../carmen-inventory-frontend/types/document.ts` — `DocumentFile`.
- **Cross-module:** see Section 3.
