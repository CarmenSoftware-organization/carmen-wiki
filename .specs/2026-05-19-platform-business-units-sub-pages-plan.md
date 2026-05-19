# Platform `business-units/` Sub-Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the two stub sub-pages under `en/platform/business-units/` (`data-model.md`, `ui-screens.md`) into full reference pages, reusing the convention proven by the prior users and clusters rounds.

**Architecture:** Each task replaces one stub file in-place. Sources: backend Prisma platform schema (primary), carmen-platform SPA (secondary), landing for positioning only. EN only this round.

**Tech Stack:** Markdown only. Frontmatter verifier at `.specs/verify_frontmatter.py`. Working directory: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`. Branch: `main`.

**Reference spec:** `.specs/2026-05-19-platform-business-units-sub-pages-design.md`

**Calibration targets** (recently merged):
- `en/platform/users/data-model.md` (235 lines, commit `a1a5686`)
- `en/platform/clusters/data-model.md` (150 lines, commit `77cdda0`)
- `en/platform/users/ui-screens.md` (190 lines, commit `00bda7d`)
- `en/platform/clusters/ui-screens.md` (194 lines, commit `d94923b`)

---

## Common Context

### Sources of truth

**Primary (Prisma platform schema, `prisma-shared-schema-platform/prisma/schema.prisma`):**
- `model tb_business_unit` — starts line 79
- `model tb_business_unit_tb_module` — starts line 146 (M:N BU↔module activation)
- `model tb_module` — starts line 247 (module catalog — referenced only)
- `model tb_user_tb_business_unit` — starts line 489 (M:N BU↔user — full doc in [[users]]/data-model, brief here)
- `enum enum_user_business_unit_role` — starts line 560 (admin / user)

**Secondary (carmen-platform SPA):**
- `../carmen-platform/SITEMAP.md` — three BU routes, all "Authenticated" (no `allowedRoles`)
- `../carmen-platform/src/pages/BusinessUnitManagement.tsx` (543 lines) — list page
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx` (1785 lines — the largest Platform edit page) — create/view/edit page with collapsible form sections
- `../carmen-platform/src/services/businessUnitService.ts` (59 lines) — REST client
- `../carmen-platform/src/types/index.ts` — `BusinessUnit` TS type

**Positioning only (do NOT restate):**
- `en/platform/business-units.md` — landing
- `en/platform/users/data-model.md` (full `tb_user_tb_business_unit` doc — cross-link)
- `en/platform/clusters/data-model.md` (parent cluster — cross-link)

### Frontmatter timestamp

`date` → `'2026-05-19T17:30:00.000Z'`. Keep `dateCreated` (`'2026-05-19T00:00:00.000Z'`).

### Per-task verification

```bash
python3 .specs/verify_frontmatter.py en/platform/business-units/<file>.md
grep -l '^> \*\*At a Glance\*\*' en/platform/business-units/<file>.md
grep -nE '^## [0-9]+\. TODO$' en/platform/business-units/<file>.md && echo "FAIL: TODO heading remains" || echo "OK: no TODO heading"
grep -nE '^## [0-9]+\. At a Glance$' en/platform/business-units/<file>.md && echo "FAIL: stub At-a-Glance heading remains" || echo "OK: callout-style At-a-Glance"
grep -nE '\(/th/' en/platform/business-units/<file>.md && echo "FAIL: cross-locale link present" || echo "OK: no cross-locale link"
grep -n '\[\[data-model\]\]\|\[\[ui-screens\]\]' en/platform/business-units/<file>.md && echo "FAIL: stale sibling-slug link" || echo "OK: no sibling slug links"
wc -l en/platform/business-units/<file>.md
```

Note: the placeholder-syntax grep (`<[A-Z][a-z]+|<[a-z-]+>`) will flag JSX component names (`<BusinessUnitEdit>` etc.) in code spans — these are false positives. Confirm by eyeballing the matches.

All OK lines must print before commit. Line count target 150-300 (density-over-padding allowance applies — clusters/permissions ran 139 and was accepted).

---

## File Structure

**Modified (2 existing stubs — replace contents):**
- `en/platform/business-units/data-model.md` (24 → 150-300 lines)
- `en/platform/business-units/ui-screens.md` (24 → 150-300 lines)

