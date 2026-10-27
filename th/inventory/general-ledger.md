---
title: บัญชีแยกประเภททั่วไป (General Ledger)
description: ระบบย่อย GL และ AP subledger บันทึกเฉพาะส่วนที่แตะ inventory Inventory ไม่ post เข้า ledger โดยตรง voucher เดียวที่ inventory ป้อนคือ AP invoice ที่สร้างจาก GRN ที่ commit แล้ว
published: true
date: '2026-10-27T15:00:00.000Z'
tags: general-ledger, inventory, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# บัญชีแยกประเภททั่วไป (General Ledger)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ledger แบบ journal-voucher (`tb_gl_jv_header` / `tb_gl_jv_detail` → `tb_gl_balance`) บวก AP และ AR subledger (ตั้งแต่ 2026-09-23) ที่ post เข้าไปผ่าน facade &nbsp;·&nbsp; **ขอบเขตของ wiki:** บันทึก **เฉพาะส่วนที่แตะ inventory**; GL master data, budget, JV template, รายงาน GL, AP payment, AR และ dashboard บัญชี เป็นช่องว่างที่ตั้งใจเว้น (§ 1.1, § 1.2) &nbsp;·&nbsp; **Inventory→GL วันนี้:** **ไม่มีการ post โดยตรง** — ไม่มี GRN, stock-in/out, credit note, store requisition, physical count, cost layer หรือการปิดงวด inventory ใดที่เขียน voucher (ดู [gl-posting](/th/inventory/general-ledger/gl-posting) § 2) **ลิงก์เดียว:** **AP invoice ที่สร้างจากบรรทัด GRN ที่ commit แล้ว** post `Dr inventory / Dr input VAT / Cr AP` และล็อกบรรทัด GRN เหล่านั้นไม่ให้แก้ไข — ดู [AP Invoice from GRN](/th/inventory/general-ledger/ap-invoice-from-grn) &nbsp;·&nbsp; **Frontend:** `routes/accounting` — รายการ/ฟอร์ม journal-voucher และฟอร์ม settings เรียก API จริง; AP, AR, หน้าเอกสาร และ dashboard ยังทำงานบน mock ในเบราว์เซอร์ (§ 4) &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_gl_jv_header`, `tb_gl_jv_detail`, `tb_gl_balance`, `tb_gl_period` (ปฏิทินคนละชุดกับ `tb_inventory_period`), `tb_ap_invoice` + `tb_ap_invoice_detail_source` &nbsp;·&nbsp; **หน้าย่อย:** 2

![บัญชีแยกประเภททั่วไป (General Ledger) screen](/screenshots/general-ledger/index.png)

## 1. ภาพรวม

General Ledger คือระบบย่อย backend ใต้ `apps/micro-business/src/gl/` (NestJS module สิบตัว: `gl-account-group`, `gl-balance`, `gl-budget`, `gl-dimension`, `gl-jv`, `gl-jv-prefix`, `gl-jv-template`, `gl-period`, `gl-posting`, `gl-subledger-posting`) พร้อม route ของ gateway ใต้ `api/:bu_code/gl-*` และ `api/config/:bu_code/gl-*`, tenant migration `20260909170000` … `20260915043038` สำหรับ ledger และ `20260923060040` / `20260930*` สำหรับตาราง AP และ AR และ scheduled job หนึ่งตัวใน `micro-cronjobs` มันคือ ledger บัญชีอเนกประสงค์ — ผังบัญชี, cost center, ปฏิทินการเงิน 13 งวด, journal voucher พร้อม review workflow, ยอดคงเหลือ, budget, template แบบ recurring/allocation/amortize, trial balance

