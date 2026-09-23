---
title: เวอร์ชันเอกสาร (Optimistic Concurrency)
description: ฟิลด์ doc_version (integer) ที่ป้องกันทุกตาราง tenant จากการเขียนทับ — ไคลเอนต์ส่งเวอร์ชันกลับมาตอนบันทึก; ค่าเก่าได้ 409 DOC_VERSION_CONFLICT ค่าหายได้ COMMON_DOC_VERSION_REQUIRED บังคับใช้โดย Prisma client extension
published: true
date: '2026-09-23T01:30:00.000Z'
tags: system-config, concurrency, doc-version, optimistic-lock, carmen-software
editor: markdown
dateCreated: 2026-06-09T00:00:00.000Z
---

# เวอร์ชันเอกสาร (Optimistic Concurrency)

> **สรุปโดยย่อ**
> **ฟิลด์:** `doc_version` (integer) ในเพย์โหลดการอัปเดตของเอกสาร &nbsp;·&nbsp; **ป้องกัน:** การเขียนทับข้อมูลจากการแก้ไขพร้อมกัน &nbsp;·&nbsp; **เมื่อค่าไม่ตรง:** **409** พร้อม code `DOC_VERSION_CONFLICT`; **เมื่อไม่ส่งมา:** `COMMON_DOC_VERSION_REQUIRED` &nbsp;·&nbsp; **ใช้กับ:** ทุก model ของ tenant ยกเว้น `tb_gl_balance` และ `tb_gl_jv_template_run` (157 จาก 159 ที่ HEAD — ตรวจสอบ 2026-09-22) &nbsp;·&nbsp; **ไม่ใช่** ตัวนับการเรนเดอร์ไฟล์แนบ (ดู §5)

## สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22)

กลไกนี้รวมศูนย์อยู่ใน Prisma client ของ tenant ไม่ได้เขียนมือต่อ service `packages/prisma-shared-schema-tenant/src/client.ts` (`$extends` บน `update`, ~`:440-490`):

- ถ้าผู้เรียกใส่ `doc_version` ใน `where` clause extension จะถือว่าเป็น version guard; เมื่อสำเร็จจะ **เพิ่มค่าอัตโนมัติ** `doc_version` (`{ increment: 1 }`) เว้นแต่ผู้เรียกตั้ง `data.doc_version` ไว้ชัดเจน
- เมื่อ Prisma ตอบ `P2025` ("record to update not found") ภายใต้ version guard extension จะอ่านแถวซ้ำด้วย id: ถ้ายังมีอยู่แปลว่าการอัปเดตแพ้ race และโยน `OptimisticLockError` (`code = 'DOC_VERSION_CONFLICT'`); ถ้าหายไปจริง error not-found เดิมจะถูกส่งต่อ
- `@TryCatch` (`apps/micro-business/src/common/decorators/try-catch.decorator.ts:7-12,67`) รู้จัก `DOC_VERSION_CONFLICT` และ map เป็น **409**
- service จึงเขียน `where: { id, doc_version: data.doc_version }` และปฏิเสธเวอร์ชันที่หายไปตั้งแต่ต้นด้วย `ERROR_CATALOG.COMMON_DOC_VERSION_REQUIRED` (เช่น `notification-template.service.ts:129-150`, `running-code.service.ts:301`, `inventory-period.service.ts:243`)

ความครอบคลุมขยายขึ้นตั้งแต่เขียนหน้านี้: 157 จาก 159 model ของ tenant ประกาศ `doc_version Int @default(0)` (มีเพียง `tb_gl_balance` และ `tb_gl_jv_template_run` ที่ไม่มี) รวมตารางที่รายการใน §3 ไม่เคยกล่าวถึง — `tb_inventory_period*`, `tb_workflow`, `tb_notification_template`, `tb_application_config`, `tb_location_user`, `tb_department_user` platform schema ใช้คอลัมน์เดียวกันบน `tb_user`, `tb_application_role`, `tb_permission`, `tb_user_invitation` ฯลฯ ฟอร์มของ frontend ส่งค่าที่โหลดมากลับไป (`doc_version` บนทุก payload `PATCH`/`PUT` ใน `types/*.ts`)

