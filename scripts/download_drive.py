#!/usr/bin/env python3
"""
Download Google Drive audio files using Playwright.
Handles virus scan confirmation pages.

Usage:
  python3 scripts/download_drive.py              # download all
  python3 scripts/download_drive.py --dry-run    # show what would download
  python3 scripts/download_drive.py --folder "2015"  # single folder

Output: scripts/_downloads/
"""

import json
import sys
from pathlib import Path
import asyncio

BASE_DIR = Path(__file__).resolve().parent.parent
DRIVE_INPUT = BASE_DIR / "scripts" / "_drive_files.json"
DOWNLOAD_DIR = BASE_DIR / "scripts" / "_downloads"


def load_drive_files():
    if not DRIVE_INPUT.exists():
        print(f"Error: {DRIVE_INPUT} not found. Run scan_drive.py first.")
        sys.exit(1)
    with open(DRIVE_INPUT, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_name(name):
    return name.replace("/", "_").replace("\\", "_").replace(":", "_")


async def download_one(page, file_id, dest_path):
    url = f"https://drive.google.com/uc?export=download&id={file_id}"

    try:
        async with page.expect_download(timeout=60000) as download_info:
            try:
                await page.goto(url, wait_until="commit", timeout=30000)
            except Exception:
                pass
        download = await download_info.value
        await download.save_as(str(dest_path))
        if dest_path.exists() and dest_path.stat().st_size > 0:
            return True
    except Exception:
        pass

    return False


async def download_all(files, dry_run=False):
    from playwright.async_api import async_playwright

    total = len(files)
    downloaded = 0
    skipped = 0
    failed = 0

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        for i, f in enumerate(files):
            folder = safe_name(f["folder"])
            filename = safe_name(f["name"])
            file_id = f["id"]

            dest_dir = DOWNLOAD_DIR / folder
            dest_path = dest_dir / filename

            if dest_path.exists() and dest_path.stat().st_size > 1024:
                skipped += 1
                if (i + 1) % 50 == 0:
                    print(f"[{i+1}/{total}] {downloaded} ok, {skipped} skip, {failed} fail")
                continue

            if dry_run:
                print(f"[{i+1}/{total}] (dry) {folder}/{filename}")
                continue

            dest_dir.mkdir(parents=True, exist_ok=True)

            try:
                ok = await download_one(page, file_id, dest_path)
                if ok:
                    downloaded += 1
                else:
                    failed += 1
                    if dest_path.exists():
                        dest_path.unlink()
            except Exception:
                failed += 1
                if dest_path.exists():
                    dest_path.unlink()

            if (i + 1) % 10 == 0:
                print(f"[{i+1}/{total}] {downloaded} ok, {skipped} skip, {failed} fail")

        await browser.close()

    print(f"\nDone. Downloaded: {downloaded}, Skipped: {skipped}, Failed: {failed}, Total: {total}")


def main():
    dry_run = "--dry-run" in sys.argv
    folder_filter = None
    for arg in sys.argv:
        if arg.startswith("--folder="):
            folder_filter = arg.split("=", 1)[1]

    files = load_drive_files()
    if folder_filter:
        files = [f for f in files if folder_filter in f["folder"]]
        print(f"Filtered to folder: {folder_filter} ({len(files)} files)")

    if dry_run:
        print(f"Dry run: {len(files)} files would be downloaded to {DOWNLOAD_DIR}")
        return

    print(f"Downloading {len(files)} files to {DOWNLOAD_DIR}")
    asyncio.run(download_all(files, dry_run=dry_run))


if __name__ == "__main__":
    main()
