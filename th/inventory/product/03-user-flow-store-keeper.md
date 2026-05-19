---
title: สินค้า (Product) — User Flow — Store Keeper
description: flow ของ Store Keeper ในโมดูลสินค้า — การ lookup อ่านอย่างเดียวที่ขับเคลื่อนด้วยบาร์โค้ด การอ้างอิงนโยบาย location และเส้นทาง feedback
published: true
date: 2026-05-19T23:55:00.000Z
tags: product, user-flow, store-keeper, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# สินค้า (Product) — User Flow — Store Keeper

> **At a Glance**
> **Persona:** Store Keeper &nbsp;·&nbsp; **โมดูล:** [product](/th/inventory/product) &nbsp;·&nbsp; **ขั้นตอน workflow:** lookup อ่านอย่างเดียวที่ระดับ floor — barcode scan (`tb_product.barcode`); ดูโน้ตการจัดการ อายุการเก็บรักษา flag ของสิ่งของเน่าเสีย; อ้างอิงนโยบายสต๊อกต่อ location (`tb_product_location.min_qty / max_qty / par_qty / re_order_qty`); post comment barcode-mismatch และโน้ตการจัดการ &nbsp;·&nbsp; **สิทธิ์สำคัญ:** อ่านอย่างเดียวบนแคตตาล็อก; comment (`tb_product_comment`); ไม่มีการเปลี่ยนวงจรชีวิต
> **persona นี้ทำอะไร:** สแกนและอ่านข้อมูลหลักของสินค้าระหว่างการรับ การหยิบ การโอน การนับ; รายงานปัญหาเชิงปฏิบัติการกลับผ่าน comment

## 1. บทบาทในโมดูลนี้

persona **Store Keeper** เป็น **ผู้บริโภค read-only** ของแคตตาล็อกสินค้า ดำเนินการที่ระดับ **floor / location** ระหว่างการรับ การหยิบ การโอน การนับ ในโมดูล product อำนาจของพวกเขาคือ **lookup เท่านั้น**: สแกนบาร์โค้ด (`tb_product.barcode`) สำหรับการระบุที่รวดเร็วบนอุปกรณ์มือถือ ดูรายละเอียดสินค้า (คำแนะนำการจัดการจาก JSON `tb_product.info` อายุการเก็บรักษา ข้อกำหนดการจัดเก็บ flag ของสิ่งของเน่าเสีย) อ้างอิงนโยบายสต๊อกต่อ location (`tb_product_location.min_qty / max_qty / par_qty / re_order_qty`) สำหรับบริบทระหว่างการนับและการเติมสต๊อก และ post comment (`tb_product_comment`) สำหรับ barcode ไม่ตรงและปัญหาเชิงปฏิบัติการ พวกเขา **ไม่** สร้างสินค้า **ไม่** แก้ฟิลด์ข้อมูลหลักใด ๆ **ไม่** แก้นโยบายสต๊อกต่อ location (role ของ Inventory Controller ตาม [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) `INV_AUTH_004`) **ไม่** แก้การแปลงหน่วย และ **ไม่** มีส่วนร่วมในการเปลี่ยนวงจรชีวิตของสินค้า กิจกรรมธุรกรรมของพวกเขา (การรับ GRN การ stock-in / stock-out การ run การนับสต๊อก / spot count) อยู่ในไฟล์ persona ของ [good-receive-note](/th/inventory/good-receive-note), [inventory](/th/inventory/inventory), [physical-count](/th/inventory/physical-count) และ [spot-check](/th/inventory/spot-check) — หน้านี้ครอบคลุมเฉพาะ surface **product-catalogue lookup** ที่พวกเขาแตะเพื่อสนับสนุนงานนั้น

## 2. Entry Point และ Primary Flow

**Entry point:** เส้นทางหลักสามทางสู่การโต้ตอบของ Store Keeper กับโมดูล product ทั้งหมด read-only และส่วนใหญ่ผ่านมือถือ

