# Platform `report-templates/` Sub-Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the `report-templates/` module into four sub-pages (two new files, two stub expansions), the fourth and final multi-page Platform module. This is the FIRST round to use the formal template spec (`.specs/platform-sub-page-template.md`) as predecessor.

**Architecture:** Two stubs replaced in-place (`ui-screens.md`, `xml-spec.md`); two new files created (`data-model.md`, `permissions.md`). EN only this round. Conventions inherited from the template spec.

**Tech Stack:** Markdown only. Frontmatter verifier at `.specs/verify_frontmatter.py`. Branch: `main`.

**Reference spec:** `.specs/2026-05-19-platform-report-templates-sub-pages-design.md`

**Reference predecessors:**
- `.specs/platform-sub-page-template.md` — formal convention.
- `en/platform/clusters/permissions.md` (commit `d6a818b`, 139 lines) — calibration target for `permissions.md`; same role gate.
- `en/platform/business-units/data-model.md` (commit `6a64ef5`, 261 lines) — calibration target for `data-model.md` (grouped field table pattern).
- `en/platform/clusters/ui-screens.md` (commit `d94923b`, 194 lines) — calibration target for `ui-screens.md`.

---

## Common Context

### Sources of truth

**Primary (Prisma platform schema):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
  - `model tb_report_template` — starts line 567
  - (Out of scope: `model tb_print_template_mapping` starts line 641 — sibling feature, separate spec)
  - Any `source_type` enum if Prisma declares one — verify (could be inline enum on the column)

**Secondary (carmen-platform SPA):**
- `../carmen-platform/SITEMAP.md` — three report-template routes (`/report-templates`, `/report-templates/new`, `/report-templates/:id/edit`)
- `../carmen-platform/src/pages/ReportTemplateManagement.tsx` (550 lines)
- `../carmen-platform/src/pages/ReportTemplateEdit.tsx` (1000 lines)
- `../carmen-platform/src/services/reportTemplateService.ts` (97 lines — note `listDbObjects` method for the probe)
- `../carmen-platform/src/App.tsx` lines 114, 122, 130 — the three report-templates `allowedRoles` declarations
- `../carmen-platform/src/types/index.ts` — `ReportTemplate` TS type

### Frontmatter timestamp

`date` → `'2026-05-19T18:30:00.000Z'`. For the 2 existing stubs: keep `dateCreated` (`'2026-05-19T00:00:00.000Z'`). For the 2 new files: set both `date` and `dateCreated` to `'2026-05-19T18:30:00.000Z'`.

### Per-task verification

Standard grep set from template §7. The placeholder-syntax grep (`<[A-Z][a-z]+|<[a-z-]+>`) WILL fire on `xml-spec.md` (and to a lesser extent `ui-screens.md`) because XML element names and JSX component names look like template placeholders. Confirm matches by eyeball — accept JSX/XML refs inside code fences/inline backticks.

---

## File Structure

**Created (2 new files):**
- `en/platform/report-templates/data-model.md`
- `en/platform/report-templates/permissions.md`

**Modified (2 stubs replaced):**
- `en/platform/report-templates/ui-screens.md` (28 → target 200-280 lines)
- `en/platform/report-templates/xml-spec.md` (25 → target 180-280 lines including a worked example)

**Not touched:** the landing, `th/`, any file outside `en/platform/report-templates/`. The landing patch is a separate post-implementation commit.

---

## Task 1: Create `data-model.md` (new file)

**Files:**
- Create: `en/platform/report-templates/data-model.md`

**Sources:** Prisma `model tb_report_template` (line 567); SPA `ReportTemplate` TS type in `src/types/index.ts`; `ReportTemplateFormData` interface in `ReportTemplateEdit.tsx` if present; `source_params` JSON shape from validator code in `ReportTemplateEdit.tsx`.

- [ ] **Step 1: Read Prisma `tb_report_template`**

```bash
sed -n '567,640p' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma
```

Capture every field. Note whether `source_type` is a Prisma enum (`enum_xyz`) or a plain `String` column with values enforced at the SPA. Note nullable JSON columns (`dialog`, `content`, `source_params`).

- [ ] **Step 2: Read SPA ReportTemplate type**

```bash
grep -n "interface ReportTemplate\|type ReportTemplate\|ReportTemplateFormData\|source_params\|source_type" ../carmen-platform/src/types/index.ts ../carmen-platform/src/pages/ReportTemplateEdit.tsx | head -40
```

