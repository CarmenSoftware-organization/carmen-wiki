---
title: การเติมสต๊อก (Stock Replenishment)
description: รายการที่ต่ำกว่า par ขับโดย threshold par / max บน tb_product_location พร้อม wizard สร้าง draft PR หรือ SR — เป็น API จริงตั้งแต่ 2026-08; ไม่มี scheduled sweep
published: true
date: '2026-09-23T01:30:00.000Z'
tags: store-requisition, replenishment, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# การเติมสต๊อก (Stock Replenishment)

> **At a Glance**
> **เจ้าของ:** Purchaser / Requester (review รายการที่ต่ำกว่า par แล้วสร้าง draft PR หรือ SR) &nbsp;·&nbsp; **ตาราง:** ไม่มีเฉพาะ — อ่าน `tb_product_location` + on-hand เขียน draft `tb_purchase_request` / `tb_store_requisition` ธรรมดา &nbsp;·&nbsp; **Trigger:** on demand (ตอนโหลดหน้าจอ) — **ไม่มี cron** &nbsp;·&nbsp; **Endpoints:** `GET /api/{bu}/stock-replenishment`, `GET …/location-products/:location_id/:product_id/pending-documents`, `POST …/stock-replenishment/pr`, `POST …/stock-replenishment/sr` &nbsp;·&nbsp; **สรุป 1 บรรทัด:** หน้าจอแสดงทุก `(location, product)` ที่ต่ำกว่า par; มนุษย์เลือกแถวแล้วสร้างเอกสาร

> ✅ **สถานะการ implement (ตรวจสอบซ้ำ 2026-09-22):** หมายเหตุรอบ 2026-07-15 ที่ว่าหน้าจอนี้ขับด้วย mock data ล้าสมัยแล้ว `feat: add stock replenishment and wastage reporting api` (`c9348f667`, 2026-08) เพิ่ม backend (`apps/micro-business/src/inventory/stock-replenishment/`, gateway `apps/backend-gateway/src/application/stock-replenishment/`), `57d5715a0` (2026-08-26) เพิ่ม endpoint สร้าง PR/SR และ hook ฝั่ง frontend `routes/store-operation/stock-replenishment/use-stock-replenishment.ts` เรียก API จริงแล้ว สิ่งที่ **ยังคง** ไม่ได้ implement: scheduled sweep ใด ๆ (ไม่พบ `replenish` / `par_qty` ใน `../micro-cronjobs/`), idempotent "หนึ่ง draft ต่อวัน", term `on_order`, การ config สถานที่ต้นทาง และ period gate — Section 2–6 ด้านล่างบรรยายโค้ดตามที่เป็นอยู่

![การเติมสต๊อก (Stock Replenishment) screen](/screenshots/store-requisition/stock-replenishment.png)

## 1. ภาพรวมและผู้ใช้งาน

Stock Replenishment คือ **ประตูหน้าที่ขับโดยนโยบายสู่ [store-requisition](/th/inventory/store-requisition) และ [purchase-request](/th/inventory/purchase-request)** `GET /api/{bu}/stock-replenishment` สแกนทุกแถว `tb_product_location` ที่ `par_qty > 0` ซึ่งสถานที่ active และไม่ใช่ `direct` รวม on-hand ต่อคู่ `(location, product)` และคืนแถวที่ on-hand ต่ำกว่า par โดยจัดกลุ่มตามสถานที่และเรียงตามปริมาณสั่งเติม จากหน้าจอ (`/store-operation/stock-replenishment`) ผู้ใช้ติ๊กแถวแล้วเปิดหนึ่งในสอง wizard: **Create PR** (`POST …/pr` ซื้อส่วนที่ขาดเข้ามา) หรือ **Create SR** (`POST …/sr` ดึงจากสถานที่อื่น) เอกสารที่สร้างเป็น draft ธรรมดาที่จากนั้นวิ่งผ่าน workflow PR / SR ปกติ

