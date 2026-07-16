---
title: ผู้ใช้ของหน่วยธุรกิจ (Business Unit User)
description: Pivot การเป็นสมาชิกต่อ business unit — ประกาศว่าผู้ใช้คนใดอาจเข้าถึง BU ใด พร้อมตาราง staging การเชิญที่ออกแบบไว้แต่ยังไม่ implement
published: true
date: 2026-07-15T23:46:09.000Z
tags: access-control, business-unit-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ผู้ใช้ของหน่วยธุรกิจ (Business Unit User)

> **At a Glance**
> **เจ้าของ:** Sysadmin / BU Admin &nbsp;·&nbsp; **ตาราง:** `tb_user_tb_business_unit` (+ `tb_temp_bu_user`) &nbsp;·&nbsp; **ใช้โดย:** ทุก request ที่ authenticate แล้ว (การ resolve BU) &nbsp;·&nbsp; Pivot การเข้าถึง multi-tenant — ประกาศว่าผู้ใช้คนใดอาจดำเนินงานภายใน BU ใด

## 1. คืออะไรและใครใช้

`business-unit-user` คือ **pivot การเข้าถึง multi-tenant**: ประกาศว่า [access-control/user](/th/inventory/access-control/user) ที่กำหนดได้รับอนุญาตให้ดำเนินงานภายใน [master-data/business-unit](/th/inventory/master-data/business-unit) ที่กำหนด และมอบ BU-level role แบบหยาบ (`admin` หรือ `user`) ถ้าไม่มี row ที่ active ที่นี่ user ไม่สามารถเห็น BU ใน BU selector ของตนเองไม่ว่าจะมี [access-control/application-role](/th/inventory/access-control/application-role) อะไรอยู่ใน BU นั้น เมื่อมี row user สามารถ switch เข้า BU ได้ (`POST /api/business-units/default`); backend จะ resolve grant ต่อ BU ของ user นั้นเข้าไปใน header `x-bu-datas` ที่ `PermissionGuard` ของ [access-control/permission](/th/inventory/access-control/permission) อ่านในทุก request ถัดไป (`x-app-id` เป็น header ที่ไม่เกี่ยวข้องกัน — มันระบุ *client application* ที่เรียกเข้ามา เทียบกับ allowlist แยกต่างหาก ไม่ใช่ BU หรือ user ที่ active; ดู [access-control/permission](/th/inventory/access-control/permission) หัวข้อ 1.1)

ตาราง `tb_temp_bu_user` ถูกออกแบบให้ stage **การเชิญตาม email** ก่อนผู้รับสมัคร (BU id, email, role) แต่ไม่มี backend code ใดสร้าง อ่าน หรือ consume มันในวันนี้ — ดูกรณีพิเศษ Flow การเชิญที่มีอยู่จริง (`/api/auth/invite-user`) ออกแค่ token ลงทะเบียนแบบทั่วไปของ platform โดยไม่ผูก BU หรือ role ใด ๆ

**บำรุงรักษาโดย** Sysadmin และ BU admin **อ่านโดย** ทุก request ที่ authenticate แล้ว

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| Grant การเข้าถึง BU ให้ user | ไม่มีหน้าจอใน `carmen-inventory-frontend-react` ที่ทำสิ่งนี้ | BU-membership admin CRUD (grant/revoke, ตั้ง `role` ต่อ BU) ไม่ถูก implement ใน frontend นี้; แอป inventory มีแค่มุมมอง self-service (ด้านล่าง) |
| เชิญคนใหม่ตาม email | `POST /api/auth/invite-user` (`{ "email": ... }`) — sign-up แบบทั่วไปของ platform ไม่ได้ surface เป็นหน้าจอ UI ใน frontend นี้ | สร้างแค่ token ลงทะเบียน `tb_shot_url`; **ไม่** เขียน `tb_temp_bu_user` หรือผูก BU/role เป้าหมายตอนเชิญ |
| Switch BU ที่ active / ตั้ง default | BU switcher บน navbar (`components/navbar/bu-switcher.tsx`) → คลิก BU | เป็น action เดียว ไม่ใช่สองขั้นตอน — คลิกแล้วเรียก `POST /api/business-units/default` ทันทีและ flip `is_default` บน row ที่เลือก (optimistic UI update ใน `hooks/use-switch-bu.ts`); ไม่มี control "Make default" แยกต่างหาก |
| ดู BU membership ของตนเอง | `/profile` → ส่วน Business Units (`routes/profile/bu-section.tsx`) | มุมมองอ่านอย่างเดียว + upload logo/avatar ของ BU ที่ user เป็น admin; ไม่ใช่หน้าจอ grant membership |
| Suspend การเข้าถึงโดยไม่ลบ | Toggle `is_active = false` (ระดับ schema; ไม่มี admin UI ใน frontend นี้) | User เสีย access ตอน request ถัดไป; การมอบหมาย role รักษาไว้ |
| Revoke การเข้าถึงถาวร | Soft-delete row (ระดับ schema; ไม่มี admin UI ใน frontend นี้) | Filter membership ต้องการ `deleted_at IS NULL` |
| Promote เป็น BU admin | ตั้ง `role = admin` (ระดับ schema; ไม่มี admin UI ใน frontend นี้) | ยืนยันแล้วว่ามีนัยสำคัญเชิงพฤติกรรม: `PermissionGuard` ปฏิบัติต่อ `tb_user_tb_business_unit.role = admin` เป็น RBAC bypass เต็มรูปแบบ ("god-mode") สำหรับ BU นั้น — ดู [access-control/permission](/th/inventory/access-control/permission) |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| BU หายจาก switcher หลัง grant | Session ที่ cached | Refresh / re-login |
| "User already exists" (409) ตอนเชิญ | `/api/auth/invite-user` พบ `tb_user` ที่มี email นั้นอยู่แล้ว (`auth.service.ts` `inviteUser`) | Grant การเข้าถึง BU ให้ user ที่มีอยู่แทนการเชิญซ้ำ |
| Row หลายตัวที่ `is_default = true` | Invariant ของแอปพลิเคชันถูกละเมิด | รัน repair script; ควรอย่างมากที่สุดหนึ่งต่อ user |
| Link เชิญ 404 | Token `tb_shot_url` หมดอายุ (`INVITATION_LIMIT_HOURS` default 1 ชั่วโมง) | ส่งใหม่ผ่าน `/api/auth/invite-user` |

