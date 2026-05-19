# Platform Book — Sub-Page Template

**Date:** 2026-05-19
**Status:** Approved (user)
**Scope:** Codifies the sub-page convention that solidified across three independent Platform-book module rounds. Future per-module specs reference this document instead of re-deriving the convention.

**Predecessors** (the three rounds that established this convention):
- `.specs/2026-05-19-platform-users-sub-pages-design.md` — first instance; 3 sub-pages (data-model, lifecycle, ui-screens)
- `.specs/2026-05-19-platform-clusters-sub-pages-design.md` — second instance; introduced `permissions.md` for role-gated modules; 3 sub-pages
- `.specs/2026-05-19-platform-business-units-sub-pages-design.md` — third instance; 2 sub-pages (the modules-activation join `tb_business_unit_tb_module` exists in schema but has no SPA surface and so does not get a sub-page); reused everything else without revision

After three modules with no convention drift, the pattern is stable enough to extract.

---

## 1. When this template applies

This template applies to any module in the Platform book (`en/platform/<module>/`) that needs sub-pages. A module qualifies for sub-pages when its landing page is dense enough that further elaboration into axis-specific reference pages would help developers and QA engineers.

The Platform book's "module landing → sub-pages elaborate beneath" pattern is fixed. The landing is the canonical overview; sub-pages dive deeper along specific axes and should NOT restate what the landing already covers.

A module that exists only as a single landing (e.g. `auth-roles`, `profile`) does not need sub-pages — its landing's Section 7 states "This module is a single page; see the parent [Platform book index](/en/platform)" and the convention here does not apply.

## 2. Sub-page shapes

Sub-pages are named topically (no numeric prefix). Two shapes are universal across modules; three are module-specific.

### 2.1 Universal: `data-model.md`

The schema view. Every module that owns Prisma tables has this sub-page.

Section structure (numbered, mandatory):

1. **Overview** — 2-3 paragraphs positioning the entities this module owns, relative to neighbour modules. Brief; leave field detail to §2.
2. **Entities** — one `### N.N` sub-section per entity:
   - For entities the module **owns**: full field table (Field / Prisma Type / Nullable / Description) row-by-row from Prisma; verbatim **Constraints** (`@id`, `@@unique`, FK targets with `onDelete`/`onUpdate`) and **Indexes** (`@@index`).
   - For entities the module **references** (full doc lives elsewhere): one-paragraph cross-link only; document just the perspective relevant to this module.
   - When a field table grows beyond ~20 rows, add bold separator rows to group fields by purpose (Identity / Status / Locale / Audit / etc.). Group names should match the Overview paragraph's groupings.
3. **Relationships** — bullet list of FK relations with cardinality (1:M, M:N) derived from Prisma `@relation` directives.
4. **Enums** — list each enum's values plus one-line meaning. Cross-link to sibling modules where the same enum is fully covered.
5. **Divergences from carmen-platform SPA shape** — table comparing Prisma against the SPA TS types (`src/types/index.ts`, any module-specific `<X>FormData` interface). If aligned: write "No divergences detected against carmen-platform SPA shape as of <YYYY-MM-DD>." Include the Notes column when divergence exists, calling out developer-facing implications (e.g. "use `BusinessUnitConfig[]` not raw `Json`").
6. **References** — Primary (Prisma path), Secondary (SPA paths), Cross-links to siblings and related-module landings.

**Source-of-truth callout** at the top of every data-model page, immediately below the At-a-Glance callout (before §1):

```markdown
> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.
```

### 2.2 Universal: `ui-screens.md`

The interaction view. Every module with one or more SPA pages has this sub-page.

Section structure (numbered, mandatory):

1. **Overview** — 1-2 paragraphs covering the screen pattern (typically two-screen: list + create/view/edit), edit-page layout (single card / 3-column grid / N collapsible sections), and any module-specific UI quirks.
2. **`<ListComponent>`** (`/<module>`) — list page. Sub-sections:
   - 2.1 Layout
   - 2.2 Filters (Sheet panel)
   - 2.3 Header actions
   - 2.4 Row actions
   - 2.5 Audit columns
