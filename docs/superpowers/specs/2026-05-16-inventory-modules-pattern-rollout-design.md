# Inventory Modules Pattern Rollout — Design Spec

**Date:** 2026-05-16
**Status:** Approved — ready for implementation plan
**Author:** brainstorming session with @samutpra

## 1. Context

The Purchase Request (`en/purchase-request/`) and Purchase Order (`en/purchase-order/`) modules were enhanced in commit `e4c3a4a` to adopt a Test_case-inspired documentation pattern:

- **Mermaid workflow diagrams** in `03-user-flow.md` (state machine) and every `03-user-flow-{role}.md` (flow graph with the persona highlighted).
- **Permission Matrix** per role file — Status × Action, Action × Stage Role, or another shape chosen to fit the role.
- **Discrepancy callouts** flagging BRD-vs-live-UI gaps, sourced from `Test_case/Purchase_*/` files held in a sibling directory outside the wiki repo.
- **Status Lifecycle — Live UI vs BRD Mapping** table in `02-business-rules.md`.

This spec extends the same pattern to **six inventory modules** that already share the PR/PO directory shape and that have at least one corresponding Test_case file.

## 2. Goals

1. Make `02-business-rules.md` and `03-user-flow-*.md` for six inventory modules consistent with PR/PO conventions so QA and developers can use one mental model across 16 modules instead of two.
2. Surface every Test_case-confirmed BRD-vs-live-UI discrepancy in the wiki where developers and testers will actually read it, instead of leaving it in `Test_case/`.
3. Preserve the wiki ⟂ Test_case separation — Test_case stays the screen / process-level deep dive outside the wiki; wiki references it by relative path.

## 3. Non-Goals

- **Do not move Test_case files into the wiki.** They remain at `/Users/samutpra/GitHub/Test_case/`.
- **Do not add screen-level pages** to the wiki (no `05-screens-{role}.md` etc.). That is a separate, larger decision deferred to a future spec.
- **Do not refactor existing prose** beyond the three additions (Mermaid, Permission Matrix, Discrepancy callouts) and frontmatter `date:` updates. No rewording of unrelated sections.
- **Do not extend the rollout to the remaining four modules** (`inventory`, `recipe`, `vendor-pricelist`, `product`) that have no Test_case coverage — postpone to a future spec.

## 4. Scope — Six Modules in Order

The rollout proceeds module-by-module, each as its own commit. Order follows the procure-to-pay → inventory-control chain (GRN sits one step downstream of PO; spot check and physical count gate end-period close).

| # | Module | Wiki path | Primary Test_case source | Notes |
|---|---|---|---|---|
| 1 | Good Receive Note | `en/good-receive-note/` | `tx-01-grn.md` (+ `proc-01..03` for system effects) | Receiver-driven; downstream from PO `sent`. |
| 2 | Store Requisition | `en/store-requisition/` | `tx-03-sr.md` | Internal stock transfer with 3-variant nature. |
| 3 | Inventory Adjustment | `en/inventory-adjustment/` | `tx-06-stock-in-adj.md`, `tx-07-stock-out-adj.md` | Two Test_case files cover the in / out adjustments. |
| 4 | Physical Count | `en/physical-count/` | `tx-08-physical-stocktake.md` | Period-close prerequisite. |
| 5 | Spot Check | `en/spot-check/` | `tx-10-spot-check.md` | Period-close prerequisite. |
| 6 | Costing | `en/costing/` | `proc-03-cost-calculation.md` (+ tx files that trigger it) | AVCO / FIFO recompute logic. |

## 5. Per-Module Edit Pattern

Each module's commit edits **exactly three categories of files** in the wiki:

### 5.1 `02-business-rules.md`

Add **two** insertions (and update the frontmatter `date:`):

- A new **`### 5.1 Status Lifecycle — Live UI vs BRD Mapping`** subsection. Anchor: place it immediately after the posting-rules state diagram if the file has one (PO precedent); otherwise place it at the end of `## 5. Posting Rules` before `## 6. Cross-Module Rules`. Table columns: `Live UI status | BRD equivalent | Diff | Notes`. Diff legend: `✅ match | 🟡 renamed | 🔴 new in live UI | 🔵 BRD only`. If the module has no diff (Live UI matches BRD on every status), the table still appears with every row marked ✅ and a one-line note at the top reading `No diff observed against Test_case/System_Process/tx-NN-*.md at <capture date>`.
- One **`> ⚠️ Discrepancy`** callout per gap identified, placed under the rule (`<MOD>_AUTH_*`, `<MOD>_POST_*`, etc.) where the gap is most relevant. Each callout cites `Source: Test_case/System_Process/tx-NN-*.md` (capture date) and follows the convention in §6 below.

