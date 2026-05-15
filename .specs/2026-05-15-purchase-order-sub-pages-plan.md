# Purchase Order Sub-Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the four sub-page types for the `purchase-order/` module in both English (canonical) and Thai, with persona-axis pages decomposed into separate files per persona group — 16 page concepts × 2 languages = 32 files + a new `th/purchase-order/index.md` + an updated `en/purchase-order/index.md` Section 7.

**Architecture:** Each page concept produces an EN file in `en/purchase-order/` and a matching TH file in `th/purchase-order/`. Wiki.js handles the language toggle across the locale trees; each tree is self-contained (relative cross-links inside the same locale). EN is canonical; TH is a section-for-section translation. Persona-axis pages (03-user-flow, 04-test-scenarios) split into an overview file plus 6 persona files. Each commit pairs one concept's EN + TH files.

**Tech Stack:** Markdown only. Frontmatter verifier at `.specs/verify_frontmatter.py`. Working directory: `/Users/samutpra/GitHub/carmensoftware-organize/carmen-wiki`. Branch: `main` (user-approved direct commits).

**Reference spec:** `.specs/2026-05-15-purchase-order-sub-pages-design.md`
**Reference module:** PR module — `.specs/2026-05-15-purchase-request-sub-pages-design.md` and the executed sub-pages at `en/purchase-request/` + `th/purchase-request/`. Patterns established there apply unchanged.

---

## Common Context

### Sources

**Prisma (primary for 01-data-model):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
  - `tb_purchase_order` (line 1818), `tb_purchase_order_comment` (1893), `tb_purchase_order_detail` (1927), `tb_purchase_order_detail_comment` (2041), `tb_purchase_order_detail_tb_purchase_request_detail` bridge (2075)
  - `enum_purchase_order_type` (150), `enum_purchase_order_doc_status` (235)

**carmen/docs (secondary, thin — only 1 file):**
- `../carmen/docs/purchase-order-management/purchase-order-module.md`

**Supplementary (cross-module flow):**
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` — PR→PO conversion
- `../carmen/docs/purchase-request-management/purchase-request-ba.md` — vendor allocation rules

**E2E (for 04-test-scenarios):**
- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/403-po-approver-journey.spec.ts`

### Persona slugs (fixed, 6 groups)

| Slug | Source personas in `en/purchase-order/index.md` Section 4 | EN display | TH display |
|------|------------------------------------------------------------|-----------|-----------|
| `purchaser` | Procurement Officer / Purchaser | Purchaser | เจ้าหน้าที่จัดซื้อ (Purchaser) |
| `procurement-manager` | Procurement Manager | Procurement Manager | ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager) |
| `vendor` | Vendor | Vendor | ผู้ขาย (Vendor) |
| `receiver` | Receiver / Store Keeper + Inventory Manager | Receiver | ผู้รับสินค้า (Receiver) |
| `finance` | Finance Officer / AP + Finance Manager | Finance | ฝ่ายการเงิน (Finance) |
| `audit-config` | Auditor + System Administrator | Audit / Config | ผู้ตรวจสอบและผู้ดูแลระบบ (Audit / Config) |

### Common frontmatter timestamp

Use `2026-05-15T10:00:00.000Z` for both `date` and `dateCreated` on every new file.

### Module-level substitutions

| Placeholder | EN value | TH value |
|-------------|----------|----------|
| `<Module>` | `Purchase Order` | `ใบสั่งซื้อ (Purchase Order)` |
| `<module-slug>` | `purchase-order` | `purchase-order` |

### Translation rules

- Translate prose only. Keep these in English: section numbers, frontmatter keys, code identifiers (Prisma model names, field names, enum values), file paths, rule IDs, slug values, currency codes, status names.
- Cross-links inside the same locale tree (e.g. `[03-user-flow.md](./03-user-flow.md)`) — paths stay relative; same path string works in both EN and TH files because each tree is self-contained.
- Cross-module `[[slug]]` references — slug stays English; surrounding prose is translated.

### Verification per task

After writing each pair of files, run from the repo root:

```bash
python3 .specs/verify_frontmatter.py en/purchase-order/<file>.md
python3 .specs/verify_frontmatter.py th/purchase-order/<file>.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/purchase-order/<file>.md th/purchase-order/<file>.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

All three checks must pass before commit.

---

## File Structure

**Created files in `en/purchase-order/` (16):**
- `01-data-model.md`, `02-business-rules.md`
- `03-user-flow.md` (overview), `03-user-flow-{purchaser,procurement-manager,vendor,receiver,finance,audit-config}.md` (6)
- `04-test-scenarios.md` (overview), `04-test-scenarios-{purchaser,procurement-manager,vendor,receiver,finance,audit-config}.md` (6)

**Created files in `th/purchase-order/` (17):**
- Same 16 sub-pages as the EN list, plus
- `index.md` (NEW — TH translation of the existing EN landing page)

**Modified files (1):**
- `en/purchase-order/index.md` — Section 7 replaced (Task 17). Frontmatter `date` updated to `2026-05-15T10:00:00.000Z`; `dateCreated` unchanged.

---

## Task 1: 01-data-model (EN + TH)

**Files:**
- Create: `en/purchase-order/01-data-model.md`
- Create: `th/purchase-order/01-data-model.md`

**Sources:**
- Prisma tenant schema — search for `tb_purchase_order`, `tb_purchase_order_comment`, `tb_purchase_order_detail`, `tb_purchase_order_detail_comment`, `tb_purchase_order_detail_tb_purchase_request_detail`, `enum_purchase_order_type`, `enum_purchase_order_doc_status`
- `../carmen/docs/purchase-order-management/purchase-order-module.md` (cross-check)
- Sibling: `en/purchase-request/01-data-model.md` (PR data-model documented the bridge table — reference, don't duplicate)

**Template:** `.specs/templates/01-data-model.md`

- [ ] **Step 1: Read Prisma source**

```bash
grep -n -A 80 'model tb_purchase_order\b\|model tb_purchase_order_comment\b\|model tb_purchase_order_detail\b\|model tb_purchase_order_detail_comment\b\|model tb_purchase_order_detail_tb_purchase_request_detail\b\|enum enum_purchase_order_type\b\|enum enum_purchase_order_doc_status\b' ../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma | less
```

- [ ] **Step 2: Read carmen/docs cross-check source**

```bash
cat ../carmen/docs/purchase-order-management/purchase-order-module.md
```

- [ ] **Step 3: Write `en/purchase-order/01-data-model.md`**

Use the template at `.specs/templates/01-data-model.md` with substitutions:
- Title: `Purchase Order — Data Model`
- Description: `Entities, fields, relationships, and enums for the purchase-order module.`
- Tags: `purchase-order, data-model, inventory, carmen-software`
- Dates: `2026-05-15T10:00:00.000Z` for both `date` and `dateCreated`

Sections:
- **Source of truth callout:** keep verbatim from the template, pointing at both Prisma schemas.
- **Section 1 Overview:** 2-3 paragraphs — entities owned by this module (header + line + comment tables + the PR↔PO bridge), brief positioning (downstream of PR via the bridge; upstream of GRN via the PO line `pending_qty`).
- **Section 2 Entities:** one `### 2.x` per Prisma model. Field table (Field / Prisma Type / Nullable / Description). Constraints and Indexes lines per entity. Cover all 5 models. For the bridge table, note that the same entity appears in `en/purchase-request/01-data-model.md` and cross-reference it.
- **Section 3 Relationships:** text or simple ASCII showing header→detail (1-many), header→comment (1-many), detail→comment (1-many), and the many-to-many PR↔PO via the bridge. Cite `@relation` directives from Prisma.
- **Section 4 Enums:** `enum_purchase_order_type` (note the `purchase_request` default value driving PR-conversion behaviour); `enum_purchase_order_doc_status` (all values with meaning of each).
- **Section 5 Divergences from carmen/docs:** compare Prisma against the single carmen/docs file. If consistent or carmen/docs lacks detail, write `No divergences detected against carmen/docs as of 2026-05-15.` Otherwise fill the table.
- **Section 6 References:** the two Prisma file paths (header callout) and `../carmen/docs/purchase-order-management/purchase-order-module.md`.

- [ ] **Step 4: Write `th/purchase-order/01-data-model.md`** as a section-by-section translation.

Frontmatter:
- `title: ใบสั่งซื้อ — แบบจำลองข้อมูล`
- `description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูล purchase-order (อิงจาก Prisma schema)`

Translate prose, table column headers (`Field` → `ฟิลด์`, `Nullable` → `ค่าว่างได้`, `Description` → `คำอธิบาย`; keep `Prisma Type` as-is). Keep model names, field names, enum values, file paths in English. Section 5 fallback becomes: `ไม่พบความแตกต่างจาก carmen/docs ณ วันที่ 2026-05-15.`

- [ ] **Step 5: Verify**

