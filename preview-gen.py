"""
DeenBG — Theme Preview Generator
==================================
Generates a 1920x1080 PNG wallpaper for every theme using Quran 2:78.
Run this to create preview images for the README or to pick your theme.

Usage:
    python generate_previews.py

Output:
    previews/midnight_blue.png
    previews/obsidian.png
    ... (one per theme)

Requirements:
    pip install pillow arabic-reshaper python-bidi
    Place Amiri-Regular.ttf and Lato-Regular.ttf in the fonts/ folder.
"""

import sys
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
FONT_DIR = BASE_DIR / "fonts"
OUT_DIR = BASE_DIR / "previews"
OUT_DIR.mkdir(exist_ok=True)

# ─────────────────────────────────────────────────────────────
# AYAH  —  Quran 2:78
# ─────────────────────────────────────────────────────────────
AYAH = {
    "arabic": "وَمِنْهُمْ أُمِّيُّونَ لَا يَعْلَمُونَ الْكِتَابَ إِلَّا أَمَانِيَّ وَإِنْ هُمْ إِلَّا يَظُنُّونَ",
    "translation": "And among them are the unlettered who do not know the Scripture except in wishful thinking, but they are only assuming.",
    "surah_name": "Al-Baqarah",
    "ayah_number": 78,
}


# ─────────────────────────────────────────────────────────────
# THEMES
# ─────────────────────────────────────────────────────────────
def _build_theme(name, bg, arabic, translation, reference, decorative):
    """
    Convert the user-facing flat theme dict into the internal format
    the renderer expects (bg, bg2, arabic, translation, reference,
    decorative, vignette, vignette_color).

    bg2 is derived by slightly darkening/lightening the background.
    vignette strength and color are inferred from whether the bg is dark or light.
    """

    def hex_to_rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))

    def rgb_to_hex(r, g, b):
        return f"#{r:02x}{g:02x}{b:02x}"

    r, g, b = hex_to_rgb(bg)
    brightness = (r * 299 + g * 587 + b * 114) / 1000  # perceptual luminance

    if brightness < 128:
        # Dark background: bg2 is slightly lighter for a subtle gradient
        dr = min(255, r + 12)
        dg = min(255, g + 12)
        db = min(255, b + 12)
        vignette = 0.28
        vignette_color = (0, 0, 0)
    else:
        # Light background: bg2 is slightly darker/warmer
        dr = max(0, r - 15)
        dg = max(0, g - 15)
        db = max(0, b - 18)
        vignette = 0.12
        # Vignette color leans warm for light themes
        vignette_color = (max(0, r - 60), max(0, g - 70), max(0, b - 80))

    return {
        "name": name,
        "bg": bg,
        "bg2": rgb_to_hex(dr, dg, db),
        "arabic": arabic,
        "translation": translation,
        "reference": reference,
        "decorative": decorative,
        "vignette": vignette,
        "vignette_color": vignette_color,
    }


THEMES = {
    "midnight_blue": _build_theme(
        name="Midnight Blue",
        bg="#11161e",
        arabic="#e8d5b7",
        translation="#c8b99a",
        reference="#7a6a55",
        decorative="#7a6a55",
    ),
    "obsidian": _build_theme(
        name="Obsidian",
        bg="#000000",
        arabic="#ffffff",
        translation="#cccccc",
        reference="#888888",
        decorative="#555555",
    ),
    "charcoal_gold": _build_theme(
        name="Charcoal & Gold",
        bg="#1c1c1e",
        arabic="#d4a843",
        translation="#c8a96e",
        reference="#7a6535",
        decorative="#7a6535",
    ),
    "parchment": _build_theme(
        name="Parchment",
        bg="#e0d3bd",
        arabic="#2c1810",
        translation="#4a3020",
        reference="#8a6040",
        decorative="#8a6040",
    ),
    "slate": _build_theme(
        name="Slate",
        bg="#1d2230",
        arabic="#e2e8f0",
        translation="#94a3b8",
        reference="#4a5568",
        decorative="#4a5568",
    ),
    "forest": _build_theme(
        name="Forest",
        bg="#0E1E0E",
        arabic="#c8e6c9",
        translation="#a5d6a7",
        reference="#4a7a4a",
        decorative="#4a7a4a",
    ),
    "desert": _build_theme(
        name="Desert Sand",
        bg="#442A10",
        arabic="#dbc484",
        translation="#a38e59",
        reference="#bb8c5b",
        decorative="#AC7743",
    ),
    "ivory": _build_theme(
        name="Ivory Minimal",
        bg="#ffffa9",
        arabic="#1b1b1a",
        translation="#2f2f2f",
        reference="#7A7979",
        decorative="#878787",
    ),
    "deep_teal": _build_theme(
        name="Deep Teal",
        bg="#0E1A2C",
        arabic="#abece6",
        translation="#7cccc4",
        reference="#2d847c",
        decorative="#539d97",
    ),
    "rose_noir": _build_theme(
        name="Rose Noir",
        bg="#210f15",
        arabic="#f8c8d0",
        translation="#e8a0b0",
        reference="#7a3545",
        decorative="#7a3545",
    ),
}