Capture the `source_params` JSON element shape (`{ filter, type, nullable }`).

- [ ] **Step 3: Write `en/platform/report-templates/data-model.md` (new file)**

Frontmatter: `date` and `dateCreated` both `'2026-05-19T18:30:00.000Z'`.

Structure (substitute `<…>` with sourced content):

```markdown
---
title: Report Template — Data Model
description: tb_report_template entity, dialog/content XML payloads, source binding, BU scope.
published: true
date: 2026-05-19T18:30:00.000Z
tags: book/platform, report-templates, data-model
editor: markdown
dateCreated: 2026-05-19T18:30:00.000Z
---

# Report Template — Data Model

> **At a Glance**
> **Tables:** `tb_report_template` (primary) &nbsp;·&nbsp; **Out of scope:** `tb_print_template_mapping` (sibling feature pair, separate documentation) &nbsp;·&nbsp; **JSON payloads:** `dialog` (XML), `content` (XML), `source_params` (`{ params: [...] }`) &nbsp;·&nbsp; **Source binding:** `source_type` (view/function/procedure) + `source_name` + `source_params` &nbsp;·&nbsp; **BU scope:** comma-separated allow/deny code lists &nbsp;·&nbsp; **Lifecycle flags:** `is_standard`, `is_active`

> **Source of truth:** Backend Prisma platform schema. Always read this first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` file is an auto-generated copy and not authoritative.

## 1. Overview
2-3 paragraphs positioning `tb_report_template` as the catalogue entry that captures one printable/exportable document — identity, XML payloads, runtime source binding, BU scope, lifecycle flags. Position relative to neighbour modules: [[business-units]] (BU codes referenced in chip lists), [[clusters]] (sibling admin-tier-gated surface).

## 2. Entities

### 2.1 `tb_report_template`
One-paragraph role statement. Full field table row-by-row from Prisma. Use bold separator rows to group fields if 15+ fields warrant it (Identity / XML Payloads / Source Binding / BU Scope / Lifecycle / Audit / Soft-delete).

**Constraints:** verbatim.
**Indexes:** verbatim.

## 3. Relationships
Bullet list of FK relations (likely minimal: created_by/updated_by self-FKs to `tb_user`). If there are no other FKs, state that explicitly: "Report templates are tenant-global; there is no FK to cluster, BU, or any other tenant container."

## 4. Enums
- **`source_type`** — values `view` / `function` / `procedure`. If declared as a Prisma enum (`enum_source_type` or similar), reference it; if it's a plain String column, note the SPA-side validation in `ReportTemplateEdit.tsx`.
- Any other BU-local enum if Prisma declares one.

## 5. The JSON columns (`dialog`, `content`, `source_params`)
Three Json? columns. Document each:

### 5.1 `dialog` (XML payload)
String of XML rendered by the report runtime as the parameter form. Detailed XML structure documented in `[XML Spec](./xml-spec.md) §2`.

### 5.2 `content` (XML payload)
String of XML rendered by the report runtime as the output. Detailed structure in `[XML Spec](./xml-spec.md) §3`. The Content tab in the editor also accepts `.frx` / `.xml` / `.txt` file uploads (legacy FastReport migration).

### 5.3 `source_params` (object)
Shape: `{ params: [{ filter: string, type: string, nullable: boolean }, ...] }`. Each element maps one Dialog filter field name (e.g. `DateFrom`) to a PostgreSQL type (e.g. `date`, `uuid`, `text`) plus a nullability flag.

Empty `{}` or `{ params: [] }` is valid when `source_type === 'view'` (views take no parameters). For `function` and `procedure`, the array order is positional.

## 6. Divergences from carmen-platform SPA shape
Compare Prisma `tb_report_template` against `ReportTemplate` TS type and `ReportTemplateFormData` interface. Table or "No divergences detected against carmen-platform SPA shape as of 2026-05-19."

