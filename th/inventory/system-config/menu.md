---
title: เมนู (Menu)
description: ตาราง tb_menu มีอยู่ใน tenant schema แต่ไม่มีการอ้างอิงจากโค้ด non-schema เลยไม่ว่าใน backend หรือ frontend — sidebar จริงของ app shell คือ static navigation tree ที่เขียนด้วยโค้ด ไม่ได้ขับเคลื่อนด้วยข้อมูลจากตารางนี้
published: true
date: '2026-09-23T01:30:00.000Z'
tags: system-config, menu, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T08:00:00.000Z
---

# เมนู (Menu)

> **At a Glance**
> **เจ้าของ:** ไม่มีใคร — **ไม่มีโค้ดใดอ่านหรือเขียนตารางนี้เลย** &nbsp;·&nbsp; **ตาราง:** `tb_menu` (schema เท่านั้น) &nbsp;·&nbsp; **การนำทางจริง:** static tree ที่เขียนด้วยโค้ด (เช่น `CHAPTERS` ใน `landing-types.ts` สำหรับ System Admin hub และโครงสร้างเดียวกันสำหรับ sidebar หลักของแอป) &nbsp;·&nbsp; ตาราง dead — เก็บไว้ใน schema แต่ไม่ต่อสายกับอะไรเลย

## สถานะการ implement (ตรวจสอบ 2026-07-16; ตรวจสอบซ้ำ 2026-09-22 — ไม่เปลี่ยน)

การค้นทั่ว repo หา `tb_menu` ใน `carmen-turborepo-backend-v2/apps` และ `carmen-turborepo-backend-v2/packages` พบ **เฉพาะการประกาศใน Prisma schema และ migration SQL ของมัน** — ไม่มีแม้แต่จุดเดียวในไฟล์ `.service.ts`, `.controller.ts` หรือ DTO ใดเลย (รันซ้ำ 2026-09-22 ยังเป็นศูนย์) ไม่มี `menu.service.ts`, ไม่มี `menu.controller.ts`, ไม่มี Bruno folder `config/menu/*` และไม่มี route `menu` ที่ไหนใต้ `../carmen-inventory-frontend-react/routes/`

การนำทางจริงของ app shell ถูก **hard-code ไว้ใน frontend** ไม่ได้ขับเคลื่อนด้วยข้อมูล: หน้า System Admin landing render จาก array `CHAPTERS` ที่กำหนดตอน compile (`routes/system-admin/landing-types.ts:43-140`) ที่มีห้า chapter — `access` (roles, assign), `process` (`inventoryPeriod` → `/system-admin/inventory-period`, workflows, docs), `observe` (userActivity, monitor), `config` (interface, notifyTemplate, code), `data` (dataset) — และ sidebar หลักคือ tree แบบ static ใน `constant/module-list.ts` สิ่งที่*แปรผัน*ต่อ property ที่ runtime จริง ๆ คือ **การมองเห็นตาม licence และ permission** ไม่ใช่ตามตารางนี้: แต่ละ entry ใน `module-list.ts` มี key `licenseFeature` และ `permission` และ `hooks/use-license.ts` (`isLicensed`, `isHidden`, `canWrite`) ซ่อนฟีเจอร์ที่เลิกใช้และล็อกฟีเจอร์ที่ไม่มี licence (FE `2addc658`, 2026-08-31) การเพิ่มหรือเปลี่ยนชื่อ entry ยังต้องอาศัย **การแก้โค้ด frontend และ redeploy** — ไม่มีหน้าจอ admin และไม่มี row ที่ runtime ควบคุมมันได้

เนื้อหาหลังจากบรรทัดนี้ทั้งหมดอธิบาย **เจตนาการออกแบบ** ที่บอกใบ้จากรูปร่างฟิลด์ของ schema (`is_visible` / `is_active` / `is_lock` / `module_id`) เก็บไว้เพราะตารางอาจถูกสร้างต่อในอนาคต — ไม่ใช่พฤติกรรมที่ยืนยันแล้วหรือ ship แล้ว

## 1. คืออะไรและใครใช้

`tb_menu` เห็นได้ชัดว่าถูกออกแบบให้เป็น **registry การนำทาง** — หนึ่ง row ต่อหน้าจอ addressable จัดกลุ่มโดย `module_id` พร้อม `url` ปลายทาง, ชื่อ `name` สำหรับแสดง และ boolean control 3 ตัว (`is_visible`, `is_active`, `is_lock`) ไม่พบโค้ดใดอ่านตารางนี้ตอน boot ตอน login หรือที่ไหนเลย — app shell ไม่ปรึกษามันเลย

**บำรุงรักษาโดย** ไม่มีใคร — ไม่มีหน้าจอ admin **อ่านโดย** ไม่พบเลย

## 2. งานทั่วไป

ไม่มีงานด้านล่างที่ทำได้จริงวันนี้ — เก็บไว้เป็นเจตนาการออกแบบเท่านั้น

