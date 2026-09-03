---
title: คลังสินค้า (Inventory)
description: ยอดคงเหลือสต๊อก ตำแหน่งจัดเก็บ และกระบวนการปิดงวด — แกนกลางของระบบ ERP ด้านคลังสินค้า
published: true
date: 2026-07-15T09:00:00.000Z
tags: inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# คลังสินค้า (Inventory)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ระบบบันทึกหลักของการเคลื่อนไหวสต๊อก (สินค้า × ตำแหน่ง × lot) — ledger ธุรกรรมแบบ append-only ที่ป้อนข้อมูลให้การคำนวณต้นทุน พร้อมกระบวนการปิดงวด &nbsp;·&nbsp; **หน้าจอ:** `/inventory-management/transaction` (ledger แบบอ่านอย่างเดียว), `/inventory-management/period-end` + `/review` (ปิดงวด) &nbsp;·&nbsp; **ตารางสำคัญ:** `tb_inventory_transaction` (+ `_detail`, `_cost_layer`), `tb_period`, `tb_period_snapshot` (เฉพาะ tenant วิธี average) &nbsp;·&nbsp; **หน้าย่อย:** 14

![คลังสินค้า (Inventory) screen](/screenshots/inventory/index.png)

## 1. ภาพรวม

โมดูล Inventory คือระบบบันทึกหลักของการเคลื่อนไหวสต๊อกทั่วทั้งทรัพย์สิน **ไม่มีแถวยอดคงเหลือที่ persist ไว้** — on-hand ที่ `(location, product, lot)` เป็นผลรวมที่คำนวณจาก ledger ของ cost layer เสมอ (`Σ in_qty − Σ out_qty`) และตัวเลขยอดคงเหลือทุกจุดในผลิตภัณฑ์ (dialog on-hand ของ PR, system qty ของ spot check) อ่านจากผลรวมเดียวกันนี้ ต้นทุนต่อหน่วยเดินทางไปกับแต่ละ layer เพื่อให้ปริมาณและการตีมูลค่าเดินไปด้วยกัน

การเปลี่ยนแปลงปริมาณทั้งหมดไหลผ่าน **inventory transactions** ธุรกรรมถูกจำแนกด้วย `enum_inventory_doc_type` — `good_received_note`, `credit_note`, `store_requisition`, `stock_in`, `stock_out`, `close` หรือ `open` — และชี้ไปยังเอกสารต้นทางที่สร้างมัน ธุรกรรม**ไม่มีสถานะ workflow ของตัวเอง**: มันถูกเขียนในสภาพ posted แล้วเมื่อเอกสารต้นทางไปถึงเหตุการณ์ posting ของมัน (GRN **save**, SR อนุมัติที่ stage สุดท้าย, inventory-adjustment เสร็จสมบูรณ์, credit-note เสร็จสมบูรณ์, การปิดงวด) การรับเข้าตำแหน่งชนิด `direct` จะเขียนการเบิกหักล้างอัตโนมัติเพิ่มอีกหนึ่งรายการที่ต้นทุนเดียวกัน ทำให้ on-hand สุทธิเป็นศูนย์ ("เบิกใช้ทันทีที่มาถึง"); ไม่มีการ post GL/journal สำหรับ movement ใด ๆ (ดู [01 — แบบจำลองข้อมูล](/th/inventory/inventory/01-data-model) § 1)

ณ สิ้นแต่ละงวดบัญชี โมดูลจะรัน **การปิดงวด (period-end close)**: เอกสารที่ยังค้างและการนับสต๊อกถูกตรวจเป็น gate ที่ block การปิด จากนั้นยอดคงเหลือของทุก lot จะถูกทำให้เป็นศูนย์ในงวดที่ปิดและถูกสร้างขึ้นใหม่ในงวดถัดไปที่ต้นทุนเดิม บน tenant วิธี average การปิดยังเขียนแถว `tb_period_snapshot` ด้วย (opening / bucket การเคลื่อนไหว / closing ต่อสินค้า × ตำแหน่ง); tenant แบบ FIFO ยก lot ไปข้างหน้าโดยไม่มี snapshot movement ใหม่ประทับเข้างวดที่เปิดอยู่ปัจจุบันเสมอ — แถวย้อนหลังไม่มีวันเข้างวดที่ปิดแล้ว

## 2. บริบททางธุรกิจ

ในการดำเนินงานโรงแรม inventory คือที่ที่ต้นทุนอาหารอาศัยอยู่ ต้นทุนผันแปรส่วนใหญ่ของทรัพย์สิน — วัตถุดิบ F&B, อุปกรณ์แม่บ้าน, สต๊อก minibar — อยู่ในโมดูลนี้ก่อนกลายเป็น COGS การได้ยอดคงเหลือที่ถูกต้องสำคัญด้วยสามเหตุผล:

- **การควบคุมต้นทุนอาหาร** Plate cost, yield ของสูตร และความสามารถในการทำกำไรของเมนู ทั้งหมดขึ้นกับการเคลื่อนไหวสต๊อกที่แม่นยำที่ป้อนให้โมดูล costing สต๊อกผีซ่อนการสูญเสีย; การรับของที่ขาดหายไปทำให้ margin บนกระดาษพองเกินจริง
- **ความโปร่งใสในการ audit** กลุ่มธุรกิจโรงแรมทำงานภายใต้รอบ audit ที่เข้มงวด ทุกการเคลื่อนไหวสต๊อกต้องสาวกลับไปยังเอกสารต้นทาง (GRN, requisition, count sheet, อนุมัติ write-off) และการ lock สิ้นงวดต้องสามารถปกป้องได้ต่อ external auditor
- **การรายงานเชิงกฎระเบียบและรายงานกลุ่ม** การตีมูลค่า inventory ป้อน balance sheet; การจำแนกการเคลื่อนไหว (inventory vs. direct expense vs. consignment) กำหนดว่ายอดใช้จ่ายจะลงสินทรัพย์หรือ P&L วิธีผสมเป็นเรื่องปกติในเครือโรงแรม โมดูลต้องรักษาให้แต่ละตำแหน่งใช้วิธีของตนได้

โมดูลนี้ตั้งอยู่ระหว่าง **Procurement** (รับเข้า) และ **Operations** (เบิกออก) และเป็นแหล่งข้อมูลที่โมดูล **Costing** อ่านเพื่อตีมูลค่า

## 3. แนวคิดสำคัญ

- **Stock Balance (derived)**: ปริมาณคงเหลือของสินค้าที่ตำแหน่งหนึ่ง อาจแยกตาม lot **ไม่ใช่ตาราง** — คำนวณเป็น `Σ cost_layer.in_qty − Σ out_qty` สำหรับ key นั้นเสมอ ไม่มีคอลัมน์ `allocated` / `available` / `inTransit` อยู่จริง; อะไรก็ตามที่มีรูปทรงแบบนั้นถูกคำนวณจากสถานะเอกสารที่ยังเปิดอยู่ ณ เวลาอ่าน
- **Location Type**: จำแนกตำแหน่งจัดเก็บเป็น `inventory` (ยอดคงเหลือสะสมตามปกติ), `direct` (การรับจะเบิกตัวเองออกอัตโนมัติที่ต้นทุนเดียวกัน — on-hand สุทธิเป็นศูนย์ "เบิกใช้ทันทีที่มาถึง") หรือ `consignment` (ไม่พบ code path แยกเฉพาะ — พฤติกรรมเหมือน `inventory` ในแง่ cost layer และการนับ) ไม่มีผลทาง GL ที่ยืนยันได้สำหรับทั้งสามค่า
- **Inventory Transaction**: บันทึก posted ที่ไม่สามารถแก้ได้ของการเปลี่ยนปริมาณ จำแนกตามโมดูลต้นทาง (`enum_inventory_doc_type`) บน header และตามผล cost-flow (`enum_transaction_type` — `good_received_note`, `issue`, `transfer_in/out`, `adjustment_in/out`, `credit_note_*`, `eop_*`, `close_period`, `open_period`) บน cost layer อ้างอิงเอกสารต้นทางแบบ polymorphic; movement คือหน่วยอะตอมที่ audit trail ถูกสร้างขึ้นมา
- **Period-End Close**: การปิดงวดบัญชีที่มี gate ตรวจสอบ (`open → closed` บน `tb_period.status`) gate ที่ block ได้แก่: PR/PO/SR ที่ยัง in-progress, GRN/CN ในสถานะกลางทาง และการนับสต๊อกที่ยังไม่เสร็จที่ตำแหน่งที่บังคับนับ การปิดจะทำให้ทุก lot ที่ยังเหลืออยู่เป็นศูนย์ (`CLOSE-…`) และสร้างขึ้นใหม่ในงวดถัดไปที่ถูก provision อัตโนมัติ (`OPEN-…`); บน tenant วิธี average ยังเขียน bucket ของ `tb_period_snapshot` ด้วย การ backdate ถูกจัดการด้วยการ re-date (movement ประทับเข้างวดที่เปิดอยู่เสมอ) ไม่ใช่การ reject
- **Valuation Method**: สมมติฐาน cost-flow — `fifo` หรือ `average` — กำหนด**ต่อ business unit** (`tb_business_unit.calculation_method`, platform schema; ค่าเริ่มต้น `average`) ไม่ใช่ต่อสินค้า posting engine ใช้อย่างสม่ำเสมอทั่วทั้ง tenant เมื่อ movement บริโภคสต๊อก ดู [costing](/th/inventory/costing) สำหรับกฎการคำนวณ; โมดูลนี้เก็บ input (lot, วันที่, ต้นทุน) ที่ engine ต้องการ

