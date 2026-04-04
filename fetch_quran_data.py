"""
DeenBG — One-Time Quran Data Fetcher
======================================
Run this ONCE to download all 6236 ayahs and save them
locally as  data/quran.json.

After this, DeenBG runs completely offline forever.

Usage:
    python fetch_quran_data.py
    python fetch_quran_data.py --translation en.sahih
"""

import json
import sys
import time
import argparse
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
OUT_FILE = DATA_DIR / "quran.json"

API_BASE = "https://api.alquran.cloud/v1"

TRANSLATIONS = {
    "en.pickthall": "Pickthall",
    "en.sahih": "Saheeh International",
    "en.yusufali": "Yusuf Ali",
    "en.asad": "Muhammad Asad",
}

# Surah metadata (name + ayah count) — used for progress display
SURAH_META = [
    ("Al-Fatihah", 7),
    ("Al-Baqarah", 286),
    ("Ali 'Imran", 200),
    ("An-Nisa", 176),
    ("Al-Ma'idah", 120),
    ("Al-An'am", 165),
    ("Al-A'raf", 206),
    ("Al-Anfal", 75),
    ("At-Tawbah", 129),
    ("Yunus", 109),
    ("Hud", 123),
    ("Yusuf", 111),
    ("Ar-Ra'd", 43),
    ("Ibrahim", 52),
    ("Al-Hijr", 99),
    ("An-Nahl", 128),
    ("Al-Isra", 111),
    ("Al-Kahf", 110),
    ("Maryam", 98),
    ("Ta-Ha", 135),
    ("Al-Anbya", 112),
    ("Al-Hajj", 78),
    ("Al-Mu'minun", 118),
    ("An-Nur", 64),
    ("Al-Furqan", 77),
    ("Ash-Shu'ara", 227),
    ("An-Naml", 93),
    ("Al-Qasas", 88),
    ("Al-'Ankabut", 69),
    ("Ar-Rum", 60),
    ("Luqman", 34),
    ("As-Sajdah", 30),
    ("Al-Ahzab", 73),
    ("Saba", 54),
    ("Fatir", 45),
    ("Ya-Sin", 83),
    ("As-Saffat", 182),
    ("Sad", 88),
    ("Az-Zumar", 75),
    ("Ghafir", 85),
    ("Fussilat", 54),
    ("Ash-Shuraa", 53),
    ("Az-Zukhruf", 89),
    ("Ad-Dukhan", 59),
    ("Al-Jathiyah", 37),
    ("Al-Ahqaf", 35),
    ("Muhammad", 38),
    ("Al-Fath", 29),
    ("Al-Hujurat", 18),
    ("Qaf", 45),
    ("Adh-Dhariyat", 60),
    ("At-Tur", 49),
    ("An-Najm", 62),
    ("Al-Qamar", 55),
    ("Ar-Rahman", 78),
    ("Al-Waqi'ah", 96),
    ("Al-Hadid", 29),
    ("Al-Mujadila", 22),
    ("Al-Hashr", 24),
    ("Al-Mumtahanah", 13),
    ("As-Saf", 14),
    ("Al-Jumu'ah", 11),
    ("Al-Munafiqun", 11),
    ("At-Taghabun", 18),
    ("At-Talaq", 12),
    ("At-Tahrim", 12),
    ("Al-Mulk", 30),
    ("Al-Qalam", 52),
    ("Al-Haqqah", 52),
    ("Al-Ma'arij", 44),
    ("Nuh", 28),
    ("Al-Jinn", 28),
    ("Al-Muzzammil", 20),
    ("Al-Muddaththir", 56),
    ("Al-Qiyamah", 40),
    ("Al-Insan", 31),
    ("Al-Mursalat", 50),
    ("An-Naba", 40),
    ("An-Nazi'at", 46),
    ("'Abasa", 42),
    ("At-Takwir", 29),
    ("Al-Infitar", 19),
    ("Al-Mutaffifin", 36),
    ("Al-Inshiqaq", 25),
    ("Al-Buruj", 22),
    ("At-Tariq", 17),
    ("Al-A'la", 19),
    ("Al-Ghashiyah", 26),
    ("Al-Fajr", 30),
    ("Al-Balad", 20),
    ("Ash-Shams", 15),
    ("Al-Layl", 21),
    ("Ad-Duha", 11),
    ("Ash-Sharh", 8),
    ("At-Tin", 8),
    ("Al-'Alaq", 19),
    ("Al-Qadr", 5),
    ("Al-Bayyinah", 8),
    ("Az-Zalzalah", 8),
    ("Al-'Adiyat", 11),
    ("Al-Qari'ah", 11),
    ("At-Takathur", 8),
    ("Al-'Asr", 3),
    ("Al-Humazah", 9),
    ("Al-Fil", 5),
    ("Quraysh", 4),
    ("Al-Ma'un", 7),
    ("Al-Kawthar", 3),
    ("Al-Kafirun", 6),
    ("An-Nasr", 3),
    ("Al-Masad", 5),
    ("Al-Ikhlas", 4),
    ("Al-Falaq", 5),
    ("An-Nas", 6),
]


