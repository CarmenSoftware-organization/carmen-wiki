# Diagrams from carmen/docs — Design

**Date:** 2026-09-28
**Branch:** `docs/diagrams-from-carmen`
**Status:** Approved in brainstorming; awaiting written-spec review

## 1. Intent

### 1.1 Goal

Enrich existing **Inventory book** pages with Mermaid diagrams sourced from `../carmen/docs/`, so developers and QA grasp module flows, status lifecycles, and data models faster.

### 1.2 Decisions made with the user

| Question | Decision |
|---|---|
| Purpose | Enrich existing pages (not a gallery, not a verbatim bulk copy) |
| Diagram disagrees with code | Adapt it to match current implementation; if it cannot be adapted, do not import it |
| Thai pages | Mirror every imported diagram into `th/inventory/`; descriptive label text translated to Thai (identifiers stay English), matching existing TH pages — revised at the Task 3 checkpoint 2026-09-28 |
| Approach | Module-by-module curation, preceded by a catalog of all source diagrams |

### 1.3 Assumptions

- Inventory book only. `carmen/docs` has almost no carmen-platform (cluster/BU/license) content; its `system-administration` folder describes the inventory app's own users/locations/permissions, which map to Inventory modules.
- The task is **import and adapt**, not author. No new diagrams are drawn without a source block.

### 1.4 Source survey (2026-09-28)

- ~1,862 ` ```mermaid ` blocks in 269 files under `../carmen/docs/`; no `.drawio`/`.puml`/diagram `.svg` files.
- Types: flowchart ~1,071, graph ~536, sequenceDiagram 105, stateDiagram-v2 88, erDiagram 37, others < 20.
- Main sources: `docs/app/` (1,108) and `docs/documents/` (585), with heavy duplication between them.
- Wiki today: 60 pages already carry Mermaid; only `graph`, `stateDiagram-v2`, `sequenceDiagram` are in use. 10 of 19 Inventory modules have no diagram.

### 1.5 Success criteria

1. Every source block has a final status in `.specs/diagram-catalog.md` (`imported`, `duplicate of …`, `out-of-scope`, or `rejected: <reason>`); none left `candidate` or `unmapped`.
2. Every imported diagram carries a source + verification line and matches the cited implementation.
3. EN and TH pages have structurally identical Mermaid blocks — same count, same shape once label text is stripped (parity check passes, excluding mismatches recorded in the pre-work baseline).
4. Every diagram type used renders on the dev Wiki.js (`http://dev.blueledgers.com:3987/`).

### 1.6 Out of scope

Platform book; drawing diagrams with no source; diagrams on `04-test-scenarios*` pages; changes to `.specs/process-coverage-checklist.md`.

## 2. Phase 0 — Catalog

### 2.1 Script

`scripts/diagram_catalog.py`, Python stdlib only (same style as `scripts/embed_screenshots.py`).

