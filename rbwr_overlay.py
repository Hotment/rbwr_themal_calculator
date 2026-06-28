import tkinter as tk
from tkinter import ttk
import math
import sys
import os
import threading
import logging
import traceback
import re
import queue
from PIL import Image, ImageDraw, ImageTk

__version__ = "1.6.3"

# --- Update Server Configuration ---
SUGGESTIONS_SERVER_URL = "https://rbwr.hotment.dev"
UPDATE_HTTP_HEADERS = {'User-Agent': 'Mozilla/5.0'}

try:
    __compiled__  # pyright: ignore[reportUndefinedVariable, reportUnusedExpression]
    _is_compiled = True
except NameError:
    _is_compiled = False

_log_dir = os.path.dirname(os.path.abspath(sys.argv[0])) if _is_compiled else os.path.dirname(os.path.abspath(__file__))
_log_path = os.path.join(_log_dir, "RBWR_APRM_Calculator.log")
_sanitization_mappings = []

def get_sanitization_mappings():
    mappings = []
    sources = [
        ("TEMP", "%temp%"),
        ("TMP", "%temp%"),
        ("LOCALAPPDATA", "%localappdata%"),
        ("APPDATA", "%appdata%"),
        ("USERPROFILE", "%userprofile%"),
    ]
    seen_variants = set()
    for var_name, placeholder in sources:
        path = os.environ.get(var_name)
        if not path:
            continue
        variants = [path]
        if os.name == 'nt':
            try:
                import ctypes
                buf = ctypes.create_unicode_buffer(1024)
                if ctypes.windll.kernel32.GetShortPathNameW(path, buf, 1024):
                    short = buf.value
                    if short not in variants:
                        variants.append(short)
            except Exception:
                pass
        for var in variants:
            var = var.rstrip('/\\')
            if not var or len(var) < 4:
                continue
            for slash_var in [var.replace('/', '\\'), var.replace('\\', '/')]:
                if slash_var.lower() not in seen_variants:
                    seen_variants.add(slash_var.lower())
                    pattern = re.compile(re.escape(slash_var), re.IGNORECASE)
                    mappings.append((pattern, placeholder))
    mappings.sort(key=lambda x: len(x[0].pattern), reverse=True)
    return mappings

_sanitization_mappings = get_sanitization_mappings()

def sanitize_string(text: str) -> str:
    if not text:
        return text
    for pattern, placeholder in _sanitization_mappings:
        text = pattern.sub(placeholder, text)
    return text

class SanitizingFormatter(logging.Formatter):
    def format(self, record):
        formatted = super().format(record)
        return sanitize_string(formatted)

file_handler = logging.FileHandler(_log_path, mode="w", encoding="utf-8")
stream_handler = logging.StreamHandler(sys.stdout)

formatter = SanitizingFormatter("%(asctime)s [%(levelname)s] %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

logging.basicConfig(
    level=logging.INFO,
    handlers=[file_handler, stream_handler],
)
# Silence noisy third-party loggers
logging.getLogger("PIL").setLevel(logging.WARNING)
logging.getLogger("onnxruntime").setLevel(logging.WARNING)
log = logging.getLogger("rbwr")

def show_crash_dialog(tb_text):
    try:
        crash_win = tk.Tk()
        crash_win.title("Application Crash Detected")
        
        if os.path.exists("icon.ico"):
            try:
                crash_win.iconbitmap("icon.ico")
            except Exception:
                pass
        else:
            try:
                icon_path = os.path.join(_log_dir, "icon.ico")
                if os.path.exists(icon_path):
                    crash_win.iconbitmap(icon_path)
                else:
                    crash_win.tk_icon = ImageTk.PhotoImage(get_default_icon_image())  # pyright: ignore[reportAttributeAccessIssue]
                    crash_win.iconphoto(False, crash_win.tk_icon)  # pyright: ignore[reportArgumentType, reportAttributeAccessIssue]
            except Exception:
                pass

        crash_win.geometry("560x380")
        crash_win.configure(bg="#07080a")
        crash_win.attributes("-topmost", True)
        
        screen_width = crash_win.winfo_screenwidth()
        screen_height = crash_win.winfo_screenheight()
        x = (screen_width - 560) // 2
        y = (screen_height - 380) // 2
        crash_win.geometry(f"560x380+{x}+{y}")
        
        lbl_header = tk.Label(crash_win, text="CRITICAL EXCEPTION ENCOUNTERED", bg="#07080a", fg="#ff003c", font=("Segoe UI", 11, "bold"))
        lbl_header.pack(pady=(15, 5))
        
        lbl_sub = tk.Label(crash_win, text="The application has crashed. A detailed crash log was saved to the log file.\nPlease copy the traceback below to report this issue.", 
                           bg="#07080a", fg="#6c7d93", font=("Segoe UI", 8), justify="center", wraplength=520)
        lbl_sub.pack(pady=(0, 10))
        
        btn_frame = tk.Frame(crash_win, bg="#07080a")
        btn_frame.pack(side="bottom", fill="x", pady=15, padx=20)
        
        txt_frame = tk.Frame(crash_win, bg="#11141a", bd=1, relief="solid")
        txt_frame.pack(fill="both", expand=True, padx=20, pady=5)
        txt_frame.columnconfigure(0, weight=1)
        txt_frame.rowconfigure(0, weight=1)
        
        txt_tb = tk.Text(txt_frame, bg="#11141a", fg="#ffffff", insertbackground="#ffffff", font=("Consolas", 8), bd=0, wrap="none")
        txt_tb.insert("1.0", tb_text)
        txt_tb.config(state="disabled")
        txt_tb.grid(row=0, column=0, sticky="nsew")
        
        from tkinter import ttk
        style = ttk.Style(crash_win)
        style.theme_use('clam')
        style.configure("Dark.Vertical.TScrollbar",
                        gripcount=0,
                        background="#1f2430",
                        troughcolor="#07080a",
                        bordercolor="#11141a",
                        arrowcolor="#6c7d93",
                        lightcolor="#1f2430",
                        darkcolor="#1f2430")
        style.map("Dark.Vertical.TScrollbar",
                  background=[("active", "#3a4659"), ("pressed", "#6c7d93")])
                        
        scroll_y = ttk.Scrollbar(txt_frame, orient="vertical", command=txt_tb.yview, style="Dark.Vertical.TScrollbar")
        
        def scroll_set(first, last):
            first, last = float(first), float(last)
            if first <= 0.0 and last >= 1.0:
                scroll_y.grid_forget()
            else:
                scroll_y.grid(row=0, column=1, sticky="ns")
            scroll_y.set(first, last)
            
        txt_tb.config(yscrollcommand=scroll_set)
        
        def copy_to_clipboard():
            crash_win.clipboard_clear()
            crash_win.clipboard_append(tb_text)
            btn_copy.config(text="Copied!", fg="#39ff14")
            
        def open_github():
            import urllib.parse
            import webbrowser
            body_param = urllib.parse.quote(f"Please describe what you were doing when the crash occurred:\n\n```\n{tb_text}```")
            webbrowser.open(f"https://github.com/Hotment/rbwr_themal_calculator/issues/new?body={body_param}")
            
        def close_app():
            crash_win.destroy()
            os._exit(1)
            
        import queue
        crash_queue = queue.Queue()
        
        def poll_crash_queue():
            try:
                while True:
                    fn, args, kwargs = crash_queue.get_nowait()
                    try:
                        fn(*args, **kwargs)
                    except Exception:
                        pass
                    crash_queue.task_done()
            except queue.Empty:
                pass
            crash_win.after(50, poll_crash_queue)
            
        crash_win.after(0, poll_crash_queue)

        def send_report():
            btn_send.config(text="Sending Report...", fg=ACCENT_GOLD)
            crash_win.update()
            
            log_data = ""
            try:
                if os.path.exists(_log_path):
                    with open(_log_path, "r", encoding="utf-8") as lf:
                        log_data = lf.read()
            except Exception:
                pass
                
            def perform_send():
                import urllib.request
                import json
                
                payload = {
                    "version": __version__,
                    "traceback": tb_text,
                    "log_data": log_data
                }
                
                try:
                    data_bytes = json.dumps(payload).encode('utf-8')
                    req = urllib.request.Request(
                        f"{SUGGESTIONS_SERVER_URL}/crashes",
                        data=data_bytes,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "RBWR-Overlay-Client"
                        },
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        if resp.status == 200:
                            crash_queue.put((lambda: btn_send.config(text="Report Sent!", fg=ACCENT_GREEN), (), {}))
                        else:
                            crash_queue.put((lambda: btn_send.config(text="Send Failed!", fg=ACCENT_RED), (), {}))
                except Exception:
                    crash_queue.put((lambda: btn_send.config(text="Send Failed!", fg=ACCENT_RED), (), {}))
                    
            threading.Thread(target=perform_send, daemon=True).start()

        btn_copy = tk.Label(btn_frame, text="Copy Traceback", bg="#11141a", fg="#00f0ff", font=("Segoe UI", 8, "bold"), bd=1, relief="solid", padx=10, pady=6, cursor="hand2")
        btn_copy.pack(side="left", padx=3)
        btn_copy.bind("<Button-1>", lambda e: copy_to_clipboard())
        
        btn_issue = tk.Label(btn_frame, text="Report on GitHub", bg="#11141a", fg="#ffaa00", font=("Segoe UI", 8, "bold"), bd=1, relief="solid", padx=10, pady=6, cursor="hand2")
        btn_issue.pack(side="left", padx=3)
        btn_issue.bind("<Button-1>", lambda e: open_github())

        btn_send = tk.Label(btn_frame, text="Send Report (Anon)", bg="#11141a", fg="#00f0ff", font=("Segoe UI", 8, "bold"), bd=1, relief="solid", padx=10, pady=6, cursor="hand2")
        btn_send.pack(side="left", padx=3)
        btn_send.bind("<Button-1>", lambda e: send_report())

        btn_close = tk.Label(btn_frame, text="Exit App", bg="#11141a", fg="#ff003c", font=("Segoe UI", 8, "bold"), bd=1, relief="solid", padx=10, pady=6, cursor="hand2")
        btn_close.pack(side="right", padx=3)
        btn_close.bind("<Button-1>", lambda e: close_app())
        
        crash_win.protocol("WM_DELETE_WINDOW", close_app)
        crash_win.mainloop()
    except Exception:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, f"Critical Crash:\n{tb_text}", "RBWR Overlay Crash", 0x10)
        os._exit(1)

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    tb_text = sanitize_string("".join(tb_lines))
    log.critical("Unhandled exception captured:\n" + tb_text)
    show_crash_dialog(tb_text)

