---
title: การปรับสต๊อก (Inventory Adjustment)
description: การแก้ไขยอดสต๊อกด้วยมือ — write-off, write-on, การจัดประเภทใหม่
published: true
date: 2026-05-19T23:55:00.000Z
tags: inventory-adjustment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# การปรับสต๊อก (Inventory Adjustment)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** การแก้ไขสต๊อกแบบควบคุม (IN / OUT) นอกเหนือจากการจัดซื้อและการบริโภค — write-off, write-on, ผลต่างการนับ, การจัดประเภทใหม่ (`Draft` → `Posted` → `Void`) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Store Keeper, Inventory Controller, Finance, Auditor &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_inventory_adjustment`, `tb_inventory_adjustment_detail`, `InventoryStatus`, `JournalEntry`, master ของ reason-code &nbsp;·&nbsp; **หน้าย่อย:** 13

![การปรับสต๊อก (Inventory Adjustment) screen](/screenshots/inventory-adjustment/index.png)

## 1. ภาพรวม

**Inventory Adjustment (การปรับสต๊อก)** คือการแก้ไขปริมาณและ/หรือมูลค่าสต๊อกแบบควบคุม นอกเหนือจากกระแสจัดซื้อและบริโภคปกติ การปรับสต๊อกแต่ละครั้งเป็นเอกสารที่มีส่วนหัว — เลขที่อ้างอิง, วันที่, ประเภท (`IN` หรือ `OUT`), ตำแหน่ง, แผนก, reason code, คำอธิบาย, หลักฐานแนบ — และรายการสินค้าหนึ่งบรรทัดหรือมากกว่า แต่ละบรรทัดประกอบด้วยสินค้า รายละเอียด lot (เมื่อสินค้าติดตาม lot) ต้นทุนต่อหน่วย ปริมาณ และยอดรวมต่อบรรทัดที่ระบบคำนวณให้; ส่วนหัวจะ roll up สิ่งเหล่านี้เป็น `inQty`, `outQty` และ `totalCost`

Adjustment ดำเนินตามวงจรชีวิตที่จำกัดอย่างเข้มงวด: `Draft` (แก้ไขได้ ยังไม่กระทบสต๊อก) → `Posted` (immutable, สต๊อกและ GL อัปเดตแล้ว) → `Void` (กลับรายการ adjustment ที่ post แล้วผ่านธุรกรรมแยกต่างหาก) Draft แก้ไขได้อย่างอิสระ แต่เมื่อ post แล้วเอกสารถูก lock — การแก้ไขต้อง void และทำ adjustment ใหม่ การ post ยังกระตุ้นการสร้าง stock-movement การคำนวณ FIFO layer หรือต้นทุนเฉลี่ยถ่วงน้ำหนักใหม่ตาม costing method ของสินค้า และการสร้าง journal entry อัตโนมัติเข้าบัญชี GL ที่ map จาก reason code

Adjustments ถูกใช้เมื่อใดก็ตามที่สต๊อกเปลี่ยนนอกเหนือจากเอกสารปกติ: ของเสียหายที่พบในห้องเก็บ, ของหมดอายุที่ถูก write-off, การ write-off จากขโมยหรือการสูญเสีย, ของที่พบคืนจากการตรวจสอบ, ผลต่างจาก physical count หรือ spot check ที่ post เป็น adjustment แบบโครงสร้าง, และการจัดประเภทใหม่ระหว่างตำแหน่งหรือหน่วยนับ โมดูลรองรับทั้งทิศทางบวก (`IN` — write-on) และลบ (`OUT` — write-off) พร้อมความละเอียดระดับ lot สำหรับสินค้าที่ติดตามแบบ batch

## 2. บริบททางธุรกิจ

