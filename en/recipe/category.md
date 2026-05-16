---
title: Recipe Category
description: Hierarchical category taxonomy for recipes — drives menu engineering, cost-band reporting, and recipe library navigation.
published: true
date: 2026-05-16T15:00:00.000Z
tags: recipe, category, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Recipe Category

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/operation-plan/category`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Recipe Category is the classification layer over the recipe master. Categories are typically hierarchical (e.g. `Hot Beverage > Coffee > Specialty`) and assigned per recipe to drive cost-per-category dashboards, allergen / dietary filtering, and the operation-plan navigation in the F&B app. The page is read by the Chef and F&B Manager personas when composing menus.

## 2. Related Modules

- [[recipe]] — the master this taxonomy classifies
- [[recipe/03-user-flow-chef]] — Chef navigates by category when composing

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/operation-plan/category/` — frontend page