- **Barcode scan (มือถือ)** — flow หลักระหว่างการรับ การหยิบ การนับ Store Keeper สแกนฉลากสินค้า; mobile app resolve ตัวระบุที่สแกนกับ `tb_product.barcode` และแสดงสินค้าที่ resolve ไปยัง flow ธุรกรรม
- **รายละเอียดสินค้า (มือถือหรือ desktop)** — browse ตรงไปยังสินค้าเพื่อดูคำแนะนำการจัดการ อายุการเก็บรักษา การจำแนก หรือเพื่อตรวจสอบนโยบายสต๊อกต่อ location ใช้ระหว่างการรันการนับหรือเมื่อ triage ปัญหาการรับ
- **การอ้างอิงนโยบายต่อ location** — ดู `tb_product_location` สำหรับสินค้าที่ location เฉพาะ เพื่อเปรียบเทียบ on-hand กับ par / min / max ระหว่างการนับหรือตรวจสอบการเติมสต๊อก

**Primary flow (barcode scan ระหว่างการรับ 5 ขั้นตอน — รูปแบบหลัก):**

1. **เปิด flow การรับบนมือถือ** จากภายใน flow Receiver ของ [good-receive-note](/th/inventory/good-receive-note) Store Keeper อยู่ที่หน้าจอ line entry ของ GRN พวกเขาแตะปุ่ม scan
2. **สแกนบาร์โค้ด** mobile camera อ่านฉลากสินค้า (UPC / EAN / CODE128 ตาม `PRD_VAL_005`); app post ค่าที่สแกนไปยัง endpoint lookup endpoint query `tb_product.barcode = <scanned>` filter ไปที่สินค้า active (`product_status_type = active`, `is_active = true`, `deleted_at IS NULL`) ถ้าพบ match เพียงหนึ่ง สินค้าที่ resolve ถูก return พร้อม id, code, name, หน่วยฐาน, เส้นทางการจำแนกและโน้ตการจัดการ
3. **ยืนยันสินค้าที่ resolve** mobile app แสดงการ์ดสินค้าที่ resolve พร้อมรูป (ถ้ามี), code, name, local name และทางเลือก action ถัดไป ("เพิ่มไปยังบรรทัด GRN นี้", "ดูรายละเอียด", "สินค้าผิด") Store Keeper ยืนยันหรือ pivot — ถ้าสินค้าที่ resolve match กับ item ทางกายภาพในมือ พวกเขาเพิ่มไปยังบรรทัด; ถ้าไม่ พวกเขา pivot ไปยังเส้นทางการค้นหาด้วยมือหรือ barcode-mismatch
4. **อ้างอิงบริบทการจัดการ / location (เป็นทางเลือก)** ก่อนเพิ่มไปยังบรรทัด Store Keeper อาจแตะ "ดูรายละเอียด" เพื่อดู:
   - **โน้ตการจัดการ** จาก JSON `tb_product.info` — อุณหภูมิการจัดเก็บ อายุการเก็บรักษา flag เปราะ / อันตราย สารก่อภูมิแพ้
   - **นโยบายสต๊อกต่อ location** ที่ location การรับ — `tb_product_location.min_qty / max_qty / par_qty` สำหรับบริบท (การรับนี้สูงกว่า max? ต่ำกว่า min?)
   - **Standard cost** (`tb_product.standard_cost`) สำหรับ item มูลค่าสูงเป็น sanity-check กับต้นทุนต่อหน่วยของบรรทัด GRN
   - **vendor mapping** (`tb_product_tb_vendor`) — vendor การรับ match กับ vendor ที่ตั้งค่าสำหรับสินค้านี้หรือไม่?
5. **เพิ่มไปยังบรรทัด GRN** บรรทัด GRN ถูก populate ด้วย `product_id`, หน่วยฐาน และหน่วยสั่งซื้อที่เลือก (จาก `tb_unit_conversion`) Store Keeper กรอก qty (ในหน่วยสั่งซื้อ) และบรรทัด save Product master ไม่เปลี่ยน

flow **count / spot-check** เป็นรูปแบบคู่ขนาน:

- สแกนบาร์โค้ดเพื่อระบุสินค้าบนชั้น
- อ้างอิง `tb_product_location.par_qty` สำหรับ location การนับ — qty ที่นับ match กับ par? ต่ำกว่า par? สูงกว่า par?
- อ้างอิงโน้ตการจัดการ — สินค้าเน่าเสียหรือไม่ (วันหมดอายุจำเป็นบนบรรทัด count ตาม extension `INV_VAL_006`)?
- เพิ่มบรรทัด count; สินค้าถูกอ่าน ไม่แก้

flow **stock-in / stock-out** (การปรับด้วยมือตาม [inventory/03-user-flow-store-keeper](/th/inventory/inventory/03-user-flow-store-keeper)):

