---
title: Running Code
description: Document-number generator configuration — prefix, date token, and running counter pattern per document type (PR, PO, GRN, SR, etc.). The admin screen is a plain type + raw-JSON-textarea dialog, not a segment editor with a live preview.
published: true
date: 2026-07-16T00:00:00.000Z
tags: system-config, running-code, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Running Code

> **At a Glance**
> **Owner:** Sysadmin &nbsp;·&nbsp; **Table:** `tb_config_running_code` &nbsp;·&nbsp; **Used by:** numbering service on every document create &nbsp;·&nbsp; Document-numbering rules — `PR202605-00001` etc. &nbsp;·&nbsp; **Admin screen edits the `config` JSONB as raw text — there is no per-segment (prefix/date/counter) editor or live number preview.**

![Running Code screen](/screenshots/system-config/running-code.png)

## Implementation status (verified 2026-07-16)

The `/system-admin/running-code` edit dialog (`running-code-dialog.tsx` + `running-code-form-schema.ts`) is a **plain type text input + a raw JSON textarea** for `config` (max 256 characters), with a single "Format" button that only pretty-prints the JSON (`JSON.stringify(parsed, null, 2)`) — it does not validate the pattern's shape beyond "is this valid JSON." There is no per-segment (`A`/`B`/`C`) width editor, no drag-reorder, and no live "preview next three numbers" field anywhere in the component. `type` is a free-text field (not a picker constrained to a fixed enum), and it becomes read-only once a row exists (`disabled={isPending || isEdit}`). The underlying `config` JSONB pattern language (`date('yyyyMM')`, `running(5,'0')`, `format` template) **is real and actively consumed** by `GenerateCode`/`getPattern` in `common/helpers/running-code.helper.ts` (confirmed via that file's own unit tests) — only the admin-screen UX description below has been corrected; §5's data-model documentation of the pattern language is unchanged and accurate.

## 1. What & Who

Running codes are the **document-numbering rules** for every transactional document type. A row defines the prefix, optional date token, and zero-padded running counter — assembled into a `format` string — which the numbering service consumes at document-create time to mint a human-readable reference like `PR202605-00001`. This pattern is authored as raw JSON text, not through a structured segment builder (see Implementation status).

The system is keyed by `type` (one row per document type — `PR`, `PO`, `GRN`, `SR`, `IA`, etc.) with the entire pattern captured inside the `config` JSONB column. Keeping the pattern as data lets a property change `PR-YYYYMM-NNNN` to `REQ-2026-NNNNN` without a code deploy — but doing so today means hand-editing JSON, not filling in a segment form.

**Maintained by** Sysadmin. **Read by** the numbering service on every new document.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Change pattern for a document type | System Config → Running Code → edit row → **Config** textarea | Raw JSON edit; use **Format** to pretty-print, not to validate the pattern semantics |
| Add running code for a new doc type | System Config → Running Code → New | Free-text `type` field (not a picker) + raw JSON `config` |
| Widen counter (e.g. 4→5 digits) | Hand-edit the `C` segment's `running(<width>, '0')` value in the JSON textarea | Takes effect at next mint; historical refs unchanged |
| Preview next three numbers | ~~Preview field on row~~ | **No such field exists** — there is no live preview anywhere in the dialog |
| Retire a document type | Soft-delete the row | Only on retired types not in active use |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Duplicate type" | Existing non-deleted row | Edit existing row instead |
| Textarea rejects the value on save | `config` is not valid JSON | Fix syntax; the form only checks `JSON.parse` succeeds, not that the shape is a usable pattern |
| Counter unexpectedly restarted | Dated segment changed | Counter scoped by `type + dated-segment` — adding `yyyyMM` restarts monthly |
| Format placeholder missing | `format` references undefined segment | Add segment or remove placeholder — not caught by the form, only surfaces at document-create time |
| Document number collision | Counter persistence bug or manual edit | Reset numbering service counter; investigate |
| Cannot delete | Active document type | Soft-delete only after retirement |

## 4. Edge Cases

- **No structured editor or preview.** Confirmed: the dialog is a bare JSON textarea with a format-only "Format" button; malformed *pattern* semantics (e.g. a `format` string referencing an undefined segment) pass client-side validation and only fail when a document is actually created.
- **Counter scope.** Implicit — scoped by `type + dated-segment`. Without a dated segment, counter is global per type.
- **Counter persistence** is service state (advisory lock / sequence), not this table — this entity defines the *pattern* only.
- **Pattern changes mid-period** take effect at next mint; existing references render as stored.
- **Format must reference at least one segment** — unreferenced segments allowed; no UI warning was found for this (contrary to a prior version of this page).

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
- **Format validation.** Must reference at least one segment to be usable at mint time; the admin form does not check this — only that `config` parses as JSON.
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

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_config_running_code` (lines ~4864-4883).
- **Backend pattern logic:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/helpers/running-code.helper.ts` — `GenerateCode`, `getPattern` (confirmed via `running-code.helper.spec.ts`, `common.helper.spec.ts`).
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_config_running_code.json`.
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/running-code/` — `running-code-component.tsx` (list), `running-code-dialog.tsx` (raw-JSON create/edit), `running-code-form-schema.ts`.
