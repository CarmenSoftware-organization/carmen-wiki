# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Nature

**carmen-wiki** is a **user manual for developers and testers** of the Carmen **inventory ERP** product. Content is Markdown rendered by [Wiki.js](https://js.wiki/). There is no application code, no package manager, no build pipeline, and no test suite in this repo — tasks here are always content edits.

Audience and scope:
- Readers are developers building inventory features and QA engineers testing them — not end users, not architects designing greenfield platforms.
- Inventory ERP topics are in scope: costing methods, GRN/receiving flow, physical count, spot check, valuation, transaction edge cases, data models, algorithms.
- Other Carmen modules (PR Approval, vendor catalogs, business unit management) are out of scope **unless** they directly interact with inventory.
- Useful page shapes: developer how-tos, test scenarios, expected behaviors, edge-case matrices, algorithm pseudo-code, data-model references.

Work is organized as `<locale>/<book>/<module>/`. Two books are defined: **Carmen Inventory** (existing content — costing, GRN, physical count, etc.) and **Carmen Platform** (admin product — clusters, business units, users, report templates). The language-root pages `en/home.md` and `th/home.md` (Wiki.js URL `/en/home`, `/th/home` — locale roots must live inside their locale folder for Wiki.js git-storage to assign them the correct locale) are the two-card landings; each book has its own `<book>.md` sibling page (e.g. `en/inventory.md` beside `en/inventory/`) that opens the book. Each `.md` file is a standalone wiki page. Wiki.js handles the language toggle natively across the locale trees, so individual pages should not include inline cross-locale links. The `.specs/` directory is hidden meta and stays at the repo root.

## Multi-book layout

| Book | Location | Audience |
|------|----------|----------|
| Inventory | `en/inventory/`, `th/inventory/` | Developers and QA working on Carmen Inventory ERP |
| Platform | `en/platform/`, `th/platform/` | Developers and support working on the platform admin product |

Screenshots live under `assets/screenshots/<book>/<module>/<slug>.png`.

When adding a new page, place it under the correct book. Cross-book content (e.g. how Inventory interacts with cluster-scoped permissions) goes in the most-affected book and links across.

## Wiki.js Page Format

Every page must begin with Wiki.js YAML frontmatter. Match the existing pattern in `en/costing/calculation-methods.md`:

```yaml
---
title: <Human-readable page title>
description: <One-line summary used by Wiki.js search and previews>
published: true
date: <ISO 8601 timestamp of last edit>
tags: <comma-separated tags>
editor: markdown
dateCreated: <ISO 8601 timestamp of original creation — never change after creation>
---
```

When editing an existing page, update `date` to the current timestamp but leave `dateCreated` untouched. When creating a new page, set both to the same value.

## Documentation Conventions

Conventions established by the existing wiki content — match them when adding or editing pages:

- **Numbered section hierarchy**: top-level sections use `## 1. Title`, `## 2. Title`, with `### 2.1`, `### 2.2` subsections. Keeps cross-references stable.
- **Comparison tables** for design trade-offs (advantages/disadvantages, FIFO vs. Weighted Average, etc.) — prefer tables over prose bullet lists when comparing options.
- **Pseudo-code blocks** (language-agnostic, fenced as ``` with no language tag) for algorithms and data models, rather than real TypeScript/SQL. The wiki documents *platform design*, not implementation in any single repo's stack.
- **Currency in examples**: Thai Baht (`฿`) — Carmen is a Thailand-based hospitality platform.
- **Edge-case sections**: design docs typically end with an "Edge Cases" table and a "Recommendations" section. Preserve this structure.

## Project Context

**carmen-wiki** documents the inventory ERP slice of the Carmen Software platform, a hospitality supply chain management system. The wiki is the reference manual that developers and testers consult while working on inventory features across the repos below.

### Reference Repositories (source of truth — always consult before writing)

Sibling directories under `/Users/samutpra/GitHub/carmensoftware-organize/`. Before drafting or revising a page, read the corresponding source rather than inventing details. Check each path exists on the current machine before reading.

| Role | Path | Use for |
|------|------|---------|
| **Concepts / design docs** | `../carmen/docs/` | Canonical concept reference. Topic folders for inventory-management, costing, recipe, purchase-request/order-management, GRN, store-requisitions, vendor-pricelist, product-management, workflow-permissions, business-rules, API/technical specs, prd, use-cases, mobile-app, prisma-schema, etc. Carmen-wiki pages should synthesize from here. |
| **Frontend** | `../carmen-inventory-frontend-react/` | Vite + React SPA inventory UI — React Router, TypeScript, Tailwind, Bun, Vitest, Playwright. Source of truth for screen/component behavior. Has its own `CLAUDE.md` and `DESIGN.md`. |
| **Platform admin** | `../carmen-platform/` | React/TypeScript SPA for cluster/BU/user/report-template management — source of truth for the Platform book |
| **Backend (main)** | `../carmen-turborepo-backend-v2/` | Turborepo monorepo (`apps/`, `packages/`, Bun, Docker, k8s). REST API surface. |
| **Backend (reports)** | `../micro-report/` | Go microservice for reporting (controllers, services, queues, migrations). |
| **Backend (cron)** | `../micro-cronjobs/` | Go microservice for scheduled inventory jobs. |
| **API contracts** | `../carmen-turborepo-backend-bruno/` | Bruno API collections — verify exact request/response shapes here, not by guessing. |
| **E2E tests** | `../carmen-inventory-frontend-e2e/` | Playwright suite. Existing tests are the executable spec — consult before writing test-scenario or expected-behavior pages. |

When in doubt about what the system actually does: implementation (frontend/backend) and E2E tests beat `../carmen/docs/`; `../carmen/docs/` beats memory or speculation.

### Domain

Hospitality supply chain management — modules include Dashboard, Receiving (GRN), PR Approval, Store Requisition, Physical Count, Spot Check, vendor/product catalogs, and business unit/cluster management.
