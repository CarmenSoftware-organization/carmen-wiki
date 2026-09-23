# Screenshots for Every Screen Page, Both Books — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **User preference (overrides TDD):** do NOT write new `*.test.ts` / `*.spec.ts` / `test_*.py` files and skip any "write failing test" step. Static checks (type-check, lint) and the existing test suites still run. Manual verification steps (dry-runs, curl, looking at PNGs) are NOT skipped.

**Goal:** Capture a current screenshot for every wiki page that documents a real screen (Inventory + Platform, EN + TH) with a repeatable pipeline, and publish it to the dev Wiki.js.

**Architecture:** Each e2e repo owns a Playwright capture project whose manifest names the wiki target file directly (`wikiTarget` / `targets`), so PNGs land in `carmen-wiki/assets/screenshots/<book>/<module>/<slug>.png` with no remap. A convention-driven Python script in `carmen-wiki` embeds each PNG into the matching EN and TH page; a GraphQL-aware uploader pushes PNGs into the Wiki.js Asset Manager.

**Tech Stack:** Playwright + Bun + TypeScript (both e2e repos), Python 3.11 (`carmen-wiki/scripts`, `.venv`), Wiki.js 2 GraphQL + `/u` upload endpoint.

**Spec:** `docs/superpowers/specs/2026-09-23-screenshots-all-books-design.md`

## Global Constraints

- Branch in every repo: `docs/screenshots-all-books`, cut from `main`.
- Image path on disk: `assets/screenshots/<book>/<module>/<slug>.png`; landing = `<module>/index.png`; variant = `<slug>-<variant>.png`.
- Markdown URL: Inventory `/screenshots/<module>/<file>.png` (unchanged); Platform `/screenshots/platform/<module>/<file>.png`.
- Never `fullPage: true`; viewport 1440×1600 (Inventory, existing) / 1440×900 (Platform); 60 s hard timeout per shot.
- Out of scope pages: `*data-model*`, `*business-rules*`, `*test-scenarios*`, `*user-flow*`, `*permissions*`, plus `inventory/costing`, `inventory/costing/calculation-methods`, `inventory/general-ledger/gl-posting`, `inventory/system-config/doc-version`, `platform/users/lifecycle`, `platform/report-templates/xml-spec`.
- TH pages embed the same image as EN; TH alt text uses the TH page title.
- Frontmatter: update `date` on changed pages only; never touch `dateCreated`.
- No credentials in code or commits; capture users come from each e2e repo's gitignored `.env`.
- Dev wiki: `http://dev.blueledgers.com:3987`; API token in `carmen-wiki/scripts/.env`.
- Merge order: both e2e PRs first, `carmen-wiki` PR last.

## Review Focus

1. **Running the embed twice** — the second run must insert nothing (URL already present check). Verified in Task 7 Step 4.
2. **A page with no `> **At a Glance**` block, or a TH mirror missing for an EN page** — insert before `## 1.` / after H1; a missing TH page is reported, not crashed on. Verified in Task 7 Step 3.
3. **A route that redirects to `/403`, `/login` or a not-found page** — the shot must be skipped with a reason, never saved as the page's screenshot. Platform capture checks the final URL (Task 4); every captured PNG is eyeballed in Tasks 3 and 5.
4. **Variant vs. exact page name clash** (`credit-note-detail.png` next to a page `credit-note.md`) — exact page match wins, then longest-prefix page. Verified in Task 7 Step 3 dry-run output.
5. **Stray files in asset folders** (route-output leftovers, `--role` suffixed shots) — must not be embedded; the dry-run lists them as unmatched/skipped. Verified in Task 7 Step 3.

---

## File Structure

| Repo | File | Responsibility |
|------|------|----------------|
| `carmen-inventory-frontend-e2e` | `tests/wiki-screenshots/types.ts` (modify) | `ShotSpec.wikiTarget` field |
| | `tests/wiki-screenshots/shot-path.ts` (modify) | `wikiOutputs()` — resolve wiki target files |
| | `tests/wiki-screenshots/capture.spec.ts` (modify) | copy each baseline shot to its wiki targets; `WIKI_CAPTURE_WIKI_ONLY` filter |
| | `tests/wiki-screenshots/manifest.ts` (modify) | new shots (§3.1) + `wikiTarget` on existing shots |
| `carmen-platform-e2e` | `tests/wiki-screenshots/types.ts` (create) | `ShotSpec` for Platform |
| | `tests/wiki-screenshots/manifest.ts` (create) | §3.2 mapping |
| | `tests/wiki-screenshots/capture.spec.ts` (create) | capture loop |
| | `playwright.config.ts`, `package.json`, `.gitignore` (modify) | `wiki-screenshots` project + `wiki:capture` script |
| `carmen-wiki` | `scripts/embed_screenshots.py` (create) | convention-based embed into EN+TH pages |
| | `scripts/upload_assets.py` (create), `scripts/upload_assets.sh` (modify → wrapper) | folder-resolving upload for both books |
| | `assets/screenshots/**`, `en/**`, `th/**` | captured PNGs and embedded pages |

---

### Task 0: Environment preflight (all repos)

**Files:** none changed.

- [ ] **Step 1: Branch the two e2e repos from an up-to-date main**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize
for r in carmen-inventory-frontend-e2e carmen-platform-e2e; do
  git -C $r checkout main && git -C $r pull --ff-only && git -C $r checkout -b docs/screenshots-all-books
done
git -C carmen-wiki branch --show-current   # already docs/screenshots-all-books (spec + plan commits)
```

- [ ] **Step 2: Confirm both frontends and a backend are reachable**

```bash
for u in http://localhost:3000 http://localhost:3304 https://dev.blueledgers.com:4001/api http://localhost:4000/api; do
  printf "%s -> %s\n" $u "$(curl -sk -o /dev/null -w '%{http_code}' --max-time 6 $u)"; done