```bash
python3 .specs/verify_frontmatter.py en/purchase-order/01-data-model.md
python3 .specs/verify_frontmatter.py th/purchase-order/01-data-model.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/purchase-order/01-data-model.md th/purchase-order/01-data-model.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

Expected: two `OK:` lines + `OK: no placeholders`.

- [ ] **Step 6: Commit**

```bash
git add en/purchase-order/01-data-model.md th/purchase-order/01-data-model.md
git commit -m "docs(purchase-order): add 01-data-model (EN + TH)

Prisma-derived entities, fields, relationships, and enums
for the five PO models plus the PR↔PO bridge."
```

---

## Task 2: 02-business-rules (EN + TH)

**Files:**
- Create: `en/purchase-order/02-business-rules.md`
- Create: `th/purchase-order/02-business-rules.md`

**Sources:**
- `../carmen/docs/purchase-order-management/purchase-order-module.md`
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` (PR→PO conversion)
- `../carmen/docs/purchase-request-management/purchase-request-ba.md` (vendor allocation rules — relevant to PO creation)
- Sibling: `en/purchase-order/01-data-model.md` (entity references)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/purchase-order-management/purchase-order-module.md
cat ../carmen/docs/purchase-request-management/PR-Module-Structure.md
cat ../carmen/docs/purchase-request-management/purchase-request-ba.md
```

- [ ] **Step 2: Write `en/purchase-order/02-business-rules.md`** using template `.specs/templates/02-business-rules.md`:

Frontmatter:
- Title: `Purchase Order — Business Rules`
- Description: `Validation, calculation, authorization, posting, and three-way-match rules for purchase-order.`
- Tags: `purchase-order, business-rules, inventory, carmen-software`

Sections:
- **Section 1 Overview:** 1-2 paragraphs — scope (which rules apply, which entities).
- **Section 2 Validation Rules:** table with rule IDs `PO_VAL_001`–`PO_VAL_NNN`. Cover: required header fields (vendor, currency, type, delivery terms, payment terms, dates), line fields (product, quantity > 0, unit, unit price), at-submit checks (at least one line, valid dates, vendor active, currency matches across lines), amendment rules (only certain fields editable post-transmission). Aim for 10-16 rules.
- **Section 3 Calculation Rules:** line subtotal = qty × unit_price, line tax, line total, header subtotal, header tax (line-tax sum), header grand total, currency conversion (base = local × exchange rate), rounding (Prisma `Decimal(15, 5)`). One worked example in `฿`.
- **Section 4 Authorization Rules:** threshold matrix or per-role bullets. Cover: Purchaser creates and transmits POs, Procurement Manager high-value approval threshold, void / amend rights, segregation (Purchaser cannot also be Receiver, Finance separation).
- **Section 5 Posting Rules:** what happens on submit (status `draft` → `submitted`), on approve (`approved`), on transmission (`sent`), on GRN posting (`partially_received` or `fully_received`), on three-way match success (`completed`), on void (`voided`), on close (`closed`). Map to actual `enum_purchase_order_doc_status` values from Task 1.
- **Section 6 Cross-Module Rules:** PR→PO conversion (via bridge table), GRN creation against PO (downstream), Vendor pricelist deviation check on PO creation, AP integration on GRN+invoice match, Inventory integration on receipt. Reference `[[purchase-request]]`, `[[good-receive-note]]`, `[[vendor-pricelist]]`, `[[inventory]]`.
- **Section 7 References:** the three carmen/docs sources plus a backend module path pointer (look in `apps/`).

- [ ] **Step 3: Write `th/purchase-order/02-business-rules.md`** — translate prose + table column headers, keep rule IDs / Prisma names / enum values / status names / currency codes / slug values in English.

Frontmatter:
- `title: ใบสั่งซื้อ — กฎทางธุรกิจ`
- `description: กฎ validation, การคำนวณ, การอนุมัติ, การ post, และ three-way match สำหรับโมดูล purchase-order`

- [ ] **Step 4: Verify** (same three checks as Task 1)

```bash
python3 .specs/verify_frontmatter.py en/purchase-order/02-business-rules.md
python3 .specs/verify_frontmatter.py th/purchase-order/02-business-rules.md
grep -n '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/purchase-order/02-business-rules.md th/purchase-order/02-business-rules.md && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 5: Commit**

```bash
git add en/purchase-order/02-business-rules.md th/purchase-order/02-business-rules.md
git commit -m "docs(purchase-order): add 02-business-rules (EN + TH)

Validation, calculation, authorization, posting, three-way
match, and cross-module rules. Sources: carmen/docs PO file
plus PR cross-module docs (PR-Module-Structure, PR-BA)."
```

---

## Task 3: 03-user-flow overview (EN + TH)

**Files:**
- Create: `en/purchase-order/03-user-flow.md`
- Create: `th/purchase-order/03-user-flow.md`

