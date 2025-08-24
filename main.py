import logging
import time
from datetime import datetime
from typing import Optional

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from utils.Embedding import Embedding
from utils.Get_request import GetRequest
from utils.Kolya import Answerer
from utils.Qdrant import Qdrant
from utils.Db import Db
from utils.Upload_chats import Upload_chats
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent  # .../backend

# <<< NEW >>>
import asyncio
from utils.idle_manager import IdleManager

# ---- ЛОГИ ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

app = FastAPI(title="Echo API")

e = Embedding()
req = GetRequest()
ans = Answerer()
qd = Qdrant()
db = Db()
up = Upload_chats()

# <<< NEW >>> ваш скрипт, запускаемый после 5 минут простоя
def run_idle_script():
    logging.info("[IDLE] maintenance started")
    up.upload()
    logging.info("[IDLE] maintenance finished")

# <<< NEW >>> обёртка, чтобы не блокировать event loop
async def on_idle():
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, run_idle_script)

# <<< NEW >>> менеджер простоя: 300 сек = 5 минут
idle = IdleManager(idle_seconds=300, on_idle=on_idle)


# Раздача статики (папка backend/static)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.api_route("/chat.js", methods=["GET", "HEAD"])
def serve_chat_js():
    return FileResponse(
        BASE_DIR / "js" / "chat.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-store"},
    )
# CORS: для MVP разрешаем всё (можно сузить позже под свои домены)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=False,
)

# ---- МОДЕЛИ ----
class ReplyIn(BaseModel):
    sid: str = Field(..., min_length=8, max_length=128, description="Клиентский session id (UUID)")
    message: str = Field(..., min_length=1, max_length=4000, description="Текст пользователя")

class ReplyOut(BaseModel):
    sid: str
    reply: str
    echoed_at: str  # ISO UTC время ответа

# ---- ЭНДПОИНТЫ ----
@app.api_route("/health", methods=["GET", "HEAD"])
async def health():
    return {"ok": True}

# <<< NEW >>> на выключении аккуратно останавливаем таймер
@app.on_event("shutdown")
async def _shutdown():
    await idle.stop()

@app.post("/v1/reply", response_model=ReplyOut)
async def reply(payload: ReplyIn, request: Request):
    client_ip: Optional[str] = request.client.host if request.client else None

    # <<< NEW >>> ПИНГ здесь: любое действие откладывает запуск на 5 минут
    await idle.ping()

    logging.info("[RECV] ip=%s sid=%s message=%r", client_ip, payload.sid, payload.message)

    context = qd.search(e.get_vector(payload.message))
    answer = ans.get_message(payload.message, context, history=db.get_dialogue(payload.sid))

    if db.search_session(payload.sid):
        db.add_message(payload.sid, payload.message, answer)
    else:
        db.add_session(payload.sid)
        db.add_message(payload.sid, payload.message, answer)
    time.sleep(10)
    logging.info("[SEND] ip=%s sid=%s reply=%r", client_ip, payload.sid, answer)

    return ReplyOut(
        sid=payload.sid,
        reply=answer,
        echoed_at=datetime.utcnow().isoformat() + "Z",
    )
