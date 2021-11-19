import asyncio
import multiprocessing
import re
import threading
from datetime import timedelta, datetime
from pathlib import Path

from colorama import Fore
from telethon import TelegramClient
from telethon import events

loop = asyncio.get_event_loop()
api_id = 17800567
api_hash = 'e801e094f0aa1edce04c1ab22565bbb0'
client = TelegramClient('Miro', api_id, api_hash, sequential_updates=False)


# Retorna sim se o tempo atual for maior que o tempo passado
def get_datetime(self):
    now = datetime.now()
    nowTime = str(now.time())[0:5]
    nowSplit = nowTime.split(":")
    compareSplit = self.split(":")
    if ((int(nowSplit[0])) > int(compareSplit[0]) or (
            int(nowSplit[0]) == int(compareSplit[0]) and int(nowSplit[1]) >= int(compareSplit[1]))):
        now = now + timedelta(days=1)
    return now.replace(hour=int(compareSplit[0]), minute=int(compareSplit[1]))


def parse_sinaisconsitente_(self):
    lines = []
    if str(self[0].strip().lower()).startswith("Sinais convertidos START BOT".lower()):
        operations = list(filter(lambda x: x.__contains__("PUT") or x.__contains__("CALL"), self))
        for operation in operations:
            split = operation.split(";")
            parity = split[0]
            time = split[2]
            action = split[3]
            timeframe = split[4].strip()
            datetime = get_datetime(time)

            formmated = parity + "," + datetime.strftime("%d:%m:%Y:%I:%M") + "," + str(
                timeframe) + ",2," + action
            lines.append(formmated)
    return lines


async def read_sinaisconsistente_channel():
    # -1001471304586
    # -747797582
    base_path = Path(__file__).parent
    file_path = (base_path / "../resources/signals.txt").resolve()

    print(Fore.GREEN + "* Iniciando catalogador de sinais ‘sinais consistente’ - telegram bot." + Fore.RESET)

    channel = await client.get_entity(-747797582)
    print(channel)

    @client.on(events.NewMessage(chats=channel, incoming=False))
    async def callback(event):
        message = event.message
        lines = message.message.splitlines()
        newLines = parse_sinaisconsitente_(lines)
        if len(newLines) > 0:
            readfile = open(file_path, encoding='utf8')
            writefile = open(file_path, 'a+')
            writefile.truncate(0)
            readlines = readfile.readlines()
            print("O total de ", len(newLines), " sinais foram capturados.", sep="")
            newLines.insert(0, "#SINAIS CAPTURADOS DO TELEGRAM 'SINAIS CONSISTENTE FREE'!")
            for line in newLines:
                if not readlines.__contains__(line):
                    writefile.seek(0)
                    writefile.write(line + '\n')
            readfile.close()
            writefile.close()
    await client.start()
    await client.run_until_disconnected()




def parse_tigersfree_signals(self):
    lines = []
    if str(self[0].strip().lower()).startswith("Sinais Free".lower()):
        operations = list(filter(lambda x: x.__contains__("PUT") or x.__contains__("CALL"), self))
        for operation in operations:
            split = operation.split(" ")
            parity = split[0]
            time = split[1]
            action = split[2]
            timeframe = next(filter(lambda x: x.startswith('Sinais M'), self), None)

            if timeframe is None:
                timeframe = 5
            else:
                timeframe = int(re.search(r'[0-9]', timeframe).group())

            datetime = get_datetime(time)

            formmated = parity + "," + datetime.strftime("%d:%m:%Y:%I:%M") + "," + str(
                timeframe) + ",1," + action
            lines.append(formmated)

    return lines


async def read_signalsfree_channel():
    base_path = Path(__file__).parent
    file_path = (base_path / "../resources/signals.txt").resolve()
    api_id = 17800567
    api_hash = 'e801e094f0aa1edce04c1ab22565bbb0'
    # -1001188178371
    client = TelegramClient('Miro', api_id, api_hash, sequential_updates=False)
    channel2 = await client.get_input_entity(-747797582)
    print("Iniciando Telegram - bot")

    @client.on(events.NewMessage(chats=channel2, incoming=False))
    async def callback(event):
        message = event.original_update.message.message
        lines = message.splitlines()
        newLines = parse_tigersfree_signals(lines)
        if len(newLines) > 0:
            print("aqui")
            readfile = open(file_path, encoding='utf8')
            writefile = open(file_path, 'a+')
            readlines = readfile.readlines()
            newLines.insert(0, "#SINAIS CAPTURADOS DO TELEGRAM 'Tigers Sinais Free'!")
            for line in newLines:
                if not readlines.__contains__(line):
                    writefile.seek(0)
                    writefile.write(line + '\n')
            readfile.close()
            writefile.close()

    client.start()
    client.run_until_disconnected()


async def main():
    await read_sinaisconsistente_channel()

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())