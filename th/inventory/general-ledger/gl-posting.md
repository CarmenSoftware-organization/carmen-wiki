---
title: GL Posting และรอยต่อกับ Inventory
description: journal voucher ไปถึง tb_gl_balance ได้อย่างไร (post/void/reverse/year-end), lifecycle สถานะ JV และ workflow gl_jv, cron gl_run_due, การสร้าง template และข้อเท็จจริงที่ยืนยันแล้วว่าไม่มีธุรกรรม inventory ใด post เข้า GL วันนี้
published: true
date: '2026-09-23T01:30:00.000Z'
tags: general-ledger, inventory, costing, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# GL Posting และรอยต่อกับ Inventory

> **At a Glance**
> **ข้อสรุป (backend `ef4d6f08f`, 2026-09-22):** **ยังไม่มีการ post จาก inventory→GL** ไม่มี GRN, stock-in/stock-out, credit note, store requisition, physical count, spot check, การเขียน cost layer หรือการปิดงวด inventory ใดที่สร้างหรือ post journal voucher; `enum_gl_jv_source.inventory` ถูกประกาศไว้และไม่เคยถูกเขียน (§ 2) &nbsp;·&nbsp; **สิ่งที่มี:** ledger ที่สมบูรณ์ในตัว — `GlJvService` (CRUD ของ draft + workflow `gl_jv`) และ `GlPostingService` (post / void / reverse / close-year / reopen-year / run-due) เขียน `tb_gl_balance` ภายใต้ advisory lock ต่อ (BU, ปีการเงิน) (§ 3–5) &nbsp;·&nbsp; **Cron:** `gl_run_due` ใน `micro-cronjobs` post voucher `scheduled` ที่ถึงกำหนดและ fire auto-reversal ที่ถึงกำหนดต่อ BU; มัน **ไม่** สร้าง JV template (§ 6) &nbsp;·&nbsp; **ปฏิทิน:** `tb_gl_period` (13/ปี) และ `tb_inventory_period` (12/ปี) เป็นตารางที่ไม่เกี่ยวข้องกัน ไม่มี code path ระหว่างกัน (§ 8) &nbsp;·&nbsp; **UI / E2E:** ไม่มี (หน้าแรก § 4)

## 1. ขอบเขต

หน้านี้ครอบคลุม General Ledger เฉพาะที่รอยต่อกับ inventory ตามการตัดสินใจของเจ้าของที่บันทึกไว้ที่ [หน้าแรก General Ledger](/th/inventory/general-ledger) § 1 มันตอบห้าคำถามที่นักพัฒนาหรือ tester ฝั่ง inventory จะถาม:

1. วันนี้มีอะไรใน inventory post เข้า GL ไหม? (§ 2 — ไม่มี)
2. `gl-posting` ทำอะไรกับ `tb_gl_balance` เพื่อให้ผู้ post จาก inventory ในอนาคตรู้ contract? (§ 3)
3. lifecycle สถานะ JV และ workflow `gl_jv` เป็นอย่างไร? (§ 4–5)
4. cron `gl_run_due` trigger อะไร และ request `generate` / `generate-all-due` คืออะไร? (§ 6–7)
5. `tb_gl_period` คือสิ่งเดียวกับงวด inventory ไหม? (§ 8 — ไม่ใช่)

GL master data, budget, template ในตัวมันเอง และ trial balance อยู่นอกขอบเขต; ดูหน้าแรก § 1.1 ว่าอยู่ที่ไหน

## 2. ยังไม่มีการ post จาก inventory→GL

### 2.1 grep ที่รัน (backend `ef4d6f08f`, 2026-09-22)

```
# identifier ของ GL ใด ๆ ภายใน service inventory และ procurement
grep -rn -E "gl[-_]posting|gl[-_]jv|tb_gl_|GlPosting|GlJv|journal" \
  apps/micro-business/src/inventory apps/micro-business/src/procurement
→ 0 hits

# ทุกไฟล์นอก gl/ ที่เอ่ยชื่อตารางหรือ service ของ GL
grep -rl -E "tb_gl_|GlPosting|gl_jv|GlJv" apps/micro-business/src apps/backend-gateway/src | grep -v "/gl"
→ app.module.ts (การลงทะเบียน module)
  authen/tenant_seed/**            (type / spec ของ seed)
  common/activity/activity-registry.ts   (comment: `jv` ตั้งใจ NOT อยู่ใน map, :763)
  common/enrichment/enrichment.map.generated.ts
  master/workflows/workflows.service.ts  (การ map gl_jv → tb_gl_jv_header, :780 :905 :979 :1071)
  master/workflows/workflow-stage-role.helper.ts (:12-15, :44)
  master/running-code/const/running-code.const.ts (:113, หมายเหตุการออกเลข jv_no)
  backend-gateway config_gl-jv-prefixes/**, route-config.ts, route-application.ts

# ใครตั้งค่า source ของ voucher
grep -rn "enum_gl_jv_source\." apps/micro-business/src --include='*.ts'
→ gl-jv.service.ts:214          source: enum_gl_jv_source.manual
  gl-posting.service.ts:571     source: enum_gl_jv_source.reversal
  gl-posting.service.ts:909     source: enum_gl_jv_source.closing
  gl-posting.service.ts:1116    source: enum_gl_jv_source.closing
  gl-jv-template.service.ts:777 source: enum_gl_jv_source[template.template_type]   (recurring|allocation|amortize)

# การปิดงวด inventory อ่านปฏิทิน GL ไหม?
grep -rn -iE "tb_gl_period|gl_period" apps/micro-business/src/inventory
→ 0 hits
```

