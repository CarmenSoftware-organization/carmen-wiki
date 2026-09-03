---
title: เทมเพลตรายการราคา (Price List Template)
description: scaffold RFQ / pricelist ที่ใช้ซ้ำได้ นิยาม currency, validity, คำแนะนำ vendor, และรายการสินค้า/MOQ — template ต้นทางที่รอบ Request for Pricing ถูกออกจากมัน
published: true
date: 2026-07-29T04:41:24.000Z
tags: templates, price-list, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# เทมเพลตรายการราคา (Price List Template)

> **At a Glance**
> **Owner:** Product Admin / Procurement Lead &nbsp;·&nbsp; **Table:** `tb_pricelist_template` (+ detail, comments) &nbsp;·&nbsp; **ใช้โดย:** [vendor-pricelist](/th/inventory/vendor-pricelist) — รอบ Request for Pricing เก็บ FK `pricelist_template_id` แบบ live &nbsp;·&nbsp; รูปร่างของรอบ pricelist — currency, validity, คำแนะนำ vendor, และรายการสินค้า/MOQ

![เทมเพลตรายการราคา (Price List Template) screen](/screenshots/templates/price-list.png)

![เทมเพลตรายการราคา (Price List Template) detail screen](/screenshots/templates/price-list-detail.png)

> **สถานะการ implement (ตรวจสอบ 2026-07-29):** ฟอร์มสร้าง/แก้ (`plt-form.tsx`) มีแค่ 6 อย่าง — Name, Currency, Validity period, Description, Status, Vendor instructions — บวกส่วน **Products** (MOQ tier ต่อสินค้า) ที่หน้านี้เวอร์ชันก่อนไม่เคยพูดถึงเลย `reminder_days`, `send_reminders`, และ `escalation_after_days` เป็นคอลัมน์จริงบน `tb_pricelist_template` และ `update()` ฝั่ง backend ยินดีบันทึกให้ถ้า post มาตรงกับ API แต่ **ไม่มี UI field ตั้งค่าพวกมัน ไม่มี server-side validation ตรวจสอบ และไม่มี background job (`micro-cronjobs`, ค้นทั้ง repo) อ่านค่ามัน** — มันไม่มีผลจริง Clone ถูกถอดออกอย่างชัดเจน: `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` มี suite เฉพาะชื่อ "Pricelist Template — Clone (removed)" ที่ assert ว่าไม่มี clone affordance ใน list, detail, หรือ edit view สำหรับทุก role Delete (`price-list-template.service.ts` → `remove()`) เป็น **soft delete** แบบไม่มีเงื่อนไข (`status = inactive` + `deleted_at`) ไม่มี usage guard — ไม่มี hard-delete path แยกที่จะถูกบล็อกเลย

## 1. คืออะไรและสำหรับใคร

template pricelist คือ **รูปร่างของรอบ pricelist**: ใบเสนอราคาอยู่ในสกุลเงินใด, pricelist ที่ได้อยู่ valid กี่วัน, คำแนะนำที่ render ให้ vendor, และรายการสินค้า (แต่ละตัวมี MOQ tier อย่างน้อยหนึ่งชุด — unit + จำนวน + note) ที่ vendor คนไหนก็ตามที่ได้รับ template นี้จะถูกขอให้เสนอราคา ผู้ซื้อเลือก template ตอนเริ่มรอบ Request for Pricing (RFQ); `tb_request_for_pricing.pricelist_template_id` เป็น FK จริงที่ persist — ต่างจาก PR template (ดู [templates/purchase-request](/th/inventory/templates/purchase-request)) pricelist template ยังผูกอยู่กับทุกรอบ RFQ ที่ออกจากมัน ไม่ใช่แค่คัดลอกแล้วลืม

Template เร่งวงจรการจัดซื้อที่เกิดซ้ำ — แทนที่จะป้อนรายการสินค้า/MOQ และคำแนะนำ vendor ใหม่ทุกครั้ง ผู้ซื้อใช้ template เช่น "Fresh Produce Template" ซ้ำ พร้อม currency, validity, และรายการสินค้าที่ตั้งไว้แล้ว

