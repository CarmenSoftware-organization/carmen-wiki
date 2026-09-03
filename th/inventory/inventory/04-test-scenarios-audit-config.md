---
title: คลังสินค้า (Inventory) — Test Scenarios — Audit & Config
description: หน้าแก้ไข — test suite ของ Audit/Config ที่เคยบันทึกไว้บนหน้านี้อ้างถึง audit workspace และ configuration console ที่ไม่มีอยู่จริง
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, test-scenarios, audit-config, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — Test Scenarios — Audit & Config

> **At a Glance**
> **สถานะ:** แก้ไขแล้ว 2026-07-15 — scenario ~32 รายการที่เคยอยู่บนหน้านี้ (query บน audit-log workspace, เครื่องมือ lot-recall trace, query กระทบยอด period-snapshot, การ export ฟิลด์อ่อนไหวพร้อม watermark, ตัว block การ drain ตาม location-type, การเปลี่ยน costing method รายสินค้า, การแก้ไข threshold tier, RBAC deadlock preview, integration dual-write cutover) อ้างถึง surfaces ที่**ไม่มี source รองรับ** และถูกตัดออกแทนที่จะสร้างขึ้นใหม่

## 1. เหตุผลที่ scenarios เหล่านี้ถูกตัดออก

- **ไม่มี route ของ audit workspace หรือ configuration console** ใต้ `/inventory-management/` (`routes/router.tsx` list เพียง `transaction`, `period-end(/review)`, `inventory-adjustment`, `physical-count`, `spot-check`)
- **ไม่มีกลไก threshold, impact-preview, configuration-history, หรือ dual-write** ใน backend inventory services
- **Costing method ไม่ใช่รายสินค้า** — มันคือ `tb_business_unit.calculation_method` (setting ระดับ BU ฝั่ง platform); ไม่มีอะไรให้ config ใน UI ของผลิตภัณฑ์นี้ และไม่มี drain-guard อยู่จริง
- **ไม่มีเครื่องมือ lot-trace หรือ snapshot-reconciliation เฉพาะทาง**; ข้อมูล lot lineage (`from_lot_no` / `current_lot_no` / `parent_lot_no`) มีจริง แต่ query ได้ผ่าน transaction list หรือ database เท่านั้น

สิ่งนี้สอดคล้องกับ pattern config-workbench ที่ยืนยันแล้วว่าไม่มีอยู่จริง จากรอบตรวจของ purchase-request, purchase-order, good-receive-note และ store-requisition

## 2. Configuration ที่มีจริงและ test ได้อยู่ที่ไหน

| เคย test ที่นี่ | ที่ test จริง |
|---|---|
| สร้าง location / `location_type` / `physical_count_type` | [master-data/location](/th/inventory/master-data/location) — E2E `080-location.spec.ts` |
| Reason codes ของ adjustment-type | โมดูล Config — E2E `031-adjustment-type.spec.ts` |
| นิยามงวด / lock | [system-config/period](/th/inventory/system-config/period) |
| User / role / permission scope | [access-control](/th/inventory/access-control) |
| Activity log | [reporting-audit/activity](/th/inventory/reporting-audit/activity) |
| การตรวจ ledger แบบ read-only | [04-test-scenarios-store-keeper](/th/inventory/inventory/04-test-scenarios-store-keeper) (scenarios ของ Transaction Log) |

## 3. แหล่งอ้างอิง

- Frontend routes: `../carmen-inventory-frontend-react/routes/router.tsx`
- ภาพรวม parent: [04-test-scenarios](/th/inventory/inventory/04-test-scenarios); คู่ user-flow: [03-user-flow-audit-config](/th/inventory/inventory/03-user-flow-audit-config)
