---
title: บทบาท (Application Role)
description: นิยาม role ต่อ business unit บวกตาราง join role→permission และ user→role — หัวใจของ tenant RBAC List คืนจำนวน permission, detail คืนแคตตาล็อกเต็ม; role print; แก้ picker สำหรับ permission ระดับโมดูล
published: true
date: '2026-09-23T01:30:00.000Z'
tags: access-control, application-role, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# บทบาท (Application Role)

> **At a Glance**
> **เจ้าของ:** Sysadmin (ต่อ BU) &nbsp;·&nbsp; **ตาราง:** `tb_application_role` (+ `tb_application_role_tb_permission`, `tb_user_tb_application_role`) &nbsp;·&nbsp; **หน้าจอ:** `/system-admin/role` (+ `/new`, `/:id`) — permission `system_admin.role.view`, licence `system_admin.role` &nbsp;·&nbsp; **Endpoint:** `api/config/:bu_code/application-roles` (`KeycloakGuard` เท่านั้น — **ไม่มี `AppIdGuard` และไม่มี `@Permission` บน route ทั้งห้า** ตรวจสอบซ้ำ 2026-09-22) &nbsp;·&nbsp; **ใช้โดย:** การตรวจสอบ permission ของทุกโมดูลธุรกรรม &nbsp;·&nbsp; Bundle ที่ตั้งชื่อแล้วของ permission ที่มอบให้ผู้ใช้ภายใน BU

## สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22)

- **แยก payload ของ list กับ detail (BE `d911ad988`, 2026-09-07)** `GET …/application-roles` คืน `permissions: { count }` ต่อ role บวก `audit` (`ApplicationRoleResponseDto`, `swagger/response.ts:38-66`); `GET …/application-roles/:id` คืน **แคตตาล็อก permission ทั้งหมด** พร้อมทำเครื่องหมาย grant ของ role (`ApplicationRoleDetailResponseDto`, `:91-105`) type ฝั่ง FE สะท้อนแบบเดียวกัน (`types/role.ts`: `Role.permissions: { count }`, `RoleDetail.permissions: RolePermission[]`; FE `3d339913`) ตั้งแต่รอบ serializer 2026-09-17 row ของ list มี `business_unit: { id }` แทน `business_unit_id` แบบ flat (BE `5d64f5dfd` — เฉพาะ list; DTO ของ detail ไม่มีฟิลด์นี้)
- **Payload สร้าง / แก้ไข:** `CreateRoleDto { name, description?, permissions: { add: string[] } }`, `UpdateRoleDto { …, doc_version, permissions: { add: string[], remove: string[] } }` (`types/role.ts:35-44`)
- **หน้าจอ role ถูกสร้างใหม่ (FE `aad79674`, 2026-08-20)** `permission-matrix.tsx` ถูกลบ; ฟอร์มตอนนี้เป็น `role-form.tsx` + `role-form-hero.tsx` + `permission-picker.tsx` (`permission-catalog.ts` จัดกลุ่มแคตตาล็อกเป็น category → resource → action; action เป็น Toggle pill, `4c28bcf0`) แก้บั๊ก picker สองจุดเมื่อ 2026-08-31 (`bad71662`): permission ที่ `resource` ไม่มีจุด — grant **ระดับโมดูล** `procurement`, `configuration`, `inventory_management`, `dashboard`, `report`, `system_admin`, … (11 ตัว) — ถูกข้ามด้วย `if (dot === -1) continue;` จึง grant จาก UI ไม่ได้เลย; และ permission ที่ soft-delete แล้วที่คืนมาพร้อม `audit.deleted` ยังถูก render อยู่ ตอนนี้ row ระดับโมดูลแสดงเป็นแถวแรกในแต่ละ category ในชื่อ "Module access" (`MODULE_RESOURCE_KEY`)
- **Print (FE `efdc52ba`, 2026-08-20)** `use-role-print.ts` render สรุป permission ที่ grant ต่อโมดูล (ลำดับและ label เดียวกับ picker) พร้อม header BU / printed-by / printed-at ผ่าน iframe ที่ซ่อนอยู่
- **Delete** มีให้ทั้งใน row ของ list และบน hero ของ detail ตรวจสอบ permission ทั้งสองจุด (`65751027`)

![บทบาท (Application Role) screen](/screenshots/access-control/application-role.png)

![บทบาท (Application Role) detail screen](/screenshots/access-control/application-role-detail.png)

## 1. คืออะไรและใครใช้

