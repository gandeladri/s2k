import re

EXCEPTIONS_FILE = "spanish_phonetizer_exceptions.json"

BASE_URL = "https://www.sljfaq.org/cgi/e2k.cgi"
LANG = "en"
TIMEOUT = 20
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"

WORD_RE = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+|[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")
API_TOKEN_RE = re.compile(r"[a-z]+|[^a-z]+")
VOWELS = "aeiouáéíóúü"

DEFAULT_EXCEPTIONS = {
    "uruguay": "ooroogooy",
    "montevideo": "montebeedeyo",
    "buenos": "bwenos",
    "aires": "aires",
    "youtube": "yootoob",
    "wifi": "waifai",
    "whatsapp": "guatsap",
    "ok": "ok",
}
