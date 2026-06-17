# Inventory Wiki Re-sync — Design

**Date:** 2026-06-17
**Topic:** Re-sync the Carmen Inventory wiki book against source repos that changed since the last sync (2026-06-11).
**Status:** Approved (Approach A). Execution starts with the `purchase-order` module.

## 1. Problem

Source repositories changed substantially since the wiki's last sync on **2026-06-11**:

| Repo | Commits since 2026-06-11 | Affects |
|------|--------------------------|---------|
| `carmen-turborepo-backend-v2` | 330 | Inventory API behavior + data model (prisma migrations) |
| `carmen-inventory-frontend-react` | 109 | Inventory screen/component behavior |
| `carmen-platform` | 7 | Platform book (out of scope this round) |
| `carmen/docs`, `micro-*` | 0 | Concept docs unchanged |

The Inventory wiki book (~233 EN pages + 233 TH mirrors) may now describe stale behavior, renamed fields, removed screens, or out-of-date data models. We need to bring affected pages back in line with the implementation.

## 2. Scope

**In scope:** Inventory book only (`en/inventory/**`, `th/inventory/**`). Edit only pages whose source changed since 2026-06-11.

**Out of scope (this round):** Platform book (7 commits, deferred to a later pass); any module whose source had no material change; net-new pages for net-new features unless a clear gap is found (flag, don't silently invent).

**Source-of-truth order** (per CLAUDE.md): implementation (frontend routes + backend) and E2E tests beat `carmen/docs`, which beats memory. `carmen/docs` did not change, so the implementation diff is the primary signal this round.

## 3. Approach A — Module-sequential, diff-driven reconciliation

Process one module at a time, ordered by frontend change volume (PO → PR → workflow/access-control → store-requisition → recipe → spot-check → product → vendor-pricelist → physical-count → inventory-adjustment → master-data → dashboard → reporting-audit → costing → system-config → …). Each module is one reviewable unit and one commit.

`purchase-order` runs first and acts as the pilot: after it lands, the user reviews quality before the remaining modules proceed.

### Per-module procedure (repeatable)

For each module `M`:

1. **Collect the source delta.** `git log --since=2026-06-11` scoped to `M`'s frontend routes (`routes/<area>/<M>/**`, plus shared `types/<M>.ts`) and any clearly-related backend paths. Read the actual diffs, not just subjects. Filter out noise (tests, lockfiles, pure refactors with no behavior change).
2. **Read current source.** Open the changed frontend route/component/schema files and relevant backend handlers/prisma models at HEAD to learn the *current* behavior — not just the diff hunks.
3. **Diff against the wiki.** For each EN page under `en/inventory/<M>/`, compare what it claims against current behavior. Note divergences: renamed/removed/added fields, changed flows, changed business rules, changed data models, changed test expectations.
4. **Edit EN pages.** Apply minimal, targeted edits that bring the page in line. Preserve the doc conventions in §5. Do not rewrite unaffected sections.
5. **Mirror to TH.** Apply the equivalent change to the matching `th/inventory/<M>/` page. Keep file artifacts in English where they are code/identifiers; translate prose to Thai matching the existing TH page's style.
6. **Frontmatter.** Update `date` to the current timestamp on every edited page; leave `dateCreated` untouched.
7. **Commit** the module as one logical commit: `docs(wiki): resync <M> with <repo> changes since 2026-06-11`.

### Cross-cutting data-model changes

Prisma migrations (50 files) signal schema changes. These are handled *inside the owning module* (e.g. a PO schema change is reflected in `purchase-order/01-data-model.md`), not as a separate global pass. If a schema change spans multiple modules, reflect it in each as those modules are processed.

## 4. Verification (per module)

- Every edited claim is traceable to a current source file (cite `path:line` in the working notes, not in the page).
- EN and TH edits are paired — no EN-only or TH-only drift.
- `date` updated, `dateCreated` preserved, frontmatter still valid.
- No invented behavior: if the source is ambiguous, flag it for the user rather than guessing.
- Optional: spot-check rendering on the dev Wiki.js (`http://dev.blueledgers.com:3987/`) for heavily edited pages.

## 5. Conventions (from CLAUDE.md — preserve)

- Numbered section hierarchy (`## 1.`, `### 2.1`).
- Comparison tables for trade-offs; pseudo-code blocks (no language tag) for algorithms/data models.
- Thai Baht (`฿`) in examples.
- Edge-case + recommendations sections preserved where present.
- No inline cross-locale links (Wiki.js handles the language toggle).
- Sub-page lists use absolute-URL markdown links, not pipe wikilinks.

## 6. Out-of-scope / deferred (do not undo without asking)

- Platform book re-sync (separate later pass).
- Net-new feature pages (flag gaps; create only with user confirmation).
- Screenshot re-capture (tracked separately by the screenshot pipeline).
- Coverage-checklist regeneration (update `.specs/process-coverage-checklist.md` only if a module's coverage materially changes).
