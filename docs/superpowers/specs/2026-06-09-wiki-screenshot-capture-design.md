# Wiki Screenshot Capture — Design

- **Date:** 2026-06-09
- **Status:** Approved (pending spec review)
- **Scope:** Capture screenshots of every Carmen **Inventory frontend** screen to build a reusable image catalog for the wiki.

## 1. Purpose

Produce a complete, repeatable screenshot set of the `carmen-inventory-frontend-react`
app and store it in the wiki's shared screenshot tree
(`assets/screenshots/inventory/<module>/<slug>.png`). The images serve two goals
at once:

1. **Wiki embeds** — pages reference these files with
   `![alt](/screenshots/<module>/<file>)` (the existing pattern, mirrored EN+TH).
2. **Visual catalog** — a single rerunnable source of every screen, so coverage
   gaps and stale UI are visible.

The capture must be **manifest-driven and rerunnable**, not a one-off manual pass.

## 2. Decisions (locked)

| Decision | Choice |
|----------|--------|
| Apps in scope | Inventory frontend only (`carmen-inventory-frontend-react`, ~134 `page.tsx`) |
| Platform admin | Out of scope |
| Route depth | Static routes + detail (`[id]`) routes via a manifest-supplied `seedId` |
| Locale | **EN only** — reused for both EN and TH wiki pages |
| Roles | **Multiple** — `Admin` baseline for all routes; per-route role override for workflow/approval screens |
| Approach | **A** — new Playwright project inside `carmen-inventory-frontend-e2e`, reusing its auth harness |
| Manifest format | **TypeScript** (type-checked) |
| Coverage report | Written into the wiki repo's **`.specs/`** directory |
| Manifest bootstrap | **Auto-seeded** from the 134 discovered routes (Admin/static first), then enriched by hand |

## 3. Why Approach A

The E2E repo already provides everything auth-related:

- `playwright.config.ts` — `baseURL` `http://localhost:3000`, auto-starts `bun dev`
  on the frontend via `webServer`, `screenshot: "on"`.
- `tests/auth.setup.ts` — logs in every test user once per run and persists
  `storageState` to `.auth/<email>.json`.
- `tests/test-users.ts` — 9 roles (Requestor, HOD, Purchase, FC, GM, Owner,
  StoreManager, Budget, Admin), all password `12345678`, `BU_CODE = "BLAVG"`.

Reusing this avoids reimplementing login (Approach B) and gives a rerunnable,
trackable pipeline (vs. manual Approach C).

Locale is resolved by `next-intl` from the **`NEXT_LOCALE` cookie** (no URL
prefix; confirmed in `app/layout.tsx` / `app/global-error.tsx`). EN is forced by
injecting `NEXT_LOCALE=en` into the browser context before navigation.

## 4. Components

Each component has a single responsibility and a defined interface.

### 4.1 Route manifest — `tests/wiki-screenshots/manifest.ts`

The source of truth for *what* to capture. One entry = one PNG.

```
type ShotSpec = {
  path: string;        // real URL, e.g. "/store-operation/store-requisition"
                       // detail routes use seedId to fill [id]: "/.../price-list/:id"
  module: string;      // wiki module folder, e.g. "store-requisition"
  slug: string;        // output filename stem, e.g. "list" -> store-requisition/list.png
  role?: string;       // default "Admin"; override for workflow/approval screens
  seedId?: string;     // value substituted into a :id / [id] placeholder in path
  waitFor?: string;    // CSS selector to await before shooting; default networkidle
  viewport?: { width: number; height: number }; // default 1440x900
};

export const SHOTS: ShotSpec[] = [ /* auto-seeded, then curated */ ];
```

**Interface:** import `SHOTS`; depends on nothing at runtime (pure data).

### 4.2 Coverage checker — `tests/wiki-screenshots/coverage.ts`

Scans the frontend's `app/**/page.tsx`, derives canonical URL paths (stripping
route groups like `(root)`/`(external)`, mapping `[id]` → `:id`), and diffs
against the manifest. Emits a Markdown report.

- **Input:** `E2E_FRONTEND_DIR` (default `../carmen-inventory-frontend-react`), `manifest.ts`.
- **Output:** `<WIKI_SPECS_DIR>/screenshot-coverage.md` (default
  `../carmen-wiki/.specs/screenshot-coverage.md`).