**Not touched:** landing, `th/`, anything outside `en/platform/business-units/`.

---

## Task 1: Expand `data-model.md` (schema view)

**Files:**
- Modify: `en/platform/business-units/data-model.md`

**Sources for this task:** Prisma `model tb_business_unit` (line 79), `model tb_business_unit_tb_module` (line 146), `model tb_module` (line 247, referenced only), `model tb_user_tb_business_unit` (line 489, brief only), `enum enum_user_business_unit_role` (line 560); SPA `BusinessUnit` TS type in `src/types/index.ts`; any `BusinessUnitFormData` interface in `BusinessUnitEdit.tsx`.

- [ ] **Step 1: Read Prisma models**

```bash
sed -n '79,160p;247,300p;485,520p;555,575p' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
```

Capture every field on `tb_business_unit` (including DB connection block + formatting/locale block + info JSON). Capture full `tb_business_unit_tb_module` join. For `tb_module` and `tb_user_tb_business_unit`, capture only fields relevant to the BU perspective.

- [ ] **Step 2: Read SPA BusinessUnit type**

```bash
grep -n "interface BusinessUnit\|type BusinessUnit\|BusinessUnitFormData\|info\|config" ../carmen-platform/src/types/index.ts ../carmen-platform/src/pages/BusinessUnitEdit.tsx | head -30
```

If `tb_business_unit.info` (JSON column) carries structured config, read enough of `BusinessUnitEdit.tsx` to know what keys the SPA writes/reads under `info`.

- [ ] **Step 3: Rewrite `en/platform/business-units/data-model.md`**

Replace the entire body. Frontmatter: `date` → `'2026-05-19T17:30:00.000Z'`, `dateCreated` unchanged.

Structure to fill:

```markdown
# Business Unit — Data Model

> **At a Glance**
> **Tables:** `tb_business_unit` (primary) &nbsp;·&nbsp; `tb_business_unit_tb_module` (M:N modules activation) &nbsp;·&nbsp; `tb_user_tb_business_unit` (M:N user-join, full doc in [[users]]) &nbsp;·&nbsp; `tb_module` (referenced, full catalog out of scope) &nbsp;·&nbsp; **Enums:** `enum_user_business_unit_role` (admin/user) &nbsp;·&nbsp; **Schema features:** formatting/locale block (date/time/currency/decimal/timezone), DB connection block, optional `info` JSON column &nbsp;·&nbsp; **License field:** `max_license_users` caps how many users may be assigned to this BU

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview
2-3 paragraphs positioning `tb_business_unit` as the operational tenant unit beneath a cluster. Explain the three notable schema features (formatting/locale, DB connection, info JSON / config). Cross-reference [[clusters]] (parent) and [[users]] (M:N join full doc).

## 2. Entities

### 2.1 `tb_business_unit`
One-paragraph role statement. Full field table (Field / Prisma Type / Nullable / Description) row-by-row from Prisma. Cover:
- Identity: id, code, name, cluster_id (FK), alias_name (if present)
- Formatting/locale block: date_format, time_format, currency_code, decimal-related fields, timezone, language (verify exact field names)
- DB connection block: db_connection / db_username / db_password / db_name / db_host / db_port (verify exact names)
- License: max_license_users
- Status: is_active
- Soft-delete trio
- `info` Json column (if present)
- Standard audit columns

**Constraints:** verbatim.
**Indexes:** verbatim.

### 2.2 `tb_business_unit_tb_module`
One-paragraph role statement: M:N join activating modules per BU. Full field table (likely: id, business_unit_id FK, module_id FK, is_active, audit columns). Document the practical semantics (which modules are turned on for which BU).

**Constraints:** verbatim.
**Indexes:** verbatim.

### 2.3 `tb_user_tb_business_unit` (BU-side view)
One paragraph: cross-link to [[users]]/data-model for the full field table. Document only the BU-side relevance:
- per-BU `role` from `enum_user_business_unit_role`
- `is_default` flag (which BU the user lands on at login)
- The `Add BU` dialog on the user-edit page scopes available BUs to the user's existing clusters — restate that integrity rule.

### 2.4 `tb_module` (referenced, brief)
One paragraph: the module catalog table is referenced by the M:N join. Document only the FK side; full catalog doc is out of scope. List any enum or status field on `tb_module` that the join references.

## 3. Relationships
Bullet list of FK relations with cardinality:
- `tb_business_unit` M ─ 1 `tb_cluster` (via `cluster_id`)
- `tb_business_unit` 1 ─ M `tb_business_unit_tb_module` M ─ 1 `tb_module`
- `tb_business_unit` 1 ─ M `tb_user_tb_business_unit` M ─ 1 `tb_user`
- Self-FKs (created_by / updated_by → tb_user.id) if present in Prisma.

## 4. Enums
- **`enum_user_business_unit_role`** — values + meaning + independence from cluster role and platform_role. Restate from users/data-model with cross-link.
- Any `tb_business_unit`-local enum if Prisma declares one.

## 5. The `info` JSON column (or config column)
If `tb_business_unit.info` (or equivalent) exists, document the JSON shape used by the SPA. The stub mentioned a "config array (key/value pairs)" — verify whether this is inside `info` or in a separate column or table.

If the SPA writes structured keys (e.g. `info.tax_inclusive`, `info.fiscal_year_start`), list the known keys discovered from `BusinessUnitEdit.tsx`. If you cannot enumerate them confidently, document what the column carries with a verification hint (e.g. "JSON object; the SPA writes BU-level configuration keys read by inventory features — see `BusinessUnitEdit.tsx` lines <N>-<N>").

If the `info` column does NOT carry config (or doesn't exist), drop this section and renumber the remaining sections.

## 6. Divergences from carmen-platform SPA shape
Compare Prisma `tb_business_unit` against `BusinessUnit` TS type and `BusinessUnitFormData` interface. Table or "No divergences detected as of 2026-05-19."

## 7. References
- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (`tb_business_unit`, `tb_business_unit_tb_module`, `tb_module`, `tb_user_tb_business_unit`, `enum_user_business_unit_role`).
- **Secondary (consumer shape):** `../carmen-platform/src/pages/BusinessUnitEdit.tsx`, `../carmen-platform/src/pages/BusinessUnitManagement.tsx`, `../carmen-platform/src/services/businessUnitService.ts`, `../carmen-platform/src/types/index.ts`.
- **Cross-links:** [[business-units]] (landing), [[clusters]] (parent — supplies `cluster_id`), [[users]] (full `tb_user_tb_business_unit` doc), sibling [UI Screens](./ui-screens.md).
```

