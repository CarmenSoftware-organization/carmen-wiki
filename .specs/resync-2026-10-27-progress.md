# Re-sync 2026-10-27 — progress log

Owner said "update it" / "เริ่มเลย" (skip questions) on 2026-10-27. Defaults carried
over from the 2026-09-22 round, as Claude's call: both books, **EN only** (TH
later, as its own round), diff-based against the 2026-09-22 source HEADs, fix
claims in place with `file:line` citations, fabrication sweep, ~1 diff-untouched
page spot-checked per group, no screenshot recapture, one branch + PR per book,
Backstage (Platform) book first, push to dev Wiki.js before merge, **merge is the
owner's step**. Coverage checklists updated in the same PR.

## Baselines (source HEADs used by the 2026-09-22 round → target)

| Repo (current name) | Baseline | Target (origin/main 2026-10-27) | Commits |
|---|---|---|---|
| carmen-turborepo-backend | `ef4d6f08f` | `c9d788829` | 1,059 |
| carmen-frontend | `0713cbc9` | `391062b5` | 1,027 |
| carmen-backstage | `f1c69f1` | `8405788f` | 436 |
| carmen-turborepo-backend-bruno | `7f96637` | `5c98670` | 28 |
| carmen-frontend-e2e | `809d8e3` | `d795a25` | 37 |
| micro-report | `c9ebf77` | origin/main | 130 |
| micro-data | `7f21905` | `c9aa145` | 57 |
| micro-cronjobs | `5137b0a` | `c5464da` | 11 |

`carmen/docs` unchanged since 2026-04-27.

## Cross-cutting changes found in recon

- Gateway `apps/backend-gateway/src/platform/**` → `src/backstage/**` (files
  renamed `platform_*` → `backstage_*`), and every `@Controller('api-system/platform/…')`
  → `api-system/backstage/…` (20 controllers). 20 Backstage-book pages quote
  `api-system/platform`, 34 wiki pages cite `backend-gateway/src/platform`.
- New Backstage SPA modules with no wiki page: AI Providers, Dashboard Templates,
  Tenant Seed; new Backstage Config page dir; SSO `AuthCallback`; cluster/BU notes;
  cluster seats.

## Backstage book — branch `docs/resync-platform-2026-10-27`

(groups and results recorded below as they land)

## Inventory book — branch `docs/resync-inventory-2026-10-27` (worktree `../carmen-wiki-inventory-2026-10-27`)

10 implementer agents (one per module group) + 1 follow-up for system-config leftovers; coordinator verified headline claims against source before each commit.

| Group | Commit | Headline |
|---|---|---|
| Store Requisition + replenishment + wastage | 181359f | Stock check + posting inside the completion tx (2026-09-22 finding closed); active-period date rule; issue-stage guards; stage-action switches |
| Vendor Pricelist | db70a87 | Void/restore + admin hard delete; pre-tax add-VAT entry; price-compare MOQ suggestions; vendor rating/AP account |
| PO + Credit Note | 294a1b4 | Stage price hiding + action switches; CN period gate + stock-cover check; AP exists (GRN-based, no PO match) |
| PR + Templates | b4f654a | Hidden prices, stage actions, row visibility keys, Ask AI; PR template line-delete fix; send-back never rewrites pr_status |
| Master Data + Product | 18071e6, a95a2fe | Account mapping real (new page); COA create finding closed; cost center screens; vendor form fields; ingredient conversion; last-cost base currency |
| Recipe / Operation Plan | 44ffab9 | Ingredients persisted + costed; backend recipe permissions; new Sales Consumption + Import POS pages |
| System Config + Access Control | e650164, ca62838 | Workflow stage rail + action switches (`stage_actions` in gateway serializers); period status via period-end only; running-code engine; OAuth email; Google sign-in; new Ask AI + Interface pages; user-locations endpoint never registered |
| Inventory / IA / PC / Spot Check | b94cfb0 | Physical-count submit now posts EOP-IN/OUT (2026-09-22 finding reversed); on-hand from cost layers; average_per_location close |
| Dashboard / Reporting / GL | 0e2b64c | Still no inventory→GL posting (re-verified); AP invoice from GRN (new page); BU widgets + Backstage templates |
| GRN + Costing | e256ee3 | FOC-only GRN now moves stock (fc03b5718); saved GRN editable with stock lock; AP freeze; FIFO receipt order; average_per_location |

Checklist: 313 → 381 rows, 326 Done / 54 Partial / 1 Not yet, 86%.

Code findings worth tickets (documented on pages, not fixed): role/permission + app-config controllers still KeycloakGuard-only; `approve` skips PR verify rules; `guardHiddenPrices` not on reject/review/submit; PO `canSendEmail` ignores hidden prices; SR `buildViewScope` returns no filter with no view key; `approved ≤ requested` unenforced; COA form toggles not in DTO; COA delete guard reads absent `is_used`; POS explosion ignores `deduct_from_stock`; recipe in-use guard ignores `tb_pos_item.recipe_id`; RFQ `has_submitted` overstates; JV UI statuses `submitted/voided` vs backend `in_review/void`; count surplus with no cost priced ฿0; `hasMovementInOpenPeriod` has no caller; `doc_version` guard skipped when version omitted; e2e 401/402 still expect "Send to Vendor", 159-pl expects "Delete".

Not done (by decision): TH mirrors; screenshots; e2e case mirroring.