**wiki นี้เป็นคู่มือ inventory ERP ดังนั้น ledger จึงถูกบันทึกเฉพาะที่รอยต่อกับ inventory** (การตัดสินใจของเจ้าของเมื่อ 2026-09-22) รอยต่อนั้น **ยังว่างเปล่าในฝั่ง posting**: ที่ backend `c9d788829` (2026-10-27, ตรวจซ้ำด้วย grep ของ 2026-09-22) ไม่มี code path จากเอกสาร inventory หรือ procurement ใดเข้าสู่ `tb_gl_jv_header` และสมาชิกของ `enum_gl_jv_source` คือ `inventory`, `asset` และ `interface` ถูกประกาศไว้แต่ไม่เคยถูกเขียน สิ่งที่เปลี่ยนคือ `ap` และ `ar` ตอนนี้ถูกเขียนแล้ว - โดย service ของ AP invoice, AP payment และ AR invoice ผ่าน `GlSubledgerPostingService` - และ AP invoice สร้าง *จาก* บรรทัด GRN ที่ commit แล้วได้ ซึ่งเป็นวิธีแรก (และวิธีเดียว) ที่สินค้าที่รับมาไปถึง ledger หน้าย่อยสองหน้าครอบคลุมรอยต่อนี้: [gl-posting](/th/inventory/general-ledger/gl-posting) (grep, voucher ไปถึง `tb_gl_balance` ได้อย่างไร, subledger facade, `gl_run_due`) และ [AP Invoice from GRN](/th/inventory/general-ledger/ap-invoice-from-grn) (route ที่ใช้ GRN, voucher ที่ post, การล็อกแก้ไข GRN และการ export GRN/CN/SR/SI/SO แบบอ่านอย่างเดียวเป็นข้อมูล Dr/Cr)

### 1.1 ตั้งใจไม่บันทึก

ทุกอย่างด้านล่างมีอยู่ในโค้ดและ **ตั้งใจเว้นไว้ไม่ใส่ใน wiki นี้** ตารางนี้อยู่ที่นี่เพื่อให้นักพัฒนาที่ grep identifier ของ GL มาลงที่หน้านี้และรู้ว่านี่คือช่องว่างที่เลือกแล้ว ไม่ใช่ตกหล่น ให้ดู source path โดยตรง

