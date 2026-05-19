---
title: สูตรอาหาร (Recipe)
description: สูตรอาหาร (รายการวัตถุดิบพร้อม yield) — สะพานเชื่อมระหว่างเมนูและการใช้คลังสินค้า
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# สูตรอาหาร (Recipe)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** สูตรการผลิตที่คิดต้นทุนและจัดเวอร์ชัน (พร้อม sub-recipe, yield, wastage, prep steps) ที่ขับเคลื่อนการใช้วัตถุดิบเชิงทฤษฎีและความแปรปรวนของ food-cost เทียบกับยอดขาย POS &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Chef / Kitchen Manager, Cost Controller, Outlet Manager, F&B Operations, Procurement &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_recipe`, `tb_recipe_ingredient`, `tb_recipe_preparation_step`, `tb_recipe_yield_variant`, `tb_recipe_version`, `tb_recipe_pricing_history` &nbsp;·&nbsp; **หน้าย่อย:** 18

![สูตรอาหาร (Recipe) screen](/screenshots/recipe/index.png)

## 1. ภาพรวม

**สูตรอาหาร (Recipe)** คือสูตรมาตรฐานที่คิดต้นทุนสำหรับการผลิตอาหารหรือเครื่องดื่มหนึ่งหน่วยเอาท์พุต แต่ละสูตรมีส่วนหัว (ชื่อและรหัสสูตร หมวดหมู่ ประเภทอาหาร ประเภทคอร์ส yield พร้อมปริมาณและหน่วย เวลาเตรียม เวลาปรุง ระดับความยาก สารก่อภูมิแพ้ tag สถานะ) และบรรทัดวัตถุดิบหนึ่งบรรทัดหรือมากกว่าที่ระบุสินค้าหรือ sub-recipe ปริมาณที่ต้องการ หน่วยสูตรอาหาร หน่วยสต๊อก เปอร์เซ็นต์ wastage ต้นทุนต่อหน่วย และต้นทุนรวมต่อบรรทัด ขั้นตอนการเตรียม — เรียงลำดับ มีรูปภาพ ระยะเวลา และอุปกรณ์เป็นทางเลือก — อยู่ข้างรายการวัตถุดิบและทำให้สูตรเป็นเอกสารการผลิตที่สมบูรณ์ไม่ใช่แค่ใบคิดต้นทุน สูตรเดินผ่านวงจรชีวิตสถานะที่ควบคุม (`Draft` → `Published`) และจัดเวอร์ชันเพื่อให้ทุกการเปลี่ยนแปลงในวัตถุดิบ ปริมาณ วิธี หรือต้นทุนถูกบันทึกพร้อม timestamp และผู้ใช้สำหรับการตรวจสอบ

วัตถุดิบสามารถเป็นได้ทั้ง **สินค้า** ที่ดึงจากแคตตาล็อกคลังสินค้าหรือ **sub-recipe** — สูตรที่ publish แล้วอื่นที่ใช้เป็นส่วนประกอบของสูตรหลัก ("mother sauce" ที่ใช้ในเมนูหลักสามจาน base ขนมที่ใช้ในของหวานสองรายการ) sub-recipe ช่วยให้ครัวสร้างเมนูที่ซับซ้อนจากบล็อกที่นำกลับมาใช้และคิดต้นทุนแล้ว: เมื่อต้นทุนวัตถุดิบของ sub-recipe เปลี่ยน สูตรแม่ที่อ้างอิงทุกตัวจะคิดต้นทุนใหม่อัตโนมัติ สูตรอาหารถูกแยกอย่างจงใจจาก **menu item**: สูตรคือสูตรการผลิตและแหล่งความจริงสำหรับต้นทุน menu item คือรายการที่ขายได้บน POS ซึ่งเชื่อมไปยังสูตรหนึ่งหรือหลายสูตร (และไปยัง add-on, modifier และการกำหนดราคา) สูตรหนึ่งสามารถรองรับ menu item หลายรายการได้ (สูตร "House Burger" เดียวขายเป็นทั้งเดี่ยวและเป็นชุดคอมโบ) menu item หนึ่งสามารถประกอบจากหลายสูตร ("Steak Plate" ที่รวมสูตรสเต็ก sub-recipe ของซอส และสูตรเครื่องเคียง)

