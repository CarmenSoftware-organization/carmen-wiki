# Docs Sync — Backend / Platform / micro-data split — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sync carmen-wiki to source-repo changes committed after 2026-06-04 — the micro-data split, new permission keys, `doc_version` optimistic locking, the attachment download DTO, and the platform changelog — across EN and TH.

**Architecture:** Pure Markdown content edits, no code. Tasks run A → B → D → C → E. Each task: (1) confirm against source, (2) edit/create EN page, (3) verify frontmatter + stale-claim greps, (4) mirror to the parallel TH page, (5) commit. New pages embed full content here; edits give exact anchor strings.

**Tech Stack:** Wiki.js Markdown, YAML frontmatter. Spec: `docs/superpowers/specs/2026-06-09-docs-sync-backend-platform-microdata-design.md`.

## Conventions (every task)

- Frontmatter: edited pages bump `date` to `2026-06-09T00:00:00.000Z`, keep `dateCreated`. New pages set both to `2026-06-09T00:00:00.000Z`.
- Links: absolute-URL markdown `[text](/en/inventory/<mod>/<slug>)` (TH uses `/th/...`). No pipe wikilinks. No inline cross-locale links.
- TH prose is Thai; keep field names, endpoints, table names, and `code` tokens in English.
- "Verify frontmatter" step = the file still has the 8 required keys (`title, description, published, date, tags, editor, dateCreated`) and `date` is the bumped value. Run: `head -10 <file>` and eyeball, or `python3 .specs/verify_frontmatter.py` if it accepts the path.

## File map

| Part | EN files | TH mirror |
|---|---|---|
| A | `en/inventory/system-config/dashboard-dataset.md`, `.../query-dataset.md`, `en/inventory/reporting-audit/report.md`, `.../widget.md` | parallel `th/...` |
| B | `en/inventory/access-control/permission.md` | `th/...` |
| C | **new** `en/inventory/system-config/doc-version.md`; edit `en/inventory/system-config.md` + 5 × `01-data-model.md` (PR/PO/GRN/SR/spot-check); edit `en/inventory/reporting-audit/attachment.md` (cross-link) | parallel `th/...` |
| D | `en/inventory/reporting-audit/attachment.md` | `th/...` |
| E | **new** `en/platform/changelog.md`; edit `en/platform.md` | parallel `th/...` |

---

## Task A1: dashboard-dataset.md — micro-data backing

**Files:**
- Modify: `en/inventory/system-config/dashboard-dataset.md`
- Modify: `th/inventory/system-config/dashboard-dataset.md`

