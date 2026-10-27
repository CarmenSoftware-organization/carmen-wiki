---
title: ผังบัญชี (Chart of Accounts)
description: รหัสบัญชี GL (nature, type, category, account group, กฎ dimension) พร้อมนำเข้าจากไฟล์และ Carmen GL — เปลี่ยนชื่อจาก Account Code 2026-08-27; ป้อน GL, allow-list ศูนย์ต้นทุน และ account mapping
published: true
date: '2026-10-27T15:00:00.000Z'
tags: master-data, chart-of-accounts, general-ledger, configuration, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# ผังบัญชี (Chart of Accounts)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Finance &nbsp;·&nbsp; **ตาราง:** `tb_chart_of_accounts` + `enum_chart_of_accounts_{nature,type,category,use_in}` &nbsp;·&nbsp; **ใช้โดย:** [general-ledger](/th/inventory/general-ledger) (บรรทัด JV, account group), allow-list ของ [cost-center](/th/inventory/master-data/cost-center), override ของ [chart-of-account-mapping](/th/inventory/master-data/chart-of-account-mapping) &nbsp;·&nbsp; **Permission:** `configuration.chart_of_accounts.*` &nbsp;·&nbsp; **Licence key:** `configuration.chart_of_accounts` &nbsp;·&nbsp; รายการรหัสบัญชีของ BU ดูแลได้ผ่านฟอร์มเต็มหน้า, อัปโหลดไฟล์ (API) หรือดึงจาก Carmen GL

![ผังบัญชี (Chart of Accounts) screen](/screenshots/master-data/chart-of-accounts.png)

## 1. คืออะไร / ใครใช้

**ผังบัญชี (Chart of Accounts)** คือรายการรหัสบัญชี GL ที่หน่วยธุรกิจ post ไป แต่ละแถวคือ `code` พร้อมคำอธิบายสองบรรทัด, **nature** ของยอดคงเหลือ (`debit` / `credit`), **type** ของงบ (`header` = หัวข้อกลุ่มที่ไม่ post, `balance_sheet`, `income_statement`, `statistic`, `summary`), **category** ทางบัญชี (`asset` … `statistic` ใช้สำหรับ roll-forward สิ้นปีและจับคู่ account group), ledger ที่**ใช้ได้ใน** (`ap`, `ar`, `gl`, `ast`), flag การแสดงผล `reverse_sign`, flag `is_require_cost_center` ที่บังคับให้ทุกบรรทัด JV ต้องมีศูนย์ต้นทุน และลิงก์ไปยัง GL account group แบบเลือกได้

มันมาเป็นสองขั้น: **Account Code** (`tb_account_code`, `code` / `name` / `description`, 2026-08-20) ถูกเปลี่ยนชื่อและขยายเป็น **Chart of Accounts** เมื่อ 2026-08-27 (`name → description_1`, `description → description_2` บวก `nature`, `type`, `reverse_sign`, `use_in`); migration GL-core เมื่อ 2026-09-09 เพิ่ม `category`, `is_require_cost_center`, `account_group_id` และ type `summary` frontend ตามมาด้วยการเปลี่ยนชื่อสองครั้ง (`account-code → chart-of-account`, 2026-09-03; `chart-of-account → chart-of-accounts`, 2026-09-08) และอยู่ที่ `/config/chart-of-accounts` (list), `/config/chart-of-accounts/new` และ `/config/chart-of-accounts/:id` (ฟอร์มเต็มหน้า แทนที่ dialog เดิม; `coa-new.route.tsx`, `coa-edit.route.tsx`) หน้าจอที่เกี่ยวข้อง: Account Grouping (`/config/account-grouping` สรุปไว้ใน [master-data landing](/th/inventory/master-data) § 3.5) ดูแลต้นไม้ account-group ที่ฟิลด์ **Account group** ชี้ไป **บริหารจัดการโดย** Sysadmin / Finance **อ่านโดย** ทุกเส้นทาง GL posting และการตั้งค่าศูนย์ต้นทุน

