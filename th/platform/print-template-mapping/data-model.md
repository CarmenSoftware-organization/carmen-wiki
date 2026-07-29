---
title: Print Template Mapping — แบบจำลองข้อมูล (Data Model)
description: บันทึกประวัติศาสตร์ — tb_print_template_mapping ถูก drop โดย migration 20260723120000_print_form_default; is_default ย้ายไปอยู่ที่ tb_report_template แทน
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, print-template-mapping, data-model
editor: markdown
dateCreated: 2026-06-10T15:30:00.000Z
---

# Print Template Mapping — แบบจำลองข้อมูล (Data Model)

> **สถานะการใช้งาน (ตรวจสอบล่าสุด 2026-07-29): `tb_print_template_mapping` ไม่มีอยู่แล้ว** Migration `20260723120000_print_form_default` (carmen-turborepo-backend-v2) รัน `DROP TABLE "tb_print_template_mapping"` หลังจาก backfill ความหมายของ `is_default` ไปยังคอลัมน์ใหม่ `tb_report_template.is_default` หน้านี้บันทึกตารางตามที่เคยเป็นจนถึงการ sync ที่ตรวจสอบล่าสุด (2026-06-10) เพื่อการอ้างอิงเชิงประวัติศาสตร์เท่านั้น — อย่าใช้เป็นข้อมูลอ้างอิง schema ปัจจุบัน ดู [Report Templates — Data Model](/th/platform/report-templates/data-model) สำหรับกลไก `is_default` / `report_group` ที่ใช้งานจริง

> **At a Glance (เชิงประวัติศาสตร์)**
> **ตาราง:** `tb_print_template_mapping` — **ถูก drop เมื่อ 2026-07-23** &nbsp;·&nbsp; **ถูกอ้างอิง:** `tb_report_template` (ยังใช้งานอยู่ — ดู [Report Templates](/th/platform/report-templates/data-model)) &nbsp;·&nbsp; **Enum:** ไม่มี — `document_type` เป็น VarChar ที่ validate กับรายการ 10 code ที่ hard-code ไว้ใน Go &nbsp;·&nbsp; **Constraint:** มีแค่ `@id` — ไม่มี `@@unique`, ไม่มี Prisma `@relation`/FK ระดับ DB

## 1. ภาพรวม (ตามที่เคยเป็นจนถึง 2026-06-10)

โมดูลนี้เป็นเจ้าของตารางเดียว `tb_print_template_mapping` เป็นแถว routing: code `document_type`, ตัวชี้ไปยัง `tb_report_template` ที่ render มัน, field การนำเสนอสำหรับเมนูพิมพ์ (`is_default`, `display_label`, `display_order`), คู่ allow/deny ของ BU, `is_active` และ audit trio มาตรฐานของแพลตฟอร์ม ตารางนี้ผิดปกติสำหรับ platform schema ตรงที่ไม่มี unique constraint และไม่มี Prisma relation เลย — กฎความถูกต้องทั้งหมด (validate document-type, ลด default คู่แข่ง) อยู่ใน Go service ของ micro-report ไม่ใช่ฐานข้อมูล

แม้ตารางนี้จะอยู่ใน platform Prisma schema แต่เจ้าของ CRUD คือ Go service ของ micro-report (GORM); controller ของ backend-gateway เป็นเพียง pass-through proxy ทั้ง Go model/repo/controller และ gateway proxy ถูกลบไปพร้อมกับตาราง (carmen-turborepo-backend-v2 commit `c135bb21e`)

## 2. Schema เดิม

### 2.1 `tb_print_template_mapping` (ถูก drop แล้ว)

