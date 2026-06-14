# Sub-Page Templates

Standalone copies of the four canonical sub-page templates defined in `.specs/2026-05-15-sub-page-templates-design.md` Section 3. These files exist for convenience — they are copy-sources for per-module sub-page implementation.

The spec is canonical. If the spec changes, these files must be regenerated.

## Templates

| File | Purpose |
| ---- | ------- |
| `01-data-model.md` | Entities, fields, relationships, enums. Sourced from Prisma schema. |
| `02-business-rules.md` | Validation, calculation, authorization, posting, cross-module rules. |
| `03-user-flow.md` | Document lifecycle + flows organized by persona. |
| `04-test-scenarios.md` | Test cases organized by persona + E2E test mapping. |

## Usage

When implementing sub-pages for a module `<m>`:

1. Copy each template into the module folder under the appropriate locale (`en/` for English, `th/` for Thai — translate after copying):
   ```bash
   cp .specs/templates/01-data-model.md en/<m>/01-data-model.md
   cp .specs/templates/02-business-rules.md en/<m>/02-business-rules.md
   cp .specs/templates/03-user-flow.md en/<m>/03-user-flow.md
   cp .specs/templates/04-test-scenarios.md en/<m>/04-test-scenarios.md

   # When a Thai translation is also being authored:
   cp .specs/templates/01-data-model.md th/<m>/01-data-model.md  # then translate
   cp .specs/templates/02-business-rules.md th/<m>/02-business-rules.md  # then translate
   cp .specs/templates/03-user-flow.md th/<m>/03-user-flow.md  # then translate
   cp .specs/templates/04-test-scenarios.md th/<m>/04-test-scenarios.md  # then translate
   ```

2. Substitute placeholders in each copied file:
   - `<Module>` → human-readable module name (matches `index.md` `title:`)
   - `<module-slug>` → folder name (e.g. `inventory`, `good-receive-note`)
   - `<ISO 8601 timestamp>` (both `date` and `dateCreated`) → current ISO timestamp
   - Page-type-specific placeholders: `<EntityName>`, `<Persona>`, `<Rule ID>`, etc.

3. Read the relevant source for the page type:
   - **Data Model:** Read both Prisma schemas first, then cross-check `../carmen/docs/<source>/`.
   - **Business Rules:** Read `../carmen/docs/<source>/` PRD and business-requirements files.
   - **User Flow:** Read `../carmen/docs/<source>/` flow/UX docs, supplement with `../carmen-inventory-frontend-react/routes/`.
   - **Test Scenarios:** Read `../carmen-inventory-frontend-e2e/tests/` for executable spec, supplement with `../carmen/docs/<source>/testing.md`.

4. Fill in the content section by section. Keep the section numbering exactly as the template.

5. Run the frontmatter verifier:
   ```bash
   python3 .specs/verify_frontmatter.py en/<m>/01-data-model.md
   ```
   Each filled-in sub-page should print `OK: ... — title='<Module> — ...'`.

6. Update the module's `index.md` Section 7 to list the new sub-pages. Either bundle this with the first sub-page commit or do it as a final cleanup commit for the module.

## Persona discipline

`03-user-flow.md` and `04-test-scenarios.md` use persona as their primary organizing axis. The personas in these pages MUST match the roles listed in the module's `index.md` Section 4. If you add a persona that isn't in the index, update the index in the same commit.

## Cross-link integrity

Any `[[slug]]` reference must resolve to one of the 12 valid module slugs: `inventory`, `costing`, `inventory-adjustment`, `good-receive-note`, `store-requisition`, `physical-count`, `spot-check`, `purchase-request`, `purchase-order`, `vendor-pricelist`, `product`, `recipe`. (Note: `stock-take` was renamed to `physical-count` — do not use the old slug.)

## Why templates live in `.specs/`

The `.specs/` directory is hidden from Wiki.js — pages inside are not served as wiki content. Putting templates here means the placeholder-laden template files won't appear as broken pages on the live site. Per-module copies (without `.specs/` prefix) are real wiki pages.
