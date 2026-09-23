---
title: ผู้ใช้ (User)
description: Account ผู้ใช้หลักพร้อมตาราง profile และ login-session — ตัวตนเบื้องหลังทุก audit column รหัสผ่านอยู่ใน Keycloak; email verification + partial unique index ตั้งแต่ 2026-08; แก้ไขสิทธิ์ผ่าน PATCH /api/config/:bu_code/users/:id
published: true
date: '2026-09-23T01:30:00.000Z'
tags: access-control, user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ผู้ใช้ (User)

> **At a Glance**
> **เจ้าของ:** Sysadmin (+ Security Officer สำหรับ sessions) &nbsp;·&nbsp; **ตาราง:** `tb_user` (+ `tb_user_profile`, `tb_user_login_session`) &nbsp;·&nbsp; **หน้าจอ admin:** `/system-admin/user` (list, Print / Export รายงาน user × role) และ `/system-admin/user/:id` (กำหนด role, location, department) — permission `system_admin.user.view`, licence `system_admin.user` &nbsp;·&nbsp; **Endpoint:** `GET api/:bu_code/users` (พร้อม `roles[]`), `GET`/`PATCH api/config/:bu_code/users/:user_id` (record สิทธิ์การเข้าถึงแบบ response เดียว), `GET api/config/:bu_code/user-application-roles` (matrix), `GET`/`PATCH /api/user/profile`, `GET /api/user/permission` &nbsp;·&nbsp; **ใช้โดย:** ทุก audit column `*_by_id` ในระบบ &nbsp;·&nbsp; **รหัสผ่านถูก externalize** (ตาราง `tb_password` ถูกตัดออก 2026-05-17); email verification อยู่บน `tb_user` ตั้งแต่ 2026-08-04

## สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22)