### 2.2 ความหมาย

| event ของ inventory | เขียน voucher ไหม? | หลักฐาน |
|---|---|---|
| การ commit GRN (รวม FOC-to-stock, extra cost → landed cost) | ไม่ | 0 hit ใน `procurement/`; service ของ GRN แตะเฉพาะ `tb_inventory_transaction*` และ cost layer |
| Credit note (คืนเข้าสต๊อก / ตีราคาต้นทุนใหม่) | ไม่ | grep เดียวกัน; "การ post AP" บน [purchase-order/credit-note](/th/inventory/purchase-order/credit-note) ยังไม่ยืนยัน |
| Stock-in / stock-out `PATCH commit` | ไม่ | 0 hit ใน `inventory/stock-in`, `inventory/stock-out` |
| การจ่าย / โอนของ store requisition | ไม่ | 0 hit ใน `inventory/store-requisition` |
| variance ของ physical count / spot check | ไม่ | 0 hit ใน `inventory/physical-count*`, `inventory/spot-check*` |
| การเขียน cost layer (`tb_inventory_transaction_cost_layer`) | ไม่ | 0 hit ใน `inventory/inventory-transaction`, `inventory/costing` |
| การปิดงวด inventory (`POST /api/:bu_code/period-ends`) | ไม่ | `period-end.close-transaction.helper.ts:80,195,210` อ่าน/เขียนเฉพาะ `tb_inventory_period`; ไม่เคยแตะ `tb_gl_period` หรือ `tb_gl_jv_header` |

`enum_gl_jv_source` (schema `:4724`) สงวน `ap`, `ar`, `inventory`, `asset` และ `interface` ไว้ และ `tb_gl_jv_header.source_ref_type` / `source_ref_id` (schema `:4741`) มีอยู่เพื่อชี้กลับไปยังเอกสารต้นทาง ทั้งสองอย่างเป็น **placeholder สำหรับอนาคต**: ไม่มีอะไรเติมค่าให้ comment ที่ header ของ `GlPostingService` บอกว่ามัน "separate from `GlJvService` so AP/AR can post without going through the JV DTO" (`gl-posting.service.ts:68`) — อีกครั้ง เป็นเจตนาที่ระบุไว้ ไม่ใช่ผู้เรียกที่ implement แล้ว

**drift ของ carmen/docs** `../carmen/docs/app/inventory-management/inventory-transactions/BR-inventory-transactions.md:21,31,143,162,214` ("automatic integration with general ledger for all inventory movements", "variance posted to designated GL variance accounts", "return posts to GL (debit AP, credit Inventory)"), `../carmen/docs/inventory-management/period-end-process.md:135-136` ("GL posting verification", "period end journal entries") และ `../carmen/docs/store-requisitions/SR-API-JournalEntry-Endpoints.md` อธิบายพฤติกรรมที่ HEAD ไม่ได้ implement เอกสาร persona ของ e2e `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-09-end-period-close.md:65,200` กล่าวซ้ำ claim เดียวกัน ("Finalized = variance adjustments posted to the General Ledger"); gate การปิดงวดที่ implement จริงคือสถานะของ physical-count ไม่ใช่การ post GL ([inventory/period-end](/th/inventory/inventory/period-end))

## 3. `gl-posting` ทำอะไร

`apps/micro-business/src/gl/gl-posting/` คือ **ผู้เขียนเพียงรายเดียวของ `tb_gl_balance`** (`gl-posting.service.ts:68`) gateway module `apps/backend-gateway/src/application/gl-posting/` เปิดมันเป็น `api/:bu_code/gl-posting` (`gl-posting.controller.ts:63`) หลัง `KeycloakGuard` + `PermissionGuard` resource `accounting.gl` (`:52`) RPC contract: `packages/rpc-contract/src/contracts/gl-posting.ts` (`post`, `void`, `reverse`, `close-year`, `reopen-year`, `run-due`)

### 3.1 Route

