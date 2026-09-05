# Platform Book Full Re-sync — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the Platform book (`en/platform/`, `th/platform/`) in line with `carmen-platform` HEAD — verify 13 existing units, delete the module whose feature was removed from the product, add 16 new modules, rewrite the coverage checklist, and publish to the dev Wiki.js.

**Architecture:** Content-only repo; there is no build or test suite. Every task reads the current SPA source, edits Markdown, runs the frontmatter checker, and commits. Modules stay flat under `<locale>/platform/`; the SPA's eight nav groups are expressed on `platform.md` and in the Wiki.js nav tree. EN is written first and TH mirrored semantically in the same task, so the two locales can never drift apart between commits.

**Tech Stack:** Markdown + Wiki.js YAML frontmatter · Python 3.11 tooling in `scripts/` and `.specs/` · Wiki.js GraphQL API at `http://dev.blueledgers.com:3987/`

**Spec:** `.specs/2026-09-05-platform-resync-design.md` (commit `f8862d9`)

## Global Constraints

- Branch: `docs/resync-platform-2026-09-05` (already created). Never commit to `main`.
- Truth precedence: **implementation + e2e (`../carmen-platform-e2e/tests/`) > `../carmen/docs/` > memory or speculation.** A claim that cannot be traced to current source gets rewritten from source, not preserved.
- **Never modify `dateCreated` on an existing page.** Bump `date` to the current ISO 8601 timestamp on every page you edit. New pages get the same value for both.
- Frontmatter must carry all seven keys: `title`, `description`, `published: true`, `date`, `tags`, `editor: markdown`, `dateCreated`.
- Sub-page links use absolute-URL markdown — `[Display](/en/platform/<module>/<slug>)`. Pipe wikilinks (`[[a|b]]`) do not render in this Wiki.js.
- Currency in examples: Thai Baht (`฿`).
- Section numbering: `## 1. Title`, `### 1.1 Subtitle`.
- Per user preference, **no automated tests are written in this plan.** Static checks still run — the frontmatter checker on every touched page, and `pytest scripts/` when `scripts/` is modified.
- Every module landing page states the module's **permission key**, **feature-flag key**, and whether it is `superAdminOnly`, read from `../carmen-platform/src/components/nav/platformNav.ts` or `clusterAdminNav.ts`.
- Sub-page depth rule: landing always; `data-model` only when the module owns tables; `ui-screens` only when it has more than one screen; `permissions` only when it has more than one permission key or notable gating. No stub pages.
- Update `.specs/resync-platform-2026-09-05-progress.md` in the same commit as the module it describes.

**Frontmatter check** — `.specs/verify_frontmatter.py` takes exactly one path, so use this loop and require zero `FAIL` lines:

```bash
fail=0
while IFS= read -r f; do
  python3 .specs/verify_frontmatter.py "$f" || fail=1
done < <(git diff --name-only HEAD -- 'en/**/*.md' 'th/**/*.md'; git ls-files -o --exclude-standard -- 'en/**/*.md' 'th/**/*.md')
echo "frontmatter check exit: $fail"   # must print 0
```

**dateCreated guard** — run before every commit that touches existing pages; it must print nothing:

```bash
git diff -U0 -- 'en/**/*.md' 'th/**/*.md' | grep '^-dateCreated'
```

---

## Deviation from the spec — read before Task 1

The spec lists 17 new modules, counting `license-features` and `license-feature-groups` separately. Reading `../carmen-platform/src/pages/LicenseCatalog.tsx` during planning showed both routes render the **same component**, as two tabs of one screen (`TAB_PATH = { bundles: '/license-feature-groups', features: '/license-features' }`), with the page header deliberately held constant across tabs so readers see one place. Documenting them as two wiki modules would contradict the product's own information architecture.

This plan therefore creates **16 modules**, with a single `license-catalog` module covering both routes and their two tabs. If that is rejected, split Task 14 into two module tasks and update the spec's count.

---

## File Structure

| Path | Responsibility |
|------|----------------|
| `.specs/resync-platform-2026-09-05-progress.md` | Tracking log: per-module source map, status, claims fixed, e2e backing, visually-changed routes. Created in Task 1, appended by every later task. |
| `en/platform/<module>.md` + `en/platform/<module>/`, and the TH mirrors | Sibling landing file plus a folder of sub-pages — the shape every existing module uses. No `index.md`. |
| `en/platform.md`, `th/platform.md` | Book landing: eight nav-group sections with one card per module. Rebuilt in Task 29. |
| `scripts/migrate_books/platform_pages.yaml` | Declarative record of every page the book contains; input to the scaffolder. Extended in Task 12. |
| `scripts/nav-overrides.yaml` | `books:` block driving the Wiki.js nav rebuild. Updated in Task 31. |
| `.specs/platform-coverage-checklist.md` | Coverage tracker, rewritten in Task 30. |

---

### Task 1: Source map and tracking log

**Files:**
- Create: `.specs/resync-platform-2026-09-05-progress.md`

**Interfaces:**
- Produces: the per-module source map every later task reads to know which SPA files back its module, and the status table every later task appends to.

- [ ] **Step 1: Confirm the branch**

```bash
git rev-parse --abbrev-ref HEAD   # must print docs/resync-platform-2026-09-05
```

- [ ] **Step 2: Regenerate the route → component map**

```bash
cd ../carmen-platform && python3 - <<'PY'
import re, pathlib
s = pathlib.Path('src/App.tsx').read_text()
for m in re.finditer(r'path="([^"]+)"(.{0,400}?)(?:/>|</Route>)', s, re.S):
    comps = [c for c in re.findall(r'<([A-Z][A-Za-z0-9]*)', m.group(2))
             if c not in ('Route', 'Suspense', 'ProtectedRoute', 'Layout')]
    print(f"{m.group(1):45s} {comps[:4]}")
PY
```

- [ ] **Step 3: Write the tracking log**

Create `.specs/resync-platform-2026-09-05-progress.md` with this exact skeleton, then fill the source-map table from Step 2 plus `src/components/nav/platformNav.ts`, `src/components/nav/clusterAdminNav.ts`, `src/services/`, and `ls ../carmen-platform-e2e/tests/`:

```markdown
# Platform Re-sync 2026-09-05 — Progress Log

Spec: `.specs/2026-09-05-platform-resync-design.md`
Source HEAD: `<carmen-platform git rev-parse --short HEAD>` (<date>)
Branch: `docs/resync-platform-2026-09-05`

## Source map

| Module | Routes | Components | Service | Permission key | Feature key | e2e suite |
|--------|--------|-----------|---------|----------------|-------------|-----------|

## Status

| # | Module | Type | EN | TH | Claims fixed | e2e backing | Routes visually changed | Commit |
|---|--------|------|----|----|--------------|-------------|-------------------------|--------|
```

