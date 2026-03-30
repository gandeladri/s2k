# Spanish to Katakana (S2K)

Convert Spanish text into Katakana through an intermediate phonetic English representation.

This project provides a **windows application** built around a shared core conversion engine.

---

## ✨ Features

- Spanish → English phonetic → Katakana conversion
- Windows app (Windows executable)
- Shared core logic
- Automated build scripts
- Validation tools for project integrity

---

## 🏗️ Project Structure

```
s2k/
│
├── core/
├── frontend/
│   └── windows/
│
├── scripts/
│   ├── build.py
│   ├── build_windows.py
│   └── validate_project.py
│
├── assets/
│   └── icons/
│
├── requirements-windows.txt
└── README.md
```

---

## ⚙️ Requirements

### Windows (Windows)
- Python 3.10+
- pip

---

## 🚀 Quick Start

### Install dependencies

```
pip install -r requirements-windows.txt
```

---

## 🖥️ Run

```
python run_windows.py
```

---

## 🏗️ Build

```
python scripts/build.py --windows
```

---

## 🧪 Validation

```
python scripts/build.py --validate
```

---

## 📄 License

Private / Internal
