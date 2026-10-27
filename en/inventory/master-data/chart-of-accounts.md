---
title: Chart of Accounts
description: GL account codes (nature, type, category, account group, dimension rules) with file and Carmen GL import — renamed from Account Code on 2026-08-27; feeds the GL book, cost-center allow-lists and account mapping.
published: true
date: 2026-10-27T00:00:00.000Z
tags: master-data, chart-of-accounts, general-ledger, configuration, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# Chart of Accounts

> **At a Glance**
> **Owner:** Sysadmin / Finance &nbsp;·&nbsp; **Table:** `tb_chart_of_accounts` + `enum_chart_of_accounts_{nature,type,category,use_in}` &nbsp;·&nbsp; **Used by:** [general-ledger](/en/inventory/general-ledger) (JV lines, account groups), [cost-center](/en/inventory/master-data/cost-center) allow-lists, [chart-of-account-mapping](/en/inventory/master-data/chart-of-account-mapping) overrides &nbsp;·&nbsp; **Permission:** `configuration.chart_of_accounts.*` &nbsp;·&nbsp; **Licence key:** `configuration.chart_of_accounts` &nbsp;·&nbsp; The BU's account-code list, maintainable on a full-page form, by file upload (API), or by pull from Carmen GL.

![Chart of Accounts screen](/screenshots/master-data/chart-of-accounts.png)

## 1. What & Who

The **chart of accounts** is the list of GL account codes a business unit posts to. Each row is a `code` with two description lines, a balance **nature** (`debit` / `credit`), a statement **type** (`header` = non-posting group title, `balance_sheet`, `income_statement`, `statistic`, `summary`), an accounting **category** (`asset` … `statistic`, used for year-end roll-forward and account-group matching), the ledgers it may be **used in** (`ap`, `ar`, `gl`, `ast`), a `reverse_sign` presentation flag, an `is_require_cost_center` flag that forces a cost center onto every JV line, and an optional link to a GL account group.

It arrived in two steps: **Account Code** (`tb_account_code`, `code` / `name` / `description`, 2026-08-20) was renamed and widened into **Chart of Accounts** on 2026-08-27 (`name → description_1`, `description → description_2`, plus `nature`, `type`, `reverse_sign`, `use_in`); the 2026-09-09 GL-core migration added `category`, `is_require_cost_center`, `account_group_id`, and the `summary` type. The frontend followed with two renames (`account-code → chart-of-account`, 2026-09-03; `chart-of-account → chart-of-accounts`, 2026-09-08) and lives at `/config/chart-of-accounts` (list), `/config/chart-of-accounts/new` and `/config/chart-of-accounts/:id` (full-page form, replacing the old dialog; `coa-new.route.tsx`, `coa-edit.route.tsx`). Related screens: Account Grouping (`/config/account-grouping`, summarised in the [master-data landing](/en/inventory/master-data) § 3.5) maintains the account-group tree the **Account group** field points at. **Maintained by** Sysadmin / Finance. **Read by** every GL posting path and by cost-center setup.

The per-account **dimension rules** (which GL dimensions are mandatory / optional / prohibited on a JV line) are stored separately in `tb_gl_account_dimension_rule` (`api/config/:bu_code/gl-account-dimension-rules`, `requirement` = `mandatory` \| `optional` \| `prohibited`, unique per account x dimension) and are saved by the form with one create/update/delete call per dimension after the account itself is saved.

Do not confuse it with the older, product-side `tb_product_account_code_mapping` ([product/01-data-model](/en/inventory/product/01-data-model) § 2.11) — that table stores a free-text `account_code` string per product / classification level and has **no FK** to this table.

## 2. Common Tasks

