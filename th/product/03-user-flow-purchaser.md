---
title: สินค้า (Product) — User Flow — Purchaser
description: flow ของ Purchaser ในโมดูลสินค้า — การ lookup อ่านอย่างเดียว การอ้างอิง และเส้นทาง feedback
published: true
date: 2026-05-17T12:00:00.000Z
tags: product, user-flow, purchaser, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# สินค้า (Product) — User Flow — Purchaser

> **At a Glance**
> **Persona:** Purchaser &nbsp;·&nbsp; **โมดูล:** [[product]] &nbsp;·&nbsp; **ขั้นตอน workflow:** lookup อ่านอย่างเดียว — ค้นหา / filter แคตตาล็อก live; อ้างอิง `standard_cost`, ต้นทุนรับล่าสุด (`PRD_CALC_008`), การแปลงหน่วย, vendor mapping, tax profile; post comment สำหรับแคตตาล็อกเก่าหรือการขอสินค้าใหม่ &nbsp;·&nbsp; **สิทธิ์สำคัญ:** อ่านอย่างเดียวบนแคตตาล็อก; comment (`tb_product_comment`); ไม่มีการเปลี่ยนวงจรชีวิต
> **persona นี้ทำอะไร:** ค้นหาสินค้าและอ้างอิงค่าข้อมูลหลักขณะจัดทำบรรทัด PR / PO; ให้ feedback ผ่าน comment

## 1. บทบาทในโมดูลนี้

persona **Purchaser** เป็น **ผู้บริโภค read-only** ของแคตตาล็อกสินค้า ในโมดูล product อำนาจของพวกเขาคือ **lookup เท่านั้น**: ค้นหาและ filter แคตตาล็อก live ดูรายละเอียดสินค้า (รวม standard cost ต้นทุนรับล่าสุดตาม `PRD_CALC_008` การแปลงหน่วย vendor mapping การจำแนก tax profile) อ้างอิง conversion factor หน่วยสั่งซื้อเมื่อจัดทำบรรทัด PR / PO และ post comment (`tb_product_comment`) บนสินค้าที่พบเก่าหรือผิดหรือเพื่อขอให้สร้างสินค้าใหม่ พวกเขา **ไม่** สร้างสินค้า **ไม่** แก้ฟิลด์ข้อมูลหลักใด ๆ **ไม่** แก้การแปลงหน่วยหรือการจำแนก **ไม่** อนุมัติการเปลี่ยน standard cost (role ของ Cost Controller / Finance) **ไม่** แก้นโยบายสต๊อกต่อ location (role ของ Inventory Controller) และ **ไม่** มีส่วนร่วมในการเปลี่ยนวงจรชีวิตของสินค้า กิจกรรมด้านคลังของพวกเขา (การจัดทำ PR และ PO) เป็นธุรกรรมเต็มและอยู่ในไฟล์ persona ของ [[purchase-request]] และ [[purchase-order]] — หน้านี้ครอบคลุมเฉพาะ surface **product-catalogue lookup** ที่พวกเขาแตะเพื่อสนับสนุนงานนั้น

## 2. Entry Point และ Primary Flow

**Entry point:** เส้นทางหลักสองทางสู่การโต้ตอบของ Purchaser กับโมดูล product — หนึ่ง direct (browse แคตตาล็อก) และหนึ่ง indirect (product picker บนบรรทัด PR / PO)

- **Product Management → Products (list / search)** — browse / search โดยตรง ใช้เมื่อค้นคว้าความครบของแคตตาล็อกก่อนการ run procurement ที่วางแผน ตรวจสอบ standard cost ของชุด item หรือตรวจสอบ vendor mapping ก่อนเปิด PR
- **PR / PO line product picker** — indirect ฝังใน flow การจัดทำ PR / PO Picker filter ด้วย `product_status_type = active`, `is_active = true` และ `deleted_at IS NULL` ตาม `PRD_AUTH_009` Picker อาจถูกกำหนดขอบเขตเพิ่มด้วย vendor (เมื่อจัดทำ PO ต่อ vendor เฉพาะ picker filter สินค้าที่มี `tb_product_tb_vendor` mapping กับ vendor นั้น)

