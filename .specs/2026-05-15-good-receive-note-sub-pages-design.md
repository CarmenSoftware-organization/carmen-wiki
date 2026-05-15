# Design: Good Receive Note (GRN) Sub-Pages

**Date:** 2026-05-15
**Status:** Approved (user)
**Scope:** Sub-page implementation for the `good-receive-note/` module — **EN only this round**
**Predecessor specs:**
- `.specs/2026-05-15-sub-page-templates-design.md` — defines the four sub-page types
- `.specs/2026-05-15-purchase-request-sub-pages-design.md` — PR reference module
- `.specs/2026-05-15-purchase-order-sub-pages-design.md` — PO reference module

Third per-module implementation. Patterns established in PR/PO apply unchanged. Two important departures from those rounds, listed in Section 2.

---

## 1. Goal

Produce a complete set of EN sub-pages for the `good-receive-note` module in `en/good-receive-note/`. TH translations are explicitly deferred to a later round. Developers and testers building or testing GRN features get four sub-pages: data model, business rules, user flow (with per-persona drill-downs), and test scenarios (with per-persona drill-downs).

## 2. Departures from PR/PO Pattern

| Concern | PR (round 1) | PO (round 2) | **GRN (this round)** |
|---------|--------------|--------------|----------------------|
| Languages produced | EN + TH | EN + TH | **EN only** |
| TH index translation | new TH index | new TH index | **none — TH deferred** |
| Persona groups | 5 | 6 | **4** (smaller, more collapsed) |
| Page concepts | 14 | 16 | **12** (4 main + 4×2 persona) |
| Total new sub-pages | 28 (14×2) | 32 (16×2) | **12 (EN only)** |
| carmen/docs source files | 18 | 1 | **17** (richest source so far) |
| E2E specs | 4 | 3 | **1** (`501-grn.spec.ts`) |

