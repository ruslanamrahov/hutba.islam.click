#!/usr/bin/env python3
"""Extract per-khutba islam.click / Telegram / YouTube links from the mockup page.

The reference design file ``biblioteka_hutb_abuyahya.html`` contains curated
per-row links for the 2014/2015/2016 khutbas. This script parses them into an
intermediate JSON consumed by ``merge_data.py``.

Only rows with an actual list are kept (years 2017+ are "архив в Telegram"
placeholders and are skipped). Audio ``data-mp3`` and the shared PDF channel
link are intentionally ignored.
"""

import json
from html.parser import HTMLParser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT = BASE_DIR / "biblioteka_hutb_abuyahya.html"
OUTPUT = BASE_DIR / "scripts" / "_mockup_links.json"

YEAR_BY_DETAILS_ID = {
    "year-before2015": 2014,
    "year-2015": 2015,
    "year-2016": 2016,
}


class MockupParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.current_year = None
        self.row = None
        self.capture = None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        cls = attrs.get("class", "")

        if tag == "details":
            details_id = attrs.get("id", "")
            self.current_year = YEAR_BY_DETAILS_ID.get(details_id)
            return

        if tag == "li" and self.current_year is not None:
            self.row = {
                "year": self.current_year,
                "number": "",
                "title": "",
                "textUrl": "",
                "telegramUrl": "",
                "videoUrl": "",
            }
            self.capture = None
            return

        if tag == "span" and self.row is not None:
            if "kn" in cls.split():
                self.capture = "number"
            elif "kt" in cls.split():
                self.capture = "title"
            return

        if tag == "a" and self.row is not None:
            href = attrs.get("href", "")
            if "t.me/hutby_abuyahya" in href:
                self.row["telegramUrl"] = href
            elif "islam.click" in href:
                self.row["textUrl"] = href
            elif "youtu" in href:
                self.row["videoUrl"] = href

    def handle_endtag(self, tag):
        if tag == "span":
            self.capture = None
        elif tag == "li" and self.row is not None:
            number = "".join(ch for ch in self.row["number"] if ch.isdigit())
            if number:
                self.row["number"] = int(number)
                self.rows.append(self.row)
            self.row = None
        elif tag == "details":
            self.current_year = None

    def handle_data(self, data):
        if self.row is None or self.capture is None:
            return
        self.row[self.capture] += data


def parse_mockup():
    if not INPUT.exists():
        print(f"WARNING: {INPUT.name} not found — skipping mockup link extraction.")
        return []

    parser = MockupParser()
    parser.feed(INPUT.read_text(encoding="utf-8"))

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(parser.rows, f, ensure_ascii=False, indent=2)

    years = {}
    links = {"textUrl": 0, "telegramUrl": 0, "videoUrl": 0}
    for r in parser.rows:
        years[r["year"]] = years.get(r["year"], 0) + 1
        for key in links:
            if r.get(key):
                links[key] += 1

    print(f"Mockup links: {len(parser.rows)} rows → {OUTPUT}")
    print(f"By year: {years}")
    print(f"Link counts: {links}")
    return parser.rows


if __name__ == "__main__":
    parse_mockup()
