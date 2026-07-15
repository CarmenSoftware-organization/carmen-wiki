---
title: สูตรอาหาร (Recipe)
description: สูตรอาหาร (รายการวัตถุดิบพร้อม yield) — สะพานเชื่อมระหว่างเมนูและการใช้คลังสินค้า
published: true
date: 2026-07-16T04:00:00.000Z
tags: recipe, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# สูตรอาหาร (Recipe)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** แคตตาล็อกสูตรการผลิตที่คิดต้นทุนแล้ว (การคิดต้นทุนระดับส่วนหัว, การอ้างอิง sub-recipe, prep-step API, แกลเลอรีรูปภาพ) ภายใต้ `/operation-plan/*` — ดีไซน์เป้าหมายขยายไปถึงการใช้วัตถุดิบเชิงทฤษฎีและความแปรปรวนของ food-cost เทียบกับยอดขาย POS (ยังไม่ได้ implement — ดูหมายเหตุสถานะด้านล่าง) &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Chef / Kitchen Manager, Cost Controller, Outlet Manager, F&B Operations, Procurement &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_recipe`, `tb_recipe_ingredient`, `tb_recipe_preparation_step`, `tb_recipe_image`, `tb_recipe_yield_variant`, `tb_recipe_version`, `tb_recipe_pricing_history` &nbsp;·&nbsp; **หน้าย่อย:** 18

![สูตรอาหาร (Recipe) screen](/screenshots/recipe/index.png)

![สูตรอาหาร (Recipe) detail screen](/screenshots/recipe/detail.png)

> **สถานะการ implement (ตรวจสอบกับซอร์สโค้ด 2026-07-15)** สิ่งที่ใช้งานได้จริงวันนี้คือ **recipe catalogue ระดับส่วนหัว**: list/detail/create/edit/delete ที่ `/operation-plan/recipe` รองรับโดย `POST/PUT/PATCH/DELETE /api/config/{bu_code}/recipes` (gateway `config_recipes.controller.ts` → micro-business `recipe.service.ts`) บวกรูปภาพสูตร (แกลเลอรี multipart), endpoint REST ของขั้นตอนเตรียม (`.../recipes/:recipe_id/preparation-steps` — มีเฉพาะ API ยังไม่มี UI ในฟอร์มสูตร) และหน้าจอ master data สี่หน้า (category, cuisine, equipment, equipment category) ส่วน ingredient grid บนฟอร์มสูตรเป็น **preview เท่านั้น** อย่างชัดเจน ("Preview only — ingredients are not yet persisted with the recipe", `messages/en.json` `ingredientsPreviewNote`) และไม่มี endpoint เขียนวัตถุดิบใน backend `tb_recipe_version`, `tb_recipe_pricing_history` และ `tb_recipe_yield_variant` มีอยู่ใน schema แต่วันนี้ยังไม่มี service ใดเขียนลงตารางเหล่านี้ ส่วน menu-item linkage, การใช้วัตถุดิบเชิงทฤษฎี, POS explosion, ความแปรปรวน food-cost, การ cascade ต้นทุนของ sub-recipe และ store requisition ที่ขับเคลื่อนโดยสูตร **ไม่มีโค้ดที่ไหนเลย** ทั้งใน frontend และ backend — section ด้านล่างที่บรรยายสิ่งเหล่านี้เป็นการบันทึกแนวคิดดีไซน์จาก `../carmen/docs/` ไม่ใช่พฤติกรรมปัจจุบัน

## 1. ภาพรวม

