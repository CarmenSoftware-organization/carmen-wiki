---
title: คลังสินค้า — User Flow — Store Keeper (Inventory — User Flow — Store Keeper)
description: Flow ของ Store Keeper ในโมดูล inventory — การเคลื่อนไหวสต๊อกประจำวัน เอกสาร stock-in / stock-out การดำเนินการนับสต๊อก
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory, user-flow, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า — User Flow — Store Keeper (Inventory — User Flow — Store Keeper)

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **โมดูล:** [[inventory]] &nbsp;·&nbsp; **ขั้นตอน workflow:** เริ่ม draft ของ manual stock-in / stock-out &nbsp;·&nbsp; auto-post ต่ำกว่า threshold (transaction post ตรงเข้า `tb_inventory_transaction`) &nbsp;·&nbsp; route เอกสารเหนือ threshold ไปที่ Controller &nbsp;·&nbsp; ดำเนินการนับสต๊อกบน location ที่อยู่ใน scope &nbsp;·&nbsp; **สิทธิ์สำคัญ:** เริ่ม / post ต่ำกว่า threshold; แก้ไข cost-layer ledger ไม่ได้; SoD (`INV_AUTH_010`) จำกัด write-off ของ lot ที่ตนรับเองเหนือ threshold
> **สิ่งที่ persona นี้ทำ:** บันทึก movement ประจำวันที่ระดับ floor / location และส่งเอกสารเหนือ threshold ออกเพื่อขออนุมัติจาก Controller

## 1. บทบาทในโมดูลนี้

Persona **Store Keeper** คือผู้ปฏิบัติงานที่ระดับ floor / location — ผู้ใช้ที่มือสัมผัสกับสต๊อกจริง ๆ ภายในโมดูล inventory สิทธิ์ของพวกเขาถูก **จำกัด**: สามารถ **เริ่ม** movement ปกติใด ๆ (manual stock-in สำหรับ found stock / count overage / vendor-replaced damaged stock, manual stock-out สำหรับ breakage / expiry write-off / count shortage, การดำเนินการนับสต๊อกบน location ที่มี `tb_user_location` mapping) และสามารถ **post** movement ต่ำกว่า threshold ของ Inventory Controller ที่ตั้งค่าโดย tenant แต่ทุก adjustment เหนือ threshold route ขึ้นเพื่อขออนุมัติ Store Keeper **ไม่** แก้ไข cost-layer ledger ของ inventory ตรง ๆ **ไม่** ตั้งค่า location type / costing method / adjustment-type reason code **ไม่** อนุมัติ adjustment ของ Store Keeper คนอื่น และ **ไม่** มีส่วนร่วมในการปิดงวด ความเป็นเจ้าของในโมดูล inventory ของพวกเขาจบเมื่อ (a) เอกสาร source (`tb_stock_in` / `tb_stock_out` / `tb_count_stock`) ออกจากมือพวกเขาไปยัง Inventory Controller เพื่อ review, (b) เอกสาร source ถูก auto-approve ต่ำกว่า threshold และ post ตรงเข้า `tb_inventory_transaction` หรือ (c) GRN receipt ปกติที่ dock post ผ่านเข้า inventory (รายละเอียดฝั่ง GRN เป็นเจ้าของโดย [[good-receive-note]] Receiver persona; ที่นี่ Store Keeper เป็นผู้ปฏิบัติทางกายภาพเดียวกัน แต่ความกังวลฝั่ง inventory เพียง "movement ถูกที่หรือเปล่า") Segregation of duties (`INV_AUTH_010`) จำกัด write-off ขนาดใหญ่ของสต๊อกจาก lot ที่ Store Keeper คนเดียวกันรับมาก่อน; สำหรับเหล่านั้น ต้องใช้ adjuster อิสระ (Inventory Controller หรือ Store Keeper คนอื่น)

## 2. จุดเข้าและ Flow หลัก

**จุดเข้า:** สามเส้นทางเข้าสู่งานประจำวันด้าน inventory ของ Store Keeper บวกที่สี่โดยปริยาย (GRN receipt) ซึ่งอาศัยอยู่ในไฟล์ persona ของ GRN

