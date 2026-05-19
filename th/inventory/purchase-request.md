---
title: ใบขอซื้อ (Purchase Request)
description: เอกสารคำขอภายในเพื่อจัดซื้อสินค้า — สัญญาณความต้องการต้นน้ำที่จะถูกแปลงเป็นใบสั่งซื้อหลังได้รับอนุมัติ
published: true
date: 2026-05-19T20:00:00.000Z
tags: purchase-request, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# ใบขอซื้อ (Purchase Request)

> **At a Glance**
> **วัตถุประสงค์ของโมดูล:** workflow ความต้องการภายในแบบหลายระดับที่รับรู้งบประมาณ (`Draft` → `Submitted` → `Under Review` → `Approved`/`Rejected`/`Sent Back`) ส่งความต้องการที่จัดสรรผู้ขายแล้วต่อให้ฝ่ายจัดซื้อ &nbsp;·&nbsp; **กลุ่มผู้ใช้:** Requestor, Department Head, Budget Controller, Finance, Purchaser, Procurement Manager, Auditor &nbsp;·&nbsp; **เอนทิตี/ตารางหลัก:** `tb_purchase_request`, `tb_purchase_request_detail`, approval history, pricelist allocation, [[purchase-request/my-approval]] &nbsp;·&nbsp; **หน้าย่อย:** 15

![Purchase Request module screen](/screenshots/purchase-request/index.png)

## 1. ภาพรวม

**ใบขอซื้อ (Purchase Request — PR)** คือเอกสารคำขอภายในที่หน่วยงานปฏิบัติการสร้างขึ้นเพื่อขออนุมัติการจัดซื้อสินค้าหรือบริการ ก่อนที่จะมีการผูกพันใด ๆ กับผู้ขายภายนอก แต่ละ PR ประกอบด้วยส่วนหัว — หมายเลขอ้างอิงที่ระบบสร้างให้อัตโนมัติ วันที่ขอและวันที่ต้องการรับของ ประเภท PR (General Purchase, Market List, Asset) ผู้ขอและแผนก รหัสงาน/รหัสต้นทุน จุดส่งของ คำอธิบายและเหตุผลประกอบ สกุลเงินและอัตราแลกเปลี่ยน — และรายการสินค้าหนึ่งรายการขึ้นไปที่บรรจุข้อมูลสินค้าจากแคตตาล็อกหรือคำอธิบายแบบอิสระ คลังจัดเก็บ ปริมาณที่ขอและปริมาณที่อนุมัติ ปริมาณ FOC หน่วยนับ ราคาต่อหน่วยโดยประมาณ ส่วนลด การจัดการภาษี ยอดรวมต่อบรรทัดที่ระบบคำนวณให้ และลิงก์ไปยังคลังสินค้าและประวัติ PO ส่วนหัวจะรวบยอดจากรายการต่าง ๆ เป็น subtotal, total discount, total tax และ grand total ทั้งในสกุลเงินที่ใช้บันทึกธุรกรรมและสกุลเงินฐาน

วงจรชีวิตของ PR ขับเคลื่อนด้วย workflow: `Draft` (ผู้ขอแก้ไขได้ ยังไม่กระทบงบประมาณหรือสต๊อก) → `Submitted` (เข้าสายอนุมัติ พร้อมสร้าง soft commitment กับงบประมาณ) → `Under Review` (อยู่ในมือของผู้อนุมัติหนึ่งคนหรือมากกว่า) → `Approved` (พร้อมจัดซื้อและพร้อมแปลงเป็นใบสั่งซื้อ) หรือ `Rejected` / `Sent Back` (ส่งกลับให้ผู้ขอพร้อมความคิดเห็น) การอนุมัติเป็นแบบ **หลายระดับ** และอ้างอิงตามมูลค่า — โดยทั่วไปคือ หัวหน้าแผนกก่อน จากนั้น budget controller จากนั้น finance review สำหรับ PR มูลค่าสูง และสุดท้ายคือการเซ็นอนุมัติจาก procurement — พร้อมกติกา delegation of authority เพื่อให้สายอนุมัติเดินหน้าได้แม้ผู้อนุมัติไม่อยู่ PR ที่ submit แล้วจะไม่สามารถ void ได้ การยกเลิกทำได้ผ่านเส้นทาง reject ของ workflow เท่านั้น เพื่อรักษา audit trail ไว้ครบถ้วน

