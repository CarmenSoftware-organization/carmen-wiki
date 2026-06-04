---
title: ผู้ใช้ระดับแผนก (Department User)
description: Pivot การเป็นสมาชิกของผู้ใช้กับแผนก — ประกาศว่าผู้ใช้คนใดอยู่ในแผนกใด และระบุ Head of Department (HOD) ที่ขับเคลื่อน approval routing บน PR และ SR
published: true
date: 2026-06-04T00:00:00.000Z
tags: access-control, department-user, configuration, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# ผู้ใช้ระดับแผนก (Department User)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Product Admin &nbsp;·&nbsp; **ตาราง:** `tb_department_user` &nbsp;·&nbsp; **ใช้โดย:** approval routing ของ PR และ SR, RBAC scope, รายงาน cost-centre &nbsp;·&nbsp; Pivot การเป็นสมาชิกระหว่างผู้ใช้กับแผนก — `is_hod = true` ระบุ Head of Department ที่ต้องการการอนุมัติบน requisition ของแผนก

## 1. คืออะไรและใครใช้

`department-user` คือ **pivot การเป็นสมาชิกระหว่างผู้ใช้กับแผนก**: ประกาศว่า [access-control/user](/th/inventory/access-control/user) ที่กำหนดอยู่ใน [master-data/department](/th/inventory/master-data/department) ที่กำหนด ผู้ใช้หนึ่งคนสามารถอยู่ในหลายแผนก โดยแต่ละ row การเป็นสมาชิกเป็นอิสระจากกัน flag boolean `is_hod` ระบุ Head of Department สำหรับการมอบหมายนั้น ๆ — แอปพลิเคชันบังคับว่าแต่ละแผนกมี HOD ได้มากที่สุดหนึ่งคน

flag HOD ขับเคลื่อน logic workflow ปลายน้ำ: เมื่อ [purchase-request](/th/inventory/purchase-request) หรือ [store-requisition](/th/inventory/store-requisition) ถูก submit โดยผู้ใช้ที่แผนกของตนมี HOD pipeline การอนุมัติจะ route ขั้นตอน review ไปยัง HOD นั้น ถ้าไม่มี row ที่นี่ ผู้ใช้จะมองไม่เห็นใน approval routing ของแผนกและรายงาน cost-centre

**บำรุงรักษาโดย** Sysadmin (การมอบหมายผู้ใช้กับแผนก, flag HOD) **อ่านโดย** workflow การอนุมัติของ PR/SR, ตัว resolve scope ของ RBAC และระบบรายงาน

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| มอบหมายผู้ใช้ให้แผนก | หน้าจอ user-admin → แท็บ Department → **Add** | เลือกแผนก; `is_hod` default `false` |
| กำหนดเป็น Head of Department | หน้าจอเดียวกัน → toggle `is_hod` | มากที่สุดหนึ่ง HOD ต่อแผนก (invariant ของแอป) |
| เปลี่ยน HOD | Toggle ปิดตัวเก่า, เปิดตัวใหม่ | การอนุมัติในอดีตยังคงใช้ผู้ลงนามเดิม |
| ลบผู้ใช้ออกจากแผนก | Soft-delete row | ขั้นตอน PR/SR ที่เปิดอยู่ซึ่งอ้างอิงผู้ใช้นี้ไม่ได้รับผลกระทบ; การ routing ในอนาคตจะไม่พบ HOD |
| รายชื่อ HOD ทั้งหมดของแผนก | Query `tb_department_user WHERE is_hod = true AND deleted_at IS NULL` | ใช้สำหรับ audit หรือการยืนยัน config ของ workflow |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Duplicate department assignment" | Unique constraint `(department_id, user_id)` บน row ที่ไม่ถูกลบ | ลบ row ที่มีอยู่ก่อน หรือ soft-delete แล้วเพิ่มใหม่ |
| Workflow ไม่สามารถ resolve HOD ได้ | ไม่มี row `is_hod = true` สำหรับแผนก | ตั้งผู้ใช้หนึ่งคนเป็น HOD ในแท็บ Department ของ user-admin |
| Row HOD หลายตัวสำหรับแผนกเดียวกัน | Invariant ของแอปพลิเคชันถูกละเมิด | รัน maintenance check; ล้าง row `is_hod = true` ส่วนเกิน |
| ขั้นตอนที่อนุมัติแล้วแสดงผู้ใช้ที่ถูกลบออก | ขั้นตอน approval ในอดีตบันทึกผู้ลงนาม ณ เวลาที่ดำเนินการ | ถูกต้อง — การเปลี่ยน HOD ไม่ย้อนหลัง |

