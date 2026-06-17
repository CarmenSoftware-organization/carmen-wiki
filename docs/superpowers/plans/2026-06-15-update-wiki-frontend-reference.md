# Update carmen-wiki Frontend Reference (Next.js → React/Vite) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Repoint every `carmen-inventory-frontend` documentation reference in carmen-wiki to `carmen-inventory-frontend-react`, remapping paths for the new Vite SPA structure, verified by a full leaf-file existence check.

**Architecture:** Docs-only change. One mechanical bulk transform (ordered `perl` substitutions) across the `en/`, `th/`, `docs/`, `.specs/` trees, then three small manual fix-up tasks (dashboard component restructure, one historical-spec annotation, the two README/CLAUDE prose descriptors), then a verification gate. No code, no tests. Each task is its own commit.

**Tech Stack:** Markdown + Mermaid docs; `perl -pi` for in-place edits (portable on macOS, unlike `sed -i`). Branch `docs/update-frontend-reference` (already created; spec already committed at `e950e3d`).

**Spec:** `docs/superpowers/specs/2026-06-15-update-wiki-frontend-reference-design.md`

**Working directory for every command:** `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`

**Key invariants (verified 2026-06-15):**
- `-e2e` references must stay unchanged: **256 in `en/`, 251 in `th/`**. The transform's lookahead (`(?!-)`) protects every `-` suffixed form.
- Shared dirs (`components/ hooks/ types/ constant/ lib/ utils/`) keep their names; only `app/(root)/(protected)/` route-group prefixes collapse to `routes/`.
- **This spec and plan are excluded** from the transform and the gate. They are meta-documents about the rename and intentionally name *both* repos (`carmen-inventory-frontend` and `…-react`); rewriting them would corrupt their meaning. Every command below carries `! -path '*2026-06-15-update-wiki-frontend-reference*'` (for `find`) or `--exclude='2026-06-15-update-wiki-frontend-reference*'` (for `grep`).

---

### Task 1: Bulk mechanical transform across content trees

**Files:**
- Modify: every `*.md` under `en/`, `th/`, `docs/`, `.specs/` that contains a bare `carmen-inventory-frontend` token (README.md and CLAUDE.md are intentionally **excluded** here — handled in Task 4).

- [ ] **Step 1: Record the baseline counts**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
echo -n "e2e en (must stay): "; grep -rho "carmen-inventory-frontend-e2e" en | wc -l
echo -n "e2e th (must stay): "; grep -rho "carmen-inventory-frontend-e2e" th | wc -l
echo -n "bare en+th+docs+.specs (should go to 0 after Tasks 1-4): "; \
  grep -rhoE --exclude='2026-06-15-update-wiki-frontend-reference*' "carmen-inventory-frontend(-e2e|-react)?" en th docs .specs \
  | grep -vE "carmen-inventory-frontend-(e2e|react)" | wc -l
```
Expected: e2e en = `256`, e2e th = `251`, bare ≈ `288`.

- [ ] **Step 2: Apply the ordered transform**

The four substitutions run in order: most-specific path prefix first, then a generic lookahead-guarded repo-token rename that catches every remaining bare form (paths *and* prose mentions) while leaving `-e2e`/`-react` untouched.

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
find en th docs .specs -type f -name '*.md' ! -path '*2026-06-15-update-wiki-frontend-reference*' -print0 | xargs -0 perl -pi -e '
  s{carmen-inventory-frontend/app/\(root\)/\(protected\)/}{carmen-inventory-frontend-react/routes/}g;
  s{carmen-inventory-frontend/app/\(root\)/}{carmen-inventory-frontend-react/routes/}g;
  s{carmen-inventory-frontend/app/}{carmen-inventory-frontend-react/routes/}g;
  s{carmen-inventory-frontend(?!-)}{carmen-inventory-frontend-react}g;
'
# Second pass: bare top-level `app` dir with no trailing slash (e.g. `ls ../carmen-inventory-frontend/app`
# or prose "from `…/app`") — the new repo has no top-level app/, so map it to routes too.
find en th docs .specs -type f -name '*.md' ! -path '*2026-06-15-update-wiki-frontend-reference*' -print0 \
  | xargs -0 perl -pi -e 's{carmen-inventory-frontend-react/app\b}{carmen-inventory-frontend-react/routes}g;'
```

- [ ] **Step 3: Verify the mechanical pass**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
# No app/ or route-group prefixes survived (exclude this plan/spec, which quote the token literally):
grep -rn --exclude='2026-06-15-update-wiki-frontend-reference*' "carmen-inventory-frontend-react/app" en th docs .specs        # expect: no output
grep -rn --exclude='2026-06-15-update-wiki-frontend-reference*' "carmen-inventory-frontend-react/routes/(protected)" en th docs .specs  # expect: no output
# e2e refs untouched:
echo -n "e2e en: "; grep -rho "carmen-inventory-frontend-e2e" en | wc -l   # expect: 256
echo -n "e2e th: "; grep -rho "carmen-inventory-frontend-e2e" th | wc -l   # expect: 251
# Bare tokens remaining in these trees:
grep -rnE --exclude='2026-06-15-update-wiki-frontend-reference*' "carmen-inventory-frontend(-e2e|-react)?" en th docs .specs \
  | grep -vE "carmen-inventory-frontend-(e2e|react)"                       # expect: no output
