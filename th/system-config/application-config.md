---
title: การตั้งค่าแอปพลิเคชัน (Application Config)
description: การตั้งค่าแอปพลิเคชันแบบ key-value ทั่วไป — การตั้งค่าระดับ tenant และการ override preference ต่อผู้ใช้ที่จัดเก็บเป็น JSONB
published: true
date: 2026-05-17T12:00:00.000Z
tags: system-config, application-config, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# การตั้งค่าแอปพลิเคชัน (Application Config)

> **At a Glance**
> **เจ้าของ:** Sysadmin (ระดับ tenant) + ผู้ใช้แต่ละคน (preferences) &nbsp;·&nbsp; **ตาราง:** `tb_application_config` (+ `tb_application_user_config`) &nbsp;·&nbsp; **ใช้โดย:** ทุกโมดูลสำหรับ feature flag + preference ต่อผู้ใช้ &nbsp;·&nbsp; ที่เก็บ key-value JSONB ทั่วไป — ทางออกสำหรับการตั้งค่าขนาดเล็ก

## 1. คืออะไรและใครใช้

Application Config คือ **ที่เก็บ key-value ทั่วไป** สำหรับการตั้งค่าที่ไม่คุ้มที่จะมี schema เฉพาะของตัวเอง ตารางสองตารางใช้ shape เดียวกัน: `tb_application_config` เก็บการตั้งค่าระดับ tenant (เช่น `tax_profile` ที่ active, feature flag, toggle เริ่มต้น) และ `tb_application_user_config` เก็บการ override preference ต่อผู้ใช้ (ลำดับคอลัมน์ของตาราง ฟิลเตอร์ที่บันทึก theme location เริ่มต้น) ทั้งคู่เก็บค่าเป็น JSONB ดังนั้น shape ใดก็ตาม — string, number, object, array — ใช้งานได้โดยไม่ต้อง migration

รูปแบบนี้คือ *ทางออก* — การตั้งค่าขนาดเล็กที่ไม่อย่างนั้นจะ pollute schema เป็นตารางคอลัมน์เดียวมาอยู่ที่นี่ภายใต้ key ที่เสถียร trade-off: schema ไม่บังคับ shape — consumer ต้อง validate ตอนอ่าน

**บำรุงรักษาโดย** Sysadmin (การตั้งค่าระดับ tenant) และผู้ใช้ปลายทาง (preferences เขียนแบบโปร่งใส) **อ่านโดย** ทุก list view และทุก path ที่มี feature gate

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ตั้งค่า feature flag ระดับ tenant | System Config → Application Settings | Typed editor หรือ raw JSON สำหรับ key ที่ไม่รู้จัก |
| เปลี่ยน tax profile | System Config → Application Settings → `tax_profile` | Drop-down editor |
| จัดเรียงคอลัมน์ใหม่ (ต่อผู้ใช้) | ลากใน list view ใดก็ได้ | บันทึกอัตโนมัติไปยัง `tb_application_user_config` |
| รีเซ็ต preference ของฉัน | เมนูโปรไฟล์ผู้ใช้ → Reset my preferences | ลบทั้งหมดโดย `user_id` |
| เพิ่ม config key ใหม่ | Insert ผ่าน service code | ข้อตกลง: dotted namespace |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Key collision ตอน insert | มี row ที่ไม่ถูก delete อยู่แล้ว | Update row เดิมหรือเลือก key อื่น |
| Value ถูก reject ตอน runtime | Zod schema mismatch | แก้ shape ตาม contract ของ consumer |
| Preference ไม่ถูกใช้ | ไม่มี user row — fallback ไปที่ tenant | ตรวจสอบว่ามี row `user_id`+`key` อยู่ |
| Secret รั่ว | เก็บ credentials ใน config | ย้ายไป env / secrets manager — config แก้ไขได้โดยมนุษย์ |

## 4. กรณีพิเศษ

- **Schema by convention** ไม่มีการบังคับ shape ระดับ DB บน `value` — code ที่ consume เป็นเจ้าของ shape (โดยทั่วไป Zod-validated ตอนอ่าน)
- **ลำดับการ resolve** ค่าต่อผู้ใช้ชนะค่า tenant เมื่อทั้งคู่มีอยู่สำหรับการตั้งค่าเดียวกัน
- **ห้ามมี secret** API key, credentials ต้อง NOT ถูกเก็บที่นี่
- **Hard-delete ใช้ได้** สำหรับ row ระดับ tenant (fallback ไปที่ default ที่ compile-time)

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_application_config`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `key` | `String @db.VarChar` | No | Key ของการตั้งค่า (เช่น `tax_profile`, `feature.enable_recipe_costing`) |
| `value` | `Json @db.JsonB` | No | Default `{}` Shape นิยามโดยแอปพลิเคชันต่อ key |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([key, deleted_at])` Index บน `[key]`

### 5.2 `tb_application_user_config`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `user_id` | `String @db.Uuid` | No | เจ้าของ (cross-schema ไปยัง `tb_user` ของแพลตฟอร์ม) |
| `key` | `String @db.VarChar` | No | Key ของ preference (เช่น `pr_list.columns`, `theme`) |
| `value` | `Json @db.JsonB` | No | Default `{}` |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([user_id, key, deleted_at])` Index บน `[user_id, key]` ไม่มี FK ไปยัง `tb_user` (cross-schema)

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `key` unique ใน row ที่ไม่ถูก delete ในตาราง tenant; `(user_id, key)` unique ในตาราง user
- **Schema by convention** Consumer validate shape; ไม่มีการบังคับระดับ DB
- **Key namespace** ข้อตกลง dotted-namespace (`feature.*`, `default_*`, `<module>.*`)
- **ลำดับการ resolve** User ชนะ tenant สำหรับการตั้งค่าเดียวกัน
- **ค่าที่ sensitive** ห้าม — ใช้ env / secrets manager
- **การ delete** Hard-delete ยอมรับได้; แอป fallback ไปที่ default ตอน compile

## 7. การอ้างอิงข้าม

- ทุกโมดูล — feature gate และ preference ต่อผู้ใช้
- [[purchase-request]], [[purchase-order]], [[good-receive-note]], [[store-requisition]], [[inventory-adjustment]], [[physical-count]], [[spot-check]] — preference ของ list view
- [[access-control/user]] — การ resolve `user_id`
- [[reporting-audit/widget]] — ทางเลือกการเก็บข้อมูลสำหรับ dashboard config

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_application_config` (lines ~4910-4924), `tb_application_user_config` (lines ~4926-4941)
- **Seed:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/seed-data-a01/tb_application_config.json`
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/application-config/`
