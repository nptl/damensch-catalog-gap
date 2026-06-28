#!/usr/bin/env python3
# Report with 3 rows per PDP: old (9:16) | current new (3:4) | projected new gallery after upload.
# Images referenced directly from img.damensch.com (no base64).
import json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(ROOT, "work")
L = json.load(open(os.path.join(WORK, "layout.json")))
M = json.load(open(os.path.join(WORK, "manifest.json")))
OUT = os.path.join(ROOT, "damensch_catalog_comparison.html")

OLD_BASE = "https://img.damensch.com/products-old"
NEW_BASE = "https://img.damensch.com/products"

def esc(s): return html.escape(str(s if s is not None else ""))
def old_meta(pkey, order):
    for it in M[pkey]["old"]:
        if it["order"] == order: return it
    return {}
def old_src(pkey, order): return f'{OLD_BASE}/{old_meta(pkey,order)["src"]}'
def old_src_webp(pkey, order): return f'{OLD_BASE}/{old_meta(pkey,order)["src"]}?fm=webp'
def new_src(pkey, order): return f'{NEW_BASE}/{L[pkey]["new_style"]}_p{order}.jpg'

def delta_phrase(o, n):
    d = n - o
    if d == 0: return "same number of images"
    if d < 0:  return f"{-d} fewer image{'' if -d==1 else 's'}"
    return f"{d} more image{'' if d==1 else 's'}"

# ---------- rows 1 & 2 : aligned comparison ----------
def old_cell(pkey, order, label):
    return f'''<div class="ocell">
      <div class="imw"><span class="ob old">{order}</span>
        <img loading="lazy" class="oimg" src="{esc(old_src_webp(pkey,order))}"></div>
      <div class="olabel">{esc(label)}</div></div>'''

def new_cell(pkey, new_order):
    if new_order is None:
        return '<div class="ncell"><div class="na">Not Available</div></div>'
    return f'''<div class="ncell"><div class="imw">
      <span class="ob new">{new_order}</span>
      <img loading="lazy" class="nimg" src="{esc(new_src(pkey,new_order))}"></div></div>'''

def extra_col(pkey, new_order, label):
    return f'''<div class="col extra">
      <div class="ocell"><div class="imw blank"><span class="addtag">extra new image</span></div>
        <div class="olabel muted">{esc(label)}</div></div>
      <div class="ncell"><div class="imw"><span class="ob new">{new_order}</span>
        <img loading="lazy" class="nimg" src="{esc(new_src(pkey,new_order))}"></div></div></div>'''

# ---------- row 3 : projected gallery after upload ----------
def projected(pkey):
    d = L[pkey]; nc = d["new_count"]
    missing = sorted([c for c in d["columns"] if c["new_order"] is None], key=lambda c: c["old_order"])
    cards = []
    # current new images (3:4)
    for i in range(1, nc + 1):
        cards.append(f'''<div class="pcard">
          <div class="pimw"><span class="pb cur">{i}</span>
            <img loading="lazy" class="pimg cur" src="{esc(new_src(pkey,i))}"></div>
          <div class="ptag cur">current · 3:4</div></div>''')
    # appended old images (9:16)
    pos = nc + 1
    for c in missing:
        cards.append(f'''<div class="pcard">
          <div class="pimw"><span class="pb add">{pos}</span><span class="newflag">NEW</span>
            <img loading="lazy" class="pimg add" src="{esc(old_src_webp(pkey,c["old_order"]))}"></div>
          <div class="ptag add">added · 9:16</div>
          <div class="pdesc">{esc(c["old_label"])}</div></div>''')
        pos += 1
    return nc, len(missing), pos - 1, "".join(cards)

def section(pkey):
    d = L[pkey]; oc = d["old_count"]; nc = d["new_count"]
    matched = sum(1 for c in d["columns"] if c["new_order"] is not None)
    missing = sum(1 for c in d["columns"] if c["new_order"] is None)
    cols = "".join(f'<div class="col">{old_cell(pkey,c["old_order"],c["old_label"])}{new_cell(pkey,c["new_order"])}</div>' for c in d["columns"])
    cols += "".join(extra_col(pkey, e["new_order"], e["label"]) for e in d.get("extra_new", []))
    dcls = "neg" if nc < oc else ("pos" if nc > oc else "zero")
    p_cur, p_add, p_total, p_cards = projected(pkey)
    return f'''<section class="pdp">
      <a class="title" href="{esc(d["url"])}" target="_blank">{esc(d["title"])}</a>
      <div class="count">{oc} images <span class="ar">&rarr;</span> {nc} images
        <span class="badge {dcls}">{delta_phrase(oc,nc)}</span>
        <span class="mm">{matched} matched &middot; <b class="miss">{missing} missing</b></span></div>

      <div class="rowlabel">Old website (9:16) &nbsp;vs&nbsp; current new website (3:4)</div>
      <div class="carousel">{cols}</div>

      <div class="proj-head">
        <div class="rowlabel proj">After upload &mdash; projected new gallery</div>
        <div class="proj-sub">{p_cur} current images (3:4) + <b>{p_add} added</b> (9:16, kept as-is) &rarr; final order, positions 1&ndash;{p_total}</div>
      </div>
      <div class="proj">{p_cards}</div>
    </section>'''

