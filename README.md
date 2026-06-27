# DaMENSCH — Catalog Image Gap Report

Visual comparison of **old website (9:16)** vs **new website (3:4)** product catalog images, per PDP.

- Each column = one old-website image (top, with its type label) and the matching new-website image directly below (with its position badge).
- A red **Not Available** box = the new website has no equivalent for that old image (a gap to fix).
- Each new image is matched to **only one** old image, so the `matched / missing` counts are accurate.
- Images are served live from `img.damensch.com`.

Open **index.html** (or the published GitHub Pages link).

## Trial scope
2 PDPs (Sleeveless Shapewear Vest – Crisp White, Deo Soft Trunks – Klint Black). Methodology validated here will scale to ~800 PDPs.

## Reproduce
`data/layout.json` holds the per-PDP old→new mapping; `tools/build_report.py` regenerates `index.html` from it.