**สูตรอาหาร (Recipe)** คือสูตรมาตรฐานที่คิดต้นทุนสำหรับการผลิตอาหารหรือเครื่องดื่มหนึ่งหน่วยเอาท์พุต แต่ละสูตรมีส่วนหัว (ชื่อและรหัสสูตร หมวดหมู่ ประเภทอาหาร ประเภทคอร์ส yield พร้อมปริมาณและหน่วย เวลาเตรียม เวลาปรุง ระดับความยาก สารก่อภูมิแพ้ tag สถานะ) และบรรทัดวัตถุดิบหนึ่งบรรทัดหรือมากกว่าที่ระบุสินค้าหรือ sub-recipe ปริมาณที่ต้องการ หน่วยสูตรอาหาร หน่วยสต๊อก เปอร์เซ็นต์ wastage ต้นทุนต่อหน่วย และต้นทุนรวมต่อบรรทัด ขั้นตอนการเตรียม — เรียงลำดับ มีรูปภาพ ระยะเวลา และอุปกรณ์เป็นทางเลือก — อยู่ข้างรายการวัตถุดิบและทำให้สูตรเป็นเอกสารการผลิตที่สมบูรณ์ไม่ใช่แค่ใบคิดต้นทุน สูตรมีสถานะสามสถานะ (`DRAFT` / `PUBLISHED` / `ARCHIVED`, `enum_recipe_status`) การเปลี่ยนสถานะเป็น dropdown ธรรมดาบน toolbar ของสูตร (`recipe-toolbar.tsx`) โดยไม่มีการตรวจความครบถ้วน และ backend ประทับ `published_at` / `archived_at` อัตโนมัติเมื่อเปลี่ยนสถานะ (`recipe.service.ts`) การจัดเวอร์ชันการเปลี่ยนแปลงแบบเต็มเป็นดีไซน์ระดับ schema (`tb_recipe_version`) ที่ยังไม่มีตัวเขียนถูก implement — audit trail ปัจจุบันคือคอลัมน์ `created_*` / `updated_*` มาตรฐานบวก optimistic locking ด้วย `doc_version`

วัตถุดิบสามารถเป็นได้ทั้ง **สินค้า** ที่ดึงจากแคตตาล็อกคลังสินค้าหรือ **sub-recipe** — สูตรที่ publish แล้วอื่นที่ใช้เป็นส่วนประกอบของสูตรหลัก ("mother sauce" ที่ใช้ในเมนูหลักสามจาน base ขนมที่ใช้ในของหวานสองรายการ) นี่คือโมเดลสอง FK ของ `tb_recipe_ingredient` (`product_id` / `sub_recipe_id` พร้อม discriminator `enum_ingredient_type`) และกฎ sub-recipe เดียวที่บังคับในโค้ดวันนี้คือ delete guard — สูตรที่ถูกอ้างอิงเป็น sub-recipe จะลบไม่ได้ (`RECIPE_USED_AS_SUB_RECIPE`, `recipe.service.ts`) ส่วนการคิดต้นทุนสูตรแม่ใหม่อัตโนมัติเมื่อต้นทุนของ sub-recipe เปลี่ยนเป็นเป้าหมายดีไซน์ที่ยังไม่มีการ implement สูตรอาหารถูกแยกอย่างจงใจจาก **menu item**: สูตรคือสูตรการผลิตและแหล่งความจริงสำหรับต้นทุน menu item คือรายการที่ขายได้บน POS ซึ่งเชื่อมไปยังสูตรหนึ่งหรือหลายสูตร (และไปยัง add-on, modifier และการกำหนดราคา) สูตรหนึ่งสามารถรองรับ menu item หลายรายการได้ (สูตร "House Burger" เดียวขายเป็นทั้งเดี่ยวและเป็นชุดคอมโบ) menu item หนึ่งสามารถประกอบจากหลายสูตร ("Steak Plate" ที่รวมสูตรสเต็ก sub-recipe ของซอส และสูตรเครื่องเคียง)

ในดีไซน์เป้าหมาย (`../carmen/docs/recipe-module/`) สูตรอาหารเป็นสะพานเชื่อมระหว่างยอดขายเมนูและการใช้คลังสินค้า: เมื่อ menu item ถูกขาย ระบบจะ explode สูตรที่เชื่อมไว้แต่ละตัวด้วยปริมาณที่ขาย คูณผ่านบรรทัดวัตถุดิบ (ใช้ wastage และการแปลงหน่วย) และ post **การใช้วัตถุดิบเชิงทฤษฎี** ที่ได้เป็น stock OUT movement ต่อ inventory ของ outlet ขับเคลื่อนรายงาน food-cost การวิเคราะห์ความแปรปรวนทฤษฎีกับจริง และ store requisition ที่สร้างจากสูตร **pipeline ทั้งหมดนี้ยังไม่มีในโค้ดวันนี้** — ไม่มีตาราง menu item ไม่มีการเชื่อมต่อ POS ไม่มีการเขียนการใช้วัตถุดิบเชิงทฤษฎี และไม่มีการสร้างสูตร→SR ที่ไหนเลยใน `carmen-turborepo-backend-v2` หรือ frontend โมดูล recipe ปัจจุบันจบที่ตัวเรคคอร์ดสูตรที่คิดต้นทุนแล้วนั่นเอง