```
Expected: `:3000` and `:3304` → 200; at least one backend answers (any HTTP code, not `000`). If the backend the frontends use answers `000`, stop and tell the user which `.env` to change — do not edit env files that hold credentials yourself.

- [ ] **Step 3: Confirm capture users are configured (names only, never print passwords)**

```bash
grep -E '^(WIKI_CAPTURE_EMAIL|E2E_BASE_URL)=' carmen-inventory-frontend-e2e/.env.local carmen-inventory-frontend-e2e/.env 2>/dev/null
grep -E '^(TEST_USER_EMAIL|E2E_BASE_URL|E2E_NO_WEBSERVER)=' carmen-platform-e2e/.env
```
Expected: Inventory has a data-rich capture user (the zebra tenant admin, passed as `WIKI_CAPTURE_EMAIL` at run time); Platform `TEST_USER_EMAIL` is a super-admin. If either is missing, ask the user to add it.

---

### Task 1: Inventory — `wikiTarget` support in the capture pipeline

**Repo:** `carmen-inventory-frontend-e2e`

**Files:**
- Modify: `tests/wiki-screenshots/types.ts` (the `ShotSpec` type)
- Modify: `tests/wiki-screenshots/shot-path.ts` (append a function)
- Modify: `tests/wiki-screenshots/capture.spec.ts` (`CaptureJob`, `planJobs`, `planSingleUserJobs`, job loop, shot filter)

**Interfaces:**
- Produces: `ShotSpec.wikiTarget?: string | string[]` — `"<module>/<file-stem>"` relative to `WIKI_ASSETS_DIR`, no extension.
- Produces: `wikiOutputs(assetsDir: string, spec: ShotSpec): string[]` in `shot-path.ts`.
- Produces: env `WIKI_CAPTURE_WIKI_ONLY=1` → capture only shots that have a `wikiTarget`.

- [ ] **Step 1: Add the field to `ShotSpec`** — in `types.ts`, directly after the `interaction?: "add-dialog";` line add:

```ts
  /**
   * Wiki file(s) this shot also feeds, as "<module>/<file-stem>" relative to
   * WIKI_ASSETS_DIR (no ".png"). Written only for the baseline role (or the
   * WIKI_CAPTURE_EMAIL override user) so the wiki's curated images refresh in
   * the same run as the route-derived catalog. Omit for catalog-only shots.
   */
  wikiTarget?: string | string[];
```

- [ ] **Step 2: Add `wikiOutputs` to `shot-path.ts`** — append:

```ts
/** Absolute wiki target files for a spec; [] when the spec has no wikiTarget. Pure. */
export function wikiOutputs(assetsDir: string, spec: ShotSpec): string[] {
  const t = spec.wikiTarget;
  if (!t) return [];
  return (Array.isArray(t) ? t : [t]).map((stem) => join(assetsDir, `${stem}.png`));
}
```

- [ ] **Step 3: Carry copies on each job** — in `capture.spec.ts`:

Change the imports:
```ts
import { copyFileSync, mkdirSync, writeFileSync } from "node:fs";
import { resolvePath, outputFile, wikiOutputs } from "./shot-path";
```

Change the job type:
```ts
/** One planned screenshot: a spec shot as a specific role, to a specific file, plus wiki copies. */
type CaptureJob = { spec: ShotSpec; role: string; out: string; copies: string[] };
```

In `planJobs`, replace `jobs.push({ spec, role, out });` with:
```ts
      const copies = role === base.role ? wikiOutputs(ASSETS_DIR, spec).filter((c) => c !== out) : [];
      jobs.push({ spec, role, out, copies });
```

In `planSingleUserJobs`, replace `jobs.push({ spec, role: "override", out });` with:
```ts
    jobs.push({ spec, role: "override", out, copies: wikiOutputs(ASSETS_DIR, spec).filter((c) => c !== out) });
```

- [ ] **Step 4: Write the copies after a successful capture** — in the job loop, directly after the `await Promise.race([...]);` call inside `try`, add:

```ts
        for (const copy of job.copies) {
          mkdirSync(dirname(copy), { recursive: true });
          copyFileSync(job.out, copy);
        }
```

- [ ] **Step 5: Add the wiki-only filter** — directly after the existing `WIKI_CAPTURE_DETAIL_ONLY` line add:

```ts
  // WIKI_CAPTURE_WIKI_ONLY captures just the shots that feed a wiki page.
  if (process.env.WIKI_CAPTURE_WIKI_ONLY) shots = shots.filter((s) => s.wikiTarget);
```

- [ ] **Step 6: Type-check**

Run: `cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-inventory-frontend-e2e && bunx tsc --noEmit`
Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add tests/wiki-screenshots/types.ts tests/wiki-screenshots/shot-path.ts tests/wiki-screenshots/capture.spec.ts
git commit -m "feat(wiki-screenshots): write baseline shots straight to wiki target files via wikiTarget"
```

---

### Task 2: Inventory — manifest targets for every in-scope page

**Repo:** `carmen-inventory-frontend-e2e`

**Files:**
- Modify: `tests/wiki-screenshots/manifest.ts`

**Interfaces:**
- Consumes: `ShotSpec.wikiTarget` (Task 1).

- [ ] **Step 1: Resolve full routes for the gap pages.** Relative routes in `carmen-inventory-frontend-react/routes/**` are nested; find each one's parent prefix:

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-inventory-frontend-react
for r in chart-of-accounts shelf company-profile business-setting default-setting approval journal-voucher; do
  echo "== $r"; grep -rn "path: *[\"']$r[\"']" routes | head -3; done
