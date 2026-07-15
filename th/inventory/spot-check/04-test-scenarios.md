---
title: การสุ่มตรวจ (Spot Check) — Test Scenarios
description: Test case ตามหน้าจอ scenario end-to-end และการ map กับ manual test-case catalog สำหรับการสุ่มตรวจ
published: true
date: 2026-07-15T18:38:42.000Z
tags: spot-check, test-scenarios, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T14:30:00.000Z
---

# การสุ่มตรวจ (Spot Check) — Test Scenarios

> **At a Glance**
> **โมดูล:** [spot-check](/th/inventory/spot-check) &nbsp;·&nbsp; **ขอบเขต:** role เดียวที่มีสิทธิ์จริง แบ่งเป็นสองไฟล์หน้าจอ (list/create; entry/review) บวกกลุ่มที่สามที่ยืนยันแล้วว่าไม่มีอยู่จริง
> **ลำดับการรัน:** scenario หน้ารายการ/สร้าง → scenario หน้า entry/review → scenario end-to-end ด้านล่าง
> **ความครอบคลุม E2E:** ไม่มี Playwright spec ของ `spot-check` ที่ `../carmen-inventory-frontend-e2e/tests/`; มี manual test-case catalog ที่ `docs/test-cases/760-spot-check.md` (32 case เขียนจาก live component) — ดู § 5 ว่า map เข้ากับ และต่างจาก routing จริงอย่างไร

## 1. ภาพรวม

หน้านี้เป็นจุดเริ่ม overview สำหรับชุด test-scenario ของโมดูล `spot-check` ความครอบคลุมจัดตาม role เดียวที่มีสิทธิ์จริงของโมดูล มองจากคู่หน้าจอสองคู่ — รายการตำแหน่งและฟอร์มสร้าง (`04-test-scenarios-inventory-controller.md`) และ flow entry/review (`04-test-scenarios-counter.md`) — บวกหน้า correction (`04-test-scenarios-audit-config.md`) ที่บันทึกกลุ่ม persona ที่สามที่ยืนยันแล้วว่าไม่มีอยู่จริง หัวข้อ 4 ด้านล่างครอบคลุม scenario end-to-end ที่ข้ามทั้งสี่หน้าจอในวงจรชีวิตเอกสารเดียว

## 2. ขอบเขต

- **หน้ารายการ / สร้าง** — เริ่ม spot check สำหรับตำแหน่ง เลือกวิธีสุ่มและ scope; ตาม [spot-check/03-user-flow-inventory-controller](/th/inventory/spot-check/03-user-flow-inventory-controller)
- **หน้า Entry / Review** — ป้อนบรรทัด notes import/export Submit for Review และ Submit ขั้นสุดท้าย; ตาม [spot-check/03-user-flow-counter](/th/inventory/spot-check/03-user-flow-counter)
- **ยืนยันแล้วว่าไม่มีอยู่จริง** — surface ของ Approver/Finance, Auditor หรือ Sysadmin; ตาม [spot-check/03-user-flow-audit-config](/th/inventory/spot-check/03-user-flow-audit-config)

## 3. ไฟล์ Test ของ Persona

- [Scenario หน้ารายการ/สร้าง](./04-test-scenarios-inventory-controller.md)
- [Scenario หน้า Entry/Review](./04-test-scenarios-counter.md)
- [กลุ่มที่ยืนยันแล้วว่าไม่มีอยู่จริง (หน้า correction)](./04-test-scenarios-audit-config.md)

## 4. Scenario End-to-End

แต่ละ row ด้านล่างเป็นวงจรชีวิตเอกสารเต็ม anchor กับ state machine จริงใน [03-user-flow.md](./03-user-flow.md) § 2

