import datetime
import logging
import time

from colorama import Fore
from iqoptionapi.stable_api import IQ_Option

from src.config import Config
from src.signals import Signals

logging.basicConfig(level=logging.ERROR, format='%(asctime)s %(message)s')
error_password = """{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""
config = Config.load_config()
user = config["email"]
password = config["password"]
session = IQ_Option(user, password)
totalEarnings = 0
ids = []
stopwin = None
totalEarningsToClose = 0
lastLoss = None


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
        print(Fore.YELLOW + "\nAguardando resultado (BINARY) ->", id)
        return session.check_win_v4(id)
    else:
        print(Fore.YELLOW + "\nAguardando resultado (DIGITAL) ->", id)
        while True:
            check, win = session.check_win_digital_v2(id)
            if check:
                return check, win


def new_operation(self, session):
    totalMoney = session.get_balance()
    global totalEarnings
    global lastLoss

    moneyForOperations = round(totalMoney * int(config["operatingpercentage"]) / 100, 2)
    # trend = get_trend(session, self["parity"], int(self["timeframe"]))
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
    # else:
    # ALL_Asset = session.get_all_open_time()
    # for type_name, data in ALL_Asset.items():
    #    for Asset, value in data.items():
    #        print(type_name, Asset, value["open"])
    #
    # print(float(moneyForOperations), self["parity"], self["action"], int(self["timeframe"]))
    check, id = buy(self, moneyForOperations)
    if check:
        if lastLoss is not None:
            lastLossWithFactor = lastLoss * float(config["doublefactor"])
            moneyForOperations += lastLossWithFactor
            print(Fore.YELLOW + "* Estrategia 'DOBRO OU NADA' sendo utilizada, o valor de " + str(
                round(lastLossWithFactor, 2)) + " foi adicionado a entrada." + Fore.RESET, sep="")
            lastLoss = None
        print(Fore.GREEN + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ") (",
              config["options"].upper(),
              ") ",
              self["parity"],
              " = Entrada em ",
              self["action"],
              " efetuada com sucesso | valor: ", str(round(moneyForOperations, 2)), " | timeframe ",
              str(self["timeframe"]),
              "M | id: ",
              id, Fore.RESET, end="", sep="")
        result, gain = check_win(id)
        totalEarnings += gain
        if gain < 0:
            if int(self["martingale"]) > 0 and config["strategy"].upper() == "GALE":
                currentgale = 0
                while currentgale < int(config["galemax"]):
                    moneyForOperations *= float(config["galefactor"])
                    print(Fore.GREEN + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ") (",
                          config["options"], ")",
                          " Resultado: ", gain,
                          " | operando em gale (", currentgale + 1, "/", config["galemax"],
                          ") | valor da nova operação: ", str(round(moneyForOperations, 2)), end="", sep="")
                    color = Fore.GREEN if totalEarnings > 0 else Fore.RED
                    print(Fore.BLUE + "\nLucro atual: ", color + str(round(totalEarnings, 2)),
                          Fore.RESET, Fore.BLUE + "/", round(totalEarningsToClose, 2), Fore.RESET,
                          sep="")
                    check, id = buy(self, moneyForOperations)
                    result, gain = check_win(id)
                    print(Fore.GREEN + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ")",
                          " Resultado da operação = ", str(round(gain, 2)), Fore.RESET, end="", sep="")
                    color = Fore.GREEN if totalEarnings > 0 else Fore.RED
                    print(Fore.BLUE + "\nLucro atual: ", color + str(round(totalEarnings, 2)),
                          Fore.RESET, Fore.BLUE + "/", round(totalEarningsToClose, 2), Fore.RESET,
                          sep="")
                    currentgale += 1
                    if gain > 0:
                        break
            elif float(config["doublefactor"]) > 0 and config["strategy"].upper() == "DOBROOUNADA":
                print(Fore.GREEN + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ") (",
                      config["options"], ")",
                      " Resultado: ", gain,
                      " | o valor de ", str(round(moneyForOperations * float(config["doublefactor"]), 2)),
                      " será adicionado na proxima entrada.",
                      " | valor da nova operação: ", str(round(moneyForOperations, 2)), end="", sep="")
                color = Fore.GREEN if totalEarnings > 0 else Fore.RED
                print(Fore.BLUE + "\nLucro atual: ", color + str(round(totalEarnings, 2)),
                      Fore.RESET, Fore.BLUE + "/", round(totalEarningsToClose, 2), Fore.RESET,
                      sep="")
                lastLoss = abs(gain)
        else:
            print(Fore.GREEN + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ")",
                  " Resultado da operação = ", round(gain, 2), end="", sep="")
            color = Fore.GREEN if totalEarnings > 0 else Fore.RED
            print(Fore.BLUE + "\nLucro atual: ", color + str(round(totalEarnings, 2)),
                  Fore.RESET, Fore.BLUE + "/", round(totalEarningsToClose, 2), Fore.RESET,
                  sep="")
    else:
        print(Fore.RED + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ") (", config["options"],
              ") ",
              self["parity"],
              " = Entrada em ",
              self["action"],
              " cancelada, mercado fechado =( | valor: ", str(moneyForOperations), " | timeframe ",
              str(self["timeframe"]),
              "M", Fore.RESET, "\n", end="", sep="")
        print(Fore.RED + "ERRO: ", id, Fore.RESET)


def get_trend(self, parity, timeframe):
    velas = self.get_candles(parity, (int(timeframe) * 60), 20, datetime.time())
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


def start_signals_core():
    global stopwin
    global totalEarningsToClose
    global totalEarnings
    header = {"User-Agent": r"Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0"}
    session.set_session(header, {})
    checkConnection, reason = session.connect()
    if checkConnection:
        balance = session.get_balance()
        totalEarningsToClose = round(balance * int(config["maxwin"]) / 100, 2)
        totalEarnings = 0
        print(Fore.CYAN + "Sua banca total é de", str(round(balance, 2)))
        print(Fore.CYAN + "O total de ganhos para concluir as operações hoje é de", totalEarningsToClose)
        session.change_balance(config["mode"])
        print(Fore.GREEN + "Conexão feita com sucesso. Iniciando operações.")
        print(Fore.GREEN + "Aguardando sinais...\n")
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
                print(Fore.RED + "\nOcorreu uma falha ->", e)
                time.sleep(5)
            if totalEarnings >= totalEarningsToClose and stopwin is None:
                print(Fore.YELLOW + "\nLucro de ", Fore.GREEN + round(totalEarnings, 2), Fore.YELLOW + "/",
                      round(totalEarningsToClose, 2),
                      ", meta alcançada hoje. Finalizando operações por hoje.\n", Fore.RESET, sep="")
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
    start_signals_core()


if __name__ == "__main__":
    main()
