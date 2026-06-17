# Design: Purchase Request Sub-Pages

**Date:** 2026-05-15
**Status:** Approved (user)
**Scope:** Sub-page implementation for the `purchase-request/` module
**Predecessor:** `.specs/2026-05-15-sub-page-templates-design.md` (defined the four sub-page types and templates)

This is the **first per-module implementation** of the sub-page blueprint. It applies the four standard page types to `purchase-request/`, with one significant adaptation: **persona-axis pages are split into separate files**, one file per persona group.

---

## 1. Goal

Produce a complete set of sub-pages for the `purchase-request` module so developers and testers have:
- The data model (Prisma-derived) of purchase request entities
- The business rules that govern PR lifecycle
- The user flow per persona (separate file per persona)
- The test scenarios per persona (separate file per persona)
- An updated module landing page that lists everything

The result is the reference implementation that downstream module work (10 more modules) can pattern-match.

### 1.1 Bilingual Output (EN + TH)

Every sub-page is produced in **two languages — English (default/canonical) and Thai**.

- **Canonical:** the English file at `<name>.md` is the source of truth for content. When facts diverge between EN and TH, EN wins; TH is updated to match.
- **TH variant:** sits alongside the EN file at `<name>.th.md` (suffix convention). Same frontmatter shape with title and description translated, same section structure, same numbering — only prose is translated.
- **Out of scope:** retrofitting existing content (the 12 module `index.md` files and `costing/calculation-methods.md`) to bilingual. A separate effort handles those if needed.

## 2. Persona Adaptation

The general template spec (Section 3 of `.specs/2026-05-15-sub-page-templates-design.md`) defines `03-user-flow.md` and `04-test-scenarios.md` as single files with persona-axis Section 3. **For this module, those single files are decomposed into separate files per persona, plus an overview file.**

This is a **structural deviation from the template spec** justified by:
- 5 persona groups produce a large single file (~200 lines each)
- Wiki.js readers typically come in looking for their own role, not all personas
- Separate files mean smaller, more focused pages — better for the developer/tester audience

If this pattern works well for PR, downstream module specs will adopt the same split, and the template spec will be amended accordingly. If it proves cumbersome, future modules can revert to single-file persona-axis Section 3.

## 3. Persona Groups (5 groups)

Collapsed from the 8 personas listed in `purchase-request/index.md` Section 4:

| Group slug | Source personas in index.md | Scope in this module |
|------------|-----------------------------|----------------------|
| `requestor` | Requestor | Creates PR, selects type, adds lines, attaches docs, submits, responds to send-back |
| `approver` | Department Head, Budget Controller, Finance Officer/Manager | Multi-stage approval chain; approve / reject / send-back / split-reject |
| `purchaser` | Procurement Officer / Purchaser | Receives approved PRs, validates vendor and pricing, converts to PO |
| `procurement-manager` | Procurement Manager | Oversight, high-value approval, vendor ranking, Allocate Vendor rule tuning |
| `audit-config` | Auditor + System Administrator | Read-only audit trail (Auditor); workflow / threshold / delegation configuration (Sysadmin) |

The combined `audit-config` group reflects two different read/configure surfaces of the same module — both peripheral to the transactional flow, both useful to document together.

## 4. Sources

### 4.1 Primary (source of truth)

