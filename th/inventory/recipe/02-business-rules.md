---
title: สูตรอาหาร (Recipe) — Business Rules
description: การตรวจสอบความถูกต้อง การคำนวณ การกำหนดสิทธิ์ การ posting และกฎข้ามโมดูลสำหรับโมดูลสูตรอาหาร
published: true
date: '2026-10-27T15:00:00.000Z'
tags: recipe, business-rules, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — Business Rules

> **At a Glance**
> **family ของกฎ:** `REC_VAL_*` validation &nbsp;·&nbsp; `REC_AUTH_*` permission &nbsp;·&nbsp; `REC_CALC_*` calc &nbsp;·&nbsp; `REC_POST_*` posting &nbsp;·&nbsp; `REC_XMOD_*` cross-module
> **จำนวนกฎ:** ประมาณ 69 กฎ — **ส่วนใหญ่เป็นเป้าหมายการออกแบบจาก carmen/docs ไม่ใช่พฤติกรรมที่ implement แล้ว**; §1.1 แสดงรายการชุดย่อยเล็ก ๆ ที่บังคับใช้จริงพร้อมการอ้างอิงแหล่งที่มา
> **กลุ่มผู้ใช้:** ผู้เขียน test + developer — ให้ถือกฎที่ยังไม่บังคับใช้เป็น requirement ตัวเลือก ไม่ใช่พฤติกรรมของระบบที่คาดหวัง

## 1. ภาพรวม

หน้านี้จัดทำแคตตาล็อกกฎทางธุรกิจที่การออกแบบใน carmen/docs กำหนดให้กับโมดูลสูตรอาหาร: การ validate input ห่วงโซ่การคำนวณ cost-engineering (วัตถุดิบ → บรรทัด → สูตร → portion → ราคา → margin) การกำหนดสิทธิ์ตาม role ผลกระทบของการ posting ต่อการเปลี่ยนแต่ละครั้งของ `enum_recipe_status` และกฎข้ามโมดูลกับ [product](/th/inventory/product), [inventory](/th/inventory/inventory), [costing](/th/inventory/costing) และ [store-requisition](/th/inventory/store-requisition) ต่างจากเอกสารที่ขับเคลื่อนด้วย workflow (PR, PO, GRN, SR) สูตร **ไม่ใช่** เอกสาร workflow — ไม่มี `workflow_id` ไม่มีลายเซ็นการอนุมัติต่อบรรทัด (มี comment thread ธรรมดา — `tb_recipe_comment` ดู [Data Model §2.11](/th/inventory/recipe/01-data-model))

### 1.1 สิ่งที่บังคับใช้จริงในปัจจุบัน (ตรวจสอบซ้ำ 2026-10-27)

Implementation ปัจจุบันบังคับใช้ชุดกฎที่เล็กกว่าแคตตาล็อกด้านล่างมาก ตรวจสอบแล้วเทียบกับ `recipe.service.ts`, `preparation-steps.service.ts`, DTO ของ gateway (`recipe.create.dto.ts` / `recipe.update.dto.ts`), error catalog (`@repo/error-catalog`) และ form ฝั่ง frontend (`recipe-form-schema.ts`, `use-recipe-cost-calc.ts`):

| กฎที่บังคับใช้ | ที่ไหน | Error / พฤติกรรม |
|---|---|---|
| `code` ต้องไม่ซ้ำในบรรดาสูตรที่ไม่ถูกลบ (จับคู่ตรงบน `code` อย่างเดียว; unique ของ DB คือ `(code, name, deleted_at)`) | `recipe.service.ts create()` | `RECIPE_ALREADY_EXISTS` (409) |
| `code`, `name`, `category_id` (uuid), `cuisine_id` (uuid), `base_yield`, `base_yield_unit` จำเป็นที่ create | gateway `RecipeCreateSchema` (zod) | 400 validation error |
| `category_id` / `cuisine_id` ต้องอ้างอิงแถวที่**ไม่ถูก soft-delete** (*ไม่* ตรวจสอบ `is_active`) | `recipe.logic.ts validateCategory()/validateCuisine()` | `RECIPE_CATEGORY_NOT_FOUND` / `RECIPE_CUISINE_NOT_FOUND` |
| `doc_version` จำเป็นที่ update/patch; optimistic-lock `where: { id, doc_version }` | `RecipeUpdateSchema` + `recipe.service.ts` | Update ล้มเหลวเมื่อ version ไม่ตรงกัน |
| ผลข้างเคียงของการเปลี่ยนสถานะ: `published_at = now()` เมื่อ `→ PUBLISHED`, `archived_at = now()` เมื่อ `→ ARCHIVED`; **ไม่มี gate ใด ๆ** บนการเปลี่ยนสถานะเอง | `recipe.service.ts update()/patch()` | Timestamp เท่านั้น |
| การลบถูกบล็อกขณะสูตรถูกอ้างอิงเป็น sub-recipe | `recipe.service.ts delete()` + `sub-recipe-usage.ts findRecipeUsers` | `RECIPE_USED_AS_SUB_RECIPE`; ข้อความตอนนี้แสดงรายการสูตรที่ใช้อยู่ (สูงสุด 20 ชื่อ, `812e9be0`) |
| Deactivate (`is_active=false`), archive (`status=ARCHIVED`) หรือเปลี่ยน `base_yield_unit` ถูกบล็อกขณะมีสูตร live อื่นใช้สูตรนี้เป็นวัตถุดิบ | `recipe.service.ts checkInUseGuards()` (`054147fa1`) | `RECIPE_IN_USE_CANNOT_DEACTIVATE` / `RECIPE_YIELD_UNIT_LOCKED` |
| Ingredient save: ไม่เกิน 200 บรรทัด, `qty` 0.00001–999,999,999, wastage 0–100 %, `note` ≤ 500; สินค้า xor sub-recipe ต่อบรรทัด; บรรทัด recipe ต้องใช้หน่วย yield ของ sub-recipe; บรรทัดใหม่ต้องใช้สินค้าที่ **active** และ sub-recipe ที่ active และไม่ใช่ `ARCHIVED`; สูตรไม่สามารถมีตัวเอง (แบบ transitive) | `recipe-ingredient.dto.ts`, `recipe-ingredient-cost.ts costIngredients()`, `sub-recipe-graph.ts findCycle()` | 400 `COMMON_VALIDATION_FAILED`, `RECIPE_INGREDIENT_PRODUCT_NOT_FOUND` / `_PRODUCT_INACTIVE` / `_UNIT_INVALID`, `RECIPE_SUB_RECIPE_NOT_FOUND` / `_NO_YIELD_UNIT` / `_CYCLE` |
| route REST ของ recipe, preparation-step, step-image และ ingredient ทั้งหมดต้องมี `operation_plan.recipe.{view,create,update,delete}` | gateway `config_recipes*.controller.ts` (`30612605e`, 2026-10) | 403 หากไม่มี key |
| ขั้นตอนการเตรียม (preparation steps): `description` จำเป็น; การเพิ่มเป็นแบบ bulk พร้อม `sequence_no` อัตโนมัติ; การ reorder ต้องระบุทุกขั้นตอน active ครบหนึ่งครั้งพอดี; การ patch ขั้นตอนต้องการ `doc_version` | `preparation-steps.service.ts` | `RECIPE_PREPARATION_STEPS_REQUIRED`, `INVALID_ARGUMENT` |
| Form ฝั่ง frontend: `code`, `name`, `status`, `difficulty`, `cuisine_id`, `category_id`, `base_yield_unit` จำเป็น; ฟิลด์ตัวเลข `≥ 0`; บรรทัดวัตถุดิบต้องมี `qty > 0`, หน่วย และสินค้า (หรือ sub-recipe) — บรรทัดที่ไม่มีหน่วยไม่นับว่าครบ (`834bb9ce`); `description` ของขั้นตอนจำเป็น; `max_food_cost_percentage` ต้องไม่ต่ำกว่าเป้าหมาย | `recipe-form-schema.ts` (zod, client-side เท่านั้น) | Error ของฟิลด์แบบ inline |
| ตัวเลข pricing ที่ derive คำนวณฝั่ง client แล้วเก็บ: `cost_per_portion`, `gross_margin(_percentage)`, `actual_food_cost_percentage`, `labor_cost_percentage`, `overhead_percentage`, `suggested_price` | `use-recipe-cost-calc.ts` | ดู §3 สำหรับสูตรจริง |