Known e2e coverage — `../carmen-platform-e2e/tests/` holds: `applications`, `auth`, `broadcast`, `business-units`, `changelog`, `clusters`, `dashboard`, `journeys`, `landing`, `news`, `permission-catalog`, `print-template-mapping`, `profile`, `report-templates`, `roles`, `super-admins`, `user-platform`, `users`. Every other module has **no e2e backing** and must be marked as such. (The `print-template-mapping` suite is stale in that repo — note it in the log; fixing it is out of scope here.)

Note in the log that `../carmen-platform` has no static permission-key catalog: per-menu keys come from `platformNav.ts`, and the full catalog is served to `PermissionCatalog.tsx` from the backend.

- [ ] **Step 4: Commit**

```bash
git add .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(resync): source map and tracking log for the platform re-sync

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

---

## Phase 1 — Verify the 13 existing units (Tasks 2–10)

Every task in this phase follows the same shape: read source, verify each checkable claim on the EN page, fix inline, bump `date`, mirror to TH, log, check, commit. The claims listed per task are the ones known from the design pass; they are a floor, not a ceiling — verify the whole page.

### Task 2: Verify `clusters`

**Files:**
- Modify: `en/platform/clusters/*.md`, `en/platform/clusters.md`, `th/platform/clusters/*.md`, `th/platform/clusters.md`
- Read: `../carmen-platform/src/pages/ClusterManagement.tsx`, `src/pages/ClusterEdit.tsx`, `src/pages/clusterManagement/`, `src/pages/clusterEdit/`, `../carmen-platform-e2e/tests/clusters/`

- [ ] **Step 1: Read the source**

Routes: `/clusters` → `ClusterManagement`; `/clusters/new` and `/clusters/:id/edit` → `ClusterEdit`. Nav: `permission: 'cluster.read'`, `feature: 'clusters'`, group `navGroup.organization`. `src/pages/clusterEdit/` saw 78 commits in the window — read it in full, not just the top-level component.

- [ ] **Step 2: Verify and fix every checkable claim on the EN pages**

Check: route paths, tab names and order, field labels, required/optional and read-only states, button labels, list columns and default sort, validation messages, permission keys, and any API request/response shape. Fix inline against source. Confirm the landing page states `cluster.read` / `clusters` / not `superAdminOnly`.

- [ ] **Step 3: Bump `date`, leave `dateCreated`**

Set `date` to the current ISO 8601 timestamp on each edited page. Then:

```bash
git diff -U0 -- 'en/**/*.md' 'th/**/*.md' | grep '^-dateCreated'   # must print nothing
```

- [ ] **Step 4: Mirror fixes to TH**

Apply the same corrections semantically to `th/platform/clusters*`. Do not re-translate untouched prose. Also scan the TH pages for structural drift against EN (missing or extra sections) and fix.

- [ ] **Step 5: Update the tracking log and run the frontmatter check**

Add the `clusters` row to the Status table. Run the frontmatter loop from Global Constraints; require exit 0.

- [ ] **Step 6: Commit**

```bash
git add en/platform/clusters* th/platform/clusters* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): verify clusters against carmen-platform HEAD

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 3: Verify `business-units`

**Files:**
- Modify: `en/platform/business-units/*.md`, `en/platform/business-units.md`, and the TH mirrors
- Read: `../carmen-platform/src/pages/BusinessUnitManagement.tsx`, `src/pages/BusinessUnitEdit.tsx`, `src/pages/businessUnitEdit/`, `../carmen-platform-e2e/tests/business-units/`

- [ ] **Step 1: Read the source**

Routes: `/business-units` → `BusinessUnitManagement`; `/business-units/new` and `/business-units/:id/edit` → `BusinessUnitEdit`. Nav: `permission: 'cluster.read'`, `feature: 'business_units'`. `src/pages/businessUnitEdit/` saw 98 commits — read the whole directory.

- [ ] **Step 2: Verify the four known changes plus everything else**

