# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

import math

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *


class GraphicsItem(QGraphicsPixmapItem):

    def __init__(self, id_: int, pixmap: QPixmap, parent=None) -> None:
        super().__init__(pixmap, parent=parent)
        self.id = id_
        self.path = None
        self.type = None
        self.is_flipped = False
        self.is_deleted = False
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges, True)
        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.BoundingRectShape)


    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value: any) -> any:
        if self.scene():
            if change == QGraphicsItem.GraphicsItemChange.ItemSelectedHasChanged:
                self.sendToFront()
            elif change == QGraphicsItem.GraphicsItemChange.ItemPositionHasChanged:
                self.sendToFront()
        return super().itemChange(change, value)


    def flip(self) -> None:
        mirror = self.pixmap().transformed(QTransform().scale(-1, 1))
        self.setPixmap(mirror)
        self.is_flipped = not self.is_flipped


    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget) -> None:
        width = 1
        color = QColor(Qt.GlobalColor.black)

        if self.isSelected():
            # override selection border
            option.state = QStyle.StateFlag.State_None
            super().paint(painter, option, widget)
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


    def getRotation(self) -> float:
        t = self.sceneTransform()
        return math.atan2(t.m12(), t.m11())


    def sendToFront(self) -> None:
        max_z = 0
        colliding_items = self.collidingItems(Qt.ItemSelectionMode.IntersectsItemBoundingRect)
        for colliding_item in colliding_items:
            max_z = max(max_z, colliding_item.zValue())
        self.setZValue(max_z + 1)
