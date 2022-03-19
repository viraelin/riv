# Copyright (C) 2020 viraelin
# License: GPLv3.0-or-later

from enum import (Enum, unique)

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *


@unique
class GraphicsItemData(Enum):
    ItemPath = Qt.ItemDataRole.UserRole+1
    ItemIsFlipped = Qt.ItemDataRole.UserRole+2
    ItemIsDeleted = Qt.ItemDataRole.UserRole+3


class GraphicsItem(QGraphicsPixmapItem):

    def __init__(self, pixmap: QPixmap, parent=None) -> None:
        super().__init__(pixmap, parent=parent)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)


    def flip(self) -> None:
        mirror = self.pixmap().transformed(QTransform().scale(-1, 1))
        self.setPixmap(mirror)
        state = not self.data(GraphicsItemData.ItemIsFlipped.value)
        self.setData(GraphicsItemData.ItemIsFlipped.value, state)


    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        width = 1
        color = QColor(Qt.GlobalColor.black)

        if self.isSelected():
            # override selection border
            custom_option = QStyleOptionGraphicsItem(option)
            custom_option.state = QStyle.StateFlag.State_None
            super().paint(painter, custom_option, widget)
            width = 2
            color = QColor("#33CCCC")
        else:
            super().paint(painter, option, widget)

        rect = self.boundingRect()
        pen = QPen()
        pen.setWidth(width)
        pen.setCosmetic(True)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        pen.setColor(color)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(pen)
        painter.drawRect(rect)