## 2. บริบททางธุรกิจ

ในการดำเนินงานโรงแรม สูตรอาหารคือสิ่งประดิษฐ์เดียวที่ผูกสิ่งที่ครัวผลิต ต้นทุน และคลังที่ใช้ไว้ด้วยกัน ถ้าไม่มีสูตรมาตรฐาน สามสิ่งจะพัง: พนักงานครัวเตรียมจานเดียวกันต่างกันในแต่ละกะและแต่ละ outlet ทำให้คุณภาพและสัดส่วนไม่สอดคล้องกัน ต้นทุนต่อ portion ไม่สามารถรู้ได้ ดังนั้นการตั้งราคาเมนูกลายเป็นการเดาและกำไรถูกบั่นทอน และคลังไม่สามารถหักลบจากยอดขายได้ ดังนั้นรายงานความแปรปรวน food-cost จึงไม่มีความหมาย สูตรอาหารมาตรฐานที่คิดต้นทุนแล้วคือรากฐานที่ทำให้การดำเนินงาน F&B ทำงานบนตัวเลขมากกว่าสัญชาตญาณ

โมดูลนี้ถูกสร้างรอบ ๆ **food cost engineering** — วินัยของการออกแบบแต่ละจานให้เข้าเป้าหมายเปอร์เซ็นต์ food-cost ในขณะที่รักษาคุณภาพ การจัดจาน และความสอดคล้อง Cost Controller ตั้งเปอร์เซ็นต์ food-cost เป้าหมาย (โดยทั่วไป 28–35% สำหรับ casual dining ต่ำกว่าสำหรับ fine dining) ระบบคำนวณราคาขายที่แนะนำจาก `Cost Per Portion / (1 − Target Food Cost%)` และ gross margin ออกมาเป็น `(Selling Price − Cost Per Portion) / Selling Price` เมื่อราคาของวัตถุดิบเคลื่อนไหว — ขับเคลื่อนโดยการอัปเดต procurement จาก vendor pricelist และการ post GRN — สูตรคิดต้นทุนใหม่แบบ real time แสดงเมนูที่ margin เลื่อนออกนอกเกณฑ์และ flag เพื่อ review ก่อนการรีเฟรชเมนูครั้งต่อไป

ฟังก์ชันทางธุรกิจหลักอีกอย่างที่โมดูลรองรับคือ **การวิเคราะห์ความแปรปรวนทฤษฎีกับจริง** การใช้วัตถุดิบเชิงทฤษฎีคือสิ่งที่สูตรบอกว่าควรถูกใช้เพื่อผลิตยอดขายของวัน (ยอดขาย POS × บรรทัดวัตถุดิบของสูตร × wastage) การใช้จริงคือสิ่งที่ข้อมูลการนับสต๊อกและ store requisition แสดงว่าถูกดึงออกจากคลังจริง ความแปรปรวนระหว่างทั้งสองคือ KPI food-cost ที่สำคัญที่สุดอันเดียวของการดำเนินงาน: ความแปรปรวนบวกที่ยังคงอยู่ชี้ไปที่ over-portioning การโจรกรรม การเสีย หรือ sub-recipe ที่ไม่ถูกต้อง ความแปรปรวนลบที่ยังคงอยู่ชี้ไปที่สูตรผิดหรือการ portion น้อยเกินไป ความถูกต้องของสูตร — yield, wastage, การแปลงหน่วย — จึงไม่ใช่แค่เรื่องของครัวแต่เป็นเรื่องการควบคุมทางการเงิน (ฟังก์ชันความแปรปรวนทั้งหมดนี้อยู่ในขั้นดีไซน์: ไม่มีการคำนวณความแปรปรวน POS feed หรือการเขียนการใช้วัตถุดิบเชิงทฤษฎีใน codebase ปัจจุบัน — ดูหมายเหตุสถานะการ implement ด้านบน)

