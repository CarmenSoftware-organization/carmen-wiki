---
title: เทมเพลตใบขอซื้อ (Purchase Request Template)
description: scaffold PR ที่ใช้ซ้ำได้ — บันทึก bundle ของรายการที่ซื้อบ่อยเป็น template ให้ Requestor instantiate PR ได้ด้วยคลิกเดียว
published: true
date: 2026-06-09T16:28:56.000Z
tags: templates, purchase-request, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# เทมเพลตใบขอซื้อ (Purchase Request Template)

> **At a Glance**
> **Owner:** Procurement Manager / Product Admin &nbsp;·&nbsp; **Table:** `tb_purchase_request_template` (+ detail, comments) &nbsp;·&nbsp; **Workflow:** ไม่มี (config artefact) &nbsp;·&nbsp; **ใช้โดย:** [purchase-request](/th/inventory/purchase-request) **Create PR from Template** &nbsp;·&nbsp; scaffold bundle รายการที่ใช้ซ้ำได้ ถูก clone ไปยัง PR ใหม่ตามต้องการ

![เทมเพลตใบขอซื้อ (Purchase Request Template) screen](/screenshots/templates/purchase-request.png)

![เทมเพลตใบขอซื้อ (Purchase Request Template) detail screen](/screenshots/templates/purchase-request-detail.png)

## 1. คืออะไรและสำหรับใคร

**เทมเพลตใบขอซื้อ** คือ scaffold ที่ใช้ซ้ำได้ ที่จับ bundle รายการที่ Requestor ต้องป้อนซ้ำในทุก PR ที่เกิดขึ้นเป็นประจำ: สินค้า standard, location default, จำนวน default, currency, snapshot ของ tax / discount และ workflow ที่ PR ในอนาคตจะ route ผ่าน **Create PR from Template** deep-clone header และ detail row ลงใน `tb_purchase_request` ใหม่ที่ `pr_status = draft` ตัว template ไม่ถูกแตะ; PR ใหม่เป็นอิสระและแก้ได้ก่อน submit

**ดูแลโดย** Procurement Manager / Product Admin &nbsp;·&nbsp; **ใช้โดย** Requestor (สิทธิ์อ่านอย่างเดียวต่อ picker) &nbsp;·&nbsp; **ไม่ post อะไร** — config artefact seed-only ไม่มีผลต่อ GL / AP / inventory

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง PR จาก template | PR → **New** → picker **From Template** | Deep-clone header + detail row ที่ `is_active = true` ลงใน PR ใหม่ |
| แก้รายการ template | Templates → Purchase Request → **Edit** | การแก้ไข **ไม่** propagate ไปยัง PR ที่ clone ไปแล้ว |
| ปิดรายการตามฤดูกาล | detail row → toggle `is_active = false` | บรรทัดอยู่ใน template แต่ถูกข้ามตอน clone |
| ปลดประจำการ template | header → toggle `is_active = false` | ลบออกจาก picker; PR เก่ายังอ้าง `created_from_template_id` |
| Hard-delete template ที่ไม่เคยใช้ | header → **Delete** | อนุญาตเฉพาะถ้าไม่เคย instantiate — มิฉะนั้นให้ flip `is_active` |
| เพิ่ม comment | Template → Comments | เก็บใน `tb_purchase_request_template_comment` |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Name must be unique within workflow" | template ที่ไม่ถูก delete อีกตัวมี `(name, workflow_id)` เดียวกัน | เลือกชื่อหรือ workflow อื่น |
| "At least one active detail row required" | ทุกบรรทัดมี `is_active = false` | เปิดอย่างน้อย 1 บรรทัดก่อน publish |
| "Hard-delete blocked — template in use" | PR เคยถูก clone จาก template นี้ | set `is_active = false` แทน |
| "Rate not in history" (ตอน clone) | ไม่มี row `tb_exchange_rate` บน `pr_date` ของ PR ที่ clone | เพิ่ม rate (ดู [master-data/exchange-rate](/th/inventory/master-data/exchange-rate)) แล้วลอง clone อีกครั้ง |
| "Product / location reference inactive" | master record ถูก soft-delete หลัง template ถูกเขียน | แก้บรรทัดให้ swap ไปยัง reference ที่ active |
| PR ที่ clone มี currency ผิด | code ของ currency ถูกคัดลอกตามตัวอักษร; rate เท่านั้นที่ re-resolve | แก้ header ของ PR ที่ clone; currency เปลี่ยนบน template หลัง clone ไม่ได้ |