| Route | Permission | Body | Service |
|---|---|---|---|
| `POST api/:bu_code/gl-posting/:gl_jv_id/post` (`:128`) | `accounting.gl:post` | `{ post_at?: ISO datetime }` | `GlPostingService.post` (`:293`) |
| `POST .../:gl_jv_id/void` (`:185`) | `accounting.gl:void` | `{ reason }` (บังคับ) | `voidJv` (`:414`) |
| `POST .../:gl_jv_id/reverse` (`:233`) | `accounting.gl:reverse` | `{ jv_date }` | `reverse` (`:507`); gateway คำนวณ `can_post = hasAllPermissions(accounting.gl:post)` เพิ่ม (`:115`) |
| `POST .../recalculate` (`:296`) | `accounting.gl:recalculate` | `{ fiscal_year }` | `GlBalanceService.recalculate` (`gl-balance.service.ts:60`) — สร้างทุกแถว `tb_gl_balance` ของปีใหม่จาก voucher ที่ post แล้ว โดยคง opening ของงวด 1 |
| `POST .../close-year` (`:349`) | `accounting.gl:close_year` | `{ fiscal_year }` | `closeYear` (`:698`) |
| `POST .../reopen-year` (`:403`) | `accounting.gl:close_year` | `{ fiscal_year }` | `reopenYear` (`:1096`) |

Bruno: `_uncategorized/gl-posting/POST-{post,void-jv,reverse,recalculate,close-year,reopen-year}-gl-posting.bru` สังเกตว่าทุก sample response ใน Bruno ของ folder เหล่านี้เป็น placeholder ทั่วไป `{ "data": { "id": ... }, "status": 201 }`; envelope จริงคือ `{ id, jv_status }` (post/void), `{ id, jv_status, reversal_of_jv_id }` (reverse), `{ fiscal_year, closing_jv_id, carried_rows }` (close-year) และ `{ posted, reversed, skipped, failed[] }` (run-due)

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

`validateJvLines` (`gl-jv/gl-jv.validation.ts:39`): ทุกบรรทัดเป็นด้านเดียว (`debit > 0 XOR credit > 0`), ≥ 2 บรรทัด และ `Σ base_debit == Σ base_credit` (`gl-jv.logic.ts`), ทุกบัญชีมีอยู่ active และไม่ใช่ type `header` / `summary`, บัญชี `is_require_cost_center` มี `cost_center_id` และทุก cost center ที่ระบุ active Error: `GL_JV_NOT_BALANCED`, `GL_ACCOUNT_NOT_POSTABLE`, `GL_COST_CENTER_REQUIRED`, `GL_COST_CENTER_NOT_ALLOWED`

### 3.3 กติกาของยอดคงเหลือ (`gl-balance.logic.ts:78 planBalanceWrites`)

สำหรับแต่ละ key (`cost_center_id` หรือ nil-uuid, `chart_of_accounts_id`) ที่ voucher แตะ ภายในปีการเงิน:

```
net = Δdebit − Δcredit
rows = existing tb_gl_balance rows of this key in the fiscal year
1. row for period N exists      → bump: debit += Δdebit, credit += Δcredit
2. row does not exist           → insert: opening = closing(latest existing row BEFORE N)  or 0
                                   where closing(row) = opening + debit − credit   (never stored)
3. every existing row AFTER N   → opening += net
Rows after N that do not exist are NOT pre-created (rule 2 derives them later).
```

กติกาข้อ 3 คือเหตุผลที่ทุกการ mutate ledger ต้องเอา advisory lock ก่อน void และ reverse ใช้ planner ตัวเดิมพร้อม `negateDelta` (`:125`) opening ของงวดหลังจึงถูกเลื่อนกลับด้วย

### 3.4 Void และ reverse

| | Void (`:414`) | Reverse (`:507`) |
|---|---|---|
| เงื่อนไขก่อน | `jv_status == posted` และ `reversed_by_jv_id` เป็น null; `reason` ไม่ว่าง | `jv_status == posted` และ `reversed_by_jv_id` เป็น null; `gl_setting.reversal_prefix_id` ตั้งไว้และ active; งวดเป้าหมายของ `jv_date` เปิด (หรือ `allow_post_to_closed_period`) |
| งวดที่ใช้ | งวดที่มันถูก post เข้าไป (`gl_period_id`) ไม่ใช่ resolve `jv_date` ใหม่ | `jv_date` ที่ผู้เรียกส่งมา |
| ผลต่อ ledger | delta ที่ negate แล้ว apply กับ `tb_gl_balance` | ต้นฉบับคงอยู่; voucher เงา (`source = reversal`, สลับ debit↔credit, `reversal_of_jv_id`) ถูกสร้างผ่าน `createInternal` และ post ผ่าน `post()` เมื่อ `can_post` มิฉะนั้นทิ้งไว้เป็น `draft` |
| ผลที่ header | `jv_status = void`, `void_at/by/reason`; `total_*` ไม่เปลี่ยน | ต้นฉบับได้ `reversed_by_jv_id` หลัง post สำเร็จ; partial unique `gljvheader_reversed_by_u` บล็อกการ reverse ครั้งที่สอง (→ `GL_JV_IMMUTABLE`) |

### 3.5 สิ้นปี (`closeYear :698`, `assertYearClosable :742`, `reopenYear :1096`)

