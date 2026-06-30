# DaMENSCH Catalog Image Gap Analysis — Complete Workflow Prompt

> Paste this entire document as the task prompt into a fresh Claude Code (or equivalent agentic coding) session on the new machine. It is self-contained: it encodes the mission, every decision rule, the exact output formats, and all the technical gotchas we discovered over many iterations. Follow it precisely; do not "optimize" away the verification passes.

---

## 0) MISSION / CONTEXT (read first)

DaMENSCH (damensch.com, Indian premium men's innerwear & loungewear) migrated from an OLD website to a NEW website.
- **OLD site** catalog images were **9:16** aspect ratio (~480×853), and **rich**: typically 8–10 images per colour, including not just model shots but feature/benefit cards, size charts, FAQ panels, how-to-wear guides, comparison charts, before/after results, pack-of-N callouts, fit guides, and lifestyle shots.
- **NEW site** catalog images are **3:4** (~1080×1440). They were pulled from **Myntra** via an AI script and AI-mapped to website SKUs — a **lossy** process. Result: fewer images per product, and several image *types* dropped because Myntra disallows them (size charts, FAQ, return/exchange, comparison charts, etc.).

**Goal:** For each product PDP, compare the NEW-site catalog images against the OLD-site images (provided in a CSV) and identify, at the **concept level**, what the old catalog communicated that the new one no longer does. Then produce two deliverables:
1. A **hosted visual comparison report** (GitHub Pages) — a 3-row layout per PDP.
2. An **Excel upload sheet** listing the missing old images and the position to upload each to on the new site.

The point of comparison is **concept**, not pixels. Because aspect ratio changed (9:16 → 3:4), exact layout/crop differs — count a concept as present if it appears in any form; only flag it missing when the concept/information is genuinely gone.

---

## 1) INPUTS

You will be given a **CSV** of the PDPs to process. Expected columns (names may vary slightly in case/spelling — match leniently):
- `new pdp url` — the live new-site PDP, e.g. `https://www.damensch.com/p/<slug>`
- `old image url` — an old-site catalog image, e.g. `https://img.damensch.com/products-old/<file>.jpg?fm=webp`
- `DisplayOrder` — integer position of that old image on the old site
- (optional) `Stockcode`, `Category`, `manual review comments`, `SKU Code` — **carry through untouched** if present.

One PDP appears across **multiple rows** (one per old image). Group by `new pdp url`.

> **Do NOT use the Stockcode (or any filename pattern) to derive the new images.** It is unreliable. See §3.

### Image URL conventions (memorize these)
- OLD image: `https://img.damensch.com/products-old/<file>.jpg?fm=webp` → serves **WebP**. Strip `?fm=webp` to get the **native JPG** (`...jpg`). For download/vision, use the JPG.
- NEW image: `https://img.damensch.com/products/<file>.jpg` → JPG. Append `?fm=webp` for WebP.
- OLD images are 9:16 (~480×853). NEW images are 3:4 (~1080×1440).

---

## 2) STEP 0 — SANITIZE THE PDP LIST (do this first if the input is a raw list)

If the input is a raw list of PDP URLs (e.g., a "remaining revenue" sheet) rather than a clean per-image export, sanitize before anything else:

1. **Dedup.** Canonicalize each URL: lowercase host, strip query string (`?...`) and fragment (`#...`), strip trailing slash. Also dedup at the slug level (the part after `/p/`). Keep one representative row per canonical URL (prefer the row with the most non-empty metadata columns; merge distinct `manual review comments` if they differ).
2. **Remove dead / 404 PDPs.** ⚠️ **CRITICAL GOTCHA:** damensch returns **HTTP 200 even for non-existent products** (soft-404). Do NOT rely on status code. A page is **dead** if, after GET, it has **no JSON-LD `Product` block**, an **empty `<title></title>`**, and **no `og:image`**. A page is **working** if it has a `Product` JSON-LD + a real `<title>` + an `og:image` pointing at `img.damensch.com/products/...`. (Verify your detector on a couple of known-good and a deliberately-bad URL before trusting it at scale.)
3. **Output** only the working, de-duplicated PDPs, **keeping any metadata columns (`manual review comments`, `Category`, `SKU Code`) exactly as-is.**

(In our run, ~53% of a long-tail list was dead — mostly discontinued colourways and old size-suffixed URLs like `...-night-black-l`, `...-rifle-green-xl`. Expect a high dead rate for long-tail lists; surface this number to the user.)

---

## 3) STEP 1 — EXTRACT THE NEW-SITE GALLERY (universal method)

For each PDP, the authoritative ordered catalog gallery is the page's own **JSON-LD `Product.image` array**.
- GET the PDP URL (server-rendered; a plain `curl` with a normal User-Agent is enough — no browser needed).
- Find every `<script type="application/ld+json">…</script>`, JSON-parse each, locate the object with `@type == "Product"`, take its `image` field (string or array). That array, **in order**, IS the new catalog gallery.
- Dedupe preserving order. These URLs look like `https://img.damensch.com/products/<file>.jpg`.

This works **uniformly** for both "migrated" products (filenames like `sw1002-cspwht-0101_p1.jpg … _pN.jpg`) and "legacy" non-migrated products (descriptive filenames like `bamboo-towel-catalog-blue-1.jpg`, `card-dc-t-solid-measurement.jpg`). We verified it on 90/90 PDPs with zero failures. (Do **not** scrape `<img>` tags or guess `_pN` ranges — those miss legacy products and pick up recommended-product noise.)

> Note: legacy/non-migrated products often **kept their original rich images** on the new site (incl. size charts / feature cards) — so they may have few or zero gaps. That's correct and expected.

---

## 4) STEP 2 — DOWNLOAD IMAGES LOCALLY (required for vision)

Vision agents must read local files (they cannot "see" a URL). Download every old + new image to per-PDP folders, e.g. `work/pdps/<slug>/old/oNN.jpg` and `.../new/nNN.jpg`.
- OLD: download from the **native JPG** (strip `?fm=webp`). Sort by `DisplayOrder`. **Handle duplicate DisplayOrder values** by assigning a stable sequence id (`seq` = 1..n) as the identifier; keep the original DisplayOrder only for reference. Use `seq` everywhere downstream.
- NEW: download the JSON-LD image URLs in order; index `idx` = 1..m.
- Keep a manifest JSON: per PDP → `{key/slug, url, title, old:[{seq, url, path}], new:[{idx, url, path}]}`. Derive a human `title` from the slug (Title Case) or from the page's `<title>`/Product name.
- Validate all downloads (non-zero size, valid JPEG). If you must read WebP and your image tool can't, convert to JPG (macOS: `sips -s format jpeg in.webp --out out.jpg`).

---

## 5) STEP 3 — CONCEPT MATCHING (the core; MUST be multi-pass + adversarial)

A single classification/mapping pass **is not reliable** — in our trial a single mapping agent made ~4 concept errors on just 2 PDPs. Use the following **four passes**. Operate **per PDP** (one agent reads all of that PDP's ~10–15 images); do **not** spawn one agent per image (too many at scale).

### Concept taxonomy (use these `type` values)
`model-front, model-back, model-side, model-threequarter, detail-closeup, lifestyle, fabric-material, feature-callout, pack-shot, size-chart-measurement, size-selection-guide, fit-guide, care-instructions, return-exchange, offer-promo, brand-story, colour-range, flatlay-product, other`

Definitions that matter:
- **feature-callout** = a product/studio image with TEXT callouts describing features/benefits.
- **fit-guide** = a model shot overlaid with fit/size spec text (height, chest, "wearing size M").
- **size-chart-measurement** = a measurement TABLE with numbers.
- **detail-closeup** = zoomed crop of fabric/waistband/seam (often with callouts).
- **lifestyle** = model in a real-world scenario/setting (not plain studio).
- **pack-shot** = folded product / packaging / multiple units / pack-of-N.
- **colour-range** = shows the colour variants available.

### Pass A — Analyst (per PDP)
Classify every old and new image (`label` + `type`), and build an **alignment**: for **every** old image (`seq`), pick the single new image (`idx`) that represents the same concept. Rules:
- Match at **concept level**, tolerant of the 9:16→3:4 re-crop (layout/exact info differs; concept should be present).
- **ONE new image maps to AT MOST ONE old image — NO REUSE.** If several old images share a concept but the new set has fewer, assign the new image to the **closest** old and set `new_idx = null` for the surplus old(s). (This is essential so the matched/missing counts are honest — a count reduction must surface as "missing," not as the same new image reused.)
- Set `new_idx = null` when the concept is genuinely **absent** from the new set (size chart, FAQ, a feature card, a comparison chart, etc.).
- Every old `seq` must appear exactly once. Output classifications for old & new, plus the alignment, as structured JSON (use a forced schema).

### Pass B — Skeptic / verify-missing (per PDP)
For each old image the analyst marked `null` (missing): look at the NEW images and ask "is there an **unused** new image that clearly depicts this same concept?" If yes → rescue (assign that idx). If no → confirm missing. **Default to still-missing if unsure.** This catches false negatives (under-matching).

### Pass C — Match-verification (only the non-trivial matched pairs)
Skip pairs where old and new have **identical label AND type** (high confidence). For every other matched pair, an independent agent looks at the two images and decides: do they occupy the **same catalog slot / same concept** (tolerant of re-crop & minor re-branding)? This catches **wrong matches** (e.g., a "98% chest reduction" feature card wrongly matched to a plain front-model photo; a "pack of 3" card matched to a colour-variant collage). Output `same_concept: bool`.

### Pass D — Gap-confirm (only the pairs Pass C doubted)
For each pair marked `same_concept=false`, the **right question** is not "are these two identical" but "**does the old image's concept exist ANYWHERE in the new gallery?**" Give the agent the old image + ALL new images. Decision rules:
- **PRESENT (keep — not a gap):**
  - Same feature whose **headline number/branding changed** (e.g. "4X posture lift" → "2-way posture lift") = same concept.
  - Old feature **subsumed** inside a larger combined "reasons we're better" card on the new site.
  - Same photo with only a **text overlay dropped**, where the *informational* content still appears elsewhere.
  - A body view (front/back/side) that **does** appear on some new image.
- **ABSENT (real gap — break the match → old becomes missing, its matched new becomes "extra"):**
  - A feature / fit-guide / size-chart / comparison / detail card whose **information does not appear on any new image**.
  - A specific **body view/shot that no new image shows**.
  - **Pack-of-N / pack communication** missing (do NOT let a pack image count as matched just because a front-model exists — pack comms is its own concept and must be flagged if gone).

> Tolerance principle throughout: rebrands and supersets = present; lost *information* (specs, size tables, FAQ, distinct features, distinct views, pack comms) = gap. When genuinely unsure, prefer flagging as a gap but record low confidence.

### Why all four passes
Pass B catches false-missing; Passes C+D catch false-matches. Together they removed real errors our earlier passes would have shipped. **Do not skip them.**

---

## 6) STEP 4 — RECONCILE + CONSISTENCY CHECKS (deterministic code)

Build the final alignment from the four passes:
1. Start from Analyst alignment. Dedupe old `seq` (keep first). **Block new reuse**: if a `new_idx` appears twice, keep it for the first old and null the rest.
2. Apply **Skeptic** rescues (assign an unused valid idx to a previously-null old).
3. Apply **Gap-confirm** breaks (set those matches to `null`).
4. Recompute: `missing` = olds with null; `extra_new` = new idx never used; `matched` = count used.

Run **consistency checks** per PDP and **flag (don't silently ship)** any PDP that fails:
- `matched + missing == old_count`
- `matched + extra == new_count`
- every old `seq` present exactly once; no `new_idx` used twice
- upload positions contiguous (see §7B)
- (sample) all image URLs return 200

**Handle agent failures / rate limits gracefully:** if a verification agent fails for a PDP (e.g., usage cap), **do not guess** — keep the safe default (original match) and mark that PDP `manual_review` so it's visibly flagged in the report.

---

## 7) STEP 5 — OUTPUTS

### A) Hosted visual HTML report (GitHub Pages)

Per PDP, **three rows**, plus a master index at top.

**Master index (top of page):** one row per PDP — clickable product title (jump link), old count, new count, matched, missing — colour-coded by missing count (red ≥5, amber ≥1, green 0). For large sets, **group/paginate** (e.g., by Category or in batches) rather than one giant scroll page; keep the index as the landing page.

**Per-PDP block:**
- Clickable **product title** → new PDP URL.
- **Count line:** `{old} → {new} images · {N fewer/more/same}` and `{matched} matched · {missing} missing`.
- **Rows 1 & 2 (aligned columns):** a horizontal, scrollable strip of columns. Each column = ONE old image on **top** (9:16) with a **top-left position badge** (dark) + its concept **type label** underneath; directly **below** it, the matched new image (3:4) with a **top-left position badge (blue) = its actual position on the new site** — OR, where the new site has no equivalent, a **red dashed "Not Available" box** (sized 3:4). Position is shown **as a badge on the image, not as separate text**. Any **extra** new images (matched to no old) are appended as trailing columns labeled "extra new".
- **Row 3 — "After upload — projected new gallery":** the merged final order = the current new images (positions 1..N, at **3:4**) followed by the appended missing old images at positions N+1, N+2… shown at their **original 9:16** aspect. **Do NOT normalize the aspect ratio** — keep 3:4 for current and 9:16 for added, so the visual inconsistency is obvious. Mark each added one with an amber "NEW" flag + its final position badge.

**Critical rendering rules:**
- Reference all images **directly from `img.damensch.com` URLs** — **do NOT base64-embed**. This keeps the file tiny (a 90-PDP report was ~600 KB) and shareable, and scales to hundreds of PDPs. (Base64 made a 2-PDP report 13 MB — avoid.)
- CSS: old `aspect-ratio: 9/16`, new `aspect-ratio: 3/4`, `object-fit: cover` (no crop since native ratio matches). Lazy-load images.
- Self-contained single HTML file(s) per page; mobile-friendly (user reviews on phone).

### B) Excel/CSV upload sheet

For each PDP, the **missing** old images are to be appended to the **END** of the new gallery — regardless of where they sat on the old site. Positions = `(current new count) + 1, +2, …`, assigned in **old display order**.
- Columns (first three MUST match the input export schema so it feeds the upload pipeline): `new pdp url`, `old image url` (the **native .jpg**, no `?fm=webp` — this is the file to upload), `display order` (= the new append position). Then helper columns: `image type`, `old position`, `product`.
- Positions per PDP must be **contiguous** starting at new_count+1.
- Add a **summary tab**: per PDP → old count, new count, matched, missing, flags.
- Build .xlsx with openpyxl (clickable hyperlinks on the URL columns, bold header, freeze panes, autofilter).

**Nuances to preserve in the sheet:**
- "Pack of N" comms, surplus poses (e.g., an old side view with no new side), fit-guide/size-spec cards, FAQ, comparison charts, size charts — all appear as missing rows when genuinely absent. That is intended; it's the count/concept reduction surfaced.
- The old images are 9:16 but the new site is 3:4 — these files will need **reformatting to 3:4** before upload (note this to the user; optionally add a "needs 3:4 reformat" column). They are *not* a straight copy.

---

## 8) STEP 6 — QA / "NO MISTAKES" GATES

1. **Pre-flight extraction validation:** confirm a new gallery was extracted for **every** PDP (count + order); eyeball a sample of thumbnails before the expensive vision step.
2. **Adversarial verification at every stage** (Passes B/C/D) — never trust a single pass.
3. **Automated consistency checks** (§6) — flag, never silently ship.
4. **Confidence / review flagging** for ambiguous or agent-failed PDPs (`manual_review`).
5. **Post-run sample audit:** spot-check ~10 random PDPs visually against the live pages before declaring done.
6. **Idempotent & resumable:** drive everything from the CSV + a per-PDP layout JSON so any fix regenerates deterministically. Never silently truncate/cap coverage — if you bound anything, log what was dropped.

---

## 9) SCALE & BATCHING (for hundreds–thousands of PDPs)

- ~14.5 images/PDP average (~7–8 old, ~6–7 new). 90 PDPs ≈ 1,300 images.
- Per PDP you'll spawn ≈ 1 analyst + ~0.8 skeptic + ~1 match-verify (on non-trivial pairs) + ~0.5 gap-confirm. 
- **Hard limit: ≤ ~1,000 agents per single orchestration run** → process in **batches of ~100–150 PDPs**, each batch running the full pipeline, then **consolidate** into one report + one Excel.
- Expect to hit **usage/rate limits** at large scale — make batches **resumable** (cache completed results) and run them across multiple sessions as capacity frees up.
- **Dedupe against any PDPs already processed** so you only do the remainder; keep prior results in the consolidated output.

---

## 10) HOSTING (GitHub Pages)

- Use the `gh` CLI (must be authenticated). Create/realize a repo, put the report at `index.html` (+ `data/` for the CSV/XLSX, `tools/` for the build scripts, a README). Commit; push.
- Enable Pages via API: `gh api --method POST repos/<owner>/<repo>/pages -f "source[branch]=main" -f "source[path]=/"`.
- The URL is `https://<owner>.github.io/<repo>/`. **Poll until live** with `curl --fail --retry N --retry-delay 6 --retry-all-errors <url>` (note: without `--fail`, a 404 during build counts as success — use `--fail`), or grep the served HTML for a known marker.
- Public Pages exposes the report to anyone with the link (images were already public on the CDN, but the gap analysis becomes public) — confirm with the user; offer a private option if needed.

---

## 11) ENVIRONMENT / TOOLING GOTCHAS (encountered on macOS)

- **Soft-404:** damensch returns HTTP **200** for non-existent PDPs — detect via missing JSON-LD `Product` / empty `<title>` / no `og:image` (see §2).
- **WebP vs JPG:** old served WebP via `?fm=webp`; raw is JPG (sometimes `Content-Type: application/octet-stream`). Download native JPG for vision/display; the Read/vision tool may not handle WebP.
- **New site uses Next.js `/_next/image`** for on-the-fly optimization; ignore that — use the JSON-LD `Product.image` URLs.
- **openpyxl install:** system Python may block pip (PEP 668). Use a venv: `python3 -m venv .venv && .venv/bin/pip install openpyxl` (don't pass `-q` to `venv`, it can fail silently on some setups). Use `.venv/bin/python` (absolute path) when in subdirs.
- **Image dims/convert:** `sips -g pixelWidth -g pixelHeight file` and `sips -s format jpeg in --out out`.
- **Private Google Sheet:** public CSV export returns 401; read it via an authenticated Drive integration (export the first/active sheet to CSV). Large exports may be base64-chunked — decode fully.

---

## 12) OPTIONAL — IMAGE FILE-SIZE ANALYSIS (if asked)

Compare per-PDP total/average image bytes old vs new. Use **WebP-as-served** (both sites deliver WebP via the CDN) for a like-for-like comparison: fetch each image with `?fm=webp` and read actual bytes. (Finding from our run: new images average ~2× the bytes of old ones — ~90 KB vs ~43 KB each — because resolution jumped 480×853 → 1080×1440 (~2.25× pixels), so total page image weight rose ~53% *despite fewer images*. Also report raw-JPG originals as a secondary number, and note that the live new site further downscales via Next.js so real per-page delivery may be lower.)

---

## 13) DELIVERABLES CHECKLIST

- [ ] Sanitized working PDP list (if input was a raw list) — dups + dead removed, metadata kept.
- [ ] New galleries extracted via JSON-LD for 100% of PDPs (pre-flight validated).
- [ ] Per-PDP concept alignment via Analyst → Skeptic → Match-verify → Gap-confirm.
- [ ] Reconciliation + consistency checks pass; ambiguous PDPs flagged `manual_review`.
- [ ] Hosted 3-row HTML report (master index + per-PDP, remote images, projected row keeps mixed aspect ratios) — live on GitHub Pages, verified.
- [ ] Excel upload sheet (missing old images at appended positions; schema-compatible columns; summary tab).
- [ ] Post-run sample audit done; headline stats reported (totals, missing by type, top-gap PDPs).

---

### One-line summary of the spirit of this task
Find, **conservatively and verifiably**, every concept the old richer 9:16 catalog communicated that the new 3:4 catalog no longer does — match by concept (not pixels), never reuse a new image across two olds, adversarially verify both the "missing" and the "matched" claims, and output a shareable visual report plus a ready-to-upload Excel sheet — at scale, in resumable batches, with no silently-dropped coverage.
