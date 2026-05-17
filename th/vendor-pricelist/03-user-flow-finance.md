---
title: รายการราคาผู้ขาย — User Flow — Finance (Vendor Pricelist — User Flow — Finance)
description: Flow ของ Finance ภายในโมดูล vendor-pricelist — การ audit variance เทียบกับ GRN/invoice ที่ post, การ validate สกุลเงิน/FX, การ sign-off multi-currency
published: true
date: 2026-05-17T12:00:00.000Z
tags: vendor-pricelist, user-flow, finance, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย — User Flow — Finance (Vendor Pricelist — User Flow — Finance)

> **At a Glance**
> **Persona:** Finance Officer / AP + Finance Manager &nbsp;·&nbsp; **โมดูล:** [[vendor-pricelist]] &nbsp;·&nbsp; **Workflow stage:** off-path — multi-currency / high-value pre-activation co-approve + post-receipt variance audit &nbsp;·&nbsp; **สิทธิ์สำคัญ:** อ่านข้าม pricelist, co-approve multi-currency / high-value, audit variance GRN / invoice, ไม่มีการเขียน status โดยตรง
> **สิ่งที่ persona นี้ทำ:** Audit variance ราคาเทียบกับ GRN / invoice ที่ post, validate สกุลเงิน / FX และ co-sign การ activate multi-currency หรือ high-value

## 1. Role ในโมดูลนี้

Persona **Finance** ครอบคลุมพนักงาน **Finance Officer / Accounts Payable** ที่ audit variance ราคาระหว่าง pricelist active และบรรทัด GRN / invoice ที่ post, validate การจัดการสกุลเงินและอัตราแลกเปลี่ยน และ reconcile ราคาที่ต่อรอง vs ที่เกิดขึ้นจริง บวก **Finance Manager** ที่ review รายงาน variance และ performance ผู้ขาย, validate ผลกระทบทางการเงินของ pricelist multi-currency และใช้สิทธิ์ co-approval บน pricelist multi-currency หรือ high-value ข้าง Purchasing Manager Finance มี **surface เขียนที่ไม่มีบน pricelist เอง** — `VPL_AUTH_009` คือการอ่านอย่างเดียวข้าม pricelist, campaign และ invitation; Finance ไม่สามารถแก้, approve หรือเปลี่ยนสถานะ pricelist เดียวลำพัง สิทธิ์ **co-approval** ของ Finance Manager บน pricelist multi-currency (`VPL_AUTH_010`) ใช้ผ่าน Finance-stage signoff ใน workflow การ approve แต่การ flip สถานะ `VPL_POST_017` จริงถูกบันทึกเทียบกับ Purchaser / Purchasing Manager; signoff ของ Finance Manager จับเป็น `system` comment ใน `tb_pricelist_comment` Touch point หลักของ Finance คือ **การ audit variance หลังการรับ** — เมื่อการ post GRN / invoice ใน chain procure-to-pay ปลายน้ำ surface gap ราคาเทียบกับ pricelist active (ตาม [[purchase-order/02-business-rules]] § `PO_POST_009` ความล้มเหลว three-way-match หรือ [[vendor-pricelist/02-business-rules]] § `VPL_XMOD_005`) Finance สืบสวนว่า gap คือ (a) ภายในขีดจำกัด tenant — ดำเนินการ post AP ที่ราคาที่วางบิลพร้อม entry purchase-price-variance (PPV), (b) นอกขีดจำกัด — route ความคลาดเคลื่อนกลับไปยัง Purchaser สำหรับ resolution (credit note, amendment หรือ pricelist re-collection) หรือ (c) เกิดจาก FX move บนการ post ข้ามสกุล — บันทึกเป็น FX gain / loss ที่เกิดขึ้นจริง โมดูล PO บันทึก mechanic เชิงปฏิบัติการของ three-way match; หน้านี้ครอบคลุม **ฝั่ง vendor-pricelist** ของ flow เดียวกัน: วิธีที่ Finance อ่าน pricelist active เพื่อ anchor การ audit, สิ่งที่ Finance เขียนกลับไปยังโมดูล pricelist (entry variance, analytics deviation) และวิธีที่ Finance sign off บนการ activate pricelist multi-currency