## 3. แนวคิดสำคัญ

- **Recipe Header**: metadata ระดับบนสุดสำหรับสูตร — รหัส ชื่อ คำอธิบาย โน้ต หมวดหมู่ cuisine yield (`base_yield` + `base_yield_unit`) เวลาเตรียม เวลาปรุง ระดับความยาก (`EASY`/`MEDIUM`/`HARD`) สารก่อภูมิแพ้ tag สถานะ (`DRAFT`/`PUBLISHED`/`ARCHIVED`) รูปภาพหลัก (ผ่าน `tb_recipe_image`) carbon footprint และ flag `deduct_from_stock` ไม่มี `course_type` และไม่มี `total_time` ที่ persist ใน schema ส่วนหัวเป็นสิ่งที่ปรากฏใน recipe library ขับเคลื่อนการกรองและการค้นหา (ตัวกรอง status, cuisine, category, difficulty บนหน้าจอ list) และมีตัวเลขต้นทุน/ราคา (cost per portion, selling price, gross margin) สำหรับสูตรโดยรวม
- **Ingredient**: รายการบรรทัดในสูตรที่ระบุสิ่งที่ใส่ในเมนู ใน schema (`tb_recipe_ingredient`) วัตถุดิบแต่ละตัวมี type (`product` สำหรับรายการคลังหรือ `recipe` สำหรับ sub-recipe) ปริมาณ หน่วยสูตรอาหาร หน่วยสต๊อก conversion factor ระหว่างสอง เปอร์เซ็นต์ wastage ต้นทุนต่อหน่วย และ `net_cost` / `wastage_cost` ที่คำนวณ **วันนี้ยังไม่มีเส้นทางเขียนสำหรับตารางนี้** — ingredient grid บนฟอร์มสูตรเป็นตาราง local แบบ preview เท่านั้น (ชื่อ, qty, หน่วย, ต้นทุน, yield %, prep notes) ที่ไม่ถูกส่งไปกับ payload ตอนบันทึก และไม่มี ingredient endpoint ใน gateway หรือ Bruno collections
- **Sub-Recipe (Recipe-as-Ingredient)**: สูตรที่ publish แล้วที่ใช้เป็นวัตถุดิบในสูตรอื่น — mother sauce, สต็อก, base ขนม, ส่วนผสมเครื่องเทศ — ผ่าน `tb_recipe_ingredient.sub_recipe_id` delete guard ถูก implement แล้ว (`RECIPE_USED_AS_SUB_RECIPE`) ส่วนการคิดต้นทุนสูตรแม่ใหม่อัตโนมัติเมื่อต้นทุนของ sub-recipe เปลี่ยนยังอยู่ในขั้นดีไซน์เท่านั้น
- **Yield**: ปริมาณเอาท์พุตที่การรันสูตรหนึ่งครั้งผลิต แสดงเป็นตัวเลขบวกกับหน่วย (`base_yield` + `base_yield_unit` เช่น `12 portions`, `2.5 kg`) yield ขับเคลื่อน cost-per-portion (`Total Cost / Yield` — คำนวณฝั่ง client ใน `use-recipe-cost-calc.ts`) ไม่มีเครื่องคิดเลข scaling และไม่มีฟิลด์ปริมาณเริ่มต้น/หลังเตรียม/เปอร์เซ็นต์ recovery ใน schema หรือ UI ปัจจุบัน
- **Wastage Percentage**: การเสียจากการตัด ปอก ระเหย หรือหก ที่คาดหวังต่อวัตถุดิบ แสดงเป็นเปอร์เซ็นต์ ต้นทุนสุทธิต่อวัตถุดิบคือ `Unit Cost × Quantity × (1 + Wastage%)` wastage เป็นการตั้งค่าต่อบรรทัดเพราะวัตถุดิบต่าง ๆ มี profile การเสียที่ต่างกันมาก — ปลาแซลมอนตัวเต็มใช้ได้ 60% ถุงแป้งใช้ได้ 100% — และการ roll-up ตามวัตถุดิบเป็นวิธีเดียวที่ทำให้ต้นทุนสูตรสะท้อนความจริง
- **Recipe Cost (Total / Per Portion)**: ในฟอร์มปัจจุบัน `total_ingredient_cost`, `labor_cost` และ `overhead_cost` เป็นฟิลด์ส่วนหัวที่ **กรอกด้วยมือ** (`recipe-cost-breakdown.tsx`) ฟอร์มคำนวณ **Cost Per Portion** เป็น `(total_ingredient_cost + labor_cost + overhead_cost) / base_yield` ฝั่ง client (`use-recipe-cost-calc.ts`) และเก็บผลลัพธ์ ไม่มีการคิดต้นทุนใหม่อัตโนมัติจากการเปลี่ยนราคาในแคตตาล็อก — ingredient grid ไม่ได้ป้อนค่าเข้า `total_ingredient_cost`
- **Target Food Cost % and Selling Price**: เปอร์เซ็นต์ food-cost เป้าหมายถูกตั้งต่อสูตรหรือต่อหมวดหมู่ (โดยทั่วไป 28–35% ใน casual dining) **Recommended Selling Price** คือ `Cost Per Portion / (1 − Target Food Cost%)` ราคาขายจริงอาจต่างไป (เช่น สำหรับกลยุทธ์การตั้งราคาเมนู การ match คู่แข่ง) และระบบติดตามทั้งสองข้างพร้อม **Gross Margin %** ที่ได้ = `(Selling Price − Cost Per Portion) / Selling Price × 100`
- **Preparation Step**: คำสั่งตามลำดับในวิธีการ (`tb_recipe_preparation_step`) มี `sequence_no`, `title` ทางเลือก, `description` ที่จำเป็น, `duration` ทางเลือก, `temperature` + หน่วย, JSON array ของ `equipment` / `techniques`, `chef_notes`, `safety_warnings` และรูปภาพผ่าน `tb_recipe_preparation_step_image` มี endpoint REST CRUD เต็ม + reorder + รูปภาพ (`.../recipes/:recipe_id/preparation-steps`) แต่ฟอร์มสูตรยังไม่มี UI แก้ไขขั้นตอน — วันนี้ขั้นตอนมีเฉพาะทาง API เท่านั้น
- **Theoretical Consumption** *(แนวคิดดีไซน์ — ยังไม่ implement)*: คลังที่ยอดขายของเมนู *ควรจะ* ดึงลงตามสูตร คำนวณเป็น `Σ over sold menu items (sold_qty × recipe_ingredient_qty × (1 + wastage%) × unit_conversion)` ไม่มี POS feed หรือการเขียน theoretical OUT ในโค้ด
- **Actual Consumption** *(แนวคิดดีไซน์สำหรับคู่การวิเคราะห์ความแปรปรวน)*: คลังที่ครัวดึงลงจริง derive จากการ post การนับสต๊อก store requisition และการเบิกตรง — movement เหล่านี้มีจริงในโมดูล [inventory](/th/inventory/inventory) แต่ยังไม่มีการเปรียบเทียบความแปรปรวนฝั่ง recipe ที่บริโภคข้อมูลเหล่านี้
- **Variance (Theoretical − Actual)** *(แนวคิดดีไซน์ — ยังไม่ implement)*: ช่องว่างระหว่างสิ่งที่สูตรบอกว่าถูกใช้และสิ่งที่ stock movement บอกว่าถูกใช้ ไม่มีการคำนวณหรือรายงานความแปรปรวนใน codebase ปัจจุบัน
- **Menu Item Linkage** *(แนวคิดดีไซน์ — ยังไม่ implement)*: การ map จาก menu item ที่ขายได้บน POS ไปยังสูตร ไม่มีตาราง menu item ใน tenant schema และไม่มีโค้ด linkage
- **Version History** *(schema เท่านั้น)*: `tb_recipe_version` โมเดล snapshot เต็ม (`recipe_data`, `ingredients_data`, `steps_data`, `variants_data`, `change_summary`) แต่วันนี้ยังไม่มี service เขียนหรืออ่านตารางนี้ audit trail ที่ใช้งานจริงคือคอลัมน์ `created_*` / `updated_*` และ optimistic locking ด้วย `doc_version`
- **Status Lifecycle (`DRAFT` / `PUBLISHED` / `ARCHIVED`)**: สูตรเริ่มต้นใน `DRAFT` (ค่า default ของ backend) สถานะเป็น dropdown อิสระบน toolbar — backend **ไม่มีการตรวจความครบถ้วน** ตอนเปลี่ยนสถานะ ทำเพียงประทับ `published_at` อัตโนมัติเมื่อสถานะเปลี่ยนเป็น `PUBLISHED` และ `archived_at` เมื่อเปลี่ยนเป็น `ARCHIVED` (`recipe.service.ts` `update()`/`patch()`)
- **Category and Cuisine Type**: ข้อมูลหลักประเภทที่ใช้จัดระเบียบ recipe library — `Category` (เป็นลำดับชั้น เช่น Appetiser, Main, Dessert) และ `Cuisine` (แบน มี tag ภูมิภาค เช่น ไทย อิตาเลียน ฝรั่งเศส) ทั้งสองเป็น FK ที่จำเป็นบนส่วนหัวสูตร หมวดหมู่มี JSON `default_cost_settings` / `default_margins` ที่ตั้งใจไว้เป็นค่าตั้งต้นสำหรับสูตรใหม่
- **Allergens and Tags**: JSON array ต่อสูตร ฟอร์มมี checklist สารก่อภูมิแพ้มาตรฐาน (`ALLERGEN_OPTIONS` ใน `constant/recipe.ts`) บวกสารก่อภูมิแพ้ custom แบบ free-text และ tag แบบ free-text
- **Stock Deduction Setting**: boolean เดียว `deduct_from_stock` บนส่วนหัว (default `true`) แก้ไขเป็น switch บน hero section ของฟอร์ม matrix นโยบายหักเมื่อขาย/ผลิต/เบิกที่ละเอียดกว่าตามที่บรรยายใน carmen/docs ไม่มีอยู่ใน schema
- **Carbon Footprint**: เลขทศนิยมต่อสูตรที่กรอกด้วยมือ (`carbon_footprint`, default 0) ไม่มีการ rollup footprint ต่อวัตถุดิบ

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Chef / Kitchen Manager | สร้างสูตรใหม่และปรับปรุงสูตรเดิม — นิยามวัตถุดิบ ปริมาณ wastage วิธี yield อุปกรณ์ เวลาเตรียมและเวลาปรุง ดูแล sub-recipe และทำให้สอดคล้องกันทั่ว outlet อนุมัติการ publish สูตรและการปรับปรุง และตั้งมาตรฐานการจัดจาน การ portion และคุณภาพ |
| Cost Controller | review ต้นทุนสูตร เปอร์เซ็นต์ food-cost เป้าหมาย ราคาขายที่แนะนำ และ gross margin ติดตามการเลื่อนของต้นทุนเมื่อราคาวัตถุดิบเคลื่อน flag สูตรที่ margin ตกลงนอกเกณฑ์ เซ็นอนุมัติการเปลี่ยนแปลงต้นทุนสูตรที่กระทบราคาเมนู และรันรายงานความแปรปรวนทฤษฎีกับจริง |
| Outlet Manager | สั่งวัตถุดิบจากคลังกลางตาม demand ของสูตร (มักผ่าน store requisition อัตโนมัติที่ขนาดตามยอดขายคาดการณ์ × สูตร) ติดตามความแปรปรวน food-cost ของ outlet เทียบกับงบประมาณ review สูตรที่ใช้ใน outlet และส่ง feedback ปัญหาการควบคุม portion หรือความถูกต้องของสูตรให้ Chef |
| Kitchen Staff | อ่านสูตรที่ publish แล้วระหว่างบริการ — ทำตามรายการวัตถุดิบ วิธี อุปกรณ์ และการจัดจานเพื่อเตรียมเมนูให้สอดคล้องกัน อาจรายงานการรันสูตรและ flag ความไม่ถูกต้อง (ปริมาณผิด ขั้นตอนขาด) กลับไปให้ Chef เข้าถึงสูตรบนอุปกรณ์มือถือในครัว |
| Cost Control Department | เจ้าของกระบวนการคิดต้นทุนสูตรที่ระดับ portfolio — ตั้งเปอร์เซ็นต์ food-cost เป้าหมายระดับหมวดหมู่ กระทบยอดความแปรปรวนของ outlet กับ GL รันการ review ต้นทุนรายเดือน และขับเคลื่อน workflow การอนุมัติการจัดเวอร์ชันสูตรเมื่อราคาวัตถุดิบเลื่อนอย่างมีนัยสำคัญ |
| Procurement Department | บริโภค demand ของสูตรเพื่อแจ้งการจัดซื้อ — ใช้ recipe explosion × ยอดขายคาดการณ์เพื่อกำหนดขนาด PO และตรวจสอบว่าการมีอยู่ของวัตถุดิบตรงกับความต้องการของสูตร รับคำขอทดแทนเมื่อหาวัตถุดิบไม่ได้ |
| F&B Operations Manager | เจ้าของ recipe library ที่ระดับกลยุทธ์ — อนุมัติ menu item ใหม่และการ link สูตร เซ็นอนุมัติ menu engineering กับข้อมูล margin และความแปรปรวน และทำให้เอกสารสูตรรองรับการอบรมและการตรวจสอบ |
| System Administrator | จัดการการตั้งค่าโมดูล recipe — หมวดหมู่ ประเภทอาหาร การตั้งค่าต้นทุน default สิทธิ์ตาม role สำหรับการสร้าง/แก้ไข/อนุมัติสูตร และการตั้งค่าการเชื่อมต่อกับคลัง POS และ procurement |

