---
title: การนับสต๊อกประจำงวด (Physical Count) — Data Model
description: เอนทิตี ฟิลด์ ความสัมพันธ์ และ enum ของโมดูลการนับสต๊อกประจำงวด
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, data-model, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Data Model

> **At a Glance**
> **ตาราง:** `tb_physical_count_period` &nbsp;·&nbsp; `tb_physical_count` &nbsp;·&nbsp; `tb_physical_count_detail` &nbsp;·&nbsp; ตาราง `_comment` ต่อระดับ (สามตาราง)
> **กลุ่มผู้ใช้:** นักพัฒนา / ผู้ตรวจสอบ (อ้างอิงเชิงพัฒนา)
> **FK สำคัญ:** period `→ tb_period`; count `→ tb_location` และ `→ tb_physical_count_period`; detail `→ tb_product` และ `→ tb_unit` (`inventory_unit_id`) การเชื่อม variance rollup ไปยัง [inventory-adjustment](/th/inventory/inventory-adjustment) **ไม่มี FK และไม่มีฟิลด์เชื่อม JSON เลย** — row `tb_stock_in`/`tb_stock_out` ที่สร้างขึ้นพกพาแค่ข้อความ description แบบ human-readable ที่ใช้ร่วมกัน
> **รูปแบบการตรวจสอบ:** มาตรฐาน `created_*` / `updated_*` / `deleted_*`; ลำดับชั้นสามระดับ (period → document → detail) — การนับเองไม่เขียนลง inventory ledger; rollup ตอน submit สุดท้ายสร้างเอกสาร stock-in/out ที่ `completed` แล้วซึ่งก็ไม่เขียนลง ledger เช่นกัน (ดู § 3)

