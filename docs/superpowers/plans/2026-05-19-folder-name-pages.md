# Folder-Name Default Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Switch the wiki from `<folder>/index.md` to sibling `<folder>.md` so Wiki.js URLs resolve as `/en`, `/en/inventory`, `/en/inventory/costing` (no `/index` suffix), and update the navigation script, tests, and docs to match.

**Architecture:** All landing files are moved up one level via `git mv` to become siblings of their folder. The sidebar-building script (`scripts/sync_nav.py`) drops the `home_slug` URL segment so book/module sidebar links emit clean folder URLs. Internal links in landing files lose their `/index` suffix; internal back-links in sub-pages convert from relative `[index.md](./index.md)` to absolute `/<locale>/<book>/<module>`.

**Tech Stack:** Markdown content (Wiki.js Git storage), Python 3 (`scripts/sync_nav.py`, pytest), YAML config (`scripts/nav-overrides.yaml`).

**Branch:** `feat/folder-name-pages` (already created and contains the spec commit).

**Commit strategy:** One small commit per task on the feature branch. Squash on PR merge so `main` sees a single atomic structural change — Wiki.js pulls from `main` and would be confused by intermediate states.

**Spec:** `docs/superpowers/specs/2026-05-19-folder-name-pages-design.md`

---

## File Structure

Files **created** in this plan (54 landings, all via `git mv`):

| New path | From |
|---|---|
| `en.md` | `en/index.md` |
| `th.md` | `th/index.md` |
| `en/inventory.md` | `en/inventory/index.md` |
| `en/platform.md` | `en/platform/index.md` |
| `th/inventory.md` | `th/inventory/index.md` |
| `th/platform.md` | `th/platform/index.md` |
| `{en,th}/inventory/<module>.md` × 18 modules × 2 locales = 36 files | `{en,th}/inventory/<module>/index.md` |
| `{en,th}/platform/<module>.md` × 6 modules × 2 locales = 12 files | `{en,th}/platform/<module>/index.md` |

Files **modified** (no new files):

- `scripts/sync_nav.py` — drop `home_slug` URL segment, update locale-root path references
- `scripts/test_sync_nav.py` — update fixtures and expectations to match new paths/URLs
- `scripts/nav-overrides.yaml` — remove `home_slug: index` from both books
- `README.md` — convention docs
- `CLAUDE.md` — convention docs
- 14 sub-page files with relative `[...](./index.md)` or `[...](../index.md)` back-links → absolute `/<locale>/<book>/<module>`

Files **untouched** in this plan (explicit out-of-scope):

- All non-`index.md` content files (`01-data-model.md`, `02-business-rules.md`, role-specific user-flow files, etc.)
- `docs/superpowers/plans/*.md` and `docs/superpowers/specs/*.md` (historical)
- `scripts/migrate_books/verify.py` (one-shot migration helper)

---

## Task 1: Update sync_nav tests to expect new paths and URLs (failing)

Make the tests reflect the target convention. They will fail against current production code; Task 2 fixes that.

**Files:**
- Modify: `scripts/test_sync_nav.py`

- [ ] **Step 1.1: Update locale-root path fixtures (lines 401–409)**

Open `scripts/test_sync_nav.py`. Find the block that writes `tmp_path / "en" / "index.md"` and `tmp_path / "th" / "index.md"` (around line 401–409 inside `test_build_label_map_real_files` or similar). Replace those paths with `tmp_path / "en.md"` and `tmp_path / "th.md"`.

Before:
```python
(tmp_path / "th" / "index.md").write_text(
    "...",
    ...
)
(tmp_path / "en" / "index.md").write_text(
    "...",
    ...
)
```

After:
```python
(tmp_path / "th.md").write_text(
    "...",
    ...
)
(tmp_path / "en.md").write_text(
    "...",
    ...
)
```

- [ ] **Step 1.2: Remove `home_slug` from all `build_tree_from_config` fixtures**

Search the file for `"home_slug": "index"` (appears at approximately lines 439, 471, 485, 514, 542, 569, 615, 635 — eight occurrences). Delete each line entirely (including the trailing comma cleanup on the preceding line if applicable).

Example (one occurrence, line 439 area):
```python
"books": {
    "inventory": {
        "label_en": "Carmen Inventory",
        "label_th": "Carmen Inventory",
        "home_slug": "index",      # ← delete this line
        "groups": [ ... ],
    },
},
```

After deletion:
```python
"books": {
    "inventory": {
        "label_en": "Carmen Inventory",
        "label_th": "Carmen Inventory",
        "groups": [ ... ],
    },
},
```

- [ ] **Step 1.3: Update expected URL assertions (drop `/index` suffix)**

In the same file, update every assertion that expects a URL ending in `/index`:

| Line (approx) | Before | After |
|---|---|---|
| 457 | `assert items_en[1]["target"] == "/en/inventory/index"` | `assert items_en[1]["target"] == "/en/inventory"` |
| 460 | `assert items_en[3]["target"] == "/en/inventory/costing/index"` | `assert items_en[3]["target"] == "/en/inventory/costing"` |
| 529 | `assert items_th[1]["target"] == "/th/inventory/index"` | `assert items_th[1]["target"] == "/th/inventory"` |
| 531 | `assert items_th[3]["target"] == "/th/inventory/costing/index"` | `assert items_th[3]["target"] == "/th/inventory/costing"` |
| 624 | `assert items[1]["target"] == "/en/inventory/index"` | `assert items[1]["target"] == "/en/inventory"` |

Use a grep to confirm no more `/index"` URL assertions remain (the heading-parser tests do not assert URLs and are unaffected):
```bash
grep -nE "\"/(en|th)/[^\"]+/index\"" scripts/test_sync_nav.py
```
Expected after edits: no output.

- [ ] **Step 1.4: Run tests, confirm they fail in the expected places**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: tests covering `build_tree_from_config` fail (assertion mismatch — production code still emits `/index` suffix; production also still uses old paths). Heading-parser tests (`test_parse_index_headings_*`) continue to pass — they're generic.

If anything *unexpected* fails (e.g. import error, syntax error), fix it now before moving on.

- [ ] **Step 1.5: Commit**

```bash
git add scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
test(sync_nav): expect sibling .md convention (failing)

Drop /index URL suffix in assertions, remove home_slug from fixtures,
move locale-root fixtures from <locale>/index.md to <locale>.md.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 2: Update sync_nav.py and nav-overrides.yaml to make tests pass

Production-code changes that match the test expectations from Task 1.

**Files:**
- Modify: `scripts/sync_nav.py`
- Modify: `scripts/nav-overrides.yaml`

- [ ] **Step 2.1: Drop `home_slug` segment from `build_tree_from_config` URL builder**

Open `scripts/sync_nav.py`. Find `build_tree_from_config` (around line 645). Edit the URL construction:

Before:
```python
home_slug = book.get("home_slug", "index")
items.append(
    _new_link(
        "Home",
        f"/{locale}/{book_slug}/{home_slug}",
    )
)
for group in book.get("groups") or []:
    items.append(_new_header(group[label_key]))
    for module in group.get("modules") or []:
        items.append(
            _new_link(
                module[label_key],
                f"/{locale}/{book_slug}/{module['slug']}/{home_slug}",
            )
        )
```

After:
```python
items.append(
    _new_link(
        "Home",
        f"/{locale}/{book_slug}",
    )
)
for group in book.get("groups") or []:
    items.append(_new_header(group[label_key]))
    for module in group.get("modules") or []:
        items.append(
            _new_link(
                module[label_key],
                f"/{locale}/{book_slug}/{module['slug']}",
            )
        )
```

- [ ] **Step 2.2: Update locale-root path references in `parse_index_headings` callers**

Find every call to `parse_index_headings(repo_root / "en" / "index.md")` and `parse_index_headings(repo_root / "th" / "index.md")` (approximately lines 397, 398, 467, 468).

Before:
```python
en_index = parse_index_headings(repo_root / "en" / "index.md")
th_index = parse_index_headings(repo_root / "th" / "index.md")
```

After:
```python
en_index = parse_index_headings(repo_root / "en.md")
th_index = parse_index_headings(repo_root / "th.md")
```

Apply the same change to the second pair around lines 467–468.

- [ ] **Step 2.3: Leave the `LabelSource.INDEX_MD` enum value and summary string alone**

No edit. The string `"index.md"` on line 102 (`INDEX_MD = "index.md"`) and the matching key in `format_summary` (line 377) are the **semantic** name of a label source — "this TH label was sourced from the EN heading parser." They are not filenames. Renaming them is out of scope; leaving them keeps the diff smaller and the test assertions in `test_sync_nav.py` (`counts["index.md"]`, `"6 index.md"` in summary string) continue to pass without modification.

If a future cleanup wants to rename to e.g. `LANDING_HEADING` for clarity, that's a separate change.

- [ ] **Step 2.4: Leave the `resolve_th_page_title` fallback alone**

Verify (no edit) — lines 84–88 should still read:
```python
for candidate in (
    repo_root / f"{rel}.md",
    repo_root / rel / "index.md",
):
```
Per spec decision, this defensive fallback stays.

- [ ] **Step 2.5: Update `scripts/nav-overrides.yaml` — remove `home_slug`**

Open `scripts/nav-overrides.yaml`. Delete the `home_slug: index` line under both `inventory:` and `platform:` (lines 13 and 91).

Before:
```yaml
books:
  inventory:
    label_en: "Carmen Inventory"
    label_th: "Carmen Inventory"
    home_slug: index
    groups:
      ...
  platform:
    label_en: "Carmen Platform"
    label_th: "Carmen Platform"
    home_slug: index
    groups:
      ...
```

After:
```yaml
books:
  inventory:
    label_en: "Carmen Inventory"
    label_th: "Carmen Inventory"
    groups:
      ...
  platform:
    label_en: "Carmen Platform"
    label_th: "Carmen Platform"
    groups:
      ...
