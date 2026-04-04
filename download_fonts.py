"""
download_fonts.py  —  Automatic Font Downloader
================================================
Downloads the required fonts for Quran Wallpaper Generator:
  • Amiri       (Arabic — beautiful Naskh calligraphy style)
  • Lato        (Latin  — clean readable translation text)

Fonts are saved into the ./fonts/ subfolder next to this script.
All fonts are open-source (OFL / Apache 2.0).
"""

import os
import sys
import hashlib
from pathlib import Path
from urllib.request import urlretrieve, urlopen
from urllib.error import URLError

FONT_DIR = Path(__file__).parent / "fonts"
FONT_DIR.mkdir(exist_ok=True)

# ─── Font registry ────────────────────────────────────────────────────────────
# Each entry: (filename, download_url, sha256_checksum_or_None)
FONTS = [
    (
        "Amiri-Regular.ttf",
        "https://github.com/aliftype/amiri/releases/download/1.000/Amiri-1.000.zip",
        None,  # We'll extract from zip
        "zip",
    ),
    (
        "Amiri-Bold.ttf",
        "https://github.com/aliftype/amiri/releases/download/1.000/Amiri-1.000.zip",
        None,
        "zip",
    ),
    (
        "Lato-Regular.ttf",
        "https://fonts.gstatic.com/s/lato/v24/S6uyw4BMUTPHjx4wXiWtFCc.woff2",
        None,
        "woff2",  # woff2 needs conversion — use TTF direct link instead
    ),
]

# Direct TTF links (more reliable than zip extraction)
FONTS_DIRECT = [
    (
        "Amiri-Regular.ttf",
        "https://github.com/aliftype/amiri/raw/main/fonts/ttf/Amiri-Regular.ttf",
    ),
    (
        "Amiri-Bold.ttf",
        "https://github.com/aliftype/amiri/raw/main/fonts/ttf/Amiri-Bold.ttf",
    ),
    (
        "Lato-Regular.ttf",
        # Google Fonts CDN TTF
        "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Regular.ttf",
    ),
    (
        "Lato-Light.ttf",
        "https://github.com/google/fonts/raw/main/ofl/lato/Lato-Light.ttf",
    ),
]


def _download(url: str, dest: Path) -> bool:
    """Download url to dest. Returns True on success."""
    try:
        print(f"  Downloading {dest.name}…", end=" ", flush=True)
        tmp = dest.with_suffix(".tmp")
        urlretrieve(url, tmp)
        tmp.rename(dest)
        size_kb = dest.stat().st_size // 1024
        print(f"✓  ({size_kb} KB)")
        return True
    except (URLError, OSError) as e:
        print(f"✗  ({e})")
        if dest.with_suffix(".tmp").exists():
            dest.with_suffix(".tmp").unlink()
        return False


def download_all():
    print("\n" + "═" * 55)
    print("  Quran Wallpaper — Font Downloader")
    print("═" * 55)
    print(f"  Destination: {FONT_DIR}\n")

    all_ok = True
    for filename, url in FONTS_DIRECT:
        dest = FONT_DIR / filename
        if dest.exists():
            print(f"  {filename:<28} already exists, skipping.")
            continue
        if not _download(url, dest):
            all_ok = False

    print()
    if all_ok:
        print("✓ All fonts downloaded successfully.")
        print("  You're ready to run: python wallpaper_generator.py")
    else:
        print("⚠ Some fonts failed to download.")
        print("  Manual download instructions:")
        print("  1. Amiri font:  https://www.amirifont.org  (download TTF package)")
        print("  2. Lato font:   https://fonts.google.com/specimen/Lato")
        print(f"  3. Place .ttf files into: {FONT_DIR}")
    print("═" * 55 + "\n")


if __name__ == "__main__":
    download_all()