## 4. Edge Cases

- **Deep-copy clone semantics** Clone insert `tb_purchase_request` ใหม่ (`pr_no` ใหม่, `pr_status = draft`, ผู้ใช้ปัจจุบันเป็นผู้สร้าง) และหนึ่ง `tb_purchase_request_detail` ต่อบรรทัด template ที่ `is_active = true` จำนวน, หน่วย, snapshot ของ tax / discount, dimension ถูกคัดลอก **ตามตัวอักษร** บรรทัด inactive ถูกข้าม
- **ไม่มี workflow บน template เอง** Template ไม่มี `workflow_current_stage`, `user_action`, `doc_status` การแก้ live ทันทีตอน save — ตั้งใจไว้ เพราะ template เป็น configuration ไม่ใช่ transactional
- **Currency / FX resolution ตอน clone** Currency code ถูกคัดลอกตามตัวอักษร; `exchange_rate` และ `exchange_rate_date` **re-resolve** ตอน clone กับ [master-data/exchange-rate](/th/inventory/master-data/exchange-rate) โดยใช้ `pr_date` ของ PR ใหม่ — ป้องกัน FX เก่า
- **Seed-only persistence** row ของ template ไม่เคยถูก FK-reference โดยเอกสาร transactional — PR บันทึก copy ไม่ใช่ reference การแก้ template หลังจาก PR ถูก clone **ไม่** ย้อนเปลี่ยน PR นั้น
- **Hard-delete guard** เมื่อ PR ถูก clone จาก template แล้ว hard-delete ถูกบล็อก; ปลดประจำการแบบ soft เท่านั้น
- **`is_active` ต่อบรรทัด** บรรทัดถูก disable ชั่วคราวได้โดยไม่ลบ — มีประโยชน์สำหรับ SKU ตามฤดูกาล
- **Dimension awareness** JSON `dimension` มีส่วนใน unique key ต่อบรรทัด สินค้าเดียวจึงสามารถปรากฏ 2 ครั้งใน template ภายใต้ค่า dimension ต่างกัน (เช่น cost center ต่างกัน)

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_purchase_request_template`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อ template (unique กับ workflow) |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `workflow_id` | `String? @db.Uuid` | Yes | FK ไป `tb_workflow` workflow ที่ PR ที่ clone จาก template นี้จะใช้ |
| `workflow_name` | `String? @db.VarChar` | Yes | snapshot denormalised ของชื่อ workflow |
| `is_active` | `Boolean? @default(true)` | Yes | flag lifecycle `true` = เลือกได้ใน picker; `false` = ปลดประจำการ |
| `note`, `info`, `dimension` | mixed | Yes | metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, workflow_id, deleted_at])` map `PRT1_name_workflow_id_u` — ชื่อเดียวกันมีได้ภายใต้ workflow ต่างกัน; `@@index([workflow_id])`; `@@index([name])` FK ไป `tb_workflow` `onDelete: NoAction`

ไม่มี enum `status` บน template — lifecycle เป็น boolean `is_active` + `deleted_at` ดู Section 6 ว่า 3 logical state (draft / active / inactive) map อย่างไร

### 5.2 `tb_purchase_request_template_detail`

หนึ่ง row ต่อบรรทัด template

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id`, `purchase_request_template_id` | mixed | No / Yes | PK + parent FK |
| `location_id`, `location_*`, `delivery_point_*` | mixed | Yes | snapshot ปลายทาง default |
| `product_id`, `product_*` | mixed | No / Yes | snapshot สินค้า |
| `inventory_unit_id`, `inventory_unit_name` | mixed | Yes | snapshot หน่วย inventory |
| `description`, `comment` | `String? @db.VarChar` | Yes | Free text |
| `currency_id`, `currency_code`, `exchange_rate`, `exchange_rate_date` | mixed | Yes | snapshot currency — resolve ตอน clone ไม่ใช่ตอนแก้ template |
| `requested_qty`, `requested_unit_*`, `requested_unit_conversion_factor`, `requested_base_qty` | `Decimal(20,5)` / mixed | Yes | จำนวนที่ขอ default (user + หน่วยฐาน) |
| `foc_qty`, `foc_unit_*`, `foc_unit_conversion_factor`, `foc_base_qty` | `Decimal(20,5)` / mixed | Yes | จำนวน free-of-charge default |
| `tax_*`, `is_tax_adjustment` | mixed | Yes | snapshot ภาษี |
| `discount_*`, `is_discount_adjustment` | mixed | Yes | snapshot ส่วนลด |
| `is_active` | `Boolean? @default(true)` | Yes | flag ต่อบรรทัด — บรรทัด inactive ถูกข้ามตอน clone |
| `info`, `dimension`, `doc_version` | mixed | Yes | metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([purchase_request_template_id, product_id, location_id, dimension, deleted_at])` map `PRT1_purchase_request_template_product_location_dimension_u`; `@@index([purchase_request_template_id, product_id, location_id])`; `@@index([purchase_request_template_id])` FK ไป `tb_currency`, `tb_unit` (สองครั้ง — requested_unit และ foc_unit), `tb_location`, `tb_product`, `tb_purchase_request_template`, `tb_tax_profile` — ทั้งหมด `onDelete: NoAction`

