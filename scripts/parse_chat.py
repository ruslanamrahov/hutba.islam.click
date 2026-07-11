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


def extract_text(msg):
    parts = []
    for item in msg.get("text", []):
        if isinstance(item, str):
            parts.append(item)
        elif isinstance(item, dict):
            parts.append(item.get("text", ""))
    return "".join(parts)


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
    title = re.sub(r"\s+текст\s*$", "", title).strip()
    title = re.sub(r"\s+аудио\s*$", "", title).strip()
    title = re.sub(r"\s*_{2,}.*$", "", title).strip()
    title = re.sub(r"\s*\(\s*ﷺ\s*\)", "", title).strip()
    return title


KHUTBA_LINE_RE = re.compile(
    r"🎙\s*([⁰¹²³⁴⁵⁶⁷⁸⁹\d]+)\s*(?:[|]|\s+)\s*(.+)",
    re.UNICODE,
)


def build_links_lookup(links):
    telegram = {}
    text_links = {}
    for l in links:
        href = l["href"]
        lt = l["text"].strip()
        if "t.me/hutby_abuyahya" in href:
            num = normalize_number(lt)
            if num:
                telegram[num] = href
        elif "islam.click" in href:
            num = normalize_number(lt)
            if num:
                text_links[num] = href
    return telegram, text_links


def parse_entries_with_year_headers(text, links):
    """Parse entries from text that has year section headers."""
    telegram, text_map = build_links_lookup(links)
    entries = []
    lines = text.split("\n")
    current_year = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if YEAR_SECTION_RE.search(stripped):
            year = parse_year_from_line(stripped)
            if year is not None:
                current_year = year
            continue

        m = KHUTBA_LINE_RE.match(stripped)
        if not m:
            continue

        number = normalize_number(m.group(1))
        title = clean_title(m.group(2))

        if not title or len(title) < 3:
            continue

        entry = {
            "number": number,
            "title": title,
            "year": current_year or 0,
            "telegramUrl": telegram.get(number, ""),
            "textUrl": text_map.get(number, ""),
        }
        entries.append(entry)

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

        text = extract_text(msg)
        links = extract_links(msg)

        entries = parse_entries_with_year_headers(text, links)

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
