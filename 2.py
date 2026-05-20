"""
Read each 1.txt, split lines by word count.
Output per subfolder:
  temp/2.1.txt — lines with < 10 words
  temp/2.2.txt — lines with >= 10 words
  temp/2.3.txt — tracking: "filename [original_line_number]"
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")

folders = sorted(os.listdir(INPUT_DIR))

for folder in folders:
    folder_path = os.path.join(INPUT_DIR, folder)
    if not os.path.isdir(folder_path):
        continue
    if folder == "sample":
        continue

    in_file = os.path.join(folder_path, "temp", "1.txt")
    if not os.path.exists(in_file):
        continue

    out_dir = os.path.join(folder_path, "temp")
    out_small = os.path.join(out_dir, "2.1.txt")
    out_big = os.path.join(out_dir, "2.2.txt")
    out_track = os.path.join(out_dir, "2.3.txt")

    with open(in_file, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    small_lines = []
    big_lines = []
    track_lines = []

    for i, line in enumerate(lines, start=1):
        word_count = len(line.split())
        if word_count < 10:
            small_lines.append(line)
            track_lines.append(f"2.1.txt [{i}]")
        else:
            big_lines.append(line)
            track_lines.append(f"2.2.txt [{i}]")

    with open(out_small, "w", encoding="utf-8") as f:
        for line in small_lines:
            f.write(line + "\n")

    with open(out_big, "w", encoding="utf-8") as f:
        for line in big_lines:
            f.write(line + "\n")

    with open(out_track, "w", encoding="utf-8") as f:
        for line in track_lines:
            f.write(line + "\n")

    print(f"[{folder}] Done. Total: {len(lines)} lines")
    print(f"  {out_small} — {len(small_lines)} lines (< 10 words)")
    print(f"  {out_big} — {len(big_lines)} lines (>= 10 words)")
    print(f"  {out_track} — {len(track_lines)} tracking entries")