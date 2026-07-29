---
title: เทมเพลตใบขอซื้อ (Purchase Request Template)
description: scaffold PR ที่ใช้ซ้ำได้ — บันทึก bundle ของรายการที่ซื้อบ่อยเป็น template ให้ Requestor prefill PR ใหม่ได้ด้วยคลิกเดียว
published: true
date: 2026-07-29T04:21:35.000Z
tags: templates, purchase-request, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# เทมเพลตใบขอซื้อ (Purchase Request Template)

> **At a Glance**
> **Owner:** Procurement Manager / Product Admin &nbsp;·&nbsp; **Table:** `tb_purchase_request_template` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** ไม่มี (config artefact) &nbsp;·&nbsp; **ใช้โดย:** [purchase-request](/th/inventory/purchase-request) **Create PR from Template** &nbsp;·&nbsp; scaffold bundle รายการที่ใช้ซ้ำได้ ฟิลด์ของมัน prefill ลง PR draft ใหม่ตามต้องการ

![เทมเพลตใบขอซื้อ (Purchase Request Template) screen](/screenshots/templates/purchase-request.png)

![เทมเพลตใบขอซื้อ (Purchase Request Template) detail screen](/screenshots/templates/purchase-request-detail.png)

> **สถานะการ implement (ตรวจสอบ 2026-07-29):** "Create PR from Template" เป็น **การ prefill ฝั่ง client** ไม่ใช่ backend clone endpoint การเลือก template จะ navigate ไป `/procurement/purchase-request/new?template_id=<id>`; หน้า PR ใหม่ fetch รายการ template ทั้งหมด หา template ที่ตรงกันในเบราว์เซอร์ แล้ว prefill ฟอร์ม PR ใหม่มาตรฐาน (`getDefaultValues(purchaseRequest, template)` ใน `pr-form-schema.ts`) ไม่มีอะไรถูกเขียนจนกว่าผู้ใช้จะ submit PR ตามปกติ และ `tb_purchase_request` ที่ได้ **ไม่มี reference กลับไปยัง template** — ไม่มีคอลัมน์ `created_from_template_id` (หรือเทียบเท่า) อยู่ใน schema เลย การลบ template (`purchase-request-template.service.ts` → `delete()`) เป็น **hard delete** แบบไม่มีเงื่อนไข ไม่มี usage guard และ item grid ตอนสร้าง/แก้ไขมีแค่ location, product, unit, quantity, currency — ไม่มี tax, discount, FOC quantity, หรือ dimension แม้ตารางฐานข้อมูลจะรองรับก็ตาม

## 1. คืออะไรและสำหรับใคร

**เทมเพลตใบขอซื้อ** คือ scaffold ที่ใช้ซ้ำได้ ที่จับ bundle รายการที่ Requestor ต้องป้อนซ้ำในทุก PR ที่เกิดขึ้นเป็นประจำ: สินค้า standard, location default, จำนวน default, currency, และ workflow ที่ PR ในอนาคตจะ route ผ่าน **Create PR from Template** prefill ฟิลด์ของฟอร์ม PR ใหม่จาก header และ detail row ของ template — เป็นการ merge ฝั่ง client ธรรมดา ไม่ใช่ backend operation เฉพาะ ตัว template ไม่ถูกแตะ; PR ใหม่เป็นอิสระ แก้ได้ก่อน submit และ — เมื่อสร้างแล้ว — ไม่มี link ที่ persist กลับไปยัง template ที่มัน prefill มา

