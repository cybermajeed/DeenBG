"""
DeenBG — Quran Wallpaper Generator
====================================
Picks a random Quran ayah from the local offline database,
renders it as a beautiful desktop wallpaper, and sets it
as the Windows desktop background.

Fully offline after the one-time data fetch (fetch_quran_data.py).

Author  : CyberMajeed
License : MIT
"""

import os
import sys
import json
import random
import logging
import ctypes
from pathlib import Path
from datetime import datetime

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"
QURAN_DB = BASE_DIR / "data" / "quran.json"
CACHE_FILE = BASE_DIR / "cache" / "seen_ayahs.json"
WALLPAPER_DIR = BASE_DIR / "wallpapers"
FONT_DIR = BASE_DIR / "fonts"
LOG_FILE = BASE_DIR / "logs" / "deenbg.log"

for _d in [WALLPAPER_DIR, BASE_DIR / "cache", BASE_DIR / "logs", BASE_DIR / "data"]:
    _d.mkdir(parents=True, exist_ok=True)

# ─────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# THEMES
# ─────────────────────────────────────────────
THEMES = {
    "midnight_blue": {
        "name": "Midnight Blue",
        "background_color": "#11161e",
        "text_color_arabic": "#e8d5b7",
        "text_color_translation": "#c8b99a",
        "text_color_reference": "#7a6a55",
        "decorative_color": "#7a6a55",
    },
    "obsidian": {
        "name": "Obsidian",
        "background_color": "#000000",
        "text_color_arabic": "#ffffff",
        "text_color_translation": "#cccccc",
        "text_color_reference": "#888888",
        "decorative_color": "#555555",
    },
    "charcoal_gold": {
        "name": "Charcoal & Gold",
        "background_color": "#1c1c1e",
        "text_color_arabic": "#d4a843",
        "text_color_translation": "#c8a96e",
        "text_color_reference": "#7a6535",
        "decorative_color": "#7a6535",
    },
    "parchment": {
        "name": "Parchment",
        "background_color": "#f5ead0",
        "text_color_arabic": "#2c1810",
        "text_color_translation": "#4a3020",
        "text_color_reference": "#8a6040",
        "decorative_color": "#8a6040",
    },
    "slate": {
        "name": "Slate",
        "background_color": "#1d2230",
        "text_color_arabic": "#e2e8f0",
        "text_color_translation": "#94a3b8",
        "text_color_reference": "#4a5568",
        "decorative_color": "#4a5568",
    },
    "forest": {
        "name": "Forest",
        "background_color": "#0E1E0E",
        "text_color_arabic": "#c8e6c9",
        "text_color_translation": "#a5d6a7",
        "text_color_reference": "#4a7a4a",
        "decorative_color": "#4a7a4a",
    },
    "desert": {
        "name": "Desert Sand",
        "background_color": "#4D2E10",
        "text_color_arabic": "#ab9351",
        "text_color_translation": "#76612c",
        "text_color_reference": "#825b30",
        "decorative_color": "#7E4C1A",
    },
    "ivory": {
        "name": "Ivory Minimal",
        "background_color": "#ffffa9",
        "text_color_arabic": "#1b1b1a",
        "text_color_translation": "#2f2f2f",
        "text_color_reference": "#7A7979",
        "decorative_color": "#878787",
    },
    "deep_teal": {
        "name": "Deep Teal",
        "background_color": "#091527",
        "text_color_arabic": "#abece6",
        "text_color_translation": "#7cccc4",
        "text_color_reference": "#2d847c",
        "decorative_color": "#539d97",
    },
    "rose_noir": {
        "name": "Rose Noir",
        "background_color": "#210f15",
        "text_color_arabic": "#f8c8d0",
        "text_color_translation": "#e8a0b0",
        "text_color_reference": "#7a3545",
        "decorative_color": "#7a3545",
    },
}

# ─────────────────────────────────────────────
# DEFAULT CONFIG
# ─────────────────────────────────────────────
DEFAULT_CONFIG = {
    "design": {
        "theme": "midnight_blue",
        "font_arabic": "Amiri-Regular.ttf",
        "font_latin": "Lato-Regular.ttf",
        "decorative_line": True,
    },
    "behavior": {
        "avoid_repeats": True,
        "max_cache_size": 6236,
        "save_wallpapers": True,
        "max_saved_wallpapers": 30,
    },
}


def load_config() -> dict:
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_FILE, encoding="utf-8") as f:
            loaded = json.load(f)
        return _deep_merge(DEFAULT_CONFIG, loaded)
    except Exception as e:
        log.warning(f"Config read error ({e}), using defaults.")
        return DEFAULT_CONFIG


def save_config(cfg: dict) -> None:
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2, ensure_ascii=False)


