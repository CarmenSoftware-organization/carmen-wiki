---
title: สูตรอาหาร (Recipe) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum สำหรับโมดูลสูตรอาหาร
published: true
date: 2026-07-16T04:00:00.000Z
tags: recipe, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — Data Model

> **At a Glance**
> **ตาราง:** `tb_recipe` &nbsp;·&nbsp; `tb_recipe_ingredient` &nbsp;·&nbsp; `tb_recipe_preparation_step` &nbsp;·&nbsp; `tb_recipe_image` / `tb_recipe_preparation_step_image` (galleries) &nbsp;·&nbsp; `tb_recipe_yield_variant` &nbsp;·&nbsp; `tb_recipe_version` &nbsp;·&nbsp; `tb_recipe_pricing_history` &nbsp;·&nbsp; `tb_recipe_category` / `tb_recipe_cuisines` (master)
> **กลุ่มผู้ใช้:** Developer / Auditor (อ้างอิงสำหรับ dev)
> **FK สำคัญ:** recipe `→ tb_recipe_category` / `tb_recipe_cuisines` (Restrict); ingredient `→ tb_product` (เมื่อ type=product) **หรือ** `→ tb_recipe` self-ref ผ่าน `sub_recipe_id` (เมื่อ type=recipe); ingredient `→ tb_unit` ×2 (UoM สูตร + คลัง); variant / step / version / pricing-history ทั้งหมด `→ tb_recipe` (Cascade)
> **รูปแบบ audit:** `created_*` / `updated_*` / `deleted_*` มาตรฐาน; **ไม่มี `tb_recipe_comment` และไม่มี workflow** — audit มาจาก snapshot `tb_recipe_version` + `tb_recipe_pricing_history`; วงจรชีวิต 3 สถานะ `DRAFT / PUBLISHED / ARCHIVED`

