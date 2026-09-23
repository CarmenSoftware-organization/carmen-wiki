---
title: ผังบัญชี (Chart of Accounts)
description: รหัสบัญชี GL (nature, type, category, use-in, flag ศูนย์ต้นทุน) พร้อมการนำเข้าจากไฟล์และ Carmen GL — เปลี่ยนชื่อจาก Account Code เมื่อ 2026-08-27; ป้อนให้ GL book และ allow-list ของศูนย์ต้นทุน
published: true
date: '2026-09-23T01:30:00.000Z'
tags: master-data, chart-of-accounts, general-ledger, configuration, carmen-software
editor: markdown
dateCreated: '2026-09-22T18:00:00.000Z'
---

# ผังบัญชี (Chart of Accounts)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Finance &nbsp;·&nbsp; **ตาราง:** `tb_chart_of_accounts` + `enum_chart_of_accounts_{nature,type,category,use_in}` &nbsp;·&nbsp; **ใช้โดย:** [general-ledger](/en/inventory/general-ledger) (บรรทัด JV, account group), allow-list ของ [cost-center](/th/inventory/master-data/cost-center) &nbsp;·&nbsp; **Permission:** `configuration.chart_of_accounts.*` &nbsp;·&nbsp; **Licence key:** `configuration.chart_of_accounts` &nbsp;·&nbsp; รายการรหัสบัญชีของ BU ดูแลได้ผ่าน dialog, อัปโหลดไฟล์ หรือดึงจาก Carmen GL

## 1. คืออะไร / ใครใช้

**ผังบัญชี (Chart of Accounts)** คือรายการรหัสบัญชี GL ที่หน่วยธุรกิจ post ไป แต่ละแถวคือ `code` พร้อมคำอธิบายสองบรรทัด, **nature** ของยอดคงเหลือ (`debit` / `credit`), **type** ของงบ (`header` = หัวข้อกลุ่มที่ไม่ post, `balance_sheet`, `income_statement`, `statistic`, `summary`), **category** ทางบัญชี (`asset` … `statistic` ใช้สำหรับ roll-forward สิ้นปีและจับคู่ account group), ledger ที่**ใช้ได้ใน** (`ap`, `ar`, `gl`, `ast`), flag การแสดงผล `reverse_sign`, flag `is_require_cost_center` ที่บังคับให้ทุกบรรทัด JV ต้องมีศูนย์ต้นทุน และลิงก์ไปยัง GL account group แบบเลือกได้

มันมาเป็นสองขั้น: **Account Code** (`tb_account_code`, `code` / `name` / `description`, 2026-08-20) ถูกเปลี่ยนชื่อและขยายเป็น **Chart of Accounts** เมื่อ 2026-08-27 (`name → description_1`, `description → description_2` บวก `nature`, `type`, `reverse_sign`, `use_in`); migration GL-core เมื่อ 2026-09-09 เพิ่ม `category`, `is_require_cost_center`, `account_group_id` และ type `summary` frontend ตามมาด้วยการเปลี่ยนชื่อสองครั้ง (`account-code → chart-of-account`, 2026-09-03; `chart-of-account → chart-of-accounts`, 2026-09-08) และอยู่ที่ `/config/chart-of-accounts` **บริหารจัดการโดย** Sysadmin / Finance **อ่านโดย** ทุกเส้นทาง GL posting และการตั้งค่าศูนย์ต้นทุน

