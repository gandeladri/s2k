import requests

from .constants import API_TOKEN_RE, BASE_URL, LANG, TIMEOUT, USER_AGENT


class KatakanaClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.session.headers.update({
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.9,es;q=0.8",
            "referer": "https://www.sljfaq.org/cgi/e2k.cgi",
            "sec-ch-ua": '"Chromium";v="146", "Not-A.Brand";v="24", "Google Chrome";v="146"',
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": USER_AGENT,
        })
        self.initialized = False
        self.cache: dict[str, str] = {}

    def init_session(self) -> None:
        if self.initialized:
            return
        response = self.session.get(BASE_URL, timeout=TIMEOUT)
        response.raise_for_status()
        self.initialized = True

    def english_word_to_katakana(self, word: str) -> str:
        normalized = word.strip().lower()
        if not normalized:
            return normalized

        cached = self.cache.get(normalized)
        if cached is not None:
            return cached

        self.init_session()
        response = self.session.get(
            BASE_URL,
            params={"o": "json", "word": normalized, "lang": LANG},
            timeout=TIMEOUT,
        )
        response.raise_for_status()

        data = response.json()

        if data.get("check_captcha"):
            raise RuntimeError("captcha requerido por la api")

        if data.get("error_msg"):
            raise RuntimeError(str(data.get("error_msg")))

        words = data.get("words") or []
        parts: list[str] = []
        for item in words:
            value = item.get("j_pron_spell") or item.get("j_pron_only")
            if value:
                parts.append(value.strip())

        result = " ".join(part for part in parts if part).strip()
        if not result:
            result = normalized

        self.cache[normalized] = result
        return result

    def english_text_to_katakana(self, text: str) -> str:
        tokens = API_TOKEN_RE.findall(text.lower())
        converted: list[str] = []

        for token in tokens:
            if token.isalpha() and token.isascii() and token.islower():
                converted.append(self.english_word_to_katakana(token))
            else:
                converted.append(token)

        return "".join(converted)