```

- [ ] **Step 2.6: Run tests, confirm they pass**

```bash
pytest scripts/test_sync_nav.py -v
```

Expected: all tests pass. If any tests still fail, inspect the failure, fix the production code (not the test), and re-run.

- [ ] **Step 2.7: Run the script in build mode to confirm no runtime errors**

```bash
python scripts/sync_nav.py --mode=build --dry-run 2>&1 | head -40
```

Expected: script completes without exception. The locale-root path reads (`en.md`, `th.md`) will fail because the files don't exist yet — that's expected at this point. The error message should be a clear FileNotFoundError mentioning `en.md`, not a logic bug.

If `--dry-run` isn't a flag the script supports, check `python scripts/sync_nav.py --help` and use whatever no-op mode is available, or just confirm it raises on file-not-found rather than crashing earlier.

- [ ] **Step 2.8: Commit**

```bash
git add scripts/sync_nav.py scripts/nav-overrides.yaml scripts/test_sync_nav.py
git commit -m "$(cat <<'EOF'
scripts(sync_nav): emit clean folder URLs, drop home_slug

URL builder emits /{locale}/{book} and /{locale}/{book}/{module} without
the index suffix. nav-overrides.yaml drops home_slug for both books.
Locale-root heading parser now reads <locale>.md at repo root.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 3: Rename locale roots and update their URLs

**Files:**
- Move: `en/index.md` → `en.md`
- Move: `th/index.md` → `th.md`
- Modify: `en.md` (after move) — drop `/index` from book links
- Modify: `th.md` (after move) — drop `/index` from book links

- [ ] **Step 3.1: Rename the locale-root files**

```bash
git mv en/index.md en.md
git mv th/index.md th.md
```

Confirm:
```bash
ls -1 en.md th.md
test ! -e en/index.md && test ! -e th/index.md && echo "originals removed"
```

- [ ] **Step 3.2: Update URLs inside `en.md`**

The file has two links pointing to book landings. Open `en.md` and replace:

Before:
```markdown
[Open the Inventory book →](/en/inventory/index)
...
[Open the Platform book →](/en/platform/index)
```

After:
```markdown
[Open the Inventory book →](/en/inventory)
...
[Open the Platform book →](/en/platform)
```

- [ ] **Step 3.3: Update URLs inside `th.md`**

Same change in `th.md`:

Before:
```markdown
[เปิด Inventory book →](/th/inventory/index)
...
[เปิด Platform book →](/th/platform/index)
```

After:
```markdown
[เปิด Inventory book →](/th/inventory)
...
[เปิด Platform book →](/th/platform)
```

- [ ] **Step 3.4: Verify**

```bash
grep -nE "/(en|th)/(inventory|platform)/index" en.md th.md
```
Expected: no output.

- [ ] **Step 3.5: Commit**

```bash
git add en.md th.md
git commit -m "$(cat <<'EOF'
docs(structure): move locale roots to en.md, th.md

Wiki.js URL for the locale landing now resolves at /en and /th
(no /index suffix). Internal book links updated to match.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 4: Rename book landings and update their URLs

**Files:**
- Move: `en/inventory/index.md` → `en/inventory.md`
- Move: `en/platform/index.md` → `en/platform.md`
- Move: `th/inventory/index.md` → `th/inventory.md`
- Move: `th/platform/index.md` → `th/platform.md`
- Modify each of the four moved files: drop `/index` from module links

- [ ] **Step 4.1: Rename the four book-landing files**

```bash
git mv en/inventory/index.md en/inventory.md
git mv en/platform/index.md en/platform.md
git mv th/inventory/index.md th/inventory.md
git mv th/platform/index.md th/platform.md
```

Confirm:
```bash
ls -1 en/inventory.md en/platform.md th/inventory.md th/platform.md
test ! -e en/inventory/index.md && test ! -e en/platform/index.md \
  && test ! -e th/inventory/index.md && test ! -e th/platform/index.md \
  && echo "originals removed"