## 7. References
- **Primary:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (`tb_report_template`, line 567).
- **Secondary:** `../carmen-platform/src/pages/ReportTemplateEdit.tsx`, `../carmen-platform/src/pages/ReportTemplateManagement.tsx`, `../carmen-platform/src/services/reportTemplateService.ts`, `../carmen-platform/src/types/index.ts`.
- **Cross-links:** [[report-templates]] (landing), [[business-units]] (BU codes referenced in chip lists), [[clusters]] (sibling admin-tier-gated surface), sibling [Permissions](./permissions.md), [UI Screens](./ui-screens.md), [XML Spec](./xml-spec.md).
```

- [ ] **Step 4: Run verification**

```bash
python3 .specs/verify_frontmatter.py en/platform/report-templates/data-model.md
grep -l '^> \*\*At a Glance\*\*' en/platform/report-templates/data-model.md
grep -nE '^## [0-9]+\. TODO$' en/platform/report-templates/data-model.md && echo "FAIL: TODO heading" || echo "OK: no TODO heading"
grep -nE '^## [0-9]+\. At a Glance$' en/platform/report-templates/data-model.md && echo "FAIL: stub heading" || echo "OK: callout-style"
grep -nE '\(/th/' en/platform/report-templates/data-model.md && echo "FAIL: cross-locale link" || echo "OK: no cross-locale link"
grep -n '\[\[data-model\]\]\|\[\[permissions\]\]\|\[\[ui-screens\]\]\|\[\[xml-spec\]\]' en/platform/report-templates/data-model.md && echo "FAIL: sibling-slug link" || echo "OK: no sibling-slug links"
wc -l en/platform/report-templates/data-model.md
```

Expected: all OK lines + line count 150-300.

- [ ] **Step 5: Commit**

```bash
git add en/platform/report-templates/data-model.md
git commit -m "docs(platform/report-templates): add data-model sub-page

Prisma-derived field table for tb_report_template; JSON-column
detail for dialog/content/source_params; divergence check against
SPA ReportTemplate type."
```

---

## Task 2: Create `permissions.md` (new file)

**Files:**
- Create: `en/platform/report-templates/permissions.md`

**Calibration:** `en/platform/clusters/permissions.md` (commit `d6a818b`, 139 lines) — the original permissions.md. Same role gate, same shape; substitute "report-templates" for "clusters" throughout and cross-link generously to the cluster page for the bootstrap-exception detail.

**Sources:** `src/App.tsx` lines 114, 122, 130; `src/context/AuthContext.tsx`; `src/components/PrivateRoute.tsx`; `src/components/Layout.tsx`; Prisma `enum_platform_role` (line 539).

- [ ] **Step 1: Read App.tsx report-templates route guards**

```bash
sed -n '108,135p' ../carmen-platform/src/App.tsx
```

Confirm lines 114, 122, 130 each carry `allowedRoles={["platform_admin", "support_manager", "support_staff"]}`.

- [ ] **Step 2: Read Layout sidebar for Report Templates nav item**

```bash
grep -n "Report Template\|report-templates\|roles" ../carmen-platform/src/components/Layout.tsx | head -20
```

Capture the Report Templates nav item's `roles` field.

- [ ] **Step 3: Write `en/platform/report-templates/permissions.md` (new file)**

Frontmatter: `date` and `dateCreated` both `'2026-05-19T18:30:00.000Z'`.

Structure:

```markdown
---
title: Report Template — Permissions
description: Route gates, effective access matrix, AccessDenied behaviour, sidebar filter — all three report-templates routes admin-tier-gated.
published: true
date: 2026-05-19T18:30:00.000Z
tags: book/platform, report-templates, permissions
editor: markdown
dateCreated: 2026-05-19T18:30:00.000Z
---

# Report Template — Permissions

> **At a Glance**
> **Gate:** all three report-templates routes carry `allowedRoles={["platform_admin", "support_manager", "support_staff"]}` &nbsp;·&nbsp; **Bootstrap exception:** same `userCount <= 1` mechanic as [Clusters Permissions §4](../clusters/permissions.md) &nbsp;·&nbsp; **On role failure:** `<AccessDenied>` renders inside `<Layout>` &nbsp;·&nbsp; **Sidebar filter:** Report Templates entry hidden from users who fail `hasRole()` &nbsp;·&nbsp; **No per-button role gates** within the surface

## 1. Overview
Two paragraphs: why report-templates is role-gated (Carmen-internal authoring surface; not exposed to customers); contrast with open-access modules. Note that report-templates shares the EXACT same role gate as [[clusters]] — three Carmen admin-tier roles — and cross-link to that page's matrix for the canonical detail.

## 2. Route guards

| Route | Component | `allowedRoles` | Source |
|---|---|---|---|
| `/report-templates` | `ReportTemplateManagement` | `platform_admin`, `support_manager`, `support_staff` | `src/App.tsx` line 114 |
| `/report-templates/new` | `ReportTemplateEdit` | (same) | line 122 |
| `/report-templates/:id/edit` | `ReportTemplateEdit` | (same) | line 130 |

