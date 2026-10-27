---
title: "Workflow stage_actions lives only in gateway serializers, not micro-business"
author: Thammanoon
date: 2026-10-27
branch: docs/resync-inventory-2026-10-27
id: l-08e73517
scope: repo
status: active
src: agent
touches:
  - en/inventory/dashboard.md
  - en/inventory/dashboard/widget-workspace.md
  - en/inventory/general-ledger.md
  - en/inventory/general-ledger/gl-posting.md
  - en/inventory/good-receive-note.md
  - en/inventory/good-receive-note/02-business-rules.md
  - en/inventory/good-receive-note/03-user-flow-audit-config.md
  - en/inventory/good-receive-note/03-user-flow-finance.md
  - en/inventory/good-receive-note/03-user-flow-purchaser.md
  - en/inventory/good-receive-note/03-user-flow-receiver.md
---

## Watch out
- `stage_actions: {approve, reject, sendback}` is added to PR/PO/SR detail responses in carmen-turborepo-backend `apps/backend-gateway/src/common/dto/*/<doc>.serializer.ts` (BE aeafc119d). micro-business stores the flags as `available_actions.<verb>.is_active` on the workflow stage and enforces them in `workflow-orchestrator.service.ts` (`checkStageActionAllowed`, 422 WORKFLOW_STAGE_ACTION_DISABLED). If you grep only micro-business you'll wrongly conclude `stage_actions` doesn't exist. During the 2026-10-27 re-sync one agent made exactly that call and contradicted the PR/PO pages.
- Wiki pages: en/inventory/system-config/workflow.md, purchase-request/02-business-rules.md, purchase-order/02-business-rules.md.
