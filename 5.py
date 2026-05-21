"""
Convert each 4.json (translated layout) to HTML.
Output per subfolder: 5.html
"""

import json
import math
import os
from html import escape
from statistics import NormalDist
from collections import Counter

DEBUG = True  # Toggle: colored borders + type labels on each block

BLOCK_COLORS = {
    "title": "#e74c3c",  # red
    "text": "#3498db",   # blue
    "list": "#2ecc71",   # green
    "table": "#9b59b6",  # purple
    "image": "#f39c12",  # orange
    "chart": "#1abc9c",  # teal
}

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")

folders = sorted(os.listdir(INPUT_DIR))


def fit_font_size(text, box_w, box_h, min_font=5, max_lh=2.0, cap=None, newlines_are_breaks=False):
    """Pick largest font where text fits. Returns (font_size, line_height)."""
    if not text or box_w <= 0 or box_h <= 0:
        return (min_font, 1.2)
    clean = text.replace('\n', ' ')
    n = len(clean)
    if n == 0:
        return (min_font, 1.2)
    limit = cap if cap is not None else 100
    max_font = max(min_font, min(limit, int(box_h / 1.0)))
    for f in range(max_font, min_font - 1, -1):
        cpl = box_w / (0.48 * f)
        if newlines_are_breaks:
            segments = text.split('\n')
            total_lines = 0
            for seg in segments:
                seg_chars = len(seg)
                seg_lines = math.ceil(seg_chars / cpl) if seg_chars > 0 else 1
                total_lines += seg_lines
            needed = total_lines
        else:
            needed = math.ceil(n / cpl) if cpl > 0 else 999
        if needed <= 0:
            continue
        lh = box_h / (needed * f)
        if lh < 1.0:
            continue
        if lh > max_lh:
            # Cap forces small font in tall box → compact lh, no stretching
            if cap is not None and f == max_font:
                return (f, max_lh)
            continue
        if lh * needed * f > box_h:
            continue
        return (f, lh)
    return (min_font, 1.2)


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


def compute_gap_threshold(gaps, fallback=10, percentile=0.30):
    """Gaussian fit: find 'a' where P(0 ≤ gap ≤ a) = percentile."""
    if len(gaps) < 3:
        return fallback
    mu = sum(gaps) / len(gaps)
    var = sum((g - mu) ** 2 for g in gaps) / len(gaps)
    sigma = var ** 0.5
    if sigma < 1e-6:
        return max(mu, 5)
    dist = NormalDist(mu, sigma)
    p_lo = dist.cdf(0)
    p_target = percentile + p_lo
    if p_target >= 0.999:
        p_target = 0.999
    a = dist.inv_cdf(p_target)
    return max(a, 3)


def collect_gaps(blocks, page_w, page_h):
    """Collect vertical and horizontal gaps between source blocks."""
    margin_top = 50
    margin_bottom = 50
    content_top = margin_top
    content_bottom = page_h - margin_bottom

    valid = []
    for block in blocks:
        b = block.get('bbox')
        if not b or len(b) < 4:
            continue
        if b[3] <= content_top or b[1] >= content_bottom:
            continue
        valid.append(b)

    vert_gaps = []
    by_y = sorted(valid, key=lambda b: b[1])
    for i in range(len(by_y) - 1):
        cur = by_y[i]
        nxt = by_y[i + 1]
        if not (cur[2] <= nxt[0] or cur[0] >= nxt[2]):
            gap = nxt[1] - cur[3]
            if gap > 0:
                vert_gaps.append(gap)

    horz_gaps = []
    by_x = sorted(valid, key=lambda b: b[0])
    for i in range(len(by_x) - 1):
        cur = by_x[i]
        nxt = by_x[i + 1]
        if not (cur[3] <= nxt[1] or cur[1] >= nxt[3]):
            gap = nxt[0] - cur[2]
            if gap > 0:
                horz_gaps.append(gap)

    return vert_gaps, horz_gaps