```

- [ ] **Step 4.2: Update URLs inside `en/inventory.md`**

The file has 18 links — one per Inventory module — each ending in `/index`. Replace all of them with a single `sed`-style or editor pass:

Pattern to replace (Markdown link to module landing):
```
](/en/inventory/<module>/index)
```
Replacement:
```
](/en/inventory/<module>)
```

Apply to all 18 modules: `access-control`, `costing`, `dashboard`, `good-receive-note`, `inventory`, `inventory-adjustment`, `master-data`, `physical-count`, `product`, `purchase-order`, `purchase-request`, `recipe`, `reporting-audit`, `spot-check`, `store-requisition`, `system-config`, `templates`, `vendor-pricelist`.

The simplest implementation is a single regex-replace across the file using your editor's "Replace in file" with regex `/en/inventory/([a-z-]+)/index\b` → `/en/inventory/$1`.

- [ ] **Step 4.3: Update URLs inside `en/platform.md`**

Six modules: `auth-roles`, `business-units`, `clusters`, `profile`, `report-templates`, `users`. Same regex pattern, with `platform` instead of `inventory`:

Replace `/en/platform/([a-z-]+)/index\b` → `/en/platform/$1`.

- [ ] **Step 4.4: Update URLs inside `th/inventory.md`**

Same as 4.2 but with the `/th/` prefix. Regex: `/th/inventory/([a-z-]+)/index\b` → `/th/inventory/$1`.

- [ ] **Step 4.5: Update URLs inside `th/platform.md`**

Same as 4.3 but with `/th/`. Regex: `/th/platform/([a-z-]+)/index\b` → `/th/platform/$1`.

- [ ] **Step 4.6: Verify**

```bash
grep -nE "/(en|th)/(inventory|platform)/[a-z-]+/index" en/inventory.md en/platform.md th/inventory.md th/platform.md
```
Expected: no output.

- [ ] **Step 4.7: Commit**

```bash
git add en/inventory.md en/platform.md th/inventory.md th/platform.md
git commit -m "$(cat <<'EOF'
docs(structure): move book landings to <book>.md siblings

Inventory and Platform book landings now sit beside their folder rather
than inside it. Module links in each landing drop the /index suffix.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 5: Rename Inventory module landings (36 files)

Mechanical bulk rename. No URL updates inside these files — module landings don't currently link to other modules with `/index` suffix (verified during plan-writing).

**Files (36):**
- Move: `en/inventory/<module>/index.md` → `en/inventory/<module>.md` × 18 modules
- Move: `th/inventory/<module>/index.md` → `th/inventory/<module>.md` × 18 modules

- [ ] **Step 5.1: Run the rename in a loop (EN)**

```bash
for m in access-control costing dashboard good-receive-note inventory \
         inventory-adjustment master-data physical-count product \
         purchase-order purchase-request recipe reporting-audit \
         spot-check store-requisition system-config templates \
         vendor-pricelist; do
  git mv "en/inventory/$m/index.md" "en/inventory/$m.md"
done
```

- [ ] **Step 5.2: Run the rename in a loop (TH)**

```bash
for m in access-control costing dashboard good-receive-note inventory \
         inventory-adjustment master-data physical-count product \
         purchase-order purchase-request recipe reporting-audit \
         spot-check store-requisition system-config templates \
         vendor-pricelist; do
  git mv "th/inventory/$m/index.md" "th/inventory/$m.md"
done
```

- [ ] **Step 5.3: Verify**

```bash
find en/inventory th/inventory -name "index.md" -type f
```
Expected: no output.

```bash
find en/inventory th/inventory -maxdepth 2 -name "*.md" -type f | sort | head -20
```
Expected: 36 module landings (`en/inventory/access-control.md`, `en/inventory/costing.md`, …, `th/inventory/...`).

- [ ] **Step 5.4: Spot-check that one module landing is intact**

```bash
head -20 en/inventory/costing.md
```
Expected: frontmatter starts with `title: Costing`, then `# Costing` heading, then "At a Glance" block. Unchanged content.

- [ ] **Step 5.5: Commit**

```bash
git add -A en/inventory th/inventory
git commit -m "$(cat <<'EOF'
docs(structure): move inventory module landings to sibling .md (36 files)

Each en/inventory/<module>/index.md and th/inventory/<module>/index.md
moves to <module>.md beside its folder. Sub-pages inside each module
folder are unchanged.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 6: Rename Platform module landings and update single-page back-links

**Files (12 renames + 4 back-link edits):**
- Move: `{en,th}/platform/<module>/index.md` → `{en,th}/platform/<module>.md` × 6 modules × 2 locales
- Modify: `en/platform/auth-roles.md` (after move) — update `../index.md` back-link
- Modify: `en/platform/profile.md` (after move) — update `../index.md` back-link
- Modify: `th/platform/auth-roles.md` (after move) — update `../index.md` back-link
- Modify: `th/platform/profile.md` (after move) — update `../index.md` back-link

- [ ] **Step 6.1: Rename the EN Platform module landings**

```bash
for m in auth-roles business-units clusters profile report-templates users; do
  git mv "en/platform/$m/index.md" "en/platform/$m.md"
done
```

- [ ] **Step 6.2: Rename the TH Platform module landings**

```bash
for m in auth-roles business-units clusters profile report-templates users; do
  git mv "th/platform/$m/index.md" "th/platform/$m.md"