- [ ] **Step 1: Confirm source.** `head -120 ../micro-data/README.md` — confirm the "Dashboard datasets & widgets" section: 68 shaped datasets (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`), `GET /api/dashboard/datasets`, gateway proxies over HTTP, each runs in a read-only txn with `SET LOCAL search_path` pinned to the tenant schema.

- [ ] **Step 2: Edit EN — At a Glance line.** Replace:

```
> **Owner:** Sysadmin (read-only catalog) &nbsp;·&nbsp; **Backing:** Code-registered in-memory registry (`micro-business/dashboard-dataset/registry/`) — **no dedicated tenant table** &nbsp;·&nbsp; **Used by:** [reporting-audit/widget](/en/inventory/reporting-audit/widget) (widget picker), dashboard tiles &nbsp;·&nbsp; **50+ pre-built feeds** across inventory, workflow, procurement, product, vendor, recipe, and equipment categories.
```

with:

```
> **Owner:** Sysadmin (read-only catalog) &nbsp;·&nbsp; **Backing:** Code-registered in the **micro-data** service (`GET /api/dashboard/datasets`), proxied by backend-gateway over HTTP — **no dedicated tenant table** &nbsp;·&nbsp; **Used by:** [reporting-audit/widget](/en/inventory/reporting-audit/widget) (widget picker), dashboard tiles &nbsp;·&nbsp; **68 shaped feeds** (`scalar`, `scalar_delta`, `time_series`, `categorical`, `ranked`, `matrix`) across inventory, workflow, procurement, product, vendor, recipe, and equipment categories.
```

- [ ] **Step 3: Edit EN — section 1 paragraph.** In the sentence starting "Dashboard Dataset is the **read-only admin catalog screen**…", replace `Each dataset entry is a **code-registered definition** on the `micro-business` microservice — not a sysadmin-editable database row.` with `Each dataset entry is a **code-registered definition** in the **micro-data** microservice (Go), executed against the tenant database and proxied to the gateway over HTTP — not a sysadmin-editable database row.`

- [ ] **Step 4: Edit EN — "differs from" table row.** Replace the row:

```
| **Dashboard Dataset** (this page) | Named data feed catalog — query runs against tenant DB and returns typed data | Read-only; updated by code deployment | `micro-business` registry (code) |
```

with:

```
| **Dashboard Dataset** (this page) | Named data feed catalog — query runs against tenant DB and returns typed data | Read-only; updated by code deployment | **micro-data** service (Go), served at `/api/dashboard/datasets` |
```

- [ ] **Step 5: Edit EN — add execution note.** After the paragraph that begins "**Maintained by** Engineering (code releases)." append a new line:

```

Each dataset executes inside a **read-only transaction** with `SET LOCAL search_path` pinned to the caller's tenant schema, so a single deployed catalog serves every tenant safely. The backend-gateway is a thin proxy: `GET /api/dashboard/datasets` lists the catalogue (`{items,count}`) and `GET /api/dashboard/datasets/:id?bu_code=&user_id=` executes one feed (`{meta,data}`).
```

- [ ] **Step 6: Bump `date`** in EN frontmatter to `2026-06-09T00:00:00.000Z` (leave `dateCreated`).

- [ ] **Step 7: Verify stale claim gone.** Run: `grep -n "micro-business/dashboard-dataset/registry" en/inventory/system-config/dashboard-dataset.md` → Expected: no matches. Run: `grep -n "micro-data" en/inventory/system-config/dashboard-dataset.md` → Expected: ≥3 matches.

- [ ] **Step 8: Mirror to TH.** Apply the same five edits to `th/inventory/system-config/dashboard-dataset.md` (find the parallel Thai text), translating prose to Thai but keeping `micro-data`, endpoint paths, the six shape names, and `SET LOCAL search_path` in English. Bump TH `date` likewise. Verify the same greps against the TH file.

- [ ] **Step 9: Commit.**

```bash
git add en/inventory/system-config/dashboard-dataset.md th/inventory/system-config/dashboard-dataset.md
git commit -m "docs(system-config): dashboard-dataset now hosted in micro-data (EN+TH)"
```

---

## Task A2: query-dataset.md — micro-data execution note

**Files:**
- Modify: `en/inventory/system-config/query-dataset.md`
- Modify: `th/inventory/system-config/query-dataset.md`

- [ ] **Step 1: Edit EN.** At the end of section 1 ("What & Who"), after the paragraph ending "…reload-from-catalog is the recovery path.", append:

```

The views, stored procedures, and functions authored here are the data sources the **micro-data** service executes at run time: a report or dashboard names one (by `builder_key` or template `name`), and micro-data resolves it via `POST /api/datasets/execute`, composes the WHERE clause from the supplied filters, fans the query across the requested business units, and returns a `Dataset` (columns + rows + totals + summary). See [reporting-audit/report](/en/inventory/reporting-audit/report) for the render side.
```

- [ ] **Step 2: Bump EN `date`** to `2026-06-09T00:00:00.000Z`.

- [ ] **Step 3: Verify.** Run: `grep -n "datasets/execute\|micro-data" en/inventory/system-config/query-dataset.md` → Expected: ≥1 match.

- [ ] **Step 4: Mirror to TH** (`th/inventory/system-config/query-dataset.md`): same appended paragraph in Thai, keeping `POST /api/datasets/execute`, `builder_key`, `Dataset` in English; bump `date`.

- [ ] **Step 5: Commit.**

```bash
git add en/inventory/system-config/query-dataset.md th/inventory/system-config/query-dataset.md
git commit -m "docs(system-config): note micro-data executes query-dataset sources (EN+TH)"
```

---

## Task A3: report.md — micro-data ⇄ micro-report split

**Files:**
- Modify: `en/inventory/reporting-audit/report.md`
- Modify: `th/inventory/reporting-audit/report.md`

- [ ] **Step 1: Confirm source.** `head -60 ../micro-data/README.md` — the "Where the split came from" table: dataset columns (`source_type`, `source_name`, `source_params`, `dialog`, `view_name`, `builder_key`) → **micro-data**; report columns (`content`, `kind`, `report_group`, format/render) → **micro-report**. The `tb_report_template` table is unchanged for now.

- [ ] **Step 2: Edit EN — add a section.** After section 1 ("What & Who"), insert a new section (renumber following sections if the page numbers them sequentially; if section 2 is "Common Tasks", insert this as the new section 2 and shift the rest):

```
## 2. Dataset vs render — the micro-data split

Report generation is split across two Go services with the **`Dataset`** object as the boundary contract:

| Concern | Columns on `tb_report_template` | Owner | Does |
|---|---|---|---|
| **Dataset** | `source_type`, `source_name`, `source_params`, `dialog`, `view_name`, `builder_key` | **micro-data** | Resolves the view / function / procedure, composes the WHERE clause from filters, fans out across tenant BUs, returns `Dataset` (columns + rows + totals + summary). Renders nothing. |
| **Report** | `content`, `kind`, `report_group`, format / orientation / signatures | **micro-report** | Owns output format (PDF / Excel / CSV / JSON), template layout, `kind`, print mappings, and job tracking. |

micro-report no longer runs the query in-process — it calls micro-data's `POST /api/datasets/execute` (passing the source's `builder_key` or `name`, `bu_codes`, and `filters`) and renders the returned `Dataset`. The `tb_report_template` row still physically holds both column sets; micro-data reads only the dataset columns (mapped onto `model.DatasetSource`). Extracting them into a `tb_dataset_source` table is a noted future migration, not yet in effect.
```

- [ ] **Step 3: Renumber.** If subsequent sections were `## 2.`, `## 3.` …, increment each by one so numbering stays sequential. Update any in-page `### N.M` subsection numbers and cross-references to match.

