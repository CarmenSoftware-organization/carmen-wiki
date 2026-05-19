---
title: การคำนวณต้นทุน (Costing)
description: วิธีตีมูลค่าสินค้าคงคลัง (FIFO, Weighted Average) และเอนจินคำนวณต้นทุนสำหรับคิด COGS และมูลค่าสินค้าคงเหลือปลายงวด
published: true
date: 2026-05-17T12:00:00.000Z
tags: costing, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# การคำนวณต้นทุน (Costing)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เอนจินตีมูลค่าระดับธุรกรรมที่คำนวณ COGS สำหรับสินค้าออกและปรับปรุงต้นทุนพื้นฐานของสินค้าเข้าภายใต้ FIFO หรือ Weighted Average &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Finance, Inventory Controller, Auditor &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_period_snapshot`, FIFO cost layers, `AverageCostTracking`, `JournalEntry`, [[costing/calculation-methods]] &nbsp;·&nbsp; **หน้าย่อย:** 11

## 1. ภาพรวม

โมดูล Costing คือเอนจินตีมูลค่าของระบบ ERP สินค้าคงคลัง โดยใช้ข้อมูลธุรกรรมการเคลื่อนไหวสต๊อกที่ผลิตจากโมดูล Inventory และสำหรับธุรกรรมขาออกทุกครั้ง จะคำนวณ **ต้นทุนขาย (Cost of Goods Sold — COGS)** ที่เรียกเก็บจากแผนกหรือ revenue centre ส่วนสำหรับธุรกรรมขาเข้าทุกครั้ง จะปรับปรุง **ต้นทุนพื้นฐาน (cost basis)** ของยอดคงเหลือที่ได้รับผลกระทบ เอนจินทำงานแบบ per-transaction ไม่ใช่แบบ batch ตามคาบเวลา — บรรทัด GRN ที่ post ตอน 14:02 จะถูก cost ตอน 14:02 เพื่อให้ยอดคงเหลือและการตีมูลค่ายังคงสอดคล้องกับปริมาณ

รองรับสมมติฐาน cost-flow สองแบบ ตั้งค่าได้ต่อสินค้า (หรือทั้งระบบ): **FIFO** ซึ่งเก็บการรับเข้าแต่ละครั้งเป็น lot แยกและใช้ lot เก่าที่สุดก่อน และ **Weighted Average Cost (WAC)** ซึ่งผสมการรับเข้าทุกครั้งเป็นค่าเฉลี่ยเคลื่อนที่เดียว เอนจินเปิดเผย input และ output แบบเดียวกันทั้งสองกรณี — ปริมาณที่ลง cost, ต้นทุนต่อหน่วย, journal entry, และการตีมูลค่ายอดคงเหลือใหม่ — ดังนั้นผู้บริโภคปลายน้ำ (recipe costing, financial reporting, variance analysis) ไม่จำเป็นต้องรู้ว่าสินค้าใดใช้วิธีไหน

Output จะลงที่สามที่: ยอดคงเหลือสต๊อกมี `currentCost` และ `totalValue` ที่อัปเดตล่าสุด; การเคลื่อนไหวขาออก (`ISSUE`, `WRITE_OFF`, `TRANSFER` จากสถานที่ inventory) มี COGS ที่เกิดขึ้นจริงเข้าสู่ GL; และ snapshot ปลายงวดล็อกการตีมูลค่าที่งบดุลและรายงานต้นทุนอาหารใช้ อัลกอริทึม FIFO vs WAC อย่างละเอียด ตัวอย่างตัวเลข และ trade-off ระหว่างสองวิธี อยู่ในหน้าย่อยด้านล่าง — หน้านี้เป็นเพียงจุดเริ่มต้น

## 2. บริบททางธุรกิจ