> **Source of truth:** Prisma schema ฝั่ง backend รวมถึง service method ที่อ่าน/เขียนมัน อ่านทั้งสองอย่างก่อนเสมอเมื่ออัปเดตหน้านี้:
> - `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma`
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts`
> - `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count-period/physical-count-period.service.ts`
>
> ไฟล์ `generated/client/schema.prisma` ใน package เป็น copy ที่ auto-generate และไม่ถือเป็น authoritative

## 1. ภาพรวม

โมดูล Physical Count persist ต้นไม้เอกสารสามระดับภายใต้ลำดับชั้น **`tb_physical_count_period` → `tb_physical_count` → `tb_physical_count_detail`**: period header รวบรวมเอกสารการนับทุกฉบับที่เปิดในงวดบัญชีเดียวกัน (`tb_period`) แต่ละเอกสาร count แทนการจับคู่หนึ่ง `(period, location)` และแต่ละ row ของ detail คือหนึ่งบรรทัดสินค้าบนการนับนั้น โดยมี `on_hand_qty` (book), `actual_qty` (counted) และ `diff_qty` (variance) Comment และ attachment ห้อยอยู่บนทั้งสามระดับ (`tb_physical_count_period_comment`, `tb_physical_count_comment`, `tb_physical_count_detail_comment`); ตาราง comment ระดับ detail คือตัวเดียวที่ live UI ใช้งานจริง ผ่าน dialog "Add Notes" ต่อบรรทัดบนหน้า entry (photo + ข้อความอิสระ)

โมดูลอยู่ **เหนือ [inventory-adjustment](/th/inventory/inventory-adjustment)** เพียงในชื่อ: เมื่อการ **Submit** สุดท้ายของเอกสารการนับยิง (`physical-count.service.ts` `submit()`) service จะ insert บรรทัด variance โดยตรงเข้า row `tb_stock_in` (overage) และ/หรือ `tb_stock_out` (shortage) ใหม่ — แต่ทำผ่าน Prisma transaction ดิบ ๆ ที่ไม่เคย import หรือเรียก `InventoryTransactionService`, `executeAdjustmentIn`, หรือ `executeAdjustmentOut` ซึ่งเป็น helper ที่ `stock-in.service.ts`/`stock-out.service.ts` เรียกทุกครั้งสำหรับบรรทัด detail ของตัวเอง ผลที่ตามมาโดยตรง: ไม่มี row `tb_inventory_transaction` ถูกสร้างโดย rollup นี้ `adjustment_type_id` ถูกปล่อยเป็น `null` บน header ทั้งสองที่สร้างขึ้น (ไม่มี reason code) และไม่มีฟิลด์ `info` JSON ของทั้ง header หรือบรรทัด detail ใดถูกใส่ back-reference กลับไปยัง `tb_physical_count.id` ต้นทาง — ร่องรอยเดียวที่เชื่อมสองเอกสารเข้าด้วยกันคือข้อความ description แบบ human-readable ที่ใช้ร่วมกัน (`"Physical Count Adjustment - Period: <start> to <end>"`) และข้อความ `note` ต่อบรรทัด ข้อมูล lot บน count detail บางเบา — `tb_physical_count_detail` พกพาเพียง `on_hand_qty` / `actual_qty` ต่อสินค้าต่อสถานที่ (ไม่มีคอลัมน์ `lot_no`) — และเนื่องจาก rollup ไม่เคยไปถึง code path ของ inventory-transaction/cost-layer เลย จึงไม่มี lot ใดถูกสร้างหรือบริโภคโดยการนับสต๊อกประจำงวดใน implementation ปัจจุบัน

## 2. เอนทิตี

Prisma schema canonical กำหนดหกตาราง (ตรวจสอบกับ `prisma-shared-schema-tenant/prisma/schema.prisma` บรรทัด 5370–5537):

- **`tb_physical_count_period`** — header ระดับ period จัดกลุ่มเอกสารการนับทั้งหมดสำหรับหนึ่งงวดบัญชี (`period_id → tb_period`) พกพา `status` บน `enum_physical_count_period_status` (`draft`, `counting`, `completed`) default เป็น `draft` **ช่องว่างที่ยืนยันแล้ว:** ไม่พบ code path ใดทั้ง frontend หรือ backend ที่ตั้งค่าฟิลด์นี้เป็น `counting` เลย — `findCurrent()` ของ `physical-count-period.service.ts` (ที่หน้ารายการใช้) auto-create period ที่ขาดไปที่ `status: draft` และ `create()` ของ `physical-count.service.ts` reject แบบไม่มีเงื่อนไขด้วย `"Physical Count Period is not in counting status"` เว้นแต่ period จะเป็น `counting` อยู่แล้ว วิธีเดียวที่ period จะถึง `counting` ดูเหมือนคือการเรียก `POST /physical-count-periods` โดยตรงพร้อมตั้งค่า `status` ใน request body เอง — Bruno sample body ของ endpoint นั้นเองยังส่ง `"status": null` (ซึ่ง fallback ไป `draft`) และไม่มีหน้าจอ frontend ใดที่เรียก create/update hook ของ endpoint นี้เลย (`useCreatePhysicalCountPeriod`/`useUpdatePhysicalCountPeriod` ถูก export แต่ไม่มี route ใดใช้) Flag ไว้ใน progress log เป็นช่องว่างที่ยังไม่ยืนยันแทนที่จะยืนยันเป็น defect แน่นอน เพราะ tenant ที่ seed มาก่อนอาจมี period ที่ `counting` อยู่แล้ว
- **`tb_physical_count_period_comment`** — comment / attachment ระดับ period พกพา `message`, JSON array ของ `attachments` และ `enum_comment_type` (`user` / `system`) ไม่มี UI ใน frontend ปัจจุบันที่แสดง comment ระดับ period
- **`tb_physical_count`** — เอกสารการนับสำหรับหนึ่งคู่ `(period, location)` พกพา `location_id → tb_location`, snapshot `location_code` / `location_name`, `physical_count_type` (`enum_physical_count_type`, schema default `yes` แต่ไม่เคยถูกตั้งค่าโดย `create()` เลย — ทุกเอกสารที่สร้างผ่าน flow จริงคงค่า default นี้ไว้; ไม่มี behavioural branch ของ frozen-vs-live ใด ๆ ในโค้ด ดู [physical-count](/th/inventory/physical-count) § 3), `description`, `status` บน `enum_physical_count_status` (`pending`, `in_progress`, `completed` — `create()` ตั้งเอกสารใหม่ไปที่ `in_progress` ตรง ๆ ดังนั้น `pending` จึงเข้าถึงไม่ได้ผ่าน create path ที่ยืนยันแล้ว มันถูกอ้างอิงเพียงเป็นส่วนหนึ่งของ filter รวม `{pending, in_progress}` ใน query widget dashboard "pending count" ข้าม BU), `start_counting_at` / `start_counting_by_id` (stamp ทันทีตอนสร้าง ไม่ใช่ตอน counter ป้อนบรรทัดแรก), `completed_at` / `completed_by_id`, ตัวนับความคืบหน้า `product_counted` / `product_total`, และ `doc_version` (`Int @db.Integer`, default `0`) — ตัวนับเวอร์ชันสำหรับ optimistic-concurrency ที่จำเป็นในทุก call `save`/`update`/`review`/`submit`; ค่าไม่ตรงจะถูกแปลงเป็นผล `ALREADY_EXISTS` แบบ `409` โดย decorator `@TryCatch` ที่ใช้ร่วมกัน (ดู [system-config/doc-version](/th/inventory/system-config/doc-version)) Unique ภายใน `(physical_count_period_id, location_id, deleted_at)`
- **`tb_physical_count_comment`** — comment / attachment ระดับเอกสารบน count ไม่มี UI ใน frontend ปัจจุบันที่แสดง comment ระดับเอกสาร (มีเฉพาะระดับ detail ดูด้านล่าง)
- **`tb_physical_count_detail`** — บรรทัดการนับต่อสินค้า พกพา `product_id`, snapshot `product_code` / `product_name` / `product_local_name` / `product_sku`, `inventory_unit_id` (FK ไปยัง `tb_unit`), `on_hand_qty` (seed `0` ตอนสร้าง; คำนวณใหม่เป็นค่าสดเฉพาะโดยขั้นตอน **Submit for Review**, `reviewItems()` — ดู [physical-count](/th/inventory/physical-count) § 3), `actual_qty` (seed `null`; ตั้งค่าโดย **Save** หรือถูกเขียนทับโดย **Submit for Review**), `diff_qty` (`actual_qty − on_hand_qty`), `counted_at` / `counted_by_id` (stamp **เฉพาะ** โดย call **Save** เท่านั้น ไม่ใช่โดย Submit for Review — ดู discrepancy note ใน [physical-count](/th/inventory/physical-count) § 3), และ `sequence_no` สำหรับลำดับบน sheet
- **`tb_physical_count_detail_comment`** — comment / attachment ระดับบรรทัดบน row ของ count detail นี่คือตาราง comment ตัวเดียวที่ live UI ใช้งานจริง: dialog "Add Notes" ต่อบรรทัดบนหน้า entry (`pc-entry-notes-dialog.tsx`) อ่าน/เขียนผ่าน `GET`/`POST /physical-count-detail-comments/:detailId` เก็บข้อความอิสระพร้อมรูปแนบ

## 3. ความสัมพันธ์

```
tb_period
    │
    └─1──*──► tb_physical_count_period  (status: draft → counting → completed;
                │                          ไม่พบ code path ที่ยืนยันแล้วที่ตั้งค่า counting — ดู § 2)
                │
                ├─1──*──► tb_physical_count_period_comment
                │
                └─1──*──► tb_physical_count  (หนึ่ง row ต่อ (period, location);
                            │                  status: pending → in_progress → completed;
                            │                  ถูกสร้างที่ in_progress ทันที ไม่ใช่ pending;
                            │                  physical_count_type คงค่า default ของ schema —
                            │                  ไม่มี branch ของ frozen/live ใด ๆ)
                            │
                            ├─1──*──► tb_physical_count_comment  (ไม่ถูกใช้โดย UI ปัจจุบัน)
                            │
                            └─1──*──► tb_physical_count_detail
                                        │   (on_hand_qty คงเป็น 0 จนกว่า Submit for Review;
                                        │    actual_qty / diff_qty; counted_at / counted_by_id
                                        │    stamp เฉพาะโดย Save; ไม่มีคอลัมน์ lot_no)
                                        │
                                        └─1──*──► tb_physical_count_detail_comment  (ของจริง: photo/notes)

