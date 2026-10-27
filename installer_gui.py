"""
DeenBG - Standalone Installer & Wallpaper Generator
====================================================
Single-file application compiled to a self-contained .exe via PyInstaller.
No Python or dependencies required on the target machine.

Run modes
---------
  DeenBG-Setup.exe             -> Interactive installer GUI
  DeenBG-Setup.exe --generate  -> Silent wallpaper generation (Task Scheduler)

Author  : CyberMajeed
License : MIT
"""
from __future__ import annotations
import sys, os, json, shutil, subprocess, threading, ctypes, logging, random, tempfile, time
from datetime import datetime
from pathlib import Path

# Configure Windows DLL & Tcl path if needed
if sys.platform == "win32" and not getattr(sys, "frozen", False):
    for _p in [
        Path(sys.prefix) / "Lib" / "site-packages" / "tcl",
        Path.home() / "AppData" / "Roaming" / "Python" / f"Python{sys.version_info.major}{sys.version_info.minor}" / "site-packages" / "tcl",
        Path.home() / "AppData" / "Roaming" / "Python" / "Python314" / "site-packages" / "tcl",
        Path(sys.prefix) / "tcl",
    ]:
        if _p.exists() and (_p / "tcl8.6" / "init.tcl").exists():
            try:
                os.add_dll_directory(str(_p.parent))
            except Exception:
                pass
            os.environ["TCL_LIBRARY"] = str(_p / "tcl8.6")
            os.environ["TK_LIBRARY"] = str(_p / "tk8.6")
            break

try:
    import tkinter as tk
    from tkinter import ttk, filedialog
    from PIL import ImageTk
    HAS_TK = True
except Exception:
    tk = None
    ttk = None
    filedialog = None
    ImageTk = None
    HAS_TK = False

from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

# ============================================================
# CONSTANTS
# ============================================================
APP_NAME  = "DeenBG"
APP_VER   = "2.0"
TASK_NAME = "DeenBG"
EXE_NAME  = "deenbg.exe"
DEFAULT_INSTALL = Path.home() / "AppData" / "Local" / "DeenBG"

UI = {
    "bg": "#c7ffda", "panel": "#b4f5cb", "card": "#ffffff",
    "border": "#8cdbb0", "accent": "#085229", "accent_dim": "#4e946c",
    "accent_light": "#0e6635", "text": "#001c0a", "muted": "#114d2a",
    "success": "#085229", "error": "#b91c1c", "btn_bg": "#b4f5cb",
    "btn_hover": "#a2e8bc", "btn_text_pri": "#ffffff",
}

THEMES = {
    "midnight_blue": {"name":"Midnight Blue",  "bg":"#11161e","ar":"#e8d5b7","tr":"#c8b99a","ref":"#7a6a55","dec":"#7a6a55"},
    "obsidian":      {"name":"Obsidian",        "bg":"#000000","ar":"#ffffff","tr":"#cccccc","ref":"#888888","dec":"#555555"},
    "charcoal_gold": {"name":"Charcoal & Gold", "bg":"#1c1c1e","ar":"#d4a843","tr":"#c8a96e","ref":"#7a6535","dec":"#7a6535"},
    "parchment":     {"name":"Parchment",       "bg":"#e0d3bd","ar":"#2c1810","tr":"#4a3020","ref":"#8a6040","dec":"#8a6040"},
    "slate":         {"name":"Slate",            "bg":"#1d2230","ar":"#e2e8f0","tr":"#94a3b8","ref":"#4a5568","dec":"#4a5568"},
    "forest":        {"name":"Forest",           "bg":"#0E1E0E","ar":"#c8e6c9","tr":"#a5d6a7","ref":"#4a7a4a","dec":"#4a7a4a"},
    "desert":        {"name":"Desert Sand",      "bg":"#442A10","ar":"#dbc484","tr":"#a38e59","ref":"#bb8c5b","dec":"#AC7743"},
    "ivory":         {"name":"Ivory Minimal",    "bg":"#ffffa9","ar":"#1b1b1a","tr":"#2f2f2f","ref":"#7A7979","dec":"#878787"},
    "deep_teal":     {"name":"Deep Teal",        "bg":"#0E1A2C","ar":"#abece6","tr":"#7cccc4","ref":"#2d847c","dec":"#539d97"},
    "rose_noir":     {"name":"Rose Noir",        "bg":"#210f15","ar":"#f8c8d0","tr":"#e8a0b0","ref":"#7a3545","dec":"#7a3545"},
}

TRANSLATIONS = {
    "en.sahih":     ("Saheeh International",  "Most accurate, recommended for beginners"),
    "en.pickthall": ("Pickthall",             "Classic literary translation, 1930"),
    "en.yusufali":  ("Yusuf Ali",             "Widely used, includes commentary notes"),
    "en.asad":      ("Muhammad Asad",         "Modern, explanatory, scholarly"),
}

PREVIEW_AYAH = {
    "arabic":        "\u0642\u064f\u0644\u0652 \u0647\u064f\u0648\u064e \u0627\u0644\u0644\u0651\u064e\u0647\u064f \u0623\u064e\u062d\u064e\u062f\u064c",
    "translation":   "Say, He is Allah, the One.",
    "surah_name":    "Al-Ikhlas",
    "ayah_in_surah": 1,
}

DEFAULT_CONFIG = {
    "api":    {"translation_edition": "en.sahih"},
    "design": {"theme":"midnight_blue","font_arabic":"Amiri-Regular.ttf","font_latin":"Lato-Regular.ttf",
               "decorative_line":True,"font_scale_arabic":1.0,"font_scale_translation":1.0},
    "behavior": {"avoid_repeats":True,"max_cache_size":6236,"save_wallpapers":True,"max_saved_wallpapers":40},
}

SURAH_META = [
    ("Al-Fatihah",7),("Al-Baqarah",286),("Ali 'Imran",200),("An-Nisa",176),
    ("Al-Ma'idah",120),("Al-An'am",165),("Al-A'raf",206),("Al-Anfal",75),
    ("At-Tawbah",129),("Yunus",109),("Hud",123),("Yusuf",111),("Ar-Ra'd",43),
    ("Ibrahim",52),("Al-Hijr",99),("An-Nahl",128),("Al-Isra",111),("Al-Kahf",110),
    ("Maryam",98),("Ta-Ha",135),("Al-Anbya",112),("Al-Hajj",78),("Al-Mu'minun",118),
    ("An-Nur",64),("Al-Furqan",77),("Ash-Shu'ara",227),("An-Naml",93),("Al-Qasas",88),
    ("Al-'Ankabut",69),("Ar-Rum",60),("Luqman",34),("As-Sajdah",30),("Al-Ahzab",73),
    ("Saba",54),("Fatir",45),("Ya-Sin",83),("As-Saffat",182),("Sad",88),
    ("Az-Zumar",75),("Ghafir",85),("Fussilat",54),("Ash-Shuraa",53),("Az-Zukhruf",89),
    ("Ad-Dukhan",59),("Al-Jathiyah",37),("Al-Ahqaf",35),("Muhammad",38),("Al-Fath",29),
    ("Al-Hujurat",18),("Qaf",45),("Adh-Dhariyat",60),("At-Tur",49),("An-Najm",62),
    ("Al-Qamar",55),("Ar-Rahman",78),("Al-Waqi'ah",96),("Al-Hadid",29),("Al-Mujadila",22),
    ("Al-Hashr",24),("Al-Mumtahanah",13),("As-Saf",14),("Al-Jumu'ah",11),("Al-Munafiqun",11),
    ("At-Taghabun",18),("At-Talaq",12),("At-Tahrim",12),("Al-Mulk",30),("Al-Qalam",52),
    ("Al-Haqqah",52),("Al-Ma'arij",44),("Nuh",28),("Al-Jinn",28),("Al-Muzzammil",20),
    ("Al-Muddaththir",56),("Al-Qiyamah",40),("Al-Insan",31),("Al-Mursalat",50),
    ("An-Naba",40),("An-Nazi'at",46),("'Abasa",42),("At-Takwir",29),("Al-Infitar",19),
    ("Al-Mutaffifin",36),("Al-Inshiqaq",25),("Al-Buruj",22),("At-Tariq",17),("Al-A'la",19),
    ("Al-Ghashiyah",26),("Al-Fajr",30),("Al-Balad",20),("Ash-Shams",15),("Al-Layl",21),
    ("Ad-Duha",11),("Ash-Sharh",8),("At-Tin",8),("Al-'Alaq",19),("Al-Qadr",5),
    ("Al-Bayyinah",8),("Az-Zalzalah",8),("Al-'Adiyat",11),("Al-Qari'ah",11),
    ("At-Takathur",8),("Al-'Asr",3),("Al-Humazah",9),("Al-Fil",5),("Quraysh",4),
    ("Al-Ma'un",7),("Al-Kawthar",3),("Al-Kafirun",6),("An-Nasr",3),("Al-Masad",5),
    ("Al-Ikhlas",4),("Al-Falaq",5),("An-Nas",6),
]

