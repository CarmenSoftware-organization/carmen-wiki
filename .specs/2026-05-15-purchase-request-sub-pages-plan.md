# Purchase Request Sub-Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the four sub-page types for the `purchase-request/` module in both English (canonical) and Thai, with persona-axis pages decomposed into separate files per persona group — 14 concepts × 2 languages = 28 files + an updated `index.md` Section 7.

**Architecture:** Each concept produces an EN file (`.md`) and a TH file (`.th.md`) in `purchase-request/`. EN is canonical; TH is a section-for-section translation of the same EN content. Code-like identifiers (Prisma model names, enum values, rule IDs, field names) stay English in both. Persona-axis pages (03-user-flow and 04-test-scenarios) split into an overview file + 5 persona files. Each commit covers the EN + TH pair for a single concept.

**Tech Stack:** Markdown only. No build pipeline. Frontmatter verifier at `.specs/verify_frontmatter.py` validates Wiki.js frontmatter. Working directory: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`. Branch: `main` (user-approved direct commits).

**Reference spec:** `.specs/2026-05-15-purchase-request-sub-pages-design.md`

---

## Common Context

### Sources of truth

**Prisma (primary for 01-data-model):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — search for `tb_purchase_request_header`, `tb_purchase_request_detail`, `tb_purchase_request_workflow`, `tb_purchase_request_template_detail`, `enum_purchase_request_doc_status`

**carmen/docs (secondary, by sub-page):**
- `../carmen/docs/purchase-request-management/data-models.md` — for 01-data-model cross-check
- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — for 02-business-rules
- `../carmen/docs/purchase-request-management/PR-Technical-Specification.md` — for 02-business-rules
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — for 02-business-rules (cross-module)
- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — for 03-user-flow
- `../carmen/docs/purchase-request-management/PR-Overview.md` — for 03-user-flow
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md` — for 03-user-flow
- `../carmen/docs/purchase-request-management/testing.md` — for 04-test-scenarios
- `../carmen/docs/purchase-request-management/troubleshooting.md` — for 04-test-scenarios

**E2E (for 04-test-scenarios E2E mapping):**
- `../carmen-inventory-frontend-e2e/tests/` — Playwright specs

### Persona slugs (fixed)

| Slug | Source personas in index.md Section 4 | EN display | TH display |
|------|--------------------------------------|-----------|-----------|
| `requestor` | Requestor | Requestor | ผู้ร้องขอ (Requestor) |
| `approver` | Department Head, Budget Controller, Finance Officer/Manager | Approver | ผู้อนุมัติ (Approver) |
| `purchaser` | Procurement Officer / Purchaser | Purchaser | เจ้าหน้าที่จัดซื้อ (Purchaser) |
| `procurement-manager` | Procurement Manager | Procurement Manager | ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager) |
| `audit-config` | Auditor + System Administrator | Audit / Config | ผู้ตรวจสอบและผู้ดูแลระบบ (Audit / Config) |

For TH display, keep the English term in parentheses for fields/forms — operational vocabulary stays English in Carmen.

### Common frontmatter timestamp

Use `2026-05-15T09:00:00.000Z` for both `date` and `dateCreated` on every new file in this plan. (For future edits, `date` will be updated; `dateCreated` stays.)

### Module substitutions

| Placeholder | EN value | TH value |
|-------------|----------|----------|
| `<Module>` | `Purchase Request` | `ใบขอซื้อ (Purchase Request)` |
| `<module-slug>` | `purchase-request` | `purchase-request` |

### Translation rules

- Translate prose only. Keep these in English: section numbers, frontmatter keys, code identifiers (Prisma model names, field names, enum values), file paths, rule IDs, slug values.
- TH frontmatter `title` and `description` are Thai. Other frontmatter values (tags, dates, editor) match EN.
- Cross-links inside TH files point at TH siblings (e.g. `./03-user-flow-requestor.th.md`).
- Tables: translate column headers and prose cells; keep code-like cell content in English.

### Verification per task

After writing each pair of files, run from the repo root:

```bash
python3 .specs/verify_frontmatter.py purchase-request/<file>.md
python3 .specs/verify_frontmatter.py purchase-request/<file>.th.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' purchase-request/<file>.md purchase-request/<file>.th.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

All three checks must pass before commit. If `grep` returns no match, it exits 1 — that's the "OK" path.

---

## File Structure

**Created files (28):**
```
purchase-request/01-data-model.md
purchase-request/01-data-model.th.md
purchase-request/02-business-rules.md
purchase-request/02-business-rules.th.md
purchase-request/03-user-flow.md
purchase-request/03-user-flow.th.md
purchase-request/03-user-flow-requestor.md
purchase-request/03-user-flow-requestor.th.md
purchase-request/03-user-flow-approver.md
purchase-request/03-user-flow-approver.th.md
purchase-request/03-user-flow-purchaser.md
purchase-request/03-user-flow-purchaser.th.md
purchase-request/03-user-flow-procurement-manager.md
purchase-request/03-user-flow-procurement-manager.th.md
purchase-request/03-user-flow-audit-config.md
purchase-request/03-user-flow-audit-config.th.md
purchase-request/04-test-scenarios.md
purchase-request/04-test-scenarios.th.md
purchase-request/04-test-scenarios-requestor.md
purchase-request/04-test-scenarios-requestor.th.md
purchase-request/04-test-scenarios-approver.md
purchase-request/04-test-scenarios-approver.th.md
purchase-request/04-test-scenarios-purchaser.md
purchase-request/04-test-scenarios-purchaser.th.md
purchase-request/04-test-scenarios-procurement-manager.md
purchase-request/04-test-scenarios-procurement-manager.th.md
purchase-request/04-test-scenarios-audit-config.md
purchase-request/04-test-scenarios-audit-config.th.md
```

**Modified file (1):**
- `purchase-request/index.md` — Section 7 replaced (Task 15).

---

## Task 1: 01-data-model (EN + TH)

**Files:**
- Create: `purchase-request/01-data-model.md`
- Create: `purchase-request/01-data-model.th.md`

**Sources:**
- Both Prisma schemas (tenant primary; platform if applicable). Search for the four PR models named in the Common Context section.
- `../carmen/docs/purchase-request-management/data-models.md` (cross-check)

**Template:** `.specs/templates/01-data-model.md` (uses the data-model template from the previous spec round)

- [ ] **Step 1: Read sources**

```bash
grep -n -A 30 'tb_purchase_request_header\|tb_purchase_request_detail\|tb_purchase_request_workflow\|tb_purchase_request_template_detail\|enum_purchase_request_doc_status' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma | less
cat ../carmen/docs/purchase-request-management/data-models.md
```

- [ ] **Step 2: Write `purchase-request/01-data-model.md`** using `.specs/templates/01-data-model.md` as the starting structure, with substitutions:
  - Title: `Purchase Request — Data Model`
  - Description: `Entities, fields, relationships, and enums for the purchase-request module.`
  - Tags: `purchase-request, data-model, inventory, carmen-software`
  - Dates: `2026-05-15T09:00:00.000Z` for both `date` and `dateCreated`

Fill sections:
- **Section 1 Overview:** what PR entities cover (header + line + workflow + template), 2-3 paragraphs.
- **Section 2 Entities:** one sub-section per Prisma model. Tables of fields with exact Prisma types. Cite `@@index`, `@@unique` constraints.
- **Section 3 Relationships:** FK chain — header has many details; detail references product, tax_profile, vendor; workflow stages chained to header; template_detail referenced by both.
- **Section 4 Enums:** `enum_purchase_request_doc_status` values with meaning of each. Also note the `purchase_request` value of `enum_purchase_order_type`.
- **Section 5 Divergences from carmen/docs:** compare what `data-models.md` says against Prisma. If they match, write `No divergences detected against carmen/docs as of 2026-05-15.` Otherwise fill the table.
- **Section 6 References:** point at the Prisma file paths (verbatim from the header callout) and `../carmen/docs/purchase-request-management/data-models.md`.

- [ ] **Step 3: Write `purchase-request/01-data-model.th.md`** as a section-by-section translation of the EN file. Title becomes `ใบขอซื้อ — แบบจำลองข้อมูล`. Description in Thai. Keep all Prisma model names, field names, type names, enum values, file paths in English. Translate the prose paragraphs and column headers. Section 5 fallback text becomes `ไม่พบความแตกต่างจาก carmen/docs ณ วันที่ 2026-05-15.`

- [ ] **Step 4: Run verification**

```bash
python3 .specs/verify_frontmatter.py purchase-request/01-data-model.md
python3 .specs/verify_frontmatter.py purchase-request/01-data-model.th.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' purchase-request/01-data-model.md purchase-request/01-data-model.th.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```
Expected: two `OK:` lines and `OK: no placeholders`.

