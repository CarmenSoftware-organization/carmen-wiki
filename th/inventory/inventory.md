---
title: คลังสินค้า (Inventory)
description: ยอดคงเหลือสต๊อก ตำแหน่งจัดเก็บ และกระบวนการปิดงวด — แกนกลางของระบบ ERP ด้านคลังสินค้า
published: true
date: 2026-05-19T23:45:00.000Z
tags: inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# คลังสินค้า (Inventory)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** ระบบบันทึกหลักของยอดคงเหลือสต๊อก (สินค้า × คลัง × ตำแหน่ง × lot) และสายธารของการเคลื่อนไหวที่ป้อนข้อมูลให้กับการคำนวณต้นทุนและ snapshot ปิดงวด &nbsp;·&nbsp; **ผู้ใช้งาน:** Store Keeper, Inventory Controller, Finance &nbsp;·&nbsp; **เอนทิตี/ตารางสำคัญ:** `InventoryStatus`, รายการเคลื่อนไหวสต๊อก (`RECEIPT`/`ISSUE`/`TRANSFER`/`ADJUSTMENT`/`RETURN`/`WRITE_OFF`), `tb_period_snapshot`, ตาราง lot/batch &nbsp;·&nbsp; **หน้าย่อย:** 14

![คลังสินค้า (Inventory) screen](/screenshots/inventory/index.png)

## 1. ภาพรวม

โมดูล Inventory คือระบบบันทึกหลักของยอดคงเหลือสต๊อกทั่วทั้งทรัพย์สิน ยอดคงเหลือถูก key ด้วย **สินค้า × คลัง × ตำแหน่ง** (พร้อม batch/lot เพิ่มเติมเมื่อเปิดใช้การติดตาม batch) และเปิดเผยปริมาณ `onHand`, `allocated`, `available` และ `inTransit` ควบคู่กับรายละเอียดราย batch ทุกยอดคงเหลือพ่วงต้นทุนต่อหน่วยปัจจุบัน/เฉลี่ยมาด้วย เพื่อให้ปริมาณและการตีมูลค่าเดินไปด้วยกัน

การเปลี่ยนแปลงปริมาณทั้งหมดไหลผ่าน **stock movements** การเคลื่อนไหวมีประเภท — `RECEIPT`, `ISSUE`, `TRANSFER`, `ADJUSTMENT`, `RETURN` หรือ `WRITE_OFF` — ตำแหน่งต้นทาง ตำแหน่งปลายทาง (optional) บรรทัดรายการ และสถานะ workflow (`DRAFT` → `PENDING` → `IN_TRANSIT` → `COMPLETED` / `CANCELLED`) การเคลื่อนไหวจำแนกพฤติกรรมการ post: ตำแหน่งแบบ inventory จะ debit บัญชีสินทรัพย์สต๊อก ส่วนตำแหน่งแบบ direct-cost จะข้ามคลังและ post ตรงเข้าค่าใช้จ่ายของแผนก Returns, write-offs และ adjustments ใช้กระดูกสันหลังของการเคลื่อนไหวเดียวกัน แต่ต่างกันที่ทิศทาง journal และกฎการอนุมัติ

ณ สิ้นแต่ละงวดบัญชี โมดูลจะสร้าง **period-end snapshot**: การนับสต๊อกครั้งสุดท้ายจะถูกกระทบยอดกับปริมาณในระบบ ผลต่างถูก post เป็น adjustments การตีมูลค่าถูก lock และงวดถูกปิดจากการ post ย้อนหลัง snapshot คือสมอ audit ที่โมดูลปลายน้ำ (costing, financial reporting) บริโภคต่อ

## 2. บริบททางธุรกิจ

ในการดำเนินงานโรงแรม inventory คือที่ที่ต้นทุนอาหารอาศัยอยู่ ต้นทุนผันแปรส่วนใหญ่ของทรัพย์สิน — วัตถุดิบ F&B, อุปกรณ์แม่บ้าน, สต๊อก minibar — อยู่ในโมดูลนี้ก่อนกลายเป็น COGS การได้ยอดคงเหลือที่ถูกต้องสำคัญด้วยสามเหตุผล:

- **การควบคุมต้นทุนอาหาร** Plate cost, yield ของสูตร และความสามารถในการทำกำไรของเมนู ทั้งหมดขึ้นกับการเคลื่อนไหวสต๊อกที่แม่นยำที่ป้อนให้โมดูล costing สต๊อกผีซ่อนการสูญเสีย; การรับของที่ขาดหายไปทำให้ margin บนกระดาษพองเกินจริง
- **ความโปร่งใสในการ audit** กลุ่มธุรกิจโรงแรมทำงานภายใต้รอบ audit ที่เข้มงวด ทุกการเคลื่อนไหวสต๊อกต้องสาวกลับไปยังเอกสารต้นทาง (GRN, requisition, count sheet, อนุมัติ write-off) และการ lock สิ้นงวดต้องสามารถปกป้องได้ต่อ external auditor
- **การรายงานเชิงกฎระเบียบและรายงานกลุ่ม** การตีมูลค่า inventory ป้อน balance sheet; การจำแนกการเคลื่อนไหว (inventory vs. direct expense vs. consignment) กำหนดว่ายอดใช้จ่ายจะลงสินทรัพย์หรือ P&L วิธีผสมเป็นเรื่องปกติในเครือโรงแรม โมดูลต้องรักษาให้แต่ละตำแหน่งใช้วิธีของตนได้

