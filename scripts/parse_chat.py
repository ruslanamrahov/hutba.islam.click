#!/usr/bin/env python3
"""Parse Telegram chat export into structured khutba data."""

import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT = BASE_DIR / "tg_chat" / "result.json"
OUTPUT = BASE_DIR / "scripts" / "_parsed.json"

CATALOG_KEYS = {
    1288: ("general", None),
    1297: ("ramadan", None),
    1300: ("ramadan", None),
    1315: ("sira", None),
    1318: ("companions", None),
    1320: ("zul-hijjah", None),
    1326: ("muharram", None),
    1336: ("names-of-allah", None),
    1339: ("mawlid", None),
    1341: ("general", 2023),
    1381: ("shaban", None),
    1384: ("forbidden-deeds", None),
    1393: ("ramadan", None),
    1394: ("aqida", None),
    1400: ("ramadan", None),
    1407: ("ramadan", None),
    1414: ("ramadan", None),
    1415: ("ramadan", None),
    1419: ("zul-hijjah", None),
    1430: ("muharram", None),
    1438: ("aqida", None),
    1439: ("mawlid", None),
    1452: ("new-year", None),
    1467: ("ramadan", None),
    1471: ("ramadan", None),
    1472: ("ramadan", None),
    1475: ("ramadan", None),
    1492: ("zul-hijjah", None),
    1497: ("zul-hijjah", None),
    1554: ("muharram", None),
}


def extract_links(msg):
    links = []
    for item in msg.get("text", []):
        if isinstance(item, dict) and item.get("href"):
            links.append({"text": item.get("text", ""), "href": item["href"]})
    return links


def normalize_number(num_str):
    mapping = {
        "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
        "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
    }
    result = ""
    for ch in num_str:
        result += mapping.get(ch, ch)
    clean = re.sub(r"[^0-9]", "", result)
    return clean if clean else num_str


YEAR_SECTION_RE = re.compile(
    r"📆|🗓",
    re.UNICODE,
)


def parse_year_from_line(line):
    """Extract gregorian year from a section header line."""
    line = line.strip()
    m = re.search(r"(\d{4})\s*[-–]\s*\d{4}\s*года?", line)
    if m:
        year = int(m.group(1))
        if 2010 <= year <= 2030:
            return year
    m = re.search(r"(\d{4})\s*года?", line)
    if m:
        year = int(m.group(1))
        if 2010 <= year <= 2030:
            return year
    m = re.search(r"до\s+(\d{4})\s*[-–]", line)
    if m:
        year = int(m.group(1))
        if 2010 <= year <= 2030:
            return year
    m = re.search(r"до\s+(\d{4})", line)
    if m:
        year = int(m.group(1))
        if 2010 <= year <= 2030:
            return year
    return None


def clean_title(title):
    title = re.sub(r"\s*🌐➤\s*текст\s*$", "", title).strip()
    title = re.sub(r"\s*🌐\s*$", "", title).strip()
    title = re.sub(r"\s*➤\s*текст\s*$", "", title).strip()
    title = re.sub(r"\s*🌐➤\s*$", "", title).strip()
    title = re.sub(r"\s*➤\s*$", "", title).strip()
    title = re.sub(r"\s+текст\s*$", "", title).strip()
    title = re.sub(r"\s+аудио\s*$", "", title).strip()
    title = re.sub(r"\s*_{2,}.*$", "", title).strip()
    title = re.sub(r"\s*\(\s*ﷺ\s*\)", "", title).strip()
    return title


TEXT_LINK_MARKERS = {
    "текст",
    "текст хутбы",
    "читать текст",
    "читать полный текст",
    "читать полный текст хутбы",
    "читать",
    "полный текст",
    "полный текст хутбы",
}


