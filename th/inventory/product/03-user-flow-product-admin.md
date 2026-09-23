---
title: สินค้า (Product) — User Flow — Product Admin
description: flow ของ Product Administrator ในโมดูลสินค้า — CRUD เต็มบนข้อมูลหลัก การจำแนก หน่วย การแปลง location และ vendor mapping วงจรชีวิต และ bulk import/export
published: true
date: '2026-09-23T01:30:00.000Z'
tags: product, user-flow, product-admin, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:30:00.000Z
---

# สินค้า (Product) — User Flow — Product Admin

> **At a Glance**
> **Persona:** Product Administrator &nbsp;·&nbsp; **โมดูล:** [product](/th/inventory/product) &nbsp;·&nbsp; **ขั้นตอน workflow:** สร้าง / แก้ `tb_product` (`active`) &nbsp;·&nbsp; ห่วงโซ่การจำแนก (category / sub-category / item-group) &nbsp;·&nbsp; หน่วยและการแปลง &nbsp;·&nbsp; location และ vendor mapping &nbsp;·&nbsp; bulk import / export &nbsp;·&nbsp; ปิดใช้ / re-activate / soft-delete / restore &nbsp;·&nbsp; ตอบ comment ขาเข้า &nbsp;·&nbsp; **สิทธิ์สำคัญ:** CRUD เต็มบนข้อมูลหลัก (`PRD_AUTH_001` / `PRD_AUTH_003` / `PRD_AUTH_004`); SoD บนการเปลี่ยน `standard_cost` เกินเกณฑ์ tenant (`PRD_AUTH_012` — Cost Controller / Finance signature ที่สอง)
> **persona นี้ทำอะไร:** เป็นเจ้าของแคตตาล็อก — สร้าง / ดูแลสินค้า การจำแนก หน่วย mapping และรันวงจรชีวิตของ record สินค้า

## 1. บทบาทในโมดูลนี้

persona **Product Administrator** เป็น **เจ้าของแคตตาล็อก** ในโมดูล product พวกเขามี **อำนาจ CRUD เต็ม** บนทุก surface ข้อมูลหลัก: แถว `tb_product` (สร้าง แก้ ปิดใช้ soft-delete restore) ห่วงโซ่การจำแนก (`tb_product_category → tb_product_sub_category → tb_product_item_group`) นิยามหน่วย (`tb_unit`) conversion factor (`tb_unit_conversion` สำหรับขอบเขตทั้ง `order_unit` และ `ingredient_unit`) นโยบายสต๊อกต่อ location mapping (`tb_product_location`) และ vendor mapping (`tb_product_tb_vendor`) พวกเขารัน bulk import และ export สำหรับ surface ของสินค้า / หมวดหมู่ / หน่วย / conversion จัดการวงจรชีวิตของสินค้า (`active ↔ inactive ↔ soft-deleted`) และตอบ comment ขาเข้าจาก Purchaser (feedback แคตตาล็อกเก่า ขอสินค้าใหม่) และ Store Keeper (barcode ไม่ตรง การ update โน้ตการจัดการ) Product Administrator **ไม่** อนุมัติเอกสารธุรกรรม (PR / PO / GRN / SR) และ **ไม่** มีส่วนร่วมในการปิด period หรือการกระทบยอดทางการเงิน พวกเขา **แก้ไข** ค่านโยบายสต๊อกต่อ location สำหรับการเติมสต๊อก (`tb_product_location.min_qty / max_qty / re_order_qty / par_qty`) โดยตรงบน Location Assignment tab ของ product edit form เดียวกัน — **แก้ไขในรอบนี้:** ฉบับร่างก่อนหน้าระบุว่าสิ่งนี้ถูกมอบหมายให้ "Inventory Controller" แยกต่างหากตาม `INV_AUTH_004`; ไม่พบ edit surface เช่นนั้นที่ใดในโค้ดเบสเลย (`INV_AUTH_004` ของโมดูล inventory เองก็ถูกทำเครื่องหมายเป็น *(unconfirmed)* ด้วยเหตุผลเดียวกัน) ดังนั้นการแก้ไขนโยบาย location จึงเป็นอำนาจของ Product Administrator เหมือนฟิลด์สินค้าอื่น ๆ ทุกตัว โดยถูก gate ด้วยการเข้าถึงหน้าจอ product edit เท่านั้น Segregation of duties (`PRD_AUTH_012`) จำกัด Product Administrator จากการอนุมัติการเปลี่ยน `standard_cost` ของตนเองเกินเกณฑ์ SoD ของ tenant — Cost Controller / Finance คือ signature ที่สอง

