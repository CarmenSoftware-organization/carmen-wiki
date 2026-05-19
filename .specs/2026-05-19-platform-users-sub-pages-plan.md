# Platform `users/` Sub-Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the three stub sub-pages under `en/platform/users/` (`data-model.md`, `lifecycle.md`, `ui-screens.md`) into full reference pages matching the prose density and structure of `en/platform/users.md` — establishing the Platform-book sub-page convention by example.

**Architecture:** Each task replaces one stub file in-place. Sources are mined from the backend Prisma platform schema (primary), the carmen-platform SPA source (secondary), and the `users.md` landing (positioning only — sub-pages elaborate, not restate). EN only this round; TH mirror and screenshots are explicit non-goals (deferred per spec).

**Tech Stack:** Markdown only. No build pipeline. Frontmatter verifier at `.specs/verify_frontmatter.py` (Python 3, no deps). Working directory: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`. Branch: `main` (user-approved direct commits).

**Reference spec:** `.specs/2026-05-19-platform-users-sub-pages-design.md`

---

## Common Context

### Sources of truth (primary → secondary)

**Primary (Prisma platform schema):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
  - `model tb_user` — starts line 368
  - `model tb_cluster_user` — starts line 194 (M:N user ↔ cluster join)
  - `model tb_user_tb_business_unit` — starts line 489 (M:N user ↔ BU join)
  - `enum enum_platform_role` — starts line 539 (7 values)
  - `enum enum_cluster_user_role` — starts line 534 (admin / user)
  - `enum enum_user_business_unit_role` — starts line 560 (admin / user)

**Secondary (carmen-platform SPA, the API consumer):**
- `../carmen-platform/SITEMAP.md` — the three user routes (all "Authenticated", no `allowedRoles`)
- `../carmen-platform/src/pages/UserManagement.tsx` — list page (775 lines)
- `../carmen-platform/src/pages/UserEdit.tsx` — create/view/edit page (976 lines)
- `../carmen-platform/src/services/userService.ts` — REST client (61 lines)
- `../carmen-platform/src/context/AuthContext.tsx` — `ALLOWED_ROLES` allow-list, `hasRole`, bootstrap-exception logic
- `../carmen-platform/src/types/index.ts` — TS shapes for User, UserFormData, etc.

**Positioning only (do NOT restate):**
- `en/platform/users.md` — the landing this sub-page tree elaborates under

### API endpoints (confirmed via `userService.ts`)

| Operation | Method | Path |
|---|---|---|
| List | GET | `/api-system/user?<query>` |
| Get one | GET | `/api-system/user/:id` |
| Create | POST | `/api-system/user` |
| Update | PUT | `/api-system/user/:id` |
| Soft delete | DELETE | `/api-system/user/:id` |
| Hard delete | DELETE | `/api-system/user/:id/hard` |
| Admin reset password | PUT | `/api-system/user/:id/reset-password` (body: `{ newPassword }`) |
| Keycloak sync | POST | `/api-system/fetch-user` |

### Frontmatter timestamp

For each rewritten page, set `date` to `2026-05-19T15:00:00.000Z`. Keep `dateCreated` exactly as the stub already has it (`'2026-05-19T00:00:00.000Z'`).

### Section anchor convention

Numbered sections begin at `## 1. Overview` (NOT `## 1. At a Glance` — that becomes a callout block above the numbered sections, not a heading). Section count varies per file (6 sections for data-model, 9 for lifecycle, 8 for ui-screens — exactly as in the spec).

### Per-task verification (run before each commit)

```bash
# 1. Frontmatter check
python3 .specs/verify_frontmatter.py en/platform/users/<file>.md
# Expected: OK: en/platform/users/<file>.md — title='...'

# 2. At-a-Glance callout present
grep -l '^> \*\*At a Glance\*\*' en/platform/users/<file>.md
# Expected: prints the path

# 3. No bare TODO heading (the stub's "## 3. TODO" block must be gone)
grep -nE '^## [0-9]+\. TODO$' en/platform/users/<file>.md && echo "FAIL: TODO heading remains" || echo "OK: no TODO heading"
# Expected: OK: no TODO heading

# 4. No stub-style At-a-Glance heading (callout replaces it)
grep -nE '^## [0-9]+\. At a Glance$' en/platform/users/<file>.md && echo "FAIL: stub At-a-Glance heading remains" || echo "OK: callout-style At-a-Glance"
# Expected: OK: callout-style At-a-Glance

# 5. No cross-locale link
grep -nE '\(/th/' en/platform/users/<file>.md && echo "FAIL: cross-locale link present" || echo "OK: no cross-locale link"
# Expected: OK: no cross-locale link
```