ทุกอย่างที่เหลือบนหน้านี้ — gate ความครบที่ publish, การ cascade ต้นทุนไปยังสูตรแม่, การเขียน versioning, snapshot pricing-history, permission ต่อ persona (Chef vs Cost Controller vs Outlet Manager แบบอ่านอย่างเดียว) และ **variance** ทฤษฎี-vs-จริง — ยัง **ไม่มีโค้ดที่ implement**: `tb_recipe_version` / `tb_recipe_pricing_history` ไม่มีตัวเขียน และโมเดล permission คือชุด CRUD ทั่วไป `operation_plan.recipe.*` (ไม่มี key สำหรับ publish / เซ็นอนุมัติต้นทุน) คำกล่าวเดิมเรื่อง "placeholder `operation_plan.view` ฝั่ง frontend เท่านั้น" **หายไปแล้ว**: sidebar และ `RouteGuard` ตอนนี้ใช้ key ระดับ resource (`operation_plan.recipe.view` ฯลฯ, `module-list.ts`) และ gateway บังคับ `operation_plan.recipe.*` บน route ของ recipe สิ่งที่ *เข้ามา* คือด้านยอดขาย POS ของการใช้วัตถุดิบ: สูตรที่ขายถูก explode และตัดสต๊อกเป็น Stock Out ผ่าน [Sales Consumption](/th/inventory/recipe/sales-consumption)

การแก้ไขเชิงโครงสร้างเพิ่มเติมสองจุดต่อการเล่าเรื่องด้านล่าง **ประการแรก** วงจรชีวิตในทางปฏิบัติ *ไม่* มีทิศทางบังคับ: `DRAFT ⇄ PUBLISHED ⇄ ARCHIVED` ไปได้ทุกทิศทางผ่าน dropdown สถานะบน toolbar รวมถึง `ARCHIVED → PUBLISHED` และ `ARCHIVED → DRAFT` **ประการที่สอง** ไม่มีแถว `tb_recipe_version` ถูกเขียนบนการแก้ใด ๆ — กลไก versioning/rollback ที่อธิบายในกฎเดิมเป็นการออกแบบระดับ schema เท่านั้น

## 2. กฎการตรวจสอบความถูกต้อง

> **สถานะ: แคตตาล็อกการออกแบบ ที่บังคับใช้บางส่วน** `REC_VAL_001`–`REC_VAL_004` บังคับใช้บางส่วน (ดู §1.1 — ความไม่ซ้ำของ code ตรวจบน `code` อย่างเดียว และการตรวจสอบการอ้างอิง category/cuisine ไม่ต้องการ `is_active`) กฎบรรทัด (009–014) ตอนนี้ **ทำงานบางส่วน** เพราะบรรทัดวัตถุดิบถูก persist: ช่วงของ qty/หน่วย/wastage และความถูกต้องของสินค้า/sub-recipe ทำงานใน `costIngredients`; การตรวจความสอดคล้องของต้นทุน `REC_VAL_013` เป็นจริงโดยโครงสร้าง (server คำนวณตัวเลขเอง) กฎ at-publish (015–018) ยังไม่มี gate การ publish ให้รัน Rule ID ถูกเก็บไว้เป็นแคตตาล็อก requirement ที่หน้า `04-test-scenarios*` อ้างอิง

Rule ID ตามรูปแบบ `REC_VAL_NNN` ตามการออกแบบ: กฎ header (001–008) รันทุก save และที่ publish; กฎบรรทัด (009–014) รันต่อบรรทัดที่ save และที่ publish; กฎ aggregate / at-publish (015–018) รันเฉพาะที่การเปลี่ยน `DRAFT → PUBLISHED`

| Rule ID | เงื่อนไข | บังคับใช้เมื่อ | Error / พฤติกรรม |
| ------- | --------- | ------------- | ----------------- |
| `REC_VAL_001` | `tb_recipe.code` non-null, non-empty และตามนโยบาย code-format ของ tenant (โดยทั่วไป `RCP-<CATEGORY>-<SEQ>`) triple `(code, name, deleted_at)` ไม่ซ้ำเทียบกับสูตรที่ไม่ถูก soft-delete | Create, save, publish | ปฏิเสธด้วย "Recipe code is required and the (code, name) pair must be unique." |
| `REC_VAL_002` | `tb_recipe.name` non-null และ non-empty (trim) | Create, save, publish | ปฏิเสธด้วย "Recipe name is required." |
| `REC_VAL_003` | `tb_recipe.category_id` non-null และอ้างอิงแถวที่ไม่ถูก soft-delete, `is_active = true` ใน `tb_recipe_category` | Save, publish | ปฏิเสธด้วย "Recipe category is required and must reference an active category." |
| `REC_VAL_004` | `tb_recipe.cuisine_id` non-null และอ้างอิงแถวที่ไม่ถูก soft-delete, `is_active = true` ใน `tb_recipe_cuisines` | Save, publish | ปฏิเสธด้วย "Cuisine type is required and must reference an active cuisine." |
| `REC_VAL_005` | `tb_recipe.base_yield > 0` และ `tb_recipe.base_yield_unit` non-empty | Save (warn สำหรับ 0), publish (block) | ปฏิเสธด้วย "Recipe yield must be greater than zero and a yield unit is required." |
| `REC_VAL_006` | `tb_recipe.prep_time ≥ 0` และ `tb_recipe.cook_time ≥ 0` (ศูนย์อนุญาต; ค่าลบไม่อนุญาต) | Save, publish | ปฏิเสธด้วย "Prep time and cook time must be non-negative." |
| `REC_VAL_007` | ถ้า `tb_recipe.default_variant_id` non-null `tb_recipe_yield_variant.recipe_id` ที่อ้างอิง match `tb_recipe.id` (pointer default-variant เป็นของสูตรเดียวกัน) และ variant ไม่ถูก soft-delete | Save, publish | ปฏิเสธด้วย "Default yield variant must belong to this recipe and must not be deleted." |
| `REC_VAL_008` | `target_food_cost_percentage`, `labor_cost_percentage`, `overhead_percentage` (เมื่อ non-null) แต่ละตัวอยู่ใน `[0, 100]` | Save, publish | ปฏิเสธด้วย "Cost percentage values must be between 0 and 100." |
| `REC_VAL_009` | แต่ละแถว `tb_recipe_ingredient` มี `qty > 0` และ `cost_per_unit ≥ 0` และ `wastage_percentage ∈ [0, 100)` (100% wastage ไม่มีความหมาย; ≥ 100 ปฏิเสธ) | Save line (warn สำหรับ 0 qty), publish (block) | ปฏิเสธบรรทัดด้วย "Ingredient quantity must be greater than zero; cost per unit must be non-negative; wastage percentage must be in [0, 100)." |
| `REC_VAL_010` | ความสมบูรณ์ของ discriminator ต่อบรรทัด: เมื่อ `ingredient_type = product`, `product_id` non-null และอ้างอิง `tb_product` ที่ไม่ถูก soft-delete พร้อม `is_used_in_recipe = true` และ `is_active = true`; `sub_recipe_id` เป็น null เมื่อ `ingredient_type = recipe`, `sub_recipe_id` non-null และอ้างอิง `tb_recipe` ที่ไม่ถูก soft-delete พร้อม `status = PUBLISHED`; `product_id` เป็น null | Save line, publish | ปฏิเสธบรรทัดด้วย "Ingredient discriminator mismatch: type `<ingredient_type>` requires `<expected_fk>` populated and the referenced row to be active and (for sub-recipes) published." |
| `REC_VAL_011` | กฎ no-cycle บน sub-recipe: สูตรไม่สามารถใช้ตัวเองทั้งตรงหรือ transitive เป็น sub-recipe กราฟ dependency root ที่ `sub_recipe_id` ต้อง acyclic | Save line, publish | ปฏิเสธบรรทัดด้วย "Sub-recipe cycle detected: recipe `<name>` cannot reference itself directly or through another sub-recipe." |
| `REC_VAL_012` | UoM consistency บนบรรทัด: `ingredient_unit_id` non-null และอ้างอิง `tb_unit` active ถ้า `inventory_unit_id` non-null และต่างจาก `ingredient_unit_id` `conversion_factor` ต้อง non-null และบวก ถ้า `inventory_unit_id IS NULL` `inventory_qty` และ `conversion_factor` ก็ควรเป็น null (display unit = stock unit ไม่ต้องการ conversion) | Save line, publish | ปฏิเสธบรรทัดด้วย "Unit conversion is incomplete: when the recipe unit and inventory unit differ, a positive conversion factor is required." |
| `REC_VAL_013` | ความสอดคล้องของ cost-component: `net_cost` เท่ากับ `qty × cost_per_unit × (1 + wastage_percentage/100)` ในความแม่นยำการปัดเศษ; `wastage_cost` เท่ากับ `qty × cost_per_unit × (wastage_percentage/100)` Application re-compute สิ่งเหล่านี้ทุก save; การ override ด้วยมือไม่ได้รับอนุญาต | Save line, publish | ปฏิเสธบรรทัดด้วย "Ingredient cost columns are inconsistent — `net_cost` and `wastage_cost` must equal the values derived from `qty × cost_per_unit × wastage%`." |
| `REC_VAL_014` | สถานะ sub-recipe ต่อบรรทัด: เมื่อ `ingredient_type = recipe` sub-recipe ที่อ้างอิงอยู่ใน `status = PUBLISHED` **ในขณะ save / publish ของสูตร parent** sub-recipe ที่ archive ตั้งแต่นั้นบล็อก publish ของ parent; บรรทัดต้องถูก reassign หรือ sub-recipe ต้อง re-publish | Save line, publish | ปฏิเสธบรรทัดด้วย "Sub-recipe `<name>` is not currently published; the parent recipe cannot reference an unpublished or archived sub-recipe." |
| `REC_VAL_015` | ที่ publish สูตรมีแถว `tb_recipe_ingredient` ที่ไม่ถูก soft-delete อย่างน้อยหนึ่ง | Publish | ปฏิเสธด้วย "Recipe must contain at least one ingredient line before it can be published." |
| `REC_VAL_016` | ที่ publish สูตรมีแถว `tb_recipe_preparation_step` ที่ไม่ถูก soft-delete อย่างน้อยหนึ่ง | Publish | ปฏิเสธด้วย "Recipe must contain at least one preparation step before it can be published." |
| `REC_VAL_017` | ที่ publish การ rollup cost ของสูตร valid: `total_ingredient_cost = Σ active line net_cost`; `cost_per_portion = (total_ingredient_cost + labor_cost + overhead_cost) / base_yield`; `cost_per_portion > 0` | Publish | ปฏิเสธด้วย "Recipe cost rollup is invalid or zero — verify ingredient costs, labor, overhead, and yield before publishing." |
| `REC_VAL_018` | ที่ publish ถ้า `selling_price` non-null มัน satisfy `selling_price > cost_per_portion` (สูตรที่ขายต่ำกว่าต้นทุนถูกปฏิเสธที่ publish แม้ฟิลด์ nullable เพื่ออนุญาตสูตรที่ไม่ได้ตั้งราคาตรง เช่นเครื่องเคียงหรือ sub-recipe) | Publish | ปฏิเสธด้วย "Selling price must be greater than cost per portion at publish; review pricing." |