> **แหล่งความจริง:** Prisma schema ของ backend อ่านสิ่งเหล่านี้ก่อนเสมอเมื่อเขียนหรืออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma`
>
> ไฟล์ `generated/client/schema.prisma` ใต้แต่ละแพ็กเกจเป็นสำเนาที่สร้างอัตโนมัติ ไม่ใช่ฉบับทางการ

## 1. ภาพรวม

โมดูล recipe เป็นเจ้าของสิบสองเอนทิตีของ tenant-schema บวก enum เฉพาะโมดูลสี่ตัว trio หลักคือ header ของสูตร (`tb_recipe`) บรรทัดวัตถุดิบ (`tb_recipe_ingredient`) และขั้นตอนการเตรียม (`tb_recipe_preparation_step`); สองตาราง image-gallery ถือสื่อ (`tb_recipe_image` สำหรับ gallery ของ header, `tb_recipe_preparation_step_image` สำหรับรูปภาพต่อขั้นตอน — image เป็นแถว first-class พร้อม `file_token` / `sort_order` / `is_primary` **ไม่ใช่** คอลัมน์ JSON บน parent); สองตารางประวัติเวอร์ชัน model การเปลี่ยนแปลงตามเวลา (`tb_recipe_version` — snapshot เต็ม `tb_recipe_pricing_history` — snapshot ต้นทุน / ราคา; ทั้งคู่ปัจจุบันเป็น schema-only ไม่มี service ที่เขียนพวกมัน); ตาราง yield variant (`tb_recipe_yield_variant`) รองรับสูตรที่ผลิตหลายขนาดที่ขายได้จากสูตรเดียว; และตารางข้อมูลหลักสี่ (`tb_recipe_category`, `tb_recipe_cuisines` บวกคู่อุปกรณ์ `tb_recipe_equipment_category` / `tb_recipe_equipment`) ให้ taxonomy ตามประเภทที่ header และขั้นตอนอ้างอิง enum สี่ตัว (`enum_recipe_status`, `enum_recipe_difficulty`, `enum_ingredient_type`, `enum_temperature_unit`) เป็นเฉพาะ recipe; โมดูล recipe **ไม่** reuse `enum_doc_status` ที่แชร์เพราะสูตรไม่ไหลผ่าน workflow เอกสารมาตรฐาน — มีวงจรชีวิตของตัวเองสามสถานะ (`DRAFT / PUBLISHED / ARCHIVED`)

สูตรอยู่ **ต้นน้ำของ [inventory](/th/inventory/inventory) consumption และปลายน้ำของข้อมูล [product](/th/inventory/product) catalog** บรรทัดวัตถุดิบแต่ละบรรทัด resolve เป็นทั้งสินค้า (`tb_recipe_ingredient.product_id → tb_product` เมื่อ `ingredient_type = product`) หรือ sub-recipe (`sub_recipe_id → tb_recipe` เมื่อ `ingredient_type = recipe`); ทั้งสองเส้นทางอยู่บนโมเดลเดียวกันด้วย discriminator `enum_ingredient_type` เดียว บรรทัดวัตถุดิบมี reference สองหน่วย — `ingredient_unit_id` (UoM แสดงผลของสูตร) และ `inventory_unit_id` (UoM สต๊อกของแหล่ง) — บวก `conversion_factor` ที่เชื่อม; สิ่งนี้ทำให้สูตรพูดได้ว่า "200 g แป้ง" ขณะที่คลังถือ "ถุง 1 kg" โดยไม่กำกวม ข้อมูลต้นทุนถูก model บนบรรทัด (`cost_per_unit`, `wastage_percentage`, `net_cost`, `wastage_cost`) พร้อมคอลัมน์ rollup บน header (`total_ingredient_cost` บวกคอลัมน์ labor / overhead / per-portion / pricing / margin); cascade ต้นทุน sub-recipe แบบ recursive ที่โมเดลสื่อถึงยังเป็น design-stage — ไม่มีโค้ด roll-up อยู่จริง และวันนี้ฟิลด์ต้นทุนบน header ถูก populate ตรงจาก form (costing ระดับบรรทัดไม่มี write path เลย)

จุดโครงสร้างที่น่าสังเกต: ต่างจากเอกสารส่วนใหญ่ในระบบ สูตร **ไม่ใช่** เอกสารที่ขับเคลื่อนด้วย workflow — ไม่มี `workflow_id` ไม่มีตาราง `tb_recipe_comment` ไม่มีคอลัมน์ `workflow_history` / `workflow_current_stage` การเปลี่ยนสถานะ (`DRAFT → PUBLISHED → ARCHIVED`) ถูกจับเป็น enum เดียวบน header (`status`) บวกสองคอลัมน์ timestamp (`published_at`, `archived_at`); ความสามารถในการตรวจสอบมาจากตาราง `tb_recipe_version` เฉพาะ (snapshot เวอร์ชันเต็มของ JSON blob `recipe_data`, `ingredients_data`, `steps_data`, `variants_data`) และ `tb_recipe_pricing_history` (snapshot ต้นทุน / ราคาพร้อม `change_reason` และ `effective_date`) carmen/docs PRD อธิบายโมเดลสูตร / sub-recipe เชิงลำดับชั้น enum `type` ของวัตถุดิบ และ linkage `Recipe → Menu Item`; Prisma schema จริงมี link สูตร / sub-recipe บน `tb_recipe_ingredient.sub_recipe_id` discriminator บน `enum_ingredient_type` แต่ **ไม่มีตาราง `tb_menu_item`** — menu-item linkage เป็น application-layer หรือใน package POS-integration ปลายน้ำที่ไม่อยู่ใน tenant schema ดู Section 5

## 2. เอนทิตี

### 2.1 tb_recipe

Header ของสูตร มีเอกลักษณ์ การจำแนก yield timing การ rollup ต้นทุน pricing สถานะ tag สารก่อภูมิแพ้ และคอลัมน์ audit หนึ่ง header มีหลายวัตถุดิบ หลายขั้นตอน หลาย yield variant หลายเวอร์ชัน และหลายแถว pricing-history

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `doc_version` | `Int @default(0) @db.Integer` | No | Counter optimistic-concurrency — DTO update/patch ต้องการ `doc_version` ที่ client อ่านล่าสุด และ service ทำ update ด้วย `where: { id, doc_version }` (fail แบบ 409 เมื่อ mismatch) |
| `id` | `String @db.Uuid` | No | Primary key สร้างผ่าน `gen_random_uuid()` |
| `code` | `String @db.VarChar` | No | code สูตรที่มนุษย์อ่านได้ (เช่น `RCP-HSBURG-001`) จำเป็น |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผลของสูตร จำเป็น |
| `description` | `String? @db.VarChar` | Yes | คำอธิบายอิสระของจาน |
| `note` | `String? @db.VarChar` | Yes | โน้ตภายในสำหรับครัว / การควบคุมต้นทุน |
| `is_active` | `Boolean?` | Yes | flag soft-active; default `true` แยกจาก `status` |
| `category_id` | `String @db.Uuid` | No | FK ไปยัง `tb_recipe_category.id` จำเป็น Restrict on delete |
| `cuisine_id` | `String @db.Uuid` | No | FK ไปยัง `tb_recipe_cuisines.id` จำเป็น Restrict on delete |
| `difficulty` | `enum_recipe_difficulty` | No | `EASY` / `MEDIUM` / `HARD`; default `MEDIUM` |
| `base_yield` | `Decimal @db.Decimal(20, 5)` | No | ปริมาณเอาท์พุตฐานต่อการรันสูตรหนึ่งครั้ง |
| `base_yield_unit` | `String @db.VarChar` | No | หน่วยของ `base_yield` (เช่น `portions`, `kg`, `pieces`) |
| `default_variant_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_recipe_yield_variant.id` (relation ชื่อ `DefaultVariant`); ชี้ไปยัง yield variant ที่ถือเป็น default สำหรับ pricing / display Nullable เพราะสูตรอาจไม่มี variant (yield เดี่ยว) |
| `prep_time` | `Int @default(0)` | No | เวลาเตรียมเป็นนาที |
| `cook_time` | `Int @default(0)` | No | เวลาปรุงเป็นนาที หมายเหตุ: **ไม่มี** คอลัมน์ `total_time` ที่ persist; การ rollup คำนวณที่เวลา display เป็น `prep_time + cook_time` |
| `total_ingredient_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | ยอดรวมต้นทุนวัตถุดิบ **กรอกด้วยมือ** บน form ปัจจุบัน (`recipe-cost-breakdown.tsx` register เป็น input ธรรมดา) — เจตนาการออกแบบ Σ `net_cost` ของบรรทัดไม่มี implementation เพราะบรรทัดวัตถุดิบยังไม่ถูก persist |
| `labor_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | ส่วนประกอบต้นทุนแรงงาน กรอกด้วยมือบน form; ไม่มี tenant config `labor_rate` ที่ไหนเลยใน backend |
| `overhead_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | ส่วนประกอบต้นทุน overhead กรอกด้วยมือบน form |
| `cost_per_portion` | `Decimal @default(0) @db.Decimal(20, 5)` | No | คำนวณฝั่ง client (`use-recipe-cost-calc.ts`): `(total_ingredient_cost + labor_cost + overhead_cost) / base_yield` ปัดเศษ 2 ตำแหน่งทศนิยม |
| `suggested_price` | `Decimal? @db.Decimal(20, 5)` | Yes | คำนวณฝั่ง client: `cost_per_portion / (1 − target_food_cost_percentage/100)` เมื่อ `0 < target < 100` ไม่เช่นนั้นเป็น null |
| `selling_price` | `Decimal? @db.Decimal(20, 5)` | Yes | ราคาขายจริงที่เลือก (อาจต่างจาก `suggested_price` สำหรับกลยุทธ์เมนู) |
| `target_food_cost_percentage` | `Decimal? @default(33.00) @db.Decimal(20, 5)` | Yes | % food-cost เป้าหมาย (โดยทั่วไป 28–35); default ของ schema 33 |
| `actual_food_cost_percentage` | `Decimal? @db.Decimal(20, 5)` | Yes | คำนวณฝั่ง client เป็น `total_ingredient_cost / selling_price × 100` เมื่อ `selling_price > 0` (หมายเหตุ: ต้นทุนวัตถุดิบหารด้วยราคา **ไม่ใช่** `cost_per_portion / selling_price` — ดู `use-recipe-cost-calc.ts`) |
| `gross_margin` | `Decimal? @db.Decimal(20, 5)` | Yes | `selling_price − cost_per_portion` (ยอด absolute) คำนวณฝั่ง client |
| `gross_margin_percentage` | `Decimal? @db.Decimal(20, 5)` | Yes | `(selling_price − cost_per_portion) / selling_price × 100` คำนวณฝั่ง client |
| `labor_cost_percentage` | `Decimal? @default(30.00) @db.Decimal(20, 5)` | Yes | default ของ schema 30 แต่ calc hook ของ form **เขียนทับ** ด้วย `labor_cost / selling_price × 100` ทุกครั้งที่คำนวณใหม่ |
| `overhead_percentage` | `Decimal? @default(20.00) @db.Decimal(20, 5)` | Yes | default ของ schema 20 แต่ calc hook ของ form **เขียนทับ** ด้วย `overhead_cost / selling_price × 100` |
| `carbon_footprint` | `Decimal? @default(0) @db.Decimal(20, 5)` | Yes | Footprint CO₂-equivalent ที่กรอกด้วยมือ; ไม่มี rollup per-ingredient อยู่จริง |
| `deduct_from_stock` | `Boolean @default(true)` | No | flag boolean เดียวที่แก้บน hero section ของ form เจตนาการออกแบบ (การขายเมนูยิง recipe-explosion stock OUT; `false` = ไม่หักคลัง) ยังไม่มีโค้ดที่ consume |
| `status` | `enum_recipe_status @default(DRAFT)` | No | สถานะวงจรชีวิต; default `DRAFT` |
| `tags` | `Json @default("[]") @db.JsonB` | No | Array tag อิสระ (เช่น `["vegan", "halal", "summer-menu"]`) |
| `allergens` | `Json @default("[]") @db.JsonB` | No | Array flag สารก่อภูมิแพ้ (เช่น `["gluten", "dairy", "nuts"]`); roll up ไปยังการแสดง menu-item สำหรับ front-of-house |
| `published_at` | `DateTime?` | Yes | Timestamp ของการเปลี่ยน `DRAFT → PUBLISHED` |
| `archived_at` | `DateTime?` | Yes | Timestamp ของการเปลี่ยน `* → ARCHIVED` |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String? @db.Uuid` | Yes | id user ผู้สร้าง |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String? @db.Uuid` | Yes | id user ผู้ update ล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String? @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK: `category_id → tb_recipe_category.id` (Restrict on delete), `cuisine_id → tb_recipe_cuisines.id` (Restrict), `default_variant_id → tb_recipe_yield_variant.id` (Restrict, relation ชื่อ `DefaultVariant`) Back-relation: หลาย `tb_recipe_ingredient` (เป็นสูตร), หลาย `tb_recipe_ingredient` ผ่าน `SubRecipeIngredients` (เมื่อใช้เป็นวัตถุดิบ sub-recipe ที่อื่น), หลาย `tb_recipe_preparation_step`, หลาย `tb_recipe_yield_variant` (relation ชื่อ `RecipeYieldVariants`), หลาย `tb_recipe_version`, หลาย `tb_recipe_pricing_history`, หลาย `tb_recipe_image` (gallery ของ header — Cascade on delete; `is_primary` mark thumbnail ของ card ที่ list endpoint คืนเป็น `primary_image`)
**Indexes:** `@@unique([code, name, deleted_at])` เป็น `recipe_code_name_u`; `@@index([code])` เป็น `recipe_code_idx`; `@@index([name])` เป็น `recipe_name_idx`; `@@index([code, name])` เป็น `recipe_code_name_idx` หมายเหตุ: **ไม่มี** `@@unique([code, deleted_at])` — unique key คือคู่ (code, name) ดังนั้นสองสูตรสามารถแชร์ code ถ้าชื่อต่างกัน (ไม่ปกติแต่อนุญาต)