All five checks must print their `OK:` line before the file is committed.

---

## File Structure

**Modified (3 existing stubs — replace contents):**
- `en/platform/users/data-model.md` (currently 27 lines → target 150-300 lines)
- `en/platform/users/lifecycle.md` (currently 25 lines → target 150-300 lines)
- `en/platform/users/ui-screens.md` (currently 24 lines → target 150-300 lines)

**Not touched:**
- `en/platform/users.md` landing — the spec explicitly forbids edits in this round
- `th/platform/users/*` — does not exist; TH is a future plan
- Any file outside `en/platform/users/`

---

## Task 1: Expand `data-model.md` (schema view)

**Files:**
- Modify: `en/platform/users/data-model.md` (replace entire contents, keep `dateCreated` frontmatter value)

**Sources for this task:**
- Prisma: `model tb_user`, `model tb_cluster_user`, `model tb_user_tb_business_unit`, `enum enum_platform_role`, `enum enum_cluster_user_role`, `enum enum_user_business_unit_role` in `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
- SPA: `../carmen-platform/src/pages/UserEdit.tsx` (look for `UserFormData` interface to confirm the 8 editable fields), `../carmen-platform/src/types/index.ts`

- [ ] **Step 1: Read Prisma models**

```bash
sed -n '194,220p;368,440p;489,560p;530,575p' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma | less
```

Capture: every field name, Prisma type (e.g. `String @db.Uuid`, `Boolean`, `DateTime @db.Timestamptz(6)`), nullability, defaults, and any `@@index` / `@@unique` constraints under each of the three models. Capture every value of each of the three enums.

- [ ] **Step 2: Read SPA-side shapes (cross-check only)**

```bash
grep -n "UserFormData\|interface User\b\|PLATFORM_ROLES\|BU_ROLES" ../carmen-platform/src/pages/UserEdit.tsx ../carmen-platform/src/types/index.ts
```

Confirm the SPA's idea of the editable fields matches Prisma. Note any discrepancy for Section 5.

- [ ] **Step 3: Rewrite `en/platform/users/data-model.md`**

Replace the entire body (after `---` frontmatter close) with the structure below. Frontmatter: update `date` to `'2026-05-19T15:00:00.000Z'`, keep `dateCreated` as `'2026-05-19T00:00:00.000Z'`, keep `title`, `description`, `tags`, `published`, `editor` unchanged.

Structure:

```markdown
# User — Data Model

> **At a Glance**
> **Tables:** `tb_user` &nbsp;·&nbsp; `tb_cluster_user` &nbsp;·&nbsp; `tb_user_tb_business_unit` &nbsp;·&nbsp; **Enums:** `enum_platform_role` (7 values) &nbsp;·&nbsp; `enum_cluster_user_role` (admin/user) &nbsp;·&nbsp; `enum_user_business_unit_role` (admin/user) &nbsp;·&nbsp; **Audit columns:** standard `created_*`/`updated_*`/`deleted_*` trio on `tb_user` &nbsp;·&nbsp; **Sign-in gate:** only 5 of the 7 `enum_platform_role` values pass `AuthContext.ALLOWED_ROLES`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview
<2-3 paragraphs: entities this module owns (`tb_user` plus the two M:N joins), positioning relative to the cluster module (which authoritatively mutates `tb_cluster_user`) and the BU module (whose own page reads `tb_user_tb_business_unit`).>

## 2. Entities

### 2.1 `tb_user`
<1-paragraph role statement: identity row, drives sign-in, holds platform_role.>

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
<One row per field in the Prisma model. Include `id`, `username`, `email`, `password` (note: hashed; not exposed by API), `platform_role`, `firstname`, `middlename`, `lastname`, `alias_name`, `is_active`, the standard created_*/updated_*/deleted_* audit columns, plus anything else present.>

**Constraints:** <list `@unique`, `@id`, FK targets verbatim>
**Indexes:** <list `@@index` and `@@unique` verbatim>

### 2.2 `tb_cluster_user`
<1-paragraph: M:N join between user and cluster, carries per-cluster role.>

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
<rows from Prisma>

**Constraints:** <verbatim>
**Indexes:** <verbatim>

### 2.3 `tb_user_tb_business_unit`
<1-paragraph: M:N join between user and BU, carries per-BU role and is_default.>

| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |
<rows from Prisma>

**Constraints:** <verbatim>
**Indexes:** <verbatim>

