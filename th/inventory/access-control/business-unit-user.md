---
title: ผู้ใช้ของหน่วยธุรกิจ (Business Unit User)
description: Pivot การเป็นสมาชิกต่อ BU (tb_user_tb_business_unit) บวก flow การเชิญที่ scope ระดับ cluster (tb_user_invitation + _business_unit) ที่มาแทน tb_temp_bu_user ซึ่งถูก drop เมื่อ 2026-08-05; /api/auth/invite-user ถูกลบแล้ว
published: true
date: 2026-09-23T10:06:26.000Z
tags: access-control, business-unit-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# ผู้ใช้ของหน่วยธุรกิจ (Business Unit User)

> **At a Glance**
> **เจ้าของ:** Platform / cluster admin (เชิญ), ผู้ใช้ (ตอบรับ), Sysadmin (row membership) &nbsp;·&nbsp; **ตาราง:** `tb_user_tb_business_unit` (membership) + `tb_user_invitation` / `tb_user_invitation_business_unit` (การเชิญ — **มาแทน `tb_temp_bu_user` ที่ถูก drop เมื่อ 2026-08-05**) &nbsp;·&nbsp; **Endpoint:** `POST /api/business-units/default` (switch), `GET /api/business-units` (ปัจจุบัน), `api/invitations/{mine,:token,:token/accept,:token/accept-with-signup,:token/decline}`, Platform `api-system/clusters/:cluster_id/invitations` (create / list / revoke / resend) &nbsp;·&nbsp; **ใช้โดย:** ทุก request ที่ authenticate แล้ว (การ resolve BU) &nbsp;·&nbsp; Pivot การเข้าถึง multi-tenant — ประกาศว่าผู้ใช้คนใดอาจดำเนินงานภายใน BU ใด

![ผู้ใช้ของหน่วยธุรกิจ (Business Unit User) screen](/screenshots/access-control/business-unit-user.png)

## สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22)

ข้อค้นพบเมื่อ 2026-07-15 ("`tb_temp_bu_user` มีแค่ schema; `/api/auth/invite-user` ออก token ลงทะเบียนเปล่า ๆ") ล้าสมัยแล้วทั้งสองข้อ:

- **`tb_temp_bu_user` ถูก drop** (platform migration `20260805100000_drop_temp_bu_user`) และ **`/api/auth/invite-user` ถูกลบ** (BE `7f93ce6ad`, 2026-08-05, "remove the invite flow that never worked")
- **Flow การเชิญจริงมาแทน** (migration `20260805000000_user_invitation`; BE `3592a420e` 2026-08-05, `2945a4d04` 2026-08-08): `tb_user_invitation` คือข้อเสนอที่ scope ระดับ cluster และ **ผูกกับ email** (`cluster_id`, `email`, `token_hash`, `cluster_role`, `status` `pending|accepted|declined|revoked`, `invited_by_id`, `expires_at`, `accepted_at`/`accepted_user_id`, `declined_*`, `revoked_*`) พร้อม row `tb_user_invitation_business_unit` หนึ่งตัวต่อ BU ที่การเชิญมอบให้ (`business_unit_id`, `role` = `enum_user_business_unit_role`, `is_default`) partial unique index บังคับให้มีการเชิญ *pending* ได้หนึ่งรายการต่อ `(cluster, email)` — เป็น SQL เท่านั้น Prisma แสดงไม่ได้ `expired` ตั้งใจไม่เก็บเป็น status; derive จาก `expires_at`
- **ใครทำอะไร:** cluster admin สร้าง / list / revoke / resend จาก Platform (`api-system/clusters/:cluster_id/invitations`, `platform_cluster-invitations.controller.ts:74-266`, platform permission); ผู้รับอ่าน `GET api/invitations/:token` และ `GET api/invitations/mine` แล้วตอบด้วย `POST …/accept`, `POST …/accept-with-signup` (public — `@IgnoreGuards(KeycloakGuard)`, `invitations.controller.ts:107,206` — สำหรับ email ที่ยังไม่มีบัญชี) หรือ `POST …/decline` เมื่อ accept `user-invitation.service.ts` (micro-cluster) สร้าง cluster membership และ row `tb_user_tb_business_unit` หนึ่งตัวต่อ BU ที่เชิญ พร้อม `role` และ `is_default` ที่เชิญไว้ (`:480-500`, `:577-578`) ที่นั่งนับจาก pool ของ **cluster** (`v_business_unit_seat`, `SEAT_LIMIT_EXCEEDED`; การเชิญที่ pending รายงานคู่กับ `used`/`cap` ใน `GET /api/license` `seat.pending_invites`)
- ตาราง membership เองไม่เปลี่ยน; `admin` RBAC bypass ใน `PermissionGuard` ยังคงอยู่ ยังคง**ไม่มีหน้าจอ BU-membership admin CRUD ใน `carmen-inventory-frontend-react`** — grant/revoke และ UI การเชิญอยู่ใน Platform SPA (ดู Platform book)