### 2.2 tb_recipe_ingredient

บรรทัดวัตถุดิบของสูตร ระบุสิ่งที่ใส่ในสูตร (สินค้าหรือสูตรอื่น) ปริมาณ หน่วยสูตรและหน่วยคลัง conversion factor ระหว่างพวกเขา และส่วนประกอบต้นทุนต่อบรรทัด

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `doc_version` | `Int @default(0) @db.Integer` | No | Counter optimistic-concurrency (รูปแบบมาตรฐาน; ยังไม่มี write path ระดับบรรทัด) |
| `id` | `String @db.Uuid` | No | Primary key |
| `sequence_no` | `Int?` | Yes | การจัดลำดับบรรทัดภายในสูตร; default `1` |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผลบนสูตร (อาจต่างจากชื่อสินค้า / sub-recipe — เช่น "หัวหอมหั่นลูกเต๋า" ชี้ไปยังสินค้า `Onion`) |
| `note` | `String? @db.VarChar` | Yes | โน้ตอิสระบนบรรทัด (เช่น "ใช้สด ไม่ใช่แห้ง") |
| `recipe_id` | `String @db.Uuid` | No | FK ไปยัง `tb_recipe.id` (Cascade on delete — การลบสูตรลบบรรทัดของมัน) |
| `ingredient_type` | `enum_ingredient_type` | No | Discriminator: `product` (resolve เป็น `product_id → tb_product`) หรือ `recipe` (resolve เป็น `sub_recipe_id → tb_recipe`) |
| `product_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_product.id` (Restrict on delete) จำเป็นเมื่อ `ingredient_type = product` |
| `sub_recipe_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_recipe.id` ผ่าน relation ชื่อ `SubRecipeIngredients` (Restrict on delete) จำเป็นเมื่อ `ingredient_type = recipe` Self-referential — สูตรสามารถใช้สูตรอื่นเป็นวัตถุดิบได้ (เฉพาะ sub-recipe ที่ `PUBLISHED` ควรถูกอ้างอิง; ไม่บังคับใช้ที่ระดับ schema ดู business rule) |
| `qty` | `Decimal @db.Decimal(20, 5)` | No | ปริมาณที่ต้องการใน `ingredient_unit_id` |
| `ingredient_unit_id` | `String @db.Uuid` | No | FK ไปยัง `tb_unit.id` ผ่าน relation ชื่อ `recipe_ingredient_unit` (Restrict on delete) UoM แสดงผลของสูตร |
| `inventory_qty` | `Decimal? @db.Decimal(20, 5)` | Yes | ปริมาณแสดงในหน่วยคลัง คำนวณเป็น `qty × conversion_factor` เมื่อหน่วยต่างกัน |
| `inventory_unit_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_unit.id` ผ่าน relation ชื่อ `recipe_inventory_unit` (Restrict on delete) UoM สต๊อกของแหล่ง Nullable เมื่อหน่วยสูตร = หน่วยคลัง |
| `conversion_factor` | `Decimal? @db.Decimal(20, 5)` | Yes | Multiplier จาก `ingredient_unit_id` ไปยัง `inventory_unit_id` (เช่น `0.001` เพื่อไปจากกรัมเป็นกิโลกรัม) |
| `cost_per_unit` | `Decimal @default(0) @db.Decimal(20, 5)` | No | ต้นทุนต่อ `ingredient_unit_id` (หรือต่อ `inventory_unit_id` ถ้า conversion ลง cost บนพื้นฐานหน่วยสต๊อก) มาจากต้นทุน weighted-average หรือ standard ปัจจุบันของสินค้า; สำหรับ sub-recipe มาจาก `cost_per_portion` ของ sub-recipe |
| `wastage_percentage` | `Decimal @default(0) @db.Decimal(20, 5)` | No | การเสีย trim / peel / evaporation เป็น % default 0 |
| `net_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | `qty × cost_per_unit × (1 + wastage_percentage/100)` ตัวเลขต้นทุนที่ roll up ไปยัง `tb_recipe.total_ingredient_cost` |
| `wastage_cost` | `Decimal @default(0) @db.Decimal(20, 5)` | No | `qty × cost_per_unit × (wastage_percentage/100)` ส่วนประกอบของ `net_cost` ที่มาจาก wastage; persist สำหรับรายงาน |
| `tb_recipe_yield_variantId` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_recipe_yield_variant.id` (ชื่อคอลัมน์แบบ Prisma-style camelCase); nullable เมื่อตั้ง บรรทัดวัตถุดิบใช้กับ yield variant นั้นเท่านั้น (บาง variant อาจใช้ ingredient ratio ต่าง) |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String? @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String? @db.Uuid` | Yes | id ผู้ update ล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String? @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK: `recipe_id → tb_recipe.id` (Cascade); `product_id → tb_product.id` (Restrict, nullable); `sub_recipe_id → tb_recipe.id` (Restrict, nullable, relation ชื่อ `SubRecipeIngredients`); `ingredient_unit_id → tb_unit.id` (Restrict, relation ชื่อ `recipe_ingredient_unit`); `inventory_unit_id → tb_unit.id` (Restrict, nullable, relation ชื่อ `recipe_inventory_unit`); `tb_recipe_yield_variantId → tb_recipe_yield_variant.id` (nullable)
**Indexes:** ไม่ประกาศนอกเหนือจาก primary key **ไม่มี** unique index บน `(recipe_id, product_id)` หรือ `(recipe_id, sub_recipe_id)` — สินค้า / sub-recipe เดียวกันสามารถปรากฏหลายครั้งบนสูตรเดียวกัน (เช่น เป็นสองบรรทัดแยกสำหรับสองขั้นตอนการเตรียม) ซึ่งจงใจ
**Implementation status:** ไม่มี endpoint create/update สำหรับบรรทัดวัตถุดิบที่ไหนเลยใน backend (`tb_recipe_ingredient` ถูกอ่านเฉพาะใน `recipe.service.ts findOne` และถูกนับใน delete guard ของ sub-recipe); grid วัตถุดิบบน form ของสูตรเป็น preview-only และไม่รวมใน payload ของการ save

### 2.3 tb_recipe_preparation_step

ขั้นตอนการเตรียมบนสูตร เรียงลำดับ พร้อมสื่อทางเลือก timing temperature equipment technique และโน้ตความปลอดภัย / chef

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `doc_version` | `Int @default(0) @db.Integer` | No | Counter optimistic-concurrency — endpoint patch ของ step ต้องการมัน (`preparation-steps.service.ts patchStep`) |
| `id` | `String @db.Uuid` | No | Primary key |
| `recipe_id` | `String @db.Uuid` | No | FK ไปยัง `tb_recipe.id` (Cascade on delete) |
| `sequence_no` | `Int` | No | ลำดับขั้นตอนภายในสูตร (1, 2, 3, ...) จำเป็น auto-assign ต่อจาก max ปัจจุบันเมื่อ bulk add; เขียนใหม่ 1..n เมื่อ reorder |
| `title` | `String? @db.VarChar` | Yes | ชื่อสั้น (เช่น "Sear the steak") |
| `description` | `String @db.Text` | No | เนื้อหาขั้นตอน — ข้อความคำสั่ง จำเป็น |
| `videos` | `Json? @default("[]") @db.JsonB` | Yes | video ref ของขั้นตอน; default `[]` (**image** ของขั้นตอนไม่ใช่คอลัมน์ JSON — อยู่ในตารางลูก `tb_recipe_preparation_step_image` พร้อม `file_token` / `caption` / `alt_text` / `sort_order` / `is_primary`, Cascade เมื่อลบ step) |
| `duration` | `Int?` | Yes | ระยะเวลาขั้นตอนเป็นนาที |
| `temperature` | `Decimal? @db.Decimal(20, 5)` | Yes | temperature ปรุง / holding ที่ต้องการสำหรับขั้นตอน |
| `temperature_unit` | `enum_temperature_unit?` | Yes | `c` (Celsius) หรือ `f` (Fahrenheit); default `c` |
| `equipment` | `Json @default("[]")` | No | reference อุปกรณ์สำหรับขั้นตอน (เช่น `[{equipment_id, name}]`) — อาจอ้างอิงแถว `tb_recipe_equipment` |
| `techniques` | `Json @default("[]")` | No | tag เทคนิค (เช่น `["sous-vide", "flambé"]`) |
| `chef_notes` | `String? @db.Text` | Yes | เคล็ดลับและทริก chef อิสระ |
| `safety_warnings` | `String? @db.Text` | Yes | โน้ต HACCP / food-safety (จุดควบคุมสำคัญ) |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String? @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String? @db.Uuid` | Yes | id ผู้ update ล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String? @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `recipe_id → tb_recipe.id` (Cascade) Back-relation: หลาย `tb_recipe_preparation_step_image`
**Indexes:** `@@index([recipe_id, deleted_at])` และ `@@index([recipe_id, sequence_no])` **ไม่มี** unique index บน `(recipe_id, sequence_no)` — sequence number ดูแลที่ application; endpoint reorder ต้องการรายการ ID ของ step ที่ active ครบทั้งชุดและเขียน `sequence_no` ใหม่ 1..n