| ส่วน | Backend (`apps/micro-business/src/`) | route ของ gateway (`apps/backend-gateway/src/`) | folder ของ Bruno (`collections/carmen-inventory/_uncategorized/`) | Migration | key ของ permission / licence | Enum |
|---|---|---|---|---|---|---|
| ผังบัญชี (`tb_chart_of_accounts`; เปลี่ยนชื่อจาก account code ขยายด้วย `category`, `is_require_cost_center`, `account_group_id`; import จาก interface `carmen-gl`) | `master/chart-of-accounts/` | `config/config_chart-of-accounts/` → `api/config/:bu_code/chart-of-accounts` (+ `POST import`, `POST import-from-interface/carmen-gl`) | — (collection ของ config) | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` เท่านั้น; ไม่มี `@Permission` บน config controller | `enum_chart_of_accounts_category` (`asset, liability, equity, revenue, expense, statistic`), `enum_chart_of_accounts_type` += `summary` |
| Cost center / กลุ่ม cost center / การเชื่อม cost-center↔account (`tb_cost_center`, `tb_cost_center_group`, `tb_cost_center_account`) | `master/cost-center*/` | `config/config_cost-centers/`, `config/config_cost-center-groups/` | — | `20260904103000_add_cost_center` | Keycloak + `AppIdGuard` | — |
| กลุ่มบัญชี GL (`tb_gl_account_group`, tree ≤ 4 ระดับ, category ต้องตรงกับ parent) | `gl/gl-account-group/` | `config/config_gl-account-groups/` → `api/config/:bu_code/gl-account-groups` | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | — |
| JV prefix (`tb_gl_jv_prefix`; `code` แก้ไม่ได้, `is_system` ลบไม่ได้, `is_default` ตัวเดียว) | `gl/gl-jv-prefix/` | `config/config_gl-jv-prefixes/` → `api/config/:bu_code/gl-jv-prefixes` | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | — |
| งวด GL (`tb_gl_period`; 13 งวดต่อปีการเงินสร้างจาก key `gl_setting`.`fiscal_year_start_month` ใน `tb_application_config`; close/reopen ตามลำดับ) | `gl/gl-period/` | `config/config_gl-periods/` → `api/config/:bu_code/gl-periods` (`POST years`, `POST :id/close`, `POST :id/reopen`) | — | `20260909170000_gl_core_master` | Keycloak + `AppIdGuard` | `enum_gl_period_status` (`open, closed, locked`) |
| Journal voucher — CRUD ของ draft และ review workflow (`tb_gl_jv_header`, `tb_gl_jv_detail`) | `gl/gl-jv/` | `application/gl-jv/` → `api/:bu_code/gl-jv` (11 route) | `gl-jv/*` (11 ไฟล์) | `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path` | licence `accounting.gl`; การร่าง gate ด้วย workflow (`permission.route-map.ts:395-397` ยกเว้น `accounting.gl:create/update/delete`) | `enum_jv_status` += `in_review`, `scheduled`, `void`; `enum_workflow_type` += `gl_jv`; `enum_gl_jv_source` |
| การ post ledger และยอดคงเหลือ (`tb_gl_balance`) — **ครอบคลุมบนหน้าย่อยเฉพาะในฐานะเป้าหมายที่ inventory จะ post ไป** | `gl/gl-posting/`, `gl/gl-balance/` | `application/gl-posting/` → `api/:bu_code/gl-posting` | `gl-posting/*` (6 ไฟล์) | `20260914030000_gl_core_jv_ledger` | `accounting.gl:{post, void, reverse, recalculate, close_year}` (`seed.permission.data.ts`, บล็อก `accounting.gl` ตั้งแต่ ~`:1666`) | — |
| มิติทางบัญชี (`tb_gl_dimension` code ≤ 20 ตัวอักษร, `tb_gl_dimension_value` code ≤ 30 ตัวอักษร พร้อม `effective_from` / `effective_to` ที่ไม่บังคับ, `tb_gl_account_dimension_rule` ที่ `requirement` เป็น `mandatory`/`optional`/`prohibited`, `tb_gl_jv_detail_dimension`) - ใหม่ 2026-09/10; บังคับบนบรรทัด JV ตอน submit และ post | `gl/gl-dimension/` | `config/config_gl-dimensions/`, `config/config_gl-account-dimension-rules/` → `api/config/:bu_code/gl-dimensions`, `…/gl-account-dimension-rules` | — | tenant schema (`enum_gl_account_dimension_rule_requirement`) | Keycloak + `AppIdGuard` | `enum_gl_account_dimension_rule_requirement` (`mandatory, optional, prohibited`) |
| Budget (`tb_gl_budget`, `tb_gl_budget_detail`; revision ที่ active หนึ่งตัวต่อปี) | `gl/gl-budget/` | `application/gl-budgets/` → `api/:bu_code/gl-budgets` (+ `POST :id/activate`) | `gl-budgets/*` (6 ไฟล์) | `20260915043038_gl_core_budget_template` | `accounting.gl.budget:{view, create, update, delete, activate}`; licence `accounting.gl.budget` | `enum_gl_budget_status` (`draft, active, superseded`) |
| JV template (`tb_gl_jv_template`, `_detail`, `_run`; `generate` / `generate-all-due`) | `gl/gl-jv-template/` | `application/gl-jv-templates/` → `api/:bu_code/gl-jv-templates` (+ `POST :id/generate`, `POST generate-all-due`) | `gl-jv-templates/*` (7 ไฟล์) | `20260915043038_gl_core_budget_template` | `accounting.gl.jv_template:{view, create, update, delete, generate}`; licence `accounting.gl.jv_template` | `enum_gl_jv_template_type` (`recurring, allocation, amortize`), `enum_gl_amortize_type` (`day_in_month, monthly`), `enum_gl_side` (`debit, credit`) |
| รายงาน GL — trial balance | `gl/gl-balance/` (raw SQL) | `application/gl-reports/` → `GET api/:bu_code/gl-reports/trial-balance` | `gl-reports/*` (1 ไฟล์) | — | `accounting.gl:view` | — |

Licence feature: `accounting.gl` (parent `accounting`), `accounting.gl.budget` และ `accounting.gl.jv_template` (ลูกของ `accounting.gl`) — `packages/prisma-shared-schema-backstage/prisma/seed.license-feature.data.ts:60,100,108` การ map segment ของ gateway → resource: `packages/prisma-shared-schema-backstage/prisma/permission.route-map.ts:57-61` (`app:gl-jv`, `app:gl-posting`, `app:gl-reports` → `accounting.gl`; `app:gl-budgets` → `accounting.gl.budget`; `app:gl-jv-templates` → `accounting.gl.jv_template`)

### 1.2 ฟีเจอร์บัญชีที่ไม่มีจุดสัมผัสกับ inventory (สรุปเท่านั้น)

| ฟีเจอร์ | อยู่ที่ | ความเชื่อมโยงกับ inventory |
|---|---|---|
| AP payment voucher (ชำระ AP invoice, WHT, FX, deposit) | `micro-business/src/ap/ap-payment/`, `api/:bu_code/ap-payment`; FE `routes/accounting/accounts-payable/payment/` (mock) | ไม่มี - ชำระ AP invoice; post `source = ap` |
| AR invoice / credit note, tax invoice, receipt | `micro-business/src/ar/ar-invoice/`, `api/:bu_code/ar-invoice`; ตาราง `tb_ar_invoice*`, `tb_ar_tax_invoice`, `tb_ar_receipt*` (migration `20260930074505`, `20260930180414`); FE `accounts-receivable/` (mock) | ไม่มี - post `source = ar`; ไม่มีการเคลื่อนไหวสต๊อก |
| dashboard บัญชี, cash forecast, หน้ารายการ/รายละเอียดเอกสารสำหรับ voucher แบบ template / recurring / allocation และรายงานการเงิน | FE `routes/accounting/dashboard`, `documents/` (ข้อมูล mock, `dashboard-mock-data.ts`) | ไม่มี |
| Chart-of-accounts mapping สำหรับ export | `api/:bu_code/account-mapping`, `tb_account_mapping` | ฝั่ง inventory: ดู [chart-of-account-mapping](/th/inventory/master-data/chart-of-account-mapping) |
| AP invoice **จาก GRN** | `api/:bu_code/ap-invoice` | มี - [AP Invoice from GRN](/th/inventory/general-ledger/ap-invoice-from-grn) |

## 2. โมเดลข้อมูล (โครง)

จาก `packages/prisma-shared-schema-tenant/prisma/schema.prisma` ที่ `c9d788829` หนึ่งบรรทัดต่อตาราง; รายละเอียดระดับฟิลด์อยู่นอกขอบเขต (§ 1.1)

| ตาราง (บรรทัดใน schema) | วัตถุประสงค์ |
|---|---|
| `tb_chart_of_accounts` (3067) | บัญชี master: `code`, `nature`, `type` (รวม `header` / `summary` ที่ post ไม่ได้), `category`, `reverse_sign`, `use_in[]`, `is_require_cost_center`, `account_group_id` |
| `tb_cost_center_group` (3112), `tb_cost_center` (3141), `tb_cost_center_account` (3175) | cost center ทางบัญชี (ต่างจาก `tb_department`) จัดกลุ่ม; whitelist แบบเลือกได้ว่า cost center หนึ่งจะ post ไปบัญชีไหนได้ |
| `tb_gl_jv_prefix` (3203) | prefix การออกเลข voucher (`code` ≤ 10 ตัวอักษร, `is_system`, `is_default` ตัวเดียว) |
| `tb_gl_account_group` (3231) | tree การจัดกลุ่มบัญชีสำหรับรายงาน ≤ 4 ระดับ `category` เดียวต่อ subtree |
| `tb_gl_period` (3266) | ปฏิทินการเงิน: `fiscal_year`, `period_no` 1–13 (13 = งวดปรับปรุงสิ้นปีที่ใช้ instant สุดท้ายร่วมกับงวด 12), `start_at`, `end_at`, `status`, `closed_at/by` **ไม่มี relation กับ `tb_inventory_period`** |
| `tb_gl_jv_header` (4902) | header ของ voucher: `jv_no` + `prefix_code`, `jv_date`, `is_adjustment`, `source` (`enum_gl_jv_source`), `source_ref_type/id`, `template_id`, `post_at` / `posted_at`, `is_auto_reverse` / `reverse_at`, `reversal_of_jv_id` / `reversed_by_jv_id`, `void_*`, `total_debit/credit`, `jv_status` บวกคอลัมน์มาตรฐาน `workflow_*` / `user_action` / `last_action*` ที่ทุกเอกสาร workflow มี ป้องกันโดย DB trigger `gl_jv_posted_guard` |
| `tb_gl_jv_detail` (4656) | บรรทัดของ voucher: `chart_of_accounts_id` (+ `account_code/name` แบบ denormalise), `cost_center_id` (+ code/name), `debit` XOR `credit`, `exchange_rate`, `base_debit/credit`, `quantity` |
| `tb_gl_balance` (4713) | ยอดคงเหลือที่ derive ต่อ (`gl_period_id`, `cost_center_id` หรือ nil-uuid, `chart_of_accounts_id`): `opening`, `debit`, `credit` ไม่มี soft-delete ไม่มี `doc_version` เขียนโดย `GlPostingService` เท่านั้นและสร้างใหม่ด้วย `recalculate` |
| `tb_gl_budget` (4736), `tb_gl_budget_detail` (4764) | budget รายปี × revision; หนึ่งบรรทัดต่อ (cost center?, บัญชี, งวด 1–12) |
| `tb_gl_jv_template` (4793), `tb_gl_jv_template_detail` (4838) | template แบบ recurring / allocation / amortize พร้อมช่วงงวด from–to, `frequency_months` และคอลัมน์ต่อ type |
| `tb_gl_jv_template_run` (4869) | fact row "template T สร้าง voucher V สำหรับงวด P"; unique บน (`template_id`, `gl_period_id`) |
| `tb_application_config` (6060) key `gl_setting` | JSON: `fiscal_year_start_month`, `allow_post_to_closed_period`, `reversal_prefix_id`, `retained_earnings_account_id`, `auto_jv_prefix_id` บวก key ของ AP/AR คือ `ap_control_account_id`, `input_vat_account_id`, `wht_payable_account_id`, `advance_deposit_account_id`, `realized_fx_gain_account_id`, `realized_fx_loss_account_id`, `ap_jv_prefix_id`, `ar_control_account_id`, `output_vat_account_id`, `ar_jv_prefix_id` (`GlSetting`, `gl-posting.service.ts:91-106`) |
| `tb_gl_dimension` (7049), `tb_gl_dimension_value` (7079), `tb_gl_account_dimension_rule` (7109), `tb_gl_jv_detail_dimension` (7130) | มิติทางบัญชีและกฎ `mandatory`/`optional`/`prohibited` ต่อบัญชีที่ตรวจบนบรรทัด JV |
| `tb_ap_invoice` (7182), `_detail` (7267), `_detail_source` (7350), `_reference` (7370), `_tax` (7390) | AP invoice / debit note / credit note / deposit; `_detail_source` เชื่อมบรรทัดกับรายการ GRN (`matched_qty`) - ดู [AP Invoice from GRN](/th/inventory/general-ledger/ap-invoice-from-grn) `tb_ap_payment*` (7417+) และ `tb_ar_*` (7637+) อยู่นอกขอบเขต |

Enum: `enum_jv_status` (schema 135) `draft, in_review, scheduled, posted, void` · `enum_workflow_type` (271) `purchase_request, store_requisition, purchase_order, gl_jv, ap_invoice, ap_payment, ar_invoice` · `enum_gl_period_status` (3032) · `enum_gl_budget_status` (3038) · `enum_gl_jv_template_type` (3044) · `enum_gl_amortize_type` (3050) · `enum_gl_side` (3055) · `enum_ap_invoice_doc_type` (300) `invoice, debit_note, credit_note, deposit` · `enum_ap_invoice_status` (307) `draft, in_review, posted, void` · `enum_ap_invoice_source` (314) `manual, grn, copy, excel, ai, interface` · `enum_gl_jv_source` (4885) `manual, recurring, allocation, amortize, reversal, closing, ap, ar, inventory, asset, interface`

## 3. จุดที่ inventory พบกับ ledger

สรุปจาก [gl-posting](/th/inventory/general-ledger/gl-posting) และ [AP Invoice from GRN](/th/inventory/general-ledger/ap-invoice-from-grn):

- **ไม่มีอะไร post โดยตรง** `grep -rn -E "gl[-_]posting|gl[-_]jv|tb_gl_|GlPosting|GlJv|journal" apps/micro-business/src/inventory apps/micro-business/src/procurement` คืน hit เฉพาะใต้ `inventory/accounting-export/` (ชื่อที่มี "GlJournal"; export แบบอ่านอย่างเดียว ไม่เคยเรียก `gl/`) การ commit GRN, การ commit stock-in/stock-out, credit note, store requisition, physical count / spot check, การเขียน cost layer และการปิดงวด inventory ทั้งหมดจบโดยไม่แตะ `tb_gl_jv_header` ผู้เขียน `enum_gl_jv_source` คือ `manual`, `reversal`, `closing`, template สามประเภท และ — ใหม่ — `ap` (AP invoice, AP payment) และ `ar` (AR invoice); `inventory`, `asset`, `interface` ไม่เคยถูกเขียน
- **ลิงก์เดียว: AP invoice จาก GRN** `POST api/:bu_code/ap-invoice/from-grn` แปลงรายการ GRN ที่ committed และ `post_type = ap` เป็น AP invoice แบบ draft (`doc_source = grn`, `tb_ap_invoice_detail_source.matched_qty` ติดตามว่าออก invoice ไปแล้วเท่าใดของแต่ละบรรทัด GRN) การอนุมัติขั้นสุดท้าย post `Dr inventory account / Dr input VAT / Cr AP` ผ่าน `GlSubledgerPostingService`; GRN จะแก้ไขไม่ได้ตราบที่มี invoice ที่ยังใช้งานอ้างอิงอยู่ (`GRN_AP_LINKED_NOT_EDITABLE`) ปริมาณสต๊อกและ cost layer ไม่ถูกแตะโดยกระบวนการนี้ ดังนั้นราคา invoice ที่ต่างจากราคา GRN จะสร้าง `variance_amount` บนบรรทัด invoice แต่ไม่ตีมูลค่าสต๊อกใหม่
- **ปฏิทินสองชุด ไม่เชื่อมกัน** การปิด inventory ทำงานบน `tb_inventory_period`; ledger ทำงานบน `tb_gl_period` ไม่มีตารางใดอ้างอิงอีกตาราง `tb_gl_period` ไม่ถูกอ่านที่ไหนใต้ `inventory/` หรือ `procurement/` และการปิดอันหนึ่งไม่มีผลต่ออีกอัน (AP invoice ตรวจว่า GL period ของ `doc_date` เปิดอยู่)
- **`gl_run_due` ไม่ใช่ job ของ inventory** cron (`micro-cronjobs/internal/executor/gl_run_due.go`, job type `gl_run_due`) เรียก `POST /api/internal/gl/run-due` ต่อ business unit ซึ่ง post voucher `scheduled` ที่ `post_at` ผ่านไปแล้ว และ reverse voucher ที่ post แล้วซึ่ง `reverse_at` ผ่านไปแล้ว มัน **ไม่** สร้าง JV template — `generate-all-due` เป็น endpoint แยกที่เรียกด้วยมือ ไม่มี cron เรียก
- **External export เป็นรอยต่อแยก** `GET api/ext/v1/ap-invoices` (GRN, CN) และ `GET api/ext/v1/gl-journals` (SR, SI, SO) ส่งข้อมูล Dr/Cr ที่สร้างจากเอกสาร inventory และ `tb_account_mapping` ให้ระบบบัญชีภายนอก; ไม่มีสิ่งใดถูกเขียนลง ledger (ดู AP Invoice from GRN § 6)
- **สิ่งที่ต้องเปลี่ยน** เพื่อให้ inventory เองเป็นผู้ post: ผู้เรียกภายใน service inventory/procurement ที่สร้าง `ISubledgerPostingLine` และเรียก `GlSubledgerPostingService.postFromSource({ source: enum_gl_jv_source.inventory, source_ref_type, source_ref_id, ... }, tx)` ภายใน transaction ของตัวเอง ไม่มีสิ่งเหล่านั้นอยู่เลย; [gl-posting](/th/inventory/general-ledger/gl-posting) § 9 ระบุสิ่งที่ tester ควร assert จนกว่าจะมี

## 4. สถานะ frontend

`carmen-frontend/routes/accounting/` (router `routes/router.tsx:885-1030`, launcher สี่ส่วนใน `constant/module-list.ts:151+`: General Ledger `accounting.gl`, Accounts Payable `accounting.ap`, Accounts Receivable `accounting.ar`, Asset) เป็น mock แบบ hardcode เมื่อ 2026-09-22 และตอนนี้ **จริงบางส่วน**:

| หน้าจอ | แหล่งข้อมูล |
|---|---|
| รายการ / ฟอร์ม journal voucher (`/accounting/journal-voucher[/:id]`) | **API จริง** — `journal-voucher-http-repository.ts` เรียก endpoint `GL_JV_*` และ `GL_POSTING_*` (`gl-jv`, `gl-posting` post/void/reverse, `gl-jv-prefixes`); id ที่ขึ้นต้นด้วย `mock-` ยังไป mock repository |
| ฟอร์ม accounting settings (`/accounting/settings`) | **จริง** — อ่าน/เขียน `tb_application_config` key `gl_setting` (`gl-setting-value.ts`, `use-gl-jv-prefix-options.ts`) |
| AP dashboard, รายการ/รายละเอียด AP invoice, รายการ/รายละเอียด AP payment | **Mock** — `use-accounts-payable.ts` สร้าง `createApMockRepository` เสมอ (เก็บใน localStorage, prefix `carmen-ap-mock-v1`); ไม่เรียก `api/:bu_code/ap-invoice` |
| รายการ/รายละเอียด AR invoice | **Mock** (`ar-invoice-model.ts`, `ar-invoice-list.route.tsx`) |
| dashboard บัญชี (`/accounting`, dashboard AP/AR/asset) และ cash forecast | **Mock** — `dashboard-mock-data.ts`; กลุ่มผู้ชมตาม role `accountant` / `controller` / `executive` (`dashboard-access.ts`) |
| หน้า template / recurring / allocation voucher, รายงานการเงิน, AR receipt, asset | **Mock** — `documents/accounting-document-model.ts` |

ความไม่ตรงกันระหว่าง frontend/backend ที่ทราบ (บันทึกไว้เท่านั้น): type ของ UI journal-voucher ใช้สถานะ `submitted`, `posting`, `post_failed`, `voided`, `reversal_scheduled`, `reversed` (`types/journal-voucher.ts:1-10`) ขณะที่ enum ของ backend คือ `draft, in_review, scheduled, posted, void` และ gateway ไม่คืน `capabilities`; `journalVoucherCapabilities` (`journal-voucher-source.ts`) คำนวณปุ่มที่ใช้ได้จาก `jv_status === "submitted"` ดังนั้น voucher จริงที่อยู่ใน `in_review` จะไม่เปิดปุ่ม approve/reject/return ที่นั่น นอกจากนี้ `sourceDocumentHref` จับคู่ `source_type === "ap_invoice"` ขณะที่ค่า `source` ของ backend คือ `ap` (`source_ref_type` คือ `ap_invoice`) ลิงก์ "เปิดเอกสารต้นทาง" จึงจะไม่ resolve สำหรับ voucher ที่สร้างจาก AP ทั้งสองข้อควรเปิด ticket หลังตรวจด้วยมือโดยตั้งค่า workflow `gl_jv`

E2E: `../carmen-frontend-e2e/docs/test-cases/COVERAGE.md` ยังระบุ URL `/accounting/*` ว่าไม่ครอบคลุม ไม่มี Playwright spec ให้เชื่อม; อย่าเขียนหน้า user-flow หรือ test-scenario สำหรับโมดูลนี้จนกว่าหน้าจอ AP/AR จะเลิกเป็น mock

## 5. แหล่งอ้างอิง

- Backend: `../carmen-turborepo-backend/apps/micro-business/src/gl/` (`gl-account-group`, `gl-balance`, `gl-budget`, `gl-jv`, `gl-jv-prefix`, `gl-jv-template`, `gl-period`, `gl-posting`, `gl-dimension`, `gl-subledger-posting`) และ `ap/ap-invoice/`; gateway `apps/backend-gateway/src/application/{gl-jv,gl-posting,gl-reports,gl-budgets,gl-jv-templates}/` และ `config/config_{chart-of-accounts,cost-centers,cost-center-groups,gl-account-groups,gl-jv-prefixes,gl-periods}/`; RPC contract `packages/rpc-contract/src/contracts/gl-posting.ts`
- Prisma: `packages/prisma-shared-schema-tenant/prisma/schema.prisma` และ migration `20260909170000_gl_core_master`, `20260914030000_gl_core_jv_ledger`, `20260915010000_fix_gl_jv_guard_search_path`, `20260915043038_gl_core_budget_template`
- Cron: `../micro-cronjobs/internal/executor/gl_run_due.go`, `internal/model/cronjob.go:141-149`, `README.md:254`
- API contract: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/{gl-jv,gl-posting,gl-reports,gl-budgets,gl-jv-templates,ap-invoice,ap-payment,ar-invoice}/`
- Frontend: `../carmen-frontend/routes/accounting/` (journal-voucher + settings จริง; AP/AR/dashboard/documents เป็น mock)
- E2E: ไม่มี (`../carmen-frontend-e2e/docs/test-cases/COVERAGE.md` § Accounting)
- carmen/docs: freeze เมื่อ 2026-04-27 และ **ขัดแย้งกับ HEAD** ในหัวข้อนี้ — `app/inventory-management/inventory-transactions/BR-inventory-transactions.md:21,31,143,162,214` และ `store-requisitions/SR-API-JournalEntry-Endpoints.md` อธิบายการเชื่อม GL อัตโนมัติที่ไม่มีอยู่จริง; อย่าอ้างอิง

## 6. หน้าในโมดูลนี้

- [GL Posting และรอยต่อกับ Inventory](/th/inventory/general-ledger/gl-posting) — `gl-posting` ทำอะไร, lifecycle สถานะ JV และ workflow `gl_jv`, subledger facade, cron `gl_run_due`, request สร้าง template, `tb_gl_period` เทียบกับ `tb_inventory_period` และการยืนยันว่าไม่มีการ post จาก inventory→GL โดยตรงเลย
- [AP Invoice from GRN](/th/inventory/general-ledger/ap-invoice-from-grn) — เส้นทาง ledger เดียวที่ inventory ป้อน: `grn-candidates` / `from-grn`, `matched_qty`, voucher `Dr inventory / Dr input VAT / Cr AP`, การล็อกแก้ไข GRN, กฎการ void และการ export Dr/Cr ของ GRN/CN/SR/SI/SO ภายนอก