- [ ] **Step 5: Commit**

```bash
git add purchase-request/01-data-model.md purchase-request/01-data-model.th.md
git commit -m "docs(purchase-request): add 01-data-model (EN + TH)

Prisma-derived entities, fields, relationships, and enums
for the four PR models. Divergences from carmen/docs noted
in Section 5."
```

---

## Task 2: 02-business-rules (EN + TH)

**Files:**
- Create: `purchase-request/02-business-rules.md`
- Create: `purchase-request/02-business-rules.th.md`

**Sources:**
- `../carmen/docs/purchase-request-management/purchase-request-ba.md`
- `../carmen/docs/purchase-request-management/PR-Technical-Specification.md`
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md`

**Template:** `.specs/templates/02-business-rules.md`

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/purchase-request-management/purchase-request-ba.md
cat ../carmen/docs/purchase-request-management/PR-Technical-Specification.md
cat ../carmen/docs/purchase-request-management/PR-Module-Structure.md
```

- [ ] **Step 2: Write `purchase-request/02-business-rules.md`** using the template structure with substitutions:
  - Title: `Purchase Request — Business Rules`
  - Description: `Validation, calculation, authorization, and posting rules for purchase-request.`
  - Tags: `purchase-request, business-rules, inventory, carmen-software`

Fill sections:
- **Section 1 Overview:** scope (which entities the rules govern), 1-2 paragraphs.
- **Section 2 Validation Rules:** table with rule IDs like `PR_VAL_001`. Pull rules from the BA and technical-spec docs: required fields, format constraints, line-level constraints (qty > 0, valid product, valid unit, etc.). Aim for 8-15 rules.
- **Section 3 Calculation Rules:** totals (sum of line subtotals), tax calculation, currency conversion (exchange rate snapshot), rounding (specific decimal precision). Show formulas with small worked examples.
- **Section 4 Authorization Rules:** approval threshold matrix — by amount tier × role × department. Multi-stage workflow: Department Head → Budget Controller → Finance → Procurement Manager. Send-back rights, reject rights, split-reject rights.
- **Section 5 Posting Rules:** what happens on PR submit (status → Submitted, soft-commitment to budget), on PR approve (status → Approved, ready for vendor allocation), on PR convert (status → Converted, generates PO).
- **Section 6 Cross-Module Rules:** budget-module integration (soft commitment), inventory (current-stock context), vendor (preferred-vendor lookup), pricelist (price reference), PO (conversion handoff).
- **Section 7 References:** the three carmen/docs source files plus backend NestJS module path if obvious from `../carmen-turborepo-backend-v2/apps/`.

- [ ] **Step 3: Write `purchase-request/02-business-rules.th.md`** — translate prose, keep rule IDs (e.g. `PR_VAL_001`), enum values, role names, currency codes in English.

- [ ] **Step 4: Run verification** (same three commands as Task 1, with filenames substituted)

```bash
python3 .specs/verify_frontmatter.py purchase-request/02-business-rules.md
python3 .specs/verify_frontmatter.py purchase-request/02-business-rules.th.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' purchase-request/02-business-rules.md purchase-request/02-business-rules.th.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 5: Commit**

```bash
git add purchase-request/02-business-rules.md purchase-request/02-business-rules.th.md
git commit -m "docs(purchase-request): add 02-business-rules (EN + TH)

Validation, calculation, authorization, posting, and
cross-module rules synthesised from purchase-request-ba.md,
PR-Technical-Specification.md, and PR-Module-Structure.md."
```

---

## Task 3: 03-user-flow overview (EN + TH)

**Files:**
- Create: `purchase-request/03-user-flow.md`
- Create: `purchase-request/03-user-flow.th.md`

**Sources:**
- `../carmen/docs/purchase-request-management/PR-Overview.md`
- `../carmen/docs/purchase-request-management/PR-User-Experience.md`
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md`

