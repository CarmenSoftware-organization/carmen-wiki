---
title: Platform RBAC — แบบจำลองข้อมูล (Data Model)
description: ตาราง RBAC ทั้งห้า — permission catalog, role, join ระหว่าง role กับ permission, assignment ผู้ใช้แบบมี scope, flag super-admin — การ rollout doc_version เมื่อ 2026-07-16 และความแตกต่างจาก shape ของ SPA
published: true
date: 2026-09-05T00:00:00.000Z
tags: book/platform, rbac, data-model
editor: markdown
dateCreated: 2026-06-10T15:00:00.000Z
---

# Platform RBAC — แบบจำลองข้อมูล (Data Model)

> **At a Glance**
> **ตาราง:** `tb_platform_permission` &nbsp;·&nbsp; `tb_platform_role` &nbsp;·&nbsp; `tb_platform_role_tb_permission` &nbsp;·&nbsp; `tb_user_tb_platform_role` &nbsp;·&nbsp; `tb_platform_super_admin` &nbsp;·&nbsp; **Enum:** ไม่มี — `resource`/`action` เป็น VarChar รูปแบบอิสระ &nbsp;·&nbsp; **Scope:** `cluster_id` แบบ nullable บน assignment row (`null` = ทั้งแพลตฟอร์ม) &nbsp;·&nbsp; **คอลัมน์ audit:** trio มาตรฐาน `created_*`/`updated_*`/`deleted_*` บนทุกตาราง บวก `doc_version Int @default(0)` บนทั้งห้าตาราง (เพิ่มเมื่อ 2026-07-16, การ rollout optimistic-lock ทั้งแพลตฟอร์ม) &nbsp;·&nbsp; **Unique แบบ soft-delete:** uniqueness constraint ทุกตัวรวม `deleted_at` ดังนั้น row ที่ถูกลบสามารถสร้างใหม่ได้

> **Source of truth:** Prisma platform schema ฝั่ง backend อ่านไฟล์นี้ก่อนเสมอเมื่อเขียนหรืออัพเดทหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` เป็นสำเนาที่ generate อัตโนมัติ ไม่ใช่ไฟล์อ้างอิงหลัก

## 1. ภาพรวม

โมดูล RBAC เป็นเจ้าของตารางห้าตัว จัดกลุ่มใต้ banner `// Platform RBAC` และ `// Platform Super Admin` ใน Prisma schema (บรรทัด 933–1032) `tb_platform_permission` คือ catalog: หนึ่ง row ต่อคู่ `resource` + `action` เขียนโดย backend เท่านั้น (seed/migration) — SPA อ่านได้แต่ไม่มี surface สำหรับสร้าง/แก้ไข `tb_platform_role` เก็บชุด key ที่มีชื่อ และ `tb_platform_role_tb_permission` คือ M:N join ที่บันทึกว่า role มอบ row ใดของ catalog บ้าง

`tb_user_tb_platform_role` ผูก role เข้ากับผู้ใช้พร้อม scope: คอลัมน์ `cluster_id` ที่เป็น nullable ของมันคือกลไก scope ทั้งหมด — `null` หมายถึง assignment มีผลทั้งแพลตฟอร์ม ส่วน UUID หมายถึงมีผลภายใน cluster นั้นเท่านั้น `tb_platform_super_admin` จงใจไม่เป็นส่วนหนึ่งของกราฟ role: มันคือตาราง flag (มีแค่ `user_id` + `is_active` นอกเหนือจาก audit trio) ที่ row ของมันทำเครื่องหมายผู้ใช้ที่ bypass ทุกการตรวจสอบ permission