**กฎ dimension** ต่อบัญชี (dimension GL ใดบ้างที่ mandatory / optional / prohibited บนบรรทัด JV) เก็บแยกใน `tb_gl_account_dimension_rule` (`api/config/:bu_code/gl-account-dimension-rules`, `requirement` = `mandatory` \| `optional` \| `prohibited`, unique ต่อ account x dimension) และฟอร์มบันทึกด้วยการเรียก create/update/delete หนึ่งครั้งต่อ dimension หลังบันทึกตัวบัญชีเอง

อย่าสับสนกับ `tb_product_account_code_mapping` ฝั่งสินค้าที่เก่ากว่า ([product/01-data-model](/th/inventory/product/01-data-model) § 2.11) — ตารางนั้นเก็บ string `account_code` แบบ free-text ต่อสินค้า / ระดับการจำแนก และ**ไม่มี FK** มายังตารางนี้

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มบัญชี | Configuration → Chart of Accounts → **New** (ฟอร์มเต็มหน้า, `/config/chart-of-accounts/new`) | บังคับ: `code`, `description_1`, `category`, `nature`, `type` การเลือก **category** จะตั้ง **nature** อัตโนมัติ (`liability` / `equity` / `revenue` → `credit` นอกนั้น `debit`; `natureFor()`) และ picker ของ account-group แสดงเฉพาะกลุ่มที่มี category เดียวกัน `description_2`, `account_group_id`, `is_active` ไม่บังคับ **แก้ไขแล้วตั้งแต่รอบ 2026-09-22:** ฟอร์มตอนนี้ส่ง `category` ช่องว่างของ create-DTO ก่อนหน้าจึงปิดแล้ว (§ 3) |
| Filter รายการ | filter sheet บน toolbar | เลือกหลายค่าตาม `category`, `nature` และ `type` (`coa-filter-fields.ts`) บวก status/search |
| รัน wizard เทมเพลตเริ่มต้น | ปุ่ม **COA Wizard** บน list (`coa-wizard-modal.tsx`) | **UI stub:** modal แสดงรายการ business module (ห้องพักโรงแรม, ร้านอาหาร F&B, banquet…) แต่ **Apply** แสดงแค่ toast สำเร็จ — ไม่เรียก API และไม่สร้างบัญชี |
| โหลดจากไฟล์แบบ bulk | API เท่านั้น — `POST /api/config/:bu_code/chart-of-accounts/import` (multipart `file`, เลือกได้ `duplicate_mode`) | `.xlsx` หรือ `.csv` เลือกตาม magic bytes; all-or-nothing; ไม่พบปุ่มบน frontend ในรอบนี้ |
| ดึงจาก Carmen GL | ปุ่ม **Import from Carmen GL** (`coa-import-carmen-gl-button.tsx`) → `POST …/import-from-interface/carmen-gl` | ปุ่ม render เฉพาะเมื่อ interface entitlement `accounting.carmen_gl` ของ BU เป็น `entitled` และผู้ใช้เขียนได้; นโยบาย duplicate / local-only มาจาก app-config `interface_accounting_carmen_gl.sync_policy` ไม่เคยมาจาก request |
| ลิงก์ไปยัง account group | ฟิลด์ **Account group** บนฟอร์ม (tree picker, `coa-tree-selector-modal.tsx`) หรือ dialog assign ของหน้า Account Grouping | `account_group_id` รับทั้งตอน create **และ** update (fix `ce56a37b7`) และ service บังคับใช้ (`checkAccountGroup`): กลุ่มต้องมีอยู่, เป็น **leaf** และมี **category เดียวกัน** กับบัญชี — ดู § 3 |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก picker; ประวัติ JV ไม่ได้รับผลกระทบ |
| ลบ | action **Delete** | Backend: soft-delete แบบไม่มีเงื่อนไข — ไม่มีการเช็คแถว allow-list ของศูนย์ต้นทุน, account mapping หรือบรรทัด JV (ดู § 6) frontend เพิ่ม *guardrail dialog* ที่บล็อกการลบเมื่อ `account.is_used` เป็น true และแนะนำให้ deactivate แทน แต่ **ไม่มีฟิลด์ backend ชื่อ `is_used`** (grep ใน DTO ของ gateway, service ของ micro-business และ swagger ไม่พบ) ดังนั้นการบล็อกไม่เคยแสดง — ถือว่ายังไม่ได้ wire |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| `409 CHART_OF_ACCOUNTS_DUPLICATE_CODE` — "Chart of accounts code already exists" | แถวอื่นที่ยังไม่ถูกลบมี `code` เดียวกัน (pre-check แบบไม่สนตัวพิมพ์ใน `create()` / `update()` หนุนด้วย partial unique index `chartofaccounts_code_live_u`; race ที่แพ้ตอน insert ถูกแปลจาก Prisma `P2002` เป็น 409 เดียวกัน) | เลือก code อื่นหรือกู้คืนแถวที่ soft-delete |
| `400 CHART_OF_ACCOUNTS_CATEGORY_REQUIRED` — "Chart of accounts category is required" | `create()` บังคับ `category` เสมอ; `update()` บังคับเมื่อแถวที่เก็บอยู่ยังมี `category = null` (แถวที่สร้างก่อน 2026-09-09) และ request ไม่ได้ส่งมา | ส่งหนึ่งใน `asset`, `liability`, `equity`, `revenue`, `expense`, `statistic` |
| `404 GL_ACCOUNT_GROUP_NOT_FOUND` / `400 GL_ACCOUNT_GROUP_NOT_LEAF` / `400 GL_ACCOUNT_GROUP_CATEGORY_MISMATCH` | `account_group_id` ระบุกลุ่มที่ไม่มีอยู่, กลุ่มที่มีลูก หรือกลุ่มที่ category ต่างจากบัญชี ตรวจซ้ำตอน update ด้วยเมื่อมีแค่ category เปลี่ยนขณะบัญชียังอยู่ในกลุ่ม | เลือกกลุ่ม leaf ที่ category เดียวกัน |
| **แก้ไขแล้ว: "create DTO ต้องการ `category` ที่ FE ไม่เคยส่ง" ของรอบก่อน** | create DTO ของ gateway ยังต้องการ `category` (`chart-of-accounts.dto.ts:36`), `reverse_sign` / `use_in` / `is_require_cost_center` มี default เป็น `false` / `[]` / `false` ฟอร์มใหม่ (`coa-form.tsx`, สร้าง payload ที่ `:128-143`) ส่ง `category`, `nature`, `type` ทุกครั้งแล้ว | ปิดแล้ว ความไม่ตรงที่เหลือ: ฟอร์มยังส่ง `allowed_departments`, `department_required`, `allowed_dimensions`, `dimension_required`, `attributes`, `grouping_path` ซึ่ง DTO create/update ของ gateway ไม่ประกาศ (ไม่ปรากฏทั้งใน DTO และ service ของ micro-business) ดังนั้น *toggle* ของ department / dimension และ allowed-list บนฟอร์ม **ไม่ถูกบันทึก** โดยการเรียกนี้; มีเพียง *กฎ* dimension เท่านั้นที่บันทึก (ผ่าน `gl-account-dimension-rules`) ฟอร์มยังตั้ง `reverse_sign`, `use_in` หรือ `is_require_cost_center` ไม่ได้ |
| `404 CHART_OF_ACCOUNTS_NOT_FOUND` | id ที่ไม่รู้จักหรือถูก soft-delete | — |
| `400` ตอนนำเข้าไฟล์: "file is empty / missing required column / over the row limit / has failing rows (nothing was written)" | `importFile()` บังคับคอลัมน์ `Code`, `Description 1` (alias `description_1`, `name`), `Nature`, `Type`; เลือกได้ `Description 2` (`description`), `Reverse sign`, `Use in`, `Active`; สูงสุด `MAX_IMPORT_ROWS = 2000`; `MAX_CODE_LENGTH = 50`; แถวใดผิดพลาดจะยกเลิกการนำเข้าทั้งหมดและคืนแถวเหล่านั้นใต้ `data.errors` (จำกัดที่ `MAX_SUMMARY_ERRORS = 100`) | แก้ไฟล์แล้วส่งใหม่ |
| "duplicate_mode must be one of: skip, upsert, error" | form field `duplicate_mode` ไม่ถูกต้อง (default `skip`) | — |
| `400 CHART_OF_ACCOUNTS_INTERFACE_NOT_CONFIGURED` / `…_DISABLED` | ไม่มีแถว app-config `interface_accounting_carmen_gl` หรือถูกปิดใช้งาน | ตั้งค่า interface ใต้ Application Config |
| `502 CHART_OF_ACCOUNTS_INTERFACE_REQUEST_FAILED` — "…failed with status {status}" | endpoint ของ Carmen 4 เข้าไม่ถึง / non-2xx; frontend แสดงข้อความจาก server ตัวนี้ตรง ๆ (กรณีพิเศษ `INTERFACE_REQUEST_FAILED` ในปุ่ม) | ตรวจ token / URL |
| `400 CHART_OF_ACCOUNTS_INTERFACE_MULTI_PAGE` / `…_TOKEN_UNREADABLE` | upstream คืนมากกว่าหนึ่งหน้า (รองรับหน้าเดียวเท่านั้น); interface token ถอดรหัสไม่ได้ (`SECRET_ENCRYPTION_KEY`) | Ops แก้ไข |

