---
title: บันทึกกิจกรรม (Activity)
description: บันทึก activity ระดับ tenant — ทุกการเปลี่ยนสถานะที่มีความหมายถูกเก็บเป็นหนึ่งแถวพร้อม actor, entity, snapshot ก่อน/หลัง, IP และ user agent แสดงผลผ่านหน้าจอ /system-admin/activity-log ทั่วแพลตฟอร์มเท่านั้น — ไม่มี drawer ต่อเอกสารฝังอยู่เลย
published: true
date: 2026-07-22T00:00:00.000Z
tags: reporting-audit, activity, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# บันทึกกิจกรรม (Activity)

> **At a Glance**
> **เจ้าของ:** Append-only (audit service) &nbsp;·&nbsp; **ตาราง:** `tb_activity` &nbsp;·&nbsp; **ใช้โดย:** chain audit ของทุกโมดูลธุรกรรม &nbsp;·&nbsp; Audit log ของ tenant — หนึ่งแถวต่อหนึ่งการเปลี่ยนสถานะที่มีความหมาย

![บันทึกกิจกรรม (Activity) screen](/screenshots/reporting-audit/activity.png)

## 1. ภาพรวมและผู้ใช้งาน

ตาราง activity คือ **audit log ของ tenant** — หนึ่งแถวต่อหนึ่งการเปลี่ยนสถานะที่มีความหมาย เก็บข้อมูล *ใครทำอะไรกับแถวไหน* โดยไม่ผูกผู้เขียนกับผู้บริโภค ทุกโมดูลธุรกรรม append ผ่าน audit service เดียว ผู้บริโภค (compliance export, history panel ใน app, security forensics) อ่านโดย `entity_type` + `entity_id` เสริมคอลัมน์ audit ระดับแถว (`created_by_id` ฯลฯ) ด้วย chain ของ event แบบเต็มพร้อม snapshot เก่า/ใหม่และ context ของ request

ตารางออกแบบให้เป็น generic และ write-heavy โดยตั้งใจ `entity_type` เป็น discriminator ที่เป็น string แบบอิสระ; `entity_id` คือ UUID ของเป้าหมาย; enum `action` ครอบคลุมคำกริยา lifecycle

**ดูแลโดย** audit service (เขียนอย่างเดียว) **อ่านโดย** หน้าจอเดียวเท่านั้น — `/system-admin/activity-log` ไม่พบ "Activity drawer" ต่อเอกสารที่ฝังอยู่ที่ไหนใน `carmen-inventory-frontend-react` เลย — `useActivityLog`/endpoint `ACTIVITY_LOGS` ถูกอ้างอิงเฉพาะโดย `activity-log-component.tsx` และ table hook ของมันเอง

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดูรายการ activity log | `/system-admin/activity-log` | มุมมองรายการหรือ grid; filter สำหรับ **action**, **entity type** และ **ผู้ใช้** (actor) บวกค้นหาแบบข้อความอิสระ |
| กรองตาม action | Multi-select Action | จำกัดเหลือ 5 ตัวเลือกใน UI (`create`, `update`, `delete`, `login`, `logout`) — enum มี 20 ค่าทั้งหมด; action อื่นถูกเขียนแต่ไม่มีเป็น filter ด่วน |
| กรองตามประเภท entity | Multi-select Entity Type | รายการคัดสรร ~13 ค่า (`purchase_request`, `purchase_order`, `good_received_note`, `credit_note`, `store_requisition`, `inventory_transaction`, `product`, `vendor`, `location`, `department`, `currency`, `period`, `auth`) — `entity_type` เองเป็น free-form ดังนั้นค่าอื่นอาจมีอยู่ในข้อมูลโดยไม่มี filter chip ที่ตรงกัน |
| Export มุมมองที่กรองปัจจุบัน | ปุ่ม **Export** | export XLSX แบบ client-side (`useExportActivityLog`) ใช้ query params เดียวกับรายการ |
| Print | ปุ่ม **Print** | Print หน้าปัจจุบันของ browser |
| ตรวจดูหนึ่งแถว | คลิกแถว | เปิด `ActivityLogDetailSheet` — ใกล้เคียงที่สุดกับมุมมอง "diff เก่า vs ใหม่"; render `old_data`/`new_data` JSONB |
| **ไม่มีที่ไหนเลย** | — | "Activity" drawer/tab ต่อเอกสารที่ฝังบนหน้ารายละเอียด PR/PO/GRN/ฯลฯ ไม่มีอยู่จริง — หน้าจอรายการทั่วแพลตฟอร์มเป็น surface เดียว กรองด้วย `entity_type` + `entity_id` ที่คัดลอกด้วยมือผ่าน URL params ได้ถ้าจำเป็น |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ | สาเหตุ | การจัดการ |
|---|---|---|
| ไม่มีแถว activity สำหรับการเปลี่ยนที่ทราบ | service-layer interceptor ถูกข้าม | ยืนยันว่าการเปลี่ยนเดินผ่าน audit service ไม่ใช่ raw SQL |
| `actor_id IS NULL` | actor ของระบบ (background job) — เป็นไปตามคาด | ไม่ต้องแก้; ถือเป็น action ของระบบ |
| `old_data` ว่างเปล่าบน update | snapshotter รันหลังการเขียน | บั๊ก — snapshotter ต้องจับ state ก่อน |
| Audit log ช้า | scan ช่วงวันที่บน `created_at` | ใช้ query แบบ scope ตาม entity เมื่อทำได้; หรือ partition |

