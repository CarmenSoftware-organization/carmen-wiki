---
title: ผู้ใช้ (Users)
description: บัญชีผู้ใช้ระดับแพลตฟอร์ม — identity, avatar และการ assign cluster/BU ที่กำหนดขอบเขตว่าผู้ใช้เข้าถึงอะไรได้ใน inventory app ส่วนสิทธิ์เข้า Platform admin มอบผ่าน role assignment ของ RBAC
published: true
date: 2026-06-10T16:30:00.000Z
tags: platform/users, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# ผู้ใช้ (Users)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** หน้าจัดการบัญชีผู้ใช้ระดับแพลตฟอร์ม — หนึ่ง row ต่อหนึ่งคนที่ login ได้ เก็บ identity (`username`, `email`, ชื่อแบ่งส่วน, `alias_name`), avatar, flag `is_active` และมุมมอง read-only ของ cluster และ BU ที่ผู้ใช้ถูก assign อยู่ (การ assign จริงทำจากฝั่ง cluster หรือ — สำหรับ BU — จาก dialog Add-BU ในหน้านี้) ส่วนสิ่งที่บัญชี *ทำได้* ใน Platform admin SPA ไม่ได้เก็บที่นี่ — นั่นคือ role assignment ของโมดูล [RBAC](/th/platform/rbac) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** ผู้ถือ permission key `user.read`/`user.create`/`user.update`/`user.delete` — โดยทั่วไปคือวิศวกร support ของ Carmen และ admin ฝั่งลูกค้า &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_user` + `tb_user_profile` (ฟิลด์ในฟอร์ม 7 ตัว: `username`, `email`, `alias_name`, `firstname`, `middlename`, `lastname`, `is_active`; พร้อม soft-delete trio `deleted_at`/`deleted_by_name` และ timestamp บวก `avatar_url` แบบ presigned ตอนอ่าน), `tb_cluster_user` (M:N join กับ cluster — อ่านอย่างเดียวที่นี่), BU-user join (M:N join กับ BU พร้อม `role` ระดับ BU เป็น `admin`/`user` และ flag `is_default`) &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูล Users เปิดเผย aggregate ของ user ระดับแพลตฟอร์มผ่านรูปแบบสองหน้าจอ มาตรฐานเดียวกับที่ใช้ในทุกที่ใน Platform SPA:

- **`/users` → `UserManagement`** — `DataTable` แบบ server-side พร้อมคอลัมน์ avatar นำหน้า (fallback เป็นอักษรย่อใน badge วงกลม วาง `avatar_url` แบบ presigned ของจริงทับเมื่อมีค่า), การค้นหาแบบ debounce, แผง filter แบบ Sheet (สถานะ Active/Inactive และ "show soft-deleted" — filter ตาม Role รุ่นเก่าหายไปพร้อมกับ role enum), ส่งออก CSV, จดจำสถานะ UI ใน `localStorage` (search, page, perpage, sort, status filter, toggle show-deleted), คอลัมน์ audit Created/Updated พร้อมปุ่ม header สองตัวที่มีเฉพาะในโมดูลนี้: **Fetch Keycloak** (เรียก `userService.fetchKeycloakUsers()` เพื่อดึง user list ปัจจุบันจาก Keycloak เข้ามาที่ DB ของแพลตฟอร์ม) และ **Add User** (ห่อด้วย `<Can permission="user.create">`) ส่วน action Edit และ Delete/Hard-Delete ของ row ถูก gate ภายในหน้าด้วย `user.update` และ `user.delete`
- **`/users/new` → `UserEdit` (โหมด create)** — การ์ด "User Details" เดียวที่มีฟอร์ม 7 ฟิลด์ เมื่อสร้างสำเร็จ หน้าจะ `navigate(..., { replace: true })` ไป route edit ของ id ที่เพิ่งสร้าง
- **`/users/:id/edit` → `UserEdit` (โหมด view/edit)** — header แสดง avatar ของ user (pattern อักษรย่อ fallback เดียวกับหน้า list) ข้างชื่อหน้า ตามด้วยการ์ดสามใบ วางเรียงกันลงล่าง การ์ด **User Details** เริ่มต้นแบบดูอย่างเดียวและ เปลี่ยนเป็นแก้ไขผ่านปุ่ม Edit ซึ่งห่อด้วย `<Can permission="user.update">` (ในโหมดแก้ไข `username` จะ disable — ตั้งค่าได้ตอนสร้างเท่านั้น) การ์ด **Clusters** แสดงข้อมูลแบบ read-only จาก `tb_cluster_user`: การ์ดย่อยแต่ละใบแสดงชื่อ/code ของ cluster, badge active/inactive และ role ระดับ cluster (`admin` หรือ `user`) การ์ด **Business Units** แสดง row ของ BU-user join พร้อม role ระดับ BU, badge `is_default` และไอคอนถังขยะสำหรับลบ พร้อม dialog **Add BU** ของตัวเอง ซึ่ง BU ที่เลือกได้จะถูกจำกัดเฉพาะ cluster ที่ user ถูก assign อยู่แล้ว

