---
title: Widget My Pending แดชบอร์ด (My Pending Dashboard Widget)
description: widget นับจำนวนเอกสาร pending ส่วนตัวบน /dashboard แสดงจำนวนร่างหรือเอกสารที่อยู่ระหว่างดำเนินการที่รอการทำงานของผู้ใช้ที่ล็อกอิน ครอบคลุม PR, PO และ SR
published: true
date: 2026-06-04T00:00:00.000Z
tags: dashboard, my-pending, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Widget My Pending แดชบอร์ด (My Pending Dashboard Widget)

> **At a Glance**
> **Route:** `/dashboard` (widget — ไม่ใช่ route แบบ standalone) &nbsp;·&nbsp; **สำหรับ:** Requester &nbsp;·&nbsp; Purchaser &nbsp;·&nbsp; Store Manager &nbsp;·&nbsp; **สถานะ:** **Live** — API endpoint จริง; hook mount แล้วและคืนค่า count จริง &nbsp;·&nbsp; **ขอบเขต:** ส่วนบุคคล — count ผูกกับผู้ใช้ที่ล็อกอินเท่านั้น

## 1. คืออะไรและสำหรับใคร

Section **My Pending** คือ widget ที่ render อยู่ภายในหน้า `/dashboard` แสดงแถว card นับสามใบที่มีสี — หนึ่งใบต่อประเภทเอกสาร (PR / PO / SR) — แต่ละใบแสดงจำนวนเอกสารในสถานะ pending ที่เป็นของผู้ใช้ปัจจุบัน การคลิก card จะ navigate ไปยังโมดูล transactional ที่เกี่ยวข้อง

**Layout:** สาม card ในกริด responsive (1 col → 2 col → 3 col) แต่ละ card มี:
- ขอบซ้ายสี (module colour จาก `module-color-map.ts`)
- ไอคอนประเภทเอกสาร (FileText / ShoppingCart / ClipboardList)
- ตัวเลขนับ + label "pending"
- ไอคอน arrow-right มองเห็นเมื่อ hover

**กลุ่มผู้ใช้**

- **Requester** — เห็น PR ร่างที่ค้างอยู่และ PR ที่ submit แล้วที่ยังอยู่ใน workflow
- **Purchaser** — เห็น PO ที่รอการดำเนินการ
- **Store Manager / Store Staff** — เห็นเอกสาร SR ที่รอการประมวลผล

## 2. Tile และการ Drill-down

| Card | แสดงอะไร | Drill-down |
|---|---|---|
| **Purchase Requests** | จำนวน PR ของผู้ใช้ที่ pending (`prCount.pending`) | → [purchase-request](/th/inventory/purchase-request) รายการ (pending ของตัวเอง) |
| **Purchase Orders** | จำนวน PO ของผู้ใช้ที่ pending (`poCount.pending`) | → [purchase-order](/th/inventory/purchase-order) รายการ (pending ของตัวเอง) |
| **Store Requisitions** | จำนวน SR ของผู้ใช้ที่ pending (`srCount.pending`) | → [store-requisition](/th/inventory/store-requisition) รายการ (pending ของตัวเอง) |

