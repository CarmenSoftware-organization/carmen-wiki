---
title: การคำนวณต้นทุน (Costing)
description: วิธีตีมูลค่าสินค้าคงคลัง (FIFO, Weighted Average) และเอนจินคำนวณต้นทุนสำหรับคิด COGS และมูลค่าสินค้าคงเหลือปลายงวด — ตรวจสอบซ้ำ 2026-09-22 (landed cost, FOC, average ต่อสินค้า, tb_inventory_period)
published: true
date: '2026-09-23T01:30:00.000Z'
tags: costing, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# การคำนวณต้นทุน (Costing)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** เอนจินตีมูลค่าระดับธุรกรรมที่เลือก `cost_per_unit` ให้ทุกการเคลื่อนไหวขาออกและปรับปรุง `average_cost_per_unit` ให้ทุกการเคลื่อนไหวขาเข้า ภายใต้วิธี FIFO-หรือ-Average เดียวที่ตั้งค่า **ต่อ business unit** &nbsp;·&nbsp; **กลุ่มผู้ใช้:** นักพัฒนา/QA ที่ทำงานกับการตีมูลค่าสินค้าคงคลัง — โมดูลนี้ไม่มี persona แยกในแอป มีแต่ permission gate ทั่วไปแบบ `inventory_management.*` &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_inventory_transaction_cost_layer` (ledger การไหลของต้นทุน ตอนนี้มี `extra_cost_amount` แล้ว), `tb_inventory_period_snapshot` (เปลี่ยนชื่อจาก `tb_period_snapshot` เมื่อ 2026-09-16; เฉพาะงวดที่ใช้วิธี average), `tb_business_unit.calculation_method`, [costing/calculation-methods](/th/inventory/costing/calculation-methods) &nbsp;·&nbsp; **หน้าย่อย:** 11
> **ตรวจสอบซ้ำ 2026-09-22** กับ `carmen-turborepo-backend-v2` HEAD สิ่งที่เปลี่ยนตั้งแต่ 2026-07-29: extra cost ถูกจัดสรรเข้า landed cost (`20260910130000_add_cost_layer_extra_cost`); ปริมาณ FOC เข้าสต๊อก; business unit แบบ average โพสต์การเคลื่อนไหวของ GRN ตอน **save** (FIFO ตอน commit); `tb_period*` → `tb_inventory_period*`; หมายเลข lot เป็น `<location_code><YYMM><run>`; มีโมดูล GL แล้วแต่ยังไม่เชื่อมกับ inventory (ดู §1)

## 1. ภาพรวม

โมดูล Costing คือเอนจินตีมูลค่าของระบบ ERP สินค้าคงคลัง โดยใช้ข้อมูลธุรกรรมการเคลื่อนไหวสต๊อกที่ผลิตจากโมดูล Inventory และสำหรับธุรกรรมขาออกทุกครั้ง จะเลือก **ต้นทุนขาย (Cost of Goods Sold — COGS)** ที่จะใช้ ส่วนสำหรับธุรกรรมขาเข้าทุกครั้ง จะเขียน cost basis ของสต๊อกใหม่และ (ภายใต้ Weighted Average) ปรับปรุงค่าเฉลี่ยเคลื่อนที่ เอนจินทำงานแบบ per-transaction ไม่ใช่แบบ batch ตามคาบเวลา — แถว cost-layer ขาเข้าของ GRN ถูกเขียนภายใน database transaction เดียวกันกับการเปลี่ยนสถานะ GRN ที่โพสต์มัน: **commit** บน business unit แบบ FIFO, **save** บน business unit แบบ average (`GoodReceivedNoteLogic.save()` / `commit()` → `postGrnLedger()` → `InventoryTransactionService.createFromGoodReceivedNote()`, `inventory-transaction.service.ts:841-1250`) เพื่อให้ยอดคงเหลือและการตีมูลค่ายังคงสอดคล้องกับปริมาณ ต้นทุนขาเข้าที่เอนจินได้รับคือ **landed cost**: `(base_net_amount + extra cost ที่จัดสรร) / (received_base_qty + foc_base_qty)` ปัดเป็น **2 ตำแหน่ง** (`stockQtyOf` / `stockCostOf`, `:73-92`; `Math.round(x × 100) / 100`, `:941,1134`)

