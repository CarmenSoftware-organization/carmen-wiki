---
title: Platform RBAC — หน้าจอ UI (UI Screens)
description: RoleManagement/RoleEdit พร้อม PermissionPicker และ RolesAccessSummary, Permission Catalog แบบ read-only, หน้า Super Admins ที่เขียนใหม่เป็น DataTable และหน้าจอ assignment ของ User Platform
published: true
date: 2026-07-29T00:00:00.000Z
tags: book/platform, rbac, ui
editor: markdown
dateCreated: 2026-06-10T15:00:00.000Z
---

# Platform RBAC — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `RoleManagement` (`/platform/roles`) · `RoleEdit` (`/platform/roles/new`, `/platform/roles/:id/edit`) · `PermissionCatalog` (`/platform/permissions`) · `SuperAdminManagement` (`/platform/super-admins`) · `UserPlatformManagement` (`/platform/user-platform`) · `UserPlatformEdit` (`/platform/user-platform/:userId`) &nbsp;·&nbsp; **รูปแบบมาตรฐาน:** Roles, Super Admins (ตั้งแต่ 2026-07) และ User Platform ใช้ `DataTable` แบบ server-side ทั้งหมด; มีเพียง Permission Catalog ที่แตกต่างออกไป (grid card แบบ read-only) &nbsp;·&nbsp; **Component หลัก:** `PermissionPicker` แบบ accordion จัดกลุ่มตาม resource &nbsp;·&nbsp; **Gate ภายในหน้า:** list/edit ของ Roles gate Add/Edit/Delete และ toggle Edit (เพิ่มมาตั้งแต่ 2026-06-10); `<Can permission="user_platform.manage">` บนหน้า detail ของ User Platform &nbsp;·&nbsp; **แถบสรุป (ใหม่ตั้งแต่ 2026-07):** `RolesAccessSummary` บนหน้า list ของ Roles, `PlatformAccessSummary` บนหน้า list ของ User Platform

## 1. ภาพรวม

สามในสี่ surface ทำตามรูปแบบ Management/Edit มาตรฐานของ Platform SPA: **Roles** (list แบบ `DataTable` ฝั่ง server พร้อมการค้นหาแบบ debounce, filter แบบ Sheet, ส่งออก CSV, แถบสรุป `RolesAccessSummary` รวมถึงหน้า create/view/edit ที่นำด้วยการ์ด `RoleIdentityHero`), **User Platform** (list shape แบบ `DataTable` เดียวกันบวกแถบสรุป `PlatformAccessSummary` แต่ไม่มี route สำหรับ create — ผู้ใช้ถูกสร้างในโมดูล Users และหน้า "edit" จัดการ role assignment ไม่ใช่ field ของเอนทิตี) และ **Super Admins** ซึ่ง **ถูกเขียนใหม่เมื่อ 2026-07** — ไม่ใช่ layout สองการ์ดที่ sync ครั้งก่อนอธิบายไว้อีกต่อไป ตอนนี้เป็น `DataTable` (ค้นหาได้ ไม่มี filter) โดยย้าย action Add ไปเป็น dialog แบบ modal บน header

มีเพียง **Permission Catalog** ที่ยังแตกต่างออกไป: หน้าอ้างอิงแบบ read-only, grid ของ card แบบ responsive จัดกลุ่มตาม resource ไม่มีตาราง ไม่มี mutation เข้าถึงได้จากปุ่ม header บนหน้า list ของ Roles เท่านั้น (ไม่มีรายการใน sidebar)

ทั้งหกหน้าจอมาพร้อม **Debug Sheet** เฉพาะ dev ของ SPA — ปุ่มลอยสีเหลืองอำพัน (มุมขวาล่าง) ที่เปิด JSON ดิบของ API response ของหน้าจอนั้น (เฉพาะ `import.meta.env.DEV` ไม่มีใน production build) บน `RoleEdit` มีสอง tab คือ Role และ Catalog เปิดเผย payload ของทั้งสอง endpoint — เป็นวิธีที่เร็วที่สุดสำหรับ QA ในการตรวจสอบการซ้อนของ envelope และ shape ของ audit จริง ๆ ตามที่อธิบายด้านล่าง

