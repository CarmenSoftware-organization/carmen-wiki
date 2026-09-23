---
title: ใบขอซื้อ (Purchase Request)
description: เอกสารคำขอภายในเพื่อจัดซื้อสินค้า — สัญญาณความต้องการต้นน้ำที่จะถูกแปลงเป็นใบสั่งซื้อหลังได้รับอนุมัติ
published: true
date: '2026-09-23T01:30:00.000Z'
tags: purchase-request, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# ใบขอซื้อ (Purchase Request)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** workflow ความต้องการภายในแบบหลายขั้นตอน (`Draft` → `In Progress` (สายอนุมัติหลายขั้นตอน; Send-Back คงอยู่ที่ `In Progress`) → `Approved` → `Completed`, หรือ `Voided` ผ่านการ Reject ของผู้อนุมัติ; draft ถูก soft-delete) ส่งความต้องการที่จัดสรรผู้ขายแล้วต่อให้ฝ่ายจัดซื้อ &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Requestor, ผู้อนุมัติแต่ละ stage (HOD / FC / GM — ตามที่ workflow กำหนด), Purchaser, Procurement Manager, Auditor &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_purchase_request`, `tb_purchase_request_detail`, approval history, pricelist allocation, [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) &nbsp;·&nbsp; **หน้าย่อย:** 15

![Purchase Request module screen](/screenshots/purchase-request/index.png)

![Purchase Request module detail screen](/screenshots/purchase-request/detail.png)

## 1. ภาพรวม

**ใบขอซื้อ (Purchase Request — PR)** คือเอกสารคำขอภายในที่หน่วยงานปฏิบัติการสร้างขึ้นเพื่อขออนุมัติการจัดซื้อสินค้าหรือบริการ ก่อนที่จะมีการผูกพันใด ๆ กับผู้ขายภายนอก แต่ละ PR ประกอบด้วยส่วนหัว — `pr_no` ที่ server สร้างให้, `pr_date`, `workflow_id` ที่จะใช้ route, ผู้ขอและแผนก (snapshot เป็น `*_name`), คำอธิบายและ note — และรายการสินค้าหนึ่งรายการขึ้นไปที่บรรจุสินค้า คลังจัดเก็บ จุดส่งของและวันส่งของ ชุดปริมาณ requested / approved / FOC ที่แต่ละชุดมีหน่วยของตัวเอง snapshot ของผู้ขายและ pricelist ราคาต่อหน่วย ส่วนลด tax profile และยอดรวมต่อบรรทัดที่คำนวณแล้วทั้งในสกุลเงินธุรกรรมและสกุลเงินฐาน ส่วนหัวรวบยอดจากรายการเป็น `base_net_amount` / `base_total_amount` (`tb_purchase_request`, Prisma schema model `tb_purchase_request`) **ไม่มีคอลัมน์ PR-type, job/cost-code หรือวันส่งของระดับ header** — สิ่งเหล่านั้นปรากฏเฉพาะใน concept docs ดู [01-data-model](/th/inventory/purchase-request/01-data-model) §5

สถานะเอกสารของ PR (`tb_purchase_request.pr_status`, `enum_purchase_request_doc_status`) ขับเคลื่อนด้วย workflow: `draft` (ผู้ขอแก้ไขได้) → `in_progress` เมื่อ submit (PR คงอยู่ที่ `in_progress` ตลอดที่ถูกส่งผ่านทุก stage ของสายอนุมัติ **รวมถึงหลัง Send-Back** — การ review ย้าย `workflow_current_stage` ถอยหลังแต่ไม่เคยเขียนทับ `pr_status`, `purchase-request.service.ts:2052`) → `approved` เมื่อ stage สุดท้ายผ่าน → `completed` เมื่อทุกบรรทัดถูกแปลงเป็นใบสั่งซื้อครบแล้ว การ **Reject** ระดับเอกสารจากผู้อนุมัติคนใดก็ตามย้าย PR ไปที่ `voided` — code path เดียวที่เขียนค่านั้น (`purchase-request.service.ts:2201`); **ไม่มี endpoint "void" โดยผู้ดูแลระบบแยกต่างหาก** ใน `purchase-requests.controller.ts` (เคยระบุในเอกสารรุ่นก่อน — ยังไม่ยืนยัน) `draft` ไม่ถูก void แต่ถูก **soft-delete** (`DELETE /:bu_code/purchase-requests/:id` เฉพาะ draft โดยเจ้าของหรือ platform super-admin — `purchase-request.service.ts:1648-1720`) Stage คือสิ่งที่ workflow ที่กำหนดนิยามไว้ (`enum_stage_role = create | approve | purchase | issue | view_only`); ชื่อเช่น "Department Head", "Budget Controller" หรือ "Finance" ในหน้าของโมดูลนี้เป็นชื่อ stage ประกอบการอธิบาย ไม่ใช่ role ที่ code รู้จัก การ route ระหว่าง stage ตามเกณฑ์มูลค่ามีจริง (`tb_workflow.data.routing_rules` ดู `PR_AUTH_005`); กลไก delegation-of-authority ไม่มี (`PR_AUTH_006` ยังไม่ยืนยัน)

