---
title: ผู้ใช้ระดับแผนก (Department User)
description: Pivot การเป็นสมาชิกของผู้ใช้กับแผนก — ผู้ใช้คนใดอยู่ในแผนกใด และ Head of Department (HOD) ที่ขับเคลื่อน approval routing ของ PR/SR ตั้งแต่ 2026-09-04 แก้ไขแผนกของผู้ใช้จากหน้าจอ user ได้ด้วย
published: true
date: '2026-09-23T01:30:00.000Z'
tags: access-control, department-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# ผู้ใช้ระดับแผนก (Department User)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_department_user` (tenant) &nbsp;·&nbsp; **แก้ไขจาก:** หน้าจอ Department (`/config/department/:id`, สมาชิก + HOD) **และ** ตั้งแต่ 2026-09-04 หน้าจอ User (`PATCH /api/config/:bu_code/users/:user_id { department_id }`) &nbsp;·&nbsp; **Endpoint:** `api/config/:bu_code/department-users` (App ID `departmentUser.*`; licence `configuration.department`) &nbsp;·&nbsp; **ใช้โดย:** approval routing ของ PR และ SR (ขั้น HOD, กฎ routing ตามแผนก), รายงานผลกระทบ assignee ของ workflow &nbsp;·&nbsp; Pivot การเป็นสมาชิกระหว่างผู้ใช้กับแผนก — `is_hod = true` ระบุ Head of Department ที่ต้องการการอนุมัติบน requisition ของแผนก

## สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22)

- **แก้ไขจากฝั่ง user ทำได้จริงอีกครั้ง** ส่วน Departments ของหน้าจอ User Assign เป็นแบบอ่านอย่างเดียวที่ baseline; ตั้งแต่ BE `9a91d7f32` (2026-09-04) `PATCH /api/config/:bu_code/users/:user_id` รับ `department_id` ค่าเดียว และหน้าจอแสดงเป็น `LookupDepartment` (`user-assigned-departments.tsx:38-40`, FE `39ae1bba`, 2026-09-07) endpoint ของ user คืน `department: { id, name } | null` — ค่าเดียว สอดคล้องกับกฎ membership ที่ในทางปฏิบัติเป็นแผนกเดียวด้านล่าง Error: `USER_ACCESS_DEPARTMENT_NOT_FOUND`, `USER_ACCESS_DEPARTMENT_ALREADY_HOD` (ผู้ใช้เป็น HOD ของแผนกใดแผนกหนึ่ง; การย้ายถูกปฏิเสธเพื่อไม่ให้ขั้น HOD ว่างเปล่าโดยเงียบ ๆ — `catalog.ts:351-358`) flag HOD เองยังตั้งได้จากหน้าจอ Department เท่านั้น (บล็อก HOD ของหน้าจอ user ถูกถอดออก, `5684f93e`)
- **การอ้างอิง user แบบ nested (BE `5d64f5dfd`, 2026-09-17)** `department_users[]` และ `hod_users[]` ของ detail แผนกตอนนี้มี `user: { id }` แทน `user_id` แบบ flat (ไม่มี name คู่กัน); ฟอร์มแผนกถูกแก้ให้อ่าน object (`b55294b3`) `DepartmentUserResponseDto` บน `api/config/:bu_code/department-users` ไม่เปลี่ยน (`id`, `department_id`, `user_id`, `is_active`, `doc_version`, `audit`)
- **ผลกระทบต่อ workflow** `GET api/config/:bu_code/workflows/assignees/:target_user_id` (2026-09-03) list ขั้นที่ผู้ใช้ถืออยู่ — เรียกก่อนลบผู้ใช้ออกจากแผนก; ขั้นที่ดึง actor จาก HOD ของแผนกหรือจากทั้งแผนกถูกยกเว้น เพราะการเสียสมาชิกหนึ่งคนไม่ทำให้ขั้นว่าง ดู [system-config/workflow](/th/inventory/system-config/workflow)
- `findByUserId` ยังใช้ `findFirst` (`department-user.service.ts:85`) — แผนก "สมาชิก" หนึ่งแผนกต่อผู้ใช้; ข้อค้นพบเรื่อง HOD / HOD เดียวด้านล่างตรวจสอบซ้ำแล้วและไม่เปลี่ยน

## 1. คืออะไรและใครใช้