ที่ Submit สุดท้าย backend จัดกลุ่มบรรทัดที่ diff_qty ไม่เป็นศูนย์ตามเครื่องหมาย
แล้ว insert เอกสารกำพร้าที่ไม่มีฟิลด์เชื่อมกลับไปยังการนับเลย ในหนึ่ง transaction:
    ▼
tb_stock_in  (doc_status = completed ทันที; adjustment_type_id = null)   สำหรับบรรทัด diff_qty > 0
tb_stock_out (doc_status = completed ทันที; adjustment_type_id = null)   สำหรับบรรทัด diff_qty < 0
    │
    └── description / detail.note = ข้อความอิสระ "Physical Count Adjustment - Period: …" เท่านั้น
    │
    └── ไม่มี row tb_inventory_transaction ถูกสร้างโดย action นี้ (ไม่มีการเรียก executeAdjustmentIn/Out)
```

หมายเหตุ:

- **ลำดับชั้นสามระดับ แต่มีเพียงสองระดับล่างที่มี UI จริง** Period header มีไว้เพื่อจัดกลุ่มสถานที่ภายใต้งวดบัญชีเดียว; หน้ารายการของ frontend (`physical-count`) อ่านมันผ่าน `GET /physical-count-periods/current` โดย auto-provision period ที่ `draft` ในครั้งแรกที่ถูกร้องขอสำหรับงวดบัญชีที่เพิ่งเปิดใหม่
- **ไม่มี FK และไม่มีฟิลด์เชื่อม JSON แบบ structured สำหรับ variance rollup** Draft ก่อนหน้าของหน้านี้อธิบาย convention `info.countId` / `info.countPeriodId` บน row `tb_stock_in`/`tb_stock_out` ที่สร้างขึ้น การอ่าน method `submit()` ของ `physical-count.service.ts` โดยตรง (บรรทัด ~934-1036) แสดงว่าไม่มี field `info` ของ header หรือบรรทัด detail ใดถูกเขียนเลย — ร่องรอยเดียวของ rollup ที่ย้อนกลับไปยังการนับต้นทางคือข้อความ description แบบไม่มีโครงสร้าง การสร้าง "การนับใดที่ทำให้เกิด stock-in/out นี้" จากฝั่ง ledger จึงเป็นไปไม่ได้ผ่านฟิลด์ที่ index ใด ๆ
- **`@relation` FK declaration ที่ระบุชัดเจนทั้งหมดใช้ `onDelete: NoAction` หรือ `onDelete: Cascade`** — รักษาความหมาย soft-delete (`deleted_at`)

## 4. Enum

- **`enum_physical_count_period_status`** — วงจรชีวิตระดับ period สามค่า: `draft`, `counting`, `completed` ดูช่องว่างที่ยืนยันแล้วใน § 2 — ไม่พบ code path ใดที่เปลี่ยน period จาก `draft` เป็น `counting`
- **`enum_physical_count_status`** — วงจรชีวิตระดับเอกสาร สามค่า: `pending`, `in_progress`, `completed` `pending` ถูกประกาศไว้บน enum แต่เข้าถึงไม่ได้ผ่าน `create()` path ที่ยืนยันแล้ว (ทุกเอกสารถูกสร้างที่ `in_progress` โดยตรง)
- **`enum_physical_count_type`** — สองค่า `yes` / `no` ประกาศทั้งบน `tb_location` (default `no`; flag admin ระดับสถานที่ "สถานที่นี้จำเป็นต้องนับหรือไม่" ตั้งค่าบนฟอร์ม config ของสถานที่เอง) และ `tb_physical_count` (default `yes`; ไม่เคยถูกตั้งค่าโดย `create()` เลย ดังนั้นจึงคงค่า default บนทุกเอกสารจริง) ไม่มี behavioural branch ของ frozen-vs-live ใด ๆ ในโค้ดที่เกี่ยวข้องกับ enum นี้ — ดู [physical-count](/th/inventory/physical-count) § 3
- **`enum_physical_count_costing_method`** — enum ระดับบนสุดแยกต่างหาก (`standard`, `last`, `average`, `last_receiving`) ที่ **ไม่** ปรากฏเป็นฟิลด์บนตาราง physical-count ใด ๆ มันถูกอ่านครั้งเดียวต่อการ `submit()` สุดท้าย เป็น **ค่า tenant config ระดับ business-unit** (`enum_business_unit_config_key.physical_count_costing_method`, fallback default `last_receiving` ถ้าไม่ตั้งค่าหรือไม่ถูกต้อง) ผ่าน `TenantService.getBuConfig()` และนำไปใช้อย่างสม่ำเสมอกับ `cost_per_unit` ของทุกบรรทัด variance สำหรับ submit นั้น ไม่พบหน้าจอ frontend ใดที่ให้ผู้ใช้ตั้งค่า config key นี้
- **`enum_transaction_type`** — ที่ระดับ inventory ledger `physical-count` ไม่ใช่ค่าบน enum นี้ และ — ตาม § 1/§ 3 ข้างต้น — ค่า `adjustment_in`/`adjustment_out` ที่การ post inventory-adjustment ปกติจะสร้างนั้นไม่เคยถูกเขียนโดย rollup ของโมดูลนี้เองเลย เนื่องจากไม่มี row `tb_inventory_transaction` ถูกสร้าง

## 5. ความแตกต่างจาก carmen/docs

ไม่มีโฟลเดอร์ source ใน carmen/docs สำหรับโมดูลนี้ เอกสารวางแผนสองฉบับใน E2E repo (`docs/persona-doc/System Process/tx-08-physical-stocktake.md` และ `docs/test-cases/750-physical-count.md`, `docs/user-stories/750-physical-count.md`) อธิบายการออกแบบที่แตกต่างจาก implementation ปัจจุบันอย่างมาก — ดู [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) § 5.1 สำหรับการเปรียบเทียบทีละจุด (transaction type ของตัวเองเทียบกับการใช้ Stock In/Out จริง; สถานะ `FINALIZED`/GL-posted ที่ไม่มีอยู่จริง; transaction lock ระหว่างการนับที่ไม่มีโค้ดรองรับ; กลไก tolerance และ recount ที่ไม่มีโค้ดรองรับ)

## 6. แหล่งอ้างอิง

- **Primary (source of truth):** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — เอนทิตีหกตัว (`tb_physical_count_period`, `tb_physical_count_period_comment`, `tb_physical_count`, `tb_physical_count_comment`, `tb_physical_count_detail`, `tb_physical_count_detail_comment`); enum สี่ตัว (`enum_physical_count_period_status`, `enum_physical_count_status`, `enum_physical_count_type`, `enum_physical_count_costing_method`)
- **Service layer:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts` (create/refresh/save/reviewItems/submit/delete/update); `.../physical-count-period/physical-count-period.service.ts` (findCurrent/create/update); `.../period-end/period-end.validate.ts` (`validatePhysicalCount`, gate การปิดงวด)
- **Secondary (วางแผน ยังไม่ implement):** `../carmen-inventory-frontend-e2e/docs/persona-doc/System Process/tx-08-physical-stocktake.md`
- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/` (`pc-component.tsx`, `pc-entry-component.tsx`, `pc-review-component.tsx`); `types/physical-count.ts`; `hooks/use-physical-count.ts`, `hooks/use-physical-count-period.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count
- โมดูลที่เกี่ยวข้อง: [inventory](/th/inventory/inventory) (ledger ที่การ post inventory-adjustment *ปกติ* เขียนลง — ไม่ถูกแตะโดย rollup ของโมดูลนี้เอง), [inventory-adjustment](/th/inventory/inventory-adjustment) (ตารางที่ rollup เขียนเข้า โดยข้าม service layer ของโมดูลนั้น), [spot-check](/th/inventory/spot-check) (ลูกพี่ลูกน้องการนับบางส่วนที่ใช้ต้นไม้เอกสารแยก)