done
```

- [ ] **Step 6.3: Update back-link in `en/platform/auth-roles.md`**

Find the line containing `[Platform book index](../index.md)`.

Before:
```markdown
This module is a single page; see the parent [Platform book index](../index.md).
```

After:
```markdown
This module is a single page; see the parent [Platform book index](/en/platform).
```

- [ ] **Step 6.4: Update back-link in `en/platform/profile.md`**

Same edit as 6.3:

Before:
```markdown
This module is a single page; see the parent [Platform book index](../index.md).
```

After:
```markdown
This module is a single page; see the parent [Platform book index](/en/platform).
```

- [ ] **Step 6.5: Update back-link in `th/platform/auth-roles.md`**

Before:
```markdown
โมดูลนี้เป็นหน้าเดี่ยว ดู [สารบัญหนังสือ Platform](../index.md)
```

After:
```markdown
โมดูลนี้เป็นหน้าเดี่ยว ดู [สารบัญหนังสือ Platform](/th/platform)
```

- [ ] **Step 6.6: Update back-link in `th/platform/profile.md`**

Same edit as 6.5:

Before:
```markdown
โมดูลนี้เป็นหน้าเดี่ยว ดู [สารบัญหนังสือ Platform](../index.md)
```

After:
```markdown
โมดูลนี้เป็นหน้าเดี่ยว ดู [สารบัญหนังสือ Platform](/th/platform)
```

- [ ] **Step 6.7: Verify**

```bash
find en/platform th/platform -name "index.md" -type f
```
Expected: no output.

```bash
grep -rnE "\(\.\./index\.md\)" en/platform th/platform
```
Expected: no output.

- [ ] **Step 6.8: Commit**

```bash
git add -A en/platform th/platform
git commit -m "$(cat <<'EOF'
docs(structure): move platform module landings to sibling .md (12 files)

Six Platform modules per locale move to <module>.md beside the folder.
Single-page modules (auth-roles, profile) get their parent-book back-link
rewritten to /<locale>/platform.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 7: Rewrite relative back-links in PR / PO / vendor-pricelist sub-pages

Twenty-four `[index.md](./index.md)` references across fourteen files. Convert to absolute `/<locale>/<book>/<module>` and change the link text so the sentence reads naturally.

**Files (14):**
- `en/inventory/purchase-order/03-user-flow.md`
- `en/inventory/purchase-order/03-user-flow-audit-config.md`
- `en/inventory/purchase-request/03-user-flow.md`
- `en/inventory/purchase-request/03-user-flow-approver.md`
- `en/inventory/purchase-request/03-user-flow-audit-config.md`
- `en/inventory/purchase-request/03-user-flow-procurement-manager.md`
- `en/inventory/purchase-request/03-user-flow-purchaser.md`
- `en/inventory/purchase-request/03-user-flow-requestor.md` (×2)
- `en/inventory/vendor-pricelist/03-user-flow.md` (×2)
- `en/inventory/vendor-pricelist/03-user-flow-purchaser.md`
- TH counterparts of all of the above

- [ ] **Step 7.1: List every file and exact line that needs editing**

```bash
grep -rnE "\]\(\./index\.md\)" en/inventory/purchase-order en/inventory/purchase-request en/inventory/vendor-pricelist th/inventory/purchase-order th/inventory/purchase-request th/inventory/vendor-pricelist
```

Expected: 24 lines, one match per `(./index.md)` occurrence. Save the output for reference.

- [ ] **Step 7.2: Update each EN sub-page**

For each EN file, the surrounding sentence contains `[index.md](./index.md)` and usually a `Section 4` reference. Replace `[index.md](./index.md)` with `[the module landing](/en/inventory/<module>)`, where `<module>` is the parent folder of the file. Concrete edits:

**`en/inventory/purchase-order/03-user-flow.md`** — replace:
```
defined in [index.md](./index.md) Section 4
```
with:
```
defined in [the module landing](/en/inventory/purchase-order) Section 4
```

**`en/inventory/purchase-order/03-user-flow-audit-config.md`** — replace:
```
Sibling: [index.md](./index.md) Section 4 — canonical Auditor and System Administrator role descriptions
```
with:
```
Sibling: [the module landing](/en/inventory/purchase-order) Section 4 — canonical Auditor and System Administrator role descriptions
```

**`en/inventory/purchase-request/03-user-flow.md`** — replace:
```
defined in [index.md](./index.md) Section 4
```
with:
```
defined in [the module landing](/en/inventory/purchase-request) Section 4
```

**`en/inventory/purchase-request/03-user-flow-approver.md`**:
```
Sibling: [index.md](./index.md) Section 4 — canonical Approver role description and stage chain
```
→
```
Sibling: [the module landing](/en/inventory/purchase-request) Section 4 — canonical Approver role description and stage chain
```

**`en/inventory/purchase-request/03-user-flow-audit-config.md`**:
```
Sibling: [index.md](./index.md) Section 4 — canonical Auditor and System Administrator role descriptions
```
→
```
Sibling: [the module landing](/en/inventory/purchase-request) Section 4 — canonical Auditor and System Administrator role descriptions
```

**`en/inventory/purchase-request/03-user-flow-procurement-manager.md`**:
```
Sibling: [index.md](./index.md) Section 4 — canonical Procurement Manager role description
```
→
```
Sibling: [the module landing](/en/inventory/purchase-request) Section 4 — canonical Procurement Manager role description
```