# ============================================================
# RESOURCE PATH
# ============================================================
def res(relative):
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
    return base / relative

# ============================================================
# TEXT / ARABIC UTILITIES
# ============================================================
_reshaper = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat":False,"support_ligatures":True})

def reshape(text):
    return get_display(_reshaper.reshape(text))

def load_font(filename, size, font_dir=None):
    dirs = [d for d in [font_dir, res("fonts")] if d is not None]
    for d in dirs:
        p = Path(d) / filename
        if p.exists():
            try: return ImageFont.truetype(str(p), size)
            except Exception: pass
    return ImageFont.load_default()

def _lh(f):
    a,d = f.getmetrics(); return a+d

def _top(f):
    img=Image.new("RGB",(10,10)); return ImageDraw.Draw(img).textbbox((0,0),"A",font=f)[1]

def _tw(f,t):
    img=Image.new("RGB",(10,10)); return ImageDraw.Draw(img).textlength(t,font=f)

def _wrap_ar(text,font,mw):
    words,raw,cur=text.split(),[],[]
    for w in words:
        test=reshape(" ".join(cur+[w]))
        if _tw(font,test)<=mw: cur.append(w)
        else:
            if cur: raw.append(" ".join(cur))
            cur=[w]
    if cur: raw.append(" ".join(cur))
    return [reshape(ln) for ln in raw]

def _wrap_lat(text,font,mw):
    words,lines,line=text.split(),[],""
    for w in words:
        test=(line+" "+w).strip()
        if _tw(font,test)<=mw: line=test
        else:
            if line: lines.append(line)
            line=w
    if line: lines.append(line)
    return lines

def _draw_block(draw,lines,font,color,W,y,gap):
    lh=_lh(font); top=_top(font)
    for line in lines:
        lw=_tw(font,line); draw.text((int((W-lw)/2),y-top),line,font=font,fill=color); y+=lh+gap
    return y

def _bh(lines,font,gap):
    if not lines: return 0
    return len(lines)*_lh(font)+max(0,len(lines)-1)*gap