อย่าสับสนกับ `tb_product_account_code_mapping` ฝั่งสินค้าที่เก่ากว่า ([product/01-data-model](/th/inventory/product/01-data-model) § 2.11) — ตารางนั้นเก็บ string `account_code` แบบ free-text ต่อสินค้า / ระดับการจำแนก และ**ไม่มี FK** มายังตารางนี้

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มบัญชี | Configuration → Chart of Accounts → **New** (dialog) | ฟอร์ม frontend (`coa-form-schema.ts`): `code`, `description_1` (บังคับ), `description_2`, `nature`, `type`, `is_active` **ดู § 3 — API บังคับ `category` ซึ่ง dialog ไม่ได้ส่ง** |
| Filter รายการ | filter sheet บน toolbar | ตาม `nature` และ `type` (`coa-filter-fields.ts`) บวก active/search ตามปกติ |
| โหลดจากไฟล์แบบ bulk | API เท่านั้น — `POST /api/config/:bu_code/chart-of-accounts/import` (multipart `file`, เลือกได้ `duplicate_mode`) | `.xlsx` หรือ `.csv` เลือกตาม magic bytes; all-or-nothing; ไม่พบปุ่มบน frontend ในรอบนี้ |
| ดึงจาก Carmen GL | ปุ่ม **Import from Carmen GL** (`coa-import-carmen-gl-button.tsx`) → `POST …/import-from-interface/carmen-gl` | ปุ่ม render เฉพาะเมื่อ interface entitlement `accounting.carmen_gl` ของ BU เป็น `entitled` และผู้ใช้เขียนได้; นโยบาย duplicate / local-only มาจาก app-config `interface_accounting_carmen_gl.sync_policy` ไม่เคยมาจาก request |
| ลิงก์ไปยัง account group | API เท่านั้น — `account_group_id` ตอน create/update | comment ใน schema บอกว่าลิงก์ได้เฉพาะกลุ่มระดับ **leaf** และ service บังคับใช้; ไม่พบการเช็คแบบนั้นใน `chart-of-accounts.service.ts` ในรอบนี้ (ยังไม่ยืนยัน) |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก picker; ประวัติ JV ไม่ได้รับผลกระทบ |
| ลบ | action **Delete** | soft-delete แบบไม่มีเงื่อนไข — ไม่มีการเช็คแถว allow-list ของศูนย์ต้นทุนหรือบรรทัด JV (ดู § 6) |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| `409 CHART_OF_ACCOUNTS_DUPLICATE_CODE` — "Chart of accounts code already exists" | แถวอื่นที่ยังไม่ถูกลบมี `code` เดียวกัน (pre-check แบบไม่สนตัวพิมพ์ใน `create()` / `update()` หนุนด้วย partial unique index `chartofaccounts_code_live_u`; race ที่แพ้ตอน insert ถูกแปลจาก Prisma `P2002` เป็น 409 เดียวกัน) | เลือก code อื่นหรือกู้คืนแถวที่ soft-delete |
| `400 CHART_OF_ACCOUNTS_CATEGORY_REQUIRED` — "Chart of accounts category is required" | `create()` บังคับ `category` เสมอ; `update()` บังคับเมื่อแถวที่เก็บอยู่ยังมี `category = null` (แถวที่สร้างก่อน 2026-09-09) และ request ไม่ได้ส่งมา | ส่งหนึ่งใน `asset`, `liability`, `equity`, `revenue`, `expense`, `statistic` |
| **ช่องว่างของ contract ระหว่าง frontend / API (พบในรอบนี้ ยังไม่ได้ยืนยันบนระบบจริง)** | create DTO ของ gateway ประกาศ `category: z.nativeEnum(enum_chart_of_accounts_category)` โดยไม่มี default (`common/dto/chart-of-accounts/chart-of-accounts.dto.ts:36`) แต่ Zod schema ของ dialog และ `CreateChartOfAccountDto` (`types/chart-of-accounts.ts`) ไม่มี `category`, `reverse_sign`, `use_in` หรือ `is_require_cost_center` | คาดว่าจะได้ `400` จาก dialog **New** จนกว่า frontend จะเพิ่มฟิลด์; การสร้างผ่าน Bruno / การนำเข้าไฟล์ทำงานได้ ยกธงเป็นคำถามที่ยังเปิดอยู่ |
| `404 CHART_OF_ACCOUNTS_NOT_FOUND` | id ที่ไม่รู้จักหรือถูก soft-delete | — |
| `400` ตอนนำเข้าไฟล์: "file is empty / missing required column / over the row limit / has failing rows (nothing was written)" | `importFile()` บังคับคอลัมน์ `Code`, `Description 1` (alias `description_1`, `name`), `Nature`, `Type`; เลือกได้ `Description 2` (`description`), `Reverse sign`, `Use in`, `Active`; สูงสุด `MAX_IMPORT_ROWS = 2000`; `MAX_CODE_LENGTH = 50`; แถวใดผิดพลาดจะยกเลิกการนำเข้าทั้งหมดและคืนแถวเหล่านั้นใต้ `data.errors` (จำกัดที่ `MAX_SUMMARY_ERRORS = 100`) | แก้ไฟล์แล้วส่งใหม่ |
| "duplicate_mode must be one of: skip, upsert, error" | form field `duplicate_mode` ไม่ถูกต้อง (default `skip`) | — |
| `400 CHART_OF_ACCOUNTS_INTERFACE_NOT_CONFIGURED` / `…_DISABLED` | ไม่มีแถว app-config `interface_accounting_carmen_gl` หรือถูกปิดใช้งาน | ตั้งค่า interface ใต้ Application Config |
| `502 CHART_OF_ACCOUNTS_INTERFACE_REQUEST_FAILED` — "…failed with status {status}" | endpoint ของ Carmen 4 เข้าไม่ถึง / non-2xx; frontend แสดงข้อความจาก server ตัวนี้ตรง ๆ (กรณีพิเศษ `INTERFACE_REQUEST_FAILED` ในปุ่ม) | ตรวจ token / URL |
| `400 CHART_OF_ACCOUNTS_INTERFACE_MULTI_PAGE` / `…_TOKEN_UNREADABLE` | upstream คืนมากกว่าหนึ่งหน้า (รองรับหน้าเดียวเท่านั้น); interface token ถอดรหัสไม่ได้ (`SECRET_ENCRYPTION_KEY`) | Ops แก้ไข |

