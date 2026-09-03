---
title: บทบาท (Application Role)
description: นิยาม role ต่อ business unit บวกตาราง join ที่ map role กับ permission และ user กับ role — หัวใจของ tenant RBAC
published: true
date: 2026-07-15T23:46:09.000Z
tags: access-control, application-role, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# บทบาท (Application Role)

> **At a Glance**
> **เจ้าของ:** Sysadmin (ต่อ BU) &nbsp;·&nbsp; **ตาราง:** `tb_application_role` (+ `tb_application_role_tb_permission`, `tb_user_tb_application_role`) &nbsp;·&nbsp; **ใช้โดย:** การตรวจสอบ permission ของทุกโมดูลธุรกรรม &nbsp;·&nbsp; Bundle ที่ตั้งชื่อแล้วของ permission ที่มอบให้ผู้ใช้ภายใน BU

![บทบาท (Application Role) screen](/screenshots/access-control/application-role.png)

![บทบาท (Application Role) detail screen](/screenshots/access-control/application-role-detail.png)

## 1. คืออะไรและใครใช้

Application role คือ **bundle ที่ตั้งชื่อแล้วของ [access-control/permission](/th/inventory/access-control/permission)** ที่มอบให้ผู้ใช้ภายใน [master-data/business-unit](/th/inventory/master-data/business-unit) เป็นเลเยอร์การอนุญาตฝั่ง tenant แบบละเอียดที่ควบคุม *สิ่งที่ผู้ใช้แต่ละคนทำได้ในแต่ละ BU* แยกจาก role ระดับ platform (`tb_platform_role` ระบบ relational ที่ scope ตาม cluster แยกต่างหาก เป็นของ Carmen Platform admin — ดูหัวข้อกรณีพิเศษใน [access-control/user](/th/inventory/access-control/user); คอลัมน์ enum `tb_user.platform_role` เดิมที่ระบบนี้มาแทนถูกลบไปแล้วเมื่อ 2026-06-10) ทุก action UI ธุรกรรม — submit PR, อนุมัติ GRN, post adjustment — ถูก gate โดยการตรวจสอบว่า user ที่ active ถือ application role ที่รวม atom permission ที่ตรงกับ BU ที่ active หรือไม่

**บำรุงรักษาโดย** Sysadmin (ต่อ BU) **อ่านโดย** ทุก API endpoint ตอน request time

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง role สำหรับ BU | `/system-admin/role/new` → **Name** + permission matrix → Save | ไม่มี BU picker บนฟอร์มนี้ — role ถูกสร้างภายใน BU context ที่ active ของผู้เรียก |
| เพิ่ม permission ให้ role | Role edit → permission matrix / picker (`permission-matrix.tsx`, `permission-picker.tsx`) | Checkbox บน `tb_permission` จัดกลุ่มโดย `resource`; คลิก column-header grant/revoke ทั้ง action ข้ามทุก resource, row `Grant All` grant ทั้งหมวดหมู่ |
| มอบหมายผู้ใช้ให้ role | **ไม่ได้อยู่บนหน้าจอ Role** — ทำจาก `/system-admin/user/:id` → ส่วน **Assign Roles** → toggle role card → Save | หน้าจอ Role edit มีแค่ Name + Permissions; ไม่มีแท็บ Users (ยืนยันจาก `role-form.tsx` และแคตตาล็อก test-case e2e `1101-role.md`) |
| ปลดระวาง role | ตั้ง `is_active = false` | การมอบหมายที่มีอยู่คงอยู่; permission หยุด grant ตอน eval ครั้งถัดไป |
| ลบ role | Action ของ row ใน role list, หรือปุ่ม **Delete** บน Hero ของหน้าจอ detail | ถูกบล็อกถ้ามีการมอบหมายที่ active อยู่ ตาม การตรวจสอบและ Error ด้านล่าง |
| ตรวจสอบการเปลี่ยนแปลง role | [reporting-audit/activity](/th/inventory/reporting-audit/activity) log | Filter โดย `entity_type = application_role` |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Role name already exists in this BU" | `(business_unit_id, name)` ซ้ำในกลุ่มที่ไม่ถูก delete | เลือกชื่ออื่นหรือ reactivate role ที่มีอยู่ |
| "User has no access to this BU" | ไม่มี row `tb_user_tb_business_unit` | Grant การเข้าถึง BU ก่อนผ่าน [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) |
| ไม่สามารถ delete role | มีการมอบหมายที่ active อยู่ | Soft-delete หรือตั้ง `is_active = false` แทน |
| User ยังเห็น permission เก่า | Session ที่ cached | รอ refresh หรือบังคับ re-login |

## 4. กรณีพิเศษ