3. **`<EditComponent>` — create mode** (`/<module>/new`)
4. **`<EditComponent>` — view/edit mode** (`/<module>/:id/edit`) — one `### N.N` sub-section per form section (label match the SPA source). For modules with many sections (BU has 9), each subsection covers its fields, any locked-in-edit-mode fields, and any cross-page navigation it triggers.
5. **Dialogs** — one `### N.N` sub-section per dialog. Trigger, fields/UX, validation, endpoint.
6. **Persisted UI state** — table (Key / Stored type / Persists) listing every `localStorage` key written by the list page; verbatim names from source. State explicitly when the edit page does not persist UI state.
7. **Screenshots** — deferred until the Platform-wide screenshots batch. The section body is a single inline callout:
   ```markdown
   > **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.
   ```
8. **References** — SITEMAP.md, the SPA page sources, the service file, cross-links.

### 2.3 Module-specific: `lifecycle.md` (operations view)

When a module's primary value is a set of operations (CRUD plus side-effects like Keycloak sync, password reset, soft-delete cascade), document them here. The `users` round established this shape.

Section structure (mandatory sections in this order; module-specific operations slot in as numbered sections):

1. **Overview** — operations covered + explicit absences (e.g. "no SSO, MFA, OAuth, email-link password reset").
2. **Create flow** — trigger, endpoint, body shape, success/failure behaviour.
3. **Edit flow** — trigger, endpoint, locked-after-create fields, mode toggle.
4. **Activate / Deactivate** — `is_active` semantics, sign-in effect, independence from soft-delete.
5. **Soft delete vs. Hard delete** — endpoint, dialog UX, server-side effects, FK cascade behaviour (verify `onDelete` in Prisma).
6. **Module-specific operations** — anything else (password reset, Keycloak sync, etc.). Each gets a `## N.` section.
7. **Cross-entity side effects** — where this module's mutations affect rows owned by other modules.
8. **References** — service file, SPA page sources, Prisma path for FK cascades, cross-links.

### 2.4 Module-specific: `permissions.md` (role-gate view)

When a module's routes carry `allowedRoles` on `PrivateRoute`, document the gate story. The `clusters` round established this shape.

Section structure (mandatory):

1. **Overview** — why this module is role-gated; contrast with open-access modules.
2. **Route guards** — table of every route in the module with its `allowedRoles` array and source line citation.
3. **Effective access matrix** — table covering ALL `enum_platform_role` values × can-sign-in × can-reach-this-module. Include a one-sentence reading guide before the table.
4. **Bootstrap exception** — the `userCount <= 1` shortcut in `AuthContext.hasRole`. Document the `null` vs `<= 1` vs `> 1` cases separately.
5. **AccessDenied behaviour** — render path on role-fail (inside Layout) vs auth-fail (redirect to /login).
6. **Sidebar filter** — `Layout.tsx` `NavItem[]` filter. State explicitly that the sidebar role list and the route guard role list are the same (or document the divergence as a bug).
7. **Within the surface** — whether individual buttons / fields are additionally gated by role. Most Platform modules are NOT additionally gated; document this explicitly to set tester expectations.
8. **References** — `src/App.tsx`, `src/context/AuthContext.tsx`, `src/components/PrivateRoute.tsx`, `src/components/Layout.tsx`, Prisma `enum_platform_role`, cross-links to `[[auth-roles]]` and `[[users]]`.

### 2.5 Module-specific: `xml-spec.md` (data-format view)

When a module has a non-trivial data-format that the SPA edits (e.g. `report-templates` carries XML schemas in Dialog and Content fields), document the format here. This shape is not yet validated by a real implementation — the `report-templates` round will refine it.

Provisional structure (subject to revision when first implemented):

1. **Overview** — what data formats this module owns, where they are stored, how the SPA edits them.
2. **Format A** (e.g. Dialog XML) — root element, child structure, attribute conventions.
3. **Format B** (e.g. Content XML) — same shape.
4. **Editor surface** — the SPA editor component (CodeMirror config, syntax highlighting, validation hooks).
5. **Validation** — what the SPA enforces vs what the backend enforces.
6. **References** — SPA editor source, backend parser source (if applicable), example documents.

When `report-templates/xml-spec.md` is written, revise this section based on what works.

## 3. Frontmatter

Every sub-page begins with this YAML frontmatter:

```yaml
---
title: <Module> — <Axis>
description: <One-line summary used by Wiki.js search and previews>
published: true
date: <ISO 8601 timestamp of the most recent edit>
tags: book/platform, <module-slug>, <axis-slug>
editor: markdown
dateCreated: <ISO 8601 timestamp of original creation — never change after creation>
---
```

