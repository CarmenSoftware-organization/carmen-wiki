---
title: คลังสินค้า (Inventory) — User Flow — Inventory Controller
description: Flow ของ Inventory Controller ในโมดูล inventory — ความถูกต้องของยอด การ review variance การประสานงานนับสต๊อก policy สต๊อก
published: true
date: 2026-05-19T23:55:00.000Z
tags: inventory, user-flow, inventory-controller, carmen-software
editor: markdown
dateCreated: 2026-05-15T12:00:00.000Z
---

# คลังสินค้า (Inventory) — User Flow — Inventory Controller

> **At a Glance**
> **Persona:** Inventory Controller &nbsp;·&nbsp; **โมดูล:** [inventory](/th/inventory/inventory) &nbsp;·&nbsp; **ขั้นตอน workflow:** อนุมัติ adjustment เหนือ threshold ของ Store Keeper (`draft → in_progress → completed`) &nbsp;·&nbsp; ประสานงานโปรแกรม physical-count และ spot-check &nbsp;·&nbsp; ปรับ policy สต๊อกต่อสินค้า / ต่อ location &nbsp;·&nbsp; เซ็นรับรอง variance ก่อนปิดงวด &nbsp;·&nbsp; **สิทธิ์สำคัญ:** อนุมัติเหนือ threshold (`INV_AUTH_003`); แก้ไข stock-policy (`INV_AUTH_004`); เจ้าของโปรแกรมนับ
> **สิ่งที่ persona นี้ทำ:** เป็นเจ้าของความถูกต้องของยอด — อนุมัติ adjustment เหนือ threshold ประสานงานการนับ และเซ็นรับรอง variance ก่อน Finance ปิดงวด

## 1. บทบาทในโมดูลนี้

Persona **Inventory Controller** เป็นเจ้าของ **ความถูกต้องของยอด** ทั่วทรัพย์สิน พวกเขาเป็นสิทธิ์อนุมัติชั้นที่สองที่ Store Keeper escalate ขึ้นมา และเป็นสิทธิ์อนุมัติชั้นแรกที่ Finance escalate จาก ภายในโมดูล inventory งานของพวกเขาครอบคลุมสี่สาย: (1) **อนุมัติ adjustment เหนือ threshold ของ Store Keeper** — ทุกเอกสาร `tb_stock_in` และ `tb_stock_out` เหนือ cap auto-approve route ไปยัง Controller ตาม `INV_AUTH_003` และ Controller คือ role ที่ fire การ advance `draft → in_progress → completed` บนเอกสารเหล่านี้; (2) **ประสานงานโปรแกรมการนับ** — กำหนดเวลา physical counts (`tb_physical_count` ขับด้วย `tb_location.physical_count_type = yes`), รัน spot checks สำหรับสินค้า velocity สูง / มูลค่าสูง, review variance ที่เกิดตาม `INV_XMOD_003` / `INV_XMOD_004` และตัดสินใจว่า variance ใด post (approve), ต้อง recount (กลับไปที่ Store Keeper) และต้อง investigate (ส่งต่อ Finance); (3) **ปรับ policy สต๊อกต่อสินค้า / ต่อ location** — คอลัมน์ par / min / max / reorder บน `tb_product_location` ขับโดยรูปแบบการบริโภคและ lead time ตาม `INV_AUTH_004` รวมถึง suggestion engine ที่แสดง outlier ของ stock-policy; (4) **เซ็นรับรอง variance ก่อนปิดงวด** — Controller คือ gate ที่การ run period-close ของ Finance รอ: ทุก count-variance adjustment ในงวดต้อง post (อนุมัติหรือ reject) ก่อนที่ Finance จะปิดงวด สำคัญ Inventory Controller **ไม่** post รายการกระทบยอด inventory-to-GL (นั่นเป็น `INV_AUTH_005` ของ Finance), **ไม่** lock งวด (นั่นเป็น `INV_AUTH_006` ของ Finance Manager) และ **ไม่** ตั้งค่า location type / costing method / adjustment-type reason code (นั่นเป็น `INV_AUTH_008` ของ Sysadmin) Segregation of duties carry through: Controller ที่ยังเป็น Store Keeper ที่ location เจาะจงไม่สามารถอนุมัติเอกสารของตนเอง; ระบบ route กรณีดังกล่าวไปยัง Controller peer หรือ Finance