- **หน้าจอ user ของ admin เป็น request เดียวแล้ว** `GET /api/config/:bu_code/users/:user_id` (`configUser.getAccess`, `config_users.controller.ts:149`) คืน `UserDetail` — `user{ username, email, alias_name, is_active, firstname, middlename, lastname, telephone, avatar_url }`, `application_roles[{ id, application_role_id, application_role_name, application_role_description, assigned_at }]`, `locations[]`, `department{ id, name } | null` (BE `671288897`; FE `types/user.ts`) `PATCH` บน URL เดียวกัน (`configUser.patchAccess`, `:64`) รับ `{ application_role_id?: { add, remove }, location_id?: { add, remove }, department_id?: string }` และ apply role (platform) + location (tenant) + department ใน transaction เดียว (BE `b9eb20818`, `9a91d7f32`; FE `a5038c84`, `39ae1bba`) Error: `USER_ACCESS_NO_CHANGES`, `USER_ACCESS_ROLE_ADD_REMOVE_CONFLICT`, `USER_ACCESS_LOCATION_ADD_REMOVE_CONFLICT`, `USER_ACCESS_LOCATIONS_TO_ADD_NOT_FOUND`, `…_TO_REMOVE_NOT_FOUND`, `USER_ACCESS_LOCATION_WRITE_FAILED`, `USER_ACCESS_DEPARTMENT_NOT_FOUND`, `USER_ACCESS_DEPARTMENT_ALREADY_HOD` (`packages/error-catalog/src/catalog.ts:306-358`) Bruno: `config/users/{GET-get-access,PATCH-patch-access}-config-users.bru`
- **Print / Export บน list ผู้ใช้ใช้งานได้จริง** (FE `ae37df84`, 2026-08-20): `use-user-role-report.ts` อ่าน `GET /api/config/:bu_code/user-application-roles` สองครั้ง (ครั้งแรกเอา `paginate.total` แล้ว `perpage=total`) และ render matrix user × role — print แบบ A4 แนวนอนผ่าน iframe ที่ซ่อน หรือ CSV พร้อม UTF-8 BOM endpoint matrix (BE `7a2390f11`) คืน row `{ user_id, username, email, firstname, middlename, lastname, bu_role, is_active, is_bu_active, role_ids[] }` พร้อม `summary.roles[]` เป็นชุดคอลัมน์ (`config_user-application-roles/swagger/response.ts:77-152`; Bruno `config/user-application-roles/GET-find-matrix`) FE build ก่อนหน้าแสดง toast "Coming soon" (`8c16c424`); ถูกแทนที่ในวันเดียวกัน
- **`GET /api/user/profile` ไม่มี `business_unit[i].license` แล้ว** (BE `dc5623a05`, 2026-09-09, breaking) — ข้อมูล licence ย้ายไป `GET /api/license` profile ยังมี `config` JSON ของแต่ละ BU และ inventory period ปัจจุบันที่ status bar ของ footer อ่าน
- **คอลัมน์และความไม่ซ้ำของ `tb_user` เปลี่ยน** (platform migrations `20260804000000_user_email_verification`, `20260806000000_user_active_identifier_unique`): เพิ่ม `email_verified_at`, `email_verification_token_hash`, `email_verification_expires_at`; `@@unique([username, deleted_at])` ถูก drop แทนด้วย **partial** unique index สองตัว `user_email_active_u` บน `lower(email)` และ `user_username_active_u` บน `lower(username)` where `deleted_at IS NULL` — Prisma แสดง partial index ไม่ได้ schema จึงมีแค่ `@@index` ธรรมดาและ comment เตือนว่าอย่าอ่านเป็น "ไม่มีความไม่ซ้ำ" ความไม่ซ้ำตอนนี้ไม่สนตัวพิมพ์เล็ก-ใหญ่
- **Auth surface** (`apps/backend-gateway/src/auth/auth.controller.ts`): `login`, `logout`, `register`, `signup-request` (`AppIdGuard('auth.signup-request')` ส่ง link สมัคร), `signup-token/verify`, `verify-email`, `resend-verification`, `refresh-token`, `forgot-password`, `reset-password-with-token` **`invite-user` ถูกลบ** เมื่อ 2026-08-05 (`7f93ce6ad`, "remove the invite flow that never worked") — การเชิญคือ flow `tb_user_invitation` ที่ scope ระดับ cluster ซึ่ง documented ที่ [access-control/business-unit-user](/th/inventory/access-control/business-unit-user)
- `GET /api/user/:user_id/signature` (`user.getSignatureByUserId`, `user.controller.ts:602`) expose รูป signature ของผู้ใช้อื่นสำหรับเอกสารที่พิมพ์ (Bruno `user-management/user/GET-get-signature-by-user-id`); บล็อก signature ของเลเยอร์ print (`99c5708d3`) อ่านจากที่นี่
- บล็อก HOD ถูกถอดออกจากหน้าจอ user (`5684f93e`, 2026-09-04); membership แผนกแสดง/แก้ไขเป็น `LookupDepartment` ค่าเดียว (`user-assigned-departments.tsx`)

![ผู้ใช้ (User) screen](/screenshots/access-control/user.png)

![ผู้ใช้ (User) detail screen](/screenshots/access-control/user-detail.png)

## 1. คืออะไรและใครใช้

เอนทิตี user คือ **เลเยอร์ตัวตน** สำหรับทั้งแพลตฟอร์ม ทุก row ธุรกรรมในทุก tenant พกพา `created_by_id` / `updated_by_id` / `deleted_by_id` ที่อ้างอิง row ที่นี่ ดังนั้นนี่คือเอนทิตีที่ถูก foreign-key มากที่สุดในระบบ มันยัง feed RBAC ([access-control/application-role](/th/inventory/access-control/application-role)), การเข้าถึงต่อ BU ([access-control/business-unit-user](/th/inventory/access-control/business-unit-user)) และ scope ต่อ location ([access-control/user-location](/th/inventory/access-control/user-location))

เอนทิตีแบ่งข้าม 3 ตารางใน platform schema: `tb_user` (account), `tb_user_profile` (name/phone/bio/avatar), `tb_user_login_session` (token) การแบ่งทำให้ hot path แคบ ตาราง `tb_password` ถูกตัดออกเมื่อ 2026-05-17 — การเก็บและตรวจสอบรหัสผ่านตอนนี้อยู่ใน Keycloak (`auth.service.ts` เมธอด `changePassword` proxy ไปยัง Keycloak Account API) ซึ่งออก token ที่บันทึกใน `tb_user_login_session` ดังนั้น platform schema จึงไม่มี credential

