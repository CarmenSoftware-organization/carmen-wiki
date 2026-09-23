---
title: GL Posting and the Inventory Seam
description: How a journal voucher reaches tb_gl_balance (post/void/reverse/year-end), the JV status lifecycle and gl_jv workflow, the gl_run_due cron, template generation, and the verified fact that no inventory transaction posts to the GL today.
published: true
date: '2026-09-22T18:00:00.000Z'
tags: general-ledger, inventory, costing, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# GL Posting and the Inventory Seam

> **At a Glance**
> **Verdict (backend `ef4d6f08f`, 2026-09-22):** **No inventory→GL posting exists yet.** No GRN, stock-in/stock-out, credit note, store requisition, physical count, spot check, cost-layer write or inventory period-end close creates or posts a journal voucher; `enum_gl_jv_source.inventory` is declared and never written (§ 2) &nbsp;·&nbsp; **What exists:** a self-contained ledger — `GlJvService` (draft CRUD + `gl_jv` workflow) and `GlPostingService` (post / void / reverse / close-year / reopen-year / run-due) writing `tb_gl_balance` under a per-(BU, fiscal year) advisory lock (§ 3–5) &nbsp;·&nbsp; **Cron:** `gl_run_due` in `micro-cronjobs` posts due `scheduled` vouchers and fires due auto-reversals per BU; it does **not** generate JV templates (§ 6) &nbsp;·&nbsp; **Calendars:** `tb_gl_period` (13/yr) and `tb_inventory_period` (12/yr) are unrelated tables with no code path between them (§ 8) &nbsp;·&nbsp; **UI / E2E:** none (landing § 4)

## 1. Scope

This page covers the General Ledger only at the seam with inventory, per the owner decision recorded on the [General Ledger landing](/en/inventory/general-ledger) § 1. It answers five questions a developer or tester on the inventory side will ask:

1. Does anything in inventory post to the GL today? (§ 2 — no)
2. What does `gl-posting` do to `tb_gl_balance`, so that a future inventory poster knows the contract? (§ 3)
3. What is the JV status lifecycle and the `gl_jv` workflow? (§ 4–5)
4. What does the `gl_run_due` cron trigger, and what are the `generate` / `generate-all-due` requests? (§ 6–7)
5. Is `tb_gl_period` the same thing as the inventory period? (§ 8 — no)

GL master data, budgets, templates as such, and the trial balance are out of scope; see the landing page § 1.1 for where they live.

## 2. No inventory→GL posting exists yet

### 2.1 Greps run (backend `ef4d6f08f`, 2026-09-22)

```
# any GL identifier inside the inventory and procurement services
grep -rn -E "gl[-_]posting|gl[-_]jv|tb_gl_|GlPosting|GlJv|journal" \
  apps/micro-business/src/inventory apps/micro-business/src/procurement
→ 0 hits

# every file outside gl/ that names a GL table or service
grep -rl -E "tb_gl_|GlPosting|gl_jv|GlJv" apps/micro-business/src apps/backend-gateway/src | grep -v "/gl"
→ app.module.ts (module registration)
  authen/tenant_seed/**            (seed types / specs)
  common/activity/activity-registry.ts   (comment: `jv` deliberately NOT in the map, :763)
  common/enrichment/enrichment.map.generated.ts
  master/workflows/workflows.service.ts  (gl_jv → tb_gl_jv_header mapping, :780 :905 :979 :1071)
  master/workflows/workflow-stage-role.helper.ts (:12-15, :44)
  master/running-code/const/running-code.const.ts (:113, jv_no numbering note)
  backend-gateway config_gl-jv-prefixes/**, route-config.ts, route-application.ts

# who sets a voucher's source
grep -rn "enum_gl_jv_source\." apps/micro-business/src --include='*.ts'
→ gl-jv.service.ts:214          source: enum_gl_jv_source.manual
  gl-posting.service.ts:571     source: enum_gl_jv_source.reversal
  gl-posting.service.ts:909     source: enum_gl_jv_source.closing
  gl-posting.service.ts:1116    source: enum_gl_jv_source.closing
  gl-jv-template.service.ts:777 source: enum_gl_jv_source[template.template_type]   (recurring|allocation|amortize)

# does the inventory period-end read the GL calendar?
grep -rn -iE "tb_gl_period|gl_period" apps/micro-business/src/inventory
→ 0 hits
```