## 2. จุดเข้าและ Flow หลัก

**จุดเข้า:** ห้าเส้นทาง ทั้งหมดเป็นผลของกิจกรรมต้นน้ำที่ route เข้า queue ของ Controller หรือเริ่มจากปฏิทินของ Controller

- **Queue อนุมัติ adjustment** — เอกสาร `tb_stock_in` และ `tb_stock_out` ที่ `doc_status = in_progress` รอการอนุมัติของ Controller; เรียงตาม submitted-at ขึ้น ขับ flow อนุมัติประจำวัน (Section 2.1 ด้านล่าง)
- **Dashboard count-variance** — เอกสารนับที่ `tb_count_stock.status = completed` พร้อม variance lines ที่ stage ไว้; ขับ flow อนุมัติ count-cycle (Section 2.2 ด้านล่าง)
- **ปฏิทินนับ / ตาราง** — events `tb_physical_count_period` ที่กำลังจะมาถึงและการ launch spot-check ad-hoc; ขับการเริ่มการนับ (ส่งต่อให้ Store Keeper ที่ location เพื่อดำเนินการ; flow เต็มใน [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check))
- **Dashboard stock policy** — rows `tb_product_location` ที่มี replenishment alerts (on-hand ต่ำกว่า `min_qty`, เหนือ `max_qty`) และหน้าจอแก้ไข policy ของ Controller สำหรับ par / min / max / reorder
- **Pre-flight ปิดงวด** — dashboard ที่ rollup จากเอกสาร variance ที่เปิด, การปรับ count ที่ไม่ post และ checklist เซ็นรับรอง variance review ของ Controller สำหรับงวดที่ปิด

### 2.1 Flow อนุมัติ adjustment (Store Keeper-initiated, 6 ขั้นตอน)

1. **เปิด queue อนุมัติ adjustment** หน้าจอแสดงเอกสาร `tb_stock_in` และ `tb_stock_out` ที่ `doc_status = in_progress` พร้อมผู้สร้าง (Store Keeper), location, reason code (`adjustment_type_id`), ผลกระทบต้นทุนรวม (`Σ qty × cost_per_unit`) และ attachments สนับสนุน
2. **เปิดเอกสารเฉพาะ** หน้าจอ render lines, รายละเอียดระดับ lot และ preview cost-pick (FIFO จาก lot ที่เก่าที่สุดหรือ weighted-average ปัจจุบัน ตาม costing method ของสินค้า) สำหรับ outbound lines Controller cross-check ความคลาดเคลื่อนกับ evidence ที่มาจาก — count sheet, ภาพถ่ายความเสียหาย, vendor RMA, lot-label scan
3. **ตัดสินใจผลลัพธ์** **Approve** ถ้าความคลาดเคลื่อนแท้และ reason code เหมาะสม **Reject** พร้อม comment ถ้าความคลาดเคลื่อนดูเหมือนข้อผิดพลาดการนับหรือเลือก reason code ผิด (เช่น write-off บันทึกเป็น breakage เมื่อควรเป็น expiry — GL classification ต่างกัน) **Adjust and approve** สำหรับการแก้ระดับ line (เปลี่ยน `qty` บน line เดียว; แก้ pick lot) ที่เอกสารโดยรวมดีแต่ line ต้องการความสนใจ
4. **ตรวจสอบ gate ผลกระทบต้นทุน** ถ้าผลกระทบต้นทุนรวมของเอกสารเกิน threshold ของ Controller หน้าจอ flag สำหรับ **การอนุมัติของ Finance** — การอนุมัติของ Controller ย้ายเอกสารไปยัง sub-state Finance-pending; Finance คือ role ที่ complete การอนุมัติสำหรับ write-off ขนาดใหญ่มาก สำหรับเอกสาร Controller-threshold ปกติ การอนุมัติของ Controller เป็น terminal
5. **Approve fire การ post** บนการอนุมัติของ Controller ที่ threshold ของ Controller: `tb_stock_in.doc_status = completed` (หรือ `tb_stock_out.doc_status = completed`); inventory transaction เขียนตาม `INV_POST_001` / `INV_POST_002`; cost-layer rows เขียนตามประเภท inbound / outbound; on-hand ที่ `(location, product, lot)` ก้าวหน้า Queue ของ Controller refresh; Store Keeper เห็นเอกสารที่ `completed` ใน activity log
6. **Reject กลับไปยัง Store Keeper** บนการ reject ของ Controller: `doc_status = draft` พร้อม comment ของ Controller บน activity log ของเอกสาร; Store Keeper เห็น rejection ใน inbox และแก้ไข / re-submit หรือ void ตาม flow (Section 2 ของ `[03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md)`)