## 4. กรณีพิเศษ

- **Append-only** โค้ดของแอปไม่อัปเดตแถวเลย — `updated_*` มีไว้เพื่อความสมมาตรเท่านั้น Hard-delete สงวนไว้สำหรับการล้างตาม retention
- **ไม่มีการบังคับ FK บน `entity_id`** เป็น polymorphic ข้ามหลายตาราง; แถวค้างเป็นความตั้งใจ (ยังมีค่าสำหรับ audit ของ entity ที่ถูกลบ)
- **Actor ข้าม schema** `actor_id` อ้างอิง `tb_user.id` ของแพลตฟอร์มโดยไม่มี relation ที่บังคับใช้ `NULL` = actor ของระบบ
- **Retention** ขับโดยนโยบายของ tenant; schema ไม่กำหนดเพดาน Job ตามเวลาอาจย้ายแถวเก่าไปที่ cold storage

---

## 5. โมเดลข้อมูล (Dev)

แหล่ง: tenant schema

### 5.1 `tb_activity`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `action` | `enum_activity_action?` | Yes | คำกริยา lifecycle |
| `entity_type` | `String?` | Yes | discriminator แบบอิสระ (เช่น `purchase_request`) |
| `entity_id` | `String? @db.Uuid` | Yes | UUID ของแถวเป้าหมาย |
| `actor_id` | `String? @db.Uuid` | Yes | ผู้ใช้ที่ดำเนินการ (ข้าม schema; ไม่ถูกบังคับ) |
| `meta_data` | `Json? @db.JsonB` | Yes | Default `{}` Context ของ request (route, session, correlation id) |
| `old_data` | `Json? @db.JsonB` | Yes | Default `{}` Snapshot ก่อน |
| `new_data` | `Json? @db.JsonB` | Yes | Snapshot หลัง |
| `ip_address` / `user_agent` / `description` | `String?` | Yes | metadata ของ request + สรุปแบบเลือกได้ |
| `doc_version` | `Int @db.Integer` | No | Default `0` เพิ่มเมื่อ 2026-06-12 ทั่ว 103 ตาราง tenant; ยังไม่ยืนยันว่าถูกอ่าน/เขียนสำหรับตาราง append-only นี้โดยเฉพาะ |
| คอลัมน์ audit | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@index([entity_type, entity_id])` map `activity_entitytype_entityid_idx` — รองรับ "ประวัติของแถว X ในตาราง Y" `actor_id` ไม่มี relation DB (ข้าม schema)

**`enum_activity_action`:** `view`, `create`, `update`, `delete`, `login`, `logout`, `approve`, `reject`, `cancel`, `void`, `print`, `email`, `other`, `upload`, `download`, `export`, `import`, `copy`, `move`, `rename`, `save`

## 6. กติกาทางธุรกิจ

- **Append-only** ไม่มี update จากโค้ดแอป; hard-delete สงวนไว้สำหรับการล้างตาม retention
- **ความเที่ยงตรงของ snapshot** `old_data` / `new_data` carry JSON ของแถวเต็มในเวลาที่เปลี่ยน การ diff เป็นเรื่องของ render ความลับถูก redact ก่อน persist
- **ไม่บังคับ FK บน `entity_id`** เป็น polymorphic; แถวค้างเป็นความตั้งใจ
- **Actor ข้าม schema** FK ไม่ถูกบังคับ; `NULL` = actor ของระบบ
- **ประสิทธิภาพ** การทำดัชนีน้อยโดยตั้งใจ (composite ครอบคลุมรูปแบบหลัก) การ scan ช่วงวันที่อาจต้อง partition เมื่อมีขนาดใหญ่
- **Retention** ขับโดยนโยบาย tenant; schema ไม่กำหนดเพดาน

## 7. ความเชื่อมโยงข้ามโมดูล

- โมดูลธุรกรรมทั้งหมด — [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory](/th/inventory/inventory), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check), [costing](/th/inventory/costing), [vendor-pricelist](/th/inventory/vendor-pricelist), [product](/th/inventory/product), [recipe](/th/inventory/recipe)
- [access-control/user](/th/inventory/access-control/user) — การ resolve `actor_id`
- [reporting-audit/notification](/th/inventory/reporting-audit/notification) — event ของ workflow โดยปกติ fan-out ไปทั้งสองทาง
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — action `upload` / `download` บันทึกด้วย `entity_type = 'attachment'`

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity` (บรรทัด ~280), `enum_activity_action` (บรรทัด ~56)
- **Frontend route:** `../carmen-inventory-frontend-react/routes/system-admin/activity-log/activity-log.route.tsx`, `activity-log-component.tsx`, `activity-log-detail-sheet.tsx`
- **Frontend hook/type:** `../carmen-inventory-frontend-react/hooks/use-activity-log.ts` (`useActivityLog`, `useExportActivityLog`), `types/activity-log.ts`
- **ผู้เขียน (ตัวอย่าง):** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` — `logAuthActivity()` เขียนแถว `login`/`logout` ไปยัง business unit เริ่มต้นของผู้ใช้เท่านั้น