- สำหรับ workflow ที่ไม่ใช่ barcode (เช่น found-stock entry ที่ไม่มีฉลาก) Store Keeper ค้นหาด้วย code หรือ name ใน picker ด้วยมือ กฎ scope เดียวกัน (`active` + `is_active = true` + non-deleted)
- สำหรับสินค้าเน่าเสีย form prompt วันหมดอายุ (จำเป็นตาม `INV_VAL_006`); flag เน่าเสียมาจาก JSON `tb_product.info` (หรือตามธรรมเนียมหมวดหมู่)

flow **comment / feedback**:

- **Barcode ไม่ตรง** เมื่อบาร์โค้ดที่สแกน resolve เป็นสินค้าผิด (ฉลากทางกายภาพบอก "Spring Water 1L" แต่สินค้าที่ resolve คือ "Spring Water 500ml") Store Keeper post comment บนสินค้าที่ resolve พร้อมบาร์โค้ดที่สแกนและรูปของฉลากทางกายภาพตาม [03-user-flow.md](./03-user-flow.md) Section 4 Product Administrator update `tb_product.barcode` (หรือ SKU mapping) และตอบ Store Keeper สแกนใหม่เพื่อยืนยัน
- **Barcode ที่ไม่ resolve** เมื่อการสแกน return no match (`PRD_VAL_005` จะบล็อกการเพิ่มบาร์โค้ดถ้ามันชน; ที่นี่ปัญหาคือบาร์โค้ดไม่อยู่ในแคตตาล็อก) Store Keeper อาจใช้การค้นหาด้วยมือเพื่อหาสินค้าด้วย code/name และ post comment ขอให้ Product Administrator เพิ่ม barcode mapping หรือ Product Administrator สร้างสินค้าใหม่ทั้งหมดถ้าเป็น SKU ใหม่
- **การแก้ไขโน้ตการจัดการ** ถ้าคำแนะนำการจัดเก็บ / อายุการเก็บรักษาใน `tb_product.info` ผิด (เช่น ถุงบอก "Refrigerate at 4°C" แต่ master บอก "Ambient") Store Keeper post comment เพื่อให้ Product Administrator update JSON การแก้ไขที่เกี่ยวกับความปลอดภัยสำคัญ (การละเว้นสารก่อภูมิแพ้ flag อันตรายขาด) ถูก escalate out-of-band นอกเหนือจาก comment
- **การปรับนโยบาย location** เมื่อ `min_qty` / `max_qty` / `par_qty` ที่ตั้งค่ารู้สึกผิดสำหรับ location (stock-out คงที่ที่ min หรือ overstock คงที่เหนือ max) Store Keeper post feedback บน `tb_product_location` (ผ่าน tab location ของรายละเอียดสินค้า) Handoff คือ **Inventory Controller** (ไม่ใช่ Product Administrator) ตาม `INV_AUTH_004`

## 3. Decision Branch