```
Read each hit's enclosing route file to get the full path (e.g. a `shelf` child under the `config` tree → `/config/shelf`).

- [ ] **Step 2: Add `wikiTarget` to existing shots and new shots for the gaps.** Edit `manifest.ts`. For an existing entry, add the field in place; for a route with no entry, add one in the same style. Mapping (left = route, right = `wikiTarget`):

| Route | wikiTarget |
|-------|-----------|
| `/dashboard` | `["dashboard/main", "dashboard/widget-workspace", "dashboard/my-pending"]` |
| `/procurement/approval` | `["purchase-request/my-approval", "dashboard/my-approval"]` |
| `/procurement/purchase-request` | `purchase-request/index` |
| `/procurement/purchase-request/:id` | `purchase-request/detail` |
| `/procurement/purchase-order` | `purchase-order/index` |
| `/procurement/purchase-order/:id` | `purchase-order/detail` |
| `/procurement/credit-note` | `purchase-order/credit-note` |
| `/procurement/credit-note/:id` | `purchase-order/credit-note-detail` |
| `/procurement/goods-receive-note` | `good-receive-note/index` |
| `/procurement/goods-receive-note/:id` | `good-receive-note/detail` |
| `/procurement/purchase-request-template` | `templates/purchase-request` |
| `/procurement/purchase-request-template/:id` | `templates/purchase-request-detail` |
| `/vendor-management/price-list-template` | `templates/price-list` |
| `/vendor-management/price-list-template/:id` | `templates/price-list-detail` |
| `/vendor-management/price-list` | `vendor-pricelist/index` |
| `/vendor-management/request-price-list` | `vendor-pricelist/request-price-list` |
| `/vendor-management/request-price-list/:id` | `vendor-pricelist/request-price-list-detail` |
| `/vendor-management/vendor` | `master-data/vendor` |
| `/vendor-management/vendor/:id` | `master-data/vendor-detail` |
| `/inventory-management` | `inventory/index` |
| `/inventory-management/transaction` | `inventory/transaction` |
| `/inventory-management/period-end` | `inventory/period-end` |
| `/inventory-management/inventory-adjustment` | `inventory-adjustment/index` |
| `/store-operation/wastage-reporting` | `inventory-adjustment/wastage-reporting` |
| `/inventory-management/physical-count` | `physical-count/index` |
| `/inventory-management/physical-count/:id` | `physical-count/detail` |
| `/inventory-management/spot-check` | `spot-check/index` |
| `/store-operation/store-requisition` | `store-requisition/index` |
| `/store-operation/store-requisition/:id` | `store-requisition/detail` |
| `/store-operation/stock-replenishment` | `store-requisition/stock-replenishment` |
| `/product-management/product` | `product/index` |
| `/product-management/product/:id` | `product/detail` |
| `/product-management/category` | `product/category` |
| `/operation-plan/recipe` | `recipe/index` |
| `/operation-plan/recipe/:id` | `recipe/detail` |
| `/operation-plan/category` | `recipe/category` |
| `/operation-plan/cuisine` | `recipe/cuisine` |
| `/operation-plan/equipment` | `recipe/equipment` |
| `/operation-plan/equipment-category` | `recipe/equipment-category` |
| `/config` | `master-data/index` |
| `/config/adjustment-type` | `master-data/adjustment-type` |
| `/config/business-type` | `["master-data/business-unit", "master-data/vendor-business-type"]` |
| `/config/credit-note-reason` | `master-data/credit-note-reason` |
| `/config/credit-term` | `master-data/credit-term` |
| `/config/currency` | `master-data/currency` |
| `/config/delivery-point` | `master-data/delivery-point` |
| `/config/department` | `master-data/department` |
| `/config/department/:id` | `["master-data/department-detail", "access-control/department-user"]` |
| `/config/exchange-rate` | `master-data/exchange-rate` |
| `/config/extra-cost` | `master-data/extra-cost-type` |
| `/config/location` | `master-data/location` |
| `/config/location/:id` | `["master-data/location-detail", "access-control/user-location"]` |
| `/config/tax-profile` | `master-data/tax-profile` |
| `/config/unit` | `master-data/unit` |
| chart-of-accounts full path (Step 1) — new entry if absent | `master-data/chart-of-accounts` |
| shelf full path (Step 1) — new entry if absent | `master-data/shelf` |
| `/system-admin` | `system-config/index` |
| `/system-admin/workflow` | `system-config/workflow` |
| `/system-admin/workflow/:id` | `system-config/workflow-detail` |
| `/system-admin/running-code` | `system-config/running-code` |
| `/system-admin/document` | `system-config/document` |
| `/system-admin/config-email` | `system-config/config-email` |
| `/system-admin/inventory-period` | `system-config/period` |
| `/system-admin/dashboard-dataset` | `["system-config/dashboard-dataset", "reporting-audit/widget"]` |
| `/system-admin/query-dataset` | `system-config/query-dataset` |
| company-profile full path (Step 1) — new entry if absent | `system-config/company-profile` |
| business-setting full path (Step 1) — new entry if absent | `system-config/application-config` |
| `/system-admin/user` | `access-control/user` |
| `/system-admin/user/:id` | `["access-control/user-detail", "access-control/business-unit-user"]` |
| `/system-admin/role` | `access-control/application-role` |
| `/system-admin/role/:id` | `["access-control/application-role-detail", "access-control/permission"]` |
| `/system-admin/activity-log` | `reporting-audit/activity` |
| `/system-admin/user-activity` | `reporting-audit/user-activity` |
| `/report` | `reporting-audit/report` |
| `/report/history` | `reporting-audit/history` |
| `/report/schedules` | `reporting-audit/schedule` |
| `/notifications` | `reporting-audit/notification` |
| `/accounting/journal-voucher` — new entry | `general-ledger/index` |

Not mapped on purpose (expected skips, spec §3.1): `master-data/cost-center`, `reporting-audit/attachment`, `system-config/dimension`, `system-config/menu`. The obsolete `dashboard/{grn,po,pr,sr,inventory}` images are left as they are (the old per-module dashboards no longer exist in the app).

A new entry looks like:
```ts
  { path: "/accounting/journal-voucher", module: "journal-voucher", slug: "index", wikiTarget: "general-ledger/index" },
```

- [ ] **Step 3: Sanity-check the manifest**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-inventory-frontend-e2e
bunx tsc --noEmit
grep -c "wikiTarget" tests/wiki-screenshots/manifest.ts
```
Expected: no type errors; the count equals the number of mapped rows (≈79).

- [ ] **Step 4: Commit**

```bash
git add tests/wiki-screenshots/manifest.ts
git commit -m "feat(wiki-screenshots): map manifest shots to wiki page images; add GL, shelf, COA, company-profile, app-config shots"
```

---

### Task 3: Inventory — run the capture and review the images

**Repo:** `carmen-inventory-frontend-e2e` (writes PNGs into `carmen-wiki`)

