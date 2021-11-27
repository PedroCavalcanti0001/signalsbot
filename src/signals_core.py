import datetime
import logging
import time

from colorama import Fore
from iqoptionapi.stable_api import IQ_Option

from src.loader.config import Config
from src.loader.signals import Signals
from src.mysql_connection import MysqlConnection

logging.basicConfig(level=logging.ERROR)

error_password = """{"code":"invalid_credentials","message":"You entered the wrong credentials. Please check that the login/password is correct."}"""
config = Config.load_config()
user = config["email"]
password = config["password"]
session = IQ_Option(user, password, config["mode"])
totalEarnings = 0
ids = []
stopwin = None
stoploss = None
start = datetime.datetime.now()
totalEarningsToClose = 0
lastLoss = None
moneyForOperations = 0
doublesUsedInSequence = 0


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


def timestamp_to_date(timestamp):
    timestamp = timestamp / 1000
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt


def opening_message(balance, totalLossesToClose):
    print(Fore.YELLOW + "_________________________________________________________________")
    print("")
    print(Fore.CYAN + "Operando em conta ", Fore.WHITE + config["mode"] + Fore.CYAN + ".", sep="")
    print(Fore.CYAN + "O valor base para operações é de ",
          Fore.WHITE + str(round(balance * float(config["operatingpercentage"]) / 100.0, 2)) + Fore.CYAN + ".",
          sep="")
    print(Fore.CYAN + "Sua banca total é de ", Fore.WHITE + str(round(balance, 2)) + Fore.CYAN + ".",
          sep="")
    print(Fore.CYAN + "O total de ganhos para concluir as operações hoje é de ", Fore.GREEN,
          "+" + str(totalEarningsToClose) + Fore.CYAN + " (" + config["maxwin"] + "%) " + Fore.RESET, sep="")
    print(Fore.CYAN + "O total de perdas para terminar as operações hoje é de ", Fore.RED,
          "-" + str(totalLossesToClose) + Fore.CYAN + " (" + config["maxloss"] + "%) " + Fore.RESET, sep="")
    print(Fore.CYAN + "Conexão feita com sucesso. Iniciando operações.")
    print(Fore.GREEN + "Aguardando sinais...")
    print(Fore.YELLOW + "_________________________________________________________________\n")


def save_operation(id, parity, timeframe, value, result):
    mysqlConnection = MysqlConnection()
    ret = session.get_async_order(id)["position-changed"]["msg"]
    opentime = ret["open_time"]
    closetime = ret["close_time"]
    opentime_datetime = timestamp_to_date(opentime)
    closetime_datetime = timestamp_to_date(closetime)
    mysqlConnection.saveOperation({
        "start": opentime_datetime,
        "end": closetime_datetime,
        "timeframe": timeframe,
        "value": value,
        "parity": parity,
        "result": result,
        "account_type": config["mode"]
    })


