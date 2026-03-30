# S2K – Spanish to Katakana Converter

## Rebuild Instructions

This project includes a build script to generate the executable (`.exe`) using PyInstaller.

### Requirements

Make sure you have PyInstaller installed:

```bash
pip install pyinstaller
```

---

## How to Rebuild

1. Place yourself in the project folder (where `build.py` is located)

2. Run:

```bash
python build.py
```

---

## What the Script Does

The script will automatically:

- Clean previous build artifacts:
  - `build/`
  - `dist/`
  - `s2k.spec`
- Rebuild the executable using:
  - `s2k.ico` as the application icon
- Output the final executable to:

```
dist/s2k.exe
```

---

## Important Notes

### Icon Changes

If you update `s2k.ico`, Windows may still show the old icon due to caching.

To fix this:

1. Restart Windows Explorer:

```bash
taskkill /f /im explorer.exe
start explorer.exe
```

OR

2. Rename the `.exe` file temporarily

OR

3. Move the `.exe` to a different folder

---

## Project Structure

```
build.py
s2k.py
s2k.ico
README.md
```

---

## Output

After a successful build:

```
dist/s2k.exe
```

---

## Troubleshooting

- If the icon does not appear → restart Explorer (see above)
- If build fails → ensure `pyinstaller` is installed and available in PATH
