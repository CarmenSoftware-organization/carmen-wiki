---
title: General Ledger
description: GL subsystem (backend + Bruno + cron only, no UI) documented only where it touches inventory. Today nothing in inventory posts to the ledger; GL master, budgets, JV templates and reports are a deliberate gap.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: general-ledger, inventory, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# General Ledger

> **At a Glance**
> **Module purpose:** A journal-voucher ledger (`tb_gl_jv_header` / `tb_gl_jv_detail` → `tb_gl_balance`) that arrived in the backend 2026-09-09..15 with **no frontend** — the React `routes/accounting` tree is a hard-coded mock &nbsp;·&nbsp; **Wiki scope:** documented **only where it touches inventory**; GL master data, budgets, JV templates and GL reports are an intentional gap (§ 1.1) &nbsp;·&nbsp; **Inventory→GL today:** **none** — no GRN, stock-in/out, credit note, store requisition, physical count, cost layer or inventory period-end writes a voucher (see [gl-posting](/en/inventory/general-ledger/gl-posting) § 2) &nbsp;·&nbsp; **Key entities/tables:** `tb_gl_jv_header`, `tb_gl_jv_detail`, `tb_gl_balance`, `tb_gl_period` (a separate calendar from `tb_inventory_period`) &nbsp;·&nbsp; **Sub-pages:** 1

## 1. Overview

The General Ledger is a new backend subsystem under `apps/micro-business/src/gl/` (eight NestJS modules) with gateway routes under `api/:bu_code/gl-*` and `api/config/:bu_code/gl-*`, four tenant migrations, and one scheduled job in `micro-cronjobs`. It is a general-purpose accounting ledger — chart of accounts, cost centers, 13-period fiscal calendar, journal vouchers with a review workflow, balances, budgets, recurring/allocation/amortize templates, trial balance.

**This wiki is an inventory ERP manual, so the ledger is documented only at the seam with inventory** (owner decision 2026-09-22). That seam is currently *empty*: as of backend `ef4d6f08f` (2026-09-22) there is no code path from any inventory or procurement document into `tb_gl_jv_header`, and the `enum_gl_jv_source` members `inventory`, `ap`, `ar`, `asset` and `interface` are declared but never written. The one sub-page, [gl-posting](/en/inventory/general-ledger/gl-posting), records that finding with the greps that established it, and documents the two things a developer or tester *will* run into from the inventory side: how a voucher reaches `tb_gl_balance` (post / void / reverse / year-end) and what the `gl_run_due` cron actually does.

### 1.1 Intentionally not documented

Everything below exists in code and is **deliberately left out of this wiki**. The table is here so that a developer who greps a GL identifier lands on this page and knows it is a chosen gap, not an omission. Consult the source paths directly.

