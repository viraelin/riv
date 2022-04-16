# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

import system
from graphics_item import GraphicsItem


class Move(QUndoCommand):

    def __init__(self, items: list[GraphicsItem], offset: QPointF, skip=False, parent=None) -> None:
        super().__init__(parent=parent)
        self.items = items
        self.offset = offset
        self.skip = skip


    def undo(self) -> None:
        x = self.offset.x()
        y = self.offset.y()
        for item in self.items:
            item.moveBy(-x, -y)


    def redo(self) -> None:
        if self.skip:
            self.skip = False
            return
        x = self.offset.x()
        y = self.offset.y()
        for item in self.items:
            item.moveBy(x, y)
