---
title: RBAC ของแพลตฟอร์ม (Platform RBAC)
description: การควบคุมการเข้าถึงแบบอิง permission สำหรับ Platform admin SPA — permission catalog, role, การ assign ผู้ใช้แบบมี scope, super-admin bypass และการเปลี่ยนคีย์เป็น platform_role.* ช่วงสิงหาคม/กันยายน 2026 พร้อมการปรับปรุง RoleEdit/RolesAccessSummary/SuperAdminManagement
published: true
date: 2026-09-05T00:00:00.000Z
tags: platform/rbac, carmen-software
editor: markdown
dateCreated: 2026-06-10T15:00:00.000Z
---

# RBAC ของแพลตฟอร์ม (Platform RBAC)

โมดูล **Platform RBAC** คือระบบควบคุมการเข้าถึงของ Carmen Platform admin SPA โมดูลนี้แทนที่ role enum ค่าเดียวแบบเดิมด้วยแบบจำลองที่อิง permission: **permission catalog** ที่ backend เป็นเจ้าของกำหนด key รูปแบบ `resource.action`, **role** รวม key เหล่านั้นเป็นชุด, **assignment** ผูก role เข้ากับผู้ใช้ที่ scope ระดับทั้งแพลตฟอร์มหรือเฉพาะ cluster และ **flag super-admin** ที่แยกต่างหากจะ bypass ทุกการตรวจสอบ route guard, รายการ sidebar และ gate ของ action ในหน้าทุกตัวใน SPA ล้วน resolve กับระบบนี้

> **Permission key, feature key, superAdminOnly** (`src/components/nav/platformNav.ts`): รายการ nav **Platform Roles** (ป้ายชื่อ "Platform Roles" ไม่ใช่ "Roles" อีกต่อไป) มี `permission: 'platform_role.read'`, `feature: 'platform_roles'`, ไม่มี `superAdminOnly` ส่วน Permission Catalog **ไม่มีรายการ nav เลย** — ดู §1

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** การควบคุมการเข้าถึงแบบอิง permission — catalog กำหนด key รูปแบบ `resource.action`, role รวม key เป็นชุด, assignment แบบมี scope ผูก role เข้ากับผู้ใช้, flag super-admin จะ bypass ทุกการตรวจสอบ &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA และ authorization backend ของมัน &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_platform_permission`, `tb_platform_role`, `tb_platform_role_tb_permission`, `tb_user_tb_platform_role` (scope ผ่าน `cluster_id` ที่เป็น nullable), `tb_platform_super_admin` — ทั้งห้าตารางมี `doc_version` (การ rollout optimistic-lock ทั้งแพลตฟอร์มเมื่อ 2026-07-16) &nbsp;·&nbsp; **หน้าจอ:** Roles · Permission Catalog · Super Admins · User Platform &nbsp;·&nbsp; **หน้าย่อย:** 3 &nbsp;·&nbsp; **เปลี่ยนคีย์เมื่อ 2026-08-20:** `role.*` → `platform_role.*` ทุกจุด, คีย์ `rbac.read` แบบเดี่ยวที่บางหน้าเคยใช้ถูกยกเลิก, และ route ของ Permission Catalog ย้ายจาก `/platform/permissions` ไปเป็น `/platform/category-permissions` (commit `8df0b10`) &nbsp;·&nbsp; **ตั้งแต่ 2026-09-02:** `RoleManagement`/`RoleEdit` วัดจำนวน permission ของ role เทียบกับ **ขนาด catalog** ไม่ใช่ role ที่กว้างที่สุด และตัวเลือก permission ของ `RoleEdit` กลายเป็น grid แบบแถวต่อ resource พร้อมปุ่ม toggle (`#252`/`#253`); `SuperAdminManagement` ถูกเขียนใหม่เป็นครั้งที่สอง จาก `DataTable` เป็นทะเบียนคนแบบการ์ด (`#244`)

