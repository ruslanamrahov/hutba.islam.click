#!/usr/bin/env python3
"""Build khutba catalog from DigitalOcean Spaces audio (source of truth).

Each of the ~453 audio files on DO Spaces becomes one khutba entry. Metadata is
derived from the Drive folder + filename, then enriched from the parsed Telegram
catalog (category + Telegram/text links) where a title match exists.
"""

import json
import re as _re
import unicodedata
from pathlib import Path

import _islam_study_common as isl_common

BASE_DIR = Path(__file__).resolve().parent.parent
INPUT = BASE_DIR / "scripts" / "_parsed.json"
DRIVE_INPUT = BASE_DIR / "scripts" / "_drive_files.json"
ABUYAHYA_INPUT = BASE_DIR / "scripts" / "_abuyahya_categories.json"
MOCKUP_INPUT = BASE_DIR / "scripts" / "_mockup_links.json"
ISLAM_STUDY_INPUT = BASE_DIR / "scripts" / "_islam_study.json"
PDF_DIR = BASE_DIR / "tg_chat" / "files"
CHAT_EXPORT_PDF_DIR = BASE_DIR / "ChatExport_2026-08-09" / "files"
OUTPUT = BASE_DIR / "src" / "data" / "khutbas.json"

SPACES_BASE = "https://islamclick-coolify.ams3.digitaloceanspaces.com"
PDF_CHANNEL = "https://t.me/alhadispdf"

THEMATIC_FOLDERS = {
    "Зуль-хиджжа": "ibadaty",
    "жизнеописании": "sira",
    "сподвижниках": "spodvizhniki",
}

# Conservative, unambiguous keywords only — used as a last resort before
# falling back to "general". Ordered by priority (first match wins).
CATEGORY_KEYWORDS = [
    ("ramadan", ["рамадан", "рамазан", "ураза", "таравих", "и'тикаф", "ляйлят аль-кадр", "ночь предопределен"]),
    ("zul-hijjah", ["зуль-хидж", "жертвоприношен", "курбан", "10 лучших дней", "десять лучших дней", "день арафат"]),
    ("muharram", ["мухаррам", "ашура", "ашуры", "день ашура"]),
    ("mawlid", ["маулид", "мавлид"]),
    ("shaban", ["ша'бан", "шаабан", "бараат"]),
    ("spodvizhniki", ["сподвижник"]),
    ("zapretnye-deyaniya", ["ростовщичеств", "колдовств", "сглаз", "прелюбодеян", "злослови"]),
]


def safe_name(name):
    return name.replace("/", "_").replace("\\", "_")