The `allowedRoles` array is hardcoded inline at each route (no shared constant), matching the pattern documented in `../clusters/permissions.md` §2.

## 3. Effective access matrix

Reading guide: sign-in eligibility (`AuthContext.ALLOWED_ROLES`, see [[auth-roles]]) is checked first at login; route eligibility (the `allowedRoles` array on `PrivateRoute`) is checked only for roles that can sign in. The "Effective access" column states the combined outcome.

| `platform_role` | Can sign in? | In report-templates `allowedRoles`? | Effective access |
|---|---|---|---|
| `super_admin` | Yes | No | No — `<AccessDenied>` |
| `platform_admin` | Yes | Yes | Full |
| `support_manager` | Yes | Yes | Full |
| `support_staff` | Yes | Yes | Full |
| `security_officer` | Yes | No | No — `<AccessDenied>` |
| `integration_developer` | No | n/a | Cannot sign in to SPA |
| `user` | No | n/a | Cannot sign in to SPA |

The matrix is identical to the clusters matrix. The bootstrap exception applies the same way (see §4).

## 4. Bootstrap exception
The `userCount <= 1` shortcut in `AuthContext.hasRole()` works identically for every role-gated module. Full detail (the `null` vs `<= 1` vs `> 1` cases, the non-reactive refetch behaviour) is in `[Clusters Permissions §4](../clusters/permissions.md) §4`. The same caveats apply here: during the API loading window, normal role checking applies; once `userCount > 1`, the exception goes dormant.

## 5. AccessDenied behaviour
Same as [Clusters Permissions §5](../clusters/permissions.md) §5 — on role-fail, `<AccessDenied>` renders inside the normal `<Layout>` (sidebar stays); on auth-fail, redirect to `/login`. The "Back to Dashboard" button navigates to `/dashboard`.

## 6. Sidebar filter
`Layout.tsx` filters its `NavItem[]` through `hasRole()`. The Report Templates nav item's `roles` field is set to `["platform_admin", "support_manager", "support_staff"]` (verify exact form). The list MUST match the route-guard list above — any divergence would expose the sidebar entry while blocking the route. Any future change to which roles may access Report Templates must be applied in BOTH `src/App.tsx` (lines 114, 122, 130) AND `src/components/Layout.tsx` (the sidebar `NavItem` `roles` field).

## 7. Within the report-templates surface
Once a user passes the route guard, the SPA does NOT additionally gate individual buttons or fields by `platform_role`:
- Edit, Save, Cancel — visible to every authorized user.
- Add Template — visible.
- Soft Delete — visible.
- Browse in BU probe — visible.
- File upload (Content tab) — visible.
- Standard/Custom and Active/Inactive toggles — visible.

There is no "viewer" sub-role within this module.

## 8. References
- `src/App.tsx` — route wiring (lines 114, 122, 130).
- `src/context/AuthContext.tsx` — `ALLOWED_ROLES`, `hasRole`, `userCount` bootstrap.
- `src/components/PrivateRoute.tsx` — gate logic, `<AccessDenied>` render.
- `src/components/Layout.tsx` — sidebar nav filter.
- Prisma `enum_platform_role` for the 7-value source list.
- Cross-links: [[auth-roles]] (full role definitions); [[users]] (where `platform_role` is set); `[Clusters Permissions](../clusters/permissions.md)` (canonical permissions.md shape; same role gate); sibling `[Data Model](./data-model.md)`, `[UI Screens](./ui-screens.md)`, `[XML Spec](./xml-spec.md)`.
```

- [ ] **Step 4: Run verification** (same grep set as Task 1, target 130-180 lines — permissions.md can be on the lower end since it cross-links to clusters/permissions for shared mechanics).

- [ ] **Step 5: Commit**

```bash
git add en/platform/report-templates/permissions.md
git commit -m "docs(platform/report-templates): add permissions sub-page