รองรับสมมติฐาน cost-flow สองแบบ: **FIFO** ซึ่งเก็บการรับเข้าแต่ละครั้งเป็น lot แยก (`tb_inventory_transaction_cost_layer` เรียงตาม `lot_seq_no`) และใช้ lot เก่าที่สุดก่อน และ **Weighted Average Cost (WAC)** ซึ่งผสมการรับเข้าทุกครั้งเป็นค่าเฉลี่ยเคลื่อนที่เดียว (`average_cost_per_unit`) **แก้ไข 2026-09-22:** ค่าเฉลี่ยถูกรักษา **ต่อสินค้าข้ามทุก location ของ business unit** — `getNetTotals(tx, productId)` (`:1487-1509`) รวมสุทธิทุก layer ที่ยังมีชีวิตของสินค้านั้นโดยไม่สน `location_id` และค่าเฉลี่ยใหม่ถูกประทับลงทุก layer แบบ non-direct ของสินค้า (`:1236-1247`); location มีบทบาทเฉพาะในการตรวจ on-hand (`getLocationBalance`) วิธีนี้ **ไม่สามารถ** ตั้งค่าต่อสินค้าหรือต่อหมวดได้ — เป็นค่าเดียวบน `tb_business_unit.calculation_method` (platform schema, `average` | `fifo`, default `average`) ที่ใช้กับทุกสินค้าใน business unit นั้น `InventoryTransactionService.getCalculationMethod(bu_code)` (`:402-408`) อ่านค่านี้ครั้งเดียวและใช้อย่างสม่ำเสมอ ไม่มี code path ที่ผสม FIFO กับ Average ภายใน business unit เดียว และไม่มีหน้าจอในแอปสำหรับเปลี่ยนค่านี้ — เป็นฟิลด์ระดับ platform/cluster-admin บน business unit ที่อยู่นอก route ของโมดูลนี้เอง ดู [01-data-model](/th/inventory/costing/01-data-model) § 5 สำหรับความแตกต่างฉบับเต็มจากกรอบคิดแบบต่อสินค้าเดิม

Output ลงที่สองที่: ตัวแถว cost-layer เองพก `cost_per_unit` / `average_cost_per_unit` ที่เลือกไว้ (และตั้งแต่ 2026-09-10 ยังพกส่วนแบ่ง `extra_cost_amount` ของ `total_cost`) ให้ผู้บริโภคปลายน้ำทุกรายอ่าน; และตอนปิดงวด `tb_inventory_period_snapshot` จะล็อกคอลัมน์ opening/receipt/issue/adjustment/closing cost ของงวด — **เฉพาะเมื่อ business unit ใช้วิธี `average`** เท่านั้น (`period-end.close-average.helper.ts:480`) เส้นทางปิดงวดแบบ FIFO จะนำยอดคงเหลือไปต่อเป็นแถว `close_period`/`open_period` บน cost-layer แทน และไม่เขียน snapshot เลย (`period-end.close-transaction.helper.ts`) **การโพสต์ GL — สถานะที่แม่นยำ 2026-09-22:** ตอนนี้มีโมดูล general ledger แล้ว (`apps/micro-business/src/gl/`; `GlPostingService.post()` ที่ `gl-posting.service.ts:293` โพสต์ `tb_gl_jv` ลง `tb_gl_balance`) แต่ไม่มีส่วนใดใน `inventory-transaction.service.ts`, `good-received-note.*.ts` หรือ `period-end.*.ts` ที่ import หรือเรียกมัน; ผู้เขียน JV มีเพียงโมดูล JV เอง (`gl-jv.service.ts:214`, source `manual`), การรัน template (`gl-jv-template.service.ts:786`) และ voucher แบบ reversal / closing ของ posting service (`gl-posting.service.ts:571,909,1116`); `enum_gl_jv_source.inventory` (`schema.prisma:4733`) ไม่มีผู้เขียน **ไม่มีการเคลื่อนไหวสินค้าคงคลัง, GRN หรือการปิดงวดใดโพสต์เข้า GL ledger ในวันนี้** — ไม่มี `Dr`/`Cr` ไม่มี GL control account ไม่มี reconciliation ระหว่าง inventory กับ GL อัลกอริทึม FIFO vs WAC อย่างละเอียด ตัวอย่างตัวเลข และ trade-off ระหว่างสองวิธี อยู่ในหน้าย่อยด้านล่าง — หน้านี้เป็นเพียงจุดเริ่มต้น