- [ ] **Step 4: Bump EN `date`** to `2026-06-09T00:00:00.000Z`.

- [ ] **Step 5: Verify.** Run: `grep -n "datasets/execute\|micro-data\|Dataset" en/inventory/reporting-audit/report.md` → Expected: ≥3 matches.

- [ ] **Step 6: Mirror to TH** (`th/inventory/reporting-audit/report.md`): same new section in Thai (translate the prose and the "Does" column; keep column names, service names, endpoint, `Dataset`, `model.DatasetSource`, `tb_dataset_source` in English), with the same renumbering. Bump `date`.

- [ ] **Step 7: Commit.**

```bash
git add en/inventory/reporting-audit/report.md th/inventory/reporting-audit/report.md
git commit -m "docs(reporting-audit): document micro-data/micro-report split in report (EN+TH)"
```

---

## Task A4: widget.md — widget CRUD hosted in micro-data

**Files:**
- Modify: `en/inventory/reporting-audit/widget.md`
- Modify: `th/inventory/reporting-audit/widget.md`

- [ ] **Step 1: Edit EN — add a section.** After section 1 ("What & Who"), insert (renumber following sections as in Task A3):

```
## 2. Where widget CRUD runs (micro-data)

Widget create / read / update / delete is hosted by the **micro-data** service and proxied by the backend-gateway over HTTP — the tenant tables (`tb_widget_dashboard`, `tb_widget_default_layout`, `tb_widget_workspace`) are unchanged. Two scopes:

| Scope | Endpoints (gateway → micro-data) |
|---|---|
| **BU widgets** | `GET/POST /api/dashboard/bu-widgets?bu_code=` · `GET/PATCH/DELETE /api/dashboard/bu-widgets/:id?bu_code=&user_id=` |
| **Personal widgets** | `GET/POST /api/dashboard/personal-widgets?user_id=` · `GET/PATCH/DELETE /api/dashboard/personal-widgets/:id?user_id=` · `POST /api/dashboard/personal-widgets/reorder?user_id=` (bulk reorder) |

The feeds these widgets display come from [system-config/dashboard-dataset](/en/inventory/system-config/dashboard-dataset), also hosted in micro-data.
```

- [ ] **Step 2: Renumber** subsequent sections sequentially (as Task A3, Step 3).

- [ ] **Step 3: Bump EN `date`** to `2026-06-09T00:00:00.000Z`.

- [ ] **Step 4: Verify.** Run: `grep -n "micro-data\|bu-widgets\|personal-widgets" en/inventory/reporting-audit/widget.md` → Expected: ≥3 matches.

- [ ] **Step 5: Mirror to TH** (`th/inventory/reporting-audit/widget.md`): same section in Thai (keep endpoints, table names, scope labels in English). Bump `date`.

- [ ] **Step 6: Commit.**

```bash
git add en/inventory/reporting-audit/widget.md th/inventory/reporting-audit/widget.md
git commit -m "docs(reporting-audit): widget CRUD now hosted in micro-data (EN+TH)"
```

---

## Task B: permission.md — new permission keys

**Files:**
- Modify: `en/inventory/access-control/permission.md`
- Modify: `th/inventory/access-control/permission.md`