> **RBAC reality check:** frontend ปัจจุบัน gate กลุ่ม `/operation-plan/*` ทั้งหมดไว้หลัง permission placeholder ฝั่ง frontend ตัวเดียวคือ `operation_plan.view` (`constant/permissions.ts` — มี comment ว่า "BE catalog ยังไม่มี operation_plan namespace") ซึ่งในทางปฏิบัติหมายถึงทุกหน้าจอ recipe เข้าถึงได้เฉพาะ admin ความสามารถต่อ role ในตารางนี้ (การอนุมัติ publish การเซ็นอนุมัติต้นทุน การเข้าถึงอ่านอย่างเดียวของ outlet) ยังไม่มีตัวใดถูกแยกแยะด้วย permission check ใด ๆ ในวันนี้ ตารางนี้บันทึกโมเดลการดำเนินงานเป้าหมายจาก `../carmen/docs/`

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [product](/th/inventory/product) — บรรทัดวัตถุดิบของสูตรอ้างอิงสินค้าใน schema (`tb_recipe_ingredient.product_id`) ยังไม่มีเส้นทางเขียนที่ใช้งานจริง
- [inventory](/th/inventory/inventory) — ดีไซน์เป้าหมาย: การใช้สูตรขับเคลื่อน inventory OUT movement (การใช้วัตถุดิบเชิงทฤษฎี — ยังไม่ implement)
- [costing](/th/inventory/costing) — ดีไซน์เป้าหมาย: ต้นทุนสูตรมาจาก valuation ของวัตถุดิบที่คิดต้นทุน (ปัจจุบันกรอกด้วยมือบนส่วนหัว)
- [store-requisition](/th/inventory/store-requisition) — ดีไซน์เป้าหมาย: สูตรสร้าง requisition อัตโนมัติ (ยังไม่มีโค้ดดังกล่าว)