- **Inventory module → Stock-In** — manual inbound สำหรับเหตุผลที่ไม่ใช่ GRN (found stock, count overage, recall replacement, vendor-supplied free-replacement ที่ข้าม GRN) สร้างเอกสาร `tb_stock_in` ที่ `doc_status = draft`
- **Inventory module → Stock-Out** — manual outbound สำหรับเหตุผลที่ไม่ใช่ issue (breakage / damage write-off, expired-stock disposal, count shortage, recall write-off) สร้างเอกสาร `tb_stock_out` ที่ `doc_status = draft`
- **Physical-count module → Run count** — กวาด location ที่กำหนดสำหรับ window การนับที่ตั้งเวลาไว้; ผลของการนับ stage variance lines ที่เมื่ออนุมัติ post เป็น `tb_stock_in` (overage) หรือ `tb_stock_out` (shortage) ตาม `INV_XMOD_003`
- *(โดยปริยาย)* **GRN receipt ที่ dock** — Store Keeper อาจเป็น Receiver ฝั่ง GRN ด้วย; ผล inventory (การเขียน cost-layer ที่ `(location, product, new_lot)`) fire ที่ GRN commit ตาม `INV_XMOD_001` งานเชิงสัมผัสด้าน inventory ของ Store Keeper ในเส้นทางนี้คือเรื่องการป้อน lot number และการ resolve accepted-qty; flow เต็มอาศัยอยู่ในไฟล์ Receiver persona ของ [[good-receive-note]] หน้านี้อ้างอิงแต่ไม่ทำซ้ำ

**Flow หลัก (stock-in สำหรับ found stock / count overage, 8 ขั้นตอน — เป็นตัวแทนของรูปแบบ manual-adjustment):**

1. **ระบุความคลาดเคลื่อน** ระหว่างการตรวจสอบ bin-stock ปกติ การ count run หรือการส่งมอบ vendor-replacement Store Keeper เห็นสต๊อกจริงบนชั้นมากกว่าที่ระบบแสดง (หรือพบสต๊อกที่เคยคิดว่าหายไปก่อนหน้านี้) พวกเขายืนยันความคลาดเคลื่อนโดยการนับใหม่และโดยการตรวจ lot label
2. **เปิดหน้าจอ Stock-In** Inventory module → Stock-In → New หน้าจอสร้าง `tb_stock_in` ที่ `doc_status = draft` โดย Store Keeper เป็น `created_by_id` และ location ที่กำหนดถูก pre-fill จาก primary `tb_user_location` mapping ของ user (override ไปยัง location อื่นที่ user มี scope ได้)
3. **เลือกเหตุผลการ adjustment** บังคับ: `adjustment_type_id` อ้างอิง `tb_adjustment_type` — reason code ทั่วไปสำหรับ inbound คือ `FOUND_STOCK`, `COUNT_OVERAGE`, `RECALL_REPLACEMENT`, `VENDOR_FREE_REPLACEMENT`, `DATA_FIX` Reason code ขับการจำแนกปลายน้ำใน GL และในการรายงานผลการดำเนินงานของ vendor
4. **เพิ่ม lines** ต่อสินค้า: `product_id`, `qty` (บวก), `lot_no` ของ lot (lot ที่มีอยู่ถ้าสต๊อกตรงกับ lot label ที่รู้จัก; lot ใหม่ถ้า found stock ไม่มีบันทึกก่อนหน้า), `cost_per_unit` (ต้องตรงกับต้นทุน lot ของ receipt ดั้งเดิมถ้า `lot_no` มีอยู่; user-entered พร้อม gate การอนุมัติของ Controller ถ้า `lot_no` ใหม่และต้นทุนไม่เป็นศูนย์) สำหรับสินค้าเน่าเสียง่าย expiry date จำเป็นบน lot ใหม่
5. **ตรวจสอบต้นทุน** หน้าจอ render `tb_inventory_transaction_cost_layer.cost_per_unit` ล่าสุดสำหรับ lot (ถ้ามีอยู่) — รายการต้องตรงภายใน tolerance ของ tenant; ต้นทุนไม่ตรง flag สำหรับ Controller review ตาม `INV_AUTH_003` สำหรับ found stock lot ใหม่ ต้นทุนต้องสามารถปกป้องได้ — โดยทั่วไปอ่านจาก `[[vendor-pricelist]]` last-price หรือกำหนดเป็นศูนย์พร้อมหมายเหตุอธิบาย
6. **Submit เพื่ออนุมัติ** คลิก **Submit** — เอกสาร source transition `draft → in_progress` ตาม `enum_doc_status` บน `tb_stock_in` ถ้า `qty × cost_per_unit` รวม **ต่ำกว่า** auto-approve threshold ของ Store Keeper เอกสาร auto-advance และ post ไปยัง inventory ทันที (ข้ามไปที่ขั้นตอนที่ 8) ถ้า **เหนือ** threshold เอกสาร route ไปยัง queue ของ Inventory Controller ตาม `INV_XMOD_005`
7. **Inventory Controller review และอนุมัติ** (หรือ reject พร้อม comment) บนการอนุมัติของ Controller เอกสาร post ไปยัง inventory (`tb_stock_in.doc_status = completed`); บนการ reject เอกสารกลับไปที่ `draft` พร้อม comment ของ Controller ใน activity log — Store Keeper แก้ไขและ re-submit หรือ void เอกสารถ้าความคลาดเคลื่อนเป็นข้อผิดพลาดการนับฝั่ง Store Keeper
8. **Post fire** ระบบเขียน `tb_inventory_transaction` (`inventory_doc_type = stock_in`, `inventory_doc_no = tb_stock_in.id`), `tb_inventory_transaction_detail` (`qty > 0`) และ `tb_inventory_transaction_cost_layer` (`in_qty > 0`, `transaction_type = adjustment_in`, `cost_per_unit` จาก line, `lot_no` และ `lot_index` ตามกฎ inbound, `at_period` และ `period_id` populate จาก current `open` period) ความเป็นเจ้าของฝั่ง inventory ของ Store Keeper จบที่นี่; on-hand ที่ `(location, product, lot)` ตอนนี้คือค่า derive ใหม่ตาม `INV_CALC_004`

