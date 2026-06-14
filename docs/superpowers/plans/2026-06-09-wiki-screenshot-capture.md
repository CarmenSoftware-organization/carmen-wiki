# Wiki Screenshot Capture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a manifest-driven Playwright pipeline that captures every Carmen Inventory frontend screen (EN, multi-role) into the wiki's shared screenshot tree, with a coverage report tracked in the wiki's `.specs/`.

**Architecture:** A new `wiki-screenshots` Playwright project inside `carmen-inventory-frontend-e2e` reuses that repo's existing auth harness (`auth.setup.ts` → `.auth/<email>.json`). A TypeScript manifest lists each screen; a route-discovery + coverage module diffs the manifest against the frontend's real `app/**/page.tsx` routes; the runner loads each role's `storageState`, forces `NEXT_LOCALE=en`, and writes PNGs to `carmen-wiki/assets/screenshots/inventory/<module>/<slug>.png`.

**Tech Stack:** TypeScript, Bun, Playwright, Vitest (for pure-logic unit tests), Next.js + next-intl (the target app).

---

## Repos and conventions

- **Code lives in** `carmen-inventory-frontend-e2e` (sibling repo). New files go under `tests/wiki-screenshots/` (pure modules + runner) and `unit/wiki-screenshots/` (vitest tests, per `vitest.config.ts` `include: ["unit/**/*.test.ts"]`).
- **Output lands in** `carmen-wiki` (`assets/screenshots/inventory/...` for images, `.specs/screenshot-coverage.md` for the report).
- Each task's `git` commands note the repo to run them in. Default working dir is `carmen-wiki`; prefix e2e commits with `cd ../carmen-inventory-frontend-e2e`.
- Existing facts the code depends on:
  - `tests/test-users.ts` exports `TEST_USERS` (`{ role, email, password }[]`), all password `12345678`; `Admin` is `admin@blueledgers.com`.
  - `tests/fixtures/auth.paths.ts` exports `authFile(email): string` → `<cwd>/.auth/<email>.json`.
  - `playwright.config.ts` has projects `setup`, `login`, `chromium`; `webServer` auto-runs `bun dev` on `../carmen-inventory-frontend-react` at `http://localhost:3000`.
  - Frontend resolves locale from the `NEXT_LOCALE` cookie (next-intl, no URL prefix).

---

## File structure

| File | Responsibility |
|------|----------------|
| `tests/wiki-screenshots/types.ts` | `ShotSpec` type only |
| `tests/wiki-screenshots/route-discovery.ts` | Pure: map `page.tsx` paths → canonical routes; walk `app/` |
| `tests/wiki-screenshots/seed-manifest.ts` | Pure: infer module/slug + generate manifest source; CLI to write `manifest.ts` |
| `tests/wiki-screenshots/manifest.ts` | Auto-generated then curated `SHOTS: ShotSpec[]` |
| `tests/wiki-screenshots/coverage.ts` | Pure: `computeCoverage` + `renderReport`; CLI writes report to wiki `.specs/` |
| `tests/wiki-screenshots/locale.ts` | Helper: add `NEXT_LOCALE=en` cookie to a context |
| `tests/wiki-screenshots/capture.spec.ts` | Playwright runner: per-role context, navigate, screenshot |
| `unit/wiki-screenshots/route-discovery.test.ts` | Vitest for route mapping |
| `unit/wiki-screenshots/seed-manifest.test.ts` | Vitest for module/slug inference + generation |
| `unit/wiki-screenshots/coverage.test.ts` | Vitest for coverage diff |
| `playwright.config.ts` (modify) | Register `wiki-screenshots` project; ignore it in `chromium` |
| `package.json` (modify) | Add `wiki:seed`, `wiki:coverage`, `wiki:capture` scripts |

---

## Task 1: Route discovery (pure)

**Files:**
- Create: `../carmen-inventory-frontend-e2e/tests/wiki-screenshots/route-discovery.ts`
- Test: `../carmen-inventory-frontend-e2e/unit/wiki-screenshots/route-discovery.test.ts`

- [ ] **Step 1: Write the failing test**