## 1. คืออะไรและใครใช้

`business-unit-user` คือ **pivot การเข้าถึง multi-tenant**: ประกาศว่า [access-control/user](/th/inventory/access-control/user) ที่กำหนดได้รับอนุญาตให้ดำเนินงานภายใน [master-data/business-unit](/th/inventory/master-data/business-unit) ที่กำหนด และมอบ BU-level role แบบหยาบ (`admin` หรือ `user`) ถ้าไม่มี row ที่ active ที่นี่ user ไม่สามารถเห็น BU ใน BU selector ของตนเองไม่ว่าจะมี [access-control/application-role](/th/inventory/access-control/application-role) อะไรอยู่ใน BU นั้น เมื่อมี row user สามารถ switch เข้า BU ได้ (`POST /api/business-units/default`); backend จะ resolve grant ต่อ BU ของ user นั้นเข้าไปใน header `x-bu-datas` ที่ `PermissionGuard` ของ [access-control/permission](/th/inventory/access-control/permission) อ่านในทุก request ถัดไป (`x-app-id` เป็น header ที่ไม่เกี่ยวข้องกัน — มันระบุ *client application* ที่เรียกเข้ามา เทียบกับ allowlist แยกต่างหาก ไม่ใช่ BU หรือ user ที่ active; ดู [access-control/permission](/th/inventory/access-control/permission) หัวข้อ 1.1) ตั้งแต่ 2026-08 มีการตรวจสอบที่สามต่อ request: **licence** ของ BU ต้องรวม feature ของ route นั้น (`LicenseInterceptor`) ซึ่ง client อ่านจาก `GET /api/license` แทนที่จะอ่านจาก profile

