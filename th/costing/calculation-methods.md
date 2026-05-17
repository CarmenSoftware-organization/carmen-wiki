---
title: วิธีคำนวณต้นทุนสินค้าคงคลัง: FIFO vs. Weighted Average (Inventory Costing Methods)
description: การวิเคราะห์วิธีคำนวณต้นทุนสินค้าคงคลัง FIFO vs. Weighted Average สำหรับแพลตฟอร์ม Carmen Software
published: true
date: 2026-05-17T12:00:00.000Z
tags: inventory, costing, fifo, weighted-average, carmen-software
editor: markdown
dateCreated: 2026-02-16T11:19:18.975Z
---

# วิธีคำนวณต้นทุนสินค้าคงคลัง: FIFO vs. Weighted Average

> **At a Glance**
> **กลุ่มผู้ใช้:** นักพัฒนา & QA ฝั่ง Inventory &nbsp;·&nbsp; **ขอบเขต:** FIFO vs. Weighted Average — แนวคิด สูตร ผลกระทบ COGS trade-off &nbsp;·&nbsp; วิธี costing ล็อกที่ตอนตั้งค่า BU; หน้านี้เป็นเอกสารอ้างอิงในการตัดสินใจ

## 1. ภาพรวม

เอกสารนี้วิเคราะห์วิธีคำนวณต้นทุนสินค้าคงคลังหลักสองวิธีสำหรับแพลตฟอร์มจัดการสินค้าคงคลัง:

- **FIFO (First-In, First-Out)**: สินค้าที่ซื้อก่อนจะถูกขาย/ใช้ก่อน
- **Weighted Average Cost**: สินค้าทั้งหมดถูกตีมูลค่าที่ต้นทุนเฉลี่ยถ่วงน้ำหนัก

ทั้งสองวิธีใช้กำหนด **ต้นทุนขาย (COGS)** และ **มูลค่าสินค้าคงเหลือปลายงวด** ซึ่งกระทบโดยตรงต่อการรายงานทางการเงินและการตัดสินใจเชิงปฏิบัติการ

---

## 2. FIFO (First-In, First-Out)

### 2.1 แนวคิด

FIFO สมมติว่าสินค้าคงคลังเก่าที่สุดถูกบริโภคก่อน Lot ที่ซื้อแต่ละครั้งเก็บต้นทุนเดิมไว้จนกว่าจะถูกบริโภคหมด

### 2.2 การทำงาน

```
Purchase Lot 1: 100 units @ ฿10.00
Purchase Lot 2:  50 units @ ฿12.00
Purchase Lot 3:  80 units @ ฿11.50

Issue 120 units:
  - 100 units from Lot 1 @ ฿10.00 = ฿1,000.00
  -  20 units from Lot 2 @ ฿12.00 = ฿  240.00
  - Total COGS = ฿1,240.00

Remaining Inventory:
  - 30 units from Lot 2 @ ฿12.00 = ฿360.00
  - 80 units from Lot 3 @ ฿11.50 = ฿920.00
  - Total = ฿1,280.00 (110 units)
```

### 2.3 แบบจำลองข้อมูล

การเคลื่อนไหวสินค้าคงคลังทุกครั้งต้องติดตามข้อมูล **lot/batch**:

```
inventory_lot:
  - lot_id          (PK)
  - product_id      (FK)
  - warehouse_id    (FK)
  - purchase_date   (timestamp)       -- วันที่ซื้อ
  - quantity         (decimal)         -- ปริมาณคงเหลือใน lot นี้
  - unit_cost        (decimal)         -- ต้นทุนซื้อต้นฉบับ
  - created_at       (timestamp)

inventory_transaction:
  - transaction_id   (PK)
  - product_id       (FK)
  - warehouse_id     (FK)
  - transaction_type (enum: IN, OUT, ADJUST)  -- รับ ใช้ ปรับ
  - quantity          (decimal)
  - reference_doc     (varchar)        -- หมายเลข PO, SO ฯลฯ
  - created_at        (timestamp)

inventory_transaction_lot:
  - transaction_id   (FK)
  - lot_id           (FK)
  - quantity          (decimal)        -- ปริมาณที่บริโภคจาก lot นี้
  - unit_cost         (decimal)        -- ต้นทุนตอนบริโภค
```

### 2.4 อัลกอริทึม (การ Issue Stock)