ตารางทั้งห้ามี audit trio มาตรฐานของแพลตฟอร์ม (`created_at`/`created_by_id`, `updated_at`/`updated_by_id`, `deleted_at`/`deleted_by_id`) และใช้ unique constraint ที่รองรับ soft-delete (`deleted_at` ร่วมอยู่ในทุก `@@unique`) ดังนั้นชื่อ role, key ของ catalog, assignment หรือ flag super-admin ที่ถูกลบสามารถสร้างใหม่ได้โดยไม่เกิด unique-key ชนกัน

## 2. เอนทิตี

### 2.1 `tb_platform_permission`

permission catalog หนึ่ง row ต่อ action ที่มอบสิทธิ์ได้; SPA derive key string เป็น `resource.action` (เช่น `platform_role.read`) row เป็นข้อมูลอ้างอิงที่ backend เป็นเจ้าของ

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `resource` | `String @db.VarChar` | No | segment ฝั่ง resource ของ key (เช่น `role`, `cluster`, `user_platform`) |
| `action` | `String @db.VarChar` | No | segment ฝั่ง action ของ key (เช่น `read`, `create`, `manage`, `send`) |
| `description` | `String?` | Yes | คำอธิบายที่อ่านเข้าใจได้ แสดงบนหน้าจอ Permission Catalog และ tooltip ของ PermissionPicker |
| `doc_version` | `Int @default(0) @db.Integer` | No | Token สำหรับ optimistic-lock เพิ่มเมื่อ 2026-07-16 (rollout ทั้งแพลตฟอร์ม 35 ตาราง) |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่สร้าง |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่อัพเดทล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่ลบ |

**Constraint:**
- `@id` บน `id`
- `@@unique([resource, action, deleted_at])` — map `"platform_permission_resource_action_deleted_at_u"` — หนึ่ง live row ต่อ key; key ที่ถูก soft-delete สามารถนำกลับมาใหม่ได้

**Index:** ไม่มีนอกเหนือจาก unique map

### 2.2 `tb_platform_role`

ชุดของ permission ที่มีชื่อและเปิด/ปิดได้ ชุด key ของ role อยู่ในตาราง join ทั้งหมด (§2.3); row นี้เก็บเฉพาะ identity และสถานะ

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `name` | `String @db.VarChar` | No | ชื่อ role; unique ในหมู่ live row |
| `description` | `String?` | Yes | คำอธิบาย optional แสดงบนหน้า list ของ Roles |
| `is_active` | `Boolean?` | Yes | Default `true`; badge Active/Inactive ใน SPA |
| `doc_version` | `Int @default(0) @db.Integer` | No | Token สำหรับ optimistic-lock เพิ่มเมื่อ 2026-07-16; `RoleEdit.tsx` ส่งค่านี้ทุกครั้งที่ `PUT` และแสดง toast conflict + reload เมื่อไม่ตรงกัน |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่สร้าง |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่อัพเดทล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่ลบ |

**Constraint:**
- `@id` บน `id`
- `@@unique([name, deleted_at])` — map `"platform_role_name_deleted_at_u"` — อนุญาตให้ใช้ชื่อซ้ำได้หลัง soft delete

**Index:** ไม่มีนอกเหนือจาก unique map

### 2.3 `tb_platform_role_tb_permission`

