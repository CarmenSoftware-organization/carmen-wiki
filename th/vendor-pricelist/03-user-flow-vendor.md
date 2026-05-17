---
title: รายการราคาผู้ขาย — User Flow — Vendor (Vendor Pricelist — User Flow — Vendor)
description: Flow ของ Vendor ภายในโมดูล vendor-pricelist — external party ที่มีการเข้าถึง portal-token (ไม่มี Carmen system login)
published: true
date: 2026-05-17T12:00:00.000Z
tags: vendor-pricelist, user-flow, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย — User Flow — Vendor (Vendor Pricelist — User Flow — Vendor)

> **At a Glance**
> **Persona:** Vendor (external — portal session ที่ authenticate ด้วย token, ไม่มี Carmen login) &nbsp;·&nbsp; **โมดูล:** [[vendor-pricelist]] &nbsp;·&nbsp; **Workflow stage:** pricelist (none) → draft → submitted (จากนั้น Purchaser approve / reject) &nbsp;·&nbsp; **สิทธิ์สำคัญ:** การเข้า portal scope ด้วย token — ป้อน / upload ราคา, ตั้งสกุลเงิน / MOQ, save draft, submit
> **สิ่งที่ persona นี้ทำ:** เข้าถึง portal ต่อ vendor ผ่าน token cryptographic, ป้อนหรือ upload ราคาตาม template และ submit สำหรับ Purchaser review

## 1. Role ในโมดูลนี้

**Vendor** เป็น **external party ที่ไม่มี Carmen system login** ไม่เหมือนกับ persona external ส่วนใหญ่ (เช่น vendor บนโมดูล [[purchase-order]] ที่ติดต่อทั้งหมดผ่าน email / EDI) โมดูล vendor-pricelist ให้ vendor มี **portal session ที่ authenticate ด้วย token** — ที่เดียวที่ external party ขับ system state โดยตรงภายในระบบ Carmen Vendor ได้รับ email invitation จาก campaign ที่ Purchaser launch, navigate ไปยัง URL portal ต่อ vendor ฝัง `tb_request_for_pricing_detail.pricelist_url_token` cryptographic ([[vendor-pricelist/01-data-model]] § 2.6), ป้อนหรือ upload ราคาสำหรับสินค้าที่ template ระบุ, เลือกสกุลเงินการ submission, จัด MOQ tier พร้อมหน่วย, save draft (auto-save ทุก ~30 วินาที) และสุดท้ายคลิก Submit — ที่จุดนั้น `tb_pricelist.submitted_at` ถูกเขียนและไฟล์ route ไปยัง Purchaser สำหรับ review Session ของ vendor gate โดย `VPL_AUTH_007` (token-validity, IP allowlist ถ้าตั้งค่า, session limit) และ `VPL_AUTH_008` (สกุลเงินต้องอยู่ในรายการสกุลเงินที่ tenant อนุญาต; conversion factor หน่วยอ่านจาก master data ไม่ใช่ vendor-supplied) Vendor ไม่เคยปฏิบัติการ `tb_pricelist.status` โดยตรงเกินกว่า implicit `(none) → draft` และ action submit; การ approve, reject, inactivation และ expiry ทั้งหมดขับโดย persona ภายในหรือ cron job เพราะ surface หลักของ vendor คือ portal session เดียวที่มีสาขาการตัดสินใจจำกัดและไม่มี matrix RBAC ใน-ระบบที่จะแจกแจง ไฟล์นี้สั้นกว่าไฟล์ Purchaser โดยตั้งใจ — เทียบขนาดได้กับไฟล์ Vendor external ใน [[purchase-order/03-user-flow-vendor]]

## 2. จุดเข้าและ Primary Flow

**จุดเข้า:** Vendor ได้รับ email invitation (หรือ reminder ครั้งเดียวตาม schedule reminder ของ campaign) Email carry URL portal ต่อ vendor ฝัง `pricelist_url_token`, วัน window ของ campaign และข้อความ custom การคลิก link เปิด portal; token แลกเป็น session cookie ที่อยู่ภายใต้ portal-token policy ของ tenant ([[vendor-pricelist/02-business-rules]] § `VPL_AUTH_007`)