- **scan resolve เป็นสินค้าหนึ่ง — ยืนยันหรือ pivot** match resolve เดี่ยวเป็น happy path; Store Keeper ยืนยันหรือถ้า item ทางกายภาพไม่ match แตะ "สินค้าผิด" เพื่อเข้า flow comment barcode-mismatch
- **scan resolve เป็นสินค้าหลายตัว (หายาก)** ตาม `PRD_VAL_005` ความไม่ซ้ำของบาร์โค้ดบังคับใช้ที่ application ดังนั้นซ้ำจริงไม่ควรมีในสถานะ live ถ้า lookup return match หลายตัว (โดยทั่วไปเพราะสินค้าหนึ่ง soft-delete แต่ index บาร์โค้ดของ application รวมมัน) app แสดง picker; Store Keeper เลือกตัว active กรณีนี้โดยทั่วไปบ่งบอกถึงปัญหาคุณภาพข้อมูลพื้นฐาน — Store Keeper post comment เพื่อให้ Product Administrator ทำความสะอาด
- **scan resolve เป็นไม่มีสินค้า — fallback ด้วยมือ** ไม่มี match: สลับเป็นการค้นหาด้วยมือด้วย code หรือ name ถ้าสินค้าไม่มีจริง post comment ขอสินค้าใหม่และ route งานกลับไปยัง floor supervisor หรือถือบรรทัดการรับ
- **พบสินค้า inactive (หายาก)** endpoint barcode-lookup filter เป็นสินค้า active ตาม default ถ้า Store Keeper toggle filter inactive (หายากบนมือถือ — โดยทั่วไปเป็นฟีเจอร์ desktop) พวกเขาอาจเห็นสินค้า inactive ในมุมมองรายละเอียดแต่ไม่สามารถเพิ่มไปยังบรรทัดธุรกรรมใหม่ตาม `PRD_XMOD_001` Picker ปฏิเสธ
- **อ้างอิง standard cost vs สมมติต้นทุน vendor-quoted บน GRN** บทบาทของ Store Keeper บน GRN คือยืนยันการรับ; พวกเขาไม่ตั้งต้นทุนต่อหน่วย (บรรทัด GRN ถือมันจาก PO / pricelist) อย่างไรก็ตามเมื่อต้นทุนบรรทัด GRN เบี่ยงจาก `standard_cost` อย่างมีนัยสำคัญ Store Keeper flag บน thread comment ของ GRN เพื่อให้ Receiver / Inventory Manager สอบสวนก่อน commit นี่เป็นความกังวลของ [good-receive-note](/th/inventory/good-receive-note) แต่ข้อมูลอ่านจาก product master
- **ใช้ barcode สำหรับการหยิบ (SR) vs ใช้ code สำหรับการค้นหา** ระหว่าง SR dispatch (การออกสต๊อกให้ outlet) Store Keeper โดยทั่วไปสแกน barcode เพื่อยืนยันว่าพวกเขาหยิบสินค้าที่ถูกจากถัง ระหว่าง SR composition (outlet manager ขอ) การค้นหาด้วย code เป็นปกติมากกว่า surface ของ product master เหมือนกัน; เส้นทางเข้าต่างกัน
- **นโยบายต่อ location เป็นสัญญาณ soft ไม่ใช่ gate แข็ง** `min_qty` / `max_qty` / `par_qty` เป็นที่แนะนำ — พวกเขา trigger alert และคำแนะนำการเติมสต๊อกแต่ไม่บล็อกธุรกรรม การรับที่ดัน on-hand เหนือ `max_qty` จะสำเร็จ; ระบบ flag สำหรับ review แต่ไม่ปฏิเสธ Store Keeper ใช้ค่าเหล่านี้เป็นบริบทสำหรับการสอบสวนการนับ (การนับที่ไกลจาก par อาจบ่งบอกถึงปัญหาที่ควรสอบสวน) แทนที่จะเป็น gate ธุรกรรม
- **comment vs entry activity-log** Comment (`tb_product_comment`) เป็น user-driven การอภิปรายอิสระ Activity log เป็น system-driven (การเปลี่ยนสถานะ การเปลี่ยนฟิลด์) Store Keeper post ใน comment; system event post ใน activity log ทั้งสอง query ได้แต่ทำหน้าที่ต่างกัน

## 4. Exit Point / Handoff

การโต้ตอบของ Store Keeper กับ product master จบที่หนึ่งใน boundary เหล่านี้:

- **Barcode resolve แล้ว บรรทัด populate แล้ว งานดำเนินต่อในโมดูลต้นทาง** Product master ถูกอ่าน; บรรทัด GRN / count / SR / stock-in / stock-out ถูก populate ด้วย `product_id` Product master ไม่เปลี่ยน; งานธุรกรรมของ Store Keeper ดำเนินต่อในโมดูลต้นทางตามไฟล์ persona ของมัน
- **comment post แล้วสำหรับ barcode ไม่ตรง** comment barcode-mismatch ถูก log บนสินค้าที่ได้รับผลกระทบ; Product Administrator หยิบจาก comments queue ตาม [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) Section 4 Store Keeper อาจต้องเลื่อนบรรทัด GRN / บรรทัด count จนกว่า master จะ update และการสแกนใหม่สำเร็จ (หรือใช้การค้นหาด้วยมือเพื่อดำเนินการกับงานและ post comment สำหรับการทำความสะอาดข้อมูลหลักภายหลัง)
- **comment post แล้วสำหรับ barcode ที่ไม่ resolve / ขอสินค้าใหม่** เหมือนข้างบน; งานหยุดหรือดำเนินการผ่านการค้นหาด้วยมือขึ้นอยู่กับความเร่งด่วน
- **feedback นโยบายต่อ location route ไปยัง Inventory Controller** feedback Min / max / par / reorder log ผ่าน comment บน tab location ของสินค้า; **Inventory Controller** หยิบ (ไม่ใช่ Product Administrator) การมีส่วนร่วมของ Store Keeper ต่อความกังวลเรื่องนโยบายจบ; Inventory Controller อาจ engage พวกเขาสำหรับบริบทระหว่าง review ตาม [inventory/03-user-flow-inventory-controller](/th/inventory/inventory/03-user-flow-inventory-controller)
- **โน้ตการจัดการ post การแก้ไขแล้ว** comment บนสินค้าพร้อมการแก้ไขที่เสนอ (storage temp อายุการเก็บรักษา allergen flag) ถูก log; Product Administrator update JSON `tb_product.info` ตาม flow ของพวกเขา
- **session lookup จบโดยไม่มีการเปลี่ยนสถานะ** เมื่อ Store Keeper ใช้แคตตาล็อกล้วน ๆ สำหรับการอ้างอิง (เช่นตรวจสอบคำแนะนำการจัดการก่อนเปิด shipment ของของเน่าเสีย) session จบโดยไม่มีการเปลี่ยน master และไม่มีการ post ธุรกรรม

