from multiprocessing import Process

from src.signals_core import start_signals_core
from src.telegram_bot import start_telegram_bot


def start():
    p1 = Process(target=start_signals_core, args=())
    p2 = Process(target=start_telegram_bot, args=())
    p1.start()
    p2.start()
    p1.join()
    p2.join()

if __name__ == '__main__':
    start()
