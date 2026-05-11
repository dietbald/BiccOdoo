# 001_homepage_hero_project_focus

## What changes

Rewrites the hero/cover block of the BICC homepage (view key
`website.bicc-construction-engineering-services-in-iloilo`, `website_id=1`) to
focus on active construction work rather than generic corporate copy.

**Before** (single H1, no CTAs):

> Leading Construction and Engineering Solutions in Iloilo City - BiCC, Your Trusted Partner for Comprehensive Construction, Engineering, and Project Management Services.

**After**:

- **H1**: *Your Construction & Project Management Partner in Iloilo*
- **Lead paragraph**: *Vertical builds, roads, demolition, and end-to-end project management — delivered across Panay for government and private clients.*
- **CTAs**:
  - `See Recent Projects` → `#our-services` anchor (services section showcases project capability lines)
  - `Request a Bid` → `#contact-us` anchor (existing contact form)

The parallax background image, all section anchors (`#cover`, `#our-services`,
`#about-us`, `#contact-us`), and the OUR SERVICES / ABOUT US / CONTACT US
sections are preserved verbatim.

## Notes for review on dev (bicc-xerxes.odoo.com)

- The `See Recent Projects` CTA currently anchors to `#our-services` because no
  dedicated `/projects` or recent-projects gallery page exists yet. When such a
  page is added, update the `<a href>` in the cover section accordingly.
- Copy is intentionally generic-truthful: no specific project names or
  numerical claims (e.g. "12+ sites") that I couldn't verify against source.
  Edit the H1/lead in the website builder if you want to swap in real numbers.
- Lead paragraph has inline `color: #ffffff` so it stays readable over the dark
  parallax background filter. Remove if the theme handles cover-text color.