- `title`: human-readable, em-dash separator (`—`, not `-`).
- `tags`: at minimum `book/platform`, `<module-slug>`, `<axis-slug>` (e.g. `data-model`, `lifecycle`, `ui-screens`, `permissions`).
- `date`: update on every edit; `dateCreated`: set once, never changed.
- Frontmatter verifier (`.specs/verify_frontmatter.py`) enforces the required key set and `published: true` / `editor: markdown`.

When rewriting a stub: keep `dateCreated` exactly as the stub already has it; update `date` to the implementation timestamp.

## 4. At-a-Glance callout

Every sub-page opens with a two-line blockquote callout immediately after the `# Title` H1 and before any numbered section:

```markdown
> **At a Glance**
> **<Key 1>:** <value 1> &nbsp;·&nbsp; **<Key 2>:** <value 2> &nbsp;·&nbsp; **<Key 3>:** <value 3>
```

- The first line is always exactly `> **At a Glance**`.
- The second line is a single line with `&nbsp;·&nbsp;` separators between bold-labeled segments. Use bold for the segment label; plain text for the value.
- Within a segment, when listing multiple short values, separate with ` · ` (plain centered dot, no `&nbsp;`).
- Segments are short (≤80 chars typically) and surface the page's most load-bearing facts. The reader should be able to skim the callout in 30 seconds and know what's in the page.
- The callout is NOT a numbered heading (`## 1. At a Glance` is forbidden — it is reserved for the old stub format).

Recurring segment labels by sub-page type:

| Sub-page | Typical segments |
|---|---|
| `data-model` | Tables · Enums · Audit columns · License / Status fields · Source-specific callouts |
| `ui-screens` | Screens · Edit layout · Dialogs · Access · Persisted UI state |
| `lifecycle` | Operations covered · Not in this product · Endpoints · Cross-entity effects |
| `permissions` | Gate · Bootstrap exception · On role failure · Sidebar filter · Within-surface gates |
| `xml-spec` | (TBD when first implemented) |

## 5. Cross-link conventions

| Link type | Form | Example |
|---|---|---|
| Cross-module landing (slug resolves uniquely) | `[[slug]]` | `[[users]]`, `[[clusters]]`, `[[business-units]]`, `[[auth-roles]]`, `[[profile]]` |
| Intra-module landing → sub-page (or back) | `[Label](./sub-page.md)` or `[Label](./)` | `[Data Model](./data-model.md)` |
| Sub-page → sibling sub-page | `[Label](./sibling.md)` | `[Permissions](./permissions.md)` |
| Sub-page → another module's sub-page | `[Label](../<module>/<sub-page>.md)` | `[users data-model](../users/data-model.md)` |
| Cross-book (Platform ↔ Inventory) | Same patterns; landings via `[[slug]]` when the slug is unique | `[[purchase-request]]` |

**Forbidden:** `[[data-model]]`, `[[lifecycle]]`, `[[ui-screens]]`, `[[permissions]]`, `[[xml-spec]]` — these slugs are NOT unique across modules (every module has a `data-model` sub-page) and `[[slug]]` will not resolve to a single page.

**No cross-locale links.** Wiki.js handles the locale toggle natively. EN pages do not link to `/th/...`; TH pages do not link to `/en/...`.

## 6. Source-of-truth ordering

When facts conflict between sources, use this precedence:

1. **Backend Prisma platform schema** (`../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`) — primary.
2. **Carmen-platform SPA source** (`../carmen-platform/src/`) — secondary; the consumer shape. Disagreements with Prisma go in the data-model `Divergences` section.
3. **`../carmen-platform/docs/OVERVIEW.md` and `SITEMAP.md`** — tertiary; useful for routing and the role allow-lists.

When the source actually shows behaviour that contradicts the plan or the spec's expectations (e.g. "Modules section does not exist in the SPA despite the Prisma join table"), document what you observe — not what was assumed. The implementer's job is to surface reality.

## 7. Verification gates

Run before every commit:

```bash
# Frontmatter
python3 .specs/verify_frontmatter.py en/platform/<module>/<file>.md

# At-a-Glance callout present
grep -l '^> \*\*At a Glance\*\*' en/platform/<module>/<file>.md

# Stub residue gone
grep -nE '^## [0-9]+\. TODO$' en/platform/<module>/<file>.md && echo "FAIL: TODO heading remains" || echo "OK: no TODO heading"
grep -nE '^## [0-9]+\. At a Glance$' en/platform/<module>/<file>.md && echo "FAIL: stub At-a-Glance heading remains" || echo "OK: callout-style At-a-Glance"

# No cross-locale links
grep -nE '\(/th/' en/platform/<module>/<file>.md && echo "FAIL: cross-locale link present" || echo "OK: no cross-locale link"

# No sibling-slug links
grep -n '\[\[data-model\]\]\|\[\[lifecycle\]\]\|\[\[ui-screens\]\]\|\[\[permissions\]\]\|\[\[xml-spec\]\]' en/platform/<module>/<file>.md && echo "FAIL: sibling-slug link" || echo "OK: no sibling-slug links"

# Line count
wc -l en/platform/<module>/<file>.md
```