def fetch_edition(edition: str, timeout: int = 30) -> list:
    """Fetch an entire Quran edition in one API call."""
    url = f"{API_BASE}/quran/{edition}"
    print(f"  Fetching {edition}…", end=" ", flush=True)
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if data["status"] != "OK":
        raise ValueError(f"API error: {data.get('status')}")
    if "ayahs" in data["data"]:
        ayahs = data["data"]["ayahs"]
    elif "surahs" in data["data"]:
        ayahs = []
        for surah in data["data"]["surahs"]:
            ayahs.extend(surah["ayahs"])
    else:
        raise ValueError(f"Unexpected API format: {data}")
    print(f"✓  ({len(ayahs)} ayahs)")
    return ayahs


def build_db(arabic_ayahs: list, trans_ayahs: list, trans_name: str) -> list:
    """Merge Arabic and translation ayah lists into our DB format."""
    if len(arabic_ayahs) != len(trans_ayahs):
        raise ValueError(
            f"Length mismatch: Arabic={len(arabic_ayahs)}, "
            f"Translation={len(trans_ayahs)}"
        )

    db = []
    global_num = 0
    for surah_idx, (surah_name, ayah_count) in enumerate(SURAH_META):
        surah_num = surah_idx + 1
        for ayah_idx in range(ayah_count):
            ar = arabic_ayahs[global_num]
            tr = trans_ayahs[global_num]
            db.append(
                {
                    "number": global_num + 1,
                    "surah_number": surah_num,
                    "surah_name": surah_name,
                    "ayah_in_surah": ayah_idx + 1,
                    "arabic": ar["text"],
                    "translation": tr["text"],
                }
            )
            global_num += 1

    return db


def main():
    parser = argparse.ArgumentParser(
        description="Download Quran data for offline use by DeenBG."
    )
    parser.add_argument(
        "--translation",
        default="en.sahih",
        choices=list(TRANSLATIONS.keys()),
        help="English translation to download (default: en.sahih)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-download even if data/quran.json already exists.",
    )
    args = parser.parse_args()

    print("\n" + "═" * 55)
    print("  DeenBG — Quran Data Fetcher")
    print("═" * 55)

    if OUT_FILE.exists() and not args.force:
        with open(OUT_FILE, encoding="utf-8") as f:
            existing = json.load(f)
        print(f"\n  data/quran.json already exists ({len(existing)} ayahs).")
        print("  Use --force to re-download.")
        print("═" * 55 + "\n")
        return

    print(f"\n  Translation : {TRANSLATIONS[args.translation]}")
    print(f"  Output      : {OUT_FILE}\n")
    print("  Downloading (2 API calls — takes ~10 seconds)...\n")

    try:
        arabic_ayahs = fetch_edition("quran-uthmani")
        time.sleep(1)
        trans_ayahs = fetch_edition(args.translation)
    except requests.RequestException as e:
        print(f"\n✗ Network error: {e}")
        print("  Check your internet connection and try again.")
        sys.exit(1)

    print("\n  Building local database…", end=" ")
    db = build_db(arabic_ayahs, trans_ayahs, args.translation)
    print(f"✓  {len(db)} ayahs")

    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, separators=(",", ":"))

    size_kb = OUT_FILE.stat().st_size // 1024
    print(f"\n✓ Saved to: {OUT_FILE}  ({size_kb} KB)")
    print("  DeenBG will now run fully offline.")
    print("═" * 55 + "\n")


if __name__ == "__main__":
    main()
