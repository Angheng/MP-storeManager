import sys

import pymysql as sql
from PyQt5.QtWidgets import QLabel, QComboBox, QWidget, QApplication, QVBoxLayout, QHBoxLayout, QSpinBox, QPushButton

import requests
import json

from pyfcm import FCMNotification
push_sevice = FCMNotification(api_key='AAAA-3x8xzg:APA91bHR0MyJue9WfJ4uohd5VR4K1sxG0yLTOHtZi0hsXFvWqZ4W1JiyE73Jcwt1bNO5VhRcniYm8mmz6WJl7buFkCqURW9QPeAEabWwYJ2gBikR1qUQo09gied4lkfLLeJprQbFonMo')


class MySQL:

    def __init__(self, host, user, pw, db, charset):
        self.host = host
        self.user = user
        self.pw = pw
        self.db = db
        self.charset = charset

    def show(self, col="", table="", where=""):
        conn = sql.connect(
            host=self.host,
            user=self.user,
            password=self.pw,
            db=self.db,
            charset=self.charset)

        inst = 'SELECT '

        if col != "":
            inst += col + ' FROM ' + table
        else:
            inst += '* FROM ' + table

        if where is not "":
            inst += ' WHERE ' + where

        print(inst)
        try:
            with conn.cursor() as curs:
                curs.execute(inst)
                return curs.fetchall()

        finally:
            conn.close()

    def execute(self, inst):
        conn = sql.connect(
            host=self.host,
            user=self.user,
            password=self.pw,
            db=self.db,
            charset=self.charset)

        try:
            with conn.cursor() as curs:
                print(inst)
                curs.execute(inst)
            conn.commit()

        finally:
            conn.close()


class App(QWidget):

    def __init__(self):
        super().__init__()

        self.sql = MySQL('54.180.153.64', 'MPuser', '13572468', 'MPDB', 'utf8')
        self.initUI()

    def initUI(self):
        # Store ComboBox ==================================

        self.storeLabel = QLabel('store not selected')
        self.storeLabel.adjustSize()

        self.cb = QComboBox()
        self.setCb()
        self.cb.activated[str].connect(self.optionActivated)

        storebox = QHBoxLayout()
        storebox.addWidget(self.storeLabel)
        storebox.addWidget(self.cb)

        # =================================================

        # Remain And Max Amount ===========================

        self.remainValue = QLabel('')
        self.maxValue = QLabel('')

        userAmountBox = QHBoxLayout()
        userAmountBox.addWidget( QLabel('Remain: ') )
        userAmountBox.addWidget(self.remainValue)
        userAmountBox.addWidget( QLabel('Max: ') )
        userAmountBox.addWidget(self.maxValue)

        # =================================================

        # Spinner For Amount Modifying ====================

        self.spinBox = QSpinBox()
        self.spinBox.setMinimum(0)
        self.spinBox.setMaximum(80)
        self.spinBox.setSingleStep(1)

        incBtn = QPushButton('Increase')
        incBtn.setObjectName('inc')
        decBtn = QPushButton('Decrease')
        decBtn.setObjectName('dec')

        incBtn.clicked.connect(self.amountModifying)
        decBtn.clicked.connect(self.amountModifying)

        modifyingBox = QHBoxLayout()
        modifyingBox.addWidget(self.spinBox)
        modifyingBox.addWidget(incBtn)
        modifyingBox.addWidget(decBtn)

        # =================================================

        vBox = QVBoxLayout()
        vBox.addLayout(storebox)
        vBox.addLayout(userAmountBox)
        vBox.addLayout(modifyingBox)

        self.setLayout(vBox)
        self.setWindowTitle('Store Manager')
        self.setGeometry(300, 300, 720, 540)
        self.show()

    def setCb(self):
        stores = self.sql.show(table='stores')

        for store in stores:
            self.cb.addItem(store[1])

    def amountModifying(self):
        if self.storeLabel.text() == 'store not selected':
            return

        btn = self.sender()
        val = 0

        if btn.objectName() == 'inc':
            val = int(self.remainValue.text()) + int(self.spinBox.value())
        else:
            val = int(self.remainValue.text()) - int(self.spinBox.value())

        if 0 <= val <= int(self.maxValue.text()):
            self.sql.execute("UPDATE stores SET remain='{}' WHERE name='{}'".format(str(val), self.storeLabel.text()))
            self.remainValue.setText(str(val))
            self.fmcMessaging(self.storeLabel.text())

    def fmcMessaging(self, store):
        reserves = self.sql.show(col='reserve', table='stores', where="name='"+store+"'")
        reserves = json.loads(reserves[0][0])

        remain = int(self.remainValue.text())
        targ_tokens = list()
        jsonResult = str()

        data = {
            "title": "가게로 가면 됩니당",
            "body": "가게가 텅텅"
        }
        notification = {
                "title": "가게로 가영",
                "body": "가게가 텅텅"
            }


        for reserve in reserves:
            if remain - reserve['amount'] >= 0:
                remain -= reserve['amount']
                targ_tokens.append(reserve['token'])


            else:
                jsonResult += "json_object('token', '{}', 'amount', ),".format(reserve['token'], reserve['amount'])

        if remain != int(self.remainValue.text()):
            self.sql.execute("UPDATE stores SET remain='{}' WHERE name='{}'".format(str(remain), self.storeLabel.text()))
            self.remainValue.setText(str(remain))
            self.sql.execute("UPDATE stores SET reserve=json_array({}) WHERE name='{}'"
                             .format(jsonResult[:-1], self.storeLabel.text())
                             )

        if len(targ_tokens) > 0:
            result = push_sevice.notify_multiple_devices(
                registration_ids=targ_tokens,
                message_body=notification,
                data_message=data
            )
            print(result)

    def optionActivated(self, txt):
        self.storeLabel.setText(txt)
        store = self.sql.show(table='stores', where="name='"+txt+"'")[0]

        self.remainValue.setText(str(store[3]))
        self.maxValue.setText(str(store[4]))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
