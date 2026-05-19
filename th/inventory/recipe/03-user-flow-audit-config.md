---
title: สูตรอาหาร (Recipe) — User Flow — Audit & Config
description: flow ของ System Administrator + Auditor ในโมดูลสูตร — config (หมวดหมู่ ประเภทอาหาร RBAC integration) versioning audit compliance review
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, user-flow, audit-config, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — User Flow — Audit & Config

> **At a Glance**
> **Persona:** System Administrator + Auditor &nbsp;·&nbsp; **โมดูล:** [recipe](/th/inventory/recipe) &nbsp;·&nbsp; **ขั้นตอน workflow:** off-path — ตั้งค่า (หมวดหมู่ / ประเภทอาหาร / อุปกรณ์ / RBAC / publish-gate / integration) และ audit (versioning, pricing history) &nbsp;·&nbsp; **สิทธิ์สำคัญ:** เขียน config (Sysadmin), read-history (Auditor), soft-delete archived (Sysadmin)
> **persona นี้ทำอะไร:** Sysadmin เป็นเจ้าของข้อมูลหลัก RBAC และการ wire integration; Auditor review trail เวอร์ชันและ pricing-history สำหรับ compliance

## 1. บทบาทในโมดูลนี้

persona **Audit / Config** ครอบคลุมสอง role ที่ควบคุมความถูกต้อง ความครบ และการตั้งค่าของโมดูล recipe: **System Administrator** (เป็นเจ้าของการตั้งค่าโมดูล recipe — ข้อมูลหลัก `tb_recipe_category` รวมลำดับชั้นและ `default_cost_settings` ข้อมูลหลัก `tb_recipe_cuisines` master `tb_recipe_equipment_category` และ `tb_recipe_equipment` การ map RBAC ของสูตร `recipe:create / edit / publish / archive / edit-published / edit-cost / approve-menu-link / read / read-history` นโยบาย tenant publish-gate ที่ตัดสินใจว่าการ publish margin off-target ต้องการ co-approval ของ Cost Controller หรือไม่ และการ wire integration กับ `[product](/th/inventory/product)` / `[inventory](/th/inventory/inventory)` / `[store-requisition](/th/inventory/store-requisition)` สำหรับ theoretical-consumption fan-out และ SR auto-create) และ **Auditor** (review ประวัติสูตรอ่านอย่างเดียว — snapshot `tb_recipe_version` timeline `tb_recipe_pricing_history` คอลัมน์ audit ต่อแถว `created_by_id` / `updated_by_id` / `created_at` / `updated_at` timestamp การ publish / archive `published_at` / `archived_at` thread comment บนแต่ละ `tb_recipe_version.change_summary` — เพื่อยืนยันว่าการควบคุมทำงาน การ publish off-target ถูก co-approve และ chain ของการ revise กระทบยอดกับโมเดลอำนาจ) ทั้งสอง role ไม่ทำ action บน happy path ของสูตร; พวกเขาทำ action บน **periphery** — ก่อนสูตรใดอยู่ (config) ระหว่างวงจรชีวิต (การบังคับใช้ RBAC สุขภาพ integration) และหลัง publish (audit trace) Sysadmin ถือ read / write เต็มบนตาราง config และการ map RBAC; Auditor เป็น read-only บน recipe library (`recipe:read` + `recipe:read-history`) และบนประวัติการตั้งค่า ไม่มีเส้นทาง "void" หรือ "admin-cancel" บนสูตร — สูตรไม่ใช่เอกสารธุรกรรม; สุขภาพข้อมูลบนสูตรที่ archive เป็นอำนาจ delete เดียว และอยู่กับ Sysadmin ตาม `REC_AUTH_014`

## 2. Entry Point และ Primary Flow

**Entry point (หนึ่งต่อ sub-role):**

