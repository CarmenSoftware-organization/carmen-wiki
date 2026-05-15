# Design: Purchase Order Sub-Pages

**Date:** 2026-05-15
**Status:** Approved (user)
**Scope:** Sub-page implementation for the `purchase-order/` module
**Predecessor specs:**
- `.specs/2026-05-15-sub-page-templates-design.md` — defines the four sub-page types
- `.specs/2026-05-15-purchase-request-sub-pages-design.md` — the PR reference module (this spec follows the same pattern)

This is the **second per-module implementation** of the sub-page blueprint. Patterns established in the PR module (bilingual EN+TH, persona-axis page split, Prisma-as-source-of-truth for data-model) apply unchanged. Differences from PR are listed in Section 2.

---

## 1. Goal

Produce a complete bilingual (EN canonical + TH translation) set of sub-pages for the `purchase-order` module in `en/purchase-order/` and `th/purchase-order/`. Each sub-page covers a sliver of what developers and testers need to know to build or test the PO module. A `th/purchase-order/index.md` is also created so the TH locale tree has a navigable module landing page.

## 2. Differences from PR Module

| Concern | PR module | PO module (this spec) |
|---------|-----------|-----------------------|
| Persona groups | 5 (requestor, approver, purchaser, procurement-manager, audit-config) | **6** (purchaser, procurement-manager, vendor, receiver, finance, audit-config) |
| Page concepts | 14 (2 content + 2 overview + 5×2 persona) | **16** (2 content + 2 overview + 6×2 persona) |
| Bilingual sub-page files | 28 | **32** |
| carmen/docs source files | 18 | **1** (`purchase-order-module.md`) |
| E2E specs available | 4 | **3** (`401-po.spec.ts`, `402-po-purchaser-journey.spec.ts`, `403-po-approver-journey.spec.ts`) |
| Vendor persona | not applicable | **external party** (no system login) — actions documented conceptually since they drive state transitions |

The thin carmen/docs source means sub-page content draws more heavily from Prisma + the E2E test specs + the existing `en/purchase-order/index.md` (created in the module-folder-structure round, with substantial business framing). When the single carmen/docs file is insufficient, supplement from PR module sources (purchase-request-ba.md, PR-Module-Structure.md) where they describe cross-module PR→PO flow.

## 3. Persona Groups

| Slug | Source personas in index.md Section 4 | EN display | TH display | Scope |
|------|---------------------------------------|-----------|-----------|-------|
| `purchaser` | Procurement Officer / Purchaser | Purchaser | เจ้าหน้าที่จัดซื้อ (Purchaser) | Creates PO (manually or by PR conversion), validates pricing, sets delivery/payment terms, transmits to vendor, manages amendments, voids/closes. |
| `procurement-manager` | Procurement Manager | Procurement Manager | ผู้จัดการฝ่ายจัดซื้อ (Procurement Manager) | Oversight, high-value PO approval, vendor ranking, conversion/grouping rule tuning, override authority (including delete-in-draft). |
| `vendor` | Vendor | Vendor | ผู้ขาย (Vendor) | External party (no system login). Receives PO, acknowledges, fulfils delivery, issues invoice. Actions documented as conceptual triggers; system entry is by Purchaser or vendor portal. |
| `receiver` | Receiver / Store Keeper + Inventory Manager | Receiver | ผู้รับสินค้า (Receiver) | Downstream — physically accepts goods, raises GRN against PO, validates received/accepted quantities, triggers inventory increment and PO partial-/fully-received transition. Inventory Manager closes POs once receipt complete. |
| `finance` | Finance Officer / AP + Finance Manager | Finance | ฝ่ายการเงิน (Finance) | Three-way match (PO ↔ GRN ↔ invoice), AP posting, currency/FX handling, high-value PO sign-off, discrepancy reporting back to procurement. |
| `audit-config` | Auditor + System Administrator | Audit / Config | ผู้ตรวจสอบและผู้ดูแลระบบ (Audit / Config) | Auditor (read-only audit trail across PR/PO/GRN/invoice). Sysadmin (PO numbering, status transitions, RBAC, integration config, document templates, conversion/grouping rules). |

## 4. Sources

### 4.1 Primary — Prisma (source of truth for `01-data-model`)