### 2.2 Flow review count-variance (count-initiated, 7 ขั้นตอน)

1. **เปิด dashboard count-variance** แสดงเอกสารนับ (`tb_count_stock`) ที่ `status = completed` พร้อม location, count window, จำนวนรวม variance และรายละเอียดต่อ line (overage / shortage / lot-mismatch)
2. **เปิด count เฉพาะ** หน้าจอ render variance lines ต่อสินค้า: system qty vs counted qty vs variance, รายละเอียดระดับ lot, ผลกระทบต้นทุนต่อ line ที่ต้นทุน cost-layer ล่าสุดของระบบ Re-count attachments และ Store Keeper notes มองเห็น
3. **การตัดสินใจต่อ line** สำหรับแต่ละ variance line ตัดสินใจ: **post** (variance แท้; จะเขียนเอกสาร `tb_stock_in` (overage) / `tb_stock_out` (shortage) อัตโนมัติบน commit), **re-count** (variance น่าสงสัย; route กลับไปยัง Store Keeper สำหรับ re-count) หรือ **investigate** (variance ใหญ่และไม่ได้อธิบาย; route ไปยัง Finance สำหรับ flag investigation โดยยังไม่ post)
4. **การรวมผลกระทบต้นทุน** หน้าจอรวมผลกระทบต้นทุนของการตัดสินใจ `post` ทั้งหมดใน count; ถ้ารวมเกิน threshold ของ Controller, gate post-on-commit route ไปยังการอนุมัติของ Finance (analogous ต่อขั้นตอนที่ 4 ของ Section 2.1)
5. **Commit การตัดสินใจ** คลิก **Commit count decisions** — ระบบสร้างเอกสาร `tb_stock_in` หนึ่งฉบับ (rolling up ทุก overage lines จาก count นี้) และเอกสาร `tb_stock_out` หนึ่งฉบับ (rolling up ทุก shortage lines) แต่ละฉบับด้วย `adjustment_type_id` กำหนดเป็น reason code ที่ derive จาก count (`COUNT_OVERAGE` / `COUNT_SHORTAGE`); แต่ละเอกสารถือ count reference บน `info` JSON หรือ activity log
6. **Posts fire** เอกสาร stock-in และ stock-out auto-advance ผ่าน `draft → in_progress → completed` เพราะการอนุมัติของ Controller เป็นโดยปริยายในการกระทำ count-commit (Controller เป็นผู้กระทำบน commit) Inventory transactions เขียนตาม Section 2.1 step 5; on-hand reconcile ไปยัง counted qty
7. **อัปเดตเอกสารนับ** `tb_count_stock.status = completed_posted` (หรือสถานะ terminal ที่คล้าย); record การนับปิดด้วยรายละเอียด variance รักษาไว้สำหรับ audit; การอ่าน on-hand ต่อมา return balance ที่แก้ไขแล้ว

กิ่งการตัดสินใจและ flow stock-policy / pre-flight ปิดงวดสรุปใน Section 3

## 3. กิ่งการตัดสินใจ

