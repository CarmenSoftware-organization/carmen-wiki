# carmen/docs drift register — 2026-09-22

`../carmen/docs/` has had **no commits since 2026-04-27** (`56fa3432`). Per the wiki's
own rule (implementation beats concept docs), the Inventory book re-sync of
2026-09-22 overwrote every claim below with what the source repos do at HEAD
(`carmen-turborepo-backend-v2` `ef4d6f08f`, `carmen-inventory-frontend-react`
`0713cbc9`). This file records what the concept docs still say so someone can
fix them at source; the wiki itself does not cite them as current truth.

Owner decision 2026-09-22 (Q11 b): record here, never edit `carmen/docs`.

| carmen/docs path | Stale claim | What HEAD does | Wiki page that corrects it |
|---|---|---|---|
| `app/inventory-management/inventory-transactions/BR-inventory-transactions.md` (lines 21, 31, 143, 162, 214) | Inventory transactions post automatically to the GL (variance, return postings) | No inventory→GL code path exists: `grep -rn -E "gl[-_]posting\|gl[-_]jv\|tb_gl_" apps/micro-business/src/{inventory,procurement}` → 0 hits; the only JV sources written today are `manual`, `reversal`, `closing`, template | [GL posting](/en/inventory/general-ledger/gl-posting) §2 |
| `inventory-management/period-end-process.md` (lines 135–136) | Period end includes "GL posting verification" and "period end journal entries" | Inventory period-end reads/writes `tb_inventory_period*` only (`period-end.close-transaction.helper.ts:80,195,210`); `tb_gl_period` is a separate 13-period calendar with no FK to it | [GL posting](/en/inventory/general-ledger/gl-posting) §3, [Period End](/en/inventory/inventory/period-end) |
| `store-requisitions/SR-API-JournalEntry-Endpoints.md` | SR journal-entry endpoints | No such endpoints exist in the gateway or Bruno | [Store Requisition](/en/inventory/store-requisition) |
