---
title: การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — หน้า Entry & Review
description: Test case ของหน้า entry และ review สำหรับโมดูลการนับสต๊อกประจำงวด
published: true
date: 2026-07-15T17:56:09.000Z
tags: physical-count, test-scenarios, counter, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:00:00.000Z
---

# การนับสต๊อกประจำงวด (Physical Count) — Test Scenarios — หน้า Entry & Review

> **At a Glance**
> **หน้าจอ:** `physical-count/:id/entry` (`pc-entry-component.tsx`), `physical-count/:id/review` (`pc-review-component.tsx`) &nbsp;·&nbsp; **โมดูล:** [physical-count](/th/inventory/physical-count) &nbsp;·&nbsp; **Role:** role เดียวกับ [04-test-scenarios-count-lead.md](/th/inventory/physical-count/04-test-scenarios-count-lead)
> **หมวด:** Happy Path &nbsp;·&nbsp; Permission &nbsp;·&nbsp; Validation &nbsp;·&nbsp; Edge Case
> **ความครอบคลุม E2E:** ไม่มี Playwright spec ของ `physical-count`; scenario เป็น manual/planned

## 1. ขอบเขต

Scenario ด้านล่างใช้ action ที่ catalogue ใน [physical-count/03-user-flow-counter](/th/inventory/physical-count/03-user-flow-counter) § 3 — การป้อนบรรทัด, note, import/export, Save, Submit for Review และ Submit สุดท้าย

## 2. Functional — Happy Path

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| E-F-01 | ป้อน `actual_qty` บนบรรทัด | เอกสาร `in_progress` | ค่า commit เข้า local state ตอน blur; ป้าย "counted" ปรากฏเมื่อมีค่าแล้ว |
| E-F-02 | Save บรรทัดบางส่วน | บางบรรทัดมีค่า บางบรรทัดยังไม่มี | `PATCH .../save` stamp `counted_at`/`counted_by_id` บนบรรทัดที่ส่งมา; `product_counted` อัปเดต |
| E-F-03 | แนบ note และ photo ให้บรรทัด | เวลาใดก็ได้ | `POST /physical-count-detail-comments/:detailId` สร้าง `tb_physical_count_detail_comment` row พร้อมข้อความและ attachment |
| E-F-04 | ใช้ calculator เพื่อคำนวณยอดรวม | สินค้ามีการแปลงลัง/หน่วยที่ counter ต้องการคำนวณ | `CalculatorDialog` คืนยอดรวมที่ถูกเขียนเข้า `actual_qty` ของบรรทัด |
| E-F-05 | Export ยอดนับปัจจุบัน | เวลาใดก็ได้ | ไฟล์ `.xlsx` ดาวน์โหลดพร้อม id, รหัส/ชื่อ/ชื่อท้องถิ่น/SKU สินค้า, หน่วย, และ `actual_qty` effective ปัจจุบันต่อแถว |
| E-F-06 | Import ยอดนับจาก spreadsheet | ไฟล์ที่ export ไว้ก่อนหน้า (หรือเตรียมจากภายนอก) ที่มี SKU ตรงกัน | แถวที่จับคู่เติมค่า local ของบรรทัดของตน; toast รายงานจำนวนที่จับคู่/รวม/ข้าม |
| E-F-07 | Refresh สินค้าระหว่างการนับ | สินค้าเข้าเงื่อนไขใหม่สำหรับสถานที่ (assign แล้ว หรือมีสต๊อกแล้ว) | `PATCH .../refresh` เพิ่มบรรทัดใหม่เข้า sheet; บรรทัดที่มีอยู่ไม่ได้รับผลกระทบ |
| E-F-08 | Submit for Review เมื่อทุกบรรทัดมีค่าแล้ว | `uncountedCount === 0` | `PATCH .../review` คำนวณ `on_hand_qty`/`diff_qty` ใหม่สำหรับทุกบรรทัดจากยอด ledger สด; navigate ไป `/review` |
| E-F-09 | หน้า review แสดงตัวเลขสรุปถูกต้อง | บางบรรทัด match บางบรรทัด overage บางบรรทัด shortage | ตัวเลข matches/variances/overages/shortages บนหน้า review ตรงกับ `diff_qty` ของแต่ละบรรทัด |
| E-F-10 | Submit สุดท้ายด้วย variance ผสม | `counted_at != null` ของทุกบรรทัด | `PATCH .../submit` ตั้ง `status = completed`, สร้าง `tb_stock_in` หนึ่งฉบับ (บรรทัด overage) และ/หรือ `tb_stock_out` หนึ่งฉบับ (บรรทัด shortage) ทั้งคู่ `doc_status = completed` แล้ว; navigate กลับหน้ารายการ |

