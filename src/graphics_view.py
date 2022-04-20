# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

import os
import math
import tempfile
import rpack
import shutil
import urllib.request
import time

from PIL import (Image, UnidentifiedImageError)
from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

import system
import commands
from graphics_item import GraphicsItem


class GraphicsView(QGraphicsView):

    itemMoved = pyqtSignal(list, list)

    def __init__(self, scene: QGraphicsScene, parent=None) -> None:
        super().__init__(scene, parent=parent)

        scene.selectionChanged.connect(self.onSelectionChanged)
        self._mouse_last_press_position = QPointF()
        self._mouse_last_drop_position = QPointF()

        self.transformation_mode = Qt.TransformationMode.SmoothTransformation
        self.grayscale_effect = QGraphicsColorizeEffect()
        self.grayscale_effect.setColor(0)
        self.grayscale_effect.setEnabled(False)
        self.setGraphicsEffect(self.grayscale_effect)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setStyleSheet("background-color: #100111111;")


    def load(self):
        image_data = system.sql.loadImages()
        for entry in image_data:
            item_id = entry["id"]

            item_x = entry["x"]
            item_y = entry["y"]
            item_z_value = entry["z"]
            item_rotation = entry["rotation"]
            item_scale = entry["scale"]
            item_is_flipped = entry["flip"]
            item_image = entry["image"]

            pixmap = QPixmap()
            pixmap.loadFromData(item_image)

            item = GraphicsItem(item_id, pixmap)

            item.path = entry["path"]
            item.type = entry["type"]
            item.ctime = entry["ctime"]
            item.mtime = entry["mtime"]

            item.setPos(item_x, item_y)
            item.setZValue(item_z_value)
            item.setScale(item_scale)
            item.setRotation(math.degrees(item_rotation))
            item.setTransformationMode(self.transformation_mode)
            if item_is_flipped:
                item.flip()
            self.scene().addItem(item)
            system.item_ids.append(item_id)

        view_data = system.sql.loadView()
        view_x = view_data["x"]
        view_y = view_data["y"]
        view_scale = view_data["scale"]
        view_pos = QPointF(view_x, view_y)

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
        self.updateSceneSize()
        default_scale = 1.0/self.transform().m11()
        self.scale(default_scale, default_scale)
        self.scale(view_scale, view_scale)
        self.centerOn(view_pos)


    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self._mouse_last_press_position = event.position()
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                event.accept()
                return
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                event.accept()
                return
        if event.button() == Qt.MouseButton.RightButton:
            # context menu
            return
        if event.button() == Qt.MouseButton.MiddleButton:
            self._mouse_last_press_position = event.position()
            event.accept()
            return
        super().mousePressEvent(event)


    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        super().mouseReleaseEvent(event)
        if event.button() == Qt.MouseButton.LeftButton:
            items = self.scene().selectedItems()
            if len(items) > 0:
                p1 = self.mapToScene(self._mouse_last_press_position.toPoint())
                p2 = self.mapToScene(event.position().toPoint())
                offset = p2 - p1
                if offset:
                    system.undo_stack.push(commands.Move(items, offset, True))


    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.MouseButton.LeftButton:
            if event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
                self.rotateSelection(event)
                event.accept()
                return
            if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.scaleSelection(event)
                event.accept()
                return
        if event.buttons() == Qt.MouseButton.MiddleButton:
            self.panView(event)
            event.accept()
            return
        super().mouseMoveEvent(event)


    def wheelEvent(self, event: QWheelEvent) -> None:
        self.zoomView(event)


    def dragMoveEvent(self, event: QDragMoveEvent) -> None:
        event.acceptProposedAction()


    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        mimedata = event.mimeData()
        if mimedata.hasUrls():
            event.acceptProposedAction()
        elif mimedata.hasImage():
            event.acceptProposedAction()


    def dropEvent(self, event: QDropEvent) -> None:
        mimedata = event.mimeData()
        pos = self.mapToScene(event.position().toPoint())
        self._mouse_last_drop_position = pos

        can_store = False
        if system.sql.file_path != "":
            can_store = True

        items = []
        if mimedata.hasUrls():
            urls = mimedata.urls()
            print("urls: ", urls)
            for url in urls:
                if url.isLocalFile():
                    path = url.path()
                    item = self.createItem(path, pos, can_store=can_store)
                    items.append(item)
                else:
                    s_url = url.url()
                    with urllib.request.urlopen(s_url) as response:
                        with tempfile.NamedTemporaryFile() as temp_file:
                            shutil.copyfileobj(response, temp_file)
                            path = temp_file.name
                            item = self.createItem(path, pos, url=s_url, can_store=can_store)
                            items.append(item)
        elif mimedata.hasImage():
            print("image: ")

        if len(items) > 1:
            self.scene().clearSelection()
            for item in items:
                item.setSelected(True)
            self.packSelection()


    def createItem(self, path: str, pos: QPointF, is_flipped=False, scale=1.0, z_value=0, url="", can_store=False) -> GraphicsItem:
        file_type = None
        try:
            img = Image.open(path)
            file_type = img.format
        except UnidentifiedImageError:
            return None

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

        new_id = system.getItemID()

        item = GraphicsItem(new_id, QPixmap(path))

        item.path = basename
        item.mtime = os.path.getmtime(path)
        item.ctime = time.time()

        item.type = file_type
        item.setPos(pos)
        item.setScale(scale)
        item.setZValue(z_value)
        item.setTransformationMode(self.transformation_mode)

        if is_flipped:
            item.flip()

        self.scene().addItem(item)
        center = item.boundingRect().center()
        item.setPos(item.pos() - center)

        if can_store:
            system.sql.storeItem(item)

        return item


    def panView(self, event: QMouseEvent) -> None:
        if not len(self.scene().items()) > 0:
            return

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.updateSceneSize()
        old_pos = self.mapToScene(self._mouse_last_press_position.toPoint())
        new_pos = self.mapToScene(event.position().toPoint())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        self._mouse_last_press_position = event.position()


    def zoomView(self, event: QWheelEvent) -> None:
        if not len(self.scene().items()) > 0:
            return

        scale_max = 500.0
        scale_min = 0.005
        scale_in_factor = 1.2
        scale_out_factor = 1.0 / scale_in_factor
        scale = self.transform().m11()

        self.updateSceneSize()
        pos = event.position().toPoint()
        old_pos = self.mapToScene(pos)
        angle = event.angleDelta().y()
        factor: float
        if angle > 0.0:
            factor = scale_in_factor
            if scale * factor > scale_max:
                return
        else:
            factor = scale_out_factor
            if scale * factor < scale_min:
                return

        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)
        self.scale(factor, factor)
        new_pos = self.mapToScene(pos)
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())


    def packSelection(self) -> None:
        items = self.scene().selectedItems()
        group = self.scene().createItemGroup(items)
        rect_sizes = []

        for item in items:
            scale = item.scale()
            width = int(item.boundingRect().width() * scale)
            height = int(item.boundingRect().height() * scale)
            rect = (width, height)
            rect_sizes.append(rect)

        bounding_rect = group.boundingRect()
        origin = bounding_rect.topLeft()

        packed_positions = rpack.pack(sizes=rect_sizes)

        for i in range(0, len(items)):
            item = items[i]
            x, y = packed_positions[i]
            pos = origin + QPointF(x, y)
            item.setPos(pos)

        self.scene().destroyItemGroup(group)


    def contextMenuEvent(self, event: QContextMenuEvent) -> None:
        pos = self.mapToGlobal(event.pos())
        system.actions.menu.popup(pos)
        event.accept()


    def updateSceneSize(self) -> None:
        # bypass scrollbar scene size restrictions
        pad = 16000
        widget_rect_in_scene = QRectF(self.mapToScene(-pad, -pad), self.mapToScene(self.rect().bottomRight() + QPoint(pad, pad)))
        new_top_left = QPointF(self.sceneRect().topLeft())
        new_bottom_right = QPointF(self.sceneRect().bottomRight())

        if self.sceneRect().top() > widget_rect_in_scene.top():
            new_top_left.setY(widget_rect_in_scene.top())

        if self.sceneRect().bottom() < widget_rect_in_scene.bottom():
            new_bottom_right.setY(widget_rect_in_scene.bottom())

        if self.sceneRect().left() > widget_rect_in_scene.left():
            new_top_left.setX(widget_rect_in_scene.left())

        if self.sceneRect().right() < widget_rect_in_scene.right():
            new_bottom_right.setX(widget_rect_in_scene.right())

        self.setSceneRect(QRectF(new_top_left, new_bottom_right))


    def onSelectionChanged(self) -> None:
        selected_items = self.scene().selectedItems()
        if len(selected_items) > 0:
            system.actions.setState(True)
        else:
            system.actions.setState(False)


    def rotateSelection(self, event: QMouseEvent) -> None:
        items = self.scene().selectedItems()
        if not len(items) > 0:
            return

        group = self.scene().createItemGroup(items)
        center = group.boundingRect().center()
        group.setTransformOriginPoint(center)

        event_pos = self.mapToScene(event.position().toPoint())
        mid_pos = group.mapToScene(center)
        offset_pos = self.mapToScene(self._mouse_last_press_position.toPoint())

        dx = event_pos - mid_pos
        ax = math.atan2(dx.y(), dx.x())
        dy = offset_pos - mid_pos
        ay = math.atan2(dy.y(), dy.x())
        rotation = math.degrees(ax - ay)

        group.setRotation(group.rotation() + rotation)

        self.scene().destroyItemGroup(group)
        self._mouse_last_press_position = event.position()


    def scaleSelection(self, event: QMouseEvent) -> None:
        items = self.scene().selectedItems()
        if not len(items) > 0:
            return

        # todo: get correct transform scale
        # group = self.scene().createItemGroup(items)
        # center = group.boundingRect().center()
        # group.setTransformOriginPoint(center)

        event_pos = self.mapToScene(event.position().toPoint())
        offset_pos = self.mapToScene(self._mouse_last_press_position.toPoint())
        factor = 0.0005
        scale = (event_pos - offset_pos).x() * factor

        for item in items:
            item_center = item.boundingRect().center()
            # item.setTransformOriginPoint(item_center)
            item.setScale(item.scale() + scale)

        # group.setScale(group.scale() + scale)
        # self.scene().destroyItemGroup(group)
        self._mouse_last_press_position = event.position()