- **Purchaser / Requester** — review รายการ เลือก PR หรือ SR เลือก workflow (และสำหรับ SR เลือกสถานที่ต้นทาง) แก้ปริมาณใน wizard และ submit draft ที่ได้จากโมดูลของมันเอง
- **ไม่มี service account ไม่มี cron** — ไม่มีสิ่งใด run โดยไม่มีคนดูแล
- **ไม่มีตาราง `tb_replenishment`** — artefact ถาวรมีเพียง draft PR / SR

## 2. งานที่พบบ่อย

| งาน | ที่ไหน | หมายเหตุ |
|---|---|---|
| ดูว่าอะไรต่ำกว่า par | Store Operation → Stock Replenishment | Summary bar: locations / items / critical / warning / low / total reorder qty; หนึ่งกลุ่มพับได้ต่อสถานที่; แต่ละแถวแสดง on-hand, min, max, par, reorder qty และ status badge |
| สร้าง PR สำหรับส่วนที่ขาด | เลือกแถว → wizard **Create PR** → เลือก workflow ปรับ `request_qty` / order unit → ยืนยัน | `POST …/stock-replenishment/pr` — draft PR หนึ่งใบต่อ call; สถานที่ติดไปกับแต่ละบรรทัด |
| สร้าง SR สำหรับส่วนที่ขาด | เลือกแถว → wizard **Create SR** → เลือกสถานที่ต้นทาง + SR workflow → ยืนยัน | `POST …/stock-replenishment/sr` — บรรทัดที่ใช้คู่ `(from_location, location_id)` เดียวกันกลายเป็น draft SR หนึ่งใบ; response คือ array ของ id ที่สร้าง |
| ดูว่าอะไรกำลังมาสำหรับแถวนั้นแล้ว | แถว → pending documents | `GET …/location-products/:location_id/:product_id/pending-documents` (`stock-replenishment.pending.ts`) แสดง PR ใน `draft` / `in_progress` / `approved` (approved นับเป็น pending โดยตั้งใจ — ผ่าน workflow แล้ว แต่ยังไม่ได้รับของ), SR ใน `draft` / `in_progress` และบรรทัด PO ที่ลิงก์กับบรรทัด PR เหล่านั้น สำหรับคู่นั้น เป็นข้อมูลประกอบ — รายการ **ไม่** หักออกจากส่วนที่ขาด |
| เปลี่ยน threshold | [product](/th/inventory/product) → tab location → แก้ `tb_product_location.par_qty` / `max_qty` / `min_qty` | มีผลตอนโหลดหน้าจอครั้งถัดไป |
| สอบสวนแถวที่หายไป | Check `tb_product_location` มีอยู่, `is_active` และ `par_qty > 0` | คู่ที่ไม่มีนโยบายหรือ `par_qty = 0` ถูกตัดออก; `min_qty` ไม่มีส่วนในการเลือก |

## 3. ข้อผิดพลาดและการตรวจสอบ