- **Sysadmin — Config console** — Editor master สำหรับหมวดหมู่ ประเภทอาหาร อุปกรณ์; matrix RBAC ต่อ role / หมวดหมู่; การตั้งค่านโยบาย tenant สำหรับ publish-gate, edit-published-with-versioning, นโยบายการทดแทน sub-recipe, การ wire recipe → SR auto-create
- **Sysadmin — Dashboard สุขภาพ integration** — แสดงสถานะของการ coupling ต้นน้ำ / ปลายน้ำ: chain vendor pricelist → product cost → recipe cost-drift (`REC_XMOD_005` / `REC_XMOD_006`), การ wire recipe → SR auto-create (`REC_XMOD_007`), recipe → inventory theoretical-consumption fan-out (`REC_XMOD_003`)
- **Auditor — มุมมองประวัติสูตร** — browser `tb_recipe_version` อ่านอย่างเดียวสำหรับสูตรใด; มุมมอง timeline; diff per-version (snapshot JSON header / วัตถุดิบ / ขั้นตอน / variant)
- **Auditor — มุมมอง Pricing-history** — timeline `tb_recipe_pricing_history` อ่านอย่างเดียว; filter ตาม date, change reason, หมวดหมู่ recipe

**Primary flow (การกำกับ / การตั้งค่า 10 ขั้นตอน — รันต่อเนื่องข้าม period ไม่ใช่ per-recipe):**

1. **(Sysadmin) ตั้งค่า category master ที่ tenant onboarding** นิยามลำดับชั้น `tb_recipe_category` (Appetiser / Main / Dessert / Beverage / ...; sub-category ด้านล่าง); ตั้ง `default_cost_settings` per category (% food-cost เป้าหมาย % labor / overhead) ที่สูตรใหม่จะสืบทอดที่เวลา create Cost Control Department เซ็นอนุมัติเป้าหมายระดับหมวดหมู่
2. **(Sysadmin) ตั้งค่า cuisine master** Populate `tb_recipe_cuisines` ด้วย cuisine ที่ operation serve (ไทย / อิตาเลียน / ฝรั่งเศส / ญี่ปุ่น / fusion) แต่ละตัว tag โดย `enum_cuisine_region`; populate `popular_dishes` และ `key_ingredients` สำหรับบริบท menu engineering
3. **(Sysadmin) ตั้งค่า equipment master** Populate `tb_recipe_equipment_category` และ `tb_recipe_equipment` ด้วยแคตตาล็อกอุปกรณ์ครัว (oven sous-vide rig mixer ฯลฯ) เพื่อให้ chef อ้างอิงอุปกรณ์ใน JSON prep-step
4. **(Sysadmin) ตั้งค่า RBAC** Map role → permission per หมวดหมู่ (executive chef = ทุกหมวดหมู่ pastry chef = desserts เท่านั้น cost controller = ฟิลด์ cost / pricing เท่านั้น); กำหนด user ให้ role; จัดการการ delegate (chef ลา → deputy publish ในหมวดหมู่ของพวกเขาได้) ชุด permission ของสูตรคือ `recipe:create / edit / publish / archive / edit-published / edit-cost / approve-menu-link / read / read-history`
5. **(Sysadmin) ตั้งค่า publish-gate และนโยบาย tenant** ตัดสินใจว่าการ publish margin off-target (`actual_food_cost_percentage > target + tolerance`) ต้องการ co-approval ของ Cost Controller ตาม `REC_AUTH_007` หรือไม่; ตัดสินใจว่าการแก้สูตร `PUBLISHED` ใช้ in-place ด้วย versioning (`REC_POST_004`) หรือต้องการ un-publish round-trip (`REC_POST_005`); ตัดสินใจ tolerance band ของ tenant สำหรับการตรวจจับ off-target (โดยทั่วไป 2 percentage points)
6. **(Sysadmin) Wire integration hook** ยืนยันว่า chain ต้นน้ำ (vendor pricelist → product cost → event cost-drift ของสูตร) ยิงถูกต้อง; ยืนยันว่า chain ปลายน้ำ — recipe → SR auto-create (`REC_XMOD_007`), recipe → inventory theoretical-consumption (`REC_XMOD_003`), recipe → menu-item linkage (`REC_XMOD_008`) — ปฏิบัติการ ความล้มเหลวใน chain ใดแสดงเป็น alert integration
7. **(Sysadmin) จัดการวงจรชีวิตของ master** Soft-delete cuisine / หมวดหมู่ที่ไม่ใช้แล้ว (FK `Restrict` จาก `tb_recipe` บล็อก hard delete; soft delete คือรูปแบบปฏิบัติการ); merge หมวดหมู่ที่ซ้ำ; reorder ลำดับชั้น Sysadmin ประสานกับ Cost Control Department บนการเปลี่ยนระดับหมวดหมู่ที่กระทบ % food-cost เป้าหมาย
8. **(Auditor) Audit sample เป็นระยะ** Sample สูตร `PUBLISHED` ที่ commit ข้าม period; สำหรับแต่ละ verify: (a) event publish มีแถว `tb_recipe_version` ที่สอดคล้องกับ `published = true` และ `change_summary` populate; (b) เมื่อ margin จริง off-target ที่ publish co-approval ของ Cost Controller บันทึกใน `change_summary` หรือ log signoff ตาม `REC_AUTH_007`; (c) ทุกการแก้สูตร `PUBLISHED` เขียนแถว `tb_recipe_version` ใหม่ตาม `REC_POST_004`; (d) ทุกการเปลี่ยน cost / ราคาเขียนแถว `tb_recipe_pricing_history` ตาม `REC_POST_010` ด้วย `change_reason` populate; (e) คอลัมน์ audit กระทบยอด (`created_by_id` เป็น user ที่รู้จัก; chain `updated_by_id` สอดคล้อง)
9. **(Auditor) Compliance review บน cost drift และ sub-recipe cascade** Sample สูตรที่ `tb_recipe_pricing_history.change_reason` บ่งบอก sub-recipe cascade (`REC_POST_006`) หรือ cost-drift update จาก costing (`REC_XMOD_006`); verify ว่า chain cascade สอดคล้องภายใน (การเปลี่ยน cost ของสูตร parent กระทบยอดกับการเปลี่ยน cost ของ sub-recipe และการเปลี่ยน cost ของวัตถุดิบใบไม้); verify ว่า cascade trigger action review ที่ margin ที่ได้เคลื่อนนอก tolerance (signoff ของ Cost Controller หรือการ revise ของ Chef)
10. **(ทุก sub-role) ออกการค้นพบและ action แก้ไข** การค้นพบของ Sysadmin (config gap, anomaly RBAC, ความล้มเหลว integration) trigger การแก้ไข config การค้นพบของ Auditor (แถวเวอร์ชันขาด co-approval ขาด cascade ที่ไม่กระทบยอด) trigger การสอบสวนและการปรับปรุงกระบวนการ; การค้นพบที่ยังคงอยู่อาจขับเคลื่อนการเปลี่ยนนโยบาย (publish gate เข้มขึ้น RBAC ละเอียดกว่า การตรวจสอบสุขภาพ integration แรงกว่า)

