#!/usr/bin/env python3
"""Scrape the islam.study abuyahya khutba archive into a structured JSON.

The mirror exposes its whole catalog (549 khutbas) on a single page as
`<li data-khutbah …>` elements with all metadata embedded as data-attributes.
Run independently (network required) when the mirror changes; merge_data.py
reads the cached _islam_study.json.

Usage:
  python3 scripts/scrape_islam_study.py
"""

import json
import re
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
URL = "https://islam.study/hutby/abuyahya/"
OUTPUT = BASE_DIR / "scripts" / "_islam_study.json"

import _islam_study_common as common


def attr(tag, name):
    v = tag.get(name)
    return v if v else ""


def parse(html):
    soup = BeautifulSoup(html, "html.parser")
    entries = []
    for li in soup.select("[data-khutbah]"):
        entries.append(
            {
                "id": li.get("id", ""),
                "year": common.year_from_id(li.get("id", "")),
                "number": attr(li, "data-n"),
                "title": attr(li, "data-t").strip(),
                "date": attr(li, "data-d"),
                "duration": attr(li, "data-dur"),
                "audio": common.resolve_audio(attr(li, "data-a")),
                "textUrl": attr(li, "data-x"),
                "pdfUrl": attr(li, "data-pdf"),
                "telegramUrl": "",
                "tg": attr(li, "data-tg"),
                "abuyahyaUrl": attr(li, "data-ay"),
            }
        )

    for e in entries:
        if e["tg"]:
            e["telegramUrl"] = f"https://t.me/hutby_abuyahya/{e['tg']}"
        if e["textUrl"].startswith("/"):
            e["textUrl"] = f"https://islam.study{e['textUrl']}"

    entries.sort(key=lambda e: (e["year"], _num(e["number"])))
    return entries


def _num(number):
    return int(number) if number.isdigit() else 0


def main():
    print(f"Fetching {URL} ...")
    resp = requests.get(URL, timeout=60)
    resp.raise_for_status()

    entries = parse(resp.text)
    if not entries:
        print("Error: no [data-khutbah] entries parsed.")
        sys.exit(1)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    years = {}
    for e in entries:
        years[e["year"]] = years.get(e["year"], 0) + 1
    print(f"Scraped {len(entries)} khutbas -> {OUTPUT}")
    print(f"By year: {dict(sorted(years.items(), key=lambda x: (str(x[0]), x[0])))}")


if __name__ == "__main__":
    main()
