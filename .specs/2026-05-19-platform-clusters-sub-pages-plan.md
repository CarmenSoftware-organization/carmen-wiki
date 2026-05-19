# Platform `clusters/` Sub-Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the three stub sub-pages under `en/platform/clusters/` (`data-model.md`, `permissions.md`, `ui-screens.md`) into full reference pages matching the prose density of `en/platform/clusters.md` — reusing the convention established by the `users/` round and adding the new `permissions.md` shape for role-gated modules.

**Architecture:** Each task replaces one stub file in-place. Sources are mined from the backend Prisma platform schema (primary), the carmen-platform SPA source (secondary), and the `clusters.md` landing (positioning only — sub-pages elaborate, not restate). EN only this round.

**Tech Stack:** Markdown only. Frontmatter verifier at `.specs/verify_frontmatter.py`. Working directory: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`. Branch: `main`.

**Reference spec:** `.specs/2026-05-19-platform-clusters-sub-pages-design.md`

**Reference implementation** (calibration target for tone, At-a-Glance shape, cross-link style):
- `en/platform/users/data-model.md` (commit `a1a5686`) — 235 lines
- `en/platform/users/lifecycle.md` (commit `51ae878`) — 151 lines
- `en/platform/users/ui-screens.md` (commit `00bda7d`) — 190 lines

---

## Common Context

### Sources of truth

**Primary (Prisma platform schema):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
  - `model tb_cluster` — starts line 166
  - `model tb_cluster_user` — starts line 194 (already documented in users/data-model — restate briefly here)
  - `model tb_business_unit` — starts line 79 (full doc lives in business-units module; here only the `cluster_id` FK side)
  - `enum enum_cluster_user_role` — starts line 534 (admin / user)
  - `enum enum_platform_role` — starts line 539 (7 values; permissions.md references this)

**Secondary (carmen-platform SPA):**
- `../carmen-platform/SITEMAP.md` — the three cluster routes (all `platform_admin` / `support_manager` / `support_staff`)
- `../carmen-platform/src/pages/ClusterManagement.tsx` — list page (583 lines)
- `../carmen-platform/src/pages/ClusterEdit.tsx` — create/view/edit page (1149 lines)
- `../carmen-platform/src/services/clusterService.ts` — REST client (49 lines, 6 methods)
- `../carmen-platform/src/App.tsx` — `PrivateRoute` wiring; cluster routes carry `allowedRoles={["platform_admin", "support_manager", "support_staff"]}` at lines 42, 50, 58 (verify exact lines)
- `../carmen-platform/src/context/AuthContext.tsx` — `ALLOWED_ROLES` list, `hasRole`, `userCount` bootstrap exception
- `../carmen-platform/src/components/PrivateRoute.tsx` — route guard + `AccessDenied` rendering
- `../carmen-platform/src/components/Layout.tsx` — sidebar `NavItem[]` filter via `hasRole()`
- `../carmen-platform/src/types/index.ts` — TS shapes for `Cluster`, `BusinessUnit`, `User`

**Positioning only (do NOT restate):**
- `en/platform/clusters.md` — the landing this sub-page tree elaborates under
- `en/platform/users/data-model.md` — full doc of `tb_cluster_user`; the clusters/data-model sub-page restates the join briefly and cross-links

### API endpoints (confirmed via `clusterService.ts`)

| Operation | Method | Path |
|---|---|---|
| List | GET | `/api-system/cluster?<query>` |
| Get one | GET | `/api-system/cluster/:id` |
| Create | POST | `/api-system/cluster` |
| Update | PUT | `/api-system/cluster/:id` |
| Soft delete | DELETE | `/api-system/cluster/:id` |
| Get cluster users | GET | `/api-system/user/cluster/:clusterId` |

(No hard-delete endpoint exists on the cluster service — verify in `ClusterManagement.tsx` whether a hard-delete dialog is wired up at all.)

### Frontmatter timestamp

For each rewritten page, set `date` to `'2026-05-19T16:30:00.000Z'`. Keep `dateCreated` exactly as the stub already has it (`'2026-05-19T00:00:00.000Z'`).

### Per-task verification (run before each commit)

```bash
python3 .specs/verify_frontmatter.py en/platform/clusters/<file>.md
grep -l '^> \*\*At a Glance\*\*' en/platform/clusters/<file>.md
grep -nE '^## [0-9]+\. TODO$' en/platform/clusters/<file>.md && echo "FAIL: TODO heading remains" || echo "OK: no TODO heading"
grep -nE '^## [0-9]+\. At a Glance$' en/platform/clusters/<file>.md && echo "FAIL: stub At-a-Glance heading remains" || echo "OK: callout-style At-a-Glance"
grep -nE '\(/th/' en/platform/clusters/<file>.md && echo "FAIL: cross-locale link present" || echo "OK: no cross-locale link"
grep -nE '<[A-Z][a-z]+|<[a-z-]+>' en/platform/clusters/<file>.md && echo "FAIL: placeholder syntax remains" || echo "OK: no placeholder syntax"
grep -n '\[\[data-model\]\]\|\[\[permissions\]\]\|\[\[ui-screens\]\]' en/platform/clusters/<file>.md && echo "FAIL: stale sibling-slug link" || echo "OK: no sibling slug links"
wc -l en/platform/clusters/<file>.md
```

All five `OK:` lines must print before commit.

---

## File Structure

**Modified (3 existing stubs — replace contents):**
- `en/platform/clusters/data-model.md` (currently 24 lines → target 150-300 lines)
- `en/platform/clusters/permissions.md` (currently 25 lines → target 150-300 lines)
- `en/platform/clusters/ui-screens.md` (currently 28 lines → target 150-300 lines)

**Not touched:** the landing, `th/`, any file outside `en/platform/clusters/`.

---

## Task 1: Expand `data-model.md` (schema view)

**Files:**
- Modify: `en/platform/clusters/data-model.md`

**Sources:** Prisma `model tb_cluster` (line 166), `model tb_cluster_user` (line 194), `model tb_business_unit` (line 79); `src/types/index.ts` for the `Cluster` TS type; `ClusterEdit.tsx` for any form-specific TS shape.

- [ ] **Step 1: Read Prisma models**

```bash
sed -n '79,150p;166,220p;530,575p' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
```

Capture every field on `tb_cluster`. For `tb_cluster_user` and `tb_business_unit`, capture only the fields relevant to the cluster perspective (the `cluster_id` FK, per-cluster role, license-related fields).

- [ ] **Step 2: Read SPA cluster type**

```bash
grep -n "Cluster\b\|ClusterFormData\|interface Cluster" ../carmen-platform/src/types/index.ts ../carmen-platform/src/pages/ClusterEdit.tsx | head -30
```

- [ ] **Step 3: Rewrite `en/platform/clusters/data-model.md`**

Replace the entire body. Frontmatter: `date` → `'2026-05-19T16:30:00.000Z'`, `dateCreated` unchanged.

Structure (mirror `en/platform/users/data-model.md` shape):

```markdown
# Cluster — Data Model