## 3. กฎการคำนวณ

สูตรเป็น **เอกสาร cost-engineering**: surface การคำนวณรุ่มรวย ทุกคอลัมน์ cost / quantity เก็บเป็น `Decimal(20, 5)` ที่ระดับแถว ห่วงโซ่การคำนวณตามการออกแบบคือ บรรทัด → สูตร → portion → ราคา → margin โดย cost ของ sub-recipe ไหลเข้ามาแบบ recursive

> **สถานะ (ตรวจสอบซ้ำ 2026-10-27): calculator ที่ทำงานจริงสองตัว** (1) **Server, ต่อบรรทัดวัตถุดิบ** (`computeLine` / `costIngredients` ใน `recipe-ingredient-cost.ts` รันโดย `POST .../ingredients/preview` และ `PUT .../ingredients`): `inventory_qty = qty × from_qty / to_qty` (อัตราส่วนไม่ปัดเศษ), `net_cost = inventory_qty × cost_per_unit`, `wastage_cost = net_cost × wastage% / 100`, ต้นทุนบรรทัด = `net_cost + wastage_cost` ปัด half-up เป็น 5 ตำแหน่งแต่ละตัว; `total_ingredient_cost` = Σ ต้นทุนบรรทัด fallback ของต้นทุนต่อหน่วย: net moving average → average ของ cost layer ล่าสุด → standard cost → 0; บรรทัด sub-recipe คิดต้นทุน `sub.total_ingredient_cost ÷ sub.base_yield` ต่อหน่วย yield (หน่วย 1:1) (2) **Client, header** (`computeRecipeCost` ใน `use-recipe-cost-calc.ts`) จาก `total_ingredient_cost` (ตอนนี้ derive จาก server เมื่อมีบรรทัด), `labor_cost`, `overhead_cost` (ยังกรอกเอง), `base_yield`, `selling_price`, `target_food_cost_percentage`, `max_food_cost_percentage` ตัวเลขระดับ header ทั้งหมดเป็นของทั้ง batch หารด้วย `base_yield` ก่อน สูตร (ปัดเศษ half-up ถึง 2 ทศนิยมผ่าน `round2`):
> - `cost_per_portion = (total_ingredient_cost + labor_cost + overhead_cost) / base_yield` (เป็น 0 เมื่อ yield ≤ 0) — ตรงกับ `REC_CALC_006`–`007`
> - `suggested_price = (total_ingredient_cost / base_yield) / (target/100)` เมื่อ `0 < target ≤ 100`, yield > 0 และต้นทุนวัตถุดิบ > 0 — **ต่างจาก `REC_CALC_008`** (ราคาที่ food cost ของ *วัตถุดิบ* ถึงเป้าหมาย; ไม่รวม labor/overhead; แก้ใน `37c12897`) `min_price` ใช้สูตรเดียวกันกับ `max_food_cost_percentage`; ต่ำกว่านั้นเป็นเพียงคำเตือน
> - `actual_food_cost_percentage = (total_ingredient_cost / base_yield) / selling_price × 100` — **ต่างจาก `REC_CALC_009`** (ซึ่งระบุ `cost_per_portion / selling_price`): ตัวเลขที่ implement ไม่รวม labor/overhead
> - `gross_margin = selling_price − cost_per_portion`; `gross_margin_percentage = gross_margin / selling_price × 100` — ตรงกับ `REC_CALC_010`
> - `labor_cost_percentage = labor_cost / selling_price × 100`; `overhead_percentage = overhead_cost / selling_price × 100` — **ต่างจาก semantics ของ default ใน schema** (default 30%/20% แบบ "ส่วนแบ่งของต้นทุน"); hook เขียนทับค่าที่เก็บด้วย % แบบสัมพัทธ์กับราคา
>
> กฎระดับบรรทัด `REC_CALC_001`–`003` implement ฝั่ง server ตามข้างต้น (หมายเหตุ ข้อความของ `REC_CALC_002` ผิดเมื่อเทียบกับโค้ด: `net_cost` ไม่รวม wastage; ต้นทุนบรรทัดคือ `net_cost + wastage_cost`) กฎ `011`–`014` (cascade, variant) ไม่มี implementation; ไม่มี config `labor_rate` สำหรับ `REC_CALC_004` และการ derive overhead ของ `REC_CALC_005` ไม่ถูกคำนวณที่ไหนเลย (overhead ถูกกรอกโดย user)

Rule ID ตามรูปแบบ `REC_CALC_NNN`

