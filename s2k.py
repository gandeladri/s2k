import json
import re
import unicodedata
from pathlib import Path
import tkinter as tk
from tkinter import ttk
import tkinter.font as tkfont
import requests
import ctypes
import sys
import webbrowser
from urllib.parse import quote

APP_TITLE = "Spanish to Katana Converter"
EXCEPTIONS_FILE = "spanish_phonetizer_exceptions.json"

BASE_URL = "https://www.sljfaq.org/cgi/e2k.cgi"
LANG = "en"
TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"

WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")
API_TOKEN_RE = re.compile(r"[a-z]+|[^a-z]+")
VOWELS = "aeiouáéíóúü"

DEFAULT_EXCEPTIONS = {
    "uruguay": "ooroogooy",
    "montevideo": "montebeedeyo",
    "buenos": "bwenos",
    "aires": "aires",
    "youtube": "yootoob",
    "wifi": "waifai",
    "whatsapp": "guatsap",
    "ok": "ok",
}

BG_COLOR = "#1e1e1e"
SURFACE_COLOR = "#252526"
TEXT_COLOR = "#f3f3f3"
MUTED_TEXT_COLOR = "#d6d6d6"
ACCENT_COLOR = "#3a86ff"
BORDER_COLOR = "#3c3c3c"
INSERT_COLOR = "#ffffff"
SCROLL_TROUGH_COLOR = "#2a2a2a"
SCROLL_BG_COLOR = "#4a4a4a"

E2K_WEB_URL = "https://www.sljfaq.org/cgi/e2k.cgi"
GOOGLE_TRANSLATE_BASE_URL = "https://translate.google.com/?sl=ja&tl=es&text={text}&op=translate"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # .exe
    except Exception:
        base_path = os.path.abspath(".")  # .py
    return os.path.join(base_path, relative_path)

def enable_dark_title_bar(window: tk.Tk) -> bool:
    if sys.platform != "win32":
        return False

    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())

        value = ctypes.c_int(1)
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19

        dwmapi = ctypes.windll.dwmapi
        set_attr = dwmapi.DwmSetWindowAttribute
        set_attr.argtypes = [
            ctypes.c_void_p,
            ctypes.c_uint,
            ctypes.c_void_p,
            ctypes.c_uint,
        ]
        set_attr.restype = ctypes.c_int

        result = set_attr(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )

        if result != 0:
            result = set_attr(
                hwnd,
                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )

        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)
        return result == 0
    except Exception:
        return False



def load_exceptions() -> dict[str, str]:
    path = Path(__file__).with_name(EXCEPTIONS_FILE)
    if not path.exists():
        return DEFAULT_EXCEPTIONS.copy()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return DEFAULT_EXCEPTIONS.copy()
        merged = DEFAULT_EXCEPTIONS.copy()
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, str):
                merged[key.lower()] = value.lower()
        return merged
    except Exception:
        return DEFAULT_EXCEPTIONS.copy()


EXCEPTIONS = load_exceptions()



def is_vowel(ch: str) -> bool:
    return ch in VOWELS



def normalize_spanish_word(word: str) -> str:
    return word.lower()



def should_keep_word(word: str) -> bool:
    lower = word.lower()
    if any(ch.isdigit() for ch in lower):
        return True
    vowels = sum(1 for ch in lower if is_vowel(ch))
    if vowels == 0:
        return True
    return False



def join_phonetic_parts(parts: list[str]) -> str:
    result = "".join(parts)
    replacements = {
        "hhh": "hh",
        "yyy": "yy",
        "oooo": "ooo",
        "eeee": "eee",
    }
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result