For every ` ```mermaid ` block in `../carmen/docs/**/*.md`, record:

```
id          = short hash of whitespace-normalized block text
source      = path relative to carmen/docs
line        = starting line number
heading     = nearest preceding markdown heading
type        = first keyword (flowchart | graph | stateDiagram-v2 | erDiagram | sequenceDiagram | ...)
stmts       = statement lines (non-blank, non-comment, excluding subgraph/end/classDef/style lines) — a rough size signal
module      = wiki module from the static folder map (§2.2), or none
status      = candidate | duplicate of <source:line> | out-of-scope | unmapped | rejected: unclosed (fence never closed)
```

### 2.2 Folder → module map

A static dict in the script, e.g.:

```
procurement/purchase-requests, documents/pr       -> purchase-request
procurement/purchase-orders, documents/po         -> purchase-order
inventory-management/physical-count, documents/pc -> physical-count
inventory-management/spot-check, documents/sc     -> spot-check
store-operations/store-requisitions, documents/sr -> store-requisition
documents/grn, good-recive-note-managment         -> good-receive-note
operational-planning/recipe-management            -> recipe
product-management/*                              -> product | master-data
system-administration/permission-management       -> access-control
...
```

Vendor sources are **in scope** (corrected 2026-09-28): `documents/vm`, `vendor-management/requests-for-pricing`, `vendor-management/vendor-portal` → `vendor-pricelist`; `vendor-management/vendor-directory` → `master-data` (wiki has `master-data/vendor.md`, `vendor-pricelist/request-price-list.md`, `vendor-pricelist/vendor-dashboard.md`).

Out-of-scope folders (marked `out-of-scope`): `operational-planning/menu-engineering`, `operational-planning/demand-forecasting`, `procurement/my-approvals`, `template-guide`, `documents/module-spec-template.md`, `documents/MERMAID-TEST.md`. Any folder the map does not cover is listed as `unmapped` for manual decision rather than silently dropped.

### 2.3 Deduplication

Blocks with identical normalized hashes form a group; one survivor stays `candidate` (prefer `docs/app/` over `docs/documents/`, as the newer tree), the rest become `duplicate`.

### 2.4 Output

`.specs/diagram-catalog.md` — one table per module:

```
| id | source:line | type | heading | candidate wiki page | status |
```

The catalog is both the tracker and the evidence that all blocks were considered. It is **generated** — never hand-edited. Human/subagent decisions live in `.specs/diagram-decisions/<module>.tsv`, one line per decided block:

```
<id>	<status>	<wiki page path, or ->
```

where status is `imported` or `rejected: diverges|covered|unverifiable|too-large|render|page-full`. Every rebuild re-applies these files, so decisions survive re-runs; an unknown id or invalid status aborts the build. Unmapped folders are resolved by editing the script's folder map, not by decision lines. The allow-list block (between `<!-- ALLOW-LIST:START -->` / `<!-- ALLOW-LIST:END -->`) is preserved across rebuilds.

### 2.5 Checkpoint

**Outcome (2026-09-28):** 1,378 candidates. The user chose the filter: `docs/app/` sources only; types `flowchart`, `graph`, `stateDiagram(-v2)`, `erDiagram`, `sequenceDiagram`; drop headings describing prototype architecture (architecture, component/page hierarchy, page load, context diagram / level 0, deployment, tech stack, navigation, state management, layer); `stmts` ≤ 25. Filtered survivors become `out-of-scope (filter: <reason>)`. Unmapped folders mapped as proposed at the checkpoint.

After Phase 0, report the candidate count to the user. **If more than ~400 candidates remain, stop and agree on extra filtering before Phase 1.**

## 3. Phase 0.5 — Render check (throwaway)

Create a scratch page on dev Wiki.js containing `flowchart TD`, `erDiagram`, `stateDiagram-v2`, `sequenceDiagram`, plus constructs common in `carmen/docs` (`subgraph`, `classDef`, `<br/>` in labels). View it in Chrome, record what renders, then delete the page.

Output: a **syntax allow-list** at the top of the catalog (e.g. "`flowchart` unsupported → rewrite as `graph`"). All subagents follow it.

## 4. Verification rules

### 4.1 Precedence

E2E tests and implementation (frontend/backend) beat `carmen/docs`.

### 4.2 Verification source per diagram type

| Type | Verify against | Must match |
|---|---|---|
| `erDiagram` | Prisma schema in `carmen-turborepo-backend-v2/packages/**/schema.prisma` | Real `tb_*` table/column names, relations, cardinality; key columns only (≤ ~8 per entity) |
| `stateDiagram-v2` | Prisma enums, backend services, E2E | Status names equal enum values; each transition exists in a service/workflow |
| `flowchart` (user flow) | Frontend routes/pages, E2E specs | Steps, buttons, and screens that exist; drop design-only steps |
| `sequenceDiagram` | Backend controllers/services, Bruno collections | Endpoints and methods match; call order is realistic |

### 4.3 Decision per candidate

1. **Fully matches** → import as-is (syntax adjusted to the allow-list) → `imported`.
2. **Mostly matches** → fix nodes/states/labels, drop non-existent parts → `imported` with a Changes note.
3. **Structure diverges** (e.g. 5-stage flow in doc vs 2 in code) → `rejected: diverges`. Do not redraw.
4. **Duplicates an existing wiki diagram** → `rejected: covered`, unless clearly more detailed and verified, in which case replace and record why.
5. **No verification source** (feature not implemented) → `rejected: unverifiable`.
6. **Too large** (> ~25 nodes and cannot be trimmed to the happy path) → `rejected: too-large`.
7. **Does not render** after allow-list fixes → `rejected: render`.
8. **Target page already has 3 diagrams** and rule 4 replacement does not apply → `rejected: page-full`.

### 4.4 Source line

Directly below every imported diagram, in both EN and TH (English text in both):

```
> Diagram adapted from `carmen/docs/app/.../file.md` · verified against `carmen-turborepo-backend-v2/.../x.service.ts`, `schema.prisma` (2026-09-28)
```

When adapted, append e.g. `· Changes: removed "Pending Finance" state (not in enum)`.

### 4.5 Spot-check

After each group finishes, the orchestrator personally re-verifies 2 imported diagrams from that group before accepting it.

## 5. Placement and format

### 5.1 Placement by page type

| Page | Diagram | Where |
|---|---|---|
| `01-data-model.md` | one `erDiagram` | Start of the first entity section, before column tables |
| `02-business-rules.md` | `stateDiagram-v2` for status lifecycle | In the status/transition section; if absent, add `### x.y Status Lifecycle` |
| `03-user-flow*.md` | `flowchart` / `sequenceDiagram` | Under the matching flow heading; if none matches, add a sub-heading continuing the numbering |
| `<module>.md` landing | at most one overview `graph` | In `## 5. Related Modules`, only for a verified cross-module relation |
| `04-test-scenarios*.md` | none | — |
| Flat entity page (e.g. `master-data/location.md`, `system-config/workflow.md`, `access-control/permission.md`) | `stateDiagram-v2` / `flowchart` / `erDiagram` as fits | In the section describing that entity's lifecycle, flow, or fields; if none, add a sub-heading continuing the numbering |