| # | Scenario | ขั้นตอน | สถานะปลายทางที่คาดหวัง |
| - | -------- | ----- | ------------------- |
| 1 | Random sample ไม่มี variance | Start (Random, `items = 10`) → นับทุกบรรทัดให้ตรงกับสิ่งที่ `reviewItems()` คำนวณได้ → Save For Resume → Submit For Review → Submit Spot Check | `tb_spot_check.doc_status = completed`; ไม่มีเอกสารอื่นถูกสร้าง; ทุก `diff_qty = 0` |
| 2 | High-value sample ผสม overage และ shortage | Start (High Value, `items = 10`, ไม่มี `minimum_cost`) พร้อมงวดบัญชีที่เปิด/ล็อกอยู่ → นับให้เกิด variance ทั้งบวกและลบ → Submit For Review → Submit | `doc_status = completed`; หน้า review แสดงทั้ง tile overage และ shortage; ไม่มีเอกสาร rollup ใด ๆ อยู่ที่ไหนสำหรับทั้งสอง |
| 3 | Manual sample, trigger โดยความสงสัยความไม่ตรง | Start (Manual) → เลือก 3 สินค้าเฉพาะผ่าน transfer picker → นับ → Submit For Review → Submit | สร้างแถว detail ตรง 3 แถวและนับแล้ว; `doc_status = completed` |
| 4 | High-value sample ไม่มีงวดบัญชีที่เปิด | พยายาม Start (High Value) เมื่อไม่มี `tb_period` ใดที่ `status ∈ {open, locked}` | `POST /spot-checks` ถูก reject ด้วย `SPOT_CHECK_NO_ACTIVE_PERIOD` (`SPC_VAL_004`); เอกสารไม่ถูกสร้าง |
| 5 | ข้าม Save ไปตรง Submit for Review | Start → นับทุกบรรทัดโดยไม่เคยกด Save For Resume → Submit For Review (ปุ่มมีให้เพราะ `uncountedCount === 0`) → Submit | `doc_status` ไม่เคยผ่าน `in_progress` — ไปจาก `pending → completed` โดยตรง เพราะมีแค่ Save เท่านั้นที่ทำ transition นั้น; เอกสารยังคง complete ปกติ |
| 6 | Submit ทั้งที่มีบรรทัดยังไม่นับ | Start → ปล่อยหลายบรรทัดไว้ที่ `actual_qty = 0` ที่ seed ไว้ → Submit For Review → Submit | ทั้งสอง call สำเร็จ — ไม่มีการตรวจความครบถ้วนฝั่ง server (`SPC_VAL_008`); บรรทัดที่ยังไม่นับแสดง `diff_qty = -on_hand_qty` (shortage เต็ม) บนหน้า review |
| 7 | Reset spot check ที่กำลังดำเนิน | Start → Save การนับบางส่วน → กลับไปหน้ารายการ → คลิก Reset → ยืนยัน | `doc_status = void`; แถว `tb_spot_check_detail` **ไม่** ถูกล้าง (ยังคงสิ่งที่พิมพ์ไว้); ตำแหน่งกลับไปเป็น bucket Not Started |
| 8 | เปิด spot check ที่ completed แล้วจาก History | Complete spot check → เปิดใหม่จาก tab History → กดต่อไป Submit For Review อีกครั้ง | `reviewItems()` สำเร็จ (ไม่มี guard สถานะ) และเขียนทับ `on_hand_qty`/`actual_qty`/`diff_qty`/`counted_at` บนทุกแถว detail; ความพยายาม Submit ขั้นสุดท้ายครั้งถัดไปถูก reject ด้วย `"Spot check is already completed"` (`SPC_VAL_008`) |
| 9 | ความขัดแย้งของ `doc_version` | สอง browser tab เปิด spot check เดียวกัน; Tab A save; Tab B save ด้วย `doc_version` ที่ stale แล้ว | Save ของ Tab B ไม่ match `where` clause และถูก reject; client ต้อง reload และ retry |
| 10 | ไม่มีสินค้าที่ตำแหน่ง | Start spot check สำหรับตำแหน่งที่ eligible product pool ว่างเปล่า (ไม่มี `tb_product_location` assignment และไม่มีสต๊อกไม่เป็นศูนย์) | `POST /spot-checks` reject ด้วย `"No products found at this location"` (`SPC_VAL_002`); เอกสารไม่ถูกสร้าง |
| 11 | Manual sample มีสินค้านอก pool ของตำแหน่ง | Start (Manual) → เลือกสินค้าที่ไม่เคย assign หรือมีสต๊อกที่ตำแหน่งนี้เลย | ถ้าเป็นสินค้าเดียวที่เลือก การสร้างถูก reject ด้วย `"None of the selected products were found at this location"` (`SPC_VAL_003`); ถ้าเลือกร่วมกับสินค้าที่ valid ก็ถูกทิ้งเงียบ ๆ ส่วนที่เหลือดำเนินต่อ |
| 12 | Variance ไม่เคยไปถึง ledger | Complete spot check ที่มี shortage ที่ยืนยันแล้วหลายรายการ | `tb_spot_check.doc_status = completed`; ไม่มี `tb_stock_in`/`tb_stock_out`, ไม่มี row `tb_inventory_transaction`, และไม่มีฟิลด์ใดที่ไหนอ้างอิงถึง spot check นี้นอกตารางของตัวมันเอง — ผู้ใช้ต้องสร้างเอกสาร [inventory-adjustment](/th/inventory/inventory-adjustment) แยกเองเพื่อแก้ไข ledger โดยไม่มีลิงก์ที่ระบบให้กลับไปยัง spot check นี้ |

