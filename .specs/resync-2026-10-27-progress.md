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
