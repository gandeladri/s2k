# Spanish to Katana Converter (S2K)

A desktop application that converts Spanish text into phonetically accurate Katakana, with optional Google Translate integration.

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

> Note: If the icon does not appear correctly after updating, restart Windows Explorer.

---

## Requirements

```bash
pip install -r requirements-windows.txt
pip install pyinstaller
```

---

## Notes

- The application is designed specifically for Windows.
- The executable is built using PyInstaller.
- If rebuilding with a new icon, Windows may cache the old one — restart Explorer if needed.
