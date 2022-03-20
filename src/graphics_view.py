# Copyright (C) 2020 viraelin
# License: GPLv3.0-or-later

import os
import json
import zipfile
import tempfile
import shutil
from enum import (Enum, unique)

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtNetwork import *

from graphics_item import (GraphicsItem, GraphicsItemData)


@unique
class GraphicsViewState(Enum):
    Default = 0
    Pan = 1
    Resize = 2


class GraphicsView(QGraphicsView):

    itemMoved = pyqtSignal(list, list)

    def __init__(self, scene: QGraphicsScene, parent=None) -> None:
        super().__init__(scene, parent=parent)
        self.progress_bar = QProgressBar(self)
        self.effect = QGraphicsColorizeEffect(self)
        self.image_layer = QGraphicsRectItem()

        self.current_project_path = ""
        self.project_filter = "RIV (*.riv)"
        self.default_project_name = "untitled.riv"
        self.moving_items = []
        self.moving_items_old_positions = []
        self.transformation_mode = Qt.TransformationMode.SmoothTransformation

        self._state = GraphicsViewState.Default
        self._resize_origin = QPointF()
        self._mouse_last_resize_position = QPointF()
        self._mouse_last_pan_position = QPointF()
        self._mouse_last_drop_position = QPointF()
        self._network_manager = QNetworkAccessManager(self)

        self._network_manager.finished.connect(self.onNetworkReplyFinished)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setStyleSheet("background-color: #100111111;")
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.NoAnchor)

        self.progress_bar.reset()
        self.progress_bar.setMinimum(0)
        self.progress_bar.hide()

        self.pen = QPen()
        self.pen.setStyle(Qt.PenStyle.NoPen)
        self.brush = QBrush(QColor("#222222"))
        self.brush.setStyle(Qt.BrushStyle.SolidPattern)
        self.bounding_rect_item = scene.addRect(QRectF(), self.pen, self.brush)
        self.bounding_rect_item.setZValue(-100)

        self.effect.setColor(QColor(0, 0, 0))
        self.effect.setEnabled(False)
        self.setGraphicsEffect(self.effect)

        scene.addItem(self.image_layer)


    def projectSave(self) -> None:
        if not self.parentWidget().isWindowModified():
            return

        project_path = self.current_project_path
        if not project_path:
            path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
            file_name, ok = QFileDialog().getSaveFileName(
                self.parentWidget(),
                "Save Project",
                QDir(path).filePath(self.default_project_name),
                self.project_filter
            )

            if file_name and ok:
                project_path = file_name
            else:
                return

        # todo: error handling
        ok, save_file = tempfile.mkstemp()
        with zipfile.ZipFile(save_file, "w", zipfile.ZIP_STORED) as zf:
            items = self.image_layer.childItems()
            view_position = self.mapToScene(self.rect().center())
            version = 100
            zoom = self.transform().m11()

            data = {
                "version": version,
                "viewPosX": view_position.x(),
                "viewPosY": view_position.y(),
                "zoom": zoom,
                "items": [],
            }

            item_count = len(items)
            self.showProgressBar(item_count)

            # save items
            for i in range(0, item_count):
                item = items[i]
                pixmap = item.pixmap()
                path = item.data(GraphicsItemData.ItemPath.value)
                is_flipped = item.data(GraphicsItemData.ItemIsFlipped.value)
                # if zoomed in really far narrowing could matter
                position = item.pos().toPoint()
                scale = item.sceneTransform().m11()
                z_value = item.zValue()

                if item.data(GraphicsItemData.ItemIsDeleted.value):
                    del item
                    continue

                path_base = os.path.basename(path)
                item_data = {
                    "path": path_base,
                    "flipped": is_flipped,
                    "posX": position.x(),
                    "posY": position.y(),
                    "scale": scale,
                    "zValue": z_value,
                }
                data["items"].append(item_data)

                if path_base == path:
                    # hack: also in loop, not ideal
                    with zipfile.ZipFile(project_path, "r", zipfile.ZIP_STORED) as zf_old:
                        old_path = zf_old.read(path_base)
                        zf.writestr(path_base, old_path)
                else:
                    zf.write(path, path_base)

                self.progress_bar.setValue(i * 100)
                QApplication.processEvents()

            data_file_name = "data.json"
            with open(data_file_name, "w") as fp:
                json.dump(data, fp)

            zf.write(data_file_name)

            self.progress_bar.hide()
            self.current_project_path = project_path

        # can't move file inside of with
        if save_file and ok:
            shutil.move(save_file, project_path)


    def projectLoad(self, project_path="") -> None:
        if not project_path:
            project_path = self.current_project_path

        if not os.path.exists(project_path):
            return

        with zipfile.ZipFile(project_path, "r") as zf:
            data_file_name = "data.json"

            fp = zf.read(data_file_name)
            data = json.loads(fp)
            assert(data)

            version = data["version"]
            view_position = QPointF(data["viewPosX"], data["viewPosY"])
            zoom = data["zoom"]

            # todo
            if version != 100:
                return

            items = data["items"]
            item_count = len(items)

            self.clearCanvas()
            self.showProgressBar(item_count)

            default_scale = 1.0/self.transform().m11()
            self.scale(default_scale, default_scale)
            self.scale(zoom, zoom)

            for i in range(0, item_count):
                item = items[i]
                path = item["path"]

                if not path:
                    continue

                try:
                    pixmap_data = zf.read(path)
                except KeyError:
                    continue

                pixmap = QPixmap()
                pixmap.loadFromData(pixmap_data)
                is_flipped = item["flipped"]
                position = QPointF(item["posX"], item["posY"])
                scale = item["scale"]
                z_value = item["zValue"]

                # todo: merge with createItem or args for GraphicsItem
                item = GraphicsItem(pixmap)
                item.setData(GraphicsItemData.ItemPath.value, path)
                item.setData(GraphicsItemData.ItemIsFlipped.value, False)
                item.setData(GraphicsItemData.ItemIsDeleted.value, False)
                item.setPos(position)
                item.setScale(scale)
                item.setZValue(z_value)
                item.setTransformationMode(self.transformation_mode)

                if is_flipped:
                    item.flip()

                item.setParentItem(self.image_layer)

                self.progress_bar.setValue(i * 100)
                QApplication.processEvents()

            self.setBoundingRect()
            self.centerOn(view_position)

            self.current_project_path = project_path
            self.progress_bar.hide()

            info = QFileInfo(project_path)
            self.parentWidget().setWindowTitle(info.fileName() + "[*]")


    def mousePressEvent(self, event: QMouseEvent) -> None:
        if self._state == GraphicsViewState.Default:
            if event.button() == Qt.MouseButton.LeftButton:
                super().mousePressEvent(event)
                self.moving_items = self.scene().selectedItems()
                if len(self.moving_items) > 0:
                    for item in self.moving_items:
                        self.sendToFront(item)
                        self.moving_items_old_positions.append(item.pos())
            elif event.button() == Qt.MouseButton.MiddleButton:
                self._mouse_last_pan_position = event.position()
                self.setState(GraphicsViewState.Pan)
        elif self._state == GraphicsViewState.Pan:
            if event.button() == Qt.MouseButton.LeftButton:
                self._mouse_last_pan_position = event.position()
            elif event.button() == Qt.MouseButton.MiddleButton:
                self._mouse_last_pan_position = event.position()
        elif self._state == GraphicsViewState.Resize:
            if event.button() == Qt.MouseButton.LeftButton:
                self._mouse_last_resize_position = event.position()
                items = self.scene().selectedItems()
                group = self.scene().createItemGroup(items)
                self._resize_origin = group.childrenBoundingRect().center()
                self.scene().destroyItemGroup(group)
                self.setItemParents(items)


    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if self._state == GraphicsViewState.Default:
            if event.button() == Qt.MouseButton.LeftButton:
                super().mouseReleaseEvent(event)
                if len(self.moving_items) > 0:
                    self.itemMoved.emit(self.moving_items, self.moving_items_old_positions)
                    self.moving_items.clear()
                    self.moving_items_old_positions.clear()
                self.setBoundingRect()
        elif self._state == GraphicsViewState.Pan:
            if event.button() == Qt.MouseButton.LeftButton:
                self.setCursor(Qt.CursorShape.OpenHandCursor)
            elif event.button() == Qt.MouseButton.MiddleButton:
                self.setState(GraphicsViewState.Default)


    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if self._state == GraphicsViewState.Default:
            super().mouseMoveEvent(event)
            if len(self.moving_items) > 0:
                for item in self.moving_items:
                    self.sendToFront(item)
        elif self._state == GraphicsViewState.Pan:
            if (event.buttons() == Qt.MouseButton.LeftButton):
                self.panView(event)
            elif (event.buttons() == Qt.MouseButton.MiddleButton):
                self.panView(event)
        elif self._state == GraphicsViewState.Resize:
            if event.buttons() == Qt.MouseButton.LeftButton:
                self.resizeSelection(event)


    def keyPressEvent(self, event: QKeyEvent) -> None:
        if self._state == GraphicsViewState.Default:
            if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
                self.setState(GraphicsViewState.Pan)
            elif event.key() == Qt.Key.Key_Control and not event.isAutoRepeat():
                self.setState(GraphicsViewState.Resize)


    def keyReleaseEvent(self, event: QKeyEvent) -> None:
        if self._state == GraphicsViewState.Pan:
            if event.key() == Qt.Key.Key_Space and not event.isAutoRepeat():
                self.setState(GraphicsViewState.Default)
        elif self._state == GraphicsViewState.Resize:
            if event.key() == Qt.Key.Key_Control and not event.isAutoRepeat():
                self.setState(GraphicsViewState.Default)


    def wheelEvent(self, event: QWheelEvent) -> None:
        self.zoomView(event)


    # required
    def dragMoveEvent(self, _event: QDragMoveEvent) -> None:
        return


    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        event.accept()


    def dropEvent(self, event: QDropEvent) -> None:
        self._mouse_last_drop_position = self.mapToScene(event.position().toPoint())
        urls = event.mimeData().urls()
        paths = []

        # todo: drag and drop and network usage has changed
        for url in urls:
            path = url.toLocalFile()
            if self.checkMimeData(path):
                paths.append(path)
            else:
                request = QNetworkRequest(url)
                reply = self._network_manager.get(request)
                reply.downloadProgress.connect(self.onNetworkReplyProgress)

        if len(paths) > 0:
            self.createItems(paths, self._mouse_last_drop_position)


    def setBoundingRect(self) -> None:
        self.updateSceneSize()
        new_rect = self.image_layer.childrenBoundingRect()
        self.bounding_rect_item.setRect(new_rect)


    def createItem(self, path: str, pos: QPointF, is_flipped=False, scale=1.0, z_value=0) -> GraphicsItem:
        item = GraphicsItem(QPixmap(path))
        item.setData(GraphicsItemData.ItemPath.value, path)
        item.setData(GraphicsItemData.ItemIsFlipped.value, False)
        item.setData(GraphicsItemData.ItemIsDeleted.value, False)
        item.setPos(pos)
        item.setScale(scale)
        item.setZValue(z_value)
        item.setTransformationMode(self.transformation_mode)

        if is_flipped:
            item.flip()

        item.setParentItem(self.image_layer)
        self.update()
        return item


    def createItems(self, paths: list, origin: QPointF) -> None:
        self.scene().clearSelection()
        item_count = len(paths)
        self.showProgressBar(item_count)

        for i in range(0, item_count):
            path = paths[i]
            item = self.createItem(path, origin)
            item.setSelected(True)
            self.progress_bar.setValue(i * 100)
            QApplication.processEvents()

        self.progress_bar.hide()
        self.packSelection(origin)


    def checkMimeData(self, path: str) -> bool:
        mimetype = QMimeDatabase().mimeTypeForFile(path)
        if mimetype.name().startswith("image"):
            return True
        return False


    def onNetworkReplyProgress(self, bytes_received: int, bytes_total: int) -> None:
        percent = float(bytes_received) / float(bytes_total)
        value = (percent * 100.0) * 100
        count = 10000
        self.showProgressBar(count)
        self.progress_bar.setValue(value)


    def onNetworkReplyFinished(self, reply: QNetworkReply) -> None:
        # some requests fail: no redirect, no error
        self.progress_bar.hide()
        temp = QDir.temp().filePath("XXXXXXXX-" + reply.url().fileName())
        file = QTemporaryFile(temp)

        if file.open():
            file_name = file.fileName()
            file.write(reply.readAll())
            file.close()

            if checkMimeData(file_name):
                self.createItem(file_name, self._mouse_last_drop_position)


    def panView(self, event: QMouseEvent) -> None:
        self.updateSceneSize()
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        old_pos = self.mapToScene(self._mouse_last_pan_position.toPoint())
        new_pos = self.mapToScene(event.position().toPoint())
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        self._mouse_last_pan_position = event.position()


    def zoomView(self, event: QWheelEvent) -> None:
        self.updateSceneSize()
        pos = event.position().toPoint()
        old_pos = self.mapToScene(pos)
        angle = event.angleDelta().y()
        factor: float
        zoom_in_factor = 1.2
        zoom_out_factor = 1.0 / zoom_in_factor
        if angle > 0.0:
            factor = zoom_in_factor
        else:
            factor = zoom_out_factor
        self.scale(factor, factor)
        new_pos = self.mapToScene(pos)
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())
        self.setBoundingRect()


    def resizeSelection(self, event: QMouseEvent) -> None:
        items = self.scene().selectedItems()
        if len(items) > 0:
            group = self.scene().createItemGroup(items)

            epos = event.position()
            delta = self._mouse_last_resize_position - epos

            n = -delta.x()
            sign = (n > 0) - (n < 0)

            scene_scale = 1.0/self.transform().m11()
            zoom_scale = 0.001 * sign

            current_scale = group.scale()
            scale = current_scale + (delta.manhattanLength() * scene_scale) * zoom_scale
            scale = max(scale, 0.01 * scene_scale)
            group.setTransformOriginPoint(self._resize_origin)
            group.setScale(scale)
            self._mouse_last_resize_position = epos
            self.scene().destroyItemGroup(group)
            self.setItemParents(items)


    def setState(self, s: GraphicsViewState) -> None:
        if s == self._state:
            return

        if s == GraphicsViewState.Default:
            self.setCursor(Qt.CursorShape.ArrowCursor)
            self.setDragMode(self.DragMode.RubberBandDrag)

        elif s == GraphicsViewState.Pan:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
            self.setDragMode(self.DragMode.NoDrag)

        elif s == GraphicsViewState.Resize:
            self.setCursor(Qt.CursorShape.SizeHorCursor)
            self.setDragMode(self.DragMode.NoDrag)

        self._state = s


    def setItemParents(self, items: list) -> None:
        # hack to try to prevent loss when switching item group
        # use plain rect item as parent because still allows canvas interaction
        for item in items:
            item.setParentItem(self.image_layer)


    def packSelection(self, origin: QPointF) -> None:
        # simple row packing
        items = self.scene().selectedItems()

        area = 0.0
        max_width = 0.0

        for item in items:
            scale = item.sceneTransform().m11()
            area += (item.pixmap().width() * scale) * (item.pixmap().height() * scale)
            max_width = max(max_width, item.pixmap().width() * scale)

        max_width *= 2.0

        def sortByHeight(a: GraphicsItem, b: GraphicsItem) -> bool:
            _as = a.sceneTransform().m11()
            _bs = b.sceneTransform().m11()
            return (a.pixmap().height() * _as) > (b.pixmap().height() * _bs)

        items = sorted(items, key=lambda i: i.sceneTransform().m11() * i.pixmap().height())

        x = 0
        y = 0
        largest_height_this_row = 0

        for item in items:
            pixmap = item.pixmap()
            scale = item.sceneTransform().m11()
            width = pixmap.width() * scale
            height = pixmap.height() * scale

            # if outside max width, start new row
            if (x + height) > max_width:
                x = 0
                y += largest_height_this_row
                largest_height_this_row = 0

            # adjusted position
            p = QPointF(origin.x() + (x - max_width), origin.y() + (y - max_width))
            item.setPos(p)

            x += width

            if height > largest_height_this_row:
                largest_height_this_row = height


    def showProgressBar(self, item_count: int) -> None:
        if item_count > 0:
            # set progress bar to center
            # geometry is only correct if window is shown
            geometry_view = self.geometry()
            geometry_progress_bar = self.progress_bar.geometry()
            geometry_progress_bar.moveCenter(geometry_view.center())
            self.progress_bar.setGeometry(geometry_progress_bar)
            self.progress_bar.reset()
            self.progress_bar.show()
            self.progress_bar.setMaximum((item_count * 100) - 100)


    def selectAll(self) -> None:
        items = self.image_layer.childItems()
        for item in items:
            item.setSelected(True)


    def clearCanvas(self) -> None:
        current_items = self.image_layer.childItems()
        for item in current_items:
            self.scene().removeItem(item)
            del item


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


    def sendToFront(self, item: GraphicsItem) -> None:
        max_z = 0
        colliding_items = item.collidingItems(Qt.ItemSelectionMode.IntersectsItemBoundingRect)
        for colliding_item in colliding_items:
            if colliding_item == self.bounding_rect_item:
                continue
            max_z = max(max_z, colliding_item.zValue())
        item.setZValue(max_z + 1)