เงื่อนไขก่อน: แถว `tb_gl_period` ปกติทั้ง 12 ของปีมีอยู่และเป็น `closed`/`locked`, งวด 13 เป็น `open`, ไม่มี voucher ของปีอยู่ใน `draft`/`in_review`/`scheduled` (`GL_YEAR_CLOSE_PENDING_JV`), งวด 1 ของปี+1 มีอยู่, `gl_setting.retained_earnings_account_id` และ `auto_jv_prefix_id` ตั้งไว้ จากนั้น: สร้าง closing voucher (`source = closing`, ลงวันที่ instant ของงวด 13, บรรทัด retained-earnings หนึ่งบรรทัด **ต่อ cost center**), post ผ่าน `post()`, ยก closing ของ asset/liability/equity ไปงวด 1 ของปี+1, lock ทุกงวด รันเป็นสาม transaction ต่อเนื่อง ไม่ใช่หนึ่ง (`:683-688` เบี่ยงจาก spec โดยตั้งใจ) `reopenYear` ถอน opening ที่ยกไปและถูกปฏิเสธเมื่อปีถัดไปมีกิจกรรมแล้ว

### 3.6 guard ใน DB

Migration `20260914030000_gl_core_jv_ledger:151-231` ติดตั้ง `gl_jv_posted_guard` (`BEFORE UPDATE/DELETE` บน `tb_gl_jv_header` และ `tb_gl_jv_detail`; body สร้างใหม่พร้อม `search_path` ชัดเจนใน `20260915010000_fix_gl_jv_guard_search_path`) เมื่อ header เป็น `posted` หรือ `void` แล้ว: hard delete โยน `GL_JV_IMMUTABLE`; การเปลี่ยนสถานะเดียวที่อนุญาตคือ `posted → void`; `deleted_at` อยู่ในชุดคอลัมน์ที่เปรียบเทียบ ดังนั้น **soft-delete เป็นไปไม่ได้**; เปลี่ยนได้เฉพาะ `reverse_at`, `reversed_by_jv_id`, `void_*`, `updated_*`, `doc_version`, `info`, `note` (header) และ `updated_*`/`doc_version`/`info`/`note`/ชื่อแบบ denormalise (detail) Prisma มองไม่เห็น trigger — tenant schema ที่สร้างจาก `schema.prisma` อย่างเดียวจะไม่มีมัน (comment ใน schema `:4738-4740`)

## 4. lifecycle สถานะ JV

`enum_jv_status` (schema `:140`; `in_review`, `scheduled`, `void` เพิ่มโดย `20260914030000_gl_core_jv_ledger:23-25`):

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

| การเปลี่ยน | โค้ด | Guard |
|---|---|---|
| create → `draft` | `GlJvService.create` `:211` → `createInternal` `:119` | prefix active; บรรทัด validate แล้ว; `jv_no` จาก `generateJvNo` (running code, prefix เก็บแยก) |
| `draft` → `in_review` / `posted` | `submit` `:341` | บรรทัด validate ซ้ำ; `resolveJvWorkflowId` `:321` เลือก `tb_workflow` ที่ active ตัวแรกที่ `workflow_type = gl_jv`; **ไม่มีที่ตั้งค่าไว้ → post ทันทีบน session ของผู้เรียก** (spec § 4.1) |
| `in_review` → `in_review` / `posted` / `scheduled` | `approve` `:421` | `WorkflowOrchestratorService.buildApproveWorkflow` ตัดสิน `isFinalApproval`; final → `GlPostingService.post(id, post_at)` |
| `in_review` → `draft` | `reject` `:478` | reason เก็บบน `note` |
| `scheduled` → `draft` | `unschedule` `:532` | กลับไป draft ไม่ใช่ review — การอนุมัติเป็นของการ post ที่ไม่เคยเกิด |
| update / delete ของ `draft` | `update` `:232`, `delete` `:278` | ปฏิเสธสำหรับ `posted`/`void` (update) และอะไรก็ตามที่ไม่ใช่ `draft` (delete) ก่อนที่ trigger จะทำ |

## 5. workflow `gl_jv`

- `enum_workflow_type` += `gl_jv` (`20260914030000_gl_core_jv_ledger:26`; schema `:276`) `workflows.service.ts:1071` map มันไป `tb_gl_jv_header`; `:780`, `:905`, `:979` เพิ่มมันใน lookup เอกสารที่รอ (ด้วย `department = null` เพราะ JV ไม่มีแผนก)
- Stage role: `workflow-stage-role.helper.ts:44` — `gl_jv: [create, approve]` header ของไฟล์ (`:12-15`) ระบุว่า `gl_jv` "has no configured workflow in any tenant yet" — แถว stage-role ของมัน hardcode แทนที่จะ derive จากข้อมูล
- Routing: `gl-jv/workflow/gl-jv-workflow.mapper.ts` สร้าง `WorkflowDocument` ด้วย `requestor_id = created_by_id`, `department = null`, `navigation_request_data.total_amount = total_debit` (routing ของ stage ตามจำนวนเงินใช้ได้; ตามแผนกไม่ใช้)
- Gateway `api/:bu_code/gl-jv` (`gl-jv.controller.ts:62`) **ไม่มี `@Permission`** บน route ใด — `KeycloakGuard` เท่านั้น `submit` (`:301`), `approve` (`:345`), `reject` (`:397`), `unschedule` (`:447`) gate โดย workflow engine ต่อ stage; CRUD ของ draft (`:131` list, `:83` get, `:177` create, `:215` patch, `:259` delete) ได้รับการยกเว้นโดย `WORKFLOW_GATED_ACTIONS` (`permission.route-map.ts:346-354`) licence feature `accounting.gl` ต้องเปิดบน BU
- Bruno: `_uncategorized/gl-jv/` — `GET-list`, `GET-by-id`, `POST-create`, `PATCH-update`, `DELETE-remove`, `POST-submit`, `POST-approve`, `POST-reject`, `POST-unschedule`, `POST-run-due-gl-jv-gl-jv` (route ของปุ่ม UI), `POST-run-due-gl-jv-gl` (bridge ภายใน)

