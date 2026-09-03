---
title: ผู้ใช้ (Users)
description: บัญชีผู้ใช้ระดับแพลตฟอร์ม — identity, avatar และการ assign cluster/BU ที่กำหนดขอบเขตว่าผู้ใช้เข้าถึงอะไรได้ใน inventory app ส่วนสิทธิ์เข้า Platform admin มอบผ่าน role assignment ของ RBAC
published: true
date: 2026-07-29T07:06:05.000Z
tags: platform/users, carmen-software
editor: markdown
dateCreated: 2026-05-19T00:00:00.000Z
---

# ผู้ใช้ (Users)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** หน้าจัดการบัญชีผู้ใช้ระดับแพลตฟอร์ม — หนึ่ง row ต่อหนึ่งคนที่ login ได้ เก็บ identity (`username`, `email`, ชื่อแบ่งส่วน, `alias_name`), avatar, flag `is_active` และมุมมอง read-only ของ cluster และ BU ที่ผู้ใช้ถูก assign อยู่ (การ assign จริงทำจากฝั่ง cluster หรือ — สำหรับ BU — จาก dialog Add-BU ในหน้านี้) ส่วนสิ่งที่บัญชี *ทำได้* ใน Platform admin SPA ไม่ได้เก็บที่นี่ — นั่นคือ role assignment ของโมดูล [RBAC](/th/platform/rbac) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** ผู้ถือ permission key `user.read`/`user.create`/`user.update`/`user.delete` — โดยทั่วไปคือวิศวกร support ของ Carmen และ admin ฝั่งลูกค้า &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_user` + `tb_user_profile` (ฟิลด์ในฟอร์ม 7 ตัว: `username`, `email`, `alias_name`, `firstname`, `middlename`, `lastname`, `is_active`; พร้อม soft-delete trio `deleted_at`/`deleted_by_name` และ timestamp บวก `avatar_url` แบบ presigned ตอนอ่าน), `tb_cluster_user` (M:N join กับ cluster — อ่านอย่างเดียวที่นี่), BU-user join (M:N join กับ BU พร้อม `role` ระดับ BU เป็น `admin`/`user` และ flag `is_default`) &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูล Users เปิดเผย aggregate ของ user ระดับแพลตฟอร์มผ่านรูปแบบสองหน้าจอ มาตรฐานเดียวกับที่ใช้ในทุกที่ใน Platform SPA:

