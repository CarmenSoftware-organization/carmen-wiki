---
title: ใบขอซื้อ (Purchase Request) — Test Scenarios
description: Test case แยกตาม persona, scenario ข้าม persona และ mapping ไป Playwright สำหรับโมดูล purchase-request
published: true
date: 2026-05-19T23:55:00.000Z
tags: purchase-request, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ (Purchase Request) — Test Scenarios

> **At a Glance**
> **โมดูล:** [purchase-request](/th/inventory/purchase-request) &nbsp;·&nbsp; **scenario รวม:** ~10 ข้าม persona + drill-down ต่อ persona ทุก persona &nbsp;·&nbsp; **Persona ที่ครอบคลุม:** Requestor, Approver, Purchaser, Procurement Manager, Audit / Config
> **ลำดับการรัน:** Audit / Config setup → happy path ของ persona หลัก → scenario ข้าม persona
> **drill-down ของแต่ละ persona อยู่ที่ `04-test-scenarios-<role>.md`**

## 1. ภาพรวม

หน้านี้เป็น **จุดเริ่มต้นภาพรวม** สำหรับชุด test-scenario ของโมดูล `purchase-request` มันแจกแจง persona ที่อยู่ในการทดสอบ, ชี้ไปยังไฟล์ scenario แยกตาม persona สำหรับแต่ละ persona และจับเส้นทาง handoff ข้าม persona ที่ไม่มี persona เดียวเป็นเจ้าของ end-to-end Coverage ครอบคลุมสามมิติ: **functional** (happy path บวก validation error ที่คาดที่จับใน [02-business-rules.md](./02-business-rules.md)), **RBAC / authorization** (แต่ละ persona ถูกจำกัดกับ action ที่อนุญาตที่ stage ของ [03-user-flow.md](./03-user-flow.md) Section 2) และ **edge / negative** (boundary value, pre-condition ที่ขาด, send-back loop, split-reject, escalation และ void ธุรการ)

Scenario ต่อ persona — Happy Path, Permission / Authorization, Validation / Error และ Edge Case — อยู่ในห้าไฟล์ที่ link ใน Section 3 และตาม layout ใน `.specs/templates/04-test-scenarios.md` ตารางข้าม persona ใน Section 4 ด้านล่างรับช่วงที่ขอบเขต handoff ที่ระบุใน [03-user-flow.md](./03-user-flow.md) Section 4 และเชื่อมโยงเข้าด้วยกันเป็นเส้นทาง end-to-end เต็มสำหรับการรัน golden / regression Section 5 ผูก scenario แต่ละตัวกลับไปยัง Playwright spec ใน `../carmen-inventory-frontend-e2e/tests/`

## 2. Persona ที่อยู่ใน scope

- **Requestor**: สร้างและ submit PR; ตอบสนองต่อ send-back โดยแก้และ resubmit; ยกเลิก draft ของตัวเอง
- **Approver**: chain อนุมัติหลายระดับ (Department Head, Budget Controller, Finance Officer / Manager); approve / reject / send-back / split-reject ต่อ stage
- **Purchaser**: validate การจัดสรร vendor และราคา; consolidate และแปลง PR ที่ approved เป็น PO; สามารถ bounce PR กลับไปยัง chain Approver
- **Procurement Manager**: override การอนุมัติมูลค่าสูง; ปรับ vendor ranking และกฎ Allocate Vendor; รับ PR ที่ escalated
- **Audit / Config**: Auditor (review PR และ activity log แบบอ่านอย่างเดียว); System Administrator (ตั้งค่า stage workflow, threshold, กฎ delegation, void ธุรการ)

## 3. ไฟล์ test ต่อ persona

- [Requestor scenarios](./04-test-scenarios-requestor.md)
- [Approver scenarios](./04-test-scenarios-approver.md)
- [Purchaser scenarios](./04-test-scenarios-purchaser.md)
- [Procurement Manager scenarios](./04-test-scenarios-procurement-manager.md)
- [Audit / Config scenarios](./04-test-scenarios-audit-config.md)

## 4. Scenario ข้าม persona / Handoff