## 6. cron `gl_run_due`

| | ค่า | แหล่ง |
|---|---|---|
| Job type | `gl_run_due` | `micro-cronjobs/internal/executor/executor.go:84` |
| Job config | `{ "bu_codes": [...], "user_id": "<uuid v4>" }` — `user_id` คือ actor ที่ประทับบนทุก voucher ที่การรัน post/reverse เพราะ platform ไม่มี system user | `internal/model/cronjob.go:141-149` |
| เรียกอะไร | `POST {GATEWAY_URL}/api/internal/gl/run-due`, header `x-internal-token: {INTERNAL_JOB_TOKEN}`, body `{ bu_code, user_id }`, **หนึ่งครั้งต่อ BU ตามลำดับ** | `gl_run_due.go:55-87` |
| Timeout | HTTP client 120 วินาที **ต่อ BU**; scheduler ห่อทั้ง job ด้วย `timeout_seconds` (default 300) → operator ต้องตั้ง `timeout_seconds ≥ len(bu_codes) × 120` | `gl_run_due.go:37-41`, `README.md:254` |
| ความหมายเมื่อล้มเหลว | BU หนึ่งล้มเหลวไม่หยุด BU อื่น; ความล้มเหลวถูกรวมและ job บันทึกว่าล้มเหลว ความล้มเหลวต่อ voucher ภายใน BU ถูก log เป็น warning ไม่ใช่ความล้มเหลวของ job | `gl_run_due.go:77-86`, `:122-128` |
| ฝั่ง gateway | `GlJvInternalController` `api/internal/gl/run-due` (`gl-jv-internal.controller.ts:24-39`) ไม่อยู่ใน Swagger guard ด้วย `InternalJobGuard` (`auth/guards/internal-job.guard.ts:41`): fail-closed เว้นแต่ `INTERNAL_JOB_API_ENABLED` และ `INTERNAL_JOB_TOKEN` ถูกตั้งและ header ตรง (เปรียบเทียบแบบ constant-time) schema ของ body `GlJvRunDueInternalSchema` (`common/dto/gl-jv/gl-jv-run-due-internal.dto.ts:8-23`): `bu_code`, `user_id` (uuid v4), `now` ไม่บังคับ (เฉพาะการรัน acceptance; log ระดับ warn) | |
| งานเดียวกัน ประตูสำหรับคน | `POST api/:bu_code/gl-jv/run-due` (`gl-jv.controller.ts:496`, ปุ่ม "Run due jobs"; ไม่มี permission แบบ static) | |
| Service | ทั้งคู่เรียก `GlJvService.runDue` (gateway `gl-jv.service.ts:214`) → RPC `gl-posting.run-due` → `GlPostingService.runDueJobs(now)` (`:1251`) | |

การรันหนึ่งครั้งทำอะไร (`runDueJobs :1251`):

```
posted   = runDueSchedules(now):      for each tb_gl_jv_header {jv_status: scheduled, post_at ≤ now} order by post_at
                                        post(id) ; on error → releaseToDraft(id, reason)   -- :1353, tb_activity row entity_type 'gl_jv'
reversed = runDueAutoReversals(now):  for each {jv_status: posted, is_auto_reverse, reverse_at ≤ now, reversed_by_jv_id null}
                                        period = resolvePeriod(reverse_at) ; not open → skipped++ (not failed)
                                        reverse(id, reverse_at, can_post = true) ; on error → failed[]
return { posted, reversed, skipped, failed: [{ id, reason }] }
```

**มันไม่สร้าง JV template** `grep -rn -i "generate-all-due\|generateAllDue\|jv-template" micro-cronjobs --include='*.go'` → 0 hit การสร้าง template คือ § 7 และไม่มีผู้เรียกตามเวลาที่ไหนเลย

## 7. การสร้าง JV template (`generate` / `generate-all-due`)

บันทึกไว้ที่นี่เพียงเพราะหน้าแรกเอ่ยชื่อ endpoint และ sample response ใน Bruno เป็น placeholder ที่ทำให้เข้าใจผิด

