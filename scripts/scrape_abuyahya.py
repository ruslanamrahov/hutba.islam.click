#!/usr/bin/env python3
"""Scrape khutba number → category mapping from abuyahya.net WP API."""

import json
import re
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT = BASE_DIR / "scripts" / "_abuyahya_categories.json"

API_BASE = "https://abuyahya.net/wp-json/wp/v2/posts"

TOPKAL_CATEGORY_IDS = [20, 21, 22, 23, 24, 25, 26, 27, 28]

CAT_SLUG_TO_CLEAN = {
    "akida-i-manhadzh1": "akida-i-manhadzh",
    "zapretnye-deyaniya1": "zapretnye-deyaniya",
    "zikry-i-molby1": "zikry-i-molby",
    "ibadaty1": "ibadaty",
    "prazdnichnye-hutby1": "prazdnichnye-hutby",
    "smyagcheniya-serdec-i-uveshchevaniya1": "smyagcheniya-serdec",
    "spodvizhniki1": "spodvizhniki",
    "sira1": "sira",
    "raznoe1": "raznoe",
}

CAT_ID_TO_CLEAN = {
    20: "raznoe",
    21: "sira",
    22: "spodvizhniki",
    23: "zikry-i-molby",
    24: "smyagcheniya-serdec",
    25: "ibadaty",
    26: "akida-i-manhadzh",
    27: "prazdnichnye-hutby",
    28: "zapretnye-deyaniya",
}


def fetch_page(page, per_page=100):
    cats_csv = ",".join(str(c) for c in TOPKAL_CATEGORY_IDS)
    url = f"{API_BASE}?categories={cats_csv}&per_page={per_page}&page={page}&_embed=wp:featuredmedia"
    req = urllib.request.Request(url, headers={"User-Agent": "hutba-catalog/1.0"})
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        if e.code == 400:
            return []
        raise


def extract_primary_cat(post):
    all_cats = post.get("categories", [])
    for cat_id in all_cats:
        clean = CAT_ID_TO_CLEAN.get(cat_id)
        if clean:
            return clean

    link = post.get("link", "")
    m = re.search(r"/hutby/([^/]+)/", link)
    if m:
        raw = m.group(1)
        url_cat = CAT_SLUG_TO_CLEAN.get(raw)
        if url_cat:
            return url_cat

    return "raznoe"


def extract_number(post):
    embedded = post.get("_embedded", {})
    media_list = embedded.get("wp:featuredmedia", [])
    if media_list:
        title = media_list[0].get("title", {}).get("rendered", "")
        num = title.strip()
        if num.isdigit():
            return num
    return None


def extract_title(post):
    return post.get("title", {}).get("rendered", "")


def scrape():
    entries = []
    page = 1
    missing_number = 0

    while True:
        posts = fetch_page(page)
        if not posts:
            break

        for post in posts:
            num = extract_number(post)
            title = extract_title(post)
            cat = extract_primary_cat(post)
            if num and title:
                entries.append({"number": num, "title": title, "category": cat})
            else:
                missing_number += 1

        print(f"Page {page}: {len(posts)} posts, total entries: {len(entries)}")
        page += 1

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)

    cats_count = {}
    for e in entries:
        cats_count[e["category"]] = cats_count.get(e["category"], 0) + 1

    print(f"\nDone. {len(entries)} khutba entries ({missing_number} skipped).")
    print(f"By category: {dict(sorted(cats_count.items()))}")
    return entries


if __name__ == "__main__":
    scrape()