## 2. บริบททางธุรกิจ

การตีมูลค่าสินค้าคงคลังเป็นกิจกรรมที่มีกฎควบคุม ทั้ง **IFRS** (IAS 2) และ **US GAAP** (ASC 330) ยอมรับ FIFO และ Weighted Average เป็นสมมติฐาน cost-flow ที่ใช้ได้ แต่ต้องเลือกใช้อย่างสม่ำเสมอต่อหมวดสินค้าและเปิดเผยในงบการเงิน ดังนั้นโมดูล costing จึงเป็นองค์ประกอบที่หันหน้าเข้าหา audit: ตัวเลข COGS ทุกตัวต้อง trace กลับไปยังการรับเข้าครั้งใดครั้งหนึ่ง (FIFO) หรือการคำนวณค่าเฉลี่ยเคลื่อนที่ครั้งใดครั้งหนึ่ง (WAC) และ trail ต้องอยู่ผ่านวัฏจักรการตรวจสอบภายนอกได้

เชิงปฏิบัติงาน costing คือที่ที่ **food cost control** อยู่ Plate cost, recipe profitability, และการตัดสินใจ menu-engineering ทั้งหมดอ่านจากโมดูลนี้ ถ้าเอนจิน costing เลื่อน — lot เก่าค้าง waste write-off ตกหล่น การคำนวณค่าเฉลี่ยใหม่ผิดหลังการคืน — ทุกตัวเลข margin ปลายน้ำก็จะเลื่อนตาม กลุ่มโรงแรมมักดำเนินงานบน margin ค่าอาหารที่บางมาก ดังนั้นความผิดพลาดในการตีมูลค่าหนึ่งหรือสองจุดเปอร์เซ็นต์จะแปลตรงเป็น P&L miss ที่สังเกตเห็นได้ โมดูลนี้คือสัญญาระหว่างการเคลื่อนไหวสต๊อกทางกายภาพและภาพการเงินที่ธุรกิจใช้ในการขับเคลื่อน

## 3. แนวคิดสำคัญ

