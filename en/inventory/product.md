---
title: Product
description: Product master data — categories, units of measure, locations, and import/export — the catalog every inventory document references.
published: true
date: 2026-06-09T16:25:48.000Z
tags: product, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T07:48:00.000Z
---

# Product

> **At a Glance**
> **Module purpose:** Product catalogue master — codes, categories, base/order/recipe units with conversions, location mapping, allergens, variants, and bulk import/export &nbsp;·&nbsp; **Audience:** Product Administrator, Purchaser, Store Keeper &nbsp;·&nbsp; **Key entities/tables:** `tb_product`, `tb_product_category`, `tb_product_unit_conversion`, `tb_product_location`, `tb_product_variant` &nbsp;·&nbsp; **Sub-pages:** 11

![Product screen](/screenshots/product/index.png)

![Product detail screen](/screenshots/product/detail.png)

## 1. Overview

The Product module is the central master-data catalogue for the ERP. Every product is identified by a unique `productCode`, classified through a **category → sub-category → item group** hierarchy (up to five levels deep), and carries the descriptive, costing, taxation, and packaging attributes that downstream modules consume. English and local-language descriptions, barcode, standard cost, last receiving cost, and quantity/price deviation tolerances live on the product header; extended attributes (weight, shelf life, storage instructions, size, color, allergens, sustainability data) are modelled as typed key-value pairs that can be inherited from the category and overridden at the product level.

A product is measured in a **base inventory unit** with one or more **order units** and **recipe units** layered on top via explicit conversion factors. The conversion table is validated for consistency (bidirectional, non-circular) so that a quantity entered in any unit on any document — PR, PO, GRN, requisition, recipe — can be resolved back to the base unit for valuation. Every product is also activated against one or more **storage locations**, with per-location minimum and maximum thresholds that drive replenishment and the level-check logic in inventory.

Bulk maintenance is a first-class concern. **Import/export** workflows accept Excel and CSV payloads for products, categories, units, and conversion factors with row-level validation, dry-run preview, and a downloadable error report; barcodes, QR codes, and category templates support bulk generation. The combination of validated master data and bulk tooling is what lets new properties and new menu launches go live without one-off entry per item.

## 2. Business Context

Product master is the foundation every other module reads from. A purchase request line, a PO line, a GRN line, a requisition line, a recipe ingredient, a stock balance, a costing record — none of them exist independently of a product. Bad master data corrupts everything downstream: the wrong base unit silently inflates or deflates valuation, a missing conversion factor blocks receiving, a stale category breaks reporting roll-ups, an inactive product still attached to an open recipe causes orders to fail. Hospitality groups operating across multiple properties feel this acutely — a single global product list with property-level location enablement is what keeps the chain consistent while local kitchens stay flexible.

This module is therefore the system of record for the *definition* of an item, not its movements or balances. It feeds product identity and structure to [inventory](/en/inventory/inventory), [vendor-pricelist](/en/inventory/vendor-pricelist), [purchase-request](/en/inventory/purchase-request), [purchase-order](/en/inventory/purchase-order), and [recipe](/en/inventory/recipe), and consumes nothing back from them except usage flags (e.g., "in-use" prevents delete). Getting this layer right — codes, units, categories, locations, allergens — is the precondition for every other module functioning correctly.

## 3. Key Concepts