- [ ] **Step 1: Refresh seed ids for the capture tenant** (back up first — discovery overwrites the file)

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-inventory-frontend-e2e
export WIKI_CAPTURE_EMAIL=<zebra admin email confirmed in Task 0>
cp tests/wiki-screenshots/seed-ids.json /private/tmp/claude-501/seed-ids.backup.json 2>/dev/null || true
rm -f ".auth/$WIKI_CAPTURE_EMAIL.json"   # stale token cache causes silent login failures
bun run tests/wiki-screenshots/discover-seeds.ts
```
Expected: a seed id for most dynamic routes. If every route fails, the backend or login is wrong — stop and report.

- [ ] **Step 2: Capture only the wiki-feeding shots** (foreground, so progress is visible)

```bash
WIKI_CAPTURE_WIKI_ONLY=1 bun run wiki:capture
cat tests/wiki-screenshots/last-run.json
```
Expected: "Captured N screens"; `last-run.json` lists only known skips (spot-check `:id`, inventory-adjustment `:id`, routes without seed id).

- [ ] **Step 3: Look at every wiki-target PNG the run changed**

```bash
cd ../carmen-wiki && git status --short assets/screenshots/inventory | head -120
```
Open each new/modified PNG with the Read tool. Reject any image showing a login page, a 403/permission notice, an error toast over the content, or an empty skeleton: `git checkout -- <file>` if it existed before, `rm <file>` if it is new. Record each rejection and its reason for the final report.

- [ ] **Step 4: Push the e2e branch and open its PR**

```bash
cd ../carmen-inventory-frontend-e2e
git status --short    # seed-ids.json / last-run.json are run artefacts — commit source changes only
git push -u origin docs/screenshots-all-books
gh pr create --base main --title "wiki-screenshots: capture straight into wiki page images (wikiTarget)" --body "Implements carmen-wiki spec docs/superpowers/specs/2026-09-23-screenshots-all-books-design.md §4.1: ShotSpec.wikiTarget, WIKI_CAPTURE_WIKI_ONLY, and a wikiTarget for every in-scope wiki page. Type-check clean."
```
PNG changes stay uncommitted in `carmen-wiki` until Task 8.

---

### Task 4: Platform — capture project in `carmen-platform-e2e`

**Repo:** `carmen-platform-e2e`

**Files:**
- Create: `tests/wiki-screenshots/types.ts`
- Create: `tests/wiki-screenshots/manifest.ts`
- Create: `tests/wiki-screenshots/capture.spec.ts`
- Modify: `playwright.config.ts` (`projects` array)
- Modify: `package.json` (`scripts`)
- Modify: `.gitignore`

**Interfaces:**
- Produces: env `WIKI_ASSETS_DIR` (default `../carmen-wiki/assets/screenshots/platform`); output files `<WIKI_ASSETS_DIR>/<target>.png`.
- Consumes: `.auth/user.json` written by the existing `global-setup.ts`.

- [ ] **Step 1: Create `tests/wiki-screenshots/types.ts`**

```ts
/** One entry = one screen, written to one or more wiki image files. */
export type ShotSpec = {
  /** Route to open. For openFirstRow shots this is the LIST route. */
  path: string;
  /** Wiki image stems relative to WIKI_ASSETS_DIR, e.g. "clusters/index" (no ".png"). */
  targets: string[];
  /**
   * Open the first record of the list at `path` (its first link, else the row)
   * and shoot the page it lands on. Used for routes that need an id.
   */
  openFirstRow?: boolean;
};
```

- [ ] **Step 2: Create `tests/wiki-screenshots/manifest.ts`** (spec §3.2)

```ts
import type { ShotSpec } from "./types";

