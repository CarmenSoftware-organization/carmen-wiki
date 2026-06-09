---
title: เทมเพลตรายการราคา (Price List Template)
description: template RFQ / pricelist ที่ใช้ซ้ำได้ นิยาม currency, validity, การเตือน และการ escalate — parent ของ vendor pricelist
published: true
date: 2026-06-09T16:28:56.000Z
tags: templates, price-list, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# เทมเพลตรายการราคา (Price List Template)

> **At a Glance**
> **Owner:** Product Admin / Procurement Lead &nbsp;·&nbsp; **Table:** `tb_pricelist_template` &nbsp;·&nbsp; **ใช้โดย:** [vendor-pricelist](/th/inventory/vendor-pricelist) (รอบ RFQ spawn จาก template) &nbsp;·&nbsp; รูปร่างของรอบ pricelist — currency, validity, การเตือน, การ escalate

![เทมเพลตรายการราคา (Price List Template) screen](/screenshots/templates/price-list.png)

![เทมเพลตรายการราคา (Price List Template) detail screen](/screenshots/templates/price-list-detail.png)

## 1. คืออะไรและสำหรับใคร

template pricelist คือ **รูปร่างของรอบ pricelist**: ใบเสนอราคาอยู่ในสกุลเงินใด, pricelist ที่ได้อยู่ valid กี่วัน, ตารางการเตือนแบบใดที่ไล่ผู้ขายก่อน deadline, และหลังกี่วันที่การตอบยังไม่เข้ามาจะ escalate ผู้ซื้อเลือก template ตอนเริ่มรอบ RFQ ใหม่; การตอบของผู้ขายจริงอยู่บนตาราง child `tb_pricelist`

template เร่งวงจรการจัดซื้อที่เกิดซ้ำ — แทนที่จะตั้งค่าทุก RFQ ใหม่ ผู้ซื้อใช้ template เช่น "Quarterly Beverage RFQ" ซ้ำพร้อมการตั้งค่าการแจ้งเตือนทั้งหมดที่อยู่ในที่แล้ว

**ดูแลโดย** Product Admin หรือ Procurement Lead **อ่านโดย** flow การสร้าง RFQ และ background job การเตือน

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง template | Master Data → Pricelist Templates → New | เลือก currency, validity, การเตือน |
| activate สำหรับรอบใหม่ | set `status = active` | เลือกได้ใน picker RFQ ใหม่ |
| แก้ตารางการเตือน | edit template → reminder days | array ของวันก่อน deadline (เช่น `[14,7,3,1]`) |
| ปลดประจำการ template | set `status = inactive` | ลบออกจาก picker; RFQ เก่ายังอ่านได้ |
| Clone สำหรับ variant | ใช้ action clone ใน UI | หลีกเลี่ยงการป้อน currency/validity/reminders ใหม่ |
| เปลี่ยนคำแนะนำสำหรับ vendor | edit template → vendor instructions text | render ให้ vendor เมื่อ RFQ ถูกส่ง |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Name already exists" | ซ้ำในกลุ่ม template ที่ไม่ถูก delete | เลือกชื่ออื่น (บังคับโดย app) |
| ลบไม่ได้ | template มีรอบ RFQ ที่ออกแล้ว | flip `status = inactive` แทน |
| reminder days ถูกปฏิเสธ | ไม่ sort descending หรือมี integer ที่ไม่ใช่ค่าบวก | แก้ array (เช่น `[14,7,3,1]`) |
| "Currency not active" | `tb_currency.is_active = false` | activate currency ภายใต้ [master-data/currency](/th/inventory/master-data/currency) |
| validity ติดลบ | `validity_period < 0` | ใช้ integer ที่ไม่ติดลบ |

## 4. Edge Cases

- **เปลี่ยน currency บน template ที่ active** กระทบเฉพาะรอบ RFQ ใหม่; pricelist ที่มีอยู่คง currency เดิม
- **การรันการเตือน** อยู่ใน background job; template จับ *ตาราง* ไม่ใช่ state ของ job
- **Lifecycle** `draft` → `active` → `inactive` `draft` แก้ได้; `active` เลือกได้; `inactive` ถอนจาก picker แต่ยังอ่านได้บน history
- **Hard-delete ถูกบล็อก** เมื่อ template ถูกออกแล้ว; soft-delete เท่านั้น

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

**Constraints:** Primary key บน `id` FK บน `currency_id` `onDelete: NoAction` reverse relation ไป `tb_pricelist_template_detail` และ `tb_request_for_pricing`

**`enum_pricelist_template_status`:** `draft`, `active`, `inactive`

## 6. กฎทางธุรกิจ

- **Uniqueness** `name` unique ในกลุ่มที่ไม่ถูก delete (บังคับโดย app; ไม่มี `@@unique` แบบ explicit)
- **Deletion guards** template ที่ออกเป็น RFQ จริงแล้ว hard-delete ไม่ได้; flip `inactive` แทน
- **Validation** `validity_period >= 0`; `escalation_after_days >= 0`; `reminder_days` sort descending พร้อม integer บวก; `currency_id` ต้องอ้าง currency ที่ active
- **Lifecycle** `draft` แก้ได้; `active` เลือกได้สำหรับ RFQ ใหม่; `inactive` ลบออกจาก picker คงอ่านได้
- **การรันการเตือน** Background job ตรวจ flag + deadline ของ RFQ; template จับเฉพาะตาราง
- **เปลี่ยน currency** รอบใหม่เท่านั้น — pricelist เก่าไม่เปลี่ยน

## 7. การอ้างอิงข้าม

- [vendor-pricelist](/th/inventory/vendor-pricelist) — ผู้บริโภคเพียงรายเดียว รอบ RFQ spawn จาก template
- [master-data/currency](/th/inventory/master-data/currency) — การ resolve `currency_id`

## 8. การอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_pricelist_template` (บรรทัด ~3869-3911), `enum_pricelist_template_status` (บรรทัด ~3863-3867)
- **Frontend:** `../carmen-inventory-frontend/app/(root)/(protected)/vendor-management/price-list-template/`