## 1. คืออะไรและใครใช้

`doc_version` คือกลไก **optimistic-concurrency**: เป็น integer ที่เพิ่มขึ้นเรื่อย ๆ ซึ่งเก็บไว้ที่ aggregate root ของเอกสาร การอ่านทุกครั้งจะคืนค่า `doc_version` ปัจจุบัน และทุกการ **อัปเดตต้องส่งค่าเวอร์ชันที่ไคลเอนต์ได้รับมาล่าสุด** เซิร์ฟเวอร์จะเขียนข้อมูลก็ต่อเมื่อค่าเวอร์ชันที่ส่งมายังตรงกับค่าที่จัดเก็บอยู่ — แล้วจึงเพิ่มค่าเวอร์ชัน หากผู้ใช้สองคนเปิดเอกสารเดียวกันและบันทึกพร้อมกัน การบันทึกครั้งที่สองจะล้มเหลวแทนที่จะเขียนทับข้อมูลโดยไม่แจ้งเตือน

กลไกนี้เป็น *optimistic*: ไม่มีการล็อกแถวข้อมูลขณะที่ผู้ใช้กำลังแก้ไข ความขัดแย้งจะถูกตรวจพบเมื่อบันทึก ไม่ใช่การป้องกันล่วงหน้า ซึ่งเหมาะกับการแก้ไขเอกสารที่ใช้เวลานานและความขัดแย้งเกิดขึ้นน้อย แต่มีผลกระทบมากหากเกิดขึ้น

**ตั้งค่าโดย** path การอัปเดตของทุก service (เปิดตัวพร้อมกันทั่ว backend เมื่อ 2026-06-04) **ตรวจสอบโดย** update handler เดียวกัน **แสดงต่อ** ไคลเอนต์ในรูปแบบ `409 Conflict` ที่ต้องจัดการ

## 2. พฤติกรรม

```
function update(id, payload):
    current = load(id)                       # current.doc_version = N
    if payload.doc_version != current.doc_version:
        raise Conflict(409)                  # someone saved first
    apply(payload)
    current.doc_version = N + 1              # bump on success
    save(current)
    return current                           # client reads back N+1
```

ไคลเอนต์ต้องส่งค่า `doc_version` ที่ได้รับจากการอ่านครั้งล่าสุด หลังจากบันทึกสำเร็จ ต้องใช้ค่าเวอร์ชันที่เพิ่มขึ้นซึ่งส่งกลับมาสำหรับการแก้ไขครั้งถัดไป

## 3. Entities ที่มีฟิลด์นี้

| กลุ่ม | Entities |
|---|---|
| การจัดซื้อ | purchase-request, purchase-order, purchase-request-template, request-for-pricing, credit-note |
| การรับสินค้าและสต็อก | good-received-note, stock-in, stock-out |
| การนับ | spot-check |
| การเบิกวัสดุ | store-requisition |
| ราคา | pricelist, pricelist-template |
| Config masters | credit-term, extra-cost-type, running-code, vendor-business-type, recipe-category, recipe-cuisine, recipe-equipment, recipe-equipment-category |
| System config (เพิ่มภายหลัง) | inventory-period, workflow, notification-template, application-config, application-user-config, business-unit (`PATCH` ของ Company Profile / Default Setting) |
| Access control (เพิ่มภายหลัง) | location-user, department-user, application-role, user-application-role (platform) |

ตารางข้างต้นเป็นเพียงตัวอย่าง; กติกาที่เป็นทางการคือ "ทุก model ของ tenant ยกเว้นสองตาราง GL ที่ระบุใน block สถานะ"

## 4. สถานการณ์ทดสอบ

