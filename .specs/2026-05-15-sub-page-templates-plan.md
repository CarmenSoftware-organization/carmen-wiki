# Sub-Page Templates Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Materialize the four sub-page templates from the design spec into reusable standalone files under `.specs/templates/`, plus a README that explains how downstream per-module plans should use them.

**Architecture:** Each template is a self-contained `.md` file containing the canonical content from the spec's Section 3, with placeholder fields (`<Module>`, `<EntityName>`, `<ISO 8601 timestamp>`, etc.) preserved so implementers can copy and substitute. `.specs/templates/` is non-wiki content (under the hidden `.specs/` directory) so Wiki.js won't surface the templates as pages and the frontmatter verifier won't auto-scan them.

**Tech Stack:** Markdown only. No build tooling. Working directory: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`. Branch: `main` (user-approved direct commits).

**Reference spec:** `.specs/2026-05-15-sub-page-templates-design.md` (canonical source of the templates — these extracted files are a convenience copy).

---

## File Structure

**Created files:**
- `.specs/templates/01-data-model.md` — Data model template
- `.specs/templates/02-business-rules.md` — Business rules template
- `.specs/templates/03-user-flow.md` — User flow template (persona-axis primary flow)
- `.specs/templates/04-test-scenarios.md` — Test scenarios template (persona-axis)
- `.specs/templates/README.md` — How to use these templates

No other files are touched.

---

## Task 1: Create `.specs/templates/01-data-model.md`

**Files:**
- Create: `.specs/templates/01-data-model.md`

- [ ] **Step 1: Create the templates directory**

```bash
mkdir -p .specs/templates
```

- [ ] **Step 2: Write `.specs/templates/01-data-model.md`** with this exact content:

````markdown
---
title: <Module> — Data Model
description: Entities, fields, relationships, and enums for the <module> module.
published: true
date: <ISO 8601 timestamp>
tags: <module-slug>, data-model, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# <Module> — Data Model

> **Source of truth:** Backend Prisma schema. Always read these first when writing or updating this page:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> The `generated/client/schema.prisma` files under each package are auto-generated copies and not authoritative.

## 1. Overview
<Entities owned by this module + brief positioning relative to neighbouring modules.>

## 2. Entities

### 2.1 <EntityName>
| Field | Prisma Type | Nullable | Description |
| ----- | ----------- | -------- | ----------- |

**Constraints:** <PK, FK, unique, indexes — verbatim from Prisma.>
**Indexes:** <`@@index` and `@@unique` declarations from Prisma.>

### 2.2 <EntityName>
<Repeat per entity owned by this module.>

## 3. Relationships
<Text diagram or bullet list of FK relationships derived from Prisma `@relation` directives. Indicate 1-to-1, 1-to-many, many-to-many cardinality.>

## 4. Enums
- **<EnumName>**: `VALUE1` / `VALUE2` / ... — meaning of each value (one bullet per enum, sourced from Prisma `enum` blocks).

## 5. Divergences from carmen/docs

When writing this page, cross-check entities, fields, and enums against the corresponding `../carmen/docs/<source>/` files. Any discrepancy goes here:

| # | Item | carmen/docs says | Prisma has | Action |
|---|------|------------------|------------|--------|

If no divergences are found, replace the table with: "No divergences detected against carmen/docs as of <YYYY-MM-DD>."

## 6. References
- **Primary (source of truth):** Prisma schemas listed in the header callout.
- **Secondary (concept cross-check):** `../carmen/docs/<source-folder>/` — specific file paths.
````

- [ ] **Step 3: Verify the file exists and has expected line count (~50-60 lines)**

```bash
wc -l .specs/templates/01-data-model.md
```
Expected: roughly 50-60 lines (frontmatter + 6 sections + headings).

- [ ] **Step 4: Verify placeholders are intact (they should be — these are template placeholders, not bugs)**

```bash
grep -c '<Module\|<Entity\|<ISO\|<module-slug\|<EnumName\|<YYYY' .specs/templates/01-data-model.md
```
Expected: a positive integer (placeholders preserved on purpose). No commit yet — wait for Task 5.

---

## Task 2: Create `.specs/templates/02-business-rules.md`

**Files:**
- Create: `.specs/templates/02-business-rules.md`

- [ ] **Step 1: Write `.specs/templates/02-business-rules.md`** with this exact content:

````markdown
---
title: <Module> — Business Rules
description: Validation, calculation, authorization, and posting rules for <module>.
published: true
date: <ISO 8601 timestamp>
tags: <module-slug>, business-rules, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# <Module> — Business Rules

## 1. Overview
<Scope: which rule categories apply, which documents/entities they govern.>

## 2. Validation Rules
| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |

<Rules enforced at create/edit/submit. Rule IDs follow `<MODULE-PREFIX>_VAL_NNN` where the prefix matches the module (e.g. PR_VAL_001 for purchase-request).>

## 3. Calculation Rules
<Formulas for totals, taxes, conversions, rounding. Show the formula plus a small worked example. Reference any constants or system parameters.>

## 4. Authorization Rules
<Who can do what — by role, by document status, by amount threshold. Use a matrix or per-role bullet list.>

## 5. Posting Rules
<What happens at posting: stock movements (which inventory entity is touched, in what direction), GL journal entries (debits/credits), inter-module side effects (e.g. closes the related PO line, triggers AP commitment).>

## 6. Cross-Module Rules
<Rules involving other modules — e.g. GRN must reference an open PO line, store-requisition can only issue if source location has sufficient stock and source location is INVENTORY type.>

## 7. References
- `../carmen/docs/<source-folder>/` — specific files describing business rules.
- Backend rule implementation (if relevant): `../carmen-turborepo-backend-v2/apps/<app>/src/<module>/` (point at the file/class).
````

- [ ] **Step 2: Verify line count and placeholders**

```bash
wc -l .specs/templates/02-business-rules.md
grep -c '<Module\|<source\|<MODULE-PREFIX\|<ISO\|<module-slug' .specs/templates/02-business-rules.md
```
Expected: ~30-40 lines; positive grep count.

---

## Task 3: Create `.specs/templates/03-user-flow.md`

**Files:**
- Create: `.specs/templates/03-user-flow.md`

- [ ] **Step 1: Write `.specs/templates/03-user-flow.md`** with this exact content:

````markdown
---
title: <Module> — User Flow
description: Document lifecycle, state transitions, and persona-specific paths for <module>.
published: true
date: <ISO 8601 timestamp>
tags: <module-slug>, user-flow, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# <Module> — User Flow

## 1. Overview
<Scope: which personas covered, which document type(s).>

## 2. Document Lifecycle
<State machine — global view, not split by persona. Table form:>

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |

## 3. Flows by Persona

### 3.1 <Persona A>
**Role in this module:** <one-line summary of their job here>
**Entry point:** <where they start — which screen, which trigger>
**Primary flow (happy path):**
1. <step>
2. <step>

**Decision branches:**
- If <condition> → <alternate path or hand-off>

**Exit point:** <end state, hand-off to which other persona, or terminal>

### 3.2 <Persona B>
<Same structure.>

<Repeat per persona relevant to this module. Personas should match the roles listed in the module's index.md Section 4.>

## 4. Cross-Persona Handoffs
<Key handoff moments — e.g. Requester → Approver → Purchaser → Receiver. Show each handoff as a row with: from persona, trigger, to persona, what state the document is in at handoff.>

## 5. References
- `../carmen/docs/<source-folder>/` — specific files describing flow/UX.
- Frontend screens: `../carmen-inventory-frontend-react/routes/<route>/` (if relevant).
````

- [ ] **Step 2: Verify**

```bash
wc -l .specs/templates/03-user-flow.md
grep -c '<Module\|<Persona\|<ISO\|<module-slug' .specs/templates/03-user-flow.md
```
Expected: ~35-45 lines; positive grep count.

---

## Task 4: Create `.specs/templates/04-test-scenarios.md`

**Files:**
- Create: `.specs/templates/04-test-scenarios.md`

- [ ] **Step 1: Write `.specs/templates/04-test-scenarios.md`** with this exact content:

````markdown
---
title: <Module> — Test Scenarios
description: Test cases, edge cases, and Playwright mapping for <module>, organized by persona.
published: true
date: <ISO 8601 timestamp>
tags: <module-slug>, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# <Module> — Test Scenarios

## 1. Overview
<Personas covered + scope of testing.>

## 2. Personas in Scope
- **<Persona>**: <one-line scope of what they do in this module — match index.md Section 4>

## 3. Scenarios by Persona

### 3.1 <Persona A>

#### Happy Path
| # | Scenario | Pre-condition | Steps | Expected |

#### Permission / Authorization
| # | Scenario | Expected behaviour (allow/deny + reason) |

#### Validation / Error
| # | Scenario | Trigger | Expected error |

#### Edge Cases
| # | Scenario | Condition | Expected |

### 3.2 <Persona B>
<Same four sub-sections.>

<Each persona gets the same four sub-sections. Each Section 2/3/4 Business Rule should have at least one corresponding negative test under "Validation / Error" for the persona who would trigger it.>

## 4. Cross-Persona / Handoff Scenarios
<Flows that span multiple personas — Requester submits, Approver reviews, Purchaser converts to PO, etc. One row per handoff scenario.>

## 5. E2E Test Mapping
<Links to specific Playwright specs in `../carmen-inventory-frontend-e2e/tests/`, grouped by persona. Each link includes the test file path + test name + which scenarios from Section 3 it covers.>

## 6. References
- `../carmen-inventory-frontend-e2e/` — Playwright test suite (executable spec).
- `../carmen/docs/<source-folder>/testing.md` if it exists.
````

- [ ] **Step 2: Verify**

```bash
wc -l .specs/templates/04-test-scenarios.md
grep -c '<Module\|<Persona\|<ISO\|<module-slug' .specs/templates/04-test-scenarios.md
```
Expected: ~40-50 lines; positive grep count.

---

## Task 5: Create `.specs/templates/README.md`

**Files:**
- Create: `.specs/templates/README.md`

- [ ] **Step 1: Write `.specs/templates/README.md`** with this exact content:

````markdown
# Sub-Page Templates

Standalone copies of the four canonical sub-page templates defined in `.specs/2026-05-15-sub-page-templates-design.md` Section 3. These files exist for convenience — they are copy-sources for per-module sub-page implementation.

The spec is canonical. If the spec changes, these files must be regenerated.

## Templates

| File | Purpose |
| ---- | ------- |
| `01-data-model.md` | Entities, fields, relationships, enums. Sourced from Prisma schema. |
| `02-business-rules.md` | Validation, calculation, authorization, posting, cross-module rules. |
| `03-user-flow.md` | Document lifecycle + flows organized by persona. |
| `04-test-scenarios.md` | Test cases organized by persona + E2E test mapping. |

## Usage

When implementing sub-pages for a module `<m>`:

1. Copy each template into the module folder:
   ```bash
   cp .specs/templates/01-data-model.md <m>/01-data-model.md
   cp .specs/templates/02-business-rules.md <m>/02-business-rules.md
   cp .specs/templates/03-user-flow.md <m>/03-user-flow.md
   cp .specs/templates/04-test-scenarios.md <m>/04-test-scenarios.md
   ```

2. Substitute placeholders in each copied file:
   - `<Module>` → human-readable module name (matches `index.md` `title:`)
   - `<module-slug>` → folder name (e.g. `inventory`, `good-receive-note`)
   - `<ISO 8601 timestamp>` (both `date` and `dateCreated`) → current ISO timestamp
   - Page-type-specific placeholders: `<EntityName>`, `<Persona>`, `<Rule ID>`, etc.

3. Read the relevant source for the page type:
   - **Data Model:** Read both Prisma schemas first, then cross-check `../carmen/docs/<source>/`.
   - **Business Rules:** Read `../carmen/docs/<source>/` PRD and business-requirements files.
   - **User Flow:** Read `../carmen/docs/<source>/` flow/UX docs, supplement with `../carmen-inventory-frontend-react/routes/`.
   - **Test Scenarios:** Read `../carmen-inventory-frontend-e2e/tests/` for executable spec, supplement with `../carmen/docs/<source>/testing.md`.

4. Fill in the content section by section. Keep the section numbering exactly as the template.

5. Run the frontmatter verifier:
   ```bash
   python3 .specs/verify_frontmatter.py <m>/01-data-model.md
   ```
   Each filled-in sub-page should print `OK: ... — title='<Module> — ...'`.

6. Update the module's `index.md` Section 7 to list the new sub-pages. Either bundle this with the first sub-page commit or do it as a final cleanup commit for the module.

## Persona discipline

`03-user-flow.md` and `04-test-scenarios.md` use persona as their primary organizing axis. The personas in these pages MUST match the roles listed in the module's `index.md` Section 4. If you add a persona that isn't in the index, update the index in the same commit.

## Cross-link integrity

Any `[[slug]]` reference must resolve to one of the 12 valid module slugs: `inventory`, `costing`, `inventory-adjustment`, `good-receive-note`, `store-requisition`, `physical-count`, `spot-check`, `purchase-request`, `purchase-order`, `vendor-pricelist`, `product`, `recipe`. (Note: `stock-take` was renamed to `physical-count` — do not use the old slug.)

## Why templates live in `.specs/`

The `.specs/` directory is hidden from Wiki.js — pages inside are not served as wiki content. Putting templates here means the placeholder-laden template files won't appear as broken pages on the live site. Per-module copies (without `.specs/` prefix) are real wiki pages.
````

- [ ] **Step 2: Verify**

```bash
wc -l .specs/templates/README.md
```
Expected: ~50-70 lines.

---

## Task 6: Commit and push

**Files:** none new — only staging the work from Tasks 1-5.

- [ ] **Step 1: Inspect what will be committed**

```bash
git status
git diff --stat
```
Expected: 5 new files under `.specs/templates/`: `01-data-model.md`, `02-business-rules.md`, `03-user-flow.md`, `04-test-scenarios.md`, `README.md`. Nothing else modified.

- [ ] **Step 2: Confirm no other files leaked into the change**

```bash
git status --porcelain | grep -v '^?? \.specs/templates/' | grep -v '^A  \.specs/templates/'
```
Expected: empty output (every change is inside `.specs/templates/`).

- [ ] **Step 3: Stage and commit**

```bash
git add .specs/templates/
git commit -m "docs: add reusable sub-page templates under .specs/templates/

Extracts the four sub-page templates (01-data-model,
02-business-rules, 03-user-flow, 04-test-scenarios)
from .specs/2026-05-15-sub-page-templates-design.md
Section 3 into standalone files, plus a README explaining
how downstream per-module implementation should consume
them.

The spec remains canonical; these are convenience copies."
```

- [ ] **Step 4: Verify commit**

```bash
git log -1 --stat
```
Expected: 5 files changed, all under `.specs/templates/`, hundreds of insertions, no deletions.

- [ ] **Step 5: Push to origin**

```bash
git push origin main
```
Expected: push succeeds, branch advances by one commit.