## 2. Roles

### 2.1 `RoleManagement` — list (`/platform/roles`)

แถว header: title "Roles" / subtitle "Manage platform roles and their permissions" และ header action สามตัวจากซ้ายไปขวา — **Permission Catalog** (นำทางไป `/platform/permissions`), **Export** (CSV ฝั่ง client ของหน้าที่โหลดอยู่: Name, Description, Permissions, Active; ไฟล์ `roles-<YYYY-MM-DD>.csv`; disable ขณะกำลังโหลดหรือว่างเปล่า) และ **Add Role** (นำทางไป `/platform/roles/new`, ห่อด้วย `<Can permission="role.create">` — **เพิ่มมาตั้งแต่ 2026-06-10** เดิมไม่ถูก gate)

**เพิ่มมาตั้งแต่ 2026-06-10:** ใต้ header มีแถบ **`RolesAccessSummary`** (`roleManagement/RolesAccessSummary.tsx`) — การ์ดแสดงจำนวน role รวม (แยก active/inactive) บวกสาม role ที่มีขอบเขต permission กว้างที่สุด แต่ละตัวแสดงชื่อ + แท่งแนวนอน (scale ตาม `permission_count` ของ role ที่กว้างที่สุด) + จำนวน มันโหลดเป็นอิสระจากตาราง (`perpage: -1` ไม่สนใจ filter ของตาราง) และมีสถานะ skeleton/error/retry ของตัวเอง

ด้านล่างคือแถวค้นหาและ filter มาตรฐาน: input ค้นหาแบบ debounce (400 ms) เหนือ `name`/`description` และ Sheet **Filters** ที่มีกลุ่ม Status กลุ่มเดียว (ปุ่ม toggle Active / Inactive → query `advance` `{ where: { is_active } }` เมื่อเลือกเพียงค่าเดียว) chip ของ filter ที่ active แสดงใต้แถวค้นหา

คอลัมน์ของ `DataTable` ตามลำดับ:

| คอลัมน์ | การ render |
|---|---|
| Name | ลิงก์คลิกได้ — นำทางไป `/platform/roles/:id/edit` — พร้อม `description` ของ role เป็นข้อความสีจางด้านล่าง (**รวมเข้าคอลัมน์นี้แล้ว ไม่มีคอลัมน์ Description แยกต่างหาก**) |
| Permissions | `permission_count` เป็น badge รอง (`0` เมื่อไม่มีค่า); sort ไม่ได้ |
| Status | badge Active/Inactive จาก `is_active` |
| Created | `created_at` (`YYYY-MM-DD HH:mm:ss` ตามเวลาท้องถิ่นของ browser) + `created_by_name` บรรทัดถัดไป — flatten จาก shape ซ้อน `audit.created` `{ at, name }` เมื่อ API ซ้อนมา |
| Updated | shape เดียวกันจาก `audit.updated`; render `-` เมื่อ `updated_at === created_at` |
| Actions | dropdown `⋯`: **Edit** (นำทาง; `<Can permission="role.update">` — **เพิ่มมาตั้งแต่ 2026-06-10**) และ **Delete** (เปิด `ConfirmDialog` แบบ destructive; เมื่อยืนยันเรียก `DELETE /api-system/platform/roles/:id`; `<Can permission="role.delete">` — **เพิ่มมาตั้งแต่ 2026-06-10**) session ที่มีเพียง `role.read` ตอนนี้เห็น dropdown ว่างเปล่า เหมือน management list อื่น ๆ ทุกหน้าใน SPA |

เมื่อชุดผลลัพธ์ว่างเปล่า ตารางถูกแทนด้วยการ์ด `EmptyState` ("No roles yet" พร้อม CTA Add Role แบบ inline — ซึ่ง gate ด้วย `<Can permission="role.create">` เช่นกัน — เมื่อไม่มี search term หรือข้อความ `No roles matching "<term>"` เมื่อมี) sort เริ่มต้นคือ `created_at:desc` สถานะ UI ที่จดจำไว้:

| Key ใน `localStorage` | ชนิดที่เก็บ | จดจำอะไร |
|---|---|---|
| `search_roles` | string | search term |
| `filters_roles` | JSON string array | การเลือก filter Status |
| `page_roles` | number string | หน้าปัจจุบัน |
| `perpage_roles` | number string | ขนาดหน้า |
| `sort_roles` | string | Sort (`column:dir`) |

### 2.2 `RoleEdit` — เลย์เอาต์ (ทั้งสองโหมด เขียนใหม่ตั้งแต่ 2026-06-10)

**เลย์เอาต์ทั้งหน้าเปลี่ยนไป** grid สองการ์ด `lg:grid-cols-2` เดิม (Role Details ซ้าย, Permissions ขวา) หายไปแล้ว ตอนนี้หน้าเปิดด้วยการ์ด **`RoleIdentityHero`** (`roleEdit/RoleIdentityHero.tsx`) — ไอคอนโล่, ชื่อ role (หรือ "(unnamed role)"), badge Active/Inactive และสรุป **ขอบเขต permission** บรรทัดเดียว: "Full access to every permission" (สีอำพันพร้อมสามเหลี่ยมเตือน เมื่อจำนวน key ที่มอบให้ role ถึงขนาดของ catalog), "No permissions granted yet" หรือ "`N` permissions across `M` resources" ปุ่ม **Edit** (เดิม ในโหมด view เท่านั้น) render อยู่ใน action slot ของ hero, gate ด้วย `<Can permission="role.update">`

ใต้ hero ฟอร์มเป็น grid สองคอลัมน์ (`lg:grid-cols-[1fr_minmax(300px,340px)]`) โดย **คอลัมน์สลับตำแหน่งจากเลย์เอาต์เดิม**: **Permissions** ตอนนี้เป็นคอลัมน์ซ้าย/กว้าง (เป็นที่อยู่ของ `PermissionPicker`, §2.6, เมื่ออยู่ในโหมด edit หรือ badge แบบ read-only จัดกลุ่มตาม resource เมื่อไม่ใช่) และ **Settings** — เปลี่ยนชื่อจาก "Role Details" — เป็น rail ขวา/แคบแบบ sticky มี `name` (จำเป็น), `description` (textarea) และ checkbox/badge `is_active`

### 2.3 `RoleEdit` — โหมด create (`/platform/roles/new`)

Title มาจาก hero (ชื่อว่างแสดง "(unnamed role)"); ฟอร์มแก้ไขได้ทันทีตั้งแต่ mount (`editing = true`) — โหมด create ไม่มีปุ่ม Edit ตอน submit SPA เรียก `POST /api-system/platform/roles` พร้อม `permissions: { add: <key ที่เลือกทั้งหมด> }` เมื่อสำเร็จจะ redirect ไป `/platform/roles/:id/edit` ของ id ที่สร้าง (fallback ไปหน้า list เมื่อ response ไม่มี id)

### 2.4 `RoleEdit` — โหมด view/edit (`/platform/roles/:id/edit`)

**Not-found gating (เพิ่มมาตั้งแต่ 2026-06-10):** `id` ที่ผิดหรือถูกลบ render shell เฉพาะแทนฟอร์ม — มีเพียงลิงก์ย้อนกลับและ `EmptyState` ไอคอน `SearchX` ("Role not found", "This role doesn't exist, or it may have been deleted…", ปุ่ม "Back to roles") — ตาม pattern เดียวกับที่เพิ่มใน clusters/business-units/users/applications/report-templates

