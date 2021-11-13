from iqoptionapi.stable_api import IQ_Option
import logging
import time
API=IQ_Option("pedroeugeniocavalcanti@gmail.com", "PEdro2014")
API.connect()


def get_trend_v2(self, parity, timeframe):
    velas = self.get_candles(parity, (int(timeframe) * 60), 60, time.time())
    print("velas qtd",len(velas))
    ultimo = round(velas[0]['close'], 4)
    primeiro = round(velas[-1]['close'], 4)
    diferenca = abs(round(((ultimo - primeiro) / primeiro) * 100, 3))
    trend = "CALL" if ultimo < primeiro and diferenca > 0.01 else "PUT" if ultimo > primeiro and diferenca > 0.01 else False
    print("ultimo", ultimo)
    print("primeiro", primeiro)
    print("diferença",diferenca)
    print("-------------------")
    return trend