---
title: Platform RBAC — หน้าจอ UI (UI Screens)
description: RoleManagement/RoleEdit พร้อม RolesAccessSummary แบบวัดเทียบ catalog และ PermissionGrid แบบแถวต่อ resource, Permission Catalog แบบ read-only, และ (ระดับสรุป) ทะเบียน Super Admins กับหน้าจอ assignment ของ User Platform ที่เขียนใหม่
published: true
date: 2026-09-05T16:00:00.000Z
tags: book/platform, rbac, ui
editor: markdown
dateCreated: 2026-06-10T15:00:00.000Z
---

# Platform RBAC — หน้าจอ UI (UI Screens)

> **At a Glance**
> **หน้าจอ:** `RoleManagement` (`/platform/roles`) · `RoleEdit` (`/platform/roles/new`, `/platform/roles/:id/edit`) · `PermissionCatalog` (`/platform/category-permissions`) · `SuperAdminManagement` (`/platform/super-admins`) · `UserPlatformManagement` (`/platform/user-platform`) · `UserPlatformEdit` (`/platform/user-platform/:userId`) &nbsp;·&nbsp; **รูปแบบมาตรฐาน:** Roles และ User Platform ใช้ `DataTable` แบบ server-side; Super Admins (เขียนใหม่อีกครั้งเมื่อ 2026-09-02) เป็นทะเบียนแบบการ์ด ไม่ใช่ตาราง; Permission Catalog เป็น card grid แบบ read-only &nbsp;·&nbsp; **Component หลัก:** `PermissionGrid` — action ทุกตัวใน catalog แสดงเป็นแถวต่อ resource, ปุ่ม toggle ในโหมดแก้ไข, action ที่ไม่ได้มอบให้แสดงจางลงแทนที่จะซ่อนไป (แทนที่ accordion `PermissionPicker` เมื่อ 2026-08-20) &nbsp;·&nbsp; **Gate ภายในหน้า:** list/edit ของ Roles gate Add/Edit/Delete และ toggle Edit ด้วยคีย์ `platform_role.*`; `<Can permission="user_platform.manage">` บนหน้า detail ของ User Platform &nbsp;·&nbsp; **แถบสรุป:** `RolesAccessSummary` บนหน้า list ของ Roles (วัดเทียบ catalog ตั้งแต่ 2026-09-02), `PlatformAccessSummary` บนหน้า list ของ User Platform

**หมายเหตุขอบเขต:** หน้านี้ตรวจสอบ §2 (Roles) และ §3 (Permission Catalog) กับซอร์สปัจจุบันอย่างครบถ้วน §4 (Super Admins) และ §5 (User Platform) อัพเดทเฉพาะระดับสรุปเท่านั้น — ดูหมายเหตุขอบเขตใน[หน้า landing ของโมดูล](/th/platform/rbac)

## 1. ภาพรวม

**Roles** ทำตามรูปแบบ Management/Edit มาตรฐานของ Platform SPA: list แบบ `DataTable` ฝั่ง server พร้อมการค้นหาแบบ debounce, filter แบบ Sheet, ส่งออก CSV, แถบสรุป `RolesAccessSummary` รวมถึงหน้า create/view/edit ที่นำด้วยการ์ด `RoleIdentityHero` **permission key เปลี่ยนจาก `role.*` เป็น `platform_role.*` และ route ของ Permission Catalog ย้ายไปเป็น `/platform/category-permissions` เมื่อ 2026-08-20** (`carmen-platform` commit `8df0b10`) — ดู[หน้า landing ของโมดูล](/th/platform/rbac) และ [Permissions](/th/platform/rbac/permissions) สำหรับการเปลี่ยนชื่อฉบับเต็ม

**Permission Catalog** เป็นหน้าอ้างอิงแบบ read-only: grid ของ card แบบ responsive จัดกลุ่มตาม resource ไม่มีตาราง ไม่มี mutation เข้าถึงได้จากปุ่ม header บนหน้า list ของ Roles เท่านั้น ไม่มีรายการ sidebar และ — ต่างจากทุกหน้าจอในโมดูลนี้ — **ไม่มี permission gate ที่ระดับ route ของ SPA เลย** ผู้ใช้ platform ที่ login แล้วคนใดก็นำทางไปหน้านี้ได้โดยตรง การดึงข้อมูลของหน้ายังคงถูกบังคับที่ฝั่ง backend ด้วย `platform_role.read` (§3)

