"""
DeenBG — Setup Wizard
======================
Run once to configure your theme, translation, font sizes, and behavior.
Saves settings to config.json.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_FILE = BASE_DIR / "config.json"

THEMES = {
    "1": ("midnight_blue", "Midnight Blue       — Dark navy, warm cream text"),
    "2": ("obsidian", "Obsidian            — Pure black, white text (elegant)"),
    "3": ("charcoal_gold", "Charcoal & Gold     — Dark charcoal, golden Arabic"),
    "4": ("parchment", "Parchment           — Warm beige, dark ink (manuscript feel)"),
    "5": ("slate", "Slate               — Blue-grey, soft white text"),
    "6": ("forest", "Forest              — Deep green, mint text"),
    "7": ("desert", "Desert Sand         — Warm brown, golden text"),
    "8": ("ivory", "Ivory Minimal       — Off-white, dark text (clean)"),
    "9": ("deep_teal", "Deep Teal           — Dark teal, soft cyan text"),
    "10": ("rose_noir", "Rose Noir           — Dark maroon, rose text (elegant)"),
}

TRANSLATIONS = {
    "1": ("en.sahih", "Saheeh International  (most accurate, recommended)"),
    "2": ("en.pickthall", "Pickthall              (classic, literary)"),
    "3": ("en.yusufali", "Yusuf Ali              (widely known)"),
    "4": ("en.asad", "Muhammad Asad          (modern, explanatory)"),
}


def _ask(prompt: str, default: str = "") -> str:
    val = input(prompt).strip()
    return val if val else default


def _ask_int(prompt: str, default: int, lo: int, hi: int) -> int:
    while True:
        raw = _ask(prompt, str(default))
        try:
            v = int(raw)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        print(f"  Please enter a number between {lo} and {hi}.")


def _ask_float(prompt: str, default: float, lo: float, hi: float) -> float:
    while True:
        raw = _ask(prompt, str(default))
        try:
            v = float(raw)
            if lo <= v <= hi:
                return round(v, 2)
        except ValueError:
            pass
        print()
        print(f"  Please enter a number between {lo} and {hi} (e.g. 0.9, 1.2).")


def run():
    print("\n" + "═" * 58)
    print("                  DeenBG — Setup Wizard")
    print("═" * 58)
    print("  Press Enter to accept [default] values.\n")

    # ── Translation ───────────────────────────────────────────
    print("  Choose English translation:")
    for k, (_, label) in TRANSLATIONS.items():
        print(f"    {k}. {label}")
    tc = _ask("\n  Your choice [1]: ", "1")
    if tc not in TRANSLATIONS:
        tc = "1"
    translation_id = TRANSLATIONS[tc][0]
    print(f"  ✓ {TRANSLATIONS[tc][1]}\n")

    # ── Theme ─────────────────────────────────────────────────
    print("  Choose wallpaper theme:")
    for k, (_, label) in THEMES.items():
        print(f"    {k:>2}. {label}")
    thc = _ask("\n  Your choice [1]: ", "1")
    if thc not in THEMES:
        thc = "1"
    theme_id = THEMES[thc][0]
    print(f"  ✓ {THEMES[thc][1]}\n")

    # ── Font sizes ────────────────────────────────────────────
    print("  Font scale (1.0 = default, 0.8 = smaller, 1.3 = larger)")
    scale_ar = _ask_float("  Arabic font scale [1.0]: ", 1.0, 0.4, 3.0)
    scale_tr = _ask_float("  Translation font scale [1.0]: ", 1.0, 0.4, 3.0)
    print()

    # ── Behavior ──────────────────────────────────────────────
    print("  ─" * 29)
    avoid = _ask("  Avoid repeating ayahs? (y/n) [y]: ", "y").lower() == "y"
    save = _ask("  Save wallpaper PNG files? (y/n) [y]: ", "y").lower() == "y"
    max_w = _ask_int("  Max wallpapers to keep [30]: ", 30, 1, 500) if save else 30

    # ── Build & save ──────────────────────────────────────────
    config = {
        "api": {
            "translation_edition": translation_id,
        },
        "design": {
            "theme": theme_id,
            "font_arabic": "Amiri-Regular.ttf",
            "font_latin": "Lato-Regular.ttf",
            "decorative_line": True,
            "font_scale_arabic": scale_ar,
            "font_scale_translation": scale_tr,
        },
        "behavior": {
            "avoid_repeats": avoid,
            "max_cache_size": 6236,
            "save_wallpapers": save,
            "max_saved_wallpapers": max_w,
        },
    }

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print("\n" + "═" * 58)
    print(f"  ✓ Config saved to config.json")
    print(f"  Theme            : {THEMES[thc][1].split('—')[0].strip()}")
    print(f"  Translation      : {TRANSLATIONS[tc][1].split('(')[0].strip()}")
    print(f"  Arabic scale     : {scale_ar}x")
    print(f"  Translation scale: {scale_tr}x")
    print(f"  Avoid repeats    : {'Yes' if avoid else 'No'}")
    print()
    print("  To change font size later, edit config.json:")
    print('    "font_scale_arabic": 1.2')
    print('    "font_scale_translation": 1.0')
    print()
    print("  Next: run  python wallpaper_generator.py")
    print("═" * 58 + "\n")


if __name__ == "__main__":
    run()