### 2.4 tb_recipe_yield_variant

Yield variant บนสูตร ให้สูตรเดียวผลิตหลายขนาดที่ขายได้จากสูตรเดียวกัน (เช่น "small" / "medium" / "large" portion; "half-tray" / "full-tray") มี pricing ระดับ variant ของตัวเอง **อ่านอย่างเดียวในทางปฏิบัติวันนี้** — endpoint detail รวม `yield_variants` ใน response และ form เปิด `default_variant_id` แต่ไม่มี endpoint create/update สำหรับ variant

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `recipe_id` | `String @db.Uuid` | No | FK ไปยัง `tb_recipe.id` ผ่าน relation ชื่อ `RecipeYieldVariants` (Cascade on delete) |
| `variant_name` | `String @db.VarChar` | No | ชื่อแสดงผล variant (เช่น "Half-Portion", "Large") |
| `variant_unit` | `String @db.VarChar` | No | หน่วยของ `variant_quantity` (เช่น `portions`, `pieces`) |
| `variant_quantity` | `Decimal @db.Decimal(20, 5)` | No | ปริมาณเอาท์พุตสำหรับ variant นี้ |
| `conversion_rate` | `Decimal @db.Decimal(20, 5)` | No | อัตราการแปลงจาก yield ฐานเป็น variant นี้ (เช่น `0.5` สำหรับ half-portion เมื่อฐานเต็ม) |
| `cost_per_unit` | `Decimal? @db.Decimal(20, 5)` | Yes | ต้นทุน per-variant (คำนวณ: base cost × conversion_rate ปรับสำหรับบรรทัด variant-specific) |
| `selling_price` | `Decimal? @db.Decimal(20, 5)` | Yes | ราคาขาย per-variant |
| `food_cost_percentage` | `Decimal? @db.Decimal(20, 5)` | Yes | `cost_per_unit / selling_price × 100` |
| `gross_margin` | `Decimal? @db.Decimal(20, 5)` | Yes | `selling_price − cost_per_unit` |
| `is_default` | `Boolean @default(false)` | No | ว่าเป็น variant default สำหรับสูตรหรือไม่ (ติดตามโดย `tb_recipe.default_variant_id` ด้วย) |
| `shelf_life` | `Int?` | Yes | อายุการเก็บ variant-specific เป็นชั่วโมง / วัน (หน่วยกำหนดโดย tenant) |
| `wastage_rate` | `Decimal? @db.Decimal(20, 5)` | Yes | % wastage variant-specific (override wastage ระดับบรรทัดสำหรับ variant นี้) |
| `min_order_quantity` | `Int?` | Yes | ปริมาณสั่งซื้อขั้นต่ำสำหรับ variant (ใช้ในการวางแผนการผลิต) |
| `max_order_quantity` | `Int?` | Yes | ปริมาณสั่งซื้อสูงสุดสำหรับ variant |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String? @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String? @db.Uuid` | Yes | id ผู้ update ล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String? @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `recipe_id → tb_recipe.id` (Cascade, relation ชื่อ `RecipeYieldVariants`) Back-relation: หลาย `tb_recipe_ingredient` (วัตถุดิบที่ variant-scope), หลาย `tb_recipe_pricing_history`, หลาย `tb_recipe` ผ่าน relation ชื่อ `DefaultVariant` (เมื่อสูตรชี้ไปที่ variant นี้เป็น default)
**Indexes:** ไม่ประกาศนอกเหนือจาก primary key

### 2.5 tb_recipe_version

Snapshot เวอร์ชันเต็มของสูตรในจุดเวลา จับ JSON blob สี่ตัวที่ร่วมอธิบายสูตร: ข้อมูล header, วัตถุดิบ, ขั้นตอน, และ yield variant หนึ่งแถวต่อเวอร์ชันที่ save **Schema-only วันนี้** — ไม่มี backend service ที่เขียนหรืออ่านตารางนี้ (verify แล้ว: การอ้างอิง `tb_recipe_version` นอก schema/ไฟล์ generated มีศูนย์รายการ); การแก้สูตร update `tb_recipe` in place ด้วย optimistic locking แบบ `doc_version`

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `recipe_id` | `String @db.Uuid` | No | FK ไปยัง `tb_recipe.id` (Cascade on delete) |
| `version_number` | `Int` | No | หมายเลขเวอร์ชันต่อเนื่อง (1, 2, 3, ...); กำหนดที่ application |
| `recipe_data` | `Json @db.JsonB` | No | Snapshot header เต็ม (คอลัมน์ทั้งหมดของ `tb_recipe` ในเวลา versioning) |
| `ingredients_data` | `Json @db.JsonB` | No | Snapshot เต็มของบรรทัดวัตถุดิบทั้งหมดบนสูตร |
| `steps_data` | `Json @db.JsonB` | No | Snapshot เต็มของขั้นตอนการเตรียมทั้งหมด |
| `variants_data` | `Json @db.JsonB` | No | Snapshot เต็มของ yield variant ทั้งหมด |
| `change_summary` | `String? @db.Text` | Yes | สรุปอิสระของสิ่งที่เปลี่ยนตั้งแต่เวอร์ชันก่อน |
| `published` | `Boolean @default(false)` | No | ว่าเวอร์ชันนี้ถูก publish (vs. save เป็น draft); ประวัติที่ publish ของสูตรคือ subset ของเวอร์ชันที่ `published = true` |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String? @db.Uuid` | Yes | ผู้ author เวอร์ชัน (user ที่ trigger save / publish) |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด (โดยทั่วไปเท่ากับ `created_at` เพราะเวอร์ชัน immutable) |
| `updated_by_id` | `String? @db.Uuid` | Yes | id ผู้ update ล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String? @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `recipe_id → tb_recipe.id` (Cascade)
**Indexes:** ไม่ประกาศนอกเหนือจาก primary key คู่ (recipe_id, version_number) ดูแลที่ application สำหรับ monotonicity; ไม่มี unique constraint ที่ระดับ DB

### 2.6 tb_recipe_pricing_history