**User Platform** และ **Super Admins** สรุปไว้ใน §4/§5 ตามหมายเหตุขอบเขตข้างบน ทั้งคู่ผ่านการเขียนใหม่ต่ออีกครั้งตั้งแต่ sync ครั้งก่อน (`carmen-platform` PR #244/#250/#251 ทั้งหมดเมื่อ 2026-09-02) ที่ไม่ได้ตรวจสอบบรรทัดต่อบรรทัดในหน้านี้

ทั้งหกหน้าจอมาพร้อม **Debug Sheet** เฉพาะ dev ของ SPA — ปุ่มลอยสีเหลืองอำพัน (มุมขวาล่าง) ที่เปิด JSON ดิบของ API response ของหน้าจอนั้น (เฉพาะ `import.meta.env.DEV` ไม่มีใน production build) บน `RoleEdit` มีสอง tab คือ Role และ Catalog เปิดเผย payload ของทั้งสอง endpoint — เป็นวิธีที่เร็วที่สุดสำหรับ QA ในการตรวจสอบการซ้อนของ envelope และ shape ของ audit จริง ๆ ตามที่อธิบายด้านล่าง

## 2. Roles

### 2.1 `RoleManagement` — list (`/platform/roles`)

แถว header: title "Roles" / subtitle "Manage platform roles and their permissions" และ header action สามตัวจากซ้ายไปขวา — **Permission Catalog** (นำทางไป `/platform/category-permissions`), **Export** (CSV ฝั่ง client ของหน้าที่โหลดอยู่: Name, Description, Permissions, Active, Created At/By, Updated At/By — ผ่าน `auditCsvFields(normalizeAudit(r))`; ไฟล์ `roles-<YYYY-MM-DD>.csv`; disable ขณะกำลังโหลดหรือว่างเปล่า) และ **Add Role** (นำทางไป `/platform/roles/new`, ห่อด้วย `<Can permission="platform_role.create">`)

ใต้ header มีแถบ **`RolesAccessSummary`** (`roleManagement/RolesAccessSummary.tsx`) ดึงจาก endpoint เฉพาะทาง `GET /api-system/platform/roles/summary` (`roleService.getAccessSummary()` — ทั้งระบบ ไม่สนใจ search/filter ของตาราง คงตัวเลขล่าสุดไว้และหรี่ตัวเองเมื่อ refresh ล้มเหลวแทนที่จะว่างเปล่า) แสดงจำนวน role รวมพร้อม breakdown active/inactive/**deleted** (จำนวนที่ถูก soft-delete เป็นข้อมูลใหม่ที่มีในระบบแต่ไม่เคยแสดงมาก่อน) บวกสาม role ที่มีขอบเขต permission กว้างที่สุด **ตั้งแต่ 2026-09-02 (`#252`) แท่ง "broadest roles" วัดเทียบกับขนาดของ permission catalog ไม่ใช่เทียบกับ role ที่กว้างที่สุดในสามตัวที่แสดง** — role ที่มอบ permission ครบทุกตัวใน catalog จะได้แท่งสีอำพันพร้อมไอคอนเตือน (ตรงกับถ้อยคำ "Full access" ของ `RoleIdentityHero`) และหัวข้อของ section จะระบุ "of `N`" เมื่อทราบขนาด catalog แล้ว; ถ้าไม่ทราบ (catalog กำลังโหลดหรือล้มเหลว) แท่งจะถูกตัดออกทั้งหมดแทนที่จะวาดเทียบตัวหารที่ไม่มีความหมาย

ด้านล่างคือแถวค้นหาและ filter มาตรฐาน: input ค้นหาแบบ debounce (400 ms) เหนือ `name`/`description` และ Sheet **Filters** ที่มีกลุ่ม Status กลุ่มเดียว (ปุ่ม toggle Active / Inactive → query `advance` `{ where: { is_active } }` เมื่อเลือกเพียงค่าเดียว) chip ของ filter ที่ active แสดงใต้แถวค้นหา

คอลัมน์ของ `DataTable` ตามลำดับ:

| คอลัมน์ | การ render |
|---|---|
| Name | ลิงก์คลิกได้ — นำทางไป `/platform/roles/:id/edit` — พร้อม `description` ของ role เป็นข้อความสีจางด้านล่าง (รวมเข้าคอลัมน์นี้แล้ว ไม่มีคอลัมน์ Description แยกต่างหาก) |
| Permissions | **`RoleReachCell`** (`roleManagement/RoleReachCell.tsx`, ตั้งแต่ 2026-09-02) — `permission_count`/`catalogSize` เป็นเศษส่วนพร้อมแท่งตามสัดส่วน (ซ่อนแท่งต่ำกว่า `lg` เพื่อไม่ให้เหลือเป็นเส้นบางจนแทบมองไม่เห็น) พร้อมไอคอนเตือน + สไตล์สีอำพันเมื่อ role ถือ catalog ทั้งหมด และบรรทัด `resource_count` แบบ optional ด้านล่าง ("N resources") เมื่อ backend ส่งมา; sort ไม่ได้ |
| Status | badge Active/Inactive จาก `is_active` |
| Created | `AuditMeta` (`variant="cell"`) ผ่าน `auditColumns()` ที่ใช้ร่วมกัน — เวลาแบบ relative (เช่น "5mo ago") บรรทัดหนึ่ง ชื่อ actor บรรทัดถัดไป timestamp เต็มเป็น tooltip `title` เมื่อ hover อ่านจาก `normalizeAudit(row)` ซึ่งลองรูปแบบซ้อน `audit.created` `{ at, name }` ก่อน แล้ว fallback ไปคอลัมน์แบบแบน `created_at`/`created_by_name` เฉพาะเมื่อไม่มี nested เท่านั้น |
| Updated | render ด้วย `AuditMeta` แบบเดียวกันจาก `normalizeAudit(row).updated` — **ถูกซ่อน (render `-`) ก็ต่อเมื่อ record ยังไม่เคยถูกแก้ไขจริง** (`everEdited`: มีชื่อ actor ที่แก้ หรือ timestamp ต่างจาก `created`) ไม่ใช่การเทียบ `updated_at === created_at` ตรง ๆ |
| Actions | dropdown `⋯`: **Edit** (นำทาง; `<Can permission="platform_role.update">`) และ **Delete** (เปิด `ConfirmDialog` แบบ destructive; เมื่อยืนยันเรียก `DELETE /api-system/platform/roles/:id`; `<Can permission="platform_role.delete">`) session ที่มีเพียง `platform_role.read` เห็น dropdown ว่างเปล่า เหมือน management list อื่น ๆ ทุกหน้าใน SPA |

เมื่อชุดผลลัพธ์ว่างเปล่า ตารางถูกแทนด้วยการ์ด `EmptyState` ("No roles yet" พร้อม CTA Add Role แบบ inline — ซึ่ง gate ด้วย `<Can permission="platform_role.create">` เช่นกัน — เมื่อไม่มี search term หรือข้อความ `No roles matching "<term>"` เมื่อมี) sort เริ่มต้นคือ `created_at:desc` สถานะ UI ที่จดจำไว้:

| Key ใน `localStorage` | ชนิดที่เก็บ | จดจำอะไร |
|---|---|---|
| `search_roles` | string | search term |
| `filters_roles` | JSON string array | การเลือก filter Status |
| `page_roles` | number string | หน้าปัจจุบัน |
| `perpage_roles` | number string | ขนาดหน้า |
| `sort_roles` | string | Sort (`column:dir`) |

### 2.2 `RoleEdit` — เลย์เอาต์

หน้าเปิดด้วยการ์ด **`RoleIdentityHero`** (`roleEdit/RoleIdentityHero.tsx`) — ไอคอนโล่, ชื่อ role (หรือ "(unnamed role)"), บรรทัด `description` ที่**แสดงเฉพาะในโหมด view** (ย้ายขึ้นมาจากการ์ด Settings ดูด้านล่าง), badge Active/Inactive และ — ใหม่ตั้งแต่ sync ครั้งก่อน — **บรรทัด audit-actor** (`<AuditMeta variant="header">`, "Created … · Updated … by …") ปุ่ม **Edit** (โหมด view เท่านั้น) render อยู่ใน action slot ของ hero, gate ด้วย `<Can permission="platform_role.update">`

สรุปขอบเขต permission มีสองรูปแบบขึ้นกับโหมด:
- **โหมด view (role ที่มีอยู่แล้ว ไม่ได้แก้ไข):** แสดงข้อความที่ละเอียดกว่าซึ่ง `RoleEdit.tsx` คำนวณเอง (`grantSummary`) — "`N` permission(s) · `X` of `Y` resources" บวก " · read only" เมื่อ action ที่มอบให้ทั้งหมดเป็น `read` หรือ verb ไม่เกินสามตัวคั่นด้วย " · " ในกรณีอื่น
- **โหมด create หรือขณะแก้ไข:** hero กลับไปใช้ `permissionSummary()` แบบง่ายของตัวเอง — "No permissions granted yet" หรือ "`N` permission(s) across `M` resource(s)" — คำนวณใหม่แบบ live ตาม toggle ที่เปลี่ยน
- **ทั้งสองโหมด เมื่อจำนวน key ที่มอบให้ role ถึงขนาดของ catalog:** ทั้งสองรูปแบบถูกแทนที่ด้วย "Full access to every permission" สีอำพันพร้อมสามเหลี่ยมเตือน — สถานะที่ audit-worthy ที่สุด จึงชนะเสมอ

ใต้ hero ฟอร์มเป็น grid สองคอลัมน์ **เฉพาะขณะแก้ไขเท่านั้น** (`lg:grid-cols-[1fr_minmax(300px,340px)]`); ในโหมด view จะยุบเหลือคอลัมน์เดียว **Permissions** เป็นการ์ดซ้าย/กว้างในทั้งสองโหมด เป็นที่อยู่ของ `PermissionGrid` (§2.6) **Settings** — `name` (จำเป็น), `description` (textarea) และ checkbox/badge `is_active` — เป็น rail ขวา/แคบแบบ sticky แต่ **ตั้งแต่ 2026-09-02 (`#253`) แสดงเฉพาะขณะแก้ไขเท่านั้น**: ในโหมด view ไม่มีการ์ด "Settings" หรือ "Role Details" แยกต่างหากอีกต่อไป เพราะสองข้อเท็จจริงที่มันเคยซ้ำ (ชื่อเป็น `<h1>`, สถานะเป็น badge) อยู่ใน hero อยู่แล้ว และข้อเท็จจริงเดียวที่มันถืออยู่คนเดียว (description) ก็ย้ายไปที่ hero ด้วย รูปแบบนี้คือ pattern เดียวกับที่โมดูล `users` เจอ — การ์ด detail ของโหมด read ถูกดูดซับเข้า identity hero

### 2.3 `RoleEdit` — โหมด create (`/platform/roles/new`)

Title มาจาก hero (ชื่อว่างแสดง "(unnamed role)"); ฟอร์มแก้ไขได้ทันทีตั้งแต่ mount (`editing = true`) — โหมด create ไม่มีปุ่ม Edit ตอน submit SPA เรียก `POST /api-system/platform/roles` พร้อม `permissions: { add: <key ที่เลือกทั้งหมด> }` เมื่อสำเร็จจะ redirect ไป `/platform/roles/:id/edit` ของ id ที่สร้าง (fallback ไปหน้า list เมื่อ response ไม่มี id)

### 2.4 `RoleEdit` — โหมด view/edit (`/platform/roles/:id/edit`)

**Not-found gating:** `id` ที่ผิดหรือถูกลบ render shell เฉพาะแทนฟอร์ม — มีเพียงลิงก์ย้อนกลับและ `EmptyState` ไอคอน `SearchX` ("Role not found", "This role doesn't exist, or it may have been deleted…", ปุ่ม "Back to roles")

โหลดผ่าน `GET /api-system/platform/roles/:id` ซึ่งคืนแค่ `{ id, doc_version, name, description, is_active, permissions }` และ **ไม่มี audit block เลย** `RoleEdit.tsx` แก้ปัญหาด้วยการยิง request ที่สองแบบ best-effort — ไป query endpoint แบบ *list* กรองด้วย `id` นั้น (`roleService.getAll({ advance: { where: { id } } })`) แล้วดึง field audit ของ row นั้นมาใช้กับบรรทัด `AuditMeta` ของ hero; audit ของ record ของ role เองชนะถ้ามันมี audit block ในอนาคต ไม่งั้นใช้ fallback จาก list-row และถ้า fallback ล้มเหลวก็แค่ไม่แสดงบรรทัด audit หน้าเริ่มต้นแบบ **read-only**: การ์ด Permissions แสดง action ทุกตัวใน catalog จัดกลุ่มตาม resource action ที่มอบให้ไฮไลต์และ**action ที่ไม่ได้มอบให้แสดงจางลงแทนที่จะซ่อนไป** (§2.6) — หรือถ้า catalog เองโหลดไม่สำเร็จ ก็แสดงแค่ key ที่ role ถืออยู่โดยไม่จางอะไรเลย (หน้าไม่สามารถแยกแยะ "ไม่ได้มอบให้" จาก "ไม่เคยรู้จัก" ได้ถ้าไม่มี catalog); role ที่ไม่มี permission เลยและไม่มี catalog ให้ fallback จะแสดง "No permissions granted." แทนการ์ดว่างเปล่า คลิก **Edit** (ใน hero) สลับเป็นแก้ไขได้; **Cancel** (ใน sticky bar ด้านล่าง, §2.5) คืนค่า snapshot ก่อนแก้ไข การเปลี่ยนแปลงที่ยังไม่บันทึก trigger navigation guard `useUnsavedChanges` และ shortcut ระดับ global ใช้ save (`formRef.requestSubmit`) และ cancel ได้ (เฉพาะเมื่อ `!isNew`)

การบันทึกคำนวณ **permission delta** เทียบกับชุด key ที่จับไว้ตอน fetch — `add` = ถูกเลือกแต่ไม่อยู่ในชุดเดิม, `remove` = อยู่ในชุดเดิมแต่ไม่ถูกเลือก — แล้วส่ง `PUT /api-system/platform/roles/:id` พร้อม `permissions: { add, remove }` บวก `doc_version` เมื่อทราบค่า ความไม่ตรงกันของ version จะ trigger toast `notifyVersionConflict()` ที่ใช้ร่วมกันและ re-fetch แทนที่จะเขียนทับเงียบ ๆ หลังบันทึกสำเร็จหน้าจะ refetch role และกลับสู่โหมด view

### 2.5 Sticky action bar

Render เฉพาะขณะ `editing = true` ตาม pattern เดียวกับ clusters/business-units/users/applications/report-templates: bar แบบ `fixed bottom-0` มีตัวบ่งชี้การเปลี่ยนแปลงที่ยังไม่บันทึก (จุดสีอำพันกระพริบ + "Unsaved changes" หรือ "No changes" ด้วยข้อความสีจาง) ทางซ้าย และ **Cancel** (ซ่อนในโหมด create; disable ขณะบันทึก) + **Create Role**/**Save Changes** (disable ขณะบันทึก หรือในโหมด edit เมื่อไม่มีการเปลี่ยนแปลง) ทางขวา

### 2.6 `PermissionGrid` (แทนที่ accordion `PermissionPicker` เมื่อ 2026-08-20, `carmen-platform` commit `42eeafe`)

`roleEdit/PermissionGrid.tsx` คือ component เดียวที่ทั้งสองโหมดใช้ร่วมกัน — read และ edit render เหมือนกันทุกประการยกเว้น affordance ดังนั้นการกด Edit จะไม่ขยับอะไรบนหน้าจอเลย แถวเรียงหนึ่งต่อ `resource` ตามลำดับ `resourceRank()` (ลำดับที่ derive จาก nav ของ `platformNav.ts` — ดู [Permissions](/th/platform/rbac/permissions)); ภายในแถว action เรียงตาม `actionRank()` (`utils/permissionOrder.ts`: `['read', 'create', 'update', 'delete', 'manage']` verb ที่ไม่อยู่ในรายการเรียงท้ายสุดตามลำดับ catalog) แทนที่จะเป็นลำดับตัวอักษรของ catalog เอง ซึ่งจะทำให้ `create`/`delete` มาก่อน `read`

**action ทุกตัวใน catalog ถูกแสดง ไม่ว่าจะมอบให้หรือไม่** — accordion ที่ถูกแทนที่นี้เคย render เฉพาะ key ที่มอบให้เท่านั้น ทำให้ส่วนที่ role ไม่ได้ถือมองไม่เห็นเลย ใน **โหมดแก้ไข** แต่ละ action เป็นปุ่ม toggle `<button aria-pressed>` (ไม่ใช่ checkbox): ทึบสี/tint เมื่อมอบให้ ขอบเส้นประและจางเมื่อไม่ได้มอบให้ พร้อม `description` ของ action เป็น tooltip เมื่อ hover; ลิงก์ข้อความสั้น ๆ ท้ายแถวของแต่ละ resource เขียนว่า **"All"** (มอบทุก action ที่เหลือใน resource นั้น) หรือ **"None"** (ล้าง action ที่มอบให้ทั้งหมดใน resource นั้น) สลับตามสถานะปัจจุบันของแถว ใน **โหมด read** action เดียวกัน render เป็น `Badge` — ทึบสำหรับที่มอบให้ ขอบเส้นประสำหรับที่ไม่ได้มอบให้ — และ resource ที่ไม่มี grant เลยจะจางลงไปอีก บรรทัด legend สั้น ๆ ("Dashed actions are in the catalog but not granted to this role.") ปรากฏใต้ grid แต่เฉพาะในโหมด read ที่โหลด catalog ครบแล้วเท่านั้น และเฉพาะเมื่อมีอย่างน้อยหนึ่ง resource ที่จำนวน action ที่มอบให้น้อยกว่าจำนวนทั้งหมด (รวมถึง resource ที่ไม่มี grant เลย) — จะไม่ปรากฏขณะแก้ไข (action แบบเส้นประคือปุ่มที่กดได้ ซึ่งอธิบายตัวเองอยู่แล้ว)

## 3. Permission Catalog

`PermissionCatalog` (`/platform/category-permissions` — ย้ายมาจาก `/platform/permissions` เมื่อ 2026-08-20) เป็นหน้าอ้างอิงแบบ read-only ของ key ทุกตัวใน catalog โหลดครั้งเดียวผ่าน `GET /api-system/platform/permissions` header: ลิงก์ย้อนกลับไป `/platform/roles`, title "Permission Catalog", subtitle "Read-only reference of all platform permissions" **ตัว route เองไม่มี permission requirement เลย** — `App.tsx` ห่อด้วย `<PrivateRoute>` เปล่า ๆ — แต่การดึงข้อมูลของหน้าถูกบังคับที่ฝั่ง backend ด้วย `platform_role.read`; session ที่ไม่มี key นี้จะเห็น shell ของหน้า, toast แจ้ง error และ grid ว่างเปล่า ไม่ใช่ "access denied" ฝั่ง client

เนื้อหาเป็น grid ของ card แบบ responsive (2 คอลัมน์ที่ `sm`, 3 ที่ `lg`) หนึ่ง card ต่อ resource โดยรักษาลำดับของ catalog แต่ละ card แสดง permission ของมันเป็น outline badge แบบ monospace พร้อม key `resource.action` ฉบับเต็ม, `description` เป็นข้อความสีจางด้านล่างเมื่อมี และ — ใหม่ตั้งแต่ sync ครั้งก่อน — บรรทัด audit แบบย่อ (`AuditMeta variant="compact"` ผ่าน `latestActor()`) แสดงว่าใครแก้ไข catalog row นั้นล่าสุด ในทางปฏิบัติบรรทัดนี้ไม่แสดงอะไรเลยสำหรับแทบทุก key: `tb_platform_permission` เป็นข้อมูล seed ที่ `created_by_id` เป็น null ทุก row จึง field audit ของ `PermissionCatalogItem` จะมีค่าก็ต่อเมื่อ backend เริ่ม attribute การแก้ไข catalog ให้ actor เท่านั้น ไม่มีปุ่ม ไม่มีการค้นหา ไม่มี filter และไม่มี affordance ของการ mutation ใด ๆ — catalog เป็นข้อมูลที่ backend เป็นเจ้าของ catalog ที่ว่างเปล่า render เป็น `EmptyState` ("No permissions") หน้าจอนี้ **ไม่มีรายการใน sidebar**; เส้นทางนำทางเข้ามามีเพียงปุ่ม header ของหน้า Roles และ URL โดยตรงเท่านั้น

## 4. Super Admins (ระดับสรุป — ดูหมายเหตุขอบเขตใน §1)

`SuperAdminManagement` (`/platform/super-admins`) ถูกเขียนใหม่เป็น**ครั้งที่สอง**นับตั้งแต่ sync ฉบับเต็มครั้งก่อน เมื่อ 2026-09-02 (`#244`, "ทำให้หน้านี้เป็นทะเบียนคน ไม่ใช่ตารางข้อมูล") ไม่ใช่หน้า `DataTable` ที่ sync ครั้งก่อนอธิบายไว้อีกต่อไป ตอนนี้เป็น**ทะเบียนแบบการ์ด** —

- **Header:** title "Super Admins", subtitle แบบ dynamic ระบุจำนวนคนปัจจุบัน ("N super admins") แทนคำอธิบายตายตัว และสอง action — **Export** (CSV ฝั่ง client รวมคอลัมน์ audit แล้ว: User, Email, User ID, Status, Created At/By, Updated At/By) และ **Add Super Admin** ซึ่งเปิด `Dialog` แบบ modal
- **Dialog Add Super Admin:** typeahead แบบ server-side **`UserPicker`** (ไม่ใช่ `Select` ที่โหลดผู้ใช้ 200 คนไว้ล่วงหน้า) ค้นหาผู้ใช้ทุกคนตามชื่อ/อีเมลขณะพิมพ์ ตัดผู้ใช้ที่ถือ flag อยู่แล้วออก การยืนยันเรียก `POST /api-system/platform/super-admins` พร้อม `{ user_id }`
- **ทะเบียน:** `<ul>` ธรรมดาของแถว (avatar-initials, ชื่อ, badge Active/Inactive, email, `user_id` และบรรทัด audit แบบย่อ "granted … by …" ต่อแถว) — ไม่ใช่ `DataTable` กล่องค้นหาปรากฏก็ต่อเมื่อทะเบียนมีมากกว่า 8 แถว ปุ่ม Remove ของแต่ละแถวเป็น `<Button>` แบบ destructive ธรรมดา (ไม่ใช่ dropdown item) — **บนแถวของตัวเองมันถูกแทนที่ด้วยข้อความอธิบายทั้งหมด** ("cannot remove yourself") แทนที่จะเป็นปุ่มที่ disable เฉย ๆ เพราะหน้าจอนี้เข้าถึงได้เฉพาะ super admin และปุ่ม Remove ที่ยังกดได้บนแถวของตัวเองมีความเสี่ยงจะล็อกตัวเอง (และอาจล็อกทุกคน) ออกจากระบบ

response ของ list ยังคงซ้อน envelope `{ data }` หลายชั้นและถูกไล่ลงด้วย helper `extractArray` ระดับ local เหมือนเดิม สถานะ UI ที่จดจำไว้มีแค่ search term (`search_super_admins`)

## 5. User Platform (ระดับสรุป — ดูหมายเหตุขอบเขตใน §1)

ทั้งสองหน้าจอถูกเขียนใหม่ครั้งใหญ่นับตั้งแต่ sync ฉบับเต็มครั้งก่อน (`#250`/`#251`, 2026-09-02, "ทำให้นี่เป็นทะเบียนสิทธิ์ ไม่ใช่ฟอร์มแก้ role")

**`UserPlatformManagement`** (`/platform/user-platform`) list: ยังคงไม่มีปุ่ม Add (ผู้ใช้ถูกสร้างในโมดูล [users](/th/platform/users)) แถบสรุป (`PlatformAccessSummary`) ตอนนี้มาจาก **block `summary` แบบ filter-consistent บน response ของ list เอง** แทนที่จะเป็นการกวาด `userRoleService.list()` แบบ N+1 ต่อผู้ใช้ทุกคน — คอลัมน์ **Roles** ของ list เองประกอบ assignment ของแต่ละแถวแบบ inline (`RoleChips`) แทนที่จะเป็น badge นับจำนวนเปล่า ๆ filter ขยายจาก Status เพิ่มเป็น Role และ Scope (ทั้งแพลตฟอร์ม/cluster เฉพาะ) Export ตอนนี้เป็นต่อ**assignment** ไม่ใช่ต่อผู้ใช้ (หนึ่งแถว CSV ต่อ role หนึ่งตัว ผู้ใช้ที่มีสาม role จึงได้สามแถว) และแต่ละแถวมี action "Revoke all access" แบบ destructive (`<Can permission="user_platform.manage">`) เคียงข้าง "Manage roles" ใน dropdown ของ row

**`UserPlatformEdit`** (`/platform/user-platform/:userId`) detail: ได้ **Access Reach Band** (สรุปขอบเขตทั้งแพลตฟอร์มเทียบกับต่อ cluster) แบบใหม่, banner เตือนเมื่อบัญชีที่ถูกปิดใช้งานยังถือ role assignment อยู่, badge "Email Unverified" (`!!userRecord?.email_verified_at` — คอลัมน์ email-verification ของ `tb_user` ที่ระบุไว้ใน[หน้า landing ของโมดูล](/th/platform/rbac)) และ **Membership Card** ที่ list cluster/BU ของผู้ใช้เพื่อบริบท การระบุ "granted by" ต่อ assignment ยัง workaround อยู่: endpoint ของ role ต่อผู้ใช้ไม่คืน actor มาด้วย หน้าจึง query endpoint list ของ registry ด้วย search term แยกต่างหากแล้วจับคู่ row กลับด้วย `user_id` ถ้าล้มเหลวจะแสดง "ไม่มีข้อมูล provenance" อย่างชัดเจนแทนที่จะเดา การ์ด Roles & Scope, gate `<Can permission="user_platform.manage">` และ flow add-role/remove เป็นกลไกเดียวกับเดิม แม้ UI ของ add-role จะย้ายจากฟอร์ม inline ไปเป็น Sheet (`AddRoleSheet`)

ด้วยความลึกของการเขียนใหม่นี้ การตรวจสอบ §4/§5 แบบละเอียดทุก section (คอลัมน์, ถ้อยคำที่แน่นอน, key ของ `localStorage` ที่จดจำไว้, ทุก component) จึงเลื่อนไปให้ task ที่สร้างโมดูล `user-platform`/`super-admins` แบบ standalone ตามที่แผน resync ปัจจุบันเรียกร้อง

## 6. แหล่งข้อมูลอ้างอิง

- `../carmen-platform/src/App.tsx` — การลงทะเบียน route ของสี่ route Roles/Permission-Catalog (บรรทัด 402–432 รวม `<PrivateRoute>` เปล่า ๆ ของ `/platform/category-permissions`); route ของ User Platform และ Super Admins อยู่ที่อื่นในไฟล์เดียวกัน
- `../carmen-platform/src/pages/RoleManagement.tsx` — คอลัมน์ของ list (name+description รวมกัน, `RoleReachCell`), gate ด้วยคีย์ `platform_role.*`, ส่งออก CSV รวม audit, key ที่จดจำไว้
- `../carmen-platform/src/pages/roleManagement/RolesAccessSummary.tsx`, `.../RoleReachCell.tsx` — แถบสรุปและแท่งของ cell ที่วัดเทียบ catalog (2026-09-02)
- `../carmen-platform/src/pages/RoleEdit.tsx` — เลย์เอาต์ hero + `PermissionGrid` (rail ของ Settings เฉพาะโหมดแก้ไข), not-found gating, `doc_version`, การ fallback audit จาก list endpoint (`fetchAudit`), การคำนวณ permission delta (`handleSubmit`)
- `../carmen-platform/src/pages/roleEdit/RoleIdentityHero.tsx` — การ์ด hero, ข้อความสรุป `permissionSummary()` และบรรทัด audit-actor
- `../carmen-platform/src/pages/roleEdit/PermissionGrid.tsx` — grid มอบสิทธิ์แบบแถวต่อ resource (แทนที่ `PermissionPicker` เมื่อ 2026-08-20, `42eeafe`; component accordion เดิมไม่มีอยู่แล้ว)
- `../carmen-platform/src/utils/permissionOrder.ts` — `ACTION_ORDER`/`actionRank()`
- `../carmen-platform/src/components/nav/platformNav.ts` — `resourceRank()`/`NAV_RESOURCE_ORDER` ที่ `RoleEdit.tsx` ใช้
- `../carmen-platform/src/pages/PermissionCatalog.tsx` — grid card ของ resource แบบ read-only, บรรทัด audit ต่อ item
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-permissions/platform-permissions.controller.ts` — การบังคับ `platform_role.read` บน endpoint ของ catalog
- `../carmen-platform/src/pages/SuperAdminManagement.tsx` — การเขียนใหม่เป็นทะเบียนแบบการ์ด (2026-09-02, `#244`), การไล่ลง envelope ด้วย `extractArray`, self-removal guard, typeahead `UserPicker`
- `../carmen-platform/src/components/UserPicker.tsx` — typeahead ของผู้ใช้ฝั่ง server ที่ dialog Add ของ Super Admins ใช้
- `../carmen-platform/src/pages/UserPlatformManagement.tsx`, `.../UserPlatformEdit.tsx` — การเขียนใหม่เป็นทะเบียนสิทธิ์ (2026-09-02, `#250`/`#251`); ไม่ได้ตรวจสอบบรรทัดต่อบรรทัดในหน้านี้ (ดูหมายเหตุขอบเขตใน §1)
- `../carmen-platform/src/components/Can.tsx` — wrapper สำหรับ render ที่ gate ด้วย permission
- `../carmen-platform/src/pages/Forbidden.tsx` — หน้า 403 render เมื่อ route guard ไม่ผ่าน (ดู [Permissions](/th/platform/rbac/permissions))

**Cross-link:** [หน้า landing ของ Platform RBAC](/th/platform/rbac) &nbsp;·&nbsp; [Data Model](/th/platform/rbac/data-model) &nbsp;·&nbsp; [Permissions](/th/platform/rbac/permissions)