def compute_font_cap(sizes):
    """Compute font cap from mode (or mean if too scattered)."""
    if not sizes:
        return None
    counter = Counter(sizes)
    mode_size, mode_count = counter.most_common(1)[0]
    # If tie (multiple sizes at same frequency), pick smallest
    all_modes = [s for s, c in counter.items() if c == mode_count]
    mode_size = min(all_modes)
    # If mode < 25% of samples, distribution too scattered → use mean
    if mode_count / len(sizes) < 0.25:
        return round(sum(sizes) / len(sizes))
    return mode_size


def expand_blocks(blocks, page_w, page_h):
    """Expand text blocks using source-layout gap statistics."""
    expandable = {'title', 'text', 'list'}
    fixed_types = {'table', 'chart', 'image'}
    margin_top = 50
    margin_bottom = 50
    margin_left = 40
    margin_right = 40
    content_left = margin_left
    content_right = page_w - margin_right
    content_top = margin_top
    content_bottom = page_h - margin_bottom

    # Compute min gaps from source layout statistics
    vert_gaps, horz_gaps = collect_gaps(blocks, page_w, page_h)
    min_gap_y = compute_gap_threshold(vert_gaps, fallback=13)
    min_gap_x = compute_gap_threshold(horz_gaps, fallback=10)

    # Collect fixed (non-expandable) bboxes for horizontal constraint
    fixed_bboxes = []
    for block in blocks:
        t = block.get('type', '')
        if t in fixed_types:
            b = block.get('bbox')
            if b and len(b) >= 4 and not (b[3] <= content_top or b[1] >= content_bottom):
                fixed_bboxes.append(b)

    # Phase 1: expand text blocks horizontally
    for block in blocks:
        t = block.get('type', '')
        if t not in expandable:
            continue
        b = block.get('bbox')
        if not b or len(b) < 4:
            continue
        if b[3] <= content_top or b[1] >= content_bottom:
            continue

        new_x1 = content_left
        new_x2 = content_right

        # Constrain by fixed blocks (tight, no gap)
        for fb in fixed_bboxes:
            if b[1] < fb[3] and b[3] > fb[1]:
                if fb[0] >= b[0] and fb[0] < new_x2:
                    new_x2 = fb[0]
                if fb[2] <= b[2] and fb[2] > new_x1:
                    new_x1 = fb[2]

        # Constrain by expandable blocks (with min_gap_x)
        for other in blocks:
            if other is block:
                continue
            ot = other.get('type', '')
            if ot not in expandable:
                continue
            ob = other.get('bbox')
            if not ob or len(ob) < 4:
                continue
            if ob[3] <= content_top or ob[1] >= content_bottom:
                continue
            if b[1] < ob[3] and b[3] > ob[1]:
                if ob[0] >= b[0] and ob[0] - min_gap_x < new_x2:
                    new_x2 = ob[0] - min_gap_x
                if ob[2] <= b[2] and ob[2] + min_gap_x > new_x1:
                    new_x1 = ob[2] + min_gap_x

        b[0] = new_x1
        b[2] = new_x2

    # Phase 2: collect ALL content-zone blocks sorted by y1
    all_blocks = []
    for block in blocks:
        b = block.get('bbox')
        if not b or len(b) < 4:
            continue
        t = block.get('type', '')
        if b[3] <= content_top or b[1] >= content_bottom:
            continue
        all_blocks.append((b, t))

    all_blocks.sort(key=lambda x: x[0][1])

    # Phase 3: redistribute vertical gaps
    for idx in range(len(all_blocks) - 1):
        cur_b, cur_t = all_blocks[idx]
        nxt_b, _ = all_blocks[idx + 1]

        if cur_t not in expandable:
            continue

        if cur_b[2] <= nxt_b[0] or cur_b[0] >= nxt_b[2]:
            continue

        gap = nxt_b[1] - cur_b[3]
        if gap > min_gap_y:
            extra = gap - min_gap_y
            cur_b[3] += extra

    # Expand last expandable block toward footer margin
    if all_blocks:
        last_b, last_t = all_blocks[-1]
        if last_t in expandable:
            gap = content_bottom - last_b[3]
            if gap > min_gap_y:
                extra = gap - min_gap_y
                last_b[3] += extra


