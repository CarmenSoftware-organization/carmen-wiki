# Design: TH Locale Navigation Sync

**Date:** 2026-05-18
**Status:** Draft — awaiting user review
**Scope:** Add Wiki.js sidebar navigation for the `th` locale by syncing from `en` via a scripted GraphQL workflow

## 1. Problem

Wiki.js renders `carmen-wiki` content under two locales — `/en/*` and `/th/*` — with identical folder structure. The `en` locale has a hand-curated **static** navigation tree configured in Wiki.js admin (visible in `nav-updated.png`: groups for Procure-to-Pay, Inventory Control, Costing & Recipe, Master Configuration, Reporting & Audit). The `th` locale has **no navigation tree at all** (`th-home.png` shows no sidebar), so Thai readers cannot navigate between modules from the wiki chrome.

Recreating the navigation in admin by hand is feasible (Option A), but the EN nav has been iterated multiple times (see commits and `nav-*.png` artifacts) and is expected to keep evolving. Without automation, the TH nav will drift from EN every time EN is edited, and the work must be redone manually.

## 2. Goal

Provide a repeatable, scripted way to mirror the EN navigation tree into the TH locale:

- Same structure (headers, links, dividers, ordering) as EN
- Paths rewritten `/en/...` → `/th/...`
- Labels translated to Thai using three resolution sources (frontmatter / `home.md` headings / manual overrides)
- Script committed to the repo; can be re-run whenever EN nav changes

The script is the only artifact this work produces. Wiki.js continues to store the navigation in its DB; the script reads and writes it via the Wiki.js GraphQL API.

## 3. Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Wiki.js (dev.blueledgers.com:3987)                     │
│  ┌──────────────────────┐    ┌──────────────────────┐   │
│  │  Navigation (EN)     │    │  Navigation (TH)     │   │
│  │  source of truth     │    │  written by script   │   │
│  └──────────┬───────────┘    └──────────▲───────────┘   │
│             │ query                       │ mutation    │
└─────────────┼─────────────────────────────┼─────────────┘
              │      GraphQL API            │
              │                             │
        ┌─────▼─────────────────────────────┴───────┐
        │  scripts/sync-nav.py  (run locally)       │
        │  1. Fetch full nav tree                   │
        │  2. Clone EN items, rewrite paths         │
        │  3. Resolve TH labels (3 sources)         │
        │  4. Push full tree (EN unchanged + new TH)│
        └────────────────┬──────────────────────────┘
                         │ reads
        ┌────────────────▼──────────────────────────┐
        │  th/**/*.md frontmatter `title:`          │
        │  th/home.md ## section headings           │
        │  scripts/nav-overrides.yaml               │
        └───────────────────────────────────────────┘
```

EN is the source of truth — the script never writes EN, only reads it and uses it as the template for TH.

## 4. Wiki.js GraphQL API

Wiki.js 2.x exposes navigation under the `navigation` namespace.

### 4.1 Read (query)

```graphql
query {
  navigation {
    tree {
      locale
      items {
        id
        kind            # header | link | divider
        label
        icon
        targetType      # home | page | url
        target          # e.g. "/en/purchase-request/index"
        visibilityMode
        visibilityGroups
      }
    }
    config { mode }     # script asserts STATIC before pushing
  }
}
```

### 4.2 Write (mutation)

```graphql
mutation($tree: [NavigationTreeInput]!) {
  navigation {
    updateTree(tree: $tree) {
      responseResult { succeeded errorCode message }
    }
  }
}
```

**Critical constraint:** `updateTree` replaces the **entire** tree for **all** locales. The script must always send the EN tree back unchanged alongside the new TH tree, or EN nav will be wiped.

### 4.3 Authentication

Both query and mutation are sent to `${WIKI_API_URL}` (the `/graphql` endpoint) with header `Authorization: Bearer <WIKI_API_TOKEN>`. The token is obtained from Wiki.js admin → API Access and must have scopes that cover `navigation:read` and `navigation:manage` (Wiki.js 2.x permission keys; verify exact names against the running version at run time).

## 5. Sync algorithm

```
1. FETCH      query navigation.tree + navigation.config.mode
              assert mode == STATIC, abort otherwise
              extract en_items, th_items_old
