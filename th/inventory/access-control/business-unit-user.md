---
title: ผู้ใช้ของหน่วยธุรกิจ (Business Unit User)
description: Pivot การเป็นสมาชิกต่อ business unit — ประกาศว่าผู้ใช้คนใดอาจเข้าถึง BU ใด พร้อมตาราง staging การเชิญชั่วคราว
published: true
date: 2026-05-19T23:55:00.000Z
tags: access-control, business-unit-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ผู้ใช้ของหน่วยธุรกิจ (Business Unit User)

> **At a Glance**
> **เจ้าของ:** Sysadmin / BU Admin &nbsp;·&nbsp; **ตาราง:** `tb_user_tb_business_unit` (+ `tb_temp_bu_user`) &nbsp;·&nbsp; **ใช้โดย:** ทุก request ที่ authenticate แล้ว (การ resolve BU) &nbsp;·&nbsp; Pivot การเข้าถึง multi-tenant — ประกาศว่าผู้ใช้คนใดอาจดำเนินงานภายใน BU ใด

## 1. คืออะไรและใครใช้

`business-unit-user` คือ **pivot การเข้าถึง multi-tenant**: ประกาศว่า [access-control/user](/th/inventory/access-control/user) ที่กำหนดได้รับอนุญาตให้ดำเนินงานภายใน [master-data/business-unit](/th/inventory/master-data/business-unit) ที่กำหนด และมอบ BU-level role แบบหยาบ (`admin` หรือ `user`) ถ้าไม่มี row ที่ active ที่นี่ user ไม่สามารถเห็น BU ใน BU selector ของตนเองไม่ว่าจะมี [access-control/application-role](/th/inventory/access-control/application-role) อะไรอยู่ใน BU นั้น เมื่อมี row user เข้า BU, JWT `x-app-id` resolve และ tenant RBAC เริ่มทำงาน

คู่ `tb_temp_bu_user` stage **การเชิญตาม email** ก่อนผู้รับสมัคร: BU id, email, role — consume เมื่อ user ยอมรับและ `tb_user` จริงมีอยู่

**บำรุงรักษาโดย** Sysadmin และ BU admin **อ่านโดย** ทุก request ที่ authenticate แล้ว

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| Grant การเข้าถึง BU ให้ user | หน้าจอ user-management ของ BU → **Add** | เลือก user, ตั้ง role (`user` หรือ `admin`) |
| เชิญ non-user ตาม email | BU user-management → **Invite** | เขียน `tb_temp_bu_user` + token `tb_shot_url` |
| เปลี่ยน BU default ของ user | BU switcher → เลือก BU → "Make default" | Flip `is_default` บนหนึ่ง row, unset others |
| Suspend การเข้าถึงโดยไม่ลบ | Toggle `is_active = false` | User เสีย access ตอน request ถัดไป; การมอบหมาย role รักษาไว้ |
| Revoke การเข้าถึงถาวร | Soft-delete row | Filter membership ต้องการ `deleted_at IS NULL` |
| Promote เป็น BU admin | แก้ row → ตั้ง `role = admin` | Grant อำนาจ admin BU-wide โดยไม่ต้องการ app role แยก |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| BU หายจาก switcher หลัง grant | Session ที่ cached | Refresh / re-login |
| "Email already invited" | Row `tb_temp_bu_user` ที่ pending มีอยู่ | ยกเลิก invite เก่าหรือรอการยอมรับ/หมดอายุ |
| Row หลายตัวที่ `is_default = true` | Invariant ของแอปพลิเคชันถูกละเมิด | รัน repair script; ควรอย่างมากที่สุดหนึ่งต่อ user |
| Link เชิญ 404 | Token หมดอายุใน `tb_shot_url` | ส่ง invitation ใหม่ |

## 4. กรณีพิเศษ

- **ไม่มีความเป็นหนึ่งเดียวบน `tb_temp_bu_user`** — การเชิญที่ pending หลายตัวสำหรับ (email, BU) เดียวกันอาจอยู่ร่วมกัน; แอปรับผิดชอบการ dedup
- **Role = `admin`** grant admin BU-wide (จัดการ role, เชิญ user) โดยไม่ต้องการ application role แยก
- **Cross-schema invite** `tb_temp_bu_user.business_unit_id` เก็บเป็น `VarChar(255)` เพราะ tenant ของผู้เชิญ/ผู้รับเชิญอาจ resolve แตกต่างกัน
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

### 5.2 `tb_temp_bu_user`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `business_unit_id` | `String @db.VarChar(255)` | No | BU id ปลายทาง (เก็บเป็น string สำหรับ resolve cross-tenant) |
| `email` | `String @db.VarChar(255)` | No | Email ที่เชิญ |
| `role` | `String @db.VarChar(50)` | No | Role ที่ตั้งใจ |
| `created_at` | `DateTime @db.Timestamptz(6)` | No | Default `now()` คู่กับ TTL สำหรับ invite ที่หมดอายุ |

**Constraints:** none คู่กับ token `tb_shot_url` ที่อายุสั้น

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** อย่างมากที่สุดหนึ่ง row `(user_id, business_unit_id)` ที่ active ต่อ user — การ re-invite toggle `is_active`
- **Invariant default BU** อย่างมากที่สุดหนึ่ง row ต่อ user ที่ `is_default = true` (บังคับโดยแอป)
- **Role semantics** `admin` = ความสามารถ admin BU-wide โดยไม่ต้องการ app role แยก; `user` = default พึ่งพาการมอบหมาย app-role
- **Lifecycle การเชิญ** `tb_temp_bu_user` + `tb_shot_url` = หนึ่งการเชิญ การยอมรับ upsert membership และลบ row staging
- **การ inactivation** `is_active = false` revoke access ตอน request ถัดไป; การมอบหมาย app-role ไม่ถูกแตะต้อง

## 7. การอ้างอิงข้าม

- [access-control/user](/th/inventory/access-control/user) — ฝั่ง user ของ membership
- [master-data/business-unit](/th/inventory/master-data/business-unit) — ฝั่ง BU
- [access-control/application-role](/th/inventory/access-control/application-role) — scope ตาม BU; การตรวจสอบเงื่อนไขเบื้องต้น
- ทุกโมดูลธุรกรรม — ทุก request resolve BU ที่ active ผ่านตารางนี้

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_tb_business_unit` (lines ~511-532), `tb_temp_bu_user` (lines ~548-554), `enum_user_business_unit_role` (lines ~582-585)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/cluster/`
