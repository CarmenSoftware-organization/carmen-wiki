---
title: ใบขอซื้อ (Purchase Request) — Test Scenarios — Purchaser
description: Test case ของ Purchaser (happy path, permission, validation, edge case) สำหรับโมดูล purchase-request
published: true
date: 2026-07-15T10:50:00.000Z
tags: purchase-request, test-scenarios, purchaser, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ (Purchase Request) — Test Scenarios — Purchaser

> **At a Glance**
> **Persona:** Purchaser (Purchasing Staff — stage role `enum_stage_role = purchase` ในสายอนุมัติของ PR เอง บวกผู้ใช้งาน dialog Convert-to-PO แยกต่างหาก) &nbsp;·&nbsp; **โมดูล:** [purchase-request](/th/inventory/purchase-request) &nbsp;·&nbsp; **Scenario:** ~18
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **E2E coverage:** `tests/304-pr-purchaser-journey.spec.ts` (`TC-PR-0701xx`–`TC-PR-0709xx`, แหล่งหลัก) บวก block ของ purchase-role ใน `tests/301-pr.spec.ts` (`TC-PR-470xxx` edit pricing, `TC-PR-490xxx` submit after allocation, `TC-PR-600xxx` reject, `TC-PR-410xxx` convert to PO) ใน `../carmen-inventory-frontend-e2e/`