## 5. แหล่งอ้างอิง

- Parent overview: [03-user-flow.md](./03-user-flow.md) — canonical state machine ของ record สินค้า (Section 2 — Store Keeper เป็นผู้บริโภคของสถานะ `active`) และตาราง handoff ข้าม persona (Section 4 — Store Keeper → Product Administrator บน barcode ไม่ตรง / การแก้ไขโน้ตการจัดการ, Store Keeper → Inventory Controller บน feedback นโยบายต่อ location)
- Sibling: [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) — persona ต้นน้ำที่สร้าง / ดูแลแคตตาล็อกที่ Store Keeper อ่าน; การแก้ไข barcode-mismatch และโน้ตการจัดการ route ไปยัง persona นี้
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ผู้บริโภค read-only คู่ขนานที่ชั้น procurement
- Sibling: [01-data-model.md](./01-data-model.md) — รูปทรง `tb_product` (โดยเฉพาะ `barcode`, JSON `info`, `inventory_unit_id` อ้างในขั้นตอน 4 ของ primary flow), `tb_product_location` สำหรับนโยบายต่อ location (รายละเอียดขั้นตอน 4), `enum_product_status_type` (filter active บน endpoint barcode-lookup)
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ validation `PRD_VAL_005` (ความไม่ซ้ำของบาร์โค้ด — application-enforced), กฎการคำนวณ `PRD_CALC_001` (เส้นทางการจำแนก), กฎการกำหนดสิทธิ์ `PRD_AUTH_007` (Store Keeper อ่านด้วย barcode lookup) และ `PRD_AUTH_008` (Store Keeper อ่านนโยบายต่อ location — แต่ไม่แก้); กฎข้ามโมดูล `PRD_XMOD_001` (สินค้า inactive ถูกปฏิเสธบนบรรทัดใหม่) อ้างใน decision branch
- ที่เกี่ยวข้อง: [good-receive-note](/th/inventory/good-receive-note) — โมดูลหลักสำหรับ flow barcode-scan หลัก (ขั้นตอน 1 entry); product master ถูกบริโภคที่ line entry ค่าความคลาดเคลื่อนของสินค้า (`PRD_CALC_003`) gate การอนุมัติ variance ของบรรทัด GRN
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — `tb_product_location` อ่านที่นี่; อำนาจ **edit** เป็นของ Inventory Controller ตาม [inventory/02-business-rules](/th/inventory/inventory/02-business-rules) `INV_AUTH_004` feedback นโยบายต่อ location route ไปยัง persona นั้น
- ที่เกี่ยวข้อง: [physical-count](/th/inventory/physical-count) / [spot-check](/th/inventory/spot-check) — การรันการนับใช้ barcode scan และการอ้างอิงนโยบายต่อ location ตาม Section 2 (flow count / spot-check)
- ที่เกี่ยวข้อง: [store-requisition](/th/inventory/store-requisition) — SR dispatch / picking ใช้ barcode scan สำหรับการยืนยันการหยิบจากถัง; product master ถูกบริโภคที่ขั้นตอนการหยิบ
- ที่เกี่ยวข้อง: [inventory-adjustment](/th/inventory/inventory-adjustment) — stock-in / stock-out สำหรับการปรับด้วยมือ; flag เน่าเสียจาก JSON `tb_product.info` อ้างที่ line save ตามกฎวันหมดอายุต่อสินค้า