การตีมูลค่าสินค้าคงคลังเป็นกิจกรรมที่มีกฎควบคุม ทั้ง **IFRS** (IAS 2) และ **US GAAP** (ASC 330) ยอมรับ FIFO และ Weighted Average เป็นสมมติฐาน cost-flow ที่ใช้ได้ แต่ต้องเลือกใช้อย่างสม่ำเสมอต่อหมวดสินค้าและเปิดเผยในงบการเงิน ดังนั้นโมดูล costing จึงเป็นองค์ประกอบที่หันหน้าเข้าหา audit: ตัวเลข COGS ทุกตัวต้อง trace กลับไปยังการรับเข้าครั้งใดครั้งหนึ่ง (FIFO) หรือการคำนวณค่าเฉลี่ยเคลื่อนที่ครั้งใดครั้งหนึ่ง (WAC) และ trail ต้องอยู่ผ่านวัฏจักรการตรวจสอบภายนอกได้

เชิงปฏิบัติงาน costing คือที่ที่ **food cost control** อยู่ Plate cost, recipe profitability, และการตัดสินใจ menu-engineering ทั้งหมดอ่านจากโมดูลนี้ ถ้าเอนจิน costing เลื่อน — lot เก่าค้าง waste write-off ตกหล่น การคำนวณค่าเฉลี่ยใหม่ผิดหลังการคืน — ทุกตัวเลข margin ปลายน้ำก็จะเลื่อนตาม กลุ่มโรงแรมมักดำเนินงานบน margin ค่าอาหารที่บางมาก ดังนั้นความผิดพลาดในการตีมูลค่าหนึ่งหรือสองจุดเปอร์เซ็นต์จะแปลตรงเป็น P&L miss ที่สังเกตเห็นได้ โมดูลนี้คือสัญญาระหว่างการเคลื่อนไหวสต๊อกทางกายภาพและภาพการเงินที่ธุรกิจใช้ในการขับเคลื่อน

## 3. แนวคิดสำคัญ

- **COGS (Cost of Goods Sold)**: ต้นทุนที่เรียกเก็บเป็นค่าใช้จ่ายเมื่อสินค้าออกจากสถานที่ประเภท inventory เพื่อบริโภค (issue ไปครัว, write-off, ขายผ่าน POS-linked recipe) คำนวณโดยเอนจิน costing ตอนเกิดการเคลื่อนไหว post เป็น debit ไปยัง cost centre ที่ใช้และ credit ไปยังบัญชีสินทรัพย์ inventory
- **มูลค่าสินค้าคงเหลือปลายงวด (Ending Inventory Value)**: มูลค่าเงินของสต๊อกที่มีอยู่ ณ จุดเวลาใดเวลาหนึ่ง — ปริมาณคูณต้นทุนต่อหน่วยตามวิธี costing ที่ใช้งานอยู่ ล็อกเข้า snapshot ปลายงวดและรายงานในงบดุล เท่ากับ มูลค่าเปิด + รับเข้า - COGS - การปรับ
- **FIFO (First-In, First-Out)**: สมมติฐาน cost-flow ที่การรับเข้าเก่าที่สุดถูกใช้ก่อน การรับเข้าแต่ละครั้งกลายเป็น **lot** แยกที่มีต้นทุนต่อหน่วยของตัวเอง เอนจินใช้ lot ตามลำดับจนกระทั่งปริมาณที่ issue ได้รับการตอบสนอง ดังนั้นต้นทุนเก่าจะไหลไป COGS ในขณะที่ต้นทุนใหม่ยังคงอยู่ในสินค้าคงเหลือปลายงวด
- **Weighted Average Cost (WAC)**: สมมติฐาน cost-flow ที่การรับเข้าทุกครั้งถูกผสมเป็นต้นทุนต่อหน่วยเฉลี่ยเคลื่อนที่เดียว ค่าเฉลี่ยถูกคำนวณใหม่ทุกการรับเข้าด้วย `(prevQty × prevAvg + receivedQty × receivedCost) / (prevQty + receivedQty)` การ issue ถูก cost ที่ค่าเฉลี่ยที่มีอยู่ ณ เวลาการ issue สินค้าคงเหลือปลายงวดและ COGS ทั้งคู่สะท้อนต้นทุนผสมเดียวกัน
- **Lot/Batch**: กลุ่มสต๊อกที่ระบุได้จากการรับเข้าครั้งเดียว มีปริมาณ วันที่รับ และต้นทุนต่อหน่วยของตัวเอง จำเป็นสำหรับ FIFO (เอนจินใช้ lot ตามลำดับการรับ) และใช้แยกต่างหากสำหรับการติดตามวันหมดอายุและ traceability ของสินค้า
- **Cost Basis**: ต้นทุนต่อหน่วยที่เอนจินกำหนดให้ยอดคงเหลือเพื่อการตีมูลค่าและ costing ปลายน้ำ ภายใต้ FIFO เป็น per-lot; ภายใต้ WAC เป็นค่าเฉลี่ยเคลื่อนที่ปัจจุบันสำหรับสินค้าที่สถานที่ การปรับ การคืน หรือการบริโภคใน recipe ทุกอย่างต้องการ cost basis จากโมดูลนี้ — เอนจินคือแหล่งความจริงเดียวสำหรับ "หน่วยนี้ราคาเท่าไหร่?"

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Finance | เป็นเจ้าของนโยบายการตีมูลค่า: เลือก FIFO หรือ WAC ต่อหมวดสินค้า กระทบยอด sub-ledger inventory กับ GL เซ็นรับรองการตีมูลค่าปลายงวด |
| Inventory Controller | ทำให้ input ที่เอนจินพึ่งพาสะอาด: lot dates, ต้นทุนรับเข้า, cost basis ของการปรับ waste write-off ตรวจสอบ valuation variance |
| Auditor | ตรวจสอบว่า COGS ที่ cost แล้วและสินค้าคงเหลือปลายงวด tie กลับไปยังการรับเข้าต้นทาง และวิธี costing ถูกใช้อย่างสม่ำเสมอข้ามงวด |