The new keys (confirmed from `../carmen-turborepo-backend-v2/apps/backend-gateway/x-app-id.json`):
- Comment keys for PR / PO / SR, each with: `.findAll`, `.create`, `.update`, `.delete`, `.addAttachment`, `.removeAttachment`, `.createWithFiles` — prefixes `purchaseRequestComment`, `purchaseOrderComment`, `storeRequisitionComment`.
- `storeRequisition.approve`
- `my-approve.findAll`

- [ ] **Step 1: Confirm source.** Run: `grep -iE 'Comment\.|my-approve|storeRequisition.approve' ../carmen-turborepo-backend-v2/apps/backend-gateway/x-app-id.json` — confirm the keys above are present.

- [ ] **Step 2: Edit EN — add a section.** After section 1 ("What & Who"), insert a new section (renumber following sections sequentially):

```
## 2. Comment & approval-workflow permissions

Per-document **comment threads** and **approval actions** are gated by their own permission atoms (App IDs). Comment permissions follow a uniform verb set per document type:

| Document type | Comment App ID prefix | Actions |
|---|---|---|
| Purchase Request | `purchaseRequestComment` | `findAll`, `create`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |
| Purchase Order | `purchaseOrderComment` | `findAll`, `create`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |
| Store Requisition | `storeRequisitionComment` | `findAll`, `create`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |

`createWithFiles` is the single-call create that posts a comment with attachments in one multipart request (vs. `create` then `addAttachment`).

Approval-workflow atoms:

| App ID | Purpose |
|---|---|
| `storeRequisition.approve` | Approve / act on a store-requisition approval step |
| `my-approve.findAll` | List every document awaiting **the current user's** approval, across document types — backs the cross-module approval inbox ([dashboard/my-approval](/en/inventory/dashboard/my-approval)) |

These are seed-managed atoms like all others on this page; they are bundled into roles via [access-control/application-role](/en/inventory/access-control/application-role).
```

- [ ] **Step 3: Renumber** subsequent sections sequentially.

- [ ] **Step 4: Bump EN `date`** to `2026-06-09T00:00:00.000Z`.

- [ ] **Step 5: Verify.** Run: `grep -n "purchaseRequestComment\|my-approve.findAll\|createWithFiles" en/inventory/access-control/permission.md` → Expected: ≥3 matches.

- [ ] **Step 6: Mirror to TH** (`th/inventory/access-control/permission.md`): same section in Thai (keep all App ID strings and the verb names in English; translate "Purpose"/prose). Bump `date`.

- [ ] **Step 7: Commit.**

```bash
git add en/inventory/access-control/permission.md th/inventory/access-control/permission.md
git commit -m "docs(access-control): add comment + approval-workflow permission keys (EN+TH)"
```

---

## Task D: attachment.md — download URL / comment-attachment DTO

**Files:**
- Modify: `en/inventory/reporting-audit/attachment.md`
- Modify: `th/inventory/reporting-audit/attachment.md`

Confirmed from source:
- `comment-attachment.dto.ts` → `AttachmentSchema`: `fileName: string`, `fileUrl?: string`, `contentType: string`, `size?: number`. The internal `fileToken` is **stripped** before any response.
- `document-download-url.ts` → on read, each attachment's `fileUrl` is refilled with a **presigned MinIO URL** (TTL 3600 s) resolved from its `fileToken` via the `files.presigned-url` micro-file handler; if that fails it falls back to the relative gateway URL `buildDocumentDownloadUrl(bu_code, fileToken)` = `/api/{bu_code}/documents/{fileToken}/download`. Comment responses also strip internal author fields (`user_id`, `username`, `firstname`, `middlename`, `lastname`); the resolved author is exposed via the enriched `audit` object.

- [ ] **Step 1: Confirm source.** Run: `sed -n '1,40p' ../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/dto/_shared/comment-attachment.dto.ts` and `sed -n '1,40p' ../carmen-turborepo-backend-v2/apps/backend-gateway/src/common/helpers/document-download-url.ts` — confirm the field list and the presigned/fallback logic above.

- [ ] **Step 2: Edit EN — add a section.** After section 1 ("What & Who"), insert (renumber following sections sequentially):