สูตรอาหารเป็นสะพานเชื่อมระหว่างยอดขายเมนูและการใช้คลังสินค้า เมื่อ menu item ถูกขาย ระบบจะ explode สูตรที่เชื่อมไว้แต่ละตัวด้วยปริมาณที่ขาย คูณผ่านบรรทัดวัตถุดิบ (ใช้ wastage และการแปลงหน่วย) และ post **การใช้วัตถุดิบเชิงทฤษฎี** ที่ได้เป็น stock OUT movement ต่อ inventory ของ outlet สิ่งนี้ขับเคลื่อนรายงาน food-cost ต่อ outlet การวิเคราะห์ความแปรปรวน (ทฤษฎีกับจริง) และการเติมสต๊อกปลายน้ำ — สูตรสามารถสร้าง store requisition อัตโนมัติสำหรับวัตถุดิบที่ต้องใช้เพื่อตอบสนองการผลิตตามคาดการณ์

## 2. บริบททางธุรกิจ

ในการดำเนินงานโรงแรม สูตรอาหารคือสิ่งประดิษฐ์เดียวที่ผูกสิ่งที่ครัวผลิต ต้นทุน และคลังที่ใช้ไว้ด้วยกัน ถ้าไม่มีสูตรมาตรฐาน สามสิ่งจะพัง: พนักงานครัวเตรียมจานเดียวกันต่างกันในแต่ละกะและแต่ละ outlet ทำให้คุณภาพและสัดส่วนไม่สอดคล้องกัน ต้นทุนต่อ portion ไม่สามารถรู้ได้ ดังนั้นการตั้งราคาเมนูกลายเป็นการเดาและกำไรถูกบั่นทอน และคลังไม่สามารถหักลบจากยอดขายได้ ดังนั้นรายงานความแปรปรวน food-cost จึงไม่มีความหมาย สูตรอาหารมาตรฐานที่คิดต้นทุนแล้วคือรากฐานที่ทำให้การดำเนินงาน F&B ทำงานบนตัวเลขมากกว่าสัญชาตญาณ

โมดูลนี้ถูกสร้างรอบ ๆ **food cost engineering** — วินัยของการออกแบบแต่ละจานให้เข้าเป้าหมายเปอร์เซ็นต์ food-cost ในขณะที่รักษาคุณภาพ การจัดจาน และความสอดคล้อง Cost Controller ตั้งเปอร์เซ็นต์ food-cost เป้าหมาย (โดยทั่วไป 28–35% สำหรับ casual dining ต่ำกว่าสำหรับ fine dining) ระบบคำนวณราคาขายที่แนะนำจาก `Cost Per Portion / (1 − Target Food Cost%)` และ gross margin ออกมาเป็น `(Selling Price − Cost Per Portion) / Selling Price` เมื่อราคาของวัตถุดิบเคลื่อนไหว — ขับเคลื่อนโดยการอัปเดต procurement จาก vendor pricelist และการ post GRN — สูตรคิดต้นทุนใหม่แบบ real time แสดงเมนูที่ margin เลื่อนออกนอกเกณฑ์และ flag เพื่อ review ก่อนการรีเฟรชเมนูครั้งต่อไป

ฟังก์ชันทางธุรกิจหลักอีกอย่างที่โมดูลรองรับคือ **การวิเคราะห์ความแปรปรวนทฤษฎีกับจริง** การใช้วัตถุดิบเชิงทฤษฎีคือสิ่งที่สูตรบอกว่าควรถูกใช้เพื่อผลิตยอดขายของวัน (ยอดขาย POS × บรรทัดวัตถุดิบของสูตร × wastage) การใช้จริงคือสิ่งที่ข้อมูลการนับสต๊อกและ store requisition แสดงว่าถูกดึงออกจากคลังจริง ความแปรปรวนระหว่างทั้งสองคือ KPI food-cost ที่สำคัญที่สุดอันเดียวของการดำเนินงาน: ความแปรปรวนบวกที่ยังคงอยู่ชี้ไปที่ over-portioning การโจรกรรม การเสีย หรือ sub-recipe ที่ไม่ถูกต้อง ความแปรปรวนลบที่ยังคงอยู่ชี้ไปที่สูตรผิดหรือการ portion น้อยเกินไป ความถูกต้องของสูตร — yield, wastage, การแปลงหน่วย — จึงไม่ใช่แค่เรื่องของครัวแต่เป็นเรื่องการควบคุมทางการเงิน นั่นเป็นเหตุผลที่ทุกการเปลี่ยนแปลงสูตรถูกจัดเวอร์ชันและอนุมัติ