| Rule ID | สูตร |
| ------- | ------- |
| `REC_CALC_001` (ส่วนประกอบ wastage ของบรรทัด) | `wastage_cost = qty × cost_per_unit × (wastage_percentage / 100)` Persist บนแถววัตถุดิบ ใช้โดยรายงานเพื่อแยก "ต้นทุนดิบ" จาก "wastage allowance" |
| `REC_CALC_002` (net cost ของบรรทัด) | *ดีไซน์:* `net_cost = qty × cost_per_unit × (1 + wastage_percentage / 100)` *ที่ implement:* `net_cost = inventory_qty × cost_per_unit` (ก่อน wastage); ต้นทุนบรรทัดที่ roll up คือ `net_cost + wastage_cost` |
| `REC_CALC_003` (ต้นทุนวัตถุดิบรวมของสูตร) | `total_ingredient_cost = Σ tb_recipe_ingredient.net_cost` ข้ามบรรทัด active (ไม่ถูก soft-delete) Persist บน header คำนวณใหม่บนการเปลี่ยนบรรทัดวัตถุดิบ |
| `REC_CALC_004` (ต้นทุนแรงงาน) | *การออกแบบ:* `labor_cost = (prep_time + cook_time) × labor_rate × labor_cost_percentage / 100` โดย `labor_rate` มาจาก config tenant และ default ต่อหมวดหมู่ผ่าน `tb_recipe_category.default_cost_settings` *ที่ implement:* ไม่มี config `labor_rate` อยู่ที่ไหนเลย; `labor_cost` เป็นฟิลด์ form ที่กรอกด้วยมือ persist บน header |
| `REC_CALC_005` (ต้นทุน overhead) | `overhead_cost = total_ingredient_cost × overhead_percentage / 100` % overhead default คือ 20% ตั้งค่าได้ต่อหมวดหมู่ Persist บน header |
| `REC_CALC_006` (ต้นทุนรวมของสูตร) | `total_recipe_cost = total_ingredient_cost + labor_cost + overhead_cost` คำนวณสำหรับการแสดงและการหาร per-portion; **ไม่** persist เป็นคอลัมน์แยกบน `tb_recipe` (มันคือผลรวมของสามส่วนประกอบที่ persist) |
| `REC_CALC_007` (cost per portion) | `cost_per_portion = total_recipe_cost / base_yield` สำหรับ variant `cost_per_unit = total_recipe_cost × (variant.conversion_rate / base_yield) × variant.variant_quantity` แต่ `cost_per_unit` ของ variant ที่ persist คำนวณที่เวลา variant-write Persist บน header สำหรับสูตรฐานและบนแต่ละแถว `tb_recipe_yield_variant` |
| `REC_CALC_008` (ราคาขายที่แนะนำ) | `suggested_price = cost_per_portion / (1 − target_food_cost_percentage / 100)` ราคาที่ให้เป้าหมาย % food-cost คืน margin ที่ต้องการ Persist บน header คำนวณใหม่บนการเปลี่ยน cost หรือการเปลี่ยนเป้าหมาย |
| `REC_CALC_009` (% food cost จริง) | `actual_food_cost_percentage = cost_per_portion / selling_price × 100` คำนวณเฉพาะเมื่อ `selling_price` non-null Persist บน header |
| `REC_CALC_010` (gross margin) | `gross_margin = selling_price − cost_per_portion` (ยอด absolute) `gross_margin_percentage = (selling_price − cost_per_portion) / selling_price × 100` คำนวณเฉพาะเมื่อ `selling_price` non-null ทั้งสอง persist |
| `REC_CALC_011` (sub-recipe cost roll-up) | เมื่อ `ingredient_type = recipe` `cost_per_unit` บนบรรทัดคือ `cost_per_portion` ของ sub-recipe (หรือ per-unit equivalent ตาม `ingredient_unit_id` ของบรรทัดและ yield unit ของ sub-recipe) เมื่อ `cost_per_portion` ของ sub-recipe เปลี่ยน ทุกสูตร parent ที่อ้างอิงต้องคำนวณใหม่: การเขียน `tb_recipe.cost_per_portion` กระจายผ่าน `tb_recipe_used_in_recipes` (back-relation inverse บน sub-recipe) เพื่อ refresh `cost_per_unit` และ `net_cost` บนบรรทัดวัตถุดิบของแต่ละ parent แล้ว `total_ingredient_cost` และคอลัมน์ปลายน้ำบนแต่ละ header ของ parent การ cascade นี้อาจซ้อนถ้า parent ก็เป็น sub-recipe |
| `REC_CALC_012` (variant scaling) | สำหรับแต่ละ `tb_recipe_yield_variant`: ปริมาณวัตถุดิบของ variant = ปริมาณฐาน × `conversion_rate` (เว้นแต่วัตถุดิบ variant-scope ผ่าน `tb_recipe_ingredient.tb_recipe_yield_variantId` ในกรณีนั้น `qty` ใช้ตามเดิม); `cost_per_unit` ของ variant = `total_recipe_cost` ที่ scale / `variant_quantity`; `selling_price`, `food_cost_percentage`, `gross_margin` ของ variant ตามสูตรเดียวกันกับสูตรฐานแต่ใช้ input pricing ของ variant |
| `REC_CALC_013` (UoM conversion บนบรรทัด) | `inventory_qty = qty × conversion_factor` เมื่อ `inventory_unit_id ≠ ingredient_unit_id` Cost-per-unit บนบรรทัดเป็นต่อ `ingredient_unit_id` ตาม default ของ tenant; เมื่อสินค้าต้นทางถูกคิดต้นทุนต่อ `inventory_unit_id` ใช้การ conversion: `cost_per_unit_recipe = cost_per_unit_stock / conversion_factor` |
| `REC_CALC_014` (theoretical consumption) | เมื่อ menu item ที่ link กับสูตร `R` ถูกขายปริมาณ `S` OUT movement เชิงทฤษฎีต่อวัตถุดิบคือ `theoretical_out_qty = S × R.line.qty × R.line.conversion_factor × (1 + R.line.wastage_percentage/100)` แสดงใน `R.line.inventory_unit_id` บรรทัด sub-recipe ซ้อน `theoretical_out_cost = theoretical_out_qty × inventory_unit_cost` (มาจากการ valuation วิธีการคิดต้นทุนของ outlet ผ่าน `[costing](/th/inventory/costing)`) คำนวณที่ event การขายเมนูโดย inventory / POS-integration layer; โมดูล recipe คือแหล่งสูตร |
| `REC_CALC_015` (โหมดการปัดเศษ) | Half-up ถึง 5 ทศนิยมสำหรับ storage (`Decimal(20, 5)`); half-up ถึง 2 ทศนิยมสำหรับการแสดงสกุลเงิน; half-up ถึง 3 ทศนิยมสำหรับการแสดงปริมาณ การ roll-up cost ของ sub-recipe ถือความแม่นยำ 5dp เต็มผ่านห่วงโซ่; เฉพาะการแสดงเท่านั้นที่ปัดเศษ |

### 3.1 ตัวอย่างที่คำนวณ (1 สูตร, 4 วัตถุดิบรวม 1 sub-recipe, 1 variant)

> ตัวอย่างนี้ใช้สูตร**การออกแบบ** (รวมถึงห่วงโซ่ระดับบรรทัดที่ยังไม่ implement และ config tenant `labor_rate` ที่ยังไม่มีจริง); เฉพาะขั้น roll-up ที่ทำเครื่องหมายด้วยกฎที่ตรวจสอบแล้วใน §1.1 เท่านั้นที่ทำงานแบบนี้ในแอปปัจจุบัน ซึ่ง input ต้นทุนสามตัวจะถูกกรอกตรงเข้า form

สูตร *House Burger* พร้อม `base_yield = 1 portion`, `base_yield_unit = portions`, `prep_time = 8 min`, `cook_time = 12 min`, `target_food_cost_percentage = 32.00`, `labor_rate = ฿2.50/min` (config เฉพาะการออกแบบ), `labor_cost_percentage = 30.00`, `overhead_percentage = 20.00` สี่บรรทัดวัตถุดิบ

- **บรรทัด 1** (Beef Patty, `product`): `qty = 1`, `ingredient_unit = piece`, `cost_per_unit = ฿45.00`, `wastage_percentage = 5%`
  - `wastage_cost = 1 × 45.00 × 0.05 = ฿2.25`
  - `net_cost = 1 × 45.00 × 1.05 = ฿47.25`
- **บรรทัด 2** (Brioche Bun, `product`): `qty = 1`, `ingredient_unit = piece`, `cost_per_unit = ฿8.00`, `wastage_percentage = 0%`
  - `wastage_cost = 0`; `net_cost = ฿8.00`
- **บรรทัด 3** (Cheese, `product`): `qty = 30`, `ingredient_unit = g`, `inventory_unit = kg`, `conversion_factor = 0.001`, `cost_per_unit = ฿0.40/g` (หรือ ฿400/kg จากด้านสต๊อก), `wastage_percentage = 2%`
  - `wastage_cost = 30 × 0.40 × 0.02 = ฿0.24`
  - `net_cost = 30 × 0.40 × 1.02 = ฿12.24`
  - `inventory_qty = 30 × 0.001 = 0.030 kg`
- **บรรทัด 4** (Burger Sauce — sub-recipe, `recipe`): `qty = 15`, `ingredient_unit = g`, `cost_per_unit` มาจาก `cost_per_portion` ของ sub-recipe แปลเป็น per-gram = `฿0.18/g`, `wastage_percentage = 0%`
  - `wastage_cost = 0`; `net_cost = 15 × 0.18 = ฿2.70`

Roll-up:

- `total_ingredient_cost = 47.25 + 8.00 + 12.24 + 2.70 = ฿70.19` (ตาม `REC_CALC_003`)
- `labor_cost = (8 + 12) × 2.50 × 30/100 = 20 × 2.50 × 0.30 = ฿15.00` (ตาม `REC_CALC_004`)
- `overhead_cost = 70.19 × 20/100 = ฿14.04` (ตาม `REC_CALC_005`)
- `total_recipe_cost = 70.19 + 15.00 + 14.04 = ฿99.23` (ตาม `REC_CALC_006`)
- `cost_per_portion = 99.23 / 1 = ฿99.23` (ตาม `REC_CALC_007`)
- `suggested_price = 99.23 / (1 − 0.32) = 99.23 / 0.68 = ฿145.93` (ตาม `REC_CALC_008`)

ถ้า chef เลือก `selling_price = ฿150.00`:

- สูตรการออกแบบ (`REC_CALC_009`): `actual_food_cost_percentage = cost_per_portion / selling_price × 100 = 99.23 / 150.00 × 100 = 66.15%` **สูงกว่าเป้าหมาย 32% มาก — สูตร over-cost สำหรับราคาเมนู ฿150** flag สูตรสำหรับ cost review หรือการปรับราคา (ตัวเลขฝั่ง client ที่ implement จริงจะเป็น `total_ingredient_cost / selling_price × 100 = 70.19 / 150.00 × 100 = 46.79%` แทน — ดู status note ใน §3) Chef จะลดต้นทุนวัตถุดิบ (เจรจาราคาเนื้อ swap bun ที่ถูกกว่า) ลดการ allocate labor / overhead หรือเพิ่มราคาขายไปยัง ฿310 (ซึ่งเป็นสิ่งที่เป้าหมาย 32% บน cost ฿99 ต้องการ)
- `gross_margin = 150.00 − 99.23 = ฿50.77` (ตาม `REC_CALC_010`)
- `gross_margin_percentage = 50.77 / 150.00 × 100 = 33.85%`

ตัวอย่างแสดงว่าการไหลการคำนวณเป็น mechanical แต่ตัวเลขที่ได้เปิดเผยว่าสูตรเป็น commercially viable ที่ราคาที่เลือกหรือไม่ — ซึ่งเป็นจุดของวินัย cost-engineering

**Variant scaling**: variant "Double Burger" ที่ `conversion_rate = 1.8` (1.8x ฐาน) — ปริมาณวัตถุดิบ scale: บรรทัด 1 patty กลายเป็น `qty = 2` (มักตั้งค่าแยกต่อ variant แทนตาม pure factor สำหรับวัตถุดิบที่เป็นขั้นเช่น patty ทั้งชิ้น); บรรทัด 3 cheese กลายเป็น 54g; เป็นต้น Variant cost = `total_recipe_cost / variant_quantity` ที่ scale; pricing variant ตามแยก

### 3.2 ตัวอย่างที่คำนวณ (การ cascade การเปลี่ยน cost ของ sub-recipe)

> การ cascade นี้ (`REC_CALC_011` / `REC_POST_006`) เป็นขั้นการออกแบบทั้งหมด — ไม่มีโค้ดการกระจาย re-cost อยู่จริง

Sub-recipe *Burger Sauce* (ใช้เป็นบรรทัด 4 ข้างบน) มี `cost_per_unit` ของวัตถุดิบ mayonnaise เพิ่มจาก ฿0.10/g เป็น ฿0.14/g เนื่องจากการ update pricelist vendor

- `Burger Sauce.cost_per_portion` คำนวณใหม่: ก่อน ฿18.00 / 100g portion → ใหม่ ฿20.40 / 100g portion (ตัวเลขแสดง)
- *House Burger* บรรทัด 4 `cost_per_unit` refresh จาก ฿0.18/g เป็น ฿0.204/g (ตาม `REC_CALC_011`)
- บรรทัด 4 `net_cost` refresh จาก ฿2.70 เป็น ฿3.06
- *House Burger* `total_ingredient_cost` update จาก ฿70.19 เป็น ฿70.55
- `overhead_cost` update (เพราะมันอิงตามต้นทุนวัตถุดิบ) จาก ฿14.04 เป็น ฿14.11
- `total_recipe_cost` update จาก ฿99.23 เป็น ฿99.66
- `cost_per_portion` update จาก ฿99.23 เป็น ฿99.66
- `actual_food_cost_percentage` ที่ราคา ฿150 ย้ายจาก 66.15% เป็น 66.44%

การ cascade นี้คือสิ่งที่ทำให้ sub-recipe มีค่า — เปลี่ยน cost วัตถุดิบหนึ่งบน sub-recipe และทุก parent คิดต้นทุนใหม่อัตโนมัติ แถว `tb_recipe_pricing_history` ถูกเขียนสำหรับแต่ละสูตรที่ได้รับผลกระทบด้วย `change_reason = "vendor pricelist update propagated through sub-recipe Burger Sauce"`

## 4. กฎการกำหนดสิทธิ์

> **สถานะ: permission แบบ role-scoped (ต่อ persona) ด้านล่างยังไม่มี แต่ RBAC ทั่วไปมีแล้ว** ยังไม่มี permission `recipe:*` / publish / เซ็นอนุมัติต้นทุน สิ่งที่มี (ตรวจสอบซ้ำ 2026-10-27): key ใน catalog `operation_plan.recipe`, `.category`, `.cuisine`, `.equipment`, `.equipment_category` โดยแต่ละตัวมี `view/create/update/delete` (`constant/permissions.ts`) ที่ sidebar ใช้ (`module-list.ts`); และ gateway บังคับ `operation_plan.recipe.*` บน recipe, preparation step, step image และ ingredient (ตั้งแต่ `30612605e`) controller REST ของ category / cuisine / equipment **ไม่มี** `@Permission` (มีเพียง route-map ของ licence `config:recipe-* → operation_plan.*`) และ recipe comment ก็ไม่มีเช่นกัน placeholder `operation_plan.view` เดิมไม่ถูกใช้โดย menu leaf ใดอีกแล้ว ทุกกฎ persona ด้านล่างคือโมเดล RBAC เป้าหมายจาก carmen/docs เก็บไว้สำหรับการ implement ในอนาคตและการวางแผน test

Rule ID ตามรูปแบบ `REC_AUTH_NNN` ตามการออกแบบ การกำหนดสิทธิ์บังคับใช้โดย RBAC ที่ API layer; โมดูล recipe **ไม่ใช่** workflow-driven ดังนั้นการกำหนดสิทธิ์เป็นตรง (role-on-object) ไม่ใช่ stage-gated ชื่อ role map กับการ grouping persona ห้าตัวจาก index ของ wiki: Chef, Cost Controller, Outlet Manager, Procurement / F&B Ops, Audit / Config

