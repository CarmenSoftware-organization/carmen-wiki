---
title: Credit Note Reason
description: Coded reasons for credit notes raised against GRN — supports the return-to-vendor and price-correction flows.
published: true
date: 2026-05-16T08:00:00.000Z
tags: master-data, credit-note-reason, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Credit Note Reason

## 1. Purpose

A credit note records goods returned to the vendor or a price correction against a previously received delivery. The credit-note reason is the *why* — damaged goods, wrong item shipped, agreed price reduction, expiry, etc. Every credit note header references one of these reasons, and downstream reporting groups CN volume by reason to spot quality / vendor issues.

The entity is a flat lookup table; reason logic (return-to-stock vs. write-off) lives in the credit-note flow itself, not on the reason record.

## 2. Prisma Model(s)

Source: tenant schema.

### 2.1 `tb_credit_note_reason`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Damaged on receipt`, `Price correction`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `creditnotereason_name_u`. Index on `name`. Reverse relation to `tb_credit_note`. Note: no `is_active` column — lifecycle is via soft-delete only.

## 3. Usage / Cross-References

- [[good-receive-note]] — credit notes are raised in the GRN context (return-to-vendor flow). Reason FK lives on `tb_credit_note`.
- [[inventory-adjustment]] — if the credit-note posting requires a stock adjustment (e.g. write-off rather than return-to-stock), the adjustment carries its own `[[master-data/adjustment-type]]` while the parent CN keeps the reason.

## 4. Configuration UI

Managed by **Product Admin** under the Master Data area. Simple list + edit dialog (name, description).

## 5. Business Rules

- **Uniqueness.** `name` is unique among non-deleted rows (DB-enforced).
- **Deletion guards.** A reason referenced by any credit note cannot be hard-deleted. Soft-delete via `deleted_at` only if the reason is to be retired and no historical CNs reference it (or if downstream reports can tolerate "Unknown reason" rendering).
- **Validation.** `name` is required.
- **Lifecycle.** No `is_active` flag — to retire a reason, soft-delete it. Historical credit notes keep the FK and resolve the name via lookup even on a soft-deleted row.
- **Translation.** Reasons are often shown to vendors — translations should live in `info` JSON until a localisation table is introduced.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note_reason` (lines ~299-319), used by `tb_credit_note` (lines ~321-…).
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/credit-note-reason/`.
- **Cross-module:** see Section 3.