- **`/users` → `UserManagement`** — `DataTable` แบบ server-side พร้อมคอลัมน์ avatar นำหน้า (fallback เป็นอักษรย่อใน badge วงกลม วาง `avatar_url` แบบ presigned ของจริงทับเมื่อมีค่า), แถบสรุป **Directory** (`UserDirectorySummary` — จำนวนรวม/active/inactive/archived บวก "Recently added" ที่แสดง avatar ซ้อนกันของ user ใหม่ล่าสุด), การค้นหาแบบ debounce, แผง filter แบบ Sheet (สถานะ Active/Inactive และ "show soft-deleted"), ส่งออก CSV, จดจำสถานะ UI ใน `localStorage` (search, page, perpage, sort, status filter, toggle show-deleted), คอลัมน์ **BU** (จำนวน active/total ของการ assign business unit ต่อ user ใหม่ตั้งแต่ sync ก่อนหน้า), คอลัมน์ audit Created/Updated พร้อมปุ่ม header สองตัวที่มีเฉพาะในโมดูลนี้: **Fetch Keycloak** (เรียก `userService.fetchKeycloakUsers()` เพื่อดึง user list ปัจจุบันจาก Keycloak เข้ามาที่ DB ของแพลตฟอร์ม — ตอนนี้ gate ด้วย `<Can permission="user.create">`) และ **Add User** (ห่อด้วย `<Can permission="user.create">` เช่นกัน) สำหรับ session ระดับ super-admin เท่านั้น checkbox ของแถวจะเปิดใช้งาน **bulk soft-delete** และ **bulk hard-delete** (แบบหลังอยู่หลังรหัสยืนยัน 6 ตัวอักษรแบบสุ่ม) ส่วน action Edit และ Delete/Hard-Delete ของ row ถูก gate ภายในหน้าด้วย `user.update` และ `user.delete`; dialog hard-delete แบบทีละคนได้ปุ่ม "Copy username" สำหรับ super-admin เพิ่มมาด้วย
- **`/users/new` → `UserEdit` (โหมด create)** — การ์ด "Account details" เดียวที่มีฟอร์ม 7 ฟิลด์ เมื่อสร้างสำเร็จ หน้าจะ `navigate(..., { replace: true })` ไป route edit ของ id ที่เพิ่งสร้าง
- **`/users/:id/edit` → `UserEdit` (โหมด view/edit)** — การ์ด **`UserIdentityHero`** (avatar, ชื่อเป็น `<h1>` เดียวของหน้า, chip username/email/alias, badge Active/Inactive, บรรทัดสรุป "Access to N business units across M clusters") แทนที่ header แบบธรรมดาเดิม การ์ด **User Details** ด้านล่างยังคงเริ่มต้นแบบดูอย่างเดียวและเปลี่ยนเป็นแก้ไขผ่านปุ่ม Edit เดิม (ห่อด้วย `<Can permission="user.update">`; ในโหมดแก้ไข `username` จะ disable — ตั้งค่าได้ตอนสร้างเท่านั้น) ด้านล่างนั้น การ์ด Clusters และการ์ด Business Units แยกกันเดิม ถูก **รวมเป็นการ์ด `UserAccessTree` ใบเดียว** — ลำดับชั้นเดียวของ cluster ของ user แต่ละอันขยายไปดู business unit ที่ assign อยู่ภายใน (พร้อมกลุ่ม "Other business units" รวบรวม BU assignment ที่ cluster ไม่อยู่ในสมาชิกภาพของ user) dialog **Add BU** ของตัวเองยังคงจำกัดเฉพาะ cluster ที่ user เป็นสมาชิกอยู่แล้วเหมือนเดิม empty state แบบ not-found จะ gate ทั้งหน้าเมื่อ id หาไม่เจอ และการบันทึกได้รับการป้องกันด้วย token optimistic-lock `doc_version` — ทั้งสามแพทเทิร์นนี้ใช้ร่วมกับ [clusters](/th/platform/clusters)/[business-units](/th/platform/business-units)

header บนหน้า edit ยังเปิดเผยปุ่ม **Change Password** (admin-initiated password reset ผ่าน `userService.resetPassword` มี dialog ให้ยืนยัน สองครั้ง) ส่วนหน้า list มี dialog hard-delete ที่บังคับให้ operator พิมพ์ username/email เพื่อยืนยัน

## 2. บริบททางธุรกิจ

ตาราง user คือ source of truth ของแพลตฟอร์มสำหรับ "คนนี้ login ได้" แต่สิ่งที่บัญชี *ทำได้* ใน Platform admin SPA ไม่ได้เก็บบน row ของ user อีกต่อไป: enum `platform_role` ค่าเดี่ยวรุ่นเก่าถูกถอดออกแล้ว (commit `6091ffc` ของ frontend; ทั้งคอลัมน์และ `enum_platform_role` หายไปจาก Prisma platform schema) สิทธิ์ระดับแพลตฟอร์มมอบผ่าน role assignment ของ RBAC ซึ่งจัดการบนหน้าจอ **User Platform** แยกต่างหาก (`/platform/user-platform`) — โมดูล Users จัดการตัว *บัญชี* ส่วนการ assign role และ scope อยู่ในโมดูล [RBAC](/th/platform/rbac) ตอน login SPA จะ validate effective permission ของบัญชี (`GET /api/user/permission/platform`) และปฏิเสธ session ที่ไม่ถือ permission ใดเลย โดยมีข้อยกเว้น bootstrap ขณะที่แพลตฟอร์มมี user 0–1 คน — ดังนั้นบัญชีที่เพิ่งสร้างใหม่จะเข้า Platform admin SPA ไม่ได้จนกว่าจะมีคน assign role ให้

นอกจาก identity แล้ว ตาราง user ยังบันทึก **ที่ไหน** ที่ user ทำงานได้ การเป็นสมาชิก cluster เก็บใน `tb_cluster_user` และถูกแก้ไข จากหน้า edit cluster (cross-link ใน Section 5) โมดูล Users แสดงผลลัพธ์แบบ read-only ซ้อนอยู่ในการ์ด `UserAccessTree` บนหน้า edit ส่วนการเป็นสมาชิก BU ทำงานต่อ cluster — dialog **Add BU** บนหน้านี้จะแสดงเฉพาะ BU ที่ `cluster_id` ตรงกับ cluster ที่ user เป็นสมาชิกอยู่แล้ว เพื่อรักษาขอบเขต tenant ให้สะอาด: user ถูก assign ให้ BU นอก cluster ที่ตนเองสังกัด ไม่ได้ ส่วน BU-user join ก็มี `role` ของตัวเอง (`admin` หรือ `user` เป็นอิสระจาก RBAC assignment ของแพลตฟอร์ม) และ flag `is_default` ที่บอกว่า BU ตัวไหน จะเป็น BU ที่ inventory app เปิดให้เมื่อ login

