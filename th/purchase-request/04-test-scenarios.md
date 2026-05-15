---
title: ใบขอซื้อ — กรณีทดสอบ
description: กรณีทดสอบแยกตาม persona, กรณีข้าม persona, และการเชื่อมโยงกับ Playwright สำหรับโมดูล purchase-request
published: true
date: 2026-05-15T09:00:00.000Z
tags: purchase-request, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ — กรณีทดสอบ

## 1. ภาพรวม

หน้านี้เป็น **จุดเริ่มต้นภาพรวม** ของชุดเอกสารกรณีทดสอบสำหรับโมดูล `purchase-request` จุดมุ่งหมายคือระบุ persona ที่อยู่ในขอบเขตการทดสอบ, ชี้ไปยังไฟล์กรณีทดสอบแยกตาม persona ในแต่ละบทบาท และเก็บเส้นทาง handoff ข้าม persona ที่ไม่มี persona ใด persona เดียวรับผิดชอบครบทั้ง flow ขอบเขตการทดสอบครอบคลุมสามมิติ: **เชิงฟังก์ชัน** (happy path บวกกับ validation error ที่กำหนดไว้ใน [02-business-rules.md](./02-business-rules.md)), **RBAC / authorization** (แต่ละ persona ถูกจำกัดให้ทำ action ตามที่ stage ของตัวเองอนุญาตใน [03-user-flow.md](./03-user-flow.th.md) หัวข้อ 2) และ **edge / negative** (ค่าขอบ, ขาด pre-condition, send-back loop, split-reject, การ escalate และการ void เชิงบริหาร)

กรณีทดสอบแยกตาม persona — Happy Path, Permission / Authorization, Validation / Error และ Edge Cases — อยู่ในไฟล์ทั้งห้าที่ลิงก์ในหัวข้อ 3 และยึดรูปแบบจาก `.specs/templates/04-test-scenarios.md` ตารางข้าม persona ในหัวข้อ 4 ด้านล่างต่อยอดจากจุด handoff ที่ระบุไว้ใน [03-user-flow.md](./03-user-flow.th.md) หัวข้อ 4 แล้วร้อยเป็นเส้นทาง end-to-end เต็มที่เหมาะกับการรันแบบ golden / regression หัวข้อ 5 เชื่อมแต่ละ scenario กลับไปยัง Playwright spec ใน `../carmen-inventory-frontend-e2e/tests/`

## 2. Personas ที่อยู่ในขอบเขต

- **Requestor** (ผู้ร้องขอ): สร้างและส่ง PR; ตอบสนองต่อการส่งกลับด้วยการแก้ไขและส่งซ้ำ; ยกเลิกร่างของตัวเอง
- **Approver** (ผู้อนุมัติ): ห่วงโซ่การอนุมัติหลายระดับ (Department Head, Budget Controller, Finance Officer / Manager); approve / reject / send-back / split-reject ในแต่ละ stage
- **Purchaser** (ผู้จัดซื้อ): ตรวจสอบการ allocate vendor และราคา; รวบและแปลง PR ที่อนุมัติแล้วเป็น PO; สามารถส่ง PR กลับเข้าห่วงโซ่ผู้อนุมัติ
- **Procurement Manager** (ผู้จัดการฝ่ายจัดซื้อ): อนุมัติเหนือชั้นสำหรับรายการมูลค่าสูง; ปรับ vendor ranking และกฎ Allocate Vendor; รับ PR ที่ถูก escalate
- **Audit / Config**: Auditor (ตรวจสอบ PR และ activity log แบบ read-only); System Administrator (ตั้งค่า stage ของ workflow, threshold, กฎ delegation และการ void เชิงบริหาร)

## 3. ไฟล์กรณีทดสอบตาม Persona