`../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`:
- Models: `tb_purchase_order` (line 1818), `tb_purchase_order_comment` (1893), `tb_purchase_order_detail` (1927), `tb_purchase_order_detail_comment` (2041), `tb_purchase_order_detail_tb_purchase_request_detail` bridge (2075)
- Enums: `enum_purchase_order_type` (150), `enum_purchase_order_doc_status` (235)

### 4.2 Secondary — carmen/docs

- `../carmen/docs/purchase-order-management/purchase-order-module.md` (the only file in that folder)

Where the single carmen/docs file is thin, supplement from:
- `../carmen/docs/purchase-request-management/PR-Module-Structure.md` (cross-module PR→PO flow)
- `../carmen/docs/purchase-request-management/purchase-request-ba.md` (vendor allocation, conversion rules)

### 4.3 E2E — for `04-test-scenarios`

- `../carmen-inventory-frontend-e2e/tests/401-po.spec.ts` (shared/general PO specs)
- `../carmen-inventory-frontend-e2e/tests/402-po-purchaser-journey.spec.ts`
- `../carmen-inventory-frontend-e2e/tests/403-po-approver-journey.spec.ts`

No vendor / receiver / finance / audit-config E2E specs identified — those persona test-scenarios files note "No dedicated E2E spec yet" and point at the shared `401-po.spec.ts` plus relevant fixture/role tests.

## 5. File List (32 new sub-page files + 1 new TH index + 1 EN index update)

```
en/purchase-order/
├── index.md                                          (existing — Section 7 updated)
├── 01-data-model.md                                  (NEW)
├── 02-business-rules.md                              (NEW)
├── 03-user-flow.md                                   (NEW, overview)
├── 03-user-flow-purchaser.md                         (NEW)
├── 03-user-flow-procurement-manager.md               (NEW)
├── 03-user-flow-vendor.md                            (NEW)
├── 03-user-flow-receiver.md                          (NEW)
├── 03-user-flow-finance.md                           (NEW)
├── 03-user-flow-audit-config.md                      (NEW)
├── 04-test-scenarios.md                              (NEW, overview)
├── 04-test-scenarios-purchaser.md                    (NEW)
├── 04-test-scenarios-procurement-manager.md          (NEW)
├── 04-test-scenarios-vendor.md                       (NEW)
├── 04-test-scenarios-receiver.md                     (NEW)
├── 04-test-scenarios-finance.md                      (NEW)
└── 04-test-scenarios-audit-config.md                 (NEW)

th/purchase-order/
├── index.md                                          (NEW — TH translation of EN landing)
├── 01-data-model.md                                  (NEW)
├── 02-business-rules.md                              (NEW)
├── 03-user-flow.md                                   (NEW, overview)
├── 03-user-flow-purchaser.md                         (NEW)
├── 03-user-flow-procurement-manager.md               (NEW)
├── 03-user-flow-vendor.md                            (NEW)
├── 03-user-flow-receiver.md                          (NEW)
├── 03-user-flow-finance.md                           (NEW)
├── 03-user-flow-audit-config.md                      (NEW)
├── 04-test-scenarios.md                              (NEW, overview)
├── 04-test-scenarios-purchaser.md                    (NEW)
├── 04-test-scenarios-procurement-manager.md          (NEW)
├── 04-test-scenarios-vendor.md                       (NEW)
├── 04-test-scenarios-receiver.md                     (NEW)
├── 04-test-scenarios-finance.md                      (NEW)
└── 04-test-scenarios-audit-config.md                 (NEW)
```

= 32 sub-page files + 1 new TH index + 1 EN index update.

## 6. Templates

Use the four canonical templates from `.specs/templates/` verbatim, plus the persona-axis variants defined in the PR module spec (Section 6.1 — overview, 6.2 — persona file, 6.3 — test-scenarios overview, 6.4 — test-scenarios persona file). Substitutions per module/persona below.

### 6.1 Module-level substitutions

| Placeholder | EN value | TH value |
|-------------|----------|----------|
| `<Module>` | `Purchase Order` | `ใบสั่งซื้อ (Purchase Order)` |
| `<module-slug>` | `purchase-order` | `purchase-order` |

### 6.2 Frontmatter conventions

- Both `date` and `dateCreated`: `2026-05-15T10:00:00.000Z` for all new files in this round.
- `tags` for content-axis pages: `purchase-order, <page-type>, inventory, carmen-software`
- `tags` for persona pages: `purchase-order, <page-type>, <persona-slug>, inventory, carmen-software`

