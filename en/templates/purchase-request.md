---
title: Purchase Request Template
description: Reusable PR scaffold — frequently-purchased line bundles saved as templates so a Requestor can instantiate a PR with one click.
published: true
date: 2026-05-16T16:00:00.000Z
tags: templates, purchase-request, configuration, carmen-software
editor: markdown
dateCreated: 2026-05-16T15:00:00.000Z
---

# Purchase Request Template

## 1. Overview

> **Status:** Documentation in progress — page registered for parity with the app navigation at `/procurement/purchase-request-template`. Detail to be filled when the corresponding module captures land. For now this page serves as the navigation target so testers and developers can confirm the slug exists and reach the related concepts.

Purchase Request Templates (`tb_purchase_request_template`, `tb_purchase_request_template_detail`) are seed-only documents — they do not enter a workflow themselves. When a Requestor uses **Create from Template**, the template's header (currency, workflow, type) and detail rows are cloned into a brand-new `tb_purchase_request` at `pr_status = draft`. The template itself is unchanged; the new PR is independent and can be edited freely before submission.

## 2. Related Modules

- [[purchase-request]] — the document type templates instantiate
- [[purchase-request/03-user-flow-requestor]] — REQ-HP-06 scenario uses the template path

## 3. Reference Sources

- `../carmen-inventory-frontend/app/(root)/(protected)/procurement/purchase-request-template/` — frontend page
- `../carmen/docs/purchase-request-management/PR-User-Experience.md` — template-based creation flow
