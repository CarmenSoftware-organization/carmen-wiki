# Design: Platform `business-units/` Sub-Pages

**Date:** 2026-05-19
**Status:** Approved (user)
**Scope:** Expand the two stub sub-pages under `en/platform/business-units/` into full reference pages, reusing the conventions established by the `users/` and `clusters/` rounds.
**Predecessors:**
- `.specs/2026-05-19-platform-users-sub-pages-design.md` — established the Platform-book sub-page convention.
- `.specs/2026-05-19-platform-clusters-sub-pages-design.md` — validated the convention on a second module and added the `permissions.md` shape for role-gated modules (not needed here — BU is open-access).

The Platform book's `business-units/` folder carries two stub sub-pages:
- `en/platform/business-units/data-model.md` (24 lines)
- `en/platform/business-units/ui-screens.md` (24 lines)

No `permissions.md` is needed: `/business-units*` routes carry `PrivateRoute` without an `allowedRoles` prop (open to any authenticated platform user), matching the access model of `users`. The role gate concept lives in [[auth-roles]] and [[clusters]]/permissions.

---

## 1. Goals

1. **Two full sub-pages** for the `business-units` module, in English, each in the 150-300 line range (with the same density-over-padding allowance the clusters round applied at 139-194 lines).
2. **No edits to the landing** (`en/platform/business-units.md`) during the implementation window. A landing stub-cleanup patch may follow if the landing carries `(stub — in progress)` annotations.
3. **Reuse the convention** established by the two previous rounds. Where this spec stays silent, the convention applies.
4. **Cover the BU's three non-trivial schema features:** the M:N `tb_business_unit_tb_module` join (BU↔module activation), the BU-config array semantics, and the formatting/locale fields cluster (date format, currency, decimal, timezone).

## 2. Non-goals

- TH mirror (deferred to a dedicated future round across all completed EN pages).
- Screenshots (batched across the Platform book).
- The remaining `report-templates/` module — separate spec.
- A `permissions.md` for business-units — not needed; the module is open-access.
- A formal "Platform sub-page template" spec — still deferred. The convention is being validated module by module.

## 3. Sub-page shape

Each sub-page begins with the Wiki.js YAML frontmatter already in the stub (keep `dateCreated`, update `date` to `'2026-05-19T17:30:00.000Z'`), then `# Business Unit — <Axis>`, then an At a Glance callout, then numbered sections beginning at `## 1. Overview`. Stub residue (`## 1. At a Glance` heading, `## 3. TODO` block) is removed.

### 3.1 `data-model.md` — schema view

Mirrors `en/platform/clusters/data-model.md` shape (which mirrors users/data-model). Sections:

1. **Overview** — entities this module owns:
   - `tb_business_unit` (primary)
   - `tb_business_unit_tb_module` (M:N BU↔module join; activates which modules each BU can use)
   - `tb_user_tb_business_unit` (cluster-side already documented in [[users]] — restate briefly with cross-link)
   - `tb_module` (referenced; full doc belongs to a future modules sub-page if one ever exists — here only the FK side)

   Position relative to: [[clusters]] (parent — `tb_business_unit.cluster_id`), [[users]] (M:N user-BU assignments).

2. **Entities**:
   - `tb_business_unit` — full field table from Prisma row-by-row. Cover identity (id, code, name, cluster_id), formatting/locale block (date_format, time_format, currency_code, decimal fields, timezone, language), DB connection block (db_connection, db_username, db_password, db_name, db_host, db_port — verify exact field names), max_license_users, is_active, soft-delete trio, info JSON column, the standard audit columns, plus anything else.
   - `tb_business_unit_tb_module` — full field table (likely: id, business_unit_id, module_id, is_active, audit columns). Document the M:N join semantics: which modules are activated per BU.
   - `tb_user_tb_business_unit` — brief; cross-link to [[users]]/data-model for the full field table. Document only the BU-side relevance: per-BU role (`enum_user_business_unit_role`), `is_default` flag.
   - `tb_module` — brief; FK side. Full module catalog doc is out of scope for this round.

3. **Relationships** — bullet list of FK relations with cardinality from `@relation` directives.

4. **Enums** — `enum_user_business_unit_role` (already covered in users/data-model — restate values and cross-link). Any `tb_business_unit`-local enum (e.g. status, type) if Prisma declares one.

5. **The `info` JSON column** — if `tb_business_unit.info` is present, document the JSON shape used by the SPA (read from `BusinessUnitEdit.tsx`). The plan-template's "config array (key/value pairs)" hint from the stub suggests there's a structured config inside `info` or a separate column — verify which.

6. **Divergences from carmen-platform SPA shape** — compare Prisma `tb_business_unit` against the `BusinessUnit` TS type in `src/types/index.ts` (and any `BusinessUnitFormData` interface in `BusinessUnitEdit.tsx`). Table or "No divergences detected as of 2026-05-19."

7. **References** — Prisma path (primary), SPA paths (secondary), cross-links to [[clusters]] (parent), [[users]] (M:N join full doc), sibling [UI Screens](./ui-screens.md).

**Source-of-truth callout** at top, identical pattern to clusters/data-model.