## 2. จุดเข้าและ Primary Flow

Finance มีสอง flow ในโมดูลนี้ จัดการแยกด้านล่าง

### 2.1. Multi-currency / high-value pre-activation sign-off (Finance Manager)

**จุดเข้า:** Finance Manager ถูกเพิ่มเป็น co-approver บน stage approve ของ workflow สำหรับ pricelist ที่ submit ใด ๆ ที่สกุลเงินต่างจากสกุลเงินฐานของ tenant และมูลค่า aggregate ที่ projected ข้ามขีดจำกัด cross-border-FX OR ที่มูลค่า aggregate ข้ามขีดจำกัด high-value approve โดยไม่คำนึงถึงสกุลเงิน จุดเข้าผ่านการแจ้งเตือน **queue Finance review** เมื่อ pricelist เข้า stage นี้

**Primary flow (4 step):**

1. **เปิด pricelist จาก queue review** หน้าจอแสดง **Header** (vendor, สกุลเงิน, วัน validity, วิธีการ submission), **Detail Rows** (product, unit, MOQ, price-without-tax, tax, lead-time), **Validation Panel** (output engine ที่เขียนไปยัง `tb_pricelist.info.validation_results` + `quality_score` ตาม `VPL_CALC_006`) และ **Activity Log**
2. **ตรวจสอบความถูกต้องทางการเงิน** ยืนยัน `currency_id` ตรงกับสกุลเงินที่ vendor มีสัญญา (หรือทางเลือกที่ tenant-approve สำหรับ vendor dual-currency); ตรวจสอบว่าแหล่งอัตรา FX ของ tenant สามารถ quote `currency_id ↔ tenant_base_currency` สำหรับ validity window ของ pricelist; เช็คว่าอัตราภาษีบนแถว detail reconcile กับการลงทะเบียนภาษีของ vendor และ tax profile ของสินค้าตาม `VPL_CALC_001`–`VPL_CALC_002`
3. **Spot-check ผลกระทบทางการเงิน aggregate** คำนวณ spend ที่ project = `Σ (effective_unit_price_per_base_uom × historical_demand_by_product)` เหนือ validity window; ตรวจสอบว่า projection สอดคล้องกับเหตุผลขีดจำกัด high-value ของ Purchasing Manager; ทำให้แน่ใจว่าไม่มีบรรทัดเดียว carry outlier order-of-magnitude ที่ validator ไม่จับ
4. **Sign off หรือ send-back**
   - **Sign off:** post `system` comment Finance signoff บน `tb_pricelist_comment` Workflow ดำเนินไป; ถ้า Purchaser / Purchasing Manager sign off แล้ว `VPL_POST_017` fire และ pricelist activate มิฉะนั้น workflow ดำเนินต่อรอฝั่ง Purchaser
   - **Send-back:** post การคัดค้านของ Finance พร้อมข้อความเหตุผล Pricelist return ไป `draft + submitted_at = NULL` ตาม `VPL_POST_018`; vendor ถูกแจ้งสำหรับ resubmission พร้อมเหตุผลฝั่ง Finance ที่ Purchaser เห็นได้ Send-back เป็น veto แข็งบนการ activate multi-currency; Purchaser ไม่สามารถ override Finance บน gate นี้

### 2.2. Post-receipt variance audit (Finance Officer / AP)