- [ ] **Step 4: Run verification** (per-task block, substituting `data-model.md`)

- [ ] **Step 5: Commit**

```bash
git add en/platform/business-units/data-model.md
git commit -m "docs(platform/business-units): expand data-model from stub to canonical reference

Prisma-derived field tables for tb_business_unit (identity +
formatting/locale + DB connection + info JSON), tb_business_unit_tb_module
(M:N modules activation), brief BU-side views of tb_user_tb_business_unit
and tb_module with cross-links to their full docs, divergence check
against SPA BusinessUnit type."
```

---

## Task 2: Expand `ui-screens.md` (interaction view)

**Files:**
- Modify: `en/platform/business-units/ui-screens.md`

**Sources:** `BusinessUnitManagement.tsx` (543 lines), `BusinessUnitEdit.tsx` (1785 lines — large, expect many sections/dialogs), `businessUnitService.ts`, `SITEMAP.md`.

- [ ] **Step 1: Read SITEMAP**

```bash
sed -n '/^| `\/business-units/,/^| `\/business-units\/:id\/edit/p' ../carmen-platform/SITEMAP.md
```

Confirm the three BU routes and that they are "Authenticated" (no `allowedRoles`).

- [ ] **Step 2: Read BusinessUnitManagement.tsx**

```bash
grep -n "export\|DataTable\|Filters\|Sheet\|CSV\|Export\|Add Business Unit\|Add BU\|Dialog\|localStorage\|debounce\|hardDelete\|handleDelete\|cluster_id" ../carmen-platform/src/pages/BusinessUnitManagement.tsx
```

Capture filter set, header actions, row actions, audit columns, every `localStorage` key, whether the list page filters by cluster.

- [ ] **Step 3: Read BusinessUnitEdit.tsx structure (large file — be systematic)**

