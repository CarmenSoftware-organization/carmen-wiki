---
title: ผู้ใช้ (Users)
description: บัญชีผู้ใช้ระดับแพลตฟอร์ม — identity, ฟิลด์ `platform_role` ที่ใช้ขับเคลื่อน role gate ทุกที่ และการ assign cluster/BU ที่กำหนดขอบเขตว่าผู้ใช้เข้าถึงอะไรได้ใน inventory app
published: true
date: 2026-05-19T12:00:00.000Z
tags: platform/users, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# ผู้ใช้ (Users)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** หน้าจัดการบัญชีผู้ใช้ระดับแพลตฟอร์ม — หนึ่ง row ต่อหนึ่งคนที่ login ได้ เก็บ identity (`username`, `email`, ชื่อแบ่งส่วน, `alias_name`), ค่า `platform_role` เดียวที่ array `allowedRoles` ของทุกโมดูลอื่นใช้ตรวจสอบ, flag `is_active` และมุมมอง read-only ของ cluster และ BU ที่ผู้ใช้ถูก assign อยู่ (การ assign จริงทำจากฝั่ง cluster หรือ — สำหรับ BU — จาก dialog Add-BU ในหน้านี้) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** ผู้ใช้แพลตฟอร์มที่ login แล้วทุกคน — รูปแบบ open-access เดียวกับ Business Units; ทั้งวิศวกร support ของ Carmen และ admin ฝั่งลูกค้าใช้หน้านี้ &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `user` (ฟิลด์ในฟอร์ม 8 ตัว: `username`, `email`, `platform_role`, `alias_name`, `firstname`, `middlename`, `lastname`, `is_active`; พร้อม soft-delete trio `deleted_at`/`deleted_by_name` และ timestamp), `tb_cluster_user` (M:N join กับ cluster — อ่านอย่างเดียวที่นี่), BU-user join (M:N join กับ BU พร้อม `role` ระดับ BU เป็น `admin`/`user` และ flag `is_default`) &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูล Users เปิดเผย aggregate ของ user ระดับแพลตฟอร์มผ่านรูปแบบสองหน้าจอ
มาตรฐานเดียวกับที่ใช้ในทุกที่ใน Platform SPA:

- **`/users` → `UserManagement`** — `DataTable` แบบ server-side พร้อม
  การค้นหาแบบ debounce, แผง filter แบบ Sheet (เลือก Role หลายค่าได้จาก
  ค่าคงที่ `PLATFORM_ROLES` 7 ค่า, สถานะ Active/Inactive,
  "show soft-deleted"), ส่งออก CSV, จดจำสถานะ UI ใน `localStorage`
  (search, page, perpage, sort, role/status filter, toggle show-deleted)
  พร้อมปุ่ม header สองตัวที่มีเฉพาะในโมดูลนี้: **Fetch Keycloak** (เรียก
  `userService.fetchKeycloakUsers()` เพื่อดึง user list ปัจจุบันจาก
  Keycloak เข้ามาที่ DB ของแพลตฟอร์ม) และปุ่ม **Add User** มาตรฐาน
- **`/users/new` → `UserEdit` (โหมด create)** — การ์ด "User Details"
  เดียวที่มีฟอร์ม 8 ฟิลด์ เมื่อสร้างสำเร็จ หน้าจะ
  `navigate(..., { replace: true })` ไป route edit ของ id ที่เพิ่งสร้าง
- **`/users/:id/edit` → `UserEdit` (โหมด view/edit)** — การ์ดสามใบ
  วางเรียงกันลงล่าง การ์ด **User Details** เริ่มต้นแบบดูอย่างเดียวและ
  เปลี่ยนเป็นแก้ไขผ่านปุ่ม Edit (ในโหมดแก้ไข `username` จะ disable —
  ตั้งค่าได้ตอนสร้างเท่านั้น) การ์ด **Clusters** แสดงข้อมูลแบบ
  read-only จาก `tb_cluster_user`: การ์ดย่อยแต่ละใบแสดงชื่อ/code ของ
  cluster, badge active/inactive และ role ระดับ cluster (`admin` หรือ
  `user`) การ์ด **Business Units** แสดง row ของ BU-user join พร้อม role
  ระดับ BU, badge `is_default` และไอคอนถังขยะสำหรับลบ พร้อม dialog
  **Add BU** ของตัวเอง ซึ่ง BU ที่เลือกได้จะถูกจำกัดเฉพาะ cluster ที่
  user ถูก assign อยู่แล้ว