// Wiki image targets for the Platform book. Landing pages use "<module>/index";
// ui-screens pages use "<module>/ui-screens" (list) and "<module>/ui-screens-form".
export const SHOTS: ShotSpec[] = [
  { path: "/", targets: ["landing/index"] },
  { path: "/dashboard", targets: ["dashboard/index"] },
  { path: "/changelog", targets: ["changelog/index"] },
  { path: "/profile", targets: ["profile/index"] },
  { path: "/activity-events", targets: ["activity-events/index"] },
  { path: "/analytics", targets: ["usage-analytics/index"] },
  { path: "/sql-workbench", targets: ["sql-workbench/index"] },
  { path: "/clusters", targets: ["clusters/index", "clusters/ui-screens"] },
  { path: "/clusters/new", targets: ["clusters/ui-screens-form"] },
  { path: "/applications", targets: ["applications/index", "applications/ui-screens"] },
  { path: "/applications/new", targets: ["applications/ui-screens-form"] },
  { path: "/business-units", targets: ["business-units/index", "business-units/ui-screens"] },
  { path: "/business-units/new", targets: ["business-units/ui-screens-form"] },
  { path: "/tenant-migrations", targets: ["tenant-migrations/index", "business-units/tenant-migrations"] },
  { path: "/tenant-imports", targets: ["tenant-imports/index", "tenant-imports/ui-screens"] },
  { path: "/licenses", targets: ["licenses/index", "licenses/ui-screens"] },
  { path: "/licenses", targets: ["licenses/ui-screens-form"], openFirstRow: true },
  { path: "/license-feature-groups", targets: ["license-catalog/index", "license-catalog/ui-screens"] },
  { path: "/license-feature-groups/new", targets: ["license-catalog/ui-screens-form"] },
  { path: "/users", targets: ["users/index", "users/ui-screens"] },
  { path: "/users/new", targets: ["users/ui-screens-form"] },
  { path: "/platform/user-platform", targets: ["user-platform/index", "user-platform/ui-screens"] },
  { path: "/platform/user-platform", targets: ["user-platform/ui-screens-form"], openFirstRow: true },
  { path: "/platform/roles", targets: ["rbac/index", "rbac/ui-screens"] },
  { path: "/platform/roles/new", targets: ["rbac/ui-screens-form"] },
  { path: "/platform/super-admins", targets: ["super-admins/index"] },
  { path: "/report-templates", targets: ["report-templates/index", "report-templates/ui-screens"] },
  { path: "/report-templates/new", targets: ["report-templates/ui-screens-form"] },
  { path: "/report-form-groups", targets: ["report-form-groups/index", "report-templates/form-groups"] },
  { path: "/news", targets: ["news/index", "news/ui-screens"] },
  { path: "/news/new", targets: ["news/ui-screens-form"] },
  { path: "/broadcasts", targets: ["broadcasts/index", "broadcasts/ui-screens"] },
  { path: "/broadcasts/new", targets: ["broadcasts/ui-screens-form"] },
  { path: "/cronjobs", targets: ["cronjobs/index", "cronjobs/ui-screens"] },
  { path: "/cronjobs/new", targets: ["cronjobs/ui-screens-form"] },
  { path: "/platform/database-pools", targets: ["database-pools/index", "database-pools/ui-screens"] },
  { path: "/platform/database-pools/new", targets: ["database-pools/ui-screens-form"] },
  { path: "/cluster-admin", targets: ["cluster-admin/index", "cluster-admin/ui-screens"] },
  { path: "/cluster-admin", targets: ["cluster-admin/ui-screens-form"], openFirstRow: true },
  { path: "/platform/email-settings", targets: ["email-settings/index"] },
  { path: "/platform/configs", targets: ["platform-config/index"] },
  { path: "/platform/migrations", targets: ["platform-migrations/index"] },
  { path: "/platform/features", targets: ["feature-flags/index"] },
];
```

- [ ] **Step 3: Create `tests/wiki-screenshots/capture.spec.ts`**

```ts
import { test, expect, type Page } from "@playwright/test";
import { copyFileSync, mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { SHOTS } from "./manifest";
import type { ShotSpec } from "./types";

const ASSETS_DIR = process.env.WIKI_ASSETS_DIR ?? "../carmen-wiki/assets/screenshots/platform";
const RESULTS = join(process.cwd(), "tests/wiki-screenshots/last-run.json");
const HARD_TIMEOUT_MS = 60_000;
// Final URLs that mean "this is not the screen we asked for".
const BAD_LANDING = /\/(login|403)(\/|$|\?)|not-found/i;

async function settle(page: Page): Promise<void> {
  // Bounded: a persistent websocket can keep "networkidle" from ever firing.
  await page.waitForLoadState("networkidle", { timeout: 6_000 }).catch(() => {});
  await page
    .waitForFunction(() => document.querySelectorAll(".animate-pulse").length === 0, { timeout: 8_000 })
    .catch(() => {});
  // Close stray popovers and park the pointer so no tooltip lands in the shot.
  await page.keyboard.press("Escape").catch(() => {});
  await page.mouse.move(2, 2).catch(() => {});
  await page.waitForTimeout(300);
}

/** Open the spec's screen and write it to `out`. Throws on any failure. */
async function captureOne(page: Page, spec: ShotSpec, out: string): Promise<void> {
  await page.goto(spec.path, { waitUntil: "domcontentloaded", timeout: 30_000 });
  await settle(page);
  if (spec.openFirstRow) {
    const row = page.locator("table tbody tr").first();
    await row.waitFor({ state: "visible", timeout: 10_000 });
    const link = row.locator("a").first();
    const before = page.url();
    if (await link.count()) await link.click();
    else await row.click();
    await page.waitForURL((u) => u.toString() !== before, { timeout: 10_000 });
    await settle(page);
  }
  const landed = new URL(page.url()).pathname;
  if (BAD_LANDING.test(landed)) throw new Error(`landed on ${landed}`);
  mkdirSync(dirname(out), { recursive: true });
  await page.screenshot({ path: out, fullPage: false, animations: "disabled", timeout: 20_000 });
}

test("capture platform wiki screenshots", async ({ browser, baseURL }) => {
  test.setTimeout(0); // batch job; each shot has its own hard timeout
  const skipped: Record<string, string> = {};
  let captured = 0;
  const context = await browser.newContext({
    storageState: ".auth/user.json",
    baseURL,
    viewport: { width: 1440, height: 900 },
    ignoreHTTPSErrors: true,
  });
  await context.addInitScript(() => {
    const css = "*{transition:none!important;animation:none!important;caret-color:transparent!important}";
    const inject = (): void => {
      const el = document.createElement("style");
      el.textContent = css;
      (document.head ?? document.documentElement).appendChild(el);
    };
    if (document.head) inject();
    else document.addEventListener("DOMContentLoaded", inject, { once: true });
  });

  for (const spec of SHOTS) {
    const [first, ...rest] = spec.targets.map((t) => join(ASSETS_DIR, `${t}.png`));
    const key = `${spec.path}${spec.openFirstRow ? " [first row]" : ""}`;
    const page = await context.newPage();
    let timer: ReturnType<typeof setTimeout> | undefined;
    try {
      await Promise.race([
        captureOne(page, spec, first),
        new Promise<never>((_, reject) => {
          timer = setTimeout(() => reject(new Error("hard timeout after 60s")), HARD_TIMEOUT_MS);
        }),
      ]);
      for (const copy of rest) {
        mkdirSync(dirname(copy), { recursive: true });
        copyFileSync(first, copy);
      }
      captured++;
    } catch (err) {
      skipped[key] = (err as Error).message.split("\n")[0];
    } finally {
      if (timer) clearTimeout(timer);
      await Promise.race([page.close(), new Promise((res) => setTimeout(res, 5_000))]).catch(() => {});
    }
  }
  await context.close();

  writeFileSync(RESULTS, JSON.stringify(skipped, null, 2));
  console.log(`Captured ${captured}/${SHOTS.length} screens; skipped ${Object.keys(skipped).length}.`);
  // Zero captures means auth or the backend is broken — fail loudly instead of passing green.
  expect(captured, `No screen captured. Skips:\n${JSON.stringify(skipped, null, 2)}`).toBeGreaterThan(0);
});
```

- [ ] **Step 4: Register the project** — in `playwright.config.ts` replace the `projects` array with:

```ts
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
      testIgnore: /wiki-screenshots\//,
    },
    {
      name: 'wiki-screenshots',
      testMatch: /wiki-screenshots\/capture\.spec\.ts$/,
      // Documentation shots: no per-test video/trace/failure-screenshot artefacts.
      use: { ...devices['Desktop Chrome'], video: 'off', trace: 'off', screenshot: 'off' },
    },
  ],