> **At a Glance**
> **Tables:** `tb_cluster` (primary) · `tb_cluster_user` (M:N user-join, full doc in [[users]]) · `tb_business_unit` (`cluster_id` FK side, full doc in [[business-units]]) &nbsp;·&nbsp; **Enums:** `enum_cluster_user_role` (admin/user) &nbsp;·&nbsp; **Audit columns:** standard `created_*`/`updated_*`/`deleted_*` trio on `tb_cluster` &nbsp;·&nbsp; **License field:** `max_license_bu` caps how many BUs this cluster may have

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview
Two paragraphs positioning `tb_cluster` as the tenant container that owns BUs and (via the join) users, plus the license fields that meter the cluster's growth.

## 2. Entities

### 2.1 `tb_cluster`
One-paragraph role statement. Full field table (Field / Prisma Type / Nullable / Description). Include `id`, `code`, `name`, `alias_name`, `logo_url`, `max_license_bu`, `is_active`, the soft-delete trio, the standard audit columns. Anything else in the model.

**Constraints:** verbatim from Prisma.
**Indexes:** verbatim.

### 2.2 `tb_cluster_user` (cluster-side view)
Brief — refer the reader to [[users]]/data-model for the full field table. Document the cluster-side relevance (per-cluster role, soft-delete behaviour, `parent_bu_id` if present).