**`en/inventory/purchase-request/03-user-flow-purchaser.md`**:
```
Sibling: [index.md](./index.md) Section 4 — canonical Purchaser role description
```
→
```
Sibling: [the module landing](/en/inventory/purchase-request) Section 4 — canonical Purchaser role description
```

**`en/inventory/purchase-request/03-user-flow-requestor.md`** has **two** occurrences:

1. `(see [index.md](./index.md) Section 4)` → `(see [the module landing](/en/inventory/purchase-request) Section 4)`
2. `Sibling: [index.md](./index.md) Section 4 — canonical Requestor role description` → `Sibling: [the module landing](/en/inventory/purchase-request) Section 4 — canonical Requestor role description`

**`en/inventory/vendor-pricelist/03-user-flow.md`** has **two** occurrences:

1. `role catalogue itself is defined in [index.md](./index.md) Section 4` → `role catalogue itself is defined in [the module landing](/en/inventory/vendor-pricelist) Section 4`
2. `Receiver / Store Keeper is listed as an "indirect consumer" in [index.md](./index.md) Section 4` → `Receiver / Store Keeper is listed as an "indirect consumer" in [the module landing](/en/inventory/vendor-pricelist) Section 4`

**`en/inventory/vendor-pricelist/03-user-flow-purchaser.md`**:
```
two organisational roles documented in [index.md](./index.md) Section 4
```
→
```
two organisational roles documented in [the module landing](/en/inventory/vendor-pricelist) Section 4
```

- [ ] **Step 7.3: Update each TH sub-page (mirror of 7.2)**

Same files in `th/inventory/...`. The Thai link-text equivalent is `[หน้าหลักโมดูล]` and the URL prefix is `/th/`. Concrete edits:

**`th/inventory/purchase-order/03-user-flow.md`**:
```
นิยามใน [index.md](./index.md) Section 4
```
→
```
นิยามใน [หน้าหลักโมดูล](/th/inventory/purchase-order) Section 4
```

**`th/inventory/purchase-order/03-user-flow-audit-config.md`**:
```
- Sibling: [index.md](./index.md) Section 4 — คำอธิบาย role canonical ของ Auditor และ System Administrator
```
→
```
- หน้าพี่น้อง: [หน้าหลักโมดูล](/th/inventory/purchase-order) Section 4 — คำอธิบาย role canonical ของ Auditor และ System Administrator
```

(Note: the existing `Sibling:` token is left in English in some TH files. If you encounter it, rewrite it to `หน้าพี่น้อง:` for consistency with the other TH sub-pages where it already reads that way.)

**`th/inventory/purchase-request/03-user-flow.md`**:
```
แค็ตตาล็อก role อยู่ที่ [index.md](./index.md) Section 4
```
→
```
แค็ตตาล็อก role อยู่ที่ [หน้าหลักโมดูล](/th/inventory/purchase-request) Section 4
```

**`th/inventory/purchase-request/03-user-flow-approver.md`**:
```
- หน้าพี่น้อง: [index.md](./index.md) Section 4 — คำอธิบาย role ของ Approver ตามมาตรฐานและ stage chain
```
→
```
- หน้าพี่น้อง: [หน้าหลักโมดูล](/th/inventory/purchase-request) Section 4 — คำอธิบาย role ของ Approver ตามมาตรฐานและ stage chain
```

**`th/inventory/purchase-request/03-user-flow-audit-config.md`**:
```
- หน้าพี่น้อง: [index.md](./index.md) Section 4 — คำอธิบาย role ของ Auditor และ System Administrator ตามมาตรฐาน
```
→
```
- หน้าพี่น้อง: [หน้าหลักโมดูล](/th/inventory/purchase-request) Section 4 — คำอธิบาย role ของ Auditor และ System Administrator ตามมาตรฐาน
```

**`th/inventory/purchase-request/03-user-flow-procurement-manager.md`**:
```
- หน้าพี่น้อง: [index.md](./index.md) Section 4 — คำอธิบาย role ของ Procurement Manager ตามมาตรฐาน
```
→
```
- หน้าพี่น้อง: [หน้าหลักโมดูล](/th/inventory/purchase-request) Section 4 — คำอธิบาย role ของ Procurement Manager ตามมาตรฐาน
```

**`th/inventory/purchase-request/03-user-flow-purchaser.md`**:
```
- หน้าพี่น้อง: [index.md](./index.md) Section 4 — คำอธิบาย role ของ Purchaser ตามมาตรฐาน
```
→
```
- หน้าพี่น้อง: [หน้าหลักโมดูล](/th/inventory/purchase-request) Section 4 — คำอธิบาย role ของ Purchaser ตามมาตรฐาน
```

**`th/inventory/purchase-request/03-user-flow-requestor.md`** (two occurrences):