`department-user` คือ **pivot การเป็นสมาชิกระหว่างผู้ใช้กับแผนก**: ประกาศว่า [access-control/user](/th/inventory/access-control/user) ที่กำหนดอยู่ใน [master-data/department](/th/inventory/master-data/department) ที่กำหนด การเป็นสมาชิกปกติ (`is_hod = false`) ในทางปฏิบัติเป็น **หนึ่งแผนกต่อผู้ใช้หนึ่งคน**: endpoint การ lookup (`findByUserId` ใน `department-user.service.ts`) ใช้ `findFirst` เพื่อคืนแผนก "สมาชิก" หนึ่งแผนก (nullable) และ Members picker ของหน้าจอ edit แผนกกรองผู้ใช้ที่มี `department` อยู่ที่อื่นแล้วออก ส่วน boolean `is_hod` เป็นแกนแยกต่างหากและ **สามารถครอบคลุมหลายแผนกได้** — ผู้ใช้อาจเป็น Head of Department ของหลายแผนกพร้อมกัน ไม่มี code ใดบังคับว่าแต่ละแผนกมี HOD ได้มากที่สุดหนึ่งคน (ดูกรณีพิเศษ)

Flag HOD ขับเคลื่อน logic workflow ปลายน้ำ: เมื่อ [purchase-request](/th/inventory/purchase-request) หรือ [store-requisition](/th/inventory/store-requisition) ถูก submit โดยผู้ใช้ที่แผนกของตนมี HOD pipeline การอนุมัติจะ route ขั้นตอน review ไปยัง HOD นั้น ถ้าไม่มี row ที่นี่ ผู้ใช้จะมองไม่เห็นใน approval routing ของแผนกและรายงาน cost-centre

**บำรุงรักษาโดย** Sysadmin (การมอบหมายผู้ใช้กับแผนก, flag HOD) **อ่านโดย** workflow การอนุมัติของ PR/SR, ตัว resolve scope ของ RBAC และระบบรายงาน

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| มอบหมายผู้ใช้ให้แผนก | หน้าจอ edit **Department** (`/config/department/:id`) → panel **Members** → Transfer control (`department-form.tsx`) — **หรือ** หน้าจอ User Assign (`/system-admin/user/:id`) → **Edit** → lookup Department → Save | ฝั่ง user ส่ง `PATCH …/users/:user_id { department_id }` (ค่าเดียว ไม่ใช่ add/remove); ถูกปฏิเสธด้วย `USER_ACCESS_DEPARTMENT_ALREADY_HOD` ถ้าผู้ใช้เป็น HOD ที่ไหนสักแห่ง |
| กำหนดเป็น Head of Department | หน้าจอ edit Department เดียวกัน → panel **HOD** → Transfer control | Transfer widget แยกอิสระจาก Members; การเพิ่ม/ลบไม่ถูกบล็อกด้วยการตรวจสอบ HOD ที่มีอยู่แล้วใด ๆ |
| เปลี่ยน HOD | Panel HOD → ย้าย HOD เก่ากลับ Available, ย้ายคนใหม่ไป Assigned → Save | การอนุมัติในอดีตยังคงใช้ผู้ลงนามเดิม; ไม่มีอะไรล้าง HOD คนก่อนหน้าโดยอัตโนมัติ (ดูกรณีพิเศษ) |
| ลบผู้ใช้ออกจากแผนก | Panel Members → ย้ายผู้ใช้กลับ Available → Save | ขั้นตอน PR/SR ที่เปิดอยู่ซึ่งอ้างอิงผู้ใช้นี้ไม่ได้รับผลกระทบ; การ routing ในอนาคตจะไม่พบ HOD ถ้านี่คือคนสุดท้าย |
| รายชื่อ HOD ทั้งหมดของแผนก | Query `tb_department_user WHERE department_id = ? AND is_hod = true AND deleted_at IS NULL` (`getHodInDepartment` ใน `department-user.service.ts`) | ใช้สำหรับ audit หรือการยืนยัน config ของ workflow |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Duplicate department assignment" | Unique constraint `(department_id, user_id)` บน row ที่ไม่ถูกลบ | ลบ row ที่มีอยู่ก่อน หรือ soft-delete แล้วเพิ่มใหม่ |
| Workflow ไม่สามารถ resolve HOD ได้ | ไม่มี row `is_hod = true` สำหรับแผนก | เพิ่มผู้ใช้ในหน้าจอ panel HOD ของแผนก |
| ขั้นตอนที่อนุมัติแล้วแสดงผู้ใช้ที่ถูกลบออก | ขั้นตอน approval ในอดีตบันทึกผู้ลงนาม ณ เวลาที่ดำเนินการ | ถูกต้อง — การเปลี่ยน HOD ไม่ย้อนหลัง |
| `USER_ACCESS_DEPARTMENT_ALREADY_HOD` บนหน้าจอ user | เปลี่ยนแผนกของผู้ใช้ที่เป็น HOD ของแผนกใดแผนกหนึ่ง | ถอด flag HOD บนหน้าจอ Department ก่อน |
| `USER_ACCESS_DEPARTMENT_NOT_FOUND` | `department_id` ไม่รู้จัก / ถูกลบ | เลือกแผนกที่มีอยู่ |