**บำรุงรักษาโดย** Sysadmin (account) และ Security Officer (sessions) **อ่านโดย** ทุก API request (audit + การตรวจสอบ token) การรีเซ็ต / rotate รหัสผ่านจัดการโดย external identity provider

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้าง account user | **ไม่มีหน้าจอ create/invite ใน `carmen-inventory-frontend-react`** — ยืนยันจาก e2e test-case doc ของ repo นั้นเอง (`1102-user.md`: "โมดูลนี้ไม่มีหน้า create/invite ผู้ใช้ใหม่"); `/system-admin/user/:id` ทำแค่กำหนด role/department/location ให้ account ที่มีอยู่แล้ว | Account เข้ามาผ่านการเชิญของ cluster (`POST api-system/clusters/:cluster_id/invitations` จาก Platform ตอบรับที่ `POST api/invitations/:token/accept` หรือ `…/accept-with-signup`) หรือสมัครเอง (`POST /api/auth/signup-request` → `signup-token/verify` → `register`); `/api/auth/invite-user` ไม่มีอยู่แล้ว |
| กำหนด role / location / department ให้ผู้ใช้ | `/system-admin/user/:id` → **Edit** → ติ๊ก role (`user-assigned-roles.tsx`), ติ๊ก location (DataGrid `user-assigned-locations.tsx`), เลือกแผนก (`user-assigned-departments.tsx`) → Save | `PATCH /api/config/:bu_code/users/:user_id` เดียวที่ส่งเฉพาะ diff (`buildUserPatch`) |
| Print / export matrix user × role | `/system-admin/user` → **Print** / **Export** | `GET /api/config/:bu_code/user-application-roles`; print = A4 แนวนอนมี ✓ ต่อ role, export = CSV (Y / ว่าง) |
| แก้ profile (firstname, phone, avatar) | `/profile/setting` (`routes/profile/user-profile-setting.tsx`) | User self-edit; upload avatar / signature ก็อยู่ที่นี่ |
| เปลี่ยนรหัสผ่าน | `/profile/setting` → dialog Change Password (`change-password-dialog.tsx`) | Proxy ไปยัง **Keycloak** Account API (`keycloak-auth.change-password`) ซึ่ง validate รหัสผ่านปัจจุบัน; carmen platform schema ไม่เห็นเลย logout อัตโนมัติเมื่อสำเร็จ |
| ปิดใช้ account | ตั้ง `is_active = false` | Login บล็อกที่นี่แม้ Keycloak ยังออก token (server validate `is_active`) |
| บังคับ logout | ลบ row `tb_user_login_session` | หรือรอ `expired_on` lapse |
| Soft-delete user | ตั้ง `deleted_at` | FK target ยัง valid สำหรับ audit ประวัติศาสตร์ |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Username already exists" / "Email already exists" | Partial unique index บน `lower(username)` / `lower(email)` ในกลุ่ม user ที่ไม่ถูก delete (บังคับที่ DB ตั้งแต่ 2026-08-06 ไม่สนตัวพิมพ์) | เลือกค่าอื่น; account ที่ soft-delete แล้วไม่บล็อกการใช้ซ้ำ |
| Error `USER_ACCESS_*` บนหน้าจอ assign | ดูสถานะการ implement — add/remove ขัดกัน, location ไม่รู้จัก, แผนกมี HOD อยู่แล้ว ฯลฯ | Reload แล้ว submit ใหม่ |
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
| `socket_id` | `String?` | Yes | Socket id ที่ live (presence) (`is_online` ที่หน้านี้เวอร์ชันก่อนระบุไว้ ไม่มีบน model ที่ HEAD) |
| `consent_at` | `DateTime? @db.Timestamptz(6)` | Yes | เมื่อ user ยอมรับ T&C |
| `email_verified_at` | `DateTime? @db.Timestamptz(6)` | Yes | ตั้งโดย `POST /api/auth/verify-email` (เพิ่ม 2026-08-04) |
| `email_verification_token_hash` / `email_verification_expires_at` | `String? @db.VarChar` / `DateTime?` | Yes | Token ใช้ครั้งเดียวแบบ hash + วันหมดอายุสำหรับ link ยืนยัน / สมัคร; มี index (`user_email_verification_token_hash_idx`) |
| `doc_version` | `Int` | No | Default `0` Optimistic-lock version |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** index ธรรมดาบน `email` และ `username`; ความไม่ซ้ำบังคับด้วย partial unique index สองตัวที่มี**เฉพาะใน SQL** (`user_email_active_u`, `user_username_active_u` — `lower(col) WHERE deleted_at IS NULL`, migration `20260806000000_user_active_identifier_unique`) `is_online` ไม่มีอยู่ที่ HEAD (`schema.prisma` `model tb_user`) — หมายเหตุกรณีพิเศษด้านล่างเรื่อง cache presence หมายถึง `socket_id` เท่านั้น ไม่มีคอลัมน์ `platform_role` แล้ว — ดูหัวข้อกรณีพิเศษสำหรับระบบ relational ที่มาแทน

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

