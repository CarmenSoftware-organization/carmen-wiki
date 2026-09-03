---
title: รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Vendor
description: Flow ของ Vendor ภายในโมดูล vendor-pricelist — external party ที่มีการเข้าถึง portal-token (ไม่มี Carmen system login); confirmed gap ใน backend route ของ Save/Submit
published: true
date: 2026-07-16T00:00:00.000Z
tags: vendor-pricelist, user-flow, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Vendor

> **At a Glance**
> **Persona:** Vendor (external — portal ที่ authenticate ด้วย token, ไม่มี Carmen login) &nbsp;·&nbsp; **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist)
> **Confirmed gap (2026-07-16):** ปุ่ม Save และ Submit ของ portal เรียก backend route ที่ไม่มีอยู่จริง มีเพียง call เริ่มต้น "เปิด link" เท่านั้นที่ทำงานได้

## 1. Role ในโมดูลนี้

**Vendor** เป็น external party ที่ไม่มี Carmen login ได้รับ link รูปแบบ `/pl/:url_token` (route component `price-list-external-component.tsx`) โดย token คือ `pricelist_url_token` ที่ถูกสร้างสำหรับแถว invitation ของตน เมื่อ Purchaser สร้าง [Request for Pricing](/th/inventory/vendor-pricelist/request-price-list) ต่างจาก pattern "ไม่มี portal เฉพาะ ไม่มี state ที่คงอยู่" ของ vendor ภายนอกในโมดูลอื่น (เช่น vendor บนโมดูล [purchase-order](/th/inventory/purchase-order)) โมดูลนี้ให้ vendor มีหน้าจริงให้โต้ตอบด้วย — แต่ตามที่ยืนยันในรอบนี้ ส่วนใหญ่ของสิ่งที่หน้านั้นพยายามทำไม่ไปถึง backend endpoint ที่ทำงานได้จริง

## 2. จุดเข้าและ Primary Flow

**จุดเข้า:** Vendor คลิก link จาก invitation ของตน (ไม่ว่าจะถูกส่งมาด้วยวิธีใด — ไม่พบโค้ด email-dispatch ใน repo นี้ ดังนั้นในทางปฏิบัติ link ต้องถูกส่งแบบ out-of-band ในวันนี้ ดูสาขาการตัดสินใจ)

**สิ่งที่เกิดขึ้นจริง ทีละขั้นตอน:**

1. **เปิด link** Frontend เรียก `POST /api/check-pricelist/:url_token` (`usePriceListExternal`) ฝั่ง backend ไปถึง `CheckPricelistController` → `CheckPricelistService` → (ผ่าน microservice message `check-pricelists.check`) `CheckPriceListService.checkPricelist()` ถ้าแถว invitation ยังไม่มี pricelist link, call นี้ **จะสร้างหนึ่งตัว**: แถว `tb_pricelist` ที่ `status = draft` พร้อมแถว `tb_pricelist_detail` ราคาเป็นศูนย์หนึ่งแถวต่อสินค้าใน template (ฟิลด์ราคาทั้งหมดเป็น `0`) และ link กลับไปยังแถว invitation ถ้ามี pricelist อยู่แล้วสำหรับ token นี้ call เดียวกันจะ return มันกลับมาเฉย ๆ **นี่คือ call เดียวที่ทำงานได้ในทั้ง flow ของ vendor-portal**
2. **View/edit ใน browser** หน้าจอ render header (`PriceListExternalHeader`) และตาราง product (`PriceListExternalProductTable`) พร้อม toggle โหมด View/Edit ในโหมด edit vendor สามารถพิมพ์ราคาและ MOQ tier ลงในฟอร์ม
3. **คลิก Save** Frontend เรียก `PATCH /api/external/api/pricelist-external/:url_token` (`useUpdatePriceListExternal`) **Confirmed gap:** การค้นหาทั่ว repo `carmen-turborepo-backend-v2` สำหรับ string ตรงตัว `pricelist-external` คืนผลเป็นศูนย์ hit นอกจาก `constant/api-endpoints.ts` ของ frontend เอง ไม่มี controller, ไม่มี module, ไม่มี microservice message pattern ใดตรงกับ route นี้ Call จะล้มเหลว (path การจัดการ error ของ frontend เองถูก wire ไว้สำหรับกรณีนี้ — `mutateAsync` ที่ reject จะแสดง toast พร้อมข้อความ error จาก backend หรือ "Failed to save changes" ทั่วไปถ้า error ไม่ใช่ `HttpError`) แต่ไม่มีอะไรในโค้ด, test หรือ comment ของ frontend เองที่ flag นี่ว่าเป็นข้อจำกัดที่รู้อยู่แล้ว — มันไม่ได้เป็น placeholder "coming soon" ที่มีเอกสารเหมือน `stock-replenishment` หรือ `wastage-reporting` ในโมดูลอื่น มันอ่านเหมือน feature จริงที่ backend ครึ่งหนึ่งหายไปจาก repo snapshot นี้เฉย ๆ
4. **คลิก Submit** เรื่องเดียวกัน: frontend เรียก `POST /api/external/api/pricelist-external/:url_token/submit` (`useSubmitPriceListExternal`); ไม่มี backend route ที่ตรงกันเช่นกัน