```
## 2. File retrieval & the comment-attachment shape

**On read, the stored URL is not trusted — it is re-resolved.** For every attachment returned, the gateway resolves a fresh **presigned MinIO URL** (1-hour TTL) from the internal `fileToken`; if resolution fails it falls back to a relative gateway route `/api/{bu_code}/documents/{fileToken}/download`. The internal `fileToken` is then **stripped** from the response — callers only ever see `fileUrl`.

The attachment shape exposed in comment responses:

| Field | Type | Notes |
|---|---|---|
| `fileName` | string | Original file name |
| `fileUrl` | string (optional) | Presigned URL, or relative fallback route; refilled per request |
| `contentType` | string | MIME type (`image/jpeg`, `image/png`, `image/webp`, `image/gif`, `application/pdf`) |
| `size` | number (optional) | Bytes |

Upload limits on `POST :id/attachment`: **1–10 files, ≤ 10 MB each**, MIME restricted to the five types above. Comment responses additionally **strip internal author fields** (`user_id`, `username`, `firstname`, `middlename`, `lastname`) — the resolved author is exposed via the enriched `audit` object instead.

> **Note — two unrelated `doc_version` fields.** `tb_attachment.doc_version` is a **re-render counter** for regenerated documents (e.g. a re-printed PDF); it is *not* the optimistic-concurrency `doc_version` carried by transactional documents. See [system-config/doc-version](/en/inventory/system-config/doc-version).
```

- [ ] **Step 3: Renumber** subsequent sections sequentially.

- [ ] **Step 4: Bump EN `date`** to `2026-06-09T00:00:00.000Z`.

- [ ] **Step 5: Verify.** Run: `grep -n "presigned\|fileToken\|doc-version" en/inventory/reporting-audit/attachment.md` → Expected: ≥3 matches.

- [ ] **Step 6: Mirror to TH** (`th/inventory/reporting-audit/attachment.md`): same section in Thai (keep field names, MIME types, route, `fileToken`, `audit`, `doc_version` in English). Bump `date`.

- [ ] **Step 7: Commit.**

```bash
git add en/inventory/reporting-audit/attachment.md th/inventory/reporting-audit/attachment.md
git commit -m "docs(reporting-audit): document attachment presigned-URL retrieval + DTO (EN+TH)"
```

> Note: the cross-link added here points to the doc-version page created in Task C1. Run Task D before C1 only if you accept a temporarily-dangling link; the link target is created in C1 and both are committed before the final verification task, so the end state is consistent either way.

---

## Task C1: NEW page system-config/doc-version.md (EN + TH)

**Files:**
- Create: `en/inventory/system-config/doc-version.md`
- Create: `th/inventory/system-config/doc-version.md`

Entities carrying optimistic-lock `doc_version` (confirmed from the 06-04 commits touching `*.dto.ts` / `*.serializer.ts` / swagger `request.ts`): purchase-request, purchase-order, good-received-note, credit-note, pricelist, pricelist-template, purchase-request-template, request-for-pricing, spot-check, stock-in, stock-out, store-requisition, plus config masters credit-term, extra-cost-type, recipe-category, recipe-cuisine, recipe-equipment, recipe-equipment-category, running-code, vendor-business-type.

- [ ] **Step 1: Confirm source.** Run: `git -C ../carmen-turborepo-backend-v2 show f6694fbc --stat | grep -c doc_version` style check, or `git -C ../carmen-turborepo-backend-v2 log --since=2026-06-04 --until=2026-06-05 --name-only --pretty=format:%s | grep -iE 'dto|serializer|swagger'` to confirm the entity list above before finalizing the table.

- [ ] **Step 2: Create EN file** with this exact content:

```markdown
---
title: Document Version (Optimistic Concurrency)
description: The doc_version integer that guards transactional documents against lost updates — clients must echo the current version on save or get a 409 Conflict.
published: true
date: 2026-06-09T00:00:00.000Z
tags: system-config, concurrency, doc-version, optimistic-lock, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# Document Version (Optimistic Concurrency)

> **At a Glance**
> **Field:** `doc_version` (integer) on each document's update payload &nbsp;·&nbsp; **Guards against:** lost updates from concurrent edits &nbsp;·&nbsp; **On mismatch:** **409 Conflict** &nbsp;·&nbsp; **Applies to:** ~20 transactional & config entities (see §3) &nbsp;·&nbsp; **Not** the attachment re-render counter (see §5).

## 1. What & Who

`doc_version` is an **optimistic-concurrency** guard: a monotonically increasing integer carried on the aggregate root of a document. Every read returns the current `doc_version`; every **update must echo the version the client started from**. The server only applies the write if the supplied version still matches the stored one — then it increments the version. If two users open the same document and both save, the second save fails instead of silently overwriting the first.

It is *optimistic*: no row is locked while a user is editing. Conflicts are detected at save time rather than prevented up front, which suits human-paced document editing where conflicts are rare but costly.

**Set by** every service's update path (rolled out across the backend on 2026-06-04). **Checked by** the same update handlers. **Surfaced to** clients as a `409 Conflict` they must recover from.

## 2. Behaviour

```
function update(id, payload):
    current = load(id)                       # current.doc_version = N
    if payload.doc_version != current.doc_version:
        raise Conflict(409)                  # someone saved first
    apply(payload)
    current.doc_version = N + 1              # bump on success
    save(current)
    return current                           # client reads back N+1
