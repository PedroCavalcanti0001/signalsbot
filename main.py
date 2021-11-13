from iqoptionapi.stable_api import IQ_Option
import datetime
import time
import logging
import iqoptionapi.global_value as gki

logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(message)s')
config = {}
error_password = """{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""


def get_signals():
    signals = []
    with open('signals.txt', encoding='utf8') as signalsFile:
        lines = signalsFile.readlines()
        for line in lines:
            if not line.startswith("#") and line:
                split1 = line.split(',')
                parity = split1[0]
                dateTimeStr = split1[1]
                dateTimeSplit = dateTimeStr.split(":")
                dt = datetime.datetime(int(dateTimeSplit[2].strip()), int(dateTimeSplit[1].strip()),
                                       int(dateTimeSplit[0].strip()),
                                       int(dateTimeSplit[3].strip()), int(dateTimeSplit[4].strip()))
                timeframe = split1[2]
                gale = split1[3]
                tipo = split1[4]
                signals.append({
                    "parity": parity.strip().upper(),
                    "datetime": dt,
                    "timeframe": timeframe.strip(),
                    "martingale": gale.strip(),
                    "action": tipo.strip().upper()
                })
    return signals


def get_config():
    with open('config.txt', encoding='utf8') as configFile:
        allLines = configFile.readlines()
        for line in allLines:
            split = line.split(":")
            if line.__contains__("email"):
                config["email"] = split[1].strip()
            elif line.__contains__("password"):
                config["password"] = split[1].strip()
            elif line.__contains__("maxwin"):
                config["maxwin"] = split[1].strip()
            elif line.__contains__("operatingpercentage"):
                config["operatingpercentage"] = split[1].strip()
            elif line.__contains__("mode"):
                config["mode"] = split[1].strip()
            elif line.__contains__("galefactor"):
                config["galefactor"] = split[1].strip()


get_config()
user = config["email"]
password = config["password"]
session = IQ_Option(user, password)
totalEarnings = 0
ids = []


def new_operation(self, session):
    totalMoney = session.get_balance()
    global totalEarnings
    moneyForOperations = round(totalMoney * int(config["operatingpercentage"]) / 100, 2)
    if moneyForOperations < 2:
        moneyForOperations = 2

    trend = get_trend(session, self["parity"], int(self["timeframe"]))
    print("TENDENCIA:", trend)
    # if not trend == self["action"]:
    if not 1 == 1:
        print("Operação cancelada. Contra a tendencia :(")
    else:
        ALL_Asset = session.get_all_open_time()
        for type_name, data in ALL_Asset.items():
            for Asset, value in data.items():
                print(type_name, Asset, value["open"])
        print("----------------")


        print("---------")
        print(float(moneyForOperations), self["parity"], self["action"], int(self["timeframe"]))
        check, id = session.buy(float(moneyForOperations), self["parity"], self["action"], int(self["timeframe"]))
        if check:
            print(self["parity"], "= Entrada em", self["action"], "efetuada com sucesso, valor:", moneyForOperations, "id:", id)
            result, gain = session.check_win_v4(id)
            if gain < 0 and int(self["martingale"]) > 0:
                moneyForOperations *= float(config["galefactor"])
                print("Resultado:", gain, "| operando em gale | valor da nova operação:", round(moneyForOperations, 2))
                check, id = session.buy(moneyForOperations, self["parity"], self["action"], int(self["timeframe"]))
                result, gain = session.check_win_v4(id)
                print("RESULTADO DA OPERAÇÃO", float(moneyForOperations), "-", self["parity"], "-", self[
                    "action"], "-", self["timeframe"], "=", round(gain, 2))
                totalEarnings += gain
                print("TOTAL DE GANHOS:", round(totalEarnings, 2))
            else:
                print("RESULTADO DA OPERAÇÃO", 100.0, "-", self["parity"], "-", self[
                    "action"], "-", self["timeframe"], "=", round(gain, 2))
                totalEarnings += gain
                print("TOTAL DE GANHOS:", round(totalEarnings, 2))
        else:
            print("Entrada não efetuada, mercado fechado. ->", id)


def get_trend(self, parity, timeframe):
    velas = self.get_candles(parity, (int(timeframe) * 60), 20, time.time())
    ultimo = round(velas[0]['close'], 4)
    primeiro = round(velas[-1]['close'], 4)
    diferenca = abs(round(((ultimo - primeiro) / primeiro) * 100, 3))
    trend = "CALL" if ultimo < primeiro and diferenca > 0.01 else "PUT" if ultimo > primeiro and diferenca > 0.01 else False
    return trend


def get_trend_v2():
    pass


def getAllOpened(self, find_type_name):
    openParitys = []
    ALL_Asset = session.get_all_open_time()

    for type_name, data in ALL_Asset.items():
        if type_name == find_type_name:
            for Asset, value in data.items():
                print(value)
                if bool(value["open"]):
                    print(type_name)
                    print(type_name, Asset, value["open"])
                    openParitys.__add__(Asset)
                    print("================")
    return openParitys


def start():
    header = {"User-Agent": r"Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0"}
    session.set_session(header, {})
    checkConnection, reason = session.connect()
    if checkConnection:

        totalEarningsToClose = round(session.get_balance() * int(config["maxwin"]) / 100, 2)
        totalEarnings = 0
        print("O total de ganhos para concluir as operações hoje é de", totalEarningsToClose)
        session.change_balance(config["mode"])
        print("Conexão feita com sucesso. Iniciando operações.")
        time.sleep(2)
        print("Aguardando sinais...\n\n")
        # Serve para fazer com que o minuto atual só chega buscado na lista de sinais uma vez!
        checkInCurrentMin = False
        curMin = 0
        while True:
            try:
                if not session.check_connect():
                    checkConnection, reason = session.connect()
                    print("Conexão com iq option perdida...")
                    if checkConnection:
                        print("Robo reconectado com sucesso!")
                    else:
                        print("robo não conectado. ->", reason)

                now = datetime.datetime.now()

                if not checkInCurrentMin:
                    curMin = now.minute
                    for sign in get_signals():
                        signDateTime = sign["datetime"]
                        if (now.year == signDateTime.year
                                and now.month == signDateTime.month
                                and now.day == signDateTime.day
                                and now.hour == signDateTime.hour
                                and now.minute == signDateTime.minute):
                            new_operation(sign, session)
                            print("==========")

                    checkInCurrentMin = True
                elif curMin != now.minute:
                    checkInCurrentMin = False
            except Exception as e:
                print("Ocorreu uma falha ao se conectar ->", e)
                time.sleep(5)
    else:
        if reason == "[Errno -2] Name or service not known":
            print("Sem internet...")
        elif reason == error_password:
            print("Senha incorreta...")
        else:
            print("Falha ao tentar conectar. ->", reason)


start()