- [กรณีทดสอบของ Requestor](./04-test-scenarios-requestor.th.md)
- [กรณีทดสอบของ Approver](./04-test-scenarios-approver.th.md)
- [กรณีทดสอบของ Purchaser](./04-test-scenarios-purchaser.th.md)
- [กรณีทดสอบของ Procurement Manager](./04-test-scenarios-procurement-manager.th.md)
- [กรณีทดสอบของ Audit / Config](./04-test-scenarios-audit-config.th.md)

## 4. กรณีข้าม Persona / การส่งต่อ

| # | กรณี | Personas ตามลำดับ | เงื่อนไขก่อนหน้า | สถานะปลายทางที่คาดหวัง |
| - | ---- | ----------------- | ---------------- | ---------------------- |
| X-PR-01 | Happy path เต็มรูปแบบ: สร้าง PR, ผ่านห่วงโซ่อนุมัติสามขั้น, และแปลงเป็น PO | Requestor → Department Head → Budget Controller → Finance → Purchaser | workflow active ที่มีสาม stage อนุมัติ; `base_total_amount` ในส่วนหัวยังไม่ถึง threshold มูลค่าสูง; มีข้อมูล vendor และราคาพร้อม | PR อยู่ในสถานะ `completed` มี `tb_purchase_order` หนึ่งใบหรือมากกว่าที่ลิงก์กลับมายัง PR และ soft commitment แข็งตัวกลายเป็น commitment ของ PO |
| X-PR-02 | Send-back loop: ผู้อนุมัติส่ง PR กลับ, ผู้ร้องขอแก้และส่งซ้ำ | Requestor → Approver (stage N) → Requestor → Approver (stage N) → … → Approver stage สุดท้าย | PR ถูก submit และรอการอนุมัติที่ stage N; มีข้อความเหตุผลสำหรับการส่งกลับ | สุดท้าย PR อยู่ในสถานะ `approved` หลังรอบที่สอง; เก็บประวัติการแก้ไขและความเห็นของผู้อนุมัติไว้; soft commitment งบประมาณถูกปลดตอน send-back แล้วสร้างใหม่ตอน resubmit |
| X-PR-03 | Split-reject: ผู้อนุมัติปฏิเสธบางบรรทัด, อนุมัติบรรทัดที่เหลือ, PR เดินหน้าต่อด้วยบรรทัดที่รอด | Requestor → Approver (stage N) → Approver stage ถัดไป | PR มีอย่างน้อยสองบรรทัด; ผู้อนุมัติให้เหตุผลแยกตามบรรทัด | PR ยังคงอยู่ใน `in_progress` โดยบรรทัดที่ปฏิเสธถูกตั้ง flag; บรรทัดที่รอดเดินไปยัง stage ถัดไป; บรรทัดที่ปฏิเสธไม่ถูกแปลงเป็น PO ในภายหลัง |
| X-PR-04 | Partial conversion: ผู้จัดซื้อแปลงเฉพาะบางบรรทัด เหลือที่เหลือไว้ | Requestor → ห่วงโซ่ Approver ครบ → Purchaser | PR อยู่ในสถานะ `approved` และมีหลายบรรทัด; ต้องการเพียงบางบรรทัดในตอนนี้ (เช่น vendor ที่เลือกไม่พร้อมส่งของบรรทัดอื่น) | สร้าง `tb_purchase_order` อย่างน้อยหนึ่งใบสำหรับบรรทัดที่เลือก; ส่วนหัว PR ยังเป็น `approved` สำหรับบรรทัดที่เหลือจนกว่าจะแปลงต่อหรือหมดอายุ |
| X-PR-05 | การ escalate: ยอดในส่วนหัวเกิน threshold มูลค่าสูงและ route ไปยัง Procurement Manager | Requestor → Department Head → Budget Controller → (escalate) → Procurement Manager | `base_total_amount` ในส่วนหัวเกิน threshold ที่ตั้งไว้ใน workflow | PR เป็น `approved` เฉพาะหลังจาก Procurement Manager เซ็น stage ที่ escalate; cursor ของ stage บันทึกการกระโดด |
| X-PR-06 | Reject path: ผู้อนุมัติปฏิเสธ PR ทั้งฉบับ workflow ยุติ | Requestor → Approver (stage ใดก็ได้) | ผู้อนุมัติให้ข้อความเหตุผล | PR เป็น `cancelled` ปลด soft commitment งบประมาณ ไม่อนุญาตให้กระทำการใด ๆ ต่อ และมี audit comment |
| X-PR-07 | Bounce-back จาก Purchaser: Purchaser ส่ง PR กลับเพื่อ clarify vendor / scope | Requestor → ห่วงโซ่ Approver ครบ → Purchaser → Approver (stage N หรือ Requestor) | PR เป็น `approved`; Purchaser ไม่สามารถจัดการ vendor หรือราคาภายใน scope ได้ | PR กลับเข้าห่วงโซ่ (หรือกลับไปที่ Requestor ในฐานะ returned PR) พร้อมความเห็นของ Purchaser; ขึ้นกับการตั้งค่า workflow สถานะอาจกลับเป็น `in_progress` หรือ `draft` |
| X-PR-08 | การ void เชิงบริหารโดย System Administrator บน PR ที่ยังไม่จบ flow | Requestor → Approver (stage N) → System Administrator | PR อยู่ใน `in_progress`; admin มีเหตุผล (เช่น เอกสารซ้ำ ปัญหา compliance) | PR เป็น `voided` ปลด soft commitment งบประมาณ workflow ยุติ; Auditor อ่านเหตุผลการ void ย้อนหลังได้ |
| X-PR-09 | Cancel-own-draft: Requestor ทิ้งร่างก่อน submit | Requestor เท่านั้น | PR เป็น `draft` และยังไม่เคย submit | PR เป็น `cancelled`; stage ใน workflow ไม่เคยเดินหน้า; ไม่มี audit chain เพิ่มเติมนอกจากเหตุการณ์ cancel |
| X-PR-10 | รอบ Returned PR ตามเส้นทาง golden ของ Playwright | Requestor → HOD (Department Head) → Requestor → HOD → … | seed ด้วย helper `submitPRAsRequestor` + `sendForReviewAsHOD` ใน E2E suite | PR เปลี่ยนจาก Returned → In Progress หลัง Requestor ส่งซ้ำ; status badge และ Workflow History สะท้อนทั้งวงรอบ |

