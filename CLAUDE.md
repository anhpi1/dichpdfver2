# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PDF → Vietnamese translation via MinerU `layout.json` → HTML output.

Pipeline works directly with MinerU's JSON layout structure (not Markdown). Translates text content fields while preserving layout, images, tables.

## Pipeline

| Step | Script | What it does |
|------|--------|-------------|
| 1 | `1.py` | Read `layout.json`, replace every text `content` field with sequential `[N]` marker. Output: `temp/1.json` (modified JSON), `temp/1.txt` (original texts by line) |
| 2 | `2.py` | Split `1.txt` by word count. Output: `temp/2.1.txt` (<10 words), `temp/2.2.txt` (>=10 words), `temp/2.3.txt` (tracking file mapping line numbers to source files) |
| 3.1 | `3.1.py` | Translate short lines (<10 words) via Google Translate API (`deep-translator`). Batched at ~4500 chars. Output: `temp/3.1.txt` |
| 3.2 | `3.2.py` | Translate long lines (>=10 words) via local `VietAI/envit5-translation` T5 model. Output: `temp/3.2.txt` |
| 4 | `4.py` | Merge translations back into JSON using tracking file (`2.3.txt`). Replaces `[N]` markers with translated text. Output: `temp/4.json` |
| 5 | `5.py` | Convert translated `4.json` to positioned HTML with CSS. Renders titles, text, lists, tables, images as absolutely-positioned elements matching original layout. Output: `temp/5.html` |

## Run

```bash
python 1.py
python 2.py
python 3.1.py
python 3.2.py
python 4.py
python 5.py
```

## Input Structure

`input/<pdf-name>-<uuid>/` contains MinerU output:
- `layout.json` — Page layout with `pdf_info[].preproc_blocks[]`, each block has `type` (title/text/list/table/image/chart), `bbox`, `lines[]`, `spans[]`
- `content_list.json` / `content_list_v2.json` — Extracted content blocks
- `model.json` — MinerU model metadata
- `full.md` — Extracted Markdown (not used by this pipeline)
- `images/` — Extracted images referenced by spans

## Output

`temp/5.html` — Self-contained HTML page with:
- Pages as `<div>` elements matching original PDF dimensions
- Absolutely-positioned content blocks matching original layout
- Vietnamese translations preserving original structure
- Embedded images and HTML tables

## Key Design Decisions

- **Hardcoded paths**: All scripts hardcode a single PDF path with Windows absolute paths. Must update `BASE` in each script to target a different PDF.
- **Two-phase translation**: Short lines use Google Translate (fast, batched). Long lines use local T5 model (free, handles context).
- **No shared config**: Each script is standalone with duplicated boilerplate. No CLI args or config module.
- **Tracking file**: `2.3.txt` maps each `[N]` marker to its source file, enabling lossless merge after parallel translation.

## Dependencies

```bash
pip install deep-translator tqdm transformers torch sentencepiece
```

Python 3.10+. Step 3.2 (T5 model) needs significant RAM; GPU recommended.