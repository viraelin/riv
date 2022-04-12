import os
import sqlite3

from PyQt6.QtCore import *

from graphics_item import GraphicsItem


class Database:

    def __init__(self) -> None:
        self.db = "data.riv"
        if not os.path.isfile(self.db):
            self.createDatabase()


    def createDatabase(self) -> None:
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
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


    def loadDatabase(self) -> list:
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM images")
        data = cursor.fetchall()
        return data


    def saveDatabase(self, items: list) -> None:
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
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