โมดูลนี้ตั้งอยู่ระหว่าง **Procurement** (รับเข้า) และ **Operations** (เบิกออก) และเป็นแหล่งข้อมูลที่โมดูล **Costing** อ่านเพื่อตีมูลค่า

## 3. แนวคิดสำคัญ

- **Stock Balance**: ปริมาณคงเหลือของสินค้าที่คลังและตำแหน่งเจาะจง อาจแยกตาม batch/lot พ่วงปริมาณ `onHand`, `allocated`, `available`, `inTransit` พร้อมต้นทุนต่อหน่วยปัจจุบันและมูลค่ารวม อัปเดตจากทุก stock movement ที่ commit แล้ว
- **Location Type**: จำแนกตำแหน่งจัดเก็บเป็น `INVENTORY` (สินทรัพย์สต๊อก post เข้าบัญชี GL คลัง), `DIRECT` (cost centre แบบตรง post ตรงเข้าค่าใช้จ่ายแผนก) หรือ transit/วัตถุประสงค์พิเศษ Location type กำหนด journal entry ที่การเคลื่อนไหวสร้าง และกำหนดว่าสินค้านั้นจะปรากฏเป็นสินทรัพย์บน balance sheet หรือไม่
- **Stock Movement**: บันทึก post ที่ไม่สามารถแก้ได้ของการเปลี่ยนปริมาณ ระบุโดยประเภท (`RECEIPT`, `ISSUE`, `TRANSFER`, `ADJUSTMENT`, `RETURN`, `WRITE_OFF`) อ้างอิงเอกสารต้นทาง (GRN, store requisition, count, อนุมัติ write-off) และผลิตทั้งการอัปเดตยอดและ journal entry การเคลื่อนไหวคือหน่วยอะตอมที่ audit trail ถูกสร้างขึ้นมา
- **Period-End Snapshot**: สถานะที่ถูก lock ของยอดคงเหลือสต๊อกทุกยอด ณ สิ้นงวดบัญชี สร้างขึ้นหลังจาก checklist ปิดงวด (นับสต๊อก → กระทบยอดผลต่าง → อนุมัติ adjustment → ตรวจสอบการตีมูลค่า → lock งวด) ธุรกรรมย้อนหลังที่ post เข้างวดที่ปิดแล้วจะถูก reject โดยระบบ
- **Valuation Method**: สมมติฐาน cost-flow ที่ใช้กับสินค้า — `FIFO` หรือ `WEIGHTED_AVERAGE` — กำหนดต่อสินค้า (หรือกำหนดรวม) และใช้โดย costing engine เมื่อ movement บริโภคสต๊อก ดู [[costing]] สำหรับกฎการคำนวณ; โมดูลนี้เก็บ input (lot, วันที่, ต้นทุน) ที่ engine ต้องการ

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Store Keeper | บันทึก stock movement ประจำวัน — รับ เบิก โอน — และดำเนินการนับสต๊อกระดับตำแหน่ง |
| Inventory Controller | เป็นเจ้าของความถูกต้องของยอด: review ผลต่าง อนุมัติ adjustments ประสานงาน spot check และนับเต็ม เซ็นปิดการกระทบยอดสิ้นงวด |
| Finance | ตรวจสอบการตีมูลค่า กระทบยอด GL ของ inventory กับ sub-ledger อนุมัติ journal entry จาก movement และ lock งวดหลังปิด |

## 5. โมดูลที่เกี่ยวข้อง

**กระแสข้ามโมดูล:**
- [[costing]] — คำนวณต้นทุนเทียบกับยอดสต๊อก; ทุก stock movement อัปเดตการตีมูลค่า
- [[good-receive-note]] — GRN เป็นแหล่งต้นน้ำหลักของการรับสต๊อก
- [[store-requisition]] — store requisitions เป็นผู้บริโภคปลายน้ำหลัก
- [[inventory-adjustment]] — การปรับยอดด้วยมือ
- [[physical-count]] — การนับเต็มเป็นงวด
- [[spot-check]] — การนับยืนยันบางส่วน

**การกำหนดค่าหลัก:**
- [[master-data/unit]] — หน่วยฐาน หน่วยสั่ง และหน่วยสูตรของทุกยอดสต๊อก
- [[master-data/location]] — คลังและตำแหน่งจัดเก็บที่ผูกกับทุกยอดสต๊อก
- [[master-data/business-unit]] — ขอบเขต tenant/property ที่แยกยอดคงเหลือและ movement
- [[system-config/period]] — งวดบัญชีที่ gate การ post และ lock snapshot
- [[system-config/dimension]] — มิติเชิงวิเคราะห์ที่ประทับบนบรรทัด journal ของ movement
- [[access-control/user-location]] — จำกัดว่าผู้ใช้สามารถทำธุรกรรมกับตำแหน่งใดได้บ้าง
- [[reporting-audit/activity]] — log กิจกรรม movement และการเปลี่ยนยอดสำหรับ audit

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/inventory-management/`
- Concepts: `../carmen/docs/Inventory/`
- Frontend: `../carmen-inventory-frontend/`
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