- **ความเป็นหนึ่งเดียว** ระดับ DB ตั้งแต่ 2026-08-06: `lower(username)` และ `lower(email)` unique ในกลุ่ม user ที่ไม่ถูก delete (partial index มองไม่เห็นใน Prisma)
- **การแก้ไขสิทธิ์เป็น atomic ต่อผู้ใช้** role, location และ department เปลี่ยนใน `PATCH` เดียว; การเขียน location ล้มเหลวหลังเขียน role จะ surface เป็น `USER_ACCESS_LOCATION_WRITE_FAILED`
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

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user`, `tb_user_profile`, `tb_user_login_session`; migrations `20260804000000_user_email_verification`, `20260806000000_user_active_identifier_unique`, `20260808100000_signup_verification` `tb_password` ถูกตัดออกใน commit `b2829da2` (2026-05-17); คอลัมน์ enum `platform_role` ถูกตัดออกใน commit `06d8a921` (2026-06-10) — ดูหัวข้อกรณีพิเศษ การเก็บและตรวจสอบ credential ตอนนี้อยู่ใน Keycloak
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/authen/auth/auth.service.ts` (`changePassword` — Keycloak Account API); gateway `apps/backend-gateway/src/auth/auth.controller.ts`, `apps/backend-gateway/src/application/user/user.controller.ts` (profile, permission, `api/:bu_code/users`, signature), `apps/backend-gateway/src/config/config_users/` (record สิทธิ์แบบ response เดียว + `PATCH`), `apps/backend-gateway/src/config/config_user-application-roles/` (matrix + CRUD role ต่อผู้ใช้)
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/users/`, `config/user-application-roles/GET-find-matrix-…`, `user-management/user/GET-get-signature-by-user-id-…`
- **Frontend:** `../carmen-inventory-frontend-react/routes/profile/` (self-service profile, avatar, signature, change-password, รายการ BU); `../carmen-inventory-frontend-react/routes/system-admin/user/` (`user-component.tsx` list + Print/Export, `user-edit.route.tsx` + `user-edit-content.tsx`, `user-assigned-form.tsx`, `user-assigned-roles.tsx`, `user-assigned-locations.tsx`, `user-assigned-departments.tsx`, `user-assigned-form-schema.ts`, `use-user-role-report.ts`); `types/user.ts` (`UserDetail`, `UpdateUserPayload`, `UserApplicationRole`); `hooks/use-license.ts` + `types/license.ts` สำหรับบล็อก licence ที่ย้ายออกจาก profile
- **E2E:** `../carmen-inventory-frontend-e2e/docs/test-cases/1102-user.md` (39 case แบบเอกสารเท่านั้น; ระบุชัดว่าไม่มีหน้า create/invite)
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md`
