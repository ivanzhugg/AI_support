from datetime import datetime, timezone
from typing import Optional
import os

from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build


class SheetsChatLogger:
    def __init__(self):
        load_dotenv()
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.service_json_path = os.path.join(BASE_DIR, "..", "service-account.json")
        self.spreadsheet_id = os.getenv("SPREADSHEET_ID")
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]
        creds = Credentials.from_service_account_file(self.service_json_path, scopes=scopes)
        self.svc = build("sheets", "v4", credentials=creds)

    def _month_title(self, dt: datetime) -> str:
        ru = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
              "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        return f"{ru[dt.month - 1]} {dt.year}"

    def _get_sheet_id(self, title: str) -> Optional[int]:
        meta = self.svc.spreadsheets().get(spreadsheetId=self.spreadsheet_id).execute()
        for s in meta.get("sheets", []):
            if s["properties"]["title"] == title:
                return s["properties"]["sheetId"]
        return None

    def _ensure_sheet(self, title: str) -> int:
        sheet_id = self._get_sheet_id(title)
        if sheet_id is not None:
            return sheet_id
        reqs = [{
            "addSheet": {
                "properties": {
                    "title": title,
                    "gridProperties": {"rowCount": 1000, "columnCount": 5}
                }
            }
        }]
        self.svc.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id, body={"requests": reqs}
        ).execute()
        sheet_id = self._get_sheet_id(title)
        headers = [["Date", "Time", "Name", "phone", "chat"]]
        self.svc.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{title}!A1:E1",
            valueInputOption="RAW",
            body={"values": headers}
        ).execute()
        return sheet_id

    def _insert_top_row(self, sheet_id: int):
        reqs = [{
            "insertDimension": {
                "range": {
                    "sheetId": sheet_id,
                    "dimension": "ROWS",
                    "startIndex": 1,
                    "endIndex": 2
                },
                "inheritFromBefore": False
            }
        }]
        self.svc.spreadsheets().batchUpdate(
            spreadsheetId=self.spreadsheet_id, body={"requests": reqs}
        ).execute()

    def add_record(self, name: str, phone: str, chat: str, when: Optional[datetime] = None):
        if when is None:
            now = datetime.now(timezone.utc)
        else:
            if when.tzinfo is None:
                now = when.replace(tzinfo=timezone.utc)
            else:
                now = when.astimezone(timezone.utc)

        title = self._month_title(now)
        sheet_id = self._ensure_sheet(title)
        self._insert_top_row(sheet_id)
        self.svc.spreadsheets().values().update(
            spreadsheetId=self.spreadsheet_id,
            range=f"{title}!A2:E2",
            valueInputOption="RAW",
            body={"values": [[
                now.date().isoformat(),
                now.strftime("%H:%M:%S"),
                name,
                phone,
                chat
            ]]}
        ).execute()



def test_sheets_logger():
    logger = SheetsChatLogger()
    dt1 = datetime(2023, 9, 15, 14, 45)         # попадёт в "Сентябрь 2025"
    dt2 = datetime(2025, 10, 1, 9, 0)           # создаст "Октябрь 2025" и добавит туда
    logger.add_record("Иван", "+70000000000", "Первое тестовое сообщение", when=dt1)
    logger.add_record("Мария", "+71112223344", "Сообщение следующего месяца", when=dt2)


if __name__ == "__main__":
    test_sheets_logger()


