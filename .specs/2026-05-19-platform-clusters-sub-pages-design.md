# Design: Platform `clusters/` Sub-Pages

**Date:** 2026-05-19
**Status:** Approved (user)
**Scope:** Expand the three stub sub-pages under `en/platform/clusters/` into full reference pages, reusing the conventions established by the `users/` round.
**Predecessor:** `.specs/2026-05-19-platform-users-sub-pages-design.md` — defines the Platform-book sub-page convention by example. This spec adopts those conventions and adds the **`permissions.md`** sub-page shape, which is unique to clusters.

The Platform book's `clusters/` folder carries three stub sub-pages:
- `en/platform/clusters/data-model.md` (24 lines)
- `en/platform/clusters/permissions.md` (25 lines)
- `en/platform/clusters/ui-screens.md` (28 lines)

The cluster surface differs from users in one important respect: every cluster route is gated to the three admin-tier roles (`platform_admin`, `support_manager`, `support_staff`) via the `allowedRoles` prop on `PrivateRoute`. This makes a dedicated `permissions.md` sub-page worthwhile in a way it was not for the open-access `users` module.

---

## 1. Goals

1. **Three full sub-pages** for the `clusters` module, in English, each in the 150-300 line range, matching the prose density of `en/platform/clusters.md` (the landing).
2. **No edits to the landing** (`en/platform/clusters.md`) — it was polished in the same round as `users.md` and is the canonical overview. Sub-pages elaborate beneath; they do not restate.
3. **Reuse the convention** established by the `users/` round (commits `5f16a9b..00bda7d`) without re-deriving it. Where this spec stays silent, the `users/` convention applies.
4. **Define the `permissions.md` shape** by example. Future Platform modules with role-gated routes (any module that lists `allowedRoles` on `PrivateRoute`) can adopt this shape.

## 2. Non-goals

- **TH mirroring.** The `th/platform/clusters/` stubs stay as they are; a separate TH plan handles them later.
- **Screenshots.** Deferred to the same batch as `users/` screenshots.
- **Other Platform modules.** `business-units/` and `report-templates/` are out of scope here.
- **Restructuring the landing or its cross-links.**
- **A formal "Platform sub-page template" spec.** Still deferred — the convention is being validated across modules, not abstracted.

## 3. Sub-page shape

Each sub-page begins with the Wiki.js YAML frontmatter already in the stub (keep `dateCreated`, update `date` to `'2026-05-19T16:30:00.000Z'`), then `# <Module> — <Axis>`, then an **At a Glance** callout (one `>` line, then a second `>` line with `&nbsp;·&nbsp;`-separated bold-labeled segments), then numbered sections beginning at `## 1. Overview`. The stubs' `## 1. At a Glance` (bullet list) and `## 3. TODO` blocks are removed.

### 3.1 `data-model.md` — schema view

Mirrors `en/platform/users/data-model.md`. Sections:

1. **Overview** — entities this module owns: `tb_cluster` (primary), the cluster side of `tb_cluster_user` (the M:N join already documented in the users sub-page), and the `cluster_id` FK side of `tb_business_unit` (full BU table belongs to the business-units module — only the foreign-key story lives here).
2. **Entities** — sub-sections per table:
   - `tb_cluster` — full field table from Prisma `model tb_cluster { … }` (starts line 166 in `prisma-shared-schema-platform/prisma/schema.prisma`). Include constraints and indexes verbatim.
   - `tb_cluster_user` — brief; reference the full table in [[users]]/data-model and document only the cluster-side relevance (per-cluster role from `enum_cluster_user_role`, soft-delete impact).
   - `tb_business_unit` (cluster_id leg) — brief; document the FK from BU to cluster, with cardinality.
