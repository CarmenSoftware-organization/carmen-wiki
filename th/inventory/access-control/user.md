---
title: ผู้ใช้ (User)
description: Account ผู้ใช้หลักพร้อมตาราง profile และ login-session — ตัวตนเบื้องหลังทุก audit column ในระบบ รหัสผ่านถูก externalize (ไม่มีตาราง tb_password)
published: true
date: 2026-07-15T23:46:09.000Z
tags: access-control, user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ผู้ใช้ (User)

> **At a Glance**
> **เจ้าของ:** Sysadmin (+ Security Officer สำหรับ sessions) &nbsp;·&nbsp; **ตาราง:** `tb_user` (+ `tb_user_profile`, `tb_user_login_session`) &nbsp;·&nbsp; **ใช้โดย:** ทุก audit column `*_by_id` ในระบบ &nbsp;·&nbsp; เลเยอร์ตัวตน — เอนทิตีที่ถูก FK มากที่สุดในแพลตฟอร์ม **รหัสผ่านถูก externalize** (ตาราง `tb_password` ถูกตัดออก 2026-05-17)

![ผู้ใช้ (User) screen](/screenshots/access-control/user.png)

![ผู้ใช้ (User) detail screen](/screenshots/access-control/user-detail.png)

## 1. คืออะไรและใครใช้

เอนทิตี user คือ **เลเยอร์ตัวตน** สำหรับทั้งแพลตฟอร์ม ทุก row ธุรกรรมในทุก tenant พกพา `created_by_id` / `updated_by_id` / `deleted_by_id` ที่อ้างอิง row ที่นี่ ดังนั้นนี่คือเอนทิตีที่ถูก foreign-key มากที่สุดในระบบ มันยัง feed RBAC ([access-control/application-role](/th/inventory/access-control/application-role)), การเข้าถึงต่อ BU ([access-control/business-unit-user](/th/inventory/access-control/business-unit-user)) และ scope ต่อ location ([access-control/user-location](/th/inventory/access-control/user-location))

เอนทิตีแบ่งข้าม 3 ตารางใน platform schema: `tb_user` (account), `tb_user_profile` (name/phone/bio/avatar), `tb_user_login_session` (token) การแบ่งทำให้ hot path แคบ ตาราง `tb_password` ถูกตัดออกเมื่อ 2026-05-17 — การเก็บและตรวจสอบรหัสผ่านตอนนี้อยู่ใน Keycloak (`auth.service.ts` เมธอด `changePassword` proxy ไปยัง Keycloak Account API) ซึ่งออก token ที่บันทึกใน `tb_user_login_session` ดังนั้น platform schema จึงไม่มี credential

