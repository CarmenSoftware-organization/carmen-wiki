# Inventory Wiki Resync to React/Vite Stack — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resync `en/inventory` + `th/inventory` routes, frontend-architecture statements, and screen behavior to match `carmen-inventory-frontend-react` (Vite + React Router 7 SPA).

**Architecture:** Three layered passes ordered cheap→expensive. Pass 1 mechanically diffs every documented route against the authoritative table generated from `router.tsx`. Pass 2 corrects the handful of sentences that describe frontend infrastructure. Pass 3 re-verifies screen behavior only for modules flagged by Pass 1 or by `-react` git history; everything else gets a recorded spot-check.

**Tech Stack:** Markdown content (Wiki.js), no build/test pipeline. "Tests" in this plan are **verification shell commands** whose output is checked — a passing check is an empty diff or an expected count, not a unit test.

## Global Constraints

- **Scope:** `en/inventory/**` and `th/inventory/**` only. Platform book (`*/platform/**`) is **out of scope** (it tracks the unchanged `carmen-platform` repo).
- **No new pages, no gap-filling:** correct drift caused by the stack change only. Do not author pages for undocumented routes; do not fill pre-existing TODO/coverage gaps (e.g. physical-count / spot-check behavior sections). Log them instead.
- **EN + TH mirrored:** every content change applies to both locale copies.
- **Frontmatter:** update `date` on edited pages to the edit timestamp; **never** change `dateCreated`.
- **Preserve conventions:** numbered `## N.` sections, comparison tables, untagged pseudo-code fences, ฿ currency.
- **Keep the 2 intentional historical annotations** ("legacy Next.js repo") in `en/inventory/dashboard/widget-workspace.md` and its TH mirror unchanged.
- **Source-of-truth order:** `-react/routes/router.tsx` → `-react` components/`lib` → `-react/CLAUDE.md` → `../carmen/docs/`. Code wins on conflict.
- **Repo paths:** wiki = `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki` (run all commands from here); react app = `../carmen-inventory-frontend-react`.
- **Branch:** `docs/resync-react-stack-2026-06-18` (already created; spec already committed there).

---

### Task 1: Setup — authoritative route list + tracking log

Generates the deterministic route table everything else diffs against, and the progress log.

**Files:**
- Create: `.specs/resync-react-stack-2026-06-18-routes.txt`
- Create: `.specs/resync-react-stack-2026-06-18.md`

**Interfaces:**
- Produces: `routes.txt` — one absolute route per line, `:id`-style params, sorted unique. Consumed by Task 2.
- Produces: tracking log with a module table. Appended to by Tasks 2–6.

- [ ] **Step 1: Generate the authoritative route list from router.tsx**

The router's `import("./<path>/page")` string equals the full route (strip `./` and `/page`, convert `[x]`→`:x`, prefix `/`). Run:

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
grep -oE 'import\("\./[^"]+/page"\)' ../carmen-inventory-frontend-react/routes/router.tsx \
  | sed -E 's|import\("\./||; s|/page"\)||; s|\[([a-z_]+)\]|:\1|g; s|^|/|' \
  | sort -u > .specs/resync-react-stack-2026-06-18-routes.txt
# Append the two special-case routes whose path != import path:
printf '/login\n/pl/:url_token\n' >> .specs/resync-react-stack-2026-06-18-routes.txt
sort -u -o .specs/resync-react-stack-2026-06-18-routes.txt .specs/resync-react-stack-2026-06-18-routes.txt
wc -l .specs/resync-react-stack-2026-06-18-routes.txt
```

Expected: ~125–127 lines, including entries like `/inventory-management/physical-count/:id/entry`, `/inventory-management/period-end`, `/store-operation/stock-replenishment`, `/operation-plan/recipe-equipment-category`.

- [ ] **Step 2: Verify the known-drift targets are present (and the stale forms absent)**

```bash
grep -xE '/inventory-management/period-end(/review)?' .specs/resync-react-stack-2026-06-18-routes.txt
grep -x '/store-operation/stock-replenishment' .specs/resync-react-stack-2026-06-18-routes.txt
grep -x '/operation-plan/recipe-equipment-category' .specs/resync-react-stack-2026-06-18-routes.txt
grep -x '/inventory-management/period-end-process' .specs/resync-react-stack-2026-06-18-routes.txt || echo "OK: period-end-process is NOT a real route (expected)"
```

Expected: first three print matches; the fourth prints `OK: ...`.

- [ ] **Step 3: Create the tracking log**

Write `.specs/resync-react-stack-2026-06-18.md` with this content:

```markdown
# Resync to React/Vite stack — progress log (2026-06-18)