No edits to existing rule rows, calculation examples, or prose.

### 5.2 `03-user-flow.md` (module overview)

Insert one `mermaid` block of type `stateDiagram-v2` in **Section 2 (Document Lifecycle)** below the introductory paragraph, mirroring the convention used in `en/purchase-order/03-user-flow.md`. Every transition from the existing prose table must be represented as a `state --> state: label` edge. No edits to the existing transition table.

### 5.3 `03-user-flow-{role}.md` — one file per persona

In Section 1 (Role in This Module), append **two** subsections in this order:

1. `### Workflow position (<role> highlighted)` — a `graph LR` Mermaid block. The current persona's nodes use `classDef current fill:#1a56db,color:#fff,stroke:#1a56db;`. Optional `escalated` / `cfg` classes follow the conventions established by `en/purchase-request/03-user-flow-procurement-manager.md` (purple `#7c3aed` for configurational, dashed stroke for escalated paths).
2. `### Permission Matrix — <variant>` — a markdown table whose shape is chosen per role type per §5.4 below. Lead with a 1-2 sentence framing paragraph and follow with an optional `> ℹ️` note where a non-obvious caveat applies (snapshot semantics, send-back loops, segregation-of-duties).

Update the frontmatter `date:` field; never touch `dateCreated:`.

### 5.4 Permission Matrix variants — per role type

Choose at implementation time based on what the role actually controls. The six variants below are the menu; PR/PO has already exercised each one.

| Role type | Matrix shape | PR/PO precedent |
|---|---|---|
| Document owner (creator) | Status × Action | PR Requestor; PO Purchaser |
| Multi-stage approver | Action × Stage Role | PR Approver (HOD/BC/Finance) |
| Receiver / executor with sub-roles | Status × Action with sub-role columns | PO Receiver (Store Keeper / Inv Mgr) |
| External party | Event × System Effect mapping | PO Vendor |
| Bi-touchpoint (pre + post) | Touchpoint × Action | PO Finance |
| Off-path observer | Action × Sub-persona | PR / PO Audit / Config |

### 5.5 Frontmatter

Bump `date:` on every edited file to the commit timestamp (ISO-8601 UTC, hour resolution is sufficient — e.g. `2026-05-16T11:00:00.000Z`). Never modify `dateCreated:`. Wiki.js `published: true` and `editor: markdown` stay as-is.

## 6. Discrepancy Extraction Strategy

Test_case/System_Process/tx-*.md is **process-level** (status flow, swim lane, system effects) — not the screen-by-screen format used by `Test_case/Purchase_*/INDEX.md`. Discrepancies therefore surface from different anchors:

| Anchor in Test_case file | What to extract | Where it lands in wiki |
|---|---|---|
| Frontmatter `changelog` entries marked "corrected" / "updated to reflect" | The mismatch the changelog describes (e.g. GRN tx-01 v1.1.0: "BR-01 updated to reflect PO-linked and standalone GRN") | ⚠️ callout under the relevant `<MOD>_AUTH_*` or `<MOD>_POST_*` rule |
| Header block ("Who creates / Creation paths / Status flow") | The exact status-flow string and creation-path list | `### 5.x Status Lifecycle — Live UI vs BRD Mapping` table + ⚠️ callout when status names don't match BRD |
| System Effects table + Step Detail | "TBC" markers (e.g. "Lot number — system-generated or supplier-provided — TBC") | 🟡 **Verification pending** callout |
| Business Rules section (when present, `BR-NN`) | Rules flagged "TBC / Unconfirmed / Discrepancy" | ⚠️ callout linked to `<MOD>_VAL_NNN` / `<MOD>_POST_NNN` / `<MOD>_AUTH_NNN` in wiki |

### 6.1 Callout severity legend

| Marker | Use when |
|---|---|
| ⚠️ **Discrepancy** | Live UI directly conflicts with BRD (status name differs, missing state, extra state, manual step missing). |
| ℹ️ **Note** | Live UI matches BRD but a nuance matters for testers (snapshot semantics, segregation-of-duties, FX freeze, etc.). |
| 🟡 **Verification pending** | Test_case marker "TBC" — capture environment didn't cover the case. |

### 6.2 Callout body format

```
> ⚠️ **Discrepancy — <one-line topic>:** BRD <reference> specifies <X>. The live UI <does Y>. Source: `Test_case/System_Process/tx-NN-*.md` (capture date YYYY-MM-DD).
```