## 3. Relationships
- `tb_user` 1 ─ M `tb_cluster_user` M ─ 1 `tb_cluster` (each user can belong to many clusters)
- `tb_user` 1 ─ M `tb_user_tb_business_unit` M ─ 1 `tb_business_unit` (each user can belong to many BUs)
- `tb_user_tb_business_unit.cluster_id` (if present) FKs to `tb_cluster` — capture if Prisma defines it; this is the integrity link that lets the Add BU dialog scope BUs to the user's existing clusters
- <Add any other FK relations discovered in Prisma `@relation` directives.>

## 4. Enums

- **`enum_platform_role`** — 7 values: `super_admin`, `platform_admin`, `support_manager`, `support_staff`, `security_officer`, `integration_developer`, `user`. One-line meaning per value. Call out: only 5 of these (`super_admin`, `platform_admin`, `support_manager`, `support_staff`, `security_officer`) appear in `AuthContext.ALLOWED_ROLES`; rows carrying `integration_developer` or `user` are valid data but their holders cannot sign in to the Platform admin SPA.
- **`enum_cluster_user_role`** — `admin` / `user`. Per-cluster role on `tb_cluster_user`. Independent of `platform_role`.
- **`enum_user_business_unit_role`** — `admin` / `user`. Per-BU role on `tb_user_tb_business_unit`. Independent of both `platform_role` and the per-cluster role.

## 5. Divergences from carmen-platform SPA shape
<Compare the Prisma `tb_user` fields against `UserFormData` in `UserEdit.tsx` and any user types in `src/types/index.ts`. If everything aligns (8 editable fields plus `username` locked after create), write: "No divergences detected against carmen-platform SPA shape as of 2026-05-19." Otherwise produce a table:>

| # | Item | Prisma has | SPA expects | Action |
|---|------|------------|-------------|--------|

## 6. References

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — models `tb_user`, `tb_cluster_user`, `tb_user_tb_business_unit`; enums `enum_platform_role`, `enum_cluster_user_role`, `enum_user_business_unit_role`.
- **Secondary (consumer shape):** `../carmen-platform/src/pages/UserEdit.tsx` (`UserFormData` interface), `../carmen-platform/src/types/index.ts`, `../carmen-platform/src/services/userService.ts` (API contract).
- **Landing cross-link:** [[users]] for the module overview.
```

Substitute every `<…>` placeholder with content derived from the sources above. Field tables must be derived row-by-row from the actual Prisma model — do not paraphrase.

- [ ] **Step 4: Run verification**

```bash
python3 .specs/verify_frontmatter.py en/platform/users/data-model.md
grep -l '^> \*\*At a Glance\*\*' en/platform/users/data-model.md
grep -nE '^## [0-9]+\. TODO$' en/platform/users/data-model.md && echo "FAIL: TODO heading remains" || echo "OK: no TODO heading"
grep -nE '^## [0-9]+\. At a Glance$' en/platform/users/data-model.md && echo "FAIL: stub At-a-Glance heading remains" || echo "OK: callout-style At-a-Glance"
grep -nE '\(/th/' en/platform/users/data-model.md && echo "FAIL: cross-locale link present" || echo "OK: no cross-locale link"
grep -nE '<[A-Z][a-z]+|<[a-z-]+>' en/platform/users/data-model.md && echo "FAIL: placeholder syntax remains" || echo "OK: no placeholder syntax"
wc -l en/platform/users/data-model.md
```

Expected outputs:
1. `OK: en/platform/users/data-model.md — title='User — Data Model'`
2. `en/platform/users/data-model.md`
3. `OK: no TODO heading`
4. `OK: callout-style At-a-Glance`
5. `OK: no cross-locale link`
6. `OK: no placeholder syntax`
7. Line count between 150 and 300.

- [ ] **Step 5: Commit**

```bash
git add en/platform/users/data-model.md
git commit -m "docs(platform/users): expand data-model from stub to canonical reference