Route-guard table for 3 routes, effective access matrix (identical
to clusters), bootstrap exception via cross-link to clusters/permissions,
sidebar filter, within-surface action list. Second use of the
permissions.md shape established by clusters."
```

---

## Task 3: Expand `ui-screens.md` (existing stub)

**Files:**
- Modify: `en/platform/report-templates/ui-screens.md`

**Sources:** SITEMAP.md; `ReportTemplateManagement.tsx` (550 lines); `ReportTemplateEdit.tsx` (1000 lines) — particularly the tabbed editor layout, source section, BU chip inputs, sticky action bar; `reportTemplateService.ts` (note `listDbObjects`).

- [ ] **Step 1: SITEMAP**

```bash
sed -n '/^| `\/report-templates/,/^| `\/report-templates\/:id\/edit/p' ../carmen-platform/SITEMAP.md
```

- [ ] **Step 2: Read ReportTemplateManagement.tsx**

```bash
grep -n "export\|DataTable\|Filters\|Sheet\|CSV\|Export\|Add\|Dialog\|localStorage\|debounce\|is_standard\|is_active\|hardDelete\|handleDelete" ../carmen-platform/src/pages/ReportTemplateManagement.tsx
```

Capture: filter set (Standard/Custom + Active/Inactive likely), header actions, row actions, localStorage keys.

- [ ] **Step 3: Read ReportTemplateEdit.tsx**

```bash
grep -n "Tab\|CodeMirror\|Card\|Dialog\|source_type\|source_name\|source_params\|allow_business_unit\|deny_business_unit\|builder_key\|is_standard\|is_active\|Browse\|listDbObjects\|useUnsavedChanges\|StickyBar" ../carmen-platform/src/pages/ReportTemplateEdit.tsx | head -80
```

Then read chunks:

```bash
sed -n '1,250p' ../carmen-platform/src/pages/ReportTemplateEdit.tsx
sed -n '250,550p' ../carmen-platform/src/pages/ReportTemplateEdit.tsx
sed -n '550,800p' ../carmen-platform/src/pages/ReportTemplateEdit.tsx
sed -n '800,1000p' ../carmen-platform/src/pages/ReportTemplateEdit.tsx
```

Capture: left-pane sections (Identity / Source binding / BU Scope / Lifecycle), right-pane tabs (Dialog XML, Content XML, Preview), the Browse-in-BU dialog, the sticky action bar, the unsaved-changes hook integration.

- [ ] **Step 4: Rewrite `en/platform/report-templates/ui-screens.md`**

Replace entire body. Keep `dateCreated` (`'2026-05-19T00:00:00.000Z'`); set `date` to `'2026-05-19T18:30:00.000Z'`.

Structure (mirror clusters/ui-screens and business-units/ui-screens):

```markdown
# Report Template — UI Screens

> **At a Glance**
> **Screens:** `ReportTemplateManagement` (list, `/report-templates`) &nbsp;·&nbsp; `ReportTemplateEdit` create (`/report-templates/new`) &nbsp;·&nbsp; `ReportTemplateEdit` view/edit (`/report-templates/:id/edit`) &nbsp;·&nbsp; **Edit layout:** 2-pane (left: identity + source + BU scope + lifecycle &nbsp;·&nbsp; right: 3-tab CodeMirror — Dialog XML, Content XML, Preview) &nbsp;·&nbsp; **Dialogs:** Browse in BU &nbsp;·&nbsp; Soft Delete confirm (verify) &nbsp;·&nbsp; **Access:** all three routes gated to `platform_admin` / `support_manager` / `support_staff` (see [Permissions](./permissions.md)) &nbsp;·&nbsp; **Persisted UI state:** N `localStorage` keys (substitute count)

## 1. Overview
2 paragraphs: two-screen pattern; the 2-pane edit layout with 3-tab CodeMirror right pane; cross-reference to [XML Spec](./xml-spec.md) for the XML structures the tabs accept.

## 2. `ReportTemplateManagement` — list page (`/report-templates`)
### 2.1 Layout
### 2.2 Filters (Sheet panel)
Standard / Custom toggle; Active / Inactive toggle; show-soft-deleted (verify).

### 2.3 Header actions
Export, Add Template, etc.

### 2.4 Row actions
Edit / Delete (soft) / Hard Delete if present.

### 2.5 Audit columns

## 3. `ReportTemplateEdit` — create mode (`/report-templates/new`)
- Layout: same 2-pane structure as edit mode but with empty Dialog/Content panes.
- Required fields at create.
- Submit endpoint, navigate destination on success.

## 4. `ReportTemplateEdit` — view/edit mode (`/report-templates/:id/edit`)
2-pane layout. Page starts in view mode; Edit toggles to edit mode (or always-editable — verify).

### 4.1 Left pane — Identity section
Fields (name, description, report_group, builder_key). Locked-in-edit-mode fields if any.

