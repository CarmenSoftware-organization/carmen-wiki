---
title: Document Management
description: Tenant-scoped file storage registry — upload, list, download, presigned URLs, and delete for documents attached to transactional records.
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, document, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Document Management

> **At a Glance**
> **Owner:** Sysadmin (delete); list / download via App ID grants &nbsp;·&nbsp; **Storage:** `FILE_SERVICE` microservice (S3-compatible) + `tb_attachment` metadata mirror &nbsp;·&nbsp; **Used by:** PR / PO / GRN / SR / IA / count / pricelist / vendor / product attachments &nbsp;·&nbsp; **10 MB cap, BU-scoped.**

![Document Management screen](/screenshots/system-config/document.png)

## 1. What & Who

Document Management is the **file-storage registry surface** at `/system-admin/document` — the BU-scoped index of every file uploaded into Carmen. Each row is one binary blob in object storage (S3-compatible) plus its display metadata. The same files surface elsewhere as attachments on PR / PO / GRN / SR / IA / pricelist / count documents, where each transactional table carries an `attachments` JSONB referencing **file tokens** from this registry.

**Audience:** Sysadmin manages uploads / deletes here; non-admin roles typically have list / get / download but not delete. The file microservice (`FILE_SERVICE`, commands `files.upload` / `files.get` / `files.list` / `files.delete`) owns storage; the gateway exposes the REST surface.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Upload a new file | System Admin → Document → **Upload** | Single-file picker; accepts `.pdf, .docx, .xls/.xlsx, .csv, .txt`; 10 MB cap |
| Check the 10 MB upload limit | Frontend rejects pre-`POST` | `MAX_FILE_SIZE = 10 * 1024 * 1024`; backend re-validates; toast `fileSizeLimit` on rejection |
| Filter by file type | Type multi-select (PDF, Excel/CSV, Word, Image, Text, Archive, Code) | URL-synced; active-filter badge bar appears |
| Download a file | Per-row download action | Presigned URL via `GET /api/:bu_code/documents/:filetoken/download` |
| Share a time-limited link | `GET /api/:bu_code/documents/:filetoken/presigned-url?expirySeconds=N` | Never embed permanent storage creds in the browser |
| Delete a stale file | Per-row delete (Sysadmin only) | Confirmation dialog; **hard delete** — dangling `fileToken`s render as "missing" on bound documents |
| Attach a file to a PR / PO / GRN | **NOT here** — use the transactional screen | This page is the registry, not per-document attachment management |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `fileSizeLimit` toast on upload | File > 10 MB | Compress / split before upload |
| File rejected by picker | MIME not in allow-list (`.pdf, .docx, .xls/.xlsx, .csv, .txt`) | Convert to an accepted format; `FILE_SERVICE` also sniffs server-side |
| "Missing" attachment on a PR/PO/GRN | File was hard-deleted from this registry while still referenced | Re-upload and re-attach; clean up dangling `fileToken`s manually |
| 403 on delete | User lacks `documents.delete` App ID | Grant via [access-control/application-role](/en/inventory/access-control/application-role) |
| File from BU `T01` invisible in BU `T02` | Expected — BU-scoped storage prefix | Each BU has its own partition; cross-BU access impossible |
| Presigned URL expired | `expirySeconds` elapsed | Request a new one |

## 4. Edge Cases

- **10 MB hard cap.** Enforced client-side *and* server-side. Larger files have no workaround in the current pipeline.
- **MIME allow-list at upload, broader categories at list.** Frontend filter recognises Image / Archive / Code so legacy uploads remain discoverable, but new uploads must land in the picker's allow-list. `FILE_SERVICE` performs defence-in-depth MIME sniffing server-side.
- **Hard delete, no cascade.** `DELETE` removes storage and sets `tb_attachment.deleted_at`; per-document `attachments` JSONB arrays are *not* cleaned up — dangling tokens render as "missing". Do not delete files still attached to in-flight documents.
- **No in-place versioning.** `tb_attachment.doc_version` defaults to `0` and is reserved; current pipeline overwrites by delete-and-re-upload.
- **Presigned URLs preferred over direct streaming** for browser sharing — never embed permanent storage credentials in the page.

---

## 5. Data Model (Dev)

The tenant schema does not have a `tb_document` table. Files are tracked in two places: a metadata mirror table and per-document JSONB arrays.