- **Product Category**: A hierarchical classification node (category → sub-category → item group, up to five levels) used for organisation, reporting roll-ups, and attribute inheritance. Categories can carry required attributes, default values, and business rules that propagate to every product assigned beneath them. Deletion is blocked while any product is still assigned.
- **Base Unit**: The canonical inventory unit of measure for a product (e.g., `KG`, `LITRE`, `EACH`). All stock balances, costs, and valuations are stored in the base unit; every other unit attached to the product is defined relative to it via a conversion factor.
- **Conversion Factor**: The multiplier that translates a quantity expressed in an order unit or recipe unit into the base unit (e.g., 1 `CASE` = 12 `EACH`). Conversions are validated for bidirectional consistency, must avoid cycles, and propagate to PR/PO/GRN/recipe lines so the system can always resolve the same physical quantity regardless of how it is entered.
- **Location Mapping**: The assignment of a product to one or more storage locations (warehouses, stores, kitchens), each with optional minimum and maximum quantity thresholds. Only locations a product is mapped to can hold a balance for that product; the mapping also drives par-level alerts and replenishment suggestions.
- **Active/Inactive**: The lifecycle flag controlling whether a product can appear on new documents. Inactive products retain their history (balances, past POs, past recipes) but are excluded from pickers and from new transactions; the status transition is auditable and can be scheduled to take effect on a future date.
- **Barcode**: A scannable identifier (UPC, EAN, CODE128, QR) attached to a product or product variant. Barcodes must be unique, can be generated in bulk, are printable as labels, and are the primary lookup key for mobile receiving, picking, counting, and spot-check workflows.
- **Allergen**: A regulated attribute flagging the presence of allergens (gluten, dairy, nuts, shellfish, etc.) in a product. Allergen data is set on the product, inherited through recipes to the menu item, and surfaced to F&B Operations for guest disclosure and to Procurement when sourcing substitutes.
- **Product Variant**: A specific version of a product distinguished by attribute combinations (size, color, packaging) with its own SKU, optional pricing/costing overrides, and inventory tracking. Variants share the parent product's category and base unit but can carry variant-specific media and sustainability data.
- **Standard Cost / Last Receiving Cost**: The reference costs carried on the product header. Standard cost is the planned/budgeted cost used for variance analysis; last receiving cost is the most recent actual unit cost observed on a GRN, displayed alongside the date and vendor for context. Neither replaces the moving valuation maintained by the costing module.
- **Quantity / Price Deviation Tolerance**: Per-product percentage tolerances (0–100%) that bound how far a downstream document line (PR, PO, GRN) may diverge from the master quantity or price before approval is required. The tolerances trickle down to child records and act as guard-rails against entry errors.
- **Import/Export**: A bulk-load and bulk-extract workflow for products, categories, units, and conversion factors. Imports run row-level validation, support dry-run preview, and emit a downloadable error report; exports support multiple formats and respect the user's saved view and filters.

## 4. Roles and Personas

| Role | Responsibility |
|------|----------------|
| Product Administrator | Owns the catalogue: creates and maintains products, categories, sub-categories, item groups, and units; configures conversion factors, attributes, and location mappings; runs imports/exports and manages product lifecycle (activation, deprecation, deletion). |
| Purchaser | Looks up products to compose PRs and POs, references standard and last receiving costs, verifies order-unit conversions and vendor mappings, and flags missing or stale catalogue entries back to the administrator. |
| Store Keeper | Looks up products during receiving, picking, transfers, and counts; scans barcodes for fast identification; references location thresholds and per-product handling notes (storage instructions, shelf life). |

## 5. Related Modules

**Cross-module flow:**
- [inventory](/en/inventory/inventory) — every inventory balance is keyed by product
- [vendor-pricelist](/en/inventory/vendor-pricelist) — pricelists reference products
- [purchase-request](/en/inventory/purchase-request) — PR lines reference products
- [purchase-order](/en/inventory/purchase-order) — PO lines reference products
- [recipe](/en/inventory/recipe) — recipes reference products as ingredients

**Master configuration:**
- [master-data/unit](/en/inventory/master-data/unit) — base, order, and recipe units of measure plus conversion factors
- [system-config/application-config](/en/inventory/system-config/application-config) — tenant-level defaults (deviation tolerances, barcode policy, attribute schema)
- [reporting-audit/activity](/en/inventory/reporting-audit/activity) — product lifecycle and bulk-import activity log for audit
- [reporting-audit/attachment](/en/inventory/reporting-audit/attachment) — product images, spec sheets, and certificates attached to each product

## 6. Reference Sources

- Concepts: `../carmen/docs/product-management/`
- Frontend: `../carmen-inventory-frontend-react/`
- Backend: `../carmen-turborepo-backend-v2/`
- API contracts: `../carmen-turborepo-backend-bruno/`
- E2E tests: `../carmen-inventory-frontend-e2e/`

## 7. Pages in This Module

- [01 — Data Model](/en/inventory/product/01-data-model) — Entities, fields, relationships, and enums (Prisma-derived).
- [02 — Business Rules](/en/inventory/product/02-business-rules) — Validation, calculation / inheritance, authorization, lifecycle, and cross-module rules.
- [03 — User Flow](/en/inventory/product/03-user-flow) — Product record lifecycle, plus persona index.
  - [Product Administrator](/en/inventory/product/03-user-flow-product-admin)
  - [Purchaser](/en/inventory/product/03-user-flow-purchaser)
  - [Store Keeper](/en/inventory/product/03-user-flow-store-keeper)
- [04 — Test Scenarios](/en/inventory/product/04-test-scenarios) — Persona scope, cross-persona scenarios, E2E mapping.
  - [Product Administrator](/en/inventory/product/04-test-scenarios-product-admin)
  - [Purchaser](/en/inventory/product/04-test-scenarios-purchaser)
  - [Store Keeper](/en/inventory/product/04-test-scenarios-store-keeper)