## 2. Entry Point และ Primary Flow

**Entry point:** เส้นทางหลักห้าทางสู่งานประจำวันของ Product Administrator — หนึ่งสำหรับแต่ละ surface หลักที่พวกเขาเป็นเจ้าของ

- **Product Management → Products → New** — สร้างสินค้าใหม่เดี่ยว (ปกติสำหรับ SKU ใหม่หรือการเปิดตัวเมนู)
- ~~**Product Management → Products → Import**~~ — **ไม่มีอยู่จริง** (แก้ไข 2026-09-22): toolbar ของ list มีแค่ **Export** (`useExportProduct`); ไม่มี route นำเข้าใน `config_products.controller.ts` หรือ Bruno collection
- **Product Management → Category** (`/product-management/category`) — สร้างหรือแก้ node การจำแนก (category, sub-category, item-group) ในหน้าจอต้นไม้ การเปลี่ยน cascading-default กระจายไปยังลูกที่การอ่านครั้งต่อไปตาม `PRD_CALC_002` / `PRD_CALC_003`
- **Configuration → Unit** (`/config/unit` ไม่ได้อยู่ใต้ Product Management) — สร้างหน่วย การแปลงหน่วยต่อสินค้านิยามบนแท็บ **Unit** ของฟอร์มสินค้า ไม่ใช่บนหน้าจอหน่วย
- **คิว Comment (ต่อสินค้าหรือ global)** — review และตอบ feedback ขาเข้าของ Purchaser / Store Keeper บนแคตตาล็อก

**Primary flow (สร้างสินค้าใหม่เดี่ยว 10 ขั้นตอน — เป็นตัวอย่างของรูปแบบ full-CRUD):**