1. `(ดู [index.md](./index.md) Section 4)` → `(ดู [หน้าหลักโมดูล](/th/inventory/purchase-request) Section 4)`
2. `- หน้าพี่น้อง: [index.md](./index.md) Section 4 — คำอธิบาย role ของ Requestor ตามมาตรฐาน` → `- หน้าพี่น้อง: [หน้าหลักโมดูล](/th/inventory/purchase-request) Section 4 — คำอธิบาย role ของ Requestor ตามมาตรฐาน`

**`th/inventory/vendor-pricelist/03-user-flow.md`** (two occurrences):

1. `Catalogue role เองนิยามใน [index.md](./index.md) Section 4` → `แค็ตตาล็อก role อยู่ที่ [หน้าหลักโมดูล](/th/inventory/vendor-pricelist) Section 4` (also fixing the slightly inconsistent prefix wording)
2. `โน้ต: Receiver / Store Keeper ระบุเป็น "ผู้บริโภคทางอ้อม" ใน [index.md](./index.md) Section 4` → `โน้ต: Receiver / Store Keeper ระบุเป็น "ผู้บริโภคทางอ้อม" ใน [หน้าหลักโมดูล](/th/inventory/vendor-pricelist) Section 4`

**`th/inventory/vendor-pricelist/03-user-flow-purchaser.md`**:
```
ไฟล์ persona **Purchaser** รวบ role องค์กรสองตัวที่บันทึกใน [index.md](./index.md) Section 4
```
→
```
ไฟล์ persona **Purchaser** รวบ role องค์กรสองตัวที่บันทึกใน [หน้าหลักโมดูล](/th/inventory/vendor-pricelist) Section 4
```

- [ ] **Step 7.4: Verify all relative back-links are gone**

```bash
grep -rnE "\]\(\./index\.md\)" en/ th/ --include="*.md"
```
Expected: no output.

```bash
grep -rnE "\]\(\.\./index\.md\)" en/ th/ --include="*.md"
```
Expected: no output (Task 6 cleaned the Platform `../index.md` cases).

- [ ] **Step 7.5: Commit**

```bash
git add en/inventory/purchase-order en/inventory/purchase-request en/inventory/vendor-pricelist th/inventory/purchase-order th/inventory/purchase-request th/inventory/vendor-pricelist
git commit -m "$(cat <<'EOF'
docs(inventory): rewrite sub-page back-links to absolute module URLs

PR/PO/vendor-pricelist user-flow sub-pages drop the relative
[index.md](./index.md) reference for an absolute /<locale>/<book>/<module>
link, and rewrite the link text so the sentence still reads naturally
("the module landing" / "หน้าหลักโมดูล").

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 8: Update README.md and CLAUDE.md

**Files:**
- Modify: `README.md` (lines 17, 19, 43 area)
- Modify: `CLAUDE.md` (line 15 area)

- [ ] **Step 8.1: Update README.md tree diagram**

Open `README.md`. Around line 14–22 there is a tree diagram showing the wiki layout. Update the `index.md` lines:

Before:
```
├── en/
│   ├── index.md           # Wiki landing page (book index)
│   └── inventory/
│       ├── index.md       # Module landing page
│       └── ...
```

After:
```
├── en.md                  # Locale landing (sibling of en/)
├── en/
│   ├── inventory.md       # Book landing (sibling of inventory/)
│   └── inventory/
│       ├── costing.md     # Module landing (sibling of costing/)
│       └── costing/
│           ├── 01-data-model.md
│           └── ...
```

Adjust the existing tree to match — preserve any other context in the diagram around it.

- [ ] **Step 8.2: Update README.md page-types table**

Around line 43, find:
```
| `index.md` | Module overview, business context, key concepts, roles, related modules, reference sources, pages-in-this-module |
```

Replace with:
```
| `<module>.md` | Module landing (sibling of `<module>/`): overview, business context, key concepts, roles, related modules, reference sources, pages-in-this-module |
```

- [ ] **Step 8.3: Update CLAUDE.md language-root mention**

Open `CLAUDE.md`. Line 15 currently reads (in context):

> The language-root pages `en/index.md` and `th/index.md` are the two-card landings; each book has its own `<book>/index.md` page that opens the book.

Replace with:

> The language-root pages `en.md` and `th.md` (sibling files at the repo root, beside the `en/` and `th/` folders) are the two-card landings; each book has its own `<book>.md` sibling page (e.g. `en/inventory.md` beside `en/inventory/`) that opens the book.

- [ ] **Step 8.4: Verify**

```bash
grep -nE "(en|th)/index\.md|<book>/index\.md" README.md CLAUDE.md
```
Expected: no output.

```bash
grep -n "index\.md" README.md CLAUDE.md
```
Expected: at most a small number of incidental mentions in unrelated paragraphs (review each — most should be gone after this task).

- [ ] **Step 8.5: Commit**

```bash
git add README.md CLAUDE.md
git commit -m "$(cat <<'EOF'
docs: update README + CLAUDE.md for sibling .md convention

Document the new layout where landing pages sit beside their folder
(en.md, en/inventory.md, en/inventory/costing.md) rather than as
index.md inside the folder.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

---

