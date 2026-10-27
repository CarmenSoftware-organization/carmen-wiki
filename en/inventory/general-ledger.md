---
title: General Ledger
description: GL and AP subledger, documented only where they touch inventory. Inventory never posts to the ledger directly; the one inventory-fed voucher is an AP invoice built from committed GRN lines.
published: true
date: 2026-10-27T00:00:00.000Z
tags: general-ledger, inventory, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# General Ledger

> **At a Glance**
> **Module purpose:** A journal-voucher ledger (`tb_gl_jv_header` / `tb_gl_jv_detail` → `tb_gl_balance`) plus, since 2026-09-23, AP and AR subledgers that post into it through a facade &nbsp;·&nbsp; **Wiki scope:** documented **only where it touches inventory**; GL master data, budgets, JV templates, GL reports, AP payment, AR and accounting dashboards are an intentional gap (§ 1.1, § 1.2) &nbsp;·&nbsp; **Inventory→GL today:** **no direct posting** — no GRN, stock-in/out, credit note, store requisition, physical count, cost layer or inventory period-end writes a voucher (see [gl-posting](/en/inventory/general-ledger/gl-posting) § 2). **The one link:** an **AP invoice built from committed GRN lines** posts `Dr inventory / Dr input VAT / Cr AP` and locks those GRN lines against editing — see [AP Invoice from GRN](/en/inventory/general-ledger/ap-invoice-from-grn) &nbsp;·&nbsp; **Frontend:** `routes/accounting` — journal-voucher list/form and the settings form call the real API; AP, AR, document pages and the dashboard still run on browser mocks (§ 4) &nbsp;·&nbsp; **Key entities/tables:** `tb_gl_jv_header`, `tb_gl_jv_detail`, `tb_gl_balance`, `tb_gl_period` (a separate calendar from `tb_inventory_period`), `tb_ap_invoice` + `tb_ap_invoice_detail_source` &nbsp;·&nbsp; **Sub-pages:** 2

![General Ledger screen](/screenshots/general-ledger/index.png)

## 1. Overview

The General Ledger is a backend subsystem under `apps/micro-business/src/gl/` (ten NestJS modules: `gl-account-group`, `gl-balance`, `gl-budget`, `gl-dimension`, `gl-jv`, `gl-jv-prefix`, `gl-jv-template`, `gl-period`, `gl-posting`, `gl-subledger-posting`) with gateway routes under `api/:bu_code/gl-*` and `api/config/:bu_code/gl-*`, tenant migrations `20260909170000` … `20260915043038` for the ledger and `20260923060040` / `20260930*` for the AP and AR tables, and one scheduled job in `micro-cronjobs`. It is a general-purpose accounting ledger — chart of accounts, cost centers, 13-period fiscal calendar, journal vouchers with a review workflow, balances, budgets, recurring/allocation/amortize templates, trial balance.

**This wiki is an inventory ERP manual, so the ledger is documented only at the seam with inventory** (owner decision 2026-09-22). That seam is **still empty on the posting side**: as of backend `c9d788829` (2026-10-27, re-verified with the 2026-09-22 greps) there is no code path from any inventory or procurement document into `tb_gl_jv_header`, and `enum_gl_jv_source` members `inventory`, `asset` and `interface` are declared but never written. What changed is that `ap` and `ar` are now written - by the AP invoice, AP payment and AR invoice services through `GlSubledgerPostingService` - and an AP invoice can be created *from* committed GRN lines, which is the first (and only) way received goods reach the ledger. Two sub-pages cover the seam: [gl-posting](/en/inventory/general-ledger/gl-posting) (the greps, how a voucher reaches `tb_gl_balance`, the subledger facade, `gl_run_due`) and [AP Invoice from GRN](/en/inventory/general-ledger/ap-invoice-from-grn) (the GRN-consuming route, the voucher it posts, the GRN edit lock, and the read-only external export of GRN/CN/SR/SI/SO as Dr/Cr data).

### 1.1 Intentionally not documented

Everything below exists in code and is **deliberately left out of this wiki**. The table is here so that a developer who greps a GL identifier lands on this page and knows it is a chosen gap, not an omission. Consult the source paths directly.

