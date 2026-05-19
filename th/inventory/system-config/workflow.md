---
title: เวิร์กโฟลว์ (Workflow)
description: เวิร์กโฟลว์การอนุมัติแบบหลายขั้นที่ตั้งชื่อแล้วผูกกับเอกสารธุรกรรม — นิยาม stage, action, ผู้รับ, SLA และฟิลด์ที่ซ่อนต่อ stage
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, workflow, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# เวิร์กโฟลว์ (Workflow)

> **At a Glance**
> **เจ้าของ:** Sysadmin / Workflow Administrator &nbsp;·&nbsp; **ตาราง:** `tb_workflow` &nbsp;·&nbsp; **ใช้โดย:** PR / SR / PO (โมดูลที่มีการอนุมัติ) &nbsp;·&nbsp; นิยามสาย stage — action, ผู้รับ, SLA, ฟิลด์ที่ซ่อน, ผู้ได้รับมอบหมาย

![เวิร์กโฟลว์ (Workflow) screen](/screenshots/system-config/workflow.png)

## 1. คืออะไรและใครใช้

Record ของเวิร์กโฟลว์คือ *นิยามการ route เอกสาร* ที่ใช้โดยทุกโมดูลที่มีการอนุมัติ คอลัมน์ header น้อย — name, type, active flag — แต่งานหนักอยู่ใน `data` JSONB: รายการ **stages** ตามลำดับ, **action ที่ใช้ได้** ต่อ stage (`submit`, `approve`, `reject`, `sendback`), **ผู้รับ** ที่จะ notify เมื่อแต่ละ action, **ฟิลด์ที่ซ่อน** ที่ stage นั้น และ **ผู้ใช้ที่ได้รับมอบหมาย** ให้ดำเนินการ

เวิร์กโฟลว์เป็นแบบ *typed*: เวิร์กโฟลว์ SR ไม่สามารถแนบกับ PR Typing ผ่าน `enum_workflow_type` และบังคับเมื่อเอกสารเลือกเวิร์กโฟลว์ เวิร์กโฟลว์หลายตัวของ type เดียวกันอยู่ร่วมกันได้ — property โดยทั่วไปดำเนินงาน "Standard PR" และ "High-Value PR" ด้วย chain ที่แตกต่างกัน

**บำรุงรักษาโดย** Sysadmin (หรือ Workflow Admin ที่ได้รับมอบหมาย) **อ่านโดย** engine runtime ของเวิร์กโฟลว์ในทุก stage transition

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| สร้างเวิร์กโฟลว์ใหม่ | System Config → Workflow → New | เลือก `workflow_type`; สร้าง stages |
| แก้ stage | Workflow detail → stage editor | ลากเรียงใหม่; ต่อ stage ตั้ง SLA, action, ผู้รับ, ฟิลด์ที่ซ่อน |
| มอบหมายผู้ใช้ให้ stage | Stage → grid assigned_users | User ID หรือ role descriptor |
| Mark stage เป็น HoD gate | Toggle `is_hod = true` | Route ไปยัง HoD ของแผนกของเอกสาร; ละเว้น `assigned_users` |
| Clone สำหรับ variant ใหม่ | ใช้ action clone ของ UI | เส้นทาง migration มาตรฐานสำหรับการเปลี่ยนแปลงที่ทำลายเข้ากันได้ |
| ปลดระวางเวอร์ชันเก่า | ตั้ง `is_active = false` | เอกสารใหม่เลือกจาก `is_active = true` เท่านั้น |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Workflow name exists" | `(name, workflow_type)` ซ้ำ | เลือกชื่ออื่น |
| Type assignment ไม่ตรงกัน | ประเภทเอกสาร ≠ `workflow_type` | เลือกเวิร์กโฟลว์ของ type ที่ถูก |
| Validation: ขาด submit stage | Stage แรกไม่มี `submit: is_active=true` | เพิ่ม action submit ที่ stage แรก |
| ไม่สามารถ delete เวิร์กโฟลว์ | ถูกอ้างอิงโดยเอกสารที่ไม่ complete | Clone + inactivate เวอร์ชันเก่า |
| ผู้อนุมัติเห็นราคาที่ mask | `hide_fields.price_per_unit = true` ที่ stage ที่ active | คาดหวัง — ปรับ stage หากไม่ได้ตั้งใจ |
| HoD route ล้มเหลว | ไม่มี HoD ตั้งค่าสำหรับแผนกของเอกสาร | ตั้งค่า HoD บน [master-data/department](/th/inventory/master-data/department) |

## 4. กรณีพิเศษ

