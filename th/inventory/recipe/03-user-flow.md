---
title: สูตรอาหาร (Recipe) — User Flow
description: วงจรชีวิตของสูตรอาหารและไฟล์ flow เฉพาะ persona สำหรับโมดูล recipe
published: true
date: 2026-07-16T04:00:00.000Z
tags: recipe, user-flow, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — User Flow

> **At a Glance**
> **โมดูล:** [recipe](/th/inventory/recipe) &nbsp;·&nbsp; **Persona:** Chef &nbsp;·&nbsp; Cost Controller &nbsp;·&nbsp; Outlet Manager &nbsp;·&nbsp; Procurement / F&B Ops &nbsp;·&nbsp; Audit / Config
> **วงจรชีวิตของ workflow:** DRAFT ⇄ PUBLISHED ⇄ ARCHIVED — ในแอปปัจจุบันการเปลี่ยนสถานะทั้งหมดเป็น dropdown สถานะแบบอิสระที่มีผลข้างเคียงเพียง timestamp เท่านั้น; RBAC gate / audit trail versioning ที่อธิบายด้านล่างเป็นเป้าหมายการออกแบบ
> **เจาะลงในมุมมองต่อ persona ด้านล่างสำหรับรายละเอียดระดับ action**

> **สถานะการติดตั้งใช้งานจริง (ตรวจสอบกับซอร์ส 2026-07-15).** flow ที่มีอยู่จริงวันนี้คือ CRUD journey เดียวที่ gate ด้วยสิทธิ์ admin: recipe list (`/operation-plan/recipe`, ค้นหา + filter สถานะ/ประเภทอาหาร/หมวดหมู่/ความยาก, สลับ list/grid) → form รายละเอียด/แก้ไขหรือสร้างใหม่ (field ส่วน header, grid วัตถุดิบแบบ preview เท่านั้น, gallery รูปภาพ, เครื่องคำนวณต้นทุนฝั่ง client) → save พร้อม optimistic locking ด้วย `doc_version` → ลบได้ตามต้องการ (ถูก block เฉพาะเมื่อถูกใช้เป็น sub-recipe) สถานะเป็น dropdown บน toolbar ที่ไม่มี gate ไม่มี permission ต่อ persona (placeholder `operation_plan.view` gate ทั้งกลุ่ม) ไม่มีกลไก publish/co-approval ไม่มีการเขียน versioning หรือ pricing-history และไม่มี integration กับ menu/POS/SR/variance ไฟล์ persona ที่ link ด้านล่างอธิบาย operating model เป้าหมาย; แต่ละไฟล์มี caveat เดียวกันนี้

## 1. ภาพรวม

หน้านี้เป็น **จุดเข้าภาพรวม** สำหรับชุด user-flow ของโมดูล `recipe` สูตรคือสูตรที่มาตรฐานและคิดต้นทุนสำหรับการผลิตหนึ่งเอาท์พุตของจานหรือเครื่องดื่ม — แถว header ใน `tb_recipe` ร่วมกับบรรทัดวัตถุดิบใน `tb_recipe_ingredient` (วันนี้มีเฉพาะระดับ schema) ขั้นตอนการเตรียมใน `tb_recipe_preparation_step` (วันนี้มีเฉพาะระดับ API) และ (ทางเลือก) yield variant หนึ่งหรือหลายตัวใน `tb_recipe_yield_variant` (วันนี้ read-only) ต่างจากเอกสารที่ขับเคลื่อนด้วย workflow (PR, PO, GRN, SR) ที่ทุกการเปลี่ยนสถานะถูก gate โดย workflow stage และเซ็นต่อบรรทัด วงจรชีวิตของสูตรเป็น **ตรง** — สามสถานะ (`DRAFT`, `PUBLISHED`, `ARCHIVED`) โดยตามดีไซน์มี RBAC ระดับ application และกฎความครบ พร้อม versioning (`tb_recipe_version`) และ pricing-history (`tb_recipe_pricing_history`) เป็นกลไก audit; gate และตัวเขียน audit เหล่านี้ยังไม่มีตัวใดถูก implement ในดีไซน์เป้าหมายสูตรคือ **แหล่งความจริงสำหรับสิ่งที่ควรถูกบริโภคเมื่อมีการขาย** (OUT movement เชิงทฤษฎีตาม [02-business-rules.md](./02-business-rules.md) `REC_XMOD_003`) — pipeline การบริโภคนั้นยังไม่มีโค้ดในวันนี้

