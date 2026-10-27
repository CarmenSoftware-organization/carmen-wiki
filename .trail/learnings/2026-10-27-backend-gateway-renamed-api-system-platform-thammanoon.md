---
title: Backend gateway renamed api-system/platform to api-system/backstage; wiki citations must follow
author: Thammanoon
date: 2026-10-27
branch: docs/resync-platform-2026-10-27
cost: { minutes: 15, tokens: 66528 }
id: l-1bda56d4
scope: repo
status: active
src: agent
touches:
  - en/platform/ai-providers.md
  - en/platform/ai-providers/data-model.md
  - en/platform/ai-providers/ui-screens.md
  - en/platform/dashboard-templates.md
  - en/platform/dashboard-templates/data-model.md
  - en/platform/dashboard-templates/lifecycle.md
  - en/platform/dashboard-templates/ui-screens.md
  - en/platform/tenant-seed.md
  - en/platform/tenant-seed/lifecycle.md
  - en/platform/tenant-seed/ui-screens.md
---

## Decided
- Re-sync 2026-10-27 baselines are the 2026-09-22 source HEADs (see .specs/resync-2026-10-27-progress.md).
- Backstage "Config" is the old Platform Config renamed (carmen-backstage 56d90a5d, 318949a3): route /backstage/configs, permission backstage_config.read. Document it on en/platform/platform-config.md; don't create a new module page.

## Watch out
- carmen-turborepo-backend moved apps/backend-gateway/src/platform/** to src/backstage/** (files platform_* became backstage_*) and every @Controller('api-system/platform/...') to 'api-system/backstage/...'. Some new controllers have no backstage/ segment (api-system/ai-providers, api-system/dashboard-templates, api-system/clusters). Any wiki page citing the old paths or routes is stale; re-check the line numbers at the new location.
