---
title: Attachment
description: Generic file-storage entity — S3-backed binary metadata with polymorphic linkage to any transactional document.
published: true
date: 2026-05-17T11:00:00.000Z
tags: reporting-audit, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Attachment

> **At a Glance**
> **Owner:** Owning module (PR, PO, GRN, …) &nbsp;·&nbsp; **Table:** `tb_attachment` &nbsp;·&nbsp; **Used by:** every module with file uploads &nbsp;·&nbsp; Generic file-metadata catalogue — S3-backed, polymorphic linkage from owning module.

## 1. What & Who

The attachment entity is the **shared binary metadata catalogue** for every module that stores files. Quotations on a PR, vendor confirmations on a PO, signed delivery dockets on a GRN, count sheets on a physical count, photos on a spot check — all land in `tb_attachment` and link back through application-side polymorphism (no in-schema FK from this table). Each row carries the S3 token + folder, original file metadata (name, ext, type, size), a public/signed URL, free-form `info`, and a `doc_version` integer for regenerated documents (e.g. re-rendered PDF).

The entity is intentionally generic — no `document_type` discriminator. The convention is that the **owning** table holds the FK columns to attachment rows.

**Maintained by** the owning module's upload flow. **Read by** the owning module's detail screens.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Attach a file to a document | Document detail → **Attachments** tab → Upload | Writes `tb_attachment` row + FK on owning table |
| Download attachment | Click filename | Re-resolves through S3 service (URLs may be signed/short-lived) |
| Remove an attachment | Attachments tab → Delete | Soft-deletes the row; S3 blob reaped by GC job |
| Re-render a document PDF | Owning module print action | Increments `doc_version`; older versions retained for audit |
| Replace an uploaded file | Soft-delete old + upload new | `s3_token` unique among non-deleted rows |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Duplicate s3_token" | Existing non-deleted row | Soft-delete or use a different token |
| Broken file_url | Signed URL expired | Re-resolve via S3 service rather than caching |
| File missing in S3 but row exists | GC mismatch / external deletion | Orphan; reaped by retention job |
| MIME mismatch | `file_type` taken from client, not re-verified | Do NOT rely on `file_type`/`file_ext` for security |

## 4. Edge Cases

- **Soft-delete semantics.** `deleted_at` hides from UI but does not remove the S3 object — GC reaps after retention.
- **No polymorphic FK enforced.** Owning row deletes can orphan attachment rows; same GC handles cleanup.
- **`doc_version` increment.** Owning modules bump when re-rendering (e.g. PR PDF after stage advance); older versions stay downloadable from activity history.
- **MIME / extension trust.** Both come from client; downstream code must not rely on them for security.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_attachment`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `s3_token` | `String? @db.VarChar(255)` | Yes | Opaque S3 object key. Unique among non-deleted rows. |
| `s3_folder` | `String? @db.VarChar(255)` | Yes | Logical folder / bucket prefix. |
| `file_name` | `String? @db.VarChar(255)` | Yes | Original filename. |
| `file_ext` | `String? @db.VarChar(255)` | Yes | Extension (`pdf`, `xlsx`, `jpg`, …). |
| `file_type` | `String? @db.VarChar(255)` | Yes | MIME type. |
| `file_size` | `BigInt? @db.BigInt` | Yes | Bytes. |
| `file_url` | `String? @db.VarChar(255)` | Yes | Resolved URL (signed or public). |
| `info` | `Json? @db.Json` | Yes | Free-form metadata. |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Incremented on re-render. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([s3_token, deleted_at])` map `attachment_s3_token_u`. `@@index([s3_token])`. No FK columns — linkage on owning table.

## 6. Business Rules

- **Uniqueness.** `s3_token` unique among non-deleted; constraint includes `deleted_at` so re-upload after soft-delete is allowed.
- **Soft-delete semantics.** Row hidden; S3 blob reaped by retention GC.
- **`doc_version` increment.** Owning modules bump on re-render; older versions retained.
- **No FK enforcement.** Orphans handled by retention job.
- **URL lifecycle.** Re-resolve via S3 service; do not cache `file_url` across sessions.
- **MIME / extension trust.** Client-provided, server-unverified — do not use for security decisions.

## 7. Cross-References

- [[purchase-request]], [[purchase-order]], [[good-receive-note]] — quotations, confirmations, dockets.
- [[inventory-adjustment]], [[physical-count]], [[spot-check]] — supporting paperwork and evidence.
- [[store-requisition]], [[vendor-pricelist]], [[recipe]], [[product]] — module-specific attachments.
- [[reporting-audit/activity]] — `upload` / `download` logged with `entity_type = 'attachment'`.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (lines ~4427-4449).
- **Frontend:** Embedded in each module's detail screen (e.g. `.../purchase-request/[id]/`). Shared `attachment` service handles blob upload.
