---
title: การคำนวณต้นทุน (Costing)
description: วิธีตีมูลค่าสินค้าคงคลัง (FIFO, Weighted Average) และเอนจินคำนวณต้นทุนสำหรับคิด COGS และมูลค่าสินค้าคงเหลือปลายงวด
published: true
date: 2026-07-22T10:00:00.000Z
tags: costing, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# การคำนวณต้นทุน (Costing)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เอนจินตีมูลค่าระดับธุรกรรมที่เลือก `cost_per_unit` ให้ทุกการเคลื่อนไหวขาออกและปรับปรุง `average_cost_per_unit` ให้ทุกการเคลื่อนไหวขาเข้า ภายใต้วิธี FIFO-หรือ-Average เดียวที่ตั้งค่า **ต่อ business unit** &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนา/QA ที่ทำงานกับการตีมูลค่าสินค้าคงคลัง — โมดูลนี้ไม่มี persona แยกในแอป มีแต่ permission gate ทั่วไปแบบ `inventory_management.*` &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_inventory_transaction_cost_layer` (ledger การไหลของต้นทุน), `tb_period_snapshot` (เฉพาะงวดที่ใช้วิธี average), `tb_business_unit.calculation_method`, [costing/calculation-methods](/th/inventory/costing/calculation-methods) &nbsp;·&nbsp; **หน้าย่อย:** 11

## 1. ภาพรวม

โมดูล Costing คือเอนจินตีมูลค่าของระบบ ERP สินค้าคงคลัง โดยใช้ข้อมูลธุรกรรมการเคลื่อนไหวสต๊อกที่ผลิตจากโมดูล Inventory และสำหรับธุรกรรมขาออกทุกครั้ง จะเลือก **ต้นทุนขาย (Cost of Goods Sold — COGS)** ที่จะใช้ ส่วนสำหรับธุรกรรมขาเข้าทุกครั้ง จะเขียน cost basis ของสต๊อกใหม่และ (ภายใต้ Weighted Average) ปรับปรุงค่าเฉลี่ยเคลื่อนที่ เอนจินทำงานแบบ per-transaction ไม่ใช่แบบ batch ตามคาบเวลา — การ commit GRN จะเขียนแถว cost-layer ขาเข้าในการเรียกเดียวกันกับที่ post GRN เพื่อให้ยอดคงเหลือและการตีมูลค่ายังคงสอดคล้องกับปริมาณ

รองรับสมมติฐาน cost-flow สองแบบ: **FIFO** ซึ่งเก็บการรับเข้าแต่ละครั้งเป็น lot แยก (`tb_inventory_transaction_cost_layer` เรียงตาม `lot_seq_no`) และใช้ lot เก่าที่สุดก่อน และ **Weighted Average Cost (WAC)** ซึ่งผสมการรับเข้าทุกครั้งเป็นค่าเฉลี่ยเคลื่อนที่เดียว (`average_cost_per_unit`) ต่อ `(location_id, product_id)` วิธีนี้ **ไม่สามารถ** ตั้งค่าต่อสินค้าหรือต่อหมวดได้ — เป็นค่าเดียวบน `tb_business_unit.calculation_method` (platform schema, `average` | `fifo`, default `average`) ที่ใช้กับทุกสินค้าใน business unit นั้น `InventoryTransactionService.getCalculationMethod(bu_code)` อ่านค่านี้ครั้งเดียวและใช้อย่างสม่ำเสมอ ไม่มี code path ที่ผสม FIFO กับ Average ภายใน business unit เดียว และไม่มีหน้าจอในแอปสำหรับเปลี่ยนค่านี้ — เป็นฟิลด์ระดับ platform/cluster-admin บน business unit ที่อยู่นอก route ของโมดูลนี้เอง ดู [01-data-model](/th/inventory/costing/01-data-model) § 5 สำหรับความแตกต่างฉบับเต็มจากกรอบคิดแบบต่อสินค้าเดิม

