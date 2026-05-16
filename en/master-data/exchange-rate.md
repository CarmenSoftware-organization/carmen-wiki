---
title: Exchange Rate
description: Dated history of currency-to-base-currency conversion rates — every transactional document snapshots the rate effective on its document date.
published: true
date: 2026-05-16T15:00:00.000Z
tags: master-data, exchange-rate, currency, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Exchange Rate

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/config/exchange-rate`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Exchange Rate (`tb_exchange_rate`) is the dated companion to [[master-data/currency]]. Each row keys on `(currency_id, effective_date)` with a `Decimal(15, 5)` rate to the BU's base currency. Transactional documents (PR / PO / GRN / pricelist) snapshot the rate effective on their document date at submit time and freeze it for the life of the document — re-approving does not re-fetch. The costing engine reads the same source for FX revaluation on credit-note-amount adjustments and period close. The rate feed is typically populated daily from an external FX provider.

## 2. Related Modules

- [[master-data/currency]] — currency catalogue this dates
- [[costing]] — `COST_CALC_005` credit-note FX revaluation reads here
- [[purchase-request]], [[purchase-order]], [[good-receive-note]] — documents snapshot rates

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/config/exchange-rate/` — frontend page
