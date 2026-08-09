#!/usr/bin/env python3
"""
Upload local audio/PDF files to DigitalOcean Spaces.

Credentials loaded from:
  ../islamclick-infra.online/.env

Usage:
  python3 scripts/upload_spaces.py              # upload audio from _downloads
  python3 scripts/upload_spaces.py --pdfs       # upload PDFs from tg_chat/files
  python3 scripts/upload_spaces.py --dry-run    # show what would upload

Target structure:
  hutba/{folder}/{filename}
"""

import json
import sys
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DRIVE_INPUT = BASE_DIR / "scripts" / "_drive_files.json"
DOWNLOAD_DIR = BASE_DIR / "scripts" / "_downloads"
PDF_DIR = BASE_DIR / "tg_chat" / "files"
CHAT_EXPORT_PDF_DIR = BASE_DIR / "ChatExport_2026-08-09" / "files"
ENV_FILE = Path(__file__).resolve().parent.parent.parent / "islamclick-infra.online" / ".env"

PUBLIC_BASE = "https://islamclick-coolify.ams3.digitaloceanspaces.com"
SPACES_PATH = "hutba"


def load_creds():
    creds = {}
    if not ENV_FILE.exists():
        print(f"Warning: {ENV_FILE} not found")
        return creds

    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            for key in ["DO_ENDPOINT", "DO_BUCKET", "DO_REGION", "DO_ACCESS_KEY", "DO_SECRET_KEY"]:
                if line.startswith(f"{key}="):
                    val = line.split("=", 1)[1].strip().strip('"').strip("'")
                    creds[key] = val
    return creds


def safe_name(name):
    return name.replace("/", "_").replace("\\", "_")


def upload_files(files, creds, dry_run=False):
    import boto3

    client = boto3.client(
        "s3",
        endpoint_url=creds.get("DO_ENDPOINT"),
        region_name=creds.get("DO_REGION"),
        aws_access_key_id=creds.get("DO_ACCESS_KEY"),
        aws_secret_access_key=creds.get("DO_SECRET_KEY"),
    )

    bucket = creds.get("DO_BUCKET")

    total = len(files)
    uploaded = 0

    for i, f in enumerate(files):
        local_path = f["local"]
        folder = safe_name(f["folder"] or "pdfs")
        filename = os.path.basename(local_path)
        key = f"{SPACES_PATH}/{folder}/{safe_name(filename)}"

        if dry_run:
            print(f"[{i+1}/{total}] (dry) {local_path} → {bucket}/{key}")
            continue

        content_type = "audio/mpeg" if filename.endswith(".mp3") else "application/pdf"
        if filename.endswith(".m4a"):
            content_type = "audio/mp4"

        print(f"[{i+1}/{total}] Uploading {filename}...")
        sys.stdout.flush()

        try:
            client.upload_file(
                str(local_path),
                bucket,
                key,
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": content_type,
                    "ContentDisposition": "inline",
                },
            )
            uploaded += 1
        except Exception as e:
            print(f"  FAILED: {e}")

    print(f"\nDone. Uploaded: {uploaded}/{total}")


def gather_audio_files():
    """Return list of {local: path, folder: name} for audio files."""
    if not DRIVE_INPUT.exists():
        print(f"No drive files index at {DRIVE_INPUT}")
        return []

    with open(DRIVE_INPUT, "r") as f:
        drive_files = json.load(f)

    result = []
    for df in drive_files:
        folder = safe_name(df["folder"])
        filename = safe_name(df["name"])
        local_path = DOWNLOAD_DIR / folder / filename
        if local_path.exists():
            result.append({"local": str(local_path), "folder": df["folder"]})
        else:
            result.append({"local": None, "folder": df["folder"], "name": filename})

    missing = [f for f in result if f["local"] is None]
    result = [f for f in result if f["local"] is not None]

    if missing:
        print(f"Warning: {len(missing)} files not found locally. Run download_drive.py first.")
        for m in missing[:3]:
            print(f"  Missing: {m['folder']}/{m['name']}")

    return result


def gather_pdf_files():
    """Return list of {local: path, folder: 'pdfs'} for PDF files.

    Scans both ChatExport and legacy tg_chat directories. Deduplicates by
    filename (ChatExport takes priority as the primary source).
    """
    seen = set()
    result = []

    for pdf_dir in (CHAT_EXPORT_PDF_DIR, PDF_DIR):
        if not pdf_dir.exists():
            continue
        for f in pdf_dir.iterdir():
            if f.suffix.lower() != ".pdf" or "_thumb" in f.name:
                continue
            if f.name in seen:
                continue
            seen.add(f.name)
            result.append({"local": str(f), "folder": "pdfs"})

    return result


def main():
    dry_run = "--dry-run" in sys.argv
    upload_pdfs = "--pdfs" in sys.argv

    creds = load_creds()
    if not creds or not creds.get("DO_ACCESS_KEY"):
        print("Error: DO credentials not found in ../islamclick-infra.online/.env")
        sys.exit(1)

    print(f"Bucket: {creds['DO_BUCKET']}")
    print(f"Region: {creds.get('DO_REGION')}")
    print()

    files = []

    if upload_pdfs:
        pdf_files = gather_pdf_files()
        print(f"PDFs to upload: {len(pdf_files)}")
        files = pdf_files
    else:
        audio_files = gather_audio_files()
        print(f"Audio files to upload: {len(audio_files)}")
        files = audio_files

    if not files:
        print("No files to upload.")
        return

    upload_files(files, creds, dry_run=dry_run)


if __name__ == "__main__":
    main()