The "EN only this round" decision came from user feedback ("ยังไม่ต้องทำภาษาไทย" — don't do Thai yet). TH can be added as a separate effort later by translating each EN file. This pattern can also apply to the remaining 9 modules to clear the EN backlog before tackling TH.

## 3. Persona Groups (4 groups)

Collapsed from the 6 personas in `en/good-receive-note/index.md` Section 4:

| Slug | Source personas in index.md | EN display | Scope in this module |
|------|-----------------------------|-----------|----------------------|
| `receiver` | Store Keeper / Receiving Clerk + Store Manager / Inventory Manager | Receiver | Creates GRN in `Received` (Draft) status at the dock — counts, inspects against PO and delivery note, attaches packing slips and quality evidence, records lot numbers and expiry dates, documents discrepancies. Store/Inventory Manager reconciles, oversees lot/batch + location assignment, commits individual GRNs or runs batch commits at end-of-shift / period. |
| `purchaser` | Purchaser / Procurement Officer + Department Manager | Purchaser | Owns the upstream PO that the GRN matches, reviews receiving information for the POs they raised, investigates vendor performance issues (late / short / damaged / wrong item), coordinates vendor resolution. Department Manager reviews GRNs hitting their cost-centre, validates received goods match what was ordered, monitors price variance against the vendor pricelist. |
| `finance` | Finance Team / AP Clerk | Finance | Verifies GRN against vendor invoice (three-way match), validates extra-cost allocation and tax treatment, adjusts and finalises GRN entries before AP posting, reconciles inventory sub-ledger against the GL, signs off on receipt activity at period close. |
| `audit-config` | System Administrator | Audit / Config | Maintains lot-number generation format, configures user permissions and approval thresholds, manages tax codes, currency rates, reason codes for cancellations and rejections, oversees integration with PO / Inventory / Finance / Vendor modules. (Auditor is implicit — read-only audit-trail scenarios are documented under audit-config persona.) |

The combined `receiver` group reflects two roles working the same flow (the Store Keeper raises, the Inventory Manager commits) and keeps file count manageable. The Auditor role is folded into `audit-config` because it isn't listed as a separate persona in GRN's index.md — read-only audit-trail concerns are still covered under `audit-config`.

## 4. Sources

### 4.1 Primary — Prisma (source of truth for `01-data-model`)

`../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`:
- Models: `tb_good_received_note` (line 804), `tb_good_received_note_comment` (886), `tb_good_received_note_detail` (920), `tb_good_received_note_detail_comment` (949), `tb_good_received_note_detail_item` (983)
- Enums: `enum_good_received_note_status` (102), `enum_good_received_note_type` (145)
- Relations: `tb_purchase_order` and `tb_purchase_order_detail` (upstream), `tb_product` (line content), `tb_vendor` (header)

### 4.2 Secondary — carmen/docs (7 of 17 files in scope)

| Sub-page | carmen/docs files |
|----------|-------------------|
| `01-data-model.md` | `GRN-Technical-Specification.md`, `grn-master-prd.md` (cross-check vs Prisma) |
| `02-business-rules.md` | `GRN-Technical-Specification.md`, `grn-master-prd.md`, `grn-create-process-doc.md` |
| `03-user-flow.md` (overview + persona files) | `GRN-User-Experience.md`, `GRN-User-Flow-Diagram.md`, `GRN-Overview.md`, `grn-master-prd.md` |
| `04-test-scenarios.md` (overview + persona files) | Cross-reference 02-business-rules for negative tests; E2E spec (Section 4.3) for happy-path mapping |

**Out of scope (10 files):** `GRN-API-Endpoints*` (7 files — API contract specs, out of scope for user manual), `GRN-API-Overview.md`, `GRN-Component-Specifications.md` (UI internals), `README.md`, `consolidate-docs.sh` (script).

### 4.3 E2E — for `04-test-scenarios`

- `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` (only file — happy-path + shared fixtures)

No persona-specific E2E specs exist yet. Per-persona test files will note "no dedicated E2E spec yet — see shared `501-grn.spec.ts`".

## 5. File List (12 new sub-page files + 1 EN index.md update)

```
en/good-receive-note/
├── index.md                                         (existing — Section 7 updated)
├── 01-data-model.md                                 (NEW)
├── 02-business-rules.md                             (NEW)
├── 03-user-flow.md                                  (NEW, overview)
├── 03-user-flow-receiver.md                         (NEW)
├── 03-user-flow-purchaser.md                        (NEW)
├── 03-user-flow-finance.md                          (NEW)
├── 03-user-flow-audit-config.md                     (NEW)
├── 04-test-scenarios.md                             (NEW, overview)
├── 04-test-scenarios-receiver.md                    (NEW)
├── 04-test-scenarios-purchaser.md                   (NEW)
├── 04-test-scenarios-finance.md                     (NEW)
└── 04-test-scenarios-audit-config.md                (NEW)
```

= 12 sub-page files + 1 EN index update. **No `th/good-receive-note/` directory is created in this round.**

## 6. Templates

Use the four canonical templates from `.specs/templates/` and the persona-axis variants defined in the PR module spec (Section 6.1 — user-flow overview, 6.2 — user-flow persona file, 6.3 — test-scenarios overview, 6.4 — test-scenarios persona file). Substitutions per module/persona below.

### 6.1 Module-level substitutions

| Placeholder | EN value |
|-------------|----------|
| `<Module>` | `Good Receive Note (GRN)` |
| `<module-slug>` | `good-receive-note` |

### 6.2 Frontmatter conventions

- Both `date` and `dateCreated`: `2026-05-15T11:00:00.000Z` for every new file.
- `tags` for content-axis pages: `good-receive-note, <page-type>, inventory, carmen-software`
- `tags` for persona pages: `good-receive-note, <page-type>, <persona-slug>, inventory, carmen-software`

### 6.3 Section 7 update for `en/good-receive-note/index.md`

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

## 7. GRN-Specific Concerns

Some GRN concerns are distinctive vs PR/PO and deserve emphasis in the sub-pages:

- **Lot / batch tracking** — the `tb_good_received_note_detail_item` entity records lot numbers, expiry dates, and serial numbers per received line. This is a GRN-specific concern (PR/PO don't track lot at line level). Covered in `01-data-model` Section 2 + `02-business-rules` Section 3 (lot generation) + `03-user-flow-receiver` (capture at receipt).
- **Extra-cost allocation** — freight, customs, duties allocated across received lines proportionally. Covered in `02-business-rules` Section 3 (calculation) and `03-user-flow-finance` (allocation decision).
- **Three-way match anchor** — GRN is the central document in the PO ↔ GRN ↔ invoice three-way match. Covered in `02-business-rules` Section 5 (posting) and `03-user-flow-finance` + `04-test-scenarios-finance`.
- **Quality hold / partial acceptance** — `accepted_qty` may be less than `received_qty` when quality issues found. Covered in `02-business-rules` Section 2 + `03-user-flow-receiver`.
- **Batch commit at end-of-shift / period** — Inventory Manager may commit multiple draft GRNs in batch. Covered in `03-user-flow-receiver` Section 3 (decision branches).
- **Variance posting back upstream** — short/over/wrong receipts feed back to `[[purchase-order]]` for vendor performance tracking. Covered in `03-user-flow-purchaser` + cross-persona scenarios.

## 8. Out of Scope

- **TH translations** — explicitly deferred. Can be added in a later round by translating each EN file in this module.
- **Other modules** — only `good-receive-note/` is implemented in this round.
- **The 10 unread carmen/docs files** for GRN (API endpoints, component specs, etc.) — not needed for developer/tester user-manual content. Can be folded in later if specific pages need them.
- **Vendor portal / vendor performance dashboards** — separate feature surface beyond GRN sub-pages.
- **Inventory sub-ledger reconciliation details** — covered at the conceptual level in `03-user-flow-finance`, but the full reconciliation procedure is an `[[inventory]]` concern.
- **Backfilling carmen/docs to match Prisma** — record divergences in `01-data-model` Section 5 but do not modify carmen/docs.

## 9. Implementation Notes (for the plan)

1. **Order:** Tasks 1-13 produce the 12 page concepts (one task per concept, each commits its EN file). Task 13 updates EN index Section 7. (No TH index task this round.)
2. **Synthesis discipline:** every sub-page grounded in the listed sources. The richer carmen/docs source (17 files) means fewer placeholders — exploit it.
3. **Persona consistency:** the 4 group slugs are fixed: `receiver`, `purchaser`, `finance`, `audit-config`. Both 03 and 04 persona files use the same slugs. Frontmatter `tags` include the persona slug.
4. **Cross-link integrity:** any new `[[slug]]` reference must resolve to one of the 12 valid module slugs.
5. **Verifier:** run `.specs/verify_frontmatter.py` on every new file. All 12 new files plus the updated EN index must pass.
6. **Commit granularity:** one commit per page concept (12 concepts = 12 commits + 1 final commit for the index update).
7. **No TH dispatched at all this round.** Do not create files under `th/good-receive-note/`. Do not produce TH translations inline. TH is a separate effort.

## 10. Open Questions

None at design time.
