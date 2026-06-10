# carmen-wiki

User manual for developers and QA engineers working on the **Carmen Software** hospitality supply chain platform. Content is organised into two books:

- **Carmen Inventory** — the inventory ERP slice (costing, GRN, physical count, requisitions, etc.). Pages document the data model, business rules, user flows by persona, and test scenarios at a level useful for building features and verifying them against the BRD and the live UI.
- **Carmen Platform** — the platform admin product (clusters, business units, users, RBAC, news, broadcasts, applications, report/print templates). Pages document the SPA's data model, UI screens, lifecycle, and permission model.

This repo is the **source of truth** for the Wiki.js content; the rendered site is what users actually read.

| Surface | URL |
| --- | --- |
| Source repo | <https://github.com/CarmenSoftware-organization/carmen-wiki> |
| Rendered wiki (dev) | <http://dev.blueledgers.com:3987/> — landing at `/en/home`, books at `/en/inventory` and `/en/platform` |

## Repository Layout

```
carmen-wiki/
├── en/                            # Canonical English content (rendered by Wiki.js)
│   ├── home.md                    # Locale landing (URL: /en/home) — two-card book picker
│   ├── inventory.md               # Book landing (sibling of inventory/)
│   ├── inventory/                 # Carmen Inventory book
│   │   ├── costing.md             # Module landing (sibling of costing/)
│   │   ├── costing/               # One folder per module
│   │   │   ├── 01-data-model.md
│   │   │   ├── 02-business-rules.md
│   │   │   ├── 03-user-flow.md
│   │   │   ├── 03-user-flow-<role>.md       # One per persona
│   │   │   ├── 04-test-scenarios.md
│   │   │   └── 04-test-scenarios-<role>.md
│   │   └── ...                    # good-receive-note, physical-count, etc.
│   ├── platform.md                # Book landing (sibling of platform/)
│   └── platform/                  # Carmen Platform book
│       ├── clusters.md            # Module landing
│       ├── clusters/              # Topical sub-pages (no numeric prefix)
│       │   ├── data-model.md
│       │   ├── ui-screens.md
│       │   ├── lifecycle.md
│       │   └── permissions.md
│       └── ...                    # business-units, users, rbac, profile, news,
│                                  # broadcasts, applications, report-templates,
│                                  # print-template-mapping, changelog
├── th/                            # Thai translation tracking (mirrors en/ shape)
│   ├── home.md                    # Locale landing (URL: /th/home)
│   ├── inventory.md, inventory/
│   └── platform.md,  platform/
├── assets/
│   └── screenshots/<book>/<module>/<slug>.png   # Wiki URL: /screenshots/<module>/<file>
├── scripts/                       # Tooling (sync_nav.py mirrors EN nav into TH)
├── .specs/                        # Hidden meta — templates, design/plan docs, frontmatter validator
├── docs/                          # Bundled superpowers skill content (not wiki pages)
├── CLAUDE.md                      # Project instructions for Claude Code
├── .gitignore
└── README.md                      # ← you are here
```

Top-level locale directories `en/` and `th/` are self-contained: each tree carries its own relative cross-references; Wiki.js handles the language toggle natively across them. The `.specs/` directory is hidden from Wiki.js — pages inside are not served as wiki content, and they hold the per-round design + implementation plans used to evolve the wiki itself.

## Sub-Page Convention

The two books share the same "module landing → sub-pages elaborate beneath" shape, but the sub-page set differs by book.

### Carmen Inventory — numeric prefix, persona-split

Inventory modules document a workflow with multiple personas, so sub-pages are numbered to fix a reading order and split per role:

| File | Content |
| --- | --- |
| `<module>.md` | Module landing (sibling of `<module>/`): overview, business context, key concepts, roles, related modules, reference sources, pages-in-this-module |
| `01-data-model.md` | Prisma entities, enums, relationships, rounding precision |
| `02-business-rules.md` | Validation, calculation, authorization, posting, and cross-module rules with stable rule IDs (`<MOD>_VAL_NNN`, `<MOD>_AUTH_NNN`, etc.). Includes **Section 5.1 Status Lifecycle — Live UI vs BRD Mapping** for transactional modules. |
| `03-user-flow.md` | Module-wide state-machine Mermaid + persona index |
| `03-user-flow-<role>.md` | Per-persona drill-down: Workflow Position Mermaid (`graph LR`, role highlighted) + Permission Matrix table + Section 2 entry/flow + Section 3 decision branches + Section 4 handoffs |
| `04-test-scenarios.md` | Cross-persona scope, E2E mapping |
| `04-test-scenarios-<role>.md` | Per-persona scenarios: happy path / permission / validation / edge cases, mapped to rule IDs and E2E specs |

### Carmen Platform — topical, no numeric prefix