### 5.2 Format rules

- Each diagram: a one-sentence lead-in or heading, the ` ```mermaid ` block, then the source line (§4.4).
- At most **3 diagrams per page**; at most ~25 nodes per diagram.
- Never renumber existing sections; new headings append as `### x.(n+1)`.
- Existing verified diagrams are kept unless §4.3 rule 4 replacement applies.
- Update frontmatter `date` on every edited page; never touch `dateCreated`.

### 5.3 Thai mirror

- The Mermaid block in `th/inventory/...` has the same structure as EN (same node ids, edges, states, participants, entities, attributes); descriptive label text — node labels, edge labels, transition/message text, notes, subgraph titles — is translated to Thai, while identifiers (status/enum values, table/column names, endpoints, HTTP methods, UI button names quoted from the app) stay English. This matches the existing TH user-flow diagrams (decision at the Task 3 checkpoint, 2026-09-28). The source line stays identical English.
- New lead-ins and headings on TH pages are written in Thai, matching that page's style.
- Placement mirrors EN (same section number).
- `scripts/diagram_catalog.py --check-parity` compares, per page pair, the count and **shape hashes** of Mermaid blocks in EN vs TH (shape = block with label text stripped) and exits non-zero on mismatch. Before any page edit, its output on the untouched branch is saved as `.specs/diagram-parity-baseline.txt`; `--baseline` suppresses those pre-existing mismatches so only new ones fail.

## 6. Execution

### 6.1 Workspace

Branch `docs/diagrams-from-carmen`; implementation runs in a separate git worktree.

### 6.2 Phases

1. **Phase 0** (orchestrator): catalog script + `.specs/diagram-catalog.md`, commit, checkpoint (§2.5).
2. **Phase 0.5** (orchestrator): render check, allow-list recorded in catalog.
3. **Phase 1**: 6 parallel subagents, disjoint file sets:

| Group | Wiki modules |
|---|---|
| G1 Procurement | purchase-request, purchase-order, vendor-pricelist |
| G2 Receiving & costing | good-receive-note, costing, general-ledger |
| G3 Stock ops | inventory, inventory-adjustment, store-requisition |
| G4 Counting | physical-count, spot-check, dashboard, reporting-audit |
| G5 Master & product | product, master-data, recipe |
| G6 Admin | access-control, system-config, templates |

Each subagent receives this spec, the allow-list, its catalog rows, and verification repo paths; is told explicitly **not to write tests**; edits only its group's EN+TH pages and writes decisions only to `.specs/diagram-decisions/<module>.tsv` for its own modules; **does not run git** (six agents committing in one worktree collide on `index.lock`). After spot-checking a group, the orchestrator rebuilds the catalog and commits that group per module as `docs(<module>): diagrams from carmen/docs (EN+TH)`.

4. **Phase 2** (orchestrator): spot-checks (§4.5), `--check-parity`, confirm no `candidate` rows remain.
5. **Phase 3**: push changed pages to dev Wiki.js with `scripts/push_pages.py`; open at least one page per diagram type in Chrome to confirm real rendering (Wiki.js fails silently on bad Mermaid).
6. **PR** to `main`; merge only after user confirmation; then sync and branch cleanup.

### 6.3 Error handling

| Situation | Handling |
|---|---|
| Subagent fails midway | Catalog shows remaining `candidate` rows; dispatch a fresh subagent for just those |
| Diagram fails to render on Wiki.js | Fix per allow-list; if still broken, mark `rejected: render` and remove from pages |
| Unmapped source folder | Listed as `unmapped` for manual decision, never silently dropped |
| Concurrent writes between groups | Prevented by construction — groups own disjoint pages and per-module decision files; only the orchestrator rebuilds the catalog and commits |

## 7. Edge Cases

| Case | Handling |
|---|---|
| Near-identical diagram in `docs/app` and `docs/documents` (different hash) | Not auto-merged; both stay `candidate`, subagent imports at most one and marks the other `rejected: covered` |
| Diagram spans two modules | Placed in the most-affected module's page; the other copy is marked `rejected: covered` with a pointer |
| TH page missing for an EN page | Report it; do not create TH pages in this effort |
| Source uses Mermaid features newer than Wiki.js supports | Allow-list rewrite, else `rejected: render` |
| Page already at 3 diagrams | `rejected: page-full` unless §4.3 rule 4 replacement applies |

## 8. Recommendations

- Keep `scripts/diagram_catalog.py` for future re-syncs: re-running it after `carmen/docs` changes surfaces new blocks by hash.
- Consider a Thai-label pass only if Thai readers report English labels as a barrier.