PR เป็นสัญญาณความต้องการต้นน้ำในห่วงโซ่ procure-to-pay มันบันทึก *อะไร* ที่ต้องการ *เพื่อใคร* *เมื่อไหร่* และ *ราคาประมาณเท่าไหร่* แล้วส่งความต้องการที่ผ่านการอนุมัติ มีต้นทุนกำกับ และถูกจัดสรรผู้ขายแล้วต่อให้ฝ่ายจัดซื้อ **Auto Allocate** (`pr-auto-allocate.ts`) เรียก endpoint price-compare ของ pricelist ต่อบรรทัด; backend คืน pricelist row ที่ active ทุกแถวสำหรับ product / unit / currency / date ที่ `price > 0` เรียงตาม **ผู้ขาย preferred ก่อน แล้วราคาต่ำสุด** (`price-list.service.ts:715` `orderBy: [{ is_preferred: 'desc' }, { price: 'asc' }]`) เก็บ MOQ tier ที่ดีที่สุดที่ `qty` ที่ขอไปถึง และส่งผู้ชนะกลับมาเป็น `selected` พร้อม **ราคาซื้อล่าสุด** ของสินค้า (`last_price`, 2026-09-17) "ประวัติการรับของล่าสุด" ในฐานะเกณฑ์จัดอันดับ — เคยระบุในเอกสารรุ่นก่อน — ไม่มี code path PR ที่อนุมัติแล้วจะถูกแปลงเป็นใบสั่งซื้อเพื่อผูกพันภายนอก **การตรวจสอบงบประมาณและ soft commitment** — ที่ระบุไว้ทั่วเอกสารรุ่นก่อนของโมดูลนี้ — **ไม่มี code path**: การ grep `budget` / `soft_commit` ใน `apps/micro-business/src/procurement/purchase-request`, `apps/backend-gateway/src/application/purchase-requests`, `apps/backend-gateway/src/application/my-pending` และ `routes/procurement/purchase-request` พบเพียงฟิลด์ interface `budget_code?: string` แบบ optional และข้อความ reject ตัวอย่าง "Budget exceeded for this period" ถือว่าทุกประโยคเกี่ยวกับงบประมาณในโมดูลนี้เป็น design intent ที่ยังไม่ยืนยัน

## 2. บริบททางธุรกิจ

ธุรกิจ procurement ในอุตสาหกรรมโรงแรมดำเนินบนกำไรขั้นต้นที่บางเฉียบ และมีการซื้อปริมาณมากต่อใบแต่มูลค่าต่อใบไม่สูงกระจายอยู่ใน cost center จำนวนมาก PR จึงเป็นจุดควบคุมที่ป้องกันการใช้จ่ายที่ควบคุมไม่ได้ก่อนที่จะมีการผูกพันภายนอก โดยการบังคับให้ความตั้งใจซื้อทุกครั้งผ่าน workflow ที่มีเอกสารกำกับและผ่านผู้อนุมัติหลายคน — พร้อมข้อมูลบังคับ คือ ผู้ขอ แผนก workflow วันที่ PR อย่างน้อยหนึ่งบรรทัดที่ซื้อ (`requested_qty > 0`) หรือรับของฟรี (`foc_qty > 0`) และหมายเลขอ้างอิงที่ไม่ซ้ำกัน (`purchase-request.validate.ts`) — PR บังคับใช้นโยบายการใช้จ่ายไว้ที่ต้นน้ำของผู้ขาย *(มุมมองงบประมาณล่วงหน้าที่ขับเคลื่อนด้วย soft commitment เคยระบุในเอกสารรุ่นก่อน — ยังไม่ยืนยัน ไม่มี code path ดู §1)*