**หมายเหตุขอบเขต (resync 2026-09-05):** หน้านี้ครอบคลุมหน้าจอ **Roles** และ **Permission Catalog** อย่างครบถ้วน ส่วน **User Platform** และ **Super Admins** ครอบคลุมเฉพาะระดับสรุปเท่านั้น — แผน resync ปัจจุบันมีแผนแยกทั้งสองออกเป็นโมดูล Platform ระดับบนสุดของตัวเอง (มีรายการ nav, permission key และชุด e2e เป็นของตัวเองอยู่แล้ว) การตรวจสอบแบบละเอียดทุกบรรทัดของสองหน้าจอนี้จึงเลื่อนไปให้ task ที่สร้างโมดูลเหล่านั้น ข้อเท็จจริงที่ระบุด้านล่างเกี่ยวกับทั้งสองผ่านการตรวจสอบกับซอร์สปัจจุบันแล้ว แต่หน้าย่อยยังไม่ได้เขียนใหม่ละเอียดเท่าเนื้อหาของ Roles/Permission Catalog

## 1. ภาพรวม

โมดูลนี้ปรากฏเป็นสี่หน้าจอในกลุ่ม **Platform** ของ sidebar ใน SPA ประกอบกันเป็น pipeline เดียวตั้งแต่การนิยาม key ไปจนถึงการบังคับใช้การเข้าถึง:

- **Permission Catalog (`/platform/category-permissions` → `PermissionCatalog`)** — หน้าอ้างอิงแบบ read-only ของ permission key ทุกตัวที่ backend กำหนด จัดกลุ่มตาม resource **ไม่มีรายการ nav และไม่มี permission gate ที่ระดับ route ของ SPA เลย** — `App.tsx` ห่อ route นี้ด้วย `<PrivateRoute>` เปล่า ๆ ไม่มี `requiredPermission`/`feature` ผู้ใช้ platform ที่ login แล้วคนใดก็ตามที่รู้หรือได้รับ URL จึงเปิดหน้านี้ได้ อย่าตีความว่า "ข้อมูลไม่มีการป้องกัน" เพราะการดึงข้อมูลของหน้านี้เอง (`GET /api-system/platform/permissions`) ถูกบังคับที่ฝั่ง backend ด้วย `platform_role.read` (`RequirePlatformPermission('platform_role.read')`, `platform-permissions.controller.ts`) — session ที่ไม่มี key นี้จะเข้าถึงหน้าได้แต่ call ของ catalog จะ 403 (SPA ขึ้น toast แจ้ง error แล้วโชว์ grid ว่างเปล่า ไม่ใช่หน้าจอ "access denied" ฝั่ง client) route ย้ายมาจาก `/platform/permissions` เมื่อ 2026-08-20 (`8df0b10`); เข้าถึงได้จากปุ่ม header บนหน้า list ของ Roles SPA สร้างหรือแก้ไขรายการใน catalog ไม่ได้
- **Roles (`/platform/roles` → `RoleManagement`, `/platform/roles/new` และ `/platform/roles/:id/edit` → `RoleEdit`)** — รูปแบบ list + create/view/edit มาตรฐาน role คือชุดของ permission key ที่มีชื่อและเปิด/ปิดได้ เลือกจาก catalog เดิมตัวเลือกเป็น accordion แบบ checklist ตั้งแต่ 2026-08-20 เปลี่ยนเป็น grid แถวต่อ resource พร้อมปุ่ม toggle — ดู [UI Screens](/th/platform/rbac/ui-screens)
- **User Platform (`/platform/user-platform` → `UserPlatformManagement`, `/platform/user-platform/:userId` → `UserPlatformEdit`)** — assign role ให้ผู้ใช้ แต่ละ assignment มี scope กำกับ: ทั้งแพลตฟอร์มหรือ cluster ที่ระบุ การ์ด "Roles & Scope" บนหน้า detail คือจุดที่เพิ่มและลบ assignment ถูกเขียนใหม่อีกครั้งตั้งแต่ sync ครั้งก่อนให้เป็น "ทะเบียนสิทธิ์" (`#250`/`#251`) — ดูหมายเหตุขอบเขตด้านบน
- **Super Admins (`/platform/super-admins` → `SuperAdminManagement`)** — ทะเบียน add/remove ของผู้ใช้ที่ bypass ทุกการตรวจสอบ permission การเป็นสมาชิกที่นี่คือ flag ไม่ใช่ role ถูกเขียนใหม่สองครั้งนับตั้งแต่ sync ครั้งแรกเมื่อ 2026-06-10: ครั้งแรกเป็น `DataTable` ที่ค้นหาได้ แล้วเขียนใหม่อีกครั้งเมื่อ 2026-09-02 (`#244`) เป็นทะเบียนคนแบบการ์ด (avatar, ชื่อ/สถานะ/อีเมล/id, บรรทัด audit แบบย่อ "granted … by …" และ self-removal guard ที่แทนที่ปุ่ม Remove ด้วยข้อความอธิบายบนแถวของตัวเอง) — ดูหมายเหตุขอบเขตด้านบน

