# utils/idle_manager.py
import asyncio
import contextlib
from typing import Awaitable, Callable, Optional

class IdleManager:
    def __init__(self, idle_seconds: int, on_idle: Callable[[], Awaitable[None]]):
        self.idle_seconds = idle_seconds
        self.on_idle = on_idle
        self._task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()

    async def _runner(self):
        try:
            await asyncio.sleep(self.idle_seconds)
            await self.on_idle()
        finally:
            # после срабатывания таймер очищается
            self._task = None

    async def ping(self):
        """Сбросить таймер и начать отсчёт заново."""
        async with self._lock:
            if self._task and not self._task.done():
                self._task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._task
            self._task = asyncio.create_task(self._runner())

    async def stop(self):
        async with self._lock:
            if self._task and not self._task.done():
                self._task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await self._task
            self._task = None
