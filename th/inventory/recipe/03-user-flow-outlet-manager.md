---
title: สูตรอาหาร (Recipe) — User Flow — Outlet Manager
description: flow ของ Outlet Manager ในโมดูลสูตร — บริโภคสูตรสำหรับการวางแผน demand ติดตาม variance food-cost ของ outlet ส่ง feedback ปัญหาความถูกต้อง / การควบคุม portion
published: true
date: 2026-05-19T23:55:00.000Z
tags: recipe, user-flow, outlet-manager, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T16:00:00.000Z
---

# สูตรอาหาร (Recipe) — User Flow — Outlet Manager

> **At a Glance**
> **Persona:** Outlet Manager &nbsp;·&nbsp; **โมดูล:** [recipe](/th/inventory/recipe) &nbsp;·&nbsp; **ขั้นตอน workflow:** off-path — บริโภคสูตร PUBLISHED สำหรับการวางแผน demand และการติดตาม variance &nbsp;·&nbsp; **สิทธิ์สำคัญ:** อ่านสูตร; author / submit SR ปลายน้ำ; ยก feedback ไปยัง Chef
> **persona นี้ทำอะไร:** อ่านสูตรเพื่อวางแผนการผลิตและยก SR; ติดตาม variance food-cost ของ outlet และส่ง feedback ปัญหาความถูกต้องไปยัง Chef

## 1. บทบาทในโมดูลนี้

persona **Outlet Manager** คือผู้จัดการของ outlet ที่บริโภค — ครัว บาร์ ห้อง banquet ร้านอาหาร — ที่ใช้สูตรสำหรับการผลิตประจำวันและดึงวัตถุดิบจากคลังกลางเพื่อ meet demand สูตร Outlet Manager เป็น **read-only บน recipe library** (`recipe:read` ตาม `REC_AUTH_009`); พวกเขาไม่สร้างหรือแก้สูตร การ engage ของพวกเขากับโมดูล recipe ไหลในสามทิศทาง: **ด้าน demand** (ใช้ recipe explosion × ยอดขายคาดการณ์เพื่อวางแผนการดึงวัตถุดิบ; ยก SR เทียบกับคลังกลาง มักสร้างอัตโนมัติจาก demand สูตรตาม `REC_XMOD_007`); **ด้าน variance** (ติดตาม variance food-cost ของ outlet vs งบประมาณ ซึ่งขับเคลื่อนบางส่วนโดยความถูกต้องของสูตร — สูตรที่ wastage understate yield overstate หรือ cost เก่าสร้าง variance); และ **ด้าน feedback** (รายงานปัญหาการควบคุม portion ปัญหาความถูกต้องของวัตถุดิบ ขั้นตอนเตรียมที่ขาดหรือผิดกลับไปยัง Chef เป็น input สำหรับการ revise สูตรตาม flow การ revise `REC_POST_004` ของ persona Chef) Outlet Manager เป็น **author หลักของเอกสาร [store-requisition](/th/inventory/store-requisition)** (สูตรขับเคลื่อน SR ผ่าน auto-create หรือผ่านการ entry ด้วยมือต่อ demand สูตร); Outlet Manager เป็น **ปลายทางของของที่ออก** และ **เจ้าของ KPI variance food-cost ระดับ outlet** จากมุมมองของโมดูล recipe Outlet Manager เป็นผู้บริโภคปลายน้ำ ไม่ใช่ producer; จากมุมมองปฏิบัติการพวกเขาเป็นสัญญาณ demand ที่ขับเคลื่อนการใช้สูตรที่ scale

## 2. Entry Point และ Primary Flow

**Entry point:** สี่เส้นทางสู่งาน Outlet Manager ที่แตะโมดูล recipe

- **Recipe library → มุมมอง outlet-scope** — มุมมอง list filter เป็นสูตรที่ใช้ใน outlet (กล่าวคือ สูตรที่ link กับ menu item ที่ขายที่ outlet หรือสูตรสำหรับ event ที่ book ที่ outlet); read-only
- **การวางแผนการผลิต → recipe explosion** — การผลิตที่วางแผนของ outlet สำหรับวัน / สัปดาห์ (จำนวน cover, event banquet) คูณผ่านบรรทัดวัตถุดิบของสูตรตาม `REC_CALC_014` เพื่อผลิต list การดึงวัตถุดิบ; list seed draft SR ตาม `REC_XMOD_007`
- **Dashboard variance ของ outlet** — variance food-cost ระดับ outlet (ทฤษฎี-vs-จริง) สำหรับ period พร้อม drill-down เข้าสูตรและวัตถุดิบที่มีส่วนร่วมใน variance
- **ช่อง feedback → submit issue ของสูตร** — ช่อง in-app (หรือ workflow ภายนอก — ขึ้นกับ tenant) ที่ Outlet Manager (หรือ Kitchen Staff รายงานขึ้น) flag issue การควบคุม portion / ความถูกต้อง / ขั้นตอนขาดบนสูตร `PUBLISHED`