- **Report rows:** route → status one of `covered`, `missing` (route exists, no
  manifest entry), `needs-seed` (dynamic route with no `seedId`), `stale`
  (manifest path matches no real route), `skipped` (last run failed to capture).
- Runnable standalone (`bun run coverage`) and invoked at the end of a capture run.

### 4.3 Capture runner — `tests/wiki-screenshots/capture.spec.ts`

A Playwright test that iterates `SHOTS`:

1. Resolve `role` → load that user's `storageState` (`.auth/<email>.json` from
   the existing setup project).
2. Create context, inject cookie `NEXT_LOCALE=en` (domain `localhost`).
3. Set viewport (default 1440×900), disable CSS animations/transitions and
   `prefers-reduced-motion` for stable images.
4. Substitute `seedId` into the path, `goto`, await `waitFor` (or `networkidle`).
5. `page.screenshot({ fullPage: true, path: <output> })`.
6. On navigation/seed failure: record `skipped` with reason, continue (do not
   fail the whole run).

- **Output dir:** `WIKI_ASSETS_DIR` (default
  `../carmen-wiki/assets/screenshots/inventory`), file
  `<module>/<slug>.png`.
- Registered as a new project in `playwright.config.ts` with
  `dependencies: ["setup"]`.

### 4.4 Auth/locale helper — `tests/wiki-screenshots/locale.ts`

Small helper to add the `NEXT_LOCALE=en` cookie to a context. Reuses
`authFile(email)` from `tests/fixtures/auth.paths.ts`. No new login logic.

### 4.5 Manifest bootstrap — `tests/wiki-screenshots/seed-manifest.ts`

One-time generator: reuses the coverage checker's route discovery to emit an
initial `manifest.ts` with every static route as an `Admin` entry, `module`/`slug`
inferred from the path, dynamic routes included but commented with a
`// TODO seedId` marker. Run once, then the file is hand-curated and committed.

## 5. Data flow

```
seed-manifest.ts ──(one-time)──► manifest.ts (curated, committed)
                                      │
auth.setup.ts ──► .auth/<role>.json   │
                                      ▼
                              capture.spec.ts
                    (load storageState + NEXT_LOCALE=en cookie)
                                      │
                                      ▼
                       dev server localhost:3000 (EN)
                                      │
                                      ▼
        carmen-wiki/assets/screenshots/inventory/<module>/<slug>.png
                                      │
                                      ▼
                 coverage.ts ──► carmen-wiki/.specs/screenshot-coverage.md
```

## 6. Error handling

| Failure | Behaviour |
|---------|-----------|
| Login fails | Handled by existing `setup` project retry (`retries: 2`). |
| Page/seed won't load | Mark entry `skipped` + reason in report; run continues. |
| Manifest path matches no real route | Coverage checker flags `stale`. |
| Real route absent from manifest | Coverage checker flags `missing`. |
| Dynamic route, no `seedId` | Coverage checker flags `needs-seed`; runner skips. |

## 7. Configuration (env)

| Var | Default | Purpose |
|-----|---------|---------|
| `E2E_BASE_URL` | `http://localhost:3000` | Frontend URL (existing). |
| `E2E_FRONTEND_DIR` | `../carmen-inventory-frontend-react` | For webServer + route discovery (existing). |
| `WIKI_ASSETS_DIR` | `../carmen-wiki/assets/screenshots/inventory` | Screenshot output root. |
| `WIKI_SPECS_DIR` | `../carmen-wiki/.specs` | Coverage report output. |

## 8. Out of scope (YAGNI)

- No TH capture (EN images reused across locales).
- No Platform admin capture.
- No visual-diff / screenshot regression testing.
- No automated DB seeding — relies on data already present in the target env plus
  hand-supplied `seedId` values.
- No wiki-page edits to embed the images (separate follow-up task).

## 9. Open follow-ups (not this task)

- Embedding captured images into specific wiki pages (EN+TH) is a later content task.
- Per-role coverage of approval/workflow screens beyond the initial overrides can
  grow the manifest incrementally.
