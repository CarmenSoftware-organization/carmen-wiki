---
title: สูตรอาหาร (Recipe) — User Flow — Chef
description: flow ของ Chef ในโมดูลสูตรอาหาร — สร้างและปรับปรุงสูตร ดูแล sub-recipe publish และ archive
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, user-flow, chef, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — User Flow — Chef

> **At a Glance**
> **Persona:** Chef / Kitchen Manager (+ Kitchen Staff read-only) &nbsp;·&nbsp; **โมดูล:** [recipe](/th/inventory/recipe) &nbsp;·&nbsp; **ขั้นตอน workflow:** DRAFT → PUBLISHED → ARCHIVED (+ un-publish round-trip) &nbsp;·&nbsp; **สิทธิ์สำคัญ:** create, edit, publish, archive, edit-published (พร้อม versioning), clone
> **persona นี้ทำอะไร:** Author และดูแล recipe library — วัตถุดิบ ขั้นตอน yield variant sub-recipe — และเป็นเจ้าของอำนาจ publish และ archive

## 1. บทบาทในโมดูลนี้

persona **Chef** คือ **Chef / Kitchen Manager** (พร้อม subset **Kitchen Staff** เป็นผู้บริโภค read-only ระหว่างบริการ) — บุคคลที่เป็นเจ้าของ recipe library ที่ระดับปฏิบัติการ Chef สร้างสูตรใหม่ ปรับปรุงสูตรเดิม ดูแล library ของ sub-recipe (mother sauce, สต๊อก, base ขนม, ส่วนผสมเครื่องเทศ) ทำให้สอดคล้องกันทั่ว outlet ภายในประเภทอาหาร / หมวดหมู่เดียวกัน และอนุมัติการ publish และการปรับปรุง ตอนเข้า Chef login พร้อม permission `recipe:create` และ `recipe:edit` บนหมวดหมู่ที่เกี่ยวข้อง (RBAC อาจ scope chef ให้หมวดหมู่เฉพาะ — เช่น Pastry Chef → Desserts, Executive Chef → ทั้งหมด) Chef เป็นเจ้าของ `DRAFT` ที่แก้ได้ (สิทธิ์แก้เต็มบน header, วัตถุดิบ, ขั้นตอน, variant) ถืออำนาจ publish (`recipe:publish` ตาม `REC_AUTH_003`) และเป็นเจ้าของอำนาจ archive (`recipe:archive` ตาม `REC_AUTH_004`); สำหรับนโยบาย tenant ที่ต้องการ co-approval ของ Cost Controller เมื่อ % food-cost จริงเกินเป้าหมายเกิน tolerance Chef ประสาน co-approval นั้น (`REC_AUTH_007`) แต่ Chef คือ author formal ของทุกการเปลี่ยนสถานะ subset Kitchen Staff เป็น read-only (`recipe:read` เท่านั้น) และอ่านสูตร `PUBLISHED` ระหว่างบริการ — พวกเขา execute สูตรแต่ไม่เปลี่ยนมัน; feedback จาก Kitchen Staff (ปัญหาการควบคุม portion ขั้นตอนขาด ความกังวลความถูกต้อง) ไหลกลับไปยัง Chef เป็น input สำหรับการปรับปรุงครั้งต่อไป

## 2. Entry Point และ Primary Flow

**Entry point:** สามเส้นทางสู่หน้าจอ recipe-create / edit