- **อนุมัติ adjustment vs reject สำหรับการประเมินใหม่** Approve เมื่อความคลาดเคลื่อนเป็นเอกสาร (ภาพถ่าย, count sheet, RMA reference) และ reason code เหมาะสม Reject และกลับไปยัง Store Keeper ถ้า (a) evidence ขาดหรือไม่เพียงพอ, (b) reason code ผิด (ทำให้ GL classification ผิด — เช่น `BREAKAGE` vs `EXPIRY` route ไปยังบัญชี GL ที่ต่างกัน), (c) cost-per-unit บน stock-in (lot ที่มีอยู่) ไม่ตรงกับต้นทุนที่บันทึกของ lot
- **ต่ำกว่า vs เหนือ threshold ของ Controller** ต่ำกว่า — การอนุมัติของ Controller เป็น terminal; เอกสาร post บนการอนุมัติ เหนือ — การอนุมัติของ Controller ย้ายเอกสารไปยัง sub-state Finance-pending; Finance คือ role ที่ fire การ post ตาม chain การ route threshold ใน `INV_AUTH_005` Threshold ตั้งค่าโดย Sysadmin ตาม `INV_AUTH_008`
- **Count variance: post / re-count / investigate** **Post** เมื่อ variance น่าจะเป็น (ภายในช่วงปกติของ shrinkage / overage หรืออธิบายโดย event ที่ทราบเช่น recall write-off) และต่ำกว่า threshold ต่อ line ของ Controller **Re-count** เมื่อ variance น่าสงสัย — ใหญ่กว่าอัตรา shrinkage ประวัติศาสตร์อย่างมาก หรือกระทบสินค้ามูลค่าสูงโดยไม่มี event ที่ทราบ **Investigate** เมื่อ variance ใหญ่พอที่จะแนะนำปัญหาเชิงระบบ (overage ใหญ่แนะนำ inbound ที่หายไป; shortage ใหญ่แนะนำการลักทรัพย์หรือ breakage ที่ไม่บันทึกขนาดใหญ่) — Finance เป็น stop ถัดไปด้วย flag ไม่ post
- **Outlier ของ stock-policy vs ปกติ** Replenishment alerts ปรากฏเมื่อ on-hand ลดลงต่ำกว่า `min_qty` (แนะนำให้สั่งซื้อใหม่) หรือสูงขึ้นเหนือ `max_qty` (แนะนำ overstock) Controller อาจ **ดำเนินการ** บน alert (ยก `[purchase-request](/th/inventory/purchase-request)` เพื่อ replenish หรือเริ่ม transfer เพื่อ redistribute), **ปรับ policy** (แก้ `min_qty` / `max_qty` / `re_order_qty` / `par_qty` บน `tb_product_location` ถ้า alert เปิดเผย policy ที่ล้าสมัย) หรือ **dismiss** (event ครั้งเดียว ไม่มีการเปลี่ยน policy) การแก้ไข policy ใช้กับ prospective; on-hand ที่มีอยู่ไม่ได้รับผลกระทบ
- **การเซ็นรับรอง variance ปิดงวด vs hold** **เซ็นรับรอง** เมื่อ (a) ไม่มีเอกสาร adjustment `in_progress` ใน period ที่ปิด, (b) ทุก count run สำหรับ period คือ `completed_posted`, (c) ไม่มี count variance ที่ flag `investigate` ที่ค้าง **Hold** เมื่อ gate ใดเปิด — Controller สื่อสาร hold กับ Finance พร้อมรายการที่เปิดและวันที่คาดว่าจะแก้ไข การปิดงวดรันไม่ได้โดยไม่มีการเซ็นรับรองของ Controller ตามการส่งต่อข้าม persona ใน `[03-user-flow.md](./03-user-flow.md)` Section 4

## 4. จุดออก / การส่งต่อ

การมีส่วนร่วมของ Inventory Controller บน movement / count / period ที่กำหนดจบที่หนึ่งในสี่ขอบเขต:

- **Adjustment อนุมัติและ post** การอนุมัติต่ำกว่า threshold ของ Controller fire การ post; เอกสาร `completed`; inventory transaction เขียน; on-hand ก้าวหน้า Queue ของ Controller refresh; ไม่มีการกระทำเพิ่มเติมบนเอกสารนี้ Store Keeper เห็น `completed` ใน activity log
- **Adjustment escalate ไปยัง Finance** การอนุมัติเหนือ threshold ของ Controller ย้ายเอกสารไปยัง Finance-pending; ส่งต่อไปยัง **Finance** ([03-user-flow-finance.md](./03-user-flow-finance.md)) สำหรับการอนุมัติผลกระทบต้นทุนตาม `INV_AUTH_005` Controller re-engage ก็ต่อเมื่อ Finance reject (เอกสารกลับไปที่ `draft` พร้อม comment ของ Finance) หรือขอ supporting evidence เพิ่มเติม
- **Count variance committed** Count-commit fire การ post stock-in / stock-out rollup; เอกสาร count ย้ายไปที่ `completed_posted`; on-hand reconcile ส่งต่อกลับไปยัง **Store Keeper** ถ้า line ใด return สำหรับ re-count; ส่งต่อไปยัง **Finance** ถ้า line ใด flag `investigate` (พร้อม hold ไม่ post)
- **การเซ็นรับรอง variance ปิดงวด** Controller เซ็นรับรอง; ส่งต่อไปยัง **Finance** สำหรับการกระทบยอด inventory-to-GL และการรันปิดงวดตาม `INV_POST_009` Controller re-engage ก็ต่อเมื่อ Finance flag variance ของการกระทบยอดที่ต้องการการ investigate ฝั่ง Controller (ปกติ variance ที่นับแต่ไม่ post ที่การเซ็นรับรองของ Controller พลาด)