### 2.2 What that means

| Inventory event | Writes a voucher? | Evidence |
|---|---|---|
| GRN commit (incl. FOC-to-stock, extra cost → landed cost) | No | 0 hits in `procurement/`; GRN service touches `tb_inventory_transaction*` and cost layers only |
| Credit note (return-to-stock / cost revaluation) | No | same grep; the "AP posting" on [purchase-order/credit-note](/en/inventory/purchase-order/credit-note) remains unconfirmed |
| Stock-in / stock-out `PATCH commit` | No | 0 hits in `inventory/stock-in`, `inventory/stock-out` |
| Store requisition issue / transfer | No | 0 hits in `inventory/store-requisition` |
| Physical count / spot check variance | No | 0 hits in `inventory/physical-count*`, `inventory/spot-check*` |
| Cost-layer write (`tb_inventory_transaction_cost_layer`) | No | 0 hits in `inventory/inventory-transaction`, `inventory/costing` |
| Inventory period-end close (`POST /api/:bu_code/period-ends`) | No | `period-end.close-transaction.helper.ts:80,195,210` reads/writes `tb_inventory_period` only; never `tb_gl_period` or `tb_gl_jv_header` |

`enum_gl_jv_source` (schema `:4724`) reserves `ap`, `ar`, `inventory`, `asset` and `interface`, and `tb_gl_jv_header.source_ref_type` / `source_ref_id` (schema `:4741`) exist to point back at a source document. Both are **forward-looking placeholders**: nothing populates them. `GlPostingService`'s header comment says it is "separate from `GlJvService` so AP/AR can post without going through the JV DTO" (`gl-posting.service.ts:68`) — again a stated intent, not an implemented caller.

**carmen/docs drift.** `../carmen/docs/app/inventory-management/inventory-transactions/BR-inventory-transactions.md:21,31,143,162,214` ("automatic integration with general ledger for all inventory movements", "variance posted to designated GL variance accounts", "return posts to GL (debit AP, credit Inventory)"), `../carmen/docs/inventory-management/period-end-process.md:135-136` ("GL posting verification", "period end journal entries") and `../carmen/docs/store-requisitions/SR-API-JournalEntry-Endpoints.md` describe behaviour that HEAD does not implement. The e2e persona doc `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-09-end-period-close.md:65,200` repeats the same claim ("Finalized = variance adjustments posted to the General Ledger"); the implemented period-end gate is the physical-count status, not a GL posting ([inventory/period-end](/en/inventory/inventory/period-end)).

## 3. What `gl-posting` does

`apps/micro-business/src/gl/gl-posting/` is the **single writer of `tb_gl_balance`** (`gl-posting.service.ts:68`). The gateway module `apps/backend-gateway/src/application/gl-posting/` exposes it as `api/:bu_code/gl-posting` (`gl-posting.controller.ts:63`) behind `KeycloakGuard` + `PermissionGuard`, resource `accounting.gl` (`:52`). RPC contract: `packages/rpc-contract/src/contracts/gl-posting.ts` (`post`, `void`, `reverse`, `close-year`, `reopen-year`, `run-due`).

### 3.1 Routes

| Route | Permission | Body | Service |
|---|---|---|---|
| `POST api/:bu_code/gl-posting/:gl_jv_id/post` (`:128`) | `accounting.gl:post` | `{ post_at?: ISO datetime }` | `GlPostingService.post` (`:293`) |
| `POST .../:gl_jv_id/void` (`:185`) | `accounting.gl:void` | `{ reason }` (required) | `voidJv` (`:414`) |
| `POST .../:gl_jv_id/reverse` (`:233`) | `accounting.gl:reverse` | `{ jv_date }` | `reverse` (`:507`); gateway additionally computes `can_post = hasAllPermissions(accounting.gl:post)` (`:115`) |
| `POST .../recalculate` (`:296`) | `accounting.gl:recalculate` | `{ fiscal_year }` | `GlBalanceService.recalculate` (`gl-balance.service.ts:60`) — rebuilds every `tb_gl_balance` row of the year from posted vouchers, preserving period 1 openings |
| `POST .../close-year` (`:349`) | `accounting.gl:close_year` | `{ fiscal_year }` | `closeYear` (`:698`) |
| `POST .../reopen-year` (`:403`) | `accounting.gl:close_year` | `{ fiscal_year }` | `reopenYear` (`:1096`) |

