"""
Read every layout.json in input/, replace each text "content" with [N] marker.
Output per subfolder: temp/1.json (modified JSON), temp/1.txt (original content per marker).
"""

import json
import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")

folders = sorted(os.listdir(INPUT_DIR))

def process_folder(folder):
    folder_path = os.path.join(INPUT_DIR, folder)
    if not os.path.isdir(folder_path):
        return
    if folder == "sample":
        return

    layout_path = os.path.join(folder_path, "layout.json")
    if not os.path.exists(layout_path):
        return

    out_dir = os.path.join(folder_path, "temp")
    out_json = os.path.join(out_dir, "1.json")
    out_txt = os.path.join(out_dir, "1.txt")

    os.makedirs(out_dir, exist_ok=True)

    with open(layout_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    counter = 0
    mapping = []

    def replace_content(obj):
        nonlocal counter
        if isinstance(obj, dict):
            if "content" in obj and isinstance(obj.get("content"), str) and obj.get("type") == "text":
                counter += 1
                mapping.append(obj["content"])
                obj["content"] = f"[{counter}]"
                return
            for v in obj.values():
                replace_content(v)
        elif isinstance(obj, list):
            for item in obj:
                replace_content(item)

    replace_content(data)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    with open(out_txt, "w", encoding="utf-8") as f:
        for line in mapping:
            f.write(line + "\n")

    print(f"[{folder}] Done. Replaced {counter} content fields.")
    print(f"  {out_json}")
    print(f"  {out_txt}")


for folder in folders:
    process_folder(folder)