Output ลงที่สองที่: ตัวแถว cost-layer เองพก `cost_per_unit` / `average_cost_per_unit` ที่เลือกไว้ให้ผู้บริโภคปลายน้ำทุกราย (recipe costing, stock-card report, variance analysis) อ่าน; และตอนปิดงวด `tb_period_snapshot` จะล็อกคอลัมน์ opening/receipt/issue/adjustment/closing cost ของงวด — **เฉพาะเมื่อ business unit ใช้วิธี `average`** เท่านั้น เส้นทางปิดงวดแบบ FIFO จะนำยอดคงเหลือไปต่อเป็นแถว `close_period`/`open_period` บน cost-layer แทน และ **ไม่เขียน** `tb_period_snapshot` เลย (`processCloseTransactions` ใน `period-end.close-transaction.helper.ts`) ไม่มีการ post journal entry หรือ general ledger ที่ใดใน backend เลย — ไม่มี `Dr`/`Cr` ไม่มี GL control account ไม่มีโค้ด reconciliation ระหว่าง inventory กับ GL สำหรับโมดูลนี้ (สอดคล้องกับข้อค้นพบเดียวกันที่ยืนยันแล้วบน [inventory/01-data-model](/th/inventory/inventory/01-data-model) § 1) อัลกอริทึม FIFO vs WAC อย่างละเอียด ตัวอย่างตัวเลข และ trade-off ระหว่างสองวิธี อยู่ในหน้าย่อยด้านล่าง — หน้านี้เป็นเพียงจุดเริ่มต้น

## 2. บริบททางธุรกิจ

การตีมูลค่าสินค้าคงคลังเป็นกิจกรรมที่มีกฎควบคุม ทั้ง **IFRS** (IAS 2) และ **US GAAP** (ASC 330) ยอมรับ FIFO และ Weighted Average เป็นสมมติฐาน cost-flow ที่ใช้ได้ แต่ต้องเลือกใช้อย่างสม่ำเสมอต่อหมวดสินค้าและเปิดเผยในงบการเงิน ดังนั้นโมดูล costing จึงเป็นองค์ประกอบที่หันหน้าเข้าหา audit: ตัวเลข COGS ทุกตัวต้อง trace กลับไปยังการรับเข้าครั้งใดครั้งหนึ่ง (FIFO) หรือการคำนวณค่าเฉลี่ยเคลื่อนที่ครั้งใดครั้งหนึ่ง (WAC) และ trail ต้องอยู่ผ่านวัฏจักรการตรวจสอบภายนอกได้

เชิงปฏิบัติงาน costing คือที่ที่ **food cost control** อยู่ Plate cost, recipe profitability, และการตัดสินใจ menu-engineering ทั้งหมดอ่านจากโมดูลนี้ ถ้าเอนจิน costing เลื่อน — lot เก่าค้าง waste write-off ตกหล่น การคำนวณค่าเฉลี่ยใหม่ผิดหลังการคืน — ทุกตัวเลข margin ปลายน้ำก็จะเลื่อนตาม กลุ่มโรงแรมมักดำเนินงานบน margin ค่าอาหารที่บางมาก ดังนั้นความผิดพลาดในการตีมูลค่าหนึ่งหรือสองจุดเปอร์เซ็นต์จะแปลตรงเป็น P&L miss ที่สังเกตเห็นได้ โมดูลนี้คือสัญญาระหว่างการเคลื่อนไหวสต๊อกทางกายภาพและภาพการเงินที่ธุรกิจใช้ในการขับเคลื่อน

## 3. แนวคิดสำคัญ

