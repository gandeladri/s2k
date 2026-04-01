import ctypes
import os
import sys
import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from tkinter import messagebox, ttk
from urllib.parse import quote

from core import KatakanaClient, convert_text
from frontend.windows.bootstrap import bootstrap_settings
from frontend.windows.tts_utils import WinRTSpeechPlayer

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
VOICE_DROPDOWN_WIDTH = 18
EMPTY_VOICE_PLACEHOLDER = "Empty"


WARNING_ICON_TEXT = "⚠"
WARNING_TOOLTIP_TEXT = "Japanese TTS not detected. Audio may not play."


def get_runtime_base_path() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(sys.argv[0]))


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
        self.runtime_base_path = get_runtime_base_path()
        self.settings_manager, self.japanese_voices = bootstrap_settings(self.runtime_base_path)
        self.tts_warning_shown = False
        self.tts_player = WinRTSpeechPlayer()

        self.auto_open_translate_var = tk.BooleanVar(value=self.settings_manager.settings["auto_open_google_translate"])
        self.auto_copy_var = tk.BooleanVar(value=self.settings_manager.settings["copy_to_clipboard"])
        self.auto_play_var = tk.BooleanVar(value=self.settings_manager.settings["play_audio"])
        self.voice_display_to_id: dict[str, str] = {}
        self.voice_dropdown_var = tk.StringVar()

        self.configure_styles()
        self.build_ui()
        self.refresh_japanese_voices()
        self.bind_ui_events()
        self.persist_current_ui_settings()
        self.update_google_translate_button_state()
        self.maybe_warn_missing_japanese_tts_on_startup()

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
        style.configure(
            "TCombobox",
            fieldbackground=SURFACE_COLOR,
            background=SURFACE_COLOR,
            foreground=TEXT_COLOR,
            arrowcolor=TEXT_COLOR,
            bordercolor=BORDER_COLOR,
            lightcolor=SURFACE_COLOR,
            darkcolor=SURFACE_COLOR,
            padding=(8, 4),
        )
        style.map(
            "TCombobox",
            fieldbackground=[("readonly", SURFACE_COLOR)],
            foreground=[("readonly", TEXT_COLOR)],
            selectforeground=[("readonly", TEXT_COLOR)],
            selectbackground=[("readonly", SURFACE_COLOR)],
        )

    def bind_ui_events(self) -> None:
        self.voice_dropdown.bind("<<ComboboxSelected>>", self.on_selected_voice_changed, add="+")

    def persist_setting(self, key: str, value: object) -> None:
        self.settings_manager.update_setting(key, value)

    def persist_current_ui_settings(self) -> None:
        self.persist_setting("auto_open_google_translate", self.is_auto_open_translate_enabled())
        self.persist_setting("copy_to_clipboard", self.is_auto_copy_enabled())
        self.persist_setting("play_audio", self.is_auto_play_enabled())
        self.persist_setting("selected_voice", self.get_selected_voice_id())

    def is_auto_open_translate_enabled(self) -> bool:
        return self.auto_open_translate_var.get()

    def is_auto_copy_enabled(self) -> bool:
        return self.auto_copy_var.get()

    def is_auto_play_enabled(self) -> bool:
        return self.auto_play_var.get()

    def on_auto_open_translate_changed(self) -> None:
        self.persist_setting("auto_open_google_translate", self.is_auto_open_translate_enabled())

    def on_auto_copy_changed(self) -> None:
        self.persist_setting("copy_to_clipboard", self.is_auto_copy_enabled())

    def on_auto_play_changed(self) -> None:
        is_enabled = self.is_auto_play_enabled()
        self.persist_setting("play_audio", is_enabled)
        if is_enabled:
            self.refresh_japanese_voices()
            self.maybe_warn_missing_japanese_tts()

    def on_selected_voice_changed(self, *_args: object) -> None:
        selected_display_name = self.voice_dropdown_var.get().strip()
        selected_voice_id = self.voice_display_to_id.get(selected_display_name)
        self.persist_setting("selected_voice", selected_voice_id)

    def has_japanese_voices(self) -> bool:
        return bool(self.japanese_voices)

    def get_voice_display_values(self) -> list[str]:
        if not self.japanese_voices:
            return [EMPTY_VOICE_PLACEHOLDER]
        return [voice.name for voice in self.japanese_voices]

    def get_selected_voice_display_name(self) -> str:
        selected_voice_id = self.get_selected_voice_id()
        if selected_voice_id is None:
            return EMPTY_VOICE_PLACEHOLDER

        for voice in self.japanese_voices:
            if voice.id == selected_voice_id:
                return voice.name

        return EMPTY_VOICE_PLACEHOLDER

    def maybe_warn_missing_japanese_tts_on_startup(self) -> None:
        self.refresh_japanese_voices()
        if self.is_auto_play_enabled():
            self.maybe_warn_missing_japanese_tts()

    def maybe_warn_missing_japanese_tts(self) -> None:
        if self.has_japanese_voices() or self.tts_warning_shown:
            return

        self.tts_warning_shown = True
        messagebox.showwarning(
            title="Japanese TTS not detected",
            message=(
                "No Japanese text-to-speech voice was detected on this system. "
                "Playback will remain available, but audio may not be heard until a Japanese Windows voice is installed."
            ),
        )

    def get_selected_voice_id(self) -> str | None:
        selected_voice_id = self.settings_manager.settings.get("selected_voice")
        for voice in self.japanese_voices:
            if voice.id == selected_voice_id:
                return voice.id

        fallback_voice_id = self.japanese_voices[0].id if self.japanese_voices else None
        if selected_voice_id != fallback_voice_id:
            self.persist_setting("selected_voice", fallback_voice_id)
        return fallback_voice_id

    def refresh_japanese_voices(self) -> None:
        previous_display_name = self.voice_dropdown_var.get().strip()
        previous_voice_id = self.voice_display_to_id.get(previous_display_name)

        self.japanese_voices = bootstrap_settings(self.runtime_base_path)[1]
        self.voice_display_to_id = {voice.name: voice.id for voice in self.japanese_voices}

        selected_voice_id = self.settings_manager.settings.get("selected_voice")
        available_voice_ids = {voice.id for voice in self.japanese_voices}

        if selected_voice_id not in available_voice_ids:
            selected_voice_id = self.japanese_voices[0].id if self.japanese_voices else None
            if self.settings_manager.settings.get("selected_voice") != selected_voice_id:
                self.persist_setting("selected_voice", selected_voice_id)

        display_values = self.get_voice_display_values()
        self.voice_dropdown.configure(values=display_values)

        selected_display_name = EMPTY_VOICE_PLACEHOLDER
        if selected_voice_id is not None:
            for voice in self.japanese_voices:
                if voice.id == selected_voice_id:
                    selected_display_name = voice.name
                    break
        elif previous_voice_id in available_voice_ids:
            for voice in self.japanese_voices:
                if voice.id == previous_voice_id:
                    selected_display_name = voice.name
                    break

        self.voice_dropdown_var.set(selected_display_name)
        self.on_selected_voice_changed()
        self.update_missing_tts_ui()


    def create_tooltip(self, widget: tk.Widget, text: str) -> None:
        tooltip_window: tk.Toplevel | None = None

        def show_tooltip(_event: tk.Event) -> None:
            nonlocal tooltip_window
            if tooltip_window is not None:
                return

            x = widget.winfo_rootx() + 12
            y = widget.winfo_rooty() + widget.winfo_height() + 8

            tooltip_window = tk.Toplevel(self.root)
            tooltip_window.wm_overrideredirect(True)
            tooltip_window.wm_geometry(f"+{x}+{y}")
            tooltip_window.configure(bg="#d2a106")

            label = tk.Label(
                tooltip_window,
                text=text,
                bg="#d2a106",
                fg="#111111",
                padx=8,
                pady=4,
                font=self.button_font,
                relief="solid",
                borderwidth=1,
            )
            label.pack()

        def hide_tooltip(_event: tk.Event) -> None:
            nonlocal tooltip_window
            if tooltip_window is None:
                return
            tooltip_window.destroy()
            tooltip_window = None

        widget.bind("<Enter>", show_tooltip, add="+")
        widget.bind("<Leave>", hide_tooltip, add="+")
        widget.bind("<ButtonPress>", hide_tooltip, add="+")

    def update_missing_tts_ui(self) -> None:
        if self.has_japanese_voices():
            self.missing_tts_warning_label.grid_remove()
            return

        self.missing_tts_warning_label.grid()


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
        for index in range(8):
            button_frame.columnconfigure(index, weight=0)
        button_frame.columnconfigure(8, weight=1)

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
            command=self.on_auto_open_translate_changed,
        )
        self.auto_open_translate_check.grid(row=0, column=3, padx=(10, 0), sticky="w")

        self.auto_copy_check = ttk.Checkbutton(
            button_frame,
            text="copy",
            variable=self.auto_copy_var,
            command=self.on_auto_copy_changed,
        )
        self.auto_copy_check.grid(row=0, column=4, padx=(10, 0), sticky="w")

        self.auto_play_check = ttk.Checkbutton(
            button_frame,
            text="play",
            variable=self.auto_play_var,
            command=self.on_auto_play_changed,
        )
        self.auto_play_check.grid(row=0, column=5, padx=(10, 0), sticky="w")

        self.voice_dropdown = ttk.Combobox(
            button_frame,
            textvariable=self.voice_dropdown_var,
            values=self.get_voice_display_values(),
            state="readonly",
            width=VOICE_DROPDOWN_WIDTH,
        )
        self.voice_dropdown.grid(row=0, column=6, padx=(10, 0), sticky="w")

        self.missing_tts_warning_label = tk.Label(
            button_frame,
            text=WARNING_ICON_TEXT,
            bg=BG_COLOR,
            fg="#f0c94d",
            font=tkfont.Font(family=self.base_font.cget("family"), size=13, weight="bold"),
            cursor="hand2",
        )
        self.missing_tts_warning_label.grid(row=0, column=7, padx=(8, 0), sticky="w")
        self.create_tooltip(self.missing_tts_warning_label, WARNING_TOOLTIP_TEXT)
        self.update_missing_tts_ui()

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
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(value)
            self.root.update()
        except Exception:
            pass


    def stop_current_playback(self) -> None:
        try:
            self.tts_player.stop()
        except Exception:
            pass

    def play_katakana_async(self, value: str) -> None:
        text = value.strip()
        if not text:
            return

        self.refresh_japanese_voices()
        try:
            self.tts_player.speak_async(text, self.get_selected_voice_id())
        except Exception:
            pass

    def open_e2k_page(self) -> None:
            try:
                webbrowser.open_new_tab(E2K_WEB_URL)
            except Exception:
                pass

    def build_google_translate_url(self) -> str:
        encoded_text = quote(self.last_katakana_output, safe="")
        return GOOGLE_TRANSLATE_BASE_URL.format(text=encoded_text)

    def open_google_translate(self) -> None:
        if not self.last_katakana_output.strip():
            return
        try:
            webbrowser.open_new_tab(self.build_google_translate_url())
        except Exception:
            pass

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

        if is_valid_result and self.is_auto_copy_enabled():
            self.copy_to_clipboard(self.last_katakana_output)

        if is_valid_result and self.is_auto_open_translate_enabled():
            self.open_google_translate()

        if is_valid_result and self.is_auto_play_enabled():
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
