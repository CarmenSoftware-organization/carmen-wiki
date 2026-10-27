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

| Group | Commit | Headline |
|---|---|---|
| New modules | 012dcbe | AI Providers, Dashboard Templates, Tenant Seed (10 pages) |
| Users/RBAC/config rename + content | 58faa40, 117aefb | platform→backstage keys/tables/labels; RBAC redesign; Google sign-in; Backstage Config cards; /login/callback + /403 |
| Clusters/BU/licenses | d73ed82 | Cluster + BU notes; cluster seats; BU form tabs; licenses deleted view + retired numbers; catalog 112/13/105/7 |
| Report templates/cronjobs/SQL/email/pools | 154ba06 | Export XML, dialog layout editor, versions, backup/import; SQL workbench role claim fixed; `POST /v1/emails` notification flow; worker job types |
| Read-through of rename-only pages | fea6150 | Application status/bypass/secret; tenant migrations permission gate + dashboard views; ~360 cites re-verified |

Nav (`scripts/nav-overrides.yaml`): Tenant Seeds, Dashboard Templates, new AI group; "Platform" group and labels → "Backstage". Inventory nav unchanged (new pages are sub-pages).
Checklist: 219 → 267 rows, 100%.
Wiki.js pushes: 15 pages had `description` > 255 chars (DB varchar(255)) and failed to push; shortened.

Code findings worth tickets: seat release/restore UI shown to `cluster.update` holders but backend refuses non-cluster-admins; `interface.pos.micros` seed replaced with no migration; `gl_run_due`/`pos_simphony_pull` missing from SPA CronJobType + DTO enum; skipped cron runs counted as retries; `GET report-templates/forms` no permission decorator; TenantSeed "Showing N of M" never shows; system-widget cache per-instance; `doc_version` optional on AI provider / dashboard template updates; e2e smoke specs still use `/platform/...` paths.