## 4. กรณีพิเศษ

- **Invariant HOD หนึ่งคน** บังคับโดยแอปพลิเคชัน ไม่ใช่ DB ผู้ใช้คนหนึ่งสามารถเป็น HOD ของหลายแผนกพร้อมกัน (หนึ่ง row ต่อแผนกที่มี `is_hod = true`) แต่แต่ละแผนกควรมี HOD ไม่เกินหนึ่งคน
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
| `user_id` | `String @db.Uuid` | No | FK ไปยัง platform `tb_user` |
| `department_id` | `String @db.Uuid` | No | FK ไปยัง `tb_department` |
| `is_hod` | `Boolean?` | Yes | Default `false` `true` = Head of Department สำหรับการมอบหมายนี้ |
| `note` | `String? @db.VarChar` | Yes | Annotation แบบ free-text |
| `info` | `Json?` | Yes | Metadata ที่ไม่มีโครงสร้าง |
| `dimension` | `Json?` | Yes | Metadata มิติ |
| `doc_version` | `Decimal` | No | Default `0` Token สำหรับ optimistic concurrency |
| Audit columns | — | Yes | `created_at`, `created_by_id`, `updated_at`, `updated_by_id`, `deleted_at`, `deleted_by_id` |

**Constraints:** `@@unique([department_id, user_id])` map `department_user_u` FK `tb_department_user.department_id → tb_department.id` `onDelete: NoAction, onUpdate: NoAction` Index บน `user_id`, `department_id` และ partial index บน `(department_id, is_hod) WHERE deleted_at IS NULL AND is_hod = true`

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** อย่างมากที่สุดหนึ่ง row `(department_id, user_id)` ที่ active ต่อ combination — unique constraint ป้องกันการมอบหมายซ้ำ
- **Invariant HOD** อย่างมากที่สุดหนึ่ง row `is_hod = true` ต่อแผนก — บังคับโดยแอปพลิเคชัน; การ toggle HOD ใหม่ควรล้าง flag HOD ของ row ก่อนหน้า
- **อำนาจ HOD** `is_hod = true` ให้อำนาจการอนุมัติอัตโนมัติภายในแผนกนั้นสำหรับขั้นตอน workflow ของ PR และ SR ที่ route ไปยัง role type HOD
- **การเป็นสมาชิกหลายแผนก** ผู้ใช้หนึ่งคนสามารถอยู่ในหลายแผนก แต่ละการเป็นสมาชิกเป็นอิสระและสามารถถือ `is_hod` ได้อย่างอิสระ
- **Soft-delete** การลบเป็นแบบ soft (`deleted_at`) เพื่อรักษา audit filter การเป็นสมาชิกที่ active ต้องการ `deleted_at IS NULL`
- **ไม่มี cascade** FK `onDelete: NoAction` — การลบแผนกที่มี row ผู้ใช้ที่ active ถูกบล็อกที่ระดับ DB; ต้องปิดใช้งานหรือมอบหมาย user ใหม่ก่อน

## 7. การอ้างอิงข้าม

- [access-control/user](/th/inventory/access-control/user) — ฝั่ง user ของ membership
- [master-data/department](/th/inventory/master-data/department) — ฝั่งแผนก; บันทึก `tb_department_user` ในส่วน Data Model ด้วย
- [purchase-request](/th/inventory/purchase-request) — approval routing ของ PR resolve HOD จาก `tb_department_user` สำหรับขั้นตอน review ระดับแผนก
- [store-requisition](/th/inventory/store-requisition) — SR routing ใช้ flag HOD เช่นกันสำหรับ requisition ระหว่างแผนก
- [access-control/business-unit-user](/th/inventory/access-control/business-unit-user) — pivot ระดับ BU ที่เทียบเคียง (`tb_user_tb_business_unit`); การเป็นสมาชิก BU กำหนดการเข้าถึง; การเป็นสมาชิกแผนก scope approval routing ภายใน BU

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_department_user` (lines ~2345-2366)
- **Docs:** `../carmen/docs/app/system-administration/user-management/DD-user-management.md` — รายละเอียด entity `tb_department_user` และ definition ของ HOD index
- **Docs:** `../carmen/docs/app/system-administration/user-management/BR-user-management.md` — BR-002: กฎทางธุรกิจ HOD Designation
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/department/`
