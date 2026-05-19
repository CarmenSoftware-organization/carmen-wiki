# Folder Default Pages — Standardize on index.md + Upgrade Platform Stubs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rename every per-folder landing page in the wiki from `home.md` to `index.md` (18 files across language root, book, and Platform module levels), update the navigation script, config, URL references, and a handful of doc files in one atomic structural commit; then upgrade the six Platform module landing pages from stubs to the canonical 7-section Inventory template, in EN+TH parity, one commit per module.

**Architecture:** Seven sequential units. **Unit 0** is one atomic commit that does all the structural changes — file renames, script updates, YAML config, URL updates inside renamed files, and stray text references. After U0 the repo is on a consistent `index.md` baseline and Wiki.js still works; Platform pages remain stubs (acceptable interim state). **Units 1–6** each upgrade one Platform module's content (EN + TH together in a single commit per module), sequenced light→heavy: profile → auth-roles → report-templates → business-units → clusters → users.

**Tech Stack:** Markdown content with Wiki.js YAML frontmatter, Python 3 (`scripts/sync_nav.py` using `frontmatter`, `gql`, `yaml`), pytest, Wiki.js at `dev.blueledgers.com:3987`.

**Spec:** `docs/superpowers/specs/2026-05-19-folder-default-pages-design.md`

---

## File Structure

### Files renamed in U0 (18, via `git mv`)

| Level | Path before | Path after |
|---|---|---|
| Lang root EN | `en/home.md` | `en/index.md` |
| Lang root TH | `th/home.md` | `th/index.md` |
| Book EN inv | `en/inventory/home.md` | `en/inventory/index.md` |
| Book EN plat | `en/platform/home.md` | `en/platform/index.md` |
| Book TH inv | `th/inventory/home.md` | `th/inventory/index.md` |
| Book TH plat | `th/platform/home.md` | `th/platform/index.md` |
| Platform EN modules (6) | `en/platform/{auth-roles,business-units,clusters,profile,report-templates,users}/home.md` | `…/index.md` |
| Platform TH modules (6) | `th/platform/{auth-roles,business-units,clusters,profile,report-templates,users}/home.md` | `…/index.md` |

### Other files modified in U0

| File | Edit | Purpose |
|---|---|---|
| `scripts/sync_nav.py` | rename function, rename enum, update 4 hardcoded paths, update format string, update log message | drop hardcoded `home.md` dependency |
| `scripts/test_sync_nav.py` | update test fixtures, imports, assertions to use `index.md` and `LabelSource.INDEX_MD` | tests track the rename |
| `scripts/nav-overrides.yaml` | `home_slug: home` → `home_slug: index` (both books) | nav URL slug now matches filename |
| `README.md` | line 10 `/en/home` → `/en/index` | documented landing URL matches reality |
| `CLAUDE.md` | reword section that says "repo root `home.md`" — there is no root home.md; correct to `en/index.md` / `th/index.md` (after rename) | doc accuracy |
| `en/platform/clusters/permissions.md` | line 26 `auth-roles/home.md` → `auth-roles/index.md` | stray text ref |
| `th/platform/clusters/permissions.md` | line 26 same edit | TH counterpart |
| `en/index.md` (was `en/home.md`) | 2 URLs `/<book>/home` → `/<book>/index` | language-root → book links |
| `th/index.md` (was `th/home.md`) | 2 URLs same | |
| `en/inventory/index.md` | ~18 URLs `/<book>/<module>/home` → `/<book>/<module>/index` | book → module links |
| `en/platform/index.md` | ~6 URLs same | |
| `th/inventory/index.md` | ~18 URLs same | |
| `th/platform/index.md` | ~6 URLs same | |

### Files modified in Units 1–6 (per Platform module)

For each module `<m>` ∈ {profile, auth-roles, report-templates, business-units, clusters, users}:

| File | Edit |
|---|---|
| `en/platform/<m>/index.md` | full rewrite — 7-section canonical template, content sourced from `../carmen-platform/SITEMAP.md` and `../carmen-platform/src/pages/<Page>.tsx` |
| `th/platform/<m>/index.md` | full rewrite — Thai translation matching EN |

### Explicitly not touched

- `en/inventory/<module>/index.md` (18 files, both locales) — already at target state
- `*.md` files inside `en/inventory/<module>/` sub-pages — `./index` back-links already correct
- `docs/superpowers/plans/*.md`, `docs/superpowers/specs/*.md` — historical record
- Wiki.js admin settings (manual step, not file-based)

---

## Unit 0 — Structural Rename (Atomic Commit)

All Unit 0 tasks happen in sequence with **no intermediate commits**. The single commit at Task 8 ships them all.

### Task 1: Pre-flight inventory and baseline check

**Files:** none (read-only verification)

- [ ] **Step 1: Verify all 18 source files exist before rename**

