# Navigation Module Groups — Design

**Date:** 2026-05-19
**Status:** Approved (awaiting spec review)
**Scope:** `scripts/nav-overrides.yaml`, `scripts/sync_nav.py`, `scripts/test_sync_nav.py`, `en/inventory/home.md`, `th/inventory/home.md`

## Goal

Group the modules inside each book's Wiki.js sidebar into named categories instead of one flat list. Today the Inventory book renders 18 modules in a single sequence; readers must scroll past unrelated areas to find the page they want. Categories mirror the mental model already established by `carmen-inventory-frontend-react` (procurement / inventory ops / product / etc).

## Why

- Inventory book has 18 modules — too many for a flat sidebar to be scannable
- The frontend already groups these concepts; the wiki should match the developers' mental model so navigation is predictable
- Adding Platform book (6 modules) makes the asymmetry worse if we group one and not the other

## Constraints

- Wiki.js static navigation is a flat list of items with `kind ∈ {header, link, divider}`. There is no real hierarchy and no collapse/expand. Grouping is **visual**, achieved by inserting `header` items between groups of `link` items.
- `--mode=build` (declarative rebuild from YAML) is the source of truth for navigation. `--mode=mirror` (derive TH from live EN tree) must keep working but is secondary.
- Existing book divider + book header pattern stays as-is.
- EN and TH labels for groups must both come from YAML (`label_en`, `label_th`) — no fallback to `home.md` heading parsing for group labels, because group labels are a new concept that home.md does not currently expose.

## Decisions

| Decision | Choice | Why |
|---|---|---|
| Schema | Replace `book.modules` with `book.groups`, each group containing `modules` | Single canonical layout; no dual-path branching in code |
| Backward compat for old `modules:` | None — both books migrate at once | Only two books exist today; transitional support adds complexity for no benefit |
| Empty group label support | Not supported in this iteration | All groups in this rollout have real names; "ungrouped module" is YAGNI |
| Wiki.js render | `header` items as group titles, placed between module `link`s within the book | Wiki.js's only mechanism for visual grouping in a flat list |
| TH label source | `groups[].label_th` in YAML directly | `home.md` headings are already used for module groups via mirror mode; not appropriate for nav-only group labels |
| `home.md` TOC | Updated to mirror sidebar groups (numbered `## N. <Group>` per group, table per group) | Keeps page TOC consistent with sidebar; mirror mode still works |

## Inventory book grouping

18 modules organized into 6 groups, derived from `carmen-inventory-frontend-react/constant/module-list.ts`:

| # | Group (`label_en` / `label_th`) | Modules |
|---|---|---|
| 1 | Overview / ภาพรวม | dashboard |
| 2 | Procurement / การจัดซื้อ | purchase-request, purchase-order, good-receive-note, vendor-pricelist |
| 3 | Inventory Operations / การดำเนินงานคลัง | inventory, inventory-adjustment, physical-count, spot-check, store-requisition |
| 4 | Product & Recipe / สินค้าและสูตร | product, master-data, recipe |
| 5 | Costing & Reporting / ต้นทุนและรายงาน | costing, reporting-audit |
| 6 | Administration / การดูแลระบบ | access-control, system-config, templates |

## Platform book grouping

6 modules organized into 3 groups (conceptual — the live `carmen-platform` Sidebar is flat, so we choose boundaries by concept):

| # | Group (`label_en` / `label_th`) | Modules |
|---|---|---|
| 1 | Tenancy / Tenancy | clusters, business-units |
| 2 | Identity & Access / Identity & Access | users, auth-roles, profile |
| 3 | Reporting / Reporting | report-templates |

(TH labels kept identical to EN for the Platform book initially; can be localized later without a schema change.)

## YAML schema

```yaml
books:
  <book-slug>:
    label_en: "<Book label EN>"
    label_th: "<Book label TH>"
    home_slug: home
    groups:
      - label_en: "<Group label EN>"
        label_th: "<Group label TH>"
        modules:
          - slug: <module-slug>
            label_en: "<Module label EN>"
            label_th: "<Module label TH>"
          - ...
```

The legacy `book.modules:` key is removed.

## Code change