## Task 9: Final verification + push

No new code. Run the full verification matrix from the spec, then push the branch and prepare the merge.

- [ ] **Step 9.1: Run unit tests**

```bash
pytest scripts/ -v
```
Expected: all tests pass.

- [ ] **Step 9.2: Confirm no `index.md` files remain under `en/` or `th/`**

```bash
find en th -type f -name "index.md"
```
Expected: no output.

- [ ] **Step 9.3: Confirm no `/index` URL references remain in content**

```bash
grep -rnE "/(en|th)/[^[:space:])]+/index\b" en/ th/ --include="*.md"
```
Expected: no output. (Matches inside `docs/superpowers/...` are allowed and out-of-scope.)

- [ ] **Step 9.4: Confirm no relative `index.md` references remain in content**

```bash
grep -rnE "\]\(\.{1,2}/index\.md\)" en/ th/ --include="*.md"
```
Expected: no output.

- [ ] **Step 9.5: Confirm scripts and docs are clean**

```bash
grep -nE "home\.md|home_slug" scripts/sync_nav.py scripts/nav-overrides.yaml scripts/test_sync_nav.py
```
Expected: no output (other than possibly comments explaining the historical change).

```bash
grep -nE "(en|th)/index\.md" README.md CLAUDE.md
```
Expected: no output.

- [ ] **Step 9.6: Run sync_nav build in dry-run and inspect output**

```bash
python scripts/sync_nav.py --mode=build --dry-run 2>&1 | head -60
```
Expected: script completes cleanly. The emitted nav-tree URLs end at `/en/inventory`, `/en/inventory/costing`, etc. — no `/index` suffix.

If `--dry-run` is unsupported, dump to a temp file:
```bash
python scripts/sync_nav.py --mode=build --output=/tmp/nav.json
grep -oE '"target":\s*"/(en|th)/[^"]+"' /tmp/nav.json | sort -u | head -30
```
Expected: targets look like `"target": "/en/inventory"`, not `"target": "/en/inventory/index"`.

- [ ] **Step 9.7: Push the branch**

```bash
git push -u origin feat/folder-name-pages
```

- [ ] **Step 9.8: Open a PR (squash merge intended)**

```bash
gh pr create --title "docs(structure): sibling .md convention for folder landings" --body "$(cat <<'EOF'
## Summary
- Switch from `<folder>/index.md` to sibling `<folder>.md` at every level so Wiki.js URLs resolve as `/en`, `/en/inventory`, `/en/inventory/costing` — no `/index` suffix.
- Update `scripts/sync_nav.py` URL builder to drop the `home_slug` segment and read locale-root headings from `<locale>.md`.
- Rewrite 24 relative `[index.md](./index.md)` back-links in PR/PO/vendor-pricelist sub-pages to absolute `/<locale>/<book>/<module>` with natural-reading link text ("the module landing" / "หน้าหลักโมดูล").
- Refresh `README.md`, `CLAUDE.md` to document the new convention.

## Squash merge
Wiki.js git-storage syncs from `main`. Squash so it sees one atomic structural change rather than 8 intermediate states.

## Manual deploy step
After merge, set Wiki.js admin → Site Settings → Default Path to `/en`.

## Test plan
- [x] `pytest scripts/` passes
- [x] `find en th -name index.md` returns nothing
- [x] `grep -rnE "/(en|th)/[^[:space:])]+/index\b" en/ th/` returns nothing
- [ ] After merge: `/en`, `/en/inventory`, `/en/inventory/costing`, `/en/platform/profile`, `/th/...` all load in `dev.blueledgers.com:3987`
- [ ] Sidebar emits clean `/en/inventory` etc. URLs

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

- [ ] **Step 9.9: After merge — manual Wiki.js admin step**

Log into `dev.blueledgers.com:3987` admin. Navigate to Site Settings → General → "Default Path". Set value to `/en`. Save.

Verify in a private browser window: visiting `dev.blueledgers.com:3987/` redirects to `dev.blueledgers.com:3987/en` and renders the Carmen Wiki two-card landing.

- [ ] **Step 9.10: Spot-check rendered URLs in browser**

Open in browser (the dev wiki at `dev.blueledgers.com:3987`):

- `/en` — Carmen Wiki two-card landing
- `/th` — Thai two-card landing
- `/en/inventory` — Inventory book home, all 18 module links resolve (click 2–3 to confirm)
- `/en/platform` — Platform book home, all 6 module links resolve
- `/en/inventory/costing` — Costing module home, internal links work
- `/en/inventory/purchase-order` — PO module home; click into `03-user-flow.md` and confirm the back-link "the module landing" returns to `/en/inventory/purchase-order`
- `/en/platform/profile` — Profile single-page; back-link "[Platform book index]" goes to `/en/platform`
- Repeat for a sample of `/th/...` paths

If the Wiki.js page cache serves stale `/index` URLs, flush the cache from admin or wait for TTL expiry — this is a known acceptable transient state, not a bug to fix.