### 4.2 Left pane — Source binding section
`source_type` select (view/function/procedure), `source_name` input, `source_params` editable list. Document the **"Browse in BU"** button that opens the probe dialog (§5.1).

### 4.3 Left pane — BU Scope section
`allow_business_unit` and `deny_business_unit` chip inputs. Document the UX (typing comma-separated codes, autocomplete source if any).

### 4.4 Left pane — Lifecycle section
`is_standard` toggle, `is_active` toggle.

### 4.5 Right pane — Dialog XML tab
CodeMirror editor with XML language mode, folding, search, parse-error markers. Line count display. See [XML Spec §2](./xml-spec.md) for the schema.

### 4.6 Right pane — Content XML tab
CodeMirror editor. ACCEPTS file uploads: `.frx`, `.xml`, `.txt` (legacy FastReport migration support). See [XML Spec §3](./xml-spec.md).

### 4.7 Right pane — Preview tab
Renders the Dialog XML as a disabled form so the author can see what the end user will see.

### 4.8 Sticky action bar
Save / Cancel / Reset / unsaved-changes indicator via `useUnsavedChanges` hook.

## 5. Dialogs
### 5.1 Browse in BU probe
Triggered from §4.2 Source binding. Lets the author pick a target BU, calls `reportTemplateService.listDbObjects(business_unit_id)`, displays available views/functions/procedures, and on select populates `source_name`.

### 5.2 Soft Delete confirm
Triggered from `ReportTemplateManagement` row action. Confirm UX. Submit: `DELETE /api-system/report-template/:id` (verify exact endpoint).

(Add 5.3 etc. if other dialogs discovered.)

## 6. Persisted UI state
Standard table format.

## 7. Screenshots
> **TODO:** Screenshots deferred to the upcoming Platform screenshots batch. See `.specs/2026-05-17-screenshots-coverage-checklist.md` for the cross-module coverage plan.

## 8. References
- SITEMAP.md, ReportTemplateManagement.tsx, ReportTemplateEdit.tsx, reportTemplateService.ts
- Cross-links: [[report-templates]] (landing), [[business-units]] (BU chip context), [Data Model](./data-model.md), [Permissions](./permissions.md), [XML Spec](./xml-spec.md).
```

- [ ] **Step 5: Run verification** (standard grep set, line count 180-280).

- [ ] **Step 6: Commit**

```bash
git add en/platform/report-templates/ui-screens.md
git commit -m "docs(platform/report-templates): expand ui-screens from stub to canonical reference

ReportTemplateManagement list with Standard/Custom + Active/Inactive
facets, 2-pane ReportTemplateEdit (left: identity + source + BU scope +
lifecycle; right: 3-tab CodeMirror — Dialog XML / Content XML / Preview),
Browse-in-BU probe dialog, sticky action bar with useUnsavedChanges,
persisted localStorage keys. Screenshots deferred."
```

---

## Task 4: Expand `xml-spec.md` (existing stub; refines template §2.5)

**Files:**
- Modify: `en/platform/report-templates/xml-spec.md`

**Sources:** `ReportTemplateEdit.tsx` (specifically the parts of the file that validate XML or render the Preview tab); any XML samples already in the repo or referenced from `../carmen-platform/`.

- [ ] **Step 1: Read the XML validators / Preview-tab code in ReportTemplateEdit.tsx**

```bash
grep -n "Dialog\|Content\|<Label\|<Date\|<Lookup\|parseError\|validateXml\|xmlMode\|CodeMirror\|fileUpload\|.frx\|.xml" ../carmen-platform/src/pages/ReportTemplateEdit.tsx | head -60
```

Read the validator function(s) and the Preview renderer to enumerate which XML elements the editor understands.

- [ ] **Step 2: Search for sample XML in the repo**

```bash
grep -rn "<Dialog\|<Content\|<Label\|<Date\|<Lookup" ../carmen-platform/ 2>&1 | grep -v "node_modules\|build" | head -20
```

If samples exist, capture a minimal but complete pair (Dialog + Content). If no samples exist, construct one from the validator code.

- [ ] **Step 3: Rewrite `en/platform/report-templates/xml-spec.md`**

Replace entire body. Keep `dateCreated` (`'2026-05-19T00:00:00.000Z'`); set `date` to `'2026-05-19T18:30:00.000Z'`.

Structure:

```markdown
# Report Template — XML Spec