**Flow stock-out** ตามรูปทรงเดียวกันแต่ทิศทางกลับ (line `qty` ลบ, cost-layer `out_qty > 0`, `transaction_type = adjustment_out`) และตามปกติ cost-per-unit **ไม่** ป้อนโดย Store Keeper — มันถูก pick โดย FIFO หรือ weighted-average ตาม costing method ของสินค้าโดย engine post (`INV_CALC_005` / `INV_CALC_006`) Stock-out เหนือ threshold (breakage write-off, expiry write-off) route ไปยัง Inventory Controller; stock-out ขนาดใหญ่มาก (large recall write-off) route Controller → Finance สำหรับการอนุมัติผลกระทบต้นทุน

**Flow physical-count** เป็นเจ้าของโดยไฟล์ persona ของ [[physical-count]] module; การ post ฝั่ง inventory จาก count ผ่าน stock-in (overage) / stock-out (shortage) และตามขั้นตอนที่ 6–8 ของ flow หลักด้านบน

## 3. กิ่งการตัดสินใจ

- **lot ที่มีอยู่ vs lot ใหม่ inbound** เมื่อความคลาดเคลื่อนอยู่บน lot ที่ระบบรู้จักแล้ว (`(location, product, lot_no)` มีอยู่ใน `tb_inventory_transaction_cost_layer`) ป้อน `lot_no` ที่มีอยู่; cost-per-unit อ่านจาก layer ล่าสุดของ lot และไม่สามารถแก้ไขได้โดย Store Keeper เมื่อความคลาดเคลื่อนอยู่บนสต๊อกที่ไม่มีบันทึกในระบบก่อนหน้า (found stock จริง) ป้อน `lot_no` ใหม่และต้นทุนสามารถแก้ไขได้ — แต่รายการ route สำหรับการอนุมัติของ Controller โดยไม่คำนึงถึง threshold เพราะการสร้าง lot ใหม่โดย Store Keeper เป็น event ที่ sensitive
- **ต่ำกว่า vs เหนือ auto-approve threshold** ต่ำกว่า — เอกสาร auto-advance ไปที่ `completed` บน Submit, inventory transaction post ทันที, งาน inventory ของ Store Keeper เสร็จ เหนือ — เอกสาร route ไปยัง queue ของ Inventory Controller ตาม `INV_XMOD_005`; Store Keeper รอ (เอกสารเป็น read-only สำหรับพวกเขาขณะที่อยู่ใน `in_progress`)
- **Stock-out cost-per-unit ไม่ใช่ user-entered** สำหรับ stock-out (write-off / shortage / breakage) Store Keeper ป้อน `qty` เท่านั้น — `cost_per_unit` pick ที่เวลา post โดย costing engine Store Keeper เห็น preview ต้นทุนที่ pick (FIFO จาก lot ที่เก่าที่สุดหรือ weighted-average ปัจจุบัน) ก่อน submit เพื่อให้สามารถ flag ได้ถ้าต้นทุนที่ pick ดูผิดปกติ (เช่น lot ราคาแพงผิดปกติถูกบริโภคสำหรับ write-off ปกติ)
- **การพยายามทำให้ balance ติดลบถูก reject**: เมื่อ stock-out `qty` จะขับ `(location, product, lot)` ต่ำกว่าศูนย์ตาม `INV_VAL_005` เอกสาร **submit ไม่ได้** Store Keeper ลด `qty`, pick lot อื่น หรือ escalate ไปยัง Controller เพื่อ investigate (ความคลาดเคลื่อนอาจบ่งชี้ inbound ที่ขาดที่ไม่ได้บันทึก) กฎ "no negative balance" ของระบบบังคับใช้ที่ submit ไม่ใช่ที่ post
- **Gate ของ location-type**: เอกสาร stock-in และ stock-out ไม่สามารถยกขึ้นต่อ location ที่ `location_type = direct` ตาม `INV_VAL_009` — location direct-cost ไม่ถือ balance ดังนั้นไม่มี "stock" ที่จะปรับ หน้าจอ filter location picker เป็น inventory-type (และ consignment-type ที่ใช้ได้) Store Keeper เห็น tooltip ถ้าพยายามเปลี่ยนไปยัง direct location
- **การรวม multi-line**: เอกสาร stock-in หรือ stock-out เดียวสามารถถือ multiple product lines (ปกติสำหรับ count-variance run — หลายสินค้าด้วย shortage หรือ overage) การตรวจสอบ threshold รวมข้าม lines; เอกสาร multi-line ที่ `Σ qty × cost_per_unit` รวมเกิน threshold route สำหรับการอนุมัติของ Controller แม้แต่ละ line จะต่ำกว่า threshold