**จุดเข้า:** การ post GRN หรือ three-way-match ใน chain PO / AP ปลายน้ำ flag variance ราคาเทียบกับ pricelist active Event variance surface ใน dashboard **Pricelist Variance** (รายงานฝั่ง Finance join `tb_pricelist_detail` ไปยัง `tb_good_received_note_detail` ที่ post และบันทึก AP invoice) แต่ละแถวแสดง vendor, สินค้า, ราคา pricelist, ราคา GRN / invoice, ขนาด (สัมบูรณ์และเปอร์เซ็นต์) และ id PO / GRN / invoice ที่ link

**Primary flow (6 step):**

1. **เปิด dashboard variance** กรองโดย vendor, สินค้า, period, ขนาด หรือการอ้างอิง PO / GRN แต่ละแถว drill เข้า chain ธุรกรรมที่อยู่เบื้องหลัง
2. **Drill เข้า variance หนึ่ง** เปิดแถว variance; detail view แสดง **แถว pricelist active** (`tb_pricelist_detail` พร้อมราคา, MOQ, หน่วย, validity), **บรรทัด GRN** (qty รับ, ราคาต่อหน่วย GRN, actor และ timestamp การ post GRN) และ **บรรทัด invoice** (เลข invoice vendor, qty invoice, ราคาต่อหน่วย invoice, ผล three-way-match)
3. **จัดประเภท variance** สามประเภท:
   - **ภายในขีดจำกัด (auto-pass ฝั่ง PO three-way-match):** variance อยู่ภายใน band tolerance ราคาของ tenant, การ match PO ผ่าน (ตาม [[purchase-order/02-business-rules]] § `PO_POST_008`) และ AP ถูก post ที่ราคาที่วางบิลพร้อม entry PPV Role ของ Finance Officer ที่นี่คือ review reconciliation เท่านั้น; ไม่มี action บน pricelist
   - **นอกขีดจำกัด, vendor over-bill:** การ match PO ล้มเหลว (ตาม `PO_POST_009`); invoice อยู่ในข้อพิพาท; Finance Officer ดำเนินการขอ credit note จาก vendor ผ่าน Purchaser ไม่มี action บน pricelist เองยกเว้น over-billing เปิดเผย pattern ระบบ (vendor / สินค้าหลายตัว) ในกรณีนั้น Finance escalate ไปยัง Purchasing Manager สำหรับ pricelist re-collection
   - **นอกขีดจำกัด, pricelist out-of-date:** ราคา pricelist ไม่สะท้อนความจริงของตลาดอีกต่อไป (เช่น commodity spike) และ vendor วางบิลที่อัตราตลาดใหม่ Finance Officer file memo variance, route ไปยัง Purchaser และแนะนำการ inactivate + re-collect pricelist Finance ไม่ inactivate โดยตรง (ไม่มีสิทธิ์เขียนตาม `VPL_AUTH_009`); Purchaser execute `VPL_POST_019` หลัง review
4. **ตรวจสอบการจัดการสกุลเงิน / FX** สำหรับ invoice ข้ามสกุลเงิน ยืนยันว่าอัตรา FX ที่ใช้ตอน post ตรงกับนโยบาย FX ของ tenant ที่วัน invoice; ยืนยันว่า entry FX gain / loss บน AP จัดประเภทถูกต้อง ค่า Pricelist ที่เก็บในสกุลเงิน vendor ตาม `VPL_CALC_005` ไม่เคย mutate สำหรับ FX — ผลกระทบ FX อยู่ฝั่งการ post AP
5. **เขียนกลับไปยัง pricelist** เมื่อการจัดประเภท variance เสร็จ Finance เขียน `system` comment บน `tb_pricelist_comment` (และบน `tb_pricelist_detail_comment` ที่ได้รับผลกระทบ) อ้างอิง id GRN / invoice, ขนาด variance และการจัดประเภท นี่ป้อน rollup analytics pricelist-deviation ที่ logic preferred-vendor บรรทัด PR ปลายน้ำ ([[vendor-pricelist/02-business-rules]] § `VPL_XMOD_001`) และ scoring performance vendor ของ Purchasing Manager อ่าน
6. **ปิดเคส variance** เมื่อการจัดประเภทถูกบันทึกและ action ที่ต้องการ (การติดตาม credit note, คำขอ pricelist re-collection) ถูก handoff แถว variance drop จาก dashboard เปิดของ Finance audit log คงไฟล์เคสสำหรับ chain audit ของ Auditor