Create `unit/wiki-screenshots/route-discovery.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { fileToRoute } from "../../tests/wiki-screenshots/route-discovery";

describe("fileToRoute", () => {
  it("maps the app root page to /", () => {
    expect(fileToRoute("page.tsx")).toBe("/");
  });

  it("strips route groups like (root) and (external)", () => {
    expect(fileToRoute("(root)/dashboard/page.tsx")).toBe("/dashboard");
    expect(fileToRoute("(external)/pl/[url_token]/page.tsx")).toBe("/pl/:url_token");
  });

  it("converts dynamic segments [id] to :id", () => {
    expect(fileToRoute("(root)/config/department/[id]/page.tsx")).toBe(
      "/config/department/:id",
    );
  });

  it("handles nested groups and multiple statics", () => {
    expect(
      fileToRoute("(root)/procurement/purchase-order/new/page.tsx"),
    ).toBe("/procurement/purchase-order/new");
  });

  it("returns null for non-page files", () => {
    expect(fileToRoute("(root)/dashboard/layout.tsx")).toBeNull();
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ../carmen-inventory-frontend-e2e && bun run test:unit -- route-discovery`
Expected: FAIL — `Failed to resolve import ".../route-discovery"`.

- [ ] **Step 3: Write minimal implementation**

Create `tests/wiki-screenshots/route-discovery.ts`:

```ts
import { readdirSync, statSync } from "node:fs";
import { join, relative, sep } from "node:path";

/**
 * Convert an `app/`-relative path (e.g. "(root)/config/[id]/page.tsx") into a
 * canonical route ("/config/:id"), or null if the file is not a page.tsx.
 * Route groups "(name)" are dropped; "[seg]"/"[...seg]" become ":seg".
 */
export function fileToRoute(relPath: string): string | null {
  const norm = relPath.split(sep).join("/");
  if (norm !== "page.tsx" && !norm.endsWith("/page.tsx")) return null;
  const body = norm.replace(/\/?page\.tsx$/, "");
  const segments = body
    .split("/")
    .filter((s) => s.length > 0)
    .filter((s) => !(s.startsWith("(") && s.endsWith(")")))
    .map((s) => s.replace(/^\[(?:\.{3})?([^\]]+)\]$/, ":$1"));
  const route = "/" + segments.join("/");
  return route === "/" ? "/" : route;
}

/** Recursively walk an `app/` directory and return sorted unique routes. */
export function discoverRoutes(appDir: string): string[] {
  const routes = new Set<string>();
  const walk = (dir: string): void => {
    for (const name of readdirSync(dir)) {
      const full = join(dir, name);
      if (statSync(full).isDirectory()) walk(full);
      else if (name === "page.tsx") {
        const r = fileToRoute(relative(appDir, full));
        if (r) routes.add(r);
      }
    }
  };
  walk(appDir);
  return [...routes].sort();
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ../carmen-inventory-frontend-e2e && bun run test:unit -- route-discovery`
Expected: PASS (5 tests).

- [ ] **Step 5: Commit**

```bash
cd ../carmen-inventory-frontend-e2e && \
git add tests/wiki-screenshots/route-discovery.ts unit/wiki-screenshots/route-discovery.test.ts && \
git commit -m "feat(wiki-screenshots): add route discovery from app/ pages

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: ShotSpec type + locale helper

**Files:**
- Create: `../carmen-inventory-frontend-e2e/tests/wiki-screenshots/types.ts`
- Create: `../carmen-inventory-frontend-e2e/tests/wiki-screenshots/locale.ts`

No unit test — `types.ts` is a type declaration and `locale.ts` is a thin Playwright wrapper exercised by the Task 5 smoke run.

- [ ] **Step 1: Create the type**

Create `tests/wiki-screenshots/types.ts`:

```ts
/** One entry = one screenshot PNG. */
export type ShotSpec = {
  /** Canonical route; dynamic segments use the :seg form, e.g. "/vendor-management/vendor/:id". */
  path: string;
  /** Wiki module folder under assets/screenshots/inventory/. */
  module: string;
  /** Output filename stem; final file is <module>/<slug>.png. */
  slug: string;
  /** Test-user role to capture as. Defaults to "Admin". */
  role?: string;
  /** Value substituted into the first :seg of `path` for detail routes. */
  seedId?: string;
  /** CSS selector awaited before the screenshot; defaults to networkidle only. */
  waitFor?: string;
  /** Override the default 1440x900 viewport. */
  viewport?: { width: number; height: number };
};
```

- [ ] **Step 2: Create the locale helper**

Create `tests/wiki-screenshots/locale.ts`:

```ts
import type { BrowserContext } from "@playwright/test";