```

- [ ] **Step 5: Add the script and ignore the run log**

In `package.json` `scripts` add `"wiki:capture": "playwright test --project=wiki-screenshots"`, then:

```bash
echo "tests/wiki-screenshots/last-run.json" >> .gitignore
```

- [ ] **Step 6: Static checks**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-platform-e2e
git stash -q && bunx playwright test --list --project=chromium | tail -1; git stash pop -q   # baseline count on main's config
bun run typecheck
bunx playwright test --list --project=chromium | tail -1
bunx playwright test --list --project=wiki-screenshots
```
Expected: type-check clean; the chromium test count equals the baseline; wiki-screenshots lists exactly 1 test.

- [ ] **Step 7: Commit**

```bash
git add tests/wiki-screenshots playwright.config.ts package.json .gitignore
git commit -m "feat(wiki-screenshots): capture Platform screens straight into carmen-wiki page images"
```

---

### Task 5: Platform — run the capture and review the images

**Repo:** `carmen-platform-e2e`

- [ ] **Step 1: Run** (foreground; frontend already serving `:3304`)

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-platform-e2e
E2E_NO_WEBSERVER=1 bun run wiki:capture
cat tests/wiki-screenshots/last-run.json
```
Expected: "Captured N/43 screens"; every skip carries a reason.

- [ ] **Step 2: Review every PNG**

```bash
find ../carmen-wiki/assets/screenshots/platform -name '*.png' | sort
```
Open each with the Read tool. Delete any that shows a login page, a 403 notice, an empty skeleton, or (for `ui-screens-form`) a list instead of a form; record the reason for the final report.

- [ ] **Step 3: Push and open the PR**

```bash
git push -u origin docs/screenshots-all-books
gh pr create --base main --title "wiki-screenshots: Platform capture project" --body "Implements carmen-wiki spec docs/superpowers/specs/2026-09-23-screenshots-all-books-design.md §4.2: project wiki-screenshots + bun run wiki:capture. Type-check clean; chromium suite count unchanged."
```

---

### Task 6: Wiki — folder-resolving asset upload for both books

**Repo:** `carmen-wiki`

**Files:**
- Create: `scripts/upload_assets.py`
- Modify: `scripts/upload_assets.sh` (becomes a wrapper)

**Interfaces:**
- Produces: `python3 scripts/upload_assets.py <file.png>...` — each file lives under `assets/screenshots/<book>/<module>/`; uploads to Asset Manager folder `screenshots/<module>` (inventory) or `screenshots/platform/<module>` (platform), creating folders as needed; prints `OK <url>` / `FAIL …` per file; exits 1 if any failed.

- [ ] **Step 1: Create `scripts/upload_assets.py`**

```python
#!/usr/bin/env python3
"""Upload screenshot PNGs into the Wiki.js Asset Manager, creating folders as needed.

Usage: python3 scripts/upload_assets.py assets/screenshots/<book>/<module>/<file>.png ...

Folder layout (spec 2026-09-23 §2.1):
  inventory -> screenshots/<module>/            URL /screenshots/<module>/<file>
  platform  -> screenshots/platform/<module>/   URL /screenshots/platform/<module>/<file>
Reads WIKI_API_URL / WIKI_API_TOKEN from scripts/.env.
"""
import json, os, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
for line in (ROOT / "scripts" / ".env").read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k, v)
API = os.environ["WIKI_API_URL"]
TOKEN = os.environ["WIKI_API_TOKEN"]
BASE = os.environ.get("WIKI_BASE", API.rsplit("/graphql", 1)[0])