- Prisma tenant schema: `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
  - Relevant models: `tb_purchase_request_header`, `tb_purchase_request_detail`, `tb_purchase_request_workflow`, `tb_purchase_request_template_detail`
  - Relevant enums: `enum_purchase_request_doc_status`, value `purchase_request` of `enum_purchase_order_type`
  - Relations: `tb_tax_profile`, `tb_product`, `tb_vendor`, `tb_purchase_order_detail`, `tb_purchase_order_detail_tb_purchase_request_detail`

### 4.2 Secondary (carmen/docs cross-check)

Selected from the 18 files in `../carmen/docs/purchase-request-management/`:

| Sub-page | carmen/docs files to read |
|----------|---------------------------|
| `01-data-model.md` | `data-models.md` |
| `02-business-rules.md` | `purchase-request-ba.md`, `PR-Technical-Specification.md`, `PR-Module-Structure.md` |
| `03-user-flow.md` (and persona variants) | `PR-User-Experience.md`, `PR-Overview.md`, `purchase-request-module-prd.md` |
| `04-test-scenarios.md` (and persona variants) | `testing.md`, `troubleshooting.md` |

The remaining 9 carmen/docs files (API specs, component specs, module-implementation, README, consolidation reports, template-ba) are out of scope for this round.

## 5. File List (28 new sub-page files + 1 index.md update)

14 page concepts × 2 languages = 28 files. EN file is canonical; TH file is the same content translated.

```
purchase-request/
├── index.md                                          (existing — Section 7 updated)
├── 01-data-model.md                                  (NEW, EN)
├── 01-data-model.th.md                               (NEW, TH)
├── 02-business-rules.md                              (NEW, EN)
├── 02-business-rules.th.md                           (NEW, TH)
├── 03-user-flow.md                                   (NEW, EN, overview)
├── 03-user-flow.th.md                                (NEW, TH, overview)
├── 03-user-flow-requestor.md                         (NEW, EN)
├── 03-user-flow-requestor.th.md                      (NEW, TH)
├── 03-user-flow-approver.md                          (NEW, EN)
├── 03-user-flow-approver.th.md                       (NEW, TH)
├── 03-user-flow-purchaser.md                         (NEW, EN)
├── 03-user-flow-purchaser.th.md                      (NEW, TH)
├── 03-user-flow-procurement-manager.md               (NEW, EN)
├── 03-user-flow-procurement-manager.th.md            (NEW, TH)
├── 03-user-flow-audit-config.md                      (NEW, EN)
├── 03-user-flow-audit-config.th.md                   (NEW, TH)
├── 04-test-scenarios.md                              (NEW, EN, overview)
├── 04-test-scenarios.th.md                           (NEW, TH, overview)
├── 04-test-scenarios-requestor.md                    (NEW, EN)
├── 04-test-scenarios-requestor.th.md                 (NEW, TH)
├── 04-test-scenarios-approver.md                     (NEW, EN)
├── 04-test-scenarios-approver.th.md                  (NEW, TH)
├── 04-test-scenarios-purchaser.md                    (NEW, EN)
├── 04-test-scenarios-purchaser.th.md                 (NEW, TH)
├── 04-test-scenarios-procurement-manager.md          (NEW, EN)
├── 04-test-scenarios-procurement-manager.th.md       (NEW, TH)
├── 04-test-scenarios-audit-config.md                 (NEW, EN)
└── 04-test-scenarios-audit-config.th.md              (NEW, TH)
```

## 6. Templates

`01-data-model.md` and `02-business-rules.md` use the templates from `.specs/templates/` verbatim (with `<Module>` = `Purchase Request`, `<module-slug>` = `purchase-request`).

The persona-axis templates below are the new addition.

### 6.1 `03-user-flow.md` (overview)

```markdown
---
title: Purchase Request — User Flow
description: Document lifecycle and persona-specific flow files for purchase-request.
published: true
date: <ISO 8601 timestamp>
tags: purchase-request, user-flow, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# Purchase Request — User Flow

## 1. Overview
<Scope: which document type(s), which personas, where to drill down for each>

## 2. Document Lifecycle
<Global state machine — table form:>

| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |

## 3. Persona Index
- [Requestor](./03-user-flow-requestor.md) — Creates and submits PRs, responds to send-backs.
- [Approver](./03-user-flow-approver.md) — Multi-stage approval chain (Dept Head, Budget Controller, Finance).
- [Purchaser](./03-user-flow-purchaser.md) — Validates and converts approved PRs to POs.
- [Procurement Manager](./03-user-flow-procurement-manager.md) — Oversight, high-value approval, vendor ranking.
- [Audit / Config](./03-user-flow-audit-config.md) — Read-only audit (Auditor) + workflow configuration (Sysadmin).

## 4. Cross-Persona Handoffs
<Key handoff moments: Requestor → Approver → Purchaser → PO module. One row per handoff with from/to/trigger/state.>