M:N join ระหว่าง role กับ row ของ catalog แต่ละ row มอบหนึ่ง permission ให้หนึ่ง role การเขียนแบบ delta ของ SPA (`permissions: { add, remove }`) แปลเป็นการ insert และ soft-delete row ที่นี่

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()` |
| `platform_role_id` | `String @db.Uuid` | No | FK ไป `tb_platform_role.id` |
| `platform_permission_id` | `String @db.Uuid` | No | FK ไป `tb_platform_permission.id` |
| `is_active` | `Boolean?` | Yes | Default `true`; flag ว่า grant ยัง active |
| `doc_version` | `Int @default(0) @db.Integer` | No | Token สำหรับ optimistic-lock เพิ่มเมื่อ 2026-07-16 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่สร้าง |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่อัพเดทล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่ลบ |

**Constraint:**
- `@id` บน `id`
- FK: `platform_role_id` → `tb_platform_role.id` (`onDelete: NoAction, onUpdate: NoAction`)
- FK: `platform_permission_id` → `tb_platform_permission.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([platform_role_id, platform_permission_id, deleted_at])` — map `"platform_role_permission_deleted_at_u"` — grant ที่ถูกลบสามารถเพิ่มกลับได้

**Index:**
- `@@index([platform_permission_id, deleted_at])` — map `"platform_role_permission_permission_deleted_at_idx"` — รองรับการค้นหา "role ใดมอบ key X บ้าง"

### 2.4 `tb_user_tb_platform_role`

ตาราง assignment: ผูกผู้ใช้เข้ากับ role ที่ scope หนึ่ง นี่คือ row ที่หน้าจอ detail ของ User Platform สร้างและลบ และเป็น input ของการ flatten effective-permissions

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()`; คือ `assignmentId` ที่ endpoint delete ใช้ |
| `user_id` | `String @db.Uuid` | No | id ของผู้ใช้เป้าหมาย — คอลัมน์ธรรมดา **ไม่มี Prisma `@relation` ไป `tb_user`** |
| `platform_role_id` | `String @db.Uuid` | No | FK ไป `tb_platform_role.id` |
| `cluster_id` | `String? @db.Uuid` | Yes | Scope: `null` = scope ทั้งแพลตฟอร์ม; มีค่า = scope เฉพาะ cluster นี้ (ตาม comment ใน schema คำต่อคำ) คอลัมน์ธรรมดา ไม่มี `@relation` ไป `tb_cluster` |
| `doc_version` | `Int @default(0) @db.Integer` | No | Token สำหรับ optimistic-lock เพิ่มเมื่อ 2026-07-16 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่สร้าง |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่อัพเดทล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่ลบ |

**Constraint:**
- `@id` บน `id`
- FK: `platform_role_id` → `tb_platform_role.id` (`onDelete: NoAction, onUpdate: NoAction`)
- `@@unique([user_id, platform_role_id, cluster_id, deleted_at])` — map `"user_platform_role_deleted_at_u"` — role เดียวกัน assign ให้ผู้ใช้คนเดียวกันได้หนึ่งครั้งต่อ scope ที่แตกต่างกัน

**Index:**
- `@@index([user_id, deleted_at])` — map `"user_platform_role_user_deleted_at_idx"` — ขับเคลื่อน "role ของผู้ใช้ X" (endpoint list และการ flatten effective-permissions)
- `@@index([cluster_id, deleted_at])` — map `"user_platform_role_cluster_deleted_at_idx"` — ขับเคลื่อน "assignment ที่ scope ไปยัง cluster Y"

### 2.5 `tb_platform_super_admin`

flag สำหรับ bypass การมี live row ที่นี่ทำให้ `is_super_admin: true` ปรากฏใน payload effective-permissions ของผู้ใช้ short-circuit ทุกการตรวจสอบ มันไม่อ้างอิง role หรือ permission ใด ๆ — การเป็นสมาชิกคือ semantics ทั้งหมด