Row ถูกสร้างได้สามทาง: จากการตอบรับการเชิญของ cluster (ทางปกติ ด้านบน), จากการจัดการ BU/user ของ Platform หรือจาก seed **บำรุงรักษาโดย** cluster admin (Platform) และ Sysadmin **อ่านโดย** ทุก request ที่ authenticate แล้ว

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| Grant การเข้าถึง BU ให้ user | ไม่มีหน้าจอใน `carmen-inventory-frontend-react` ที่ทำสิ่งนี้ | เชิญผู้ใช้ (ด้านล่าง) หรือใช้การจัดการ BU / user ของ Platform SPA; แอป inventory มีแค่มุมมอง self-service |
| เชิญคนใหม่ตาม email | Platform SPA → cluster → Invitations (`POST api-system/clusters/:cluster_id/invitations` พร้อม `email`, `cluster_role`, `business_units[{ business_unit_id, role, is_default }]`) | เขียน `tb_user_invitation` + `_business_unit`; ผู้รับได้ link ที่มี token; มี `resend` และ `DELETE` (revoke) |
| ตอบรับการเชิญ | Link → `GET api/invitations/:token` → `POST …/accept` (login อยู่) หรือ `…/accept-with-signup` (ยังไม่มีบัญชี — สร้างบัญชีและตอบรับในขั้นตอนเดียว) | สร้าง cluster membership และ row `tb_user_tb_business_unit` พร้อม `role` / `is_default` ที่เชิญไว้; `INVITATION_ADDRESS_CONFLICT` ถ้า login ด้วย email อื่น |
| ดูการเชิญที่ pending ของฉัน | `GET api/invitations/mine` | ผูกกับ email ของผู้เรียก |
| Switch BU ที่ active / ตั้ง default | BU switcher บน navbar (`components/navbar/bu-switcher.tsx`) → คลิก BU | เป็น action เดียว ไม่ใช่สองขั้นตอน — คลิกแล้วเรียก `POST /api/business-units/default` ทันทีและ flip `is_default` บน row ที่เลือก (optimistic UI update ใน `hooks/use-switch-bu.ts`); ไม่มี control "Make default" แยกต่างหาก |
| ดู BU membership ของตนเอง | `/profile` → ส่วน Business Units (`routes/profile/bu-section.tsx`) | มุมมองอ่านอย่างเดียว + upload logo/avatar ของ BU ที่ user เป็น admin; ไม่ใช่หน้าจอ grant membership |
| Suspend การเข้าถึงโดยไม่ลบ | Toggle `is_active = false` (ระดับ schema; ไม่มี admin UI ใน frontend นี้) | User เสีย access ตอน request ถัดไป; การมอบหมาย role รักษาไว้ |
| Revoke การเข้าถึงถาวร | Soft-delete row (ระดับ schema; ไม่มี admin UI ใน frontend นี้) | Filter membership ต้องการ `deleted_at IS NULL` |
| Promote เป็น BU admin | ตั้ง `role = admin` (ระดับ schema; ไม่มี admin UI ใน frontend นี้) | ยืนยันแล้วว่ามีนัยสำคัญเชิงพฤติกรรม: `PermissionGuard` ปฏิบัติต่อ `tb_user_tb_business_unit.role = admin` เป็น RBAC bypass เต็มรูปแบบ ("god-mode") สำหรับ BU นั้น — ดู [access-control/permission](/th/inventory/access-control/permission) |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| BU หายจาก switcher หลัง grant | Session ที่ cached | Refresh / re-login |
| การเชิญ pending ซ้ำสำหรับ `(cluster, email)` เดียวกัน | Partial unique index (SQL เท่านั้น) | Revoke หรือ resend รายการเดิมแทน |
| `INVITATION_ADDRESS_CONFLICT` | ตอบรับขณะ login ด้วยบัญชีที่ email ต่างจากที่ถูกเชิญ | Login ด้วย email ที่ถูกเชิญ หรือใช้ `accept-with-signup` |
| การเชิญแสดงว่าหมดอายุ | เลย `expires_at` แล้ว (derive ไม่ได้เก็บ) | Cluster admin → **Resend** |
| `SEAT_LIMIT_EXCEEDED` ตอนตอบรับ | Pool ที่นั่งของ cluster (`cap`) ถูกใช้หมดแล้ว โดยนับรวมการเชิญที่ pending | ซื้อที่นั่งเพิ่มหรือ revoke การเชิญที่ไม่ใช้ |
| Row หลายตัวที่ `is_default = true` | Invariant ของแอปพลิเคชันถูกละเมิด | รัน repair script; ควรอย่างมากที่สุดหนึ่งต่อ user |

## 4. กรณีพิเศษ

- **`tb_temp_bu_user` ไม่มีอยู่แล้ว** (drop เมื่อ 2026-08-05) invitation stage ที่มันถูกออกแบบมาตอนนี้คือ `tb_user_invitation` + `tb_user_invitation_business_unit` — scope ระดับ cluster แทนที่จะเป็นระดับ BU ดังนั้นการเชิญหนึ่งรายการมอบหลาย BU พร้อมกันได้และมี `cluster_role` ด้วย
- **การเชิญผูกกับ email ไม่ใช่ user** ดังนั้นเชิญ email ที่ยังไม่มีบัญชีได้; `accept-with-signup` สร้างบัญชีให้ allowlist `x-app-id` ยังใช้กับ route accept ที่เป็น public
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

### 5.2 `tb_user_invitation` (platform; มาแทน `tb_temp_bu_user` ที่ถูก drop)

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `cluster_id` | `String @db.Uuid` | No | Cluster ที่การเชิญสังกัด |
| `email` | `String @db.VarChar(255)` | No | Email ที่เชิญ (การเชิญผูกกับ email ไม่ใช่ user id) |
| `token_hash` | `String @db.VarChar` | No | Hash ของ token ใน link |
| `cluster_role` | `enum_cluster_user_role` | No | Default `user` Role ระดับ cluster ที่มอบให้ตอน accept |
| `status` | `enum_user_invitation_status` | No | `pending` (default), `accepted`, `declined`, `revoked` `expired` derive จาก `expires_at` |
| `invited_by_id` | `String @db.Uuid` | No | Admin ผู้เชิญ |
| `expires_at` | `DateTime @db.Timestamptz(6)` | No | วันหมดอายุของ link |
| `accepted_at` / `accepted_user_id`, `declined_at` / `declined_user_id`, `revoked_at` / `revoked_by_id` | — | Yes | Stamp ผลลัพธ์ |
| `doc_version` | `Int` | No | Default `0` |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** partial unique index "การเชิญ pending หนึ่งรายการต่อ `(cluster_id, email)`" อยู่ใน migration SQL เท่านั้น (`20260805000000_user_invitation`)