ตอน login SPA จะดึง **effective permissions** ของผู้ใช้ (`GET /api/user/permission/platform`) — ผลลัพธ์ที่ flatten จาก assignment ทั้งหมดของผู้ใช้ — และ guard ทุกตัวในแอปจะประเมินกับ snapshot นี้ นอกจากนี้ยังมีเส้นทาง login ที่สองแยกต่างหากสำหรับ session แบบ **cluster-admin เท่านั้น** (§2, §5) — ดู [Permissions](/th/platform/rbac/permissions) §4 ว่าประกอบกับข้อยกเว้น bootstrap อย่างไร

**เปลี่ยนคีย์เมื่อ 2026-08-20** (`8df0b10`, "เปลี่ยนคีย์เป็น platform_role.\*, เลิกใช้ rbac.read, ย้าย route เป็น category-permissions"): permission key ของ Roles ทุกตัวเปลี่ยนจาก `role.*` เป็น `platform_role.*` (`platform_role.read`/`.create`/`.update`/`.delete`), คีย์ชั่วคราว `rbac.read` ที่บาง build เคยใช้ถูกยกเลิก, และ route ของ Permission Catalog ย้ายไปเป็น `/platform/category-permissions` **หน้า เทสต์ หรือ ticket ใดที่อ้างถึง `role.read`/`role.create`/`role.update`/`role.delete`/`rbac.read`/`/platform/permissions` กำลังอธิบายสถานะที่ไม่มีอยู่แล้ว**

**ตั้งแต่ 2026-09-02 ทั้งสองหน้าจอของ Roles เปลี่ยนแปลงต่ออีก** (design commit `#252`/`#253` วันเดียวกัน): list ของ `RoleManagement` และแถบ `RolesAccessSummary` ตัวใหม่ตอนนี้วัด `permission_count` ของ role **เทียบกับขนาดของ permission catalog** ไม่ใช่เทียบกับ role ที่กว้างที่สุดในสามตัวที่สรุป — แถบสรุปยังโชว์จำนวน `deleted` (role ที่ถูก soft-delete) ที่เดิมมีในข้อมูลแต่ไม่เคยแสดงมาก่อน และคอลัมน์ Permissions ของ list เองก็ได้แถบวัดเทียบ catalog แบบเดียวกัน `RoleEdit`'s Settings card (name/description/active toggle) ตอนนี้แสดงเฉพาะตอนแก้ไขเท่านั้น — ในโหมดดู ชื่อ/description/สถานะของ role และบรรทัด audit-actor ใหม่ย้ายขึ้นไปอยู่ใน `RoleIdentityHero` แทน จึงไม่มีการ์ด details แยกให้อ่านอีกต่อไป (รูปแบบ "hero ดูดซับการ์ดโหมดดู" แบบเดียวกับที่โมดูล `users` เจอ) การ์ด Permissions ตอนนี้ใช้ `PermissionGrid`: action ทุกตัวใน catalog แสดงเป็นแถวต่อ resource, ปุ่ม toggle ในโหมดแก้ไข และ — ใหม่ — **action ที่ไม่ได้มอบให้แสดงแบบจางลงแทนที่จะซ่อนไป** ทำให้เห็นรูปร่างของ role ได้แม้ตรงที่ไม่มีอะไรเลย รายละเอียดเต็มอยู่ใน [UI Screens](/th/platform/rbac/ui-screens)

## 2. บริบททางธุรกิจ

แบบจำลองเดิมให้ผู้ใช้แต่ละคนมีค่า role-enum ได้ค่าเดียว และ guard ทุกตัว hardcode ว่าค่า enum ใดผ่านได้บ้าง (ดู §5 สำหรับ mapping ฉบับเต็ม) แบบจำลองนั้นตอบคำถามที่แพลตฟอร์มมีจริง ๆ ไม่ได้:

- **การกำหนด scope ต่อ cluster** วิศวกร support ของ Carmen มักรับผิดชอบ cluster ของลูกค้ารายเดียว ไม่ใช่ทั้งหมด assignment row ที่มี `scope = { type: 'cluster', cluster_id }` มอบ key ของ role ภายใน cluster นั้นเท่านั้น — สิ่งที่ enum ค่า global แสดงออกไม่ได้
- **ความเท่าเทียมกับ Applications** โมดูล Applications มอบ key `api_name` แบบละเอียด (เช่น `cluster.create`) ให้ machine client อยู่แล้ว ตอนนี้การเข้าถึงของมนุษย์ใช้ key รูปแบบ `resource.action` เดียวกัน นักพัฒนาจึงใช้เหตุผลกับคลังศัพท์ permission ชุดเดียวได้ทั้งฝั่ง caller ที่เป็นมนุษย์และ machine
- **หน้าที่ที่ประกอบกันได้** "จัดการ report template ได้แต่อ่าน cluster ได้อย่างเดียว" เมื่อก่อนต้องสร้างค่า enum ใหม่ต่อทุกชุดผสม; ตอนนี้เป็นเพียง role ที่มีชุด key ที่ถูกต้อง
- **Bootstrap** การติดตั้งใหม่ยังไม่มี role จาก catalog ถูก assign ให้ใครเลย gate ตอน login จึงมีทางหนีสำหรับ admin คนแรก: เมื่อแพลตฟอร์มมีผู้ใช้รวม 0 หรือ 1 คน login จะข้ามการตรวจสอบว่าต้องมีอย่างน้อยหนึ่ง permission เพื่อให้ administrator คนแรกเข้าระบบและสร้าง role ได้ (ดู §3) ยังมีข้อยกเว้นตอน login อีกแบบหนึ่งที่ไม่เกี่ยวกัน คือรับ session แบบ **cluster-admin เท่านั้น** (ผู้ใช้ที่มีเพียงสิทธิ์ admin ของ `tb_cluster_user` ไม่มี permission ระดับแพลตฟอร์มเลย) — เพิ่มเข้ามาหลังจาก persona cluster-admin เปิดตัว ดู [Permissions](/th/platform/rbac/permissions) §4
- **ลำดับตาม menu** — permission grid ของ role และมุมมอง grant แบบ read-only ต่างก็เรียงลำดับ resource ตามลำดับเดียวกับที่ sidebar ใช้ (`NAV_RESOURCE_ORDER`/`resourceRank()` ใน `platformNav.ts` derive จาก prefix ของ `permission` แต่ละรายการ nav แบบแรกที่ปรากฏชนะ) **comment ในซอร์สของ `platformNav.ts` เองยังระบุ `rbac` และ `license` เป็นตัวอย่าง resource ที่ไม่มีแถว menu เป็นของตัวเอง — comment นั้นล้าสมัยแล้ว** `platform_role` (resource ของโมดูลนี้เอง เปลี่ยนชื่อจาก `role`/`rbac` เมื่อ 2026-08-20) ตอนนี้มีแถว nav **Platform Roles** เป็นของตัวเองแล้ว จึงเรียงลำดับปกติ ไม่ได้อยู่ท้ายกลุ่มที่ไม่มี menu เมื่อ grep ทุกจุดที่เรียก `permission="resource.action"` / `requiredPermission` / `hasPermission()` เทียบกับรายการ permission ของ nav เอง resource สองตัวที่ไม่มีแถว menu เป็นของตัวเองในปัจจุบันจริง ๆ คือ **`activity_log`** (gate "View History" แบบข้าม module ที่ใช้ใน Clusters/Business Units/Users ไม่ใช่โมดูลนี้) และ **`license`** (key ภายในหน้าของโมดูล Licenses แยกจาก key ระดับ nav `subscription.*` ของโมดูลนั้น) — ทั้งสองจะเรียงหลังสุดตามลำดับ catalog ในกลุ่มของตัวเอง นี่คือเหตุผลที่ permission ของ `cluster` มักปรากฏก่อน permission ของ `news` ใน picker เสมอ — มันสะท้อน sidebar ที่ผู้อ่านเพิ่งผ่านมา ไม่ใช่ลำดับตัวอักษรหรือลำดับในฐานข้อมูล
- **ความสามารถในการ audit** ตาราง RBAC ทั้งห้าตัวมี audit trio มาตรฐานของแพลตฟอร์มและ unique constraint ที่รองรับ soft-delete ทุกการมอบสิทธิ์ การเปลี่ยน role และ assignment จึงสืบย้อนถึงผู้กระทำได้และย้อนกลับได้โดยไม่เกิด key ชนกัน — ต่างจากคอลัมน์ enum เดิมที่เปลี่ยนค่าในที่เงียบ ๆ มีช่องว่างหนึ่งจุด: `GET /api-system/platform/roles/:id` (endpoint ที่ `RoleEdit` โหลดข้อมูล role มา) **ไม่ส่ง audit block กลับมาเลย** — SPA จึง fallback ไปอ่าน audit field จาก row ของ role นั้นใน endpoint แบบ *list* แทน (จับคู่ด้วย `id`, best-effort) เพื่อให้ identity hero ยังแสดงบรรทัด "created/updated" ได้

