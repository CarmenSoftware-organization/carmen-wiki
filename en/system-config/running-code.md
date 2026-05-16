---
title: Running Code
description: Document-number generator configuration — prefix, date token, and running counter pattern per document type (PR, PO, GRN, SR, etc.).
published: true
date: 2026-05-16T08:00:00.000Z
tags: system-config, running-code, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Running Code

## 1. Purpose

Running codes are the **document-numbering rules** for every transactional document type. A row defines the prefix, optional date token, and a zero-padded running counter — assembled into a `format` string — which the numbering service consumes at document-create time to mint a human-readable reference like `PR202605-00001`.

The system is keyed by `type` (one row per document type — `PR`, `PO`, `GRN`, `SR`, `IA`, etc.) with the entire pattern captured inside the `config` JSONB column. Keeping the pattern as data rather than hardcoded application logic lets a property change `PR-YYYYMM-NNNN` to `REQ-2026-NNNNN` without a code deploy.

## 2. Prisma Model(s)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`).

### 2.1 `tb_config_running_code`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `type` | `String? @db.VarChar(255)` | Yes | Document type discriminator (`PR`, `PO`, `GRN`, `SR`, `IA`, etc.). Effectively required by uniqueness. |
| `config` | `Json? @db.JsonB` | Yes | Pattern definition. Default `{}`. Shape described below. |
| `note` | `String? @db.VarChar` | Yes | Free-text note. |
| `info` | `Json? @db.JsonB` | Yes | Free-form metadata. |
| `doc_version` | `Int` | No | Optimistic-concurrency token. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([type, deleted_at])` map `config_running_code_type_u`. Index on `[type]`. Reverse relation to `tb_config_running_code_comment`.

### 2.2 `config` JSONB shape

Observed in seed data:

```jsonc
{
  "A": "PR",                  // segment A: static prefix
  "B": "date('yyyyMM')",      // segment B: dated token, evaluated at mint time
  "C": "running(5, '0')",     // segment C: running counter, 5 digits, zero-padded
  "format": "{A}{B}{C}"       // assembly template using {A}, {B}, {C} placeholders
}
```

Token grammar:

- **Static** — any literal string (`"PR"`, `"GRN"`).
- **Date** — `date('<pattern>')` using a date-fns-style pattern (`yyyyMM`, `yyyy`, `yyMMdd`).
- **Running** — `running(<width>, '<pad-char>')` — zero-padded sequence number. Counter scope is per `type` + the dated segment (so each month restarts the counter when the pattern includes a `yyyyMM` token).
- **Format** — a template string with `{A}`, `{B}`, `{C}` (more segments may be added) controlling assembly order and any literal separators.

## 3. Usage / Cross-References

- [[purchase-request]] — `tb_purchase_request.pr_no` is minted from the `PR` row.
- [[purchase-order]] — `tb_purchase_order.po_no` is minted from the `PO` row.
- [[good-receive-note]] — GRN reference number uses the `GRN` row.
- [[store-requisition]] — SR reference number uses the `SR` row.
- [[inventory-adjustment]] — stock-in / stock-out documents use the `IA` (or split `SI` / `SO`) rows.
- [[physical-count]] — count document numbering.
- [[spot-check]] — spot-check document numbering.
- [[vendor-pricelist]] — pricelist reference numbering.

## 4. Configuration UI

Managed by **Sysadmin** under System Configuration → Running Code. Each document type appears as a row with an inline editor for the pattern segments and a *Preview* field that mints the next-three sample numbers using the current pattern. Changing the pattern does *not* renumber historical documents; new documents from that moment forward use the new pattern.

## 5. Business Rules

- **Uniqueness.** `type` is unique among non-deleted rows — one pattern per document type.
- **Counter scope.** The running counter is implicitly scoped by the dated segment. With pattern `{A}{date('yyyyMM')}{running(5)}`, August and September both start at `00001`. Without a dated segment, the counter is global per type.
- **Counter persistence.** The current counter is managed by the numbering service (typically using `pg_advisory_lock` or a sequence keyed on `type + dated-segment`) — not by this table. This entity defines the *pattern*; the *next value* is service state.
- **Format validation.** The `format` string must reference at least one segment placeholder. Unreferenced segments are allowed (admin draft state) but warned in the UI.
- **Pattern changes mid-period.** Changing the pattern (e.g. widening the counter from 4 to 5 digits) on a live document type takes effect at the next mint. Existing references render as stored.
- **Deletion guards.** A row whose `type` is in active use by any document module cannot be deleted. Soft-delete only on retired document types.

## 6. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_config_running_code` (lines ~4493-4512).
- **Seed example:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_config_running_code.json`.
- **Frontend route (if known):** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/running-code/`.
- **Cross-module:** see Section 3.