หน้านี้จับ test scenario ที่ persona Purchaser ขับโดยตรงในโมดูล `purchase-request` แบ่งตามสองสิ่งที่พวกเขาทำจริงใน build ปัจจุบัน: (1) ทำหน้าที่ที่ stage role `purchase` ภายในสายอนุมัติของ PR เอง — แก้ vendor / ราคาต่อหน่วย / ส่วนลด / tax profile, รัน **Auto Allocate** แล้ว bulk Approve / Reject / Send for Review / Split เหมือน stage อื่นทุกประการ — และ (2) แยกต่างหาก เมื่อ PR เป็น `approved` แล้ว รัน dialog **Convert to PO** จากโมดูล Purchase Order ดู [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) สำหรับ walkthrough เต็มของทั้งสองอย่าง

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | คาดหวัง |
| - | -------- | ------------- | ----- | -------- |
| PUR-HP-01 | List load, My Pending เป็น default; PR ที่ stage Purchase มองเห็น | Purchaser ล็อกอิน; PR ถูก submit และ HOD-approve แล้วจนลงที่ stage ที่มอบหมายให้ Purchaser | Sidebar → Purchase Request ยืนยัน URL และแท็บ My Pending (`TC-PR-070101`) | List load ที่ `/procurement/purchase-request`; แท็บ My Pending ถูกเลือกเมื่อมีอยู่ |
| PUR-HP-02 | Detail load แท็บ Items เป็น default; ไม่มีปุ่ม Approve/Reject แบบ standalone | PR seed ที่ stage Purchase (`submitPRAsRequestor` + `approveAsHOD`) | เปิดหน้า PR detail (`TC-PR-070201`, `TC-PR-070203`) | Detail URL load; แท็บ Items ถูกเลือกเมื่อมีอยู่; ไม่มีปุ่ม Approve / Reject / Send-back แบบ standalone ระดับ header (ช่องว่างตาม BRD — bulk toolbar เท่านั้น) |
| PUR-HP-03 | เข้า Edit Mode → vendor / ราคา / ส่วนลด / tax แก้ไขได้ | PR เดียวกัน, ปุ่ม Edit มองเห็น | คลิก **Edit**; ตรวจ input Vendor, Unit Price, Discount, Tax Profile บนบรรทัดแรก (`TC-PR-070301`–`TC-PR-070305`) | Input Vendor, Unit Price, Discount, Tax Profile แก้ได้; `Approved Qty` ยังคง disabled/read-only (`TC-PR-070306`) เพราะ stage HOD ตั้งไว้แล้ว |
| PUR-HP-04 | Auto Allocate เติม vendor + ราคาผ่าน scoring lookup | Edit Mode active, มีบรรทัดอย่างน้อยหนึ่งที่ตั้งสินค้า / หน่วย / สกุลเงินแล้ว | คลิก **Auto Allocate** (`TC-PR-070307`) | Request เสร็จและหน้ายังอยู่ที่ URL detail เดิม; vendor, ราคา, pricelist reference และ tax เติมจาก price-compare lookup สำหรับบรรทัดที่ resolve ได้ |
| PUR-HP-05 | Save edits เก็บการเปลี่ยน vendor/ราคา | Edit Mode ที่มีการแก้ Unit Price | เติม Unit Price, คลิก **Save Draft** (`TC-PR-070309`) | Form กลับไป view mode; ปุ่ม Edit มองเห็นอีกครั้ง; ราคาใหม่ถูกเก็บไว้ |
| PUR-HP-06 | Bulk Approve เดินหน้า PR | Edit Mode, เลือกทุกแถว | เลือกทั้งหมด, คลิก bulk **Approve**, ยืนยัน (`TC-PR-070401`, golden flow `TC-PR-070901`) | PR อยู่ที่ URL detail เดิม; stage เดินหน้า (หรือ `pr_status` พลิก `in_progress → approved` ตาม `PR_POST_005` ถ้านี่เป็น stage สุดท้าย) |
| PUR-HP-07 | Bulk Reject พร้อมเหตุผล | Edit Mode, เลือกทุกแถว | เลือกทั้งหมด, คลิก bulk **Reject**, กรอกเหตุผล, ยืนยัน (`TC-PR-070402`; ยังมี `TC-PR-600001` ผ่านปุ่ม Reject บน PR เดียว) | `pr_status` พลิกเป็น `voided` (terminal); เหตุผลและผู้ใช้ที่ reject ถูกบันทึกใน audit trail |
| PUR-HP-08 | Bulk Send for Review กลับไป stage ก่อนหน้า | Edit Mode, เลือกทุกแถว | เลือกทั้งหมด, คลิก bulk **Send for Review**, กรอกเหตุผลและ stage เป้าหมาย, ยืนยัน (`TC-PR-070403`) | `workflow_current_stage` ย้ายกลับหนึ่ง step; ถ้าเป้าหมายคือ create stage `pr_status` กลับเป็น `draft` |
| PUR-HP-09 | Bulk Split — accept บางบรรทัด, reject บรรทัดอื่น | Edit Mode, PR มี 2+ บรรทัด | เลือกทั้งหมด, คลิก bulk **Split** (`TC-PR-070404`) | UI Split เปิด; บรรทัดที่ reject ถูก flag `current_stage_status = rejected` และตัดออกจากการดำเนินการต่อไป, บรรทัดที่ accept เดินต่อ |
| PUR-HP-10 | แปลง PR ที่ approved เป็น PO | PR หนึ่งใบหรือมากกว่าที่ `pr_status = approved` | จากโมดูล Purchase Order เปิด **Convert to PO**; เลือก workflow; tick PR ที่ approved แล้ว; review draft PO ที่ group อัตโนมัติ; ยืนยัน (`TC-PR-410001`, และ endpoint `group-pr` / `confirm-pr`) | สร้าง `tb_purchase_order` หนึ่งใบต่อ group `(vendor, delivery_date, currency)`; PR ต้นทางที่บรรทัดถูก bridge ครบแล้วพลิกจาก `approved` เป็น `completed` (`PR_POST_007`) |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาด (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| PUR-PERM-01 | Purchaser เปิด PR ที่อยู่ที่ stage ซึ่งมอบหมายให้ตน | **Allow** view + Edit Mode + bulk toolbar action `PR_AUTH_002` ผ่านเพราะผู้ใช้ที่ล็อกอินอยู่ใน `user_action.execute[]` ของ stage ปัจจุบัน |
| PUR-PERM-02 | Purchaser เปิด PR ที่ stage ไม่ใช่ Purchase (เช่นยังอยู่ที่ HOD) | **Deny edit** ไม่มีปุ่ม Edit หรือฟิลด์ vendor ใน Edit Mode ยังคง disabled (`TC-PR-070405`) — Purchaser ไม่ใช่ผู้ใช้ที่มอบหมายของ stage ปัจจุบัน |
| PUR-PERM-03 | Purchaser พยายามแก้ `approved_qty` | **Deny.** ฟิลด์ read-only สำหรับ stage role `purchase`; ถูกตั้งโดย chain Approver ตาม `PR_VAL_013` |
| PUR-PERM-04 | ผู้ใช้ non-purchase (Requestor / HOD) พยายามเปิด dialog Convert-to-PO | **ไม่พบการบังคับสิทธิ์ใน source ปัจจุบัน** เอกสาร Bruno ของ `group-pr` / `confirm-pr` ระบุ `Permissions: None` ทั้งคู่, controller ฝั่ง backend ไม่มี role guard และสาย dialog (`po-create-dialog.tsx` → `po-from-pr-dialog.tsx`) ไม่มีการตรวจ `hasPermission` — catalog `PERMISSIONS` นิยาม `procurement.purchase_order` เป็น view-only โดยไม่มี key create และไม่ถูกอ้างอิงโดย dialog การเข้าถึงถูกจำกัดเพียงด้วยการเข้าถึง UI ของโมดูล Purchase Order เท่านั้น `TC-PR-410004` ("No Permission to Convert PR") มีอยู่ใน `301-pr.spec.ts` แต่ไม่ assert การ deny — ปุ่มที่ไม่มีอยู่ทำให้ test ผ่านโดยอัตโนมัติ บันทึกใน discrepancy log ของการ resync แล้ว; ให้ถือว่าความคาดหวังเรื่องการ deny ยังไม่ถูก implement จนกว่าจะมี guard จริง |
| PUR-PERM-05 | Purchaser พยายามแปลง PR ที่ยัง `in_progress` | **Deny — สถานะผิด.** รายการ PR-for-PO คืนเฉพาะ PR ที่ `pr_status = approved`; PR ที่ยังกลาง flow ไม่ปรากฏเป็น candidate ที่เลือกได้ |

## 3. Validation / Error

| # | Scenario | Trigger | Error ที่คาด |
| - | -------- | ------- | -------------- |
| PUR-VAL-01 | Bulk action ที่เทียบเท่า submit พร้อมราคาต่อหน่วยที่ขาด | พยายาม bulk Approve ขณะบรรทัดหนึ่งไม่มี `unit_price` / `pricelist_price` (`TC-PR-490002`) | Reject — inline validation error ปรากฏ; Purchaser เติมราคาแล้วลองใหม่ |
| PUR-VAL-02 | Bulk action พร้อมการเลือก vendor ไม่ครบ | พยายาม bulk Approve ขณะบรรทัดหนึ่งมี `vendor_id IS NULL` (`TC-PR-490003`) | Reject — inline validation error; Purchaser รัน Auto Allocate หรือเลือก vendor ด้วยมือแล้วลองใหม่ |
| PUR-VAL-03 | Reject ด้วยเหตุผลสั้นเกินไป | เหตุผลของ Bulk/Reject สั้นกว่าความยาวขั้นต่ำ (`TC-PR-600002`) | Reject — ข้อความ error ว่าเหตุผลสั้นเกินไป; Confirm ถูกบล็อกจนกว่าจะแก้ |
| PUR-VAL-04 | Convert to PO ด้วย vendor ไม่ถูกต้องบน group | พยายาม Convert-to-PO ขณะบรรทัดของ PR ที่เลือก resolve เป็น vendor ไม่ตรง/ไม่พบ (`TC-PR-410002`) | Reject — error ปรากฏใน dialog; ไม่มีการสร้าง PO; `pr_status` ของ PR ต้นทางไม่เปลี่ยน |

## 4. Edge Case

| # | Scenario | เงื่อนไข | คาดหวัง |
| - | -------- | --------- | -------- |
| PUR-EDGE-01 | หลายบรรทัด — การแก้ราคาแยกอิสระต่อแถว | PR seed ด้วย 2 บรรทัด | การตั้ง Unit Price บนแถว 0 ไม่กระทบค่าของแถว 1 (`TC-PR-070308`) |
| PUR-EDGE-02 | Cancel edits ทิ้งการเปลี่ยนแปลง | Edit Mode ที่มีการแก้ราคาที่ยังไม่ save | คลิก **Cancel** — form กลับไป view mode; การเปลี่ยนไม่ถูก persist (`TC-PR-070310`) |
| PUR-EDGE-03 | Convert to PO เมื่อ PR ไม่มีวันส่งของ | PR approved ที่บรรทัดหนึ่งไม่มี `delivery_date` (`TC-PR-410003`) | PO ถูกสร้างด้วยวันส่งของ default แทนที่จะบล็อกการแปลง |
| PUR-EDGE-04 | PR ที่แปลงครบแล้วไม่กลับมาในรายการ PR-for-PO | PR ต้นทางที่พลิกเป็น `completed` แล้วผ่าน `PR_POST_007` | PR ไม่ปรากฏในรายการขั้นตอนที่ 1 ของ Convert-to-PO; เลือกซ้ำไม่ได้ |

## 5. แหล่งอ้างอิง

- ภาพรวมหลัก: [04-test-scenarios.md](./04-test-scenarios.md)
- User flow: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — แหล่ง happy-path สำหรับ Section 1 ด้านบน; อธิบาย flow แก้ที่ stage `purchase` + bulk-decide และ dialog Convert-to-PO แยกต่างหาก
- กฎทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) Section 5 (`PR_POST_005` final approve → `approved`, `PR_POST_007` convert to PO → `completed`)
- โมเดลข้อมูล: [01-data-model.md](./01-data-model.md) Section 2 — ตาราง bridge `tb_purchase_order_detail_tb_purchase_request_detail`
- E2E: `../carmen-inventory-frontend-e2e/tests/304-pr-purchaser-journey.spec.ts` (แหล่งหลัก, persona-journey — fixture `purchaseTest`) และ `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` (block purchase-role: "PR — Edit pricing", "PR — Submit after vendor allocation", "PR — Reject by Purchase Staff", "PR — Convert to PO — Purchase Staff") Coverage PR Template ที่ใกล้กับ scope Purchaser อยู่ใน `../carmen-inventory-frontend-e2e/tests/310-pr-template.spec.ts`
- Cross-link: [purchase-order](/th/inventory/purchase-order) — โมดูลปลายน้ำที่รับ PO ที่แปลงแล้ว
- Cross-link: [vendor-pricelist](/th/inventory/vendor-pricelist) — แหล่ง pricelist สำหรับ Auto Allocate