ประวัติต้นทุน / ราคาสำหรับสูตร (และ yield variant เฉพาะทางเลือก) แต่ละแถวเป็น snapshot ที่ `effective_date` จับ cost-per-portion, ราคาขาย, เปอร์เซ็นต์ food-cost และ gross margin บวก benchmark คู่แข่งทางเลือก **Schema-only วันนี้** — ไม่มี backend service ที่เขียนตารางนี้; การเปลี่ยน pricing แค่เขียนทับคอลัมน์บน header

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `recipe_id` | `String @db.Uuid` | No | FK ไปยัง `tb_recipe.id` (Cascade on delete) |
| `variant_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_recipe_yield_variant.id` (Cascade on delete); nullable เมื่อ snapshot เป็นสำหรับสูตรฐาน |
| `cost_per_portion` | `Decimal @db.Decimal(20, 5)` | No | Snapshot ของต้นทุนต่อ portion ที่ `effective_date` |
| `selling_price` | `Decimal @db.Decimal(20, 5)` | No | Snapshot ของราคาขาย |
| `food_cost_percentage` | `Decimal @db.Decimal(20, 5)` | No | Snapshot ของ `cost / price × 100` |
| `gross_margin` | `Decimal @db.Decimal(20, 5)` | No | Snapshot ของ `price − cost` |
| `competitor_avg_price` | `Decimal? @db.Decimal(20, 5)` | Yes | Benchmark ตลาด — ราคาเฉลี่ยคู่แข่งสำหรับจานที่เทียบได้ |
| `competitor_min_price` | `Decimal? @db.Decimal(20, 5)` | Yes | Benchmark ตลาด — ราคาคู่แข่งต่ำสุด |
| `competitor_max_price` | `Decimal? @db.Decimal(20, 5)` | Yes | Benchmark ตลาด — ราคาคู่แข่งสูงสุด |
| `change_reason` | `String? @db.VarChar` | Yes | เหตุผลที่ snapshot ถูกเอา (เช่น "menu refresh", "ingredient cost spike", "competitor price match") |
| `effective_date` | `DateTime @db.Timestamptz(6)` | No | วันที่ snapshot ใช้กับ |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การสร้างแถว |
| `created_by_id` | `String? @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String? @db.Uuid` | Yes | id ผู้ update ล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String? @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK: `recipe_id → tb_recipe.id` (Cascade); `variant_id → tb_recipe_yield_variant.id` (Cascade, nullable)
**Indexes:** ไม่ประกาศนอกเหนือจาก primary key

### 2.7 tb_recipe_category

ข้อมูลหลักสำหรับหมวดหมู่สูตร รองรับลำดับชั้น self-referential (parent → subcategory) และการตั้งค่าต้นทุน / margin default ต่อหมวดหมู่ที่สืบทอดโดยสูตรใหม่ในหมวดหมู่

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `code` | `String @db.VarChar` | No | code หมวดหมู่ |
| `name` | `String @db.VarChar` | No | ชื่อแสดงผลหมวดหมู่ |
| `description` | `String? @db.VarChar` | Yes | คำอธิบายอิสระ |
| `note` | `String? @db.VarChar` | Yes | โน้ตภายใน |
| `is_active` | `Boolean?` | Yes | flag active; default `true` |
| `parent_id` | `String? @db.Uuid` | Yes | FK ไปยัง `tb_recipe_category.id` ผ่าน relation ชื่อ `CategoryHierarchy` (Restrict on delete); nullable สำหรับหมวดหมู่ root |
| `level` | `Int @default(1)` | No | ระดับลำดับชั้น (1 = root, 2 = child, ...) ดูแลที่ application: service ตั้ง `parent.level + 1` เมื่อ create/reparent (เฉพาะแถวที่ย้ายเท่านั้น — descendant ไม่ถูก recascade) |
| `image_file_token` | `String? @db.VarChar` | Yes | รูปภาพหมวดหมู่ ตั้งผ่าน flow `recipe-categories.set-image` (multipart upload ผ่าน gateway) |
| `default_cost_settings` | `Json @default("{}") @db.JsonB` | No | การตั้งค่าต้นทุน default ต่อหมวดหมู่ (% food-cost เป้าหมาย, % labor, % overhead ฯลฯ) ที่สูตรใหม่สืบทอด |
| `default_margins` | `Json @default("{}") @db.JsonB` | No | การตั้งค่า margin default ต่อหมวดหมู่ |
| `info` | `Json? @default("{}") @db.JsonB` | Yes | Extension bag |
| `dimension` | `Json? @default("[]") @db.JsonB` | Yes | Cost-dimension default สำหรับหมวดหมู่ |
| `doc_version` | `Int @default(0) @db.Integer` | No | Counter optimistic-concurrency |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String? @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String? @db.Uuid` | Yes | id ผู้ update ล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String? @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` FK `parent_id → tb_recipe_category.id` (Restrict, relation ชื่อ `CategoryHierarchy`) Back-relation: หลาย `tb_recipe_category` (subcategory), หลาย `tb_recipe`
**Indexes:** ไม่ประกาศนอกเหนือจาก primary key (หมายเหตุ: ไม่มี unique index บน `code` หรือ `name` — schema อนุญาตให้ code / name ซ้ำ; ความไม่ซ้ำบังคับใช้ที่ application)

### 2.8 tb_recipe_cuisines

ข้อมูลหลักสำหรับประเภทอาหาร แต่ละ cuisine มี tag region (`enum_cuisine_region`) และอาจประกาศ popular dish / key ingredient สำหรับ menu engineering

| ฟิลด์ | Prisma Type | Nullable | คำอธิบาย |
| ----- | ----------- | -------- | ----------- |
| `id` | `String @db.Uuid` | No | Primary key |
| `name` | `String @db.VarChar` | No | ชื่อ cuisine (เช่น "Thai", "Italian", "French") |
| `description` | `String? @db.VarChar` | Yes | คำอธิบายอิสระ |
| `note` | `String? @db.VarChar` | Yes | โน้ตภายใน |
| `is_active` | `Boolean?` | Yes | flag active; default `true` |
| `region` | `enum_cuisine_region` | No | tag region — `ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA` |
| `popular_dishes` | `Json @default("[]")` | No | Array ของชื่อจานยอดนิยมสำหรับ cuisine |
| `key_ingredients` | `Json @default("[]")` | No | Array ของวัตถุดิบ signature |
| `image_file_token` | `String? @db.VarChar` | Yes | รูปภาพ cuisine ตั้งผ่าน flow `recipe-cuisines.set-image` |
| `info` | `Json? @default("{}") @db.JsonB` | Yes | Extension bag |
| `dimension` | `Json? @default("[]") @db.JsonB` | Yes | Cost-dimension default |
| `doc_version` | `Int @default(0) @db.Integer` | No | Counter optimistic-concurrency |
| `created_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การสร้าง |
| `created_by_id` | `String? @db.Uuid` | Yes | id ผู้สร้าง |
| `updated_at` | `DateTime? @default(now()) @db.Timestamptz(6)` | Yes | Timestamp การ update ล่าสุด |
| `updated_by_id` | `String? @db.Uuid` | Yes | id ผู้ update ล่าสุด |
| `deleted_at` | `DateTime? @db.Timestamptz(6)` | Yes | Timestamp soft-delete |
| `deleted_by_id` | `String? @db.Uuid` | Yes | id ผู้ soft-delete |

**Constraints:** `@id` บน `id` Back-relation: หลาย `tb_recipe`
**Indexes:** `@@unique([name, deleted_at])` เป็น `recipe_cuisines_name_u`; `@@index([region])`; `@@index([name])` เป็น `recipe_cuisines_name_idx`

### 2.9 tb_recipe_equipment_category / tb_recipe_equipment (master เพื่อน)

`tb_recipe_equipment_category` เป็น list แบนของประเภทอุปกรณ์ (ไม่มีลำดับชั้น — มันไม่มี `parent_id`); `tb_recipe_equipment` เป็น master ต่อ item (code, name, category, รายละเอียดทางกายภาพ, capacity, station, ข้อความ operational / maintenance, attachment, คู่มือ, `image_file_token`) อุปกรณ์ถูกอ้างอิงจากขั้นตอนการเตรียมผ่าน array JSON `equipment` ของขั้นตอน ไม่ผ่านคอลัมน์ foreign-key ดู Prisma schema lines 5614–5704 สำหรับชุด field เต็ม เหล่านี้เป็นข้อมูลหลักสำหรับการอ้างอิงด้าน recipe; พวกเขาไม่ขับเคลื่อนคลัง

### 2.10 tb_recipe_image / tb_recipe_preparation_step_image (galleries)

ทั้งคู่มีรูปทรงเดียวกัน: `doc_version`, `id`, FK ไปยัง parent (`recipe_id` / `preparation_step_id`, Cascade on delete), `file_token` (จำเป็น), `caption`, `alt_text`, `sort_order @default(0)`, `is_primary @default(false)`, คอลัมน์ audit Index บน `(parent, deleted_at)` และ `(parent, sort_order)` Gallery ของ header ดูแลผ่าน multipart payload ของการ create/update สูตร (`data` + manifest `gallery` + ไฟล์ `images` — semantic แบบ full-sync: ละ `gallery` ไว้เก็บ image ที่มีอยู่, `[]` ลบทั้งหมด, id ที่อยู่ใน manifest ถูกเก็บตามลำดับ; `use-recipe.ts`); image ของ step มี REST endpoint ของตัวเองใต้ `.../preparation-steps/:stepId/images` (list / add / delete / set-primary / reorder / update-metadata)

## 3. ความสัมพันธ์

```
tb_recipe_category ──1──*──► tb_recipe              (Restrict on delete)
tb_recipe_cuisines ──1──*──► tb_recipe              (Restrict on delete)