header บนหน้า edit ยังเปิดเผยปุ่ม **Change Password** (admin-initiated
password reset ผ่าน `userService.resetPassword` มี dialog ให้ยืนยัน
สองครั้ง) ส่วนหน้า list มี dialog hard-delete ที่บังคับให้ operator
พิมพ์ username/email เพื่อยืนยัน

## 2. บริบททางธุรกิจ

ตาราง user คือ source of truth ของแพลตฟอร์มสำหรับ "คนนี้ login ได้"
ฟิลด์ `platform_role` คือค่าเดียวที่ทุก array `allowedRoles` ใน SPA
ตรวจสอบ — clusters และ report templates จำกัดเฉพาะ
`platform_admin`/`support_manager`/`support_staff`, business units และ
users เองเปิดให้ทุก authenticated role และ inventory app อ่านค่าเดียวกัน
นี้เพื่อตัดสินใจว่าคน ๆ นี้เป็น operator ภายในของ Carmen หรือ user
ฝั่งลูกค้า เนื่องจาก field เดียวขับเคลื่อน gate ปลายน้ำมากมายขนาดนี้
การตั้งค่าให้ถูกต้องตอน create user จึงเป็นการตัดสินใจที่สำคัญที่สุดบน
หน้านี้

นอกจาก platform role แล้ว ตาราง user ยังบันทึก **ที่ไหน** ที่ user
ทำงานได้ การเป็นสมาชิก cluster เก็บใน `tb_cluster_user` และถูกแก้ไข
จากหน้า edit cluster (cross-link ใน Section 5) โมดูล Users แสดงผลลัพธ์
แบบ read-only เป็นการ์ด Clusters บนหน้า edit ส่วนการเป็นสมาชิก BU
ทำงานต่อ cluster — dialog **Add BU** บนหน้านี้จะแสดงเฉพาะ BU ที่
`cluster_id` ตรงกับ cluster ที่ user เป็นสมาชิกอยู่แล้ว เพื่อรักษาขอบ
เขต tenant ให้สะอาด: user ถูก assign ให้ BU นอก cluster ที่ตนเองสังกัด
ไม่ได้ ส่วน BU-user join ก็มี `role` ของตัวเอง (`admin` หรือ `user`
เป็นอิสระจาก `platform_role`) และ flag `is_default` ที่บอกว่า BU ตัวไหน
จะเป็น BU ที่ inventory app เปิดให้เมื่อ login

มีอีกสอง flow ที่ตามธรรมเนียมเป็น admin-only แม้ route จะเปิดให้
authenticated user ทุกคนเข้า: ปุ่ม sync **Fetch Keycloak**
(มีความหมายเฉพาะกับ operator ที่มีสิทธิ์ admin ฝั่ง backend ของ
Keycloak) และ action **Hard Delete** (ยืนยันด้วยการพิมพ์ username บน
หน้า list เทียบกับ soft-delete มาตรฐานจากเมนู action ของ row)

## 3. แนวคิดสำคัญ

- **User** — หนึ่ง row ใน `user` แทนหนึ่ง identity ที่ login ได้ ฟอร์ม
  มี 8 field ที่แก้ไขได้: `username` (ตั้งครั้งเดียวตอน create แล้ว
  disable), `email`, `platform_role`, `alias_name`, `firstname`,
  `middlename`, `lastname` และ `is_active` ส่วน response ของ list ยัง
  มี `created_at`/`created_by_name` และ `updated_at`/`updated_by_name`
  สำหรับคอลัมน์ audit และ `deleted_at`/`deleted_by_name` สำหรับ badge
  soft-delete
- **Platform role** — ค่าเดี่ยวที่เลือกจากค่าคงที่ `PLATFORM_ROLES` 7 ค่า:
  `super_admin`, `platform_admin`, `support_manager`, `support_staff`,
  `security_officer`, `integration_developer`, `user` ฟิลด์นี้คือสิ่งที่
  array `allowedRoles` ของทุกโมดูลใช้ตรวจสอบ การเปลี่ยนค่าจะเปลี่ยน
  โมดูลที่ user เข้าถึงได้ตั้งแต่ login ครั้งถัดไป หมายเหตุ: มีเพียง 5
  ใน 7 ค่านี้ (`platform_admin`, `super_admin`, `support_manager`,
  `support_staff`, `security_officer`) ที่ปรากฏใน `AuthContext.ALLOWED_ROLES`
  และสามารถ authenticate กับ Platform admin SPA ได้ — `integration_developer`
  และ `user` เป็นค่าข้อมูลที่ถูกต้องแต่ผู้ถือค่าเหล่านี้ไม่สามารถ login
  ได้ ดู [[auth-roles]] สำหรับ login flow
