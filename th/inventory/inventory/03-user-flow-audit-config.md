---
title: คลังสินค้า (Inventory) — User Flow — Audit & Config (แก้ไข/correction)
description: หน้าแก้ไข — ไม่มี inventory audit workspace หรือ configuration console อยู่จริง; configuration จริงอยู่ใน master-data, system-config และ access-control
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, user-flow, audit-config, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — User Flow — Audit & Config (แก้ไข/correction)

> **At a Glance**
> **สถานะ:** แก้ไขเมื่อ 2026-07-15 — "inventory audit-log workspace" และ "inventory configuration console" ที่เคยเอกสารไว้ในหน้านี้ (เครื่องมือ lot-recall trace, query กระทบยอด period-snapshot, panel threshold/RBAC/integration, engine impact-preview) **ไม่มีอยู่จริงในผลิตภัณฑ์**
> **สิ่งที่จริง:** Transaction Log แบบอ่านอย่างเดียวที่ `/inventory-management/transaction` บวกหน้าจอ configuration ทั่วไปในโมดูลอื่น

## 1. หน้านี้เคยกล่าวอ้างอะไร และเหตุใดจึงถูกลบ

Draft ก่อนหน้าอธิบาย workspace เฉพาะทางสองตัว: หน้าจอ Auditor (audit-log query, lot-recall trace แบบ forward/backward, การกระทบยอด period-snapshot, การ export sensitive-field แบบมี watermark พร้อม co-approval) และ "inventory configuration console" ของ Sysadmin (panel สำหรับ location, costing method ต่อสินค้า, adjustment types, งวด, approval threshold, RBAC scope, การ cutover integration-endpoint แบบ dual-write พร้อม impact preview และ configuration history) การตรวจสอบเทียบกับ source ปัจจุบันไม่พบ route, component หรือ endpoint ที่ตรงกัน — เป็นรูปแบบการกุขึ้นแบบ config-workbench เดียวกับที่ยืนยันว่าไม่มีอยู่จริงไปแล้วในรอบ purchase-request, purchase-order, good-receive-note และ store-requisition รายละเอียด:

- ไม่มี route ภายใต้ `/inventory-management/` นอกเหนือจาก `transaction`, `period-end(/review)`, `inventory-adjustment`, `physical-count`, `spot-check` (ดู `routes/router.tsx`)
- ไม่มี configuration `threshold` ที่ใดเลยใน backend inventory services; ไม่มี costing method ต่อสินค้าให้ตั้งค่า (method คือ `tb_business_unit.calculation_method` — เป็น setting ระดับ BU ของ platform)
- ไม่มีเครื่องมือ lot-trace หรือ query กระทบยอด snapshot; *ข้อมูล* lot lineage เป็นของจริง (`from_lot_no` / `current_lot_no` / `parent_lot_no`) แต่ UI เดียวที่อยู่เหนือมันคือ transaction list
- ไม่พบกลไก impact-preview, drain-requirement, dual-write หรือ configuration-history ใด ๆ

## 2. Configuration จริงอยู่ที่ใด

| สิ่งที่เคยกล่าวอ้างในหน้านี้ | หน้าจอ / เจ้าของจริง |
|---|---|
| นิยาม location (`location_type`, `physical_count_type`) | [master-data/location](/th/inventory/master-data/location) (`/config/location`) |
| Reason code ของ adjustment (`tb_adjustment_type`) | โมดูล Config (`/config/adjustment-type`) — ดู [inventory-adjustment](/th/inventory/inventory-adjustment) |
| Costing method | `tb_business_unit.calculation_method` — setting ระดับ BU ของ platform (Carmen Platform) ไม่สามารถตั้งค่าใน UI ของผลิตภัณฑ์นี้ |
| นิยามงวด / การ lock | [system-config/period](/th/inventory/system-config/period) (`/system-admin/period`) |
| Scope ของ user/role/permission | [access-control](/th/inventory/access-control) (`/system-admin/user`, `/role`, permission keys) |
| Activity / audit log | [reporting-audit/activity](/th/inventory/reporting-audit/activity) (`/system-admin/activity-log`) และ ledger อ่านอย่างเดียว [transaction](/th/inventory/inventory/transaction) |

## 3. สิ่งที่ auditor ทำได้จริงในวันนี้

- อ่าน ledger แบบ append-only ที่ `/inventory-management/transaction` (`inventory_management.view`): filter ตามช่วงวันที่, direction, location, category, ref-type; trace `parent_document_no` กลับไปยังเอกสารต้นทาง
- ตาม lot lineage ในข้อมูลผ่าน `from_lot_no` / `current_lot_no` บน `tb_inventory_transaction_detail` และ `parent_lot_no` บน cost layers — ด้วยการ query ไม่ใช่เครื่องมือ trace เฉพาะทาง
- Review งวดที่ปิดแล้วบน `/inventory-management/period-end` (history list) และ ledger rows `close` / `open` ที่การปิดเขียน

## 4. แหล่งอ้างอิง

- Frontend routes: `../carmen-inventory-frontend-react/routes/router.tsx` (รายการ route ของ inventory-management ที่ definitive)
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/` (ไม่มี audit/config service ใน scope นี้)
- ภาพรวม parent: [03-user-flow](/th/inventory/inventory/03-user-flow)