- **COGS (Cost of Goods Sold)**: ต้นทุนที่เลือกเมื่อสินค้าออกจากสถานที่ประเภท inventory เพื่อบริโภค (issue ไปครัว, write-off, ขายผ่าน POS-linked recipe) เขียนโดยเอนจิน costing ลงบนแถว `tb_inventory_transaction_cost_layer` ขาออก ณ ตอนเกิดการเคลื่อนไหว ไม่มีการเคลื่อนไหวสินค้าคงคลังใดถูกโพสต์เข้า GL (โมดูล GL มีอยู่แต่ไม่ถูกเรียกจากโค้ด inventory) — ตัวแถว cost-layer เองคือบันทึกถาวรเพียงอย่างเดียวของต้นทุนการเคลื่อนไหวนั้น
- **มูลค่าสินค้าคงเหลือปลายงวด (Ending Inventory Value)**: มูลค่าเงินของสต๊อกที่มีอยู่ ณ จุดเวลาใดเวลาหนึ่ง — ปริมาณคูณต้นทุนต่อหน่วยตามวิธี costing ที่ใช้งานอยู่ บน business unit ที่ใช้ **วิธี average** ค่านี้จะถูกล็อกเข้า `tb_inventory_period_snapshot` ตอนปิดงวด; บน business unit ที่ใช้ **วิธี FIFO** ค่านี้คำนวณจาก lot คงเหลือบน cost-layer ที่ถูกนำไปต่อเป็นแถว `open_period` (ไม่มีการเขียนแถว snapshot)
- **FIFO (First-In, First-Out)**: สมมติฐาน cost-flow ที่การรับเข้าเก่าที่สุดถูกใช้ก่อน การรับเข้าแต่ละครั้งกลายเป็น **lot** แยกที่มีต้นทุนต่อหน่วยของตัวเอง เอนจินใช้ lot ตามลำดับจนกระทั่งปริมาณที่ issue ได้รับการตอบสนอง ดังนั้นต้นทุนเก่าจะไหลไป COGS ในขณะที่ต้นทุนใหม่ยังคงอยู่ในสินค้าคงเหลือปลายงวด ภายใต้ FIFO layer ของการรับเข้าใหม่ถูกเขียนด้วย `average_cost_per_unit = 0` (`inventory-transaction.service.ts:998`) — ไม่มี "shadow average" ที่รักษาไว้บนการรับ GRN
- **Weighted Average Cost (WAC)**: สมมติฐาน cost-flow ที่การรับเข้าทุกครั้งถูกผสมเป็นต้นทุนต่อหน่วยเฉลี่ยเคลื่อนที่เดียว **ต่อสินค้า** (ทุก location) ค่าเฉลี่ยถูกคำนวณใหม่ทุกการรับเข้าด้วย `Round2((Σ ต้นทุนสุทธิของ layer ที่ยังมีชีวิต + total cost ใหม่) / (Σ ปริมาณสุทธิของ layer ที่ยังมีชีวิต + qty ใหม่))` (`calculateNewAverageCost`, `common/helpers/inventory-cost.formula.ts:90-101`; `getNetTotals` รวมสุทธิ `in_qty − out_qty` ของแต่ละ layer ที่ `cost_per_unit` ของ layer นั้น) การ issue ถูก cost ที่ค่าเฉลี่ยที่มีอยู่ ณ เวลาการ issue; ค่าเดียวกันถูกประทับซ้ำลงทุก layer ที่ยังมีชีวิตของสินค้า เพื่อให้รายงานอ่านได้โดยไม่ต้องคำนวณใหม่
- **Landed cost**: มูลค่าที่เอนจินใช้ตีการรับเข้า — `base_net_amount` ของบรรทัดบวกส่วนแบ่ง extra cost ของ GRN (`allocateExtraCost`, `good-received-note.extra-cost.ts`: `by_qty` = แบ่งเท่ากันต่อบรรทัด, `by_value` = ถ่วงน้ำหนักตามปริมาณสต๊อก, `manual` = ไม่จัดสรร) หารด้วย `received_base_qty + foc_base_qty` ส่วนแบ่ง extra cost ถูกเก็บถาวรต่อ layer เป็น `extra_cost_amount`
- **Lot/Batch**: กลุ่มสต๊อกที่ระบุได้จากการรับเข้าครั้งเดียว มีปริมาณ วันที่รับ และต้นทุนต่อหน่วยของตัวเอง หมายเลข lot คือ `<location_code><YYMM><ลำดับ 4 หลัก>` (`common/helpers/lot-number.helper.ts`) โดยเลขลำดับคือ `lot_seq_no` ซึ่งเริ่มนับใหม่ที่ 1 ทุกงวดสินค้าคงคลัง จำเป็นสำหรับ FIFO (เอนจินใช้ lot ตามลำดับการรับ) และใช้แยกต่างหากสำหรับ traceability ของสินค้า (แถว ledger ชี้กลับไปยังเหตุการณ์รับของ GRN ผ่าน `good_received_note_detail_item_id`)
- **Cost Basis**: ต้นทุนต่อหน่วยที่เอนจินกำหนดให้ยอดคงเหลือเพื่อการตีมูลค่าและ costing ปลายน้ำ ภายใต้ FIFO เป็น per-lot; ภายใต้ WAC เป็นค่าเฉลี่ยเคลื่อนที่ปัจจุบันสำหรับสินค้าที่สถานที่ การปรับ การคืน หรือการบริโภคใน recipe ทุกอย่างต้องการ cost basis จากโมดูลนี้ — เอนจินคือแหล่งความจริงเดียวสำหรับ "หน่วยนี้ราคาเท่าไหร่?"

## 4. บทบาทและ Persona