def debug_wrapper(h, block, idx):
    """Wrap rendered block with colored border + type label."""
    if not DEBUG or not h:
        return h
    t = block.get("type", "?")
    b = block.get("bbox", [0, 0, 100, 20])
    color = BLOCK_COLORS.get(t, "#95a5a6")
    x1, y1, x2, y2 = b
    label = f"#{idx} {t} ({x2-x1:.0f}×{y2-y1:.0f})"
    return (
        f'  <div style="position:absolute;left:{x1}px;top:{y1}px;'
        f'width:{x2-x1}px;height:{y2-y1}px;'
        f'border:2px solid {color};box-sizing:border-box;pointer-events:none;'
        f'z-index:999;">'
        f'<span style="position:absolute;top:0;left:0;'
        f'background:{color};color:#fff;font-size:9px;line-height:1;'
        f'padding:1px 3px;white-space:nowrap;">{label}</span>'
        f'</div>\n'
        f'{h}'
    )


def render(block, base_path, cap=None):
    t = block.get("type", "")
    b = block.get("bbox", [0, 0, 100, 20])
    x1, y1, x2, y2 = b
    s = f"position:absolute;left:{x1}px;top:{y1}px;width:{x2-x1}px;height:{y2-y1}px;"

    if t == "title":
        tx = extract_text_lines(block).strip()
        if not tx:
            return ""
        w, h = x2 - x1, y2 - y1
        fs, lh = fit_font_size(tx, w, h, cap=cap)
        return f'  <h3 style="{s}font-weight:bold;font-size:{fs}px;line-height:{lh};overflow:hidden;">{escape(tx)}</h3>'

    if t == "text":
        tx = extract_text_lines(block).strip()
        if not tx:
            return ""
        w, h = x2 - x1, y2 - y1
        fs, lh = fit_font_size(tx, w, h, cap=cap)
        return f'  <p style="{s}font-size:{fs}px;line-height:{lh};overflow:hidden;">{escape(tx)}</p>'

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
        combined = "\n".join(items)
        w, h = x2 - x1, y2 - y1
        fs, lh = fit_font_size(combined, w, h, cap=cap, newlines_are_breaks=True)
        lis = "\n".join(f"    <li>{i}</li>" for i in items)
        return f'  <ul style="{s}overflow:hidden;font-size:{fs}px;line-height:{lh};list-style-position:inside;padding-left:10px;margin:0;">\n{lis}\n  </ul>'

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

    # Pass 1: expand blocks and collect font sizes for cap computation
    all_font_sizes = []
    for page in pages:
        ps = page.get("page_size", [612, 792])
        blocks = page.get("preproc_blocks", [])
        expand_blocks(blocks, ps[0], ps[1])
        for block in blocks:
            t = block.get("type", "")
            if t not in ("title", "text", "list"):
                continue
            b = block.get("bbox")
            if not b or len(b) < 4:
                continue
            # Extract text matching render() logic exactly
            if t == "list":
                items = []
                for sub in block.get("blocks", []):
                    tx = extract_text(sub).strip()
                    if tx:
                        items.append(tx)
                if not items:
                    tx = extract_text_lines(block).strip()
                    if tx:
                        items = [tx]
                tx = "\n".join(items) if items else ""
            else:
                tx = extract_text_lines(block).strip()
            if not tx:
                continue
            w, h = b[2] - b[0], b[3] - b[1]
            fs, _ = fit_font_size(tx, w, h, newlines_are_breaks=(t == "list"))
            all_font_sizes.append(fs)

    cap = compute_font_cap(all_font_sizes)

    # Pass 2: re-expand and render with cap
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

    # Re-load JSON to get fresh (un-expanded) blocks
    with open(in_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    pages = data.get("pdf_info", [])

    for pi, page in enumerate(pages):
        ps = page.get("page_size", [612, 792])
        blocks = page.get("preproc_blocks", [])
        expand_blocks(blocks, ps[0], ps[1])
        out.append(f'<div class="page" style="width:{ps[0]}px;height:{ps[1]}px;" data-page="{pi+1}">\n')
        for bi, block in enumerate(blocks):
            h = render(block, folder_path, cap=cap)
            if h:
                out.append(debug_wrapper(h, block, bi))
        out.append("</div>\n")

    out.append("</body>\n</html>")

    with open(out_html, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"[{folder}] Done. Cap={cap}, Output: {out_html} ({len(pages)} pages)")