**Primary flow (happy path — การป้อน online):**

1. **เปิด portal ผ่าน invitation link** Portal render หน้า welcome พร้อมรายละเอียด invitation, countdown deadline (`VPL_CALC_007`), indicator ความคืบหน้า และตัวเลือก submission สามตัว: **Direct online entry**, **Download Excel template and upload**, **Download Excel template and email to purchasing staff** `system` comment บันทึกบน `tb_request_for_pricing_detail_comment` จับ timestamp first-access; สถานะ invitation ที่ derive ย้ายจาก `pending` ไป `in-progress` (`VPL_POST_011`)
2. **เลือกสกุลเงิน submission** Currency picker เสนอสกุลเงินที่ tenant อนุญาต; ค่าที่เลือกเขียนไป `tb_pricelist.currency_id` ตอน save ครั้งแรก (`VPL_AUTH_008`) การเลือกสกุลเงินใช้กับ **ทุก** บรรทัดบน submission นี้; ไม่มีสกุลเงินต่อบรรทัด
3. **เลือกโหมด submission**
   - **การป้อน online:** portal render รายการสินค้าของ template เป็น single-page editable form แต่ละแถวสินค้าแสดง inventory unit, default order unit จาก template และปุ่ม `[+]` เพื่อเพิ่ม MOQ tier เพิ่มเติม (`VPL_VAL_006`)
   - **Excel upload:** คลิก **Download template**, กรอกออฟไลน์ และ drag-and-drop workbook กลับมาที่ portal Portal parse workbook (`submission_method = portal`) เป็นแถว `tb_pricelist_detail`
   - **Email submission:** คลิก **Download template**, กรอกออฟไลน์, email ไปยัง staff ฝ่ายจัดซื้อ Purchaser upload ในนาม vendor (`submission_method = email`, `VPL_AUTH_003`) — session portal ของ vendor สามารถปิด; ไม่ต้องการ action vendor เพิ่มยกเว้นการตอบ email reject
4. **ป้อนราคาต่อสินค้าต่อ MOQ tier (เส้นทาง online-entry)** สำหรับแต่ละสินค้า ป้อน `price_without_tax`, `tax_rate` (เมื่อมีผลใช้กับ tax profile ของ vendor), `lead_time_days` และโน้ตต่อแถว ใช้ `[+]` เพื่อเพิ่มแถว MOQ-tier สำหรับการตั้งราคา bulk (เช่น MOQ 1 @ ฿12.50, MOQ 50 @ ฿10.50, MOQ 100 @ ฿9.75) Portal auto-sort tier และเตือน inline (`VPL_VAL_020`) ถ้า MOQ ที่สูงกว่า carry ราคาต่อหน่วยที่สูงกว่า MOQ ที่ต่ำกว่า feedback validation แบบ real-time flag ฟิลด์ที่ขาดหรือค่านอกช่วง
5. **Save และ resume ข้าม session (auto-save)** Portal auto-save pricelist in-progress ทุก ~30 วินาทีและที่ field-blur Vendor สามารถปิด browser และกลับมาภายหลังผ่าน invitation link เดียวกันตราบเท่าที่ (a) campaign `end_date` ยังไม่ผ่าน, (b) token ไม่ถูก revoke และ (c) session limit (default 5 พร้อมกัน) ไม่ถูกเกิน `tb_pricelist.status` ยัง `draft` ตลอด; `submitted_at IS NULL`
6. **Review panel validation ก่อน submit** Portal surface output การรันของ validator — เปอร์เซ็นต์ความสมบูรณ์, ฟิลด์ที่ขาด, อัตราการผ่าน business-rule และ `quality_score` ที่คำนวณ (`VPL_CALC_006`) ข้อความ error inline พร้อมคำแนะนำการแก้ปรากฏข้างแต่ละแถวที่ได้รับผลกระทบ
7. **คลิก Submit** Validator รัน full pass (`VPL_VAL_018`–`VPL_VAL_023`) ตอนสำเร็จ `tb_pricelist.submitted_at = now()`, `submission_method` finalise, quality score เขียนไป `info` และ `system` comment append ใน `tb_pricelist_comment` Portal render หน้ายืนยันพร้อมหมายเลขอ้างอิง submission และ timeline review ที่คาด; email ยืนยันอัตโนมัติ dispatch ไปยัง contact ของ vendor สถานะ invitation ย้ายไป `submitted` (`VPL_POST_012`)
8. **รอ review ของ purchaser** ไม่ต้องการ action เพิ่มจาก vendor ยกเว้น Purchaser reject submission (ดู สาขาการตัดสินใจ)