- **การตรวจสอบ permission เป็นแบบ live ไม่ใช่ snapshot** ไม่เหมือน master data การเปลี่ยน role มีผลตอน re-evaluation ของ permission ครั้งถัดไป — เอกสารประวัติศาสตร์ไม่ได้รับ permission แบบ retro
- **BU scoping บังคับฝั่งแอปพลิเคชัน** ไม่มี constraint DB บล็อกการมอบ role ให้ user ที่ไม่มี BU access — เลเยอร์ service ต้อง validate
- **Role ที่ soft-delete** หยุด grant permission (join filter `deleted_at IS NULL`) แต่ row การมอบหมายคงอยู่สำหรับ audit
- **Link permission ที่ inactive** (`tb_application_role_tb_permission.is_active = false`) ลบ permission โดยไม่ delete link — มีประโยชน์สำหรับ rollout เป็นขั้น
- **การจัดการ role เองก็ถูก gate แบบหยาบ** Route `/system-admin/role` (และ `/system-admin/user`, `/system-admin/user-activity`) ถูก gate ด้วย frontend permission key แบบหยาบตัวเดียว คือ `PERMISSIONS.system_configuration.view` (`constant/module-list.ts`) — ไม่มี permission แบบละเอียด "ใครจัดการ role ได้" แยกจาก system-configuration access ทั่วไป

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
| `doc_version` | `Int` | No | Default `0` Optimistic-lock version — update DTO สะท้อน version ของ record ที่โหลดมา (`role.doc_version` ใน `role-form.tsx`); backend ปฏิเสธค่าที่ stale |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([business_unit_id, name, deleted_at])` Index บน `(business_unit_id, name, deleted_at)` FK ไปยัง `tb_business_unit` `onDelete: NoAction`

### 5.2 `tb_application_role_tb_permission`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `application_role_id` | `String @db.Uuid` | No | FK ไปยัง `tb_application_role` |
| `permission_id` | `String @db.Uuid` | No | FK ไปยัง `tb_permission` |
| `is_active` | `Boolean? @db.Boolean` | Yes | Default `true` Schema รองรับการปิด permission link ชั่วคราวโดยไม่ unlink; ไม่มี UI ใดที่ surface toggle นี้วันนี้ — หน้าจอ role-edit เพิ่ม/ลบ link เท่านั้น |
| `doc_version` | `Int` | No | Default `0` Optimistic-lock version |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([application_role_id, permission_id, deleted_at])` FKs `onDelete: NoAction`

### 5.3 `tb_user_tb_application_role`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String @db.Uuid` | No | FK ไปยัง `tb_user` |
| `application_role_id` | `String @db.Uuid` | No | FK ไปยัง `tb_application_role` |
| `doc_version` | `Int` | No | Default `0` Optimistic-lock version |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([user_id, application_role_id, deleted_at])` การ traversal (user, BU) → role[] join ผ่าน `tb_application_role` เพราะ `business_unit_id` อยู่ที่นั่น

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `(business_unit_id, name)` unique ในกลุ่ม role ที่ไม่ถูก delete User ถือแต่ละ role อย่างมากที่สุดหนึ่งครั้งต่อ BU
- **BU scoping** Role สามารถมอบให้ user ที่มี row `tb_user_tb_business_unit` ที่ active สำหรับ BU เดียวกันเท่านั้น (บังคับฝั่งแอปพลิเคชัน)
- **การ์ดการลบ** Hard-delete ถูกบล็อกถ้ามีการมอบหมายที่ active Soft-delete อนุญาต; การมอบหมายคงอยู่แต่ไม่มี permission ที่ grant
- **Cascade การ inactivate** `is_active = false` revoke permission ตอน re-evaluation ครั้งถัดไป; session ที่ cached อาจคงอยู่จนกว่าจะ refresh
- **Live ไม่ใช่ snapshot** การตรวจสอบ permission evaluate state join ปัจจุบัน — ไม่มี snapshot ฝั่งเอกสาร

## 7. การอ้างอิงข้าม

- [access-control/permission](/th/inventory/access-control/permission) — atom ที่ role รวบรวม
- [access-control/user](/th/inventory/access-control/user) — account ที่ role มอบให้
- [master-data/business-unit](/th/inventory/master-data/business-unit) — ทุก role เป็นเจ้าของโดย BU
- [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) — เงื่อนไขเบื้องต้นสำหรับการมอบหมาย role
- ทุกโมดูลธุรกรรม — ทุก auth check join ผ่านตารางเหล่านี้

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application_role` (บรรทัด 19), `tb_application_role_tb_permission` (บรรทัด 44), `tb_user_tb_application_role` (บรรทัด 606)
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/role/` (`role-form.tsx`, `permission-matrix.tsx`, `permission-picker.tsx`, `role-component.tsx`) สำหรับหน้าจอ role เอง; `../carmen-inventory-frontend-react/routes/system-admin/user/user-assigned-roles.tsx` สำหรับการมอบหมาย user↔role; permission key ของ route guard อยู่ที่ `constant/module-list.ts` / `constant/permissions.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1101-role.md` (แคตตาล็อก test-case แบบเอกสารเท่านั้น; ยังไม่มี Playwright spec อัตโนมัติ)
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`