Application role คือ **bundle ที่ตั้งชื่อแล้วของ [access-control/permission](/th/inventory/access-control/permission)** ที่มอบให้ผู้ใช้ภายใน [master-data/business-unit](/th/inventory/master-data/business-unit) เป็นเลเยอร์การอนุญาตฝั่ง tenant แบบละเอียดที่ควบคุม *สิ่งที่ผู้ใช้แต่ละคนทำได้ในแต่ละ BU* แยกจาก role ระดับ platform (`tb_platform_role` ระบบ relational ที่ scope ตาม cluster แยกต่างหาก เป็นของ Carmen Platform admin — ดูหัวข้อกรณีพิเศษใน [access-control/user](/th/inventory/access-control/user); คอลัมน์ enum `tb_user.platform_role` เดิมที่ระบบนี้มาแทนถูกลบไปแล้วเมื่อ 2026-06-10) ทุก action UI ธุรกรรม — submit PR, อนุมัติ GRN, post adjustment — ถูก gate โดยการตรวจสอบว่า user ที่ active ถือ application role ที่รวม atom permission ที่ตรงกับ BU ที่ active หรือไม่

**บำรุงรักษาโดย** Sysadmin (ต่อ BU) **อ่านโดย** ทุก API endpoint ตอน request time

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง role สำหรับ BU | `/system-admin/role/new` → **Name**, Description + permission picker → Save | ไม่มี BU picker บนฟอร์มนี้ — role ถูกสร้างภายใน BU context ที่ active ของผู้เรียก; `POST …/application-roles { name, description, permissions: { add } }` |
| เพิ่ม permission ให้ role | Role edit → permission picker (`permission-picker.tsx`) | หนึ่ง row ต่อ resource พร้อม Toggle pill ต่อ action จริง; "Grant all" ต่อ category และ select-all ต่อ row; row ระดับโมดูล "Module access" อยู่แถวแรกของแต่ละ category |
| Print grant ของ role | Role detail → **Print** | `use-role-print.ts` — สรุป grant ต่อโมดูล header เอกสารสไตล์โรงแรม |
| มอบหมายผู้ใช้ให้ role | **ไม่ได้อยู่บนหน้าจอ Role** — ทำจาก `/system-admin/user/:id` → **Edit** → ติ๊ก role → Save (`PATCH /api/config/:bu_code/users/:user_id { application_role_id: { add, remove } }`) | หน้าจอ Role edit มีแค่ Name + Description + Permissions; ไม่มีแท็บ Users (ยืนยันจาก `role-form.tsx` และแคตตาล็อก test-case e2e `1101-role.md`) |
| ดูว่าใครถือ role ไหน | `/system-admin/user` → **Print** / **Export** | Matrix ผู้ใช้ × role จาก `GET /api/config/:bu_code/user-application-roles` |
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
- **การจัดการ role ถูก gate เฉพาะฝั่ง frontend** รายการ nav `/system-admin/role` gate ด้วย `PERMISSIONS.system_admin.role.view` (`constant/module-list.ts:691-695`; key `system_configuration.view` ที่เวอร์ชันก่อนอ้างถึงเป็น key ผี ถูกแทนที่เมื่อ 2026-09-21) และ `tb_permission` มี `system_admin.role.{view,create,update,delete}` — แต่ `config_application-roles.controller.ts` ไม่ตรวจสักตัว: route ทั้งห้าอยู่หลัง `KeycloakGuard` ระดับ class (`:59`) โดยไม่มี `AppIdGuard` และไม่มี decorator `@Permission` (`grep -c` = 0 ที่ HEAD) `config_user-application-roles` และ `config_permissions` ก็เป็นแบบเดียวกัน สมาชิก BU ที่ authenticate แล้วคนใดก็ตามที่ licence รวม `system_admin.role` สามารถสร้าง แก้ไข หรือลบ role ผ่าน API ได้ **ยังไม่ยืนยันว่าตั้งใจให้เป็นแบบนี้หรือไม่** — flag ไว้ ไม่ได้แก้

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

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`
- **Backend gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_application-roles/config_application-roles.controller.ts` (`GET` `:76`, `GET :id` `:140`, `POST` `:190`, `PUT :id` `:253`, `DELETE :id` `:320`; swagger `response.ts`), `config/config_user-application-roles/` (matrix `GET` `:80`, ต่อผู้ใช้ `GET :user_id`, `POST`, `PATCH`, `DELETE`); service `apps/micro-business/src/authen/role_permission/role_permission.service.ts`; serializer `apps/backend-gateway/src/common/dto/application-role/application-role.serializer.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/application-roles/`, `config/user-application-roles/`
- **Frontend:** `../carmen-inventory-frontend-react/routes/system-admin/role/` (`role.route.tsx`, `role-new.route.tsx`, `role-edit.route.tsx`, `role-component.tsx`, `role-form.tsx`, `role-form-hero.tsx`, `role-form-schema.ts`, `permission-picker.tsx`, `permission-catalog.ts`, `use-permission.ts`, `use-role-print.ts`, `use-role-table.tsx`) สำหรับหน้าจอ role เอง; `../carmen-inventory-frontend-react/routes/system-admin/user/user-assigned-roles.tsx` สำหรับการมอบหมาย user↔role; `types/role.ts`; nav key ใน `constant/module-list.ts:691-695` / `constant/permissions.ts` (`system_admin.role`)
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1101-role.md` (44 case แบบเอกสารเท่านั้น; ยังไม่มี Playwright spec อัตโนมัติ)
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`
