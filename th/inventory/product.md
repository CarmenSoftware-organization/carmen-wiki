---
title: สินค้า (Product)
description: ข้อมูลหลักของสินค้า — หมวดหมู่ หน่วยนับ คลังจัดเก็บและชั้นวาง eco label และการส่งออก — แคตตาล็อกที่เอกสารคลังทุกใบอ้างอิง
published: true
date: '2026-09-23T01:30:00.000Z'
tags: product, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# สินค้า (Product)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** แคตตาล็อกข้อมูลหลักของสินค้า — รหัส หมวดหมู่ หน่วยฐาน/หน่วยสั่งซื้อ/หน่วยสูตรอาหารพร้อมการแปลงหน่วย การจับคู่กับคลังจัดเก็บ สารก่อภูมิแพ้ ใบรับรอง eco-label และการนำเข้า/ส่งออกเป็นชุด &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Product Administrator, Purchaser, Store Keeper &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_product`, `tb_product_category`, `tb_unit_conversion`, `tb_product_location` (+ `tb_location_shelf`), `tb_eco_label` / `tb_product_eco_label` &nbsp;·&nbsp; **หน้าย่อย:** 11

![สินค้า (Product) screen](/screenshots/product/index.png)

![สินค้า (Product) detail screen](/screenshots/product/detail.png)

## 1. ภาพรวม

โมดูลสินค้าคือแคตตาล็อกข้อมูลหลักศูนย์กลางของระบบ ERP สินค้าทุกตัวถูกระบุด้วย `productCode` ที่ไม่ซ้ำกัน จัดประเภทผ่านลำดับชั้น **หมวดหมู่ → หมวดหมู่ย่อย → กลุ่มสินค้า** (สามระดับพอดี — ดู [01-data-model](/th/inventory/product/01-data-model) § 5 ข้อ 8) และมีคุณสมบัติเชิงคำอธิบาย ต้นทุน ภาษี และบรรจุภัณฑ์ที่โมดูลปลายน้ำต้องใช้ คำอธิบายภาษาอังกฤษและภาษาท้องถิ่น บาร์โค้ด standard cost ต้นทุนรับล่าสุด และค่าความคลาดเคลื่อนของปริมาณ/ราคาที่ยอมรับได้อยู่บนส่วนหัวของสินค้า ส่วนคุณสมบัติเสริม (น้ำหนัก อายุการเก็บรักษา คำแนะนำการจัดเก็บ ขนาด สี สารก่อภูมิแพ้ ข้อมูลความยั่งยืน) ถูกออกแบบเป็นคู่ key-value แบบมี type ที่สืบทอดมาจากหมวดหมู่ได้และ override ที่ระดับสินค้าได้

สินค้าทุกตัววัดด้วย **หน่วยคลังฐาน** โดยมี **หน่วยสั่งซื้อ** และ **หน่วยสูตรอาหาร** หนึ่งหน่วยขึ้นไปวางทับด้วย conversion factor ที่ระบุชัดเจน ตารางการแปลงหน่วยถูกตรวจสอบความสอดคล้อง (สองทิศทาง ไม่มีวงกลม) เพื่อให้ปริมาณที่กรอกในหน่วยใดก็ตามบนเอกสารใดก็ตาม — PR, PO, GRN, requisition, recipe — สามารถ resolve กลับเป็นหน่วยฐานเพื่อการประเมินมูลค่าได้ สินค้าทุกตัวยังถูก activate กับ **คลังจัดเก็บ** หนึ่งคลังหรือหลายคลัง พร้อม threshold minimum / maximum / par ต่อคลังที่ขับเคลื่อนการเติมสต๊อก และ — นับจาก 2026-08 — **ชั้นวาง** แบบเลือกได้จากข้อมูลหลัก [shelf](/th/inventory/master-data/shelf) ระดับ BU

เครื่องมือจัดการเป็นชุดแคบกว่าที่หน้านี้เวอร์ชันก่อนอ้างไว้ (**แก้ไข 2026-09-22**): หน้าจอ list มี action **Export** (`hooks/use-product.ts:37` `useExportProduct`) แต่**ไม่มีการนำเข้าสินค้า** — `config_products.controller.ts` เปิดเฉพาะ CRUD, lookup กลุ่มสินค้า และ endpoint รูปภาพ และ `grep -ri import routes/product-management/product` พบแค่ ES-module import เท่านั้น ตัวอย่าง dry-run, error report และการสร้างบาร์โค้ด / QR เป็นชุดไม่มี code path ทั้งใน frontend, gateway หรือ Bruno collection; ถือว่าทุกข้อความ "bulk import" บนหน้าย่อยเป็น design intent