**Primary flow (8 ขั้นตอน — รันรายวัน / ต่อกะ):**

1. **Review การผลิตที่วางแผนของวัน** เปิดมุมมองการวางแผนการผลิตสำหรับ outlet: จำนวน cover คาดการณ์ต่อ menu item event banquet ที่ book ปริมาณวาระพิเศษ แต่ละ menu item link กับสูตร `PUBLISHED` หนึ่งหรือหลายตัว (linkage อยู่นอก schema สูตรตาม `REC_XMOD_008`)
2. **Explode สูตรเป็น demand วัตถุดิบ** สำหรับแต่ละ menu item × ปริมาณคาดการณ์ ระบบ explode สูตรที่ link ตาม `REC_CALC_014`: ปริมาณวัตถุดิบ scale ด้วยปริมาณที่ขาย ใช้ % wastage แปลง UoM เป็นหน่วยสต๊อก วัตถุดิบ sub-recipe ซ้อนไปยังสินค้าใบไม้ตาม `REC_XMOD_004` demand วัตถุดิบที่รวมแสดงเป็น list การดึง (หนึ่งแถวต่อสินค้า ปริมาณรวมในหน่วยสต๊อก)
3. **กระทบยอดกับ on-hand ที่ outlet** สำหรับแต่ละสินค้าใน list การดึง เปรียบเทียบกับ on-hand ปัจจุบันของ outlet (อ่านจาก `tb_inventory_status` ต่อ location ของ outlet) Net demand = demand คาดการณ์ − on-hand ปัจจุบัน − ที่ reserve โดย SR เปิดอื่น
4. **สร้าง / review draft SR** ระบบอย่างใดอย่างหนึ่งสร้าง SR `draft` อัตโนมัติเทียบกับคลังกลางพร้อม net demand (ตาม `REC_XMOD_007`; SR ถือ `info.recipe_id` หรือ `info.production_event_id` เป็น back-reference) หรือ Outlet Manager สร้าง SR ด้วยมือโดยใช้ list การดึงเป็น reference Outlet Manager review ปริมาณ ปรับถ้าต้อง และ submit SR SR ตาม flow store-requisition ปกติ (`SR_POST_001` ขึ้นไปใน [store-requisition/02-business-rules](/th/inventory/store-requisition/02-business-rules)) — อนุมัติ → fulfilment → รับที่ outlet
5. **การ execute บริการ** Kitchen Staff ที่ outlet อ่านสูตร `PUBLISHED` ระหว่างบริการเพื่อเตรียมจาน; การแสดงมือถือ / station แสดง header สูตร list วัตถุดิบ ขั้นตอนวิธี คำแนะนำการจัดจาน Kitchen Staff เป็น read-only บนสูตร (`REC_AUTH_009`); issue ที่ยกระหว่างบริการจับในช่อง feedback
6. **ติดตาม variance food-cost ระหว่าง period** Dashboard variance ของ outlet แสดงการใช้เชิงทฤษฎี (จากการขายเมนูที่ recipe-driven) vs การใช้จริง (จากการออก SR การ post physical-count การปรับ) Variance บวกที่ยังคงอยู่ (จริง > ทฤษฎี) หมายถึง outlet บริโภคมากกว่าที่สูตรบอก — over-portioning การโจรกรรม การเสีย sub-recipe ที่ไม่ถูกต้อง หรือ cost สูตรเก่า Variance ลบที่ยังคงอยู่ (ทฤษฎี > จริง) หมายถึงสูตร overstate การใช้ — under-portioning สูตรผิด หรือ kitchen staff ใช้น้อยกว่าที่สูตรระบุ
7. **สอบสวน variance และ feedback** Drill เข้าผู้มีส่วนร่วมที่ใหญ่ที่สุดใน variance สำหรับแต่ละ: variance attribute ไปที่ (a) วินัยการควบคุม portion (Outlet Manager เป็นเจ้าของ action แก้ไข — การอบรม Kitchen Staff การ audit การจัดจาน), (b) ความไม่ถูกต้องของสูตร (escalate ไปยัง Chef สำหรับการ revise ตาม `REC_POST_004` — % wastage ต่ำเกินไป yield สูงเกินไป wastage ขาดบนขั้นตอน) หรือ (c) shrinkage / spoilage (escalate ไปยัง Inventory Controller สำหรับการสอบสวนผ่าน `[inventory-adjustment](/th/inventory/inventory-adjustment)`)?
8. **Submit รายการ recipe-feedback ไปยัง Chef** สำหรับ issue ที่ recipe-attributable log feedback ในช่อง feedback (in-app comment ticket หรือ meeting ปฏิบัติการ) Chef ได้รับ feedback และตัดสินใจว่าจะ revise สูตรตาม `REC_POST_004` (in-place ด้วย versioning) หรือ `REC_POST_005` (un-publish round-trip) Outlet Manager ติดตามรอบ variance ถัดไปเพื่อยืนยันว่าการ revise ปิดช่องว่าง