**บำรุงรักษาโดย** Sysadmin (account) และ Security Officer (sessions) **อ่านโดย** ทุก API request (audit + การตรวจสอบ token) การรีเซ็ต / rotate รหัสผ่านจัดการโดย external identity provider

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง account user | **ไม่มีหน้าจอ create/invite ใน `carmen-inventory-frontend-react`** — ยืนยันจาก e2e test-case doc ของ repo นั้นเอง (`1102-user.md`: "โมดูลนี้ไม่มีหน้า create/invite ผู้ใช้ใหม่"); `/system-admin/user/:id` ทำแค่กำหนด role/department/location ให้ account ที่มีอยู่แล้ว | การสร้าง account เกิดผ่าน `/api/auth/invite-user` (คำเชิญลงทะเบียนด้วย email เท่านั้น) หรือ platform admin นอกหน้าจอนี้ |
| แก้ profile (firstname, phone, avatar) | `/profile/setting` (`routes/profile/user-profile-setting.tsx`) | User self-edit; upload avatar / signature ก็อยู่ที่นี่ |
| เปลี่ยนรหัสผ่าน | `/profile/setting` → dialog Change Password (`change-password-dialog.tsx`) | Proxy ไปยัง **Keycloak** Account API (`keycloak-auth.change-password`) ซึ่ง validate รหัสผ่านปัจจุบัน; carmen platform schema ไม่เห็นเลย logout อัตโนมัติเมื่อสำเร็จ |
| ปิดใช้ account | ตั้ง `is_active = false` | Login บล็อกที่นี่แม้ Keycloak ยังออก token (server validate `is_active`) |
| บังคับ logout | ลบ row `tb_user_login_session` | หรือรอ `expired_on` lapse |
| Soft-delete user | ตั้ง `deleted_at` | FK target ยัง valid สำหรับ audit ประวัติศาสตร์ |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Username already exists" | ความเป็นหนึ่งเดียวระดับแอปบน user ที่ไม่ถูก delete | เลือก username อื่น |
| Login ถูก reject แบบไม่คาดคิด | External identity provider reject credential หรือคืน subject ที่ไม่ได้ map | ตรวจสอบที่ IdP; platform schema ไม่ได้เก็บ state รหัสผ่านอีกแล้ว |
| "Must accept T&Cs" | `is_consent = false` | User ต้องยอมรับเพื่อปลดล็อก UI ธุรกรรม |
| ไม่สามารถ hard-delete user | FK audit อ้างอิง row | Inactivate หรือ soft-delete แทน |
| บังคับเปลี่ยนรหัสผ่าน | ขับเคลื่อนโดยนโยบาย rotation ของ external IdP | จัดการนอก schema นี้ |

## 4. กรณีพิเศษ

- **คอลัมน์ enum `platform_role` ไม่มีอยู่แล้ว** ถูกลบไป 2026-06-10 (`06d8a921` "remove legacy platform_role column and API surface") พร้อมกับฟิลด์ใน login response (`433b5e77`) Role ระดับ platform ตอนนี้เป็นระบบ RBAC แบบ relational ที่ scope ตาม cluster — `tb_platform_role` (role ที่ตั้งชื่อ) + `tb_platform_role_tb_permission` (bundle) + `tb_user_tb_platform_role` (assignment; `cluster_id = null` หมายถึง platform-wide, ถ้าตั้งค่าจะ scope เฉพาะ cluster นั้น) — พร้อมแคตตาล็อก `tb_platform_permission` ของตัวเอง แยกจาก `tb_permission` ฝั่ง tenant ที่หน้านี้ documented การจัดการ platform role/cluster เป็นขอบเขตของ Carmen Platform admin (ดู Platform book) ไม่ใช่ record `tb_user` ของ inventory frontend นี้
- **Online presence เป็น best-effort** `is_online` / `socket_id` เป็น cache ที่เขียนโดย realtime channel — **ไม่ใช่** authoritative สำหรับ security
- **ไม่มีประวัติรหัสผ่านฝั่งนี้** hash เก่า / นโยบาย rotation อยู่ใน external identity provider Platform schema ของ carmen เห็นเพียง token ที่ออกใน `tb_user_login_session`
- **ความเป็นหนึ่งเดียวของ session** `token` unique globally ดังนั้นการ reuse token ตรวจจับได้

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: platform schema

### 5.1 `tb_user`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key Target ของทุก FK `*_by_id` |
| `username` | `String @db.VarChar` | No | Username สำหรับ login |
| `email` | `String @db.VarChar` | No | Email สำหรับ login / contact |
| `alias_name` | `String? @db.VarChar` | Yes | Alias สำหรับแสดงแบบ optional |
| `is_active` | `Boolean?` | Yes | Default `false` Account-enabled |
| `is_consent` | `Boolean?` | Yes | Default `false` การยอมรับ T&C |
| `socket_id` | `String?` | Yes | Socket id ที่ live (presence) |
| `is_online` | `Boolean` | No | Default `false` Cached presence |
| `consent_at` | `DateTime? @db.Timestamptz(6)` | Yes | เมื่อ user ยอมรับ T&C |
| `doc_version` | `Int` | No | Default `0` Optimistic-lock version |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