/** Force the frontend into English by setting the next-intl NEXT_LOCALE cookie. */
export async function setEnLocale(
  context: BrowserContext,
  baseURL: string,
): Promise<void> {
  const { hostname } = new URL(baseURL);
  await context.addCookies([
    { name: "NEXT_LOCALE", value: "en", domain: hostname, path: "/" },
  ]);
}
```

- [ ] **Step 3: Type-check**

Run: `cd ../carmen-inventory-frontend-e2e && bunx tsc --noEmit`
Expected: no errors referencing `types.ts` or `locale.ts`.

- [ ] **Step 4: Commit**

```bash
cd ../carmen-inventory-frontend-e2e && \
git add tests/wiki-screenshots/types.ts tests/wiki-screenshots/locale.ts && \
git commit -m "feat(wiki-screenshots): add ShotSpec type and EN-locale cookie helper

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Coverage checker (pure + CLI)

**Files:**
- Create: `../carmen-inventory-frontend-e2e/tests/wiki-screenshots/coverage.ts`
- Test: `../carmen-inventory-frontend-e2e/unit/wiki-screenshots/coverage.test.ts`

- [ ] **Step 1: Write the failing test**

Create `unit/wiki-screenshots/coverage.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import { computeCoverage, renderReport } from "../../tests/wiki-screenshots/coverage";
import type { ShotSpec } from "../../tests/wiki-screenshots/types";

const shots: ShotSpec[] = [
  { path: "/dashboard", module: "dashboard", slug: "index" },
  { path: "/vendor-management/vendor/:id", module: "vendor", slug: "detail", seedId: "v1" },
  { path: "/config/unit", module: "unit", slug: "index" },
  { path: "/gone", module: "x", slug: "index" }, // not a real route -> stale
];
const routes = [
  "/dashboard",
  "/vendor-management/vendor/:id",
  "/config/unit",
  "/config/department/:id", // real route, no shot -> missing
];

describe("computeCoverage", () => {
  it("classifies covered / missing / stale", () => {
    const rows = computeCoverage(routes, shots);
    const byRoute = Object.fromEntries(rows.map((r) => [r.route, r.status]));
    expect(byRoute["/dashboard"]).toBe("covered");
    expect(byRoute["/vendor-management/vendor/:id"]).toBe("covered");
    expect(byRoute["/config/department/:id"]).toBe("missing");
    expect(byRoute["/gone"]).toBe("stale");
  });

  it("flags dynamic routes whose shot lacks seedId as needs-seed", () => {
    const noSeed: ShotSpec[] = [{ path: "/x/:id", module: "x", slug: "detail" }];
    const rows = computeCoverage(["/x/:id"], noSeed);
    expect(rows[0].status).toBe("needs-seed");
  });

  it("marks routes listed in the skipped map as skipped", () => {
    const rows = computeCoverage(["/dashboard"], shots, { "/dashboard": "timeout" });
    expect(rows[0].status).toBe("skipped");
    expect(rows[0].reason).toBe("timeout");
  });
});

describe("renderReport", () => {
  it("emits a markdown table with a summary line", () => {
    const md = renderReport(computeCoverage(routes, shots));
    expect(md).toContain("# Screenshot Coverage");
    expect(md).toContain("| Route | Status |");
    expect(md).toMatch(/covered: \d+/);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ../carmen-inventory-frontend-e2e && bun run test:unit -- coverage`
Expected: FAIL — cannot resolve `coverage`.

- [ ] **Step 3: Write minimal implementation**

