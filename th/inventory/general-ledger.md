---
title: บัญชีแยกประเภททั่วไป (General Ledger)
description: ระบบย่อย GL (backend + Bruno + cron เท่านั้น ไม่มี UI) บันทึกเฉพาะส่วนที่แตะ inventory วันนี้ไม่มีอะไรใน inventory ที่ post เข้า ledger; GL master, budget, JV template และรายงานเป็นช่องว่างที่ตั้งใจเว้นไว้
published: true
date: '2026-09-23T01:30:00.000Z'
tags: general-ledger, inventory, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# บัญชีแยกประเภททั่วไป (General Ledger)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ledger แบบ journal-voucher (`tb_gl_jv_header` / `tb_gl_jv_detail` → `tb_gl_balance`) ที่มาถึง backend เมื่อ 2026-09-09..15 โดย **ไม่มี frontend** — tree `routes/accounting` ของ React เป็น mock แบบ hardcode &nbsp;·&nbsp; **ขอบเขตของ wiki:** บันทึก **เฉพาะส่วนที่แตะ inventory**; GL master data, budget, JV template และรายงาน GL เป็นช่องว่างที่ตั้งใจเว้น (§ 1.1) &nbsp;·&nbsp; **Inventory→GL วันนี้:** **ไม่มี** — ไม่มี GRN, stock-in/out, credit note, store requisition, physical count, cost layer หรือการปิดงวด inventory ใดที่เขียน voucher (ดู [gl-posting](/th/inventory/general-ledger/gl-posting) § 2) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_gl_jv_header`, `tb_gl_jv_detail`, `tb_gl_balance`, `tb_gl_period` (ปฏิทินคนละชุดกับ `tb_inventory_period`) &nbsp;·&nbsp; **หน้าย่อย:** 1

## 1. ภาพรวม

General Ledger คือระบบย่อย backend ใหม่ใต้ `apps/micro-business/src/gl/` (NestJS module แปดตัว) พร้อม route ของ gateway ใต้ `api/:bu_code/gl-*` และ `api/config/:bu_code/gl-*`, tenant migration สี่ตัว และ scheduled job หนึ่งตัวใน `micro-cronjobs` มันคือ ledger บัญชีอเนกประสงค์ — ผังบัญชี, cost center, ปฏิทินการเงิน 13 งวด, journal voucher พร้อม review workflow, ยอดคงเหลือ, budget, template แบบ recurring/allocation/amortize, trial balance

**wiki นี้เป็นคู่มือ inventory ERP ดังนั้น ledger จึงถูกบันทึกเฉพาะที่รอยต่อกับ inventory** (การตัดสินใจของเจ้าของเมื่อ 2026-09-22) รอยต่อนั้นตอนนี้*ว่างเปล่า*: ที่ backend `ef4d6f08f` (2026-09-22) ไม่มี code path จากเอกสาร inventory หรือ procurement ใดเข้าสู่ `tb_gl_jv_header` และสมาชิกของ `enum_gl_jv_source` คือ `inventory`, `ap`, `ar`, `asset` และ `interface` ถูกประกาศไว้แต่ไม่เคยถูกเขียน หน้าย่อยหนึ่งหน้า [gl-posting](/th/inventory/general-ledger/gl-posting) บันทึกข้อค้นพบนั้นพร้อม grep ที่ยืนยัน และบันทึกสองสิ่งที่นักพัฒนาหรือ tester ฝั่ง inventory *จะ* เจอ: voucher ไปถึง `tb_gl_balance` ได้อย่างไร (post / void / reverse / year-end) และ cron `gl_run_due` ทำอะไรจริง ๆ

### 1.1 ตั้งใจไม่บันทึก

ทุกอย่างด้านล่างมีอยู่ในโค้ดและ **ตั้งใจเว้นไว้ไม่ใส่ใน wiki นี้** ตารางนี้อยู่ที่นี่เพื่อให้นักพัฒนาที่ grep identifier ของ GL มาลงที่หน้านี้และรู้ว่านี่คือช่องว่างที่เลือกแล้ว ไม่ใช่ตกหล่น ให้ดู source path โดยตรง