## 4. กรณีพิเศษ

- **HOD หนึ่งคนต่อแผนกไม่ถูกบังคับที่ไหนเลย** เส้นทางเพิ่ม HOD ของ `departments.service.ts` (`data.hod_users.add`) ตรวจสอบแค่ว่าผู้ใช้ที่กำลังทำ action มี row `is_hod = true` สำหรับ*แผนกเดียวกันนั้น*อยู่แล้วหรือไม่ (เพื่อเลี่ยง row ซ้ำ) — ไม่ตรวจสอบหรือล้าง row HOD ที่มีอยู่ของผู้ใช้*คนอื่น*ก่อน ไม่มีอะไรใน backend หรือ frontend หยุดไม่ให้ผู้ใช้สองคนขึ้นไปถูก mark เป็น HOD ของแผนกเดียวกันพร้อมกัน ถือว่า "หนึ่ง HOD ต่อแผนก" เป็นข้อตกลงการกรอกข้อมูล ไม่ใช่การรับประกัน
- **การเป็นสมาชิกปกติในทางปฏิบัติเป็นแบบหนึ่งแผนก** ขับเคลื่อนโดยรูปแบบ query (`findFirst`) และ filter ของ picker ฝั่ง frontend — ไม่ใช่ DB constraint Unique constraint คือ `(department_id, user_id, deleted_at)` ซึ่งทางเทคนิคอนุญาตให้ user เดียวกันอยู่ใน Members list ของสองแผนกได้ถ้า insert ตรง — UI และ lookup `findByUserId` แค่ไม่รองรับหรือ surface state นั้น
- **การเปลี่ยน HOD** ไม่ย้อนแก้การอนุมัติในอดีต — ขั้นตอน workflow ในอดีตยังคงใช้ผู้ที่ลงนาม
- **Soft-delete เป็นที่แนะนำ** — hard-delete ได้รับอนุญาตทางกายภาพ (ไม่มี FK target ธุรกรรมบน row นี้) แต่ soft-delete รักษา audit trail ไว้
- **ผู้ใช้ที่ไม่มีแผนก** — ผู้ใช้ที่ไม่มี row `tb_department_user` ยังคง login และถือ application role ได้ แต่ approval routing ของ PR/SR จะไม่พบเส้นทาง HOD resolution ผ่านพวกเขา
- **ฟิลด์ note / info / dimension** พร้อมใช้งานสำหรับ annotation การดำเนินงาน (เช่น comment วันที่มีผล) แต่ไม่ถูกใช้โดย logic ที่ระบบบังคับใช้

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`)

### 5.1 `tb_department_user`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String @db.Uuid` | No | อ้างอิง platform `tb_user.id`; **ไม่ใช่** Prisma FK บน model นี้ (cross-schema, pattern เดียวกับ [access-control/user-location](/th/inventory/access-control/user-location)) — มีแค่ `department_id` ที่ประกาศ `@relation` |
| `department_id` | `String @db.Uuid` | No | FK ไปยัง `tb_department` |
| `is_hod` | `Boolean?` | Yes | Default `false` `true` = Head of Department สำหรับการมอบหมายนี้ |
| `note` | `String? @db.VarChar` | Yes | Annotation แบบ free-text |
| `info` | `Json?` | Yes | Metadata ที่ไม่มีโครงสร้าง |
| `dimension` | `Json?` | Yes | Metadata มิติ |
| `doc_version` | `Int` | No | Default `0` Token สำหรับ optimistic concurrency |
| Audit columns | — | Yes | `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` |