| อาการ / Message | สาเหตุ | Action |
|---|---|---|
| สินค้าไม่อยู่ในรายการ | ไม่มีแถว `tb_product_location`, `par_qty = 0`, on-hand ≥ par หรือสถานที่เป็น `direct` / inactive | เพิ่ม / ยกแถวนโยบาย; หมายเหตุ `min_qty` *ไม่ใช่* trigger และสถานที่ `direct` ไม่ถูกแสดงเลย |
| `STOCK_REPLENISHMENT_WORKFLOW_NOT_FOUND` / `…_WORKFLOW_PERMISSION_DENIED` (400, "Insufficient user permission to create sr/pr") | `workflow_id` ที่เลือกไม่มีอยู่ หรือขั้นแรกของมันไม่อนุญาตให้ผู้เรียก create | เลือก workflow ประเภทที่ถูกต้อง (`purchase_request` สำหรับ PR, `store_requisition` สำหรับ SR) ที่ขั้น create รวมผู้ใช้อยู่ (`stock-replenishment.verify.ts`) |
| `STOCK_REPLENISHMENT_LOCATION_PERMISSION_DENIED` (400) | ผู้เรียกไม่ได้ถูก assign สถานที่ของบรรทัดนั้น (`tb_location_user`) | Assign สถานที่ให้ผู้ใช้หรือตัดแถวออก |
| `STOCK_REPLENISHMENT_PRODUCTS_NOT_APPLICABLE` (400, "…cannot apply with workflow: {workflow_name}") | รายการ `data.products` ของ workflow ไม่ว่างและไม่รวมสินค้าที่เลือก | เลือก workflow ที่ครอบคลุมสินค้านั้น |
| PR wizard ปฏิเสธ order unit | `request_unit_id` ไม่ใช่หนึ่งใน order unit ของสินค้า (`loadProductOrderUnits`) | เลือกหน่วยที่อยู่ในรายการ; conversion factor ถูก resolve ฝั่ง server |
| draft SR ล้มเหลวปลายน้ำ | กฎ create ของ SR ใช้บังคับเหมือนเดิม — เช่น สถานที่ต้นทางแบบ `direct` ถูกปฏิเสธโดย `deriveSrType()` | เลือกต้นทางแบบ `inventory` / `consignment` |
| ส่วนที่ขาดเดียวกันถูกสร้างซ้ำ | ไม่มี idempotency — แต่ละรอบ wizard สร้าง draft ใหม่ | ตรวจรายการ pending-documents ก่อน |

## 4. กรณีพิเศษ

- **Status band เป็นอัตราส่วน on-hand ต่อ par** (`stock-replenishment.helper.ts`): `on_hand / par_qty ≤ 0.25` → `critical`; `≤ 0.5` → `warning`; อื่น ๆ → `low` ยอด ledger ติดลบถูก clamp เป็นศูนย์สำหรับอัตราส่วนและสูตร reorder ขณะที่ `on_hand_qty` ใน response ยังแสดงตัวเลขดิบ (ซึ่งอาจติดลบ)
- **Reorder level เลือก `max_qty` ก่อน** `reorder_level = max_qty > 0 ? max_qty : par_qty`; `reorder_qty = max(reorder_level − on_hand, 0)` `min_qty` ถูกคืนเพื่อแสดงผลเท่านั้น
- **ไม่มี term `on_order`** PO ที่เปิดอยู่และ SR transfer ที่กำลังดำเนินการไม่ลดส่วนที่ขาด; endpoint pending-documents คือสิ่งทดแทนแบบ manual
- **ไม่มี cron ไม่มี idempotency ไม่มี period gate** ทุกรอบ wizard สร้าง draft ใหม่; ไม่มีสิ่งใดตรวจ inventory period ที่นี่ (กฎวันที่ submit/issue ของ SR เองใช้บังคับภายหลัง — ดู [store-requisition/02-business-rules](/th/inventory/store-requisition/02-business-rules) `SR_VAL_014`)
- **สถานที่ต้นทางถูกเลือกต่อรอบ wizard** ไม่ได้ config ต่อ BU; SR wizard ตัดปลายทางออกจากตัวเลือกต้นทาง
- **ส่วนหัวของ draft มาจากผู้เรียก**: `buildDraftHeader()` ใช้สมาชิกภาพ `tb_department_user` แรกของผู้เรียกเป็นแผนกและ workflow ที่เลือก; `requestor_id` คือผู้เรียก
- **Pagination เป็นตามกลุ่มสถานที่** (`perpage < 0` คืนทั้งหมด); แถวภายในกลุ่มเรียง `reorder_qty desc, name asc`

---

## 5. กระบวนการ (Dev)

Stock Replenishment **ไม่ใช่ตาราง Prisma แยก** — เป็น read model เหนือ `tb_product_location` บวกยอด on-hand และตัวสร้างบาง ๆ สองตัวที่ delegate ไปยังโมดูล PR / SR