## 3. แนวคิดสำคัญ

- **Permission key** — string รูปแบบ `resource.action` catalog เก็บ `resource` และ `action` เป็นคอลัมน์แยกกัน; key ถูก derive ขึ้นมา key ถูกกำหนดโดย backend — SPA อ่านได้อย่างเดียว ตัวอย่าง key ที่เป็นตัวแทน:

| Key ตัวอย่าง | เปิดอะไร |
|---|---|
| `platform_role.read` | หน้า list ของ Roles และมุมมอง detail ของ role **ไม่ใช่** Permission Catalog — route นั้นไม่มี permission key เลย (ดู §1) แม้ว่าตัว data fetch ของ catalog เองจะถูกบังคับที่ฝั่ง backend ด้วย key เดียวกันนี้ |
| `platform_role.create` / `platform_role.update` / `platform_role.delete` | action สร้าง/แก้ไข/ลบ role (เปลี่ยนชื่อจาก `role.*` เมื่อ 2026-08-20, `8df0b10`) |
| `user_platform.read` | หน้า list และ detail ของ User Platform (read-only) |
| `user_platform.manage` | เพิ่ม/ลบ role assignment บนหน้า detail (gate `<Can>` ภายในหน้า) |
| `cluster.read` | หน้า list ของ Clusters — และหน้า list ของ Business Units ผ่านการ reuse key (ดู §6) |
| `broadcast.send` | route Send Broadcast เพียงตัวเดียว — ตัวอย่าง action segment ที่ไม่ใช่ CRUD |

- **Role** — ชุดของ permission key ที่มีชื่อ พร้อม `is_active` และ description การเขียน role เป็น **delta**: SPA ส่ง `permissions: { add: string[], remove?: string[] }` ที่คำนวณเทียบกับชุด key ที่โหลดมาตอน fetch ไม่ใช่ชุดเต็มที่ต้องการ
- **Assignment และ Scope** — row ใน `tb_user_tb_platform_role` ที่ผูก user + role + scope ใน SPA `Scope` เป็น union `{ type: 'platform' } | { type: 'cluster', cluster_id }`; ใน Prisma เป็นคอลัมน์ `cluster_id` ที่เป็น nullable คอลัมน์เดียว (`null` = ทั้งแพลตฟอร์ม)
- **EffectivePermissions** — `{ platform: string[], clusters: Record<clusterId, string[]>, is_super_admin?: boolean }` ดึงหลัง login และทุกครั้งที่ `AuthProvider` mount ผ่าน `GET /api/user/permission/platform` cache ใน `localStorage` ภายใต้ key `effectivePermissions`
- **ลำดับของ `checkPermission`** (`src/utils/permissions.ts`) — super-admin bypass มาก่อน; จากนั้น array `platform` (สิทธิ์ระดับแพลตฟอร์มใช้ได้ทุกที่); จากนั้น ถ้ามี `clusterId` ดูเฉพาะ array ของ cluster นั้น; ถ้าไม่มี ดู array ของ cluster ใดก็ได้ (การตรวจสอบแบบกว้าง "แสดง nav/หน้านี้ไหม") ไม่เปลี่ยนแปลงตั้งแต่ sync ครั้งก่อน — ตรวจสอบกับซอร์สปัจจุบันบรรทัดต่อบรรทัดแล้ว
- **ข้อยกเว้น bootstrap** — เมื่อจำนวนผู้ใช้รวมเป็น 0 หรือ 1 `login()` จะข้าม gate ที่ต้องมีอย่างน้อย 1 permission และ `hasPermission()` คืน `true` โดยไม่มีเงื่อนไข — ข้อยกเว้นนี้หยุดมีผลทันทีที่มีผู้ใช้คนที่สอง
- **Flag super-admin ≠ role** — `tb_platform_super_admin` คือตาราง flag ต่อผู้ใช้ ไม่ใช่ role ใน `tb_platform_role` ปรากฏเป็น `is_super_admin` ใน payload ของ effective-permissions และ short-circuit ทุกการตรวจสอบก่อนที่จะดู key ใด ๆ

