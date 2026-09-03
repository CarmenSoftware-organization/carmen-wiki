---
title: การสุ่มตรวจ (Spot Check) — User Flow — Audit & Config (Correction)
description: ประกาศแก้ไข — ไม่มี surface ของ Approver/Finance, Auditor หรือ Sysadmin สำหรับการสุ่มตรวจ
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, user-flow, audit, config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — User Flow — Audit & Config (Correction)

> **At a Glance**
> **Status:** กลุ่ม persona ที่ยืนยันแล้วว่าไม่มีอยู่จริง &nbsp;·&nbsp; **โมดูล:** [spot-check](/th/inventory/spot-check) &nbsp;·&nbsp; **สิ่งที่แทนที่:** [03-user-flow-inventory-controller](/th/inventory/spot-check/03-user-flow-inventory-controller) และ [03-user-flow-counter](/th/inventory/spot-check/03-user-flow-counter) บันทึก role เดียวที่มีสิทธิ์จริงของโมดูล

## 1. สิ่งที่หน้านี้เคยกล่าวอ้าง

ดราฟต์ก่อนหน้าของ wiki module นี้บรรยายกลุ่ม persona ที่สามของ spot check — Auditor ที่สังเกตการตรวจขณะดำเนินอยู่และตรวจ audit chain เต็ม (spot-check sheet → recount → การอนุมัติ rollup adjustment → journal entry) และ Sysadmin โดยปริยายที่ config variance-tolerance threshold, default sampling size/method, และ reason-code mapping สำหรับ rollup `SPOT_CHECK_OVERAGE`/`SPOT_CHECK_SHORTAGE`

## 2. สิ่งที่ Source แสดงจริง

การค้นเป้าหมายใน frontend (`../carmen-inventory-frontend-react/routes/inventory-management/spot-check/`), backend (`../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check*`), และ Bruno API collection (`../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/spot-check*`) ไม่พบ route, permission key, workflow stage หรือ configuration screen ที่ตรงกับ sub-role ใดที่กล่าวอ้าง

| ข้อกล่าวอ้าง | Status | Source แสดงอะไร |
|---|---|---|
| มีเอกสาร rollup adjustment ให้ persona Approver/Finance อนุมัติ | ไม่พบ | `submit()` ไม่มีเอกสารปลายทางใดให้อนุมัติเลย — ผลของมันมีแค่ `doc_status = completed` บวก stamp `end_date` (ดู [02-business-rules.md](/th/inventory/spot-check/02-business-rules) `SPC_POST_001`–`002`) ไม่มีอะไรให้ route ไปอนุมัติ |
| Auditor มีสิทธิ์ตรวจสอบ read-only เข้าถึง audit chain เต็ม | ไม่พบ | มีแค่ permission key เดียวสำหรับโมดูลนี้ คือ `inventory_management.spot_check` (CRUD) — ไม่มี variant read-only หรือ role auditor แยกต่างหาก ก็ไม่มี chain ให้ตรวจด้วย: ไม่มีเอกสาร rollup ไม่มี journal entry ไม่มีฟิลด์เชื่อมโยงใดเชื่อม spot check กับสิ่งอื่น |
| Sysadmin config variance-tolerance threshold | ไม่พบ | ไม่มีกลไก tolerance ชนิดใด — เปอร์เซ็นต์ ปริมาณสัมบูรณ์ หรืออื่น — อยู่ใน frontend หรือ backend สำหรับโมดูลนี้ |
| Sysadmin config default sampling `size`/`method` | ไม่พบ | ไม่มีหน้าจอ configuration ตั้งค่า default ระดับ tenant สำหรับทั้งสองฟิลด์ — `method`/`size` (หรือ `product_id[]` สำหรับ manual) ของทุก spot check ถูกเลือกใหม่ทุกครั้งที่หน้าสร้าง |
| Sysadmin map reason code `SPOT_CHECK_OVERAGE`/`SPOT_CHECK_SHORTAGE` | ไม่พบ | ทั้งสอง reason code ไม่มีอยู่ที่ใดใน schema หรือโค้ด — ไม่มี rollup ให้ reason code ผูกด้วยตั้งแต่แรก |

## 3. สิ่งที่ควรอ่านแทน

- [spot-check/03-user-flow-inventory-controller](/th/inventory/spot-check/03-user-flow-inventory-controller) — หน้ารายการและสร้าง
- [spot-check/03-user-flow-counter](/th/inventory/spot-check/03-user-flow-counter) — หน้า entry และ review ที่ spot check ถูกดำเนินการและ submit จริง
- [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) § 4 — กฎ permission จริงหนึ่งเดียวของโมดูล (`SPC_AUTH_001`–`003`)

## 4. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/constant/permissions.ts`; `routes/inventory-management/spot-check/`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts`
- **API contracts:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/spot-check/`
- ที่เกี่ยวข้อง: [spot-check/03-user-flow](/th/inventory/spot-check/03-user-flow) (overview), [spot-check/04-test-scenarios-audit-config](/th/inventory/spot-check/04-test-scenarios-audit-config) (หน้า correction คู่ขนานฝั่ง test-scenarios)