## 3. RBAC / Permission

| # | Scenario | Pre-condition | ผลที่คาดหวัง |
| - | -------- | ------------- | ---------------- |
| E-R-01 | ผู้ใช้ที่ไม่มี `inventory_management.physical_count` เปิด `:id/entry` โดยตรง | Permission ไม่ได้รับ | การเข้าถึงถูก reject ตามกลไก permission-gate ทั่วไป; ไม่มีข้อจำกัด zone หรือ assignment เฉพาะโมดูลให้ทดสอบเพิ่มนอกเหนือจากนี้ |

## 4. Validation — Negative Test

| # | กฎ | Scenario | Error ที่คาดหวัง |
| - | ---- | -------- | -------------- |
| V-01 | `PHC_VAL_006` | พยายาม Save, Submit for Review หรือ Submit บนเอกสาร `completed` | `"Physical Count is already completed"` |
| V-02 | `PHC_VAL_004` | คลิก Submit (สุดท้าย) ขณะอย่างน้อยหนึ่งบรรทัดยังมี `counted_at` เป็น null | `"<N> products have not been counted yet"` — ดูข้อควรระวัง Save-vs-Submit-for-Review ด้านล่าง |
| V-03 | `PHC_VAL_007` | Save/Review/Submit ด้วย `doc_version` ที่เก่าแล้ว (เช่น แท็บที่สองที่ยังไม่ refetch หลังการ save ของอีกแท็บ) | Conflict แบบ `409`; client ต้อง reload แล้วลองใหม่ |
| V-04 | `PHC_VAL_006` | พยายามลบเอกสาร `completed` | `"Cannot delete completed Physical Count"` |

## 5. Edge Case

| # | Scenario | ผลที่คาดหวัง |
| - | -------- | ---------------- |
| E-E-01 | ทุกบรรทัดถูกพิมพ์และ Submit for Review ทันที โดยไม่ผ่าน Save ก่อน | เนื่องจาก Save เป็น action เดียวที่ stamp `counted_at` และ Submit for Review ไม่ทำ Submit สุดท้ายบนหน้า review อาจ reject ด้วย `"<N> products have not been counted yet"` แม้ทุกบรรทัดจะแสดงค่าอยู่ก็ตาม — เป็นการอ่านตรงจาก `save()` เทียบกับ `reviewItems()` ใน `physical-count.service.ts` ยังไม่ได้ยืนยันด้วย automated test อิสระ |
| E-E-02 | ศูนย์บนชั้น | Counter ป้อน `actual_qty = 0` ชัดเจน (ไม่ปล่อยว่าง); นับเป็นการป้อนจริงที่สมบูรณ์ — shortage เต็มเทียบกับ `on_hand_qty` ที่ขั้นตอน review คำนวณได้ |
| E-E-03 | Set uncounted to zero แล้ว Submit for Review | ทุกบรรทัดที่ว่างก่อนหน้ากลายเป็น `0` ที่ local; Submit for Review พร้อมใช้และคำนวณ variance จริงสำหรับบรรทัดเหล่านั้นเทียบกับยอด ledger สด |
| E-E-04 | Import จับคู่ได้บางส่วน | บาง row ของ spreadsheet ไม่จับคู่กับ SKU ของบรรทัดใด | Toast รายงานจำนวนที่ข้าม; บรรทัดที่ไม่จับคู่คงเดิมทุกประการ |
| E-E-05 | Overage และ shortage ผสมกันใน submit เดียว | มีอย่างน้อยหนึ่งบรรทัด `diff_qty` บวกและหนึ่งบรรทัดลบ | ทั้ง `tb_stock_in` และ `tb_stock_out` ถูกสร้างโดย Submit สุดท้ายครั้งเดียวกัน |
| E-E-06 | ทุกบรรทัด reconcile เป็นศูนย์ variance | ทุก `diff_qty = 0` | Submit สุดท้ายสำเร็จ; ไม่มี `tb_stock_in`/`tb_stock_out` ถูกสร้างเลย |

## 6. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/physical-count/pc-entry-component.tsx`, `pc-review-component.tsx`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/physical-count/physical-count.service.ts` (`save`, `reviewItems`, `submit`, `refresh`, `delete`)
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec physical-count
- ที่เกี่ยวข้อง: [physical-count/03-user-flow-counter](/th/inventory/physical-count/03-user-flow-counter), [physical-count/02-business-rules](/th/inventory/physical-count/02-business-rules) (`PHC_VAL_004`–`007`, `PHC_POST_001`–`004`), [physical-count/04-test-scenarios](/th/inventory/physical-count/04-test-scenarios) (scenario end-to-end)
