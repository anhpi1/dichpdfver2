import json

path = r"C:\Users\k\Documents\2025.2\python\dichpdfver2\input\plw40_description.pdf-b148f754-f533-47f0-8734-14b178721d25\temp\4.json"
with open(path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Page 5 = pdf_info[4] (0-based), block index 4
page = data["pdf_info"][4]
page_size = page.get("page_size", page.get("page_bbox", "NOT FOUND"))
block = page["preproc_blocks"][4]

print("=== PAGE 5 (index 4) page_size ===")
print(json.dumps(page_size, indent=2, ensure_ascii=False))

print("\n=== BLOCK index 4 (raw JSON) ===")
print(json.dumps(block, indent=2, ensure_ascii=False))

print("\n=== SUMMARY ===")
print(f"block type: {block['type']}")
print(f"block bbox: {block['bbox']}")
lines = block.get("lines", [])
print(f"number of lines: {len(lines)}")
total_spans = sum(len(line.get("spans", [])) for line in lines)
print(f"total spans across all lines: {total_spans}")
for i, line in enumerate(lines):
    spans = line.get("spans", [])
    print(f"\n  Line {i}: {len(spans)} span(s)")
    for j, span in enumerate(spans):
        print(f"    Span {j}: content = {repr(span['content'])}")