---
title: RBAC ของแพลตฟอร์ม (Backstage RBAC)
description: การควบคุมการเข้าถึงแบบอิง permission สำหรับ Backstage SPA — permission catalog, role, การ assign ผู้ใช้แบบมี scope และ super-admin bypass
published: true
date: 2026-10-29T05:00:00.000Z
tags: backstage/rbac, carmen-software
editor: markdown
dateCreated: 2026-06-10T15:00:00.000Z
---

# RBAC ของแพลตฟอร์ม (Backstage RBAC)

โมดูล **Backstage RBAC** คือระบบควบคุมการเข้าถึงของ Carmen Blue Backstage admin SPA โมดูลนี้แทนที่ role enum ค่าเดียวแบบเดิมด้วยแบบจำลองที่อิง permission: **permission catalog** ที่ backend เป็นเจ้าของกำหนด key รูปแบบ `resource.action`, **role** รวม key เหล่านั้นเป็นชุด, **assignment** ผูก role เข้ากับผู้ใช้ที่ scope ระดับทั้งแพลตฟอร์มหรือเฉพาะ cluster และ **flag super-admin** ที่แยกต่างหากจะ bypass ทุกการตรวจสอบ route guard, รายการ sidebar และ gate ของ action ในหน้าทุกตัวใน SPA ล้วน resolve กับระบบนี้

