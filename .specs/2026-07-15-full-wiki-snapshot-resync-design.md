# Full Wiki Snapshot Re-sync — Design (2026-07-15)

## Goal

Bring **both books** (Inventory + Platform, EN + TH) back in line with the current
state of the source repositories, refresh affected screenshots, update both
coverage checklists, and push the result to the dev Wiki.js instance.

Last wiki sync: **2026-06-25** (commit `207d842`). Source deltas since then:

| Repo | Commits since 2026-06-18 |
|------|--------------------------|
| carmen-inventory-frontend-react | 350 |
| carmen-platform | 327 |
| carmen-turborepo-backend-v2 | 446 |
| carmen-inventory-frontend-e2e | 73 |
| micro-report | 27 |
| carmen-turborepo-backend-bruno | 9 |
| micro-data | 7 |
| micro-cronjobs | 0 |

## Approach (chosen)

**Snapshot verification of every page** (approach B). Do not reconstruct changes
from git history; instead verify each wiki page's claims directly against the
*current* source code. Rationale: chosen by the user for thoroughness — catches
drift that predates the last sync window, at the cost of more reading.

Git diffs may still be used as a *hint* for where to look, but the source of
truth for every edit is the current code, per CLAUDE.md precedence:
**implementation + e2e tests > `../carmen/docs/` > memory/speculation**.

## Scope

| Book | Modules | EN pages | TH pages |
|------|---------|----------|----------|
| Inventory (`en/inventory/`, `th/inventory/`) | 17 | 233 | 233 |
| Platform (`en/platform/`, `th/platform/`) | 11 | 38 | 38 |
| Root pages (`home.md`, `inventory.md`, `platform.md` × 2 locales) | — | 3 | 3 |

Plus: curated screenshot set (184 PNGs), `.specs/process-coverage-checklist.md`,
`.specs/platform-coverage-checklist.md`, dev Wiki.js content + nav.

New features/modules found in source with **no wiki page at all** get full new
pages (sub-page template, EN + TH, §7 link lists, nav entries) — not stubs.

## Phases

### Phase 0 — Setup
- Work branch: `docs/resync-2026-07-15` (this branch).
- Build a per-module source map: frontend module directory + route entries
  (`router.tsx`), Bruno collection paths, e2e spec paths, backend
  controllers/services where behavior claims need them; `micro-report` /
  `micro-data` for the reporting-audit module. Platform book maps to
  `carmen-platform` routes/components.
- Create tracking log `.specs/resync-2026-07-15-progress.md`: one row per
  module — pages verified, claims fixed, new pages, screenshot routes flagged.

### Phase 1 — Inventory book snapshot (17 modules, sequential)
Per module:
1. Read current source for the module (frontend first, then Bruno/e2e/backend
   as claims require).
2. For each EN page under the module, verify every checkable claim: route
   paths, field/button names, status flows, permission keys, API request/response
   shapes, edge-case tables. Fix inline.
3. Frontmatter: bump `date` to now; never touch `dateCreated`.
4. Mirror fixes to the TH page semantically (no full re-translation). Because
   this is snapshot mode, also scan the TH page for its own drift against EN
   structure.
5. Flag routes whose UI changed (for Phase 4) in the tracking log.
6. Run `.specs/verify_frontmatter.py`; commit per module.

### Phase 2 — Platform book snapshot (11 modules)
Same procedure against `carmen-platform`. Known recent themes: RBAC era
continues, `feat/env-modes` merged 2026-07-15.

### Phase 3 — New pages
For source routes/features with no wiki page: create EN page from the module's
sub-page template (PR module is the reference), mirror TH, add to the module's
§7 sub-page list using absolute-URL markdown links (`[Display](/en/...)` — pipe
wikilinks don't render), schedule nav entry for Phase 6.

### Phase 4 — Screenshots (deferrable)
- Build the route→curated remap first — the capture pipeline's route output and
  the curated embed set are not linked (known trap).
- Recapture **only** routes flagged in Phases 1–3 as visually changed; do not
  blanket-recapture all 184.
- Preconditions: live backend (`BACKEND_URL` in `.env` verified), tenant
  **zebra**, stale `.auth` cache cleared first (silent login failure otherwise).
- If the backend is down: log in the tracking file, defer this phase; it must
  not block Phases 5–6.

### Phase 5 — Coverage checklists
Update `.specs/process-coverage-checklist.md` (Inventory, was 79%) and
`.specs/platform-coverage-checklist.md` (was 98%) — statuses, counts, and new
rows for pages added in Phase 3.

### Phase 6 — Dev Wiki.js sync
Push all edited/new pages to `http://dev.blueledgers.com:3987/`, update nav for
new pages, spot-check rendering in the browser (both locales). Retry per page
on push failure; log persistent failures.

## Error handling

- Wiki claim not found anywhere in source → rewrite from current source; note
  the discrepancy in the tracking log.
- Ambiguous behavior → e2e/implementation wins over `carmen/docs`.
- Backend unavailable for screenshots → defer Phase 4, continue.
- Wiki.js push failure → per-page retry, then log and continue.

## Verification (definition of done)

1. `verify_frontmatter.py` passes on every touched page.
2. Internal links (`/en/...`, `/th/...`) resolve to existing pages.
3. EN/TH page counts remain mirrored per module.
4. Coverage checklist numbers match actual page states.
5. Spot-checked rendering on dev Wiki.js for a sample of edited pages per book.
6. Work lands as a PR from `docs/resync-2026-07-15` (same flow as PR #4).

## Out of scope

- micro-cronjobs (0 commits — skip).
- Restructuring books/modules; deferrals recorded in memory stay deferred.
- Blanket screenshot recapture of unchanged routes.