**ดูแลโดย** Product Admin หรือ Procurement Lead **อ่านโดย** flow การสร้าง RFQ (`tb_request_for_pricing.pricelist_template_id`)

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง template | Vendor Management → Price List Templates → **Add Template** | Name, currency, และ validity period เป็นฟิลด์ header ที่บังคับเพียงกลุ่มเดียว |
| เพิ่มสินค้า | edit template → tree สินค้า → ติ๊กสินค้า | เพิ่มแถว MOQ ว่าง (unit + qty); ใช้ **Add tier** เพื่อเพิ่ม MOQ break ที่สองบนสินค้าเดิม |
| ลบสินค้า / tier | แถวสินค้า → **Remove tier** หรือเอาติ๊กออกใน tree → confirm | ลบ tier สุดท้ายของสินค้าจะลบสินค้านั้นไปด้วย; ลบสินค้าตัวสุดท้ายจะกลับไปที่ empty state "No products yet" |
| Activate / deactivate | edit template → Status select (`draft`/`active`/`inactive`) → **Save** | ไม่มี quick-toggle แยก — การเปลี่ยน status ต้องผ่าน edit-and-save เต็มรูปแบบเหมือนฟิลด์อื่น ๆ backend มี `PATCH :id/status` แบบ bare อยู่ด้วย แต่ไม่มีที่ไหนใน frontend เรียกมัน |
| เปลี่ยนคำแนะนำสำหรับ vendor | edit template → textarea **Instructions to vendor** | render ให้ vendor เมื่อ template นี้ถูกออกเป็น RFQ |
| ลบ template | template detail (edit mode) → **Delete** | สำเร็จเสมอ soft-delete เสมอ (ดูสถานะด้านล่าง) — ไม่ว่าจะมีรอบ RFQ ใดอ้างถึงมันอยู่หรือไม่ |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Price list template name already exists" (409) | ซ้ำแบบไม่สนตัวพิมพ์เล็กใหญ่ในกลุ่ม template ที่ไม่ถูก delete | เลือกชื่ออื่น — เช็คนี้เป็นของจริง รันทั้งบน `create()` และ `update()` |
| แถวสินค้าถูก reject ตอน save | `product_id` และ `unit_id` บังคับทั้งคู่ต่อ detail row (`plt-form-schema.ts`) | เลือกสินค้าและ unit หรือลบแถวว่างออกก่อน save |
| Validity period ลงต่ำกว่า 1 ไม่ได้ | `<input type="number" min={1}>` ของ stepper เป็น native HTML constraint ไม่ใช่ข้อความ business-rule แบบ custom | ไม่มี minimum ฝั่ง server เลยไม่ว่าทางไหน — การบล็อกเป็นฝั่ง client ล้วน ๆ |
| "Currency not found" | `currency_id` resolve ไม่เจอ row ที่มีอยู่ | เลือก currency ที่ถูกต้อง — เช็คนี้ตรวจแค่ว่ามีอยู่ **ไม่** ตรวจว่า currency active หรือไม่ |

Claim ที่ **ไม่มี** โค้ดรองรับในรอบนี้ แต่เคยถูกเอกสารไว้ราวกับบังคับใช้จริง: array `reminder_days` ที่ถูก reject, เช็ค "inactive currency", กฎ `escalation_after_days` ไม่ติดลบ, และ delete block สำหรับ template ที่มีรอบ RFQ ออกแล้ว ไม่มีสิ่งเหล่านี้อยู่ใน `createPriceListTemplateCreateValidation`/`createPriceListTemplateUpdateValidation` (`price-list-template.dto.ts`) หรือใน `price-list-template.service.ts`

## 4. Edge Cases