> **Permission key, feature key, superAdminOnly** (`src/components/nav/backstageNav.ts`): รายการ nav **Backstage Roles** (ป้ายชื่อ "Backstage Roles" ไม่ใช่ "Roles" อีกต่อไป) มี `permission: 'backstage_role.read'`, `feature: 'backstage_roles'`, ไม่มี `superAdminOnly` ส่วน Permission Catalog **ไม่มีรายการ nav เลย** — ดู §1

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** การควบคุมการเข้าถึงแบบอิง permission — catalog กำหนด key รูปแบบ `resource.action`, role รวม key เป็นชุด, assignment แบบมี scope ผูก role เข้ากับผู้ใช้, flag super-admin จะ bypass ทุกการตรวจสอบ &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนาและ QA ที่ทำงานกับ Backstage SPA และ authorization backend ของมัน &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_backstage_permission`, `tb_backstage_role`, `tb_backstage_role_tb_permission`, `tb_user_tb_backstage_role` (scope ผ่าน `cluster_id` ที่เป็น nullable), `tb_backstage_super_admin` — ทั้งห้าตารางมี `doc_version` (การ rollout optimistic-lock ทั้งแพลตฟอร์มเมื่อ 2026-07-16) &nbsp;·&nbsp; **หน้าจอที่ครอบคลุมในหน้านี้:** Roles · Permission Catalog &nbsp;·&nbsp; **หน้าจอที่สรุปไว้ที่นี่ มีโมดูลเต็มอยู่ที่อื่น:** [Super Admins](/th/backstage/super-admins) · [Backstage Users](/th/backstage/user-backstage) (ดูหมายเหตุขอบเขตด้านล่าง) &nbsp;·&nbsp; **หน้าย่อย:** 3 &nbsp;·&nbsp; **เปลี่ยนคีย์เมื่อ 2026-08-20:** `role.*` → `platform_role.*` (→ `backstage_role.*` on 2026-10-26, `318949a3`) ทุกจุด, คีย์ `rbac.read` แบบเดี่ยวที่บางหน้าเคยใช้ถูกยกเลิก, และ route ของ Permission Catalog ย้ายจาก `/backstage/permissions` ไปเป็น `/backstage/category-permissions` (commit `8df0b10` ใน repo `carmen-backstage`) &nbsp;·&nbsp; **ตั้งแต่ 2026-09-02:** `RoleManagement`/`RoleEdit` วัดจำนวน permission ของ role เทียบกับ **ขนาด catalog** ไม่ใช่ role ที่กว้างที่สุด และตัวเลือก permission ของ `RoleEdit` กลายเป็น grid แบบแถวต่อ resource พร้อมปุ่ม toggle (`carmen-backstage` PR #252/#253); `SuperAdminManagement` ถูกเขียนใหม่เป็นครั้งที่สอง จาก `DataTable` เป็นทะเบียนคนแบบการ์ด (`carmen-backstage` PR #244)

![RBAC ของแพลตฟอร์ม (Backstage RBAC) screen](/screenshots/platform/rbac/index.png)

**หมายเหตุขอบเขต (resync 2026-09-05):** หน้านี้ครอบคลุมหน้าจอ **Roles** และ **Permission Catalog** อย่างครบถ้วน ส่วน **Backstage Users** และ **Super Admins** ครอบคลุมเฉพาะระดับสรุปเท่านั้น — ทั้งสองมีโมดูล Platform ระดับบนสุดของตัวเองแล้ว คือ [Backstage Users](/th/backstage/user-backstage) และ [Super Admins](/th/backstage/super-admins) แต่ละโมดูลมีรายการ nav, permission key และชุด e2e เป็นของตัวเองตามที่ระบุไว้ด้านล่าง พร้อมการตรวจสอบแบบละเอียดทุกบรรทัดของหน้าจอตัวเองแล้ว ข้อเท็จจริงที่ระบุด้านล่างเกี่ยวกับทั้งสองผ่านการตรวจสอบกับซอร์สปัจจุบันแล้ว แต่สำหรับเนื้อหาแบบละเอียด — หน้าจอ, คอลัมน์, endpoint — ให้ดูที่หน้าโมดูลของตัวเอง ไม่ใช่หน้านี้

## 1. ภาพรวม

SPA ยังจัดกลุ่มสี่หน้าจอไว้ใต้ระบบควบคุมการเข้าถึงนี้ในกลุ่ม **Platform** ของ sidebar หน้านี้ครอบคลุมสองหน้าจอ — **Roles** และ **Permission Catalog** — อย่างครบถ้วน ประกอบกันเป็น pipeline เดียวตั้งแต่การนิยาม key ไปจนถึงการบังคับใช้การเข้าถึง ส่วน **Super Admins** และ **Backstage Users** สรุปไว้ด้านล่างและใน [UI Screens](/th/backstage/rbac/ui-screens) เท่านั้น — ทั้งคู่มีโมดูล Platform ระดับบนสุดของตัวเองแล้ว คือ [Super Admins](/th/backstage/super-admins) และ [Backstage Users](/th/backstage/user-backstage) (ดูหมายเหตุขอบเขตด้านบน) การตรวจสอบแบบละเอียด — หน้าจอ, คอลัมน์, endpoint — จึงอยู่ที่นั่น ไม่ใช่ที่หน้านี้

ครอบคลุมอย่างครบถ้วนในหน้านี้:

- **Permission Catalog (`/backstage/category-permissions` → `PermissionCatalog`)** — หน้าอ้างอิงแบบ read-only ของ permission key ทุกตัวที่ backend กำหนด จัดกลุ่มตาม resource **ไม่มีรายการ nav และไม่มี permission gate ที่ระดับ route ของ SPA เลย** — `App.tsx` ห่อ route นี้ด้วย `<PrivateRoute>` เปล่า ๆ ไม่มี `requiredPermission`/`feature` ผู้ใช้ backstage ที่ login แล้วคนใดก็ตามที่รู้หรือได้รับ URL จึงเปิดหน้านี้ได้ อย่าตีความว่า "ข้อมูลไม่มีการป้องกัน" เพราะการดึงข้อมูลของหน้านี้เอง (`GET /api-system/backstage/permissions`) ถูกบังคับที่ฝั่ง backend ด้วย `backstage_role.read` (`RequireBackstagePermission('backstage_role.read')`, `backstage-permissions.controller.ts`) — session ที่ไม่มี key นี้จะเข้าถึงหน้าได้แต่ call ของ catalog จะ 403 (SPA ขึ้น toast แจ้ง error แล้วโชว์ grid ว่างเปล่า ไม่ใช่หน้าจอ "access denied" ฝั่ง client) route ย้ายมาจาก `/backstage/permissions` เมื่อ 2026-08-20 (commit `8df0b10` ใน repo `carmen-backstage`); เข้าถึงได้จากปุ่ม header บนหน้า list ของ Roles SPA สร้างหรือแก้ไขรายการใน catalog ไม่ได้
- **Roles (`/backstage/roles` → `RoleManagement`, `/backstage/roles/new` และ `/backstage/roles/:id/edit` → `RoleEdit`)** — รูปแบบ list + create/view/edit มาตรฐาน role คือชุดของ permission key ที่มีชื่อและเปิด/ปิดได้ เลือกจาก catalog เดิมตัวเลือกเป็น accordion แบบ checklist ตั้งแต่ 2026-08-20 เปลี่ยนเป็น grid แถวต่อ resource พร้อมปุ่ม toggle — ดู [UI Screens](/th/backstage/rbac/ui-screens)

สรุปไว้เท่านั้นในหน้านี้ — ดูหมายเหตุขอบเขตด้านบนว่าทำไม และดูหน้าโมดูลของตัวเองสำหรับเนื้อหาแบบละเอียด:

- **Backstage Users (`/backstage/user-backstage` → `UserBackstageManagement`, `/backstage/user-backstage/:userId` → `UserBackstageEdit`)** — assign role ให้ผู้ใช้ แต่ละ assignment มี scope กำกับ: ทั้งแพลตฟอร์มหรือ cluster ที่ระบุ การ์ด "Roles & Scope" บนหน้า detail คือจุดที่เพิ่มและลบ assignment ถูกเขียนใหม่อีกครั้งตั้งแต่ sync ครั้งก่อนให้เป็น "ทะเบียนสิทธิ์" (`carmen-backstage` PR #250/#251)
- **Super Admins (`/backstage/super-admins` → `SuperAdminManagement`)** — ทะเบียน add/remove ของผู้ใช้ที่ bypass ทุกการตรวจสอบ permission การเป็นสมาชิกที่นี่คือ flag ไม่ใช่ role ถูกเขียนใหม่สองครั้งนับตั้งแต่ sync ครั้งแรกเมื่อ 2026-06-10: ครั้งแรกเป็น `DataTable` ที่ค้นหาได้ แล้วเขียนใหม่อีกครั้งเมื่อ 2026-09-02 (`carmen-backstage` PR #244) เป็นทะเบียนคนแบบการ์ด (avatar, ชื่อ/สถานะ/อีเมล/id, บรรทัด audit แบบย่อ "granted … by …" และ self-removal guard ที่แทนที่ปุ่ม Remove ด้วยข้อความอธิบายบนแถวของตัวเอง)

ตอน login SPA จะดึง **effective permissions** ของผู้ใช้ (`GET /api/user/permission/backstage`) — ผลลัพธ์ที่ flatten จาก assignment ทั้งหมดของผู้ใช้ — และ guard ทุกตัวในแอปจะประเมินกับ snapshot นี้ นอกจากนี้ยังมีเส้นทาง login ที่สองแยกต่างหากสำหรับ session แบบ **cluster-admin เท่านั้น** (§2, §5) — ดู [Permissions](/th/backstage/rbac/permissions) §4 ว่าประกอบกับข้อยกเว้น bootstrap อย่างไร

**เปลี่ยนคีย์สองครั้ง** เมื่อ 2026-08-20 (`8df0b10`, "เปลี่ยนคีย์เป็น platform_role.*, เลิกใช้ rbac.read, ย้าย route เป็น category-permissions") permission key ของ Roles ทุกตัวเปลี่ยนจาก `role.*` เป็น `platform_role.*`; เมื่อ 2026-10-26 การ rename เป็น Carmen Blue Backstage (`carmen-backstage` `318949a3`, backend `e0eaeff61`) เปลี่ยนซ้ำเป็น `backstage_role.*` (`backstage_role.read`/`.create`/`.update`/`.delete`) — และ rename `user_platform.*` เป็น `user_backstage.*` กับ `platform_config.*` เป็น `backstage_config.*` ในแบบเดียวกัน migration ฝั่ง backend `20261026120000_rename_platform_values_to_backstage` เขียนทับค่า `resource` ที่เก็บไว้ในที่เดิม คีย์ชั่วคราว `rbac.read` ที่บาง build เคยใช้ถูกยกเลิก และ route ของ Permission Catalog ย้ายไปเป็น `/backstage/category-permissions` **หน้า เทสต์ หรือ ticket ใดที่อ้างถึง `role.read`/`role.create`/`role.update`/`role.delete`/`rbac.read`/`platform_role.*`/`/backstage/permissions` กำลังอธิบายสถานะที่ไม่มีอยู่แล้ว** การ rename เดียวกันนี้ย้ายทั้งคอนโซลจาก `/platform/*` ไป `/backstage/*` (และ segment `user-platform` เป็น `user-backstage`); bookmark เก่ายังใช้ได้เพราะ `App.tsx:654` mount `LegacyPlatformRedirect` บน `/platform/*` ซึ่งเขียน prefix ใหม่และคง query กับ hash ไว้ (`App.tsx:677-681`) role ที่ seed ไว้ `Platform Admin` ตอนนี้คือ `Backstage Admin` และฟิลด์ `platform` ใน payload effective-permissions ตอนนี้คือ `backstage` (`GET /api/user/permission/backstage`)

**ตั้งแต่ 2026-09-02 ทั้งสองหน้าจอของ Roles เปลี่ยนแปลงต่ออีก** (`carmen-backstage` design PR #252/#253 วันเดียวกัน): list ของ `RoleManagement` และแถบ `RolesAccessSummary` ตัวใหม่ตอนนี้วัด `permission_count` ของ role **เทียบกับขนาดของ permission catalog** ไม่ใช่เทียบกับ role ที่กว้างที่สุดในสามตัวที่สรุป — แถบสรุปยังโชว์จำนวน `deleted` (role ที่ถูก soft-delete) ที่เดิมมีในข้อมูลแต่ไม่เคยแสดงมาก่อน และคอลัมน์ Permissions ของ list เองก็ได้แถบวัดเทียบ catalog แบบเดียวกัน `RoleEdit`'s Settings card (name/description/active toggle) ตอนนี้แสดงเฉพาะตอนแก้ไขเท่านั้น — ในโหมดดู ชื่อ/description/สถานะของ role และบรรทัด audit-actor ใหม่ย้ายขึ้นไปอยู่ใน `RoleIdentityHero` แทน จึงไม่มีการ์ด details แยกให้อ่านอีกต่อไป (รูปแบบ "hero ดูดซับการ์ดโหมดดู" แบบเดียวกับที่โมดูล `users` เจอ) การ์ด Permissions ตอนนี้ใช้ `PermissionGrid`: action ทุกตัวใน catalog แสดงเป็นแถวต่อ resource, ปุ่ม toggle ในโหมดแก้ไข และ — ใหม่ — **action ที่ไม่ได้มอบให้แสดงแบบจางลงแทนที่จะซ่อนไป** ทำให้เห็นรูปร่างของ role ได้แม้ตรงที่ไม่มีอะไรเลย รายละเอียดเต็มอยู่ใน [UI Screens](/th/backstage/rbac/ui-screens)

## 2. บริบททางธุรกิจ

แบบจำลองเดิมให้ผู้ใช้แต่ละคนมีค่า role-enum ได้ค่าเดียว และ guard ทุกตัว hardcode ว่าค่า enum ใดผ่านได้บ้าง (ดู §5 สำหรับ mapping ฉบับเต็ม) แบบจำลองนั้นตอบคำถามที่แพลตฟอร์มมีจริง ๆ ไม่ได้:

- **การกำหนด scope ต่อ cluster** วิศวกร support ของ Carmen Blue มักรับผิดชอบ cluster ของลูกค้ารายเดียว ไม่ใช่ทั้งหมด assignment row ที่มี `scope = { type: 'cluster', cluster_id }` มอบ key ของ role ภายใน cluster นั้นเท่านั้น — สิ่งที่ enum ค่า global แสดงออกไม่ได้
- **ความเท่าเทียมกับ Applications** โมดูล Applications มอบ key `api_name` แบบละเอียด (เช่น `cluster.create`) ให้ machine client อยู่แล้ว ตอนนี้การเข้าถึงของมนุษย์ใช้ key รูปแบบ `resource.action` เดียวกัน นักพัฒนาจึงใช้เหตุผลกับคลังศัพท์ permission ชุดเดียวได้ทั้งฝั่ง caller ที่เป็นมนุษย์และ machine
- **หน้าที่ที่ประกอบกันได้** "จัดการ report template ได้แต่อ่าน cluster ได้อย่างเดียว" เมื่อก่อนต้องสร้างค่า enum ใหม่ต่อทุกชุดผสม; ตอนนี้เป็นเพียง role ที่มีชุด key ที่ถูกต้อง
- **Bootstrap** การติดตั้งใหม่ยังไม่มี role จาก catalog ถูก assign ให้ใครเลย gate ตอน login จึงมีทางหนีสำหรับ admin คนแรก: เมื่อแพลตฟอร์มมีผู้ใช้รวม 0 หรือ 1 คน login จะข้ามการตรวจสอบว่าต้องมีอย่างน้อยหนึ่ง permission เพื่อให้ administrator คนแรกเข้าระบบและสร้าง role ได้ (ดู §3) ยังมีข้อยกเว้นตอน login อีกแบบหนึ่งที่ไม่เกี่ยวกัน คือรับ session แบบ **cluster-admin เท่านั้น** (ผู้ใช้ที่มีเพียงสิทธิ์ admin ของ `tb_cluster_user` ไม่มี permission ระดับแพลตฟอร์มเลย) — เพิ่มเข้ามาหลังจาก persona cluster-admin เปิดตัว ดู [Permissions](/th/backstage/rbac/permissions) §4
- **ลำดับตาม menu** — permission grid ของ role และมุมมอง grant แบบ read-only ต่างก็เรียงลำดับ resource ตามลำดับเดียวกับที่ sidebar ใช้ (`NAV_RESOURCE_ORDER`/`resourceRank()` ใน `backstageNav.ts` derive จาก prefix ของ `permission` แต่ละรายการ nav แบบแรกที่ปรากฏชนะ) **comment ในซอร์สของ `backstageNav.ts` เองยังระบุ `rbac` และ `license` เป็นตัวอย่าง resource ที่ไม่มีแถว menu เป็นของตัวเอง — comment นั้นล้าสมัยแล้ว** `platform_role` (resource ของโมดูลนี้เอง เปลี่ยนชื่อจาก `role`/`rbac` เมื่อ 2026-08-20) ตอนนี้มีแถว nav **Backstage Roles** เป็นของตัวเองแล้ว จึงเรียงลำดับปกติ ไม่ได้อยู่ท้ายกลุ่มที่ไม่มี menu เมื่อ grep ทุกจุดที่เรียก `permission="resource.action"` / `requiredPermission` / `hasPermission()` เทียบกับรายการ permission ของ nav เอง resource สองตัวที่ไม่มีแถว menu เป็นของตัวเองในปัจจุบันจริง ๆ คือ **`activity_log`** (gate "View History" แบบข้าม module ที่ใช้ใน Clusters/Business Units/Users ไม่ใช่โมดูลนี้) และ **`license`** (key ภายในหน้าของโมดูล Licenses แยกจาก key ระดับ nav `subscription.*` ของโมดูลนั้น) — ทั้งสองจะเรียงหลังสุดตามลำดับ catalog ในกลุ่มของตัวเอง นี่คือเหตุผลที่ permission ของ `cluster` มักปรากฏก่อน permission ของ `news` ใน picker เสมอ — มันสะท้อน sidebar ที่ผู้อ่านเพิ่งผ่านมา ไม่ใช่ลำดับตัวอักษรหรือลำดับในฐานข้อมูล
- **ความสามารถในการ audit** ตาราง RBAC ทั้งห้าตัวมี audit trio มาตรฐานของแพลตฟอร์มและ unique constraint ที่รองรับ soft-delete ทุกการมอบสิทธิ์ การเปลี่ยน role และ assignment จึงสืบย้อนถึงผู้กระทำได้และย้อนกลับได้โดยไม่เกิด key ชนกัน — ต่างจากคอลัมน์ enum เดิมที่เปลี่ยนค่าในที่เงียบ ๆ มีช่องว่างหนึ่งจุด: `GET /api-system/backstage/roles/:id` (endpoint ที่ `RoleEdit` โหลดข้อมูล role มา) **ไม่ส่ง audit block กลับมาเลย** — SPA จึง fallback ไปอ่าน audit field จาก row ของ role นั้นใน endpoint แบบ *list* แทน (จับคู่ด้วย `id`, best-effort) เพื่อให้ identity hero ยังแสดงบรรทัด "created/updated" ได้

## 3. แนวคิดสำคัญ

- **Permission key** — string รูปแบบ `resource.action` catalog เก็บ `resource` และ `action` เป็นคอลัมน์แยกกัน; key ถูก derive ขึ้นมา key ถูกกำหนดโดย backend — SPA อ่านได้อย่างเดียว ตัวอย่าง key ที่เป็นตัวแทน:

| Key ตัวอย่าง | เปิดอะไร |
|---|---|
| `backstage_role.read` | หน้า list ของ Roles และมุมมอง detail ของ role **ไม่ใช่** Permission Catalog — route นั้นไม่มี permission key เลย (ดู §1) แม้ว่าตัว data fetch ของ catalog เองจะถูกบังคับที่ฝั่ง backend ด้วย key เดียวกันนี้ |
| `backstage_role.create` / `backstage_role.update` / `backstage_role.delete` | action สร้าง/แก้ไข/ลบ role (เปลี่ยนชื่อจาก `role.*` เมื่อ 2026-08-20, `8df0b10`) |
| `user_backstage.read` | หน้า list และ detail ของ Backstage Users (read-only) |
| `user_backstage.manage` | เพิ่ม/ลบ role assignment บนหน้า detail (gate `<Can>` ภายในหน้า) |
| `cluster.read` | หน้า list ของ Clusters — และหน้า list ของ Business Units ผ่านการ reuse key (ดู §6) |
| `broadcast.send` | route Send Broadcast เพียงตัวเดียว — ตัวอย่าง action segment ที่ไม่ใช่ CRUD |

- **Role** — ชุดของ permission key ที่มีชื่อ พร้อม `is_active` และ description การเขียน role เป็น **delta**: SPA ส่ง `permissions: { add: string[], remove?: string[] }` ที่คำนวณเทียบกับชุด key ที่โหลดมาตอน fetch ไม่ใช่ชุดเต็มที่ต้องการ
- **Assignment และ Scope** — row ใน `tb_user_tb_backstage_role` ที่ผูก user + role + scope ใน SPA `Scope` เป็น union `{ type: 'backstage' } | { type: 'cluster', cluster_id }`; ใน Prisma เป็นคอลัมน์ `cluster_id` ที่เป็น nullable คอลัมน์เดียว (`null` = ทั้งแพลตฟอร์ม)
- **EffectivePermissions** — `{ backstage: string[], clusters: Record<clusterId, string[]>, is_super_admin?: boolean }` ดึงหลัง login และทุกครั้งที่ `AuthProvider` mount ผ่าน `GET /api/user/permission/backstage` cache ใน `localStorage` ภายใต้ key `effectivePermissions`
- **ลำดับของ `checkPermission`** (`src/utils/permissions.ts`) — super-admin bypass มาก่อน; จากนั้น array `platform` (สิทธิ์ระดับแพลตฟอร์มใช้ได้ทุกที่); จากนั้น ถ้ามี `clusterId` ดูเฉพาะ array ของ cluster นั้น; ถ้าไม่มี ดู array ของ cluster ใดก็ได้ (การตรวจสอบแบบกว้าง "แสดง nav/หน้านี้ไหม") ไม่เปลี่ยนแปลงตั้งแต่ sync ครั้งก่อน — ตรวจสอบกับซอร์สปัจจุบันบรรทัดต่อบรรทัดแล้ว
- **ข้อยกเว้น bootstrap** — เมื่อจำนวนผู้ใช้รวมเป็น 0 หรือ 1 `login()` จะข้าม gate ที่ต้องมีอย่างน้อย 1 permission และ `hasPermission()` คืน `true` โดยไม่มีเงื่อนไข — ข้อยกเว้นนี้หยุดมีผลทันทีที่มีผู้ใช้คนที่สอง
- **Flag super-admin ≠ role** — `tb_backstage_super_admin` คือตาราง flag ต่อผู้ใช้ ไม่ใช่ role ใน `tb_backstage_role` ปรากฏเป็น `is_super_admin` ใน payload ของ effective-permissions และ short-circuit ทุกการตรวจสอบก่อนที่จะดู key ใด ๆ

## 4. บทบาทและ Persona

การเข้าถึงหน้าจอ RBAC ทั้งสี่ก็ถูก gate ด้วย permission เช่นกัน route guard ใช้ `requiredPermission` (หรือ `requireSuperAdmin`) บน `PrivateRoute`; หน้าจอ Roles และหน้า detail ของ Backstage Users ยัง gate action ภายในหน้าด้วย `<Can>` เพิ่มเติม (Permission Catalog, Super Admins และ list ของ Backstage Users ไม่มี gate ภายในหน้าเลย — route guard คือด่านเดียว):

| หน้าจอ | Route | Route guard | Gate ภายในหน้า |
|---|---|---|---|
| Roles list | `/backstage/roles` | `backstage_role.read` (`feature="backstage_roles"`) | Add คือ `<Can permission="backstage_role.create">`; Edit ของแถวคือ `<Can permission="backstage_role.update">`; Delete ของแถวคือ `<Can permission="backstage_role.delete">` Export ยังไม่ถูก gate |
| Role create | `/backstage/roles/new` | `backstage_role.create` (`feature="backstage_roles"`) | ไม่มี |
| Role edit | `/backstage/roles/:id/edit` | `backstage_role.update` (`feature="backstage_roles"`) | ปุ่ม **Edit** บน header คือ `<Can permission="backstage_role.update">` |
| Permission Catalog | `/backstage/category-permissions` | **ไม่มี** — `<PrivateRoute>` เปล่า ๆ ไม่มี `requiredPermission`/`feature`; ผู้ใช้ backstage ที่ login แล้วคนใดก็เปิดได้ การเรียก `GET .../permissions` ของหน้านี้เองถูกบังคับที่ฝั่ง backend ด้วย `backstage_role.read` (session ที่ไม่มี key นี้จะได้ toast 403 และ grid ว่างเปล่า) | ไม่มี (หน้าจอ read-only) |
| Super Admins | `/backstage/super-admins` | `requireSuperAdmin` (`feature="super_admins"`) | ไม่มี — มีเพียง super admin เท่านั้นที่เข้าถึงหน้านี้ได้ |
| Backstage Users list | `/backstage/user-backstage` | `user_backstage.read` (`feature="user_backstage"`) | ไม่มี |
| Backstage Users detail | `/backstage/user-backstage/:userId` | `user_backstage.read` | `<Can permission="user_backstage.manage">` ห่อปุ่ม Add Role, ฟอร์ม add-role และปุ่ม Remove ของแต่ละ row |

array ของ sidebar อยู่ที่ `src/components/nav/backstageNav.ts` (`ALL_BACKSTAGE_NAV_ITEMS` กรองผ่าน `buildBackstageNav()`) — `Layout.tsx` เรียกฟังก์ชันนี้อย่างเดียว ไม่ได้นิยาม array ของ nav เองอีกต่อไป:

| รายการ sidebar | เงื่อนไข filter |
|---|---|
| Backstage Roles (ป้ายชื่อ "Backstage Roles" ไม่ใช่ "Roles") | `permission: 'backstage_role.read'`, `feature: 'backstage_roles'` |
| Super Admins | `superAdminOnly: true`, `feature: 'super_admins'` |
| Backstage Users | `permission: 'user_backstage.read'`, `feature: 'user_backstage'` |
| Permission Catalog | — ไม่มีรายการ sidebar; เข้าถึงจากปุ่ม header ของหน้า Roles |

route guard ที่ไม่ผ่านจะ render หน้า `Forbidden` (เปลี่ยนชื่อจาก component `AccessDenied` ที่เคยประกาศ inline ใน `PrivateRoute.tsx`) **ในตำแหน่งเดิม** โดย URL ไม่เปลี่ยน ภายใน shell `<Layout>` ปกติ — sidebar ยังมองเห็นอยู่ session ยังใช้ได้ และมีสอง action ให้เลือก: "Go Back" (รู้บริบท ถ้าไม่มีปลายทางย้อนกลับที่เหมาะสมจะ fallback ไป `/dashboard`) และ "Go to Dashboard" route `/403` โดยตรงก็ render หน้าเดียวกันนี้ `/dashboard` และ `/profile` ยังคงเป็น authenticated-only — ผู้ใช้ที่ login แล้วทุกคนเข้าถึงได้โดยไม่ขึ้นกับ permission แผนที่ key ต่อ route ฉบับเต็มของส่วนที่เหลือใน SPA อยู่ใน [Permissions](/th/backstage/rbac/permissions)

## 5. การย้ายจากแบบจำลอง role เดิม

จนถึง 2026-06-10 SPA gate การเข้าถึงด้วย enum `platform_role` ค่าเดียวบน row ของ user (`platform_admin`, `support_manager`, `support_staff` ฯลฯ) และ array `allowedRoles` บนแต่ละ route แบบจำลองนั้นถูกถอดออกทั้งหมดแล้ว — จาก frontend ใน commit `6091ffc` ("remove legacy platform_role from frontend") และจาก gate ตอน login ใน commit `5f629f2` ("permission-based login gate — drop platform_role/ALLOWED_ROLES from login") ทั้งคู่ใน repo `carmen-backstage` enum `enum_platform_role` และคอลัมน์ `tb_user.platform_role` ก็หายไปจาก Prisma platform schema ฝั่ง backend เช่นกัน

| ของเดิม (ถูกถอดออก) | สิ่งที่มาแทน | หมายเหตุ |
|---|---|---|
| enum `tb_user.platform_role` (หนึ่งค่าต่อผู้ใช้) | Catalog + role + assignment แบบมี scope (`tb_backstage_permission` / `tb_backstage_role` / `tb_user_tb_backstage_role`) | ตอนนี้ผู้ใช้ถือได้หลาย role แต่ละตัวเป็นระดับแพลตฟอร์มหรือต่อ cluster |
| prop `allowedRoles={[...]}` บน `PrivateRoute` | `requiredPermission="resource.action"` (หรือ `requireSuperAdmin`) | หนึ่ง key ต่อ route แทน array ของ role ที่ซ้ำกันไปมา |
| `AuthContext.hasRole(roles[])` | `AuthContext.hasPermission(key, { clusterId? })` → `checkPermission` | ทางหนี bootstrap แบบเดียวกันถูกยกมาด้วย |
| allow-list ชื่อ role `ALLOWED_ROLES` ตอน login | Gate ต้องถืออย่างน้อย 1 permission (super-admin, key ระดับแพลตฟอร์มใดก็ได้ หรือ key ระดับ cluster ใดก็ได้) | Commit `5f629f2`; ข้อยกเว้น bootstrap ใช้กับ gate นี้ด้วย |
| filter `roles: [...]` ของ sidebar ใน `Layout.tsx` | filter `permission:` / `superAdminOnly:` ของ sidebar | พฤติกรรม hide-don't-disable แบบเดิม |
| ค่า enum `super_admin` | ตาราง flag `tb_backstage_super_admin` → bypass ผ่าน `is_super_admin` | Flag ที่มี semantics ของการ bypass จริง ต่างจากค่า enum เดิมที่ไม่ได้เปิด route เพิ่ม |
| ข้อความ AccessDenied ที่อ้างชื่อ role ที่ไม่ผ่าน | ข้อความทั่วไป "You don't have permission to access this page." | SPA ไม่มีค่า role เดี่ยวให้แสดงอีกต่อไป |

โมดูลนี้แทนที่หน้า Authentication & Roles เดิม (ถูกถอดออกจาก wiki นี้แล้ว); สิ่งใดที่เขียนอิงแบบจำลองเก่า (ชื่อ role อย่าง `support_manager`/`support_staff`, ตาราง `allowedRoles`) อธิบายพฤติกรรมที่ไม่มีอยู่ใน SPA อีกต่อไป

## 6. โมดูลที่เกี่ยวข้อง

- [users](/th/backstage/users) — เป็นเจ้าของ row identity ใน `tb_user` ที่ assignment และ flag super-admin ชี้ไป การสร้าง/lifecycle ของผู้ใช้ยังอยู่ในโมดูล Users; หน้าจอ Backstage Users จัดการเฉพาะ role assignment **หมายเหตุข้ามโมดูล:** `tb_user` ได้คอลัมน์ email-verification สามตัว (`email_verified_at` และอีกสองตัว, migration `20260804000000_user_email_verification`) ที่ไม่มีหน้าไหนในโมดูลนี้เองอ่าน — จุดเดียวใน SPA ที่ใช้คือ badge "Email Unverified" บน `UserBackstageEdit.tsx` (`!!userRecord?.email_verified_at`, บรรทัด 198) บันทึกไว้ที่ [users/data-model](/th/backstage/users/data-model) เพราะคอลัมน์อยู่ที่ `tb_user`; ระบุไว้ที่นี่เพราะผู้ใช้ UI จุดเดียวคือหน้าจอที่โมดูลนี้เอกสารอยู่ในปัจจุบัน
- [applications](/th/backstage/applications) — ฝั่ง machine-client ที่เป็นคู่เทียบ: มอบ key `api_name` (รูปแบบ `resource.action` เดียวกัน) ให้ API client มีประโยชน์ในการเทียบเคียงเมื่อพิจารณาว่า caller ถูก gate ด้วย RBAC (session ของมนุษย์) หรือ application grant (token ของ machine)
- [clusters](/th/backstage/clusters) — assignment ที่มี scope ระดับ cluster อ้างอิง id ของ `tb_cluster`; dropdown cluster ในฟอร์ม add-role ถูกป้อนด้วยรายการ cluster หน้าจอ cluster ถูก guard ด้วย `cluster.read/create/update`
- [business-units](/th/backstage/business-units) — **gotcha:** route `/business-units`, `/business-units/new` และ `/business-units/:id/edit` reuse key `cluster.read` / `cluster.create` / `cluster.update` ไม่มี key `business_unit.*` — การมอบสิทธิ์เข้าถึง cluster จึงมอบ Business Units ไปด้วย และแยกมอบอย่างใดอย่างหนึ่งไม่ได้
- **ระวังสับสน seed "Role permissions" ของ Backstage Migrations กับโมดูลนี้.** คอนโซล seed ที่ `/backstage/migrations` มี op ชื่อ `seed-role-permission` ("Role permissions: Bindings between app roles and permissions") ที่ **`carmen-backstage` PR #281** (2026-09-04, commit `157a65e` ใน repo `carmen-backstage` — มี PR #281 อีกตัวที่ไม่เกี่ยวกันอยู่ใน `carmen-turborepo-backend` อย่าสับสนสองอันนี้) ขยายให้เลือกได้หลาย Business Unit พร้อมกัน (โหมด `multiple` ใหม่ของ `BuSwitcher`) แทนที่จะรันทีละ BU op นี้ seed **catalog role ระดับ tenant** ที่ Carmen Blue เองใช้ (role แบบ `Requestor`/`Approver` ผูกกับ Business Unit — `../carmen-turborepo-backend/packages/prisma-shared-schema-backstage/prisma/seed.role-permission.ts`) ซึ่งไม่เกี่ยวกับตาราง `tb_backstage_role`/`tb_backstage_permission` ของโมดูลนี้เลย op ที่ seed ข้อมูลของ*โมดูลนี้*จริง ๆ คือ `seed-backstage-role-permission` ซึ่งเป็นระดับแพลตฟอร์มทั้งหมด ไม่มีพารามิเตอร์ BU และ PR นี้ไม่ได้แตะต้อง

## 7. หน้าในโมดูลนี้

- [Data Model](/th/backstage/rbac/data-model) — ตาราง Prisma ทั้งห้า, unique constraint แบบ soft-delete, คอลัมน์ scope และความแตกต่างจาก shape TypeScript ของ SPA
- [UI Screens](/th/backstage/rbac/ui-screens) — list/edit ของ Roles พร้อม PermissionGrid แบบแถวต่อ resource, Permission Catalog แบบ read-only, และ (ระดับสรุป) ทะเบียน Super Admins กับหน้าจอ assignment ของ Backstage Users
- [Permissions](/th/backstage/rbac/permissions) — เมทริกซ์ route-guard ฉบับเต็ม, การประกอบกันของ gate ระดับ route/sidebar/ภายในหน้า, อัลกอริทึมการ resolve permission และกรณีพิเศษสำหรับผู้ทดสอบ