| ส่วน | Backend (`apps/micro-business/src/`) | route ของ gateway (`apps/backend-gateway/src/`) | folder ของ Bruno (`collections/carmen-inventory/_uncategorized/`) | Migration | key ของ permission / licence | Enum |
|---|---|---|---|---|---|---|
| ผังบัญชี (`tb_chart_of_accounts`; เปลี่ยนชื่อจาก account code ขยายด้วย `category`, `is_require_cost_center`, `account_group_id`; import จาก interface `carmen-gl`) | `master/chart-of-accounts/` | `config/config_chart-of-accounts/` → `api/config/:bu_code/chart-of-accounts` (+ `POST import`, `POST import-from-interface/carmen-gl`) | — (collection ของ config) | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` เท่านั้น; ไม่มี `@Permission` บน config controller | `enum_chart_of_accounts_category` (`asset, liability, equity, revenue, expense, statistic`), `enum_chart_of_accounts_type` += `summary` |
| Cost center / กลุ่ม cost center / การเชื่อม cost-center↔account (`tb_cost_center`, `tb_cost_center_group`, `tb_cost_center_account`) | `master/cost-center*/` | `config/config_cost-centers/`, `config/config_cost-center-groups/` | — | `20260904103000_add_cost_center` | Keycloak + `AppIdGuard` | — |
| กลุ่มบัญชี GL (`tb_gl_account_group`, tree ≤ 4 ระดับ, category ต้องตรงกับ parent) | `gl/gl-account-group/` | `config/config_gl-account-groups/` → `api/config/:bu_code/gl-account-groups` | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | — |
| JV prefix (`tb_gl_jv_prefix`; `code` แก้ไม่ได้, `is_system` ลบไม่ได้, `is_default` ตัวเดียว) | `gl/gl-jv-prefix/` | `config/config_gl-jv-prefixes/` → `api/config/:bu_code/gl-jv-prefixes` | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | — |
| งวด GL (`tb_gl_period`; 13 งวดต่อปีการเงินสร้างจาก key `gl_setting`.`fiscal_year_start_month` ใน `tb_application_config`; close/reopen ตามลำดับ) | `gl/gl-period/` | `config/config_gl-periods/` → `api/config/:bu_code/gl-periods` (`POST years`, `POST :id/close`, `POST :id/reopen`) | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | `enum_gl_period_status` (`open, closed, locked`) |
| Journal voucher — CRUD ของ draft และ review workflow (`tb_gl_jv_header`, `tb_gl_jv_detail`) | `gl/gl-jv/` | `application/gl-jv/` → `api/:bu_code/gl-jv` (11 route) | `gl-jv/*` (11 ไฟล์) | `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path` | licence `accounting.gl`; การร่าง gate ด้วย workflow (`permission.route-map.ts:352-354` ยกเว้น `accounting.gl:create/update/delete`) | `enum_jv_status` += `in_review`, `scheduled`, `void`; `enum_workflow_type` += `gl_jv`; `enum_gl_jv_source` |
| การ post ledger และยอดคงเหลือ (`tb_gl_balance`) — **ครอบคลุมบนหน้าย่อยเฉพาะในฐานะเป้าหมายที่ inventory จะ post ไป** | `gl/gl-posting/`, `gl/gl-balance/` | `application/gl-posting/` → `api/:bu_code/gl-posting` | `gl-posting/*` (6 ไฟล์) | `20260914030000_gl_core_jv_ledger` | `accounting.gl:{post, void, reverse, recalculate, close_year}` (`seed.permission.data.ts:1612-1637`) | — |
| Budget (`tb_gl_budget`, `tb_gl_budget_detail`; revision ที่ active หนึ่งตัวต่อปี) | `gl/gl-budget/` | `application/gl-budgets/` → `api/:bu_code/gl-budgets` (+ `POST :id/activate`) | `gl-budgets/*` (6 ไฟล์) | `20260915043038_gl_core_budget_template` | `accounting.gl.budget:{view, create, update, delete, activate}`; licence `accounting.gl.budget` | `enum_gl_budget_status` (`draft, active, superseded`) |
| JV template (`tb_gl_jv_template`, `_detail`, `_run`; `generate` / `generate-all-due`) | `gl/gl-jv-template/` | `application/gl-jv-templates/` → `api/:bu_code/gl-jv-templates` (+ `POST :id/generate`, `POST generate-all-due`) | `gl-jv-templates/*` (7 ไฟล์) | `20260915043038_gl_core_budget_template` | `accounting.gl.jv_template:{view, create, update, delete, generate}`; licence `accounting.gl.jv_template` | `enum_gl_jv_template_type` (`recurring, allocation, amortize`), `enum_gl_amortize_type` (`day_in_month, monthly`), `enum_gl_side` (`debit, credit`) |
| รายงาน GL — trial balance | `gl/gl-balance/` (raw SQL) | `application/gl-reports/` → `GET api/:bu_code/gl-reports/trial-balance` | `gl-reports/*` (1 ไฟล์) | — | `accounting.gl:view` | — |

Licence feature: `accounting.gl` (parent `accounting`), `accounting.gl.budget` และ `accounting.gl.jv_template` (ลูกของ `accounting.gl`) — `packages/prisma-shared-schema-platform/prisma/seed.license-feature.data.ts:60,100,108` การ map segment ของ gateway → resource: `permission.route-map.ts:57-61` (`app:gl-jv`, `app:gl-posting`, `app:gl-reports` → `accounting.gl`; `app:gl-budgets` → `accounting.gl.budget`; `app:gl-jv-templates` → `accounting.gl.jv_template`)

## 2. โมเดลข้อมูล (โครง)

จาก `packages/prisma-shared-schema-tenant/prisma/schema.prisma` ที่ `ef4d6f08f` หนึ่งบรรทัดต่อตาราง; รายละเอียดระดับฟิลด์อยู่นอกขอบเขต (§ 1.1)

| ตาราง (บรรทัดใน schema) | วัตถุประสงค์ |
|---|---|
| `tb_chart_of_accounts` (2934) | บัญชี master: `code`, `nature`, `type` (รวม `header` / `summary` ที่ post ไม่ได้), `category`, `reverse_sign`, `use_in[]`, `is_require_cost_center`, `account_group_id` |
| `tb_cost_center_group` (2976), `tb_cost_center` (3005), `tb_cost_center_account` (3037) | cost center ทางบัญชี (ต่างจาก `tb_department`) จัดกลุ่ม; whitelist แบบเลือกได้ว่า cost center หนึ่งจะ post ไปบัญชีไหนได้ |
| `tb_gl_jv_prefix` (3065) | prefix การออกเลข voucher (`code` ≤ 10 ตัวอักษร, `is_system`, `is_default` ตัวเดียว) |
| `tb_gl_account_group` (3093) | tree การจัดกลุ่มบัญชีสำหรับรายงาน ≤ 4 ระดับ `category` เดียวต่อ subtree |
| `tb_gl_period` (3128) | ปฏิทินการเงิน: `fiscal_year`, `period_no` 1–13 (13 = งวดปรับปรุงสิ้นปีที่ใช้ instant สุดท้ายร่วมกับงวด 12), `start_at`, `end_at`, `status`, `closed_at/by` **ไม่มี relation กับ `tb_inventory_period`** |
| `tb_gl_jv_header` (4741) | header ของ voucher: `jv_no` + `prefix_code`, `jv_date`, `is_adjustment`, `source` (`enum_gl_jv_source`), `source_ref_type/id`, `template_id`, `post_at` / `posted_at`, `is_auto_reverse` / `reverse_at`, `reversal_of_jv_id` / `reversed_by_jv_id`, `void_*`, `total_debit/credit`, `jv_status` บวกคอลัมน์มาตรฐาน `workflow_*` / `user_action` / `last_action*` ที่ทุกเอกสาร workflow มี ป้องกันโดย DB trigger `gl_jv_posted_guard` |
| `tb_gl_jv_detail` (4496) | บรรทัดของ voucher: `chart_of_accounts_id` (+ `account_code/name` แบบ denormalise), `cost_center_id` (+ code/name), `debit` XOR `credit`, `exchange_rate`, `base_debit/credit`, `quantity` |
| `tb_gl_balance` (4552) | ยอดคงเหลือที่ derive ต่อ (`gl_period_id`, `cost_center_id` หรือ nil-uuid, `chart_of_accounts_id`): `opening`, `debit`, `credit` ไม่มี soft-delete ไม่มี `doc_version` เขียนโดย `GlPostingService` เท่านั้นและสร้างใหม่ด้วย `recalculate` |
| `tb_gl_budget` (4575), `tb_gl_budget_detail` (4603) | budget รายปี × revision; หนึ่งบรรทัดต่อ (cost center?, บัญชี, งวด 1–12) |
| `tb_gl_jv_template` (4632), `tb_gl_jv_template_detail` (4677) | template แบบ recurring / allocation / amortize พร้อมช่วงงวด from–to, `frequency_months` และคอลัมน์ต่อ type |
| `tb_gl_jv_template_run` (4708) | fact row "template T สร้าง voucher V สำหรับงวด P"; unique บน (`template_id`, `gl_period_id`) |
| `tb_application_config` key `gl_setting` (5894) | JSON: `fiscal_year_start_month`, `allow_post_to_closed_period`, `reversal_prefix_id`, `retained_earnings_account_id`, `auto_jv_prefix_id` (`gl-posting.service.ts:57-62`, `gl-period.service.ts:21-29`) |

Enum: `enum_jv_status` (schema 140) `draft, in_review, scheduled, posted, void` · `enum_workflow_type` (276) `purchase_request, store_requisition, purchase_order, gl_jv` · `enum_gl_period_status` (2899) · `enum_gl_budget_status` (2905) · `enum_gl_jv_template_type` (2911) · `enum_gl_amortize_type` (2917) · `enum_gl_side` (2922) · `enum_gl_jv_source` (4724) `manual, recurring, allocation, amortize, reversal, closing, ap, ar, inventory, asset, interface`

## 3. จุดที่ inventory พบกับ ledger

สรุปจาก [gl-posting](/th/inventory/general-ledger/gl-posting):

- **ไม่มีอะไร post** `grep -rn -E "gl[-_]posting|gl[-_]jv|tb_gl_|GlPosting|GlJv|journal" apps/micro-business/src/inventory apps/micro-business/src/procurement` คืน **0 hit** การ commit GRN, การ commit stock-in/stock-out, credit note, store requisition, physical count / spot check, การเขียน cost layer และการปิดงวด inventory ทั้งหมดจบโดยไม่แตะ `tb_gl_jv_header` ผู้เขียน `enum_gl_jv_source` มีเพียง `manual` (`gl-jv.service.ts:214`), `reversal` (`gl-posting.service.ts:571`), `closing` (`:909`, `:1116`) และ template สามประเภท (`gl-jv-template.service.ts:777`)
- **ปฏิทินสองชุด ไม่เชื่อมกัน** การปิด inventory ทำงานบน `tb_inventory_period` (`period-end.close-transaction.helper.ts:80,195,210`); ledger ทำงานบน `tb_gl_period` ไม่มีตารางใดอ้างอิงอีกตาราง `tb_gl_period` ไม่ถูกอ่านที่ไหนนอก `gl/` และ gateway module `config_gl-*` และการปิดอันหนึ่งไม่มีผลต่ออีกอัน
- **`gl_run_due` ไม่ใช่ job ของ inventory** cron (`micro-cronjobs/internal/executor/gl_run_due.go`, job type `gl_run_due`) เรียก `POST /api/internal/gl/run-due` ต่อ business unit ซึ่ง post voucher `scheduled` ที่ `post_at` ผ่านไปแล้ว และ reverse voucher ที่ post แล้วซึ่ง `reverse_at` ผ่านไปแล้ว มัน **ไม่** สร้าง JV template — `generate-all-due` เป็น endpoint แยกที่เรียกด้วยมือ ไม่มี cron เรียก
- **สิ่งที่ต้องเปลี่ยน** เพื่อให้ inventory post ได้: ผู้เรียกภายใน service inventory/procurement ที่สร้างบรรทัด `ICreateGlJv` เรียก `GlJvService.createInternal(..., { source: enum_gl_jv_source.inventory, source_ref_type, source_ref_id })` ภายใน transaction ของตัวเอง แล้ว submit ผ่าน workflow `gl_jv` หรือ post ผ่าน `GlPostingService.post` ไม่มีสิ่งเหล่านั้นอยู่เลย; § 9 ของหน้าย่อยระบุสิ่งที่ tester ควร assert จนกว่าจะมี

## 4. ยังไม่มี frontend

`carmen-inventory-frontend-react/routes/accounting/` ปรากฏใน commit `4a72884d` (2026-07-31, "feat(accounting): add accounting document routes and dashboard") และที่ FE `0713cbc9` (2026-09-22) **เป็น mock**:

- `accounting-documents.ts:100` `documentsFor()` ประดิษฐ์ 8 แถวต่อประเภทเอกสาร (`JV2607-0001…`, คำอธิบาย/คู่ค้าคงที่, `amount = 10000 + index × 3750`); `accounting-detail.tsx` / `accounting-list.tsx` render แถวเหล่านั้น ประกาศไว้เก้าประเภท: journal, template, recurring, allocation voucher, รายงานการเงิน, AP invoice/payment, AR invoice/receipt
- `accounting.dashboard.tsx:143` ห่อ object `data` แบบ hardcode ใน `useQuery({ queryFn: async () => data, initialData: data, staleTime: Infinity })` — ไม่มีการเรียก HTTP
- ไม่มีไฟล์ใต้ `hooks/`, `types/` หรือ `routes/` อ้างถึง `/gl-jv`, `/gl-posting` หรือ `tb_gl_*` router (`routes/router.tsx:770-800`) และ tile ของโมดูล (`constant/module-list.ts:403-425`, licence feature `accounting.gl` / `accounting.gl.jv_template`) เป็นการเชื่อมต่อจริงเพียงอย่างเดียว
- E2E: `../carmen-inventory-frontend-e2e/docs/test-cases/COVERAGE.md:21-28` ระบุทุก URL `/accounting/*` เป็น "none" และ `1204-section-landing.md:15` บันทึกเหตุผลที่ไม่เขียน case (dashboard hardcode ทั้งหกวิดเจ็ตและไม่เรียก API)

จึงไม่มีหน้าจอให้บันทึก ไม่มี Playwright spec ให้เชื่อม และไม่มี screenshot ให้จับ อย่าเขียนหน้า user-flow หรือ test-scenario สำหรับโมดูลนี้จนกว่า UI จริงจะมาถึง

## 5. แหล่งอ้างอิง

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/gl/` (`gl-account-group`, `gl-balance`, `gl-budget`, `gl-jv`, `gl-jv-prefix`, `gl-jv-template`, `gl-period`, `gl-posting`); gateway `apps/backend-gateway/src/application/{gl-jv,gl-posting,gl-reports,gl-budgets,gl-jv-templates}/` และ `config/config_{chart-of-accounts,cost-centers,cost-center-groups,gl-account-groups,gl-jv-prefixes,gl-periods}/`; RPC contract `packages/rpc-contract/src/contracts/gl-posting.ts`
- Prisma: `packages/prisma-shared-schema-tenant/prisma/schema.prisma` และ migration `20260909170000_gl_core_master`, `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path`, `20260915043038_gl_core_budget_template`
- Cron: `../micro-cronjobs/internal/executor/gl_run_due.go`, `internal/model/cronjob.go:141-149`, `README.md:254`
- API contract: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/{gl-jv,gl-posting,gl-reports,gl-budgets,gl-jv-templates}/`
- Frontend (mock เท่านั้น): `../carmen-inventory-frontend-react/routes/accounting/`
- E2E: ไม่มี (`../carmen-inventory-frontend-e2e/docs/test-cases/COVERAGE.md` § Accounting)
- carmen/docs: freeze เมื่อ 2026-04-27 และ **ขัดแย้งกับ HEAD** ในหัวข้อนี้ — `app/inventory-management/inventory-transactions/BR-inventory-transactions.md:21,31,143,162,214` และ `store-requisitions/SR-API-JournalEntry-Endpoints.md` อธิบายการเชื่อม GL อัตโนมัติที่ไม่มีอยู่จริง; อย่าอ้างอิง

## 6. หน้าในโมดูลนี้

- [GL Posting และรอยต่อกับ Inventory](/th/inventory/general-ledger/gl-posting) — `gl-posting` ทำอะไร, lifecycle สถานะ JV และ workflow `gl_jv`, cron `gl_run_due`, request สร้าง template, `tb_gl_period` เทียบกับ `tb_inventory_period` และการยืนยันว่าไม่มีการ post จาก inventory→GL เลย