Adjustments เป็นช่องทางเดียวที่ปล่อยให้สต๊อกเปลี่ยนโดยไม่มีเอกสาร procurement ต้นน้ำหรือเอกสารบริโภคปลายน้ำที่จับคู่กัน จึงอยู่ภายใต้การตรวจสอบ audit โดยปริยาย กลุ่มธุรกิจโรงแรมดำเนินงานบน margin ต้นทุนอาหารที่บางเฉียบ; adjustment ที่อธิบายไม่ได้หรือไม่ได้รับอนุมัติสามารถซ่อนการสูญเสีย ขโมย หรือความล้มเหลวของกระบวนการ และยอดที่ไม่สมดุล ณ ปิดงวดไม่สามารถปกป้องได้ต่อ external auditor การควบคุมของโมดูล — reason code ที่บังคับ, เอกสารหลักฐานแนบ, การอนุมัติแบบแยกบทบาท, ผลกระทบต่อสต๊อกเฉพาะเมื่อ post และสถานะ post ที่ immutable — มีอยู่เพื่อทำให้ทุกการแก้ไขสามารถอธิบายได้

ด้านการเงินสะท้อนแบบเดียวกัน Adjustment ที่ post แล้วทุกอันสร้าง journal entry: write-off (`OUT`) debit บัญชีค่าใช้จ่ายหรือการสูญเสียที่ map จาก reason code และ credit inventory ลดมูลค่าสต๊อกบน balance sheet; รายการ found-stock (`IN`) debit inventory และ credit บัญชีกำไร/การคืน Reason code กำหนดตามทิศทาง (`IN`, `OUT` หรือ `BOTH`) และมี GL mapping ของตัวเอง ดังนั้นเหตุการณ์ทางกายภาพเดียวกัน (เช่น write-off จากความเสียหาย vs. write-off จากการหมดอายุ) จะลงในบัญชีที่แตกต่างกันเพื่อการวิเคราะห์ต้นทุน การตรวจสอบสิ้นงวด reject adjustment ใด ๆ ที่ลงวันที่เข้างวดที่ปิดแล้ว เพื่อปกป้องการตีมูลค่าที่ lock ไว้

ในเชิงปฏิบัติการ adjustments ยังเป็นจุดลงเชิงระเบียบของผลต่างที่ตรวจพบโดย **physical-count** (นับเต็ม) และ **spot-check** (การตรวจยืนยันบางส่วน) เมื่อผลต่างการนับได้รับการยืนยัน ระบบจะสร้างเอกสาร adjustment สำหรับบรรทัดผลต่างและจัดเส้นทางผ่าน flow การอนุมัติและ posting เดียวกับ adjustment ที่สร้างเอง เพื่อให้การแก้ไขสต๊อกทั้งหมดแชร์ audit trail เดียวกัน

## 3. แนวคิดสำคัญ

