# Spec: Inventory wiki resync → carmen-inventory-frontend-react

**Date:** 2026-06-18
**Branch:** `docs/resync-react-stack-2026-06-18`
**Status:** Approved design — ready for implementation plan

## Background

The Carmen inventory frontend was ported from the Next.js App Router app
`../carmen-inventory-frontend/` to a Vite + React Router 7 SPA at
`../carmen-inventory-frontend-react/` (the "stack change").

A prior effort (merged 2026-06-15, `e536ac6`) already completed the **path +
stack-label** layer: every wiki reference was repointed to `-react`, the tech
stack in `CLAUDE.md` was corrected to "Vite + React SPA / React Router", and the
screenshot route remap was applied. Verification on 2026-06-18 confirmed **0 bare
`carmen-inventory-frontend` references** remain outside the two intentional meta
documents, and only **2 deliberate historical annotations** ("legacy Next.js
repo") survive in the inventory book.

What was **not** verified at the detail level, and is the subject of this spec:

1. Whether every route documented in the inventory book matches the actual route
   table in `-react/routes/router.tsx` (126 path entries, nested data router).
2. Whether wiki prose that describes frontend infrastructure reflects the new SPA
   architecture (no server, http-client proxy rewrite, in-memory auth).
3. Whether documented screen/component behavior still matches the ported app.

Concrete drift already found during scoping (proves the work is non-empty):
- `/inventory-management/period-end-process` (wiki) vs actual `/inventory-management/period-end` (+ `/review`).
- `/store-requisition/stock-replenishment` (wiki prose) vs actual `/store-operation/stock-replenishment`.
- `/operation-plan/equipment-category` vs `/operation-plan/recipe-equipment-category` (both appear in one page).

## Goal

Resync the **inventory book** (`en/inventory/**` + `th/inventory/**`) so its
routes, frontend-architecture statements, and screen-behavior descriptions match
the `-react` app as the source of truth. Fix genuine drift only; do not expand
scope into writing new pages or filling pre-existing content gaps.

## Non-goals (explicit scope boundaries)

- **Platform book** (`en/platform/**`, `th/platform/**`) — references the separate
  `carmen-platform` repo, which did not change. Out of scope.
- **Filling TODO / coverage gaps** that predate this change (e.g. physical-count
  and spot-check behavior sections tracked at 0% in the process-coverage
  checklist). Those are separate work, tracked elsewhere. This resync only
  corrects content that drifted *because of the stack change*.
- **Rewriting** otherwise-correct pages, re-toning, or restructuring.
- The 2 intentional historical "legacy Next.js repo" annotations stay as-is.

## Sources of truth (in priority order)

1. `-react/routes/router.tsx` — authoritative route table.
2. `-react` components / `lib/` (`lib/http-client.ts`, `lib/auth/*`) — behavior + architecture.
3. `-react/CLAUDE.md` — summary of architectural deltas from the source app.
4. `../carmen/docs/` — ERP concepts (stack-agnostic; only consulted if a behavior
   question is conceptual, not stack-driven).

When implementation and these sources disagree, code wins.

## Approach — three layered passes (approach "B")

Passes are ordered cheap→expensive so the bulk of coverage is banked early and the
expensive judgment work is bounded by what the earlier passes flag. Each pass is a
clean, separately-reviewable commit set.

### Pass 1 — Route-table verification (mechanical, global)

1. Build the **authoritative full-route list** from `router.tsx` by concatenating
   ancestor `path` segments down the nested data-router tree (e.g.
   `inventory-management` + `physical-count/:id/entry` →
   `/inventory-management/physical-count/:id/entry`). ~126 leaves.
2. Extract route strings referenced in the inventory book. **Filter out
   non-route paths**: `/screenshots/...`, `/en/...`, `/th/...`, and asset/image
   links. Only app routes count.
3. Classify each documented route:
   - **stale** — not present in the app → correct it to the real route.
   - **param-style** — old-style segment (`/detail`, `/index`) vs the app's
     `:id` / index convention → normalize to match `-react`.
   - **gap** — an app route with no wiki page → **log only**, do not author a new page.
4. Apply every fix to the **EN and TH** copies together.

### Pass 2 — Architecture deltas (small, targeted)

Add or correct only the wiki sentences that describe frontend infrastructure, to
reflect the new SPA model:
- **No server** — static bundle on S3/CloudFront; the browser calls the backend
  directly. No SSR, no server components, no route handlers.
- **http-client proxy rewrite** — `lib/http-client.ts` rewrites
  `/api/proxy/<rest>` and `/api/external/<rest>` → `${BACKEND_URL}/<rest>` and
  attaches `Authorization: Bearer` + `x-app-id`.
- **Auth** — access token held in memory (`lib/auth/token-store.ts`), refresh
  token in localStorage (`lib/auth/refresh-token-storage.ts`); boot order in
  `main.tsx` is `loadRuntimeConfig() → refreshTokens() → render`; `RequireAuth`
  redirects to `/login` when the token store empties.

Method: grep the inventory book for infra keywords (`server`, `endpoint`,
`proxy`, `auth`, `token`, `API`), keep only sentences that describe a *mechanism*
that is now wrong, and correct those. Do **not** touch ERP behavior prose.

### Pass 3 — Screen-behavior resync (per-module, diff-driven)

- **Signal-driven, not blanket re-read.** A module is read in depth only when
  Pass 1 flagged a route change for it **or** it appears in `-react` git history
  as a behavioral change (e.g. doc_version optimistic concurrency, location
  delivery-point display, server-error placeholder stripping). For those, read
  the actual component and verify/fix the behavior the wiki describes.
- Modules with no signal get a **spot-check** confirming the `-react` claim that
  "hooks/patterns are identical to the source app", recorded as no-change.
- Fix genuine drift only — no rewrites.

## Conventions

- **Frontmatter:** update `date` on every edited page; never touch `dateCreated`.
- **EN + TH mirroring:** every content change is applied to both locale copies.
- **Numbered section hierarchy, tables, pseudo-code, ฿ currency** — preserve
  existing wiki conventions (per `CLAUDE.md`).

## Tracking

Progress log at `.specs/resync-react-stack-2026-06-18.md`, one row per module:
routes-fixed · arch-deltas-applied · behavior-status (verified / fixed /
no-change) · notes. Mirrors the format of the prior resync logs.

## Finishing (confirm before each external step)

1. Sync edited pages to the dev Wiki.js instance (`dev.blueledgers.com:3987`) to
   verify rendering.
2. Open a PR from `docs/resync-react-stack-2026-06-18` into `main`.

## Success criteria

- Every app route documented in the inventory book matches `router.tsx` (no stale
  or wrong-prefix routes); unmatched app routes are logged as gaps.
- No wiki sentence describes a Next.js-era frontend mechanism (SSR, server
  components, server route handlers) as current; the SPA model is stated where
  relevant.
- Every module appears in the tracking log with a behavior status.
- EN and TH stay mirrored; frontmatter `date` updated on edited pages only.