PR เป็นสัญญาณความต้องการต้นน้ำในห่วงโซ่ procure-to-pay มันบันทึก *อะไร* ที่ต้องการ *เพื่อใคร* *เมื่อไหร่* และ *ราคาประมาณเท่าไหร่* แล้วส่งความต้องการที่ผ่านการอนุมัติ มีต้นทุนกำกับ และถูกจัดสรรผู้ขายแล้วต่อให้ฝ่ายจัดซื้อ ฟังก์ชัน Allocate Vendor จะเลือกผู้ขายที่ต้องการจาก pricelist โดยใช้กฎที่จัดลำดับความสำคัญไว้ (vendor rank ก่อน ตามด้วยราคาต่ำสุด ตามด้วยประวัติการรับของล่าสุด) ดึงอัตราภาษีและราคาต่อหน่วยจาก pricelist และ PR ที่ผ่านการอนุมัติ — พร้อมปริมาณที่อนุมัติและผู้ขายที่เลือก — จะถูกแปลงเป็นใบสั่งซื้อเพื่อผูกพันภายนอก งบประมาณจะถูกบันทึกเป็น soft commitment ตอน submit และเปลี่ยนเป็น commitment จริงก็ต่อเมื่อมีการออก PO

## 2. บริบททางธุรกิจ

ธุรกิจ procurement ในอุตสาหกรรมโรงแรมดำเนินบนกำไรขั้นต้นที่บางเฉียบ และมีการซื้อปริมาณมากต่อใบแต่มูลค่าต่อใบไม่สูงกระจายอยู่ใน cost center จำนวนมาก PR จึงเป็นจุดควบคุมที่ป้องกันการใช้จ่ายที่ควบคุมไม่ได้ก่อนที่จะมีการผูกพันภายนอก โดยการบังคับให้ความตั้งใจซื้อทุกครั้งผ่าน workflow ที่มีเอกสารกำกับ รับรู้งบประมาณ และผ่านผู้อนุมัติหลายระดับ — พร้อมข้อมูลบังคับ เช่น ผู้ขอ แผนก วันส่งของ เหตุผลประกอบ และหมายเลขอ้างอิงที่ไม่ซ้ำกัน — PR บังคับใช้นโยบายการใช้จ่ายไว้ที่ต้นน้ำของผู้ขาย และให้ฝ่ายการเงินเห็นภาพอนาคตของยอดผูกพันที่จะเกิดขึ้น การบันทึก soft commitment เมื่อ submit หมายความว่าการใช้งบประมาณจะปรากฏให้เห็นทันทีที่มีการตั้ง PR ไม่ใช่ตอนที่ของถึงมือ ซึ่งเป็นสิ่งที่ป้องกันไม่ให้แผนกใช้งบเกินโดยไม่ตั้งใจ

นอกจากนี้โมดูลนี้ยังเป็นแกนของการเชื่อมต่อกับทุกอย่างที่อยู่ปลายน้ำ ข้อมูล PR ไหลเข้าสู่โมดูลงบประมาณ (การตรวจสอบความพร้อมและ soft commitment) โมดูลคลังสินค้า (on-hand, on-order, reorder level, last price ที่ผู้ขอเห็นได้) โมดูลผู้ขาย (การ lookup pricelist, vendor ranking, price comparison) workflow engine (การจัดเส้นทางอนุมัติและการแจ้งเตือนที่ตั้งค่าได้) และโมดูลใบสั่งซื้อ (การแปลง PR ไปเป็น PO พร้อม traceability เต็มรูปแบบ) Document management (comments, attachments, activity log) ทำให้ PR ทุกใบมี audit trail ครบถ้วน — ใครสร้าง ใครแก้ ใครอนุมัติหรือปฏิเสธ และเมื่อใด — ซึ่งเป็นสิ่งที่ผู้ตรวจสอบมองหาในช่วงการตรวจสอบ compliance และเป็นสิ่งที่ผู้ปฏิบัติงานพึ่งพาเวลาตรวจสอบปัญหาเรื่องการจัดซื้อ