## 4. Edge Cases

- **type `summary` มองเห็นใน UI แล้ว** `ALTER TYPE … ADD VALUE 'summary'` รันใน `20260909170000_gl_core_master`; enum `CHART_OF_ACCOUNT_TYPE` ของ frontend ตอนนี้มี `SUMMARY` (`types/chart-of-accounts.ts:13-19`) ดังนั้น edge case "label ของ type ว่างเปล่า" ก่อนหน้านี้ไม่เกิดอีก
- **Category ถูกล็อกเมื่อมีการใช้งาน** ฟอร์ม disable **category** เมื่อ `is_used` เป็น true และ category ที่เก็บไว้ไม่ null (`categoryLocked`); เนื่องจาก backend ไม่เคยส่ง `is_used` ในทางปฏิบัติจึงไม่เคยถูกล็อก
- **การจับคู่คอลัมน์ตอนนำเข้ายืดหยุ่น** header ถูก normalise (ตัวพิมพ์ / ช่องว่าง) และ parser เลือก sheet ชื่อ "chart of accounts" หรือ "account code" ก่อน; `description_1` / `description_2` รับ header แบบเดิม `name` / `description` ด้วย ดังนั้นไฟล์ยุค Account-Code ยังโหลดได้ MIME type ที่อัปโหลดไม่เคยถูกเชื่อถือ — `.xlsx` ตรวจจับด้วย ZIP magic bytes
- **การ map จาก Carmen GL** Carmen 4 ไม่มีแนวคิด `header`; แถว header มีเฉพาะเมื่อสร้างในเครื่อง nature มาจาก `Debit` / `Credit`; type ถูก map ผ่าน `CARMEN_TYPE_MAP`
- **sync policy เป็น config ไม่ใช่ request** `on_duplicate ∈ {skip (default), upsert, error}`, `on_local_only ∈ {keep (default), delete}` — `delete` จะ soft-delete ทุกรหัสในเครื่องที่ยังใช้งานซึ่งไม่มีในรายการ upstream และรายงานเป็น `deleted_codes` (100 ตัวแรก) summary ของ response คือ `{ created, updated, skipped, deleted }` บวก `errors[]`
- **การลบบัญชีที่ใช้งานอยู่ไม่ถูกบล็อก** `delete()` (`chart-of-accounts.service.ts:355`) soft-delete แบบไม่มีเงื่อนไข; แถว `tb_cost_center_account`, override `tb_account_mapping.account_code`, `tb_tax_profile.chart_of_accounts_id` และบรรทัด JV ยังชี้มาที่มัน ถือว่า "cannot delete — referenced by JV" **ไม่ถูกบังคับใช้**
- **`account_group` บน wire มีแค่ id** response ของ detail / list คืน `account_group: { id }` โดยไม่มีชื่อ (หมายเหตุของ frontend ใน `types/chart-of-accounts.ts`); ฟอร์ม resolve ชื่อจาก list `gl-account-groups`

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`, line ~2934)

### 5.1 `tb_chart_of_accounts`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | รหัสบัญชี เช่น `1140-001`; ≤ 50 ตัวอักษรตอนนำเข้า |
| `description_1` | `String @db.VarChar` | No | คำอธิบายหลัก (เดิม `name`) |
| `description_2` | `String? @db.VarChar` | Yes | คำอธิบายรอง (เดิม `description`) |
| `nature` | `enum_chart_of_accounts_nature` | No | `debit` \| `credit` |
| `type` | `enum_chart_of_accounts_type` | No | `header` \| `balance_sheet` \| `income_statement` \| `statistic` \| `summary` |
| `category` | `enum_chart_of_accounts_category?` | Yes (schema) / **API บังคับ** | `asset` \| `liability` \| `equity` \| `revenue` \| `expense` \| `statistic` nullable เพียงเพื่อให้แถวก่อน 2026-09-09 migrate ได้ |
| `reverse_sign` | `Boolean` | No | กลับเครื่องหมายเมื่อแสดงในรายงาน (default `false`) |
| `use_in` | `enum_chart_of_accounts_use_in[]` | No | subset ของ `ap`, `ar`, `gl`, `ast`; default `[]` = ยังไม่ได้กำหนด |
| `is_require_cost_center` | `Boolean` | No | Default `false` เมื่อเป็น `true` ทุกบรรทัด JV บนบัญชีนี้ต้องมี `cost_center_id` และถ้าศูนย์ต้นทุนมี allow-list บัญชีนี้ต้องอยู่ในนั้น (comment ใน schema; การบังคับใช้อยู่ใน GL JV service) |
| `account_group_id` | `String? @db.Uuid` | Yes | FK → `tb_gl_account_group` (`onDelete: NoAction`); หนึ่งบัญชี : หนึ่งกลุ่ม |
| `is_active` | `Boolean?` | Yes | Default `true` |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| `doc_version` | `Int` | No | เวอร์ชัน optimistic-lock (default `0`) |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([code, deleted_at])` map `chartofaccounts_code_u`; partial unique `chartofaccounts_code_live_u` บน `(code) WHERE deleted_at IS NULL` (อยู่ใน migration SQL เท่านั้น — Prisma แสดงออกไม่ได้); index `chartofaccounts_code_idx`, `chartofaccounts_description_1_idx`, `chartofaccounts_account_group_id_idx` Reverse relation `tb_cost_center_account[]`