ไม่มีคอลัมน์ `platform_role` แล้ว — ดูหัวข้อกรณีพิเศษสำหรับระบบ relational ที่มาแทน

### 5.2 `tb_user_profile`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_user` |
| `firstname` / `middlename` / `lastname` | `String @db.VarChar(100)` | Mixed | Default `""` |
| `telephone` | `String? @db.VarChar(20)` | Yes | โทรศัพท์ |
| `bio` | `Json? @db.Json` | Yes | Default `{}` |
| `avatar_file_token` | `String? @db.VarChar` | Yes | Reference ไปยังรูป avatar ของผู้ใช้ใน file service ของ platform (เพิ่ม 2026-05-20) รูปแบบ `file_token` เดียวกับ `tb_business_unit.logo_file_token` และ `tb_product_image.file_token` |
| `signature_file_token` | `String? @db.VarChar` | Yes | Reference ไปยังรูป signature ที่ผู้ใช้ upload; แสดงที่ dialog Signature ใน `/profile/setting` และแสดงแบบ read-only ที่ `/profile` |
| `doc_version` | `Int` | No | Default `0` Optimistic-lock version |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

### 5.3 `tb_user_login_session`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` / `user_id` | `String @db.Uuid` | No | Keys |
| `token` | `String @db.VarChar` | No | Token string |
| `token_type` | `enum_token_type` | No | Default `access_token` |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + '1 day'` |
| `doc_version` | `Int` | No | Default `0` Optimistic-lock version |

**Constraints:** `@@unique([token])` `enum_token_type`: `access_token`, `refresh_token`

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** ระดับแอป: `username` และ `email` unique globally ในกลุ่ม user ที่ไม่ถูก delete
- **การ์ดการลบ** User ที่ถูก audit FK อ้างอิงไม่สามารถ hard-delete — inactivate แทน
- **Consent** `is_consent = true` จำเป็นก่อนปลดล็อก UI ธุรกรรม
- **การ rotate รหัสผ่าน** เป็นของ external identity provider — ไม่มี row ฝั่ง carmen platform
- **Session lifecycle** อายุสั้น; refresh ถูกลบตอน logout; การ reuse ตรวจจับได้ผ่าน `token` unique
- **Online presence** Cache เท่านั้น; ไม่ใช่ authoritative สำหรับการตัดสินใจด้าน security

## 7. การอ้างอิงข้าม

- [access-control/application-role](/th/inventory/access-control/application-role) — RBAC join
- [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) — การเข้าถึงต่อ BU
- [access-control/user-location](/th/inventory/access-control/user-location) — scope ฝั่ง tenant ต่อ location
- [access-control/permission](/th/inventory/access-control/permission) — grant โดยอ้อมผ่าน role
- [master-data/business-unit](/th/inventory/master-data/business-unit) — ทุก BU audit โดย `tb_user`
- ทุกโมดูลธุรกรรม — ทุก audit column `*_by_id`

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user` (บรรทัด 494), `tb_user_profile` (บรรทัด 579), `tb_user_login_session` (บรรทัด 567) `tb_password` ถูกตัดออกใน commit `b2829da2` (2026-05-17); คอลัมน์ enum `platform_role` ถูกตัดออกใน commit `06d8a921` (2026-06-10) — ดูหัวข้อกรณีพิเศษ การเก็บและตรวจสอบ credential ตอนนี้อยู่ใน Keycloak
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (`changePassword` — Keycloak Account API)
- **Frontend:** `../carmen-inventory-frontend-react/routes/profile/` (self-service profile, avatar, signature, change-password, รายการ BU); `../carmen-inventory-frontend-react/routes/system-admin/user/` (admin: กำหนด role/department/location ให้ user ที่มีอยู่แล้ว — ไม่มีหน้าจอ create/invite)
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1102-user.md` (แคตตาล็อก test-case แบบเอกสารเท่านั้น; ระบุชัดว่าไม่มีหน้า create/invite)
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`