มีอีกสอง flow ที่ต้องระวังนอกเหนือจาก gate บน UI: ปุ่ม sync **Fetch Keycloak** (ตอนนี้อยู่หลัง `<Can permission="user.create">` แล้ว — แก้ไขจาก sync ก่อนหน้าที่ไม่มี gate ภายในหน้าเลย — และมีความหมายเฉพาะกับ operator ที่มีสิทธิ์ admin ฝั่ง backend ของ Keycloak) และ action **Hard Delete** (gate ด้วย `user.delete` บวก dialog ยืนยันด้วยการพิมพ์ username บน หน้า list เทียบกับ soft-delete มาตรฐานจากเมนู action ของ row — พร้อม bulk เวอร์ชันสำหรับ super-admin ใน §3)

## 3. แนวคิดสำคัญ

- **User** — หนึ่ง row ใน `tb_user` แทนหนึ่ง identity ที่ login ได้ ฟอร์มมี 7 field ที่แก้ไขได้: `username` (ตั้งครั้งเดียวตอน create แล้ว disable), `email`, `alias_name`, `firstname`, `middlename`, `lastname` และ `is_active` ส่วน response ของ list ยังมี `created_at`/`created_by_name` และ `updated_at`/`updated_by_name` สำหรับคอลัมน์ audit (field แบบ flat ชนะ; object `audit` แบบ nested เป็น fallback) และ `deleted_at`/`deleted_by_name` สำหรับ badge soft-delete
- **สิทธิ์แพลตฟอร์มผ่าน RBAC assignment** — สิ่งที่บัญชีเข้าถึงได้ใน Platform admin SPA ตัดสินด้วย role assignment (scope ระดับแพลตฟอร์มหรือต่อ cluster) ซึ่งจัดการบนหน้าจอ `/platform/user-platform` — *ไม่ใช่* บนหน้า edit user gate ตอน login จะรับ session เฉพาะเมื่อถือ effective permission อย่างน้อยหนึ่งตัว ถือ flag super-admin หรือเข้าข้อยกเว้น bootstrap (จำนวน user รวม 0–1) ดู [Platform RBAC](/th/platform/rbac) สำหรับโมเดล catalog/role/assignment และ walkthrough ของ login; จนถึง 2026-06-10 สิ่งนี้เคยเป็น enum `platform_role` ค่าเดี่ยวบน row ของ user ซึ่งถูกถอดออกแล้ว
- **Avatar** — เก็บเป็น `avatar_file_token` บน `tb_user_profile`; API resolve เป็น string `avatar_url` แบบ presigned บน response ของ list และ detail คอลัมน์นำหน้าของ list, avatar ซ้อนใน "Recently added" ของแถบ Directory และการ์ด `UserIdentityHero` ต่างก็ render avatar วงกลมพร้อม fallback เป็นอักษรย่อ (ตัวอักษรแรกของ `firstname`+`lastname`) และวางรูปจริงทับเมื่อมี `avatar_url` โดยซ่อนอีกครั้งเมื่อโหลดรูปไม่สำเร็จ `tb_user_profile` ยังมีคอลัมน์ `signature_file_token` เพิ่มมาด้วย (ดู [Data Model](/th/platform/users/data-model) §2.4) แต่ยังไม่มี UI ใดใช้งาน
- **Display name** — คอลัมน์ Name ของ list ประกอบโดย helper `getNameDisplay`: เมื่อ `firstname`/`middlename`/`lastname` ตัวใดตัวหนึ่งมีค่า ส่วนที่ไม่ว่างจะถูกต่อกันด้วยช่องว่าง; ไม่เช่นนั้นจะแสดง field `name` แบบ flat โดย fallback เป็น `-`
- **คอลัมน์จำนวน BU** — หน้า list ตอนนี้แสดงจำนวน active/total ของการ assign business unit ต่อ user (ไอคอน `Building2` จำนวน active สีเขียวทับจำนวนรวมสีเทา) มาจาก array `business_unit` เดียวกับที่แถบ Directory ใช้นับ BU ที่แตกต่างกันทั้งประชากร
- **Cluster assignment (`tb_cluster_user`)** — M:N join ระหว่าง user กับ cluster พร้อม `role` ระดับ cluster เป็น `admin` หรือ `user` หน้า edit user แสดงข้อมูลนี้แบบ read-only ซ้อนอยู่ในการ์ด `UserAccessTree` การแก้ไขทำจากส่วน Users บนหน้า edit cluster ผู้ใช้ต้องเป็นสมาชิก cluster ก่อน ถึงจะถูกเพิ่มเข้า BU ใต้ cluster นั้น
- **BU assignment** — M:N join ระหว่าง user กับ business unit พร้อม `role` ระดับ BU ของตัวเอง (`admin` หรือ `user` จากค่าคงที่ `BU_ROLES`), flag `is_active` และ flag `is_default` หน้า edit user คือจุดมาตรฐาน ในการเพิ่ม/ลบ row เหล่านี้ dialog **Add BU** กรอง BU ที่เลือกได้ให้ เหลือเฉพาะ BU ที่อยู่ใน cluster ที่ user เป็นสมาชิกอยู่แล้ว
- **Active flag (`is_active`)** — toggle ว่า user login ได้หรือไม่ เป็นอิสระจาก soft-delete; user ที่ active อาจกำลังจะถูกลบ และ user ที่ inactive อาจถูกเก็บไว้เพื่อ audit ก่อนลบ
- **Soft delete vs. hard delete** — เมนู action ระดับ row มีให้ทั้งสอง แบบ แต่ละตัวห่อด้วย `<Can permission="user.delete">` soft delete ตั้งค่า `deleted_at`/`deleted_by_name`; หน้า list จะซ่อน row เหล่านี้ เว้นแต่จะเปิด filter "Show soft-deleted users" และจะมี badge "Deleted" สีแดง (tooltip ระบุชื่อผู้ลบผ่าน `deleted_by_name`) พร้อมคอลัมน์ "Deleted By" ส่วน hard delete ลบถาวร มี dialog เพิ่มเติมบังคับให้ operator พิมพ์ username/email ตรง ๆ เพื่อยืนยัน **ใหม่: มีเวอร์ชัน bulk ของทั้งสอง สำหรับ super-admin เท่านั้น** (`isSuperAdmin` ไม่ใช่ permission key แบบ `user.*`) — checkbox ของแถวปรากฏเฉพาะ session super-admin toolbar ที่เลือกไว้เสนอ bulk Delete (confirm ธรรมดา) และ bulk Hard Delete (อยู่หลังรหัส 6 ตัวอักษรแบบสุ่มที่ต้องพิมพ์ซ้ำ ต่างจาก flow ทีละคนที่ต้องพิมพ์ exact username) แต่ละครั้งยิง request หนึ่งครั้งต่อ user ที่เลือก (`Promise.allSettled`) พร้อม toast สรุปผลรวม
- **Keycloak sync** — `userService.fetchKeycloakUsers()` ถูกเปิดเผย เป็นปุ่ม header บนหน้า list ตอนนี้ gate ด้วย `user.create` refresh user list ของแพลตฟอร์มจาก Keycloak; หน้า reload ตารางและแถบสรุป Directory หลัง sync สำเร็จ
- **Admin password reset** — header ของหน้า edit มี action **Change Password** ที่เปิด dialog ขอ new + confirm (อย่างน้อย 6 ตัวอักษร และ ต้องตรงกัน) submit ไป `userService.resetPassword(id, newPassword)` surface นี้ไม่มี flow email-link — reset เป็น admin-initiated และ ทำทันที
- **Optimistic concurrency (`doc_version`)** — `tb_user` และ `tb_user_profile` ต่างมี counter `doc_version` (เพิ่มเมื่อ 2026-07-16 ทั้ง 35 ตารางของ platform) `UserEdit` จะส่งค่านี้กลับไปทุกครั้งที่ `PUT`; การบันทึกที่ล้าหลังจะถูกปฏิเสธด้วย `409` และแสดง toast แจ้ง conflict + โหลดใหม่แทนที่จะเขียนทับแบบเงียบ ๆ