## 5. การเชื่อมโยงกับ E2E Test

Playwright suite ใน `../carmen-inventory-frontend-e2e/tests/` มี coverage ของ PR อยู่แล้ว spec แบบ persona-journey ใช้คอนเวนชันการตั้งชื่อ test case เป็น `TC-PR-NNNNNN`; ไฟล์ per-action × per-role (`301-pr.spec.ts`) ครอบคลุมเมทริกซ์ action × role

### Requestor (Creator)
- `../carmen-inventory-frontend-e2e/tests/302-pr-creator-journey.spec.ts` — persona-journey spec ของ Requestor ครอบคลุม list / แท็บ `My Pending`, happy path การสร้าง PR และ validation error, edit / save draft, submit-for-approval, cancel-own-draft และ smoke check ตาม block `TC-PR-050NNN` เชื่อมกับกรณีของ Requestor ใน [04-test-scenarios-requestor.th.md](./04-test-scenarios-requestor.th.md)
- `../carmen-inventory-frontend-e2e/tests/311-pr-returned-flow.spec.ts` — flow ข้าม persona สำหรับ Returned PR (Requestor แก้และส่งซ้ำ PR ที่ Approver ส่งกลับ) เชื่อมกับ X-PR-02 และ X-PR-10 ในหัวข้อ 4 ด้านบน และกับ scenario send-back ในไฟล์ของ Requestor และ Approver

