"""Shared helpers for the islam.study mirror integration.

Used by scrape_islam_study.py, download_islam_study.py and merge_data.py so the
matching rules, filename sanitization and audio resolution stay in one place.
"""

import re as _re
import unicodedata

SPACES_BASE = "https://islamclick-coolify.ams3.digitaloceanspaces.com"
PDF_CHANNEL = "https://t.me/alhadispdf"

MIRROR_ISLAMCLICK = "https://islamclick.ams3.digitaloceanspaces.com/"
MIRROR_ABUYAHYA = "https://files.abuyahya.net/"

YEAR_FOLDERS = {
    2014: "1. Все хутбы до 2015 года",
    2015: "2. Все хутбы 2015 года",
    2016: "3. Все хутбы 2016 года",
    2017: "4. Все хутбы 2017 года",
    2018: "5. Все хутбы 2018 года",
    2019: "6. Все хутбы 2019 года",
    2020: "7. Все хутбы 2020 года",
    2021: "8. Все хутбы 2021 года",
    2022: "9. Все хутбы 2022 года",
    2023: "10. Все хутбы 2023 года",
}

# abuyahya.net category slugs (trailing digit stripped) -> our category slug.
CATEGORY_SLUG_MAP = {
    "smyagcheniya-serdec-i-uveshchevaniya": "smyagcheniya-serdec",
    "raznoe": "raznoe",
    "zapretnye-deyaniya": "zapretnye-deyaniya",
    "zikry-i-molby": "zikry-i-molby",
    "ibadaty": "ibadaty",
    "akida-i-manhadzh": "akida-i-manhadzh",
}


def resolve_audio(a):
    if not a:
        return ""
    if a.startswith("i:"):
        return MIRROR_ISLAMCLICK + a[2:]
    if a.startswith("a:"):
        return MIRROR_ABUYAHYA + a[2:]
    return a


def year_from_id(id_str):
    if not id_str:
        return 0
    prefix = id_str.split("-")[0]
    if prefix == "pre2015":
        return 2014
    return int(prefix) if prefix.isdigit() else 0


def year_folder(year):
    return YEAR_FOLDERS.get(year, "")


def sanitize_filename(title):
    t = title.replace("/", "_").replace("\\", "_")
    t = t.replace("?", "").replace(":", "")
    t = _re.sub(r"\s+", " ", t).strip()
    return t


def clean_title(s):
    s = unicodedata.normalize("NFC", s)
    s = s.lower()
    s = _re.sub(r"куран", "коран", s)
    s = s.replace("ё", "е")
    s = s.replace("ъ", "")
    return _re.sub(r"[^a-zа-я0-9]", "", s)


def year_from_folder(folder):
    if "до 2015" in folder:
        return 2014
    m = _re.search(r"(20\d\d)\s*года", folder)
    return int(m.group(1)) if m else 0


def _number_from_filename(name):
    m = _re.match(r"\s*audio0*(\d+)\.", name, flags=_re.IGNORECASE)
    return m.group(1) if m else ""


def _title_from_filename(name):
    t = _re.sub(r"^\s*audio\d+\.\s*", "", name, flags=_re.IGNORECASE)
    t = _re.sub(r"\.(mp3|m4a)$", "", t, flags=_re.IGNORECASE)
    return t.strip().rstrip(".").strip()


def drive_identity(drive_files):
    """Build {year, number, title} identities from Drive scan output."""
    out = []
    for df in drive_files:
        name = df.get("name", "")
        title = _title_from_filename(name)
        if not title:
            continue
        out.append(
            {
                "year": year_from_folder(df.get("folder", "")),
                "number": _number_from_filename(name),
                "title": title,
            }
        )
    return out


def category_from_abuyahya_url(url):
    m = _re.search(r"abuyahya\.net/hutby/([^/]+)/", url or "")
    if not m:
        return None
    slug = m.group(1)
    if slug.startswith("hutby-"):
        return None
    base = _re.sub(r"\d+$", "", slug)
    return CATEGORY_SLUG_MAP.get(base) or CATEGORY_SLUG_MAP.get(slug)


def find_new_entries(mirror_entries, existing):
    """Return mirror entries not already represented in `existing`.

    `existing` is a list of {year, number, title} dicts (Drive-derived catalog).
    Match order: (year, number) -> exact title -> fuzzy title prefix. Telegram
    post numbers are intentionally NOT used: they are not unique on the mirror
    (tg 355 is reused for two different khutbas).
    """
    existing_yn = set()
    existing_clean = []
    for k in existing:
        existing_yn.add((str(k.get("year", 0)), str(k.get("number", "") or "")))
        c = clean_title(k.get("title", ""))
        if c:
            existing_clean.append(c)

    new = []
    for e in mirror_entries:
        if (str(e.get("year", 0)), str(e.get("number", "") or "")) in existing_yn:
            continue
        mc = clean_title(e.get("title", ""))
        if mc and mc in existing_clean:
            continue
        matched = False
        if mc and len(mc) >= 12:
            for oc in existing_clean:
                if oc and (mc[:40] in oc or oc[:40] in mc):
                    matched = True
                    break
        if matched:
            continue
        new.append(e)
    return new
