---
title: แดชบอร์ดใบเบิกของสโตร์ (SR Dashboard)
description: ห้องนักบินใบเบิกของสโตร์ — pipeline สี่ stage, รายการ send-back / reject, ตารางรออนุมัติแบ่งช่วงเวลา, กราฟการบริโภคส่วนตัวเทียบกับแผนก, SR รอรับ และทางลัด template
published: true
date: 2026-05-17T07:00:36.000Z
tags: dashboard, store-requisition, kpi, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# แดชบอร์ดใบเบิกของสโตร์ (SR Dashboard)

> **At a Glance**
> **Route:** `/dashboard/sr` &nbsp;·&nbsp; **สำหรับ:** Requester / Store Staff &nbsp;·&nbsp; HOD / Approver &nbsp;·&nbsp; Dept Manager &nbsp;·&nbsp; **สถานะ:** **ยังเป็น mock data ในปัจจุบัน**; การ wire จริงรอ

![แดชบอร์ดใบเบิกของสโตร์ (SR Dashboard) screen](/assets/screenshots/dashboard/sr.png)

## 1. คืออะไรและสำหรับใคร

หน้าทำงานของ Requester สำหรับการโอนสต๊อกระหว่าง location ตอบคำถาม *"ฉันขออะไรไป, อะไรกำลังตีกลับ, อะไรกำลังรออนุมัติ, และปกติฉันบริโภคอะไร?"*

**Layout:** แถบ pipeline 4 tile (Requested / In Process / Approved / Issued) → คอลัมน์ซ้ายมี 3 ตารางซ้อน (Sent Back, Reject List, Awaiting Approval พร้อม tab วันนี้/สัปดาห์/เดือน) → คอลัมน์กลางมี donut My Consumption + รายการ SR Awaiting Received → คอลัมน์ขวามี bar การบริโภคของแผนก + รายการทางลัด "My Templates" Footer strip แสดง version และตัวตนผู้ใช้ที่ล็อกอิน — แสดงเฉพาะหน้านี้

**กลุ่มผู้ใช้**

- **Requester / Store Staff** — หลัก เฝ้าดู Sent Back (Bulk Submit), ใช้ My Templates, ติดตาม SR Awaiting Received
- **HOD / Approver** — ใช้ตาราง Awaiting Approval พร้อม tab ช่วงวันเป็นคิวงาน
- **Department Manager** — เฝ้าดู Dept Consumption สำหรับเทรนด์ระดับหมวด

## 2. Tile และการ Drill-down

| Tile | แสดงอะไร | Drill-down (เมื่อ live) |
|---|---|---|
| **SR Summary (Pipeline)** | 4 stage: Requested / In Process / Approved / Issued — จำนวน + sub-label | → [[store-requisition]] กรองตาม stage |
| **Sent Back SRs** | SR#, Requester, Date Sent, Sender, Reason + ปุ่ม **Bulk Submit** | → [[store-requisition]] detail; bulk action re-submit |
| **Reject List (SR & รายการ)** | SR#, Material, Requester, Rejected By, Reason | → [[store-requisition]] detail |
| **SR รออนุมัติ** | PR No, Description, Amount, Stage — tab วันนี้ / สัปดาห์ / เดือน | → [[store-requisition]] detail |
| **การบริโภคของฉัน (ส่วนตัว)** | Donut + total ตรงกลาง + legend 3 ส่วน | — |
| **SR รอรับ** | scrollable: PR No, Description, Amount | → [[store-requisition]] receipt view |
| **การบริโภคของแผนก (F&B Dept)** | bar แนวนอน + legend | — |
| **My Templates** | รายการปุ่มชื่อ template SR ที่บันทึกไว้ — คลิกเพื่อโหลด template | → [[store-requisition]] ใหม่พร้อม template |
| **Footer** | version, user, role, timestamp | — (hard-code ใน `dashboard-sr.tsx`) |

label ของคอลัมน์ header อ่านว่า "PR No" / "PR Number" ในตาราง SR — เป็น artefact จากการคัดลอกจาก mock ของ PR dashboard คอลัมน์จริงอ้างถึงเลขเอกสาร SR **(Inferred — ต้องยืนยันกับ UI จริง; แจ้งทีม frontend)**

## 3. คำถามที่พบบ่อย