**Sources:**
- `../carmen/docs/purchase-order-management/purchase-order-module.md`
- Sibling: `en/purchase-order/01-data-model.md` Section 4 (lifecycle enum values)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/purchase-order-management/purchase-order-module.md
grep -A 20 'enum_purchase_order_doc_status' en/purchase-order/01-data-model.md  # lifecycle enum reference
```

- [ ] **Step 2: Write `en/purchase-order/03-user-flow.md`**

```markdown
---
title: Purchase Order — User Flow
description: Document lifecycle and persona-specific flow files for purchase-order.
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — User Flow

## 1. Overview
<2-paragraph scope: PO is the procurement-commitment document; this page covers lifecycle states and points to per-persona files. The lifecycle in Section 2 is the global state machine; per-persona files describe each persona's path through it.>

## 2. Document Lifecycle
| From state | Action | To state | Allowed for | Pre-conditions |
| ---------- | ------ | -------- | ----------- | -------------- |
<8-12 rows covering enum_purchase_order_doc_status transitions. Examples:
- `(none)` → create → `draft` — by Purchaser
- `draft` → submit for approval → `submitted` — Purchaser; pre-condition: complete header + ≥1 line
- `submitted` → approve → `approved` — Procurement Manager (for high-value); pre-condition: threshold check
- `approved` → transmit → `sent` — Purchaser; pre-condition: vendor reachable
- `sent` → receive (partial) → `partially_received` — Receiver via GRN; pre-condition: GRN matches PO line
- `sent` / `partially_received` → receive (full) → `fully_received` — Receiver
- `fully_received` → match-invoice → `completed` — Finance; pre-condition: three-way match passes
- Any → void → `voided` — Procurement Manager / Sysadmin
- `fully_received` / `completed` → close → `closed` — Inventory Manager>

## 3. Persona Index
- [Purchaser](./03-user-flow-purchaser.md) — Creates POs (manually or from PR), validates pricing, transmits, manages amendments.
- [Procurement Manager](./03-user-flow-procurement-manager.md) — Oversight, high-value approval, vendor ranking, override authority.
- [Vendor](./03-user-flow-vendor.md) — External party (no system login); receives PO, acknowledges, fulfils, invoices.
- [Receiver](./03-user-flow-receiver.md) — Physically accepts goods, raises GRN against PO, triggers receipt-state transition.
- [Finance](./03-user-flow-finance.md) — Three-way match (PO ↔ GRN ↔ invoice), AP posting, currency/FX handling.
- [Audit / Config](./03-user-flow-audit-config.md) — Read-only audit (Auditor) + workflow / RBAC / integration configuration (Sysadmin).

## 4. Cross-Persona Handoffs
| From persona | Trigger | To persona | Document state at handoff |
| ------------ | ------- | ---------- | ------------------------- |
<6-9 rows. Examples:
- Purchaser → Procurement Manager — on submit for high-value approval — `submitted`
- Procurement Manager → Purchaser — on approval — `approved`
- Purchaser → Vendor — on transmission — `sent`
- Vendor → Receiver — on physical delivery — `sent` (system unchanged until GRN posts)
- Receiver → Purchaser/Inventory Manager — on partial receipt — `partially_received`
- Receiver → Finance — on full receipt + invoice arrival — `fully_received`
- Finance → (close) — on three-way match — `completed`
- Procurement Manager/Sysadmin → (terminal) — on void — `voided`>

## 5. References
- `../carmen/docs/purchase-order-management/purchase-order-module.md`
- Sibling: [01-data-model.md](./01-data-model.md) for the lifecycle enum
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 for posting/transition rules
```

- [ ] **Step 3: Write `th/purchase-order/03-user-flow.md`**

- `title: ใบสั่งซื้อ — เส้นทางผู้ใช้งาน`
- `description: วงจรเอกสารและไฟล์เส้นทางตาม persona สำหรับโมดูล purchase-order`
- Translate prose + table column headers. Keep enum values, status names, file paths, Prisma identifiers in English.

- [ ] **Step 4: Verify** (same three checks)

- [ ] **Step 5: Commit**

```bash
git add en/purchase-order/03-user-flow.md th/purchase-order/03-user-flow.md
git commit -m "docs(purchase-order): add 03-user-flow overview (EN + TH)