### 6.3 Section 7 update for `en/purchase-order/index.md`

Same shape as PR but with PO sub-pages and (because the wiki uses top-level locale split) no inline `[TH]` markers:

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

`th/purchase-order/index.md` Section 7 mirrors this with the same relative paths (siblings of the same TH file).

## 7. Vendor Persona Special Considerations

Unlike all other personas in the PR/PO scope, **Vendor has no system login.** Their actions are documented for completeness (because vendor responses drive PO state — acknowledge, fulfil, invoice) but the "flow" is conceptual:

- `03-user-flow-vendor.md` Section 2 (Entry Point and Primary Flow) describes:
  - Entry point: receives transmitted PO (email PDF / vendor portal if available)
  - Primary flow: what vendor is expected to do, with each action's system effect when entered (typically by Purchaser on receipt of vendor reply)
- `04-test-scenarios-vendor.md` covers:
  - Happy path: vendor acknowledges, partial-ships, full-ships, invoices on schedule
  - Permission: N/A or "external; no in-system permission to verify"
  - Validation: invoice received before PO sent (rejected); invoice for non-existent PO (rejected); over-invoicing against received quantity (flagged for three-way match)
  - Edge cases: vendor declines after acknowledgement; vendor goes out of business mid-PO; vendor confirms wrong quantity

The vendor file is shorter than other persona files — that's fine. Quality over volume.

## 8. Three-Way Match — Cross-Persona Concern

The PO module's distinctive cross-persona concern is the **three-way match** (PO ↔ GRN ↔ invoice). This appears across multiple sub-pages:

- `02-business-rules.md` Section 5 (Posting) and Section 6 (Cross-Module): match logic and the AP-posting trigger.
- `03-user-flow-purchaser.md`: handoff to Finance after GRN posted.
- `03-user-flow-receiver.md`: GRN creation against the PO (this triggers the match).
- `03-user-flow-finance.md`: invoice matching, AP posting on success, discrepancy flagging on failure.
- `04-test-scenarios-finance.md`: dedicated scenarios for clean match, qty discrepancy, price discrepancy, currency mismatch, partial receipt against open PO.

Don't duplicate the rule logic — write it once (`02-business-rules.md`) and cross-reference from the persona files.

## 9. Out of Scope

- **Other modules** — only `purchase-order/` is implemented in this round.
- **Vendor portal frontend / API contracts** — that's a separate sibling system not covered in this wiki.
- **GRN module sub-pages** — `[[good-receive-note]]` is cross-linked in `03-user-flow-receiver.md` (since GRN creation is downstream from PO), but GRN's own sub-pages are a future per-module plan.
- **Updating `.specs/templates/`** — the persona-file split pattern was finalized through PR. If validated again through PO, templates can be regenerated in a follow-up.
- **Retrofitting other modules' `index.md` to TH** — only `purchase-order` gets its TH index in this round.

## 10. Implementation Notes (for the plan)

1. **Order:** Tasks 1-17 produce the 16 page concepts (one task per concept, each commits its EN+TH pair). Task 17 updates the EN index Section 7 and creates the TH index.
2. **Synthesis discipline:** every sub-page grounded in the listed sources. When the thin carmen/docs file lacks coverage of a topic, mark it explicitly in the page rather than inventing rules.
3. **Persona consistency:** the 6 group slugs are fixed. `tags` include the persona slug for persona-axis files. Both 03 and 04 persona files share the same 6 slugs.
4. **Cross-link integrity:** the EN file under `en/purchase-order/` and the TH file under `th/purchase-order/` use the SAME relative paths (e.g. `./01-data-model.md`) because each language tree is self-contained. Cross-module `[[slug]]` references resolve within the current locale tree per Wiki.js.
5. **Translation discipline:**
   - EN is source of truth; write EN first, then translate.
   - Section structure, numbering, table row counts identical.
   - Keep in English: code identifiers (Prisma model/field names, enum values, rule IDs), file paths, slug values.
   - Translate prose, table column headers, descriptions.
6. **Vendor file is shorter** than other persona files — that's expected.
7. **Verifier:** run `.specs/verify_frontmatter.py` on every new file. All 33 new files plus the updated EN index must pass.
8. **One commit per EN+TH pair.** The two TH index + EN index Section 7 changes can be a single combined commit at the end (Task 17).

## 11. Open Questions

None at design time.