1. **ตรวจสอบเงื่อนไขเบื้องต้น** ก่อนสร้างสินค้า ยืนยันห่วงโซ่การจำแนก (item-group เป้าหมาย sub-category parent ของมัน และ category ระดับบนสุด) มีอยู่และ `active` ถ้าไม่ สร้าง node หมวดหมู่ก่อน ยืนยันหน่วยฐานคลัง (`tb_unit`) มีอยู่และ conversion factor หน่วยสั่งซื้อ / หน่วยสูตรอาหารจะนิยามได้ ยืนยัน tax profile ตั้งบนอย่างน้อยหนึ่งระดับของห่วงโซ่การจำแนก (ตามการสืบทอด `PRD_CALC_002`) — มิฉะนั้นสินค้าจะสืบทอดอัตราภาษีที่มีผล 0%
2. **เปิด Products → New** Product Management → Products → New form เปิดที่ `tb_product` create mode พร้อมฟิลด์ว่างและ preview การสืบทอดปิด
3. **กรอก name (และ local name); `code` สร้างอัตโนมัติ** **แก้ไขในรอบนี้** — ตั้งแต่การเปลี่ยนแปลง frontend เมื่อ 2026-07-14 ฟิลด์ `code` ถูกล็อก (render เป็น disabled พร้อม placeholder "auto-generated") และถูกตัดออกจาก create payload ดังนั้น Product Administrator จึงไม่ต้องพิมพ์ code ผ่าน form นี้อีกต่อไป; backend กำหนด code แบบ running-number ให้ และความไม่ซ้ำภายใน `(code, name, deleted_at)` ตาม `PRD_VAL_001` ยังคงถูกบังคับใช้ที่ server-side แต่ไม่ใช่ scenario ที่การตรวจสอบ blur-time ของ form เองต้องป้องกันสำหรับฟิลด์ code อีกต่อไป `name` คือชื่อแสดงผลภาษาอังกฤษ / หลัก; `local_name` คือการแสดงผลท้องถิ่น (ไทย ฯลฯ) Description อิสระ
4. **เลือกหน่วยคลังฐาน** `inventory_unit_id` อ้างอิง `tb_unit` ที่ active สิ่งนี้ขับเคลื่อนทุกการคำนวณปลายน้ำ (balance, cost, valuation) และ **ไม่สามารถเปลี่ยนได้เมื่อสินค้ามีประวัติคลัง** ตาม `PRD_VAL_003` (design intent — ไม่พบการเช็คฝั่ง server) ดังนั้นทางเลือกมีผลกระทบ
5. **กำหนดการจำแนก** บนแท็บ **General** เลือก Category → Sub Category → Item Group ตามลำดับ — select ของหมวดหมู่ย่อยถูก disable จนกว่าจะเลือกหมวดหมู่ และ select ของกลุ่มสินค้าจนกว่าจะเลือกหมวดหมู่ย่อย (`pd-tab-general.tsx:288`, `:309`); ทั้งสามบังคับโดย Zod schema ของฟอร์ม (`types/product.ts`, `createProductSchema`) แม้จะส่งแค่ `product_item_group_id` ไปยัง API ฟอร์มแสดง tax profile ที่สืบทอดและค่าความคลาดเคลื่อนตาม `PRD_CALC_002` / `PRD_CALC_003`; Product Administrator อาจ override ที่ระดับสินค้า
6. **ตั้ง flag ของสินค้า** `is_used_in_recipe` และ `is_sold_directly` default ตามการสืบทอดของการจำแนก (`PRD_CALC_004`); override ถ้าสินค้าเฉพาะเบี่ยงจากธรรมเนียมหมวดหมู่ `barcode` และ `sku` เป็นทางเลือก; ถ้าตั้ง ความไม่ซ้ำของ `barcode` บังคับใช้ตาม `PRD_VAL_005`
7. **ตั้งฟิลด์ cost reference** `standard_cost` คือต้นทุน reference / มาตรฐานในหน่วยคลังฐาน (ตาม `PRD_VAL_007` ต้อง ≥ 0) ใช้โดยวิธี count-costing `standard` และโดย recipe baselining `price_deviation_limit` และ `qty_deviation_limit` ถูก bound `[0, 100]` ค่าความคลาดเคลื่อนเป็นเปอร์เซ็นต์ (ตาม `PRD_VAL_006`) และสืบทอดจากห่วงโซ่การจำแนกถ้าเป็นศูนย์; override ถ้าจำเป็น **ค่า standard-cost เกินเกณฑ์อาจ route ไปยัง Cost Controller สำหรับการอนุมัติตาม `PRD_AUTH_012`** — form ระบุสิ่งนี้ด้วยประกาศ
8. **นิยามการแปลงหน่วย** บนแท็บ **Unit** (`pd-tab-unit-conversion.tsx`) เพิ่มแถวสำหรับแต่ละหน่วยสั่งซื้อ (`unit_type = order_unit` เช่น `1 CASE = 12 EACH`) และแต่ละหน่วยสูตรอาหาร (`unit_type = ingredient_unit` เช่น `1 TBSP = 15 ML`) ที่สินค้าต้องการ; แถวถูกส่งเป็น `order_units` / `ingredient_units` `{ add, update, remove }` ตาม `PRD_VAL_010` แต่ละแถวมี qty บวกทั้งสองด้านและ from/to unit ต่างกัน; ตาม `PRD_VAL_011` ความสอดคล้องสองทิศทาง validate ข้ามชุด flag "default" (`is_default`) เลือก conversion ที่แสดงก่อนบน picker PR/PO/recipe
9. **ตั้งค่า location และ vendor mapping**
   - **Location assignment (`tb_product_location`):** บนแท็บ **Location Assignment** (`pd-tab-locations.tsx`; แท็บมี label ว่า *Location Assignment* ไม่ใช่ *Locations* และมี badge นับจำนวนแถว) เพิ่ม location และตั้ง `min_qty` / `max_qty` / `par_qty` และเลือกได้ว่าจะกำหนด **Shelf** จากข้อมูลหลักชั้นวาง (`LookupShelf` เฉพาะชั้นวางที่ active; picker รีเซ็ตเมื่อเปลี่ยน location) grid ไม่มีคอลัมน์ Reorder อีกต่อไป — `re_order_qty` ถูก API derive จาก on-hand เทียบกับ `max_qty` / `par_qty` ([01-data-model](/th/inventory/product/01-data-model) § 2.7) Product Administrator ทั้งสร้างแถวและตั้งค่าที่นี่ — ไม่มี surface "Inventory Controller" แยกต่างหาก แต่ละ `shelf_id` ถูกตรวจสอบฝั่ง server (`SHELF_NOT_FOUND`) ค่าศูนย์หมายถึง "ไม่ได้ตั้งค่า"
   - **Vendor mapping (`tb_product_tb_vendor`):** **ไม่อยู่บนฟอร์มสินค้า** — แท็บมีแค่ General / Unit / Location Assignment / Eco Labels (`pd-form.tsx:422-478`) junction มีอยู่ใน schema และมี API ของตัวเอง (Bruno `master-data/vendor-product/*` ห้า request) ดังนั้นตาม `PRD_VAL_013` แต่ละคู่ (`vendor_id`, `product_id`) ไม่ซ้ำ แต่ UI การ map ฝั่ง vendor มีเอกสารอยู่ใต้ [master-data/vendor](/th/inventory/master-data/vendor) / [vendor-pricelist](/th/inventory/vendor-pricelist) ไม่ใช่ที่นี่