นอกจากนี้โมดูลนี้ยังเป็นแกนของการเชื่อมต่อกับทุกอย่างที่อยู่ปลายน้ำ ข้อมูล PR ไหลเข้าสู่โมดูลคลังสินค้า (on-hand, on-order และราคาซื้อล่าสุดที่ผู้ขอเห็นได้ต่อบรรทัด — `pr-inventory-row.tsx`, `pr-last-receiving-info.tsx`) โมดูล vendor-pricelist (การเปรียบเทียบราคา, Auto Allocate, MOQ tier) workflow engine (การจัดเส้นทางอนุมัติที่ตั้งค่าได้, `user_action.execute[]`, การแจ้งเตือน) และโมดูลใบสั่งซื้อ (การแปลง PR ไปเป็น PO พร้อม traceability เต็มรูปแบบผ่าน `tb_purchase_order_detail_tb_purchase_request_detail`) Document management (comments, attachments, activity log) ทำให้ PR ทุกใบมี audit trail ครบถ้วน — ใครสร้าง ใครแก้ ใครอนุมัติหรือปฏิเสธ และเมื่อใด

ความถูกต้องทางการเงินถูกบังคับใช้ที่ชั้นการคำนวณ: ยอดระดับบรรทัดและ header ถูกเก็บที่ทศนิยมห้าตำแหน่ง (`Decimal(20, 5)` / `Decimal(15, 5)`) server คำนวณทุกยอดใหม่จาก input ของตัวเองที่ stage `purchase` (`POST …/verify` โดย `stage_role = purchase`) และส่วนลดหรือภาษีต่อบรรทัดที่เกินมูลค่าบรรทัดจะถูกปฏิเสธ (`PR_ERROR.DISCOUNT_EXCEEDS_LINE_AMOUNT` / `TAX_EXCEEDS_LINE_AMOUNT`, `common/verify/amount.check.ts`, 2026-09-17) ดูสูตรใน [02-business-rules](/th/inventory/purchase-request/02-business-rules) §3

## 3. แนวคิดสำคัญ

