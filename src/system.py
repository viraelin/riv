# Copyright (C) 2020-2022 viraelin
# License: GPLv3.0

from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from database import Database
from actions import Actions


DEFAULT_FILE_DIR = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
DEFAULT_FILE_NAME = "untitled.riv"
PROJECT_FILTER = "RIV (*.riv)"
last_dialog_dir = DEFAULT_FILE_DIR

sql: Database = None
settings: QSettings = None
actions: Actions = None
undo_stack: QUndoStack = None

item_ids: list[int] = []

def getItemID() -> int:
    i = 0
    while i in item_ids:
        i += 1
    item_ids.append(i)
    return i
