---
title: เมนู (Menu)
description: รายการนำทางแอปพลิเคชัน — รายการเมนูต่อโมดูลที่ render ใน app shell พร้อม flag การมองเห็น active และ lock
published: true
date: 2026-05-19T23:55:00.000Z
tags: system-config, menu, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# เมนู (Menu)

> **At a Glance**
> **เจ้าของ:** Sysadmin &nbsp;·&nbsp; **ตาราง:** `tb_menu` &nbsp;·&nbsp; **ใช้โดย:** การนำทาง app shell &nbsp;·&nbsp; หนึ่ง row ต่อหน้าจอที่ addressable — sidebar / top-nav ขับเคลื่อนด้วยข้อมูล

## 1. คืออะไรและใครใช้

ตารางเมนูคือ **registry การนำทาง** — หนึ่ง row ต่อหน้าจอ addressable จัดกลุ่มโดย `module_id` App shell อ่านตารางนี้ตอน boot (หรือ login) และ render sidebar / top-nav เป็น tree แต่ละ row มี `url` ปลายทาง, ชื่อ `name` สำหรับแสดง และ boolean control 3 ตัว: `is_visible` (render), `is_active` (เลือกได้), `is_lock` (system-protected, แก้ได้เฉพาะ Sysadmin)

การรักษาข้อมูลการนำทางขับเคลื่อนด้วยข้อมูลทำให้ property ปิดโมดูลที่ไม่ใช้ ("ซ่อน Recipe ทั้งหมด") หรือ pin landing URL ที่กำหนดเองโดยไม่ต้อง deploy code Row ประกาศจุดเข้าเท่านั้น — เลเยอร์ RBAC และ feature-flag ของแพลตฟอร์มตัดสินใจว่าใครเห็นจริง

**บำรุงรักษาโดย** Sysadmin **อ่านโดย** app shell ตอน boot

## 2. งานทั่วไป

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ซ่อนรายการของโมดูล | ตั้ง `is_visible = false` | ลบจาก sidebar; route ยังถึงได้โดย URL |
| ปิดใช้ route | ตั้ง `is_active = false` | Render แต่คลิกไม่ได้ |
| เพิ่มรายการเมนูที่กำหนดเอง | System Config → Menu → New | เลือก `module_id`, name, url |
| Lock รายการ built-in | `is_lock = true` (ระบบตั้ง) | Non-Sysadmin ไม่สามารถแก้/ลบ |
| จัดเรียงใหม่ | ลากภายในกลุ่ม `module_id` | ปัจจุบันฝั่งแอปผ่าน metadata เพิ่มเติม |

## 3. การตรวจสอบและ Error

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Duplicate name in module" | `(module_id, name)` มีอยู่แล้วในกลุ่มที่ไม่ถูก delete | เลือกชื่ออื่น |
| คลิก → 404 | `url` ชี้ไปที่ route ที่ไม่มีอยู่ | อัปเดต `url` ให้เป็น route ที่ valid |
| การแก้ไขรายการที่ lock ถูกบล็อก | `is_lock = true` และ user ไม่มี `menu.manage_locked` | Grant permission หรือ unlock จาก Sysadmin |
| รายการมองเห็นแต่คลิกไม่มีอะไรเกิดขึ้น | `is_active = false` | Toggle on หรือลบรายการ |

## 4. กรณีพิเศษ

- **การมองเห็นที่มีผล** = `is_active && is_visible && deleted_at IS NULL && user has permission for URL` ค่า false ตัวใดก็ตามซ่อนรายการ
- **ไม่มี FK จาก `module_id`** ไปยังตาราง `tb_module` — แคตตาล็อกโมดูล resolve โดยเลเยอร์แอปพลิเคชัน
- **Lock semantics** การ soft-delete รายการที่ lock จริงๆ คือซ่อน route built-in
- **URL hygiene** เก็บตามตัวอักษร; ไม่มี validation — URL ที่ invalid 404 ตอนคลิก

---

## 5. แบบจำลองข้อมูล (Dev)

แหล่งที่มา: tenant schema

### 5.1 `tb_menu`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| --- | --- | --- | --- |
| `id` | `String @db.Uuid` | No | Primary key |
| `module_id` | `String @db.Uuid` | No | การจัดกลุ่มโมดูลเชิงตรรกะ (แคตตาล็อกฝั่งแอป) |
| `name` | `String @db.VarChar` | No | Label สำหรับแสดง |
| `url` | `String @db.VarChar` | No | Route ปลายทาง |
| `description` | `String?` | Yes | Tooltip / คำอธิบาย |
| `is_visible` | `Boolean?` | Yes | Default `true` |
| `is_active` | `Boolean?` | Yes | Default `true` |
| `is_lock` | `Boolean?` | Yes | Default `true` System-protected |
| Audit columns | — | Yes | `created_*`, `updated_*`, `deleted_*` |

**Constraints:** `@@unique([module_id, name, deleted_at])` Index บน `[name]` ไม่มี FK จาก `module_id` (resolve ฝั่งแอป)

## 6. กฎทางธุรกิจ

- **ความเป็นหนึ่งเดียว** `(module_id, name)` unique ในกลุ่มที่ไม่ถูก delete
- **Lock semantics** `is_lock = true` บล็อก hard-delete และการเปลี่ยน `url` สำหรับ non-Sysadmin
- **Cascade การมองเห็น** ทุกเงื่อนไขต้องผ่าน (active + visible + ไม่ถูก delete + RBAC)
- **URL hygiene** เก็บตามตัวอักษร; ไม่มี validation
- **การจัดกลุ่มโมดูล** `module_id` opaque ต่อ schema; การจัดเรียง / icon อยู่ใน metadata แอป
- **Audit** การแก้ไขรายการที่ lock ควรเขียน row [reporting-audit/activity](/th/inventory/reporting-audit/activity)

## 7. การอ้างอิงข้าม

- ทุกโมดูลธุรกรรม — แต่ละโมดูลโดยทั่วไปมีรายการเมนูหนึ่งหรือมากกว่า
- [access-control/permission](/th/inventory/access-control/permission) — การมองเห็นตัดกับสิทธิ์ต่อผู้ใช้
- [system-config/application-config](/th/inventory/system-config/application-config) — feature flag สามารถซ่อนรายการเพิ่มเติม

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_menu` (lines ~1375-1393)
- **Frontend:** `../carmen-turborepo-frontend/apps/web/app/(app)/configuration/menu/`
