from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction, QKeySequence


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

        self.flip = QAction(parent)
        self.flip.triggered.connect(self.onFlip)
        self.flip.setText("Flip Selection")
        self.flip.setShortcut(QKeySequence(Qt.Key.Key_M))
        self.flip.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.flip.setEnabled(False)
        self.parent.addAction(self.flip)

        self.menu.addAction(self.flip)
        self.menu.addSeparator()
        self.menu.addAction(self.save)
        self.menu.addAction(self.open)


    def onSave(self) -> None:
        self.parent.save()


    def onOpen(self) -> None:
        self.parent.open()


    def onFlip(self) -> None:
        self.parent.flipSelection()
