---
title: Request for Quotation
description: Outbound request-for-price (RFQ) sent to one or more vendors — collects bids before negotiating a new pricelist.
published: true
date: 2026-05-16T15:00:00.000Z
tags: vendor-pricelist, rfq, procurement, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Request for Quotation

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/vendor-management/request-price-list`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Request Price List is the procurement-initiated RFQ surface. The Purchaser or Procurement Manager bundles a set of products and quantities, picks candidate vendors, and dispatches the request via email / portal. Returned quotes are captured as draft pricelist rows or directly fed into a new [[vendor-pricelist]] entry. The flow is upstream of every PR / PO so the wiki documents it as a vendor-side process rather than a transactional document.

## 2. Related Modules

- [[vendor-pricelist]] — the catalogue RFQs ultimately update
- [[master-data/vendor]] — vendors the RFQ is dispatched to
- [[templates/price-list]] — request scaffold reuse

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/vendor-management/request-price-list/` — frontend page
