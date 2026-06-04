---
title: Widget My Approval แดชบอร์ด (My Approval Dashboard Widget)
description: widget คิวงานอนุมัติส่วนตัวบน /dashboard แสดงรายการเอกสาร PR/PO/SR ที่รอการอนุมัติของผู้ใช้ที่ล็อกอิน จัดกลุ่มตามประเภทเอกสารพร้อม count สด
published: true
date: 2026-06-04T00:00:00.000Z
tags: dashboard, my-approval, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Widget My Approval แดชบอร์ด (My Approval Dashboard Widget)

> **At a Glance**
> **Route:** `/dashboard` (widget — ไม่ใช่ route แบบ standalone) &nbsp;·&nbsp; **สำหรับ:** HOD / Approver &nbsp;·&nbsp; Procurement Manager &nbsp;·&nbsp; **สถานะ:** **Live** — hook mount แล้วและเรียก API endpoint จริง &nbsp;·&nbsp; **ขอบเขต:** ส่วนบุคคล — เฉพาะเอกสารที่ผู้ใช้ที่ล็อกอินเป็นผู้อนุมัติต่อไป

## 1. คืออะไรและสำหรับใคร

Section **My Approval** คือ widget ที่ render อยู่ภายในหน้า `/dashboard` แสดงเอกสารที่รอการอนุมัติของผู้ใช้ปัจจุบัน แบ่งออกเป็นสาม section — Purchase Requests, Purchase Orders และ Store Requisitions — แต่ละ section มี count badge และตารางรายการที่รอดำเนินการ

widget นี้คือ summary ระดับแดชบอร์ดของสิ่งที่หน้า [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) แสดงอย่างครบถ้วน จำกัดที่ 10 รายการล่าสุดต่อการ fetch (`perpage: 10`)

**Layout:**
- Section header "Pending My Approval" พร้อม warning badge แสดง total count
- สาม subsection (PR / PO / SR) แต่ละอันมีขอบซ้ายสี (module colour), count badge และตาราง item
- ตาราง PR / SR: Doc No, Requester, Department, Stage, Date
- ตาราง PO: Doc No, Vendor, Amount, Stage, Date
- ลิงก์ "View All →" ด้านล่าง navigate ไปยัง `/procurement/approval` เมื่อมี item

**กลุ่มผู้ใช้**

- **HOD / Department Head** — ผู้อนุมัติหลัก; ใช้ section PR เพื่อดำเนินการกับ request ที่รออยู่
- **Procurement Manager** — ใช้ section PO เพื่ออนุมัติ purchase order
- **Store Manager** — ใช้ section SR เพื่ออนุมัติ store requisition จาก store ของตน

## 2. Tile และการ Drill-down

| Section | แสดงอะไร | Drill-down |
|---|---|---|
| **Purchase Requests** | PR ที่รอการอนุมัติของผู้ใช้ปัจจุบัน (`doc_type = pr`) — Doc No, Requester, Dept, Stage, Date | → [purchase-request](/th/inventory/purchase-request) detail สำหรับแต่ละแถว |
| **Purchase Orders** | PO ที่รออนุมัติ (`doc_type = po`) — Doc No, Vendor, Amount, Stage, Date | → [purchase-order](/th/inventory/purchase-order) detail สำหรับแต่ละแถว |
| **Store Requisitions** | SR ที่รออนุมัติ (`doc_type = sr`) — Doc No, Requester, Dept, Stage, Date | → [store-requisition](/th/inventory/store-requisition) detail สำหรับแต่ละแถว |
| **Summary badge** | Total count รวมทุกประเภทจาก `useApprovalPendingSummary` | — |
| **View All** | ปรากฏเมื่อมี item อยู่ | → `/procurement/approval` (โมดูล approval เต็มรูปแบบ) |