| Field | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key, default `gen_random_uuid()`; คือ id ที่ endpoint remove ใช้ |
| `user_id` | `String @db.Uuid` | No | id ของผู้ใช้ที่ถูก flag — คอลัมน์ธรรมดา ไม่มี `@relation` ไป `tb_user` |
| `is_active` | `Boolean?` | Yes | Default `true`; SPA render row ที่ Inactive แต่ row เหล่านั้นมีอยู่ในข้อมูล |
| `doc_version` | `Int @default(0) @db.Integer` | No | Token สำหรับ optimistic-lock เพิ่มเมื่อ 2026-07-16 |
| `created_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาสร้าง row, default `now()` — แสดงเป็น "Added" ใน SPA |
| `created_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่สร้าง |
| `updated_at` | `DateTime? @db.Timestamptz(6)` | Yes | Audit: เวลาอัพเดทล่าสุด, default `now()` |
| `updated_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่อัพเดทล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp ของ soft-delete; NULL = row ที่ยังใช้งานอยู่ |
| `deleted_by_id` | `String? @db.Uuid` | Yes | Audit: id ของผู้ใช้ที่ลบ |

**Constraint:**
- `@id` บน `id`
- `@@unique([user_id, deleted_at])` — map `"platform_super_admin_user_deleted_at_u"` — หนึ่ง live flag ต่อผู้ใช้; ถอดออกแล้วมอบใหม่ได้

**Index:** ไม่มีนอกเหนือจาก unique map

## 3. ความสัมพันธ์

```
tb_platform_role  1 ─── M  tb_platform_role_tb_permission  M ─── 1  tb_platform_permission
tb_platform_role  1 ─── M  tb_user_tb_platform_role
tb_user_tb_platform_role.user_id     ──>  tb_user.id     (application-level, no Prisma FK)
tb_user_tb_platform_role.cluster_id  ──>  tb_cluster.id  (application-level, no Prisma FK; null = platform scope)
tb_platform_super_admin.user_id      ──>  tb_user.id     (application-level, no Prisma FK)
```

FK relation ที่ประกาศไว้ (ทั้งคู่เป็น `onDelete: NoAction, onUpdate: NoAction`):

- `tb_platform_role_tb_permission.platform_role_id` → `tb_platform_role.id`
- `tb_platform_role_tb_permission.platform_permission_id` → `tb_platform_permission.id`
- `tb_user_tb_platform_role.platform_role_id` → `tb_platform_role.id`

สังเกตความไม่สมมาตร: มีเพียง link ฝั่ง role เท่านั้นที่เป็น Prisma relation จริง `user_id` (ทั้งบนตาราง assignment และ super-admin) และ `cluster_id` (บนตาราง assignment) เป็นคอลัมน์ UUID ธรรมดาที่ **ไม่มี directive `@relation` และไม่มี FK ในฐานข้อมูล** — referential integrity ไปยัง `tb_user` และ `tb_cluster` ถูกบังคับใช้ที่ชั้น application การลบผู้ใช้หรือ cluster ไม่ cascade เข้าตารางเหล่านี้; assignment row ที่เป็น orphan เกิดขึ้นได้ในระดับ schema และผู้ทดสอบไม่ควรสันนิษฐานว่าฐานข้อมูลป้องกันไว้

## 4. Enum

โมดูลนี้ **ไม่กำหนด enum ใด ๆ** สองจุดที่อาจคาดว่าจะเป็น enum ถูกตั้งใจไม่ให้เป็น enum:

- **Permission key** — `resource` และ `action` เป็นคอลัมน์ `VarChar` รูปแบบอิสระ คลังศัพท์ของ key เป็นข้อมูลปลายเปิด ขยายโดย seed/migration ฝั่ง backend โดยไม่ต้องเปลี่ยน schema
- **Scope** — model เป็นคอลัมน์ `cluster_id` แบบ nullable บน `tb_user_tb_platform_role` ไม่ใช่ enum ชนิด scope union type `Scope` ของ SPA (§5) เป็นโครงสร้างฝั่ง client ที่สร้างทับคอลัมน์นั้น

enum role 7 ค่าแบบเดิมที่เคยอยู่บน row ของ user ถูกถอดออกจาก schema ทั้งหมดแล้ว — ดูส่วน migration ของ[หน้า landing ของโมดูล](/th/platform/rbac)

## 5. ความแตกต่างจาก shape ของ carmen-platform SPA

type ของ SPA อยู่ใน `../carmen-platform/src/types/index.ts` (`Role`, `PermissionCatalogItem`, `UserRoleAssignment`, `Scope`, `EffectivePermissions`) API flatten กราฟ Prisma ลงไปมาก:

| Shape ของ SPA | แหล่งที่มาใน SPA | การจัดเก็บใน Prisma | หมายเหตุ |
| --------- | ---------- | -------------- | ----- |
| `Role.permissions: string[]` (key string) | `Role` | join row ใน `tb_platform_role_tb_permission` | API flatten join row เป็น string `resource.action` ที่ derive แล้ว; SPA ไม่เคยเห็น id ของ join-row การเขียนส่งกลับเป็น delta `{ add, remove }` (`roleService.RoleWriteData`) ไม่ใช่ชุดเต็ม |
| `permission_count` บน row ของ list | `RoleRow` ใน `RoleManagement.tsx` | ไม่ใช่คอลัมน์ | aggregate ฝั่ง server เหนือ live join row; **ไม่มีในผลลัพธ์การอ่าน role เดี่ยว** (`Role.permission_count?` ใน `types/index.ts` ระบุว่า "list read model only") — reach ที่แสดงใน `RoleIdentityHero` จึงคำนวณฝั่ง client จาก `formData.permissions.length` แทน |
| `PermissionCatalogItem.key` | `permissionService.getCatalog` | ไม่ใช่คอลัมน์ | Derive ขึ้นมา; service สังเคราะห์ `` `${resource}.${action}` `` เมื่อ response ไม่มี `key` |
| `PermissionCatalogItem.created_at`/`created_by_name`/`audit` | mapper ของ `permissionService.getCatalog` | audit trio บน `tb_platform_permission` | เป็น optional และในทางปฏิบัติแทบไม่มีค่าเลย: `tb_platform_permission` เป็นข้อมูล seed ที่ `created_by_id` เป็น null ทุก row จึงทำให้บรรทัด `latestActor()`/`AuditMeta` ต่อ item ของ `PermissionCatalog.tsx` ไม่แสดงอะไรในปัจจุบัน field เหล่านี้ถูกเก็บไว้ใน type/mapper เผื่อ backend เริ่ม attribute การแก้ไข catalog ให้ actor ในอนาคต |
| union `Scope` `{ type: 'platform' } \| { type: 'cluster', cluster_id }` | `Scope` | คอลัมน์ `cluster_id` แบบ nullable คอลัมน์เดียว | discriminated union เป็นโครงสร้างของ API/client; `type: 'platform'` ⇔ `cluster_id IS NULL` |
| `UserRoleAssignment.role_name` | `UserRoleAssignment` | ไม่ใช่คอลัมน์ | API join มาจาก `tb_platform_role.name` เพื่อการแสดงผล |
| `EffectivePermissions` `{ platform, clusters, is_super_admin }` | `EffectivePermissions` | ไม่มีตาราง | การ flatten ที่คำนวณจาก assignment ที่ live ทั้งหมด + flag super-admin; เสิร์ฟโดย `GET /api/user/permission/platform` |
| `created_at`/`created_by_name` (หรือ `created_by: {id,name}`) แบบแบนบน row ของ role list | `RoleManagement.tsx` (ผ่าน `auditColumns()`/`normalizeAudit()` ที่ใช้ร่วมกัน) | คอลัมน์ audit id | response ของ list อาจซ้อนข้อมูล audit เป็น `audit.created/updated` `{ at, name }`; `normalizeAudit()` **ลองรูปแบบ nested ก่อนเสมอ** แล้วค่อย fallback ไปคอลัมน์แบบแบนเมื่อไม่มี entry แบบ nested เท่านั้น — ไม่ใช่ทางกลับกัน cell ของ list แสดงผลเป็นเวลาแบบ relative (`AuditMeta`, เช่น "5mo ago") พร้อม timestamp เต็มเป็น tooltip `title` ไม่ใช่ string ตายตัว; คอลัมน์ Updated จะถูกซ่อนก็ต่อเมื่อ record ยังไม่เคยถูกแก้ไขจริง (`everEdited`: มีชื่อ actor ที่แก้ หรือ `at` ต่างจาก `created.at`) — ไม่ใช่การเทียบ `updated_at === created_at` ตรง ๆ |
| **`GET /api-system/platform/roles/:id` ไม่ส่ง audit block กลับมาเลย** | `RoleEdit.fetchRole()` | n/a | payload ของ role เดี่ยวคือ `{ id, doc_version, name, description, is_active, permissions }` เท่านั้น `RoleEdit.tsx` แก้ปัญหาด้วยการยิง request ที่สองแบบ best-effort — ไป query endpoint แบบ *list* กรองด้วย `id` นั้น (`advance: { where: { id } }`) แล้วดึง field audit ของ row นั้นมาใช้กับบรรทัด audit ของ `RoleIdentityHero` role ที่ไม่พบใน request สำรองนี้ (เช่นล้มเหลวชั่วคราว) ก็แค่ไม่แสดงบรรทัด audit แทนที่จะแสดงผิด |
| envelope `{ data }` หลายชั้น | `userRoleService.list`, `SuperAdminManagement.extractArray` | n/a | endpoint user-roles และ super-admins อาจซ้อน `{ data: { data: [...] } }` ลึกกว่าหนึ่งชั้นตามปกติ; consumer ทั้งสองไล่ลงไปจนเจอ array |
| `RolesSummaryData` `{ total, active, inactive, deleted, top_roles }` | `RolesResponse.summary` (`roleService.getAccessSummary()`) | aggregate เหนือ `tb_platform_role` | ไม่กรอง (ไม่มี `search`/`advance`) ดึงจาก **endpoint สรุปเฉพาะทาง** ไม่ใช่การกวาด list ด้วย `perpage: -1` `deleted` (จำนวน role ที่ถูก soft-delete) มีอยู่ในข้อมูลแต่ก่อนการเขียนใหม่ `RolesAccessSummary` เมื่อ 2026-09-02 ไม่เคยถูกแสดงเลย |
| `Role.doc_version?: number` | `Role` (`src/types/index.ts`) | `doc_version Int @default(0)` | **สอดคล้องกัน ไม่ใช่ความแตกต่าง** — เพิ่มทั้งสองฝั่งใน rollout เมื่อ 2026-07-16 `RoleEdit.tsx` อ่านผ่าน `getDocVersion()` และส่งกลับตอน `PUT` พร้อม delta ของ `permissions` |

### 5.1 Endpoint

REST surface ที่ service ของ SPA ใช้ (`roleService.ts`, `permissionService.ts`, `superAdminService.ts`, `userRoleService.ts`):

| Method + Path | วัตถุประสงค์ | หมายเหตุ |
|---|---|---|
| `GET /api-system/platform/roles` | list ของ role | แบ่งหน้า; row มี `permission_count` และอาจมี `audit` ซ้อนอยู่; response อาจมี block `summary` (`RolesSummaryData`) |
| `GET /api-system/platform/roles/summary` | สรุปการเข้าถึงของ role (เพิ่มใหม่ตั้งแต่ sync ครั้งก่อน) | `roleService.getAccessSummary()` — aggregate ทั้งระบบ ไม่กรองตาม search/filter ปัจจุบันของตาราง |
| `POST /api-system/platform/roles` | สร้าง role | body มี `permissions: { add: string[] }` |
| `GET /api-system/platform/roles/:id` | detail ของ role | คืน `permissions: string[]` ที่ flatten แล้ว; **ไม่มี audit block** (ดู §5 ด้านบน) |
| `PUT /api-system/platform/roles/:id` | อัพเดท role | body มี `permissions: { add: string[], remove: string[] }` (delta) บวก `doc_version` เมื่อทราบค่า — ไม่ตรงกันจะแสดง toast conflict และหน้าจะ re-fetch |
| `DELETE /api-system/platform/roles/:id` | ลบ role | |
| `GET /api-system/platform/permissions` | permission catalog | read-only; ไม่มี endpoint สำหรับเขียนใน SPA **บังคับที่ฝั่ง backend ด้วย `platform_role.read`** (`RequirePlatformPermission`, `platform-permissions.controller.ts`) แม้ว่า route ของ SPA ที่เรียก (`/platform/category-permissions`) จะไม่มี permission gate ที่ฝั่ง frontend เลยก็ตาม |
| `GET /api-system/platform/super-admins` | list ของ super-admin | response อาจซ้อน envelope `{ data }` หลายชั้น |
| `POST /api-system/platform/super-admins` | มอบ flag | body `{ user_id }` |
| `DELETE /api-system/platform/super-admins/:id` | ถอน flag | `:id` คือ id ของ flag-row ไม่ใช่ id ของผู้ใช้ |
| `GET /api-system/platform/users/:userId/roles` | list assignment | response อาจซ้อน envelope `{ data }` หลายชั้น |
| `POST /api-system/platform/users/:userId/roles` | เพิ่ม assignment | body `{ role_id, scope }` ด้วย shape union ของ `Scope` |
| `DELETE /api-system/platform/users/:userId/roles/:assignmentId` | ลบ assignment | `:assignmentId` คือ `tb_user_tb_platform_role.id` |
| `GET /api/user/permission/platform` | effective permissions ของ session ปัจจุบัน | เรียกหลัง login และทุกครั้งที่ `AuthProvider` mount |

## 6. แหล่งข้อมูลอ้างอิง

**หลัก (source of truth):**
- `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (backend HEAD `2378c3b`, 2026-09-05) — model `tb_platform_permission` (บรรทัด 1007), `tb_platform_role` (บรรทัด 1026), `tb_platform_role_tb_permission` (บรรทัด 1046), `tb_user_tb_platform_role` (บรรทัด 1067), `tb_platform_super_admin` (บรรทัด 1090) รายการ field ไม่เปลี่ยนตั้งแต่ sync ครั้งก่อน — เปลี่ยนแค่เลขบรรทัดจากตารางของโมดูลอื่นที่เพิ่มเข้ามาก่อนหน้านี้ในไฟล์

