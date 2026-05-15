---
title: <Module> — Business Rules
description: Validation, calculation, authorization, and posting rules for <module>.
published: true
date: <ISO 8601 timestamp>
tags: <module-slug>, business-rules, inventory, carmen-software
editor: markdown
dateCreated: <ISO 8601 timestamp>
---

# <Module> — Business Rules

## 1. Overview
<Scope: which rule categories apply, which documents/entities they govern.>

## 2. Validation Rules
| Rule ID | Condition | When enforced | Error / behaviour |
| ------- | --------- | ------------- | ----------------- |

<Rules enforced at create/edit/submit. Rule IDs follow `<MODULE-PREFIX>_VAL_NNN` where the prefix matches the module (e.g. PR_VAL_001 for purchase-request).>

## 3. Calculation Rules
<Formulas for totals, taxes, conversions, rounding. Show the formula plus a small worked example. Reference any constants or system parameters.>

## 4. Authorization Rules
<Who can do what — by role, by document status, by amount threshold. Use a matrix or per-role bullet list.>

## 5. Posting Rules
<What happens at posting: stock movements (which inventory entity is touched, in what direction), GL journal entries (debits/credits), inter-module side effects (e.g. closes the related PO line, triggers AP commitment).>

## 6. Cross-Module Rules
<Rules involving other modules — e.g. GRN must reference an open PO line, store-requisition can only issue if source location has sufficient stock and source location is INVENTORY type.>

## 7. References
- `../carmen/docs/<source-folder>/` — specific files describing business rules.
- Backend rule implementation (if relevant): `../carmen-turborepo-backend-v2/apps/<app>/src/<module>/` (point at the file/class).