`scripts/sync_nav.py:build_tree_from_config()` (currently lines 645–677) changes from:

```python
for module in book.get("modules") or []:
    items.append(_new_link(module[label_key], f"/{locale}/{book_slug}/{module['slug']}/{home_slug}"))
```

to:

```python
for group in book.get("groups") or []:
    items.append(_new_header(group[label_key]))
    for module in group.get("modules") or []:
        items.append(_new_link(
            module[label_key],
            f"/{locale}/{book_slug}/{module['slug']}/{home_slug}",
        ))
```

Everything else in the function (book header, Home link, divider between books) stays the same.

### Rendered sequence for one book

```
[header]   <Book label>
[link]     Home               → /{locale}/{book}/home
[header]   <Group 1 label>
[link]     <Module 1.1 label> → /{locale}/{book}/<module>/home
[link]     <Module 1.2 label>
[header]   <Group 2 label>
[link]     <Module 2.1 label>
...
```

Between books, a single `_new_divider()` is emitted (unchanged behavior).

## `home.md` TOC update

Both `en/inventory/home.md` and `th/inventory/home.md` currently have a single `## 1. Modules` section listing all 18 modules in one table. Replace with one numbered section per group, each containing a table of just that group's modules. The `## N. <Group>` headings give mirror mode (`parse_home_headings`) the data it would need if we ever fell back to home.md-based labels.

The Platform book's `home.md` files get the same treatment.

## Tests

Add to `scripts/test_sync_nav.py`:

| Test | Asserts |
|---|---|
| `test_build_tree_emits_group_headers_in_order` | For a book with 2 groups, items are: book header, Home, group1 header, group1 links..., group2 header, group2 links... |
| `test_build_tree_uses_th_label_for_th_locale` | When `locale="th"`, group labels and module labels come from `label_th`, not `label_en` |
| `test_build_tree_divider_between_books` | A divider sits between the last item of book 1 and the book 2 header |
| `test_build_tree_empty_groups_list` | A book with `groups: []` emits only its book header + Home link, no crash |
| `test_build_tree_dry_run_preview` | `--mode=build --dry-run` prints expected items per locale to stderr |

Tests for `--mode=mirror` are not changed: mirror mode reads the EN tree from Wiki.js verbatim and derives TH per item; it does not know about the YAML `groups:` block.

## Rollout

1. `scripts/nav-overrides.yaml` — migrate both books from `modules:` to `groups:` with the labels above
2. `scripts/sync_nav.py` — update `build_tree_from_config` per the diff above
3. `scripts/test_sync_nav.py` — add new tests, update any existing tests that referenced the old flat `modules:` shape
4. `en/inventory/home.md` and `th/inventory/home.md` — rewrite TOC into group-per-section structure
5. `en/platform/home.md` and `th/platform/home.md` — same TOC update
6. `python scripts/sync_nav.py --mode=build --dry-run` — verify printed tree matches expected sequence
7. `python scripts/sync_nav.py --mode=build` — push to dev Wiki.js
8. Visual check at `http://dev.blueledgers.com:3987/` — verify EN and TH sidebars for both books

## Edge cases

| Case | Behavior |
|---|---|
| Group has 0 modules | Group header still emitted (degenerate but valid); flag in spec review, not in code |
| Wiki.js shows headers indistinguishably from book headers | Acceptable — book header is followed by `Home` link; group headers are followed by module links. The pattern is regular enough to be readable. |
| User wants to collapse a group | Not supported by Wiki.js static nav. Out of scope. |
| Module slug collision across groups in same book | Won't happen — module slugs are filesystem dirs; the filesystem enforces uniqueness |

## Non-goals

- Collapsible/expandable groups
- Per-group icons
- Permission-based group visibility (Wiki.js `visibilityGroups` already exists at item level; group-level visibility is YAGNI)
- Reordering modules across groups via UI — YAML stays the source of truth

## Risks

- **Wiki.js header rendering may not visually separate groups well enough.** Mitigation: visual check step 8; if groups are not visually distinct, add a divider before each group header in a follow-up.
- **TH labels for Platform groups are placeholders (= EN).** Mitigation: documented; localization is a YAML edit with no code change.
