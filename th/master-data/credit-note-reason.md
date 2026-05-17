---
title: เหตุผลใบลดหนี้ (Credit Note Reason)
description: รหัสเหตุผลสำหรับใบลดหนี้ที่ออกต่อ GRN — รองรับ flow การคืนสินค้าให้ผู้ขายและการแก้ราคา
published: true
date: 2026-05-17T07:28:28.000Z
tags: master-data, credit-note-reason, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# เหตุผลใบลดหนี้ (Credit Note Reason)

> **At a Glance**
> **เจ้าของ:** Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_credit_note_reason` &nbsp;·&nbsp; **ใช้โดย:** flow ใบลดหนี้ (return-to-vendor, แก้ราคา) &nbsp;·&nbsp; *ทำไม* ของทุกใบลดหนี้ที่ออกต่อ GRN

![เหตุผลใบลดหนี้ (Credit Note Reason) screen](/assets/screenshots/master-data/credit-note-reason.png)

## 1. คืออะไร / ใครใช้

**ใบลดหนี้** บันทึกสินค้าที่คืนให้ผู้ขายหรือการแก้ราคาต่อการส่งของที่รับไปก่อนหน้า **เหตุผลใบลดหนี้** คือ *ทำไม* — สินค้าเสียหาย, ส่งสินค้าผิด, ตกลงลดราคา, หมดอายุ ฯลฯ ทุกส่วนหัวของใบลดหนี้อ้างอิงหนึ่งเหตุผล และรายงานปลายน้ำจัดกลุ่มปริมาณ CN ตามเหตุผลเพื่อระบุปัญหาคุณภาพ / ผู้ขาย

เอนทิตีเป็น **flat lookup** — ตรรกะของเหตุผล (return-to-stock vs. write-off) อยู่ใน flow ใบลดหนี้เอง ไม่ใช่บนระเบียนเหตุผล **บริหารจัดการโดย** Product Admin; **อ่านโดย** developer และ tester ในเส้นทางใบลดหนี้ของ GRN

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มเหตุผลใหม่ | Configuration → Master Data → Credit Note Reason → **New** | บังคับ: `name`; `description` (เลือก) |
| แก้ description | Edit dialog | การเปลี่ยนชื่อเปลี่ยนการแสดงผลทุกที่ที่ CN ประวัติถูก list |
| ปลดระวางเหตุผล | Soft-delete (ตั้ง `deleted_at`) | ไม่มี `is_active` flag — soft-delete คือเส้นทาง retirement เดียว |
| ตรวจสอบว่า CN ใช้เหตุผลใด | เปิด header ของใบลดหนี้ | FK ของเหตุผลบน `tb_credit_note` |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Name already in use" | `name` ซ้ำบนแถว non-deleted | เลือกชื่ออื่นหรือ restore แถวที่มี |
| "Name required" | `name` ว่าง | เพิ่มชื่อแสดงผล |
| "Cannot delete — referenced by credit notes" | มี CN อย่างน้อยหนึ่งชี้ไปยังเหตุผลนี้ | Soft-delete เฉพาะถ้ายอมรับการแสดงผล "Unknown reason"; มิฉะนั้นเก็บไว้ |
| เหตุผลแสดงเป็นว่างบน CN | Hard-delete สำเร็จด้วยเหตุผลใดเหตุผลหนึ่ง (data fix เท่านั้น) | Restore หรือ backfill ผ่าน lookup |

## 4. Edge Cases

- **ไม่มีคอลัมน์ `is_active`** — lifecycle ผ่าน soft-delete เท่านั้น
- **การ propagate การเปลี่ยนชื่อ** — การแสดงผล refresh อัตโนมัติเพราะ CN เก็บ FK ไม่ใช่ text
- **แถวที่ soft-deleted ยัง resolve ได้** ผ่าน lookup ดังนั้น CN ประวัติยัง render ต่อ
- **การแปล** เหตุผลมักแสดงให้ผู้ขายเห็น จนกว่าจะมีตาราง localisation การแปลอยู่ใน `info` JSON
- **Adjustment-type vs. reason** ถ้า CN posts การปรับสต๊อก (write-off แทน return-to-stock) การปรับนั้นบรรจุ [[master-data/adjustment-type]] ของตัวเองในขณะที่ CN แม่เก็บเหตุผล

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_credit_note_reason`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผล (เช่น `Damaged on receipt`, `Price correction`) |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `note` | `String? @db.VarChar` | Yes | Internal note |
| `info`, `dimension` | `Json?` | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `creditnotereason_name_u` Index บน `name` Reverse relation ไปยัง `tb_credit_note` หมายเหตุ: ไม่มีคอลัมน์ `is_active`

## 6. กติกาทางธุรกิจ

- **Uniqueness** `name` unique ในแถว non-deleted (DB-enforced)
- **Deletion guards** เหตุผลที่ถูกอ้างอิงโดยใบลดหนี้ใด ๆ ไม่สามารถ hard-delete Soft-delete ถ้าไม่มี CN ประวัติอ้างอิง
- **Validation** `name` บังคับ
- **Lifecycle** ไม่มี `is_active`; soft-delete คือเส้นทาง retirement CN ประวัติเก็บ FK และ resolve ชื่อแม้บนแถวที่ soft-deleted
- **การแปล** เหตุผลอาจหันหน้าหาผู้ขาย — เก็บการแปลใน `info` จนกว่าจะมีการ introduce ตาราง localisation

## 7. การอ้างอิงข้ามโมดูล

- [[good-receive-note]] — ใบลดหนี้ออกในบริบท GRN FK ของเหตุผลบน `tb_credit_note`
- [[inventory-adjustment]] — เมื่อ CN posts การปรับสต๊อก การปรับนั้นบรรจุ [[master-data/adjustment-type]] เพิ่มเติมจากเหตุผล CN

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_credit_note_reason` (lines ~299-319); ใช้โดย `tb_credit_note` (lines ~321-…)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/credit-note-reason/`