## 4. จุดออก / การส่งต่อ

การมีส่วนร่วมของ Store Keeper บน movement inventory ที่กำหนดจบที่หนึ่งในสี่ขอบเขต:

- **Auto-approve post เสร็จสิ้น** Stock-in / stock-out ต่ำกว่า threshold post ทันทีบน submit งาน inventory ของ Store Keeper เสร็จ; ไม่มีการส่งต่อ Activity log บันทึก `{ doc_status: 'completed', action: 'auto_approve_post' }` ถ้า post กระทบ count run เอกสาร count ก้าวหน้าตาม `INV_XMOD_003`
- **การส่งต่อเหนือ threshold ไปยัง Inventory Controller** เอกสารที่ `tb_stock_in.doc_status = in_progress` (หรือ `tb_stock_out.doc_status = in_progress`) route ไปยัง **Inventory Controller** ([03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md)) สำหรับการอนุมัติ Store Keeper re-engage ก็ต่อเมื่อเอกสารถูก reject (กลับไปที่ `draft`) หรือถ้า Controller ขอ supporting evidence เพิ่มเติม (ภาพถ่าย, count-sheet attachment, vendor RMA reference) บน activity log
- **การส่งต่อ count-variance ผ่านเอกสาร count** เมื่อ post ฝั่ง inventory เป็นผลของ physical / spot count ที่ complete สมอของการส่งต่อคือ `tb_count_stock.status = completed` ของเอกสาร count และ variance lines ที่ stage ไว้ การดำเนินการนับของ Store Keeper ป้อนเข้า variance review ของ Inventory Controller ตาม `INV_XMOD_003` และ `INV_XMOD_004`; Controller ตัดสินใจเกี่ยวกับการ post (approve / adjust / re-count) Flow count เต็มอาศัยอยู่ใน [[physical-count]] / [[spot-check]]
- **เอกสารถูก void ก่อน post** ถ้าความคลาดเคลื่อนเป็นข้อผิดพลาดการนับของ Store Keeper ที่จับได้ก่อน submit (หรือโดย Controller บน reject) เอกสาร void — `tb_stock_in.doc_status = voided` (หรือ `tb_stock_out.doc_status = voided`) พร้อม reason text ไม่มี inventory transaction เขียน ไม่มีการเปลี่ยน balance เอกสารที่ voided ยังคงอยู่ใน database สำหรับ audit ตามรูปแบบ soft-delete มาตรฐาน

