# carmen-wiki

User manual for developers and QA engineers working on the **Carmen Inventory ERP** — the inventory slice of the Carmen Software hospitality supply chain platform. Pages document the data model, business rules, user flows by persona, and test scenarios at a level useful for building inventory features and verifying them against the BRD and the live UI.

This repo is the **source of truth** for the Wiki.js content; the rendered site is what users actually read.

| Surface | URL |
| --- | --- |
| Source repo | <https://github.com/CarmenSoftware-organization/carmen-wiki> |
| Rendered wiki (dev) | <http://dev.blueledgers.com:3987/> — landing at `/en/home` |

## Repository Layout

```
carmen-wiki/
├── en/                    # Canonical English content (rendered by Wiki.js)
│   ├── home.md            # Locale landing (URL: /en/home)
│   ├── inventory.md       # Book landing (sibling of inventory/)
│   ├── inventory/         # One folder per book (inventory, platform, etc.)
│   │   ├── costing.md     # Module landing (sibling of costing/)
│   │   ├── costing/       # One folder per module
│   │   │   ├── 01-data-model.md
│   │   │   ├── 02-business-rules.md
│   │   │   ├── 03-user-flow.md
│   │   │   ├── 03-user-flow-<role>.md   # One per persona
│   │   │   ├── 04-test-scenarios.md
│   │   │   └── 04-test-scenarios-<role>.md
│   │   └── ...
│   └── ...
├── th/                    # Thai translation tracking (Wiki.js language toggle)
│   ├── home.md            # Locale landing (URL: /th/home)
├── docs/                  # Meta documentation (specs, plans) — not wiki content
├── .specs/                # Hidden meta (templates, frontmatter validator)
├── CLAUDE.md              # Project instructions for Claude Code
├── .gitignore
└── README.md              # ← you are here
```

Top-level locale directories `en/` and `th/` are self-contained: each tree carries its own relative cross-references; Wiki.js handles the language toggle natively across them. The `.specs/` directory is hidden from Wiki.js — pages inside are not served as wiki content. The `docs/` directory holds the brainstorming spec + implementation plan used to evolve the wiki itself.

## Sub-Page Convention

Every module folder follows the same shape so readers know exactly where to find each kind of content:

| File | Content |
| --- | --- |
| `<module>.md` | Module landing (sibling of `<module>/`): overview, business context, key concepts, roles, related modules, reference sources, pages-in-this-module |
| `01-data-model.md` | Prisma entities, enums, relationships, rounding precision |
| `02-business-rules.md` | Validation, calculation, authorization, posting, and cross-module rules with stable rule IDs (`<MOD>_VAL_NNN`, `<MOD>_AUTH_NNN`, etc.). Includes **Section 5.1 Status Lifecycle — Live UI vs BRD Mapping** for transactional modules. |
| `03-user-flow.md` | Module-wide state-machine Mermaid + persona index |
| `03-user-flow-<role>.md` | Per-persona drill-down: Workflow Position Mermaid (`graph LR`, role highlighted) + Permission Matrix table + Section 2 entry/flow + Section 3 decision branches + Section 4 handoffs |
| `04-test-scenarios.md` | Cross-persona scope, E2E mapping |
| `04-test-scenarios-<role>.md` | Per-persona scenarios: happy path / permission / validation / edge cases, mapped to rule IDs and E2E specs |

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

## Reference Sources

Content is synthesised from these sibling repos under the Carmen Software organisation:

| Path (sibling to this repo) | Use for |
| --- | --- |
| `../carmen/docs/` | Primary concept and design references for every module |
| `../carmen-inventory-frontend/` | Next.js inventory UI — source of truth for screen behaviour |
| `../carmen-turborepo-backend-v2/` | Turborepo monorepo, REST API surface |
| `../micro-report/`, `../micro-cronjobs/` | Go microservices for reporting and scheduled jobs |
| `../carmen-turborepo-backend-bruno/` | Bruno API collections, exact request/response shapes |
| `../carmen-inventory-frontend-e2e/` | Playwright suite — executable spec for behaviour |
| `~/GitHub/Test_case/` | Screen-level and process-level test artefacts cited by discrepancy callouts |

When in doubt about what the system actually does: implementation (frontend/backend) and E2E tests beat `../carmen/docs/`; `../carmen/docs/` beats memory or speculation.

## License

Internal documentation for Carmen Software. Not currently licensed for external use.