| Request | Route / permission | Body | response จริง (`gl-jv-template.service.ts`) |
|---|---|---|---|
| `_uncategorized/gl-jv-templates/POST-generate-gl-jv-templates.bru` | `POST api/:bu_code/gl-jv-templates/:gl_jv_template_id/generate` (`gl-jv-templates.controller.ts:377`), `accounting.gl.jv_template:generate` | `{ "gl_period_id": "<uuid>" }` | `{ jv_id, jv_no, gl_period_id, amount_total }` (`:814-818`) |
| `_uncategorized/gl-jv-templates/POST-generate-all-due-gl-jv-templates.bru` | `POST api/:bu_code/gl-jv-templates/generate-all-due` (`:335`), permission เดียวกัน | `{ "gl_period_id": "<uuid>" }` | `{ generated: [{template_id, jv_id, jv_no}], skipped: [{template_id, reason: already_run \| not_due}], failed: [{template_id, code}] }` (`:865-885`) |

กติกา (`generate :707`, `generateAllDue :833`): `tb_gl_period` เป้าหมายต้องเป็น `open` และ `period_no ≤ 12`; template ต้อง active และช่วง `from`–`to` ต้องครอบคลุมงวด (`GL_JV_TEMPLATE_PERIOD_OUT_OF_RANGE`); template `recurring` ถึงกำหนดเฉพาะเมื่อ `periodIndex(from, target) % frequency_months == 0` (`gl-jv-template.generate.logic.ts:68-86` มิฉะนั้น `GL_JV_TEMPLATE_NOT_DUE`); template `amortize` ต้องการให้ทุกงวดในช่วงมีอยู่ (`GL_JV_TEMPLATE_PERIODS_INCOMPLETE`) voucher ที่สร้างเป็น **`draft`** ที่สร้างผ่าน `GlJvService.createInternal` ด้วย `source = enum_gl_jv_source[template_type]`, `template_id`, `jv_date = period.start_at`; transaction เดียวกัน insert `tb_gl_jv_template_run` ซึ่ง unique (`template_id`, `gl_period_id`) ทำให้การสร้างครั้งที่สองสำหรับงวดนั้นเป็น 409 `GL_JV_TEMPLATE_ALREADY_RUN` การลบ draft จะลบแถว run เพื่อให้สร้างงวดนั้นได้อีก (`gl-jv.service.ts:278`) `generateAllDue` รันหนึ่ง transaction ต่อ template และไม่หยุดที่ความล้มเหลวแรก

## 8. `tb_gl_period` เทียบกับ `tb_inventory_period`

เป็นปฏิทินสองชุดที่แยกอิสระ ไม่มีอะไร join กัน

| | `tb_gl_period` (schema `:3128`) | `tb_inventory_period` (schema `:1229`; เปลี่ยนชื่อจาก `tb_period` โดย `20260916141000_rename_tb_period_to_tb_inventory_period`) |
|---|---|---|
| เจ้าของ | `gl/gl-period/` — `GlPeriodService` | `inventory/inventory-period/`, `inventory/period-end/` |
| แถวต่อปี | 13 (`createYear :70` จาก `gl_setting.fiscal_year_start_month`; งวด 13 มี `start_at = end_at = end_at` ของงวด 12) | 12 (`period` `YYMM`, `fiscal_year`, `fiscal_month` 1–12) |
| enum สถานะ | `enum_gl_period_status { open, closed, locked }` | `enum_period_status { open, closed, locked }` |
| กติกาการปิด | `close :110` — งวดก่อนหน้าต้องไม่เป็น `open` (`GL_PERIOD_SEQUENCE`); `reopen :160` — ปฏิเสธถ้างวดใดของปีเป็น `locked` หรืองวดหลังไม่เป็น `open`; `closeYear` สิ้นปี lock ทั้ง 13 | `POST /api/:bu_code/period-ends` — gate เอกสารที่บล็อก + physical-count เขียน inventory transaction `close`/`open` และ (BU แบบ average) `tb_inventory_period_snapshot` ([inventory/period-end](/th/inventory/inventory/period-end)) |
| Relation | `tb_gl_jv_template_run.gl_period_id`; `tb_gl_jv_header.gl_period_id` (ตั้งตอน post); `tb_gl_balance.gl_period_id` | `tb_inventory_period_snapshot`, `tb_inventory_transaction_cost_layer.at_period`, `tb_physical_count_period`, `tb_inventory_period_comment` |
| การอ้างอิงข้ามกัน | ไม่มี — ไม่มี FK ไม่มีการเรียก service ไม่มี config key ที่ใช้ร่วม (`grep -rln "tb_gl_period\|gl_period_id" apps/micro-business/src apps/backend-gateway/src | grep -v "/gl/\|/gl-\|config_gl"` → 0 ไฟล์) | ไม่มี |
| route ของ gateway | `api/config/:bu_code/gl-periods` (`config_gl-periods.controller.ts:49`; Keycloak + `AppIdGuard` ไม่มี `@Permission`) | `api/:bu_code/inventory-periods`, `api/:bu_code/period-ends` (`period-end.controller.ts:72-280`) |