## 4. บทบาทและ Persona

route ทั้งสามของ user ห่อด้วย `PrivateRoute` พร้อม prop `requiredPermission` — ยืนยันจากการอ่าน `../carmen-platform/src/App.tsx` (block ของ route บรรทัด 152–174) — และรายการ "Users" ใน sidebar (กลุ่ม Organization, `Layout.tsx` บรรทัด 56) filter ด้วย key `user.read` ตัวเดียวกัน mutation ภายในหน้าถูกห่อเพิ่มด้วย gate `<Can>` หรือ (สำหรับสอง action ของ BU ใน access tree) boolean ที่มาจาก permission ที่คำนวณใน `UserEdit.tsx` (`canAddBU`) หรือ `<Can>` ตรงบนแถว (`UserAccessTree.tsx`) ต่างจากหน้า Clusters และ Business Units ตรงที่ route/header/row gate ไม่ส่ง `clusterId` — แต่สอง action ของ BU-assignment ใน `UserAccessTree` ตอนนี้ resolve กับ `cluster.update` ที่ scope ต่อ cluster แล้ว (เป็นการแก้ไขจาก sync ก่อนหน้า)

| Surface | Gate |
|---|---|
| `/users` (list) | route guard `user.read` |
| `/users/new` (create) | route guard `user.create` |
| `/users/:id/edit` (view/edit) | route guard `user.update` |
| Add User (header ของ list + empty state) | `<Can permission="user.create">` |
| Fetch Keycloak (header ของ list) | `<Can permission="user.create">` — **แก้ไขจาก sync ก่อนหน้า** ซึ่งไม่เคยบันทึกว่าถูก gate |
| Row action: Edit | `<Can permission="user.update">` |
| Row action: Delete + Hard Delete | `<Can permission="user.delete">` |
| Bulk Delete / Bulk Hard Delete (list, checkbox ของแถว) | `isSuperAdmin` เท่านั้น — ไม่ใช่ permission key แบบ `user.*` |
| Toggle Edit (hero ของหน้า edit) | `<Can permission="user.update">` |
| ปุ่ม Add BU (การ์ด Access) | `canAddBU` — `hasPermission('cluster.update', { clusterId })` ข้าม cluster ที่ user เป็นสมาชิกเอง **ไม่ใช่** แค่ "มี cluster อยู่บ้าง" (บั๊กเดิมที่เอา data condition มาใช้แทน permission check ได้รับการแก้ไขแล้ว) |
| Remove BU (ไอคอนถังขยะ, การ์ด Access) | `<Can permission="cluster.update" clusterId={cluster_id ของ BU เอง}>` — scope กับ cluster ของ BU เอง ไม่ใช่ของผู้ดู |