**ดูแลโดย** Procurement Manager / Product Admin &nbsp;·&nbsp; **ใช้โดย** Requestor (สิทธิ์อ่านอย่างเดียวต่อ picker) &nbsp;·&nbsp; **ไม่ post อะไร** — config artefact seed-only ไม่มีผลต่อ GL / AP / inventory

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง PR จาก template | PR → **New** → picker **From Template** | Navigate ไป `/procurement/purchase-request/new?template_id=<id>`; ฟอร์ม PR ใหม่ prefill `workflow_id` และแถวรายการจาก template — merge ฝั่ง client ไม่ใช่ server-side clone |
| แก้รายการ template | Templates → Purchase Request → **Edit** | การแก้ไข **ไม่** ย้อนกระทบ PR ที่สร้างจาก template นี้ไปแล้ว (ไม่มี link ระหว่างกันให้ propagate ผ่าน) |
| ปิดรายการตามฤดูกาล | detail row → toggle `is_active = false` (ผ่าน API เท่านั้น) | คอลัมน์ `is_active` ระดับบรรทัดมีอยู่จริงบน `tb_purchase_request_template_detail` แต่ item grid ปัจจุบันไม่มี toggle ให้ — เข้าถึงได้ผ่านเรียก API โดยตรงเท่านั้น |
| ปลดประจำการ template | header → toggle **Active** ปิด | ลบออกจาก picker "From Template" (`GET` list ยังคืนมันถ้าไม่ filter `is_active` แต่ UI picker ซ่อนแถวที่ inactive); ไม่มีผลต่อ PR ที่สร้างไปแล้ว |
| ลบ template | header → **Delete** | hard delete แบบไม่มีเงื่อนไข (`tx.tb_purchase_request_template.delete()`) — ไม่ตรวจว่าเคยถูกใช้มาก่อน ไม่มีการยืนยันผลกระทบนอกเหนือจาก delete dialog |
| เพิ่ม comment | Template → Comments | เก็บใน `tb_purchase_request_template_comment` |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การดำเนินการ |
|---|---|---|
| ชื่อซ้ำถูก reject เงียบ ๆ ด้วย database error ดิบ | `@@unique([name, workflow_id, deleted_at])` บังคับแค่ระดับ DB — ทั้ง `create()` และ `update()` ใน `purchase-request-template.service.ts` ไม่ตรวจชื่อซ้ำก่อน | decorator `@TryCatch` ทั่วไปจับ Prisma constraint violation แล้วคืนข้อความดิบของมัน ไม่ใช่ข้อความ "name already exists" ที่เป็นมิตร — เลือกชื่อหรือ workflow อื่น |
| "Required" บน Workflow / Name / Location / Delivery Point / Product / Unit | Zod schema `createPrtSchema` (frontend) บังคับฟิลด์เหล่านี้ทุกบรรทัดก่อน submit | กรอกฟิลด์ที่ถูก highlight |
| ลบ item เงียบ ๆ แทนที่จะมีการตรวจตอน save | **ไม่มี** กฎจำนวนบรรทัดขั้นต่ำ — `purchase_request_template_detail.add` เป็น optional ใน DTO และ service ไม่ตรวจจำนวน item เลย | template ที่ไม่มีบรรทัดเลย save สำเร็จ — แค่ clone ไม่ได้อะไรลง PR ใหม่ |
| Delete สำเร็จแม้เคยมี PR ถูกสร้างจาก template นี้มาก่อน | ไม่มี usage guard ใน `delete()` | ถ้าเรื่องนี้สำคัญในทางปฏิบัติ ให้ยืนยันกับผู้ขอก่อนลบ template ที่ยังมีคนพึ่งพาอยู่ |

## 4. Edge Cases