## 3. สาขาการตัดสินใจ

- **Co-approval แยกระหว่าง Finance Manager และ Purchasing Manager** บน pricelist multi-currency ที่เป็น high-value ด้วย ทั้ง Finance Manager (`VPL_AUTH_010`) และ Purchasing Manager (`VPL_AUTH_005`) ต้อง sign off ลำดับไม่เข้มงวด — ใครก่อนก็ได้ — แต่ `VPL_POST_017` fire เฉพาะเมื่อมีทั้งสอง `system` comment signoff ถ้า Finance Manager sign off แต่ Purchasing Manager reject reject ชนะและ pricelist return ไป `draft + submitted_at = NULL` สถานการณ์ย้อนกลับเป็นสมมาตร
- **Finance Manager send back บนการละเมิดนโยบาย FX** เมื่อ review ของ Finance Manager พบว่า `currency_id` ของ pricelist ไม่อยู่ในรายการสกุลเงินที่ tenant อนุญาต หรือแหล่งอัตรา FX ไม่สามารถ quote คู่สกุลเงินสำหรับ validity window (เช่น สกุลเงินที่ trade บางที่ไม่มีแหล่งอัตรา real-time) Finance veto การ activate ผ่าน `VPL_POST_018` Vendor ถูกแจ้งให้ resubmit ในสกุลเงินที่ approve นี่เป็น veto แข็ง — Purchaser ไม่สามารถทำงาน around มัน
- **Variance เปิดเผย vendor over-billing เป็นระบบ** เมื่อ audit variance ของ Finance Officer แสดงว่า vendor เดียวกัน over-bill ซ้ำ ๆ ข้าม triplet PO / GRN / invoice หลายตัว pattern escalate ไปยัง Purchasing Manager Manager ตัดสินใจว่าจะ (a) inactivate pricelist active และ re-collect, (b) trigger การ review สัญญากับ vendor (out-of-band) หรือ (c) revoke สถานะ preferred-vendor ของ vendor โดย toggle `is_preferred` flag ทั้งหมดเป็น off บนแถว pricelist active ของ vendor การตัดสินใจถูกบันทึกบน profile performance ของ vendor และป้อน business-rule engine
- **Variance เปิดเผย pricelist out-of-date เนื่องจาก market move** Finance Officer route เคสไปยัง Purchaser พร้อมการแนะนำให้ inactivate pricelist และ launch campaign ใหม่ Purchaser execute `VPL_POST_019` และติดตามด้วย campaign ใหม่ตามเส้น flow Purchaser Step 4 Cohort PR / PO ปลายน้ำที่อ้างอิง pricelist เก่าคงอยู่ภายใต้ snapshot semantic; PR ใหม่ default จาก pricelist ใดก็ตามที่ active ที่เวลาสร้าง PR (อาจเป็น pricelist fallback จาก vendor อื่นหรือ `pricelist_type = manual_input` ตาม `VPL_XMOD_002` ถ้า coverage หายแล้ว)
- **Variance attribute ไป FX move บนการ post ข้ามสกุลเงิน** เมื่อ variance ถูกอธิบายทั้งหมดโดยความแตกต่างระหว่างอัตรา FX snapshot PO และอัตรา FX วัน invoice pricelist เองไม่ผิด — FX gain / loss ที่เกิดขึ้นจริง post บน AP และ pricelist คง active Finance Officer บันทึกการจัดประเภท FX-only ในไฟล์เคส variance; ไม่ต้องการ handoff ไปยัง Purchaser ยกเว้นการเปิดรับ FX สะสมข้ามขีดจำกัด tenant (ในกรณีนั้น Finance Manager review นโยบาย currency-hedging out-of-band)
- **ไม่มี pricelist active ที่เวลาการ post GRN / invoice** เมื่อ three-way-match ล้มเหลวเพราะ PR ต้นทางถูกสร้างด้วย `pricelist_type = manual_input` (`VPL_XMOD_002`) และไม่มี anchor pricelist สำหรับ variance check Finance Officer route เคสตรงไปยัง Purchasing Manager เพื่อ (a) launch campaign เพื่อเติม gap coverage และ (b) ตัดสินว่าการขาด anchor pricelist warrant การ post AP non-policy ที่ต้องการ Manager override ฝั่ง AP โมดูล pricelist บันทึก gap coverage เป็น `system` comment บน registry pricelist ของ vendor ที่ได้รับผลกระทบ