def _deep_merge(base: dict, override: dict) -> dict:
    result = dict(base)
    for k, v in override.items():
        if isinstance(result.get(k), dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# ─────────────────────────────────────────────
# CACHE
# ─────────────────────────────────────────────
def load_cache() -> set:
    if not CACHE_FILE.exists():
        return set()
    try:
        with open(CACHE_FILE, encoding="utf-8") as f:
            return set(json.load(f))
    except Exception:
        return set()


def save_cache(seen: set, max_size: int) -> None:
    seen_list = list(seen)
    if len(seen_list) >= max_size:
        log.info("All ayahs seen — resetting cache.")
        seen_list = []
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(seen_list, f)
    except Exception as e:
        log.warning(f"Cache save error: {e}")


# ─────────────────────────────────────────────
# QURAN DATA
# ─────────────────────────────────────────────
def load_quran_db() -> list:
    if not QURAN_DB.exists():
        log.critical(
            f"\n\nQuran database not found!\n"
            f"Expected: {QURAN_DB}\n"
            f"Run this first:  python fetch_quran_data.py\n"
            f"It downloads all ayahs once and saves them locally for offline use.\n"
        )
        sys.exit(1)
    try:
        with open(QURAN_DB, encoding="utf-8") as f:
            data = json.load(f)
        log.info(f"Quran DB loaded — {len(data)} ayahs")
        return data
    except Exception as e:
        log.critical(f"Could not read Quran DB: {e}")
        sys.exit(1)


def pick_ayah(db: list, seen: set, avoid_repeats: bool) -> dict:
    if avoid_repeats and len(seen) < len(db):
        unseen = [a for a in db if a["number"] not in seen]
        return random.choice(unseen)
    return random.choice(db)


# ─────────────────────────────────────────────
# SCREEN RESOLUTION
# ─────────────────────────────────────────────
def get_screen_resolution() -> tuple:
    try:
        if sys.platform == "win32":
            user32 = ctypes.windll.user32
            user32.SetProcessDPIAware()
            w = user32.GetSystemMetrics(0)
            h = user32.GetSystemMetrics(1)
            if w > 0 and h > 0:
                log.info(f"Screen: {w}x{h}")
                return w, h
    except Exception as e:
        log.warning(f"Resolution detection failed: {e}")
    return 1920, 1080


# ─────────────────────────────────────────────
# FONT LOADING  (fonts/ folder only)
# ─────────────────────────────────────────────
def load_font(filename: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONT_DIR / filename
    if path.exists():
        try:
            return ImageFont.truetype(str(path), size)
        except Exception as e:
            log.warning(f"Could not load {filename}: {e}")
    else:
        log.warning(f"Font not found: {path} — using PIL fallback.")
    return ImageFont.load_default()


# ─────────────────────────────────────────────
# ARABIC  (harakah preserved)
# ─────────────────────────────────────────────
_reshaper = arabic_reshaper.ArabicReshaper(
    configuration={
        "delete_harakat": False,
        "support_ligatures": True,
    }
)


def reshape(text: str) -> str:
    return get_display(_reshaper.reshape(text))


# ─────────────────────────────────────────────
# TEXT LAYOUT
# ─────────────────────────────────────────────
def measure(draw, text, font):
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def wrap_latin(text, font, draw, max_w):
    words, lines, line = text.split(), [], ""
    for word in words:
        test = (line + " " + word).strip()
        if measure(draw, test, font)[0] <= max_w:
            line = test
        else:
            if line:
                lines.append(line)
            line = word
    if line:
        lines.append(line)
    return lines


def wrap_arabic(text, font, draw, max_w):
    words, raw, cur = text.split(), [], []
    for word in words:
        test = reshape(" ".join(cur + [word]))
        if measure(draw, test, font)[0] <= max_w:
            cur.append(word)
        else:
            if cur:
                raw.append(" ".join(cur))
            cur = [word]
    if cur:
        raw.append(" ".join(cur))
    return [reshape(ln) for ln in raw]


def block_h(lines, font, draw, gap_ratio=0.35):
    if not lines:
        return 0
    _, lh = measure(draw, "Agالله", font)
    return len(lines) * lh + max(0, len(lines) - 1) * int(lh * gap_ratio)


def draw_block(draw, lines, font, color, W, y, gap_ratio=0.35):
    _, lh = measure(draw, "Agالله", font)
    gap = int(lh * gap_ratio)
    for line in lines:
        lw, _ = measure(draw, line, font)
        draw.text(((W - lw) // 2, y), line, font=font, fill=color)
        y += lh + gap
    return y


# ─────────────────────────────────────────────
# WALLPAPER
# ─────────────────────────────────────────────
def generate_wallpaper(ayah: dict, cfg: dict, W: int, H: int) -> Path:
    dc = cfg["design"]
    theme = THEMES.get(dc.get("theme", "midnight_blue"), THEMES["midnight_blue"])

    bg = dc.get("background_color") or theme["background_color"]
    arc = dc.get("text_color_arabic") or theme["text_color_arabic"]
    trc = dc.get("text_color_translation") or theme["text_color_translation"]
    rfc = dc.get("text_color_reference") or theme["text_color_reference"]
    dec = dc.get("decorative_color") or theme["decorative_color"]

    # Resolution-relative font sizes — never zoomed
    sz_ar = max(28, int(H * 0.052))
    sz_tr = max(16, int(H * 0.027))
    sz_ref = max(13, int(H * 0.022))

    font_ar = load_font(dc["font_arabic"], sz_ar)
    font_tr = load_font(dc["font_latin"], sz_tr)
    font_ref = load_font(dc["font_latin"], sz_ref)

    img = Image.new("RGB", (W, H), bg)
    draw = ImageDraw.Draw(img)

    pad_x = int(W * 0.10)
    pad_y = int(H * 0.10)
    max_tw = W - 2 * pad_x

    ar_lines = wrap_arabic(ayah["arabic"], font_ar, draw, max_tw)
    tr_lines = wrap_latin(ayah["translation"], font_tr, draw, max_tw)
    ref_txt = f"— {ayah['surah_name']},  Ayah {ayah['ayah_in_surah']}"

    gap = int(H * 0.038)
    deco_h = int(H * 0.04) if dc.get("decorative_line", True) else 0

    h_ar = block_h(ar_lines, font_ar, draw, 0.30)
    h_tr = block_h(tr_lines, font_tr, draw, 0.40)
    h_ref = measure(draw, ref_txt, font_ref)[1]

    total = h_ar + gap + deco_h + gap + h_tr + gap + h_ref
    y = max(pad_y, (H - total) // 2)

    y = draw_block(draw, ar_lines, font_ar, arc, W, y, 0.30)

    y += gap
    if dc.get("decorative_line", True):
        cy = y + deco_h // 2
        lw = int(W * 0.20)
        cx = W // 2
        draw.line([(cx - lw, cy), (cx + lw, cy)], fill=dec, width=1)
        ds = 4
        draw.polygon(
            [(cx, cy - ds), (cx + ds, cy), (cx, cy + ds), (cx - ds, cy)], fill=dec
        )
        y += deco_h

    y += gap
    y = draw_block(draw, tr_lines, font_tr, trc, W, y, 0.40)

    y += gap
    rw = measure(draw, ref_txt, font_ref)[0]
    draw.text(((W - rw) // 2, y), ref_txt, font=font_ref, fill=rfc)

    # Corner ornaments
    ln = min(pad_x, pad_y) // 3
    tk = 2
    for pts in [
        [(pad_x, pad_y + ln), (pad_x, pad_y), (pad_x + ln, pad_y)],
        [(W - pad_x - ln, pad_y), (W - pad_x, pad_y), (W - pad_x, pad_y + ln)],
        [(pad_x, H - pad_y - ln), (pad_x, H - pad_y), (pad_x + ln, H - pad_y)],
        [
            (W - pad_x - ln, H - pad_y),
            (W - pad_x, H - pad_y),
            (W - pad_x, H - pad_y - ln),
        ],
    ]:
        draw.line(pts, fill=dec, width=tk)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = WALLPAPER_DIR / f"ayah_{ayah['number']}_{ts}.png"
    img.save(str(out), "PNG", optimize=True)
    log.info(f"Saved: {out}")

    # Prune old wallpapers
    files = sorted(WALLPAPER_DIR.glob("*.png"), key=lambda p: p.stat().st_mtime)
    max_w = cfg["behavior"].get("max_saved_wallpapers", 30)
    while len(files) > max_w:
        try:
            files.pop(0).unlink()
        except Exception:
            break

    return out


# ─────────────────────────────────────────────
# SET WALLPAPER
# ─────────────────────────────────────────────
def set_wallpaper(path: Path) -> bool:
    if sys.platform != "win32":
        log.warning(f"Not on Windows. Image saved at: {path}")
        return False
    result = ctypes.windll.user32.SystemParametersInfoW(
        0x0014, 0, str(path.resolve()), 3
    )
    if result:
        log.info("Wallpaper set successfully.")
        return True
    log.error("Failed to set wallpaper via SystemParametersInfoW.")
    return False


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    log.info("=" * 50)
    log.info("DeenBG — starting")
    log.info("=" * 50)

    cfg = load_config()
    db = load_quran_db()
    seen = load_cache() if cfg["behavior"]["avoid_repeats"] else set()
    W, H = get_screen_resolution()

    ayah = pick_ayah(db, seen, cfg["behavior"]["avoid_repeats"])
    log.info(f"Ayah: {ayah['surah_name']} {ayah['ayah_in_surah']} (#{ayah['number']})")

    try:
        path = generate_wallpaper(ayah, cfg, W, H)
    except Exception as e:
        log.critical(f"Generation failed: {e}", exc_info=True)
        sys.exit(1)

    set_wallpaper(path)

    if cfg["behavior"]["avoid_repeats"]:
        seen.add(ayah["number"])
        save_cache(seen, cfg["behavior"]["max_cache_size"])

    log.info("Done ✓")


if __name__ == "__main__":
    main()