## 5. References
- `../carmen/docs/purchase-request-management/PR-User-Experience.md`
- `../carmen/docs/purchase-request-management/PR-Overview.md`
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md`
- Frontend screens: `../carmen-inventory-frontend-react/routes/` (PR routes if applicable)
```

### 6.2 `03-user-flow-<persona>.md`

```markdown
---
title: Purchase Request — User Flow — <Persona>
description: <Persona>'s flow within the purchase-request module.
published: true
date: <ISO 8601 timestamp>
tags: purchase-request, user-flow, <persona-slug>, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# Purchase Request — User Flow — <Persona>

## 1. Role in This Module
<One paragraph: what this persona does in PR, where they sit in the chain, which document states they own.>

## 2. Entry Point and Primary Flow
**Entry point:** <where this persona starts — screen / trigger / notification>

**Primary flow (happy path):**
1. <step>
2. <step>

## 3. Decision Branches
- If <condition> → <alternate path or hand-off to another persona>
- If <condition> → <alternate path>

## 4. Exit Point / Handoffs
<Where this persona's involvement ends: which state the document is in, who picks it up next>

## 5. References
- Parent overview: [03-user-flow.md](./03-user-flow.md)
- Document lifecycle: see Section 2 of the parent overview
- carmen/docs source files (specific paths used for synthesis)
```

### 6.3 `04-test-scenarios.md` (overview)

```markdown
---
title: Purchase Request — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for purchase-request.
published: true
date: <ISO 8601 timestamp>
tags: purchase-request, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# Purchase Request — Test Scenarios

## 1. Overview
<Personas covered + scope of testing.>

## 2. Personas in Scope
- **Requestor**: <one-line scope>
- **Approver**: <one-line scope>
- **Purchaser**: <one-line scope>
- **Procurement Manager**: <one-line scope>
- **Audit / Config**: <one-line scope>

## 3. Persona Test Files
- [Requestor scenarios](./04-test-scenarios-requestor.md)
- [Approver scenarios](./04-test-scenarios-approver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Procurement Manager scenarios](./04-test-scenarios-procurement-manager.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios
<Scenarios that span multiple personas — full happy-path end-to-end, send-back loop, etc.>

## 5. E2E Test Mapping
<Links to Playwright specs in `../carmen-inventory-frontend-e2e/tests/`, grouped by persona.>

## 6. References
- `../carmen-inventory-frontend-e2e/`
- `../carmen/docs/purchase-request-management/testing.md`
- `../carmen/docs/purchase-request-management/troubleshooting.md`
```

### 6.4 `04-test-scenarios-<persona>.md`

```markdown
---
title: Purchase Request — Test Scenarios — <Persona>
description: <Persona>'s test cases (happy path, permission, validation, edge cases) for purchase-request.
published: true
date: <ISO 8601 timestamp>
tags: purchase-request, test-scenarios, <persona-slug>, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# Purchase Request — Test Scenarios — <Persona>

## 1. Happy Path
| # | Scenario | Pre-condition | Steps | Expected |

## 2. Permission / Authorization
| # | Scenario | Expected behaviour (allow/deny + reason) |

## 3. Validation / Error
| # | Scenario | Trigger | Expected error |

## 4. Edge Cases
| # | Scenario | Condition | Expected |

## 5. References
- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md)
- Related: [User flow for this persona](./03-user-flow-<persona-slug>.md)
- E2E tests in `../carmen-inventory-frontend-e2e/tests/` that cover this persona
```

## 7. `purchase-request/index.md` Section 7 Update

Replace the current "No sub-pages yet." with this ToC. Each entry shows the EN link first (default), then a `[TH]` link to the Thai variant in parentheses.

