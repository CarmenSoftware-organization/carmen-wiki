---
title: Good Receive Note (GRN) — Test Scenarios — Audit & Config
description: Why no dedicated GRN configuration console or lot-recall-tool test scenarios exist for good-receive-note in current source, and what is confirmed instead.
published: true
date: 2026-07-15T00:00:00.000Z
dateCreated: 2026-05-15T11:00:00.000Z
tags: good-receive-note, test-scenarios, audit-config, inventory, carmen-software
editor: markdown
---

# Good Receive Note (GRN) — Test Scenarios — Audit & Config

> **At a Glance**
> **Status:** Correction page — no dedicated GRN configuration console, RBAC panel, or lot-recall tool was confirmed for good-receive-note in current source.

> ⚠️ **Major correction this pass (2026-07-15).** The previous version of this page listed roughly 29 scenarios covering a Sysadmin "GRN configuration console" (lot-number-format editor, RBAC role/approval-threshold panel, tax/currency/reason-code maintenance, PO/Inventory/Finance/Vendor integration cutover) and an Auditor lot-recall trace tool with Controller/DPO sensitive-field-export approval. No matching route, frontend component, or backend endpoint was found in `carmen-inventory-frontend-react` or `carmen-turborepo-backend-v2`, and no such route appears in `.specs/resync-2026-07-15-routes-inventory.txt`.

| Previously-claimed scenario group | Finding |
| --- | --- |
| AUD-HP-01..04 (Auditor activity-log query, GRN drill-in, lot-recall trace, sensitive-field export with secondary approval) | No dedicated audit-module route or export-approval workflow found. The underlying data (`workflow_history` JSON, the `inventory_transaction_id` linkage) is real; no purpose-built screen was found reading it. |
| AUD-HP-05..08 (Sysadmin lot-format change, RBAC adjustment, tax/reason-code maintenance, integration cutover) | Lot-number generation is real but hardcoded (`RC{YY}{MM}{4-digit sequence}` in `inventory-transaction.service.ts`), not configurable through any panel found. Tax/currency/running-code configuration is real but lives in the generic [system-config](/en/inventory/system-config) / [master-data](/en/inventory/master-data) modules, not a GRN-specific console. No RBAC-threshold or integration-endpoint panel found. |
| AUD-PERM-01..07, AUD-VAL-01..08, AUD-EDGE-01..06 | All built on the same unconfirmed configuration-console / lot-recall-tool foundation; not reconstructed. |
| `GRN_POST_010` post-commit-void co-authorisation (Inventory Manager + Finance) referenced throughout | **Not implemented.** The `/void` endpoint has no `doc_status` precondition beyond "not already voided" and no co-authorisation gate — see [02-business-rules.md](./02-business-rules.md) `GRN_POST_010` and [03-user-flow-audit-config.md](./03-user-flow-audit-config.md). |

## What to test instead

- Lot-number generation format and manual override, as part of the Receiver's save flow — see [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md).
- Generic RBAC / permission-denial coverage — the `requestor@blueledgers.com` vs `purchase@blueledgers.com` fixture pattern used throughout `501-grn.spec.ts`'s permission-denial describe blocks.
- Tax code, currency, and running-code (GRN-number sequencing) configuration — see [system-config](/en/inventory/system-config) and [master-data](/en/inventory/master-data) for their own, real test-scenario pages.

## References

- Parent overview: [04-test-scenarios.md](./04-test-scenarios.md) — corrected cross-persona scenario table.
- Sibling: [03-user-flow-audit-config.md](./03-user-flow-audit-config.md) — the fuller correction and the searches run.
- Sibling: [04-test-scenarios-receiver.md](./04-test-scenarios-receiver.md) — lot-number entry as part of the Receiver's save flow.
- E2E spec: `../carmen-inventory-frontend-e2e/tests/501-grn.spec.ts` — permission-denial pattern (`requestor@blueledgers.com`) is the closest real coverage to the "Auditor read-only" boundary; no lot-recall or configuration-console describe block exists in this file.