- **โมดูล Recipe → New Recipe** — Chef navigate ไป recipe library คลิก **New Recipe** เลือกหมวดหมู่และประเภทอาหาร และเริ่ม authoring ระบบเขียน `tb_recipe` ที่ `status = DRAFT`; `code` กำหนดตามนโยบายการเลขของ tenant; `created_by_id` = chef
- **Clone สูตรที่มีอยู่** — Chef เลือกสูตรที่มีอยู่ (สถานะใดก็ได้) และ clone เป็น `DRAFT` ใหม่ Clone copy header / วัตถุดิบ / ขั้นตอน / variant; `code` และ `name` ถูกล้างให้ chef ตั้ง; `status = DRAFT`, ล้าง `published_at` และ `archived_at`
- **แก้ `DRAFT` ที่มีอยู่หรือ revise `PUBLISHED`** — Chef เปิดสูตรที่มีอยู่ `DRAFT` แก้ได้เต็ม `PUBLISHED` แก้ได้อย่างใดอย่างหนึ่งของ in-place (พร้อม versioning ตาม `REC_POST_004`) หรือผ่าน un-publish round-trip (`PUBLISHED → DRAFT → PUBLISHED` ตาม `REC_POST_005`) ขึ้นอยู่กับนโยบาย tenant

**Primary flow (happy path 12 ขั้นตอน):**