**รอง (shape ฝั่ง consumer):**
- `../carmen-platform/src/types/index.ts` — `Role`, `PermissionCatalogItem`, `UserRoleAssignment`, `Scope`, `EffectivePermissions`, `RolesSummaryData`
- `../carmen-platform/src/services/roleService.ts` — shape delta `RoleWriteData`, endpoint ของ roles, `getAccessSummary()`
- `../carmen-platform/src/services/permissionService.ts` — การ map catalog (การ derive key), การ fetch effective-permissions
- `../carmen-platform/src/pages/RoleEdit.tsx` — `fetchAudit()`, การ fallback audit จาก endpoint แบบ list สำหรับหน้า detail
- `../carmen-turborepo-backend-v2/apps/backend-gateway/src/platform/platform-permissions/platform-permissions.controller.ts` — `RequirePlatformPermission('platform_role.read')` บน endpoint ของ catalog
- `../carmen-platform/src/services/superAdminService.ts` และ `src/pages/SuperAdminManagement.tsx` — endpoint ของ super-admin และ `extractArray` ที่ไล่ลง envelope
- `../carmen-platform/src/services/userRoleService.ts` — endpoint ของ assignment และการไล่ลง envelope

**Cross-link:** [หน้า landing ของ Platform RBAC](/th/platform/rbac) &nbsp;·&nbsp; [UI Screens](/th/platform/rbac/ui-screens) &nbsp;·&nbsp; [Permissions](/th/platform/rbac/permissions) &nbsp;·&nbsp; [data-model ของ users](/th/platform/users/data-model) (row ของ `tb_user` ที่ assignment ชี้ไป)