| Rule ID | Subject | สิทธิ์ | ข้อจำกัด |
| ------- | ------- | ----- | ---------- |
| `REC_AUTH_001` | Chef (Kitchen Manager) | สร้างสูตร (`status = DRAFT`) | Chef ถือ permission `recipe:create` สูตรใหม่เป็น `DRAFT`; `created_by_id = user`; chef เป็นเจ้าของ draft ที่แก้ได้ |
| `REC_AUTH_002` | Chef | แก้ header สูตร วัตถุดิบ ขั้นตอน variant | อนุญาตขณะ `status = DRAFT` สำหรับ chef ใดที่มี `recipe:edit` บนหมวดหมู่; สำหรับสูตร `PUBLISHED` การแก้ต้องการอย่างใดอย่างหนึ่ง (a) chef + นโยบาย tenant `edit_published_with_versioning = true` (การเขียนใช้และแถว `tb_recipe_version` ใหม่ถูกสร้าง) หรือ (b) สูตรถูกย้ายกลับเป็น `DRAFT` ก่อน (`REC_AUTH_005`) |
| `REC_AUTH_003` | Chef | Publish สูตร (`DRAFT → PUBLISHED`) | Chef ถือ permission `recipe:publish` กฎ `REC_VAL_015`–`REC_VAL_018` ทั้งหมดผ่าน นโยบาย tenant อาจต้องการ co-approval ของ Cost Controller สำหรับ action publish เมื่อ `actual_food_cost_percentage > target_food_cost_percentage` เกินกว่า tolerance ของ tenant (เช่น 2 percentage points) |
| `REC_AUTH_004` | Chef | Archive สูตร (`PUBLISHED → ARCHIVED`) | Chef ถือ permission `recipe:archive` อนุญาตเมื่อสูตรไม่อยู่ในการใช้สำหรับการขายเมนู (ไม่มี linkage menu-item active) หรือมี override ชัดเจน ตั้ง `archived_at = now()` Linkage menu-item ที่มีอยู่ควรถูกตัดก่อน archive (นโยบาย application) |
| `REC_AUTH_005` | Chef | ย้าย `PUBLISHED → DRAFT` (un-publish สำหรับการแก้ไข) | Chef ถือ permission `recipe:edit-published` และนโยบาย tenant อนุญาตให้ un-publish (บาง tenant ต้องการการแก้ทั้งหมดเป็นแบบ in-place ด้วย versioning ไม่ un-publish เลย) ตั้ง `published_at = null` (หรือรักษา; ทางเลือก tenant) ควร review menu item ที่ link |
| `REC_AUTH_006` | Cost Controller | แก้ฟิลด์ที่เกี่ยวกับ cost (`target_food_cost_percentage`, `labor_cost`, `overhead_cost`, `labor_cost_percentage`, `overhead_percentage`, `selling_price`, `suggested_price`) | Cost Controller ถือ permission `recipe:edit-cost` อนุญาตบนสูตร `DRAFT` และ `PUBLISHED` (การแก้ cost-only เป็นรูปแบบ partial-update ที่รู้จัก; การแก้วัตถุดิบ / ขั้นตอนเต็มต้องการ role chef) การแก้ trigger แถว `tb_recipe_pricing_history` |
| `REC_AUTH_007` | Cost Controller | Co-approve publish เมื่อ % food-cost จริงเกิน tolerance ของเป้าหมาย | เมื่อนโยบาย tenant ของ `REC_AUTH_003` เปิด co-approval ของ Cost Controller บันทึกใน audit trail ของสูตร (โดยทั่วไปผ่าน `tb_recipe_version.change_summary` หรือ log signoff ระดับ application) |
| `REC_AUTH_008` | Cost Controller | Review และเซ็นอนุมัติการเปลี่ยน recipe-cost ที่กระทบราคาเมนู | อ่าน cost ทั้งหมด; trigger snapshot pricing-history; flag สูตรที่ margin drift นอก tolerance สำหรับ chef / F&B Ops review |
| `REC_AUTH_009` | Outlet Manager | อ่านสูตรที่ publish ที่ใช้ใน outlet | สิทธิ์อ่านอย่างเดียวกับสูตร `status = PUBLISHED` อาจยก feedback (ปัญหาการควบคุม portion ความกังวลความถูกต้องของวัตถุดิบ) นอก schema สูตร (ช่อง comment เชิงปฏิบัติการ) ไม่สามารถแก้ |
| `REC_AUTH_010` | Procurement / F&B Ops | อ่านสูตรทั้งหมดสำหรับการวางแผน procurement | สิทธิ์อ่านอย่างเดียวกับทุกสูตร (`status` ใดก็ได้) ใช้ recipe explosion × ยอดขายคาดการณ์เพื่อขนาด PO ไม่สามารถแก้ |
| `REC_AUTH_011` | F&B Operations Manager | การอนุมัติเชิงกลยุทธ์ — menu item ใหม่และ recipe linkage | F&B Ops ถือ permission `recipe:approve-menu-link` จำเป็นเมื่อสูตร link กับ menu item POS ใหม่หรือเมื่อ % food-cost เป้าหมายของหมวดหมู่ถูกเลื่อนขึ้น การอนุมัติบันทึกนอก schema สูตร (menu-item / POS-integration layer); สูตรเองไม่เปลี่ยน |
| `REC_AUTH_012` | Audit / Config — Sysadmin | จัดการ config ของโมดูล recipe | เป็นเจ้าของข้อมูลหลัก `tb_recipe_category` (หมวดหมู่ การตั้งค่า cost default การ map RBAC), master `tb_recipe_cuisines`, master `tb_recipe_equipment_category` / `tb_recipe_equipment`, การ wire integration กับ `[product](/th/inventory/product)` / `[inventory](/th/inventory/inventory)` / `[store-requisition](/th/inventory/store-requisition)` และการ map permission `recipe:*` ใน RBAC |
| `REC_AUTH_013` | Audit / Config — Auditor | สิทธิ์อ่านอย่างเดียวสำหรับ compliance review | Auditor ถือ permission `recipe:read` และ `recipe:read-history` อาจ review snapshot `tb_recipe_version` timeline `tb_recipe_pricing_history` และคอลัมน์ audit `created_by_id` / `updated_by_id` ไม่มี permission เขียน |
| `REC_AUTH_014` | Soft delete | Soft-delete สูตร | อนุญาตเฉพาะบนสูตร `DRAFT` (chef + permission delete) สูตร `PUBLISHED` ต้อง archive ไม่ลบ สูตร `ARCHIVED` อาจ soft-delete โดย Sysadmin สำหรับสุขภาพข้อมูลหลังช่วงเวลาการเก็บข้อมูล |

## 5. กฎ Posting

ค่าสถานะคือสมาชิก literal ของ `enum_recipe_status` ที่ documented ใน [recipe/01-data-model.md](./01-data-model.md) § 4: **`DRAFT`**, **`PUBLISHED`**, **`ARCHIVED`** ไม่มี event commit-and-fan-out ในความหมาย GRN / SR — สูตรไม่ใช่เอกสารธุรกรรม

> **สถานะ: พฤติกรรมการเปลี่ยนสถานะที่ implement แล้วมีน้อยมาก** ความจริงที่ตรวจสอบแล้ว (`recipe.service.ts`): สถานะใดก็ตั้งได้จากสถานะใดผ่านการ update ฟิลด์ธรรมดา; service ประทับ `published_at` เมื่อ `→ PUBLISHED` และ `archived_at` เมื่อ `→ ARCHIVED` และไม่มีอะไรอื่นเกิดขึ้น — ไม่มี gate การ validate ไม่มีการเขียน `tb_recipe_version` ไม่มีการเขียน `tb_recipe_pricing_history` ไม่มีผลกระทบ menu-item/consumption การ soft delete (`deleted_at`/`deleted_by_id`) อนุญาตที่สถานะ**ใดก็ได้** (guard เดียวคือการถูกใช้เป็น sub-recipe) ไม่จำกัดเฉพาะ `DRAFT` แคตตาล็อก event ด้านล่างคือโมเดลการออกแบบ

Rule ID ตามรูปแบบ `REC_POST_NNN`