## 4. Edge Cases

- **type `summary` มีจริงใน DB แต่ UI มองไม่เห็น** `ALTER TYPE … ADD VALUE 'summary'` รันใน `20260909170000_gl_core_master`; `CHART_OF_ACCOUNT_TYPES` ของ frontend ยังลิสต์แค่สี่ค่า ดังนั้นแถว `summary` ที่นำเข้าจาก GL จะแสดง label ของ type ว่างเปล่าใน dialog
- **การจับคู่คอลัมน์ตอนนำเข้ายืดหยุ่น** header ถูก normalise (ตัวพิมพ์ / ช่องว่าง) และ parser เลือก sheet ชื่อ "chart of accounts" หรือ "account code" ก่อน; `description_1` / `description_2` รับ header แบบเดิม `name` / `description` ด้วย ดังนั้นไฟล์ยุค Account-Code ยังโหลดได้ MIME type ที่อัปโหลดไม่เคยถูกเชื่อถือ — `.xlsx` ตรวจจับด้วย ZIP magic bytes
- **การ map จาก Carmen GL** Carmen 4 ไม่มีแนวคิด `header`; แถว header มีเฉพาะเมื่อสร้างในเครื่อง nature มาจาก `Debit` / `Credit`; type ถูก map ผ่าน `CARMEN_TYPE_MAP`
- **sync policy เป็น config ไม่ใช่ request** `on_duplicate ∈ {skip (default), upsert, error}`, `on_local_only ∈ {keep (default), delete}` — `delete` จะ soft-delete ทุกรหัสในเครื่องที่ยังใช้งานซึ่งไม่มีในรายการ upstream และรายงานเป็น `deleted_codes` (100 ตัวแรก) summary ของ response คือ `{ created, updated, skipped, deleted }` บวก `errors[]`
- **การลบบัญชีที่ใช้งานอยู่ไม่ถูกบล็อก** `delete()` soft-delete แบบไม่มีเงื่อนไข; แถว `tb_cost_center_account` ที่ชี้มาและบรรทัด JV ยังเก็บ FK (`onDelete: NoAction`) ถือว่า "cannot delete — referenced by JV" **ไม่ถูกบังคับใช้**
- **`account_group` บน wire มีแค่ id** response ของ detail / list คืน `account_group: { id }` โดยไม่มีชื่อ (หมายเหตุของ frontend ใน `types/chart-of-accounts.ts`) และยังไม่มี call site ใดใน frontend อ่านมัน

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
- **Deletion guard — ไม่มี** soft-delete แบบไม่มีเงื่อนไข (`is_active: false`, `deleted_at`) ไม่มีการเช็คการอ้างอิง
- **การนำเข้าเป็น transaction** ตัวนำเข้าทั้งสองตรวจสอบทุกแถวก่อน แล้วเขียนใน transaction เดียว; แถวซ้ำ*ภายใน*ไฟล์ / response เดียวกันถูกปฏิเสธ ("Duplicate of row N")
- **Lifecycle** `is_active = false` ซ่อนจาก picker; `use_in = []` หมายถึง "ยังไม่ได้กำหนดให้ ledger ใด" และเป็น default ของแถวที่นำเข้าเว้นแต่ไฟล์จะระบุอย่างอื่น
- **Default sort** `code:asc, id:asc` เมื่อไม่ส่ง `?sort=` (`chart-of-accounts.service.ts:173`)
- **Optimistic lock** update ต้องส่ง `doc_version` ปัจจุบัน
- **การเข้าถึง** route map `config:chart-of-accounts → configuration.chart_of_accounts`; แถว permission ถูก seed ไว้ (`seed.permission.data.ts:961-976`); licence feature `configuration.chart_of_accounts` (`seed.license-feature.data.ts:156`); รายการเมนูของ frontend ถูก gate ด้วย licence (`module-list.ts:486-487`) handler นำเข้าทั้งสองใช้ `AppIdGuard('chart-of-accounts.import')` / `('chart-of-accounts.import-from-interface.carmen-gl')`

