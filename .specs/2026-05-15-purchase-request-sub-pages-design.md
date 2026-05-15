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

## 5. File List (14 new sub-page files + 1 index.md update)

```
purchase-request/
├── index.md                                       (existing — Section 7 updated)
├── 01-data-model.md                               (NEW)
├── 02-business-rules.md                           (NEW)
├── 03-user-flow.md                                (NEW, overview)
├── 03-user-flow-requestor.md                      (NEW)
├── 03-user-flow-approver.md                       (NEW)
├── 03-user-flow-purchaser.md                      (NEW)
├── 03-user-flow-procurement-manager.md            (NEW)
├── 03-user-flow-audit-config.md                   (NEW)
├── 04-test-scenarios.md                           (NEW, overview)
├── 04-test-scenarios-requestor.md                 (NEW)
├── 04-test-scenarios-approver.md                  (NEW)
├── 04-test-scenarios-purchaser.md                 (NEW)
├── 04-test-scenarios-procurement-manager.md       (NEW)
└── 04-test-scenarios-audit-config.md              (NEW)
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
- Frontend screens: `../carmen-inventory-frontend/app/` (PR routes if applicable)
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

Replace the current "No sub-pages yet." with:

```markdown
## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](./02-business-rules.md) — Validation, calculation, authorization, and posting rules.
- [03 — User Flow](./03-user-flow.md) — Document lifecycle and persona index.
  - [Requestor](./03-user-flow-requestor.md)
  - [Approver](./03-user-flow-approver.md)
  - [Purchaser](./03-user-flow-purchaser.md)
  - [Procurement Manager](./03-user-flow-procurement-manager.md)
  - [Audit / Config](./03-user-flow-audit-config.md)
- [04 — Test Scenarios](./04-test-scenarios.md) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Requestor](./04-test-scenarios-requestor.md)
  - [Approver](./04-test-scenarios-approver.md)
  - [Purchaser](./04-test-scenarios-purchaser.md)
  - [Procurement Manager](./04-test-scenarios-procurement-manager.md)
  - [Audit / Config](./04-test-scenarios-audit-config.md)
```

## 8. Out of Scope

- **Other modules** — only `purchase-request/` is implemented in this round. The 10 remaining modules with sources (and the 2 skeleton modules) are future per-module plans.
- **The 9 unread carmen/docs files** for PR (API specs, component specs, module-implementation, etc.) — not needed for developer/tester user-manual content. Can be folded in later if specific pages need them.
- **Updating `.specs/templates/`** to reflect the persona-file split — defer until this approach is validated. If validated and the team wants it as the default, a follow-up commit can regenerate templates and update the predecessor spec.
- **Fixing carmen/docs divergences** — record them in `01-data-model.md` Section 5 but do not modify carmen/docs.

## 9. Implementation Notes (for the plan)

1. **Order:** create files in numeric order (01 → 02 → 03 overview → 03 persona files → 04 overview → 04 persona files), then update index.md. Each file is its own commit so review and rollback are easy.
2. **Synthesis discipline:** every sub-page must be grounded in the listed sources. Inventing rules or scenarios not present in carmen/docs / Prisma / E2E is a quality failure.
3. **Persona consistency:** the 5 group slugs (`requestor`, `approver`, `purchaser`, `procurement-manager`, `audit-config`) are fixed. Both `03-user-flow-*` and `04-test-scenarios-*` use the same slug per persona. Frontmatter `tags` include the persona slug.
4. **Cross-link integrity:** persona files link back to their parent overview file. Test scenario persona files link to the matching user-flow persona file.
5. **Verifier:** run `.specs/verify_frontmatter.py` on every new file before commit. All 14 new files plus the updated index.md must pass.

## 10. Open Questions

None at design time.