Prisma-derived field tables for tb_user, tb_cluster_user, and
tb_user_tb_business_unit; enum value lists with sign-in-gate
callout; divergence check against carmen-platform SPA shape."
```

---

## Task 2: Expand `lifecycle.md` (operations view)

**Files:**
- Modify: `en/platform/users/lifecycle.md` (replace entire contents, keep `dateCreated`)

**Sources for this task:**
- SPA: `../carmen-platform/src/services/userService.ts` (the 8 API methods)
- SPA: `../carmen-platform/src/pages/UserEdit.tsx` (Change Password dialog, Save flow, mode toggle)
- SPA: `../carmen-platform/src/pages/UserManagement.tsx` (Delete confirm dialog, Hard Delete confirm dialog, Fetch Keycloak handler)
- Landing: `en/platform/users.md` Section 3 "Key Concepts" — for terminology only (do not copy prose)

- [ ] **Step 1: Read the service methods**

```bash
cat ../carmen-platform/src/services/userService.ts
```

Map the 8 methods to their HTTP verb + path + request/response shapes (Common Context table above already lists the endpoints).

- [ ] **Step 2: Read the dialog flows in the SPA pages**

```bash
grep -n "resetPassword\|fetchKeycloakUsers\|hardDelete\|softDelete\|handleDelete\|handleSave\|Change Password\|Hard Delete\|Add BU\|is_active" ../carmen-platform/src/pages/UserManagement.tsx ../carmen-platform/src/pages/UserEdit.tsx | head -60
```

Note the request body shape for each mutating call. Note which dialog requires the operator to type the username/email vs. which only requires a click.

- [ ] **Step 3: Investigate the join-row behaviour on user delete**

```bash
grep -n "onDelete\|cluster_user\|user_tb_business_unit" ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma | head -20
```

Check whether the FK from either join to `tb_user` declares `onDelete: Cascade`. If yes, soft-delete persists the rows (no DELETE statement runs) and hard-delete cascades them. If `onDelete` is unset or `Restrict`, hard-delete will fail until joins are removed first. Document the actual behaviour observed in Section 8 — do not assert without checking.

- [ ] **Step 4: Rewrite `en/platform/users/lifecycle.md`**

Replace the entire body. Frontmatter: update `date` to `'2026-05-19T15:00:00.000Z'`, keep `dateCreated` as `'2026-05-19T00:00:00.000Z'`.

Structure:

```markdown
# User — Lifecycle

> **At a Glance**
> **Operations covered:** create &nbsp;·&nbsp; edit &nbsp;·&nbsp; activate/deactivate (`is_active`) &nbsp;·&nbsp; soft-delete &nbsp;·&nbsp; hard-delete &nbsp;·&nbsp; admin password reset &nbsp;·&nbsp; Keycloak sync &nbsp;·&nbsp; **Not in this product:** SSO, MFA, OAuth, email-link password reset &nbsp;·&nbsp; **Endpoints:** 8 methods under `/api-system/user` &nbsp;·&nbsp; **Cross-entity effects:** cluster assignments (read-only here), BU assignments (mutated here via Add BU dialog)

## 1. Overview
<2-3 paragraphs: scope of operations this page covers; explicit absences (no SSO/MFA/email-reset); how mutations split between this page (user identity + BU assignment) and the cluster page (cluster assignment).>

## 2. Create flow
- **Trigger:** Add User button on `UserManagement` → navigate `/users/new`.
- **Endpoint:** `POST /api-system/user`.
- **Required body fields:** `username`, `email`, `platform_role`, `firstname`, `lastname`, `is_active`; optional: `middlename`, `alias_name`. Password handling at create: <document what the SPA actually sends — `password` field present? Or set later via reset-password?>.
- **Success behaviour:** the SPA calls `navigate('/users/:id/edit', { replace: true })` — the create URL is replaced in history so Back returns to the list, not to a re-open of `/users/new`.
- **Failure behaviour:** <document what the SPA does on 4xx/5xx — toast? Error inline on the form?>

## 3. Edit flow
- **Trigger:** Edit button on a row in `UserManagement`, or the Edit button in the header of `/users/:id/edit`.
- **Endpoint:** `PUT /api-system/user/:id`.
- **Lock on `username`:** `username` is set once at create and disabled in edit mode. The SPA does not send it in the PUT body even when other fields are submitted.
- **Mode toggle:** the page starts in view mode; pressing Edit enables form inputs and reveals Save / Cancel. Cancel reverts the local form state and re-enters view mode without an API call.

## 4. Activate / Deactivate
- **Field:** `is_active` boolean on `tb_user`.
- **Effect:** when `false`, the user can be retained for audit/historical purposes but cannot pass sign-in. This is independent of soft-delete — an active row with `deleted_at` is hidden from the default list; an inactive row without `deleted_at` is visible but cannot sign in.
- **How it's set:** the `is_active` checkbox in the User Details card, persisted with the normal `PUT /api-system/user/:id` request.

## 5. Soft delete vs. Hard delete
### 5.1 Soft delete
- **Trigger:** "Delete" action in the row action menu on `UserManagement`. Confirm dialog: <document — single confirm click? Or typed?>.
- **Endpoint:** `DELETE /api-system/user/:id`.
- **Effect:** server stamps `deleted_at` and `deleted_by_name` on the row. The row is hidden from the default list view; toggling the "Show soft-deleted users" filter brings them back with a red "Deleted" badge and a "Deleted By" column.