| # | สถานการณ์เริ่มต้น | การกระทำ | ผลที่คาดหวัง |
|---|---|---|---|
| 1 | ไคลเอนต์ A และ B ทั้งคู่โหลดเอกสารที่ `doc_version = 5` | A บันทึกการเปลี่ยนแปลง | A สำเร็จ; เอกสารเป็น `doc_version = 6` |
| 2 | ต่อจาก #1 | B บันทึกการเปลี่ยนแปลง โดยยังส่ง `doc_version = 5` | **409 Conflict**; การเขียนของ B ถูกปฏิเสธ ไม่มีข้อมูลสูญหาย |
| 3 | ต่อจาก #2 | B ดึงข้อมูลใหม่ (ได้ `doc_version = 6`) นำการแก้ไขมาใส่ใหม่ แล้วบันทึกด้วยค่า `6` | B สำเร็จ; เอกสารเป็น `doc_version = 7` |
| 4 | ไคลเอนต์เดียว | อัปเดตโดยไม่มี `doc_version` | ถูกปฏิเสธด้วย `COMMON_DOC_VERSION_REQUIRED` ก่อนมีการเขียนใด ๆ |
| 5 | ไคลเอนต์ A ถือ `doc_version = 5`; ผู้ใช้อีกคนลบแถว | A บันทึก | error not-found **ไม่ใช่** 409 — extension อ่านซ้ำด้วย id และโยน `DOC_VERSION_CONFLICT` เฉพาะเมื่อแถวยังมีอยู่ |

## 5. อย่าสับสนกับ

`tb_attachment.doc_version` (tenant schema) มีรูปร่างเดียวกันคือ `Int @default(0)` เหมือนคอลัมน์ `doc_version` อื่นทุกตัว แต่ **มันไม่ใช่ตัวนับการเรนเดอร์ใหม่ที่ใช้งานจริง** — การค้นทั่ว repo ไม่พบโค้ดใดที่เพิ่มค่า อ่าน หรือแตะฟิลด์นี้เลย อันที่จริง `tb_attachment` เองก็ไม่มีการอ้างอิงจากโค้ด non-schema เลยที่ไหน — มันคือตาราง dead registry metadata ไฟล์จริงคือ `tb_file_tag` ในฐานข้อมูล file-service แยกต่างหาก ซึ่งไม่มีคอลัมน์ `doc_version` เลยด้วยซ้ำ ดู [system-config/document](/th/inventory/system-config/document) §5 สำหรับแบบจำลองข้อมูลที่แก้ไขแล้ว ถือว่า `tb_attachment.doc_version` เป็น schema ที่ไม่มีชีวิต ไม่ใช่ทั้ง concurrency guard ที่ใช้งานได้ *หรือ* ตัวนับการเรนเดอร์ใหม่ที่ใช้งานได้

ไม่เกี่ยวข้องเช่นกัน: `micro-cronjobs` เพิ่มคอลัมน์ `docVersion` ของตัวเอง + audit user ลงใน registry cron-job ของ platform (`5aa1cc6`, 2026-09-02) สำหรับหน้าจอ cron ของ Platform SPA — แนวคิดเดียวกัน คนละฐานข้อมูล ไม่อยู่ภายใต้ client extension ของ tenant

## 6. แหล่งอ้างอิง

- **Client extension:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/src/client.ts` — extension `update`, `OptimisticLockError` (`code = 'DOC_VERSION_CONFLICT'`)
- **การ map เป็น HTTP:** `../carmen-turborepo-backend-v2/apps/micro-business/src/common/decorators/try-catch.decorator.ts` (`isOptimisticLockError` → 409)
- **Error catalog:** `../carmen-turborepo-backend-v2/packages/error-catalog/src/catalog.ts` — `COMMON_DOC_VERSION_REQUIRED` (`:18`)
- **Schema:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `doc_version Int @default(0) @db.Integer` บน 157 จาก 159 model