10. **Save** Submit ถ้าฟิลด์บังคับใดขาดไป (name, local name, category, sub-category, item group, inventory unit, price ≥ 0) ฟอร์มแสดง toast แบบ **warning** "Some details are missing — jumped to the field to fix." ใส่จุดแดงบนแท็บที่มีปัญหา และสลับไปยังแท็บแรกที่มี error (`pd-form.tsx` `onInvalid`, การเปลี่ยน save-validation ของ frontend `2026-07-30`) เมื่อ submit ถูกต้อง payload เขียน `tb_product` ด้วย `product_status_type = active`, `is_active = true` พร้อมแถว `tb_unit_conversion` และ `tb_product_location` ที่เกี่ยวข้อง แล้ว navigate ไป `/product-management/product/:id` สินค้าปรากฏทันทีบนทุก picker ปลายน้ำ (ตาม `PRD_AUTH_009`); ไม่มีการแจ้งเตือนปล่อย

**ไม่มี flow bulk-import** (แก้ไข 2026-09-22 — ดู [02-business-rules](/th/inventory/product/02-business-rules) § 5.1); คำอธิบาย dry-run / strict-commit ที่เคยอยู่บนหน้านี้ไม่มีโค้ดรองรับ

flow **classification-change** (สร้างหรือแก้ category / sub-category / item-group) ตามขั้นตอน 2–10 แต่ที่ระดับต้นไม้ที่เกี่ยวข้อง ผลกระทบ cascading-default preview ก่อน save: การเปลี่ยน `tax_profile_id` ของ category เช่นกัน แสดงว่ามี sub-category / item-group / สินค้ากี่ตัวจะสืบทอดค่าใหม่ ตาม `PRD_LIFE_010` การเปลี่ยนเป็น **prospective** — เอกสารเปิดที่ snapshot tax-profile เก่าเก็บ snapshot

flow **lifecycle-transition** (เปิดใช้ ปิดใช้ soft-delete restore) ตาม state diagram ใน [03-user-flow.md](./03-user-flow.md) Section 2 Guard หลักคือ **การตรวจสอบ in-use**:

- **ปิดใช้** (`active → inactive`) — soft-block ถ้าถูกอ้างอิงโดยสูตรที่ publish (override ด้วยข้อความเหตุผล) Hard-block ถ้าบรรทัด PR / PO / SR เปิดใด ๆ อ้างอิงสินค้า
- **Soft-delete** (`active | inactive → soft-deleted`) — **ไม่มี guard ที่ implement ไว้ในวันนี้** (`delete()` ของ `products.service.ts`); การบล็อกจาก on-hand / เอกสาร / สูตรเป็น design intent การ drain คลังก่อนลบเป็นวินัยเชิงปฏิบัติการ ไม่ใช่สิ่งที่ระบบบังคับ
- **Restore** (`soft-deleted → active`) — ปฏิเสธถ้า `(code, name)` ถูก re-use โดยสินค้า live ในระหว่างนั้น

