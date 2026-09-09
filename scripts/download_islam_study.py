#!/usr/bin/env python3
"""Download the islam.study khutbas that are missing from our catalog.

Reads the scraped _islam_study.json and current src/data/khutbas.json, finds the
entries we don't have yet, downloads each audio file into
scripts/_downloads/islam_study/{year_folder}/ and writes a manifest mapping each
local file to its final DigitalOcean Spaces object key.

Upload step (done by hand) uses the manifest; merge_data.py constructs the same
object key so the audioUrl in khutbas.json resolves after upload.

Usage:
  python3 scripts/download_islam_study.py               # download all missing
  python3 scripts/download_islam_study.py --dry-run     # list without downloading
  python3 scripts/download_islam_study.py --limit 3     # first N only
"""

import json
import sys
from pathlib import Path

import requests

BASE_DIR = Path(__file__).resolve().parent.parent
ISLAM_STUDY_INPUT = BASE_DIR / "scripts" / "_islam_study.json"
DRIVE_INPUT = BASE_DIR / "scripts" / "_drive_files.json"
DOWNLOAD_DIR = BASE_DIR / "scripts" / "_downloads" / "islam_study"
MANIFEST = BASE_DIR / "scripts" / "_islam_study_manifest.json"

import _islam_study_common as common


def build_target(entry):
    year = entry["year"]
    folder = common.year_folder(year)
    if not folder:
        return None
    number = entry["number"]
    title = entry["title"]
    filename = f"Audio{number}. {common.sanitize_filename(title)}.mp3"
    key = f"hutba/{folder}/{filename}"
    return {"folder": folder, "filename": filename, "key": key}


def download(url, local_path):
    if local_path.exists() and local_path.stat().st_size > 0:
        return False
    local_path.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(local_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 256):
                if chunk:
                    f.write(chunk)
    return True


def main():
    dry_run = "--dry-run" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    if not ISLAM_STUDY_INPUT.exists():
        print(f"Missing {ISLAM_STUDY_INPUT}. Run scrape_islam_study.py first.")
        sys.exit(1)
    if not DRIVE_INPUT.exists():
        print(f"Missing {DRIVE_INPUT}. Run scan_drive.py first.")
        sys.exit(1)

    with open(ISLAM_STUDY_INPUT, "r", encoding="utf-8") as f:
        mirror_entries = json.load(f)
    with open(DRIVE_INPUT, "r", encoding="utf-8") as f:
        drive_files = json.load(f)

    existing = common.drive_identity(drive_files)
    new = common.find_new_entries(mirror_entries, existing)
    if limit is not None:
        new = new[:limit]

    print(f"New khutbas to download: {len(new)}")

    manifest = []
    downloaded = 0
    skipped = 0
    failed = []

    for i, e in enumerate(new):
        target = build_target(e)
        if not target:
            failed.append({"title": e["title"], "error": "no year folder"})
            continue
        if not e.get("audio"):
            failed.append({"title": e["title"], "error": "no audio url"})
            continue

        local_path = DOWNLOAD_DIR / target["folder"] / target["filename"]
        manifest.append(
            {
                "year": e["year"],
                "number": e["number"],
                "title": e["title"],
                "local": str(local_path.relative_to(BASE_DIR)),
                "key": target["key"],
                "audio": e["audio"],
            }
        )

        if dry_run:
            print(f"[{i+1}/{len(new)}] (dry) {e['audio']}\n    -> {target['key']}")
            continue

        try:
            if download(e["audio"], local_path):
                downloaded += 1
                print(f"[{i+1}/{len(new)}] {target['filename']} ({e['year']})")
            else:
                skipped += 1
                print(f"[{i+1}/{len(new)}] (exists) {target['filename']}")
        except Exception as exc:
            failed.append({"title": e["title"], "error": str(exc)})
            print(f"[{i+1}/{len(new)}] FAILED {target['filename']}: {exc}")

    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    print()
    print(f"Downloaded: {downloaded}, already present: {skipped}, failed: {len(failed)}")
    if failed:
        for item in failed:
            print(f"  FAILED: {item['title']} — {item['error']}")
    print(f"Manifest: {MANIFEST}")


if __name__ == "__main__":
    main()