- **COGS (Cost of Goods Sold)**: ต้นทุนที่เลือกเมื่อสินค้าออกจากสถานที่ประเภท inventory เพื่อบริโภค (issue ไปครัว, write-off, ขายผ่าน POS-linked recipe) เขียนโดยเอนจิน costing ลงบนแถว `tb_inventory_transaction_cost_layer` ขาออก ณ ตอนเกิดการเคลื่อนไหว ไม่มีการ post journal entry / general ledger ที่ใดใน backend เลย — ตัวแถว cost-layer เองคือบันทึกถาวรเพียงอย่างเดียวของต้นทุนการเคลื่อนไหวนั้น
- **มูลค่าสินค้าคงเหลือปลายงวด (Ending Inventory Value)**: มูลค่าเงินของสต๊อกที่มีอยู่ ณ จุดเวลาใดเวลาหนึ่ง — ปริมาณคูณต้นทุนต่อหน่วยตามวิธี costing ที่ใช้งานอยู่ บน business unit ที่ใช้ **วิธี average** ค่านี้จะถูกล็อกเข้า `tb_period_snapshot` ตอนปิดงวด; บน business unit ที่ใช้ **วิธี FIFO** ค่านี้คำนวณจาก lot คงเหลือบน cost-layer ที่ถูกนำไปต่อเป็นแถว `open_period` (ไม่มีการเขียนแถว snapshot)
- **FIFO (First-In, First-Out)**: สมมติฐาน cost-flow ที่การรับเข้าเก่าที่สุดถูกใช้ก่อน การรับเข้าแต่ละครั้งกลายเป็น **lot** แยกที่มีต้นทุนต่อหน่วยของตัวเอง เอนจินใช้ lot ตามลำดับจนกระทั่งปริมาณที่ issue ได้รับการตอบสนอง ดังนั้นต้นทุนเก่าจะไหลไป COGS ในขณะที่ต้นทุนใหม่ยังคงอยู่ในสินค้าคงเหลือปลายงวด
- **Weighted Average Cost (WAC)**: สมมติฐาน cost-flow ที่การรับเข้าทุกครั้งถูกผสมเป็นต้นทุนต่อหน่วยเฉลี่ยเคลื่อนที่เดียว ค่าเฉลี่ยถูกคำนวณใหม่ทุกการรับเข้าด้วย `(prevQty × prevAvg + receivedQty × receivedCost) / (prevQty + receivedQty)` การ issue ถูก cost ที่ค่าเฉลี่ยที่มีอยู่ ณ เวลาการ issue สินค้าคงเหลือปลายงวดและ COGS ทั้งคู่สะท้อนต้นทุนผสมเดียวกัน
- **Lot/Batch**: กลุ่มสต๊อกที่ระบุได้จากการรับเข้าครั้งเดียว มีปริมาณ วันที่รับ และต้นทุนต่อหน่วยของตัวเอง จำเป็นสำหรับ FIFO (เอนจินใช้ lot ตามลำดับการรับ) และใช้แยกต่างหากสำหรับการติดตามวันหมดอายุและ traceability ของสินค้า
- **Cost Basis**: ต้นทุนต่อหน่วยที่เอนจินกำหนดให้ยอดคงเหลือเพื่อการตีมูลค่าและ costing ปลายน้ำ ภายใต้ FIFO เป็น per-lot; ภายใต้ WAC เป็นค่าเฉลี่ยเคลื่อนที่ปัจจุบันสำหรับสินค้าที่สถานที่ การปรับ การคืน หรือการบริโภคใน recipe ทุกอย่างต้องการ cost basis จากโมดูลนี้ — เอนจินคือแหล่งความจริงเดียวสำหรับ "หน่วยนี้ราคาเท่าไหร่?"

## 4. บทบาทและ Persona

**แก้ไข (ยืนยันแล้ว 2026-07-22):** ฉบับร่างก่อนหน้าของโมดูลนี้เอกสาร RBAC persona แยกกันสามแบบ (Finance, Inventory Controller, Auditor) พร้อม approval queue เฉพาะ, valuation-policy console, sub-ledger ↔ GL reconciliation dashboard, และ read-only audit workspace ไม่มีสิ่งใดในนั้นมีอยู่จริงในผลิตภัณฑ์ ตัวเอนจินเองไม่มีหน้าจอที่ถูก gate ด้วย persona เลย — มันเป็น service ที่ถูกเรียกจาก GRN commit, store-requisition issue, inventory-adjustment, credit-note, และ period-end หน้าจอในแอปที่มีจริงมีเพียงสองหน้าจอ period-end ทั่วไป (gate ด้วย `inventory_management.period_end.view` / `.execute` ไม่ใช่ด้วยชื่อ role) ตามที่เอกสารไว้ที่ [inventory/period-end](/th/inventory/inventory/period-end); `enum_stage_role` (enum role เดียวใน tenant schema) คือ `{create, approve, purchase, issue, view_only}` — ไม่มีสมาชิก `finance` หรือ `auditor` และโมดูล inventory-adjustment (สิ่งที่ใกล้เคียงที่สุดกับหน้าจอ "ใครแก้ cost basis") ไม่มี approval queue เลย: `StockInService.create()` / `StockOutService.create()` post ทันทีเมื่อสร้าง ([inventory-adjustment](/th/inventory/inventory-adjustment) § 1)