Create `tests/wiki-screenshots/coverage.ts`:

```ts
import { mkdirSync, readFileSync, writeFileSync, existsSync } from "node:fs";
import { dirname, join } from "node:path";
import type { ShotSpec } from "./types";
import { discoverRoutes } from "./route-discovery";
import { SHOTS } from "./manifest";

export type CoverageStatus =
  | "covered"
  | "missing"
  | "needs-seed"
  | "stale"
  | "skipped";

export type CoverageRow = {
  route: string;
  status: CoverageStatus;
  module?: string;
  slug?: string;
  reason?: string;
};

/** Diff the manifest against the real route list. Pure. */
export function computeCoverage(
  routes: string[],
  shots: ShotSpec[],
  skipped: Record<string, string> = {},
): CoverageRow[] {
  const shotByPath = new Map(shots.map((s) => [s.path, s]));
  const rows: CoverageRow[] = [];

  for (const route of routes) {
    const shot = shotByPath.get(route);
    if (!shot) {
      rows.push({ route, status: "missing" });
    } else if (route.includes(":") && !shot.seedId) {
      rows.push({ route, status: "needs-seed", module: shot.module, slug: shot.slug });
    } else if (skipped[route]) {
      rows.push({
        route,
        status: "skipped",
        module: shot.module,
        slug: shot.slug,
        reason: skipped[route],
      });
    } else {
      rows.push({ route, status: "covered", module: shot.module, slug: shot.slug });
    }
  }

  const real = new Set(routes);
  for (const shot of shots) {
    if (!real.has(shot.path)) {
      rows.push({ route: shot.path, status: "stale", module: shot.module, slug: shot.slug });
    }
  }
  return rows;
}

/** Render the coverage rows as a Markdown report. Pure. */
export function renderReport(rows: CoverageRow[]): string {
  const counts: Record<string, number> = {};
  for (const r of rows) counts[r.status] = (counts[r.status] ?? 0) + 1;
  const summary = (["covered", "missing", "needs-seed", "skipped", "stale"] as const)
    .map((s) => `${s}: ${counts[s] ?? 0}`)
    .join(" | ");

  const header = [
    "# Screenshot Coverage",
    "",
    "_Auto-generated by `bun run wiki:coverage` in carmen-inventory-frontend-e2e._",
    "",
    `**Total routes: ${rows.length}** — ${summary}`,
    "",
    "| Route | Status | Module | Slug | Note |",
    "|-------|--------|--------|------|------|",
  ];
  const body = rows
    .sort((a, b) => a.route.localeCompare(b.route))
    .map(
      (r) =>
        `| \`${r.route}\` | ${r.status} | ${r.module ?? ""} | ${r.slug ?? ""} | ${r.reason ?? ""} |`,
    );
  return [...header, ...body, ""].join("\n");
}

/** CLI entry: discover routes, diff against SHOTS, write the report into the wiki. */
function main(): void {
  const frontendDir = process.env.E2E_FRONTEND_DIR ?? "../carmen-inventory-frontend-react";
  const specsDir = process.env.WIKI_SPECS_DIR ?? "../carmen-wiki/.specs";
  const resultsPath = join(process.cwd(), "tests/wiki-screenshots/last-run.json");

  const routes = discoverRoutes(join(frontendDir, "app"));
  const skipped: Record<string, string> = existsSync(resultsPath)
    ? JSON.parse(readFileSync(resultsPath, "utf8"))
    : {};
  const md = renderReport(computeCoverage(routes, SHOTS, skipped));

  const out = join(specsDir, "screenshot-coverage.md");
  mkdirSync(dirname(out), { recursive: true });
  writeFileSync(out, md);
  console.log(`Wrote ${out} (${routes.length} routes)`);
}

if (import.meta.main) main();
```

Note: `import.meta.main` is Bun's entrypoint guard; the CLI only runs under `bun run`, never during vitest import.

- [ ] **Step 4: Add a temporary stub manifest so the import resolves**

`coverage.ts` imports `./manifest`. It does not exist until Task 4. Create a minimal placeholder now so type-check and tests pass; Task 4 overwrites it:

Create `tests/wiki-screenshots/manifest.ts`:

```ts
import type { ShotSpec } from "./types";

