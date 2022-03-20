# Copyright (C) 2020 viraelin
# License: GPLv3.0-or-later

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from graphics_item import (GraphicsItem, GraphicsItemData)


class MoveCommand(QUndoCommand):

    def __init__(self, item_list: list, old_positions: list, parent=None) -> None:
        super().__init__(parent=parent)
        self.items = item_list
        self.old_positions = old_positions
        self.new_positions = []
        for item in self.items:
            self.new_positions.append(item.pos())


    def undo(self) -> None:
        for i in range(0, len(self.items)):
            item = self.items[i]
            old_position = self.old_positions[i]
            item.setPos(old_position)


    def redo(self) -> None:
        for i in range(0, len(self.items)):
            item = self.items[i]
            new_position = self.new_positions[i]
            item.setPos(new_position)


class DeleteCommand(QUndoCommand):

    def __init__(self, view: QGraphicsView, parent=None) -> None:
        super().__init__(parent=parent)
        self.view = view
        self.scene = view.scene()
        self.items = self.scene.selectedItems()
        for item in self.items:
            item.setData(GraphicsItemData.ItemIsDeleted.value, True)
            item.setSelected(True)
            item.hide()


    def undo(self) -> None:
        for item in self.items:
            item.setData(GraphicsItemData.ItemIsDeleted.value, False)
            item.show()
            item.setParentItem(self.view.image_layer)


    def redo(self) -> None:
        for item in self.items:
            item.setData(GraphicsItemData.ItemIsDeleted.value, True)
            item.hide()


class FlipCommand(QUndoCommand):

    def __init__(self, item_list: list, parent=None) -> None:
        super().__init__(parent=parent)
        self.items = item_list


    def undo(self) -> None:
        self.flip()


    def redo(self) -> None:
        self.flip()


    def flip(self) -> None:
        for item in self.items:
            item.flip()