```

The client must send the `doc_version` it received on its last read. After a successful save it must use the returned, incremented value for any further edit.

## 3. Entities that carry it

| Group | Entities |
|---|---|
| Procurement | purchase-request, purchase-order, purchase-request-template, request-for-pricing, credit-note |
| Receiving & stock | good-received-note, stock-in, stock-out |
| Counting | spot-check |
| Requisition | store-requisition |
| Pricing | pricelist, pricelist-template |
| Config masters | credit-term, extra-cost-type, running-code, vendor-business-type, recipe-category, recipe-cuisine, recipe-equipment, recipe-equipment-category |

## 4. Test scenarios

| # | Setup | Action | Expected |
|---|---|---|---|
| 1 | Two clients A and B both load document at `doc_version = 5` | A saves a change | A succeeds; document is now `doc_version = 6` |
| 2 | Continuing #1 | B saves its change, still sending `doc_version = 5` | **409 Conflict**; B's write is rejected, no data lost |
| 3 | Continuing #2 | B re-fetches (gets `doc_version = 6`), re-applies its edit, saves with `6` | B succeeds; document is now `doc_version = 7` |
| 4 | Single client | Update without any `doc_version`, or with a stale one | Rejected — the field is required for the compare-and-set |

## 5. Not to be confused with

`tb_attachment.doc_version` is a **different field with a different meaning** — it is a *re-render counter* for regenerated documents (e.g. a re-printed PDF), incremented each time the owning module re-renders the file, and it retains older versions for audit. It is **not** a concurrency guard. See [reporting-audit/attachment](/en/inventory/reporting-audit/attachment).
```

- [ ] **Step 3: Create TH file** `th/inventory/system-config/doc-version.md` — same structure and frontmatter (title/description may be translated; keep `doc_version`, `409 Conflict`, entity names, and the pseudo-code in English), prose translated to Thai. Use `/th/...` link targets.

- [ ] **Step 4: Verify.** Run: `head -10 en/inventory/system-config/doc-version.md` (8 frontmatter keys present) and `head -10 th/inventory/system-config/doc-version.md`.

- [ ] **Step 5: Commit.**

```bash
git add en/inventory/system-config/doc-version.md th/inventory/system-config/doc-version.md
git commit -m "docs(system-config): add doc-version optimistic-concurrency concept page (EN+TH)"
```

---

## Task C2: link doc-version from index + entity data-models

**Files:**
- Modify: `en/inventory/system-config.md`, `th/inventory/system-config.md`
- Modify: `01-data-model.md` for PR/PO/GRN/SR/spot-check in EN and TH (10 files)

- [ ] **Step 1: system-config index (EN).** In `en/inventory/system-config.md`, in the module table (the block containing the `dashboard-dataset` and `document` rows around line 41), add a new row after the `document` row:

```
| [doc-version](/en/inventory/system-config/doc-version) | Optimistic-concurrency `doc_version` guard — clients echo the version on save or get a 409 | Engineering |
```

- [ ] **Step 2: system-config index (TH).** Add the parallel row to `th/inventory/system-config.md` with `/th/...` link and Thai description.