```bash
grep -n "Card\|Collapsible\|Accordion\|Section\|Dialog\|Add User\|Module\|isNew\|disabled\|handleSave\|cluster_id\|navigate\|info\|config" ../carmen-platform/src/pages/BusinessUnitEdit.tsx | head -150
```

Then read the file in chunks to enumerate the actual form sections (the page has collapsible/grouped form sections — list each by visible label and what fields belong to it):

```bash
sed -n '1,200p' ../carmen-platform/src/pages/BusinessUnitEdit.tsx
sed -n '200,500p' ../carmen-platform/src/pages/BusinessUnitEdit.tsx
sed -n '500,900p' ../carmen-platform/src/pages/BusinessUnitEdit.tsx
sed -n '900,1300p' ../carmen-platform/src/pages/BusinessUnitEdit.tsx
sed -n '1300,1785p' ../carmen-platform/src/pages/BusinessUnitEdit.tsx
```

Note: you do NOT need to memorize every line. Capture: section headers (in order), fields per section, each dialog (trigger / fields / endpoint).

- [ ] **Step 4: Rewrite `en/platform/business-units/ui-screens.md`**

Replace the entire body. Frontmatter: `date` → `'2026-05-19T17:30:00.000Z'`, `dateCreated` unchanged.

Structure:

```markdown
# Business Unit — UI Screens

> **At a Glance**
> **Screens:** `BusinessUnitManagement` (list, `/business-units`) &nbsp;·&nbsp; `BusinessUnitEdit` create (`/business-units/new`) &nbsp;·&nbsp; `BusinessUnitEdit` view/edit (`/business-units/:id/edit`) &nbsp;·&nbsp; **Edit layout:** N collapsible form sections (Identity · Cluster · Locale · DB Connection · Modules · Users · …) &nbsp;·&nbsp; **Dialogs:** Add User to BU &nbsp;·&nbsp; Edit BU User &nbsp;·&nbsp; Remove BU User &nbsp;·&nbsp; Soft Delete confirm &nbsp;·&nbsp; (plus any others discovered) &nbsp;·&nbsp; **Access:** all three routes "Authenticated" — no `allowedRoles` prop &nbsp;·&nbsp; **Persisted UI state:** N `localStorage` keys

(Substitute N and the actual section list from your reading of BusinessUnitEdit.tsx.)

## 1. Overview
2 paragraphs: two-screen pattern; the BU edit page's collapsible form sections (largest Platform edit page; 1785 lines of source); cross-references to the navigate-to-new flow from [[clusters]] (passing `?cluster_id=<id>`).

## 2. `BusinessUnitManagement` — list page (`/business-units`)
### 2.1 Layout
DataTable + header row.

### 2.2 Filters (Sheet panel)
List every filter actually wired (verify: cluster select? active/inactive? show-soft-deleted?).

### 2.3 Header actions
Add BU, Export, any others.

### 2.4 Row actions
Edit / Delete (soft) / Hard Delete if present.

### 2.5 Audit columns

## 3. `BusinessUnitEdit` — create mode (`/business-units/new`)
- Layout: form sections (likely subset shown vs. edit mode — verify).
- Query-param wiring: `?cluster_id=<id>` from `[[clusters]]` edit page's Add BU flow — document whether the create form pre-selects the cluster.
- Form fields: the BU identity + locale + DB-connection set (sections shown in create mode).
- Submit endpoint and post-create navigate destination.

## 4. `BusinessUnitEdit` — view/edit mode (`/business-units/:id/edit`)
Collapsible / accordion form sections. Page starts in view mode; Edit toggles to edit mode. List the actual sections in source order:

### 4.1 <Section A name>
What fields belong here. Whether any field is locked in edit mode.

### 4.2 <Section B name>
…

(Continue for each section discovered in BusinessUnitEdit.tsx. Likely 5-10 sections. If a section deserves its own §4.X subsection, give it one; if a section is one-bullet small, group it with a sibling.)

The Modules section (`tb_business_unit_tb_module`) and the Users section (`tb_user_tb_business_unit`) deserve their own subsections because they carry their own dialogs.

## 5. Dialogs
Enumerate every dialog reachable from the BU surface. Likely candidates (verify presence):

### 5.1 Add User to BU dialog
Trigger / search target / role select / is_default checkbox if present / endpoint.

### 5.2 Edit BU User dialog
Trigger / fields / endpoint.

### 5.3 Remove BU User confirm
Trigger / UX (simple Yes/No or typed) / endpoint.

### 5.4 Module activation/deactivation
Whether there is a dialog or in-place toggle. Document the actual UX.

### 5.5 Soft Delete BU confirm
Trigger / UX / endpoint.

(Add 5.6+ if more dialogs are discovered.)

## 6. Persisted UI state
List every `localStorage` key the list page writes. Table format (Key / Stored type / Persists) matching `en/platform/users/ui-screens.md` §6.

## 7. Screenshots
> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References
- `../carmen-platform/SITEMAP.md`
- `../carmen-platform/src/pages/BusinessUnitManagement.tsx`
- `../carmen-platform/src/pages/BusinessUnitEdit.tsx`
- `../carmen-platform/src/services/businessUnitService.ts`
- Cross-links: [[business-units]] (landing), [[clusters]] (parent and source of the `?cluster_id=<id>` query param), [[users]] (the other surface that mutates the same BU-user join), [Data Model](./data-model.md).
```