**Master configuration:**
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยสูตรและหน่วยสต๊อก พร้อม conversion factor ต่อวัตถุดิบ
- [master-data/currency](/th/inventory/master-data/currency) — ต้นทุนสูตรและราคาขายแสดงในสกุลเงินฐานของ property
- [system-config/application-config](/th/inventory/system-config/application-config) — ค่า default ระดับ tenant (เปอร์เซ็นต์ food-cost เป้าหมาย การปัดเศษ นโยบายสถานะ)
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — event การสร้าง/อัปเดต/ลบสูตรใน activity log ที่ใช้ร่วมกัน
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — รูปภาพแกลเลอรีสูตร (`tb_recipe_image`) และรูปขั้นตอน (`tb_recipe_preparation_step_image`) ผ่าน file token

## 6. แหล่งอ้างอิง

- Concepts (PRD/requirements): `../carmen/docs/recipe-module/`
- Concepts (UI/page specs): `../carmen/docs/recipe/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — โมเดลข้อมูล](/th/inventory/recipe/01-data-model) — เอนทิตี Prisma (`tb_recipe`, `tb_recipe_ingredient`, `tb_recipe_preparation_step`, `tb_recipe_yield_variant`, `tb_recipe_version`, `tb_recipe_pricing_history`, `tb_recipe_category`, `tb_recipe_cuisines`, master ของอุปกรณ์), enum (`enum_recipe_status`, `enum_recipe_difficulty`, `enum_ingredient_type`, `enum_temperature_unit`, `enum_cuisine_region`), ความสัมพันธ์ (self-relation ของ sub-recipe โมเดลวัตถุดิบสองหน่วย) และจุดที่ต่างจาก carmen/docs
- [02 — กติกาทางธุรกิจ](/th/inventory/recipe/02-business-rules) — การตรวจสอบความถูกต้อง (`REC_VAL_*`), การคำนวณ (`REC_CALC_*`, ห่วงโซ่ line → recipe → portion → price → margin, การ cascade ของ sub-recipe), การกำหนดสิทธิ์ (`REC_AUTH_*`), การ posting (`REC_POST_*`, event การ publish / edit-published / cascade / archive) และกฎข้ามโมดูล (`REC_XMOD_*`)
- [03 — User Flow](/th/inventory/recipe/03-user-flow) — ภาพรวมวงจรชีวิตของสูตรและไฟล์ flow เฉพาะ persona:
  - [Chef](/th/inventory/recipe/03-user-flow-chef) — Chef / Kitchen Manager (+ Kitchen Staff อ่านอย่างเดียว): สร้าง ปรับปรุง publish archive
  - [Cost Controller](/th/inventory/recipe/03-user-flow-cost-controller) — Cost Controller (+ Cost Control Department): review ต้นทุน เซ็นอนุมัติ ติดตามการเลื่อน รันความแปรปรวน
  - [Outlet Manager](/th/inventory/recipe/03-user-flow-outlet-manager) — Outlet Manager: ผู้บริโภคด้าน demand ตั้ง SR จาก demand ของสูตร feedback ปัญหา
  - [Procurement / F&B Ops](/th/inventory/recipe/03-user-flow-procurement-fb-ops) — Procurement (การกำหนดขนาด PO การทดแทน) + F&B Ops (การอนุมัติ menu item linkage, menu engineering)
  - [Audit / Config](/th/inventory/recipe/03-user-flow-audit-config) — Sysadmin (config, RBAC, tenant policy, integration) + Auditor (อ่านอย่างเดียวสำหรับ versioning trace)
- [04 — Test Scenarios](/th/inventory/recipe/04-test-scenarios) — scenario ข้าม persona + สถานะการครอบคลุม E2E (ยังไม่มี `recipe.spec.ts` เฉพาะ; E2E spec เดียวของโมดูลคือ `121-recipe-equipment-category.spec.ts`) พร้อมการเจาะลึกต่อ persona:
  - [Chef scenarios](/th/inventory/recipe/04-test-scenarios-chef)
  - [Cost Controller scenarios](/th/inventory/recipe/04-test-scenarios-cost-controller)
  - [Outlet Manager scenarios](/th/inventory/recipe/04-test-scenarios-outlet-manager)
  - [Procurement / F&B Ops scenarios](/th/inventory/recipe/04-test-scenarios-procurement-fb-ops)
  - [Audit / Config scenarios](/th/inventory/recipe/04-test-scenarios-audit-config)
- หน้าย่อย master data (หน้าจอตั้งค่า Operation Plan):
  - [Recipe Category](/th/inventory/recipe/category) — taxonomy แบบลำดับชั้น (`tb_recipe_category`), `/operation-plan/category`
  - [Cuisine](/th/inventory/recipe/cuisine) — แคตตาล็อกแบบแบนที่ tag ภูมิภาค (`tb_recipe_cuisines`), `/operation-plan/cuisine`
  - [Equipment](/th/inventory/recipe/equipment) — master อุปกรณ์ครัว (`tb_recipe_equipment`), `/operation-plan/equipment`
  - [Equipment Category](/th/inventory/recipe/equipment-category) — การจัดกลุ่มอุปกรณ์แบบแบน (`tb_recipe_equipment_category`), `/operation-plan/equipment-category` (บวกหน้าจอซ้ำ `/operation-plan/recipe-equipment-category` ที่ชี้ตารางเดียวกัน)