- [ ] **Step 3: Entity data-model cross-links (EN).** In each of these files, add the line below at the end of section 1 (or under the data-model's "audit/system fields" note if one exists):

Files: `en/inventory/purchase-request/01-data-model.md`, `en/inventory/purchase-order/01-data-model.md`, `en/inventory/good-receive-note/01-data-model.md`, `en/inventory/store-requisition/01-data-model.md`, `en/inventory/spot-check/01-data-model.md`

Line to add:

```

**Concurrency:** updates to this document use [system-config/doc-version](/en/inventory/system-config/doc-version) optimistic locking — the client must echo the current `doc_version` on save or receive a `409 Conflict`.
```

- [ ] **Step 4: Entity data-model cross-links (TH).** Add the parallel Thai line (with `/th/...` link, `doc_version` and `409 Conflict` in English) to the five `th/inventory/<mod>/01-data-model.md` files.

- [ ] **Step 5: Bump `date`** on all 12 edited files to `2026-06-09T00:00:00.000Z`.

- [ ] **Step 6: Verify.** Run: `grep -rl "system-config/doc-version" en/inventory th/inventory | wc -l` → Expected: ≥12 (index ×2 + data-models ×10).

- [ ] **Step 7: Commit.**

```bash
git add en/inventory/system-config.md th/inventory/system-config.md en/inventory/*/01-data-model.md th/inventory/*/01-data-model.md
git commit -m "docs: link doc-version from system-config index and PR/PO/GRN/SR/spot-check data-models (EN+TH)"
```

---

## Task E1: NEW page platform/changelog.md (EN + TH)

**Files:**
- Create: `en/platform/changelog.md`
- Create: `th/platform/changelog.md`

Confirmed from `../carmen-platform/`: source of truth is `src/data/changelog.json` (an `unreleased` buffer + `versions[]`, latest first; categories = Added/Changed/Deprecated/Removed/Fixed/Security; entries are plain strings). `CHANGELOG.md` is generated from it (never hand-edited). The app reads the JSON statically (no runtime fetch). Public route `/changelog` (allowed in the auth guard as a public path). `VersionBadge` shows `v{versions[0].version}` in the sidebar footer and on the Landing page, linking to `/changelog`. Release flow: `bun run build:bump [patch|minor|major]` promotes `unreleased` into a dated `versions[0]`, syncs `package.json`, regenerates `CHANGELOG.md`, then builds. Dates are authored `YYYY-MM-DD` and rendered verbatim (no `new Date()` parsing, to avoid TZ off-by-one).

- [ ] **Step 1: Confirm source.** Run: `sed -n '1,40p' ../carmen-platform/src/data/changelog.json`, `head -40 ../carmen-platform/src/components/VersionBadge.tsx`, `head -50 ../carmen-platform/docs/superpowers/specs/2026-06-01-changelog-design.md` — confirm the JSON shape, badge placements, and release flow above.

- [ ] **Step 2: Create EN file** with this exact content:

```markdown
---
title: Changelog
description: The platform's versioned changelog — a JSON-sourced, public /changelog page reached via a version badge in the sidebar and on the landing page.
published: true
date: 2026-06-09T00:00:00.000Z
tags: platform, changelog, versioning, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# Changelog

> **At a Glance**
> **Source of truth:** `src/data/changelog.json` &nbsp;·&nbsp; **Public page:** `/changelog` (no auth) &nbsp;·&nbsp; **Discovery:** `VersionBadge` in the sidebar footer + landing page &nbsp;·&nbsp; **Generated artifact:** `CHANGELOG.md` (Keep a Changelog format) &nbsp;·&nbsp; **Release:** `bun run build:bump`.

## 1. What & Who

The Changelog is a versioned, **public** record of what shipped in the Carmen Platform admin product. A single JSON file (`src/data/changelog.json`) is the source of truth; the React app imports it statically (no runtime fetch) to render the `/changelog` page, and a Node script regenerates a human-readable `CHANGELOG.md` (Keep a Changelog format) at the repo root. `CHANGELOG.md` is **never hand-edited** — edit the JSON.

**Authored by** developers (under the `unreleased` buffer as they work). **Read by** anyone — the page is public.

## 2. How it's sourced

The JSON holds an `unreleased` buffer plus released `versions` (latest first). Empty categories are omitted for easy authoring:

```
{
  "unreleased": { "Added": ["A feature not yet released"] },
  "versions": [
    {
      "version": "0.1.0",
      "date": "2026-06-01",
      "changes": {
        "Added": ["Public changelog page with version badge"],
        "Fixed": ["Audit dates read from the nested audit object in lists"]
      }
    }
  ]
}
```

Categories use the full Keep a Changelog set, rendered in this order: **Added, Changed, Deprecated, Removed, Fixed, Security**. Change entries are plain strings (no per-entry metadata). Dates are authored as `YYYY-MM-DD` and rendered **verbatim** — the page deliberately avoids `new Date(value)` because parsing a date-only string as UTC midnight shifts it a day earlier for users west of UTC.

## 3. Where it appears

| Surface | Behaviour |
|---|---|
| `/changelog` page | Public route; lists the `unreleased` block (if non-empty) then each released version newest-first |
| Sidebar footer | `VersionBadge` shows `v{latest}` linking to `/changelog` |
| Landing page | `VersionBadge` next to the build date |

The current version for the badge is derived from `versions[0].version` (fallback `0.0.0`). `/changelog` is registered as a **public path in the auth guard**, so it renders for signed-out visitors.

## 4. For developers

- **Add a change:** edit `src/data/changelog.json`, adding strings under the appropriate category inside `unreleased`. Do not touch `CHANGELOG.md`.
- **Cut a release:** `bun run build:bump [patch|minor|major]` (default `patch`) increments the semver, promotes the `unreleased` buffer into a new dated `versions[0]` entry, resets `unreleased` to `{}`, syncs `package.json`, regenerates `CHANGELOG.md`, then builds.
- **Public-path note:** if a route-guard refactor changes how public paths are listed, `/changelog` must stay allowlisted or the page will redirect to sign-in.
```

- [ ] **Step 3: Create TH file** `th/platform/changelog.md` — same structure and frontmatter (translate title/description/prose to Thai; keep `src/data/changelog.json`, `/changelog`, `VersionBadge`, category names, `bun run build:bump`, the JSON block, and `package.json`/`CHANGELOG.md` in English). Use `/th/...` link targets.

- [ ] **Step 4: Verify.** Run: `head -10 en/platform/changelog.md` and `head -10 th/platform/changelog.md` (8 frontmatter keys present).

- [ ] **Step 5: Commit.**

```bash
git add en/platform/changelog.md th/platform/changelog.md
git commit -m "docs(platform): add Changelog page (EN+TH)"
```

---

## Task E2: link changelog from platform landing

**Files:**
- Modify: `en/platform.md`, `th/platform.md`

- [ ] **Step 1: Edit EN.** In `en/platform.md`, after the section 3 ("Reporting") table and before "## 4. How to use this book", add a new section and renumber "How to use this book" to `## 5.`:

```
## 4. Product

| Module | What it covers |
|---|---|
| [Changelog](/en/platform/changelog) | Versioned, public release history + version badge |

```

- [ ] **Step 2: Edit TH.** Apply the parallel change to `th/platform.md` (`/th/platform/changelog`, Thai labels), renumbering the trailing section likewise.

- [ ] **Step 3: Bump `date`** on both files to `2026-06-09T00:00:00.000Z`.

- [ ] **Step 4: Verify.** Run: `grep -n "platform/changelog" en/platform.md th/platform.md` → Expected: 1 match each.

- [ ] **Step 5: Commit.**

```bash
git add en/platform.md th/platform.md
git commit -m "docs(platform): link Changelog from platform landing (EN+TH)"
```

---

## Task F: Final verification

- [ ] **Step 1: No stale architecture claims.** Run: `grep -rn "micro-business/dashboard-dataset/registry" en/ th/` → Expected: no matches.

- [ ] **Step 2: micro-data referenced where expected.** Run: `grep -rln "micro-data" en/inventory th/inventory` → Expected: dashboard-dataset, query-dataset, report, widget in both locales (≥8 files).

- [ ] **Step 3: doc-version wired up.** Run: `grep -rln "system-config/doc-version" en/ th/` → Expected: ≥13 files (page self-links excluded; index ×2, data-models ×10, attachment ×2... at least 13 incl. attachment cross-link).

- [ ] **Step 4: New pages exist EN+TH.** Run: `ls en/inventory/system-config/doc-version.md th/inventory/system-config/doc-version.md en/platform/changelog.md th/platform/changelog.md` → Expected: all four exist.

- [ ] **Step 5: Frontmatter intact.** Run: `python3 .specs/verify_frontmatter.py` if it scans the tree; otherwise spot-check `head -10` on the four new pages and confirm all edited pages have `date: 2026-06-09`.

- [ ] **Step 6: EN/TH parity.** Run: `for f in $(git diff --name-only HEAD~10 -- 'en/**'); do t=${f/en\//th/}; [ -f "$t" ] || echo "MISSING TH: $t"; done` → Expected: no output (every touched EN page has a TH sibling). Adjust the `HEAD~N` range to cover all task commits.

- [ ] **Step 7: Report.** Summarize: pages created (4), pages edited, and the verification grep results. If `.specs/process-coverage-checklist.md` tracks any of these entities, note that the micro-data/permission/doc_version updates may move their BR/UF/TS status — flag for a follow-up checklist pass (out of scope for this plan).

---

## Self-review notes

- **Spec coverage:** A (4 pages) ✓, B (permission) ✓, C (new page + index + 5 entity links + attachment cross-link) ✓, D (attachment DTO) ✓, E (new page + landing link) ✓. Out-of-scope items (front-end, cronjobs, coverage backlog, `tb_dataset_source`) are not tasked, per spec.
- **Ordering note:** the spec sequences A→B→D→C→E; this plan keeps that order but places C1 (page creation) before C2 (links) and notes the D→C cross-link dependency is resolved by the time of Task F.
- **Type/name consistency:** endpoint paths, App ID strings, DTO field names, and the `doc_version` distinction are stated identically across Tasks A/B/D/C.
- **No placeholders:** new-page content is given in full; edits give exact anchor strings confirmed by reading the live files.
