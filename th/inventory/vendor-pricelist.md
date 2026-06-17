---
title: รายการราคาผู้ขาย (Vendor Pricelist)
description: แคตตาล็อกของผู้ขายที่เก็บสินค้าพร้อมราคาที่ตกลง, หน่วย และช่วงเวลาที่มีผลใช้ — แหล่งอ้างอิงราคาของ PR/PO
published: true
date: 2026-05-20T00:00:00.000Z
tags: vendor-pricelist, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** แคตตาล็อกราคาตามผู้ขายแบบมีช่วงเวลาและมี MOQ tier ที่เก็บผ่าน workflow แบบ 6-phase campaign / portal — แหล่งอ้างอิงสำหรับราคา PR / PO / GRN และ variance &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Purchaser, Purchasing Manager, Vendor (portal ภายนอก), Finance, Auditor &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_pricelist`, `tb_pricelist_detail`, `tb_request_for_pricing`, `tb_pricelist_template`, [vendor-pricelist/request-price-list](/th/inventory/vendor-pricelist/request-price-list) &nbsp;·&nbsp; **หน้าย่อย:** 13

![รายการราคาผู้ขาย (Vendor Pricelist) screen](/screenshots/vendor-pricelist/index.png)

## 1. ภาพรวม

**Vendor Pricelist** คือบันทึกที่เป็นทางการของราคาที่ผู้ขายเฉพาะรายได้เสนอสำหรับสินค้าชุดเฉพาะ แสดงในสกุลเงินของผู้ขาย กำหนดช่วงเวลาที่มีผลใช้ และจัดโครงสร้างรอบ tier ของหน่วยและปริมาณการสั่งซื้อขั้นต่ำ (MOQ) ที่ผู้ขายจะยึดถือ แต่ละ pricelist มีส่วนหัว — ผู้ขาย, หมายเลข pricelist, สกุลเงิน, วันที่มีผลใช้-จาก-และ-ถึง, campaign หรือ template ต้นทาง, วิธีการส่ง, สถานะ, คะแนนคุณภาพ และฟิลด์ audit — และ line item หนึ่งหรือมากกว่าที่ carry การอ้างอิงสินค้า, แถวราคาตาม MOQ tier (หน่วย, ราคาต่อหน่วย, conversion factor, effective unit price, lead time), สถานะการ validate และโน้ต สินค้าเดียวกันบน pricelist ของผู้ขายรายเดียวกันสามารถมี MOQ หลายแถว (เช่น MOQ 1 ที่ €12.50/Each, MOQ 50 ที่ €10.50/Each, MOQ 100 ที่ €9.75/Each) และระบบจะ auto-sort และ validate ให้ปริมาณที่สูงกว่ามีราคาต่อหน่วยต่ำกว่าหรือเท่ากันอย่างสม่ำเสมอ

Pricelist เป็นเฉพาะผู้ขายและมีกำหนดเวลา ผู้ขายหลายรายสามารถ carry สินค้าเดียวกัน แต่ละรายอยู่บน pricelist ของตนเองที่ราคาและสกุลเงินของตนเอง และฟังก์ชัน procurement ตัดสิน — ต่อสินค้า ต่อ category หรือผ่าน business rule — ว่า pricelist ของผู้ขายรายไหนเป็นแหล่ง **preferred** สำหรับสินค้านั้น ณ ขณะใดก็ตาม Multi-currency เป็น first-class: ผู้ขายเลือกสกุลเงินตอน submit และระบบ carry มันผ่านการแสดงผล, เปรียบเทียบ และรายงาน โดยการแปลงสกุลเกิดที่จุดใช้งาน (ราคา PR, การผูกพัน PO, variance ของ GRN) แทนการ mutate ราคาผู้ขายที่เก็บไว้ Pricelist ถูกเก็บผ่าน workflow แบบ 6-phase — vendor setup, การสร้าง template, การวางแผน campaign, การเชิญ, การ submit ผ่าน secure portal, การ validate — เพื่อให้ราคาที่ระบบที่เหลือพึ่งพามี provenance ที่ชัดเจนและ audit trail ที่ป้องกันได้กลับไปยังผู้ขายที่เสนอราคา

เมื่อ active แล้ว pricelist จะกลายเป็น dataset อ้างอิงสำหรับการตัดสินใจ procurement ปลายน้ำทุกครั้ง ราคา PR default จาก pricelist active ของ preferred vendor; ราคาต่อหน่วยของ PO ถูก validate กับมันก่อนที่ commitment จะถูกส่ง; การ post GRN คำนวณ variance ราคาระหว่างค่าที่รับ-และ-วางบิลและค่าของ pricelist active; และรายงาน finance จัดกลุ่มการใช้จ่ายตามผู้ขายและ pricelist สำหรับการต่อรอง Pricelist ที่หมดอายุหรือถูกแทนที่ยัง queryable ได้สำหรับการวิเคราะห์ประวัติและการตรวจจับ price-trend ในขณะที่มีเพียง pricelist เดียวต่อ window vendor-product-validity ที่ถูกจัดเป็น active สำหรับธุรกรรมสด

## 2. บริบททางธุรกิจ

Vendor pricelist คือกลไกที่องค์กรบังคับใช้อัตราที่ต่อรอง Procurement ใช้ความพยายามจริงในการต่อรองราคา, หน่วย, MOQ tier และ window ที่มีผลใช้กับผู้ขายแต่ละราย; โดยปราศจาก pricelist สด แบบ system-of-record ที่ผูกกับข้อตกลงเหล่านั้น อัตราที่ต่อรองดำรงอยู่บนกระดาษเท่านั้นและผู้ซื้อ default ไปยังราคาใดก็ตามที่ผู้ขายเสนอในวัน การ route ทุก PR และ PO ผ่าน pricelist active ปิด gap นั้น: ราคา PR default จาก pricelist, ราคา PO ถูก validate กับมัน และ variance ราคา GRN ถูกคำนวณกับมัน บรรทัดที่เบี่ยงเบนจาก pricelist ถูก flag ทันทีให้ Purchaser review แทนที่จะค้นพบหลังจากนั้นหลายสัปดาห์ที่ invoice match

โมดูลนี้ยังเป็นฐานสำหรับการรายงาน variance และ procurement performance เพราะธุรกรรมทุกรายการ anchor กับราคาผู้ขายที่ทราบ ณ จุดเวลาที่ทราบ Finance สามารถปริมาณวัด gap ระหว่างราคาที่ต่อรองและราคาที่เกิดขึ้นจริง — ตามสินค้า, ผู้ขาย, period หรือผู้ซื้อ — และป้อนกลับเข้าสู่รอบการต่อรองครั้งหน้า Quality scoring ที่ระดับการ submission (ความสมบูรณ์ของข้อมูล, การปฏิบัติตาม business-rule, ความน่าเชื่อถือของผู้ขาย) ไหลผ่านเข้าสู่ vendor performance metric และมีอิทธิพลต่อผู้ขายที่ถูกเลือกสำหรับ PR ครั้งหน้า Audit trail — campaign, invitation token, วิธีการ submission, ผลการ validate, การอนุมัติ — ให้ผู้ตรวจสอบ chain of custody ที่สะอาดจากใบเสนอราคาของผู้ขายถึงราคาบรรทัดบน invoice ที่ post

ในเชิงปฏิบัติ โมดูลนี้บีบกระบวนการที่ปกติเป็น email-and-spreadsheet หนัก Template ทำให้สิ่งที่ขอจากผู้ขายเป็นมาตรฐาน; campaign orchestrate ว่าราคาถูกเก็บเมื่อไรและจากใคร; secure vendor portal ให้ผู้ขายป้อนราคาโดยตรง, อัปโหลด Excel template หรือ email ไปยังฝ่ายจัดซื้อ — โดย engine validation เดียวกันรันข้ามทั้งสาม channel Auto-save, draft mode และการติดตามความคืบหน้าให้ผู้ขายทำราคาให้เสร็จข้าม session หลายครั้งโดยไม่สูญเสียงาน ซึ่งปรับปรุงอัตราการตอบสนองและคุณภาพของข้อมูลราคาที่โมดูลปลายน้ำบริโภคอย่างมีนัยสำคัญ

## 3. แนวคิดสำคัญ

- **Pricelist Header**: บันทึกระดับผู้ขายที่ carry การอ้างอิงผู้ขาย, หมายเลข pricelist, campaign และ template ต้นทาง, สกุลเงิน, วันที่มีผลใช้-จาก-และ-ถึง, วิธีการ submission (online, upload, email), สถานะ (`draft`, `submitted`, `under-review`, `approved`, `rejected`), คะแนนคุณภาพ, ผลการ validate และฟิลด์ audit Header ผูก line item ทั้งหมดให้กับผู้ขายรายเดียวในสกุลเงินเดียวสำหรับ window ที่มีผลใช้เดียว
- **Pricelist Line / Pricelist Item**: แถวที่แทนสินค้าตัวเดียวบน pricelist carry การอ้างอิงสินค้า (รหัส, ชื่อ, category), แถวราคา MOQ-tiered หนึ่งแถวหรือมากกว่า, lead time และโน้ตแบบเลือกได้ และสถานะการ validate (`valid`, `warning`, `error`) บรรทัดคือหน่วยของการ lookup ราคาสำหรับ PR, PO และ GRN
- **MOQ Tier**: แถวราคาภายในบรรทัด pricelist ที่ระบุ minimum order quantity, หน่วยวัด, conversion factor (เช่น 1 Box = 50 Each), ราคาต่อหน่วย, effective unit price ต่อหน่วยฐาน และ lead time แบบเลือกได้ สินค้าแต่ละชิ้นสามารถ carry หลาย tier และถูก auto-sort ตาม MOQ; ระบบ validate ว่าปริมาณที่สูงกว่ามีราคาต่อหน่วยต่ำกว่าหรือเท่ากัน
- **Validity Period**: window วันที่จาก-และ-ถึงระหว่างที่ pricelist ถูกจัดเป็นแหล่งอ้างอิงปัจจุบันสำหรับราคาปลายน้ำ นอก window pricelist เป็นแบบ historical-only — queryable สำหรับรายงาน ไม่ใช้สำหรับการ default PR/PO ใหม่หรือ variance GRN
- **Preferred Vendor**: ผู้ขายที่ pricelist active ถูกจัดเป็น default source ของราคาและ supply สำหรับสินค้าที่กำหนด ตั้งต่อสินค้า (หรือต่อ category) และ resolve ที่การสร้าง PR-item; โมดูลปลายน้ำดึงราคาจาก pricelist ของผู้ขายนี้เว้นแต่กติกา, override หรือ fallback เลือกแตกต่างกัน
- **Price Variance**: เดลตาระหว่างราคาที่ transact (บรรทัด PO, บรรทัด GRN, บรรทัด invoice ของผู้ขาย) และราคาต่อหน่วยบน pricelist active สำหรับการรวม vendor-product-unit-quantity เดียวกัน ณ จุดเวลานั้น คำนวณที่การ post GRN และ three-way match; ค่าที่เกินขีดจำกัดที่ตั้งค่าไว้ถูก flag สำหรับ review
- **Unit Conversion**: factor ที่ map หน่วยการตั้งราคาของผู้ขาย (Box, Carton, Pack) ไปยังหน่วยฐานของ inventory (Each) จับต่อ MOQ tier เพื่อให้ effective unit price ต่อหน่วยฐานถูกคำนวณและเปรียบเทียบได้ข้ามผู้ขายและหน่วย
- **Price Collection Template**: นิยามที่ใช้ซ้ำได้ของสิ่งที่จะถามผู้ขาย — สินค้า (เลือกตาม category, subcategory, item group หรือ item เฉพาะ), สกุลเงินที่รองรับ, ฟิลด์ที่ต้องการ, ขีดจำกัด MOQ tier, validity period และกติกาการ validate ใช้สร้าง Excel template และ portal interface เฉพาะผู้ขาย
- **Price Collection Campaign**: instance ที่ตั้งเวลา, targeting ผู้ขายของ template — ชื่อ campaign, ผู้ขายที่เลือก, วันเริ่มและสิ้นสุด, schedule การ reminder, สถานะ (`draft`, `active`, `paused`, `completed`, `cancelled`) และ analytics ที่ aggregate เกี่ยวกับการตอบสนองและความสำเร็จ ครั้งเดียว, เกิดซ้ำ หรือ event-based
- **Vendor Invitation**: บันทึกต่อผู้ขายของ campaign — การอ้างอิงผู้ขาย, token cryptographic ที่ไม่ซ้ำกัน, identifier ของ pricelist, telemetry การส่ง email (sent, delivered, opened, clicked), telemetry การเข้าถึง portal (first/last access, จำนวน session, IP address) และสถานะการ submission (`pending`, `in-progress`, `submitted`, `approved`, `expired`) แต่ละ invitation สร้าง pricelist เฉพาะผู้ขายหนึ่งใบ
- **Submission Method**: วิธีที่ผู้ขายส่งราคากลับมา — `online` (ป้อนตรงใน portal พร้อม inline MOQ expansion และ auto-save), `upload` (Excel template อัปโหลดไป portal) หรือ `email` (Excel email ไปยังฝ่ายจัดซื้อให้ staff ประมวลผล) engine validation เดียวกันรันข้ามทั้งสาม
- **Validation Engine**: ชุดกติกาที่รันกับทุกการ submission — รูปแบบ (ราคา, สกุลเงิน, หน่วย), ความสมบูรณ์ (ฟิลด์ที่ต้องการ, ข้อมูลขาด) และ business rule (ไม่มี MOQ ซ้ำ, ปริมาณที่สูงกว่า ≤ ราคาต่อหน่วย, ความสมเหตุสมผลของราคา vs ข้อมูลประวัติและตลาด) ผลิตผลการ validate, คะแนนคุณภาพ และคำแนะนำการแก้ไขใน inline
- **Quality Score**: rating อัตโนมัติของ pricelist ที่ submit รวมความสมบูรณ์ของข้อมูล, ความถูกต้องของรูปแบบ, อัตราการผ่าน business-rule และความสม่ำเสมอ ป้อนเข้าสู่การ route การอนุมัติและ profile performance ของผู้ขายสำหรับการเลือกผู้ขายในอนาคต
- **Portal Token**: token การเข้าถึง portal ต่อผู้ขายที่ปลอดภัยเชิง cryptographic, มี time limit ที่ฝังในอีเมล invitation อนุญาตการเข้า portal, บังคับใช้ session limit และการติดตาม IP และสามารถถูก revoke ทันทีโดยฝ่ายจัดซื้อหรือ admin
- **Auto-Save / Draft Mode**: กลไกของ vendor portal ที่บันทึกราคาที่ป้อนทุก ~30 วินาที, รักษา state ข้าม session และรองรับการ submission บางส่วน ผู้ขายสามารถจากไปและกลับมาโดยไม่สูญเสียงาน; staff สามารถเห็นอายุของ draft และความคืบหน้า
- **Active Pricelist**: สำหรับการรวม vendor-product-unit-validity ใด ๆ แถว pricelist เดียวที่ approve, อยู่ใน window และถูกจัดเป็นการอ้างอิงสดสำหรับราคาปลายน้ำและการคำนวณ variance

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Purchaser / Purchasing Staff | ต่อรองอัตรากับผู้ขาย, สร้าง template และ campaign การเก็บราคา, ส่ง invitation, review และ approve pricelist ที่ submit, จัดการการแก้ price-item รายตัวและ status, กำหนด preferred vendor ต่อสินค้า และ upload การ submission ที่ส่งมาทาง email ของผู้ขาย เป็นเจ้าของ lifecycle ของ pricelist เชิงปฏิบัติการ end-to-end |
| Purchasing Manager | เป็นเจ้าของกลยุทธ์การต่อรองและส่วนผสมของผู้ขาย, approve pricelist มูลค่าสูงหรือที่มีความ sensitive เชิงกลยุทธ์, ตั้งค่า business rule สำหรับ logic preferred-vendor และ price-assignment และเซ็นอนุมัติบนราคา multi-currency และข้ามพรมแดน |
| Vendor | External party ที่ได้รับ invitation, เข้าถึง secure portal ผ่าน token, ให้ราคาผ่านการป้อน online, upload Excel หรือ email submission, เลือกสกุลเงิน, จัด MOQ tier พร้อมหน่วยและ conversion factor และสามารถบันทึก draft และ resubmit ผู้ให้ข้อมูลราคา |
| Finance Officer / Accounts Payable | ตรวจสอบ variance ราคาระหว่าง pricelist active และบรรทัด GRN/invoice ที่ post, validate การจัดการสกุลเงินและอัตราแลกเปลี่ยน, reconcile ราคาที่ต่อรอง vs ที่เกิดขึ้นจริง และป้อนข้อค้นพบ variance กลับไปยัง procurement |
| Finance Manager | review รายงาน variance และ performance ผู้ขาย, validate ผลกระทบทางการเงินของ pricelist multi-currency และทำให้แน่ใจว่า audit trail สนับสนุนความต้องการ compliance และการรายงาน |
| Receiver / Store Keeper | ผู้บริโภคทางอ้อม — การ post GRN ใช้ pricelist active สำหรับการคำนวณ variance; ความเบี่ยงเบนที่มีนัยสำคัญจาก pricelist ถูก surface สำหรับ review ที่จุดรับ |
| System Administrator | ตั้งค่าการกำหนดเลข pricelist, การเปลี่ยนสถานะ, RBAC, การตั้งค่า template และ campaign, นโยบาย portal token (การหมดอายุ, IP restriction, session limit), การเชื่อมต่อการส่ง email และกติกาการ validate จัดการการ revoke token และการเก็บ audit log |
| Auditor | สิทธิ์อ่านอย่างเดียวต่อ pricelist, campaign, invitation, ประวัติการ submission, ผลการ validate และ activity log — ใช้ตรวจสอบ provenance ของราคา, การแยกหน้าที่ และ traceability end-to-end จากใบเสนอราคาของผู้ขายถึง invoice ที่ post |

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [product](/th/inventory/product) — entry ของ pricelist อ้างอิงสินค้า
- [purchase-request](/th/inventory/purchase-request) — PR default จาก pricelist ของ preferred vendor
- [purchase-order](/th/inventory/purchase-order) — PO validate ราคากับ pricelist active
- [good-receive-note](/th/inventory/good-receive-note) — Variance ราคา GRN ถูกคำนวณกับ pricelist

**Master configuration:**
- [master-data/vendor](/th/inventory/master-data/vendor) — master ของผู้ขายที่ pricelist แต่ละใบ scope ไป
- [master-data/currency](/th/inventory/master-data/currency) — สกุลเงินที่ผู้ขายเลือกตอน submission
- [master-data/tax-profile](/th/inventory/master-data/tax-profile) — รหัสภาษีบนแต่ละบรรทัดของ pricelist
- [templates/price-list](/th/inventory/templates/price-list) — template ที่ใช้ซ้ำได้ที่กำหนดสิ่งที่จะถามผู้ขายใน campaign
- [master-data/unit](/th/inventory/master-data/unit) — หน่วยการตั้งราคา (Box / Carton / Pack) บวก conversion ไปยังหน่วย inventory ฐาน
- [system-config/workflow](/th/inventory/system-config/workflow) — workflow การ submission และอนุมัติ pricelist
- [reporting-audit/activity](/th/inventory/reporting-audit/activity) — activity log การ submission, validation และ approval ของ pricelist สำหรับ audit

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/vendor-pricelist-management/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [vendor-pricelist/01-data-model](/th/inventory/vendor-pricelist/01-data-model) — เอนทิตี, ฟิลด์, ความสัมพันธ์, enum สำหรับ tenant-schema model สิบตัว (`tb_pricelist_template`, `tb_pricelist_template_detail`, `tb_pricelist_template_comment`, `tb_pricelist_template_detail_comment`, `tb_request_for_pricing`, `tb_request_for_pricing_comment`, `tb_request_for_pricing_detail`, `tb_request_for_pricing_detail_comment`, `tb_pricelist`, `tb_pricelist_detail`, `tb_pricelist_comment`, `tb_pricelist_detail_comment`) และ enum module-local สามตัว (`enum_pricelist_template_status`, `enum_pricelist_status`, `pricelist_submission_method`) บวกตาราง divergence สำหรับความแตกต่าง material 12 รายการระหว่าง carmen/docs `design.md` และ Prisma
- [01a — โมเดลข้อมูล — ตารางคอมเมนต์](/th/inventory/vendor-pricelist/01a-data-model-comments) — ตารางคอมเมนต์ / ไฟล์แนบระดับเอกสารและระดับบรรทัด ครอบคลุมทั้งสาม sub-entity families
- [vendor-pricelist/02-business-rules](/th/inventory/vendor-pricelist/02-business-rules) — การ validate (`VPL_VAL_001`–`VPL_VAL_025`), การคำนวณ (`VPL_CALC_001`–`VPL_CALC_008`), authorization (`VPL_AUTH_001`–`VPL_AUTH_015`), status / posting (`VPL_POST_001`–`VPL_POST_022` ข้ามทั้งสาม lifecycle + สถานะ campaign / invitation ที่ derive จากแอป) และกติกาข้ามโมดูล (`VPL_XMOD_001`–`VPL_XMOD_009` ไป PR / PO / GRN / product / vendor / currency / validation engine)
- [vendor-pricelist/03-user-flow](/th/inventory/vendor-pricelist/03-user-flow) — ภาพรวม lifecycle ของเอกสาร + index persona
  - [vendor-pricelist/03-user-flow-purchaser](/th/inventory/vendor-pricelist/03-user-flow-purchaser) — เส้นทาง Purchaser + Purchasing Manager (รวบ): template builder, campaign launcher, submission reviewer, preferred-vendor curator
  - [vendor-pricelist/03-user-flow-vendor](/th/inventory/vendor-pricelist/03-user-flow-vendor) — เส้นทาง Vendor (ภายนอก, portal session ที่ authenticate ด้วย token) ไฟล์สั้นกว่า — persona ภายนอกตัวเดียวใน Carmen suite ที่มีผลคงทนใน-ระบบผ่าน portal
  - [vendor-pricelist/03-user-flow-finance](/th/inventory/vendor-pricelist/03-user-flow-finance) — Finance Officer + Finance Manager (audit variance กับ GRN / invoice; co-signoff multi-currency สำหรับการ activate)
  - [vendor-pricelist/03-user-flow-audit-config](/th/inventory/vendor-pricelist/03-user-flow-audit-config) — Auditor + System Administrator (chain audit อ่านอย่างเดียว; การกำหนดเลข, RBAC, นโยบาย portal-token, การเชื่อม email, กติกา validation, แหล่ง currency / FX, การเก็บ audit; การ revoke token ต่อ invitation)
- [vendor-pricelist/04-test-scenarios](/th/inventory/vendor-pricelist/04-test-scenarios) — ภาพรวม test-scenario + scenario handoff ข้าม persona 12 รายการ + เป้าหมายการ mapping E2E (roadmap item — ไม่มี spec dedicated วันนี้)
  - [vendor-pricelist/04-test-scenarios-purchaser](/th/inventory/vendor-pricelist/04-test-scenarios-purchaser) — scenario Purchaser + Manager
  - [vendor-pricelist/04-test-scenarios-vendor](/th/inventory/vendor-pricelist/04-test-scenarios-vendor) — scenario Vendor; section Permission คือ N/A (แถวเดียว) เพราะ vendor ไม่มี Carmen RBAC matrix
  - [vendor-pricelist/04-test-scenarios-finance](/th/inventory/vendor-pricelist/04-test-scenarios-finance) — scenario Finance Officer + Manager
  - [vendor-pricelist/04-test-scenarios-audit-config](/th/inventory/vendor-pricelist/04-test-scenarios-audit-config) — scenario Auditor + Sysadmin

> **สถานะ:** หน้าย่อยทั้งหมดเป็นรายละเอียดเต็มและ self-contained section Data-model ยึดกับ Prisma schema canonical (`tb_pricelist*` + `tb_request_for_pricing*` + `tb_pricelist_template*` — สิบเอนทิตี, สาม enum module-local); business-rules แนะนำแคตตาล็อก rule-ID `VPL_*` ยึดกับ carmen/docs (`design.md`, `requirements.md`, `price-assignment-workflow-documentation.md`); user-flow และ test-scenarios ครอบคลุมกลุ่ม persona ทั้งสี่ที่รวบจาก 8 persona ใน Section 4 Receiver / Store Keeper จาก Section 4 ถูกบันทึกเป็นผู้บริโภคทางอ้อมใน scenario ข้าม persona (ไม่มีไฟล์ persona dedicated) ไม่มี E2E spec วันนี้ — coverage รันที่ระดับ API / integration และผ่าน E2E spec ของโมดูลปลายน้ำ (`401-po.spec.ts`, `402-po-purchaser-journey.spec.ts`); vendor-pricelist E2E spec dedicated เป็น roadmap item ตาม `../carmen/docs/vendor-pricelist-management/tasks.md`