Confirm and document from source: (a) `code` is no longer entered by the user on create (PR #279) — find what generates it; (b) the Technical tab has a schema-name randomizer button (PR #280); (c) **Licenses is now its own tab, split out of the Users tab** (PR #276); (d) the User Licenses card has a New subscription button (PR #275). Then verify the rest of the page normally.

- [ ] **Step 3: Bump `date`, leave `dateCreated`**

Run the dateCreated guard; it must print nothing.

- [ ] **Step 4: Mirror fixes to TH**

- [ ] **Step 5: Cross-check against `users`**

The License content that moved out of the Users tab must not remain described under `users` — note in the tracking log that Task 4 removes it, so the two pages cannot both claim it.

- [ ] **Step 6: Update log, run the frontmatter check, commit**

```bash
git add en/platform/business-units* th/platform/business-units* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): verify business-units — code autogen, schema randomizer, Licenses tab split

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 4: Verify `users`

**Files:**
- Modify: `en/platform/users/*.md`, `en/platform/users.md`, and the TH mirrors
- Read: `../carmen-platform/src/pages/UserManagement.tsx`, `src/pages/UserEdit.tsx`, `src/pages/userManagement/`, `src/pages/userEdit/`, `../carmen-platform-e2e/tests/users/`

- [ ] **Step 1: Read the source**

Routes: `/users` → `UserManagement`; `/users/new` and `/users/:id/edit` → `UserEdit`. Nav: `permission: 'user.read'`, `feature: 'users'`.

- [ ] **Step 2: Remove the license content that moved to business-units**

Per PR #276 the Licenses surface is a business-unit tab. Delete or rewrite any `users` page section that still describes licensing as living under Users, and point readers to `/en/platform/business-units` instead.

- [ ] **Step 3: Verify the rest of the page against source**

- [ ] **Step 4: Bump `date` (guard `dateCreated`), mirror to TH**

- [ ] **Step 5: Update log, run the frontmatter check, commit**

```bash
git add en/platform/users* th/platform/users* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): verify users — licensing moved out to the business-unit Licenses tab

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 5: Verify `rbac` (including category permissions)

**Files:**
- Modify: `en/platform/rbac/*.md`, `en/platform/rbac.md`, and the TH mirrors
- Read: `../carmen-platform/src/pages/RoleManagement.tsx`, `src/pages/RoleEdit.tsx`, `src/pages/roleManagement/`, `src/pages/roleEdit/`, `src/pages/PermissionCatalog.tsx`, `src/components/nav/platformNav.ts`, `../carmen-platform-e2e/tests/roles/`, `../carmen-platform-e2e/tests/permission-catalog/`

- [ ] **Step 1: Read the source**

Routes: `/platform/roles` → `RoleManagement`; `/platform/roles/new` and `:id/edit` → `RoleEdit`; `/platform/category-permissions` → `PermissionCatalog` (**no nav entry** — reachable only by direct link or from another screen; say so on the page). Nav: `permission: 'platform_role.read'`, `feature: 'platform_roles'`.

- [ ] **Step 2: Document the permission ordering rule**

`platformNav.ts` derives `NAV_RESOURCE_ORDER` from the nav itself, and `resourceRank()` ranks a resource by first appearance; resources with no menu entry of their own (`rbac`, `license`) sort after every menu-backed one and keep catalog order among themselves. A role's permission list therefore reads top-to-bottom in the same order as the menu. Document this — it is the reason the list is ordered the way it is, and it is not guessable from the screen.

- [ ] **Step 3: Refresh the permission-key inventory**

Keys are not enumerated in a local constant; per-menu keys live in `platformNav.ts` and the full catalog comes from the backend into `PermissionCatalog.tsx`. Rebuild any key table from `platformNav.ts` plus the catalog page, and **remove the print-template-mapping key** — it was deleted from `src/utils/permissions.ts` by `de11377`.

- [ ] **Step 4: Document multi-BU role-permission seeding (PR #281)**

- [ ] **Step 5: Bump `date` (guard `dateCreated`), mirror to TH**

- [ ] **Step 6: Update log, run the frontmatter check, commit**

```bash
git add en/platform/rbac* th/platform/rbac* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): verify rbac — nav-derived permission order, multi-BU seeding, key inventory

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 6: Verify `applications`

**Files:**
- Modify: `en/platform/applications/*.md`, `en/platform/applications.md`, and the TH mirrors
- Read: `../carmen-platform/src/pages/ApplicationManagement.tsx`, `src/pages/ApplicationEdit.tsx`, `src/pages/applicationManagement/`, `src/pages/applicationEdit/`, `../carmen-platform-e2e/tests/applications/`

- [ ] **Step 1: Read the source**

Routes: `/applications` → `ApplicationManagement`; `/applications/new` and `:id/edit` → `ApplicationEdit`. Nav: `permission: 'application.read'`, `feature: 'applications'`, group `navGroup.platform`.

- [ ] **Step 2: Verify every checkable claim and fix inline**

The 2026-06-17 re-sync added an Application device field; confirm it still matches source and that nothing else drifted.

- [ ] **Step 3: Bump `date` (guard `dateCreated`), mirror to TH**

- [ ] **Step 4: Update log, run the frontmatter check, commit**

```bash
git add en/platform/applications* th/platform/applications* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): verify applications against carmen-platform HEAD

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 7: Verify `broadcasts`

**Files:**
- Modify: `en/platform/broadcasts/*.md`, `en/platform/broadcasts.md`, and the TH mirrors
- Read: `../carmen-platform/src/pages/BroadcastManagement.tsx`, `src/pages/BroadcastCompose.tsx`, `src/pages/BroadcastEdit.tsx`, `src/pages/broadcastManagement/`, `src/pages/broadcastCompose/`, `../carmen-platform-e2e/tests/broadcast/`

- [ ] **Step 1: Read the source**

Routes: `/broadcasts` → `BroadcastManagement`; `/broadcasts/new` → `BroadcastCompose`; `/broadcasts/:id/edit` → `BroadcastEdit` (note: **compose and edit are different components** — check the wiki does not describe them as one screen). Nav: `permission: 'broadcast.read'`, `feature: 'broadcasts'`. `broadcast.send` is a separate key found in `src/utils/permissions.ts`.

- [ ] **Step 2: Verify every checkable claim and fix inline**

- [ ] **Step 3: Bump `date` (guard `dateCreated`), mirror to TH**

- [ ] **Step 4: Update log, run the frontmatter check, commit**

```bash
git add en/platform/broadcasts* th/platform/broadcasts* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): verify broadcasts — compose vs edit, send permission

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 8: Verify `news`

**Files:**
- Modify: `en/platform/news/*.md`, `en/platform/news.md`, and the TH mirrors
- Read: `../carmen-platform/src/pages/NewsManagement.tsx`, `src/pages/NewsEdit.tsx`, `src/pages/newsManagement/`, `src/pages/newsEdit/`, `../carmen-platform-e2e/tests/news/`

- [ ] **Step 1: Read the source**

Routes: `/news` → `NewsManagement`; `/news/new` and `:id/edit` → `NewsEdit`. Nav: `permission: 'news.read'`, `feature: 'news'`. `NewsManagement.buildAdvance.test.ts` exists alongside the component — read it for the advance/scheduling behavior it pins.

- [ ] **Step 2: Verify every checkable claim and fix inline**

- [ ] **Step 3: Bump `date` (guard `dateCreated`), mirror to TH**

- [ ] **Step 4: Update log, run the frontmatter check, commit**

```bash
git add en/platform/news* th/platform/news* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): verify news against carmen-platform HEAD

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 9: Verify `report-templates`

**Files:**
- Modify: `en/platform/report-templates/*.md`, `en/platform/report-templates.md`, and the TH mirrors
- Read: `../carmen-platform/src/pages/ReportTemplateManagement.tsx`, `src/pages/ReportTemplateEdit.tsx`, `src/constants/reportGroups.ts`, `../carmen-platform-e2e/tests/report-templates/`

- [ ] **Step 1: Read the source**

Routes: `/report-templates` → `ReportTemplateManagement`; `/report-templates/new` and `:id/edit` → `ReportTemplateEdit`. Nav: `permission: 'report_template.read'`, `feature: 'report_templates'`.

- [ ] **Step 2: Document the form-mode behavior changes**

From source, confirm and write: `template_type` sits in Template Info as a required select (`9cfbf72`); Report Group is a code select in form mode (`9843bb0`); Standard is hidden and forced true in form mode (`5734758`); Business Unit Scope is read-only and cleared in form mode (`b513dee`); empty Template Type renders `-` in read-only view (`0240354`); list columns were restructured (`4a91abf`) and default sort is name A→Z (`a4d994c`). `FORM_REPORT_GROUPS` is a shared constant (`aa454d3`) and RFQ was replaced by RFP (`5f68253`) — check the wiki does not still say RFQ.

- [ ] **Step 3: Add the print-template-mapping succession note**

`template_type` plus the new Form Groups surface replaced the deleted print-template-mapping feature. State this and link to `/en/platform/report-form-groups` (created in Task 28).

- [ ] **Step 4: Bump `date` (guard `dateCreated`), mirror to TH**

- [ ] **Step 5: Update log, run the frontmatter check, commit**

```bash
git add en/platform/report-templates* th/platform/report-templates* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): verify report-templates — template_type, form-mode rules, RFP rename

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 10: Verify the five standalone pages

**Files:**
- Modify: `en/platform/sql-workbench.md`, `en/platform/dashboard.md`, `en/platform/landing.md`, `en/platform/profile.md`, `en/platform/changelog.md`, and the five TH mirrors
- Read: `../carmen-platform/src/pages/sqlWorkbench/`, `src/pages/dashboard/`, `src/pages/Dashboard.tsx`, `src/pages/Landing.tsx`, `src/pages/Profile.tsx`, `src/pages/Changelog.tsx`, `src/components/Layout.tsx`, `../carmen-platform-e2e/tests/{dashboard,landing,profile,changelog}/`

- [ ] **Step 1: Read the source**

Routes: `/sql-workbench` → `SqlWorkbench` (`permission: 'sql_workbench.read'`, `feature: 'sql_workbench'`, group `navGroup.database`); `/dashboard` → `Dashboard` (no permission, no feature — always visible); `/` → `Landing`; `/profile` → `Profile`; `/changelog` → `Changelog`. Note `/profile` is also mounted at `/cluster-admin/:clusterId/profile` with the same component — Task 15 covers that context.

- [ ] **Step 2: Verify each page and fix inline**

`src/components/Layout.tsx` changed 20 times in the window and `Breadcrumbs.tsx` lost its print-template-mapping entry — check the shell description on `dashboard.md` and `landing.md` still matches.

- [ ] **Step 3: Bump `date` (guard `dateCreated`), mirror all five to TH**

- [ ] **Step 4: Update log, run the frontmatter check, commit**

```bash
git add en/platform/{sql-workbench,dashboard,landing,profile,changelog}.md \
        th/platform/{sql-workbench,dashboard,landing,profile,changelog}.md \
        .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): verify the five standalone platform pages

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

---

## Phase 2 — Remove the deleted module (Task 11)

### Task 11: Remove `print-template-mapping`

**Files:**
- Delete: `en/platform/print-template-mapping/`, `en/platform/print-template-mapping.md`, `th/platform/print-template-mapping/`, `th/platform/print-template-mapping.md`
- Modify: `en/platform.md`, `th/platform.md`, `en/platform/changelog.md`, `th/platform/changelog.md`, `scripts/migrate_books/platform_pages.yaml`, `scripts/nav-overrides.yaml`

- [ ] **Step 1: Find every inbound reference before deleting**

```bash
grep -rn "print-template-mapping" en/ th/ scripts/ .specs/ --include='*.md' --include='*.yaml'
```

- [ ] **Step 2: Delete the module in both locales**

```bash
git rm -r en/platform/print-template-mapping en/platform/print-template-mapping.md \
          th/platform/print-template-mapping th/platform/print-template-mapping.md
```

- [ ] **Step 3: Remove every reference found in Step 1**

Drop its card from `en/platform.md` and `th/platform.md`, its page entries from `scripts/migrate_books/platform_pages.yaml`, and its nav entry from `scripts/nav-overrides.yaml` so the Task 31 rebuild cannot resurrect it. Re-run the Step 1 grep; only the changelog entry written in Step 4 and this plan's own mentions may remain.

- [ ] **Step 4: Record the removal in the changelog pages**

Add an entry to `en/platform/changelog.md` and its TH mirror: the Print Template Mapping screens were removed from the product on 2026-07-24 (`de11377`), and their role is now served by the `template_type` field on report templates plus Form Groups. Bump `date`, leave `dateCreated`.

- [ ] **Step 5: Update the log, run the frontmatter check, commit**

```bash
git add -A en/platform th/platform scripts/migrate_books/platform_pages.yaml \
           scripts/nav-overrides.yaml .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): remove print-template-mapping, deleted from the product 2026-07-24

The screens, service, routes, breadcrumb and permission key were deleted by
carmen-platform de11377. template_type on report templates plus Form Groups
now serve the same need.

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

---

## Phase 3 — Create the 16 new modules (Tasks 12–28)

### Task 12: Declare and scaffold all 16 new modules

**Files:**
- Modify: `scripts/migrate_books/platform_pages.yaml`
- Create: `en/platform/<module>.md` and its `<module>/` sub-pages, plus TH mirrors, for all 16 modules

**Interfaces:**
- Produces: scaffolded EN+TH files with valid frontmatter for every module Tasks 13–28 fill in. Those tasks assume their files already exist and only rewrite the body.

- [ ] **Step 1: Decide each module's sub-pages using the depth rule**

**Page shape — read this before writing YAML.** Every module in this book is a
sibling landing file plus a folder of sub-pages: `en/platform/clusters.md` next to
`en/platform/clusters/{data-model,ui-screens,permissions}.md`. **There is no
`index.md` anywhere in the book**, and Wiki.js serves `/en/platform/clusters` from
`clusters.md`. New modules use the same shape: `path: licenses.md` for the landing
and `path: licenses/data-model.md` for each sub-page. The `<module>/index.md` form
that appears in the YAML's existing entries is a shape the book abandoned — Step 1b
removes it.

Apply the rule from Global Constraints. Recommended shape, from the route map:

| Module | Pages |
|--------|-------|
| `licenses` | landing, data-model, ui-screens, permissions |
| `license-catalog` | landing, data-model, ui-screens |
| `cluster-admin` | landing, ui-screens, permissions |
| `platform-config` | landing, data-model |
| `email-settings` | landing, data-model |
| `user-platform` | landing, ui-screens, permissions |
| `super-admins` | landing |
| `feature-flags` | landing, data-model |
| `tenant-migrations` | landing, data-model |
| `tenant-imports` | landing, ui-screens |
| `usage-analytics` | landing |
| `activity-events` | landing, data-model |
| `platform-migrations` | landing |
| `database-pools` | landing, data-model, ui-screens |
| `cronjobs` | landing, data-model, ui-screens |
| `report-form-groups` | landing |

Adjust upward only if the source shows more real content; never add a page that would carry a single row.

- [ ] **Step 1b: Prune the stale entries from the YAML first**

`scripts/migrate_books/platform_pages.yaml` still describes the May 2026 scaffold.
Seven of its entries name files that do not exist, and running the scaffolder
against them would create junk in both locales — including resurrecting
`auth-roles/`, the module RBAC replaced:

```bash
grep -E '^\s+- path:' scripts/migrate_books/platform_pages.yaml | sed 's/.*path: //' \
  | while read p; do [ -f "en/platform/$p" ] || echo "MISSING en/platform/$p"; done
```

Expect exactly these seven: `index.md`, `clusters/index.md`,
`business-units/index.md`, `users/index.md`, `report-templates/index.md`,
`profile/index.md`, `auth-roles/index.md`. Delete all seven blocks. Re-run the
check; it must print nothing before you continue. (`users/lifecycle.md` and
`report-templates/xml-spec.md` exist on disk — keep them.)

- [ ] **Step 2: Add the page specs to the YAML**

Append one block per page to `scripts/migrate_books/platform_pages.yaml`, following the existing shape exactly:

```yaml
  - path: licenses.md
    title_en: Licenses
    title_th: ไลเซนส์
    description: License centre — subscriptions, seat purchases and per-BU quota across a cluster.
    tags: [book/platform, licenses]
    at_a_glance:
      - Where licensing lives and who may reach it
      - Subscriptions, seats and BU quota
      - How a cluster's licence state is read
    references:
      - "../carmen-platform/src/pages/LicenseCenter.tsx"
      - "../carmen-platform/src/pages/licenses/"
      - "../carmen-platform/src/components/nav/platformNav.ts"
    todo:
      - Fill from source in Task 13
```

- [ ] **Step 3: Run the scaffolder with an explicit timestamp**

```bash
python3 scripts/migrate_books/scaffold_platform.py \
  --config scripts/migrate_books/platform_pages.yaml \
  --today "$(date -u +%Y-%m-%dT%H:%M:%S.000Z)"
```

**`--today` is required.** Its default is a hard-coded `2026-05-19T00:00:00.000Z`, which would stamp every new page with a four-month-old creation date. The tool skips files that already exist, so this cannot overwrite the pages verified in Phase 1 — confirm by reading its `SKIP (exists)` lines.

- [ ] **Step 4: Run the tooling tests and the frontmatter check**

```bash
python3 -m pytest scripts/ -q
```

Then run the frontmatter loop from Global Constraints across the new files; require exit 0.

- [ ] **Step 5: Commit**

```bash
git add scripts/migrate_books/platform_pages.yaml en/platform th/platform
git commit -m "docs(platform): declare and scaffold 16 new modules (EN+TH skeletons)

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

---

Tasks 13–28 share one shape. For each: read the named source in full, replace the scaffold body with content written from that source, keep the `## N. Title` numbering, state permission key / feature key / `superAdminOnly` on the landing page, add the §7 sub-page list with absolute-URL links, mirror EN to TH, mark **no e2e backing** in the log unless a suite is named, run the frontmatter check, and commit.

### Task 13: Write `licenses`

**Files:**
- Modify: `en/platform/licenses.md`, `en/platform/licenses/{data-model,ui-screens,permissions}.md` and TH mirrors
- Read: `../carmen-platform/src/pages/licenses/`, `src/pages/LicenseCenter.tsx`, `src/pages/ClusterLicenseDetail.tsx`, `src/pages/SubscriptionForm.tsx`, `src/pages/LicensePurchaseForm.tsx`, `src/pages/subscriptionEdit/`, `src/services/expiryThresholdService.ts`

- [ ] **Step 1: Read the source**

Routes: `/licenses` → `LicenseCenter`; `/licenses/:clusterId` → `ClusterLicenseDetail`; `/licenses/subscriptions/{new,:id/edit}` → `SubscriptionForm`; `/licenses/seats/{new,:id/edit}` and `/licenses/bu-quota/{new,:id/edit}` → **the same `LicensePurchaseForm`** — document what differs between the seat and BU-quota modes. Nav: `permission: 'subscription.read'`, `feature: 'licenses'`, group `navGroup.licenseManagement`. This is the heaviest-changed area in the window (228 commits); read the whole `src/pages/licenses/` directory.

- [ ] **Step 2: Document the legacy `/subscriptions` redirects**

`/subscriptions` and `/subscriptions/new` render `Navigate`, and `/subscriptions/:id/edit` renders `SubscriptionEditRedirect`. Old links still work and land under `/licenses/...`; say so, and give `/licenses/subscriptions/...` as canonical.

- [ ] **Step 3: Document expiry thresholds**

`src/services/expiryThresholdService.ts` decides when a licence reads as expiring. Put the thresholds and their effect in `data-model.md` — this is the kind of rule a tester cannot infer from the screen.

- [ ] **Step 4: Write the four pages, then mirror to TH**

Include the licence feature tree, whose three-phase spec closed in `carmen-platform` on 2026-09-03 (`docs/license/`) — read those notes for intended behavior, but verify claims against code.

- [ ] **Step 5: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/licenses* th/platform/licenses* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add the licenses module — centre, subscriptions, seats, BU quota

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 14: Write `license-catalog`

**Files:**
- Modify: `en/platform/license-catalog.md`, `en/platform/license-catalog/{data-model,ui-screens}.md` and TH mirrors
- Read: `../carmen-platform/src/pages/LicenseCatalog.tsx`, `src/pages/licenseCatalog/`, `src/pages/licenseFeatures/`, `src/pages/LicenseFeatureGroupEdit.tsx`

- [ ] **Step 1: Read the source**

One screen, two tabs, each its own route: `/license-feature-groups` → the Bundles tab, `/license-features` → the Features tab, both rendering `LicenseCatalog` with a `tab` prop. `/license-feature-groups/{new,:id/edit}` → `LicenseFeatureGroupEdit`. Nav keys differ per tab: `license_feature_group.read` / `feature: 'license_feature_groups'` and `license_feature.read` / `feature: 'license_features'`.

- [ ] **Step 2: Document the tab behavior exactly**

From `LicenseCatalog.tsx`: switching tabs navigates, which remounts the panel and refetches rather than caching; the page header name is held constant across tabs by design while only the subtitle changes; and the tab strip is hidden when the reader can reach only one tab. Each of these is a deliberate decision a tester would otherwise file as a bug.

- [ ] **Step 3: Write the three pages, then mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/license-catalog* th/platform/license-catalog* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add license-catalog — bundles and features as one screen

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 15: Write `cluster-admin`

**Files:**
- Modify: `en/platform/cluster-admin.md`, `en/platform/cluster-admin/{ui-screens,permissions}.md` and TH mirrors
- Read: `../carmen-platform/src/pages/clusterAdmin/`, `src/components/nav/clusterAdminNav.ts`, and the `ClusterAdminRoute` and `AuthedRoute` guards in `src/App.tsx`

- [ ] **Step 1: Read the source**

Routes: `/cluster-admin` → `AuthedRoute` + `ClusterAdminEntry`; then under `ClusterAdminRoute`: `/cluster-admin/:clusterId/cluster` → `ClusterProfile`, `/business-units` → `ClusterAdminBusinessUnitList`, `/business-units/:buId/edit` → `ClusterAdminBusinessUnitForm`, `/users` → `ClusterAdminUsers`, `/licenses` → `ClusterAdminLicenses`, `/profile` → the shared `Profile`. 161 commits in the window — read the whole directory.

- [ ] **Step 2: Lead with what makes this a separate persona**

State plainly: this is a **second navigation**, not the platform console. Every path carries the cluster id so the sidebar cannot navigate out of its cluster; there is **no permission filtering** on the nav because clearing `ClusterAdminRoute` is the whole check; and the feature keys are separate from the platform ones that share menu labels — `cluster_admin_cluster`, `cluster_admin_business_units`, `cluster_admin_licenses`, `cluster_admin_users`. A reader who assumes platform-side permission keys apply here will be wrong.

- [ ] **Step 3: Contrast each screen with its platform-side twin**

For business-units, users and licenses, say what a cluster admin can do that differs from the platform screens documented in Tasks 3, 4 and 13, and link across.

- [ ] **Step 4: Write the three pages, then mirror to TH**

- [ ] **Step 5: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/cluster-admin* th/platform/cluster-admin* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add cluster-admin — the second console and its route guard

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 16: Write `platform-config`

**Files:**
- Modify: `en/platform/platform-config.md`, `en/platform/platform-config/data-model.md` and TH mirrors
- Read: `../carmen-platform/src/pages/PlatformConfigManagement.tsx`, `src/pages/platformConfig/`

- [ ] **Step 1: Read the source**

Route: `/platform/configs` → `PlatformConfigManagement`. Nav: `permission: 'platform_config.read'`, `feature: 'platform_config'`, group `navGroup.platform`. 39 commits in the window.

- [ ] **Step 2: Write both pages from source**

Enumerate each config key, its type, its default, and what changes when it is edited. A config page without the effect of each key is not usable.

- [ ] **Step 3: Mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/platform-config* th/platform/platform-config* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add platform-config

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 17: Write `email-settings`

**Files:**
- Modify: `en/platform/email-settings.md`, `en/platform/email-settings/data-model.md` and TH mirrors
- Read: `../carmen-platform/src/pages/EmailSettingManagement.tsx`, `src/pages/emailSettings/`, `src/constants/emailFlows.ts`

- [ ] **Step 1: Read the source**

Route: `/platform/email-settings` → `EmailSettingManagement`. Nav: `permission: 'email_setting.read'`, `feature: 'email_settings'`. 36 commits in the window.

- [ ] **Step 2: Document the email flows**

`src/constants/emailFlows.ts` enumerates the flows; list each flow, what triggers it, and which setting controls it.

- [ ] **Step 3: Write both pages, then mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/email-settings* th/platform/email-settings* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add email-settings and the email flow catalogue

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 18: Write `user-platform`

**Files:**
- Modify: `en/platform/user-platform.md`, `en/platform/user-platform/{ui-screens,permissions}.md` and TH mirrors
- Read: `../carmen-platform/src/pages/UserPlatformManagement.tsx`, `src/pages/UserPlatformEdit.tsx`, `src/pages/userPlatformManagement/`, `src/pages/userPlatformEdit/`, `../carmen-platform-e2e/tests/user-platform/`

- [ ] **Step 1: Read the source**

Routes: `/platform/user-platform` → `UserPlatformManagement`; `/platform/user-platform/:userId` → `UserPlatformEdit` (note the param is `:userId` and there is **no `/edit` suffix**). Nav: `permission: 'user_platform.read'`, `feature: 'user_platform'`.

- [ ] **Step 2: Distinguish it from `users`**

Say explicitly how a platform user differs from the tenant users documented in Task 4, and link between the two modules.

- [ ] **Step 3: Write the three pages, then mirror to TH**

- [ ] **Step 4: Update the log (e2e: `tests/user-platform/`), run the frontmatter check, commit**

```bash
git add en/platform/user-platform* th/platform/user-platform* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add user-platform

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 19: Write `super-admins`

**Files:**
- Modify: `en/platform/super-admins.md` and TH mirror
- Read: `../carmen-platform/src/pages/SuperAdminManagement.tsx`, `../carmen-platform-e2e/tests/super-admins/`

- [ ] **Step 1: Read the source**

Route: `/platform/super-admins` → `SuperAdminManagement`. Nav: **`superAdminOnly: true` with no permission key**, `feature: 'super_admins'`, and `dividerBefore: true` because it changes what other people can reach. Lead the page with that gating.

- [ ] **Step 2: Write the landing page, then mirror to TH**

One page only, per the depth rule — a permissions page here would hold a single row.

- [ ] **Step 3: Update the log (e2e: `tests/super-admins/`), run the frontmatter check, commit**

```bash
git add en/platform/super-admins* th/platform/super-admins* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add super-admins

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 20: Write `feature-flags`

**Files:**
- Modify: `en/platform/feature-flags.md`, `en/platform/feature-flags/data-model.md` and TH mirrors
- Read: `../carmen-platform/src/pages/FeatureFlagManagement.tsx`, `src/constants/featureFlags.ts`, `src/components/nav/platformNav.ts`, `src/components/nav/clusterAdminNav.ts`

- [ ] **Step 1: Read the source**

Route: `/platform/features` → `FeatureFlagManagement`. Nav: `permission: 'feature_flag.manage'` and **deliberately no `feature` key** — the source comment says a switch that could hide itself could never be restored from the UI. Document that reasoning; it explains why this one menu entry cannot be turned off.

- [ ] **Step 2: Document the three flag states and their nav effect**

From `buildPlatformNav`: `hide` removes the row entirely; `inactive` keeps the row in place and marks it `comingSoon`; anything else shows it normally. `inactive` deliberately keeps its position because the sidebar groups by **consecutive runs of the same `groupKey`**, so removing a row mid-group would split one heading into two. List every flag key from `src/constants/featureFlags.ts` with the menu it controls, including the separate `cluster_admin_*` keys.

- [ ] **Step 3: Write both pages, then mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/feature-flags* th/platform/feature-flags* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add feature-flags — hide vs inactive and why the page is ungated

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 21: Write `tenant-migrations`

**Files:**
- Modify: `en/platform/tenant-migrations.md`, `en/platform/tenant-migrations/data-model.md` and TH mirrors
- Read: `../carmen-platform/src/pages/TenantMigrationManagement.tsx`, `src/pages/tenantMigration/`

- [ ] **Step 1: Read the source**

Route: `/tenant-migrations` → `TenantMigrationManagement`. Nav: `permission: 'cluster.read'` (shared with Clusters and Business Units — say so, since the key does not name this screen), `feature: 'tenant_migrations'`, group `navGroup.organization`.

- [ ] **Step 2: Write both pages from source**

Cover the migration states, what advances one, and what a failed migration leaves behind.

- [ ] **Step 3: Mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/tenant-migrations* th/platform/tenant-migrations* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add tenant-migrations

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 22: Write `tenant-imports`

**Files:**
- Modify: `en/platform/tenant-imports.md`, `en/platform/tenant-imports/ui-screens.md` and TH mirrors
- Read: `../carmen-platform/src/pages/TenantImportWizard.tsx`, `src/pages/tenantImport/`

- [ ] **Step 1: Read the source**

Route: `/tenant-imports` → `TenantImportWizard`. Nav label is **Data Import** while the route says tenant-imports — give both names so search finds the page. Nav: `permission: 'data_import.manage'` (a `manage` key, not `read` — this menu is hidden from read-only admins), `feature: 'tenant_imports'`. 36 commits in the window.

- [ ] **Step 2: Document the wizard step by step**

For each step: what it asks for, what it validates, what happens on failure, and whether the step can be revisited.

- [ ] **Step 3: Write both pages, then mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/tenant-imports* th/platform/tenant-imports* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add tenant-imports (Data Import wizard)

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 23: Write `usage-analytics`

**Files:**
- Modify: `en/platform/usage-analytics.md` and TH mirror
- Read: `../carmen-platform/src/pages/UsageAnalytics.tsx`, `src/pages/usageAnalytics/`

- [ ] **Step 1: Read the source**

Route: `/analytics` → `UsageAnalytics` (**folder slug is `usage-analytics`, route is `/analytics`** — state both). Nav: `permission: 'activity_event.read'`, `feature: 'usage_analytics'`, group `navGroup.analytics`.

- [ ] **Step 2: Write the landing page**

Define each metric shown, its source, and its time window. A metric without its definition invites two readers to disagree about the same number.

- [ ] **Step 3: Mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/usage-analytics* th/platform/usage-analytics* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add usage-analytics

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 24: Write `activity-events`

**Files:**
- Modify: `en/platform/activity-events.md`, `en/platform/activity-events/data-model.md` and TH mirrors
- Read: `../carmen-platform/src/pages/ActivityEventManagement.tsx`, `src/pages/activityEvents/`

- [ ] **Step 1: Read the source**

Route: `/activity-events` → `ActivityEventManagement`. Nav: `permission: 'activity_event.detail'` — **a different key from the `activity_event.read` that gates Usage Analytics**, so a reader can hold one and not the other. Say so on both pages.

- [ ] **Step 2: Write both pages**

`data-model.md` documents the event record: its fields, which are always present, and how long events are kept.

- [ ] **Step 3: Mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/activity-events* th/platform/activity-events* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add activity-events

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 25: Write `platform-migrations`

**Files:**
- Modify: `en/platform/platform-migrations.md` and TH mirror
- Read: `../carmen-platform/src/pages/PlatformMigrationManagement.tsx`, `src/pages/platformMigration/`

- [ ] **Step 1: Read the source**

Route: `/platform/migrations` → `PlatformMigrationManagement`. Nav: **`superAdminOnly: true`, no permission key**, `feature: 'platform_migrations'`, group `navGroup.database`. PR #281 added multi-BU selection when seeding role permissions — document it here and cross-link to `rbac`.

- [ ] **Step 2: Write the landing page, then mirror to TH**

Say what each migration does and what it is safe to re-run, since this screen changes data for everyone.

- [ ] **Step 3: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/platform-migrations* th/platform/platform-migrations* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add platform-migrations including multi-BU permission seeding

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 26: Write `database-pools`

**Files:**
- Modify: `en/platform/database-pools.md`, `en/platform/database-pools/{data-model,ui-screens}.md` and TH mirrors
- Read: `../carmen-platform/src/pages/DatabasePoolManagement.tsx`, `src/pages/DatabasePoolEdit.tsx`

- [ ] **Step 1: Read the source**

Routes: `/platform/database-pools` → `DatabasePoolManagement`; `/platform/database-pools/new` and `:id/edit` → `DatabasePoolEdit`. Nav: `permission: 'database_pool.read'`, `feature: 'database_pools'`, group `navGroup.database`.

- [ ] **Step 2: Write the three pages, then mirror to TH**

Cover each pool field, and the relationship between a pool and the business-unit schema names that Task 3 documents.

- [ ] **Step 3: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/database-pools* th/platform/database-pools* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add database-pools

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 27: Write `cronjobs`

**Files:**
- Modify: `en/platform/cronjobs.md`, `en/platform/cronjobs/{data-model,ui-screens}.md` and TH mirrors
- Read: `../carmen-platform/src/pages/cronjobs/`, and `../micro-cronjobs/` for what the jobs actually do

- [ ] **Step 1: Read the source**

Routes: `/cronjobs` → `CronJobManagement`; `/cronjobs/new` and `:id/edit` → `CronJobEdit`. Nav: `permission: 'cronjob.read'`, `feature: 'cronjobs'`, and its own group `navGroup.scheduling` — the source comment says scheduled work is not system configuration, which is why it is not folded into Platform.

- [ ] **Step 2: Connect the screen to the worker**

The SPA schedules; `../micro-cronjobs/` runs. Document which jobs exist, their schedule format, and where a failed run is visible.

- [ ] **Step 3: Write the three pages, then mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/cronjobs* th/platform/cronjobs* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add cronjobs

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 28: Write `report-form-groups`

**Files:**
- Modify: `en/platform/report-form-groups.md` and TH mirror
- Read: `../carmen-platform/src/pages/ReportFormGroupManagement.tsx`, `src/pages/reportFormGroups/`, `src/constants/reportGroups.ts`

- [ ] **Step 1: Read the source**

Route: `/report-form-groups` → `ReportFormGroupManagement`. Nav: `permission: 'report_template.read'` — **shared with Report Templates**, so anyone who can see one sees the other; `feature: 'report_form_groups'`, group `navGroup.content`.

- [ ] **Step 2: Document the succession from print template mapping**

This surface plus `template_type` replaced the feature removed in Task 11. Cover `FORM_REPORT_GROUPS` (`aa454d3`), the group default exposed by `cd4fc5d`, the `GroupCard` display (`ea699bc`), and the Add action that pre-fills a new template (`2a73a4d`). Link to `/en/platform/report-templates`.

- [ ] **Step 3: Write the landing page, then mirror to TH**

- [ ] **Step 4: Update the log (no e2e backing), run the frontmatter check, commit**

```bash
git add en/platform/report-form-groups* th/platform/report-form-groups* .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): add report-form-groups, successor to print template mapping

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

---

## Phase 4 — Book landing and coverage (Tasks 29–30)

### Task 29: Rebuild the book landing pages

**Files:**
- Modify: `en/platform.md`, `th/platform.md`

- [ ] **Step 1: Rebuild the module list in eight nav-group sections**

Use the SPA's own grouping and order from `platformNav.ts`, so the landing page reads in the same order as the sidebar: Dashboard, then Organization (`clusters`, `business-units`, `tenant-migrations`, `tenant-imports`, `users`), License Management (`licenses`, `license-catalog`), Content (`report-templates`, `report-form-groups`, `news`, `broadcasts`), Analytics (`usage-analytics`, `activity-events`), Scheduling (`cronjobs`), Platform (`platform-config`, `email-settings`, `applications`, `rbac`, `user-platform`, `super-admins`, `feature-flags`), Database (`platform-migrations`, `sql-workbench`, `database-pools`). Add a final section for the `cluster-admin` console, described as a separate persona rather than a ninth menu group.

Every link is absolute-URL markdown: `[Licenses](/en/platform/licenses)`.

- [ ] **Step 2: Verify every link resolves**

```bash
python3 - <<'PY'
import re, pathlib
bad = []
for md in [pathlib.Path('en/platform.md'), pathlib.Path('th/platform.md')]:
    for link in re.findall(r'\]\((/(?:en|th)/[^)]+)\)', md.read_text()):
        rel = link.lstrip('/')
        if not pathlib.Path(rel + '.md').exists():   # no index.md shape in this book
            bad.append(f"{md}: {link}")
print("\n".join(bad) if bad else "all links resolve")
PY
```

- [ ] **Step 3: Bump `date` on both pages (guard `dateCreated`), run the frontmatter check, commit**

```bash
git add en/platform.md th/platform.md
git commit -m "docs(platform): rebuild the book landing around the SPA's eight nav groups

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 30: Rewrite the coverage checklist

**Files:**
- Modify: `.specs/platform-coverage-checklist.md`

- [ ] **Step 1: Record the source HEAD the count is measured against**

```bash
cd ../carmen-platform && git rev-parse --short HEAD && git log -1 --format=%ci
```

- [ ] **Step 2: Rewrite the summary and rows**

Replace the "as of 2026-06-11 … 86 sub-processes … 100%" summary, which measures a June snapshot of the SPA and is misleading today. Enumerate sub-processes for every unit the book now holds — 24 folder modules (8 kept + 16 new) and 5 standalone pages — keeping the existing DM/UI/PERM axes and the ✅/🟡/⬜ symbols. Remove the `print-template-mapping` rows. State the HEAD from Step 1 in the summary heading.

- [ ] **Step 3: Reconcile the numbers against the tree**

```bash
find en/platform -name '*.md' | wc -l
find th/platform -name '*.md' | wc -l   # must match EN
```

The checklist's module list must match the folders that exist; no row may name a module with no pages, and no module may be missing a row.

- [ ] **Step 4: Commit**

```bash
git add .specs/platform-coverage-checklist.md
git commit -m "docs(specs): rewrite the platform coverage checklist against current SPA HEAD

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

---

## Phase 5 — Publish (Tasks 31–32)

### Task 31: Push pages and rebuild the Wiki.js nav

**Files:**
- Modify: `scripts/nav-overrides.yaml`

- [ ] **Step 1: Update the `books:` block**

Add the 16 new modules with a `label_th:` for each, and confirm `print-template-mapping` is gone (Task 11 removed it). Order the entries to match the landing page from Task 29.

- [ ] **Step 2: Run the tooling tests**

```bash
python3 -m pytest scripts/ -q
```

- [ ] **Step 3: Push the changed and new pages**

```bash
source .venv/bin/activate
set -a; source .env; set +a
git diff --name-only main...HEAD -- 'en/**/*.md' 'th/**/*.md' | xargs python3 scripts/push_pages.py
```

Retry a failed page once; if it fails again, record it in the tracking log and continue.

- [ ] **Step 4: Preview the nav rebuild and read every line**

```bash
python3 scripts/sync_nav.py --mode=build --dry-run --verbose
```

Build mode rebuilds the whole tree from the YAML, so a stale `nav-overrides.yaml` would delete live nav entries. **Do not apply on an unread diff.** Any `⚠ … [fallback]` line means a TH label could not be resolved — fix the cause and re-run; the dry run must end with no fallback lines.

- [ ] **Step 5: Apply**

```bash
python3 scripts/sync_nav.py --mode=build
```

- [ ] **Step 6: Commit**

```bash
git add scripts/nav-overrides.yaml .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(platform): nav entries for the 16 new modules; publish to dev Wiki.js

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
```

### Task 32: Final verification and pull request

**Files:**
- Modify: `.specs/resync-platform-2026-09-05-progress.md`

- [ ] **Step 1: Frontmatter and dateCreated across the whole branch**

```bash
fail=0
while IFS= read -r f; do
  python3 .specs/verify_frontmatter.py "$f" || fail=1
done < <(git diff --name-only main...HEAD -- 'en/**/*.md' 'th/**/*.md')
echo "frontmatter exit: $fail"                                    # must be 0
git diff main...HEAD -- 'en/**/*.md' 'th/**/*.md' | grep '^-dateCreated'   # must print nothing
```

- [ ] **Step 2: Locale parity and dead links**

```bash
diff <(cd en/platform && find . -name '*.md' | sort) <(cd th/platform && find . -name '*.md' | sort)
grep -rn "print-template-mapping" en/ th/ scripts/ --include='*.md' --include='*.yaml'
```

The `diff` must print nothing. The `grep` may match only the changelog entry from Task 11.

Then run the link resolver from Task 29 Step 2 across every platform page rather than just the two landings.

- [ ] **Step 3: Two-way nav check**

```bash
cd ../carmen-platform && grep -oE "path: '[^']+'" src/components/nav/platformNav.ts src/components/nav/clusterAdminNav.ts
```

Every nav entry must map to a wiki module, and every wiki module to a backing route. Record both directions in the tracking log.

- [ ] **Step 4: Spot-check rendering**

Open one page per nav group on `http://dev.blueledgers.com:3987/`, in both `/en/` and `/th/`. Confirm the page renders, its sub-page links work, and it appears in the sidebar under the right group.

- [ ] **Step 5: Close the tracking log**

Fill in the final row counts, list any page that failed to push, and list the follow-up work: the platform screenshot round, and the platform folder ids still missing from `folder_id()` in `scripts/upload_assets.sh`.

- [ ] **Step 6: Open the pull request**

```bash
git add .specs/resync-platform-2026-09-05-progress.md
git commit -m "docs(resync): close the platform re-sync tracking log

Claude-Session: https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U"
git push -u origin docs/resync-platform-2026-09-05
gh pr create --base main --title "docs: Platform book full re-sync (2026-09-05)" --body "$(cat <<'EOF'
Re-syncs the Platform book to carmen-platform HEAD after 972 commits.

- Verified the 13 existing units against current source
- Removed print-template-mapping (deleted from the product by de11377, 2026-07-24)
- Added 16 modules: licenses, license-catalog, cluster-admin, platform-config,
  email-settings, user-platform, super-admins, feature-flags, tenant-migrations,
  tenant-imports, usage-analytics, activity-events, platform-migrations,
  database-pools, cronjobs, report-form-groups
- Rebuilt the book landing around the SPA's eight nav groups
- Rewrote the coverage checklist against current SPA HEAD
- Published pages and nav to the dev Wiki.js

Screenshots are out of scope; the platform capture pipeline does not exist yet.

Spec: `.specs/2026-09-05-platform-resync-design.md`
Log: `.specs/resync-platform-2026-09-05-progress.md`

https://claude.ai/code/session_01368ie91bMhnxN3muJYUm9U
EOF
)"
```

---

## Self-review notes

- **Spec coverage:** Phase 0 → Task 1; Phase 1 → Tasks 2–10; Phase 2 → Task 11; Phase 3 → Tasks 12–28 plus the landing rebuild in Task 29; Phase 4 → Task 30; Phase 5 → Tasks 31–32. All seven definition-of-done items are checked in Task 32 except the coverage-number reconciliation, which is Task 30 Step 3, and per-group rendering, which is Task 32 Step 4.
- **Deviation:** 16 modules rather than the spec's 17 — `license-features` and `license-feature-groups` are one screen, as documented at the top of this plan.
- **Deferred by decision:** screenshots, and the platform entries missing from `folder_id()` in `scripts/upload_assets.sh`.