Section 2 ด้านล่างเป็น **state machine ระดับ global** — list canonical ของการเปลี่ยนที่ถูกกฎหมายข้ามค่าสามของ `enum_recipe_status` โดยไม่ขึ้นกับใครเป็นคนทำ แต่ละไฟล์ต่อ persona (link จาก Section 3) อธิบาย *เส้นทาง* ของ persona ผ่าน state machine — entry point, action ที่มี, decision branch ที่เผชิญ, handoff ที่จบการมีส่วนร่วม Section 4 สรุป handoff ข้าม persona ที่เย็บเส้นทางบุคคลเข้าด้วยกัน การ group persona รวบ 8 persona ดิบของ carmen/docs (Chef / Kitchen Manager, Kitchen Staff, Cost Controller, Cost Control Department, Outlet Manager, Procurement Department, F&B Operations Manager, System Administrator + Auditor implicit) เป็น **role เชิงปฏิบัติการห้าตัว**: Chef, Cost Controller, Outlet Manager, Procurement / F&B Ops, Audit / Config อ่าน overview นี้ก่อนเพื่อ anchor วงจรชีวิต แล้วเจาะลงในไฟล์ persona ที่ match role ของคุณ

หมายเหตุการขาด workflow: สูตรไม่มี `workflow_id` ไม่มี `workflow_history` ไม่มี routing per-stage การเปลี่ยนสถานะเป็น API call ตรงที่ gate โดย RBAC; "การอนุมัติ" ของ publish (เมื่อนโยบาย tenant ต้องการ co-approval ของ Cost Controller สำหรับ margin off-target ตาม `REC_AUTH_007`) เป็น flag ระดับ application ที่บันทึกใน `tb_recipe_version.change_summary` ไม่ใช่ workflow stage ดังนั้น state machine ใน Section 2 ค่อนข้างสั้น — สามสถานะ การเปลี่ยนไม่กี่ตัว — และตาราง handoff ข้าม persona ใน Section 4 จับ **ช่วงเวลาความร่วมมือ** ที่เกิดข้าง state machine มากกว่าภายในมัน

## 2. วงจรชีวิตของสูตร

สถานะของสูตรเก็บบน `tb_recipe.status` และถูก constraint เป็นค่าสามที่ประกาศใน `enum_recipe_status`: `DRAFT` (ค่า default ฝั่ง backend สำหรับสูตรใหม่), `PUBLISHED` และ `ARCHIVED` **ตามที่ implement จริง "state machine" เป็นเพียง dropdown ธรรมดา** (`recipe-toolbar.tsx`): สถานะใดก็ save จากสถานะใดก็ได้ backend ไม่ปฏิเสธอะไรเลย และผลข้างเคียงเดียวของการเปลี่ยนสถานะคือ timestamp `published_at` / `archived_at` (`recipe.service.ts`) ตารางด้านล่างคือ state machine ตาม**ดีไซน์**ของ carmen/docs — permission ต่อการเปลี่ยน, gate, การเขียน versioning และผลกระทบปลายน้ำ (theoretical-consumption fan-out ตาม `REC_CALC_014` / `REC_XMOD_003`, การ cascade cost ของ sub-recipe ตาม `REC_POST_006`, snapshot pricing-history ตาม `REC_POST_010`) ทั้งหมดยังไม่ถูก implement; ดู [02-business-rules.md](./02-business-rules.md) §1.1 สำหรับ subset ที่บังคับใช้จริง