## 2. บริบททางธุรกิจ

ข้อมูลหลักของสินค้าเป็นรากฐานที่โมดูลอื่นทุกโมดูลอ่านข้อมูลไป บรรทัดของใบขอซื้อ บรรทัด PO บรรทัด GRN บรรทัด requisition วัตถุดิบในสูตรอาหาร ยอดสต๊อก บันทึก costing — ไม่มีอะไรในนั้นที่ดำรงอยู่ได้โดยไม่อ้างอิงถึงสินค้า ข้อมูลหลักที่ผิดทำให้ทุกอย่างปลายน้ำพังตาม: หน่วยฐานผิดทำให้การประเมินมูลค่าพองหรือยุบเงียบ ๆ conversion factor ที่ขาดทำให้รับของไม่ได้ หมวดหมู่ที่เก่าทำให้ roll-up ในรายงานพัง สินค้าที่ inactive แต่ยังเชื่อมกับสูตรอาหารที่เปิดอยู่ทำให้คำสั่งล้มเหลว กลุ่มโรงแรมที่ดำเนินกิจการในหลาย property รู้สึกถึงสิ่งนี้อย่างเข้มข้น — รายการสินค้าระดับ global ตัวเดียวพร้อมการเปิดใช้คลังระดับ property คือสิ่งที่ทำให้เครือข่ายมีความสอดคล้องในขณะที่ครัวท้องถิ่นยังคงยืดหยุ่นได้

โมดูลนี้จึงเป็น system of record สำหรับ *การนิยาม* ของรายการ ไม่ใช่การเคลื่อนไหวหรือยอดคงเหลือ มันป้อนเอกลักษณ์และโครงสร้างของสินค้าให้ [inventory](/th/inventory/inventory), [vendor-pricelist](/th/inventory/vendor-pricelist), [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order) และ [recipe](/th/inventory/recipe) และไม่ได้รับอะไรกลับมาจากพวกเขายกเว้น flag การใช้งาน (เช่น "in-use" ป้องกันการลบ) การจัดการชั้นนี้ให้ถูกต้อง — รหัส หน่วย หมวดหมู่ คลัง สารก่อภูมิแพ้ — คือเงื่อนไขเบื้องต้นที่ทำให้โมดูลอื่นทุกตัวทำงานได้ถูกต้อง

## 3. แนวคิดสำคัญ

