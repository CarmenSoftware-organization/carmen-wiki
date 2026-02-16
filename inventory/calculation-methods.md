---
title: Inventory Costing Methods: FIFO vs. Weighted Average
description: Analysis of inventory costing methods: FIFO vs. Weighted Average for the Carmen Software platform
published: true
date: 2026-02-16T11:24:32.555Z
tags: inventory, costing, fifo, weighted-average, carmen-software
editor: markdown
dateCreated: 2026-02-16T11:19:18.975Z
---

# Inventory Costing Methods: FIFO vs. Weighted Average

## 1. Overview

This document analyzes two primary inventory costing methods for the inventory management platform:

- **FIFO (First-In, First-Out)**: Items purchased first are sold/used first
- **Weighted Average Cost**: All items are valued at a weighted average cost

Both methods are used to determine **Cost of Goods Sold (COGS)** and **ending inventory value**, which directly impact financial reporting and operational decision-making.

---

## 2. FIFO (First-In, First-Out)

### 2.1 Concept

FIFO assumes that the oldest inventory is consumed first. Each purchased lot retains its original cost until it is fully consumed.

### 2.2 How It Works

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

### 2.3 Data Model

Each inventory movement must track **lot/batch** information:

```
inventory_lot:
  - lot_id          (PK)
  - product_id      (FK)
  - warehouse_id    (FK)
  - purchase_date   (timestamp)       -- Purchase date
  - quantity         (decimal)         -- Remaining quantity in this lot
  - unit_cost        (decimal)         -- Original purchase cost
  - created_at       (timestamp)

inventory_transaction:
  - transaction_id   (PK)
  - product_id       (FK)
  - warehouse_id     (FK)
  - transaction_type (enum: IN, OUT, ADJUST)  -- Receive, Issue, Adjust
  - quantity          (decimal)
  - reference_doc     (varchar)        -- PO number, SO number, etc.
  - created_at        (timestamp)

inventory_transaction_lot:
  - transaction_id   (FK)
  - lot_id           (FK)
  - quantity          (decimal)        -- Quantity consumed from this lot
  - unit_cost         (decimal)        -- Cost at time of consumption
```

### 2.4 Algorithm (Stock Issuance)

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
        throw InsufficientStockError  // Insufficient stock

    return totalCost
```

### 2.5 Advantages

| Advantage | Details |
|-----------|---------|
| Accurate cost tracking | Each unit retains its actual purchase cost |
| Matches physical flow of goods | Ideal for perishable goods |
| Better in rising price environments | Lower COGS, higher reported profit, higher inventory value |
| Full audit trail | Fully traceable back to purchase source |

### 2.6 Disadvantages

| Disadvantage | Details |
|--------------|---------|
| High complexity | Must track each individual lot |
| Higher storage requirements | Each lot requires its own record |
| Slower issuance | Must iterate through lots sequentially |
| Partial lot management | Lots may be partially consumed, adding complexity |

---

## 3. Weighted Average Cost

### 3.1 Concept

Weighted average cost combines the cost of all available items into a single weighted average. Every unit in stock has the same cost at any given point in time.

### 3.2 How It Works

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

### 3.3 Data Model

No lot tracking required. Each product-warehouse pair maintains a running average:

```
inventory_balance:
  - product_id       (FK, composite PK)
  - warehouse_id     (FK, composite PK)
  - quantity          (decimal)         -- Current quantity on hand
  - average_cost      (decimal)         -- Current weighted average cost
  - total_value       (decimal)         -- quantity * average_cost
  - updated_at        (timestamp)

inventory_transaction:
  - transaction_id   (PK)
  - product_id       (FK)
  - warehouse_id     (FK)
  - transaction_type (enum: IN, OUT, ADJUST)  -- Receive, Issue, Adjust
  - quantity          (decimal)
  - unit_cost         (decimal)         -- Average cost at time of transaction
  - total_cost        (decimal)
  - reference_doc     (varchar)
  - created_at        (timestamp)
```

### 3.4 Algorithm

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
        throw InsufficientStockError  // Insufficient stock

    totalCost = requiredQty * balance.average_cost

    balance.quantity    -= requiredQty
    balance.total_value -= totalCost
    // Average cost does not change on issuance

    recordTransaction(OUT, requiredQty, balance.average_cost)

    return totalCost
```

### 3.5 Advantages

| Advantage | Details |
|-----------|---------|
| Simpler data model | No lot tracking required |
| Faster operations | O(1) for both receiving and issuing |
| Lower storage requirements | Single record per product-warehouse pair |
| Smooths price volatility | Reduces the impact of price fluctuations |

### 3.6 Disadvantages

| Disadvantage | Details |
|--------------|---------|
| No cost traceability | Cannot trace cost back to a specific purchase |
| Rounding issues | Repeated calculations may accumulate rounding errors |
| Not suitable for perishables | No built-in batch/expiry date tracking |
| Recalculation complexity | Correcting past errors requires recalculating all subsequent transactions |

---

## 4. Comparison Table

| Criteria | FIFO | Weighted Average |
|----------|------|-----------------|
| **Complexity** | High (lot management) | Low (single balance record) |
| **Performance** | O(n) per issuance (n = number of lots) | O(1) per issuance |
| **Storage** | Higher (lot records) | Lower (single balance) |
| **Cost Accuracy** | Exact per-unit cost | Averaged approximation |
| **Traceability** | Complete (lot-level) | None (aggregated) |
| **Price Volatility** | Reflects actual cost changes | Smooths volatility |
| **Perishable Goods** | Highly suitable | Not suitable |
| **Error Correction** | Easier (adjust specific lot) | Harder (recalculate entire chain) |
| **Reporting** | Detailed cost analysis | Simpler reporting |
| **Accounting Standards** | Accepted by IFRS and GAAP | Accepted by IFRS and GAAP |