## 7. การอ้างอิงข้ามโมดูล

- [general-ledger](/en/inventory/general-ledger) — account group (`tb_gl_account_group`), JV prefix, GL period และกติกา JV posting ที่บริโภค `nature`, `use_in` และ `is_require_cost_center`
- [cost-center](/th/inventory/master-data/cost-center) — แถว allow-list `tb_cost_center_account` อ้างอิงตารางนี้
- [product/01-data-model](/th/inventory/product/01-data-model) § 2.11 — `tb_product_account_code_mapping` แบบ free-text ที่ไม่เกี่ยวข้องกัน
- [system-config/application-config](/th/inventory/system-config/application-config) — key `interface_accounting_carmen_gl` ที่ขับเคลื่อนการนำเข้าจาก GL

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_chart_of_accounts` (line ~2934), enums (~2875-2932), `tb_gl_account_group` (~3093)
- **Migrations:** `20260820140000_add_account_code`, `20260827140000_rename_account_code_to_chart_of_accounts`, `20260909170000_gl_core_master`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/chart-of-accounts/chart-of-accounts.service.ts` (create `:234`, update `:285`, delete `:343`, `importFile` `:638`, `importFromInterfaceCarmenGl` `:835`), `chart-of-accounts.import.ts` (การ resolve คอลัมน์, ขีดจำกัด); gateway `apps/backend-gateway/src/config/config_chart-of-accounts/` (`@Controller('api/config/:bu_code/chart-of-accounts')`, handler นำเข้า `:477`, `:583`), DTO `common/dto/chart-of-accounts/chart-of-accounts.dto.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/chart-of-accounts/*.bru` (8 request รวม `POST-import-file-*` และ `POST-import-from-interface-carmen-gl-*`)
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/chart-of-accounts/` (`coa-form-schema.ts`, `coa-filter-fields.ts`, `coa-import-carmen-gl-button.tsx`), `types/chart-of-accounts.ts`, `constant/api-endpoints.ts:60-67`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/082-chart-of-accounts.spec.ts` (16 กรณี; กรณี multi-select filter, export, แก้ nature/type, licence หมดอายุ และนำเข้าจาก Carmen GL ถูกลิสต์ว่า skipped ใน header ของไฟล์), `docs/user-stories/082-chart-of-accounts.md`
