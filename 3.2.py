"""
Translate long lines (2.2.txt) using VietAI/envit5-translation model.
Output per subfolder: temp/3.2.txt (1:1 line mapping with input)
"""

import os
import re
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from tqdm.auto import tqdm

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "input")

device = "cuda" if torch.cuda.is_available() else "cpu"
model_name = "VietAI/envit5-translation"
max_length = 1024

print(f"Loading tokenizer and model {model_name} onto {device}...")
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name).to(device)

folders = sorted(os.listdir(INPUT_DIR))

for folder in folders:
    folder_path = os.path.join(INPUT_DIR, folder)
    if not os.path.isdir(folder_path):
        continue
    if folder == "sample":
        continue

    in_file = os.path.join(folder_path, "temp", "2.2.txt")
    if not os.path.exists(in_file):
        continue

    out_file = os.path.join(folder_path, "temp", "3.2.txt")

    with open(in_file, "r", encoding="utf-8") as f:
        lines = [line.rstrip("\n") for line in f]

    print(f"[{folder}] Translating {len(lines)} lines...")

    translated_lines = []

    for line in tqdm(lines, desc=f"  [{folder}]", unit="line"):
        line_stripped = line.strip()
        if line_stripped and re.search(r"[a-zA-Z]", line_stripped):
            try:
                inputs = ["en: " + line_stripped]
                input_ids = tokenizer(inputs, return_tensors="pt", padding=True).input_ids.to(device)
                with torch.no_grad():
                    outputs = model.generate(
                        input_ids,
                        max_length=max_length,
                        early_stopping=True
                    )
                result = tokenizer.decode(outputs[0], skip_special_tokens=True)
                if result.startswith("vi: "):
                    result = result[4:].strip()
                translated_lines.append(result)
            except Exception as e:
                print(f"  Error: {e}")
                translated_lines.append(line_stripped)
        else:
            translated_lines.append(line_stripped)

    with open(out_file, "w", encoding="utf-8") as f:
        for line in translated_lines:
            f.write(line + "\n")

    print(f"  Output: {out_file}")