**Constraints:** `@@unique([department_id, user_id, deleted_at])` map `department_user_u` FK `tb_department_user.department_id → tb_department.id` `onDelete: NoAction, onUpdate: NoAction` Index แบบธรรมดาสามตัว: `(department_id, user_id)`, `(user_id)`, `(department_id)` — **ไม่มี** index ที่เกี่ยวกับ `is_hod` เลยไม่ว่าจะเป็น partial หรือแบบใด ซึ่งสอดคล้องกับข้อค้นพบในกรณีพิเศษด้านบนว่าไม่มีอะไรใน schema บังคับว่าแต่ละแผนกมี HOD ได้มากที่สุดหนึ่งคน

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** อย่างมากที่สุดหนึ่ง row `(department_id, user_id)` ที่ active ต่อ combination — unique constraint ป้องกันการมอบหมายซ้ำ
- **HOD ไม่ถูกบังคับด้วย invariant** ไม่มีอะไรใน `departments.service.ts` หรือที่อื่นล้าง HOD ที่มีอยู่ของแผนกก่อนเพิ่มตัวใหม่ — ดูกรณีพิเศษ ถือว่า "หนึ่ง HOD ต่อแผนก" เป็นข้อตกลง UI/กระบวนการ ไม่ใช่การรับประกัน
- **อำนาจ HOD** `is_hod = true` ให้อำนาจการอนุมัติอัตโนมัติภายในแผนกนั้นสำหรับขั้นตอน workflow ของ PR และ SR ที่ route ไปยัง role type HOD
- **การเป็นสมาชิกในทางปฏิบัติเป็นแบบหนึ่งแผนก; HOD เป็นหลายแผนกได้อิสระ** ทั้ง lookup `findByUserId` และ Members picker ของหน้าจอ edit แผนกปฏิบัติต่อการเป็นสมาชิกที่ไม่ใช่ HOD เป็นหนึ่งแผนกต่อผู้ใช้; flag HOD เป็นแกนแยกต่างหากและผู้ใช้หนึ่งคนสามารถเป็น HOD ของหลายแผนกพร้อมกันได้
- **Soft-delete** การลบเป็นแบบ soft (`deleted_at`) เพื่อรักษา audit filter การเป็นสมาชิกที่ active ต้องการ `deleted_at IS NULL`
- **ไม่มี cascade** FK `onDelete: NoAction` — การลบแผนกที่มี row ผู้ใช้ที่ active ถูกบล็อกที่ระดับ DB; ต้องปิดใช้งานหรือมอบหมาย user ใหม่ก่อน

## 7. การอ้างอิงข้าม

- [access-control/user](/th/inventory/access-control/user) — ฝั่ง user ของ membership
- [master-data/department](/th/inventory/master-data/department) — ฝั่งแผนก; บันทึก `tb_department_user` ในส่วน Data Model ด้วย
- [purchase-request](/th/inventory/purchase-request) — approval routing ของ PR resolve HOD จาก `tb_department_user` สำหรับขั้นตอน review ระดับแผนก
- [store-requisition](/th/inventory/store-requisition) — SR routing ใช้ flag HOD เช่นกันสำหรับ requisition ระหว่างแผนก
- [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) — pivot ระดับ BU ที่เทียบเคียง (`tb_user_tb_business_unit`); การเป็นสมาชิก BU กำหนดการเข้าถึง; การเป็นสมาชิกแผนก scope approval routing ภายใน BU

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_department_user` (บรรทัด 4771)
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/department-user/department-user.service.ts` (`findByUserId`, `hasHodInDepartment`, `getHodInDepartment`); `.../apps/micro-business/src/master/departments/departments.service.ts` (Members/HOD add-remove ตอน update แผนก); `.../apps/backend-gateway/src/config/config_department-users/config_department-users.controller.ts` (`GET user/:user_id` `:71`, `GET :id`, `GET`, `POST`, `PUT :id`, `DELETE :id`); `.../apps/backend-gateway/src/config/config_users/` (PATCH `department_id` ฝั่ง user); serializer `apps/backend-gateway/src/common/dto/department/department.serializer.ts`
- **Bruno:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/department-user/`, `config/users/PATCH-patch-access-config-users.bru`
- **Docs:** `../carmen/docs/app/system-administration/user-management/DD-user-management.md` — รายละเอียด entity `tb_department_user` และ definition ของ HOD index (frozen 2026-04-27)
- **Docs:** `../carmen/docs/app/system-administration/user-management/BR-user-management.md` — BR-002: กฎทางธุรกิจ HOD Designation (design intent; ไม่ถูกบังคับใน code ปัจจุบัน — ดูกรณีพิเศษ)
- **Frontend:** `../carmen-inventory-frontend-react/routes/config/department/department-form.tsx` (Transfer widget ของ Members + HOD บนหน้าจอ edit แผนก); `routes/system-admin/user/user-assigned-departments.tsx` (lookup แผนกเดียว แก้ไขได้ตั้งแต่ 2026-09-07)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/010-department.spec.ts` (21 case อัตโนมัติ รวมการมอบหมายผู้ใช้เข้า Members และ HOD) + `docs/test-cases/gaps/010-department-gap.md` (37 case ที่ยังไม่ครอบคลุม prefix `DEP`); `docs/test-cases/1102-user.md` สำหรับฝั่ง user