รายการเรียงตาม `doc_date` จาก API Item ล่าสุดขึ้นก่อน widget แสดงสูงสุด `perpage: 10` item รวม; สำหรับคิวเต็มใช้ [purchase-request/my-approval](/th/inventory/purchase-request/my-approval)

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| "pending my approval" หมายถึงอะไรกันแน่? | เอกสารอยู่ที่ workflow stage ที่ role ของผู้ใช้ปัจจุบันเป็นผู้อนุมัติที่กำหนด — ถูกกำหนดโดย `workflow_current_stage` ที่ match กับ approval role ของผู้ใช้ |
| ทำไมฉันเห็น PO item ใน section PR? | ข้อมูลถูกแบ่งตาม `doc_type` บน frontend จาก API response เดียว (`root.purchase_requests`, `root.purchase_orders`, `root.store_requisitions`) ถ้า item ปะปนกัน ตรวจสอบ normalization ใน `hooks/use-approval.ts` → `normalizePR/PO/SR` |
| นี่คือ queue เดียวกับโมดูล Approval เต็มรูปแบบหรือเปล่า? | แหล่งข้อมูลเดียวกัน แต่ widget จำกัดที่ `perpage: 10` คลิก "View All" สำหรับรายการเต็มพร้อม pagination และ search |
| ทำไม total badge บอกว่า 5 แต่ฉันเห็นแค่ 3 แถว? | Summary count (`useApprovalPendingSummary` → `GET /api/proxy/api/my-approve/pending`) และ list (`useApprovalPending` → `GET /api/proxy/api/my-approve`) เป็น query แยกกันที่อาจต่างกันตามเวลา |
| การอนุมัติใน widget นี้อัปเดต count ทันทีไหม? | ไม่ใช่จาก widget นี้ — การคลิก doc-no link จะ navigate ออกไปยังหน้า detail เต็มรูปแบบ หลังอนุมัติที่นั่นแล้วกลับมา `CACHE_DYNAMIC` stale window (1 นาที) ควบคุมเวลา refresh ของ count |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| Section แสดง "No items" ทั้งที่มีเอกสาร pending ในระบบ | ผู้ใช้ปัจจุบันไม่ใช่ผู้อนุมัติที่กำหนดสำหรับเอกสารเหล่านั้น | ตรวจสอบ workflow stage → approver-role mapping ใน [system-config/workflow](/th/inventory/system-config/workflow) |
| Warning badge แสดง 0 แต่ตาราง item ไม่ว่าง | `useApprovalPendingSummary` และ `useApprovalPending` เป็น query อิสระกัน; ความต่างของเวลา | โหลดหน้าใหม่ — ทั้งคู่จะซิงค์กันภายใน `CACHE_DYNAMIC` window |
| คอลัมน์ Amount บน PO แสดง ฿0 | `total_amount` เป็น null/0 ใน API response สำหรับ PO นั้น | ตรวจสอบว่า PO line amount ถูกบันทึกอย่างถูกต้องใน [purchase-order](/th/inventory/purchase-order) |
| ลิงก์ "View All" ไม่ปรากฏ | `allItems.length === 0` — widget render link แบบมีเงื่อนไขเฉพาะเมื่อมี item | ตรวจสอบว่า approval fetch คืนข้อมูล; ดู DevTools network สำหรับ `my-approve` |
| Loading skeleton ค้างอยู่ตลอด | `useApprovalPending` query อยู่ใน loading state — `buCode` อาจ resolve ไม่สำเร็จ | ตรวจสอบ hook `useBuCode`; ตรวจสอบว่า user session มี BU context ที่ถูกต้อง |

---

## 5. แหล่งข้อมูล (Dev)

- **รายการ approval** — `GET /api/proxy/api/my-approve` (+ query param `bu_code`) → response shape: `{ data: { purchase_requests: [...], purchase_orders: [...], store_requisitions: [...] } }` Hook: `useApprovalPending({ perpage: 10 })` (`hooks/use-approval.ts`) Item ถูก normalize โดย `normalizePR`, `normalizePO`, `normalizeSR` เป็น `ApprovalItem[]`
- **Approval summary** — `GET /api/proxy/api/my-approve/pending` → `ApprovalPendingSummary { total, pr, po, sr }` Hook: `useApprovalPendingSummary` ใช้สำหรับ badge count เท่านั้น
- **API constants** (`constant/api-endpoints.ts`): `APPROVAL_PENDING = "/api/proxy/api/my-approve"`, `APPROVAL_PENDING_SUMMARY = "/api/proxy/api/my-approve/pending"`
- **ApprovalItem shape** (`types/approval.ts`): `{ id, doc_type, doc_no, doc_date, requestor_name, department_name, vendor_name, total_amount, workflow_current_stage, ... }`

## 6. จังหวะการ Refresh

`CACHE_DYNAMIC` — TanStack Query staleTime 1 นาที สำหรับทั้ง `useApprovalPending` และ `useApprovalPendingSummary` Refetch เมื่อ window focus; ไม่ poll ในพื้นหลัง หลังดำเนินการ approval ในหน้า detail กลับมายัง `/dashboard` เพื่อ trigger focus-refetch

## 7. โมดูลที่เกี่ยวข้อง

- [purchase-request/my-approval](/th/inventory/purchase-request/my-approval) — คิว approval เต็มรูปแบบพร้อม pagination, search และ approval action สำหรับ PR
- [purchase-request](/th/inventory/purchase-request) — แหล่ง transactional สำหรับ PR item
- [purchase-order](/th/inventory/purchase-order) — แหล่ง transactional สำหรับ PO item
- [store-requisition](/th/inventory/store-requisition) — แหล่ง transactional สำหรับ SR item
- [system-config/workflow](/th/inventory/system-config/workflow) — นิยาม workflow stage และ approver-role
- [dashboard/my-pending](/th/inventory/dashboard/my-pending) — widget เพิ่มเติมแสดงจำนวนเอกสาร pending ของผู้ใช้
- [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) — หน้า `/dashboard` ที่ host widget นี้

## 8. แหล่งข้อมูลอ้างอิง

- **Component:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-my-approval.tsx`
- **Hooks:** `../carmen-inventory-frontend/hooks/use-approval.ts` — `useApprovalPending`, `useApprovalPendingSummary`
- **Types:** `../carmen-inventory-frontend/types/approval.ts` — `ApprovalItem`, `ApprovalPendingSummary`, `RawApprovalPR`, `RawApprovalPO`, `RawApprovalSR`
- **API constants:** `../carmen-inventory-frontend/constant/api-endpoints.ts` → `APPROVAL_PENDING`, `APPROVAL_PENDING_SUMMARY`
- **Colour mapping:** `../carmen-inventory-frontend/constant/module-color-map.ts` → `getModuleColor`