| จากสถานะ | Action | ไปสถานะ | อนุญาตให้ | เงื่อนไขเบื้องต้น |
| ---------- | ------ | -------- | ----------- | -------------- |
| `(none)` | create | `DRAFT` | Chef | Chef ถือ permission `recipe:create`; `code` กำหนดตามนโยบายการเลขของ tenant; ตั้ง `category_id` และ `cuisine_id`; `base_yield > 0` และ `base_yield_unit` non-empty ตาม `REC_AUTH_001` และ `REC_VAL_001`–`REC_VAL_005` |
| `DRAFT` | save (แก้ header / บรรทัด / ขั้นตอน / variant) | `DRAFT` | Chef (เจ้าของ) | การ validate ที่เวลา save ใน [02-business-rules.md](./02-business-rules.md) Section 2 ผ่าน (warn-only สำหรับบางตัว); เอกสารยังคงแก้ได้ Rollup cost คำนวณใหม่ตาม `REC_CALC_001`–`REC_CALC_010` บนแต่ละ save (`REC_POST_002`) |
| `DRAFT` | แก้ cost-only | `DRAFT` | Cost Controller | ตาม `REC_AUTH_006` การแก้ต่อ `target_food_cost_percentage`, `selling_price`, `labor_cost_percentage`, `overhead_percentage` คำนวณ pricing rollup ใหม่และเขียนแถว `tb_recipe_pricing_history` (`REC_POST_010`) |
| `DRAFT` | publish | `PUBLISHED` | Chef | ตาม `REC_AUTH_003` กฎที่เวลา publish ทั้งหมดผ่าน (`REC_VAL_015`–`REC_VAL_018`): วัตถุดิบอย่างน้อยหนึ่ง prep step อย่างน้อยหนึ่ง rollup cost valid `selling_price > cost_per_portion` ถ้าตั้ง นโยบาย tenant อาจต้องการ co-approval ของ Cost Controller เมื่อ `actual_food_cost_percentage > target + tolerance` (`REC_AUTH_007`) ตั้ง `published_at = now()` เขียน `tb_recipe_version` ด้วย `version_number = 1` เขียนแถว `tb_recipe_pricing_history` ที่ snapshot การ publish (`REC_POST_003`) |
| `DRAFT` | soft-delete | `(deleted)` | Chef (เจ้าของ) + permission delete | ตาม `REC_AUTH_014` ตั้ง `deleted_at = now()` แถวยังคง; unique index `(code, name, deleted_at)` อนุญาตให้ re-use code+name เดียวกัน |
| `PUBLISHED` | แก้วัตถุดิบ / ขั้นตอน (in-place ด้วย versioning) | `PUBLISHED` | Chef | ตาม `REC_AUTH_002` (พร้อมนโยบาย tenant `edit_published_with_versioning = true`) การแก้ใช้; rollup cost คำนวณใหม่; แถว `tb_recipe_version` ใหม่ถูกเขียน; ถ้า cost / ราคาเปลี่ยน แถว `tb_recipe_pricing_history` ถูกเขียน (`REC_POST_004`) sub-recipe cost cascade (`REC_POST_006`) ยิงถ้าสูตรนี้ใช้เป็น sub-recipe ที่อื่น |
| `PUBLISHED` | แก้วัตถุดิบ / ขั้นตอน (un-publish round-trip) | `DRAFT` | Chef | ตาม `REC_AUTH_005` (นโยบาย tenant: ต้อง un-publish สำหรับการแก้) ย้ายเป็น `DRAFT` สำหรับการแก้; re-publish ตาม `REC_POST_003` เขียนแถว `tb_recipe_version` ใหม่ Menu item ที่ link flag สำหรับ review ระหว่างหน้าต่าง un-publish (สูตรไม่มีสิทธิ์ขับเคลื่อน theoretical consumption ขณะใน `DRAFT`) |
| `PUBLISHED` | แก้ cost-only | `PUBLISHED` | Cost Controller | ตาม `REC_AUTH_006` และ `REC_POST_010` คำนวณ `suggested_price`, `actual_food_cost_percentage`, `gross_margin`, `gross_margin_percentage` ใหม่ เขียนแถว `tb_recipe_pricing_history` สูตรยังคง `PUBLISHED`; ไม่มี snapshot `tb_recipe_version` เต็ม (pricing ติดตามแยก) |
| `PUBLISHED` | archive | `ARCHIVED` | Chef | ตาม `REC_AUTH_004` และ `REC_POST_007` ตั้ง `status = ARCHIVED`, `archived_at = now()` เขียนแถว `tb_recipe_version` สุดท้ายด้วย `change_summary = "archived"` สูตรไม่มีสิทธิ์สำหรับ linkage menu-item หรือ theoretical consumption บนการขายภายหลัง; linkage menu-item ที่มีอยู่ควรถูกตัด (นโยบาย application) |
| `PUBLISHED` | un-publish | `DRAFT` | Chef | ตาม `REC_AUTH_005` และ `REC_POST_008` เส้นทางทางเลือกกลับเป็น `DRAFT` สำหรับการแก้ไขเมื่อการแก้ in-place ไม่อนุญาตโดยนโยบาย tenant |
| `ARCHIVED` | (ไม่มีการเปลี่ยนสถานะเพิ่มเติมปกติ) | `ARCHIVED` | — | terminal ในการดำเนินการปกติ สูตรที่ archive ยังอ่านได้สำหรับ audit; event theoretical-consumption ประวัติใน inventory ledger ถูกรักษา เพื่อนำสูตรที่ archive กลับมาใช้ ให้ clone เป็น `DRAFT` ใหม่และ re-publish |
| `ARCHIVED` | soft-delete (สุขภาพข้อมูลหลังช่วงเวลาการเก็บข้อมูล) | `(deleted)` | Sysadmin (Audit / Config) | ตาม `REC_AUTH_014` หลังช่วงเวลาการเก็บข้อมูล (ตั้งค่าโดย tenant) Sysadmin อาจ soft-delete สูตรที่ archive สำหรับสุขภาพข้อมูล; แถวยังคงสำหรับ audit |