## 3. Decision Branch

- **สืบทอด vs override ที่ระดับการจำแนก** ธรรมเนียม default คือตั้ง tax profile และค่าความคลาดเคลื่อนที่ระดับ **category** และให้ item-group / สินค้าสืบทอด การ override ที่ระดับสินค้าสำรองไว้สำหรับข้อยกเว้นจริง (เช่นสินค้าเฉพาะมีอัตราภาษีต่างเนื่องจากกฎระเบียบท้องถิ่น หรือมี tolerance ราคาเข้มกว่าเนื่องจากปัญหาคุณภาพ vendor) form แสดงค่าที่สืบทอดในรูปแบบที่ grey-out; การแตะ override ทำให้พวกเขาแก้ได้
- **หน่วยใหม่ vs หน่วยที่มีอยู่** เมื่อสินค้าใหม่ต้องการหน่วยที่ไม่มีใน `tb_unit` (เช่น `PUNNET` สำหรับ SKU ผลผลิตใหม่) สร้างหน่วยก่อน (Units → New) แล้วสร้าง conversion factor ไปยังหน่วยคลังฐาน หลีกเลี่ยงหน่วย one-off ที่จะไม่ถูก reuse — ธรรมเนียมคือเก็บ `tb_unit` ให้บางและ reuse หน่วยมาตรฐาน (KG, LITRE, EACH, CASE, DOZEN, BOTTLE, BAG)
- **การแปลง order-unit vs ingredient-unit** ขอบเขตทั้งสองแชร์ตาราง `tb_unit_conversion`; แยกแยะผ่าน `enum_unit_type` การแปลง Order-unit อ่านโดย procurement / receiving / pricelist (การแปล qty บรรทัด PR / PO / GRN → หน่วยฐาน); การแปลง ingredient-unit อ่านโดย recipe (qty วัตถุดิบสูตร → หน่วยฐานสำหรับ theoretical consumption) การแปลงทางกายภาพเดียวกัน (`1 CASE = 12 EACH`) อาจมีเป็น **ทั้งสอง** แถว `order_unit` และแถว `ingredient_unit` ถ้าหน่วยเดียวกันใช้ในทั้งสองบริบท — นั่นจงใจเพื่อให้ namespace ทั้งสองเป็นอิสระ
- **Soft-delete vs hard-disable** flag สองตัวบรรลุผลลัพธ์คล้ายแต่ต่างกัน (ตาม `PRD_LIFE_005`):
  - `product_status_type = inactive` — สินค้าถูกลบจาก picker ธุรกรรมใหม่; admin ยังเห็น; **reversible** ผ่าน re-activation ใช้สำหรับ "ไม่ใช้ชั่วคราว" (item ตามฤดูกาลออกจากเมนู recall รอการเปิดตัวใหม่)
  - `is_active = false` — สินค้าซ่อนทุกที่รวม admin view; reversible โดยตั้ง flag ใหม่ ใช้สำหรับ "ควรมองไม่เห็นทุกคน" โดยไม่ soft-delete (เช่น compliance hold)
  - `soft-delete` (`deleted_at` ตั้ง) — terminal ในการใช้งานปกติ; เฉพาะ Auditor เห็นแถวที่ soft-deleted ใช้เมื่อสินค้าเลิกใช้จริงและ `(code, name)` ควรใช้งานได้ใหม่