**Primary flow (lookup สินค้าเพื่อเพิ่มไปยังบรรทัด PR 6 ขั้นตอน — รูปแบบหลัก):**

1. **เปิด picker ของบรรทัด PR** จากภายใน line entry ของ [[purchase-request]] คลิกฟิลด์สินค้าเพื่อเปิด picker Picker แสดงแคตตาล็อก active พร้อมคอลัมน์สำหรับ code, name, หน่วยฐาน, standard cost, ต้นทุนรับล่าสุด (derive ตาม `PRD_CALC_008`) และจำนวน vendor (จำนวน vendor ที่ map)
2. **ค้นหา / filter** พิมพ์ code, name, local name, barcode หรือ SKU การค้นหาคือ full-text ตาม `TR-SEARCH-*` (carmen/docs PRD § 5.5) filter ตาม category / sub-category / item-group (dropdown การจำแนก) ตาม vendor (vendor scope) หรือตามคุณสมบัติอื่นที่แสดงผ่านคีย์ JSON `tb_product.info` การ filter เป็น read-only — Purchaser ไม่สามารถ save filter ลงใน master ได้เพียงแต่ใน saved-view ส่วนตัว (ฟีเจอร์ frontend-only)
3. **ตรวจสอบรายละเอียดสินค้า (เป็นทางเลือก)** คลิกผ่านไปยังมุมมองรายละเอียดสินค้าเต็มสำหรับบริบทที่ลึกกว่า: เส้นทางการจำแนก (`PRD_CALC_001`), tax profile ที่สืบทอด (`PRD_CALC_002`), ค่าความคลาดเคลื่อน (`PRD_CALC_003`), การแปลงหน่วยที่นิยามทั้งหมด (แถว `tb_unit_conversion`), vendor mapping (แถว `tb_product_tb_vendor` พร้อม `vendor_product_code` cross-reference), นโยบายสต๊อกต่อ location (แถว `tb_product_location` — เพื่อแจ้งให้ทราบ; Purchaser ไม่แก้) และประวัติการซื้อล่าสุด (การรับ GRN ล่าสุดไม่กี่ครั้งพร้อม date / vendor / ต้นทุนต่อหน่วย) Tab Latest Purchase คือที่ที่ Purchaser ไปเพื่อ benchmark ราคา
4. **เลือกสินค้า** เลือกแถวใน picker; บรรทัด PR / PO ถูก populate ด้วย `product_id`, `inventory_unit_id` (หน่วยฐานของสินค้า) และ **หน่วยสั่งซื้อ default** (แถว `tb_unit_conversion` ที่ `is_default = true`, `unit_type = order_unit`) Purchaser อาจ override หน่วยสั่งซื้อโดยเลือก conversion อื่นที่ตั้งค่า (เช่น สลับจาก `CASE` เป็น `EACH` สำหรับคำสั่งที่เล็ก); ตาม `PRD_XMOD_006` หน่วยที่ไม่นิยามใน `tb_unit_conversion` สำหรับสินค้าไม่สามารถใช้ได้ (picker แสดงเฉพาะ conversion ที่นิยาม)
5. **กรอก qty และ unit-price** Qty ในหน่วยสั่งซื้อที่เลือก unit-price (โดยทั่วไป pre-populate จาก `tb_pricelist_detail` ล่าสุดหรือต้นทุน GRN ล่าสุด) ระบบคำนวณ qty หน่วยฐานตาม `PRD_CALC_005` (`order_unit_qty × conversion_factor = base_unit_qty`) สำหรับคลังและ costing ปลายน้ำ ค่าความคลาดเคลื่อนของราคา (`PRD_CALC_003` → `price_deviation_limit` ที่มีผล) อ่านที่จุดนี้; unit-price นอก tolerance flag สำหรับการอนุมัติเกินเกณฑ์ตาม `PR_VAL_*`
6. **Save บรรทัด** บรรทัด PR / PO ถูกเพิ่ม; การโต้ตอบของ Purchaser กับ product master จบ ตัวสินค้าเองไม่เปลี่ยน (read-only)