1. **ตัดสินใจเรื่องจาน** Chef มี menu item ใหม่ที่จะเพิ่ม การ refresh ตามฤดูกาล หรือการปรับปรุงที่ขับเคลื่อนด้วย cost ระบุหมวดหมู่ (Appetiser, Main, Dessert, Beverage ฯลฯ) และประเภทอาหาร (ไทย อิตาเลียน ฝรั่งเศส ฯลฯ); สิ่งเหล่านี้ขับเคลื่อน default หมวดหมู่ (% food-cost เป้าหมาย % labor / overhead) ที่สูตรจะสืบทอด
2. **เปิด Recipe → New Recipe** เลือกหมวดหมู่ (ซึ่งกำหนด `tb_recipe_category.default_cost_settings` ที่จะสืบทอด) และประเภทอาหาร ระบบเขียน `tb_recipe` ที่ `status = DRAFT`; `code` กำหนด; default populate (`target_food_cost_percentage`, `labor_cost_percentage`, `overhead_percentage` สืบทอดจากการตั้งค่าหมวดหมู่)
3. **กรอก header สูตร** `name` (เช่น "House Burger"), `description` (rich text), `difficulty` (`EASY` / `MEDIUM` / `HARD`), `base_yield` (เช่น 1) และ `base_yield_unit` (เช่น "portion"), `prep_time` (นาที), `cook_time` (นาที), `allergens` (flag gluten / dairy / nuts / shellfish), `tags` (อิสระ — "vegan", "halal", "summer-menu", "house-special") เพิ่มรูปหลักและ gallery (`images` JSON)
4. **เพิ่มบรรทัดวัตถุดิบ** สำหรับแต่ละวัตถุดิบ: เลือก `ingredient_type` (`product` หรือ `recipe`); ค้นหา product catalog (สำหรับ `product`) หรือ recipe library ที่ publish (สำหรับ `recipe`); กรอก `qty` และหน่วยสูตร; ถ้าหน่วยคลังต่าง กรอก `conversion_factor`; กรอก `wastage_percentage` (ต่อบรรทัด — วัตถุดิบต่างกันมี profile เสียต่างกันมาก เช่น 5% สำหรับหัวหอมหั่น 60% peeling loss สำหรับปลาแซลมอนตัวเต็ม 0% สำหรับแป้ง); ระบบคำนวณ `net_cost` และ `wastage_cost` ตาม `REC_CALC_001`–`REC_CALC_002` และเขียนแถว ทำซ้ำสำหรับแต่ละวัตถุดิบ
5. **เพิ่ม sub-recipe เป็นวัตถุดิบ** สำหรับจานซับซ้อนที่ใช้ mother sauce / สต็อก / ส่วนผสมเครื่องเทศ เลือก `ingredient_type = recipe` และเลือก sub-recipe จาก library `PUBLISHED` `cost_per_portion` ของ sub-recipe ป้อน `cost_per_unit` บนบรรทัด (แปลเป็นพื้นฐาน per-`ingredient_unit_id`); `net_cost` per-line roll up วิธีเดียวกัน sub-recipe ต้อง `PUBLISHED` เพื่อถูกอ้างอิง (`REC_VAL_010` และ `REC_VAL_014`); กฎ no-cycle ป้องกัน loop A→B→A (`REC_VAL_011`)
6. **เพิ่มขั้นตอนการเตรียม** สำหรับแต่ละขั้นตอน: `sequence_no`, `title`, `description` (คำสั่งเต็ม), `duration` (นาที), `temperature` และ `temperature_unit` ถ้าเกี่ยวข้อง, `equipment` (reference ไปยัง `tb_recipe_equipment` master ผ่าน JSON ref), `techniques` (sous-vide / flambé ฯลฯ), `chef_notes` และ `safety_warnings` สำหรับจุดควบคุมสำคัญ HACCP จัดลำดับใหม่ผ่าน drag-and-drop; application เขียน `sequence_no` ใหม่บนแถวที่ถูกแตะ
7. **เพิ่ม yield variant (ทางเลือก)** สำหรับสูตรที่ผลิตหลายขนาดที่ขายได้จากสูตรเดียวกัน (Small / Medium / Large; Half-Tray / Full-Tray): เพิ่มแถว `tb_recipe_yield_variant` ด้วย `variant_name`, `variant_unit`, `variant_quantity`, `conversion_rate` (multiplier บนปริมาณวัตถุดิบฐาน — หรือใช้บรรทัดวัตถุดิบ variant-scope ผ่าน `tb_recipe_ingredient.tb_recipe_yield_variantId` สำหรับวัตถุดิบปริมาณขั้น), `cost_per_unit`, `selling_price` Mark variant หนึ่งเป็น default ผ่าน `tb_recipe.default_variant_id`
8. **Review rollup cost** หน้าจอแสดง `total_ingredient_cost` (Σ `net_cost` ของบรรทัด active), `labor_cost` (คำนวณจาก `prep_time + cook_time` และ labor rate), `overhead_cost` (% ของ ingredient cost), `cost_per_portion` (ผลรวมหารด้วย `base_yield`), `suggested_price` (cost / (1 − target%)) และ — ถ้า `selling_price` ตั้ง — `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage` ปรับวัตถุดิบ wastage หรือ input pricing เพื่อให้บรรลุเป้าหมาย margin
9. **ประสานกับ Cost Controller (เส้นทาง margin off-target)** ถ้า `actual_food_cost_percentage` เกิน `target_food_cost_percentage` เกิน tolerance ของ tenant (โดยทั่วไป 2 percentage points) การ publish ถูก gate บน co-approval ของ Cost Controller ตาม `REC_AUTH_007` Chef แชร์การวิเคราะห์ cost กับ Cost Controller; Cost Controller อย่างใดอย่างหนึ่ง co-approve publish (สูตรเป็น loss leader โดยจงใจ หรือ strategic-priced) หรือขอการปรับปรุง (ลด cost วัตถุดิบ เปลี่ยน vendor ลดขนาด portion)
10. **Publish** คลิก **Publish**; ระบบยิง `REC_VAL_015`–`REC_VAL_018` (วัตถุดิบอย่างน้อยหนึ่ง prep step อย่างน้อยหนึ่ง rollup cost valid `selling_price > cost_per_portion` ถ้าตั้ง) และ `REC_AUTH_003` ในความสำเร็จ: `status = DRAFT → PUBLISHED`, `published_at = now()`; แถว `tb_recipe_version` เขียนด้วย `version_number = 1`, `published = true`; แถว `tb_recipe_pricing_history` เขียนที่ snapshot การ publish สูตรมีสิทธิ์สำหรับ linkage menu-item และการขับเคลื่อน theoretical-consumption แล้ว
11. **ประสาน linkage menu-item (กับ F&B Ops)** สูตร `PUBLISHED` ใหม่โดยทั่วไปนำเสนอต่อ F&B Ops สำหรับการอนุมัติ menu-item ตาม `REC_AUTH_011` Linkage เองอยู่นอก schema สูตร (POS-integration layer หรือ application mapping ตาม `REC_XMOD_008`); Chef ยืนยันว่าสูตรพร้อมสำหรับการขาย
12. **ดูแลตลอดเวลา** เมื่อต้นทุนวัตถุดิบ drift (การ update pricelist vendor ไหลผ่านไปยัง cost สูตรตาม `REC_XMOD_005`) Cost Controller อาจ flag สูตรที่ margin drift; Chef แก้ (in-place ด้วย versioning ตาม `REC_POST_004` หรือผ่าน un-publish round-trip ตาม `REC_POST_005`); แต่ละการแก้เขียน `tb_recipe_version` ใหม่และ (ถ้า cost เปลี่ยน) แถว `tb_recipe_pricing_history` ใหม่ การเปลี่ยน cost ของ sub-recipe cascade อัตโนมัติ (`REC_POST_006`)

