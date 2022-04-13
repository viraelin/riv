# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (QMenu, QWidgetAction)
from PyQt6.QtGui import (QAction, QKeySequence)


class Actions:

    def __init__(self, parent) -> None:
        self.parent = parent
        self.menu = QMenu(parent)

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
        self.flip.setText("Flip Selection")
        self.flip.setShortcut(QKeySequence(Qt.Key.Key_M))
        self.flip.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.flip.setEnabled(False)
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
        self.parent.addAction(self.filtering)

        self.pack_selection = QAction(parent)
        self.pack_selection.triggered.connect(self.onPackSelection)
        self.pack_selection.setText("Pack Selection")
        self.parent.addAction(self.pack_selection)

        self.delete_selection = QAction(parent)
        self.delete_selection.triggered.connect(self.onDeleteSelection)
        self.delete_selection.setText("Delete")
        self.delete_selection.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_selection.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.delete_selection)

        self.menu.addAction(self.flip)
        self.menu.addAction(self.grayscale)
        self.menu.addAction(self.select_all)
        self.menu.addAction(self.filtering)
        self.menu.addAction(self.pack_selection)
        self.menu.addSeparator()
        self.menu.addAction(self.delete_selection)
        self.menu.addSeparator()
        self.menu.addAction(self.save)
        self.menu.addAction(self.open)
        self.menu.addSeparator()
        self.menu.addAction(self.quit)


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