export const SHOTS: ShotSpec[] = [];
```

- [ ] **Step 5: Run test to verify it passes**

Run: `cd ../carmen-inventory-frontend-e2e && bun run test:unit -- coverage`
Expected: PASS (4 tests).

- [ ] **Step 6: Commit**

```bash
cd ../carmen-inventory-frontend-e2e && \
git add tests/wiki-screenshots/coverage.ts tests/wiki-screenshots/manifest.ts unit/wiki-screenshots/coverage.test.ts && \
git commit -m "feat(wiki-screenshots): add coverage diff + markdown report

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Manifest bootstrap (pure + CLI) and generate the manifest

**Files:**
- Create: `../carmen-inventory-frontend-e2e/tests/wiki-screenshots/seed-manifest.ts`
- Test: `../carmen-inventory-frontend-e2e/unit/wiki-screenshots/seed-manifest.test.ts`
- Overwrite: `../carmen-inventory-frontend-e2e/tests/wiki-screenshots/manifest.ts`

- [ ] **Step 1: Write the failing test**

Create `unit/wiki-screenshots/seed-manifest.test.ts`:

```ts
import { describe, it, expect } from "vitest";
import {
  inferModuleSlug,
  generateManifestSource,
} from "../../tests/wiki-screenshots/seed-manifest";

describe("inferModuleSlug", () => {
  it("maps the root route", () => {
    expect(inferModuleSlug("/")).toEqual({ module: "root", slug: "index" });
  });
  it("uses index for list pages", () => {
    expect(inferModuleSlug("/procurement/purchase-order")).toEqual({
      module: "purchase-order",
      slug: "index",
    });
  });
  it("uses detail for dynamic leaf pages", () => {
    expect(inferModuleSlug("/vendor-management/vendor/:id")).toEqual({
      module: "vendor",
      slug: "detail",
    });
  });
  it("keeps action segments as the slug", () => {
    expect(inferModuleSlug("/procurement/purchase-order/new")).toEqual({
      module: "purchase-order",
      slug: "new",
    });
    expect(inferModuleSlug("/inventory-management/physical-count/:id/review")).toEqual({
      module: "physical-count",
      slug: "review",
    });
  });
});

describe("generateManifestSource", () => {
  it("emits a typed SHOTS array and skips playground/login/external routes", () => {
    const src = generateManifestSource([
      "/dashboard",
      "/playground/chart",
      "/login",
      "/pl/:url_token",
      "/vendor-management/vendor/:id",
    ]);
    expect(src).toContain('import type { ShotSpec } from "./types"');
    expect(src).toContain("export const SHOTS: ShotSpec[] = [");
    expect(src).toContain('{ path: "/dashboard"');
    expect(src).not.toContain("/playground/chart");
    expect(src).not.toContain('"/login"');
    expect(src).not.toContain("/pl/:url_token");
    // dynamic route present but flagged for a seedId
    expect(src).toContain("/vendor-management/vendor/:id");
    expect(src).toContain("TODO: set seedId");
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd ../carmen-inventory-frontend-e2e && bun run test:unit -- seed-manifest`
Expected: FAIL — cannot resolve `seed-manifest`.

- [ ] **Step 3: Write minimal implementation**

Create `tests/wiki-screenshots/seed-manifest.ts`:

```ts
import { writeFileSync } from "node:fs";
import { join } from "node:path";
import { discoverRoutes } from "./route-discovery";

const ACTION_SLUGS = new Set(["new", "review", "entry"]);

/** Routes that are dev-only, unauthenticated, or token-gated — excluded from auto-seed. */
function isExcluded(route: string): boolean {
  return (
    route.startsWith("/playground") ||
    route === "/login" ||
    route.startsWith("/pl/")
  );
}

/** Infer a wiki module folder and filename slug from a canonical route. */
export function inferModuleSlug(route: string): { module: string; slug: string } {
  if (route === "/") return { module: "root", slug: "index" };
  const segs = route.split("/").filter(Boolean);
  const last = segs[segs.length - 1];

  let slug: string;
  if (last.startsWith(":")) slug = "detail";
  else if (ACTION_SLUGS.has(last)) slug = last;
  else slug = "index";

  const statics = segs.filter((s) => !s.startsWith(":") && !ACTION_SLUGS.has(s));
  const module = statics[statics.length - 1] ?? segs[0];
  return { module, slug };
}

/** Produce the TypeScript source for manifest.ts from a route list. Pure. */
export function generateManifestSource(routes: string[]): string {
  const lines = routes
    .filter((r) => !isExcluded(r))
    .sort()
    .map((r) => {
      const { module, slug } = inferModuleSlug(r);
      const entry = `  { path: ${JSON.stringify(r)}, module: ${JSON.stringify(module)}, slug: ${JSON.stringify(slug)} },`;
      return r.includes(":") ? `  // TODO: set seedId\n${entry}` : entry;
    });
  return [
    "// AUTO-GENERATED by `bun run wiki:seed`, then hand-curated.",
    "// Re-running the seed OVERWRITES this file — curate via PR, not regeneration.",
    'import type { ShotSpec } from "./types";',
    "",
    "export const SHOTS: ShotSpec[] = [",
    ...lines,
    "];",
    "",
  ].join("\n");
}

function main(): void {
  const frontendDir = process.env.E2E_FRONTEND_DIR ?? "../carmen-inventory-frontend-react";
  const routes = discoverRoutes(join(frontendDir, "app"));
  const out = join(process.cwd(), "tests/wiki-screenshots/manifest.ts");
  writeFileSync(out, generateManifestSource(routes));
  console.log(`Wrote ${out} (${routes.length} routes discovered)`);
}

if (import.meta.main) main();
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd ../carmen-inventory-frontend-e2e && bun run test:unit -- seed-manifest`
Expected: PASS (6 tests).

- [ ] **Step 5: Generate the real manifest**

Run: `cd ../carmen-inventory-frontend-e2e && bun run tests/wiki-screenshots/seed-manifest.ts`
Expected: `Wrote .../manifest.ts (N routes discovered)` with N ≈ 134. `manifest.ts` now contains an `Admin` entry per static route and `// TODO: set seedId` markers above each dynamic route.

- [ ] **Step 6: Verify it type-checks and tests still pass**

Run: `cd ../carmen-inventory-frontend-e2e && bunx tsc --noEmit && bun run test:unit -- wiki-screenshots`
Expected: no type errors; all wiki-screenshots unit tests PASS.

- [ ] **Step 7: Commit**

```bash
cd ../carmen-inventory-frontend-e2e && \
git add tests/wiki-screenshots/seed-manifest.ts tests/wiki-screenshots/manifest.ts unit/wiki-screenshots/seed-manifest.test.ts && \
git commit -m "feat(wiki-screenshots): add manifest bootstrap + generate initial manifest

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Capture runner + Playwright project + scripts

**Files:**
- Create: `../carmen-inventory-frontend-e2e/tests/wiki-screenshots/capture.spec.ts`
- Modify: `../carmen-inventory-frontend-e2e/playwright.config.ts`
- Modify: `../carmen-inventory-frontend-e2e/package.json`

- [ ] **Step 1: Write the capture runner**

Create `tests/wiki-screenshots/capture.spec.ts`:

```ts
import { test } from "@playwright/test";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { SHOTS } from "./manifest";
import type { ShotSpec } from "./types";
import { TEST_USERS } from "../test-users";
import { authFile } from "../fixtures/auth.paths";
import { setEnLocale } from "./locale";

const ASSETS_DIR =
  process.env.WIKI_ASSETS_DIR ?? "../carmen-wiki/assets/screenshots/inventory";
const BASE_URL = process.env.E2E_BASE_URL ?? "http://localhost:3000";
const RESULTS = join(process.cwd(), "tests/wiki-screenshots/last-run.json");
const DEFAULT_VIEWPORT = { width: 1440, height: 900 };

