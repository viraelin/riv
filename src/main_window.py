# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

import os
import math
import time

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

import system
from graphics_view import GraphicsView
from graphics_item import GraphicsItem


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

        system.item_load_thread = QThread()
        system.item_load_worker = system.ItemLoadWorker()
        system.item_load_worker.view = self.view
        system.item_load_worker.moveToThread(system.item_load_thread)
        system.item_load_worker.finished.connect(system.item_load_thread.quit)
        system.item_load_worker.progress.connect(self.onItemLoadWorkerProgress)
        system.item_load_worker.finished.connect(self.onItemLoadWorkerFinished)
        system.item_load_thread.started.connect(system.item_load_worker.run)

        system.item_drop_thread = QThread()
        system.item_drop_worker = system.ItemDropWorker()
        system.item_drop_worker.view = self.view
        system.item_drop_worker.moveToThread(system.item_drop_thread)
        system.item_drop_worker.finished.connect(system.item_drop_thread.quit)
        system.item_drop_worker.finished.connect(self.onItemDropWorkerFinished)
        system.item_drop_worker.progress.connect(self.onItemDropWorkerProgress)
        system.item_drop_thread.started.connect(system.item_drop_worker.run)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setValue(0)
        self.progress_bar.hide()

        self.setWindowTitle("[*]")
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        # self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
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
        self.view.resetTransform()
        system.sql.file_path = file_path
        system.sql.createDatabase()
        system.undo_stack.clear()
        system.undo_stack.resetClean()
        system.settings.setValue("file_path", file_path)
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

        system.undo_stack.setClean()


    def open(self):
        file_path, _selected_filter = QFileDialog().getOpenFileName(
            self,
            "Open Project",
            system.last_dialog_dir,
            system.PROJECT_FILTER
        )

        if file_path:
            system.last_dialog_dir, _ = os.path.split(file_path)
            self.loadFile(file_path)


    def new(self) -> None:
        if self.isWindowModified():
            result = self.notifyUnsavedChanges()
            if result == QMessageBox.StandardButton.Save:
                self.save()
            elif result == QMessageBox.StandardButton.Discard:
                pass
            elif result == QMessageBox.StandardButton.Cancel:
                return
            else:
                return

        default_file_path = os.path.join(system.last_dialog_dir, system.DEFAULT_FILE_NAME)
        file_path, _selected_filter = QFileDialog().getSaveFileName(
            self,
            "New Project",
            default_file_path,
            system.PROJECT_FILTER
        )

        if file_path:
            system.last_dialog_dir, _ = os.path.split(file_path)
            project_ext = ".riv"

            name, ext = os.path.splitext(file_path)
            if ext != project_ext:
                ext = project_ext
                file_path = name+ext

            if os.path.isfile(file_path):
                # OS responsibility, but:
                result = QMessageBox().warning(
                    self,
                    "Overwrite File",
                    f"Overwrite contents of '{file_path}'?",
                    QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Ok
                )

                if result != QMessageBox.StandardButton.Ok:
                    return

                os.remove(file_path)

            self.loadFile(file_path)


    def quit(self) -> None:
        self.close()


    def closeEvent(self, event: QCloseEvent) -> None:
        if self.isWindowModified():
            result = self.notifyUnsavedChanges()
            if result == QMessageBox.StandardButton.Save:
                self.save()
                event.accept()
            elif result == QMessageBox.StandardButton.Discard:
                event.accept()
            elif result == QMessageBox.StandardButton.Cancel:
                event.ignore()
            else:
                event.ignore()


    def notifyUnsavedChanges(self) -> QMessageBox.StandardButton:
        result = QMessageBox().warning(
            self,
            "Unsaved Changes",
            "The file has been modified.\nDo you want to save it?",
            QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )

        return result


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


    def importImages(self) -> None:
        # todo: thread
        image_filter = "Images (*.png *.jpg *.jpeg)"
        file_paths, _selected_filter = QFileDialog().getOpenFileNames(
            self,
            "Import Images",
            system.last_dialog_dir,
            image_filter
        )

        if len(file_paths) > 0:
            pos = QPointF(system.actions.menu.pos())
            path, _ = os.path.split(file_paths[0])
            system.last_dialog_dir = path

            self.scene.clearSelection()
            item_count = 0
            for file_path in file_paths:
                item = self.view.addItem(path=file_path, pos=pos)
                if item:
                    item.setSelected(True)
                    self.scene.addItem(item)
                    item_count += 1

            if item_count > 1:
                self.packSelection()


    def exportImages(self) -> None:
        items = self.scene.selectedItems()
        assert(len(items) > 0)

        directory = QFileDialog().getExistingDirectory(
            self,
            "Export Selection",
            system.last_dialog_dir
        )

        if not directory:
            return

        for item in items:
            files = os.listdir(directory)

            new_name = item.path
            name, ext = os.path.splitext(item.path)

            index = 0
            while new_name in files:
                new_name = f"{name}-{index}{ext}"
                index += 1

            file_name = os.path.join(directory, new_name)

            with open(file_name, "wb") as fp:
                data = system.sql.getImage(item)
                fp.write(data)

            atime = time.time()
            mtime = item.mtime
            os.utime(file_name, (atime, mtime))


    def onItemLoadWorkerProgress(self, item: GraphicsItem, value: int, total: int) -> None:
        self.scene.addItem(item)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(value)
        self.view.update()


    def onItemLoadWorkerFinished(self) -> None:
        self.progress_bar.hide()

    
    def onItemDropWorkerProgress(self, item: GraphicsItem, value: int, total: int) -> None:
        self.scene.addItem(item)
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(value)
        self.view.update()


    def onItemDropWorkerFinished(self, result: int, items: list) -> None:
        if len(items) > 1:
            self.view.scene().clearSelection()
            for item in items:
                item.setSelected(True)
            self.view.packSelection()
        self.progress_bar.hide()
