---
title: สิทธิ์การเข้าถึง (Access Control)
description: ผู้ใช้ บทบาท สิทธิ์ และการเข้าถึงหน่วยธุรกิจหลายหน่วย ตรวจสอบซ้ำ 2026-09-22 — tb_location_user (เปลี่ยนชื่อ), tb_user_invitation แทน tb_temp_bu_user, แก้ไขสิทธิ์ผู้ใช้ผ่าน PATCH /api/config/:bu_code/users/:user_id
published: true
date: '2026-09-23T01:30:00.000Z'
tags: access-control, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# สิทธิ์การเข้าถึง (Access Control)

> **At a Glance**
> **วัตถุประสงค์โมดูล:** Resolve "ผู้ใช้ X สามารถทำ action Y บน resource Z" สำหรับทุก request ธุรกรรม &nbsp;·&nbsp; **กลุ่มเป้าหมาย:** Sysadmin, Security Officer, BU Admin &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_user`, `tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_user_invitation` (+ `_business_unit`), `tb_department_user`, `tb_location_user` (เปลี่ยนชื่อจาก `tb_user_location` เมื่อ 2026-09-04) &nbsp;·&nbsp; **หน้าย่อย:** 6 &nbsp;·&nbsp; **ตรวจสอบซ้ำ 2026-09-22**

## การเปลี่ยนแปลงตั้งแต่ 2026-07-29 (ตรวจสอบแล้ว 2026-09-22)

| การเปลี่ยนแปลง | วันที่ | แหล่งที่มา | หน้า wiki |
|---|---|---|---|
| `tb_user_location` → `tb_location_user` (tenant) พร้อมกับ `tb_shelf` → `tb_location_shelf` | 2026-09-04 | tenant migration `20260904131500_rename_shelf_and_user_location`; BE `d49a81b34` | [user-location](/th/inventory/access-control/user-location) |
| แก้ไขสิทธิ์ผู้ใช้ได้ใน request เดียว: `GET` / `PATCH /api/config/:bu_code/users/:user_id` — role และ location เป็น `{ add[], remove[] }`, department เป็น `department_id` ค่าเดียว; response เป็น `UserDetail` เดียว (`user`, `application_roles[]`, `locations[]`, `department`) | 2026-09-04 / 2026-09-07 | BE `b9eb20818`, `9a91d7f32`, `671288897`; FE `a5038c84`, `39ae1bba`; Bruno `config/users/{GET-get-access,PATCH-patch-access}` | [user](/th/inventory/access-control/user), [user-location](/th/inventory/access-control/user-location), [department-user](/th/inventory/access-control/department-user) |
| Matrix ผู้ใช้ × role `GET /api/config/:bu_code/user-application-roles` (row `user_id`, `bu_role`, `is_active`, `is_bu_active`, `role_ids[]`; summary `roles[]`) — รองรับ Print / Export ของหน้า list ผู้ใช้ | 2026-08-20 | BE `7a2390f11`; FE `ae37df84` (`use-user-role-report.ts`) | [user](/th/inventory/access-control/user) |
| `GET /api/:bu_code/users` รวม `roles[]` ของผู้ใช้แต่ละคน | 2026-08-20 | BE `ae8d1cd1e` | [user](/th/inventory/access-control/user) |
| List ของ application-role คืน `permissions: { count }` (+ `audit`); detail คืนแคตตาล็อกสิทธิ์ทั้งหมดพร้อมทำเครื่องหมาย grant ของ role | 2026-09-07 | BE `d911ad988`, `8162d568c`; FE `3d339913` | [application-role](/th/inventory/access-control/application-role) |
| หน้าจอ role: สิทธิ์ระดับโมดูล (resource ที่ไม่มีจุด — มี 11 ตัว) ถูก picker ตัดทิ้ง และสิทธิ์ที่ soft-delete แล้วยังแสดงอยู่; แก้ไขแล้ว **Print** ของ role สร้างสรุป grant ต่อโมดูล | 2026-08-31 / 2026-08-20 | FE `bad71662`, `efdc52ba` | [application-role](/th/inventory/access-control/application-role), [permission](/th/inventory/access-control/permission) |
| Permission key ผี (`system_configuration.*`) ฝั่ง frontend ถูกแทนด้วย resource จริงใน `tb_permission`; `system_admin.query_dataset` ถูกลบออกจากแคตตาล็อก | 2026-09-21 | FE `b9e2de5f`, `91b2b274`, `02bfff7a`; BE `7bebddaa7` | [permission](/th/inventory/access-control/permission) |
| Permission resource `system_admin.period` → `system_admin.inventory_period` | 2026-09-16 | platform migration `20260916140000_rename_period_to_inventory_period` | [permission](/th/inventory/access-control/permission) |
| `tb_temp_bu_user` **ถูก drop**; การเชิญตอนนี้เป็น `tb_user_invitation` + `tb_user_invitation_business_unit` (scope ระดับ cluster ผูกกับ email สถานะ `pending/accepted/declined/revoked`) สร้างจาก Platform (`api-system/clusters/:cluster_id/invitations`) และตอบรับผ่าน `api/invitations/:token/accept` (หรือ `…/accept-with-signup` สำหรับ email ที่ยังไม่มีบัญชี); `/api/auth/invite-user` ถูกลบ ("invite flow ที่ไม่เคยใช้งานได้") | 2026-08-05 → 2026-08-08 | platform migrations `20260805000000_user_invitation`, `20260805100000_drop_temp_bu_user`; BE `7f93ce6ad`, `3592a420e`, `2945a4d04` | [business-unit-user](/th/inventory/access-control/business-unit-user) |
| `tb_user` เพิ่ม `email_verified_at`, `email_verification_token_hash`, `email_verification_expires_at`; ความไม่ซ้ำของ `email` / `username` ในบัญชีที่ยังใช้งานตอนนี้เป็น **partial unique index** สองตัว (`lower(email)` / `lower(username)` where `deleted_at IS NULL`) — Prisma `@@unique([username, deleted_at])` ถูก drop; auth เพิ่ม `signup-request`, `signup-token/verify`, `verify-email`, `resend-verification` | 2026-08-04 → 2026-08-08 | platform migrations `20260804000000_user_email_verification`, `20260806000000_user_active_identifier_unique`, `20260808100000_signup_verification` | [user](/th/inventory/access-control/user) |
| บล็อก licence ถูกถอดออกจาก `GET /api/user/profile` → `GET /api/license` | 2026-09-09 | BE `dc5623a05` | [user](/th/inventory/access-control/user) |
| การอ้างอิงเอนทิตีใน response ของ config/master ถูก serialise เป็น nested object (`business_unit: { id }` บน list ของ role; `department_users[].user: { id }`, `hod_users[].user: { id }` บน department) | 2026-09-17 | BE `5d64f5dfd`; FE `dbb93361`, `b55294b3` | [application-role](/th/inventory/access-control/application-role), [department-user](/th/inventory/access-control/department-user) |

![สิทธิ์การเข้าถึง (Access Control) screen](/screenshots/access-control/application-role.png)

![สิทธิ์การเข้าถึง (Access Control) detail screen](/screenshots/access-control/application-role-detail.png)

## 1. ภาพรวม

Access Control เป็นโมดูลร่มของ **ใครทำอะไรได้ที่ไหน** ผูกห้าเอนทิตีเป็น pipeline การอนุญาตเดียว [access-control/user](/th/inventory/access-control/user) คือตัวตน (account, profile, sessions — รหัสผ่านถูก externalize) [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) ประกาศว่าผู้ใช้สามารถเข้า business unit ใดได้บ้าง [access-control/application-role](/th/inventory/access-control/application-role) คือ bundle ที่ตั้งชื่อของ atom [access-control/permission](/th/inventory/access-control/permission) ที่มอบให้ผู้ใช้ภายใน BU [access-control/user-location](/th/inventory/access-control/user-location) แล้วจึงทำให้ scope ระดับ row ของผู้ใช้ภายใน tenant แคบลงเฉพาะ [master-data/location](/th/inventory/master-data/location) ที่ระบุ

ทุก action ธุรกรรมในระบบ — submit PR, อนุมัติ GRN, post inventory adjustment, รัน count — resolve ผ่าน pipeline นี้ คำถาม runtime "ผู้ใช้ X ทำ action Y บน resource Z ได้ไหม" decompose เป็น: X มี row `tb_user_tb_business_unit` ที่ active สำหรับ BU ที่ active หรือไม่; licence ของ BU รวม feature ที่ route นั้น map ถึงหรือไม่ (`LicenseInterceptor` ตั้งแต่ 2026-08); X ถือ `tb_application_role` ใน BU นั้นที่ชุด `tb_application_role_tb_permission` รวม `(Z, Y)` หรือไม่ — ตรวจเฉพาะ route ที่ประกาศ `@Permission` ดู [access-control/permission](/th/inventory/access-control/permission); และ (สำหรับ resource ที่ scope ตาม location) row ปลายทางอยู่ในชุด `tb_location_user` ของ X หรือไม่

เอนทิตีสี่ในห้าตัวอยู่ใน **platform schema** (แชร์ข้าม tenant — `tb_user`, `tb_user_profile`, `tb_user_login_session`, `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_user_invitation`, `tb_user_invitation_business_unit`, `enum_user_business_unit_role`, `enum_user_invitation_status`) ตัวที่ห้า — `tb_location_user` (เปลี่ยนชื่อจาก `tb_user_location` เมื่อ 2026-09-04) — อยู่ใน **tenant schema** เพราะ join ผู้ใช้กับ location ฝั่ง tenant; `tb_department_user` อยู่ฝั่ง tenant ด้วยเหตุผลเดียวกัน

## 2. กลุ่มเป้าหมาย

Sysadmin เป็นเจ้าของการตั้งค่าตั้งแต่ต้นจนจบ Security Officer ตรวจสอบ credentials, sessions และการมอบ role การเชิญผู้ใช้ระดับ BU อาจมอบหมายให้ BU admin (ผู้ใช้ที่มี `tb_user_tb_business_unit.role = admin`)

## 3. รายการเอนทิตี

| เอนทิตี | วัตถุประสงค์ | จัดการโดย |
| ------ | ------- | ---------- |
| [user](/th/inventory/access-control/user) | Account, profile และ login session — เลเยอร์ตัวตน (รหัสผ่านถูก externalize) | Sysadmin / Security Officer |
| [application-role](/th/inventory/access-control/application-role) | Role ที่ตั้งชื่อแล้ว scope ตาม BU + การ join role-permission และ user-role | Sysadmin |
| [permission](/th/inventory/access-control/permission) | แคตตาล็อกสิทธิ์ atomic `(resource, action)` | Sysadmin (จัดการโดย seed) |
| [business-unit-user](/th/inventory/access-control/business-unit-user) | Membership การเข้าถึงต่อ BU + การเชิญผ่าน email ที่ scope ระดับ cluster (`tb_user_invitation*` แทน `tb_temp_bu_user` ที่ถูก drop) | Platform / cluster admin (เชิญ), ผู้ใช้ (ตอบรับ) |
| [department-user](/th/inventory/access-control/department-user) | Membership ผู้ใช้กับแผนก + การกำหนด Head of Department (HOD) สำหรับ approval routing; ตอนนี้แก้ไขจากฝั่งผู้ใช้ได้ด้วยผ่าน `PATCH …/users/:user_id { department_id }` | Sysadmin / Product Admin |
| [user-location](/th/inventory/access-control/user-location) | Scope ฝั่ง tenant ต่อผู้ใช้ของ location (`tb_location_user`) | Sysadmin / BU Admin |

## 4. การพึ่งพาข้ามโมดูล

- **ทุกโมดูลธุรกรรม** ขึ้นอยู่กับ [access-control/user](/th/inventory/access-control/user), [access-control/application-role](/th/inventory/access-control/application-role), [access-control/permission](/th/inventory/access-control/permission) และ [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) — ทุก request ที่ authenticate แล้ว resolve ผ่าน chain นี้ก่อน logic เฉพาะโมดูลจะรัน การ list แต่ละโมดูลที่นี่จะแค่ซ้ำเอนทิตีสี่ตัวเดิม ดังนั้นกฎคือ: ทุก action ใน [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory](/th/inventory/inventory), [inventory-adjustment](/th/inventory/inventory-adjustment), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check), [costing](/th/inventory/costing), [vendor-pricelist](/th/inventory/vendor-pricelist), [product](/th/inventory/product) และ [recipe](/th/inventory/recipe) ถูก gate ด้วย RBAC
- [inventory](/th/inventory/inventory) ปรึกษา [access-control/user-location](/th/inventory/access-control/user-location) เพิ่มเติมสำหรับ filtering ระดับ row ของ list inventory และหน้าจอ movement
- [store-requisition](/th/inventory/store-requisition) ปรึกษา [access-control/user-location](/th/inventory/access-control/user-location) เพิ่มเติมสำหรับการออกที่ผูก location
- [physical-count](/th/inventory/physical-count) ปรึกษา [access-control/user-location](/th/inventory/access-control/user-location) เพิ่มเติมเพื่อให้ storekeeper เห็นและนับเฉพาะพื้นที่ของตนเอง
- [spot-check](/th/inventory/spot-check) ปรึกษา [access-control/user-location](/th/inventory/access-control/user-location) เพิ่มเติมด้วยเหตุผล scope เดียวกับ physical-count
- [master-data/business-unit](/th/inventory/master-data/business-unit) เป็น scope-anchor สำหรับ [access-control/application-role](/th/inventory/access-control/application-role) (ทุก role เป็นเจ้าของโดย BU) และ [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) (ทุก membership อ้างอิง BU)
- [master-data/location](/th/inventory/master-data/location) เป็น scope target ของ [access-control/user-location](/th/inventory/access-control/user-location)
- [reporting-audit](/th/inventory/reporting-audit) consume audit column และ event การเปลี่ยนแปลง role / membership ที่ surface โดยทุกเอนทิตีในร่มนี้

## 5. แหล่งข้อมูลอ้างอิง

- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user`, `tb_user_profile`, `tb_user_login_session`, `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_user_invitation`, `tb_user_invitation_business_unit` และ enum สนับสนุน `enum_token_type`, `enum_user_business_unit_role`, `enum_user_invitation_status` `tb_temp_bu_user` ถูก drop เมื่อ 2026-08-05 (`20260805100000_drop_temp_bu_user`) ไม่มี `enum_platform_role` แล้ว — ถูกลบไป 2026-06-10 แทนที่ด้วยระบบ relational `tb_platform_role` (ขอบเขตของ Carmen Platform admin — ดู [access-control/user](/th/inventory/access-control/user) หัวข้อ Edge Cases)
- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_location_user`, `tb_department_user`
- **Gateway:** `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/{config_users,config_user-application-roles,config_application-roles,config_permissions,config_department-users,config_locations-users,config_user-locations}/`, `apps/backend-gateway/src/application/{user,user-business-units,user-locations,invitations}/`, `apps/backend-gateway/src/platform/platform_cluster-invitations/`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/{users,user-application-roles,application-roles,permissions,department-user,locations-user,user-location}/`, `user-management/user/`
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — อธิบายว่า role-type ของ workflow-stage (requester / purchaser / approver / reviewer) ซ้อนบน application-role permission grant ที่ documented ที่นี่อย่างไร Frozen 2026-04-27; `enum_stage_role` จริงคือ `create / approve / purchase / issue / view_only` (ดู [system-config/workflow](/th/inventory/system-config/workflow))
- **Design spec:** `.specs/2026-05-16-master-config-design.md`
- **Plan:** `.specs/2026-05-16-master-config-plan.md`
