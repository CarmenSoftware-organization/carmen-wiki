---
title: Credit Note Reason
description: Coded reasons for credit notes raised against GRN — supports the return-to-vendor and price-correction flows.
published: true
date: 2026-07-15T21:47:09.000Z
tags: master-data, credit-note-reason, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Credit Note Reason

> **At a Glance**
> **Owner:** Product Admin &nbsp;·&nbsp; **Table:** `tb_credit_note_reason` &nbsp;·&nbsp; **Used by:** credit-note flow (return-to-vendor, price correction) &nbsp;·&nbsp; The *why* behind every credit note raised against a GRN.

![Credit Note Reason screen](/screenshots/master-data/credit-note-reason.png)

## 1. What & Who

A **credit note** records goods returned to the vendor or a price correction against a previously received delivery. The **credit-note reason** is the *why* — damaged goods, wrong item shipped, agreed price reduction, expiry, etc. Every credit note header references one of these reasons, and downstream reporting groups CN volume by reason to spot quality / vendor issues.

The entity is a **flat lookup** — reason logic (return-to-stock vs. write-off) lives in the credit-note flow itself, not on the reason record. **Maintained by** Product Admin; **read by** developers and testers on the GRN credit-note path.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add a new reason | Configuration → Master Data → Credit Note Reason → **New** | Required: `name`; optional `description` |
| Edit description | Edit dialog | Renaming changes display everywhere historical CNs are listed |
| Retire a reason | Soft-delete (set `deleted_at`) | No `is_active` flag — soft-delete is the only retirement path |
| Check which reason a CN used | Open the credit note header | Reason FK on `tb_credit_note` |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| "Name already in use" | Duplicate `name` on a non-deleted row | Pick a different name or restore the existing row |
| "Name required" | Empty `name` | Add a display name |
| **Unconfirmed** — no delete guard found | `credit-note-reason.service.ts`'s `delete()` is an unconditional soft-delete with no check for existing credit-note references | A prior version of this page asserted "cannot delete — referenced by credit notes" as an enforced error; treat it as **not enforced** until re-verified — soft-deleting a reason still in use will currently succeed, and since the reason has no `is_active` flag, this is also the only "retire" path |
| Reason shows blank on a CN | Hard-delete somehow succeeded (data fix only) | Restore or backfill via lookup |

## 4. Edge Cases

- **No `is_active` column** — lifecycle is via soft-delete only.
- **Rename propagation** — display refreshes automatically because CNs hold the FK, not the text.
- **Soft-deleted rows still resolvable** by lookup, so historical CNs continue to render.
- **Translation.** Reasons are often shown to vendors. Until a localisation table exists, translations live in `info` JSON.
- **Adjustment-type vs. reason.** If a CN posts a stock adjustment (write-off rather than return-to-stock), the adjustment carries its own [master-data/adjustment-type](/en/inventory/master-data/adjustment-type) while the parent CN keeps the reason.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_credit_note_reason`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `name` | `String @db.VarChar` | No | Display name (e.g. `Damaged on receipt`, `Price correction`). |
| `description` | `String? @db.VarChar` | Yes | Free text. |
| `note` | `String? @db.VarChar` | Yes | Internal note. |
| `info`, `dimension` | `Json?` | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([name, deleted_at])` map `creditnotereason_name_u`. Index on `name`. Reverse relation to `tb_credit_note`. Note: no `is_active` column.

## 6. Business Rules

- **Uniqueness.** `name` unique among non-deleted rows (DB-enforced).
- **Deletion guards — unconfirmed.** No reference check was found in `delete()`; soft-delete succeeds unconditionally even with credit-note references.
- **Validation.** `name` required.
- **Lifecycle.** No `is_active`; soft-delete is the retirement path. Historical CNs keep the FK and resolve the name even on a soft-deleted row.
- **Translation.** Reasons may face vendors — keep translations in `info` until a localisation table is introduced.

## 7. Cross-References

- [good-receive-note](/en/inventory/good-receive-note) — credit notes are raised in the GRN context. Reason FK on `tb_credit_note`.
- [inventory-adjustment](/en/inventory/inventory-adjustment) — when a CN posts a stock adjustment, the adjustment carries an [master-data/adjustment-type](/en/inventory/master-data/adjustment-type) in addition to the CN reason.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note_reason` (lines ~303-324).
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/credit-note-reason/credit-note-reason.service.ts` (lives under `procurement`, not `master`, in the backend's own module layout).
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/credit-note-reason/`.
