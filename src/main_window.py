# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from graphics_view import GraphicsView


class MainWindow(QMainWindow):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self._scene = QGraphicsScene(self)
        self._view = GraphicsView(self._scene, self)
        self._settings = QSettings(self)

        ax = 500
        ay = 200
        aw = 720
        ah = 480
        self.setGeometry(ax, ay, aw, ah)

        # self.setWindowTitle(f"{info.fileName()}[*]")
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setCentralWidget(self._view)
        self.show()

        stylesheet_path = "stylesheet.qss"
        with open(stylesheet_path, "r") as fp:
            data = fp.read()
            self.setStyleSheet(data)


    def closeEvent(self, _event: QCloseEvent) -> None:
        pass