## 4. จุดออก / Handoff

การมีส่วนร่วมของ Finance บน pricelist หรือเคส variance ที่กำหนดจบที่หนึ่งในจุดที่บันทึก; สถานะเอกสารที่แต่ละ handoff anchor กับ lifecycle ใน [03-user-flow.md](./03-user-flow.md) § 2

- **Finance Manager pre-activation sign-off** — Finance Manager sign off บน pricelist multi-currency / high-value; handoff ไปยัง **Purchaser / Purchasing Manager** สำหรับการคลิก activate สุดท้าย (หรือถ้าพวกเขา sign off แล้ว `VPL_POST_017` fire ทันทีและ pricelist activate) สถานะเอกสารที่ handoff: pricelist `draft + submitted_at IS NOT NULL`; `system` comment signoff Finance อยู่บน activity log ของ pricelist
- **Finance Manager pre-activation send-back** — Finance Manager veto การ activate; handoff ไปยัง **Vendor** (ผ่าน email reject ภายใต้ token ต้นฉบับ ตรงเหมือน `VPL_POST_018` สำหรับ reject ใด ๆ) และ **Purchaser** (การแจ้งเตือน) สถานะเอกสารที่ handoff: pricelist `draft + submitted_at = NULL`; `system` comment การคัดค้านของ Finance จับเหตุผลนโยบาย FX / multi-currency
- **Variance จัดประเภท within-tolerance** — ไม่มี action บน pricelist; แถว variance drop จาก dashboard เปิด; สถานะเอกสารบน pricelist ไม่เปลี่ยน (`active`); ไฟล์เคสคงไว้สำหรับ Auditor
- **Variance จัดประเภท vendor over-billed** — Finance Officer handoff ไปยัง **Purchaser** เพื่อดำเนินการ credit note กับ vendor; สถานะเอกสารบน pricelist ไม่เปลี่ยน (`active`); `system` comment variance เขียนสำหรับ analytics pricelist-deviation
- **Variance จัดประเภท pricelist out-of-date** — Finance Officer handoff ไปยัง **Purchasing Manager** พร้อมการแนะนำให้ inactivate; Manager execute `VPL_POST_019` (หรือ delegate ไปยัง Purchaser สำหรับ follow-up) สถานะเอกสารที่ handoff: pricelist `active`; การตัดสินใจของ Manager ขับ state ครั้งต่อไป
- **Variance จัดประเภท FX-only** — ไม่มี action บน pricelist; ฝั่ง AP-posting carry FX gain / loss ที่เกิดขึ้นจริง; สถานะเอกสารบน pricelist ไม่เปลี่ยน (`active`); `system` comment FX เขียน
- **ไม่มี coverage pricelist** — Finance Officer handoff ไปยัง **Purchasing Manager** สำหรับ launch campaign ใหม่; สถานะเอกสารบนโมดูล pricelist: gap coverage บันทึกเทียบกับ vendor / registry สินค้า; pricelist `(none)` สำหรับสินค้าที่ได้รับผลกระทบจนกว่า campaign ใหม่จะ complete