| Task | Where | Notes |
|---|---|---|
| Add an account | Configuration → Chart of Accounts → **New** (full-page form, `/config/chart-of-accounts/new`) | Required: `code`, `description_1`, `category`, `nature`, `type`. Picking a **category** auto-sets **nature** (`liability` / `equity` / `revenue` → `credit`, else `debit`; `natureFor()`), and the account-group picker only lists groups of the same category. `description_2`, `account_group_id`, `is_active` optional. **Resolved since the 2026-09-22 round:** the form now sends `category`, so the earlier create-DTO gap is closed (§ 3) |
| Filter the list | Toolbar filter sheet | Multi-select by `category`, `nature` and `type` (`coa-filter-fields.ts`) plus status/search |
| Run the starter-template wizard | **COA Wizard** button on the list (`coa-wizard-modal.tsx`) | **UI stub:** the modal lists business modules (hotel rooms, restaurant F&B, banquet…) but **Apply** only shows a success toast — it calls no API and creates no accounts |
| Bulk-load from a file | API only — `POST /api/config/:bu_code/chart-of-accounts/import` (multipart `file`, optional `duplicate_mode`) | `.xlsx` or `.csv` chosen by magic bytes; all-or-nothing; no frontend button found this pass |
| Pull from Carmen GL | **Import from Carmen GL** button (`coa-import-carmen-gl-button.tsx`) → `POST …/import-from-interface/carmen-gl` | Button renders only when the BU's interface entitlement `accounting.carmen_gl` is `entitled` and the user can write; duplicate / local-only policy comes from app-config `interface_accounting_carmen_gl.sync_policy`, never from the request |
| Link to an account group | **Account group** field on the form (tree picker, `coa-tree-selector-modal.tsx`) or the Account Grouping screen's assign dialog | `account_group_id` is accepted on create **and** update (fix `ce56a37b7`) and the service enforces it (`checkAccountGroup`): group must exist, be a **leaf**, and have the **same category** as the account — see § 3 |
| Deactivate | Toggle `is_active` | Hidden from pickers; JV history unaffected |
| Delete | **Delete** action | Backend: unconditional soft-delete — no check for cost-center allow-list rows, account mappings or JV lines (see § 6). The frontend adds a *guardrail dialog* that blocks delete when `account.is_used` is true and suggests deactivating instead, but **no backend field named `is_used` exists** (grep of the gateway DTO, the micro-business service and swagger finds none), so the block is never shown — treat it as unwired |

## 3. Validation & Errors

| Symptom / Message | Cause | Action |
|---|---|---|
| `409 CHART_OF_ACCOUNTS_DUPLICATE_CODE` — "Chart of accounts code already exists" | Another non-deleted row has the same `code` (case-insensitive pre-check in `create()` / `update()`, backed by the partial unique index `chartofaccounts_code_live_u`; a lost race on insert is translated from Prisma `P2002` to the same 409) | Pick a different code or restore the soft-deleted row |
| `400 CHART_OF_ACCOUNTS_CATEGORY_REQUIRED` — "Chart of accounts category is required" | `create()` always requires `category`; `update()` requires it when the stored row still has `category = null` (rows created before 2026-09-09) and the request does not supply one | Send one of `asset`, `liability`, `equity`, `revenue`, `expense`, `statistic` |
| `404 GL_ACCOUNT_GROUP_NOT_FOUND` / `400 GL_ACCOUNT_GROUP_NOT_LEAF` / `400 GL_ACCOUNT_GROUP_CATEGORY_MISMATCH` | `account_group_id` names a missing group, a group that has children, or a group whose category differs from the account's. Also re-checked on update when only the category changes while the account stays in a group | Pick a leaf group of the same category |
| **Resolved: last round's "create DTO requires `category` the FE never sends"** | The gateway create DTO still requires `category` (`chart-of-accounts.dto.ts:36`), `reverse_sign` / `use_in` / `is_require_cost_center` default to `false` / `[]` / `false`. The new form (`coa-form.tsx`, payload built at `:128-143`) now always sends `category`, `nature`, `type` | Closed. Remaining mismatch: the form also sends `allowed_departments`, `department_required`, `allowed_dimensions`, `dimension_required`, `attributes`, `grouping_path`, which the gateway create/update DTOs do not declare (none of them appears in the DTO or the micro-business service), so the department / dimension *toggles* and allowed-lists on the form are **not persisted** by this call; only the dimension *rules* are (via `gl-account-dimension-rules`). The form also cannot set `reverse_sign`, `use_in` or `is_require_cost_center` |
| `404 CHART_OF_ACCOUNTS_NOT_FOUND` | Unknown or soft-deleted id | — |
| `400` on file import: "file is empty / missing required column / over the row limit / has failing rows (nothing was written)" | `importFile()` requires `Code`, `Description 1` (aliases `description_1`, `name`), `Nature`, `Type` columns; optional `Description 2` (`description`), `Reverse sign`, `Use in`, `Active`; max `MAX_IMPORT_ROWS = 2000`; `MAX_CODE_LENGTH = 50`; any row error aborts the whole import and returns the rows under `data.errors` (capped at `MAX_SUMMARY_ERRORS = 100`) | Fix the file and resend |
| "duplicate_mode must be one of: skip, upsert, error" | Bad `duplicate_mode` form field (default `skip`) | — |
| `400 CHART_OF_ACCOUNTS_INTERFACE_NOT_CONFIGURED` / `…_DISABLED` | No `interface_accounting_carmen_gl` app-config row, or it is disabled | Configure the interface under Application Config |
| `502 CHART_OF_ACCOUNTS_INTERFACE_REQUEST_FAILED` — "…failed with status {status}" | Carmen 4 endpoint unreachable / non-2xx; the frontend shows this one server message verbatim (`INTERFACE_REQUEST_FAILED` special case in the button) | Check token / URL |
| `400 CHART_OF_ACCOUNTS_INTERFACE_MULTI_PAGE` / `…_TOKEN_UNREADABLE` | Upstream returned more than one page (only a single page is supported); interface token cannot be decrypted (`SECRET_ENCRYPTION_KEY`) | Ops fix |