## 3. Decision Branch

- **นโยบาย tenant: in-place vs un-publish สำหรับการแก้ `PUBLISHED`**: Sysadmin เลือกระหว่าง (a) `edit_published_with_versioning = true` (การแก้ใช้ทันทีกับสูตร `PUBLISHED`; เขียนแถว `tb_recipe_version`; theoretical consumption ใช้สูตรใหม่จาก timestamp การแก้ไป) และ (b) `edit_published_with_versioning = false` (การแก้ต้องการ `PUBLISHED → DRAFT` round-trip; สูตรไม่ขับเคลื่อน theoretical consumption ขณะใน `DRAFT`; audit ปลอดภัยกว่าแต่ friction ปฏิบัติการมากกว่า)
- **นโยบาย tenant: tolerance off-target**: Sysadmin ตั้ง tolerance band (เช่น 2 percentage points) สำหรับเมื่อ co-approval ของ Cost Controller จำเป็นที่ publish ตาม `REC_AUTH_007` Tolerance เข้มกว่า = co-approval มากขึ้น (friction การควบคุมมากขึ้น); tolerance หลวมกว่า = co-approval น้อยลง (autonomy มากขึ้นสำหรับ chef)
- **Category default-cost-settings — broad vs granular**: Sysadmin / Cost Control Department เลือกระหว่าง (a) การตั้งค่า per-category broad (เป้าหมาย food-cost % เดียวสำหรับ Mains ทั้งหมด) หรือ (b) การตั้งค่า per-sub-category granular (เป้าหมายต่างสำหรับ Premium Mains vs Standard Mains Bar Snacks vs Sit-Down Snacks) Granular ถูกต้องกว่าแต่ดูแลยากกว่า
- **RBAC scope — category-bound vs full**: Sysadmin เลือกว่า chef scope ไปยังหมวดหมู่เฉพาะ (Pastry Chef → Desserts เท่านั้น) หรือมีการเข้าถึง library เต็ม การ binding หมวดหมู่ align RBAC กับความเป็นจริงปฏิบัติการแต่ต้องการการกำหนด user-role per-category
- **Soft-delete สูตรที่ archive หลังการเก็บข้อมูล**: Sysadmin ตัดสินใจช่วงเวลาการเก็บข้อมูลสำหรับสูตร `ARCHIVED` ก่อน soft-delete สำหรับสุขภาพข้อมูล (โดยทั่วไปหลายปีสำหรับ compliance / audit แล้ว soft-delete) แถว soft-delete ยังคงใน database (audit ได้) แต่หายจาก query default
- **การค้นพบ audit — gap ของระบบ vs gap ของกระบวนการ**: Auditor จำแนกการค้นพบเป็น gap ของระบบ (การควบคุมของโมดูล recipe ไม่บังคับใช้กฎที่ควรบังคับใช้ — เช่น การ publish off-target โดยไม่มี co-approval — ต้องการการ fix code / config) หรือ gap ของกระบวนการ (กฎถูกบังคับใช้แต่กระบวนการรอบ ๆ มันอ่อน — เช่น co-approval บันทึกแต่ไม่ review — ต้องการการปรับปรุงกระบวนการ / การอบรม)