## 3. แนวคิดสำคัญ

- **Recipe Header**: metadata ระดับบนสุดสำหรับสูตร — ชื่อ ID คำอธิบาย หมวดหมู่ ประเภทอาหาร ประเภทคอร์ส yield หน่วย yield เวลาเตรียม เวลาปรุง เวลารวม ระดับความยาก สารก่อภูมิแพ้ tag สถานะ (`draft` / `published`) รูปภาพหลัก carbon footprint ส่วนหัวเป็นสิ่งที่ปรากฏใน recipe library ขับเคลื่อนการกรองและการค้นหา และมีตัวเลขต้นทุนที่ roll-up (cost per portion, selling price, gross margin) สำหรับสูตรโดยรวม
- **Ingredient**: รายการบรรทัดในสูตรที่ระบุสิ่งที่ใส่ในเมนู วัตถุดิบแต่ละตัวมี type (`product` สำหรับรายการคลังหรือ `recipe` สำหรับ sub-recipe) ปริมาณ หน่วยสูตรอาหาร หน่วยสต๊อก conversion factor ระหว่างสอง เปอร์เซ็นต์ wastage ต้นทุนต่อหน่วย และต้นทุนรวมที่คำนวณ วัตถุดิบสามารถจัดกลุ่มเป็น section หรือ component (เช่น "ซอส" "การ์นิช" "จาน") เพื่อความอ่านง่ายและการคิดต้นทุนแบบ modular
- **Sub-Recipe (Recipe-as-Ingredient)**: สูตรที่ publish แล้วที่ใช้เป็นวัตถุดิบในสูตรอื่น — mother sauce, สต็อก, base ขนม, ส่วนผสมเครื่องเทศ sub-recipe ช่วยให้ครัวสร้างเมนูที่ซับซ้อนจากส่วนประกอบที่นำกลับมาใช้และคิดต้นทุนแล้ว เมื่อต้นทุนวัตถุดิบของ sub-recipe เปลี่ยน สูตรแม่ทุกตัวคิดต้นทุนใหม่อัตโนมัติ สิ่งนี้หลีกเลี่ยงการทำสำเนารายการวัตถุดิบและรักษาข้อมูลต้นทุนให้สอดคล้องกันทั่วเมนู
- **Yield**: ปริมาณเอาท์พุตที่การรันสูตรหนึ่งครั้งผลิต แสดงเป็นตัวเลขบวกกับหน่วย (เช่น `12 portions`, `2.5 kg`, `30 pieces`) yield ขับเคลื่อน cost-per-portion (`Total Cost / Yield`) การ scale (เครื่องคิดเลข scaling คูณวัตถุดิบทั้งหมดด้วย factor เพื่อให้ได้ yield ใหม่) และการหักคลัง yield รวมปริมาณเริ่มต้นกับหลังเตรียมที่เป็นทางเลือก เปอร์เซ็นต์ loss ที่คาดหวัง และเปอร์เซ็นต์ recovery สำหรับการวิเคราะห์ yield ที่ถูกต้อง
- **Wastage Percentage**: การเสียจากการตัด ปอก ระเหย หรือหก ที่คาดหวังต่อวัตถุดิบ แสดงเป็นเปอร์เซ็นต์ ต้นทุนสุทธิต่อวัตถุดิบคือ `Unit Cost × Quantity × (1 + Wastage%)` wastage เป็นการตั้งค่าต่อบรรทัดเพราะวัตถุดิบต่าง ๆ มี profile การเสียที่ต่างกันมาก — ปลาแซลมอนตัวเต็มใช้ได้ 60% ถุงแป้งใช้ได้ 100% — และการ roll-up ตามวัตถุดิบเป็นวิธีเดียวที่ทำให้ต้นทุนสูตรสะท้อนความจริง
- **Recipe Cost (Total / Per Portion)**: ตัวเลขสองตัวที่ roll-up จาก ingredient grid **Total Recipe Cost** คือ `Σ(Ingredient Cost × (1 + Wastage%)) + Labor Cost + Overhead Cost` **Cost Per Portion** คือ `Total Recipe Cost / Yield` ค่าเหล่านี้คำนวณใหม่แบบ real time เมื่อราคาวัตถุดิบเปลี่ยนในแคตตาล็อกคลังสินค้า ดังนั้น recipe library จึงสะท้อนต้นทุนปัจจุบันเสมอ
- **Target Food Cost % and Selling Price**: เปอร์เซ็นต์ food-cost เป้าหมายถูกตั้งต่อสูตรหรือต่อหมวดหมู่ (โดยทั่วไป 28–35% ใน casual dining) **Recommended Selling Price** คือ `Cost Per Portion / (1 − Target Food Cost%)` ราคาขายจริงอาจต่างไป (เช่น สำหรับกลยุทธ์การตั้งราคาเมนู การ match คู่แข่ง) และระบบติดตามทั้งสองข้างพร้อม **Gross Margin %** ที่ได้ = `(Selling Price − Cost Per Portion) / Selling Price × 100`
- **Preparation Step**: คำสั่งตามลำดับในวิธีการ มี `order`, `description`, `duration` ทางเลือก, list ของ `equipment` ที่ต้องการทางเลือก และ `image` ของขั้นตอนทางเลือก ขั้นตอนเรียงลำดับได้ และลำดับขั้นตอนเต็มประกอบเป็นเอกสารการผลิตที่พนักงานครัวใช้ critical control point (จุดตรวจสอบความปลอดภัยอาหาร) สามารถ flag บนขั้นตอนแต่ละขั้นสำหรับ HACCP compliance
- **Theoretical Consumption**: คลังที่ยอดขายของเมนู *ควรจะ* ดึงลงตามสูตร คำนวณเป็น `Σ over sold menu items (sold_qty × recipe_ingredient_qty × (1 + wastage%) × unit_conversion)` post เป็น theoretical stock OUT movement ต่อ outlet ต่อวัตถุดิบ นี่คือตัวเลขด้าน demand ของสมการความแปรปรวน food-cost
- **Actual Consumption**: คลังที่ครัวดึงลงจริง derive จากการ post การนับสต๊อก store requisition และการเบิกตรง ตัวเลขด้าน supply สำหรับความแปรปรวน
- **Variance (Theoretical − Actual)**: ช่องว่างระหว่างสิ่งที่สูตรบอกว่าถูกใช้และสิ่งที่ stock movement บอกว่าถูกใช้ ความแปรปรวนบวก (ทฤษฎี < จริง) หมายถึง over-consumption — over-portioning, การโจรกรรม, การเสีย หรือ sub-recipe ที่ไม่ถูกต้อง ความแปรปรวนลบหมายถึงสูตรประมาณการใช้สูงเกินไป — under-portioning หรือสูตรผิด รายงานความแปรปรวนต่อวัตถุดิบต่อ outlet คือ KPI food-cost ที่สำคัญที่สุดของการดำเนินงาน
- **Menu Item Linkage**: การ map จาก menu item ที่ขายได้บน POS ไปยังสูตรหนึ่งหรือหลายสูตร สูตรหนึ่งสามารถรองรับ menu item หลายตัว (คอมโบ ขนาด) menu item หนึ่งสามารถประกอบจากหลายสูตร (จานที่รวมเมนูหลัก sub-recipe ของซอส และเครื่องเคียง) การ linkage คือสิ่งที่ทำให้ยอดขาย POS ยิง recipe explosion และขับเคลื่อนการใช้วัตถุดิบเชิงทฤษฎี
- **Version History**: ทุกการเปลี่ยนแปลงสูตร (เพิ่ม/ลบวัตถุดิบ เปลี่ยนปริมาณ แก้ไขวิธี คำนวณต้นทุนใหม่ เปลี่ยนสถานะ) เขียนเวอร์ชันใหม่พร้อม timestamp, ผู้ใช้, change log และค่าก่อนหน้า เวอร์ชันเก่ายังอ่านได้สำหรับการตรวจสอบและ rollback และ recipe library แสดง pointer ของเวอร์ชันปัจจุบัน
- **Status Lifecycle (Draft / Published)**: สูตรเริ่มต้นใน `draft` (แก้ไขได้ ยังใช้ไม่ได้ในการผลิตหรือการ link เมนู) การเปลี่ยนเป็น `published` ต้องใช้ฟิลด์ที่จำเป็นทั้งหมดครบ วัตถุดิบอย่างน้อยหนึ่งตัว ขั้นตอนเตรียมอย่างน้อยหนึ่งขั้น และการคำนวณต้นทุนถูกต้อง เฉพาะสูตรที่ publish แล้วเท่านั้นที่สามารถ link กับ menu item และขับเคลื่อนการใช้วัตถุดิบเชิงทฤษฎีได้
- **Category and Cuisine Type**: ข้อมูลหลักประเภทที่ใช้จัดระเบียบ recipe library — `Category` (เช่น Appetiser, Main, Dessert, Beverage), `Cuisine Type` (เช่น ไทย อิตาเลียน ฝรั่งเศส), `Course Type` หมวดหมู่อาจมีค่า default (เปอร์เซ็นต์ food-cost เป้าหมาย คุณสมบัติที่จำเป็น) ที่สูตรใหม่ในหมวดหมู่สืบทอด
- **Allergens and Tags**: การประกาศต่อสูตรที่ใช้สำหรับความปลอดภัยของลูกค้า (กลูเตน นม ถั่ว สัตว์น้ำมีเปลือก ฯลฯ) และสำหรับการกรอง / การค้นหาตามอาหาร (vegan, vegetarian, halal, kosher) สารก่อภูมิแพ้ roll-up ไปยังการแสดง menu item สำหรับ front-of-house และเมนูพิมพ์
- **Stock Deduction Settings**: การตั้งค่าต่อสูตรที่ควบคุมว่าสูตรขับเคลื่อนคลังอย่างไร: ว่าจะหักเมื่อขาย เมื่อผลิต หรือเมื่อ store requisition ออก จะหักวัตถุดิบหรือเฉพาะ sub-recipe ที่ผลิต และจัดการการแปลงหน่วยระหว่างหน่วยสูตรและหน่วยสต๊อกอย่างไร
- **Carbon Footprint**: คะแนนผลกระทบต่อสิ่งแวดล้อมต่อสูตรที่คำนวณจาก footprint ของวัตถุดิบ รองรับรายงานความยั่งยืนและ menu engineering ต่อ KPI ด้านสภาพภูมิอากาศ

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

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [product](/th/inventory/product) — วัตถุดิบของสูตรอ้างอิงสินค้า
- [inventory](/th/inventory/inventory) — การใช้สูตรขับเคลื่อน inventory OUT movement (การใช้วัตถุดิบเชิงทฤษฎี)
- [costing](/th/inventory/costing) — ต้นทุนสูตรคือผลรวมของปริมาณวัตถุดิบที่คิดต้นทุน
- [store-requisition](/th/inventory/store-requisition) — สูตรอาจสร้าง requisition อัตโนมัติ