ความถูกต้องทางการเงินถูกบังคับใช้ที่ชั้นการคำนวณ ไม่ปล่อยให้เป็นหน้าที่ของ UI — line item subtotal, discount, net, tax และ total ถูกปัดเศษแยกที่ระดับบรรทัดด้วย banker's rounding โดยใช้ทศนิยม 3 ตำแหน่งสำหรับปริมาณ 2 ตำแหน่งสำหรับเงิน และ 5 ตำแหน่งสำหรับอัตราแลกเปลี่ยน ยอดรวมระดับ PR roll up จากค่าบรรทัดที่ปัดเศษแล้ว และการรับของข้ามสกุลเงินจะถูก dual-post พร้อมการปัดเศษการแปลงสกุลที่ระบุชัดเจน ระบบรองรับการตั้งราคาแบบ tax-inclusive และ tax-exclusive การปรับ discount และ tax ด้วยมือที่ flag แยก และการอนุมานภาษีที่แตกต่างกันตามเส้นทางการจัดสรร (การเลือกสินค้าด้วยมือใช้อัตราภาษีของสินค้า การ auto-allocation ใช้ภาษีจาก pricelist) ความเข้มงวดนี้คือสิ่งที่ทำให้ยอดรวมของ PR กระทบยอดได้สะอาดกับ PO และ GRN ที่ตามมา

## 3. แนวคิดสำคัญ

- **Approval Level**: ขั้นตอนในสาย workflow ของ PR ที่ตั้งค่าได้ พร้อม role ผู้อนุมัติและเกณฑ์มูลค่า ระดับทั่วไปคือ หัวหน้าแผนก (บังคับสำหรับทุก PR), budget controller (ตรวจสอบกับงบประมาณที่มี), finance review (บังคับสำหรับ PR มูลค่าสูงเกินเกณฑ์ที่ตั้งไว้) และการเซ็นอนุมัติสุดท้ายจาก procurement กฎ delegation ส่งต่อการอนุมัติให้ผู้แทนเมื่อผู้อนุมัติหลักไม่อยู่ และเส้นทางทั้งหมดถูกบันทึกไว้ใน activity log
- **Budget Check**: การตรวจสอบความพร้อมของงบประมาณกับ budget category ของแผนกและ cost center ของผู้ขอตอน submit ระบบจะแสดง total budget, soft commitment จาก PR เปิดอื่น ๆ, soft commitment จาก PO เปิด, hard commitment และ available budget ที่เหลือ จากนั้น flag PR ที่จะเกินงบ — โดยไม่บล็อกการ submit — เพื่อให้ finance สามารถ review และ override หรือ reject ได้
- **Soft Commitment**: การกันงบประมาณชั่วคราวที่ถูกสร้างขึ้นเมื่อ PR ถูก submit จะลดงบประมาณที่พร้อมใช้สำหรับการวางแผน แต่สามารถถอนคืนได้ (PR ที่ถูก reject หรือ cancel จะปล่อย soft commitment ออก) Soft commitment เปลี่ยนเป็น firm commitment ก็ต่อเมื่อ PR ถูกแปลงเป็นใบสั่งซื้อ
- **Preferred Vendor / Allocate Vendor**: ฟังก์ชันของระบบที่เลือกผู้ขายสำหรับแต่ละบรรทัดของ PR โดยใช้กฎที่จัดลำดับความสำคัญ — เริ่มจาก vendor ranking บน pricelist ตามด้วยราคาต่อหน่วยต่ำสุด ตามด้วยประวัติการรับของล่าสุด — และเติมราคาต่อหน่วยและอัตราภาษีจากแถวที่สอดคล้องใน pricelist ผู้ใช้สามารถ override การจัดสรรด้วยมือได้ ในกรณีนั้นภาษีจาก pricelist จะถูกใช้ ถ้า Adjust checkbox ของบรรทัดถูกเลือก ราคาจะไม่ถูกอัปเดตอัตโนมัติเมื่อมีการ re-allocation
- **PR Type**: การจำแนกประเภท (General Purchase, Market List, Asset) ที่กำหนดการจัดเส้นทางอนุมัติ การลงรหัสบัญชี และพฤติกรรม PO ที่ตามมา Market List PR มักเป็นการสั่งของสด ปริมาณบ่อย มูลค่าต่อใบไม่สูง พร้อมเส้นทางอนุมัติที่กระชับ Asset PR ผ่านเส้นทางอนุมัติงบลงทุน ส่วน General Purchase ครอบคลุมที่เหลือ
- **Approved Quantity vs. Requested Quantity**: ทุกบรรทัดของ PR มีทั้งสองค่า ผู้ขอใส่ requested quantity ผู้อนุมัติสามารถปรับ approved quantity ลง (หรือปรับขึ้นเมื่อมีอำนาจ) ระหว่าง review โดยไม่ต้องส่งกลับ PR ค่า approved quantity คือค่าที่จะไหลต่อไปยังใบสั่งซื้อตอนแปลง
- **FOC (Free of Charge)**: ฟิลด์ระดับบรรทัดสำหรับสินค้าที่ผู้ขายให้มาในราคา 0 (ตัวอย่าง, โบนัสส่งเสริมการขาย) ปริมาณ FOC ถูกติดตามแยกจากปริมาณที่มีราคา ไม่ถูกรวมใน subtotal ของ PR แต่ปรากฏบน PO และ GRN ที่ตามมา เพื่อให้ฝั่งรับสินค้าบันทึกเข้าคลัง
- **Conversion to PO**: ขั้นตอนของฝ่ายจัดซื้อที่นำ PR หนึ่งใบหรือหลายใบที่อนุมัติแล้วมาออกเป็นใบสั่งซื้อ — แปลงทีละ PR, รวมหลาย PR เป็นใบเดียว (เมื่อ vendor, currency และเงื่อนไขตรงกัน) หรือแปลงบางบรรทัดของ PR PR จะคงลิงก์ไปยัง PO ที่เกิดขึ้น และบรรทัดที่ยังไม่แปลงจะเปิดค้างไว้จนกว่าจะสำเร็จหรือถูกยกเลิก
- **Cancellation / Reject**: PR ที่อยู่ในสถานะ `Draft` ผู้ขอสามารถ void ได้โดยตรง เมื่อ submit แล้ว การยกเลิกทำได้ผ่าน workflow เท่านั้น — ผู้อนุมัติเลือก **Reject** (ปิด PR พร้อมเหตุผล) หรือ **Send Back** (ส่งกลับให้ผู้ขอแก้ไขและ submit ใหม่) Split & Reject ให้ผู้อนุมัติปฏิเสธเฉพาะบรรทัดและอนุมัติส่วนที่เหลือ Audit trail และการถอน soft commitment จัดการอัตโนมัติโดย workflow
- **Price Comparison**: มุมมองระดับบรรทัดที่แสดงผู้ขายทุกรายบน pricelist ของสินค้า พร้อม rank, ราคาต่อหน่วย, ส่วนลด, FOC, ช่วง quantity-break และหน่วยนับ เพื่อให้ผู้ขอและผู้อนุมัติเห็นและสามารถ override ผู้ขายที่ระบบจัดสรรอัตโนมัติได้พร้อมข้อมูลครบถ้วน