```
Expected: first two greps empty; e2e counts unchanged (256 / 251); last grep empty (every bare token is now `-react`).

- [ ] **Step 4: Commit**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
git add en th docs .specs
git commit -m "docs(wiki): point frontend refs to carmen-inventory-frontend-react (bulk rename + route remap)"
```

---

### Task 2: Category B — dashboard sub-pages restructured to components

After Task 1, the dashboard per-route page references resolve to `routes/dashboard/<sub>/page.tsx`, which **do not exist** in the new repo — those sub-dashboards were merged into `routes/dashboard/_components/dashboard-<sub>.tsx` (all six confirmed present). Fix both the 12 explicit lines and the one brace-shorthand line.

**Files:**
- Modify: `en/inventory/dashboard/{grn,pr,po,sr,inventory,main}.md` and `th/inventory/dashboard/{grn,pr,po,sr,inventory,main}.md` (12 files, one `**Page shell:**` line each)
- Modify: `en/inventory/dashboard.md:78`, `th/inventory/dashboard.md:78` (the brace-shorthand line)

- [ ] **Step 1: Remap the explicit and brace-shorthand page-shell paths**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
find en th -type f -name '*.md' -print0 | xargs -0 perl -pi -e '
  s{routes/dashboard/(grn|pr|po|sr|inventory|main)/page\.tsx}{routes/dashboard/_components/dashboard-$1.tsx}g;
  s{routes/dashboard/\{main,pr,po,grn,inventory,sr\}/page\.tsx}{routes/dashboard/_components/dashboard-{main,pr,po,grn,inventory,sr}.tsx}g;
'
```

- [ ] **Step 2: Verify no stale dashboard page-shell paths remain**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
# Old non-existent form gone:
grep -rnE "routes/dashboard/(grn|pr|po|sr|inventory|main)/page\.tsx" en th        # expect: no output
grep -rn  "routes/dashboard/{main,pr,po,grn,inventory,sr}/page.tsx" en th          # expect: no output
# New component targets present (12 explicit + 2 brace lines = appears across files):
grep -rnE "routes/dashboard/_components/dashboard-(grn|pr|po|sr|inventory|main)\.tsx" en th | wc -l   # expect: 14
# Confirm the six component files truly exist in the new repo:
for s in grn pr po sr inventory main; do
  test -e ../carmen-inventory-frontend-react/routes/dashboard/_components/dashboard-$s.tsx \
    && echo "OK dashboard-$s.tsx" || echo "MISS dashboard-$s.tsx"
done
```
Expected: first two greps empty; the count line prints `14`; all six print `OK`.

- [ ] **Step 3: Commit**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
git add en th
git commit -m "docs(wiki): remap dashboard sub-page refs to routes/dashboard/_components/dashboard-*.tsx"
```

---

### Task 3: Category D — annotate the old-repo-only historical spec

The "Widget rewrite spec" reference now reads `…-react/docs/superpowers/specs/2026-05-22-widget-rewrite-design.md`, but that spec exists **only in the old Next.js repo**. Append an inline historical note so the path is not left implying the file exists in the new repo.

**Files:**
- Modify: `en/inventory/dashboard/widget-workspace.md:109`
- Modify: `th/inventory/dashboard/widget-workspace.md:109`

- [ ] **Step 1: Edit `en/inventory/dashboard/widget-workspace.md`**

Replace:
```
- **Widget rewrite spec:** `../carmen-inventory-frontend-react/docs/superpowers/specs/2026-05-22-widget-rewrite-design.md`
```
with:
```
- **Widget rewrite spec:** `../carmen-inventory-frontend-react/docs/superpowers/specs/2026-05-22-widget-rewrite-design.md` _(historical; this spec lived in the legacy Next.js frontend repo and was not carried over to -react)_
```

- [ ] **Step 2: Edit `th/inventory/dashboard/widget-workspace.md`**

Replace:
```
- **Widget rewrite spec:** `../carmen-inventory-frontend-react/docs/superpowers/specs/2026-05-22-widget-rewrite-design.md`
```
with:
```
- **Widget rewrite spec:** `../carmen-inventory-frontend-react/docs/superpowers/specs/2026-05-22-widget-rewrite-design.md` _(historical; this spec lived in the legacy Next.js frontend repo and was not carried over to -react)_
```

- [ ] **Step 3: Verify**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
grep -rc "_(historical; this spec lived in the legacy Next.js frontend repo and was not carried over to -react)_" \
  en/inventory/dashboard/widget-workspace.md th/inventory/dashboard/widget-workspace.md
```
Expected: each file prints `1`.