### 2.3 `tb_business_unit` (cluster_id FK side)
Brief — refer the reader to [[business-units]]/data-model (forthcoming). Document the FK from BU to cluster, cardinality (1:M cluster→BU), and how `max_license_bu` interacts with the BU count.

## 3. Relationships
Bullet list of FK relations with cardinality.

## 4. Enums
- `enum_cluster_user_role` — values + meaning + independence from `platform_role`. Restate from users/data-model and cross-link.
- Any `tb_cluster`-local enum (e.g. status, type) if Prisma declares one.

## 5. Divergences from carmen-platform SPA shape
Compare Prisma `tb_cluster` against the `Cluster` TS type in `src/types/index.ts` (and any `ClusterFormData` in `ClusterEdit.tsx`). Table or "No divergences detected against carmen-platform SPA shape as of 2026-05-19."

## 6. References
Primary, secondary, cross-links to [[users]] and [[business-units]].
```

- [ ] **Step 4: Run verification (per-task block above, substituting `data-model.md`)**

Expected: all OK lines + line count 150-300.

- [ ] **Step 5: Commit**

```bash
git add en/platform/clusters/data-model.md
git commit -m "docs(platform/clusters): expand data-model from stub to canonical reference

Prisma-derived field table for tb_cluster, cluster-side view of
tb_cluster_user and tb_business_unit (full docs cross-linked),
enum cross-link to users/data-model, divergence check against
SPA Cluster type."
```

---

## Task 2: Expand `permissions.md` (role-gate view — new shape)

**Files:**
- Modify: `en/platform/clusters/permissions.md`

**Sources:** `src/App.tsx`, `src/context/AuthContext.tsx`, `src/components/PrivateRoute.tsx`, `src/components/Layout.tsx`, the seven values of `enum_platform_role` from Prisma.

- [ ] **Step 1: Read App.tsx route guards**

```bash
grep -n "allowedRoles\|/clusters" ../carmen-platform/src/App.tsx
sed -n '40,65p' ../carmen-platform/src/App.tsx
```

Confirm the three cluster routes (`/clusters`, `/clusters/new`, `/clusters/:id/edit`) each carry `allowedRoles={["platform_admin", "support_manager", "support_staff"]}`.

- [ ] **Step 2: Read AuthContext for ALLOWED_ROLES + bootstrap exception**

```bash
grep -n "ALLOWED_ROLES\|hasRole\|userCount\|bootstrap" ../carmen-platform/src/context/AuthContext.tsx
```

Capture: the 5 values in `ALLOWED_ROLES` (login allow-list), the exact behaviour of `hasRole()` when `userCount` is `null` vs `0` vs `1` vs `>1`.

- [ ] **Step 3: Read PrivateRoute and AccessDenied**

```bash
cat ../carmen-platform/src/components/PrivateRoute.tsx
```

Capture the render path on auth-fail (redirect to `/login`) vs role-fail (`<AccessDenied>` inside `<Layout>`).

- [ ] **Step 4: Read Layout sidebar filter**

```bash
grep -n "NavItem\|hasRole\|Clusters\|allNavItems" ../carmen-platform/src/components/Layout.tsx | head -30
```

Capture the cluster nav item and its `roles` field.

- [ ] **Step 5: Rewrite `en/platform/clusters/permissions.md`**

Replace the entire body. Frontmatter: `date` → `'2026-05-19T16:30:00.000Z'`, `dateCreated` unchanged.

Structure:

```markdown
# Cluster — Permissions

> **At a Glance**
> **Gate:** all three cluster routes carry `allowedRoles={["platform_admin", "support_manager", "support_staff"]}` &nbsp;·&nbsp; **Bootstrap exception:** `hasRole` returns true unconditionally when `userCount <= 1` (first-admin setup) &nbsp;·&nbsp; **On role failure:** `<AccessDenied>` renders inside `<Layout>` (sidebar stays) &nbsp;·&nbsp; **Sidebar filter:** Clusters entry hidden from users who fail `hasRole()` &nbsp;·&nbsp; **No per-button role gates** within the cluster surface — pass the route guard and you see every action

