---
title: Platform RBAC — หน้าจอ UI (UI Screens)
description: RoleManagement/RoleEdit พร้อม PermissionPicker, Permission Catalog แบบ read-only, รายการ Super Admins และหน้าจอ assignment ของ User Platform
published: true
date: 2026-06-10T15:00:00.000Z
tags: book/platform, rbac, ui
editor: markdown
dateCreated: 2026-06-10T15:00:00.000Z
---

# Platform RBAC — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `RoleManagement` (`/platform/roles`) · `RoleEdit` (`/platform/roles/new`, `/platform/roles/:id/edit`) · `PermissionCatalog` (`/platform/permissions`) · `SuperAdminManagement` (`/platform/super-admins`) · `UserPlatformManagement` (`/platform/user-platform`) · `UserPlatformEdit` (`/platform/user-platform/:userId`) &nbsp;·&nbsp; **รูปแบบมาตรฐาน:** list ของ Roles และ User Platform ใช้ `DataTable` แบบ server-side; Catalog และ Super Admins แตกต่างออกไป (card / row ธรรมดา) &nbsp;·&nbsp; **Component หลัก:** `PermissionPicker` แบบ accordion จัดกลุ่มตาม resource &nbsp;·&nbsp; **Gate ภายในหน้า:** `<Can permission="user_platform.manage">` บนหน้า detail เท่านั้น

## 1. ภาพรวม

สองในสี่ surface ทำตามรูปแบบ Management/Edit มาตรฐานของ Platform SPA: **Roles** (list แบบ `DataTable` ฝั่ง server พร้อมการค้นหาแบบ debounce, filter แบบ Sheet, ส่งออก CSV, จดจำสถานะใน `localStorage` รวมถึงหน้า create/view/edit แบบสองการ์ด) และ **User Platform** (list shape แบบ `DataTable` เดียวกัน แต่ไม่มี route สำหรับ create — ผู้ใช้ถูกสร้างในโมดูล Users และหน้า "edit" จัดการ role assignment ไม่ใช่ field ของเอนทิตี)

อีกสองตัวจงใจแตกต่าง **Permission Catalog** เป็นหน้าอ้างอิงแบบ read-only: grid ของ card แบบ responsive จัดกลุ่มตาม resource ไม่มีตาราง ไม่มี mutation เข้าถึงได้จากปุ่ม header บนหน้า list ของ Roles เท่านั้น (ไม่มีรายการใน sidebar) ส่วน **Super Admins** เป็นหน้าสองการ์ด — ฟอร์ม add และ list แบบ row ธรรมดา — ไม่มี `DataTable` ไม่มีการค้นหา และไม่มีการแบ่งหน้า; ประชากรที่คาดไว้คือ row เพียงหยิบมือ

ทั้งหกหน้าจอมาพร้อม **Debug Sheet** เฉพาะ dev ของ SPA — ปุ่มลอยสีเหลืองอำพัน (มุมขวาล่าง) ที่เปิด JSON ดิบของ API response ของหน้าจอนั้น (เฉพาะ `import.meta.env.DEV` ไม่มีใน production build) บน `RoleEdit` มีสอง tab คือ Role และ Catalog เปิดเผย payload ของทั้งสอง endpoint — เป็นวิธีที่เร็วที่สุดสำหรับ QA ในการตรวจสอบการซ้อนของ envelope และ shape ของ audit จริง ๆ ตามที่อธิบายด้านล่าง

## 2. Roles

### 2.1 `RoleManagement` — list (`/platform/roles`)

แถว header: title "Roles" / subtitle "Manage platform roles and their permissions" และ header action สามตัวจากซ้ายไปขวา — **Permission Catalog** (นำทางไป `/platform/permissions`), **Export** (CSV ฝั่ง client ของหน้าที่โหลดอยู่: Name, Description, Permissions, Active; ไฟล์ `roles-<YYYY-MM-DD>.csv`; disable ขณะกำลังโหลดหรือว่างเปล่า) และ **Add Role** (นำทางไป `/platform/roles/new`)

ด้านล่างคือแถวค้นหาและ filter มาตรฐาน: input ค้นหาแบบ debounce (400 ms) เหนือ `name`/`description` และ Sheet **Filters** ที่มีกลุ่ม Status กลุ่มเดียว (ปุ่ม toggle Active / Inactive → query `advance` `{ where: { is_active } }` เมื่อเลือกเพียงค่าเดียว) chip ของ filter ที่ active แสดงใต้แถวค้นหา

คอลัมน์ของ `DataTable` ตามลำดับ:

| คอลัมน์ | การ render |
|---|---|
| Name | คลิกได้ — นำทางไป `/platform/roles/:id/edit` |
| Description | ข้อความสีจาง แสดง `-` เมื่อว่าง |
| Permissions | `permission_count` เป็น badge รอง (`0` เมื่อไม่มีค่า); sort ไม่ได้ |
| Status | badge Active/Inactive จาก `is_active` |
| Created | `created_at` (`YYYY-MM-DD HH:mm:ss` ตามเวลาท้องถิ่นของ browser) + `created_by_name` บรรทัดถัดไป — flatten จาก shape ซ้อน `audit.created` `{ at, name }` เมื่อ API ซ้อนมา |
| Updated | shape เดียวกันจาก `audit.updated`; render `-` เมื่อ `updated_at === created_at` |
| Actions | dropdown `⋯`: **Edit** (นำทาง) และ **Delete** (เปิด `ConfirmDialog` แบบ destructive; เมื่อยืนยันเรียก `DELETE /api-system/platform/roles/:id`) |

เมื่อชุดผลลัพธ์ว่างเปล่า ตารางถูกแทนด้วยการ์ด `EmptyState` ("No roles yet" พร้อม CTA Add Role แบบ inline เมื่อไม่มี search term หรือข้อความ `No roles matching "<term>"` เมื่อมี) sort เริ่มต้นคือ `created_at:desc` สถานะ UI ที่จดจำไว้:

| Key ใน `localStorage` | ชนิดที่เก็บ | จดจำอะไร |
|---|---|---|
| `search_roles` | string | search term |
| `filters_roles` | JSON string array | การเลือก filter Status |
| `page_roles` | number string | หน้าปัจจุบัน |
| `perpage_roles` | number string | ขนาดหน้า |
| `sort_roles` | string | Sort (`column:dir`) |

### 2.2 `RoleEdit` — โหมด create (`/platform/roles/new`)

Title "New Role" grid responsive สองการ์ด (`lg:grid-cols-2`): **Role Details** (ซ้าย) และ **Permissions** (ขวา) ฟอร์มแก้ไขได้ทันที Role Details มี `name` (จำเป็น validate ตอน blur และก่อน submit), `description` (textarea) และ checkbox `is_active` (ติ๊กไว้เป็นค่าเริ่มต้น) การ์ด Permissions เป็นที่อยู่ของ `PermissionPicker` (§2.4); catalog ถูก fetch ตอน mount และมี spinner แสดงจนกว่าจะมาถึง

ตอน submit SPA เรียก `POST /api-system/platform/roles` พร้อม `permissions: { add: <key ที่เลือกทั้งหมด> }` เมื่อสำเร็จจะ redirect ไป `/platform/roles/:id/edit` ของ id ที่สร้าง (fallback ไปหน้า list เมื่อ response ไม่มี id)

### 2.3 `RoleEdit` — โหมด view/edit (`/platform/roles/:id/edit`)

โหลดผ่าน `GET /api-system/platform/roles/:id` และเริ่มต้นแบบ **read-only**: field ของ Role Details render เป็นข้อความนิ่ง Status เป็น badge และการ์ด Permissions แสดง key ที่มอบไว้จัดกลุ่มตาม prefix ของ resource เป็น badge แบบ monospace (หรือ "No permissions granted.") ปุ่ม **Edit** ใน header สลับทั้งสองการ์ดเป็นแก้ไขได้; Cancel คืนค่า snapshot ก่อนแก้ไข การเปลี่ยนแปลงที่ยังไม่บันทึก trigger navigation guard `useUnsavedChanges` และ shortcut ระดับ global ใช้ save (`formRef.requestSubmit`) และ cancel ได้

การบันทึกคำนวณ **permission delta** เทียบกับชุด key ที่จับไว้ตอน fetch — `add` = ถูกเลือกแต่ไม่อยู่ในชุดเดิม, `remove` = อยู่ในชุดเดิมแต่ไม่ถูกเลือก — แล้วส่ง `PUT /api-system/platform/roles/:id` พร้อม `permissions: { add, remove }` หลังบันทึกสำเร็จหน้าจะ refetch role และกลับสู่โหมด view

### 2.4 `PermissionPicker`

Component ที่ใช้ร่วมกัน (`src/components/PermissionPicker.tsx`) render catalog เป็น accordion แบบ `<details>` native หนึ่งกลุ่มต่อ `resource` ตามลำดับใน catalog header ของแต่ละกลุ่มแสดงชื่อ resource, badge นับจำนวนที่เลือก `n/m` (เมื่อ n > 0) และลิงก์ toggle **Select all / Clear all**; กลุ่มที่มีการเลือกใด ๆ จะเริ่มต้นแบบขยาย ภายใน checkbox เรียง 2–3 ตัวต่อแถวและมี label เป็น segment ของ `action` เท่านั้น — `description` ฉบับเต็มปรากฏเป็น tooltip ตอน hover (attribute `title`)