Source of truth: `../carmen-inventory-frontend-react`. Scope: inventory book only.

| Module | Pass1 routes-fixed | Pass2 arch-deltas | Pass3 behavior | Notes |
|--------|--------------------|-------------------|----------------|-------|
| config | | | | |
| procurement (PR/PO/GRN/credit-note) | | | | |
| inventory-management (adjustment/physical-count/spot-check/period-end/transaction) | | | | |
| vendor-management (vendor/price-list/request-price-list) | | | | |
| store-operation (store-requisition/wastage/stock-replenishment) | | | | |
| operation-plan (recipe/category/cuisine/equipment) | | | | |
| product-management | | | | |
| system-admin (user-activity/period/workflow/etc.) | | | | |
| report | | | | |
| dashboard | | | | |

## Route gaps (app route with no wiki page) — log only, do not author
(none yet)

## Behavior signals (Task 4)
(filled in Task 4)
```

- [ ] **Step 4: Commit**

```bash
git add .specs/resync-react-stack-2026-06-18-routes.txt .specs/resync-react-stack-2026-06-18.md
git commit -m "docs(resync): authoritative route list + tracking log scaffold

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: Pass 1 — Route-table verification & fixes

Diffs every app route referenced in the inventory book against `routes.txt`; fixes stale/wrong-prefix routes in EN+TH; logs gaps.

**Files:**
- Modify: any `en/inventory/**/*.md` + matching `th/inventory/**/*.md` containing a stale route
- Modify: `.specs/resync-react-stack-2026-06-18.md` (Pass1 column + gaps section)

**Interfaces:**
- Consumes: `.specs/resync-react-stack-2026-06-18-routes.txt` (Task 1).

- [ ] **Step 1: Extract documented app-route references (EN), excluding asset/locale links**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
SECTIONS='config|procurement|inventory-management|vendor-management|store-operation|operation-plan|product-management|system-admin|report|dashboard|profile|notifications'
grep -rnoE "/($SECTIONS)/[a-z0-9/:_-]+" en/inventory 2>/dev/null \
  | grep -vE '/screenshots/|/en/|/th/|\.png|\.md' \
  | sort -t: -k1 > /tmp/wiki-routes-en.txt
wc -l /tmp/wiki-routes-en.txt
```

This is the candidate list of documented routes with their file:line.

- [ ] **Step 2: Find stale references — documented routes not in the authoritative list**

```bash
# Strip file:line, normalize numeric/uuid ids to :id, compare against routes.txt
cut -d: -f3- /tmp/wiki-routes-en.txt \
  | sed -E 's|/[0-9a-f-]{6,}|/:id|g; s|/[0-9]+|/:id|g' \
  | sort -u > /tmp/wiki-routes-norm.txt
echo "=== documented routes with NO exact match in app (candidates to fix) ==="
comm -23 /tmp/wiki-routes-norm.txt <(sort -u .specs/resync-react-stack-2026-06-18-routes.txt)
```

Expected: a short list. Each line is either a **stale route to fix** (e.g. `/inventory-management/period-end-process`, `/store-operation/stock-replenishment` if it currently reads `/store-requisition/stock-replenishment`) or a **deeper sub-path** that is a documented anchor — inspect each manually in the next step.

- [ ] **Step 3: For each stale route, locate and fix it in EN + TH**

For every candidate from Step 2, find its occurrences and correct to the real route. Example for the confirmed `period-end-process` drift:

```bash
grep -rn 'period-end-process' en/inventory th/inventory
```

Then edit each hit, replacing `/inventory-management/period-end-process` with `/inventory-management/period-end` (the index page) or `/inventory-management/period-end/review` per context. Repeat for each stale route. **Apply the identical fix to the TH mirror of every edited EN page.** Update each edited page's frontmatter `date`:

```bash
date -u +%Y-%m-%dT%H:%M:%S.000Z   # use this value for the `date:` field
```

- [ ] **Step 4: Log route gaps (app routes with no wiki page) — do not author pages**

```bash
echo "=== app routes never referenced anywhere in the inventory book ==="
while read -r r; do
  grep -rqF "$r" en/inventory || echo "GAP: $r"
done < .specs/resync-react-stack-2026-06-18-routes.txt
```

Paste the `GAP:` lines under the "Route gaps" section of the tracking log. Do **not** create pages for them.

- [ ] **Step 5: Verify no stale documented routes remain**

```bash
SECTIONS='config|procurement|inventory-management|vendor-management|store-operation|operation-plan|product-management|system-admin|report|dashboard|profile|notifications'
grep -rnoE "/($SECTIONS)/[a-z0-9/:_-]+" en/inventory 2>/dev/null \
  | grep -vE '/screenshots/|/en/|/th/|\.png|\.md' \
  | cut -d: -f3- | sed -E 's|/[0-9a-f-]{6,}|/:id|g; s|/[0-9]+|/:id|g' | sort -u \
  | comm -23 - <(sort -u .specs/resync-react-stack-2026-06-18-routes.txt)