- [ ] **Step 4: Commit**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
git add en/inventory/dashboard/widget-workspace.md th/inventory/dashboard/widget-workspace.md
git commit -m "docs(wiki): annotate historical widget-rewrite spec ref (old Next.js repo only)"
```

---

### Task 4: README.md + CLAUDE.md — repo token and tech descriptor

These two repo-root files were excluded from Task 1. Update both the path token and the "Next.js … App Router" prose to the new Vite SPA.

**Files:**
- Modify: `README.md:137`
- Modify: `CLAUDE.md:67`

- [ ] **Step 1: Edit `README.md`**

Replace:
```
| `../carmen-inventory-frontend/` | Next.js inventory UI — source of truth for Inventory screen behaviour |
```
with:
```
| `../carmen-inventory-frontend-react/` | Vite + React SPA inventory UI — source of truth for Inventory screen behaviour |
```

- [ ] **Step 2: Edit `CLAUDE.md`**

Replace:
```
| **Frontend** | `../carmen-inventory-frontend/` | Next.js inventory UI — App Router, TypeScript, Tailwind, Bun, Vitest, Playwright. Source of truth for screen/component behavior. Has its own `CLAUDE.md` and `DESIGN.md`. |
```
with:
```
| **Frontend** | `../carmen-inventory-frontend-react/` | Vite + React SPA inventory UI — React Router, TypeScript, Tailwind, Bun, Vitest, Playwright. Source of truth for screen/component behavior. Has its own `CLAUDE.md` and `DESIGN.md`. |
```

- [ ] **Step 3: Verify**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
# Frontend rows updated, e2e rows (also in these files) untouched:
grep -nE "carmen-inventory-frontend(-e2e|-react)?" README.md CLAUDE.md \
  | grep -vE "carmen-inventory-frontend-(e2e|react)"        # expect: no output (no bare token left)
grep -n "Vite + React SPA inventory UI" README.md CLAUDE.md  # expect: one hit each
```
Expected: first grep empty; second prints one line per file.

- [ ] **Step 4: Commit**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
git add README.md CLAUDE.md
git commit -m "docs(wiki): point frontend ref to carmen-inventory-frontend-react + correct tech (Vite SPA)"
```

---

### Task 5: Final verification gate (full leaf-file existence check)

**Files:** none (read-only check)

- [ ] **Step 1: Zero bare tokens anywhere in carmen-wiki**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
grep -rnE --exclude='2026-06-15-update-wiki-frontend-reference*' "carmen-inventory-frontend(-e2e|-react)?" en th docs .specs CLAUDE.md README.md \
  | grep -vE "carmen-inventory-frontend-(e2e|react)"        # expect: no output
```
Expected: no output (every remaining occurrence is `-react` or `-e2e`).

- [ ] **Step 2: Run the full leaf-existence check**

This extracts every distinct `-react` path reference, skips brace-glob shorthands (`{…}`), and checks each against the new repo. The **only** acceptable miss is the annotated historical widget-rewrite spec.

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
NEW=../carmen-inventory-frontend-react
grep -rhoE --exclude='2026-06-15-update-wiki-frontend-reference*' "carmen-inventory-frontend-react/[^ \`\",<>]*" en th docs .specs CLAUDE.md README.md \
  | sed 's#^carmen-inventory-frontend-react/##; s#/$##' \
  | sed -E 's#[).:;]+$##' \
  | sort -u \
  | while IFS= read -r p; do
      [ -z "$p" ] && continue
      case "$p" in *'{'*|*'}'*) continue;; esac      # skip brace-glob shorthand
      [ -e "$NEW/$p" ] || echo "MISS: $p"
    done
```
Expected output (exactly one line):
```
MISS: docs/superpowers/specs/2026-05-22-widget-rewrite-design.md
```
If any **other** path is reported MISS, it is a broken reference — investigate before declaring done. If a `MISS` is a real file that moved, remap it to the new location; if it is a not-yet-migrated route, annotate it `(not yet in -react)` like Task 3.

- [ ] **Step 3: Parity sanity check (informational)**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
echo -n "e2e en (expect 256): "; grep -rho "carmen-inventory-frontend-e2e" en | wc -l
echo -n "e2e th (expect 251): "; grep -rho "carmen-inventory-frontend-e2e" th | wc -l
echo -n "react refs en: "; grep -rho "carmen-inventory-frontend-react" en | wc -l
echo -n "react refs th: "; grep -rho "carmen-inventory-frontend-react" th | wc -l
```
Expected: e2e counts unchanged at 256 / 251 (the transform never touched them). The `-react` counts for `en` and `th` should be close but need not match exactly — the two trees are not perfectly mirrored at baseline (en had a few more refs than th). The hard gate is Steps 1–2; this step is a smell test only.

- [ ] **Step 4: Review the full diff**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
git log --oneline main..HEAD
git diff --stat main..HEAD
```
Expected: 5 commits (spec + Tasks 1–4), only files under `en/`, `th/`, `docs/`, `.specs/`, plus `README.md` and `CLAUDE.md` touched. No files outside carmen-wiki.