| # | Scenario | Persona ตามลำดับ | Pre-condition | สถานะปลายทางที่คาด |
| - | -------- | ----------------- | ------------- | ------------------ |
| X-PR-01 | Happy path เต็ม: สร้าง PR, เดินผ่าน chain อนุมัติสาม stage และแปลงเป็น PO | Requestor → Department Head → Budget Controller → Finance → Purchaser | workflow active ที่มีสาม stage อนุมัติ; header `base_total_amount` ใต้ threshold มูลค่าสูง; ข้อมูล vendor และ pricing พร้อม | PR `completed`, `tb_purchase_order` หนึ่งหรือมากกว่า link กลับมา PR, soft commitment แข็งตัวเป็น PO commitment |
| X-PR-02 | Send-back loop: ผู้อนุมัติส่ง PR กลับ, requestor แก้และ resubmit | Requestor → Approver (stage N) → Requestor → Approver (stage N) → … → Approver สุดท้าย | PR submit แล้วและรออนุมัติที่ stage N; ข้อความเหตุผล send-back valid | PR สุดท้าย `approved` หลังรอบที่สอง; ประวัติการแก้ไขและ comment ผู้อนุมัติเก็บไว้; soft budget commitment ปล่อยตอน send-back แล้วสร้างใหม่ตอน resubmit |
| X-PR-03 | Split-reject: ผู้อนุมัติ reject บางบรรทัด, approve ที่เหลือ, PR ดำเนินต่อกับ subset ที่รอด | Requestor → Approver (stage N) → Approver stage ถัดไป | PR มีอย่างน้อยสองบรรทัด; ผู้อนุมัติที่ reject ให้ข้อความเหตุผลต่อบรรทัด | PR ยังคง `in_progress` พร้อมบรรทัดที่ถูก reject flagged; บรรทัดที่รอดเลื่อนไป stage ถัดไป; บรรทัดที่ reject ถูกตัดจากการแปลง PO ใด ๆ ภายหลัง |
| X-PR-04 | Partial conversion: purchaser แปลงเฉพาะบางบรรทัดที่ approved, ทิ้งที่เหลือไว้ | Requestor → chain Approver เต็ม → Purchaser | PR เป็น `approved` ที่มีหลายบรรทัด; ต้องการเฉพาะ subset ตอนนี้ (เช่น vendor ที่ต้องการไม่พร้อมสำหรับบางบรรทัด) | สร้าง `tb_purchase_order` อย่างน้อยหนึ่งใบสำหรับบรรทัดที่เลือก; header PR ยังคง `approved` สำหรับบรรทัดที่เหลือจนกว่าจะแปลงหรือ aged out |
| X-PR-05 | Escalation: ยอด header เกิน threshold มูลค่าสูงและ route ไปยัง Procurement Manager | Requestor → Department Head → Budget Controller → (escalation) → Procurement Manager | Header `base_total_amount` เกิน threshold ที่ตั้งสำหรับ workflow | PR `approved` เฉพาะหลัง Procurement Manager เซ็น stage escalated; cursor stage บันทึก escalation hop |
| X-PR-06 | เส้นทาง reject: ผู้อนุมัติ reject PR ทันที; workflow ยุติ | Requestor → Approver (stage ใด ๆ) | ผู้อนุมัติที่ reject ให้ข้อความเหตุผล | PR `cancelled`, soft budget commitment ปล่อย, ไม่มี action เพิ่มเติม, comment audit เขียน |
| X-PR-07 | Bounce-back จาก Purchaser: Purchaser ส่ง PR กลับเพื่อ clarification vendor / scope | Requestor → chain Approver เต็ม → Purchaser → Approver (stage N หรือ Requestor) | PR `approved`; Purchaser ไม่สามารถ satisfy vendor หรือ pricing ใน scope | PR กลับเข้า chain (หรือไปยัง Requestor เป็น PR ที่ส่งกลับ) พร้อม comment ของ Purchaser; ขึ้นกับ workflow config สถานะย้ายกลับเป็น `in_progress` หรือ `draft` |
| X-PR-08 | Void ธุรการโดย System Administrator บน PR กลาง flow | Requestor → Approver (stage N) → System Administrator | PR เป็น `in_progress`; admin มีข้อความเหตุผล (เช่น duplicate, compliance) | PR `voided`, soft budget commitment ปล่อย, workflow ยุติ; Auditor อ่านเหตุผล void หลังเหตุการณ์ได้ |
| X-PR-09 | Cancel-own-draft: Requestor ทิ้ง draft ก่อน submit | Requestor เท่านั้น | PR เป็น `draft` และไม่เคย submit | PR `cancelled`; ไม่มีการเลื่อน stage workflow; ไม่มี audit chain นอกเหนือจาก cancel event |
| X-PR-10 | Returned-PR round trip บน golden path Playwright | Requestor → HOD (Department Head) → Requestor → HOD → … | Seed ผ่าน helper `submitPRAsRequestor` + `sendForReviewAsHOD` ใน E2E suite | PR ย้าย Returned → In Progress หลัง Requestor resubmit; badge สถานะและ Workflow History สะท้อน loop เต็ม |

## 5. การ Map E2E Test

Playwright suite ใต้ `../carmen-inventory-frontend-e2e/tests/` มี coverage ของ PR แล้ว Spec persona-journey ใช้ convention การตั้งชื่อ test-case `TC-PR-NNNNNN`; ไฟล์ multi-role ต่อ action (`301-pr.spec.ts`) ครอบคลุม matrix action × role

