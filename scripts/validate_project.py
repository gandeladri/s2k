from __future__ import annotations

import json
import sys
import tempfile
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


def _validate_settings_bootstrap() -> int:
    failures = 0

    try:
        from frontend.windows.bootstrap import bootstrap_settings

        with tempfile.TemporaryDirectory(prefix="s2k_settings_test_") as tmp_dir:
            base_path = Path(tmp_dir)
            manager, voices = bootstrap_settings(str(base_path))

            settings_file = base_path / "settings.json"
            created_ok = settings_file.exists()
            _print_result("settings bootstrap creates file", created_ok, str(settings_file))
            if not created_ok:
                failures += 1
                return failures

            with settings_file.open("r", encoding="utf-8") as file:
                data = json.load(file)

            keys_ok = set(data.keys()) == {
                "auto_open_google_translate",
                "copy_to_clipboard",
                "play_audio",
                "selected_voice",
            }
            _print_result("settings bootstrap keys", keys_ok, str(sorted(data.keys())))
            if not keys_ok:
                failures += 1

            selected_voice = data.get("selected_voice")
            selected_voice_ok = (
                selected_voice is None
                or any(voice.id == selected_voice for voice in voices)
            )
            _print_result("settings selected_voice normalized", selected_voice_ok, repr(selected_voice))
            if not selected_voice_ok:
                failures += 1

            manager.update_setting("play_audio", False)
            persisted_ok = False
            try:
                with settings_file.open("r", encoding="utf-8") as file:
                    reloaded = json.load(file)
                persisted_ok = reloaded.get("play_audio") is False
            except Exception as exc:
                _print_result("settings reload after update", False, repr(exc))
                failures += 1
            else:
                _print_result("settings persist immediate update", persisted_ok)
                if not persisted_ok:
                    failures += 1

    except Exception as exc:
        _print_result("settings bootstrap", False, repr(exc))
        failures += 1

    return failures


def validate_project() -> int:
    _add_project_root_to_path()

    failures = 0
    print("=== S2K project validation ===")

    for rel in (
        "run_windows.py",
        "main.py",
        "frontend/windows/app.py",
        "frontend/windows/bootstrap.py",
        "frontend/windows/settings_manager.py",
        "frontend/windows/tts_utils.py",
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

    failures += _validate_settings_bootstrap()

    exe_path = project_root() / "dist" / "s2k.exe"
    _print_result("windows exe present (optional build output)", exe_path.exists(), str(exe_path))

    if failures:
        print(f"Validation finished with {failures} blocking issue(s).")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate_project())