สิ่งที่ไม่ถูก gate ภายในหน้า (มองเห็นได้สำหรับทุกคนที่ผ่าน route guard): **Export** และ **Change Password** สำหรับสิ่งเหล่านี้ การบังคับใช้ฝั่ง backend คือขอบเขตที่แท้จริง สังเกตว่า key `user.*` gate เฉพาะ CRUD ของบัญชีเท่านั้น; การ assign role/scope ถูก gate ด้วย key `user_platform.*` แยกต่างหากบนหน้าจอของ [RBAC](/th/platform/rbac)

| Persona | Key ที่มักถือ | งานที่ทำที่นี่บ่อย |
|---|---|---|
| วิศวกร support ของ Carmen / admin ฝั่งลูกค้า | `user.read` + `user.create`/`user.update`/`user.delete` | Onboard user ลูกค้าใหม่, reset รหัสผ่าน, อัพเดทข้อมูล contact ของพนักงาน, จัดการ roster ของ BU |
| Auditor แบบอ่านอย่างเดียว | `user.read` เท่านั้น | เปิดดูได้แค่หน้า list — ลิงก์ username ชี้ไป `/users/:id/edit` ซึ่ง route guard `user.update` block ด้วย `Forbidden` (ไม่มี route detail แบบ read-only); Add User, Edit/Delete ของ row และ toggle Edit จะไม่ render |

## 5. โมดูลที่เกี่ยวข้อง