## 4. Edge Cases

- **`summary` type is now visible in the UI.** `ALTER TYPE … ADD VALUE 'summary'` ran in `20260909170000_gl_core_master`; the frontend `CHART_OF_ACCOUNT_TYPE` enum now includes `SUMMARY` (`types/chart-of-accounts.ts:13-19`), so the earlier "empty type label" edge case no longer applies.
- **Category is locked once used.** The form disables **category** when `is_used` is true and the stored category is non-null (`categoryLocked`); since the backend never sends `is_used`, in practice it is never locked.
- **Import column matching is forgiving.** Headers are normalised (case / spacing) and the parser prefers a sheet named "chart of accounts" or "account code"; `description_1` / `description_2` also accept the legacy `name` / `description` headers, so an Account-Code-era file still loads. The uploaded MIME type is never trusted — `.xlsx` is detected by the ZIP magic bytes.
- **Carmen GL mapping.** Carmen 4 has no `header` concept; header rows exist only when created locally. Nature comes from `Debit` / `Credit`; type is mapped via `CARMEN_TYPE_MAP`.
- **Sync policy is config, not request.** `on_duplicate ∈ {skip (default), upsert, error}`, `on_local_only ∈ {keep (default), delete}` — `delete` soft-deletes every live local code absent from the upstream list and reports them as `deleted_codes` (first 100). The response summary is `{ created, updated, skipped, deleted }` plus `errors[]`.
- **Deleting an account in use is not blocked.** `delete()` (`chart-of-accounts.service.ts:355`) soft-deletes unconditionally; `tb_cost_center_account` rows, `tb_account_mapping.account_code` overrides, `tb_tax_profile.chart_of_accounts_id` and JV lines keep pointing at it. Treat "cannot delete — referenced by JV" as **not enforced**.
- **`account_group` on the wire is id-only.** The detail / list responses return `account_group: { id }` with no name (frontend note in `types/chart-of-accounts.ts`); the form resolves the name from the `gl-account-groups` list.

---

## 5. Data Model (Dev)

Source: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`, line ~2934).

### 5.1 `tb_chart_of_accounts`

| Field | Prisma Type | Nullable | Description |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key. |
| `code` | `String @db.VarChar` | No | Account code, e.g. `1140-001`; ≤ 50 chars on import. |
| `description_1` | `String @db.VarChar` | No | Primary description (was `name`). |
| `description_2` | `String? @db.VarChar` | Yes | Secondary description (was `description`). |
| `nature` | `enum_chart_of_accounts_nature` | No | `debit` \| `credit`. |
| `type` | `enum_chart_of_accounts_type` | No | `header` \| `balance_sheet` \| `income_statement` \| `statistic` \| `summary`. |
| `category` | `enum_chart_of_accounts_category?` | Yes (schema) / **required by API** | `asset` \| `liability` \| `equity` \| `revenue` \| `expense` \| `statistic`. Nullable only so pre-2026-09-09 rows could migrate. |
| `reverse_sign` | `Boolean` | No | Flip sign when presented in reports (default `false`). |
| `use_in` | `enum_chart_of_accounts_use_in[]` | No | Subset of `ap`, `ar`, `gl`, `ast`; default `[]` = not yet assigned. |
| `is_require_cost_center` | `Boolean` | No | Default `false`. When `true`, every JV line on this account must carry `cost_center_id`, and if the cost center has an allow-list the account must be in it (schema comment; enforcement is in the GL JV service). |
| `account_group_id` | `String? @db.Uuid` | Yes | FK → `tb_gl_account_group` (`onDelete: NoAction`); one account : one group. |
| `is_active` | `Boolean?` | Yes | Default `true`. |
| `note`, `info`, `dimension` | — | Yes | Standard metadata. |
| `doc_version` | `Int` | No | Optimistic-lock version (default `0`). |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*`. |

**Constraints:** `@@unique([code, deleted_at])` map `chartofaccounts_code_u`; partial unique `chartofaccounts_code_live_u` on `(code) WHERE deleted_at IS NULL` (migration SQL only — Prisma cannot express it); indexes `chartofaccounts_code_idx`, `chartofaccounts_description_1_idx`, `chartofaccounts_account_group_id_idx`. Reverse relation `tb_cost_center_account[]`.

