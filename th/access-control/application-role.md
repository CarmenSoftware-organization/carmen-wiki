---
title: บทบาท (Application Role)
description: นิยาม role ต่อ business unit บวกตาราง join ที่ map role กับ permission และ user กับ role — หัวใจของ tenant RBAC
published: true
date: 2026-05-17T07:28:28.000Z
tags: access-control, application-role, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# บทบาท (Application Role)

> **At a Glance**
> **เจ้าของ:** Sysadmin (ต่อ BU) &nbsp;·&nbsp; **ตาราง:** `tb_application_role` (+ `tb_application_role_tb_permission`, `tb_user_tb_application_role`) &nbsp;·&nbsp; **ใช้โดย:** การตรวจสอบ permission ของทุกโมดูลธุรกรรม &nbsp;·&nbsp; Bundle ที่ตั้งชื่อแล้วของ permission ที่มอบให้ผู้ใช้ภายใน BU

![บทบาท (Application Role) screen](/screenshots/access-control/application-role.png)

## 1. คืออะไรและใครใช้

Application role คือ **bundle ที่ตั้งชื่อแล้วของ [[access-control/permission]]** ที่มอบให้ผู้ใช้ภายใน [[master-data/business-unit]] ขณะที่ `platform_role` บน `tb_user` เป็น switch global แบบหยาบ application role เป็นเลเยอร์การอนุญาตฝั่ง tenant แบบละเอียดที่ควบคุม *สิ่งที่ผู้ใช้แต่ละคนทำได้ในแต่ละ BU* ทุก action UI ธุรกรรม — submit PR, อนุมัติ GRN, post adjustment — ถูก gate โดยการตรวจสอบว่า user ที่ active ถือ application role ที่รวม atom permission ที่ตรงกับ BU ที่ active หรือไม่

**บำรุงรักษาโดย** Sysadmin (ต่อ BU) **อ่านโดย** ทุก API endpoint ตอน request time

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง role สำหรับ BU | Configuration → Roles → **New** | เลือก BU, name, description |
| เพิ่ม permission ให้ role | Role edit → grid **Permissions** | Checkbox บน `tb_permission` จัดกลุ่มโดย `resource` |
| มอบหมายผู้ใช้ให้ role | Role edit → tab **Users** | User ต้องเป็นสมาชิก BU แล้ว ([[access-control/business-unit-user]]) |
| ปิดใช้ link permission ชั่วคราว | Role edit → toggle `is_active` ของ row | ลบจาก grant โดยไม่ unlink |
| ปลดระวาง role | ตั้ง `is_active = false` | การมอบหมายที่มีอยู่คงอยู่; permission หยุด grant ตอน eval ครั้งถัดไป |
| ตรวจสอบการเปลี่ยนแปลง role | [[reporting-audit/activity]] log | Filter โดย `entity_type = application_role` |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Role name already exists in this BU" | `(business_unit_id, name)` ซ้ำในกลุ่มที่ไม่ถูก delete | เลือกชื่ออื่นหรือ reactivate role ที่มีอยู่ |
| "User has no access to this BU" | ไม่มี row `tb_user_tb_business_unit` | Grant การเข้าถึง BU ก่อนผ่าน [[access-control/business-unit-user]] |
| ไม่สามารถ delete role | มีการมอบหมายที่ active อยู่ | Soft-delete หรือตั้ง `is_active = false` แทน |
| User ยังเห็น permission เก่า | Session ที่ cached | รอ refresh หรือบังคับ re-login |

## 4. กรณีพิเศษ

- **การตรวจสอบ permission เป็นแบบ live ไม่ใช่ snapshot** ไม่เหมือน master data การเปลี่ยน role มีผลตอน re-evaluation ของ permission ครั้งถัดไป — เอกสารประวัติศาสตร์ไม่ได้รับ permission แบบ retro
- **BU scoping บังคับฝั่งแอปพลิเคชัน** ไม่มี constraint DB บล็อกการมอบ role ให้ user ที่ไม่มี BU access — เลเยอร์ service ต้อง validate
- **Role ที่ soft-delete** หยุด grant permission (join filter `deleted_at IS NULL`) แต่ row การมอบหมายคงอยู่สำหรับ audit
- **Link permission ที่ inactive** (`tb_application_role_tb_permission.is_active = false`) ลบ permission โดยไม่ delete link — มีประโยชน์สำหรับ rollout เป็นขั้น

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: platform schema

### 5.1 `tb_application_role`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `business_unit_id` | `String @db.Uuid` | No | FK ไปยัง `tb_business_unit` — role scope ตาม BU |
| `name` | `String @db.VarChar` | No | ชื่อ role (เช่น `Procurement Manager`, `Storekeeper`) |
| `description` | `String?` | Yes | Free text |
| `is_active` | `Boolean? @db.Boolean` | Yes | Default `true` |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([business_unit_id, name, deleted_at])` Index บน `(business_unit_id, name, deleted_at)` FK ไปยัง `tb_business_unit` `onDelete: NoAction`

### 5.2 `tb_application_role_tb_permission`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `application_role_id` | `String @db.Uuid` | No | FK ไปยัง `tb_application_role` |
| `permission_id` | `String @db.Uuid` | No | FK ไปยัง `tb_permission` |
| `is_active` | `Boolean? @db.Boolean` | Yes | Default `true` ให้ปิด permission ชั่วคราวได้โดยไม่ unlink |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([application_role_id, permission_id, deleted_at])` FKs `onDelete: NoAction`

### 5.3 `tb_user_tb_application_role`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String @db.Uuid` | No | FK ไปยัง `tb_user` |
| `application_role_id` | `String @db.Uuid` | No | FK ไปยัง `tb_application_role` |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([user_id, application_role_id, deleted_at])` การ traversal (user, BU) → role[] join ผ่าน `tb_application_role` เพราะ `business_unit_id` อยู่ที่นั่น

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `(business_unit_id, name)` unique ในกลุ่ม role ที่ไม่ถูก delete User ถือแต่ละ role อย่างมากที่สุดหนึ่งครั้งต่อ BU
- **BU scoping** Role สามารถมอบให้ user ที่มี row `tb_user_tb_business_unit` ที่ active สำหรับ BU เดียวกันเท่านั้น (บังคับฝั่งแอปพลิเคชัน)
- **การ์ดการลบ** Hard-delete ถูกบล็อกถ้ามีการมอบหมายที่ active Soft-delete อนุญาต; การมอบหมายคงอยู่แต่ไม่มี permission ที่ grant
- **Cascade การ inactivate** `is_active = false` revoke permission ตอน re-evaluation ครั้งถัดไป; session ที่ cached อาจคงอยู่จนกว่าจะ refresh
- **Live ไม่ใช่ snapshot** การตรวจสอบ permission evaluate state join ปัจจุบัน — ไม่มี snapshot ฝั่งเอกสาร

## 7. การอ้างอิงข้าม

- [[access-control/permission]] — atom ที่ role รวบรวม
- [[access-control/user]] — account ที่ role มอบให้
- [[master-data/business-unit]] — ทุก role เป็นเจ้าของโดย BU
- [[access-control/business-unit-user]] — เงื่อนไขเบื้องต้นสำหรับการมอบหมาย role
- ทุกโมดูลธุรกรรม — ทุก auth check join ผ่านตารางเหล่านี้

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application_role` (lines ~30-52), `tb_application_role_tb_permission` (lines ~54-72), `tb_user_tb_application_role` (lines ~491-509)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/user-role/`
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`