tb_recipe
    │
    │ 1
    │
    ├──*──► tb_recipe_ingredient (Cascade)
    │             │
    │             ├──► tb_product       (Restrict, เมื่อ ingredient_type = product)
    │             ├──► tb_recipe        (Restrict, ชื่อ SubRecipeIngredients,
    │             │                      เมื่อ ingredient_type = recipe — self-referential)
    │             ├──► tb_unit          (Restrict, recipe_ingredient_unit)
    │             └──► tb_unit          (Restrict, recipe_inventory_unit, nullable)
    │
    ├──*──► tb_recipe_preparation_step  (Cascade)
    │             │
    │             └──*──► tb_recipe_preparation_step_image (Cascade)
    │
    ├──*──► tb_recipe_image             (Cascade — header gallery)
    │
    ├──*──► tb_recipe_yield_variant     (Cascade, ชื่อ RecipeYieldVariants)
    │             │
    │             ├──► tb_recipe (DefaultVariant — back-ref ผ่าน tb_recipe.default_variant_id)
    │             └──► tb_recipe_pricing_history (Cascade)
    │
    ├──*──► tb_recipe_version           (Cascade)
    │
    └──*──► tb_recipe_pricing_history   (Cascade)

tb_recipe_category ──*──*──► tb_recipe_category (self-referential, CategoryHierarchy)

tb_recipe_equipment_category ──1──*──► tb_recipe_equipment
    (อุปกรณ์อ้างอิงจาก JSON prep-step ไม่ผ่าน FK)