- [ ] **Step 5: Run verification** (per-task block, substituting `ui-screens.md`)

Expected: all OK lines + exactly one `> **TODO:**` line + line count 150-300.

- [ ] **Step 6: Commit**

```bash
git add en/platform/business-units/ui-screens.md
git commit -m "docs(platform/business-units): expand ui-screens from stub to canonical reference

BusinessUnitManagement list (filters, Add BU, soft-delete confirm),
BusinessUnitEdit with N collapsible form sections (Identity / Locale /
DB Connection / Modules / Users / etc.), Add/Edit/Remove BU User
dialogs, module activation flow, navigate-to-new cluster_id query
param honoured, persisted localStorage keys. Screenshots deferred."
```

---

## Task 3: Final cross-page checks + push

**Files:**
- Read-only: both expanded pages + landing.

- [ ] **Step 1: Cross-link integrity**

```bash
grep -oE '\[\[[a-z-]+\]\]' en/platform/business-units/*.md | sort -u
ls en/platform/business-units.md en/platform/clusters.md en/platform/users.md en/platform/profile.md en/platform/auth-roles.md en/platform/business-units/data-model.md en/platform/business-units/ui-screens.md
```

- [ ] **Step 2: Landing references + stub annotations**

```bash
grep -nE '\(\./(data-model|ui-screens)\.md\)' en/platform/business-units.md
grep -n "stub — in progress" en/platform/business-units.md
```

Expected: two landing references (§7 of landing) + stub-annotation grep result (may have annotations, may not).

- [ ] **Step 3: Frontmatter + per-file verification on both files**

(Same per-task block as in Tasks 1 and 2, run for both files.)

- [ ] **Step 4: Sibling-slug consistency**

```bash
grep -n '\[\[data-model\]\]\|\[\[ui-screens\]\]' en/platform/business-units/*.md && echo "FAIL" || echo "OK"
```

- [ ] **Step 5: Visual render check on dev Wiki.js**

User opens:
- `http://dev.blueledgers.com:3987/en/platform/business-units/data-model`
- `http://dev.blueledgers.com:3987/en/platform/business-units/ui-screens`

- [ ] **Step 6: Push** (only after user confirms visual check)

```bash
git push origin main
```

- [ ] **Step 7: Optional landing stub-cleanup patch**

If Step 2 found `(stub — in progress)` annotations on the landing, produce a single-commit patch removing them (same shape as commit `12c8c50` for users and `db06f63` for clusters).

---

## Self-Review

**1. Spec coverage:**
- Spec §3.1 (`data-model.md`) → Task 1. ✓
- Spec §3.2 (`ui-screens.md`) → Task 2. ✓
- Spec §4 (inherited conventions) → enforced inline. ✓
- Spec §5 (verification gates) → per-task block + Task 3. ✓

**2. Placeholder scan:** `<…>` brackets only inside the "Rewrite" step's structure blocks (intentional fillable sections). Per-task grep catches survivors.

**3. Identifier consistency:** model names (`tb_business_unit`, `tb_business_unit_tb_module`, `tb_module`, `tb_user_tb_business_unit`), endpoint paths (`/api-system/business-unit`), and component names (`BusinessUnitManagement`, `BusinessUnitEdit`) match across all three tasks.