3. **Relationships** — bullet list of FK relations with cardinality from `@relation` directives.
4. **Enums** — `enum_cluster_user_role` (already fully covered in users/data-model — restate the values and cross-link to that page). Plus any `tb_cluster`-local enum if Prisma defines one.
5. **Divergences from carmen-platform SPA shape** — compare Prisma `tb_cluster` against the `Cluster` TypeScript type in `src/types/index.ts` (and the `ClusterFormData` interface if one exists in `ClusterEdit.tsx`). Table or "No divergences detected…".
6. **References** — Prisma path (primary), `src/pages/ClusterManagement.tsx`, `src/pages/ClusterEdit.tsx`, `src/services/clusterService.ts`, `src/types/index.ts`, cross-link to [[users]] for the join detail.

**Source-of-truth callout** at top, identical pattern to users/data-model.

### 3.2 `permissions.md` — role-gate view (NEW shape)

This is the novel sub-page shape introduced by clusters. Sections:

1. **Overview** — why every cluster route is role-gated (admin-tier responsibility, license management impact, cross-tenant data). Contrast with users (open-access) and business-units (open-access).
2. **Route guards** — table of the three cluster routes and their `allowedRoles` array from `src/App.tsx`:

   | Route | Component | `allowedRoles` |
   |---|---|---|
   | `/clusters` | `ClusterManagement` | `platform_admin`, `support_manager`, `support_staff` |
   | `/clusters/new` | `ClusterEdit` | same |
   | `/clusters/:id/edit` | `ClusterEdit` | same |

   Document this is verified against `src/App.tsx` lines 42, 50, 58 (or whatever the actual line numbers are when the implementer reads).
3. **Effective access matrix** — for each of the seven `enum_platform_role` values, can the user reach the three cluster routes? Two-column-table (Role / Can reach `/clusters*`). Mark the bootstrap exception separately.

   Expected: `platform_admin` / `support_manager` / `support_staff` = Yes; `super_admin` / `security_officer` = No (passes `ALLOWED_ROLES` at login but not in route-level `allowedRoles`); `integration_developer` / `user` = No (cannot authenticate to the SPA at all).
4. **Bootstrap exception** — the `userCount <= 1` shortcut in `AuthContext.hasRole`. When `userCount` resolves to 0 or 1, `hasRole()` returns true unconditionally so the first administrator can set up clusters. When `userCount` is `null` (API call has not yet resolved), the bootstrap exception does NOT fire — normal role checking applies. Cite the exact behaviour from `src/context/AuthContext.tsx`.
5. **AccessDenied behaviour** — when a role check fails, `PrivateRoute` renders the `<AccessDenied>` component inside the normal `<Layout>` (so the sidebar remains). The component shows the user's current role and a "Back to Dashboard" button. Document from `src/components/PrivateRoute.tsx` and the AccessDenied component definition.
6. **Sidebar filter** — `src/components/Layout.tsx` filters its `NavItem[]` array through the same `hasRole()` function, so users who would fail the route guard never see the Clusters entry in the sidebar. Document the exact `roles` field on the Clusters nav item.
7. **Module-level mutations that are NOT additionally role-gated** — within the cluster surface, the SPA does not gate individual buttons (Edit, Save, Delete, Add User, Add BU navigation, Export CSV) by role. Any user who passes the route guard sees every button. Document this for testers — there is no "viewer role within clusters."
8. **References** — `src/App.tsx`, `src/context/AuthContext.tsx`, `src/components/PrivateRoute.tsx`, `src/components/Layout.tsx`, plus cross-links to [[auth-roles]] (full role definitions and route-by-route map across the SPA) and [[users]] (where `platform_role` is set).

### 3.3 `ui-screens.md` — interaction view

Mirrors `en/platform/users/ui-screens.md` adapted for the cluster surface. Sections:

1. **Overview** — two-screen pattern (`ClusterManagement` list + `ClusterEdit` view/edit/create); note the three-column edit layout (Cluster Details + Business Units + Users cards).
2. **ClusterManagement** (`/clusters`) — list page. DataTable + debounced search + filters Sheet + CSV export + Add Cluster header action. Row actions (Edit, soft-delete — verify whether hard-delete exists on cluster as it does on user). Audit columns.
3. **ClusterEdit — create mode** (`/clusters/new`) — single "Cluster Details" card with the cluster identity fields. Success → `navigate('/clusters/:id/edit', { replace: true })`.
4. **ClusterEdit — view/edit mode** (`/clusters/:id/edit`) — three-column grid:
   - **Cluster Details card** (view-only by default; Edit button toggles to edit mode; `code` lock behaviour — verify whether `code` is settable on edit or locked).
   - **Business Units card** — lists BUs whose `cluster_id` matches; **Add** button navigates to `/business-units/new?cluster_id=<id>` so the new BU is pre-linked.
   - **Users card** — lists `tb_cluster_user` rows scoped to this cluster; supports add (search global user pool, pick role + parent BU), edit (change role), remove (dialog).
5. **Dialogs** — enumerate every dialog component reachable from the cluster surface (Add User to Cluster, Edit Cluster User, Remove Cluster User, soft/hard delete confirm if applicable).
6. **Persisted UI state** — list every `localStorage` key the list page writes. Confirm names verbatim from `ClusterManagement.tsx`.
7. **Screenshots** — deferred — inline `> **TODO:**` callout pointing at `.specs/2026-05-17-screenshots-coverage-checklist.md`.
8. **References** — `src/pages/ClusterManagement.tsx`, `src/pages/ClusterEdit.tsx`, `src/services/clusterService.ts`, `SITEMAP.md`, cross-links to [[users]] (for the user-assignment surface), [[business-units]] (Add BU flow).

## 4. Conventions inherited from `users/` (not re-derived here)

- Topical sub-page names, no numeric prefix.
- Backend Prisma > SPA source > docs/OVERVIEW.md.
- At-a-Glance is a `>` callout, NOT a heading; segmented with `&nbsp;·&nbsp;` and bold labels.
- Cross-link convention: `[[module-slug]]` for cross-module landings; `[Label](./sibling.md)` for sibling sub-pages within the same module.
- Pseudo-code blocks: language-agnostic ```` ``` ```` (no language tag) for relationship diagrams and code-shaped snippets.
- Stub residue removal: rewrite the body entirely; remove the bullet At-a-Glance heading and the `## N. TODO` block from each stub.
- Frontmatter: keep `dateCreated` from the stub; update `date` to the implementation timestamp.
- Inline `> **TODO:**` callout permitted ONLY in the `ui-screens.md` Screenshots section, mirroring the users pattern.

## 5. Verification gates

Identical to the `users/` round (see `.specs/2026-05-19-platform-users-sub-pages-design.md` §5), applied per file across all three:

1. `python3 .specs/verify_frontmatter.py <file>` prints `OK:`.
2. Wiki.js render check on `dev.blueledgers.com:3987/en/platform/clusters/<page>` confirms callout, sections, and tables render correctly.
3. No broken `[[slug]]` cross-links; sibling cross-links use the `./relative.md` form.
4. No `(/th/` cross-locale links.
5. No stub residue (`## N. TODO`, `## N. At a Glance` headings absent).
6. Line count 150-300 per file.
7. Every factual claim cites a specific path under `../carmen-platform/` or `../carmen-turborepo-backend-v2/`.
8. Final Task 4 cross-checks (cross-link inventory, landing reference integrity, frontmatter sweep across the three files).

## 6. Deferrals

- TH mirror of all three pages.
- Screenshots (batched with the rest of the Platform book).
- Landing patch — `en/platform/clusters.md` may carry stale `(stub — in progress)` markers in its Section 7 list, analogous to what was found on `users.md`. If so, that patch is a one-line follow-up after the three sub-pages land — same shape as commit `12c8c50` for users.

## 7. Out of scope

- Edits to the `clusters.md` landing during the implementation window. The landing patch (if needed) is a separate, single-commit follow-up.
- The full `tb_business_unit` data model (lives in the business-units module's data-model sub-page when that round runs).
- Cross-module concerns — e.g. how cluster-scoped permissions flow into inventory.

## 8. Open questions

None at design time. The `code` field's edit-mode behaviour (locked or editable) is an implementation-time discovery from `ClusterEdit.tsx`, not a design question.
