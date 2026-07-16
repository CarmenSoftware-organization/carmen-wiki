---
title: แดชบอร์ดใบขอซื้อ (PR Dashboard)
description: "ถูกลบแล้วเมื่อ 2026-06-27 เก็บไว้เป็นข้อมูลอ้างอิงเชิงประวัติศาสตร์เท่านั้น: tile สรุปใบขอซื้อ — pipeline ตาม stage, รายการที่ถูก send-back/reject, ค่าใช้จ่ายส่วนตัวเทียบกับแผนก และคิวงานของผู้อนุมัติ"
published: true
date: 2026-07-16T01:35:43.000Z
tags: dashboard, purchase-request, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ดใบขอซื้อ (PR Dashboard)

> **At a Glance**
> **Route:** ไม่มี — `/dashboard/pr` ไม่เคยมีอยู่จริงในฐานะ route &nbsp;·&nbsp; **สถานะ:** **ถูกลบแล้วเมื่อ 2026-06-27** — เก็บไว้เป็นข้อมูลอ้างอิงเชิงประวัติศาสตร์เท่านั้น component นี้ถูกลบทิ้งในฐานะ dead code และไม่เคยอยู่หลัง router entry ใดๆ

## สถานะการ implement (ตรวจสอบเมื่อ 2026-07-16)

หน้านี้ document `dashboard-pr.tsx` (เดิมคือ `routes/dashboard/_components/dashboard-pr.tsx`) และ fixture `mock/pr.ts` ของมัน `/dashboard/pr` ไม่เคยมีอยู่ใน `routes/router.tsx` — sidebar entry ของ Dashboard resolve ไปยัง component เดียวเท่านั้นเสมอมา คือหน้า [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) ในปัจจุบัน ไฟล์ demo นี้ถูกลบพร้อมไฟล์พี่น้องอีก 7 ไฟล์ใน commit `03891e3d` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", `carmen-inventory-frontend-react`, 2026-06-27) ซึ่ง commit message ระบุว่ามันและ mock fixture ของมัน "no importers anywhere" เนื้อหาด้านล่างทั้งหมดอธิบายหน้าจอ demo ที่ถูกลบและไม่เคยมี route จริงนี้ — เก็บไว้เป็นข้อมูลอ้างอิงเชิงประวัติศาสตร์เท่านั้น ถือว่าทุกข้อความ "ยังเป็น mock data ในปัจจุบัน", "เมื่อ live" และการอ้าง route ในส่วนที่เหลือของหน้านี้เป็นโมฆะ — จะไม่มีวัน live ภายใต้หน้านี้

![แดชบอร์ดใบขอซื้อ (PR Dashboard) screen](/screenshots/dashboard/pr.png)

## 1. คืออะไรและสำหรับใคร

ห้องนักบินของใบขอส่วนตัว หัวข้อหน้าอ่านว่า "MY PR – PERSONAL REQUISITIONS DASHBOARD" ตอบสองคำถาม: *"PR ของฉันติดอยู่ที่ไหน?"* และ *"อะไรกำลังรอที่ฉันอยู่ตอนนี้?"*

**Layout:** แถบ pipeline ห้า stage (ด้านบน) → สองตาราง Sent Back / Rejected (ซ้าย) + donut ค่าใช้จ่าย + bar แผนก (ขวา) → คิว Awaiting Approval เต็มความกว้าง (ด้านล่าง)

**กลุ่มผู้ใช้**

- **Requester** — หลัก เฝ้าดู Sent Back / Rejected เพื่อแก้และ submit ใหม่ ติดตามแถบ pipeline
- **HOD / Approver** — ใช้คิว Awaiting Approval ด้านล่างเป็นคิวงาน badge `Awaiting HOD Approve` เล็งไปที่การทำงานของ HOD
- **Procurement** — ตรวจสอบแถว `Awaiting PO` ที่พร้อมแปลงเป็น [purchase-order](/th/inventory/purchase-order)

## 2. Tile และการ Drill-down

| Tile | แสดงอะไร | Drill-down (เมื่อ live) |
|---|---|---|
| **PR Summary (Pipeline)** | 5 stage: Requests / In Process / Approved / PO Generated / Received — จำนวน + progress bar | → [purchase-request](/th/inventory/purchase-request) กรองตาม stage |
| **Sent Back PRs** | PR Number, Item, Date Sent, Sender, Reason | → [purchase-request](/th/inventory/purchase-request) detail |
| **PRs Rejected & Item Rejects** | PR Number/Item ID, Material, Requester, Rejected By, Reason | → [purchase-request](/th/inventory/purchase-request) detail |
| **ค่าใช้จ่ายของฉัน (ส่วนตัว)** | Donut ตาม 3 หมวด พร้อม external label เปอร์เซ็นต์ | — |
| **ค่าใช้จ่ายของแผนก (F&B Dept)** | bar แนวนอน: Food / Beverage / Guest Supply | — |
| **PR รออนุมัติ** | PR, Item, Requester, Dept, Date, badge สถานะ (`Awaiting HOD Approve` / `Awaiting PO`), action "Direct details" | → [purchase-request](/th/inventory/purchase-request) detail |