## 1. Overview
Two paragraphs: why clusters is role-gated (admin-tier responsibility, license management, cross-tenant impact); how the gate is structured (`PrivateRoute` + `allowedRoles` + `AccessDenied`); contrast with open-access modules (users, business-units, profile) that use `PrivateRoute` without an `allowedRoles` array.

## 2. Route guards

| Route | Component | `allowedRoles` | Source |
|---|---|---|---|
| `/clusters` | `ClusterManagement` | `platform_admin`, `support_manager`, `support_staff` | `src/App.tsx` line <N> |
| `/clusters/new` | `ClusterEdit` | (same) | line <N> |
| `/clusters/:id/edit` | `ClusterEdit` | (same) | line <N> |

(Implementer: substitute exact line numbers from App.tsx.)

## 3. Effective access matrix

For each value of `enum_platform_role` (7 total), can the user reach the cluster routes?

| `platform_role` value | Can sign in? | In cluster `allowedRoles`? | Effective access |
|---|---|---|---|
| `super_admin` | Yes (ALLOWED_ROLES) | No | No — AccessDenied |
| `platform_admin` | Yes | Yes | Full |
| `support_manager` | Yes | Yes | Full |
| `support_staff` | Yes | Yes | Full |
| `security_officer` | Yes | No | No — AccessDenied |
| `integration_developer` | No (not in ALLOWED_ROLES) | n/a | Cannot sign in |
| `user` | No | n/a | Cannot sign in |

The matrix derives from Prisma `enum_platform_role` (7 values) × `AuthContext.ALLOWED_ROLES` (5 values that pass login) × the route-level `allowedRoles` array (3 values).

## 4. Bootstrap exception
Document the `userCount <= 1` shortcut in `hasRole()`:
- `userCount` is fetched by `AuthContext` on mount.
- When it resolves to `0` or `1`, `hasRole()` returns `true` unconditionally, so the first administrator can reach role-gated routes (including `/clusters`) to set up the platform.
- When `userCount` is still `null` (the API call has not yet resolved or failed), the bootstrap exception does NOT fire — normal role checking applies.
- Once `userCount > 1`, the exception goes dormant; if data is later cleared and `userCount` drops back to 1, the exception fires again.

Cite exact lines from `AuthContext.tsx`.