**แก้ไข (ยืนยันแล้ว 2026-07-22, ตรวจซ้ำ 2026-09-22):** ฉบับร่างก่อนหน้าของโมดูลนี้เอกสาร RBAC persona แยกกันสามแบบ (Finance, Inventory Controller, Auditor) พร้อม approval queue เฉพาะ, valuation-policy console, sub-ledger ↔ GL reconciliation dashboard, และ read-only audit workspace ไม่มีสิ่งใดในนั้นมีอยู่จริงในผลิตภัณฑ์ ตัวเอนจินเองไม่มีหน้าจอที่ถูก gate ด้วย persona เลย — มันเป็น service ที่ถูกเรียกจาก GRN commit (หรือ save บน BU แบบ average), store-requisition issue, inventory-adjustment commit, credit-note, และ period-end หน้าจอในแอปที่มีจริงมีเพียงสองหน้าจอ period-end ทั่วไป (gate ด้วย `inventory_management.period_end.view` / `.execute` ไม่ใช่ด้วยชื่อ role) ตามที่เอกสารไว้ที่ [inventory/period-end](/th/inventory/inventory/period-end); `enum_stage_role` (enum role เดียวใน tenant schema) คือ `{create, approve, purchase, issue, view_only}` — ไม่มีสมาชิก `finance` หรือ `auditor` **อัปเดต 2026-09-22:** โมดูล inventory-adjustment ตอนนี้มีสถานะ `draft` แล้ว — `StockInService.create()` เขียน `doc_status = draft` (`stock-in.service.ts:418`) และมีเพียง `PATCH …/stock-ins/:id/commit` (`:471-575`) ที่โพสต์เข้า ledger และตั้งเป็น `completed` — แต่ยังคงไม่มี approval queue หรือ preview การเลือกต้นทุน: ผู้ใช้คนเดียวกับที่สร้าง draft เป็นคน commit เอง

| ใคร (ความสนใจตามหน้าที่ ไม่ใช่หน้าจอหรือ RBAC role แยก) | สิ่งที่พวกเขาสนใจ |
|------|----------------|
| ผู้ถือ permission `inventory_management.period_end.execute` | รันการปิดงวดตามที่เอกสารไว้ที่ [inventory/period-end](/th/inventory/inventory/period-end); บน business unit ที่ใช้วิธี average การกระทำนี้จะจุดชนวนการเขียน `tb_inventory_period_snapshot` |
| ผู้สร้าง GRN, store requisition, inventory adjustment, หรือ credit note | ฟิลด์ต้นทุนในเอกสารของพวกเขาคือสิ่งที่เอนจินเลือกหรือเขียนโดยตรง — ดู [good-receive-note](/th/inventory/good-receive-note), [store-requisition](/th/inventory/store-requisition), [inventory-adjustment](/th/inventory/inventory-adjustment) |
| Purchaser / receiver ที่ต้องการดู "ครั้งก่อนเราจ่ายเท่าไหร่" | endpoint ต้นทุนแบบอ่านอย่างเดียวบน gateway controller `application/cost`: `GET /api/:bu_code/cost/products/:product_id/last-cost` (ต้นทุน GRN **หรือ** stock-in ล่าสุด), `…/last-receiving` (GRN ล่าสุด), `…/last-receiving/unit/:unit_id` (ราคา GRN ล่าสุดต่อหน่วยที่รับ, `cost_per_unit = net_amount / received_qty`), `…/location/:location_id/qty/:qty` (ประมาณการต้นทุน) — guard `product.last-cost`, `product.last-receiving`, `product.last-receiving-by-unit`, `product.cost-estimate`; Bruno `_uncategorized/cost/` |
| Platform/cluster admin | ตั้งค่า `tb_business_unit.calculation_method` ตอนสร้าง business unit — อยู่นอก route ของ wiki module นี้ |

## 5. โมดูลที่เกี่ยวข้อง

**Cross-module flow:**
- [inventory](/th/inventory/inventory) — costing ทำงานบนการเคลื่อนไหวของสินค้าคงคลัง; ทุก IN/OUT จุดชนวนการคำนวณ costing
- [good-receive-note](/th/inventory/good-receive-note) — การรับ GRN ตั้ง landed unit cost (lot แบบ FIFO) หรืออัปเดตค่าเฉลี่ยของสินค้า (WAC); โพสต์ตอน commit บน BU แบบ FIFO และตั้งแต่ตอน save บน BU แบบ average; รวม extra cost และ FOC
- [recipe](/th/inventory/recipe) — การบริโภคใน recipe ใช้ปริมาณที่ cost แล้วเพื่อคำนวณ food cost
- [inventory-adjustment](/th/inventory/inventory-adjustment) — การปรับต้องการ cost basis จากเอนจิน costing

