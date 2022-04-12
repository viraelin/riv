from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *

from database import Database
from actions import Actions


project_file_path: str = None
sql: Database = None
settings: QSettings = None
actions: Actions = None
