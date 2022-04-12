# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

import system
from graphics_view import GraphicsView


class MainWindow(QMainWindow):

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.scene = QGraphicsScene(self)
        self.view = GraphicsView(self.scene, self)

        system.sql = system.Database()
        system.settings = QSettings(self)
        system.actions = system.Actions(self)

        # self.setWindowTitle(f"{info.fileName()}[*]")
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
        self.setCentralWidget(self.view)
        self.show()

        stylesheet_path = "stylesheet.qss"
        with open(stylesheet_path, "r") as fp:
            data = fp.read()
            self.setStyleSheet(data)

        self.load()


    def load(self):
        # settings
        default_geometry = QRect(500, 200, 720, 480)
        geometry = system.settings.value("geometry", default_geometry, type=QRect)
        self.setGeometry(geometry)

        # project
        system.sql.createDatabase()
        self.view.load()


    def save(self):
        # settings
        system.settings.setValue("geometry", self.geometry())

        # project
        items = self.scene.items()
        system.sql.saveDatabase(self.view, items)


    def closeEvent(self, _event: QCloseEvent) -> None:
        pass