| Field | Prisma Type | คำอธิบาย |
| ----- | ----------- | ----------- |
| `id` | `String @db.Uuid` | Primary key |
| `document_type` | `String @db.VarChar(50)` | Code ชนิดเอกสาร (`PR`, `PO`, `GRN`, …); validate โดย Go service กับ `SupportedDocumentTypes` |
| `report_template_id` | `String @db.Uuid` | id ของแถว `tb_report_template` ที่ render — ไม่มี `@relation`, ไม่มี FK ระดับ DB |
| `is_default` | `Boolean @default(true)` | เทมเพลตสำหรับปุ่ม Print แบบ legacy |
| `display_label` | `String? @db.VarChar(255)` | Label ที่แสดงในเมนู "Print as…" |
| `display_order` | `Int @default(0)` | ตำแหน่งการเรียง; ใช้เป็น tie-breaker ตอน resolve |
| `allow_business_unit` / `deny_business_unit` | `Json? @db.JsonB` | array code ของ BU ที่กำหนดขอบเขต mapping |
| `is_active` | `Boolean @default(true)` | แถวที่ inactive ถูกข้ามโดย `resolve` |
| audit trio | — | `created_at/by_id`, `updated_at/by_id`, `deleted_at/by_id` — bare UUID ไม่มี FK |

**สิ่งที่แทนที่แต่ละ field:** `is_default` → `tb_report_template.is_default` (ตอนนี้บังคับด้วย partial unique index ระดับ DB แทนการลด default แบบ best-effort ของ Go) `document_type` → `tb_report_template.report_group` (ยังเป็น plain String แต่ตอนนี้ขับเคลื่อนด้วย constant `FORM_REPORT_GROUPS` ฝั่ง SPA แทนรายการ hard-code ฝั่ง Go) `display_label` / `display_order` — ไม่พบสิ่งทดแทน; หน้าจอ Form Groups ใหม่เรียงตาม `is_default` แล้วตามด้วยชื่อ ไม่มี label ต่อแถวหรือการเรียงลำดับด้วยมือ `allow_business_unit` / `deny_business_unit` บน *mapping* — ไม่มีสิ่งทดแทน `tb_report_template` มีคู่ allow/deny ของตัวเอง (กำหนดขอบเขตการมองเห็นแถวเทมเพลตเอง) แต่ไม่มีวิธีกำหนด "default ตัวไหน" ต่างกันต่อ business unit แบบที่ mapping row เคยทำได้อีกต่อไป

## 3. ความสัมพันธ์เดิม

```
tb_report_template  1 ─── M  tb_print_template_mapping   (ถูก drop เมื่อ 2026-07-23)
```

## 4. Enum เดิม

`document_type` เคย validate กับ `model.SupportedDocumentTypes` (Go slice ที่ hard-code ไว้ เสิร์ฟด้วยผ่าน `GET .../document-types`): `PR, PO, GRN, SR, CN, IA, PC, SC, RFQ, INV` เทียบกับรายการ *ปัจจุบัน* `FORM_REPORT_GROUPS` บน `tb_report_template.report_group`: `PR, PO, GRN, SR, CN, SI, SO, IA, PC, SC, RFP, EOP` — ได้ `SI`, `SO`, `EOP` เพิ่ม; เสีย `INV`; `RFQ` เปลี่ยนชื่อเป็น `RFP` สองรายการนี้ไม่ใช่ vocabulary เดียวกัน แม้จะแก้ปัญหาเดียวกันก็ตาม

## 5. แหล่งข้อมูลอ้างอิง

- carmen-turborepo-backend-v2 migration `packages/prisma-shared-schema-platform/prisma/migrations/20260723120000_print_form_default/migration.sql` — การ drop, การ backfill และ unique index ใหม่
- carmen-turborepo-backend-v2 commit `c135bb21e` — การลบ model/repo/controller ฝั่ง Go และ proxy ของ gateway
- `../carmen-platform/src/constants/reportGroups.ts` — รายการ `FORM_REPORT_GROUPS` ปัจจุบัน

**Cross-links:** [หน้าแรก Print Template Mapping](/th/platform/print-template-mapping) &nbsp;·&nbsp; [UI Screens](./ui-screens.md) &nbsp;·&nbsp; [Permissions](./permissions.md) &nbsp;·&nbsp; [Report Templates — Data Model](../report-templates/data-model.md)