## 3. สาขาการตัดสินใจ

- **ถ้า vendor ต้องการอัปเดตราคาหลัง submit แต่ก่อนการ approve** หน้า portal ของ pricelist ที่ submit แสดง action **Recall and edit** ขณะ `tb_pricelist.status = draft` และ `submitted_at IS NOT NULL` Vendor คลิก Recall; `submitted_at` reset เป็น `NULL`, pricelist กลับไป surface draft ที่แก้ได้ และ `system` comment บันทึก recall Vendor แก้และ resubmit Purchaser ถูกแจ้งว่า submission ถูกถอน และ re-submit; timeline review เริ่มใหม่
- **ถ้า submission ของ vendor ถูก reject โดย Purchaser** (`VPL_POST_018`): vendor ได้รับ email reject ที่มีข้อความเหตุผลและ URL portal เดียวกัน (token ต้นฉบับยังถูกต้องจนกว่า campaign `end_date`) Vendor เปิด portal, เห็น `system` rejection comment บน pricelist, ทำการแก้ที่ต้องการ และคลิก Submit อีกครั้ง วงจรกลับไปที่ Step 7 ข้างต้น
- **ถ้า vendor ต้องการใช้วิธีการ submission ที่ต่างกัน mid-flight** (เช่น เริ่ม online แต่ต้องการ upload Excel แทน): portal อนุญาตการ switch ที่ใดก็ตามก่อน submit — คลิก **Switch to Excel upload** ทิ้ง entry online in-progress (พร้อมการยืนยัน) และ render surface upload การ switch กลับก็อนุญาต `submission_method` ที่เลือก finalise ที่ moment ของการคลิก Submit
- **ถ้า portal token ถูก revoke หรือ session limit เกิน** Portal return `401 — token revoked` (ตาม `VPL_AUTH_015`) หรือ `429 — session limit exceeded` Vendor ไม่สามารถกู้ session ผ่าน link ต้นฉบับ; ต้องติดต่อ staff ฝ่ายจัดซื้อ (email ผู้ติดต่อบน invitation) เพื่อรับ invitation ใหม่พร้อม token ใหม่ (ภายใต้ `VPL_AUTH_002`) หรือออกการ bypass ครั้งเดียว Auto-save draft รักษาฝั่ง server; ถ้าออก invitation ใหม่ pricelist ใหม่เริ่มว่าง (draft จาก token ที่ revoke ไม่ migrate อัตโนมัติ — รักษาสำหรับ audit ของ Purchaser เท่านั้น)
- **ถ้า vendor ไม่สามารถตรง deadline** Vendor สามารถ email หรือโทรไปยัง contact จัดซื้อเพื่อขอการขยาย campaign (การปรับ window ของ `VPL_POST_006`) หรือการ submission ภายหลังครั้งเดียวผ่านเส้นทาง email (`VPL_AUTH_003`) Portal เองไม่แสดงการขยายแบบ self-service; คำขอจัดการโดย Purchaser ผ่านหน้าจอการแก้ campaign เลย `end_date` invitation auto-expire (`VPL_POST_014`), token ถูก revoke และ pricelist draft รักษาบน Carmen แต่ไม่สามารถเข้าถึงโดย vendor

## 4. จุดออก / Handoff