| Rule ID | การเปลี่ยน / Event | ผลกระทบ |
| ------- | ------------------ | ------- |
| `REC_POST_001` | Create (→ `DRAFT`) | Insert `tb_recipe` ด้วย `status = DRAFT`, `code` ตามนโยบายการเลขของ tenant, `is_active = true`, คอลัมน์ audit populate ไม่มีวัตถุดิบ ไม่มีขั้นตอน ไม่มี variant ยัง ไม่มี rollup cost |
| `REC_POST_002` | Save (ภายใน `DRAFT`) | Update `tb_recipe`, `tb_recipe_ingredient`, `tb_recipe_preparation_step`, `tb_recipe_yield_variant` ตามการแก้ของ user คำนวณ `tb_recipe_ingredient.net_cost` และ `tb_recipe_ingredient.wastage_cost` ใหม่ตาม `REC_CALC_001`–`REC_CALC_002` คำนวณ `tb_recipe.total_ingredient_cost`, `labor_cost`, `overhead_cost`, `cost_per_portion`, `suggested_price`, `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage` ใหม่ตาม `REC_CALC_003`–`REC_CALC_010` Append `updated_at` / `updated_by_id` ไม่มี snapshot `tb_recipe_version` เขียนที่ save ขณะ `DRAFT` (เฉพาะที่ publish หรือบนการแก้ที่ `PUBLISHED`) |
| `REC_POST_003` | Publish (`DRAFT → PUBLISHED`) — **event การ publish** | ตั้ง `status = PUBLISHED`, `published_at = now()` กฎ `REC_VAL_015`–`REC_VAL_018` ทั้งหมดผ่าน (วัตถุดิบอย่างน้อยหนึ่ง ขั้นตอนอย่างน้อยหนึ่ง rollup cost valid ราคาขาย ≥ cost per portion ถ้าตั้ง) เขียนแถว `tb_recipe_version` จับ snapshot เต็ม (`recipe_data`, `ingredients_data`, `steps_data`, `variants_data`) ด้วย `version_number = 1` (หรือ next sequential), `published = true`, `change_summary = "initial publication"` เขียนแถว `tb_recipe_pricing_history` จับ snapshot ต้นทุน / ราคา / % food-cost / gross-margin ที่ `effective_date = now()` สูตรมีสิทธิ์สำหรับ linkage menu-item และ theoretical consumption แล้ว |
| `REC_POST_004` | แก้วัตถุดิบ / ขั้นตอนบนสูตร `PUBLISHED` (นโยบาย tenant: in-place ด้วย versioning) | ใช้การแก้ต่อ `tb_recipe_ingredient` / `tb_recipe_preparation_step` / `tb_recipe` คำนวณ rollup cost ใหม่ตาม `REC_CALC_003`–`REC_CALC_010` เขียนแถว `tb_recipe_version` ใหม่ด้วย `version_number = previous + 1`, `published = true`, `change_summary` จาก user ถ้า cost / ราคาเปลี่ยน เขียนแถว `tb_recipe_pricing_history` ใหม่ด้วย `effective_date = now()` และ `change_reason` จาก user สูตรยังคง `PUBLISHED` |
| `REC_POST_005` | แก้วัตถุดิบ / ขั้นตอนบนสูตร `PUBLISHED` (นโยบาย tenant: ต้อง un-publish) | ย้าย `PUBLISHED → DRAFT` ตาม `REC_AUTH_005`; ตั้ง `published_at = null` (หรือรักษา; ทางเลือก tenant) ใช้การแก้ใน `DRAFT` Re-publish ตาม `REC_POST_003` เขียนแถว `tb_recipe_version` ใหม่ Menu item ที่ link flag สำหรับ review ระหว่างหน้าต่าง un-publish (สูตรไม่มีสิทธิ์ขับเคลื่อน theoretical consumption ขณะใน `DRAFT`) |
| `REC_POST_006` | การ cascade การเปลี่ยน cost ของ sub-recipe | เมื่อ `cost_per_portion` ของ sub-recipe ที่ `PUBLISHED` เปลี่ยน (ผ่าน `REC_POST_004`) ทุกสูตร parent ที่อ้างอิง (back-relation `tb_recipe_used_in_recipes`) คิดต้นทุนใหม่ atomically ตาม `REC_CALC_011` สำหรับแต่ละ parent ที่ได้รับผลกระทบ: refresh `cost_per_unit` และ `net_cost` บนบรรทัดวัตถุดิบที่เกี่ยวข้อง refresh `total_ingredient_cost` / `cost_per_portion` / pricing ของ parent เขียนแถว `tb_recipe_pricing_history` ด้วย `change_reason = "sub-recipe cost cascade from <sub-recipe-name>"` การ cascade อาจซ้อนถ้า parent ก็เป็น sub-recipe |
| `REC_POST_007` | Archive (`PUBLISHED → ARCHIVED`) | ตั้ง `status = ARCHIVED`, `archived_at = now()` เขียนแถว `tb_recipe_version` สุดท้ายด้วย `change_summary = "archived"` สูตรไม่มีสิทธิ์สำหรับ linkage menu-item หรือ theoretical consumption บนการขายเมนูภายหลัง Menu item ที่ link ที่มีอยู่ควรถูกลบ (นโยบาย application); event theoretical-consumption ประวัติสำหรับสูตร archived ยังคงใน inventory ledger สำหรับ audit |
| `REC_POST_008` | Un-publish (`PUBLISHED → DRAFT`) — ทางเลือก | ตาม `REC_AUTH_005` ตั้ง `status = DRAFT` ทางเลือกล้าง `published_at` สูตรไม่มีสิทธิ์ขับเคลื่อน theoretical consumption ขณะใน `DRAFT` เพื่อ re-publish ให้ run `REC_POST_003` ใหม่ (ซึ่งเขียน `tb_recipe_version` ใหม่) |
| `REC_POST_009` | Soft delete | `deleted_at = now()`, `deleted_by_id = user` อนุญาตเฉพาะที่ `DRAFT` (หรือ `ARCHIVED` สำหรับสุขภาพข้อมูล Sysadmin) แถวยังคงใน database; unique index `(code, name, deleted_at)` อนุญาตให้ re-use code+name เดียวกันหลัง soft-delete |
| `REC_POST_010` | การแก้ pricing-only (ไม่เปลี่ยนวัตถุดิบ / ขั้นตอน) | เมื่อ Cost Controller update `target_food_cost_percentage` หรือ `selling_price` เท่านั้น (ตาม `REC_AUTH_006`): คำนวณ `suggested_price`, `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage` ใหม่ตาม `REC_CALC_008`–`REC_CALC_010` เขียนแถว `tb_recipe_pricing_history` ด้วย `change_reason = "pricing-only update"` สูตรอยู่ในสถานะปัจจุบัน (`DRAFT` หรือ `PUBLISHED`); ไม่ต้องการ `tb_recipe_version` ใหม่ (การเปลี่ยน pricing ถูกติดตามผ่านตาราง pricing-history ไม่ใช่ตาราง versioning เต็ม — ทางเลือก tenant) |
| `REC_POST_011` | Theoretical-consumption fan-out (ปลายน้ำ ไม่ใช่การเปลี่ยนสถานะ recipe) | เมื่อ menu item ที่ link กับสูตร `PUBLISHED` ถูกขายโดย POS inventory / POS-integration layer อ่านบรรทัดวัตถุดิบของสูตรและ post OUT movement เชิงทฤษฎีตาม `REC_CALC_014` นี่คือ **ผลกระทบปลายน้ำ** ของสูตรที่เป็น `PUBLISHED`; โมดูล recipe เองไม่เขียนไปยัง `tb_inventory_transaction` — มันคือแหล่งสูตร |

State diagram (ตามที่ implement — ทุกการเปลี่ยนสถานะเป็นการเปลี่ยนอย่างอิสระผ่าน dropdown):

```
[*] → DRAFT ⇄ PUBLISHED ⇄ ARCHIVED
        ▲__________________│
   (ไปได้ทุกทิศทาง; ผลข้างเคียงเดียวคือ
    timestamp published_at / archived_at เมื่อเข้าสถานะ)
```

Soft-delete ใช้ได้ที่สถานะใดก็ได้; guard การลบเดียวคือ `RECIPE_USED_AS_SUB_RECIPE` เจตนาการออกแบบ (`ARCHIVED` เป็น terminal, ลบได้เฉพาะจาก `DRAFT`) ไม่ถูกบังคับใช้

## 6. กฎข้ามโมดูล

> **สถานะ: ส่วนใหญ่เป็นแคตตาล็อกการออกแบบ — พร้อมเส้นทางที่ implement แล้วหนึ่งเส้น** ยังไม่ implement: re-cost cascade, event cost-drift, การสร้าง recipe→SR, รายงาน variance และการ map RBAC `recipe:*` **Implement แล้วตั้งแต่ 2026-10:** fan-out ที่ขับเคลื่อนโดย POS *จริง* สำหรับ `REC_XMOD_003` / `004` / `008` — บรรทัดขาย POS ที่ map กับสูตรจะถูก explode (ผ่าน sub-recipe รวม wastage และการแปลงหน่วย) และ post เป็น Stock Out ประเภท `SALE` โดย [Sales Consumption](/th/inventory/recipe/sales-consumption) ความต่างจากข้อความดีไซน์: movement เป็น Stock Out ที่ completed ธรรมดา (adjustment type `SALE`) **ไม่ได้**ประทับ `theoretical`; และ trigger คือเอกสารรายวันที่คนตรวจสอบ ไม่ใช่ event ต่อการขาย นอกจากนี้ implement แล้ว: FK `tb_recipe_ingredient.product_id → tb_product` (`Restrict`), guard delete / deactivate / archive / yield-unit ของ sub-recipe และการตรวจ cycle ของ sub-recipe

Rule ID ตามรูปแบบ `REC_XMOD_NNN`

