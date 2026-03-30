import re

from .constants import WORD_RE
from .phonetics import spanish_to_phonetic_word


def convert_text(text: str) -> str:
    tokens = WORD_RE.findall(text)
    converted: list[str] = []

    for token in tokens:
        if re.fullmatch(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", token):
            converted.append(spanish_to_phonetic_word(token))
        else:
            converted.append(token)

    return "".join(converted).lower()