## 5. โมดูลที่เกี่ยวข้อง

**Cross-module flow:**
- [[inventory]] — costing ทำงานบนการเคลื่อนไหวของสินค้าคงคลัง; ทุก IN/OUT จุดชนวนการคำนวณ costing
- [[good-receive-note]] — การรับ GRN ตั้งต้นทุนต่อหน่วย (FIFO) หรืออัปเดตค่าเฉลี่ย (WAC)
- [[recipe]] — การบริโภคใน recipe ใช้ปริมาณที่ cost แล้วเพื่อคำนวณ food cost
- [[inventory-adjustment]] — การปรับต้องการ cost basis จากเอนจิน costing

**การตั้งค่าหลัก:**
- [[master-data/business-unit]] — ขอบเขต tenant/property สำหรับ ledger การตีมูลค่า
- [[master-data/currency]] — สกุลเงินทำรายการและสกุลเงินฐาน รวมถึงอัตรา FX สำหรับ COGS ที่ dual-post
- [[master-data/unit]] — การแปลงหน่วยฐานที่จำเป็นสำหรับการตีมูลค่าบรรทัดที่ cost ใด ๆ
- [[system-config/period]] — งวดบัญชีที่ควบคุมการ post costing และล็อกการตีมูลค่า
- [[reporting-audit/activity]] — บันทึกกิจกรรมการคำนวณใหม่และการ post costing เพื่อ audit

## 6. แหล่งข้อมูลอ้างอิง

- Concepts: `../carmen/docs/costing/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — แบบจำลองข้อมูล](./01-data-model.md) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [02 — กฎทางธุรกิจ](./02-business-rules.md) — การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูล
- [03 — User Flow](./03-user-flow.md) — วงจรชีวิตของเอกสารและสารบัญ persona
  - [Finance](./03-user-flow-finance.md)
  - [Inventory Controller](./03-user-flow-inventory-controller.md)
  - [Auditor](./03-user-flow-auditor.md)
- [04 — Test Scenarios](./04-test-scenarios.md) — ขอบเขตของแต่ละ persona, scenario ข้าม persona และ mapping ไปยัง E2E
  - [Finance](./04-test-scenarios-finance.md)
  - [Inventory Controller](./04-test-scenarios-inventory-controller.md)
  - [Auditor](./04-test-scenarios-auditor.md)
- [วิธีคำนวณต้นทุนสินค้าคงคลัง: FIFO vs. Weighted Average](./calculation-methods.md) — เปรียบเทียบวิธีและอัลกอริทึม