## 4. บทบาทและ Persona

การเข้าถึงหน้าจอ RBAC ทั้งสี่ก็ถูก gate ด้วย permission เช่นกัน route guard ใช้ `requiredPermission` (หรือ `requireSuperAdmin`) บน `PrivateRoute`; หน้าจอ Roles และหน้า detail ของ User Platform ยัง gate action ภายในหน้าด้วย `<Can>` เพิ่มเติม (Permission Catalog, Super Admins และ list ของ User Platform ไม่มี gate ภายในหน้าเลย — route guard คือด่านเดียว):

| หน้าจอ | Route | Route guard | Gate ภายในหน้า |
|---|---|---|---|
| Roles list | `/platform/roles` | `platform_role.read` (`feature="platform_roles"`) | Add คือ `<Can permission="platform_role.create">`; Edit ของแถวคือ `<Can permission="platform_role.update">`; Delete ของแถวคือ `<Can permission="platform_role.delete">` Export ยังไม่ถูก gate |
| Role create | `/platform/roles/new` | `platform_role.create` (`feature="platform_roles"`) | ไม่มี |
| Role edit | `/platform/roles/:id/edit` | `platform_role.update` (`feature="platform_roles"`) | ปุ่ม **Edit** บน header คือ `<Can permission="platform_role.update">` |
| Permission Catalog | `/platform/category-permissions` | **ไม่มี** — `<PrivateRoute>` เปล่า ๆ ไม่มี `requiredPermission`/`feature`; ผู้ใช้ platform ที่ login แล้วคนใดก็เปิดได้ การเรียก `GET .../permissions` ของหน้านี้เองถูกบังคับที่ฝั่ง backend ด้วย `platform_role.read` (session ที่ไม่มี key นี้จะได้ toast 403 และ grid ว่างเปล่า) | ไม่มี (หน้าจอ read-only) |
| Super Admins | `/platform/super-admins` | `requireSuperAdmin` (`feature="super_admins"`) | ไม่มี — มีเพียง super admin เท่านั้นที่เข้าถึงหน้านี้ได้ |
| User Platform list | `/platform/user-platform` | `user_platform.read` (`feature="user_platform"`) | ไม่มี |
| User Platform detail | `/platform/user-platform/:userId` | `user_platform.read` | `<Can permission="user_platform.manage">` ห่อปุ่ม Add Role, ฟอร์ม add-role และปุ่ม Remove ของแต่ละ row |

array ของ sidebar อยู่ที่ `src/components/nav/platformNav.ts` (`ALL_PLATFORM_NAV_ITEMS` กรองผ่าน `buildPlatformNav()`) — `Layout.tsx` เรียกฟังก์ชันนี้อย่างเดียว ไม่ได้นิยาม array ของ nav เองอีกต่อไป:

| รายการ sidebar | เงื่อนไข filter |
|---|---|
| Platform Roles (ป้ายชื่อ "Platform Roles" ไม่ใช่ "Roles") | `permission: 'platform_role.read'`, `feature: 'platform_roles'` |
| Super Admins | `superAdminOnly: true`, `feature: 'super_admins'` |
| User Platform | `permission: 'user_platform.read'`, `feature: 'user_platform'` |
| Permission Catalog | — ไม่มีรายการ sidebar; เข้าถึงจากปุ่ม header ของหน้า Roles |

