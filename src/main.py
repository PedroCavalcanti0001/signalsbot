import asyncio
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor

from src.signals_core import start_signals_core
from src.telegram_bot import start_telegram_bot


async def main():
    executor = ThreadPoolExecutor(max_workers=2)
    executor.submit(start_telegram_bot())
    executor.submit(start_signals_core())


asyncio.run(main())