- **การแก้ standard-cost route สำหรับการอนุมัติเกินเกณฑ์** ตาม `PRD_AUTH_012` การเปลี่ยน `standard_cost` เกินเกณฑ์ SoD ของ tenant (โดยทั่วไป 10–20% การเคลื่อนไหว ตั้งค่าได้) route การ update ไปยัง Cost Controller / Finance review ใต้เกณฑ์ การแก้เป็นทันที form แสดง threshold และการตัดสินใจ routing ก่อน submit
- **ไม่มี bulk import** การโหลดแคตตาล็อกขนาดใหญ่ทำผ่านการเรียก API โดยตรงในวันนี้ (`POST /api/config/:bu_code/products` ต่อแถว) — ไม่มี importer ให้ dry-run
- **ผลกระทบการจัดระเบียบการจำแนก** การย้ายสินค้าระหว่าง item-group (เปลี่ยน `product_item_group_id`) update default ที่สืบทอด prospectively (`PRD_LIFE_010`) เอกสารเปิดเก็บค่าที่ snapshot Product Administrator review preview ผลกระทบก่อน commit — สำหรับสินค้าบนเอกสาร active หลายตัวนี่หายากและรบกวน
- **การ escalation in-use guard** เมื่อการลบถูก hard-block โดย in-use guard Product Administrator ประสานกับเจ้าของเอกสาร (Purchaser สำหรับ PR / PO; Store Keeper สำหรับ SR / count; Chef สำหรับสูตร) เพื่ออย่างใดอย่างหนึ่งยกเลิก / void เอกสาร drain คลัง หรือยอมรับว่าสินค้าไม่สามารถลบได้ในขณะนี้ ไม่มีเส้นทาง override — guard เป็น absolute (`PRD_LIFE_004`)

## 4. Exit Point / Handoff

การมีส่วนร่วมของ Product Administrator บน surface แคตตาล็อกใดจบที่หนึ่งใน boundary เหล่านี้:

- **สินค้าสร้างและ active — handoff ไปยังผู้บริโภค** สินค้าใหม่ปรากฏบนทุก picker ปลายน้ำ; Purchaser และ Store Keeper เห็นทันที ไม่มีการแจ้งเตือนปล่อย; picker อ่านเมื่อต้องการ Product Administrator อาจ post comment "สินค้าใหม่พร้อมใช้" บนสินค้าหรือผ่านช่องการสื่อสารระดับ tenant เพื่อ flag ผู้บริโภคถ้าการเปิดตัวมีนัยสำคัญเชิงปฏิบัติการ
- **การเปลี่ยน standard-cost route สำหรับการอนุมัติ Cost Controller / Finance** การแก้เกินเกณฑ์ stage ใน activity log ตาม `PRD_AUTH_012`; Product Administrator รอ signature ที่สอง ในการอนุมัติ การเปลี่ยนเป็นสุดท้าย; ในการปฏิเสธ `standard_cost` เดิม restore และ Administrator iterate
- **การเปลี่ยนการจำแนก commit แล้ว — การกระจาย prospective** การกระจาย cascading-default เกิดที่เวลา next-read บนผู้บริโภคปลายน้ำแต่ละราย (line save ของ PR อ่าน tax profile ใหม่ที่มีผลตาม `PRD_CALC_002`); งานของ Product Administrator เสร็จที่ commit เอกสารเปิดที่ snapshot ค่าเก่าไม่ถูกแก้ retroactively
- **Soft-delete commit แล้ว — terminal** เมื่อ `deleted_at` ตั้ง สินค้าถูกลบจากทุกมุมมอง live Audit log เก็บ event การลบ; restore เป็นไปได้แต่โดยทั่วไปไม่ใช้ การมีส่วนร่วมของ Product Administrator จบ
- **Comment ขาเข้า resolve แล้ว** เมื่อ comment ของ Purchaser หรือ Store Keeper ได้รับ Product Administrator สอบสวน ทำ action ที่เหมาะสม (update master สร้างสินค้าใหม่ fix barcode ปรับ location-mapping) และตอบบน thread comment การ resolve ปิด thread
- **Export ดาวน์โหลดแล้ว** การ export รายการ (`useExportProduct`) เป็น surface แบบ bulk เพียงอย่างเดียว; ไม่มีงาน import ให้ปิด
- **นโยบาย Location อยู่กับ Product Administrator** — ทั้งการเปิดใช้สินค้าที่ location และการตั้งค่า min / max / par / reorder เกิดขึ้นบน Location Assignment tab เดียวกันของ product edit form; ไม่มี handoff ไปยังหน้าจอ Inventory Controller แยกต่างหาก (แก้ไขในรอบนี้ — ดู Section 1)

## 5. แหล่งอ้างอิง

