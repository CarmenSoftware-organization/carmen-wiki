---
title: ผู้ใช้ (User)
description: Account ผู้ใช้หลักพร้อมตาราง profile, password และ login-session — ตัวตนเบื้องหลังทุก audit column ในระบบ
published: true
date: 2026-05-17T07:28:28.000Z
tags: access-control, user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ผู้ใช้ (User)

> **At a Glance**
> **เจ้าของ:** Sysadmin (+ Security Officer สำหรับ credentials) &nbsp;·&nbsp; **ตาราง:** `tb_user` (+ `tb_user_profile`, `tb_password`, `tb_user_login_session`) &nbsp;·&nbsp; **ใช้โดย:** ทุก audit column `*_by_id` ในระบบ &nbsp;·&nbsp; เลเยอร์ตัวตน — เอนทิตีที่ถูก FK มากที่สุดในแพลตฟอร์ม

![ผู้ใช้ (User) screen](/assets/screenshots/access-control/user.png)

## 1. คืออะไรและใครใช้

เอนทิตี user คือ **เลเยอร์ตัวตน** สำหรับทั้งแพลตฟอร์ม ทุก row ธุรกรรมในทุก tenant พกพา `created_by_id` / `updated_by_id` / `deleted_by_id` ที่อ้างอิง row ที่นี่ ดังนั้นนี่คือเอนทิตีที่ถูก foreign-key มากที่สุดในระบบ มันยัง feed RBAC ([[access-control/application-role]]), การเข้าถึงต่อ BU ([[access-control/business-unit-user]]) และ scope ต่อ location ([[access-control/user-location]])

เอนทิตีแบ่งข้าม 4 ตาราง: `tb_user` (account), `tb_user_profile` (name/phone/bio), `tb_password` (bcrypt + expiry), `tb_user_login_session` (token) การแบ่งทำให้ hot path แคบ

**บำรุงรักษาโดย** Sysadmin (account) และ Security Officer (credentials/sessions) **อ่านโดย** ทุก API request (audit + auth)

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง account user | Platform admin → User Management → **New** | ตั้ง `tb_user` + `tb_password` เริ่มต้น |
| แก้ profile (firstname, phone) | Account → หน้าจอ Profile | User สามารถ self-edit |
| รีเซ็ตรหัสผ่าน | Security Officer → User → **Reset** | Insert `tb_password` ใหม่, inactivate ตัวเก่า |
| ปิดใช้ account | ตั้ง `is_active = false` | Login บล็อก; FK รักษาไว้ |
| บังคับ logout | ลบ row `tb_user_login_session` | หรือรอ `expired_on` lapse |
| Soft-delete user | ตั้ง `deleted_at` | FK target ยัง valid สำหรับ audit ประวัติศาสตร์ |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Username already exists" | ความเป็นหนึ่งเดียวระดับแอปบน user ที่ไม่ถูก delete | เลือก username อื่น |
| Login ถูก reject หลังรีเซ็ต | Row `tb_password` หลายตัวที่ active | ควรมีเพียงหนึ่งที่ `is_active = true` — clean up |
| "Must accept T&Cs" | `is_consent = false` | User ต้องยอมรับเพื่อปลดล็อก UI ธุรกรรม |
| ไม่สามารถ hard-delete user | FK audit อ้างอิง row | Inactivate หรือ soft-delete แทน |
| บังคับเปลี่ยนรหัสผ่าน | `expired_on` ผ่าน | User ตั้งรหัสผ่านใหม่ (rotate `tb_password`) |

## 4. กรณีพิเศษ

- **Platform role bypass** `super_admin` / `platform_admin` bypass tenant RBAC; `security_officer` จัดการ credentials; `integration_developer` มีอยู่สำหรับ service account
- **Online presence เป็น best-effort** `is_online` / `socket_id` เป็น cache ที่เขียนโดย realtime channel — **ไม่ใช่** authoritative สำหรับ security
- **ประวัติรหัสผ่าน** Row `tb_password` หลายตัวต่อ user — เพียงหนึ่งที่ `is_active = true`; hash ที่ rotate คงอยู่สำหรับการตรวจจับ replay
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
| `platform_role` | `enum_platform_role` | No | Default `user` Role แบบหยาบ platform-wide |
| `is_active` | `Boolean?` | Yes | Default `false` Account-enabled |
| `is_consent` | `Boolean?` | Yes | Default `false` การยอมรับ T&C |
| `socket_id` | `String?` | Yes | Socket id ที่ live (presence) |
| `is_online` | `Boolean` | No | Default `false` Cached presence |
| `consent_at` | `DateTime? @db.Timestamptz(6)` | Yes | เมื่อ user ยอมรับ T&C |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**`enum_platform_role`:** `super_admin`, `platform_admin`, `support_manager`, `support_staff`, `security_officer`, `integration_developer`, `user`

### 5.2 `tb_user_profile`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_user` |
| `firstname` / `middlename` / `lastname` | `String @db.VarChar(100)` | Mixed | Default `""` |
| `telephone` | `String? @db.VarChar(20)` | Yes | โทรศัพท์ |
| `bio` | `Json? @db.Json` | Yes | Default `{}` |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

### 5.3 `tb_password`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` / `user_id` | `String @db.Uuid` | No | Keys |
| `hash` | `String` | No | Bcrypt hash |
| `is_active` | `Boolean?` | Yes | Default `false` |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + '90 days'` |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

### 5.4 `tb_user_login_session`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` / `user_id` | `String @db.Uuid` | No | Keys |
| `token` | `String @db.VarChar` | No | Token string |
| `token_type` | `enum_token_type` | No | Default `access_token` |
| `expired_on` | `DateTime @db.Timestamptz(6)` | No | Default `now() + '1 day'` |

**Constraints:** `@@unique([token])` `enum_token_type`: `access_token`, `refresh_token`

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** ระดับแอป: `username` และ `email` unique globally ในกลุ่ม user ที่ไม่ถูก delete
- **การ์ดการลบ** User ที่ถูก audit FK อ้างอิงไม่สามารถ hard-delete — inactivate แทน
- **Consent** `is_consent = true` จำเป็นก่อนปลดล็อก UI ธุรกรรม
- **การ rotate รหัสผ่าน** Row `tb_password` หลายตัว, หนึ่งที่ `is_active = true` `expired_on` ผ่านบังคับ rotation
- **Session lifecycle** อายุสั้น; refresh ถูกลบตอน logout; การ reuse ตรวจจับได้ผ่าน `token` unique
- **Online presence** Cache เท่านั้น; ไม่ใช่ authoritative สำหรับการตัดสินใจด้าน security

## 7. การอ้างอิงข้าม

- [[access-control/application-role]] — RBAC join
- [[access-control/business-unit-user]] — การเข้าถึงต่อ BU
- [[access-control/user-location]] — scope ฝั่ง tenant ต่อ location
- [[access-control/permission]] — grant โดยอ้อมผ่าน role
- [[master-data/business-unit]] — ทุก BU audit โดย `tb_user`
- ทุกโมดูลธุรกรรม — ทุก audit column `*_by_id`

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user` (lines ~388-454), `tb_user_profile` (lines ~467-489), `tb_password` (lines ~303-321), `tb_user_login_session` (lines ~456-465), enums (lines ~561-580)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/account/` + platform admin user-management
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`