# ─────────────────────────────────────────────────────────────
# FONT LOADING
# ─────────────────────────────────────────────────────────────
def find_font(filename: str, size: int) -> ImageFont.FreeTypeFont:
    """
    Look in fonts/ folder first.
    Falls back to DejaVuSans if not found (for preview purposes).
    """
    candidates = [
        FONT_DIR / filename,
        # Common system locations — just in case
        Path("C:/Windows/Fonts") / filename,
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    ]
    for path in candidates:
        if path.exists():
            try:
                font = ImageFont.truetype(str(path), size)
                if path.name == filename:
                    pass  # exact match
                else:
                    print(
                        f"    ⚠  '{filename}' not found — using fallback. "
                        f"Place it in fonts/ for best results."
                    )
                return font
            except Exception:
                continue
    print(f"    ⚠  No font found for '{filename}' — using PIL default.")
    return ImageFont.load_default()


# ─────────────────────────────────────────────────────────────
# ARABIC RESHAPER  (harakah preserved)
# ─────────────────────────────────────────────────────────────
_reshaper = arabic_reshaper.ArabicReshaper(
    configuration={
        "delete_harakat": False,
        "support_ligatures": True,
    }
)


def reshape(text: str) -> str:
    return get_display(_reshaper.reshape(text))


# ─────────────────────────────────────────────────────────────
# LAYOUT HELPERS
# ─────────────────────────────────────────────────────────────
def measure(draw: ImageDraw.ImageDraw, text: str, font) -> tuple:
    bb = draw.textbbox((0, 0), text, font=font)
    return bb[2] - bb[0], bb[3] - bb[1]


def wrap_arabic(text: str, font, draw, max_w: int) -> list:
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


def wrap_latin(text: str, font, draw, max_w: int) -> list:
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


def hex_to_rgb(h: str) -> tuple:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


# ─────────────────────────────────────────────────────────────
# BACKGROUND  —  radial gradient + vignette
# ─────────────────────────────────────────────────────────────
def make_background(W: int, H: int, theme: dict) -> Image.Image:
    """
    Creates a rich background:
    - Subtle linear gradient from bg → bg2
    - Soft radial vignette at edges for depth
    """
    import struct

    bg1 = hex_to_rgb(theme["bg"])
    bg2 = hex_to_rgb(theme["bg2"])
    vc = theme["vignette_color"]
    vs = theme["vignette"]

    # Build pixel array with gradient top→bottom
    try:
        import numpy as np

        arr = np.zeros((H, W, 3), dtype=float)
        for c in range(3):
            top = bg1[c]
            bot = bg2[c]
            gradient = np.linspace(top, bot, H)[:, np.newaxis]
            arr[:, :, c] = np.broadcast_to(gradient, (H, W))

        # Radial vignette
        cx, cy = W / 2, H / 2
        Y, X = np.ogrid[:H, :W]
        dist = np.sqrt(((X - cx) / cx) ** 2 + ((Y - cy) / cy) ** 2)
        dist = np.clip(dist, 0, 1)
        # Smooth curve: light in center, darker at edges
        vig = 1 - vs * (dist**1.6)
        vig = np.clip(vig, 0, 1)[:, :, np.newaxis]

        # Blend toward vignette color at edges
        vc_arr = np.array(vc, dtype=float)
        arr = arr * vig + vc_arr * (1 - vig)
        arr = np.clip(arr, 0, 255).astype(np.uint8)
        return Image.fromarray(arr, "RGB")

    except ImportError:
        # numpy not available — plain solid color
        return Image.new("RGB", (W, H), theme["bg"])


