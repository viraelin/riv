# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

import os
import sqlite3
import math

import tempfile
import rpack
import shutil
import urllib.request
import time

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

import system
from graphics_view import GraphicsView
from graphics_item import GraphicsItem


class Database:

    def __init__(self) -> None:
        self.file_path = ""


    def createDatabase(self) -> None:
        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS
        view(
            id INTEGER PRIMARY KEY,
            x INTEGER,
            y INTEGER,
            scale REAL
            )""")
        cursor.execute("INSERT OR IGNORE INTO view VALUES (?, ?, ?, ?)",
            [0, 0, 0, 1.0])
        cursor.execute("""CREATE TABLE IF NOT EXISTS
        images(
            id INTEGER PRIMARY KEY,
            path TEXT,
            type TEXT,
            ctime REAL,
            mtime REAL,
            x INTEGER,
            y INTEGER,
            z INTEGER,
            rotation REAL,
            scale REAL,
            flip BOOL,
            image BLOB
            )""")
        connection.commit()


    def loadView(self) -> dict:
        connection = sqlite3.connect(self.file_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM view WHERE id == 0")
        data = cursor.fetchall()[0]
        return data


    def loadImages(self) -> list[dict]:
        connection = sqlite3.connect(self.file_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM images")
        data = cursor.fetchall()
        return data


    def updateView(self, view: QGraphicsView) -> None:
        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()

        view_scale = view.transform().m11()
        view_pos = view.mapToScene(view.rect().center())
        view_x = int(view_pos.x())
        view_y = int(view_pos.y())
        cursor.execute("UPDATE view SET x = ? WHERE id == 0", [view_x])
        cursor.execute("UPDATE view SET y = ? WHERE id == 0", [view_y])
        cursor.execute("UPDATE view SET scale = ? WHERE id == 0", [view_scale])

        connection.commit()


    def updateItems(self, items: list[GraphicsItem]) -> None:
        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()

        for item in items:
            x = int(item.pos().x())
            y = int(item.pos().y())
            z = item.zValue()
            scale = item.scale()
            flip = item.is_flipped
            rotation = item.getRotation()

            cursor.execute("UPDATE images SET path = ? where id == ?", [item.path, item.id])
            cursor.execute("UPDATE images SET type = ? where id == ?", [item.type, item.id])
            cursor.execute("UPDATE images SET ctime = ? where id == ?", [item.ctime, item.id])
            cursor.execute("UPDATE images SET mtime = ? where id == ?", [item.mtime, item.id])

            cursor.execute("UPDATE images SET x = ? WHERE id == ?", [x, item.id])
            cursor.execute("UPDATE images SET y = ? WHERE id == ?", [y, item.id])
            cursor.execute("UPDATE images SET z = ? WHERE id == ?", [z, item.id])
            cursor.execute("UPDATE images SET rotation = ? WHERE id == ?", [rotation, item.id])
            cursor.execute("UPDATE images SET scale = ? WHERE id == ?", [scale, item.id])
            cursor.execute("UPDATE images SET flip = ? WHERE id == ?", [flip, item.id])

        connection.commit()
        cursor.execute("VACUUM")


    def storeItem(self, item: GraphicsItem) -> None:
        if self.file_path == "":
            return

        # todo
        image: bytes = None
        with open(item.source_path, "rb") as fp:
            image = fp.read()

        assert(image)

        x = int(item.pos().x())
        y = int(item.pos().y())
        z = item.zValue()
        scale = item.scale()
        flip = item.is_flipped
        rotation = item.getRotation()

        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [item.id, item.path, item.type, item.ctime, item.mtime, x, y, z, rotation, scale, flip, image])
        connection.commit()


    def deleteItem(self, item: GraphicsItem) -> None:
        if self.file_path == "":
            return

        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM images WHERE id == ?", [item.id])
        connection.commit()


    def getImage(self, item: GraphicsItem) -> bytes:
        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()
        cursor.execute("SELECT image FROM images WHERE id == ?", [item.id])
        data = cursor.fetchall()[0][0]
        return data


class ItemLoadWorker(QObject):

    finished = pyqtSignal(int)
    progress = pyqtSignal(GraphicsItem, int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.view: GraphicsView = None


    def run(self) -> None:
        image_data = system.sql.loadImages()
        total = len(image_data)

        i = 1
        for entry in image_data:
            x = entry["x"]
            y = entry["y"]
            pos = QPointF(x, y)

            item = GraphicsItem(pos=pos, drop=False, **entry)
            self.progress.emit(item, i, total)
            i += 1
        
        self.finished.emit(0)


class ItemDropWorker(QObject):

    finished = pyqtSignal(int, list)
    progress = pyqtSignal(GraphicsItem, int, int)

    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.view: GraphicsView = None
        self.urls: list[QUrl] = None
        self.pos: QPointF = None


    def run(self) -> None:
        urls = self.urls
        pos = self.pos

        items = []
        total = len(urls)

        i = 1
        for url in urls:
            if url.isLocalFile():
                path = url.path()
                item = self.view.addItem(path=path, pos=pos)
                items.append(item)
                self.progress.emit(item, i, total)
                i += 1
            else:
                s_url = url.url()
                with urllib.request.urlopen(s_url) as response:
                    with tempfile.NamedTemporaryFile() as temp_file:
                        shutil.copyfileobj(response, temp_file)
                        path = temp_file.name
                        item = self.view.addItem(path=path, pos=pos, url=url)
                        items.append(item)
                        self.progress.emit(item, i, total)
                        i += 1

        self.finished.emit(0, items)
