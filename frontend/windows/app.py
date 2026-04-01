import base64
import ctypes
import os
import subprocess
import sys
import threading
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from tkinter import ttk
from urllib.parse import quote

from core import KatakanaClient, convert_text

APP_TITLE = "Spanish to Katana Converter"
E2K_WEB_URL = "https://www.sljfaq.org/cgi/e2k.cgi"
GOOGLE_TRANSLATE_BASE_URL = "https://translate.google.com/?sl=ja&tl=es&text={text}&op=translate"

BG_COLOR = "#1e1e1e"
SURFACE_COLOR = "#252526"
TEXT_COLOR = "#f3f3f3"
MUTED_TEXT_COLOR = "#d6d6d6"
ACCENT_COLOR = "#3a86ff"
BORDER_COLOR = "#3c3c3c"
INSERT_COLOR = "#ffffff"
SCROLL_TROUGH_COLOR = "#2a2a2a"
SCROLL_BG_COLOR = "#4a4a4a"


def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def enable_dark_title_bar(window: tk.Tk) -> bool:
    if sys.platform != "win32":
        return False

    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())

        value = ctypes.c_int(1)
        immersive_dark_mode = 20
        immersive_dark_mode_before_20h1 = 19

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
            immersive_dark_mode,
            ctypes.byref(value),
            ctypes.sizeof(value),
        )

        if result != 0:
            result = set_attr(
                hwnd,
                immersive_dark_mode_before_20h1,
                ctypes.byref(value),
                ctypes.sizeof(value),
            )

        ctypes.windll.user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, 0x0027)
        return result == 0
    except Exception:
        return False


class SpanishToKatanaConverterApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("980x860")
        self.root.minsize(820, 700)
        self.root.iconbitmap(resource_path("assets/icons/s2k.ico"))

        self.katakana_client = KatakanaClient()
        self.last_katakana_output = ""
        self.auto_open_translate_var = tk.BooleanVar(value=True)
        self.auto_copy_var = tk.BooleanVar(value=True)
        self.auto_play_var = tk.BooleanVar(value=True)
        self.current_tts_process: subprocess.Popen[str] | None = None
        self.tts_lock = threading.Lock()

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
            background=[("active", "#4d95ff"), ("disabled", "#444444")],
            foreground=[("disabled", "#bbbbbb")],
        )
        style.configure(
            "TCheckbutton",
            background=BG_COLOR,
            foreground=MUTED_TEXT_COLOR,
            font=self.button_font,
        )
        style.map(
            "TCheckbutton",
            background=[("active", BG_COLOR)],
            foreground=[("disabled", "#888888")],
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

    def on_enter_pressed(self, event: tk.Event) -> str:
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
        for index in range(6):
            button_frame.columnconfigure(index, weight=0)
        button_frame.columnconfigure(6, weight=1)

        self.convert_button = ttk.Button(button_frame, text="convert", command=self.on_convert)
        self.convert_button.grid(row=0, column=0, padx=(0, 10), sticky="w")

        self.open_e2k_button = ttk.Button(button_frame, text="e2k", command=self.open_e2k_page)
        self.open_e2k_button.grid(row=0, column=1, padx=(0, 10), sticky="w")

        self.open_translate_button = ttk.Button(
            button_frame,
            text="google translate",
            command=self.open_google_translate,
        )
        self.open_translate_button.grid(row=0, column=2, sticky="w")

        self.auto_open_translate_check = ttk.Checkbutton(
            button_frame,
            text="auto",
            variable=self.auto_open_translate_var,
        )
        self.auto_open_translate_check.grid(row=0, column=3, padx=(10, 0), sticky="w")

        self.auto_copy_check = ttk.Checkbutton(
            button_frame,
            text="copy",
            variable=self.auto_copy_var,
        )
        self.auto_copy_check.grid(row=0, column=4, padx=(10, 0), sticky="w")

        self.auto_play_check = ttk.Checkbutton(
            button_frame,
            text="play",
            variable=self.auto_play_var,
        )
        self.auto_play_check.grid(row=0, column=5, padx=(10, 0), sticky="w")

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

    def copy_to_clipboard(self, value: str) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        self.root.update()

    def stop_current_playback(self) -> None:
        if sys.platform != "win32":
            return

        with self.tts_lock:
            process = self.current_tts_process
            self.current_tts_process = None

        if process is None:
            return

        if process.poll() is None:
            try:
                process.terminate()
                process.wait(timeout=1)
            except Exception:
                try:
                    process.kill()
                except Exception:
                    pass

    def play_katakana_async(self, value: str) -> None:
        if sys.platform != "win32":
            return

        text = value.strip()
        if not text:
            return

        self.stop_current_playback()
        threading.Thread(target=self._play_katakana_worker, args=(text,), daemon=True).start()

    def _play_katakana_worker(self, value: str) -> None:
        encoded_text = base64.b64encode(value.encode("utf-8")).decode("ascii")
        command = (
            "Add-Type -AssemblyName System.Speech;"
            f'$encoded = "{encoded_text}";'
            '$text = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($encoded));'
            '$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer;'
            '$voice = $synth.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo } | '
            'Where-Object { $_.Culture.Name -like "ja*" } | Select-Object -First 1;'
            'if ($null -eq $voice) { exit 0 };'
            '$synth.SelectVoice($voice.Name);'
            '$synth.Speak($text);'
        )

        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        try:
            process = subprocess.Popen(
                [
                    "powershell",
                    "-NoProfile",
                    "-ExecutionPolicy",
                    "Bypass",
                    "-Command",
                    command,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                text=True,
                creationflags=creation_flags,
            )
        except Exception:
            return

        with self.tts_lock:
            self.current_tts_process = process

        try:
            process.wait()
        finally:
            with self.tts_lock:
                if self.current_tts_process is process:
                    self.current_tts_process = None

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

        is_valid_result = (
            bool(self.last_katakana_output)
            and not self.last_katakana_output.lower().startswith("error:")
        )

        if is_valid_result and self.auto_copy_var.get():
            self.copy_to_clipboard(self.last_katakana_output)

        if is_valid_result and self.auto_open_translate_var.get():
            self.open_google_translate()

        if is_valid_result and self.auto_play_var.get():
            self.play_katakana_async(self.last_katakana_output)


def run_app() -> None:
    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.15)
    except Exception:
        pass

    app = SpanishToKatanaConverterApp(root)
    enable_dark_title_bar(root)
    app.input_text.focus_set()

    try:
        root.mainloop()
    finally:
        app.stop_current_playback()


main = run_app


if __name__ == "__main__":
    run_app()