Pending หมายถึงเอกสารที่ยังไม่ถึงสถานะ terminal (received / completed / cancelled) ขอบเขต stage ที่แน่นอนถูกนิยามโดย backend query เบื้องหลัง endpoint count แต่ละตัว

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| "pending" สำหรับ PR หมายถึงอะไร? | PR ใดก็ตามที่เป็นของผู้ใช้ปัจจุบันที่ไม่อยู่ในสถานะ terminal backend count endpoint นิยามขอบเขตนี้ — ตรวจสอบ `GET /api/proxy/api/my-pending/purchase-requests/count` |
| count รวมเอกสารที่ฉัน submit แล้วและตอนนี้อยู่กับผู้อนุมัติด้วยไหม? | ใช่ — pending หมายถึงเอกสารยังไม่ถึงสถานะ terminal โดยไม่คำนึงถึงว่าใครเป็นคนต้องดำเนินการต่อ |
| ทำไม count ของฉันแสดง 0 ทั้งที่มีเอกสารเปิดอยู่? | ตรวจสอบว่าเข้าระบบด้วย user ที่ถูกต้อง Count เป็นส่วนตัวอย่างเคร่งครัด (`requestor_id = current_user`) ถ้ายังเป็น 0 endpoint อาจคืน cache เก่า — รอ 1 นาทีเพื่อให้ `CACHE_DYNAMIC` หมดอายุหรือ refresh หน้า |
| "My Pending" เหมือนกับคิว Awaiting Approval ไหม? | ไม่ใช่ "My Pending" นับเอกสารที่ **ผู้ใช้ปัจจุบันเป็นผู้ขอ/เจ้าของ** คิว Awaiting Approval (ดู [dashboard/my-approval](/th/inventory/dashboard/my-approval)) แสดงเอกสารที่ผู้ใช้ปัจจุบันเป็น **ผู้อนุมัติต่อไป** |
| ฉันดูเอกสาร pending ของ user อื่นได้ไหม? | ไม่ได้ widget นี้ scope อย่างเคร่งครัดกับ `current_user` เท่านั้น สำหรับ visibility ระดับทีม ใช้แดชบอร์ดโดเมนหรือหน้ารายการ transactional |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| ทั้งสาม count แสดง 0 ผิดพลาด | Hook mount แล้วแต่ API คืน error เงียบๆ | เปิด browser DevTools → Network tab, กรองด้วย `my-pending` — ตรวจ 4xx/5xx |
| Count ไม่ลดลงหลังฉัน complete เอกสาร | `CACHE_DYNAMIC` staleTime เป็น 1 นาที | รอ 60 วินาทีหรือ navigate ออกแล้วกลับมาเพื่อ trigger refetch-on-focus |
| คลิก count card navigate แต่รายการไม่ถูก filter | Drill-down link ไปยัง module root; ไม่มี filter query param ส่งไปในปัจจุบัน | Navigate ด้วยตนเองภายในโมดูลเพื่อใช้ filter pending |
| SR count card หายไป | Component ข้าม card ถ้า hook ส่ง error | ตรวจ `useMyPendingSrCount` — ยืนยันว่า endpoint `MY_PENDING_STORE_REQUISITIONS_COUNT` เข้าถึงได้ |

---

## 5. แหล่งข้อมูล (Dev)

- **PR count** — `GET /api/proxy/api/my-pending/purchase-requests/count` → `{ pending: number }` Hook: `useMyPendingPrCount` (`hooks/use-dashboard.ts`) Query key: `MY_PENDING_PURCHASE_REQUESTS_COUNT`
- **PO count** — `GET /api/proxy/api/my-pending/purchase-orders/count` → `{ pending: number }` Hook: `useMyPendingPoCount` Query key: `MY_PENDING_PURCHASE_ORDERS_COUNT`
- **SR count** — `GET /api/proxy/api/my-pending/store-requisitions/count` → `{ pending: number }` Hook: `useMyPendingSrCount` Query key: `MY_PENDING_STORE_REQUISITIONS_COUNT`

ทั้งสาม hook ใช้ `CACHE_DYNAMIC` (staleTime 1 นาที) path endpoint ลงทะเบียนใน `constant/api-endpoints.ts`

หมายเหตุ: path endpoint เดียวกันนี้ใช้ใน sidebar badge count — hook เดียวกันถูก reuse ข้าม widget และ sidebar โดยไม่มีการ fetch แยก

## 6. จังหวะการ Refresh

`CACHE_DYNAMIC` — TanStack Query staleTime 1 นาที Refetch เมื่อ window focus; ไม่ poll ในพื้นหลัง Count จะอัปเดตภายใน 1 นาทีหลังการเปลี่ยนสถานะเอกสาร (หรือทันทีหลัง forced refresh)

## 7. โมดูลที่เกี่ยวข้อง

- [purchase-request](/th/inventory/purchase-request) — โมดูล transactional สำหรับ PR; แหล่ง pending-count
- [purchase-order](/th/inventory/purchase-order) — โมดูล transactional สำหรับ PO; แหล่ง pending-count
- [store-requisition](/th/inventory/store-requisition) — โมดูล transactional สำหรับ SR; แหล่ง pending-count
- [dashboard/my-approval](/th/inventory/dashboard/my-approval) — widget เพิ่มเติมแสดงเอกสารที่รอการอนุมัติของผู้ใช้
- [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) — หน้า `/dashboard` ที่ host widget นี้

## 8. แหล่งข้อมูลอ้างอิง

- **Component:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-my-pending.tsx`
- **Hooks:** `../carmen-inventory-frontend/hooks/use-dashboard.ts` — `useMyPendingPrCount`, `useMyPendingPoCount`, `useMyPendingSrCount`
- **API constants:** `../carmen-inventory-frontend/constant/api-endpoints.ts` → `MY_PENDING_PURCHASE_REQUESTS_COUNT`, `MY_PENDING_PURCHASE_ORDERS_COUNT`, `MY_PENDING_STORE_REQUISITIONS_COUNT`
- **Colour mapping:** `../carmen-inventory-frontend/constant/module-color-map.ts` → `getModuleColor`
- **Cache config:** `../carmen-inventory-frontend/lib/cache-config.ts` → `CACHE_DYNAMIC`