**Template:** Spec Section 6.1 (overview structure)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/purchase-request-management/PR-Overview.md
cat ../carmen/docs/purchase-request-management/PR-User-Experience.md
cat ../carmen/docs/purchase-request-management/purchase-request-module-prd.md
```

- [ ] **Step 2: Write `purchase-request/03-user-flow.md`**:

```markdown
---
title: Purchase Request — User Flow
description: Document lifecycle and persona-specific flow files for purchase-request.
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — User Flow

## 1. Overview
<2-paragraph scope: which doc types, which personas, where to drill down>

## 2. Document Lifecycle
| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
<Fill with the state transitions extracted from enum_purchase_request_doc_status + PR-User-Experience. Cover Draft → Submitted → In Review → Approved → Converted, plus Rejected, Sent Back, Cancelled, Voided.>

## 3. Persona Index
- [Requestor](./03-user-flow-requestor.md) — Creates and submits PRs, responds to send-backs.
- [Approver](./03-user-flow-approver.md) — Multi-stage approval chain (Department Head, Budget Controller, Finance).
- [Purchaser](./03-user-flow-purchaser.md) — Validates and converts approved PRs to POs.
- [Procurement Manager](./03-user-flow-procurement-manager.md) — Oversight, high-value approval, vendor ranking.
- [Audit / Config](./03-user-flow-audit-config.md) — Read-only audit (Auditor) + workflow configuration (Sysadmin).

## 4. Cross-Persona Handoffs
| From persona | Trigger | To persona | Document state at handoff |
| ------------ | ------- | ---------- | ------------------------- |
<Fill: Requestor → Department Head on submit; Department Head → Budget Controller after approval; etc.>

## 5. References
- `../carmen/docs/purchase-request-management/PR-User-Experience.md`
- `../carmen/docs/purchase-request-management/PR-Overview.md`
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md`
```

- [ ] **Step 3: Write `purchase-request/03-user-flow.th.md`** — translate. Persona Index links to `.th.md` siblings.

- [ ] **Step 4: Run verification**

```bash
python3 .specs/verify_frontmatter.py purchase-request/03-user-flow.md
python3 .specs/verify_frontmatter.py purchase-request/03-user-flow.th.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' purchase-request/03-user-flow.md purchase-request/03-user-flow.th.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 5: Commit**

```bash
git add purchase-request/03-user-flow.md purchase-request/03-user-flow.th.md
git commit -m "docs(purchase-request): add 03-user-flow overview (EN + TH)

Document lifecycle (state machine), persona index, and
cross-persona handoffs. Drill-down persona files come in
subsequent commits."
```

---

## Tasks 4–8: 03-user-flow-<persona> (EN + TH), per persona

Each task implements one persona's user-flow file pair. Same shape across the five persona tasks.

**Files (one task per row):**

| Task | Persona slug | EN file | TH file |
|------|--------------|---------|---------|
| 4 | `requestor` | `purchase-request/03-user-flow-requestor.md` | `purchase-request/03-user-flow-requestor.th.md` |
| 5 | `approver` | `purchase-request/03-user-flow-approver.md` | `purchase-request/03-user-flow-approver.th.md` |
| 6 | `purchaser` | `purchase-request/03-user-flow-purchaser.md` | `purchase-request/03-user-flow-purchaser.th.md` |
| 7 | `procurement-manager` | `purchase-request/03-user-flow-procurement-manager.md` | `purchase-request/03-user-flow-procurement-manager.th.md` |
| 8 | `audit-config` | `purchase-request/03-user-flow-audit-config.md` | `purchase-request/03-user-flow-audit-config.th.md` |

**Sources for all 5:** same three PR carmen/docs flow files (PR-Overview, PR-User-Experience, purchase-request-module-prd). For `audit-config`, also briefly check PR-Module-Structure.md for configuration surface.

**Persona-specific focus:**

| Persona | What to extract |
|---------|-----------------|
| `requestor` | Create PR → fill header (type, dept, currency) → add lines (product, qty, unit, est. price, delivery date) → attach docs → submit. Respond to send-back (edit + resubmit) or cancel. |
| `approver` | Receive notification → review header + lines → check budget alignment → adjust approved qty if needed → approve / reject / send-back / split-reject. Multi-stage: same UI used at Dept Head, Budget Controller, Finance, escalating by threshold. |
| `purchaser` | Inbox of approved PRs → review vendor allocation → look up pricelist → consolidate PRs with same vendor + currency → convert to PO. Handle vendor clarifications. |
| `procurement-manager` | High-value PR override approval → vendor ranking adjustments → Allocate Vendor rule tuning (rule maintenance is a configuration surface, not transactional). |
| `audit-config` | Auditor: view PR activity log (read-only). Sysadmin: configure workflow stages, thresholds, delegation, PR type defaults. |

### Task 4 detail (template for Tasks 4–8)

- [ ] **Step 1: Read sources** (same `cat` commands as Task 3 — once is enough if executing inline)

- [ ] **Step 2: Write the EN persona file** using this template, with persona-specific content:

```markdown
---
title: Purchase Request — User Flow — <Persona display>
description: <Persona display>'s flow within the purchase-request module.
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, user-flow, <persona-slug>, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — User Flow — <Persona display>

