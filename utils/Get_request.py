from openai import OpenAI
import os
import re
from dotenv import load_dotenv


class GetRequest:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        self.model = os.getenv("OPENAI_REQUEST_MODEL") or "gpt-4o-mini"
        self.client = OpenAI(api_key=api_key)

    def _sanitize(self, s: str) -> str:
        s = (s or "").strip().lower()
        s = s.strip('«»"\'` \t')
        s = re.sub(r"[^\wа-яё\- ]+", " ", s, flags=re.IGNORECASE)
        s = re.sub(r"\s+", " ", s).strip()
        parts = s.split()
        if len(parts) > 3:
            s = " ".join(parts[:3])
        return s

    def request(self, text: str) -> str:
        prompt = (
            "Сформулируй ключевую фразу (1-3 слова) для поиска в БД QDRANT.\n"
            "Только нижний регистр, без кавычек и знаков препинания, без предлогов.\n"
            f"Текст: {text}"
        )
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Отвечай только целевой фразой (1-3 слова), без пояснений."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=12,
        )
        return self._sanitize(resp.choices[0].message.content)