def handle_thread_exception(args):
    handle_exception(args.exc_type, args.exc_value, args.exc_traceback)

sys.excepthook = handle_exception
threading.excepthook = handle_thread_exception
tk.Tk.report_callback_exception = lambda self, exc_type, exc_value, exc_traceback: handle_exception(exc_type, exc_value, exc_traceback)  # pyright: ignore[reportAttributeAccessIssue]

log.info(f"=== RBWR APRM Calculator v{__version__} starting ===")
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

APRMtoRecircTable = {
    0: 0,
    10: 28,
    20: 28,
    30: 28,
    40: 38,
    50: 50,
    60: 70,
    70: 85,
    80: 90,
    90: 97,
    100: 100,
    110: 100
}

class UsageCalculator:
    def __init__(self, unit=1): # all usages are in MW/1kg or per pump(MW)
        self.unit = unit
        if unit == 1:
            self.feedwater_usage = 0.014
            self.condenser_usage = 0.007 # per kg
            self.condenser_circ_usage = 6.5
            self.recirculation_usage = 0.028
        elif unit == 2:
            self.feedwater_usage = 0.013
            self.condenser_usage = 3.1850 # per pump
            self.condenser_circ_usage = 6.5
            self.recirculation_usage = 0.01
            self.tower_makeup_usage = 0.5
        else:
            raise ValueError("Invalid unit number. Unit must be 1 or 2.")

    def aprm_to_recirc_pump_speed(self, aprm):
        for aprm_value in sorted(APRMtoRecircTable.keys()):
            if aprm_value >= aprm:
                return APRMtoRecircTable[aprm_value]
        return APRMtoRecircTable[max(APRMtoRecircTable.keys())]

    def calculate_usage(self, feedwater_flow, aprm, override_speed=None):
        feedwater_usage = self.feedwater_usage * feedwater_flow
        condenser_usage = self.condenser_usage if self.unit == 2 else self.condenser_usage * feedwater_flow
        
        speed = override_speed if override_speed is not None else self.aprm_to_recirc_pump_speed(aprm)
        recirculation_usage = self.recirculation_usage * speed * 10

        total_usage = feedwater_usage + condenser_usage + self.condenser_circ_usage * 2 + recirculation_usage
        return round(total_usage, 2)

class Calculator:
    def __init__(self, usage=61.32):
        self.usage = usage
        self.selected_unit = 1
        self.usage_calc1 = UsageCalculator(1)
        self.usage_calc2 = UsageCalculator(2)
        self.recirc_override: float|None = None

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
            return max(0.0, 160.0 + (11.6 * thermal) + (0.0249 * (thermal**2))) + 2

    def calc_gen_load(self, thermal):
        if self.selected_unit == 1:
            return max(0.0, -135 + (13 * thermal) + (5.33 * 10**-3 * (thermal**2)))
        else:
            return max(0.0, -82.3 + (10.9 * thermal) + (0.0238 * (thermal**2)))

    def calc_thermal(self, demand):
        current_usage = self.usage
        thermal = 0.0
        for _ in range(5):
            if self.selected_unit == 1:
                inner = 169 + 0.02132 * (demand + 135 + current_usage)
                if inner < 0:
                    thermal = 0.0
                else:
                    thermal = max(0.0, (-13 + math.sqrt(inner)) / 0.01066)
            else:
                inner = 118.81 + 0.0952 * (82.3 + demand + current_usage)
                if inner < 0:
                    thermal = 0.0
                else:
                    thermal = max(0.0, (-10.9 + math.sqrt(inner)) / 0.0476)
            
            # Calculate dynamic usage for this thermal power
            flow = self.calc_flow(thermal)
            u_calc = self.usage_calc1 if self.selected_unit == 1 else self.usage_calc2
            current_usage = u_calc.calculate_usage(flow, thermal, override_speed=self.recirc_override)
        
        self.usage = current_usage
        return thermal