ผลสำหรับ tester: การปิดงวด inventory **ไม่** ปิด lock หรือ validate อะไรใน GL และในทางกลับกัน; voucher post เข้างวด GL ที่เดือน inventory ที่ตรงกันปิดไปแล้วได้ และ inventory ยังเคลื่อนไหวได้ในเดือนที่งวด GL เป็น `locked`

## 9. กรณีพิเศษ

| # | สถานการณ์ | ผลที่คาดวันนี้ | แหล่ง |
|---|---|---|---|
| 1 | Tester หา JV หลัง commit GRN / stock-out / credit note | ไม่มีเลย; จำนวน `tb_gl_jv_header` ไม่เปลี่ยน | § 2 |
| 2 | ปิดงวด inventory บน BU ที่งวด GL ทั้งหมดเป็น `locked` | การปิดสำเร็จ; GL ไม่ถูกแตะ | § 8 |
| 3 | `POST gl-posting/:id/post` ด้วย `post_at` ในอนาคต | header กลายเป็น `scheduled`, `tb_gl_balance` ไม่ถูกแตะ; run-due post ทีหลัง | `gl-posting.service.ts:352-365` |
| 4 | voucher ที่ scheduled ซึ่งบัญชีถูกปิดใช้งานก่อน `post_at` | run-due คืนมันเป็น `draft` และเขียนแถว `tb_activity` (`entity_type = gl_jv`, `action = other`) | `:1268-1299`, `:1353` |
| 5 | auto-reversal ถึงกำหนดแต่งวดถัดไปไม่ `open` | นับใน `skipped` ลองใหม่รอบถัดไป; ไม่ใช่ error | `:1300-1352` |
| 6 | void voucher ที่ถูก reverse ไปแล้ว | `GL_JV_IMMUTABLE` | `:431` |
| 7 | reverse voucher สองครั้ง (race) | ครั้งที่สองแพ้ที่ `gljvheader_reversed_by_u` → `GL_JV_IMMUTABLE` | comment ที่ header `:507` |
| 8 | post เข้างวด `closed` | `GL_PERIOD_NOT_OPEN` เว้นแต่ `gl_setting.allow_post_to_closed_period = true` | `:331` |
| 9 | voucher วันที่ปกติ ณ instant สุดท้ายของงวด 12 | resolve เป็นงวด 12; งวด 13 เข้าถึงได้เฉพาะด้วย `is_adjustment = true` | `:152-176` |
| 10 | submit draft บน BU ที่ไม่มี workflow `gl_jv` ที่ active | post ทันทีบน session ของผู้ submit — ไม่มี review | `gl-jv.service.ts:373-375` |
| 11 | `UPDATE tb_gl_jv_header SET deleted_at = now()` บน voucher ที่ post แล้ว (raw SQL) | trigger โยน `GL_JV_IMMUTABLE` | `20260914030000…:151-231` |
| 12 | tenant schema ใหม่สร้างจาก `schema.prisma` โดยไม่รัน migration | `gl_jv_posted_guard` หายไป; voucher ที่ post แล้วแก้ไขได้ | comment ใน schema `:4738-4740` |
| 13 | job `gl_run_due` ที่มี 3 BU และ `timeout_seconds = 300` แบบ default | BU ที่สามอาจถูกตัดโดย job context (120 วินาที × 3 > 300) | `gl_run_due.go:37-41` |
| 14 | `POST /api/internal/gl/run-due` ด้วย token ถูกต้องแต่ `INTERNAL_JOB_API_ENABLED` ไม่ได้ตั้ง | 403 "Internal job API is disabled" (ข้อความเดียวกันทุกเส้นทางที่ล้มเหลว) | `internal-job.guard.ts:41-57` |
| 15 | `generate-all-due` สำหรับงวด 13 หรืองวด `closed` | ทั้งการเรียกล้มเหลว `GL_PERIOD_NOT_OPEN` (ไม่ใช่ 200 ที่ทุกอย่างอยู่ใน `failed`) | `gl-jv-template.service.ts:848-852` |
| 16 | post พร้อมกันสองรายการเข้าปีการเงินเดียวกัน | serialise ด้วย `pg_advisory_xact_lock('gl-balance:<bu>:<year>')` ที่เอาก่อนการอ่านใด ๆ | `:131`, `gl-balance.logic.ts:59-62` |

## 10. ข้อแนะนำ