## 5. แหล่งอ้างอิง

- ภาพรวม Parent: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิต movement-and-period แบบ canonical ตารางการส่งต่อข้าม persona ที่ anchor ขอบเขต Store Keeper → Inventory Controller (อนุมัติ adjustment) และ Inventory Controller → Finance (อนุมัติผลกระทบต้นทุน, เซ็นรับรองปิดงวด)
- Sibling: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — persona ต้นน้ำที่เริ่มเอกสาร `tb_stock_in` / `tb_stock_out` ที่ Controller อนุมัติ และที่ดำเนินการ physical / spot counts ที่ Controller review variance
- Sibling: [03-user-flow-finance.md](./03-user-flow-finance.md) — persona ปลายน้ำสำหรับการอนุมัติเหนือ threshold ของ Controller และสำหรับการกระทบยอด inventory-to-GL ปิดงวด
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — System Administrator ที่ตั้งค่ารายการ reason-code `tb_adjustment_type` (ซึ่ง logic ของ Controller reject ขึ้นอยู่กับสำหรับการ GL classification ที่ถูกต้อง) และ threshold การอนุมัติของ Controller / Finance; Auditor ที่ review audit trail ของการอนุมัติของ Controller
- Sibling: [01-data-model.md](./01-data-model.md) — รูปทรง canonical ของ `tb_stock_in` / `tb_stock_out`, `tb_product_location` (ตาราง policy ที่ Controller maintain ตาม `INV_AUTH_004`), `tb_count_stock` / `tb_physical_count_period` (เอกสารนับที่ Controller review), ค่า `enum_inventory_doc_type` (`stock_in`, `stock_out`)
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ authorization `INV_AUTH_003` (สิทธิ์อนุมัติของ Controller), `INV_AUTH_004` (แก้ไข stock policy), `INV_AUTH_010` (Controller อนุมัติเอกสารของตนเองไม่ได้), บวกกฎ posting `INV_POST_001` (inbound post บนการอนุมัติของ Controller) / `INV_POST_002` (outbound post), และกฎข้ามโมดูล `INV_XMOD_003` / `INV_XMOD_004` (การ post count-variance), `INV_XMOD_005` (manual adjustment routing)
- ที่เกี่ยวข้อง: [physical-count](/th/inventory/physical-count) — โปรแกรมการนับที่ Controller ประสานงาน; วงจรชีวิต `tb_count_stock` ของเอกสาร count เป็นเจ้าของโดยไฟล์ persona ของโมดูล physical-count หน้านี้ครอบคลุมเฉพาะการ post ฝั่ง inventory ที่เกิดจาก count ที่เสร็จสิ้น
- ที่เกี่ยวข้อง: [spot-check](/th/inventory/spot-check) — partial count ในกลางงวด; เส้นทางการ post เดียวกันกับ physical-count
- ที่เกี่ยวข้อง: [inventory-adjustment](/th/inventory/inventory-adjustment) — ชื่อทั่วไปสำหรับ flow manual `tb_stock_in` / `tb_stock_out` ที่ Controller อนุมัติ; reason code (`adjustment_type_id`) แยก use case เฉพาะ
- ที่เกี่ยวข้อง: [costing](/th/inventory/costing) — preview cost-pick ที่ Controller review บน outbound (FIFO จาก lot ที่เก่าที่สุด vs weighted-average ปัจจุบัน) อ่านจาก `tb_inventory_transaction_cost_layer` ตาม costing method ของสินค้า
- ที่เกี่ยวข้อง: [product](/th/inventory/product) — ถือ field `costing_method` ที่ขับ cost-pick preview Sysadmin เป็นเจ้าของการตั้งค่า; flow อนุมัติของ Controller บริโภค
