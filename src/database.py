import os
import sqlite3

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from graphics_item import GraphicsItem


class Database:

    VERSION = "0.1.0"

    def __init__(self) -> None:
        self.db = "data.riv"
        self.createDatabase()


    def createDatabase(self) -> None:
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS
        view(
            id INTEGER PRIMARY KEY,
            version STRING,
            x INTEGER,
            y INTEGER,
            zoom FLOAT
            )""")
        cursor.execute("INSERT OR IGNORE INTO view VALUES (?, ?, ?, ?, ?)",
            [0, self.VERSION, 0, 0, 1.0])
        cursor.execute("""CREATE TABLE IF NOT EXISTS
        images(
            id INTEGER PRIMARY KEY,
            image BLOB,
            x INTEGER,
            y INTEGER,
            scale FLOAT,
            z_value INTEGER,
            flipped BOOL
            )""")
        connection.commit()


    def loadView(self) -> list:
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM view WHERE id == 0")
        data = cursor.fetchall()[0]
        return data


    def loadImages(self) -> list:
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM images")
        data = cursor.fetchall()
        return data


    def saveDatabase(self, view: QGraphicsView, items: list) -> None:
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()

        zoom = view.transform().m11()
        view_pos = view.mapToScene(view.rect().center())
        print(view_pos)
        view_x = int(view_pos.x())
        view_y = int(view_pos.y())
        cursor.execute("UPDATE view SET x = ? WHERE id == 0", [view_x])
        cursor.execute("UPDATE view SET y = ? WHERE id == 0", [view_y])
        cursor.execute("UPDATE view SET zoom = ? WHERE id == 0", [zoom])

        for item in items:
            x = int(item.pos().x())
            y = int(item.pos().y())
            scale = item.sceneTransform().m11()
            z_value = item.zValue()
            flipped = item.is_flipped
            cursor.execute("UPDATE images SET x = ? WHERE id == ?", [x, item.id])
            cursor.execute("UPDATE images SET y = ? WHERE id == ?", [y, item.id])
            cursor.execute("UPDATE images SET scale = ? WHERE id == ?", [scale, item.id])
            cursor.execute("UPDATE images SET z_value = ? WHERE id == ?", [z_value, item.id])
            cursor.execute("UPDATE images SET flipped = ? WHERE id == ?", [flipped, item.id])

        connection.commit()
        cursor.execute("VACUUM")


    def storeItem(self, item: GraphicsItem) -> None:
        image = QByteArray()
        buffer = QBuffer(image)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        item.pixmap().save(buffer, item.type)

        x = int(item.pos().x())
        y = int(item.pos().y())
        scale = item.sceneTransform().m11()
        z_value = item.zValue()
        flipped = item.is_flipped

        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?)",
            [item.id, image, x, y, scale, z_value, flipped])
        connection.commit()
        buffer.close()