## 3. Decision Branch

- **In-place edit vs un-publish round-trip**: เมื่อ revise สูตร `PUBLISHED` Chef เลือกตามนโยบาย tenant **In-place** (`REC_POST_004`) ใช้การแก้ทันทีและเขียนแถว `tb_recipe_version` ใหม่; สูตรยังคง `PUBLISHED` และดำเนินการขับเคลื่อน theoretical consumption ต่อด้วยสูตรใหม่จาก timestamp การแก้ไป **Un-publish round-trip** (`REC_POST_005`) ย้ายสูตรเป็น `DRAFT` ก่อน อนุญาตการแก้ขอบเขตกว้างโดยไม่มีผลกระทบ live แล้ว re-publish; ขณะใน `DRAFT` สูตรไม่ขับเคลื่อน theoretical consumption — menu item ที่ link ถูกบล็อกหรือ fallback ไปเวอร์ชัน publish ก่อน (นโยบาย POS-integration)
- **วัตถุดิบใหม่ vs swap-existing**: เมื่อมี vendor stock-out หรือคำขอทดแทนจาก Procurement Chef เลือกอย่างใดอย่างหนึ่ง (a) swap วัตถุดิบบนบรรทัดที่ได้รับผลกระทบด้วย substitute (รักษาเอกลักษณ์สูตร; รอย audit เบากว่า) หรือ (b) clone สูตรเป็น variant หรือ `DRAFT` ใหม่ด้วยวัตถุดิบทางเลือก (รักษาต้นฉบับ; library หนักกว่าแต่ audit สะอาด) การตัดสินใจขับเคลื่อนด้วยว่าการทดแทน permanent แค่ไหน
- **การใช้ sub-recipe vs วัตถุดิบ inline**: สำหรับซอส สต๊อก หรือส่วนประกอบที่ใช้ในจานหลายตัว Chef ตัดสินใจว่าจะ model เป็น **sub-recipe** (สร้าง `tb_recipe` สำหรับส่วนประกอบ คิดต้นทุนครั้งเดียว อ้างอิงจาก parent หลายตัว — sub-recipe cost cascade `REC_POST_006` ทำให้ทุก parent sync อัตโนมัติ) หรือ **inline** วัตถุดิบโดยตรงในแต่ละ parent (sub-recipe library เบากว่าแต่แต่ละ parent คิดต้นทุนแยกและความไม่สอดคล้องเป็นไปได้) รูปแบบ sub-recipe ที่ต้องการเมื่อใดก็ตามที่ส่วนประกอบปรากฏใน 2+ สูตร
- **Yield variant vs สูตรแยก**: เมื่อจานขายในหลายขนาด (Small / Medium / Large) Chef ตัดสินใจว่าจะ model เป็น **yield variant บนสูตรหนึ่ง** (`tb_recipe` หนึ่ง หลาย `tb_recipe_yield_variant`; วัตถุดิบ scale ผ่าน `conversion_rate` หรือผ่านบรรทัดวัตถุดิบ variant-scope สำหรับปริมาณขั้น) หรือเป็น **สูตรแยก** (สูตรหนึ่งต่อขนาด; การ scale math น้อยลงแต่ entry library มากขึ้น) Yield variant ที่ต้องการสำหรับ variant linear-scale จริง (Small = 0.5x, Large = 1.5x); สูตรแยกที่ต้องการเมื่อ variant ขนาดมีการเตรียมที่ต่างกันอย่างมีความหมาย (เวลาปรุงต่าง อุปกรณ์ต่าง)
- **Wastage บนวัตถุดิบที่ stable vs variable**: สำหรับวัตถุดิบ stable (แป้ง น้ำตาล ก้อนสต๊อก) wastage โดยทั่วไป 0–2%; สำหรับวัตถุดิบ variable สูง (ปลาแซลมอนตัวเต็ม ผลไม้ทั้งลูก ผักใบ) wastage 30–60% Chef ตั้ง `wastage_percentage` ต่อบรรทัดตามที่สังเกต trim / peel loss — `net_cost = qty × cost_per_unit × (1 + wastage%)` คือ cost ที่สูตรถือ; การประเมิน wastage ต่ำเกินไปประเมิน food cost จริงต่ำ
- **Margin off-target ที่ publish**: เมื่อ % food-cost จริงเกินเป้าหมายเกิน tolerance ของ tenant Chef ต้องอย่างใดอย่างหนึ่งแก้เพื่อให้ margin อยู่ในเกณฑ์ (ลด portion swap วัตถุดิบที่ถูกกว่า เพิ่มราคา) หรือประสาน co-approval ของ Cost Controller ตาม `REC_AUTH_007` สำหรับการ publish off-target โดยจงใจ (loss leader, strategic-priced, signature dish)
- **Archive vs un-publish**: เมื่อสูตรกำลังถูกเลิกใช้ Chef เลือก **archive** (`PUBLISHED → ARCHIVED` ตาม `REC_POST_007`; สูตร terminate; ไม่ขับเคลื่อน theoretical consumption; อ่านได้สำหรับ audit) สำหรับการเลิกใช้ permanent หรือ **un-publish** (`PUBLISHED → DRAFT` ตาม `REC_POST_008`) เมื่อสูตรถูก overhaul อย่างมากและจะ re-publish Archive ตั้งใจสำหรับ end-of-life; un-publish ตั้งใจสำหรับการแก้ไข

