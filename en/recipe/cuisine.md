---
title: Cuisine
description: Cuisine catalogue — regional / style label applied to recipes for menu segmentation (Thai, Italian, French, fusion, etc.).
published: true
date: 2026-05-16T15:00:00.000Z
tags: recipe, cuisine, taxonomy, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Cuisine

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/operation-plan/cuisine`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Cuisine is a flat catalogue (no hierarchy) labelling each recipe with its regional / style origin. Used downstream by the menu-engineering surface to filter recipes for property-specific outlets. Distinct from [[recipe/category]] which is functional / mealtype-driven; cuisine is geographical / cultural.

## 2. Related Modules

- [[recipe]] — recipes tagged with cuisine
- [[recipe/category]] — sibling taxonomy on a different axis

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/operation-plan/cuisine/` — frontend page
