import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from zoneinfo import ZoneInfo

class Db():

    def __init__(self):
        MSK = ZoneInfo("Europe/Moscow")
        load_dotenv()
        self.db_user=os.getenv("db_user")
        self.db_host=os.getenv("db_host")
        self.db_port=os.getenv("db_port")
        self.db_password=os.getenv("db_password")
        self.db_name =os.getenv("db_name")

    def connect(self):
        try:
            conn = mysql.connector.connect(
                host=self.db_host,
                port=int(self.db_port),
                user=self.db_user,
                password=self.db_password,
                database=self.db_name
            )
            return conn
        except Error as e:
            print(e)
            return None
        
    def search_session(self, sid: str) -> bool:
        conn = self.connect()
        sql = "SELECT COUNT(*) AS cnt FROM sessions WHERE sid = %s"
        cursor = conn.cursor()
        cursor.execute(sql, (sid,))
        search = cursor.fetchone()
        cursor.close()
        conn.close()
        return bool(search[0]) if search else False
    
    def get_session(self, sid: str) -> list:
        conn = self.connect()
        sql = "SELECT date, time FROM sessions WHERE sid = %s"
        cursor = conn.cursor()
        cursor.execute(sql, (sid,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        result = []
        for i in rows:
            result.append(i)
        return result
    
    def add_session(self, sid: str, nomber=None):
        conn = self.connect()
        nomber = nomber if nomber is not None else ""
        date = self.get_date()
        time = self.get_time()
        sql = "INSERT INTO sessions (sid, date, time, nomber) VALUES (%s, %s, %s, %s)"
        cursor = conn.cursor()
        cursor.execute(sql, (sid, date, time, nomber))
        conn.commit()
        cursor.close()
        conn.close()

    def update_nomber(self, sid: str, nomber: str) -> bool:
        conn = self.connect()
        sql = "UPDATE sessions SET nomber = %s WHERE sid = %s"
        cursor = conn.cursor()
        cursor.execute(sql, (nomber, sid))
        conn.commit()
        updated = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return updated

    def get_date(self) -> str:
        return datetime.utcnow().date().isoformat()

    def get_time(self) -> str:
        return datetime.utcnow().strftime("%H:%M:%S")

    def add_message(self, sid: str, user_message: str, ai_message: str):
        conn = self.connect()
        sql = "INSERT INTO messages (sid, user_message, ai_message) VALUES (%s, %s, %s)"
        cursor = conn.cursor()
        cursor.execute(sql, (sid, user_message, ai_message))
        conn.commit()
        cursor.close()
        conn.close()

    def get_messages(self, sid: str):
        conn = self.connect()
        sql = "SELECT sid, user_message, ai_message FROM messages WHERE sid = %s"
        cursor = conn.cursor()
        cursor.execute(sql, (sid,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def get_dialogue(self, sid: str) -> str:
        conn = self.connect()
        sql = "SELECT user_message, ai_message FROM messages WHERE sid = %s ORDER BY id ASC"
        cursor = conn.cursor()
        cursor.execute(sql, (sid,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        result = []
        for i, (user_msg, ai_msg) in enumerate(rows, start=1):
            result.append(f"{i}. -{user_msg}\n-{ai_msg}")
        return "\n".join(result)
    
    def get_sessions_0(self) -> list:
        conn = self.connect()
        sql = "SELECT sid FROM sessions WHERE upload = %s"
        cursor = conn.cursor()
        cursor.execute(sql, (0,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        result = []
        for i in rows:
            result.append(i[0])
        return result


    def update_upload(self, sid: str) -> bool:
        conn = self.connect()
        sql = "UPDATE sessions SET upload = %s WHERE sid = %s"
        cursor = conn.cursor()
        cursor.execute(sql, (1, sid))
        conn.commit()
        updated = cursor.rowcount > 0
        cursor.close()
        conn.close()
        return updated
    

if __name__ == "__main__":
    Db = Db()
    print(Db.get_session('6611207d-9809-47e7-9d36-6303db751402'))