### 5.3 `tb_user_invitation_business_unit`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_invitation_id` | `String @db.Uuid` | No | การเชิญแม่ |
| `business_unit_id` | `String @db.Uuid` | No | BU ที่จะมอบให้ตอน accept |
| `role` | `enum_user_business_unit_role` | No | Default `user` กลายเป็น `tb_user_tb_business_unit.role` |
| `is_default` | `Boolean` | No | Default `false` กลายเป็น `tb_user_tb_business_unit.is_default` |
| `doc_version` + audit columns | — | Mixed | มาตรฐาน |

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** อย่างมากที่สุดหนึ่ง row `(user_id, business_unit_id)` ที่ active ต่อ user — การ re-invite toggle `is_active`
- **Invariant default BU** อย่างมากที่สุดหนึ่ง row ต่อ user ที่ `is_default = true` (บังคับโดยแอป — ยืนยันใน `hooks/use-switch-bu.ts` ซึ่ง flip `is_default` บนเป้าหมายและล้างที่อื่นโดยนัยตอน refetch)
- **Role semantics** `admin` = RBAC bypass BU-wide โดยไม่ต้องการ app role แยก (ยืนยันใน `PermissionGuard`); `user` = default พึ่งพาการมอบหมาย app-role
- **การเชิญพก grant ของ BU มาด้วย** `role` และ `is_default` ต่อ BU ถูกบันทึกตอนเชิญ (`tb_user_invitation_business_unit`) และ materialise เป็น `tb_user_tb_business_unit` ตอน accept; การเชิญ pending หนึ่งรายการต่อ `(cluster, email)`
- **ที่นั่งเป็น pool ของ cluster** การตอบรับถูกปฏิเสธด้วย `SEAT_LIMIT_EXCEEDED` เมื่อ `cap` ของ cluster ถึงขีดจำกัด; การเชิญที่ pending นับรวมด้วย
- **การ inactivation** `is_active = false` revoke access ตอน request ถัดไป; การมอบหมาย app-role ไม่ถูกแตะต้อง

## 7. การอ้างอิงข้าม

- [access-control/user](/th/inventory/access-control/user) — ฝั่ง user ของ membership
- [master-data/business-unit](/th/inventory/master-data/business-unit) — ฝั่ง BU
- [access-control/application-role](/th/inventory/access-control/application-role) — scope ตาม BU; การตรวจสอบเงื่อนไขเบื้องต้น
- [access-control/permission](/th/inventory/access-control/permission) — admin-role bypass ของ `PermissionGuard`
- ทุกโมดูลธุรกรรม — ทุก request resolve BU ที่ active ผ่านตารางนี้

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user_tb_business_unit`, `tb_user_invitation`, `tb_user_invitation_business_unit`, `enum_user_business_unit_role`, `enum_user_invitation_status`; migrations `20260805000000_user_invitation`, `20260805100000_drop_temp_bu_user`
- **Backend:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/invitations/invitations.controller.ts` (`mine` `:70`, `:token` `:106`, `accept` `:148`, `accept-with-signup` `:201`, `decline` `:257`); `apps/backend-gateway/src/platform/platform_cluster-invitations/` (`POST` `:74`, `GET` `:147`, `DELETE :id` `:202`, `POST :id/resend` `:266`); `apps/micro-cluster/src/cluster/user-invitation/user-invitation.service.ts`; `apps/backend-gateway/src/application/user-business-units/user-business-units.controller.ts` (`POST default`, `GET`, `PUT`, `PATCH`)
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/platform/cluster-invitations/`, `user-management/`
- **Frontend:** `../carmen-inventory-frontend-react/components/navbar/bu-switcher.tsx` + `hooks/use-switch-bu.ts` (switch/default); `../carmen-inventory-frontend-react/routes/profile/bu-section.tsx` (self-view) ไม่มีหน้าจอ BU-membership admin CRUD หรือหน้าจอการเชิญใน frontend นี้ — ดู Platform book