Bruno: `_uncategorized/gl-posting/POST-{post,void-jv,reverse,recalculate,close-year,reopen-year}-gl-posting.bru`. Note that every Bruno sample response in these folders is the generic `{ "data": { "id": ... }, "status": 201 }` placeholder; the real envelopes are `{ id, jv_status }` (post/void), `{ id, jv_status, reversal_of_jv_id }` (reverse), `{ fiscal_year, closing_jv_id, carried_rows }` (close-year) and `{ posted, reversed, skipped, failed[] }` (run-due).

### 3.2 Post

```
post(jvId, postAt?):
  header = tb_gl_jv_header + tb_gl_jv_detail (deleted_at null)
  require jv_status in {draft, in_review, scheduled}            -- else GL_JV_IMMUTABLE
  allowClosed = gl_setting.allow_post_to_closed_period == true
  TRANSACTION:
    period = resolvePeriod(jv_date, is_adjustment)               -- :152
        -- is_adjustment=false → period_no ≤ 12 whose [start_at,end_at] covers jv_date
        -- is_adjustment=true  → period 13 (shares the last instant of period 12)
    if none → GL_PERIOD_NOT_OPEN
    pg_advisory_xact_lock('gl-balance:<bu>:<fiscal_year>')       -- :131, FIRST statement
    if period.status != open and !allowClosed → GL_PERIOD_NOT_OPEN
    validateJvLines(lines, header.exchange_rate)                 -- re-validated at post, :335
    totals = Σ base_debit, Σ base_credit
    if postAt > now:
        header ← { jv_status: scheduled, post_at, total_* }      -- ledger untouched
        return { id, jv_status: scheduled }
    header ← { jv_status: posted, gl_period_id, posted_at, posted_by_id,
               post_at: null, total_*,
               reverse_at: is_auto_reverse && !reverse_at ? firstDayOfNextPeriod : reverse_at }
    applyBalanceDeltas(period, groupDeltas(lines))               -- :188
    return { id, jv_status: posted }
```

`validateJvLines` (`gl-jv/gl-jv.validation.ts:39`): every line is single-sided (`debit > 0 XOR credit > 0`), ≥ 2 lines and `Σ base_debit == Σ base_credit` (`gl-jv.logic.ts`), every account exists, is active and is not `header` / `summary` type, `is_require_cost_center` accounts carry a `cost_center_id`, and every cost center named is active. Errors: `GL_JV_NOT_BALANCED`, `GL_ACCOUNT_NOT_POSTABLE`, `GL_COST_CENTER_REQUIRED`, `GL_COST_CENTER_NOT_ALLOWED`.

### 3.3 Balance rules (`gl-balance.logic.ts:78 planBalanceWrites`)

For each (`cost_center_id` or nil-uuid, `chart_of_accounts_id`) key touched by the voucher, within the fiscal year:

```
net = Δdebit − Δcredit
rows = existing tb_gl_balance rows of this key in the fiscal year
1. row for period N exists      → bump: debit += Δdebit, credit += Δcredit
2. row does not exist           → insert: opening = closing(latest existing row BEFORE N)  or 0
                                   where closing(row) = opening + debit − credit   (never stored)
3. every existing row AFTER N   → opening += net
Rows after N that do not exist are NOT pre-created (rule 2 derives them later).
```

Rule 3 is why every ledger mutation takes the advisory lock first. Void and reverse re-use the planner with `negateDelta` (`:125`) so later periods' openings are shifted back too.

### 3.4 Void and reverse

| | Void (`:414`) | Reverse (`:507`) |
|---|---|---|
| Precondition | `jv_status == posted` and `reversed_by_jv_id` null; `reason` non-empty | `jv_status == posted` and `reversed_by_jv_id` null; `gl_setting.reversal_prefix_id` set and active; target period of `jv_date` open (or `allow_post_to_closed_period`) |
| Period used | the one it was posted into (`gl_period_id`), not `jv_date` re-resolved | `jv_date` supplied by the caller |
| Ledger effect | negated deltas applied to `tb_gl_balance` | original stays; a mirror voucher (`source = reversal`, debit↔credit swapped, `reversal_of_jv_id`) is created via `createInternal` and posted through `post()` when `can_post`, else left as `draft` |
| Header result | `jv_status = void`, `void_at/by/reason`; `total_*` unchanged | original gets `reversed_by_jv_id` after the post succeeds; partial unique `gljvheader_reversed_by_u` blocks a second reversal (→ `GL_JV_IMMUTABLE`) |