route guard ที่ไม่ผ่านจะ render หน้า `Forbidden` (เปลี่ยนชื่อจาก component `AccessDenied` ที่เคยประกาศ inline ใน `PrivateRoute.tsx`) **ในตำแหน่งเดิม** โดย URL ไม่เปลี่ยน ภายใน shell `<Layout>` ปกติ — sidebar ยังมองเห็นอยู่ session ยังใช้ได้ และมีสอง action ให้เลือก: "Go Back" (รู้บริบท ถ้าไม่มีปลายทางย้อนกลับที่เหมาะสมจะ fallback ไป `/dashboard`) และ "Go to Dashboard" route `/403` โดยตรงก็ render หน้าเดียวกันนี้ `/dashboard` และ `/profile` ยังคงเป็น authenticated-only — ผู้ใช้ที่ login แล้วทุกคนเข้าถึงได้โดยไม่ขึ้นกับ permission แผนที่ key ต่อ route ฉบับเต็มของส่วนที่เหลือใน SPA อยู่ใน [Permissions](/th/platform/rbac/permissions)

## 5. การย้ายจากแบบจำลอง role เดิม

จนถึง 2026-06-10 SPA gate การเข้าถึงด้วย enum `platform_role` ค่าเดียวบน row ของ user (`platform_admin`, `support_manager`, `support_staff` ฯลฯ) และ array `allowedRoles` บนแต่ละ route แบบจำลองนั้นถูกถอดออกทั้งหมดแล้ว — จาก frontend ใน commit `6091ffc` ("remove legacy platform_role from frontend") และจาก gate ตอน login ใน commit `5f629f2` ("permission-based login gate — drop platform_role/ALLOWED_ROLES from login") ทั้งคู่ใน repo `carmen-platform` enum `enum_platform_role` และคอลัมน์ `tb_user.platform_role` ก็หายไปจาก Prisma platform schema ฝั่ง backend เช่นกัน

| ของเดิม (ถูกถอดออก) | สิ่งที่มาแทน | หมายเหตุ |
|---|---|---|
| enum `tb_user.platform_role` (หนึ่งค่าต่อผู้ใช้) | Catalog + role + assignment แบบมี scope (`tb_platform_permission` / `tb_platform_role` / `tb_user_tb_platform_role`) | ตอนนี้ผู้ใช้ถือได้หลาย role แต่ละตัวเป็นระดับแพลตฟอร์มหรือต่อ cluster |
| prop `allowedRoles={[...]}` บน `PrivateRoute` | `requiredPermission="resource.action"` (หรือ `requireSuperAdmin`) | หนึ่ง key ต่อ route แทน array ของ role ที่ซ้ำกันไปมา |
| `AuthContext.hasRole(roles[])` | `AuthContext.hasPermission(key, { clusterId? })` → `checkPermission` | ทางหนี bootstrap แบบเดียวกันถูกยกมาด้วย |
| allow-list ชื่อ role `ALLOWED_ROLES` ตอน login | Gate ต้องถืออย่างน้อย 1 permission (super-admin, key ระดับแพลตฟอร์มใดก็ได้ หรือ key ระดับ cluster ใดก็ได้) | Commit `5f629f2`; ข้อยกเว้น bootstrap ใช้กับ gate นี้ด้วย |
| filter `roles: [...]` ของ sidebar ใน `Layout.tsx` | filter `permission:` / `superAdminOnly:` ของ sidebar | พฤติกรรม hide-don't-disable แบบเดิม |
| ค่า enum `super_admin` | ตาราง flag `tb_platform_super_admin` → bypass ผ่าน `is_super_admin` | Flag ที่มี semantics ของการ bypass จริง ต่างจากค่า enum เดิมที่ไม่ได้เปิด route เพิ่ม |
| ข้อความ AccessDenied ที่อ้างชื่อ role ที่ไม่ผ่าน | ข้อความทั่วไป "You don't have permission to access this page." | SPA ไม่มีค่า role เดี่ยวให้แสดงอีกต่อไป |

โมดูลนี้แทนที่หน้า Authentication & Roles เดิม (ถูกถอดออกจาก wiki นี้แล้ว); สิ่งใดที่เขียนอิงแบบจำลองเก่า (ชื่อ role อย่าง `support_manager`/`support_staff`, ตาราง `allowedRoles`) อธิบายพฤติกรรมที่ไม่มีอยู่ใน SPA อีกต่อไป

