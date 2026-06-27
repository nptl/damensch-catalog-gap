#!/usr/bin/env python3
# Lightweight report: images referenced directly from img.damensch.com (no base64).
import json, os, html

ROOT = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(ROOT, "work")
L = json.load(open(os.path.join(WORK, "layout.json")))
M = json.load(open(os.path.join(WORK, "manifest.json")))
OUT = os.path.join(ROOT, "damensch_catalog_comparison.html")

OLD_BASE = "https://img.damensch.com/products-old"
NEW_BASE = "https://img.damensch.com/products"

def esc(s): return html.escape(str(s if s is not None else ""))

def old_src(pkey, order):
    for it in M[pkey]["old"]:
        if it["order"] == order:
            return f'{OLD_BASE}/{it["src"]}?fm=webp'
    return ""
def new_src(pkey, order):
    return f'{NEW_BASE}/{L[pkey]["new_style"]}_p{order}.jpg'

def delta_phrase(o, n):
    d = n - o
    if d == 0: return "same number of images"
    if d < 0:  return f"{-d} fewer image{'' if -d==1 else 's'}"
    return f"{d} more image{'' if d==1 else 's'}"

def old_cell(pkey, order, label):
    return f'''<div class="ocell">
      <div class="imw"><span class="ob old">{order}</span>
        <img loading="lazy" class="oimg" src="{esc(old_src(pkey,order))}"></div>
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

def section(pkey):
    d = L[pkey]; oc = d["old_count"]; nc = d["new_count"]
    matched = sum(1 for c in d["columns"] if c["new_order"] is not None)
    missing = sum(1 for c in d["columns"] if c["new_order"] is None)
    cols = "".join(f'<div class="col">{old_cell(pkey,c["old_order"],c["old_label"])}{new_cell(pkey,c["new_order"])}</div>' for c in d["columns"])
    cols += "".join(extra_col(pkey, e["new_order"], e["label"]) for e in d.get("extra_new", []))
    dcls = "neg" if nc < oc else ("pos" if nc > oc else "zero")
    return f'''<section class="pdp">
      <a class="title" href="{esc(d["url"])}" target="_blank">{esc(d["title"])}</a>
      <div class="count">{oc} images <span class="ar">→</span> {nc} images
        <span class="badge {dcls}">{delta_phrase(oc,nc)}</span>
        <span class="mm">{matched} matched · <b class="miss">{missing} missing</b></span></div>
      <div class="carousel">{cols}</div>
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
.count{{font-size:14px;color:#475467;margin:6px 0 16px}}
.ar{{color:#98a2b3;margin:0 4px}}
.badge{{font-size:12px;font-weight:600;padding:3px 10px;border-radius:999px;margin-left:8px}}
.badge.neg{{background:#fef3f2;color:#b42318}} .badge.pos{{background:#ecfdf3;color:#067647}} .badge.zero{{background:#f2f4f7;color:#475467}}
.mm{{font-size:12px;color:#667085;margin-left:10px}} .mm .miss{{color:#b42318}}
.carousel{{display:flex;gap:14px;overflow-x:auto;padding-bottom:10px}}
.col{{flex:0 0 190px;width:190px}}
.imw{{position:relative}}
.oimg{{width:100%;aspect-ratio:9/16;object-fit:cover;border-radius:8px;border:1px solid #eaecf0;display:block;background:#f2f4f7}}
.nimg{{width:100%;aspect-ratio:3/4;object-fit:cover;border-radius:8px;border:1px solid #d1e9ff;display:block;background:#f2f4f7}}
.imw.blank{{width:100%;aspect-ratio:9/16;border:1.5px dashed #d0d5dd;border-radius:8px;background:#f9fafb;display:flex;align-items:center;justify-content:center}}
.addtag{{font-size:11px;color:#98a2b3;font-weight:600}}
.ob{{position:absolute;top:6px;left:6px;color:#fff;font-size:12px;font-weight:700;min-width:22px;height:22px;padding:0 6px;border-radius:11px;display:flex;align-items:center;justify-content:center}}
.ob.old{{background:rgba(16,24,40,.82)}}
.ob.new{{background:#1570ef}}
.olabel{{font-size:11.5px;font-weight:600;line-height:1.25;margin:7px 0 9px;min-height:42px;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden}}
.olabel.muted{{color:#98a2b3;font-weight:500}}
.na{{width:100%;aspect-ratio:3/4;display:flex;align-items:center;justify-content:center;border:1.5px dashed #fda29b;background:#fef3f2;color:#b42318;font-weight:700;font-size:13px;border-radius:8px}}
</style></head><body><div class="wrap">
<div class="pagehed">DaMENSCH · catalog comparison · old website (9:16) on top, matching new website (3:4) below · number badge = position on each site · images served from img.damensch.com</div>
{sections}
</div></body></html>'''
open(OUT, "w").write(doc)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