# ─────────────────────────────────────────────────────────────
# DECORATIVE ELEMENTS
# ─────────────────────────────────────────────────────────────
def draw_separator(draw, W: int, cy: int, color: str, line_w_ratio=0.18):
    """Thin horizontal line with a centered diamond."""
    lw = int(W * line_w_ratio)
    cx = W // 2
    rgb = hex_to_rgb(color)

    # Faded line: draw segments getting lighter toward center
    steps = 60
    for i in range(steps):
        t = i / steps
        alpha = int(255 * (0.15 + 0.85 * t))  # fade in from edges
        seg_w = lw // steps
        x0 = cx - lw + i * seg_w * 2 // 1
        x1 = x0 + seg_w
        # Left half
        xl0 = cx - lw + i * (lw // steps)
        xl1 = xl0 + (lw // steps)
        # Right half
        xr0 = cx + lw - (i + 1) * (lw // steps)
        xr1 = xr0 + (lw // steps)
        c = tuple(int(v * alpha / 255) for v in rgb)
        draw.line([(xl0, cy), (xl1, cy)], fill=c, width=1)
        draw.line([(xr0, cy), (xr1, cy)], fill=c, width=1)

    # Solid center line
    draw.line([(cx - 30, cy), (cx + 30, cy)], fill=color, width=1)

    # Diamond
    ds = 5
    draw.polygon(
        [(cx, cy - ds), (cx + ds, cy), (cx, cy + ds), (cx - ds, cy)],
        fill=color,
    )


def draw_corners(draw, W: int, H: int, px: int, py: int, color: str):
    """Elegant L-shaped corner marks."""
    length = min(px, py) // 2
    thick = 2
    segs = [
        [(px, py + length), (px, py), (px + length, py)],
        [(W - px - length, py), (W - px, py), (W - px, py + length)],
        [(px, H - py - length), (px, H - py), (px + length, H - py)],
        [(W - px - length, H - py), (W - px, H - py), (W - px, H - py - length)],
    ]
    for pts in segs:
        draw.line(pts, fill=color, width=thick)


def draw_subtle_border(draw, W: int, H: int, color: str, inset: int = 24):
    """Very faint full rectangle border just inside the edge."""
    rgb = hex_to_rgb(color)
    # Draw at low opacity by blending — simulate with a light color
    faint = (
        tuple(max(0, v - 180) for v in rgb)
        if sum(rgb) > 300
        else tuple(min(255, v + 30) for v in rgb)
    )
    draw.rectangle(
        [inset, inset, W - inset, H - inset],
        outline=faint,
        width=1,
    )


# ─────────────────────────────────────────────────────────────
# CORE RENDERER
# ─────────────────────────────────────────────────────────────
def render(ayah: dict, theme: dict, W: int = 1920, H: int = 1080) -> Image.Image:
    # ── Fonts (resolution-relative sizes) ──────────────────────
    sz_ar = max(32, int(H * 0.056))  # ~60px at 1080p
    sz_tr = max(18, int(H * 0.030))  # ~32px
    sz_ref = max(14, int(H * 0.023))  # ~25px

    font_ar = find_font("Amiri-Regular.ttf", sz_ar)
    font_tr = find_font("Lato-Regular.ttf", sz_tr)
    font_ref = find_font("Lato-Regular.ttf", sz_ref)

    # ── Background ─────────────────────────────────────────────
    img = make_background(W, H, theme)
    draw = ImageDraw.Draw(img)

    # ── Layout constants ───────────────────────────────────────
    pad_x = int(W * 0.11)  # 11% side margins = 78% usable width
    pad_y = int(H * 0.10)
    max_tw = W - 2 * pad_x

    # ── Text preparation ───────────────────────────────────────
    ar_lines = wrap_arabic(ayah["arabic"], font_ar, draw, max_tw)
    tr_lines = wrap_latin(ayah["translation"], font_tr, draw, max_tw)
    ref_text = f"— {ayah['surah_name']},  Ayah {ayah['ayah_number']}"

    # ── Block height calculation ───────────────────────────────
    def block_h(lines, font, gap_ratio):
        if not lines:
            return 0
        _, lh = measure(draw, "Agالله", font)
        return len(lines) * lh + max(0, len(lines) - 1) * int(lh * gap_ratio)

    gap_ar = 0.25
    gap_tr = 0.45
    section = int(H * 0.042)  # vertical gap between sections
    deco_h = int(H * 0.045)  # separator zone height

    h_ar = block_h(ar_lines, font_ar, gap_ar)
    h_tr = block_h(tr_lines, font_tr, gap_tr)
    h_ref = measure(draw, ref_text, font_ref)[1]

    total = h_ar + section + deco_h + section + h_tr + section + h_ref
    y = max(pad_y, (H - total) // 2)

    # ── Arabic text ────────────────────────────────────────────
    _, lh_ar = measure(draw, "Agالله", font_ar)
    gap_ar_px = int(lh_ar * gap_ar)
    for line in ar_lines:
        lw, _ = measure(draw, line, font_ar)
        draw.text(((W - lw) // 2, y), line, font=font_ar, fill=theme["arabic"])
        y += lh_ar + gap_ar_px

    # ── Separator ─────────────────────────────────────────────
    y += section
    draw_separator(draw, W, y + deco_h // 2, theme["decorative"])
    y += deco_h

    # ── Translation ────────────────────────────────────────────
    y += section
    _, lh_tr = measure(draw, "Ag", font_tr)
    gap_tr_px = int(lh_tr * gap_tr)
    for line in tr_lines:
        lw, _ = measure(draw, line, font_tr)
        draw.text(((W - lw) // 2, y), line, font=font_tr, fill=theme["translation"])
        y += lh_tr + gap_tr_px

    # ── Reference ─────────────────────────────────────────────
    y += section
    rw, _ = measure(draw, ref_text, font_ref)
    draw.text(((W - rw) // 2, y), ref_text, font=font_ref, fill=theme["reference"])

    # ── Decorative frame elements ──────────────────────────────
    draw_corners(draw, W, H, pad_x, pad_y, theme["decorative"])
    draw_subtle_border(draw, W, H, theme["decorative"])

    return img


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
def main():
    print()
    print("═" * 55)
    print("  DeenBG — Theme Preview Generator")
    print("  Ayah: Al-Baqarah 2:78")
    print("═" * 55)

    # Check fonts
    amiri = FONT_DIR / "Amiri-Regular.ttf"
    lato = FONT_DIR / "Lato-Regular.ttf"
    if not amiri.exists():
        print(f"\n  ⚠  Amiri-Regular.ttf not found in fonts/")
        print(f"     Download: https://www.amirifont.org")
        print(f"     Arabic will render with fallback font.\n")
    if not lato.exists():
        print(f"\n  ⚠  Lato-Regular.ttf not found in fonts/")
        print(f"     Download: https://fonts.google.com/specimen/Lato")
        print(f"     Translation will render with fallback font.\n")

    print(f"\n  Output folder: {OUT_DIR}\n")

    failed = []
    for theme_id, theme in THEMES.items():
        try:
            print(f"  Rendering  {theme['name']:<22}", end=" ... ", flush=True)
            img = render(AYAH, theme, W=1920, H=1080)
            path = OUT_DIR / f"{theme_id}.png"
            img.save(str(path), "PNG", optimize=True)
            kb = path.stat().st_size // 1024
            print(f"✓  saved ({kb} KB)")
        except Exception as e:
            print(f"✗  ERROR: {e}")
            failed.append(theme_id)

    print()
    if failed:
        print(f"  ✗ Failed themes: {', '.join(failed)}")
    else:
        print(f"  ✓ All {len(THEMES)} themes generated successfully.")

    print(f"  ✓ Files in: {OUT_DIR}")
    print("═" * 55)
    print()


if __name__ == "__main__":
    main()