## 3. สารบัญ Persona

แต่ละ persona ด้านล่างมีไฟล์ drill-down เฉพาะอธิบาย entry point, primary flow, decision branch และ exit point Slug match การ group persona ห้าตัว; การคลิกลิงก์เปิดมุมมองต่อ persona การ group รวบ 8 persona ดิบของ carmen/docs เป็น role เชิงปฏิบัติการด้านล่าง

- [Chef](./03-user-flow-chef.md) — Chef / Kitchen Manager (+ subset Kitchen Staff) สร้างสูตรใหม่และปรับปรุงสูตรเดิม — นิยามวัตถุดิบ ปริมาณ wastage วิธี yield อุปกรณ์ เวลาเตรียม / ปรุง ดูแล sub-recipe และทำให้สอดคล้องกันทั่ว outlet อนุมัติการ publish สูตรและการปรับปรุง ตั้งมาตรฐานการจัดจาน / portion / คุณภาพ subset Kitchen Staff อ่านสูตรที่ publish ระหว่างบริการเพื่อ execute (ไม่มี permission แก้)
- [Cost Controller](./03-user-flow-cost-controller.md) — Cost Controller (+ Cost Control Department) review ต้นทุนสูตร % food-cost เป้าหมาย ราคาขายที่แนะนำ gross margin ติดตาม cost drift เมื่อราคาวัตถุดิบเคลื่อน flag margin ที่นอก tolerance เซ็นอนุมัติการเปลี่ยน cost ที่กระทบราคาเมนู รันรายงาน variance ทฤษฎี-vs-จริง Cost Control Department เป็นเจ้าของกระบวนการ costing ที่ระดับ portfolio ตั้งเป้าหมาย food-cost ระดับหมวดหมู่ ขับเคลื่อนการอนุมัติ versioning เมื่อราคาวัตถุดิบเลื่อนอย่างมีนัยสำคัญ
- [Outlet Manager](./03-user-flow-outlet-manager.md) — Outlet Manager สั่งวัตถุดิบจากคลังกลางตาม demand สูตร (มักผ่าน SR อัตโนมัติที่ขนาดด้วยยอดขายคาดการณ์ × สูตร) ติดตาม variance food-cost ของ outlet กับงบประมาณ review สูตรที่ใช้ใน outlet ส่ง feedback ปัญหาการควบคุม portion / ความถูกต้องให้ chef
- [Procurement / F&B Ops](./03-user-flow-procurement-fb-ops.md) — Procurement Department (+ F&B Operations Manager) Procurement ใช้ recipe explosion × ยอดขายคาดการณ์เพื่อขนาด PO และตรวจสอบการมีอยู่ของวัตถุดิบ; รับคำขอทดแทนเมื่อหาวัตถุดิบไม่ได้ F&B Ops เป็นเจ้าของ recipe library เชิงกลยุทธ์ — อนุมัติ menu item ใหม่ + recipe linkage เซ็นอนุมัติ menu engineering กับข้อมูล margin และ variance
- [Audit / Config](./03-user-flow-audit-config.md) — System Administrator (+ Auditor implicit) Sysadmin จัดการ config ของโมดูล recipe (หมวดหมู่ ประเภทอาหาร การตั้งค่า cost default RBAC สำหรับ creation / editing / approval integration กับ inventory / POS / procurement) Auditor (implicit) คือ read-only สำหรับ compliance review — snapshot `tb_recipe_version` timeline `tb_recipe_pricing_history` คอลัมน์ audit