### 5.2 Enums

```
enum_chart_of_accounts_nature   { credit, debit }
enum_chart_of_accounts_type     { header, balance_sheet, income_statement, statistic, summary }
enum_chart_of_accounts_category { asset, liability, equity, revenue, expense, statistic }
enum_chart_of_accounts_use_in   { ap, ar, gl, ast }
```

## 6. Business Rules

- **Uniqueness.** `code` unique among non-deleted rows, case-insensitive at the service and DB-partial-unique; `code` and `description_1` are trimmed before checks.
- **Category is mandatory going forward.** Create always; update whenever the row has none.
- **Account-group rule.** One account : one group; group must be a leaf of the same category (`checkAccountGroup`, same rules as `GlAccountGroupService.setAccounts`).
- **Deletion guard — none server-side.** Unconditional soft-delete (`is_active: false`, `deleted_at`), no reference check; the frontend guardrail depends on an `is_used` field the API does not return.
- **Import is transactional.** Both importers validate every row first, then write in one transaction; duplicate rows *within* the same file / response are rejected ("Duplicate of row N").
- **Lifecycle.** `is_active = false` hides from pickers; `use_in = []` means "not assigned to any ledger" and is the default for imported rows unless the file says otherwise.
- **Default sort.** `code:asc, id:asc` when no `?sort=` is sent (`chart-of-accounts.service.ts:173`).
- **Optimistic lock.** Update requires the current `doc_version`.
- **Access.** Route map `config:chart-of-accounts → configuration.chart_of_accounts`; permission rows seeded (`seed.permission.data.ts:961-976`); licence feature `configuration.chart_of_accounts` (`seed.license-feature.data.ts:156`); the frontend menu entry is licence-gated (`module-list.ts:486-487`). The two import handlers use `AppIdGuard('chart-of-accounts.import')` / `('chart-of-accounts.import-from-interface.carmen-gl')`.

## 7. Cross-References

- [general-ledger](/en/inventory/general-ledger) — account groups (`tb_gl_account_group`), JV prefixes, GL periods, and the JV posting rules that consume `nature`, `use_in`, and `is_require_cost_center`.
- [cost-center](/en/inventory/master-data/cost-center) — `tb_cost_center_account` allow-list rows reference this table.
- [product/01-data-model](/en/inventory/product/01-data-model) § 2.11 — the unrelated free-text `tb_product_account_code_mapping`.
- [chart-of-account-mapping](/en/inventory/master-data/chart-of-account-mapping) — per-location x item-group account overrides must be active codes from this table.
- [tax-profile](/en/inventory/master-data/tax-profile) — optional `chart_of_accounts_id` (postable accounts only).
- [system-config/application-config](/en/inventory/system-config/application-config) — `interface_accounting_carmen_gl` key that drives the GL import.

## 8. References

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_chart_of_accounts` (line ~2934), enums (~2875-2932), `tb_gl_account_group` (~3093).
- **Migrations:** `20260820140000_add_account_code`, `20260827140000_rename_account_code_to_chart_of_accounts`, `20260909170000_gl_core_master`.
- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/master/chart-of-accounts/chart-of-accounts.service.ts` (`checkAccountGroup` `:200`, create `:226`, update `:282`, delete `:355`, `importFile` `:650`, `importFromInterfaceCarmenGl` `:847`; the Carmen 4 fetch now lives in the shared `master/carmen-gl-interface/carmen-gl-interface.ts` helper, also used by cost-center import; the unused `findAllById` handler was removed), `chart-of-accounts.import.ts` (column resolution, limits); gateway `apps/backend-gateway/src/config/config_chart-of-accounts/` (`@Controller('api/config/:bu_code/chart-of-accounts')`, import handlers `:477`, `:583`), DTO `common/dto/chart-of-accounts/chart-of-accounts.dto.ts`.
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/chart-of-accounts/*.bru` (8 requests incl. `POST-import-file-*` and `POST-import-from-interface-carmen-gl-*`).
- **Frontend:** `../carmen-frontend/routes/config/chart-of-accounts/` (`coa-form.tsx`, `coa-form-schema.ts`, `coa-filter-fields.ts`, `coa-dimension-rules.ts`, `coa-delete-guardrail-dialog.tsx`, `coa-import-carmen-gl-button.tsx`), `types/chart-of-accounts.ts`, `constant/api-endpoints.ts:60-67`.
- **E2E:** `../carmen-frontend-e2e/tests/082-chart-of-accounts.spec.ts` (16 cases; multi-select filter, export, edit nature/type, expired-licence, and Carmen GL import cases are listed as skipped in the file header), `docs/user-stories/082-chart-of-accounts.md`.
