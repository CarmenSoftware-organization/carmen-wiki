---
title: รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Vendor
description: Flow ของ Vendor ภายในโมดูล vendor-pricelist — external party ที่มีการเข้าถึง portal-token (ไม่มี Carmen system login); เปิด ตั้งราคา save import submit; ลิงก์หมดอายุที่ end date ของ RFQ
published: true
date: '2026-09-23T01:30:00.000Z'
tags: vendor-pricelist, user-flow, vendor, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T15:00:00.000Z
---

# รายการราคาผู้ขาย (Vendor Pricelist) — User Flow — Vendor

> **At a Glance**
> **Persona:** Vendor (external — portal ที่ authenticate ด้วย token, ไม่มี Carmen login) &nbsp;·&nbsp; **โมดูล:** [vendor-pricelist](/th/inventory/vendor-pricelist)
> **Re-sync 2026-09-22:** gap เรื่อง Save/Submit ที่รายงานเมื่อ 2026-07-16 **ปิดแล้ว** — `PATCH /api/pricelist-external/:url_token` และ `POST …/:url_token/submit` มีอยู่จริง (`pricelist-external.controller.ts`), ลิงก์หมดอายุที่ `end_date` ของ RFQ (`UrlTokenGuard`) และทุก action ของ portal ถูก log ลง `tb_activity`

## 1. Role ในโมดูลนี้

**Vendor** เป็น external party ที่ไม่มี Carmen login ได้รับ email (ส่งจากแถว vendor ของ RFQ — `POST …/request-for-pricings/:id/send-email`) ที่มี link รูปแบบ `/pl/:url_token` (route `routes/external/pl/price-list-external.route.tsx` → `price-list-external-component.tsx`) โดย token คือ `pricelist_url_token` ที่ถูกสร้างสำหรับแถว invitation ของตน เมื่อ Purchaser สร้าง [Request for Pricing](/th/inventory/vendor-pricelist/request-price-list) token map ผ่านตาราง platform `tb_shot_url` ไปยัง JWT ที่บรรจุ `{ bu, vendor_id, rfp_detail_id }` และ `expired_at` เท่ากับ `end_date` ของ RFQ; `UrlTokenGuard` ของ gateway รับ token แทน Keycloak session และปฏิเสธด้วย 401 เมื่อหมดอายุ ต่างจาก pattern "ไม่มี portal เฉพาะ" ของ vendor ภายนอกในโมดูลอื่น (เช่น vendor บนโมดูล [purchase-order](/th/inventory/purchase-order)) โมดูลนี้ให้ vendor มีหน้าจริงที่อ่านและเขียน pricelist ของตนเอง

## 2. จุดเข้าและ Primary Flow

**จุดเข้า:** vendor คลิก link ใน email ของ RFQ (หรือได้รับแบบ out of band — token มองเห็นได้บนแถว vendor ของ RFQ เป็น `url_token`)

**สิ่งที่เกิดขึ้น ทีละขั้นตอน:**

1. **เปิด link** Frontend เรียก `POST /api/external/api/check-pricelist/:url_token` (`usePriceListExternal`) หลัง `UrlTokenGuard` `CheckPriceListService.checkPriceList()` lookup แถว invitation; ถ้ายังไม่มี pricelist **จะสร้างหนึ่งตัว** — `tb_pricelist` ที่ `status = draft`, `pricelist_no` จาก running code, `effective_from/to` = `start_date`/`end_date` ของ RFQ (fallback วันนี้ + `validity_period` ของ template), `url_token`, `submission_method = online` บวกแถว `tb_pricelist_detail` ราคาศูนย์หนึ่งแถวต่อสินค้าของ template × order unit / MOQ tier (dedupe ด้วย `unit::moq`) แต่ละแถวเติม tax profile ของสินค้าไว้ล่วงหน้า — และ link ไปยังแถว invitation (`pricelist_id`, `pricelist_no`) activity `create` ถูก log การเปิดครั้งถัดไป return pricelist ที่มีอยู่ token ที่หมดอายุหรือไม่รู้จักได้ 401 และหน้า render `price-list-external-expired.tsx` (*This link has expired … Contact the hotel that sent it*)
2. **เลือกตัวเลือกต่อบรรทัด** หน้าโหลด tax profile ของ BU (`GET …/check-pricelist/:url_token/tax-profiles`) และ order unit ที่อนุญาตของแต่ละสินค้า (`GET …/units` มี flag default) เพื่อให้ vendor เลือก tax profile และ unit ต่อบรรทัดในโหมด edit
3. **ตั้งราคาสินค้า** ตาราง (`price-list-external-product-table.tsx` พร้อม sub-table MOQ-tier ต่อสินค้า) ให้ vendor พิมพ์ `price_without_tax` / `price`, lead time และ note ต่อ tier หรือเพิ่มบรรทัด `(unit, MOQ)` อีกบรรทัด dialog **Import** (`price-list-external-import-dialog.tsx`) รับ sheet Excel ที่ parse ฝั่ง client (`price-list-external-excel.ts`) เข้าสู่ค่าฟอร์มเดียวกัน
4. **Save** `PATCH /api/external/api/pricelist-external/:url_token` พร้อม `{ note, pricelist_detail: { update: [...], add: [...] } }` (`useUpdatePriceListExternal`) backend ต้องการให้ pricelist ยังเป็น `draft` เขียนบรรทัด และ log `vendor.pricelist.draft_saved` พร้อม snapshot ก่อน/หลัง pricelist ยังคง `draft` ดังนั้น vendor กลับมาทำต่อได้จนกว่า link จะหมดอายุ
5. **Submit** `POST /api/external/api/pricelist-external/:url_token/submit` (`useSubmitPriceListExternal`) ต้อง `status = draft`; ลบทุกบรรทัดที่ `price IS NULL OR price <= 0` (ศูนย์คือ "ไม่เสนอราคา" ไม่ใช่ของฟรี — `price-list.zero-price.ts`), ตั้ง `status = submitted` และ `submitted_at = now()`, log activity `submit` หน้าสลับเป็นอ่านอย่างเดียว (`data.status !== "submitted"` gate control การแก้ไข); แถว RFQ ของ Purchaser ตอนนี้แสดง `has_submitted = true` พร้อมเลขที่และสถานะของ pricelist