## 1. Role in This Module
<One paragraph: what this persona does in PR, where they sit in the chain, which document states they own. Pulled from the index.md Section 4 responsibility text + the persona-specific focus above.>

## 2. Entry Point and Primary Flow
**Entry point:** <screen / notification / trigger that brings this persona into the flow>

**Primary flow (happy path):**
1. <step>
2. <step>
<6-12 numbered steps end-to-end>

## 3. Decision Branches
- If <condition>: <alternate path or hand-off>
<3-6 branches based on document state, threshold breach, missing data, etc.>

## 4. Exit Point / Handoffs
<Where this persona's involvement ends: which state the document is in, who picks it up next.>

## 5. References
- Parent overview: [03-user-flow.md](./03-user-flow.md)
- `../carmen/docs/purchase-request-management/PR-User-Experience.md`
- `../carmen/docs/purchase-request-management/PR-Overview.md`
- `../carmen/docs/purchase-request-management/purchase-request-module-prd.md`
```

For Task 4 (`requestor`): `<Persona display>` = `Requestor`, `<persona-slug>` = `requestor`. Content uses the requestor focus listed above.

- [ ] **Step 3: Write the TH persona file.** Translate prose; `<Persona display>` becomes `ผู้ร้องขอ (Requestor)`. Cross-link to `./03-user-flow.th.md`.

- [ ] **Step 4: Run verification** (same commands with filenames substituted)

- [ ] **Step 5: Commit**

```bash
git add purchase-request/03-user-flow-requestor.md purchase-request/03-user-flow-requestor.th.md
git commit -m "docs(purchase-request): add 03-user-flow-requestor (EN + TH)

Requestor's flow within PR: create PR, add lines, submit,
respond to send-back."
```

### Tasks 5–8 follow the same shape

For each, substitute:
- Persona slug, display values (English and Thai) from the persona table at the top of this section
- Persona-specific focus content
- Commit message subject (`03-user-flow-<slug>`) and one-line body summary

Persona display values:

| Slug | EN display | TH display |
|------|-----------|-----------|
| `approver` | `Approver` | `ผู้อนุมัติ (Approver)` |
| `purchaser` | `Purchaser` | `เจ้าหน้าที่จัดซื้อ (Purchaser)` |
| `procurement-manager` | `Procurement Manager` | `ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager)` |
| `audit-config` | `Audit / Config` | `ผู้ตรวจสอบและผู้ดูแลระบบ (Audit / Config)` |

Commit summaries:
- Task 5: `Multi-stage approval chain: review, approve, reject, send-back, split-reject.`
- Task 6: `Validate and convert approved PRs to POs; vendor consolidation.`
- Task 7: `High-value approval override; vendor ranking; Allocate Vendor rule tuning.`
- Task 8: `Read-only audit (Auditor) and workflow / threshold configuration (Sysadmin).`

---

## Task 9: 04-test-scenarios overview (EN + TH)

**Files:**
- Create: `purchase-request/04-test-scenarios.md`
- Create: `purchase-request/04-test-scenarios.th.md`

**Sources:**
- `../carmen/docs/purchase-request-management/testing.md`
- `../carmen/docs/purchase-request-management/troubleshooting.md`
- `../carmen-inventory-frontend-e2e/tests/` (survey for PR-related spec files)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/purchase-request-management/testing.md
cat ../carmen/docs/purchase-request-management/troubleshooting.md
ls ../carmen-inventory-frontend-e2e/tests/ | grep -i 'purchase\|request\|pr-' || echo "no PR-named E2E tests found"
```

