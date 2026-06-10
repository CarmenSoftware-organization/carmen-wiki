---
title: RBAC ของแพลตฟอร์ม (Platform RBAC)
description: การควบคุมการเข้าถึงแบบอิง permission สำหรับ Platform admin SPA — permission catalog, role, การ assign ผู้ใช้แบบมี scope และ super-admin bypass
published: true
date: 2026-06-10T15:00:00.000Z
tags: platform/rbac, carmen-software
editor: markdown
dateCreated: 2026-06-10T15:00:00.000Z
---

# RBAC ของแพลตฟอร์ม (Platform RBAC)

โมดูล **Platform RBAC** คือระบบควบคุมการเข้าถึงของ Carmen Platform admin SPA โมดูลนี้แทนที่ role enum ค่าเดียวแบบเดิมด้วยแบบจำลองที่อิง permission: **permission catalog** ที่ backend เป็นเจ้าของกำหนด key รูปแบบ `resource.action`, **role** รวม key เหล่านั้นเป็นชุด, **assignment** ผูก role เข้ากับผู้ใช้ที่ scope ระดับทั้งแพลตฟอร์มหรือเฉพาะ cluster และ **flag super-admin** ที่แยกต่างหากจะ bypass ทุกการตรวจสอบ route guard, รายการ sidebar และ gate ของ action ในหน้าทุกตัวใน SPA ล้วน resolve กับระบบนี้

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** การควบคุมการเข้าถึงแบบอิง permission — catalog กำหนด key รูปแบบ `resource.action`, role รวม key เป็นชุด, assignment แบบมี scope ผูก role เข้ากับผู้ใช้, flag super-admin จะ bypass ทุกการตรวจสอบ &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Platform admin SPA และ authorization backend ของมัน &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_platform_permission`, `tb_platform_role`, `tb_platform_role_tb_permission`, `tb_user_tb_platform_role` (scope ผ่าน `cluster_id` ที่เป็น nullable), `tb_platform_super_admin` &nbsp;·&nbsp; **หน้าจอ:** Roles · Permission Catalog · Super Admins · User Platform &nbsp;·&nbsp; **หน้าย่อย:** 3

## 1. ภาพรวม

โมดูลนี้ปรากฏเป็นสี่หน้าจอในกลุ่ม **Platform** ของ sidebar ใน SPA ประกอบกันเป็น pipeline เดียวตั้งแต่การนิยาม key ไปจนถึงการบังคับใช้การเข้าถึง:

- **Permission Catalog (`/platform/permissions` → `PermissionCatalog`)** — หน้าอ้างอิงแบบ read-only ของ permission key ทุกตัวที่ backend กำหนด จัดกลุ่มตาม resource ไม่มีรายการใน sidebar; เข้าถึงได้จากปุ่ม header บนหน้า list ของ Roles SPA สร้างหรือแก้ไขรายการใน catalog ไม่ได้
- **Roles (`/platform/roles` → `RoleManagement`, `/platform/roles/new` และ `/platform/roles/:id/edit` → `RoleEdit`)** — รูปแบบ list + create/view/edit มาตรฐาน role คือชุดของ permission key ที่มีชื่อและเปิด/ปิดได้ เลือกจาก catalog ผ่าน `PermissionPicker` แบบ accordion
- **User Platform (`/platform/user-platform` → `UserPlatformManagement`, `/platform/user-platform/:userId` → `UserPlatformEdit`)** — assign role ให้ผู้ใช้ แต่ละ assignment มี scope กำกับ: ทั้งแพลตฟอร์มหรือ cluster ที่ระบุ การ์ด "Roles & Scope" บนหน้า detail คือจุดที่เพิ่มและลบ assignment
- **Super Admins (`/platform/super-admins` → `SuperAdminManagement`)** — รายการ add/remove แบบแบนของผู้ใช้ที่ bypass ทุกการตรวจสอบ permission การเป็นสมาชิกที่นี่คือ flag ไม่ใช่ role

ตอน login SPA จะดึง **effective permissions** ของผู้ใช้ (`GET /api/user/permission/platform`) — ผลลัพธ์ที่ flatten จาก assignment ทั้งหมดของผู้ใช้ — และ guard ทุกตัวในแอปจะประเมินกับ snapshot นี้

## 2. บริบททางธุรกิจ

แบบจำลองเดิมให้ผู้ใช้แต่ละคนมีค่า role-enum ได้ค่าเดียว และ guard ทุกตัว hardcode ว่าค่า enum ใดผ่านได้บ้าง (ดู §5 สำหรับ mapping ฉบับเต็ม) แบบจำลองนั้นตอบคำถามที่แพลตฟอร์มมีจริง ๆ ไม่ได้:

- **การกำหนด scope ต่อ cluster** วิศวกร support ของ Carmen มักรับผิดชอบ cluster ของลูกค้ารายเดียว ไม่ใช่ทั้งหมด assignment row ที่มี `scope = { type: 'cluster', cluster_id }` มอบ key ของ role ภายใน cluster นั้นเท่านั้น — สิ่งที่ enum ค่า global แสดงออกไม่ได้
- **ความเท่าเทียมกับ Applications** โมดูล Applications มอบ key `api_name` แบบละเอียด (เช่น `cluster.create`) ให้ machine client อยู่แล้ว ตอนนี้การเข้าถึงของมนุษย์ใช้ key รูปแบบ `resource.action` เดียวกัน นักพัฒนาจึงใช้เหตุผลกับคลังศัพท์ permission ชุดเดียวได้ทั้งฝั่ง caller ที่เป็นมนุษย์และ machine
- **หน้าที่ที่ประกอบกันได้** "จัดการ report template ได้แต่อ่าน cluster ได้อย่างเดียว" เมื่อก่อนต้องสร้างค่า enum ใหม่ต่อทุกชุดผสม; ตอนนี้เป็นเพียง role ที่มีชุด key ที่ถูกต้อง
- **Bootstrap** การติดตั้งใหม่ยังไม่มี role จาก catalog ถูก assign ให้ใครเลย gate ตอน login จึงมีทางหนีสำหรับ admin คนแรก: เมื่อแพลตฟอร์มมีผู้ใช้รวม 0 หรือ 1 คน login จะข้ามการตรวจสอบว่าต้องมีอย่างน้อยหนึ่ง permission เพื่อให้ administrator คนแรกเข้าระบบและสร้าง role ได้ (ดู §3)
- **ความสามารถในการ audit** ตาราง RBAC ทั้งห้าตัวมี audit trio มาตรฐานของแพลตฟอร์มและ unique constraint ที่รองรับ soft-delete ทุกการมอบสิทธิ์ การเปลี่ยน role และ assignment จึงสืบย้อนถึงผู้กระทำได้และย้อนกลับได้โดยไม่เกิด key ชนกัน — ต่างจากคอลัมน์ enum เดิมที่เปลี่ยนค่าในที่เงียบ ๆ

## 3. แนวคิดสำคัญ

- **Permission key** — string รูปแบบ `resource.action` catalog เก็บ `resource` และ `action` เป็นคอลัมน์แยกกัน; key ถูก derive ขึ้นมา key ถูกกำหนดโดย backend — SPA อ่านได้อย่างเดียว ตัวอย่าง key ที่เป็นตัวแทน:

| Key ตัวอย่าง | เปิดอะไร |
|---|---|
| `role.read` | หน้า list ของ Roles, มุมมอง detail ของ role และ Permission Catalog |
| `role.create` / `role.update` | route create / edit ของ role |
| `user_platform.read` | หน้า list และ detail ของ User Platform (read-only) |
| `user_platform.manage` | เพิ่ม/ลบ role assignment บนหน้า detail (gate `<Can>` ภายในหน้า) |
| `cluster.read` | หน้า list ของ Clusters — และหน้า list ของ Business Units ผ่านการ reuse key (ดู §6) |
| `broadcast.send` | route Send Broadcast เพียงตัวเดียว — ตัวอย่าง action segment ที่ไม่ใช่ CRUD |

- **Role** — ชุดของ permission key ที่มีชื่อ พร้อม `is_active` และ description การเขียน role เป็น **delta**: SPA ส่ง `permissions: { add: string[], remove?: string[] }` ที่คำนวณเทียบกับชุด key ที่โหลดมาตอน fetch ไม่ใช่ชุดเต็มที่ต้องการ
- **Assignment และ Scope** — row ใน `tb_user_tb_platform_role` ที่ผูก user + role + scope ใน SPA `Scope` เป็น union `{ type: 'platform' } | { type: 'cluster', cluster_id }`; ใน Prisma เป็นคอลัมน์ `cluster_id` ที่เป็น nullable คอลัมน์เดียว (`null` = ทั้งแพลตฟอร์ม)
- **EffectivePermissions** — `{ platform: string[], clusters: Record<clusterId, string[]>, is_super_admin?: boolean }` ดึงหลัง login และทุกครั้งที่ `AuthProvider` mount ผ่าน `GET /api/user/permission/platform` cache ใน `localStorage` ภายใต้ key `effectivePermissions`
- **ลำดับของ `checkPermission`** (`src/utils/permissions.ts`) — super-admin bypass มาก่อน; จากนั้น array `platform` (สิทธิ์ระดับแพลตฟอร์มใช้ได้ทุกที่); จากนั้น ถ้ามี `clusterId` ดูเฉพาะ array ของ cluster นั้น; ถ้าไม่มี ดู array ของ cluster ใดก็ได้ (การตรวจสอบแบบกว้าง "แสดง nav/หน้านี้ไหม")
- **ข้อยกเว้น bootstrap** — เมื่อจำนวนผู้ใช้รวมเป็น 0 หรือ 1 `login()` จะข้าม gate ที่ต้องมีอย่างน้อย 1 permission และ `hasPermission()` คืน `true` โดยไม่มีเงื่อนไข — ข้อยกเว้นนี้หยุดมีผลทันทีที่มีผู้ใช้คนที่สอง
- **Flag super-admin ≠ role** — `tb_platform_super_admin` คือตาราง flag ต่อผู้ใช้ ไม่ใช่ role ใน `tb_platform_role` ปรากฏเป็น `is_super_admin` ใน payload ของ effective-permissions และ short-circuit ทุกการตรวจสอบก่อนที่จะดู key ใด ๆ

## 4. บทบาทและ Persona

การเข้าถึงหน้าจอ RBAC ทั้งสี่ก็ถูก gate ด้วย permission เช่นกัน route guard ใช้ `requiredPermission` (หรือ `requireSuperAdmin`) บน `PrivateRoute`; มีหนึ่งหน้าจอที่ gate action ภายในหน้าเพิ่มเติมด้วย `<Can>`:

| หน้าจอ | Route | Route guard | Gate ภายในหน้า |
|---|---|---|---|
| Roles list | `/platform/roles` | `role.read` | ไม่มี — Add/Edit/Delete/Export มองเห็นทั้งหมดเมื่อ route resolve แล้ว |
| Role create | `/platform/roles/new` | `role.create` | ไม่มี |
| Role edit | `/platform/roles/:id/edit` | `role.update` | ไม่มี |
| Permission Catalog | `/platform/permissions` | `role.read` | ไม่มี (หน้าจอ read-only) |
| Super Admins | `/platform/super-admins` | `requireSuperAdmin` | ไม่มี — มีเพียง super admin เท่านั้นที่เข้าถึงหน้านี้ได้ |
| User Platform list | `/platform/user-platform` | `user_platform.read` | ไม่มี |
| User Platform detail | `/platform/user-platform/:userId` | `user_platform.read` | `<Can permission="user_platform.manage">` ห่อปุ่ม Add Role, ฟอร์ม add-role และปุ่ม Remove ของแต่ละ row |

sidebar สะท้อน route guard (`src/components/Layout.tsx` กลุ่ม "Platform"):

| รายการ sidebar | เงื่อนไข filter |
|---|---|
| Roles | `permission: 'role.read'` |
| Super Admins | `superAdminOnly: true` |
| User Platform | `permission: 'user_platform.read'` |
| Permission Catalog | — ไม่มีรายการ sidebar; เข้าถึงจากปุ่ม header ของหน้า Roles |

route guard ที่ไม่ผ่านจะ render `<AccessDenied>` ภายใน shell `<Layout>` ปกติ — sidebar ยังมองเห็นอยู่ session ยังใช้ได้ และมีปุ่ม Back-to-Dashboard ให้ `/dashboard` และ `/profile` ยังคงเป็น authenticated-only — ผู้ใช้ที่ login แล้วทุกคนเข้าถึงได้โดยไม่ขึ้นกับ permission แผนที่ key ต่อ route ฉบับเต็มของส่วนที่เหลือใน SPA อยู่ใน [Permissions](/th/platform/rbac/permissions)

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

- [users](/th/platform/users) — เป็นเจ้าของ row identity ใน `tb_user` ที่ assignment และ flag super-admin ชี้ไป การสร้าง/lifecycle ของผู้ใช้ยังอยู่ในโมดูล Users; หน้าจอ User Platform จัดการเฉพาะ role assignment
- [applications](/th/platform/applications) — ฝั่ง machine-client ที่เป็นคู่เทียบ: มอบ key `api_name` (รูปแบบ `resource.action` เดียวกัน) ให้ API client มีประโยชน์ในการเทียบเคียงเมื่อพิจารณาว่า caller ถูก gate ด้วย RBAC (session ของมนุษย์) หรือ application grant (token ของ machine)
- [clusters](/th/platform/clusters) — assignment ที่มี scope ระดับ cluster อ้างอิง id ของ `tb_cluster`; dropdown cluster ในฟอร์ม add-role ถูกป้อนด้วยรายการ cluster หน้าจอ cluster ถูก guard ด้วย `cluster.read/create/update`
- [business-units](/th/platform/business-units) — **gotcha:** route `/business-units`, `/business-units/new` และ `/business-units/:id/edit` reuse key `cluster.read` / `cluster.create` / `cluster.update` ไม่มี key `business_unit.*` — การมอบสิทธิ์เข้าถึง cluster จึงมอบ Business Units ไปด้วย และแยกมอบอย่างใดอย่างหนึ่งไม่ได้

## 7. หน้าในโมดูลนี้

- [Data Model](/th/platform/rbac/data-model) — ตาราง Prisma ทั้งห้า, unique constraint แบบ soft-delete, คอลัมน์ scope และความแตกต่างจาก shape TypeScript ของ SPA
- [UI Screens](/th/platform/rbac/ui-screens) — list/edit ของ Roles พร้อม PermissionPicker, Permission Catalog แบบ read-only, รายการ Super Admins และหน้าจอ assignment ของ User Platform
- [Permissions](/th/platform/rbac/permissions) — เมทริกซ์ route-guard ฉบับเต็ม, การประกอบกันของ gate ระดับ route/sidebar/ภายในหน้า, อัลกอริทึมการ resolve permission และกรณีพิเศษสำหรับผู้ทดสอบ