โหลดผ่าน `GET /api-system/platform/roles/:id` และเริ่มต้นแบบ **read-only**: field ของ Settings render เป็นข้อความนิ่ง/badge และการ์ด Permissions แสดง key ที่มอบไว้จัดกลุ่มตาม prefix ของ resource เป็น badge แบบ monospace (หรือ "No permissions granted.") คลิก **Edit** (ใน hero) สลับเป็นแก้ไขได้; **Cancel** (ใน sticky bar ด้านล่าง, §2.5) คืนค่า snapshot ก่อนแก้ไข การเปลี่ยนแปลงที่ยังไม่บันทึก trigger navigation guard `useUnsavedChanges` และ shortcut ระดับ global ใช้ save (`formRef.requestSubmit`) และ cancel ได้ (เฉพาะเมื่อ `!isNew`)

การบันทึกคำนวณ **permission delta** เทียบกับชุด key ที่จับไว้ตอน fetch — `add` = ถูกเลือกแต่ไม่อยู่ในชุดเดิม, `remove` = อยู่ในชุดเดิมแต่ไม่ถูกเลือก — แล้วส่ง `PUT /api-system/platform/roles/:id` พร้อม `permissions: { add, remove }` บวก **`doc_version` เมื่อทราบค่า (เพิ่มมาตั้งแต่ 2026-06-10)** ความไม่ตรงกันของ version จะ trigger toast `notifyVersionConflict()` ที่ใช้ร่วมกันและ re-fetch แทนที่จะเขียนทับเงียบ ๆ หลังบันทึกสำเร็จหน้าจะ refetch role และกลับสู่โหมด view

### 2.5 Sticky action bar (เพิ่มมาตั้งแต่ 2026-06-10)

