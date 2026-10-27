---
title: การนับสต๊อกประจำงวด (Physical Count) — User Flow — Audit & Config (Correction)
description: บันทึก correction — ไม่มี surface ของ Approver/Finance, Auditor หรือ Sysadmin สำหรับการนับสต๊อกประจำงวด
published: true
date: '2026-10-27T15:00:00.000Z'
tags: physical-count, user-flow, audit, config, inventory, carmen-software, correction
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — User Flow — Audit & Config (Correction)

> **At a Glance**
> **Status:** กลุ่ม persona ที่ยืนยันแล้วว่าไม่มีอยู่จริง &nbsp;·&nbsp; **โมดูล:** [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; **สิ่งที่แทนที่หน้านี้:** [03-user-flow-count-lead](/th/inventory/physical-count/03-user-flow-count-lead) และ [03-user-flow-counter](/th/inventory/physical-count/03-user-flow-counter) บันทึก role เดียวที่ permission-gated จริงของโมดูลนี้

## 1. สิ่งที่หน้านี้เคยอ้าง

Draft ก่อนหน้าของโมดูลวิกินี้อธิบายกลุ่ม persona ที่สามสำหรับการนับสต๊อกประจำงวด — Approver/Finance Reviewer ที่ review และอนุมัติ variance-rollup adjustment, Auditor ที่สังเกตการนับขณะ in-progress และตรวจ audit chain เต็ม, และ Sysadmin ที่ตั้งค่า tolerance threshold, default costing method และการ map reason-code

## 2. สิ่งที่ Source แสดงจริง

การค้นแบบตรงเป้าหมายในทั้ง frontend (`../carmen-frontend/`), backend (`../carmen-turborepo-backend/apps/micro-business/src/inventory/physical-count*`), และ Bruno API collection (`../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/physical-count*`) ไม่พบ route, permission key, workflow stage หรือหน้าจอ configuration ใดที่ตรงกับสาม sub-role ที่อ้างไว้เลย

| Claim | Status | Source แสดงอย่างไร |
|---|---|---|
| Approver/Finance Reviewer อนุมัติ rollup adjustment | ไม่พบ | เอกสาร rollup `tb_stock_in`/`tb_stock_out` ถูก insert **ที่ `doc_status = completed` ทันที** และ post เข้า ledger โดย `submit()` — ไม่มี draft หรือ in-progress stage ที่จะ route ไปให้ผู้อนุมัติได้ตั้งแต่แรก (ดู [02-business-rules.md](/th/inventory/physical-count/02-business-rules) `PHC_POST_001`) |
| Auditor มีสิทธิ์ตรวจสอบ read-only เต็ม chain | ไม่พบ | มี permission key เดียวสำหรับโมดูลนี้ คือ `inventory_management.physical_count` (CRUD) — ไม่มี variant read-only หรือ role auditor แยก |
| Sysadmin ตั้งค่า tolerance threshold | ไม่พบ | ไม่มีกลไก tolerance ใด ๆ ทั้ง frontend หรือ backend สำหรับโมดูลนี้ |
| Sysadmin ตั้งค่า default costing method | จริงบางส่วน อยู่นอกโมดูลนี้ | key `physical_count_costing_method` เดิมไม่ถูกอ่านอีกต่อไป บรรทัดส่วนเกินตอนนี้ถูกตั้งราคาด้วย BU config key `si.cost-from` ("Default price for added items", ค่าเริ่มต้น `last_cost`; `average` เฉพาะบน BU ที่คิดต้นทุนแบบ average) ซึ่งเป็นการตั้งค่าเดียวกับที่ตั้งราคาบรรทัด stock-in ที่กรอกมือ ไม่ได้ตั้งจากหน้าจอ physical-count ใด ๆ |
| Sysadmin map reason code `COUNT_OVERAGE`/`COUNT_SHORTAGE` | ไม่พบ (แทนที่ด้วย EOP type คงที่) | Rollup ตั้ง `adjustment_type_id` เป็น adjustment type `eop_in` / `eop_out` ที่ active ตัวแรกของ BU (จับคู่ด้วย `type`, seed เป็น `EOP-IN` / `EOP-OUT`) ไม่มี reason-code mapping ของส่วนเกิน/ส่วนขาดให้ตั้งค่า; ข้อกำหนดเบื้องต้นเดียวคือสอง type นั้นมีอยู่และ active |

## 3. ควรอ่านอะไรแทน

- [physical-count/03-user-flow-count-lead](/th/inventory/physical-count/03-user-flow-count-lead) — หน้ารายการที่ใช้เริ่มหรือทำต่อการนับ
- [physical-count/03-user-flow-counter](/th/inventory/physical-count/03-user-flow-counter) — หน้า entry และ review ที่ใช้ทำและ submit การนับจริง
- [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) § 4 — กฎ permission จริงเพียงหนึ่งเดียวของโมดูล (`PHC_AUTH_001`–`003`)

## 4. แหล่งอ้างอิง

- **Frontend:** `../carmen-frontend/constant/permissions.ts`; `routes/inventory-management/physical-count/`
- **Backend:** `../carmen-turborepo-backend/apps/micro-business/src/inventory/physical-count/physical-count.service.ts`
- **API contracts:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/inventory/physical-count*/`
- ที่เกี่ยวข้อง: [physical-count/03-user-flow](/th/inventory/physical-count/03-user-flow) (overview), [physical-count/04-test-scenarios-audit-config](/th/inventory/physical-count/04-test-scenarios-audit-config) (หน้า correction คู่ขนานฝั่ง test-scenarios)
