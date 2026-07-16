---
title: Widget My Pending แดชบอร์ด (My Pending Dashboard Widget)
description: "ถูกลบแล้ว เก็บไว้เป็นข้อมูลอ้างอิงเชิงประวัติศาสตร์เท่านั้น — ไม่เคยถูก render บน /dashboard จริง: widget นับจำนวนเอกสาร pending ส่วนตัวที่เสนอไว้ แสดงจำนวนร่างหรือเอกสารที่อยู่ระหว่างดำเนินการที่รอการทำงานของผู้ใช้ที่ล็อกอิน ครอบคลุม PR, PO และ SR"
published: true
date: 2026-07-16T01:35:43.000Z
tags: dashboard, my-pending, kpi, carmen-software
editor: markdown
dateCreated: 2026-06-04T00:00:00.000Z
---

# Widget My Pending แดชบอร์ด (My Pending Dashboard Widget)

> **At a Glance**
> **Route:** ไม่มี — ไม่เคยถูก render ที่ไหนเลย &nbsp;·&nbsp; **สถานะ:** **ถูกลบเมื่อ 2026-06-27; เป็น dead code อยู่แล้วตั้งแต่ก่อนหน้านั้น** — widget นี้ไม่เคยถูก mount บนหน้า `/dashboard` จริง แม้หน้านี้จะเคยอ้างสถานะ "Live" ไว้ก่อนหน้านี้ก็ตาม

## สถานะการ implement (ตรวจสอบเมื่อ 2026-07-16)

**การอ้างสถานะ "Live" ของหน้านี้ก่อนหน้านี้ผิด** หน้านี้ document `dashboard-my-pending.tsx` (เดิมคือ `routes/dashboard/_components/dashboard-my-pending.tsx`) ซึ่ง render card นับสามใบตามที่อธิบายด้านล่าง เมื่อตรวจสอบ `dashboard-component.tsx` (ทั้งเวอร์ชันปัจจุบันและเวอร์ชันก่อน cleanup 2026-06-27) พบว่าหน้า `/dashboard` จริงมี render แค่ header ทักทายกับกริด "Saved Widgets" เท่านั้นมาโดยตลอด — ไม่เคย import หรือ mount `dashboard-my-pending.tsx` เลย hook ที่อยู่เบื้องหลัง (`useMyPendingPrCount`, `useMyPendingPoCount`, `useMyPendingSrCount` ใน `hooks/use-dashboard.ts`) ยังคงอยู่ใน source code ปัจจุบัน และ endpoint ของมัน (`GET /api/proxy/api/my-pending/{purchase-requests,purchase-orders,store-requisitions}/count`) ยังถูกประกาศไว้ใน `constant/api-endpoints.ts` แต่การค้นหาทั่วทั้ง repo พบว่า **ไม่มี call site เลยแม้แต่แห่งเดียว** สำหรับ hook ทั้งสาม — ไม่ใช่บน `/dashboard`, ไม่ใช่ใน sidebar, ไม่มีที่ไหนเลย ไฟล์ component เองถูกลบพร้อมไฟล์พี่น้องอีก 7 ไฟล์ใน commit `03891e3d` ("refactor(dashboard): convert to idiomatic structure, drop dead demo code", 2026-06-27) ซึ่ง commit message ยืนยันว่าเป็น dead code ที่ "no importers anywhere"

เนื้อหาด้านล่างทั้งหมดอธิบาย widget ที่ไม่เคยถูก mount และถูกลบไปแล้วนี้ — เก็บไว้เป็นข้อมูลอ้างอิงเชิงประวัติศาสตร์เท่านั้น ถือว่าทุกข้อความ "Live" / "mount แล้ว" / การอ้าง route ในส่วนที่เหลือของหน้านี้เป็นโมฆะ

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

- [purchase-request](/th/inventory/purchase-request), [purchase-order](/th/inventory/purchase-order), [store-requisition](/th/inventory/store-requisition) — โมดูล transactional ที่ hook นับ count (ซึ่งไม่ถูก mount) จะ query
- [dashboard/my-approval](/th/inventory/dashboard/my-approval) — widget พี่น้องที่มีชะตากรรมเดียวกัน (ไม่เคยถูก mount ตอนนี้ถูกลบแล้ว)
- [dashboard/widget-workspace](/th/inventory/dashboard/widget-workspace) — หน้า `/dashboard` จริงที่ live; หน้านี้**ไม่ได้** host widget นี้ และไม่เคย host เลย

## 8. แหล่งข้อมูลอ้างอิง

- **Component (ถูกลบเมื่อ 2026-06-27):** `routes/dashboard/_components/dashboard-my-pending.tsx` ใน `../carmen-inventory-frontend-react`
- **Commit ที่ลบ:** `03891e3d` — "refactor(dashboard): convert to idiomatic structure, drop dead demo code"
- **Hooks (ยังอยู่ แต่ไม่พบ call site เลย):** `../carmen-inventory-frontend-react/hooks/use-dashboard.ts` — `useMyPendingPrCount`, `useMyPendingPoCount`, `useMyPendingSrCount`
- **API constants (ยังประกาศอยู่ แต่ไม่ถูกใช้):** `../carmen-inventory-frontend-react/constant/api-endpoints.ts` → `MY_PENDING_PURCHASE_REQUESTS_COUNT`, `MY_PENDING_PURCHASE_ORDERS_COUNT`, `MY_PENDING_STORE_REQUISITIONS_COUNT`
- **Colour mapping:** `../carmen-inventory-frontend-react/constant/module-color-map.ts` → `getModuleColor`
- **Cache config:** `../carmen-inventory-frontend-react/lib/cache-config.ts` → `CACHE_DYNAMIC`