Render เฉพาะขณะ `editing = true` ตาม pattern เดียวกับ clusters/business-units/users/applications/report-templates: bar แบบ `fixed bottom-0` มีตัวบ่งชี้การเปลี่ยนแปลงที่ยังไม่บันทึก (จุดสีอำพันกระพริบ + "Unsaved changes" หรือ "No changes" ด้วยข้อความสีจาง) ทางซ้าย และ **Cancel** (ซ่อนในโหมด create; disable ขณะบันทึก) + **Create Role**/**Save Changes** (disable ขณะบันทึก หรือในโหมด edit เมื่อไม่มีการเปลี่ยนแปลง) ทางขวา

### 2.6 `PermissionPicker`

Component ที่ใช้ร่วมกัน (`src/components/PermissionPicker.tsx`) render catalog เป็น accordion แบบ `<details>` native หนึ่งกลุ่มต่อ `resource` ตามลำดับใน catalog header ของแต่ละกลุ่มแสดงชื่อ resource, badge นับจำนวนที่เลือก `n/m` (เมื่อ n > 0) และลิงก์ toggle **Select all / Clear all**; กลุ่มที่มีการเลือกใด ๆ จะเริ่มต้นแบบขยาย ภายใน checkbox เรียง 2–3 ตัวต่อแถวและมี label เป็น segment ของ `action` เท่านั้น — `description` ฉบับเต็มปรากฏเป็น tooltip ตอน hover (attribute `title`)

## 3. Permission Catalog

`PermissionCatalog` (`/platform/permissions`) เป็นหน้าอ้างอิงแบบ read-only ของ key ทุกตัวใน catalog โหลดครั้งเดียวผ่าน `GET /api-system/platform/permissions` header: ลูกศรย้อนกลับไป `/platform/roles`, title "Permission Catalog", subtitle "Read-only reference of all platform permissions"

เนื้อหาเป็น grid ของ card แบบ responsive (2 คอลัมน์ที่ `sm`, 3 ที่ `lg`) หนึ่ง card ต่อ resource โดยรักษาลำดับของ catalog แต่ละ card แสดง permission ของมันเป็น outline badge แบบ monospace พร้อม key `resource.action` ฉบับเต็ม และ `description` เป็นข้อความสีจางด้านล่างเมื่อมี ไม่มีปุ่ม ไม่มีการค้นหา ไม่มี filter และไม่มี affordance ของการ mutation ใด ๆ — catalog เป็นข้อมูลที่ backend เป็นเจ้าของ catalog ที่ว่างเปล่า render เป็น `EmptyState` ("No permissions") หน้าจอนี้ **ไม่มีรายการใน sidebar**; เส้นทางนำทางเข้ามามีเพียงปุ่ม header ของหน้า Roles และ URL โดยตรงเท่านั้น

## 4. Super Admins

**เขียนใหม่ตั้งแต่ 2026-06-10 — ไม่ใช่หน้า "การ์ดสองใบซ้อนกัน ไม่ใช่ `DataTable`" ที่ sync ครั้งก่อนอธิบายไว้อีกต่อไป** `SuperAdminManagement` (`/platform/super-admins`) ตอนนี้เป็นหน้าจอ management รูปแบบมาตรฐาน:

- **Header:** title "Super Admins" / subtitle "Platform users who bypass all permission checks" พร้อมสอง action — **Export** (CSV ฝั่ง client: User, User ID, Status, Added; ไฟล์ `super-admins-<YYYY-MM-DD>.csv`; disable ขณะกำลังโหลดหรือว่างเปล่า) และ **Add Super Admin** ซึ่งตอนนี้เปิด **`Dialog`** แบบ modal แทนที่จะเป็นฟอร์มการ์ด inline
- **Dialog Add Super Admin:** `Select` แบบ shadcn (dropdown ที่ค้นหาได้ ไม่ใช่ `<select>` native) ป้อนโดย `userService.getAll({ perpage: 200, sort: 'created_at:desc' })` และ **ตัดผู้ใช้ที่เป็น super admin อยู่แล้วออก** label ของ option ประกอบจาก `firstname middlename lastname (email)` โดย fallback เป็น email/name/id การยืนยันเรียก `POST /api-system/platform/super-admins` พร้อม `{ user_id }` แล้ว refetch และปิด dialog
- **List:** การ์ดเดียวที่มี input ค้นหาแบบ debounce (filter ฝั่ง client เหนือชื่อแสดงผลที่ resolve แล้วและ `user_id` ดิบ — **เพิ่มมาตั้งแต่ 2026-06-10** เวอร์ชันก่อนไม่มีการค้นหา) และ `DataTable` ที่มีคอลัมน์ **User** (ชื่อแสดงผลที่ resolve แล้ว + `user_id` ดิบแบบ monospace ด้านล่าง), **Status** (badge Active/Inactive, `is_active !== false` render เป็น Active), **Added** (`created_at`) และ **Actions** (dropdown `⋯` พร้อม item **Remove** แบบ destructive — แทนที่ปุ่มไอคอนถังขยะแบบ inline ของเวอร์ชันก่อน) การถอดออกเปิด `ConfirmDialog` เตือนว่าผู้ใช้ "will no longer bypass permission checks" จากนั้นเรียก `DELETE /api-system/platform/super-admins/:id` ด้วย **id ของ flag-row** ไม่ใช่ id ของผู้ใช้

response ของ list อาจซ้อน envelope `{ data }` หลายชั้น; หน้านี้ยังไล่ลงด้วย helper `extractArray` ระดับ local จนเจอ array — ส่วนนี้ของ finding เดิมไม่เปลี่ยนแปลง ไม่มีตัวควบคุมการแบ่งหน้า (ค้นหาฝั่ง client เหนือ list ที่โหลดมาทั้งหมด ไม่มีการแบ่งหน้าฝั่ง server) และไม่มีสถานะ UI อื่นที่จดจำใน `localStorage` นอกจาก search term (`search_super_admins`, เพิ่มมาตั้งแต่ 2026-06-10)

## 5. User Platform

### 5.1 `UserPlatformManagement` — list (`/platform/user-platform`)

header: title "User Platform" / subtitle "Assign platform roles and scope to users" พร้อม action เดียวคือ **Export** (CSV: Username, Name, Email, Status; ไฟล์ `user-platform-<YYYY-MM-DD>.csv`) จงใจ **ไม่มีปุ่ม Add** — หน้าจอนี้ list ผู้ใช้ที่มีอยู่ (`GET /api-system/user` ผ่าน `userService.getAll`); การสร้างผู้ใช้เป็นของโมดูล [users](/th/platform/users)

**เพิ่มมาตั้งแต่ 2026-06-10:** ใต้ header มีแถบ **`PlatformAccessSummary`** (`userPlatformManagement/PlatformAccessSummary.tsx`) — การ์ดสรุปแบบ governance-band ของผู้ใช้ทั้งหมด (ไม่ใช่แค่หน้า/filter ปัจจุบัน) ตามจำนวน role assignment ระดับแพลตฟอร์ม โหลดด้วย pattern N+1 ต่อผู้ใช้แบบเดียวกับที่ตารางเองใช้ (`userRoleService.list()`) ขยายไปยังผู้ใช้ทุกคน

การค้นหา (debounce 400 ms) และ Sheet ของ filter Status เหมือนหน้า list ของ Roles คอลัมน์:

| คอลัมน์ | การ render |
|---|---|
| Username | คลิกได้ — นำทางไป `/platform/user-platform/:userId` |
| Name | ประกอบจาก `firstname middlename lastname` (filter แล้วต่อด้วยช่องว่าง) fallback เป็น `name` แล้วจึง `-` |
| Email | ข้อความธรรมดา |
| Status | badge Active/Inactive |
| Roles | badge นับจำนวน assignment **fetch ต่อ row ใน background** หลังหน้าโหลดแล้ว — เป็น N+1 ของการเรียก `userRoleService.list(userId)`; spinner เล็ก ๆ render จนกว่าแต่ละ count จะ resolve **แก้ไขแล้ว:** การ fetch ต่อแถวที่ล้มเหลว **ไม่** นับเป็น `0` แบบเงียบ ๆ อีกต่อไป — มันแสดงสามเหลี่ยมเตือนสีอำพัน + "-" ที่แยกต่างหาก (aria-label "Couldn't load roles") และ toast รายงานว่ามีกี่แถวที่ล้มเหลว; sort ไม่ได้ |
| Created / Updated | shape audit แบบ flatten เดียวกับหน้า list ของ Roles; Updated ถูกซ่อนเมื่อเท่ากับ Created |
| Actions | **เพิ่มมาตั้งแต่ 2026-06-10** dropdown `⋯` พร้อม item เดียว "Manage roles" ที่ไม่ถูก gate นำทางไปหน้า detail — ปลายทางเดียวกับการคลิกลิงก์ Username |

สถานะ UI ที่จดจำไว้: `search_user_platform`, `status_filters_user_platform`, `page_user_platform`, `perpage_user_platform`, `sort_user_platform`

### 5.2 `UserPlatformEdit` — detail (`/platform/user-platform/:userId`)

header: ลูกศรย้อนกลับไปหน้า list, ชื่อที่ resolve แล้วของผู้ใช้ (`firstname lastname` fallback เป็น username/id) และ email ตัวหน้าเป็นการ์ด **Roles & Scope** ใบเดียว list assignment ของผู้ใช้ (`GET /api-system/platform/users/:userId/roles` ไล่ลง envelope `{ data }` ที่ซ้อนกัน) แต่ละ row ของ assignment แสดงชื่อ role (fallback เป็น `role_id`) และ badge ของ scope — ชื่อของ cluster (resolve กับ cluster list, fallback เป็น `cluster_id` ดิบ) สำหรับ row ที่ scope ระดับ cluster หรือ "Platform" ในกรณีอื่น — บวกปุ่มไอคอน remove

affordance ที่ mutate ถูก gate ด้วย `<Can permission="user_platform.manage">`: ปุ่ม header **Add Role**, ฟอร์ม add-role แบบ inline และปุ่ม remove ของแต่ละ row render เฉพาะกับผู้ถือ key นั้น viewer ที่มีเพียง `user_platform.read` เห็นการ์ดเดียวกันแบบ read-only ทั้งหมด

### 5.3 ฟอร์ม add-role และการถอดออก

คลิก **Add Role** เผยฟอร์ม inline (ไม่มี dialog): select **Role** ป้อนโดย `roleService.getAll({ perpage: 200, sort: 'name:asc' })`, select **Scope** ที่มีสองตัวเลือก — `Platform` และ `Specific cluster` — และเมื่อเลือก scope ระดับ cluster จะมี select **Cluster** ป้อนโดย `clusterService.getAll({ perpage: 200, sort: 'name:asc' })` การ submit จะ validate ว่าเลือก role แล้ว (และสำหรับ scope ระดับ cluster ต้องเลือก cluster ด้วย) จากนั้นเรียก `POST /api-system/platform/users/:userId/roles` พร้อม `{ role_id, scope }` โดย `scope` เป็น discriminated union (`{ type: 'platform' }` หรือ `{ type: 'cluster', cluster_id }`) แล้ว refetch list ของ assignment

การถอดออกเปิด `ConfirmDialog` ที่ระบุชื่อ role จากนั้นเรียก `DELETE /api-system/platform/users/:userId/roles/:assignmentId` ด้วย id ของ assignment-row ฟอร์ม add-role ที่เปิดอยู่ถูกครอบคลุมโดย `useUnsavedChanges` ขณะที่ field ใด ๆ ถูกแตะ (เตือนแบบ `beforeunload` ของ browser ไม่ใช่ prompt บันทึก — ฟอร์มไม่มี baseline ที่บันทึกไว้ให้คืนค่า) หน้า detail ไม่จดจำสถานะ UI อื่นใด

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — การลงทะเบียน route ของทั้งหกหน้าจอ (บรรทัด 241–296)
- `../carmen-platform/src/pages/RoleManagement.tsx` — คอลัมน์ของ list (name+description รวมกัน, `RolesAccessSummary`), การ flatten audit, ส่งออก CSV, key ที่จดจำไว้, Edit/Delete/Add ที่ gate ด้วย `<Can>`
- `../carmen-platform/src/pages/roleManagement/RolesAccessSummary.tsx` — แถบสรุปจำนวน role/ขอบเขต
- `../carmen-platform/src/pages/RoleEdit.tsx` — เลย์เอาต์ hero + Permissions-ซ้าย/Settings-ขวา, not-found gating, `doc_version`, การคำนวณ permission delta (`handleSubmit` บรรทัด 176–230; delta ที่ 202–205)
- `../carmen-platform/src/pages/roleEdit/RoleIdentityHero.tsx` — การ์ด hero และข้อความสรุป `permissionSummary()`
- `../carmen-platform/src/components/PermissionPicker.tsx` — picker แบบ accordion จัดกลุ่มตาม resource
- `../carmen-platform/src/pages/PermissionCatalog.tsx` — grid card ของ resource แบบ read-only
- `../carmen-platform/src/pages/SuperAdminManagement.tsx` — หน้าจอ `DataTable` + dialog Add ที่เขียนใหม่, การไล่ลง envelope ด้วย `extractArray`, การตัด option ของผู้ใช้
- `../carmen-platform/src/pages/UserPlatformManagement.tsx` — คอลัมน์ของ list รวมคอลัมน์ Actions ใหม่, `PlatformAccessSummary`, การนับ roles ต่อ row ใน background (N+1) พร้อมสถานะ error แยกต่างหาก, key ที่จดจำไว้
- `../carmen-platform/src/pages/userPlatformManagement/PlatformAccessSummary.tsx` — แถบสรุปแบบ governance-band
- `../carmen-platform/src/pages/UserPlatformEdit.tsx` — การ์ด Roles & Scope, gate `<Can>`, ฟอร์ม add-role, การ resolve badge ของ scope
- `../carmen-platform/src/components/Can.tsx` — wrapper สำหรับ render ที่ gate ด้วย permission
- `../carmen-platform/src/pages/Forbidden.tsx` — หน้า 403 ที่เปลี่ยนชื่อแล้ว render เมื่อ route guard ไม่ผ่าน (ดู [Permissions](./permissions.md))

**Cross-link:** [หน้า landing ของ Platform RBAC](/th/platform/rbac) &nbsp;·&nbsp; [Data Model](./data-model.md) &nbsp;·&nbsp; [Permissions](./permissions.md)
