#!/usr/bin/env python3
"""Merge parsed khutba data with Google Drive audio files and local PDFs."""

import json
import re as _re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT = BASE_DIR / "scripts" / "_parsed.json"
DRIVE_INPUT = BASE_DIR / "scripts" / "_drive_files.json"
PDF_DIR = BASE_DIR / "tg_chat" / "files"
OUTPUT = BASE_DIR / "src" / "data" / "khutbas.json"

SPACES_BASE = "https://islamclick-coolify.ams3.digitaloceanspaces.com"


def safe_name(name):
    return name.replace("/", "_").replace("\\", "_")


def load_drive_files():
    if DRIVE_INPUT.exists():
        with open(DRIVE_INPUT, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_local_pdfs():
    if not PDF_DIR.exists():
        return []
    pdfs = []
    for f in PDF_DIR.iterdir():
        if f.is_file() and f.suffix.lower() == ".pdf" and "_thumb" not in f.name:
            pdfs.append({"name": f.stem, "filename": f.name, "path": str(f)})
    return pdfs


def clean_str(s):
    s = s.lower()
    s = _re.sub(r"куран", "коран", s)
    s = s.replace("ё", "е")
    return _re.sub(r"[^a-zа-яе0-9]", "", s)


def match_best(title, candidates, name_key="name"):
    title_clean = clean_str(title)
    best = None
    best_score = 0

    for c in candidates:
        c_clean = clean_str(c[name_key])
        if not c_clean:
            continue

        if title_clean[:40] in c_clean or c_clean[:40] in title_clean:
            score = len(title_clean)
        elif title_clean[:25] == c_clean[:25]:
            score = 25
        elif title_clean[:18] in c_clean or c_clean[:18] in title_clean:
            score = 18
        else:
            continue

        if score > best_score:
            best_score = score
            best = c

    return best


def merge():
    with open(INPUT, "r", encoding="utf-8") as f:
        khutbas = json.load(f)

    drive_files = load_drive_files()
    local_pdfs = load_local_pdfs()

    audio_matched = 0
    pdf_matched = 0

    for k in khutbas:
        title = k["title"].strip()

        if drive_files:
            cleaned = []
            for df in drive_files:
                cleaned_name = _re.sub(
                    r"^audio\d+\.\s*",
                    "",
                    df["name"],
                    flags=_re.IGNORECASE,
                ).strip(".mp3").strip(".m4a").strip()
                cleaned.append({"name": cleaned_name, "orig_name": df["name"], "folder": df["folder"], "id": df["id"]})

            best = match_best(title, cleaned)
            if best:
                folder = safe_name(best["folder"])
                fname = safe_name(best["orig_name"])
                k["audioUrl"] = f"{SPACES_BASE}/hutba/{folder}/{fname}"
                audio_matched += 1

        if local_pdfs:
            best = match_best(title, local_pdfs)
            if best:
                k["pdfUrl"] = f"{SPACES_BASE}/hutba/pdfs/{best['filename']}"
                pdf_matched += 1

    for i, k in enumerate(khutbas):
        k["id"] = i + 1

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(khutbas, f, ensure_ascii=False, indent=2)

    years = set()
    categories = set()
    for k in khutbas:
        years.add(k["year"])
        categories.add(k["category"])

    print(f"Merged {len(khutbas)} khutbas → {OUTPUT}")
    print(f"Years: {sorted(years, key=lambda y: (str(y), y))}")
    print(f"Categories: {sorted(categories)}")
    print(f"Audio URLs matched: {audio_matched}/{len(khutbas)}")
    print(f"PDF URLs matched: {pdf_matched}")

    return khutbas


if __name__ == "__main__":
    merge()