Lifecycle state machine, 6-persona index, and cross-persona
handoffs. Drill-down persona files come in subsequent commits."
```

---

## Tasks 4–9: 03-user-flow-<persona> (EN + TH), per persona

Each task implements one persona's user-flow file pair using the persona-file template from the PR spec Section 6.2.

**Files (one task per row):**

| Task | Persona slug | EN file | TH file |
|------|--------------|---------|---------|
| 4 | `purchaser` | `en/purchase-order/03-user-flow-purchaser.md` | `th/purchase-order/03-user-flow-purchaser.md` |
| 5 | `procurement-manager` | `en/purchase-order/03-user-flow-procurement-manager.md` | `th/purchase-order/03-user-flow-procurement-manager.md` |
| 6 | `vendor` | `en/purchase-order/03-user-flow-vendor.md` | `th/purchase-order/03-user-flow-vendor.md` |
| 7 | `receiver` | `en/purchase-order/03-user-flow-receiver.md` | `th/purchase-order/03-user-flow-receiver.md` |
| 8 | `finance` | `en/purchase-order/03-user-flow-finance.md` | `th/purchase-order/03-user-flow-finance.md` |
| 9 | `audit-config` | `en/purchase-order/03-user-flow-audit-config.md` | `th/purchase-order/03-user-flow-audit-config.md` |

**Sources for all 6:** the same PO carmen/docs file + the persona's responsibility text from `en/purchase-order/index.md` Section 4. Supplement from PR cross-module docs only when the topic is conversion-related.

**Persona-specific focus:**

| Persona | What to extract |
|---------|-----------------|
| `purchaser` | Create PO (manual or from PR conversion) → fill header (vendor, currency, terms, delivery, payment) → add lines (product, qty, unit, price, tax) → review → submit → on approval, transmit to vendor → manage amendments → handle vendor clarifications. |
| `procurement-manager` | Receive escalated high-value PO → review full context (vendor, amount, line composition) → approve / reject / send-back. Separate configurational surface: vendor ranking, Allocate Vendor rule tuning, override delete-in-draft. |
| `vendor` | External — no system login. Conceptual flow: receive transmitted PO → acknowledge (manual entry by Purchaser or vendor portal) → fulfil delivery → issue invoice. Each step's system effect when entered. Shorter file than other personas. |
| `receiver` | Receive goods physically against transmitted PO → open PO in receive screen → raise GRN line by line → enter received and accepted quantities → confirm. System triggers PO state advance (partial/full received) + inventory increment. Inventory Manager closes PO when receipt complete. |
| `finance` | Three-way match flow: invoice arrives → look up PO and matching GRN → run match algorithm → on success post AP liability and flip PO to `completed`; on failure flag discrepancy back to Purchaser. High-value PO sign-off pre-transmission. FX rate snapshot validation. |
| `audit-config` | Auditor: query PO activity log, drill into specific PO, follow PR→PO→GRN→invoice chain. Sysadmin: configure PO numbering, RBAC, status transitions, integration with vendor/pricelist/budget/inventory, conversion/grouping rules, document templates. |

### Task 4 detail (shape for Tasks 4–9)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen/docs/purchase-order-management/purchase-order-module.md
sed -n '/^## 4\. Roles/,/^## 5\./p' en/purchase-order/index.md
```

- [ ] **Step 2: Write the EN persona file** using this template (substitute persona slug + displays):

```markdown
---
title: Purchase Order — User Flow — <Persona display>
description: <Persona display>'s flow within the purchase-order module.
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, user-flow, <persona-slug>, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — User Flow — <Persona display>

## 1. Role in This Module
<1 paragraph: what this persona does in PO, where they sit in the chain, which document states they touch. Pulled from index.md Section 4 + persona-specific focus above.>

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
- `../carmen/docs/purchase-order-management/purchase-order-module.md`
- Cross-link to relevant sibling persona files where handoff occurs
```

For Task 4 (`purchaser`): `<Persona display>` = `Purchaser`, `<persona-slug>` = `purchaser`. Content uses the purchaser focus above.

- [ ] **Step 3: Write the TH persona file.** Title becomes `ใบสั่งซื้อ — เส้นทางผู้ใช้งาน — เจ้าหน้าที่จัดซื้อ (Purchaser)`. Translate prose, keep identifiers / status / paths in English. Internal cross-links to other TH files use the same relative paths (e.g. `./03-user-flow.md`).

- [ ] **Step 4: Verify** (same three checks)

- [ ] **Step 5: Commit**

```bash
git add en/purchase-order/03-user-flow-purchaser.md th/purchase-order/03-user-flow-purchaser.md
git commit -m "docs(purchase-order): add 03-user-flow-purchaser (EN + TH)

Purchaser's flow: create PO (manual or PR conversion),
validate pricing, transmit, manage amendments."
```

### Tasks 5–9 follow the same shape