**Target line count:** 150-300 lines. A page below 150 is acceptable when content density is genuinely high (clusters/permissions at 139 lines passed quality review — three rounds confirmed that density-over-padding is the priority). A page above 300 should be reviewed for whether it crosses into a separate concern that belongs in a sibling sub-page.

The placeholder-syntax grep (`<[A-Z][a-z]+|<[a-z-]+>`) will flag JSX component names like `<DataTable>` in code spans. These are false positives — confirm any flagged match is a legitimate JSX reference in backticks before treating as a defect.

## 8. Workflow shape

Each per-module round follows the same shape:

1. **Design spec** (`.specs/<date>-platform-<module>-sub-pages-design.md`) — references this template as predecessor; states only what's module-specific (entity list, route gates, dialog inventory). Light spec, not a re-derivation.
2. **Implementation plan** (`.specs/<date>-platform-<module>-sub-pages-plan.md`) — one task per sub-page plus a Task N for cross-checks and the optional landing stub-cleanup commit.
3. **Execution** — subagent-driven (implementer → spec reviewer → code-quality reviewer → fix subagent → re-review).
4. **Final cross-checks** — cross-link integrity, landing reference integrity, frontmatter sweep, sibling-slug consistency.
5. **Push gate** — user confirms visual render on `dev.blueledgers.com:3987` before push.
6. **Landing stub-cleanup commit** (optional) — if the landing's Section 7 carries `(stub — in progress)` annotations, remove them in a separate commit AFTER the sub-pages are committed. Pattern: commit `12c8c50` (users), `db06f63` (clusters), `68a771f` (business-units).
7. **Final cross-implementation review** — holistic subagent review of the round.

## 9. Per-module spec checklist

When writing a new per-module spec, copy and fill this checklist:

- [ ] Predecessor cites this template (`.specs/platform-sub-page-template.md`) plus any prior per-module specs that introduced sub-page shapes the new module uses.
- [ ] Module-specific entities listed in §3 / §3.1 (per-sub-page).
- [ ] If the module is role-gated, include a `permissions.md` sub-page.
- [ ] If the module has non-trivial operations (CRUD + side effects), include a `lifecycle.md` sub-page.
- [ ] If the module has a non-trivial data format (XML, JSON config, etc.), include an `xml-spec.md` or equivalent.
- [ ] Out-of-scope list explicitly excludes: TH mirror, screenshots, other modules, formal template revisions (this template).
- [ ] Frontmatter timestamp chosen for the round (e.g. `'2026-05-19T17:30:00.000Z'`) — used uniformly across all sub-pages in the round.
- [ ] Verification gates from §7 of this template inherited.

## 10. Out of scope

- TH mirror plans. The TH round is a separate effort that translates the finalized EN content. This template applies to TH pages too (same shape, translated prose), but the workflow shape is different (translation pass, not source-derived).
- Screenshots. Deferred to the Platform-wide screenshots batch (`.specs/2026-05-17-screenshots-coverage-checklist.md`).
- The Inventory book's sub-page template (`.specs/2026-05-15-sub-page-templates-design.md`) — Inventory uses numbered prefixes (`01-data-model.md`, `02-business-rules.md`, etc.) and a four-page persona-axis template. The two books deliberately use different conventions because their content shapes differ.
- Backend / SPA source fixes surfaced as divergences. Document them in the data-model page's Divergences section; do not edit those repos as part of a wiki round.

## 11. Open questions

- **`xml-spec.md` shape** — provisional in §2.5; refine when `report-templates/xml-spec.md` is written.
- **Whether a `master-config` umbrella eventually needs sub-pages** — currently the Inventory book's master-config spec treats those entities lightly (single reference page each). If the Platform book ever grows a master-config umbrella, decide then whether sub-pages apply.

This template is the source of truth for Platform-book sub-page conventions. Future modules adopt it without re-deriving. Revisions to this template require user approval and should be documented as a new dated spec that supersedes (or amends) the relevant section here.
