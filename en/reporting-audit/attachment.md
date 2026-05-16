---
title: Attachment
description: Generic file-storage entity — S3-backed binary metadata with polymorphic linkage to any transactional document.
published: true
date: 2026-05-16T08:00:00.000Z
tags: reporting-audit, attachment, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Attachment

## 1. Purpose

The attachment entity is the **shared binary metadata catalogue** for every document module that needs to store files. Quotations on a PR, vendor confirmations on a PO, signed delivery dockets on a GRN, count sheets on a physical count, photos on a spot check — they all land in `tb_attachment` and link back to the owning row through application-side polymorphism (no in-schema FK). The row carries the S3 token and folder, original file metadata (name, extension, type, size), a public/signed URL, free-form `info`, and a `doc_version` integer used to track regenerated documents (e.g. PDF re-rendered after a status change).

The entity is intentionally generic — the schema has no `document_type` discriminator on the attachment side. The convention is that the *owning* table holds the FK columns (or join table) to attachment rows. This keeps `tb_attachment` cheap to query by `s3_token` (which is unique among non-deleted rows) and lets each owning module enforce its own visibility rules without leaking into this table.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_attachment`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `s3_token` | `String? @db.VarChar(255)` | Yes | Opaque S3 object key (or compatible blob storage key). Unique among non-deleted rows. |
| `s3_folder` | `String? @db.VarChar(255)` | Yes | Logical folder / bucket prefix. |
| `file_name` | `String? @db.VarChar(255)` | Yes | Original filename as uploaded. |
| `file_ext` | `String? @db.VarChar(255)` | Yes | File extension (`pdf`, `xlsx`, `jpg`, …). |
| `file_type` | `String? @db.VarChar(255)` | Yes | MIME type (`application/pdf`, `image/jpeg`, …). |
| `file_size` | `BigInt? @db.BigInt` | Yes | Size in bytes. |
| `file_url` | `String? @db.VarChar(255)` | Yes | Resolved URL (signed or public) — may be a CDN endpoint. |
| `info` | `Json? @db.Json` | Yes | Free-form metadata (uploader app, original SHA, tags). |
| `doc_version` | `Int @db.Integer` | No | Default `0`. Incremented when the underlying document is re-rendered (e.g. PR PDF regenerated). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:**
- `@@unique([s3_token, deleted_at])` map `attachment_s3_token_u` — combined with `deleted_at` so soft-deleted rows do not block re-upload to the same token.
- `@@index([s3_token])` map `attachment_s3_token_idx`.
- No FK columns: linkage to the owning document is held on the owning table (FK column or join row).

## 3. Usage / Cross-References

- [[purchase-request]] — quotations, vendor proposals, internal justification documents attached at header level.
- [[purchase-order]] — vendor-signed confirmations and amendments.
- [[good-receive-note]] — delivery dockets, photo proof of condition, signed receipts.
- [[inventory-adjustment]] — supporting paperwork for write-offs.
- [[physical-count]] — scanned tally sheets and variance approvals.
- [[spot-check]] — photo evidence of count discrepancies.
- [[store-requisition]] — supporting forms or approvals.
- [[vendor-pricelist]] — uploaded price-list spreadsheets and contracts.
- [[recipe]] — yield-test sheets, photos of plated dishes.
- [[product]] — product photos, spec sheets.
- [[reporting-audit/activity]] — `upload` and `download` actions are logged via the activity log with `entity_type = 'attachment'`.

## 4. Configuration UI

There is no dedicated CRUD screen for attachments in isolation. Each owning module exposes its own **Attachments** tab or sidebar drawer that uploads to S3, persists a row to `tb_attachment`, and writes the FK back to the owning row in the same transaction. Roles follow the owning module — a user who can edit a PR can attach files to it; a user who can only view it can download but not upload.

## 5. Business Rules

- **Uniqueness.** `s3_token` is unique among non-deleted rows. Re-uploading the same blob after a soft-delete is allowed because the unique constraint includes `deleted_at`.
- **Soft-delete semantics.** A `deleted_at` row hides the attachment from owning-module UIs but does not remove the S3 object — a garbage-collection job reaps blobs whose row has been soft-deleted for longer than the retention horizon.
- **doc_version.** Owning modules increment `doc_version` when the underlying document is re-rendered (e.g. PR PDF after stage advance). Older versions are kept for audit and downloadable from the activity history.
- **No polymorphic FK enforced.** The FK from the owning row to `tb_attachment.id` is unenforced from the attachment side. Orphaned rows (owning row deleted, attachment still present) are reaped by the same retention job that handles S3.
- **URL lifecycle.** `file_url` may be a short-lived signed URL — UIs should re-resolve through the S3 service rather than caching the URL across sessions.
- **MIME / extension trust.** Both `file_type` and `file_ext` are taken from the client and not re-verified server-side; downstream code must not rely on them for security decisions.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_attachment` (lines ~4427-4449).
- **Frontend route (if known):** Attachments are surfaced in-document under each module's detail screen, e.g. `../carmen-turborepo-frontend/apps/web/app/(app)/procurement/purchase-request/[id]/`. The blob upload flow is in the shared `attachment` service module.
- **Cross-module:** see Section 3.