```

หมายเหตุ:

- **Recipe → ingredient** เป็น 1-to-many ด้วย **Cascade on delete** — soft-deleting / hard-deleting สูตรเอาบรรทัดวัตถุดิบไปด้วย จงใจ: บรรทัดวัตถุดิบไม่มีความหมายโดยไม่มี parent recipe
- **Recipe → sub-recipe** (recipe-as-ingredient) เป็น **self-referential 1-to-many** ผ่าน `tb_recipe_ingredient.sub_recipe_id` relation ชื่อ `SubRecipeIngredients` แยกจาก relation `recipe_id` หลัก back-reference `tb_recipe_used_in_recipes` บน `tb_recipe` คือผกผัน — กำหนดสูตร หา parent recipe ที่ใช้เป็น sub-recipe consumer ที่ live ตัวเดียวคือ delete guard ใน `recipe.service.ts` (`RECIPE_USED_AS_SUB_RECIPE` เมื่อ count ไม่เป็นศูนย์); ไม่มี dashboard การวิเคราะห์ผลกระทบ
- **Recipe → preparation step / yield variant / version / pricing history** ทั้งหมดเป็น 1-to-many ด้วย **Cascade on delete**
- **Recipe → category / cuisine** เป็น many-to-one ด้วย **Restrict on delete** — category / cuisine ไม่สามารถลบในขณะที่สูตรอ้างอิง; user ต้อง reassign ก่อน
- **Ingredient → unit (สองเส้นทาง)** — `ingredient_unit_id` (UoM สูตร จำเป็น) และ `inventory_unit_id` (UoM สต๊อก nullable) ทั้งคู่เป็น FK เข้าไปยัง `tb_unit` พร้อม relation ที่ตั้งชื่อแยก `conversion_factor` บนบรรทัดเชื่อมทั้งสอง; สำหรับ recipe explosion ที่ขับเคลื่อนด้วยคลัง ([inventory](/th/inventory/inventory) OUT movement ในการขายเมนู) หน่วยสต๊อกและ conversion factor คือสิ่งสำคัญ
- **Ingredient → product** เป็น Restrict on delete — สินค้าไม่สามารถ hard-delete ในขณะที่สูตรอ้างอิง ในทางปฏิบัติ soft-delete สินค้าคือรูปแบบปฏิบัติการ
- **ไม่มีตาราง `tb_menu_item` หรือ `tb_recipe_menu_item` join** carmen/docs PRD อ้างอิง linkage Recipe → Menu Item; ใน canonical tenant schema modelling menu-item อยู่นอกโมดูล recipe (น่าจะใน POS-integration layer หรือ application-layer mapping) ดู Section 5 สำหรับความแตกต่าง
- **ไม่มีตาราง `tb_recipe_comment`** — โมดูล recipe ไม่มี audit trail thread workflow / comment ในรูปแบบมาตรฐานของ GRN / SR / PR / PO Audit มาจาก `tb_recipe_version` (snapshot เต็ม) คอลัมน์ audit ต่อแถว (`created_at` / `created_by_id` / `updated_at` / `updated_by_id`) และ `tb_recipe_pricing_history.change_reason` การอภิปรายอิสระไม่เป็น first-class บนสูตร
- FK `Restrict` ทั้งหมดเป็น constraint foreign-key บริสุทธิ์; application บังคับใช้ soft-delete cascade ผ่านการตรวจสอบ `deleted_at` ที่ service layer แทนการพึ่งพา semantic cascade ของ Postgres

## 4. Enum

- **`enum_recipe_status`** — สามค่า เฉพาะ recipe Default `DRAFT` ใช้บน `tb_recipe.status`
  - `DRAFT` — สถานะเริ่มต้น (default ของ backend) สูตรกำลังถูก author; costing อาจไม่ครบ
  - `PUBLISHED` — สถานะ "live" **ไม่มี gate ความครบถ้วนถูกบังคับใช้** — สถานะเป็น dropdown ธรรมดาบน toolbar ของสูตร และค่าใดก็ได้ตั้งได้บนการ save ใดก็ได้; พฤติกรรม transition เดียวของ backend คือการ stamp `published_at = now()` เมื่อสถานะเปลี่ยนเป็น `PUBLISHED` (`recipe.service.ts update()/patch()`) ไม่มีแถว `tb_recipe_version` ถูกเขียนเมื่อ publish หรือเมื่อแก้ภายหลัง (ตารางไม่มี writer)
  - `ARCHIVED` — สถานะถอนจากการใช้งาน `archived_at` ถูก stamp บนการเปลี่ยน เข้าถึงได้อิสระจาก dropdown เดียวกันเช่นกัน; ไม่มีอะไรในโค้ดที่ตัด archived recipe ออกจาก search หรือ block การแก้พวกมัน
  - transition ทุกทิศทาง (`DRAFT ⇄ PUBLISHED ⇄ ARCHIVED` รวมถึง `ARCHIVED → DRAFT`) เป็นไปได้ผ่าน dropdown เดียวกัน — วงจรชีวิตทางเดียวแบบเข้มงวดที่อธิบายใน carmen/docs ไม่ถูกบังคับใช้ที่ไหนเลย
- **`enum_recipe_difficulty`** — สามค่า เฉพาะ recipe Default `MEDIUM` ใช้บน `tb_recipe.difficulty` Display-only / filter-only; ไม่มีน้ำหนักกฎทางธุรกิจ
  - `EASY` — เทคนิคขั้นต่ำ; เหมาะสำหรับผู้ฝึกหัด
  - `MEDIUM` — การรันครัวมาตรฐาน
  - `HARD` — เทคนิคขั้นสูง; พนักงานอาวุโสหรือการกำกับโดย executive-chef
- **`enum_ingredient_type`** — สองค่า เฉพาะ recipe ไม่มี default ชัดเจนที่ระดับ model (application ตั้งบน row insert) ใช้บน `tb_recipe_ingredient.ingredient_type` Discriminator ที่ตัดสินว่า FK ตัวไหนถูก populate (`product_id` สำหรับ `product`, `sub_recipe_id` สำหรับ `recipe`)
  - `product` — วัตถุดิบ resolve เป็นแถว `tb_product`
  - `recipe` — วัตถุดิบ resolve เป็นแถว `tb_recipe` อื่น (sub-recipe)
- **`enum_temperature_unit`** — สองค่า เฉพาะ recipe Default `c` ใช้บน `tb_recipe_preparation_step.temperature_unit`
  - `c` — Celsius
  - `f` — Fahrenheit
- **`enum_cuisine_region`** — หกค่า เฉพาะ recipe ไม่มี default ใช้บน `tb_recipe_cuisines.region` tag Region สำหรับข้อมูลหลัก cuisine; รองรับการ filter ตาม region และรายงาน
  - `ASIA`, `EUROPE`, `AMERICAS`, `AFRICA`, `MIDDLE_EAST`, `OCEANIA`

## 5. ความแตกต่างจาก carmen/docs

`RECIPE-Overview.md`, `RECIPE-PRD.md`, `RECIPE-Business-Requirements.md`, `RECIPE-Component-Structure.md`, `recipe-management.md` และ `recipe-create-edit-page.md` อธิบาย model interface TypeScript และชุดฟีเจอร์ที่ต่างจาก canonical Prisma schema ในหลายวิธีสำคัญ ความแตกต่างด้านล่างถูกแคตตาล็อกจากแหล่งเหล่านั้น

| # | รายการ | carmen/docs บอกว่า | Prisma มี | การดำเนินการ |
|---|------|------------------|------------|--------|
| 1 | ค่าสถานะของสูตร | PRD `status: 'draft' | 'published'` (วงจรชีวิตสองสถานะ); User-Flow-Diagram แสดงสถานะ "Archive" ที่สามแต่ไม่ list ใน enum สถานะ Business Requirements `REC_ST_001` บอก "Valid statuses are 'draft' and 'published'" | `tb_recipe.status` ใช้ `enum_recipe_status { DRAFT, PUBLISHED, ARCHIVED }` สามค่า Archived เป็นสถานะ first-class พร้อมคอลัมน์ timestamp ของตัวเอง (`archived_at`) | ถือ Prisma เป็น canonical อัปเดต carmen/docs ให้สะท้อนวงจรชีวิตสามสถานะ Section 4 ของหน้านี้ list ค่าสาม |
| 2 | enum ประเภทวัตถุดิบ | Business Requirements `Ingredient.type: 'product' | 'recipe'` (lowercase สองค่า ไม่มี constraint ชัดเจน) | `tb_recipe_ingredient.ingredient_type` ใช้ `enum_ingredient_type { product, recipe }` (lowercase สองค่า — ตรงกันเชิงแนวคิดแต่ชื่อคอลัมน์บน model คือ `ingredient_type` ไม่ใช่ `type`) | ตรงเชิงแนวคิด; ชื่อคอลัมน์ต่างจาก interface carmen/docs Document ชื่อคอลัมน์จริง |
| 3 | total time บนสูตร | PRD `Recipe.totalTime: number // Total time in minutes` Business Requirements ถือ `totalTime` เป็นฟิลด์ที่เก็บ | `tb_recipe` **ไม่มี** คอลัมน์ `total_time` Rollup คำนวณที่เวลา display เป็น `prep_time + cook_time` | อัปเดต carmen/docs ให้ mark `totalTime` เป็น computed / display-only ไม่ใช่คอลัมน์ที่เก็บ |
| 4 | Menu Item linkage | RECIPE-Overview.md, RECIPE-Business-Requirements.md และหน้า index ของ wiki อธิบาย linkage Recipe → Menu Item ที่ "สูตรเดียวสามารถรองรับ menu item หลายตัว; menu item เดียวสามารถประกอบจากหลายสูตร" RECIPE-PRD.md § 5 list `Recipe to Menu Item` เป็นความสัมพันธ์สำคัญ | tenant Prisma schema **ไม่มี** ตาราง `tb_menu_item` หรือตาราง `tb_recipe_menu_item` join model `tb_menu` เดียวใน schema (line 1412) คือ config menu navigation ไม่ใช่ menu item ที่ขายได้ Modelling menu-item อยู่นอกโมดูล recipe — น่าจะใน POS-integration layer หรือ application-resolved mapping | Document ว่า menu-item linkage **ไม่อยู่** ใน canonical tenant schema รูปแบบ recipe-as-source-of-truth-for-theoretical-consumption ยังถือ แต่ join menu-item เป็น application-layer หรือในโมดูลแยก ข้อความ overview wiki ที่อธิบาย "menu item linkage" ยังถูกต้องเชิงแนวคิดเป็นรูปแบบ domain ไม่ใช่ความสัมพันธ์ schema |
| 5 | Workflow / comment / activity log | RECIPE-Component-Structure.md และ page spec อธิบาย workflow การอนุมัติสูตร / review (REC_ST_003 "Status changes must be tracked with timestamp and user") และ component changelog / audit trail | `tb_recipe` **ไม่มี** `workflow_id` ไม่มี `workflow_history` ไม่มี `workflow_current_stage` และ **ไม่มี** ตาราง `tb_recipe_comment` การติดตามการเปลี่ยนสถานะผ่าน `tb_recipe_version` (snapshot เต็ม) บวกคอลัมน์ audit ต่อแถว (`created_at`, `created_by_id`, `updated_at`, `updated_by_id`) และสอง timestamp การเปลี่ยนสถานะ (`published_at`, `archived_at`) | อัปเดต carmen/docs ให้อธิบาย versioning (ผ่าน `tb_recipe_version`) เป็นกลไก audit ไม่ใช่ workflow / thread comment การอนุมัติเป็นนโยบาย application-layer ไม่ใช่ workflow ระดับ schema |
| 6 | Yield variants | RECIPE-Business-Requirements.md กล่าวถึง "yield" เป็นเลขเดี่ยว + หน่วยบนสูตร PRD อธิบาย scaling แต่ไม่ใช่ variant | `tb_recipe_yield_variant` เป็นเอนทิตี first-class สูตรอาจมี 0 หรือหลาย variant; `tb_recipe.default_variant_id` ชี้ไปยัง default Variant มี `cost_per_unit`, `selling_price`, `food_cost_percentage`, `gross_margin`, `wastage_rate`, `shelf_life` และ `min/max_order_quantity` ของตัวเอง วัตถุดิบสามารถ variant-scope ผ่าน `tb_recipe_ingredient.tb_recipe_yield_variantId` | อัปเดต carmen/docs ให้อธิบายโมเดล yield-variant เส้นทาง "yield เดี่ยว" คือ case ไม่มี variant (`tb_recipe.base_yield + base_yield_unit` เท่านั้น); เส้นทาง multi-variant ใช้ตาราง variant |
| 7 | Pricing history | RECIPE-Page-Flow.md กล่าวถึง "Price History" เป็น display panel ใน tab costing; PRD ถือ price เป็นคอลัมน์เดียว | `tb_recipe_pricing_history` เป็นเอนทิตี first-class จับ snapshot per-effective-date ของต้นทุน ราคา % food-cost gross margin และ benchmark คู่แข่ง แต่ละ variant สามารถมี pricing history ของตัวเอง (`variant_id` nullable บนแถว) | Document pricing history เป็น timeline ที่ persist ไม่ใช่ rollup display ใช้โดย dashboard cost-drift และรายงาน variance |
| 8 | Carbon footprint | RECIPE-Overview.md กล่าวถึงผลกระทบสิ่งแวดล้อมเป็นฟีเจอร์; PRD `Recipe.carbonFootprint: number` | `tb_recipe.carbon_footprint` เป็น `Decimal(20, 5)` พร้อม default 0 ไม่มีคอลัมน์ footprint per-ingredient บน `tb_recipe_ingredient` — ค่าระดับสูตรคือ aggregate; rollup per-ingredient คำนวณที่ application จาก footprint ระดับสินค้า (ซึ่งอยู่บน `tb_product` ถ้ามี หรือในแหล่งข้อมูล sustainability ภายนอก) | ตรงเชิงแนวคิด; document rollup เป็น application-computed ไม่ใช่ schema-stored ที่ระดับวัตถุดิบ |
| 9 | Linkage อุปกรณ์ | Page-spec อธิบาย "Equipment/Tools Required" เป็น tab บนหน้า create / edit สูตรพร้อม master อุปกรณ์ first-class | `tb_recipe_equipment` และ `tb_recipe_equipment_category` เป็นตารางข้อมูลหลัก first-class แต่อุปกรณ์ถูกอ้างอิงจาก `tb_recipe_preparation_step.equipment` (array JSON ของ equipment ref) แทนผ่าน join foreign-key ไม่มีตาราง `tb_recipe_recipe_equipment` join | Document ว่าอุปกรณ์เป็น per-step JSON ไม่ใช่ per-recipe FK ตาราง master มีอยู่สำหรับแคตตาล็อกอุปกรณ์; linkage ด้าน recipe เป็น denormalise โดยการออกแบบ |
| 10 | Unit conversion บนวัตถุดิบ | PRD อธิบาย "Unit conversions must be handled for inventory management" (REC_IN_005) เป็นกฎทางธุรกิจแต่ไม่ model สองคอลัมน์ unit | `tb_recipe_ingredient` มี FK unit **สอง** ตัว: `ingredient_unit_id` (UoM แสดงผลของสูตร) และ `inventory_unit_id` (UoM สต๊อก) เชื่อมโดย `conversion_factor` โมเดล two-unit คือสิ่งที่ทำให้สูตรพูด "200 g แป้ง" ขณะที่คลังถือ "ถุง 1 kg" `inventory_qty = qty × conversion_factor` | Document รูปแบบ two-unit อย่างชัดเจน Cost-per-unit บนบรรทัดเป็นใน UoM สูตรตาม default (หรือใน UoM คลังขึ้นอยู่กับธรรมเนียม tenant); conversion คือคำมั่นของ schema ในการเชื่อม UoM ที่ไม่มีการสูญเสีย |
| 11 | Wastage cost vs net cost | Business Requirements `Ingredient` interface มี `wastage: number` และ `totalCost: number` กฎการคำนวณต้นทุนบอก `Total Cost = Σ(Ingredient Cost × (1 + Wastage%))` | `tb_recipe_ingredient` persist **ทั้ง** `net_cost` (total `(1 + wastage%)`) และ `wastage_cost` (ส่วนประกอบ wastage เพียงอย่างเดียว) สองคอลัมน์ให้รายงานแยก "ต้นทุนวัตถุดิบดิบ" จาก "wastage allowance" โดยไม่ต้องคำนวณใหม่ | Document ทั้งสองคอลัมน์ `net_cost` คือสิ่งที่ roll up ไปยัง `tb_recipe.total_ingredient_cost`; `wastage_cost` คือรายงานเท่านั้น |