ผลสุทธิ: vendor ที่เข้า link วันนี้สามารถ **เห็น** draft ที่สร้างอัตโนมัติ (ราคาศูนย์ทั้งหมด จนกว่า Purchaser จะกรอกบนหน้าจอ Price List ภายใน — ดู [03-user-flow-purchaser](/th/inventory/vendor-pricelist/03-user-flow-purchaser) Step 5) แต่ไม่สามารถ **persist การแก้ไขของตนเองหรือ submit** ผ่านหน้าจอนี้ใน codebase ปัจจุบัน

## 3. สาขาการตัดสินใจ

- **ถ้าการแก้ไขของ vendor ดูเหมือนจะไม่ save** นี่เป็นสิ่งที่คาดไว้ตาม confirmed gap ข้างต้น — ปัจจุบันไม่มีทางแยกแยะจากฝั่ง vendor ระหว่าง "การแก้ไขของฉันไม่ save เพราะ bug" กับ "feature นี้ยังไม่ wire" ใครก็ตามที่ทดสอบ flow นี้ไม่ควรเสียเวลาไล่หา reproduction ฝั่ง client; การแก้ไขคือ backend route ไม่ใช่ frontend
- **ราคาเข้าสู่ pricelist ที่มาจาก RFQ ได้อย่างไรในวันนี้จริง ๆ** Purchaser แก้ draft ที่สร้างอัตโนมัติโดยตรงบนหน้าจอ **Price List** ภายใน (หน้าจอเดียวกับที่ใช้สำหรับ pricelist ที่ป้อนโดยไม่มี RFQ เลย) และตั้ง `status = active` ที่นั่น
- **Invitation link ถูกส่งไปยัง vendor อย่างไรจริง ๆ** ไม่พบโค้ด email-dispatch (SMTP call, email-template render หรือ queued job) ที่ใดใน backend service ของโมดูลนี้ — `create()` บน RFQ สร้าง token และ JWT แต่ไม่ส่งอะไรออกไป ในทางปฏิบัติ การส่ง link เป็นขั้นตอน manual แบบ out-of-band ในวันนี้ (เช่น copy จาก create-response payload) ไม่ใช่ invitation email อัตโนมัติ

## 4. จุดออก / Handoff

- **การเข้า Portal → Purchaser** Action เดียวที่ทำงานได้ของ vendor (การเปิด link) ส่ง draft pricelist ใหม่ไปยัง Purchaser ผู้ทำการป้อนข้อมูลจริงและ activate วันนี้ไม่มีการเปลี่ยน state เพิ่มเติมที่ vendor ขับ

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — ฟิลด์สถานะจริงและตาราง handoff ข้าม persona ที่ยืนยันแล้ว
- กติกาทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) § 5.4 — confirmed gap เดียวกัน อ้างอิงร่วมกับกติกาสถานะอื่นของโมดูล
- Frontend: `../carmen-inventory-frontend-react/routes/external/pl/price-list-external-component.tsx`, `hooks/use-price-list-external.ts`, `constant/api-endpoints.ts` (`PRICE_LIST_EXTERNAL`, `PRICE_LIST_EXTERNAL_CHECK`)
- Backend (call ที่ทำงานได้เท่านั้น): `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/pricelists/check-pricelist.controller.ts` + `check-pricelist.service.ts`; `apps/micro-business/src/master/check-price-list/check-price-list.controller.ts` + `check-price-list.service.ts`
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ภายในที่ทำการป้อนราคาจริงบน draft ที่สร้างอัตโนมัติ
- Cross-link: [product](/th/inventory/product) — ทุกสินค้าบนแถว detail ของ template กลายเป็นแถวราคาศูนย์บน draft ที่สร้างอัตโนมัติ
