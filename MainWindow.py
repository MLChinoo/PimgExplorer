# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MainWindow.ui'
##
## Created by: Qt User Interface Compiler version 6.9.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QCommandLinkButton, QGraphicsView,
    QGridLayout, QHBoxLayout, QLineEdit, QListWidget,
    QListWidgetItem, QMainWindow, QPushButton, QSizePolicy,
    QStatusBar, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(800, 600)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(20)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.openButton = QPushButton(self.centralwidget)
        self.openButton.setObjectName(u"openButton")

        self.horizontalLayout.addWidget(self.openButton)

        self.lineEdit = QLineEdit(self.centralwidget)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setReadOnly(True)

        self.horizontalLayout.addWidget(self.lineEdit)

        self.composeCheckBox = QCheckBox(self.centralwidget)
        self.composeCheckBox.setObjectName(u"composeCheckBox")

        self.horizontalLayout.addWidget(self.composeCheckBox)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setSpacing(6)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setSpacing(6)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.listWidget = QListWidget(self.centralwidget)
        self.listWidget.setObjectName(u"listWidget")

        self.verticalLayout_2.addWidget(self.listWidget)

        self.exportSingleButton = QCommandLinkButton(self.centralwidget)
        self.exportSingleButton.setObjectName(u"exportSingleButton")

        self.verticalLayout_2.addWidget(self.exportSingleButton)

        self.exportAllButton = QCommandLinkButton(self.centralwidget)
        self.exportAllButton.setObjectName(u"exportAllButton")

        self.verticalLayout_2.addWidget(self.exportAllButton)


        self.horizontalLayout_2.addLayout(self.verticalLayout_2)

        self.graphicsView = QGraphicsView(self.centralwidget)
        self.graphicsView.setObjectName(u"graphicsView")

        self.horizontalLayout_2.addWidget(self.graphicsView)

        self.horizontalLayout_2.setStretch(0, 1)
        self.horizontalLayout_2.setStretch(1, 3)

        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.verticalLayout.setStretch(0, 1)
        self.verticalLayout.setStretch(1, 10)

        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"PIMG Explorer", None))
        self.openButton.setText(QCoreApplication.translate("MainWindow", u"Open...", None))
        self.composeCheckBox.setText(QCoreApplication.translate("MainWindow", u"Compose diff images", None))
        self.exportSingleButton.setText(QCoreApplication.translate("MainWindow", u"Export single image...", None))
        self.exportAllButton.setText(QCoreApplication.translate("MainWindow", u"Export all images...", None))
    # retranslateUi