### 5.2 Hard delete
- **Trigger:** "Hard Delete" action (separate menu entry).
- **Endpoint:** `DELETE /api-system/user/:id/hard`.
- **Gate:** dialog requires the operator to type the user's exact `username` or `email` to enable the destructive button. <Confirm which field is the type-target.>
- **Effect on join rows:** <document what was found in Step 3. If Prisma declares `onDelete: Cascade` on the two joins' FK to `tb_user`, hard-delete removes them too. If not, document the actual server behaviour observed in the SPA / backend code.>

## 6. Admin-initiated password reset
- **Trigger:** "Change Password" button in the header of `/users/:id/edit`.
- **Dialog:** new password + confirm password fields; minimum 6 characters; the two must match. **Note:** the current password is NOT required — this is an admin override, not a self-service flow. (Self-service password change lives in the [[profile]] module.)
- **Endpoint:** `PUT /api-system/user/:id/reset-password` with body `{ newPassword }`.
- **Post-call behaviour:** the dialog closes; the page does NOT re-fetch the profile and does NOT refresh `AuthContext`. There is no email-link flow.

## 7. Keycloak sync
- **Trigger:** "Fetch Keycloak" button in the `UserManagement` header.
- **Endpoint:** `POST /api-system/fetch-user` via `userService.fetchKeycloakUsers()`.
- **Effect:** backend pulls the current Keycloak user list into the platform DB; the SPA reloads the table after a successful response.
- **Authorization:** the button is visible to any authenticated platform user (no `allowedRoles` gate on the route or the button). Operationally meaningful only for users with backend admin access to Keycloak.

## 8. Cross-entity side effects
- **Cluster assignments (`tb_cluster_user`)** are read-only on this page (Clusters card on `/users/:id/edit`). The canonical mutation surface is the cluster edit page; create a `tb_cluster_user` row there first so the user becomes eligible for the cluster's BUs.
- **BU assignments (`tb_user_tb_business_unit`)** are added and removed here via the Add BU dialog. The dialog filters available BUs to those whose `cluster_id` matches one of the user's current cluster memberships, which enforces the tenant boundary at the UI layer (the backend should re-enforce it).
- **Cascade behaviour on user delete:** <document the actual behaviour from Step 3. Whether soft-delete leaves join rows intact and hard-delete cascades them — or whether the backend pre-clears joins before allowing hard-delete — depends on the Prisma `onDelete` setting and any service-layer logic. State what was observed, not what is assumed.>

## 9. References
- **API surface:** `../carmen-platform/src/services/userService.ts` (all 8 methods).
- **Dialog logic:** `../carmen-platform/src/pages/UserManagement.tsx` (soft / hard delete dialogs, Fetch Keycloak), `../carmen-platform/src/pages/UserEdit.tsx` (Change Password dialog, Save / Cancel flow, mode toggle).
- **Join cascade discovery:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (FK `onDelete` settings on `tb_cluster_user` and `tb_user_tb_business_unit`).
- **Landing cross-link:** [[users]] for module overview, [[profile]] for the user's own self-service password change.
```

Replace every `<…>` placeholder with concrete content drawn from the sources cited in the same paragraph.

- [ ] **Step 5: Run verification**

```bash
python3 .specs/verify_frontmatter.py en/platform/users/lifecycle.md
grep -l '^> \*\*At a Glance\*\*' en/platform/users/lifecycle.md
grep -nE '^## [0-9]+\. TODO$' en/platform/users/lifecycle.md && echo "FAIL: TODO heading remains" || echo "OK: no TODO heading"
grep -nE '^## [0-9]+\. At a Glance$' en/platform/users/lifecycle.md && echo "FAIL: stub At-a-Glance heading remains" || echo "OK: callout-style At-a-Glance"
grep -nE '\(/th/' en/platform/users/lifecycle.md && echo "FAIL: cross-locale link present" || echo "OK: no cross-locale link"
grep -nE '<[A-Z][a-z]+|<[a-z-]+>' en/platform/users/lifecycle.md && echo "FAIL: placeholder syntax remains" || echo "OK: no placeholder syntax"
wc -l en/platform/users/lifecycle.md
```

Expected: same shape as Task 1 — all five `OK:` lines plus a line count between 150 and 300.

- [ ] **Step 6: Commit**

```bash
git add en/platform/users/lifecycle.md
git commit -m "docs(platform/users): expand lifecycle from stub to canonical reference