- **Approval Stage**: ขั้นตอนในสาย workflow ของ PR ที่ตั้งค่าได้ (`tb_workflow`) พร้อม `stage_role`, ผู้ใช้ที่ถูกมอบหมาย และ routing rule แบบ optional กฎ routing ของ workflow ข้าม stage หรือกระโดดไป stage เมื่อยอด header (หรือแผนก) ข้ามค่าที่ตั้งไว้ (`PR_AUTH_005`) เส้นทางทั้งหมดถูกบันทึกใน `workflow_history` และ activity log *(การ delegate การอนุมัติให้ผู้แทน — ยังไม่ยืนยัน ไม่พบกลไกดังกล่าว ดู `PR_AUTH_006`)*
- **Budget Check / Soft Commitment**: **ยังไม่ยืนยัน — ไม่มี code path** เอกสารรุ่นก่อนอธิบายการตรวจสอบความพร้อมตอน submit และ soft commitment ที่ถอนคืนได้เมื่อ reject ไม่มีอะไรใน backend, frontend หรือ Bruno collection ที่ implement ทั้งสองอย่าง (ดูการ grep ใน §1); artefact ที่เกี่ยวกับงบประมาณมีเพียง string `budget_code` แบบ optional บน interface และข้อความ reject ตัวอย่าง
- **Preferred Vendor / Auto Allocate**: การ lookup price-compare เลือก pricelist row ต่อบรรทัดที่ preferred ก่อนและถูกที่สุดเป็นลำดับสอง ที่ MOQ tier ซึ่งปริมาณที่ขอเข้าเกณฑ์ และเติมผู้ขาย, `pricelist_detail_id`, `pricelist_no`, ราคาต่อหน่วย, tax profile และอัตราแลกเปลี่ยน Purchaser override ได้จาก dialog **Price Comparison**; ถ้า Adjust checkbox ของบรรทัดถูกเลือก ราคาจะไม่ถูกอัปเดตอัตโนมัติเมื่อมีการ re-allocation
- **PR Type**: **ไม่ใช่ฟิลด์** `tb_purchase_request` ไม่มีคอลัมน์ `pr_type` และไม่มี enum; การจำแนก "General Purchase / Market List / Asset" มีอยู่เฉพาะใน `../carmen/docs/` ความแตกต่างของ routing มาจากการเลือก `workflow_id` ที่ต่างกัน
- **Approved Quantity vs. Requested Quantity**: ทุกบรรทัดมีทั้งสองค่า ผู้ขอใส่ `requested_qty`; ผู้อนุมัติที่ stage role `approve` แก้ไข `approved_qty` server ปฏิเสธเฉพาะ `approved_qty` ที่**ติดลบ** และหน่วยอนุมัติที่ไม่ใช่ order unit ของสินค้า (`logic/verify/purchase-request.verify-approve.ts:172-181`); เพดานที่ `requested_qty` — ที่ระบุในเอกสารรุ่นก่อน — ไม่มี code path ค่า approved quantity คือค่าที่จะไหลต่อไปยังใบสั่งซื้อตอนแปลง
- **FOC (Free of Charge)**: ชุดปริมาณระดับบรรทัด (`foc_qty`, `foc_unit_id`, factor) สำหรับสินค้าที่ผู้ขายให้มาในราคา 0 ตั้งแต่ 2026-09 บรรทัดอาจเป็น **FOC-only**: `requested_qty = 0` กับ `foc_qty > 0` submit ได้ ขณะที่บรรทัดที่ทั้งสองค่าเป็นศูนย์ถูกปฏิเสธ ("needs a requested_qty or a foc_qty", `purchase-request.validate.ts:105-131`; gate ฝั่ง FE `findRowsMissingQty` ใน `pr-form-schema.ts`) ปริมาณ FOC ไม่ถูกรวมใน subtotal ของ PR แต่ปรากฏบน PO และ GRN ที่ตามมา
- **Conversion to PO**: ขั้นตอนของฝ่ายจัดซื้อที่นำ PR สถานะ `approved` หนึ่งใบหรือหลายใบมาออกเป็นใบสั่งซื้อ — เลือกทั้ง PR, บรรทัดถูกจัดกลุ่มตาม `(vendor, delivery_date, currency)` และ PR เปลี่ยนเป็น `completed` เมื่อทุกบรรทัดถูก bridge แล้ว (`PR_POST_007`; ดู [purchase-order](/th/inventory/purchase-order))
- **Delete vs. Reject**: PR สถานะ `draft` ถูก **ลบ** (soft delete โดยเจ้าของหรือ super-admin ทีละใบหรือแบบ batch — `DELETE /:bu_code/purchase-requests/batch` รายงาน `not_found` / `not_draft` / `not_owner` ต่อ id) เมื่อ submit แล้ว การยุติทำได้ผ่าน workflow เท่านั้น: ผู้อนุมัติเลือก **Reject** (→ `voided` ต้องระบุเหตุผล) หรือ **Send Back** (cursor ของ stage ถอยหลัง PR คงอยู่ที่ `in_progress`) **Split** ให้ผู้อนุมัติปฏิเสธเฉพาะบรรทัดและอนุมัติส่วนที่เหลือ (`POST …/:id/split`)
- **Price Comparison**: dialog ระดับบรรทัด (`pr-pricelist-dialog.tsx`) ที่แสดง pricelist row ที่ active ทุกแถวของสินค้า — ผู้ขาย, เลขที่ pricelist, หน่วย, ราคา (พร้อมเครื่องหมาย "best"), ช่วงวันที่มีผล — บวกปุ่ม **Assign** ต่อแถว header ของมันแสดงปริมาณที่ขอและที่อนุมัติ และตั้งแต่ 2026-09-22 **ราคาซื้อล่าสุด** ของสินค้า (`last_price.cost_per_unit`) request ส่ง `qty` ไปด้วย จึงแสดงผู้ขายแต่ละรายที่ MOQ tier ซึ่งปริมาณนั้นไปถึง (2026-09-16)
- **Pre-flight verification**: `POST /:bu_code/purchase-requests/verify` (2026-08-19) รันชุดกฎเต็มสำหรับ `verify_state = create | submit | approve` โดยไม่เขียนอะไรและคืนทุกปัญหาในครั้งเดียว (`is_valid`, `errors[]` พร้อม `error_code` / `field`); PR ที่ไม่ผ่านยังตอบ 200 ดู `PR_VAL_017`

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Requestor | พนักงานโรงแรมหรือพนักงานแผนกที่เป็นผู้ตั้ง PR สร้างคำขอ เพิ่มรายการสินค้าพร้อมปริมาณ หน่วย คลัง จุดส่งของและวันส่งของ แนบเอกสารประกอบ และ submit เพื่อขออนุมัติ ติดตามสถานะและตอบสนองเมื่อถูก send back เป็นเจ้าของ (และลบได้) draft ของตนเอง |
| Department Head / ผู้อนุมัติ stage (role `approve`) | ตรวจสอบ PR ที่ stage ซึ่งถูกมอบหมาย ปรับ `approved_qty` ถ้าจำเป็น และอนุมัติ ปฏิเสธ ส่งกลับ หรือ split บรรทัดเฉพาะ "Budget Controller" และ "Finance" ในหน้าของโมดูลนี้คือ stage role `approve` เพิ่มเติมที่ workflow *อาจ* นิยาม — code ไม่มีการตรวจสอบงบประมาณและไม่มีพฤติกรรมเฉพาะ finance |
| Purchaser (role `purchase`) | ที่ stage `purchase` ตั้งหรือตรวจสอบผู้ขาย ราคาต่อหน่วย ส่วนลด และ tax profile ต่อบรรทัด (Auto Allocate / Price Comparison) แล้วตัดสินใจแบบ bulk เหมือน stage อื่น แยกต่างหาก แปลง PR ที่อนุมัติแล้วเป็น PO จากโมดูล Purchase Order |
| Procurement Manager | stage role `approve` ที่ escalate ขึ้นมา ถึงได้ผ่าน threshold routing หรือการตั้งค่า workflow โดยตรง — UI และสิทธิ์เหมือนผู้อนุมัติคนอื่นทุกประการ ไม่มีหน้าจอตั้งค่า vendor-ranking หรือกฎการจัดสรร |
| System Administrator | ตั้งค่าขั้นตอน workflow และเกณฑ์ routing (`/system-admin/workflow` แบบ generic), tax profile, อัตราแลกเปลี่ยน, ผู้ใช้และ role *(action "void" โดยผู้ดูแลระบบและกฎ delegation เคยถูกระบุในเอกสารรุ่นก่อน — ยังไม่ยืนยัน; ไม่มี endpoint void และไม่พบกลไก delegation)* |
| Auditor | สิทธิ์อ่านอย่างเดียวต่อ PR, comment และ `/system-admin/activity-log` แบบ generic ไม่มี audit workspace เฉพาะ |

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [purchase-order](/th/inventory/purchase-order) — PR ที่อนุมัติแล้วจะกลายเป็น PO
- [product](/th/inventory/product) — บรรทัดของ PR อ้างอิงสินค้าจากแคตตาล็อก
- [vendor-pricelist](/th/inventory/vendor-pricelist) — preferred vendor และราคาอ้างอิงมาจาก pricelist
- [inventory](/th/inventory/inventory) — ระดับสต๊อกปัจจุบันมักเป็นเหตุผลของการตั้ง PR
- [templates/purchase-request](/th/inventory/templates/purchase-request) — โครง PR ที่นำกลับมาใช้ใหม่ได้ผ่าน "Create from Template"