2. CLONE      deep-copy en_items → th_new_items
3. TRANSFORM  for each item in th_new_items:
                - id        = uuid4()  (RFC 4122 v4, fresh per run)
                - target    = item.target.replace("/en/", "/th/")
                              (only when kind=link AND targetType=page)
                - label     = resolve_label(item)
                - icon, visibilityMode, visibilityGroups: preserved
4. DIFF       compute label/target delta vs th_items_old
              print per-item diff and counts by source
5. DRY-RUN?   if --dry-run: exit 0 without mutation
6. PUSH       mutation updateTree with tree = [
                {locale:"en", items: en_items_unchanged},
                {locale:"th", items: th_new_items},
              ]
              abort if responseResult.succeeded != true
7. REPORT     summary line: N items / X frontmatter / Y home.md / Z override / W fallback
```

### 5.1 `resolve_label(item)`

```
if item.kind == "divider":
    return None

if item.kind == "link" and item.targetType == "page":
    # Wiki.js page targets may be either a folder (resolves to index)
    # or a file path. Try both shapes before giving up.
    rel = item.target.lstrip("/")              # e.g. "th/purchase-request"
    candidates = [
        repo_root / (rel + ".md"),             # th/purchase-request.md (file)
        repo_root / rel / "index.md",          # th/purchase-request/index.md (folder)
    ]
    th_file = next((p for p in candidates if p.exists()), None)
    if th_file:
        return frontmatter(th_file).title     # source: frontmatter
    log WARN "no TH file for {target}, falling back to EN label"
    return item.label                          # source: fallback

if item.kind == "header":
    th_label = home_md_headings.get(item.label)
    if th_label: return th_label               # source: home.md
    if item.label in overrides["headers"]:
        return overrides["headers"][item.label]  # source: override
    return item.label                          # source: fallback

if item.kind == "link" and item.targetType == "url":
    if item.target in overrides["links"]:
        return overrides["links"][item.target]   # source: override
    return item.label                          # source: fallback (URL kept verbatim)
```

### 5.2 `home.md` heading parser

Parse `th/home.md` for `## N. <text>` headings; build a map keyed by the **EN** heading text from `en/home.md` to the **TH** heading text at the same index. This lets the script translate header labels like `"Procure-to-Pay"` → `"จัดซื้อจัดจ้าง (Procure-to-Pay)"` without a manual map.

Index pairing example:
- `en/home.md` `## 3. Procure-to-Pay` ↔ `th/home.md` `## 3. Procure-to-Pay` → header label translation
- `en/home.md` `## 4. Inventory Control` ↔ `th/home.md` `## 4. การควบคุมคลังสินค้า` → translation

If the section count or order differs between `en/home.md` and `th/home.md`, the script logs a warning and skips home.md as a label source for the mismatching index (falls back to override or EN label).

## 6. File layout in the repo

```
carmen-wiki/
├── scripts/
│   ├── sync-nav.py             # main script
│   ├── nav-overrides.yaml      # manual label overrides (committed)
│   ├── requirements.txt        # gql, pyyaml, python-frontmatter
│   └── README.md               # usage, env setup, dry-run, troubleshooting
├── .env.example                # WIKI_API_URL=, WIKI_API_TOKEN=  (committed)
├── .env                        # actual values (gitignored, already in .gitignore)
└── .gitignore                  # ensure scripts/.env, .env both excluded
```

### 6.1 `nav-overrides.yaml` shape

```yaml
# Manual TH label overrides. Used only when frontmatter/home.md cannot resolve.
headers:
  # key = EN header text (exact match from EN nav)
  # value = TH text to use
  # Example only — populated as needed:
  "Procure-to-Pay": "จัดซื้อจัดจ้าง (Procure-to-Pay)"

links:
  # key = target URL (for kind=link, targetType=url)
  # value = TH label
  # Example:
  # "https://github.com/CarmenSoftware-organization/carmen-wiki": "GitHub repository"
```

### 6.2 `.env.example`

```
WIKI_API_URL=http://dev.blueledgers.com:3987/graphql
WIKI_API_TOKEN=<obtain from Wiki.js admin → API Access>
```

## 7. CLI surface

```
$ python scripts/sync-nav.py [--dry-run] [--verbose]

--dry-run    fetch + transform + print diff; do not push mutation
--verbose    log per-item label resolution source
```

### 7.1 Sample dry-run output