## 4. กรณีพิเศษ

- **`tb_temp_bu_user` มีแค่ schema — ไม่มี code path เขียนหรืออ่านมัน** การค้นหาทั้ง repo ของ `carmen-turborepo-backend-v2` พบว่าไม่มีการอ้างอิง `tb_temp_bu_user` เลยนอกจาก Prisma schema เอง ตารางนี้จำลอง invitation stage ที่ scope ตาม BU (business_unit_id + email + role) ที่ถูกออกแบบไว้แต่ไม่เคย implement; endpoint การเชิญจริง (`/api/auth/invite-user`) สร้างแค่ token ลงทะเบียน `tb_shot_url` แบบทั่วไปโดยไม่ผูก BU หรือ role ถือฟิลด์ด้านล่างเป็น schema reference ไม่ใช่ flow ที่ใช้งานจริง
- **Role = `admin`** grant RBAC bypass BU-wide (ยืนยันผ่านการตรวจสอบ admin ของ `PermissionGuard`) โดยไม่ต้องการ application role แยก
- **Hard-delete อนุญาต** (ไม่มี FK target ธุรกรรม) แต่ soft-delete ถูกแนะนำเพื่อรักษา audit

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: platform schema

### 5.1 `tb_user_tb_business_unit`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_user` |
| `business_unit_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_business_unit` |
| `role` | `enum_user_business_unit_role` | No | Default `user` `admin` หรือ `user` |
| `is_default` | `Boolean?` | Yes | Default `false` Mark BU ที่ user landing |
| `is_active` | `Boolean?` | Yes | Default `true` ปิด access โดยไม่ unlink |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([user_id, business_unit_id, deleted_at])` FKs `onDelete: NoAction` `enum_user_business_unit_role`: `admin`, `user`

### 5.2 `tb_temp_bu_user` (มีแค่ schema — ไม่มี code อ้างอิง; ดูกรณีพิเศษ)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `business_unit_id` | `String @db.VarChar(255)` | No | BU id ปลายทาง (เก็บเป็น string สำหรับ resolve cross-tenant) |
| `email` | `String @db.VarChar(255)` | No | Email ที่เชิญ |
| `role` | `String @db.VarChar(50)` | No | Role ที่ตั้งใจ |
| `created_at` | `DateTime @db.Timestamptz(6)` | No | Default `now()` คู่กับ TTL สำหรับ invite ที่หมดอายุ |

**Constraints:** none ออกแบบให้คู่กับ token `tb_shot_url` ที่อายุสั้น แต่ไม่มี service ใดสร้าง อ่าน หรือ consume row ที่นี่ในวันนี้

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** อย่างมากที่สุดหนึ่ง row `(user_id, business_unit_id)` ที่ active ต่อ user — การ re-invite toggle `is_active`
- **Invariant default BU** อย่างมากที่สุดหนึ่ง row ต่อ user ที่ `is_default = true` (บังคับโดยแอป — ยืนยันใน `hooks/use-switch-bu.ts` ซึ่ง flip `is_default` บนเป้าหมายและล้างที่อื่นโดยนัยตอน refetch)
- **Role semantics** `admin` = RBAC bypass BU-wide โดยไม่ต้องการ app role แยก (ยืนยันใน `PermissionGuard`); `user` = default พึ่งพาการมอบหมาย app-role
- **Flow การเชิญจริงข้าม `tb_temp_bu_user` ไปเลย** `/api/auth/invite-user` รับแค่ email ตรวจว่ายังไม่เป็น `tb_user` และออก token ลงทะเบียน `tb_shot_url` — ไม่มี `business_unit_id` หรือ `role` ถูกบันทึกตอนเชิญ
- **การ inactivation** `is_active = false` revoke access ตอน request ถัดไป; การมอบหมาย app-role ไม่ถูกแตะต้อง

## 7. การอ้างอิงข้าม

- [access-control/user](/th/inventory/access-control/user) — ฝั่ง user ของ membership
- [master-data/business-unit](/th/inventory/master-data/business-unit) — ฝั่ง BU
- [access-control/application-role](/th/inventory/access-control/application-role) — scope ตาม BU; การตรวจสอบเงื่อนไขเบื้องต้น
- [access-control/permission](/th/inventory/access-control/permission) — admin-role bypass ของ `PermissionGuard`
- ทุกโมดูลธุรกรรม — ทุก request resolve BU ที่ active ผ่านตารางนี้

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_tb_business_unit` (บรรทัด 627), `tb_temp_bu_user` (บรรทัด 666), `enum_user_business_unit_role` (บรรทัด 691)
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (`inviteUser`, `changePassword`); `../carmen-turborepo-backend-v2/apps/backend-gateway/src/auth/auth.controller.ts` (`POST /api/auth/invite-user`)
- **Frontend:** `../carmen-inventory-frontend-react/components/navbar/bu-switcher.tsx` + `hooks/use-switch-bu.ts` (switch/default); `../carmen-inventory-frontend-react/routes/profile/bu-section.tsx` (self-view) ไม่มีหน้าจอ BU-membership admin CRUD ใน frontend นี้