> **At a Glance**
> **Two payloads:** Dialog XML (parameter form) &nbsp;·&nbsp; Content XML (report output) &nbsp;·&nbsp; **Editor:** CodeMirror (XML mode, folding, search, parse-error markers) &nbsp;·&nbsp; **Content uploads:** `.frx`, `.xml`, `.txt` (legacy FastReport migration) &nbsp;·&nbsp; **Validation:** inline parse error + line/col markers + line-count display &nbsp;·&nbsp; **Worked example:** §6 contains a minimal complete pair

## 1. Overview
2 paragraphs: the two XML payloads (`dialog`, `content`) stored as Json? columns on `tb_report_template` (see [Data Model §5](./data-model.md) §5); their distinct purposes (Dialog = filter form, Content = output rendering); the runtime contract.

## 2. Dialog XML
### 2.1 Root element and children
The Dialog XML is a `<Dialog>` (verify exact root element name from source) container with children that describe the parameter form. Each child renders one filter field.

### 2.2 Element catalogue
Enumerate every element name the SPA validator or Preview renderer recognizes. Likely candidates: `<Label>`, `<Date>`, `<Lookup>`, `<TextBox>`, `<Numeric>`, `<DateRange>`. For each: which attributes (e.g. `name`, `caption`, `default`, `required`), how the Preview tab renders it (disabled form control).

### 2.3 `<Label>` + field pairing
The landing's "Label / Date / Lookup pairing" hint: typical pattern is `<Label caption="From Date" />` followed by `<Date name="DateFrom" />` — confirm whether the pairing is positional (sibling order matters) or named (the `<Label>` references the field by `for` attribute).

### 2.4 Mapping to `source_params`
Each Dialog field whose `name` appears in `tb_report_template.source_params[].filter` is bound to a positional parameter at runtime. Cross-link to [Data Model §5.3](./data-model.md).

## 3. Content XML
### 3.1 Root element and children
The Content XML is `<Content>` (verify) — the report output layout. Likely contains paragraphs, tables, images, formula cells.

### 3.2 Element catalogue
Enumerate elements recognized by the renderer. Document expression syntax (e.g. `{{field_name}}` placeholders if any).

### 3.3 `.frx` file upload
The Content tab accepts FastReport `.frx` files. State whether the SPA performs any conversion to XML on upload, or just stores raw `.frx` content into the `content` column. (Verify in source.)

## 4. Editor surface
- CodeMirror in XML language mode.
- Folding: enabled (collapse tags).
- Search: Ctrl+F / Cmd+F.
- Parse-error markers: line/col indicator next to the tab header.
- Line count display.
- File upload (Content tab only): `.frx`, `.xml`, `.txt`.

## 5. Validation
List each error category surfaced by the validator (likely: malformed XML, unknown element, missing required attribute, mismatched closing tag). For each category, the trigger and the user-facing message.

## 6. Worked example
A minimal complete Dialog + Content pair that compiles cleanly. Include in fenced code blocks. Annotate which fields bind to which `source_params` entries.

## 7. References
- `../carmen-platform/src/pages/ReportTemplateEdit.tsx` — validator and Preview renderer
- Sibling [Data Model §5](./data-model.md) for the column types and `source_params` shape
- Sibling [UI Screens §4.5-4.7](./ui-screens.md) for the editor tabs
```

- [ ] **Step 4: Run verification**

NOTE: this page contains many XML element references in code spans (`<Dialog>`, `<Label>`, etc.). The placeholder-syntax grep WILL fire. Confirm each match is a legitimate XML reference inside backticks or a code fence, not a leftover template placeholder.

- [ ] **Step 5: Commit**

```bash
git add en/platform/report-templates/xml-spec.md
git commit -m "docs(platform/report-templates): expand xml-spec from stub to canonical reference