def spanish_to_phonetic_word(word: str) -> str:
    original = normalize_spanish_word(word)

    if original in EXCEPTIONS:
        return EXCEPTIONS[original]

    if should_keep_word(original):
        return original

    chars = list(original)
    parts: list[str] = []
    i = 0
    length = len(chars)

    while i < length:
        ch = chars[i]
        nxt = chars[i + 1] if i + 1 < length else ""
        nxt2 = chars[i + 2] if i + 2 < length else ""

        if ch == "c" and nxt == "h":
            parts.append("ch")
            i += 2
            continue

        if ch == "l" and nxt == "l":
            parts.append("y")
            i += 2
            continue

        if ch == "r" and nxt == "r":
            parts.append("r")
            i += 2
            continue

        if ch == "q" and nxt == "u":
            if nxt2 in "eiéí":
                parts.append("k")
                i += 2
                continue
            parts.append("k")
            i += 1
            continue

        if ch == "g" and nxt == "u" and nxt2 in "eéií":
            parts.append("g")
            i += 2
            continue

        if ch == "g" and nxt == "ü" and nxt2 in "eéií":
            parts.append("gw")
            i += 2
            continue

        if ch in "aá":
            parts.append("ah")
            i += 1
            continue
        if ch in "eé":
            parts.append("eh")
            i += 1
            continue
        if ch in "ií":
            parts.append("ee")
            i += 1
            continue
        if ch in "oó":
            parts.append("oh")
            i += 1
            continue
        if ch in "uúü":
            parts.append("oo")
            i += 1
            continue

        if ch in ("b", "v"):
            parts.append("b")
            i += 1
            continue

        if ch == "c":
            if nxt in "eéií":
                parts.append("s")
            else:
                parts.append("k")
            i += 1
            continue

        if ch == "d":
            parts.append("d")
            i += 1
            continue

        if ch == "f":
            parts.append("f")
            i += 1
            continue

        if ch == "g":
            if nxt in "eéií":
                parts.append("h")
            else:
                parts.append("g")
            i += 1
            continue

        if ch == "h":
            i += 1
            continue

        if ch == "j":
            parts.append("h")
            i += 1
            continue

        if ch == "k":
            parts.append("k")
            i += 1
            continue

        if ch == "l":
            parts.append("l")
            i += 1
            continue

        if ch == "m":
            parts.append("m")
            i += 1
            continue

        if ch == "n":
            parts.append("n")
            i += 1
            continue

        if ch == "ñ":
            parts.append("ny")
            i += 1
            continue

        if ch == "p":
            parts.append("p")
            i += 1
            continue

        if ch == "r":
            parts.append("r")
            i += 1
            continue

        if ch == "s":
            parts.append("s")
            i += 1
            continue

        if ch == "t":
            parts.append("t")
            i += 1
            continue

        if ch == "w":
            parts.append("w")
            i += 1
            continue

        if ch == "x":
            parts.append("ks")
            i += 1
            continue

        if ch == "y":
            if i == length - 1:
                parts.append("ee")
            else:
                parts.append("y")
            i += 1
            continue

        if ch == "z":
            parts.append("s")
            i += 1
            continue

        parts.append(ch)
        i += 1

    return join_phonetic_parts(parts)



def convert_text(text: str) -> str:
    tokens = WORD_RE.findall(text)
    converted: list[str] = []

    for token in tokens:
        if re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", token):
            converted.append(spanish_to_phonetic_word(token))
        else:
            converted.append(token)

    return "".join(converted).lower()


class KatakanaClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,es;q=0.8",
            "referer": "https://www.sljfaq.org/cgi/e2k.cgi",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": USER_AGENT,
        })
        self.initialized = False
        self.cache: dict[str, str] = {}

    def init_session(self) -> None:
        if self.initialized:
            return
        response = self.session.get(BASE_URL, timeout=TIMEOUT)
        response.raise_for_status()
        self.initialized = True

    def english_word_to_katakana(self, word: str) -> str:
        normalized = word.strip().lower()
        if not normalized:
            return normalized

        cached = self.cache.get(normalized)
        if cached is not None:
            return cached

        self.init_session()
        response = self.session.get(
            BASE_URL,
            params={"o": "json", "word": normalized, "lang": LANG},
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()

        if data.get("check_captcha"):
            raise RuntimeError("captcha requerido por la api")

        if data.get("error_msg"):
            raise RuntimeError(str(data.get("error_msg")))

        words = data.get("words") or []
        parts: list[str] = []
        for item in words:
            value = item.get("j_pron_spell") or item.get("j_pron_only")
            if value:
                parts.append(value.strip())

        result = " ".join(part for part in parts if part).strip()
        if not result:
            result = normalized

        self.cache[normalized] = result
        return result

    def english_text_to_katakana(self, text: str) -> str:
        tokens = API_TOKEN_RE.findall(text.lower())
        converted: list[str] = []

        for token in tokens:
            if re.fullmatch(r"[a-z]+", token):
                converted.append(self.english_word_to_katakana(token))
            else:
                converted.append(token)

        return "".join(converted)


class SpanishToKatanaConverterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("980x860")
        self.root.minsize(820, 700)
        self.root.iconbitmap(resource_path("s2k.ico"))

        self.katakana_client = KatakanaClient()
        self.last_katakana_output = ""

        self.configure_styles()
        self.build_ui()
        self.update_google_translate_button_state()

    def configure_styles(self) -> None:
        self.base_font = tkfont.nametofont("TkDefaultFont").copy()
        self.base_font.configure(size=13)

        self.label_font = tkfont.Font(family=self.base_font.cget("family"), size=14, weight="bold")
        self.button_font = tkfont.Font(family=self.base_font.cget("family"), size=13)
        self.text_font = tkfont.Font(family="Segoe UI", size=14)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.root.configure(bg=BG_COLOR)

        style.configure("TFrame", background=BG_COLOR)

        style.configure(
            "TLabel",
            font=self.label_font,
            background=BG_COLOR,
            foreground=MUTED_TEXT_COLOR,
        )

        style.configure(
            "TButton",
            font=self.button_font,
            padding=(18, 10),
            background=ACCENT_COLOR,
            foreground=TEXT_COLOR,
            borderwidth=0,
            focuscolor=ACCENT_COLOR,
        )

        style.map(
            "TButton",
            background=[
                ("active", "#4d95ff"),
                ("disabled", "#444444"),
            ],
            foreground=[
                ("disabled", "#bbbbbb"),
            ],
        )

        style.configure(
            "Vertical.TScrollbar",
            background=SCROLL_BG_COLOR,
            troughcolor=SCROLL_TROUGH_COLOR,
            arrowcolor=TEXT_COLOR,
            bordercolor=BORDER_COLOR,
            darkcolor=SCROLL_BG_COLOR,
            lightcolor=SCROLL_BG_COLOR,
        )

    def on_enter_pressed(self, event):
        self.on_convert()
        return "break"

    def build_ui(self) -> None:
        container = ttk.Frame(self.root, padding=16, style="TFrame")
        container.pack(fill="both", expand=True)

        container.columnconfigure(0, weight=1)
        container.rowconfigure(1, weight=1)
        container.rowconfigure(4, weight=1)
        container.rowconfigure(6, weight=1)

        input_label = ttk.Label(container, text="spanish input")
        input_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        self.input_text = self.create_text_widget(container, row=1)
        self.input_text.bind("<Return>", self.on_enter_pressed)

        button_frame = ttk.Frame(container, style="TFrame")
        button_frame.grid(row=2, column=0, sticky="ew", pady=16)
        button_frame.columnconfigure(0, weight=0)
        button_frame.columnconfigure(1, weight=0)
        button_frame.columnconfigure(2, weight=0)
        button_frame.columnconfigure(3, weight=1)

        self.convert_button = ttk.Button(button_frame, text="convert", command=self.on_convert)
        self.convert_button.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.open_e2k_button = ttk.Button(
            button_frame,
            text="e2k",
            command=self.open_e2k_page,
        )
        self.open_e2k_button.grid(row=0, column=1, padx=(0, 10), sticky="w")

        self.open_translate_button = ttk.Button(
            button_frame,
            text="google translate",
            command=self.open_google_translate,
        )
        self.open_translate_button.grid(row=0, column=2, sticky="w")

        english_label = ttk.Label(container, text="phonetic english output")
        english_label.grid(row=3, column=0, sticky="w", pady=(4, 8))

        self.english_text = self.create_text_widget(container, row=4, readonly=True)

        katakana_label = ttk.Label(container, text="katakana output")
        katakana_label.grid(row=5, column=0, sticky="w", pady=(4, 8))

        self.katakana_text = self.create_text_widget(container, row=6, readonly=True)

    def create_text_widget(self, parent: ttk.Frame, row: int, readonly: bool = False) -> tk.Text:
        frame = ttk.Frame(parent, style="TFrame")
        frame.grid(row=row, column=0, sticky="nsew")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        text = tk.Text(
            frame,
            wrap="word",
            height=10,
            undo=not readonly,
            font=self.text_font,
            padx=12,
            pady=12,
            spacing1=2,
            spacing3=2,
            bg=SURFACE_COLOR,
            fg=TEXT_COLOR,
            insertbackground=INSERT_COLOR,
            selectbackground=ACCENT_COLOR,
            selectforeground=TEXT_COLOR,
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            highlightcolor=ACCENT_COLOR,
        )
        text.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=text.yview, style="Vertical.TScrollbar")
        scrollbar.grid(row=0, column=1, sticky="ns")
        text.configure(yscrollcommand=scrollbar.set)

        if readonly:
            text.configure(state="disabled")

        return text

    def set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", "end")
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def open_e2k_page(self) -> None:
        webbrowser.open_new_tab(E2K_WEB_URL)

    def build_google_translate_url(self) -> str:
        encoded_text = quote(self.last_katakana_output, safe="")
        return GOOGLE_TRANSLATE_BASE_URL.format(text=encoded_text)

    def open_google_translate(self) -> None:
        if not self.last_katakana_output.strip():
            return
        webbrowser.open_new_tab(self.build_google_translate_url())

    def update_google_translate_button_state(self) -> None:
        if self.last_katakana_output.strip():
            self.open_translate_button.state(["!disabled"])
        else:
            self.open_translate_button.state(["disabled"])

    def on_convert(self) -> None:
        raw = self.input_text.get("1.0", "end-1c")

        phonetic = convert_text(raw)
        self.set_text(self.english_text, phonetic)

        self.convert_button.state(["disabled"])
        self.root.update_idletasks()

        try:
            katakana = self.katakana_client.english_text_to_katakana(phonetic)
        except Exception as exc:
            katakana = f"error: {exc}"
        finally:
            self.convert_button.state(["!disabled"])

        self.last_katakana_output = katakana.strip()
        self.set_text(self.katakana_text, katakana)
        self.update_google_translate_button_state()



def main() -> None:
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.15)
    except Exception:
        pass
    app = SpanishToKatanaConverterApp(root)
    enable_dark_title_bar(root)
    app.input_text.focus_set()
    root.mainloop()


if __name__ == "__main__":
    main()