## 5. การ Map กับ Manual Test-Case Catalog

ยังไม่มี Playwright spec ของ `spot-check` ที่ `../carmen-inventory-frontend-e2e/tests/` (ยืนยันโดย `ls tests/ | grep -i 'spot\|check'`) มี manual test-case catalog เอกสารล้วนอยู่แทนที่ `docs/test-cases/760-spot-check.md` — 32 case (`TC-SPC-*`) เขียนจากการอ่าน live component โดยตรง เป็นสิ่งที่ใกล้เคียง executable spec ที่สุดของโมดูลนี้ scenario ส่วนใหญ่ในนั้นตรงกับ routing และกลไกที่ยืนยันในรอบนี้ (ปุ่มสลับ locations/history, KPI tiles, สาม method การสร้าง, filter/notes/calculator ของหน้า entry, Submit For Review, stat tiles ของหน้า review และ Submit ขั้นสุดท้ายที่เปลี่ยน `doc_status` เป็น `completed`)

**สอง scenario ใน catalog นั้นบรรยายหน้าจอที่ routing ของแอปนี้ไปไม่ถึงจริง** `TC-SPC-040001` ("แก้ไข spot check ที่บันทึกแล้ว: เปิด detail ในโหมด view, กด Edit, แก้ description, Save") และ `TC-SPC-050001` ("ลบ spot check ที่บันทึกแล้ว: เปิด detail, กด Edit, กด Delete") ทั้งสองสมมติว่ามีหน้า detail view/edit แยกจากหน้า counting การอ่าน `router.tsx` โดยตรงแสดงว่า `spot-check/:id` render `sc-entry-component.tsx` (UI counting) เสมอ — ไม่เคย render `sc-form.tsx` ในโหมด view หรือ edit เลย branch `isView`/`isEdit` ของ `ScForm` และ hook `useUpdateSpotCheck`/`useDeleteSpotCheck` ที่ปุ่ม Save/Delete เรียก ถูก instantiate จากหน้าสร้าง (`spot-check-by-location-content.tsx`) เท่านั้น เสมอโดยไม่มี entity — ดังนั้น branch เหล่านั้นจึงเป็น dead code ที่เข้าถึงไม่ได้ผ่าน navigation จริงใด ๆ ถือ `TC-SPC-040001`/`TC-SPC-050001` ว่าบรรยายฟังก์ชันที่ตั้งใจแต่ยังไม่ได้ wire ไม่ใช่ flow ที่ยืนยันแล้วว่า test ได้; endpoint `update()`/`delete()` ฝั่ง backend เป็นของจริงและจะทำงานได้ถ้าเรียกตรง (เช่นผ่าน Bruno) แค่ไม่มีปุ่มใดใน UI ที่ shipped ไปถึงมันได้

## 6. แหล่งอ้างอิง

- **Frontend:** `../carmen-inventory-frontend-react/routes/inventory-management/spot-check/`
- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/spot-check/spot-check.service.ts`, `spot-check.logic.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/` — ยังไม่มี spec spot-check; manual test-case catalog ที่ `docs/test-cases/760-spot-check.md` (32 case; สอง — `TC-SPC-040001`, `TC-SPC-050001` — บรรยายหน้าจอ view/edit ที่เข้าถึงไม่ได้ ดู § 5)
- ที่เกี่ยวข้อง: [spot-check/03-user-flow](/th/inventory/spot-check/03-user-flow) (state machine ที่หน้านี้ใช้), [spot-check/02-business-rules](/th/inventory/spot-check/02-business-rules) (`SPC_VAL_*` / `SPC_AUTH_*` / `SPC_POST_*`), [inventory-adjustment/04-test-scenarios](/th/inventory/inventory-adjustment/04-test-scenarios) (จุดที่ต้อง manual แก้ไขผลต่างที่ยืนยันแล้ว)