| คำถาม | คำตอบ |
|---|---|
| ทำไมคอลัมน์ขึ้น "PR No" ในตาราง SR? | **Mock data copy/paste artefact** จาก fixture ของ PR dashboard คอลัมน์จริงคือเลขเอกสาร SR แจ้งทีม frontend |
| "Bulk Submit" บน Sent Back re-submit จริงไหม? | (Inferred — ต้องยืนยันกับ UI จริง) Mock ไม่มี handler; wire จริงควร batch re-submit ผ่าน workflow ของ [[store-requisition]] |
| tab วันนี้ / สัปดาห์ / เดือน ต่างกันอย่างไร? | query เดียวกัน (`useApprovalPending({ doc_type: "sr" })`), filter window ของ `doc_date` ต่างกัน |
| "My Templates" เก็บที่ไหน? | TBD — น่าจะ `tb_sr_template` keyed ด้วย `user_id` schema ยังไม่ final |
| "My Consumption" คำนวณอย่างไร? | sum บน inventory ที่บริโภคแล้ว (recipe + wastage + manual) ที่ `requestor_id = current_user` จัดกลุ่มตาม [[product/category]] |
| อะไรเข้า "SR Awaiting Received"? | [[store-requisition]] ที่ `status = "issued"` AND `destination_location_id IN (location ของ user)` AND ยังไม่ receipt |

## 4. การแก้ปัญหา

| อาการ | สาเหตุ | การดำเนินการ |
|---|---|---|
| จำนวน pipeline stage ไม่ตรงกับรายการ [[store-requisition]] | Mock fixture ไม่ใช่ live | จะถูกแก้เมื่อ `useApprovalPending` ถูก mount |
| คลิก "Bulk Submit" ไม่มีอะไรเกิดขึ้น | ยังไม่ wire handler ในบิลด์ปัจจุบัน | (Inferred — ต้องยืนยันกับ UI จริง) |
| "My Templates" ว่างหรือแสดง template ของคนอื่น | Mock fixture เป็น global ไม่ scope user | wire จริงกรองด้วย `user_id` |
| Donut แสดง `$` ไม่ใช่ `฿` | Mock fixture currency quirk | production localise ไปยังสกุลเงินฐานของ BU |
| สลับ tab Awaiting Approval แสดง row เดิม | array mock ต่างกัน แต่ state binding อาจ regress | ตรวจสอบ `awaitingSrsToday` / `awaitingSrsWeek` / `awaitingSrsMonth` ใน `mock/sr.ts` |

---

## 5. แหล่งข้อมูล (Dev)

- **Pipeline counts** — group-count บน [[store-requisition]] ตาม workflow stage โดย project `workflow_current_stage` ไปยัง 4 bucket
- **Sent Back / Reject List** — `workflow_action_history` กรองเป็น send-back / reject join กลับไป [[store-requisition]]
- **Awaiting Approval** — `useApprovalPending({ doc_type: "sr" })` (`hooks/use-approval.ts`); tab ต่างกันที่ filter `doc_date`
- **My Consumption** — sum inventory ที่บริโภคแล้ว (recipe + wastage + manual) ที่ `requestor_id = current_user` จัดกลุ่มตาม [[product/category]]
- **SR Awaiting Received** — [[store-requisition]] ที่ `status = "issued"` AND `destination_location_id IN (location ของ user)` AND ยังไม่ receipt
- **Dept Consumption** — query เดียวกับ My Consumption แต่ scope ด้วย `department_id` ไม่ใช่ `requestor_id`
- **My Templates** — template SR ที่ user บันทึก (table TBD; น่าจะ `tb_sr_template` keyed ด้วย `user_id`)

## 6. จังหวะการ Refresh

mock แบบ static ในปัจจุบัน "Awaiting Approval" tab และ "Sent Back" / "Reject List" ควร refresh on focus เมื่อ wire แล้ว — `CACHE_DYNAMIC` (1-min stale) กราฟการบริโภคใช้ `CACHE_NORMAL` (5-min) ได้

## 7. โมดูลที่เกี่ยวข้อง

- [[store-requisition]] — ระบบบันทึก transactional เบื้องหลังทุก tile
- [[store-requisition/stock-replenishment]] — SR ตัวแปรที่ระบบสร้างให้ ซึ่งอาจปรากฏใน pipeline
- [[inventory]] — รองรับ aggregate การบริโภคและ flow รอรับ
- [[purchase-request]] — เอกสารพี่น้องที่ใช้ framework การอนุมัติร่วมกัน

## 8. แหล่งข้อมูลอ้างอิง

- **Page shell:** `../carmen-inventory-frontend/app/(root)/dashboard/sr/page.tsx`
- **Composition:** `../carmen-inventory-frontend/app/(root)/dashboard/_components/dashboard-sr.tsx`
- **Mock data:** `../carmen-inventory-frontend/app/(root)/dashboard/mock/sr.ts` (รวม type `AwaitingTab`)
- **i18n:** `messages/en.json` → `dashboard.sr.title` = "Store Requisition Dashboard"
- **Live hook (ยังไม่ mount):** `../carmen-inventory-frontend/hooks/use-approval.ts` → `useApprovalPending`
