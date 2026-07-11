#!/usr/bin/env python3
"""
Scan Google Drive folder structure to extract audio file IDs.

Usage:
  python3 scripts/scan_drive.py

Output: scripts/_drive_files.json
"""

import json
import asyncio
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT = BASE_DIR / "scripts" / "_drive_files.json"

YEAR_FOLDER_IDS = {
    "1. Все хутбы до 2015 года": "1nFvxme_S5zMblTMHCivodRBoHI3nROC0",
    "2. Все хутбы 2015 года": "1kZErc2qhkgOUszkolhWC8wS0_NR3q2GP",
    "3. Все хутбы 2016 года": "10kxFGQ2PGbEL9YXhgmpYydEZYMK0adXz",
    "4. Все хутбы 2017 года": "1g-M_dLjtPV0PbR3vkDTJC9fnfi-lciIL",
    "5. Все хутбы 2018 года": "1rCyGNVbseCRn-pEjhpFnyWsHvwZVbkDZ",
    "6. Все хутбы 2019 года": "1CWz8svm7fVNqpsx70zerAomLp5e5PEgW",
    "7. Все хутбы 2020 года": "1NMlbqCqWvMoX1yozHZFv_ENHSh4mKz2w",
    "8. Все хутбы 2021 года": "1T_DaJZrPGPKPi8AO8gtTr-neYXgCQGgi",
    "9. Все хутбы 2022 года": "11DcQmKIrdFmeJIbfgL23qbiSftPtfDvd",
    "10. Все хутбы 2023 года": "1MkJArUbNiEQ2kxD-gHYrKlVbvSO3LFJi",
}

THEMATIC_ID = "1N3afyS_c1GCUbAebBqzdTAK-zpyMLGxR"


async def extract_files(page):
    """Extract file {name, id} from current Drive folder page."""
    return await page.evaluate("""() => {
        const files = [];
        const rows = document.querySelectorAll('[role="row"]');
        rows.forEach(row => {
            const text = row.textContent.trim();
            if (!text.includes('.mp3') && !text.includes('.m4a') && !text.includes('.wav') && !text.includes('.ogg')) return;

            const dataEls = row.querySelectorAll('[data-id]');
            let fileId = '';
            dataEls.forEach(el => {
                const id = el.getAttribute('data-id');
                if (id && id.length > 10) fileId = id;
            });

            if (!fileId) return;

            let name = text;
            const extIdx = name.search(/\\.(mp3|m4a|wav|ogg|aac|flac|wma)/i);
            if (extIdx > 0) {
                name = name.substring(0, extIdx + 4);
            } else {
                name = name.substring(0, 100);
            }

            const cleanIdx = name.indexOf('Udostępniono');
            if (cleanIdx > 0) name = name.substring(0, cleanIdx);
            name = name.trim();

            if (name && fileId) {
                files.push({ name: name, id: fileId });
            }
        });
        return files;
    }""")


async def extract_folders(page):
    """Extract subfolder {name, id} from current Drive folder page."""
    return await page.evaluate("""() => {
        const folders = [];
        const rows = document.querySelectorAll('[role="row"]');
        rows.forEach(row => {
            const text = row.textContent.trim();
            if (!text || text.length < 3) return;

            const dataEls = row.querySelectorAll('[data-id]');
            let folderId = '';
            dataEls.forEach(el => {
                const id = el.getAttribute('data-id');
                if (id && id.length > 10) folderId = id;
            });

            if (!folderId) return;

            let name = text;
            const cleanIdx = name.indexOf('Ukryto');
            if (cleanIdx > 0) name = name.substring(0, cleanIdx);
            name = name.trim();

            if (name && folderId) {
                folders.push({ name: name, id: folderId });
            }
        });
        return folders;
    }""")


async def main():
    from playwright.async_api import async_playwright

    all_files = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1280, "height": 800})
        page = await context.new_page()

        # Scan year folders (flat — files directly inside)
        for folder_name, folder_id in YEAR_FOLDER_IDS.items():
            url = f"https://drive.google.com/drive/folders/{folder_id}"
            print(f"\nOpening: {folder_name}")
            await page.goto(url, wait_until="networkidle")
            await page.wait_for_timeout(4000)

            file_data = await extract_files(page)
            for f in file_data:
                f["folder"] = folder_name
                all_files.append(f)

            print(f"  Found {len(file_data)} files")

        # Scan thematic folder (nested — subfolders with files)
        print(f"\nOpening: Тематические хутбы")
        await page.goto(f"https://drive.google.com/drive/folders/{THEMATIC_ID}", wait_until="networkidle")
        await page.wait_for_timeout(4000)

        subfolders = await extract_folders(page)
        print(f"  Found {len(subfolders)} subfolders")

        for sub in subfolders:
            sub_name = sub["name"]
            sub_id = sub["id"]
            print(f"\n  Opening subfolder: {sub_name}")
            await page.goto(f"https://drive.google.com/drive/folders/{sub_id}", wait_until="networkidle")
            await page.wait_for_timeout(4000)

            file_data = await extract_files(page)
            for f in file_data:
                f["folder"] = f"Тематические хутбы/{sub_name}"
                all_files.append(f)

            print(f"    Found {len(file_data)} files")

        await browser.close()

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(all_files, f, ensure_ascii=False, indent=2)

    print(f"\nTotal: {len(all_files)} files saved to {OUTPUT}")
    return all_files


if __name__ == "__main__":
    asyncio.run(main())