Eight-endpoint operations view: create, edit, activate/deactivate,
soft + hard delete, admin password reset, Keycloak sync, plus the
read-only / mutating split for cluster and BU assignments."
```

---

## Task 3: Expand `ui-screens.md` (interaction view)

**Files:**
- Modify: `en/platform/users/ui-screens.md` (replace entire contents, keep `dateCreated`)

**Sources for this task:**
- SPA: `../carmen-platform/src/pages/UserManagement.tsx` (list page — 775 lines)
- SPA: `../carmen-platform/src/pages/UserEdit.tsx` (create/view/edit page — 976 lines)
- SPA: `../carmen-platform/src/components/Layout.tsx` (for the sidebar entry that opens this module)
- SPA: `../carmen-platform/SITEMAP.md` (the three user routes)

- [ ] **Step 1: Read SITEMAP for route confirmation**

```bash
sed -n '/^| `\/users/,/^| `\/users\/:id\/edit/p' ../carmen-platform/SITEMAP.md
```

Confirms the three user routes and that all carry "Authenticated" access (no `allowedRoles` array).

- [ ] **Step 2: Read UserManagement.tsx structure**

```bash
grep -n "export\|DataTable\|Filters\|Sheet\|CSV\|Export\|Fetch Keycloak\|Add User\|Dialog\|localStorage\|debounce" ../carmen-platform/src/pages/UserManagement.tsx
```

Capture: filter set (Role multi-select, Status active/inactive, show-soft-deleted toggle), header actions (Fetch Keycloak, Add User, Export), row action menu (Edit / Delete / Hard Delete), audit columns shown, and every `localStorage` key the page writes.

- [ ] **Step 3: Read UserEdit.tsx structure**

```bash
grep -n "Card\|Dialog\|Add BU\|Clusters\|Business Units\|Change Password\|Edit\|Save\|Cancel\|UserFormData\|disabled" ../carmen-platform/src/pages/UserEdit.tsx | head -80
```

Capture: the three cards on view/edit mode (User Details / Clusters read-only / Business Units), the Add BU dialog flow (cluster-scoping of available BUs, role select, is_default checkbox), the Change Password dialog (fields + min-length), the mode toggle (view ↔ edit, `username` disabled in edit), and what happens on Save / Cancel.

- [ ] **Step 4: Rewrite `en/platform/users/ui-screens.md`**

Replace the entire body. Frontmatter: update `date` to `'2026-05-19T15:00:00.000Z'`, keep `dateCreated` as `'2026-05-19T00:00:00.000Z'`.

Structure:

```markdown
# User — UI Screens

> **At a Glance**
> **Screens:** `UserManagement` (list, `/users`) &nbsp;·&nbsp; `UserEdit` create (`/users/new`) &nbsp;·&nbsp; `UserEdit` view/edit (`/users/:id/edit`) &nbsp;·&nbsp; **Dialogs:** Add BU &nbsp;·&nbsp; Change Password &nbsp;·&nbsp; Soft Delete confirm &nbsp;·&nbsp; Hard Delete typed-confirm &nbsp;·&nbsp; **Access:** all three routes are "Authenticated" — no `allowedRoles` prop &nbsp;·&nbsp; **Persisted UI state:** 7 `localStorage` keys on the list page (search, page, perpage, sort, role filter, status filter, show-deleted)

## 1. Overview
<2 paragraphs: the two-screen pattern shared with every other Platform admin module, plus the three header actions specific to users (Fetch Keycloak on list; Change Password on edit; Add BU on edit).>

## 2. `UserManagement` — list page (`/users`)
### 2.1 Layout
<DataTable below a header row containing a debounced search input, a Filters button that opens a Sheet, an Export button, the Fetch Keycloak button, and the Add User button. Below the table: pagination controls.>

### 2.2 Filters (Sheet panel)
- **Role** — multi-select over the seven `PLATFORM_ROLES` values.
- **Status** — active / inactive radio (or tri-state if "all" is supported — verify from source).
- **Show soft-deleted users** — toggle. When on, deleted rows surface with a red "Deleted" badge and a "Deleted By" audit column.

### 2.3 Header actions
- **Fetch Keycloak** — `userService.fetchKeycloakUsers()` (`POST /api-system/fetch-user`); reloads the table on success.
- **Export** — CSV export of the currently filtered set. <Confirm: client-side or server-side export?>
- **Add User** — navigates to `/users/new`.

### 2.4 Row actions
- **Edit** — navigates to `/users/:id/edit`.
- **Delete** (soft) — `DELETE /api-system/user/:id`. <Document the confirm dialog shape.>
- **Hard Delete** — opens the typed-username confirmation dialog (Section 5.4).

### 2.5 Audit columns
<List the audit columns shown: `created_at` + `created_by_name`, `updated_at` + `updated_by_name`, and (when soft-deleted filter is on) `deleted_at` + `deleted_by_name`. Format and timezone if relevant.>