### 5.1 `tb_product_location` (นโยบาย)

| ฟิลด์ | Type | คำอธิบาย |
|---|---|---|
| `id` | `String @db.Uuid` | Primary key |
| `product_id` | `String @db.Uuid` | FK ไปยัง `tb_product` |
| `location_id` | `String? @db.Uuid` | FK ไปยัง `tb_location` (สถานที่บริโภค) |
| `min_qty` | `Decimal(20,5)?` | คืนเพื่อแสดงผล; **ไม่** ใช้ในการเลือกหรือสูตร reorder |
| `max_qty` | `Decimal(20,5)?` | ระดับเป้าหมาย: เมื่อ `> 0` เป็น `reorder_level` |
| `par_qty` | `Decimal(20,5)?` | Trigger: แถวถูกแสดงเมื่อ `par_qty > 0` และ `on_hand < par_qty`; เป็น `reorder_level` สำรองเมื่อ `max_qty = 0` |
| `re_order_qty` | `Decimal(20,5)?` | มีใน schema; **ไม่ถูกอ่าน** โดย replenishment service |
| คอลัมน์ Audit | — | มาตรฐาน |

**Constraints:** `@@unique([product_id, location_id, deleted_at])` หนึ่งแถวนโยบายต่อ `(product, location)`

### 5.2 รูปแบบ response (`StockReplenishmentLocationResponseSchema`)

```
[
  { location_id, location_code, location_name,
    products_location: [
      { id, code, name, local_name, category{id,name}, sub_category{id,name}, item_group{id,name},
        on_hand_qty, min_qty, max_qty, par_qty, reorder_qty,
        status: low | warning | critical,
        product_location_id, inventory_unit_id, inventory_unit_name }
    ] }
]
summary: { total_locations, total_items, critical_count, warning_count, low_count, total_reorder_qty }
```

### 5.3 Payload การสร้าง

```
POST /api/{bu}/stock-replenishment/pr
{ workflow_id, products: [ { id, request_unit_id, request_qty, location_id } ] }

POST /api/{bu}/stock-replenishment/sr
{ workflow_id, products: [ { id, request_qty, location_id, from_location } ] }
→ data: [ <sr id>, … ]   (one per distinct (from_location, location_id) pair)
```

wizard ฝั่ง frontend (`stock-repl-pr-wizard.tsx`, `stock-repl-sr-wizard.tsx`) ส่งสถานที่ครั้งเดียวที่ระดับบนสุด; DTO ของ gateway คาดหวังต่อบรรทัด (`StockReplenishmentCreatePrSchema` / `…SrSchema`) — wizard กระจายสถานที่ที่เลือกไปยังทุกบรรทัดก่อน post

## 6. Algorithm / วงจรชีวิต

```
GET (on screen load, optional ?location_id=, ?search=):
1. candidates = tb_product_location WHERE deleted_at IS NULL AND par_qty > 0
                AND location IS active AND location_type <> direct
                (optionally filtered by ?location_id= / product search)
2. on_hand[(location, product)] = Σ balance from the inventory ledger for the pair
3. for each candidate:
     par = par_qty; on_hand = max(raw_balance, 0); if on_hand >= par: skip
     reorder_level = max_qty > 0 ? max_qty : par
     reorder_qty   = max(reorder_level - on_hand, 0)
     status        = ratio(on_hand / par) <= 0.25 ? critical : <= 0.5 ? warning : low
4. group by location, sort rows by reorder_qty desc then name, page by location group

POST …/sr (user action):
1. verify(): workflow exists and is store_requisition type; caller is in its create stage;
             caller is assigned to every location_id (tb_location_user);
             every product is allowed by workflow.data.products (when that list is non-empty)
2. header = { requestor = caller, department = caller's first tb_department_user, workflow }
3. group lines by (from_location, location_id) → one StoreRequisitionLogic.create() per group
   (sr_type derived from the two locations; sr_no = draft-<hex>)
4. return the created ids → the SRs continue as ordinary drafts
```

