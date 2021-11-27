from datetime import datetime

import mysql.connector as mysql


class MysqlConnection:
    def myConnection(self):
        return mysql.connect(
            host="localhost",
            user="root",
            database="dbbot",
            password="",
  	    auth_plugin='mysql_native_password'
        )

    def saveOperation(self, operation):
        db = self.myConnection()
        cursor = db.cursor()
        cursor.execute("INSERT INTO operacoes(inicio, fim, paridade, tempo, valor, resultado, tipo_conta) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s)",
                        (operation.get("start"), operation.get("end"), operation.get("parity"),
                         operation.get("timeframe"),
                         operation.get("value"),
                         round(float(operation.get("result")),2),
 			 operation.get("account_type")))
        db.commit()