```

Expected: empty output (every documented route now matches the app), except any line you have explicitly justified in the log as an intentional anchor/sub-path. Re-run the same on `th/inventory` and confirm parity.

- [ ] **Step 6: Mark Pass1 column in the tracking log and commit**

Fill the `Pass1 routes-fixed` cell for each touched module (e.g. "period-end-process→period-end (EN+TH)"). Then:

```bash
git add en/inventory th/inventory .specs/resync-react-stack-2026-06-18.md
git commit -m "docs(resync): Pass 1 — align documented routes with router.tsx

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: Pass 2 — Architecture deltas

Corrects only wiki sentences that state a frontend mechanism that the stack change made wrong.

**Files:**
- Modify: inventory-book pages that describe frontend infra (EN+TH)
- Modify: `.specs/resync-react-stack-2026-06-18.md` (Pass2 column)

**Interfaces:**
- Reference facts (from `-react/CLAUDE.md` + `lib/`), to be reflected verbatim where relevant:
  - No server: static bundle on S3/CloudFront; browser calls backend directly; no SSR / server components / route handlers.
  - `lib/http-client.ts` rewrites `/api/proxy/<rest>` and `/api/external/<rest>` → `${BACKEND_URL}/<rest>`, attaching `Authorization: Bearer` + `x-app-id`.
  - Auth: access token in memory (`lib/auth/token-store.ts`); refresh token in localStorage (`lib/auth/refresh-token-storage.ts`); boot order `loadRuntimeConfig() → refreshTokens() → render`; `RequireAuth` → `/login` when token store empties.

- [ ] **Step 1: Find candidate infra sentences**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
grep -rniE '\b(server-side render|SSR|server component|server action|route handler|getServerSide|app router|next-intl|API route)\b' en/inventory th/inventory \
  | grep -v 'legacy Next.js'
grep -rniE '\b(authenticat|bearer token|access token|refresh token|/api/|endpoint base|proxy)\b' en/inventory th/inventory | head -40
```

- [ ] **Step 2: Triage and correct**

For each hit, decide: (a) describes ERP/backend behavior → **leave untouched**; (b) describes the *frontend mechanism* in Next.js terms that is now wrong → correct using the Interface facts above. Keep edits minimal — replace the wrong clause, do not rewrite the section. Apply to EN + TH together; update `date` frontmatter on edited pages.

If Step 1 surfaces **no** frontend-mechanism sentences (likely — the inventory book documents ERP behavior, not frontend infra), record "no infra prose in inventory book; no deltas needed" in the log and skip to Step 3.

- [ ] **Step 3: Verify and commit**

```bash
grep -rniE '\b(SSR|server component|server action|app router|API route)\b' en/inventory th/inventory | grep -v 'legacy Next.js'
```

Expected: empty (no current-tense Next.js mechanism claims remain). Fill the Pass2 column, then:

```bash
git add en/inventory th/inventory .specs/resync-react-stack-2026-06-18.md
git commit -m "docs(resync): Pass 2 — SPA architecture deltas

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

(If no edits were needed, commit only the tracking-log note.)

---

### Task 4: Pass 3a — Compile behavior signals

Builds the bounded list of modules that actually need a behavior re-read.

**Files:**
- Modify: `.specs/resync-react-stack-2026-06-18.md` ("Behavior signals" section)

- [ ] **Step 1: Collect signals from `-react` git history**

```bash
git -C ../carmen-inventory-frontend-react log --oneline -40 \
  | grep -iE 'feat|fix' | grep -viE 'merge|spec|docs|runtime config|deploy'
```

Map each functional commit to a wiki module (e.g. `doc_version` → config/vendor/location; `location delivery-point display`; `server-error placeholder stripping` → cross-cutting). **Cross-check the prior resync** so already-synced items are not redone:

```bash
grep -ril 'doc_version\|optimistic' en/inventory | head
```

If a behavior is already documented (doc_version was resynced 2026-06-17), mark it "already synced" and drop it from the signal list.

- [ ] **Step 2: Add Pass-1-flagged modules**

Every module whose route was fixed in Task 2 is also a behavior signal (the route change may carry a flow change). List them.

- [ ] **Step 3: Write the signal list and commit**

Under "Behavior signals" in the log, write the final module list with the reason for each (`route-changed` / `git: <commit>` / `already-synced — skip`). Commit:

```bash
git add .specs/resync-react-stack-2026-06-18.md
git commit -m "docs(resync): Pass 3a — behavior-signal module list

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Pass 3b — Resync flagged modules

Reads the real component for each signal module and fixes drifted behavior prose.

**Files:**
- Modify: the signal modules' pages (EN+TH)
- Modify: `.specs/resync-react-stack-2026-06-18.md` (Pass3 column)

- [ ] **Step 1: For each signal module, read the real screen and compare**

For module M with wiki page `en/inventory/<M>.md` (and sub-pages), open the corresponding `-react/routes/<section>/<M>/page.tsx` and the components/hooks it imports. Example:

```bash
ls ../carmen-inventory-frontend-react/routes/inventory-management/physical-count/
sed -n '1,80p' ../carmen-inventory-frontend-react/routes/inventory-management/physical-count/page.tsx
```

Compare the wiki's documented screen behavior (actions, columns, states, gating) against the code.

- [ ] **Step 2: Fix only genuine drift**

Where the wiki states behavior that no longer matches the component, correct the sentence(s). Do not rewrite correct prose; do not add new sections for undocumented behavior (log as a gap instead). Apply EN+TH; update `date`.

- [ ] **Step 3: Record status per module**

In the Pass3 column write one of: `fixed: <what>`, `verified — no change`, or `gap logged`. 

- [ ] **Step 4: Commit (one commit per module, or per coherent group)**

```bash
git add en/inventory th/inventory .specs/resync-react-stack-2026-06-18.md
git commit -m "docs(resync): Pass 3 — <module> behavior verified against -react

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Pass 3c — Spot-check no-signal modules & finalize log

Confirms the "patterns identical to source app" claim for modules with no signal, so every module has a recorded status.

**Files:**
- Modify: `.specs/resync-react-stack-2026-06-18.md`

- [ ] **Step 1: Spot-check each no-signal module**

For each module not in the Task 4 signal list, open its `-react` `page.tsx` and confirm at a glance that the screen shape (list/detail, key actions) matches what the wiki describes. This is a confirmation, not a deep audit.

- [ ] **Step 2: Record `verified — no change` for each in the Pass3 column**

Ensure **every** row in the module table has a non-empty Pass3 cell.

- [ ] **Step 3: Verify completeness and commit**

```bash
grep -nE '^\| [a-z]' .specs/resync-react-stack-2026-06-18.md   # eyeball: no empty Pass3 cells
git add .specs/resync-react-stack-2026-06-18.md
git commit -m "docs(resync): Pass 3c — spot-check no-signal modules; log complete

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Finishing — dev Wiki.js sync & PR

External steps; **confirm with the user before each**.

- [ ] **Step 1: Summarize the diff for the user**

```bash
git log --oneline main..HEAD
git diff --stat main..HEAD
```

Present the change summary and the route-gap list. Ask whether to (a) sync to dev Wiki.js and (b) open the PR.

- [ ] **Step 2: (On approval) sync edited pages to dev Wiki.js**

Use the established sync path to `http://dev.blueledgers.com:3987/` and spot-check rendering of at least one edited page per pass.

- [ ] **Step 3: (On approval) push and open the PR**

```bash
git push -u origin docs/resync-react-stack-2026-06-18
gh pr create --base main --title "docs(resync): inventory wiki → React/Vite stack" \
  --body "Resync en/inventory + th/inventory to carmen-inventory-frontend-react. See .specs/resync-react-stack-2026-06-18.md.

🤖 Generated with [Claude Code](https://claude.com/claude-code)"
```

---

## Self-Review

**Spec coverage:**
- §1 scope (inventory only, EN+TH, exclusions) → Global Constraints + Task boundaries ✓
- §2 Pass 1 route diff → Task 1 (route list) + Task 2 (diff/fix/gap-log) ✓
- §3 Pass 2 arch deltas → Task 3 ✓
- §4 Pass 3 diff-driven behavior → Task 4 (signals) + Task 5 (flagged) + Task 6 (spot-check) ✓
- Conventions (frontmatter, EN+TH, ฿, sections) → Global Constraints ✓
- Tracking log → Task 1 creates, Tasks 2–6 fill ✓
- Finishing (dev sync + PR) → Task 7, gated on user approval ✓
- Non-goal "no new pages / no gap-fill" → enforced in Constraints + Task 2 Step 4 + Task 5 Step 2 ✓

**Placeholder scan:** No TBD/TODO in steps; every step has a concrete command or explicit edit instruction. The one conditional ("if no infra prose, skip") has a defined recorded outcome. ✓

**Type/name consistency:** `routes.txt` filename, log filename, branch name, section regex, and the three confirmed drift targets are identical across all tasks. ✓