- **สินค้าคือ payload จริงของ template และไม่เคยถูกเอกสารไว้มาก่อน** แต่ละ row ของ `tb_pricelist_template_detail` คือหนึ่งสินค้า; `order_unit_obj` (JSONB) เก็บ array ของ MOQ tier (`{unit_id, unit_name, qty, note}`) ฟอร์มแบน tier ออกเป็น list ที่ขับเคลื่อนด้วย checkbox tree — ติ๊กสินค้าเพิ่มแถว tier ว่างหนึ่งแถว **Add tier** เพิ่มอีกแถวสำหรับสินค้าเดิมพร้อม default qty ที่เพิ่มอัตโนมัติ และการลบสินค้าจะลบทุกแถว tier ของมันในการ confirm เดียว
- **การเปลี่ยน currency บน template ที่มีอยู่** มีผลแค่ไปข้างหน้าเท่านั้น — `tb_request_for_pricing` ไม่ denormalize อะไรจาก template นอกจาก FK ดังนั้นหน้านี้ยืนยันจาก frontend อย่างเดียวไม่ได้ว่า RFQ ที่กำลังดำเนินอยู่จะอ่าน currency ปัจจุบันของ template ใหม่หรือไม่ — ถือว่ายังไม่ยืนยัน
- **`reminder_days` / `send_reminders` / `escalation_after_days` เป็นของที่ตายแล้วผ่าน UI** พวกมันเป็นคอลัมน์จริง `create()`/`update()` รับไว้ถ้า post มาตรง (ยืนยันจากการอ่าน `price-list-template.service.ts`) แต่ฟอร์มสร้าง/แก้ไม่มีฟิลด์ให้เลยสักตัว และไม่มี background job อ่านมัน — คำอธิบาย step ของ test ตัวหนึ่งใน `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` (`TC-PT-030001`) ยังบรรยายว่า "toggle switch send-reminders… เลือก checkbox เตือน 14 และ 7 วัน… กรอก escalation days" แต่ตัว test body ที่มันแนบอยู่กรอกแค่ฟิลด์ Name แล้ว save เท่านั้น — annotation นั้นเก่า/ตกยุคเทียบกับโค้ดที่มันควรจะบรรยาย
- **Clone ยืนยันแล้วว่าถูกถอดออก ไม่ใช่แค่ไม่มีเอกสาร** suite "Pricelist Template — Clone (removed)" ใน `160-pl-template.spec.ts` assert ตรง ๆ ว่า `cloneButton()`/`cloneMenuItem()` มี 0 match ใน list, detail view, และ edit mode สำหรับทุก role ที่ทดสอบ
- **Delete เป็น soft ไม่มีเงื่อนไข และเกิดทันที — แต่ soft-delete ของ detail row ไม่ครบ** `remove()` set `status = inactive`, `deleted_at`, และ `deleted_by_id` บน row **header** แต่ `updateMany` ของ detail row (`price-list-template.service.ts:741-746`) set **แค่ `deleted_by_id`** เท่านั้น — `deleted_at` ไม่เคยถูกเขียนบน `tb_pricelist_template_detail` เลย query ที่ filter detail row ด้วย `deleted_at IS NULL` จะตรวจไม่พบว่ารายการของ template ที่ถูกลบแล้วถูกลบ — มีแค่ `deleted_at`/`status` ของ header เท่านั้นที่บอกสถานะ deletion ได้แน่นอน ไม่มี hard-delete action แยกที่ไหนเลย และไม่มีการเช็คว่ารอบ RFQ (`tb_request_for_pricing.pricelist_template_id`) ยังชี้มาที่ template นี้อยู่หรือไม่
- **Status เป็น enum 3 ค่าจริง** (`draft`/`active`/`inactive`, DB default `draft`) แก้ผ่าน `<Select>` ธรรมดาในฟอร์มเดียวกับฟิลด์อื่นทุกตัว — ไม่มี workflow แยก ไม่มี gate ที่ผูกกับความครบถ้วนของรายการสินค้า

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_pricelist_template`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อ template |
| `status` | `enum_pricelist_template_status` | No | `draft` (default), `active`, `inactive` |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `note` | `String? @db.VarChar` | Yes | บันทึกภายใน |
| `vendor_instructions` | `String? @db.Text` | Yes | render ให้ vendor เมื่อส่ง RFQ |
| `currency_id` | `String? @db.Uuid` | Yes | FK ไป `tb_currency` |
| `currency_code` | `String? @db.VarChar` | Yes | copy แสดง denormalised |
| `validity_period` | `Int?` | Yes | จำนวนวันที่ pricelist ที่ได้ valid หลังการออก |
| `send_reminders` | `Boolean?` | Yes | master switch (default `true`) |
| `reminder_days` | `Json? @db.JsonB` | Yes | array ของวันก่อน deadline (เช่น `[14, 7, 3, 1]`) |
| `escalation_after_days` | `Int? @db.Integer` | Yes | วันหลัง deadline ที่จะ escalate (default `0`) |
| `info`, `dimension`, `doc_version` | — | Mixed | metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** Primary key บน `id` `@@unique([name, deleted_at], map: "pricelist_template_name_deletedat_u")` — เป็น constraint ระดับ DB จริง ไม่ใช่แค่ระดับแอป FK บน `currency_id` `onDelete: NoAction` reverse relation ไป `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, และ `tb_request_for_pricing`