flow **comment** คือเส้นทางรอง:

- **feedback แคตตาล็อกเก่าหรือขาด** เมื่อ Purchaser พบสินค้าที่ข้อมูลผิด (หน่วยฐานผิด ขาด vendor mapping standard cost ล้าสมัย ขาด conversion factor สำหรับหน่วยที่พวกเขาต้องการ) หรือเมื่อสินค้าที่พวกเขาคาดหวังจะพบไม่มีในแคตตาล็อก พวกเขา post comment บนสินค้าที่เกี่ยวข้อง (`tb_product_comment.message`) Attachment สามารถรวม screenshot ของใบเสนอราคา vendor หรือ page แคตตาล็อก supplier สำหรับสินค้าที่ขาด comment ถูก post บนสินค้าที่ใกล้ที่สุดที่มีอยู่หรือผ่านช่อง "คำขอสินค้าใหม่" แยก; Product Administrator หยิบจาก comments queue ตาม [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) Section 2
- **การ escalate ราคา** ถ้าใบเสนอราคา vendor เบี่ยงจาก standard cost ที่บันทึก (`tb_product.standard_cost`) อย่างมีนัยสำคัญและจะละเมิด tolerance Purchaser flag ผ่าน comment เพื่อให้ Product Administrator (พร้อม Cost Controller sign-off ตาม `PRD_AUTH_012`) สามารถ update standard cost Purchaser **ไม่** แก้ `standard_cost` โดยตรง

flow **catalogue-browse** (entry point 1) ตามรูปทรงเดียวกันแต่ใช้นอกบริบทของ PR / PO เฉพาะ — โดยทั่วไปสำหรับการค้นคว้าวางแผน procurement หรือสำหรับการตรวจสอบความครบของแคตตาล็อกก่อนการ refresh เมนูรายไตรมาส

## 3. Decision Branch

- **filter ของ picker — รวมสินค้า inactive?** ตาม default picker แสดง `product_status_type = active` Purchaser อาจ toggle filter "แสดง inactive" เพื่อหาสินค้าประวัติ (เช่นค้นคว้าว่าใช้อะไรปีที่แล้วก่อนที่ SKU ตามฤดูกาลจะถูกปิดใช้) การเลือกสินค้า inactive สำหรับบรรทัด **ใหม่** ถูกปฏิเสธตาม `PRD_XMOD_001` — picker grey out แถว inactive เมื่อ toggle เปิด และการส่ง API ตรงด้วย `product_id` ที่ inactive ถูกปฏิเสธที่ line save ของโมดูลต้นทาง filter นี้เป็น read-only — การ toggle ไม่เปลี่ยน master
- **เลือกหน่วยสั่งซื้อบนบรรทัด** picker แสดงหน่วยสั่งซื้อ default (`is_default = true`) แต่อนุญาตให้สลับเป็น conversion หน่วยสั่งซื้ออื่นที่ตั้งค่า ถ้าหน่วยที่ Purchaser ต้องการไม่ได้ตั้งค่า เส้นทางเดียวคือ: (a) post comment ขอให้ Product Administrator เพิ่ม conversion แล้วรอ หรือ (b) ใช้หน่วยที่ตั้งค่าต่างกันและปรับ qty ด้วยมือ (เชื่อถือได้น้อยกว่า — การคำนวณระบบอาจไม่ถูก) เส้นทางแรกเป็นที่ต้องการอย่างยิ่ง
- **Standard cost vs ต้นทุนรับล่าสุด** รายละเอียดสินค้าแสดงทั้งสอง:
  - `standard_cost` คือ reference ที่ Product Administrator จัดการ; update ใน cadence (รายเดือน / รายไตรมาสตามกระบวนการของ Cost Controller)
  - **ต้นทุนรับล่าสุด** (derive ตาม `PRD_CALC_008`) คือต้นทุนต่อหน่วยจริงล่าสุดจาก GRN — "ที่เราจ่ายจริงล่าสุด"

  Purchaser ใช้ทั้งสอง: standard cost คือ reference งบประมาณ (เปรียบเทียบใบเสนอราคา vendor กับ standard flag deviation); ต้นทุนรับล่าสุดคือ reference ตลาด (เปรียบเทียบใบเสนอราคาปัจจุบันกับการซื้อจริงล่าสุด) ใบเสนอราคา vendor ที่มากกว่า standard อย่างมีนัยสำคัญแต่สอดคล้องกับการรับล่าสุดคือ "การ drift ของตลาด" — flag สำหรับการ refresh standard cost ใบเสนอราคา vendor ที่มากกว่าทั้งคู่คือ "ความผิดปกติของ vendor" — สอบสวน vendor