function emailForRole(role: string): string {
  const user = TEST_USERS.find((u) => u.role === role);
  if (!user) throw new Error(`No test user defined for role "${role}"`);
  return user.email;
}

function resolvePath(spec: ShotSpec): string {
  return spec.seedId
    ? spec.path.replace(/\/:[A-Za-z_]+/, `/${spec.seedId}`)
    : spec.path;
}

function outputFile(spec: ShotSpec): string {
  return join(ASSETS_DIR, spec.module, `${spec.slug}.png`);
}

test("capture wiki screenshots", async ({ browser }) => {
  test.setTimeout(0); // batch job; individual gotos still time out at 30s

  // Group shots by role; defer dynamic routes that lack a seedId.
  const skipped: Record<string, string> = {};
  const byRole = new Map<string, ShotSpec[]>();
  for (const spec of SHOTS) {
    if (spec.path.includes(":") && !spec.seedId) {
      skipped[spec.path] = "dynamic route without seedId";
      continue;
    }
    const role = spec.role ?? "Admin";
    const list = byRole.get(role) ?? [];
    list.push(spec);
    byRole.set(role, list);
  }

  for (const [role, specs] of byRole) {
    const context = await browser.newContext({
      storageState: authFile(emailForRole(role)),
      viewport: DEFAULT_VIEWPORT,
    });
    await setEnLocale(context, BASE_URL);
    const page = await context.newPage();
    await page.addInitScript(() => {
      const style = document.createElement("style");
      style.innerHTML =
        "*{transition:none!important;animation:none!important;caret-color:transparent!important}";
      document.documentElement.appendChild(style);
    });

    for (const spec of specs) {
      const url = resolvePath(spec);
      try {
        if (spec.viewport) await page.setViewportSize(spec.viewport);
        await page.goto(url, { waitUntil: "networkidle", timeout: 30_000 });
        if (spec.waitFor) {
          await page.waitForSelector(spec.waitFor, { timeout: 15_000 });
        }
        const out = outputFile(spec);
        mkdirSync(dirname(out), { recursive: true });
        await page.screenshot({ path: out, fullPage: true });
        if (spec.viewport) await page.setViewportSize(DEFAULT_VIEWPORT);
      } catch (err) {
        skipped[spec.path] = (err as Error).message.split("\n")[0];
      }
    }
    await context.close();
  }

  writeFileSync(RESULTS, JSON.stringify(skipped, null, 2));
  console.log(
    `Captured ${SHOTS.length - Object.keys(skipped).length} screens; skipped ${Object.keys(skipped).length}.`,
  );
});
```

- [ ] **Step 2: Register the project in `playwright.config.ts`**

In `playwright.config.ts`, the existing `chromium` project must NOT also pick up the capture spec, and a new `wiki-screenshots` project must run after `setup`.

Modify the `chromium` project's `testIgnore` (currently `/001-login\.spec\.ts$|auth\.setup\.ts$/`) to also exclude the wiki spec:

```ts
    {
      name: "chromium",
      testIgnore: /001-login\.spec\.ts$|auth\.setup\.ts$|wiki-screenshots\//,
      dependencies: ["setup"],
      use: { ...devices["Desktop Chrome"] },
    },
```

Then add a new project to the `projects` array (after `chromium`):

```ts
    {
      name: "wiki-screenshots",
      testMatch: /wiki-screenshots\/capture\.spec\.ts$/,
      dependencies: ["setup"],
      fullyParallel: false,
      use: { ...devices["Desktop Chrome"] },
    },
```

- [ ] **Step 3: Add npm scripts in `package.json`**

Add these three entries to the `"scripts"` block (next to the other `e2e:*` entries):

```json
    "wiki:seed": "bun run tests/wiki-screenshots/seed-manifest.ts",
    "wiki:coverage": "bun run tests/wiki-screenshots/coverage.ts",
    "wiki:capture": "playwright test --project=wiki-screenshots",
