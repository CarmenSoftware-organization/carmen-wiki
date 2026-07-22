---
title: การคำนวณต้นทุน (Costing) — User Flow — Auditor (แก้ไข)
description: หน้าแก้ไข — ไม่มี read-only audit workspace, chain-of-custody trace tool, หรือ FIFO-vs-Average shadow-drift audit screen ในโมดูล costing
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, user-flow, auditor, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:30:00.000Z
---

# การคำนวณต้นทุน (Costing) — User Flow — Auditor (แก้ไข)

> **At a Glance**
> **สถานะ:** แก้ไขแล้ว 2026-07-22 — persona Auditor และ "costing audit workspace" เฉพาะที่เคยเอกสารไว้ที่นี่ (chain-of-custody trace tool, period-end snapshot verification tool, FIFO-vs-Average shadow-drift audit, configuration-history audit) **ไม่มีอยู่จริงในผลิตภัณฑ์**
> **สิ่งที่มีจริง:** ข้อมูลที่อยู่เบื้องหลังอ่านได้ผ่านหน้าจอเดียวกับที่ user คนอื่นอ่าน — Transaction Log, period-end review, และ activity log ของ [reporting-audit](/th/inventory/reporting-audit) — ไม่มีอันไหน gate ด้วย role "Auditor"

## 1. สิ่งที่หน้านี้เคย claim และทำไมถูกลบ

ฉบับร่างก่อนหน้าอธิบาย persona Auditor แบบ read-only เข้มงวด ที่รันสามเครื่องมือเฉพาะ: การ trace chain-of-custody ระดับ lot (forward และ backward ผ่าน `tb_inventory_transaction_cost_layer`), เครื่องมือ verify period-end snapshot (สร้าง `tb_period_snapshot` ใหม่อิสระจาก cost-layer ledger), และ FIFO-vs-Average shadow-drift audit การตรวจสอบกับซอร์สปัจจุบันไม่พบสิ่งใดเลย:

- **ไม่มี Auditor role หรือ permission key อยู่จริง** `enum_stage_role` ไม่มีสมาชิก `auditor`; ไม่มี key เฉพาะ auditor ใน `constant/permissions.ts` สอดคล้องกับข้อค้นพบเดียวกันบน [inventory/03-user-flow-audit-config](/th/inventory/inventory/03-user-flow-audit-config) (แก้ไขแล้ว): "ไม่พบหน้าจอหรือ permission เฉพาะ audit-only ที่แยกจาก `inventory_management.view` ในโมดูลนี้"
- **ไม่มี chain-of-custody trace tool, snapshot-verification tool, หรือ shadow-drift tool อยู่ที่ใดใน frontend เลย** ทั้งหมดนี้เป็นแนวคิด UI ที่ถูกคิดขึ้นเองโดยไม่มี route หรือ component ตรงกัน
- **claim "GL absorbs the difference" / "GL Inventory control-account" ที่ checklist audit ของหน้านี้พึ่งพาไม่มีอยู่จริง** — ดูการแก้ไข [02-business-rules](./02-business-rules.md) § 4/§ 6; ไม่มี GL ให้ audit เทียบ
- **guard `COST_VAL_009` ที่ configuration-history audit ของหน้านี้ตรวจหาไม่มีอยู่ใน code** — ดูการแก้ไข [02-business-rules](./02-business-rules.md) § 2

## 2. พฤติกรรมจริงอยู่ที่ไหน

| เคย claim ที่นี่ | กลไกจริง | หน้า |
|---|---|---|
| Auditor รัน lot chain-of-custody trace | Transaction Log (`/inventory-management/transaction`) คือหน้าจอจริงที่ใกล้เคียงที่สุด — read-only ledger view แบบกรองได้ เปิดให้ใครก็ตามที่มี `inventory_management.view` | [inventory/transaction](/th/inventory/inventory/transaction) |
| Auditor ตรวจสอบ `tb_period_snapshot` เทียบ cost-layer ledger | ไม่มีเครื่องมือ reconciliation ในแอป จะต้องเป็น query ด้วยมือระหว่างสองตารางที่อธิบายใน [costing/01-data-model](/th/inventory/costing/01-data-model) § 2.1/2.3 | [costing/01-data-model](/th/inventory/costing/01-data-model) |
| Auditor audit ประวัติการเปลี่ยน configuration ของ `calculation_method` | ไม่พบ configuration-history feed สำหรับฟิลด์นี้ในรอบนี้ | — |
| Auditor ทบทวน activity เพื่อวัตถุประสงค์ audit | พื้นผิว activity/audit-log จริงอยู่ที่ [reporting-audit](/th/inventory/reporting-audit) gate เหมือนทุกอย่าง ไม่ใช่ด้วย Auditor role | [reporting-audit/activity](/th/inventory/reporting-audit/activity) |

## 3. References

- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/` — ไม่พบ controller เฉพาะ audit สำหรับข้อมูล cost-layer
- Parent overview: [03-user-flow](./03-user-flow.md)
- Cross-link: [inventory/03-user-flow-audit-config](/th/inventory/inventory/03-user-flow-audit-config) — การแก้ไขเดียวกันที่ทำแล้วบนโมดูลพี่น้อง
- Cross-link: [reporting-audit](/th/inventory/reporting-audit) — พื้นผิว activity-log จริง กำหนด permission ทั่วไป