| ใคร (ความสนใจตามหน้าที่ ไม่ใช่หน้าจอหรือ RBAC role แยก) | สิ่งที่พวกเขาสนใจ |
|------|----------------|
| ผู้ถือ permission `inventory_management.period_end.execute` | รันการปิดงวดตามที่เอกสารไว้ที่ [inventory/period-end](/th/inventory/inventory/period-end); บน business unit ที่ใช้วิธี average การกระทำนี้จะจุดชนวนการเขียน `tb_period_snapshot` |
| ผู้สร้าง GRN, store requisition, inventory adjustment, หรือ credit note | ฟิลด์ต้นทุนในเอกสารของพวกเขาคือสิ่งที่เอนจินเลือกหรือเขียนโดยตรง — ดู [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory-adjustment](/th/inventory/inventory-adjustment) |
| Platform/cluster admin | ตั้งค่า `tb_business_unit.calculation_method` ตอนสร้าง business unit — อยู่นอก route ของ wiki module นี้ |

## 5. โมดูลที่เกี่ยวข้อง

**Cross-module flow:**
- [inventory](/th/inventory/inventory) — costing ทำงานบนการเคลื่อนไหวของสินค้าคงคลัง; ทุก IN/OUT จุดชนวนการคำนวณ costing
- [good-receive-note](/th/inventory/good-receive-note) — การรับ GRN ตั้งต้นทุนต่อหน่วย (FIFO) หรืออัปเดตค่าเฉลี่ย (WAC)
- [recipe](/th/inventory/recipe) — การบริโภคใน recipe ใช้ปริมาณที่ cost แล้วเพื่อคำนวณ food cost
- [inventory-adjustment](/th/inventory/inventory-adjustment) — การปรับต้องการ cost basis จากเอนจิน costing

**การตั้งค่าหลัก:**
- [master-data/business-unit](/th/inventory/master-data/business-unit) — ขอบเขต tenant/property สำหรับ ledger การตีมูลค่า
- [master-data/currency](/th/inventory/master-data/currency) — สกุลเงินทำรายการและสกุลเงินฐาน รวมถึงอัตรา FX; ยังไม่ยืนยันจากซอร์สว่าการแปลง FX ถูกเก็บไว้ต่อแถว cost-layer หรือไม่ (ดู [02-business-rules](/th/inventory/costing/02-business-rules) § 5.2)
- [master-data/unit](/th/inventory/master-data/unit) — การแปลงหน่วยฐานที่จำเป็นสำหรับการตีมูลค่าบรรทัดที่ cost ใด ๆ
- [system-config/period](/th/inventory/system-config/period) — งวดบัญชีที่ควบคุมการ post costing และล็อกการตีมูลค่า
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — บันทึกกิจกรรมการคำนวณใหม่และการ post costing เพื่อ audit

## 6. แหล่งข้อมูลอ้างอิง

- Concepts: `../carmen/docs/costing/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — แบบจำลองข้อมูล](/th/inventory/costing/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [02 — กฎทางธุรกิจ](/th/inventory/costing/02-business-rules) — การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูล
- [03 — User Flow](/th/inventory/costing/03-user-flow) — วงจรชีวิตของเอกสารและสารบัญ persona
  - [Finance](/th/inventory/costing/03-user-flow-finance)
  - [Inventory Controller](/th/inventory/costing/03-user-flow-inventory-controller)
  - [Auditor](/th/inventory/costing/03-user-flow-auditor)
- [04 — Test Scenarios](/th/inventory/costing/04-test-scenarios) — ขอบเขตของแต่ละ persona, scenario ข้าม persona และ mapping ไปยัง E2E
  - [Finance](/th/inventory/costing/04-test-scenarios-finance)
  - [Inventory Controller](/th/inventory/costing/04-test-scenarios-inventory-controller)
  - [Auditor](/th/inventory/costing/04-test-scenarios-auditor)
- [วิธีคำนวณต้นทุนสินค้าคงคลัง: FIFO vs. Weighted Average](/th/inventory/costing/calculation-methods) — เปรียบเทียบวิธีและอัลกอริทึม