```

- [ ] **Step 4: Type-check**

Run: `cd ../carmen-inventory-frontend-e2e && bunx tsc --noEmit`
Expected: no errors.

- [ ] **Step 5: Commit**

```bash
cd ../carmen-inventory-frontend-e2e && \
git add tests/wiki-screenshots/capture.spec.ts playwright.config.ts package.json && \
git commit -m "feat(wiki-screenshots): add capture runner, project, and scripts

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

---

## Task 6: Smoke run + coverage report + commit outputs

This task runs the pipeline end-to-end. It needs the frontend's dependencies installed and the test users to exist in the target environment (the same prerequisites the existing e2e suite has). Playwright auto-starts the dev server via `webServer`.

- [ ] **Step 1: Ensure browsers are installed**

Run: `cd ../carmen-inventory-frontend-e2e && bun run install-browsers`
Expected: Playwright reports Chromium present/installed.

- [ ] **Step 2: Smoke-capture a single screen**

Temporarily verify the runner works on one known-good static route before the full batch. Run the auth setup + capture, which will attempt every static `Admin` route:

Run: `cd ../carmen-inventory-frontend-e2e && bun run wiki:capture`
Expected: console ends with `Captured <n> screens; skipped <m>.`; `tests/wiki-screenshots/last-run.json` is written.

- [ ] **Step 3: Verify PNGs landed in the wiki tree**

Run: `ls ../carmen-wiki/assets/screenshots/inventory/dashboard/index.png && find ../carmen-wiki/assets/screenshots/inventory -name '*.png' -newermt '-1 hour' | wc -l`
Expected: `dashboard/index.png` exists; the count of recently written PNGs is > 0 (most static routes captured). Open 2–3 images to confirm they are EN and fully rendered (not a spinner/blank).

- [ ] **Step 4: Generate the coverage report**

Run: `cd ../carmen-inventory-frontend-e2e && bun run wiki:coverage`
Expected: `Wrote ../carmen-wiki/.specs/screenshot-coverage.md (N routes)`. Open it: dynamic routes show `needs-seed`, any failed navigations show `skipped` with a reason, fully-captured routes show `covered`.

- [ ] **Step 5: Review skips and (optionally) curate seedIds**

Inspect `last-run.json` and the report's `skipped`/`needs-seed` rows. For high-value detail screens (e.g. one PR, one PO, one GRN, one vendor), add a `seedId` to that entry in `manifest.ts` using a real record id from the target environment, then re-run `bun run wiki:capture` to fill them. This curation is incremental and may be repeated; it is not required for the pipeline to be complete.

- [ ] **Step 6: Commit the captured screenshots (wiki repo)**

```bash
cd /Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki && \
git add assets/screenshots/inventory .specs/screenshot-coverage.md && \
git commit -m "assets(screenshots): add captured Inventory frontend screens + coverage report

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>"
```

- [ ] **Step 7: Commit any manifest curation (e2e repo)**

```bash
cd ../carmen-inventory-frontend-e2e && \
git add tests/wiki-screenshots/manifest.ts && \
git commit -m "chore(wiki-screenshots): curate seedIds for key detail screens

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>" || echo "no manifest changes to commit"
```

---

## Done criteria

- `bun run wiki:seed` regenerates `manifest.ts` from the live route list.
- `bun run wiki:capture` writes EN PNGs to `carmen-wiki/assets/screenshots/inventory/<module>/<slug>.png` for every captureable manifest entry, across the roles named in the manifest.
- `bun run wiki:coverage` writes `carmen-wiki/.specs/screenshot-coverage.md` classifying every real route as covered / missing / needs-seed / stale / skipped.
- All three vitest suites (`route-discovery`, `coverage`, `seed-manifest`) pass.
- `last-run.json` records skip reasons so re-runs and coverage stay honest.

## Notes / deferred (per spec §8–§9)

- No TH capture (EN images reused across locales), no Platform admin, no visual-diff regression, no automated DB seeding.
- Embedding the captured images into specific wiki pages (EN+TH) is a separate content task.
- `inferModuleSlug` is a best-effort bootstrap; module names that don't match an existing wiki folder (e.g. `config/*` → wiki `system-config`, or `spot-check/location/:id` → `location`) are curated by hand in `manifest.ts`.