## 4. Handoff ข้าม Persona

ตารางด้านล่างจับช่วงเวลาที่ ใน operating model เป้าหมาย ความรับผิดชอบสำหรับสูตร (หรือการตัดสินใจที่เกี่ยวกับสูตร) ย้ายจาก persona หนึ่งไปยังอีกตัว **วันนี้ไม่มี handoff ใดในตารางนี้ที่ระบบเป็นตัวกลาง** — ไม่มี flag co-approval, alert cost drift, คำขอทดแทนวัตถุดิบ, SR ที่สร้างอัตโนมัติ หรือการ post theoretical-consumption ในโค้ด; ถ้าเกิดขึ้นจริงก็เกิดนอก Carmen แต่ละ handoff ถูก anchor กับสถานะของสูตรที่จุดการถ่ายโอนหรือกับ event ที่ trigger handoff

| จาก persona | Trigger | ไป persona | สถานะของสูตรที่ handoff |
| ------------ | ------- | ---------- | ----------------------- |
| Chef | Submit สูตรใหม่สำหรับการ publish (นโยบาย tenant margin off-target trigger) | Cost Controller | `DRAFT` (publish gate บน co-approval; สูตรยังคง `DRAFT` จนกว่า co-approval บันทึก) |
| Cost Controller | Co-approve publish หรือ ยกความกังวลด้าน cost | Chef | `DRAFT` (ถ้าอนุมัติ chef publish ตาม `REC_POST_003`; ถ้ายกความกังวล chef แก้หรือลบ/swap วัตถุดิบ) |
| Chef | Publish สูตร | F&B Ops (สำหรับการอนุมัติ menu-item linkage) | `PUBLISHED` (สูตร link กับ menu item ได้แล้ว; F&B Ops review ข้อเสนอ linkage ตาม `REC_AUTH_011`) |
| Cost Controller | ตรวจจับ cost drift บนสูตร `PUBLISHED` (price spike ของวัตถุดิบ การ cascade sub-recipe) | Chef + F&B Ops | `PUBLISHED` (พร้อม `actual_food_cost_percentage > target + tolerance`; chef แก้วัตถุดิบหรือ F&B Ops ปรับราคา / เมนู) |
| Outlet Manager | รายงานปัญหาการควบคุม portion / ความถูกต้องสูตรจากบริการ | Chef | `PUBLISHED` (สูตรยัง publish; chef สอบสวน อาจเขียนการแก้แก้ไขตาม `REC_POST_004`) |
| Procurement | ไม่สามารถหาวัตถุดิบ (vendor stock-out ปลดประจำการ) | Chef | `PUBLISHED` (chef เสนอวัตถุดิบทดแทน; แก้ตาม `REC_POST_004` หรือ `REC_POST_005`) |
| F&B Ops | ตัดสินใจปลดประจำการ menu item | Chef | `PUBLISHED → ARCHIVED` (chef archive สูตรตาม `REC_POST_007`; linkage menu ถูกตัด) |
| Sysadmin | เปลี่ยน default cost setting ของหมวดหมู่หรือ RBAC mapping | Persona ทั้งหมด (prospective) | สถานะใดก็ได้ (สูตรใหม่ในหมวดหมู่สืบทอด; สูตรเดิมไม่เปลี่ยนเว้นแต่ใช้ใหม่ชัดเจน) |
| Auditor | Sample สูตรที่ commit สำหรับ compliance review | (ไม่มี handoff — read-only) | สถานะใดก็ได้ (audit อ่านประวัติ `tb_recipe_version` คอลัมน์ audit pricing history) |
| โมดูล Recipe | สร้าง SR `draft` อัตโนมัติสำหรับ event การผลิตที่วางแผน | Outlet Manager (role Requester ใน [store-requisition](/th/inventory/store-requisition)) | `PUBLISHED` (สูตรคือแหล่ง; SR ถูกสร้างในโมดูล SR ด้วย `info.recipe_id` back-reference) |
| โมดูล Recipe | Post OUT movement เชิงทฤษฎีบนการขายเมนู | โมดูล Inventory (ปลายน้ำ อัตโนมัติ) | `PUBLISHED` (สูตรคือแหล่งสูตร; inventory layer เขียน movement) |

