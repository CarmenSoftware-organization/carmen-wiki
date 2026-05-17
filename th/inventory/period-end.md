---
title: ปิดงวด (Period End)
description: orchestrator ปิดงวด — gate snapshot costing, GL handoff และ lock การ backdate เมื่อความต้องการของ Physical Count และ Spot Check ครบ
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory, period-end, costing, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# ปิดงวด (Period End)

> **At a Glance**
> **เจ้าของ:** Finance (trigger) &nbsp;·&nbsp; Inventory Manager (prerequisite checklist) &nbsp;·&nbsp; **กระบวนการ:** orchestrator เหนือ `tb_period` / `tb_period_snapshot` &nbsp;·&nbsp; **Trigger:** การปิดรายเดือนบนงวดที่เปิด &nbsp;·&nbsp; **เขียนถึง:** snapshot costing + GL handoff + lock การ backdate &nbsp;·&nbsp; **1-liner:** freeze งวดและผลิต snapshot ต่อ lot

## 1. ภาพรวมและผู้ใช้งาน

Period End คือ **พิธีการ run-the-close** — ปุ่มเดียวที่บอกว่า "งวดบัญชีนี้เสร็จแล้ว" และผลิตสาม durable outputs: snapshot costing ที่ frozen ต่อ `(location, product, lot)`, ชุด handoff ของ GL และสถานะงวดที่ flip ที่ reject การ post ย้อนหลังเพิ่มเติม พิธีการเองไม่ transact สต๊อก; freeze มัน

- **Finance** — role เดียวที่อาจ flip `tb_period.status`
- **Inventory Manager** — clear prerequisite checklist
- **Cost Engine** — actor ที่สามที่เงียบที่คำนวณ snapshot ต่อ lot

## 2. งานที่พบบ่อย

> **Prerequisite checklist — ต้องเขียว 100% ก่อน Finance สามารถ flip งวด:**
> - [ ] ทุก **GRN** สำหรับงวดคือ `completed` (ไม่มี `draft` / `in_progress`)
> - [ ] ทุก **SR** คือ `completed` หรือ `cancelled`
> - [ ] ทุก **inventory-adjustment / wastage / stock-in / stock-out** คือ `posted` หรือ `voided`
> - [ ] ทุก **Spot Check** สำหรับงวดคือ `completed`
> - [ ] ทุก **Physical Count** คือ `finalised` ด้วย variances posted เป็น adjustments
> - [ ] ทุก **Credit Note** คือ `posted` (ขับ `COST_CALC_005` FX revaluation)

| งาน | ที่ใด | หมายเหตุ |
|---|---|---|
| Run prerequisite checklist (read-only) | Inventory Management → Period End → Prerequisites | Return IDs เอกสารที่ขาด; Inventory Manager clear มัน |
| Trigger close บนงวดที่เปิด | Period End → **Close** (Finance เท่านั้น) | Cost Engine คำนวณ snapshot, status flip `open → closed` |
| Verify ว่า snapshot เขียน | Period End → tab Snapshot | หนึ่ง row `tb_period_snapshot` ต่อ `(location, product, lot)` ด้วยกิจกรรมไม่เป็นศูนย์ |
| Confirm ว่า ledger event posted | เปิด [[inventory/transaction]] → filter `inventory_doc_type = 'close'` | Close เองปรากฏบน ledger |
| Lock หลัง audit sign-off | Period End → **Lock** (Finance) | Flip `closed → locked` — terminal |
| Reopen งวด (หายาก) | Period End → **Reopen** (Finance, audited) | Log บน `tb_period_comment`; เฉพาะขณะที่ `closed` ไม่เคย `locked` |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ / ข้อความ | สาเหตุ | การกระทำ |
|---|---|---|
| "Close blocked: documents in non-terminal state" | GRN / SR / adjustment / count ใดยัง `draft` หรือ `in_progress` | เปิด IDs ที่ระบุและ complete / cancel มัน |
| "Spot Check pending" | spot checks หนึ่งหรือมากกว่าสำหรับงวดไม่ `completed` | Finalise ใน [[spot-check]] |
| "Physical Count pending" | Count ไม่ `finalised` หรือ variances ไม่ post เป็น adjustments | Finalise ใน [[physical-count]] |
| "Period is closed / locked" บน submit ของ doc ใด | `document_date` falls ในงวด `closed` / `locked` | ใช้วันที่งวด-ปัจจุบัน หรือ raise manual JV |
| "Snapshot row already exists" | Re-run close ขณะที่ `status = open` | ปลอดภัย — snapshot คือ keyed `(period_id, snapshot_at)` และ replace |
| ไม่สามารถ lock | Period ยังไม่ `closed` | Close ก่อน แล้ว lock หลัง audit |

