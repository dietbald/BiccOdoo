# 001_fix_404_page

Friendly branded 404 page for BICC / IGEBC Odoo Online websites.

## What this changes

Patches `ir.ui.view` keyed `http_routing.404` (the actual 404 body in Odoo 19 — `website.page_404` is a stub that's no longer invoked). Replaces the default arch_db with a single-sentence h1 + three cards (Open positions / About us / Get in touch) wrapped in `web.frontend_layout`. All colors use Bootstrap theme classes so each website's brand is picked up automatically.

## Coverage (verified empirically on staging)

| URL state | Behavior |
|-----------|----------|
| `hr.job` published + active | Real job detail page (HTTP 200) |
| `hr.job` unpublished, still active | New 404 page (HTTP 404) |
| `hr.job` archived (`active=False`) | New 404 page (HTTP 404) |
| `hr.job` deleted / nonexistent id | New 404 page (HTTP 404) |
| Any other broken URL | New 404 page (HTTP 404) |

## How to test

After applying to staging, visit any nonexistent URL on the target website:

```
https://bicc-xerxes.odoo.com/jobs/this-does-not-exist-99
```

Expected: branded 404 page with three cards, header/footer chrome present.

## History

Originally deployed via `workers/active/OdooDev/update_404_view.py` (legacy ad-hoc script). That script and its `backups/` folder remain as historical reference. This changeset replaces it.