- **vendor scope filter บน PO** เมื่อจัดทำ PO ต่อ vendor เฉพาะ picker กำหนดขอบเขตเป็นสินค้าที่มี `tb_product_tb_vendor` mapping กับ vendor นั้น (ตาม `PRD_AUTH_006`) ถ้าสินค้าที่ Purchaser ต้องการเพิ่มไม่ map กับ vendor บรรทัดไม่สามารถ save ต่อ PO นั้นได้ — เปลี่ยน vendor บน PO หรือ post comment ขอให้ Product Administrator เพิ่ม vendor mapping (สำหรับ PR แบบหลาย vendor ที่ explode เป็นหลาย PO filter นี้ใช้ต่อการเลือก vendor ใน PO creation)
- **comment vs out-of-band escalation** สำหรับ feedback แคตตาล็อกประจำ (ราคาเก่า ขาด conversion barcode ไม่ตรง) thread comment เป็นช่องมาตรฐาน สำหรับปัญหาเร่งด่วน (SKU สำคัญหายระหว่างการเปิดตัวเมนู vendor mapping ผิดบน PO วันเดียวกัน) Purchaser อาจ escalate ผ่านช่องตรง (chat email) และ post comment เป็น anchor audit-trail UI แคตตาล็อกไม่มี type comment "เร่งด่วน" แยก
- **ค้นหาด้วย barcode vs ด้วย code** สำหรับการ lookup SKU ประจำ ค้นหาด้วย code (สินค้าส่วนใหญ่มี code เดียวกันภายในเหมือนใน vendor catalog) สำหรับการค้นคว้าที่ขับเคลื่อนด้วยการรับ (Purchaser cross-check สินค้าบนบรรทัด GRN) ค้นหาด้วย barcode (`tb_product.barcode`) match ตัวระบุที่สแกน

## 4. Exit Point / Handoff

การโต้ตอบของ Purchaser กับ product master จบที่หนึ่งใน boundary เหล่านี้:

- **บรรทัด PR / PO save แล้ว** picker resolve `product_id`; บรรทัดถูก populate และ save บน PR / PO Product master ไม่เปลี่ยน การมีส่วนร่วมของ Purchaser ด้านแคตตาล็อกเสร็จ; งานของพวกเขาดำเนินต่อใน [[purchase-request]] / [[purchase-order]] ในฐานะเจ้าของเอกสาร
- **comment post แล้วรอ Product Administrator** feedback แคตตาล็อกเก่าหรือคำขอสินค้าใหม่ log เป็น comment บนสินค้าที่เกี่ยวข้อง (หรือสินค้าที่ใกล้ที่สุดที่มีอยู่) Product Administrator หยิบจาก comments queue ตาม [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) Section 4 ("Inbound comment resolved") Purchaser อาจได้รับการแจ้งเตือนเมื่อ comment resolve (ขึ้นอยู่กับการตั้งค่า tenant); ถ้าถูกบล็อกบนการ resolve Purchaser อาจต้องเลื่อนบรรทัด PR / PO จนกว่า master จะ update
- **การ escalate ราคา route แล้ว** ใบเสนอราคา vendor ที่ละเมิด tolerance ค่าความคลาดเคลื่อนของ standard cost trigger flow comment / escalation; การ resolve อยู่ที่ Product Administrator + Cost Controller / Finance ตาม `PRD_AUTH_012` Purchaser ถือบรรทัด PR / PO ที่ draft รอการ refresh standard cost หรือดำเนินการกับบรรทัดและยอมรับ flag deviation บน workflow เอกสาร
- **picker ปิดโดยไม่เลือก** เมื่อ Purchaser หาสิ่งที่ต้องการไม่ได้ (สินค้าขาด vendor mapping ขาด conversion ขาด) picker ปิดและ comment / คำขอสินค้าใหม่ post บรรทัด PR / PO อยู่ที่ draft
- **session browse-only research จบ** เมื่อ catalogue browse เป็นสำหรับการ research วางแผน (ไม่ผูกกับ PR / PO เฉพาะ) session ของ Purchaser จบโดยไม่มี action — ความรู้ที่ได้แจ้งงาน procurement ต่อมาแต่ไม่มีการเปลี่ยนสถานะ commit

