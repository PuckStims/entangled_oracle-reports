# Report PDF Workflow

Approved local production route: `browser_print`

Source of truth:
- Generated report HTML is the production source of truth.
- PDF output is produced from that HTML through one local browser-print workflow.

Approved steps:
1. Generate the report HTML locally.
2. Open the HTML in Chrome on the production machine.
3. Use `Print -> Save as PDF`.
4. Enable background graphics.
5. Keep paper size and margins at the report defaults unless a specific report requires a documented override.

Why this route is approved:
- It matches the templates' active `@media print` rules.
- It avoids maintaining a second HTML-to-PDF engine with conflicting pagination behavior.
- It keeps SVG/chart-wheel rendering aligned with the actual reader-facing HTML.

Required validation targets:
- font rendering and background graphics
- chart wheel and SVG visibility
- page-break behavior around month openers, event cards, tables, and technical notes
- footer consistency
- HTML/PDF naming consistency

Current output naming convention:
- HTML remains the primary generated artifact.
- PDF should keep the matching report stem and timestamp when exported from the corresponding HTML.

Non-approved route:
- `oracle_to_pdf.py` is not an active production renderer and should not be revived as a parallel default path without a deliberate replacement decision.