## 3. `UserEdit` — create mode (`/users/new`)
- **Layout:** a single "User Details" card.
- **Form fields:** the eight editable fields — `username`, `email`, `platform_role`, `alias_name`, `firstname`, `middlename`, `lastname`, `is_active`. <Confirm whether the create form includes an initial password field; if not, the user gets a password via the admin reset flow.>
- **Submit:** `POST /api-system/user`; on success, the SPA calls `navigate('/users/:id/edit', { replace: true })`. Back returns to the list, not to a re-open of the create page.

## 4. `UserEdit` — view/edit mode (`/users/:id/edit`)
Three stacked cards. The page starts in view mode; the Edit button in the header toggles all editable cards into edit mode.

### 4.1 User Details card
- **View mode:** read-only display of the eight fields plus the read-only audit fields (id, member-since).
- **Edit mode:** the eight inputs become editable. **`username` is disabled in edit mode** — it is set once at create. Save calls `PUT /api-system/user/:id`; Cancel reverts local state with no API call.

### 4.2 Clusters card (read-only)
- Lists each `tb_cluster_user` row the user belongs to: cluster name, cluster code, active/inactive badge, per-cluster role (`admin` / `user`).
- Mutation happens on the cluster edit page, not here. The card has no Add or Remove control.

### 4.3 Business Units card
- Lists each `tb_user_tb_business_unit` row: BU name, BU code, per-BU role (`admin` / `user`), an `is_default` badge if set, and a Trash icon to remove the assignment.
- Header of the card: **Add BU** button → opens the Add BU dialog (Section 5.1).

## 5. Dialogs
### 5.1 Add BU dialog
- Triggered from the Business Units card on `/users/:id/edit`.
- BU dropdown is scoped: available BUs are filtered to those whose `cluster_id` matches one of the user's current `tb_cluster_user` rows.
- Role select: `admin` / `user` (from `enum_user_business_unit_role`).
- `is_default` checkbox: marks this BU as the user's default landing BU in the inventory app.
- On submit: POSTs a new `tb_user_tb_business_unit` row (via the user-edit save flow or a dedicated endpoint — confirm from source).

### 5.2 Change Password dialog
- Triggered from the header on `/users/:id/edit`.
- Fields: new password, confirm password.
- Validation: minimum 6 characters; the two fields must match.
- Submit: `PUT /api-system/user/:id/reset-password` with body `{ newPassword }`. The dialog closes; the page does not re-fetch the profile and does not refresh `AuthContext`.

### 5.3 Soft Delete confirm
- Triggered from the row action menu on `UserManagement`.
- <Document the confirm UX: simple Yes/No, or typed?>
- Submit: `DELETE /api-system/user/:id`.

### 5.4 Hard Delete confirm
- Triggered from the row action menu on `UserManagement`.
- Requires the operator to type the user's exact `username` or `email` — the destructive button stays disabled until the typed value matches.
- Submit: `DELETE /api-system/user/:id/hard`.

## 6. Persisted UI state
The list page persists 7 keys in `localStorage` so the filter set survives reloads:
<List each key name verbatim from UserManagement.tsx (e.g. `users-list-search`, `users-list-page`, `users-list-perpage`, `users-list-sort`, `users-list-role-filter`, `users-list-status-filter`, `users-list-show-deleted`). The UserEdit page does not persist UI state.>

## 7. Screenshots
> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References
- `../carmen-platform/SITEMAP.md` — route table.
- `../carmen-platform/src/pages/UserManagement.tsx` — list page, filters, header actions, row actions, delete + hard-delete dialogs.
- `../carmen-platform/src/pages/UserEdit.tsx` — create/view/edit page, three-card layout, Add BU dialog, Change Password dialog, mode toggle.
- `../carmen-platform/src/components/Layout.tsx` — sidebar entry for the Users module.
- **Cross-links:** [[users]] (landing), [[clusters]] (mutates `tb_cluster_user`), [[business-units]] (the other surface that mutates the same BU-user join).
```

Replace every `<…>` placeholder with content drawn from the cited source files.

- [ ] **Step 5: Run verification**

```bash
python3 .specs/verify_frontmatter.py en/platform/users/ui-screens.md
grep -l '^> \*\*At a Glance\*\*' en/platform/users/ui-screens.md
grep -nE '^## [0-9]+\. TODO$' en/platform/users/ui-screens.md && echo "FAIL: TODO heading remains" || echo "OK: no TODO heading"
grep -nE '^## [0-9]+\. At a Glance$' en/platform/users/ui-screens.md && echo "FAIL: stub At-a-Glance heading remains" || echo "OK: callout-style At-a-Glance"
grep -nE '\(/th/' en/platform/users/ui-screens.md && echo "FAIL: cross-locale link present" || echo "OK: no cross-locale link"
grep -nE '<[A-Z][a-z]+|<[a-z-]+>' en/platform/users/ui-screens.md && echo "FAIL: placeholder syntax remains" || echo "OK: no placeholder syntax"
grep -n '> \*\*TODO:\*\*' en/platform/users/ui-screens.md
wc -l en/platform/users/ui-screens.md
```

Expected: five `OK:` lines, plus exactly one `> **TODO:**` line (the Screenshots callout in Section 7), plus a line count between 150 and 300.

- [ ] **Step 6: Commit**

```bash
git add en/platform/users/ui-screens.md
git commit -m "docs(platform/users): expand ui-screens from stub to canonical reference