Dialog XML and Content XML element catalogues, Label-Date-Lookup
pairing convention, source_params binding, editor surface (CodeMirror
config, file upload, parse-error markers), validation categories,
and a worked Dialog+Content example. Refines the provisional
xml-spec.md shape from platform-sub-page-template.md §2.5."
```

---

## Task 5: Final cross-page checks + push

**Files:**
- Read-only: all four sub-pages, plus `en/platform/report-templates.md` landing.

- [ ] **Step 1: Cross-link integrity**

```bash
grep -oE '\[\[[a-z-]+\]\]|\[[^]]+\]\(\.\.?/[^)]+\)' en/platform/report-templates/*.md | sort -u
ls en/platform/users.md en/platform/clusters.md en/platform/business-units.md en/platform/profile.md en/platform/auth-roles.md en/platform/report-templates/data-model.md en/platform/report-templates/permissions.md en/platform/report-templates/ui-screens.md en/platform/report-templates/xml-spec.md
```

Every `[[slug]]` must resolve. Sibling cross-links use `./relative.md`. Cross-module links to `clusters/permissions.md` use `../clusters/permissions.md`.

- [ ] **Step 2: Landing references + stub annotations**

```bash
grep -nE '\(\./(data-model|permissions|ui-screens|xml-spec)\.md\)' en/platform/report-templates.md
grep -n "stub — in progress" en/platform/report-templates.md
```

Expected: the landing's §7 currently lists only `ui-screens.md` and `xml-spec.md`. Since we're ADDING `data-model.md` and `permissions.md`, the landing §7 needs to grow to four entries. This is the landing patch step.

- [ ] **Step 3: Full-file verification per file**

Run the standard grep set on each of the four files.

- [ ] **Step 4: Sibling-slug consistency**

```bash
grep -n '\[\[data-model\]\]\|\[\[permissions\]\]\|\[\[ui-screens\]\]\|\[\[xml-spec\]\]' en/platform/report-templates/*.md && echo "FAIL" || echo "OK"
```

- [ ] **Step 5: Visual render check URLs**

- `http://dev.blueledgers.com:3987/en/platform/report-templates/data-model`
- `http://dev.blueledgers.com:3987/en/platform/report-templates/permissions`
- `http://dev.blueledgers.com:3987/en/platform/report-templates/ui-screens`
- `http://dev.blueledgers.com:3987/en/platform/report-templates/xml-spec`

- [ ] **Step 6: Push** (only after user confirms visual check)

```bash
git push origin main
```

- [ ] **Step 7: Landing patch — required this round**

Unlike previous rounds where the landing patch was optional, THIS round REQUIRES a landing patch because we're adding two new sub-pages (`data-model.md`, `permissions.md`) that the landing's §7 doesn't currently reference.

Update `en/platform/report-templates.md` §7 to reference all four sub-pages, remove any `(stub — in progress)` annotations on the existing references, and bump `date` to a fresh timestamp.

Suggested §7 content:
```markdown
## 7. Pages in This Module

- [Data Model](./data-model.md) — `tb_report_template` entity, JSON payloads (Dialog/Content/source_params), divergences from SPA shape.
- [Permissions](./permissions.md) — three admin-tier-gated routes (same gate as clusters); access matrix across all `platform_role` values; bootstrap exception via cross-link to clusters/permissions.
- [UI Screens](./ui-screens.md) — `ReportTemplateManagement` list, 2-pane `ReportTemplateEdit` (left: identity + source + BU scope + lifecycle; right: 3-tab CodeMirror), Browse-in-BU probe.
- [XML Spec](./xml-spec.md) — Dialog and Content XML element catalogues, source_params binding, editor surface, validation categories, worked example.
```

Commit:
```bash
git add en/platform/report-templates.md
git commit -m "docs(platform/report-templates): expand landing §7 to reference all 4 sub-pages

Add Data Model and Permissions entries (the two new sub-pages
created in this round); refresh the existing UI Screens and XML
Spec descriptions to match their new content; remove stub
annotations."
```

- [ ] **Step 8: (Optional) Update template spec §2.5**

If `xml-spec.md` ended up with a meaningfully different shape from the template's provisional §2.5, update the template in a separate commit. Skip this step if the shape held.

---

## Self-Review

**1. Spec coverage:**
- Spec §3.1 (`data-model.md`) → Task 1. ✓
- Spec §3.2 (`permissions.md`) → Task 2. ✓
- Spec §3.3 (`ui-screens.md`) → Task 3. ✓
- Spec §3.4 (`xml-spec.md` refinement) → Task 4. ✓
- Spec §4 / §5 (inherited template gates and workflow) → enforced via verification + subagent pattern.
- Spec §6 deferrals → out of plan; Task 5 Step 7/8 are explicit follow-ups.

**2. Placeholder scan:** the `<…>` brackets in the "Rewrite" step structure blocks are intentional fillable sections. XML element references like `<Dialog>` and `<Label>` in xml-spec.md are NOT placeholders — they're real content. The per-task verification grep is told to expect this.

**3. Identifier consistency:** model name (`tb_report_template`), endpoint paths, component names (`ReportTemplateManagement`, `ReportTemplateEdit`), service file (`reportTemplateService.ts`) match across all five tasks and the Common Context block.