header บนหน้า edit ยังเปิดเผยปุ่ม **Change Password** (admin-initiated password reset ผ่าน `userService.resetPassword` มี dialog ให้ยืนยัน สองครั้ง) ส่วนหน้า list มี dialog hard-delete ที่บังคับให้ operator พิมพ์ username/email เพื่อยืนยัน

## 2. บริบททางธุรกิจ

ตาราง user คือ source of truth ของแพลตฟอร์มสำหรับ "คนนี้ login ได้" แต่สิ่งที่บัญชี *ทำได้* ใน Platform admin SPA ไม่ได้เก็บบน row ของ user อีกต่อไป: enum `platform_role` ค่าเดี่ยวรุ่นเก่าถูกถอดออกแล้ว (commit `6091ffc` ของ frontend; ทั้งคอลัมน์และ `enum_platform_role` หายไปจาก Prisma platform schema) สิทธิ์ระดับแพลตฟอร์มมอบผ่าน role assignment ของ RBAC ซึ่งจัดการบนหน้าจอ **User Platform** แยกต่างหาก (`/platform/user-platform`) — โมดูล Users จัดการตัว *บัญชี* ส่วนการ assign role และ scope อยู่ในโมดูล [RBAC](/th/platform/rbac) ตอน login SPA จะ validate effective permission ของบัญชี (`GET /api/user/permission/platform`) และปฏิเสธ session ที่ไม่ถือ permission ใดเลย โดยมีข้อยกเว้น bootstrap ขณะที่แพลตฟอร์มมี user 0–1 คน — ดังนั้นบัญชีที่เพิ่งสร้างใหม่จะเข้า Platform admin SPA ไม่ได้จนกว่าจะมีคน assign role ให้

นอกจาก identity แล้ว ตาราง user ยังบันทึก **ที่ไหน** ที่ user ทำงานได้ การเป็นสมาชิก cluster เก็บใน `tb_cluster_user` และถูกแก้ไข จากหน้า edit cluster (cross-link ใน Section 5) โมดูล Users แสดงผลลัพธ์ แบบ read-only เป็นการ์ด Clusters บนหน้า edit ส่วนการเป็นสมาชิก BU ทำงานต่อ cluster — dialog **Add BU** บนหน้านี้จะแสดงเฉพาะ BU ที่ `cluster_id` ตรงกับ cluster ที่ user เป็นสมาชิกอยู่แล้ว เพื่อรักษาขอบเขต tenant ให้สะอาด: user ถูก assign ให้ BU นอก cluster ที่ตนเองสังกัด ไม่ได้ ส่วน BU-user join ก็มี `role` ของตัวเอง (`admin` หรือ `user` เป็นอิสระจาก RBAC assignment ของแพลตฟอร์ม) และ flag `is_default` ที่บอกว่า BU ตัวไหน จะเป็น BU ที่ inventory app เปิดให้เมื่อ login

มีอีกสอง flow ที่ต้องระวังนอกเหนือจาก gate บน UI: ปุ่ม sync **Fetch Keycloak** (ไม่มี gate `<Can>` ภายในหน้า — session ที่ถือ `user.read` ก็เห็น — และมีความหมายเฉพาะกับ operator ที่มีสิทธิ์ admin ฝั่ง backend ของ Keycloak) และ action **Hard Delete** (gate ด้วย `user.delete` บวก dialog ยืนยันด้วยการพิมพ์ username บน หน้า list เทียบกับ soft-delete มาตรฐานจากเมนู action ของ row)