```
[FETCH]  api=http://dev.blueledgers.com:3987/graphql
         mode=STATIC  locales: en (42 items), th (0 items)
[XFORM]  resolving labels...
  ✓ header  "Procure-to-Pay"     →  "จัดซื้อจัดจ้าง (Procure-to-Pay)"   [home.md]
  ✓ link    /en/purchase-request →  /th/purchase-request  "คำขอซื้อ"     [frontmatter]
  ⚠ link    /en/foo              →  /th/foo               (no TH file; "Foo") [fallback]
  ...
[DIFF]   th tree:  0 → 42 items  (all new)
[DRY-RUN] no mutation sent.

Summary: 42 items · 29 frontmatter · 6 home.md · 4 override · 3 fallback
```

## 8. Idempotency

- `resolve_label` is pure given (item, frontmatter state, home.md state, overrides) — repeated runs without underlying changes yield the same labels and targets.
- Each run generates fresh UUIDv4 IDs for TH items. The TH tree is therefore replaced in full on every push (not merged). This is acceptable: Wiki.js does not persist per-user expand/collapse state, so users experience no regression.
- EN tree is read once and written back **verbatim** (same item IDs, same labels, same order). Re-running the script does not perturb the EN nav.

## 9. Edge cases

| Case | Handling |
|------|----------|
| TH page does not exist (translation not done yet) | Log WARN, fallback to EN label. Target path still rewritten to `/th/...` — nav entry will be a broken link until the TH page is created (consistent with the existing `nav-grn-page.png` "page does not exist" state for EN). |
| EN nav header text changes | Override key must be updated. Otherwise label falls back to the new EN text. |
| `navigation.config.mode` is not STATIC | Abort before mutation, print actionable error: "Set Navigation Mode to Static in Wiki.js admin before running this script." |
| API token expired / unauthorized | Abort before mutation, surface the GraphQL error message. |
| `en/home.md` and `th/home.md` section structure diverge | Log WARN per mismatching index; that index's headers fall through to override / EN-label fallback. |
| External URL link (kind=link, targetType=url) in EN | Target preserved verbatim (not rewritten); label translated via `overrides["links"]` if present. |
| Divider items | No transformation needed; copied as-is with a fresh UUID. |
| Items with `icon`, `visibilityMode`, `visibilityGroups` set | All preserved on the cloned TH item. |

## 10. Out of scope

- **CI / pre-commit integration** — script is run manually on demand.
- **Auto-detect EN nav changes** (polling, Wiki.js webhook) — out of scope this round.
- **Locales beyond `en`/`th`** — script is hard-coded for this pair. Adding a third locale would require generalizing the locale arg.
- **Editing EN nav from the script** — script is read-only for EN.
- **Bidirectional sync** (TH → EN) — not supported; would invite drift.
- **Translation of TH page content** — script only sets nav labels, never modifies wiki page content.
- **GUI / admin-side automation** — script speaks only the GraphQL API; admin UI is not driven.

## 11. Implementation notes

1. Python 3.11+. Dependencies: `gql` (with `requests` transport), `python-frontmatter`, `pyyaml`. Pinned in `scripts/requirements.txt`.
2. The script imports nothing from the wiki content — it only **reads** TH markdown files for frontmatter. No file writes outside of stdout.
3. `nav-overrides.yaml` is committed and starts empty (only example comments). Entries are added as warnings surface during dry-runs.
4. `scripts/README.md` documents: prerequisites, getting an API token from Wiki.js admin, env setup, dry-run command, push command, troubleshooting (mode not STATIC, auth failures, label fallbacks).
5. The script does not need to be runnable in CI; running locally against the dev Wiki.js is sufficient for this round.
6. Wiki.js navigation cannot be exported as a file — the `updateTree` mutation is the only way to write nav. The script is the artifact in git that approximates "nav-as-code" without persisting the tree itself in the repo.

## 12. Verification (after implementation)

After running `python scripts/sync-nav.py` against dev Wiki.js:

1. Open `http://dev.blueledgers.com:3987/th/home` in a browser → confirm the left sidebar now appears with the same structure as `/en/home` and Thai labels.
2. Click each top-level group header → confirm it expands and reveals child links.
3. Click 3–5 representative module links (e.g. `/th/purchase-request`, `/th/good-receive-note`, `/th/inventory`) → confirm each resolves to the existing TH page and renders.
4. Switch the language toggle EN ↔ TH from the same page → confirm the sidebar swaps locale without breaking.
5. Compare the EN sidebar before and after running the script → confirm EN nav is byte-identical (no perturbation).

## 13. Open questions

None at design time.