- **Adjustment Type**: ทิศทางของการแก้ไข `IN` เพิ่มปริมาณ on-hand (write-on — ของพบใหม่, ส่วนเกินจากการนับ, ของที่คืนได้รับคืน) และ post เป็น stock movement แบบ `RECEIPT` `OUT` ลดปริมาณ on-hand (write-off — เสียหาย, หมดอายุ, ขโมย, ขาดจากการนับ) และ post แบบ `ISSUE` เก็บบน header เป็น `type: 'IN' | 'OUT'` แต่ละบรรทัดต้องสอดคล้องกับประเภทของ header
- **Reason Code**: รหัสที่จำเป็นต้องระบุเหตุผล *ทำไม* adjustment กำลังเกิดขึ้น (เช่น เสียหาย, หมดอายุ, ขโมย, ผลต่างนับ, จัดประเภทใหม่) พ่วง `type: 'IN' | 'OUT' | 'BOTH'` เพื่อให้เฉพาะเหตุผลที่ valid ปรากฏสำหรับทิศทางที่เลือก พร้อม `requiresDocument`, `requiresQualityCheck` และ `glAccount` ที่กำหนดบัญชีค่าใช้จ่าย/กำไรที่ journal การ post จะลง Reason code เป็นบังคับ (`ADJ_CRT_004`) และตรวจสอบกับประเภท adjustment (`ADJ_VAL_006`)
- **Cost Basis**: ต้นทุนต่อหน่วยที่ใช้กับแต่ละบรรทัดของ adjustment สำหรับ `OUT` ภายใต้ weighted-average costing บรรทัดใช้ต้นทุนเฉลี่ยปัจจุบัน; สำหรับ `OUT` ภายใต้ FIFO บรรทัดบริโภคต้นทุนจาก layer เก่าที่สุดก่อน สำหรับ `IN` ภายใต้ weighted-average การ post คำนวณค่าเฉลี่ยใหม่ — `New Average Cost = ((Old Qty × Old Cost) + (Adj Qty × Adj Cost)) / (Old Qty + Adj Qty)` (`ADJ_CALC_005`); ภายใต้ FIFO สร้าง cost layer ใหม่ ต้องระบุต้นทุนสำหรับทุกสินค้า (`ADJ_VAL_003`) และยอดต่อบรรทัด `Item Cost = Unit Cost × Quantity` (`ADJ_CALC_001`) ต้องเท่ากับ `totalCost` ของ header (`ADJ_VAL_005`)
- **Lot Tracking**: สำหรับสินค้าที่ควบคุมด้วย lot adjustment ต้องอ้างอิงหมายเลข lot เจาะจง (`ADJ_CRT_007`) แต่ละบรรทัดถือ array ของ `Lot { lotNo, quantity, uom, expiryDate? }` สำหรับ `OUT` ปริมาณ lot ห้ามเกินยอดคงเหลือต่อ lot (`ADJ_VAL_004`); สำหรับ `IN` สามารถสร้าง lot ใหม่ได้ ประวัติ lot ถูกรักษาตลอด end-to-end เพื่อให้ write-off จากหมดอายุและเหตุการณ์เรียกคืนสามารถสาวกลับได้
- **Approval Workflow / Status**: Adjustments เคลื่อนผ่าน `Draft` → `Posted` → `Void` (สามสถานะเดียวที่เก็บบน header) `Draft` คือสถานะทำงาน; adjustment แก้ไขได้ ยังไม่กระทบสต๊อกหรือ GL และเอกสารสามารถลบได้ `Posted` คือสถานะ active ปลายทาง — ยอดสต๊อกถูกอัปเดต, journal entry ถูกเขียน และเอกสารกลายเป็น immutable (`ADJ_PRC_007`) `Void` กลับรายการ adjustment ที่ post แล้ว แต่สร้างเป็นธุรกรรม *แยก* (`ADJ_PRC_008`) เพื่อให้การ post ต้นฉบับยังอยู่ใน audit trail การเปลี่ยนสถานะ ผู้ใช้ที่ทำ และ timestamp ถูก log ทั้งหมด
- **Posting (ผลกระทบสต๊อก + GL)**: การ post คือเหตุการณ์เดียวที่เปลี่ยนแปลงโลก — สต๊อกไม่ถูกอัปเดตจนกว่าจะ post (`ADJ_PRC_001`) เมื่อ post ระบบจะ: (1) เขียน stock-movement record ต่อบรรทัด, (2) อัปเดต `InventoryStatus.QuantityOnHand`, `LastUnitCost` และ `TotalCost`, (3) สร้าง/อัปเดต FIFO layers หรือ `AverageCostTracking` ตาม costing method ของสินค้า, (4) สร้าง `JournalEntry` rows ที่ map จาก `glAccount` ของ reason code และ cost-centre ของบรรทัด และ (5) ตรวจสอบว่าวันที่อยู่ในงวดบัญชีที่เปิดอยู่ (`ADJ_CRT_010`, `ADJ_PRC_009`) การตรวจสอบสต๊อกเรียลไทม์ (`ADJ_PRC_010`) ป้องกันยอดติดลบ (`ADJ_VAL_001`)

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Store Keeper / Warehouse Staff | ระบุความไม่ตรงในพื้นที่ ริเริ่ม adjustment ใน `Draft` แนบหลักฐานประกอบ (รูปถ่าย รายงานความเสียหาย ป้ายหมดอายุ) และระบุเหตุผล |
| Inventory Controller / Inventory Manager | review adjustment ที่ส่งเข้ามาเพื่อความถูกต้องและสมเหตุสมผล ติดตามรูปแบบผลต่างตาม reason และตำแหน่ง อนุมัติหรือปฏิเสธ และ post เอกสารให้มีผลกระทบต่อสต๊อกและ GL |
| Finance Team | ตรวจสอบผลกระทบทางต้นทุนและ GL account mapping ตาม reason code, กระทบยอด sub-ledger inventory กับ GL และเซ็นรับรองกิจกรรม adjustment ณ ปิดงวด |
| Department Manager | review adjustments ที่กระทบ cost-centre ของแผนก สืบสวนรูปแบบผิดปกติหรือผลต่างขนาดใหญ่ และผลักดันการเปลี่ยนแปลงเชิงกระบวนการแก้ไข |
| Auditor | ตรวจสอบ adjustment trail end-to-end — reason codes, เอกสารแนบ, ลายเซ็นอนุมัติ, journal entries และห่วง void — สำหรับ compliance และ segregation-of-duties |
| System Administrator | บำรุงรักษา master ของ reason code (codes, type, GL mapping, document-required flag) กำหนดสิทธิ์ผู้ใช้และเกณฑ์การอนุมัติ และจัดการการตั้งค่า integration |