```
function issueStock_FIFO(productId, warehouseId, requiredQty):
    lots = getLots(productId, warehouseId)
             .filter(qty > 0)
             .orderBy(purchase_date ASC)  // Oldest first

    totalCost = 0
    remaining = requiredQty

    for each lot in lots:
        if remaining <= 0:
            break

        consume = min(lot.quantity, remaining)
        totalCost += consume * lot.unit_cost
        lot.quantity -= consume
        remaining -= consume

        recordTransactionLot(lot.id, consume, lot.unit_cost)

    if remaining > 0:
        throw InsufficientStockError  // สต๊อกไม่พอ

    return totalCost
```

### 2.5 ข้อดี

| ข้อดี | รายละเอียด |
|-----------|---------|
| ติดตามต้นทุนได้แม่นยำ | แต่ละหน่วยเก็บต้นทุนซื้อจริงไว้ |
| ตรงกับการไหลทางกายภาพของสินค้า | เหมาะกับสินค้าที่เน่าเสียง่าย |
| ดีกว่าในช่วงราคาขาขึ้น | COGS ต่ำกว่า กำไรที่รายงานสูงกว่า มูลค่าสินค้าคงคลังสูงกว่า |
| Audit trail ครบถ้วน | สามารถ trace กลับไปยังแหล่งซื้อได้ |

### 2.6 ข้อเสีย

| ข้อเสีย | รายละเอียด |
|--------------|---------|
| ความซับซ้อนสูง | ต้องติดตามแต่ละ lot |
| ต้องการพื้นที่จัดเก็บมากกว่า | แต่ละ lot ต้องมี record ของตัวเอง |
| issue ช้ากว่า | ต้องวนผ่าน lot ตามลำดับ |
| การจัดการ lot บางส่วน | Lot อาจถูกบริโภคบางส่วน เพิ่มความซับซ้อน |

---

## 3. Weighted Average Cost

### 3.1 แนวคิด

Weighted average cost รวมต้นทุนของสินค้าที่มีอยู่ทั้งหมดเป็นค่าเฉลี่ยถ่วงน้ำหนักเดียว ทุกหน่วยในสต๊อกมีต้นทุนเดียวกัน ณ จุดเวลาใดเวลาหนึ่ง

### 3.2 การทำงาน

```
Opening Balance:    0 units @ ฿0.00    | Average Cost = ฿0.00

Purchase 1:  100 units @ ฿10.00
  Total:     100 units, Value = ฿1,000.00
  Average Cost = ฿1,000.00 / 100 = ฿10.00

Purchase 2:   50 units @ ฿12.00
  Total:     150 units, Value = ฿1,000.00 + ฿600.00 = ฿1,600.00
  Average Cost = ฿1,600.00 / 150 = ฿10.6667

Issue 120 units:
  COGS = 120 * ฿10.6667 = ฿1,280.00

Remaining:    30 units * ฿10.6667 = ฿320.00

Purchase 3:   80 units @ ฿11.50
  Total:     110 units, Value = ฿320.00 + ฿920.00 = ฿1,240.00
  Average Cost = ฿1,240.00 / 110 = ฿11.2727
```

### 3.3 แบบจำลองข้อมูล

ไม่ต้องการ lot tracking แต่ละคู่ product-warehouse รักษาค่าเฉลี่ยที่เดินอยู่:

```
inventory_balance:
  - product_id       (FK, composite PK)
  - warehouse_id     (FK, composite PK)
  - quantity          (decimal)         -- ปริมาณคงเหลือปัจจุบัน
  - average_cost      (decimal)         -- ต้นทุนเฉลี่ยถ่วงน้ำหนักปัจจุบัน
  - total_value       (decimal)         -- quantity * average_cost
  - updated_at        (timestamp)

inventory_transaction:
  - transaction_id   (PK)
  - product_id       (FK)
  - warehouse_id     (FK)
  - transaction_type (enum: IN, OUT, ADJUST)  -- รับ ใช้ ปรับ
  - quantity          (decimal)
  - unit_cost         (decimal)         -- ต้นทุนเฉลี่ยตอนทำธุรกรรม
  - total_cost        (decimal)
  - reference_doc     (varchar)
  - created_at        (timestamp)
```

### 3.4 อัลกอริทึม

