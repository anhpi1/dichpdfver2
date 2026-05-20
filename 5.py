"""
Convert each 4.json (translated layout) to HTML.
Output per subfolder: 5.html
"""

import json
import os
from html import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")

folders = sorted(os.listdir(INPUT_DIR))


def extract_text(block):
    parts = []
    for line in block.get("lines", []):
        for span in line.get("spans", []):
            c = span.get("content", "")
            if c:
                parts.append(c)
    return " ".join(parts)


def extract_text_lines(block):
    parts = []
    for line in block.get("lines", []):
        lp = []
        for span in line.get("spans", []):
            c = span.get("content", "")
            if c:
                lp.append(c)
        if lp:
            parts.append(" ".join(lp))
    return "\n".join(parts)


def render(block, base_path):
    t = block.get("type", "")
    b = block.get("bbox", [0, 0, 100, 20])
    x1, y1, x2, y2 = b
    s = f"position:absolute;left:{x1}px;top:{y1}px;width:{x2-x1}px;height:{y2-y1}px;"

    if t == "title":
        tx = extract_text_lines(block).strip()
        if not tx:
            return ""
        return f'  <h3 style="{s}font-weight:bold;overflow:hidden;">{escape(tx)}</h3>'

    if t == "text":
        tx = extract_text_lines(block).strip()
        if not tx:
            return ""
        return f'  <p style="{s}overflow:hidden;">{escape(tx)}</p>'

    if t == "list":
        items = []
        for sub in block.get("blocks", []):
            tx = extract_text(sub).strip()
            if tx:
                items.append(escape(tx))
        if not items:
            tx = extract_text_lines(block).strip()
            if tx:
                items = [escape(tx)]
        if not items:
            return ""
        lis = "\n".join(f"    <li>{i}</li>" for i in items)
        return f'  <ul style="{s}overflow:hidden;list-style-position:inside;padding-left:10px;margin:0;">\n{lis}\n  </ul>'

    if t == "table":
        hc = ""
        for sub in block.get("blocks", []):
            for l in sub.get("lines", []):
                for sp in l.get("spans", []):
                    if sp.get("type") == "table" and sp.get("html"):
                        hc = sp["html"]
        if hc:
            return f'  <div style="{s}overflow:auto;font-size:10px;">{hc}</div>'
        return ""

    if t in ("chart", "image"):
        ip = ""
        for sub in block.get("blocks", []):
            for l in sub.get("lines", []):
                for sp in l.get("spans", []):
                    p = sp.get("image_path", "")
                    if p:
                        ip = f"images/{p}"
        if ip and os.path.exists(os.path.join(base_path, ip)):
            return f'  <img style="{s}object-fit:contain;" src="{ip}" alt="{t}">'
        tx = extract_text_lines(block).strip()
        if tx:
            return f'  <pre style="{s}overflow:hidden;font-size:9px;margin:0;">{escape(tx)}</pre>'
        return ""

    return ""


for folder in folders:
    folder_path = os.path.join(INPUT_DIR, folder)
    if not os.path.isdir(folder_path):
        continue
    if folder == "sample":
        continue

    in_json = os.path.join(folder_path, "temp", "4.json")
    if not os.path.exists(in_json):
        print(f"[{folder}] Skipping — no 4.json")
        continue

    out_html = os.path.join(folder_path, "5.html")

    with open(in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    pages = data.get("pdf_info", [])

    out = []
    out.append("""<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Translated PDF Layout</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { background: #888; }
.page { position:relative; background:white; margin:20px auto; box-shadow:0 2px 8px rgba(0,0,0,0.3); overflow:hidden; }
p, h3, ul, div, pre, img { font-family:"Times New Roman",serif; font-size:11px; line-height:1.2; }
img { max-width:100%; max-height:100%; }
table { border-collapse:collapse; width:100%; font-size:10px; }
td { border:1px solid #999; padding:2px 4px; }
</style>
</head>
<body>
""")

    for pi, page in enumerate(pages):
        ps = page.get("page_size", [612, 792])
        out.append(f'<div class="page" style="width:{ps[0]}px;height:{ps[1]}px;" data-page="{pi+1}">\n')
        for block in page.get("preproc_blocks", []):
            h = render(block, folder_path)
            if h:
                out.append(h)
        out.append("</div>\n")

    out.append("</body>\n</html>")

    with open(out_html, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"[{folder}] Done. Output: {out_html} ({len(pages)} pages)")