- Parent overview: [03-user-flow.md](./03-user-flow.md) — canonical state machine ของ record สินค้า (Section 2) ที่เส้นทางของ persona นี้ traverse และตาราง handoff ข้าม persona ที่ anchor boundary Product Administrator → Cost Controller / Finance (`PRD_AUTH_012`, standard-cost SoD)
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ผู้บริโภคปลายน้ำที่อ่านแคตตาล็อกสำหรับการจัดทำ PR / PO
- Sibling: [03-user-flow-store-keeper.md](./03-user-flow-store-keeper.md) — persona ผู้บริโภคปลายน้ำที่อ่านแคตตาล็อก (barcode scan การอ้างอิงนโยบาย location) ระหว่างการรับ / หยิบ / นับ
- Sibling: [01-data-model.md](./01-data-model.md) — รูปทรง canonical `tb_product` (ขั้นตอน 3–7 ของ primary flow), ห่วงโซ่การจำแนก (`tb_product_category` / `tb_product_sub_category` / `tb_product_item_group`, ขั้นตอน 5), รูปทรง `tb_unit` และ `tb_unit_conversion` (ขั้นตอน 4 และ 8), `tb_product_location` / `tb_product_tb_vendor` (ขั้นตอน 9) และ `enum_product_status_type` (การเปลี่ยนวงจรชีวิต)
- Sibling: [02-business-rules.md](./02-business-rules.md) — กฎ validation (`PRD_VAL_001`–`PRD_VAL_018`) อ้างในขั้นตอน 3–10 ของ primary flow; กฎ calculation / inheritance (`PRD_CALC_001`–`PRD_CALC_010`) อ้างในขั้นตอน 1 (ตรวจสอบเงื่อนไขเบื้องต้น) และขั้นตอน 5 (การสืบทอดการจำแนก); กฎ authorization (`PRD_AUTH_001`–`PRD_AUTH_004`, `PRD_AUTH_012`) gate อำนาจของ Product Administrator; กฎ lifecycle (`PRD_LIFE_001`–`PRD_LIFE_010`) ควบคุมการเปลี่ยนสถานะที่ Section 1 ของหน้านี้อธิบาย; กฎข้ามโมดูล (`PRD_XMOD_001`–`PRD_XMOD_012`) นิยามวิธีที่แคตตาล็อกเชื่อมกับผู้บริโภค
- โมดูลที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — การ map `tb_product_location` เปิดสินค้าที่ location; ตัวเลขนโยบายการเติมสต๊อกตั้งค่าบน Location Assignment tab ของโมดูลเดียวกันนี้ (อำนาจของ Product Administrator — ดู Section 1) On-hand qty derive จาก cost-layer ledger (`PRD_CALC_009`) และแสดงบน tab location ของมุมมองรายละเอียดสินค้า
- ที่เกี่ยวข้อง: [costing](/th/inventory/costing) — `tb_product.standard_cost` คือแหล่งของ reference-cost; วิธี FIFO / WA cost-pick อยู่ที่ `tb_business_unit.calculation_method` ไม่ใช่บนสินค้า (ตาม [product/01-data-model](/th/inventory/product/01-data-model) § 5 รายการ 7) การเปลี่ยน standard-cost เกินเกณฑ์ SoD route สำหรับการอนุมัติ Cost Controller / Finance (`PRD_AUTH_012`)
- ที่เกี่ยวข้อง: [vendor-pricelist](/th/inventory/vendor-pricelist) — การ map `tb_product_tb_vendor` ทำให้สินค้าปรากฏบน vendor pricelist; บรรทัด pricelist อ้างอิง `tb_product` ผ่าน `product_id`
- ที่เกี่ยวข้อง: [recipe](/th/inventory/recipe) — สูตรที่ publish ที่อ้างอิงสินค้าบล็อกการปิดใช้ตาม `PRD_LIFE_002` (soft-block, override มี) และบล็อก soft-delete ตาม `PRD_LIFE_004` (hard-block, ไม่มี override)
- ที่เกี่ยวข้อง: [purchase-request](/th/inventory/purchase-request) / [purchase-order](/th/inventory/purchase-order) / [good-receive-note](/th/inventory/good-receive-note) / [store-requisition](/th/inventory/store-requisition) — เอกสารเปิดที่อ้างอิงสินค้าบล็อกการปิดใช้ / ลบตาม in-use guard