## 5. AccessDenied behaviour
On role-fail (user is authenticated but `platform_role` is not in the route's `allowedRoles`), `PrivateRoute` renders `<AccessDenied>` inside the normal `<Layout>` — the sidebar and header remain visible, only the main content is replaced. The component shows the user's current role and a "Back to Dashboard" button.

On auth-fail (no session), `PrivateRoute` redirects to `/login`.

Cite from `src/components/PrivateRoute.tsx`.

## 6. Sidebar filter
`Layout.tsx` filters its `NavItem[]` through `hasRole()`. The Clusters entry has its `roles` field set to the same `["platform_admin", "support_manager", "support_staff"]` list (or equivalent constant). Users whose `platform_role` does not match the list never see the Clusters entry in the sidebar — they cannot navigate to the route via UI, only by typing the URL (where the route guard catches them).

## 7. Within the cluster surface
Once a user passes the route guard, the SPA does NOT additionally gate individual buttons or fields by `platform_role`:
- Edit, Save, Cancel — visible to every authorized user.
- Delete (soft) — visible.
- Add User to Cluster, Edit Cluster User, Remove Cluster User — visible.
- Add BU (navigate-to-new) — visible.
- Export CSV — visible.

There is no "viewer" sub-role within clusters. Testers should plan tests around the route-level gate, not around per-button differentiation.

## 8. References
- `src/App.tsx` — route wiring with `allowedRoles` props.
- `src/context/AuthContext.tsx` — `ALLOWED_ROLES`, `hasRole`, `userCount` bootstrap.
- `src/components/PrivateRoute.tsx` — gate logic, `<AccessDenied>` render path.
- `src/components/Layout.tsx` — sidebar `NavItem[]` filter.
- Prisma `enum_platform_role` for the 7-value source list.
- Cross-links: [[auth-roles]] for the full role definitions and the cross-SPA route map; [[users]] for where `platform_role` is set.
```

- [ ] **Step 6: Run verification (per-task block, substituting `permissions.md`)**

- [ ] **Step 7: Commit**

```bash
git add en/platform/clusters/permissions.md
git commit -m "docs(platform/clusters): expand permissions from stub to canonical reference

Route-guard table for the 3 cluster routes, effective access
matrix across all 7 platform_role values, bootstrap exception
documented from AuthContext, AccessDenied render path, sidebar
filter via Layout. Establishes the permissions.md shape for
Platform-book role-gated modules."
```

---

## Task 3: Expand `ui-screens.md` (interaction view)

**Files:**
- Modify: `en/platform/clusters/ui-screens.md`

**Sources:** `ClusterManagement.tsx` (583 lines), `ClusterEdit.tsx` (1149 lines), `clusterService.ts`, `SITEMAP.md`.

- [ ] **Step 1: Read SITEMAP cluster routes**

```bash
sed -n '/^| `\/clusters/,/^| `\/clusters\/:id\/edit/p' ../carmen-platform/SITEMAP.md
```

- [ ] **Step 2: Read ClusterManagement.tsx structure**

```bash
grep -n "export\|DataTable\|Filters\|Sheet\|CSV\|Export\|Add Cluster\|Dialog\|localStorage\|debounce\|hardDelete\|handleDelete" ../carmen-platform/src/pages/ClusterManagement.tsx
```

Capture: filter set (likely active/inactive, show-soft-deleted), header actions (Add Cluster, Export), row actions, audit columns, every `localStorage` key.

- [ ] **Step 3: Read ClusterEdit.tsx structure**

```bash
grep -n "Card\|Grid\|Dialog\|Add User\|Add BU\|Business Units\|Users\|isNew\|disabled\|handleSave\|handleAddUser" ../carmen-platform/src/pages/ClusterEdit.tsx | head -100
```

Capture: the three-column grid layout (Cluster Details + Business Units + Users); whether `code` is disabled in edit mode; the Add User to Cluster dialog (search user pool, pick role, parent BU); Add BU navigate-to-new pattern; soft-delete flow.

- [ ] **Step 4: Rewrite `en/platform/clusters/ui-screens.md`**

Replace the entire body. Frontmatter: `date` → `'2026-05-19T16:30:00.000Z'`, `dateCreated` unchanged.

Structure (mirror `en/platform/users/ui-screens.md` adapted for the three-column cluster edit layout):

```markdown
# Cluster — UI Screens

> **At a Glance**
> **Screens:** `ClusterManagement` (list, `/clusters`) &nbsp;·&nbsp; `ClusterEdit` create (`/clusters/new`) &nbsp;·&nbsp; `ClusterEdit` view/edit (`/clusters/:id/edit`) &nbsp;·&nbsp; **Edit layout:** 3-column grid (Cluster Details · Business Units · Users) &nbsp;·&nbsp; **Dialogs:** Add User to Cluster &nbsp;·&nbsp; Edit Cluster User &nbsp;·&nbsp; Remove Cluster User &nbsp;·&nbsp; Soft Delete confirm &nbsp;·&nbsp; **Access:** all three routes gated to `platform_admin` / `support_manager` / `support_staff` (see [Permissions](./permissions.md)) &nbsp;·&nbsp; **Persisted UI state:** N `localStorage` keys on list page (substitute actual count)

## 1. Overview
Two paragraphs: two-screen pattern; the cluster edit page's three-column grid layout; how the Business Units and Users cards differ from the analogous cards on the user-edit page.

## 2. `ClusterManagement` — list page (`/clusters`)
### 2.1 Layout
DataTable, header row, search/filters row.

### 2.2 Filters (Sheet panel)
List every filter actually wired up in `ClusterManagement.tsx` — likely active/inactive toggle, show-soft-deleted, but verify.

### 2.3 Header actions
- Export CSV — confirm client-side vs server-side from source.
- Add Cluster — navigates to `/clusters/new`.
- Hard delete header action — verify whether it exists; if not, document its absence.

### 2.4 Row actions
- Edit — navigates to `/clusters/:id/edit`.
- Delete (soft) — `DELETE /api-system/cluster/:id`, confirm dialog UX.
- (Hard delete — verify presence or absence in source.)

### 2.5 Audit columns
List columns shown.

## 3. `ClusterEdit` — create mode (`/clusters/new`)
- Layout: single "Cluster Details" card.
- Form fields: list the cluster identity fields (`code`, `name`, `alias_name`, `logo_url`, `max_license_bu`, `is_active`, plus any others).
- Submit: `POST /api-system/cluster`; on success, `navigate('/clusters/:id/edit', { replace: true })`.

## 4. `ClusterEdit` — view/edit mode (`/clusters/:id/edit`)
Three-column grid. Page starts in view mode; Edit button toggles to edit mode.

### 4.1 Cluster Details card (left column)
- View mode: read-only display of all fields.
- Edit mode: editable. Document whether `code` is locked after create (verify in source). Save → `PUT /api-system/cluster/:id`; Cancel reverts.

### 4.2 Business Units card (middle/right column or spans)
- Lists every BU whose `cluster_id` matches this cluster.
- **Add** button → `navigate('/business-units/new?cluster_id=<id>')` so the new BU is pre-linked. The query param wires the create form to land on this cluster's child set.
- Row controls (Edit-navigates, possibly Remove from card; verify).

### 4.3 Users card (next to BU card)
- Lists `tb_cluster_user` rows scoped to this cluster.
- Each row: user name + email + per-cluster role (`admin` / `user`) + parent BU (if assigned) + remove icon.
- **Add User** button → Add User to Cluster dialog (§5.1).

## 5. Dialogs
### 5.1 Add User to Cluster dialog
- Triggered from Users card on `/clusters/:id/edit`.
- Search input over the global user pool.
- Role select: `admin` / `user` (from `enum_cluster_user_role`).
- Optional parent BU select (scoped to BUs in this cluster).
- On submit: creates a new `tb_cluster_user` row.

### 5.2 Edit Cluster User dialog
- Triggered from a row in the Users card.
- Allows changing the per-cluster role and (if applicable) the parent BU.
- On submit: updates the `tb_cluster_user` row.

### 5.3 Remove Cluster User dialog
- Triggered from the row Trash/Remove icon.
- Confirms removal; on submit: deletes (soft or hard — verify) the `tb_cluster_user` row.

### 5.4 Soft Delete Cluster confirm
- Triggered from `ClusterManagement` row action.
- Document the confirm UX (simple Yes/No vs typed — verify in source).
- Submit: `DELETE /api-system/cluster/:id`.

## 6. Persisted UI state
The list page persists keys in `localStorage`. List every key name verbatim from `ClusterManagement.tsx` (likely names: `search_clusters`, `page_clusters`, `perpage_clusters`, `sort_clusters`, plus any filter keys; confirm).

| Key | Stored type | Persists |
|---|---|---|

The `ClusterEdit` page does NOT persist UI state.

## 7. Screenshots
> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References
- `../carmen-platform/SITEMAP.md`
- `../carmen-platform/src/pages/ClusterManagement.tsx`
- `../carmen-platform/src/pages/ClusterEdit.tsx`
- `../carmen-platform/src/services/clusterService.ts`
- Cross-links: [[users]] (the global user pool the Add User dialog searches), [[business-units]] (Add BU navigate-to-new flow), [Data Model](./data-model.md), [Permissions](./permissions.md).
```

- [ ] **Step 5: Run verification (per-task block, substituting `ui-screens.md`)**

Expected: five OK lines + exactly one `> **TODO:**` line in §7 + line count 150-300.

- [ ] **Step 6: Commit**

```bash
git add en/platform/clusters/ui-screens.md
git commit -m "docs(platform/clusters): expand ui-screens from stub to canonical reference

ClusterManagement list (filters, Add Cluster, soft-delete confirm),
three-column ClusterEdit (Cluster Details + Business Units + Users
cards), Add/Edit/Remove Cluster User dialogs, navigate-to-new BU
flow, persisted localStorage keys. Screenshots deferred."
```

---

## Task 4: Final cross-page checks + push

**Files:**
- Read-only: all three expanded pages, plus `en/platform/clusters.md` landing.

- [ ] **Step 1: Cross-link integrity**

```bash
grep -oE '\[\[[a-z-]+\]\]' en/platform/clusters/*.md | sort -u
ls en/platform/users.md en/platform/business-units.md en/platform/profile.md en/platform/auth-roles.md en/platform/clusters/data-model.md en/platform/clusters/permissions.md en/platform/clusters/ui-screens.md
```

Every `[[slug]]` must resolve to a Platform-book or Inventory-book module slug.

- [ ] **Step 2: Landing references still resolve**

```bash
grep -nE '\(\./(data-model|permissions|ui-screens)\.md\)' en/platform/clusters.md
```

Expected: three matches in §7 of the landing.

- [ ] **Step 3: Full-tree frontmatter sweep + per-file verification**

```bash
for f in en/platform/clusters/data-model.md en/platform/clusters/permissions.md en/platform/clusters/ui-screens.md; do
  python3 .specs/verify_frontmatter.py "$f"
done
```

Expected: three OK lines.

Then run the full per-task verification grep set on each file (as defined in Common Context).

- [ ] **Step 4: Sibling-slug consistency**

```bash
grep -n '\[\[data-model\]\]\|\[\[permissions\]\]\|\[\[ui-screens\]\]' en/platform/clusters/*.md && echo "FAIL: sibling-slug link present" || echo "OK: no sibling-slug links"
```

- [ ] **Step 5: Visual render check on dev Wiki.js**

The user opens these URLs and confirms render quality:
- `http://dev.blueledgers.com:3987/en/platform/clusters/data-model`
- `http://dev.blueledgers.com:3987/en/platform/clusters/permissions`
- `http://dev.blueledgers.com:3987/en/platform/clusters/ui-screens`

(The dev wiki may need to pull latest commits — the user triggers if needed.)

- [ ] **Step 6: Push to remote** (only after the user confirms visual check passed)

```bash
git push origin main
```

- [ ] **Step 7: Optional follow-up — landing patch**

If `en/platform/clusters.md` Section 7 carries `(stub — in progress)` annotations next to the three sub-page links (analogous to what was found on `users.md`), produce a single-commit patch that removes those annotations. Same shape as commit `12c8c50` for users. Skip this step if the landing does not carry such annotations.

---

## Self-Review

**1. Spec coverage:**
- Spec §3.1 (`data-model.md` shape) → Task 1. ✓
- Spec §3.2 (`permissions.md` shape) → Task 2. ✓
- Spec §3.3 (`ui-screens.md` shape) → Task 3. ✓
- Spec §4 (inherited conventions) → enforced inline in each Task's rewrite step.
- Spec §5 (verification gates) → per-task verification block + Task 4. ✓
- Spec §6 (deferrals) → out of plan; Task 4 Step 7 covers the optional landing patch.
- Spec §7 (out of scope) → respected.

**2. Placeholder scan:** the only `<…>` brackets in this plan are inside the "Rewrite" step's structure blocks, which are intentional fillable sections the implementer completes from cited sources. The per-task verification grep catches any survivors.

**3. Identifier consistency:** model names (`tb_cluster`, `tb_cluster_user`, `tb_business_unit`), enum names (`enum_cluster_user_role`, `enum_platform_role`), endpoint paths (`/api-system/cluster`, `/api-system/cluster/:id`, `/api-system/user/cluster/:clusterId`), and component names (`ClusterManagement`, `ClusterEdit`, `PrivateRoute`, `AccessDenied`, `AuthContext`, `Layout`) match across all four tasks and the Common Context block.