For each, substitute persona slug + EN/TH displays from the persona table, focus content per the persona-specific focus column, and commit body summary.

TH display per persona (use as the title suffix):

| Slug | EN display | TH display (title suffix) |
|------|-----------|---------------------------|
| `procurement-manager` | `Procurement Manager` | `ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager)` |
| `vendor` | `Vendor` | `ผู้ขาย (Vendor)` |
| `receiver` | `Receiver` | `ผู้รับสินค้า (Receiver)` |
| `finance` | `Finance` | `ฝ่ายการเงิน (Finance)` |
| `audit-config` | `Audit / Config` | `ผู้ตรวจสอบและผู้ดูแลระบบ (Audit / Config)` |

Commit body summaries:
- Task 5: `High-value approval, vendor ranking, Allocate Vendor rule tuning, override authority.`
- Task 6: `External party (no system login); receives PO, acknowledges, fulfils, invoices. Actions documented conceptually since vendor responses are entered by Purchaser or via vendor portal.`
- Task 7: `Physically accepts goods, raises GRN against PO, triggers receipt state transition.`
- Task 8: `Three-way match (PO ↔ GRN ↔ invoice), AP posting, currency/FX handling.`
- Task 9: `Auditor (read-only audit log) and Sysadmin (PO numbering, RBAC, integration config).`

---

## Task 10: 04-test-scenarios overview (EN + TH)

**Files:**
- Create: `en/purchase-order/04-test-scenarios.md`
- Create: `th/purchase-order/04-test-scenarios.md`

**Sources:**
- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/403-po-approver-journey.spec.ts`
- Sibling: `en/purchase-order/03-user-flow.md` Section 4 (cross-persona handoffs)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen-inventory-frontend-e2e/tests/401-po.spec.ts
cat ../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts
cat ../carmen-inventory-frontend-e2e/tests/403-po-approver-journey.spec.ts
sed -n '/^## 4\. Cross-Persona/,/^## 5\./p' en/purchase-order/03-user-flow.md
```

- [ ] **Step 2: Write `en/purchase-order/04-test-scenarios.md`**

```markdown
---
title: Purchase Order — Test Scenarios
description: Test cases by persona, cross-persona scenarios, and Playwright mapping for purchase-order.
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Test Scenarios

## 1. Overview
<1-2 paragraphs covering personas + scope of testing.>

## 2. Personas in Scope
- **Purchaser**: <one-line>
- **Procurement Manager**: <one-line>
- **Vendor**: <one-line>
- **Receiver**: <one-line>
- **Finance**: <one-line>
- **Audit / Config**: <one-line>

## 3. Persona Test Files
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Procurement Manager scenarios](./04-test-scenarios-procurement-manager.md)
- [Vendor scenarios](./04-test-scenarios-vendor.md)
- [Receiver scenarios](./04-test-scenarios-receiver.md)
- [Finance scenarios](./04-test-scenarios-finance.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Cross-Persona / Handoff Scenarios
| # | Scenario | Personas in order | Pre-condition | Expected end state |
| - | -------- | ----------------- | ------------- | ------------------ |
<6-10 rows covering end-to-end paths. Examples:
- Full happy path: Purchaser creates PO → Procurement Manager approves (if high-value) → Vendor receives + acknowledges → Receiver posts GRN → Finance matches invoice → `completed`
- Partial receipt: Purchaser → Vendor → Receiver (partial) → another GRN later → `fully_received` → Finance → `completed`
- Three-way mismatch: Purchaser → Vendor → Receiver → Finance flags qty discrepancy → bounce-back to Purchaser
- High-value rejection: Purchaser → Procurement Manager rejects → terminal `voided`
- Amendment cycle: sent PO → Purchaser amends → re-sent to Vendor
- Void in flight: any state → Procurement Manager voids → `voided`>

## 5. E2E Test Mapping
<List 401-po.spec.ts, 402-po-purchaser-journey.spec.ts, 403-po-approver-journey.spec.ts entries with test names and which Section 4 scenarios they cover. Note no vendor / receiver / finance / audit-config dedicated specs — these personas' detail pages will mark "no dedicated E2E yet; see shared 401-po.spec.ts".>

## 6. References
- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/403-po-approver-journey.spec.ts`
- Sibling: [03-user-flow.md](./03-user-flow.md) Section 4
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 (three-way match rules)
```

- [ ] **Step 3: Write `th/purchase-order/04-test-scenarios.md`**

- `title: ใบสั่งซื้อ — กรณีทดสอบ`
- `description: กรณีทดสอบแยกตาม persona, กรณีข้าม persona, และการเชื่อมโยงกับ Playwright สำหรับโมดูล purchase-order`
- Translate prose + table column headers. Persona file links → siblings in same TH folder.

- [ ] **Step 4: Verify** (three checks)

- [ ] **Step 5: Commit**

```bash
git add en/purchase-order/04-test-scenarios.md th/purchase-order/04-test-scenarios.md
git commit -m "docs(purchase-order): add 04-test-scenarios overview (EN + TH)