- [business-units](/th/platform/business-units) — supply BU ที่ปรากฏในการ์ด Access ของ user; assignment ที่สร้างที่นี่จะปรากฏบนการ์ด Users ของ BU เอง ทั้งสองหน้าแก้ไข BU-user join เดียวกันด้วย `BU_ROLES` (`admin`/`user`) และ flag `is_default` เดียวกัน
- [clusters](/th/platform/clusters) — supply cluster ที่ปรากฏในการ์ด Access ของ user (read-only ที่นี่) หน้า edit cluster คือจุดมาตรฐานในการเพิ่ม/ลบ row `tb_cluster_user` โมดูล Users ใช้สมาชิกภาพ cluster ปัจจุบันเพื่อจำกัด dropdown ในการ assign BU จึงต้องให้สิทธิ์ cluster จากฝั่ง cluster ก่อน
- [rbac](/th/platform/rbac) — เป็นเจ้าของฝั่งสิทธิ์เข้าถึงของ user: catalog ของ permission, role, scoped assignment (`/platform/user-platform`), flag super-admin และ gate effective-permissions ตอน login โมดูล Users สร้างตัวบัญชี; RBAC ตัดสินว่าบัญชีทำอะไรได้
- [profile](/th/platform/profile) — มุมมองบุคคลที่หนึ่งของ user record เดียวกัน — เมนู avatar มีลิงก์ "Profile" ไปที่นั่น โมดูล Users คือมุมมอง admin มุมที่สาม โมดูล Profile คือ row เดียวกันที่เจ้าของดูเอง

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — การต่อสาย `PrivateRoute` (block ของ route บรรทัด 152–174); key `requiredPermission` คือ `user.read`/`user.create`/`user.update` บน user route ทั้งสาม (`SITEMAP.md` ใน repo เดียวกันยังแสดง row "Authenticated" ก่อนยุค RBAC และตามหลังโค้ด)
- `../carmen-platform/src/pages/UserManagement.tsx` และ `userManagement/UserDirectorySummary.tsx` — หน้า list: แถบสรุป Directory, คอลัมน์ avatar พร้อม fallback อักษรย่อ, `getNameDisplay`, คอลัมน์จำนวน BU, filter status/show-deleted, ส่งออก CSV, `<Can>`-gated Fetch Keycloak/Add/Edit/Delete, dialog delete/hard-delete ทั้งแบบเดี่ยวและ bulk (super-admin), การ flatten ของ `audit` แบบ nested
- `../carmen-platform/src/pages/UserEdit.tsx` และ `userEdit/{UserIdentityHero,UserAccessTree}.tsx` — หน้า create/view/edit: การ์ด hero, การ์ด User Details + การ์ด Access ที่รวมกันแล้ว, `<Can permission="user.update">` บน toggle Edit, การตรวจ permission `canAddBU`/scoped-Remove, dialog Add BU, dialog Change Password, การเดินสาย `doc_version`, ค่าคงที่ `BU_ROLES`, interface `UserFormData` (7 ฟิลด์)
- `../carmen-platform/src/utils/docVersion.ts` — helper optimistic-lock
- `../carmen-platform/src/services/userService.ts` — REST client (`/api-system/user`), `fetchKeycloakUsers`, `resetPassword`, `delete`, `hardDelete`
- `../carmen-platform/src/components/Can.tsx` และ `src/context/AuthContext.tsx` — component gate ภายในหน้า และ resolver `hasPermission` ที่อยู่เบื้องหลังทุก gate ข้างต้น

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/users/data-model) — field ของ entity user (รวม `doc_version`), ส่วนขยาย profile (ชื่อแบ่งส่วน, `avatar_file_token`, `signature_file_token`), join `tb_cluster_user` และ BU-user join พร้อม role ระดับ BU และ flag `is_default` (stub — ยังไม่สมบูรณ์)
- [Lifecycle](/th/platform/users/lifecycle) — flow การ create, gate effective-permissions ตอน sign-in, activate/deactivate ผ่าน `is_active`, soft vs. hard delete (รวม bulk แบบ super-admin เท่านั้น), password reset ที่ admin เป็นผู้ทำ, sync จาก Keycloak (stub — ยังไม่สมบูรณ์)
- [UI Screens](/th/platform/users/ui-screens) — หน้า list `UserManagement` พร้อมแถบ Directory, คอลัมน์ avatar, คอลัมน์จำนวน BU, filter, bulk action และปุ่ม sync Keycloak และเลย์เอาต์ hero + Access-tree ของ `UserEdit` รวมถึง dialog Add BU และ dialog Change Password (stub — ยังไม่สมบูรณ์)