**`enum_pricelist_template_status`:** `draft` (default), `active`, `inactive`

### 5.2 `tb_pricelist_template_detail`

หนึ่ง row ต่อสินค้าบน template; MOQ tier ของสินค้านั้นถูกอัดลงคอลัมน์ JSONB เดียว ไม่ใช่หนึ่ง row ต่อ tier

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id`, `pricelist_template_id` | mixed | No | PK + parent FK |
| `sequence_no` | `Int? @default(1)` | Yes | ลำดับการแสดง |
| `product_id`, `product_code`, `product_name`, `product_local_name`, `product_sku` | mixed | No / Yes | snapshot สินค้า เติมค่าฝั่ง server จาก `tb_product` ตอน save |
| `inventory_unit_id`, `inventory_unit_name` | mixed | Yes | หน่วย inventory ของสินค้า เติมค่าฝั่ง server |
| `order_unit_obj` | `Json? @db.JsonB` | Yes | array ของ MOQ tier — `[{unit_id, unit_name, qty, note}, …]` ปุ่ม "Add tier" ของฟอร์มเพิ่ม entry ลงตรงนี้; ไม่มีตาราง tier แยก |
| `comment` | `String? @db.VarChar` | Yes | Free text |
| `info`, `dimension`, `doc_version` | mixed | Yes | metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([pricelist_template_id, product_id, deleted_at])` — หนึ่ง detail row ต่อสินค้าต่อ template (MOQ tier ทั้งหมดของสินค้าอยู่ใน `order_unit_obj` ของ row เดียวนั้น ไม่ใช่แยกเป็น row)

### 5.3 `tb_pricelist_template_comment`

comment บน template เอง ตามรูป comment มาตรฐาน ไม่ได้ตรวจสอบ frontend surface ของสิ่งนี้ในรอบนี้

## 6. กฎทางธุรกิจ

