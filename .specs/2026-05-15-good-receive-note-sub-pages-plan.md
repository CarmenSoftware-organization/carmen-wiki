# Good Receive Note Sub-Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the four sub-page types for the `good-receive-note/` module in English (TH deferred to a later round), with persona-axis pages decomposed into separate files per persona group — 12 page concepts in `en/good-receive-note/` + an updated `en/good-receive-note/index.md` Section 7.

**Architecture:** Each page concept produces one EN file in `en/good-receive-note/`. No TH files created this round; no `th/good-receive-note/` directory. Persona-axis pages (03-user-flow, 04-test-scenarios) split into an overview file plus 4 persona files (receiver, purchaser, finance, audit-config). Each commit covers one concept.

**Tech Stack:** Markdown only. Frontmatter verifier at `.specs/verify_frontmatter.py`. Working directory: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`. Branch: `main` (user-approved direct commits).

**Reference spec:** `.specs/2026-05-15-good-receive-note-sub-pages-design.md`
**Reference modules:** purchase-request and purchase-order — patterns applied unchanged for content-axis page templates and persona-file structure.

---

## Common Context

### Sources

**Prisma (primary for 01-data-model):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
  - `tb_good_received_note` (line 804), `tb_good_received_note_comment` (886), `tb_good_received_note_detail` (920), `tb_good_received_note_detail_comment` (949), `tb_good_received_note_detail_item` (983)
  - `enum_good_received_note_status` (102), `enum_good_received_note_type` (145)

**carmen/docs (secondary):**
- `../carmen/docs/good-recive-note-managment/GRN-Technical-Specification.md` — for data model + business rules
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md` — for data model + business rules + user flow
- `../carmen/docs/good-recive-note-managment/grn-create-process-doc.md` — for business rules (process detail)
- `../carmen/docs/good-recive-note-managment/GRN-User-Experience.md` — for user flow
- `../carmen/docs/good-recive-note-managment/GRN-User-Flow-Diagram.md` — for user flow
- `../carmen/docs/good-recive-note-managment/GRN-Overview.md` — for user flow + business context

(Note: carmen/docs folder still has the typo `good-recive-note-managment`; do NOT change the path.)

**E2E (for 04-test-scenarios):**
- `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`

### Persona slugs (fixed, 4 groups)

| Slug | Source personas in `en/good-receive-note/index.md` Section 4 | EN display |
|------|--------------------------------------------------------------|-----------|
| `receiver` | Store Keeper / Receiving Clerk + Store Manager / Inventory Manager | Receiver |
| `purchaser` | Purchaser / Procurement Officer + Department Manager | Purchaser |
| `finance` | Finance Team / AP Clerk | Finance |
| `audit-config` | System Administrator (Auditor concerns folded in as read-only) | Audit / Config |

### Common frontmatter timestamp

Use `2026-05-15T11:00:00.000Z` for both `date` and `dateCreated` on every new file.

### Module-level substitutions

| Placeholder | EN value |
|-------------|----------|
| `<Module>` | `Good Receive Note (GRN)` |
| `<module-slug>` | `good-receive-note` |

### Verification per task

After writing each EN file, run from the repo root:

```bash
python3 .specs/verify_frontmatter.py en/good-receive-note/<file>.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/good-receive-note/<file>.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

Both checks must pass before commit.

---

## File Structure

**Created files in `en/good-receive-note/` (12):**
- `01-data-model.md`, `02-business-rules.md`
- `03-user-flow.md` (overview), `03-user-flow-{receiver,purchaser,finance,audit-config}.md` (4)
- `04-test-scenarios.md` (overview), `04-test-scenarios-{receiver,purchaser,finance,audit-config}.md` (4)

**Modified files (1):**
- `en/good-receive-note/index.md` — Section 7 replaced (Task 13). Frontmatter `date` updated to `2026-05-15T11:00:00.000Z`; `dateCreated` unchanged.

**No files created in `th/`.**

---

## Task 1: 01-data-model

**Files:** Create `en/good-receive-note/01-data-model.md`

**Sources:**
- Prisma tenant schema — 5 GRN models + 2 enums (see Common Context)
- `../carmen/docs/good-recive-note-managment/GRN-Technical-Specification.md`
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md`

