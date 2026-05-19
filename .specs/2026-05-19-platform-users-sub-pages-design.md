# Design: Platform `users/` Sub-Pages

**Date:** 2026-05-19
**Status:** Approved (user)
**Scope:** Expand the three stub sub-pages under `en/platform/users/` into full reference pages; establish the Platform-book sub-page convention by example.
**Predecessor:** None (this is the first per-module implementation in the Platform book — `users/` plays for Platform the role PR plays for Inventory).

The Platform book already has six polished module landings (`auth-roles`, `business-units`, `clusters`, `profile`, `report-templates`, `users` in both `en/` and `th/`). Four of those modules carry **stub** sub-page folders (`business-units/`, `clusters/`, `users/`, `report-templates/`) — each sub-page is ~25 lines of frontmatter plus an "At a Glance" bullet list and a `## TODO` block. The remaining two modules (`auth-roles`, `profile`) are intentionally landing-only.

This spec covers **only the three sub-pages under `users/`**. Subsequent per-module specs will follow the same shape once the convention is validated here.

The Platform book deliberately uses **topical sub-pages with no numeric prefix**, unlike the Inventory book's `01-data-model.md` / `02-business-rules.md` / `03-user-flow.md` / `04-test-scenarios.md` template. Platform modules are CRUD admin screens, not multi-persona document-workflow flows, so the four-page persona template does not fit. This spec keeps the existing topical names (`data-model.md`, `lifecycle.md`, `ui-screens.md`).

---

## 1. Goals

1. **Three full sub-pages** for the `users` module, in English, each in the 150-300 line range, matching the prose density and structure of `en/platform/users.md`.
2. **No edits to the landing** (`en/platform/users.md`) — it was polished in commit `06fb3e2` and is the readers' canonical overview. Sub-pages elaborate beneath it; they do not restate it.
3. **Establish the Platform-book sub-page convention** by example, so the next module (clusters, BU, or report-templates) can follow without re-deciding shape.
4. **Source-of-truth fidelity** — backend Prisma platform schema beats SPA TypeScript types beats `../carmen-platform/docs/OVERVIEW.md`. Divergences are noted, not silently merged.

## 2. Non-goals

- **TH mirroring.** The TH copies will be produced after EN lands, as a separate plan.
- **Screenshots.** Deferred to a later round (the `screenshots-coverage-checklist.md` workflow will sweep multiple modules in one pass). The `ui-screens.md` page will carry an inline `> **TODO:**` callout in its Screenshots section as a marker.
- **Other modules.** `clusters/`, `business-units/`, `report-templates/` stubs are out of scope for this spec.
- **A formal "Platform sub-page templates" spec.** Deferred until 2-3 modules have been written and a pattern is visible enough to extract. The conventions section of this spec is the interim guide.
- **Restructuring the landing or adjusting cross-links from it.** The landing already references the three sub-pages by relative path; sub-pages must keep those paths intact.
- **Fixing carmen-platform SPA divergences from Prisma.** Document them in the data-model page's Divergences section; do not change either repo.

## 3. Sub-page shape

Each sub-page begins with the Wiki.js YAML frontmatter already in the stub (keep `dateCreated`, update `date` to the implementation timestamp), then `# <Module> — <Axis>`, then an **At a Glance** callout (one paragraph, callout style with `&nbsp;·&nbsp;` separators, matching the landing), then numbered sections (`## 1.`, `## 2.`, ...).

The stubs' current `## 1. At a Glance` (bullet list) and `## 3. TODO` blocks are removed; the new At-a-Glance callout style replaces both.

### 3.1 `data-model.md` — schema view

Sections:

1. **Overview** — entities this module owns, how they relate to neighbour modules (cluster assignments, BU assignments). Brief — leave detail to Section 2.
2. **Entities** — one sub-section per entity, with a field table (Field / Prisma Type / Nullable / Description). Cover three entities:
   - `user` (identity, `platform_role`, `is_active`, soft-delete trio, audit columns)
   - `tb_cluster_user` (M:N user ↔ cluster join with per-cluster `enum_cluster_user_role`)
   - The user-business-unit join (M:N user ↔ BU with per-BU `enum_user_business_unit_role` and `is_default`)

   Under each table, list **Constraints** (PK, FKs, uniques) and **Indexes** verbatim from Prisma.
3. **Relationships** — bullet list of FK relations with cardinality (1:M, M:N) derived from Prisma `@relation` directives.
4. **Enums** — list each enum's values plus meaning. Cover three enums:
   - `enum_platform_role` (7 values: `super_admin`, `platform_admin`, `support_manager`, `support_staff`, `security_officer`, `integration_developer`, `user`). Call out that only 5 of these 7 appear in `AuthContext.ALLOWED_ROLES`; the other two (`integration_developer`, `user`) are valid data values whose holders cannot sign in to the Platform admin SPA.
   - `enum_cluster_user_role` (admin / user)
   - `enum_user_business_unit_role` (admin / user)
