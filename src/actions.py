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

        self.menu.addAction(self.save)


    def onSave(self) -> None:
        self.parent.save()
