from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMenu
from PyQt6.QtGui import QAction, QKeySequence


class Actions:

    def __init__(self, parent) -> None:
        self.parent = parent
        self.menu = QMenu(parent)

        self.project_save = QAction(parent)
        self.project_save.triggered.connect(self.onProjectSave)
        self.project_save.setText("Save")
        self.project_save.setShortcut(QKeySequence.StandardKey.Save)
        self.project_save.setShortcutContext(Qt.ShortcutContext.ApplicationShortcut)
        self.parent.addAction(self.project_save)

        self.menu.addAction(self.project_save)


    def onProjectSave(self) -> None:
        self.parent.projectSave()