5. **Divergences from carmen-platform SPA shape** — table (or "No divergences detected as of 2026-05-19") comparing Prisma model vs. `src/types/index.ts` user types and the `UserFormData` interface inside `UserEdit.tsx`.
6. **References** — Prisma paths (primary), SPA paths (secondary).

**Source-of-truth callout** at the top of the page (after the At-a-Glance, before Section 1):

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

### 3.2 `lifecycle.md` — operations view

Sections:

1. **Overview** — the operations this page covers and what is explicitly absent in this product (no SSO, no MFA, no OAuth, no email-link password reset).
2. **Create flow** — `POST /api-system/user`, the eight form fields, the `replace`-navigate to `/users/:id/edit` on success.
3. **Edit flow** — `PUT /api-system/user/:id`, `username` locked after create, the view↔edit mode toggle on `UserEdit`.
4. **Activate / Deactivate** — the `is_active` flag, its independence from soft-delete, and what it means for the user's ability to sign in.
5. **Soft delete vs. Hard delete** —
   - Soft: `DELETE /api-system/user/:id` (sets `deleted_at` / `deleted_by_name`); list page hides these rows unless the "show soft-deleted" filter is on; row carries a red "Deleted" badge and a "Deleted By" column.
   - Hard: `DELETE /api-system/user/:id/hard`, gated by a dialog requiring the operator to type the exact username/email.
6. **Admin-initiated password reset** — `PUT /api-system/user/:id/reset-password`, minimum six chars, current password NOT required (admin override), no email-link flow, the auth context is not refreshed afterwards.
7. **Keycloak sync** — `POST /api-system/fetch-user` via `userService.fetchKeycloakUsers()`; the list page reloads the table after success.
8. **Cross-entity side effects** —
   - Cluster assignments (`tb_cluster_user`) are read-only here; the canonical mutation surface is the cluster edit page.
   - BU assignments are added and removed on this page through the Add BU dialog, scoped to clusters the user is already in.
   - Document what happens to the two join rows on soft-delete and on hard-delete (cascade or persist; orphan handling on the related cluster/BU pages). Verify behaviour against the backend before asserting either way.
9. **References** — `src/services/userService.ts`, `src/pages/UserEdit.tsx`, `src/pages/UserManagement.tsx`.

### 3.3 `ui-screens.md` — interaction view

Sections:

1. **Overview** — the two-screen pattern (`UserManagement` list + `UserEdit` view/edit/create). Brief.
2. **UserManagement** (`/users`) — DataTable with debounced search, Sheet-based filters panel (Role multi-select over the seven `PLATFORM_ROLES` values, Active/Inactive status, "show soft-deleted" toggle), CSV export, two header actions unique to this module (**Fetch Keycloak**, **Add User**), row actions (Edit, soft-delete, hard-delete), audit columns.
3. **UserEdit — create mode** (`/users/new`) — single User Details card with the eight form fields; success → `navigate(..., { replace: true })` to the edit route.
4. **UserEdit — view/edit mode** (`/users/:id/edit`) — three stacked cards (User Details, Clusters read-only, Business Units with row-level Trash + Add BU button), the Edit / Save / Cancel mode toggle, `username` disabled in edit mode.
5. **Dialogs** — three of them:
   - Add BU dialog (available BUs scoped to clusters the user is already in, per-BU role admin/user, `is_default` flag).
   - Change Password dialog (new + confirm, minimum six chars, must match).
   - Hard Delete confirm (type username/email to enable the destructive button).
6. **Persisted UI state** — the `localStorage` keys the list page writes (search, page, perpage, sort, role filter, status filter, show-deleted toggle).
7. **Screenshots** — inline `> **TODO:**` callout: "Screenshots deferred to the upcoming screenshots batch (`.specs/2026-05-17-screenshots-coverage-checklist.md`)."
8. **References** — `../carmen-platform/SITEMAP.md`, `src/pages/UserManagement.tsx`, `src/pages/UserEdit.tsx`, `src/components/Layout.tsx`.

## 4. Conventions established for the Platform book

These conventions are set by this spec and inherited by subsequent per-module Platform specs. They live here, in the `users/` spec, until a formal Platform sub-page template spec is written (deferred — see Section 6).

