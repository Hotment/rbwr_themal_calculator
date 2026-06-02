import tkinter as tk
from tkinter import ttk
import math
import sys
import os
import threading
import logging
import traceback
from PIL import Image, ImageDraw, ImageTk

__version__ = "1.3.0"

# --- Update Server Configuration ---
UPDATE_SERVER_URL = "http://127.0.0.1:8400"
UPDATE_HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0'}

BASE64_ICON_PNG = "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(rest of string omitted for brevity)"


_is_compiled = not sys.executable.lower().endswith(('python.exe', 'pythonw.exe', 'python', 'python3'))
_log_dir = os.path.dirname(os.path.abspath(sys.executable)) if _is_compiled else os.path.dirname(os.path.abspath(__file__))
_log_path = os.path.join(_log_dir, "rbwr_overlay.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(_log_path, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
# Silence noisy third-party loggers
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("onnxruntime").setLevel(logging.WARNING)
log = logging.getLogger("rbwr")
log.info(f"=== RBWR APR Overlay v{__version__} starting ===")
log.info(f"Version: {__version__}")
log.info(f"Python: {sys.version}")
log.info(f"Executable: {sys.executable}")
log.info(f"Script __file__: {__file__}")
log.info(f"Log file: {_log_path}")

def get_default_icon_image():
    try:
        img = Image.new("RGBA", (256, 256), color=(7, 8, 10, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([20, 20, 236, 236], outline=(0, 240, 255, 255), width=10)
        draw.ellipse([32, 32, 224, 224], fill=(17, 20, 26, 255))
        bolt = [(145, 55), (95, 135), (125, 135), (115, 195), (165, 115), (135, 115)]
        draw.polygon(bolt, fill=(57, 255, 20, 255))
        return img
    except Exception:
        return Image.new("RGBA", (64, 64), color=(0, 240, 255, 255))

def generate_default_icon():
    try:
        img = get_default_icon_image()
        img.save("icon.png")
        img.save("icon.ico", format="ICO", sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    except Exception:
        pass

import re
from ctypes import wintypes
import ctypes
import json

CONFIG_FILE = "settings.json"

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

HAS_OCR = False
try:
    from rapidocr_onnxruntime import RapidOCR
    HAS_OCR = True
    log.info("rapidocr_onnxruntime imported successfully.")
    log.info(f"  Package location: {os.path.dirname(os.path.abspath(RapidOCR.__module__)) if hasattr(RapidOCR, '__module__') else 'unknown'}")
except ImportError as e:
    RapidOCR = None
    log.warning(f"rapidocr_onnxruntime NOT available: {e}")
except Exception as e:
    RapidOCR = None
    log.error(f"Unexpected error importing rapidocr_onnxruntime: {e}")
    log.error(traceback.format_exc())

def get_active_window_rect():
    try:
        hwnd = ctypes.windll.user32.GetForegroundWindow()
        if hwnd:
            rect = wintypes.RECT()
            if ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top
    except Exception:
        pass
    return None

BG_MAIN = "#07080a"       # Deep tactical carbon matte
BG_CARD = "#11141a"       # Cyber deck plate dark gray
BG_HEADER = "#030405"     # Pure terminal dark black
ACCENT_CYAN = "#00f0ff"   # Tactical laser cyan
ACCENT_GREEN = "#39ff14"  # Glow radioactive neon green
TEXT_LIGHT = "#ffffff"    # High contrast display white
TEXT_MUTED = "#6c7d93"    # Muted control-room slate blue
ACCENT_RED = "#ff003c"    # Emergency SCRAM laser red
ACCENT_GOLD = "#ffaa00"   # Warning amber isotope yellow

class Calculator:
    def __init__(self, usage=61.32):
        self.usage = usage
        self.selected_unit = 1

    def set_usage(self, val_str):
        try:
            val = float(val_str)
            self.usage = 0.0 if val < 0 else val
        except ValueError:
            self.usage = 61.32

    def calc_flow(self, thermal):
        if self.selected_unit == 1:
            return max(0.0, 82.8 + (13.7 * thermal) + (5.87 * 10**-3 * (thermal**2))) + 2
        else:
            return max(0.0, 115 + (12.2 * thermal) + (9.27 * 10**-3 * (thermal**2))) + 2

    def calc_gen_load(self, thermal):
        if self.selected_unit == 1:
            return max(0.0, -135 + (13 * thermal) + (5.33 * 10**-3 * (thermal**2)))
        else:
            return max(0.0, -143 + (12.5 * thermal) - (2.06 * 10**-3 * (thermal**2)))

    def calc_thermal(self, demand):
        if self.selected_unit == 1:
            inner = 169 + 0.02132 * (demand + 135 + self.usage)
            if inner < 0:
                return 0.0
            return max(0.0, (-13 + math.sqrt(inner)) / 0.01066)
        else:
            inner = 156.25 + 0.00824 * (demand + 143 + self.usage)
            if inner < 0:
                return 0.0
            return max(0.0, (-12.5 + math.sqrt(inner)) / 0.00412)


class OverlayApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"RBWR APR Calculator v{__version__}")
        
        # Load saved settings
        settings = self.load_settings()
        
        self.calc = Calculator(usage=settings["usage"])
        self.calc.selected_unit = settings["selected_unit"]
        self.is_topmost = settings["is_topmost"]
        self.is_compact = settings["is_compact"]
        self.show_config = False
        self.updating_fields = False
        
        # Window attributes
        self.root.overrideredirect(True)  # Frameless/Borderless
        self.root.attributes("-topmost", self.is_topmost)
        self.root.attributes("-alpha", settings["opacity"])
        self.root.configure(bg=BG_MAIN, highlightbackground=ACCENT_CYAN, highlightcolor=ACCENT_CYAN, highlightthickness=1)
        
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("Horizontal.TScale",
                             troughcolor=BG_MAIN,
                             background=ACCENT_CYAN,
                             bordercolor=BG_CARD,
                             lightcolor=ACCENT_CYAN,
                             darkcolor=ACCENT_CYAN,
                             sliderthickness=14,
                             sliderlength=24)
        
        # Screen Scan & OCR state variables
        self.auto_scan_active = False
        self.ocr_engine: RapidOCR | None = None  # pyright: ignore[reportInvalidTypeForm]
        self.ocr_initializing = False
        
        if HAS_OCR:
            self.ocr_initializing = True
            threading.Thread(target=self.initialize_ocr, daemon=True).start()
            
        # Start background scanner loop thread
        threading.Thread(target=self.scan_loop, daemon=True).start()
        
        self.width_detailed = 420
        self.height_detailed = 420
        self.width_compact = 450
        self.height_compact = 60
        
        self._drag_data = {"x": 0, "y": 0}
        
        self.var_demand = tk.StringVar(value="0")
        self.var_rtp = tk.StringVar(value="0")
        self.var_demand.trace_add("write", lambda name, index, mode: self.on_input_update("demand"))
        self.var_rtp.trace_add("write", lambda name, index, mode: self.on_input_update("rtp"))
        self.var_hud_scan = tk.BooleanVar(value=settings.get("enable_hud_scan", True))
        self.skipped_version = settings.get("skipped_version", "")
        
        self.var_hotkey = tk.StringVar(value=settings["hotkey"])
        self.var_hotkey.trace_add("write", lambda *args: self.start_hotkey_listener())
        self.hotkey_thread_active = False
        self.start_hotkey_listener()
        
        # Icon and Tray Setup (Loads existing icon if present, otherwise uses in-memory generated icon)
        self.icon_image_pil = get_default_icon_image()
        
        if os.path.exists("icon.ico"):
            try:
                self.root.iconbitmap("icon.ico")
            except Exception:
                try:
                    self.icon_image_tk = tk.PhotoImage(data=BASE64_ICON_PNG)
                    self.root.wm_iconphoto(True, self.icon_image_tk)
                except Exception:
                    pass
        else:
            try:
                self.icon_image_tk = tk.PhotoImage(data=BASE64_ICON_PNG)
                self.root.wm_iconphoto(True, self.icon_image_tk)
            except Exception:
                pass
                
        self.setup_tray_icon()
        
        self.context_menu = tk.Menu(self.root, tearoff=0, bg=BG_CARD, fg=TEXT_LIGHT, 
                                    activebackground=BG_HEADER, activeforeground=ACCENT_CYAN, 
                                    bd=1, relief="solid", font=("Segoe UI", 9))
        self.context_menu.add_command(label="Toggle Compact Mode", command=self.toggle_compact)
        self.context_menu.add_command(label="Toggle Always on Top", command=self.toggle_topmost)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exit Application", command=self.quit_app)
        
        self.root.bind("<Button-3>", self.show_context_menu)
        
        self.center_window(self.width_detailed, self.height_detailed)
        self.create_widgets()
        self.update_calculations(source="demand")
        
        self.check_for_updates()

    def center_window(self, w, h):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = screen_width - w - 40
        y = screen_height - h - 120
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def show_context_menu(self, event):
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()

    def create_widgets(self):
        for child in self.root.winfo_children():
            child.destroy()
            
        if self.is_compact:
            self.build_compact_layout()
        else:
            self.build_detailed_layout()

    def make_draggable(self, widget):
        widget.bind("<Button-1>", self.start_drag)
        widget.bind("<B1-Motion>", self.do_drag)

    def start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def do_drag(self, event):
        delta_x = event.x - self._drag_data["x"]
        delta_y = event.y - self._drag_data["y"]
        x = self.root.winfo_x() + delta_x
        y = self.root.winfo_y() + delta_y
        self.root.geometry(f"+{x}+{y}")

    def toggle_topmost(self):
        self.is_topmost = not self.is_topmost
        self.root.attributes("-topmost", self.is_topmost)
        symbol = "📌" if self.is_topmost else "📍"
        self.btn_topmost.config(text=symbol)
        self.save_settings()

    def toggle_compact(self):
        self.is_compact = not self.is_compact
        self.save_settings()
        if self.is_compact:
            self.root.geometry(f"{self.width_compact}x{self.height_compact}")
            self.create_widgets()
            self.update_calculations(source="demand")
        else:
            self.root.geometry(f"{self.width_detailed}x{self.height_detailed}")
            self.create_widgets()
            self.update_calculations(source="demand")

    def build_detailed_layout(self):
        title_bar = tk.Frame(self.root, bg=BG_HEADER, height=36)
        title_bar.pack(fill="x", side="top")
        title_bar.pack_propagate(False)
        self.make_draggable(title_bar)

        title_lbl = tk.Label(title_bar, text=" [ APRM MONITOR // SYS OK ]", bg=BG_HEADER, fg=ACCENT_CYAN,
                             font=("Consolas", 9, "bold"))
        title_lbl.pack(side="left", padx=10)
        self.make_draggable(title_lbl)

        btn_close = tk.Label(title_bar, text="✕", bg=BG_HEADER, fg=TEXT_MUTED, width=3, font=("Segoe UI", 11, "bold"))
        btn_close.pack(side="right", fill="y")
        btn_close.bind("<Button-1>", lambda e: self.quit_app())
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg=TEXT_LIGHT))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg=BG_HEADER, fg=TEXT_MUTED))

        btn_comp = tk.Label(title_bar, text="⛶", bg=BG_HEADER, fg=TEXT_MUTED, width=3, font=("Segoe UI", 11))
        btn_comp.pack(side="right", fill="y")
        btn_comp.bind("<Button-1>", lambda e: self.toggle_compact())
        btn_comp.bind("<Enter>", lambda e: btn_comp.config(bg=BG_CARD, fg=ACCENT_CYAN))
        btn_comp.bind("<Leave>", lambda e: btn_comp.config(bg=BG_HEADER, fg=TEXT_MUTED))

        symbol = "📌" if self.is_topmost else "📍"
        self.btn_topmost = tk.Label(title_bar, text=symbol, bg=BG_HEADER, fg=TEXT_MUTED, width=3, font=("Segoe UI", 10))
        self.btn_topmost.pack(side="right", fill="y")
        self.btn_topmost.bind("<Button-1>", lambda e: self.toggle_topmost())
        self.btn_topmost.bind("<Enter>", lambda e: self.btn_topmost.config(bg=BG_CARD, fg=ACCENT_CYAN))
        self.btn_topmost.bind("<Leave>", lambda e: self.btn_topmost.config(bg=BG_HEADER, fg=TEXT_MUTED))

        container = tk.Frame(self.root, bg=BG_MAIN, padx=15, pady=15)
        container.pack(fill="both", expand=True)
        self.make_draggable(container)

        unit_frame = tk.Frame(container, bg=BG_MAIN)
        unit_frame.pack(fill="x", pady=(0, 10))
        self.make_draggable(unit_frame)

        self.btn_u1 = tk.Label(unit_frame, text="UNIT 1", bg=BG_CARD, fg=ACCENT_CYAN, font=("Segoe UI", 9, "bold"),
                               pady=6, width=18, bd=1, relief="flat", cursor="hand2")
        self.btn_u1.pack(side="left", expand=True, fill="x", padx=(0, 4))
        self.btn_u1.bind("<Button-1>", lambda e: self.select_unit(1))

        self.btn_u2 = tk.Label(unit_frame, text="UNIT 2", bg=BG_MAIN, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold"),
                               pady=6, width=18, bd=1, relief="flat", cursor="hand2")
        self.btn_u2.pack(side="right", expand=True, fill="x", padx=(4, 0))
        self.btn_u2.bind("<Button-1>", lambda e: self.select_unit(2))

        self.update_unit_ui_state()

        self.config_toggle_frame = tk.Frame(container, bg=BG_MAIN)
        self.config_toggle_frame.pack(fill="x", pady=2)
        self.make_draggable(self.config_toggle_frame)

        arrow = "▼" if self.show_config else "▲"
        self.lbl_config_toggle = tk.Label(self.config_toggle_frame, text=f"⚙ Configuration Settings {arrow}", 
                                          bg=BG_MAIN, fg=TEXT_MUTED, font=("Segoe UI", 8, "bold"), cursor="hand2")
        self.lbl_config_toggle.pack(anchor="w")
        self.lbl_config_toggle.bind("<Button-1>", lambda e: self.toggle_config_panel())

        self.config_panel = tk.Frame(container, bg=BG_CARD, padx=10, pady=10)
        if self.show_config:
            self.config_panel.pack(fill="x", pady=(2, 10))
        self.make_draggable(self.config_panel)

        lbl_usage = tk.Label(self.config_panel, text="Site Usage (MWe):", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_usage.grid(row=0, column=0, sticky="w", pady=4)
        
        self.var_usage = tk.StringVar(value=str(self.calc.usage))
        self.ent_usage = tk.Entry(self.config_panel, textvariable=self.var_usage, bg=BG_MAIN, fg=TEXT_LIGHT, 
                                  insertbackground=TEXT_LIGHT, font=("Consolas", 10), bd=0, highlightthickness=1, 
                                  highlightcolor=ACCENT_CYAN, highlightbackground=TEXT_MUTED, width=10, justify="center")
        self.ent_usage.grid(row=0, column=1, sticky="e", padx=10, pady=4)
        self.var_usage.trace_add("write", self.on_usage_change)

        lbl_opacity = tk.Label(self.config_panel, text="Overlay Opacity:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_opacity.grid(row=1, column=0, sticky="w", pady=4)

        self.slider_opacity = ttk.Scale(self.config_panel, from_=0.3, to=1.0, value=self.root.attributes("-alpha"),
                                         orient="horizontal", command=self.on_opacity_change)
        self.slider_opacity.grid(row=1, column=1, sticky="we", padx=10, pady=4)

        lbl_hotkey = tk.Label(self.config_panel, text="Scan Hotkey:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_hotkey.grid(row=2, column=0, sticky="w", pady=4)

        self.btn_hotkey_bind = tk.Label(self.config_panel, text=self.var_hotkey.get(), bg=BG_MAIN, fg=ACCENT_CYAN,
                                        font=("Consolas", 9, "bold"), bd=1, relief="solid", padx=10, pady=3, cursor="hand2")
        self.btn_hotkey_bind.grid(row=2, column=1, sticky="e", padx=10, pady=4)
        self.btn_hotkey_bind.bind("<Button-1>", lambda e: self.listen_for_hotkey())
        self.btn_hotkey_bind.bind("<Enter>", lambda e: self.btn_hotkey_bind.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        self.btn_hotkey_bind.bind("<Leave>", lambda e: self.btn_hotkey_bind.config(bg=BG_MAIN, fg=ACCENT_CYAN if self.btn_hotkey_bind.cget("text") != "[ PRESS KEY... ]" else ACCENT_GOLD))

        lbl_log = tk.Label(self.config_panel, text="Diagnostics:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_log.grid(row=3, column=0, sticky="w", pady=4)

        self.btn_open_log = tk.Label(self.config_panel, text="📄 Open Log", bg=BG_MAIN, fg=ACCENT_CYAN,
                                      font=("Consolas", 9, "bold"), bd=1, relief="solid", padx=10, pady=3, cursor="hand2")
        self.btn_open_log.grid(row=3, column=1, sticky="e", padx=10, pady=4)
        self.btn_open_log.bind("<Button-1>", lambda e: self.open_log_file())
        self.btn_open_log.bind("<Enter>", lambda e: self.btn_open_log.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        self.btn_open_log.bind("<Leave>", lambda e: self.btn_open_log.config(bg=BG_MAIN, fg=ACCENT_CYAN))

        lbl_hud_scan = tk.Label(self.config_panel, text="Scan HUD first:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_hud_scan.grid(row=4, column=0, sticky="w", pady=4)

        hud_status = "🟢 ENABLED" if self.var_hud_scan.get() else "🔴 DISABLED"
        hud_color = ACCENT_GREEN if self.var_hud_scan.get() else ACCENT_RED
        self.btn_hud_scan_toggle = tk.Label(self.config_panel, text=hud_status, bg=BG_MAIN, fg=hud_color,
                                            font=("Consolas", 9, "bold"), bd=1, relief="solid", padx=10, pady=3, cursor="hand2")
        self.btn_hud_scan_toggle.grid(row=4, column=1, sticky="e", padx=10, pady=4)
        self.btn_hud_scan_toggle.bind("<Button-1>", lambda e: self.toggle_hud_scan_setting())
        self.btn_hud_scan_toggle.bind("<Enter>", lambda e: self.btn_hud_scan_toggle.config(bg=BG_HEADER))
        self.btn_hud_scan_toggle.bind("<Leave>", lambda e: self.btn_hud_scan_toggle.config(bg=BG_MAIN))

        input_card = tk.Frame(container, bg=BG_MAIN, bd=1, relief="solid")
        input_card.pack(fill="both", expand=True, pady=(5, 5))
        self.make_draggable(input_card)

        input_card.grid_columnconfigure(0, weight=1)
        input_card.grid_columnconfigure(1, weight=1)

        lbl_in_header = tk.Label(input_card, text="[ // CORE CONTROL IN ]", bg=BG_MAIN, fg=ACCENT_GREEN, font=("Consolas", 8, "bold"))
        lbl_in_header.grid(row=0, column=0, pady=(6, 6), sticky="w", padx=10)
        self.make_draggable(lbl_in_header)

        lbl_demand = tk.Label(input_card, text="DEMAND LOAD (MWt)", bg=BG_MAIN, fg=TEXT_MUTED, font=("Consolas", 8, "bold"))
        lbl_demand.grid(row=1, column=0, sticky="w", pady=2, padx=10)
        self.make_draggable(lbl_demand)

        demand_adj_frame = tk.Frame(input_card, bg=BG_MAIN)
        demand_adj_frame.grid(row=2, column=0, sticky="w", pady=(0, 10), padx=10)
        self.make_draggable(demand_adj_frame)

        btn_min10 = tk.Label(demand_adj_frame, text="-10", bg=BG_CARD, fg=ACCENT_CYAN, 
                             font=("Consolas", 8, "bold"), padx=5, pady=2, cursor="hand2")
        btn_min10.pack(side="left", padx=(0, 2))
        btn_min10.bind("<Button-1>", lambda e: self.adjust_demand(-10))
        btn_min10.bind("<Enter>", lambda e: btn_min10.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_min10.bind("<Leave>", lambda e: btn_min10.config(bg=BG_CARD, fg=ACCENT_CYAN))

        self.ent_demand = tk.Entry(demand_adj_frame, textvariable=self.var_demand, bg=BG_CARD, fg=TEXT_LIGHT, 
                                   insertbackground=TEXT_LIGHT, font=("Consolas", 11, "bold"), bd=0, 
                                   highlightthickness=1, highlightcolor=ACCENT_CYAN, highlightbackground=BG_CARD, 
                                   width=8, justify="center")
        self.ent_demand.pack(side="left", padx=2)

        btn_add10 = tk.Label(demand_adj_frame, text="+10", bg=BG_CARD, fg=ACCENT_CYAN, 
                             font=("Consolas", 8, "bold"), padx=5, pady=2, cursor="hand2")
        btn_add10.pack(side="left", padx=(2, 0))
        btn_add10.bind("<Button-1>", lambda e: self.adjust_demand(10))
        btn_add10.bind("<Enter>", lambda e: btn_add10.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_add10.bind("<Leave>", lambda e: btn_add10.config(bg=BG_CARD, fg=ACCENT_CYAN))

        self.btn_scan = tk.Label(demand_adj_frame, font=("Consolas", 8, "bold"), padx=5, pady=2, cursor="hand2")
        self.btn_scan.pack(side="left", padx=(6, 0))
        self.btn_scan.bind("<Button-1>", lambda e: self.toggle_auto_scan())
        self.btn_scan.bind("<Enter>", self.on_scan_enter)
        self.btn_scan.bind("<Leave>", self.on_scan_leave)

        lbl_rtp_in = tk.Label(input_card, text="CORE POWER (RTP%)", bg=BG_MAIN, fg=TEXT_MUTED, font=("Consolas", 8, "bold"))
        lbl_rtp_in.grid(row=3, column=0, sticky="w", pady=2, padx=10)
        self.make_draggable(lbl_rtp_in)

        self.ent_rtp = tk.Entry(input_card, textvariable=self.var_rtp, bg=BG_CARD, fg=TEXT_LIGHT, 
                                insertbackground=TEXT_LIGHT, font=("Consolas", 11, "bold"), bd=0, 
                                highlightthickness=1, highlightcolor=ACCENT_CYAN, highlightbackground=BG_CARD, 
                                width=12, justify="center")
        self.ent_rtp.grid(row=4, column=0, sticky="w", pady=(0, 10), padx=10)

        lbl_out_header = tk.Label(input_card, text="[ // TELEMETRY OUT ]", bg=BG_MAIN, fg=ACCENT_CYAN, font=("Consolas", 8, "bold"))
        lbl_out_header.grid(row=0, column=1, pady=(6, 6), sticky="w", padx=10)
        self.make_draggable(lbl_out_header)

        lbl_gen = tk.Label(input_card, text="GENERATOR LOAD", bg=BG_MAIN, fg=TEXT_MUTED, font=("Consolas", 8, "bold"))
        lbl_gen.grid(row=1, column=1, sticky="w", pady=2, padx=10)
        self.make_draggable(lbl_gen)
        
        self.lbl_gen_val = tk.Label(input_card, text="⚡ 0.00 MWe", bg=BG_MAIN, fg=TEXT_LIGHT, font=("Consolas", 11, "bold"))
        self.lbl_gen_val.grid(row=2, column=1, sticky="w", pady=(0, 10), padx=10)
        self.make_draggable(self.lbl_gen_val)

        lbl_feed = tk.Label(input_card, text="FEEDWATER FLOW", bg=BG_MAIN, fg=TEXT_MUTED, font=("Consolas", 8, "bold"))
        lbl_feed.grid(row=3, column=1, sticky="w", pady=2, padx=10)
        self.make_draggable(lbl_feed)
        
        self.lbl_feed_val = tk.Label(input_card, text="💧 0.00 kg/s", bg=BG_MAIN, fg=TEXT_LIGHT, font=("Consolas", 11, "bold"))
        self.lbl_feed_val.grid(row=4, column=1, sticky="w", pady=(0, 10), padx=10)
        self.make_draggable(self.lbl_feed_val)

        self.neon_frame = tk.Frame(container, bg=BG_CARD, padx=8, pady=8, bd=1, relief="solid")
        self.neon_frame.pack(fill="x", side="bottom", pady=(5, 0))
        self.make_draggable(self.neon_frame)

        self.lbl_neon_rtp = tk.Label(self.neon_frame, text="0.0% RTP", bg=BG_CARD, fg=ACCENT_CYAN, 
                                     font=("Consolas", 18, "bold"))
        self.lbl_neon_rtp.pack(anchor="center")
        self.make_draggable(self.lbl_neon_rtp)

        self.lbl_neon_sub = tk.Label(self.neon_frame, text="⚡ APRM REACTOR POWER STATUS", bg=BG_CARD, fg=TEXT_MUTED, 
                                     font=("Consolas", 8, "bold"))
        self.lbl_neon_sub.pack(anchor="center", pady=(2, 0))
        self.make_draggable(self.lbl_neon_sub)

        self.lbl_debug = tk.Label(container, text="[ OCR DIAG: STANDBY ]", bg=BG_MAIN, fg=TEXT_MUTED,
                                  font=("Consolas", 7))
        self.lbl_debug.pack(side="bottom", fill="x", pady=(4, 0))

        self.update_scan_button_styles()

    def build_compact_layout(self):
        compact_frame = tk.Frame(self.root, bg=BG_HEADER, padx=8, pady=5)
        compact_frame.pack(fill="both", expand=True)
        self.make_draggable(compact_frame)
        compact_frame.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        handle = tk.Label(compact_frame, text="⋮⋮", bg=BG_HEADER, fg=TEXT_MUTED, font=("Segoe UI", 12, "bold"), cursor="fleur")
        handle.pack(side="left", padx=(0, 5))
        self.make_draggable(handle)
        handle.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        unit_text = f"U{self.calc.selected_unit}"
        self.btn_compact_unit = tk.Label(compact_frame, text=unit_text, bg=BG_CARD, fg=ACCENT_CYAN,
                                         font=("Segoe UI", 8, "bold"), padx=4, pady=2, cursor="hand2")
        self.btn_compact_unit.pack(side="left", padx=2)
        self.btn_compact_unit.bind("<Button-1>", lambda e: self.toggle_compact_unit())

        lbl_mw = tk.Label(compact_frame, text="MWt:", bg=BG_HEADER, fg=TEXT_MUTED, font=("Segoe UI", 8, "bold"))
        lbl_mw.pack(side="left", padx=2)
        self.make_draggable(lbl_mw)

        btn_min10 = tk.Label(compact_frame, text="-", bg=BG_CARD, fg=ACCENT_CYAN, 
                             font=("Segoe UI", 9, "bold"), padx=4, pady=1, cursor="hand2")
        btn_min10.pack(side="left", padx=(2, 1))
        btn_min10.bind("<Button-1>", lambda e: self.adjust_demand(-10))
        btn_min10.bind("<Enter>", lambda e: btn_min10.config(fg=TEXT_LIGHT))
        btn_min10.bind("<Leave>", lambda e: btn_min10.config(fg=ACCENT_CYAN))

        self.btn_compact_scan = tk.Label(compact_frame, font=("Segoe UI", 9, "bold"), padx=4, pady=1, cursor="hand2", bg=BG_HEADER)
        self.btn_compact_scan.pack(side="left", padx=2)
        self.btn_compact_scan.bind("<Button-1>", lambda e: self.toggle_auto_scan())
        self.btn_compact_scan.bind("<Enter>", self.on_compact_scan_enter)
        self.btn_compact_scan.bind("<Leave>", self.on_compact_scan_leave)

        self.ent_demand = tk.Entry(compact_frame, textvariable=self.var_demand, bg=BG_MAIN, fg=TEXT_LIGHT,
                                   insertbackground=TEXT_LIGHT, font=("Consolas", 10, "bold"), bd=0,
                                   highlightthickness=1, highlightcolor=ACCENT_CYAN, highlightbackground=BG_CARD,
                                   width=6, justify="center")
        self.ent_demand.pack(side="left", padx=2)

        btn_add10 = tk.Label(compact_frame, text="+", bg=BG_CARD, fg=ACCENT_CYAN, 
                             font=("Segoe UI", 9, "bold"), padx=4, pady=1, cursor="hand2")
        btn_add10.pack(side="left", padx=(1, 2))
        btn_add10.bind("<Button-1>", lambda e: self.adjust_demand(10))
        btn_add10.bind("<Enter>", lambda e: btn_add10.config(fg=TEXT_LIGHT))
        btn_add10.bind("<Leave>", lambda e: btn_add10.config(fg=ACCENT_CYAN))

        lbl_arrow = tk.Label(compact_frame, text="➔", bg=BG_HEADER, fg=ACCENT_CYAN, font=("Segoe UI", 10, "bold"))
        lbl_arrow.pack(side="left", padx=2)
        self.make_draggable(lbl_arrow)
        lbl_arrow.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        self.lbl_compact_rtp = tk.Label(compact_frame, text="0.0% RTP", bg=BG_HEADER, fg=ACCENT_CYAN,
                                        font=("Consolas", 11, "bold"))
        self.lbl_compact_rtp.pack(side="left", padx=5)
        self.make_draggable(self.lbl_compact_rtp)
        self.lbl_compact_rtp.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        self.lbl_compact_flow = tk.Label(compact_frame, text="[0 kg/s]", bg=BG_HEADER, fg=TEXT_MUTED,
                                         font=("Consolas", 9))
        self.lbl_compact_flow.pack(side="left", padx=2)
        self.make_draggable(self.lbl_compact_flow)
        self.lbl_compact_flow.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        btn_close = tk.Label(compact_frame, text="✕", bg=BG_HEADER, fg=TEXT_MUTED, font=("Segoe UI", 9, "bold"), cursor="hand2")
        btn_close.pack(side="right", padx=2)
        btn_close.bind("<Button-1>", lambda e: self.quit_app())
        btn_close.bind("<Enter>", lambda e: btn_close.config(fg=ACCENT_RED))
        btn_close.bind("<Leave>", lambda e: btn_close.config(fg=TEXT_MUTED))

        btn_exp = tk.Label(compact_frame, text="⛶", bg=BG_HEADER, fg=TEXT_MUTED, font=("Segoe UI", 9), cursor="hand2")
        btn_exp.pack(side="right", padx=6)
        btn_exp.bind("<Button-1>", lambda e: self.toggle_compact())
        btn_exp.bind("<Enter>", lambda e: btn_exp.config(fg=ACCENT_CYAN))
        btn_exp.bind("<Leave>", lambda e: btn_exp.config(fg=TEXT_MUTED))

        self.update_scan_button_styles()

    def adjust_demand(self, amount):
        try:
            val = float(self.var_demand.get() or "0")
        except ValueError:
            val = 0.0
        new_val = max(0.0, val + amount)
        self.var_demand.set(f"{new_val:.2f}" if not self.is_compact else f"{int(new_val)}")

    def select_unit(self, unit):
        self.calc.selected_unit = unit
        self.update_unit_ui_state()
        self.update_calculations(source="demand")
        self.save_settings()

    def toggle_compact_unit(self):
        next_unit = 2 if self.calc.selected_unit == 1 else 1
        self.calc.selected_unit = next_unit
        self.btn_compact_unit.config(text=f"U{next_unit}")
        self.update_calculations(source="demand")
        self.save_settings()

    def setup_tray_icon(self):
        try:
            import pystray
            from PIL import Image
            
            if os.path.exists("icon.png"):
                image = Image.open("icon.png")
            else:
                image = self.icon_image_pil
            
            menu = pystray.Menu(
                pystray.MenuItem("Show / Restore", lambda icon, item: self.restore_window(), default=True),
                pystray.MenuItem("Toggle Compact Mode", lambda icon, item: self.toggle_compact()),
                pystray.MenuItem("Always on Top", lambda icon, item: self.toggle_topmost()),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", lambda icon, item: self.quit_app())
            )
            
            self.tray = pystray.Icon("RBWR APR Calculator", image, f"RBWR APR Calculator v{__version__}", menu)
            threading.Thread(target=self.tray.run, daemon=True).start()
        except Exception:
            self.tray = None

    def load_settings(self):
        defaults = {
            "usage": 61.32,
            "opacity": 0.90,
            "selected_unit": 1,
            "hotkey": "F7",
            "is_compact": False,
            "is_topmost": True,
            "enable_hud_scan": True,
            "skipped_version": ""
        }
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r") as f:
                    data = json.load(f)
                    defaults.update(data)
        except Exception:
            pass
        return defaults

    def save_settings(self):
        try:
            data = {
                "usage": self.calc.usage,
                "opacity": self.root.attributes("-alpha"),
                "selected_unit": self.calc.selected_unit,
                "hotkey": self.var_hotkey.get(),
                "is_compact": self.is_compact,
                "is_topmost": self.is_topmost,
                "enable_hud_scan": self.var_hud_scan.get(),
                "skipped_version": getattr(self, 'skipped_version', "")
            }
            with open(CONFIG_FILE, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def restore_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.attributes("-topmost", self.is_topmost)

    def open_log_file(self):
        try:
            if os.path.exists(_log_path):
                os.startfile(_log_path)
            else:
                from tkinter import messagebox
                messagebox.showinfo("Log File", f"Log file not found at:\n{_log_path}")
        except Exception as e:
            log.error(f"Failed to open log file: {e}")

    def quit_app(self):
        self.hotkey_thread_active = False
        try:
            ctypes.windll.user32.UnregisterHotKey(None, 101)
        except Exception:
            pass
        if hasattr(self, 'tray') and self.tray:
            try:
                self.tray.stop()
            except Exception:
                pass
        self.root.destroy()
        sys.exit(0)

    def get_ocr_model_paths(self):
        import os
        import sys
        
        det_name = "ch_PP-OCRv3_det_infer.onnx"
        rec_name = "ch_PP-OCRv3_rec_infer.onnx"
        cls_name = "ch_PP-OCRv3_cls_infer.onnx"
        
        possible_dirs = []
        
        try:
            import rapidocr_onnxruntime
            pkg_dir = os.path.dirname(os.path.abspath(rapidocr_onnxruntime.__file__))
            possible_dirs.append(os.path.join(pkg_dir, "models"))
        except Exception:
            pass
            
        main_dir = os.path.dirname(os.path.abspath(__file__))
        exe_dir = os.path.dirname(sys.executable)
        
        possible_dirs.extend([
            os.path.join(exe_dir, "rapidocr_onnxruntime", "models"),
            os.path.join(exe_dir, "models"),
            os.path.join(main_dir, "rapidocr_onnxruntime", "models"),
            os.path.join(main_dir, "models"),
            os.path.join(main_dir, "venv", "Lib", "site-packages", "rapidocr_onnxruntime", "models"),
        ])
        
        debug_info = []
        
        for d in possible_dirs:
            det_p = os.path.join(d, det_name)
            rec_p = os.path.join(d, rec_name)
            cls_p = os.path.join(d, cls_name)
            exists = os.path.exists(det_p)
            debug_info.append(f"{d} (det={exists}, rec={os.path.exists(rec_p)}, cls={os.path.exists(cls_p)})")
            if exists and os.path.exists(rec_p):
                self.log_diag(f"Found OCR models in {d}", "success")
                paths = {
                    "det_model_path": det_p,
                    "rec_model_path": rec_p,
                    "use_cls": False,
                    "limit_side_len": 720
                }
                # cls model is optional — only include if it actually exists
                if os.path.exists(cls_p):
                    paths["cls_model_path"] = cls_p
                else:
                    log.warning(f"cls model not found at {cls_p}, skipping (classification is optional)")
                return paths
                
        print("OCR Model check failed. Searched in:")
        for dbg in debug_info:
            print(" -", dbg)
        self.log_diag("OCR Model Paths not found.", "error")
        return {}

    def initialize_ocr(self):
        try:
            paths = self.get_ocr_model_paths()
            log.info(f"Initializing RapidOCR with paths: {paths}")
            
            # Monkey-patch init_module to use fully-qualified package imports.
            # RapidOCR uses importlib.import_module('ch_ppocr_v3_det') with a 
            # sys.path hack, which breaks inside Nuitka's compiled bundle.
            _original_init_module = RapidOCR.init_module  # pyright: ignore[reportOptionalMemberAccess]
            
            @staticmethod
            def _patched_init_module(module_name, class_name):
                import importlib
                # Try the fully-qualified package path first
                qualified = f"rapidocr_onnxruntime.{module_name}"
                try:
                    log.info(f"Importing OCR module: {qualified}.{class_name}")
                    mod = importlib.import_module(qualified)
                    return getattr(mod, class_name)
                except (ImportError, AttributeError):
                    log.info(f"Qualified import failed, falling back to: {module_name}")
                    return _original_init_module(module_name, class_name)
            
            RapidOCR.init_module = _patched_init_module
            
            self.ocr_engine = RapidOCR(**paths)  # pyright: ignore[reportOptionalCall]
            log.info("RapidOCR engine initialized successfully!")
        except Exception as e:
            log.error(f"Failed to initialize RapidOCR engine: {e}")
            log.error(traceback.format_exc())
            self.log_diag(f"Init fail: {e}", "error")
        finally:
            self.ocr_initializing = False
            self.root.after(0, self.update_scan_button_styles)

    def toggle_auto_scan(self):
        if not HAS_OCR:
            from tkinter import messagebox
            messagebox.showinfo("Screen Reader", 
                                "To enable automatic screen scanning, please install the OCR package:\n\n"
                                "pip install rapidocr-onnxruntime pillow\n\n"
                                "And compile using compile.bat.")
            return

        if self.ocr_initializing:
            from tkinter import messagebox
            messagebox.showinfo("Screen Reader", "Initializing OCR engine models. Please wait a few seconds...")
            return

        if not self.ocr_engine:
            try:
                paths = self.get_ocr_model_paths()
                log.info(f"Retrying RapidOCR init with paths: {paths}")
                self.ocr_engine = RapidOCR(**paths)  # pyright: ignore[reportOptionalCall]
                log.info("RapidOCR engine initialized successfully on retry!")
            except Exception as e:
                log.error(f"Failed to initialize RapidOCR on retry: {e}")
                log.error(traceback.format_exc())
                from tkinter import messagebox
                messagebox.showerror("Screen Reader", f"Failed to initialize OCR engine models.\n\nError: {e}\n\nCheck rbwr_overlay.log for details.")
                return

        self.auto_scan_active = not self.auto_scan_active
        self.update_scan_button_styles()

    def update_scan_button_styles(self):
        if hasattr(self, 'btn_scan') and self.btn_scan and self.btn_scan.winfo_exists():
            if not HAS_OCR:
                self.btn_scan.config(text="🔍 N/A", bg=BG_CARD, fg="#3a3d46")
            elif self.ocr_initializing:
                self.btn_scan.config(text="🔍 INIT", bg=BG_CARD, fg=ACCENT_GOLD)
            elif self.auto_scan_active:
                self.btn_scan.config(text="🔍 ON", bg=ACCENT_GREEN, fg=BG_MAIN)
            else:
                self.btn_scan.config(text="🔍 OFF", bg=BG_CARD, fg=ACCENT_CYAN)

        if hasattr(self, 'btn_compact_scan') and self.btn_compact_scan and self.btn_compact_scan.winfo_exists():
            if not HAS_OCR:
                self.btn_compact_scan.config(text="🔍", fg="#3a3d46")
            elif self.ocr_initializing:
                self.btn_compact_scan.config(text="⏳", fg=ACCENT_GOLD)
            elif self.auto_scan_active:
                self.btn_compact_scan.config(text="🔴", fg=ACCENT_RED)
            else:
                self.btn_compact_scan.config(text="🔍", fg=ACCENT_CYAN)

    def on_scan_enter(self, e):
        if not HAS_OCR or self.ocr_initializing:
            return
        if hasattr(self, 'btn_scan') and self.btn_scan and self.btn_scan.winfo_exists():
            if self.auto_scan_active:
                self.btn_scan.config(bg=BG_HEADER, fg=ACCENT_GREEN)
            else:
                self.btn_scan.config(bg=BG_HEADER, fg=TEXT_LIGHT)

    def on_scan_leave(self, e):
        self.update_scan_button_styles()

    def on_compact_scan_enter(self, e):
        if not HAS_OCR or self.ocr_initializing:
            return
        if hasattr(self, 'btn_compact_scan') and self.btn_compact_scan and self.btn_compact_scan.winfo_exists():
            if self.auto_scan_active:
                self.btn_compact_scan.config(fg=TEXT_LIGHT)
            else:
                self.btn_compact_scan.config(fg=TEXT_LIGHT)

    def on_compact_scan_leave(self, e):
        self.update_scan_button_styles()

    def scan_loop(self):
        import time
        while True:
            if self.auto_scan_active and self.ocr_engine:
                success = self.perform_screen_scan()
                if success:
                    self.auto_scan_active = False
                    self.root.after(0, self.update_scan_button_styles)
            time.sleep(1.0)

    def start_hotkey_listener(self):
        if hasattr(self, 'hotkey_thread_active') and self.hotkey_thread_active:
            self.hotkey_thread_active = False
            try:
                ctypes.windll.user32.UnregisterHotKey(None, 101)
            except Exception:
                pass
            
        self.hotkey_thread_active = True
        threading.Thread(target=self.hotkey_loop, daemon=True).start()

    def hotkey_loop(self):
        import time
        from ctypes import wintypes
        user32 = ctypes.windll.user32

        VK_MAP = {}
        # F1-F12
        for i in range(1, 13):
            VK_MAP[f"F{i}"] = 0x6F + i
        # Letters A-Z
        for char_code in range(65, 91):
            VK_MAP[chr(char_code)] = char_code
        # Numbers 0-9
        for num in range(10):
            VK_MAP[str(num)] = 0x30 + num
            
        # Add basic symbols
        VK_MAP["SPACE"] = 0x20
        VK_MAP["TAB"] = 0x09
        VK_MAP["RETURN"] = 0x0D
        
        time.sleep(0.5)
        
        current_key = self.var_hotkey.get().upper()
        vk = VK_MAP.get(current_key)
        if vk is None:
            self.log_diag(f"Key {current_key} not globally bindable", "warning")
            return

        user32.UnregisterHotKey(None, 101)
        if not user32.RegisterHotKey(None, 101, 0, vk):
            self.log_diag(f"Hotkey register failed for {current_key}", "error")
            return
            
        self.log_diag(f"Bound global hotkey: {current_key}", "success")

        msg = wintypes.MSG()
        while self.hotkey_thread_active:
            if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1): # PM_REMOVE = 1
                if msg.message == 0x0312:  # WM_HOTKEY
                    self.root.after(0, self.toggle_auto_scan)
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.05)
            
        user32.UnregisterHotKey(None, 101)

    def listen_for_hotkey(self):
        self.btn_hotkey_bind.config(text="[ PRESS KEY... ]", fg=ACCENT_GOLD, bg=BG_HEADER)
        self.root.bind("<Key>", self.on_hotkey_captured)
        self.root.focus_set()

    def on_hotkey_captured(self, event):
        self.root.unbind("<Key>")
        key = event.keysym.upper()
        
        if key == "ESCAPE":
            self.btn_hotkey_bind.config(text=self.var_hotkey.get(), fg=ACCENT_CYAN, bg=BG_MAIN)
            return

        # Map common keysym representations to standard names
        if key == "SPACE":
            pass
        elif key == "RETURN":
            pass
        elif len(key) == 1 and (key.isalpha() or key.isdigit()):
            pass
        elif key.startswith("F") and len(key) > 1 and key[1:].isdigit():
            pass
        else:
            if len(key) > 6:
                key = key[:6]

        self.var_hotkey.set(key)
        self.btn_hotkey_bind.config(text=key, fg=ACCENT_GREEN, bg=BG_MAIN)
        self.save_settings()

    def perform_screen_scan(self):
        try:
            rect = get_active_window_rect()
            if not rect:
                self.log_diag("No active window", "error")
                return False

            left, top, width, height = rect

            hwnd = ctypes.windll.user32.GetForegroundWindow()
            buffer_len = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
            buffer = ctypes.create_unicode_buffer(buffer_len)
            ctypes.windll.user32.GetWindowTextW(hwnd, buffer, buffer_len)
            window_title = buffer.value

            if "Roblox" not in window_title and "Realistic" not in window_title:
                self.log_diag("Roblox not focused", "warning")
                return False

            from PIL import ImageGrab

            found = False
            if self.var_hud_scan.get():
                crop_w = 800
                crop_h = 320
                x_offset = 20
                y_offset = -20
                x1_hud = left + 10 + x_offset
                y1_hud = top + height - crop_h - 10 + y_offset
                x2_hud = x1_hud + crop_w
                y2_hud = y1_hud + crop_h

                self.log_diag("HUD scan stage...", "info")
                screenshot = ImageGrab.grab(bbox=(x1_hud, y1_hud, x2_hud, y2_hud), all_screens=True)
                found = self.process_ocr_image(screenshot, stage="HUD")
                if found:
                    return True

            if not found:
                self.log_diag("HUD miss. Full screen stage...", "info")
                x1_full = left
                y1_full = top
                x2_full = x1_full + width
                y2_full = y1_full + height
                screenshot_full = ImageGrab.grab(bbox=(x1_full, y1_full, x2_full, y2_full), all_screens=True)
                return self.process_ocr_image(screenshot_full, stage="FULL")
            return False

        except Exception as e:
            self.log_diag(f"Scan crash: {str(e)}", "error")
            return False

    def process_ocr_image(self, img, stage=""):
        engine = self.ocr_engine
        if not engine:
            self.log_diag("OCR not ready yet", "warning")
            return False
        
        try:
            import numpy as np
            img_np = np.array(img.convert('RGB'))
            result, _ = engine(img_np)
            if not result:
                self.log_diag(f"No text read in {stage}", "warning")
                return False

            text_lines = [line[1] for line in result]
            full_text = " ".join(text_lines).strip()

            cleaned = re.sub(r'[\s\-_:=|\\/\[\]\(\)]+', '', full_text)

            next_match = re.search(r'(?i)NextDe[mr]a?nd?U([12lIz|ZzsS])(\*+|\d+)', cleaned)
            demand_match = re.search(r'(?i)DemandU([12lIz|ZzsS])(\d+)', cleaned)

            detected_unit = None
            detected_demand = None

            if next_match:
                unit_char = next_match.group(1).lower()
                if unit_char in ('1', 'l', 'i', '|'):
                    detected_unit = 1
                elif unit_char in ('2', 'z', 's'):
                    detected_unit = 2
                
                val_str = next_match.group(2)
                if '*' in val_str or not val_str.isdigit():
                    if demand_match:
                        dem_unit_char = demand_match.group(1).lower()
                        if dem_unit_char in ('1', 'l', 'i', '|'):
                            detected_unit = 1
                        elif dem_unit_char in ('2', 'z', 's'):
                            detected_unit = 2
                        detected_demand = float(demand_match.group(2))
                else:
                    detected_demand = float(val_str)
            elif demand_match:
                unit_char = demand_match.group(1).lower()
                if unit_char in ('1', 'l', 'i', '|'):
                    detected_unit = 1
                elif unit_char in ('2', 'z', 's'):
                    detected_unit = 2
                detected_demand = float(demand_match.group(2))

            if detected_demand is not None:
                self.log_diag(f"Matched HUD: U{detected_unit or '?'}({detected_demand})", "success")
                self.root.after(0, lambda: self.apply_auto_telemetry(detected_unit, detected_demand))
                return True

            match_net = re.search(r'(?i)Network\s*dem[a-z0-9]*\s*[:\s]+(\d+)(?:\s*\(\s*(\d+)\s*\))?', full_text)
            if match_net:
                val1 = float(match_net.group(1))
                val2 = float(match_net.group(2)) if match_net.group(2) else None
                
                if self.calc.selected_unit == 1:
                     detected_demand = val1
                else:
                    if val2 is not None:
                        if val2 > val1:
                            detected_demand = val2 - val1
                        else:
                            detected_demand = val2
                    else:
                        detected_demand = val1
                
                self.log_diag(f"Matched Net: D({detected_demand})", "success")
                self.root.after(0, lambda: self.apply_auto_telemetry(self.calc.selected_unit, detected_demand))
                return True

            match_fallback = re.search(r'(?i)Demand(\d+)', cleaned)
            if match_fallback:
                detected_demand = float(match_fallback.group(1))
                self.log_diag(f"Matched Fallback: D({detected_demand})", "success")
                self.root.after(0, lambda: self.apply_auto_telemetry(None, detected_demand))
                return True

            match_generic = re.search(r'(?i)(?:demand|load|dem)[A-Za-z]*(\d+)', cleaned)
            if match_generic:
                detected_demand = float(match_generic.group(1))
                self.log_diag(f"Matched Generic: D({detected_demand})", "success")
                self.root.after(0, lambda: self.apply_auto_telemetry(None, detected_demand))
                return True

            snippet = (full_text[:20] + "...") if len(full_text) > 20 else full_text
            self.log_diag(f"Unmatched: '{snippet}'", "warning")
            return False
        except Exception as e:
            self.log_diag(f"OCR process fail: {str(e)}", "error")
            return False

    def apply_auto_telemetry(self, unit, demand):
        if self.updating_fields:
            return

        if unit is not None and self.calc.selected_unit != unit:
            self.select_unit(unit)

        current_val = self.var_demand.get()
        try:
            current_float = float(current_val)
        except ValueError:
            current_float = -1.0

        if abs(current_float - demand) > 0.1:
            self.var_demand.set(f"{demand:.2f}" if not self.is_compact else f"{int(demand)}")

    def log_diag(self, message, level="info"):
        log_fn = getattr(log, level if level != "success" else "info", log.info)
        log_fn(f"[DIAG] {message}")
        if hasattr(self, 'lbl_debug') and self.lbl_debug and self.lbl_debug.winfo_exists():
            color = TEXT_MUTED
            if level == "error":
                color = ACCENT_RED
            elif level == "success":
                color = ACCENT_GREEN
            elif level == "warning":
                color = ACCENT_GOLD
            elif level == "info":
                color = ACCENT_CYAN
            self.root.after(0, lambda: self.lbl_debug.config(text=f"[ OCR: {message.upper()} ]", fg=color))

    def update_unit_ui_state(self):
        if hasattr(self, 'btn_u1') and hasattr(self, 'btn_u2'):
            if self.calc.selected_unit == 1:
                self.btn_u1.config(bg=BG_CARD, fg=ACCENT_CYAN, text="❖ UNIT 01 ❖", bd=1, relief="solid")
                self.btn_u2.config(bg=BG_MAIN, fg=TEXT_MUTED, text="  UNIT 02  ", bd=0, relief="flat")
            else:
                self.btn_u1.config(bg=BG_MAIN, fg=TEXT_MUTED, text="  UNIT 01  ", bd=0, relief="flat")
                self.btn_u2.config(bg=BG_CARD, fg=ACCENT_CYAN, text="❖ UNIT 02 ❖", bd=1, relief="solid")

    def toggle_config_panel(self):
        self.show_config = not self.show_config
        arrow = "▼" if self.show_config else "▲"
        self.lbl_config_toggle.config(text=f"⚙ Configuration Settings {arrow}")
        
        target_h = 420 + (160 if self.show_config else 0)
        self.root.geometry(f"{self.width_detailed}x{target_h}")
        self.create_widgets()
        self.update_calculations(source="demand")

    def on_usage_change(self, *args):
        self.calc.set_usage(self.var_usage.get())
        self.update_calculations(source="demand")
        self.save_settings()

    def on_opacity_change(self, value):
        try:
            alpha = float(value)
            self.root.attributes("-alpha", alpha)
            self.save_settings()
        except ValueError:
            pass

    def toggle_hud_scan_setting(self):
        new_val = not self.var_hud_scan.get()
        self.var_hud_scan.set(new_val)
        if hasattr(self, 'btn_hud_scan_toggle') and self.btn_hud_scan_toggle.winfo_exists():
            self.btn_hud_scan_toggle.config(text="🟢 ENABLED" if new_val else "🔴 DISABLED",
                                            fg=ACCENT_GREEN if new_val else ACCENT_RED)
        self.save_settings()

    def check_for_updates(self):
        if not _is_compiled:
            return
            
        def run_check():
            import urllib.request
            import json
            try:
                threading.Event().wait(1.5)
                
                url = f"{UPDATE_SERVER_URL}/version/latest"
                req = urllib.request.Request(url, headers=UPDATE_HTTP_HEADERS)
                with urllib.request.urlopen(req, timeout=3) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        latest_version = data.get("version")
                        if latest_version and latest_version != __version__:
                            if latest_version != self.skipped_version:
                                release_notes = data.get("notes", "No release details available.")
                                filename = data.get("filename", f"rbwr_overlay_v{latest_version}.exe")
                                self.root.after(0, lambda: self.show_update_dialog(latest_version, release_notes, filename))
            except Exception as e:
                log.info(f"Update check skipped/failed (server offline): {e}")
                
        threading.Thread(target=run_check, daemon=True).start()

    def show_update_dialog(self, latest_version, release_notes, download_filename):
        popup = tk.Toplevel(self.root)
        popup.title("Update Available")
        popup.geometry("380x260")
        popup.configure(bg=BG_CARD, highlightbackground=ACCENT_CYAN, highlightcolor=ACCENT_CYAN, highlightthickness=1)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        
        x = self.root.winfo_x() + (self.root.winfo_width() - 380) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 260) // 2
        popup.geometry(f"+{x}+{y}")
        
        title_bar = tk.Frame(popup, bg=BG_HEADER, height=30)
        title_bar.pack(fill="x", side="top")
        
        title_lbl = tk.Label(title_bar, text=" ⚡ SYSTEM UPDATE AVAILABLE", bg=BG_HEADER, fg=ACCENT_GOLD,
                             font=("Consolas", 9, "bold"))
        title_lbl.pack(side="left", padx=10, pady=5)
        
        content_frame = tk.Frame(popup, bg=BG_CARD, padx=15, pady=15)
        content_frame.pack(fill="both", expand=True)
        
        msg_lbl = tk.Label(content_frame, text=f"A new version (v{latest_version}) is ready!\nYour version: v{__version__}", 
                           bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 10, "bold"), justify="left")
        msg_lbl.pack(anchor="w", pady=(0, 10))
        
        notes_lbl = tk.Label(content_frame, text=f"Release Notes:\n{release_notes}", 
                             bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8), justify="left", wraplength=340)
        notes_lbl.pack(anchor="w", pady=(0, 15))
        
        btn_frame = tk.Frame(content_frame, bg=BG_CARD)
        btn_frame.pack(fill="x", side="bottom")
        
        def start_update():
            popup.destroy()
            self.execute_self_update(latest_version, download_filename)
            
        def skip_version():
            popup.destroy()
            self.skipped_version = latest_version
            self.save_settings()
            
        def remind_later():
            popup.destroy()
            
        btn_update = tk.Label(btn_frame, text="Update Now", bg=BG_MAIN, fg=ACCENT_GREEN,
                              font=("Segoe UI", 9, "bold"), bd=1, relief="solid", padx=10, pady=5, cursor="hand2")
        btn_update.pack(side="left", expand=True, fill="x", padx=3)
        btn_update.bind("<Button-1>", lambda e: start_update())
        btn_update.bind("<Enter>", lambda e: btn_update.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_update.bind("<Leave>", lambda e: btn_update.config(bg=BG_MAIN, fg=ACCENT_GREEN))
        
        btn_skip = tk.Label(btn_frame, text="Skip Version", bg=BG_MAIN, fg=ACCENT_RED,
                            font=("Segoe UI", 9, "bold"), bd=1, relief="solid", padx=10, pady=5, cursor="hand2")
        btn_skip.pack(side="left", expand=True, fill="x", padx=3)
        btn_skip.bind("<Button-1>", lambda e: skip_version())
        btn_skip.bind("<Enter>", lambda e: btn_skip.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_skip.bind("<Leave>", lambda e: btn_skip.config(bg=BG_MAIN, fg=ACCENT_RED))
        
        btn_cancel = tk.Label(btn_frame, text="Later", bg=BG_MAIN, fg=TEXT_MUTED,
                              font=("Segoe UI", 9, "bold"), bd=1, relief="solid", padx=10, pady=5, cursor="hand2")
        btn_cancel.pack(side="left", expand=True, fill="x", padx=3)
        btn_cancel.bind("<Button-1>", lambda e: remind_later())
        btn_cancel.bind("<Enter>", lambda e: btn_cancel.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_cancel.bind("<Leave>", lambda e: btn_cancel.config(bg=BG_MAIN, fg=TEXT_MUTED))

    def execute_self_update(self, latest_version, download_filename):
        loading = tk.Toplevel(self.root)
        loading.title("Downloading Update")
        loading.geometry("300x120")
        loading.configure(bg=BG_CARD, highlightbackground=ACCENT_CYAN, highlightcolor=ACCENT_CYAN, highlightthickness=1)
        loading.overrideredirect(True)
        loading.attributes("-topmost", True)
        
        x = self.root.winfo_x() + (self.root.winfo_width() - 300) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 120) // 2
        loading.geometry(f"+{x}+{y}")
        
        lbl_status = tk.Label(loading, text="⚡ DOWNLOADING SYSTEM UPDATE...", bg=BG_CARD, fg=ACCENT_CYAN, font=("Consolas", 10, "bold"))
        lbl_status.pack(pady=(25, 5))
        
        lbl_sub = tk.Label(loading, text=f"Fetching v{latest_version}...", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8))
        lbl_sub.pack(pady=(0, 15))
        
        def do_download():
            import urllib.request
            import subprocess
            import sys
            from tkinter import messagebox
            
            try:
                current_exe = sys.executable
                exe_dir = os.path.dirname(os.path.abspath(current_exe))
                new_exe_path = os.path.join(exe_dir, download_filename)
                
                url = f"{UPDATE_SERVER_URL}/download/{latest_version}"
                req = urllib.request.Request(url, headers=UPDATE_HTTP_HEADERS)
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status == 200:
                        with open(new_exe_path, "wb") as f:
                            f.write(response.read())
                
                lbl_status.config(text="⚡ REBOOTING OVERLAY...", fg=ACCENT_GREEN)
                lbl_sub.config(text="Deleting old version & starting new one...")
                loading.update()
                
                threading.Event().wait(1.0)
                
                cmd_script = f'timeout /t 2 /nobreak && del "{current_exe}" && start "" "{new_exe_path}"'
                subprocess.Popen(f'cmd.exe /c {cmd_script}', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                
                self.root.after(0, self.quit_app)
            except Exception as err:
                log.error(f"Self-update failed: {err}")
                self.root.after(0, lambda: [
                    loading.destroy(),
                    messagebox.showerror("Update Error", f"Failed to execute self-update:\n{err}")
                ])
                
        threading.Thread(target=do_download, daemon=True).start()

    def on_input_update(self, source):
        if self.updating_fields:
            return
        self.update_calculations(source=source)

    def update_calculations(self, source="demand"):
        self.updating_fields = True
        try:
            if source == "demand":
                raw_val = self.var_demand.get()
                if not raw_val:
                    demand_val = 0.0
                else:
                    try:
                        demand_val = float(raw_val)
                    except ValueError:
                        demand_val = -1.0

                if demand_val < 0:
                    self.show_error_state()
                else:
                    thermal = self.calc.calc_thermal(demand_val)
                    flow = self.calc.calc_flow(thermal)
                    gen_load = self.calc.calc_gen_load(thermal)
                    
                    self.var_rtp.set(f"{thermal:.3f}")
                    
                    self.render_outputs(thermal, flow, gen_load)
            
            elif source == "rtp":
                raw_val = self.var_rtp.get()
                if not raw_val:
                    thermal_val = 0.0
                else:
                    try:
                        thermal_val = float(raw_val)
                    except ValueError:
                        thermal_val = -1.0

                if thermal_val < 0 or thermal_val > 250:
                    self.show_error_state()
                else:
                    flow = self.calc.calc_flow(thermal_val)
                    gen_load = self.calc.calc_gen_load(thermal_val)
                    demand = round(gen_load - self.calc.usage, 2)
                    if demand < 0:
                        demand = 0.0
                    
                    self.var_demand.set(f"{demand:.2f}")
                    
                    self.render_outputs(thermal_val, flow, gen_load)
        except Exception as e:
            self.show_error_state()
        finally:
            self.updating_fields = False

    def render_outputs(self, thermal, flow, gen_load):
        limit = 110 if self.calc.selected_unit == 1 else 115
        if not self.is_compact:
            self.lbl_gen_val.config(text=f"⚡ {gen_load:.2f} MWe", fg=ACCENT_CYAN)
            self.lbl_feed_val.config(text=f"💧 {flow:.2f} kg/s", fg=ACCENT_GOLD)
            self.lbl_neon_rtp.config(text=f"{thermal:.2f}% RTP")
            
            if thermal > limit:
                self.neon_frame.config(bg="#2a0c0e", highlightbackground=ACCENT_RED, bd=1)
                self.lbl_neon_rtp.config(bg="#2a0c0e", fg=ACCENT_RED)
                self.lbl_neon_sub.config(text=f"⚠️ OVERPOWER SCRAM RISK (>{limit}%)", bg="#2a0c0e", fg=ACCENT_RED)
            else:
                self.neon_frame.config(bg=BG_CARD, highlightbackground=BG_CARD, bd=0)
                self.lbl_neon_rtp.config(bg=BG_CARD, fg=ACCENT_CYAN)
                self.lbl_neon_sub.config(text="⚡ APRM REACTOR POWER STATUS", bg=BG_CARD, fg=TEXT_MUTED)
        else:
            if thermal > limit:
                self.lbl_compact_rtp.config(text=f"{thermal:.1f}% RTP ⚠️", fg=ACCENT_RED)
            else:
                self.lbl_compact_rtp.config(text=f"{thermal:.1f}% RTP", fg=ACCENT_CYAN)
            self.lbl_compact_flow.config(text=f"[{int(flow)} kg/s]", fg=TEXT_MUTED)

    def show_error_state(self):
        if not self.is_compact:
            self.lbl_gen_val.config(text="⚠️ ERROR", fg=ACCENT_RED)
            self.lbl_feed_val.config(text="⚠️ ERROR", fg=ACCENT_RED)
            self.lbl_neon_rtp.config(text="ERR", fg=ACCENT_RED)
            self.neon_frame.config(bg=BG_CARD, bd=0)
            self.lbl_neon_rtp.config(bg=BG_CARD)
            self.lbl_neon_sub.config(text="⚠️ VALUE OUT OF RANGE", bg=BG_CARD, fg=ACCENT_RED)
        else:
            self.lbl_compact_rtp.config(text="ERR", fg=ACCENT_RED)
            self.lbl_compact_flow.config(text="[---]", fg=ACCENT_RED)


if __name__ == "__main__":
    root = tk.Tk()
    app = OverlayApp(root)
    root.mainloop()