## 4. บทบาทและ Persona

| Role | ความรับผิดชอบ |
|------|----------------|
| Requestor | พนักงานโรงแรมหรือพนักงานแผนกที่เป็นผู้ตั้ง PR สร้างคำขอ เลือกประเภท PR เพิ่มรายการสินค้าพร้อมปริมาณ หน่วย ราคาประมาณ วันส่งของ และเหตุผลประกอบ แนบเอกสารประกอบ และ submit เพื่อขออนุมัติ ติดตามสถานะและตอบสนองเมื่อถูก send back |
| Department Head / Department Manager | ผู้อนุมัติระดับแรกใน workflow ตรวจสอบ PR ที่มาจากแผนกของตน ตรวจสอบความจำเป็นทางธุรกิจและความสอดคล้องกับงบประมาณ ปรับ approved quantity ถ้าจำเป็น และอนุมัติ, ปฏิเสธ, ส่งกลับ หรือ split-reject บรรทัดเฉพาะ |
| Budget Controller | ตรวจสอบ PR ที่ submit แล้วกับความพร้อมของงบประมาณตาม category และ cost center ที่เกี่ยวข้อง review ผลกระทบของ soft commitment และอนุมัติหรือ escalate PR ที่เกินเกณฑ์ |
| Finance Officer / Finance Manager | ตรวจสอบประเด็นทางการเงินของ PR — สกุลเงิน อัตราแลกเปลี่ยน การจัดการภาษี ความถูกต้องของการคำนวณ — สำหรับ PR มูลค่าสูงเกินเกณฑ์ financial review ที่ตั้งไว้ และเซ็นก่อนส่งให้ procurement แปลงเป็น PO |
| Procurement Officer / Purchaser | รับ PR ที่อนุมัติแล้ว ตรวจสอบการจัดสรรผู้ขายและราคากับ pricelist รวบรวม PR เป็นใบสั่งซื้อ และแปลง PR ที่อนุมัติแล้วเป็น PO บริหารการติดตามผู้ขายเพื่อขอข้อมูลเพิ่มเติม |
| Procurement Manager | กำกับฟังก์ชัน procurement อนุมัติ PR มูลค่าสูงหรือมีความสำคัญเชิงกลยุทธ์ บริหารความสัมพันธ์และการจัดอันดับผู้ขาย และปรับแต่งกฎของ Allocate Vendor |
| System Administrator | ตั้งค่าขั้นตอน workflow เกณฑ์การอนุมัติ กฎ delegation ค่า default ของ PR type รหัสภาษี อัตราแลกเปลี่ยน และการเชื่อมต่อกับโมดูล budget, inventory, vendor และ PO บริหาร role และสิทธิ์ของผู้ใช้ |
| Auditor | สิทธิ์อ่านอย่างเดียวต่อ PR และ activity log เพื่อตรวจสอบ compliance ต่อนโยบาย การ segregation of duties และการปฏิบัติตามกฎ budget control ในช่วงการตรวจสอบตามระยะ |