```markdown
## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) ([TH](./01-data-model.th.md)) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](./02-business-rules.md) ([TH](./02-business-rules.th.md)) — Validation, calculation, authorization, and posting rules.
- [03 — User Flow](./03-user-flow.md) ([TH](./03-user-flow.th.md)) — Document lifecycle and persona index.
  - [Requestor](./03-user-flow-requestor.md) ([TH](./03-user-flow-requestor.th.md))
  - [Approver](./03-user-flow-approver.md) ([TH](./03-user-flow-approver.th.md))
  - [Purchaser](./03-user-flow-purchaser.md) ([TH](./03-user-flow-purchaser.th.md))
  - [Procurement Manager](./03-user-flow-procurement-manager.md) ([TH](./03-user-flow-procurement-manager.th.md))
  - [Audit / Config](./03-user-flow-audit-config.md) ([TH](./03-user-flow-audit-config.th.md))
- [04 — Test Scenarios](./04-test-scenarios.md) ([TH](./04-test-scenarios.th.md)) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Requestor](./04-test-scenarios-requestor.md) ([TH](./04-test-scenarios-requestor.th.md))
  - [Approver](./04-test-scenarios-approver.md) ([TH](./04-test-scenarios-approver.th.md))
  - [Purchaser](./04-test-scenarios-purchaser.md) ([TH](./04-test-scenarios-purchaser.th.md))
  - [Procurement Manager](./04-test-scenarios-procurement-manager.md) ([TH](./04-test-scenarios-procurement-manager.th.md))
  - [Audit / Config](./04-test-scenarios-audit-config.md) ([TH](./04-test-scenarios-audit-config.th.md))
```

## 8. Out of Scope

- **Other modules** — only `purchase-request/` is implemented in this round. The 10 remaining modules with sources (and the 2 skeleton modules) are future per-module plans.
- **Retrofitting existing content to bilingual** — the 12 module `index.md` files and `costing/calculation-methods.md` stay EN-only in this round. Bilingual retrofit is a separate effort if needed.
- **The 9 unread carmen/docs files** for PR (API specs, component specs, module-implementation, etc.) — not needed for developer/tester user-manual content. Can be folded in later if specific pages need them.
- **Updating `.specs/templates/`** to reflect the persona-file split and bilingual variants — defer until this approach is validated. If validated and the team wants it as the default, a follow-up commit can regenerate templates and update the predecessor spec.
- **Fixing carmen/docs divergences** — record them in `01-data-model.md` Section 5 but do not modify carmen/docs.

## 9. Implementation Notes (for the plan)

1. **Order:** for each numbered concept (01, 02, 03 overview, 03-requestor, ...), produce the EN file first, then translate to the TH file. One commit per concept pair (EN + TH together) — see note 7 below. Update `index.md` Section 7 last as a final commit.
2. **Synthesis discipline:** every sub-page must be grounded in the listed sources. Inventing rules or scenarios not present in carmen/docs / Prisma / E2E is a quality failure.
3. **Persona consistency:** the 5 group slugs (`requestor`, `approver`, `purchaser`, `procurement-manager`, `audit-config`) are fixed. Both `03-user-flow-*` and `04-test-scenarios-*` use the same slug per persona. Frontmatter `tags` include the persona slug.
4. **Cross-link integrity:** persona files link back to their parent overview file. Test scenario persona files link to the matching user-flow persona file. Within a language, links stay within that language (EN file links to EN siblings; TH file links to TH siblings).
5. **Translation discipline:**
   - The EN file is the source of truth. Write it first, get it right, then translate.
   - The TH file mirrors the EN file section-for-section, table-for-table, with the same numbering. No omissions, no additions specific to one language.
   - Frontmatter `title` and `description` are translated to Thai. `tags`, `published`, `date`, `dateCreated`, `editor` stay as in EN.
   - Code-like content (Prisma model names, enum values, rule IDs, field names) stays in English — these are identifiers, not prose.
   - Cross-links in TH files point to other TH files (e.g. `03-user-flow.th.md` links to `03-user-flow-requestor.th.md`, not `.md`).
6. **Verifier:** run `.specs/verify_frontmatter.py` on every new file before commit. All 28 new files plus the updated `index.md` must pass.
7. **Each commit covers both EN and TH for the same concept** to keep them paired in history (e.g. one commit adds `01-data-model.md` + `01-data-model.th.md` together).

## 10. Open Questions

None at design time.