## 6. แหล่งอ้างอิง

- **หลัก (แหล่งความจริง):** Prisma schema ที่ list ใน header callout — concretely `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` (โมเดล recipe ทั้งสิบสองที่ lines 5578–6073 บวก enum เฉพาะ recipe สี่ตัวที่ lines 5552–5572 และ `enum_cuisine_region` ที่ lines 5543–5550 และ flag `tb_product.is_used_in_recipe` ที่ line 1518) และ `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-platform/prisma/schema.prisma` (verify ว่าไม่มีโมเดล recipe)
- **Backend implementation:** `../carmen-turborepo-backend-v2/apps/micro-business/src/master/recipe/` (recipe CRUD, sub-service ของ prep-step + image), `.../master/recipe-category/`, `.../master/recipe-cuisine/`, `.../master/recipe-equipment/`, `.../master/recipe-equipment-category/`; REST surface ของ gateway ใน `../carmen-turborepo-backend-v2/apps/backend-gateway/src/config/config_recipes/` (และ dir พี่น้อง `config_recipe-*`)
- **API contracts:** `../carmen-turborepo-backend-bruno/collections/carmen-inventory/config/recipe/` (recipe CRUD ที่ `/api/config/{bu_code}/recipes`), `.../config/recipes/` (endpoint preparation-steps + step-image) และโฟลเดอร์ `recipe-categories` / `recipe-cuisines` / `recipe-equipment` / `recipe-equipment-categories`
- **รอง (cross-check แนวคิด):**
  - `../carmen/docs/recipe-module/RECIPE-Overview.md` — วัตถุประสงค์ของโมดูล ฟีเจอร์สำคัญ บทบาท user; ความแตกต่างใน Section 5 (รายการ 1, 4, 5, 8)
  - `../carmen/docs/recipe-module/RECIPE-PRD.md` — user story, ข้อกำหนดฟีเจอร์, ข้อกำหนดข้อมูล, ความสัมพันธ์สำคัญ; ความแตกต่างใน Section 5 (รายการ 1, 2, 3, 4, 6, 7, 10)
  - `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md` — กฎทางธุรกิจ `REC_CR_001`–`REC_CR_005` (creation), `REC_CO_001`–`REC_CO_005` (costing), `REC_IN_001`–`REC_IN_005` (ingredient), `REC_ST_001`–`REC_ST_004` (status); ความแตกต่างใน Section 5 (รายการ 1, 2, 3, 5, 10, 11)
  - `../carmen/docs/recipe-module/RECIPE-Component-Structure.md` — สัญญา component UI; ความแตกต่างใน Section 5 (รายการ 5, 9)
  - `../carmen/docs/recipe-module/RECIPE-Page-Flow.md` — flow หน้าและ user journey; ความแตกต่างใน Section 5 (รายการ 5, 7)
  - `../carmen/docs/recipe-module/RECIPE-User-Flow-Diagram.md` — flow ภาพ; ความแตกต่างใน Section 5 (รายการ 1 — สามสถานะ vs สองสถานะ)
  - `../carmen/docs/recipe/recipe-management.md` — layout หน้า master-list / create-edit / costing-sheet / preparation / media / scaling / category; การอ้างอิงระดับ layout สำหรับหน้า create-edit และ view
  - `../carmen/docs/recipe/recipe-create-edit-page.md` — แหล่ง page-spec สำหรับ interface แบบ tab ของ form สูตร (Basic Info, Ingredients, Method, Media, Costing, Nutritional)
  - `../carmen/docs/recipe/recipe-list-page.md` — page spec ของ master-list
  - `../carmen/docs/recipe/recipe-view-page.md` — page spec ของ detail page อ่านอย่างเดียว
- โมดูลที่เกี่ยวข้อง: [product](/th/inventory/product) (วัตถุดิบของสูตรอ้างอิงสินค้าผ่าน `tb_recipe_ingredient.product_id`; flag `tb_product.is_used_in_recipe` แยกแยะสินค้าที่ recipe-eligible), [inventory](/th/inventory/inventory), [costing](/th/inventory/costing) และ [store-requisition](/th/inventory/store-requisition) — integration แบบ theoretical-consumption, costing จาก valuation และ recipe→SR auto-create ที่อธิบายใน carmen/docs **ไม่มี implementation** ใน codebase ปัจจุบัน (ไม่มีการอ้างอิง `recipe_id` ที่ไหนเลยใน service ของ SR และไม่มีโค้ดฝั่ง recipe ที่เขียน inventory transaction)
