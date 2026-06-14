# Design: Update carmen-wiki Frontend Reference (Next.js → React/Vite)

**Date:** 2026-06-15
**Status:** Approved (pending spec review)

## Goal

Repoint every documentation reference in **carmen-wiki** from the legacy Next.js
repo `carmen-inventory-frontend` to the new React/Vite repo
`carmen-inventory-frontend-react`, **remapping paths** for the new repo's
structure, and verifying — with a **full leaf-file existence check** — that no
remaining reference points at a path that does not exist in the new repo.

## Context

- `carmen-inventory-frontend-react` is a **separate GitHub repo** (a Next.js →
  Vite + React SPA rewrite), not a rename. The old repo still exists.
- carmen-wiki treats the inventory frontend as a **source of truth** for screen
  behaviour; its pages cite specific frontend file paths (routes, components,
  hooks, types, constants).
- **283 bare `carmen-inventory-frontend` references** span **147 files**, almost
  all under the parallel `en/` and `th/` content trees plus `.specs/`,
  `docs/`, `CLAUDE.md`, and `README.md`.
- `-e2e` and `-react` suffixed references are a **different concern**:
  `carmen-inventory-frontend-e2e` was not renamed and is out of scope.
- **Structure delta** between old and new repo:
  - Old (Next.js App Router): `app/(root)/(protected)/<route>` route groups.
  - New (Vite SPA): flat `routes/<route>` — **no `app/`, no `(root)`/`(protected)`
    route-group segments**.
  - Shared top-level dirs are **unchanged in name**: `components/`, `hooks/`,
    `types/`, `constant/`, `lib/`, `utils/`.

## Mapping rule (apply in this order)

1. `…/app/(root)/(protected)/` → `…-react/routes/`
2. `…/app/(root)/` → `…-react/routes/`
3. `…/app/` and bare `…/app` (no trailing path) → `…-react/routes`
4. `carmen-inventory-frontend/` → `carmen-inventory-frontend-react/`
   (the **trailing slash** prevents matching `carmen-inventory-frontend-e2e/`)
5. Prose tech descriptors: `Next.js inventory UI — App Router` →
   `Vite + React SPA` (in `README.md` and `CLAUDE.md`).

Order matters: the most specific path prefix (rule 1) must run before the more
general ones (rules 2–4), or a partial match would corrupt the path.

## Scope — verification and the four miss categories

A **dry-run leaf-existence script** extracts every distinct referenced path,
applies the mapping rule, and checks the result against the
`carmen-inventory-frontend-react` filesystem. Baseline measured on
2026-06-15: **68 distinct paths, 55 resolve cleanly, 13 miss.** The 13 misses
resolve as follows.

### Category A — Route-group collapse (handled by rule 1)

`app/(root)/(protected)/procurement/purchase-request-template` and
`…/vendor-management/price-list-template` lose the `(protected)` group in the
SPA. Rule 1 maps them to `routes/procurement/purchase-request-template` and
`routes/vendor-management/price-list-template` — **both confirmed to exist**.
No manual work beyond applying the ordered rule.

### Category B — Dashboard sub-pages restructured (manual remap)

The old per-route sub-dashboards were merged into components. References of the
form:

```
app/(root)/dashboard/{grn,pr,po,sr,inventory,main}/page.tsx
```

(12 explicit references — 2 each — plus the brace-shorthand mention
`app/(root)/dashboard/{main,pr,po,grn,inventory,sr}/page.tsx`) must be **manually
remapped** to:

```
routes/dashboard/_components/dashboard-{grn,pr,po,sr,inventory,main}.tsx
```

All six target component files are **confirmed to exist** in the new repo. This
is a content restructure, not a path rename, so the generic rule cannot derive
it — it is an explicit substitution.

Note: the brace-shorthand references that already point at
`app/(root)/dashboard/_components/dashboard-{…}.tsx` and
`app/(root)/dashboard/mock/{…}.ts` map **cleanly** under rule 2 (the
`_components/` and `mock/` dirs exist in `routes/dashboard/`); only the
`dashboard/<sub>/page.tsx` form needs the Category B substitution.

### Category C — Bare `app` (handled by rule 3)

`…/app` with no trailing path (e.g. "Frontend screens: `…/app/`") maps to
`…-react/routes`, which exists.

### Category D — Historical spec, old-repo only (rename + annotate)

`docs/superpowers/specs/2026-05-22-widget-rewrite-design.md` exists **only in the
old repo**. Apply the repo-token rename (rule 4) **and** append an inline note,
e.g. `_(historical; this spec lived in the carmen-inventory-frontend Next.js
repo)_`, so the path is not left implying the file exists in the new repo. This
mirrors the handling the backend `update-frontend-reference` plan uses for its
archived widget docs.

## Bilingual parallelism

`en/` and `th/` are parallel content trees. **Every edit must be mirrored across
both.** Thai-language prose may surround a path token; only the path/repo token
changes, never the surrounding Thai text.

## Out of scope

- `carmen-inventory-frontend-e2e` references (repo not renamed).
- The old repo's own files and the `-react` repo's migration-history docs.
- `.specs/screenshot-coverage.md`'s "auto-generated by … in
  carmen-inventory-frontend-e2e" line (e2e repo).
- Any change to the frontend repos themselves.
- Re-verifying wiki prose accuracy beyond the path/repo/tech-stack tokens.

## Verification (completion gate)

1. **Leaf-existence script** reports **zero unresolved paths**, excluding the
   single annotated Category D historical reference.
2. `grep -rn "carmen-inventory-frontend" en th docs .specs CLAUDE.md README.md
   | grep -v "carmen-inventory-frontend-react" | grep -v "carmen-inventory-frontend-e2e"`
   returns **no output**.
3. No `app/(root)` or `(protected)` segment remains in any frontend path
   (`grep -rn "carmen-inventory-frontend-react/app" ...` → empty;
   `grep -rn "carmen-inventory-frontend-react/routes/(protected)" ...` → empty).
4. `en/` and `th/` show the **same number** of `-react` occurrences (parallel
   trees stayed in sync).

## Relationship to the backend work

The `carmen-turborepo-backend-v2` repo already has its own approved spec + plan
(`docs/superpowers/specs/2026-06-14-update-frontend-reference-design.md`) on
branch `docs/update-frontend-reference`, covering 5 backend docs. That work runs
**independently** and is **not re-designed here**. carmen-platform (the admin
dashboard repo) has **no** references and needs no change.
