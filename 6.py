"""
Convert 5.html to 6.pdf via Playwright (Chromium headless).
Output per subfolder: 6.pdf
"""

import os
import re
from playwright.sync_api import sync_playwright

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")

for folder in sorted(os.listdir(INPUT_DIR)):
    folder_path = os.path.join(INPUT_DIR, folder)
    if not os.path.isdir(folder_path) or folder == "sample":
        continue

    in_html = os.path.join(folder_path, "5.html")
    if not os.path.exists(in_html):
        print(f"[{folder}] Skipping -- no 5.html")
        continue

    # Extract page dimensions from first .page div
    with open(in_html, "r", encoding="utf-8") as f:
        first_page = f.read(2000)
    m = re.search(r'class="page"[^>]*style="width:(\d+)px;height:(\d+)px;"', first_page)
    pw, ph = 612, 792
    if m:
        pw, ph = int(m.group(1)), int(m.group(2))

    out_pdf = os.path.join(folder_path, "6.pdf")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context(
            viewport={"width": pw, "height": ph},
            device_scale_factor=1,
        )
        page = context.new_page()
        page.goto(f"file:///{os.path.abspath(in_html).replace(os.sep, '/')}")

        # Inject PDF-specific CSS overrides
        page.add_style_tag(content=f"""
            @page {{ size: {pw}px {ph}px; margin: 0; }}
            body {{ background: white !important; margin: 0 !important; padding: 0 !important; }}
            .page {{ margin: 0 !important; box-shadow: none !important; page-break-after: always; }}
        """)

        page.pdf(path=out_pdf, width=f"{pw}px", height=f"{ph}px")
        browser.close()

    print(f"[{folder}] Done. Page={pw}x{ph}, Output: {out_pdf}")