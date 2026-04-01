from frontend.windows.settings_manager import SettingsManager

from frontend.windows.tts_utils import JapaneseVoice, get_japanese_voices


def bootstrap_settings(base_path: str) -> tuple[SettingsManager, list[JapaneseVoice]]:
    manager = SettingsManager(base_path)
    voices = get_japanese_voices()

    available_voice_ids = {voice.id for voice in voices}
    selected_voice = manager.settings.get("selected_voice")
    normalized_selected_voice = selected_voice if selected_voice in available_voice_ids else (voices[0].id if voices else None)

    if selected_voice != normalized_selected_voice:
        manager.settings["selected_voice"] = normalized_selected_voice
        manager.save_settings()
    else:
        manager.persist_if_needed()

    return manager, voices
