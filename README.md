# Spanish to Katana Converter (S2K)

A Windows application that converts Spanish text into phonetically accurate Katakana, with optional Google Translate integration and optional Japanese TTS playback.

---

## Download (Windows)

Download the latest version here:

👉 https://github.com/gandeladri/s2k/releases/latest/download/s2k.exe

---

## Run from Source

```bash
python run_windows.py
```

---

## Build (Windows)

```bash
python scripts/build_windows.py
```

Or:

```bash
python scripts/build.py --windows
```

---

## Validate Project

```bash
python scripts/build.py --validate
```

---

## Requirements

```bash
pip install -r requirements-windows.txt
pip install pyinstaller
```

---

## settings.json

The app creates `settings.json` automatically on first run.

It stores these keys:

```json
{
  "auto_open_google_translate": true,
  "copy_to_clipboard": true,
  "play_audio": true,
  "selected_voice": null
}
```

### Location

- In the packaged `.exe`: next to `s2k.exe`
- In source mode: next to the script used to launch the app

### Behavior

- If the file does not exist, it is created automatically.
- If the file is partially invalid, missing values are recovered silently.
- If the file is fully invalid JSON, the app falls back silently to default settings and rewrites the file when possible.
- Changes in the UI are persisted immediately.
- If the saved Japanese voice no longer exists, the app falls back silently to the first available Japanese voice.

---

## Notes

- The application is designed specifically for Windows.
- The executable is built using PyInstaller.
- If rebuilding with a new icon, Windows may cache the old one — restart Explorer if needed.
- The TTS voice dropdown only lists installed Japanese voices (`ja-*`).
- If no Japanese voice is installed, playback stays available but audio may not be heard.