- **Product Category**: โหนดการจำแนกประเภทเชิงลำดับชั้น (หมวดหมู่ → หมวดหมู่ย่อย → กลุ่มสินค้า สามระดับคงที่) ใช้สำหรับการจัดระเบียบ การ roll-up เพื่อรายงาน และการสืบทอดค่า default (tax profile, ค่าความคลาดเคลื่อน, flag recipe / sold-directly) ดู [category](/th/inventory/product/category) ว่าต้นไม้บังคับใช้อะไรจริง
- **Base Unit**: หน่วยคลังมาตรฐานสำหรับสินค้า (เช่น `KG`, `LITRE`, `EACH`) ยอดสต๊อก ต้นทุน และการประเมินมูลค่าทั้งหมดถูกเก็บในหน่วยฐาน ทุกหน่วยอื่นที่ผูกกับสินค้าถูกนิยามสัมพันธ์กับมันด้วย conversion factor
- **Conversion Factor**: ตัวคูณที่แปลงปริมาณที่แสดงในหน่วยสั่งซื้อหรือหน่วยสูตรอาหารเป็นหน่วยฐาน (เช่น 1 `CASE` = 12 `EACH`) การแปลงถูกตรวจสอบความสอดคล้องสองทิศทาง ต้องหลีกเลี่ยงวงกลม และกระจายไปยังบรรทัด PR/PO/GRN/recipe เพื่อให้ระบบ resolve ปริมาณทางกายภาพเดียวกันได้เสมอไม่ว่าจะกรอกอย่างไร
- **Location Mapping**: การกำหนดสินค้ากับคลังจัดเก็บหนึ่งคลังหรือหลายคลัง (warehouse, store, kitchen) แต่ละคลังมี threshold `min_qty` / `max_qty` / `par_qty` แบบเลือกได้ และเลือกได้ว่าจะมี **ชั้นวาง** (`tb_product_location.shelf_id` + snapshot `shelf_code` / `shelf_name` ตรวจสอบกับข้อมูลหลักชั้นวาง — ไม่เช่นนั้น `SHELF_NOT_FOUND`) แท็บ **Location Assignment** ของสินค้าเป็น UI เดียวที่ตั้งชั้นวาง `re_order_qty` ไม่ใช่การตั้งค่าอีกต่อไป: API คำนวณมัน (และ `on_hand_qty`) จาก cost layer ณ เวลาอ่าน (`products.replenishment.ts`)
- **Active/Inactive**: flag วงจรชีวิตที่ควบคุมว่าสินค้าสามารถปรากฏบนเอกสารใหม่ได้หรือไม่ สินค้า inactive ยังคงประวัติ (ยอดคงเหลือ PO เก่า สูตรอาหารเก่า) แต่ถูกแยกออกจาก picker และจากธุรกรรมใหม่ การเปลี่ยนสถานะตรวจสอบได้และสามารถตั้งเวลาให้มีผลในวันที่อนาคต
- **Barcode**: คอลัมน์ `tb_product.barcode` แบบ free-text ตัวเดียว แก้ไขบนแท็บ General (label "Barcode (EAN-13)" ใน `pd-tab-general.tsx:445`) ไม่มี `@unique` ใน schema และ **ยังไม่ยืนยัน** นอกเหนือจากนั้น: ไม่พบการสร้างเป็นชุด การพิมพ์ป้าย หรือ endpoint ค้นหาด้วยบาร์โค้ดโดยเฉพาะใน gateway (`config_products.controller.ts`) หรือ frontend ในรอบนี้
- **Allergen**: คุณสมบัติที่มีการกำกับดูแลซึ่ง flag การมีอยู่ของสารก่อภูมิแพ้ (กลูเตน นม ถั่ว สัตว์น้ำมีเปลือก ฯลฯ) ในสินค้า ข้อมูลสารก่อภูมิแพ้ถูกตั้งบนสินค้า สืบทอดผ่านสูตรอาหารไปยังเมนู และแสดงต่อ F&B Operations เพื่อเปิดเผยให้ลูกค้าและต่อ Procurement เมื่อหาของทดแทน
- **Product Variant**: เวอร์ชันเฉพาะของสินค้าที่แยกแยะด้วยการรวมกันของคุณสมบัติ (ขนาด สี บรรจุภัณฑ์) แต่ละแบบมี SKU ของตัวเอง ไม่มีตาราง `tb_product_variant` แยกต่างหาก — ตัวแปรถูกจำลองเป็น `tb_product` แถวของตัวเองที่ใช้หมวดหมู่/หน่วยฐานร่วมกับสินค้าหลัก หรือเป็น JSON key ใต้ `tb_product.info` สำหรับความแตกต่างที่ใช้แสดงผลอย่างเดียวและมีจำนวนน้อย (ดู [01-data-model](/th/inventory/product/01-data-model) § 5 ข้อ 1)
- **Standard Cost / Last Receiving Cost**: ต้นทุนอ้างอิงที่อยู่บนส่วนหัวของสินค้า standard cost คือต้นทุนที่วางแผน/งบประมาณซึ่งใช้สำหรับการวิเคราะห์ความแปรปรวน last receiving cost คือต้นทุนต่อหน่วยจริงล่าสุดที่เห็นบน GRN แสดงพร้อมวันที่และผู้ขายเพื่อบริบท ทั้งสองไม่ได้แทนที่การประเมินมูลค่าแบบเคลื่อนไหวที่ดูแลโดยโมดูล costing
- **Quantity / Price Deviation Tolerance**: ค่าความคลาดเคลื่อนเป็นเปอร์เซ็นต์ต่อสินค้า (0–100%) ที่จำกัดว่าบรรทัดของเอกสารปลายน้ำ (PR, PO, GRN) สามารถเบี่ยงเบนจากปริมาณหรือราคาในข้อมูลหลักได้แค่ไหนก่อนต้องขออนุมัติ ค่าความคลาดเคลื่อนไหลลงไปยัง record ลูกและทำหน้าที่เป็น guard-rail ป้องกันการกรอกผิด
- **Export (ไม่มี import)**: รายการสินค้าส่งออกได้ (`useExportProduct`); ไม่มี endpoint หรือหน้าจอนำเข้าสินค้า — ดู § 1 การนำเข้าหมวดหมู่ หน่วย และ conversion ก็ไม่มี code path เช่นกัน

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Product Administrator | เจ้าของแคตตาล็อก: สร้างและดูแลสินค้า หมวดหมู่ หมวดหมู่ย่อย กลุ่มสินค้า และหน่วย ตั้งค่า conversion factor คุณสมบัติ และ location mapping รันการนำเข้า/ส่งออกและจัดการวงจรชีวิตของสินค้า (เปิดใช้ ปลดประจำการ ลบ) |
| Purchaser | ค้นหาสินค้าเพื่อจัดทำ PR และ PO อ้างอิง standard cost และต้นทุนรับล่าสุด ตรวจสอบการแปลงหน่วยสั่งซื้อและการ map กับผู้ขาย และ flag รายการในแคตตาล็อกที่ขาดหรือเก่ากลับไปให้ administrator |
| Store Keeper | ค้นหาสินค้าระหว่างการรับของ การหยิบ การโอน และการนับ สแกนบาร์โค้ดเพื่อระบุตัวอย่างรวดเร็ว อ้างอิง threshold ของคลังและบันทึกการจัดการต่อสินค้า (คำแนะนำการจัดเก็บ อายุการเก็บรักษา) |

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [inventory](/th/inventory/inventory) — ยอดสต๊อกทุกรายการมีคีย์เป็นสินค้า
- [vendor-pricelist](/th/inventory/vendor-pricelist) — pricelist อ้างอิงสินค้า
- [purchase-request](/th/inventory/purchase-request) — บรรทัด PR อ้างอิงสินค้า
- [purchase-order](/th/inventory/purchase-order) — บรรทัด PO อ้างอิงสินค้า
- [recipe](/th/inventory/recipe) — สูตรอาหารอ้างอิงสินค้าเป็นวัตถุดิบ