`POST …/pr` มีรูปแบบเดียวกันโดยได้ draft PR หนึ่งใบต่อ call และ `request_unit_id` ต่อบรรทัดถูกแปลงผ่าน order unit ของสินค้า

## 7. ความเชื่อมโยงข้ามโมดูล

- [store-requisition](/th/inventory/store-requisition) — ประเภทเอกสารที่ผลิต; วงจรชีวิตปลายน้ำเหมือนกัน (`SR_XMOD_011`)
- [purchase-request](/th/inventory/purchase-request) — ประเภทเอกสารที่ผลิตอีกแบบ
- [inventory](/th/inventory/inventory) — แหล่ง `on_hand` สำหรับการคำนวณส่วนที่ขาด
- [product](/th/inventory/product) — นโยบาย `tb_product_location` อยู่ใต้ master สินค้า
- [master-data/location](/th/inventory/master-data/location) — การตั้งค่า par / max ต่อ-location
- [inventory/transaction](/th/inventory/inventory/transaction) — เมื่อ SR post, log ธุรกรรมสต๊อก (`tb_inventory_transaction`, `inventory_doc_type = store_requisition`) บันทึกการเคลื่อนย้าย

## 8. แหล่งอ้างอิง

- **Backend:** `../carmen-turborepo-backend-v2/apps/micro-business/src/inventory/stock-replenishment/` — `stock-replenishment.service.ts` (`findAll`, `selectBelowPar`, `createPrByReplenishmentProduct`, `createSrByReplenishmentProduct`, `findPendingDocuments`, `buildDraftHeader`), `stock-replenishment.helper.ts` (`toReplenishmentStatus`, `toReorderQty`, `RATIO_CRITICAL = 0.25`, `RATIO_WARNING = 0.5`), `stock-replenishment.verify.ts`, `stock-replenishment.draft.ts`, `dto/stock-replenishment.dto.ts`, `dto/stock-replenishment.serializer.ts`; gateway `apps/backend-gateway/src/application/stock-replenishment/stock-replenishment.controller.ts` (app-ids `stockReplenishment.findAll` / `findPendingDocuments` / `createPr` / `createSr`)
- **Error catalogue:** `STOCK_REPLENISHMENT_WORKFLOW_NOT_FOUND`, `STOCK_REPLENISHMENT_WORKFLOW_PERMISSION_DENIED`, `STOCK_REPLENISHMENT_LOCATION_PERMISSION_DENIED`, `STOCK_REPLENISHMENT_PRODUCTS_NOT_APPLICABLE` ใน `packages/error-catalog/src/catalog.ts`
- **Prisma:** `../carmen-turborepo-backend-v2/packages/prisma-shared-schema-tenant/prisma/schema.prisma` — `tb_product_location`, `tb_store_requisition`, `enum_sr_type`
- **Frontend:** `../carmen-inventory-frontend-react/routes/store-operation/stock-replenishment/` — `use-stock-replenishment.ts` (`useStockReplenishment`, `useCreateStockReplPr`, `useCreateStockReplSr`), `stock-repl-component.tsx`, `stock-repl-location.tsx`, `stock-repl-pr-wizard.tsx`, `stock-repl-sr-wizard.tsx`; `types/stock-replenishment.ts`
- **E2E:** `../carmen-inventory-frontend-e2e/tests/711-stock-replenishment.spec.ts` (33 case, `TC-SRPL-*`: โหลดหน้า, summary bar, กลุ่มสถานที่, expand/collapse, การเลือก, wizard); narrative ใน `docs/user-stories/711-stock-replenishment.md`
- **Cron job:** ไม่มี — `../micro-cronjobs/` ไม่มีโค้ดการเติมสต๊อกในรอบนี้
- **Module landing:** [store-requisition](/th/inventory/store-requisition) § 7