- **Versioning** การแก้เวิร์กโฟลว์ที่ live ไม่ retroactively เปลี่ยนเอกสารที่กำลังดำเนินอยู่ — runtime อ่านรายการ stage ตามที่เป็นตอน attach การเปลี่ยนแปลงที่ทำลายเข้ากันได้: clone ภายใต้ชื่อใหม่
- **Assigned users vs roles** `assigned_users` ยอมรับทั้ง user ID หรือ role descriptor (resolve ผ่าน [access-control/application-role](/th/inventory/access-control/application-role)) รายการว่างที่ stage approve ที่ไม่ใช่ HOD = ใครก็ตามที่มี role ของ workflow-stage
- **HoD resolution** เมื่อ `is_hod: true` runtime lookup HoD ของแผนกและ route ไปที่นั่น — ละเว้น `assigned_users`
- **ฟิลด์ที่ซ่อน** mask cell UI แต่ค่ายังไหลผ่าน API

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_workflow`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key (`gen_random_uuid()`) |
| `name` | `String @db.VarChar` | No | ชื่อสำหรับแสดง |
| `workflow_type` | `enum_workflow_type` | No | `purchase_request_workflow`, `store_requisition_workflow`, `purchase_order_workflow` |
| `data` | `Json? @db.JsonB` | Yes | นิยาม stage เต็ม Default `{}` |
| `is_active` | `Boolean?` | Yes | Default `true` |
| `description` / `note` | `String? @db.VarChar` | Yes | Free text |
| `info` / `dimension` | `Json? @db.JsonB` | Yes | Metadata |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([name, workflow_type, deleted_at])` Index บน `[name, workflow_type]` และ `[name]` Reverse relations ไปยัง `tb_purchase_request`, `tb_purchase_request_template`, `tb_store_requisition`, `tb_workflow_comment`

### 5.2 Shape `data` JSONB

```
{
  "document_reference_pattern": "",
  "stages": [
    {
      "name": "Request Creation",
      "sla": "24",
      "sla_unit": "hours",
      "available_actions": {
        "submit":   { "is_active": true,  "recipients": { ... } },
        "approve":  { "is_active": false, "recipients": { ... } },
        "reject":   { "is_active": false, "recipients": { ... } },
        "sendback": { "is_active": false, "recipients": { ... } }
      },
      "hide_fields": { "price_per_unit": false, "total_price": false },
      "is_hod": false,
      "assigned_users": []
    }
  ]
}
```

Key ต่อ stage: `name`, `description`; `sla` + `sla_unit` (`hours`/`days`); `available_actions` (`is_active` + `recipients` ต่อ verb); `hide_fields` (mask financials); `is_hod` (HoD gate); `assigned_users` (user ID หรือ role descriptor)

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `(name, workflow_type)` unique ในกลุ่มที่ไม่ถูก delete
- **Type binding** ประเภทเอกสาร X แนบกับเวิร์กโฟลว์ที่ `workflow_type = X` เท่านั้น; runtime reject mismatch
- **At-least-one submit stage** Stage แรกต้องเปิด `submit`; stage ถัดไปต้องเปิดอย่างน้อยหนึ่งใน `approve` / `reject` / `sendback`
- **การ์ดการลบ** เวิร์กโฟลว์ที่ถูกอ้างอิงโดยเอกสารที่ไม่ complete ไม่สามารถ delete; clone + inactivate คือเส้นทาง migration
- **Versioning** การแก้ live ไม่ retroactively เปลี่ยนเอกสารที่กำลังดำเนินอยู่
- **HoD resolution** Lookup HoD ของแผนกของเอกสาร; ละเว้น `assigned_users`
- **ฟิลด์ที่ซ่อน** mask cell UI; ค่าใน API ยังไหลผ่าน

## 7. การอ้างอิงข้าม

- [purchase-request](/th/inventory/purchase-request) — consumer หลัก (`purchase_request_workflow`)
- [store-requisition](/th/inventory/store-requisition) — ผู้ใช้หลายขั้นแบบมาตรฐาน (`store_requisition_workflow`)
- [purchase-order](/th/inventory/purchase-order) — การอนุมัติมูลค่าสูง (`purchase_order_workflow`)
- [good-receive-note](/th/inventory/good-receive-note), [inventory-adjustment](/th/inventory/inventory-adjustment), [vendor-pricelist](/th/inventory/vendor-pricelist), [physical-count](/th/inventory/physical-count), [spot-check](/th/inventory/spot-check) — การ gate ด้วยเวิร์กโฟลว์แบบ optional
- [access-control/application-role](/th/inventory/access-control/application-role) — Role descriptor ใน `assigned_users`
- [master-data/department](/th/inventory/master-data/department) — HoD resolution

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_workflow` (lines ~3398-3425), `enum_workflow_type` (lines ~265-269)
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_workflow.json`
- **carmen/docs:** `../carmen/docs/workflow-permissions-system.md` — semantics ของ role-type
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/workflow/`
