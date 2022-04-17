# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

import os
import math

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
        system.undo_stack = QUndoStack(self)
        system.undo_stack.setUndoLimit(50)
        system.undo_stack.cleanChanged.connect(self.onUndoStackCleanChanged)
        system.actions = system.Actions(self)

        self.setWindowTitle("[*]")
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
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

        default_file_path = os.path.join(system.DEFAULT_FILE_DIR, system.DEFAULT_FILE_NAME)
        file_path = system.settings.value("file_path", default_file_path, type=str)
        system.last_dialog_dir = system.settings.value("last_dir", system.DEFAULT_FILE_DIR, type=str)
        is_grayscale = system.settings.value("grayscale", False, type=bool)
        system.actions.grayscale.setChecked(is_grayscale)
        self.setGrayscale(is_grayscale)
        is_filtering = system.settings.value("filtering", True, type=bool)
        system.actions.filtering.setChecked(is_filtering)
        self.setFiltering(is_filtering)

        # project
        if os.path.isfile(file_path):
            system.sql.file_path = file_path
            system.sql.createDatabase()
            self.view.load()


    def loadFile(self, file_path: str):
        self.scene.clear()
        system.sql.file_path = file_path
        system.sql.createDatabase()
        self.view.load()


    def save(self):
        # settings
        system.settings.setValue("geometry", self.geometry())
        default_file_path = os.path.join(system.DEFAULT_FILE_DIR, system.DEFAULT_FILE_NAME)
        file_path = default_file_path

        # project
        if system.sql.file_path == "":
            file_path, _selected_filter = QFileDialog().getSaveFileName(
                self,
                "Save Project",
                default_file_path,
                system.PROJECT_FILTER
            )

            if file_path:
                system.last_dialog_dir, _ = os.path.split(file_path)
                system.sql.file_path = file_path
                system.sql.createDatabase()
                system.sql.updateView(self.view)
                items = self.scene.items()
                for item in items:
                    system.sql.storeItem(item)
            else:
                return
        else:
            file_path = system.sql.file_path
            items = self.scene.items()
            system.sql.updateView(self.view)
            system.sql.updateItems(items)

        system.settings.setValue("file_path", file_path)
        system.settings.setValue("last_dir", system.last_dialog_dir)
        system.settings.setValue("grayscale", system.actions.grayscale.isChecked())
        system.settings.setValue("filtering", system.actions.filtering.isChecked())


    def open(self):
        start_dir = system.last_dialog_dir
        file_path, _selected_filter = QFileDialog().getOpenFileName(
            self,
            "Open Project",
            start_dir,
            system.PROJECT_FILTER
        )

        if file_path:
            system.last_dialog_dir, _ = os.path.split(file_path)
            self.loadFile(file_path)
        else:
            return


    def quit(self) -> None:
        self.close()


    def closeEvent(self, _event: QCloseEvent) -> None:
        pass


    def flipSelection(self) -> None:
        items = self.scene.selectedItems()
        for item in items:
            item.flip()


    def setGrayscale(self, state: bool) -> None:
        self.view.grayscale_effect.setEnabled(state)


    def selectAll(self) -> None:
        self.scene.clearSelection()
        items = self.scene.items()
        for item in items:
            item.setSelected(True)


    def setFiltering(self, state: bool) -> None:
        items = self.scene.items()
        mode = None
        if state:
            mode = Qt.TransformationMode.SmoothTransformation
        else:
            mode = Qt.TransformationMode.FastTransformation
        self.view.transformation_mode = mode
        for item in items:
            item.setTransformationMode(mode)


    def packSelection(self) -> None:
        self.view.packSelection()


    def deleteSelection(self) -> None:
        items = self.scene.selectedItems()
        if not len(items) > 0:
            return

        for item in items:
            system.sql.deleteItem(item)
            self.scene.removeItem(item)


    def onUndoStackCleanChanged(self, state: bool) -> None:
        self.setWindowModified(not state)


    def resetSelectionTransforms(self) -> None:
        items = self.scene.selectedItems()
        if not len(items) > 0:
            return

        for item in items:
            scale = item.scale() * 1.0/item.scale()
            item.setScale(scale)

            group = self.scene.createItemGroup([item])
            center = group.boundingRect().center()
            group.setTransformOriginPoint(center)
            rotation = math.degrees(item.getRotation())
            group.setRotation(0.0 - rotation)
            self.scene.destroyItemGroup(group)
