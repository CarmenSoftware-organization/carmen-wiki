# Inventory Wiki Re-sync — Progress Log (2026-06-17)

Branch: `docs/resync-inventory-2026-06-17`. Spec: `docs/superpowers/specs/2026-06-17-inventory-wiki-resync-design.md`.
Autonomous run (user asleep). Deliverable = commits on branch + this log. **No push / no PR** without explicit ask.

## Source change window
Since last sync **2026-06-11**: backend-v2 (330 commits), frontend-react (109), platform (7, deferred), carmen/docs (0).

## Dominant theme
`doc_version` optimistic-lock rollout (backend) + frontend carrying doc_version header+line. Already documented in most modules; verify enforcement wording and fill gaps.

## Module status
| Module | Status | Notes |
|--------|--------|-------|
| purchase-order | IN SYNC (no edit) | data-model already covers doc_version + 409 conflict; FE commits are bug fixes |
| physical-count | EDIT | add doc_version field (01-data-model) + optimistic-lock rule save/review/submit/desc-edit (02-business-rules). cf 684cd5da, cf249086 |
| spot-check | EDIT | add doc_version field to tb_spot_check entity table (overview already mentions locking). prisma confirms field |
| inventory | EDIT | (1) transaction.md: doc_version read-only in GET (append-only); cf 4cd73820. (2) 02-business-rules: valuation fix v_inventory_inventory_balance amount=Σ(qty×cost_per_unit); migration 063 |
| purchase-request | EDIT | doc_version on comment tables (01a-data-model-comments). cf 4ef95078 |
| vendor-pricelist | EDIT | doc_version on comment tables (01a-data-model-comments). cf 4ef95078. (exchange_rate/multi-tier = bug fixes, SKIP) |
| product | EDIT | optimistic-lock on product PATCH 409 (02-business-rules). cf e26c2439 |
| master-data | EDIT | optimistic-lock rule on vendor.md + location.md. cf 4a2c2b0d, 2647d56e |
| good-receive-note | EDIT | mobile draft-only GRN list filter (02-business-rules). cf 2b1509ce + helper 041a6ee8 |
| recipe, store-requisition, dashboard, reporting-audit, system-config, access-control, templates, inventory-adjustment, costing | IN SYNC | doc_version already documented or changes are bug fixes/infra; verified by analysis agents |

## RESULT (run complete 2026-06-17)
8 modules edited, EN+TH paired, 8 per-module commits on branch (+ spec commit). 22 files, +90/−30.
**Theme:** `doc_version` optimistic-lock rollout was already documented in most modules; filled the real gaps + 2 verified behavior changes:
1. physical-count — doc_version field + PHC_VAL_009 (save/review/submit/desc-edit, 409)
2. spot-check — doc_version field added to entity table
3. inventory — INV_CALC_013 valuation fix (signed qty×cost, migration 063) + txn doc_version (read-only GET)
4. purchase-request — doc_version on comment tables
5. vendor-pricelist — doc_version on comment tables
6. product — PRD_AUTH_013 optimistic lock on PATCH
7. master-data — optimistic lock on vendor.md + location.md
8. good-receive-note — mobile draft-only list filter (x-app-id → mobile)

**IN SYNC (no edit, verified):** purchase-order, recipe, store-requisition, dashboard, reporting-audit, system-config, access-control, templates, inventory-adjustment, costing.

**Deliberately SKIPPED (bug fixes aligning to already-documented behavior, not divergences):** PO from-price-list recompute/exchange_rate/submit-after-save; vendor-pricelist multi-tier label + foreign-currency exchange_rate; SR infinite-scroll resetKey.

## NEXT (awaiting user)
- Review branch `docs/resync-inventory-2026-06-17`; merge to main if approved. **Not pushed / no PR** (no explicit ask).
- **Platform book re-sync** (carmen-platform, 7 commits) — deferred, separate pass.
- Optional: render-check edited pages on dev Wiki.js.

## Decisions / conservatism rules
- Edit only where wiki demonstrably contradicts or omits documentable current behavior/data-model.
- Bug fixes that align code to already-documented behavior = NO doc change.
- No invented behavior. Flag ambiguity in this log instead of guessing.
- Every edit cites a source path:line in the commit body / this log.
- EN + TH always paired. Update `date` frontmatter; never touch `dateCreated`.
