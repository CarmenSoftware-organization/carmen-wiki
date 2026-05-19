---
title: location ของผู้ใช้ (User Location)
description: Scope ของ location ต่อผู้ใช้ภายใน tenant — จำกัด user ให้อยู่ใน subset ของ location สต๊อกสำหรับการออก count และ adjustment
published: true
date: 2026-05-19T23:55:00.000Z
tags: access-control, user-location, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# location ของผู้ใช้ (User Location)

> **At a Glance**
> **เจ้าของ:** Sysadmin / BU Admin &nbsp;·&nbsp; **ตาราง:** `tb_user_location` &nbsp;·&nbsp; **ใช้โดย:** [inventory](/th/inventory/inventory), [store-requisition](/th/inventory/store-requisition), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) &nbsp;·&nbsp; Filter location ระดับ row — จำกัด row สต๊อกที่ user มองเห็น

## 1. คืออะไรและใครใช้

`user-location` ทำให้ effective scope ของ user แคบลงจาก "ทุก location" เป็น "subset นี้" Storekeeper ที่มอบหมายให้สอง storeroom ควรเห็นเฉพาะสองที่ใน location picker, เอกสาร count และหน้าจอ adjustment ของตน ตารางเป็น many-to-many ง่ายๆ ระหว่าง [access-control/user](/th/inventory/access-control/user) และ [master-data/location](/th/inventory/master-data/location) พร้อม pattern soft-delete แบบ active-only

ไม่เหมือน [access-control/application-role](/th/inventory/access-control/application-role) (ซึ่ง gate **action**) และ [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) (ซึ่ง gate **การเข้า BU**) `user-location` เป็น **filter ข้อมูลระดับ row** — จำกัด row ที่มองเห็นโดยไม่เปลี่ยน role หรือ permission ชุดว่างถูกตีความตามข้อตกลงว่า "ไม่มีข้อจำกัด"

**บำรุงรักษาโดย** Sysadmin และ BU admin **อ่านโดย** ทุก list/picker ในโมดูลที่มีสต๊อก

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| มอบหมาย user ให้ location | User-edit → tab **Locations** → Add | เลือก location จากแคตตาล็อก BU |
| Reassign storekeeper | Soft-delete row เก่า + insert ใหม่ | เอกสารที่เปิดยังทำงาน (FK target `tb_location`) |
| ดู effective scope ของ user | User-edit → tab **Locations** | แสดงการมอบหมายที่ active ปัจจุบัน |
| ลบ scope ทั้งหมด (full access) | Soft-delete ทุก row | ชุดว่าง = "ไม่มีข้อจำกัด" ตามข้อตกลง |
| ตรวจสอบการเปลี่ยน scope | [reporting-audit/activity](/th/inventory/reporting-audit/activity) log | Filter โดย `entity_type = user_location` |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| User ไม่เห็น location ที่คาดหวัง | Row `tb_user_location` ขาดหาย หรือข้อตกลงชุดว่างไม่ถูก apply | เพิ่ม row หรือยืนยันพฤติกรรม service code |
| Error การมอบหมายซ้ำ | `(user_id, location_id)` มีอยู่ | Reactivate row ที่มีอยู่แทน |
| "Location not in this BU" | Location เป็นของ BU อื่น | เลือก location จาก BU ที่ active ของ user |
| Orphan `user_id` หลังการลบ platform-user | Cross-schema, ไม่มีการบังคับ FK | รัน maintenance job เพื่อ clean row เก่า |

## 4. กรณีพิเศษ

- **Empty-set semantics** ตามข้อตกลง "ไม่มีข้อจำกัดระดับ row" — ยืนยันกับ service code ถ้าพึ่งพา default นี้สำหรับเส้นทาง sensitive
- **Cross-schema integrity** `user_id` อ้างอิง platform `tb_user.id` แต่ **ไม่ใช่** Prisma FK — แอป validate ตอน insert
- **การ override ต่อเอกสาร** ตารางนี้เป็น **scope default** สำหรับ picker; เวิร์กโฟลว์เฉพาะอาจขยาย (เช่น ผู้อนุมัติใน [store-requisition](/th/inventory/store-requisition) ต้องการทั้งต้นทางและปลายทาง)
- **Reassignment เป็นสอง op** Soft-delete row A, insert row B — เอกสารที่เปิดยังทำงาน

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_user_location`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String @db.Uuid` | No | อ้างอิง platform `tb_user.id`; ไม่ใช่ Prisma FK (cross-schema) |
| `location_id` | `String @db.Uuid` | No | FK ไปยัง tenant `tb_location` |
| `note` | `String? @db.VarChar` | Yes | บริบทการมอบหมาย |
| `info` | `Json? @db.JsonB` | Yes | Default `{}` Metadata ที่สงวนไว้ |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([user_id, location_id, deleted_at])` Index บน `(user_id, location_id)` FK ไปยัง `tb_location` `onDelete: NoAction` `user_id` บังคับฝั่งแอปพลิเคชัน

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** User มีอย่างมากที่สุดหนึ่งการมอบหมายที่ active ต่อ location
- **Empty-set semantics** ตามข้อตกลง "ไม่มีข้อจำกัดระดับ row" — code path ที่ต้องการการมอบหมายชัดเจนต้องตรวจสอบ `count > 0`
- **Cross-schema integrity** แอป validate `user_id` ตอน insert; maintenance job clean up หลังการลบ user
- **การ์ดการลบ** Hard-delete อนุญาต (ไม่มี FK target ธุรกรรม); soft-delete รักษา audit
- **Lifecycle** Reassignment เป็นสอง operation (soft-delete + insert); FK ระดับเอกสาร target `tb_location` ดังนั้นงานที่เปิดถูกรักษา
- **การ override ต่อเอกสาร** Scope default เท่านั้น — เวิร์กโฟลว์เฉพาะอาจขยายหรือแคบลง

## 7. การอ้างอิงข้าม

- [inventory](/th/inventory/inventory) — หน้าจอ list และ movement filter โดยชุดของ user
- [store-requisition](/th/inventory/store-requisition) — location การออก/ขอ validate กับ scope
- [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) — เอกสาร count จำกัดที่ location ของ user
- [master-data/location](/th/inventory/master-data/location) — ฝั่ง location
- [access-control/user](/th/inventory/access-control/user) — ฝั่ง user

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_user_location` (lines ~4451-4470)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/user-role/` — tab Locations
