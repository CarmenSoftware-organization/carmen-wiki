---
title: Running Code
description: Document-number patterns — prefix, date token, running counter per document type (PR, PO, GRN, SR, GL-JV, …). Since 2026-08-27 the admin dialog is a part-by-part editor with live preview; raw JSON is a collapsed fallback.
published: true
date: '2026-10-27T00:00:00.000Z'
tags: system-config, running-code, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# Running Code

> **At a Glance**
> **Owner:** Sysadmin &nbsp;·&nbsp; **Table:** `tb_config_running_code` &nbsp;·&nbsp; **Route:** `/system-admin/running-code` &nbsp;·&nbsp; **Permission / licence:** `system_admin.running_code` &nbsp;·&nbsp; **Used by:** numbering service on every document create &nbsp;·&nbsp; Document-numbering rules — `PR202605-00001` etc. &nbsp;·&nbsp; **Admin dialog is a part-by-part editor (text / date / running / token) with a live preview since 2026-08-27; the raw `config` JSON is kept as a collapsed "Advanced" fallback.**

![Running Code screen](/screenshots/system-config/running-code.png)

## Implementation status (re-verified 2026-10-27)

- **One numbering engine for every document** (BE `48c3fc817`): `reserveDocumentNumbers` (`common/helpers/document-number.helper.ts`) is now the single way PR, PO, GRN, SR, CN, SC, price list, vendor portal, Stock-In/Out, AP, AR, tax invoice and GL JV numbers are issued. It reads the whole config and splits it into head / running digits / tail with `GenerateCode` itself (`getRunningCodeShape`), so the running number may sit **anywhere** in the pattern and dates follow the BU calendar. Numbers are issued under a lock per (BU, table, head, tail) inside the transaction that writes the document, which removes duplicate numbers when documents arrive concurrently; the latest number is found only among numbers of the configured width, the next width is read when the digits overflow (including a block that crosses the width boundary, BE `2a343f502`), and soft-deleted documents still hold their numbers. `running-code.generateCode` matches the config by exact `type` (it used to use `contains`).
- **A config that cannot number documents is refused when saved** (BE `8b42ca451`): `POST`/`PUT api/config/:bu_code/running-codes` run the generators' own checks and answer **400** with one of eight `RUNNING_CODE_*` catalog codes — `FORMAT_REQUIRED`, `FORMAT_PART_UNDEFINED`, `FORMAT_PART_REPEATED`, `PART_MALFORMED`, `RANDOM_NOT_ALLOWED`, `RUNNING_COUNT` (exactly one `running()` part), `RUNNING_PAD` (`running(n, '0')`, n ≥ 1, pad must be `0`), `RUNNING_NOT_PLACED` (`packages/error-catalog/src/catalog.ts:1203-1270`). A config already stored in that state (or edited in the database) answers **422 `RUNNING_CODE_CONFIG_UNUSABLE`** naming the type, with the reason in `params.reason`, instead of a 500 (BE `d17d08156`). The "Format must reference at least one segment" caveat in Edge Cases and §6 below is therefore **superseded**: unreferenced slots are still tolerated, but a format that omits the running part, repeats it, or uses `random()` cannot be saved.
- **Duplicate `type`** now carries `RUNNING_CODE_ALREADY_EXISTS` (409) and the dialog shows it under the Type field (FE `useServerFieldErrors`, `running-code-dialog.tsx:66`; FE `b71f86ea`).
- The list moved into `ListPageShell` (FE `c3fe01ea`); no behaviour change. Editor details below were verified 2026-09-22 and the FE files are otherwise unchanged apart from the above.