def load_drive_files():
    if DRIVE_INPUT.exists():
        with open(DRIVE_INPUT, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def load_abuyahya_categories():
    if ABUYAHYA_INPUT.exists():
        with open(ABUYAHYA_INPUT, "r", encoding="utf-8") as f:
            entries = json.load(f)
        return [{"name": e["title"], "category": e["category"]} for e in entries]
    return []


def load_mockup_links():
    """Load curated per-row links from the mockup page, keyed by (year, number)."""
    lookup = {}
    if MOCKUP_INPUT.exists():
        with open(MOCKUP_INPUT, "r", encoding="utf-8") as f:
            rows = json.load(f)
        for r in rows:
            lookup[(r["year"], int(r["number"]))] = {
                "textUrl": r.get("textUrl", ""),
                "telegramUrl": r.get("telegramUrl", ""),
                "videoUrl": r.get("videoUrl", ""),
            }
    return lookup


def load_local_pdfs():
    """Scan known PDF directories for matching.
    
    ChatExport_2026-08-09 is the primary source; tg_chat/files is the legacy
    directory with a handful of pre-existing PDFs.
    """
    seen = set()
    pdfs = []

    for pdf_dir in (CHAT_EXPORT_PDF_DIR, PDF_DIR):
        if not pdf_dir.exists():
            continue
        for f in pdf_dir.iterdir():
            if not f.is_file() or f.suffix.lower() != ".pdf":
                continue
            if "_thumb" in f.name:
                continue
            if f.name in seen:
                continue
            seen.add(f.name)

            clean = f.stem
            clean = _re.sub(r"^\d+[_\.]\s*", "", clean)
            clean = _re.sub(r"[_\(\s]\d+[\)]?$", "", clean)
            clean = _re.sub(r"_for_Pdf.*|\.docx.*$", "", clean, flags=_re.IGNORECASE)
            clean = clean.strip()
            pdfs.append({"name": clean, "filename": f.name, "path": str(f)})

    return pdfs


def clean_str(s):
    s = unicodedata.normalize("NFC", s)
    s = s.lower()
    s = _re.sub(r"куран", "коран", s)
    s = s.replace("ё", "е")
    s = s.replace("ъ", "")
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


def year_from_folder(folder):
    if "до 2015" in folder:
        return 2014
    m = _re.search(r"(20\d\d)\s*года", folder)
    if m:
        return int(m.group(1))
    return 0


def category_from_folder(folder):
    for key, cat in THEMATIC_FOLDERS.items():
        if key in folder:
            return cat
    return None


def number_from_filename(name):
    m = _re.match(r"\s*audio0*(\d+)\.", name, flags=_re.IGNORECASE)
    return m.group(1) if m else ""


def title_from_filename(name):
    t = _re.sub(r"^\s*audio\d+\.\s*", "", name, flags=_re.IGNORECASE)
    t = _re.sub(r"\.(mp3|m4a)$", "", t, flags=_re.IGNORECASE)
    return t.strip().rstrip(".").strip()


def category_from_keywords(title):
    low = title.lower()
    for cat, kws in CATEGORY_KEYWORDS:
        for kw in kws:
            if kw in low:
                return cat
    return None


def merge_islam_study(khutbas):
    """Append islam.study mirror khutbas missing from the Drive-derived catalog."""
    if not ISLAM_STUDY_INPUT.exists():
        return khutbas, 0

    with open(ISLAM_STUDY_INPUT, "r", encoding="utf-8") as f:
        mirror_entries = json.load(f)

    new = isl_common.find_new_entries(mirror_entries, khutbas)
    added = 0

    for e in new:
        year = e["year"]
        folder = isl_common.year_folder(year)
        if not folder or not e.get("audio"):
            continue

        title = e["title"]
        number = e["number"]
        filename = f"Audio{number}. {isl_common.sanitize_filename(title)}.mp3"

        category = isl_common.category_from_abuyahya_url(e.get("abuyahyaUrl", ""))
        if category is None:
            category = category_from_keywords(title)
        if category is None:
            category = "general"
        if category == "companions":
            category = "spodvizhniki"
        elif category == "forbidden-deeds":
            category = "zapretnye-deyaniya"
        elif category == "aqida":
            category = "akida-i-manhadzh"

        khutbas.append(
            {
                "number": number,
                "title": title,
                "year": year,
                "category": category,
                "audioUrl": f"{SPACES_BASE}/hutba/{folder}/{filename}",
                "textUrl": e.get("textUrl", ""),
                "telegramUrl": e.get("telegramUrl", ""),
                "videoUrl": "",
                "pdfUrl": e.get("pdfUrl", "") or PDF_CHANNEL,
            }
        )
        added += 1

    return khutbas, added


def merge():
    with open(INPUT, "r", encoding="utf-8") as f:
        tg_catalog = json.load(f)

    drive_files = load_drive_files()
    abuyahya_cats = load_abuyahya_categories()
    local_pdfs = load_local_pdfs()
    mockup_lookup = load_mockup_links()

    # Telegram catalog as enrichment candidates (title -> category + links).
    tg_candidates = [
        {
            "name": t["title"],
            "category": t["category"],
            "year": t.get("year", 0),
            "telegramUrl": t.get("telegramUrl", ""),
            "textUrl": t.get("textUrl", ""),
            "videoUrl": t.get("videoUrl", ""),
        }
        for t in tg_catalog
    ]

    khutbas = []
    enriched = 0
    keyword_tagged = 0
    abuyahya_overrides = 0
    for df in drive_files:
        folder = df["folder"]
        title = title_from_filename(df["name"])
        if not title:
            continue

        year = year_from_folder(folder)
        category = category_from_folder(folder)
        telegram_url = ""
        text_url = ""
        video_url = ""

        tg = match_best(title, tg_candidates)
        if tg:
            enriched += 1
            if category is None:
                category = tg["category"]
            if year == 0 and tg["year"]:
                year = tg["year"]
            telegram_url = tg["telegramUrl"]
            text_url = tg["textUrl"]
            video_url = tg["videoUrl"]

        if category is None:
            kw = category_from_keywords(title)
            if kw:
                category = kw
                keyword_tagged += 1

        if category is None:
            category = "general"

        number = number_from_filename(df["name"])
        if number.isdigit():
            mock = mockup_lookup.get((year, int(number)))
            if mock:
                if mock["textUrl"]:
                    text_url = mock["textUrl"]
                if mock["telegramUrl"]:
                    telegram_url = mock["telegramUrl"]
                if mock["videoUrl"]:
                    video_url = mock["videoUrl"]
        abu_match = match_best(title, abuyahya_cats)
        if abu_match:
            category = abu_match["category"]
            abuyahya_overrides += 1

        if category == "companions":
            category = "spodvizhniki"
        elif category == "forbidden-deeds":
            category = "zapretnye-deyaniya"
        elif category == "aqida":
            category = "akida-i-manhadzh"

        audio_folder = safe_name(folder)
        audio_file = safe_name(df["name"])
        khutbas.append(
            {
                "number": number,
                "title": title,
                "year": year,
                "category": category,
                "audioUrl": f"{SPACES_BASE}/hutba/{audio_folder}/{audio_file}",
                "textUrl": text_url,
                "telegramUrl": telegram_url,
                "videoUrl": video_url,
                "pdfUrl": PDF_CHANNEL,
            }
        )

    pdf_matched = 0
    if local_pdfs:
        for k in khutbas:
            best = match_best(k["title"], local_pdfs)
            if best:
                k["pdfUrl"] = f"{SPACES_BASE}/hutba/pdfs/{best['filename']}"
                pdf_matched += 1

    khutbas, islam_study_added = merge_islam_study(khutbas)

    for i, k in enumerate(khutbas):
        k["id"] = i + 1

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(khutbas, f, ensure_ascii=False, indent=2)

    years = {}
    categories = {}
    for k in khutbas:
        years[k["year"]] = years.get(k["year"], 0) + 1
        categories[k["category"]] = categories.get(k["category"], 0) + 1

    print(f"Built {len(khutbas)} khutbas from {len(drive_files)} audio files → {OUTPUT}")
    print(f"Enriched from Telegram catalog: {enriched}")
    print(f"Categorized by keyword fallback: {keyword_tagged}")
    print(f"Categorized from abuyahya.net: {abuyahya_overrides}")
    print(f"By year: {dict(sorted(years.items(), key=lambda x: (str(x[0]), x[0])))}")
    print(f"By category: {dict(sorted(categories.items()))}")
    print(f"PDF URLs matched: {pdf_matched}")
    print(f"Added from islam.study mirror: {islam_study_added}")

    return khutbas


if __name__ == "__main__":
    merge()