## 5. แหล่งอ้างอิง

- Parent overview: [03-user-flow.md](./03-user-flow.md) — canonical state machine ของ record สินค้า (Section 2 — Purchaser เป็นผู้บริโภคของสถานะ `active`) และตาราง handoff ข้าม persona (Section 4 — เส้นทาง Purchaser → Product Administrator comment / คำขอสินค้าใหม่)
- Sibling: [03-user-flow-product-admin.md](./03-user-flow-product-admin.md) — persona ต้นน้ำที่สร้าง / ดูแลแคตตาล็อกที่ Purchaser อ่าน Handoff การ resolve comment อยู่ที่นั่น
- Sibling: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — persona ผู้บริโภค read-only คู่ขนานที่ชั้นปฏิบัติการ
- Sibling: [01-data-model.md](./01-data-model.md) — รูปทรง `tb_product` ที่ picker แสดง (ขั้นตอน 1–2 ของ primary flow), `tb_unit_conversion` พร้อม `unit_type = order_unit` (ขั้นตอน 4–5), `tb_product_tb_vendor` สำหรับ vendor scope (ขั้นตอน 2 filter vendor และ decision branch บน PO scope), `enum_product_status_type` (filter active)
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎการคำนวณ `PRD_CALC_001` (เส้นทางการจำแนก), `PRD_CALC_002` (การสืบทอด tax-profile), `PRD_CALC_005` (conversion factor), `PRD_CALC_008` (ต้นทุนรับล่าสุด — derive) อ้างในขั้นตอน 3 และ 5; กฎการกำหนดสิทธิ์ `PRD_AUTH_005` (อำนาจ read-only ของ Purchaser), `PRD_AUTH_006` (อ่าน vendor-mapping), `PRD_AUTH_009` (filter default ของ picker); กฎข้ามโมดูล `PRD_XMOD_001` (สินค้า inactive ถูกปฏิเสธบนบรรทัดใหม่) อ้างใน decision branch
- โมดูลที่เกี่ยวข้อง: [[purchase-request]] / [[purchase-order]] — โมดูลหลักที่ Purchaser เป็นเจ้าของ; product picker ฝังใน line entry ค่าความคลาดเคลื่อนของสินค้า (`PRD_CALC_003`) gate การอนุมัติเกินเกณฑ์บนเอกสารเหล่านี้
- ที่เกี่ยวข้อง: [[vendor-pricelist]] — pricelist อ้างอิงสินค้า; Purchaser อ่านเพื่อสนับสนุนการตั้งราคาบรรทัด PR / PO
- ที่เกี่ยวข้อง: [[good-receive-note]] — ต้นทุนการรับจริงของ GRN ป้อนกลับเข้า `tb_inventory_transaction_cost_layer.cost_per_unit` ซึ่งเป็นสิ่งที่ `PRD_CALC_008` (ต้นทุนรับล่าสุด) แสดงกลับให้ Purchaser data flow เป็น round-trip แต่ Purchaser เป็นผู้มีส่วนร่วมด้าน read-side เท่านั้น
