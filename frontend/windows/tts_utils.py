from __future__ import annotations

import asyncio
import os
import sys
import tempfile
import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class JapaneseVoice:
    id: str
    name: str
    culture: str


def _is_windows() -> bool:
    return sys.platform == "win32"


def _import_speech_namespace():
    from winrt.windows.media.speechsynthesis import SpeechSynthesizer  # type: ignore
    return SpeechSynthesizer


def _import_stream_namespaces():
    from winrt.windows.storage.streams import DataReader  # type: ignore
    return DataReader


def is_winrt_tts_available() -> bool:
    if not _is_windows():
        return False

    try:
        _import_speech_namespace()
        _import_stream_namespaces()
    except Exception:
        return False

    return True


def get_japanese_voices() -> list[JapaneseVoice]:
    if not _is_windows():
        return []

    try:
        SpeechSynthesizer = _import_speech_namespace()
        all_voices = list(SpeechSynthesizer.all_voices)
    except Exception:
        return []

    voices: list[JapaneseVoice] = []
    seen_voice_ids: set[str] = set()

    for voice in all_voices:
        culture = str(getattr(voice, "language", "") or "").strip()
        if not culture.lower().startswith("ja"):
            continue

        voice_id = str(getattr(voice, "id", "") or "").strip()
        voice_name = str(getattr(voice, "display_name", "") or "").strip()

        if not voice_id:
            voice_id = voice_name or culture
        if not voice_name:
            voice_name = voice_id

        if voice_id in seen_voice_ids:
            continue

        seen_voice_ids.add(voice_id)
        voices.append(JapaneseVoice(id=voice_id, name=voice_name, culture=culture))

    return voices


class WinRTSpeechPlayer:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._worker_thread: threading.Thread | None = None
        self._current_temp_file: str | None = None

    def stop(self) -> None:
        self._stop_event.set()

        if _is_windows():
            try:
                import winsound
                winsound.PlaySound(None, 0)
            except Exception:
                pass

        worker = None
        with self._lock:
            worker = self._worker_thread

        if worker is not None and worker.is_alive() and worker is not threading.current_thread():
            worker.join(timeout=0.2)

        with self._lock:
            self._worker_thread = None

        self._cleanup_temp_file()

    def speak_async(self, text: str, selected_voice_id: str | None) -> None:
        if not is_winrt_tts_available():
            return

        normalized_text = text.strip()
        if not normalized_text:
            return

        self.stop()
        self._stop_event = threading.Event()

        worker = threading.Thread(
            target=self._run_worker,
            args=(normalized_text, selected_voice_id, self._stop_event),
            daemon=True,
        )
        with self._lock:
            self._worker_thread = worker
        worker.start()

    def _run_worker(self, text: str, selected_voice_id: str | None, stop_event: threading.Event) -> None:
        temp_file_path: str | None = None
        try:
            temp_file_path = asyncio.run(self._synthesize_to_wav_file(text, selected_voice_id, stop_event))
            if stop_event.is_set() or not temp_file_path:
                if temp_file_path and os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except OSError:
                        pass
                return

            with self._lock:
                self._current_temp_file = temp_file_path

            import winsound
            winsound.PlaySound(temp_file_path, winsound.SND_ASYNC | winsound.SND_FILENAME)
        except Exception:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError:
                    pass
        finally:
            with self._lock:
                if threading.current_thread() is self._worker_thread:
                    self._worker_thread = None

    async def _synthesize_to_wav_file(
        self,
        text: str,
        selected_voice_id: str | None,
        stop_event: threading.Event,
    ) -> str | None:
        SpeechSynthesizer = _import_speech_namespace()
        DataReader = _import_stream_namespaces()

        all_voices = [
            voice
            for voice in SpeechSynthesizer.all_voices
            if str(getattr(voice, "language", "") or "").lower().startswith("ja")
        ]
        if not all_voices:
            return None

        selected_voice = None
        if selected_voice_id:
            for voice in all_voices:
                voice_id = str(getattr(voice, "id", "") or "").strip()
                if voice_id == selected_voice_id:
                    selected_voice = voice
                    break

        if selected_voice is None:
            selected_voice = all_voices[0]

        synthesizer = SpeechSynthesizer()
        synthesizer.voice = selected_voice

        stream = await synthesizer.synthesize_text_to_stream_async(text)
        if stop_event.is_set():
            return None

        size = int(getattr(stream, "size", 0) or 0)
        if size <= 0:
            return None

        input_stream = stream.get_input_stream_at(0)
        reader = DataReader(input_stream)
        loaded = await reader.load_async(size)
        loaded_size = int(loaded)
        if loaded_size <= 0:
            return None

        audio_bytes = bytearray(loaded_size)
        reader.read_bytes(audio_bytes)

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        temp_file.write(audio_bytes)
        temp_file.flush()
        temp_file.close()
        return temp_file.name

    def _cleanup_temp_file(self) -> None:
        temp_file = None
        with self._lock:
            temp_file = self._current_temp_file
            self._current_temp_file = None

        if not temp_file:
            return

        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except OSError:
                pass