## 3. แนวคิดสำคัญ

- **User** — หนึ่ง row ใน `tb_user` แทนหนึ่ง identity ที่ login ได้ ฟอร์มมี 7 field ที่แก้ไขได้: `username` (ตั้งครั้งเดียวตอน create แล้ว disable), `email`, `alias_name`, `firstname`, `middlename`, `lastname` และ `is_active` ส่วน response ของ list ยังมี `created_at`/`created_by_name` และ `updated_at`/`updated_by_name` สำหรับคอลัมน์ audit (field แบบ flat ชนะ; object `audit` แบบ nested เป็น fallback) และ `deleted_at`/`deleted_by_name` สำหรับ badge soft-delete
- **สิทธิ์แพลตฟอร์มผ่าน RBAC assignment** — สิ่งที่บัญชีเข้าถึงได้ใน Platform admin SPA ตัดสินด้วย role assignment (scope ระดับแพลตฟอร์มหรือต่อ cluster) ซึ่งจัดการบนหน้าจอ `/platform/user-platform` — *ไม่ใช่* บนหน้า edit user gate ตอน login จะรับ session เฉพาะเมื่อถือ effective permission อย่างน้อยหนึ่งตัว ถือ flag super-admin หรือเข้าข้อยกเว้น bootstrap (จำนวน user รวม 0–1) ดู [Platform RBAC](/th/platform/rbac) สำหรับโมเดล catalog/role/assignment และ walkthrough ของ login; จนถึง 2026-06-10 สิ่งนี้เคยเป็น enum `platform_role` ค่าเดี่ยวบน row ของ user ซึ่งถูกถอดออกแล้ว
- **Avatar** — เก็บเป็น `avatar_file_token` บน `tb_user_profile`; API resolve เป็น string `avatar_url` แบบ presigned บน response ของ list และ detail คอลัมน์นำหน้าของ list และ header ของหน้า edit จะ render avatar วงกลมพร้อม fallback เป็นอักษรย่อ (ตัวอักษรแรกของ `firstname`+`lastname`) และวางรูปจริงทับเมื่อมี `avatar_url` โดยซ่อนอีกครั้งเมื่อโหลดรูปไม่สำเร็จ fallback ลำดับสองต่างกันตาม surface: list ใช้สองตัวอักษรแรกของ `name`/`username`/`email` ส่วน header ของหน้า edit ดูเฉพาะ `username`/`email` (form data ไม่มี field `name` แบบ flat)
- **Display name** — คอลัมน์ Name ของ list ประกอบโดย helper `getNameDisplay`: เมื่อ `firstname`/`middlename`/`lastname` ตัวใดตัวหนึ่งมีค่า ส่วนที่ไม่ว่างจะถูกต่อกันด้วยช่องว่าง; ไม่เช่นนั้นจะแสดง field `name` แบบ flat โดย fallback เป็น `-`
- **Cluster assignment (`tb_cluster_user`)** — M:N join ระหว่าง user กับ cluster พร้อม `role` ระดับ cluster เป็น `admin` หรือ `user` หน้า edit user แสดงข้อมูลนี้แบบ read-only เป็นการ์ด Clusters การแก้ไข ทำจากการ์ด Users บนหน้า edit cluster ผู้ใช้ต้องเป็นสมาชิก cluster ก่อน ถึงจะถูกเพิ่มเข้า BU ใต้ cluster นั้น
- **BU assignment** — M:N join ระหว่าง user กับ business unit พร้อม `role` ระดับ BU ของตัวเอง (`admin` หรือ `user` จากค่าคงที่ `BU_ROLES`), flag `is_active` และ flag `is_default` หน้า edit user คือจุดมาตรฐาน ในการเพิ่ม/ลบ row เหล่านี้ dialog **Add BU** กรอง BU ที่เลือกได้ให้ เหลือเฉพาะ BU ที่อยู่ใน cluster ที่ user เป็นสมาชิกอยู่แล้ว
- **Active flag (`is_active`)** — toggle ว่า user login ได้หรือไม่ เป็นอิสระจาก soft-delete; user ที่ active อาจกำลังจะถูกลบ และ user ที่ inactive อาจถูกเก็บไว้เพื่อ audit ก่อนลบ
- **Soft delete vs. hard delete** — เมนู action ระดับ row มีให้ทั้งสอง แบบ แต่ละตัวห่อด้วย `<Can permission="user.delete">` soft delete ตั้งค่า `deleted_at`/`deleted_by_name`; หน้า list จะซ่อน row เหล่านี้ เว้นแต่จะเปิด filter "Show soft-deleted users" และจะมี badge "Deleted" สีแดง (tooltip ระบุชื่อผู้ลบผ่าน `deleted_by_name`) พร้อมคอลัมน์ "Deleted By" ส่วน hard delete ลบถาวร มี dialog เพิ่มเติมบังคับให้ operator พิมพ์ username/email ตรง ๆ เพื่อยืนยัน
- **Keycloak sync** — `userService.fetchKeycloakUsers()` ถูกเปิดเผย เป็นปุ่ม header บนหน้า list refresh user list ของแพลตฟอร์มจาก Keycloak; หน้า reload ตารางหลัง sync สำเร็จ
- **Admin password reset** — header ของหน้า edit มี action **Change Password** ที่เปิด dialog ขอ new + confirm (อย่างน้อย 6 ตัวอักษร และ ต้องตรงกัน) submit ไป `userService.resetPassword(id, newPassword)` surface นี้ไม่มี flow email-link — reset เป็น admin-initiated และ ทำทันที