**Master configuration:**
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยฐาน หน่วยสั่งซื้อ และหน่วยสูตรอาหาร พร้อม conversion factor
- [master-data/location](/th/inventory/master-data/location) และ [master-data/shelf](/th/inventory/master-data/shelf) — แถว location ที่สินค้าถูกกำหนดไว้ และข้อมูลหลักชั้นวางที่แถวเหล่านั้นอาจอ้างอิง
- Eco label — ข้อมูลหลัก `tb_eco_label` (เปลี่ยนชื่อจาก `tb_product_master_eco_label` เมื่อ 2026-09-04) ดูแลที่ `/product-management/eco` (`routes/product-management/eco/` ย้ายออกจาก `/config` เมื่อ 2026-09-03); ใบรับรองต่อสินค้าแก้ไขบนแท็บ **Eco Labels** ของฟอร์มสินค้า ดู [01-data-model](/th/inventory/product/01-data-model) § 2.10
- [system-config/application-config](/th/inventory/system-config/application-config) — ค่า default ระดับ tenant (ค่าความคลาดเคลื่อน นโยบายบาร์โค้ด schema คุณสมบัติ)
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — log วงจรชีวิตของสินค้าและการนำเข้าเป็นชุดสำหรับการตรวจสอบ
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — รูปภาพสินค้า เอกสารสเปก และใบรับรองที่แนบกับแต่ละสินค้า

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/product-management/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [Product Category](/th/inventory/product/category) — อนุกรมวิธานสามระดับ (หมวดหมู่ → หมวดหมู่ย่อย → กลุ่มสินค้า) อ้างอิงฉบับเต็ม
- [01 — โมเดลข้อมูล](/th/inventory/product/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [02 — กติกาทางธุรกิจ](/th/inventory/product/02-business-rules) — การตรวจสอบความถูกต้อง การคำนวณ/การสืบทอด การกำหนดสิทธิ์ วงจรชีวิต และกฎข้ามโมดูล
- [03 — User Flow](/th/inventory/product/03-user-flow) — วงจรชีวิตของ record สินค้า พร้อมสารบัญ persona
  - [Product Administrator](/th/inventory/product/03-user-flow-product-admin)
  - [Purchaser](/th/inventory/product/03-user-flow-purchaser)
  - [Store Keeper](/th/inventory/product/03-user-flow-store-keeper)
- [04 — Test Scenarios](/th/inventory/product/04-test-scenarios) — ขอบเขตของแต่ละ persona, scenario ข้าม persona และ mapping ไปยัง E2E
  - [Product Administrator](/th/inventory/product/04-test-scenarios-product-admin)
  - [Purchaser](/th/inventory/product/04-test-scenarios-purchaser)
  - [Store Keeper](/th/inventory/product/04-test-scenarios-store-keeper)
