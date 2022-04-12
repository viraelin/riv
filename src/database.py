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
            data BLOB,
            x INTEGER,
            y INTEGER,
            scale FLOAT,
            z_value INTEGER,
            item_is_flipped BOOL
            )""")
        connection.commit()


    def loadDatabase(self) -> list:
        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM images")
        data = cursor.fetchall()
        return data


    def storeItem(self, item: GraphicsItem) -> None:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        item.pixmap().save(buffer, item.type)

        item_id = item.id
        item_x = int(item.pos().x())
        item_y = int(item.pos().y())
        item_scale = item.sceneTransform().m11()
        item_z_value = item.zValue()
        item_is_flipped = item.is_flipped

        connection = sqlite3.connect(self.db)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?)",
            [item_id, byte_array, item_x, item_y, item_scale, item_z_value, item_is_flipped])
        connection.commit()
        buffer.close()
