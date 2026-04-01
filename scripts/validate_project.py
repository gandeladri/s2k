from __future__ import annotations

import sys
from pathlib import Path


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _add_project_root_to_path() -> None:
    root_str = str(project_root())
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def _print_result(label: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{status}] {label}{suffix}")


def _check_exists(relative_path: str) -> bool:
    path = project_root() / relative_path
    ok = path.exists()
    _print_result(relative_path, ok, str(path))
    return ok


def validate_project() -> int:
    _add_project_root_to_path()

    failures = 0
    print("=== S2K project validation ===")

    for rel in (
        "run_windows.py",
        "main.py",
        "frontend/windows/app.py",
        "core/converter.py",
        "core/katakana_client.py",
        "assets/icons/s2k.ico",
        "scripts/build.py",
        "scripts/build_windows.py",
    ):
        if not _check_exists(rel):
            failures += 1

    try:
        from core.converter import convert_text
        from core.katakana_client import KatakanaClient

        result = convert_text("Hola Uruguay")
        ok = isinstance(result, str) and bool(result.strip())
        _print_result("core.convert_text", ok, result)
        if not ok:
            failures += 1

        cached = KatakanaClient()
        cached.cache["test"] = "テスト"
        katakana_ok = cached.english_word_to_katakana("test") == "テスト"
        _print_result("core.KatakanaClient cache path", katakana_ok)
        if not katakana_ok:
            failures += 1
    except Exception as exc:
        _print_result("core imports", False, repr(exc))
        failures += 1

    try:
        from frontend.windows.app import SpanishToKatanaConverterApp, run_app

        windows_ok = callable(run_app) and SpanishToKatanaConverterApp is not None
        _print_result("frontend.windows import", windows_ok)
        if not windows_ok:
            failures += 1
    except Exception as exc:
        _print_result("frontend.windows import", False, repr(exc))
        failures += 1

    exe_path = project_root() / "dist" / "s2k.exe"
    _print_result("windows exe present", exe_path.exists(), str(exe_path))

    if failures:
        print(f"Validation finished with {failures} blocking issue(s).")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate_project())
