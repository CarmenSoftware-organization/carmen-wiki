---
title: Running Code
description: Document-number patterns — prefix, date token, running counter per document type (PR, PO, GRN, SR, GL-JV, …). Since 2026-08-27 the admin dialog is a part-by-part editor with live preview; raw JSON is a collapsed fallback.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: system-config, running-code, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Running Code

> **At a Glance**
> **Owner:** Sysadmin &nbsp;·&nbsp; **Table:** `tb_config_running_code` &nbsp;·&nbsp; **Route:** `/system-admin/running-code` &nbsp;·&nbsp; **Permission / licence:** `system_admin.running_code` &nbsp;·&nbsp; **Used by:** numbering service on every document create &nbsp;·&nbsp; Document-numbering rules — `PR202605-00001` etc. &nbsp;·&nbsp; **Admin dialog is a part-by-part editor (text / date / running / token) with a live preview since 2026-08-27; the raw `config` JSON is kept as a collapsed "Advanced" fallback.**

![Running Code screen](/screenshots/system-config/running-code.png)

## Implementation status (verified 2026-07-16; re-verified 2026-09-22)

**The 2026-07-16 finding is superseded.** FE commit `704f1f9f` (2026-08-27, *"edit the document-number format part by part instead of typing JSON"*) replaced the raw textarea with a structured editor:

- `running-code-config.ts` parses the backend's `{ A, B, C, …, format }` JSON into an ordered list of **parts** — `text` (literal), `date` (`date('<pattern>')`), `running` (`running(<digits>, '<pad>')`), `token` (`{name}`) — and serialises it back, re-lettering the slots `A`, `B`, `C`… (`slotName()`) on every save. The admin never sees the letters or the word `format`.
- `running-code-config-fields.tsx` renders the parts with add/remove/reorder controls and a **live preview** (`previewCode(parts, now)`) of the next number.
- Keys present in `config` but not referenced by `format` are preserved in `extra` and written back untouched, so editing a prefix cannot silently drop unknown keys.
- The raw JSON textarea still exists, collapsed under **Advanced config** (`running-code-dialog.tsx:185-245`) with the pretty-print button; when `parseConfig()` returns `null` (no `format`, or `format` references a missing slot) the structured editor is disabled with a `configUnreadable` notice and the JSON textarea opens for manual repair.
- `type` remains a free-text input that becomes read-only once a row exists (`disabled={isPending || isEdit}`, `:172`).

The underlying pattern language (`date('yyyyMM')`, `running(5,'0')`, `format` template) is unchanged and still consumed by `GenerateCode`/`getPattern` in `common/helpers/running-code.helper.ts`. Backend fallback: when a BU has no row for a type, `getRunningPattern()` reads `RUNNING_CODE_PRESET[type].config` (`apps/micro-business/src/master/running-code/const/running-code.const.ts`) — presets exist for `PURCHASE-REQUEST`, `PURCHASE-ORDER`, `GOOD-RECEIVED-NOTE`, `CREDIT-NOTE`, `PRICE-LIST`, `STOCK-IN`, `STOCK-OUT`, `STORE-REQUISITION`, `SPOT-CHECK`, `PHYSICAL-COUNT`, `PRODUCT-CAT`, `PRODUCT-SUB-CAT`, `PRODUCT-ITEM-GROUP`, `PRODUCT`, and since 2026-09-15 `GL-JV` (`27f65cba1` — the missing preset made the first JV of every BU fail with a 500). There is **no guard** for a type outside the preset: a document type with neither a row nor a preset still crashes at number generation.

## 1. What & Who

Running codes are the **document-numbering rules** for every transactional document type. A row defines the prefix, optional date token, and zero-padded running counter — assembled into a `format` string — which the numbering service consumes at document-create time to mint a human-readable reference like `PR202605-00001`. Since 2026-08-27 the pattern is authored through a structured part editor with a live preview (see Implementation status); the JSON is a storage detail.