Personas in scope, persona file index, cross-persona
handoff scenarios (including three-way match), and E2E
mapping to the 3 PO Playwright specs."
```

---

## Tasks 11–16: 04-test-scenarios-<persona> (EN + TH), per persona

Each task implements one persona's test-scenarios file pair using the persona test-scenarios template from the PR spec Section 6.4.

**Files (one task per row):**

| Task | Persona slug | EN file | TH file |
|------|--------------|---------|---------|
| 11 | `purchaser` | `en/purchase-order/04-test-scenarios-purchaser.md` | `th/purchase-order/04-test-scenarios-purchaser.md` |
| 12 | `procurement-manager` | `en/purchase-order/04-test-scenarios-procurement-manager.md` | `th/purchase-order/04-test-scenarios-procurement-manager.md` |
| 13 | `vendor` | `en/purchase-order/04-test-scenarios-vendor.md` | `th/purchase-order/04-test-scenarios-vendor.md` |
| 14 | `receiver` | `en/purchase-order/04-test-scenarios-receiver.md` | `th/purchase-order/04-test-scenarios-receiver.md` |
| 15 | `finance` | `en/purchase-order/04-test-scenarios-finance.md` | `th/purchase-order/04-test-scenarios-finance.md` |
| 16 | `audit-config` | `en/purchase-order/04-test-scenarios-audit-config.md` | `th/purchase-order/04-test-scenarios-audit-config.md` |

**Sources for all 6:** the 3 E2E specs + `purchase-order-module.md` + the persona's matching `03-user-flow-<persona>.md` file (for happy-path scenarios).

### Task 11 detail (shape for Tasks 11–16)

- [ ] **Step 1: Read sources**

```bash
cat ../carmen-inventory-frontend-e2e/tests/401-po.spec.ts
cat ../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts  # purchaser-specific
cat en/purchase-order/03-user-flow-purchaser.md
```

- [ ] **Step 2: Write the EN file** using this template:

```markdown
---
title: Purchase Order — Test Scenarios — <Persona display>
description: <Persona display>'s test cases (happy path, permission, validation, edge cases) for purchase-order.
published: true
date: 2026-05-15T10:00:00.000Z
tags: purchase-order, test-scenarios, <persona-slug>, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T10:00:00.000Z
---

# Purchase Order — Test Scenarios — <Persona display>

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
- E2E: relevant specs in `../carmen-inventory-frontend-e2e/tests/` (cite file paths)
```

Scenario ID prefixes: `PUR-`, `PM-`, `VND-`, `RCV-`, `FIN-`, `AUD-` (e.g. `PUR-HP-01` for Purchaser Happy Path #1). Aim for 5-10 happy-path, 4-8 permission, 6-10 validation, 3-7 edge per persona — except Vendor which is shorter (3-5 happy-path, "N/A — external; no in-system permission to verify" under Section 2, 3-5 validation around invoice/PO mismatch, 2-4 edge).

- [ ] **Step 3: Write the TH file.** Translate prose + table headers. Keep scenario IDs, rule IDs, identifiers, status names, file paths in English. Internal cross-links target TH siblings.

- [ ] **Step 4: Verify** (three checks)

- [ ] **Step 5: Commit**

```bash
git add en/purchase-order/04-test-scenarios-purchaser.md th/purchase-order/04-test-scenarios-purchaser.md
git commit -m "docs(purchase-order): add 04-test-scenarios-purchaser (EN + TH)