## 4. บทบาทและ Persona

route ทั้งสามของ user ห่อด้วย `PrivateRoute` พร้อม prop `requiredPermission` — ยืนยันจากการอ่าน `../carmen-platform/src/App.tsx` (บรรทัด 132–155) — และรายการ "Users" ใน sidebar (กลุ่ม Organization) filter ด้วย key `user.read` ตัวเดียวกันใน `Layout.tsx` mutation ภายในหน้าถูกห่อเพิ่มด้วย gate `<Can>` (commit `239b4a9`, `f3f77cf`) ต่างจากหน้า Clusters และ Business Units ตรงที่ไม่มี gate ใดของ user ส่ง `clusterId` — การตรวจสอบ permission ของ user รันที่ scope แบบกว้างเสมอ ดังนั้น grant ของ key `user.*` ที่ scope ไว้กับ cluster จะมีพฤติกรรมเหมือน grant ระดับแพลตฟอร์มใน UI ของโมดูลนี้

| Surface | Gate |
|---|---|
| `/users` (list) | route guard `user.read` |
| `/users/new` (create) | route guard `user.create` |
| `/users/:id/edit` (view/edit) | route guard `user.update` |
| Add User (header ของ list) | `<Can permission="user.create">` |
| Row action: Edit | `<Can permission="user.update">` |
| Row action: Delete + Hard Delete | `<Can permission="user.delete">` |
| Toggle Edit (header ของหน้า edit) | `<Can permission="user.update">` |

สิ่งที่ไม่ถูก gate ภายในหน้า (มองเห็นได้สำหรับทุกคนที่ผ่าน route guard): **Fetch Keycloak**, **Export**, **Change Password**, **Add BU** และไอคอนถังขยะลบ assignment ของ BU — บวกกับปุ่มลัด "Add User" ใน empty state ซึ่ง (ต่างจากปุ่ม header) ไม่ถูกห่อด้วย `<Can>` สำหรับสิ่งเหล่านี้ การบังคับใช้ฝั่ง backend คือขอบเขตที่แท้จริง สังเกตว่า key `user.*` gate เฉพาะ CRUD ของบัญชีเท่านั้น; การ assign role/scope ถูก gate ด้วย key `user_platform.*` แยกต่างหากบนหน้าจอของ [RBAC](/th/platform/rbac)

| Persona | Key ที่มักถือ | งานที่ทำที่นี่บ่อย |
|---|---|---|
| วิศวกร support ของ Carmen / admin ฝั่งลูกค้า | `user.read` + `user.create`/`user.update`/`user.delete` | Onboard user ลูกค้าใหม่, reset รหัสผ่าน, อัพเดทข้อมูล contact ของพนักงาน, จัดการ roster ของ BU |
| Auditor แบบอ่านอย่างเดียว | `user.read` เท่านั้น | เปิดดูได้แค่หน้า list — ลิงก์ username ชี้ไป `/users/:id/edit` ซึ่ง route guard `user.update` block ด้วย Access Denied (ไม่มี route detail แบบ read-only); Add User, Edit/Delete ของ row และ toggle Edit จะไม่ render |