sections = "".join(section(k) for k in ["pdp1", "pdp2"])
doc = f'''<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DaMENSCH — Catalog Comparison</title>
<style>
*{{box-sizing:border-box}}
body{{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;color:#101828;background:#f8f9fb}}
.wrap{{padding:18px 16px 56px}}
.pagehed{{font-size:12px;color:#98a2b3;margin-bottom:8px}}
section.pdp{{background:#fff;border:1px solid #eaecf0;border-radius:14px;padding:18px 16px;margin:14px 0}}
.title{{font-size:18px;font-weight:700;color:#101828;text-decoration:none;display:inline-block}}
.title:hover{{color:#1570ef;text-decoration:underline}}
.count{{font-size:14px;color:#475467;margin:6px 0 14px}}
.ar{{color:#98a2b3;margin:0 4px}}
.badge{{font-size:12px;font-weight:600;padding:3px 10px;border-radius:999px;margin-left:8px}}
.badge.neg{{background:#fef3f2;color:#b42318}} .badge.pos{{background:#ecfdf3;color:#067647}} .badge.zero{{background:#f2f4f7;color:#475467}}
.mm{{font-size:12px;color:#667085;margin-left:10px}} .mm .miss{{color:#b42318}}
.rowlabel{{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#667085;margin:4px 0 10px}}
.rowlabel.proj{{color:#b54708}}
.carousel,.proj{{display:flex;gap:14px;overflow-x:auto;padding-bottom:10px}}
.col{{flex:0 0 190px;width:190px}}
.imw{{position:relative}}
.oimg{{width:100%;aspect-ratio:9/16;object-fit:cover;border-radius:8px;border:1px solid #eaecf0;display:block;background:#f2f4f7}}
.nimg{{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:8px;border:1px solid #d1e9ff;display:block;background:#f2f4f7}}
.imw.blank{{width:100%;aspect-ratio:9/16;border:1.5px dashed #d0d5dd;border-radius:8px;background:#f9fafb;display:flex;align-items:center;justify-content:center}}
.addtag{{font-size:11px;color:#98a2b3;font-weight:600}}
.ob{{position:absolute;top:6px;left:6px;color:#fff;font-size:12px;font-weight:700;min-width:22px;height:22px;padding:0 6px;border-radius:11px;display:flex;align-items:center;justify-content:center}}
.ob.old{{background:rgba(16,24,40,.82)}} .ob.new{{background:#1570ef}}
.olabel{{font-size:11.5px;font-weight:600;line-height:1.25;margin:7px 0 9px;min-height:42px;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.olabel.muted{{color:#98a2b3;font-weight:500}}
.na{{width:100%;aspect-ratio:3/4;display:flex;align-items:center;justify-content:center;border:1.5px dashed #fda29b;background:#fef3f2;color:#b42318;font-weight:700;font-size:13px;border-radius:8px}}
/* projected row */
.proj-head{{margin-top:18px;border-top:1px solid #eaecf0;padding-top:14px}}
.proj-sub{{font-size:12.5px;color:#475467;margin:-4px 0 12px}}
.proj{{align-items:flex-start}}
.pcard{{flex:0 0 150px;width:150px}}
.pimw{{position:relative}}
.pimg{{width:100%;object-fit:cover;border-radius:8px;display:block;background:#f2f4f7}}
.pimg.cur{{aspect-ratio:3/4;border:1px solid #d1e9ff}}
.pimg.add{{aspect-ratio:9/16;border:2px solid #f79009}}
.pb{{position:absolute;top:6px;left:6px;color:#fff;font-size:12px;font-weight:700;min-width:22px;height:22px;padding:0 6px;border-radius:11px;display:flex;align-items:center;justify-content:center}}
.pb.cur{{background:#1570ef}} .pb.add{{background:#f79009}}
.newflag{{position:absolute;top:6px;right:6px;background:#f79009;color:#fff;font-size:9px;font-weight:800;letter-spacing:.05em;padding:2px 5px;border-radius:5px}}
.ptag{{font-size:10.5px;font-weight:700;margin-top:6px}}
.ptag.cur{{color:#1570ef}} .ptag.add{{color:#b54708}}
.pdesc{{font-size:10.5px;color:#667085;line-height:1.2;margin-top:2px;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}
</style></head><body><div class="wrap">
<div class="pagehed">DaMENSCH &middot; catalog comparison &middot; row 1 = old (9:16), row 2 = current new (3:4), row 3 = projected new gallery after uploading the missing images &middot; images from img.damensch.com</div>
{sections}
</div></body></html>'''
open(OUT, "w").write(doc)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