- [ ] **Step 2: Write `purchase-request/04-test-scenarios.md`**:

```markdown
---
title: Purchase Request — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for purchase-request.
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Test Scenarios

## 1. Overview
<Personas covered + scope of testing, 1-2 paragraphs.>

## 2. Personas in Scope
- **Requestor**: Creates and submits PRs; responds to send-backs.
- **Approver**: Multi-stage approval chain; approve / reject / send-back / split-reject.
- **Purchaser**: Validates vendor + pricing; consolidates and converts approved PRs to POs.
- **Procurement Manager**: High-value approval override; vendor ranking; rule tuning.
- **Audit / Config**: Audit-trail read (Auditor); workflow / threshold configuration (Sysadmin).

## 3. Persona Test Files
- [Requestor scenarios](./04-test-scenarios-requestor.md)
- [Approver scenarios](./04-test-scenarios-approver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Procurement Manager scenarios](./04-test-scenarios-procurement-manager.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios
| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
<Examples: full happy-path Requestor → Approver chain → Purchaser → PO; Send-back loop Requestor → Approver → Requestor → Approver → Approved; Split-reject leaving partial PR Approved.>

## 5. E2E Test Mapping
<Group by persona. Each row: persona, Playwright spec file, test name, scenarios covered. If no PR E2E tests exist yet, write "No E2E coverage yet — TODO: add tests under ../carmen-inventory-frontend-e2e/tests/purchase-request/ as the suite is built out.">

## 6. References
- `../carmen-inventory-frontend-e2e/`
- `../carmen/docs/purchase-request-management/testing.md`
- `../carmen/docs/purchase-request-management/troubleshooting.md`
```

- [ ] **Step 3: Write `purchase-request/04-test-scenarios.th.md`** — translate. Persona file links point to `.th.md` siblings.

- [ ] **Step 4: Run verification**

```bash
python3 .specs/verify_frontmatter.py purchase-request/04-test-scenarios.md
python3 .specs/verify_frontmatter.py purchase-request/04-test-scenarios.th.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' purchase-request/04-test-scenarios.md purchase-request/04-test-scenarios.th.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 5: Commit**

```bash
git add purchase-request/04-test-scenarios.md purchase-request/04-test-scenarios.th.md
git commit -m "docs(purchase-request): add 04-test-scenarios overview (EN + TH)

Personas in scope, persona file index, cross-persona
handoff scenarios, and E2E mapping placeholder."
```

---

## Tasks 10–14: 04-test-scenarios-<persona> (EN + TH), per persona

Each task implements one persona's test-scenarios file pair.

**Files (one task per row):**

| Task | Persona slug | EN file | TH file |
|------|--------------|---------|---------|
| 10 | `requestor` | `purchase-request/04-test-scenarios-requestor.md` | `purchase-request/04-test-scenarios-requestor.th.md` |
| 11 | `approver` | `purchase-request/04-test-scenarios-approver.md` | `purchase-request/04-test-scenarios-approver.th.md` |
| 12 | `purchaser` | `purchase-request/04-test-scenarios-purchaser.md` | `purchase-request/04-test-scenarios-purchaser.th.md` |
| 13 | `procurement-manager` | `purchase-request/04-test-scenarios-procurement-manager.md` | `purchase-request/04-test-scenarios-procurement-manager.th.md` |
| 14 | `audit-config` | `purchase-request/04-test-scenarios-audit-config.md` | `purchase-request/04-test-scenarios-audit-config.th.md` |

**Sources for all 5:** testing.md, troubleshooting.md, plus the persona's own user-flow file (Task 4–8 outputs) for context.

### Task 10 detail (template for Tasks 10–14)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/purchase-request-management/testing.md
cat ../carmen/docs/purchase-request-management/troubleshooting.md
cat purchase-request/03-user-flow-requestor.md  # for persona context
```

- [ ] **Step 2: Write the EN file** using this template:

```markdown
---
title: Purchase Request — Test Scenarios — <Persona display>
description: <Persona display>'s test cases (happy path, permission, validation, edge cases) for purchase-request.
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, test-scenarios, <persona-slug>, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# Purchase Request — Test Scenarios — <Persona display>

## 1. Happy Path
| # | Scenario | Pre-condition | Steps | Expected |
<5-10 happy-path scenarios for this persona, derived from the matching user-flow persona file.>

## 2. Permission / Authorization
| # | Scenario | Expected behaviour (allow/deny + reason) |
<5-10 scenarios — what this persona can/cannot do, especially at boundary thresholds and state transitions.>

## 3. Validation / Error
| # | Scenario | Trigger | Expected error |
<Cover every Business Rule (02-business-rules.md Section 2) the persona can trigger with at least one negative test.>

## 4. Edge Cases
| # | Scenario | Condition | Expected |
<3-8 boundary cases: zero qty, max amount, decimal precision, send-back loops, partial conversion, concurrent edits.>

## 5. References
- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-<persona-slug>.md](./03-user-flow-<persona-slug>.md)
- E2E: relevant Playwright specs in `../carmen-inventory-frontend-e2e/tests/` (cite file paths)
```

- [ ] **Step 3: Write the TH file.** Translate prose, keep rule IDs, enum values, field names in English. Cross-links target `.th.md` siblings.

- [ ] **Step 4: Run verification** (same three commands)

- [ ] **Step 5: Commit**

```bash
git add purchase-request/04-test-scenarios-requestor.md purchase-request/04-test-scenarios-requestor.th.md
git commit -m "docs(purchase-request): add 04-test-scenarios-requestor (EN + TH)

Requestor test cases: happy path, permission, validation
(against PR business rules), and edge cases."
```

### Tasks 11–14 follow the same shape

For each, substitute persona slug, EN display, TH display (per table at the top of Task 4-8 section), and commit body summary.

Commit summaries:
- Task 11: `Approver test cases: approval chain, send-back loops, split-reject edge cases.`
- Task 12: `Purchaser test cases: vendor allocation, PR consolidation, conversion to PO.`
- Task 13: `Procurement Manager test cases: high-value override, vendor ranking, rule tuning.`
- Task 14: `Audit / Config test cases: audit-trail read, workflow configuration changes.`

---

## Task 15: Update `purchase-request/index.md` Section 7 + push

**Files:**
- Modify: `purchase-request/index.md` (Section 7 only)

- [ ] **Step 1: Confirm all 28 sub-page files exist**

```bash
ls purchase-request/0*.md | wc -l
```
Expected: `28`.

- [ ] **Step 2: Open `purchase-request/index.md` and locate Section 7**

Currently reads:

```markdown
## 7. Pages in This Module

No sub-pages yet.
```

(Or similar. Confirm with `sed -n '/^## 7\./,$p' purchase-request/index.md | head -20`.)

- [ ] **Step 3: Replace Section 7** with:

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

- [ ] **Step 4: Update the `date` field in `purchase-request/index.md` frontmatter** to `2026-05-15T09:00:00.000Z`. Leave `dateCreated` unchanged.

- [ ] **Step 5: Verify all sub-page files plus index.md still parse**

```bash
for f in purchase-request/index.md purchase-request/0*.md; do
  python3 .specs/verify_frontmatter.py "$f"
done
```
Expected: 29 `OK:` lines (1 index + 28 sub-pages).

- [ ] **Step 6: Verify cross-link integrity (every `[[slug]]` resolves)**

```bash
grep -hRn '\[\[' --include='*.md' purchase-request/ | grep -o '\[\[[^]]*\]\]' | sort -u
```
Expected: only the 12 valid module slugs (`inventory`, `costing`, `inventory-adjustment`, `good-receive-note`, `store-requisition`, `physical-count`, `spot-check`, `purchase-request`, `purchase-order`, `vendor-pricelist`, `product`, `recipe`). Any unexpected slug is a bug — fix before commit.

- [ ] **Step 7: Commit and push**

```bash
git add purchase-request/index.md
git commit -m "docs(purchase-request): list 28 sub-pages in index Section 7

Section 7 lists 14 concepts × 2 languages (EN + TH).
Update date to 2026-05-15."

git push origin main
```
Expected: push succeeds. `git status` reports clean tree on `main`.
