---
title: Carmen-wiki repo is a user manual for developers and testers of the Carmen inventory ERP
author: Thammanoon
date: 2026-11-09
id: l-bfc71883
scope: repo
status: active
touches:
  - CLAUDE.md
---

## Decided
The carmen-wiki repository is a **user manual targeted at developers and testers** working on Carmen products. As of 2026-05-19 it is a multi-book wiki:
- **Carmen Inventory** book — the original scope, covering the Carmen inventory ERP (developers/QA building or testing inventory features).
- **Carmen Platform** book — new scope, covering the carmen-platform admin SPA (clusters, business units, users, report templates).

It is not a general platform-design wiki spanning every Carmen module — only the two products above.

**Why:** The user clarified the inventory-only scope on 2026-05-15 (correcting an earlier mischaracterization in CLAUDE.md). On 2026-05-19 the user expanded scope to also include the Platform admin product, restructuring the repo into `<locale>/<book>/<module>/` layout.

## Watch out
- Frame new pages from a developer/tester reader's perspective.
- For Carmen Inventory book: costing methods, GRN flow, stock take, valuation, edge cases. Other Carmen modules (PR Approval, vendor catalogs) are out of scope **for this book** unless they directly interact with inventory.
- For Carmen Platform book: cluster/BU/user/report-template management as implemented in `../carmen-platform/`.
- Useful content shapes: developer how-tos, test scenarios, expected behaviors, edge-case matrices, data-model references, algorithm pseudo-code, UI screen reference.
…

_From Claude Code's memory of this repo, last updated May 19._