ผลสุทธิ: submission ของ vendor เองคือ pricelist ที่ Purchaser review และ activate — ไม่ต้องคีย์ซ้ำภายในอีกต่อไป (ดู [03-user-flow-purchaser](/th/inventory/vendor-pricelist/03-user-flow-purchaser) Step 5)

## 3. สาขาการตัดสินใจ

- **ลิงก์แจ้งว่าหมดอายุ** `end_date` ของ RFQ ผ่านไปแล้ว (หรือ token ไม่รู้จัก) ฝั่ง vendor ไม่มีอะไรต่ออายุได้ — Purchaser ต้องเชิญใหม่ (RFQ ใหม่ หรือลบและเพิ่มแถว vendor อีกครั้ง) และส่ง email ใหม่
- **vendor ต้องการเปลี่ยนราคาหลัง submit** portal เป็นอ่านอย่างเดียวเมื่อ `submitted` และ backend ปฏิเสธ `saveDraft` / `submit` บน pricelist ที่ไม่ใช่ `draft` Purchaser ยังแก้ pricelist ที่ `submitted` บนหน้าจอ Price List ภายในได้ (ไม่มี immutability guard) — การเปลี่ยนแปลงจึงอยู่ฝั่งผู้ซื้อ
- **vendor ไม่ได้ขายสินค้าบางรายการที่ขอ** ปล่อยไว้ที่ `0`; จะถูกลบตอน submit แทนที่จะปรากฏเป็นข้อเสนอ ฿0 ให้ procurement
- **การ submit สาย** ไม่ใช่ business rule ใน service — deadline มีผลเพียงเพราะ token ตายที่ `end_date` (`UrlTokenGuard`); service เองไม่เคยเปรียบเทียบ `now()` กับ `end_date`
- **Reminder** ไม่มีการส่ง; `reminder_days` / `escalation_after_days` บน template ไม่มีผล

## 4. จุดออก / Handoff

- **Submit → Purchaser** pricelist ที่ `submitted` (พร้อม `submitted_at`) คือ hand-off; Purchaser review และตั้ง `status = active` บนหน้าจอ Price List vendor ไม่เห็น state ต่อจากนั้น — ไม่มี feedback loop "accepted" / "rejected"

## 5. แหล่งอ้างอิง

- ภาพรวม parent: [03-user-flow.md](./03-user-flow.md) — ฟิลด์สถานะจริงและตาราง handoff ข้าม persona ที่ยืนยันแล้ว
- กติกาทางธุรกิจ: [02-business-rules.md](./02-business-rules.md) § 5.4 (route ของ portal), `VPL_VAL_023` (submit), `VPL_VAL_027` (การหมดอายุ token), `VPL_VAL_028` (รูปแบบ save)
- Frontend: `../carmen-inventory-frontend-react/routes/external/pl/` — `price-list-external-component.tsx`, `price-list-external-product-table.tsx`, `moq-tiers-sub-table.tsx`, `price-list-external-import-dialog.tsx`, `price-list-external-excel.ts`, `price-list-external-expired.tsx`, `use-price-list-external.ts`; `types/price-list-external.ts`; `constant/api-endpoints.ts` (`PRICE_LIST_EXTERNAL`, `PRICE_LIST_EXTERNAL_CHECK`, `PRICE_LIST_EXTERNAL_TAX_PROFILES`)
- Backend: `../carmen-turborepo-backend-v2/apps/backend-gateway/src/application/pricelists/check-pricelist.controller.ts` (`POST :url_token`, `GET :url_token/tax-profiles`, `GET :url_token/units`), `pricelist-external.controller.ts` (`PATCH :url_token`, `POST :url_token/submit`), `apps/backend-gateway/src/auth/guards/url-token.guard.ts`; `apps/micro-business/src/master/check-price-list/check-price-list.service.ts` (`checkPriceList`, `saveDraft`, `submit`, `getBuTaxProfiles`, `getPricelistProductUnits`), `apps/micro-business/src/master/price-list/price-list.zero-price.ts`
- Bruno: `../carmen-turborepo-backend-bruno/collections/carmen-inventory/_uncategorized/pricelist/` — `POST-check-pricelist`, `GET-get-bu-tax-profiles`, `GET-get-pricelist-product-units`, `PATCH-save-draft`, `POST-submit`
- E2E: catalog แบบเอกสารเท่านั้น `../carmen-inventory-frontend-e2e/docs/test-cases/1002-external-price-list.md` (42 case, `TC-EPL-*`); ยังไม่มี Playwright spec
- Sibling: [03-user-flow-purchaser.md](./03-user-flow-purchaser.md) — persona ภายในที่ส่ง email ลิงก์และ activate pricelist ที่ submit แล้ว
- Cross-link: [product](/th/inventory/product) — ทุกสินค้าบนแถว detail ของ template กลายเป็นแถวราคาศูนย์บน draft ที่สร้างอัตโนมัติ