## 3. Permission Catalog

`PermissionCatalog` (`/platform/permissions`) เป็นหน้าอ้างอิงแบบ read-only ของ key ทุกตัวใน catalog โหลดครั้งเดียวผ่าน `GET /api-system/platform/permissions` header: ลูกศรย้อนกลับไป `/platform/roles`, title "Permission Catalog", subtitle "Read-only reference of all platform permissions"

เนื้อหาเป็น grid ของ card แบบ responsive (2 คอลัมน์ที่ `sm`, 3 ที่ `lg`) หนึ่ง card ต่อ resource โดยรักษาลำดับของ catalog แต่ละ card แสดง permission ของมันเป็น outline badge แบบ monospace พร้อม key `resource.action` ฉบับเต็ม และ `description` เป็นข้อความสีจางด้านล่างเมื่อมี ไม่มีปุ่ม ไม่มีการค้นหา ไม่มี filter และไม่มี affordance ของการ mutation ใด ๆ — catalog เป็นข้อมูลที่ backend เป็นเจ้าของ catalog ที่ว่างเปล่า render เป็น `EmptyState` ("No permissions") หน้าจอนี้ **ไม่มีรายการใน sidebar**; เส้นทางนำทางเข้ามามีเพียงปุ่ม header ของหน้า Roles และ URL โดยตรงเท่านั้น

## 4. Super Admins

`SuperAdminManagement` (`/platform/super-admins`) render เป็นการ์ดสองใบวางซ้อนกัน — ไม่ใช่ `DataTable`:

- **Add Super Admin** — `<select>` แบบ native บวกปุ่ม **Add** dropdown ถูกป้อนโดย `userService.getAll({ perpage: 200, sort: 'created_at:desc' })` และ **ตัดผู้ใช้ที่เป็น super admin อยู่แล้วออก** label ของ option ประกอบจาก `firstname middlename lastname (email)` โดย fallback เป็น email/name/id Add เรียก `POST /api-system/platform/super-admins` พร้อม `{ user_id }` แล้ว refetch
- **Current Super Admins** — badge นับจำนวนใน title ของการ์ดและ list แบบ row ที่มีเส้นแบ่ง แต่ละ row แสดงชื่อแสดงผลที่ resolve แล้ว (ผ่าน user map เดียวกัน), `user_id` ดิบแบบ monospace, "Added: `<created_at>`", badge Active/Inactive (`is_active !== false` render เป็น Active) และปุ่มไอคอนถังขยะแบบ destructive การถอดออกเปิด `ConfirmDialog` เตือนว่าผู้ใช้ "will no longer bypass permission checks" จากนั้นเรียก `DELETE /api-system/platform/super-admins/:id` ด้วย **id ของ flag-row** ไม่ใช่ id ของผู้ใช้

response ของ list อาจซ้อน envelope `{ data }` หลายชั้น; หน้านี้ไล่ลงด้วย helper `extractArray` ระดับ local จนเจอ array ไม่มีการจดจำสถานะ UI ลง `localStorage`

## 5. User Platform

### 5.1 `UserPlatformManagement` — list (`/platform/user-platform`)

header: title "User Platform" / subtitle "Assign platform roles and scope to users" พร้อม action เดียวคือ **Export** (CSV: Username, Name, Email, Status; ไฟล์ `user-platform-<YYYY-MM-DD>.csv`) จงใจ **ไม่มีปุ่ม Add** — หน้าจอนี้ list ผู้ใช้ที่มีอยู่ (`GET /api-system/user` ผ่าน `userService.getAll`); การสร้างผู้ใช้เป็นของโมดูล [users](/th/platform/users)

การค้นหา (debounce 400 ms) และ Sheet ของ filter Status เหมือนหน้า list ของ Roles คอลัมน์:

| คอลัมน์ | การ render |
|---|---|
| Username | คลิกได้ — นำทางไป `/platform/user-platform/:userId` |
| Name | ประกอบจาก `firstname middlename lastname` (filter แล้วต่อด้วยช่องว่าง) fallback เป็น `name` แล้วจึง `-` |
| Email | ข้อความธรรมดา |
| Status | badge Active/Inactive |
| Roles | badge นับจำนวน assignment **fetch ต่อ row ใน background** หลังหน้าโหลดแล้ว — เป็น N+1 ของการเรียก `userRoleService.list(userId)`; spinner เล็ก ๆ render จนกว่าแต่ละ count จะ resolve (กรณีล้มเหลวนับเป็น `0`); sort ไม่ได้ |
| Created / Updated | shape audit แบบ flatten เดียวกับหน้า list ของ Roles; Updated ถูกซ่อนเมื่อเท่ากับ Created |