การมีส่วนร่วมของ vendor ใน invitation ที่กำหนดจบที่หนึ่งในสามจุด; สถานะเอกสารที่ handoff anchor กับ lifecycle ใน [03-user-flow.md](./03-user-flow.md) § 2

- **Submit → purchaser review** Vendor คลิก Submit; `tb_pricelist.submitted_at IS NOT NULL`; สถานะ invitation ย้ายไป `submitted` Handoff ไปยัง **Purchaser** สำหรับ review และ approve / reject สถานะเอกสารที่ handoff: pricelist `draft + submitted_at`; invitation `submitted` การมีส่วนร่วมตามมาของ vendor (ถ้ามี) trigger โดย email reject (กลับไปที่ portal ภายใต้ token ต้นฉบับ)
- **Submit ผ่านเส้นทาง email → staff จัดซื้อ** Vendor return Excel ทาง email; Purchaser upload ในนาม vendor สถานะเอกสารที่ handoff: pricelist `draft + submitted_at` เขียนโดย staff; invitation `submitted`; `submission_method = email` Session portal ของ vendor ถ้าเปิด ตอนนี้ supersede — pricelist ที่ email-upload คือ submission canonical
- **Token หมดอายุหรือถูก revoke** Campaign `end_date` ผ่านโดยไม่มี submission หรือ Sysadmin / Manager revoke token สถานะ invitation ย้ายไป `expired`; การเข้า portal ของ vendor terminate สถานะเอกสารที่ handoff: pricelist `(none)` หรือ `draft` (รักษาสำหรับ audit); invitation `expired` Handoff เป็น **out-of-band** — ความสัมพันธ์ของ vendor ต่อเฉพาะผ่าน campaign ในอนาคตที่ออกโดย Purchaser

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — lifecycle ทั่วโลกและตาราง handoff ข้าม persona; แถว Vendor อยู่ระหว่าง launch invitation ของ Purchaser และ review การ approve ของ Purchaser
- Authorization: [02-business-rules.md](./02-business-rules.md) § 4 — `VPL_AUTH_007` (การเข้า portal ผ่าน token), `VPL_AUTH_008` (การเลือกสกุลเงินและหน่วย), `VPL_AUTH_014` (การแยกหน้าที่ — Vendor ≠ Purchaser), `VPL_AUTH_015` (การ revoke token)
- กติกา Posting: [02-business-rules.md](./02-business-rules.md) § 5 — `VPL_POST_010`–`VPL_POST_014` (lifecycle invitation); `VPL_POST_015`–`VPL_POST_016` (การเปลี่ยน pricelist ที่ขับโดย vendor)
- กติกา Validation: [02-business-rules.md](./02-business-rules.md) § 2 — `VPL_VAL_018`–`VPL_VAL_023` (การ validate ระดับบรรทัดที่ vendor trigger บน save และ submit), `VPL_VAL_020` (MOQ-tier non-increasing check ของการตั้งราคา surface inline บน portal)
- กติกา Calculation: [02-business-rules.md](./02-business-rules.md) § 3 — `VPL_CALC_001`–`VPL_CALC_003` (การแยกราคาบรรทัดที่แสดงต่อ vendor), `VPL_CALC_007` (countdown deadline บน portal)
- `../carmen/docs/vendor-pricelist-management/design.md` § Phase 5 (Vendor Portal Price Submission) — แหล่ง carmen/docs หลักสำหรับ UX ของ portal ที่อธิบายใน Section 2 ข้างต้น
- `../carmen/docs/vendor-pricelist-management/VENDOR_PORTAL_ENHANCEMENT_SUMMARY.md` — แคตตาล็อก feature ของ portal ครอบคลุม auto-save, การ submission แบบ multi-format, การ validate แบบ real-time และการติดตามความคืบหน้า
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ภายในที่ launch campaign, review submission ของ vendor และ approve / reject
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — System Administrator ที่ตั้งค่านโยบาย portal-token (`VPL_AUTH_007`) และอาจ revoke token ของ vendor (`VPL_AUTH_015`)
- Cross-link: [[product]] — ทุกบรรทัดบน submission ของ vendor อ้างอิงสินค้าบน template