| Area | Backend (`apps/micro-business/src/`) | Gateway route (`apps/backend-gateway/src/`) | Bruno folder (`collections/carmen-inventory/_uncategorized/`) | Migration | Permission / licence key | Enums |
|---|---|---|---|---|---|---|
| Chart of accounts (`tb_chart_of_accounts`; renamed from account code, extended with `category`, `is_require_cost_center`, `account_group_id`; import from `carmen-gl` interface) | `master/chart-of-accounts/` | `config/config_chart-of-accounts/` → `api/config/:bu_code/chart-of-accounts` (+ `POST import`, `POST import-from-interface/carmen-gl`) | — (config collection) | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` only; no `@Permission` on the config controllers | `enum_chart_of_accounts_category` (`asset, liability, equity, revenue, expense, statistic`), `enum_chart_of_accounts_type` += `summary` |
| Cost centers / cost center groups / cost-center↔account links (`tb_cost_center`, `tb_cost_center_group`, `tb_cost_center_account`) | `master/cost-center*/` | `config/config_cost-centers/`, `config/config_cost-center-groups/` | — | `20260904103000_add_cost_center` | Keycloak + `AppIdGuard` | — |
| GL account groups (`tb_gl_account_group`, tree ≤ 4 levels, category must match parent) | `gl/gl-account-group/` | `config/config_gl-account-groups/` → `api/config/:bu_code/gl-account-groups` | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | — |
| JV prefixes (`tb_gl_jv_prefix`; `code` immutable, `is_system` undeletable, single `is_default`) | `gl/gl-jv-prefix/` | `config/config_gl-jv-prefixes/` → `api/config/:bu_code/gl-jv-prefixes` | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | — |
| GL periods (`tb_gl_period`; 13 per fiscal year created from `tb_application_config` key `gl_setting`.`fiscal_year_start_month`; close/reopen in sequence) | `gl/gl-period/` | `config/config_gl-periods/` → `api/config/:bu_code/gl-periods` (`POST years`, `POST :id/close`, `POST :id/reopen`) | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | `enum_gl_period_status` (`open, closed, locked`) |
| Journal vouchers — draft CRUD and review workflow (`tb_gl_jv_header`, `tb_gl_jv_detail`) | `gl/gl-jv/` | `application/gl-jv/` → `api/:bu_code/gl-jv` (11 routes) | `gl-jv/*` (11 files) | `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path` | licence `accounting.gl`; drafting is workflow-gated (`permission.route-map.ts:352-354` forgives `accounting.gl:create/update/delete`) | `enum_jv_status` += `in_review`, `scheduled`, `void`; `enum_workflow_type` += `gl_jv`; `enum_gl_jv_source` |
| Ledger posting and balances (`tb_gl_balance`) — **covered on the sub-page only insofar as it is the target inventory would post to** | `gl/gl-posting/`, `gl/gl-balance/` | `application/gl-posting/` → `api/:bu_code/gl-posting` | `gl-posting/*` (6 files) | `20260914030000_gl_core_jv_ledger` | `accounting.gl:{post, void, reverse, recalculate, close_year}` (`seed.permission.data.ts:1612-1637`) | — |
| Budgets (`tb_gl_budget`, `tb_gl_budget_detail`; one active revision per year) | `gl/gl-budget/` | `application/gl-budgets/` → `api/:bu_code/gl-budgets` (+ `POST :id/activate`) | `gl-budgets/*` (6 files) | `20260915043038_gl_core_budget_template` | `accounting.gl.budget:{view, create, update, delete, activate}`; licence `accounting.gl.budget` | `enum_gl_budget_status` (`draft, active, superseded`) |
| JV templates (`tb_gl_jv_template`, `_detail`, `_run`; `generate` / `generate-all-due`) | `gl/gl-jv-template/` | `application/gl-jv-templates/` → `api/:bu_code/gl-jv-templates` (+ `POST :id/generate`, `POST generate-all-due`) | `gl-jv-templates/*` (7 files) | `20260915043038_gl_core_budget_template` | `accounting.gl.jv_template:{view, create, update, delete, generate}`; licence `accounting.gl.jv_template` | `enum_gl_jv_template_type` (`recurring, allocation, amortize`), `enum_gl_amortize_type` (`day_in_month, monthly`), `enum_gl_side` (`debit, credit`) |
| GL reports — trial balance | `gl/gl-balance/` (raw SQL) | `application/gl-reports/` → `GET api/:bu_code/gl-reports/trial-balance` | `gl-reports/*` (1 file) | — | `accounting.gl:view` | — |

Licence features: `accounting.gl` (parent `accounting`), `accounting.gl.budget` and `accounting.gl.jv_template` (children of `accounting.gl`) — `packages/prisma-shared-schema-platform/prisma/seed.license-feature.data.ts:60,100,108`. Gateway segment → resource mapping: `permission.route-map.ts:57-61` (`app:gl-jv`, `app:gl-posting`, `app:gl-reports` → `accounting.gl`; `app:gl-budgets` → `accounting.gl.budget`; `app:gl-jv-templates` → `accounting.gl.jv_template`).

## 2. Data Model (skeleton)

From `packages/prisma-shared-schema-tenant/prisma/schema.prisma` at `ef4d6f08f`. One line per table; field-level detail is out of scope (§ 1.1).

| Table (schema line) | Purpose |
|---|---|
| `tb_chart_of_accounts` (2934) | Account master: `code`, `nature`, `type` (incl. non-postable `header` / `summary`), `category`, `reverse_sign`, `use_in[]`, `is_require_cost_center`, `account_group_id`. |
| `tb_cost_center_group` (2976), `tb_cost_center` (3005), `tb_cost_center_account` (3037) | Accounting cost centers (distinct from `tb_department`), grouped; optional whitelist of which accounts a cost center may post to. |
| `tb_gl_jv_prefix` (3065) | Voucher numbering prefix (`code` ≤ 10 chars, `is_system`, single `is_default`). |
| `tb_gl_account_group` (3093) | Report grouping tree for accounts, ≤ 4 levels, one `category` per subtree. |
| `tb_gl_period` (3128) | Fiscal calendar: `fiscal_year`, `period_no` 1–13 (13 = year-end adjustment period sharing period 12's last instant), `start_at`, `end_at`, `status`, `closed_at/by`. **No relation to `tb_inventory_period`.** |
| `tb_gl_jv_header` (4741) | Voucher header: `jv_no` + `prefix_code`, `jv_date`, `is_adjustment`, `source` (`enum_gl_jv_source`), `source_ref_type/id`, `template_id`, `post_at` / `posted_at`, `is_auto_reverse` / `reverse_at`, `reversal_of_jv_id` / `reversed_by_jv_id`, `void_*`, `total_debit/credit`, `jv_status`, plus the standard `workflow_*` / `user_action` / `last_action*` columns every workflow document carries. Guarded by DB trigger `gl_jv_posted_guard`. |
| `tb_gl_jv_detail` (4496) | Voucher line: `chart_of_accounts_id` (+ denormalised `account_code/name`), `cost_center_id` (+ code/name), `debit` XOR `credit`, `exchange_rate`, `base_debit/credit`, `quantity`. |
| `tb_gl_balance` (4552) | Derived balance per (`gl_period_id`, `cost_center_id` or nil-uuid, `chart_of_accounts_id`): `opening`, `debit`, `credit`. No soft-delete, no `doc_version`. Written only by `GlPostingService` and rebuilt by `recalculate`. |
| `tb_gl_budget` (4575), `tb_gl_budget_detail` (4603) | Annual budget × revision; one line per (cost center?, account, period 1–12). |
| `tb_gl_jv_template` (4632), `tb_gl_jv_template_detail` (4677) | Recurring / allocation / amortize templates with a from–to period range, `frequency_months`, and per-type columns. |
| `tb_gl_jv_template_run` (4708) | Fact row "template T generated voucher V for period P"; unique on (`template_id`, `gl_period_id`). |
| `tb_application_config` key `gl_setting` (5894) | JSON: `fiscal_year_start_month`, `allow_post_to_closed_period`, `reversal_prefix_id`, `retained_earnings_account_id`, `auto_jv_prefix_id` (`gl-posting.service.ts:57-62`, `gl-period.service.ts:21-29`). |

Enums: `enum_jv_status` (schema 140) `draft, in_review, scheduled, posted, void` · `enum_workflow_type` (276) `purchase_request, store_requisition, purchase_order, gl_jv` · `enum_gl_period_status` (2899) · `enum_gl_budget_status` (2905) · `enum_gl_jv_template_type` (2911) · `enum_gl_amortize_type` (2917) · `enum_gl_side` (2922) · `enum_gl_jv_source` (4724) `manual, recurring, allocation, amortize, reversal, closing, ap, ar, inventory, asset, interface`.

## 3. Where inventory meets the ledger

Summarised from [gl-posting](/en/inventory/general-ledger/gl-posting):

- **Nothing posts.** `grep -rn -E "gl[-_]posting|gl[-_]jv|tb_gl_|GlPosting|GlJv|journal" apps/micro-business/src/inventory apps/micro-business/src/procurement` returns **0 hits**. GRN commit, stock-in/stock-out commit, credit note, store requisition, physical count / spot check, cost-layer writes and the inventory period-end close all finish without touching `tb_gl_jv_header`. The only writers of `enum_gl_jv_source` are `manual` (`gl-jv.service.ts:214`), `reversal` (`gl-posting.service.ts:571`), `closing` (`:909`, `:1116`) and the three template types (`gl-jv-template.service.ts:777`).
- **Two period calendars, unlinked.** Inventory close operates on `tb_inventory_period` (`period-end.close-transaction.helper.ts:80,195,210`); the ledger operates on `tb_gl_period`. Neither table references the other, `tb_gl_period` is not read anywhere outside `gl/` and the `config_gl-*` gateway modules, and closing one has no effect on the other.
- **`gl_run_due` is not an inventory job.** The cron (`micro-cronjobs/internal/executor/gl_run_due.go`, job type `gl_run_due`) calls `POST /api/internal/gl/run-due` per business unit, which posts `scheduled` vouchers whose `post_at` has passed and reverses posted vouchers whose `reverse_at` has passed. It does **not** generate JV templates — `generate-all-due` is a separate, manually-invoked endpoint with no cron caller.
- **What would have to change** for inventory to post: a caller inside the inventory/procurement service that builds `ICreateGlJv` lines, calls `GlJvService.createInternal(..., { source: enum_gl_jv_source.inventory, source_ref_type, source_ref_id })` inside its own transaction, and then either submits it through the `gl_jv` workflow or posts it via `GlPostingService.post`. None of that exists; the sub-page § 9 lists what a tester should assert until it does.

## 4. No frontend yet

`carmen-inventory-frontend-react/routes/accounting/` appeared in commit `4a72884d` (2026-07-31, "feat(accounting): add accounting document routes and dashboard") and, as of FE `0713cbc9` (2026-09-22), **is a mock**:

- `accounting-documents.ts:100` `documentsFor()` fabricates 8 rows per document kind (`JV2607-0001…`, fixed descriptions/parties, `amount = 10000 + index × 3750`); `accounting-detail.tsx` / `accounting-list.tsx` render those rows. Nine kinds are declared: journal, template, recurring, allocation vouchers, financial reports, AP invoice/payment, AR invoice/receipt.
- `accounting.dashboard.tsx:143` wraps a hard-coded `data` object in `useQuery({ queryFn: async () => data, initialData: data, staleTime: Infinity })` — no HTTP call.
- No file under `hooks/`, `types/` or `routes/` references `/gl-jv`, `/gl-posting` or `tb_gl_*`. The router (`routes/router.tsx:770-800`) and the module tile (`constant/module-list.ts:403-425`, licence features `accounting.gl` / `accounting.gl.jv_template`) are the only real wiring.
- E2E: `../carmen-inventory-frontend-e2e/docs/test-cases/COVERAGE.md:21-28` lists every `/accounting/*` URL as "none", and `1204-section-landing.md:15` records why no case was written (the dashboard hard-codes all six widgets and does not hit an API).

There is therefore no screen to document, no Playwright spec to cross-link, and no screenshot to capture. Do not write user-flow or test-scenario pages for this module until a real UI lands.

## 5. Reference Sources

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/gl/` (`gl-account-group`, `gl-balance`, `gl-budget`, `gl-jv`, `gl-jv-prefix`, `gl-jv-template`, `gl-period`, `gl-posting`); gateway `apps/backend-gateway/src/application/{gl-jv,gl-posting,gl-reports,gl-budgets,gl-jv-templates}/` and `config/config_{chart-of-accounts,cost-centers,cost-center-groups,gl-account-groups,gl-jv-prefixes,gl-periods}/`; RPC contract `packages/rpc-contract/src/contracts/gl-posting.ts`.
- Prisma: `packages/prisma-shared-schema-tenant/prisma/schema.prisma` and migrations `20260909170000_gl_core_master`, `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path`, `20260915043038_gl_core_budget_template`.
- Cron: `../micro-cronjobs/internal/executor/gl_run_due.go`, `internal/model/cronjob.go:141-149`, `README.md:254`.
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/{gl-jv,gl-posting,gl-reports,gl-budgets,gl-jv-templates}/`.
- Frontend (mock only): `../carmen-inventory-frontend-react/routes/accounting/`.
- E2E: none (`../carmen-inventory-frontend-e2e/docs/test-cases/COVERAGE.md` § Accounting).
- carmen/docs: frozen 2026-04-27 and **contradicted by HEAD** on this topic — `app/inventory-management/inventory-transactions/BR-inventory-transactions.md:21,31,143,162,214` and `store-requisitions/SR-API-JournalEntry-Endpoints.md` describe automatic GL integration that does not exist; do not cite them.

## 6. Pages in This Module

- [GL Posting and the Inventory Seam](/en/inventory/general-ledger/gl-posting) — what `gl-posting` does, the JV status lifecycle and `gl_jv` workflow, the `gl_run_due` cron, template generation requests, `tb_gl_period` vs `tb_inventory_period`, and the verified absence of any inventory→GL posting.
