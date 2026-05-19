---
title: สิทธิ์การเข้าถึง (Access Control)
description: ผู้ใช้ บทบาท สิทธิ์ และการเข้าถึงหน่วยธุรกิจหลายหน่วย
published: true
date: 2026-05-17T12:00:00.000Z
tags: access-control, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# สิทธิ์การเข้าถึง (Access Control)

> **At a Glance**
> **วัตถุประสงค์โมดูล:** Resolve "ผู้ใช้ X สามารถทำ action Y บน resource Z" สำหรับทุก request ธุรกรรม &nbsp;·&nbsp; **กลุ่มเป้าหมาย:** Sysadmin, Security Officer, BU Admin &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_user`, `tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_user_location` &nbsp;·&nbsp; **หน้าย่อย:** 5

## 1. ภาพรวม

Access Control เป็นโมดูลร่มของ **ใครทำอะไรได้ที่ไหน** ผูกห้าเอนทิตีเป็น pipeline การอนุญาตเดียว [[access-control/user]] คือตัวตน (account, profile, password, sessions) [[access-control/business-unit-user]] ประกาศว่าผู้ใช้สามารถเข้า business unit ใดได้บ้าง [[access-control/application-role]] คือ bundle ที่ตั้งชื่อของ atom [[access-control/permission]] ที่มอบให้ผู้ใช้ภายใน BU [[access-control/user-location]] แล้วจึงทำให้ scope ระดับ row ของผู้ใช้ภายใน tenant แคบลงเฉพาะ [[master-data/location]] ที่ระบุ

ทุก action ธุรกรรมในระบบ — submit PR, อนุมัติ GRN, post inventory adjustment, รัน count — resolve ผ่าน pipeline นี้ คำถาม runtime "ผู้ใช้ X ทำ action Y บน resource Z ได้ไหม" decompose เป็น: X มี row `tb_user_tb_business_unit` ที่ active สำหรับ BU ที่ active หรือไม่; X ถือ `tb_application_role` ใน BU นั้นที่ชุด `tb_application_role_tb_permission` รวม `(Z, Y)` หรือไม่; และ (สำหรับ resource ที่ scope ตาม location) row ปลายทางอยู่ในชุด `tb_user_location` ของ X หรือไม่

เอนทิตีสี่ในห้าตัวอยู่ใน **platform schema** (แชร์ข้าม tenant — `tb_user`, `tb_user_profile`, `tb_password`, `tb_user_login_session`, `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_temp_bu_user`, `enum_user_business_unit_role`) ตัวที่ห้า — `tb_user_location` — อยู่ใน **tenant schema** เพราะ join ผู้ใช้กับ location ฝั่ง tenant

## 2. กลุ่มเป้าหมาย

Sysadmin เป็นเจ้าของการตั้งค่าตั้งแต่ต้นจนจบ Security Officer ตรวจสอบ credentials, sessions และการมอบ role การเชิญผู้ใช้ระดับ BU อาจมอบหมายให้ BU admin (ผู้ใช้ที่มี `tb_user_tb_business_unit.role = admin`)

## 3. รายการเอนทิตี

| เอนทิตี | วัตถุประสงค์ | จัดการโดย |
| ------ | ------- | ---------- |
| [user](./user.md) | Account, profile, password และ login session — เลเยอร์ตัวตน | Sysadmin / Security Officer |
| [application-role](./application-role.md) | Role ที่ตั้งชื่อแล้ว scope ตาม BU + การ join role-permission และ user-role | Sysadmin |
| [permission](./permission.md) | แคตตาล็อกสิทธิ์ atomic `(resource, action)` | Sysadmin (จัดการโดย seed) |
| [business-unit-user](./business-unit-user.md) | Membership การเข้าถึงต่อ BU + การ staging การเชิญผ่าน email | Sysadmin / BU Admin |
| [user-location](./user-location.md) | Scope ฝั่ง tenant ต่อผู้ใช้ของ location | Sysadmin / BU Admin |

## 4. การพึ่งพาข้ามโมดูล

- **ทุกโมดูลธุรกรรม** ขึ้นอยู่กับ [[access-control/user]], [[access-control/application-role]], [[access-control/permission]] และ [[access-control/business-unit-user]] — ทุก request ที่ authenticate แล้ว resolve ผ่าน chain นี้ก่อน logic เฉพาะโมดูลจะรัน การ list แต่ละโมดูลที่นี่จะแค่ซ้ำเอนทิตีสี่ตัวเดิม ดังนั้นกฎคือ: ทุก action ใน [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory]], [[inventory-adjustment]], [[physical-count]], [[spot-check]], [[costing]], [[vendor-pricelist]], [[product]] และ [[recipe]] ถูก gate ด้วย RBAC
- [[inventory]] ปรึกษา [[access-control/user-location]] เพิ่มเติมสำหรับ filtering ระดับ row ของ list inventory และหน้าจอ movement
- [[store-requisition]] ปรึกษา [[access-control/user-location]] เพิ่มเติมสำหรับการออกที่ผูก location
- [[physical-count]] ปรึกษา [[access-control/user-location]] เพิ่มเติมเพื่อให้ storekeeper เห็นและนับเฉพาะพื้นที่ของตนเอง
- [[spot-check]] ปรึกษา [[access-control/user-location]] เพิ่มเติมด้วยเหตุผล scope เดียวกับ physical-count
- [[master-data/business-unit]] เป็น scope-anchor สำหรับ [[access-control/application-role]] (ทุก role เป็นเจ้าของโดย BU) และ [[access-control/business-unit-user]] (ทุก membership อ้างอิง BU)
- [[master-data/location]] เป็น scope target ของ [[access-control/user-location]]
- [[reporting-audit]] consume audit column และ event การเปลี่ยนแปลง role / membership ที่ surface โดยทุกเอนทิตีในร่มนี้

## 5. แหล่งข้อมูลอ้างอิง

- **Prisma platform:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_user`, `tb_user_profile`, `tb_password`, `tb_user_login_session`, `tb_application_role`, `tb_application_role_tb_permission`, `tb_user_tb_application_role`, `tb_permission`, `tb_user_tb_business_unit`, `tb_temp_bu_user` และ enum สนับสนุน `enum_platform_role`, `enum_token_type`, `enum_user_business_unit_role`
- **Prisma tenant:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_user_location`
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — อธิบายว่า role-type ของ workflow-stage (requester / purchaser / approver / reviewer) ซ้อนบน application-role permission grant ที่ documented ที่นี่อย่างไร
- **Design spec:** `.specs/2026-05-16-master-config-design.md`
- **Plan:** `.specs/2026-05-16-master-config-plan.md`
