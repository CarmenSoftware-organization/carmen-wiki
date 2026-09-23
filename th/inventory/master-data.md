---
title: ข้อมูลหลัก (Master Data)
description: ข้อมูลหลักทางธุรกิจที่ถูกอ้างอิงโดยเอกสารธุรกรรมต่าง ๆ — หน่วยนับ แผนก สถานที่ ชั้นวาง ผู้ขาย สกุลเงิน Profile ภาษี ผังบัญชี ศูนย์ต้นทุน และแคตตาล็อกที่เกี่ยวข้อง
published: true
date: '2026-09-23T01:30:00.000Z'
tags: master-data, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ข้อมูลหลัก (Master Data)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** แคตตาล็อกของระเบียนที่มีชื่อ (หน่วยนับ ผู้ขาย สกุลเงิน สถานที่ Profile ภาษี รหัสเหตุผล) ที่เอกสารธุรกรรมอ้างอิงผ่าน FK + denormalised snapshot &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Product Admin, Configurator, Sysadmin &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_unit`, `tb_vendor`, `tb_currency` + `tb_exchange_rate`, `tb_tax_profile`, `tb_location`, `tb_location_shelf`, `tb_chart_of_accounts`, `tb_cost_center` &nbsp;·&nbsp; **หน้าย่อย:** 17

![ข้อมูลหลัก (Master Data) screen](/screenshots/master-data/index.png)

## 1. ภาพรวม

ข้อมูลหลัก (Master Data) คือชุดของระเบียนที่มีชื่อซึ่งเอกสารธุรกรรม *อ้างอิง* แต่ไม่ได้เป็นเจ้าของ หน่วยนับ แผนก สถานที่ ชั้นวาง จุดส่งของ หน่วยธุรกิจ สกุลเงิน ผู้ขาย Profile ภาษี เงื่อนไขการชำระเงิน ประเภทค่าใช้จ่ายเพิ่ม ประเภทการปรับสต๊อก เหตุผลใบลดหนี้ ผังบัญชี และศูนย์ต้นทุน ทั้งหมดอยู่ที่นี่ (เทมเพลต pricelist เป็นเอนทิตีแยกต่างหาก เป็นเจ้าของโดยโมดูล [vendor-pricelist](/th/inventory/vendor-pricelist)'s route `vendor-management/price-list-template` — ไม่ได้อยู่ในโมดูลนี้) แต่ละเอนทิตีเล็กในตัวเอง แต่ทุกตัวถูกอ้างอิงโดยแถวธุรกรรมจำนวนมาก

**หมายเหตุเรื่องขอบเขต (ยืนยันซ้ำ 2026-09-22):** route tree `/config/*` จริงของ frontend (`routes/config/`) ตอนนี้มี 15 หน้าย่อย — `unit`, `department`, `location`, `shelf`, `delivery-point`, `currency`, `exchange-rate`, `tax-profile`, `credit-term`, `extra-cost`, `adjustment-type`, `credit-note-reason`, `business-type`, `chart-of-accounts`, `chart-of-account-mapping` นับจาก baseline 2026-07-29 `certification` ย้ายไปอยู่ที่ `routes/vendor-management/certification` และ `eco` ย้ายไปอยู่ที่ `routes/product-management/eco` (frontend commit `ac1e7c56`, 2026-09-03) จึงไม่ใช่หน้าจอ Configuration อีกต่อไป — ดู [vendor](/th/inventory/master-data/vendor) § 5.5 และ [product/01-data-model](/th/inventory/product/01-data-model) § 2.10 ตามลำดับ มีหน้าจอ/เอนทิตีสามรายการที่ถูกเพิ่มในช่วงเดียวกันและตอนนี้มีหน้าย่อยแล้ว: [shelf](/th/inventory/master-data/shelf), [chart-of-accounts](/th/inventory/master-data/chart-of-accounts) และ [cost-center](/th/inventory/master-data/cost-center) (มีเฉพาะ backend + Bruno — ยังไม่มี route `/config/*`) ส่วน `chart-of-account-mapping` (เปลี่ยนชื่อจาก "Account Mapping" เมื่อ 2026-09-20, frontend `11ec09a3`) เป็น **รายการแบบอ่านอย่างเดียวที่ยังเรนเดอร์ mock ในรีโป `coam-mock.ts`** — ไม่มี gateway endpoint; map `LICENSE_ONLY_RESOURCES` ของ backend (`permission.route-map.ts:429-432`) ระบุไว้อย่างนั้นชัดเจน และ licence key ของมัน `configuration.chart_of_account_mapping` ถูกล็อกไว้ที่ frontend เท่านั้น จึงยังไม่มีหน้าย่อยจนกว่าจะมี endpoint ในทางกลับกัน สองหน้าย่อยของโมดูลนี้ — [vendor](/th/inventory/master-data/vendor) และ [business-unit](/th/inventory/master-data/business-unit) — เอกสาร entity ที่ UI จริงอยู่นอก `/config/*` (`vendor-management/vendor` และแอป admin แยกต่างหาก `carmen-platform` ตามลำดับ); ยังคงเก็บไว้ที่นี่ในฐานะ cross-reference เพราะเอกสาร inventory และ costing engine ต้องพึ่งพามัน ไม่ใช่เพราะหน้าจอของมันอยู่ใต้ Configuration → Master Data

มีหลักการสองข้อที่ขับเคลื่อนการจัดวางของโมดูลร่ม **snapshot semantics**: เอกสารเก็บ FK ไปยังระเบียนหลัก *พร้อมกับ* สำเนาสำหรับแสดงผลแบบ denormalised (name, rate, code) เพื่อให้เอกสารย้อนหลังยังแสดงผลถูกต้องแม้ระเบียนหลักจะถูกเปลี่ยนชื่อหรือยกเลิกการใช้งานในภายหลัง สอง **soft-delete พร้อม active flag**: ทุกเอนทิตีใช้ `is_active` + `deleted_at` เพื่อปลดระวางระเบียนโดยไม่ทำลาย referential integrity ดังนั้นคำตอบมาตรฐานต่อ "ลบ X" คือ "ยกเลิกการใช้งาน X"

โมดูลร่มนี้ครอบคลุม Prisma schema ทั้งสอง เอนทิตีส่วนใหญ่อยู่ใน schema แบบ **tenant** (ฐานข้อมูลต่อ property) แต่ `business-unit` และ `currency-iso` อยู่ที่ระดับ **platform** (ใช้ร่วมกันข้าม tenant) ส่วน `currency` เป็นแบบผสม — การอ้างอิง ISO อยู่ที่ platform ส่วนรายการสกุลเงินที่เปิดใช้งานและอัตรามีวันที่อยู่ที่ tenant

## 2. กลุ่มผู้ใช้

Product Admin และ Configurator เป็นผู้บริหารจัดการข้อมูลเหล่านี้ Sysadmin กำกับดูแลด้านการเชื่อมต่อและ RBAC และเป็นเจ้าของแต่เพียงผู้เดียวในการตั้งค่า `business-unit` และ `currency-iso` ที่ระดับ platform

## 3. รายการเอนทิตี

| Entity | วัตถุประสงค์ | ผู้บริหารจัดการ |
| ------ | ------------ | ---------------- |
| [unit](/th/inventory/master-data/unit) | หน่วยนับและการแปลงหน่วยต่อสินค้า | Product Admin |
| [department](/th/inventory/master-data/department) | แผนกขององค์กรและการ map ผู้ใช้กับแผนก | Product Admin / Sysadmin |
| [location](/th/inventory/master-data/location) | สถานที่ inventory, direct และ consignment พร้อมพฤติกรรมการนับ | Product Admin |
| [delivery-point](/th/inventory/master-data/delivery-point) | จุดส่งสินค้าทางกายภาพสำหรับการจัดส่งของผู้ขาย | Product Admin |
| [business-unit](/th/inventory/master-data/business-unit) | หน่วยปฏิบัติการ — เป็นเจ้าของ calculation method และ default currency | Sysadmin |
| [currency](/th/inventory/master-data/currency) | สกุลเงินที่เปิดใช้งาน, ISO reference และประวัติอัตราแลกเปลี่ยนแบบมีวันที่ | Product Admin / Sysadmin |
| [exchange-rate](/th/inventory/master-data/exchange-rate) | ประวัติอัตรา FX แบบมีวันที่ที่ใช้สำหรับ snapshot บนเอกสารและ FX revaluation ของ costing | Product Admin |
| [vendor](/th/inventory/master-data/vendor) | ผู้ขายพร้อมที่อยู่ ผู้ติดต่อ และ taxonomy ของประเภทธุรกิจ | Product Admin |
| [vendor-business-type](/th/inventory/master-data/vendor-business-type) | จัดประเภทผู้ขายตามลักษณะธุรกิจ (ผู้ผลิต, ผู้จัดจำหน่าย, บริการ ฯลฯ) | Product Admin |
| [tax-profile](/th/inventory/master-data/tax-profile) | นิยามอัตราภาษีแบบมีชื่อ | Product Admin |
| [credit-term](/th/inventory/master-data/credit-term) | เงื่อนไขการชำระเงินกับผู้ขาย (NET 30, COD, ฯลฯ) | Product Admin |
| [extra-cost-type](/th/inventory/master-data/extra-cost-type) | หมวด landed cost ของ GRN พร้อมโหมดการจัดสรร | Product Admin |
| [adjustment-type](/th/inventory/master-data/adjustment-type) | รหัสเหตุผลสำหรับการปรับสต๊อก stock-in / stock-out | Product Admin |
| [credit-note-reason](/th/inventory/master-data/credit-note-reason) | รหัสเหตุผลสำหรับใบลดหนี้ที่ออกต่อ GRN | Product Admin |
| [shelf](/th/inventory/master-data/shelf) | ชั้นวางระดับ BU (ลำดับการเดินนับ) กำหนดต่อ product-location | Product Admin |
| [chart-of-accounts](/th/inventory/master-data/chart-of-accounts) | รหัสบัญชี GL (nature / type / category, นำเข้าจากไฟล์ + Carmen GL) | Sysadmin / Finance |
| [cost-center](/th/inventory/master-data/cost-center) | กลุ่มศูนย์ต้นทุน ศูนย์ต้นทุน และ allow-list บัญชีต่อศูนย์ — API เท่านั้น | Sysadmin / Finance |

### 3.1 เพิ่มเข้ามานับจาก baseline 2026-07-29

| Entity | Table (tenant) | Migration | HTTP (gateway) | Bruno | Frontend |
| ------ | -------------- | --------- | -------------- | ----- | -------- |
| Shelf | `tb_location_shelf` | `20260814150000_add_location_shelf` → `20260820120000_rename_location_shelf_to_shelf` (ตัด `location_id` ออก) → `20260904131500_rename_shelf_and_user_location` (กลับมาเป็น `tb_location_shelf`) | `api/config/:bu_code/shelves` | `config/location-shelves/*` (6) | `routes/config/shelf/` |
| Chart of accounts | `tb_chart_of_accounts` + `enum_chart_of_accounts_{nature,type,category,use_in}` | `20260820140000_add_account_code` → `20260827140000_rename_account_code_to_chart_of_accounts` → `20260909170000_gl_core_master` (เพิ่ม `category`, `is_require_cost_center`, `account_group_id`) | `api/config/:bu_code/chart-of-accounts` (+ `/import`, `/import-from-interface/carmen-gl`) | `config/chart-of-accounts/*` (8) | `routes/config/chart-of-accounts/` |
| Cost center | `tb_cost_center_group`, `tb_cost_center`, `tb_cost_center_account` | `20260904103000_add_cost_center` | `api/config/:bu_code/cost-center-groups`, `api/config/:bu_code/cost-centers` (+ `PUT :id/accounts`) | `config/cost-center-groups/*` (6), `config/cost-centers/*` (7) | ไม่มี |

### 3.2 การเปลี่ยนชื่อตารางนับจาก baseline

ตาราง junction/master สามตารางถูกเปลี่ยนชื่อเมื่อ 2026-09-04 โดยไม่มีการเปลี่ยนคอลัมน์; ให้อัปเดต query หรือ seed ใด ๆ ที่ยังใช้ชื่อเดิม:

| Old | New | Migration |
| --- | --- | --------- |
| `tb_user_location` | `tb_location_user` | `20260904131500_rename_shelf_and_user_location` |
| `tb_product_master_eco_label` | `tb_eco_label` | `20260904133000_rename_eco_label_and_certificate` |
| `tb_vendor_master_certificate` | `tb_certificate` | `20260904133000_rename_eco_label_and_certificate` |

### 3.3 การเรียงลำดับเริ่มต้นบน config list endpoint (2026-09-13)

`findAll` ของข้อมูลหลักทุกตัวตอนนี้ส่ง `?sort=` ผ่าน `withDefaultSort()` (`apps/micro-business/src/common/libs/default-sort.ts`): เมื่อผู้เรียกไม่ส่ง sort directive ที่ไม่ว่าง ระบบจะใช้ fallback ต่อเอนทิตีเพื่อให้การแบ่งหน้าเสถียร (`id:asc` เป็น tiebreaker สุดท้ายเสมอ) fallback ที่เกี่ยวข้องกับโมดูลนี้:

| Fallback | Entities |
| -------- | -------- |
| `code:asc, name:asc` | location, department, currency, adjustment-type |
| `code:asc` | vendor, chart-of-accounts, cost-center, cost-center-group, product, product-category / sub-category / item-group |
| `name:asc` | unit, delivery-point, credit-term, extra-cost-type, vendor-business-type, credit-note-reason, eco-label (`product-master-eco-label`), certificate (`vendor-master-certificate`) |
| `name:asc, tax_rate:asc` | tax-profile |
| `sequence_no:asc, code:asc` | shelf |
| `created_at:desc` | exchange-rate และรายการ `*-comment` ทุกตัว |

### 3.4 การอ้างอิงเอนทิตีเป็น nested object (2026-09-17)

response แบบ list และ detail บน config controller ไม่ส่งคู่ `<entity>_id` / `<entity>_name` แบบแบนสำหรับ foreign key ของมันอีกต่อไป; แต่ส่ง nested object `{ id, name, ... }` แทน (`@ExpandRefs` / `@Serialize` บน gateway — เช่น แถว exchange-rate มี `currency: { id, code, name }`, detail ของ department มี `department_users[].user`, detail ของ location มี `delivery_point`) type ของ frontend ใต้ `types/*.ts` ถูกปรับให้ตรงกันในช่วงเดียวกัน (`75244fde`, `b55294b3`, `f8d4026c`) คอลัมน์ snapshot เช่น `tb_location.delivery_point_name` ยังมีอยู่ใน schema แต่ไม่ใช่สิ่งที่ UI อ่านอีกต่อไป

## 4. การพึ่งพาข้ามโมดูล

- [purchase-request](/th/inventory/purchase-request) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/department](/th/inventory/master-data/department), [master-data/location](/th/inventory/master-data/location), [master-data/vendor](/th/inventory/master-data/vendor), [master-data/tax-profile](/th/inventory/master-data/tax-profile), [master-data/currency](/th/inventory/master-data/currency), [master-data/exchange-rate](/th/inventory/master-data/exchange-rate)
- [purchase-order](/th/inventory/purchase-order) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/vendor](/th/inventory/master-data/vendor), [master-data/currency](/th/inventory/master-data/currency), [master-data/exchange-rate](/th/inventory/master-data/exchange-rate), [master-data/tax-profile](/th/inventory/master-data/tax-profile), [master-data/credit-term](/th/inventory/master-data/credit-term), [master-data/delivery-point](/th/inventory/master-data/delivery-point)
- [good-receive-note](/th/inventory/good-receive-note) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/vendor](/th/inventory/master-data/vendor), [master-data/currency](/th/inventory/master-data/currency), [master-data/exchange-rate](/th/inventory/master-data/exchange-rate), [master-data/tax-profile](/th/inventory/master-data/tax-profile), [master-data/extra-cost-type](/th/inventory/master-data/extra-cost-type), [master-data/credit-note-reason](/th/inventory/master-data/credit-note-reason), [master-data/delivery-point](/th/inventory/master-data/delivery-point), [master-data/location](/th/inventory/master-data/location)
- [store-requisition](/th/inventory/store-requisition) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/location](/th/inventory/master-data/location), [master-data/department](/th/inventory/master-data/department)
- [inventory](/th/inventory/inventory) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/location](/th/inventory/master-data/location), [master-data/business-unit](/th/inventory/master-data/business-unit)
- [inventory-adjustment](/th/inventory/inventory-adjustment) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/location](/th/inventory/master-data/location), [master-data/adjustment-type](/th/inventory/master-data/adjustment-type), [master-data/credit-note-reason](/th/inventory/master-data/credit-note-reason)
- [physical-count](/th/inventory/physical-count) ต้องใช้ [master-data/location](/th/inventory/master-data/location), [master-data/unit](/th/inventory/master-data/unit) **ไม่ใช้** [master-data/adjustment-type](/th/inventory/master-data/adjustment-type) — variance rollup ของมันสร้างแถว stock-in/out โดยปล่อย `adjustment_type_id` เป็น `null` (ยืนยันในรอบนี้ ดู Cross-References ของหน้า adjustment-type)
- [spot-check](/th/inventory/spot-check) ต้องใช้ [master-data/location](/th/inventory/master-data/location) เท่านั้น **ไม่ใช้** [master-data/adjustment-type](/th/inventory/master-data/adjustment-type) — มันไม่เคยสร้างแถว stock-in/out เลย (ยืนยันในรอบนี้)
- [costing](/th/inventory/costing) ต้องใช้ [master-data/business-unit](/th/inventory/master-data/business-unit) (สำหรับ `calculation_method`), [master-data/currency](/th/inventory/master-data/currency) และ [master-data/exchange-rate](/th/inventory/master-data/exchange-rate) (สำหรับ FX revaluation แบบมีวันที่)
- [vendor-pricelist](/th/inventory/vendor-pricelist) ต้องใช้ [master-data/vendor](/th/inventory/master-data/vendor), [master-data/currency](/th/inventory/master-data/currency), [master-data/tax-profile](/th/inventory/master-data/tax-profile), [templates/price-list](/th/inventory/templates/price-list)
- [product](/th/inventory/product) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit), [master-data/tax-profile](/th/inventory/master-data/tax-profile)
- [recipe](/th/inventory/recipe) ต้องใช้ [master-data/unit](/th/inventory/master-data/unit)
- [physical-count](/th/inventory/physical-count) และ [spot-check](/th/inventory/spot-check) สามารถอ่านลำดับการเดินนับจาก [master-data/shelf](/th/inventory/master-data/shelf) ผ่านคอลัมน์ `shelf_*` บน `tb_product_location`; ยังไม่พบโค้ดการนับใดที่เรียงลำดับตามมัน (ดูหน้า shelf)

### 4.1 ข้อมูลหลัก General Ledger (ชี้ทางเท่านั้น)

migration `gl_core_master` เมื่อ 2026-09-09 เพิ่มตารางข้อมูลหลัก GL ที่อยู่ใต้ prefix `api/config/:bu_code/*` เดียวกัน — `gl-account-groups` (`tb_gl_account_group`), `gl-jv-prefixes` (`tb_gl_jv_prefix`) และ `gl-periods` (`tb_gl_period` ซึ่งตั้งใจแยกจาก `tb_inventory_period`) ตารางเหล่านี้มีเอกสารอยู่ในส่วน [general-ledger](/th/inventory/general-ledger) ของ book ไม่ใช่ที่นี่; โมดูลนี้เป็นเจ้าของเฉพาะสองเอนทิตีที่ข้อมูลหลัก GL ต้องพึ่งพา — [chart-of-accounts](/th/inventory/master-data/chart-of-accounts) (`account_group_id` → `tb_gl_account_group`) และ [cost-center](/th/inventory/master-data/cost-center) (allow-list ที่บรรทัด JV ถูกตรวจสอบเทียบกับ)

## 5. แหล่งอ้างอิง

- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
- **Migrations (tenant, นับจาก 2026-07-29):** `20260814150000_add_location_shelf`, `20260820120000_rename_location_shelf_to_shelf`, `20260820140000_add_account_code`, `20260827140000_rename_account_code_to_chart_of_accounts`, `20260904103000_add_cost_center`, `20260904131500_rename_shelf_and_user_location`, `20260904133000_rename_eco_label_and_certificate`, `20260909170000_gl_core_master`, `20260909203000_add_vendor_tax_branch_rating`, `20260915120000_po_header_delivery_point`
- **Default sort:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/libs/default-sort.ts`; fallback ต่อเอนทิตีอยู่ใน `findAll` ของแต่ละ `master/<entity>/<entity>.service.ts`
- **Licence-only resources:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/permission.route-map.ts` (`LICENSE_ONLY_RESOURCES`, `configuration.chart_of_account_mapping`)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/{010-department,020-unit,029-business-type,030-extra-cost,031-adjustment-type,032-credit-term,040-currency,041-exchange-rate,042-tax-profile,079-delivery-point,080-location,082-chart-of-accounts,083-shelf}.spec.ts` พร้อม gap report ใต้ `docs/test-cases/gaps/` และ user story ที่ generate ไว้ใต้ `docs/user-stories/`
- **carmen/docs:** `../carmen/docs/settings/locations.md` (อ้างอิงโดย [master-data/location](/th/inventory/master-data/location) เท่านั้น)
- **Design spec:** `.specs/2026-05-16-master-config-design.md`
- **Plan:** `.specs/2026-05-16-master-config-plan.md`