### Earlier status (verified 2026-07-16; re-verified 2026-09-22)

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
| Advanced-config textarea rejects the value on save | `config` is not valid JSON, or the backend refused it with a `RUNNING_CODE_*` 400 (no/duplicate `running()`, non-`0` pad, `random()`, undefined slot) | Fix syntax / the named part |
| `RUNNING_CODE_CONFIG_UNUSABLE` (422) when a document is created | The stored config for that type cannot number documents (saved before the save-time check, or edited in the database) | Correct the row here; the error names the type and reason |
| Part editor disabled, `configUnreadable` shown | `config` has no `format`, or `format` references a slot that does not exist | Repair in Advanced config; the editor refuses to guess and overwrite |
| Counter unexpectedly restarted | Dated segment changed | Counter scoped by `type + dated-segment` — adding `yyyyMM` restarts monthly |
| 500 `Cannot read properties of undefined (reading 'config')` on first document of a type | BU has no row for the type **and** no preset (`RUNNING_CODE_PRESET`) | Add the row here, or a preset in code (`GL-JV` was fixed this way on 2026-09-15) |
| Document number collision | Counter persistence bug or manual edit | Reset numbering service counter; investigate |
| Cannot delete | Active document type | Soft-delete only after retirement |

## 4. Edge Cases

- **Structured editor with a JSON escape hatch.** The part editor guarantees a consistent `format` for anything it saves; only the Advanced-config path can still store a `format` that references an undefined slot, which then fails at document-create time.
- **`GL-JV` has no literal prefix part on purpose** — the prefix lives on `tb_gl_jv_header.prefix_code` and `jv_no` holds only `date('yyyyMM') + running(5,'0')`; the series is scoped to `prefix_code` by `generateJvNo`, so each prefix counts on its own (`running-code.const.ts:109-117`; the older `startsWith` rationale was dropped from the source comment in BE `2a343f502`). The preset list also gained AP/AR/tax codes (`AP-IV`, `AP-DN`, `AP-CN`, `AP-DP`, `AP-PV`, `AR-IV`, `AR-DN`, `AR-CN`, `TX-IV`, `TX-DN`, `TX-CN`).
- **Counter scope.** Implicit — scoped by `type + dated-segment`. Without a dated segment, counter is global per type.
- **Counter persistence** is service state (advisory lock / sequence), not this table — this entity defines the *pattern* only.
- **Pattern changes mid-period** take effect at next mint; existing references render as stored.
- **Format must place exactly one `running()` part** — enforced on save since 2026-10 (see Implementation status); unreferenced extra slots are still allowed.

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
- **Format validation.** The backend rejects, on save, a `format` that is missing, uses an undefined or repeated slot, has a malformed part, uses `random()`, lacks exactly one `running(n, '0')` part, or does not place it exactly once (`RUNNING_CODE_*`, 400). The part editor always emits a consistent `format`; the Advanced-config textarea is checked by the backend instead of only for JSON syntax.
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

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_config_running_code` (lines ~4864-4883).
- **Backend pattern logic:** `../carmen-turborepo-backend/apps/micro-business/src/common/helpers/running-code.helper.ts` — `GenerateCode`, `getPattern`; presets `apps/micro-business/src/master/running-code/const/running-code.const.ts` (`RUNNING_CODE_PRESET`); service `apps/micro-business/src/master/running-code/running-code.service.ts` (`update` is `doc_version`-guarded, `:309`).
- **Gateway:** `../carmen-turborepo-backend/apps/backend-gateway/src/config/config_running-codes/` — `api/config/:bu_code/running-codes`; licence `system_admin.running_code` (`permission.route-map.ts:125`).
- **Seed:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_config_running_code.json`; `packages/prisma-shared-schema-tenant/src/seed-data/running-code.ts` (includes `GL-JV`).
- **Frontend:** `../carmen-frontend/routes/system-admin/running-code/` — `running-code-component.tsx` (list), `running-code-dialog.tsx` (create/edit), `running-code-config-fields.tsx` (part editor + preview), `running-code-config.ts` (`parseConfig`, `serializeConfig`, `previewCode`, `slotName`), `running-code-form-schema.ts`.
- **E2E:** `../carmen-frontend-e2e/docs/test-cases/1110-running-code.md` — catalog only.