def start_signals_core():
    global stopwin, start, stoploss, totalEarningsToClose, totalEarnings
    header = {"User-Agent": r"Mozilla/5.0 (X11; Linux x86_64; rv:70.0) Gecko/20100101 Firefox/70.0"}
    session.set_session(header, {})
    checkConnection, reason = session.connect()
    if checkConnection:
        session.change_balance(config["mode"])
        balance = session.get_balance()
        totalEarningsToClose = round(balance * float(config["maxwin"]) / 100, 2)
        totalLossesToClose = round(balance * float(config["maxloss"]) / 100, 2)
        totalEarnings = 0
        opening_message(balance, totalLossesToClose)
        # Serve para fazer com que o minuto atual sÃ³ chega buscado na lista de sinais uma vez!
        checkInCurrentMin = False
        curMin = 0
        while True:
            if isinstance(stopwin, datetime.datetime):
                if stopwin.day == datetime.datetime.now().day:
                    continue
                else:
                    totalEarningsToClose = round(session.get_balance() * float(config["maxwin"]) / 100, 2)
                    totalEarnings = 0
                    stopwin = None
                    print("")
                    print(Fore.YELLOW + "Bot reiniciando operações após STOPWIN.")
                    balance = session.get_balance()
                    opening_message(balance, totalLossesToClose)
            elif isinstance(stoploss, datetime.datetime):
                if stoploss.day == datetime.datetime.now().day:
                    continue
                else:
                    totalEarningsToClose = round(session.get_balance() * float(config["maxloss"]) / 100, 2)
                    totalEarnings = 0
                    stoploss = None
                    print("")
                    print(Fore.YELLOW + "Bot reiniciando operações após STOPLOSS.")
                    balance = session.get_balance()
                    opening_message(balance, totalLossesToClose)
            try:
                if not session.check_connect():
                    checkConnection, reason = session.connect()
                    print(Fore.RED + "Conexão com iq option perdida..." + Fore.RESET)
                    if checkConnection:
                        print(Fore.GREEN + "Robo reconectado com sucesso!" + Fore.RESET)
                    else:
                        print(Fore.RED + "robo não conectado. ->", reason, Fore.RESET)
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
                            print(Fore.YELLOW + "_________________________________________________________________")
                        ##print("----")
                    checkInCurrentMin = True
                elif curMin != now.minute:
                    checkInCurrentMin = False
            except Exception as e:
                print(Fore.RED + "\nOcorreu uma falha ->", e)
                time.sleep(5)
            if totalEarnings >= totalEarningsToClose and stopwin is None:
                print(Fore.YELLOW + "\nLucro de ", Fore.GREEN + str(round(totalEarnings, 2)), Fore.YELLOW + "/",
                      str(round(totalEarningsToClose, 2)),
                      ", meta alcançada. Finalizando operações por hoje.\n", Fore.RESET, sep="")
                stopwin = datetime.datetime.now()
                print("stopwin", stopwin, stopwin is datetime.datetime, stopwin is datetime)
            if totalEarnings < 0 and totalLossesToClose < abs(totalEarnings) and stoploss is None:
                print(Fore.YELLOW + "\nPrejuizo de ", Fore.RED + str(round(totalEarnings, 2)), Fore.YELLOW + "/",
                      str(round(totalEarningsToClose, 2)),
                      ", stoploss alcançado. Finalizando operações hoje.\n", Fore.RESET, sep="")
                stoploss = datetime.datetime.now()
                print("stoploss", stoploss, stoploss is datetime.datetime, stoploss is datetime)
            if start.day is not datetime.datetime.now().day:
                start = datetime.datetime.now()
                print(Fore.YELLOW + "Reiniciando operações do bot...")


    else:
        if reason == "[Errno -2] Name or service not known":
            print(Fore.RED + "Sem internet..." + Fore.RESET)
        elif reason == error_password:
            print(Fore.RED + "Senha incorreta..." + Fore.RESET)
        else:
            print(Fore.RED + "Falha ao tentar conectar. ->", reason, Fore.RESET)


