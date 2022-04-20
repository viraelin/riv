# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

import os
import tempfile
import sqlite3

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

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
            path STRING,
            x INTEGER,
            y INTEGER,
            z INTEGER,
            rotation REAL,
            scale REAL,
            flip BOOL,
            image BLOB
            )""")
        connection.commit()


    def loadView(self) -> list:
        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM view WHERE id == 0")
        data = cursor.fetchall()[0]
        return data


    def loadImages(self) -> list:
        connection = sqlite3.connect(self.file_path)
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
            path = item.path
            x = int(item.pos().x())
            y = int(item.pos().y())
            z = item.zValue()
            scale = item.scale()
            flip = item.is_flipped
            rotation = item.getRotation()

            cursor.execute("UPDATE images SET path = ? where id == ?", [path, item.id])
            cursor.execute("UPDATE images SET x = ? WHERE id == ?", [x, item.id])
            cursor.execute("UPDATE images SET y = ? WHERE id == ?", [y, item.id])
            cursor.execute("UPDATE images SET z = ? WHERE id == ?", [z, item.id])
            cursor.execute("UPDATE images SET rotation = ? WHERE id == ?", [rotation, item.id])
            cursor.execute("UPDATE images SET scale = ? WHERE id == ?", [scale, item.id])
            cursor.execute("UPDATE images SET flip = ? WHERE id == ?", [flip, item.id])

        connection.commit()
        cursor.execute("VACUUM")


    def storeItem(self, item: GraphicsItem) -> None:
        image = QByteArray()
        buffer = QBuffer(image)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        item.pixmap().save(buffer, item.type)

        path = item.path
        x = int(item.pos().x())
        y = int(item.pos().y())
        z = item.zValue()
        scale = item.scale()
        flip = item.is_flipped
        rotation = item.getRotation()

        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            [item.id, path, x, y, z, rotation, scale, flip, image])
        connection.commit()
        buffer.close()


    def deleteItem(self, item: GraphicsItem) -> None:
        connection = sqlite3.connect(self.file_path)
        cursor = connection.cursor()
        cursor.execute("DELETE FROM images WHERE id == ?", [item.id])
        connection.commit()
