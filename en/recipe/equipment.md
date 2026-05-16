---
title: Equipment
description: Kitchen equipment master — referenced from recipes that require specific tools (e.g. sous-vide bath, deep fryer, smoker).
published: true
date: 2026-05-16T15:00:00.000Z
tags: recipe, equipment, master-data, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Equipment

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/operation-plan/equipment`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Equipment is the master of kitchen tools and appliances. Each recipe's preparation steps may reference equipment (`tb_recipe_equipment`) to enable Chef workflow planning — checking that a target outlet has the required tools before adding a recipe to its menu.

## 2. Related Modules

- [[recipe]] — recipes that reference equipment
- [[recipe/equipment-category]] — type classification

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/operation-plan/equipment/` — frontend page
