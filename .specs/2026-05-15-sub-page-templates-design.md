# Design: Sub-Page Templates for Module Folders

**Date:** 2026-05-15
**Status:** Approved (user)
**Scope:** carmen-wiki sub-page structure and templates
**Predecessor:** `.specs/2026-05-15-module-folder-structure-design.md` (established the 12 module folders with `index.md`)

This spec defines the standard sub-page layout that goes inside each module folder, the template for each sub-page type, and how each module's `index.md` Section 7 references them. **It does NOT cover the per-module content implementation** — that is a separate effort, one module at a time, handed off to future plans.

---

## 1. Goal

Provide a uniform blueprint for module sub-pages so every module (12 folders today) carries the same four reference pages, structured the same way, in the same order. This gives developers and testers a predictable reading path:

1. **What** the module manages → `01-data-model.md`
2. **Rules** that govern it → `02-business-rules.md`
3. **How** users move through it → `03-user-flow.md`
4. **How** to verify it → `04-test-scenarios.md`

`01` and `02` are content-axis (entities/rules); `03` and `04` are persona-axis (who does what / who tests what) — reflecting the actual reading path a developer or QA engineer takes.

## 2. Sub-Page Types

Four standard sub-pages per module, with numbered prefix for Wiki.js alphabetical sort:

| # | File | Audience | Primary axis |
|---|------|----------|--------------|
| 1 | `01-data-model.md` | Dev + Tester | Entities |
| 2 | `02-business-rules.md` | Tester (primary), Dev | Rule categories |
| 3 | `03-user-flow.md` | Tester, PM | Persona |
| 4 | `04-test-scenarios.md` | Tester | Persona |

### 2.1 Naming convention

- Two-digit numeric prefix (`01-` ... `04-`) for stable ordering.
- kebab-case, lowercase, ASCII.
- File extension `.md`.
- Plural forms: `business-rules`, `test-scenarios` (matches established conventions).

### 2.2 Topical sub-pages

Modules may also have non-template topical pages (e.g. `costing/calculation-methods.md`). These do NOT take numbered prefixes — they sort after the four standard pages and are listed at the end of the index.md Section 7. Topical pages are out of scope for this spec.

## 3. Templates

The four templates below are the canonical content. Substitute `<Module>`, `<module-slug>`, ISO timestamps, and the persona/entity placeholders during implementation. Frontmatter `date` and `dateCreated` are set to the creation time at implementation; `dateCreated` is fixed thereafter.

### 3.1 `01-data-model.md`

```markdown
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
```

### 3.2 `02-business-rules.md`

```markdown
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
```

### 3.3 `03-user-flow.md`

```markdown
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
```

### 3.4 `04-test-scenarios.md`

```markdown
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
```

## 4. index.md Section 7 Update

Every module's `index.md` Section 7 is replaced from `No sub-pages yet.` to a ToC listing the four standard pages in order:

```markdown
## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](./02-business-rules.md) — Validation, calculation, authorization, and posting rules.
- [03 — User Flow](./03-user-flow.md) — Document lifecycle and persona-specific paths.
- [04 — Test Scenarios](./04-test-scenarios.md) — Test cases grouped by persona, plus E2E mapping.
```

For `costing/` (which already has the topical `calculation-methods.md`), the topical entry sorts last:

```markdown
## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](./02-business-rules.md) — Validation, calculation, authorization, and posting rules.
- [03 — User Flow](./03-user-flow.md) — Document lifecycle and persona-specific paths.
- [04 — Test Scenarios](./04-test-scenarios.md) — Test cases grouped by persona, plus E2E mapping.
- [Inventory Costing Methods: FIFO vs. Weighted Average](./calculation-methods.md) — Method comparison and algorithms.
```

For skeleton modules (`physical-count/`, `spot-check/`) — no carmen/docs source exists. The four sub-pages will still be created during implementation but each will carry a `> **TODO:**` callout in Section 1 pointing at frontend + E2E for source content. The Section 7 ToC entries do not change shape.

## 5. Out of Scope

- **Content implementation** for any of the 48 sub-pages (12 modules × 4 page types). Each module's implementation is its own future plan.
- **Additional page types** (API Reference, Troubleshooting, Component Specifications, etc.) — these can be added as topical pages later or as new standard types if the team needs them.
- **Wiki.js sidebar / navigation configuration** — handled in Wiki.js admin, not in this repo.
- **Backfilling carmen/docs to match Prisma divergences** — divergences are noted in the data-model page but not fixed in this work. A separate follow-up effort can address them.

## 6. Implementation Notes (for downstream plans)

When a module's sub-pages are implemented:

1. Implementation is **one module at a time**. Each module's sub-page generation is a separate plan.
2. **Reading order for synthesis** (data-model page especially):
   1. Read both Prisma schemas (tenant + platform) and locate models relevant to the module.
   2. Read `../carmen/docs/<source-folder>/` files.
   3. Where they conflict, Prisma wins for the page content; carmen/docs discrepancy goes in Section 5.
3. For `03-user-flow.md` and `04-test-scenarios.md`, the persona list must match the `## 4. Roles and Personas` section of the module's `index.md`. Adding a persona to a sub-page that isn't in the index implies the index needs an update too.
4. The `index.md` Section 7 update happens in the same commit as the first sub-page added for that module, OR as a final cleanup commit at the end. Either is fine.
5. Frontmatter verifier (`.specs/verify_frontmatter.py`) applies to sub-pages too — run it before commit.
6. Cross-link integrity check: any new `[[slug]]` references must resolve to one of the 12 valid module slugs.

## 7. Open Questions

None at design time.