### 5.2 Enums

```
enum_chart_of_accounts_nature   { credit, debit }
enum_chart_of_accounts_type     { header, balance_sheet, income_statement, statistic, summary }
enum_chart_of_accounts_category { asset, liability, equity, revenue, expense, statistic }
enum_chart_of_accounts_use_in   { ap, ar, gl, ast }
```

## 6. กติกาทางธุรกิจ

- **Uniqueness** `code` unique ในแถว non-deleted แบบไม่สนตัวพิมพ์ที่ service และ partial-unique ที่ DB; `code` และ `description_1` ถูก trim ก่อนเช็ค
- **category บังคับนับจากนี้ไป** create เสมอ; update เมื่อใดก็ตามที่แถวยังไม่มี
- **กฎ account-group** หนึ่งบัญชี : หนึ่งกลุ่ม; กลุ่มต้องเป็น leaf ที่ category เดียวกัน (`checkAccountGroup` กฎเดียวกับ `GlAccountGroupService.setAccounts`)
- **Deletion guard — ไม่มีฝั่ง server** soft-delete แบบไม่มีเงื่อนไข (`is_active: false`, `deleted_at`) ไม่มีการเช็คการอ้างอิง; guardrail ฝั่ง frontend พึ่งฟิลด์ `is_used` ที่ API ไม่ส่งกลับ
- **การนำเข้าเป็น transaction** ตัวนำเข้าทั้งสองตรวจสอบทุกแถวก่อน แล้วเขียนใน transaction เดียว; แถวซ้ำ*ภายใน*ไฟล์ / response เดียวกันถูกปฏิเสธ ("Duplicate of row N")
- **Lifecycle** `is_active = false` ซ่อนจาก picker; `use_in = []` หมายถึง "ยังไม่ได้กำหนดให้ ledger ใด" และเป็น default ของแถวที่นำเข้าเว้นแต่ไฟล์จะระบุอย่างอื่น
- **Default sort** `code:asc, id:asc` เมื่อไม่ส่ง `?sort=` (`chart-of-accounts.service.ts:173`)
- **Optimistic lock** update ต้องส่ง `doc_version` ปัจจุบัน
- **การเข้าถึง** route map `config:chart-of-accounts → configuration.chart_of_accounts`; แถว permission ถูก seed ไว้ (`seed.permission.data.ts:961-976`); licence feature `configuration.chart_of_accounts` (`seed.license-feature.data.ts:156`); รายการเมนูของ frontend ถูก gate ด้วย licence (`module-list.ts:486-487`) handler นำเข้าทั้งสองใช้ `AppIdGuard('chart-of-accounts.import')` / `('chart-of-accounts.import-from-interface.carmen-gl')`