| Area | Backend (`apps/micro-business/src/`) | Gateway route (`apps/backend-gateway/src/`) | Bruno folder (`collections/carmen-inventory/_uncategorized/`) | Migration | Permission / licence key | Enums |
|---|---|---|---|---|---|---|
| Chart of accounts (`tb_chart_of_accounts`; renamed from account code, extended with `category`, `is_require_cost_center`, `account_group_id`; import from `carmen-gl` interface) | `master/chart-of-accounts/` | `config/config_chart-of-accounts/` → `api/config/:bu_code/chart-of-accounts` (+ `POST import`, `POST import-from-interface/carmen-gl`) | — (config collection) | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` only; no `@Permission` on the config controllers | `enum_chart_of_accounts_category` (`asset, liability, equity, revenue, expense, statistic`), `enum_chart_of_accounts_type` += `summary` |
| Cost centers / cost center groups / cost-center↔account links (`tb_cost_center`, `tb_cost_center_group`, `tb_cost_center_account`) | `master/cost-center*/` | `config/config_cost-centers/`, `config/config_cost-center-groups/` | — | `20260904103000_add_cost_center` | Keycloak + `AppIdGuard` | — |
| GL account groups (`tb_gl_account_group`, tree ≤ 4 levels, category must match parent) | `gl/gl-account-group/` | `config/config_gl-account-groups/` → `api/config/:bu_code/gl-account-groups` | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | — |
| JV prefixes (`tb_gl_jv_prefix`; `code` immutable, `is_system` undeletable, single `is_default`) | `gl/gl-jv-prefix/` | `config/config_gl-jv-prefixes/` → `api/config/:bu_code/gl-jv-prefixes` | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | — |
| GL periods (`tb_gl_period`; 13 per fiscal year created from `tb_application_config` key `gl_setting`.`fiscal_year_start_month`; close/reopen in sequence) | `gl/gl-period/` | `config/config_gl-periods/` → `api/config/:bu_code/gl-periods` (`POST years`, `POST :id/close`, `POST :id/reopen`) | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | `enum_gl_period_status` (`open, closed, locked`) |
| Journal vouchers — draft CRUD and review workflow (`tb_gl_jv_header`, `tb_gl_jv_detail`) | `gl/gl-jv/` | `application/gl-jv/` → `api/:bu_code/gl-jv` (11 routes) | `gl-jv/*` (11 files) | `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path` | licence `accounting.gl`; drafting is workflow-gated (`permission.route-map.ts:395-397` forgives `accounting.gl:create/update/delete`) | `enum_jv_status` += `in_review`, `scheduled`, `void`; `enum_workflow_type` += `gl_jv`; `enum_gl_jv_source` |
| Ledger posting and balances (`tb_gl_balance`) — **covered on the sub-page only insofar as it is the target inventory would post to** | `gl/gl-posting/`, `gl/gl-balance/` | `application/gl-posting/` → `api/:bu_code/gl-posting` | `gl-posting/*` (6 files) | `20260914030000_gl_core_jv_ledger` | `accounting.gl:{post, void, reverse, recalculate, close_year}` (`seed.permission.data.ts`, `accounting.gl` block from ~`:1666`) | — |
| Accounting dimensions (`tb_gl_dimension` code ≤ 20 chars, `tb_gl_dimension_value` code ≤ 30 chars with optional `effective_from` / `effective_to`, `tb_gl_account_dimension_rule` with `requirement` `mandatory`/`optional`/`prohibited`, `tb_gl_jv_detail_dimension`) - new 2026-09/10; enforced on JV lines at submit and post | `gl/gl-dimension/` | `config/config_gl-dimensions/`, `config/config_gl-account-dimension-rules/` → `api/config/:bu_code/gl-dimensions`, `…/gl-account-dimension-rules` | — | tenant schema (`enum_gl_account_dimension_rule_requirement`) | Keycloak + `AppIdGuard` | `enum_gl_account_dimension_rule_requirement` (`mandatory, optional, prohibited`) |
| Budgets (`tb_gl_budget`, `tb_gl_budget_detail`; one active revision per year) | `gl/gl-budget/` | `application/gl-budgets/` → `api/:bu_code/gl-budgets` (+ `POST :id/activate`) | `gl-budgets/*` (6 files) | `20260915043038_gl_core_budget_template` | `accounting.gl.budget:{view, create, update, delete, activate}`; licence `accounting.gl.budget` | `enum_gl_budget_status` (`draft, active, superseded`) |
| JV templates (`tb_gl_jv_template`, `_detail`, `_run`; `generate` / `generate-all-due`) | `gl/gl-jv-template/` | `application/gl-jv-templates/` → `api/:bu_code/gl-jv-templates` (+ `POST :id/generate`, `POST generate-all-due`) | `gl-jv-templates/*` (7 files) | `20260915043038_gl_core_budget_template` | `accounting.gl.jv_template:{view, create, update, delete, generate}`; licence `accounting.gl.jv_template` | `enum_gl_jv_template_type` (`recurring, allocation, amortize`), `enum_gl_amortize_type` (`day_in_month, monthly`), `enum_gl_side` (`debit, credit`) |
| GL reports — trial balance | `gl/gl-balance/` (raw SQL) | `application/gl-reports/` → `GET api/:bu_code/gl-reports/trial-balance` | `gl-reports/*` (1 file) | — | `accounting.gl:view` | — |

Licence features: `accounting.gl` (parent `accounting`), `accounting.gl.budget` and `accounting.gl.jv_template` (children of `accounting.gl`) — `packages/prisma-shared-schema-backstage/prisma/seed.license-feature.data.ts:60,100,108`. Gateway segment → resource mapping: `packages/prisma-shared-schema-backstage/prisma/permission.route-map.ts:57-61` (`app:gl-jv`, `app:gl-posting`, `app:gl-reports` → `accounting.gl`; `app:gl-budgets` → `accounting.gl.budget`; `app:gl-jv-templates` → `accounting.gl.jv_template`).

### 1.2 Accounting features with no inventory touch-point (summary only)

| Feature | Where | Inventory link |
|---|---|---|
| AP payment voucher (settle AP invoices, WHT, FX, deposits) | `micro-business/src/ap/ap-payment/`, `api/:bu_code/ap-payment`; FE `routes/accounting/accounts-payable/payment/` (mock) | None - settles AP invoices; posts `source = ap` |
| AR invoice / credit note, tax invoice, receipt | `micro-business/src/ar/ar-invoice/`, `api/:bu_code/ar-invoice`; tables `tb_ar_invoice*`, `tb_ar_tax_invoice`, `tb_ar_receipt*` (migrations `20260930074505`, `20260930180414`); FE `accounts-receivable/` (mock) | None - posts `source = ar`; no stock movement |
| Accounting dashboard, cash forecast, document list/detail pages for template / recurring / allocation vouchers and financial reports | FE `routes/accounting/dashboard`, `documents/` (mock data, `dashboard-mock-data.ts`) | None |
| Chart-of-accounts mapping for exports | `api/:bu_code/account-mapping`, `tb_account_mapping` | Inventory-facing: see [chart-of-account-mapping](/en/inventory/master-data/chart-of-account-mapping) |
| AP invoice **from GRN** | `api/:bu_code/ap-invoice` | Yes - [AP Invoice from GRN](/en/inventory/general-ledger/ap-invoice-from-grn) |

## 2. Data Model (skeleton)

From `packages/prisma-shared-schema-tenant/prisma/schema.prisma` at `c9d788829`. One line per table; field-level detail is out of scope (§ 1.1).

| Table (schema line) | Purpose |
|---|---|
| `tb_chart_of_accounts` (3067) | Account master: `code`, `nature`, `type` (incl. non-postable `header` / `summary`), `category`, `reverse_sign`, `use_in[]`, `is_require_cost_center`, `account_group_id`. |
| `tb_cost_center_group` (3112), `tb_cost_center` (3141), `tb_cost_center_account` (3175) | Accounting cost centers (distinct from `tb_department`), grouped; optional whitelist of which accounts a cost center may post to. |
| `tb_gl_jv_prefix` (3203) | Voucher numbering prefix (`code` ≤ 10 chars, `is_system`, single `is_default`). |
| `tb_gl_account_group` (3231) | Report grouping tree for accounts, ≤ 4 levels, one `category` per subtree. |
| `tb_gl_period` (3266) | Fiscal calendar: `fiscal_year`, `period_no` 1–13 (13 = year-end adjustment period sharing period 12's last instant), `start_at`, `end_at`, `status`, `closed_at/by`. **No relation to `tb_inventory_period`.** |
| `tb_gl_jv_header` (4902) | Voucher header: `jv_no` + `prefix_code`, `jv_date`, `is_adjustment`, `source` (`enum_gl_jv_source`), `source_ref_type/id`, `template_id`, `post_at` / `posted_at`, `is_auto_reverse` / `reverse_at`, `reversal_of_jv_id` / `reversed_by_jv_id`, `void_*`, `total_debit/credit`, `jv_status`, plus the standard `workflow_*` / `user_action` / `last_action*` columns every workflow document carries. Guarded by DB trigger `gl_jv_posted_guard`. |
| `tb_gl_jv_detail` (4656) | Voucher line: `chart_of_accounts_id` (+ denormalised `account_code/name`), `cost_center_id` (+ code/name), `debit` XOR `credit`, `exchange_rate`, `base_debit/credit`, `quantity`. |
| `tb_gl_balance` (4713) | Derived balance per (`gl_period_id`, `cost_center_id` or nil-uuid, `chart_of_accounts_id`): `opening`, `debit`, `credit`. No soft-delete, no `doc_version`. Written only by `GlPostingService` and rebuilt by `recalculate`. |
| `tb_gl_budget` (4736), `tb_gl_budget_detail` (4764) | Annual budget × revision; one line per (cost center?, account, period 1–12). |
| `tb_gl_jv_template` (4793), `tb_gl_jv_template_detail` (4838) | Recurring / allocation / amortize templates with a from–to period range, `frequency_months`, and per-type columns. |
| `tb_gl_jv_template_run` (4869) | Fact row "template T generated voucher V for period P"; unique on (`template_id`, `gl_period_id`). |
| `tb_application_config` (6060) key `gl_setting` | JSON: `fiscal_year_start_month`, `allow_post_to_closed_period`, `reversal_prefix_id`, `retained_earnings_account_id`, `auto_jv_prefix_id`, plus the AP/AR keys `ap_control_account_id`, `input_vat_account_id`, `wht_payable_account_id`, `advance_deposit_account_id`, `realized_fx_gain_account_id`, `realized_fx_loss_account_id`, `ap_jv_prefix_id`, `ar_control_account_id`, `output_vat_account_id`, `ar_jv_prefix_id` (`GlSetting`, `gl-posting.service.ts:91-106`). |
| `tb_gl_dimension` (7049), `tb_gl_dimension_value` (7079), `tb_gl_account_dimension_rule` (7109), `tb_gl_jv_detail_dimension` (7130) | Accounting dimensions and the per-account `mandatory`/`optional`/`prohibited` rule checked on JV lines. |
| `tb_ap_invoice` (7182), `_detail` (7267), `_detail_source` (7350), `_reference` (7370), `_tax` (7390) | AP invoice / debit note / credit note / deposit; `_detail_source` links a line to a GRN item (`matched_qty`) - see [AP Invoice from GRN](/en/inventory/general-ledger/ap-invoice-from-grn). `tb_ap_payment*` (7417+) and `tb_ar_*` (7637+) are out of scope. |

Enums: `enum_jv_status` (schema 135) `draft, in_review, scheduled, posted, void` · `enum_workflow_type` (271) `purchase_request, store_requisition, purchase_order, gl_jv, ap_invoice, ap_payment, ar_invoice` · `enum_gl_period_status` (3032) · `enum_gl_budget_status` (3038) · `enum_gl_jv_template_type` (3044) · `enum_gl_amortize_type` (3050) · `enum_gl_side` (3055) · `enum_ap_invoice_doc_type` (300) `invoice, debit_note, credit_note, deposit` · `enum_ap_invoice_status` (307) `draft, in_review, posted, void` · `enum_ap_invoice_source` (314) `manual, grn, copy, excel, ai, interface` · `enum_gl_jv_source` (4885) `manual, recurring, allocation, amortize, reversal, closing, ap, ar, inventory, asset, interface`.

## 3. Where inventory meets the ledger

Summarised from [gl-posting](/en/inventory/general-ledger/gl-posting) and [AP Invoice from GRN](/en/inventory/general-ledger/ap-invoice-from-grn):

- **Nothing posts directly.** `grep -rn -E "gl[-_]posting|gl[-_]jv|tb_gl_|GlPosting|GlJv|journal" apps/micro-business/src/inventory apps/micro-business/src/procurement` returns hits only under `inventory/accounting-export/` (names containing "GlJournal"; read-only export, never calls `gl/`). GRN commit, stock-in/stock-out commit, credit note, store requisition, physical count / spot check, cost-layer writes and the inventory period-end close all finish without touching `tb_gl_jv_header`. The writers of `enum_gl_jv_source` are `manual`, `reversal`, `closing`, the three template types, and — new — `ap` (AP invoice, AP payment) and `ar` (AR invoice); `inventory`, `asset`, `interface` are never written.
- **The one link: AP invoice from GRN.** `POST api/:bu_code/ap-invoice/from-grn` turns committed `post_type = ap` GRN items into a draft AP invoice (`doc_source = grn`, `tb_ap_invoice_detail_source.matched_qty` tracks how much of each GRN line is invoiced). Final approval posts `Dr inventory account / Dr input VAT / Cr AP` through `GlSubledgerPostingService`; the GRN then becomes non-editable while a live invoice references it (`GRN_AP_LINKED_NOT_EDITABLE`). Stock quantity and cost layers are not touched by any of this, so an invoice price that differs from the GRN price creates a `variance_amount` on the invoice line but does not revalue stock.
- **Two period calendars, unlinked.** Inventory close operates on `tb_inventory_period`; the ledger operates on `tb_gl_period`. Neither table references the other, `tb_gl_period` is not read anywhere under `inventory/` or `procurement/`, and closing one has no effect on the other. (An AP invoice does check that the GL period of its `doc_date` is open.)
- **`gl_run_due` is not an inventory job.** The cron (`micro-cronjobs/internal/executor/gl_run_due.go`, job type `gl_run_due`) calls `POST /api/internal/gl/run-due` per business unit, which posts `scheduled` vouchers whose `post_at` has passed and reverses posted vouchers whose `reverse_at` has passed. It does **not** generate JV templates — `generate-all-due` is a separate, manually-invoked endpoint with no cron caller.
- **External export is a separate seam.** `GET api/ext/v1/ap-invoices` (GRN, CN) and `GET api/ext/v1/gl-journals` (SR, SI, SO) hand an external accounting system Dr/Cr data built from inventory documents and `tb_account_mapping`; nothing is written to the ledger (see AP Invoice from GRN § 6).
- **What would have to change** for inventory itself to post: a caller inside the inventory/procurement service that builds `ISubledgerPostingLine`s and calls `GlSubledgerPostingService.postFromSource({ source: enum_gl_jv_source.inventory, source_ref_type, source_ref_id, ... }, tx)` inside its own transaction. None of that exists; [gl-posting](/en/inventory/general-ledger/gl-posting) § 9 lists what a tester should assert until it does.

## 4. Frontend status

`carmen-frontend/routes/accounting/` (router `routes/router.tsx:885-1030`, four launcher sections in `constant/module-list.ts:151+`: General Ledger `accounting.gl`, Accounts Payable `accounting.ap`, Accounts Receivable `accounting.ar`, Asset) was a hard-coded mock on 2026-09-22 and is now **partly real**:

| Screen | Data source |
|---|---|
| Journal voucher list / form (`/accounting/journal-voucher[/:id]`) | **Real API** — `journal-voucher-http-repository.ts` calls `GL_JV_*` and `GL_POSTING_*` endpoints (`gl-jv`, `gl-posting` post/void/reverse, `gl-jv-prefixes`); ids starting `mock-` still go to a mock repository |
| Accounting settings form (`/accounting/settings`) | **Real** — reads/writes `tb_application_config` key `gl_setting` (`gl-setting-value.ts`, `use-gl-jv-prefix-options.ts`) |
| AP dashboard, AP invoice list/detail, AP payment list/detail | **Mock** — `use-accounts-payable.ts` always builds `createApMockRepository` (localStorage-backed, prefix `carmen-ap-mock-v1`); no call to `api/:bu_code/ap-invoice` |
| AR invoice list/detail | **Mock** (`ar-invoice-model.ts`, `ar-invoice-list.route.tsx`) |
| Accounting dashboard (`/accounting`, AP/AR/asset dashboards) and cash forecast | **Mock** — `dashboard-mock-data.ts`; role audiences `accountant` / `controller` / `executive` (`dashboard-access.ts`) |
| Template / recurring / allocation voucher, financial report, AR receipt, asset pages | **Mock** — `documents/accounting-document-model.ts` |

Known frontend/back-end mismatch (document only): the journal-voucher UI types use statuses `submitted`, `posting`, `post_failed`, `voided`, `reversal_scheduled`, `reversed` (`types/journal-voucher.ts:1-10`), while the backend enum is `draft, in_review, scheduled, posted, void` and the gateway returns no `capabilities`; `journalVoucherCapabilities` (`journal-voucher-source.ts`) derives button availability from `jv_status === "submitted"`, so a real voucher in `in_review` would not enable approve/reject/return there. Also `sourceDocumentHref` matches `source_type === "ap_invoice"` while the backend `source` value is `ap` (the `source_ref_type` is `ap_invoice`), so the "open source document" link would not resolve for AP-generated vouchers. Both are worth a ticket after a manual check with a `gl_jv` workflow configured.

E2E: `../carmen-frontend-e2e/docs/test-cases/COVERAGE.md` still lists the `/accounting/*` URLs as uncovered. There is no Playwright spec to cross-link; do not write user-flow or test-scenario pages for this module until the AP/AR screens leave the mock.

## 5. Reference Sources

- Backend: `../carmen-turborepo-backend/apps/micro-business/src/gl/` (`gl-account-group`, `gl-balance`, `gl-budget`, `gl-jv`, `gl-jv-prefix`, `gl-jv-template`, `gl-period`, `gl-posting`, `gl-dimension`, `gl-subledger-posting`) and `ap/ap-invoice/`; gateway `apps/backend-gateway/src/application/{gl-jv,gl-posting,gl-reports,gl-budgets,gl-jv-templates}/` and `config/config_{chart-of-accounts,cost-centers,cost-center-groups,gl-account-groups,gl-jv-prefixes,gl-periods}/`; RPC contract `packages/rpc-contract/src/contracts/gl-posting.ts`.
- Prisma: `packages/prisma-shared-schema-tenant/prisma/schema.prisma` and migrations `20260909170000_gl_core_master`, `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path`, `20260915043038_gl_core_budget_template`.
- Cron: `../micro-cronjobs/internal/executor/gl_run_due.go`, `internal/model/cronjob.go:141-149`, `README.md:254`.
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/{gl-jv,gl-posting,gl-reports,gl-budgets,gl-jv-templates,ap-invoice,ap-payment,ar-invoice}/`.
- Frontend: `../carmen-frontend/routes/accounting/` (journal-voucher + settings real; AP/AR/dashboard/documents mock).
- E2E: none (`../carmen-frontend-e2e/docs/test-cases/COVERAGE.md` § Accounting).
- carmen/docs: frozen 2026-04-27 and **contradicted by HEAD** on this topic — `app/inventory-management/inventory-transactions/BR-inventory-transactions.md:21,31,143,162,214` and `store-requisitions/SR-API-JournalEntry-Endpoints.md` describe automatic GL integration that does not exist; do not cite them.

## 6. Pages in This Module

- [GL Posting and the Inventory Seam](/en/inventory/general-ledger/gl-posting) — what `gl-posting` does, the JV status lifecycle and `gl_jv` workflow, the subledger facade, the `gl_run_due` cron, template generation requests, `tb_gl_period` vs `tb_inventory_period`, and the verified absence of any direct inventory→GL posting.
- [AP Invoice from GRN](/en/inventory/general-ledger/ap-invoice-from-grn) — the only inventory-fed ledger path: `grn-candidates` / `from-grn`, `matched_qty`, the `Dr inventory / Dr input VAT / Cr AP` voucher, the GRN edit lock, void rules, and the external GRN/CN/SR/SI/SO Dr/Cr export.