---

## 5. Numerical Comparison Example

Using the same transactions, compare the results:

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

**Key Observation**: In a rising price scenario, FIFO results in lower COGS and higher ending inventory value compared to Weighted Average.

---

## 6. Platform Design Considerations

### 6.1 Supporting Both Methods

The platform should allow configuration at the **organization or product category** level:

```
organization_settings:
  - org_id                (FK)
  - costing_method        (enum: FIFO, AVERAGE)   -- Costing method
  - allow_negative_stock  (boolean, default: false) -- Allow negative stock
  - decimal_precision     (integer, default: 4)     -- Decimal precision

-- Or configure by product category:
product_category:
  - category_id           (PK)
  - costing_method        (enum: FIFO, AVERAGE)   -- Costing method
```

### 6.2 Architecture Pattern (Strategy Pattern)

```
interface InventoryCostingStrategy:
    receiveStock(productId, warehouseId, qty, cost)    // Receive stock
    issueStock(productId, warehouseId, qty) -> totalCost  // Issue stock
    getValuation(productId, warehouseId) -> value       // Get inventory valuation
    recalculate(productId, warehouseId, fromDate)       // Recalculate

class FIFOStrategy implements InventoryCostingStrategy:
    // Lot-based processing

class AverageCostStrategy implements InventoryCostingStrategy:
    // Weighted average processing

class CostingService:
    getStrategy(productId) -> InventoryCostingStrategy:
        method = getConfiguredMethod(productId)
        if method == FIFO:
            return FIFOStrategy()
        else:
            return AverageCostStrategy()
```

### 6.3 Transaction Processing Workflow

```
Receiving Stock:
  1. Validate purchase order / goods receipt document
  2. Determine costing method for the product
  3. Execute receiving via the appropriate Strategy
  4. Record inventory movement with cost details
  5. Update general ledger (Debit: Inventory, Credit: Accounts Payable/Cash)

Issuing Stock:
  1. Validate sales order / stock requisition document
  2. Verify available stock quantity
  3. Determine costing method for the product
  4. Execute issuance via the appropriate Strategy -> obtain COGS
  5. Record inventory movement with cost details
  6. Update general ledger (Debit: COGS, Credit: Inventory)
```

### 6.4 Edge Cases to Handle

| Edge Case | FIFO Handling | Weighted Average Handling |
|-----------|--------------|-------------------------|
| **Zero stock + receive** | Create new lot | Set average cost = purchase cost |
| **Return to vendor** | Reverse specific lot | Recalculate average |
| **Customer return** | Create new lot with original cost | Recalculate average with return cost |
| **Stock adjustment (+)** | Create lot with specified cost | Recalculate average |
| **Stock adjustment (-)** | Consume from oldest lot | Reduce quantity, keep current average cost |
| **Inter-warehouse transfer** | Move lot records | Issue at average cost, receive at same cost |
| **Negative stock (if allowed)** | Track negative lots | Allow negative quantity, keep average cost |
| **Rounding** | Round per lot | Risk of accumulated errors - use high precision |

### 6.5 Recalculation and Error Correction

When past transactions are corrected, all subsequent transactions must be recalculated:

```
function recalculate(productId, warehouseId, fromDate):
    // Reset balance to state before fromDate
    balance = getSnapshotBefore(fromDate)

    // Replay all transactions in chronological order
    transactions = getTransactions(productId, warehouseId, fromDate)
                    .orderBy(created_at ASC)

    for each txn in transactions:
        if txn.type == IN:
            strategy.receiveStock(txn.qty, txn.cost)
        else if txn.type == OUT:
            txn.updated_cost = strategy.issueStock(txn.qty)
            // Update transaction record with corrected cost

    // Save final balance
    saveBalance(balance)
```

---

## 7. Reporting Requirements

### 7.1 Core Reports

| Report | Description | FIFO Data | Weighted Average Data |
|--------|-------------|-----------|----------------------|
| **Inventory Valuation** | Current value of all inventory | Sum of all lot values | Quantity * Average Cost |
| **COGS Report** | Cost of goods issued in the period | Actual lot costs consumed | Average cost at time of issuance |
| **Stock Movement Report** | All receipts/issues with costs | Per-lot details | Average cost per transaction |
| **Inventory Aging Report** | Age of inventory by lot | Directly supported | Not available |
| **Price Variance** | Purchase price changes | Visible per lot | Absorbed into average |

### 7.2 Audit Trail

Every transaction must record:
- Who performed the action
- When it occurred
- What changed (before/after values)
- Why (reference document, reason code)
- Costing method used and cost calculation details

---

## 8. Recommendations

| Scenario | Recommended Method |
|----------|-------------------|
| Food & Beverage / Perishables | **FIFO** (batch/expiry tracking required) |
| Pharmaceuticals | **FIFO** (regulatory requirement for lot tracking) |
| Commodities / Bulk goods | **Weighted Average** (simpler, price volatility) |
| High-volume retail | **Weighted Average** (performance, simplicity) |
| Manufacturing with raw materials | **Weighted Average** (raw materials are blended) |
| Electronics / Serialized items | **FIFO** (serial/batch tracking required) |
| Multi-method organizations | **Support both methods** configured by category |

### Final Recommendation for the Platform

**Support both methods** using the Strategy Pattern approach, which provides:

1. **Flexibility** - Different product categories can use different methods
2. **Regulatory compliance** - Meets requirements across various industries and accounting standards
3. **Migration path** - Organizations can switch methods at accounting period boundaries
4. **Competitive advantage** - Attracts a broader market than single-method platforms

Start with **Weighted Average** as the default (simpler to develop and test), then add **FIFO** support. Both methods use the same transaction table structure, differing only in how costs are calculated and stored.