## 5. แหล่งอ้างอิง

- ภาพรวม Parent: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิต movement-and-period แบบ canonical (Section 2 movement-level transitions + period-level transitions) ที่เส้นทาง persona นี้เดินผ่าน และตารางการส่งต่อข้าม persona ที่ anchor ขอบเขต Store Keeper → Inventory Controller
- Sibling: [03-user-flow-inventory-controller.md](./03-user-flow-inventory-controller.md) — persona ปลายน้ำที่รับเอกสาร stock-in / stock-out เหนือ threshold และ count-variance lines เพื่ออนุมัติ
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — persona ปลายน้ำสำหรับกรณีที่หายากที่ผลกระทบต้นทุนของ write-off ที่ Store Keeper เริ่มเกิน threshold ของ Inventory Controller (large recall write-off, large damage write-off) และ route Controller → Finance
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — System Administrator ที่ตั้งค่ารายการ reason-code `tb_adjustment_type` ที่ Store Keeper เลือก, `tb_user_location` mapping ของ user ที่ scope locations ที่ pick ได้ และ threshold ที่ auto-approve gate เปรียบเทียบ
- Sibling: [01-data-model.md](./01-data-model.md) — รูปทรง canonical ของ `tb_stock_in` / `tb_stock_out` (อ้างอิงในขั้นตอน 2–6 ของ flow หลัก), รูปทรง `tb_inventory_transaction` (ขั้นตอน 8), ค่า `enum_inventory_doc_type` (`stock_in`, `stock_out`), ค่า `enum_transaction_type` (`adjustment_in`, `adjustment_out`)
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎการตรวจสอบ `INV_VAL_002` (product / location จำเป็น), `INV_VAL_003` (location active), `INV_VAL_004` (qty sign), `INV_VAL_005` (no negative balance — อ้างอิงในขั้นตอนที่ 7 ของกิ่งการตัดสินใจ), `INV_VAL_006` (lot identity), `INV_VAL_009` (gate direct-location), และกฎข้ามโมดูล `INV_XMOD_005` (manual adjustment threshold-based approval routing)
- ที่เกี่ยวข้อง: [[good-receive-note]] — Store Keeper เป็นผู้ปฏิบัติทางกายภาพเดียวกันกับ GRN Receiver ที่ dock; ผลฝั่ง inventory ของ GRN commit เป็นเจ้าของในรายละเอียดในไฟล์ Receiver persona ของโมดูล GRN ไม่ใช่ที่นี่
- ที่เกี่ยวข้อง: [[store-requisition]] — Store Keeper ที่ location **issuing** dispatch สต๊อกตาม SR ที่อนุมัติแล้ว; ผลฝั่ง inventory (outbound consumption) เป็นเจ้าของโดยไฟล์ persona ของโมดูล SR หน้านี้ครอบคลุมเฉพาะเส้นทาง outbound **non-SR** (write-off, breakage, expiry)
- ที่เกี่ยวข้อง: [[physical-count]] / [[spot-check]] — การดำเนินการนับที่ระดับ location; การ post ฝั่ง inventory ที่เกิดจาก count ผ่าน stock-in / stock-out documents ที่ครอบคลุมด้านบน
- ที่เกี่ยวข้อง: [[inventory-adjustment]] — การปรับด้วยมือสำหรับ scenarios data-fix / found-stock / breakage; รูปทรง `tb_stock_in` / `tb_stock_out` เดียวกัน จำแนกโดย `adjustment_type_id`