**Master configuration:**
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยสูตรและหน่วยสต๊อก พร้อม conversion factor ต่อวัตถุดิบ
- [master-data/currency](/th/inventory/master-data/currency) — ต้นทุนสูตรและราคาขายแสดงในสกุลเงินฐานของ property
- [system-config/application-config](/th/inventory/system-config/application-config) — ค่า default ระดับ tenant (เปอร์เซ็นต์ food-cost เป้าหมาย การปัดเศษ นโยบายสถานะ)
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — log ประวัติเวอร์ชันสูตร การ publish และการเปลี่ยนแปลงต้นทุนสำหรับการตรวจสอบ
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — รูปภาพสูตรและรูปขั้นตอนที่แนบกับแต่ละสูตร

## 6. แหล่งอ้างอิง

- Concepts (PRD/requirements): `../carmen/docs/recipe-module/`
- Concepts (UI/page specs): `../carmen/docs/recipe/`
- Frontend: `../carmen-inventory-frontend/`
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
- [04 — Test Scenarios](/th/inventory/recipe/04-test-scenarios) — scenario ข้าม persona + สถานะการครอบคลุม E2E (ยังไม่มี `recipe.spec.ts` เฉพาะ) พร้อมการเจาะลึกต่อ persona:
  - [Chef scenarios](/th/inventory/recipe/04-test-scenarios-chef)
  - [Cost Controller scenarios](/th/inventory/recipe/04-test-scenarios-cost-controller)
  - [Outlet Manager scenarios](/th/inventory/recipe/04-test-scenarios-outlet-manager)
  - [Procurement / F&B Ops scenarios](/th/inventory/recipe/04-test-scenarios-procurement-fb-ops)
  - [Audit / Config scenarios](/th/inventory/recipe/04-test-scenarios-audit-config)
