"""
Merge translations back into 1.json using 2.3.txt tracking.
- 2.3.txt maps each [N] -> source file (2.1.txt / 2.2.txt)
- 3.1.txt contains translated short lines
- 3.2.txt contains translated long lines
Output per subfolder: temp/4.json
"""

import json
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")

folders = sorted(os.listdir(INPUT_DIR))

def process_folder(folder):
    folder_path = os.path.join(INPUT_DIR, folder)
    if not os.path.isdir(folder_path):
        return
    if folder == "sample":
        return

    in_json = os.path.join(folder_path, "temp", "1.json")
    in_track = os.path.join(folder_path, "temp", "2.3.txt")
    in_small = os.path.join(folder_path, "temp", "3.1.txt")
    in_big = os.path.join(folder_path, "temp", "3.2.txt")
    out_json = os.path.join(folder_path, "temp", "4.json")

    # Check required inputs exist
    missing = [p for p in [in_json, in_track, in_small, in_big] if not os.path.exists(p)]
    if missing:
        print(f"[{folder}] Skipping — missing: {missing}")
        return

    with open(in_small, "r", encoding="utf-8") as f:
        trans_small = [line.rstrip("\n") for line in f]

    with open(in_big, "r", encoding="utf-8") as f:
        trans_big = [line.rstrip("\n") for line in f]

    with open(in_track, "r", encoding="utf-8") as f:
        track_lines = [line.strip() for line in f]

    mapping = {}
    i_small = 0
    i_big = 0

    for entry in track_lines:
        match = re.match(r"(2\.\d\.txt)\s+\[(\d+)\]", entry)
        if not match:
            continue
        filename, num_str = match.groups()
        n = int(num_str)

        if filename == "2.1.txt":
            mapping[n] = trans_small[i_small] if i_small < len(trans_small) else ""
            i_small += 1
        else:
            mapping[n] = trans_big[i_big] if i_big < len(trans_big) else ""
            i_big += 1

    print(f"[{folder}] Mapping: {len(mapping)} entries ({i_small} short, {i_big} long)")

    with open(in_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    replace_count = 0

    def replace_markers(obj):
        nonlocal replace_count
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k == "content" and isinstance(v, str):
                    match = re.fullmatch(r"\[(\d+)\]", v)
                    if match:
                        n = int(match.group(1))
                        if n in mapping:
                            obj[k] = mapping[n]
                            replace_count += 1
                else:
                    replace_markers(v)
        elif isinstance(obj, list):
            for item in obj:
                replace_markers(item)

    replace_markers(data)

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"  Replaced {replace_count} markers. Output: {out_json}")


for folder in folders:
    process_folder(folder)