- **Cluster assignment (`tb_cluster_user`)** — M:N join ระหว่าง user
  กับ cluster พร้อม `role` ระดับ cluster เป็น `admin` หรือ `user` หน้า
  edit user แสดงข้อมูลนี้แบบ read-only เป็นการ์ด Clusters การแก้ไข
  ทำจากการ์ด Users บนหน้า edit cluster ผู้ใช้ต้องเป็นสมาชิก cluster ก่อน
  ถึงจะถูกเพิ่มเข้า BU ใต้ cluster นั้น
- **BU assignment** — M:N join ระหว่าง user กับ business unit พร้อม
  `role` ระดับ BU ของตัวเอง (`admin` หรือ `user` จากค่าคงที่ `BU_ROLES`),
  flag `is_active` และ flag `is_default` หน้า edit user คือจุดมาตรฐาน
  ในการเพิ่ม/ลบ row เหล่านี้ dialog **Add BU** กรอง BU ที่เลือกได้ให้
  เหลือเฉพาะ BU ที่อยู่ใน cluster ที่ user เป็นสมาชิกอยู่แล้ว
- **Active flag (`is_active`)** — toggle ว่า user login ได้หรือไม่
  เป็นอิสระจาก soft-delete; user ที่ active อาจกำลังจะถูกลบ และ user
  ที่ inactive อาจถูกเก็บไว้เพื่อ audit ก่อนลบ
- **Soft delete vs. hard delete** — เมนู action ระดับ row มีให้ทั้งสอง
  แบบ soft delete ตั้งค่า `deleted_at`/`deleted_by_name`; หน้า list
  จะซ่อน row เหล่านี้ เว้นแต่จะเปิด filter "Show soft-deleted users"
  และจะมี badge "Deleted" สีแดงพร้อมคอลัมน์ "Deleted By" ส่วน hard
  delete ลบถาวร มี dialog บังคับให้ operator พิมพ์ username/email ตรง ๆ
  เพื่อยืนยัน
- **Keycloak sync** — `userService.fetchKeycloakUsers()` ถูกเปิดเผย
  เป็นปุ่ม header บนหน้า list refresh user list ของแพลตฟอร์มจาก
  Keycloak; หน้า reload ตารางหลัง sync สำเร็จ
- **Admin password reset** — header ของหน้า edit มี action **Change
  Password** ที่เปิด dialog ขอ new + confirm (อย่างน้อย 6 ตัวอักษร และ
  ต้องตรงกัน) submit ไป `userService.resetPassword(id, newPassword)`
  surface นี้ไม่มี flow email-link — reset เป็น admin-initiated และ
  ทำทันที

## 4. บทบาทและ Persona

route ทั้งสามของ user ห่อด้วย `PrivateRoute` **โดยไม่มี prop
`allowedRoles`** — ยืนยันจากการอ่าน `../carmen-platform/src/App.tsx`
(บรรทัด 87–109) และ `../carmen-platform/SITEMAP.md` (row ของ `/users`,
`/users/new`, `/users/:id/edit` ระบุเป็น "Authenticated" ทุก row) user
ใด ๆ ที่มี session ที่ใช้ได้เข้าถึง route เหล่านี้ได้ `UserEdit.tsx`
ไม่ gate ปุ่มแต่ละตัว (Edit, Save, Change Password, Add BU, Trash บน
row BU) ตาม platform role ด้วย; `UserManagement.tsx` ก็ไม่ gate Fetch
Keycloak, Export, Add User, Delete หรือ Hard Delete ตาม platform role
แนวคิด role เดียวที่หน้านี้จัดการคือ **data** ที่หน้าแก้ไข —
`platform_role` ของ user เอง และ `role` ระดับ BU บน row assignment
ไม่ใช่ gate ของหน้า

| Persona | สิทธิ์เข้า route | งานที่ทำที่นี่บ่อย |
|---|---|---|
| ผู้ใช้แพลตฟอร์มที่ login แล้วทุกคน | เข้าถึงเต็มสำหรับ list, create, edit, soft-delete, hard-delete user, fetch จาก Keycloak, เปลี่ยนรหัสผ่าน และ assign/unassign BU | ตามบริบทงาน — วิศวกร support ของ Carmen onboard user ลูกค้าใหม่และ reset รหัสผ่าน; admin ฝั่งลูกค้าอัพเดทข้อมูล contact ของพนักงานและ roster BU ของตัวเอง |