**Master configuration:**
- [master-data/vendor](/th/inventory/master-data/vendor) — ผู้ขายที่ถูกจัดสรรต่อบรรทัด resolve จาก pricelist
- [master-data/currency](/th/inventory/master-data/currency) — สกุลเงินธุรกรรมและอัตราแลกเปลี่ยนสำหรับ PR หลายสกุลเงิน
- [master-data/tax-profile](/th/inventory/master-data/tax-profile) — รหัสภาษีที่ derive ให้บรรทัดของ PR
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยนับของแต่ละบรรทัด PR
- [master-data/department](/th/inventory/master-data/department) — แผนกผู้ขอ / cost center ที่อยู่บนส่วนหัวของ PR
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม workflow อนุมัติแบบหลายระดับสำหรับการอนุญาต PR
- [system-config/running-code](/th/inventory/system-config/running-code) — การกำหนดลำดับเลขเอกสาร PR
- [system-config/dimension](/th/inventory/system-config/dimension) — มิติเชิงวิเคราะห์ (รหัสงาน/รหัสต้นทุน, โครงการ) ที่บันทึกบน PR
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — log การเปลี่ยนสถานะ PR และประวัติการอนุมัติสำหรับการตรวจสอบ
- [reporting-audit/attachment](/th/inventory/reporting-audit/attachment) — เอกสารประกอบ (ใบเสนอราคา, สเปก) ที่แนบกับ PR
- [reporting-audit/notification](/th/inventory/reporting-audit/notification) — การแจ้งเตือนการอนุมัติ / send-back / reject ที่จัดส่งผ่าน workflow

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/purchase-request-management/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [01 — โมเดลข้อมูล](/th/inventory/purchase-request/01-data-model) — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/purchase-request/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด พร้อมการแยก user/system ผ่าน `enum_comment_type`
- [02 — กติกาทางธุรกิจ](/th/inventory/purchase-request/02-business-rules) — การตรวจสอบความถูกต้อง การคำนวณ การกำหนดสิทธิ์ และกฎการ posting
- [03 — User Flow](/th/inventory/purchase-request/03-user-flow) — วงจรชีวิตของเอกสารและสารบัญ persona
  - [Requestor](/th/inventory/purchase-request/03-user-flow-requestor)
  - [Approver](/th/inventory/purchase-request/03-user-flow-approver)
  - [Purchaser](/th/inventory/purchase-request/03-user-flow-purchaser)
  - [Procurement Manager](/th/inventory/purchase-request/03-user-flow-procurement-manager)
  - [Audit / Config](/th/inventory/purchase-request/03-user-flow-audit-config)