1. **อย่าเขียน test scenario ของ inventory ที่ assert การ post GL** — สำหรับ GRN, CN, SR, การปรับ, การนับ หรือการปิดงวด — จนกว่าผู้เรียก `GlJvService.createInternal` ด้วย `source = inventory` จะปรากฏใน `apps/micro-business/src/inventory` หรือ `procurement` รัน grep ใน § 2.1 ซ้ำก่อน; ถ้ามี hit หน้านี้และหน้า GRN / credit-note / period-end ต้องมีส่วน "GL posting" ใหม่
2. **เมื่อสร้างการ post จาก inventory** ควรผ่าน `createInternal` ภายใน transaction ของผู้เรียกพร้อมตั้ง `source_ref_type` / `source_ref_id` แล้วตามด้วย `GlPostingService.post` — ไม่ใช่เขียน `tb_gl_balance` โดยตรง (§ 3 กติกาผู้เขียนรายเดียว) การ resolve `tb_inventory_period` → `tb_gl_period` ที่วางแผนไว้ (12 vs 13 งวด, `start_at` ต่างกันถ้า `fiscal_year_start_month ≠ 1`) จะต้องมี mapping ที่ชัดเจน; ยังไม่มี
3. **Ops:** ตั้ง `timeout_seconds` บนแถว cron `gl_run_due` เป็น `len(bu_codes) × 120` และตั้ง `INTERNAL_JOB_API_ENABLED` / `INTERNAL_JOB_TOKEN` บน gateway มิฉะนั้น job จะ fail closed ด้วย 403 ทุก BU
4. **การ provision tenant:** หลังสร้าง BU schema ใหม่ ตรวจว่า trigger `gl_jv_posted_guard_header` / `_detail` มีอยู่ (`SELECT tgname FROM pg_trigger WHERE tgname LIKE 'gl_jv_posted_guard%'`) — Prisma จะไม่สร้างมัน
5. **สุขอนามัยของเอกสาร:** ถือทุก claim เรื่อง GL ใน `../carmen/docs` (§ 2.2) และในเอกสาร persona ของ e2e `tx-09-end-period-close.md` เป็นความตั้งใจ; drift log ของ coordinator สำหรับ 2026-09-22 มีรายการอยู่

## 11. แหล่งอ้างอิง

- **Backend (micro-business):** `../carmen-turborepo-backend-v2/apps/micro-business/src/gl/gl-posting/` (`gl-posting.service.ts`, `gl-balance.logic.ts`, `gl-posting.controller.ts`), `gl/gl-jv/` (`gl-jv.service.ts`, `gl-jv.validation.ts`, `gl-jv.logic.ts`, `gl-jv.running-code.ts`, `workflow/gl-jv-workflow.mapper.ts`), `gl/gl-jv-template/` (`gl-jv-template.service.ts`, `gl-jv-template.generate.logic.ts`, `gl-jv-template.validation.ts`), `gl/gl-period/gl-period.service.ts`, `gl/gl-balance/gl-balance.service.ts`; `master/workflows/workflows.service.ts`, `master/workflows/workflow-stage-role.helper.ts`; `inventory/period-end/period-end.close-transaction.helper.ts` (ฝั่ง inventory ที่ไม่เรียก GL)
- **Backend (gateway):** `apps/backend-gateway/src/application/gl-posting/gl-posting.controller.ts`, `application/gl-jv/gl-jv.controller.ts`, `application/gl-jv/gl-jv-internal.controller.ts`, `application/gl-jv-templates/gl-jv-templates.controller.ts`, `auth/guards/internal-job.guard.ts`, `common/dto/gl-jv/gl-jv-run-due-internal.dto.ts`, `libs/config.env.ts:227-228,419-420`; `packages/rpc-contract/src/contracts/gl-posting.ts`
- **Prisma:** `packages/prisma-shared-schema-tenant/prisma/schema.prisma` (`enum_jv_status :140`, `enum_workflow_type :276`, `tb_inventory_period :1229`, `enum_gl_period_status :2899`, `tb_gl_period :3128`, `tb_gl_jv_detail :4496`, `tb_gl_balance :4552`, `tb_gl_jv_template_run :4708`, `enum_gl_jv_source :4724`, `tb_gl_jv_header :4741`); migration `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path`, `20260915043038_gl_core_budget_template`, `20260916141000_rename_tb_period_to_tb_inventory_period`
- **Permission / licence:** `packages/prisma-shared-schema-platform/prisma/permission.route-map.ts:57-61,346-354`, `seed.permission.data.ts:1612-1637,1674-1698`, `seed.license-feature.data.ts:60,100,108`
- **Cron:** `../micro-cronjobs/internal/executor/gl_run_due.go`, `internal/executor/executor.go:84`, `internal/model/cronjob.go:141-149`, `README.md:254`
- **API contract:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/{gl-posting,gl-jv,gl-jv-templates}/*.bru`
- **Frontend / E2E:** ไม่มี — ดู [General Ledger](/th/inventory/general-ledger) § 4
- **หน้า wiki ที่เกี่ยวข้อง:** [inventory/period-end](/th/inventory/inventory/period-end), [system-config/period](/th/inventory/system-config/period), [costing](/th/inventory/costing) § 1 (ข้อค้นพบ "ไม่มีการ post GL" ก่อนหน้าที่หน้านี้ยืนยัน), [system-config/workflow](/th/inventory/system-config/workflow) (`enum_workflow_type`)