## 4. Exit Point / Handoff

การมีส่วนร่วมของ Chef บนสูตรใดจบที่หนึ่งในหลาย boundary:

- **Publish สำเร็จ** — handoff ไปยัง **F&B Ops** สำหรับการอนุมัติ menu-item linkage (ตาม `REC_AUTH_011`); สูตรเป็น `PUBLISHED` และมีสิทธิ์สำหรับ linkage menu-item และการขับเคลื่อน theoretical-consumption Chef กลับไปสู่ maintenance mode (ติดตาม cost drift แก้ตามต้องการ)
- **Co-approval ของ Cost Controller pending** — handoff ชั่วคราว **ไปยัง Cost Controller** (ตาม `REC_AUTH_007`); สูตรยังคง `DRAFT` จนกว่า co-approval บันทึก; ในการอนุมัติ Chef publish ในการปฏิเสธ Chef แก้
- **คำขอแก้จาก Outlet Manager / Procurement** — Chef รับ issue (การควบคุม portion ความถูกต้อง คำขอทดแทน) และแก้สูตรตาม `REC_POST_004` / `REC_POST_005` Handoff เป็น informal (ช่อง feedback เชิงปฏิบัติการ) แต่ไหลผ่านอำนาจการแก้ของ Chef
- **flag cost-drift จาก Cost Controller** — Cost Controller แสดงสูตรที่ margin drift; Chef สอบสวนและอย่างใดอย่างหนึ่งแก้วัตถุดิบ (การเปลี่ยนด้านสูตร) หรือเลื่อนไปยัง F&B Ops สำหรับการปรับราคา (การเปลี่ยนด้านเมนู) Handoff กลับไปยัง Cost Controller หลังการแก้สำหรับการ verify ใหม่
- **Archive** — Chef archive สูตรตาม `REC_POST_007` F&B Ops แจ้งเตือนเพื่อตัด linkage menu-item สูตร terminate