Always include: (a) the BRD reference identifier where available (e.g. `FR-GRN-005`), (b) what BRD says, (c) what live UI actually does, (d) source path, (e) capture date pulled from Test_case `last_updated:` frontmatter.

### 6.3 Source citation rule

Test_case lives at `/Users/samutpra/GitHub/Test_case/`, outside the wiki repo. Cite by **relative path text** only — do not turn it into a markdown link. Wiki.js cannot resolve external relative paths and turning them into links would break on publish. The text path is enough for the reader to open the file locally.

### 6.4 When a module has no discrepancies

Insert the Status Lifecycle table with every row marked ✅, and add a single line above the table: `No diff observed against Test_case/System_Process/tx-NN-*.md at <capture date>`. Do not insert any ⚠️ callouts. ℹ️ notes are still allowed where a nuance is worth surfacing.

## 7. Commit Strategy

- **One commit per module.** Six commits total.
- Commit message format (matches `e4c3a4a` precedent):
  ```
  docs(<module>): add Mermaid flows, permission matrices, and BRD-vs-live-UI discrepancy callouts
  ```
  Body explains the variants chosen for that module and the Test_case sources cited.
- Do **not** push to `origin/main` automatically — push only on explicit user request, same as the PR/PO rollout.

## 8. Effort Estimate

| Module | Files edited | Estimated diff size |
|---|---|---|
| Good Receive Note | 6 (1 rules + 1 overview + 4 role) | ~250 lines added |
| Store Requisition | 7 (1 rules + 1 overview + 5 role) | ~290 lines added |
| Inventory Adjustment | 7 (1 rules + 1 overview + 5 role) | ~290 lines added |
| Physical Count | 6 (1 rules + 1 overview + 4 role) | ~250 lines added |
| Spot Check | 6 (1 rules + 1 overview + 4 role) | ~250 lines added |
| Costing | 6 (1 rules + 1 overview + 4 role) | ~250 lines added |
| **Total** | **38 files** | **~1,580 lines added across 6 commits** |

Calibrated against the PR/PO rollout (15 files, +510 lines, 1 commit).

## 9. Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Some role files (e.g. read-only Auditor) will have a thin Permission Matrix that adds noise. | Allow the Audit / Config Permission Matrix to use the Action × Sub-persona shape (PR/PO precedent). When a sub-persona has only "view" rights, the matrix degenerates to one column — that's acceptable; it's still parallel structure. |
| Modules without obvious BRD reference IDs (e.g. costing) won't yield clean `FR-XXX` citations. | Cite the wiki rule ID (`<MOD>_CALC_NNN`) in the callout instead, with the BRD-vs-live-UI mismatch described in prose. |
| Test_case `last_updated:` capture date may drift between commits. | Read the Test_case file's frontmatter at the moment the module's commit is prepared; do not cache from this spec. |
| Roles in inventory modules may not match the six variants in §5.4 cleanly. | When in doubt, choose the closest variant and add a 1-2 sentence intro paragraph explaining the choice. Do not invent a seventh variant. |
| GRN's status flow ("Received → Committed") in Test_case may not match the Prisma enum in the wiki's `01-data-model.md`. | This is exactly the kind of discrepancy the Status Lifecycle table is designed to surface — capture both labels in the table, flag with 🔴 or 🟡, and add ⚠️ callout. |

## 10. Verification

Per-module verification after each commit:
1. `git diff --stat HEAD~1 HEAD` shows only the expected files (no accidental edits).
2. Every edited file has its `date:` field bumped; `dateCreated:` unchanged.
3. Every `03-user-flow-{role}.md` for the module contains exactly one new `### Workflow position` Mermaid block and one new `### Permission Matrix` section in Section 1.
4. `02-business-rules.md` contains the new Status Lifecycle table and (where applicable) ⚠️ callouts citing `Test_case/System_Process/tx-NN-*.md`.
5. No Mermaid block references `:::current` without a matching `classDef current` definition (would render as plain).

End-of-rollout verification:
1. `grep -l "Permission Matrix" en/{good-receive-note,store-requisition,inventory-adjustment,physical-count,spot-check,costing}/03-user-flow-*.md` returns every role file.
2. `grep -l "mermaid" en/{good-receive-note,store-requisition,inventory-adjustment,physical-count,spot-check,costing}/03-user-flow*.md` returns every file (overview + role).
3. `git log --oneline` shows exactly six new `docs(<module>):` commits on top of `e4c3a4a`.

## 11. Open Questions

None at spec-approval time. Decisions deferred to implementation:
- Exact `BR-NN` references and capture dates per module — read from Test_case file frontmatter at commit time.
- Choice of Permission Matrix variant per role — pick from the §5.4 menu after reading each role file.
