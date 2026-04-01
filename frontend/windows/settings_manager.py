import json
import os
from typing import Any


class SettingsManager:
    FILE_NAME = "settings.json"

    def __init__(self, base_path: str) -> None:
        self.base_path = base_path
        self.file_path = os.path.join(self.base_path, self.FILE_NAME)
        self.is_persistence_available = True
        self.did_recover_from_invalid_file = False
        self.settings = self.load_settings()

    def get_default_settings(self) -> dict[str, Any]:
        return {
            "auto_open_google_translate": True,
            "copy_to_clipboard": True,
            "play_audio": True,
            "selected_voice": None,
        }

    def normalize_settings(self, data: Any) -> dict[str, Any]:
        defaults = self.get_default_settings()
        if not isinstance(data, dict):
            return defaults

        normalized = defaults.copy()
        normalized["auto_open_google_translate"] = self._coerce_bool(
            data.get("auto_open_google_translate"),
            defaults["auto_open_google_translate"],
        )
        normalized["copy_to_clipboard"] = self._coerce_bool(
            data.get("copy_to_clipboard"),
            defaults["copy_to_clipboard"],
        )
        normalized["play_audio"] = self._coerce_bool(
            data.get("play_audio"),
            defaults["play_audio"],
        )

        selected_voice = data.get("selected_voice", defaults["selected_voice"])
        normalized["selected_voice"] = selected_voice if isinstance(selected_voice, str) or selected_voice is None else defaults["selected_voice"]

        return normalized

    def _coerce_bool(self, value: Any, default: bool) -> bool:
        if isinstance(value, bool):
            return value
        return default

    def load_settings(self) -> dict[str, Any]:
        if not os.path.exists(self.file_path):
            return self.get_default_settings()

        try:
            with open(self.file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
        except Exception:
            self.did_recover_from_invalid_file = True
            return self.get_default_settings()

        normalized = self.normalize_settings(data)
        if normalized != data:
            self.did_recover_from_invalid_file = True
        return normalized

    def save_settings(self) -> bool:
        try:
            os.makedirs(self.base_path, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as file:
                json.dump(self.settings, file, indent=2)
            self.is_persistence_available = True
            return True
        except Exception:
            self.is_persistence_available = False
            return False

    def update_setting(self, key: str, value: Any) -> bool:
        defaults = self.get_default_settings()
        if key not in defaults:
            return False

        self.settings[key] = value
        self.settings = self.normalize_settings(self.settings)
        return self.save_settings()

    def replace_with_defaults(self) -> bool:
        self.settings = self.get_default_settings()
        return self.save_settings()

    def persist_if_needed(self) -> bool:
        if self.did_recover_from_invalid_file or not os.path.exists(self.file_path):
            self.did_recover_from_invalid_file = False
            return self.save_settings()
        return True