def gql(query: str, variables: dict) -> dict:
    req = urllib.request.Request(
        API,
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {TOKEN}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        body = json.load(r)
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body["data"]


def children(parent_id: int) -> dict[str, int]:
    q = "query($p:Int!){assets{folders(parentFolderId:$p){id slug}}}"
    return {f["slug"]: f["id"] for f in gql(q, {"p": parent_id})["assets"]["folders"]}


def ensure_folder(parent_id: int, slug: str) -> int:
    existing = children(parent_id)
    if slug in existing:
        return existing[slug]
    m = ("mutation($p:Int!,$s:String!){assets{createFolder(parentFolderId:$p,slug:$s,name:$s)"
         "{responseResult{succeeded message}}}}")
    res = gql(m, {"p": parent_id, "s": slug})["assets"]["createFolder"]["responseResult"]
    if not res["succeeded"]:
        raise RuntimeError(f"createFolder {slug}: {res['message']}")
    return children(parent_id)[slug]


_cache: dict[tuple[int, str], int] = {}


def folder_for(parts: list[str]) -> int:
    fid = 0  # Asset Manager root
    for slug in parts:
        key = (fid, slug)
        if key not in _cache:
            _cache[key] = ensure_folder(fid, slug)
        fid = _cache[key]
    return fid


def curl_code(args: list[str]) -> str:
    return subprocess.run(["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", *args],
                          capture_output=True, text=True).stdout


def upload(png: Path) -> tuple[bool, str]:
    rel = png.resolve().relative_to(ROOT / "assets" / "screenshots")
    book, module = rel.parts[0], rel.parts[1]
    folder = ["screenshots", module] if book == "inventory" else ["screenshots", book, module]
    fid = folder_for(folder)
    url = "/" + "/".join(folder + [png.name])
    up = curl_code(["-m", "60", "-X", "POST", f"{BASE}/u",
                    "-H", f"Authorization: Bearer {TOKEN}",
                    "-F", f'mediaUpload={{"folderId":{fid}}};type=application/json',
                    "-F", f"mediaUpload=@{png};type=image/png"])
    get = curl_code(["-m", "20", f"{BASE}{url}"])
    return (up == "200" and get == "200", f"{url} (upload {up}, get {get})")


def main(argv: list[str]) -> int:
    ok = fail = 0
    for arg in argv:
        p = Path(arg)
        if not p.is_file():
            print(f"SKIP (missing) {arg}")
            continue
        good, msg = upload(p)
        print(("OK   " if good else "FAIL ") + msg)
        ok, fail = ok + good, fail + (not good)
    print(f"---- uploaded {ok}, failed {fail} ----")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Replace `scripts/upload_assets.sh` with a wrapper**

```bash
#!/usr/bin/env bash
# Kept for muscle memory; the folder-resolving uploader lives in upload_assets.py.
# Usage: scripts/upload_assets.sh assets/screenshots/<book>/<module>/<file>.png...
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 scripts/upload_assets.py "$@"
```

- [ ] **Step 3: Verify with one already-published Inventory image** (re-uploading an existing file is harmless)

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
python3 scripts/upload_assets.py assets/screenshots/inventory/master-data/unit.png
```
Expected: `OK   /screenshots/master-data/unit.png (upload 200, get 200)`. If the GraphQL folder query errors, print the error and stop — do not guess field names; check the Wiki.js 2 GraphQL schema via an introspection query first.

- [ ] **Step 4: Existing suite and commit**

```bash
.venv/bin/python -m pytest -q scripts
git add scripts/upload_assets.py scripts/upload_assets.sh
git commit -m "scripts: folder-resolving asset uploader for both books (creates screenshots/platform/<module>)"
```
Expected: 72 passed.

---

### Task 7: Wiki — `embed_screenshots.py`

**Repo:** `carmen-wiki`

**Files:**
- Create: `scripts/embed_screenshots.py`

**Interfaces:**
- Produces: `python3 scripts/embed_screenshots.py [--dry-run] [--book inventory|platform]` — prints `+ <locale>/<page>.md  <url>` per insert, `- <png>  <reason>` per skipped image, `! <page> missing` per missing TH/EN page, and a summary; writes pages only without `--dry-run`; writes changed page paths to `/private/tmp/claude-501/embed-changed.txt` (used by Task 8).

- [ ] **Step 1: Create the script**

```python
#!/usr/bin/env python3
"""Embed screenshots into EN and TH wiki pages by path convention.

Spec: docs/superpowers/specs/2026-09-23-screenshots-all-books-design.md §2, §5.1.

  assets/screenshots/<book>/<module>/index.png            -> <loc>/<book>/<module>.md
  assets/screenshots/<book>/<module>/<slug>.png           -> <loc>/<book>/<module>/<slug>.md
  assets/screenshots/<book>/<module>/<slug>-<variant>.png -> same page as <slug> (exact page name wins)

Idempotent: a URL already present in a page is never inserted again.
"""
import argparse, datetime, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets" / "screenshots"
LOCALES = ("en", "th")
URL_PREFIX = {"inventory": "/screenshots", "platform": "/screenshots/platform"}
SKIP_NAME = re.compile(r"(data-model|business-rules|test-scenarios|user-flow|permissions)")
SKIP_PAGES = {
    "inventory/costing", "inventory/costing/calculation-methods",
    "inventory/general-ledger/gl-posting", "inventory/system-config/doc-version",
    "platform/users/lifecycle", "platform/report-templates/xml-spec",
}
CHANGED_LIST = Path("/private/tmp/claude-501/embed-changed.txt")


def page_exists(rel: str) -> bool:
    return (ROOT / "en" / f"{rel}.md").is_file()


def resolve(book: str, module: str, stem: str) -> tuple[str, str | None] | None:
    """Map an image to (page_rel, variant); page_rel is '<book>/<module>[/<slug>]'."""
    if "--" in stem:  # role-suffixed catalog shot, never embedded
        return None
    if stem == "index" or stem.startswith("index-"):
        rel = f"{book}/{module}"
        return (rel, stem[len("index-"):] or None) if page_exists(rel) else None
    exact = f"{book}/{module}/{stem}"
    if page_exists(exact):
        return (exact, None)
    parts = stem.split("-")
    for i in range(len(parts) - 1, 0, -1):  # longest prefix first
        rel = f"{book}/{module}/{'-'.join(parts[:i])}"
        if page_exists(rel):
            return (rel, "-".join(parts[i:]))
    return None


def title_of(text: str) -> str:
    m = re.search(r"^title:\s*(.+)$", text, re.M)
    return m.group(1).strip().strip("'\"") if m else ""


def insert_at(lines: list[str]) -> int:
    """Index before which the image line goes (spec §5.1 placement)."""
    fm_end = lines.index("---", 1)
    body = range(fm_end + 1, len(lines))
    glance = next((i for i in body if lines[i].startswith("> **At a Glance**")), None)
    if glance is not None:
        i = glance
        while i < len(lines) and lines[i].startswith(">"):
            i += 1
    else:
        first_section = next((i for i in body if re.match(r"^## 1\.", lines[i])), None)
        if first_section is not None:
            return first_section
        i = next((j + 1 for j in body if lines[j].startswith("# ")), fm_end + 1)
    # Keep images grouped: step over blank lines and images already placed here.
    while i < len(lines) and (lines[i].strip() == "" or lines[i].startswith("![")):
        i += 1
    return i


def embed(page: Path, url: str, variant: str | None, now: str) -> bool:
    text = page.read_text(encoding="utf-8")
    if f"]({url})" in text:
        return False
    alt = title_of(text) + (f" {variant.replace('-', ' ')}" if variant else "") + " screen"
    lines = text.split("\n")
    at = insert_at(lines)
    lines[at:at] = [f"![{alt}]({url})", ""]
    out = re.sub(r"^date:.*$", f"date: {now}", "\n".join(lines), count=1, flags=re.M)
    page.write_text(out, encoding="utf-8")
    return True


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--book", choices=sorted(URL_PREFIX))
    args = ap.parse_args(argv)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    inserts = skips = 0
    changed: set[str] = set()
    for book in [args.book] if args.book else sorted(URL_PREFIX):
        for png in sorted((ASSETS / book).glob("*/*.png")):
            module, stem = png.parent.name, png.stem
            hit = resolve(book, module, stem)
            if not hit:
                print(f"- {png.relative_to(ROOT)}  no matching page")
                skips += 1
                continue
            rel, variant = hit
            if rel in SKIP_PAGES or SKIP_NAME.search(rel.rsplit("/", 1)[-1]):
                print(f"- {png.relative_to(ROOT)}  out-of-scope page {rel}")
                skips += 1
                continue
            url = f"{URL_PREFIX[book]}/{module}/{png.name}"
            for loc in LOCALES:
                page = ROOT / loc / f"{rel}.md"
                if not page.is_file():
                    print(f"! {loc}/{rel}.md missing (image {url})")
                    continue
                if f"]({url})" in page.read_text(encoding="utf-8"):
                    continue
                print(f"+ {loc}/{rel}.md  {url}")
                inserts += 1
                if not args.dry_run and embed(page, url, variant, now):
                    changed.add(f"{loc}/{rel}.md")
    if not args.dry_run:
        CHANGED_LIST.parent.mkdir(parents=True, exist_ok=True)
        CHANGED_LIST.write_text("".join(f"{p}\n" for p in sorted(changed)))
    verb = "planned" if args.dry_run else "inserted"
    print(f"---- {verb} {inserts}, skipped images {skips}, pages changed {len(changed)} ----")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 2: Static check and existing suite**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
python3 -c "import ast; ast.parse(open('scripts/embed_screenshots.py').read())"
.venv/bin/python -m pytest -q scripts
```
Expected: no syntax error; 72 passed.

- [ ] **Step 3: Dry-run review (Review Focus 2, 4, 5)**

```bash
python3 scripts/embed_screenshots.py --dry-run > /private/tmp/claude-501/embed-dry.txt; tail -1 /private/tmp/claude-501/embed-dry.txt
grep '^+' /private/tmp/claude-501/embed-dry.txt | head -120
grep -E '^(-|!)' /private/tmp/claude-501/embed-dry.txt
```
Check: every `+` line pairs an image with the page it depicts (e.g. `purchase-order/credit-note-detail.png` → `purchase-order/credit-note.md`); `-` lines are only route-catalog folders, `--role` shots and out-of-scope pages; each `!` (missing locale page) is noted for the report. If a `+` line is wrong, fix the image target name in the Task 2/4 manifest and re-capture — do not special-case the script.

- [ ] **Step 4: Idempotence check (Review Focus 1)** — on a scratch worktree, run twice:

```bash
S=/private/tmp/claude-501/embed-idem && rm -rf $S && git worktree add -q $S HEAD
cp -R assets/screenshots/. $S/assets/screenshots/
(cd $S && python3 scripts/embed_screenshots.py | tail -1 && python3 scripts/embed_screenshots.py | tail -1)
git worktree remove --force $S
```
Expected: the second run prints `inserted 0, … pages changed 0`.

- [ ] **Step 5: Commit**

```bash
git add scripts/embed_screenshots.py
git commit -m "scripts: embed_screenshots.py — convention-based screenshot embedding for EN and TH pages"
```

---

### Task 8: Wiki — embed, commit, publish, verify

**Repo:** `carmen-wiki`

- [ ] **Step 1: Embed for real**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki
python3 scripts/embed_screenshots.py | tail -1
wc -l < /private/tmp/claude-501/embed-changed.txt
git diff --stat | tail -1
```

- [ ] **Step 2: Spot-check placement** — one Inventory landing, one Inventory sub-page, one Platform `ui-screens` page (EN + TH):

```bash
git diff en/inventory/general-ledger.md en/inventory/master-data/shelf.md en/platform/clusters/ui-screens.md th/platform/clusters/ui-screens.md
```
Expected: image lines directly after the At a Glance blockquote (after any images already there), `date` updated, `dateCreated` unchanged.

- [ ] **Step 3: Commit PNGs and pages**

```bash
git add assets/screenshots en th
git commit -m "docs: screenshots for every screen page in the Inventory and Platform books (EN + TH)"
```

- [ ] **Step 4: Upload the PNGs added or changed on this branch** (foreground)

```bash
git diff --name-only main...HEAD -- 'assets/screenshots/**/*.png' > /private/tmp/claude-501/pngs.txt
wc -l < /private/tmp/claude-501/pngs.txt
xargs python3 scripts/upload_assets.py < /private/tmp/claude-501/pngs.txt | tail -5
```
Expected: `failed 0`. Re-run for any failed file before Step 5.

- [ ] **Step 5: Push pages**

```bash
xargs python3 scripts/push_pages.py < /private/tmp/claude-501/embed-changed.txt | tail -3
```
Expected: `failed 0`.

- [ ] **Step 6: Verify every embedded URL on the dev wiki**

```bash
grep -rhoE '\]\(/screenshots/[^)]+\)' en th | sort -u | sed -E 's/^\]\((.*)\)$/\1/' | while read u; do
  c=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "http://dev.blueledgers.com:3987$u"); [ "$c" = 200 ] || echo "$c $u"; done; echo verify-done
```
Expected: only `verify-done` printed.

- [ ] **Step 7: Coverage numbers, push, PR**

```bash
python3 - <<'EOF'
import glob, os, re
skip = re.compile(r'(data-model|business-rules|test-scenarios|user-flow|permissions)')
for book in ("inventory", "platform"):
    pages = [p for p in glob.glob(f"en/{book}/**/*.md", recursive=True) + [f"en/{book}.md"] if not skip.search(os.path.basename(p))]
    have = [p for p in pages if "](/screenshots/" in open(p).read()]
    print(f"{book}: {len(have)}/{len(pages)} screen-type pages have a screenshot")
EOF
git push -u origin docs/screenshots-all-books
```
Then open the PR with `gh pr create --base main --title "docs: screenshots for every screen page (Inventory + Platform, EN + TH)"` and a body containing: before → after coverage per book (run the same snippet on `main` via `git stash`/a `main` worktree for the before numbers), every skipped page with its reason (from Tasks 3, 5, 7), and links to the two e2e PRs.

- [ ] **Step 8: Merge order** — merge the two e2e PRs first, then this one. After merging, re-run Step 5 from `main` and Step 6 to confirm the dev wiki matches `main`.