### 3.2 `ui-screens.md` — interaction view

Mirrors `en/platform/clusters/ui-screens.md` adapted for the BU surface. `BusinessUnitEdit.tsx` is the largest edit page in the Platform admin product (1785 lines) — expect more sections / dialogs / collapsible groups than clusters or users. Sections:

1. **Overview** — two-screen pattern; BU edit page's collapsible form sections (the stub hints at this).

2. **`BusinessUnitManagement`** (`/business-units`) — list page:
   - 2.1 Layout
   - 2.2 Filters (Sheet panel) — verify filter set (likely cluster filter + active/inactive + show-soft-deleted)
   - 2.3 Header actions (Export, Add BU, plus any others)
   - 2.4 Row actions (Edit, Delete soft, hard-delete if present)
   - 2.5 Audit columns

3. **`BusinessUnitEdit` — create mode** (`/business-units/new`) — form sections. The route accepts `?cluster_id=<id>` query param (per [[clusters]]/ui-screens §4.2); document whether the create form pre-selects the cluster from this param. Submit endpoint, post-create navigate destination.

4. **`BusinessUnitEdit` — view/edit mode** (`/business-units/:id/edit`) — collapsible form sections. Document each section by name; describe what fields belong to each. The actual sections are discovered from `BusinessUnitEdit.tsx`; the implementer enumerates them. Likely groupings: Identity, Cluster, Formatting/Locale, DB Connection, Modules (M:N from `tb_business_unit_tb_module`), Users (M:N from `tb_user_tb_business_unit`, read-only or with row controls).

5. **Dialogs** — enumerate every dialog reachable from the BU edit page (Add User to BU, Edit BU User, Remove BU User, Module toggle confirm, Soft Delete confirm). Cite source line numbers.

6. **Persisted UI state** — list every `localStorage` key the list page writes. Format matches users/ui-screens §6 (Key / Stored type / Persists table).

7. **Screenshots** — deferred — inline `> **TODO:**` callout pointing at `.specs/2026-05-17-screenshots-coverage-checklist.md`.

8. **References** — `src/pages/BusinessUnitManagement.tsx`, `src/pages/BusinessUnitEdit.tsx`, `src/services/businessUnitService.ts`, `SITEMAP.md`, cross-links to [[clusters]] (parent), [[users]] (user-assignment surface), [Data Model](./data-model.md).

## 4. Conventions inherited from `users/` and `clusters/` (not re-derived here)

- Topical sub-page names, no numeric prefix.
- Backend Prisma > SPA source > docs/OVERVIEW.md.
- At-a-Glance: `>` callout (NOT heading), segmented with `&nbsp;·&nbsp;` and bold labels.
- Cross-link convention: `[[module-slug]]` for module landings; `[Label](./sibling.md)` for sibling sub-pages.
- Pseudo-code: ```` ``` ```` (no language tag) for diagrams and code-shape blocks.
- Stub residue removal: rewrite entirely; remove the bullet At-a-Glance heading and `## N. TODO` block.
- Frontmatter: keep `dateCreated`; update `date` to implementation timestamp.
- Inline `> **TODO:**` callout permitted ONLY in `ui-screens.md` Screenshots section.

## 5. Verification gates

Identical to the previous rounds, per file:

1. `python3 .specs/verify_frontmatter.py <file>` prints `OK:`.
2. Wiki.js render check on `dev.blueledgers.com:3987/en/platform/business-units/<page>` confirms callout, sections, and tables render correctly.
3. No broken `[[slug]]` cross-links; sibling cross-links use the `./relative.md` form.
4. No `(/th/` cross-locale links.
5. No stub residue (`## N. TODO`, `## N. At a Glance` headings absent).
6. Line count 150-300 per file (lower-floor density-over-padding allowance from clusters round applies — going as low as 135 is OK if the content density warrants).
7. Every factual claim cites a specific path under `../carmen-platform/` or `../carmen-turborepo-backend-v2/`.
8. The placeholder-syntax grep (`<[A-Z][a-z]+|<[a-z-]+>`) may flag JSX component names in code spans (e.g. `<BusinessUnitEdit>`); confirm any flagged match is a legitimate JSX reference, not a leftover `<placeholder>` template token.

Plus a final Task 3 cross-check across both sub-pages and an optional landing stub-cleanup patch (analogous to commit `12c8c50` for users and `db06f63` for clusters) if `en/platform/business-units.md` carries `(stub — in progress)` annotations.

## 6. Deferrals

- TH mirror of both pages.
- Screenshots.
- `report-templates/` module.
- Any backend / SPA fixes surfaced as divergences (those are documentation findings, not wiki tasks).

## 7. Out of scope

- Edits to the `business-units.md` landing during the implementation window (the optional stub-cleanup patch is a separate post-implementation commit).
- The full `tb_module` catalog (a future modules sub-page or a `master-config` spec — out of scope here).
- Cross-module concerns — e.g. how BU formatting fields propagate into inventory transactions.

## 8. Open questions

None at design time. The exact section list inside `BusinessUnitEdit.tsx` (collapsible form sections) is an implementation-time discovery — not a design question.
