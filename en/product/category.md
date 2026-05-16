---
title: Product Category
description: Hierarchical category taxonomy for products — drives catalogue navigation, cost-band reporting, and category-based permission filters.
published: true
date: 2026-05-16T15:00:00.000Z
tags: product, category, taxonomy, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Product Category

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/product-management/category`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Product Category is the classification layer over the product master. Categories are hierarchical (e.g. `Food > Beverage > Coffee Beans`) and assigned per product to drive catalogue navigation in PR / PO line entry, category-level cost reporting, and the category-scoped permission filters used by Purchaser and Store Keeper roles. Maintained by the Product Admin persona.

## 2. Related Modules

- [[product]] — the master this taxonomy classifies
- [[product/03-user-flow-product-admin]] — Product Admin maintains the tree
- [[access-control/permission]] — category-scoped permission rules

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/product-management/category/` — frontend page