block ที่ comment ไว้ (vendor_id, approved_*, foc_*) ใน schema ชี้ว่า template ตั้งใจ **ละ** การจัดสรร vendor และจำนวน approved — ค่าเหล่านี้ resolve ตอนสร้าง PR

### 5.3 `tb_purchase_request_template_comment`

comment บน template เอง ตามรูป comment มาตรฐาน

## 6. Workflow / กฎทางธุรกิจ

Template **ไม่** มีส่วนใน workflow engine 3 logical state มาจาก `is_active` และ `deleted_at`:

- **`draft`** (`is_active = false`, `deleted_at IS NULL`, ยังไม่เคยใช้) — แก้ได้ ไม่อยู่ใน picker อนุญาตให้ประกอบแบบส่วนตัวก่อน publish
- **`active`** (`is_active = true`, `deleted_at IS NULL`) — ปรากฏใน picker; ยังแก้ได้ แต่การแก้ ไม่ propagate ไปยัง PR ที่ clone ไปแล้ว
- **`inactive`** (`is_active = false`, `deleted_at IS NULL`, ใช้แล้วอย่างน้อย 1 ครั้ง) — ถูกถอนจาก picker; ยังอ่านได้บน PR เก่า

`deleted_at` คือ soft-delete sentinel — ใช้เฉพาะตอนไม่เคย instantiate

**Authorization:** Template ดูแลโดย Procurement Manager / Product Admin Requestor ใช้ได้แต่แก้ไม่ได้ (บังคับด้วย role) **Validation ตอน save:** name unique ภายใน `workflow_id`; ต้องมี detail row ที่ `is_active = true` อย่างน้อย 1 รายการเพื่อ enable การปรากฏใน picker

## 7. การอ้างอิงข้าม

- [purchase-request](/th/inventory/purchase-request) — ผู้บริโภคเพียงรายเดียว **Create PR from Template** clone header + detail ลงใน `tb_purchase_request` + `tb_purchase_request_detail` ใหม่ที่ `pr_status = draft`
- [purchase-request/03-user-flow-requestor](/th/inventory/purchase-request/03-user-flow-requestor) — scenario happy-path REQ-HP-06 ใช้ flow นี้
- [system-config/workflow](/th/inventory/system-config/workflow) — `workflow_id` คือ workflow ที่ PR ที่ clone จะเข้าตอน submit
- [product](/th/inventory/product), [master-data/location](/th/inventory/master-data/location), [master-data/currency](/th/inventory/master-data/currency), [master-data/tax-profile](/th/inventory/master-data/tax-profile) — ทุกบรรทัด snapshot จาก master เหล่านี้ตอนแก้ template; clone re-resolve currency/rate แต่คง ref อื่นไว้
- [templates/price-list](/th/inventory/templates/price-list) — template พี่น้องภายใต้ร่ม [templates](/th/inventory/templates)

## 8. การอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_purchase_request_template` (บรรทัด 2402-2430), `tb_purchase_request_template_detail` (บรรทัด 2466-2562), `tb_purchase_request_template_comment` (บรรทัด 2432-2464)
- **Frontend route:** `../carmen-inventory-frontend/app/(root)/procurement/purchase-request-template/`
- **Carmen docs:** `../carmen/docs/purchase-request-management/purchase-request-template-ba.md`; `../carmen/docs/purchase-request-management/PR-User-Experience.md` (flow การสร้างจาก template)
