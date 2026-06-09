---
title: แผนก (Department)
description: แผนกขององค์กรและการกำหนดผู้ใช้ — ใช้เป็น cost-centre และ scope การอนุมัติบนเอกสาร requisition และ PR
published: true
date: 2026-06-09T16:28:56.000Z
tags: master-data, department, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# แผนก (Department)

> **At a Glance**
> **เจ้าของ:** Product Admin (รายการ) / Sysadmin (user mapping) &nbsp;·&nbsp; **ตาราง:** `tb_department`, `tb_department_user` &nbsp;·&nbsp; **ใช้โดย:** PR, SR, approval workflows, RBAC, รายงาน &nbsp;·&nbsp; มิติ cost-centre + requesting-unit; resolve ผู้ review ระดับ Head-of-Department

![แผนก (Department) screen](/screenshots/master-data/department.png)

![แผนก (Department) detail screen](/screenshots/master-data/department-detail.png)

## 1. คืออะไร / ใครใช้

แผนกเป็น **มิติ cost-centre / requesting-unit** ของ property — Kitchen, F&B, Engineering, Housekeeping, Front Office ฯลฯ ทุกคำขอภายในสำหรับสินค้า (PR, SR) บรรจุ FK ของแผนก และ workflow อนุมัติมักจัดเส้นทางตามแผนก แผนกยังเป็นแกนเชื่อมระหว่างผู้ใช้และส่วนของธุรกิจที่พวกเขาสังกัดผ่าน `tb_department_user` ซึ่งมาร์คผู้ใช้หนึ่งคนเป็น **Head of Department** (`is_hod`)

**บริหารจัดการโดย** Product Admin (รายการแผนก, active flag) และ Sysadmin (การกำหนดผู้ใช้กับแผนก, HOD flag) **อ่านโดย** developer ใน PR/SR routing, RBAC และรายงาน

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| เพิ่มแผนก | Configuration → Master Data → Department → **New** | บังคับ: `code`, `name` |
| ยกเลิกการใช้งาน | Toggle `is_active` | ซ่อนจาก picker PR/SR; การอ้างอิงประวัติยังเก็บไว้ |
| กำหนดผู้ใช้ให้กับแผนก | หน้า user-admin → Department tab | เขียนไปยัง `tb_department_user` |
| ตั้ง HOD | หน้าเดียวกัน → toggle `is_hod` | มากที่สุดหนึ่ง HOD ต่อแผนก (app invariant) |
| เปลี่ยน HOD | Toggle off อันเก่า, on อันใหม่ | การอนุมัติในอดีตยังเก็บผู้เซ็นจริง |

## 3. การตรวจสอบและข้อผิดพลาด

| อาการ / ข้อความ | สาเหตุ | การจัดการ |
|---|---|---|
| "Code already in use" | `code` ซ้ำบนแถว non-deleted | เลือก code อื่น |
| "Department-name typo conflict" | `(code, name)` ชนกับแถวที่มีอยู่ | แก้ชื่อหรือ reactivate แถวที่มี |
| "Code / name required" | Form ส่งว่าง | เพิ่มทั้งคู่ |
| "Cannot delete — referenced by open PR/SR" | มี FK references | Soft-delete หลังปิด document ที่เปิดอยู่และเคลียร์ user mapping เท่านั้น |
| Workflow resolve HOD ไม่ได้ | ไม่มี `is_hod = true` ในแผนก | ตั้งผู้ใช้หนึ่งคนเป็น HOD |

## 4. Edge Cases

- **Single-HOD invariant** บังคับใช้ระดับ app ไม่ใช่ DB การ maintenance check ควรล้มเหลวอย่างชัดเจนถ้ามีแถว `is_hod = true` หลายแถว
- **การเปลี่ยน HOD** ไม่ retro-fit การอนุมัติย้อนหลัง — ขั้นตอนที่ผ่านมายังเก็บผู้ใช้ที่เซ็นจริง
- **Soft-delete** ต้องไม่มี user mapping ที่ active; มิฉะนั้น HOD resolution จะแตกสำหรับผู้ใช้เหล่านั้น
- **Triple unique** — `code`, `name` และ `(code, name)` มี uniqueness guard ทั้งหมดเพื่อป้องกันการ typo ซ้ำ

---

## 5. โมเดลข้อมูล (Dev)

แหล่งที่มา: tenant schema (`packages/prisma-shared-schema-tenant/prisma/schema.prisma`)

### 5.1 `tb_department`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | รหัสแผนกแบบสั้น (เช่น `KIT`, `FB`) |
| `name` | `String @db.VarChar` | No | ชื่อแผนก |
| `description` | `String? @db.VarChar` | Yes | Free text |
| `is_active` | `Boolean?` | Yes | Active flag, default `true` |
| `note`, `info`, `dimension` | — | Yes | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, deleted_at])` map `department_name_u`; `@@unique([code, deleted_at])` map `department_code_u`; `@@unique([code, name, deleted_at])` map `department_code_name_u` Index บน `name` และ `code`

### 5.2 `tb_department_user`

| Field | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String @db.Uuid` | No | FK ไปยัง platform `tb_user` |
| `department_id` | `String @db.Uuid` | No | FK ไปยัง `tb_department` |
| `is_hod` | `Boolean?` | Yes | True สำหรับ Head of Department (default `false`) |
| `note`, `info`, `dimension`, `doc_version` | — | Mixed | Metadata มาตรฐาน |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([department_id, user_id, deleted_at])` map `department_user_u` Index บน `(department_id, user_id)`, `user_id`, `department_id` FK ไปยัง `tb_department` `onDelete: NoAction`

## 6. กติกาทางธุรกิจ

- **Uniqueness** `code` unique ในแถว non-deleted; index `(code, name)` ป้องกัน typo duplicate
- **Deletion guards** การอ้างอิงจาก PR/SR ที่เปิดอยู่บล็อก hard-delete; soft-delete หลังจากปิดและเคลียร์ user mapping เท่านั้น
- **Validation** `code` และ `name` บังคับ มากที่สุดหนึ่ง `is_hod = true` ต่อแผนก (app invariant)
- **Lifecycle** `is_active = false` ซ่อนจาก picker ใหม่; รักษาการอ้างอิงประวัติ
- **การเปลี่ยน HOD** ไม่ retro-fit การอนุมัติประวัติ

## 7. การอ้างอิงข้ามโมดูล

- [purchase-request](/th/inventory/purchase-request) — PR header อ้างอิงแผนกที่ขอ; routing ใช้ HOD จาก `tb_department_user`
- [store-requisition](/th/inventory/store-requisition) — `from`/`to` location จับคู่กับแผนกบนทุก requisition
- [access-control](/th/inventory/access-control) — การเป็นสมาชิกแผนกขับเคลื่อน RBAC scope default
- [reporting-audit](/th/inventory/reporting-audit) — รายงานหลายตัวจัดกลุ่มตามแผนก

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_department` (lines ~682-708), `tb_department_user` (lines ~4401-4425)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/department/`
