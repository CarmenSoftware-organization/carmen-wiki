---
title: Running Code
description: Document-number generator configuration — prefix, date token, and running counter pattern per document type (PR, PO, GRN, SR, etc.).
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, running-code, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Running Code

> **At a Glance**
> **Owner:** Sysadmin &nbsp;·&nbsp; **Table:** `tb_config_running_code` &nbsp;·&nbsp; **Used by:** numbering service on every document create &nbsp;·&nbsp; Document-numbering rules — `PR202605-00001` etc.

![Running Code screen](/screenshots/system-config/running-code.png)

## 1. What & Who

Running codes are the **document-numbering rules** for every transactional document type. A row defines the prefix, optional date token, and zero-padded running counter — assembled into a `format` string — which the numbering service consumes at document-create time to mint a human-readable reference like `PR202605-00001`.

The system is keyed by `type` (one row per document type — `PR`, `PO`, `GRN`, `SR`, `IA`, etc.) with the entire pattern captured inside the `config` JSONB column. Keeping the pattern as data lets a property change `PR-YYYYMM-NNNN` to `REQ-2026-NNNNN` without a code deploy.

**Maintained by** Sysadmin. **Read by** the numbering service on every new document.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Change pattern for a document type | System Config → Running Code → edit row | Inline segment editor + preview |
| Add running code for a new doc type | System Config → Running Code → New | Pick `type` (e.g. `IA`), define segments |
| Widen counter (e.g. 4→5 digits) | Edit `C` segment width | Takes effect at next mint; historical refs unchanged |
| Preview next three numbers | Preview field on row | Verifies pattern before save |
| Retire a document type | Soft-delete the row | Only on retired types not in active use |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Duplicate type" | Existing non-deleted row | Edit existing row instead |
| Counter unexpectedly restarted | Dated segment changed | Counter scoped by `type + dated-segment` — adding `yyyyMM` restarts monthly |
| Format placeholder missing | `format` references undefined segment | Add segment or remove placeholder |
| Document number collision | Counter persistence bug or manual edit | Reset numbering service counter; investigate |
| Cannot delete | Active document type | Soft-delete only after retirement |

## 4. Edge Cases

- **Counter scope.** Implicit — scoped by `type + dated-segment`. Without a dated segment, counter is global per type.
- **Counter persistence** is service state (advisory lock / sequence), not this table — this entity defines the *pattern* only.
- **Pattern changes mid-period** take effect at next mint; existing references render as stored.
- **Format must reference at least one segment** — unreferenced segments allowed but warned in UI.

---

## 5. Data Model (Dev)

Source: tenant schema.

### 5.1 `tb_config_running_code`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `type` | `String? @db.VarChar(255)` | Yes | Document type discriminator (`PR`, `PO`, `GRN`, `SR`, `IA`, …). Effectively required by uniqueness. |
| `config` | `Json? @db.JsonB` | Yes | Pattern definition. Default `{}`. |
| `note` | `String? @db.VarChar` | Yes | Free-text note. |
| `info` | `Json? @db.JsonB` | Yes | Free-form metadata. |
| `doc_version` | `Int` | No | Optimistic-concurrency token. |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([type, deleted_at])`. Index on `[type]`. Reverse relation to `tb_config_running_code_comment`.

### 5.2 `config` JSONB shape

Observed in seed data:

```
{
  "A": "PR",                  // segment A: static prefix
  "B": "date('yyyyMM')",      // segment B: dated token, evaluated at mint
  "C": "running(5, '0')",     // segment C: running counter, 5 digits, zero-padded
  "format": "{A}{B}{C}"       // assembly template
}
```

**Tokens:** `Static` (literal string), `date('<pattern>')` (date-fns-style), `running(<width>, '<pad>')` (zero-padded sequence; scope = per `type` + dated segment), `format` (template with `{A}`, `{B}`, `{C}` placeholders + separators).

## 6. Business Rules

- **Uniqueness.** `type` unique among non-deleted — one pattern per doc type.
- **Counter scope.** Implicit per `type + dated-segment`; global per type without a dated segment.
- **Counter persistence.** Service state, not this table.
- **Format validation.** Must reference at least one segment; unreferenced segments allowed but warned.
- **Pattern changes** take effect at next mint; historical references unchanged.
- **Deletion guards.** Active types cannot be deleted; soft-delete only on retired types.

## 7. Cross-References

- [purchase-request](/en/inventory/purchase-request) — `pr_no`.
- [purchase-order](/en/inventory/purchase-order) — `po_no`.
- [good-receive-note](/en/inventory/good-receive-note) — GRN reference.
- [store-requisition](/en/inventory/store-requisition) — SR reference.
- [inventory-adjustment](/en/inventory/inventory-adjustment) — IA / SI / SO references.
- [physical-count](/en/inventory/physical-count), [spot-check](/en/inventory/spot-check) — count document numbering.
- [vendor-pricelist](/en/inventory/vendor-pricelist) — pricelist reference.

## 8. References

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_config_running_code` (lines ~4493-4512).
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_config_running_code.json`.
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/running-code/`.