UserManagement list (filters, Fetch Keycloak, hard-delete confirm),
three-card UserEdit (User Details + Clusters read-only + Business
Units with Add BU dialog), Change Password dialog, persisted
localStorage keys. Screenshots deferred to next batch."
```

---

## Task 4: Final cross-page checks and push

**Files:**
- Read-only: all three expanded pages, plus `en/platform/users.md` landing for cross-link integrity.

- [ ] **Step 1: Cross-link integrity**

```bash
# Every [[slug]] in the three sub-pages must resolve to one of the six Platform modules
# or one of the Inventory modules. Print all bracket-links and eyeball:
grep -oE '\[\[[a-z-]+\]\]' en/platform/users/*.md | sort -u
```

Expected slugs (any subset of): `users`, `clusters`, `business-units`, `auth-roles`, `profile`, `report-templates`, plus any Inventory-book slug if cross-referenced.

- [ ] **Step 2: Landing references still resolve**

```bash
grep -nE '\(\./(data-model|lifecycle|ui-screens)\.md\)' en/platform/users.md
```

Expected: three matches in Section 7 of the landing, all pointing at `./data-model.md`, `./lifecycle.md`, `./ui-screens.md`. Confirms the landing's relative links to the now-expanded files still work.

- [ ] **Step 3: Full-tree frontmatter sweep on the new files**

```bash
for f in en/platform/users/data-model.md en/platform/users/lifecycle.md en/platform/users/ui-screens.md; do
  python3 .specs/verify_frontmatter.py "$f"
done
```

Expected: three `OK:` lines.

- [ ] **Step 4: Visual render check on dev Wiki.js**

Open each URL in a browser and confirm the At-a-Glance callout, numbered sections, and tables render correctly. The dev instance may need a re-pull from git; the user can trigger that if pages do not refresh:

- `http://dev.blueledgers.com:3987/en/platform/users/data-model`
- `http://dev.blueledgers.com:3987/en/platform/users/lifecycle`
- `http://dev.blueledgers.com:3987/en/platform/users/ui-screens`

If any page 404s, ask the user whether the dev wiki has pulled the latest commits — do not assume the page is broken.

- [ ] **Step 5: Push to remote** (only after the user confirms the visual render check passed)

```bash
git push origin main
```

- [ ] **Step 6: Final task summary**

Report back to the user:
- Three files expanded from stubs to canonical references (line counts).
- Three commits made on `main` plus a successful push (or a hold if visual check is pending).
- Outstanding: TH mirror (separate plan), screenshots (separate batch), and the four other Platform modules (one spec/plan each, in the order the user chooses).

---

## Self-Review (completed by author of this plan)

**1. Spec coverage:**
- Spec Section 3.1 (`data-model.md` shape) → Task 1. ✓
- Spec Section 3.2 (`lifecycle.md` shape) → Task 2. ✓
- Spec Section 3.3 (`ui-screens.md` shape) → Task 3. ✓
- Spec Section 4 (conventions) → enforced inline in each Task's "Rewrite" step (callout style, no numeric prefix, source-of-truth ordering, inline TODO callout).
- Spec Section 5 (verification gates) → covered across the per-task verification blocks plus Task 4. ✓
- Spec Section 6 (deferrals) → out-of-scope in plan; Task 4 Step 6 surfaces them in the final summary.
- Spec Section 7 (out of scope) → respected (no landing edits, no new files outside the 3 targets, no TH).

**2. Placeholder scan:** the only placeholders in the plan are inside the `<…>` brackets in the "Rewrite" step's structure blocks — those are intentional fillable sections the implementer completes from the cited sources, and the per-task verification grep (`grep -nE '<[A-Z][a-z]+|<[a-z-]+>'`) catches any that survive.

**3. Identifier consistency:** model names (`tb_user`, `tb_cluster_user`, `tb_user_tb_business_unit`), enum names (`enum_platform_role`, `enum_cluster_user_role`, `enum_user_business_unit_role`), and endpoint paths (`/api-system/user`, `/api-system/user/:id/hard`, `/api-system/user/:id/reset-password`, `/api-system/fetch-user`) match across all four tasks and the Common Context block.