### 5.1 `tb_attachment` (file metadata mirror)

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `s3_token` | `String? @db.VarChar(255)` | Yes | Storage token returned by `FILE_SERVICE` — canonical handle downstream. |
| `s3_folder` | `String? @db.VarChar(255)` | Yes | Storage prefix (typically `<bu_code>/<yyyy-mm>/`). |
| `file_name` / `file_ext` / `file_type` | `String?` | Yes | Display name, extension, MIME. |
| `file_size` | `BigInt? @db.BigInt` | Yes | Bytes. |
| `file_url` | `String? @db.VarChar(255)` | Yes | Persistent URL (presigned URLs issued on demand, not stored). |
| `doc_version` | `Int` | No | Default `0`; reserved for future versioning. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([s3_token, deleted_at], map: "attachment_s3_token_u")` + index on `[s3_token]`. **No FKs out** — referential integrity to transactional documents lives in their `attachments` JSONB.

### 5.2 Per-document `attachments` JSONB

Every transactional table that supports attachments (`tb_purchase_request`, `tb_purchase_order`, `tb_goods_received_note`, `tb_store_requisition`, `tb_inventory_adjustment`, `tb_physical_count`, `tb_spot_check`, `tb_credit_note`, `tb_recipe`, `tb_product`, `tb_vendor`, `tb_tax_profile`, …) carries:

```jsonc
"attachments": [
  { "fileToken": "S3_UUID", "fileName": "vendor-invoice.pdf",
    "fileSize": 102400, "contentType": "application/pdf",
    "uploadedAt": "2026-05-15T08:00:00.000Z" }
]
```

`fileToken` matches `tb_attachment.s3_token`. The list endpoint queries `FILE_SERVICE` (source of truth), not `tb_attachment` directly.

### 5.3 `DocumentFile` API projection

`fileToken` (may carry `<buCode>/` prefix — stripped before delete) &nbsp;·&nbsp; `objectName` &nbsp;·&nbsp; `originalName` &nbsp;·&nbsp; `size` &nbsp;·&nbsp; `contentType` (drives type filter) &nbsp;·&nbsp; `lastModified`.

## 6. Business Rules

- **10 MB upload cap.** Client and server enforced.
- **MIME allow-list** on picker + server-side sniffing.
- **BU-scoped.** All endpoints under `/api/:bu_code/documents/*`; storage partitioned by `bu_code`.
- **Presigned URLs** for download / sharing — never embed permanent credentials.
- **AppId guards.** `documents.upload`, `documents.list`, `documents.get`, `documents.download`, `documents.info`, `documents.presignedUrl`, `documents.delete`. Non-admin = list / get / download only.
- **Hard delete.** Storage removed, `tb_attachment.deleted_at` set, per-document arrays *not* cascaded.
- **Audit logging** via `EnrichAuditUsers` (uploads, deletes; presigned-URL specifically *inferred — to be verified*).
- **No in-place versioning** — overwrite via delete + re-upload.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) / [purchase-order](/en/inventory/purchase-order) / [good-receive-note](/en/inventory/good-receive-note) / [store-requisition](/en/inventory/store-requisition) / [inventory-adjustment](/en/inventory/inventory-adjustment) / [physical-count](/en/inventory/physical-count) / [spot-check](/en/inventory/spot-check) — carry `attachments` JSONB.
- [master-data/vendor](/en/inventory/master-data/vendor) / [product](/en/inventory/product) — vendor and product master records carry their own `attachments` arrays.
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — cross-module attachment policy and visibility rules.
- [reporting-audit/report](/en/inventory/reporting-audit/report) — generated report artefacts land here via the same `fileToken` mechanism.
- [system-config/workflow](/en/inventory/system-config/workflow) — workflow comments embed `attachments` arrays for evidence files.
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — upload / delete / presigned-URL audit entries.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (lines ~4427-4449); per-document `attachments` JSONB columns throughout.
- **Backend controller:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.controller.ts`.
- **Backend service:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/document-management/document-management.service.ts` — forwards to `FILE_SERVICE` over `files.*` microservice commands.
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/system-admin/document/page.tsx` and `_components/document-component.tsx`.
- **Frontend hook:** `../carmen-inventory-frontend/hooks/use-document.ts` — `useDocument`, `useUploadDocument`, `useDeleteDocument`.
- **Frontend type:** `../carmen-inventory-frontend/types/document.ts` — `DocumentFile`.
