#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Dec 16 15:50:30 2018

@author: mattis
"""

import sys
from PyQt5 import QtWidgets
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMainWindow, QLabel, QGridLayout, QWidget, QListWidget, QListWidgetItem
from PyQt5.QtCore import QSize, QThread, QObject, pyqtSignal
import time
import PyQt5 as Qt

class HelloWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setMinimumSize(QSize(640, 480))    
        self.setWindowTitle("Hello world") 

        self.listWidget = GalleryWidget()
        self.setCentralWidget(self.listWidget)
        
    def addPic(self,name):
        self.listWidget.addItem(QListWidgetItem(QIcon('thumbSmall.jpg'),name))
        
class GalleryWidget(QListWidget):
    def __init__(self, parent=None):
        super(GalleryWidget, self).__init__(parent)
        self.setViewMode(QListWidget.IconMode)
        self.setIconSize(QSize(200,200))
        self.setResizeMode(QListWidget.Adjust)
        self.addItem(QListWidgetItem(QIcon('thumbSmall.jpg'), 'Test'))
        
class SomeObject(QObject):

    finished = pyqtSignal()
    addPic = pyqtSignal(str)
    

    def long_running(self):
        count = 0
        while count < 20:
            time.sleep(0.1)
            print("B Increasing")
            count += 1
            self.addPic.emit('name')
        self.finished.emit()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    mainWin = HelloWindow()
    mainWin.show()
    mainWin.addPic('name')
    objThread = QThread()
    
    obj = SomeObject()
    obj.moveToThread(objThread)
    obj.finished.connect(objThread.quit)
    objThread.started.connect(obj.long_running)
    #objThread.finished.connect(app.exit)
    obj.addPic.connect(mainWin.addPic)
    objThread.start()
        
    sys.exit( app.exec_() )
    