- [04 — Test Scenarios](/th/inventory/purchase-request/04-test-scenarios) — ขอบเขตของแต่ละ persona, scenario ข้าม persona และ mapping ไปยัง E2E
  - [Requestor](/th/inventory/purchase-request/04-test-scenarios-requestor)
  - [Approver](/th/inventory/purchase-request/04-test-scenarios-approver)
  - [Purchaser](/th/inventory/purchase-request/04-test-scenarios-purchaser)
  - [Procurement Manager](/th/inventory/purchase-request/04-test-scenarios-procurement-manager)
  - [Audit / Config](/th/inventory/purchase-request/04-test-scenarios-audit-config)

## 8. API Surface (ตรวจสอบแล้ว 2026-09-22)

Route ทั้งหมดอยู่ใน `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/purchase-requests/purchase-requests.controller.ts` (`@Controller('api')`); guard คือ `AppIdGuard('purchaseRequest.<verb>')` บวก `@Permission({ 'procurement.purchase_request': ['view'] })` บน endpoint แบบ list Bruno: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/procurement/purchase-request/`

| Verb + path | วัตถุประสงค์ | หมายเหตุ |
|---|---|---|
| `GET /purchase-requests` | List ข้าม unit (ไม่มี `bu_code` ใน path) | `@Serialize(PurchaseRequestListItemResponseSchema)` |
| `GET /:bu_code/purchase-requests/for-po` | PR ที่อนุมัติแล้วซึ่งเลือกไปแปลงเป็น PO ได้ | |
| `GET /:bu_code/purchase-requests/workflow-stages` · `/:pr_id/previous-stages` | รายการ stage สำหรับ filter / เป้าหมาย send-back | |
| `GET /:bu_code/purchase-requests/:id` | Detail; การอ้างอิงเอนทิตีเป็น object, `last_price` ต่อบรรทัด | serializer `common/dto/purchase-request/purchase-request.serializer.ts` |
| `GET /:bu_code/purchase-requests/:id/status/:status` | Detail ที่กรองตามสถานะ stage ของบรรทัด | `AppIdGuard('purchaseRequest.approval')` |
| `POST /:bu_code/purchase-requests` · `PATCH …/:id/save` | สร้าง / บันทึก draft (`stage_role` ใน body; `@ExpandRefs`) | qty `0` อนุญาตตอน save |
| `POST /:bu_code/purchase-requests/verify` | ตรวจกฎแบบ pre-flight, `verify_state = create \| submit \| approve` | 200 พร้อม `is_valid: false` เมื่อไม่ผ่าน |
| `PATCH …/:id/submit` · `/approve` · `/reject` · `/review` | Verb ของ workflow (`doc_version` ถูก echo กลับ) | `review` = send back |
| `POST …/duplicate-pr` · `POST …/:id/split` | คัดลอก PR; split บรรทัดที่เลือกเป็น PR ใหม่ | |
| `POST …/swipe-approve` · `/swipe-reject` | Bulk approve / reject บน mobile | |
| `DELETE /:bu_code/purchase-requests/:id` · `DELETE …/batch` | Soft-delete draft (เจ้าของหรือ super-admin) | batch คืน `not_found` / `not_draft` / `not_owner` ต่อ id |
| `GET …/:id/export` · `/print` · `/print-viewer` | Export Excel, print PDF | |
| `GET …/detail/:detail_id/dimension` · `/history` · `/calculate` | Dimension ของบรรทัด, ประวัติ stage ต่อบรรทัด, การคำนวณราคา | |
| `POST …/regenerate-totals` · `POST …/:id/regenerate-totals` | คำนวณ roll-up ของ header ใหม่ | |
| `GET /api/my-pending/purchase-requests…` | PR ที่ pending ต่อผู้ใช้ (แท็บ My Pending) | ดู [my-approval](/th/inventory/purchase-request/my-approval) |