```
function receiveStock_AVG(productId, warehouseId, receivedQty, purchaseCost):
    balance = getBalance(productId, warehouseId)

    newTotalValue = (balance.quantity * balance.average_cost)
                  + (receivedQty * purchaseCost)
    newTotalQty   = balance.quantity + receivedQty
    newAvgCost    = newTotalValue / newTotalQty

    balance.quantity     = newTotalQty
    balance.average_cost = newAvgCost
    balance.total_value  = newTotalValue

    recordTransaction(IN, receivedQty, purchaseCost)


function issueStock_AVG(productId, warehouseId, requiredQty):
    balance = getBalance(productId, warehouseId)

    if balance.quantity < requiredQty:
        throw InsufficientStockError  // สต๊อกไม่พอ

    totalCost = requiredQty * balance.average_cost

    balance.quantity    -= requiredQty
    balance.total_value -= totalCost
    // ค่าเฉลี่ยไม่เปลี่ยนตอน issue

    recordTransaction(OUT, requiredQty, balance.average_cost)

    return totalCost
```

### 3.5 ข้อดี

| ข้อดี | รายละเอียด |
|-----------|---------|
| แบบจำลองข้อมูลง่ายกว่า | ไม่ต้องการ lot tracking |
| ดำเนินการเร็วกว่า | O(1) ทั้งการรับและการ issue |
| ต้องการพื้นที่จัดเก็บต่ำกว่า | Record เดียวต่อคู่ product-warehouse |
| ลดความผันผวนของราคา | ลดผลกระทบของความผันผวนของราคา |

### 3.6 ข้อเสีย

| ข้อเสีย | รายละเอียด |
|--------------|---------|
| ไม่มี traceability ของต้นทุน | ไม่สามารถ trace ต้นทุนกลับไปยังการซื้อเฉพาะ |
| ปัญหาการปัดเศษ | การคำนวณซ้ำ ๆ อาจสะสม rounding error |
| ไม่เหมาะกับสินค้าเน่าเสียง่าย | ไม่มี batch/expiry date tracking ในตัว |
| ความซับซ้อนของการคำนวณใหม่ | การแก้ไขข้อผิดพลาดในอดีตต้องคำนวณ transaction ที่ตามมาทั้งหมดใหม่ |

---

## 4. ตารางเปรียบเทียบ

| เกณฑ์ | FIFO | Weighted Average |
|----------|------|-----------------|
| **ความซับซ้อน** | สูง (จัดการ lot) | ต่ำ (record balance เดียว) |
| **ประสิทธิภาพ** | O(n) ต่อการ issue (n = จำนวน lot) | O(1) ต่อการ issue |
| **พื้นที่จัดเก็บ** | สูงกว่า (lot records) | ต่ำกว่า (balance เดียว) |
| **ความแม่นยำของต้นทุน** | ต้นทุนต่อหน่วยที่ถูกต้อง | ค่าเฉลี่ยโดยประมาณ |
| **Traceability** | ครบถ้วน (ระดับ lot) | ไม่มี (รวบ) |
| **ความผันผวนของราคา** | สะท้อนการเปลี่ยนแปลงต้นทุนจริง | ลดความผันผวน |
| **สินค้าเน่าเสียง่าย** | เหมาะอย่างยิ่ง | ไม่เหมาะ |
| **การแก้ไขข้อผิดพลาด** | ง่ายกว่า (ปรับ lot เฉพาะ) | ยากกว่า (คำนวณ chain ทั้งหมดใหม่) |
| **การรายงาน** | วิเคราะห์ต้นทุนละเอียด | รายงานง่ายกว่า |
| **มาตรฐานบัญชี** | ยอมรับโดย IFRS และ GAAP | ยอมรับโดย IFRS และ GAAP |

---

## 5. ตัวอย่างเปรียบเทียบเชิงตัวเลข

ใช้ transaction เดียวกัน เปรียบเทียบผลลัพธ์:

```
Transactions:
  1. Receive 100 units @ ฿10.00
  2. Receive  50 units @ ฿12.00
  3. Issue   120 units
  4. Receive  80 units @ ฿11.50

                            FIFO            Weighted Average
                            ----            ----------------
After Receive 1:
  On Hand                   100             100
  Inventory Value           ฿1,000.00       ฿1,000.00
  Unit Cost                 ฿10.00          ฿10.00

After Receive 2:
  On Hand                   150             150
  Inventory Value           ฿1,600.00       ฿1,600.00
  Unit Cost                 Varies by lot   ฿10.6667

After Issue 120 units:
  COGS                      ฿1,240.00       ฿1,280.00
  On Hand                   30              30
  Inventory Value           ฿360.00         ฿320.00

After Receive 3:
  On Hand                   110             110
  Inventory Value           ฿1,280.00       ฿1,240.00
```

