---
title: ใบขอซื้อ (Purchase Request) — Test Scenarios — Procurement Manager
description: Test case ของ Procurement Manager (อนุมัติมูลค่าสูงแบบ escalated) สำหรับโมดูล purchase-request
published: true
date: 2026-07-15T10:20:00.000Z
tags: purchase-request, test-scenarios, procurement-manager, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T09:00:00.000Z
---

# ใบขอซื้อ (Purchase Request) — Test Scenarios — Procurement Manager

> **At a Glance**
> **Persona:** Procurement Manager / General Manager (stage approve แบบ escalated / มูลค่าสูง — UI เดียวกับ chain Approver พื้นฐาน) &nbsp;·&nbsp; **โมดูล:** [purchase-request](/th/inventory/purchase-request) &nbsp;·&nbsp; **Scenario:** ~7
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation
> **E2E coverage:** ยังไม่มี persona-journey spec เฉพาะของ Procurement Manager; เส้นทาง escalation / มูลค่าสูงถูกทดสอบผ่าน fixture `gmTest` ใน `tests/301-pr.spec.ts` ใน `../carmen-inventory-frontend-e2e/`

หน้านี้จับ test scenario ที่ persona Procurement Manager ขับในโมดูล `purchase-request` ตามที่บันทึกใน [03-user-flow-procurement-manager.md](./03-user-flow-procurement-manager.md) source ปัจจุบันไม่มีหน้าจอเฉพาะของ Procurement Manager — persona นี้คือ stage role `approve` ใน workflow **เดียวกัน** กับ chain Approver พื้นฐาน โดยเข้าถึงผ่าน threshold-based escalation (`PR_AUTH_005`) หรือ workflow route ตรง Scenario ด้านล่างเป็น subset ระดับ stage-escalated ของ scenario Approver พื้นฐานใน [04-test-scenarios-approver.md](./04-test-scenarios-approver.md); scenario ระดับบรรทัด, delegation และ threshold-boundary ของหน้านั้นใช้ที่นี่ตรงตัวเช่นกัน

> ⚠️ **หมายเหตุความคลาดเคลื่อน:** เนื้อหารุ่นก่อนหน้าของหน้านี้อธิบาย "configurational surface" (scoring weight ของ Vendor Allocation Rules, override priority ต่อ vendor, bulk action Stuck PR Oversight) พร้อม scenario เพิ่มเติมอีก ~20 รายการ ไม่พบหน้าจอ, route หรือ endpoint ที่ตรงกันใน `../carmen-inventory-frontend-react/` หรือ `../carmen-turborepo-backend-v2/` ในรอบตรวจสอบนี้ — ดูรายการ discrepancy log ใน progress log ของการ resync scenario เหล่านั้นถูกลบออกแทนที่จะคงไว้เป็นเนื้อหาสมมติ

## 1. Happy Path

| # | Scenario | Pre-condition | Steps | คาดหวัง |
| - | -------- | ------------- | ----- | -------- |
| PM-HP-01 | รับและ review PR ที่ escalated | PR `pr_status = in_progress`, route ไปยัง Procurement Manager เพราะ `base_total_amount` ข้าม threshold ที่ตั้ง (`PR_AUTH_005`) หรือผ่าน workflow route ตรง | เปิด **My Pending**; เปิด PR ที่ escalated; review header, บรรทัด, Budget Impact และ Activity Log (comment ของ Approver ต้นน้ำทั้งหมดมองเห็น) | หน้า PR detail load ด้วย UI read-mostly / Edit Mode เดียวกันกับ chain Approver พื้นฐาน; action bar แสดง bulk toolbar มาตรฐาน |
| PM-HP-02 | Approve PR ที่ escalated ที่ stage สุดท้าย | PR อยู่ที่ stage ของ Procurement Manager ซึ่งเป็น stage `approve`-role สุดท้ายของ chain | เข้า Edit Mode, เลือกทั้งหมด, bulk **Approve**, ยืนยัน | `PR_POST_005` fire: `pr_status` พลิก `in_progress → approved`; PR เข้าเกณฑ์สำหรับ dialog Convert-to-PO แยกต่างหาก |
| PM-HP-03 | Reject PR มูลค่าสูงมาก | PR ถูกมอบหมายให้ Procurement Manager / General Manager เพื่ออนุมัติ (`TC-PR-060005`) | เปิด PR; คลิก **Reject**; กรอกเหตุผล; ยืนยัน | `pr_status` พลิกเป็น `voided`; requestor ได้รับแจ้ง; Auditor review เหตุผลได้ภายหลัง |
| PM-HP-04 | ส่ง PR escalated กลับเพื่อแก้ไข | PR อยู่ที่ stage escalated; เหตุผลไม่เพียงพอ | Bulk **Send for Review** พร้อมเหตุผล | `workflow_current_stage` ย้ายกลับหนึ่ง step (หรือถึง create stage ของ Requestor ทั้งหมด ทำให้ `pr_status` กลับเป็น `draft` ขึ้นกับ workflow configuration) |

