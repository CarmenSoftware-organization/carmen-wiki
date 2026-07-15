# Full Wiki Snapshot Re-sync — Implementation Plan (2026-07-15)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Verify every page of both wiki books (Inventory + Platform, EN + TH) against current source code, create pages for new features, refresh changed screenshots, update coverage checklists, and push everything to the dev Wiki.js instance.

**Architecture:** Module-sequential snapshot verification. Each module is one unit of work: read current source → verify/fix EN pages → mirror TH → commit. Screenshots, checklists, and Wiki.js push are separate downstream tasks fed by per-module findings recorded in a tracking log.

**Tech Stack:** Markdown + Wiki.js frontmatter, Python helper scripts (`scripts/push_pages.py`, `scripts/sync_nav.py`, `.specs/verify_frontmatter.py`), Bash (`scripts/upload_assets.sh`), Playwright capture pipeline in `../carmen-inventory-frontend-e2e`.

**Spec:** `.specs/2026-07-15-full-wiki-snapshot-resync-design.md` (approved 2026-07-15).

## Global Constraints

- Branch: `docs/resync-2026-07-15`. Never commit to `main`. No push to origin / no PR until Task 9.
- Source-of-truth precedence: implementation + e2e tests > `../carmen/docs/` > memory/speculation (CLAUDE.md).
- Frontmatter: on edit, set `date:` to current ISO 8601 UTC timestamp (e.g. `2026-07-15T09:00:00.000Z`); **never modify `dateCreated:`**. New pages: `date` = `dateCreated` = now. Required keys: title, description, published (true), date, tags, editor (markdown), dateCreated.
- Every EN edit gets a semantically mirrored TH edit in the same commit. EN/TH page counts per module must stay equal.
- Internal links: absolute-URL markdown `[Display](/en/<book>/<module>/<slug>)` — never pipe wikilinks `[[t|d]]` (they don't render on this Wiki.js).
- No inline cross-locale links (Wiki.js handles the locale toggle).
- Section style: numbered headings `## 1.` / `### 1.1`; comparison tables over prose; pseudo-code fenced with no language tag; currency `฿`.
- Commit message style: `docs(resync): <module> snapshot — <summary>` (or `docs(spec): …` for `.specs/` files), ending with `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Deferrals recorded in project memory (e.g. TH platform stub deferral, config sub-page gap list) must not be silently undone — Task 5 handles them with an explicit user checkpoint.
- All helper scripts run from the repo root `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki` unless a step says otherwise.

---

### Task 1: Setup — route dumps + tracking log

**Files:**
- Create: `.specs/resync-2026-07-15-progress.md`
- Create: `.specs/resync-2026-07-15-routes-inventory.txt`
- Create: `.specs/resync-2026-07-15-routes-platform.txt`

**Interfaces:**
- Consumes: `../carmen-inventory-frontend-react/routes/router.tsx`, `../carmen-platform/src/App.tsx`.
- Produces: `routes-*.txt` (one route path per line — Tasks 2, 4, 5 diff wiki content against these); `progress.md` (tracking table — every later task appends to it; Task 6 reads its `Screenshot routes flagged` column; Task 7 reads its per-module status).

- [ ] **Step 1: Dump inventory routes**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
grep -oE 'path:\s*"[^"]+"' ../carmen-inventory-frontend-react/routes/router.tsx \
  | sed 's/path:\s*"//; s/"$//' | sort -u > .specs/resync-2026-07-15-routes-inventory.txt
wc -l .specs/resync-2026-07-15-routes-inventory.txt
```

Expected: ~80–120 lines. If 0 lines, the router uses single quotes or JSX `<Route path=…>` — open `../carmen-inventory-frontend-react/routes/router.tsx`, identify the actual pattern, and adjust the grep until the file lists every `path` value.

- [ ] **Step 2: Dump platform routes**

```bash
grep -oE 'path="[^"]+"' ../carmen-platform/src/App.tsx \
  | sed 's/path="//; s/"$//' | sort -u > .specs/resync-2026-07-15-routes-platform.txt
wc -l .specs/resync-2026-07-15-routes-platform.txt
```

Expected: ~30–40 lines (SITEMAP.md lists ~35 routes). Cross-check: `diff <(grep -oE '^\| `/[^`]*`' ../carmen-platform/SITEMAP.md | tr -d '|` ') .specs/resync-2026-07-15-routes-platform.txt` — differences mean SITEMAP.md is stale; trust `App.tsx` and note the drift in the progress log.

- [ ] **Step 3: Create tracking log**

Write `.specs/resync-2026-07-15-progress.md` with exactly this scaffold (fill rows as work proceeds):

```markdown
# Full Wiki Snapshot Re-sync — Progress Log (2026-07-15)

Branch: `docs/resync-2026-07-15`. Spec: `.specs/2026-07-15-full-wiki-snapshot-resync-design.md`.
Approach B: snapshot-verify every page against current source. Last sync: 2026-06-25 (`207d842`).

## Inventory book (source: ../carmen-inventory-frontend-react, backend-v2, bruno, e2e, micro-report/micro-data)

| Module | Pages | Status | Claims fixed | New pages | Screenshot routes flagged |
|--------|-------|--------|--------------|-----------|---------------------------|
| purchase-request | 16 | pending | | | |
| purchase-order | 18 | pending | | | |
| good-receive-note | 13 | pending | | | |
| store-requisition | 16 | pending | | | |
| inventory | 14 | pending | | | |
| inventory-adjustment | 14 | pending | | | |
| physical-count | 10 | pending | | | |
| spot-check | 10 | pending | | | |
| product | 11 | pending | | | |
| recipe | 18 | pending | | | |
| vendor-pricelist | 14 | pending | | | |
| master-data | 14 | pending | | | |
| system-config | 11 | pending | | | |
| access-control | 6 | pending | | | |
| dashboard | 9 | pending | | | |
| reporting-audit | 8 | pending | | | |
| costing | 11 | pending | | | |
| templates | 2 | pending | | | |

## Platform book (source: ../carmen-platform)

| Module | Pages | Status | Claims fixed | New pages | Screenshot routes flagged |
|--------|-------|--------|--------------|-----------|---------------------------|
| clusters | 3 | pending | | | |
| business-units | 2 | pending | | | |
| users | 3 | pending | | | |
| applications | 3 | pending | | | |
| rbac | 3 | pending | | | |
| report-templates | 4 | pending | | | |
| print-template-mapping | 3 | pending | | | |
| news | 3 | pending | | | |
| broadcasts | 3 | pending | | | |
| changelog (page) | 1 | pending | | | |
| profile (page) | 1 | pending | | | |

## Root/landing pages

| Page | Status |
|------|--------|
| en/home.md + th/home.md | pending |
| en/inventory.md + th/inventory.md | pending |
| en/platform.md + th/platform.md | pending |

## Discrepancy log

(claims found in wiki with no source backing — one bullet each: page, claim, what source actually says)

## Route gaps

(source routes with no wiki page — carried decisions in Task 5)

## Deferred

(anything postponed, with reason — e.g. backend down for screenshots)
```

Note for the module-page counts above: they are `find en/inventory/<module> -name '*.md' | wc -l` plus the module landing page `en/inventory/<module>.md` is counted separately when editing — verify counts at module start and correct the table if they drifted.

- [ ] **Step 4: Verify tooling works**

```bash
python3 .specs/verify_frontmatter.py en/inventory/costing.md
```

Expected: `OK: en/inventory/costing.md — title='...'`. (Script checks one file per invocation; loop it in later tasks.)

- [ ] **Step 5: Commit**

```bash
git add .specs/resync-2026-07-15-progress.md .specs/resync-2026-07-15-routes-inventory.txt .specs/resync-2026-07-15-routes-platform.txt
git commit -m "docs(spec): resync 2026-07-15 tracking log + authoritative route dumps

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: Inventory book snapshot — 18 modules, sequential

One iteration per row of the module map below, in listed order. Each iteration is independently committable and reviewable; the procedure (Steps A–G) is identical, only the paths change. **Do not batch modules into one commit.**

**Files (per iteration):**
- Modify: `en/inventory/<module>.md`, `en/inventory/<module>/*.md`, `th/inventory/<module>.md`, `th/inventory/<module>/*.md`
- Modify: `.specs/resync-2026-07-15-progress.md` (status row)

**Interfaces:**
- Consumes: `routes-inventory.txt` (Task 1); source paths from the module map.
- Produces: per-module commit; progress-log row with `Screenshot routes flagged` (consumed by Task 6) and `New pages` candidates (consumed by Task 5).

**Module map** (wiki module → where the truth lives):

| Wiki module | Frontend (in `../carmen-inventory-frontend-react/`) | Bruno collection dir (in `../carmen-turborepo-backend-bruno/`) | E2E specs (in `../carmen-inventory-frontend-e2e/tests/`) |
|---|---|---|---|
| purchase-request | `routes/` + components under procurement purchase-request | folder matching `purchase-request` | specs matching `purchase-request` / `pr` |
| purchase-order | procurement purchase-order (+ `from-price-list`) | `purchase-order` | `purchase-order` / `po` |
| good-receive-note | procurement goods-receive-note | `good-receive-note` or `grn` | `grn` |
| store-requisition | store-operation store-requisition | `store-requisition` | `store-requisition` / `sr` |
| inventory | inventory-management (transaction, period-end, stock views) | `inventory` | `inventory` |
| inventory-adjustment | inventory-management inventory-adjustment | `inventory-adjustment` | `adjustment` |
| physical-count | inventory-management physical-count | `physical-count` | `physical-count` |
| spot-check | inventory-management spot-check | `spot-check` | `spot-check` |
| product | product-management | `product` | `product` |
| recipe | operation-plan (recipe, category, cuisine, equipment) | `recipe` | `recipe` |
| vendor-pricelist | vendor-management (vendor, price-list, request-price-list, price-list-template) | `vendor` / `price-list` | `vendor` / `price-list` |
| master-data | config (location, department, delivery-point, currency, unit, tax-profile, …) | `config` / master-data folders | `config` |
| system-config | system-admin (period, running-code, workflow, notification, activity-log) | `system-admin` folders | `system-admin` |
| access-control | system-admin user/role/permission + route guards | `user` / `role` / `permission` | `auth` / `permission` |
| dashboard | dashboard (widget workspace, KPI cards) | `dashboard` | `dashboard` |
| reporting-audit | report (list/schedules/history) **plus** `../micro-report/` and `../micro-data/` | `report` | `report` |
| costing | period-end/costing views **plus** backend costing engine in `../carmen-turborepo-backend-v2/` and `../carmen/docs/` costing | `costing` if present | `costing` / `period-end` |
| templates | PR-template + `price-list-template` routes | `template` | `template` |

Locate exact dirs at iteration start with, e.g.: `ls ../carmen-inventory-frontend-react/components/ | grep -i <module>` and `ls ../carmen-turborepo-backend-bruno/ | grep -i <module>` — the table names the concept, the filesystem gives the exact path. If a Bruno/e2e dir doesn't exist for a module, note it in the progress log and verify API claims against backend controllers in `../carmen-turborepo-backend-v2/apps/` instead.

Per module, execute:

- [ ] **Step A: Read source first**

Read, in order: (1) the module's route entries in `.specs/resync-2026-07-15-routes-inventory.txt`; (2) the frontend module components (list/detail/new screens, hooks — enough to know current fields, buttons, tabs, statuses, permission checks); (3) Bruno requests for the module's endpoints (exact request/response shapes); (4) e2e specs (expected behaviors); (5) backend service code only where a wiki page makes a backend-behavior claim the frontend can't confirm (validation rules, calculations, doc_version rules). For `costing` and `reporting-audit`, the backend/micro-service side is primary, not optional.

- [ ] **Step B: Verify every EN page of the module**

For `en/inventory/<module>.md` and each file in `en/inventory/<module>/`, check each verifiable claim against what Step A found:
- route paths quoted in the page exist in `routes-inventory.txt`
- field names, button labels, tab names, status values match the components
- permission keys match route guards / `hasPermission` calls
- API endpoints + request/response shapes match Bruno
- business rules / edge-case tables match backend logic and e2e assertions

Fix wrong claims in place. Claims that are design-rationale or historical context (not checkable against code) stay untouched. A claim with **no** source backing: rewrite from current source and add a bullet to the progress log's **Discrepancy log**.

- [ ] **Step C: Bump frontmatter date on every edited page**

Set `date:` to now (UTC ISO 8601) on each file actually edited — untouched files keep their old `date`.

- [ ] **Step D: Mirror to TH**

For every EN page edited, apply the same change semantically to the matching `th/inventory/...` page (translate prose, keep code/identifiers/routes verbatim). Also scan each TH page in the module for structural drift against its EN counterpart (missing sections, stale routes) and fix — this is snapshot mode, TH gets verified too. Bump `date:` on edited TH files.

- [ ] **Step E: Flag screenshots + record findings**

If any screen the module's curated screenshots depict changed visibly (new columns, renamed buttons, new tabs), add the route(s) to the module's `Screenshot routes flagged` cell. Routes in source with no wiki page: add to the **Route gaps** section (decision in Task 5, don't author yet). Update the module row: `Status` = `IN SYNC` (no edits) or `EDITED (n pages)`, fill `Claims fixed` with a one-line summary.

- [ ] **Step F: Verify frontmatter + mirror parity**

```bash
for f in $(git diff --name-only -- 'en/**/*.md' 'th/**/*.md'); do python3 .specs/verify_frontmatter.py "$f" || echo "BROKEN: $f"; done
echo "EN: $(find en/inventory/<module> -name '*.md' | wc -l)  TH: $(find th/inventory/<module> -name '*.md' | wc -l)"
git diff --stat -- 'en/*' | tail -1; git diff --stat -- 'th/*' | tail -1
```

Expected: all `OK`, EN/TH counts equal, both locales show changes when either does (unless genuinely EN-only fix of an EN-only typo — then say so in the commit body).

- [ ] **Step G: Commit**

```bash
git add en/inventory/<module> en/inventory/<module>.md th/inventory/<module> th/inventory/<module>.md .specs/resync-2026-07-15-progress.md
git commit -m "docs(resync): <module> snapshot — <one-line summary of fixes, or 'in sync, no content change'>

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

If a module is fully IN SYNC (zero page edits), commit only the progress-log row update, batching consecutive in-sync modules into one `docs(resync): progress — <m1>, <m2> in sync` commit is allowed.

---

### Task 3: Root and landing pages

**Files:**
- Modify: `en/home.md`, `th/home.md`, `en/inventory.md`, `th/inventory.md`, `en/platform.md`, `th/platform.md`
- Modify: `.specs/resync-2026-07-15-progress.md`

**Interfaces:**
- Consumes: module lists as they exist after Task 2 (inventory) and current `en/platform/` tree.
- Produces: verified landing pages; commit.

- [ ] **Step 1: Verify the two-card landing (`home.md`) and both book landings**

Check: card/book descriptions still accurate; every module link on `en/inventory.md` / `en/platform.md` points at an existing page (`/en/inventory/<module>` etc.); no dead links; module lists complete vs the filesystem:

```bash
for slug in $(grep -oE '\(/en/[a-z0-9/-]+\)' en/inventory.md | tr -d '()'); do f="${slug#/}.md"; [ -f "$f" ] || echo "DEAD: $slug"; done
for slug in $(grep -oE '\(/en/[a-z0-9/-]+\)' en/platform.md | tr -d '()'); do f="${slug#/}.md"; [ -f "$f" ] || echo "DEAD: $slug"; done
```

Expected: no `DEAD:` lines. Fix EN, mirror TH, bump `date:` on edited files.

- [ ] **Step 2: Frontmatter check + commit**

```bash
for f in en/home.md th/home.md en/inventory.md th/inventory.md en/platform.md th/platform.md; do python3 .specs/verify_frontmatter.py "$f"; done
git add en/home.md th/home.md en/inventory.md th/inventory.md en/platform.md th/platform.md .specs/resync-2026-07-15-progress.md
git commit -m "docs(resync): root + book landing pages verified

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

(Skip the commit if nothing changed except the progress log — fold the log row into the next commit instead.)

---

### Task 4: Platform book snapshot — 11 units

Same procedure as Task 2 Steps A–G with these substitutions; one commit per unit (or batch consecutive in-sync units in the progress-log commit):

- Source = `../carmen-platform/src/` only (routes in `src/App.tsx`, screens/components under `src/`; `SITEMAP.md` is a hint, `App.tsx` is truth). Backend claims verify against Bruno (`../carmen-turborepo-backend-bruno/`, platform folders) when pages quote endpoints.
- Wiki paths = `en/platform/<module>...` / `th/platform/<module>...`; standalone pages `en/platform/changelog.md`, `en/platform/profile.md` are one-page units.
- Route dump = `.specs/resync-2026-07-15-routes-platform.txt`.
- Known change themes since last sync (verify, don't assume): RBAC permission keys on routes (`cluster.read`, `application.*`, `role.*`, …), `feat/env-modes` (merged 2026-07-15), tenant-migrations route, current business-unit GET/PUT/PATCH endpoints (Bruno commit `d8e4675`).
- Unit order: clusters, business-units, users, applications, rbac, report-templates, print-template-mapping, news, broadcasts, changelog, profile.
- BU routes reuse `cluster.*` permission keys — that is intentional, not a doc bug (project memory).
- Commit message: `docs(resync): platform/<module> snapshot — <summary>`.

- [ ] All 11 units processed, committed, progress log rows filled.

---

### Task 5: New pages for uncovered features

**Files:**
- Create: `en/platform/dashboard.md`-style new pages as decided below (exact list comes from Route gaps)
- Modify: parent module landing pages (§7 sub-page lists), `.specs/resync-2026-07-15-progress.md`

**Interfaces:**
- Consumes: **Route gaps** section of the progress log (filled by Tasks 2 & 4).
- Produces: new EN+TH page pairs; list of new pages for Task 6 (screenshots), Task 7 (checklist rows), Task 8 (nav entries).

- [ ] **Step 1: Split the gap list into two buckets**

- **Bucket A — new since last sync:** the feature/route did not exist at 2026-06-25 (check: `git -C ../carmen-inventory-frontend-react log --oneline --since=2026-06-25 -- <feature dir>` shows its introduction, or it's absent from `.specs/resync-react-stack-2026-06-18-routes.txt`). → author pages now.
- **Bucket B — pre-existing documented deferrals:** gaps already logged on 2026-06-18 (`/config/*` sub-pages, detail-route quoting, Platform Dashboard hub + Landing page from platform-coverage-checklist). → do **not** author; present the bucket to the user with page-count estimate and ask create-now vs keep-deferred (AskUserQuestion). Honor the answer; record it in the progress log.

- [ ] **Step 2: Author Bucket A (and any Bucket B approved) pages**

For each new page: copy the structure of the closest existing sibling (PR module sub-pages are the reference; `.specs/platform-sub-page-template.md` for platform pages; `.specs/templates/` holds inventory sub-page templates). Content synthesized from source per the Task 2 Step A reading order. Frontmatter: `date` = `dateCreated` = now, `published: true`, `editor: markdown`. Write EN, then TH mirror. Add the page to the parent module's §7 sub-page list as `[Display](/en/inventory/<module>/<slug>)` (and TH list with `/th/...`).

- [ ] **Step 3: Verify + commit per module touched**

```bash
for f in $(git status --porcelain -- en th | awk '{print $2}'); do python3 .specs/verify_frontmatter.py "$f"; done
git add <new and modified files> .specs/resync-2026-07-15-progress.md
git commit -m "docs(resync): new pages — <module>/<slug>[, ...]

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Selective screenshot refresh (deferrable)

**Files:**
- Create: `.specs/resync-2026-07-15-screenshot-remap.md`
- Modify: `assets/screenshots/<book>/<module>/<slug>.png` (recaptured files only)

**Interfaces:**
- Consumes: `Screenshot routes flagged` cells from the progress log; capture pipeline `../carmen-inventory-frontend-e2e/tests/wiki-screenshots/` (`manifest.ts`, `capture.spec.ts`); curated set `assets/screenshots/`.
- Produces: refreshed PNGs (Task 8 uploads them); remap doc for future runs.

- [ ] **Step 1: Build the route→curated remap**

The capture pipeline's output names and the curated embed set are **not linked** (known trap). Read `../carmen-inventory-frontend-e2e/tests/wiki-screenshots/manifest.ts` (route+slug definitions) and list the curated files (`find assets/screenshots -name '*.png'`). Write `.specs/resync-2026-07-15-screenshot-remap.md`: a table `capture route → capture output file → curated path (or NONE)`. Only flagged routes need rows filled; note unmapped-but-flagged routes explicitly.

- [ ] **Step 2: Preconditions for capture**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-inventory-frontend-e2e
grep -E 'BACKEND_URL|BASE_URL' .env
curl -sS -o /dev/null -w "%{http_code}\n" "$(grep -E '^BACKEND_URL' .env | cut -d= -f2)/health" || true
find . -maxdepth 2 -type d -name '.auth' -not -path './node_modules/*'
```

Backend must answer (2xx/3xx) and point at the data-rich tenant (**zebra**, not blueledgers). Delete any `.auth` dir found (stale cache = silent login failure). If the backend is down or wrong-tenant and can't be fixed locally: write the flagged-route list under **Deferred** in the progress log, commit that, and skip to Task 7 — screenshots must not block Tasks 7–9.

- [ ] **Step 3: Capture flagged routes only**

```bash
bunx playwright test --project=wiki-screenshots --grep "<route-or-slug-pattern>"
```

One `--grep` per flagged route (pattern = the spec title/slug from `manifest.ts` — confirm the grep matches by running with `--list` first: `bunx playwright test --project=wiki-screenshots --list --grep "<pattern>"`). Output lands in the e2e repo's screenshots dir (see `capture.spec.ts` for the exact output path).

- [ ] **Step 4: Copy into curated set + verify + commit**

Copy each capture to its curated path per the remap (overwrite). Then:

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
git diff --stat -- assets/screenshots | tail -1
file assets/screenshots/<book>/<module>/<slug>.png   # sanity: PNG image data, non-zero size
git add assets/screenshots .specs/resync-2026-07-15-screenshot-remap.md .specs/resync-2026-07-15-progress.md
git commit -m "docs(resync): refresh screenshots for changed routes

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

Visually open 2–3 recaptured PNGs (Read tool) and confirm they show the expected screen, logged-in, zebra data — not a login page.

---

### Task 7: Coverage checklists

**Files:**
- Modify: `.specs/process-coverage-checklist.md` (Inventory — 79% / 279 sub-processes as of 2026-06-09)
- Modify: `.specs/platform-coverage-checklist.md` (Platform — 98% / 86 sub-processes)

**Interfaces:**
- Consumes: progress log statuses + Task 5 new-page list.
- Produces: updated coverage numbers quoted in the Task 9 PR body.

- [ ] **Step 1: Update rows**

For each checklist: flip statuses where Task 2/4/5 work changed reality (new pages → `Partial`→`Done` or new rows; edited pages that filled a documented gap → status up). Add rows for genuinely new sub-processes discovered in source. Recompute the summary percentages from the actual row counts (count `Done` / total with grep, don't eyeball):

```bash
grep -c 'Done' .specs/process-coverage-checklist.md
```

(Adjust the pattern to the checklist's actual status column format — open the file first.)

- [ ] **Step 2: Commit**

```bash
git add .specs/process-coverage-checklist.md .specs/platform-coverage-checklist.md
git commit -m "docs(spec): coverage checklists updated post-resync

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: Dev Wiki.js sync

**Files:** none in repo (remote side-effects) — plus `.specs/resync-2026-07-15-progress.md` result notes.

**Interfaces:**
- Consumes: all `.md` files changed on the branch; recaptured PNGs; `scripts/.env` (`WIKI_API_URL`, `WIKI_API_TOKEN`), root `.env` for `sync_nav.py`.
- Produces: dev wiki at `http://dev.blueledgers.com:3987/` matching the branch.

- [ ] **Step 1: Push changed pages**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
git diff --name-only main...HEAD -- 'en/**/*.md' 'th/**/*.md' 'en/*.md' 'th/*.md' > /tmp/changed-pages.txt
wc -l /tmp/changed-pages.txt
python3 scripts/push_pages.py $(cat /tmp/changed-pages.txt)
```

Expected: one `OK`/updated line per page, no errors. **New pages (Task 5) may not exist in Wiki.js yet — `push_pages.py` only updates existing pages** (it maps to page ids). If any new page reports not-found, create it via the same GraphQL API (`pages.create` mutation, mirroring the `UPDATE` mutation fields in `push_pages.py`) or through the Wiki.js admin UI, then re-run push for that file. Log per-page failures, retry once, then record persistent failures under **Deferred**.

- [ ] **Step 2: Upload refreshed screenshots (if Task 6 ran)**

```bash
scripts/upload_assets.sh $(git diff --name-only main...HEAD -- 'assets/screenshots/**/*.png')
```

Expected: `OK   /screenshots/<module>/<file>` per file. **Caveat:** `upload_assets.sh` has a hard-coded inventory `folder_id` map only — a platform-module PNG prints `SKIP (no folder id …)`. If platform screenshots were refreshed: look up the folder id in Wiki.js admin (Assets), extend the `folder_id()` case list in the script, commit that script change, re-run.

- [ ] **Step 3: Navigation**

Only needed if Task 5 created pages (new nav links) — otherwise skip:

```bash
source .venv/bin/activate 2>/dev/null || (python3 -m venv .venv && source .venv/bin/activate && pip install -r scripts/requirements.txt)
set -a; source .env; set +a
python3 scripts/sync_nav.py --dry-run --verbose
```

Read every line; `⚠ [fallback]` means a TH label failed to resolve — fix (TH page frontmatter or `nav-overrides.yaml`) before the live run. New module-level entries require build mode (`--mode=build`) per `scripts/README.md`; new sub-pages under existing modules only need mirror mode. Then run live: `python3 scripts/sync_nav.py` (add `--mode=build` only if used in dry-run).

- [ ] **Step 4: Browser spot-check**

Open `http://dev.blueledgers.com:3987/` (claude-in-chrome). Check: (a) 3 edited inventory pages EN + their TH twins render with the new content, (b) 1 edited platform page EN+TH, (c) every Task 5 new page reachable from its module's §7 list, (d) refreshed screenshots display (no broken images), (e) nav shows new entries in both locales. Record pass/fail per check in the progress log; fix and re-push anything broken.

---

### Task 9: Final verification + PR

**Interfaces:**
- Consumes: everything above.
- Produces: pushed branch + open PR.

- [ ] **Step 1: Full-tree verification**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
fail=0; for f in $(git diff --name-only main...HEAD -- '*.md' | grep -E '^(en|th)/'); do python3 .specs/verify_frontmatter.py "$f" >/dev/null || { echo "FAIL: $f"; fail=1; }; done; echo "frontmatter fail=$fail"
for L in en th; do echo "$L inventory: $(find $L/inventory -name '*.md' | wc -l)  platform: $(find $L/platform -name '*.md' | wc -l)"; done
grep -rn '\[\[.*|.*\]\]' en th && echo "PIPE WIKILINKS FOUND — fix" || echo "no pipe wikilinks"
for f in $(git diff --name-only main...HEAD -- '*.md' | grep -E '^(en|th)/'); do for slug in $(grep -oE '\((/(en|th)/[a-z0-9/-]+)\)' "$f" | tr -d '()'); do [ -f "${slug#/}.md" ] || echo "DEAD LINK in $f: $slug"; done; done
git diff main...HEAD --stat | tail -1
```

Expected: `fail=0`, EN/TH counts equal per book, no pipe wikilinks, no dead links.

- [ ] **Step 2: Confirm `dateCreated` untouched**

```bash
git diff main...HEAD -- '*.md' | grep -E '^[-+]dateCreated:' && echo "dateCreated CHANGED — revert those hunks" || echo "dateCreated clean"
```

Expected: `dateCreated clean` (new files show only `+dateCreated:` with no matching `-` line — inspect any hits: a `-`/`+` pair on the same file is a violation).

- [ ] **Step 3: Push branch + open PR**

```bash
git push -u origin docs/resync-2026-07-15
gh pr create --title "docs: full wiki snapshot re-sync 2026-07-15" --body "$(cat <<'EOF'
## Summary
- Snapshot-verified all pages of both books (Inventory 18 modules, Platform 11 units, EN+TH) against current source
- <n> claims fixed across <n> pages; <n> new pages; <n> screenshots refreshed
- Coverage: Inventory <x>% (was 79%), Platform <x>% (was 98%)
- Dev Wiki.js synced and spot-checked

Tracking log: `.specs/resync-2026-07-15-progress.md`
Spec: `.specs/2026-07-15-full-wiki-snapshot-resync-design.md`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Fill the `<n>`/`<x>` placeholders from the progress log and checklists before running.

---

## Self-review notes

- Spec coverage: Phase 0→Task 1, Phase 1→Task 2, Phase 2→Task 4, Phase 3→Task 5, Phase 4→Task 6, Phase 5→Task 7, Phase 6→Task 8; root pages (spec scope table) → Task 3; PR/verification (spec "definition of done") → Task 9. ✔
- Deferral guard (memory): Bucket B user checkpoint in Task 5. ✔
- Known tool gaps encoded: `push_pages.py` update-only, `upload_assets.sh` inventory-only folder ids, capture `.auth` cache, route→curated remap. ✔