**Template:** `.specs/templates/01-data-model.md`

- [ ] **Step 1: Read Prisma source**

```bash
grep -n -A 80 'model tb_good_received_note\b\|model tb_good_received_note_comment\b\|model tb_good_received_note_detail\b\|model tb_good_received_note_detail_comment\b\|model tb_good_received_note_detail_item\b\|enum enum_good_received_note_status\b\|enum enum_good_received_note_type\b' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma | less
```

- [ ] **Step 2: Read carmen/docs sources**

```bash
cat ../carmen/docs/good-recive-note-managment/GRN-Technical-Specification.md
cat ../carmen/docs/good-recive-note-managment/grn-master-prd.md
```

- [ ] **Step 3: Write `en/good-receive-note/01-data-model.md`**

Frontmatter:
```yaml
---
title: Good Receive Note (GRN) — Data Model
description: Entities, fields, relationships, and enums for the good-receive-note module.
published: true
date: 2026-05-15T11:00:00.000Z
tags: good-receive-note, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---
```

Sections:
- **Source of truth callout** (after H1) — standard template blockquote pointing at both Prisma schemas.
- **Section 1 Overview:** 2-3 paragraphs — entities owned (header + line + detail-item for lot/serial + comments), positioning (downstream of `[[purchase-order]]` via reference, upstream of `[[inventory]]` via on-hand increment, central anchor for three-way match).
- **Section 2 Entities:** one `### 2.x` per Prisma model (5 entities). Field table (Field / Prisma Type / Nullable / Description). Below each: `**Constraints:**` and `**Indexes:**` lines citing `@@unique`, `@@index`, `@@id` from Prisma. Highlight `tb_good_received_note_detail_item` — this is the GRN-specific lot/expiry/serial tracking entity (PR/PO don't have an equivalent).
- **Section 3 Relationships:** text or simple ASCII showing header→detail (1-many), detail→detail_item (1-many for lot tracking), header→comment, detail→comment. FK to `tb_purchase_order` (header) and `tb_purchase_order_detail` (line).
- **Section 4 Enums:** `enum_good_received_note_status` (all values + meaning of each) + `enum_good_received_note_type` (all values).
- **Section 5 Divergences from carmen/docs:** compare Prisma against the GRN-Technical-Specification and grn-master-prd. If consistent, write `No divergences detected against carmen/docs as of 2026-05-15.` Otherwise fill the table with concrete rows.
- **Section 6 References:** two Prisma file paths plus the two carmen/docs files.

- [ ] **Step 4: Verify**

```bash
python3 .specs/verify_frontmatter.py en/good-receive-note/01-data-model.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/good-receive-note/01-data-model.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 5: Commit**

```bash
git add en/good-receive-note/01-data-model.md
git commit -m "docs(good-receive-note): add 01-data-model (EN)

Prisma-derived entities, fields, relationships, and enums
for the five GRN models. Includes the GRN-specific
detail_item entity for lot / expiry / serial tracking."
```

---

## Task 2: 02-business-rules

**Files:** Create `en/good-receive-note/02-business-rules.md`

**Sources:**
- `../carmen/docs/good-recive-note-managment/GRN-Technical-Specification.md`
- `../carmen/docs/good-recive-note-managment/grn-master-prd.md`
- `../carmen/docs/good-recive-note-managment/grn-create-process-doc.md`
- Sibling `en/good-receive-note/01-data-model.md` (just written) for entity reference

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/good-recive-note-managment/GRN-Technical-Specification.md
cat ../carmen/docs/good-recive-note-managment/grn-master-prd.md
cat ../carmen/docs/good-recive-note-managment/grn-create-process-doc.md
```

- [ ] **Step 2: Write `en/good-receive-note/02-business-rules.md`** using template `.specs/templates/02-business-rules.md`

Frontmatter:
- `title: Good Receive Note (GRN) — Business Rules`
- `description: Validation, calculation, authorization, posting, three-way-match, and cross-module rules for good-receive-note.`
- `tags: good-receive-note, business-rules, inventory, carmen-software`
- Dates: `2026-05-15T11:00:00.000Z`

Sections:
- **Section 1 Overview:** 1-2 paragraphs — scope of rules; which entities they govern; emphasis on lot tracking, extra-cost allocation, three-way match (these are GRN-specific concerns per spec Section 7).
- **Section 2 Validation Rules:** table `| Rule ID | Condition | When enforced | Error / behaviour |`. Rule IDs `GRN_VAL_001`–`GRN_VAL_NNN`. Cover: required header (vendor, currency, receipt date, PO reference), required line (product, received_qty > 0, unit, lot info where lot-tracked), at-commit checks (at least one line, accepted_qty ≤ received_qty, accepted_qty ≥ 0 for posted lines, PO line must be open / not fully received yet), lot/expiry validation. Aim 10-15 rules.
- **Section 3 Calculation Rules:** line subtotal (`received_qty × unit_price`), accepted subtotal (`accepted_qty × unit_price`), variance (`received_qty − ordered_qty`), header totals, extra-cost allocation across received lines proportionally (by value or quantity — pick per source spec), tax calculation, currency conversion. One worked example in `฿`.
- **Section 4 Authorization Rules:** Receiver can create + edit draft GRN, Inventory Manager can commit, Finance can adjust extra-cost allocation before AP posting, void rights, batch commit rights. Segregation: Receiver ≠ Purchaser (cannot raise PO they receive). Use a matrix or per-role bullets.
- **Section 5 Posting Rules:** what happens on commit — inventory on-hand increment via stock movement (cross-ref `[[inventory]]`), PO line `received_qty` increment, PO state advances (`sent` → `partial` or `completed`), GL accrual for AP-pending, three-way match flag set. Map to actual `enum_good_received_note_status` values.
- **Section 6 Cross-Module Rules:** PO integration (receive only against open PO line, cannot receive against `voided` PO), inventory integration (on-hand increment on commit, valuation per costing method), finance integration (three-way match triggers AP posting), vendor performance feedback (variance recorded against vendor). Reference `[[purchase-order]]`, `[[inventory]]`, `[[vendor-pricelist]]`, `[[costing]]`.
- **Section 7 References:** the three carmen/docs sources + sibling `01-data-model.md` + backend module hint.

- [ ] **Step 3: Verify**

```bash
python3 .specs/verify_frontmatter.py en/good-receive-note/02-business-rules.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/good-receive-note/02-business-rules.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 4: Commit**

```bash
git add en/good-receive-note/02-business-rules.md
git commit -m "docs(good-receive-note): add 02-business-rules (EN)

Validation, calculation (including extra-cost allocation),
authorization, posting (inventory increment + PO advance +
three-way match anchor), and cross-module rules synthesised
from GRN-Technical-Specification, grn-master-prd, and
grn-create-process-doc."
```

---

## Task 3: 03-user-flow overview

**Files:** Create `en/good-receive-note/03-user-flow.md`

**Sources:**
- `../carmen/docs/good-recive-note-managment/GRN-User-Experience.md`
- `../carmen/docs/good-recive-note-managment/GRN-User-Flow-Diagram.md`
- `../carmen/docs/good-recive-note-managment/GRN-Overview.md`
- Sibling `en/good-receive-note/01-data-model.md` Section 4 (lifecycle enum values)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/good-recive-note-managment/GRN-User-Experience.md
cat ../carmen/docs/good-recive-note-managment/GRN-User-Flow-Diagram.md
cat ../carmen/docs/good-recive-note-managment/GRN-Overview.md
grep -A 20 'enum_good_received_note_status' en/good-receive-note/01-data-model.md
```

- [ ] **Step 2: Write `en/good-receive-note/03-user-flow.md`**

```markdown
---
title: Good Receive Note (GRN) — User Flow
description: Document lifecycle and persona-specific flow files for good-receive-note.
published: true
date: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# Good Receive Note (GRN) — User Flow

## 1. Overview
<2-paragraph scope: GRN is the document recording physical receipt of goods against a PO; central anchor for three-way match; this page covers lifecycle states and points to per-persona files.>

## 2. Document Lifecycle
| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
<8-12 rows using actual enum_good_received_note_status values. Examples likely include: (none) → create → Received (Draft); Received → save → Received; Received → commit → Committed; Received → cancel → Cancelled / Voided; Committed → adjust → Committed (amendment); Committed → void → Voided; any → batch-commit → Committed.>

## 3. Persona Index
- [Receiver](./03-user-flow-receiver.md) — Creates GRN at the dock, counts, inspects, records lot info, commits (Inventory Manager subset).
- [Purchaser](./03-user-flow-purchaser.md) — Owns upstream PO, reviews receiving info, investigates variance, coordinates vendor resolution. Department Manager reviews cost-centre variance.
- [Finance](./03-user-flow-finance.md) — Three-way match, extra-cost allocation, AP posting, period close.
- [Audit / Config](./03-user-flow-audit-config.md) — Sysadmin (lot format, RBAC, integration) + read-only audit.

## 4. Cross-Persona Handoffs
| From persona | Trigger | To persona | Document state at handoff |
| ------------ | ------- | ---------- | ------------------------- |
<5-8 rows: Receiver → Inventory Manager on commit-ready; Receiver/Inventory Manager → Finance on commit; Inventory Manager → Purchaser on variance flagged; Finance → Purchaser on three-way match discrepancy; Sysadmin → all on lot format change.>

## 5. References
- `../carmen/docs/good-recive-note-managment/GRN-User-Experience.md`
- `../carmen/docs/good-recive-note-managment/GRN-User-Flow-Diagram.md`
- `../carmen/docs/good-recive-note-managment/GRN-Overview.md`
- Sibling: [01-data-model.md](./01-data-model.md) for the lifecycle enum
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 for posting / transition rules
```

- [ ] **Step 3: Verify**

```bash
python3 .specs/verify_frontmatter.py en/good-receive-note/03-user-flow.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/good-receive-note/03-user-flow.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 4: Commit**

```bash
git add en/good-receive-note/03-user-flow.md
git commit -m "docs(good-receive-note): add 03-user-flow overview (EN)

Lifecycle state machine, 4-persona index, and cross-persona
handoffs. Drill-down persona files come in subsequent commits."
```

---

## Tasks 4–7: 03-user-flow-<persona>, per persona

Each task implements one persona's user-flow file using the persona-file template from the PR module spec Section 6.2.

| Task | Persona slug | File |
|------|--------------|------|
| 4 | `receiver` | `en/good-receive-note/03-user-flow-receiver.md` |
| 5 | `purchaser` | `en/good-receive-note/03-user-flow-purchaser.md` |
| 6 | `finance` | `en/good-receive-note/03-user-flow-finance.md` |
| 7 | `audit-config` | `en/good-receive-note/03-user-flow-audit-config.md` |

**Sources for all 4:** the three GRN flow-related carmen/docs files + the persona's responsibility text from `en/good-receive-note/index.md` Section 4.

**Persona-specific focus:**

| Persona | What to extract |
|---------|-----------------|
| `receiver` | Physical receipt at dock → count and inspect against PO and delivery note → create GRN in `Received` (Draft) → record line received_qty, accepted_qty, lot numbers, expiry dates → attach packing slips and quality evidence → resolve discrepancies → commit (Inventory Manager subset) or batch-commit at end of shift. |
| `purchaser` | Receive notification of GRN against own PO → review receiving info → investigate variance (late / short / damaged / wrong item) → coordinate vendor resolution → Department Manager subset reviews cost-centre variance + price variance against vendor pricelist. |
| `finance` | Post-commit: three-way match (GRN ↔ PO ↔ invoice) → validate extra-cost allocation and tax → adjust/finalise GRN financial entries → AP posting → reconcile inventory sub-ledger against GL → period-close sign-off. |
| `audit-config` | Sysadmin: maintain lot-number generation format, RBAC, tax/currency/reason codes, integration config. Auditor (folded in): read-only audit trail across receipt activity, variance reports, lot tracing for recalls. |

### Task 4 detail (shape for Tasks 4–7)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/good-recive-note-managment/GRN-User-Experience.md
cat ../carmen/docs/good-recive-note-managment/GRN-User-Flow-Diagram.md
cat ../carmen/docs/good-recive-note-managment/GRN-Overview.md
sed -n '/^## 4\. Roles/,/^## 5\./p' en/good-receive-note/index.md
```

- [ ] **Step 2: Write the EN persona file** using this template (substitute persona slug + EN display):

```markdown
---
title: Good Receive Note (GRN) — User Flow — <Persona display>
description: <Persona display>'s flow within the good-receive-note module.
published: true
date: 2026-05-15T11:00:00.000Z
tags: good-receive-note, user-flow, <persona-slug>, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# Good Receive Note (GRN) — User Flow — <Persona display>

## 1. Role in This Module
<1 paragraph: what this persona does in GRN, where they sit in the chain, which document states they touch. Pulled from index.md Section 4 + persona-specific focus above.>

## 2. Entry Point and Primary Flow
**Entry point:** <screen / notification / trigger>

**Primary flow (happy path):**
1. <step>
...
<6-12 steps end-to-end>

## 3. Decision Branches
- If <condition>: <alternate path or hand-off>
<3-6 branches>

## 4. Exit Point / Handoffs
<Where this persona's involvement ends, including document state and the next persona.>

## 5. References
- Parent overview: [03-user-flow.md](./03-user-flow.md)
- `../carmen/docs/good-recive-note-managment/GRN-User-Experience.md`
- `../carmen/docs/good-recive-note-managment/GRN-Overview.md`
- Cross-link to relevant sibling persona files where handoff occurs
```

For Task 4 (`receiver`): `<Persona display>` = `Receiver`, `<persona-slug>` = `receiver`. Content uses the receiver focus above.

- [ ] **Step 3: Verify**

```bash
python3 .specs/verify_frontmatter.py en/good-receive-note/03-user-flow-receiver.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/good-receive-note/03-user-flow-receiver.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 4: Commit**

```bash
git add en/good-receive-note/03-user-flow-receiver.md
git commit -m "docs(good-receive-note): add 03-user-flow-receiver (EN)

Receiver's flow: physical receipt → count + inspect → GRN
creation with lot/expiry → commit (or batch-commit)."
```

### Tasks 5–7 follow the same shape

For each, substitute persona slug + EN display from the persona table at the top of Task 4–7 section, focus content per the persona-specific focus column, and a commit body summary.

Commit body summaries:
- Task 5 (purchaser): `Owns upstream PO; reviews GRN against PO, investigates variance, coordinates vendor resolution. Department Manager reviews cost-centre.`
- Task 6 (finance): `Three-way match, extra-cost allocation, AP posting, period-close reconciliation.`
- Task 7 (audit-config): `Lot-number format, RBAC, tax/currency/reason codes, integration config. Read-only audit trail folded in.`

---

## Task 8: 04-test-scenarios overview

**Files:** Create `en/good-receive-note/04-test-scenarios.md`

**Sources:**
- `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`
- Sibling `en/good-receive-note/03-user-flow.md` Section 4 (cross-persona handoffs)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts
sed -n '/^## 4\. Cross-Persona/,/^## 5\./p' en/good-receive-note/03-user-flow.md
```

- [ ] **Step 2: Write `en/good-receive-note/04-test-scenarios.md`**

```markdown
---
title: Good Receive Note (GRN) — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for good-receive-note.
published: true
date: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# Good Receive Note (GRN) — Test Scenarios

## 1. Overview
<1-2 paragraphs: 4 personas + scope of testing (functional + RBAC + edge + three-way match + lot tracking).>

## 2. Personas in Scope
- **Receiver**: <one-line>
- **Purchaser**: <one-line>
- **Finance**: <one-line>
- **Audit / Config**: <one-line>

## 3. Persona Test Files
- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios
| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
<6-10 rows covering end-to-end paths. Examples:
- Full happy path: Receiver creates GRN → Inventory Manager commits → Finance matches invoice → AP posted
- Partial receipt: Receiver creates partial GRN → commits → second GRN later → PO completed → Finance match
- Quality issue: Receiver records accepted_qty < received_qty → Inventory Manager commits with quality flag
- Wrong item: Receiver rejects line → Purchaser investigates with vendor
- Three-way mismatch: GRN ok → Finance flags invoice discrepancy → bounce-back
- Extra-cost allocation: Receiver records freight/duty → Finance reviews allocation
- Batch commit: Inventory Manager processes N draft GRNs at end of shift
- Lot recall: Sysadmin queries by lot → Auditor traces affected GRNs
- Void post-commit: Sysadmin voids committed GRN (escalated)>

## 5. E2E Test Mapping
<List 501-grn.spec.ts with test names and which Section 4 scenarios they cover. Note no per-persona dedicated specs — per-persona test files will reference the shared spec.>

## 6. References
- `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts`
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 (posting + three-way match)
```

- [ ] **Step 3: Verify**

```bash
python3 .specs/verify_frontmatter.py en/good-receive-note/04-test-scenarios.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/good-receive-note/04-test-scenarios.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 4: Commit**

```bash
git add en/good-receive-note/04-test-scenarios.md
git commit -m "docs(good-receive-note): add 04-test-scenarios overview (EN)

Personas in scope, persona file index, cross-persona
handoff scenarios (including three-way match + lot recall),
and E2E mapping to 501-grn.spec.ts."
```

---

## Tasks 9–12: 04-test-scenarios-<persona>, per persona

Each task implements one persona's test-scenarios file using the persona test-scenarios template from the PR module spec Section 6.4.

| Task | Persona slug | File |
|------|--------------|------|
| 9 | `receiver` | `en/good-receive-note/04-test-scenarios-receiver.md` |
| 10 | `purchaser` | `en/good-receive-note/04-test-scenarios-purchaser.md` |
| 11 | `finance` | `en/good-receive-note/04-test-scenarios-finance.md` |
| 12 | `audit-config` | `en/good-receive-note/04-test-scenarios-audit-config.md` |

**Sources for all 4:** `501-grn.spec.ts` + `02-business-rules.md` (for negative tests) + the persona's matching `03-user-flow-<persona>.md` file (for happy-path scenarios).

### Task 9 detail (shape for Tasks 9–12)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts
cat en/good-receive-note/03-user-flow-receiver.md
sed -n '/^## 2\. Validation/,/^## 3\./p' en/good-receive-note/02-business-rules.md
```

- [ ] **Step 2: Write the EN file** using this template:

```markdown
---
title: Good Receive Note (GRN) — Test Scenarios — <Persona display>
description: <Persona display>'s test cases (happy path, permission, validation, edge cases) for good-receive-note.
published: true
date: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, <persona-slug>, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---

# Good Receive Note (GRN) — Test Scenarios — <Persona display>

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
- User flow: [03-user-flow-<slug>.md](./03-user-flow-<slug>.md)
- E2E: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` (no dedicated persona spec yet)
```

Scenario ID prefixes:
- Task 9 (receiver): `RCV-` (e.g. `RCV-HP-01`, `RCV-PERM-01`, etc.)
- Task 10 (purchaser): `PUR-`
- Task 11 (finance): `FIN-`
- Task 12 (audit-config): `AUD-`

Aim for 5-10 happy-path, 4-8 permission, 6-10 validation, 3-7 edge per persona.

- [ ] **Step 3: Verify**

```bash
python3 .specs/verify_frontmatter.py en/good-receive-note/04-test-scenarios-receiver.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/good-receive-note/04-test-scenarios-receiver.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 4: Commit**

```bash
git add en/good-receive-note/04-test-scenarios-receiver.md
git commit -m "docs(good-receive-note): add 04-test-scenarios-receiver (EN)

Receiver test cases: GRN creation, line entry with lot info,
quality issue handling, batch commit, partial receipt."
```

### Tasks 10–12 follow the same shape

Commit body summaries:
- Task 10 (purchaser): `Purchaser test cases: own-PO GRN review, variance investigation, vendor coordination. Department Manager cost-centre review.`
- Task 11 (finance): `Finance test cases: three-way match, extra-cost allocation, AP posting, period-close reconciliation.`
- Task 12 (audit-config): `Audit / Config test cases: lot format change, RBAC change, integration config, audit-trail query, lot recall.`

---

## Task 13: EN index Section 7 update + push

**Files:**
- Modify: `en/good-receive-note/index.md` (Section 7 + frontmatter `date`)

- [ ] **Step 1: Confirm all 12 sub-page files exist**

```bash
ls en/good-receive-note/0*.md | wc -l
```
Expected: `12`.

- [ ] **Step 2: Open `en/good-receive-note/index.md` and locate Section 7**

```bash
sed -n '/^## 7\./,$p' en/good-receive-note/index.md | head -10
```

- [ ] **Step 3: Replace Section 7 with**:

```markdown
## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](./02-business-rules.md) — Validation, calculation, authorization, posting, and three-way-match rules.
- [03 — User Flow](./03-user-flow.md) — Document lifecycle and persona index.
  - [Receiver](./03-user-flow-receiver.md)
  - [Purchaser](./03-user-flow-purchaser.md)
  - [Finance](./03-user-flow-finance.md)
  - [Audit / Config](./03-user-flow-audit-config.md)
- [04 — Test Scenarios](./04-test-scenarios.md) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Receiver](./04-test-scenarios-receiver.md)
  - [Purchaser](./04-test-scenarios-purchaser.md)
  - [Finance](./04-test-scenarios-finance.md)
  - [Audit / Config](./04-test-scenarios-audit-config.md)
```

- [ ] **Step 4: Update `en/good-receive-note/index.md` frontmatter `date`** to `2026-05-15T11:00:00.000Z`. Leave `dateCreated` unchanged.

- [ ] **Step 5: Run comprehensive verification**

```bash
for f in en/good-receive-note/index.md en/good-receive-note/0*.md; do
  python3 .specs/verify_frontmatter.py "$f"
done

grep -rn '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/good-receive-note/ && echo "FAIL: placeholders remain" || echo "OK: no placeholders"

grep -hRn '\[\[' --include='*.md' en/good-receive-note/ | grep -o '\[\[[^]]*\]\]' | sort -u
```

Expected:
- 13 `OK:` lines (1 index + 12 sub-pages)
- `OK: no placeholders`
- Cross-link slugs: only from the 12 valid module slugs (`inventory`, `costing`, `inventory-adjustment`, `good-receive-note`, `store-requisition`, `physical-count`, `spot-check`, `purchase-request`, `purchase-order`, `vendor-pricelist`, `product`, `recipe`)

- [ ] **Step 6: Commit and push**

```bash
git status
git add en/good-receive-note/index.md
git commit -m "docs(good-receive-note): update EN index Section 7

Section 7 lists 12 sub-pages (4 main + 8 persona-axis).
TH translations are deferred to a later round per spec.
Date bumped to 2026-05-15T11:00:00.000Z."

git push origin main
```

Expected: push succeeds.