## 3. Decision Branch

- **SR ที่สร้างอัตโนมัติ vs SR ด้วยมือ**: config ของ tenant ตัดสินใจว่าการ explode demand สูตรสร้าง SR `draft` อัตโนมัติ (ตาม `REC_XMOD_007`) หรือแสดง list การดึงให้ Outlet Manager ใช้เป็น reference เมื่อสร้าง SR ด้วยมือ Auto-create เร็วกว่าและถูกต้องกว่า (ไม่มีการ transcribe); ด้วยมือที่ต้องการเมื่อ outlet ปกติ override demand (เช่น สต๊อก buffer ฉุกเฉิน par-level top-up) Outlet Manager อาจแก้ draft ที่ auto-create เสมอก่อน submit
- **Variance attribute ไปที่การควบคุม portion vs สูตร**: เมื่อสอบสวน variance ของ outlet Outlet Manager ประเมินว่าช่องว่างเป็น issue วินัยครัว (Kitchen Staff จัดจานต่างจากสูตร — เป็นเจ้าของ action แก้ไขผ่านการอบรมและ audit) หรือ issue ความถูกต้องของสูตร (wastage / yield ของสูตรผิด — escalate ไปยัง Chef) ความแตกต่างมักมองเห็นใน drill-down per-ingredient: วัตถุดิบเดียวที่มี over-consumption เรื้อรังบ่งบอกการควบคุม portion; over-consumption กว้างบนวัตถุดิบของจานบ่งบอกสูตร understate การใช้จริง
- **การปรับความถูกต้องของ forecast**: เมื่อ explosion ของ demand ผลิตปริมาณวัตถุดิบที่ไม่ match รูปแบบการใช้จริงของ outlet issue อาจอยู่ใน **forecast** (จำนวน cover สูงเกินไปหรือต่ำเกินไป) แทนในสูตร Outlet Manager ปรับ forecast ในรอบการวางแผนถัดไป; สูตรคือแหล่งสูตรและไม่ปรับ
- **ความถูกต้องของ sub-recipe**: เมื่อ sub-recipe ใช้ในจานหลายตัว ความถูกต้องของ cost / yield มีผลกระทบใหญ่ การสอบสวน variance อาจแสดง sub-recipe ที่ cost เก่าหรือ yield ผิด; Outlet Manager escalate ไปยัง Chef ที่รับผิดชอบ sub-recipe
- **Variant สูตรเฉพาะ outlet**: เมื่อสูตรใช้ที่หลาย outlet ด้วยอุปกรณ์ / scale ต่าง ความถูกต้องอาจต่างตาม outlet Outlet Manager flag issue เฉพาะ outlet; Chef ตัดสินใจว่าจะดูแลสูตรเดียว (และยอมรับ variance outlet บ้าง) หรือสร้าง variant per-outlet (แถว yield-variant หรือสูตรแยก)
- **Banquet vs demand a-la-carte**: สำหรับ outlet ที่จัดการ event banquet การ explode demand มีความต้องการความถูกต้องสูงกว่า (จำนวน cover รับประกันใหญ่; demand มองเห็นล่วงหน้าสัปดาห์) สำหรับ a-la-carte demand เป็น probabilistic และ SR ขนาดเป็น par + buffer มากกว่าต่อ event Outlet Manager ทำการเลือก methodology per outlet operation

## 4. Exit Point / Handoff

การมีส่วนร่วมที่เกี่ยวข้องกับสูตรของ Outlet Manager บนรอบปฏิบัติการที่กำหนดจบที่หนึ่งในหลาย boundary:

- **SR submit ไปยังคลังกลาง** — handoff ไปยัง **Approver** และ **Fulfiller** ใน flow [store-requisition](/th/inventory/store-requisition) (วงจรชีวิตของ SR ดำเนินต่อโดยอิสระ); Outlet Manager ติดตามแต่ไม่ advance สถานะของ SR
- **Recipe-feedback ยกไปยัง Chef** — handoff ไปยัง **Chef** สำหรับการประเมินและ revise ตาม `REC_POST_004`; Outlet Manager ติดตามรอบ variance ถัดไปเพื่อยืนยันการปิด
- **Variance attribute ไปที่ shrinkage** — handoff ไปยัง **Audit / Config (Inventory Controller)** สำหรับการสอบสวนผ่าน `[inventory-adjustment](/th/inventory/inventory-adjustment)`; Outlet Manager ให้บริบทปฏิบัติการแต่การ resolve อยู่ที่ inventory layer
- **Action แก้ไขการควบคุม portion เสร็จ** — สูตรไม่เปลี่ยน; Kitchen Staff อบรมหรือ audit; Outlet Manager เป็นเจ้าของ action แก้ไขและการติดตาม
- **Signoff ที่ปิด period** — handoff ไปยัง **Audit / Config (Finance + Cost Control)** สำหรับการกระทบยอด food-cost ของ outlet กับ GL; Outlet Manager ยืนยันภาพปฏิบัติการสำหรับ period

Outlet Manager เป็น **ผู้บริโภคปลายน้ำต่อเนื่อง** ของ recipe library — ทุกกะ ทุกบริการ ทุก event banquet ขับเคลื่อนการใช้สูตร Outlet Manager หายากที่จะ "exit" flow ที่เกี่ยวข้องกับสูตร; engagement คือ daily-operational

## 5. แหล่งอ้างอิง

- Parent overview: [03-user-flow.md](./03-user-flow.md) — วงจรชีวิต canonical; Section 4 แถว "Outlet Manager → Chef (feedback)", "Recipe module → Outlet Manager (auto-create SR)", "Recipe module → Inventory module (theoretical OUT)" กรอบการโต้ตอบของ persona นี้
- `../carmen/docs/recipe-module/RECIPE-Overview.md` § Kitchen Staff (และตาราง user-roles ใน index ของ wiki สำหรับ Outlet Manager) — แหล่ง carmen/docs สำหรับ role ปฏิบัติการ
- `../carmen/docs/recipe-module/RECIPE-PRD.md` § Kitchen Staff user story — user story ของ carmen/docs ("As a kitchen staff member, I want to view detailed recipe instructions...", "...see ingredient quantities and preparation steps clearly...")
- `../carmen/docs/recipe-module/mobile-app.md` — reference mobile-app สำหรับการบริโภคพื้นครัวของสูตร `PUBLISHED`
- `../carmen/docs/recipe/recipe-view-page.md` — page spec รายละเอียดอ่านอย่างเดียว — surface หลักของ Outlet Manager และ Kitchen Staff
- Sibling: [03-user-flow-chef.md](./03-user-flow-chef.md) — ผู้รับหลักของ feedback Outlet Manager; การ revise ไหลจาก issue ที่ Outlet-Manager ยกผ่านการเป็นเจ้าของของ Chef
- Sibling: [03-user-flow-cost-controller.md](./03-user-flow-cost-controller.md) — collaborator การสอบสวน variance; Cost Controller มอง variance ระดับ portfolio Outlet Manager เป็นเจ้าของ variance ระดับ outlet
- Sibling: [03-user-flow-procurement-fb-ops.md](./03-user-flow-procurement-fb-ops.md) — Procurement ใช้ demand ระดับ outlet (explosion เดียวกัน) เพื่อขนาด PO; feed ด้าน demand แชร์
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Inventory Controller สอบสวน shrinkage ที่ outlet; การ scope RBAC ของ Sysadmin bound มุมมอง recipe library ของ Outlet Manager
- Sibling: [01-data-model.md](./01-data-model.md) — `tb_recipe.status` (เฉพาะสูตร `PUBLISHED` มีสิทธิ์สำหรับการบริโภคของ outlet) ฟิลด์ `tb_recipe_ingredient` ที่ใช้ใน explosion demand (`qty`, `inventory_unit_id`, `conversion_factor`, `wastage_percentage`)
- Sibling: [02-business-rules.md](./02-business-rules.md) — `REC_CALC_014` (สูตร theoretical-consumption — explosion demand), `REC_AUTH_009` (scope read-only ของ Outlet Manager), `REC_XMOD_003` (OUT เชิงทฤษฎี fan-out trigger โดยการขายเมนู), `REC_XMOD_007` (auto-create SR จาก demand สูตร)
- ที่เกี่ยวข้อง: [store-requisition](/th/inventory/store-requisition) — เอกสารปลายน้ำหลักที่ Outlet Manager author; demand สูตร seed SR
- ที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) — การกระทบยอด on-hand ของ outlet กับการใช้เชิงทฤษฎีที่ recipe-driven คือการคำนวณ food-cost-variance
- ที่เกี่ยวข้อง: [inventory-adjustment](/th/inventory/inventory-adjustment) — movement แก้ไขสำหรับ shrinkage / spoilage ที่ flag โดยการสอบสวน variance