## 7. การอ้างอิงข้ามโมดูล

- [general-ledger](/th/inventory/general-ledger) — account group (`tb_gl_account_group`), JV prefix, GL period และกติกา JV posting ที่บริโภค `nature`, `use_in` และ `is_require_cost_center`
- [cost-center](/th/inventory/master-data/cost-center) — แถว allow-list `tb_cost_center_account` อ้างอิงตารางนี้
- [chart-of-account-mapping](/th/inventory/master-data/chart-of-account-mapping) — override บัญชีต่อ location x item group ต้องเป็นรหัส active จากตารางนี้
- [tax-profile](/th/inventory/master-data/tax-profile) — `chart_of_accounts_id` ที่ไม่บังคับ (เฉพาะบัญชีที่ postable)
- [product/01-data-model](/th/inventory/product/01-data-model) § 2.11 — `tb_product_account_code_mapping` แบบ free-text ที่ไม่เกี่ยวข้องกัน
- [system-config/application-config](/th/inventory/system-config/application-config) — key `interface_accounting_carmen_gl` ที่ขับเคลื่อนการนำเข้าจาก GL

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_chart_of_accounts` (line ~2934), enums (~2875-2932), `tb_gl_account_group` (~3093)
- **Migrations:** `20260820140000_add_account_code`, `20260827140000_rename_account_code_to_chart_of_accounts`, `20260909170000_gl_core_master`
- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/master/chart-of-accounts/chart-of-accounts.service.ts` (`checkAccountGroup` `:200`, create `:226`, update `:282`, delete `:355`, `importFile` `:650`, `importFromInterfaceCarmenGl` `:847`; การดึง Carmen 4 ตอนนี้อยู่ใน helper ที่ใช้ร่วมกัน `master/carmen-gl-interface/carmen-gl-interface.ts` ซึ่ง import ของ cost-center ก็ใช้ด้วย; handler `findAllById` ที่ไม่ได้ใช้ถูกลบแล้ว), `chart-of-accounts.import.ts` (การ resolve คอลัมน์, ขีดจำกัด); gateway `apps/backend-gateway/src/config/config_chart-of-accounts/` (`@Controller('api/config/:bu_code/chart-of-accounts')`, handler นำเข้า `:477`, `:583`), DTO `common/dto/chart-of-accounts/chart-of-accounts.dto.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/chart-of-accounts/*.bru` (8 request รวม `POST-import-file-*` และ `POST-import-from-interface-carmen-gl-*`)
- **Frontend:** `../carmen-frontend/routes/config/chart-of-accounts/` (`coa-form.tsx`, `coa-form-schema.ts`, `coa-filter-fields.ts`, `coa-dimension-rules.ts`, `coa-delete-guardrail-dialog.tsx`, `coa-import-carmen-gl-button.tsx`), `types/chart-of-accounts.ts`, `constant/api-endpoints.ts:60-67`
- **E2E:** `../carmen-frontend-e2e/tests/082-chart-of-accounts.spec.ts` (16 กรณี; กรณี multi-select filter, export, แก้ nature/type, licence หมดอายุ และนำเข้าจาก Carmen GL ถูกลิสต์ว่า skipped ใน header ของไฟล์), `docs/user-stories/082-chart-of-accounts.md`
