"""
Translate short lines (2.1.txt) using Google Translate API.
Output per subfolder: temp/3.1.txt (1:1 line mapping with input)
"""

import os
import re
import time
from deep_translator import GoogleTranslator
from tqdm import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")

folders = sorted(os.listdir(INPUT_DIR))

print("Initializing Google Translate (EN->VI)...")
translator = GoogleTranslator(source="en", target="vi")

for folder in folders:
    folder_path = os.path.join(INPUT_DIR, folder)
    if not os.path.isdir(folder_path):
        continue
    if folder == "sample":
        continue

    in_file = os.path.join(folder_path, "temp", "2.1.txt")
    if not os.path.exists(in_file):
        continue

    out_file = os.path.join(folder_path, "temp", "3.1.txt")

    with open(in_file, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    non_empty_indices = [i for i, line in enumerate(lines) if line.strip()]
    all_texts = [lines[i] for i in non_empty_indices]

    print(f"[{folder}] Total lines: {len(lines)}, non-empty: {len(all_texts)}")

    batches = []
    current_batch = ""
    current_indices = []
    batch_info = []

    for idx, text in zip(non_empty_indices, all_texts):
        if current_batch and len(current_batch) + len(text) + 1 > 4500:
            batch_info.append((current_batch, current_indices))
            current_batch = text
            current_indices = [idx]
        else:
            current_batch += ("\n" + text) if current_batch else text
            current_indices.append(idx)
    if current_batch:
        batch_info.append((current_batch, current_indices))

    print(f"  Translating in {len(batch_info)} batches...")

    translated_lines = [""] * len(lines)

    for batch_text, indices in tqdm(batch_info, desc=f"  [{folder}]", unit="batch"):
        if not re.search(r"[a-zA-Z]", batch_text):
            for idx in indices:
                translated_lines[idx] = lines[idx]
            continue

        for attempt in range(3):
            try:
                result = translator.translate(batch_text)
                time.sleep(1)
                result_lines = result.split("\n")
                for i, idx in enumerate(indices):
                    if i < len(result_lines):
                        translated_lines[idx] = result_lines[i].strip()
                    else:
                        translated_lines[idx] = lines[idx]
                break
            except Exception as e:
                print(f"  Retry {attempt+1}: {e}")
                time.sleep(5)
        else:
            for idx in indices:
                translated_lines[idx] = lines[idx]

    with open(out_file, "w", encoding="utf-8") as f:
        for line in translated_lines:
            f.write(line + "\n")

    print(f"  Output: {out_file}")