class OverlayApp:
    def show_custom_message(self, title, message, is_error=False):
        if hasattr(self, 'custom_message_window') and self.custom_message_window and self.custom_message_window.winfo_exists():
            try:
                self.custom_message_window.destroy()
            except Exception:
                pass

        popup = tk.Toplevel(self.root)
        self.custom_message_window = popup
        popup.transient(self.root)
        popup.title(title)
        
        accent_color = ACCENT_RED if is_error else ACCENT_CYAN
        popup.configure(bg=BG_CARD, highlightbackground=accent_color, highlightcolor=accent_color, highlightthickness=1)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        
        w = 360
        h = 180
        if len(message) > 150:
            w = 400
            h = 240

        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = max(0, min(x, screen_w - w))
        y = max(0, min(y, screen_h - h))
        
        popup.geometry(f"{w}x{h}+{x}+{y}")
        
        drag_data = {"x": 0, "y": 0}
        def start_drag(event):
            drag_data["x"] = event.x
            drag_data["y"] = event.y
            
        def do_drag(event):
            dx = event.x - drag_data["x"]
            dy = event.y - drag_data["y"]
            px = popup.winfo_x() + dx
            py = popup.winfo_y() + dy
            popup.geometry(f"+{px}+{py}")
            
        title_bar = tk.Frame(popup, bg=BG_HEADER, height=30)
        title_bar.pack(fill="x", side="top")
        title_bar.bind("<Button-1>", start_drag)
        title_bar.bind("<B1-Motion>", do_drag)
        
        prefix = " ⚠ ERROR" if is_error else " ⚙ INFO"
        title_lbl = tk.Label(title_bar, text=f"{prefix}: {title.upper()}", bg=BG_HEADER, fg=accent_color,
                             font=("Consolas", 9, "bold"))
        title_lbl.pack(side="left", padx=10, pady=5)
        title_lbl.bind("<Button-1>", start_drag)
        title_lbl.bind("<B1-Motion>", do_drag)
        
        btn_close_top = tk.Label(title_bar, text="✕", bg=BG_HEADER, fg=TEXT_MUTED, width=3, font=("Segoe UI", 11, "bold"), cursor="hand2")
        btn_close_top.pack(side="right", fill="y")
        btn_close_top.bind("<Button-1>", lambda e: popup.destroy())
        btn_close_top.bind("<Enter>", lambda e: btn_close_top.config(bg=ACCENT_RED, fg=TEXT_LIGHT))
        btn_close_top.bind("<Leave>", lambda e: btn_close_top.config(bg=BG_HEADER, fg=TEXT_MUTED))
        
        content_frame = tk.Frame(popup, bg=BG_CARD, padx=20, pady=15)
        content_frame.pack(fill="both", expand=True)
        
        msg_lbl = tk.Label(content_frame, text=message, bg=BG_CARD, fg=TEXT_LIGHT, 
                           font=("Segoe UI", 9), justify="left", wraplength=w - 40)
        msg_lbl.pack(anchor="nw", fill="both", expand=True, pady=(0, 15))
        
        btn_ok = tk.Label(content_frame, text="OK", bg=BG_MAIN, fg=accent_color,
                          font=("Segoe UI", 9, "bold"), bd=1, relief="solid", padx=25, pady=4, cursor="hand2")
        btn_ok.pack(anchor="se", side="bottom")
        btn_ok.bind("<Button-1>", lambda e: popup.destroy())
        btn_ok.bind("<Enter>", lambda e: btn_ok.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_ok.bind("<Leave>", lambda e: btn_ok.config(bg=BG_MAIN, fg=accent_color))
        
        def on_custom_message_destroy(event):
            if event.widget == popup:
                self.custom_message_window = None
                self.update_topmost_state()

        popup.bind("<Destroy>", on_custom_message_destroy)
        popup.deiconify()
        popup.lift(self.root)
        popup.focus_force()

    def poll_gui_queue(self):
        try:
            while True:
                fn, args, kwargs = self.gui_queue.get_nowait()
                try:
                    fn(*args, **kwargs)
                except Exception as e:
                    log.error(f"Error in queue callback: {e}")
                self.gui_queue.task_done()
        except queue.Empty:
            pass
        self.root.after(50, self.poll_gui_queue)

    def run_on_main_thread(self, fn, *args, **kwargs):
        if threading.current_thread() is threading.main_thread():
            fn(*args, **kwargs)
        else:
            self.gui_queue.put((fn, args, kwargs))

    def _sync_hud_scan(self):
        self.enable_hud_scan = self.var_hud_scan.get()

    def _sync_topmost_on_roblox(self):
        self.topmost_on_roblox = self.var_topmost_on_roblox.get()

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.withdraw()
        self.gui_queue = queue.Queue()
        self.poll_gui_queue()
        self.root.title(f"RBWR APRM Calculator v{__version__}")
        
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
        self.height_detailed = 350
        self.width_compact = 430
        self.height_compact = 60
        self.settings_window = None
        self.suggestions_window = None
        self.update_window = None
        self.loading_window = None
        self.custom_message_window = None
        
        self._drag_data = {"x": 0, "y": 0}
        
        self.var_demand = tk.StringVar(value="0")
        self.var_rtp = tk.StringVar(value="0")
        self.var_usage = tk.StringVar(value=f"{self.calc.usage:.2f}")
        self.var_demand.trace_add("write", lambda name, index, mode: self.on_input_update("demand"))
        self.var_rtp.trace_add("write", lambda name, index, mode: self.on_input_update("rtp"))
        self.enable_hud_scan = settings.get("enable_hud_scan", True)
        self.topmost_on_roblox = settings.get("topmost_on_roblox", True)
        self.var_hud_scan = tk.BooleanVar(value=self.enable_hud_scan)
        self.var_topmost_on_roblox = tk.BooleanVar(value=self.topmost_on_roblox)
        self.var_hud_scan.trace_add("write", lambda *args: self._sync_hud_scan())
        self.var_topmost_on_roblox.trace_add("write", lambda *args: self._sync_topmost_on_roblox())
        self.var_compact_menu = tk.BooleanVar(value=self.is_compact)
        self.var_topmost_menu = tk.BooleanVar(value=self.is_topmost)
        self.skipped_version = settings.get("skipped_version", "")
        self.var_recirc_override = tk.StringVar(value="")
        self.var_recirc_override.trace_add("write", lambda *args: self.on_recirc_override_change())
        
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
                log.warning("Failed to load custom icon from icon.ico")
        else:
            try:
                icon_path = os.path.join(_log_dir, "icon.ico")
                if os.path.exists(icon_path):
                    self.root.iconbitmap(icon_path)
                else:
                    self.tk_icon = ImageTk.PhotoImage(self.icon_image_pil)
                    self.root.iconphoto(False, self.tk_icon)  # pyright: ignore[reportArgumentType]
            except Exception as e:
                log.warning(f"Failed to set fallback icon: {e}")
                
        self.setup_tray_icon()
        
        self.context_menu = tk.Menu(self.root, tearoff=0, bg=BG_CARD, fg=TEXT_LIGHT, 
                                    activebackground=BG_HEADER, activeforeground=ACCENT_CYAN, 
                                    bd=1, relief="solid", font=("Segoe UI", 9))
        self.context_menu.add_checkbutton(label="Compact Mode", variable=self.var_compact_menu, command=self.toggle_compact)
        self.context_menu.add_checkbutton(label="Always on Top", variable=self.var_topmost_menu, command=self.toggle_topmost)
        self.context_menu.add_checkbutton(label="Topmost on Roblox", variable=self.var_topmost_on_roblox, command=self.save_settings)
        self.context_menu.add_checkbutton(label="Scan HUD First", variable=self.var_hud_scan, command=self.on_hud_scan_menu_toggle)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Exit Application", command=self.quit_app)
        
        self.root.bind("<Button-3>", self.show_context_menu)
        
        if self.is_compact:
            self.center_window(self.width_compact, self.height_compact)
        else:
            self.center_window(self.width_detailed, self.height_detailed)
        self.create_widgets()
        self.update_calculations(source="demand")
        
        self.check_for_updates()
        self.check_focus_loop()
        self.root.after(10, self.setup_app_window_style)

    def center_window(self, w, h):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        x = (screen_width - w) // 2
        y = (screen_height - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.start_x = x
        self.start_y = y

    def show_context_menu(self, event):
        try:
            self.root.attributes("-topmost", False)
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
            self.root.attributes("-topmost", self.is_topmost)

    def setup_app_window_style(self):
        try:
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            
            hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = style & ~WS_EX_TOOLWINDOW
            style = style | WS_EX_APPWINDOW
            
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
            
            w = self.width_compact if self.is_compact else self.width_detailed
            h = self.height_compact if self.is_compact else self.height_detailed
            x = getattr(self, 'start_x', 0)
            y = getattr(self, 'start_y', 0)
            
            self.root.deiconify()
            self.root.geometry(f"{w}x{h}+{x}+{y}")
        except Exception as e:
            log.warning(f"Failed to set WS_EX_APPWINDOW: {e}")

    def create_widgets(self):
        self.telemetry_frame = None
        for child in self.root.winfo_children():
            if child != self.context_menu:
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
        if hasattr(self, 'btn_topmost') and self.btn_topmost and self.btn_topmost.winfo_exists():
            self.btn_topmost.config(text=symbol)
        self.var_topmost_menu.set(self.is_topmost)
        self.save_settings()
        if hasattr(self, 'tray') and self.tray:
            try:
                self.tray.update_menu()
            except Exception:
                pass

    def toggle_compact(self):
        self.is_compact = not self.is_compact
        self.var_compact_menu.set(self.is_compact)
        self.save_settings()
        if hasattr(self, 'tray') and self.tray:
            try:
                self.tray.update_menu()
            except Exception:
                pass
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

        title_lbl = tk.Label(title_bar, text=f" [ APRM MONITOR v{__version__} // SYS OK ]", bg=BG_HEADER, fg=ACCENT_CYAN,
                             font=("Consolas", 9, "bold"))
        title_lbl.pack(side="left", padx=5)
        self.make_draggable(title_lbl)

        btn_close = tk.Label(title_bar, text="✕", bg=BG_HEADER, fg=TEXT_MUTED, width=3, font=("Segoe UI", 11, "bold"))
        btn_close.pack(side="right", fill="y")
        btn_close.bind("<Button-1>", lambda e: self.quit_app())
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg=TEXT_LIGHT))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg=BG_HEADER, fg=TEXT_MUTED))

        btn_settings = tk.Label(title_bar, text="⚙", bg=BG_HEADER, fg=TEXT_MUTED, width=3, font=("Segoe UI", 11))
        btn_settings.pack(side="right", fill="y")
        btn_settings.bind("<Button-1>", lambda e: self.open_settings_dialog())
        btn_settings.bind("<Enter>", lambda e: btn_settings.config(bg=BG_CARD, fg=ACCENT_CYAN))
        btn_settings.bind("<Leave>", lambda e: btn_settings.config(bg=BG_HEADER, fg=TEXT_MUTED))

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

        unit_suffix = "APRM" if self.calc.selected_unit == 1 else "RTP"
        self.lbl_rtp_in = tk.Label(input_card, text=f"CORE POWER ({unit_suffix}%)", bg=BG_MAIN, fg=TEXT_MUTED, font=("Consolas", 8, "bold"))
        self.lbl_rtp_in.grid(row=3, column=0, sticky="w", pady=2, padx=10)
        self.make_draggable(self.lbl_rtp_in)

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

        self.lbl_debug = tk.Label(container, text="[ OCR DIAG: STANDBY ]", bg=BG_MAIN, fg=TEXT_MUTED,
                                  font=("Consolas", 7))
        self.lbl_debug.pack(side="bottom", fill="x", pady=(4, 0))

        self.btn_feedback = tk.Label(container, text="💬 Feedback & Suggestions", bg=BG_MAIN, fg=TEXT_MUTED,
                                     font=("Segoe UI", 8, "bold"), cursor="hand2")
        self.btn_feedback.pack(side="bottom", pady=(3, 3))
        self.btn_feedback.bind("<Button-1>", lambda e: self.open_suggestions_dialog())
        self.btn_feedback.bind("<Enter>", lambda e: self.btn_feedback.config(fg=ACCENT_CYAN))
        self.btn_feedback.bind("<Leave>", lambda e: self.btn_feedback.config(fg=TEXT_MUTED))

        self.neon_frame = tk.Frame(container, bg=BG_CARD, padx=8, pady=8, bd=1, relief="solid")
        self.neon_frame.pack(fill="x", side="bottom", pady=(5, 0))
        self.make_draggable(self.neon_frame)

        unit_suffix = "APRM" if self.calc.selected_unit == 1 else "RTP"
        self.lbl_neon_rtp = tk.Label(self.neon_frame, text=f"0.00% {unit_suffix}", bg=BG_CARD, fg=ACCENT_CYAN, 
                                     font=("Consolas", 18, "bold"))
        self.lbl_neon_rtp.pack(anchor="center")
        self.make_draggable(self.lbl_neon_rtp)

        self.lbl_neon_sub = tk.Label(self.neon_frame, text="⚡ APRM REACTOR POWER STATUS", bg=BG_CARD, fg=TEXT_MUTED, 
                                     font=("Consolas", 8, "bold"))
        self.lbl_neon_sub.pack(anchor="center", pady=(2, 0))
        self.make_draggable(self.lbl_neon_sub)

        self.update_scan_button_styles()

    def build_compact_layout(self):
        compact_frame = tk.Frame(self.root, bg=BG_HEADER, padx=8, pady=5)
        compact_frame.pack(fill="both", expand=True)
        self.make_draggable(compact_frame)
        compact_frame.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        # Pack right-side control buttons first so they are never clipped/hidden when layout expands
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

        handle = tk.Label(compact_frame, text="⋮⋮", bg=BG_HEADER, fg=TEXT_MUTED, font=("Segoe UI", 12, "bold"), cursor="fleur")
        handle.pack(side="left", padx=(0, 5))
        self.make_draggable(handle)
        handle.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        self.btn_compact_u1 = tk.Label(compact_frame, text="U1", bg=BG_HEADER, fg=TEXT_MUTED,
                                       font=("Segoe UI", 8, "bold"), padx=4, pady=2, cursor="hand2")
        self.btn_compact_u1.pack(side="left", padx=(2, 1))
        self.btn_compact_u1.bind("<Button-1>", lambda e: self.select_unit(1))

        self.btn_compact_u2 = tk.Label(compact_frame, text="U2", bg=BG_HEADER, fg=TEXT_MUTED,
                                       font=("Segoe UI", 8, "bold"), padx=4, pady=2, cursor="hand2")
        self.btn_compact_u2.pack(side="left", padx=(1, 2))
        self.btn_compact_u2.bind("<Button-1>", lambda e: self.select_unit(2))

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

        # Stack RTP and Flow vertically to save horizontal space
        self.telemetry_frame = tk.Frame(compact_frame, bg=BG_HEADER)
        self.telemetry_frame.place(x=288, rely=0.5, anchor="w")
        self.make_draggable(self.telemetry_frame)
        self.telemetry_frame.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        unit_suffix = "APRM" if self.calc.selected_unit == 1 else "RTP"
        self.lbl_compact_rtp = tk.Label(self.telemetry_frame, text=f"0.0% {unit_suffix}", bg=BG_HEADER, fg=ACCENT_CYAN,
                                         font=("Consolas", 10, "bold"))
        self.lbl_compact_rtp.pack(side="top", anchor="center")
        self.make_draggable(self.lbl_compact_rtp)
        self.lbl_compact_rtp.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        self.lbl_compact_flow = tk.Label(self.telemetry_frame, text="[0 kg/s]", bg=BG_HEADER, fg=TEXT_MUTED,
                                         font=("Consolas", 8))
        self.lbl_compact_flow.pack(side="top", anchor="center")
        self.make_draggable(self.lbl_compact_flow)
        self.lbl_compact_flow.bind("<Double-Button-1>", lambda e: self.toggle_compact())

        self.update_scan_button_styles()
        self.update_unit_ui_state()

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
        self.select_unit(next_unit)

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
                pystray.MenuItem("Compact Mode", lambda icon, item: self.toggle_compact(), checked=lambda item: self.is_compact),
                pystray.MenuItem("Always on Top", lambda icon, item: self.toggle_topmost(), checked=lambda item: self.is_topmost),
                pystray.MenuItem("Topmost on Roblox", lambda icon, item: self.toggle_topmost_on_roblox(), checked=lambda item: self.topmost_on_roblox),
                pystray.MenuItem("Scan HUD First", lambda icon, item: self.toggle_hud_scan_setting(), checked=lambda item: self.enable_hud_scan),
                pystray.Menu.SEPARATOR,
                pystray.MenuItem("Exit", lambda icon, item: self.quit_app())
            )
            
            self.tray = pystray.Icon("RBWR APRM Calculator", image, f"RBWR APRM Calculator v{__version__}", menu)
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
            "topmost_on_roblox": True,
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
                "topmost_on_roblox": self.var_topmost_on_roblox.get(),
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
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.lift(self.root)
        if hasattr(self, 'suggestions_window') and self.suggestions_window and self.suggestions_window.winfo_exists():
            self.suggestions_window.lift(self.root)
        if hasattr(self, 'update_window') and self.update_window and self.update_window.winfo_exists():
            self.update_window.lift(self.root)
        if hasattr(self, 'loading_window') and self.loading_window and self.loading_window.winfo_exists():
            self.loading_window.lift(self.root)

    def open_log_file(self):
        try:
            if os.path.exists(_log_path):
                os.startfile(_log_path)
            else:
                self.show_custom_message("Log File", f"Log file not found at:\n{_log_path}")
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
            self.run_on_main_thread(self.update_scan_button_styles)

    def toggle_auto_scan(self):
        if not HAS_OCR:
            self.show_custom_message("Screen Reader", 
                                     "To enable automatic screen scanning, please install the OCR package:\n\n"
                                     "pip install rapidocr-onnxruntime pillow")
            return

        if self.ocr_initializing:
            self.show_custom_message("Screen Reader", "Initializing OCR engine models. Please wait a few seconds...")
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
                self.show_custom_message("Screen Reader", f"Failed to initialize OCR engine models.\n\nError: {e}\n\nCheck RBWR_APRM_Calculator.log for details.", is_error=True)
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
                    self.run_on_main_thread(self.update_scan_button_styles)
            time.sleep(1.0)

    def start_hotkey_listener(self):
        if hasattr(self, 'hotkey_thread_active') and self.hotkey_thread_active:
            self.hotkey_thread_active = False
            try:
                ctypes.windll.user32.UnregisterHotKey(None, 101)
            except Exception:
                pass
            
        self.hotkey_thread_active = True
        hotkey_val = self.var_hotkey.get().upper()
        threading.Thread(target=self.hotkey_loop, args=(hotkey_val,), daemon=True).start()

    def hotkey_loop(self, current_key):
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
                    self.run_on_main_thread(self.toggle_auto_scan)
                user32.TranslateMessage(ctypes.byref(msg))
                user32.DispatchMessageW(ctypes.byref(msg))
            time.sleep(0.05)
            
        user32.UnregisterHotKey(None, 101)

    def listen_for_hotkey(self):
        if hasattr(self, 'btn_hotkey_bind') and self.btn_hotkey_bind and self.btn_hotkey_bind.winfo_exists():
            self.btn_hotkey_bind.config(text="[ PRESS KEY... ]", fg=ACCENT_GOLD, bg=BG_HEADER)
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.bind("<Key>", self.on_hotkey_captured)
            self.settings_window.focus_set()
        else:
            self.root.bind("<Key>", self.on_hotkey_captured)
            self.root.focus_set()

    def on_hotkey_captured(self, event):
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.unbind("<Key>")
        else:
            self.root.unbind("<Key>")
        key = event.keysym.upper()
        
        if key == "ESCAPE":
            if hasattr(self, 'btn_hotkey_bind') and self.btn_hotkey_bind and self.btn_hotkey_bind.winfo_exists():
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
        if hasattr(self, 'btn_hotkey_bind') and self.btn_hotkey_bind and self.btn_hotkey_bind.winfo_exists():
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
            if self.enable_hud_scan:
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
            def clean_demand_string(val_str: str) -> str:
                if not val_str:
                    return val_str
                if not val_str.endswith('0'):
                    r_index = val_str.rfind('0')
                    if r_index != -1:
                        val_str = val_str[:r_index + 1]
                while True:
                    if not val_str:
                        break
                    try:
                        val_num = float(val_str)
                    except ValueError:
                        break
                    if val_num > 1200 and val_str.endswith('00'):
                        val_str = val_str[:-1]
                    else:
                        break
                return val_str

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
                        detected_demand = float(clean_demand_string(demand_match.group(2)))
                else:
                    detected_demand = float(clean_demand_string(val_str))
            elif demand_match:
                unit_char = demand_match.group(1).lower()
                if unit_char in ('1', 'l', 'i', '|'):
                    detected_unit = 1
                elif unit_char in ('2', 'z', 's'):
                    detected_unit = 2
                detected_demand = float(clean_demand_string(demand_match.group(2)))

            # Scan the rest of the text for a general unit indicator if not found via HUD demand labels
            if detected_unit is None:
                unit_word_match = re.search(r'(?i)\bUnit\s*0?([12])\b', full_text)
                if unit_word_match:
                    detected_unit = int(unit_word_match.group(1))
                else:
                    unit_cleaned_match = re.search(r'(?i)Unit0?([12])', cleaned)
                    if unit_cleaned_match:
                        detected_unit = int(unit_cleaned_match.group(1))
                    else:
                        u_word_match = re.search(r'(?i)\bU([12])\b', full_text)
                        if u_word_match:
                            detected_unit = int(u_word_match.group(1))

            if detected_demand is not None:
                self.log_diag(f"Matched HUD: U{detected_unit or '?'}({detected_demand})", "success")
                self.root.after(0, lambda: self.apply_auto_telemetry(detected_unit, detected_demand))
                return True

            match_net = re.search(r'(?i)Network\s*dem[a-z0-9]*\s*[:\s]+(\d+)(?:\s*\(\s*(\d+)\s*\))?', full_text)
            if match_net:
                val1 = float(clean_demand_string(match_net.group(1)))
                val2 = float(clean_demand_string(match_net.group(2))) if match_net.group(2) else None
                
                active_unit = detected_unit if detected_unit is not None else self.calc.selected_unit
                if active_unit == 1:
                     detected_demand = val1
                else:
                    if val2 is not None:
                        if val2 > val1:
                            detected_demand = val2 - val1
                        else:
                            detected_demand = val2
                    else:
                        detected_demand = val1
                
                self.log_diag(f"Matched Net: D({detected_demand}) (Unit: {active_unit})", "success")
                self.run_on_main_thread(lambda: self.apply_auto_telemetry(active_unit, detected_demand))
                return True

            match_fallback = re.search(r'(?i)Demand(\d+)', cleaned)
            if match_fallback:
                detected_demand = float(clean_demand_string(match_fallback.group(1)))
                self.log_diag(f"Matched Fallback: D({detected_demand}) (Unit: {detected_unit})", "success")
                self.run_on_main_thread(lambda: self.apply_auto_telemetry(detected_unit, detected_demand))
                return True

            match_generic = re.search(r'(?i)(?:demand|load|dem)[A-Za-z]*(\d+)', cleaned)
            if match_generic:
                detected_demand = float(clean_demand_string(match_generic.group(1)))
                self.log_diag(f"Matched Generic: D({detected_demand}) (Unit: {detected_unit})", "success")
                self.run_on_main_thread(lambda: self.apply_auto_telemetry(detected_unit, detected_demand))
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
            self.run_on_main_thread(lambda: self.lbl_debug.config(text=f"[ OCR: {message.upper()} ]", fg=color))

    def update_unit_ui_state(self):
        if hasattr(self, 'btn_u1') and hasattr(self, 'btn_u2') and self.btn_u1.winfo_exists() and self.btn_u2.winfo_exists():
            if self.calc.selected_unit == 1:
                self.btn_u1.config(bg=BG_CARD, fg=ACCENT_CYAN, text="❖ UNIT 01 ❖", bd=1, relief="solid")
                self.btn_u2.config(bg=BG_MAIN, fg=TEXT_MUTED, text="  UNIT 02  ", bd=0, relief="flat")
            else:
                self.btn_u1.config(bg=BG_MAIN, fg=TEXT_MUTED, text="  UNIT 01  ", bd=0, relief="flat")
                self.btn_u2.config(bg=BG_CARD, fg=ACCENT_CYAN, text="❖ UNIT 02 ❖", bd=1, relief="solid")

        if hasattr(self, 'btn_compact_u1') and hasattr(self, 'btn_compact_u2') and self.btn_compact_u1.winfo_exists() and self.btn_compact_u2.winfo_exists():
            if self.calc.selected_unit == 1:
                self.btn_compact_u1.config(bg=ACCENT_CYAN, fg=BG_MAIN)
                self.btn_compact_u2.config(bg=BG_HEADER, fg=TEXT_MUTED)
            else:
                self.btn_compact_u1.config(bg=BG_HEADER, fg=TEXT_MUTED)
                self.btn_compact_u2.config(bg=ACCENT_CYAN, fg=BG_MAIN)

        unit_suffix = "APRM" if self.calc.selected_unit == 1 else "RTP"
        if hasattr(self, 'lbl_rtp_in') and self.lbl_rtp_in and self.lbl_rtp_in.winfo_exists():
            self.lbl_rtp_in.config(text=f"CORE POWER ({unit_suffix}%)")

    def open_settings_dialog(self):
        if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
            self.settings_window.deiconify()
            self.settings_window.lift()
            self.settings_window.attributes("-topmost", True)
            self.settings_window.focus_force()
            return

        settings_win = tk.Toplevel(self.root)
        self.settings_window = settings_win
        settings_win.transient(self.root)

        settings_win.title("APRM Monitor Settings")
        settings_win.configure(bg=BG_CARD, highlightbackground=ACCENT_CYAN, highlightcolor=ACCENT_CYAN, highlightthickness=1)
        settings_win.overrideredirect(True)
        settings_win.attributes("-topmost", True)

        # Center relative to root window
        w = 380
        h = 435
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2

        settings_win.geometry(f"{w}x{h}+{x}+{y}")

        drag_data = {"x": 0, "y": 0}
        def start_drag(event):
            drag_data["x"] = event.x
            drag_data["y"] = event.y
            
        def do_drag(event):
            dx = event.x - drag_data["x"]
            dy = event.y - drag_data["y"]
            px = settings_win.winfo_x() + dx
            py = settings_win.winfo_y() + dy

            settings_win.geometry(f"+{px}+{py}")

        title_bar = tk.Frame(settings_win, bg=BG_HEADER, height=30)
        title_bar.pack(fill="x", side="top")
        title_bar.bind("<Button-1>", start_drag)
        title_bar.bind("<B1-Motion>", do_drag)

        title_lbl = tk.Label(title_bar, text=" ⚙ CONFIGURATION SETTINGS", bg=BG_HEADER, fg=ACCENT_CYAN,
                             font=("Consolas", 9, "bold"))
        title_lbl.pack(side="left", padx=10, pady=5)
        title_lbl.bind("<Button-1>", start_drag)
        title_lbl.bind("<B1-Motion>", do_drag)

        btn_close = tk.Label(title_bar, text="✕", bg=BG_HEADER, fg=TEXT_MUTED, width=3, font=("Segoe UI", 11, "bold"), cursor="hand2")
        btn_close.pack(side="right", fill="y")
        btn_close.bind("<Button-1>", lambda e: settings_win.destroy())
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg=TEXT_LIGHT))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg=BG_HEADER, fg=TEXT_MUTED))

        content_frame = tk.Frame(settings_win, bg=BG_CARD, padx=15, pady=10)
        content_frame.pack(fill="both", expand=True)

        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)


        lbl_usage = tk.Label(content_frame, text="Site Usage (MWe):", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_usage.grid(row=0, column=0, sticky="w", pady=4)

        self.ent_usage = tk.Entry(content_frame, textvariable=self.var_usage, bg=BG_CARD, fg=ACCENT_CYAN, 
                                  readonlybackground=BG_CARD, insertbackground=TEXT_LIGHT, font=("Consolas", 10, "bold"), 
                                  bd=0, highlightthickness=0, width=10, justify="center", state="readonly")
        self.ent_usage.grid(row=0, column=1, sticky="e", padx=10, pady=4)


        lbl_usage_note = tk.Label(content_frame, text="Use Recirc Speed Override if Site Usage is off by a lot (10-15 MW off)", 
                                  bg=BG_CARD, fg=ACCENT_GOLD, font=("Segoe UI", 7, "italic"), justify="left", wraplength=340)
        lbl_usage_note.grid(row=1, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 4))


        lbl_opacity = tk.Label(content_frame, text="Overlay Opacity:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_opacity.grid(row=2, column=0, sticky="w", pady=4)

        self.slider_opacity = ttk.Scale(content_frame, from_=0.3, to=1.0, value=self.root.attributes("-alpha"),
                                         orient="horizontal", command=self.on_opacity_change)
        self.slider_opacity.grid(row=2, column=1, sticky="we", padx=10, pady=4)


        lbl_hotkey = tk.Label(content_frame, text="Scan Hotkey:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_hotkey.grid(row=3, column=0, sticky="w", pady=4)

        self.btn_hotkey_bind = tk.Label(content_frame, text=self.var_hotkey.get(), bg=BG_MAIN, fg=ACCENT_CYAN,
                                        font=("Consolas", 9, "bold"), bd=1, relief="solid", padx=10, pady=3, cursor="hand2")
        self.btn_hotkey_bind.grid(row=3, column=1, sticky="e", padx=10, pady=4)
        self.btn_hotkey_bind.bind("<Button-1>", lambda e: self.listen_for_hotkey())
        self.btn_hotkey_bind.bind("<Enter>", lambda e: self.btn_hotkey_bind.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        self.btn_hotkey_bind.bind("<Leave>", lambda e: self.btn_hotkey_bind.config(bg=BG_MAIN, fg=ACCENT_CYAN if self.btn_hotkey_bind.cget("text") != "[ PRESS KEY... ]" else ACCENT_GOLD))


        lbl_log = tk.Label(content_frame, text="Diagnostics:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_log.grid(row=4, column=0, sticky="w", pady=4)

        self.btn_open_log = tk.Label(content_frame, text="📄 Open Log", bg=BG_MAIN, fg=ACCENT_CYAN,
                                      font=("Consolas", 9, "bold"), bd=1, relief="solid", padx=10, pady=3, cursor="hand2")
        self.btn_open_log.grid(row=4, column=1, sticky="e", padx=10, pady=4)
        self.btn_open_log.bind("<Button-1>", lambda e: self.open_log_file())
        self.btn_open_log.bind("<Enter>", lambda e: self.btn_open_log.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        self.btn_open_log.bind("<Leave>", lambda e: self.btn_open_log.config(bg=BG_MAIN, fg=ACCENT_CYAN))


        lbl_hud_scan = tk.Label(content_frame, text="Scan HUD first:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_hud_scan.grid(row=5, column=0, sticky="w", pady=4)

        hud_status = "🟢 ENABLED" if self.var_hud_scan.get() else "🔴 DISABLED"
        hud_color = ACCENT_GREEN if self.var_hud_scan.get() else ACCENT_RED
        self.btn_hud_scan_toggle = tk.Label(content_frame, text=hud_status, bg=BG_MAIN, fg=hud_color,
                                            font=("Consolas", 9, "bold"), bd=1, relief="solid", padx=10, pady=3, cursor="hand2")
        self.btn_hud_scan_toggle.grid(row=5, column=1, sticky="e", padx=10, pady=4)
        self.btn_hud_scan_toggle.bind("<Button-1>", lambda e: self.toggle_hud_scan_setting())
        self.btn_hud_scan_toggle.bind("<Enter>", lambda e: self.btn_hud_scan_toggle.config(bg=BG_HEADER))
        self.btn_hud_scan_toggle.bind("<Leave>", lambda e: self.btn_hud_scan_toggle.config(bg=BG_MAIN))


        lbl_roblox_topmost = tk.Label(content_frame, text="Topmost on Roblox:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_roblox_topmost.grid(row=6, column=0, sticky="w", pady=4)

        roblox_topmost_status = "🟢 ENABLED" if self.var_topmost_on_roblox.get() else "🔴 DISABLED"
        roblox_topmost_color = ACCENT_GREEN if self.var_topmost_on_roblox.get() else ACCENT_RED
        self.btn_roblox_topmost_toggle = tk.Label(content_frame, text=roblox_topmost_status, bg=BG_MAIN, fg=roblox_topmost_color,
                                                  font=("Consolas", 9, "bold"), bd=1, relief="solid", padx=10, pady=3, cursor="hand2")
        self.btn_roblox_topmost_toggle.grid(row=6, column=1, sticky="e", padx=10, pady=4)
        self.btn_roblox_topmost_toggle.bind("<Button-1>", lambda e: self.toggle_roblox_topmost_setting())
        self.btn_roblox_topmost_toggle.bind("<Enter>", lambda e: self.btn_roblox_topmost_toggle.config(bg=BG_HEADER))
        self.btn_roblox_topmost_toggle.bind("<Leave>", lambda e: self.btn_roblox_topmost_toggle.config(bg=BG_MAIN))


        lbl_recirc = tk.Label(content_frame, text="Recirc Override (%):", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_recirc.grid(row=7, column=0, sticky="w", pady=4)

        recirc_frame = tk.Frame(content_frame, bg=BG_CARD)
        recirc_frame.grid(row=7, column=1, sticky="e", padx=10, pady=4)

        self.ent_recirc = tk.Entry(recirc_frame, textvariable=self.var_recirc_override, bg=BG_MAIN, fg=ACCENT_CYAN,
                                   insertbackground=TEXT_LIGHT, font=("Consolas", 9, "bold"), bd=1, relief="solid",
                                   width=6, justify="center")
        self.ent_recirc.pack(side="left", padx=(0, 5))
        self.ent_recirc.bind("<Button-1>", lambda e: self.ent_recirc.focus_force())
        
        settings_win.bind("<Button-1>", lambda e: settings_win.focus_force() if not isinstance(e.widget, (tk.Entry, tk.Text)) else None)
        content_frame.bind("<Button-1>", lambda e: settings_win.focus_force() if not isinstance(e.widget, (tk.Entry, tk.Text)) else None)

        btn_recirc_reset = tk.Label(recirc_frame, text="Reset", bg=BG_MAIN, fg=TEXT_MUTED,
                                    font=("Segoe UI", 8, "bold"), bd=1, relief="solid", padx=8, pady=2, cursor="hand2")
        btn_recirc_reset.pack(side="left")
        btn_recirc_reset.bind("<Button-1>", lambda e: self.reset_recirc_override())
        btn_recirc_reset.bind("<Enter>", lambda e: btn_recirc_reset.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_recirc_reset.bind("<Leave>", lambda e: btn_recirc_reset.config(bg=BG_MAIN, fg=TEXT_MUTED))

        lbl_recirc_note = tk.Label(content_frame, text="Use this when running RBMK or SELF-CIRC mode as those don't require recirc changes.", 
                                   bg=BG_CARD, fg=ACCENT_GOLD, font=("Segoe UI", 7, "italic"), justify="left")
        lbl_recirc_note.grid(row=8, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 4))


        lbl_feedback = tk.Label(content_frame, text="Feedback & Help:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_feedback.grid(row=9, column=0, sticky="w", pady=4)

        btn_feedback_settings = tk.Label(content_frame, text="💬 Feedback", bg=BG_MAIN, fg=ACCENT_CYAN,
                                      font=("Consolas", 9, "bold"), bd=1, relief="solid", padx=10, pady=3, cursor="hand2")
        btn_feedback_settings.grid(row=9, column=1, sticky="e", padx=10, pady=4)
        btn_feedback_settings.bind("<Button-1>", lambda e: self.open_suggestions_dialog())
        btn_feedback_settings.bind("<Enter>", lambda e: btn_feedback_settings.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_feedback_settings.bind("<Leave>", lambda e: btn_feedback_settings.config(bg=BG_MAIN, fg=ACCENT_CYAN))


        lbl_ver = tk.Label(content_frame, text=f"Version: {__version__}", bg=BG_CARD, fg=TEXT_MUTED, font=("Segoe UI", 8))
        lbl_ver.grid(row=10, column=0, columnspan=2, sticky="w", pady=(12, 0))

        def on_settings_destroy(event):
            if event.widget == settings_win:
                self.settings_window = None
                self.update_topmost_state()

        settings_win.bind("<Destroy>", on_settings_destroy)
        settings_win.focus_force()

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
        if hasattr(self, 'tray') and self.tray:
            try:
                self.tray.update_menu()
            except Exception:
                pass

    def on_hud_scan_menu_toggle(self):
        new_val = self.var_hud_scan.get()
        if hasattr(self, 'btn_hud_scan_toggle') and self.btn_hud_scan_toggle.winfo_exists():
            self.btn_hud_scan_toggle.config(text="🟢 ENABLED" if new_val else "🔴 DISABLED",
                                            fg=ACCENT_GREEN if new_val else ACCENT_RED)
        self.save_settings()
        if hasattr(self, 'tray') and self.tray:
            try:
                self.tray.update_menu()
            except Exception:
                pass

    def on_recirc_override_change(self):
        val_str = self.var_recirc_override.get().strip()
        if not val_str:
            self.calc.recirc_override = None
        else:
            try:
                val = float(val_str)
                if val > 100.0:
                    self.var_recirc_override.set("100")
                    val = 100.0
                self.calc.recirc_override = max(0.0, val)
            except ValueError:
                pass
        self.update_calculations(source="demand")

    def reset_recirc_override(self):
        self.var_recirc_override.set("")
        self.calc.recirc_override = None
        self.update_calculations(source="demand")

    def toggle_topmost_on_roblox(self):
        new_val = not self.var_topmost_on_roblox.get()
        self.var_topmost_on_roblox.set(new_val)
        self.save_settings()
        if hasattr(self, 'tray') and self.tray:
            try:
                self.tray.update_menu()
            except Exception:
                pass

    def toggle_roblox_topmost_setting(self):
        new_val = not self.var_topmost_on_roblox.get()
        self.var_topmost_on_roblox.set(new_val)
        if hasattr(self, 'btn_roblox_topmost_toggle') and self.btn_roblox_topmost_toggle.winfo_exists():
            self.btn_roblox_topmost_toggle.config(text="🟢 ENABLED" if new_val else "🔴 DISABLED",
                                                  fg=ACCENT_GREEN if new_val else ACCENT_RED)
        self.save_settings()
        if hasattr(self, 'tray') and self.tray:
            try:
                self.tray.update_menu()
            except Exception:
                pass

    def update_topmost_state(self):
        try:
            settings_open = False
            if hasattr(self, 'settings_window') and self.settings_window and self.settings_window.winfo_exists():
                settings_open = True

            suggestions_open = False
            if hasattr(self, 'suggestions_window') and self.suggestions_window and self.suggestions_window.winfo_exists():
                suggestions_open = True

            update_open = False
            if hasattr(self, 'update_window') and self.update_window and self.update_window.winfo_exists():
                update_open = True

            loading_open = False
            if hasattr(self, 'loading_window') and self.loading_window and self.loading_window.winfo_exists():
                loading_open = True

            custom_message_open = False
            if hasattr(self, 'custom_message_window') and self.custom_message_window and self.custom_message_window.winfo_exists():
                custom_message_open = True

            if (settings_open and self.settings_window) or \
               (suggestions_open and self.suggestions_window) or \
               (update_open and self.update_window) or \
               (loading_open and self.loading_window) or \
               (custom_message_open and self.custom_message_window):
                if self.root.attributes("-topmost"):
                    self.root.attributes("-topmost", False)

                if settings_open and self.settings_window:
                    if not self.settings_window.attributes("-topmost"):
                        self.settings_window.attributes("-topmost", True)
                    self.settings_window.lift()

                if suggestions_open and self.suggestions_window:
                    if not self.suggestions_window.attributes("-topmost"):
                        self.suggestions_window.attributes("-topmost", True)
                    self.suggestions_window.lift()

                if update_open and self.update_window:
                    if not self.update_window.attributes("-topmost"):
                        self.update_window.attributes("-topmost", True)
                    self.update_window.lift()

                if loading_open and self.loading_window:
                    if not self.loading_window.attributes("-topmost"):
                        self.loading_window.attributes("-topmost", True)
                    self.loading_window.lift()

                if custom_message_open and self.custom_message_window:
                    if not self.custom_message_window.attributes("-topmost"):
                        self.custom_message_window.attributes("-topmost", True)
                    self.custom_message_window.lift()
                return

            if self.is_topmost:
                if not self.root.attributes("-topmost"):
                    self.root.attributes("-topmost", True)
            elif self.topmost_on_roblox:
                hwnd = ctypes.windll.user32.GetForegroundWindow()
                if hwnd:
                    buffer_len = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
                    buffer = ctypes.create_unicode_buffer(buffer_len)
                    ctypes.windll.user32.GetWindowTextW(hwnd, buffer, buffer_len)
                    window_title = buffer.value
                    
                    import os
                    active_pid = wintypes.DWORD()
                    ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(active_pid))
                    
                    is_roblox = "Roblox" in window_title or "Realistic" in window_title
                    is_ours = (active_pid.value == os.getpid())
                    
                    if is_roblox or is_ours:
                        if not self.root.attributes("-topmost"):
                            self.root.attributes("-topmost", True)
                    else:
                        if self.root.attributes("-topmost"):
                            self.root.attributes("-topmost", False)
                else:
                    if self.root.attributes("-topmost"):
                        self.root.attributes("-topmost", False)
            else:
                if self.root.attributes("-topmost"):
                    self.root.attributes("-topmost", False)
        except Exception:
            pass

    def check_focus_loop(self):
        self.update_topmost_state()
        self.root.after(300, self.check_focus_loop)

    def check_for_updates(self):
        if not _is_compiled:
            log.info("Update check skipped (not running compiled binary).")
            return
            
        def run_check():
            import urllib.request
            import json
            try:
                threading.Event().wait(1.5)
                
                url = "https://api.github.com/repos/Hotment/rbwr_themal_calculator/releases/latest"
                req = urllib.request.Request(url, headers=UPDATE_HTTP_HEADERS)
                with urllib.request.urlopen(req, timeout=5) as response:
                    if response.status == 200:
                        data = json.loads(response.read().decode('utf-8'))
                        tag_name = data.get("tag_name", "")
                        latest_version = tag_name.lstrip('vV')
                        if latest_version and latest_version != __version__:
                            if latest_version != self.skipped_version:
                                release_notes = data.get("body", "No release details available.")
                                download_url = None
                                filename = f"RBWR_APRM_Calculator_v{latest_version}.exe"
                                for asset in data.get("assets", []):
                                    if asset.get("name", "").endswith(".exe"):
                                        filename = asset.get("name")
                                        download_url = asset.get("browser_download_url")
                                        break
                                
                                if download_url:
                                    log.info(f"Update check: New update {latest_version} is available.")
                                    self.run_on_main_thread(lambda: self.show_update_dialog(latest_version, release_notes, filename, download_url))
                                else:
                                    log.warning("Update check: Found update but no .exe asset in the release.")
                            else:
                                log.info(f"Update check: New update {latest_version} matches skipped version. Prompt suppressed.")
                        else:
                            log.info("Update check: Application is up to date.")
                    else:
                        log.warning(f"Update check: Unexpected response status from GitHub: {response.status}")
            except Exception as e:
                log.info(f"Update check skipped/failed (GitHub API offline/error): {e}")
                
        threading.Thread(target=run_check, daemon=True).start()

    def show_update_dialog(self, latest_version, release_notes, download_filename, download_url):
        if hasattr(self, 'update_window') and self.update_window and self.update_window.winfo_exists():
            self.update_window.deiconify()
            self.update_window.lift()
            self.update_window.attributes("-topmost", True)
            self.update_window.focus_force()
            return

        popup = tk.Toplevel(self.root)
        self.update_window = popup
        popup.transient(self.root)

        popup.title("Update Available")
        popup.configure(bg=BG_CARD, highlightbackground=ACCENT_CYAN, highlightcolor=ACCENT_CYAN, highlightthickness=1)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        
        # Center relative to root window
        w = 380
        h = 260
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        
        popup.geometry(f"{w}x{h}+{x}+{y}")
        
        drag_data = {"x": 0, "y": 0}
        def start_drag(event):
            drag_data["x"] = event.x
            drag_data["y"] = event.y
            
        def do_drag(event):
            dx = event.x - drag_data["x"]
            dy = event.y - drag_data["y"]
            px = popup.winfo_x() + dx
            py = popup.winfo_y() + dy

            popup.geometry(f"+{px}+{py}")
            
        title_bar = tk.Frame(popup, bg=BG_HEADER, height=30)
        title_bar.pack(fill="x", side="top")
        title_bar.bind("<Button-1>", start_drag)
        title_bar.bind("<B1-Motion>", do_drag)
        
        title_lbl = tk.Label(title_bar, text=" ⚡ SYSTEM UPDATE AVAILABLE", bg=BG_HEADER, fg=ACCENT_GOLD,
                             font=("Consolas", 9, "bold"))
        title_lbl.pack(side="left", padx=10, pady=5)
        title_lbl.bind("<Button-1>", start_drag)
        title_lbl.bind("<B1-Motion>", do_drag)

        btn_close = tk.Label(title_bar, text="✕", bg=BG_HEADER, fg=TEXT_MUTED, width=3, font=("Segoe UI", 11, "bold"), cursor="hand2")
        btn_close.pack(side="right", fill="y")
        btn_close.bind("<Button-1>", lambda e: popup.destroy())
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg=TEXT_LIGHT))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg=BG_HEADER, fg=TEXT_MUTED))
        
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
            self.execute_self_update(latest_version, download_filename, download_url)
            
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

        def on_popup_destroy(event):
            if event.widget == popup:
                self.update_window = None
                self.update_topmost_state()

        popup.bind("<Destroy>", on_popup_destroy)

    def open_suggestions_dialog(self):
        if hasattr(self, 'suggestions_window') and self.suggestions_window and self.suggestions_window.winfo_exists():
            self.suggestions_window.deiconify()
            self.suggestions_window.lift()
            self.suggestions_window.attributes("-topmost", True)
            self.suggestions_window.focus_force()
            return

        popup = tk.Toplevel(self.root)
        self.suggestions_window = popup
        popup.transient(self.root)

        popup.title("Submit Feedback & Suggestions")
        popup.configure(bg=BG_CARD, highlightbackground=ACCENT_CYAN, highlightcolor=ACCENT_CYAN, highlightthickness=1)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        
        # Center relative to root window
        w = 380
        h = 370
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        
        popup.geometry(f"{w}x{h}+{x}+{y}")
        
        drag_data = {"x": 0, "y": 0}
        def start_drag(event):
            drag_data["x"] = event.x
            drag_data["y"] = event.y
            
        def do_drag(event):
            dx = event.x - drag_data["x"]
            dy = event.y - drag_data["y"]
            px = popup.winfo_x() + dx
            py = popup.winfo_y() + dy

            popup.geometry(f"+{px}+{py}")
            
        title_bar = tk.Frame(popup, bg=BG_HEADER, height=30)
        title_bar.pack(fill="x", side="top")
        title_bar.bind("<Button-1>", start_drag)
        title_bar.bind("<B1-Motion>", do_drag)
        
        title_lbl = tk.Label(title_bar, text=" 💡 SUBMIT FEEDBACK & SUGGESTIONS", bg=BG_HEADER, fg=ACCENT_CYAN,
                             font=("Consolas", 9, "bold"))
        title_lbl.pack(side="left", padx=10, pady=5)
        title_lbl.bind("<Button-1>", start_drag)
        title_lbl.bind("<B1-Motion>", do_drag)
        
        btn_close = tk.Label(title_bar, text="✕", bg=BG_HEADER, fg=TEXT_MUTED, width=3, font=("Segoe UI", 11, "bold"), cursor="hand2")
        btn_close.pack(side="right", fill="y")
        btn_close.bind("<Button-1>", lambda e: popup.destroy())
        btn_close.bind("<Enter>", lambda e: btn_close.config(bg=ACCENT_RED, fg=TEXT_LIGHT))
        btn_close.bind("<Leave>", lambda e: btn_close.config(bg=BG_HEADER, fg=TEXT_MUTED))

        content_frame = tk.Frame(popup, bg=BG_CARD, padx=15, pady=10)
        content_frame.pack(fill="both", expand=True)
        

        lbl_warning = tk.Label(content_frame, text="⚠️ Warning: Inappropriate feedback/suggestions or spam can result in a permanent or temporary IP ban.",
                               bg=BG_CARD, fg=ACCENT_GOLD, font=("Segoe UI", 8, "bold"), justify="left", wraplength=340)
        lbl_warning.pack(anchor="w", pady=(0, 10))
        

        name_frame = tk.Frame(content_frame, bg=BG_CARD)
        name_frame.pack(fill="x", pady=(0, 5))
        
        lbl_name = tk.Label(name_frame, text="Your Name:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_name.pack(side="left")
        
        ent_name = tk.Entry(name_frame, bg=BG_MAIN, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT, 
                            disabledbackground=BG_HEADER, disabledforeground=TEXT_MUTED,
                            font=("Segoe UI", 9), bd=1, relief="solid", width=25)
        ent_name.pack(side="left", padx=(10, 0))
        ent_name.bind("<Button-1>", lambda e: ent_name.focus_force())

        popup.bind("<Button-1>", lambda e: popup.focus_force() if not isinstance(e.widget, (tk.Entry, tk.Text)) else None)
        content_frame.bind("<Button-1>", lambda e: popup.focus_force() if not isinstance(e.widget, (tk.Entry, tk.Text)) else None)
        

        var_anonymous = tk.BooleanVar(value=True)
        
        def toggle_anonymous():
            if var_anonymous.get():
                ent_name.delete(0, tk.END)
                ent_name.config(state="disabled")
            else:
                ent_name.config(state="normal")
                
        chk_anon = tk.Checkbutton(content_frame, text="Submit Anonymously", variable=var_anonymous,
                                  onvalue=True, offvalue=False, command=toggle_anonymous,
                                  bg=BG_CARD, fg=TEXT_LIGHT, selectcolor=BG_MAIN, activebackground=BG_CARD,
                                  activeforeground=TEXT_LIGHT, font=("Segoe UI", 9), bd=0, highlightthickness=0)
        chk_anon.pack(anchor="w", pady=(0, 10))
        

        ent_name.config(state="disabled")
        

        lbl_body = tk.Label(content_frame, text="Feedback / Suggestion details:", bg=BG_CARD, fg=TEXT_LIGHT, font=("Segoe UI", 9))
        lbl_body.pack(anchor="w", pady=(0, 3))
        

        txt_body = tk.Text(content_frame, bg=BG_MAIN, fg=TEXT_LIGHT, insertbackground=TEXT_LIGHT,
                           font=("Segoe UI", 9), bd=1, relief="solid", height=6, wrap="word")
        txt_body.pack(fill="both", expand=True, pady=(0, 10))
        txt_body.bind("<Button-1>", lambda e: txt_body.focus_force())
        

        lbl_status = tk.Label(content_frame, text="", bg=BG_CARD, fg=ACCENT_CYAN, font=("Segoe UI", 9, "bold"), wraplength=340, justify="center")
        lbl_status.pack(pady=(0, 5))
        

        btn_frame = tk.Frame(content_frame, bg=BG_CARD)
        btn_frame.pack(fill="x", side="bottom")
        
        submit_in_progress = False

        def perform_submit():
            nonlocal submit_in_progress
            if submit_in_progress:
                return
            sug_text = txt_body.get("1.0", tk.END).strip()
            if not sug_text:
                lbl_status.config(text="Error: Feedback details cannot be empty.", fg=ACCENT_RED)
                return
            
            name_val = ent_name.get().strip() if not var_anonymous.get() else ""
            is_anon = var_anonymous.get()
            
            lbl_status.config(text="Sending feedback...", fg=ACCENT_CYAN)
            submit_in_progress = True
            
            # Start background thread to submit
            def run_submit():
                nonlocal submit_in_progress
                import urllib.request
                import urllib.error
                import json
                
                payload = {
                    "name": name_val,
                    "suggestion": sug_text,
                    "anonymous": is_anon
                }
                
                try:
                    data_bytes = json.dumps(payload).encode('utf-8')
                    req = urllib.request.Request(
                        f"{SUGGESTIONS_SERVER_URL}/suggestions",
                        data=data_bytes,
                        headers={
                            "Content-Type": "application/json",
                            "User-Agent": "RBWR-Overlay-Client"
                        },
                        method="POST"
                    )
                    with urllib.request.urlopen(req, timeout=5) as resp:
                        if resp.status == 200:
                            def success_ui():
                                lbl_status.config(text="Feedback submitted successfully!", fg=ACCENT_GREEN)
                                txt_body.delete("1.0", tk.END)
                                popup.after(1500, popup.destroy)
                            self.run_on_main_thread(success_ui)
                        else:
                            def fail_ui():
                                nonlocal submit_in_progress
                                lbl_status.config(text=f"Error: Server returned status {resp.status}", fg=ACCENT_RED)
                                submit_in_progress = False
                            self.run_on_main_thread(fail_ui)
                except urllib.error.HTTPError as he:
                    # Read the error body synchronously on the background thread
                    reason = he.reason
                    try:
                        body = he.read().decode('utf-8')
                        detail = json.loads(body).get("detail", reason)
                    except Exception:
                        detail = reason
                    
                    def http_err_ui():
                        nonlocal submit_in_progress
                        lbl_status.config(text=f"Error: {detail}", fg=ACCENT_RED)
                        submit_in_progress = False
                    self.run_on_main_thread(http_err_ui)
                except Exception as ex:
                    def err_ui():
                        nonlocal submit_in_progress
                        lbl_status.config(text="Error: Connection to server failed.", fg=ACCENT_RED)
                        submit_in_progress = False
                    self.run_on_main_thread(err_ui)
                    
            threading.Thread(target=run_submit, daemon=True).start()


        btn_submit = tk.Label(btn_frame, text="Submit", bg=BG_MAIN, fg=ACCENT_GREEN,
                              font=("Segoe UI", 9, "bold"), bd=1, relief="solid", padx=15, pady=5, cursor="hand2")
        btn_submit.pack(side="right", padx=(5, 0))
        btn_submit.bind("<Button-1>", lambda e: perform_submit())
        btn_submit.bind("<Enter>", lambda e: btn_submit.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_submit.bind("<Leave>", lambda e: btn_submit.config(bg=BG_MAIN, fg=ACCENT_GREEN))
        

        btn_cancel = tk.Label(btn_frame, text="Cancel", bg=BG_MAIN, fg=TEXT_MUTED,
                              font=("Segoe UI", 9, "bold"), bd=1, relief="solid", padx=15, pady=5, cursor="hand2")
        btn_cancel.pack(side="right")
        btn_cancel.bind("<Button-1>", lambda e: popup.destroy())
        btn_cancel.bind("<Enter>", lambda e: btn_cancel.config(bg=BG_HEADER, fg=TEXT_LIGHT))
        btn_cancel.bind("<Leave>", lambda e: btn_cancel.config(bg=BG_MAIN, fg=TEXT_MUTED))

        def on_popup_destroy(event):
            if event.widget == popup:
                self.suggestions_window = None
                self.update_topmost_state()

        popup.bind("<Destroy>", on_popup_destroy)
        popup.focus_force()

    def execute_self_update(self, latest_version, download_filename, download_url):
        if hasattr(self, 'loading_window') and self.loading_window and self.loading_window.winfo_exists():
            self.loading_window.lift()
            self.loading_window.attributes("-topmost", True)
            self.loading_window.focus_force()
            return

        loading = tk.Toplevel(self.root)
        self.loading_window = loading
        loading.transient(self.root)

        loading.title("Downloading Update")
        loading.configure(bg=BG_CARD, highlightbackground=ACCENT_CYAN, highlightcolor=ACCENT_CYAN, highlightthickness=1)
        loading.overrideredirect(True)
        loading.attributes("-topmost", True)
        
        # Center relative to root window
        w = 300
        h = 120
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        
        loading.geometry(f"{w}x{h}+{x}+{y}")
        
        drag_data = {"x": 0, "y": 0}
        def start_drag(event):
            drag_data["x"] = event.x
            drag_data["y"] = event.y
            
        def do_drag(event):
            dx = event.x - drag_data["x"]
            dy = event.y - drag_data["y"]
            px = loading.winfo_x() + dx
            py = loading.winfo_y() + dy

            loading.geometry(f"+{px}+{py}")
            
        loading.bind("<Button-1>", start_drag)
        loading.bind("<B1-Motion>", do_drag)
        
        lbl_status = tk.Label(loading, text="⚡ DOWNLOADING SYSTEM UPDATE...", bg=BG_CARD, fg=ACCENT_CYAN, font=("Consolas", 10, "bold"))
        lbl_status.pack(pady=(25, 5))
        lbl_status.bind("<Button-1>", start_drag)
        lbl_status.bind("<B1-Motion>", do_drag)
        
        lbl_sub = tk.Label(loading, text=f"Fetching v{latest_version}...", bg=BG_CARD, fg=TEXT_MUTED, font=("Consolas", 8))
        lbl_sub.pack(pady=(0, 15))
        lbl_sub.bind("<Button-1>", start_drag)
        lbl_sub.bind("<B1-Motion>", do_drag)
        
        def do_download():
            import urllib.request
            import subprocess
            import sys
            from tkinter import messagebox
            
            try:
                current_exe = sys.argv[0] if _is_compiled else sys.executable
                exe_dir = os.path.dirname(os.path.abspath(current_exe))
                new_exe_path = os.path.join(exe_dir, download_filename)
                
                url = download_url
                req = urllib.request.Request(url, headers=UPDATE_HTTP_HEADERS)
                
                with urllib.request.urlopen(req, timeout=30) as response:
                    if response.status == 200:
                        with open(new_exe_path, "wb") as f:
                            f.write(response.read())
                
                threading.Event().wait(1.0)
                
                def update_success_ui_and_reboot():
                    lbl_status.config(text="⚡ REBOOTING OVERLAY...", fg=ACCENT_GREEN)
                    lbl_sub.config(text="Deleting old version & starting new one...")
                    loading.update()
                    cmd_script = f'timeout /t 2 /nobreak && del "{current_exe}" && start "" "{new_exe_path}"'
                    subprocess.Popen(f'cmd.exe /c {cmd_script}', shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    self.quit_app()

                self.run_on_main_thread(update_success_ui_and_reboot)
            except Exception as err:
                log.error(f"Self-update failed: {err}")
                def handle_err():
                    loading.destroy()
                    self.show_custom_message("Update Error", f"Failed to execute self-update:\n{err}", is_error=True)
                self.run_on_main_thread(handle_err)
                
        threading.Thread(target=do_download, daemon=True).start()

        def on_loading_destroy(event):
            if event.widget == loading:
                self.loading_window = None
                self.update_topmost_state()

        loading.bind("<Destroy>", on_loading_destroy)

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
                    if hasattr(self, 'var_usage') and self.var_usage:
                        self.var_usage.set(f"{self.calc.usage:.2f}")
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
                    
                    # Update dynamic usage
                    u_calc = self.calc.usage_calc1 if self.calc.selected_unit == 1 else self.calc.usage_calc2
                    self.calc.usage = u_calc.calculate_usage(flow, thermal_val, override_speed=self.calc.recirc_override)
                    
                    demand = round(gen_load - self.calc.usage, 2)
                    if demand < 0:
                        demand = 0.0
                    
                    self.var_demand.set(f"{demand:.2f}")
                    if hasattr(self, 'var_usage') and self.var_usage:
                        self.var_usage.set(f"{self.calc.usage:.2f}")
                    
                    self.render_outputs(thermal_val, flow, gen_load)
        except Exception as e:
            self.show_error_state()
        finally:
            self.updating_fields = False

    def render_outputs(self, thermal, flow, gen_load):
        limit = 110 if self.calc.selected_unit == 1 else 115
        unit_suffix = "APRM" if self.calc.selected_unit == 1 else "RTP"
        if not self.is_compact:
            self.lbl_gen_val.config(text=f"⚡ {gen_load:.2f} MWe", fg=ACCENT_CYAN)
            self.lbl_feed_val.config(text=f"💧 {flow:.2f} kg/s", fg=ACCENT_GOLD)
            self.lbl_neon_rtp.config(text=f"{thermal:.2f}% {unit_suffix}")
            
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
                self.lbl_compact_rtp.config(text=f"{thermal:.1f}% {unit_suffix}", fg=ACCENT_RED)
            else:
                self.lbl_compact_rtp.config(text=f"{thermal:.1f}% {unit_suffix}", fg=ACCENT_CYAN)
            self.lbl_compact_flow.config(text=f"[{int(flow)} kg/s]", fg=TEXT_MUTED)
            
            if hasattr(self, 'telemetry_frame') and self.telemetry_frame and self.telemetry_frame.winfo_exists():
                x_pos = 280 if thermal >= 100 else 288
                self.telemetry_frame.place(x=x_pos)

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
            if hasattr(self, 'telemetry_frame') and self.telemetry_frame and self.telemetry_frame.winfo_exists():
                self.telemetry_frame.place(x=288)


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    app = OverlayApp(root)
    root.mainloop()