**ข้อสังเกตสำคัญ**: ในสถานการณ์ราคาขาขึ้น FIFO ให้ COGS ต่ำกว่าและมูลค่าสินค้าคงเหลือปลายงวดสูงกว่าเมื่อเทียบกับ Weighted Average

---

## 6. ข้อพิจารณาด้านการออกแบบแพลตฟอร์ม

### 6.1 รองรับทั้งสองวิธี

แพลตฟอร์มควรอนุญาตให้ตั้งค่าที่ระดับ **องค์กรหรือหมวดสินค้า**:

```
organization_settings:
  - org_id                (FK)
  - costing_method        (enum: FIFO, AVERAGE)   -- วิธี costing
  - allow_negative_stock  (boolean, default: false) -- อนุญาตสต๊อกติดลบ
  - decimal_precision     (integer, default: 4)     -- ความละเอียดทศนิยม

-- หรือตั้งค่าตามหมวดสินค้า:
product_category:
  - category_id           (PK)
  - costing_method        (enum: FIFO, AVERAGE)   -- วิธี costing
```

### 6.2 รูปแบบสถาปัตยกรรม (Strategy Pattern)

```
interface InventoryCostingStrategy:
    receiveStock(productId, warehouseId, qty, cost)    // รับ stock
    issueStock(productId, warehouseId, qty) -> totalCost  // issue stock
    getValuation(productId, warehouseId) -> value       // คำนวณการตีมูลค่า
    recalculate(productId, warehouseId, fromDate)       // คำนวณใหม่

class FIFOStrategy implements InventoryCostingStrategy:
    // ประมวลผลตาม lot

class AverageCostStrategy implements InventoryCostingStrategy:
    // ประมวลผลค่าเฉลี่ยถ่วงน้ำหนัก

class CostingService:
    getStrategy(productId) -> InventoryCostingStrategy:
        method = getConfiguredMethod(productId)
        if method == FIFO:
            return FIFOStrategy()
        else:
            return AverageCostStrategy()
```

### 6.3 Workflow การประมวลผล Transaction

```
Receiving Stock:
  1. ตรวจสอบเอกสาร purchase order / goods receipt
  2. กำหนดวิธี costing สำหรับสินค้า
  3. ดำเนินการรับผ่าน Strategy ที่เหมาะสม
  4. บันทึก inventory movement พร้อมรายละเอียดต้นทุน
  5. อัปเดต general ledger (Debit: Inventory, Credit: Accounts Payable/Cash)

Issuing Stock:
  1. ตรวจสอบเอกสาร sales order / stock requisition
  2. ตรวจสอบปริมาณสต๊อกที่มี
  3. กำหนดวิธี costing สำหรับสินค้า
  4. ดำเนินการ issue ผ่าน Strategy ที่เหมาะสม -> ได้ COGS
  5. บันทึก inventory movement พร้อมรายละเอียดต้นทุน
  6. อัปเดต general ledger (Debit: COGS, Credit: Inventory)
```

### 6.4 Edge Cases ที่ต้องจัดการ

| Edge Case | การจัดการ FIFO | การจัดการ Weighted Average |
|-----------|--------------|-------------------------|
| **สต๊อก 0 + รับเข้า** | สร้าง lot ใหม่ | ตั้ง average cost = ต้นทุนซื้อ |
| **คืนผู้ขาย** | กลับ lot เฉพาะ | คำนวณค่าเฉลี่ยใหม่ |
| **ลูกค้าคืน** | สร้าง lot ใหม่ด้วยต้นทุนเดิม | คำนวณค่าเฉลี่ยใหม่ด้วยต้นทุนคืน |
| **ปรับสต๊อก (+)** | สร้าง lot ด้วยต้นทุนที่ระบุ | คำนวณค่าเฉลี่ยใหม่ |
| **ปรับสต๊อก (-)** | บริโภคจาก lot เก่าที่สุด | ลดปริมาณ คงค่าเฉลี่ยเดิม |
| **โอนระหว่างคลัง** | ย้าย lot records | issue ที่ average cost รับที่ต้นทุนเดียวกัน |
| **สต๊อกติดลบ (ถ้าอนุญาต)** | ติดตาม lot ติดลบ | อนุญาตปริมาณติดลบ คงค่าเฉลี่ยเดิม |
| **การปัดเศษ** | ปัดเศษต่อ lot | เสี่ยง error สะสม - ใช้ precision สูง |

### 6.5 การคำนวณใหม่และการแก้ไขข้อผิดพลาด