| Rule ID | โมดูลที่เกี่ยวข้อง | กฎ |
| ------- | -------------- | ---- |
| `REC_XMOD_001` | [product](/th/inventory/product) | บรรทัดวัตถุดิบของสูตรอ้างอิงสินค้าผ่าน `tb_recipe_ingredient.product_id → tb_product.id` เฉพาะสินค้าที่ `is_used_in_recipe = true` และ `is_active = true` มีสิทธิ์ (`REC_VAL_010`) Cost ของสินค้าป้อนบรรทัด: `cost_per_unit` มาจาก `tb_product.standard_cost` (หรือการ valuation ที่ outlet คิดต้นทุนผ่าน [costing](/th/inventory/costing) สำหรับ costing ที่ขับเคลื่อนด้วย valuation) เมื่อ cost ของสินค้าเปลี่ยน (ผ่านการ update pricelist vendor ผ่าน `[vendor-pricelist](/th/inventory/vendor-pricelist)` → `[purchase-order](/th/inventory/purchase-order)` → `[good-receive-note](/th/inventory/good-receive-note)` → การ rebuild ของ costing layer) ทุกสูตรที่อ้างอิง flag สำหรับ re-cost; re-cost ใช้ atomically โดย service การคิดต้นทุนสูตร |
| `REC_XMOD_002` | [product](/th/inventory/product) | การ soft-delete สินค้าที่ถูกอ้างอิงโดยสูตร active (ไม่ถูก soft-delete `PUBLISHED`) ถูกบล็อกที่ application layer (FK เป็น `Restrict` แต่ constraint ระดับ schema บังคับเฉพาะ hard delete; soft delete ต้องการการตรวจสอบของ application) ผู้ใช้ต้อง swap วัตถุดิบบนแต่ละสูตรก่อนหรือ archive สูตร |
| `REC_XMOD_003` | [inventory](/th/inventory/inventory) | *(implement บางส่วนเป็นเส้นทาง Sales Consumption → Stock Out; ดูหมายเหตุสถานะด้านบนและ [Sales Consumption](/th/inventory/recipe/sales-consumption))* Theoretical-consumption fan-out: เมื่อ menu item ที่ link กับสูตร `R` ถูกขายโดย POS ปริมาณ `S` inventory layer post OUT movement เชิงทฤษฎีต่อบรรทัดวัตถุดิบตาม `REC_CALC_014` เทียบกับ inventory location ของ **outlet** Movement ประทับเป็น `theoretical` (แตกต่างจาก movement `actual` ที่ขับเคลื่อนโดย SR / GRN) dashboard variance ทฤษฎี-vs-จริงของโมดูล inventory ใช้ประทับนี้เพื่อคำนวณ variance food-cost ของ outlet โมดูล recipe คือแหล่งสูตร; โมดูล inventory เป็นเจ้าของการเขียน |
| `REC_XMOD_004` | [inventory](/th/inventory/inventory) | การ consumption ของ sub-recipe เป็น recursive: เมื่อบรรทัดวัตถุดิบเป็น `ingredient_type = recipe` theoretical-consumption fan-out เจาะเข้าบรรทัดวัตถุดิบของ sub-recipe เองและ post OUT movement สำหรับแต่ละวัตถุดิบสินค้าใบไม้ บรรทัด sub-recipe ไม่เขียน OUT เทียบกับ sub-recipe เอง (สูตรไม่ใช่ inventory item); พวกเขาส่งผ่าน |
| `REC_XMOD_005` | [costing](/th/inventory/costing) | `cost_per_unit` per-ingredient มาจากการ valuation วิธีการคิดต้นทุนของ **outlet** ของสินค้าพื้นฐาน (FIFO หรือ moving-average ตาม config per-location ของ outlet) โมดูล recipe อ่าน cost จากโมดูล costing ที่เวลา line save / re-cost; สำหรับวัตถุดิบ sub-recipe `cost_per_portion` ของสูตรเองถูกใช้ (sub-recipe ไม่มี valuation costing per-outlet — พวกเขาเป็นสูตร ไม่ใช่ inventory) |
| `REC_XMOD_006` | [costing](/th/inventory/costing) | การตรวจจับ cost-drift: เมื่อการ valuation costing ของ outlet สำหรับสินค้าเปลี่ยนเกินกว่า threshold drift ของ tenant (เช่น ±5%) โมดูล costing emit event re-cost; โมดูล recipe consume event และ refresh ทุกสูตรที่อ้างอิงสินค้า แถว `tb_recipe_pricing_history` ถูกเขียนด้วย `change_reason = "cost-drift update from costing module"` สูตรที่ `actual_food_cost_percentage` ตอนนี้เกิน `target_food_cost_percentage` เกิน tolerance flag สำหรับ chef / cost-controller review |
| `REC_XMOD_007` | [store-requisition](/th/inventory/store-requisition) | demand สูตรสามารถสร้าง SR `draft` อัตโนมัติสำหรับการดึงวัตถุดิบ: เมื่อ event การผลิต / banquet ถูกวางแผน โมดูล recipe คำนวณปริมาณวัตถุดิบ × cover count และ post SR `draft` ที่ outlet ปลายทางด้วย `info.recipe_id` ถือ back-reference สูตร SR หลังจากนั้นตาม flow ปกติ (`SR_POST_001` ขึ้นไปใน [store-requisition/02-business-rules](/th/inventory/store-requisition/02-business-rules)) Variance ที่ปิด period ระหว่าง demand ที่สูตรคำนวณและ `issued_qty` จริงปรากฏใน dashboard variance ของ outlet |
| `REC_XMOD_008` | Menu Item / POS integration | ไม่มี `tb_menu_item`; linkage ที่ implement คือ master POS item `tb_pos_item.recipe_id` (ต่อ POS store + item code) พร้อม override ต่อบรรทัดขายทางเลือก `tb_pos_sale_line.recipe_id` / `is_ignored` (ดู [Sales Consumption](/th/inventory/recipe/sales-consumption)) ข้อความดีไซน์ต่อไปนี้: สูตรเดียวอาจ link กับ menu item หลายตัว (combo ขนาด) และ menu item เดียวอาจประกอบจากหลายสูตร (จานที่มีหลายส่วนประกอบ) โมดูล recipe expose query "linked menu items" อ่านอย่างเดียวแต่ไม่ได้เป็นเจ้าของตาราง linkage Event การขายเมนูคือ trigger สำหรับ theoretical-consumption fan-out (`REC_XMOD_003`) |
| `REC_XMOD_009` | Audit / Versioning | ทุกการเปลี่ยนต่อสูตร `PUBLISHED` เขียนแถว `tb_recipe_version` จับ snapshot เต็ม ประวัติเวอร์ชันคือ audit trail; rollback บรรลุโดยอ่าน snapshot JSON ของเวอร์ชันเก่าและใช้ใหม่เป็นการแก้ใหม่ (ซึ่งเองเขียนแถวเวอร์ชันใหม่ รักษาประวัติ) Timeline pricing-only จับแยกใน `tb_recipe_pricing_history` สำหรับการวิเคราะห์ cost-drift |
| `REC_XMOD_010` | RBAC / Sysadmin | สิทธิ์สูตร (`recipe:create`, `recipe:edit`, `recipe:publish`, `recipe:archive`, `recipe:edit-published`, `recipe:edit-cost`, `recipe:approve-menu-link`, `recipe:read`, `recipe:read-history`) ถูก map ต่อ role และต่อหมวดหมู่ Sysadmin (persona Audit / Config) เป็นเจ้าของการ map; การเปลี่ยนใช้ prospectively การ scope permission per-category (เช่น "Pastry Chef แก้ได้เฉพาะหมวด Desserts") รองรับโดย RBAC layer |

## 7. แหล่งอ้างอิง

- `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md` — ข้อกำหนดเชิงฟังก์ชัน `REC_CR_001`–`REC_CR_005` (creation), `REC_CO_001`–`REC_CO_005` (costing), `REC_IN_001`–`REC_IN_005` (ingredient), `REC_ST_001`–`REC_ST_004` (status) กฎ validation ป้อน `REC_VAL_*`; การคำนวณ cost ป้อน `REC_CALC_*` หมายเหตุ: วงจรชีวิตสองสถานะของ Business Requirements (`draft / published`) และการขาด `archived` ใน enum ต่างจาก Prisma enum สามสถานะ — กฎด้านบนใช้ canonical schema
- `../carmen/docs/recipe-module/RECIPE-PRD.md` — user story, ข้อกำหนดฟีเจอร์, ข้อกำหนด integration; section Cost Calculations ใน `RECIPE-Business-Requirements.md` และ section Logic Implementation ป้อน `REC_CALC_*` `Recipe.totalTime` ของ PRD คำนวณที่เวลา display ไม่ persist (ความแตกต่าง — ดู [recipe/01-data-model.md](./01-data-model.md) § 5 รายการ 3)
- `../carmen/docs/recipe-module/RECIPE-Overview.md` — วัตถุประสงค์ของโมดูล บทบาท user จุด integration; section User Roles map ไปยังตาราง persona ในหน้านี้ [03-user-flow.md](./03-user-flow.md) overview
- `../carmen/docs/recipe-module/RECIPE-Page-Flow.md` — flow หน้าและ user journey; แจ้งไฟล์ user-flow แต่ไม่ใช่ชุดกฎโดยตรง
- `../carmen/docs/recipe/recipe-management.md` — การอ้างอิงระดับ layout สำหรับหน้า create / edit (interface แบบ tab: Basic Info, Ingredients, Method, Media, Costing, Nutritional) และ costing sheet
- `../carmen/docs/recipe/recipe-create-edit-page.md` — แหล่ง page-spec สำหรับ form สูตร
- Sibling: `en/recipe/01-data-model.md` — canonical Prisma model, enum เฉพาะ recipe (`enum_recipe_status`, `enum_recipe_difficulty`, `enum_ingredient_type`, `enum_temperature_unit`, `enum_cuisine_region`) และแคตตาล็อกความแตกต่างที่ Section 1, Section 2 และ Section 6 พึ่งพา
- Sibling: `en/recipe/03-user-flow.md` — overview วงจรชีวิตและ persona drill-down; หน้ากฎนี้เป็น complement formal สำหรับการเล่าวงจรชีวิต
- การ implement กฎ backend (ปัจจุบัน): `../carmen-turborepo-backend/apps/micro-business/src/master/recipe/` (`recipe.service.ts`, `recipe.logic.ts`, `preparation-steps/`) — ปัจจุบัน implement เฉพาะชุดย่อยใน §1.1; gate ความครบที่เวลา publish, การคำนวณ rollup cost ใหม่, sub-recipe cascade, theoretical-consumption fan-out และ snapshot pricing-history ยังคงเป็น hook ที่ยังไม่ implement
- การ implement การคำนวณฝั่ง frontend: `../carmen-frontend/routes/operation-plan/recipe/use-recipe-cost-calc.ts` — calculator pricing ฝั่ง client ที่สูตรของมันถูกอ้างถึงใน status note ของ §3