## 5. โมดูลที่เกี่ยวข้อง

**การไหลข้ามโมดูล:**
- [[purchase-order]] — PR ที่อนุมัติแล้วจะกลายเป็น PO
- [[product]] — บรรทัดของ PR อ้างอิงสินค้าจากแคตตาล็อก
- [[vendor-pricelist]] — preferred vendor และราคาอ้างอิงมาจาก pricelist
- [[inventory]] — ระดับสต๊อกปัจจุบันมักเป็นเหตุผลของการตั้ง PR
- [[templates/purchase-request]] — โครง PR ที่นำกลับมาใช้ใหม่ได้ผ่าน "Create from Template"

**Master configuration:**
- [[master-data/vendor]] — ผู้ขายที่ถูกจัดสรรต่อบรรทัด resolve จาก pricelist
- [[master-data/currency]] — สกุลเงินธุรกรรมและอัตราแลกเปลี่ยนสำหรับ PR หลายสกุลเงิน
- [[master-data/tax-profile]] — รหัสภาษีที่ derive ให้บรรทัดของ PR
- [[master-data/unit]] — หน่วยนับของแต่ละบรรทัด PR
- [[master-data/department]] — แผนกผู้ขอ / cost center ที่อยู่บนส่วนหัวของ PR
- [[system-config/workflow]] — นิยาม workflow อนุมัติแบบหลายระดับสำหรับการอนุญาต PR
- [[system-config/running-code]] — การกำหนดลำดับเลขเอกสาร PR
- [[system-config/dimension]] — มิติเชิงวิเคราะห์ (รหัสงาน/รหัสต้นทุน, โครงการ) ที่บันทึกบน PR
- [[reporting-audit/activity]] — log การเปลี่ยนสถานะ PR และประวัติการอนุมัติสำหรับการตรวจสอบ
- [[reporting-audit/attachment]] — เอกสารประกอบ (ใบเสนอราคา, สเปก) ที่แนบกับ PR
- [[reporting-audit/notification]] — การแจ้งเตือนการอนุมัติ / send-back / reject ที่จัดส่งผ่าน workflow

## 6. แหล่งอ้างอิง

- Concepts: `../carmen/docs/purchase-request-management/`
- Frontend: `../carmen-inventory-frontend/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. หน้าในโมดูลนี้

- [[purchase-request/01-data-model|01 — โมเดลข้อมูล]] — เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum (อิงจาก Prisma)
- [[purchase-request/02-business-rules|02 — กติกาทางธุรกิจ]] — การตรวจสอบความถูกต้อง การคำนวณ การกำหนดสิทธิ์ และกฎการ posting
- [[purchase-request/03-user-flow|03 — User Flow]] — วงจรชีวิตของเอกสารและสารบัญ persona
  - [[purchase-request/03-user-flow-requestor|Requestor]]
  - [[purchase-request/03-user-flow-approver|Approver]]
  - [[purchase-request/03-user-flow-purchaser|Purchaser]]
  - [[purchase-request/03-user-flow-procurement-manager|Procurement Manager]]
  - [[purchase-request/03-user-flow-audit-config|Audit / Config]]
- [[purchase-request/04-test-scenarios|04 — Test Scenarios]] — ขอบเขตของแต่ละ persona, scenario ข้าม persona และ mapping ไปยัง E2E
  - [[purchase-request/04-test-scenarios-requestor|Requestor]]
  - [[purchase-request/04-test-scenarios-approver|Approver]]
  - [[purchase-request/04-test-scenarios-purchaser|Purchaser]]
  - [[purchase-request/04-test-scenarios-procurement-manager|Procurement Manager]]
  - [[purchase-request/04-test-scenarios-audit-config|Audit / Config]]