## 5. โมดูลที่เกี่ยวข้อง

- [business-units](/th/platform/business-units) — supply BU ที่ปรากฏในการ์ด Business Units ของ user; assignment ที่สร้างที่นี่จะปรากฏบนการ์ด Users ของ BU เอง ทั้ง สองหน้าแก้ไข BU-user join เดียวกันด้วย `BU_ROLES` (`admin`/`user`) และ flag `is_default` เดียวกัน
- [clusters](/th/platform/clusters) — supply cluster ที่ปรากฏในการ์ด Clusters ของ user (read-only ที่นี่) หน้า edit cluster คือจุดมาตรฐานในการเพิ่ม/ลบ row `tb_cluster_user` โมดูล Users ใช้สมาชิกภาพ cluster ปัจจุบันเพื่อจำกัด dropdown ในการ assign BU จึงต้องให้สิทธิ์ cluster จากฝั่ง cluster ก่อน
- [rbac](/th/platform/rbac) — เป็นเจ้าของฝั่งสิทธิ์เข้าถึงของ user: catalog ของ permission, role, scoped assignment (`/platform/user-platform`), flag super-admin และ gate effective-permissions ตอน login โมดูล Users สร้างตัวบัญชี; RBAC ตัดสินว่าบัญชีทำอะไรได้
- [profile](/th/platform/profile) — มุมมองบุคคลที่หนึ่งของ user record เดียวกัน — เมนู avatar มีลิงก์ "Profile" ไปที่นั่น โมดูล Users คือมุมมอง admin มุมที่สาม โมดูล Profile คือ row เดียวกันที่เจ้าของดูเอง

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — การต่อสาย `PrivateRoute` บรรทัด 132–155; key `requiredPermission` คือ `user.read`/`user.create`/`user.update` บน user route ทั้งสาม (`SITEMAP.md` ใน repo เดียวกันยังแสดง row "Authenticated" ก่อนยุค RBAC และตามหลังโค้ด)
- `../carmen-platform/src/pages/UserManagement.tsx` — หน้า list, คอลัมน์ avatar พร้อม fallback อักษรย่อ, `getNameDisplay`, filter status/show-deleted, ส่งออก CSV, action Fetch Keycloak, Add/Edit/Delete ที่ gate ด้วย `<Can>`, dialog delete และ hard-delete, การ flatten ของ `audit` แบบ nested
- `../carmen-platform/src/pages/UserEdit.tsx` — หน้า create/view/edit, avatar บน header, การ์ด User Details, `<Can permission="user.update">` บน toggle Edit, การ์ด Clusters (read-only), การ์ด Business Units พร้อม dialog Add BU, dialog Change Password, ค่าคงที่ `BU_ROLES`, interface `UserFormData` (7 ฟิลด์)
- `../carmen-platform/src/services/userService.ts` — REST client (`/api-system/user`), `fetchKeycloakUsers`, `resetPassword`, `delete`, `hardDelete`
- `../carmen-platform/src/components/Can.tsx` และ `src/context/AuthContext.tsx` — component gate ภายในหน้า และ resolver `hasPermission` ที่อยู่เบื้องหลังทุก gate ข้างต้น

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/users/data-model) — field ของ entity user, ส่วนขยาย profile (ชื่อแบ่งส่วน, `avatar_file_token`), join `tb_cluster_user` และ BU-user join พร้อม role ระดับ BU และ flag `is_default` (stub — ยังไม่สมบูรณ์)
- [Lifecycle](/th/platform/users/lifecycle) — flow การ create, gate effective-permissions ตอน sign-in, activate/deactivate ผ่าน `is_active`, soft vs. hard delete, password reset ที่ admin เป็นผู้ทำ, sync จาก Keycloak (stub — ยังไม่สมบูรณ์)
- [UI Screens](/th/platform/users/ui-screens) — หน้า list `UserManagement` พร้อมคอลัมน์ avatar, filter และปุ่ม sync Keycloak และเลย์เอาต์สามการ์ดของ `UserEdit` รวมถึง dialog Add BU และ dialog Change Password (stub — ยังไม่สมบูรณ์)
