from openai import OpenAI
import os
from dotenv import load_dotenv
import re
from utils.Db import Db
from utils.Google_sheets import SheetsChatLogger
from datetime import datetime, timedelta, date



def prepare_datetimes(data: list):
    result = []
    for d, t in data:
        # t — это timedelta, достаём часы, минуты, секунды
        total_seconds = int(t.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        dt = datetime(d.year, d.month, d.day, hours, minutes, seconds)
        result.append(dt)
    return result



class Upload_chats():

    def __init__(self):
        load_dotenv()
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_REQUEST_MODEL") or "gpt-4o-mini"
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        return
    
    def upload(self):

        
        shet = SheetsChatLogger()
        db = Db()
        sids = db.get_sessions_0()
        for i in sids:
            try:
                chat_text = db.get_dialogue(i)
                time = prepare_datetimes(db.get_session(i))
                name, phone = self.ai_analysis(chat_text).split(",")
                shet.add_record(name, phone, chat_text, time[0])
                db.update_upload(i)

            except:
                pass
    
    
    def ai_analysis(self, text: str):

        prompt = (
        "Ты экстрактор. Твоя задача — найти в диалоге ФИО клиента и номер телефона и вернуть ИСКЛЮЧИТЕЛЬНО строку формата:\n"
        "<Фамилия Имя Отчество>,<Номер телефона>\n"
        "Если ФИО неизвестно — напиши ОТСУТСТВУЕТ вместо ФИО.\n"
        "Если телефон неизвестен — напиши ОТСУТСТВУЕТ вместо номера.\n"
        "\n"
        "Правила извлечения телефона:\n"
        "1) Телефон может быть записан как угодно (пробелы, скобки, дефисы, точки, слово 'тел', 'whatsapp', '+7', '8' и т.п.).\n"
        "2) Нормализуй: удали все, кроме цифр и ведущего плюса. Затем:\n"
        "   - Если есть ведущий '+<код_страны>' — оставь так, но без пробелов/скобок (пример: '+7 (999) 123-45-67' -> '+79991234567').\n"
        "   - Если номер начинается с '8' и в сумме 11 цифр для России — замени первую цифру на '+7' (например '8 999 123-45-67' -> '+79991234567').\n"
        "   - Если номер начинается с '7' и 11 цифр — добавь '+' перед 7 (например '79991234567' -> '+79991234567').\n"
        "   - Если ровно 10 цифр без кода страны (часто мобильный РФ) — добавь '+7' в начало (например '9991234567' -> '+79991234567').\n"
        "3) Игнорируй последовательности цифр, которые похожи на даты (форматы с точками/дефисами и 6–8 цифр), суммы денег, счета, ИНН/ОГРН, номера карт (16 цифр), коды подтверждения (4–6 цифр).\n"
        "4) Если найдено несколько номеров — выбери наиболее вероятный телефон: ближайший к словам 'тел', 'номер', 'whatsapp', или первый по порядку.\n"
        "\n"
        "Правила извлечения ФИО:\n"
        "1) Предпочитай кириллицу. Возможны форматы: 'Фамилия Имя Отчество', 'Фамилия Имя', просто 'Имя'.\n"
        "2) Если отчество отсутствует — верни то, что есть (например: 'Иванов Иван'). Если вообще нет ФИО — 'ОТСУТСТВУЕТ'.\n"
        "3) Не путай ФИО с названием компании/никами/логинами/email.\n"
        "\n"
        "Формат ответа строго один: '<ФИО>,<телефон>' без пробелов вокруг запятой. Никаких пояснений.\n"
        "\n"
        "Примеры:\n"
        "Диалог: 'Здравствуйте, я Иванов Иван Иванович. Тел: 8 (999) 123-45-67'\n"
        "Ответ: Иванов Иван Иванович,+79991234567\n"
        "\n"
        "Диалог: 'Пишите в WhatsApp +7 916 000 11 22, меня зовут Пётр'\n"
        "Ответ: Пётр,+79160001122\n"
        "\n"
        "Диалог: 'Меня Анна Смирнова, свяжитесь по 999-555-44-33'\n"
        "Ответ: Смирнова Анна,+79995554433\n"
        "\n"
        "Диалог: 'Добрый день. Когда приедете? Мой ИНН 7701234567, карта 5469 12** **** 1234'\n"
        "Ответ: ОТСУТСТВУЕТ,ОТСУТСТВУЕТ\n"
        "\n"
        f"Диалог клиента и консультанта:\n{text}\n"
                                                                                                            )

        resp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Отвечай только целевой строкой '<ФИО>,<телефон>' без пояснений."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=40,
        )
        return resp.choices[0].message.content.strip()