Chef อาจทำหน้าที่เป็น **ผู้บริโภค read-only** ของสูตรที่พวกเขาไม่ได้ author — Kitchen Staff ระหว่างบริการ execute สูตร `PUBLISHED` โดยไม่มีอำนาจแก้; Pastry Chef อาจอ่านแต่ไม่แก้สูตรในหมวด Mains ถ้า RBAC เป็น category-scope

## 5. แหล่งอ้างอิง

- Parent overview: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิตสามค่า canonical (`DRAFT / PUBLISHED / ARCHIVED`) บน `enum_recipe_status` และตาราง handoff ข้าม persona; Section 4 แถว "Chef → Cost Controller (co-approval)", "Chef → F&B Ops (menu-item linkage)", "Chef → Archive" anchor exit ของ persona นี้
- `../carmen/docs/recipe-module/RECIPE-Overview.md` § Kitchen Management — แหล่ง carmen/docs สำหรับขอบเขตความรับผิดชอบของ chef
- `../carmen/docs/recipe-module/RECIPE-PRD.md` § Kitchen Management user story — user story ของ carmen/docs ("As a kitchen manager, I want to create and manage standardized recipes...")
- `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md` § Recipe Creation (`REC_CR_001`–`REC_CR_005`), Ingredient Management (`REC_IN_001`–`REC_IN_005`), Recipe Status (`REC_ST_001`–`REC_ST_004`) — ป้อน gate การ validate ที่ Chef พบ
- `../carmen/docs/recipe/recipe-create-edit-page.md` — แหล่ง page-spec สำหรับ surface การแก้หลักของ chef (form แบบ tab: Basic Info, Ingredients, Method, Media, Costing, Nutritional)
- `../carmen/docs/recipe/recipe-management.md` — การอ้างอิงระดับ layout สำหรับ master list, create / edit, costing sheet, หน้าการเตรียม, gallery สื่อ, เครื่องคิดเลข scaling และการจัดการหมวดหมู่ — surface ปฏิบัติการเต็มของ Chef
- Sibling: [03-user-flow-cost-controller.md](./03-user-flow-cost-controller.md) — persona ปลายน้ำที่ co-approve การ publish off-target และ flag cost drift กลับไปยัง Chef
- Sibling: [03-user-flow-outlet-manager.md](./03-user-flow-outlet-manager.md) — persona feedback (ปัญหาการควบคุม portion / ความถูกต้อง) และด้าน demand ของการ consumption สูตร
- Sibling: [03-user-flow-procurement-fb-ops.md](./03-user-flow-procurement-fb-ops.md) — ช่องคำขอทดแทน (Procurement) และการอนุมัติ menu-item เชิงกลยุทธ์ (F&B Ops)
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Sysadmin ตั้ง RBAC category-scope ของ chef และนโยบาย tenant ของ publish-gate; Auditor review ประวัติ `tb_recipe_version` ของ chef
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_recipe_status`, discriminator `tb_recipe_ingredient` (`enum_ingredient_type`), sub-recipe self-relation, โมเดล yield-variant
- Sibling: [02-business-rules.md](./02-business-rules.md) — `REC_VAL_001`–`REC_VAL_018` (gate validation), `REC_CALC_001`–`REC_CALC_015` (cost math ที่ Chef เห็น), `REC_AUTH_001`–`REC_AUTH_005` (scope อำนาจของ Chef), `REC_POST_001`–`REC_POST_008` (ผลกระทบการเปลี่ยนสถานะ)
- ที่เกี่ยวข้อง: [product](/th/inventory/product) — `cost_per_unit` และ flag `is_used_in_recipe` ของวัตถุดิบเป็นต้นน้ำของทุก line entry ของ Chef
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — สูตรของ Chef ขับเคลื่อน OUT movement เชิงทฤษฎีบนการขายเมนู; event cost-drift ไหลกลับผ่าน inventory / costing layer