# ============================================================
# THEME PREVIEW GENERATOR
# ============================================================
def generate_theme_preview(theme_key, W=356, H=200, font_dir=None):
    t=THEMES[theme_key]; img=Image.new("RGB",(W,H),t["bg"]); draw=ImageDraw.Draw(img)
    px,py=int(W*0.08),int(H*0.08); mw=W-2*px
    fa=load_font("Amiri-Regular.ttf",max(12,int(H*0.095)),font_dir)
    ft=load_font("Lato-Regular.ttf",max(7,int(H*0.052)),font_dir)
    fr=load_font("Lato-Regular.ttf",max(6,int(H*0.042)),font_dir)
    arl=_wrap_ar(PREVIEW_AYAH["arabic"],fa,mw); trl=_wrap_lat(PREVIEW_AYAH["translation"],ft,mw)
    ref=f"— {PREVIEW_AYAH['surah_name']}, Ayah {PREVIEW_AYAH['ayah_in_surah']}"
    gar=max(1,int(_lh(fa)*0.18)); gtr=max(1,int(_lh(ft)*0.28)); sec=max(4,int(H*0.042)); dh=max(4,int(H*0.04))
    total=_bh(arl,fa,gar)+sec+dh+sec+_bh(trl,ft,gtr)+sec+_lh(fr)
    y=max(py,(H-total)//2); y=_draw_block(draw,arl,fa,t["ar"],W,y,gar); y+=sec
    cy=y+dh//2; lw=int(W*0.18); cx=W//2
    draw.line([(cx-lw,cy),(cx+lw,cy)],fill=t["dec"],width=1); ds=3
    draw.polygon([(cx,cy-ds),(cx+ds,cy),(cx,cy+ds),(cx-ds,cy)],fill=t["dec"]); y+=dh+sec
    y=_draw_block(draw,trl,ft,t["tr"],W,y,gtr); y+=sec
    rw=_tw(fr,ref); draw.text((int((W-rw)/2),y-_top(fr)),ref,font=fr,fill=t["ref"])
    ln=max(4,min(px,py)//2)
    for pts in [[(px,py+ln),(px,py),(px+ln,py)],[(W-px-ln,py),(W-px,py),(W-px,py+ln)],
                [(px,H-py-ln),(px,H-py),(px+ln,H-py)],[(W-px-ln,H-py),(W-px,H-py),(W-px,H-py-ln)]]:
        draw.line(pts,fill=t["dec"],width=1)
    return img

# ============================================================
# WALLPAPER GENERATION  (--generate mode)
# ============================================================
def _merge(base,override):
    r=dict(base)
    for k,v in override.items():
        r[k]=_merge(r[k],v) if isinstance(r.get(k),dict) and isinstance(v,dict) else v
    return r

def run_generate_mode():
    idir=Path(sys.executable).parent if getattr(sys,"frozen",False) else Path(__file__).parent
    ld=idir/"logs"; ld.mkdir(parents=True,exist_ok=True)
    logging.basicConfig(level=logging.INFO,format="%(asctime)s [%(levelname)s] %(message)s",
                        handlers=[logging.FileHandler(ld/"deenbg.log",encoding="utf-8")])
    log=logging.getLogger(__name__)
    for d in ["wallpapers","cache","data"]: (idir/d).mkdir(exist_ok=True)
    try:
        with open(idir/"config.json",encoding="utf-8") as f: cfg=_merge(DEFAULT_CONFIG,json.load(f))
    except Exception: cfg=DEFAULT_CONFIG
    dbp=idir/"data"/"quran.json"
    if not dbp.exists(): dbp=res("data")/"quran.json"
    if not dbp.exists(): log.critical("Quran DB not found: %s",dbp); sys.exit(1)
    with open(dbp,encoding="utf-8") as f: db=json.load(f)
    log.info("DB: %d ayahs",len(db))
    cp=idir/"cache"/"seen_ayahs.json"; seen=set()
    if cfg["behavior"]["avoid_repeats"] and cp.exists():
        try:
            with open(cp,encoding="utf-8") as f: seen=set(json.load(f))
        except Exception: pass
    if cfg["behavior"]["avoid_repeats"] and len(seen)<len(db):
        ayah=random.choice([a for a in db if a["number"] not in seen])
    else: ayah=random.choice(db)
    log.info("Ayah: %s %s (#%s)",ayah["surah_name"],ayah["ayah_in_surah"],ayah["number"])
    try:
        u=ctypes.windll.user32; u.SetProcessDPIAware()
        W,H=u.GetSystemMetrics(0),u.GetSystemMetrics(1)
        if W<=0 or H<=0: W,H=1920,1080
    except Exception: W,H=1920,1080
    log.info("Screen: %dx%d",W,H)
    fd=idir/"fonts"
    if not fd.exists(): fd=res("fonts")
    dc=cfg["design"]; t=THEMES.get(dc.get("theme","midnight_blue"),THEMES["midnight_blue"])
    sar=float(dc.get("font_scale_arabic",1.0)); str_=float(dc.get("font_scale_translation",1.0))
    sza=max(24,int(H*0.052*sar)); szt=max(14,int(H*0.027*str_)); szr=max(12,int(H*0.022*str_))
    fa=load_font(dc["font_arabic"],sza,fd); ft=load_font(dc["font_latin"],szt,fd); fr=load_font(dc["font_latin"],szr,fd)
    log.info("Fonts: ar=%dpx tr=%dpx ref=%dpx",sza,szt,szr)
    img=Image.new("RGB",(W,H),t["bg"]); draw=ImageDraw.Draw(img)
    px=int(W*0.10); py=int(H*0.10); mw=W-2*px
    arl=_wrap_ar(ayah["arabic"],fa,mw); trl=_wrap_lat(ayah["translation"],ft,mw)
    ref=f"— {ayah['surah_name']},  Ayah {ayah['ayah_in_surah']}"
    gar=int(_lh(fa)*0.20); gtr=int(_lh(ft)*0.35); sec=int(H*0.040); dh=int(H*0.040)
    ud=dc.get("decorative_line",True)
    har=_bh(arl,fa,gar); htr=_bh(trl,ft,gtr)
    total=har+sec+(dh+sec if ud else 0)+htr+sec+_lh(fr)
    y=max(py,(H-total)//2); y=_draw_block(draw,arl,fa,t["ar"],W,y,gar); y+=sec
    if ud:
        cy=y+dh//2; lw=int(W*0.20); cx=W//2
        draw.line([(cx-lw,cy),(cx+lw,cy)],fill=t["dec"],width=1); ds=4
        draw.polygon([(cx,cy-ds),(cx+ds,cy),(cx,cy+ds),(cx-ds,cy)],fill=t["dec"]); y+=dh+sec
    y=_draw_block(draw,trl,ft,t["tr"],W,y,gtr); y+=sec
    rw=_tw(fr,ref); draw.text((int((W-rw)/2),y-_top(fr)),ref,font=fr,fill=t["ref"])
    ln=min(px,py)//3
    for pts in [[(px,py+ln),(px,py),(px+ln,py)],[(W-px-ln,py),(W-px,py),(W-px,py+ln)],
                [(px,H-py-ln),(px,H-py),(px+ln,H-py)],[(W-px-ln,H-py),(W-px,H-py),(W-px,H-py-ln)]]:
        draw.line(pts,fill=t["dec"],width=2)
    wpd=idir/"wallpapers"; wpd.mkdir(exist_ok=True)
    ts=datetime.now().strftime("%Y%m%d_%H%M%S"); out=wpd/f"ayah_{ayah['number']}_{ts}.png"
    img.save(str(out),"PNG",optimize=True); log.info("Saved: %s",out)
    files=sorted(wpd.glob("*.png"),key=lambda p:p.stat().st_mtime)
    ms=cfg["behavior"].get("max_saved_wallpapers",40)
    while len(files)>ms:
        try: files.pop(0).unlink()
        except Exception: break
    ok=ctypes.windll.user32.SystemParametersInfoW(0x0014,0,str(out.resolve()),3)
    log.info("Wallpaper set: %s","OK" if ok else "FAIL")
    if cfg["behavior"]["avoid_repeats"]:
        seen.add(ayah["number"]); sl=list(seen)
        if len(sl)>=cfg["behavior"]["max_cache_size"]: log.info("Cache reset"); sl=[]
        try:
            with open(cp,"w") as f: json.dump(sl,f)
        except Exception as e: log.warning("Cache err: %s",e)
    log.info("Done OK")

def run_uninstall_mode():
    try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try: ctypes.windll.user32.SetProcessDPIAware()
        except Exception: pass

    confirmed = False
    if any(arg in sys.argv for arg in ("--quiet", "--silent", "-y")):
        confirmed = True
    else:
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            confirmed = messagebox.askyesno(
                "Uninstall DeenBG",
                "Are you sure you want to completely uninstall DeenBG and remove all its components?",
                icon="warning"
            )
            root.destroy()
        except Exception:
            try:
                if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
                    ans = input("Are you sure you want to completely uninstall DeenBG? (y/n) [n]: ").strip().lower()
                    confirmed = (ans == "y")
                else:
                    confirmed = True
            except Exception:
                confirmed = True

    if not confirmed:
        sys.exit(0)

    # 1. Terminate running background deenbg processes
    try:
        subprocess.run(["taskkill", "/F", "/IM", EXE_NAME], capture_output=True)
        time.sleep(0.3)
    except Exception:
        pass

    # 2. Delete Task Scheduler tasks
    for tn in [TASK_NAME, "DeenBG Wallpaper"]:
        try:
            subprocess.run(["schtasks", "/Delete", "/TN", tn, "/F"], capture_output=True)
        except Exception:
            pass
        try:
            subprocess.run([
                "powershell.exe", "-WindowStyle", "Hidden", "-Command",
                f"Unregister-ScheduledTask -TaskName '{tn}' -Confirm:$false -ErrorAction SilentlyContinue"
            ], capture_output=True)
        except Exception:
            pass

    # 3. Delete Windows Startup registry key if present
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, TASK_NAME)
    except Exception:
        pass

    # 4. Delete Windows Startup folder script if present
    try:
        st = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "DeenBG.cmd"
        if st.exists():
            st.unlink()
    except Exception:
        pass

    # 5. Determine target install directories to remove
    target_dirs = set()
    if DEFAULT_INSTALL.exists():
        target_dirs.add(DEFAULT_INSTALL.resolve())

    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DeenBG") as k:
            loc, _ = winreg.QueryValueEx(k, "InstallLocation")
            if loc and Path(loc).exists():
                target_dirs.add(Path(loc).resolve())
    except Exception:
        pass

    cur_exe = Path(sys.executable).resolve()
    if cur_exe.parent.name.lower() == "deenbg":
        target_dirs.add(cur_exe.parent)

    # 6. Delete Control Panel Uninstall registry key
    try:
        import winreg
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DeenBG")
    except Exception:
        pass

    # 7. Delete installed files and directories
    for d in target_dirs:
        if not d.exists() or not d.is_dir():
            continue
        if d.name.lower() != "deenbg":
            continue
        # Synchronously remove non-locked files and subdirectories
        for item in list(d.iterdir()):
            try:
                if item.resolve() == cur_exe:
                    continue
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    try:
                        os.chmod(item, 0o777)
                    except Exception:
                        pass
                    item.unlink(missing_ok=True)
            except Exception:
                pass

        # Schedule delayed self-deletion for folder and running executable
        try:
            cmd = (
                f'timeout /t 2 /nobreak >nul & '
                f'taskkill /F /IM "{EXE_NAME}" >nul 2>&1 & '
                f'rmdir /s /q "{d}"'
            )
            subprocess.Popen(["cmd.exe", "/c", cmd], creationflags=0x08000000 | 0x00000008)
        except Exception:
            pass
        try:
            ps = (
                f"Start-Sleep -Seconds 2; "
                f"Stop-Process -Name '{Path(EXE_NAME).stem}' -Force -ErrorAction SilentlyContinue; "
                f"Remove-Item -LiteralPath '{d}' -Recurse -Force -ErrorAction SilentlyContinue"
            )
            subprocess.Popen(["powershell.exe", "-WindowStyle", "Hidden", "-Command", ps],
                             creationflags=0x08000000 | 0x00000008)
        except Exception:
            pass

    # 8. Notify user (unless quiet/silent)
    if not any(arg in sys.argv for arg in ("--quiet", "--silent")):
        try:
            import tkinter as tk
            from tkinter import messagebox
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("DeenBG", "DeenBG has been successfully uninstalled from your computer.")
            root.destroy()
        except Exception:
            print("DeenBG has been successfully uninstalled from your computer.")
    else:
        print("DeenBG has been successfully uninstalled from your computer.")
    sys.exit(0)

def _clean_install_dir(d: Path):
    if not d.exists():
        return
    try:
        subprocess.run(["taskkill", "/F", "/IM", EXE_NAME], capture_output=True)
        time.sleep(0.3)
    except Exception:
        pass
    cur_exe = Path(sys.executable).resolve()
    for item in list(d.iterdir()):
        try:
            if item.resolve() == cur_exe:
                continue
            if item.is_dir():
                shutil.rmtree(item, ignore_errors=True)
            else:
                try:
                    os.chmod(item, 0o777)
                except Exception:
                    pass
                item.unlink(missing_ok=True)
        except Exception:
            pass

# ============================================================
# INSTALLER GUI
# ============================================================
class InstallerApp:
    WIN_W,WIN_H=880,680
    STEPS=["Welcome","Install Folder","Choose Theme","Translation","Settings","Installing"]

    def __init__(self,root):
        self.root=root
        self.install_dir=tk.StringVar(value=str(DEFAULT_INSTALL))
        self.selected_theme=tk.StringVar(value="midnight_blue")
        self.selected_trans=tk.StringVar(value="en.sahih")
        self.scale_arabic=tk.DoubleVar(value=1.0)
        self.scale_translation=tk.DoubleVar(value=1.0)
        self.avoid_repeats=tk.BooleanVar(value=True)
        self.save_wallpapers=tk.BooleanVar(value=True)
        self.register_task=tk.BooleanVar(value=True)
        self.interval_var=tk.StringVar(value="0")
        self._pc={}; self._tf={}; self._ok=False
        self._setup_window(); self._setup_styles(); self._build_chrome(); self._show_page(0)

    def _setup_window(self):
        self.root.title(f"{APP_NAME} — Setup"); self.root.configure(bg=UI["bg"])
        self.root.resizable(False,False); self.root.update_idletasks()
        x=(self.root.winfo_screenwidth()-self.WIN_W)//2; y=(self.root.winfo_screenheight()-self.WIN_H)//2
        self.root.geometry(f"{self.WIN_W}x{self.WIN_H}+{x}+{y}")
        for ic in [res("docs/logo/icon.ico"), res("icon.ico")]:
            if ic.exists():
                try: self.root.iconbitmap(str(ic)); break
                except Exception: pass
        for ip in [res("docs/logo/icon_transparent.png"), res("docs/logo/icon.png")]:
            if ip.exists():
                try:
                    self._wicon = ImageTk.PhotoImage(Image.open(ip))
                    self.root.iconphoto(False, self._wicon)
                    break
                except Exception: pass

    def _setup_styles(self):
        s=ttk.Style(self.root); s.theme_use("clam")
        for f,bg in [("TFrame",UI["bg"]),("Card.TFrame",UI["card"]),("Panel.TFrame",UI["panel"])]:
            s.configure(f,background=bg)
        s.configure("TLabel",background=UI["bg"],foreground=UI["text"],font=("Segoe UI",10))
        s.configure("Sub.TLabel",background=UI["bg"],foreground=UI["muted"],font=("Segoe UI",10))
        s.configure("Card.TLabel",background=UI["card"],foreground=UI["text"],font=("Segoe UI",10))
        s.configure("Horizontal.TProgressbar",troughcolor=UI["card"],background=UI["accent"],
                    bordercolor=UI["border"],lightcolor=UI["accent"],darkcolor=UI["accent"],thickness=6)
        s.configure("TScrollbar",background=UI["panel"],troughcolor=UI["bg"],arrowcolor=UI["muted"])

    def _build_chrome(self):
        self.hdr=tk.Frame(self.root,bg=UI["panel"],height=68)
        self.hdr.pack(fill="x",side="top"); self.hdr.pack_propagate(False)
        lf=tk.Frame(self.hdr,bg=UI["panel"]); lf.pack(side="left",padx=24)
        tk.Label(lf,text="DeenBG",bg=UI["panel"],fg=UI["accent"],font=("Segoe UI",20,"bold")).pack(side="left")
        tk.Label(lf,text=f"  v{APP_VER}",bg=UI["panel"],fg=UI["muted"],font=("Segoe UI",10)).pack(side="left",pady=8)
        self.slbl=tk.Label(self.hdr,text="",bg=UI["panel"],fg=UI["muted"],font=("Segoe UI",9))
        self.slbl.pack(side="right",padx=24)
        self.df=tk.Frame(self.hdr,bg=UI["panel"]); self.df.pack(side="right",padx=12)
        self._dots=[]
        for _ in range(len(self.STEPS)):
            d=tk.Label(self.df,text="●",bg=UI["panel"],fg=UI["border"],font=("Segoe UI",7))
            d.pack(side="left",padx=2); self._dots.append(d)
        tk.Frame(self.root,bg=UI["border"],height=1).pack(fill="x")
        tk.Frame(self.root,bg=UI["border"],height=1).pack(fill="x",side="bottom")
        self.footer=tk.Frame(self.root,bg=UI["panel"],height=62)
        self.footer.pack(fill="x",side="bottom"); self.footer.pack_propagate(False)
        self.content=tk.Frame(self.root,bg=UI["bg"]); self.content.pack(fill="both",expand=True)

    def _clear(self):
        for w in self.content.winfo_children(): w.destroy()
        for w in self.footer.winfo_children(): w.destroy()

    def _show_page(self,idx):
        self.step_idx=idx
        for i,d in enumerate(self._dots):
            d.configure(fg=UI["accent_dim"] if i<idx else (UI["accent"] if i==idx else UI["border"]))
        self.slbl.configure(text=f"{self.STEPS[idx]}  ·  {idx+1}/{len(self.STEPS)}")
        self._clear()
        [self._p_welcome,self._p_path,self._p_theme,
         self._p_translation,self._p_settings,self._p_install][idx]()

    def _btn(self,parent,text,cmd,primary=False):
        bg=UI["accent"] if primary else UI["btn_bg"]; fg=UI["btn_text_pri"] if primary else UI["text"]
        hv=UI["accent_light"] if primary else UI["btn_hover"]
        b=tk.Label(parent,text=text,bg=bg,fg=fg,cursor="hand2",
                   font=("Segoe UI",10,"bold" if primary else "normal"),padx=24,pady=9)
        b.bind("<Button-1>",lambda e:cmd()); b.bind("<Enter>",lambda e:b.configure(bg=hv))
        b.bind("<Leave>",lambda e:b.configure(bg=bg)); return b

    def _p_welcome(self):
        f=tk.Frame(self.content,bg=UI["bg"]); f.place(relx=0.5,rely=0.5,anchor="center")
        tk.Label(f,text="\u0628\u0650\u0633\u0652\u0645\u0650 \u0627\u0644\u0644\u0651\u064e\u0647\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0652\u0645\u064e\u0646\u0650 \u0627\u0644\u0631\u0651\u064e\u062d\u0650\u064a\u0645\u0650",
                 bg=UI["bg"],fg=UI["accent"],font=("Segoe UI",15)).pack(pady=(0,8))

        logo_loaded = False
        candidates = [
            res("docs/logo/icon_transparent.png"),
            res("docs/logo/icon.png"),
            Path("docs/logo/icon_transparent.png"),
            Path("docs/logo/icon.png"),
        ]
        for lp in candidates:
            if lp.exists():
                try:
                    lim = Image.open(lp).convert("RGBA")
                    # If image does not have transparent pixels, make white background transparent
                    extrema = lim.getchannel("A").getextrema()
                    if extrema[0] >= 250:
                        gray = lim.convert("L")
                        diff = Image.eval(gray, lambda v: 255 - v)
                        alpha = Image.eval(diff, lambda v: min(255, int(v * 6.5)))
                        lim.putalpha(alpha)
                    bbox = lim.getbbox()
                    if bbox:
                        lim = lim.crop(bbox)
                    tw = 320
                    th = int(tw * lim.height / lim.width)
                    lim = lim.resize((tw, th), Image.Resampling.LANCZOS)
                    self._welcome_logo = ImageTk.PhotoImage(lim)
                    tk.Label(f, image=self._welcome_logo, bg=UI["bg"]).pack(pady=(0, 6))
                    logo_loaded = True
                    break
                except Exception:
                    pass
        if not logo_loaded:
            tk.Label(f, text="DeenBG", bg=UI["bg"], fg=UI["text"], font=("Segoe UI", 36, "bold")).pack(pady=(0, 4))

        tk.Label(f,text=f"Quran Wallpaper Generator  \u00b7  v{APP_VER}",
                 bg=UI["bg"],fg=UI["muted"],font=("Segoe UI",11)).pack(pady=(2,6))
        tk.Frame(f,bg=UI["border"],height=1,width=480).pack(pady=16)
        tk.Label(f,text=("DeenBG sets a random Quran ayah as your desktop wallpaper each time you log in.\n"
                         "All in a clean, readable layout that adapts to your screen resolution.\n\n"
                         "More than just a wallpaper changer, DeenBG turns your everyday screen time\n"
                         "into a moment of reflection."),
                 bg=UI["bg"],fg=UI["text"],font=("Segoe UI",10),justify="center").pack()
        self._btn(self.footer,"Begin Installation  \u2192",lambda:self._show_page(1),
                  primary=True).pack(side="right",padx=22,pady=12)

    def _p_path(self):
        f=tk.Frame(self.content,bg=UI["bg"]); f.pack(fill="both",expand=True,padx=54,pady=34)
        tk.Label(f,text="Installation Folder",bg=UI["bg"],fg=UI["text"],
                 font=("Segoe UI",20,"bold")).pack(anchor="w")
        tk.Label(f,text="DeenBG will be installed in the folder below.",
                 bg=UI["bg"],fg=UI["muted"],font=("Segoe UI",10)).pack(anchor="w",pady=(4,20))
        row=tk.Frame(f,bg=UI["card"],padx=14,pady=10,highlightbackground=UI["border"],highlightthickness=1); row.pack(fill="x")
        tk.Entry(row,textvariable=self.install_dir,bg=UI["card"],fg=UI["text"],
                 insertbackground=UI["text"],relief="flat",
                 font=("Segoe UI",10),width=55).pack(side="left",fill="x",expand=True)
        def browse():
            d=filedialog.askdirectory(initialdir=self.install_dir.get(),title="Choose install folder")
            if d: self.install_dir.set(d)
        b=tk.Label(row,text="Browse",bg=UI["accent"],fg=UI["btn_text_pri"],
                   font=("Segoe UI",9,"bold"),padx=14,pady=4,cursor="hand2")
        b.pack(side="right",padx=(10,0)); b.bind("<Button-1>",lambda e:browse())
        tk.Frame(f,bg=UI["border"],height=1).pack(fill="x",pady=18)
        tk.Label(f,text=("  \u2022 Approximately 40 MB of disk space is required.\n"
                         "  \u2022 No administrator privileges needed.\n"
                         "  \u2022 To uninstall: remove via Windows Settings \u2192 Installed apps or Control Panel."),
                 bg=UI["bg"],fg=UI["muted"],font=("Segoe UI",9),justify="left").pack(anchor="w")
        self._btn(self.footer,"\u2190  Back",lambda:self._show_page(0)).pack(side="left",padx=22,pady=12)
        self._btn(self.footer,"Next  \u2192",lambda:self._show_page(2),primary=True).pack(side="right",padx=22,pady=12)

    def _p_theme(self):
        outer=tk.Frame(self.content,bg=UI["bg"]); outer.pack(fill="both",expand=True)
        hdr=tk.Frame(outer,bg=UI["bg"]); hdr.pack(fill="x",padx=22,pady=(14,6))
        tk.Label(hdr,text="Choose a Wallpaper Theme",bg=UI["bg"],fg=UI["text"],
                 font=("Segoe UI",18,"bold")).pack(anchor="w")
        tk.Label(hdr,text="Click any card to select it. Each preview shows the actual rendering style.",
                 bg=UI["bg"],fg=UI["muted"],font=("Segoe UI",9)).pack(anchor="w",pady=(2,0))
        cf=tk.Frame(outer,bg=UI["bg"]); cf.pack(fill="both",expand=True,padx=16,pady=4)
        canv=tk.Canvas(cf,bg=UI["bg"],highlightthickness=0)
        sb=ttk.Scrollbar(cf,orient="vertical",command=canv.yview)
        canv.configure(yscrollcommand=sb.set); sb.pack(side="right",fill="y")
        canv.pack(side="left",fill="both",expand=True)
        gf=tk.Frame(canv,bg=UI["bg"]); win=canv.create_window((0,0),window=gf,anchor="nw")
        canv.bind("<Configure>",lambda e:canv.itemconfig(win,width=e.width))
        gf.bind("<Configure>",lambda e:canv.configure(scrollregion=canv.bbox("all")))
        canv.bind_all("<MouseWheel>",lambda e:canv.yview_scroll(int(-1*(e.delta/120)),"units"))
        self._tf={}; COLS=2
        def _sel(key):
            self.selected_theme.set(key)
            for k,b in self._tf.items(): b.configure(bg=UI["accent"] if k==key else UI["border"])
        for idx,tkey in enumerate(THEMES.keys()):
            row,col=divmod(idx,COLS); t=THEMES[tkey]; issel=tkey==self.selected_theme.get()
            border=tk.Frame(gf,bg=UI["accent"] if issel else UI["border"],padx=2,pady=2)
            border.grid(row=row,column=col,padx=10,pady=8,sticky="nsew")
            gf.columnconfigure(col,weight=1,uniform="thm"); self._tf[tkey]=border
            inner=tk.Frame(border,bg=UI["card"]); inner.pack(fill="both",expand=True)
            if tkey not in self._pc:
                img=generate_theme_preview(tkey,W=358,H=202); self._pc[tkey]=ImageTk.PhotoImage(img)
            ph=self._pc[tkey]; il=tk.Label(inner,image=ph,bg=UI["card"],cursor="hand2")
            il.image=ph; il.pack()
            nb=tk.Frame(inner,bg=UI["panel"]); nb.pack(fill="x")
            tk.Label(nb,text=t["name"],bg=UI["panel"],fg=UI["text"],
                     font=("Segoe UI",10,"bold"),pady=7,cursor="hand2").pack(side="left",padx=12)
            sw=tk.Frame(nb,bg=UI["panel"]); sw.pack(side="right",padx=10)
            for ch in [t["bg"],t["ar"],t["tr"]]:
                tk.Label(sw,bg=ch,width=2,relief="flat").pack(side="left",padx=2)
            for w in [border,inner,il,nb]+list(nb.winfo_children())+list(sw.winfo_children()):
                w.bind("<Button-1>",lambda e,k=tkey:_sel(k))
        self._btn(self.footer,"\u2190  Back",lambda:self._show_page(1)).pack(side="left",padx=22,pady=12)
        self._btn(self.footer,"Next  \u2192",lambda:self._show_page(3),primary=True).pack(side="right",padx=22,pady=12)

    def _p_translation(self):
        f=tk.Frame(self.content,bg=UI["bg"]); f.pack(fill="both",expand=True,padx=54,pady=(20,10))
        tk.Label(f,text="Choose a Translation",bg=UI["bg"],fg=UI["text"],
                 font=("Segoe UI",20,"bold")).pack(anchor="w")
        tk.Label(f,text="Select the English translation that will appear beneath the Arabic text.",
                 bg=UI["bg"],fg=UI["muted"],font=("Segoe UI",10)).pack(anchor="w",pady=(2,12))
        cards=[]
        for key,(name,desc) in TRANSLATIONS.items():
            issel=key==self.selected_trans.get()
            card=tk.Frame(f,bg=UI["card"],padx=16,pady=8,
                          highlightbackground=UI["accent"] if issel else UI["border"],highlightthickness=1)
            card.pack(fill="x",pady=4); cards.append(card)
            rb=tk.Radiobutton(card,variable=self.selected_trans,value=key,bg=UI["card"],fg=UI["text"],
                              selectcolor=UI["card"],activebackground=UI["card"],
                              activeforeground=UI["text"],cursor="hand2"); rb.pack(side="left")
            tf=tk.Frame(card,bg=UI["card"]); tf.pack(side="left",padx=6)
            tk.Label(tf,text=name,bg=UI["card"],fg=UI["text"],font=("Segoe UI",11,"bold")).pack(anchor="w")
            tk.Label(tf,text=desc,bg=UI["card"],fg=UI["muted"],font=("Segoe UI",9)).pack(anchor="w")
            def _sel(k=key,c=card,ac=cards):
                self.selected_trans.set(k)
                for ch in ac: ch.configure(highlightbackground=UI["accent"] if ch is c else UI["border"])
            for w in [card,rb,tf]+list(tf.winfo_children()):
                w.bind("<Button-1>",lambda e,k=key,c=card:_sel(k,c))
        self._btn(self.footer,"\u2190  Back",lambda:self._show_page(2)).pack(side="left",padx=22,pady=12)
        self._btn(self.footer,"Next  \u2192",lambda:self._show_page(4),primary=True).pack(side="right",padx=22,pady=12)

    def _p_settings(self):
        f=tk.Frame(self.content,bg=UI["bg"]); f.pack(fill="both",expand=True,padx=54,pady=(18,10))
        tk.Label(f,text="Configure Settings",bg=UI["bg"],fg=UI["text"],
                 font=("Segoe UI",20,"bold")).pack(anchor="w")
        tk.Label(f,text="All settings can be changed later by editing config.json.",
                 bg=UI["bg"],fg=UI["muted"],font=("Segoe UI",10)).pack(anchor="w",pady=(4,16))
        def sec(t): tk.Label(f,text=t,bg=UI["bg"],fg=UI["accent"],font=("Segoe UI",9,"bold")).pack(anchor="w",pady=(10,4))
        sec("FONT SIZE")
        for lbl,var in [("Arabic text size:",self.scale_arabic),("Translation size:",self.scale_translation)]:
            row=tk.Frame(f,bg=UI["bg"]); row.pack(fill="x",pady=3)
            tk.Label(row,text=lbl,bg=UI["bg"],fg=UI["text"],font=("Segoe UI",10),width=22,anchor="w").pack(side="left")
            vl=tk.Label(row,text=f"{var.get():.1f}\u00d7",bg=UI["bg"],fg=UI["accent"],font=("Segoe UI",10,"bold"),width=4)
            vl.pack(side="right")
            def _upd(v,ll=vl): ll.configure(text=f"{float(v):.1f}\u00d7")
            ttk.Scale(row,from_=0.5,to=2.0,variable=var,orient="horizontal",command=_upd,length=340).pack(side="left",padx=10)
        sec("BEHAVIOUR")
        for txt,var in [("Avoid repeating Ayahs (cycles all 6,236 ayah before repeating)",self.avoid_repeats),
                        ("Save generated wallpaper PNG files to disk",self.save_wallpapers)]:
            tk.Checkbutton(f,text=txt,variable=var,bg=UI["bg"],fg=UI["text"],selectcolor=UI["card"],
                           activebackground=UI["bg"],activeforeground=UI["text"],font=("Segoe UI",10)).pack(anchor="w",pady=2)
        sec("SCHEDULE")
        tk.Checkbutton(f,text="Change wallpaper automatically at every login (Windows Task Scheduler)",
                       variable=self.register_task,bg=UI["bg"],fg=UI["text"],selectcolor=UI["card"],
                       activebackground=UI["bg"],activeforeground=UI["text"],font=("Segoe UI",10)).pack(anchor="w",pady=2)
        ir=tk.Frame(f,bg=UI["bg"]); ir.pack(anchor="w",pady=(4,0))
        tk.Label(ir,text="   Also rotate every",bg=UI["bg"],fg=UI["muted"],font=("Segoe UI",10)).pack(side="left")
        eb=tk.Frame(ir,bg=UI["border"],padx=1,pady=1); eb.pack(side="left",padx=8)
        ie=tk.Entry(eb,bg="#ffffff",fg=UI["accent_dim"],insertbackground=UI["text"],
                    relief="flat",font=("Segoe UI",10),width=5,justify="center")
        ie.pack()

        def _on_focus_in(e):
            val = self.interval_var.get().strip()
            if val == "0" or not val:
                ie.delete(0, "end"); ie.configure(fg=UI["text"])

        def _on_focus_out(e):
            val=ie.get().strip()
            if not val or val == "0":
                self.interval_var.set("0")
                ie.delete(0, "end"); ie.insert(0, "0"); ie.configure(fg=UI["accent_dim"])
            else:
                self.interval_var.set(val); ie.configure(fg=UI["text"])

        def _on_key(e):
            self.root.after_idle(lambda: self.interval_var.set(ie.get().strip()))

        ie.bind("<FocusIn>", _on_focus_in)
        ie.bind("<FocusOut>", _on_focus_out)
        ie.bind("<KeyRelease>", _on_key)

        cur_val = self.interval_var.get().strip()
        if cur_val and cur_val != "0":
            ie.insert(0, cur_val); ie.configure(fg=UI["text"])
        else:
            ie.insert(0, "0"); ie.configure(fg=UI["accent_dim"])

        tk.Label(ir,text="minutes  (0 or leave empty for login only)",bg=UI["bg"],fg=UI["muted"],font=("Segoe UI",9)).pack(side="left")
        self._btn(self.footer,"\u2190  Back",lambda:self._show_page(3)).pack(side="left",padx=22,pady=12)
        self._btn(self.footer,"Install Now  \u2192",lambda:self._show_page(5),primary=True).pack(side="right",padx=22,pady=12)

    def _p_install(self):
        f=tk.Frame(self.content,bg=UI["bg"]); f.pack(fill="both",expand=True,padx=40,pady=22)
        self._title_lbl=tk.Label(f,text="Installing DeenBG\u2026",bg=UI["bg"],fg=UI["text"],
                 font=("Segoe UI",20,"bold"))
        self._title_lbl.pack(anchor="w")
        self._slbl=tk.Label(f,text="Preparing\u2026",bg=UI["bg"],fg=UI["muted"],font=("Segoe UI",10))
        self._slbl.pack(anchor="w",pady=(6,10))
        self._prog=ttk.Progressbar(f,orient="horizontal",mode="determinate",
                                   style="Horizontal.TProgressbar",length=800); self._prog.pack(fill="x")
        lw=tk.Frame(f,bg=UI["border"],padx=1,pady=1); lw.pack(fill="both",expand=True,pady=(12,0))
        self._logt=tk.Text(lw,bg="#ffffff",fg=UI["text"],insertbackground=UI["text"],
                           relief="flat",font=("Consolas",9),state="disabled",wrap="word")
        lsb=ttk.Scrollbar(lw,orient="vertical",command=self._logt.yview)
        self._logt.configure(yscrollcommand=lsb.set); lsb.pack(side="right",fill="y")
        self._logt.pack(fill="both",expand=True,padx=10,pady=8)
        self._fin=self._btn(self.footer,"Finish",self._on_finish,primary=True)
        self._fin.pack(side="right",padx=22,pady=12); self._fin.configure(fg=UI["accent_dim"],cursor="arrow")
        threading.Thread(target=self._do_install,daemon=True).start()

    def _log(self,msg,color=None):
        def _a():
            self._logt.configure(state="normal")
            if color:
                tag=f"t{random.randint(0,999999)}"; self._logt.tag_configure(tag,foreground=color)
                self._logt.insert("end",msg+"\n",tag)
            else: self._logt.insert("end",msg+"\n")
            self._logt.see("end"); self._logt.configure(state="disabled")
        self.root.after(0,_a)

    def _status(self,msg,pct):
        self.root.after(0,lambda:(self._slbl.configure(text=msg),self._prog.configure(value=pct)))

    def _unlock_fin(self):
        self.root.after(0,lambda:(self._fin.configure(fg=UI["btn_text_pri"],cursor="hand2"),
                                   setattr(self,"_ok",True)))

    def _do_install(self):
        try: self._run(Path(self.install_dir.get()))
        except Exception as e:
            self._log(f"\n[ERROR] {e}",UI["error"]); self._status("Installation failed.",0)
            self.root.after(0,lambda: self._title_lbl.configure(text="Installation Failed",fg=UI["error"]))
            self._unlock_fin()

    def _run(self,d):
        self._log(f"Installing to: {d}"); self._status("Cleaning previous installation…",3)
        _clean_install_dir(d)
        self._status("Creating directories…",5)
        for sub in ["","fonts","data","wallpapers","cache","logs"]: (d/sub).mkdir(parents=True,exist_ok=True)
        self._log("  [OK] Previous files cleaned, directories ready"); self._status("Copying program files…",15)
        dst=d/EXE_NAME; src=Path(sys.executable); self._log(f"  Copying {src.name} -> {EXE_NAME}")
        try: shutil.copy2(src,dst); self._log(f"  [OK] {EXE_NAME} installed")
        except Exception as e: self._log(f"  [ERR] {e}",UI["error"]); raise
        self._status("Copying fonts\u2026",28); fs=res("fonts")
        if fs.exists():
            for fn in fs.iterdir(): shutil.copy2(fn,d/"fonts"/fn.name)
            self._log("  [OK] Fonts copied")
        else: self._log("  [WARN] Fonts not in bundle",UI["muted"])
        self._status("Preparing Quran database\u2026",40)
        qdst=d/"data"/"quran.json"; qsrc=res("data")/"quran.json"
        if qsrc.exists(): shutil.copy2(qsrc,qdst); self._log("  [OK] Quran DB ready (6,236 ayahs)")
        elif not qdst.exists():
            self._log("  Downloading Quran DB (requires internet, ~3 MB)\u2026")
            self._status("Downloading Quran data\u2026",42); ok=self._dl(qdst,self.selected_trans.get())
            self._log("  [OK] Downloaded" if ok else "  [ERR] Download failed",None if ok else UI["error"])
        else: self._log("  [OK] Quran DB already present")
        self._status("Writing configuration\u2026",60)
        cfg={"api":{"translation_edition":self.selected_trans.get()},
             "design":{"theme":self.selected_theme.get(),"font_arabic":"Amiri-Regular.ttf",
                       "font_latin":"Lato-Regular.ttf","decorative_line":True,
                       "font_scale_arabic":round(self.scale_arabic.get(),2),
                       "font_scale_translation":round(self.scale_translation.get(),2)},
             "behavior":{"avoid_repeats":self.avoid_repeats.get(),"max_cache_size":6236,
                         "save_wallpapers":self.save_wallpapers.get(),"max_saved_wallpapers":40}}
        with open(d/"config.json","w",encoding="utf-8") as fh: json.dump(cfg,fh,indent=2,ensure_ascii=False)
        self._log(f"  [OK] config.json (theme: {THEMES[self.selected_theme.get()]['name']})")
        if self.register_task.get():
            self._status("Registering Task Scheduler\u2026",74)
            iv=int(self.interval_var.get()) if self.interval_var.get().strip().isdigit() else None
            ok,msg=self._reg(dst,iv); self._log(f"  [{'OK' if ok else 'ERR'}] Task: {msg}",None if ok else UI["error"])
        self._reg_uninstall(dst, d)
        self._status("Generating first wallpaper\u2026",88); self._log("\n  Generating first wallpaper\u2026")
        try:
            r=subprocess.run([str(dst),"--generate"],capture_output=True,timeout=40)
            self._log("  [OK] Wallpaper set!",UI["success"] if r.returncode==0 else None)
        except Exception as e: self._log(f"  [WARN] {e} (will run at next login)",UI["muted"])
        self._status("Setup finished successfully. Click Finish to exit.",100)
        self.root.after(0,lambda: self._title_lbl.configure(text="Installation Complete!  \u2713",fg=UI["accent"]))
        self._log(f"\n{'='*52}"); self._log("  DeenBG installed!",UI["success"])
        self._log(f"  Location : {d}"); self._log(f"  Theme    : {THEMES[self.selected_theme.get()]['name']}")
        self._log("  Wallpaper changes at every Windows login."); self._log(f"{'='*52}"); self._unlock_fin()

    def _dl(self,dst,edition):
        import urllib.request
        try:
            def _fetch(url):
                with urllib.request.urlopen(url,timeout=40) as r: return json.loads(r.read().decode("utf-8"))
            def _ext(data):
                d=data["data"]
                if "ayahs" in d: return d["ayahs"]
                r=[]
                for s in d["surahs"]: r.extend(s["ayahs"])
                return r
            ar=_ext(_fetch("https://api.alquran.cloud/v1/quran/quran-uthmani"))
            tr=_ext(_fetch(f"https://api.alquran.cloud/v1/quran/{edition}"))
            db=[]; gn=0
            for si,(sn,ac) in enumerate(SURAH_META):
                for ai in range(ac):
                    if gn>=len(ar): break
                    db.append({"number":gn+1,"surah_number":si+1,"surah_name":sn,
                               "ayah_in_surah":ai+1,"arabic":ar[gn]["text"],"translation":tr[gn]["text"]}); gn+=1
            with open(dst,"w",encoding="utf-8") as f: json.dump(db,f,ensure_ascii=False,separators=(",",":"))
            return True
        except Exception as e: self._log(f"    DL error: {e}",UI["error"]); return False

    def _reg(self, exe, iv):
        return register_scheduled_task(exe, iv)

    def _reg_uninstall(self, exe, d):
        if register_uninstall(exe, d):
            self._log("  [OK] Registered in Control Panel (Installed Apps)")
        else:
            self._log("  [WARN] Could not register in Control Panel", UI["muted"])

    def _on_finish(self):
        if self._ok: self.root.destroy()

# ============================================================
# SCHEDULED TASK & UNINSTALL REGISTRATION (SHARED)
# ============================================================
def register_uninstall(exe: Path, d: Path) -> bool:
    try:
        import winreg
        k = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Uninstall\DeenBG")
        winreg.SetValueEx(k, "DisplayName", 0, winreg.REG_SZ, "DeenBG")
        winreg.SetValueEx(k, "DisplayVersion", 0, winreg.REG_SZ, APP_VER)
        winreg.SetValueEx(k, "Publisher", 0, winreg.REG_SZ, "CyberMajeed")
        winreg.SetValueEx(k, "DisplayIcon", 0, winreg.REG_SZ, f'"{exe}",0')
        winreg.SetValueEx(k, "UninstallString", 0, winreg.REG_SZ, f'"{exe}" --uninstall')
        winreg.SetValueEx(k, "InstallLocation", 0, winreg.REG_SZ, str(d))
        winreg.SetValueEx(k, "NoModify", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "NoRepair", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(k, "EstimatedSize", 0, winreg.REG_DWORD, 42000)
        winreg.CloseKey(k)
        return True
    except Exception:
        return False

def register_scheduled_task(exe, iv=0):
    import re

    # Ensure no startup app entries exist so DeenBG runs ONLY from Task Scheduler
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as k:
            winreg.DeleteValue(k, TASK_NAME)
    except Exception:
        pass
    try:
        st = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup" / "DeenBG.cmd"
        if st.exists():
            st.unlink()
    except Exception:
        pass

    # Resolve current user SID so Task Scheduler allows standard non-admin users to register logon tasks
    sid = ""
    try:
        r = subprocess.run(["whoami", "/user"], capture_output=True, text=True, timeout=5)
        m = re.search(r"(S-1-5-[0-9-]+)", r.stdout)
        if m:
            sid = m.group(1)
    except Exception:
        pass

    iv_int = int(iv) if str(iv).strip().isdigit() else 0

    def _iso(m):
        h, mn = divmod(m, 60)
        if h and mn: return f"PT{h}H{mn}M"
        if h: return f"PT{h}H"
        return f"PT{mn}M"

    user_node = f"      <UserId>{sid}</UserId>" if sid else ""
    p_user = f"\n      <UserId>{sid}</UserId>" if sid else ""

    triggers = [
        "    <LogonTrigger>\n"
        "      <Enabled>true</Enabled>\n"
        f"{user_node}\n"
        "    </LogonTrigger>"
    ]
    if iv_int > 0:
        now_iso = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
        triggers.append(
            f"    <TimeTrigger>\n"
            f"      <StartBoundary>{now_iso}</StartBoundary>\n"
            f"      <Enabled>true</Enabled>\n"
            f"      <Repetition>\n"
            f"        <Interval>{_iso(iv_int)}</Interval>\n"
            f"        <StopAtDurationEnd>false</StopAtDurationEnd>\n"
            f"      </Repetition>\n"
            f"    </TimeTrigger>"
        )
    triggers_block = "\n".join(triggers)

    xml = (f'<?xml version="1.0" encoding="UTF-16"?>\n'
           f'<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">\n'
           f'  <RegistrationInfo><Description>DeenBG Quran wallpaper generator.</Description></RegistrationInfo>\n'
           f'  <Triggers>\n{triggers_block}\n  </Triggers>\n'
           f'  <Principals><Principal id="Author">{p_user}\n'
           f'    <LogonType>InteractiveToken</LogonType>\n'
           f'  </Principal></Principals>\n'
           f'  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>'
           f'<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'
           f'<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>'
           f'<ExecutionTimeLimit>PT5M</ExecutionTimeLimit><Priority>7</Priority>'
           f'<StartWhenAvailable>true</StartWhenAvailable></Settings>\n'
           f'  <Actions Context="Author"><Exec><Command>{exe}</Command>'
           f'<Arguments>--generate</Arguments><WorkingDirectory>{exe.parent}</WorkingDirectory>'
           f'</Exec></Actions>\n</Task>')

    tmp = Path(tempfile.gettempdir()) / "_deenbg_task.xml"
    try:
        with open(tmp, "w", encoding="utf-16") as tf:
            tf.write(xml)

        subprocess.run(["schtasks", "/Delete", "/TN", TASK_NAME, "/F"], capture_output=True)

        r = subprocess.run(["schtasks", "/Create", "/XML", str(tmp), "/TN", TASK_NAME, "/F"],
                         capture_output=True, text=True)
        if r.returncode == 0:
            desc = "runs at every login" + (f" + every {iv_int} min" if iv_int > 0 else "")
            return True, f"Task Scheduler: {desc}"

        # If primary name is blocked by an existing admin-owned task, use alternative name
        alt_name = "DeenBG Wallpaper"
        subprocess.run(["schtasks", "/Delete", "/TN", alt_name, "/F"], capture_output=True)
        r2 = subprocess.run(["schtasks", "/Create", "/XML", str(tmp), "/TN", alt_name, "/F"],
                          capture_output=True, text=True)
        if r2.returncode == 0:
            desc = "runs at every login" + (f" + every {iv_int} min" if iv_int > 0 else "")
            return True, f"Task Scheduler: {desc}"

        return False, f"Task Scheduler error: {r.stderr.strip() or r2.stderr.strip()}"
    finally:
        try:
            tmp.unlink()
        except Exception:
            pass

# ============================================================
# CLI SETUP WIZARD (NO TKINTER FALLBACK)
# ============================================================
def _ask_input(prompt: str, default: str = "1") -> str:
    try:
        if sys.stdin and hasattr(sys.stdin, "isatty") and sys.stdin.isatty():
            val = input(prompt).strip()
            return val if val else default
    except Exception:
        pass
    return default

def run_cli_mode():
    print("\n" + "=" * 58)
    print("             DeenBG — Setup Wizard")
    print("=" * 58)
    print("  Bismillah ar-Rahman ar-Rahim\n")

    t_keys = list(TRANSLATIONS.keys())
    print("  Choose English translation:")
    for i, (k, (name, desc)) in enumerate(TRANSLATIONS.items(), 1):
        print(f"    {i}. {name} — {desc}")
    ans = _ask_input("  Your choice [1]: ", "1")
    idx = int(ans) - 1 if ans.isdigit() and 1 <= int(ans) <= len(t_keys) else 0
    selected_trans = t_keys[idx]

    th_keys = list(THEMES.keys())
    print("\n  Choose wallpaper theme:")
    for i, (k, v) in enumerate(THEMES.items(), 1):
        print(f"    {i:>2}. {v['name']}")
    ans = _ask_input("  Your choice [1]: ", "1")
    tidx = int(ans) - 1 if ans.isdigit() and 1 <= int(ans) <= len(th_keys) else 0
    selected_theme = th_keys[tidx]

    idir = DEFAULT_INSTALL
    print(f"\n  Installing to: {idir}")
    print("  Cleaning previous installation…")
    _clean_install_dir(idir)
    for sub in ["", "fonts", "data", "wallpapers", "cache", "logs"]:
        (idir / sub).mkdir(parents=True, exist_ok=True)
    print("  [OK] Previous files cleaned, fresh directory ready")

    dst = idir / EXE_NAME
    src = Path(sys.executable)
    try:
        shutil.copy2(src, dst)
    except Exception:
        pass

    fs = res("fonts")
    if fs.exists():
        for fn in fs.iterdir():
            shutil.copy2(fn, idir / "fonts" / fn.name)

    qdst = idir / "data" / "quran.json"
    qsrc = res("data") / "quran.json"
    if qsrc.exists():
        shutil.copy2(qsrc, qdst)

    cfg = {
        "api": {"translation_edition": selected_trans},
        "design": {
            "theme": selected_theme, "font_arabic": "Amiri-Regular.ttf",
            "font_latin": "Lato-Regular.ttf", "decorative_line": True,
            "font_scale_arabic": 1.0, "font_scale_translation": 1.0
        },
        "behavior": {
            "avoid_repeats": True, "max_cache_size": 6236,
            "save_wallpapers": True, "max_saved_wallpapers": 40
        }
    }
    with open(idir / "config.json", "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)

    ok, msg = register_scheduled_task(dst, 0)
    print(f"\n  [{'OK' if ok else 'WARN'}] {msg}")
    if register_uninstall(dst, idir):
        print("  [OK] Registered in Control Panel (Installed Apps)")

    try:
        subprocess.run([str(dst), "--generate"], capture_output=True, timeout=40)
        print("  [OK] First wallpaper set!")
    except Exception:
        pass

    print("\n" + "=" * 58)
    print("  Setup Complete!")
    print(f"  Location: {idir}")
    print("=" * 58 + "\n")

# ============================================================
# ENTRY POINT
# ============================================================
def main():
    if "--generate" in sys.argv:
        run_generate_mode()
    elif "--uninstall" in sys.argv:
        run_uninstall_mode()
    else:
        if HAS_TK:
            try:
                try: ctypes.windll.shcore.SetProcessDpiAwareness(2)
                except Exception:
                    try: ctypes.windll.user32.SetProcessDPIAware()
                    except Exception: pass
                root = tk.Tk()
                InstallerApp(root)
                root.mainloop()
                return
            except Exception:
                pass
        run_cli_mode()

if __name__ == "__main__":
    main()