## 5. โมดูลที่เกี่ยวข้อง

**กระแสข้ามโมดูล:**
- [inventory](/th/inventory/inventory) — adjustments แก้ไขยอดสต๊อกโดยตรง
- [costing](/th/inventory/costing) — adjustments ต้องการ cost basis (ใส่ด้วยมือหรือจาก costing engine)
- [physical-count](/th/inventory/physical-count) — ผลต่างการนับกลายเป็นเอกสาร adjustment
- [spot-check](/th/inventory/spot-check) — ผลต่างจากการนับบางส่วนกลายเป็นเอกสาร adjustment

**การกำหนดค่า master:**
- [master-data/adjustment-type](/th/inventory/master-data/adjustment-type) — master ของ reason code พร้อมทิศทาง (IN/OUT/BOTH) และ GL mapping ต่อเหตุผล
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยนับสำหรับปริมาณแต่ละบรรทัด
- [master-data/location](/th/inventory/master-data/location) — ตำแหน่งต้นทางที่ adjustment ขยับยอด
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม workflow การอนุมัติสำหรับการอนุญาต adjustment
- [system-config/period](/th/inventory/system-config/period) — gate งวดบัญชี; adjustments ที่ลงวันที่ในงวดที่ปิดถูก reject
- [access-control/user-location](/th/inventory/access-control/user-location) — จำกัดตำแหน่งที่ผู้ใช้สามารถปรับได้
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — log การเปลี่ยนสถานะ adjustment สำหรับ audit
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — รูปถ่ายที่จำเป็น / รายงานความเสียหาย / หลักฐาน เก็บกับ adjustment

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/inventory-adjustment/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — โมเดลข้อมูล](/th/inventory/inventory-adjustment/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [02 — กติกาทางธุรกิจ](/th/inventory/inventory-adjustment/02-business-rules) — การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูล
- [03 — User Flow](/th/inventory/inventory-adjustment/03-user-flow) — วงจรชีวิตเอกสาร พร้อมสารบัญ persona
  - [Store Keeper](/th/inventory/inventory-adjustment/03-user-flow-store-keeper)
  - [Inventory Controller](/th/inventory/inventory-adjustment/03-user-flow-inventory-controller)
  - [Finance](/th/inventory/inventory-adjustment/03-user-flow-finance)
  - [Audit / Config](/th/inventory/inventory-adjustment/03-user-flow-audit-config)
- [04 — Test Scenarios](/th/inventory/inventory-adjustment/04-test-scenarios) — ขอบเขต persona, scenario ข้าม persona, การ map E2E
  - [Store Keeper](/th/inventory/inventory-adjustment/04-test-scenarios-store-keeper)
  - [Inventory Controller](/th/inventory/inventory-adjustment/04-test-scenarios-inventory-controller)
  - [Finance](/th/inventory/inventory-adjustment/04-test-scenarios-finance)
  - [Audit / Config](/th/inventory/inventory-adjustment/04-test-scenarios-audit-config)