เพราะไม่มี array `allowedRoles` หน้าที่จำกัดว่าใครแก้ไข state ของ user
ได้ที่ระดับ API จึงเป็นความรับผิดชอบของ backend และ process การ
provisioning ไม่ใช่ surface admin นี้ cross-link ใน Section 5
ครอบคลุมว่า surface admin ที่ gate เข้มกว่า (clusters, report
templates) ของแพลตฟอร์มอ่านค่า `platform_role` ที่เขียนที่นี่ไปใช้
อย่างไร

## 5. โมดูลที่เกี่ยวข้อง

- [[business-units]] — supply BU ที่ปรากฏในการ์ด Business Units ของ
  user; assignment ที่สร้างที่นี่จะปรากฏบนการ์ด Users ของ BU เอง ทั้ง
  สองหน้าแก้ไข BU-user join เดียวกันด้วย `BU_ROLES` (`admin`/`user`)
  และ flag `is_default` เดียวกัน
- [[clusters]] — supply cluster ที่ปรากฏในการ์ด Clusters ของ user
  (read-only ที่นี่) หน้า edit cluster คือจุดมาตรฐานในการเพิ่ม/ลบ row
  `tb_cluster_user` โมดูล Users ใช้สมาชิกภาพ cluster ปัจจุบันเพื่อจำกัด
  dropdown ในการ assign BU จึงต้องให้สิทธิ์ cluster จากฝั่ง cluster
  ก่อน
- [[auth-roles]] — กำหนดความหมายของค่า `platform_role` ทั้ง 7 ค่าและ
  array `allowedRoles` ที่ค่าแต่ละค่าปรากฏใน SPA การเปลี่ยน
  `platform_role` ที่นี่จะเปลี่ยนโมดูลที่ user เข้าถึงได้ตั้งแต่ login
  ครั้งถัดไป
- [[profile]] — มุมมองบุคคลที่หนึ่งของ user record เดียวกัน — เมนู
  avatar มีลิงก์ "Profile" ไปที่นั่น โมดูล Users คือมุมมอง admin
  มุมที่สาม โมดูล Profile คือ row เดียวกันที่เจ้าของดูเอง

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/SITEMAP.md` — ตาราง route เป็น source of truth
  ของ user route ทั้งสาม (เป็น "Authenticated" ทั้งหมด)
- `../carmen-platform/src/App.tsx` — การต่อสาย `PrivateRoute` บรรทัด
  87–109; ยืนยันว่าไม่มี prop `allowedRoles` บน user route ใด ๆ
- `../carmen-platform/src/pages/UserManagement.tsx` — หน้า list, filter
  role/status/show-deleted, ส่งออก CSV, action Fetch Keycloak, dialog
  delete และ hard-delete, ค่าคงที่ `PLATFORM_ROLES`
- `../carmen-platform/src/pages/UserEdit.tsx` — หน้า create/view/edit,
  การ์ด User Details, การ์ด Clusters (read-only), การ์ด Business Units
  พร้อม dialog Add BU, dialog Change Password, ค่าคงที่ `BU_ROLES` และ
  `PLATFORM_ROLES`, interface `UserFormData`
- `../carmen-platform/src/services/userService.ts` — REST client
  (`/api-system/user`), `fetchKeycloakUsers`, `resetPassword`,
  `delete`, `hardDelete`

## 7. หน้าในโมดูลนี้

- [Data Model](./data-model.md) — field ของ entity user, enum
  `platform_role`, join `tb_cluster_user` และ BU-user join พร้อม role
  ระดับ BU และ flag `is_default` (stub — ยังไม่สมบูรณ์)
- [Lifecycle](./lifecycle.md) — flow การ create, activate/deactivate
  ผ่าน `is_active`, soft vs. hard delete, password reset ที่ admin
  เป็นผู้ทำ, sync จาก Keycloak (stub — ยังไม่สมบูรณ์)
- [UI Screens](./ui-screens.md) — หน้า list `UserManagement` พร้อม
  filter และปุ่ม sync Keycloak และเลย์เอาต์สามการ์ดของ `UserEdit`
  รวมถึง dialog Add BU และ dialog Change Password
  (stub — ยังไม่สมบูรณ์)