- **Uniqueness** `name` unique ในกลุ่มที่ไม่ถูก delete — บังคับใช้ **ทั้งสองระดับ**: ระดับ DB (`@@unique([name, deleted_at])`) และตรวจซ้ำในโค้ดแอป (`create()` ทำ `findFirst` ก่อน insert อย่างชัดเจน; `superRefine` ของ Zod ใน `update()` ทำ `findFirst` อีกครั้ง)
- **ไม่มี deletion guard เลย** `remove()` สำเร็จเสมอและ soft-delete เสมอ — `status = inactive` + `deleted_at` บน **header** เท่านั้น; ทุก detail row ได้แค่ `deleted_by_id` **ไม่ได้** `deleted_at` (ดู note ใน Edge Cases ด้านบน) — ไม่มี hard-delete path ที่จะถูกบล็อก และไม่มีการเช็ครอบ RFQ ที่ยังอ้างถึง template
- **Validation ที่บังคับใช้จริง:** name uniqueness (ข้างต้น); `currency_id` ต้องอ้าง currency ที่ *มีอยู่จริง* (แค่ตรวจมีอยู่ ไม่ตรวจ `is_active`); `product_id` ของแต่ละ detail สินค้าต้องมีอยู่จริง และ `unit_id` ของแต่ละ MOQ tier ต้องมีอยู่จริง **ไม่บังคับใช้ที่ไหนในโค้ด:** ความไม่ติดลบของ `validity_period` (มีแค่ native `min=1` ฝั่ง client บน input ของ stepper), ความไม่ติดลบของ `escalation_after_days`, ลำดับ sort หรือความเป็นค่าบวกของ `reminder_days`
- **Status ไม่ใช่ workflow** `draft`/`active`/`inactive` แก้ผ่าน `<Select>` เดียวกับฟิลด์ header อื่นทุกตัวใน flow edit-and-save มาตรฐาน backend ยังมี `updateStatus()` (`PATCH :id/status` แบบ bare write ไม่มีเงื่อนไข ไม่มี validation) แต่ไม่มีโค้ด frontend เรียกมัน
- **Reminder/escalation ไม่มีใครอ่าน** `send_reminders`, `reminder_days`, `escalation_after_days` ถูกรับและบันทึกโดย `create()`/`update()` ถ้ามีอยู่ใน request body แต่ไม่มีอะไรใน repo นี้หรือใน `micro-cronjobs` (ค้นทั้ง repo แบบไม่สนตัวพิมพ์เล็กใหญ่หา "reminder"/"escalat" ไม่เจอเลยที่นั่น) อ่านมันกลับออกมา
- **การเปลี่ยน currency** ไม่มีอะไรที่สังเกตได้จากฝั่ง frontend/backend ในรอบนี้ที่อ่าน currency ของ template หลังรอบ RFQ ถูกออกแล้ว — RFQ ที่กำลังดำเนินอยู่จะเห็นการเปลี่ยน currency ทีหลังหรือไม่ยังไม่ยืนยัน ไม่ใช่ "รอบใหม่เท่านั้น" อย่างที่เคยยืนยันไว้

## 7. การอ้างอิงข้าม

- [vendor-pricelist](/th/inventory/vendor-pricelist) — รอบ RFQ (`tb_request_for_pricing`) เก็บ FK `pricelist_template_id` แบบ persist และ portal vendor ภายนอก auto-create draft `tb_pricelist` ต่อ vendor ที่ถูกเชิญจาก RFQ; ดูกลไก RFQ/portal ในหน้าของโมดูลนั้นเอง (นอกขอบเขตที่นี่)
- [master-data/currency](/th/inventory/master-data/currency) — การ resolve `currency_id` (ตรวจแค่มีอยู่)
- [templates/purchase-request](/th/inventory/templates/purchase-request) — template พี่น้องที่กลไกต่างกันโดยพื้นฐาน: hard delete เทียบกับ soft delete ของ template นี้ และไม่มี link ฝั่งผู้บริโภคที่ persist เทียบกับ FK แบบ live จาก `tb_request_for_pricing` ของ template นี้

## 8. การอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `enum_pricelist_template_status` + `tb_pricelist_template` (บรรทัด 4222-4268), `tb_pricelist_template_comment` (บรรทัด 4270-4303), `tb_pricelist_template_detail` (บรรทัด 4305 เป็นต้นไป)
- **Backend service:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/price-list-template/price-list-template.service.ts` (เข้า Prisma โดยตรง — นี่คือ data layer จริง; `backend-gateway` `pricelist-templates.service.ts` เป็นแค่ TCP proxy บาง ๆ อยู่หน้ามัน); DTO และ validation factory ใน `dto/price-list-template.dto.ts`
- **Frontend:** `../carmen-inventory-frontend-react/routes/vendor-management/price-list-template/` (`plt-form.tsx`, `plt-form-schema.ts`, `plt-form-products-section.tsx` สำหรับ UI ของ MOQ)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/160-pl-template.spec.ts` — ดู suite "Clone (removed)" และสังเกตว่า step annotation ของ `TC-PT-030001` บรรยาย UI control (switch multi-MOQ, switch lead-time, ฟิลด์ max-items, checkbox เตือน, escalation days) ที่ test body ไม่เคยแตะเลย และที่ไม่มีอยู่ใน `plt-form.tsx`