สกุลเงินในกราฟค่าใช้จ่ายแสดงเป็น `$` ใน mock — production ควรใช้สกุลเงินฐานของ BU จาก [master-data/exchange-rate](/th/inventory/master-data/exchange-rate)

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| ทำไม pipeline count ไม่อัปเดตหลัง submit PR? | **ยังเป็น mock data** — ตัวเลขมาจาก `mock/pr.ts` ไม่ใช่จาก [purchase-request](/th/inventory/purchase-request) การ wire จริงจะ refresh on focus |
| ห้า stage มาจากไหน? | การ project แบบยุบของ `workflow_current_stage` (ดู [system-config/workflow](/th/inventory/system-config/workflow)) ไปยัง Requests / In Process / Approved / PO Generated / Received |
| "My Spending" คือ PR ของฉันเท่านั้นหรือของแผนกฉัน? | "My" คือ `requestor_id = current_user`; "Department" คือ scope `department_id` — query เดียวกัน แต่ scope บนยอด PR line ที่จัดกลุ่มตาม [product/category](/th/inventory/product/category) ต่างกัน |
| Awaiting Approval จะ live เมื่อไหร่? | hook มีอยู่ — `useApprovalPending({ doc_type: "pr" })` ใน `hooks/use-approval.ts` — แต่ **ยังไม่ถูก mount** บนหน้านี้ |
| ทำไมสกุลเงินขึ้นเป็น `$` ไม่ใช่ `฿`? | Mock fixture quirk; production จะ localise ไปยังสกุลเงินฐานของ BU |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Tile กดไม่ได้ / drill ไม่ไปไหน | drill-down route ยังไม่ wire ในบิลด์ปัจจุบัน | (Inferred — ต้องยืนยันกับ UI จริง) |
| ตัวเลขไม่ตรงกับรายการ [purchase-request](/th/inventory/purchase-request) | หน้านี้อ่าน mock fixture อิสระ ไม่ใช่ข้อมูลจริง | จะถูกแก้เมื่อ `useApprovalPending` ถูก mount |
| ตาราง Sent Back ว่างทั้งที่มี PR ที่ถูก send-back | mock fixture มี seed row จำกัด | ตรวจสอบ `mock/pr.ts` → `sentBackPrs` |
| badge `Awaiting HOD Approve` ไม่ refresh หลัง approve | mock เป็น static ไม่มี event listener | wire จริงใช้ TanStack Query refetch-on-focus |

---

## 5. แหล่งข้อมูล (Dev)

- **Pipeline counts** — group-count บน [purchase-request](/th/inventory/purchase-request) โดย `workflow_current_stage`
- **Sent Back / Rejected** — `workflow_action_history` กรองเป็น `action ∈ {send_back, reject}` join กลับไป [purchase-request](/th/inventory/purchase-request)
- **ค่าใช้จ่ายของฉัน / ของแผนก** — sum ยอด PR line จัดกลุ่มตาม [product/category](/th/inventory/product/category) scope ด้วย `requestor_id` / `department_id`
- **Awaiting Approval** — `useApprovalPending({ doc_type: "pr" })` (`hooks/use-approval.ts`) เมื่อ wire แล้ว

## 6. จังหวะการ Refresh

mock แบบ static ในปัจจุบัน เมื่อ wire ผ่าน `useApprovalPending` แล้ว ค่า default ของ TanStack Query จะใช้ — refetch on focus, ไม่ poll Sidebar pending-count badge (แยกจากหน้านี้) ใช้ `CACHE_DYNAMIC` (1-min stale)

## 7. โมดูลที่เกี่ยวข้อง

- [purchase-request](/th/inventory/purchase-request) — ระบบบันทึก transactional
- [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) — ปลายทาง drill สำหรับคิวงาน
- [purchase-order](/th/inventory/purchase-order) — ปลายทางการแปลงสำหรับ `PO Generated`
- [good-receive-note](/th/inventory/good-receive-note) — stage `Received` ปลายน้ำ
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม stage ที่ขับเคลื่อน pipeline bucket

## 8. แหล่งข้อมูลอ้างอิง

- **Page shell / composition (ถูกลบเมื่อ 2026-06-27):** `routes/dashboard/_components/dashboard-pr.tsx` ใน `../carmen-inventory-frontend-react`
- **Mock data (ถูกลบเมื่อ 2026-06-27):** `routes/dashboard/mock/pr.ts` ใน `../carmen-inventory-frontend-react`
- **Commit ที่ลบ:** `03891e3d` — "refactor(dashboard): convert to idiomatic structure, drop dead demo code"
- **i18n key ที่ยังอยู่แต่ไม่ถูกใช้:** `messages/en.json` → `dashboard.pr.title` = "Purchase Request Dashboard"
- **hook `useApprovalPending`** (`hooks/use-approval.ts`) เป็นของจริงและ live แต่ขับเคลื่อน `/procurement/approval` — ดู [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) — ไม่ใช่หน้านี้ที่ถูกลบไปแล้ว