The system is keyed by `type` (one row per document type — the preset keys above; note the seed/preset spelling is `PURCHASE-REQUEST`, `GOOD-RECEIVED-NOTE`, `GL-JV`, not `PR`/`GRN`) with the entire pattern captured inside the `config` JSONB column. Keeping the pattern as data lets a property change `PR-YYYYMM-NNNN` to `REQ-2026-NNNNN` without a code deploy.

**Maintained by** Sysadmin. **Read by** the numbering service on every new document.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Change pattern for a document type | System Admin → Running Code → edit row → add / edit / reorder **parts** | Preview updates live; **Advanced config** shows the JSON that will be saved |
| Add running code for a new doc type | System Admin → Running Code → New | Free-text `type` field (not a picker; use the preset spelling) + parts |
| Widen counter (e.g. 4→5 digits) | Edit the **Running** part's digits | Takes effect at next mint; historical refs unchanged |
| Preview the next number | Preview line in the dialog (`previewLabel`) | Renders the parts with today's date and sequence 1 — it does not read the real counter |
| Repair an unreadable config | Dialog shows `configUnreadable` and opens **Advanced config** | Fix `format` / slot references in the JSON, then the part editor re-enables |
| Retire a document type | Soft-delete the row | Only on retired types not in active use |

## 3. Validation & Errors

| Symptom | Cause | Action |
|---|---|---|
| "Duplicate type" | Existing non-deleted row | Edit existing row instead |
| Advanced-config textarea rejects the value on save | `config` is not valid JSON | Fix syntax |
| Part editor disabled, `configUnreadable` shown | `config` has no `format`, or `format` references a slot that does not exist | Repair in Advanced config; the editor refuses to guess and overwrite |
| Counter unexpectedly restarted | Dated segment changed | Counter scoped by `type + dated-segment` — adding `yyyyMM` restarts monthly |
| 500 `Cannot read properties of undefined (reading 'config')` on first document of a type | BU has no row for the type **and** no preset (`RUNNING_CODE_PRESET`) | Add the row here, or a preset in code (`GL-JV` was fixed this way on 2026-09-15) |
| Document number collision | Counter persistence bug or manual edit | Reset numbering service counter; investigate |
| Cannot delete | Active document type | Soft-delete only after retirement |

## 4. Edge Cases

- **Structured editor with a JSON escape hatch.** The part editor guarantees a consistent `format` for anything it saves; only the Advanced-config path can still store a `format` that references an undefined slot, which then fails at document-create time.
- **`GL-JV` has no literal prefix part on purpose** — the prefix lives on `tb_gl_jv_header.prefix_code` and `jv_no` holds only `date('yyyyMM') + running(5,'0')`; adding a literal would break the GL module's `startsWith` lookup and counter reset (`running-code.const.ts:119`).
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
- **Format validation.** Must reference at least one segment to be usable at mint time; the part editor always emits a consistent `format`, the Advanced-config textarea only checks that `config` parses as JSON.
- **Preset fallback.** A BU without a row for a type uses `RUNNING_CODE_PRESET[type]`; a type with neither fails hard.
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
- **Backend pattern logic:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/helpers/running-code.helper.ts` — `GenerateCode`, `getPattern`; presets `apps/micro-business/src/master/running-code/const/running-code.const.ts` (`RUNNING_CODE_PRESET`); service `apps/micro-business/src/master/running-code/running-code.service.ts` (`update` is `doc_version`-guarded, `:301`).
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_running-codes/` — `api/config/:bu_code/running-codes`; licence `system_admin.running_code` (`permission.route-map.ts:121`).
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_config_running_code.json`; `packages/prisma-shared-schema-tenant/src/seed-data/running-code.ts` (includes `GL-JV`).
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/running-code/` — `running-code-component.tsx` (list), `running-code-dialog.tsx` (create/edit), `running-code-config-fields.tsx` (part editor + preview), `running-code-config.ts` (`parseConfig`, `serializeConfig`, `previewCode`, `slotName`), `running-code-form-schema.ts`.
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1110-running-code.md` — catalog only.