Run:
```bash
for f in en/home.md th/home.md \
         en/inventory/home.md en/platform/home.md \
         th/inventory/home.md th/platform/home.md \
         en/platform/{auth-roles,business-units,clusters,profile,report-templates,users}/home.md \
         th/platform/{auth-roles,business-units,clusters,profile,report-templates,users}/home.md; do
  [ -f "$f" ] && echo "OK   $f" || echo "MISS $f"
done | sort -u | head -40
```

Expected: 18 lines, all "OK", zero "MISS".

- [ ] **Step 2: Capture baseline test result**

Run: `cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki && pytest scripts/ -q`

Expected: all tests pass (this is the pre-change baseline; if it doesn't pass, stop and report — something else is broken).

- [ ] **Step 3: Capture baseline URL reference counts**

Run:
```bash
echo "URLs ending in /home in book/lang-root files:"
grep -c "/home)" en/home.md th/home.md en/inventory/home.md en/platform/home.md th/inventory/home.md th/platform/home.md 2>/dev/null
echo ""
echo "home.md text refs in current-content files (expected: 2 — clusters/permissions.md EN+TH):"
grep -rn "home\.md" en/ th/ 2>/dev/null | grep -v "/inventory/" | wc -l
```

Expected counts shown by `grep -c` per file: `en/home.md`=2, `th/home.md`=2, `en/inventory/home.md`≈18, `en/platform/home.md`≈6, same for TH — total ≈52 across the six files. Second count (text refs to `home.md` outside Inventory): 2 (the EN and TH `clusters/permissions.md`).

Record the numbers shown — Task 7 verification re-checks the counterparts (`/index)` and zero stray `home.md`).

- [ ] **Step 4: No commit (Task 1 is read-only)**

Proceed to Task 2.

---

### Task 2: Update `scripts/test_sync_nav.py` to expect `index.md`

**Files:**
- Modify: `scripts/test_sync_nav.py:4, 9, 23, 30, 58, 186, 190, 202, 334, 349, 381, 389, 401, 405, 422, 426, 439, 471, 485, 514, 542, 569, 615, 635`

This task updates only the tests. Tests will go RED here — that's the desired TDD state. Task 3 makes them GREEN.

- [ ] **Step 1: Update test imports and fixtures**

In `scripts/test_sync_nav.py`:

Change line 4:
```python
from scripts.sync_nav import parse_home_headings
```
to:
```python
from scripts.sync_nav import parse_index_headings
```

Within the three test functions `test_parse_home_headings_*` (currently at lines 7, 21, 28), rename them to `test_parse_index_headings_*` and update each function body:
- Line 9, 23, 30: `home = tmp_path / "home.md"` → `index_md = tmp_path / "index.md"`
- The variable `home` is used as a Path; rename references inside each test function (`home.write_text(...)`, `parse_home_headings(home)`) to use `index_md` and the renamed function `parse_index_headings`.

- [ ] **Step 2: Update warning-message assertion**

Line 58 currently:
```python
assert any("home.md heading count" in r.message for r in caplog.records)
```
Change to:
```python
assert any("index.md heading count" in r.message for r in caplog.records)
```

- [ ] **Step 3: Update LabelSource enum-value test references**

Line 186 currently:
```python
assert source == LabelSource.HOME_MD
```
Change to:
```python
assert source == LabelSource.INDEX_MD
```

Update docstrings on lines 190 and 202:
- Line 190 `"""home.md doesn't have it → overrides.headers wins."""` → `"""index.md doesn't have it → overrides.headers wins."""`
- Line 202 `"""No home.md match, no override → EN label."""` → `"""No index.md match, no override → EN label."""`

- [ ] **Step 4: Update count-dict keys and assertion strings**

Search the file for `"home.md"` used as a count dict key. Lines around 334 (comment `# home.md`), 349 (`"home.md": 1,`), 381 (`"home.md": 6,`), 389 (`assert "6 home.md" in s`), 422 (comment `# home.md exact-match self-pair`), 426 (`counts["home.md"]`): replace each occurrence of the literal string `"home.md"` with `"index.md"` and each comment mentioning `home.md` with `index.md`.

- [ ] **Step 5: Update test path fixtures and YAML test configs**

Lines 401 and 405 — `tmp_path / "th" / "home.md"` and `tmp_path / "en" / "home.md"` → `index.md` for both.

Lines 439, 471, 485, 514, 542, 569, 615, 635 — in each test dict literal containing `"home_slug": "home",`, change to `"home_slug": "index",`.

- [ ] **Step 6: Run tests — expect failures**

Run: `cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki && pytest scripts/ -q`

Expected: tests fail with `ImportError: cannot import name 'parse_index_headings'` and/or `AttributeError: type object 'LabelSource' has no attribute 'INDEX_MD'`. Some count-dict tests will also fail with KeyError on `"index.md"`. This is the desired RED state.

- [ ] **Step 7: No commit (atomic with rest of U0)**

Proceed to Task 3.

---

### Task 3: Update `scripts/sync_nav.py` to match new test expectations

**Files:**
- Modify: `scripts/sync_nav.py:30-31, 46, 54, 102, 133, 377, 397, 398, 467, 468`

- [ ] **Step 1: Rename function `parse_home_headings` → `parse_index_headings`**

In `scripts/sync_nav.py` line 30, change the function definition:
```python
def parse_home_headings(home_md: Path) -> list[str]:
    """Parse `## N. <text>` headings from a home.md file, in document order.
```
to:
```python
def parse_index_headings(index_md: Path) -> list[str]:
    """Parse `## N. <text>` headings from an index.md file, in document order.
```

Update the docstring body (lines 31–36) so the description matches: replace any remaining `home.md` text inside the docstring with `index.md`. Update the parameter reference inside the body — line 38 currently reads `for line in home_md.read_text(encoding="utf-8").splitlines():`; change to `for line in index_md.read_text(encoding="utf-8").splitlines():`.

- [ ] **Step 2: Update `build_header_label_map` docstring and warning**

Line 46 docstring: `"""Pair EN and TH home.md headings by index → {en_text: th_text}.`  → replace `home.md` with `index.md`.

Line 54 log message: `"home.md heading count mismatch: en=%d th=%d — pairing up to min"` → replace `home.md` with `index.md`.

- [ ] **Step 3: Rename `LabelSource.HOME_MD` → `LabelSource.INDEX_MD`**

Line 102 in the `LabelSource` enum:
```python
HOME_MD = "home.md"
```
Change to:
```python
INDEX_MD = "index.md"
```

Line 133 — usage inside `resolve_label`:
```python
return header_map[item["label"]], LabelSource.HOME_MD
```
Change to:
```python
return header_map[item["label"]], LabelSource.INDEX_MD
```

- [ ] **Step 4: Update `format_summary` count key**

Line 377:
```python
f"·  {counts.get('home.md', 0)} home.md  "
```
Change to:
```python
f"·  {counts.get('index.md', 0)} index.md  "
```

- [ ] **Step 5: Update hardcoded path references**

Four locations need the same edit. Lines 397–398 in `run_sync`:
```python
en_home = parse_home_headings(repo_root / "en" / "home.md")
th_home = parse_home_headings(repo_root / "th" / "home.md")
```
Change to:
```python
en_index = parse_index_headings(repo_root / "en" / "index.md")
th_index = parse_index_headings(repo_root / "th" / "index.md")
```

Update the next line that references these variables (line 399):
```python
header_map = build_header_label_map(en_home, th_home)
```
Change to:
```python
header_map = build_header_label_map(en_index, th_index)
```

Lines 467–468 inside `_run_mirror_mode` verbose block:
```python
header_map=build_header_label_map(
    parse_home_headings(repo_root / "en" / "home.md"),
    parse_home_headings(repo_root / "th" / "home.md"),
),
```
Change to:
```python
header_map=build_header_label_map(
    parse_index_headings(repo_root / "en" / "index.md"),
    parse_index_headings(repo_root / "th" / "index.md"),
),
```

- [ ] **Step 6: Update the `home_slug` fallback default**

Line 664 in `build_tree_from_config`:
```python
home_slug = book.get("home_slug", "home")
```
Change to:
```python
home_slug = book.get("home_slug", "index")
```

(The YAML config now always provides this key explicitly — see Task 4 — but updating the fallback keeps the default consistent with the new convention for any future book that omits the key. The YAML key name `home_slug` is intentionally left unchanged; renaming the field itself would force a YAML schema migration for no functional gain.)

- [ ] **Step 7: Run tests — expect pass**

Run: `cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki && pytest scripts/ -q`

Expected: all tests pass. If any fail, re-read the failure and reconcile with Task 2's test edits — the test file is the contract.

- [ ] **Step 8: Final grep verification on sync_nav.py**

Run:
```bash
grep -n "home\.md\|HOME_MD\|parse_home_headings\|\"home\"" scripts/sync_nav.py
```

Expected: zero matches.

- [ ] **Step 9: No commit (atomic with rest of U0)**

Proceed to Task 4.

---

### Task 4: Update `scripts/nav-overrides.yaml`

**Files:**
- Modify: `scripts/nav-overrides.yaml` (two `home_slug:` lines)

- [ ] **Step 1: Change both `home_slug` values**

In `scripts/nav-overrides.yaml`, find:
```yaml
books:
  inventory:
    label_en: "Carmen Inventory"
    label_th: "Carmen Inventory"
    home_slug: home
```
Change `home_slug: home` to `home_slug: index`.

Find the corresponding block for `platform:` further down (around line 88) and change its `home_slug: home` to `home_slug: index` the same way.

- [ ] **Step 2: Verify zero remaining `home_slug: home`**

Run: `grep -n "home_slug:" scripts/nav-overrides.yaml`

Expected: 2 lines, both showing `home_slug: index`.

- [ ] **Step 3: No commit**

Proceed to Task 5.

---

### Task 5: Rename all 18 files with `git mv`

**Files:** the 18 listed in the "Files renamed in U0" table above.

`git mv` preserves history — `git log --follow` on any renamed file will continue past the rename.

- [ ] **Step 1: Rename language-root files**

```bash
git mv en/home.md en/index.md
git mv th/home.md th/index.md
```

- [ ] **Step 2: Rename book-level files**

```bash
git mv en/inventory/home.md en/inventory/index.md
git mv en/platform/home.md en/platform/index.md
git mv th/inventory/home.md th/inventory/index.md
git mv th/platform/home.md th/platform/index.md
```

- [ ] **Step 3: Rename Platform module files (EN + TH)**

```bash
for m in auth-roles business-units clusters profile report-templates users; do
  git mv "en/platform/$m/home.md" "en/platform/$m/index.md"
  git mv "th/platform/$m/home.md" "th/platform/$m/index.md"
done
```

- [ ] **Step 4: Verify no `home.md` remains in content folders**

Run: `find en th -name home.md`

Expected: zero output.

- [ ] **Step 5: Verify 18 new `index.md` exist where expected**

Run:
```bash
find en/inventory en/platform th/inventory th/platform -maxdepth 2 -name index.md | wc -l
ls en/index.md th/index.md
```

Expected: first count 24 (18 module index.md from Inventory unchanged + 6 Platform module index.md just renamed + 4 book-level just renamed = 28; actually 18 Inventory + 6 Platform + 4 book = 28). Wait — let me recount: `find en/inventory en/platform th/inventory th/platform -maxdepth 2 -name index.md` returns:
- `en/inventory/index.md` (book, renamed) — 1
- `en/inventory/<18 modules>/index.md` — wait, `-maxdepth 2` from `en/inventory` means it sees `en/inventory/index.md` at depth 1 and `en/inventory/<m>/index.md` at depth 2. So 1 + 18 + 1 + 6 + 1 + 18 + 1 + 6 = 52? No — `find` is invoked with 4 separate roots. Let me re-derive: 4 roots × (1 book-level + N module-level) where N is 18 (inv) or 6 (plat). Result: (1+18) + (1+6) + (1+18) + (1+6) = 52.

Use a simpler verification:
```bash
find en/inventory en/platform th/inventory th/platform -mindepth 1 -maxdepth 2 -name index.md | wc -l
```
Expected: 52.

```bash
ls en/index.md th/index.md
```
Expected: both files listed (no error).

- [ ] **Step 6: No commit**

Proceed to Task 6.

---

### Task 6: Update URLs inside renamed book and language-root pages

**Files:**
- Modify: `en/index.md`, `th/index.md`, `en/inventory/index.md`, `en/platform/index.md`, `th/inventory/index.md`, `th/platform/index.md`

- [ ] **Step 1: Update language-root files**

In `en/index.md`, replace:
- `/en/inventory/home` → `/en/inventory/index`
- `/en/platform/home` → `/en/platform/index`

In `th/index.md`, replace:
- `/th/inventory/home` → `/th/inventory/index`
- `/th/platform/home` → `/th/platform/index`

Use Edit tool per file (each has 2 URL refs).

- [ ] **Step 2: Update EN book home pages**

In `en/inventory/index.md`, replace all `/en/inventory/<module>/home` → `/en/inventory/<module>/index`. Use Edit with `replace_all=true` on the pattern `/home)` → `/index)` after verifying the file contains no other `/home)` occurrences.

Quickest method: open the file and inspect — every module link is a Markdown table row like `[Costing](/en/inventory/costing/home)`. The trailing `)` distinguishes URL endings from accidental matches in prose. A single `replace_all` of `/home)` to `/index)` covers all 18 URLs in one edit.

Repeat for `en/platform/index.md` (6 URLs).

- [ ] **Step 3: Update TH book home pages**

Same as Step 2 but for `th/inventory/index.md` and `th/platform/index.md`.

- [ ] **Step 4: Verify zero remaining `/home)` in content**

Run:
```bash
grep -rn "/home)" en/ th/ 2>/dev/null
```

Expected: zero output.

- [ ] **Step 5: No commit**

Proceed to Task 7.

---

### Task 7: Update remaining text references (README, CLAUDE.md, permissions.md)

**Files:**
- Modify: `README.md`, `CLAUDE.md`, `en/platform/clusters/permissions.md`, `th/platform/clusters/permissions.md`

- [ ] **Step 1: Update `README.md`**

Find line 10 (or wherever `/en/home` appears):
```markdown
| Rendered wiki (dev) | <http://dev.blueledgers.com:3987/> — landing at `/en/home` |
```

Change to:
```markdown
| Rendered wiki (dev) | <http://dev.blueledgers.com:3987/> — landing at `/en/index` |
```

- [ ] **Step 2: Update `CLAUDE.md`**

In `CLAUDE.md`, find the passage describing the landing structure. The current wording mentions "repo root `home.md`" — there is no such file (the actual landings are `en/home.md` and `th/home.md`, which are being renamed to `en/index.md` and `th/index.md`). Correct the passage to refer to `en/index.md` and `th/index.md` as the language-root two-card landings.

Specifically the line currently containing:
> The repo root `home.md` is a two-card landing; each book has its own `<book>/home.md` index.

Change to:
> The language-root pages `en/index.md` and `th/index.md` are the two-card landings; each book has its own `<book>/index.md` page that opens the book.

If `CLAUDE.md` contains other `home.md` or `/home` references, update those too. Run `grep -n "home" CLAUDE.md` and inspect each match — keep matches that refer to the Carmen domain or unrelated text; update matches that refer to the wiki landing-page filename convention.

- [ ] **Step 3: Update `en/platform/clusters/permissions.md`**

Find line 26:
```markdown
- [ ] Cross-link to auth-roles/home.md for role definitions
```

Change to:
```markdown
- [ ] Cross-link to auth-roles/index.md for role definitions
```

- [ ] **Step 4: Update `th/platform/clusters/permissions.md`**

Identical edit on the TH counterpart.

- [ ] **Step 5: Verify zero remaining text references**

Run:
```bash
grep -rn "home\.md\|/en/home\|/th/home" en/ th/ README.md CLAUDE.md scripts/ 2>/dev/null | grep -v "/inventory/"
```

Expected: zero output. (Historical references inside `docs/superpowers/` are out of scope per the spec.)

- [ ] **Step 6: No commit**

Proceed to Task 8.

---

### Task 8: U0 verification + atomic commit

- [ ] **Step 1: Run full test suite**

Run: `cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki && pytest scripts/ -q`

Expected: all tests pass.

- [ ] **Step 2: Sanity-check sync_nav.py build mode**

Run: `python -c "import scripts.sync_nav; print('import ok')"`

Expected: `import ok`.

Run the build-mode dry-run (no network, just config parsing + tree assembly):
```bash
WIKI_API_URL=http://localhost WIKI_API_TOKEN=fake \
  python scripts/sync_nav.py --mode=build --dry-run 2>&1 | head -20