## 4. กรณีพิเศษ

- **Idempotency** Close คือ re-runnable ขณะที่ `status = open`; snapshot replace ไม่เคย duplicate (unique บน `(period_id, snapshot_at, deleted_at)`)
- **Backdating lock** ด้วย `status IN ('closed', 'locked')`, เอกสารใด ๆ ที่มีวันที่ภายใน `[start_at, end_at]` คือ reject ที่ submit time — ไม่มี escape hatch ยกเว้น JV
- **`locked` คือ terminal** Re-open จาก `locked` ไม่ใช่ path ปกติ; ต้องการ Finance unlock authority อย่างชัดเจน
- **Cost-layer attribution** ทุก row `tb_inventory_transaction_cost_layer` carry `period_id` และ `at_period` (YYMM) stamped ที่ posting; snapshot trust stamp นี้และ **ไม่** re-derive จากวันที่ document
- **Period uniqueness** เฉพาะหนึ่ง period ที่ไม่ deleted ต่อ YYMM (`@@unique([fiscal_year, fiscal_month, deleted_at])`)

---

## 5. กระบวนการ (Dev)

Period End **ไม่ใช่ Prisma table เดียว** — เป็นกระบวนการเหนือหลายตาราง:

| ตาราง | บทบาท |
|---|---|
| `tb_period` | Status row ที่ flip `open → closed → locked` Carry `period` (YYMM), `fiscal_year`, `fiscal_month`, `start_at`, `end_at` |
| `tb_period_snapshot` | หนึ่ง row ต่อ `(period_id, location, product, lot)` ด้วย opening / receipt / issue / adjustment / closing qty และ total cost Audit anchor |
| `tb_period_comment` | Log แบบ free-text ของบันทึก close-out, attachments, คำอธิบาย variance, การเซ็นรับรองของ reviewer |
| `tb_inventory_transaction_cost_layer` | แต่ละ layer carry `period_id` และ `at_period`; snapshot derived จาก `GROUP BY` เหนือเหล่านี้ |
| `tb_inventory_transaction` | Event `close` (และ `open` ภายหลัง) เขียนผ่าน `enum_inventory_doc_type` เพื่อให้ close เองปรากฏบน ledger |

`tb_period.status` คือ `enum_period_status { open, closed, locked }` — `open` อนุญาตการ post, `closed` block posts ใหม่แต่อนุญาตการ reversals บางอย่าง, `locked` คือ terminal

## 6. Lifecycle

```
1. Inventory Manager clear prerequisite checklist (Section 2)
2. Finance trigger close บน row tb_period ที่เปิด:
   - Cost Engine คำนวณ closing balance ต่อ lot จาก tb_inventory_transaction_cost_layer
   - INSERT rows tb_period_snapshot ต่อ (location, product, lot) ด้วยกิจกรรมไม่เป็นศูนย์
   - INSERT rows tb_inventory_transaction ด้วย inventory_doc_type = 'close'
   - tb_period.status flip open -> closed
3. GL handoff (read-only): Finance export snapshot + journal entries
4. Optional ภายหลัง: Finance flip closed -> locked หลัง audit sign-off
```

Status flips ถูก log บน `tb_period_comment` ด้วย `created_by_id` และ timestamp

## 7. ความเชื่อมโยงข้ามโมดูล

- [[system-config/period]] &nbsp;·&nbsp; [[costing]] &nbsp;·&nbsp; [[physical-count]] &nbsp;·&nbsp; [[spot-check]]
- [[good-receive-note]] &nbsp;·&nbsp; [[inventory-adjustment]] &nbsp;·&nbsp; [[store-requisition]]
- [[inventory/transaction]] — close เขียน `close` ledger row
- [[reporting-audit]] — รายงาน close-out อ่าน `tb_period_snapshot`

## 8. แหล่งอ้างอิง

- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_period` (~1172-1203), `tb_period_snapshot` (~1239-1292), `tb_period_comment` (~1205-1237), `enum_period_status` (~1166-1170), `enum_inventory_doc_type` (~208-216), `tb_inventory_transaction_cost_layer` (~1123-1164)
- **Frontend:** `../carmen-inventory-frontend/app/(root)/inventory-management/period-end/`
- **carmen/docs:** `../carmen/docs/inventory-management/period-end-process.md`
- **Test cases:** `Test_case/System_Process/tx-09-end-period-close.md`; `Test_case/System_Process/INDEX.md` § Process Execution Swim Lane