## 2. Permission / Authorization

| # | Scenario | พฤติกรรมที่คาด (allow/deny + เหตุผล) |
| - | -------- | --------------------------------------- |
| PM-PERM-01 | Procurement Manager เปิด PR ที่ stage escalated ซึ่งมอบหมายให้ตน | **Allow** — สิทธิ์เดียวกับ chain Approver พื้นฐาน (`PR_AUTH_002`, `PR_AUTH_003`, `PR_AUTH_004`) |
| PM-PERM-02 | Procurement Manager เปิด PR ที่ยังอยู่ stage ก่อนหน้า (เช่น Budget Controller) ที่ยังไม่ escalate | **Deny action, read-only** (ถ้ามองเห็นเลย) — `user_action.execute[]` ของ stage ปัจจุบันไม่มี Procurement Manager |
| PM-PERM-03 | Procurement Manager พยายามแก้ vendor / ราคาต่อหน่วย / ส่วนลด / tax บนบรรทัด | **Deny.** ฟิลด์เหล่านั้นสงวนสำหรับ stage role `purchase` ตาม `PR_AUTH_008`; stage approve-role แบบ escalated ได้เฉพาะ `approved_qty` ตาม `PR_VAL_013` |

## 3. Validation / Error

| # | Scenario | Trigger | Error ที่คาด |
| - | -------- | ------- | -------------- |
| PM-VAL-01 | Reject / Send for Review โดยไม่มีเหตุผล | ทิ้งฟิลด์เหตุผลว่าง, คลิก Confirm | Reject — ปุ่ม Confirm ยังคง disabled หรือ server reject การเรียก; เหตุผลเป็น mandatory ทั้งสอง action |
| PM-VAL-02 | ปรับ `approved_qty` เกิน `requested_qty` | ตั้ง `approved_qty` เกิน `requested_qty` บนบรรทัด, คลิก Approve | `PR_VAL_013` — reject ด้วย "Approved quantity must be positive and may not exceed requested quantity" |

## 4. แหล่งอ้างอิง

- ภาพรวมหลัก: [04-test-scenarios.md](./04-test-scenarios.md) — handoff ข้าม persona `X-PR-05` (threshold escalation)
- User flow: [03-user-flow-procurement-manager.md](./03-user-flow-procurement-manager.md)
- กฎทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) Section 4 (`PR_AUTH_005` routing ตาม threshold, `PR_AUTH_006` delegation), Section 5 (`PR_POST_003`, `PR_POST_005`, `PR_POST_006`)
- หน้าพี่น้อง: [04-test-scenarios-approver.md](./04-test-scenarios-approver.md) — scenario Approver พื้นฐานที่ชุดนี้ extend ตรงตัว (validation ระดับบรรทัด, delegation, edge case threshold-boundary)
- E2E: **ช่องว่าง** — ยังไม่มี `30X-pr-procurement-manager-journey.spec.ts` เฉพาะ Scenario escalation / มูลค่าสูงถูกทดสอบผ่าน fixture `gmTest` ใน `../carmen-inventory-frontend-e2e/tests/301-pr.spec.ts` (เช่น `TC-PR-060005`)
- Cross-link: [purchase-order](/th/inventory/purchase-order) — โมดูลปลายน้ำที่รับ PR ที่ final-approved สำหรับการแปลง