```

Expected: output begins with `[BUILD]  en: N items, th: N items` then `[DRY-RUN] tree preview:` followed by lines that include `/en/inventory/index`, `/en/platform/index`, `/en/inventory/<module>/index`, etc. (NOT `/home`). If `WIKI_API_URL`/`WIKI_API_TOKEN` env vars are unset the script exits with the "must be set" error — that's why we set fake values; build mode does not actually call the API.

- [ ] **Step 3: Final grep sweep**

Run:
```bash
echo "Should be 0:"; grep -rn "home\.md" en/ th/ README.md CLAUDE.md scripts/ 2>/dev/null | grep -v "/inventory/" | wc -l
echo "Should be 0:"; grep -rn "/home)" en/ th/ 2>/dev/null | wc -l
echo "Should be 0:"; grep -n "HOME_MD\|parse_home_headings\|home_slug: home" scripts/sync_nav.py scripts/nav-overrides.yaml scripts/test_sync_nav.py 2>/dev/null | wc -l
echo "Should be 52:"; find en/inventory en/platform th/inventory th/platform -mindepth 1 -maxdepth 2 -name index.md | wc -l
```

All four counts must match the comment.

- [ ] **Step 4: Stage all changes and inspect**

Run: `git status`

Expected output should show:
- 18 renames (R) of `home.md` → `index.md`
- Modified: `scripts/sync_nav.py`, `scripts/test_sync_nav.py`, `scripts/nav-overrides.yaml`, `README.md`, `CLAUDE.md`, `en/platform/clusters/permissions.md`, `th/platform/clusters/permissions.md`
- Modified (URL updates inside renamed files — git tracks these as R + content changes on the same path)

Run: `git diff --stat --cached HEAD 2>/dev/null || git diff --stat HEAD`

Spot-check the count: roughly 25 files changed.

- [ ] **Step 5: Commit U0 atomically**

```bash
git add -A
git commit -m "$(cat <<'EOF'
docs(structure): rename home.md → index.md at all levels

