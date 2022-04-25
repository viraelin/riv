# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

import os
import math
import time
import tempfile

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

import system


class GraphicsItem(QGraphicsPixmapItem):

    def __init__(self, **kwargs: dict) -> None:
        super().__init__()

        item_id = kwargs.get("id")
        path = kwargs.get("path")
        url = kwargs.get("url", "")
        pos = kwargs.get("pos", QPointF())
        scale = kwargs.get("scale", 1.0)
        z_value = kwargs.get("z", 0)
        is_flipped = kwargs.get("flip", False)
        is_drop = kwargs.get("drop", True)
        file_type = kwargs.get("type")
        rotation = kwargs.get("rotation", 0.0)
        ctime = kwargs.get("ctime")
        mtime = kwargs.get("mtime")

        basename = os.path.basename(path)
        if url != "":
            basename = os.path.basename(url)
        name, ext = os.path.splitext(basename)
        ext_changed = False
        if ext == "":
            ext = "." + file_type.lower()
            if ext == ".jpeg":
                ext = ".jpg"
            ext_changed = True
        if name == ext:
            with tempfile.NamedTemporaryFile() as temp_file:
                basename = os.path.basename(temp_file.name)
        if ext_changed:
            basename += ext

        if item_id:
            system.item_ids.append(item_id)
        else:
            item_id = system.getItemID()

        if is_drop:
            pixmap = QPixmap(path)
            ctime = time.time()
            mtime = os.path.getmtime(path)
        else:
            image = kwargs.get("image")
            pixmap = QPixmap()
            pixmap.loadFromData(image)

        self.id = item_id
        self.path = basename
        self.source_path = path
        self.ctime = ctime
        self.mtime = mtime
        self.type = file_type

        self.setPixmap(pixmap)
        self.setPos(pos)
        self.setScale(scale)
        self.setRotation(math.degrees(rotation))
        self.setZValue(z_value)

        self.is_flipped = False
        if is_flipped:
            self.flip()

        if is_drop:
            center = self.boundingRect().center()
            self.setPos(self.pos() - center)

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