### 3.5 Year-end (`closeYear :698`, `assertYearClosable :742`, `reopenYear :1096`)

Preconditions: all 12 regular `tb_gl_period` rows of the year exist and are `closed`/`locked`, period 13 is `open`, no voucher of the year is in `draft`/`in_review`/`scheduled` (`GL_YEAR_CLOSE_PENDING_JV`), period 1 of year+1 exists, `gl_setting.retained_earnings_account_id` and `auto_jv_prefix_id` set. Then: build a closing voucher (`source = closing`, dated at period 13's instant, one retained-earnings line **per cost center**), post it through `post()`, carry asset/liability/equity closings into period 1 of year+1, lock every period. Runs as three consecutive transactions, not one (`:683-688`, deliberate deviation from the spec). `reopenYear` withdraws the carried openings and is refused once the next year has activity.

### 3.6 The DB guard

Migration `20260914030000_gl_core_jv_ledger:151-231` installs `gl_jv_posted_guard` (`BEFORE UPDATE/DELETE` on `tb_gl_jv_header` and `tb_gl_jv_detail`; body re-created with an explicit `search_path` in `20260915010000_fix_gl_jv_guard_search_path`). Once a header is `posted` or `void`: hard delete raises `GL_JV_IMMUTABLE`; the only status transition allowed is `posted → void`; `deleted_at` is in the compared column set so **soft-delete is impossible**; only `reverse_at`, `reversed_by_jv_id`, `void_*`, `updated_*`, `doc_version`, `info`, `note` (header) and `updated_*`/`doc_version`/`info`/`note`/denormalised names (detail) may change. Prisma cannot see triggers — a tenant schema created from `schema.prisma` alone will lack it (schema comment `:4738-4740`).

## 4. JV status lifecycle

`enum_jv_status` (schema `:140`; `in_review`, `scheduled`, `void` added by `20260914030000_gl_core_jv_ledger:23-25`):

```
                 submit (workflow configured)            final approve, post_at empty/past
  draft ───────────────────────────────► in_review ─────────────────────────────────► posted
    ▲  ▲          submit (no gl_jv workflow) ─────────────────────────────────────────► posted
    │  │                                        final approve, post_at future
    │  │                                   in_review ───────────────────────► scheduled
    │  └──── reject (in_review → draft, reason → note)                            │
    │  └──── unschedule (scheduled → draft; must be re-reviewed)                  │
    │  └──── run-due: scheduled voucher that no longer validates → draft (+ tb_activity row)
    │                                                        run-due / post: post_at ≤ now
    │                                                    scheduled ───────────────► posted
    │
    └─ delete: draft only (soft-delete header + details, drop tb_gl_jv_template_run row)

  posted ── void (reason) ──► void                      (terminal; ledger backed out)
  posted ── reverse(jv_date) ─► posted + new voucher {source: reversal, reversal_of_jv_id}
  posted ── is_auto_reverse ─► reverse fired by run-due at reverse_at (default: first day of next period)
```

| Transition | Code | Guard |
|---|---|---|
| create → `draft` | `GlJvService.create` `:211` → `createInternal` `:119` | prefix active; lines validated; `jv_no` from `generateJvNo` (running code, prefix stored separately) |
| `draft` → `in_review` / `posted` | `submit` `:341` | lines re-validated; `resolveJvWorkflowId` `:321` picks the first active `tb_workflow` with `workflow_type = gl_jv`; **none configured → posts immediately on the caller's session** (spec § 4.1) |
| `in_review` → `in_review` / `posted` / `scheduled` | `approve` `:421` | `WorkflowOrchestratorService.buildApproveWorkflow` decides `isFinalApproval`; final → `GlPostingService.post(id, post_at)` |
| `in_review` → `draft` | `reject` `:478` | reason stored on `note` |
| `scheduled` → `draft` | `unschedule` `:532` | back to draft, not to review — the approval was for a posting that never happened |
| `draft` update / delete | `update` `:232`, `delete` `:278` | refused for `posted`/`void` (update) and anything but `draft` (delete) before the trigger would |

## 5. The `gl_jv` workflow

- `enum_workflow_type` += `gl_jv` (`20260914030000_gl_core_jv_ledger:26`; schema `:276`). `workflows.service.ts:1071` maps it to `tb_gl_jv_header`; `:780`, `:905`, `:979` add it to the pending-document lookups (with `department = null`, since a JV has no department).
- Stage roles: `workflow-stage-role.helper.ts:44` — `gl_jv: [create, approve]`. The file's header (`:12-15`) states that `gl_jv` "has no configured workflow in any tenant yet" — its stage-role row is hard-coded rather than derived from data.
- Routing: `gl-jv/workflow/gl-jv-workflow.mapper.ts` builds the `WorkflowDocument` with `requestor_id = created_by_id`, `department = null`, `navigation_request_data.total_amount = total_debit` (amount-based stage routing works; department-based does not apply).
- Gateway `api/:bu_code/gl-jv` (`gl-jv.controller.ts:62`) carries **no `@Permission`** on any route — `KeycloakGuard` only. `submit` (`:301`), `approve` (`:345`), `reject` (`:397`), `unschedule` (`:447`) are gated by the workflow engine per stage; draft CRUD (`:131` list, `:83` get, `:177` create, `:215` patch, `:259` delete) is forgiven by `WORKFLOW_GATED_ACTIONS` (`permission.route-map.ts:346-354`). Licence feature `accounting.gl` must be on the BU.
- Bruno: `_uncategorized/gl-jv/` — `GET-list`, `GET-by-id`, `POST-create`, `PATCH-update`, `DELETE-remove`, `POST-submit`, `POST-approve`, `POST-reject`, `POST-unschedule`, `POST-run-due-gl-jv-gl-jv` (UI button route), `POST-run-due-gl-jv-gl` (internal bridge).

## 6. The `gl_run_due` cron

| | Value | Source |
|---|---|---|
| Job type | `gl_run_due` | `micro-cronjobs/internal/executor/executor.go:84` |
| Job config | `{ "bu_codes": [...], "user_id": "<uuid v4>" }` — `user_id` is the actor stamped on every voucher the run posts/reverses because the platform has no system user | `internal/model/cronjob.go:141-149` |
| What it calls | `POST {GATEWAY_URL}/api/internal/gl/run-due`, header `x-internal-token: {INTERNAL_JOB_TOKEN}`, body `{ bu_code, user_id }`, **once per BU, sequentially** | `gl_run_due.go:55-87` |
| Timeout | HTTP client 120 s **per BU**; the scheduler wraps the whole job in `timeout_seconds` (default 300) → operators size `timeout_seconds ≥ len(bu_codes) × 120` | `gl_run_due.go:37-41`, `README.md:254` |
| Failure semantics | one BU failing does not stop the others; failures are joined and the job is recorded failed. Per-voucher failures inside a BU are logged as warnings, not job failures | `gl_run_due.go:77-86`, `:122-128` |
| Gateway side | `GlJvInternalController` `api/internal/gl/run-due` (`gl-jv-internal.controller.ts:24-39`), excluded from Swagger, guarded by `InternalJobGuard` (`auth/guards/internal-job.guard.ts:41`): fail-closed unless `INTERNAL_JOB_API_ENABLED` and `INTERNAL_JOB_TOKEN` are set and the header matches (constant-time compare). Body schema `GlJvRunDueInternalSchema` (`common/dto/gl-jv/gl-jv-run-due-internal.dto.ts:8-23`): `bu_code`, `user_id` (uuid v4), optional `now` (acceptance runs only; logged at warn level) | |
| Same work, human door | `POST api/:bu_code/gl-jv/run-due` (`gl-jv.controller.ts:496`, the "Run due jobs" button; no static permission) | |
| Service | both call `GlJvService.runDue` (gateway `gl-jv.service.ts:214`) → RPC `gl-posting.run-due` → `GlPostingService.runDueJobs(now)` (`:1251`) | |

What one run does (`runDueJobs :1251`):

```
posted   = runDueSchedules(now):      for each tb_gl_jv_header {jv_status: scheduled, post_at ≤ now} order by post_at
                                        post(id) ; on error → releaseToDraft(id, reason)   -- :1353, tb_activity row entity_type 'gl_jv'
reversed = runDueAutoReversals(now):  for each {jv_status: posted, is_auto_reverse, reverse_at ≤ now, reversed_by_jv_id null}
                                        period = resolvePeriod(reverse_at) ; not open → skipped++ (not failed)
                                        reverse(id, reverse_at, can_post = true) ; on error → failed[]
return { posted, reversed, skipped, failed: [{ id, reason }] }
```

**It does not generate JV templates.** `grep -rn -i "generate-all-due\|generateAllDue\|jv-template" micro-cronjobs --include='*.go'` → 0 hits. Template generation is § 7 and has no scheduled caller anywhere.

## 7. JV template generation (`generate` / `generate-all-due`)

Documented here only because the landing page names the endpoints and the Bruno sample responses are misleading placeholders.

| Request | Route / permission | Body | Real response (`gl-jv-template.service.ts`) |
|---|---|---|---|
| `_uncategorized/gl-jv-templates/POST-generate-gl-jv-templates.bru` | `POST api/:bu_code/gl-jv-templates/:gl_jv_template_id/generate` (`gl-jv-templates.controller.ts:377`), `accounting.gl.jv_template:generate` | `{ "gl_period_id": "<uuid>" }` | `{ jv_id, jv_no, gl_period_id, amount_total }` (`:814-818`) |
| `_uncategorized/gl-jv-templates/POST-generate-all-due-gl-jv-templates.bru` | `POST api/:bu_code/gl-jv-templates/generate-all-due` (`:335`), same permission | `{ "gl_period_id": "<uuid>" }` | `{ generated: [{template_id, jv_id, jv_no}], skipped: [{template_id, reason: already_run \| not_due}], failed: [{template_id, code}] }` (`:865-885`) |

Rules (`generate :707`, `generateAllDue :833`): the target `tb_gl_period` must be `open` and `period_no ≤ 12`; the template must be active and its `from`–`to` range must cover the period (`GL_JV_TEMPLATE_PERIOD_OUT_OF_RANGE`); `recurring` templates are due only when `periodIndex(from, target) % frequency_months == 0` (`gl-jv-template.generate.logic.ts:68-86`, else `GL_JV_TEMPLATE_NOT_DUE`); `amortize` templates require every period of the range to exist (`GL_JV_TEMPLATE_PERIODS_INCOMPLETE`). The generated voucher is a **`draft`** created through `GlJvService.createInternal` with `source = enum_gl_jv_source[template_type]`, `template_id`, `jv_date = period.start_at`; the same transaction inserts `tb_gl_jv_template_run` whose unique (`template_id`, `gl_period_id`) makes a second generation for the period a 409 `GL_JV_TEMPLATE_ALREADY_RUN`. Deleting the draft removes the run row so the period can be generated again (`gl-jv.service.ts:278`). `generateAllDue` runs one transaction per template and never stops at the first failure.

## 8. `tb_gl_period` vs `tb_inventory_period`

They are two independent calendars. Nothing joins them.

| | `tb_gl_period` (schema `:3128`) | `tb_inventory_period` (schema `:1229`; renamed from `tb_period` by `20260916141000_rename_tb_period_to_tb_inventory_period`) |
|---|---|---|
| Owner | `gl/gl-period/` — `GlPeriodService` | `inventory/inventory-period/`, `inventory/period-end/` |
| Rows per year | 13 (`createYear :70` from `gl_setting.fiscal_year_start_month`; period 13 has `start_at = end_at = end_at` of period 12) | 12 (`period` `YYMM`, `fiscal_year`, `fiscal_month` 1–12) |
| Status enum | `enum_gl_period_status { open, closed, locked }` | `enum_period_status { open, closed, locked }` |
| Close rule | `close :110` — previous period must not be `open` (`GL_PERIOD_SEQUENCE`); `reopen :160` — refused if any period of the year is `locked` or a later period is not `open`; year-end `closeYear` locks all 13 | `POST /api/:bu_code/period-ends` — blocking-document + physical-count gates, writes `close`/`open` inventory transactions and (average BUs) `tb_inventory_period_snapshot` ([inventory/period-end](/en/inventory/inventory/period-end)) |
| Relations | `tb_gl_jv_template_run.gl_period_id`; `tb_gl_jv_header.gl_period_id` (set at post); `tb_gl_balance.gl_period_id` | `tb_inventory_period_snapshot`, `tb_inventory_transaction_cost_layer.at_period`, `tb_physical_count_period`, `tb_inventory_period_comment` |
| Cross-reference | none — no FK, no service call, no shared config key (`grep -rln "tb_gl_period\|gl_period_id" apps/micro-business/src apps/backend-gateway/src | grep -v "/gl/\|/gl-\|config_gl"` → 0 files) | none |
| Gateway route | `api/config/:bu_code/gl-periods` (`config_gl-periods.controller.ts:49`; Keycloak + `AppIdGuard`, no `@Permission`) | `api/:bu_code/inventory-periods`, `api/:bu_code/period-ends` (`period-end.controller.ts:72-280`) |

Consequence for testers: closing the inventory period does **not** close, lock or validate anything in the GL, and vice-versa; a voucher can be posted into a GL period whose matching inventory month is already closed, and inventory can keep moving in a month whose GL period is `locked`.

## 9. Edge Cases

| # | Scenario | Expected today | Source |
|---|---|---|---|
| 1 | Tester looks for a JV after committing a GRN / stock-out / credit note | None exists; `tb_gl_jv_header` count unchanged | § 2 |
| 2 | Inventory period-end close on a BU whose GL periods are all `locked` | Close succeeds; GL untouched | § 8 |
| 3 | `POST gl-posting/:id/post` with `post_at` in the future | Header becomes `scheduled`, `tb_gl_balance` untouched; run-due posts it later | `gl-posting.service.ts:352-365` |
| 4 | Scheduled voucher whose account was deactivated before `post_at` | Run-due returns it to `draft` and writes a `tb_activity` row (`entity_type = gl_jv`, `action = other`) | `:1268-1299`, `:1353` |
| 5 | Auto-reversal due but the next period is not `open` | Counted in `skipped`, retried on the next run; not an error | `:1300-1352` |
| 6 | Void a voucher that was already reversed | `GL_JV_IMMUTABLE` | `:431` |
| 7 | Reverse a voucher twice (race) | Second loses on `gljvheader_reversed_by_u` → `GL_JV_IMMUTABLE` | `:507` header comment |
| 8 | Post into a `closed` period | `GL_PERIOD_NOT_OPEN` unless `gl_setting.allow_post_to_closed_period = true` | `:331` |
| 9 | Regular-dated voucher on the last instant of period 12 | Resolves to period 12; period 13 is reachable only with `is_adjustment = true` | `:152-176` |
| 10 | Submit a draft on a BU with no active `gl_jv` workflow | Posted immediately on the submitter's session — no review | `gl-jv.service.ts:373-375` |
| 11 | `UPDATE tb_gl_jv_header SET deleted_at = now()` on a posted voucher (raw SQL) | Trigger raises `GL_JV_IMMUTABLE` | `20260914030000…:151-231` |
| 12 | New tenant schema created from `schema.prisma` without running the migrations | `gl_jv_posted_guard` is missing; posted vouchers are mutable | schema comment `:4738-4740` |
| 13 | `gl_run_due` job with 3 BUs and default `timeout_seconds = 300` | Third BU may be cut off by the job context (120 s × 3 > 300) | `gl_run_due.go:37-41` |
| 14 | `POST /api/internal/gl/run-due` with the right token but `INTERNAL_JOB_API_ENABLED` unset | 403 "Internal job API is disabled" (same message for every failure path) | `internal-job.guard.ts:41-57` |
| 15 | `generate-all-due` for period 13 or a `closed` period | Whole call fails `GL_PERIOD_NOT_OPEN` (not a 200 with everything in `failed`) | `gl-jv-template.service.ts:848-852` |
| 16 | Two concurrent postings into the same fiscal year | Serialised by `pg_advisory_xact_lock('gl-balance:<bu>:<year>')` taken before any read | `:131`, `gl-balance.logic.ts:59-62` |

## 10. Recommendations

1. **Do not write inventory test scenarios that assert GL postings** — for GRN, CN, SR, adjustments, counts or period-end — until a caller of `GlJvService.createInternal` with `source = inventory` appears in `apps/micro-business/src/inventory` or `procurement`. Re-run the § 2.1 greps first; if they light up, this page and the GRN / credit-note / period-end pages need a new "GL posting" section.
2. **When inventory posting is built**, it should go through `createInternal` inside the caller's transaction with `source_ref_type` / `source_ref_id` set, and then `GlPostingService.post` — not write `tb_gl_balance` directly (§ 3, single-writer rule). The planned resolution of `tb_inventory_period` → `tb_gl_period` (12 vs 13 periods, different `start_at` if `fiscal_year_start_month ≠ 1`) will need an explicit mapping; none exists.
3. **Ops:** size `timeout_seconds` on the `gl_run_due` cron row to `len(bu_codes) × 120` and set `INTERNAL_JOB_API_ENABLED` / `INTERNAL_JOB_TOKEN` on the gateway, or the job fails closed with a 403 on every BU.
4. **Tenant provisioning:** after creating a new BU schema, verify `gl_jv_posted_guard_header` / `_detail` triggers exist (`SELECT tgname FROM pg_trigger WHERE tgname LIKE 'gl_jv_posted_guard%'`) — Prisma will not create them.
5. **Docs hygiene:** treat every GL claim in `../carmen/docs` (§ 2.2) and in the e2e persona doc `tx-09-end-period-close.md` as aspirational; the coordinator's drift log for 2026-09-22 carries the list.

## 11. References

- **Backend (micro-business):** `../carmen-turborepo-backend-v2/apps/micro-business/src/gl/gl-posting/` (`gl-posting.service.ts`, `gl-balance.logic.ts`, `gl-posting.controller.ts`), `gl/gl-jv/` (`gl-jv.service.ts`, `gl-jv.validation.ts`, `gl-jv.logic.ts`, `gl-jv.running-code.ts`, `workflow/gl-jv-workflow.mapper.ts`), `gl/gl-jv-template/` (`gl-jv-template.service.ts`, `gl-jv-template.generate.logic.ts`, `gl-jv-template.validation.ts`), `gl/gl-period/gl-period.service.ts`, `gl/gl-balance/gl-balance.service.ts`; `master/workflows/workflows.service.ts`, `master/workflows/workflow-stage-role.helper.ts`; `inventory/period-end/period-end.close-transaction.helper.ts` (the inventory side that does not call the GL).
- **Backend (gateway):** `apps/backend-gateway/src/application/gl-posting/gl-posting.controller.ts`, `application/gl-jv/gl-jv.controller.ts`, `application/gl-jv/gl-jv-internal.controller.ts`, `application/gl-jv-templates/gl-jv-templates.controller.ts`, `auth/guards/internal-job.guard.ts`, `common/dto/gl-jv/gl-jv-run-due-internal.dto.ts`, `libs/config.env.ts:227-228,419-420`; `packages/rpc-contract/src/contracts/gl-posting.ts`.
- **Prisma:** `packages/prisma-shared-schema-tenant/prisma/schema.prisma` (`enum_jv_status :140`, `enum_workflow_type :276`, `tb_inventory_period :1229`, `enum_gl_period_status :2899`, `tb_gl_period :3128`, `tb_gl_jv_detail :4496`, `tb_gl_balance :4552`, `tb_gl_jv_template_run :4708`, `enum_gl_jv_source :4724`, `tb_gl_jv_header :4741`); migrations `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path`, `20260915043038_gl_core_budget_template`, `20260916141000_rename_tb_period_to_tb_inventory_period`.
- **Permissions / licence:** `packages/prisma-shared-schema-platform/prisma/permission.route-map.ts:57-61,346-354`, `seed.permission.data.ts:1612-1637,1674-1698`, `seed.license-feature.data.ts:60,100,108`.
- **Cron:** `../micro-cronjobs/internal/executor/gl_run_due.go`, `internal/executor/executor.go:84`, `internal/model/cronjob.go:141-149`, `README.md:254`.
- **API contracts:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/{gl-posting,gl-jv,gl-jv-templates}/*.bru`.
- **Frontend / E2E:** none — see [General Ledger](/en/inventory/general-ledger) § 4.
- **Related wiki pages:** [inventory/period-end](/en/inventory/inventory/period-end), [system-config/period](/en/inventory/system-config/period), [costing](/en/inventory/costing) § 1 (the earlier "no GL posting" finding this page confirms), [system-config/workflow](/en/inventory/system-config/workflow) (`enum_workflow_type`).
