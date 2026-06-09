---
title: สิทธิ์ (Permission)
description: คู่ resource + action แบบ atomic — บล็อกสร้างที่รวมเข้าใน application role เพื่ออนุญาตทุก UI และ API operation
published: true
date: 2026-06-09T00:00:00.000Z
tags: access-control, permission, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# สิทธิ์ (Permission)

> **At a Glance**
> **เจ้าของ:** จัดการโดย seed (release-time) &nbsp;·&nbsp; **ตาราง:** `tb_permission` &nbsp;·&nbsp; **ใช้โดย:** [access-control/application-role](/th/inventory/access-control/application-role) (consumer เดียว) &nbsp;·&nbsp; คู่ `(resource, action)` แบบ atomic — หน่วยเล็กที่สุดของการอนุญาต

## 1. คืออะไรและใครใช้

Permission คือ **หน่วยเล็กที่สุดของการอนุญาต**: คู่ `(resource, action)` เช่น `(purchase_request, approve)` หรือ `(inventory, view)` Permission ถูก catalog ส่วนกลางและ **ไม่เคยมอบโดยตรง** ให้ผู้ใช้ — รวบรวมเข้าใน row [access-control/application-role](/th/inventory/access-control/application-role) ผ่าน `tb_application_role_tb_permission` และผู้ใช้ได้รับมันโดยอ้อมจากการได้รับ role

การตรวจสอบ runtime "user X ทำ action Y บน resource Z ใน BU B ได้ไหม" คือ join เดียวข้าม `tb_user_tb_application_role`, `tb_application_role` และ `tb_application_role_tb_permission`

**บำรุงรักษาโดย** release migration (seed) **อ่านโดย** UI role-edit สำหรับการ bundle และโดยทุก API request สำหรับการตรวจสอบ permission

### 1.1 สิทธิ์ comment และ approval workflow

**comment thread** แต่ละเอกสารและ **action การอนุมัติ** ถูก gate ด้วย permission atom (App ID) ของตนเอง สิทธิ์ comment ใช้ชุด verb เดียวกันในแต่ละประเภทเอกสาร:

| ประเภทเอกสาร | App ID prefix ของ comment | Actions |
|---|---|---|
| Purchase Request | `purchaseRequestComment` | `findAll`, `create`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |
| Purchase Order | `purchaseOrderComment` | `findAll`, `create`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |
| Store Requisition | `storeRequisitionComment` | `findAll`, `create`, `update`, `delete`, `addAttachment`, `removeAttachment`, `createWithFiles` |

`createWithFiles` คือ create แบบ single-call ที่ post comment พร้อม attachment ในคำขอ multipart เดียว (เทียบกับการใช้ `create` แล้วตามด้วย `addAttachment`)

Approval-workflow atom:

| App ID | วัตถุประสงค์ |
|---|---|
| `storeRequisition.approve` | อนุมัติ / ดำเนินการขั้นตอนการอนุมัติ store requisition |
| `my-approve.findAll` | แสดงรายการเอกสารทุกชนิดที่รอการอนุมัติ**ของผู้ใช้ปัจจุบัน** ข้ามประเภทเอกสาร — รองรับ approval inbox ข้ามโมดูล ([dashboard/my-approval](/th/inventory/dashboard/my-approval)) |

สิทธิ์เหล่านี้เป็น atom ที่จัดการโดย seed เหมือนกับสิทธิ์อื่น ๆ ในหน้านี้ และรวมเข้า role ผ่าน [access-control/application-role](/th/inventory/access-control/application-role)

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดู catalogue permission | Sysadmin → Platform → Permissions (read-only) | รายการจัดกลุ่มโดย `resource` |
| Bundle permission เข้า role | หน้าจอ edit [access-control/application-role](/th/inventory/access-control/application-role) | Checkbox grid; นี่คือเส้นทางปกติ |
| เพิ่ม atom permission ใหม่ | Release migration / seed | `tb_permission` จัดการโดย seed ไม่แก้ผ่าน UI |
| Rename / retire permission | Soft-delete + re-create | Constraint รวม `deleted_at` ดังนั้น `(resource, action)` re-use ได้ |
| หา role ใดรวม permission | Query `tb_application_role_tb_permission` โดย `permission_id` | มีประโยชน์ก่อนการปลดระวาง |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Permission not found" ตอน runtime | Code อ้างอิง permission ที่ถูกลบหรือไม่เคย seed | Re-seed หรือ restore ผ่าน migration |
| Duplicate `(resource, action)` insert | Row ที่ไม่ถูก delete มีอยู่แล้ว | ใช้ row ที่มีอยู่แทน |
| Feature เงียบปิดสำหรับทุกคน | Permission ถูก delete ขณะ code ยังอ้างอิง | Operational guard — restore ผ่าน migration |
| Tooltip สับสนใน role editor | `description` ขาดหายหรือสั้น | Update seed; description ควรอธิบาย *สิ่งที่ permission ปลดล็อก* |

## 4. กรณีพิเศษ

- **Closed enumeration** ชุดของ permission ปิดต่อ release — permission ใหม่มาพร้อม code ที่ตรวจสอบ
- **ไม่มี link user โดยตรง** ไม่มี join `tb_user_tb_permission` — ทุกเส้นทางไปผ่าน application role
- **Soft-delete + rename** Constraint รวม `deleted_at` ดังนั้น permission ที่ rename สามารถ soft-delete และ `(resource, action)` re-create
- **วินัย Description** `description` สำหรับ tooltip role-edit — ต้องอธิบาย *สิ่งที่ permission ปลดล็อก* ไม่ใช่แค่ restate คู่

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: platform schema

### 5.1 `tb_permission`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `resource` | `String @db.VarChar` | No | Resource เชิงตรรกะ (เช่น `purchase_request`, `inventory`, `vendor`) |
| `action` | `String @db.VarChar` | No | Verb (เช่น `view`, `create`, `update`, `delete`, `approve`, `post`) |
| `description` | `String?` | Yes | Label และเหตุผลที่อ่านได้ |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([resource, action, deleted_at])` Back-relation ไปยัง `tb_application_role_tb_permission` Audit FKs `onDelete: NoAction`

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `(resource, action)` unique ในกลุ่ม permission ที่ไม่ถูก delete; constraint รวม `deleted_at` เพื่อให้ rename ผ่าน soft-delete + re-create
- **Closed enumeration** Permission ใหม่มาพร้อม code ที่ตรวจสอบ; การ delete เป็น guard *operational* (กระบวนการ release) ไม่บังคับโดย DB
- **ไม่มี link user โดยตรง** ทุกเส้นทางการอนุญาตไปผ่าน `tb_application_role` Source of truth เดียวรักษา audit trail ให้เรียบง่าย
- **วินัย Description** จำเป็นสำหรับ tooltip ของ UI role-edit — ต้องอธิบาย consequences ไม่ใช่แค่ restate คู่

## 7. การอ้างอิงข้าม

- [access-control/application-role](/th/inventory/access-control/application-role) — consumer เดียว
- [access-control/user](/th/inventory/access-control/user) — ถือ permission โดยอ้อมผ่าน role
- ทุกโมดูลธุรกรรม — ทุก action UI ที่ guard / endpoint API ที่ protected resolve กับ `(resource, action)`

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` — `tb_permission` (lines ~323-341)
- **Frontend:** Surface ภายใน role-edit ที่ `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/user-role/` ไม่มี CRUD แบบ standalone