สถานะ UI ที่จดจำไว้: `search_user_platform`, `status_filters_user_platform`, `page_user_platform`, `perpage_user_platform`, `sort_user_platform`

### 5.2 `UserPlatformEdit` — detail (`/platform/user-platform/:userId`)

header: ลูกศรย้อนกลับไปหน้า list, ชื่อที่ resolve แล้วของผู้ใช้ (`firstname lastname` fallback เป็น username/id) และ email ตัวหน้าเป็นการ์ด **Roles & Scope** ใบเดียว list assignment ของผู้ใช้ (`GET /api-system/platform/users/:userId/roles` ไล่ลง envelope `{ data }` ที่ซ้อนกัน) แต่ละ row ของ assignment แสดงชื่อ role (fallback เป็น `role_id`) และ badge ของ scope — ชื่อของ cluster (resolve กับ cluster list, fallback เป็น `cluster_id` ดิบ) สำหรับ row ที่ scope ระดับ cluster หรือ "Platform" ในกรณีอื่น — บวกปุ่มไอคอน remove

affordance ที่ mutate ถูก gate ด้วย `<Can permission="user_platform.manage">`: ปุ่ม header **Add Role**, ฟอร์ม add-role แบบ inline และปุ่ม remove ของแต่ละ row render เฉพาะกับผู้ถือ key นั้น viewer ที่มีเพียง `user_platform.read` เห็นการ์ดเดียวกันแบบ read-only ทั้งหมด

### 5.3 ฟอร์ม add-role และการถอดออก

คลิก **Add Role** เผยฟอร์ม inline (ไม่มี dialog): select **Role** ป้อนโดย `roleService.getAll({ perpage: 200, sort: 'name:asc' })`, select **Scope** ที่มีสองตัวเลือก — `Platform` และ `Specific cluster` — และเมื่อเลือก scope ระดับ cluster จะมี select **Cluster** ป้อนโดย `clusterService.getAll({ perpage: 200, sort: 'name:asc' })` การ submit จะ validate ว่าเลือก role แล้ว (และสำหรับ scope ระดับ cluster ต้องเลือก cluster ด้วย) จากนั้นเรียก `POST /api-system/platform/users/:userId/roles` พร้อม `{ role_id, scope }` โดย `scope` เป็น discriminated union (`{ type: 'platform' }` หรือ `{ type: 'cluster', cluster_id }`) แล้ว refetch list ของ assignment

การถอดออกเปิด `ConfirmDialog` ที่ระบุชื่อ role จากนั้นเรียก `DELETE /api-system/platform/users/:userId/roles/:assignmentId` ด้วย id ของ assignment-row หน้า detail ไม่จดจำสถานะ UI ใด ๆ

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — การลงทะเบียน route ของทั้งหกหน้าจอ (บรรทัด 236–291)
- `../carmen-platform/src/pages/RoleManagement.tsx` — คอลัมน์ของ list, การ flatten audit, ส่งออก CSV, key ที่จดจำไว้, confirm ตอนลบ
- `../carmen-platform/src/pages/RoleEdit.tsx` — เลย์เอาต์สองการ์ด, การสลับ view/edit, การคำนวณ permission delta (บรรทัด 174–187)
- `../carmen-platform/src/components/PermissionPicker.tsx` — picker แบบ accordion จัดกลุ่มตาม resource
- `../carmen-platform/src/pages/PermissionCatalog.tsx` — grid card ของ resource แบบ read-only
- `../carmen-platform/src/pages/SuperAdminManagement.tsx` — การ์ด add/remove, การไล่ลง envelope ด้วย `extractArray`, การตัด option ของผู้ใช้
- `../carmen-platform/src/pages/UserPlatformManagement.tsx` — คอลัมน์ของ list, การนับ roles ต่อ row ใน background (N+1), key ที่จดจำไว้
- `../carmen-platform/src/pages/UserPlatformEdit.tsx` — การ์ด Roles & Scope, gate `<Can>`, ฟอร์ม add-role, การ resolve badge ของ scope
- `../carmen-platform/src/components/Can.tsx` — wrapper สำหรับ render ที่ gate ด้วย permission

**Cross-link:** [หน้า landing ของ Platform RBAC](/th/platform/rbac) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
