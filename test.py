import multiprocessing

from src.telegram_bot import read_signalsfree_channel

multiprocessing.Process(target=read_signalsfree_channel, args=(3333,)).start()