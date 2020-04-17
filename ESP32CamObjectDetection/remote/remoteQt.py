# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'remoteQt.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

import PyQt5
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QThread, pyqtSignal, QRectF
from time import sleep
import asyncore
import numpy as np
import pickle
from imageThread import ImageThread
import cv2
import time

DEBUG = False

class Ui_MainWindow(object):

    def __init__(self):
        self.setupUi(self)

        self.ImageThread = ImageThread()
        self.ImageThread.new_image.connect(self.viewImage)
    
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
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1305, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(0, 700, 71, 21))
        self.label_2.setObjectName("label_2")

        self.fwButton.setCheckable(True)
        self.fwButton.toggled.connect(self.buttontoggled)
        self.bwButton.setCheckable(True)
        self.bwButton.toggled.connect(self.buttontoggled)
        self.leftButton.setCheckable(True)
        self.leftButton.toggled.connect(self.buttontoggled)
        self.rightButton.setCheckable(True)
        self.rightButton.toggled.connect(self.buttontoggled)
        self.streamButton.setCheckable(True)
        self.streamButton.toggled.connect(self.buttontoggled)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 942, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def viewImage(self):
      img, fps = self.ImageThread.getImage()
      if img is not None:
        img = cv2.resize(img, (self.label.size().width(), self.label.size().height()))
        # img = img[:, :, ::-1]
        height, width, channel = img.shape
        bytesPerLine = 3 * width
        self.qImg = QImage(img.data, width, height, bytesPerLine, QImage.Format_RGB888)
        pixMap = QPixmap.fromImage(self.qImg)
        self.label.setPixmap(pixMap)
        self.label_2.setText('FPS: {}'.format(fps))
        # print('label size {}'.format(self.label.size()))
        # print('image size {}'.format(self.qImg.size()))

        if DEBUG:
          cv2.imwrite('test2.jpg', self.ImageThread.getImage())

    def closeEvent(self, event):
        self.ImageThread.stop_signal.emit()
        self.ImageThread.wait()

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "ControlPanel"))
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
        self.label_2.setText(_translate("MainWindow", "<html><head/><body><p><span style=\" font-size:12pt;\">FPS: </span></p></body></html>"))
    
    def buttontoggled(self):
        sender = self.sender()  # This is what you need
        if sender.isChecked():
          if sender.text() == 'STREAM':
            print('START')
            self.streamButton.setChecked(True)
            if self.ImageThread.isPause:
              self.ImageThread.resume_signal.emit()
            else:
              self.ImageThread.start()
          if sender.text() == 'LEFT':
            self.ImageThread.requestLeft(True)
          if sender.text() == 'RIGHT':
            self.ImageThread.requestRight(True)
          if sender.text() == 'FW':
            self.ImageThread.requestFw(True)
          if sender.text() == 'BW':
            self.ImageThread.requestBw(True)
          self.statusBar().showMessage(sender.text() + ' is pressed')
        else:
          if sender.text() == 'STREAM':
            print('PAUSE')
            self.streamButton.setChecked(False)
            self.ImageThread.pause_signal.emit()
          if sender.text() == 'LEFT':
            self.ImageThread.requestLeft(False)
          if sender.text() == 'RIGHT':
            self.ImageThread.requestRight(False)
          if sender.text() == 'FW':
            self.ImageThread.requestFw(False)
          if sender.text() == 'BW':
            self.ImageThread.requestBw(False)
          self.statusBar().showMessage(sender.text() + ' is released')

    def onkeyPressEvent(self,event):
        if event.key() == ord('W') and not event.isAutoRepeat():
          
          self.fwButton.setChecked(True)
        
        if event.key() == ord('S') and not event.isAutoRepeat():
          self.bwButton.setChecked(True)
        
        if event.key() == ord('A') and not event.isAutoRepeat():
          self.leftButton.setChecked(True)

        if event.key() == ord('D') and not event.isAutoRepeat():
          self.rightButton.setChecked(True)

        if not event.isAutoRepeat():
          print(event.key())

    def onkeyReleaseEvent(self, event):
        if event.key() == ord('W') and not event.isAutoRepeat():
          self.fwButton.setChecked(False)
        
        if event.key() == ord('S') and not event.isAutoRepeat():
          self.bwButton.setChecked(False)
        
        if event.key() == ord('A') and not event.isAutoRepeat():
          self.leftButton.setChecked(False)

        if event.key() == ord('D') and not event.isAutoRepeat():
          self.rightButton.setChecked(False)

        if not event.isAutoRepeat():
          print(event.key())