### Requestor (Creator)
- `../carmen-inventory-frontend-e2e/tests/302-pr-creator-journey.spec.ts` — spec persona-journey สำหรับ Requestor ครอบคลุมแท็บ list / `My Pending`, happy path การสร้าง PR และ validation error, edit / save draft, submit-for-approval, cancel-own-draft และ smoke check ตาม block `TC-PR-050NNN` Map ไปยัง scenario Requestor ใน [04-test-scenarios-requestor.md](./04-test-scenarios-requestor.md)
- `../carmen-inventory-frontend-e2e/tests/311-pr-returned-flow.spec.ts` — flow Returned-PR ข้าม persona (Requestor แก้และ resubmit PR ที่ Approver ส่งกลับ) Map ไปยัง X-PR-02 และ X-PR-10 ใน Section 4 ด้านบนและไปยัง scenario send-back ในไฟล์ Requestor และ Approver

### Approver
- `../carmen-inventory-frontend-e2e/tests/303-pr-approver-journey.spec.ts` — spec persona-journey สำหรับ Approver (HOD หลัก, Finance Controller สำหรับ scope ที่ต่างกัน) ครอบคลุม dashboard My Approvals, edit mode ใน scope ของ approver (approved-qty / item-note / delivery-point แก้ได้, vendor / unit-price read-only), bulk approve / reject / send-for-review / split ผ่าน toolbar Map ไปยัง scenario Approver ใน [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) และไปยัง X-PR-02, X-PR-03, X-PR-06 ใน Section 4 ด้านบน

### Purchaser
- `../carmen-inventory-frontend-e2e/tests/304-pr-purchaser-journey.spec.ts` — spec persona-journey สำหรับ Purchaser ครอบคลุม list scoping ไปยัง stage `Purchase`, edit-mode permission (vendor / unit-price / discount / tax-profile แก้ได้, approved-qty read-only), Auto Allocate vendor, bulk approve / reject / send-for-review / split บวก scenario golden full-flow `TC-PR-070901` Map ไปยัง scenario Purchaser ใน [04-test-scenarios-purchaser.md](./04-test-scenarios-purchaser.md) และไปยัง X-PR-01, X-PR-04, X-PR-07 ใน Section 4 ด้านบน

### Procurement Manager
- ยังไม่มี spec Procurement Manager เฉพาะ เส้นทาง escalation (X-PR-05) และ override มูลค่าสูงถูก exercise บางส่วนผ่าน block `gmTest` ใน `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` **TODO**: เพิ่ม `30X-pr-procurement-manager-journey.spec.ts` เมื่อไฟล์ scenario Procurement Manager publish

### Audit / Config
- ยังไม่มี spec Auditor / System Administrator เฉพาะ — flow config / void / threshold ส่วนใหญ่อยู่ในหน้า admin นอกโมดูล PR เอง **TODO**: เพิ่ม coverage ใต้ `../carmen-inventory-frontend-e2e/tests/` (เช่น การตั้งค่า stage workflow, การ setup threshold, void-with-reason บน PR กลาง flow) เมื่อไฟล์ scenario Audit / Config publish; X-PR-08 จาก Section 4 ด้านบนเป็น candidate ลำดับความสำคัญ

### Shared / Multi-Role
- `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` — coverage ต่อ action × ต่อ role ที่มีก่อน spec persona-journey มีประโยชน์สำหรับ regression permission / authorization ข้าม fixture `requestorTest`, `hodTest`, `fcTest`, `purchaseTest`, `gmTest` และ `noAuthTest`
- `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts` — coverage การสร้าง / edit PR Template (purchase-role + requestor-deny) ใกล้กับไฟล์ scenario Purchaser

## 6. แหล่งอ้างอิง

- `../carmen-inventory-frontend-e2e/` — Playwright test suite (spec executable สำหรับแถวด้านบน)
- `../carmen/docs/purchase-request-management/testing.md` — กลยุทธ์ testing ต้นน้ำ, level unit / integration / E2E / performance / security, test ตัวอย่าง
- `../carmen/docs/purchase-request-management/troubleshooting.md` — mode failure ที่รู้, code error และการแก้ไขที่ขับเคลื่อน sub-section Validation / Error ในแต่ละไฟล์ persona
- หน้าพี่น้อง: [03-user-flow.md](./03-user-flow.md) — บริบท flow โดยเฉพาะ Section 4 (Handoff ข้าม Persona) จากที่ Section 4 ด้านบน derive
- หน้าพี่น้อง: [02-business-rules.md](./02-business-rules.md) — กฎที่ถูก verify โดย test negative ใต้ block Validation / Error ของแต่ละ persona