Standardize the per-folder landing page filename to index.md across the
whole wiki:

- 18 file renames: en/home.md, th/home.md (lang-root); 4 book-level
  files; 12 Platform module files (6 EN + 6 TH). Inventory module
  index.md files unchanged — they were already on the target name.
- scripts/sync_nav.py: rename parse_home_headings → parse_index_headings,
  LabelSource.HOME_MD → INDEX_MD, update 4 hardcoded paths.
- scripts/test_sync_nav.py: mirror the above.
- scripts/nav-overrides.yaml: home_slug: home → home_slug: index (both
  books).
- 4 book home pages + 2 lang-root pages: rewrite ~50 internal URLs
  from /<book>/<module>/home to /<book>/<module>/index.
- README.md, CLAUDE.md: correct landing-page references.
- en/platform/clusters/permissions.md + th counterpart: stray
  home.md ref → index.md.

Out of scope: historical references inside docs/superpowers/plans/ and
docs/superpowers/specs/ are preserved as snapshots of past work.

Wiki.js admin "Default Path" setting must be updated to /en/index manually
after deploy — see Task 9 below.

See docs/superpowers/specs/2026-05-19-folder-default-pages-design.md.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

- [ ] **Step 6: Verify commit and clean tree**

Run: `git status && git log --oneline -3`