Purchaser test cases: PO creation (manual + PR conversion),
amendment, transmission, vendor-clarification handling."
```

### Tasks 12–16 follow the same shape

Substitute persona slug + EN/TH displays + commit body. Title TH suffixes per the table in Task 9.

Commit body summaries:
- Task 12: `Procurement Manager test cases: high-value approval, override, vendor ranking, rule tuning.`
- Task 13: `Vendor test cases: acknowledgement, fulfilment, invoice issuance. External party — permission section is N/A.`
- Task 14: `Receiver test cases: GRN creation against PO, partial / full receipt, qty discrepancy.`
- Task 15: `Finance test cases: three-way match, AP posting, FX handling, discrepancy bounce-back.`
- Task 16: `Audit / Config test cases: audit-log query, RBAC + workflow + integration configuration.`

---

## Task 17: EN index Section 7 + new TH index.md + push

**Files:**
- Modify: `en/purchase-order/index.md` (Section 7 + frontmatter `date`)
- Create: `th/purchase-order/index.md` (TH translation of EN landing page)

- [ ] **Step 1: Confirm all 32 sub-page files exist**

```bash
ls en/purchase-order/0*.md | wc -l   # expected: 16
ls th/purchase-order/0*.md | wc -l   # expected: 16
```

- [ ] **Step 2: Open `en/purchase-order/index.md` and locate Section 7**

```bash
sed -n '/^## 7\./,$p' en/purchase-order/index.md | head -10
```

- [ ] **Step 3: Replace Section 7 with**:

```markdown
## 7. Pages in This Module

- [01 — Data Model](./01-data-model.md) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](./02-business-rules.md) — Validation, calculation, authorization, posting, and three-way-match rules.
- [03 — User Flow](./03-user-flow.md) — Document lifecycle and persona index.
  - [Purchaser](./03-user-flow-purchaser.md)
  - [Procurement Manager](./03-user-flow-procurement-manager.md)
  - [Vendor](./03-user-flow-vendor.md)
  - [Receiver](./03-user-flow-receiver.md)
  - [Finance](./03-user-flow-finance.md)
  - [Audit / Config](./03-user-flow-audit-config.md)
- [04 — Test Scenarios](./04-test-scenarios.md) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Purchaser](./04-test-scenarios-purchaser.md)
  - [Procurement Manager](./04-test-scenarios-procurement-manager.md)
  - [Vendor](./04-test-scenarios-vendor.md)
  - [Receiver](./04-test-scenarios-receiver.md)
  - [Finance](./04-test-scenarios-finance.md)
  - [Audit / Config](./04-test-scenarios-audit-config.md)
```

- [ ] **Step 4: Update `en/purchase-order/index.md` frontmatter `date`**

Change `date` to `2026-05-15T10:00:00.000Z`. Leave `dateCreated` unchanged.

- [ ] **Step 5: Create `th/purchase-order/index.md`** — TH translation of `en/purchase-order/index.md`.

- Frontmatter: `title: ใบสั่งซื้อ (Purchase Order)`, Thai `description`, `date: 2026-05-15T10:00:00.000Z`, `dateCreated: 2026-05-15T10:00:00.000Z`, other frontmatter matches EN.
- Mirror all 7 sections of the EN file. Translate prose, table headers, role text. Keep Prisma identifiers, enum values, currency codes, sibling repo paths, cross-link slugs (`[[purchase-request]]`, `[[good-receive-note]]`, etc.) in English.
- Section 7 has the same shape as the EN one — relative paths point to TH siblings (same path strings as EN's Section 7 because each tree is self-contained).

- [ ] **Step 6: Verify everything parses**

```bash
python3 .specs/verify_frontmatter.py en/purchase-order/index.md
python3 .specs/verify_frontmatter.py th/purchase-order/index.md
for f in en/purchase-order/0*.md th/purchase-order/0*.md; do
  python3 .specs/verify_frontmatter.py "$f"
done
```

Expected: 34 `OK:` lines total (2 indices + 32 sub-pages).

- [ ] **Step 7: Cross-link slug audit**

```bash
grep -hRn '\[\[' --include='*.md' en/purchase-order/ th/purchase-order/ | grep -o '\[\[[^]]*\]\]' | sort -u
```

Expected: only valid module slugs (`inventory`, `costing`, `inventory-adjustment`, `good-receive-note`, `store-requisition`, `physical-count`, `spot-check`, `purchase-request`, `purchase-order`, `vendor-pricelist`, `product`, `recipe`).

- [ ] **Step 8: Placeholder audit**

```bash
grep -rn '<MODULE_\|<Term>\|<role>\|<other-module\|<Persona\|<EntityName\|<EnumName' en/purchase-order/ th/purchase-order/ && echo "FAIL: placeholders remain" || echo "OK: no placeholders"
```

- [ ] **Step 9: Commit and push**

```bash
git status
git add en/purchase-order/index.md th/purchase-order/index.md
git commit -m "docs(purchase-order): update EN index Section 7 + add TH index

EN Section 7 lists 16 sub-pages. New th/purchase-order/index.md
is a Thai translation of the EN landing page, mirroring all
7 sections and Section 7's ToC. Date field bumped to
2026-05-15T10:00:00.000Z; dateCreated unchanged."

git push origin main
```

Expected: push succeeds.