def new_operation(self, session):
    totalMoney = session.get_balance()
    global totalEarnings
    global lastLoss
    global moneyForOperations
    global doublesUsedInSequence
    # trend = get_trend(session, self["parity"], int(self["timeframe"]))
    moneyForOperations = round(totalMoney * float(config["operatingpercentage"]) / 100, 2)
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
    if lastLoss is not None and config["strategy"].upper() == "DOBROOUNADA":
        lastLossWithFactor = lastLoss * float(config["doublefactor"])
        moneyForOperations += lastLossWithFactor
        print(Fore.YELLOW + "* Estrategia 'DOBRO OU NADA' sendo utilizada, o valor de " + str(
            round(lastLossWithFactor, 2)) + " adicionado a entrada." + Fore.RESET, sep="")

    check, id = buy(self, moneyForOperations)
    if check:
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

        try:
            # def save_operation(id, parity, timeframe, value, result):
            save_operation(
                id, self["parity"], self["timeframe"], moneyForOperations, gain
            )
        except Exception as e:
            print(e)
        totalEarnings += gain

        if gain < 0:
            if int(self["martingale"]) > 0 and config["strategy"].upper() == "GALE":
                currentgale = 0
                while currentgale < int(config["galemax"]):
                    moneyForOperations *= float(config["galefactor"])
                    print(Fore.RED + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ") (",
                          config["options"], ")",
                          " Resultado: ", gain,
                          " | operando em gale (", currentgale + 1, "/", config["galemax"],
                          ") | valor da nova operação: ", str(round(moneyForOperations, 2)), end="", sep="")
                    color = Fore.GREEN if totalEarnings > 0 else Fore.RED
                    print(Fore.BLUE + "\nLucro atual: ", color + str(round(totalEarnings, 2)),
                          Fore.RESET, Fore.BLUE + "/", round(totalEarningsToClose, 2), Fore.RESET,
                          sep="")
                    check, id = buy(self, moneyForOperations)
                    col = Fore.GREEN if gain > 0 else Fore.RED
                    try:
                        save_operation(
                            id, self["parity"], self["timeframe"], moneyForOperations, gain,
                        )
                    except Exception as e:
                        print(e)

                    result, gain = check_win(id)
                    print(col + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ")",
                          " Resultado da operação = ", str(round(gain, 2)), Fore.RESET, end="", sep="")
                    color = Fore.GREEN if totalEarnings > 0 else Fore.RED
                    print(Fore.BLUE + "\nLucro atual: ", color + str(round(totalEarnings, 2)),
                          Fore.RESET, Fore.BLUE + "/", round(totalEarningsToClose, 2), Fore.RESET,
                          sep="")
                    currentgale += 1
                    if gain > 0:
                        break
            elif float(config["doublefactor"]) > 0 and config["strategy"].upper() == "DOBROOUNADA":
                col = Fore.GREEN if gain > 0 else Fore.RED
                print(col + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ")",
                      " Resultado da operação = ", str(round(gain, 2)), Fore.RESET, end="", sep="")
                color = Fore.GREEN if totalEarnings > 0 else Fore.RED
                print(Fore.BLUE + "\nLucro atual: ", color + str(round(totalEarnings, 2)),
                      Fore.RESET, Fore.BLUE + "/", round(totalEarningsToClose, 2), Fore.RESET,
                      sep="")
                if doublesUsedInSequence != int(config["doublelimit"]):
                    print(Fore.RED + "O valor de " + str(round(moneyForOperations * float(config["doublefactor"]), 2)),
                          " (LOSS X FACTOR) serÃ¡ somado valor de ", str(round(moneyForOperations, 2)),
                          " na proxima operação!\n" + Fore.RESET, end="", sep="")
                    if lastLoss is not None:
                        lastLoss += abs(gain)
                    else:
                        lastLoss = abs(gain)
                    doublesUsedInSequence += 1
                    if doublesUsedInSequence >= int(config["doublelimit"]):
                        doublesUsedInSequence = 0
                        lastLoss = None
                        print(Fore.RED + "Ultimo 'DOBROOUNADA' alcançado, cancelando..." + Fore.RESET)
        else:
            print(Fore.GREEN + "(", datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S').strip(), ")",
                  " Resultado da operação = ", round(gain, 2), end="", sep="")
            color = Fore.GREEN if totalEarnings > 0 else Fore.RED
            print(Fore.BLUE + "\nLucro atual: ", color + str(round(totalEarnings, 2)),
                  Fore.RESET, Fore.BLUE + "/", round(totalEarningsToClose, 2), Fore.RESET,
                  sep="")
            if totalEarnings > 0 and lastLoss is not None:
                lastLoss = None
    else:
        if lastLoss is not None:
            lastLossWithFactor = lastLoss * float(config["doublefactor"])
            moneyForOperations -= lastLossWithFactor
            print("limpando lastLoss em mercado fechado")

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


def main():
    start_signals_core()


if __name__ == "__main__":
    main()