- **Prefill ฝั่ง client ไม่ใช่ clone endpoint** `PrSelectTemplate` แค่ navigate ด้วย `?template_id=`; `new-purchase-request-content.tsx` fetch รายการ template ทั้งหมดใหม่แล้วหาที่ตรงกันในเบราว์เซอร์; `getDefaultValues(purchaseRequest, template)` ใน `pr-form-schema.ts` map detail row ของ template ลงใน item array ของ PR ใหม่ PR ใหม่ถูกสร้างผ่าน submit path เดียวกับ PR ที่สร้างจากศูนย์ทุกประการ — ไม่มี backend call พิเศษสำหรับ "instantiate from template"
- **ไม่มี workflow บน template เอง** Template ไม่มี `workflow_current_stage`, `user_action`, `doc_status` การแก้ live ทันทีตอน save — ตั้งใจไว้ เพราะ template เป็น configuration ไม่ใช่ transactional
- **Currency คัดลอกตามตัวอักษร แต่ exchange rate ไม่** `currency_id` ถูกคัดลอกจากบรรทัด template แต่ `getDefaultValues` hardcode `exchange_rate: 1` และตัด `currency_code`/`exchange_rate_date` ทิ้งทั้งหมดสำหรับบรรทัดที่มาจาก template — มัน **ไม่** ถูก re-resolve กับข้อมูล FX ปัจจุบัน ไม่ว่า currency บนบรรทัด template จะเป็นอะไร exchange rate ของ PR ใหม่เริ่มที่ `1` เสมอ จนกว่าการคำนวณใหม่ตามปกติของฟอร์ม PR (อยู่นอกขอบเขตโมดูลนี้) จะแก้มัน
- **ไม่มี link ที่ persist เพราะขาดหาย ไม่ใช่เพราะมี guard ออกแบบไว้** `tb_purchase_request` ไม่มีคอลัมน์ `created_from_template_id` หรือเทียบเท่า — PR ที่มาจาก template แยกไม่ออกจาก PR ที่สร้างจากศูนย์เมื่อสร้างเสร็จแล้ว การแก้ template หลังจาก PR ถูก prefill จากมันไม่มีผลต่อ PR นั้น เพราะไม่มีอะไรเชื่อมพวกมันเข้าด้วยกัน
- **ไม่มี delete guard** Hard delete ไม่มีการตรวจ usage เลย ทั้งในโค้ดและใน copy ของ confirm dialog
- **`is_active` ระดับบรรทัดมีอยู่จริงแต่ UI ไม่แตะ** คอลัมน์นี้มีจริงบน `tb_purchase_request_template_detail` และ default เป็น `true` แต่ไม่มี control ใน `prt-item-fields.tsx`/`prt-item-table.tsx` ที่อ่านหรือเขียนมัน — ทุกบรรทัดที่ save ผ่าน UI เป็น `is_active = true`
- **Tax, discount, FOC quantity, และ dimension เป็น schema/DTO-only** `PurchaseRequestTemplateDetailCreateSchema` รับ `tax_profile_id`, `tax_rate`, `discount_rate`, `foc_qty`, `dimension`, ฯลฯ และ `create()`/`update()` บันทึกทุกอย่างที่ถูกส่งมา — แต่ item grid (`prt-item-table.tsx`) แสดงแค่คอลัมน์ Location, Product, Qty/Unit, Currency, และ Delivery Point ทุกบรรทัดที่สร้างผ่านแอปมี tax เป็นศูนย์, discount เป็นศูนย์, FOC quantity เป็นศูนย์, และ `dimension` ว่างเปล่า; ฟิลด์อื่น ๆ เข้าถึงได้ผ่านเรียก API โดยตรงเท่านั้น

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_purchase_request_template`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อ template (unique กับ workflow) |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `workflow_id` | `String? @db.Uuid` | Yes | FK ไป `tb_workflow` ถูกคัดลอกลง `workflow_id` ของ PR ที่ prefill เมื่อเลือก template |
| `workflow_name` | `String? @db.VarChar` | Yes | snapshot denormalised ของชื่อ workflow |
| `is_active` | `Boolean? @default(true)` | Yes | flag lifecycle `true` = เลือกได้ใน picker; `false` = ปลดประจำการ |
| `note`, `info`, `dimension` | mixed | Yes | metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, workflow_id, deleted_at])` map `PRT1_name_workflow_id_u` — ชื่อเดียวกันมีได้ภายใต้ workflow ต่างกัน; `@@index([workflow_id])`; `@@index([name])` FK ไป `tb_workflow` `onDelete: NoAction` constraint นี้เป็น DB-only: ทั้ง `create()` และ `update()` ไม่ตรวจก่อน ทำให้ชื่อชนกันแสดงเป็น Prisma error ดิบ ไม่ใช่ข้อความระดับแอป

ไม่มี enum `status` บน template — lifecycle เป็น boolean เดียว `is_active` บวก `deleted_at` ไม่มี state "draft": `StatusSwitch` ใน `prt-general-fields.tsx` render `is_active` เป็น toggle สองทางธรรมดา และ template ใหม่ default เป็น `is_active = true` (`EMPTY_FORM` ใน `prt-form-schema.ts`) — filter `STATUS_OPTIONS` ของ picker ก็เป็น binary เช่นกัน (`is_active|bool:true` / `is_active|bool:false`) ไม่มีโค้ดที่ไหนสร้าง state ที่ 3 จาก "เคยถูกใช้แล้ว"