**การตั้งค่าหลัก:**
- [master-data/business-unit](/th/inventory/master-data/business-unit) — ขอบเขต tenant/property สำหรับ ledger การตีมูลค่า
- [master-data/currency](/th/inventory/master-data/currency) — สกุลเงินทำรายการและสกุลเงินฐาน รวมถึงอัตรา FX; **ยืนยันแล้ว 2026-09-22:** ledger เก็บ **สกุลเงินฐานเท่านั้น** — GRN ป้อน `base_net_amount` และแปลงส่วนแบ่ง extra cost ด้วย `calcBase(share, exchange_rate)` (`good-received-note.ledger.ts:131`); ไม่มีการเก็บอัตรา FX ต่อ layer
- [master-data/unit](/th/inventory/master-data/unit) — การแปลงหน่วยฐานที่จำเป็นสำหรับการตีมูลค่าบรรทัดที่ cost ใด ๆ
- [system-config/period](/th/inventory/system-config/period) — งวดสินค้าคงคลัง (`tb_inventory_period`, HTTP `/inventory-periods`, permission `system_admin.inventory_period`) ที่ควบคุมการ post costing (งวดของ GRN ถูก resolve จาก `grn_date` ตามช่วงวันที่ เฉพาะสถานะ `open` หรือ `locked` เท่านั้น) และล็อกการตีมูลค่า
- [system-config](/th/inventory/system-config) cost centre — `tb_cost_center`, `tb_cost_center_group`, `tb_cost_center_account` (`20260904103000_add_cost_center`) **ไม่ได้เชื่อมกับ costing**: ไม่มีตาราง inventory ใดพก `cost_center_id` (FK เดียวคือ `tb_gl_jv_detail.cost_center_id`); แถว inventory พกเพียง JSON `dimension` แบบอิสระเท่านั้น
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — บันทึกกิจกรรมการคำนวณใหม่และการ post costing เพื่อ audit

## 6. แหล่งข้อมูลอ้างอิง

- Concepts: `../carmen/docs/costing/enhanced-costing-engine.md` (หยุดอัปเดตตั้งแต่ 2026-04-27 — เป็น recipe/portion costing ไม่ใช่เอนจิน inventory)
- Frontend: `../carmen-inventory-frontend-react/` — ไม่มีหน้าจอ costing; `routes/accounting/` เป็น mock data
- Backend: `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/inventory-transaction/inventory-transaction.service.ts` (เอนจิน), `apps/micro-business/src/common/helpers/{inventory-cost.formula,fifo-cost-split.helper,lot-number.helper}.ts`, `apps/micro-business/src/inventory/good-received-note/good-received-note.{ledger,extra-cost}.ts` (ขาเข้า), `apps/micro-business/src/inventory/period-end/` (ปิดงวด), `apps/micro-business/src/inventory/costing/` (endpoint อ่านต้นทุน), gateway `apps/backend-gateway/src/application/cost/`
- API contracts: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/cost/` (4 request)
- E2E tests: `../carmen-inventory-frontend-e2e/` — ไม่มี spec เฉพาะ costing (ดู [04-test-scenarios](/th/inventory/costing/04-test-scenarios) § 4)

## 7. หน้าในโมดูลนี้

- [01 — แบบจำลองข้อมูล](/th/inventory/costing/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [02 — กฎทางธุรกิจ](/th/inventory/costing/02-business-rules) — การตรวจสอบ การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูล
- [03 — User Flow](/th/inventory/costing/03-user-flow) — วงจรชีวิต cost-flow; ไม่มี persona แยกจริง (ดูหน้าแก้ไขด้านล่าง)
  - [Finance (แก้ไข)](/th/inventory/costing/03-user-flow-finance)
  - [Inventory Controller (แก้ไข)](/th/inventory/costing/03-user-flow-inventory-controller)
  - [Auditor (แก้ไข)](/th/inventory/costing/03-user-flow-auditor)
- [04 — Test Scenarios](/th/inventory/costing/04-test-scenarios) — 11 scenario ระดับ engine ที่ตัดข้าม + mapping ไปยัง E2E
  - [Finance (แก้ไข)](/th/inventory/costing/04-test-scenarios-finance)
  - [Inventory Controller (แก้ไข)](/th/inventory/costing/04-test-scenarios-inventory-controller)
  - [Auditor (แก้ไข)](/th/inventory/costing/04-test-scenarios-auditor)
- [วิธีคำนวณต้นทุนสินค้าคงคลัง: FIFO vs. Weighted Average](/th/inventory/costing/calculation-methods) — เปรียบเทียบวิธีและอัลกอริทึม