เมื่อ transaction ในอดีตถูกแก้ไข transaction ที่ตามมาทั้งหมดต้องถูกคำนวณใหม่:

```
function recalculate(productId, warehouseId, fromDate):
    // รีเซ็ต balance เป็นสถานะก่อน fromDate
    balance = getSnapshotBefore(fromDate)

    // เล่น transaction ทั้งหมดใหม่ตามลำดับเวลา
    transactions = getTransactions(productId, warehouseId, fromDate)
                    .orderBy(created_at ASC)

    for each txn in transactions:
        if txn.type == IN:
            strategy.receiveStock(txn.qty, txn.cost)
        else if txn.type == OUT:
            txn.updated_cost = strategy.issueStock(txn.qty)
            // อัปเดต transaction record ด้วยต้นทุนที่แก้แล้ว

    // บันทึก balance สุดท้าย
    saveBalance(balance)
```

---

## 7. ข้อกำหนดด้านการรายงาน

### 7.1 รายงานหลัก

| รายงาน | คำอธิบาย | ข้อมูล FIFO | ข้อมูล Weighted Average |
|--------|-------------|-----------|----------------------|
| **Inventory Valuation** | มูลค่าปัจจุบันของสินค้าคงคลังทั้งหมด | ผลรวมมูลค่า lot ทั้งหมด | Quantity * Average Cost |
| **COGS Report** | ต้นทุนสินค้าที่ issue ในงวด | ต้นทุน lot จริงที่บริโภค | ต้นทุนเฉลี่ยตอน issue |
| **Stock Movement Report** | การรับ/ issue ทั้งหมดพร้อมต้นทุน | รายละเอียดต่อ lot | ต้นทุนเฉลี่ยต่อ transaction |
| **Inventory Aging Report** | อายุสินค้าคงคลังตาม lot | รองรับโดยตรง | ไม่มี |
| **Price Variance** | การเปลี่ยนแปลงราคาซื้อ | เห็นได้ต่อ lot | ดูดซับเข้าค่าเฉลี่ย |

### 7.2 Audit Trail

ทุก transaction ต้องบันทึก:
- ใครเป็นผู้กระทำ
- เกิดขึ้นเมื่อใด
- มีอะไรเปลี่ยน (ค่าก่อน/หลัง)
- ทำไม (เอกสารอ้างอิง รหัสเหตุผล)
- วิธี costing ที่ใช้และรายละเอียดการคำนวณต้นทุน

---

## 8. คำแนะนำ

| Scenario | วิธีที่แนะนำ |
|----------|-------------------|
| Food & Beverage / สินค้าเน่าเสียง่าย | **FIFO** (ต้องการ batch/expiry tracking) |
| ยา | **FIFO** (กฎหมายกำหนดให้ติดตาม lot) |
| สินค้าโภคภัณฑ์ / สินค้าจำนวนมาก | **Weighted Average** (ง่ายกว่า ผันผวนราคา) |
| ค้าปลีกปริมาณสูง | **Weighted Average** (ประสิทธิภาพ ความเรียบง่าย) |
| การผลิตด้วยวัตถุดิบ | **Weighted Average** (วัตถุดิบถูกผสม) |
| อิเล็กทรอนิกส์ / สินค้า serialized | **FIFO** (ต้องการ serial/batch tracking) |
| องค์กรหลายวิธี | **รองรับทั้งสองวิธี** ตั้งค่าตามหมวด |

### คำแนะนำสุดท้ายสำหรับแพลตฟอร์ม

**รองรับทั้งสองวิธี** โดยใช้แนวทาง Strategy Pattern ซึ่งให้:

1. **ความยืดหยุ่น** - หมวดสินค้าต่างกันใช้วิธีต่างกัน
2. **การปฏิบัติตามกฎหมาย** - ตรงตามข้อกำหนดของอุตสาหกรรมและมาตรฐานบัญชีหลากหลาย
3. **เส้นทางการย้าย** - องค์กรเปลี่ยนวิธีได้ที่จุดสิ้นสุดของงวดบัญชี
4. **ความได้เปรียบในการแข่งขัน** - ดึงดูดตลาดที่กว้างกว่าแพลตฟอร์มที่มีวิธีเดียว

เริ่มด้วย **Weighted Average** เป็น default (พัฒนาและ test ง่ายกว่า) แล้วเพิ่มการรองรับ **FIFO** ทั้งสองวิธีใช้โครงสร้างตาราง transaction เดียวกัน ต่างกันเพียงวิธีคำนวณและเก็บต้นทุน


TEST