### Approver
- `../carmen-inventory-frontend-e2e/tests/303-pr-approver-journey.spec.ts` — persona-journey spec ของ Approver (HOD เป็นหลัก, Finance Controller สำหรับเปรียบเทียบ scope) ครอบคลุม My Approvals dashboard, edit mode ในขอบเขตของ approver (approved-qty / item-note / delivery-point แก้ได้, vendor / unit-price อ่านอย่างเดียว), bulk approve / reject / send-for-review / split ผ่าน toolbar เชื่อมกับกรณีของ Approver ใน [04-test-scenarios-approver.th.md](./04-test-scenarios-approver.th.md) และ X-PR-02, X-PR-03, X-PR-06 ในหัวข้อ 4 ด้านบน

### Purchaser
- `../carmen-inventory-frontend-e2e/tests/304-pr-purchaser-journey.spec.ts` — persona-journey spec ของ Purchaser ครอบคลุม list ที่จำกัด scope ไว้ที่ stage `Purchase`, สิทธิ์ใน edit mode (vendor / unit-price / discount / tax-profile แก้ได้, approved-qty อ่านอย่างเดียว), Auto Allocate vendor, bulk approve / reject / send-for-review / split และกรณี golden `TC-PR-070901` แบบ full-flow เชื่อมกับกรณีของ Purchaser ใน [04-test-scenarios-purchaser.th.md](./04-test-scenarios-purchaser.th.md) และ X-PR-01, X-PR-04, X-PR-07 ในหัวข้อ 4 ด้านบน

### Procurement Manager
- ยังไม่มี spec เฉพาะของ Procurement Manager เส้นทาง escalation (X-PR-05) และการ override มูลค่าสูงถูก cover บางส่วนใน block `gmTest` ใน `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` **TODO**: เพิ่ม `30X-pr-procurement-manager-journey.spec.ts` หลังจากเผยแพร่ไฟล์กรณีของ Procurement Manager

### Audit / Config
- ยังไม่มี spec เฉพาะของ Auditor / System Administrator — flow ส่วนใหญ่ที่เป็นการตั้งค่า / void / threshold อยู่ในหน้า admin นอกตัวโมดูล PR **TODO**: เพิ่ม coverage ใต้ `../carmen-inventory-frontend-e2e/tests/` (เช่น การตั้งค่า stage ของ workflow, ตั้ง threshold, void-with-reason บน PR ที่ยังไม่จบ flow) หลังจากเผยแพร่ไฟล์กรณีของ Audit / Config; X-PR-08 จากหัวข้อ 4 ด้านบนเป็นตัวเลือกที่ควรทำก่อน

### shared / multi-role
- `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` — coverage แบบ per-action × per-role ที่มีมาก่อน persona-journey spec ใช้ได้ดีสำหรับการ regression เรื่อง permission / authorization ครอบคลุม fixture `requestorTest`, `hodTest`, `fcTest`, `purchaseTest`, `gmTest` และ `noAuthTest`
- `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts` — coverage การ create / edit ของ PR Template (purchase-role + การปฏิเสธ requestor) อยู่ใกล้กับไฟล์ของ Purchaser

## 6. แหล่งอ้างอิง

- `../carmen-inventory-frontend-e2e/` — Playwright test suite (executable spec ของแถวต่าง ๆ ด้านบน)
- `../carmen/docs/purchase-request-management/testing.md` — กลยุทธ์การทดสอบต้นน้ำ ครอบคลุมระดับ unit / integration / E2E / performance / security พร้อมตัวอย่างการทดสอบ
- `../carmen/docs/purchase-request-management/troubleshooting.md` — failure mode ที่ทราบ, error code และวิธีแก้ ใช้ขับเคลื่อนหัวข้อย่อย Validation / Error ในไฟล์ของแต่ละ persona
- ไฟล์พี่น้อง: [03-user-flow.md](./03-user-flow.th.md) — บริบทของ flow โดยเฉพาะหัวข้อ 4 (Cross-Persona Handoffs) ที่ใช้เป็นที่มาของหัวข้อ 4 ด้านบน
- ไฟล์พี่น้อง: [02-business-rules.md](./02-business-rules.md) — กฎที่ถูกตรวจสอบโดย negative test ในบล็อก Validation / Error ของแต่ละ persona