## 4. บทบาทและ Persona

ระบบไม่ได้นิยาม role ของโมดูล inventory ไว้ — การเข้าถึงเป็นแบบ permission key (`constant/permissions.ts`) และ "persona" ที่ใช้ในหน้า user-flow / test-scenario ของโมดูลนี้เป็นการจัดกลุ่มเชิงเอกสารครอบ key เหล่านั้น ไม่ใช่เอนทิตีของระบบ:

| Persona (การจัดกลุ่มเชิงเอกสาร) | พื้นผิวการเข้าถึงจริง |
|------|----------------|
| Store Keeper | อ่าน transaction ledger (`inventory_management.view`); สร้างการปรับยอดในโมดูลพี่น้อง [inventory-adjustment](/th/inventory/inventory-adjustment) (`inventory_management.stock_in.*` / `.stock_out.*`) และการนับใน [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) |
| Inventory Controller / ผู้ดำเนินการปิดงวด | รันการ review และการปิดงวด (`inventory_management.period_end.view` / `.execute`) ไม่มี approval queue, variance dashboard หรือการ route ตาม threshold ในโมดูลนี้ |
| Finance | **ไม่มี role Finance หรือพื้นผิว GL อยู่จริง** — `enum_stage_role` ไม่มีสมาชิก `finance` และไม่พบโค้ด post journal; ดูหน้าแก้ไขข้อมูล [User Flow — Finance](/th/inventory/inventory/03-user-flow-finance) และ [01 — แบบจำลองข้อมูล](/th/inventory/inventory/01-data-model) § 1 |

## 5. โมดูลที่เกี่ยวข้อง

**กระแสข้ามโมดูล:**
- [costing](/th/inventory/costing) — คำนวณต้นทุนเทียบกับยอดสต๊อก; ทุก stock movement อัปเดตการตีมูลค่า
- [good-receive-note](/th/inventory/good-receive-note) — GRN เป็นแหล่งต้นน้ำหลักของการรับสต๊อก
- [store-requisition](/th/inventory/store-requisition) — store requisitions เป็นผู้บริโภคปลายน้ำหลัก
- [inventory-adjustment](/th/inventory/inventory-adjustment) — การปรับยอดด้วยมือ
- [physical-count](/th/inventory/physical-count) — การนับเต็มเป็นงวด
- [spot-check](/th/inventory/spot-check) — การนับยืนยันบางส่วน

**การกำหนดค่าหลัก:**
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยฐาน หน่วยสั่ง และหน่วยสูตรของทุกยอดสต๊อก
- [master-data/location](/th/inventory/master-data/location) — คลังและตำแหน่งจัดเก็บที่ผูกกับทุกยอดสต๊อก
- [master-data/business-unit](/th/inventory/master-data/business-unit) — ขอบเขต tenant/property ที่แยกยอดคงเหลือและ movement
- [system-config/period](/th/inventory/system-config/period) — งวดบัญชีที่ gate การ post และ lock snapshot
- [system-config/dimension](/th/inventory/system-config/dimension) — มิติเชิงวิเคราะห์ที่เก็บใน JSON `dimension` บนธุรกรรมและ cost layer
- [access-control/user-location](/th/inventory/access-control/user-location) — จำกัดว่าผู้ใช้สามารถทำธุรกรรมกับตำแหน่งใดได้บ้าง
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — log กิจกรรม movement และการเปลี่ยนยอดสำหรับ audit

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/inventory-management/`
- Concepts: `../carmen/docs/Inventory/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — แบบจำลองข้อมูล](/th/inventory/inventory/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [02 — กฎทางธุรกิจ](/th/inventory/inventory/02-business-rules) — การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูล
- [03 — User Flow](/th/inventory/inventory/03-user-flow) — วงจรชีวิตของ movement และงวด พร้อมสารบัญ persona
  - [Store Keeper](/th/inventory/inventory/03-user-flow-store-keeper)
  - [Inventory Controller](/th/inventory/inventory/03-user-flow-inventory-controller)
  - [Finance](/th/inventory/inventory/03-user-flow-finance)
  - [Audit / Config](/th/inventory/inventory/03-user-flow-audit-config)
- [04 — Test Scenarios](/th/inventory/inventory/04-test-scenarios) — ขอบเขต persona, scenario ข้าม persona, การ map E2E
  - [Store Keeper](/th/inventory/inventory/04-test-scenarios-store-keeper)
  - [Inventory Controller](/th/inventory/inventory/04-test-scenarios-inventory-controller)
  - [Finance](/th/inventory/inventory/04-test-scenarios-finance)
  - [Audit / Config](/th/inventory/inventory/04-test-scenarios-audit-config)
