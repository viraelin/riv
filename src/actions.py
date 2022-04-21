# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMenu, QWidgetAction)
from PyQt6.QtGui import (QAction, QKeySequence)

import system


class Actions:

    def __init__(self, parent) -> None:
        self.parent = parent
        self.menu = QMenu(parent)

        self.undo = QAction(parent)
        self.undo.triggered.connect(self.onUndo)
        self.undo.setText("Undo")
        self.undo.setShortcut(QKeySequence.StandardKey.Undo)
        self.undo.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.undo)

        self.redo = QAction(parent)
        self.redo.triggered.connect(self.onRedo)
        self.redo.setText("Redo")
        self.redo.setShortcut(QKeySequence.StandardKey.Redo)
        self.redo.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.redo)

        self.save = QAction(parent)
        self.save.triggered.connect(self.onSave)
        self.save.setText("Save")
        self.save.setShortcut(QKeySequence.StandardKey.Save)
        self.save.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.save)

        self.open = QAction(parent)
        self.open.triggered.connect(self.onOpen)
        self.open.setText("Open")
        self.open.setShortcut(QKeySequence.StandardKey.Open)
        self.open.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.open)

        self.quit = QAction(parent)
        self.quit.triggered.connect(self.onQuit)
        self.quit.setText("Quit")
        self.quit.setShortcut(QKeySequence.StandardKey.Quit)
        self.quit.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.quit)

        self.flip = QAction(parent)
        self.flip.triggered.connect(self.onFlip)
        self.flip.setText("Flip")
        self.flip.setShortcut(QKeySequence(Qt.Key.Key_M))
        self.flip.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.flip)

        self.grayscale = QWidgetAction(parent)
        self.grayscale.setCheckable(True)
        self.grayscale.toggled.connect(self.onGrayscale)
        self.grayscale.setText("Grayscale")
        self.grayscale.setShortcut(QKeySequence(Qt.Key.Key_G))
        self.grayscale.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.grayscale)

        self.select_all = QAction(parent)
        self.select_all.triggered.connect(self.onSelectAll)
        self.select_all.setText("Select All")
        self.select_all.setShortcut(QKeySequence.StandardKey.SelectAll)
        self.select_all.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.select_all)

        self.filtering = QWidgetAction(parent)
        self.filtering.setCheckable(True)
        self.filtering.toggled.connect(self.onFiltering)
        self.filtering.setText("Filtering")
        self.filtering.setShortcut(QKeySequence(Qt.Key.Key_A))
        self.filtering.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.filtering)

        self.pack_selection = QAction(parent)
        self.pack_selection.triggered.connect(self.onPackSelection)
        self.pack_selection.setText("Pack")
        self.parent.addAction(self.pack_selection)

        self.delete_selection = QAction(parent)
        self.delete_selection.triggered.connect(self.onDeleteSelection)
        self.delete_selection.setText("Delete")
        self.delete_selection.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_selection.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.delete_selection)

        self.reset_transform = QAction(parent)
        self.reset_transform.triggered.connect(self.onResetTransform)
        self.reset_transform.setText("Reset Transform")
        self.parent.addAction(self.reset_transform)

        self.import_images = QAction(parent)
        self.import_images.triggered.connect(self.onImportImages)
        self.import_images.setText("Import Images")
        self.import_images.setShortcut(QKeySequence("CTRL+SHIFT+O"))
        self.import_images.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.import_images)

        self.export_images = QAction(parent)
        self.export_images.triggered.connect(self.onExportImages)
        self.export_images.setText("Export")
        self.parent.addAction(self.export_images)
        
        self.new = QAction(parent)
        self.new.triggered.connect(self.onNew)
        self.new.setText("New")
        self.new.setShortcut(QKeySequence.StandardKey.New)
        self.new.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.new)

        self.menu.addAction(self.undo)
        self.menu.addAction(self.redo)
        self.menu.addSeparator()
        self.menu.addAction(self.select_all)
        self.menu.addAction(self.grayscale)
        self.menu.addAction(self.filtering)
        self.menu.addSeparator()
        self.menu.addAction(self.flip)
        self.menu.addAction(self.reset_transform)
        self.menu.addAction(self.pack_selection)
        self.menu.addAction(self.export_images)
        self.menu.addSeparator()
        self.menu.addAction(self.delete_selection)
        self.menu.addSeparator()
        self.menu.addAction(self.new)
        self.menu.addAction(self.open)
        self.menu.addAction(self.import_images)
        self.menu.addSeparator()
        self.menu.addAction(self.save)
        self.menu.addSeparator()
        self.menu.addAction(self.quit)

        self.setState(False)


    def setState(self, state: bool) -> None:
        self.flip.setEnabled(state)
        self.delete_selection.setEnabled(state)
        self.reset_transform.setEnabled(state)
        self.pack_selection.setEnabled(state)
        self.export_images.setEnabled(state)


    def onSave(self) -> None:
        self.parent.save()


    def onOpen(self) -> None:
        self.parent.open()


    def onQuit(self) -> None:
        self.parent.quit()


    def onFlip(self) -> None:
        self.parent.flipSelection()


    def onGrayscale(self, state: bool) -> None:
        self.parent.setGrayscale(state)


    def onSelectAll(self) -> None:
        self.parent.selectAll()


    def onFiltering(self, state: bool) -> None:
        self.parent.setFiltering(state)


    def onPackSelection(self) -> None:
        self.parent.packSelection()


    def onDeleteSelection(self) -> None:
        self.parent.deleteSelection()


    def onUndo(self) -> None:
        system.undo_stack.undo()


    def onRedo(self) -> None:
        system.undo_stack.redo()


    def onResetTransform(self) -> None:
        self.parent.resetSelectionTransforms()


    def onImportImages(self) -> None:
        self.parent.importImages()


    def onExportImages(self) -> None:
        self.parent.exportImages()


    def onNew(self) -> None:
        self.parent.new()
