# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'remoteQtUI.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1305, 913)
        MainWindow.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.fwButton = QtWidgets.QPushButton(self.centralwidget)
        self.fwButton.setGeometry(QtCore.QRect(640, 700, 51, 41))
        self.fwButton.setAutoRepeat(False)
        self.fwButton.setAutoRepeatInterval(10)
        self.fwButton.setObjectName("fwButton")
        self.bwButton = QtWidgets.QPushButton(self.centralwidget)
        self.bwButton.setGeometry(QtCore.QRect(640, 820, 51, 41))
        self.bwButton.setObjectName("bwButton")
        self.leftButton = QtWidgets.QPushButton(self.centralwidget)
        self.leftButton.setGeometry(QtCore.QRect(570, 760, 51, 41))
        self.leftButton.setObjectName("leftButton")
        self.rightButton = QtWidgets.QPushButton(self.centralwidget)
        self.rightButton.setGeometry(QtCore.QRect(710, 760, 51, 41))
        self.rightButton.setObjectName("rightButton")
        self.streamButton = QtWidgets.QPushButton(self.centralwidget)
        self.streamButton.setGeometry(QtCore.QRect(630, 750, 71, 61))
        self.streamButton.setObjectName("streamButton")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(10, 10, 1271, 671))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(0, 700, 71, 21))
        self.label_2.setObjectName("label_2")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1305, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Terminator"))
        self.fwButton.setText(_translate("MainWindow", "FW"))
        self.fwButton.setShortcut(_translate("MainWindow", "W"))
        self.bwButton.setText(_translate("MainWindow", "BW"))
        self.bwButton.setShortcut(_translate("MainWindow", "S"))
        self.leftButton.setText(_translate("MainWindow", "LEFT"))
        self.leftButton.setShortcut(_translate("MainWindow", "A"))
        self.rightButton.setText(_translate("MainWindow", "RIGHT"))
        self.rightButton.setShortcut(_translate("MainWindow", "D"))
        self.streamButton.setText(_translate("MainWindow", "STREAM"))
        self.streamButton.setShortcut(_translate("MainWindow", "Q"))
        self.label.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">Image View</p></body></html>"))
        self.label_2.setText(_translate("MainWindow", "<html><head/><body><p><span style=\" font-size:16pt;\">FPS: </span></p></body></html>"))