## 4. Exit Point / Handoff

การมีส่วนร่วมของ persona Audit / Config ไม่ "จบ" per recipe — มันเป็นการกำกับต่อเนื่อง การ action การกำกับแต่ละครั้งมี handoff ที่นิยามไว้:

- **การเปลี่ยน config ของ Sysadmin ใช้** — handoff ไปยัง **persona ทั้งหมด (prospective)**; หมวดหมู่ / cuisine / กฎ RBAC ใหม่ใช้กับสูตรใหม่จาก save time ไป; สูตรเดิมไม่ update retroactively เว้นแต่ใช้ใหม่ชัดเจน (operation ด้วยมือ) การประสานกับ Cost Control Department บนการเปลี่ยน cost-setting; กับ F&B Ops บนการเปลี่ยน RBAC / permission ที่กระทบอำนาจกลยุทธ์
- **Sysadmin soft-delete master (หลังการ clear Restrict-FK)** — handoff ไปยัง **Chef** เพื่อ reassign สูตรออกจากหมวดหมู่ / cuisine ที่จะถูกลบก่อนการลบ; เมื่อ clear แล้ว master ถูก soft-delete
- **Auditor finding — gap ของระบบ** — handoff ไปยัง **Sysadmin** สำหรับการ fix code / config; finding ถูก log และการ fix ติดตามผ่านการจัดการการเปลี่ยน tenant
- **Auditor finding — gap ของกระบวนการ** — handoff ไปยัง **Cost Control Department / F&B Ops / Chef** สำหรับการปรับปรุงกระบวนการ; finding อาจ trigger การ review นโยบาย (publish gate เข้มขึ้น review margin บ่อยขึ้น การอบรมบนกระบวนการ revise)
- **Auditor finding — audit สะอาด** — ไม่มี handoff; audit ของ period log เป็นสะอาดและ cycle ถัดไปดำเนินการ
- **Alert สุขภาพ integration** — handoff ไปยัง **Sysadmin** เพื่อสอบสวน chain ที่ล้มเหลว (vendor → product → recipe cost drift; recipe → SR auto-create; recipe → inventory theoretical OUT); การ resolve ไหลกลับผ่านโมดูลที่ได้รับผลกระทบ