## 6. โมดูลที่เกี่ยวข้อง

- [users](/th/platform/users) — เป็นเจ้าของ row identity ใน `tb_user` ที่ assignment และ flag super-admin ชี้ไป การสร้าง/lifecycle ของผู้ใช้ยังอยู่ในโมดูล Users; หน้าจอ User Platform จัดการเฉพาะ role assignment **หมายเหตุข้ามโมดูล:** `tb_user` ได้คอลัมน์ email-verification สามตัว (`email_verified_at` และอีกสองตัว, migration `20260804000000_user_email_verification`) ที่ไม่มีหน้าไหนในโมดูลนี้เองอ่าน — จุดเดียวใน SPA ที่ใช้คือ badge "Email Unverified" บน `UserPlatformEdit.tsx` (`!!userRecord?.email_verified_at`, บรรทัด 195) บันทึกไว้ที่ [users/data-model](/th/platform/users/data-model) เพราะคอลัมน์อยู่ที่ `tb_user`; ระบุไว้ที่นี่เพราะผู้ใช้ UI จุดเดียวคือหน้าจอที่โมดูลนี้เอกสารอยู่ในปัจจุบัน
- [applications](/th/platform/applications) — ฝั่ง machine-client ที่เป็นคู่เทียบ: มอบ key `api_name` (รูปแบบ `resource.action` เดียวกัน) ให้ API client มีประโยชน์ในการเทียบเคียงเมื่อพิจารณาว่า caller ถูก gate ด้วย RBAC (session ของมนุษย์) หรือ application grant (token ของ machine)
- [clusters](/th/platform/clusters) — assignment ที่มี scope ระดับ cluster อ้างอิง id ของ `tb_cluster`; dropdown cluster ในฟอร์ม add-role ถูกป้อนด้วยรายการ cluster หน้าจอ cluster ถูก guard ด้วย `cluster.read/create/update`
- [business-units](/th/platform/business-units) — **gotcha:** route `/business-units`, `/business-units/new` และ `/business-units/:id/edit` reuse key `cluster.read` / `cluster.create` / `cluster.update` ไม่มี key `business_unit.*` — การมอบสิทธิ์เข้าถึง cluster จึงมอบ Business Units ไปด้วย และแยกมอบอย่างใดอย่างหนึ่งไม่ได้
- **ระวังสับสน seed "Role permissions" ของ Platform Migrations กับโมดูลนี้.** คอนโซล seed ที่ `/platform/migrations` มี op ชื่อ `seed-role-permission` ("Role permissions: Bindings between app roles and permissions") ที่ PR #281 (2026-09-04, `157a65e`) ขยายให้เลือกได้หลาย Business Unit พร้อมกัน (โหมด `multiple` ใหม่ของ `BuSwitcher`) แทนที่จะรันทีละ BU op นี้ seed **catalog role ระดับ tenant** ที่ Carmen Inventory เองใช้ (role แบบ `Requestor`/`Approver` ผูกกับ Business Unit — `packages/prisma-shared-schema-platform/prisma/seed.role-permission.ts`) ซึ่งไม่เกี่ยวกับตาราง `tb_platform_role`/`tb_platform_permission` ของโมดูลนี้เลย op ที่ seed ข้อมูลของ*โมดูลนี้*จริง ๆ คือ `seed-platform-role-permission` ซึ่งเป็นระดับแพลตฟอร์มทั้งหมด ไม่มีพารามิเตอร์ BU และ PR #281 ไม่ได้แตะต้อง

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/rbac/data-model) — ตาราง Prisma ทั้งห้า, unique constraint แบบ soft-delete, คอลัมน์ scope และความแตกต่างจาก shape TypeScript ของ SPA
- [UI Screens](/th/platform/rbac/ui-screens) — list/edit ของ Roles พร้อม PermissionGrid แบบแถวต่อ resource, Permission Catalog แบบ read-only, และ (ระดับสรุป) ทะเบียน Super Admins กับหน้าจอ assignment ของ User Platform
- [Permissions](/th/platform/rbac/permissions) — เมทริกซ์ route-guard ฉบับเต็ม, การประกอบกันของ gate ระดับ route/sidebar/ภายในหน้า, อัลกอริทึมการ resolve permission และกรณีพิเศษสำหรับผู้ทดสอบ