| งาน (เจตนาการออกแบบ ยังไม่สร้าง) | ที่ไหน (ไม่มีอยู่จริง) | หมายเหตุ |
|---|---|---|
| ซ่อนรายการของโมดูล | ~~ตั้ง `is_visible = false`~~ | ไม่มีหน้าจอเขียนตารางนี้; การนำทางคือค่าคงที่ในโค้ด frontend |
| ปิดใช้ route | ~~ตั้ง `is_active = false`~~ | ยังไม่ implement |
| เพิ่มรายการเมนูที่กำหนดเอง | ~~System Config → Menu → New~~ | ไม่มีหน้าจอนี้ |
| Lock รายการ built-in | ~~`is_lock = true`~~ | ยังไม่ implement |
| จัดเรียงใหม่ | ~~ลากภายในกลุ่ม `module_id`~~ | ยังไม่ implement — ลำดับตายตัวใน array `CHAPTERS`/sidebar ของ frontend |

## 3. การตรวจสอบและ Error

ยังไม่ยืนยัน — ไม่มี service layer บังคับสิ่งเหล่านี้เลย

| อาการ (สมมติฐาน) | สาเหตุ | การดำเนินการ |
|---|---|---|
| "Duplicate name in module" | `(module_id, name)` มีอยู่แล้วในกลุ่มที่ไม่ถูก delete | ยังไม่ implement — ไม่มี create endpoint |
| คลิก → 404 | `url` ชี้ไปที่ route ที่ไม่มีอยู่ | ไม่เกี่ยวข้อง — การนำทางคือค่าคงที่ในโค้ดที่ทดสอบแล้ว ไม่ใช่ข้อมูลที่ผู้ใช้แก้ได้ |
| การแก้ไขรายการที่ lock ถูกบล็อก | `is_lock = true` | ยังไม่ implement |
| รายการมองเห็นแต่คลิกไม่มีอะไรเกิดขึ้น | `is_active = false` | ยังไม่ implement |

## 4. กรณีพิเศษ

- **ไม่มีสูตรการมองเห็นที่มีผลอยู่ในโค้ดเลย** ชุดค่าผสม `is_active && is_visible && deleted_at IS NULL` ที่อธิบายไว้ ณ ที่นี้ อนุมานจากชื่อคอลัมน์ ไม่ใช่จาก guard ที่สังเกตได้จริง
- **ไม่มี FK จาก `module_id`** ไปยังตาราง `tb_module` ใน schema — สอดคล้องกับการออกแบบที่ไม่เคยเสร็จ ไม่ใช่หลักฐานยืนยันการ implement ไปทางใดทางหนึ่ง
- **การจะซ่อนโมดูลจริงๆ วันนี้** Sysadmin ไม่มี lever ในผลิตภัณฑ์นี้ — lever ที่มีอยู่คือสถานะ licence feature ฝั่ง Platform (`tb_license_feature.state = 'hide'` เอาออกจากเมนูของทุก BU; ฟีเจอร์ที่ยังไม่ได้ขายแสดงเป็นล็อก) และ role permission ของ tenant; นอกเหนือจากนั้นต้องผ่านโค้ดเบส frontend (`CHAPTERS` ใน `landing-types.ts`, `constant/module-list.ts`) และ deploy

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

กฎด้านล่างไม่มีกฎใดถูกบังคับด้วยโค้ดเลย — unique index คือสิ่งเดียวที่ฐานข้อมูลบังคับจริง ส่วนที่เหลืออนุมานจากชื่อคอลัมน์

- **ความเป็นหนึ่งเดียว (ระดับ schema เท่านั้น)** `(module_id, name)` unique ในกลุ่มที่ไม่ถูก delete — เป็น DB constraint ไม่มี service ใดรองรับ
- **Lock semantics, cascade การมองเห็น, URL hygiene, การจัดกลุ่มโมดูล, audit ตอนแก้ไข** — ทั้งหมดเป็นเจตนาการออกแบบ **ไม่มีโค้ดใด implement สิ่งเหล่านี้เลย**

## 7. การอ้างอิงข้าม

ไม่พบโมดูลใดอ่าน `tb_menu` เลย ลิงก์ข้ามถูกลบออก — ไม่มีอะไรให้อ้างอิงข้ามจนกว่าตารางนี้จะถูกต่อสายกับอะไรสักอย่าง ดู [system-config/application-config](/th/inventory/system-config/application-config) สำหรับแนวคิด feature-flag (ที่ก็ยังไม่ implement เป็นส่วนใหญ่เช่นกัน)

## 8. แหล่งข้อมูลอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_menu` (lines ~1412-1430)
- **Frontend (การนำทางจริงแบบ static สำหรับเทียบ):** `../carmen-inventory-frontend-react/routes/system-admin/landing-types.ts` (`CHAPTERS` — รายการโมดูลของ System Admin hub), `constant/module-list.ts` (tree ของ sidebar พร้อม `licenseFeature` / `permission` ต่อ entry), `hooks/use-license.ts` (ซ่อน/ล็อกที่ runtime) และ `routes/router.tsx` (route tree แบบ static ทั้งหมด) ไม่มีตัวไหนอ่าน `tb_menu`