persona Audit / Config คือ **safety net** ของโมดูล recipe — พวกเขาไม่ author สูตร แต่พวกเขาตั้งค่า rail ที่ persona อื่นรันบน (หมวดหมู่ cuisine RBAC นโยบาย) verify ว่า rail ถูกทำตามที่เวลา audit (versioning ลายเซ็น co-approval trace cost-drift) และทำให้ integration กับข้อมูล cost ต้นน้ำและการบริโภคปลายน้ำมีสุขภาพดี

## 5. แหล่งอ้างอิง

- Parent overview: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิต canonical และตาราง handoff ข้าม persona; Section 4 แถว "Sysadmin → persona ทั้งหมด (การเปลี่ยน config)", "Auditor — review read-only" anchor role ของ persona นี้
- `../carmen/docs/recipe-module/RECIPE-Overview.md` § General Users (และแถว `System Administrator` ใน index ของ wiki) — แหล่ง carmen/docs สำหรับ scope Sysadmin; role auditor เป็น implicit ในบริบท audit / compliance
- `../carmen/docs/recipe-module/RECIPE-Business-Requirements.md` § Maintenance and Governance — Ownership, Review Process, Change Management; แจ้งความรับผิดชอบ Sysadmin / Auditor
- `../carmen/docs/recipe-module/RECIPE-PRD.md` § Non-Functional Requirements (§ Security, § Scalability) — RBAC การ log audit การรองรับหลาย location
- `../carmen/docs/recipe/setup-pages-spec.md` — แหล่ง page-spec สำหรับหน้าจอ setup / config ที่ Sysadmin operate
- `../carmen/docs/recipe/recipe-management.md` § Recipe Categories Management — การอ้างอิงระดับ layout สำหรับการดูแล category-master
- Sibling: [03-user-flow-chef.md](./03-user-flow-chef.md) — RBAC หมวดหมู่ของ Sysadmin scope library ของ chef; Auditor review ประวัติ `tb_recipe_version` ของ chef
- Sibling: [03-user-flow-cost-controller.md](./03-user-flow-cost-controller.md) — `default_cost_settings` ของหมวดหมู่ของ Sysadmin กระทบเป้าหมาย per-recipe ของ Cost Controller; Auditor verify ว่าการแก้ cost-only trigger แถว pricing-history
- Sibling: [03-user-flow-outlet-manager.md](./03-user-flow-outlet-manager.md) — RBAC ของ Sysadmin scope การเข้าถึง read ของ outlet-manager; Auditor review การใช้ recipe-to-outlet เป็นส่วนของ variance review
- Sibling: [03-user-flow-procurement-fb-ops.md](./03-user-flow-procurement-fb-ops.md) — Sysadmin เป็นเจ้าของ permission `recipe:approve-menu-link` ที่ F&B Ops ใช้; Sysadmin wire ช่อง substitution-request
- Sibling: [01-data-model.md](./01-data-model.md) — `tb_recipe_version` (audit trail snapshot เต็ม), `tb_recipe_pricing_history` (timeline cost / ราคา), คอลัมน์ audit (`created_by_id`, `updated_by_id`, `published_at`, `archived_at`); ตารางข้อมูลหลัก (`tb_recipe_category`, `tb_recipe_cuisines`, `tb_recipe_equipment_category`, `tb_recipe_equipment`)
- Sibling: [02-business-rules.md](./02-business-rules.md) — `REC_AUTH_007` (gate co-approval ของ Cost Controller), `REC_AUTH_011`–`REC_AUTH_014` (อำนาจ F&B Ops / Sysadmin / Auditor), `REC_POST_009` (soft-delete), `REC_XMOD_009`–`REC_XMOD_010` (audit / versioning RBAC)
- ที่เกี่ยวข้อง: [product](/th/inventory/product) — Sysadmin เป็นเจ้าของ flag `is_used_in_recipe` บนสินค้าที่ gate ว่าสินค้ามีสิทธิ์เป็นวัตถุดิบ recipe หรือไม่
- ที่เกี่ยวข้อง: [costing](/th/inventory/costing) — chain integration cost-drift ที่ Sysadmin ดูแล
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — chain integration theoretical-consumption ที่ Sysadmin ดูแล
- ที่เกี่ยวข้อง: [store-requisition](/th/inventory/store-requisition) — การ wire recipe → SR auto-create ที่ Sysadmin เป็นเจ้าของ