def parse_catalog_message(msg):
    """Stream-parse a catalog message into khutba entries with inline links.

    Entries begin at a `t.me/hutby_abuyahya` link whose text is a number.
    Everything up to the next number link belongs to that entry: the title plus
    optional islam.click (text) and youtube (video) links.
    """
    entries = []
    current = None
    year = None

    def finalize(entry):
        if not entry:
            return
        title = "".join(entry["title_parts"])
        title = title.replace("\n", " ").replace("\xa0", " ")
        title = re.sub(r"^\s*[|｜]\s*", "", title)
        title = re.sub(r"[🎙📆🗓🗂📕📋]+", "", title)
        title = clean_title(title)
        if not title or len(title) < 3:
            return
        entries.append(
            {
                "number": entry["number"],
                "title": title,
                "year": entry["year"],
                "telegramUrl": entry["telegramUrl"],
                "textUrl": entry["textUrl"],
                "videoUrl": entry["videoUrl"],
            }
        )

    for item in msg.get("text", []):
        if isinstance(item, str):
            s = item
            if YEAR_SECTION_RE.search(s):
                y = parse_year_from_line(s)
                if y is not None:
                    year = y
            if current is not None:
                current["title_parts"].append(s)
            continue

        href = item.get("href")
        txt = item.get("text") or ""
        if not href:
            if YEAR_SECTION_RE.search(txt):
                y = parse_year_from_line(txt)
                if y is not None:
                    year = y
            if current is not None:
                current["title_parts"].append(txt)
            continue

        if "t.me/hutby_abuyahya" in href:
            num = normalize_number(txt)
            if num.isdigit():
                finalize(current)
                current = {
                    "number": num,
                    "telegramUrl": href,
                    "title_parts": [],
                    "textUrl": "",
                    "videoUrl": "",
                    "year": year or 0,
                }
        elif "islam.click" in href:
            if current is None:
                continue
            t = txt.strip().lower()
            if t == "" or t in TEXT_LINK_MARKERS:
                current["textUrl"] = href
            else:
                current["title_parts"].append(txt)
                current["textUrl"] = href
        elif "youtu" in href:
            if current is not None:
                current["videoUrl"] = href
        else:
            if current is not None:
                current["title_parts"].append(txt)

    finalize(current)
    return entries


def build_global_telegram_lookup(data):
    """Build a global lookup of krutba entry numbers to Telegram links."""
    lookup = {}
    for msg in data["messages"]:
        if msg["type"] != "message":
            continue
        links = extract_links(msg)
        for l in links:
            href = l["href"]
            lt = l["text"].strip()
            if "t.me/hutby_abuyahya" in href:
                num = normalize_number(lt)
                if num and num.isdigit():
                    lookup[num] = href
    return lookup


def parse_result():
    with open(INPUT, "r", encoding="utf-8") as f:
        data = json.load(f)

    global_telegram = build_global_telegram_lookup(data)

    all_khutbas = []

    for msg in data["messages"]:
        if msg["type"] != "message":
            continue

        msg_id = msg["id"]
        if msg_id not in CATALOG_KEYS:
            continue

        info = CATALOG_KEYS[msg_id]
        category = info[0]
        default_year = info[1]

        entries = parse_catalog_message(msg)

        for entry in entries:
            entry["category"] = category

            if default_year and entry["year"] == 0:
                entry["year"] = default_year

            if not entry["telegramUrl"] and entry["number"] in global_telegram:
                entry["telegramUrl"] = global_telegram[entry["number"]]

            all_khutbas.append(entry)

    seen = set()
    deduped = []
    for k in all_khutbas:
        key = f"{k['title'][:50]}|{k.get('number', '')}|{k['category']}"
        if key not in seen:
            seen.add(key)
            deduped.append(k)

    for i, k in enumerate(deduped):
        k["id"] = i + 1

    for k in deduped:
        if k["year"] is None:
            k["year"] = 0

    sorted_khutbas = sorted(
        deduped,
        key=lambda k: (
            int(k["number"]) if k["number"].isdigit() else 9999,
        ),
    )

    output = []
    for k in sorted_khutbas:
        output.append(
            {
                "id": k["id"],
                "number": k["number"],
                "title": k["title"],
                "year": k["year"],
                "category": k["category"],
                "audioUrl": "",
                "textUrl": k.get("textUrl", ""),
                "telegramUrl": k.get("telegramUrl", ""),
                "videoUrl": k.get("videoUrl", ""),
                "pdfUrl": "",
            }
        )

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    categories = {}
    years = {}
    for k in output:
        years[k["year"]] = years.get(k["year"], 0) + 1
        categories[k["category"]] = categories.get(k["category"], 0) + 1

    print(f"Total entries: {len(output)}")
    print(f"By year: {dict(sorted(years.items(), key=lambda x: (str(x[0]), x[0])))}")
    print(f"By category: {dict(categories)}")

    return output


if __name__ == "__main__":
    parse_result()