### 5.2 `tb_purchase_request_template_detail`

หนึ่ง row ต่อบรรทัด template

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id`, `purchase_request_template_id` | mixed | No / Yes | PK + parent FK |
| `location_id`, `location_*`, `delivery_point_*` | mixed | Yes | snapshot ปลายทาง default |
| `product_id`, `product_*` | mixed | No / Yes | snapshot สินค้า |
| `inventory_unit_id`, `inventory_unit_name` | mixed | Yes | snapshot หน่วย inventory |
| `description`, `comment` | `String? @db.VarChar` | Yes | Free text |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | `currency_id` เป็นตัวเดียวจากสี่ตัวนี้ที่ item grid (`prt-item-table.tsx`) แสดงจริง; `getDefaultValues` คัดลอก `currency_id` ตามตัวอักษรลง PR ที่ prefill แต่ hardcode `exchange_rate: 1` และตัด `currency_code`/`exchange_rate_date` ทิ้ง — rate **ไม่** ถูก re-resolve |
| `requested_qty`, `requested_unit_*`, `requested_unit_conversion_factor`, `requested_base_qty` | `Decimal(20,5)` / mixed | Yes | จำนวนที่ขอ default (user + หน่วยฐาน) — ฟิลด์จำนวนตัวเดียวที่ UI แสดง |
| `foc_qty`, `foc_unit_*`, `foc_unit_conversion_factor`, `foc_base_qty` | `Decimal(20,5)` / mixed | Yes | จำนวน free-of-charge — DTO create/update รับได้ แต่ไม่ถูก render ที่ไหนใน `prt-item-table.tsx`; เป็น `0`/`null` เสมอบนบรรทัดที่ save ผ่านแอป |
| `tax_*`, `is_tax_adjustment` | mixed | Yes | snapshot ภาษี — เหมือน `foc_*`: schema/DTO-only ไม่มีคอลัมน์ใน grid |
| `discount_*`, `is_discount_adjustment` | mixed | Yes | snapshot ส่วนลด — เหมือน `foc_*`: schema/DTO-only ไม่มีคอลัมน์ใน grid |
| `is_active` | `Boolean? @default(true)` | Yes | flag ต่อบรรทัด default `true` ไม่มี control ใน item grid ที่อ่านหรือเขียนมัน และ branch ของ template ใน `getDefaultValues` map ทุก detail row ลง PR ที่ prefill โดยไม่มีเงื่อนไข — ฟิลด์นี้ไม่ถูกอ่านที่ไหนบน path การ prefill ตอนนี้ |
| `info`, `dimension`, `doc_version` | mixed | Yes | metadata มาตรฐาน `dimension` มีส่วนใน unique constraint ด้านล่างแต่ไม่มี form field — ทุกบรรทัด save ด้วย `dimension = []` |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([purchase_request_template_id, product_id, location_id, dimension, deleted_at])` map `PRT1_purchase_request_template_product_location_dimension_u`; `@@index([purchase_request_template_id, product_id, location_id])`; `@@index([purchase_request_template_id])` FK ไป `tb_currency`, `tb_unit` (สองครั้ง — requested_unit และ foc_unit), `tb_location`, `tb_product`, `tb_purchase_request_template`, `tb_tax_profile` — ทั้งหมด `onDelete: NoAction`

block ที่ comment ไว้ (vendor_id, approved_*, foc_*) ใน schema ชี้ว่า template ตั้งใจ **ละ** การจัดสรร vendor และจำนวน approved — ค่าเหล่านี้ resolve ตอนสร้าง PR

### 5.3 `tb_purchase_request_template_comment`

comment บน template เอง ตามรูป comment มาตรฐาน

## 6. Workflow / กฎทางธุรกิจ

Template **ไม่** มีส่วนใน workflow engine Lifecycle เป็น boolean เดียว:

- **`is_active = true`** (default ตอนสร้าง) — ปรากฏใน picker "From Template"; ยังแก้ได้ และการแก้ไม่มีผลต่อ PR ที่ prefill จากมันไปแล้ว (ไม่มี link ให้ propagate ผ่าน)
- **`is_active = false`** — ซ่อนจาก picker; row ของ template ยังอยู่และ reactivate ได้
- **Deletion แยกจากทั้งสองอย่าง** `delete()` ลบ header และ detail row ของมันจริง ๆ ใน transaction เดียว ไม่ว่า `is_active` หรือเคยถูกใช้มาก่อนหรือไม่

`deleted_at` มีอยู่เป็น audit column มาตรฐานแต่ `delete()` ของ service ทำ `DELETE` จริง ไม่ใช่การเขียน soft-delete ลงมัน — ไม่มี path โค้ดในโมดูลนี้ที่ set `deleted_at` โดยไม่ลบ row ออกจริง ๆ ด้วย

**Authorization:** Template ดูแลโดย Procurement Manager / Product Admin Requestor ใช้ได้แต่แก้ไม่ได้ (บังคับด้วย role ที่ระดับ route ไม่ได้ตรวจในระดับ DTO ในรอบนี้) **Validation ตอน save:** ไม่มีอะไรนอกจากการตรวจ `required` ต่อฟิลด์ใน Zod schema ฝั่ง frontend (`createPrtSchema`) — ไม่มีการตรวจ uniqueness ฝั่ง server ไม่มีกฎจำนวนบรรทัดขั้นต่ำ

## 7. การอ้างอิงข้าม

- [purchase-request](/th/inventory/purchase-request) — ผู้บริโภคเพียงรายเดียว **Create PR from Template** prefill `workflow_id` และแถวรายการของ PR ใหม่จาก template ฝั่ง client ก่อน submit PR ตามปกติ
- [purchase-request/03-user-flow-requestor](/th/inventory/purchase-request/03-user-flow-requestor) — scenario happy-path REQ-HP-06 ใช้ flow นี้
- [system-config/workflow](/th/inventory/system-config/workflow) — `workflow_id` คือ workflow ที่ PR ที่ prefill จะเข้าตอน submit
- [product](/th/inventory/product), [master-data/location](/th/inventory/master-data/location), [master-data/currency](/th/inventory/master-data/currency) — ฟิลด์ที่ item grid resolve จริง; [master-data/tax-profile](/th/inventory/master-data/tax-profile) เชื่อมใน schema แต่เข้าไม่ถึงจาก UI ของโมดูลนี้
- [templates/price-list](/th/inventory/templates/price-list) — template พี่น้องภายใต้ร่ม [templates](/th/inventory/templates); design ต่างกันโดยพื้นฐาน (soft-delete, enum `status` จริง, ไม่มี link-back parity — ดูหน้านั้น)

## 8. การอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_purchase_request_template` (บรรทัด 2635-2664), `tb_purchase_request_template_detail` (บรรทัด 2701-2797), `tb_purchase_request_template_comment` (บรรทัด 2666-2699)
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/procurement/purchase-request-template/purchase-request-template.service.ts` (เข้า Prisma โดยตรง — `create`/`update`/`delete`/`findAll`/`findOne`); DTO ใน `dto/purchase-requesr-template.dto.ts` และ `dto/update-purchase-request-template.dto.ts`
- **Frontend route:** `../carmen-inventory-frontend-react/routes/procurement/purchase-request-template/`; ผู้บริโภคของการ prefill ที่ `../carmen-inventory-frontend-react/routes/procurement/purchase-request/new-purchase-request-content.tsx` และ `pr-form-schema.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/procurement/purchase-request-template/`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts` — สังเกตว่า `describe` block หลายตัวของมัน ("Clone", "Set as Default") assert กับ UI affordance (`cloneButton()`, แนวคิด default-template) ที่ไม่มีอยู่ในโค้ด frontend หรือ schema ปัจจุบัน — test เหล่านั้น soft-skip (`.catch(() => {})`, guard `count() === 0`) หรือบรรยายพฤติกรรมที่หวังไว้ ไม่ใช่ implementation ที่ยืนยันแล้ว