Expected: working tree clean, top commit shows the message above.

---

### Task 9: Wiki.js admin manual verification

**Files:** none in repo. This is a manual step outside the codebase.

This task is informational. It does not produce a commit. The plan executor must surface this to the operator after Task 8's commit is pushed to the dev environment.

- [ ] **Step 1: Push the U0 commit to the dev wiki** (per the repo's existing deploy mechanism, which is outside the scope of this plan — most likely a `git push` to a branch that the dev wiki polls or a manual sync trigger).

- [ ] **Step 2: Open `http://dev.blueledgers.com:3987/` in a browser**

Expected: either the Carmen Wiki two-card landing renders (if Wiki.js auto-detects `index`), or it 404s / shows a "page not found" prompt (if Wiki.js was hardcoded to redirect `/` to `/en/home`).

- [ ] **Step 3: If `/` shows a 404, open Wiki.js admin**

Navigate to Administration → Site → Default Path. The current value is likely `/en/home`. Change it to `/en/index`. Save.

- [ ] **Step 4: Re-test `/`**

Reload `http://dev.blueledgers.com:3987/` — the two-card landing should render.

- [ ] **Step 5: Spot-check renamed module URLs**

Open each in a fresh tab:
- `http://dev.blueledgers.com:3987/en/inventory/index` — Inventory book home renders with all module links
- Click one Inventory module link — opens the module index without 404
- `http://dev.blueledgers.com:3987/en/platform/clusters/index` — opens the (still-stub) Clusters landing
- `http://dev.blueledgers.com:3987/th/index` — opens the Thai two-card landing

- [ ] **Step 6: Document the admin change**

If the Default Path setting was changed, note this in a follow-up commit message or the deployment log — the next time the dev wiki is restored from backup, this admin setting may need to be re-applied. (Out of scope for this plan to automate.)

---

## Units 1–6 — Platform Module Content Upgrades

Each unit is one commit. Each commit edits exactly two files: `en/platform/<module>/index.md` and `th/platform/<module>/index.md`.

The 7-section canonical template comes from `en/inventory/costing/index.md` (the reference module). Read it once before starting U1 so the shape is familiar.

### Canonical `index.md` template (reference)

```markdown
---
title: <Module name>
description: <one-line summary used by Wiki.js search and previews>
published: true
date: 2026-05-19T00:00:00.000Z
tags: platform/<module-slug>, carmen-software
editor: markdown
dateCreated: <preserve original from stub if present, else 2026-05-19T00:00:00.000Z>
---

# <Module name>

> **At a Glance**
> **Module purpose:** <one sentence> &nbsp;·&nbsp; **Audience:** <role(s)> &nbsp;·&nbsp; **Key entities/tables:** <comma list> &nbsp;·&nbsp; **Sub-pages:** N

## 1. Overview
(2–3 paragraphs)

## 2. Business Context
(1–2 paragraphs, terse OK)

## 3. Key Concepts
- **<Term>**: <one-sentence definition>
- … (4–8 items)

## 4. Roles and Personas
| Role | Responsibility |
|------|----------------|
| ... | ... |

(or one line of prose if single role)

## 5. Related Modules
- [[<other-module>]] — <relationship>
- ...

## 6. Reference Sources
- Concepts: <path or "n/a">
- Frontend: `../carmen-platform/SITEMAP.md`, `../carmen-platform/src/pages/<Page>.tsx`
- Backend / API / E2E: <paths if applicable, omit lines that don't apply>

## 7. Pages in This Module
- [<Sub-page name>](./<slug>.md) — <one-line description>
- ... (or "This module is a single page; see the parent [Platform book index](../index.md)." for single-file modules)
```

### Per-unit task structure

Each Unit `N` (N = 1..6) follows the same 5-step shape. The placeholders `<module>`, `<sub-pages>` etc. are filled in per the table below.

| Unit | Module | Sub-page count | EN title | Notes |
|------|--------|----------------|----------|-------|
| U1 | profile | 0 | "Profile" | Section 2 terse (no business angle), Section 4 collapses to one prose line, Section 7 explicit single-page text |
| U2 | auth-roles | 0 | "Authentication & Roles" | Section 2 mentions access/security model briefly |
| U3 | report-templates | 2 | "Report Templates" | Full template |
| U4 | business-units | 2 | "Business Units" | Full template |
| U5 | clusters | 3 | "Clusters" | Full template — richest data model among Platform modules |
| U6 | users | 3 | "Users" | Full template |

### Task N.1: Read source material for `<module>`

**Files:** none (read-only)

- [ ] **Step 1: Read `../carmen-platform/SITEMAP.md`**

Run: `cat ../carmen-platform/SITEMAP.md`

Extract the section describing `<module>` — typically a URL, a one-line description, and links to React page files.

- [ ] **Step 2: Read the React page files referenced for this module**

For each `src/pages/<Page>.tsx` mentioned (e.g. for `clusters`: `ClusterManagement.tsx`, `ClusterEdit.tsx`), read the file to extract:
- The visible UI controls and screens (informs Section 1 Overview, Section 7 sub-page descriptions)
- Form fields and state shape (informs Section 3 Key Concepts and any data-model bullets)
- Role/permission gates (informs Section 4 Roles)
- API calls or service references (informs Section 6 Reference Sources)

Use Read tool with absolute path: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-platform/src/pages/<Page>.tsx`

- [ ] **Step 3: Read the existing stub at `en/platform/<module>/index.md`**

The stub contains an "At a Glance" bullet list, a "References" section, and a "TODO" checklist. Reuse the references and the spirit of the bullets; the TODO checklist disappears in the upgraded page.

- [ ] **Step 4: Read existing sub-pages in `en/platform/<module>/`** (if any)

For modules with sub-pages (report-templates, business-units, clusters, users), read each sub-page to derive the Section 7 one-line description.

Run: `ls en/platform/<module>/`

Then `Read` each non-`index.md` `.md` file there.

- [ ] **Step 5: No commit**

Proceed to Task N.2.

### Task N.2: Write the EN `index.md`

**Files:**
- Modify: `en/platform/<module>/index.md` (overwrite the stub)

- [ ] **Step 1: Replace the file with the canonical template, fully filled in**

Use the Write tool to overwrite `en/platform/<module>/index.md` with content following the canonical template above, with all sections filled from the source material gathered in Task N.1.

Specifics per module:

**For `profile` (U1):**
- Section 2: one short sentence — the profile module shows the signed-in user their own information; no external business driver.
- Section 4: one prose line — "Used by the signed-in user themselves. No admin role applies."
- Section 7: "This module is a single page; see the parent [Platform book index](../index.md)."

**For `auth-roles` (U2):**
- Section 2: brief mention of the platform's RBAC model and where roles bind users to capabilities.
- Section 4: list the role personas (typically "Cluster Admin" or "Security Admin") that interact with role assignment.
- Section 7: same single-page text as U1.

**For `report-templates`, `business-units`, `clusters`, `users` (U3–U6):**
- Full template. Section 7 lists the 2–3 sub-pages with one-line descriptions each. Cross-link to other Platform modules in Section 5 (e.g. clusters → business-units, business-units → clusters, users → auth-roles, users → business-units).

- [ ] **Step 2: Render-check by reading back**

Open the file (in the editor or via Read tool) and read it top-to-bottom. Confirm:
- Frontmatter is valid YAML, `published: true`, `date` updated to today (2026-05-19 or later), `dateCreated` preserved or set to today if missing
- All 7 sections present with numbered prefix `## 1.` through `## 7.`
- No `TODO`, `TBD`, or stub markers remain
- The "At a Glance" blockquote uses the `&nbsp;·&nbsp;` separator pattern, not raw `·` (matches Inventory style)
- Internal `[[wiki-style]]` links use bare module names (e.g. `[[business-units]]`), not paths

- [ ] **Step 3: No commit yet — TH translation in next task**

Proceed to Task N.3.

### Task N.3: Write the TH `index.md` (translation)

**Files:**
- Modify: `th/platform/<module>/index.md` (overwrite the English stub)

- [ ] **Step 1: Translate the EN `index.md` to Thai**

Use the Write tool to overwrite `th/platform/<module>/index.md`. Translate:
- The `title:` frontmatter field to Thai (consult existing translated Inventory titles for style — e.g. `en/inventory/costing/index.md` has `title: Costing`, `th/inventory/costing/index.md` has `title: การคำนวณต้นทุน (Costing)` keeping the English in parentheses for searchability).
- `description:` frontmatter field to Thai.
- All section headings (`## 1. Overview` → `## 1. ภาพรวม`, etc.) — use the same Thai phrasing that appears in `th/inventory/<any-module>/index.md` for the same section number so navigation labels stay consistent.
- All body prose to Thai.
- Code blocks, paths, file names, and `[[wiki-style]]` link slugs: do NOT translate (they are technical identifiers).
- The `tags:` field stays the same (it's machine-readable, not user-facing).
- `dateCreated` preserved from the original stub if present, else set to today.
- `date` set to today.

- [ ] **Step 2: Verify Thai-section-heading parity with Inventory TH**

Section numbering and heading phrasing must match the Inventory TH pattern so `sync_nav.py` cross-referencing works consistently. Run:

```bash
grep -h "^## " th/inventory/costing/index.md | head -10
```

The Thai headings of sections 1–7 in your new file should phrase the same concepts the same way as Inventory TH does for those positions. Re-translate if any drift.

- [ ] **Step 3: No TODO/stub markers remain**

Run: `grep -nE "TODO|TBD|^- \[ \]" th/platform/<module>/index.md`

Expected: zero output.

### Task N.4: Manual render check in dev wiki

**Files:** none (manual browser step)

- [ ] **Step 1: Push the working changes (or wait for poll) to dev wiki**

(Same deploy mechanism as Task 9.)

- [ ] **Step 2: Open `http://dev.blueledgers.com:3987/en/platform/<module>/index`**

Confirm:
- Page renders without 404
- Title and "At a Glance" appear in the page header area
- All 7 sections render with proper numbering
- Sidebar still shows the module at the expected position under the Platform book
- Internal `[[wiki-style]]` links highlight properly (Wiki.js link resolution)

- [ ] **Step 3: Switch language to TH**

Use Wiki.js's language switcher. Expected: `/th/platform/<module>/index` loads, all prose is Thai, no leftover English in body text (the title may include `(English Name)` in parentheses by design — that is acceptable).

- [ ] **Step 4: Spot-check sub-page navigation** (modules U3–U6 only)

Click each sub-page link in Section 7. Each should open the existing sub-page without 404. (Sub-page content is unchanged by this plan.)

### Task N.5: Commit Unit N

**Files:** the two `index.md` files for this module.

- [ ] **Step 1: Stage and commit**

```bash
git add en/platform/<module>/index.md th/platform/<module>/index.md
git commit -m "$(cat <<'EOF'
docs(platform/<module>): upgrade landing from stub to canonical template

Replace the skeleton home (now index.md) for the <module name> module
with the 7-section landing-page template used by Inventory modules.
EN + TH parity in this commit. TH was previously English placeholder
text under TH frontmatter; rewritten as a true Thai translation.

Sources read: ../carmen-platform/SITEMAP.md and the relevant
src/pages/<Page>.tsx files. Section 7 (Pages in This Module) reflects
the N existing sub-pages in this module folder.

See docs/superpowers/specs/2026-05-19-folder-default-pages-design.md.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

(Substitute `<module>` and `<module name>` with the actual values for the unit being committed.)

- [ ] **Step 2: Verify clean tree and continue to next unit**

Run: `git status`

Expected: working tree clean. Then begin Task (N+1).1 for the next module in the sequence (profile → auth-roles → report-templates → business-units → clusters → users).

---

## Final State Verification (after Units 1–6 complete)

- [ ] **Step 1: No stub markers anywhere in Platform**

Run:
```bash
grep -rnE "TODO|TBD|^- \[ \]" en/platform/ th/platform/ 2>/dev/null
```

Expected: zero output.

- [ ] **Step 2: All 6 Platform module landings have 7 numbered sections**

Run:
```bash
for m in auth-roles business-units clusters profile report-templates users; do
  count=$(grep -c "^## [0-9]\+\." "en/platform/$m/index.md")
  printf "%-25s %d sections\n" "$m" "$count"
done
```

Expected: each line shows 7 sections.

- [ ] **Step 3: Render-check the Platform book home in dev wiki**

Open `http://dev.blueledgers.com:3987/en/platform/index`. All 6 module links resolve to upgraded landings (no stubs). Repeat for `/th/platform/index`.

---

## Self-Review Checklist (for the plan author)

1. **Spec coverage:** Every section of the spec maps to at least one task — the 18 renames (Task 5), script updates (Tasks 2 & 3), YAML (Task 4), URL updates (Task 6), text refs (Task 7), atomic commit (Task 8), Wiki.js admin (Task 9), Platform content upgrades (Units 1–6).
2. **Placeholders:** Searched for "TBD" / "implement later" / "similar to" — none in this plan; per-module specifics are inlined per-unit.
3. **Type/name consistency:** `parse_home_headings` → `parse_index_headings` and `HOME_MD` → `INDEX_MD` used consistently across Tasks 2, 3, 8. `home_slug: index` value used in Task 4 and matches Task 2's test fixture changes.
4. **No imagined APIs:** Every script API referenced (`parse_index_headings`, `LabelSource.INDEX_MD`, `_run_build_mode`) exists in the actual `scripts/sync_nav.py` post-Task-3 edits.
