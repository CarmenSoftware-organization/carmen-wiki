---
title: บันทึกกิจกรรม (Activity)
description: บันทึก activity ระดับ tenant — ทุกการเปลี่ยนสถานะที่มีความหมายถูกเก็บเป็นหนึ่งแถวพร้อม actor, entity, snapshot ก่อน/หลัง, IP และ user agent
published: true
date: 2026-05-17T12:00:00.000Z
tags: reporting-audit, activity, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# บันทึกกิจกรรม (Activity)

> **At a Glance**
> **เจ้าของ:** Append-only (audit service) &nbsp;·&nbsp; **ตาราง:** `tb_activity` &nbsp;·&nbsp; **ใช้โดย:** chain audit ของทุกโมดูลธุรกรรม &nbsp;·&nbsp; Audit log ของ tenant — หนึ่งแถวต่อหนึ่งการเปลี่ยนสถานะที่มีความหมาย

## 1. ภาพรวมและผู้ใช้งาน

ตาราง activity คือ **audit log ของ tenant** — หนึ่งแถวต่อหนึ่งการเปลี่ยนสถานะที่มีความหมาย เก็บข้อมูล *ใครทำอะไรกับแถวไหน* โดยไม่ผูกผู้เขียนกับผู้บริโภค ทุกโมดูลธุรกรรม append ผ่าน audit service เดียว ผู้บริโภค (compliance export, history panel ใน app, security forensics) อ่านโดย `entity_type` + `entity_id` เสริมคอลัมน์ audit ระดับแถว (`created_by_id` ฯลฯ) ด้วย chain ของ event แบบเต็มพร้อม snapshot เก่า/ใหม่และ context ของ request

ตารางออกแบบให้เป็น generic และ write-heavy โดยตั้งใจ `entity_type` เป็น discriminator ที่เป็น string แบบอิสระ; `entity_id` คือ UUID ของเป้าหมาย; enum `action` ครอบคลุมคำกริยา lifecycle

**ดูแลโดย** audit service (เขียนอย่างเดียว) **อ่านโดย** drawer activity บนเอกสารแต่ละใบและ audit log ทั่วทั้งแพลตฟอร์ม

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดูประวัติของเอกสาร | รายละเอียดเอกสาร → drawer **Activity** | กรองโดย `entity_type` + `entity_id` |
| ค้นหา audit log ตามผู้ใช้ | Sysadmin → Audit Log | กรองโดย `actor_id` + ช่วงวันที่ |
| Compliance export | Audit Log → Export | เส้นทาง query เดียวกัน ส่งแถวไปยังที่จัดเก็บระยะยาว |
| Diff เก่า vs ใหม่ | เปิดแถว activity | snapshot JSONB `old_data` / `new_data`; diff ที่ฝั่ง render |
| ตรวจสอบการลบ | ค้นด้วย `entity_id` + `action = delete` | แถวเก่ายังมีค่า (ประวัติ entity ที่ถูกลบ) |

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

- โมดูลธุรกรรมทั้งหมด — [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[costing]], [[vendor-pricelist]], [[product]], [[recipe]]
- [[access-control/user]] — การ resolve `actor_id`
- [[reporting-audit/notification]] — event ของ workflow โดยปกติ fan-out ไปทั้งสองทาง
- [[reporting-audit/attachment]] — action `upload` / `download` บันทึกด้วย `entity_type = 'attachment'`

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_activity` (lines ~277-297), `enum_activity_action` (lines ~67-89)
- **Frontend:** Activity drawer ฝังในหน้ารายละเอียดของเอกสารแต่ละใบ; audit log ทั่วทั้งแพลตฟอร์มใน Sysadmin tooling