## 5. แหล่งอ้างอิง

- `../carmen/docs/recipe-module/RECIPE-User-Flow-Diagram.md` — แหล่ง user-flow ของ carmen/docs: diagram วงจรชีวิต flow creation flow ค้นหา / filter flow มุมมองรายละเอียด การดำเนินการเป็น batch flow มือถือ flow integration หมายเหตุ diagram ของ carmen/docs แสดงวงจรชีวิตสองสถานะใน panel บางตัวและสามสถานะ (`Draft → Published → Archive`) ในอื่น — หน้านี้ตาม Prisma enum สามสถานะ canonical
- `../carmen/docs/recipe-module/RECIPE-Page-Flow.md` — แหล่ง page-flow ของ carmen/docs: recipe list / detail / create flow, การ navigate tab, user flow มือถือ, จุด integration (inventory, cost control), flow error-handling Map ไปยัง journey ของ chef / cost controller / outlet-manager
- `../carmen/docs/recipe-module/RECIPE-Overview.md` — วัตถุประสงค์ของโมดูล ขอบเขต กลุ่มผู้ใช้ จุด integration; section user-roles แจ้งการ group persona ด้านบน
- `../carmen/docs/recipe-module/RECIPE-PRD.md` — user story ต่อ role (Kitchen Management, Kitchen Staff, Cost Control, General Users); สารบัญ Section 3 map ไปยัง story เหล่านี้
- `../carmen/docs/recipe/recipe-management.md` — การอ้างอิงระดับ layout สำหรับหน้า create / edit, costing sheet, เครื่องคิดเลข scaling, หน้าการเตรียม, gallery สื่อ และการจัดการหมวดหมู่; แจ้ง flow ของ chef และ cost controller
- Sibling: [01-data-model.md](./01-data-model.md) — canonical `enum_recipe_status` และวงจรชีวิตสามสถานะอ้างทั่ว Section 2
- Sibling: [02-business-rules.md](./02-business-rules.md) Section 5 — ผลกระทบ posting และ gate การกำหนดสิทธิ์ที่อ้างโดยแต่ละแถวของ Section 2
- โมดูลที่เกี่ยวข้อง: [product](/th/inventory/product) (วัตถุดิบสูตรอ้างอิงสินค้าที่ `is_used_in_recipe = true` — ระดับ schema), [inventory](/th/inventory/inventory), [costing](/th/inventory/costing), [store-requisition](/th/inventory/store-requisition) — integration theoretical-OUT, costing จาก valuation และ recipe→SR ที่ระบุในดีไซน์ยังไม่มีโค้ดที่ implement (ตรวจสอบกับซอร์ส 2026-07-15)
- Frontend implementation: `../carmen-inventory-frontend-react/routes/operation-plan/recipe/` — `recipe-component.tsx` (list), `recipe-form.tsx` + section component (detail/new), `recipe-toolbar.tsx` (dropdown สถานะ), `use-recipe-cost-calc.ts` (เครื่องคำนวณ pricing ฝั่ง client)