Platform modules describe an admin SPA without per-persona workflows, so sub-pages are named topically. Full convention in [`.specs/platform-sub-page-template.md`](./.specs/platform-sub-page-template.md):

| File | Content |
| --- | --- |
| `<module>.md` | Module landing (sibling of `<module>/`): overview, key entities, roles, related modules, sub-page index |
| `data-model.md` | Universal. Prisma entities owned by this module, relationships, enums, divergences vs. SPA TS types |
| `ui-screens.md` | Universal. List + create/view/edit screens, layout shape, module-specific UI quirks |
| `lifecycle.md` | Module-specific. State transitions for modules with non-trivial lifecycles (e.g. users, report templates) |
| `permissions.md` | Module-specific. Role-gating matrix for modules whose surface is permission-sensitive (e.g. clusters) |

Single-page modules (e.g. `profile`, `changelog`) skip sub-pages entirely.

## Wiki.js Page Format

Every page must begin with Wiki.js YAML frontmatter. Example from a recent commit:

```yaml
---
title: Good Receive Note (GRN) — User Flow — Receiver
description: Receiver's flow within the good-receive-note module — dock receipt, GRN creation with lot/expiry capture, commit.
published: true
date: 2026-05-16T12:00:00.000Z
tags: good-receive-note, user-flow, receiver, inventory, carmen-software
editor: markdown
dateCreated: 2026-05-15T11:00:00.000Z
---
```

When editing an existing page, update `date` to the current timestamp but leave `dateCreated` untouched. The frontmatter validator at `.specs/verify_frontmatter.py` sanity-checks these fields.

## Contributing Content

1. Edit Markdown files locally in your IDE (no build pipeline, no dependencies — just text editing).
2. Commit and push to `main`.
3. Wiki.js's git storage target on the dev server pulls `main` every 5 minutes. New pages appear automatically.
4. **Modified pages**: Wiki.js git sync only auto-detects *new and deleted* files. If you change content in an existing page and want it to refresh on the dev site, an admin needs to click **Storage → Git → Import Everything** in the Wiki.js admin (`/a/storage`) after the pull.

Conventions to follow when editing (full list in [`CLAUDE.md`](./CLAUDE.md)):

- Numbered section hierarchy: `## 1. Title` → `### 1.1 Sub`. Stable cross-references.
- Comparison tables for design trade-offs over prose bullet lists.
- Pseudo-code blocks for algorithms (language-agnostic).
- Currency in examples: Thai Baht (`฿`).
- Cite Test_case as plain-text relative path with backticks — never markdown links — since Test_case lives outside this repo.
- **Internal links use absolute URLs**, not pipe wikilinks. Write `[Display](/en/inventory/costing/01-data-model)` rather than `[[en/inventory/costing/01-data-model|Display]]` — pipe wikilinks do not render in this Wiki.js setup.
- **Screenshots** live on disk under `assets/screenshots/<book>/<module>/<slug>.png` and are embedded as `![alt](/screenshots/<module>/<file>.png)` immediately after the **At a Glance** callout. Mirror the same embed in EN and TH.

## Tooling

[`scripts/sync_nav.py`](./scripts/) mirrors the Wiki.js EN navigation tree into the TH locale via the admin GraphQL API. Run it after adding or moving pages so the language toggle stays consistent. See [`scripts/README.md`](./scripts/README.md) for setup and usage. The frontmatter validator at [`.specs/verify_frontmatter.py`](./.specs/verify_frontmatter.py) sanity-checks `date`, `dateCreated`, and the rest of the header.

## Reference Sources

Content is synthesised from these sibling repos under the Carmen Software organisation:

| Path (sibling to this repo) | Use for |
| --- | --- |
| `../carmen/docs/` | Primary concept and design references for every Inventory module |
| `../carmen-inventory-frontend/` | Next.js inventory UI — source of truth for Inventory screen behaviour |
| `../carmen-platform/` | React/TypeScript SPA — source of truth for the Platform book |
| `../carmen-turborepo-backend-v2/` | Turborepo monorepo, REST API surface. Platform Prisma schema lives at `packages/prisma-shared-schema-platform/`. |
| `../micro-report/`, `../micro-cronjobs/` | Go microservices for reporting and scheduled jobs |
| `../carmen-turborepo-backend-bruno/` | Bruno API collections, exact request/response shapes |
| `../carmen-inventory-frontend-e2e/` | Playwright suite — executable spec for Inventory behaviour |
| `~/GitHub/Test_case/` | Screen-level and process-level test artefacts cited by discrepancy callouts |

When in doubt about what the system actually does: implementation (frontend/backend) and E2E tests beat `../carmen/docs/`; `../carmen/docs/` beats memory or speculation.

## License

Internal documentation for Carmen Software. Not currently licensed for external use.