ในทุกกรณี `status` ของ pricelist เปลี่ยน (ถ้าเลย) โดย Purchaser / Purchasing Manager เท่านั้น — role ของ Finance คือการ anchor การ audit, post entry ฝั่ง AP และแนะนำ action ฝั่ง pricelist

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — lifecycle ทั่วโลกและตาราง handoff ข้าม persona; แถว Finance อยู่ที่ gate co-approval multi-currency และที่การสืบสวน variance post-GRN ทุกครั้ง
- Authorization: [02-business-rules.md](./02-business-rules.md) § 4 — `VPL_AUTH_009` (Finance Officer อ่านอย่างเดียว), `VPL_AUTH_010` (Finance Manager co-approval), `VPL_AUTH_014` (การแยกหน้าที่)
- กติกา Posting: [02-business-rules.md](./02-business-rules.md) § 5 — `VPL_POST_017` (การ activate โดย Purchaser, มีเงื่อนไขบน signoff Finance Manager สำหรับ multi-currency), `VPL_POST_018` (การ reject รวม veto Finance), `VPL_POST_019` (การ inactivate, execute โดย Purchaser ตามการแนะนำของ Finance)
- กติกา Calculation: [02-business-rules.md](./02-business-rules.md) § 3 — `VPL_CALC_001`–`VPL_CALC_002` (การแยกภาษีที่ Finance ตรวจสอบ), `VPL_CALC_005` (การแสดงผล multi-currency — pricelist ไม่เคย FX-mutate), `VPL_CALC_006` (quality score ที่ Finance review)
- กติกาข้ามโมดูล: [02-business-rules.md](./02-business-rules.md) § 6 — `VPL_XMOD_005` (price-variance check ของ GRN เทียบกับ pricelist active — จุดเข้าหลัก post-receipt ของ Finance), `VPL_XMOD_002` (การขาด coverage pricelist บนการป้อน manual บรรทัด PR — การ refer gap coverage ของ Finance), `VPL_XMOD_008` (ความถูกต้องของ currency master ตรวจสอบที่ Finance pre-activation sign-off)
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ภายในที่ activate / inactivate pricelist ตามการแนะนำของ Finance; ดำเนินการ credit note ตามคำขอของ Finance
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — Auditor บริโภคไฟล์เคส variance ของ Finance ใน chain audit; Sysadmin ตั้งค่าแหล่งอัตรา FX และ tax-profile master data ที่ Finance ตรวจสอบ
- Sibling: [03-user-flow-vendor.md](./03-user-flow-vendor.md) — counterparty ภายนอกที่ loop reject-resubmission ปิดกลับผ่าน Finance review เดียวกันในรอบครั้งต่อไปสำหรับเคส multi-currency
- Cross-link: [[purchase-order]] — ผู้บริโภคปลายน้ำหลักที่ Finance รัน three-way match ที่ขับการสืบสวน variance กลับเข้าโมดูลนี้ `PO_POST_008` / `PO_POST_009` เป็น counterpart เชิงปฏิบัติการของ `VPL_XMOD_005`
- Cross-link: [[good-receive-note]] — แหล่ง variance ต้นน้ำที่การ post GRN เปรียบเทียบกับ pricelist active ครั้งแรก
- Cross-link: [[purchase-request]] — การ refer gap missing-pricelist coverage `VPL_XMOD_002` ต้นกำเนิดที่การสร้างบรรทัด PR
- `../carmen/docs/vendor-pricelist-management/design.md` — Phase 6 (Data Validation & Quality Control) และชั้น analytics / reporting ที่ Finance อ่าน
- `../carmen/docs/vendor-pricelist-management/price-assignment-workflow-documentation.md` — การจัดประเภท variance และการ link PPV ฝั่ง AP-posting
