import json
from pathlib import Path

from .constants import DEFAULT_EXCEPTIONS, EXCEPTIONS_FILE, VOWELS


def _exceptions_path() -> Path:
    return Path(__file__).resolve().parents[1] / EXCEPTIONS_FILE


def load_exceptions() -> dict[str, str]:
    path = _exceptions_path()
    if not path.exists():
        return DEFAULT_EXCEPTIONS.copy()

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return DEFAULT_EXCEPTIONS.copy()

        merged = DEFAULT_EXCEPTIONS.copy()
        for key, value in data.items():
            if isinstance(key, str) and isinstance(value, str):
                merged[key.lower()] = value.lower()
        return merged
    except Exception:
        return DEFAULT_EXCEPTIONS.copy()


EXCEPTIONS = load_exceptions()


def is_vowel(ch: str) -> bool:
    return ch in VOWELS


def normalize_spanish_word(word: str) -> str:
    return word.lower()


def should_keep_word(word: str) -> bool:
    lower = word.lower()
    if any(ch.isdigit() for ch in lower):
        return True

    vowels = sum(1 for ch in lower if is_vowel(ch))
    return vowels == 0


def join_phonetic_parts(parts: list[str]) -> str:
    result = "".join(parts)
    replacements = {
        "hhh": "hh",
        "yyy": "yy",
        "oooo": "ooo",
        "eeee": "eee",
    }
    for old, new in replacements.items():
        result = result.replace(old, new)
    return result


def spanish_to_phonetic_word(word: str) -> str:
    original = normalize_spanish_word(word)

    if original in EXCEPTIONS:
        return EXCEPTIONS[original]

    if should_keep_word(original):
        return original

    chars = list(original)
    parts: list[str] = []
    i = 0
    length = len(chars)

    while i < length:
        ch = chars[i]
        nxt = chars[i + 1] if i + 1 < length else ""
        nxt2 = chars[i + 2] if i + 2 < length else ""

        if ch == "c" and nxt == "h":
            parts.append("ch")
            i += 2
            continue

        if ch == "l" and nxt == "l":
            parts.append("y")
            i += 2
            continue

        if ch == "r" and nxt == "r":
            parts.append("r")
            i += 2
            continue

        if ch == "q" and nxt == "u":
            if nxt2 in "eiéí":
                parts.append("k")
                i += 2
                continue
            parts.append("k")
            i += 1
            continue

        if ch == "g" and nxt == "u" and nxt2 in "eéií":
            parts.append("g")
            i += 2
            continue

        if ch == "g" and nxt == "ü" and nxt2 in "eéií":
            parts.append("gw")
            i += 2
            continue

        if ch in "aá":
            parts.append("ah")
            i += 1
            continue
        if ch in "eé":
            parts.append("eh")
            i += 1
            continue
        if ch in "ií":
            parts.append("ee")
            i += 1
            continue
        if ch in "oó":
            parts.append("oh")
            i += 1
            continue
        if ch in "uúü":
            parts.append("oo")
            i += 1
            continue

        if ch in ("b", "v"):
            parts.append("b")
            i += 1
            continue

        if ch == "c":
            if nxt in "eéií":
                parts.append("s")
            else:
                parts.append("k")
            i += 1
            continue

        if ch == "d":
            parts.append("d")
            i += 1
            continue

        if ch == "f":
            parts.append("f")
            i += 1
            continue

        if ch == "g":
            if nxt in "eéií":
                parts.append("h")
            else:
                parts.append("g")
            i += 1
            continue

        if ch == "h":
            i += 1
            continue

        if ch == "j":
            parts.append("h")
            i += 1
            continue

        if ch == "k":
            parts.append("k")
            i += 1
            continue

        if ch == "l":
            parts.append("l")
            i += 1
            continue

        if ch == "m":
            parts.append("m")
            i += 1
            continue

        if ch == "n":
            parts.append("n")
            i += 1
            continue

        if ch == "ñ":
            parts.append("ny")
            i += 1
            continue

        if ch == "p":
            parts.append("p")
            i += 1
            continue

        if ch == "r":
            parts.append("r")
            i += 1
            continue

        if ch == "s":
            parts.append("s")
            i += 1
            continue

        if ch == "t":
            parts.append("t")
            i += 1
            continue

        if ch == "w":
            parts.append("w")
            i += 1
            continue

        if ch == "x":
            parts.append("ks")
            i += 1
            continue

        if ch == "y":
            if i == length - 1:
                parts.append("ee")
            else:
                parts.append("y")
            i += 1
            continue

        if ch == "z":
            parts.append("s")
            i += 1
            continue

        parts.append(ch)
        i += 1

    return join_phonetic_parts(parts)