| Decision | Choice | Rationale |
|---|---|---|
| File naming | Topical, no numeric prefix (`data-model.md`, `lifecycle.md`, `ui-screens.md`, `permissions.md`, `xml-spec.md`) | Matches the existing stubs; per-module Platform shapes vary too much for the numbered template that fits Inventory. |
| Source-of-truth order | Backend Prisma platform schema > carmen-platform SPA source > `../carmen-platform/docs/OVERVIEW.md` and `SITEMAP.md` | Backend schema is the lowest layer and the only one that survives a SPA rewrite. |
| At-a-Glance callout | One-paragraph callout block in the page's voice (Tables / Audience / Key entities / etc.), `&nbsp;·&nbsp;` separators — matching `users.md` landing | Single skim path; reader gets the page's scope in 30 seconds. |
| Cross-link style | `[[slug]]` for intra-Platform-book links; relative paths (`./data-model.md`) for intra-module links; no cross-locale links | Matches landing; Wiki.js handles locale toggle natively. |
| Pseudo-code | Language-agnostic fenced ```` ``` ```` blocks (no language tag); reserve real code for verbatim Prisma snippets, TS types, or API request/response shapes that the reader will copy | Matches Inventory book convention from CLAUDE.md. |
| Stub residue removal | The original `## 1. At a Glance` bullet block, the original `## 2. References` mini-list, and the `## 3. TODO` block in the stub are all replaced — not appended to. The expanded page is a rewrite, not a patch. | Stub blocks were placeholders, not content. |
| Frontmatter | Keep `dateCreated` from the stub; update `date` to the implementation timestamp. Leave `title`, `description`, `tags`, `published`, `editor` unchanged unless they are wrong. | Matches the convention in `CLAUDE.md`. |
| Deferred sections | If a section's content is genuinely deferred (e.g. Screenshots), keep the section heading and put an inline `> **TODO:**` callout under it pointing at the future plan. Do not invent placeholder prose. | Readers can navigate the table of contents; deferred-but-present beats absent-and-surprising. |

## 5. Verification gates (before claiming done)

1. **Frontmatter verifier passes** for all three files: `python3 .specs/verify_frontmatter.py en/platform/users/*.md`
2. **Wiki.js render check** on the dev instance — load all three pages at `http://dev.blueledgers.com:3987/en/platform/users/data-model`, `.../lifecycle`, `.../ui-screens` and confirm the At-a-Glance callout, numbered sections, and tables render correctly.
3. **No broken cross-links** — every `[[slug]]` resolves to one of the six Platform module slugs (`auth-roles`, `business-units`, `clusters`, `profile`, `report-templates`, `users`) or one of the Inventory module slugs.
4. **No cross-locale links** — `grep -nE '\(/th/' en/platform/users/*.md` returns nothing.
5. **No stub residue** —
   - `grep -nE '^## [0-9]+\. TODO$' en/platform/users/*.md` returns nothing.
   - Every file has `> **At a Glance**` near the top: `grep -l '^> \*\*At a Glance\*\*' en/platform/users/*.md` lists all three files.
   - The original stub layout (`## 1. At a Glance` heading containing a bullet list followed by `## 2. References` and `## 3. TODO`) is gone — the new files use the callout style with numbered sections beginning at `## 1. Overview`.
   - The only `TODO` text permitted is the inline `> **TODO:**` callout in the `ui-screens.md` Screenshots section.
6. **Source-citation discipline** — every claim about API endpoints, field counts, or SPA behaviour cites a specific path under `../carmen-platform/` or `../carmen-turborepo-backend-v2/`.

## 6. Deferrals (do not undo without asking)

- **Formal "Platform sub-page template" spec.** Defer until at least three Platform modules have been written (`users`, plus two of `clusters` / `business-units` / `report-templates`). Premature templating would lock in shapes that may not generalize — `clusters/permissions.md` and `report-templates/xml-spec.md` are clearly module-specific, and the right abstraction will only emerge after the second or third module.
- **TH mirroring.** A separate plan will produce `th/platform/users/*.md` by translating the finalized EN content. Producing TH in parallel risks drift; doing it after EN settles is cheaper.
- **Screenshots.** Will be batched across all Platform modules in one screenshots-coverage pass once the content is stable.
- **Landing edits.** `en/platform/users.md` is fixed for the duration of this implementation. If a sub-page discovers a factual issue in the landing, raise it as a follow-up — do not in-line edit.

## 7. Out of scope

- Editing the `users.md` landing or any other landing in the Platform book.
- Adding new files outside `.specs/<this-spec>.md` and the three target sub-page paths.
- Modifying `.specs/templates/` or the existing Inventory sub-page templates.
- Sourcing content from end-user docs (this is a developer/tester reference, not a user manual page).
- Refactoring the Platform book's folder layout or navigation overrides.

## 8. Open questions

None at design time. Conventions in Section 4 are decisions, not open questions; they can be revisited after the first module if a downstream module surfaces a problem.
