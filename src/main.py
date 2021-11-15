import datetime
import logging
import multiprocessing
import time
from iqoptionapi.stable_api import IQ_Option

from src.config import Config
from src.signals import Signals
from src.telegram_bot import read_sinaisconsistente_channel

logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(message)s')
error_password = """{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""
config = Config.load_config()
user = config["email"]
password = config["password"]
session = IQ_Option(user, password)
totalEarnings = 0
ids = []
stopwin = None


def buy(self, moneyForOperations):
    options = config["options"]
    if options == "BINARY":
        return session.buy(float(moneyForOperations), self["parity"], self["action"], int(self["timeframe"]))
    else:
        return session.buy_digital_spot(self["parity"], float(moneyForOperations), self["action"],
                                        int(self["timeframe"]))


def check_win(id):
    options = config["options"]
    if options == "BINARY":
        print("\nAguardando resultado (BINARY) ->", id)
        return session.check_win_v4(id)
    else:
        print("\nAguardando resultado (DIGITAL) ->", id)
        while True:
            check, win = session.check_win_digital_v2(id)
            if check:
                return check, win


def new_operation(self, session):
    totalMoney = session.get_balance()
    global totalEarnings
    global totalEarnings
    moneyForOperations = round(totalMoney * int(config["operatingpercentage"]) / 100, 2)
    trend = get_trend(session, self["parity"], int(self["timeframe"]))
    if moneyForOperations < 2:
        moneyForOperations = 2
    # if not trend == self["action"]:
    #    print("(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ") (", config["options"], ") ",
    #          self["parity"],
    #         " = Entrada em ",
    #          self["action"],
    #          " cancelada, contra a tendencia | valor: ", str(moneyForOperations), " | timeframe ",
    #          str(self["timeframe"]),
    #          "M", "\n", end="", sep="")
    else:
        # ALL_Asset = session.get_all_open_time()
        # for type_name, data in ALL_Asset.items():
        #    for Asset, value in data.items():
        #        print(type_name, Asset, value["open"])
        #
        # print(float(moneyForOperations), self["parity"], self["action"], int(self["timeframe"]))
        check, id = buy(self, moneyForOperations)
        if check:
            print("(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ") (", config["options"].upper(),
                  ") ",
                  self["parity"],
                  " = Entrada em ",
                  self["action"],
                  " efetuada com sucesso | valor: ", str(moneyForOperations), " | timeframe ", str(self["timeframe"]),
                  "M | id: ",
                  id, end="", sep="")
            result, gain = check_win(id)
            if gain < 0 and int(self["martingale"]) > 0:
                currentgale = 0
                while currentgale < int(config["galemax"]):
                    moneyForOperations *= float(config["galefactor"])
                    print("(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ") (",
                          config["options"], ")",
                          " Resultado: ", gain,
                          " | operando em gale (", currentgale + 1, "/", config["galemax"],
                          ") | valor da nova operação: ", round(moneyForOperations, 2), end="", sep="")
                    check, id = buy(self, moneyForOperations)
                    result, gain = check_win(id)
                    print("(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ")",
                          " Resultado da operação = ", round(gain, 2), end="", sep="")
                    totalEarnings += gain
                    print("\nLucro atual:", round(totalEarnings, 2))
                    currentgale += 1
                    if gain > 0:
                        break
            else:
                print("(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ")",
                      " Resultado da operação = ", round(gain, 2), end="", sep="")
                totalEarnings += gain
                print("\nLucro atual:", round(totalEarnings, 2))
        else:
            print("(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ") (", config["options"], ") ",
                  self["parity"],
                  " = Entrada em ",
                  self["action"],
                  " cancelada, mercado fechado =( | valor: ", str(moneyForOperations), " | timeframe ",
                  str(self["timeframe"]),
                  "M", "\n", end="", sep="")


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
                    print("------------------------------------------------")
                    print("")
    return openParitys


def start():
    global stopwin
    header = {"User-Agent": r"Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0"}
    session.set_session(header, {})
    checkConnection, reason = session.connect()
    if checkConnection:
        multiprocessing.Process(target=read_sinaisconsistente_channel).start()
        totalEarningsToClose = round(session.get_balance() * int(config["maxwin"]) / 100, 2)
        totalEarnings = 0
        print("O total de ganhos para concluir as operações hoje é de", totalEarningsToClose)
        session.change_balance(config["mode"])
        print("Conexão feita com sucesso. Iniciando operações.")
        print("Aguardando sinais...\n")
        # Serve para fazer com que o minuto atual só chega buscado na lista de sinais uma vez!
        checkInCurrentMin = False
        curMin = 0
        while True:
            if stopwin is datetime:
                if stopwin.day == datetime.datetime.now().day:

                    return
                else:
                    print("Limpando stopwin")
                    totalEarningsToClose = round(session.get_balance() * int(config["maxwin"]) / 100, 2)
                    totalEarnings = 0
                    stopwin = None
            try:
                if not session.check_connect():
                    checkConnection, reason = session.connect()
                    print("Conexão com iq option perdida...")
                    if checkConnection:
                        print("Robo reconectado com sucesso!")
                    else:
                        print("robo não conectado. ->", reason)
                now = datetime.datetime.now() + datetime.timedelta(seconds=int(config["delay"]))
                # print("now",now, " delay ",int(config["delay"]))

                if not checkInCurrentMin:
                    curMin = now.minute
                    for sign in Signals.load():
                        signDateTime = sign["datetime"]
                        # print(signDateTime)
                        if (now.year == signDateTime.year
                                and now.month == signDateTime.month
                                and now.day == signDateTime.day
                                and now.hour == signDateTime.hour
                                and now.minute == signDateTime.minute):
                            new_operation(sign, session)
                            print("------------------------------------------------")
                        ##print("----")
                    checkInCurrentMin = True
                elif curMin != now.minute:
                    checkInCurrentMin = False
            except Exception as e:
                print("Ocorreu uma falha ao se conectar ->", e)
                time.sleep(5)
            if totalEarnings >= totalEarningsToClose:
                print("\nLucro de ", round(totalEarnings, 2), "/", round(totalEarningsToClose, 2),
                      " finalizando operações por hoje.", sep="")
                stopwin = datetime.datetime.now()
    else:
        if reason == "[Errno -2] Name or service not known":
            print("Sem internet...")
        elif reason == error_password:
            print("Senha incorreta...")
        else:
            print("aqui")
            print("Falha ao tentar conectar. ->", reason)


def main():
    start()


if __name__ == '__main__':
    main()
